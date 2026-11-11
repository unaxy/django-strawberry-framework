"""Script tests for ``scripts/fleet_setup.py``, the one-command setup of a new fleet machine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from scripts import fleet, fleet_setup, fleet_stop

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


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
    picked = fleet_setup.select(["checkout", "uv", "ssh-key"], ["keys"])
    assert [step.key for step in picked] == ["uv", "checkout"]


def test_select_refuses_an_unknown_step_or_kind() -> None:
    with pytest.raises(ValueError, match="nope, root"):
        _ = fleet_setup.select(["nope"], ["root"])


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
