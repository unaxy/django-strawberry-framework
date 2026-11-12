"""Script tests for ``docs/fleet/scripts/fleet_update.py``, the fleet's pinned-version updater."""

from __future__ import annotations

import dataclasses
import getpass
import json
import os
import plistlib
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, fleet_setup, fleet_stop, fleet_update
from docs.fleet.scripts.setup.ubuntu import personal

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

PINS = fleet_setup.load_versions()
#: The real ``subprocess.run`` and ``Popen``, for the tests that run ``bash`` on purpose
#: (:func:`_real_processes`; the autouse fixture refuses every other process).
_REAL_RUN = subprocess.run
_REAL_POPEN = subprocess.Popen
#: ``json.loads`` and ``plistlib.loads``, their results typed ``object`` for the test to narrow.
_loads: Callable[[str], object] = json.loads
_plist: Callable[[bytes], object] = plistlib.loads
#: Where each binary-probed tool lives under the home folder.
BINARIES = {
    "claude": ".local/bin/claude",
    "uv": ".local/bin/uv",
    "pre-commit": ".local/bin/pre-commit",
    "osv-scanner": ".local/bin/osv-scanner",
    "opencode": ".opencode/bin/opencode",
    "muse": ".local/bin/muse",
    "grok": ".grok/bin/grok",
    "agy": ".local/bin/agy",
}
#: What each tool's ``--version`` prints, around the version.
SHAPES = {
    "claude": "{} (Claude Code)",
    "uv": "uv {} (316c827e0 2026-11-03 aarch64-apple-darwin)",
    "pre-commit": "pre-commit {}",
    "osv-scanner": "osv-scanner version: {}",
    "opencode": "opencode v{}",
    "muse": "Muse Code {} (1.4.15-R8339.1)",
    "grok": "grok {} (f50904eaee6c) [stable]",
    "agy": "{}",
}
#: An install line's marker and the tool it installs.
INSTALLS = (
    ("nvm-sh/nvm/", "nvm"),
    ("nvm install ", "node"),
    ("npm install -g npm@", "npm"),
    ("npm install -g @openai/codex@", "codex"),
    ("claude.ai/install.sh", "claude"),
    ("astral.sh/uv/", "uv"),
    ("pre-commit==", "pre-commit"),
    ("osv-scanner_", "osv-scanner"),
    (fleet_setup.OPENCODE_INSTALLER, "opencode"),
    *((url, key) for key, url in fleet_setup.VENDOR_INSTALLERS.items()),
    ("strawberry-graphql/strawberry-django/archive/", "strawberry-django"),
    ("git clone --quiet --branch", "django-graphene-filters"),
    ("uv sync --frozen", "graphene-django"),
)
#: A strawberry-django tree whose ``pyproject.toml`` names no version.
NO_RELEASE = "no-release"
AT_PINS = {
    key: (version if version != fleet_update.LATEST else "1.0.0") for key, version in PINS.items()
}


def _bare(version: str) -> str:
    return version.removeprefix("v")


class Box:
    """A fake fleet machine: tool versions, the commands it was asked to run, its answers."""

    def __init__(
        self,
        home: Path,
        versions: Mapping[str, str],
        system: str,
    ) -> None:
        """Make the box in ``home`` with ``versions`` installed."""
        self.home = home
        self.versions = {key: _bare(value) for key, value in versions.items()}
        self.calls: list[list[str]] = []
        self.scripts: list[str] = []
        self.sudo: Callable[[list[str]], fleet_update.Ran] = lambda _argv: fleet_update.Ran(
            0,
            "ok\n",
            "",
        )
        self.after_install: Callable[[str], None] = lambda _key: None
        self.fail_install: set[str] = set()
        self.filters_changes = ""
        #: ``ps -A -o pid=,ppid=,args=``'s lines, ``lsof``'s answer, the apt packages
        #: installed and held, each cask's latest version and ``brew outdated``'s names.
        self.ps = ""
        self.lsof = ""
        self.debs: set[str] = set()
        self.holds: set[str] = set()
        self.casks: dict[str, str] = {}
        self.outdated = "glab\nfirefox\n"
        self.alias = f"v{self.versions['node']}" if self.versions.get("node") else ""
        self.host = fleet_update.Host(
            fleet_setup.Box(home=home, user="someone", repo=home / "checkout", system=system),
            "x86_64",
            home / "checkout",
        )
        (home / "checkout").mkdir()
        self.sync()

    def sync(self) -> None:
        """Make the files a probe looks for match :attr:`versions`."""
        for key, relative in BINARIES.items():
            path = self.home / relative
            if self.versions.get(key):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            else:
                path.unlink(missing_ok=True)
        if self.versions.get("node"):
            (self.home / ".nvm" / "versions" / "node" / f"v{self.versions['node']}" / "bin").mkdir(
                parents=True,
                exist_ok=True,
            )
        self.sync_references()
        alias = self.home / ".nvm" / "alias" / "default"
        alias.parent.mkdir(parents=True, exist_ok=True)
        _ = alias.write_text(self.alias)

    def sync_references(self) -> None:
        """Make the reference trees a probe reads match :attr:`versions`."""
        projects = self.home / fleet_setup.PROJECTS
        tree = projects / fleet_setup.STRAWBERRY_DJANGO_DIR
        version = self.versions.get("strawberry-django")
        if version:
            tree.mkdir(parents=True, exist_ok=True)
            line = "" if version == NO_RELEASE else f'version = "{version}"\n'
            _ = (tree / "pyproject.toml").write_text(f"[project]\n{line}")
        elif tree.exists():
            shutil.rmtree(tree)
        clone = projects / fleet_setup.FILTERS_DIR
        if self.versions.get("django-graphene-filters"):
            clone.mkdir(parents=True, exist_ok=True)
        lib = clone / ".venv" / "lib" / "python3.14" / "site-packages"
        if lib.exists():
            shutil.rmtree(lib)
        graphene = self.versions.get("graphene-django")
        if graphene:
            (lib / f"graphene_django-{graphene}.dist-info").mkdir(parents=True)

    def git(self, argv: list[str]) -> fleet_update.Ran:
        """Answer a ``git`` read of the django-graphene-filters clone (a fake history).

        Its ``HEAD`` is ``head-<version>``; a version ``<pin>-<n>-g<sha>`` is past the tag.
        """
        assert argv[:4] == [
            "git",
            "--no-optional-locks",
            "-C",
            argv[3],
        ]
        args = argv[4:]
        version = self.versions.get("django-graphene-filters", "")
        tag = _bare(PINS["django-graphene-filters"])
        answers: dict[tuple[str, ...], str] = {
            ("rev-parse", "--show-toplevel"): argv[3],
            ("config", "--get", "remote.origin.url"): fleet_setup.FILTERS_URL,
            (
                "rev-parse",
                "--verify",
                "--quiet",
                "HEAD",
            ): f"head-{version}",
            ("status", "--porcelain"): self.filters_changes,
            ("describe", "--tags", "--always"): f"v{version}",
        }
        if tuple(args) in answers:
            return fleet_update.Ran(0, answers[tuple(args)] + "\n", "")
        if args[:3] == ["rev-parse", "--verify", "--quiet"]:
            return fleet_update.Ran(0, f"head-{tag}\n", "")
        if args[:2] == ["merge-base", "--is-ancestor"]:
            past = version.startswith(f"{tag}-")
            ancestor = args[2:] == [f"head-{tag}", f"head-{version}"] and past
            return fleet_update.Ran(0 if ancestor else 1, "", "")
        msg = f"unexpected git command {argv}"
        raise AssertionError(msg)

    def install(self, script: str) -> fleet_update.Ran:
        for marker, key in INSTALLS:
            if marker not in script:
                continue
            if key in self.fail_install:
                return fleet_update.Ran(1, "", f"{key}: download failed")
            pin = PINS[key]
            self.versions[key] = _bare(pin) if pin != fleet_update.LATEST else "1.0.1"
            self.after_install(key)
        if "nvm alias default" in script:
            self.alias = script.rsplit("nvm alias default ", 1)[1].split(maxsplit=1)[0]
        self.sync()
        return fleet_update.Ran(0, "installed\n", "")

    def fleet_path(self) -> str:
        """Stand in for the PATH block (``test_the_fleet_path_*`` runs the real one).

        The newest nvm node's ``bin``, ``~/.local/bin``, then the system folders.
        """
        nodes = sorted(
            (self.home / ".nvm" / "versions" / "node").glob("v*/bin"),
            key=lambda folder: fleet_update.numbers(folder.parent.name),
        )
        return os.pathsep.join(
            [*(str(folder) for folder in nodes[-1:]), str(self.home / ".local" / "bin"), "/bin"],
        )

    def answer(self, argv: list[str]) -> fleet_update.Ran:
        if argv[:2] == ["bash", "-c"]:
            return self.bash(argv[2])
        if argv[0] == "git":
            return self.git(argv)
        if argv[:3] == ["bash", "--noprofile", "--norc"]:
            return fleet_update.Ran(0, self.fleet_path(), "")
        name = Path(argv[0]).name
        if argv[0] == "sudo":
            return self.sudo_and_hold(argv)
        if argv[:2] == ["ps", "-A"]:
            return fleet_update.Ran(0, self.ps, "")
        if argv[0] == "/usr/sbin/lsof":
            return fleet_update.Ran(0, self.lsof, "")
        if argv[0] == "dpkg-query":
            found = [f"{name} ii \n" for name in argv[4:] if name in self.debs]
            return fleet_update.Ran(0 if len(found) == len(argv[4:]) else 1, "".join(found), "")
        if argv == ["apt-mark", "showhold"]:
            return fleet_update.Ran(0, "".join(f"{name}\n" for name in sorted(self.holds)), "")
        if name == "brew" and argv[1:4] == ["info", "--cask", "--json=v2"]:
            known = [token for token in argv[4:] if token in self.casks]
            casks = [{"token": token, "version": f"{self.casks[token]},abc"} for token in known]
            code = 0 if len(known) == len(argv[4:]) else 1
            return fleet_update.Ran(
                code,
                json.dumps({"casks": casks}),
                "" if code == 0 else "Error: no cask",
            )
        if argv[-1] == "--version":
            key = next(key for key, relative in BINARIES.items() if argv[0].endswith(relative))
            return fleet_update.Ran(0, SHAPES[key].format(self.versions[key]) + "\n", "")
        if argv[:3] == ["apt", "list", "--upgradable"]:
            return fleet_update.Ran(
                0,
                "Listing...\ngit/noble 1:2.51 amd64 [upgradable from: 1:2.50]\n",
                "",
            )
        if argv[:3] == ["snap", "refresh", "--list"]:
            return fleet_update.Ran(0, "", "All snaps up to date.\n")
        if name == "brew":
            return fleet_update.Ran(0, self.outdated if "outdated" in argv else "done\n", "")
        if name == "softwareupdate":
            return fleet_update.Ran(
                0,
                "Software Update found:\n* Label: macOS 27.2.1-26B131\n",
                "",
            )
        msg = f"unexpected command {argv}"
        raise AssertionError(msg)

    def sudo_and_hold(self, argv: list[str]) -> fleet_update.Ran:
        """Answer a ``sudo`` call, tracking what ``apt-mark`` holds."""
        ran = self.sudo(argv)
        if ran.code == 0 and argv[2:4] == [fleet_update.APT_MARK, "hold"]:
            self.holds.add(argv[4])
        if ran.code == 0 and argv[2:4] == [fleet_update.APT_MARK, "unhold"]:
            self.holds.discard(argv[4])
        return ran

    def bash(self, script: str) -> fleet_update.Ran:
        if "nvm alias default" in script or any(marker in script for marker, _key in INSTALLS):
            self.scripts.append(script)
            return self.install(script)
        if script.endswith("nvm --version"):
            return self._version("nvm")
        if script.endswith("nvm version default"):
            node = self.versions.get("node")
            return (
                fleet_update.Ran(0, f"v{node}\n", "") if node else fleet_update.Ran(3, "N/A\n", "")
            )
        if script.endswith("npm --version"):
            return self._version("npm")
        if script.endswith("npm ls -g --depth=0 --json"):
            codex = self.versions.get("codex")
            listed = {"@openai/codex": {"version": codex}} if codex else {}
            return fleet_update.Ran(0, json.dumps({"dependencies": listed}), "")
        msg = f"unexpected bash script {script!r}"
        raise AssertionError(msg)

    def _version(self, key: str) -> fleet_update.Ran:
        found = self.versions.get(key)
        return (
            fleet_update.Ran(0, f"{found}\n", "")
            if found
            else fleet_update.Ran(127, "", "not found")
        )


