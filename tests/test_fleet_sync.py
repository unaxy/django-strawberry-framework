"""Repo-tooling tests for the fleet sync of private working copies, pins, evidence and main.

Two fleet machines are two home folders under ``tmp_path``, each with its own
checkout at ``~/projects/django-strawberry-framework``. Only the network
boundary is faked: a ``tailscale`` on ``PATH`` prints the tailnet, and an
``ssh`` on ``PATH`` runs the remote command locally with that machine's
``HOME`` and ``DSF_MACHINE_ID``, so real git, real rsync (driven through that
``ssh``, as on the fleet) and the real agents of both machines do the work.
The rows that matter most are the ones whose failure would lose or misplace
work: a replica is never synced back or overwritten once edited, two homes stop
the copy, a handoff keeps whichever side changed, a removal reaches only an
unchanged replica, and main only ever fast-forwards. A live ``/graphql/``
request has no wire shape for syncing machines, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

import contextlib
import dataclasses
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Generator, Sequence
from pathlib import Path

import pytest
from typing_extensions import override

from docs.fleet.scripts import fleet as fleet_rules
from docs.fleet.scripts import fleet_sync
from scripts import _git, work, workspace
from tests._idioms import json_list, json_loads, json_object

NAME = "spike-fleet-probe"
#: ``plistlib.loads``, its result typed ``object`` for the caller to narrow.
_load_plist: Callable[[bytes], object] = plistlib.loads
SCRIPTS = str(Path(fleet_sync.__file__).resolve().parent)

FAKE_SSH = """\
#!/bin/sh
while [ $# -gt 0 ]; do
  case $1 in
    -o|-p|-l|-i|-F|-E|-c|-m|-J|-b|-D|-L|-R|-W|-S) shift 2 ;;
    -*) shift ;;
    *) break ;;
  esac
done
host=$1
shift
entry=$(grep "^$host " "$FAKE_SSH_MAP") || {
  echo "Host key verification failed." >&2
  exit 255
}
home=$(echo "$entry" | cut -d' ' -f2)
id=$(echo "$entry" | cut -d' ' -f3)
cd "$home" || exit 255
HOME=$home DSF_MACHINE_ID=$id exec sh -c "$*"
"""


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(content, encoding="utf-8")
    return path


def _git_out(root: Path, *args: str) -> str:
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
        env=_git.repository_env(),
    )
    return result.stdout


def _commit(root: Path, path: str, content: str) -> str:
    _ = _write(root / path, content)
    _ = _git_out(root, "add", path)
    _ = _git_out(root, "commit", "-q", "-m", f"edit {path}")
    return _git_out(root, "rev-parse", "HEAD").strip()


def _row(name: str) -> dict[str, object]:
    """Return the ``machines.json`` row of fake machine ``name``: its ssh alias and id alike."""
    return {
        "name": name,
        "ssh": name,
        "os": "macos" if sys.platform == "darwin" else "linux",
        "repo": "~/projects/django-strawberry-framework",
        "weight": {"light": 1.0, "heavy": 1.0},
        "floors": {"light": {}, "heavy": {}},
    }


@dataclasses.dataclass
class Fleet:
    """Two fake machines: ``a`` (this one, the run's) and ``b`` (a peer over the fake ssh)."""

    tmp: Path
    monkeypatch: pytest.MonkeyPatch
    capsys: pytest.CaptureFixture[str]
    peers: dict[str, dict[str, object]] = dataclasses.field(default_factory=dict)

    @property
    def repo_a(self) -> Path:
        return self.tmp / "a" / "projects" / "django-strawberry-framework"

    @property
    def repo_b(self) -> Path:
        return self.tmp / "b" / "projects" / "django-strawberry-framework"

    def peer(
        self,
        label: str,
        home: Path | None,
        *,
        os_name: str = "linux",
        online: bool = True,
    ) -> None:
        """List a tailnet peer; ``home`` maps its ssh name to that fake machine."""
        self.peers[label] = {
            "HostName": label,
            "DNSName": f"{label}.tail0.ts.net.",
            "OS": os_name,
            "Online": online,
        }
        if home is not None:
            with (self.tmp / "ssh-map").open("a", encoding="utf-8") as handle:
                _ = handle.write(f"{label} {home} {label}\n")
        self.write_tailnet()

    def write_tailnet(self) -> None:
        document = {
            "Self": {
                "HostName": "a",
                "DNSName": "a.tail0.ts.net.",
                "OS": "macOS" if sys.platform == "darwin" else "linux",
                "Online": True,
            },
            "Peer": self.peers,
        }
        _ = _write(self.tmp / "tailnet.json", json.dumps(document))

    def run(self, *args: str, scripts: bool = True) -> tuple[int, dict[object, object]]:
        """Run ``fleet_sync.py args --json`` on machine ``a``; return its exit and document."""
        extra = ["--remote-scripts", SCRIPTS] if scripts else []
        _ = self.capsys.readouterr()
        code = fleet_sync.main([*args, "--json", *extra])
        out = self.capsys.readouterr().out
        return code, json_object(json_loads(out)) if out.strip() else {}

    def at_b(self) -> None:
        """Make ``work.py`` calls in this process act as machine ``b``."""
        self.monkeypatch.setattr(work, "REPO_ROOT", self.repo_b)
        self.monkeypatch.setenv(fleet_rules.MACHINE_ENV, "b")

    def at_a(self) -> None:
        """Make ``work.py`` calls in this process act as machine ``a`` again."""
        self.monkeypatch.setattr(work, "REPO_ROOT", self.repo_a)
        self.monkeypatch.setenv(fleet_rules.MACHINE_ENV, "a")

    def repo(self, label: str) -> Path:
        return self.tmp / label / "projects" / "django-strawberry-framework"

    def machine(self, label: str) -> Path:
        """Add a third machine ``label`` (no ``machines.json`` row: reached by its MagicDNS name)."""
        repo = self.repo(label)
        repo.parent.mkdir(parents=True)
        _ = _git_out(repo.parent, "clone", "-q", str(self.repo_a), repo.name)
        _venv_python(repo)
        self.peer(label, self.tmp / label)
        return repo

    def at(self, label: str) -> None:
        """Make ``work.py`` calls in this process act as machine ``label``."""
        self.monkeypatch.setattr(work, "REPO_ROOT", self.repo(label))
        self.monkeypatch.setenv(fleet_rules.MACHINE_ENV, label)

    @contextlib.contextmanager
    def running_on(self, label: str) -> Generator[None, None, None]:
        """Make :meth:`run` run on machine ``label``, ``a`` one of its peers over the fake ssh."""
        here = self.peers[label]
        others = {key: value for key, value in self.peers.items() if key != label}
        others["a"] = {
            "HostName": "a",
            "DNSName": "a.tail0.ts.net.",
            "OS": "linux",
            "Online": True,
        }
        tailnet = _write(
            self.tmp / f"tailnet-{label}.json",
            json.dumps({"Self": here, "Peer": others}),
        )
        if not (self.repo_a / ".venv").exists():
            _venv_python(self.repo_a)
            with (self.tmp / "ssh-map").open("a", encoding="utf-8") as handle:
                _ = handle.write(f"a {self.tmp / 'a'} a\n")
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("FAKE_TAILNET", str(tailnet))
            patch.setenv("HOME", str(self.tmp / label))
            patch.setenv(fleet_rules.MACHINE_ENV, label)
            patch.setattr(fleet_sync, "REPO_ROOT", self.repo(label))
            patch.setattr(work, "REPO_ROOT", self.repo(label))
            yield


def _results(document: dict[object, object]) -> list[tuple[str, str, str]]:
    return [
        (str(entry.get("result")), str(entry.get("subject")), str(entry.get("detail")))
        for entry in (json_object(item) for item in json_list(document, "rows"))
    ]


def _machines(document: dict[object, object]) -> dict[str, dict[object, object]]:
    return {
        str(entry.get("machine")): entry
        for entry in (json_object(item) for item in json_list(document, "machines"))
    }


def _note(copy: Path, scope: str = "--local") -> dict[str, str]:
    return work._config_values(copy, scope)


def _venv_python(root: Path) -> None:
    """Give a fake checkout the ``.venv/bin/python`` the remote wrapper runs: this interpreter."""
    wrapper = _write(
        root / ".venv" / "bin" / "python",
        f'#!/bin/sh\nexec "{sys.executable}" "$@"\n',
    )
    wrapper.chmod(0o755)


def _make_checkout(root: Path) -> None:
    _ = _write(root / "django_strawberry_framework" / "__init__.py", "VALUE = 1\n")
    _ = _write(root / ".gitignore", ".work/\n.venv/\n__pycache__/\n*.pyc\n.python-version\n")
    _ = _write(root / "gone.txt", "to delete\n")
    machines = {"machines": [_row("a"), _row("b")]}
    _ = _write(root / "docs" / "fleet" / "machines.json", json.dumps(machines, indent=2))
    _ = _git_out(root, "init", "-q", "-b", "main")
    _ = _git_out(root, "add", "-A")
    _ = _git_out(root, "commit", "-q", "-m", "initial")


@pytest.fixture
def fleet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> Fleet:
    if shutil.which("rsync") is None:
        pytest.skip("no rsync on this machine")
    if work.cwd_users(tmp_path) is None:
        pytest.skip("neither /proc nor lsof can take a process census here")
    for name in work.LOCATING_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv(workspace.ROOT_ENV, str(tmp_path / "ws"))
    state = Fleet(tmp_path, monkeypatch, capsys)
    _make_checkout(state.repo_a)
    state.repo_b.parent.mkdir(parents=True)
    _ = _git_out(state.repo_b.parent, "clone", "-q", str(state.repo_a), state.repo_b.name)
    _venv_python(state.repo_b)
    bin_dir = tmp_path / "bin"
    _write(bin_dir / "ssh", FAKE_SSH).chmod(0o755)
    tailnet = tmp_path / "tailnet.json"
    _write(bin_dir / "tailscale", f'#!/bin/sh\ncat "${{FAKE_TAILNET:-{tailnet}}}"\n').chmod(0o755)
    _ = _write(tmp_path / "ssh-map", f"b {tmp_path / 'b'} b\n")
    monkeypatch.setenv("FAKE_SSH_MAP", str(tmp_path / "ssh-map"))
    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), os.environ["PATH"]]))
    monkeypatch.setenv("HOME", str(tmp_path / "a"))
    monkeypatch.setattr(fleet_sync, "REPO_ROOT", state.repo_a)
    state.at_a()
    state.peer("b", None)
    return state


def _new(name: str = NAME, *extra: str) -> Path:
    assert (
        work.main(
            [
                "new",
                name,
                "--no-setup",
                "--purpose",
                "a probe",
                *extra,
            ],
        )
        == 0
    )
    copy = work.locate(work.REPO_ROOT, name)
    assert copy.path is not None
    return copy.path


def _age(path: Path, seconds: float = 3600) -> None:
    """Move every mtime under ``path`` (``.git`` and ``.venv`` aside) back by ``seconds``."""
    past = time.time() - seconds
    for directory, dirnames, filenames in os.walk(path):
        dirnames[:] = [name for name in dirnames if name not in work.UNWATCHED_DIRS]
        for name in filenames:
            os.utime(Path(directory) / name, (past, past), follow_symlinks=False)
        os.utime(directory, (past, past))


# --------------------------------------------------------------------------------------------
# Machines
# --------------------------------------------------------------------------------------------


def test_status_names_every_online_machine_and_why_one_is_not_synced(fleet: Fleet) -> None:
    empty = fleet.tmp / "y"
    empty.mkdir()
    other = fleet.tmp / "r" / "projects" / "django-strawberry-framework"
    other.parent.mkdir(parents=True)
    _ = _git_out(other.parent, "init", "-q", "-b", "main", other.name)
    _ = _commit(other, "x.txt", "unrelated\n")
    _ = _write(other / ".gitignore", ".work/\n")
    _venv_python(other)
    unknown = fleet.tmp / "x" / "projects" / "django-strawberry-framework"
    unknown.parent.mkdir(parents=True)
    _ = _git_out(unknown.parent, "clone", "-q", str(fleet.repo_a), unknown.name)
    _venv_python(unknown)
    fleet.peer("c", None)
    fleet.peer("w", None, os_name="windows")
    fleet.peer("y", empty)
    fleet.peer("r", fleet.tmp / "r")
    fleet.peer("x", fleet.tmp / "x")
    fleet.peer("gone", None, online=False)
    code, document = fleet.run("status")
    assert code == 0
    machines = _machines(document)
    assert set(machines) == {
        "a",
        "b",
        "c",
        "w",
        "y",
        "r",
        "x",
    }
    assert machines["a"]["qualified"] is True
    assert machines["b"]["qualified"] is True
    assert machines["b"]["ssh"] == "b"
    assert "Host key verification failed" in str(machines["c"]["reason"])
    assert "not supported yet" in str(machines["w"]["reason"])
    assert "no checkout at ~/projects/django-strawberry-framework" in str(machines["y"]["reason"])
    assert "root commit differs" in str(machines["r"]["reason"])
    assert machines["x"]["qualified"] is True
    suggested = json_object(machines["x"], "suggested_row")
    assert (suggested["name"], suggested["aliases"]) == ("x", [])


def test_a_peer_without_the_script_or_ignoring_no_work_folder_is_not_synced(fleet: Fleet) -> None:
    code, document = fleet.run("status", scripts=False)
    assert code == 0
    assert "lacks docs/fleet/scripts/fleet_sync.py" in str(_machines(document)["b"]["reason"])
    _ = _write(fleet.repo_b / ".gitignore", ".venv/\n")
    _, document = fleet.run("status")
    assert "does not ignore .work/" in str(_machines(document)["b"]["reason"])


def test_a_checkout_outside_projects_is_bad_setup(fleet: Fleet) -> None:
    fleet.monkeypatch.setenv("HOME", str(fleet.tmp / "elsewhere"))
    code, _ = fleet.run("status")
    assert code == 2


def _setup_error(fleet: Fleet, *args: str) -> str:
    """Run ``fleet_sync.py args`` on machine ``a``, expecting bad setup; return its stderr."""
    _ = fleet.capsys.readouterr()
    code = fleet_sync.main(
        [
            *args,
            "--json",
            "--remote-scripts",
            SCRIPTS,
        ],
    )
    captured = fleet.capsys.readouterr()
    assert (code, captured.out) == (2, "")
    return captured.err


def test_sync_and_handoff_refuse_on_a_host_no_row_names_and_status_still_reports(
    fleet: Fleet,
) -> None:
    """Only a listed machine writes records naming itself; reading needs no row."""
    copy = _new()
    _age(copy)
    fleet.monkeypatch.setenv(fleet_rules.MACHINE_ENV, "stranger")
    for command in (["sync"], ["handoff", NAME]):
        error = _setup_error(fleet, *command)
        assert "this machine is 'stranger' ($DSF_MACHINE_ID)" in error
        assert "listed: a, b" in error
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()
    assert fleet.run("status")[0] == 0


def test_a_typed_machine_name_selects_its_row_through_its_aliases_case_and_domain() -> None:
    """``--machine``/``--to`` take the label, ssh, row or id as typed, or any stored-name form."""
    rows = [
        fleet_rules.Machine(
            name="rio-air",
            ssh="air-ssh",
            os="macos",
            repo="~/projects/django-strawberry-framework",
            weights={"light": 1.0, "heavy": 1.0},
            floors={"light": {}, "heavy": {}},
            aliases=("riordens-macbook-air",),
        ),
    ]
    listed = fleet_sync.Machine("rio-air", "air-ssh", "macos", local=False, row="rio-air")
    unlisted = fleet_sync.Machine("x", "x", "linux", local=False, row="", labels=("x",))
    for typed in (
        "rio-air",
        "air-ssh",
        "Rio-Air.lan",
        "Riordens-MacBook-Air.local",
    ):
        assert fleet_sync._named_by(listed, typed, rows), typed
    assert fleet_sync._named_by(unlisted, "X.tail0.ts.net", rows)
    for typed in (
        "rio-ubu",
        "x",
        "",
        " ",
        ".",
    ):
        assert not fleet_sync._named_by(listed, typed, rows), typed
    for typed in ("", " "):
        assert not fleet_sync._named_by(unlisted, typed, rows), typed


