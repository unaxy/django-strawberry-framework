"""Script tests for ``docs/fleet/scripts/fleet_update.py``, the fleet's pinned-version updater."""

from __future__ import annotations

import getpass
import json
import os
import plistlib
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, fleet_setup, fleet_stop, fleet_update
from docs.fleet.scripts.setup.ubuntu import personal

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

PINS = fleet_setup.load_versions()
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
    *((url, key) for key, url in fleet_setup.VENDOR_INSTALLERS.items()),
)
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
            (self.home / ".nvm" / "versions" / "node" / f"v{self.versions['node']}").mkdir(
                parents=True,
                exist_ok=True,
            )
        alias = self.home / ".nvm" / "alias" / "default"
        alias.parent.mkdir(parents=True, exist_ok=True)
        _ = alias.write_text(self.alias)

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

    def answer(self, argv: list[str]) -> fleet_update.Ran:
        if argv[:2] == ["bash", "-c"]:
            return self.bash(argv[2])
        name = Path(argv[0]).name
        if argv[0] == "sudo":
            return self.sudo(argv)
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
            return fleet_update.Ran(0, "glab\nfirefox\n" if "outdated" in argv else "done\n", "")
        if name == "softwareupdate":
            return fleet_update.Ran(
                0,
                "Software Update found:\n* Label: macOS 27.2.1-26B131\n",
                "",
            )
        msg = f"unexpected command {argv}"
        raise AssertionError(msg)

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
    assert (
        latest
        == set(fleet_setup.VENDOR_INSTALLERS)
        == {
            "opencode",
            "muse",
            "grok",
            "agy",
        }
    )


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
    (box.home / ".nvm" / "versions" / "node" / "v99.0.0").mkdir()
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
        'bash -c \'. "$HOME/.nvm/nvm.sh" && npm uninstall -g --prefix "$HOME"/.local @openai/codex\'',
    )
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
    assert [row["item"] for row in rows if fleet.is_json_object(row)][:12] == list(PINS)


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
    assert script.lstrip("( ").startswith('. "$NVM_DIR/nvm.sh" && ')
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
    assert [row.status for row in rows] == ["busy"]
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
    [(path, text)] = files.items()
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
    ]
    assert fleet_update.SUDOERS_FILE.parent == fleet_setup.PATH_BLOCK_FILE.parent


def test_sudoers_renders_the_account_and_refuses_an_odd_one() -> None:
    assert (
        fleet_update.sudoers_text("rio")
        .splitlines()[-1]
        .startswith("rio ALL=(root) NOPASSWD: /usr/bin/apt-get update,")
    )
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
    assert fleet_update.sudoers_text("rio") in out
    assert fleet_update.sudoers_command(fleet_update.sudoers_text("rio")) in out


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
