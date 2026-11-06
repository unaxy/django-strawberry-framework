"""Script tests for ``scripts/fleet.py``, the machine list's one reader.

The tracked ``docs/fleet/machines.json`` loads; every schema rule of the list
refuses with a message naming the entry and the rule; :func:`fleet.machine`
refuses a name the list lacks; this machine is identified by its hostname
(macOS's ``scutil`` name first) and nothing else; every ssh call is built with
the one option set, keepalive included. Only ``subprocess.run`` and
``socket.gethostname`` are faked, the hostname boundary. A live ``/graphql/``
request has no wire shape for any of it, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from __future__ import annotations

import dataclasses
import json
import shlex
import socket
import subprocess
import sys
from typing import TYPE_CHECKING

import pytest

from scripts import fleet

if TYPE_CHECKING:
    from pathlib import Path


def _machine(name: str, os_name: str = "linux") -> fleet.Machine:
    return fleet.Machine(
        name=name,
        ssh=f"{name}-ssh",
        os=os_name,
        repo="~/projects/repo",
        weights={"light": 1.0, "heavy": 1.0},
        floors={"light": {}, "heavy": {}},
    )


def _write_list(tmp_path: Path, machines: list[dict[str, object]]) -> Path:
    path = tmp_path / "machines.json"
    _ = path.write_text(json.dumps({"machines": machines}), encoding="utf-8")
    return path


def _entry(name: str, os_name: str, **fields: object) -> dict[str, object]:
    return {
        "name": name,
        "ssh": name,
        "os": os_name,
        "repo": "~/projects/repo",
        "weight": {"light": 1, "heavy": 1},
        "floors": {"light": {}, "heavy": {}},
        **fields,
    }


def _checkout(tmp_path: Path, machines: list[dict[str, object]]) -> Path:
    """Return a checkout root under ``tmp_path`` holding ``machines`` as its list."""
    listed = tmp_path / fleet.MACHINES_PATH
    listed.parent.mkdir(parents=True)
    _ = _write_list(listed.parent, machines)
    return tmp_path


# -- the machine list ---------------------------------------------------------------------


def test_the_tracked_machine_list_loads_with_the_current_fleet() -> None:
    """The fleet file names every machine with both modes' weights."""
    machines = {machine.name: machine for machine in fleet.load_machines()}
    assert set(machines) >= {"rio-air", "rio-ubu", "rio-mini"}
    assert machines["rio-ubu"].os == "linux"
    assert machines["rio-air"].os == "macos"
    assert machines["rio-mini"].os == "macos"
    assert machines["rio-ubu"].floors["heavy"]["heavy_slots"] == 3
    assert machines["rio-air"].weights["heavy"] < machines["rio-ubu"].weights["heavy"]