@pytest.fixture(autouse=True)
def _no_real_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """No test starts a real process: every command goes through a fake ``run``."""

    def refuse(*args: object, **_kwargs: object) -> object:
        msg = f"a real subprocess was started: {args!r}"
        raise AssertionError(msg)

    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(subprocess, "Popen", refuse)
    monkeypatch.setenv(fleet.MACHINE_ENV, "rio-ubu")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")


def _box(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    versions: Mapping[str, str] | None = None,
    system: str = fleet_setup.LINUX,
) -> Box:
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("PATH", str(tmp_path / "no-tools"))
    box = Box(home, AT_PINS if versions is None else versions, system)

    def fake(
        argv: Sequence[str],
        *,
        timeout: float,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> fleet_update.Ran:
        del timeout, env, cwd
        box.calls.append(list(argv))
        return box.answer(list(argv))

    monkeypatch.setattr(fleet_update, "run", fake)
    return box


def _homebrew(_host: fleet_update.Host) -> str:
    return "/opt/homebrew/bin/brew"


def _here(monkeypatch: pytest.MonkeyPatch, box: Box) -> None:
    def here(_cls: type[fleet_update.Host]) -> fleet_update.Host:
        return box.host

    monkeypatch.setattr(fleet_update.Host, "here", classmethod(here))


def _local(action: str, name: str) -> fleet_update.Report:
    return fleet_update.Report(name, (fleet_update.Row(action, "", "", "ok"),))


def _rows(rows: Sequence[fleet_update.Row]) -> dict[str, fleet_update.Row]:
    return {row.item: row for row in rows}


# -- the pins ------------------------------------------------------------------------------


def test_the_pins_name_exactly_the_tools_and_only_vendor_tools_read_latest() -> None:
    assert fleet_update.pins() == PINS
    assert list(PINS) == [tool.key for tool in fleet_update.TOOLS]
    latest = {key for key, version in PINS.items() if version == fleet_update.LATEST}
    assert latest == set(fleet_setup.VENDOR_INSTALLERS) == {"muse", "grok", "agy"}


def test_osv_scanner_is_pinned_in_the_versions_file_not_in_personal() -> None:
    source = Path(personal.__file__).read_text(encoding="utf-8")
    assert "OSV_VERSION" not in source
    step = next(step for step in personal.STEPS if step.key == "osv-scanner")
    lines = step.lines(personal.Box(home=Path("/h"), user="u", facts={}))
    assert f"/{PINS['osv-scanner']}/osv-scanner_linux_amd64" in lines[-1]


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"node": None}, "no pin for node"),
        ({"rustc": "1.0.0"}, "rustc is no tool"),
        ({"grok": "1.0.70"}, "grok has no versioned installer"),
        ({"uv": "latest"}, "uv needs an exact release"),
        ({"uv": "0.13.7; true"}, "neither 'latest' nor an exact release"),
        ({"node": "v26.13.1 && true"}, "neither 'latest' nor an exact release"),
        ({"codex": "0.167"}, None),
        ({"codex": "0.167.2-alpha"}, "neither 'latest' nor an exact release"),
    ],
)
def test_a_versions_file_out_of_step_with_the_tools_is_refused(
    tmp_path: Path,
    change: Mapping[str, str | None],
    problem: str | None,
) -> None:
    pinned: dict[str, str | None] = {**PINS, **change}
    path = tmp_path / "versions.json"
    _ = path.write_text(
        json.dumps({"versions": {k: v for k, v in pinned.items() if v is not None}}),
    )
    if problem is None:
        assert fleet_update.pins(path)[next(iter(change))] == next(iter(change.values()))
        return
    with pytest.raises(fleet_update.UpdateError, match=problem):
        _ = fleet_update.pins(path)


def test_an_unreadable_versions_file_is_exit_2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    broken = tmp_path / "versions.json"
    _ = broken.write_text("{")
    monkeypatch.setattr(fleet_setup, "VERSIONS_FILE", broken)
    assert fleet_update.main(["check"]) == 2
    assert "cannot read the pins" in capsys.readouterr().err


@pytest.mark.parametrize(
    (
        "pin",
        "installed",
        "updater",
        "status",
    ),
    [
        (
            "v26.13.1",
            "26.13.1",
            "",
            "ok",
        ),
        (
            "v26.13.1",
            "24.22.2",
            "",
            "behind",
        ),
        (
            "12.2.2",
            "12.10.0",
            "",
            "differs",
        ),
        (
            "2.1.322",
            "2.1.330",
            "own",
            "ahead",
        ),
        (
            "2.1.322",
            "2.1.318",
            "own",
            "behind",
        ),
        (
            "0.167.2",
            "",
            "",
            "missing",
        ),
        (
            "latest",
            "2.2.5",
            "",
            "latest",
        ),
    ],
)
def test_compare_reads_versions_as_numbers(
    pin: str,
    installed: str,
    updater: str,
    status: str,
) -> None:
    assert fleet_update.compare(pin, installed, self_updating=updater == "own") == status


@pytest.mark.parametrize(
    ("output", "version"),
    [
        ("codex-cli 0.166.0", "0.166.0"),
        ("Muse Code 1.4.15 (1.4.15-R8339.1)", "1.4.15"),
        ("osv-scanner version: 2.7.0", "2.7.0"),
        ("v24.22.2", "24.22.2"),
        ("N/A", ""),
    ],
)
def test_version_of_takes_the_first_dotted_version(output: str, version: str) -> None:
    assert fleet_update.version_of(output) == version


# -- check ---------------------------------------------------------------------------------


