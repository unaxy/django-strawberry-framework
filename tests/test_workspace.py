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
import dataclasses
import errno
import fcntl
import hashlib
import io
import json
import os
import re
import select
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import BinaryIO, cast

import pytest
import yaml
from typing_extensions import override

from django_strawberry_framework.utils.typing import object_result
from scripts import prove_failability, workspace
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


@pytest.fixture(autouse=True)
def state_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point the proof state home into ``tmp_path``; the environment reaches child runs too."""
    home = tmp_path / "state-home"
    monkeypatch.setenv(prove_failability.STATE_HOME_ENV, str(home))
    return home


def _plant_proof_state(copy: Path) -> Path:
    """Leave what a proof run killed mid-mutation leaves for ``copy``: marker and pristine copy."""
    directory = prove_failability.tree_state_directory(copy.resolve())
    pristine = _write(
        directory / prove_failability.PRISTINE_DIRECTORY_NAME / "core.py.pristine",
        "old\n",
    )
    mutated = copy.resolve() / PACKAGE / "core.py"
    files = [{"mutated_file": str(mutated), "restore_from": str(pristine)}]
    _write(directory / prove_failability.ACTIVE_MARKER_NAME, json.dumps({"files": files}))
    return directory


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


@pytest.mark.parametrize("window", ["compare", "replace", "remove"])
def test_a_copy_file_the_purge_removes_after_its_check_reads_as_already_gone(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    window: str,
) -> None:
    copy = tmp_path / "copy"
    first = workspace.mirror_tree(repo, copy)
    victim = copy / PACKAGE / "core.py"
    if window == "compare":
        _run_once_after_checking(monkeypatch, Path, "is_dir", victim, victim.unlink)
    elif window == "replace":
        _write(victim, "CORE = 'dirtied by a probe'\n")
        _run_once_after_checking(monkeypatch, os.path, "lexists", victim, victim.unlink)
    else:
        victim = _write(copy / "extra.py", "leftover\n")
        real_walk = os.walk
        pending = [victim.unlink]

        def _walk(
            top: Path,
            *,
            topdown: bool = True,
        ) -> Iterator[tuple[str, list[str], list[str]]]:
            for listing in real_walk(top, topdown=topdown):
                if pending:
                    pending.pop()()
                yield listing

        monkeypatch.setattr(os, "walk", _walk)

    second = workspace.mirror_tree(repo, copy)

    assert workspace.tree_digest(second) == workspace.tree_digest(first)
    assert (copy / PACKAGE / "core.py").read_text(encoding="utf-8") == "CORE = 2\n"
    assert not (copy / "extra.py").exists()


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


@pytest.mark.parametrize(
    "how",
    [
        "first-bind",
        "rebind",
        "fresh",
        "reuse",
    ],
)
def test_a_resync_removes_its_copys_proof_state_and_leaves_every_other_copys(
    layout: workspace.Layout,
    syncs: _Syncs,
    how: str,
) -> None:
    # A proof killed mid-mutation leaves a marker that refuses every later proof in its copy;
    # a resync mirrors the shared tree's bytes over that mutation, so the marker goes with it.
    with workspace.lease(layout, _address("mech-1")) as other:
        pass
    kept = _plant_proof_state(other.directory)
    target = layout.slot_dir("slot-2")
    if how != "first-bind":
        with workspace.lease(layout, _address("perf-1")):
            pass
    if how == "rebind":
        assert workspace.release(layout, "pkg/a.py", roles=["perf-1"]) == [
            "slot-2 review/pkg/a.py/perf-1",
        ]
    planted = _plant_proof_state(target)
    role = "perf-2" if how == "rebind" else "perf-1"

    with workspace.lease(layout, _address(role), fresh=how == "fresh") as held:
        pass

    assert held.directory == target
    assert planted.exists() is (how == "reuse")
    assert syncs.count(target) == (1 if how in {"first-bind", "reuse"} else 2)
    assert (kept / prove_failability.ACTIVE_MARKER_NAME).is_file()


@pytest.mark.parametrize(
    "case",
    [
        "restored",
        "two-restored",
        "pristine-missing",
        "unreadable-marker",
        "copy-root",
    ],
)
def test_a_resync_restores_a_killed_proofs_venv_mutation_before_it_drops_the_marker(
    layout: workspace.Layout,
    syncs: _Syncs,
    case: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The mirror keeps ``.venv``, so a killed proof's mutation there survives the resync: the
    # marker's pristine copy is its only restore source and goes only once every file it names
    # there is restored. A marker that cannot be honoured is kept, never a failed resync.
    del syncs
    with workspace.lease(layout, _address("perf-1")) as held:
        pass
    copy = held.directory.resolve()
    state = prove_failability.tree_state_directory(copy)
    pristine = state / prove_failability.PRISTINE_DIRECTORY_NAME
    venv_files = [
        _write(copy / ".venv" / "lib" / "site" / f"mod{index}.py", "mutated\n")
        for index in range(2 if case == "two-restored" else 1)
    ]
    package_file = _write(copy / PACKAGE / "core.py", "MUTATED\n")
    files = [
        {"mutated_file": str(path), "restore_from": str(pristine / f"{path.name}.pristine")}
        for path in venv_files
    ]
    for path in venv_files:
        if case != "pristine-missing":
            _write(pristine / f"{path.name}.pristine", "original\n")
    _write(pristine / "core.py.pristine", "CORE = 2\n")
    files.append(
        {"mutated_file": str(package_file), "restore_from": str(pristine / "core.py.pristine")},
    )
    if case == "copy-root":
        files.append({"mutated_file": str(copy), "restore_from": str(pristine / "x")})
    marker = state / prove_failability.ACTIVE_MARKER_NAME
    _write(marker, "{not json" if case == "unreadable-marker" else json.dumps({"files": files}))
    capsys.readouterr()

    with workspace.lease(layout, _address("perf-1"), fresh=True):
        pass

    err = capsys.readouterr().err
    assert package_file.read_text(encoding="utf-8") == "CORE = 2\n"
    assert _statuses(layout) == {"slot-1": "ready"}
    if case in {"restored", "two-restored"}:
        assert [path.read_text(encoding="utf-8") for path in venv_files] == [
            "original\n",
        ] * len(venv_files)
        assert not state.exists()
        assert err == ""
    else:
        assert marker.is_file()
        assert err.startswith(f"workspace: kept live-mutation marker {marker}: ")
        assert err.count("\n") == 1
        assert "Traceback" not in err
        if case == "pristine-missing":
            assert venv_files[0].read_text(encoding="utf-8") == "mutated\n"


@pytest.mark.parametrize("how", ["resync", "gc"])
def test_a_prove_failability_directory_that_is_a_symlink_is_never_followed(
    layout: workspace.Layout,
    syncs: _Syncs,
    state_home: Path,
    tmp_path: Path,
    how: str,
) -> None:
    # The prover refuses a ``prove_failability`` that is not a real directory of this user, so
    # whatever lies behind such a link is no copy's state and is never removed.
    del syncs
    with workspace.lease(layout, _address("perf-1")) as held:
        pass
    foreign = tmp_path / "foreign"
    # The workspace's own state already made the state home.
    state_home.mkdir(exist_ok=True)
    (state_home / prove_failability.STATE_DIRECTORY_NAME).symlink_to(foreign)
    behind = foreign / prove_failability.tree_namespace(held.directory.resolve())
    _write(behind / prove_failability.ACTIVE_MARKER_NAME, "{}\n")

    if how == "resync":
        with workspace.lease(layout, _address("perf-1"), fresh=True):
            pass
    else:
        workspace.gc(layout)

    assert (behind / prove_failability.ACTIVE_MARKER_NAME).is_file()


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


def _run_once_after_checking(
    monkeypatch: pytest.MonkeyPatch,
    owner: object,
    check: str,
    target: Path,
    action: Callable[[], object],
) -> None:
    """Run ``action`` once, right after ``owner.check`` first answers for ``target``."""
    real_check = object_result(getattr, owner, check)
    assert callable(real_check)
    pending = [action]

    def _check(path: Path) -> object:
        answer = real_check(path)
        if path == target and pending:
            pending.pop()()
        return answer

    monkeypatch.setattr(owner, check, _check)


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
#: what cannot run under test is replaced: ``uv sync``, the provenance probe, the environment
#: ``uv run`` resolves (this process's own) and the worker's command, which records the
#: ``*.edit`` files it finds in the copy and then leaves its own.
#: Each step touches ``<name>.<step>`` when reached: ``bound`` once the address is bound,
#: ``sync`` in ``uv sync``, ``in`` in the command, ``probe`` at a lock tried without waiting or
#: creating, ``postgres`` and ``state`` at those reads. A step the test names as a pause then
#: waits until ``<name>.go-<step>`` appears. ``die_in_sync`` kills the process in its sync;
#: the ``hold`` command only holds the lock at ``path``, stepping ``opened`` each time it opens
#: that file. ``bin`` puts a folder ahead of ``PATH`` (a stand-in ``uv``); ``real_stream`` and
#: ``real_sync`` keep the script's own ``stream`` (with the environment ``uv run`` resolves)
#: and ``uv sync``, run through that ``uv``.
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


def uv_launch(_directory, command, env):
    return list(command), env


def stream(command, _env, _log_path, _header, cwd=None, holding=()):
    copy = Path(cwd)
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
    workspace.uv_launch = uv_launch
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


def test_gc_removes_the_proof_state_of_every_copy_it_deletes_and_no_other_flows(
    layout: workspace.Layout,
    state_home: Path,
) -> None:
    copies = [
        workspace.bind(layout, _address("perf-1")).directory,
        workspace.bind(layout, _address("mech-1")).directory,
        layout.gate_dir,
    ]
    other = workspace.Layout(layout.repo_root, layout.base, "hunt")
    other_copy = workspace.bind(other, workspace.Address.parse("hunt/pkg/a.py/perf-1")).directory
    for copy in (*copies, other_copy):
        _write(copy / "file.txt", "x\n")
    planted = [_plant_proof_state(copy) for copy in copies]
    kept = _plant_proof_state(other_copy)

    workspace.gc(layout)

    assert not layout.flow_dir.exists()
    assert [directory.exists() for directory in planted] == [False, False, False]
    assert (kept / prove_failability.ACTIVE_MARKER_NAME).is_file()
    assert kept.is_relative_to(state_home.resolve())
    assert other_copy.is_dir()


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


_DAY = 86400


def _purge(root: Path, keep: tuple[str, ...] = ()) -> None:
    """Age everything under ``root`` but ``keep`` four days, then apply the macOS ``$TMPDIR`` purge.

    The purge unlinks each regular file created and last read more than three
    days ago, open or locked or not (where the platform reports no creation
    time, the last write stands in for it); directories and symlinks stay.
    ``keep`` names paths relative to ``root``.
    """
    aged = time.time() - 4 * _DAY
    for folder, dirs, files in os.walk(root):
        for name in (*dirs, *files):
            path = Path(folder) / name
            if str(path.relative_to(root)) not in keep:
                os.utime(path, (aged, aged), follow_symlinks=False)
    cutoff = time.time() - 3 * _DAY
    for folder, _dirs, files in os.walk(root):
        for name in files:
            path = Path(folder) / name
            facts = path.lstat()
            created = getattr(facts, "st_birthtime", facts.st_mtime)
            if (
                path.is_file()
                and not path.is_symlink()
                and facts.st_atime < cutoff
                and created < cutoff
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


@pytest.mark.parametrize("window", ["size", "remove", "marker"])
def test_gc_reads_a_file_the_purge_removes_after_its_check_as_already_gone(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
    window: str,
) -> None:
    binding = workspace.bind(layout, _address("perf-1"))
    if window == "size":
        victim = _write(binding.directory / "file.txt", "x\n")
        _run_once_after_checking(monkeypatch, Path, "is_file", victim, victim.unlink)
    elif window == "remove":
        victim = _write(layout.legacy_state_path, "{}\n")
        _run_once_after_checking(monkeypatch, Path, "is_dir", victim, victim.unlink)
    else:
        victim = layout.flow_dir / workspace.MARKER_NAME
        victim.rmdir()
        _write(victim, "")
        _run_once_after_checking(monkeypatch, Path, "is_dir", victim, victim.unlink)

    workspace.gc(layout)

    assert not victim.exists()
    assert not layout.flow_dir.exists()


def test_a_purge_of_every_file_keeps_the_flow_releasable_and_listed(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    binding = workspace.bind(layout, _address("perf-1"))
    _write(binding.directory / "file.txt", "x\n")

    _purge(layout.flow_dir)

    assert "review: 1 of 4 copies" in workspace.status(layout.repo_root, None)
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]


def test_state_is_written_under_the_state_home_never_under_the_temporary_base(
    layout: workspace.Layout,
    state_home: Path,
) -> None:
    workspace.bind(layout, _address("perf-1"))

    assert layout.state_path.is_file()
    assert layout.state_path.is_relative_to(state_home.resolve())
    folders = (layout.state_dir, layout.state_dir.parent, layout.state_dir.parent.parent)
    assert [stat.S_IMODE(folder.stat().st_mode) for folder in folders] == [0o700] * 3
    assert [path.name for path in layout.base.rglob("*") if path.is_file()] == []


def test_bindings_survive_a_purge_of_every_file_and_keep_their_slots(
    layout: workspace.Layout,
    syncs: list[Path],
) -> None:
    with workspace.lease(layout, _address("perf-1")) as first:
        edit = _write(first.directory / "edit.txt", "kept\n")
    with workspace.lease(layout, _address("mech-1")) as second:
        pass
    del syncs[:]

    _purge(layout.base, keep=(str(edit.relative_to(layout.base)),))
    with workspace.lease(layout, _address("mech-1")) as again:
        pass

    assert (first.slot, second.slot, again.slot) == ("slot-1", "slot-2", "slot-2")
    assert syncs == [second.directory]
    assert edit.read_text(encoding="utf-8") == "kept\n"
    assert _bound_to(layout) == {
        "slot-1": "review/pkg/a.py/perf-1",
        "slot-2": "review/pkg/a.py/mech-1",
    }


def test_a_binding_whose_copy_a_reboot_removed_resyncs_into_the_same_slot(
    layout: workspace.Layout,
    syncs: list[Path],
) -> None:
    with workspace.lease(layout, _address("perf-1")):
        pass
    with workspace.lease(layout, _address("mech-1")) as second:
        pass
    del syncs[:]

    shutil.rmtree(layout.base)
    with workspace.lease(layout, _address("mech-1")) as again:
        synced = (again.directory / workspace.PACKAGE_DIR / "__init__.py").is_file()

    assert again.slot == second.slot == "slot-2"
    assert syncs == [second.directory]
    assert synced
    assert _statuses(layout) == {"slot-1": "ready", "slot-2": "ready"}


def test_release_and_gc_reach_the_state_of_a_flow_a_reboot_removed(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    workspace.bind(layout, _address("perf-1"))
    workspace.bind(layout, _address("mech-1", item="pkg/b.py"))
    shutil.rmtree(layout.base)

    assert "review: 2 of 4 copies" in workspace.status(layout.repo_root, None)
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]
    assert _bound_to(layout) == {"slot-1": None, "slot-2": "review/pkg/b.py/mech-1"}
    shutil.rmtree(layout.base)
    _ = workspace.gc(layout)

    assert not layout.state_dir.exists()
    assert not layout.flow_dir.exists()
    assert workspace.status(layout.repo_root, None)[1:] == ["postgres: no fakeshop container runs"]


def test_gc_removes_an_empty_state_folder_a_crash_left_for_a_flow_with_no_folder(
    layout: workspace.Layout,
) -> None:
    layout.state_dir.mkdir(parents=True)

    _ = workspace.gc(layout)

    assert not layout.state_dir.exists()
    assert not layout.flow_dir.exists()


def test_a_state_moved_between_the_two_reads_is_read_from_the_state_home(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace.bind(layout, _address("perf-1"))
    moved = layout.state_path.read_text(encoding="utf-8")
    layout.state_path.unlink()
    legacy = _write(layout.legacy_state_path, moved)

    def _move() -> None:
        _write(layout.state_path, moved)
        legacy.unlink()

    _run_once_before_reading(monkeypatch, legacy, _move)

    assert _bound_to(layout) == {"slot-1": "review/pkg/a.py/perf-1"}


def test_gc_and_release_of_a_bound_flow_remove_or_rewrite_its_state(
    layout: workspace.Layout,
) -> None:
    workspace.bind(layout, _address("perf-1"))
    assert workspace.release(layout, "pkg/a.py") == ["slot-1 review/pkg/a.py/perf-1"]
    assert workspace._load_state(layout)["slots"] == {"slot-1": None}
    assert layout.state_path.is_relative_to(workspace.state_root(layout.base))

    _ = workspace.gc(layout)

    assert not layout.state_dir.exists()
    assert not layout.state_dir.parent.exists()


def test_a_state_file_an_older_version_left_moves_to_the_state_home_with_its_slots(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(workspace.ROOT_ENV, str(layout.base.parent))
    layout.ensure_marked()
    bound = {"address": "review/pkg/a.py/perf-1", "item": "pkg/a.py", "role": "perf-1"}
    legacy = {
        "version": 1,
        "repo_root": str(layout.repo_root),
        "slots": {"slot-1": None, "slot-2": {**bound, "bound_at": "t", "status": "syncing"}},
        "items": {"pkg/a.py": {"item_baseline": "abc", "at": "t"}},
    }
    _write(layout.legacy_state_path, json.dumps(legacy))

    assert "  slot-2  review/pkg/a.py/perf-1 (syncing)" in workspace.status(layout.repo_root, None)
    assert workspace.bind(layout, _address("perf-1")).slot == "slot-2"
    assert not layout.legacy_state_path.exists()
    assert workspace.bind(layout, _address("mech-1")).slot == "slot-1"

    assert not layout.legacy_state_path.exists()
    moved = workspace._load_state(layout)
    assert moved["items"] == legacy["items"]
    assert _bound_to(layout) == {
        "slot-1": "review/pkg/a.py/mech-1",
        "slot-2": "review/pkg/a.py/perf-1",
    }


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


@pytest.mark.parametrize(
    "content",
    [
        "file",
        "folder",
        "symlink",
        "marker symlink",
    ],
)
def test_gc_clears_what_another_program_left_inside_the_marker(
    layout: workspace.Layout,
    tmp_path: Path,
    content: str,
) -> None:
    workspace.bind(layout, _address("perf-1"))
    marker = layout.flow_dir / workspace.MARKER_NAME
    outside = _write(tmp_path / "outside" / "kept.txt", "x\n")
    if content == "file":
        _write(marker / ".DS_Store", "x\n")
    elif content == "folder":
        _write(marker / "nested" / "file.txt", "x\n")
    elif content == "symlink":
        (marker / "link").symlink_to(outside.parent, target_is_directory=True)
    else:
        marker.rmdir()
        marker.symlink_to(outside.parent, target_is_directory=True)

    report = workspace.gc(layout)

    assert not layout.flow_dir.exists()
    assert report[0].startswith(f"removed {layout.flow_dir}")
    assert outside.read_text(encoding="utf-8") == "x\n"


def test_gc_cut_short_inside_the_flow_folder_keeps_the_marker_so_the_next_gc_finishes(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspace.bind(layout, _address("perf-1"))
    victim = _write(layout.legacy_state_path, "{}\n")
    real_unlink = Path.unlink

    def _fails_once(path: Path, *, missing_ok: bool = False) -> None:
        if path == victim:
            monkeypatch.setattr(Path, "unlink", real_unlink)
            raise OSError(1, "Operation not permitted", str(path))
        real_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", _fails_once)

    with pytest.raises(OSError, match="not permitted"):
        workspace.gc(layout)
    assert (layout.flow_dir / workspace.MARKER_NAME).is_dir()
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


def test_a_lock_replaced_while_waited_on_never_admits_two_holders(
    actors: _Actors,
    tmp_path: Path,
) -> None:
    lock = tmp_path / "copy.lock"
    actors.start("first", "hold", pauses=("in",), path=str(lock))
    assert actors.reached("first", "in")
    actors.start("waiter", "hold", pauses=("in",), path=str(lock))
    assert actors.reached("waiter", "opened")
    lock.rmdir()
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


def _lock_of(layout: workspace.Layout, family: str) -> Path:
    """Bind a copy and return the lock of ``family`` a command of the flow takes."""
    binding = workspace.bind(layout, _address("perf-1"))
    return {
        "pool": layout.pool_lock,
        "slot": layout.slot_lock(binding.slot),
        "gate": layout.flow_dir / "gate.lock",
    }[family]


def _older_lock_file(lock: Path) -> Path:
    """Put the regular lock file an older version of ``workspace.py`` made at ``lock``."""
    if lock.is_dir():
        lock.rmdir()
    return _write(lock, "")


_LOCK_FAMILIES = pytest.mark.parametrize("family", ["pool", "slot", "gate"])


def _taken_within(
    path: Path,
    seconds: float,
    until: threading.Event | None = None,
) -> tuple[threading.Event, threading.Thread]:
    """Start a blocking ``file_lock`` on ``path`` in a thread, held until ``until`` is set.

    Returns after ``seconds`` or once the thread holds the lock, whichever is first.
    """
    taken = threading.Event()

    def _take() -> None:
        with workspace.file_lock(path):
            taken.set()
            if until is not None:
                _ = until.wait(10)

    taker = threading.Thread(target=_take)
    taker.start()
    _ = taken.wait(seconds)
    return taken, taker


def test_the_purge_removes_a_held_lock_file_and_keeps_a_held_lock_directory(
    tmp_path: Path,
) -> None:
    lock_file = _write(tmp_path / "file.lock", "")
    lock_dir = tmp_path / "dir.lock"
    lock_dir.mkdir()
    held = [os.open(lock_file, os.O_RDWR), os.open(lock_dir, os.O_RDONLY | os.O_DIRECTORY)]
    try:
        for descriptor in held:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        _purge(tmp_path)
        assert not lock_file.exists()
        assert lock_dir.is_dir()
    finally:
        for descriptor in held:
            os.close(descriptor)


@_LOCK_FAMILIES
def test_a_held_lock_outlives_the_tmpdir_purge_and_admits_no_second_holder(
    layout: workspace.Layout,
    family: str,
) -> None:
    lock = _lock_of(layout, family)
    with workspace.flow_lease(layout), workspace.file_lock(lock):
        _purge(layout.flow_dir)
        assert lock.is_dir()
        with pytest.raises(workspace.LockBusyError), workspace.file_lock(lock, blocking=False):
            pass
        taken, taker = _taken_within(lock, 0.3)
        assert not taken.is_set()
    taker.join()
    assert taken.is_set()


def test_release_refuses_a_copy_held_across_the_tmpdir_purge(layout: workspace.Layout) -> None:
    binding = workspace.bind(layout, _address("perf-1"))
    with workspace.flow_lease(layout), workspace.file_lock(layout.slot_lock(binding.slot)):
        _purge(layout.flow_dir)
        with pytest.raises(workspace.LockBusyError, match="a command still runs in slot-1"):
            _ = workspace.release(layout, "pkg/a.py")
        assert workspace.running_slots(layout, [binding.slot]) == [binding.slot]
    assert _bound_to(layout) == {"slot-1": "review/pkg/a.py/perf-1"}


def test_binds_racing_across_the_tmpdir_purge_keep_both_bindings(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout.ensure_marked()
    real_load_state = workspace._load_state
    inside = threading.Event()
    resume = threading.Event()
    slots: dict[str, str] = {}

    def _paused_load_state(lay: workspace.Layout) -> workspace._PoolState:
        state = real_load_state(lay)
        if threading.current_thread().name == "first":
            inside.set()
            _ = resume.wait(10)
        return state

    def _bind(role: str) -> None:
        slots[role] = workspace.bind(layout, _address(role)).slot

    monkeypatch.setattr(workspace, "_load_state", _paused_load_state)
    first = threading.Thread(target=_bind, args=("perf-1",), name="first")
    first.start()
    assert inside.wait(10)
    _purge(layout.flow_dir)
    second = threading.Thread(target=_bind, args=("mech-1",), name="second")
    second.start()
    second.join(timeout=0.3)
    assert second.is_alive()
    resume.set()
    first.join()
    second.join()

    assert slots == {"perf-1": "slot-1", "mech-1": "slot-2"}
    assert _bound_to(layout) == {
        "slot-1": "review/pkg/a.py/perf-1",
        "slot-2": "review/pkg/a.py/mech-1",
    }


@_LOCK_FAMILIES
@pytest.mark.parametrize("create", [True, False])
def test_a_lock_file_an_older_version_left_becomes_the_lock_directory(
    layout: workspace.Layout,
    family: str,
    *,
    create: bool,
) -> None:
    lock = _older_lock_file(_lock_of(layout, family))

    with workspace.file_lock(lock, create=create):
        assert lock.is_dir()
        with pytest.raises(workspace.LockBusyError), workspace.file_lock(lock, blocking=False):
            pass
    with pytest.raises(IsADirectoryError):
        os.close(workspace._flock(lock, os.O_RDWR | os.O_CREAT, fcntl.LOCK_EX | fcntl.LOCK_NB))


@_LOCK_FAMILIES
def test_a_held_lock_file_is_replaced_only_once_its_holder_lets_go(
    layout: workspace.Layout,
    family: str,
) -> None:
    lock = _older_lock_file(_lock_of(layout, family))
    older = os.open(lock, os.O_RDWR)
    let_go = threading.Event()
    try:
        fcntl.flock(older, fcntl.LOCK_EX)
        with pytest.raises(workspace.LockBusyError), workspace.file_lock(lock, blocking=False):
            pass
        taken, taker = _taken_within(lock, 0.3, until=let_go)
        assert not taken.is_set()
        assert lock.is_file()
    finally:
        os.close(older)
    try:
        assert taken.wait(10)
        assert lock.is_dir()
        with pytest.raises(workspace.LockBusyError), workspace.file_lock(lock, blocking=False):
            pass
    finally:
        let_go.set()
        taker.join()


@_LOCK_FAMILIES
def test_two_commands_replacing_one_lock_file_hold_its_directory_in_turn(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
    family: str,
) -> None:
    lock = _older_lock_file(_lock_of(layout, family))
    older = os.open(lock, os.O_RDWR)
    fcntl.flock(older, fcntl.LOCK_EX)
    real_flock = fcntl.flock
    guard = threading.Lock()
    parked: list[str] = []
    errors: list[OSError] = []
    holders = [0, 0]

    def _flock(descriptor: int, operation: int) -> None:
        if os.path.samestat(os.fstat(descriptor), os.fstat(older)):
            with guard:
                parked.append(threading.current_thread().name)
        real_flock(descriptor, operation)

    def _hold() -> None:
        try:
            with workspace.file_lock(lock):
                with guard:
                    holders[0] += 1
                    holders[1] = max(holders)
                time.sleep(0.05)
                with guard:
                    holders[0] -= 1
        except OSError as error:
            errors.append(error)

    monkeypatch.setattr(fcntl, "flock", _flock)
    commands = [threading.Thread(target=_hold, name=name) for name in ("one", "two")]
    try:
        for command in commands:
            command.start()
        deadline = time.monotonic() + 10
        while len(parked) < 2 and time.monotonic() < deadline:
            time.sleep(0.01)
        time.sleep(0.1)
        assert sorted(parked) == ["one", "two"]
    finally:
        os.close(older)
        for command in commands:
            command.join()

    assert errors == []
    assert holders == [0, 1]
    assert lock.is_dir()


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


def test_gate_binds_its_result_to_a_snapshot_of_the_gate_copy_on_its_head(
    layout: workspace.Layout,
    syncs: _Syncs,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = layout.repo_root
    for name in ("pyproject.toml", "uv.lock"):
        _ = _write(repo / name, f"{name}\n")
    _git(repo, "add", "pyproject.toml", "uv.lock")
    _git(repo, "commit", "-q", "-m", "project files")
    before_sync = _git(repo, "rev-parse", "HEAD").strip()
    _write(repo / PACKAGE / "untracked.py", "NEW = 1\n")
    real_mirror = workspace.mirror_tree

    def mirror_after_a_landing(
        root: Path,
        destination: Path,
        *,
        preserved: frozenset[str],
    ) -> dict[str, list[str | int]]:
        _write(root / PACKAGE / "landed.py", "LANDED = 1\n")
        _git(root, "add", f"{PACKAGE}/landed.py")
        _git(root, "commit", "-q", "-m", "landed")
        return real_mirror(root, destination, preserved=preserved)

    monkeypatch.setattr(workspace, "mirror_tree", mirror_after_a_landing)

    assert workspace.gate(layout, []) == 0

    _ = capsys.readouterr()
    assert syncs == [layout.gate_dir]
    (result_path,) = layout.evidence.glob("gate-*.json")
    result = json_object(json_loads(result_path.read_text(encoding="utf-8")))
    snapshot = str(result["snapshot"])
    assert result["head"] == _git(repo, "rev-parse", "HEAD").strip() != before_sync
    assert _git(repo, "rev-parse", f"{snapshot}^").strip() == result["head"]
    assert {".python-version", f"{PACKAGE}/untracked.py"} <= set(_tree_files(repo, snapshot))
    assert _tree_files(repo, snapshot) == _copy_files(repo, layout.gate_dir)


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
    """The push/PR compatibility node of ``django.yml``'s ``test`` job and its ``run:`` lines.

    The node runs as two shard jobs that differ in ``shard`` alone.
    """
    job = _django_workflow_job("test")
    include = json_at(job, "strategy", "matrix", "include")
    assert isinstance(include, str), include
    lists: list[str] = re.findall(r"fromJSON\('(\[.*?\])'\)", include, re.DOTALL)
    push_nodes = json_list(json_loads(lists[-1]))
    floor = [
        node for node in map(json_object, push_nodes) if node.get("compatibility_only") == "1"
    ]
    assert [node.pop("shard") for node in floor] == ["library-keyset", "remainder"]
    assert floor[0] == floor[1]
    return floor[0], _run_lines(job)


#: A ``[dependency-groups].dev`` table naming every soft dependency at its floor.
SOFT_DEV_GROUP = (
    "[dependency-groups]\n"
    'dev = ["channels[daphne]>=4.3.2", "cryptography>=44.0.0", '
    '"django-debug-toolbar>=7.0.0", "djangorestframework>=3.17.0", "pytest>=9.0.2"]\n'
)
#: The soft-dependency pins ``SOFT_DEV_GROUP`` yields, in the order the floor installs them.
SOFT_PINS = {
    "channels[daphne]": "4.3.2",
    "cryptography": "44.0.0",
    "django-debug-toolbar": "7.0.0",
    "djangorestframework": "3.17.0",
}


def test_floor_pins_are_the_pyproject_lower_bounds(tmp_path: Path) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        "[project]\n"
        'requires-python = ">=3.10,<4.0"\n'
        "dependencies = [\n"
        '    "django>=5.2.16",\n'
        "    \"Strawberry_Graphql[debug] >= 0.322.2, <1 ; python_version >= '3.10'\",\n"
        '    "graphql-core>=3.2.0,<3.3",\n'
        "]\n"
        "[dependency-groups]\n"
        "dev = [\n"
        '    "Django_Debug_Toolbar >= 7.0.0, <9",\n'
        '    "channels[ Daphne ]>=4.3.2",\n'
        '    "djangorestframework-stubs>=3.18.0",\n'
        "    \"cryptography>=44.0.0 ; python_version >= '3.10'\",\n"
        '    "djangorestframework>=3.17.0",\n'
        "]\n",
    )

    pins = workspace.floor_pins(pyproject)

    assert pins == {
        "python": "3.10",
        "Django": "5.2.16",
        "strawberry-graphql": "0.322.2",
        **SOFT_PINS,
    }
    assert list(pins)[3:] == list(workspace.SOFT_FLOOR_PACKAGES) == list(SOFT_PINS)


@pytest.mark.parametrize(
    ("dependencies", "dev_group", "match"),
    [
        ('"Django>=5.2.16"', SOFT_DEV_GROUP, "lists no strawberry-graphql"),
        ('"Django==5.2.16", "strawberry-graphql>=0.322.2"', SOFT_DEV_GROUP, "states no >= floor"),
        ('"Django>=5.2.16", "strawberry-graphql>=0.322.2"', "", "dependency-groups"),
        (
            '"Django>=5.2.16", "strawberry-graphql>=0.322.2"',
            SOFT_DEV_GROUP.replace("channels[daphne]", "channels"),
            r"\[dependency-groups\]\.dev in .* lists no channels\[daphne\]$",
        ),
        (
            '"Django>=5.2.16", "strawberry-graphql>=0.322.2"',
            SOFT_DEV_GROUP.replace('"djangorestframework>=3.17.0", ', ""),
            "lists no djangorestframework$",
        ),
        (
            '"Django>=5.2.16", "strawberry-graphql>=0.322.2"',
            SOFT_DEV_GROUP.replace("cryptography>=44.0.0", "cryptography==44.0.0"),
            "states no >= floor",
        ),
    ],
)
def test_floor_pins_refuse_a_pyproject_without_a_floor(
    tmp_path: Path,
    dependencies: str,
    dev_group: str,
    match: str,
) -> None:
    pyproject = _write(
        tmp_path / "pyproject.toml",
        f'[project]\nrequires-python = ">=3.10"\ndependencies = [{dependencies}]\n{dev_group}',
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
        r"with strawberry-graphql \*\*([^*]+)\*\*, and the soft dependencies at "
        r"(\S+) \*\*([^*]+)\*\*, (\S+) \*\*([^*]+)\*\*, (\S+) \*\*([^*]+)\*\* "
        r"and (\S+) \*\*([^*]+)\*\*",
        build,
    )
    recipe = re.findall(
        r"^uv pip install --python <scratch>/dsf-floor/bin/python ('.*')$",
        build,
        re.MULTILINE,
    )
    soft = [(name, pins[name]) for name in workspace.SOFT_FLOOR_PACKAGES]
    node, _lines = _ci_floor_node()

    assert stated is not None
    assert stated.groups()[:3] == (pins["Django"], pins["python"], pins["strawberry-graphql"])
    assert list(zip(stated.groups()[3::2], stated.groups()[4::2], strict=True)) == soft
    assert recipe == [
        f"'django=={pins['Django']}' 'strawberry-graphql=={pins['strawberry-graphql']}'",
        " ".join(f"'{name}=={version}'" for name, version in soft),
    ]
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
    ``--upgrade-package Django``, then strawberry-graphql, then every soft
    dependency in one install, and runs pytest with ``addopts`` that drop
    ``--cov``; the suite does each of those against its own virtualenv and only
    adds ``-p no:cacheprovider``. CI splits the run into a ``load`` shard of two
    live-API modules and a ``loadscope`` shard of the rest; the suite runs the
    whole selection at once with the ``loadscope`` shard's ``addopts``.
    """
    _node, lines = _ci_floor_node()
    ci_addopts: list[str] = re.findall(r'addopts="(-[^"]*)"', "\n".join(lines))
    pins = {
        "python": "3.10",
        "Django": "5.2.16",
        "strawberry-graphql": "0.322.2",
        **SOFT_PINS,
    }
    soft = [f"{name}=={version}" for name, version in SOFT_PINS.items()]
    venv = tmp_path / "gate-floor"
    python = str(venv / "bin" / "python")

    commands = workspace.floor_install_commands(tmp_path / "gate", venv, pins)

    assert "uv sync --python ${{ matrix.python }}" in lines
    assert 'uv pip install --upgrade-package Django "Django==${{ matrix.django }}"' in lines
    assert 'uv pip install "strawberry-graphql==${{ matrix.strawberry }}"' in lines
    assert "uv pip install " + " ".join(f'"{pin}"' for pin in soft) in lines
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
        [*pip, *soft],
    ]
    arguments, cell = workspace.GATE_SUITES[workspace.FLOOR_SUITE]
    no_cov = [opts for opts in ci_addopts if "--cov" not in opts]
    assert no_cov == [
        "-v -n auto --dist load --durations=25",
        "-v -n auto --dist loadscope --durations=25",
    ]
    assert arguments == (
        "pytest",
        "-p",
        "no:cacheprovider",
        "-o",
        f"addopts={no_cov[1]}",
    )
    assert cell == "default"
    assert list(workspace.GATE_SUITES)[:3] == ["lint", "default", "floor"]