def test_an_empty_machine_filter_selects_no_peer(fleet: Fleet) -> None:
    """``--machine ""`` never matches an unlisted peer's empty row."""
    _ = fleet.machine("c")
    for typed in ("", " "):
        here, others = fleet_sync.find_machines(SCRIPTS, [typed])
        assert here.row == "a"
        assert others == [], typed


def test_handoff_to_a_machine_typed_with_a_domain_and_another_case(fleet: Fleet) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME, "--machine", "B.tail0.ts.net")[0] == 0
    code, document = fleet.run("handoff", NAME, "--to", "B.lan")
    assert code == 0, document
    assert _note(copy)["home"] == "b"


def test_sync_refuses_when_tailscale_names_this_machine_as_another_row(fleet: Fleet) -> None:
    fleet.monkeypatch.setenv(fleet_rules.MACHINE_ENV, "b")
    assert "Tailscale names this machine 'a'" in _setup_error(fleet, "sync")


# --------------------------------------------------------------------------------------------
# Clones
# --------------------------------------------------------------------------------------------


def test_sync_makes_a_replica_on_the_peer_that_is_marked_and_points_at_its_own_checkout(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "work.txt", "uncommitted work\n")
    (copy / "gone.txt").unlink()
    _ = _write(copy / ".venv" / "lib.txt", "platform venv\n")
    _ = _write(copy / "pkg" / "__pycache__" / "m.pyc", "bytecode")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert ("synced", NAME, "synced a -> b") in _results(document)
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert (replica / "work.txt").read_text(encoding="utf-8") == "uncommitted work\n"
    assert not (replica / "gone.txt").exists()
    assert not (replica / ".venv").exists()
    assert not (replica / "pkg" / "__pycache__").exists()
    note = _note(replica)
    assert note["replica"] == "true"
    assert note["home"] == "a"
    assert note["syncedfrom"] == "a"
    assert note["purpose"] == "a probe"
    assert note["syncedtree"] == work.content_tree(copy)
    assert "syncing" not in note
    assert _git_out(replica, "remote", "get-url", "parent").strip() == str(fleet.repo_b)
    assert _git_out(replica, "remote", "get-url", "--push", "parent").strip() == work.NO_PUSH
    assert (replica / ".git" / work.VENV_STALE).exists()
    assert work.pins(fleet.repo_b)[NAME]["start"] == work.pins(fleet.repo_a)[NAME]["start"]
    assert "replica" not in _note(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0
    assert ("fresh", NAME, "replica on b is fresh") in _results(document)


def test_an_edit_at_home_reaches_the_replica_and_a_replica_edit_stops_the_copy(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    _ = _write(copy / "later.txt", "home edit\n")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert (replica / "later.txt").read_text(encoding="utf-8") == "home edit\n"
    _ = _write(replica / "later.txt", "replica edit\n")
    _ = _write(copy / "later.txt", "second home edit\n")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert (replica / "later.txt").read_text(encoding="utf-8") == "replica edit\n"
    code, document = fleet.run("status", "--copy", NAME)
    assert code == 1
    [entry] = [json_object(item) for item in json_list(document, "copies")]
    assert json_object(entry, "replicas") == {"b": "changed"}


def test_a_copy_both_machines_hold_as_home_is_a_conflict(fleet: Fleet) -> None:
    _age(_new())
    fleet.at_b()
    _age(_new())
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any(
        result == "conflict" and "both hold" in detail for result, _s, detail in _results(document)
    )


def test_a_save_carried_to_a_second_home_stays_its_makers_and_rm_drop_saves_keeps_it(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    copy = _new()
    fleet.at_b()
    other = _new()
    assert set(work.recorded_pins(_note(other))) == {work.START_PIN}
    fleet.at_a()
    _ = _write(copy / "saved.txt", "a's work\n")
    assert work.main(["save", NAME]) == 0
    saved = work.pins(fleet.repo_a)[NAME]["save-1"]
    _age(copy)
    _age(other)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any(
        result == "conflict" and "both hold" in detail for result, _s, detail in _results(document)
    )
    assert work.pins(fleet.repo_b)[NAME]["save-1"] == saved
    fleet.at_b()
    assert set(work.recorded_pins(work.attributed_note(fleet.repo_b, _note(other)))) == {
        work.START_PIN,
    }
    _ = capsys.readouterr()
    assert work.main(["rm", NAME, "--drop-saves"]) == 0
    assert f"save-1 {saved[:12]}" in capsys.readouterr().out
    assert work.pins(fleet.repo_b)[NAME] == {"save-1": saved}


def test_a_busy_home_is_read_but_a_replica_a_process_works_in_is_left_alone(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    with subprocess.Popen(["sleep", "30"], cwd=copy) as process:
        try:
            assert fleet.run("sync", "--copy", NAME)[0] == 0
        finally:
            process.kill()
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert replica.is_dir()
    _ = _write(copy / "later.txt", "home edit\n")
    _age(copy)
    with subprocess.Popen(["sleep", "30"], cwd=replica) as process:
        try:
            code, document = fleet.run("sync", "--copy", NAME)
        finally:
            process.kill()
    assert code == 1
    assert any(
        result == "skip" and "works in it" in detail for result, _s, detail in _results(document)
    )
    assert not (replica / "later.txt").exists()


def test_save_land_and_rm_on_a_replica_refuse_and_name_the_home(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    fleet.at_b()
    for command in (["save", NAME], ["land", NAME], ["rm", NAME]):
        assert work.main(command) == 1
        assert f"{NAME} is a replica of a's copy" in capsys.readouterr().err


def test_handoff_moves_the_home_and_the_old_home_takes_the_new_homes_edits(fleet: Fleet) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    code, document = fleet.run("handoff", NAME, "--to", "b")
    assert code == 0, document
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert _note(replica)["replica"] == "false"
    assert _note(replica)["home"] == "b"
    assert _note(copy)["replica"] == "true"
    assert _note(copy)["home"] == "b"
    _ = _write(replica / "from-b.txt", "edited at the new home\n")
    _age(replica)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert ("synced", NAME, "synced b -> a") in _results(document)
    assert (copy / "from-b.txt").read_text(encoding="utf-8") == "edited at the new home\n"
    assert _note(copy)["syncedtree"] == work.content_tree(copy)


def test_handoff_to_an_edited_replica_keeps_its_edits_when_the_home_did_not_change(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(replica / "mistake.txt", "edited on the replica\n")
    _age(replica)
    code, document = fleet.run("handoff", NAME, "--to", "b")
    assert code == 0, document
    assert (replica / "mistake.txt").exists()
    assert _note(replica)["replica"] == "false"
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert (copy / "mistake.txt").read_text(encoding="utf-8") == "edited on the replica\n"


def test_a_handoff_chain_reaches_a_replica_whose_machine_missed_a_handoff(fleet: Fleet) -> None:
    repo_c = fleet.machine("c")
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica_c = repo_c / ".work" / "clones" / NAME
    assert _note(replica_c)["home"] == "a"
    fleet.peer("c", None, online=False)
    assert fleet.run("handoff", NAME, "--to", "b")[0] == 0
    home_b = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(home_b / "from-b.txt", "edited at the new home\n")
    _age(home_b)
    fleet.peer("c", None)
    with fleet.running_on("b"):
        code, document = fleet.run("handoff", NAME, "--to", "c")
    assert code == 0, document
    note = _note(replica_c)
    assert (note["replica"], note["home"], note["generation"]) == ("false", "c", "2")
    assert note["formerhomes"] == "a,b"
    assert (replica_c / "from-b.txt").read_text(encoding="utf-8") == "edited at the new home\n"
    assert (_note(home_b)["replica"], _note(home_b)["home"]) == ("true", "c")
    assert _note(copy)["home"] == "c"


def test_the_new_homes_tombstone_removes_a_replica_whose_machine_missed_the_handoff(
    fleet: Fleet,
) -> None:
    repo_c = fleet.machine("c")
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    fleet.peer("c", None, online=False)
    assert fleet.run("handoff", NAME, "--to", "b")[0] == 0
    fleet.at_b()
    _age(fleet.repo_b / ".work" / "clones" / NAME)
    assert work.main(["rm", NAME]) == 0
    fleet.at_a()
    fleet.peer("c", None)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert not (fleet.repo_a / ".work" / "clones" / NAME).exists()
    assert not (repo_c / ".work" / "clones" / NAME).exists()
    assert [entry.name.rsplit("-", 1)[-1] for entry in (repo_c / ".work" / "trash").iterdir()] == [
        work.KEPT_TRASH,
    ]


def test_handoff_with_the_home_offline_refuses_unless_forced_and_the_old_home_is_a_conflict(
    fleet: Fleet,
) -> None:
    repo_c = fleet.machine("c")
    fleet.at("c")
    old_home = _new()
    _age(old_home)
    fleet.at_a()
    assert fleet.run("sync", "--copy", NAME, "--machine", "c")[0] == 0
    replica = fleet.repo_a / ".work" / "clones" / NAME
    assert _note(replica)["home"] == "c"
    fleet.peer("c", None, online=False)
    code, document = fleet.run("handoff", NAME)
    assert code == 1
    [(result, _subject, detail)] = _results(document)
    assert result == "skip"
    assert "--force-offline-home" in detail
    assert work.is_replica(_note(replica))
    code, document = fleet.run("handoff", NAME, "--force-offline-home")
    assert code == 0, document
    assert (_note(replica)["replica"], _note(replica)["generation"]) == ("false", "1")
    fleet.peer("c", None)
    code, document = fleet.run("sync", "--copy", NAME, "--machine", "c")
    assert code == 1
    assert any(
        result == "conflict" and "a holds the newer handoff" in detail
        for result, _s, detail in _results(document)
    )
    assert _note(old_home)["home"] == "c"
    assert not work.is_replica(_note(old_home))
    assert repo_c.is_dir()


def test_a_copy_removed_at_home_leaves_every_unchanged_replica_and_keeps_an_edited_one(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    identity = work.copy_identity(_note(copy))
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert work.main(["rm", NAME]) == 0
    assert [(t.name, t.home, t.identity) for t in work.tombstones(fleet.repo_a)] == [
        (NAME, "a", identity),
    ]
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert ("synced", NAME, "tombstone a -> b") in _results(document)
    assert work.tombstones(fleet.repo_b) == work.tombstones(fleet.repo_a)
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()
    assert NAME not in work.discover(fleet.repo_b)
    kept = list((fleet.repo_b / ".work" / "trash").iterdir())
    assert [entry.name.rsplit("-", 1)[-1] for entry in kept] == [work.KEPT_TRASH]
    assert work.copy_identity(_note(kept[0])) == identity
    fleet.at_b()
    assert work.main(["gc"]) == 0
    assert kept[0].is_dir()
    fleet.at_a()
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(replica / "edit.txt", "replica edit\n")
    assert work.main(["rm", NAME]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert (replica / "edit.txt").exists()


def test_a_replica_commit_that_leaves_its_content_as_synced_is_never_refreshed_or_removed(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "work.txt", "uncommitted work\n")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _git_out(replica, "add", "work.txt")
    _ = _git_out(replica, "commit", "-q", "-m", "replica commit")
    commit = _git_out(replica, "rev-parse", "HEAD").strip()
    assert work.content_tree(replica) == _note(replica)["syncedtree"]
    _ = _write(copy / "later.txt", "home edit\n")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert _git_out(replica, "rev-parse", "HEAD").strip() == commit
    assert not (replica / "later.txt").exists()
    assert work.main(["rm", NAME, "--discard"]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any(
        result == "conflict" and "has commits or edits" in detail
        for result, _s, detail in _results(document)
    )
    assert _git_out(replica, "rev-parse", "HEAD").strip() == commit


def _cut_short(patch: pytest.MonkeyPatch, only: Sequence[str]) -> None:
    """Make each copy transfer write just ``only`` (no deletion) and then fail."""
    real = fleet_sync.rsync

    def cut(
        source: fleet_sync.Endpoint,
        source_path: str,
        target: fleet_sync.Endpoint,
        target_path: str,
        *,
        excludes: Sequence[str] = (),
        files: Sequence[str] | None = None,
    ) -> None:
        real(source, source_path, target, target_path, excludes=excludes, files=files or only)
        if files is None:
            msg = "cut short"
            raise fleet_sync.FleetError(msg)

    patch.setattr(fleet_sync, "rsync", cut)


@pytest.mark.parametrize("after", ["nothing", "edit", "commit"])
def test_a_sync_cut_short_is_completed_next_run_unless_the_replica_was_worked_in_after_it(
    fleet: Fleet,
    after: str,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(copy / "first.txt", "home edit\n")
    _ = _write(copy / "second.txt", "home edit\n")
    _age(copy)
    with pytest.MonkeyPatch.context() as patch:
        _cut_short(patch, ["first.txt"])
        code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert ("failed", NAME, "cut short") in _results(document)
    assert (replica / "first.txt").exists()
    assert not (replica / "second.txt").exists()
    assert _note(replica)["syncing"] == "true"
    if after == "edit":
        _ = _write(replica / "first.txt", "replica edit\n")
    elif after == "commit":
        _ = _git_out(replica, "commit", "-q", "--allow-empty", "-m", "replica commit")
    code, document = fleet.run("sync", "--copy", NAME)
    if after == "nothing":
        assert code == 0, document
        assert (replica / "second.txt").exists()
        assert not any(key.startswith("syncing") for key in _note(replica))
        return
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert not (replica / "second.txt").exists()


@pytest.mark.parametrize("kind", ["branch", "stash", "stash-old-note"])
def test_a_replica_side_branch_or_stash_is_never_deleted_by_a_refresh(
    fleet: Fleet,
    kind: str,
) -> None:
    copy = _new()
    _ = _write(copy / "work.txt", "uncommitted work\n")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    head = _git_out(replica, "rev-parse", "HEAD").strip()
    if kind == "branch":
        _ = _git_out(replica, "switch", "-q", "-c", "scratch")
        _ = _commit(replica, "side.txt", "side work\n")
        _ = _git_out(replica, "switch", "-q", "--detach", head)
        ref = "refs/heads/scratch"
    else:
        if kind == "stash-old-note":
            _ = _git_out(
                replica,
                "config",
                "--local",
                "--unset",
                f"{work.NOTE_SECTION}.syncedrefs",
            )
        _ = _write(replica / "gone.txt", "stashed edit\n")
        _ = _git_out(replica, "stash", "-q")
        ref = "refs/stash"
    assert work.content_tree(replica) == _note(replica)["syncedtree"]
    assert _git_out(replica, "rev-parse", "HEAD").strip() == head
    _ = _write(copy / "later.txt", "home edit\n")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert _git_out(replica, "rev-parse", "--verify", "-q", ref).strip()
    assert not (replica / "later.txt").exists()


@pytest.mark.parametrize("race", ["edit", "commit"])
def test_work_done_in_a_replica_during_its_transfer_is_never_marked_synced(
    fleet: Fleet,
    race: str,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    synced = _note(replica)["syncedtree"]
    _ = _write(copy / "later.txt", "home edit\n")
    _age(copy)
    real = fleet_sync.rsync

    def racing(
        source: fleet_sync.Endpoint,
        source_path: str,
        target: fleet_sync.Endpoint,
        target_path: str,
        *,
        excludes: Sequence[str] = (),
        files: Sequence[str] | None = None,
    ) -> None:
        real(source, source_path, target, target_path, excludes=excludes, files=files)
        if race == "edit":
            later = time.time() + 60
            os.utime(_write(replica / "race.txt", "replica edit\n"), (later, later))
        else:
            _ = _git_out(replica, "commit", "-q", "--allow-empty", "-m", "replica commit")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(fleet_sync, "rsync", racing)
        code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "not marked synced" in detail
    note = _note(replica)
    assert note["syncing"] == "true"
    assert note["syncedtree"] == synced
    head = _git_out(replica, "rev-parse", "HEAD").strip()
    _ = _write(copy / "later.txt", "second home edit\n")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert _git_out(replica, "rev-parse", "HEAD").strip() == head
    assert (replica / "later.txt").read_text(encoding="utf-8") == "home edit\n"
    assert (replica / "race.txt").exists() is (race == "edit")


@pytest.mark.parametrize("then", ["sync", "handoff"])
def test_a_home_save_a_cut_short_sync_copied_is_no_replica_edit(fleet: Fleet, then: str) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(copy / "first.txt", "home edit\n")
    _ = _write(copy / "second.txt", "home edit\n")
    _age(copy)
    real = fleet_sync.rsync

    def saved_then_cut(
        source: fleet_sync.Endpoint,
        source_path: str,
        target: fleet_sync.Endpoint,
        target_path: str,
        *,
        excludes: Sequence[str] = (),
        files: Sequence[str] | None = None,
    ) -> None:
        if files is None:
            later = time.time() + 60
            os.utime(_write(copy / "first.txt", "saved at home meanwhile\n"), (later, later))
        real(
            source,
            source_path,
            target,
            target_path,
            excludes=excludes,
            files=files or ["first.txt"],
        )
        if files is None:
            msg = "cut short"
            raise fleet_sync.FleetError(msg)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(fleet_sync, "rsync", saved_then_cut)
        code, _document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert (replica / "first.txt").read_text(encoding="utf-8") == "saved at home meanwhile\n"
    code, document = fleet.run("status", "--copy", NAME)
    [entry] = [json_object(item) for item in json_list(document, "copies")]
    assert json_object(entry, "replicas") == {"b": "syncing"}
    args = (
        ["sync", "--copy", NAME]
        if then == "sync"
        else [
            "handoff",
            NAME,
            "--to",
            "b",
        ]
    )
    code, document = fleet.run(*args)
    assert code == 0, document
    assert (replica / "second.txt").exists()
    assert not any(key.startswith("syncing") for key in _note(replica))
    if then == "handoff":
        assert _note(replica)["replica"] == "false"


def test_a_home_that_saves_a_file_again_after_a_transfer_copied_its_save_completes_next_run(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(copy / "first.txt", "home edit\n")
    _age(copy)
    real = fleet_sync.rsync

    def saved_meanwhile(
        source: fleet_sync.Endpoint,
        source_path: str,
        target: fleet_sync.Endpoint,
        target_path: str,
        *,
        excludes: Sequence[str] = (),
        files: Sequence[str] | None = None,
    ) -> None:
        _ = _write(copy / "first.txt", "saved at home meanwhile\n")
        real(source, source_path, target, target_path, excludes=excludes, files=files)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(fleet_sync, "rsync", saved_meanwhile)
        code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any("not marked synced" in detail for _r, _s, detail in _results(document))
    _ = _write(copy / "first.txt", "saved at home again\n")
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert (replica / "first.txt").read_text(encoding="utf-8") == "saved at home again\n"
    assert not any(key.startswith("syncing") for key in _note(replica))


def test_a_mode_change_in_a_replica_a_sync_was_cut_short_in_is_kept(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "work.txt", "uncommitted work\n")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(copy / "first.txt", "home edit\n")
    _ = _write(copy / "second.txt", "home edit\n")
    _age(copy)
    with pytest.MonkeyPatch.context() as patch:
        _cut_short(patch, ["first.txt"])
        assert fleet.run("sync", "--copy", NAME)[0] == 1
    (replica / "work.txt").chmod(0o755)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert (replica / "work.txt").stat().st_mode & 0o111
    assert not (replica / "second.txt").exists()


def test_digests_refuses_a_path_through_a_symlinked_folder(fleet: Fleet) -> None:
    copy = _new()
    outside = _write(fleet.tmp / "outside" / "secret.txt", "not the copy's\n").parent
    (copy / "linked").symlink_to(outside)
    asked = json.dumps({"paths": ["linked/secret.txt"]}).encode("utf-8")
    with pytest.raises(fleet_sync.FleetError, match="no real folder"):
        _ = fleet_sync.agent_digests(fleet.repo_a, NAME, asked)


def test_a_deletion_in_a_replica_a_sync_was_cut_short_in_is_kept(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "work.txt", "uncommitted work\n")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    _ = _write(copy / "first.txt", "home edit\n")
    _ = _write(copy / "second.txt", "home edit\n")
    _age(copy)
    with pytest.MonkeyPatch.context() as patch:
        _cut_short(patch, ["first.txt"])
        assert fleet.run("sync", "--copy", NAME)[0] == 1
    (replica / "work.txt").unlink()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    [(result, _subject, detail)] = [row for row in _results(document) if row[1] == NAME]
    assert result == "conflict"
    assert "has commits or edits since its last sync" in detail
    assert not (replica / "work.txt").exists()
    assert not (replica / "second.txt").exists()


def test_a_home_that_lost_the_copy_without_a_tombstone_removes_no_replica(fleet: Fleet) -> None:
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    work.delete_tree(fleet.repo_a / ".work")
    replica = fleet.repo_b / ".work" / "clones" / NAME
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1, document
    assert any(
        result == "conflict"
        and subject == NAME
        and "no tombstone either side holds removes this copy" in detail
        for result, subject, detail in _results(document)
    )
    assert replica.is_dir()
    assert work.is_replica(_note(replica))


def test_an_older_copys_tombstone_never_removes_a_later_copy_reusing_the_name(
    fleet: Fleet,
) -> None:
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert work.main(["rm", NAME]) == 0
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert len(work.tombstones(fleet.repo_b)) == 1
    work.delete_tree(fleet.repo_a / ".work")
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1, document
    assert any(
        "no tombstone either side holds removes this copy" in detail
        for _r, _s, detail in _results(document)
    )
    assert replica.is_dir()
    assert len(work.tombstones(fleet.repo_a)) == 1


def test_a_replica_removed_off_its_home_leaves_no_tombstone(fleet: Fleet) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    fleet.at_b()
    assert work.main(["rm", NAME, "--discard"]) == 0
    fleet.at_a()
    assert work.tombstones(fleet.repo_b) == []
    (kept,) = (fleet.repo_b / ".work" / "trash").iterdir()
    assert kept.name.endswith(f"-{work.KEPT_TRASH}")
    assert work.copy_identity(_note(kept)) == work.copy_identity(_note(copy))
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert copy.is_dir()
    assert (fleet.repo_b / ".work" / "clones" / NAME).is_dir()


@pytest.mark.parametrize("old_copy", ["tombstoned", "lost"])
def test_a_new_copy_reusing_a_replicas_name_never_overwrites_that_replica(
    fleet: Fleet,
    old_copy: str,
) -> None:
    old = _new()
    _ = _write(old / "old.txt", "earlier work\n")
    _age(old)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    replica = fleet.repo_b / ".work" / "clones" / NAME
    trash = fleet.repo_b / ".work" / "trash"
    if old_copy == "tombstoned":
        assert work.main(["rm", NAME, "--discard"]) == 0
    else:
        work.delete_tree(fleet.repo_a / ".work")
    new = _new()
    _age(new)
    code, document = fleet.run("sync", "--copy", NAME)
    if old_copy == "lost":
        assert code == 1, document
        assert any(
            result == "conflict" and "a replica of an earlier one" in detail
            for result, _s, detail in _results(document)
        )
        assert (replica / "old.txt").read_text(encoding="utf-8") == "earlier work\n"
        assert not trash.exists() or not list(trash.iterdir())
        with pytest.raises(fleet_sync.FleetError, match="replica of an earlier copy"):
            _ = fleet_sync.agent_prepare(
                fleet.repo_b,
                NAME,
                "clone",
                "a",
                work._head(new),
                work.content_tree(new),
                _note(new),
            )
        return
    assert code == 0, document
    assert not replica.exists()
    (kept,) = trash.iterdir()
    assert kept.name.endswith(f"-{work.KEPT_TRASH}")
    assert (kept / "old.txt").read_text(encoding="utf-8") == "earlier work\n"
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert ("synced", NAME, "synced a -> b") in _results(document)
    assert not (replica / "old.txt").exists()
    assert work.copy_identity(_note(replica)) == work.copy_identity(_note(new))


def test_gc_on_a_former_home_never_removes_the_landed_copy_it_now_holds_as_a_replica(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "landed.txt", "landed work\n")
    assert work.main(["land", NAME]) == 0
    _ = _git_out(fleet.repo_a, "add", "landed.txt")
    _ = _git_out(fleet.repo_a, "commit", "-q", "-m", "the maintainer commits the landing")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    code, document = fleet.run("handoff", NAME, "--to", "b")
    assert code == 0, document
    _ = fleet.capsys.readouterr()
    assert work.main(["gc"]) == 0
    assert f"keep {NAME}: a replica of b" in fleet.capsys.readouterr().out
    assert copy.is_dir()
    assert work.tombstones(fleet.repo_a) == []


def test_a_worktree_replica_gets_its_commit_without_a_ref_and_its_own_git_file(
    fleet: Fleet,
) -> None:
    head = _commit(fleet.repo_a, "main-only.txt", "only on a's main\n")
    copy = _new(NAME, "--worktree")
    _ = _write(copy / "work.txt", "worktree work\n")
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    replica = fleet.repo_b / ".work" / "worktrees" / NAME
    assert (replica / "work.txt").read_text(encoding="utf-8") == "worktree work\n"
    assert (replica / "main-only.txt").exists()
    assert _git_out(replica, "rev-parse", "HEAD").strip() == head
    assert str(fleet.repo_b) in (replica / ".git").read_text(encoding="utf-8")
    assert head not in _git_out(fleet.repo_b, "for-each-ref", "--format=%(objectname)")
    assert _note(replica, "--worktree")["replica"] == "true"
    entries = work.worktree_entries(fleet.repo_b)
    assert [entry.locked for entry in entries] == [f"{work.LOCK_REASON_PREFIX}{NAME}"]


# --------------------------------------------------------------------------------------------
# Pins, evidence
# --------------------------------------------------------------------------------------------


def test_pins_travel_both_ways_create_only_and_a_differing_pin_is_a_conflict(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    saved = work.pins(fleet.repo_a)[NAME]["save-1"]
    assert work.pins(fleet.repo_b)[NAME]["save-1"] == saved
    fleet.at_b()
    head = _git_out(fleet.repo_b, "rev-parse", "HEAD").strip()
    assert work.publish_pin(fleet.repo_b, fleet.repo_b, head, NAME, "save-2")
    fleet.at_a()
    assert work.publish_pin(fleet.repo_a, copy, saved, NAME, "save-2")
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any(
        result == "conflict" and subject == f"{NAME}/save-2"
        for result, subject, _d in _results(document)
    )
    assert work.pins(fleet.repo_a)[NAME]["save-2"] == saved
    assert work.pins(fleet.repo_b)[NAME]["save-2"] == head


def test_fetch_pins_restores_saved_work_without_syncing_the_replica_or_other_data(
    fleet: Fleet,
) -> None:
    fleet.at_b()
    source = _new()
    _ = _write(source / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _ = _new("spike-fleet-other")
    _ = _write(fleet.repo_b / ".work" / "evidence" / NAME / "proof.txt", "evidence\n")
    _ = _commit(fleet.repo_b, "later.txt", "main moved on\n")
    source_pins = work.pins(fleet.repo_b)
    fleet.at_a()
    _ = _new("spike-fleet-local")
    local_head = _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()
    assert work.publish_pin(fleet.repo_a, fleet.repo_a, local_head, NAME, "save-9")
    refs = _git_out(fleet.repo_a, "show-ref")
    code, document = fleet.run("fetch-pins", NAME, "--machine", "B.tail0.ts.net.")
    assert code == 0, document
    assert work.pins(fleet.repo_a)[NAME] == {**source_pins[NAME], "save-9": local_head}
    assert "spike-fleet-other" not in work.pins(fleet.repo_a)
    assert work.pins(fleet.repo_b) == source_pins
    assert _git_out(fleet.repo_a, "show-ref") == refs
    assert not (fleet.repo_a / ".git" / "FETCH_HEAD").exists()
    assert not (fleet.repo_a / ".work" / "clones" / NAME).exists()
    assert not (fleet.repo_a / ".work" / "evidence" / NAME).exists()
    restored = _new("verify-fetched-save", "--from", f"refs/work/{NAME}/save-1")
    assert (restored / "saved.txt").read_text() == "saved work\n"
    assert "saved.txt" in _git_out(restored, "ls-files").splitlines()
    code, document = fleet.run("fetch-pins", NAME, "--machine", "b")
    assert code == 0, document
    assert _results(document) == [("unchanged", NAME, "all source pins already held")]


def test_fetch_pins_keeps_both_commits_when_a_ref_differs(fleet: Fleet) -> None:
    fleet.at_b()
    source = _new()
    _ = _write(source / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    source_pins = work.pins(fleet.repo_b)
    fleet.at_a()
    head = _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()
    assert work.publish_pin(fleet.repo_a, fleet.repo_a, head, NAME, "save-1")
    code, document = fleet.run("fetch-pins", NAME, "--machine", "b")
    assert code == 1
    assert any(
        result == "conflict" and subject == f"{NAME}/save-1"
        for result, subject, _detail in _results(document)
    )
    assert work.pins(fleet.repo_a)[NAME]["save-1"] == head
    assert work.pins(fleet.repo_b) == source_pins


def test_fetch_pins_dry_run_writes_no_pins_or_replica(fleet: Fleet) -> None:
    fleet.at_b()
    source = _new()
    _ = _write(source / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    before = work.pins(fleet.repo_b)
    fleet.at_a()
    code, document = fleet.run("fetch-pins", NAME, "--machine", "b", "--dry-run")
    assert code == 0, document
    assert {result for result, _subject, _detail in _results(document)} == {"would"}
    assert work.pins(fleet.repo_a) == {}
    assert work.pins(fleet.repo_b) == before
    assert not (fleet.repo_a / ".work").exists()


def test_fetch_pins_never_revives_a_pin_a_local_tombstone_dropped(fleet: Fleet) -> None:
    fleet.at_b()
    source = _new()
    _ = _write(source / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    saved = work.pins(fleet.repo_b)[NAME]["save-1"]
    fleet.at_a()
    assert work.publish_pin(fleet.repo_a, source, saved, NAME, "save-1")
    assert work.main(["rm", NAME, "--drop-saves"]) == 0
    code, document = fleet.run("fetch-pins", NAME, "--machine", "b")
    assert code == 0, document
    assert "save-1" not in work.pins(fleet.repo_a)[NAME]
    assert work.pins(fleet.repo_b)[NAME]["save-1"] == saved


@pytest.mark.parametrize(
    ("name", "machine", "expected"),
    [(NAME, "not-a-peer", 2), ("spike-missing", "b", 1), ("bad name", "b", 2)],
)
def test_fetch_pins_refuses_an_unknown_source_copy_or_invalid_name(
    fleet: Fleet,
    name: str,
    machine: str,
    expected: int,
) -> None:
    code, _document = fleet.run("fetch-pins", name, "--machine", machine)
    assert code == expected
    assert work.pins(fleet.repo_a) == {}


@pytest.mark.parametrize(
    ("where", "lock"),
    [
        ("local", "fleet"),
        ("peer", "fleet"),
        ("local", "land"),
        ("peer", "land"),
    ],
)
def test_fetch_pins_respects_existing_fleet_and_land_locks(
    fleet: Fleet,
    where: str,
    lock: str,
) -> None:
    fleet.at_b()
    _ = _new()
    fleet.at_a()
    repo = fleet.repo_a if where == "local" else fleet.repo_b
    hold = fleet_sync.holding(repo) if lock == "fleet" else work.land_lock(repo)
    with hold:
        code, document = fleet.run("fetch-pins", NAME, "--machine", "b")
    assert code == 1
    expected = "another fleet_sync run" if lock == "fleet" else "land is in progress"
    assert any(expected in detail for _result, _subject, detail in _results(document))
    assert work.pins(fleet.repo_a) == {}


def test_rm_drop_saves_drops_the_replicas_pins_and_a_new_copy_gets_none(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert "save-1" in work.pins(fleet.repo_b)[NAME]
    assert work.main(["rm", NAME, "--drop-saves"]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert NAME not in work.pins(fleet.repo_a)
    assert NAME not in work.pins(fleet.repo_b)
    _age(_new())
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert set(work.pins(fleet.repo_a)[NAME]) == set(work.pins(fleet.repo_b)[NAME]) == {"start"}


def test_saves_a_plain_rm_kept_are_freed_by_rm_drop_saves_on_any_machine(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert work.main(["rm", NAME]) == 0
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert set(work.pins(fleet.repo_b)[NAME]) == {"save-1"}
    fleet.at_b()
    _ = capsys.readouterr()
    assert (
        work.main(
            [
                "new",
                NAME,
                "--no-setup",
                "--purpose",
                "again",
            ],
        )
        == 1
    )
    assert f"`work.py rm {NAME} --drop-saves`" in capsys.readouterr().err
    assert work.main(["rm", NAME, "--drop-saves"]) == 0
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert NAME not in work.pins(fleet.repo_a)
    assert NAME not in work.pins(fleet.repo_b)
    _ = _new()


def test_a_new_copy_saved_before_its_first_sync_syncs_cleanly(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert not [row for row in _results(document) if row[0] in fleet_sync.TROUBLE]
    assert work.pins(fleet.repo_b)[NAME] == work.pins(fleet.repo_a)[NAME]


def test_a_name_holding_an_earlier_copys_saves_gets_no_replica_and_keeps_them(
    fleet: Fleet,
) -> None:
    old = _new()
    _ = _write(old / "saved.txt", "the first copy's work\n")
    assert work.main(["save", NAME]) == 0
    first = work.pins(fleet.repo_a)[NAME]["save-1"]
    _age(old)
    assert work.main(["rm", NAME]) == 0
    fleet.at_b()
    later = _new()
    _ = _write(later / "saved.txt", "the second copy's work\n")
    assert work.main(["save", NAME]) == 0
    _age(later)
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    (detail,) = [
        d for result, subject, d in _results(document) if (result, subject) == ("conflict", NAME)
    ]
    assert "leftover pins from an earlier copy" in detail
    assert f"`work.py rm {NAME} --drop-saves` there to drop them, or rename" in detail
    assert work.discover(fleet.repo_a)[NAME].form == "pins"
    fleet.at_b()
    assert work.main(["rm", NAME, "--drop-saves"]) == 0
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert work.pins(fleet.repo_a)[NAME] == work.pins(fleet.repo_b)[NAME] == {"save-1": first}


@pytest.mark.parametrize("replica", ["clean", "edited"])
def test_a_save_of_unchanged_content_stays_the_copys_own_after_a_handoff(
    fleet: Fleet,
    replica: str,
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert work.main(["save", NAME]) == 0
    held = fleet.repo_b / ".work" / "clones" / NAME
    if replica == "clean":
        code, document = fleet.run("sync", "--copy", NAME)
        assert ("synced", NAME, "synced a -> b") in _results(document), document
        assert "save-2" in work.recorded_pins(_note(held))
    else:
        _ = _write(held / "mistake.txt", "edited on the replica\n")
        _age(held)
    code, document = fleet.run("handoff", NAME, "--to", "b")
    assert code == 0, document
    assert set(work.recorded_pins(_note(held))) == {work.START_PIN, "save-1", "save-2"}
    _age(copy)
    assert work.main(["rm", "--discard", NAME]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert _note(copy)["home"] == "b"


def test_handoff_carries_a_home_save_no_sync_carried_to_the_promoted_machine(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    _ = _write(copy / "more.txt", "more work\n")
    assert work.main(["save", NAME]) == 0
    second = work.pins(fleet.repo_a)[NAME]["save-2"]
    assert "save-2" not in work.pins(fleet.repo_b)[NAME]
    _age(copy)
    code, document = fleet.run("handoff", NAME, "--to", "b")
    assert code == 0, document
    assert ("synced", f"{NAME}/save-2", "pin a -> b") in _results(document)
    held = fleet.repo_b / ".work" / "clones" / NAME
    assert _note(held)["home"] == "b"
    assert work.recorded_pins(_note(held))["save-2"] == second
    assert work.pins(fleet.repo_b)[NAME]["save-2"] == second


def test_a_copy_older_than_its_pin_record_still_owns_its_saves(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _ = _git_out(copy, "config", "--local", "--unset", f"{work.NOTE_SECTION}.{work.PINS_NOTE}")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    fleet.at_b()
    assert work.main(["rm", "--discard", NAME]) == 0
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert "save-1" in work.recorded_pins(_note(fleet.repo_b / ".work" / "clones" / NAME))


def test_pins_gc_drops_are_buried_on_every_machine_and_the_name_is_free_again(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "landed.txt", "landed work\n")
    assert work.main(["land", NAME]) == 0
    _ = _git_out(fleet.repo_a, "add", "landed.txt")
    _ = _git_out(fleet.repo_a, "commit", "-q", "-m", "the maintainer commits the landing")
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert {"landed", "landed-copy"} <= set(work.pins(fleet.repo_b)[NAME])
    assert work.main(["gc"]) == 0
    assert NAME not in work.pins(fleet.repo_a)
    for _run in range(2):
        code, document = fleet.run("sync", "--copy", NAME)
        assert code == 0, document
    assert NAME not in work.pins(fleet.repo_a)
    assert NAME not in work.pins(fleet.repo_b)
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()
    _ = _new()


def test_pins_a_link_created_stay_reported_when_the_bundle_after_it_fails(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copy = _new()
    _age(copy)
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    start = work.pins(fleet.repo_a)[NAME]["start"]
    assert work.publish_pin(fleet.repo_a, copy, start, NAME, "save-1")
    _ = _write(copy / "saved.txt", "saved work\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    real = fleet_sync.Endpoint.bytes_of

    def no_bundle(endpoint: fleet_sync.Endpoint, *args: str) -> bytes:
        if args[0] == "pins-export":
            msg = "the bundle broke"
            raise fleet_sync.FleetError(msg)
        return real(endpoint, *args)

    monkeypatch.setattr(fleet_sync.Endpoint, "bytes_of", no_bundle)
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    rows = _results(document)
    assert ("synced", f"{NAME}/save-1", "pin a -> b") in rows
    assert ("failed", "pins", "the bundle broke") in rows
    assert work.pins(fleet.repo_b)[NAME]["save-1"] == start
    assert "save-2" not in work.pins(fleet.repo_b)[NAME]


def test_a_pin_or_worktree_head_the_peer_reaches_from_a_later_main_still_exports(
    fleet: Fleet,
) -> None:
    worktree = _new("spike-fleet-tree", "--worktree")
    copy = _new()
    start = work.pins(fleet.repo_a)[NAME]["start"]
    later = _commit(fleet.repo_a, "later.txt", "main moved on\n")
    assert work.publish_pin(fleet.repo_a, fleet.repo_a, later, "spike-fleet-later", "start")
    bundle = fleet_sync.agent_pins_export(fleet.repo_a, [f"{NAME}/start"], [later])
    assert fleet_sync.agent_pins_import(fleet.repo_b, bundle)["created"] == [f"{NAME}/start"]
    assert work.pins(fleet.repo_b)[NAME]["start"] == start
    head = fleet_sync.agent_head_export(fleet.repo_a, "spike-fleet-tree", [later])
    assert fleet_sync.agent_commit_import(fleet.repo_b, head)["commit"] == work._head(worktree)
    assert work._head(copy) == start


def test_evidence_is_a_union_the_changed_side_wins_and_both_changed_is_reported(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    evidence_a = fleet.repo_a / ".work" / "evidence" / NAME
    evidence_b = fleet.repo_b / ".work" / "evidence" / NAME
    _ = _write(evidence_a / "a.txt", "from a\n")
    _ = _write(evidence_a / "shared.txt", "v1\n")
    _ = _write(evidence_a / "both.txt", "v1\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert (evidence_b / "a.txt").read_text(encoding="utf-8") == "from a\n"
    _ = _write(evidence_b / "b.txt", "from b\n")
    _ = _write(evidence_b / "shared.txt", "v2 on b\n")
    os.utime(evidence_b / "shared.txt", (time.time() + 5, time.time() + 5))
    _ = _write(evidence_a / "both.txt", "v2 on a\n")
    _ = _write(evidence_b / "both.txt", "v2 on b, longer\n")
    (evidence_a / "a.txt").unlink()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert (evidence_a / "b.txt").read_text(encoding="utf-8") == "from b\n"
    assert (evidence_a / "shared.txt").read_text(encoding="utf-8") == "v2 on b\n"
    assert (evidence_a / "a.txt").read_text(encoding="utf-8") == "from a\n"
    assert (evidence_b / "a.txt").exists()
    assert (evidence_a / "both.txt").read_text(encoding="utf-8") == "v2 on a\n"
    assert (evidence_b / "both.txt").read_text(encoding="utf-8") == "v2 on b, longer\n"
    assert ("conflict", f"{NAME}/both.txt") in [(r, s) for r, s, _d in _results(document)]


def test_evidence_and_replicas_carry_symlinks_as_links_dangling_ones_included(
    fleet: Fleet,
) -> None:
    """A link travels as a link both ways with its mtime, never followed; a resync is clean."""
    outside = _write(fleet.tmp / "outside" / "secret.txt", "outside .work\n").parent
    copy = _new()
    (copy / "dangling-in-copy").symlink_to(copy / "missing.txt")
    _age(copy)
    evidence_a, evidence_b = _evidence(fleet.repo_a), _evidence(fleet.repo_b)
    proofs = evidence_a / "pytest-final" / "popen-gw0"
    _ = _write(proofs / "base.sqlite3", "base\n")
    (proofs / "out.sqlite3").symlink_to(proofs / "missing.sqlite3")
    (proofs / "ours.sqlite3").symlink_to("./base.sqlite3")
    (evidence_a / "folder-link").symlink_to(outside, target_is_directory=True)
    code, document = fleet.run("sync")
    assert code == 0, document
    assert ("synced", NAME, "evidence: 4 out, 0 in") in _results(document), document
    assert str((evidence_b / "folder-link").readlink()) == str(outside)
    assert "folder-link/secret.txt" not in work.evidence_files(evidence_b)
    landed = evidence_b / "pytest-final" / "popen-gw0"
    assert str((landed / "out.sqlite3").readlink()) == str(proofs / "missing.sqlite3")
    assert work.link_text(landed / "ours.sqlite3") == "./base.sqlite3"
    assert work.evidence_files(evidence_b) == work.evidence_files(evidence_a)
    replica = fleet.repo_b / ".work" / "clones" / NAME
    assert str((replica / "dangling-in-copy").readlink()) == str(copy / "missing.txt")
    (evidence_b / "from-b").symlink_to("nowhere")
    code, document = fleet.run("sync")
    assert code == 0, document
    assert ("synced", NAME, "evidence: 0 out, 1 in") in _results(document), document
    assert str((evidence_a / "from-b").readlink()) == "nowhere"
    code, document = fleet.run("sync")
    assert code == 0, document
    assert [row for row in _results(document) if row[1] == NAME and row[0] == "synced"] == []


def test_an_evidence_file_rsync_cannot_send_is_one_failed_row_and_the_rest_still_syncs(
    fleet: Fleet,
) -> None:
    """The file is named, every other file and stem arrives, and the next run carries it."""
    if os.geteuid() == 0:
        pytest.skip("root reads a file whatever its mode")
    copy = _new()
    _age(copy)
    evidence_a, evidence_b = _evidence(fleet.repo_a), _evidence(fleet.repo_b)
    locked = _write(evidence_a / "locked.txt", "unreadable\n")
    _ = _write(evidence_a / "fine.txt", "readable\n")
    _ = _write(_evidence(fleet.repo_a, "spike-later-stem") / "later.txt", "later\n")
    locked.chmod(0)
    try:
        code, document = fleet.run("sync")
    finally:
        locked.chmod(0o644)
    assert code == 1, document
    rows = [(result, subject) for result, subject, _detail in _results(document)]
    assert ("failed", f"{NAME}/locked.txt") in rows, document
    assert ("failed", "sync") not in rows, document
    assert ("synced", NAME, "evidence: 1 out, 0 in") in _results(document), document
    assert (evidence_b / "fine.txt").read_text(encoding="utf-8") == "readable\n"
    assert not (evidence_b / "locked.txt").exists()
    later = _evidence(fleet.repo_b, "spike-later-stem") / "later.txt"
    assert later.read_text(encoding="utf-8") == "later\n"
    code, document = fleet.run("sync")
    assert code == 0, document
    assert [row for row in _results(document) if row[1] == NAME and row[0] != "fresh"] == [
        ("synced", NAME, "evidence: 1 out, 0 in"),
    ], document
    assert (evidence_b / "locked.txt").read_text(encoding="utf-8") == "unreadable\n"


def test_a_peer_without_the_links_feature_gets_its_evidence_links_by_rsync(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copy = _new()
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "base.txt", "base\n")
    (_evidence(fleet.repo_a) / "alias.txt").symlink_to("base.txt")
    _without_feature(monkeypatch, "b", fleet_sync.LINKS_FEATURE)
    seen = _record_calls(monkeypatch)
    code, document = fleet.run("sync")
    assert code == 0, document
    assert [call.args[0] for call in seen if call.args[0] == "evidence-links"] == []
    assert str((_evidence(fleet.repo_b) / "alias.txt").readlink()) == "base.txt"


def test_an_agent_writes_no_evidence_link_through_a_symlinked_folder(fleet: Fleet) -> None:
    outside = (fleet.tmp / "outside").resolve()
    outside.mkdir()
    evidence = _evidence(fleet.repo_b)
    evidence.mkdir(parents=True)
    (evidence / "sub").symlink_to(outside, target_is_directory=True)
    (evidence / "taken").mkdir()
    links = {
        "sub/x": ["t", 0],
        "taken": ["t", 0],
        "odd": ["t"],
        "ok/y": ["t", 5],
    }
    answer = fleet_sync.agent_evidence_links(fleet.repo_b, NAME, json.dumps(links).encode())
    assert answer["written"] == ["ok/y"]
    assert sorted(str(rel) for rel in json_object(answer["failed"])) == ["odd", "sub/x", "taken"]
    assert list(outside.iterdir()) == []
    assert work.evidence_files(evidence)["ok/y"] == (1, 5)


# --------------------------------------------------------------------------------------------
# Evidence tombstones: an explicit deletion reaches every machine, a hand deletion none
# --------------------------------------------------------------------------------------------


def _evidence(repo: Path, stem: str = NAME) -> Path:
    return repo / ".work" / "evidence" / stem


def _evidence_trash(repo: Path, stem: str = NAME) -> list[Path]:
    trash = repo / ".work" / "trash"
    entries = trash.iterdir() if trash.is_dir() else iter(())
    return sorted(entry for entry in entries if entry.name.startswith(f"evidence-{stem}-"))


def _grave(
    stem: str,
    files: dict[str, Path],
    *,
    whole: bool = True,
    removed_at: float | None = None,
    copy: str = "",
) -> work.EvidenceTombstone:
    """Return a record of ``files`` (rel to the file holding the state) as machine ``a`` writes it."""
    states = sorted((rel, *work.file_state(path.lstat())) for rel, path in files.items())
    at = time.time() if removed_at is None else removed_at
    return work.EvidenceTombstone(stem, "a", at, "a", tuple(states), whole=whole, copy=copy)


def _apply(repo: Path, *names: str) -> dict[str, object]:
    """Run ``evidence-apply`` on ``repo`` in this process, holding its lock as a run would."""
    with fleet_sync.holding(repo):
        return fleet_sync.agent_evidence_apply(repo, names)


def test_an_evidence_deletion_reaches_the_peer_by_full_sync_alone_and_goes_to_its_kept_trash(
    fleet: Fleet,
) -> None:
    """The timer carries the record, a dry run counts, a full sync moves; a later file stays."""
    copy = _new()
    _age(copy)
    evidence_a, evidence_b = _evidence(fleet.repo_a), _evidence(fleet.repo_b)
    _ = _write(evidence_a / "proofs" / "out.txt", "proof\n")
    _ = _write(evidence_a / "top.txt", "top\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert (evidence_b / "proofs" / "out.txt").read_text(encoding="utf-8") == "proof\n"
    _ = _write(evidence_b / "__pycache__" / "x.cpython-314.pyc", "cache")
    assert work.main(["rm", NAME, "--evidence"]) == 0
    (grave,) = work.evidence_tombstones(fleet.repo_a)
    code, document = fleet.run("sync", "--pins-only")
    assert code == 0, document
    assert ("synced", NAME, "evidence tombstone a -> b") in _results(document)
    assert work.evidence_tombstones(fleet.repo_b) == [grave]
    assert (evidence_b / "top.txt").is_file()
    assert _evidence_trash(fleet.repo_b) == []
    code, document = fleet.run("sync", "--copy", NAME, "--dry-run")
    assert ("would", NAME, "evidence: trash 2 on b") in _results(document), document
    assert (evidence_b / "top.txt").is_file()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    days = work.TRASH_RETENTION_SECONDS // 86400
    assert (
        "synced",
        NAME,
        f"evidence: 2 deleted on b (kept in .work/trash for {days} days)",
    ) in _results(document)
    assert (
        "note",
        NAME,
        (
            "evidence folder kept on b holding only files no sync carries (__pycache__); "
            f"`work.py evidence-rm {NAME}` there removes it"
        ),
    ) in _results(document)
    assert [path.name for path in evidence_b.iterdir()] == ["__pycache__"]
    (entry,) = _evidence_trash(fleet.repo_b)
    assert entry.name.endswith(f"-{work.KEPT_TRASH}")
    assert sorted(path.relative_to(entry).as_posix() for path in entry.rglob("*.txt")) == [
        "proofs/out.txt",
        "top.txt",
    ]
    assert not (entry / "__pycache__").exists()
    code, document = fleet.run("sync", "--copy", NAME)
    assert (code, [row for row in _results(document) if row[1] == NAME]) == (0, [])
    fleet.at_b()
    assert work.main(["evidence-rm", NAME]) == 0
    fleet.at_a()
    assert not evidence_b.exists()
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert NAME not in json_object(
        json_loads((fleet.repo_a / ".work" / "fleet" / "evidence-b.json").read_text()),
    )
    later = _write(evidence_a / "top.txt", "recreated, longer than before\n")
    past = grave.removed_at - 1000
    os.utime(later, (past, past))
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    recreated = (evidence_b / "top.txt").read_text(encoding="utf-8")
    assert recreated == "recreated, longer than before\n"
    assert later.is_file()
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert (evidence_b / "top.txt").is_file()
    assert later.is_file()


def test_a_stem_a_peer_name_still_uses_is_skipped_there_and_its_file_never_revives(
    fleet: Fleet,
) -> None:
    """A sibling holding pins alone on c keeps c's file with a note, never an exit 1 per run.

    a, holding the record, never pulls the file back.
    """
    repo_c = fleet.machine("c")
    copy = _new()
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert (_evidence(repo_c) / "f.txt").is_file()
    sibling = f"{NAME}-verify"
    fleet.at("c")
    verify = _new(sibling)
    _ = _write(verify / "saved.txt", "saved\n")
    assert work.main(["save", sibling]) == 0
    assert work.main(["rm", sibling]) == 0
    assert work.discover(repo_c)[sibling].form == "pins"
    fleet.at_a()
    assert work.main(["rm", NAME, "--evidence"]) == 0
    for _run in range(2):
        code, document = fleet.run("sync", "--copy", NAME)
        assert code == 0, document
        kept = ("note", NAME, f"evidence kept on c: {sibling} still use it here")
        assert kept in _results(document)
    assert not _evidence(fleet.repo_a).exists()
    assert not _evidence(fleet.repo_b).exists()
    assert (_evidence(repo_c) / "f.txt").is_file()
    assert len(work.evidence_tombstones(repo_c)) == 1
    fleet.at("c")
    assert work.main(["rm", sibling, "--drop-saves"]) == 0
    fleet.at_a()
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert not _evidence(repo_c).exists()
    assert not _evidence(fleet.repo_a).exists()
    (entry,) = _evidence_trash(repo_c)
    assert (entry / "f.txt").read_text(encoding="utf-8") == "proof\n"


def test_a_file_changed_on_the_peer_after_the_delete_is_kept_reported_and_returns_to_the_deleter(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "f.txt", "v1\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    changed = _write(_evidence(fleet.repo_b) / "f.txt", "v2\n")
    past = time.time() - 5000
    os.utime(changed, (past, past))
    assert work.main(["rm", NAME, "--evidence"]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1, document
    conflicts = [row for row in _results(document) if row[0] == "conflict"]
    assert conflicts == [
        (
            "conflict",
            f"{NAME}/f.txt",
            "evidence deleted on a, changed on b since: kept there and copied back to a",
        ),
    ]
    assert changed.read_text(encoding="utf-8") == "v2\n"
    assert (_evidence(fleet.repo_a) / "f.txt").read_text(encoding="utf-8") == "v2\n"
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert [row for row in _results(document) if row[1].startswith(NAME)] == []


@pytest.mark.parametrize(
    ("size", "mtime", "outcome"),
    [
        (0, 0, "trashed"),
        (1, 0, "kept"),
        (0, 1, "kept"),
        (0, -1, "kept"),
    ],
    ids=[
        "equal",
        "size",
        "mtime-later",
        "mtime-earlier",
    ],
)
def test_the_state_match_is_exact_on_size_and_second_mtime(
    fleet: Fleet,
    size: int,
    mtime: int,
    outcome: str,
) -> None:
    fleet.at_b()
    held = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    os.utime(held, (1_700_000_000.4, 1_700_000_000.4))
    grave = dataclasses.replace(
        _grave(NAME, {"f.txt": held}, whole=False),
        files=(("f.txt", 6 + size, 1_700_000_000 + mtime),),
    )
    assert work.write_evidence_tombstone(fleet.repo_b, grave)
    answer = _apply(fleet.repo_b)
    assert ("kept" if held.exists() else "trashed") == outcome
    assert answer["kept"] == ([] if outcome == "trashed" else [[NAME, "f.txt"]])


def test_a_hand_deleted_file_comes_back_with_a_note_and_a_wiped_evidence_folder_removes_nothing(
    fleet: Fleet,
) -> None:
    copy = _new()
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    _ = _write(_evidence(fleet.repo_a) / "g.txt", "proof\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    shutil.rmtree(_evidence(fleet.repo_a))
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert (
        "note",
        NAME,
        (
            f"2 evidence files removed by hand on a came back from b; `work.py evidence-rm {NAME} "
            "--adopt-missing` on a deletes them everywhere"
        ),
    ) in _results(document)
    assert (_evidence(fleet.repo_a) / "f.txt").is_file()
    assert work.evidence_tombstones(fleet.repo_a) == []
    shutil.rmtree(fleet.repo_a / ".work" / "evidence")
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert (_evidence(fleet.repo_b) / "f.txt").is_file()
    assert (_evidence(fleet.repo_a) / "g.txt").is_file()
    assert work.evidence_tombstones(fleet.repo_b) == []


def test_a_peer_that_lacks_the_evidence_feature_gets_no_new_operation_and_the_sync_continues(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    parse = fleet_sync.Probe.parse

    def older(answer: dict[str, object]) -> fleet_sync.Probe:
        probe = parse(answer)
        return dataclasses.replace(probe, features=()) if probe.id == "b" else probe

    seen: list[tuple[str, str]] = []
    run = fleet_sync.Endpoint.run

    def recording(
        self: fleet_sync.Endpoint,
        *args: str,
        stdin: bytes | None = None,
        timeout: float = fleet_sync.CALL_TIMEOUT,
    ) -> subprocess.CompletedProcess[bytes]:
        seen.append((self.machine, args[0]))
        return run(self, *args, stdin=stdin, timeout=timeout)

    monkeypatch.setattr(fleet_sync.Probe, "parse", staticmethod(older))
    monkeypatch.setattr(fleet_sync.Endpoint, "run", recording)
    assert work.main(["rm", NAME, "--evidence"]) == 0
    code, document = fleet.run("sync", "--copy", NAME)
    assert code == 0, document
    assert (
        "note",
        "evidence",
        "b runs an older fleet_sync; evidence deletions not carried there",
    ) in _results(document)
    assert [op for machine, op in seen if machine == "b" and op.startswith("evidence-")] == []
    assert ("a", "evidence-apply") not in seen
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()
    assert "save-1" in work.pins(fleet.repo_b)[NAME]
    assert work.evidence_tombstones(fleet.repo_b) == []
    assert (_evidence(fleet.repo_b) / "f.txt").is_file()
    assert not _evidence(fleet.repo_a).exists()


def test_clock_skew_between_machines_does_not_change_the_outcome(fleet: Fleet) -> None:
    """A deleter's clock years ahead or behind deletes exactly the recorded states."""
    fleet.at_b()
    evidence = _evidence(fleet.repo_b)
    old = _write(evidence / "old.txt", "old\n")
    new = _write(evidence / "new.txt", "new\n")
    other = _write(evidence / "other.txt", "other\n")
    year = 365 * 86400
    os.utime(old, (time.time() - year, time.time() - year))
    os.utime(new, (time.time() + year, time.time() + year))
    os.utime(other, (time.time() - 2 * year, time.time() - 2 * year))
    size, mtime = work.file_state(other.lstat())
    for removed_at in (time.time() + 10 * year, time.time() - 10 * year):
        grave = _grave(NAME, {"old.txt": old, "new.txt": new}, whole=False, removed_at=removed_at)
        grave = dataclasses.replace(grave, files=(*grave.files, ("other.txt", size + 1, mtime)))
        assert work.write_evidence_tombstone(fleet.repo_b, grave)
    _ = _apply(fleet.repo_b)
    assert not old.exists()
    assert not new.exists()
    assert other.is_file()


def test_a_machine_offline_for_days_applies_the_tombstone_and_a_reaped_one_applies_nothing(
    fleet: Fleet,
) -> None:
    fleet.at_b()
    late = _write(_evidence(fleet.repo_b, "lead-merge") / "f.txt", "proof\n")
    gone = _write(_evidence(fleet.repo_b, "sol-review") / "f.txt", "proof\n")
    day = 86400
    week3 = _grave("lead-merge", {"f.txt": late}, removed_at=time.time() - 20 * day)
    reaped = _grave(
        "sol-review",
        {"f.txt": gone},
        removed_at=time.time() - work.EVIDENCE_TOMBSTONE_RETENTION_SECONDS - day,
    )
    assert work.write_evidence_tombstone(fleet.repo_b, week3)
    assert work.write_evidence_tombstone(fleet.repo_b, reaped)
    assert work.main(["gc"]) == 0
    assert work.evidence_tombstones(fleet.repo_b) == [week3]
    _ = _apply(fleet.repo_b)
    assert not late.exists()
    assert gone.is_file()


def test_a_stopped_fleet_carries_and_applies_no_evidence_tombstone(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    copy = _new()
    _age(copy)
    _ = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert work.main(["rm", NAME, "--evidence"]) == 0
    fleet_sync.write_stop(fleet.repo_a, "runaway sync")
    assert fleet.run("sync")[0] == 2
    assert work.evidence_tombstones(fleet.repo_b) == []
    assert (_evidence(fleet.repo_b) / "f.txt").is_file()
    fleet.at_b()
    assert work.write_evidence_tombstone(fleet.repo_b, work.evidence_tombstones(fleet.repo_a)[0])
    fleet_sync.write_stop(fleet.repo_b, "runaway sync")
    with fleet_sync.holding(fleet.repo_b) as token:
        _ = capsys.readouterr()
        argv = [
            "agent",
            "--repo",
            str(fleet.repo_b),
            "evidence-apply",
            "--token",
            token,
        ]
        assert fleet_sync.main(argv) == 1
    assert "the fleet is stopped (runaway sync)" in capsys.readouterr().out
    assert (_evidence(fleet.repo_b) / "f.txt").is_file()


@pytest.mark.parametrize("operation", ["evidence-apply", "evidence-tombstones-import"])
def test_the_new_agent_writes_are_refused_without_the_runs_token(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
    operation: str,
) -> None:
    fleet.at_b()
    held = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    grave = _grave(NAME, {"f.txt": held})
    assert work.write_evidence_tombstone(fleet.repo_b, grave)
    _ = capsys.readouterr()
    assert (
        fleet_sync.main(
            [
                "agent",
                "--repo",
                str(fleet.repo_b),
                operation,
                "--token",
                "guess",
            ],
        )
        == 1
    )
    assert "not part of the fleet_sync run" in capsys.readouterr().out
    assert held.is_file()


def test_an_agent_evidence_apply_answers_its_own_shape_and_makes_no_folder(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fleet.at_b()
    held = _write(_evidence(fleet.repo_b, "lead-merge") / "f.txt", "proof\n")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave("lead-merge", {"f.txt": held}))
    with fleet_sync.holding(fleet.repo_b) as token:
        _ = capsys.readouterr()
        argv = [
            "agent",
            "--repo",
            str(fleet.repo_b),
            "evidence-apply",
            "--token",
            token,
        ]
        assert fleet_sync.main(argv) == 0
    answer = json_object(json_loads(capsys.readouterr().out))
    assert answer == {
        "trashed": {"lead-merge": 1},
        "kept": [],
        "skipped": {},
        "failed": {},
        "remaining": {},
        "leftover": {},
        "stopped": "",
    }
    assert sorted(path.name for path in (fleet.repo_b / ".work" / "evidence").iterdir()) == []


def test_a_failed_trash_move_leaves_the_file_and_reports_failed(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fleet.at_b()
    held = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave(NAME, {"f.txt": held}))
    real_rename = Path.rename

    def refusing(self: Path, target: Path) -> Path:
        if self == held:
            raise PermissionError(1, "Operation not permitted", str(self))
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", refusing)
    answer = _apply(fleet.repo_b)
    assert list(json_object(answer, "failed")) == [f"{NAME}/f.txt"]
    assert held.read_text(encoding="utf-8") == "proof\n"
    assert answer["trashed"] == {}


def test_a_hostile_tombstone_path_is_refused(fleet: Fleet, tmp_path: Path) -> None:
    fleet.at_b()
    outside = _write(tmp_path / "outside" / "x.txt", "outside\n")
    evidence = _evidence(fleet.repo_b)
    evidence.mkdir(parents=True)
    (evidence / "sub").symlink_to(outside.parent, target_is_directory=True)
    grave = _grave(NAME, {"sub/x.txt": outside}, whole=False)
    assert work.write_evidence_tombstone(fleet.repo_b, grave)
    answer = _apply(fleet.repo_b)
    assert list(json_object(answer, "failed")) == [f"{NAME}/sub/x.txt"]
    assert outside.read_text(encoding="utf-8") == "outside\n"
    assert _evidence_trash(fleet.repo_b) == []
    hostile = dict(grave.as_json(), files={"../../x.txt": [8, 1]})
    assert work.EvidenceTombstone.parse(hostile) is None


def test_an_emptied_stem_folder_goes_and_one_left_holding_unrecorded_or_unsynced_files_stays(
    fleet: Fleet,
) -> None:
    """Only recorded files move: what else a stem folder holds keeps it, and is never moved."""
    fleet.at_b()
    clean = _evidence(fleet.repo_b, "fix-i1-clean")
    mixed = _evidence(fleet.repo_b, "lead-merge")
    unsynced = _evidence(fleet.repo_b, "sol-review")
    graves = [
        _grave(stem, {"proofs/f.txt": _write(folder / "proofs" / "f.txt", "proof\n")})
        for stem, folder in (
            ("fix-i1-clean", clean),
            ("lead-merge", mixed),
            ("sol-review", unsynced),
        )
    ]
    _ = _write(mixed / "new.txt", "made after the delete\n")
    python = _write(unsynced / ".venv" / "bin" / "python", "venv\n")
    cache = _write(unsynced / "sub" / "__pycache__" / "m.cpython-314.pyc", "cache")
    for grave in graves:
        assert work.write_evidence_tombstone(fleet.repo_b, grave)
    answer = _apply(fleet.repo_b)
    assert answer["trashed"] == {"fix-i1-clean": 1, "lead-merge": 1, "sol-review": 1}
    assert (answer["remaining"], answer["leftover"]) == (
        {"lead-merge": 1},
        {"sol-review": [".venv", "sub"]},
    )
    assert not clean.exists()
    assert sorted(path.name for path in mixed.iterdir()) == ["new.txt"]
    assert python.read_text(encoding="utf-8") == "venv\n"
    assert cache.is_file()
    for stem in ("fix-i1-clean", "lead-merge", "sol-review"):
        (entry,) = _evidence_trash(fleet.repo_b, stem)
        assert sorted(path.relative_to(entry).as_posix() for path in entry.rglob("*")) == [
            "proofs",
            "proofs/f.txt",
        ]
    again = _apply(fleet.repo_b)
    assert (again["trashed"], again["remaining"], again["leftover"]) == ({}, {}, {})


def test_a_whole_record_leaves_a_stem_folder_it_moved_no_recorded_file_from(
    fleet: Fleet,
) -> None:
    """A stem made again since the delete, or holding only a venv, is no leftover of it."""
    fleet.at_b()
    reused = _evidence(fleet.repo_b, "lead-merge")
    venv_only = _evidence(fleet.repo_b, "sol-review")
    graves = [
        _grave("lead-merge", {"f.txt": _write(reused / "f.txt", "proof\n")}),
        _grave("sol-review", {"f.txt": _write(venv_only / "f.txt", "proof\n")}),
    ]
    for grave in graves:
        assert work.write_evidence_tombstone(fleet.repo_b, grave)
    shutil.rmtree(reused)
    reused.mkdir()
    (venv_only / "f.txt").unlink()
    python = _write(venv_only / ".venv" / "bin" / "python", "venv\n")
    answer = _apply(fleet.repo_b)
    assert (answer["trashed"], answer["failed"]) == ({}, {})
    assert reused.is_dir()
    assert python.read_text(encoding="utf-8") == "venv\n"
    assert _evidence_trash(fleet.repo_b, "lead-merge") == []
    assert _evidence_trash(fleet.repo_b, "sol-review") == []


def test_a_copy_filter_applies_only_the_stems_of_the_named_copies_including_verify_siblings(
    fleet: Fleet,
) -> None:
    fleet.at_b()
    mine = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    other = _write(_evidence(fleet.repo_b, "lead-merge") / "f.txt", "proof\n")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave(NAME, {"f.txt": mine}))
    assert work.write_evidence_tombstone(fleet.repo_b, _grave("lead-merge", {"f.txt": other}))
    listed = json_list(
        fleet_sync.agent_inventory(fleet.repo_b, [f"{NAME}-verify"]),
        "evidence_tombstones",
    )
    assert [json_object(entry)["stem"] for entry in listed] == [NAME]
    answer = _apply(fleet.repo_b, f"{NAME}-verify")
    assert answer["trashed"] == {NAME: 1}
    assert not mine.exists()
    assert other.is_file()


def test_apply_is_idempotent_and_two_records_for_one_stem_use_separate_trash_entries(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Both applies fall in one second (the clock is held), so their entries could collide."""
    fleet.at_b()
    now = time.time()
    monkeypatch.setattr(time, "time", lambda: now)
    held = _write(_evidence(fleet.repo_b) / "f.txt", "first\n")
    _ = _write(_evidence(fleet.repo_b) / "g.txt", "kept\n")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave(NAME, {"f.txt": held}, whole=False))
    assert _apply(fleet.repo_b)["trashed"] == {NAME: 1}
    assert _apply(fleet.repo_b)["trashed"] == {}
    again = _write(held, "second, longer\n")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave(NAME, {"f.txt": again}, whole=False))
    assert _apply(fleet.repo_b)["trashed"] == {NAME: 1}
    first, second = _evidence_trash(fleet.repo_b)
    assert sorted(
        [
            (first / "f.txt").read_text(encoding="utf-8"),
            (second / "f.txt").read_text(encoding="utf-8"),
        ],
    ) == ["first\n", "second, longer\n"]
    assert (_evidence(fleet.repo_b) / "g.txt").is_file()


def test_a_file_written_after_the_last_listing_stays_in_evidence_and_out_of_the_trash(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A whole record moves recorded files alone: one written while it runs is never swept."""
    fleet.at_b()
    evidence = _evidence(fleet.repo_b)
    held = _write(evidence / "f.txt", "proof\n")
    cache = _write(evidence / "__pycache__" / "m.cpython-314.pyc", "cache")
    assert work.write_evidence_tombstone(fleet.repo_b, _grave(NAME, {"f.txt": held}))
    listing = work.evidence_files
    late = evidence / "new-proof.txt"

    def racing(folder: Path) -> dict[str, tuple[int, int]]:
        found = listing(folder)
        if folder == evidence:
            _ = _write(late, "no tombstone records this\n")
        return found

    monkeypatch.setattr(work, "evidence_files", racing)
    answer = _apply(fleet.repo_b)
    assert answer["trashed"] == {NAME: 1}
    assert late.read_text(encoding="utf-8") == "no tombstone records this\n"
    assert cache.is_file()
    (entry,) = _evidence_trash(fleet.repo_b)
    assert [path.relative_to(entry).as_posix() for path in entry.rglob("*")] == ["f.txt"]


def test_a_copy_made_during_the_owner_check_never_outlives_its_evidence(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The apply holds the stem's lock from its owner check to its last move: ``new`` waits, then refuses."""
    held = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    assert work.write_evidence_tombstone(fleet.repo_a, _grave(NAME, {"f.txt": held}))
    monkeypatch.setattr(work, "STEM_LOCK_WAIT_SECONDS", 0.3, raising=False)
    users = work.evidence_users
    made: list[int] = []

    def interleaved(
        repo: Path,
        stem: str,
        *,
        removed: work.RemovedCopy | None = None,
    ) -> list[str]:
        found = users(repo, stem, removed=removed)
        made.append(
            work.main(
                [
                    "new",
                    NAME,
                    "--no-setup",
                    "--purpose",
                    "a probe",
                ],
            ),
        )
        return found

    monkeypatch.setattr(work, "evidence_users", interleaved)
    answer = _apply(fleet.repo_a)
    alive = NAME in work.discover(fleet.repo_a)
    assert alive or not held.exists()
    assert (made, alive, answer["trashed"]) == ([1], False, {NAME: 1})
    assert not (fleet.repo_a / ".work" / "names" / NAME).exists()


def test_an_apply_while_new_takes_a_stem_skips_it_and_the_new_copy_keeps_its_evidence(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    held = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    assert work.write_evidence_tombstone(fleet.repo_a, _grave(NAME, {"f.txt": held}))
    claim = work.claim_name
    answers: list[dict[str, object]] = []

    def applying(repo: Path, name: str) -> Path:
        claimed = claim(repo, name)
        answers.append(_apply(repo))
        return claimed

    monkeypatch.setattr(work, "claim_name", applying)
    copy = _new()
    assert held.read_text(encoding="utf-8") == "proof\n"
    assert copy.is_dir()
    (answer,) = answers
    assert answer["trashed"] == {}
    assert list(json_object(answer, "skipped")) == [NAME]


def test_an_old_copys_record_never_exempts_a_later_copys_saved_pins(fleet: Fleet) -> None:
    """A record binds its exemption to the removed incarnation's pins, never to its name alone."""
    copy = _new()
    proof = _write(_evidence(fleet.repo_a) / "proof.txt", "proof\n")
    state = proof.lstat()
    _age(copy)
    assert (
        work.main(
            [
                "rm",
                NAME,
                "--drop-saves",
                "--evidence",
            ],
        )
        == 0
    )
    assert len(work.evidence_tombstones(fleet.repo_a)) == 1
    later = _new()
    restored = _write(_evidence(fleet.repo_a) / "proof.txt", "proof\n")
    os.utime(restored, ns=(state.st_atime_ns, state.st_mtime_ns))
    _ = _write(later / "saved.txt", "the later copy's own work\n")
    assert work.main(["save", NAME]) == 0
    _age(later)
    assert work.main(["rm", NAME]) == 0
    assert work.discover(fleet.repo_a)[NAME].form == "pins"
    answer = _apply(fleet.repo_a)
    assert answer["trashed"] == {}
    assert list(json_object(answer, "skipped")) == [NAME]
    assert restored.read_text(encoding="utf-8") == "proof\n"


@pytest.mark.parametrize(
    ("identity", "pinned", "outcome"),
    [
        ("i1", "owned", "trashed"),
        ("", "owned", "kept"),
        ("i1", "fewer", "kept"),
        ("i1", "moved", "kept"),
    ],
    ids=[
        "its-own-pins",
        "a-record-without-identity",
        "a-pin-it-never-owned",
        "a-pin-moved-since",
    ],
)
def test_a_removed_copys_name_is_exempt_only_while_it_holds_the_pins_the_record_lists(
    fleet: Fleet,
    identity: str,
    pinned: str,
    outcome: str,
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved\n")
    assert work.main(["save", NAME]) == 0
    _ = _write(copy / "saved.txt", "saved again\n")
    assert work.main(["save", NAME]) == 0
    _age(copy)
    assert work.main(["rm", NAME]) == 0
    held = work.pins(fleet.repo_a)[NAME]
    assert set(held) == {"save-1", "save-2"}
    listed = {
        "owned": held,
        "fewer": {"save-1": held["save-1"]},
        "moved": {"save-1": held["save-1"], "save-2": held["save-1"]},
    }[pinned]
    proof = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    grave = dataclasses.replace(
        _grave(NAME, {"f.txt": proof}),
        copy=NAME,
        identity=identity,
        pins=tuple(sorted(listed.items())),
    )
    assert work.write_evidence_tombstone(fleet.repo_a, grave)
    answer = _apply(fleet.repo_a)
    assert ("kept" if proof.exists() else "trashed") == outcome
    if outcome == "kept":
        assert answer["skipped"] == {NAME: f"{NAME} still use it here"}


def test_a_stop_raised_during_an_apply_moves_nothing_of_the_next_stem(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fleet.at_b()
    first = _write(_evidence(fleet.repo_b, "lead-merge") / "f.txt", "proof\n")
    second = _write(_evidence(fleet.repo_b, "sol-review") / "f.txt", "proof\n")
    for stem, held in (("lead-merge", first), ("sol-review", second)):
        assert work.write_evidence_tombstone(fleet.repo_b, _grave(stem, {"f.txt": held}))
    move = work.move_evidence_file

    def stopping(
        folder: Path,
        rel: str,
        state: tuple[int, int],
        entry: Callable[[], Path],
    ) -> str:
        outcome = move(folder, rel, state, entry)
        fleet_sync.write_stop(fleet.repo_b, "mid apply")
        return outcome

    monkeypatch.setattr(work, "move_evidence_file", stopping)
    answer = _apply(fleet.repo_b)
    assert (answer["trashed"], answer.get("stopped")) == ({"lead-merge": 1}, "mid apply")
    assert not first.exists()
    assert second.read_text(encoding="utf-8") == "proof\n"


def test_an_evidence_tombstone_adds_about_one_listing_of_its_stem_to_the_inventory(
    fleet: Fleet,
) -> None:
    """A large stem's record costs an older run's inventory about what the stem's listing costs."""
    fleet.at_b()
    evidence = _evidence(fleet.repo_b, "lead-merge")
    for index in range(1000):
        _ = _write(evidence / "proofs" / f"run-{index:04}" / "out.txt", f"{index}\n")
    before = len(json.dumps(fleet_sync.agent_inventory(fleet.repo_b, [])))
    listing = len(json.dumps(work.evidence_files(evidence)))
    files = {rel: evidence / rel for rel in work.evidence_files(evidence)}
    assert work.write_evidence_tombstone(fleet.repo_b, _grave("lead-merge", files))
    after = len(json.dumps(fleet_sync.agent_inventory(fleet.repo_b, [])))
    assert listing < after - before < listing * 1.1


@dataclasses.dataclass(frozen=True)
class _Call:
    """One agent call a run made: the machine, its argv after ``agent --repo``, stdin, stdout."""

    machine: str
    args: tuple[str, ...]
    stdin: bytes
    stdout: bytes


def _record_calls(patch: pytest.MonkeyPatch) -> list[_Call]:
    """Record every agent call the run makes (in order) and let each one through."""
    seen: list[_Call] = []
    run = fleet_sync.Endpoint.run

    def recording(
        self: fleet_sync.Endpoint,
        *args: str,
        stdin: bytes | None = None,
        timeout: float = fleet_sync.CALL_TIMEOUT,
    ) -> subprocess.CompletedProcess[bytes]:
        completed = run(self, *args, stdin=stdin, timeout=timeout)
        seen.append(_Call(self.machine, args, stdin or b"", completed.stdout))
        return completed

    patch.setattr(fleet_sync.Endpoint, "run", recording)
    return seen


def _without_feature(patch: pytest.MonkeyPatch, machine: str, feature: str) -> None:
    """Make machine ``machine``'s probe lack ``feature``, as an older script's does."""
    parse = fleet_sync.Probe.parse

    def older(answer: dict[str, object]) -> fleet_sync.Probe:
        probe = parse(answer)
        if probe.id != machine:
            return probe
        return dataclasses.replace(
            probe,
            features=tuple(name for name in probe.features if name != feature),
        )

    patch.setattr(fleet_sync.Probe, "parse", staticmethod(older))


def _tombstone(name: str, *, removed_at: float | None = None, pins: int = 1) -> work.Tombstone:
    """Return a pins-alone tombstone of ``name`` recording ``pins`` dropped pins, as ``a`` writes."""
    dropped = tuple((f"save-{index}", f"{index:040x}") for index in range(1, pins + 1))
    at = time.time() if removed_at is None else removed_at
    return work.Tombstone(name, "a", f"pins@{name}", at, "a", dropped_pins=dropped)


def _records(repo: Path) -> tuple[set[str], set[str]]:
    """Return the file names of ``repo``'s tombstones and evidence tombstones."""
    return (
        {grave.file_name for grave in work.tombstones(repo)},
        {grave.file_name for grave in work.evidence_tombstones(repo)},
    )


def test_the_timer_lists_tombstone_ids_alone_and_moves_no_body_both_machines_hold(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Records both machines hold cost the timer's inventories one id each, and no body moves."""
    held = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    grave = _grave(NAME, {"f.txt": held}, whole=False)
    tombstone = _tombstone("spike-fleet-gone")
    for repo in (fleet.repo_a, fleet.repo_b):
        assert work.write_evidence_tombstone(repo, grave)
        assert work.write_tombstone(repo, tombstone)
    seen = _record_calls(monkeypatch)
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    inventories = [call for call in seen if call.args[0] == "inventory"]
    assert sorted(call.machine for call in inventories) == ["a", "b"]
    for call in inventories:
        assert {"--ids", "--no-evidence"} <= set(call.args)
        answer = json_object(json_loads(call.stdout.decode()))
        assert answer["evidence"] == {}
        assert answer["tombstones"] == {tombstone.file_name: tombstone.removed_at}
        assert answer["evidence_tombstones"] == {grave.file_name: grave.removed_at}
    assert [call for call in seen if call.args[0].startswith(("tombstones-", "evidence-"))] == []


def test_a_missing_tombstone_body_moves_by_id_both_ways_and_reaches_the_planning(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only a record one side lacks moves, asked for by id and sent under it."""
    held = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    theirs = _grave(NAME, {"f.txt": held}, whole=False)
    from_b = _tombstone("spike-fleet-b")
    from_a = _tombstone("spike-fleet-a")
    both = _tombstone("spike-fleet-both")
    assert work.write_evidence_tombstone(fleet.repo_b, theirs)
    assert work.write_tombstone(fleet.repo_b, from_b)
    assert work.write_tombstone(fleet.repo_a, from_a)
    for repo in (fleet.repo_a, fleet.repo_b):
        assert work.write_tombstone(repo, both)
    seen = _record_calls(monkeypatch)
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    names = {from_a.file_name, from_b.file_name, both.file_name}
    assert _records(fleet.repo_a) == _records(fleet.repo_b) == (names, {theirs.file_name})
    exports = [
        (call.machine, json_object(json_loads(call.stdin.decode())))
        for call in seen
        if call.args[0] == "tombstones-export"
    ]
    assert exports == [
        ("a", {"tombstones": [from_a.file_name], "evidence_tombstones": []}),
        ("b", {"tombstones": [from_b.file_name], "evidence_tombstones": [theirs.file_name]}),
    ]
    imports = [call for call in seen if call.args[0].endswith("-import")]
    assert [(call.machine, call.args[0]) for call in imports] == [
        ("b", "tombstones-import"),
        ("a", "tombstones-import"),
        ("a", "evidence-tombstones-import"),
    ]
    sent = {
        (call.machine, key): sorted(str(rel) for rel in json_object(value))
        for call in imports
        for key, value in json_object(json_loads(call.stdin.decode())).items()
    }
    assert sent == {
        ("b", "tombstones"): [from_a.file_name],
        ("a", "tombstones"): [from_b.file_name],
        ("a", "evidence_tombstones"): [theirs.file_name],
    }


def test_a_tombstone_body_that_does_not_match_its_id_is_refused_by_the_run(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A peer sending another record's body under an id writes nothing and fails the pair."""
    first, second = _tombstone("spike-fleet-one"), _tombstone("spike-fleet-two")
    for tombstone in (first, second):
        assert work.write_tombstone(fleet.repo_b, tombstone)
    call = fleet_sync.Endpoint.call

    def swapping(
        self: fleet_sync.Endpoint,
        *args: str,
        stdin: bytes | None = None,
    ) -> dict[str, object]:
        answer = call(self, *args, stdin=stdin)
        if args[0] == "tombstones-export":
            bodies = json_object(answer["tombstones"])
            answer["tombstones"] = dict.fromkeys(bodies, bodies[second.file_name])
        return answer

    monkeypatch.setattr(fleet_sync.Endpoint, "call", swapping)
    code, document = fleet.run("sync", "--timer")
    assert code == 1, document
    assert (
        "failed",
        "pins",
        f"b: tombstone {first.file_name} does not match its id; refused",
    ) in _results(document)
    assert work.tombstones(fleet.repo_a) == []


def test_an_agent_refuses_an_imported_body_sent_under_another_id(fleet: Fleet) -> None:
    """The importing machine checks each body against the id it came under; a list has none."""
    held = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    grave = _grave(NAME, {"f.txt": held}, whole=False)
    other = _grave(NAME, {"f.txt": held}, whole=True)
    first, second = _tombstone("spike-fleet-one"), _tombstone("spike-fleet-two")
    fleet.at_b()
    document = {"tombstones": {first.file_name: second.as_json()}}
    answer = fleet_sync.agent_tombstones_import(fleet.repo_b, json.dumps(document).encode())
    assert (answer["created"], answer["refused"]) == ([], [first.file_name])
    document = {"evidence_tombstones": {grave.file_name: other.as_json()}}
    answer = fleet_sync.agent_evidence_tombstones_import(
        fleet.repo_b,
        json.dumps(document).encode(),
    )
    assert (answer["created"], answer["refused"]) == ([], [grave.file_name])
    assert _records(fleet.repo_b) == (set(), set())
    document = {"tombstones": [first.as_json()], "evidence_tombstones": [grave.as_json()]}
    data = json.dumps(document).encode()
    assert fleet_sync.agent_tombstones_import(fleet.repo_b, data)["created"] == [first.file_name]
    created = fleet_sync.agent_evidence_tombstones_import(fleet.repo_b, data)["created"]
    assert created == [grave.file_name]


def test_a_peer_without_tombstone_ids_gets_the_full_exchange_and_both_sides_still_converge(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An older peer is never sent ``--ids``, an export or an id-keyed import, and still syncs."""
    held = _write(_evidence(fleet.repo_b) / "f.txt", "proof\n")
    theirs = _grave(NAME, {"f.txt": held}, whole=False)
    from_b, from_a = _tombstone("spike-fleet-b"), _tombstone("spike-fleet-a")
    assert work.write_evidence_tombstone(fleet.repo_b, theirs)
    assert work.write_tombstone(fleet.repo_b, from_b)
    assert work.write_tombstone(fleet.repo_a, from_a)
    _without_feature(monkeypatch, "b", fleet_sync.IDS_FEATURE)
    seen = _record_calls(monkeypatch)
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    names = {from_a.file_name, from_b.file_name}
    assert _records(fleet.repo_a) == _records(fleet.repo_b) == (names, {theirs.file_name})
    at_b = [call for call in seen if call.machine == "b"]
    assert [call.args for call in at_b if call.args[0] == "inventory"] == [("inventory",)]
    assert [call for call in at_b if call.args[0] == "tombstones-export"] == []
    sent = [call for call in at_b if call.args[0] == "tombstones-import"]
    assert [
        json_list(json_object(json_loads(call.stdin.decode())), "tombstones") for call in sent
    ] == [
        [from_a.as_json()],
    ]


def test_a_record_gc_deleted_never_comes_back_from_a_machine_that_still_holds_it(
    fleet: Fleet,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Past its retention a record moves neither way, and no agent imports one."""
    held = _write(_evidence(fleet.repo_a) / "f.txt", "proof\n")
    day = 86400
    expired = _grave(
        NAME,
        {"f.txt": held},
        whole=False,
        removed_at=time.time() - work.EVIDENCE_TOMBSTONE_RETENTION_SECONDS - day,
    )
    old = _tombstone(
        "spike-fleet-old",
        removed_at=time.time() - work.TOMBSTONE_RETENTION_SECONDS - day,
    )
    for repo in (fleet.repo_a, fleet.repo_b):
        assert work.write_evidence_tombstone(repo, expired)
        assert work.write_tombstone(repo, old)
    fleet.at_b()
    assert work.main(["gc"]) == 0
    assert _records(fleet.repo_b) == (set(), set())
    fleet.at_a()
    seen = _record_calls(monkeypatch)
    for _run in range(2):
        code, document = fleet.run("sync", "--timer")
        assert code == 0, document
        assert _records(fleet.repo_b) == (set(), set())
    assert [call for call in seen if call.args[0].startswith(("tombstones-", "evidence-"))] == []
    fleet.at_b()
    document = {"tombstones": [old.as_json()], "evidence_tombstones": [expired.as_json()]}
    data = json.dumps(document).encode()
    answer = fleet_sync.agent_tombstones_import(fleet.repo_b, data)
    assert (answer["created"], answer["expired"]) == ([], [old.file_name])
    answer = fleet_sync.agent_evidence_tombstones_import(fleet.repo_b, data)
    assert (answer["created"], answer["expired"]) == ([], [expired.file_name])
    assert _records(fleet.repo_b) == (set(), set())


@pytest.mark.parametrize("kind", ["evidence", "pins"])
def test_an_inventory_by_id_stays_one_size_however_many_files_or_pins_a_record_lists(
    fleet: Fleet,
    kind: str,
) -> None:
    """The ids answer's size depends on how many records there are, never on their bodies."""
    fleet.at_b()
    evidence = _evidence(fleet.repo_b, "lead-merge")
    for index in range(1000):
        _ = _write(evidence / "proofs" / f"run-{index:04}" / "out.txt", f"{index}\n")
    files = {rel: evidence / rel for rel in work.evidence_files(evidence)}
    sizes: list[tuple[int, int]] = []
    for count in (1, 1000):
        for folder in ("tombstones", "evidence-tombstones"):
            shutil.rmtree(fleet.repo_b / ".work" / folder, ignore_errors=True)
        if kind == "evidence":
            listed = dict(sorted(files.items())[:count])
            record = _grave("lead-merge", listed, removed_at=1_700_000_000.0)
            assert work.write_evidence_tombstone(fleet.repo_b, record)
        else:
            tombstone = _tombstone("spike-fleet-gone", removed_at=1_700_000_000.0, pins=count)
            assert work.write_tombstone(fleet.repo_b, tombstone)
        body = len(json.dumps(fleet_sync.agent_inventory(fleet.repo_b, [], evidence=False)))
        ids = fleet_sync.agent_inventory(fleet.repo_b, [], ids=True, evidence=False)
        sizes.append((body, len(json.dumps(ids))))
    (small_body, small_ids), (large_body, large_ids) = sizes
    assert large_body > small_body * 10
    assert large_ids == small_ids


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------


def test_main_fast_forwards_from_a_peer_ahead_under_every_guard(fleet: Fleet) -> None:
    ahead = _commit(fleet.repo_b, "new.txt", "from b\n")
    code, document = fleet.run("sync", "--main-only", "--dry-run")
    assert code == 0
    assert any("would fast-forward main" in detail for _r, _s, detail in _results(document))
    assert _git_out(fleet.repo_a, "rev-parse", "HEAD").strip() != ahead
    assert not _git_out(fleet.repo_a, "for-each-ref", "--contains", ahead).strip()
    _ = _write(fleet.repo_a / "new.txt", "dirty here\n")
    code, document = fleet.run("sync", "--main-only")
    assert code == 1
    assert any("--ff-only refused" in detail for _r, _s, detail in _results(document))
    (fleet.repo_a / "new.txt").unlink()
    code, document = fleet.run("sync", "--main-only")
    assert code == 0, document
    assert _git_out(fleet.repo_a, "rev-parse", "HEAD").strip() == ahead
    code, document = fleet.run("sync", "--main-only")
    assert ("fresh", "main", f"main {ahead[:12]} on both") in _results(document)


def test_main_is_never_merged_when_diverged_and_never_moved_off_main(fleet: Fleet) -> None:
    _ = _commit(fleet.repo_b, "b.txt", "b\n")
    here = _commit(fleet.repo_a, "a.txt", "a\n")
    code, document = fleet.run("sync", "--main-only")
    assert code == 1
    assert any(
        result == "conflict" and "diverged" in detail for result, _s, detail in _results(document)
    )
    assert _git_out(fleet.repo_a, "rev-parse", "HEAD").strip() == here
    _ = _git_out(fleet.repo_a, "checkout", "-q", "--detach")
    _ = _git_out(fleet.repo_a, "reset", "-q", "--hard", "HEAD~1")
    _ = _git_out(fleet.repo_a, "update-ref", "refs/heads/main", "HEAD")
    code, document = fleet.run("sync", "--main-only")
    assert code == 1
    assert any("not refs/heads/main" in detail for _r, _s, detail in _results(document))


def test_a_copy_run_leaves_main_alone(fleet: Fleet) -> None:
    _ = _commit(fleet.repo_b, "new.txt", "from b\n")
    before = _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()
    _age(_new())
    assert fleet.run("sync", "--copy", NAME)[0] == 0
    assert _git_out(fleet.repo_a, "rev-parse", "HEAD").strip() == before


def _main(repo: Path) -> str:
    return _git_out(repo, "rev-parse", "refs/heads/main").strip()


def _after_pins(patch: pytest.MonkeyPatch, then: Callable[[], object]) -> None:
    """Run ``then`` after each peer's pin pass, before the timer run's main pass."""
    real = fleet_sync.sync_pins_with_peer

    def wrapped(
        here: fleet_sync.Machine,
        peer: fleet_sync.Machine,
        local_token: str,
        args: fleet_sync._Args,
    ) -> list[fleet_sync.Row]:
        rows = real(here, peer, local_token, args)
        _ = then()
        return rows

    patch.setattr(fleet_sync, "sync_pins_with_peer", wrapped)


def test_the_timer_run_carries_saves_and_fast_forwards_main_where_pins_only_does_not(
    fleet: Fleet,
) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved on a\n")
    assert work.main(["save", NAME]) == 0
    before = _main(fleet.repo_a)
    ahead = _commit(fleet.repo_b, "new.txt", "from b\n")
    code, document = fleet.run("sync", "--pins-only")
    assert code == 0, document
    assert _main(fleet.repo_a) == before
    code, document = fleet.run("sync", "--timer", "--dry-run")
    assert code == 0, document
    assert any("would fast-forward main" in detail for _r, _s, detail in _results(document))
    assert _main(fleet.repo_a) == before
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == ahead
    assert (fleet.repo_a / "new.txt").read_text() == "from b\n"
    assert _main(fleet.repo_b) == ahead
    assert work.pins(fleet.repo_b)[NAME] == work.pins(fleet.repo_a)[NAME]
    assert ("note", "main", fleet_sync.STALE_VENV) not in _results(document)


def test_a_land_holding_its_lock_skips_the_timers_main_pass_with_a_note(fleet: Fleet) -> None:
    before = _main(fleet.repo_a)
    _ = _commit(fleet.repo_b, "new.txt", "from b\n")
    with contextlib.ExitStack() as stack:
        _after_pins(fleet.monkeypatch, lambda: stack.enter_context(work.land_lock(fleet.repo_a)))
        code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == before
    assert any(
        result == "note" and subject == "main" and "land is in progress" in detail
        for result, subject, detail in _results(document)
    )


@pytest.mark.parametrize(
    "state",
    [
        "detached",
        "merge",
        "bisect",
        "index-lock",
    ],
)
def test_the_timer_leaves_main_alone_off_main_mid_operation_or_with_the_index_locked(
    fleet: Fleet,
    state: str,
) -> None:
    _ = _commit(fleet.repo_b, "new.txt", "from b\n")
    expected = {
        "detached": "not refs/heads/main",
        "merge": "MERGE_HEAD in progress",
        "bisect": "BISECT_LOG in progress",
        "index-lock": "the index is locked",
    }[state]
    if state == "detached":
        _ = _git_out(fleet.repo_a, "checkout", "-q", "--detach")
    elif state == "merge":
        _ = _git_out(fleet.repo_a, "checkout", "-q", "--detach")
        side = _commit(fleet.repo_a, "side.txt", "side\n")
        _ = _git_out(fleet.repo_a, "checkout", "-q", "main")
        _ = _git_out(fleet.repo_a, "merge", "-q", "--no-commit", "--no-ff", side)
    elif state == "bisect":
        _ = _git_out(fleet.repo_a, "bisect", "start")
    else:
        _ = _write(fleet.repo_a / ".git" / "index.lock", "")
    main, head = _main(fleet.repo_a), _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert (_main(fleet.repo_a), _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()) == (
        main,
        head,
    )
    assert any(
        result == "note" and subject == "main" and expected in detail
        for result, subject, detail in _results(document)
    ), document


def test_the_timer_fast_forward_keeps_every_uncommitted_change_it_does_not_touch(
    fleet: Fleet,
) -> None:
    ahead = _commit(fleet.repo_b, "new.txt", "from b\n")
    _ = _write(fleet.repo_a / "gone.txt", "unstaged here\n")
    package = fleet.repo_a / "django_strawberry_framework" / "__init__.py"
    _ = _write(package, "VALUE = 2\n")
    _ = _git_out(fleet.repo_a, "add", str(package))
    _ = _write(fleet.repo_a / "untracked.txt", "untracked here\n")
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == ahead
    assert (fleet.repo_a / "gone.txt").read_text() == "unstaged here\n"
    assert package.read_text() == "VALUE = 2\n"
    staged = _git_out(fleet.repo_a, "diff", "--cached", "--name-only").split()
    assert staged == ["django_strawberry_framework/__init__.py"]
    assert (fleet.repo_a / "untracked.txt").read_text() == "untracked here\n"


def test_a_dirty_path_the_fast_forward_would_change_blocks_it_with_a_note_naming_it(
    fleet: Fleet,
) -> None:
    _ = _git_out(fleet.repo_a, "config", "merge.autoStash", "true")
    _ = _commit(fleet.repo_b, "gone.txt", "changed on b\n")
    before = _main(fleet.repo_a)
    _ = _write(fleet.repo_a / "gone.txt", "dirty here\n")
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == before
    assert (fleet.repo_a / "gone.txt").read_text() == "dirty here\n"
    assert not _git_out(fleet.repo_a, "stash", "list").strip()
    assert any(
        result == "note"
        and subject == "main"
        and "uncommitted changes to gone.txt would be overwritten" in detail
        for result, subject, detail in _results(document)
    ), document


def test_a_diverged_main_is_one_conflict_row_per_peer_and_leaves_the_timer_exit_clean(
    fleet: Fleet,
) -> None:
    _ = _commit(fleet.repo_b, "b.txt", "b\n")
    here = _commit(fleet.repo_a, "a.txt", "a\n")
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    diverged = [row for row in _results(document) if row[1] == "main" and "diverged" in row[2]]
    assert [result for result, _s, _d in diverged] == ["conflict"]
    assert _main(fleet.repo_a) == here
    assert fleet.run("sync", "--main-only")[0] == 1


def test_a_fast_forward_that_changes_uv_lock_adds_a_stale_venv_note(fleet: Fleet) -> None:
    ahead = _commit(fleet.repo_b, "uv.lock", "version = 1\n")
    venv = sorted(str(path) for path in (fleet.repo_a / ".venv").rglob("*"))
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == ahead
    assert ("note", "main", fleet_sync.STALE_VENV) in _results(document)
    assert sorted(str(path) for path in (fleet.repo_a / ".venv").rglob("*")) == venv


def test_the_stop_flag_stops_the_timer_run_and_one_written_mid_run_its_main_pass(
    fleet: Fleet,
) -> None:
    before = _main(fleet.repo_a)
    _ = _commit(fleet.repo_b, "new.txt", "from b\n")
    fleet_sync.write_stop(fleet.repo_a, "halt")
    assert fleet.run("sync", "--timer")[0] == 2
    assert _main(fleet.repo_a) == before
    (fleet.repo_a / ".work" / fleet_sync.STOP_FLAG).unlink()
    _after_pins(fleet.monkeypatch, lambda: fleet_sync.write_stop(fleet.repo_a, "mid run"))
    code, document = fleet.run("sync", "--timer")
    assert code == 0, document
    assert _main(fleet.repo_a) == before
    assert any(
        result == "note" and "the fleet is stopped (mid run)" in detail
        for result, _s, detail in _results(document)
    ), document


# --------------------------------------------------------------------------------------------
# Locks
# --------------------------------------------------------------------------------------------


def test_one_run_per_machine_and_none_during_a_land(fleet: Fleet) -> None:
    _age(_new())
    with fleet_sync.holding(fleet.repo_a):
        code, document = fleet.run("sync", "--copy", NAME)
    assert code == 1
    assert any("another fleet_sync run" in detail for _r, _s, detail in _results(document))
    with work.land_lock(fleet.repo_b):
        code, document = fleet.run("status")
    assert "land is in progress" in str(_machines(document)["b"]["reason"])


def test_an_agent_write_outside_a_held_run_is_refused(fleet: Fleet) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            fleet_sync.__file__,
            "agent",
            "--repo",
            str(fleet.repo_b),
            "prepare",
            NAME,
            "--home",
            "a",
            "--head",
            "HEAD",
            "--token",
            "guess",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1
    assert "not part of the fleet_sync run" in completed.stdout
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()


# --------------------------------------------------------------------------------------------
# Deadlines: a stalled peer never hangs a run
# --------------------------------------------------------------------------------------------


class _SilentPeer(fleet_sync.Endpoint):
    """A peer whose ``hold`` connects and then never answers."""

    @override
    def argv(self, *args: str) -> list[str]:
        return [sys.executable, "-c", "import time; time.sleep(30)"]


def _capture_run(patch: pytest.MonkeyPatch, seen: list[tuple[list[str], dict[str, str]]]) -> None:
    def fake(
        argv: list[str],
        env: dict[str, str] | None = None,
        **_kwargs: object,
    ) -> subprocess.CompletedProcess[bytes]:
        seen.append((argv, dict(env or {})))
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    patch.setattr(subprocess, "run", fake)


def test_a_peers_ssh_and_rsync_carry_the_keepalive_and_rsync_an_io_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    peer = fleet_sync.Endpoint("b", "b", "b-ssh", SCRIPTS)
    argv = peer.argv("probe")
    assert argv == fleet_rules.ssh_argv("b-ssh", argv[-1])
    seen: list[tuple[list[str], dict[str, str]]] = []
    _capture_run(monkeypatch, seen)
    fleet_sync.rsync(fleet_sync.Endpoint("a", "a", ""), "/x", peer, "/y")
    rsync_argv = seen[0][0]
    assert "--timeout=120" in rsync_argv
    assert rsync_argv[rsync_argv.index("-e") + 1] == fleet_rules.ssh_command()


def test_fetch_main_runs_git_with_the_batch_mode_keepalive_ssh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DSF_FETCH_PROBE", "kept")
    probe = fleet_sync.Probe(
        id="b",
        os="linux",
        repo="/home/b/projects/django-strawberry-framework",
        at_checkout=True,
        roots=(),
        branch="main",
        main="0" * 40,
        ignored=True,
        land_busy=False,
        fleet_busy=False,
        rsync="rsync",
    )
    machine = fleet_sync.Machine("b", "b-ssh", "linux", local=False, row="", probe=probe)
    seen: list[tuple[list[str], dict[str, str]]] = []
    _capture_run(monkeypatch, seen)
    assert not fleet_sync.fetch_main(machine)
    argv, env = next((argv, env) for argv, env in seen if "fetch" in argv)
    assert f"b-ssh:{probe.repo}" in argv
    assert env["GIT_SSH_COMMAND"] == fleet_rules.ssh_command()
    assert env["DSF_FETCH_PROBE"] == "kept"


def test_a_hold_on_a_silent_peer_times_out_with_a_fleet_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(fleet_sync, "HOLD_TIMEOUT", 0.3)
    started = time.monotonic()
    with (
        pytest.raises(fleet_sync.FleetError, match=r"the hold printed nothing in 0\.3s"),
        _SilentPeer("b", "b", "b-ssh").hold("token"),
    ):
        pass
    assert time.monotonic() - started < 10


def test_sync_pins_only_carries_saves_both_ways_and_nothing_else(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved on a\n")
    assert work.main(["save", NAME]) == 0
    _ = _write(fleet.repo_a / ".work" / "evidence" / NAME / "proof.txt", "evidence\n")
    fleet.at_b()
    other = _new("spike-fleet-other")
    _ = _write(other / "saved.txt", "saved on b\n")
    assert work.main(["save", "spike-fleet-other"]) == 0
    head_b = _git_out(fleet.repo_b, "rev-parse", "HEAD").strip()
    fleet.at_a()
    _ = _commit(fleet.repo_a, "later.txt", "main moved on a\n")
    code, document = fleet.run("sync", "--pins-only")
    assert code == 0, document
    assert work.pins(fleet.repo_b)[NAME] == work.pins(fleet.repo_a)[NAME]
    assert (
        work.pins(fleet.repo_a)["spike-fleet-other"]
        == work.pins(fleet.repo_b)["spike-fleet-other"]
    )
    assert not (fleet.repo_b / ".work" / "clones" / NAME).exists()
    assert not (fleet.repo_a / ".work" / "clones" / "spike-fleet-other").exists()
    assert not (fleet.repo_b / ".work" / "evidence" / NAME).exists()
    assert _git_out(fleet.repo_b, "rev-parse", "HEAD").strip() == head_b
    code, document = fleet.run("sync", "--pins-only")
    assert code == 0, document
    assert not [row for row in _results(document) if row[0] != "skip"]


@pytest.mark.parametrize(
    "flags",
    [("--pins-only", "--main-only"), ("--timer", "--pins-only"), ("--timer", "--main-only")],
)
def test_the_sync_scope_flags_cannot_be_combined(fleet: Fleet, flags: tuple[str, str]) -> None:
    with pytest.raises(SystemExit) as raised:
        _ = fleet.run("sync", *flags)
    assert raised.value.code == 2


def test_the_timer_line_runs_sync_timer(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(fleet_sync, "REPO_ROOT", tmp_path)
    line = fleet_sync.schedule_line()
    assert "docs/fleet/scripts/fleet_sync.py sync --timer --json" in line
    assert "--pins-only" not in line


def test_the_macos_schedule_is_a_launchd_agent_running_sync_timer(tmp_path: Path) -> None:
    files = fleet_sync.schedule_files(tmp_path, 120, "darwin")
    [(path, text)] = files.items()
    assert path == tmp_path / "Library" / "LaunchAgents" / f"{fleet_sync.SCHEDULE_LABEL}.plist"
    agent = json_object(_load_plist(text.encode()))
    program = json_list(agent, "ProgramArguments")
    assert program[:2] == ["/bin/sh", "-c"]
    assert "docs/fleet/scripts/fleet_sync.py sync --timer --json" in str(program[2])
    assert agent["StartInterval"] == 120
    assert agent["WorkingDirectory"] == str(fleet_sync.REPO_ROOT)
    assert agent["StandardOutPath"] == str(fleet_sync.REPO_ROOT / ".work" / "fleet-pins.log")
    commands = fleet_sync.schedule_commands(files, "darwin")
    assert [command[:2] for command in commands] == [
        ["launchctl", "bootout"],
        ["launchctl", "bootstrap"],
    ]


def test_the_linux_schedule_is_a_systemd_user_timer(tmp_path: Path) -> None:
    files = fleet_sync.schedule_files(tmp_path, 300, "linux")
    units = tmp_path / ".config" / "systemd" / "user"
    service = files[units / f"{fleet_sync.SCHEDULE_UNIT}.service"]
    timer = files[units / f"{fleet_sync.SCHEDULE_UNIT}.timer"]
    assert "sync --timer --json" in service
    assert "OnUnitActiveSec=300s" in timer
    assert f">> {fleet_sync.REPO_ROOT / '.work' / 'fleet-pins.log'} 2>&1" in service
    assert fleet_sync.schedule_commands(files, "linux")[-1][-2:] == [
        "--now",
        f"{fleet_sync.SCHEDULE_UNIT}.timer",
    ]
    with pytest.raises(fleet_sync.SetupError, match="not win32"):
        _ = fleet_sync.schedule_files(tmp_path, 300, "win32")


def test_schedule_prints_by_default_and_installs_only_when_asked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    ran: list[list[str]] = []

    def record(commands: Sequence[Sequence[str]]) -> None:
        ran.extend(list(command) for command in commands)

    monkeypatch.setattr(fleet_sync, "load_schedule", record)
    assert fleet_sync.main(["schedule"]) == 0
    printed = capsys.readouterr().out
    assert "sync --timer --json" in printed
    assert not list(tmp_path.rglob("*"))
    assert not ran
    assert fleet_sync.main(["schedule", "--every", "10"]) == 2
    assert (
        fleet_sync.main(
            [
                "schedule",
                "--install",
                "--every",
                "60",
            ],
        )
        == 0
    )
    written = list(fleet_sync.schedule_files(tmp_path, 60))
    assert all(path.is_file() for path in written)
    assert ran == fleet_sync.schedule_commands(fleet_sync.schedule_files(tmp_path, 60))


def test_a_stopped_fleet_refuses_sync_and_fetch_pins(
    fleet: Fleet,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fleet_sync.write_stop(fleet.repo_a, "runaway sync")
    assert fleet_sync.stop_reason(fleet.repo_a) == "runaway sync"
    for command in (
        ["sync", "--pins-only"],
        [
            "fetch-pins",
            NAME,
            "--machine",
            "b",
        ],
    ):
        _ = capsys.readouterr()
        assert fleet_sync.main([*command, "--remote-scripts", SCRIPTS]) == 2
        assert "the fleet is stopped (runaway sync)" in capsys.readouterr().err


def test_a_machine_that_meets_a_stopped_peer_stops_itself(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved\n")
    assert work.main(["save", NAME]) == 0
    fleet_sync.write_stop(fleet.repo_b, "stopped on b")
    code, _document = fleet.run("sync", "--pins-only")
    assert code == 2
    assert fleet_sync.stop_reason(fleet.repo_a).startswith("adopted from ")
    assert fleet_sync.stop_reason(fleet.repo_a).endswith("stopped on b")
    assert NAME not in work.pins(fleet.repo_b)


def test_the_timer_line_checks_the_stop_flag_before_any_python(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(fleet_sync, "REPO_ROOT", tmp_path)
    line = fleet_sync.schedule_line()
    assert line.index(".work/fleet-stop") < line.index(".venv/bin/python")
    assert f"alarm shift @ARGV; exec @ARGV or die' {fleet_sync.SCHEDULE_TIME_LIMIT}" in line
    (tmp_path / ".work").mkdir()
    (tmp_path / ".work" / "fleet-stop").write_text("stopped\n")
    assert subprocess.run(["/bin/sh", "-c", line], check=False).returncode == 0
    (tmp_path / ".work" / "fleet-stop").unlink()
    ran = subprocess.run(["/bin/sh", "-c", line], capture_output=True, check=False)
    assert ran.returncode != 0


def test_sync_pins_only_leaves_landed_pins_that_moved_alone(fleet: Fleet) -> None:
    copy = _new()
    _ = _write(copy / "saved.txt", "saved\n")
    assert work.main(["save", NAME]) == 0
    head_a = _git_out(fleet.repo_a, "rev-parse", "HEAD").strip()
    assert work.publish_pin(fleet.repo_a, copy, head_a, NAME, "landed")
    fleet.at_b()
    other = _commit(fleet.repo_b, "b.txt", "b\n")
    assert work.publish_pin(fleet.repo_b, fleet.repo_b, other, NAME, "landed")
    fleet.at_a()
    code, document = fleet.run("sync", "--pins-only")
    assert code == 0, document
    assert not [row for row in _results(document) if row[0] == "conflict"]
    assert "save-1" in work.pins(fleet.repo_b)[NAME]
    assert work.pins(fleet.repo_b)[NAME]["landed"] == other
    assert work.pins(fleet.repo_a)[NAME]["landed"] == head_a
