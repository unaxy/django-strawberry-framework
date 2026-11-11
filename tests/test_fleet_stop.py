"""Script tests for ``docs/fleet/scripts/fleet_stop.py``, the one-command stop of fleet syncing."""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, fleet_stop

if TYPE_CHECKING:
    from pathlib import Path

ROWS = [
    {
        "name": "rio-air",
        "ssh": "rio-air",
        "repo": "~/projects/dsf",
        "aliases": "Air-Laptop",
    },
    {
        "name": "rio-mini",
        "ssh": "rio-mini",
        "repo": "~/projects/dsf",
        "aliases": "",
    },
]


def test_the_ssh_options_match_the_fleets() -> None:
    assert fleet_stop.SSH_OPTIONS == fleet.SSH_OPTIONS


def test_the_machine_list_is_read_from_its_json(tmp_path: Path) -> None:
    listed = tmp_path / "machines.json"
    listed.write_text(
        json.dumps(
            {
                "machines": [
                    {
                        "name": "rio-air",
                        "ssh": "rio-air",
                        "repo": "~/p",
                        "aliases": ["Air"],
                    },
                    {"name": "broken"},
                ],
            },
        ),
    )
    assert fleet_stop.machine_rows(listed) == [
        {
            "name": "rio-air",
            "ssh": "rio-air",
            "repo": "~/p",
            "aliases": "Air",
        },
    ]
    assert [row["name"] for row in fleet_stop.machine_rows()]


def test_this_machine_is_found_by_its_name_or_an_alias() -> None:
    assert fleet_stop.is_here(ROWS[0], {fleet_stop.MACHINE_ENV: "air-laptop"})
    assert not fleet_stop.is_here(ROWS[1], {fleet_stop.MACHINE_ENV: "rio-air"})


def _sh(line: str, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", line],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("tilde", [True, False], ids=["home-relative", "absolute"])
def test_the_remote_lines_stop_report_and_resume_a_checkout(
    tmp_path: Path,
    *,
    tilde: bool,
) -> None:
    checkout = tmp_path / "projects" / "dsf"
    checkout.mkdir(parents=True)
    repo = "~/projects/dsf" if tilde else str(checkout)
    text = fleet_stop.flag_text("runaway sync", "rio-air")
    assert _sh(fleet_stop.remote_line("stop", repo, text), tmp_path).returncode == 0
    flag = checkout / ".work" / "fleet-stop"
    assert json.loads(flag.read_text())["reason"] == "runaway sync"
    status = _sh(fleet_stop.remote_line("status", repo, text), tmp_path)
    assert "runaway sync" in status.stdout
    assert _sh(fleet_stop.remote_line("resume", repo, text), tmp_path).returncode == 0
    assert not flag.exists()
    assert _sh(fleet_stop.remote_line("status", repo, text), tmp_path).stdout.strip() == "clear"


def test_a_missing_checkout_fails_and_an_unsafe_repo_path_is_refused(tmp_path: Path) -> None:
    assert _sh(fleet_stop.remote_line("stop", "~/nowhere", "x"), tmp_path).returncode == 3
    with pytest.raises(ValueError, match="unsafe repo path"):
        _ = fleet_stop.remote_line("stop", "~/p; rm -rf ~", "x")


def test_stop_writes_here_first_then_reports_every_machine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(fleet_stop.MACHINE_ENV, "rio-air")
    called: list[tuple[str, str]] = []

    def remote(row: dict[str, str], action: str, text: str) -> str:
        assert json.loads(text)["by"] == "rio-air"
        called.append((row["name"], action))
        return "unreached (exit 255: timed out)"

    monkeypatch.setattr(fleet_stop, "apply_remote", remote)
    lines, reached = fleet_stop.run("stop", "runaway sync", ROWS, tmp_path)
    assert lines == [
        "rio-air (this machine): stopped",
        "rio-mini: unreached (exit 255: timed out)",
    ]
    assert not reached
    assert called == [("rio-mini", "stop")]
    assert json.loads((tmp_path / ".work" / "fleet-stop").read_text())["reason"] == "runaway sync"
    lines, _reached = fleet_stop.run("resume", "", ROWS, tmp_path)
    assert lines[0] == "rio-air (this machine): resumed"
    assert not (tmp_path / ".work" / "fleet-stop").exists()
