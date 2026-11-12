"""Script tests for ``docs/fleet/scripts/fleet_setup.py``, the one-command setup of a new fleet machine."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, fleet_setup, fleet_stop

if TYPE_CHECKING:
    from collections.abc import Sequence


def _box(tmp_path: Path) -> fleet_setup.Box:
    return fleet_setup.Box(home=tmp_path, user="someone", repo=tmp_path / "projects" / "dsf")


def _step(key: str, kind: str, gaps: list[str | None]) -> fleet_setup.Step:
    """Return a step whose check answers ``gaps`` in turn, its line naming ``key``."""
    return fleet_setup.Step(
        key,
        kind,
        key,
        lambda _box: gaps.pop(0) if gaps else None,
        lambda _box: [f"make {key}"],
    )


def test_the_ssh_options_match_the_fleets() -> None:
    assert fleet_setup.SSH_OPTIONS == fleet.SSH_OPTIONS


def test_the_checkout_path_is_the_one_fleet_sync_requires() -> None:
    assert {row["repo"] for row in fleet_stop.machine_rows()} == {fleet_setup.REPO}


def test_step_keys_are_unique_and_every_kind_is_known() -> None:
    keys = [step.key for step in fleet_setup.STEPS]
    assert len(keys) == len(set(keys))
    assert {step.kind for step in fleet_setup.STEPS} <= set(fleet_setup.KINDS)


def test_root_steps_come_first_so_one_prompt_covers_them() -> None:
    kinds = [step.kind for step in fleet_setup.STEPS]
    assert kinds[: kinds.count("sudo")] == ["sudo"] * kinds.count("sudo")


def test_select_keeps_order_and_drops_skipped_kinds() -> None:
    picked = fleet_setup.select(["checkout", "uv", "ssh-key"], ["keys"], fleet_setup.LINUX)
    assert [step.key for step in picked] == ["uv", "checkout"]


def test_select_refuses_an_unknown_step_or_kind() -> None:
    with pytest.raises(ValueError, match="nope, root"):
        _ = fleet_setup.select(["nope"], ["root"], fleet_setup.LINUX)


def test_report_marks_each_step(tmp_path: Path) -> None:
    steps = [_step("uv", "user", [None]), _step("packages", "sudo", ["git"])]
    lines = fleet_setup.report(fleet_setup.check(_box(tmp_path), steps))
    assert lines == ["ok      user uv", "missing sudo packages  git"]


def test_install_runs_root_steps_first_in_one_call_and_skips_done_ones(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[list[str], bool]] = []

    def fake(lines: Sequence[str], _box: fleet_setup.Box, *, sudo: bool = False) -> int:
        calls.append((list(lines), sudo))
        return 0

    monkeypatch.setattr(fleet_setup, "run_lines", fake)
    steps = [
        _step("done", "user", [None, None]),
        _step("tool", "user", ["tool", None, None]),
        _step("pkg", "sudo", ["pkg", None]),
        _step("login", "hand", ["login", "login"]),
    ]
    assert fleet_setup.install(_box(tmp_path), steps) == 0
    assert calls == [(["make pkg"], True), (["make tool"], False)]


def test_install_stops_at_a_step_whose_check_still_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ran: list[str] = []

    def fake(lines: Sequence[str], _box: fleet_setup.Box, *, sudo: bool = False) -> int:
        del sudo
        ran.extend(lines)
        return 0

    monkeypatch.setattr(fleet_setup, "run_lines", fake)
    steps = [_step("first", "user", ["x", "still x"]), _step("second", "user", ["y"])]
    assert fleet_setup.install(_box(tmp_path), steps) == 1
    assert ran == ["make first"]


def test_the_direnv_hook_check_reads_bashrc(tmp_path: Path) -> None:
    box = _box(tmp_path)
    hook = next(step for step in fleet_setup.STEPS if step.key == "direnv-hook")
    assert hook.check(box) is not None
    _ = (tmp_path / ".bashrc").write_text(f"# shell\n{fleet_setup.DIRENV_HOOK}\n")
    assert hook.check(box) is None


def test_a_github_ssh_remote_becomes_https() -> None:
    assert fleet_setup.https_url("git@github.com:o/r.git") == "https://github.com/o/r.git"
    assert fleet_setup.https_url("https://example.com/r.git") == "https://example.com/r.git"


def test_box_command_quotes_its_words() -> None:
    line = fleet_setup.box_command("check", ["--repo-url", "a b"])
    assert line == f"python3 {fleet_setup.REMOTE_COPY} box check --repo-url 'a b'"


def test_a_small_box_gets_low_weights_and_lowered_floors() -> None:
    assert fleet_setup.suggest_row("box", 4, 7 * 1024 * 1024) == {
        "name": "box",
        "ssh": "box",
        "os": "linux",
        "repo": fleet_setup.REPO,
        "weight": {"light": 0.4, "heavy": 0.2},
        "floors": {
            "light": {
                "min_mem_available_gib": 2,
                "min_disk_free_gib": 6,
                "max_psi_memory_full_avg10": 5,
            },
            "heavy": {
                "min_mem_available_gib": 3,
                "min_disk_free_gib": 12,
                "max_psi_memory_full_avg10": 5,
            },
        },
        "aliases": [],
    }


@pytest.mark.parametrize(
    (
        "cores",
        "gib",
        "light",
        "heavy",
    ),
    [
        (
            12,
            45,
            1.0,
            1.0,
        ),
        (
            1,
            1,
            0.1,
            0.1,
        ),
    ],
)
def test_a_suggested_weight_is_capped_at_one_and_floored_at_a_tenth(
    cores: int,
    gib: int,
    light: float,
    heavy: float,
) -> None:
    suggested = fleet_setup.suggest_row("box", cores, gib * 1024 * 1024)
    assert suggested["weight"] == {"light": light, "heavy": heavy}


def test_machine_names_reads_every_named_row(tmp_path: Path) -> None:
    listed = tmp_path / "machines.json"
    _ = listed.write_text(json.dumps({"machines": [{"name": "a"}, {"ssh": "b"}, "c"]}))
    assert fleet_setup.machine_names(listed) == ["a"]


SYSTEMS = (fleet_setup.LINUX, fleet_setup.MACOS)


def _block() -> str:
    return fleet_setup.block(fleet_setup.PATH_MARK, fleet_setup.PATH_BLOCK_FILE.read_text())


def _listing(home: Path) -> dict[str, bytes]:
    return {path.name: path.read_bytes() for path in sorted(home.iterdir())}


def test_one_block_file_serves_every_os_and_the_ubuntu_layer() -> None:
    setup = fleet_setup.PATH_BLOCK_FILE.parent.parent
    assert setup / "files" / "path.sh" == fleet_setup.PATH_BLOCK_FILE
    assert fleet_setup.PATH_BLOCK_FILE.is_file()
    assert not any(setup.rglob("bashrc-path.sh"))
    assert (fleet_setup.PATH_BLOCK_FILE, "setup/files/path.sh") in fleet_setup.PUSHED
    step = next(step for step in fleet_setup.STEPS if step.key == "path-block")
    assert step.systems == SYSTEMS


@pytest.mark.parametrize(
    ("system", "name"),
    [(fleet_setup.LINUX, ".bashrc"), (fleet_setup.MACOS, ".zshenv")],
)
def test_each_os_gets_the_file_its_shell_reads_for_an_ssh_command(
    tmp_path: Path,
    system: str,
    name: str,
) -> None:
    assert fleet_setup.startup_file(tmp_path, system) == tmp_path / name


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_creates_an_absent_file_holding_the_block_alone(
    tmp_path: Path,
    system: str,
) -> None:
    assert fleet_setup.write_path_block(tmp_path, system, 7) is None
    target = fleet_setup.startup_file(tmp_path, system)
    assert _listing(tmp_path) == {target.name: _block().encode()}
    assert target.stat().st_mode & 0o777 == 0o644
    assert fleet_setup.check_path_block(tmp_path, system) is None


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_replaces_a_stale_block_moves_it_first_and_keeps_a_backup(
    tmp_path: Path,
    system: str,
) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    stale = "export A=1\n" + fleet_setup.block(fleet_setup.PATH_MARK, "PATH=old") + "export B=2\n"
    _ = target.write_text(stale)
    target.chmod(0o600)
    backup = tmp_path / f"{target.name}.bak-7"
    assert fleet_setup.write_path_block(tmp_path, system, 7) == backup
    assert backup.read_text() == stale
    assert target.read_text() == _block() + "\nexport A=1\nexport B=2\n"
    assert target.stat().st_mode & 0o777 == 0o600
    assert sorted(_listing(tmp_path)) == sorted([target.name, backup.name])


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_writer_prepends_the_block_to_a_file_without_one(tmp_path: Path, system: str) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text("\n\nexport A=1\n")
    backup = fleet_setup.write_path_block(tmp_path, system, 7)
    assert backup is not None
    assert backup.read_text() == "\n\nexport A=1\n"
    assert target.read_text() == _block() + "\nexport A=1\n"


@pytest.mark.parametrize("system", SYSTEMS)
def test_a_second_write_changes_nothing_and_keeps_no_second_backup(
    tmp_path: Path,
    system: str,
) -> None:
    _ = fleet_setup.startup_file(tmp_path, system).write_text("export A=1\n")
    _ = fleet_setup.write_path_block(tmp_path, system, 7)
    before = _listing(tmp_path)
    assert fleet_setup.write_path_block(tmp_path, system, 8) is None
    assert _listing(tmp_path) == before


@pytest.mark.parametrize("system", SYSTEMS)
def test_a_file_holding_the_block_alone_is_current_and_left_as_it_is(
    tmp_path: Path,
    system: str,
) -> None:
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text(_block())
    assert fleet_setup.check_path_block(tmp_path, system) is None
    assert fleet_setup.write_path_block(tmp_path, system, 7) is None
    assert _listing(tmp_path) == {target.name: _block().encode()}


@pytest.mark.parametrize("system", SYSTEMS)
def test_the_check_writes_nothing_and_wants_the_block_first(tmp_path: Path, system: str) -> None:
    name = fleet_setup.startup_file(tmp_path, system).name
    gap = f"PATH block at the top of ~/{name}"
    assert fleet_setup.check_path_block(tmp_path, system) == gap
    assert _listing(tmp_path) == {}
    target = fleet_setup.startup_file(tmp_path, system)
    _ = target.write_text("guard\n" + _block())
    stamp = target.stat().st_mtime_ns
    assert fleet_setup.check_path_block(tmp_path, system) == gap
    assert _listing(tmp_path) == {name: ("guard\n" + _block()).encode()}
    assert target.stat().st_mtime_ns == stamp


def test_the_steps_writer_line_runs_this_file_with_this_python(tmp_path: Path) -> None:
    (line,) = fleet_setup.path_block_lines()
    assert line.endswith(" box write-path-block")
    env = {**os.environ, "HOME": str(tmp_path)}
    completed = subprocess.run(
        ["bash", "-c", line],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr
    assert fleet_setup.check_path_block(tmp_path, platform.system()) is None


def test_a_mac_box_runs_only_the_path_step() -> None:
    steps = fleet_setup.select([], [], fleet_setup.MACOS)
    assert [step.key for step in steps] == ["path-block"]
    assert "path-block" in [step.key for step in fleet_setup.select([], [], fleet_setup.LINUX)]
    with pytest.raises(ValueError, match="not a Darwin step: linger"):
        _ = fleet_setup.select(["linger"], [], fleet_setup.MACOS)


@pytest.mark.parametrize(
    ("answers", "system"),
    [
        ([(0, "Darwin")], "Darwin"),
        ([(0, "Linux"), (0, "ubuntu")], "Linux"),
        ([(0, "Linux"), (0, "debian")], "Linux debian"),
        ([(255, "unreached")], ""),
    ],
)
def test_add_tells_a_mac_from_ubuntu_and_anything_else(
    monkeypatch: pytest.MonkeyPatch,
    answers: list[tuple[int, str]],
    system: str,
) -> None:
    def fake(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        del host, command
        return answers.pop(0)

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.system_of("box") == system
    assert answers == []


def test_add_copies_the_script_and_the_path_block(monkeypatch: pytest.MonkeyPatch) -> None:
    pushed: list[tuple[str, str | None]] = []

    def fake(host: str | None, command: str, **options: str | None) -> tuple[int, str]:
        del host
        pushed.append((command, options.get("stdin")))
        return 0, ""

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.push_self("box") == 0
    root = fleet_setup.REMOTE_ROOT
    assert pushed == [
        (
            f"mkdir -p {root} && cat > {root}/fleet_setup.py",
            Path(fleet_setup.__file__).read_text(),
        ),
        (
            f"mkdir -p {root}/setup/files && cat > {root}/setup/files/path.sh",
            fleet_setup.PATH_BLOCK_FILE.read_text(),
        ),
    ]


def test_verify_asks_plain_ssh_for_every_tool() -> None:
    assert fleet_setup.tools_command() == "command -v uv git python3 node claude codex gh"


@pytest.mark.parametrize(
    ("output", "absent", "code"),
    [
        ("\n".join(f"/some/bin/{tool}" for tool in fleet_setup.SSH_TOOLS), [], 0),
        (
            "/l/bin/uv\n/usr/bin/git\n/usr/bin/python3",
            [
                "node",
                "claude",
                "codex",
                "gh",
            ],
            1,
        ),
    ],
)
def test_verify_names_each_tool_a_non_interactive_ssh_misses(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    output: str,
    absent: list[str],
    code: int,
) -> None:
    asked: list[tuple[str | None, str]] = []

    def fake(host: str | None, command: str, **_options: object) -> tuple[int, str]:
        asked.append((host, command))
        return (1 if absent else 0), output

    monkeypatch.setattr(fleet_setup, "on", fake)
    assert fleet_setup.missing_tools(output) == absent
    assert fleet_setup.check_tools("box") == code
    assert asked == [("box", fleet_setup.tools_command())]
    expected = f"missing {', '.join(absent)}" if absent else "ok      every tool on PATH"
    assert capsys.readouterr().out.splitlines()[-1] == expected