@pytest.mark.parametrize(
    ("options", "suites"),
    [
        pytest.param([], ["lint"], id="bare-gate-runs-only-lint"),
        pytest.param(["--suites", "lint"], ["lint"], id="lint-named"),
        pytest.param(
            ["--suites", "lint,default,floor,sharded,pg"],
            [
                "lint",
                "default",
                "floor",
                "sharded",
                "pg",
            ],
            id="maintainer-named-suites-still-run",
        ),
    ],
)
def test_a_bare_gate_runs_only_the_lint_suite(
    options: list[str],
    suites: list[str],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """``gate`` defaults to CI's lint job; every other suite runs only when named.

    AGENTS.md runs the full suite, the coverage gate and the version matrix only
    in GitHub Actions, so a flow doc's bare ``workspace.py gate <flow>`` must not
    start them locally; the maintainer can still name them.
    """
    monkeypatch.setenv(workspace.ROOT_ENV, str(tmp_path))
    calls: list[tuple[str, list[str]]] = []

    def record_gate(layout: workspace.Layout, chosen: Sequence[str]) -> int:
        calls.append((layout.flow, list(chosen)))
        return 0

    monkeypatch.setattr(workspace, "gate", record_gate)

    assert workspace.main(["gate", "hunt", *options]) == 0
    assert calls == [("hunt", suites)]


def test_gate_refuses_a_suite_it_does_not_know(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown ``--suites`` entry is refused with the known set, before any suite runs."""
    monkeypatch.setenv(workspace.ROOT_ENV, str(tmp_path))
    calls: list[Sequence[str]] = []

    def record_gate(_layout: workspace.Layout, chosen: Sequence[str]) -> int:
        calls.append(chosen)
        return 0

    monkeypatch.setattr(workspace, "gate", record_gate)
    _ = capsys.readouterr()

    assert (
        workspace.main(
            [
                "gate",
                "hunt",
                "--suites",
                "lint,nope",
            ],
        )
        == 1
    )
    assert calls == []
    assert capsys.readouterr().err == (
        "workspace: --suites takes a subset of lint, default, floor, sharded, pg; "
        "got 'lint,nope'\n"
    )


def _gate_copy_inputs(layout: workspace.Layout, lock: str = "lock v1\n") -> None:
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.16", "strawberry-graphql>=0.322.2"]\n' + SOFT_DEV_GROUP,
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
    assert built["pins"] == {
        "python": "3.10",
        "Django": "5.2.16",
        "strawberry-graphql": "0.322.2",
        **SOFT_PINS,
    }
    assert built["python"] == str(layout.floor_venv / "bin" / "python")
    assert [command[:3] for command, _env in calls] == [
        ["uv", "sync", "--directory"],
        ["uv", "pip", "install"],
        ["uv", "pip", "install"],
        ["uv", "pip", "install"],
    ]
    assert all(env["UV_PROJECT_ENVIRONMENT"] == str(layout.floor_venv) for _c, env in calls)
    assert reused == {**built, "reused": True}
    assert len(calls) == 4

    _gate_copy_inputs(layout, lock="lock v2\n")
    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["reused"] is False
    assert rebuilt["key"] != built["key"]
    assert len(calls) == 8
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
        'dependencies = ["Django>=5.2.17", "strawberry-graphql>=0.322.2"]\n' + SOFT_DEV_GROUP,
    )

    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["key"] != built["key"]
    assert calls[-3][0][-1] == "Django==5.2.17"


def test_a_soft_dependency_floor_move_rebuilds_the_floor_venv(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)
    built = workspace.ensure_floor_venv(layout)
    _write(
        layout.gate_dir / "pyproject.toml",
        '[project]\nrequires-python = ">=3.10"\n'
        'dependencies = ["Django>=5.2.16", "strawberry-graphql>=0.322.2"]\n'
        + SOFT_DEV_GROUP.replace("djangorestframework>=3.17.0", "djangorestframework>=3.18.0"),
    )

    rebuilt = workspace.ensure_floor_venv(layout)

    assert rebuilt["key"] != built["key"]
    assert calls[-1][0][-1] == "djangorestframework==3.18.0"


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
    assert len(calls) == 4


def test_a_floor_key_gone_when_the_gate_reads_it_rebuilds_the_floor_venv(
    layout: workspace.Layout,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _gate_copy_inputs(layout)
    calls = _record_installs(monkeypatch, layout)
    built = workspace.ensure_floor_venv(layout)
    key_path = layout.floor_venv / workspace.FLOOR_KEY_NAME
    _run_once_before_reading(monkeypatch, key_path, key_path.unlink)

    again = workspace.ensure_floor_venv(layout)

    assert again == built
    assert again["reused"] is False
    assert len(calls) == 8
    assert key_path.read_text(encoding="utf-8") == built["key"]


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
# Snapshot baseline
# --------------------------------------------------------------------------------------------


def _tree_files(root: Path, commit: str) -> dict[str, str]:
    """Return ``{name: blob id}`` of ``commit``'s tree."""
    listing = _git(root, "ls-tree", "-r", "-z", commit).split("\0")
    return {
        record.split("\t", 1)[1]: record.split("\t", 1)[0].split()[2]
        for record in listing
        if record
    }


def _copy_files(root: Path, copy: Path) -> dict[str, str]:
    """Return ``{name: blob id}`` of every file under ``copy``, its own ``.git`` left out."""
    return {
        path.relative_to(copy).as_posix(): _git(root, "hash-object", str(path)).strip()
        for path in sorted(copy.rglob("*"))
        if path.is_file() and path.relative_to(copy).parts[0] != ".git"
    }


def _manifest_of(entries: dict[str, list[str | int]]) -> workspace._Manifest:
    return {
        "synced_at": "now",
        "tree_digest": workspace.tree_digest(entries),
        "package_digest": "",
        "entries": entries,
    }


def _snapshot_of_a_copy(repo: Path, tmp_path: Path) -> tuple[str, Path]:
    copy = tmp_path / "copy"
    manifest = _manifest_of(workspace.mirror_tree(repo, copy))
    head = _git(repo, "rev-parse", "HEAD").strip()
    return workspace.snapshot_commit(repo, copy, manifest, head), copy


def test_snapshot_commit_holds_the_copy_untracked_and_ignored_extras_included(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _write(repo / PACKAGE / "pre_existing.py", "PRE = 1\n")
    (repo / "examples" / "fakeshop" / "db.sqlite3").unlink()
    _write(repo / "ignored.txt", "never copied\n")
    index = (repo / ".git" / "index").read_bytes()
    refs = _git(repo, "for-each-ref")

    sha, copy = _snapshot_of_a_copy(repo, tmp_path)

    assert _tree_files(repo, sha) == _copy_files(repo, copy)
    assert {".python-version", f"{PACKAGE}/pre_existing.py"} <= set(_tree_files(repo, sha))
    assert "ignored.txt" not in _tree_files(repo, sha)
    assert _git(repo, "rev-parse", f"{sha}^").strip() == _git(repo, "rev-parse", "HEAD").strip()
    assert (repo / ".git" / "index").read_bytes() == index
    assert _git(repo, "for-each-ref") == refs


def test_snapshot_commit_refuses_a_copy_edited_since_its_sync(repo: Path, tmp_path: Path) -> None:
    copy = tmp_path / "copy"
    manifest = _manifest_of(workspace.mirror_tree(repo, copy))
    _write(copy / PACKAGE / "core.py", "EDITED = 1\n")

    with pytest.raises(workspace.WorkspaceError, match="changed while it was snapshotted"):
        _ = workspace.snapshot_commit(
            repo,
            copy,
            manifest,
            _git(repo, "rev-parse", "HEAD").strip(),
        )


def test_snapshot_commit_stores_the_bytes_on_disk_whatever_the_callers_line_endings(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _ = (repo / PACKAGE / "core.py").write_bytes(b"CORE = 3\r\n")
    home = tmp_path / "home"
    _write(home / ".gitconfig", "[core]\n\tautocrlf = true\n")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))

    sha, _copy = _snapshot_of_a_copy(repo, tmp_path)

    stored = workspace._git(repo, "cat-file", "blob", f"{sha}:{PACKAGE}/core.py")
    assert stored == "CORE = 3\r\n"


def test_snapshot_commit_needs_no_identity_from_the_callers_config(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(repo, "config", "user.useConfigOnly", "true")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "home" / ".config"))

    sha, copy = _snapshot_of_a_copy(repo, tmp_path)

    assert _tree_files(repo, sha) == _copy_files(repo, copy)


def test_baseline_names_the_copy_whatever_landed_while_it_waited_for_its_lock(
    layout: workspace.Layout,
    syncs: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = layout.repo_root
    _write(repo / PACKAGE / "pre_existing.py", "PRE = 1\n")
    real_mirror = workspace.mirror_tree

    def mirror_after_a_landing(
        root: Path,
        destination: Path,
        *,
        preserved: frozenset[str],
    ) -> dict[str, list[str | int]]:
        _write(root / PACKAGE / "landed.py", "LANDED = 1\n")
        _git(root, "add", f"{PACKAGE}/landed.py")
        _git(root, "commit", "-q", "-m", "landed")
        _write(root / PACKAGE / "core.py", "CORE = 3\n")
        _write(root / PACKAGE / "late.py", "LATE = 1\n")
        return real_mirror(root, destination, preserved=preserved)

    def for_flow(_flow: str) -> workspace.Layout:
        return layout

    monkeypatch.setattr(workspace, "mirror_tree", mirror_after_a_landing)
    monkeypatch.setattr(workspace.Layout, "for_flow", staticmethod(for_flow))

    assert workspace.main(["baseline", "review/pkg/a.py"]) == 0

    sha = capsys.readouterr().out.splitlines()[0].removeprefix("ITEM_BASELINE=")
    assert syncs == [layout.slot_dir("slot-1")]
    assert _tree_files(repo, sha) == _copy_files(repo, layout.slot_dir("slot-1"))
    assert _git(repo, "rev-parse", f"{sha}^").strip() == _git(repo, "rev-parse", "HEAD").strip()
    assert workspace._load_state(layout)["items"]["pkg/a.py"]["item_baseline"] == sha
    assert workspace.item_diff(repo, sha, (".",)).startswith(b"sha256 ")
    _write(repo / PACKAGE / "core.py", "CORE = 4\n")
    assert _headers(workspace.item_diff(repo, sha, (".",)).decode()) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
    ]


def test_baseline_leaves_a_landing_during_the_copys_sync_out_of_its_snapshot(
    layout: workspace.Layout,
    syncs: list[Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = layout.repo_root
    database = repo / "examples" / "fakeshop" / "db.sqlite3"
    recorded_sync = workspace._uv_sync

    def sync_while_the_shared_tree_moves(destination: Path, holding: Sequence[int] = ()) -> None:
        recorded_sync(destination, holding)
        _write(database, "landed during the sync\n")

    def for_flow(_flow: str) -> workspace.Layout:
        return layout

    monkeypatch.setattr(workspace, "_uv_sync", sync_while_the_shared_tree_moves)
    monkeypatch.setattr(workspace.Layout, "for_flow", staticmethod(for_flow))

    assert workspace.main(["baseline", "review/pkg/a.py"]) == 0

    sha = capsys.readouterr().out.splitlines()[0].removeprefix("ITEM_BASELINE=")
    assert syncs == [layout.slot_dir("slot-1")]
    assert _tree_files(repo, sha) == _copy_files(repo, layout.slot_dir("slot-1"))
    assert _headers(workspace.item_diff(repo, sha, (".",)).decode()) == [
        "diff --git a/examples/fakeshop/db.sqlite3 b/examples/fakeshop/db.sqlite3",
    ]


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


def test_item_diff_orders_every_file_by_path_whatever_its_kind_or_staging(repo: Path) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    for name in ("zeta", "alpha", "mid"):
        _write(repo / PACKAGE / f"{name}.py", f"{name.upper()} = 1\n")
    _git(repo, "add", f"{PACKAGE}/mid.py")
    expected = [
        f"diff --git a/{PACKAGE}/{name}.py b/{PACKAGE}/{name}.py"
        for name in (
            "alpha",
            "core",
            "mid",
            "zeta",
        )
    ]

    assert _headers(_item_diff(repo)) == expected


@pytest.mark.parametrize(
    "step",
    [
        pytest.param(("add", f"{PACKAGE}/aaa.py"), id="add-new-file"),
        pytest.param(("add", "-N", f"{PACKAGE}/aaa.py"), id="intent-to-add"),
        pytest.param(
            (
                "rm",
                "-q",
                "--cached",
                f"{PACKAGE}/__init__.py",
            ),
            id="rm-cached-unchanged",
        ),
        pytest.param(
            (
                "rm",
                "-q",
                "--cached",
                f"{PACKAGE}/core.py",
            ),
            id="rm-cached-edited",
        ),
    ],
)
def test_item_diff_bytes_ignore_the_index(repo: Path, step: tuple[str, ...]) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _write(repo / PACKAGE / "aaa.py", "AAA = 1\n")
    unstaged = _item_diff(repo)

    _git(repo, *step)

    assert _item_diff(repo) == unstaged


def test_item_diff_takes_the_working_content_over_a_staged_edit(repo: Path) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _git(repo, "add", f"{PACKAGE}/core.py")
    _write(repo / PACKAGE / "core.py", "CORE = 4\n")

    diff = _item_diff(repo)

    assert "+CORE = 4" in diff
    assert "CORE = 3" not in diff


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_item_diff_reads_an_edit_the_index_flags_as_unchanged(repo: Path, flag: str) -> None:
    _git(repo, "update-index", flag, f"{PACKAGE}/core.py")
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")

    assert "+CORE = 3" in _item_diff(repo)


def test_item_diff_finds_an_unstaged_move_as_the_rename_staging_it_gives(repo: Path) -> None:
    (repo / PACKAGE / "core.py").rename(repo / PACKAGE / "renamed.py")

    unstaged = _item_diff(repo)
    _git(repo, "add", "-A")

    assert _headers(unstaged) == [f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/renamed.py"]
    assert _item_diff(repo) == unstaged


def test_item_diff_carries_a_module_turned_into_a_package_and_back(repo: Path) -> None:
    (repo / PACKAGE / "core.py").unlink()
    _write(repo / PACKAGE / "core.py" / "inner.py", "INNER = 1\n")

    assert _headers(_item_diff(repo)) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
        f"diff --git a/{PACKAGE}/core.py/inner.py b/{PACKAGE}/core.py/inner.py",
    ]
    shutil.rmtree(repo / PACKAGE / "core.py")
    _write(repo / PACKAGE / "core.py", "CORE = 2\n")

    assert _headers(_item_diff(repo)) == []


def test_item_diff_keeps_a_tracked_link_to_a_directory_a_link(repo: Path) -> None:
    _write(repo / PACKAGE / "sub" / "a.py", "A = 1\n")
    (repo / PACKAGE / "link").symlink_to("sub")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "link")

    assert _headers(_item_diff(repo)) == []


def test_item_diff_carries_a_nested_repository_as_a_gitlink_once_staged(repo: Path) -> None:
    nested = repo / PACKAGE / "vendored"
    _write(nested / "lib.py", "LIB = 1\n")
    _git(nested, "init", "-q")
    _git(nested, "add", "-A")
    _git(nested, "commit", "-q", "-m", "vendored")
    assert _headers(_item_diff(repo)) == []
    _git(repo, "add", f"{PACKAGE}/vendored")

    diff = _item_diff(repo)

    assert _headers(diff) == [f"diff --git a/{PACKAGE}/vendored b/{PACKAGE}/vendored"]
    assert "+Subproject commit " in diff
    _git(repo, "commit", "-q", "-m", "gitlink")
    assert _headers(_item_diff(repo)) == []


def test_item_diff_leaves_out_what_a_sparse_checkout_keeps_off_disk(repo: Path) -> None:
    _git(repo, "sparse-checkout", "set", "--cone", PACKAGE)
    assert not (repo / "examples").exists()
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")

    assert _headers(_item_diff(repo, ".")) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
    ]


def test_item_diff_keeps_a_force_added_ignored_file(repo: Path) -> None:
    _write(repo / PACKAGE / "ignored.txt", "kept\n")
    assert _headers(_item_diff(repo)) == []
    _git(repo, "add", "-f", f"{PACKAGE}/ignored.txt")

    assert _headers(_item_diff(repo)) == [
        f"diff --git a/{PACKAGE}/ignored.txt b/{PACKAGE}/ignored.txt",
    ]


# One file under each shape ``is_excluded`` names: a parked ``*-ws`` copy, both excluded
# prefixes, and both scratch segments.
EXCLUDED_NAMES = [
    pytest.param("hunt-ws/notes.py", id="ws-folder"),
    pytest.param("output/report.txt", id="output"),
    pytest.param("docs/shadow/current/core.py", id="shadow"),
    pytest.param(f"{PACKAGE}/temp-tests/test_probe.py", id="temp-tests"),
    pytest.param("docs/bug_hunt/worker-memory/notes.md", id="worker-memory"),
]


def _unignore_scratch(repo: Path) -> None:
    """Commit a ``.gitignore`` that leaves every excluded shape visible to git."""
    _write(repo / ".gitignore", ".python-version\nignored.txt\n")
    _git(repo, "commit", "-q", "-am", "scratch not ignored")


@pytest.mark.parametrize("name", EXCLUDED_NAMES)
def test_item_diff_leaves_out_an_untracked_file_the_mirror_leaves_out(
    repo: Path,
    name: str,
) -> None:
    assert workspace.is_excluded(name)
    _unignore_scratch(repo)
    _write(repo / name, "scratch\n")
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    expected = [f"diff --git a/{PACKAGE}/new.py b/{PACKAGE}/new.py"]

    assert _headers(_item_diff(repo, ".")) == expected
    assert _headers(_item_diff(repo, name.rsplit("/", 1)[0], PACKAGE)) == expected


@pytest.mark.parametrize("name", EXCLUDED_NAMES)
@pytest.mark.parametrize("change", ["edited", "deleted"])
def test_item_diff_keeps_the_baseline_blob_of_a_tracked_file_the_mirror_leaves_out(
    repo: Path,
    name: str,
    change: str,
) -> None:
    _unignore_scratch(repo)
    _write(repo / name, "tracked scratch\n")
    _git(repo, "add", "-f", name)
    _git(repo, "commit", "-q", "-m", "tracked scratch")
    if change == "deleted":
        (repo / name).unlink()
    else:
        _write(repo / name, "edited scratch\n")
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")

    assert _headers(_item_diff(repo, ".")) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
    ]