@pytest.mark.parametrize(
    ("machines", "message"),
    [
        ([], "non-empty list"),
        ([_entry("a", "linux"), _entry("a", "linux")], "duplicate machine name(s) a"),
        ([_entry("a", "plan9")], "is not one of"),
        ([_entry("a", "linux", weight={"light": 1})], "no 'heavy' weight"),
        ([_entry("a", "linux", weight={"light": "1", "heavy": 1})], "must be a number"),
        ([_entry("a", "linux", weight={"light": True, "heavy": 1})], "must be a number"),
        (
            [_entry("a", "linux", weight={"light": 1, "heavy": 1, "medium": 1})],
            "unknown mode(s) medium",
        ),
        (
            [_entry("a", "macos", floors={"light": {"heavy_slots": 3}})],
            "heavy_slots cannot be measured on macos",
        ),
        (
            [_entry("a", "windows", floors={"heavy": {"max_psi_memory_full_avg10": 5}})],
            "cannot be measured on windows",
        ),
        ([_entry("a", "linux", ssh="")], "ssh must be a non-empty string"),
        ([_entry("a", "linux", ssh="-oProxyCommand=x")], "which ssh reads as an option"),
        (
            [_entry("a", "linux", weight={"light": float("nan"), "heavy": 1})],
            "weight.light must be a finite number of at least 0, got nan",
        ),
        (
            [_entry("a", "linux", weight={"light": -1, "heavy": 1})],
            "weight.light must be a finite number of at least 0",
        ),
        (
            [_entry("a", "linux", floors={"light": {"min_mem_available_gib": float("nan")}})],
            "min_mem_available_gib must be a finite number of at least 0, got nan",
        ),
        (
            [_entry("a", "linux", floors={"light": {"min_disk_free_gib": float("inf")}})],
            "min_disk_free_gib must be a finite number of at least 0, got inf",
        ),
        (
            [_entry("a", "linux", floors={"heavy": {"heavy_slots": 10**400}})],
            "heavy_slots must be finite",
        ),
        ([_entry("a", "linux", hostnames="box")], "hostnames must be a list"),
        ([_entry("a", "linux", hostnames=[""])], "hostnames must be a list"),
        (
            [
                _entry("a", "linux", hostnames=["Box.local"]),
                _entry("b", "macos", hostnames=["box"]),
            ],
            "hostname(s) box belong to more than one machine",
        ),
        ([_entry("a", "linux", floors=[])], "floors must be an object"),
    ],
)
def test_a_machine_list_breaking_the_schema_is_refused(
    tmp_path: Path,
    machines: list[dict[str, object]],
    message: str,
) -> None:
    """Each schema rule refuses with a message naming the entry and the rule."""
    with pytest.raises(fleet.MachineListError) as raised:
        _ = fleet.load_machines(_write_list(tmp_path, machines))
    assert message in str(raised.value)


def test_a_missing_or_non_json_machine_list_is_refused(tmp_path: Path) -> None:
    """Unreadable files are list errors, not tracebacks."""
    with pytest.raises(fleet.MachineListError):
        _ = fleet.load_machines(tmp_path / "absent.json")
    bad = tmp_path / "bad.json"
    _ = bad.write_text("{", encoding="utf-8")
    with pytest.raises(fleet.MachineListError):
        _ = fleet.load_machines(bad)


def test_machines_reads_the_list_of_the_checkout_named() -> None:
    """``machines(repo)`` is ``load_machines`` of that checkout's list, in file order."""
    assert fleet.machines() == fleet.load_machines(fleet.MACHINES_FILE)


def test_machines_of_another_checkout_reads_that_checkouts_list(tmp_path: Path) -> None:
    repo = _checkout(tmp_path, [_entry("b", "linux"), _entry("a", "macos")])
    assert [entry.name for entry in fleet.machines(repo)] == ["b", "a"]


def test_machine_returns_the_entry_of_that_name(tmp_path: Path) -> None:
    repo = _checkout(tmp_path, [_entry("a", "linux"), _entry("b", "macos")])
    found = fleet.machine("b", repo)
    assert (found.name, found.os) == ("b", "macos")


def test_machine_refuses_a_name_the_list_lacks_naming_the_list(tmp_path: Path) -> None:
    """No ``KeyError`` and no ``None``: a list error naming the file and what it holds."""
    repo = _checkout(tmp_path, [_entry("a", "linux"), _entry("b", "macos")])
    with pytest.raises(fleet.MachineListError) as raised:
        _ = fleet.machine("c", repo)
    message = str(raised.value)
    assert "no machine named 'c'" in message
    assert "listed: a, b" in message
    assert str(repo / fleet.MACHINES_PATH) in message


def test_machine_refuses_a_broken_list(tmp_path: Path) -> None:
    repo = _checkout(tmp_path, [_entry("a", "plan9")])
    with pytest.raises(fleet.MachineListError, match="is not one of"):
        _ = fleet.machine("a", repo)


# -- identity -----------------------------------------------------------------------------