def test_check_reports_each_tool_against_its_pin_and_only_reads(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(
        tmp_path,
        monkeypatch,
        {
            **AT_PINS,
            "node": "v24.22.2",
            "codex": "",
            "claude": "2.1.400",
        },
    )
    rows = _rows(fleet_update.check(box.host, PINS))
    assert rows["node"].status == "behind"
    assert rows["codex"].status == "missing"
    assert rows["claude"].status == "ahead"
    assert rows["uv"].status == "ok"
    assert rows["muse"].status == "latest"
    assert (rows["apt"].installed, rows["apt"].status, rows["apt"].detail) == (
        "1",
        "pending",
        "git",
    )
    assert rows["snap"].status == "ok"
    assert box.scripts == []
    assert not any(call[0] == "sudo" for call in box.calls)


def test_nvm_is_sourced_in_bash_and_npm_runs_under_the_default_node(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    _ = fleet_update.check(box.host, PINS)
    scripts = [call[2] for call in box.calls if call[:2] == ["bash", "-c"]]
    assert scripts
    assert all(script.startswith('. "$NVM_DIR/nvm.sh" --no-use && ') for script in scripts)
    npm = [script for script in scripts if "npm " in script]
    assert npm
    assert all("nvm use --silent default >/dev/null && npm" in script for script in npm)


def test_node_at_the_pin_under_another_default_alias_is_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.alias = "lts/*"
    box.sync()
    node = _rows(fleet_update.check(box.host, PINS))["node"]
    assert (node.status, node.detail) == (
        "drift",
        f"nvm's default alias is lts/*, not {PINS['node']}",
    )


def test_a_newer_node_than_the_default_is_a_shadow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    (box.home / ".nvm" / "versions" / "node" / "v99.0.0" / "bin").mkdir(parents=True)
    row = _rows(fleet_update.check(box.host, PINS))["node shadow"]
    assert row.status == "shadowed"
    assert "nvm uninstall v99.0.0" in row.detail


def _executable(path: Path, target: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if target is None:
        _ = path.write_text("#!/bin/sh\n")
        path.chmod(0o755)
    else:
        path.symlink_to(target)
    return path


def test_another_codex_on_path_is_named_with_the_command_that_removes_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    home = box.home
    node_bin = home / ".nvm" / "versions" / "node" / f"v{_bare(PINS['node'])}" / "bin"
    _ = _executable(node_bin / "codex")
    script = _executable(
        home / ".local" / "lib" / "node_modules" / "@openai" / "codex" / "bin" / "codex.js",
    )
    _ = _executable(home / ".local" / "bin" / "codex", script)
    _ = _executable(home / "other" / "codex")
    search = os.pathsep.join(
        [
            str(node_bin),
            str(home / ".local" / "bin"),
            str(home / ".local" / "bin"),
            str(home / "other"),
        ],
    )
    rows = fleet_update.codex_shadows(box.host, _bare(PINS["node"]), search)
    assert [row.installed for row in rows] == ["~/.local/bin/codex", "~/other/codex"]
    assert all(row.status == "shadowed" for row in rows)
    assert rows[0].detail.endswith(
        fleet_update.by_hand('npm uninstall -g --prefix "$HOME"/.local @openai/codex'),
    )
    assert "nvm use --silent default" in rows[0].detail
    assert rows[1].detail.endswith('rm "$HOME"/other/codex')
    assert (home / ".local" / "bin" / "codex").is_symlink()
    assert (home / "other" / "codex").is_file()


def test_nvms_own_codex_alone_is_no_shadow(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    node_bin = box.home / ".nvm" / "versions" / "node" / f"v{_bare(PINS['node'])}" / "bin"
    _ = _executable(node_bin / "codex")
    assert fleet_update.codex_shadows(box.host, _bare(PINS["node"]), str(node_bin)) == []


def test_macos_check_lists_brew_with_casks_and_system_updates_without_auto_update(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, system=fleet_setup.MACOS)
    seen: list[Mapping[str, str] | None] = []
    answer = fleet_update.run

    def spy(
        argv: Sequence[str],
        *,
        timeout: float,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> fleet_update.Ran:
        if Path(argv[0]).name == "brew":
            seen.append(env)
        return answer(argv, timeout=timeout, env=env, cwd=cwd)

    monkeypatch.setattr(fleet_update, "run", spy)
    monkeypatch.setattr(fleet_update, "brew", _homebrew)
    rows = _rows(fleet_update.check(box.host, PINS))
    assert (rows["brew"].installed, rows["brew"].detail) == ("2", "glab, firefox")
    assert (rows["macos"].status, rows["macos"].detail) == ("pending", "macOS 27.2.1-26B131")
    assert [
        "/opt/homebrew/bin/brew",
        "outdated",
        "--greedy",
        "--quiet",
    ] in box.calls
    assert ["/usr/sbin/softwareupdate", "-l"] in box.calls
    assert seen
    assert all(env is not None and env["HOMEBREW_NO_AUTO_UPDATE"] == "1" for env in seen)


def test_check_exits_1_on_drift_and_0_at_the_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    box = _box(tmp_path, monkeypatch)
    _here(monkeypatch, box)
    assert fleet_update.main(["check"]) == 0
    box.versions["uv"] = "0.1.0"
    assert fleet_update.main(["check"]) == 1
    assert "0.1.0" in capsys.readouterr().out


def test_check_json_is_one_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    box = _box(tmp_path, monkeypatch)
    _here(monkeypatch, box)
    assert fleet_update.main(["check", "--json"]) == 0
    document = _loads(capsys.readouterr().out)
    assert fleet.is_json_object(document)
    rows = document["rows"]
    assert document["machine"] == "rio-ubu"
    assert fleet.is_json_array(rows)
    assert [row["item"] for row in rows if fleet.is_json_object(row)][: len(PINS)] == list(PINS)


# -- apply ---------------------------------------------------------------------------------


def test_apply_installs_only_what_is_off_its_pin_and_reads_each_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "npm": "11.19.1", "osv-scanner": "v2.7.0"})
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert (rows["npm"].status, rows["npm"].installed, rows["npm"].detail) == (
        "updated",
        "12.2.2",
        "from 11.19.1",
    )
    assert rows["osv-scanner"].status == "updated"
    assert rows["uv"].status == "ok"
    pinned = [
        script
        for script in box.scripts
        if not any(url in script for url in fleet_setup.VENDOR_INSTALLERS.values())
    ]
    assert len(pinned) == 2
    assert fleet_setup.npm_global_lines("npm", PINS["npm"])[0] in pinned[0]
    assert f"/{PINS['osv-scanner']}/osv-scanner_linux_amd64" in pinned[1]


def test_apply_runs_each_latest_tools_installer_every_time(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    rows = _rows(fleet_update.apply(box.host, PINS))
    for key, url in fleet_setup.VENDOR_INSTALLERS.items():
        assert any(fleet_setup.vendor_lines(url)[0] in script for script in box.scripts)
        assert rows[key].status == "updated"


def test_apply_never_downgrades_claude_code_past_its_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "claude": "2.1.999"})
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert rows["claude"].status == "ahead"
    assert not any("claude.ai/install.sh" in script for script in box.scripts)


def test_apply_moves_an_uv_past_its_pin_back_to_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "uv": "0.99.0"})
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert (rows["uv"].status, rows["uv"].installed) == ("updated", PINS["uv"])
    assert any(
        f"astral.sh/uv/{PINS['uv']}/install.sh | UV_NO_MODIFY_PATH=1 sh" in script
        for script in box.scripts
    )


def test_a_new_node_carries_the_global_packages_over_and_becomes_the_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "node": "v24.22.2"})
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert rows["node"].status == "updated"
    script = next(script for script in box.scripts if "nvm install" in script)
    pin = PINS["node"]
    assert (
        f"nvm install {pin} --reinstall-packages-from=v24.22.2 && nvm alias default {pin}"
        in script
    )
    assert script.lstrip("( ").startswith('. "$NVM_DIR/nvm.sh" --no-use && ')
    assert box.alias == pin


def test_node_whose_alias_alone_drifted_gets_the_alias_and_no_install(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.alias = "lts/*"
    box.sync()
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert rows["node"].status == "updated"
    assert box.alias == PINS["node"]
    assert not any("nvm install" in script for script in box.scripts)


@pytest.mark.parametrize("mode", ["install-fails", "reads-back-wrong"])
def test_an_install_that_does_not_reach_the_pin_is_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    failing = mode == "install-fails"
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "pre-commit": "4.0.0"})
    if failing:
        box.fail_install.add("pre-commit")
    else:

        def undo(key: str) -> None:
            if key == "pre-commit":
                box.versions["pre-commit"] = "4.0.0"

        box.after_install = undo
    row = _rows(fleet_update.apply(box.host, PINS))["pre-commit"]
    assert row.status == "failed"
    assert row.detail == (
        "pre-commit: download failed" if failing else "still 4.0.0 after the install (behind)"
    )


def test_linux_apply_runs_exactly_the_three_sudo_commands_without_a_prompt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    rows = fleet_update.apply(box.host, PINS)
    sudo = [call for call in box.calls if call[0] == "sudo"]
    assert sudo == [
        [
            "sudo",
            "-n",
            "/usr/bin/apt-get",
            "update",
        ],
        [
            "sudo",
            "-n",
            "/usr/bin/apt-get",
            "upgrade",
            "-y",
        ],
        [
            "sudo",
            "-n",
            "/usr/bin/snap",
            "refresh",
        ],
    ]
    assert [row.status for row in rows[-3:]] == ["done", "done", "done"]


def test_a_refused_sudo_is_one_row_naming_the_missing_rule_and_ends_the_os_steps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.sudo = lambda _argv: fleet_update.Ran(1, "", "sudo: a password is required\n")
    rows = fleet_update.apply(box.host, PINS)
    assert [call for call in box.calls if call[0] == "sudo"] == [
        [
            "sudo",
            "-n",
            "/usr/bin/apt-get",
            "update",
        ],
    ]
    assert rows[-1] == fleet_update.Row("sudo", "", "", "refused", fleet_update.sudoers_hint())
    assert "fleet_update.py sudoers" in rows[-1].detail


def test_an_apt_failure_is_failed_and_the_next_os_step_still_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.sudo = lambda argv: (
        fleet_update.Ran(100, "", "E: Could not get lock\n")
        if argv[-1] == "update"
        else fleet_update.Ran(0, "", "")
    )
    rows = fleet_update.apply(box.host, PINS)
    assert [(row.item, row.status) for row in rows[-3:]] == [
        ("apt-get update", "failed"),
        ("apt-get upgrade -y", "done"),
        ("snap refresh", "done"),
    ]


