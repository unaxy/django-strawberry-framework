"""Repo-tooling tests for the agentflow workspace tool's copies, pool, evidence and cleanup.

Keeps the contracts of ``scripts/workspace.py`` against throwaway git
repositories and workspace roots under ``tmp_path``, never against this
checkout's copies or a running Postgres. The rows that matter most are the ones
whose failure would let a measurement read the wrong tree: the copy listing,
the exact mirror, the scrubbed environment, the provenance check, the per-copy
database match, the cleanup that must leave nothing, the turn-taking of runs
that share a copy and the locks that keep cleanup from taking a copy a command
is using (each second owner in its own process, so each holds its own locks).
A live ``/graphql/`` request has no wire shape for workspace copies, so none of
these rows can move there. There is no live sibling in
``examples/fakeshop/test_query/``.
"""

import contextlib
import errno
import fcntl
import hashlib
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import cast

import pytest
import yaml

from django_strawberry_framework.utils.typing import object_result
from scripts import workspace
from tests._idioms import json_at, json_list, json_loads, json_object

PACKAGE = workspace.PACKAGE_DIR


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
        env=workspace.clean_env(),
    )
    return result.stdout


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / PACKAGE / "__init__.py", "VALUE = 1\n")
    _write(root / PACKAGE / "core.py", "CORE = 2\n")
    _write(root / "examples" / "fakeshop" / "db.sqlite3", "tracked db\n")
    _write(root / ".gitignore", ".python-version\nignored.txt\noutput/\ntemp-tests/\n")
    _write(root / ".python-version", "3.14\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "initial")
    return root


@pytest.fixture
def layout(repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> workspace.Layout:
    monkeypatch.delenv(workspace.SLOTS_ENV, raising=False)

    def _no_running_postgres(_root: Path) -> None:
        return None

    def _ample_free_bytes(_path: Path) -> int:
        return workspace.MIN_FREE_BYTES * 2

    monkeypatch.setattr(workspace, "_running_postgres", _no_running_postgres)
    monkeypatch.setattr(workspace, "_free_bytes", _ample_free_bytes)
    return workspace.Layout(repo, tmp_path / "ws" / workspace.repo_key(repo), "review")


# --------------------------------------------------------------------------------------------
# Addresses and environment
# --------------------------------------------------------------------------------------------


def test_address_takes_flow_first_role_last_and_the_item_between() -> None:
    address = workspace.Address.parse(
        "review/django_strawberry_framework/optimizer/walker.py/perf-1",
    )

    assert (address.flow, address.item, address.role) == (
        "review",
        "django_strawberry_framework/optimizer/walker.py",
        "perf-1",
    )
    assert str(address) == "review/django_strawberry_framework/optimizer/walker.py/perf-1"
    assert address.evidence_slug == "django_strawberry_framework__optimizer__walker.py"


@pytest.mark.parametrize(
    "text",
    [
        "review/role",
        "Review/item/role",
        "review/../role",
        "review/item/.",
        "review/it em/role",
    ],
)
def test_address_refuses_what_is_not_flow_item_role(text: str) -> None:
    with pytest.raises(workspace.WorkspaceError):
        workspace.Address.parse(text)


def test_item_ref_keeps_slashes_in_the_item() -> None:
    ref = workspace.ItemRef.parse("hunt/pkg/filters/sets.py")

    assert (ref.flow, ref.item) == ("hunt", "pkg/filters/sets.py")
    with pytest.raises(workspace.WorkspaceError):
        workspace.ItemRef.parse("hunt")


def test_clean_env_scrubs_every_redirect_and_keeps_the_rest() -> None:
    caller = {
        "PATH": "/bin",
        "HOME": "/home/x",
        "DJANGO_STRAWBERRY_KANBAN_DB": "/repo/examples/fakeshop/db.sqlite3",
        "FAKESHOP_PG_DSN": "postgres://elsewhere",
        "GIT_INDEX_FILE": "/scratch/idx",
        "UV_PROJECT_ENVIRONMENT": "/repo/.venv",
        "VIRTUAL_ENV": "/repo/.venv",
        "PYTHONPATH": "/repo",
        "PYTEST_ADDOPTS": "-x",
        "UV_CACHE_DIR": "/cache",
    }

    env = workspace.clean_env(caller, FAKESHOP_SHARDED="1")

    assert env == {
        "PATH": "/bin",
        "HOME": "/home/x",
        "UV_CACHE_DIR": "/cache",
        "FAKESHOP_SHARDED": "1",
    }


# --------------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------------


def test_workspace_base_is_keyed_per_checkout_and_honours_the_root_override(
    repo: Path,
    tmp_path: Path,
) -> None:
    base = workspace.workspace_base(repo, {workspace.ROOT_ENV: str(tmp_path / "roots")})
    other = workspace.workspace_base(
        tmp_path / "other",
        {workspace.ROOT_ENV: str(tmp_path / "roots")},
    )

    assert base == (tmp_path / "roots").resolve() / workspace.repo_key(repo)
    assert base != other


def test_workspace_base_refuses_a_root_inside_the_repository(repo: Path) -> None:
    with pytest.raises(workspace.WorkspaceError, match="recurse"):
        workspace.workspace_base(repo, {workspace.ROOT_ENV: str(repo / "hunt-ws")})


def test_check_shared_checkout_refuses_a_copy(repo: Path, tmp_path: Path) -> None:
    workspace.check_shared_checkout(repo)
    copy = tmp_path / "flow" / "slots" / "slot-1"
    copy.mkdir(parents=True)
    (tmp_path / "flow" / workspace.MARKER_NAME).mkdir()

    with pytest.raises(workspace.WorkspaceError, match="shared checkout"):
        workspace.check_shared_checkout(copy)
    with pytest.raises(workspace.WorkspaceError, match=r"no \.git"):
        workspace.check_shared_checkout((tmp_path / "plain").resolve())


@pytest.mark.parametrize(("raw", "expected"), [("", 4), ("1", 1), ("9", 9)])
def test_pool_size_reads_the_slots_override(raw: str, expected: int) -> None:
    assert workspace.pool_size({workspace.SLOTS_ENV: raw}) == expected


@pytest.mark.parametrize("raw", ["0", "-2", "four"])
def test_pool_size_refuses_a_non_positive_cap(raw: str) -> None:
    with pytest.raises(workspace.WorkspaceError):
        workspace.pool_size({workspace.SLOTS_ENV: raw})


def test_database_names_are_per_copy_and_fit_postgres_identifiers(repo: Path) -> None:
    layout = workspace.Layout(repo, Path("/unused"), "review")
    name = layout.db_name("slot-12")

    assert name.startswith(layout.db_prefix)
    assert name.endswith("_review_slot12")
    assert layout.db_name("slot-1") != layout.db_name("slot-10")
    assert len(f"test_{name}_gw63") <= 63  # NAMEDATALEN - 1


# --------------------------------------------------------------------------------------------
# The copy listing and the mirror
# --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("name", "excluded"),
    [
        ("output/report.txt", True),
        ("docs/shadow/current/a.py", True),
        ("docs/review/temp-tests/x/probe.py", True),
        ("docs/dry/worker-memory/w1.md", True),
        ("hunt-ws/item/pkg/a.py", True),
        ("docs/review/REVIEW.md", False),
        ("django_strawberry_framework/core.py", False),
        ("scripts/workspace.py", False),
    ],
)
def test_is_excluded_drops_cycle_scratch_and_parked_copies(name: str, *, excluded: bool) -> None:
    assert workspace.is_excluded(name) is excluded


def test_wanted_files_is_the_git_listing_plus_python_version_minus_scratch(repo: Path) -> None:
    _write(repo / "untracked.py", "NEW = 1\n")
    _write(repo / "ignored.txt", "ignored\n")
    _write(repo / "output" / "run.txt", "out\n")
    _write(repo / "hunt-ws" / "item" / "copy.py", "parked\n")
    (repo / PACKAGE / "core.py").unlink()

    wanted = workspace.wanted_files(repo)

    assert sorted(wanted) == [
        ".gitignore",
        ".python-version",
        f"{PACKAGE}/__init__.py",
        "examples/fakeshop/db.sqlite3",
        "untracked.py",
    ]


def test_wanted_files_refuses_a_listing_without_the_package(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    _write(root / "README.md", "x\n")
    _git(root, "init", "-q")

    with pytest.raises(workspace.WorkspaceError, match="refusing to copy"):
        workspace.wanted_files(root)


def test_mirror_makes_an_exact_copy_and_a_resync_restores_a_dirtied_one(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "copy"
    first = workspace.mirror_tree(repo, copy)
    _write(copy / ".venv" / "bin" / "python", "kept\n")
    _write(copy / PACKAGE / "core.py", "CORE = 'mutated'\n")
    _write(copy / "examples" / "fakeshop" / "db.sqlite3", "written by a probe\n")
    _write(copy / "extra" / "probe.py", "leftover\n")
    _write(copy / PACKAGE / "__pycache__" / "core.cpython-314.pyc", "cache\n")

    second = workspace.mirror_tree(repo, copy)

    assert workspace.tree_digest(first) == workspace.tree_digest(second)
    assert (copy / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert (copy / "examples" / "fakeshop" / "db.sqlite3").read_text(
        encoding="utf-8",
    ) == "tracked db\n"
    assert not (copy / "extra").exists()
    assert not (copy / PACKAGE / "__pycache__").exists()
    assert (copy / ".venv" / "bin" / "python").read_text(encoding="utf-8") == "kept\n"
    on_disk = sorted(
        path.relative_to(copy).as_posix()
        for path in copy.rglob("*")
        if path.is_file() and ".venv" not in path.parts
    )
    assert on_disk == sorted(second)


def test_mirror_replaces_a_file_that_became_a_directory(repo: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy"
    workspace.mirror_tree(repo, copy)
    (repo / PACKAGE / "core.py").unlink()
    _write(repo / PACKAGE / "core.py" / "inner.py", "INNER = 1\n")

    entries = workspace.mirror_tree(repo, copy)

    assert f"{PACKAGE}/core.py/inner.py" in entries
    assert (copy / PACKAGE / "core.py" / "inner.py").is_file()


def test_mirror_copies_a_relative_symlink_and_refuses_an_absolute_one_into_the_tree(
    repo: Path,
    tmp_path: Path,
) -> None:
    (repo / "link.py").symlink_to(f"{PACKAGE}/core.py")
    copy = tmp_path / "copy"
    workspace.mirror_tree(repo, copy)

    assert (copy / "link.py").readlink() == Path(f"{PACKAGE}/core.py")

    (repo / "link.py").unlink()
    (repo / "link.py").symlink_to(repo / PACKAGE / "core.py")
    with pytest.raises(workspace.WorkspaceError, match="absolute path"):
        workspace.mirror_tree(repo, tmp_path / "copy2")


def test_tree_digest_moves_with_content_and_not_with_order() -> None:
    entries = {
        "a.py": [
            "h1",
            1,
            0,
            0,
        ],
        "b.py": [
            "h2",
            1,
            0,
            0,
        ],
    }
    reordered = {
        "b.py": [
            "h2",
            9,
            9,
            9,
        ],
        "a.py": [
            "h1",
            9,
            9,
            9,
        ],
    }
    changed = {
        "a.py": [
            "h1",
            1,
            0,
            0,
        ],
        "b.py": [
            "h3",
            1,
            0,
            0,
        ],
    }

    assert workspace.tree_digest(entries) == workspace.tree_digest(reordered)
    assert workspace.tree_digest(entries) != workspace.tree_digest(changed)


def _manifest(entries: dict[str, list[str | int]]) -> workspace._Manifest:
    """A slot manifest holding ``entries`` and placeholder sync stamps."""
    return {
        "synced_at": "t",
        "tree_digest": "d",
        "package_digest": "p",
        "entries": entries,
    }


def test_copy_edits_reports_changes_additions_and_deletions_but_not_caches(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "copy"
    manifest = _manifest(workspace.mirror_tree(repo, copy))
    assert workspace.copy_edits(copy, manifest) == []

    _write(copy / PACKAGE / "core.py", "CORE = 3\n")
    _write(copy / "new_probe.py", "x\n")
    (copy / ".python-version").unlink()
    _write(copy / PACKAGE / "__pycache__" / "x.pyc", "c\n")
    _write(copy / ".coverage", "c\n")
    _write(copy / ".venv" / "lib" / "site.py", "v\n")

    assert workspace.copy_edits(copy, manifest) == [
        ".python-version",
        f"{PACKAGE}/core.py",
        "new_probe.py",
    ]


def test_shared_moves_reports_what_the_shared_tree_changed_since_the_sync(
    repo: Path,
    tmp_path: Path,
) -> None:
    manifest = _manifest(workspace.mirror_tree(repo, tmp_path / "copy"))
    assert workspace.shared_moves(repo, manifest) == []

    _write(repo / PACKAGE / "core.py", "CORE = 'edited by Worker-2'\n")
    _write(repo / "added.py", "x\n")

    assert workspace.shared_moves(repo, manifest) == ["added.py", f"{PACKAGE}/core.py"]


# --------------------------------------------------------------------------------------------
# Pool
# --------------------------------------------------------------------------------------------


def _address(role: str, item: str = "pkg/a.py") -> workspace.Address:
    return workspace.Address("review", item, role)


def _statuses(layout: workspace.Layout) -> dict[str, str | None]:
    return {
        slot: (bound["status"] if bound else None)
        for slot, bound in workspace._load_state(layout)["slots"].items()
    }


def test_bind_reuses_an_address_and_gives_each_new_address_its_own_copy(
    layout: workspace.Layout,
) -> None:
    first = workspace.bind(layout, _address("perf-1"))
    again = workspace.bind(layout, _address("perf-1"))
    second = workspace.bind(layout, _address("mech-1"))

    assert (first.slot, again.slot, second.slot) == ("slot-1", "slot-1", "slot-2")
    assert _statuses(layout) == {"slot-1": "syncing", "slot-2": "syncing"}
    assert (layout.flow_dir / workspace.MARKER_NAME).is_dir()


class _Syncs(list[Path]):
    """The copies synced, in order, and what each ``uv sync`` held: each descriptor's file."""

    def __init__(self) -> None:
        super().__init__()
        self.holding: list[list[tuple[int, int]]] = []


@pytest.fixture
def syncs(monkeypatch: pytest.MonkeyPatch) -> _Syncs:
    """Every copy synced in this process, in order; ``uv sync`` itself never runs."""
    synced = _Syncs()

    def _uv_sync(destination: Path, holding: Sequence[int] = ()) -> None:
        synced.append(destination)
        synced.holding.append([(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in holding])

    monkeypatch.setattr(workspace, "_uv_sync", _uv_sync)
    return synced


def test_lease_syncs_a_new_copy_once_reuses_it_with_its_edits_and_fresh_resyncs_it(
    layout: workspace.Layout,
    syncs: list[Path],
) -> None:
    with workspace.lease(layout, _address("perf-1")) as first:
        _write(first.directory / "edit.txt", "kept\n")
    with workspace.lease(layout, _address("perf-1")) as again:
        kept = (again.directory / "edit.txt").exists()
    with workspace.lease(layout, _address("perf-1"), fresh=True) as fresh:
        wiped = not (fresh.directory / "edit.txt").exists()

    assert (first.slot, again.slot, fresh.slot) == ("slot-1", "slot-1", "slot-1")
    assert syncs == [first.directory, first.directory]
    assert kept
    assert wiped
    assert again.manifest == first.manifest
    assert _statuses(layout) == {"slot-1": "ready"}


def _run_once_before_reading(
    monkeypatch: pytest.MonkeyPatch,
    target: Path,
    action: Callable[[], object],
) -> None:
    """Run ``action`` once, right before the first ``read_text`` of ``target`` reads it."""
    real_read_text = Path.read_text
    pending = [action]

    def _read_text(path: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if path == target and pending:
            pending.pop()()
        return real_read_text(path, encoding=encoding, errors=errors)

    monkeypatch.setattr(Path, "read_text", _read_text)


def test_a_manifest_gone_when_the_lease_reads_it_resyncs_the_copy(
    layout: workspace.Layout,
    syncs: list[Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with workspace.lease(layout, _address("perf-1")) as first:
        pass
    manifest = layout.manifest_path(first.slot)
    _run_once_before_reading(monkeypatch, manifest, manifest.unlink)
    with workspace.lease(layout, _address("perf-1")) as again:
        pass

    assert syncs == [first.directory, again.directory]
    assert manifest.is_file()
    assert _statuses(layout) == {"slot-1": "ready"}


@pytest.mark.parametrize("fresh", [False, True], ids=["first-sync", "fresh-sync"])
def test_a_sync_that_dies_part_way_resyncs_on_the_next_run(
    layout: workspace.Layout,
    syncs: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    *,
    fresh: bool,
) -> None:
    if fresh:
        with workspace.lease(layout, _address("perf-1")):
            pass
    real_uv_sync = workspace._uv_sync

    def _dying_uv_sync(_destination: Path, _holding: object = ()) -> None:
        msg = "uv sync died"
        raise workspace.WorkspaceError(msg)

    monkeypatch.setattr(workspace, "_uv_sync", _dying_uv_sync)
    with (
        pytest.raises(workspace.WorkspaceError, match="uv sync died"),
        workspace.lease(layout, _address("perf-1"), fresh=fresh),
    ):
        pass
    left = _statuses(layout)
    monkeypatch.setattr(workspace, "_uv_sync", real_uv_sync)
    with workspace.lease(layout, _address("perf-1")) as held:
        pass

    assert left == {"slot-1": "syncing"}
    assert syncs[-1] == held.directory
    assert len(syncs) == (2 if fresh else 1)
    assert _statuses(layout) == {"slot-1": "ready"}


def test_a_sync_never_marks_a_copy_released_during_it(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))
    _ = workspace.release(layout, "pkg/a.py")
    _ = workspace.bind(layout, _address("mech-1", item="pkg/b.py"))

    with pytest.raises(workspace.WorkspaceError, match="no longer holds"):
        workspace._mark_synced(layout, binding.slot, _address("perf-1"), _manifest({}))
    bound = workspace._load_state(layout)["slots"]["slot-1"]
    assert bound is not None
    assert (bound["address"], bound["status"]) == ("review/pkg/b.py/mech-1", "syncing")


def test_copy_path_syncs_an_unsynced_copy_and_reuses_a_synced_one(
    layout: workspace.Layout,
    syncs: list[Path],
) -> None:
    _ = workspace.bind(layout, _address("perf-1"))

    first = workspace.copy_path(layout, _address("perf-1"))
    _write(first / "edit.txt", "kept\n")
    again = workspace.copy_path(layout, _address("perf-1"))

    assert first == again == layout.slot_dir("slot-1")
    assert syncs == [first]
    assert (again / "edit.txt").exists()


# --------------------------------------------------------------------------------------------
# Commands in other processes
# --------------------------------------------------------------------------------------------

#: One ``workspace.py`` command in its own process, so it holds its own locks on its own open
#: file descriptions. It runs the real command line (``main``) against the test's layout; only
#: what cannot run under test is replaced: ``uv sync``, the provenance probe and the worker's
#: command, which records the ``*.edit`` files it finds in the copy and then leaves its own.
#: Each step touches ``<name>.<step>`` when reached: ``bound`` once the address is bound,
#: ``sync`` in ``uv sync``, ``in`` in the command, ``probe`` at a lock tried without waiting or
#: creating, ``postgres`` and ``state`` at those reads. A step the test names as a pause then
#: waits until ``<name>.go-<step>`` appears. ``die_in_sync`` kills the process in its sync;
#: the ``hold`` command only holds the lock at ``path``, stepping ``opened`` each time it opens
#: that file. ``bin`` puts a folder ahead of ``PATH`` (a stand-in ``uv``); ``real_stream`` and
#: ``real_sync`` keep the script's own ``stream`` and ``uv sync``, run through that ``uv``.
_ACTOR = """
import json, os, sys, time
from pathlib import Path

config = json.loads(sys.argv[1])
sys.path.insert(0, config["scripts"])
import workspace

if config.get("bin"):
    os.environ["PATH"] = config["bin"] + os.pathsep + os.environ["PATH"]
sync = Path(config["sync"])
name = config["name"]
pauses = set(config["pauses"])
repo = Path(config["repo"])


def step(event):
    (sync / f"{name}.{event}").touch()
    if event in pauses:
        pauses.discard(event)
        while not (sync / f"{name}.go-{event}").exists():
            time.sleep(0.005)


def stepped(event, function):
    def wrapper(*args, **kwargs):
        step(event)
        return function(*args, **kwargs)
    return wrapper


real_bind = workspace.bind


def bind(*args, **kwargs):
    binding = real_bind(*args, **kwargs)
    step("bound")
    return binding


def uv_sync(_destination, _holding=()):
    step("sync")
    if config.get("die_in_sync"):
        os._exit(9)


def probe(directory, _env):
    return {
        "executable": str(directory / ".venv" / "bin" / "python"),
        "package_file": str(directory / workspace.PACKAGE_DIR / "__init__.py"),
        "databases": {},
    }


def stream(command, _env, _log_path, _header, cwd=None, holding=()):
    copy = Path(command[command.index("--directory") + 1])
    seen = sorted(path.stem for path in copy.glob("*.edit"))
    (copy / f"{name}.edit").write_text(name)
    (sync / f"{name}.json").write_text(json.dumps({"slot": copy.name, "seen": seen}))
    step("in")
    return workspace.Finished(0)


real_file_lock = workspace.file_lock


def file_lock(path, *, blocking=True, create=True):
    if not blocking and not create:
        step("probe")
    return real_file_lock(path, blocking=blocking, create=create)


def for_flow(flow, repo_root=repo):
    return workspace.Layout(repo_root, workspace.workspace_base(repo_root), flow)


workspace.REPO_ROOT = repo
workspace.Layout.for_flow = staticmethod(for_flow)
workspace.bind = bind
workspace.file_lock = file_lock
workspace.probe = probe
if not config.get("real_stream"):
    workspace.stream = stream
if not config.get("real_sync"):
    workspace._uv_sync = uv_sync
workspace._free_bytes = lambda _path: workspace.MIN_FREE_BYTES * 2
workspace._running_postgres = stepped("postgres", lambda _root: None)
workspace._load_state = stepped("state", workspace._load_state)
if config["argv"] == ["hold"]:
    real_open = os.open

    def opened(path, flags, mode=0o777, **kwargs):
        descriptor = real_open(path, flags, mode, **kwargs)
        if str(path) == config["path"]:
            step("opened")
        return descriptor

    os.open = opened
    step("waiting")
    with real_file_lock(Path(config["path"])):
        step("in")
    sys.exit(0)
sys.exit(workspace.main(config["argv"]))
"""

_ADDRESS = "review/pkg/a.py/perf-1"


class _Actors:
    """``workspace.py`` commands in separate processes, each stopped and let on at named steps."""

    def __init__(self, layout: workspace.Layout, sync: Path) -> None:
        self.layout = layout
        self.sync = sync
        self.processes: dict[str, subprocess.Popen[str]] = {}

    def start(
        self,
        name: str,
        *argv: str,
        pauses: tuple[str, ...] = (),
        **options: object,
    ) -> None:
        payload = {
            "name": name,
            "argv": list(argv),
            "pauses": list(pauses),
            "sync": str(self.sync),
            "scripts": str(Path(workspace.__file__).parent),
            "repo": str(self.layout.repo_root),
            **options,
        }
        env = workspace.clean_env()
        env[workspace.ROOT_ENV] = str(self.layout.base.parent)
        _ = env.pop(workspace.SLOTS_ENV, None)
        self.processes[name] = subprocess.Popen(
            [
                sys.executable,
                "-c",
                _ACTOR,
                json.dumps(payload),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )

    def run(
        self,
        name: str,
        address: str = _ADDRESS,
        *flags: str,
        pauses: tuple[str, ...] = (),
        **options: object,
    ) -> None:
        self.start(name, "run", address, *flags, "--", "edit", pauses=pauses, **options)

    def reached(
        self,
        name: str,
        event: str,
        within: float = 30.0,
    ) -> bool:
        deadline = time.monotonic() + within
        while not (self.sync / f"{name}.{event}").exists():
            if self.processes[name].poll() is not None or time.monotonic() > deadline:
                return (self.sync / f"{name}.{event}").exists()
            time.sleep(0.01)
        return True

    def go(self, name: str, event: str) -> None:
        (self.sync / f"{name}.go-{event}").touch()

    def finish(self, name: str, timeout: float = 30.0) -> tuple[int, str, str]:
        """Return the command's exit code, stdout and stderr; fail on a wait that never ends."""
        process = self.processes[name]
        try:
            out, err = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            _ = process.communicate()
            pytest.fail(f"{name} never finished: a lock wait that never ends")
        return process.returncode, out, err

    def ran(self, name: str) -> dict[str, object] | None:
        """Return what the command saw in its copy, or ``None`` when it never ran."""
        record = self.sync / f"{name}.json"
        if not record.exists():
            return None
        document = json_loads(record.read_text(encoding="utf-8"))
        assert workspace._is_json_object(document)
        return document

    def synced(self, name: str) -> bool:
        return (self.sync / f"{name}.sync").exists()


@pytest.fixture
def actors(layout: workspace.Layout, tmp_path: Path) -> Iterator[_Actors]:
    sync = tmp_path / "sync"
    sync.mkdir()
    crew = _Actors(layout, sync)
    yield crew
    for process in crew.processes.values():
        if process.poll() is None:
            process.kill()
        _ = process.communicate()


def _edits(directory: Path) -> list[str]:
    return sorted(path.stem for path in directory.glob("*.edit"))


def _bound_to(layout: workspace.Layout) -> dict[str, str | None]:
    return {
        slot: bound["address"] if bound else None
        for slot, bound in workspace._load_state(layout)["slots"].items()
    }


def _refusal(address: str, slot: str) -> str:
    return (
        f"workspace: {address}: {slot} was released while this command waited for it; "
        "run it again\n"
    )


@pytest.mark.parametrize("queued", [["B"], ["B", "C"]], ids=["one-queued", "two-queued"])
def test_runs_started_during_the_first_sync_reuse_its_copy_and_every_edit_since(
    layout: workspace.Layout,
    actors: _Actors,
    queued: list[str],
) -> None:
    actors.run("A", pauses=("sync",))
    assert actors.reached("A", "sync")
    for name in queued:
        actors.run(name)
        assert actors.reached(name, "bound")
    actors.go("A", "sync")

    codes = [actors.finish(name)[0] for name in ["A", *queued]]

    assert codes == [0] * (1 + len(queued))
    assert [actors.synced(name) for name in queued] == [False] * len(queued)
    for name in queued:
        assert "A" in cast("list[str]", cast("dict[str, object]", actors.ran(name))["seen"])
    assert _edits(layout.slot_dir("slot-1")) == sorted(["A", *queued])
    assert _statuses(layout) == {"slot-1": "ready"}


def test_a_fresh_run_started_during_the_first_sync_still_resyncs(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("A", pauses=("sync",))
    assert actors.reached("A", "sync")
    actors.run("B", _ADDRESS, "--fresh")
    assert actors.reached("B", "bound")
    actors.go("A", "sync")

    assert [actors.finish("A")[0], actors.finish("B")[0]] == [0, 0]
    assert actors.synced("B")
    assert actors.ran("B") == {"slot": "slot-1", "seen": []}
    assert _edits(layout.slot_dir("slot-1")) == ["B"]
    assert _statuses(layout) == {"slot-1": "ready"}


def test_a_run_started_during_a_first_sync_that_dies_resyncs(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("A", pauses=("sync",), die_in_sync=True)
    assert actors.reached("A", "sync")
    actors.run("B")
    assert actors.reached("B", "bound")
    actors.go("A", "sync")

    assert [actors.finish("A")[0], actors.finish("B")[0]] == [9, 0]
    assert actors.ran("A") is None
    assert actors.synced("B")
    assert actors.ran("B") == {"slot": "slot-1", "seen": []}
    assert _statuses(layout) == {"slot-1": "ready"}


def test_an_edit_at_the_printed_path_survives_a_run_started_during_paths_sync(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.start("P", "path", _ADDRESS, pauses=("sync",))
    assert actors.reached("P", "sync")
    actors.run("B", pauses=("bound",))
    assert actors.reached("B", "bound")
    actors.go("P", "sync")
    assert actors.finish("P")[:2] == (0, f"{layout.slot_dir('slot-1')}\n")
    _ = _write(layout.slot_dir("slot-1") / "worker.edit", "kept\n")
    actors.go("B", "bound")

    assert actors.finish("B")[0] == 0
    assert not actors.synced("B")
    assert actors.ran("B") == {"slot": "slot-1", "seen": ["worker"]}


@pytest.mark.parametrize(
    "after",
    [[], ["C"], ["C", "D"]],
    ids=["left-free", "taken-by-another", "address-moved"],
)
def test_a_run_whose_copy_is_released_while_it_waits_refuses_and_never_runs(
    layout: workspace.Layout,
    actors: _Actors,
    after: list[str],
) -> None:
    actors.run("B", pauses=("bound",))
    assert actors.reached("B", "bound")
    released = workspace.release(layout, "pkg/a.py")
    if "C" in after:
        actors.run("C", "review/pkg/c.py/perf-1")
        assert actors.finish("C")[0] == 0
        _ = _write(layout.slot_dir("slot-1") / "worker.edit", "kept\n")
    if "D" in after:
        actors.run("D")
        assert actors.finish("D")[0] == 0
    actors.go("B", "bound")

    code, out, err = actors.finish("B")

    assert released == ["slot-1 review/pkg/a.py/perf-1"]
    assert (code, out, err) == (workspace.REFUSED, "", _refusal(_ADDRESS, "slot-1"))
    assert actors.ran("B") is None
    assert not actors.synced("B")
    assert _bound_to(layout) == {
        "slot-1": "review/pkg/c.py/perf-1" if after else None,
        **({"slot-2": _ADDRESS} if "D" in after else {}),
    }
    if after:
        assert _edits(layout.slot_dir("slot-1")) == ["C", "worker"]
        assert actors.ran("C") == {"slot": "slot-1", "seen": []}
        assert set(_statuses(layout).values()) == {"ready"}
    if "D" in after:
        assert actors.ran("D") == {"slot": "slot-2", "seen": []}


def test_a_run_whose_address_holds_its_copy_again_runs_in_that_binding(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("B", pauses=("bound",))
    assert actors.reached("B", "bound")
    released = workspace.release(layout, "pkg/a.py")
    actors.run("D")
    assert actors.finish("D")[0] == 0
    actors.go("B", "bound")

    code, out, _ = actors.finish("B")

    assert released == ["slot-1 review/pkg/a.py/perf-1"]
    assert (code, out) == (0, "")
    assert actors.ran("D") == {"slot": "slot-1", "seen": []}
    assert actors.ran("B") == {"slot": "slot-1", "seen": ["D"]}
    assert not actors.synced("B")
    assert _bound_to(layout) == {"slot-1": _ADDRESS}
    assert _edits(layout.slot_dir("slot-1")) == ["B", "D"]
    assert _statuses(layout) == {"slot-1": "ready"}


def test_a_fresh_run_killed_in_its_sync_leaves_the_copy_to_resync(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("A")
    assert actors.finish("A")[0] == 0
    actors.run("F", _ADDRESS, "--fresh", die_in_sync=True)
    assert actors.finish("F")[0] == 9
    left = _statuses(layout)
    actors.run("B")

    assert actors.finish("B")[0] == 0
    assert left == {"slot-1": "syncing"}
    assert actors.synced("B")
    assert actors.ran("B") == {"slot": "slot-1", "seen": []}
    assert _statuses(layout) == {"slot-1": "ready"}


def test_path_prints_a_synced_copy_while_a_command_runs_in_it(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("A")
    assert actors.finish("A")[0] == 0
    actors.run("B", pauses=("in",))
    assert actors.reached("B", "in")
    actors.start("P", "path", _ADDRESS)

    printed = actors.finish("P", timeout=20)
    actors.go("B", "in")

    assert printed[:2] == (0, f"{layout.slot_dir('slot-1')}\n")
    assert actors.finish("B")[0] == 0


def test_bind_refuses_when_every_copy_is_bound_and_release_frees_them(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.SLOTS_ENV, "2")
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("perf-1"))

    with pytest.raises(workspace.WorkspaceError, match="release review/<item>"):
        workspace.bind(layout, _address("before", item="pkg/b.py"))

    released = workspace.release(layout, "pkg/a.py")
    reused = workspace.bind(layout, _address("before", item="pkg/b.py"))

    assert released == ["slot-1 review/pkg/a.py/before", "slot-2 review/pkg/a.py/perf-1"]
    assert reused.slot == "slot-1"
    assert _statuses(layout) == {"slot-1": "syncing", "slot-2": None}


def test_bind_refuses_a_new_copy_below_the_free_disk_guard(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _short_free_bytes(_path: Path) -> int:
        return workspace.MIN_FREE_BYTES - 1

    monkeypatch.setattr(workspace, "_free_bytes", _short_free_bytes)

    with pytest.raises(workspace.WorkspaceError, match="GB free"):
        workspace.bind(layout, _address("perf-1"))


def test_release_of_one_role_keeps_the_item_and_its_other_copies(layout: workspace.Layout) -> None:
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("perf-1"))

    assert workspace.release(layout, "pkg/a.py", roles=["perf-1"]) == [
        "slot-2 review/pkg/a.py/perf-1",
    ]
    assert workspace.bind(layout, _address("before")).slot == "slot-1"


def test_release_keep_frees_a_phase_and_spares_the_pinned_copy(layout: workspace.Layout) -> None:
    workspace.bind(layout, _address("before"))
    workspace.bind(layout, _address("performance"))
    workspace.bind(layout, _address("mechanics"))
    with workspace.file_lock(layout.pool_lock):
        state = workspace._load_state(layout)
        state["items"]["pkg/a.py"] = {"item_baseline": "abc", "at": "t"}
        workspace._write_json(layout.state_path, state)

    released = workspace.release(layout, "pkg/a.py", keep=["before"])

    assert released == ["slot-2 review/pkg/a.py/performance", "slot-3 review/pkg/a.py/mechanics"]
    state = workspace._load_state(layout)
    assert state["slots"]["slot-1"] is not None
    assert state["slots"]["slot-1"]["role"] == "before"
    assert state["items"]["pkg/a.py"]["item_baseline"] == "abc"


def test_release_refuses_while_a_command_runs_in_the_copy(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))

    with (
        workspace.file_lock(layout.slot_lock(binding.slot)),
        pytest.raises(workspace.LockBusyError, match="still runs"),
    ):
        workspace.release(layout, "pkg/a.py")
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]


def test_release_of_a_flow_that_never_ran_creates_nothing(layout: workspace.Layout) -> None:
    assert workspace.release(layout, "pkg/a.py") == []
    assert not layout.flow_dir.exists()


# --------------------------------------------------------------------------------------------
# Cleanup
# --------------------------------------------------------------------------------------------


def test_gc_removes_the_flow_folder_and_its_empty_parent(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(workspace.ROOT_ENV, raising=False)
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")
    _write(layout.run_log, "{}\n")

    report = workspace.gc(layout)

    assert not layout.flow_dir.exists()
    assert not layout.base.exists()
    assert not layout.base.parent.exists()
    assert report[0].startswith(f"removed {layout.flow_dir}")


def test_gc_keeps_a_root_override_folder(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    workspace.bind(layout, _address("perf-1"))

    workspace.gc(layout)

    assert not layout.base.exists()
    assert layout.base.parent.exists()


def test_gc_refuses_a_folder_it_did_not_create(layout: workspace.Layout) -> None:
    _write(layout.flow_dir / "someone-elses.txt", "x\n")

    with pytest.raises(workspace.WorkspaceError, match="marker"):
        workspace.gc(layout)
    assert (layout.flow_dir / "someone-elses.txt").exists()


def test_gc_refuses_while_a_command_runs_and_names_its_copy(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))

    with workspace.flow_lease(layout), workspace.file_lock(layout.slot_lock(binding.slot)):
        with pytest.raises(workspace.LockBusyError, match=r"still runs in review \(slot-1\)"):
            workspace.gc(layout)
        assert binding.directory.parent.exists()
    workspace.gc(layout)
    assert not layout.flow_dir.exists()


def test_gc_cut_short_keeps_the_marker_so_the_next_gc_finishes(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")
    _write(layout.run_log, "{}\n")
    real_rmtree = shutil.rmtree

    def _fails_once(path: Path) -> None:
        monkeypatch.setattr(shutil, "rmtree", real_rmtree)
        real_rmtree(path)
        raise OSError(66, "Directory not empty", str(path))

    monkeypatch.setattr(shutil, "rmtree", _fails_once)

    with pytest.raises(OSError, match="not empty"):
        workspace.gc(layout)
    assert (layout.flow_dir / workspace.MARKER_NAME).exists()
    workspace.gc(layout)
    assert not layout.flow_dir.exists()


def _purge(root: Path, keep: tuple[str, ...] = ()) -> None:
    """Unlink every regular file under ``root`` but ``keep``, as the macOS ``$TMPDIR`` purge does.

    Directories and symlinks stay; ``keep`` names paths relative to ``root``.
    """
    for folder, _dirs, files in os.walk(root):
        for name in files:
            path = Path(folder) / name
            if (
                path.is_file()
                and not path.is_symlink()
                and str(path.relative_to(root)) not in keep
            ):
                path.unlink()


def test_gc_removes_a_flow_the_tmpdir_purge_emptied(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(workspace.ROOT_ENV, raising=False)
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")
    _write(layout.run_log, "{}\n")
    assert (layout.flow_dir / workspace.MARKER_NAME).is_dir()

    _purge(layout.flow_dir)
    workspace.gc(layout)

    assert not layout.flow_dir.exists()
    assert not layout.base.exists()
    assert not layout.base.parent.exists()


def test_a_purge_that_spares_state_json_keeps_the_flow_releasable_and_listed(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")

    _purge(layout.flow_dir, keep=("state.json",))

    assert "review: 1 of 4 copies" in workspace.status(layout.repo_root, None)
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]


@pytest.mark.parametrize("run_first", [True, False])
def test_a_marker_file_becomes_the_directory_and_gc_removes_either(
    layout: workspace.Layout,
    *,
    run_first: bool,
) -> None:
    marker = _write(layout.flow_dir / workspace.MARKER_NAME, "{}")
    if run_first:
        with workspace.flow_lease(layout) as marked:
            assert marked
        assert marker.is_dir()

    workspace.gc(layout)

    assert not layout.flow_dir.exists()


def test_a_marker_file_is_upgraded_under_the_pool_lock(layout: workspace.Layout) -> None:
    marker = _write(layout.flow_dir / workspace.MARKER_NAME, "{}")
    upgrade = threading.Thread(target=layout.ensure_marked)
    try:
        with workspace.file_lock(layout.pool_lock):
            upgrade.start()
            upgrade.join(timeout=0.5)
            waited = upgrade.is_alive()
            still_a_file = marker.is_file()
    finally:
        if upgrade.ident is not None:
            upgrade.join()

    assert waited
    assert still_a_file
    assert marker.is_dir()


def test_a_marker_another_command_upgraded_first_is_left_as_the_directory(
    layout: workspace.Layout,
) -> None:
    marker = _write(layout.flow_dir / workspace.MARKER_NAME, "{}")
    errors: list[OSError] = []

    def _upgrade() -> None:
        try:
            layout.ensure_marked()
        except OSError as error:
            errors.append(error)

    upgrade = threading.Thread(target=_upgrade)
    try:
        with workspace.file_lock(layout.pool_lock):
            upgrade.start()
            upgrade.join(timeout=0.5)
            marker.unlink()
            marker.mkdir()
    finally:
        if upgrade.ident is not None:
            upgrade.join()

    assert errors == []
    assert marker.is_dir()


def test_a_lock_taken_after_gc_never_brings_the_flow_back(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    binding = workspace.bind(layout, _address("perf-1"))
    workspace.gc(layout)

    with pytest.raises(FileNotFoundError), workspace.file_lock(layout.slot_lock(binding.slot)):
        pass
    assert workspace.release(layout, "pkg/a.py") == []
    assert workspace.status(layout.repo_root, layout.flow)[1] == "review: 0 of 4 copies"
    assert not layout.flow_dir.exists()


def test_status_reports_a_flow_gc_removes_mid_read_as_gone(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    workspace.bind(layout, _address("perf-1"))

    def _gc() -> None:
        workspace.gc(layout)

    _run_once_before_reading(monkeypatch, layout.state_path, _gc)

    assert workspace.status(layout.repo_root, None) == [
        f"root {layout.base}",
        "review: 0 of 4 copies",
        "postgres: no fakeshop container runs",
    ]
    assert not layout.flow_dir.exists()


def test_a_state_file_that_cannot_be_read_is_an_error_not_an_empty_pool(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    workspace.bind(layout, _address("perf-1"))
    layout.state_path.unlink()
    layout.state_path.mkdir()

    with pytest.raises(IsADirectoryError):
        workspace.status(layout.repo_root, None)


def test_a_flow_folder_is_made_while_another_gc_removes_the_empty_parents(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_mkdir = Path.mkdir
    races = [errno.EINVAL, errno.ENOENT]

    def _parent_removed_twice(
        path: Path,
        mode: int = 0o777,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        if path == layout.flow_dir and races:
            raise OSError(races.pop(0), "a parent was removed", str(path))
        real_mkdir(path, mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", _parent_removed_twice)

    with workspace.flow_lease(layout) as flow:
        assert flow.marked
    assert races == []


def test_a_flow_folder_gone_right_after_it_exists_is_made_again_and_a_file_there_raises(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_mkdir = Path.mkdir
    vanished = [True]

    def _exists_then_vanishes(
        path: Path,
        mode: int = 0o777,
        *,
        parents: bool = False,
        exist_ok: bool = False,
    ) -> None:
        if path == layout.flow_dir and vanished:
            vanished.pop()
            raise FileExistsError(errno.EEXIST, "made and removed again", str(path))
        real_mkdir(path, mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", _exists_then_vanishes)
    workspace._make_flow_dir(layout.flow_dir)
    assert vanished == []
    assert layout.flow_dir.is_dir()

    layout.flow_dir.rmdir()
    _write(layout.flow_dir, "not a folder\n")
    with pytest.raises(FileExistsError):
        workspace._make_flow_dir(layout.flow_dir)
    assert layout.flow_dir.is_file()


def test_status_marks_the_copy_a_command_holds(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    held = workspace.bind(layout, _address("perf-1"))
    workspace.bind(layout, _address("mech-1"))

    with workspace.file_lock(layout.slot_lock(held.slot)):
        lines = workspace.status(layout.repo_root, layout.flow)

    assert lines[2:4] == [
        "  slot-1  review/pkg/a.py/perf-1 (syncing) RUNNING",
        "  slot-2  review/pkg/a.py/mech-1 (syncing)",
    ]


# --------------------------------------------------------------------------------------------
# Cleanup against other processes
# --------------------------------------------------------------------------------------------


def test_release_keeps_the_copy_until_its_binding_is_gone(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("run", pauses=("bound",))
    assert actors.reached("run", "bound")
    actors.start("release", "release", "review/pkg/a.py", pauses=("postgres",))
    assert actors.reached("release", "postgres")
    with (
        pytest.raises(workspace.LockBusyError),
        workspace.file_lock(layout.slot_lock("slot-1"), blocking=False),
    ):
        pass

    actors.go("run", "bound")

    with (
        pytest.raises(workspace.LockBusyError),
        workspace.file_lock(layout.slot_lock("slot-1"), blocking=False),
    ):
        pass
    assert not actors.reached("run", "in", within=0.5)
    actors.go("release", "postgres")
    assert actors.finish("release") == (
        0,
        "released 1 copy(ies)\n  slot-1 review/pkg/a.py/perf-1\n",
        "",
    )
    assert actors.finish("run") == (workspace.REFUSED, "", _refusal(_ADDRESS, "slot-1"))
    assert actors.ran("run") is None
    assert _bound_to(layout) == {"slot-1": None}


@pytest.mark.usefixtures("layout")
def test_gc_refuses_while_a_run_waits_for_its_copy(
    actors: _Actors,
) -> None:
    actors.run("run", pauses=("bound",))
    assert actors.reached("run", "bound")

    actors.start("gc", "gc", "review")

    assert actors.finish("gc") == (
        1,
        "",
        "workspace: a command still runs in review; wait for it to finish\n",
    )
    actors.go("run", "bound")
    assert actors.finish("run")[0] == 0
    assert actors.ran("run") == {"slot": "slot-1", "seen": []}


def test_gc_keeps_the_flow_until_it_is_gone_and_the_run_it_held_off_holds_off_the_next(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    old = workspace.bind(layout, _address("before"))
    _write(old.directory / "retained.txt", "edits\n")
    actors.start("gc", "gc", "review", pauses=("postgres",))
    assert actors.reached("gc", "postgres")
    flow = os.open(layout.flow_dir, os.O_RDONLY | os.O_DIRECTORY)
    try:
        with pytest.raises(BlockingIOError):
            fcntl.flock(flow, fcntl.LOCK_SH | fcntl.LOCK_NB)
    finally:
        os.close(flow)

    actors.run("run", pauses=("in",))

    assert not actors.reached("run", "bound", within=0.5)
    assert (old.directory / "retained.txt").exists()
    actors.go("gc", "postgres")
    assert actors.finish("gc") == (0, f"removed {layout.flow_dir} (0 MB)\n", "")
    assert actors.reached("run", "in")
    assert (layout.flow_dir / workspace.MARKER_NAME).exists()
    assert _bound_to(layout) == {"slot-1": _ADDRESS}
    assert not (old.directory / "retained.txt").exists()
    actors.start("gc-again", "gc", "review")
    assert actors.finish("gc-again") == (
        1,
        "",
        "workspace: a command still runs in review (slot-1); wait for it to finish\n",
    )
    actors.go("run", "in")
    assert actors.finish("run")[0] == 0
    assert _edits(old.directory) == ["run"]


def test_status_never_makes_a_release_refuse(layout: workspace.Layout, actors: _Actors) -> None:
    bound = workspace.bind(layout, _address("perf-1"))
    with workspace.file_lock(layout.slot_lock(bound.slot)):
        pass
    actors.start("status", "status", "review", pauses=("probe",))
    assert actors.reached("status", "probe")
    with (
        pytest.raises(workspace.LockBusyError),
        workspace.file_lock(layout.pool_lock, blocking=False),
    ):
        pass

    actors.start("release", "release", "review/pkg/a.py")

    assert not actors.reached("release", "state", within=0.5)
    actors.go("status", "probe")
    assert actors.finish("release") == (
        0,
        "released 1 copy(ies)\n  slot-1 review/pkg/a.py/perf-1\n",
        "",
    )
    assert actors.finish("status") == (
        0,
        "\n".join(
            [
                f"root {layout.base}",
                "review: 1 of 4 copies",
                "  slot-1  review/pkg/a.py/perf-1 (syncing)",
                "postgres: no fakeshop container runs",
                "",
            ],
        ),
        "",
    )


def test_release_and_a_syncing_run_never_wait_on_each_other(
    layout: workspace.Layout,
    actors: _Actors,
) -> None:
    actors.run("run", pauses=("sync",))
    assert actors.reached("run", "sync")
    actors.start("release", "release", "review/pkg/a.py", pauses=("state",))
    assert actors.reached("release", "state")

    actors.go("run", "sync")
    time.sleep(0.3)
    actors.go("release", "state")

    assert actors.finish("release") == (
        1,
        "",
        "workspace: review/pkg/a.py: a command still runs in slot-1\n",
    )
    assert actors.finish("run")[0] == 0
    assert _bound_to(layout) == {"slot-1": _ADDRESS}
    assert _statuses(layout) == {"slot-1": "ready"}


def test_a_lock_file_replaced_while_waited_on_never_admits_two_holders(
    actors: _Actors,
    tmp_path: Path,
) -> None:
    lock = tmp_path / "copy.lock"
    actors.start("first", "hold", pauses=("in",), path=str(lock))
    assert actors.reached("first", "in")
    actors.start("waiter", "hold", pauses=("in",), path=str(lock))
    assert actors.reached("waiter", "opened")
    lock.unlink()
    actors.start("third", "hold", pauses=("in",), path=str(lock))
    assert actors.reached("third", "in")

    actors.go("first", "in")
    assert actors.finish("first")[0] == 0

    assert not actors.reached("waiter", "in", within=0.5)
    actors.go("third", "in")
    assert actors.reached("waiter", "in")
    actors.go("waiter", "in")
    assert actors.finish("waiter")[0] == 0
    assert actors.finish("third")[0] == 0


# --------------------------------------------------------------------------------------------
# Provenance and audit
# --------------------------------------------------------------------------------------------


def _probe(copy: Path, **databases: workspace._ProbeDatabase) -> workspace._ProbeResult:
    return {
        "executable": str(copy / ".venv" / "bin" / "python"),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "databases": databases,
    }


def _sqlite(name: object) -> workspace._ProbeDatabase:
    return {"ENGINE": "django.db.backends.sqlite3", "NAME": str(name)}


def test_provenance_accepts_the_copys_package_interpreter_and_databases(tmp_path: Path) -> None:
    copy = tmp_path / "slot-1"
    found = _probe(
        copy,
        default=_sqlite(copy / "examples" / "fakeshop" / "db.sqlite3"),
        shard_b=_sqlite(copy / "examples" / "fakeshop" / "db_shard_b.sqlite3"),
    )

    assert workspace.provenance_faults(found, copy, "sharded", None) == []


def test_provenance_refuses_the_shared_package_and_the_tracked_database(
    repo: Path,
    tmp_path: Path,
) -> None:
    copy = tmp_path / "slot-1"
    found = _probe(copy, default=_sqlite(repo / "examples" / "fakeshop" / "db.sqlite3"))
    found["package_file"] = str(repo / PACKAGE / "__init__.py")
    found["executable"] = str(repo / ".venv" / "bin" / "python")

    faults = workspace.provenance_faults(found, copy, "default", None)

    assert len(faults) == 3  # package, interpreter, database
    assert all(str(copy) in fault or ".venv" in fault for fault in faults)


def test_provenance_refuses_a_postgres_database_that_is_not_the_copys(tmp_path: Path) -> None:
    copy = tmp_path / "slot-1"
    postgres: workspace._ProbeDatabase = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "fakeshop",
    }

    faults = workspace.provenance_faults(
        _probe(copy, default=postgres),
        copy,
        "pg",
        "ws_x_review_slot1",
    )

    assert faults == [
        "alias 'default' opens Postgres 'fakeshop', not 'ws_x_review_slot1'",
        "cell pg did not select 'ws_x_review_slot1' for the default alias",
    ]


def test_audit_binds_cited_run_ids_and_fails_unknown_or_foreign_ones(
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _layout_base(_root: Path) -> Path:
        return layout.base

    monkeypatch.setattr(workspace, "workspace_base", _layout_base)
    copy = layout.slot_dir("slot-1")
    good = {
        "run_id": "review-20260924T120000-aaaaaa",
        "address": "review/pkg/a.py/perf-1",
        "directory": str(copy),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "package_digest": "sha256:" + "0" * 64,
        "databases": {"default": str(copy / "examples" / "fakeshop" / "db.sqlite3")},
        "cell": "default",
        "exit": 0,
        "copy_edits": [],
        "shared_moves": ["pkg/a.py"],
    }
    foreign = {
        **good,
        "run_id": "review-20260924T120001-bbbbbb",
        "package_file": str(layout.repo_root / PACKAGE / "__init__.py"),
    }
    _write(layout.run_log, "".join(json.dumps(run) + "\n" for run in (good, foreign)))
    record = _write(
        tmp_path / "rev.md",
        "Proof: review-20260924T120000-aaaaaa, again review-20260924T120000-aaaaaa;\n"
        "review-20260924T120001-bbbbbb and review-20260101T000000-cccccc.\n",
    )

    lines, ok = workspace.audit_record(layout.repo_root, record)

    assert ok is False
    assert lines[0].endswith("3 run id(s) cited")
    assert lines[1].startswith("  ok   review-20260924T120000-aaaaaa")
    assert "shared=moved 1" in lines[1]
    assert lines[2].startswith("  FAIL review-20260924T120001-bbbbbb")
    assert lines[3].startswith("  FAIL review-20260101T000000-cccccc: no run log entry")


def test_audit_reports_a_run_log_gc_removes_mid_read_as_gone(
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    def _layout_base(_root: Path) -> Path:
        return layout.base

    monkeypatch.setattr(workspace, "workspace_base", _layout_base)
    layout.ensure_marked()
    copy = layout.slot_dir("slot-1")
    run_id = "review-20260924T120000-aaaaaa"
    run: dict[str, object] = {
        "run_id": run_id,
        "address": "review/pkg/a.py/perf-1",
        "directory": str(copy),
        "package_file": str(copy / PACKAGE / "__init__.py"),
        "package_digest": "sha256:" + "0" * 64,
        "databases": {"default": str(copy / "examples" / "fakeshop" / "db.sqlite3")},
        "cell": "default",
        "exit": 0,
        "copy_edits": [],
        "shared_moves": [],
    }
    _write(layout.run_log, json.dumps(run) + "\n")
    record = _write(tmp_path / "rev.md", f"Proof: {run_id}.\n")

    def _gc() -> None:
        workspace.gc(layout)

    _run_once_before_reading(monkeypatch, layout.run_log, _gc)
    lines, ok = workspace.audit_record(layout.repo_root, record)

    assert ok is False
    assert lines[1:] == [f"  FAIL {run_id}: no run log entry (never ran here, or gc removed it)"]
    assert not layout.flow_dir.exists()


def test_audit_fails_a_run_that_recorded_no_package_file_and_no_exit(
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A run log line may hold ``null`` for both; the audit reports it, it does not crash."""

    def _layout_base(_root: Path) -> Path:
        return layout.base

    monkeypatch.setattr(workspace, "workspace_base", _layout_base)
    copy = layout.slot_dir("slot-1")
    unresolved = {
        "run_id": "review-20260924T120000-aaaaaa",
        "address": "review/pkg/a.py/perf-1",
        "directory": str(copy),
        "package_file": None,
        "package_digest": "sha256:" + "0" * 64,
        "databases": {"default": str(copy / "examples" / "fakeshop" / "db.sqlite3")},
        "cell": "default",
        "exit": None,
        "copy_edits": list[str](),
        "shared_moves": list[str](),
    }
    _write(layout.run_log, json.dumps(unresolved) + "\n")
    record = _write(tmp_path / "rev.md", "Proof: review-20260924T120000-aaaaaa.\n")

    lines, ok = workspace.audit_record(layout.repo_root, record)

    assert ok is False
    assert lines[1].startswith("  FAIL review-20260924T120000-aaaaaa: review/pkg/a.py/perf-1")
    assert "exit=None" in lines[1]
    assert lines[1].endswith("[no package `__file__` was recorded]")


def test_audit_refuses_a_run_log_line_missing_a_field(
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A line without every field the audit reads is a malformed log, not a passing run."""

    def _layout_base(_root: Path) -> Path:
        return layout.base

    monkeypatch.setattr(workspace, "workspace_base", _layout_base)
    partial = {"run_id": "review-20260924T120000-aaaaaa", "address": "review/pkg/a.py/perf-1"}
    _write(layout.run_log, json.dumps(partial) + "\n")
    record = _write(tmp_path / "rev.md", "Proof: review-20260924T120000-aaaaaa.\n")

    with pytest.raises(workspace.WorkspaceError, match="a run log line has an unexpected shape"):
        workspace.audit_record(layout.repo_root, record)


# --------------------------------------------------------------------------------------------
# Postgres identity and database matching
# --------------------------------------------------------------------------------------------


def test_postgres_finds_the_fakeshop_container_by_identity_not_port(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    inspect = [
        {
            "Id": "aaaaaaaaaaaa1111",
            "Config": {
                "Env": ["POSTGRES_USER=medtrics", "POSTGRES_DB=medtrics"],
                "Labels": dict[str, str](),
            },
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostPort": "2345"}]}},
        },
        {
            "Id": "bbbbbbbbbbbb2222",
            "Config": {
                "Env": ["POSTGRES_USER=fakeshop", "POSTGRES_DB=fakeshop"],
                "Labels": {"com.docker.compose.project": workspace.COMPOSE_PROJECT},
            },
            "NetworkSettings": {"Ports": {"5432/tcp": [{"HostPort": "5432"}]}},
        },
    ]
    answers = {"ps": "aaaaaaaaaaaa\nbbbbbbbbbbbb\n", "inspect": json.dumps(inspect)}
    postgres = workspace.Postgres(tmp_path)

    def _answer(*args: str, **_kw: object) -> str:
        return answers[args[0]]

    monkeypatch.setattr(postgres, "_docker", _answer)

    assert postgres.find() == ("bbbbbbbbbbbb", "5432", workspace.COMPOSE_PROJECT)


def test_postgres_exact_match_never_takes_slot10_for_slot1(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    names = [
        "postgres",
        "ws_abc_review_slot1",
        "ws_abc_review_slot10",
        "ws_other_review_slot1",
        "test_ws_abc_review_slot1",
        "test_ws_abc_review_slot1_gw0",
        "test_ws_abc_review_slot10",
    ]
    rows = "\n".join([*names, ""])
    postgres = workspace.Postgres(tmp_path)

    def _canned_sql(_statement: str, _database: str = "postgres") -> str:
        return rows

    monkeypatch.setattr(postgres, "sql", _canned_sql)

    assert postgres.databases("ws_abc_review_slot1", exact=True) == [
        "ws_abc_review_slot1",
        "test_ws_abc_review_slot1",
        "test_ws_abc_review_slot1_gw0",
    ]
    assert postgres.databases("ws_abc_review_slot1") == [
        "ws_abc_review_slot1",
        "ws_abc_review_slot10",
        "test_ws_abc_review_slot1",
        "test_ws_abc_review_slot1_gw0",
        "test_ws_abc_review_slot10",
    ]


# --------------------------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------------------------


def test_gate_copy_git_lists_what_the_shared_tree_lists_and_reports_its_changes(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo / "untracked.py", "NEW = 1\n")
    _write(repo / PACKAGE / "core.py", "CORE = 'dirty'\n")
    gate_dir = tmp_path / "gate"
    workspace.mirror_tree(repo, gate_dir, preserved=workspace.PRESERVED | {".git"})

    head = workspace.build_gate_git(repo, gate_dir)

    assert head == _git(repo, "rev-parse", "HEAD").strip()
    assert _git(gate_dir, "ls-files", "-co", "--exclude-standard") == _git(
        repo,
        "ls-files",
        "-co",
        "--exclude-standard",
    )
    assert _git(gate_dir, "status", "--short") == _git(repo, "status", "--short")


def test_the_lint_gate_suite_runs_the_ci_lint_job_commands_in_order() -> None:
    """``gate``'s lint suite is the ``lint`` job of ``django.yml``, command for command.

    Every ``run:`` line of that job past its setup (``uv python install``,
    ``uv sync``) is a ``uv run`` command, and the suite runs each one without the
    prefix, in the workflow's order; a step added to the workflow and not here
    would let a gate pass that CI fails.
    """
    lines = _run_lines(_django_workflow_job("lint"))
    setup = [line for line in lines if line.startswith("uv python install") or line == "uv sync"]
    commands = [line for line in lines if line not in setup]

    assert len(setup) == 2
    assert all(line.startswith("uv run ") for line in commands)
    assert tuple(line.removeprefix("uv run ") for line in commands) == workspace.LINT_COMMANDS
    arguments, cell = workspace.GATE_SUITES["lint"]
    assert arguments == ("sh", "-exc", "\n".join(workspace.LINT_COMMANDS))
    assert cell == "default"


def _django_workflow_job(name: str) -> dict[object, object]:
    """The ``name`` job of ``django.yml``, as the YAML loader reads it."""
    workflow = workspace.REPO_ROOT / ".github" / "workflows" / "django.yml"
    document = object_result(yaml.safe_load, workflow.read_text(encoding="utf-8"))
    return json_object(document, "jobs", name)


def _run_lines(job: dict[object, object]) -> list[str]:
    """Every non-blank line of the ``run:`` steps of ``job``, in order."""
    return [
        line.strip()
        for step in json_list(job, "steps")
        for line in str(json_object(step).get("run", "")).splitlines()
        if line.strip()
    ]


def _ci_floor_node() -> tuple[dict[object, object], list[str]]:
    """The push/PR compatibility node of ``django.yml``'s ``test`` job and its ``run:`` lines."""
    job = _django_workflow_job("test")
    include = json_at(job, "strategy", "matrix", "include")
    assert isinstance(include, str), include
    lists: list[str] = re.findall(r"fromJSON\('(\[.*?\])'\)", include, re.DOTALL)
    push_nodes = json_list(json_loads(lists[-1]))
    floor = [
        node for node in map(json_object, push_nodes) if node.get("compatibility_only") == "1"
    ]
    assert len(floor) == 1
    return floor[0], _run_lines(job)


def test_floor_pins_are_the_pyproject_lower_bounds(tmp_path: Path) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        "[project]\n"
        'requires-python = ">=3.10,<4.0"\n'
        "dependencies = [\n"
        '    "django>=5.2.16",\n'
        "    \"Strawberry_Graphql[debug] >= 0.322.2, <1 ; python_version >= '3.10'\",\n"
        '    "graphql-core>=3.2.0,<3.3",\n'
        "]\n",
    )

    assert workspace.floor_pins(pyproject) == {
        "python": "3.10",
        "Django": "5.2.16",
        "strawberry-graphql": "0.322.2",
    }


@pytest.mark.parametrize(
    ("dependencies", "match"),
    [
        ('"Django>=5.2.16"', "lists no strawberry-graphql"),
        ('"Django==5.2.16", "strawberry-graphql>=0.322.2"', "states no >= floor"),
    ],
)
def test_floor_pins_refuse_a_pyproject_without_a_floor(
    tmp_path: Path,
    dependencies: str,
    match: str,
) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        f'[project]\nrequires-python = ">=3.10"\ndependencies = [{dependencies}]\n',
    )

    with pytest.raises(workspace.WorkspaceError, match=match):
        workspace.floor_pins(pyproject)


def test_the_floor_pins_are_the_points_build_md_and_the_ci_floor_cell_state() -> None:
    """``pyproject.toml``'s lower bounds, BUILD.md's floor policy and CI's floor node agree.

    The gate reads its pins from ``pyproject.toml``; BUILD.md "Floor
    verification" records the exact point a floor run installs. Were the policy
    ever to name a point other than the lower bound, this row fails rather than
    the gate silently testing a different floor from CI.
    """
    pins = workspace.floor_pins(workspace.REPO_ROOT / "pyproject.toml")
    build = (workspace.REPO_ROOT / "docs" / "builder" / "BUILD.md").read_text(encoding="utf-8")
    stated = re.search(
        r"The supported floor is Django \*\*([^*]+)\*\* on Python \*\*([^*]+)\*\* "
        r"with strawberry-graphql \*\*([^*]+)\*\*",
        build,
    )
    node, _lines = _ci_floor_node()

    assert stated is not None
    assert stated.groups() == (pins["Django"], pins["python"], pins["strawberry-graphql"])
    assert (node["django"], node["python"], node["strawberry"]) == (
        pins["Django"],
        pins["python"],
        pins["strawberry-graphql"],
    )


def test_the_floor_gate_suite_installs_and_runs_what_the_ci_floor_cell_does(
    tmp_path: Path,
) -> None:
    """The floor suite is the ``test`` job's floor node: its install and its coverage-free run.

    That job syncs the lock at the floor Python, installs Django over it with
    ``--upgrade-package Django``, then strawberry-graphql, and runs pytest with
    ``addopts`` that drop ``--cov``; the suite does each of those against its
    own virtualenv and only adds ``-p no:cacheprovider``.
    """
    _node, lines = _ci_floor_node()
    ci_addopts: list[str] = re.findall(r'addopts="(-[^"]*)"', "\n".join(lines))
    pins = {"python": "3.10", "Django": "5.2.16", "strawberry-graphql": "0.322.2"}
    venv = tmp_path / "gate-floor"
    python = str(venv / "bin" / "python")

    commands = workspace.floor_install_commands(tmp_path / "gate", venv, pins)

    assert "uv sync --python ${{ matrix.python }}" in lines
    assert 'uv pip install --upgrade-package Django "Django==${{ matrix.django }}"' in lines
    assert 'uv pip install "strawberry-graphql==${{ matrix.strawberry }}"' in lines
    pip = [
        "uv",
        "pip",
        "install",
        "--directory",
        str(tmp_path / "gate"),
        "--python",
        python,
        "-q",
    ]
    assert commands == [
        [
            "uv",
            "sync",
            "--directory",
            str(tmp_path / "gate"),
            "--frozen",
            "--python",
            "3.10",
            "-q",
        ],
        [
            *pip,
            "--upgrade-package",
            "Django",
            "Django==5.2.16",
        ],
        [*pip, "strawberry-graphql==0.322.2"],
    ]
    arguments, cell = workspace.GATE_SUITES[workspace.FLOOR_SUITE]
    no_cov = [opts for opts in ci_addopts if "--cov" not in opts]
    assert len(no_cov) == 1
    assert arguments == (
        "pytest",
        "-p",
        "no:cacheprovider",
        "-o",
        f"addopts={no_cov[0]}",
    )
    assert cell == "default"
    assert list(workspace.GATE_SUITES)[:3] == ["lint", "default", "floor"]


def _gate_copy_inputs(layout: workspace.Layout, lock: str = "lock v1\n") -> None:
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.16", "strawberry-graphql>=0.322.2"]\n',
    )
    _write(layout.gate_dir / "uv.lock", lock)


def _record_installs(
    monkeypatch: pytest.MonkeyPatch,
    layout: workspace.Layout,
    fail_on: str | None = None,
) -> list[tuple[list[str], dict[str, str]]]:
    """Replace the build commands' subprocess layer; ``uv sync`` lays down the interpreter."""
    calls: list[tuple[list[str], dict[str, str]]] = []

    def _run_checked(command: list[str], env: dict[str, str], _holding: object = ()) -> None:
        calls.append((list(command), env))
        if fail_on is not None and fail_on in command:
            msg = f"{' '.join(command)} failed (1): no such release"
            raise workspace.WorkspaceError(msg)
        if command[:2] == ["uv", "sync"]:
            _write(layout.floor_venv / "bin" / "python", "interpreter\n")

    monkeypatch.setattr(workspace, "_run_checked", _run_checked)
    return calls


def test_the_floor_venv_is_built_once_and_rebuilt_when_its_inputs_move(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)

    built = workspace.ensure_floor_venv(layout)
    _write(layout.floor_venv / "lib" / "leftover.py", "x\n")
    reused = workspace.ensure_floor_venv(layout)

    assert built["reused"] is False
    assert built["pins"] == {"python": "3.10", "Django": "5.2.16", "strawberry-graphql": "0.322.2"}
    assert built["python"] == str(layout.floor_venv / "bin" / "python")
    assert [command[:3] for command, _env in calls] == [
        ["uv", "sync", "--directory"],
        ["uv", "pip", "install"],
        ["uv", "pip", "install"],
    ]
    assert all(env["UV_PROJECT_ENVIRONMENT"] == str(layout.floor_venv) for _c, env in calls)
    assert reused == {**built, "reused": True}
    assert len(calls) == 3

    _gate_copy_inputs(layout, lock="lock v2\n")
    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["reused"] is False
    assert rebuilt["key"] != built["key"]
    assert len(calls) == 6
    assert not (layout.floor_venv / "lib" / "leftover.py").exists()


def test_a_floor_pin_move_rebuilds_the_floor_venv(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)
    built = workspace.ensure_floor_venv(layout)
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.17", "strawberry-graphql>=0.322.2"]\n',
    )

    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["key"] != built["key"]
    assert calls[-2][0][-1] == "Django==5.2.17"


def test_a_failed_floor_build_writes_no_key_so_the_next_gate_rebuilds(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    _record_installs(monkeypatch, layout, fail_on="strawberry-graphql==0.322.2")

    with pytest.raises(workspace.WorkspaceError, match="no such release"):
        workspace.ensure_floor_venv(layout)
    assert (layout.floor_venv / "bin" / "python").exists()
    assert not (layout.floor_venv / workspace.FLOOR_KEY_NAME).exists()

    calls = _record_installs(monkeypatch, layout)
    again = workspace.ensure_floor_venv(layout)

    assert again["reused"] is False
    assert len(calls) == 3


def test_summarize_suite_reads_summary_collected_and_coverage() -> None:
    log = (
        "12 workers [3456 items]\n"
        "TOTAL                         9000      0   100%\n"
        "Required test coverage of 100% reached. Total coverage: 100.00%\n"
        "===== 3450 passed, 6 skipped in 88.12s (0:01:28) =====\n"
    )

    assert workspace.summarize_suite(log) == {
        "summary": "3450 passed, 6 skipped in 88.12s (0:01:28)",
        "collected": 3456,
        "coverage": [
            "TOTAL                         9000      0   100%",
            "Required test coverage of 100% reached. Total coverage: 100.00%",
        ],
    }


# --------------------------------------------------------------------------------------------
# Item diff
# --------------------------------------------------------------------------------------------


def _item_diff(root: Path, *paths: str) -> str:
    """Return the item diff since ``HEAD`` after checking its closing ``sha256`` line."""
    raw = workspace.item_diff(root, _git(root, "rev-parse", "HEAD").strip(), paths or (PACKAGE,))
    split = raw.rindex(b"sha256 ")
    body, seal = raw[:split], raw[split:]
    assert seal == f"sha256 {hashlib.sha256(body).hexdigest()}\n".encode()
    return raw.decode("utf-8")


def _headers(diff: str) -> list[str]:
    return [line for line in diff.splitlines() if line.startswith("diff --git ")]


def test_item_diff_carries_a_tracked_edit(repo: Path) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py"]
    assert "+CORE = 3" in diff


def test_item_diff_adds_an_untracked_file_exactly_once(repo: Path) -> None:
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/new.py b/{PACKAGE}/new.py"]
    assert "+NEW = 1" in diff


def test_item_diff_leaves_out_untracked_files_outside_the_paths_and_ignored_ones(
    repo: Path,
) -> None:
    _write(repo / "other" / "x.py", "X = 1\n")
    _write(repo / PACKAGE / "ignored.txt", "ignored\n")
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")

    assert _headers(_item_diff(repo)) == [f"diff --git a/{PACKAGE}/new.py b/{PACKAGE}/new.py"]


def test_item_diff_adds_a_staged_file_exactly_once(repo: Path) -> None:
    _write(repo / PACKAGE / "staged.py", "STAGED = 1\n")
    _git(repo, "add", f"{PACKAGE}/staged.py")

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/staged.py b/{PACKAGE}/staged.py"]
    assert "new file mode" in diff


def test_item_diff_carries_a_deletion(repo: Path) -> None:
    (repo / PACKAGE / "core.py").unlink()

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py"]
    assert "deleted file mode" in diff


def test_item_diff_carries_a_rename(repo: Path) -> None:
    _git(repo, "mv", f"{PACKAGE}/core.py", f"{PACKAGE}/renamed.py")

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/renamed.py"]
    assert f"rename to {PACKAGE}/renamed.py" in diff


def test_item_diff_orders_untracked_files_by_path_whatever_order_git_lists_them(
    repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("zeta", "alpha", "mid"):
        _write(repo / PACKAGE / f"{name}.py", f"{name.upper()} = 1\n")
    expected = _item_diff(repo)
    listed = workspace._git

    def _reversed_listing(root: Path, *args: str) -> str:
        output = listed(root, *args)
        if args[:1] != ("ls-files",):
            return output
        return "\0".join(reversed(output.rstrip("\0").split("\0"))) + "\0"

    monkeypatch.setattr(workspace, "_git", _reversed_listing)

    diff = _item_diff(repo)

    assert diff == expected
    assert _headers(diff) == [
        f"diff --git a/{PACKAGE}/{name}.py b/{PACKAGE}/{name}.py"
        for name in ("alpha", "mid", "zeta")
    ]


def test_item_diff_gives_identical_bytes_from_two_clones_of_one_change(tmp_path: Path) -> None:
    origin = tmp_path / "origin"
    _write(origin / PACKAGE / "core.py", "CORE = 2\n")
    _write(origin / PACKAGE / "gone.py", "GONE = 1\n")
    _git(origin, "init", "-q")
    _git(origin, "add", "-A")
    _git(origin, "commit", "-q", "-m", "initial")
    diffs: list[str] = []
    for name in ("first-copy", "second"):
        clone = tmp_path / name
        _git(tmp_path, "clone", "-q", str(origin), str(clone))
        _write(clone / PACKAGE / "core.py", "CORE = 3\n")
        _write(clone / PACKAGE / "staged.py", "STAGED = 1\n")
        _git(clone, "add", f"{PACKAGE}/staged.py")
        (clone / PACKAGE / "gone.py").unlink()
        _write(clone / PACKAGE / "new.py", "NEW = 1\n")
        diffs.append(_item_diff(clone))

    assert diffs[0] == diffs[1]
    assert len(_headers(diffs[0])) == 4


def test_diff_check_passes_on_the_written_diff_and_fails_once_the_tree_moves(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(workspace, "REPO_ROOT", repo)
    baseline = _git(repo, "rev-parse", "HEAD").strip()
    record = tmp_path / "pass-1.diff"
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    command = [
        "diff",
        baseline,
        "--output",
        str(record),
        "--",
        PACKAGE,
    ]

    assert workspace.main(command) == 0
    assert (
        workspace.main(
            [
                "diff",
                baseline,
                "--check",
                str(record),
                "--",
                PACKAGE,
            ],
        )
        == 0
    )
    _write(repo / PACKAGE / "new.py", "NEW = 2\n")
    capsys.readouterr()

    assert (
        workspace.main(
            [
                "diff",
                baseline,
                "--check",
                str(record),
                "--",
                PACKAGE,
            ],
        )
        == 1
    )
    assert "does not match the tree" in capsys.readouterr().out


def test_diff_refuses_an_empty_path_list(repo: Path) -> None:
    with pytest.raises(workspace.WorkspaceError):
        workspace.item_diff(repo, "HEAD", ())


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


def test_run_refuses_a_uv_command_with_the_refusal_exit_code(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        workspace.main(
            [
                "run",
                "review/pkg/a.py/perf-1",
                "--cell",
                "pg",
                "--",
                "uv",
                "run",
                "x",
            ],
        )
        == 125
    )

    assert "follows `uv run`" in capsys.readouterr().err


def test_run_refuses_a_missing_command() -> None:
    assert workspace.main(["run", "review/pkg/a.py/perf-1"]) == workspace.REFUSED


def test_only_run_and_prove_take_a_command_after_the_separator() -> None:
    with pytest.raises(SystemExit):
        workspace.main(
            [
                "baseline",
                "review/pkg/a.py",
                "--",
                "x",
            ],
        )


# --------------------------------------------------------------------------------------------
# Stop signals
# --------------------------------------------------------------------------------------------

# Spelled out rather than read from the script, so a signal dropped there fails its rows.
STOP_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
    signal.SIGHUP,
    signal.SIGQUIT,
)

# Stands in for ``uv run <command>``: it writes ``<pid> <pgid> <grandchild pid>`` to
# ``S_READY`` once it has started a grandchild (uv -> pytest -> xdist worker), appends the
# name of every stop signal it gets to ``<S_READY>.got`` and blocks until
# ``<S_READY>.release`` exists, then prints ``released`` and exits 0. ``S_ON_STOP=teardown``
# makes a stop take a second, print ``torn down`` and exit 3, as pytest's teardown does;
# ``count`` only records it; ``hang`` records the first and exits 4 on the second, as pytest
# does on a second Ctrl-C during a teardown that hangs; ``ignore`` leaves every stop signal as
# the command inherited it.
_COMMAND = """
import os, signal, subprocess, sys, time
from pathlib import Path

ready = Path(os.environ["S_READY"])
mode = os.environ["S_ON_STOP"]
stops = []


def stopped(signum, _frame):
    stops.append(signum)
    with open(str(ready) + ".got", "a", encoding="utf-8") as got:
        got.write(signal.Signals(signum).name + "\\n")
    if mode == "teardown":
        time.sleep(1)
        print("torn down", flush=True)
        sys.exit(3)
    if mode == "hang" and len(stops) == 2:
        print("stopped twice", flush=True)
        sys.exit(4)


if mode != "ignore":
    for stop_signal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        signal.signal(stop_signal, stopped)
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
ready.with_suffix(".tmp").write_text(f"{os.getpid()} {os.getpgid(0)} {child.pid}")
os.replace(ready.with_suffix(".tmp"), ready)
release = Path(str(ready) + ".release")
deadline = time.monotonic() + 30
while not release.exists() and time.monotonic() < deadline:
    time.sleep(0.02)
child.kill()
print("released", flush=True)
"""

# Runs the real ``stream`` in a process of its own, as ``run`` does, holding an ``flock`` on
# ``S_LOCK`` it hands the command, and writes what ``stream`` returned to ``S_RESULT``.
# ``starting`` signals the process itself as the command is being started, before the fork;
# ``started`` signals it once the command has started, before ``stream`` has recorded it;
# ``sink-stdout`` and ``sink-stderr`` point that stream at a pipe whose reader has gone.
_STREAM_RUN = """
import json, os, signal, subprocess, sys
from pathlib import Path

from scripts import workspace

mode = os.environ["S_MODE"]
signum = int(os.environ["S_SIGNUM"])
if mode in {"starting", "started"}:

    class SignalledPopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            if mode == "starting":
                os.kill(os.getpid(), signum)
            super().__init__(*args, **kwargs)
            if mode == "started":
                os.kill(os.getpid(), signum)

    subprocess.Popen = SignalledPopen
if mode.startswith("sink-"):
    reader, writer = os.pipe()
    os.close(reader)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    setattr(sys, mode[len("sink-") :], os.fdopen(writer, "w"))
command = [sys.executable, "-c", os.environ["S_COMMAND"]]
with workspace.file_lock(Path(os.environ["S_LOCK"])) as held:
    finished = workspace.stream(
        command,
        dict(os.environ),
        Path(os.environ["S_LOG"]),
        "header\\n",
        holding=(held,),
    )
Path(os.environ["S_RESULT"]).write_text(json.dumps([finished.code, finished.stopped_by]))
"""

# Sets ``S_SIGNUM`` to ``SIG_IGN`` and execs the rest of its argv under a fresh interpreter,
# which inherits the ignored disposition as a process started under ``nohup`` does.
_IGNORING_EXEC = """
import os, signal, sys

signal.signal(int(os.environ["S_SIGNUM"]), signal.SIG_IGN)
os.execv(sys.executable, [sys.executable, *sys.argv[1:]])
"""

# Writes 2 MB to ``S_STREAM`` (``stdout`` or ``stderr``), far past what a pipe buffers.
_FLOOD = """
import os, sys

out = getattr(sys, os.environ["S_STREAM"])
for _ in range(20000):
    out.write("x" * 99 + "\\n")
"""

# Stands in for ``uv`` on ``PATH``: ``uv run ... -- <command>`` becomes ``<command>``;
# ``uv sync`` writes its pid to ``WSTEST_SYNC`` and blocks until ``<WSTEST_SYNC>.release``.
_UV = """
import os, sys, time
from pathlib import Path

arguments = sys.argv[1:]
if arguments[0] == "sync":
    ready = Path(os.environ["WSTEST_SYNC"])
    ready.write_text(str(os.getpid()))
    release = Path(str(ready) + ".release")
    deadline = time.monotonic() + 30
    while not release.exists() and time.monotonic() < deadline:
        time.sleep(0.02)
    sys.exit(0)
command = arguments[arguments.index("--") + 1 :]
os.execvp(command[0], command)
"""


# Stands in for a job-control shell on the terminal it was started on (stdin): it makes that
# terminal its own, runs its argv as a job in a process group of its own in the foreground,
# and appends ``job <pid>``, then ``stopped`` each time the job stops, and ``exited <code>`` to
# ``argv[1]``. ``fg`` is the file ``<argv[1]>.fg``: the shell gives the job the terminal back
# and continues it, as ``fg`` does.
_JOB_SHELL = """
import fcntl, os, signal, subprocess, sys, termios, time
from pathlib import Path

report = Path(sys.argv[1])
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
for job_signal in (signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU):
    signal.signal(job_signal, signal.SIG_IGN)


def as_job():
    os.setpgid(0, 0)
    for job_signal in (signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU):
        signal.signal(job_signal, signal.SIG_DFL)


job = subprocess.Popen(sys.argv[2:], preexec_fn=as_job)
os.tcsetpgrp(0, job.pid)
with report.open("a", encoding="utf-8") as out:
    out.write(f"job {job.pid}\\n")
fg = Path(str(report) + ".fg")
while True:
    _, status = os.waitpid(job.pid, os.WUNTRACED)
    if os.WIFSTOPPED(status):
        with report.open("a", encoding="utf-8") as out:
            out.write("stopped\\n")
        deadline = time.monotonic() + 30
        while not fg.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        fg.unlink()
        os.tcsetpgrp(0, job.pid)
        os.killpg(job.pid, signal.SIGCONT)
        continue
    with report.open("a", encoding="utf-8") as out:
        out.write(f"exited {os.waitstatus_to_exitcode(status)}\\n")
    break
"""

# Stands in for a command that beats: as ``_COMMAND``, but it appends a line to
# ``<S_READY>.beats`` every 20 ms until released.
_BEATING = """
import os, time
from pathlib import Path

ready = Path(os.environ["S_READY"])
ready.with_suffix(".tmp").write_text(f"{os.getpid()} {os.getpgid(0)} {os.getpid()}")
os.replace(ready.with_suffix(".tmp"), ready)
release = Path(str(ready) + ".release")
deadline = time.monotonic() + 30
while not release.exists() and time.monotonic() < deadline:
    with open(str(ready) + ".beats", "a", encoding="utf-8") as beats:
        beats.write("beat\\n")
    time.sleep(0.02)
print("released", flush=True)
"""

# Stands in for a command that leaves a process holding its output and exits at once:
# ``bash -c 'sleep 30 & echo started'``, writing ``<pid> <pgid> <sleep pid>`` to ``S_READY``.
_LEAVING = """
import os

os.execvp(
    "bash",
    [
        "bash",
        "-c",
        'sleep 30 & echo "$$ $$ $!" > "$S_READY.tmp"; mv "$S_READY.tmp" "$S_READY"; echo started',
    ],
)
"""


class _StreamRun:
    """One real ``stream`` in its own process, its stand-in command, and what each left."""

    def __init__(
        self,
        tmp_path: Path,
        *,
        mode: str = "external",
        on_stop: str = "teardown",
        signum: int = signal.SIGTERM,
        ignored: bool = False,
        command: str = _COMMAND,
        stream: str = "stdout",
        tty: int | None = None,
    ) -> None:
        self.tmp_path = tmp_path
        self.shell = tmp_path / "shell"
        self.ready = tmp_path / "ready"
        self.lock = tmp_path / "copy.lock"
        self.log = tmp_path / "run.log"
        self.result = tmp_path / "result.json"
        environment = {
            **os.environ,
            "PYTHONPATH": str(Path(workspace.__file__).resolve().parents[1]),
            "S_MODE": mode,
            "S_ON_STOP": on_stop,
            # ``int`` first: on Python 3.10 ``str`` of a ``Signals`` member is ``Signals.SIGTERM``.
            "S_SIGNUM": str(int(signum)),
            "S_COMMAND": command,
            "S_STREAM": stream,
            "S_READY": str(self.ready),
            "S_LOCK": str(self.lock),
            "S_LOG": str(self.log),
            "S_RESULT": str(self.result),
        }
        argv = [sys.executable, "-c", _STREAM_RUN]
        if ignored:
            argv = [
                sys.executable,
                "-c",
                _IGNORING_EXEC,
                *argv[1:],
            ]
        if tty is not None:
            # A job of a shell on the terminal ``tty``, Ctrl-Z and ``fg`` included.
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    _JOB_SHELL,
                    str(self.shell),
                    *argv,
                ],
                env=environment,
                stdin=tty,
                stdout=tty,
                stderr=tty,
                start_new_session=True,
            )
            return
        self.process = subprocess.Popen(
            argv,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

    def pids(self) -> list[int]:
        """Return the command's pid, its process group and its grandchild's pid, once started."""
        assert _poll(self.ready.exists), "the command never started"
        return [int(pid) for pid in self.ready.read_text(encoding="utf-8").split()]

    def got(self) -> list[str]:
        return _stops_got(self.tmp_path)

    def beats(self) -> int:
        beats = self.tmp_path / "ready.beats"
        return len(beats.read_text(encoding="utf-8").split()) if beats.exists() else 0

    def shell_said(self) -> list[str]:
        return self.shell.read_text(encoding="utf-8").splitlines() if self.shell.exists() else []

    def release(self) -> None:
        (self.tmp_path / "ready.release").touch()

    def finish(self, timeout: float = 30) -> tuple[object, object]:
        """Return the code and stop signal ``stream`` returned; fail on a run that never ends."""
        try:
            _ = self.process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            self.process.kill()
            pytest.fail("the run never finished")
        code, stopped_by = json_list(json_loads(self.result.read_text(encoding="utf-8")))
        return code, stopped_by

    def kill(self) -> None:
        """Kill whatever a failed row left running, so it cannot outlive the row."""
        self.release()
        if self.process.poll() is None:
            self.process.kill()
        _ = self.process.communicate()
        for line in self.shell_said():
            if line.startswith("job ") and _is_running(int(line.split()[1])):
                os.kill(int(line.split()[1]), signal.SIGKILL)
        if self.ready.exists():
            for pid in self.pids()[::2]:
                if _is_running(pid):
                    os.kill(pid, signal.SIGKILL)


def _stops_got(tmp_path: Path) -> list[str]:
    """Return the name of every stop signal the stand-in command got, in order."""
    got = tmp_path / "ready.got"
    return got.read_text(encoding="utf-8").split() if got.exists() else []


def _poll(predicate: Callable[[], bool], seconds: float = 20) -> bool:
    """Return whether ``predicate`` became true within ``seconds``."""
    deadline = time.monotonic() + seconds
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.02)
    return True


def _is_running(pid: int) -> bool:
    """Return whether ``pid`` is a process that has not exited (a zombie has exited)."""
    state = subprocess.run(
        [
            "ps",
            "-o",
            "stat=",
            "-p",
            str(pid),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return bool(state) and not state.startswith("Z")


def _lock_is_held(path: Path) -> bool:
    try:
        with workspace.file_lock(path, blocking=False):
            return False
    except workspace.LockBusyError:
        return True


def _gc_refused(layout: workspace.Layout) -> bool:
    try:
        _ = workspace.gc(layout)
    except workspace.LockBusyError:
        return True
    return False


@pytest.fixture
def stream_runs() -> Iterator[list[_StreamRun]]:
    runs: list[_StreamRun] = []
    yield runs
    for run in runs:
        run.kill()


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_stop_signal_to_the_run_alone_reaches_the_whole_command_and_the_run_outlives_it(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
    signum: signal.Signals,
) -> None:
    run = _StreamRun(tmp_path)
    stream_runs.append(run)
    command, group, grandchild = run.pids()

    os.kill(run.process.pid, signum)

    assert _poll(lambda: not _is_running(grandchild))
    assert group == command != os.getpgid(run.process.pid)
    assert run.got() == [signum.name]
    # The command is tearing down: the run still holds its lease and waits for it.
    assert _is_running(run.process.pid)
    assert _lock_is_held(run.lock)
    assert run.finish() == (3, signum)
    assert not _is_running(command)
    assert not _lock_is_held(run.lock)
    assert run.log.read_text(encoding="utf-8").endswith("torn down\n")


def test_a_repeat_stop_inside_the_grace_is_dropped_and_a_later_one_is_relayed(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
) -> None:
    run = _StreamRun(tmp_path, on_stop="count")
    stream_runs.append(run)
    _ = run.pids()

    os.kill(run.process.pid, signal.SIGTERM)
    assert _poll(lambda: run.got() == ["SIGTERM"])
    os.kill(run.process.pid, signal.SIGINT)
    time.sleep(workspace.STOP_REPEAT_GRACE + 0.3)
    os.kill(run.process.pid, signal.SIGINT)
    assert _poll(lambda: len(run.got()) >= 2)
    run.release()

    assert run.finish() == (0, signal.SIGTERM)
    # A relayed repeat would sit between the two: the command gets its signals in order.
    assert run.got() == ["SIGTERM", "SIGINT"]


def test_a_second_stop_after_the_grace_reaches_a_command_whose_teardown_hangs(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
) -> None:
    # pytest ends on a second Ctrl-C during a teardown that hangs; the run passes it on.
    run = _StreamRun(tmp_path, on_stop="hang")
    stream_runs.append(run)
    _ = run.pids()

    os.kill(run.process.pid, signal.SIGTERM)
    assert _poll(lambda: run.got() == ["SIGTERM"])
    time.sleep(workspace.STOP_REPEAT_GRACE + 0.3)
    os.kill(run.process.pid, signal.SIGTERM)

    assert run.finish(timeout=10) == (4, signal.SIGTERM)
    assert run.got() == ["SIGTERM", "SIGTERM"]


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_stop_signal_the_run_inherited_as_ignored_stays_ignored_and_stops_nothing(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
    signum: signal.Signals,
) -> None:
    run = _StreamRun(tmp_path, signum=signum, ignored=True)
    stream_runs.append(run)
    _ = run.pids()

    os.kill(run.process.pid, signum)
    # Then, past the grace, a stop the run does relay: a relayed ``signum`` would show before it.
    time.sleep(workspace.STOP_REPEAT_GRACE + 0.3)
    other = signal.SIGTERM if signum != signal.SIGTERM else signal.SIGHUP
    os.kill(run.process.pid, other)

    assert run.finish() == (3, other)
    assert run.got() == [other.name]


@pytest.mark.parametrize("mode", ["starting", "started"])
def test_a_stop_before_the_command_is_recorded_reaches_it_once_it_is(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
    mode: str,
) -> None:
    run = _StreamRun(
        tmp_path,
        mode=mode,
        signum=signal.SIGHUP,
        command="import time; time.sleep(25)",
    )
    stream_runs.append(run)

    # The command died by the relayed signal, read as ``128 + N``, long before its sleep ended.
    assert run.finish(timeout=10) == (128 + signal.SIGHUP, signal.SIGHUP)


def test_a_killed_stream_leaves_its_lock_held_while_its_command_runs(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
) -> None:
    run = _StreamRun(tmp_path)
    stream_runs.append(run)
    command, _group, _grandchild = run.pids()

    run.process.kill()
    _ = run.process.wait()

    assert _is_running(command)
    assert _lock_is_held(run.lock)
    run.release()
    assert _poll(lambda: not _is_running(command))
    assert _poll(lambda: not _lock_is_held(run.lock))


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_a_reader_gone_from_the_run_keeps_the_log_and_never_blocks_the_command(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
    stream: str,
) -> None:
    # ``workspace.py run ... | head``, or a closed terminal: the echo fails, the log does not.
    run = _StreamRun(tmp_path, mode=f"sink-{stream}", command=_FLOOD, stream=stream)
    stream_runs.append(run)

    assert run.finish(timeout=15) == (0, None)
    assert run.log.stat().st_size == len("header\n") + 20000 * 100


def _is_stopped(pid: int) -> bool:
    state = subprocess.run(
        [
            "ps",
            "-o",
            "stat=",
            "-p",
            str(pid),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return state.startswith("T")


def _drain(master: int, done: threading.Event) -> None:
    """Read the terminal's output until ``done``, so nothing writing to it ever blocks.

    It never blocks in a read: closing a descriptor another thread is reading
    can hang on macOS while a process still holds the terminal.
    """
    with contextlib.suppress(OSError):
        while not done.is_set():
            if select.select([master], [], [], 0.05)[0]:
                _ = os.read(master, 1 << 16)


@pytest.fixture
def terminal() -> Iterator[tuple[int, int]]:
    """A pseudo-terminal: its master side, read until the row ends, and its terminal side.

    Rows take it before ``stream_runs``, so whatever a row left holding the
    terminal is killed before the terminal closes.
    """
    master, tty = os.openpty()
    done = threading.Event()
    drain = threading.Thread(target=_drain, args=(master, done), daemon=True)
    drain.start()
    yield master, tty
    done.set()
    drain.join()
    os.close(tty)
    os.close(master)


@pytest.mark.parametrize("ignored", [None, signal.SIGCONT], ids=["plain", "sigcont-ignored"])
def test_ctrl_z_suspends_the_command_with_the_run_and_fg_continues_both(
    tmp_path: Path,
    terminal: tuple[int, int],
    stream_runs: list[_StreamRun],
    ignored: signal.Signals | None,
) -> None:
    # With ``SIGCONT`` inherited as ignored the run still continues, and must continue its group.
    master, tty = terminal
    run = _StreamRun(
        tmp_path,
        command=_BEATING,
        tty=tty,
        signum=ignored or signal.SIGTERM,
        ignored=ignored is not None,
    )
    stream_runs.append(run)
    command, _, _ = run.pids()
    assert _poll(lambda: run.beats() > 3)

    _ = os.write(master, b"\x1a")  # Ctrl-Z

    assert _poll(lambda: "stopped" in run.shell_said())
    assert _poll(lambda: _is_stopped(command))
    stopped_at = run.beats()
    time.sleep(0.5)
    assert run.beats() == stopped_at
    Path(f"{run.shell}.fg").touch()  # fg
    assert _poll(lambda: run.beats() > stopped_at + 3)
    assert not _is_stopped(command)
    run.release()

    assert _poll(lambda: "exited 0" in run.shell_said())
    assert json_list(json_loads(run.result.read_text(encoding="utf-8"))) == [0, None]
    assert run.log.read_text(encoding="utf-8").endswith("released\n")


def test_ctrl_z_the_run_inherited_as_ignored_stays_ignored_and_stops_nothing(
    tmp_path: Path,
    terminal: tuple[int, int],
    stream_runs: list[_StreamRun],
) -> None:
    master, tty = terminal
    run = _StreamRun(tmp_path, command=_BEATING, tty=tty, signum=signal.SIGTSTP, ignored=True)
    stream_runs.append(run)
    command, _, _ = run.pids()
    assert _poll(lambda: run.beats() > 3)

    _ = os.write(master, b"\x1a")  # Ctrl-Z

    beats = run.beats()
    assert _poll(lambda: run.beats() > beats + 25)
    assert not _is_stopped(command)
    assert "stopped" not in run.shell_said()
    run.release()
    assert _poll(lambda: "exited 0" in run.shell_said())
    assert json_list(json_loads(run.result.read_text(encoding="utf-8"))) == [0, None]


def test_a_continue_to_the_run_alone_continues_its_stopped_command(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
) -> None:
    run = _StreamRun(tmp_path, command=_BEATING)
    stream_runs.append(run)
    command, group, _ = run.pids()
    assert _poll(lambda: run.beats() > 3)
    # Only the command's own group: never this test's (a run that shared it would stop it too).
    assert group == command != os.getpgrp()
    os.killpg(group, signal.SIGSTOP)
    assert _poll(lambda: _is_stopped(command))
    stopped_at = run.beats()

    os.kill(run.process.pid, signal.SIGCONT)

    assert _poll(lambda: run.beats() > stopped_at + 3)
    run.release()
    assert run.finish() == (0, None)


def test_a_stop_after_the_command_exits_reaches_what_it_left_holding_its_output(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
) -> None:
    run = _StreamRun(tmp_path, command=_LEAVING)
    stream_runs.append(run)
    command, _, leftover = run.pids()
    # The command has exited; its ``sleep`` holds the output, so the run waits on it.
    assert _poll(lambda: not _is_running(command))
    assert _is_running(leftover)
    assert run.process.poll() is None

    os.kill(run.process.pid, signal.SIGTERM)

    assert _poll(lambda: not _is_running(leftover), 5)
    assert run.finish(timeout=5) == (0, signal.SIGTERM)
    assert run.log.read_text(encoding="utf-8").endswith("started\n")


@pytest.fixture
def stand_in_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Put ``_UV`` on the actors' ``PATH`` and point ``_COMMAND`` at ``tmp_path``.

    Yields the folder it lives in; afterwards kills whatever the command or ``uv sync``
    left running, so a failed row cannot outlive the row.
    """
    folder = tmp_path / "bin"
    uv = _write(folder / "uv", f"#!{sys.executable}\n{_UV}")
    uv.chmod(0o755)
    monkeypatch.setenv("S_READY", str(tmp_path / "ready"))
    monkeypatch.setenv("S_ON_STOP", "count")
    monkeypatch.setenv("WSTEST_SYNC", str(tmp_path / "sync-ready"))
    yield folder
    (tmp_path / "ready.release").touch()
    (tmp_path / "sync-ready.release").touch()
    pids: list[int] = []
    if (tmp_path / "ready").exists():
        pids += [int(pid) for pid in (tmp_path / "ready").read_text(encoding="utf-8").split()][::2]
    if (tmp_path / "sync-ready").exists():
        pids.append(int((tmp_path / "sync-ready").read_text(encoding="utf-8")))
    for pid in pids:
        if _is_running(pid):
            os.kill(pid, signal.SIGKILL)


def _run_record(layout: workspace.Layout) -> dict[object, object]:
    (record,) = [json_object(json_loads(line)) for line in layout.run_log.read_text().splitlines()]
    return record


def test_a_stopped_run_keeps_its_leases_until_its_command_ends_then_records_the_stop(
    layout: workspace.Layout,
    actors: _Actors,
    stand_in_uv: Path,
    tmp_path: Path,
) -> None:
    command = (
        "--",
        sys.executable,
        "-c",
        _COMMAND,
    )
    actors.start("A", "run", _ADDRESS, *command, bin=str(stand_in_uv), real_stream=True)
    assert _poll((tmp_path / "ready").exists)
    process = actors.processes["A"]

    # A non-TTY Ctrl-C under ``uv run python scripts/workspace.py``: the group's SIGINT, then
    # uv's forward of it 200 ms later. A stop after the grace is relayed.
    os.kill(process.pid, signal.SIGINT)
    assert _poll(lambda: _stops_got(tmp_path) == ["SIGINT"])
    time.sleep(0.2)
    os.kill(process.pid, signal.SIGINT)
    time.sleep(workspace.STOP_REPEAT_GRACE + 0.3)
    os.kill(process.pid, signal.SIGTERM)
    assert _poll(lambda: len(_stops_got(tmp_path)) >= 2)
    refused = _gc_refused(layout)
    (tmp_path / "ready.release").touch()
    code, _out, err = actors.finish("A")

    assert _stops_got(tmp_path) == ["SIGINT", "SIGTERM"]
    assert refused
    assert code == 128 + signal.SIGINT
    record = _run_record(layout)
    assert (record["exit"], record["stopped_by"]) == (0, "SIGINT")
    assert err.rstrip().endswith(f"exit 0 in {record['seconds']}s, stopped by SIGINT")


def test_a_killed_run_keeps_its_flow_and_copy_leased_until_its_command_ends(
    layout: workspace.Layout,
    actors: _Actors,
    stand_in_uv: Path,
    tmp_path: Path,
) -> None:
    command = (
        "--",
        sys.executable,
        "-c",
        _COMMAND,
    )
    actors.start("A", "run", _ADDRESS, *command, bin=str(stand_in_uv), real_stream=True)
    assert _poll((tmp_path / "ready").exists)
    pid = int((tmp_path / "ready").read_text(encoding="utf-8").split()[0])

    actors.processes["A"].kill()
    assert actors.finish("A")[0] == -signal.SIGKILL
    actors.run("B")

    assert _is_running(pid)
    assert _gc_refused(layout)
    with pytest.raises(workspace.LockBusyError):
        _ = workspace.release(layout, "pkg/a.py")
    assert workspace.running_slots(layout, ["slot-1"]) == ["slot-1"]
    assert actors.reached("B", "bound")
    assert not actors.reached("B", "in", within=0.5)
    (tmp_path / "ready.release").touch()
    assert actors.finish("B")[0] == 0
    assert _poll(lambda: not _gc_refused(layout))


def test_a_killed_sync_keeps_its_flow_and_copy_leased_until_uv_sync_ends(
    layout: workspace.Layout,
    actors: _Actors,
    stand_in_uv: Path,
    tmp_path: Path,
) -> None:
    sync = tmp_path / "sync-ready"
    actors.run("A", bin=str(stand_in_uv), real_sync=True)
    assert _poll(sync.exists)
    pid = int(sync.read_text(encoding="utf-8"))

    actors.processes["A"].kill()
    assert actors.finish("A")[0] == -signal.SIGKILL

    assert _is_running(pid)
    assert _gc_refused(layout)
    with pytest.raises(workspace.LockBusyError):
        _ = workspace.release(layout, "pkg/a.py")
    (tmp_path / "sync-ready.release").touch()
    assert _poll(lambda: not _gc_refused(layout))


def test_each_floor_install_holds_the_locks_the_gate_holds(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    held: list[object] = []

    def _run_checked(command: list[str], _env: dict[str, str], holding: object = ()) -> None:
        held.append(holding)
        if command[:2] == ["uv", "sync"]:
            _write(layout.floor_venv / "bin" / "python", "interpreter\n")

    monkeypatch.setattr(workspace, "_run_checked", _run_checked)

    _ = workspace.ensure_floor_venv(layout, (7, 8))

    assert held == [(7, 8)] * 3


def test_a_stopped_gate_runs_no_later_suite_and_ends_by_the_signal(
    layout: workspace.Layout,
    syncs: _Syncs,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in ("pyproject.toml", "uv.lock"):
        _ = _write(layout.repo_root / name, f"{name}\n")
    streamed: list[tuple[list[str], list[tuple[int, int]]]] = []

    def stopped_stream(
        command: list[str],
        _env: dict[str, str],
        log_path: Path,
        header: str,
        cwd: Path | None = None,
        *,
        holding: tuple[int, ...] = (),
    ) -> workspace.Finished:
        del cwd
        streamed.append((command, [(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in holding]))
        _ = _write(log_path, header)
        return workspace.Finished(128 + signal.SIGINT, signal.SIGINT)

    monkeypatch.setattr(workspace, "stream", stopped_stream)

    code = workspace.gate(layout, ["lint", "default"])

    out = capsys.readouterr().out
    assert code == 128 + signal.SIGINT
    assert syncs == [layout.gate_dir]
    ((command, holding),) = streamed
    assert command[-3:] == list(workspace.GATE_SUITES["lint"][0])
    # The copy's sync and the suite hold the flow's lease and the gate's lock.
    locks = [layout.flow_dir, layout.flow_dir / "gate.lock"]
    files = [(path.stat().st_dev, path.stat().st_ino) for path in locks]
    assert syncs.holding == [files]
    assert holding == files
    assert "  stopped by SIGINT; later suites did not run" in out
    (result_path,) = layout.evidence.glob("gate-*.json")
    result = json_object(json_loads(result_path.read_text(encoding="utf-8")))
    assert result["stopped_by"] == "SIGINT"
    assert list(json_object(result, "suites")) == ["lint"]


# Runs ``_cli`` with ``main`` returning ``W_CODE``, as the script's entry point does.
_CLI = """
import os

from scripts import workspace

workspace.main = lambda argv=None: int(os.environ["W_CODE"])
workspace._cli()
"""


@pytest.mark.parametrize(
    ("code", "returncode"),
    [
        (128 + signal.SIGTERM, -signal.SIGTERM),
        (128 + signal.SIGINT, -signal.SIGINT),
        (3, 3),
        (128 + signal.SIGKILL, 128 + signal.SIGKILL),
    ],
    ids=[
        "stopped-by-sigterm",
        "stopped-by-sigint",
        "plain-exit",
        "not-a-stop-signal",
    ],
)
def test_the_script_ends_by_the_stop_signal_that_stopped_its_run(
    code: int,
    returncode: int,
) -> None:
    completed = subprocess.run(
        [sys.executable, "-c", _CLI],
        env={
            **os.environ,
            "PYTHONPATH": str(Path(workspace.__file__).resolve().parents[1]),
            "W_CODE": str(code),
        },
        capture_output=True,
        check=False,
    )

    assert completed.returncode == returncode