def test_the_local_machine_is_the_one_whose_hostname_matches_or_the_one_named() -> None:
    """A hostname match ignores case and the domain; ``--here`` takes a name or an ssh host."""
    mac = dataclasses.replace(_machine("m", "macos"), hostnames=("laptop",))
    linux = dataclasses.replace(_machine("l"), hostnames=("desk",))
    assert fleet.local_machine([mac, linux], None, "Laptop.local") is mac
    assert fleet.local_machine([mac, linux], None, "desk") is linux
    assert fleet.local_machine([mac, linux], "l-ssh", "laptop") is linux
    with pytest.raises(fleet.MachineListError, match="names no machine"):
        _ = fleet.local_machine([mac], "nowhere", "laptop")


def test_an_unidentified_host_is_no_machine_even_when_one_shares_its_os() -> None:
    """The only Linux row is not this Linux box unless its hostname says so."""
    machines = fleet.load_machines()
    assert any(machine.os == "linux" for machine in machines)
    assert fleet.local_machine(machines, None, "unknown-linux-laptop") is None
    assert fleet.local_machine(machines, None, "rio-ubu.lan") is not None


def test_a_mac_is_named_by_its_local_host_name_not_the_network_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """On macOS the name comes from scutil, so a DHCP lease (``mac.lan`` at home) cannot rename it."""
    calls: list[list[str]] = []

    def scutil(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "Riordens-MacBook-Air\n", "")

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(subprocess, "run", scutil)
    monkeypatch.setattr(socket, "gethostname", lambda: "mac.lan")
    assert fleet.this_hostname() == "Riordens-MacBook-Air"
    assert calls == [["scutil", "--get", "LocalHostName"]]


@pytest.mark.parametrize(
    "outcome",
    [
        subprocess.CompletedProcess(["scutil"], 1, "", "no LocalHostName"),
        subprocess.CompletedProcess(["scutil"], 0, "  \n", ""),
        FileNotFoundError("scutil"),
        subprocess.TimeoutExpired(["scutil"], 5),
    ],
)
def test_a_mac_whose_scutil_gives_no_name_falls_back_to_the_network_name(
    monkeypatch: pytest.MonkeyPatch,
    outcome: subprocess.CompletedProcess[str] | Exception,
) -> None:
    def scutil(_argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(subprocess, "run", scutil)
    monkeypatch.setattr(socket, "gethostname", lambda: "mac.lan")
    assert fleet.this_hostname() == "mac.lan"


def test_off_macos_the_name_is_the_socket_hostname_and_scutil_never_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(subprocess, "run", refuse)
    monkeypatch.setattr(socket, "gethostname", lambda: "rio-ubu")
    assert fleet.this_hostname() == "rio-ubu"


# -- ssh ----------------------------------------------------------------------------------


def test_every_ssh_call_is_batch_mode_with_a_connect_timeout_and_a_keepalive() -> None:
    """A password prompt cannot hang a run, nor a peer silent for 45 seconds."""
    assert fleet.SSH_OPTIONS == (
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ServerAliveInterval=15",
        "-o",
        "ServerAliveCountMax=3",
    )


def test_ssh_argv_reaches_a_listed_machine_by_its_ssh_host() -> None:
    assert fleet.ssh_argv(_machine("l"), "sh -s -- 'x y'") == [
        "ssh",
        *fleet.SSH_OPTIONS,
        "l-ssh",
        "sh -s -- 'x y'",
    ]


def test_ssh_argv_reaches_an_unlisted_host_by_its_name() -> None:
    """A peer no row lists is reached by its MagicDNS name; the command stays one word."""
    assert fleet.ssh_argv("peer.tailnet.ts.net", "true") == [
        "ssh",
        *fleet.SSH_OPTIONS,
        "peer.tailnet.ts.net",
        "true",
    ]


def test_ssh_command_is_the_argv_prefix_as_one_shell_string() -> None:
    """Rsync ``-e`` and ``GIT_SSH_COMMAND`` split it back into the same words."""
    command = fleet.ssh_command()
    assert shlex.split(command) == ["ssh", *fleet.SSH_OPTIONS]
    assert shlex.split(command) == fleet.ssh_argv("h", "c")[:-2]