def test_macos_apply_upgrades_brew_greedily_and_only_lists_system_updates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, system=fleet_setup.MACOS)
    monkeypatch.setattr(fleet_update, "brew", _homebrew)
    rows = fleet_update.apply(box.host, PINS)
    assert ["/opt/homebrew/bin/brew", "update"] in box.calls
    assert ["/opt/homebrew/bin/brew", "upgrade", "--greedy"] in box.calls
    updates = [call for call in box.calls if Path(call[0]).name == "softwareupdate"]
    assert updates == [["/usr/sbin/softwareupdate", "-l"]]
    assert not any(call[0] == "sudo" for call in box.calls)
    assert rows[-1].item == "macos"
    assert rows[-1].status == "report"


def test_apply_refuses_while_the_fleet_is_stopped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "uv": "0.1.0"})
    flag = box.host.root / fleet_stop.FLAG
    flag.parent.mkdir(parents=True)
    _ = flag.write_text(fleet_stop.flag_text("disk full", "rio-air"))
    rows = fleet_update.apply(box.host, PINS)
    assert rows == [
        fleet_update.Row("apply", "", "", "stopped", "the fleet is stopped: disk full"),
    ]
    assert box.calls == []


def test_a_stop_flag_set_mid_run_ends_apply_before_the_next_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "node": "v24.22.2", "uv": "0.1.0"})
    flag = box.host.root / fleet_stop.FLAG

    def stop(key: str) -> None:
        if key == "node":
            flag.parent.mkdir(parents=True, exist_ok=True)
            _ = flag.write_text("{}")

    box.after_install = stop
    rows = fleet_update.apply(box.host, PINS)
    assert [row.item for row in rows] == ["nvm", "node", "apply"]
    assert rows[-1].status == "stopped"
    assert not any("astral.sh" in script for script in box.scripts)
    assert not any(call[0] == "sudo" for call in box.calls)


def test_a_second_apply_on_the_machine_is_refused_by_the_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    with fleet_update.update_lock(box.host.root):
        rows = fleet_update.apply(box.host, PINS)
    assert [row.status for row in rows] == ["locked"]
    assert "locked" in fleet_update.TROUBLE
    assert "update.lock" in rows[0].detail
    assert box.calls == []
    assert (box.host.root / ".work" / fleet_update.LOCK).is_file()