def test_item_diff_since_a_snapshot_agrees_with_it_on_what_the_mirror_leaves_out(
    repo: Path,
    tmp_path: Path,
) -> None:
    _write(repo / "hunt-ws" / "notes.py", "untracked scratch\n")
    tracked = f"{PACKAGE}/worker-memory/notes.md"
    _write(repo / tracked, "tracked scratch\n")
    _git(repo, "add", tracked)
    _git(repo, "commit", "-q", "-m", "tracked scratch")
    _write(repo / tracked, "edited before the snapshot\n")

    sha, _copy = _snapshot_of_a_copy(repo, tmp_path)

    assert _headers(workspace.item_diff(repo, sha, (".",)).decode()) == []
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    assert _headers(workspace.item_diff(repo, sha, (".",)).decode()) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
    ]


def test_item_diff_leaves_the_shared_index_and_its_stat_data_untouched(repo: Path) -> None:
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    os.utime(repo / PACKAGE / "core.py", (1, 1))
    index = repo / ".git" / "index"
    before = (index.read_bytes(), index.stat().st_mtime_ns)

    _ = _item_diff(repo)

    assert (index.read_bytes(), index.stat().st_mtime_ns) == before


# Each row is a file the caller's own git setup holds: under a private HOME and XDG config
# directory, so the session running the tests never leaks in.
CALLERS_GLOBAL_GIT_FILES = [
    pytest.param({".config/git/ignore": "*.local.py\n"}, id="xdg-ignore"),
    pytest.param({".config/git/attributes": "*.py -diff\n"}, id="xdg-attributes"),
    pytest.param(
        {".gitconfig": "[core]\n\texcludesFile = {home}/excludes\n", "excludes": "*.local.py\n"},
        id="global-excludes-file",
    ),
]


def _callers_home(home: Path, files: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    for name, content in files.items():
        _write(home / name, content.format(home=home))
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))


@pytest.mark.parametrize("files", CALLERS_GLOBAL_GIT_FILES)
def test_item_diff_ignores_the_callers_global_git_files(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _write(repo / PACKAGE / "scratch.local.py", "LOCAL = 1\n")
    _callers_home(tmp_path / "bare-home", {}, monkeypatch)
    expected = _item_diff(repo)
    assert _headers(expected) == [
        f"diff --git a/{PACKAGE}/core.py b/{PACKAGE}/core.py",
        f"diff --git a/{PACKAGE}/scratch.local.py b/{PACKAGE}/scratch.local.py",
    ]
    assert "GIT binary patch" not in expected

    _callers_home(tmp_path / "home", files, monkeypatch)

    assert _item_diff(repo) == expected


@pytest.mark.parametrize(
    "files",
    [row for row in CALLERS_GLOBAL_GIT_FILES if row.id != "xdg-attributes"],
)
def test_wanted_files_ignores_the_callers_global_ignore_files(
    repo: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    files: dict[str, str],
) -> None:
    _write(repo / PACKAGE / "scratch.local.py", "LOCAL = 1\n")
    _callers_home(tmp_path / "home", files, monkeypatch)

    assert f"{PACKAGE}/scratch.local.py" in workspace.wanted_files(repo)


def test_content_tree_is_the_baseline_overlaid_with_the_working_content(repo: Path) -> None:
    _write(repo / PACKAGE / "core.py", "CORE = 3\n")
    _write(repo / PACKAGE / "new.py", "NEW = 1\n")
    (repo / PACKAGE / "__init__.py").unlink()
    _write(repo / "examples" / "outside.py", "OUTSIDE = 1\n")

    tree = workspace.content_tree(repo, "HEAD", (PACKAGE,))

    listing = _git(repo, "ls-tree", "-r", "--name-only", tree).split()
    assert listing == [
        ".gitignore",
        f"{PACKAGE}/core.py",
        f"{PACKAGE}/new.py",
        "examples/fakeshop/db.sqlite3",
    ]
    assert _git(repo, "show", f"{tree}:{PACKAGE}/core.py") == "CORE = 3\n"


def test_content_tree_reads_exactly_the_named_files_from_another_work_tree(
    repo: Path,
    tmp_path: Path,
) -> None:
    other = tmp_path / "other"
    _write(other / PACKAGE / "core.py", "CORE = 9\n")
    _write(other / "unnamed.py", "UNNAMED = 1\n")
    empty = _git(repo, "hash-object", "-t", "tree", os.devnull).strip()

    tree = workspace.content_tree(
        repo,
        empty,
        names=[f"{PACKAGE}/core.py", f"{PACKAGE}/missing.py"],
        work_tree=other,
    )

    assert _git(repo, "ls-tree", "-r", "--name-only", tree).split() == [f"{PACKAGE}/core.py"]
    assert _git(repo, "show", f"{tree}:{PACKAGE}/core.py") == "CORE = 9\n"


def test_content_tree_refreshes_an_explicitly_named_file_it_would_leave_out_by_default(
    repo: Path,
) -> None:
    name = "hunt-ws/notes.py"
    assert workspace.is_excluded(name)
    _write(repo / name, "named scratch\n")

    tree = workspace.content_tree(repo, "HEAD", names=[name], excluded=workspace.is_excluded)

    assert _git(repo, "show", f"{tree}:{name}") == "named scratch\n"
    assert (
        name
        not in _git(
            repo,
            "ls-tree",
            "-r",
            "--name-only",
            workspace.content_tree(repo, "HEAD", excluded=workspace.is_excluded),
        ).split()
    )


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


def _flow_is_leased(layout: workspace.Layout) -> bool:
    """Whether a command holds the flow's lease: the exclusive ``flock`` ``gc`` takes fails."""
    try:
        descriptor = workspace._lock_flow_dir(layout, fcntl.LOCK_EX | fcntl.LOCK_NB, create=False)
    except BlockingIOError:
        return True
    if descriptor is not None:
        os.close(descriptor)
    return False


def _file_id(path: Path) -> tuple[int, int]:
    found = path.stat()
    return found.st_dev, found.st_ino


@dataclasses.dataclass(frozen=True)
class _Started:
    """A command a run started: its argv, its environment, its directory, and the locks held."""

    command: list[str]
    env: dict[str, str]
    cwd: Path | None
    holding: list[tuple[int, int]]
    flow_leased: bool
    copy_locked: bool


def _launch_as_given(
    _directory: Path,
    command: Sequence[str],
    env: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    """Stand in for ``workspace.uv_launch``: the command as given, in the environment given."""
    return list(command), env


class _StartedCommands(list[_Started]):
    """The commands started, in order, and the exit code each one reports: ``code``."""

    def __init__(self) -> None:
        super().__init__()
        self.code = 0


@pytest.fixture
def started(
    layout: workspace.Layout,
    syncs: _Syncs,
    monkeypatch: pytest.MonkeyPatch,
) -> _StartedCommands:
    """Every command ``main`` starts in this process, in order; none of them runs.

    ``Layout.for_flow`` answers under the test's pool for any flow, ``uv sync`` is ``syncs``,
    the provenance probe reports the copy itself, the environment ``uv run`` resolves is the
    one given, and ``stream`` records the command with whether the flow's lease and the copy's
    lock are held while it would run, then reports ``code`` as its exit.
    """
    del syncs
    commands = _StartedCommands()

    def for_flow(flow: str) -> workspace.Layout:
        return workspace.Layout(layout.repo_root, layout.base, flow)

    def probe(directory: Path, _env: dict[str, str]) -> workspace._ProbeResult:
        return _probe(directory)

    def stream(
        command: Sequence[str],
        env: dict[str, str],
        _log_path: Path,
        _header: str,
        cwd: Path | None = None,
        *,
        holding: Sequence[int] = (),
    ) -> workspace.Finished:
        assert cwd is not None
        owner = for_flow(cwd.parent.parent.name)
        commands.append(
            _Started(
                list(command),
                env,
                cwd,
                [(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in holding],
                _flow_is_leased(owner),
                _lock_is_held(owner.slot_lock(cwd.name)),
            ),
        )
        return workspace.Finished(commands.code)

    monkeypatch.setattr(workspace.Layout, "for_flow", staticmethod(for_flow))
    monkeypatch.setattr(workspace, "probe", probe)
    monkeypatch.setattr(workspace, "uv_launch", _launch_as_given)
    monkeypatch.setattr(workspace, "stream", stream)
    return commands


def _prove(manifest: Path | str, *flags: str, address: str = _ADDRESS) -> int:
    return workspace.main(
        [
            "prove",
            address,
            str(manifest),
            *flags,
        ],
    )


@pytest.mark.parametrize("given", ["proofs.json", "~/proofs.json"], ids=["relative", "home"])
@pytest.mark.parametrize("flow", ["review", "hunt"])
def test_prove_runs_the_proof_script_on_its_flows_copy_and_logs_the_run(
    flow: str,
    given: str,
    layout: workspace.Layout,
    started: _StartedCommands,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _write(tmp_path / "proofs.json", "{}\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    started.code = 3

    code = _prove(given, "--", "--only", "1", address=f"{flow}/pkg/a.py/perf-1")

    owner = workspace.Layout(layout.repo_root, layout.base, flow)
    record = _run_record(owner)
    copy = owner.slot_dir("slot-1")
    scratch = owner.evidence / "proofs" / "pkg__a.py" / "perf-1"
    proof = [
        "python",
        "scripts/prove_failability.py",
        str(manifest),
        "--workspace",
        str(copy),
        "--scratch-root",
        str(scratch),
        "--json",
        str(scratch / f"{record['run_id']}.json"),
        "--only",
        "1",
    ]
    assert code == 3
    assert [(run.command, run.cwd) for run in started] == [(proof, copy)]
    assert (record["address"], record["command"], record["exit"]) == (
        f"{flow}/pkg/a.py/perf-1",
        proof,
        3,
    )


def test_prove_runs_its_command_holding_the_flow_lease_and_the_copy_lock(
    layout: workspace.Layout,
    started: _StartedCommands,
    tmp_path: Path,
) -> None:
    assert _prove(_write(tmp_path / "proofs.json", "{}\n")) == 0

    (run,) = started
    assert (run.flow_leased, run.copy_locked) == (True, True)
    assert run.holding == [_file_id(layout.flow_dir), _file_id(layout.slot_lock("slot-1"))]


@pytest.mark.parametrize(
    ("flags", "sharded"),
    [((), None), (("--cell", "sharded"), "1")],
    ids=["default", "sharded"],
)
def test_prove_runs_its_command_in_its_cell(
    flags: tuple[str, ...],
    sharded: str | None,
    started: _StartedCommands,
    tmp_path: Path,
) -> None:
    assert _prove(_write(tmp_path / "proofs.json", "{}\n"), *flags) == 0

    assert [run.env.get("FAKESHOP_SHARDED") for run in started] == [sharded]


@pytest.mark.parametrize(("fresh", "kept"), [(False, True), (True, False)], ids=["reuse", "fresh"])
@pytest.mark.usefixtures("started")
def test_prove_reuses_its_copy_with_its_edits_and_fresh_resyncs_it(
    layout: workspace.Layout,
    syncs: _Syncs,
    tmp_path: Path,
    *,
    fresh: bool,
    kept: bool,
) -> None:
    manifest = _write(tmp_path / "proofs.json", "{}\n")
    assert _prove(manifest) == 0
    edit = _write(layout.slot_dir("slot-1") / "edit.txt", "kept\n")

    assert _prove(manifest, *(["--fresh"] if fresh else [])) == 0

    assert edit.exists() is kept
    assert syncs == [layout.slot_dir("slot-1")] * (2 if fresh else 1)


@pytest.mark.parametrize("name", ["missing.json", "folder"], ids=["missing", "directory"])
def test_prove_refuses_a_manifest_that_is_not_a_file_before_it_binds_a_copy(
    name: str,
    layout: workspace.Layout,
    started: _StartedCommands,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    (tmp_path / "folder").mkdir()
    manifest = (tmp_path / name).resolve()

    code = _prove(manifest)

    assert code == workspace.REFUSED
    assert capsys.readouterr().err == f"workspace: manifest {manifest} is not a file\n"
    assert started == []
    assert not layout.flow_dir.exists()


@pytest.mark.parametrize(
    ("extra", "option"),
    [
        (("--workspace", "/elsewhere"), "--workspace"),
        (("--workspace=/elsewhere",), "--workspace"),
        (("--work", "/elsewhere"), "--workspace"),
        (("--scratch-root", "/elsewhere"), "--scratch-root"),
        (("--scratch-root=/elsewhere",), "--scratch-root"),
        (("--scr", "/elsewhere"), "--scratch-root"),
        (("--json", "/elsewhere/proofs.json"), "--json"),
        (("--json=/elsewhere/proofs.json",), "--json"),
        (("--js", "/elsewhere/proofs.json"), "--json"),
    ],
    ids=[
        "workspace",
        "workspace-equals",
        "workspace-prefix",
        "scratch-root",
        "scratch-root-equals",
        "scratch-root-prefix",
        "json",
        "json-equals",
        "json-prefix",
    ],
)
def test_prove_refuses_an_extra_argument_that_would_replace_one_of_its_own_flags(
    extra: tuple[str, ...],
    option: str,
    layout: workspace.Layout,
    started: _StartedCommands,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # The proof script's parser keeps the last value, so an extra ``--json`` (or its prefix)
    # would move the proof's evidence out of the flow folder, where ``gc`` never looks.
    manifest = _write(tmp_path / "proofs.json", "{}\n")

    code = _prove(manifest, "--", "--only", "1", *extra)

    assert code == workspace.REFUSED
    assert capsys.readouterr().err == (
        "workspace: prove passes --workspace, --scratch-root and --json itself, so the proof's "
        f"evidence stays in the flow folder; drop {option} from the arguments after --\n"
    )
    assert started == []
    assert not layout.flow_dir.exists()


@pytest.mark.parametrize(
    ("tools", "message"),
    [
        ((), "git is not on PATH, so the shared tree cannot be listed, copied or diffed"),
        (("git",), "uv is not on PATH, so no copy can be synced"),
    ],
    ids=["no-git", "no-uv"],
)
def test_run_refuses_a_tool_missing_from_path_before_its_header(
    tools: tuple[str, ...],
    message: str,
    layout: workspace.Layout,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    folder = tmp_path / "bin"
    folder.mkdir()
    for tool in tools:
        real = shutil.which(tool)
        assert real is not None
        _write(folder / tool, f'#!/bin/sh\nexec {real} "$@"\n').chmod(0o755)

    def for_flow(flow: str) -> workspace.Layout:
        return workspace.Layout(layout.repo_root, layout.base, flow)

    monkeypatch.setattr(workspace.Layout, "for_flow", staticmethod(for_flow))
    monkeypatch.setenv("PATH", str(folder))

    code = workspace.main(
        [
            "run",
            _ADDRESS,
            "--",
            "pytest",
        ],
    )

    assert code == workspace.REFUSED
    assert capsys.readouterr().err == f"workspace: {message}\n"
    assert not layout.run_log.exists()


def test_gc_refuses_while_a_prove_waits_for_its_copy(
    layout: workspace.Layout,
    actors: _Actors,
    tmp_path: Path,
) -> None:
    manifest = _write(tmp_path / "proofs.json", "{}\n")
    actors.start("P", "prove", _ADDRESS, str(manifest), pauses=("bound",))
    assert actors.reached("P", "bound")

    refused = _gc_refused(layout)
    actors.go("P", "bound")

    assert refused
    assert actors.finish("P")[0] == 0
    assert actors.ran("P") == {"slot": "slot-1", "seen": []}


def test_a_second_prove_waits_for_the_first_to_finish_in_their_copy(
    actors: _Actors,
    tmp_path: Path,
) -> None:
    manifest = _write(tmp_path / "proofs.json", "{}\n")
    actors.start("P", "prove", _ADDRESS, str(manifest), pauses=("in",))
    assert actors.reached("P", "in")
    actors.start("Q", "prove", _ADDRESS, str(manifest))
    assert actors.reached("Q", "bound")

    waited = not actors.reached("Q", "in", within=0.5)
    actors.go("P", "in")

    assert waited
    assert [actors.finish("P")[0], actors.finish("Q")[0]] == [0, 0]
    assert actors.ran("Q") == {"slot": "slot-1", "seen": ["P"]}


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
# Ctrl-Z; a background job reading from or writing to its terminal.
JOB_SIGNALS = (signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU)

# Stands in for a command a run starts: it writes ``<pid> <pgid> <grandchild pid>`` to
# ``S_READY`` once it has started a grandchild (pytest -> xdist worker), appends the
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
# ``S_LOCK`` it hands the command, writes what ``stream`` returned to ``S_RESULT``, writes a
# footer to stderr as ``execute`` does, and exits with the code ``stream`` returned (``run``
# instead ends by signal ``N`` on a stop's ``128 + N``).
# ``starting`` signals the process itself as the command is being started, before the fork;
# ``started`` signals it once the command has started, before ``stream`` has recorded it;
# ``started-continued`` then sends it ``SIGCONT`` as well, each signal handled before the next;
# ``pipe-<stream>`` points that stream (``stdout`` or ``stderr``) at a pipe whose reader has
# gone, ``tty-<stream>`` at a terminal whose master side has closed; ``<sink>-both`` points
# the descriptors 1 and 2 at that one dead file, as ``2>&1 | head`` does.
_STREAM_RUN = """
import json, os, signal, subprocess, sys
from pathlib import Path

from scripts import workspace

mode = os.environ["S_MODE"]
signum = int(os.environ["S_SIGNUM"])


def deliver(signal_number):
    # A call of its own: the handler of one runs on entering the next, never after it.
    os.kill(os.getpid(), signal_number)


if mode in {"starting", "started", "started-continued"}:

    class SignalledPopen(subprocess.Popen):
        def __init__(self, *args, **kwargs):
            if mode == "starting":
                deliver(signum)
            super().__init__(*args, **kwargs)
            if mode.startswith("started"):
                deliver(signum)
            if mode == "started-continued":
                deliver(signal.SIGCONT)

    subprocess.Popen = SignalledPopen
if mode.startswith(("pipe-", "tty-")):
    sink, name = mode.split("-")
    reader, writer = os.pipe() if sink == "pipe" else os.openpty()
    os.close(reader)
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    if name == "both":
        os.dup2(writer, 1)
        os.dup2(writer, 2)
        os.close(writer)
    else:
        setattr(sys, name, os.fdopen(writer, "w"))
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
sys.stderr.write(f"workspace run exit {finished.code}\\n")
sys.exit(finished.code)
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

# Stands in for ``uv`` on ``PATH``: ``uv run ... -- <command>`` appends its arguments to
# ``<WSTEST_SYNC>.runs``, one JSON list a line, and runs ``<command>`` in the ``--directory``
# as a child it waits for, then exits with its code; like uv it forwards every stop signal it
# gets to that child, ``SIGINT`` after 0.2 s and the others at once. ``uv sync`` writes its pid
# to ``WSTEST_SYNC`` and blocks until ``<WSTEST_SYNC>.release``.
_UV = """
import json, os, signal, subprocess, sys, threading, time
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
with open(os.environ["WSTEST_SYNC"] + ".runs", "a", encoding="utf-8") as runs:
    runs.write(json.dumps(arguments) + "\\n")
command = arguments[arguments.index("--") + 1 :]
child = subprocess.Popen(command, cwd=arguments[arguments.index("--directory") + 1])


def forward(signum, _frame):
    def send():
        if child.poll() is None:
            child.send_signal(signum)

    threading.Timer(0.2 if signum == signal.SIGINT else 0.0, send).start()


for stop_signal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
    signal.signal(stop_signal, forward)
code = child.wait()
sys.exit(128 - code if code < 0 else code)
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
        self.err: str = ""
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
        """Return the code and stop signal ``stream`` returned; fail on a run that never ends.

        What the run wrote to its own stderr lands in ``err``.
        """
        try:
            _, err = self.process.communicate(timeout=timeout)
            if isinstance(err, str):
                self.err = err
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


@pytest.mark.parametrize("code", [0, 7])
@pytest.mark.parametrize("sink", ["pipe", "tty"])
@pytest.mark.parametrize("stream", ["stdout", "stderr", "both"])
def test_a_reader_gone_from_the_run_keeps_the_log_and_never_blocks_the_command(
    tmp_path: Path,
    stream_runs: list[_StreamRun],
    stream: str,
    sink: str,
    code: int,
) -> None:
    # A pipe whose reader exited (``| head``) or a terminal whose master side closed, on one
    # stream or on both (``2>&1 | head``): the echo fails, the log does not.
    run = _StreamRun(
        tmp_path,
        mode=f"{sink}-{stream}",
        command=f"{_FLOOD}\nsys.exit({code})",
        stream="stdout" if stream == "both" else stream,
    )
    stream_runs.append(run)

    assert run.finish(timeout=15) == (code, None)
    assert run.log.stat().st_size == len("header\n") + 20000 * 100
    # The run ends with the command's own code: nothing it left buffered for the dead sink fails
    # its exit.
    assert run.process.returncode == code
    assert "Exception ignored" not in run.err


@pytest.mark.parametrize(
    ("error", "names"),
    [
        (errno.EPIPE, "devnull"),
        (errno.EIO, "devnull"),
        (errno.ENOSPC, "sink"),
        (errno.EFBIG, "sink"),
    ],
    ids=[
        "EPIPE",
        "EIO",
        "ENOSPC",
        "EFBIG",
    ],
)
def test_only_a_sink_whose_reader_is_gone_is_pointed_at_devnull(
    tmp_path: Path,
    error: int,
    names: str,
) -> None:
    # A full disk is no reader gone: the sink is dropped, its descriptor still names its file.

    class FailingSink(io.BufferedWriter):
        @override
        def write(self, buffer: object, /) -> int:
            raise OSError(error, os.strerror(error))

    reader, writer = os.pipe()
    _ = os.write(writer, b"chunk\n")
    os.close(writer)
    log = io.BytesIO()
    path = tmp_path / "sink"
    with os.fdopen(reader, "rb") as source, FailingSink(io.FileIO(path, "wb")) as sink:
        workspace._pump(source, sink, log, threading.Lock())
        found = os.fstat(sink.fileno())

    expected = Path(os.devnull).stat() if names == "devnull" else path.stat()
    assert log.getvalue() == b"chunk\n"
    assert (found.st_dev, found.st_ino) == (expected.st_dev, expected.st_ino)


@pytest.fixture
def started_commands(monkeypatch: pytest.MonkeyPatch) -> list[subprocess.Popen[bytes]]:
    """Every command an in-process ``stream`` starts, in order."""
    processes: list[subprocess.Popen[bytes]] = []
    real = workspace._StopRelay.started

    def record(self: workspace._StopRelay, process: subprocess.Popen[bytes]) -> None:
        processes.append(process)
        real(self, process)

    monkeypatch.setattr(workspace._StopRelay, "started", record)
    return processes


def _stream_in_process(tmp_path: Path, program: str) -> workspace.Finished:
    return workspace.stream([sys.executable, "-c", program], {}, tmp_path / "run.log", "header\n")


def _interrupt_the_first_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the command's first ``wait`` raise ``KeyboardInterrupt``: an error out of the run."""
    recorded = workspace._StopRelay.started

    def started(self: workspace._StopRelay, process: subprocess.Popen[bytes]) -> None:
        recorded(self, process)
        real = process.wait
        interrupted: list[bool] = []

        def wait(timeout: float | None = None) -> int:
            if not interrupted:
                interrupted.append(True)
                raise KeyboardInterrupt
            return real(timeout)

        monkeypatch.setattr(process, "wait", wait)

    monkeypatch.setattr(workspace._StopRelay, "started", started)


def _assert_pipes_closed(processes: list[subprocess.Popen[bytes]]) -> None:
    (process,) = processes
    assert process.stdout is not None
    assert process.stderr is not None
    assert process.stdout.closed
    assert process.stderr.closed


@pytest.mark.parametrize("code", [0, 3], ids=["success", "nonzero"])
def test_an_in_process_stream_closes_the_pipes_it_read(
    tmp_path: Path,
    started_commands: list[subprocess.Popen[bytes]],
    code: int,
) -> None:
    # Left open, the pipes reach the garbage collector as an unclosed-file ``ResourceWarning``.
    finished = _stream_in_process(
        tmp_path,
        f"import sys; print('out'); print('err', file=sys.stderr); sys.exit({code})",
    )

    assert finished == workspace.Finished(code)
    _assert_pipes_closed(started_commands)


@pytest.mark.parametrize("failure", ["interrupt", "no-thread"])
def test_an_interrupted_stream_kills_its_command_and_closes_the_pipes(
    tmp_path: Path,
    started_commands: list[subprocess.Popen[bytes]],
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    error: type[BaseException] = KeyboardInterrupt
    if failure == "interrupt":
        _interrupt_the_first_wait(monkeypatch)
    else:
        # The second reader thread cannot start: the first is already reading.
        real = threading.Thread.start
        starts: list[threading.Thread] = []

        def start(self: threading.Thread) -> None:
            starts.append(self)
            if len(starts) == 2:
                raise RuntimeError("can't start new thread")
            real(self)

        monkeypatch.setattr(threading.Thread, "start", start)
        error = RuntimeError

    # Left running, the command would hold the run's leases; closing the pipes would wait on it.
    with pytest.raises(error, match=None if failure == "interrupt" else "can't start new thread"):
        _ = _stream_in_process(tmp_path, "import time; print('up', flush=True); time.sleep(15)")

    _assert_pipes_closed(started_commands)
    assert started_commands[0].returncode == -signal.SIGKILL


def test_a_stream_with_no_byte_stdout_starts_no_command(
    tmp_path: Path,
    started_commands: list[subprocess.Popen[bytes]],
) -> None:
    # An in-process caller that redirected stdout to text: the error comes before any command runs.
    started = time.monotonic()
    with contextlib.redirect_stdout(io.StringIO()), pytest.raises(AttributeError):
        _ = _stream_in_process(tmp_path, "import time; time.sleep(15)")

    assert time.monotonic() - started < 5
    assert started_commands == []


@pytest.mark.parametrize("ending", ["normal", "interrupted"])
def test_a_slow_reader_is_joined_before_the_pipes_close(
    tmp_path: Path,
    started_commands: list[subprocess.Popen[bytes]],
    monkeypatch: pytest.MonkeyPatch,
    ending: str,
) -> None:
    # A reader still copying when the pipes close loses the rest of the output.
    real = workspace._pump
    ended: list[int] = []

    def slow(
        source: io.BufferedReader,
        sink: BinaryIO,
        log: BinaryIO,
        lock: threading.Lock,
    ) -> None:
        time.sleep(0.3)
        try:
            real(source, sink, log, lock)
        finally:
            ended.append(1)

    monkeypatch.setattr(workspace, "_pump", slow)
    if ending == "interrupted":
        _interrupt_the_first_wait(monkeypatch)
        with pytest.raises(KeyboardInterrupt):
            _ = _stream_in_process(tmp_path, "import time; time.sleep(15)")
        assert started_commands[0].returncode == -signal.SIGKILL
    else:
        assert _stream_in_process(tmp_path, "print('x' * 99)") == workspace.Finished(0)
        assert (tmp_path / "run.log").stat().st_size == len("header\n") + 100

    assert ended == [1, 1]
    _assert_pipes_closed(started_commands)


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


@pytest.mark.parametrize("signum", JOB_SIGNALS, ids=[signum.name for signum in JOB_SIGNALS])
@pytest.mark.parametrize("mode", ["starting", "started"])
def test_a_suspend_before_the_command_is_recorded_stops_it_with_the_run_once_it_is(
    tmp_path: Path,
    terminal: tuple[int, int],
    stream_runs: list[_StreamRun],
    mode: str,
    signum: signal.Signals,
) -> None:
    _master, tty = terminal
    run = _StreamRun(tmp_path, mode=mode, signum=signum, command=_BEATING, tty=tty)
    stream_runs.append(run)

    assert _poll(lambda: "stopped" in run.shell_said())
    # Stopped with the run: a command left running would beat on, holding the run's leases.
    stopped_at = run.beats()
    time.sleep(0.5)
    assert run.beats() == stopped_at
    Path(f"{run.shell}.fg").touch()  # fg
    assert _poll(lambda: run.beats() > stopped_at + 3)
    command, _, _ = run.pids()
    assert not _is_stopped(command)
    run.release()

    assert _poll(lambda: "exited 0" in run.shell_said())
    assert run.shell_said().count("stopped") == 1
    assert json_list(json_loads(run.result.read_text(encoding="utf-8"))) == [0, None]
    assert run.log.read_text(encoding="utf-8").endswith("released\n")


@pytest.mark.parametrize("signum", JOB_SIGNALS, ids=[signum.name for signum in JOB_SIGNALS])
def test_a_continue_before_the_command_is_recorded_drops_the_suspend_before_it(
    tmp_path: Path,
    terminal: tuple[int, int],
    stream_runs: list[_StreamRun],
    signum: signal.Signals,
) -> None:
    _master, tty = terminal
    run = _StreamRun(
        tmp_path,
        mode="started-continued",
        signum=signum,
        command=_BEATING,
        tty=tty,
    )
    stream_runs.append(run)

    assert _poll(lambda: run.beats() > 10)
    run.release()

    assert _poll(lambda: "exited 0" in run.shell_said())
    assert "stopped" not in run.shell_said()
    assert json_list(json_loads(run.result.read_text(encoding="utf-8"))) == [0, None]


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


@pytest.mark.parametrize("signum", STOP_SIGNALS, ids=[signum.name for signum in STOP_SIGNALS])
def test_a_run_starts_its_command_with_no_uv_between_so_a_stop_reaches_it_once(
    layout: workspace.Layout,
    actors: _Actors,
    stand_in_uv: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    signum: signal.Signals,
) -> None:
    # ``uv run`` stays the parent of what it runs and forwards every stop it gets, so a
    # command started under it would get the relayed stop and then uv's copy, SIGINT 0.2 s
    # later, inside a teardown that takes a second. ``uv run`` only resolves the copy's
    # environment; the run starts the command itself, which gets one stop and tears down.
    monkeypatch.setenv("S_ON_STOP", "teardown")
    command = (
        "--",
        sys.executable,
        "-c",
        _COMMAND,
    )
    actors.start("A", "run", _ADDRESS, *command, bin=str(stand_in_uv), real_stream=True)
    assert _poll((tmp_path / "ready").exists)
    process = actors.processes["A"]
    pid = int((tmp_path / "ready").read_text(encoding="utf-8").split()[0])
    parent = subprocess.run(
        [
            "ps",
            "-o",
            "ppid=",
            "-p",
            str(pid),
        ],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()

    os.kill(process.pid, signum)
    code, out, _err = actors.finish("A")

    assert _stops_got(tmp_path) == [signum.name]
    assert "torn down" in out
    # ``uv run`` resolved the copy's environment, and the run itself is the command's parent.
    runs = (tmp_path / "sync-ready.runs").read_text(encoding="utf-8").splitlines()
    copy = str(layout.slot_dir("slot-1"))
    assert [json_loads(line) for line in runs] == [
        [
            "run",
            "--directory",
            copy,
            "--frozen",
            "--group",
            "pg",
            "--",
            "env",
            "-0",
        ],
    ]
    assert parent == str(process.pid)
    assert code == 128 + signum
    record = _run_record(layout)
    assert (record["exit"], record["stopped_by"]) == (3, signum.name)


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

    assert held == [(7, 8)] * 4


def test_a_stopped_gate_runs_no_later_suite_and_ends_by_the_signal(
    layout: workspace.Layout,
    syncs: _Syncs,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    for name in ("pyproject.toml", "uv.lock"):
        _ = _write(layout.repo_root / name, f"{name}\n")
    streamed: list[tuple[list[str], Path | None, list[tuple[int, int]]]] = []

    def stopped_stream(
        command: list[str],
        _env: dict[str, str],
        log_path: Path,
        header: str,
        cwd: Path | None = None,
        *,
        holding: tuple[int, ...] = (),
    ) -> workspace.Finished:
        streamed.append(
            (command, cwd, [(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in holding]),
        )
        _ = _write(log_path, header)
        return workspace.Finished(128 + signal.SIGINT, signal.SIGINT)

    monkeypatch.setattr(workspace, "uv_launch", _launch_as_given)
    monkeypatch.setattr(workspace, "stream", stopped_stream)

    code = workspace.gate(layout, ["lint", "default"])

    out = capsys.readouterr().out
    assert code == 128 + signal.SIGINT
    assert syncs == [layout.gate_dir]
    ((command, cwd, holding),) = streamed
    assert command[-3:] == list(workspace.GATE_SUITES["lint"][0])
    # The suite runs in the gate's copy of the tree, never the working tree.
    assert cwd == layout.gate_dir
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


def test_the_floor_suite_installs_and_runs_holding_the_locks_the_gate_holds(
    layout: workspace.Layout,
    syncs: _Syncs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("pyproject.toml", "uv.lock"):
        _ = _write(layout.repo_root / name, f"{name}\n")
    installed: list[list[tuple[int, int]]] = []
    streamed: list[tuple[list[str], list[tuple[int, int]]]] = []

    def floor_venv(_layout: workspace.Layout, holding: Sequence[int] = ()) -> object:
        installed.append([(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in holding])
        return {
            "python": "floor-python",
            "pins": {},
            "key": "key",
            "reused": False,
        }

    def recorded_stream(
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
        return workspace.Finished(0)

    monkeypatch.setattr(workspace, "ensure_floor_venv", floor_venv)
    monkeypatch.setattr(workspace, "stream", recorded_stream)

    code = workspace.gate(layout, [workspace.FLOOR_SUITE])

    assert code == 0
    ((command, holding),) = streamed
    assert command == ["floor-python", "-m", *workspace.GATE_SUITES[workspace.FLOOR_SUITE][0]]
    # The copy's sync, the floor install and the suite hold the flow's lease and the gate's lock.
    locks = [layout.flow_dir, layout.flow_dir / "gate.lock"]
    files = [(path.stat().st_dev, path.stat().st_ino) for path in locks]
    assert syncs.holding == [files]
    assert installed == [files]
    assert holding == files


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