def test_apply_prints_one_line_per_step_and_exits_1_on_trouble(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.sudo = lambda _argv: fleet_update.Ran(1, "", "sudo: a password is required\n")
    _here(monkeypatch, box)
    assert fleet_update.main(["apply"]) == 1
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("== fleet_update apply on rio-ubu at ")
    assert len(lines) == 1 + len(fleet_update.TOOLS) + 2
    assert lines[-1].startswith("sudo")
    assert "refused" in lines[-1]


# -- --all ---------------------------------------------------------------------------------


def _machine(name: str, repo: str = "~/projects/django-strawberry-framework") -> fleet.Machine:
    return fleet.Machine(name=name, ssh=name, os="linux", repo=repo, weights={}, floors={})


def test_a_peer_runs_its_own_checkouts_copy_with_json() -> None:
    command = fleet_update.remote_command(_machine("rio-bee"), "check")
    assert command == (
        'cd "$HOME"/projects/django-strawberry-framework || exit 3; py=.venv/bin/python; '
        '[ -x "$py" ] || py=python3; exec "$py" docs/fleet/scripts/fleet_update.py check --json'
    )
    with pytest.raises(fleet_update.UpdateError, match="unsafe repo"):
        _ = fleet_update.remote_command(_machine("x", "~/a b;rm"), "check")


@pytest.mark.parametrize(
    ("ran", "status", "detail"),
    [
        (
            fleet_update.Ran(255, "", "ssh: connect to host rio-bee: timed out\n"),
            "unreached",
            "ssh: connect to host rio-bee: timed out",
        ),
        (
            fleet_update.Ran(
                2,
                "",
                "python3: can't open file 'docs/fleet/scripts/fleet_update.py': "
                "[Errno 2] No such file or directory\n",
            ),
            "error",
            "its checkout has no docs/fleet/scripts/fleet_update.py yet (main not synced there)",
        ),
    ],
)
def test_a_peer_that_cannot_answer_is_one_row(
    ran: fleet_update.Ran,
    status: str,
    detail: str,
) -> None:
    report = fleet_update.parse_report("rio-bee", ran)
    assert report.rows == (fleet_update.Row(report.rows[0].item, "", "", status, detail),)


def test_every_machine_runs_at_once_this_one_in_process_the_rest_over_ssh(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    peers: list[list[str]] = []
    row = fleet_update.Row("uv", "0.13.7", "0.13.7", "ok")

    def fake(
        argv: Sequence[str],
        *,
        timeout: float,
        env: Mapping[str, str] | None = None,
        cwd: Path | None = None,
    ) -> fleet_update.Ran:
        del env, cwd
        peers.append(list(argv))
        assert timeout == fleet_update.REMOTE_TIMEOUT["check"]
        return fleet_update.Ran(1, json.dumps(fleet_update.Report("x", (row,)).as_json()), "")

    monkeypatch.setattr(fleet_update, "run", fake)
    monkeypatch.setattr(
        fleet_update,
        "local",
        _local,
    )
    listed = [_machine("rio-ubu"), _machine("rio-bee"), _machine("rio-air")]
    reports = fleet_update.run_all("check", listed)
    assert [report.machine for report in reports] == ["rio-ubu", "rio-bee", "rio-air"]
    assert reports[0].rows == (fleet_update.Row("check", "", "", "ok"),)
    assert reports[1].rows == (row,)
    assert sorted(argv[-2] for argv in peers) == ["rio-air", "rio-bee"]
    assert all(argv[: 1 + len(fleet.SSH_OPTIONS)] == ["ssh", *fleet.SSH_OPTIONS] for argv in peers)


def test_check_all_marks_a_latest_tool_behind_the_fleets_newest_as_drift() -> None:
    reports = [
        fleet_update.Report("a", (fleet_update.Row("grok", "latest", "1.0.77", "latest"),)),
        fleet_update.Report("b", (fleet_update.Row("grok", "latest", "1.0.70", "latest"),)),
    ]
    marked = fleet_update.latest_drift(reports)
    assert marked[0].rows[0].status == "latest"
    assert (marked[1].rows[0].status, marked[1].rows[0].detail) == (
        "drift",
        "the fleet's newest is 1.0.77",
    )


def test_check_all_prints_one_table_a_column_per_machine(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    reports = [
        fleet_update.Report("rio-ubu", (fleet_update.Row("uv", "0.13.7", "0.13.7", "ok"),)),
        fleet_update.Report("rio-air", (fleet_update.Row("uv", "0.13.7", "0.13.5", "behind"),)),
    ]

    def run_all(_action: str) -> list[fleet_update.Report]:
        return reports

    monkeypatch.setattr(fleet_update, "run_all", run_all)
    assert fleet_update.main(["check", "--all"]) == 1
    assert capsys.readouterr().out.splitlines() == [
        "item  pinned  rio-ubu  rio-air",
        "uv    0.13.7  0.13.7   0.13.5 behind",
    ]


# -- schedule ------------------------------------------------------------------------------


def test_the_schedule_line_checks_the_stop_flag_first_and_kills_a_long_run() -> None:
    line = fleet_update.schedule_line(Path("/r"), fleet_update.SCHEDULE_JITTER)
    stop = f"[ -e {fleet_stop.FLAG} ] && exit 0; "
    assert line.startswith(f"cd /r || exit 1; {stop}")
    assert line.count(stop) == 2
    assert line.index("sleep") < line.rindex(stop) < line.index("fleet_update.py apply")
    assert (
        f"alarm shift @ARGV; exec @ARGV or die' {fleet_update.SCHEDULE_TIME_LIMIT} /r/.venv/bin/python"
        in line
    )
    assert "sleep" not in fleet_update.schedule_line(Path("/r"))


def test_the_macos_schedule_is_a_daily_launchd_agent_logging_to_work(tmp_path: Path) -> None:
    files = fleet_update.schedule_files(tmp_path, Path("/r"), "darwin")
    [(path, text), _retry] = files.items()
    assert (
        path
        == tmp_path
        / "Library"
        / "LaunchAgents"
        / "com.django-strawberry-framework.fleet-update.plist"
    )
    agent = _plist(text.encode())
    assert fleet.is_json_object(agent)
    assert agent["StartCalendarInterval"] == {
        "Hour": fleet_update.SCHEDULE_HOUR,
        "Minute": fleet_update.SCHEDULE_MINUTE,
    }
    assert agent["ProgramArguments"] == [
        "/bin/sh",
        "-c",
        fleet_update.schedule_line(Path("/r"), fleet_update.SCHEDULE_JITTER),
    ]
    assert agent["StandardOutPath"] == "/r/.work/fleet-update.log"
    assert "StartInterval" not in agent
    assert fleet_update.schedule_commands(files, "darwin")[-1][:2] == ["launchctl", "bootstrap"]


def test_the_linux_schedule_is_a_persistent_daily_systemd_timer_with_jitter(
    tmp_path: Path,
) -> None:
    files = fleet_update.schedule_files(tmp_path, Path("/r"), "linux")
    service, timer = (
        files[tmp_path / ".config" / "systemd" / "user" / f"dsf-fleet-update.{kind}"]
        for kind in ("service", "timer")
    )
    assert (
        f"OnCalendar=*-*-* {fleet_update.SCHEDULE_HOUR:02d}:{fleet_update.SCHEDULE_MINUTE:02d}:00"
        in timer
    )
    assert "Persistent=true" in timer
    assert f"RandomizedDelaySec={fleet_update.SCHEDULE_JITTER}s" in timer
    assert f"TimeoutStartSec={fleet_update.SCHEDULE_TIME_LIMIT}" in service
    assert ">> /r/.work/fleet-update.log 2>&1" in service
    assert fleet_update.schedule_commands(files, "linux")[-1] == [
        "systemctl",
        "--user",
        "enable",
        "--now",
        "dsf-fleet-update.timer",
        "dsf-fleet-update-retry.timer",
    ]
    with pytest.raises(fleet_update.UpdateError, match="not win32"):
        _ = fleet_update.schedule_files(tmp_path, Path("/r"), "win32")


def test_schedule_prints_by_default_and_installs_only_when_asked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loaded: list[Sequence[Sequence[str]]] = []

    def home(_cls: type[Path]) -> Path:
        return tmp_path

    monkeypatch.setattr(Path, "home", classmethod(home))
    monkeypatch.setattr(fleet_update, "load_schedule", loaded.append)
    assert fleet_update.main(["schedule"]) == 0
    assert "# then:" in capsys.readouterr().out
    assert loaded == []
    assert not any(tmp_path.rglob("*"))
    assert fleet_update.main(["schedule", "--install"]) == 0
    files = fleet_update.schedule_files(tmp_path)
    assert all(path.read_text() == text for path, text in files.items())
    assert loaded == [fleet_update.schedule_commands(files)]


# -- sudoers -------------------------------------------------------------------------------


def test_the_sudoers_drop_in_allows_exactly_the_three_commands_and_names_no_user() -> None:
    text = fleet_update.SUDOERS_FILE.read_text()
    rules = [line for line in text.splitlines() if line and not line.startswith("#")]
    assert rules == [
        "@USER@ ALL=(root) NOPASSWD: "
        + ", ".join(" ".join(argv) for argv in fleet_update.SUDO_COMMANDS),
        "@USER@ ALL=(root) NOPASSWD: @APT_MARK@",
    ]
    assert fleet_update.SUDOERS_FILE.parent == fleet_setup.PATH_BLOCK_FILE.parent


def test_sudoers_renders_the_account_and_refuses_an_odd_one() -> None:
    assert (
        fleet_update.sudoers_text("rio")
        .splitlines()[-1]
        .startswith("rio ALL=(root) NOPASSWD: /usr/bin/apt-get update,")
    )
    assert "@" not in fleet_update.sudoers_text("rio", fleet_update.apps())
    with pytest.raises(fleet_update.UpdateError, match="refusing"):
        _ = fleet_update.sudoers_text("root ALL=(ALL) ALL #")


def test_the_install_command_validates_with_visudo_before_the_rule_goes_live() -> None:
    command = fleet_update.sudoers_command("rio ALL=(root) NOPASSWD: /usr/bin/snap refresh\n")
    staged = "/etc/sudoers.d/.dsf-fleet-update.new"
    assert f'sudo install -o root -g root -m 0440 "$t" {staged}' in command
    assert command.index(f"sudo visudo -cf {staged}") < command.index(
        f"sudo mv {staged} /etc/sudoers.d/dsf-fleet-update",
    )
    assert f"&& sudo visudo -cf {staged} && sudo mv" in command
    assert command.rstrip().endswith('echo "installed /etc/sudoers.d/dsf-fleet-update"')
    assert f"sudo rm -f {staged}" in command


def test_sudoers_prints_the_rule_and_the_command(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(getpass, "getuser", lambda: "rio")
    assert fleet_update.main(["sudoers"]) == 0
    out = capsys.readouterr().out
    text = fleet_update.sudoers_text("rio", fleet_update.apps())
    assert text in out
    assert "/usr/bin/apt-mark hold claude-desktop" in text
    assert fleet_update.sudoers_command(text) in out


# -- fleet_setup -----------------------------------------------------------------------------


def test_setup_installs_the_pins_with_the_same_line_builders() -> None:
    box = fleet_setup.Box(home=Path("/h"), user="u", repo=Path("/h/r"), system=fleet_setup.LINUX)
    steps = {step.key: step.lines(box) for step in fleet_setup.STEPS}
    assert steps["node"] == [
        *fleet_setup.nvm_lines(PINS["nvm"]),
        *fleet_setup.node_lines(PINS["node"]),
    ]
    assert steps["codex"] == fleet_setup.npm_global_lines("@openai/codex", PINS["codex"])
    assert steps["claude"] == fleet_setup.claude_lines(PINS["claude"])
    assert steps["uv"] == fleet_setup.uv_lines(PINS["uv"])
    assert steps["pre-commit"] == fleet_setup.pre_commit_lines(PINS["pre-commit"])
    assert (fleet_setup.VERSIONS_FILE, "setup/versions.json") in fleet_setup.PUSHED


def test_verify_runs_the_boxs_own_update_check(monkeypatch: pytest.MonkeyPatch) -> None:
    asked: list[tuple[str | None, str]] = []

    def on(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        asked.append((host, command))
        return (1, "drift") if "fleet_update.py check" in command else (0, "")

    monkeypatch.setattr(fleet_setup, "on", on)

    def check_tools(_host: str) -> int:
        return 0

    monkeypatch.setattr(fleet_setup, "check_tools", check_tools)
    assert fleet_setup.verify("rio-bee") == 1
    assert (
        "rio-bee",
        f"cd {fleet_setup.REPO} && .venv/bin/python {fleet_update.SCRIPT} check",
    ) in asked


def test_an_nvm_update_leaves_the_shell_files_alone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "nvm": "v0.40.3"})
    row = _rows(fleet_update.apply(box.host, PINS))["nvm"]
    assert (row.status, row.installed) == ("updated", _bare(PINS["nvm"]))
    script = next(script for script in box.scripts if "nvm-sh/nvm/" in script)
    assert f"nvm-sh/nvm/{PINS['nvm']}/install.sh | PROFILE=/dev/null bash" in script


# -- the default node, whatever node the caller's PATH holds ------------------------------

#: An ``nvm.sh`` keeping nvm's rule that matters here: sourced without ``--no-use`` it switches
#: to the default (when there is one) only while no nvm node is on ``PATH`` yet; ``nvm use``
#: puts the default's ``bin`` first and exports ``NVM_BIN``, and fails while there is no
#: default alias.
FAKE_NVM = r"""
nvm() {
  case "$1" in
    use)
      [ -f "$NVM_DIR/alias/default" ] || return 3
      NVM_BIN="$NVM_DIR/versions/node/$(cat "$NVM_DIR/alias/default")/bin"
      PATH="$NVM_BIN:$PATH"
      export NVM_BIN PATH ;;
    install) mkdir -p "$NVM_DIR/versions/node/$2/bin" ;;
    alias) mkdir -p "$NVM_DIR/alias" && printf '%s' "$3" > "$NVM_DIR/alias/default" ;;
  esac
}
if [ "${1-}" != "--no-use" ] && [ -f "$NVM_DIR/alias/default" ]; then
  case ":$PATH:" in *":$NVM_DIR/versions/node/"*) ;; *) nvm use --silent default ;; esac
fi
"""
OLD_NODE = "v24.22.2"
NEW_NODE = "v26.13.1"


def _real_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let this test start real processes (``bash`` on files under its own folder)."""
    monkeypatch.setattr(subprocess, "run", _REAL_RUN)
    monkeypatch.setattr(subprocess, "Popen", _REAL_POPEN)


def _nvm_home(home: Path, default: str | None) -> dict[str, Path]:
    """Make ``home/.nvm`` with the old and the new node, each with an ``npm`` naming itself."""
    nvm_dir = home / ".nvm"
    nvm_dir.mkdir(parents=True)
    _ = (nvm_dir / "nvm.sh").write_text(FAKE_NVM)
    bins: dict[str, Path] = {}
    for version in (OLD_NODE, NEW_NODE):
        bins[version] = nvm_dir / "versions" / "node" / version / "bin"
        npm = bins[version] / "npm"
        npm.parent.mkdir(parents=True)
        _ = npm.write_text('#!/bin/sh\necho "$0 $*"\n')
        npm.chmod(0o755)
    if default is not None:
        (nvm_dir / "alias").mkdir()
        _ = (nvm_dir / "alias" / "default").write_text(default)
    return bins


def _bash(line: str, home: Path, path: str) -> subprocess.CompletedProcess[str]:
    env = {"HOME": str(home), "NVM_DIR": str(home / ".nvm"), "PATH": path}
    return _REAL_RUN(
        ["bash", "-c", line],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def test_a_global_npm_install_runs_under_the_default_node_whatever_node_path_holds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _real_processes(monkeypatch)
    bins = _nvm_home(tmp_path, NEW_NODE)
    # The apply process's PATH: the old node first, from the PATH block read before the new existed.
    stale = f"{bins[OLD_NODE]}:/usr/bin:/bin"
    for package, pin in (("npm", PINS["npm"]), ("@openai/codex", PINS["codex"])):
        ran = _bash(fleet_setup.npm_global_lines(package, pin)[0], tmp_path, stale)
        assert ran.returncode == 0, ran.stderr
        assert ran.stdout == f"{bins[NEW_NODE] / 'npm'} install -g {package}@{pin}\n"


def test_a_fresh_box_installs_node_without_a_default_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _real_processes(monkeypatch)
    _ = _nvm_home(tmp_path, None)
    ran = _bash(fleet_setup.node_lines(PINS["node"])[0], tmp_path, "/usr/bin:/bin")
    assert ran.returncode == 0, ran.stderr
    assert (tmp_path / ".nvm" / "alias" / "default").read_text() == PINS["node"]


def test_setups_codex_check_looks_under_the_default_node_not_the_callers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _real_processes(monkeypatch)
    bins = _nvm_home(tmp_path, NEW_NODE)
    _ = _executable(bins[OLD_NODE] / "codex")
    monkeypatch.setenv("PATH", f"{bins[OLD_NODE]}:/usr/bin:/bin")
    box = fleet_setup.Box(home=tmp_path, user="u", repo=tmp_path / "r", system=fleet_setup.LINUX)
    assert fleet_setup._check_codex(box) == "codex"
    _ = _executable(bins[NEW_NODE] / "codex")
    assert fleet_setup._check_codex(box) is None


# -- shadows read the fleet PATH, never the caller's ---------------------------------------

#: The ``PATH`` launchd gives the daily timer.
TIMER_PATH = "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def _fleet_home(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[fleet_update.Host, dict[str, Path]]:
    """A machine whose apply just made v26 the default while the old v24 is still on its PATH."""
    _real_processes(monkeypatch)
    home = tmp_path / "home"
    bins = _nvm_home(home, NEW_NODE)
    (home / ".local" / "bin").mkdir(parents=True)
    host = fleet_update.Host(
        fleet_setup.Box(home=home, user="u", repo=home / "checkout", system=fleet_setup.LINUX),
        "x86_64",
        home / "checkout",
    )
    return host, bins


def _in_home(rows: Sequence[fleet_update.Row]) -> list[tuple[str, str]]:
    """The rows naming a file under the test's home (a real machine's own folders aside)."""
    return [(row.item, row.installed) for row in rows if row.installed.startswith("~")]


def test_the_fleet_path_is_the_block_over_the_system_path_whoever_asks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host, bins = _fleet_home(tmp_path, monkeypatch)
    seen: set[str] = set()
    for caller in (f"{bins[OLD_NODE]}:/usr/bin:/bin", TIMER_PATH, "/usr/bin:/bin"):
        monkeypatch.setenv("PATH", caller)
        seen.add(fleet_update.fleet_path(host, _bare(NEW_NODE)))
    assert len(seen) == 1
    folders = next(iter(seen)).split(os.pathsep)
    assert folders[0] == str(bins[NEW_NODE])
    assert str(host.box.home / ".local" / "bin") in folders
    assert str(bins[OLD_NODE]) not in folders
    assert set(fleet_update.BASE_PATH.split(os.pathsep)) <= set(folders)
    # A default older than the newest node still leads; the block's newest follows it.
    older = fleet_update.fleet_path(host, _bare(OLD_NODE)).split(os.pathsep)
    assert older[0] == str(bins[OLD_NODE])
    assert str(bins[NEW_NODE]) in older[1:]


def test_shadows_read_the_fleet_path_not_the_callers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host, bins = _fleet_home(tmp_path, monkeypatch)
    home = host.box.home
    _ = _executable(bins[OLD_NODE] / "codex")  # the old node's: on the stale PATH only
    _ = _executable(bins[NEW_NODE] / "codex")  # nvm's own
    _ = _executable(home / ".local" / "bin" / "codex")  # a real shadow, off the timer's PATH
    wanted = [("codex shadow", "~/.local/bin/codex")]
    for caller in (f"{bins[OLD_NODE]}:/usr/bin:/bin", TIMER_PATH):
        monkeypatch.setenv("PATH", caller)
        assert _in_home(fleet_update.shadows(host, _bare(NEW_NODE))) == wanted
    newest = home / ".nvm" / "versions" / "node" / "v99.0.0" / "bin"
    newest.mkdir(parents=True)
    rows = fleet_update.shadows(host, _bare(NEW_NODE))
    assert _in_home(rows) == [("node shadow", "~/.nvm/versions/node/v99.0.0"), *wanted]
    assert fleet_update.by_hand("nvm uninstall v99.0.0") in rows[0].detail


def test_an_unread_fleet_path_is_an_error_not_a_clean_bill(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    answer = box.answer

    def broken(argv: list[str]) -> fleet_update.Ran:
        if argv[:3] == ["bash", "--noprofile", "--norc"]:
            return fleet_update.Ran(2, "", "path.sh: syntax error")
        return answer(argv)

    monkeypatch.setattr(box, "answer", broken)
    row = _rows(fleet_update.check(box.host, PINS))["shadows"]
    assert (row.status, row.detail) == (
        "error",
        "cannot read the fleet PATH: path.sh: syntax error",
    )
    assert _rows(fleet_update.apply(box.host, PINS))["shadows"].status == "error"


# -- OpenCode 2, pinned --------------------------------------------------------------------


def test_opencode_1_is_brought_to_the_pinned_opencode_2_by_the_v2_installer(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert PINS["opencode"].startswith("2.")
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "opencode": "1.19.5"})
    assert _rows(fleet_update.check(box.host, PINS))["opencode"].status == "behind"
    row = _rows(fleet_update.apply(box.host, PINS))["opencode"]
    assert (row.status, row.installed) == ("updated", PINS["opencode"])
    script = next(script for script in box.scripts if "opencode.ai" in script)
    assert (
        f"https://opencode.ai/v2/install | VERSION={PINS['opencode']} bash -s -- --no-modify-path"
        in script
    )
    assert not any("https://opencode.ai/install" in script for script in box.scripts)


def test_opencode_at_its_pin_is_left_alone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    assert _rows(fleet_update.apply(box.host, PINS))["opencode"].status == "ok"
    assert not any("opencode.ai" in script for script in box.scripts)


def test_personal_installs_the_pinned_opencode_with_the_same_line_builder() -> None:
    step = next(step for step in personal.STEPS if step.key == "opencode")
    lines = step.lines(personal.Box(home=Path("/h"), user="u", facts={}))
    assert lines == fleet_setup.opencode_lines(PINS["opencode"])
    assert "opencode" not in fleet_setup.VENDOR_INSTALLERS


# -- reference sources and strays ----------------------------------------------------------


def test_check_reports_both_reference_sources_against_their_pins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(
        tmp_path,
        monkeypatch,
        {**AT_PINS, "strawberry-django": "0.81.0", "graphene-django": ""},
    )
    rows = _rows(fleet_update.check(box.host, PINS))
    assert (rows["strawberry-django"].installed, rows["strawberry-django"].status) == (
        "0.81.0",
        "behind",
    )
    assert rows["django-graphene-filters"].status == "ok"
    assert rows["graphene-django"].status == "missing"
    assert box.scripts == []


def test_a_working_filters_clone_past_the_pin_is_no_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    past = f"{_bare(PINS['django-graphene-filters'])}-3-g9ab2662"
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "django-graphene-filters": past})
    box.filters_changes = " M pyproject.toml"
    _here(monkeypatch, box)
    row = _rows(fleet_update.check(box.host, PINS))["django-graphene-filters"]
    assert (row.installed, row.status, row.detail) == (f"v{past}", "ahead", "local changes")
    assert fleet_update.main(["check"]) == 0
    _ = capsys.readouterr()
    rows = _rows(fleet_update.apply(box.host, PINS))
    assert rows["django-graphene-filters"].status == "ahead"
    assert not any(marker in script for script in box.scripts for marker in ("git ", "uv sync"))


def test_a_tree_naming_no_version_differs_and_apply_runs_its_guarded_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "strawberry-django": NO_RELEASE})
    row = _rows(fleet_update.check(box.host, PINS))["strawberry-django"]
    assert (row.status, row.detail) == ("differs", "its pyproject.toml names no release version")
    box.fail_install.add("strawberry-django")
    row = _rows(fleet_update.apply(box.host, PINS))["strawberry-django"]
    assert row.status == "failed"
    pin = PINS["strawberry-django"]
    line = fleet_setup.strawberry_django_lines(pin, "")[0]
    assert any(line in script for script in box.scripts)


def test_apply_brings_missing_reference_sources_with_the_setup_line_builders(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(
        tmp_path,
        monkeypatch,
        {
            **AT_PINS,
            "strawberry-django": "",
            "django-graphene-filters": "",
            "graphene-django": "",
        },
    )
    rows = _rows(fleet_update.apply(box.host, PINS))
    for key in ("strawberry-django", "django-graphene-filters", "graphene-django"):
        assert (rows[key].status, rows[key].detail) == ("updated", "from nothing"), key
    references = box.scripts[-3:]
    assert fleet_setup.strawberry_django_lines(PINS["strawberry-django"], "")[0] in references[0]
    assert fleet_setup.filters_lines(PINS["django-graphene-filters"])[0] in references[1]
    assert fleet_setup.graphene_django_lines()[0] in references[2]


def test_setup_installs_the_reference_sources_with_the_same_line_builders(tmp_path: Path) -> None:
    box = fleet_setup.Box(home=tmp_path, user="u", repo=tmp_path / "r")
    steps = {step.key: step.lines(box) for step in fleet_setup.STEPS}
    assert steps["strawberry-django"] == fleet_setup.strawberry_django_lines(
        PINS["strawberry-django"],
        "",
    )
    assert steps["django-graphene-filters"] == fleet_setup.filters_lines(
        PINS["django-graphene-filters"],
    )
    assert steps["graphene-django"] == fleet_setup.graphene_django_lines()


def test_strays_make_check_exit_1_and_each_row_names_its_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    box = _box(tmp_path, monkeypatch)
    _here(monkeypatch, box)
    rows = _rows(fleet_update.check(box.host, PINS))
    assert (rows["strays"].installed, rows["strays"].status) == ("none", "ok")
    projects = box.home / fleet_setup.PROJECTS
    (projects / "dsf-old").mkdir()
    _ = (projects / "x.txt").write_text("x")
    rows = _rows(fleet_update.check(box.host, PINS))
    assert "strays" not in rows
    why = "no entry ~/projects holds"
    assert (rows["stray ~/projects/dsf-old"].status, rows["stray ~/projects/dsf-old"].detail) == (
        "stray",
        why,
    )
    assert rows["stray ~/projects/x.txt"].status == "stray"
    assert fleet_update.main(["check"]) == 1
    out = capsys.readouterr().out
    assert "stray ~/projects/dsf-old" in out
    assert (projects / "dsf-old").is_dir()
    opened = dataclasses.replace(box.host, other_projects=True)

    def here(_cls: type[fleet_update.Host]) -> fleet_update.Host:
        return opened

    monkeypatch.setattr(fleet_update.Host, "here", classmethod(here))
    assert fleet_update.main(["check"]) == 0


def test_the_host_reads_other_projects_from_its_row(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(fleet.MACHINE_ENV, "rio-air")
    assert fleet_update.Host.here().other_projects is True
    monkeypatch.setenv(fleet.MACHINE_ENV, "rio-bee")
    assert fleet_update.Host.here().other_projects is False
    monkeypatch.setenv(fleet.MACHINE_ENV, "nowhere")
    assert fleet_update.Host.here().other_projects is False


def test_check_all_lists_each_stray_on_its_own_line() -> None:
    reports = [
        fleet_update.Report("rio-ubu", (fleet_update.Row("strays", "", "none", "ok"),)),
        fleet_update.Report(
            "rio-bee",
            (fleet_update.Row("stray ~/projects/dsf-2", "", "", "stray", "a clone of this repo"),),
        ),
    ]
    assert fleet_update.fleet_table(reports) == [
        "item                    pinned  rio-ubu  rio-bee",
        "strays                          none     -",
        "stray ~/projects/dsf-2          -        - stray",
        "",
        "rio-bee: stray ~/projects/dsf-2: a clone of this repo",
    ]


# -- busy families, held apps, deferred retries --------------------------------------------

#: Two listed apps (the real list is ``fleet_update.apps()``).
CLAUDE = fleet_setup.App(
    "Claude",
    "claude",
    "com.anthropic.claudefordesktop",
    "claude",
    "claude-desktop",
)
CURSOR = fleet_setup.App("Cursor", "cursor", "com.todesktop.230313mzl4w4u92", "cursor", "cursor")
LISTED = (CLAUDE, CURSOR)
#: The Claude Code CLI's real executable under the home folder.
CLAUDE_EXE = ".local/share/claude/versions/2.1.322"
#: ``sudo -n`` of each Linux OS command, and of ``apt-mark``.
UPDATE = [
    "sudo",
    "-n",
    "/usr/bin/apt-get",
    "update",
]
UPGRADE = [
    "sudo",
    "-n",
    "/usr/bin/apt-get",
    "upgrade",
    "-y",
]
SNAP = [
    "sudo",
    "-n",
    "/usr/bin/snap",
    "refresh",
]


def _mark(verb: str, package: str) -> list[str]:
    return [
        "sudo",
        "-n",
        fleet_update.APT_MARK,
        verb,
        package,
    ]


def _sudo_calls(box: Box) -> list[list[str]]:
    return [call for call in box.calls if call[0] == "sudo"]


def _ps(box: Box, *processes: tuple[int, int, str]) -> None:
    """Make ``ps`` list ``processes`` (pid, parent, command line; ``~`` is the box's home)."""
    box.ps = "".join(
        f"{pid:>6} {ppid:>6} {args.replace('~', str(box.home))}\n" for pid, ppid, args in processes
    )


def _proc(tmp_path: Path, box: Box, exes: Mapping[int, str]) -> fleet_update.Host:
    """Return the box's host reading each pid's executable from a ``/proc`` of ``exes``."""
    proc = tmp_path / "proc"
    for pid, exe in exes.items():
        (proc / str(pid)).mkdir(parents=True)
        (proc / str(pid) / "exe").symlink_to(exe.replace("~", str(box.home)))
    return dataclasses.replace(box.host, proc=proc)


def _app(
    folder: Path,
    name: str,
    bundle: str,
    version: str,
) -> Path:
    path = folder / f"{name}.app"
    (path / "Contents").mkdir(parents=True)
    info = {"CFBundleIdentifier": bundle, "CFBundleShortVersionString": version}
    _ = (path / "Contents" / "Info.plist").write_bytes(plistlib.dumps(info))
    return path


def test_the_apps_are_one_line_each_and_every_family_is_in_the_table() -> None:
    listed = fleet_update.apps()
    assert [app.name for app in listed] == [
        "Claude",
        "ChatGPT",
        "Cursor",
        "VS Code",
        "Antigravity",
        "OpenCode",
        "T3 Code",
        "Devin",
        "Warp",
        "Ghostty",
        "Grok Bot",
    ]
    assert all(app.bundle and app.cask and app.apt for app in listed)
    text = fleet_setup.VERSIONS_FILE.read_text()
    assert all(text.count(f'"{app.name}": "family={app.family} ') == 1 for app in listed)
    families = {family.name for family in fleet_update.FAMILIES}
    assert {tool.family for tool in fleet_update.TOOLS} - {""} <= families
    assert {app.family for app in listed} <= families
    assert families == {
        "claude",
        "codex",
        "opencode",
        "antigravity",
        "grok",
        "muse",
        "cursor",
        "vscode",
        "t3code",
        "devin",
        "warp",
        "ghostty",
        "node",
        "uv",
    }


@pytest.mark.parametrize(
    ("line", "message"),
    [
        ("family=claude colour=red", "no family/bundle/cask/apt=value word"),
        ("bundle=com.x cask=x", "needs a name and a family"),
        ("family=claude apt=claude*", "no family/bundle/cask/apt=value word"),
        ("family=claude family=codex", "no family/bundle/cask/apt=value word"),
        ("family=paint", "no family 'paint'"),
        ("", "non-empty string"),
    ],
)
def test_a_malformed_app_line_is_refused(tmp_path: Path, line: str, message: str) -> None:
    path = tmp_path / "versions.json"
    _ = path.write_text(json.dumps({"versions": PINS, "apps": {"Thing": line}}))
    with pytest.raises(fleet_update.UpdateError, match=message):
        _ = fleet_update.apps(path)


def test_a_running_cli_defers_its_family_and_only_its_family(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "claude": "2.0.0", "uv": "0.1.0"})
    _ps(box, (1001, 1, "claude --resume"))
    host = _proc(tmp_path, box, {1001: f"~/{CLAUDE_EXE}"})
    rows = _rows(fleet_update.apply(host, PINS))
    assert (rows["claude"].status, rows["claude"].detail) == (
        "busy",
        "claude is running (pids 1001)",
    )
    assert not any("claude.ai/install.sh" in script for script in box.scripts)
    assert rows["uv"].status == "updated"
    assert "busy" not in fleet_update.TROUBLE
    deferred = fleet_update.read_deferred(host.root)
    assert list(deferred) == ["claude"]
    assert deferred["claude"].pids == (1001,)


def test_a_node_process_is_matched_by_the_script_it_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    _ps(box, (2002, 1, "node ~/.nvm/versions/node/v26.13.1/bin/codex exec --json"))
    assert fleet_update.busy(box.host, {}) == {"codex": (2002,), "node": (2002,)}


def test_a_loose_name_is_no_family(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    box = _box(tmp_path, monkeypatch)
    _ps(
        box,
        (3003, 1, "/usr/bin/vim ~/.local/bin/claude"),
        (3004, 1, "/opt/other/claude --resume"),
        (3005, 1, "claude"),
        (3006, 1, "~/.local/bin/claudette"),
        (3007, 1, "/usr/bin/python3 -m codex"),
    )
    assert fleet_update.busy(box.host, {}) == {}


def test_the_updaters_own_tree_is_never_busy_but_the_session_it_runs_in_is(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    session = (100, 1, f"~/{CLAUDE_EXE} --resume")
    tree = (
        (200, 100, "/bin/zsh -c uv run python docs/fleet/scripts/fleet_update.py apply"),
        (300, 200, "~/.local/bin/uv run python docs/fleet/scripts/fleet_update.py apply"),
        (500, 300, "/r/.venv/bin/python docs/fleet/scripts/fleet_update.py apply"),
        (600, 500, "~/.local/bin/uv --version"),
    )
    host = dataclasses.replace(box.host, pid=500)
    _ps(box, session, *tree)
    assert fleet_update.busy(host, {}) == {"claude": (100,)}
    _ps(box, session, *tree, (700, 1, "~/.local/bin/uv run pytest"))
    assert fleet_update.busy(host, {}) == {"claude": (100,), "uv": (700,)}


def test_macos_reads_a_bare_commands_executable_from_lsof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, system=fleet_setup.MACOS)
    _ps(box, (4004, 1, "claude --resume"), (4005, 1, "/usr/bin/true"))
    box.lsof = f"p4004\nftxt\nn{box.home}/{CLAUDE_EXE}\nftxt\nn/usr/lib/dyld\n"
    assert fleet_update.busy(box.host, {}) == {"claude": (4004,)}
    lsof = [call for call in box.calls if call[0] == "/usr/sbin/lsof"]
    assert lsof == [
        [
            "/usr/sbin/lsof",
            "-a",
            "-d",
            "txt",
            "-Fpn",
            "-p",
            "4004",
        ],
    ]


def test_a_busy_desktop_app_is_held_around_the_upgrade_and_unheld(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.debs = {"claude-desktop", "cursor"}
    _ps(box, (5005, 1, "/usr/lib/claude-desktop/claude-desktop --type=renderer"))
    rows = fleet_update.apply(box.host, PINS, listed=LISTED)
    assert _sudo_calls(box) == [
        UPDATE,
        _mark("hold", "claude-desktop"),
        UPGRADE,
        _mark("unhold", "claude-desktop"),
        SNAP,
    ]
    app = _rows(rows)["app Claude"]
    assert app.status == "busy"
    assert app.detail == "claude is running (pids 5005): claude-desktop held through the upgrade"
    assert _rows(rows)["apt-get upgrade -y"].status == "done"
    assert box.holds == set()
    assert not (box.host.root / ".work" / fleet_update.HOLDS_STATE).exists()
    assert list(fleet_update.read_deferred(box.host.root)) == ["claude"]


def test_a_hold_is_recorded_before_the_upgrade_and_a_killed_runs_hold_is_undone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.debs = {"claude-desktop"}
    _ps(box, (5005, 1, "/usr/lib/claude-desktop/claude-desktop"))
    recorded: list[list[str]] = []

    def sudo(argv: list[str]) -> fleet_update.Ran:
        if argv == UPGRADE:
            recorded.append(fleet_update.read_holds(box.host.root)[1])
        return fleet_update.Ran(0, "", "")

    box.sudo = sudo
    _ = fleet_update.apply(box.host, PINS, listed=LISTED)
    assert recorded == [["claude-desktop"]]
    # A run killed mid-upgrade leaves its record; check names it, the next apply unholds it.
    fleet_update.save_holds(box.host.root, ["claude-desktop"])
    state = box.host.root / ".work" / fleet_update.HOLDS_STATE
    _ = state.write_text(json.dumps({"pid": 2_000_000_000, "packages": ["claude-desktop"]}))
    row = _rows(fleet_update.check(box.host, PINS))["hold claude-desktop"]
    assert row.status == "stale"
    assert "stale" in fleet_update.DRIFT
    _ps(box)
    box.calls.clear()
    rows = fleet_update.apply(box.host, PINS, listed=LISTED)
    assert _sudo_calls(box)[0] == _mark("unhold", "claude-desktop")
    assert rows[0].item == "holds"
    assert rows[0].status == "released"
    assert not state.exists()


def test_a_package_held_before_is_neither_held_nor_unheld(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.debs = {"claude-desktop"}
    box.holds = {"claude-desktop"}
    _ps(box, (5005, 1, "/usr/lib/claude-desktop/claude-desktop"))
    rows = fleet_update.apply(box.host, PINS, listed=LISTED)
    assert _sudo_calls(box) == [UPDATE, UPGRADE, SNAP]
    assert "left held" in _rows(rows)["app Claude"].detail
    assert box.holds == {"claude-desktop"}


def test_a_rule_without_the_hold_lines_skips_the_whole_upgrade(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch)
    box.debs = {"claude-desktop", "cursor"}
    _ps(box, (5005, 1, "/usr/lib/claude-desktop/claude-desktop"))
    box.sudo = lambda argv: (
        fleet_update.Ran(1, "", "sudo: a password is required\n")
        if argv[2] == fleet_update.APT_MARK
        else fleet_update.Ran(0, "", "")
    )
    rows = fleet_update.apply(box.host, PINS, listed=LISTED)
    assert _sudo_calls(box) == [UPDATE, _mark("hold", "claude-desktop"), SNAP]
    row = _rows(rows)["apt-get upgrade -y"]
    assert row.status == "busy"
    assert "claude is running (pids 5005): nothing upgraded" in row.detail
    assert "fleet_update.py sudoers" in row.detail
    assert list(fleet_update.read_deferred(box.host.root)) == ["claude"]


def test_apply_deferred_does_nothing_when_no_family_waits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "uv": "0.1.0"})
    rows = fleet_update.apply(box.host, PINS, listed=LISTED, deferred_only=True)
    assert [(row.item, row.status) for row in rows] == [("deferred", "ok")]
    assert box.calls == []


def test_apply_deferred_retries_only_the_waiting_families_and_clears_them(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, {**AT_PINS, "claude": "2.0.0"})
    _ps(box, (1001, 1, "claude"))
    host = _proc(tmp_path, box, {1001: f"~/{CLAUDE_EXE}"})
    _ = fleet_update.apply(host, PINS)
    since = fleet_update.read_deferred(host.root)["claude"].since
    box.versions["uv"] = "0.1.0"  # off its pin, yet no family of its waits
    box.sync()
    rows = fleet_update.apply(host, PINS, deferred_only=True)
    assert [(row.item, row.status) for row in rows] == [("claude", "busy")]
    assert fleet_update.read_deferred(host.root)["claude"].since == since
    _ps(box)
    rows = fleet_update.apply(host, PINS, deferred_only=True)
    assert [(row.item, row.status) for row in rows] == [("claude", "updated")]
    assert not any("astral.sh" in script for script in box.scripts)
    assert fleet_update.read_deferred(host.root) == {}
    rows = fleet_update.apply(host, PINS, deferred_only=True)
    assert [(row.item, row.status) for row in rows] == [("deferred", "ok")]


def test_check_shows_each_deferred_family_and_how_long_it_waited(tmp_path: Path) -> None:
    now = 1_800_000_000.0
    fleet_update.save_deferred(
        tmp_path,
        {"claude": fleet_update.Waiting(now - 3 * 3600 - 120, (100, 200))},
    )
    [row] = fleet_update.state_rows(tmp_path, now)
    assert (row.item, row.status) == ("deferred claude", "deferred")
    assert row.detail.startswith("waiting 3h 2m, since ")
    assert row.detail.endswith("claude is running (pids 100, 200)")
    assert not fleet_update.drifted(row)


def test_macos_reports_each_installed_app_against_its_cask_and_never_touches_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, system=fleet_setup.MACOS)
    monkeypatch.setattr(fleet_update, "brew", _homebrew)
    folder = tmp_path / "Applications"
    claude = _app(folder, "Claude", CLAUDE.bundle, "5.0.0")
    _ = _app(folder, "Cursor", CURSOR.bundle, "3.29.15")
    _ = _app(folder, "Safari", "com.apple.Safari", "27.2")
    host = dataclasses.replace(box.host, applications=(folder,))
    box.casks = {"claude": "5.1231.2", "cursor": "3.29.15"}
    rows = _rows(fleet_update.check(host, PINS, LISTED))
    behind, current = rows["app Claude"], rows["app Cursor"]
    assert (behind.pinned, behind.installed, behind.status) == ("5.1231.2", "5.0.0", "behind")
    assert (current.installed, current.status) == ("3.29.15", "ok")
    assert not any(fleet_update.drifted(row) for row in (behind, current))
    assert "app Safari" not in rows
    applied = _rows(fleet_update.apply(host, PINS, listed=LISTED))
    assert applied["app Claude"].status == "report"
    brew_calls = [call[1:] for call in box.calls if call[0] == "/opt/homebrew/bin/brew"]
    assert all(
        call[0]
        in {
            "info",
            "update",
            "outdated",
            "upgrade",
        }
        for call in brew_calls
    )
    assert ["upgrade", "--greedy"] in brew_calls
    _ps(box, (6006, 1, f"{claude}/Contents/MacOS/Claude"))
    found = fleet_update.app_bundles(host, LISTED)
    assert fleet_update.busy(host, fleet_update.bundle_folders(found)) == {"claude": (6006,)}


def test_macos_brew_upgrade_leaves_a_listed_apps_cask_alone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    box = _box(tmp_path, monkeypatch, system=fleet_setup.MACOS)
    monkeypatch.setattr(fleet_update, "brew", _homebrew)
    box.outdated = "glab\ncursor\n"
    rows = _rows(fleet_update.apply(box.host, PINS, listed=LISTED))
    upgrades = [call for call in box.calls if call[1:2] == ["upgrade"]]
    assert upgrades == [
        [
            "/opt/homebrew/bin/brew",
            "upgrade",
            "--greedy",
            "glab",
        ],
    ]
    assert rows["brew upgrade --greedy"].detail.endswith("left alone: cursor (listed apps)")


def test_the_retry_timer_runs_apply_deferred_hourly_under_the_same_rules(
    tmp_path: Path,
) -> None:
    stop = f"[ -e {fleet_stop.FLAG} ] && exit 0; "
    macos = fleet_update.schedule_files(tmp_path, Path("/r"), "darwin")
    retry = _plist(
        macos[
            tmp_path / "Library" / "LaunchAgents" / f"{fleet_update.RETRY_LABEL}.plist"
        ].encode(),
    )
    assert fleet.is_json_object(retry)
    assert retry["StartCalendarInterval"] == {"Minute": fleet_update.RETRY_MINUTE}
    line = fleet_update.schedule_line(Path("/r"), fleet_update.SCHEDULE_JITTER, "apply --deferred")
    assert retry["ProgramArguments"] == ["/bin/sh", "-c", line]
    assert line.count(stop) == 2
    assert line.index("sleep") < line.rindex(stop) < line.index("fleet_update.py apply --deferred")
    linux = fleet_update.schedule_files(tmp_path, Path("/r"), "linux")
    units = tmp_path / ".config" / "systemd" / "user"
    timer = linux[units / f"{fleet_update.RETRY_UNIT}.timer"]
    service = linux[units / f"{fleet_update.RETRY_UNIT}.service"]
    assert f"OnCalendar=*-*-* *:{fleet_update.RETRY_MINUTE:02d}:00" in timer
    assert "Persistent=true" in timer
    assert f"RandomizedDelaySec={fleet_update.SCHEDULE_JITTER}s" in timer
    assert "fleet_update.py apply --deferred" in service
    assert stop in service


def test_sudoers_names_one_exact_hold_and_unhold_per_listed_package() -> None:
    listed = fleet_update.apps()
    text = fleet_update.sudoers_text("rio", listed)
    rules = [line for line in text.splitlines() if line and not line.startswith("#")]
    marks = [rule for rule in rules if "apt-mark" in rule]
    assert marks == [
        f"rio ALL=(root) NOPASSWD: /usr/bin/apt-mark {verb} {app.apt}"
        for app in listed
        for verb in ("hold", "unhold")
    ]
    assert not any("*" in rule for rule in rules)
    odd = fleet_setup.App("Odd", "claude", apt="x ALL")
    with pytest.raises(fleet_update.UpdateError, match="refusing to render the packages"):
        _ = fleet_update.sudoers_text("rio", [odd])
