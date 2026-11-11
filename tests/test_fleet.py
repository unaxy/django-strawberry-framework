"""Script tests for ``docs/fleet/scripts/fleet.py``, the machine list's one reader.

The tracked ``docs/fleet/machines.json`` loads; every schema rule of the list
refuses with a message naming the entry and the rule; :func:`fleet.machine`
refuses a name the list lacks; this machine is the row named by its override
or its hostname (macOS's ``scutil`` name first) and nothing else, an alias
included; a stored name reads as the row whose name or alias it is; a host
name reaches the row whose name, alias or ssh host it is; every ssh call is
built with the one option set, keepalive included; the login a host is reached
as is ``ssh -G``'s. Only ``subprocess.run`` and
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

from docs.fleet.scripts import fleet

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
        ([_entry("a", "linux", aliases="box")], "aliases must be a list"),
        ([_entry("a", "linux", aliases=[""])], "aliases must be a list"),
        (
            [_entry("a", "linux", aliases=["Box.local"]), _entry("b", "macos", aliases=["box"])],
            "name(s) box listed more than once",
        ),
        (
            [_entry("a", "linux"), _entry("b", "macos", aliases=["A"])],
            "name(s) a listed more than once",
        ),
        ([_entry("a", "linux", aliases=["a.lan"])], "name(s) a listed more than once"),
        ([_entry(".", "linux")], "name '.' is empty before its first dot"),
        ([_entry(".local", "linux")], "name '.local' is empty before its first dot"),
        ([_entry("a", "linux", aliases=[".x"])], "aliases: '.x' empty before the first dot"),
        ([_entry(" ", "linux")], "name ' ' is empty before its first dot"),
        ([_entry("a", "linux", aliases=[" "])], "aliases: ' ' empty before the first dot"),
        (
            [_entry("a", "linux", hostnames=["a"])],
            "unknown key hostnames; former names go in aliases",
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


def test_the_local_machine_is_the_one_whose_name_matches_or_the_one_named() -> None:
    """A hostname matches a row's name, ignoring case and the domain, never an alias.

    ``--here`` takes a name, an ssh host or an alias.
    """
    mac = dataclasses.replace(_machine("laptop", "macos"), aliases=("old-laptop",))
    linux = _machine("desk")
    assert fleet.local_machine([mac, linux], None, "Laptop.local") is mac
    assert fleet.local_machine([mac, linux], None, "desk") is linux
    assert fleet.local_machine([mac, linux], None, "Old-Laptop.local") is None
    assert fleet.local_machine([mac, linux], "desk-ssh", "laptop") is linux
    assert fleet.local_machine([mac, linux], "Old-Laptop", None) is mac
    with pytest.raises(fleet.MachineListError, match="names no machine"):
        _ = fleet.local_machine([mac], "nowhere", "laptop")


def test_an_unidentified_host_is_no_machine_even_when_one_shares_its_os() -> None:
    """The only Linux row is not this Linux box unless its hostname says so."""
    machines = fleet.load_machines()
    assert any(machine.os == "linux" for machine in machines)
    assert fleet.local_machine(machines, None, "unknown-linux-laptop") is None
    assert fleet.local_machine(machines, None, "rio-ubu.lan") is not None


def _named(monkeypatch: pytest.MonkeyPatch, hostname: str, override: str | None = None) -> None:
    """Make this machine's hostname ``hostname`` and its override ``override`` (none: unset)."""
    monkeypatch.setattr(fleet, "this_hostname", lambda: hostname)
    if override is None:
        monkeypatch.delenv(fleet.MACHINE_ENV, raising=False)
    else:
        monkeypatch.setenv(fleet.MACHINE_ENV, override)


ALIASED = [
    _entry("rio-ubu", "linux"),
    _entry("rio-air", "macos", aliases=["Riordens-MacBook-Air"]),
]


@pytest.mark.parametrize(
    ("hostname", "override", "expected"),
    [
        ("Rio-Air.local", None, "rio-air"),
        ("Riordens-MacBook-Air", None, None),
        ("stranger", "RIO-UBU", "rio-ubu"),
        ("rio-air", "fake-b", None),
    ],
)
def test_the_local_machine_by_default_is_named_as_this_machine_is(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: str,
    override: str | None,
    expected: str | None,
) -> None:
    """One raw name for both: the override, else the hostname; a row's name only, else none.

    An explicit ``hostname`` still wins over both.
    """
    repo = _checkout(tmp_path, ALIASED)
    listed = fleet.machines(repo)
    _named(monkeypatch, hostname, override)
    found = fleet.local_machine(listed, None)
    assert (found.name if found is not None else None) == expected
    if expected is not None:
        assert fleet.this_machine(listed) is found
    explicit = fleet.local_machine(listed, None, "rio-ubu")
    assert explicit is not None
    assert explicit.name == "rio-ubu"


@pytest.mark.parametrize(
    ("stored", "expected"),
    [
        ("rio-air", "rio-air"),
        ("riordens-macbook-air", "rio-air"),
        ("Riordens-MacBook-Air.local", "rio-air"),
        ("Rio-Ubu.lan", "rio-ubu"),
        ("Stranger.lan", "stranger"),
        ("", ""),
        (".", ""),
        (".local", ""),
        (" ", ""),
        (" Rio-Air.lan ", "rio-air"),
    ],
)
def test_a_stored_name_reads_as_the_row_whose_name_or_alias_it_is(
    tmp_path: Path,
    stored: str,
    expected: str,
) -> None:
    """Up to its first dot, casefolded; a name no row holds stays itself."""
    repo = _checkout(tmp_path, ALIASED)
    assert fleet.canonical(stored, repo=repo) == expected
    assert fleet.canonical(stored, fleet.machines(repo)) == expected


@pytest.mark.parametrize("listed", [None, [_entry("a", "plan9")]])
def test_a_stored_name_reads_as_itself_short_when_the_list_is_unreadable(
    tmp_path: Path,
    listed: list[dict[str, object]] | None,
) -> None:
    """``canonical`` never raises: a missing or broken list resolves nothing."""
    repo = tmp_path if listed is None else _checkout(tmp_path, listed)
    assert fleet.canonical("Riordens-MacBook-Air.local", repo=repo) == "riordens-macbook-air"


def test_this_machine_is_the_row_named_by_its_hostname_or_its_override(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _checkout(tmp_path, ALIASED)
    _named(monkeypatch, "Rio-Air.local")
    assert fleet.this_machine(repo=repo).name == "rio-air"
    assert fleet.this_machine_name(repo=repo) == "rio-air"
    _named(monkeypatch, "Rio-Air.local", "RIO-UBU")
    assert fleet.this_machine(fleet.machines(repo)).name == "rio-ubu"
    assert fleet.this_machine_name(repo=repo) == "rio-ubu"


@pytest.mark.parametrize(
    (
        "hostname",
        "override",
        "raw",
        "source",
    ),
    [
        (
            "stranger.lan",
            None,
            "stranger",
            "its hostname",
        ),
        (
            "Riordens-MacBook-Air.local",
            None,
            "riordens-macbook-air",
            "its hostname",
        ),
        (
            "rio-air",
            "fake-b",
            "fake-b",
            "$DSF_MACHINE_ID",
        ),
    ],
)
def test_this_machine_refuses_a_host_no_row_is_named_by_an_alias_included(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: str,
    override: str | None,
    raw: str,
    source: str,
) -> None:
    """An alias resolves old records, never the live machine: the message names both sides."""
    repo = _checkout(tmp_path, ALIASED)
    _named(monkeypatch, hostname, override)
    with pytest.raises(fleet.MachineListError) as raised:
        _ = fleet.this_machine(repo=repo)
    message = str(raised.value)
    assert f"this machine is {raw!r} ({source})" in message
    assert "listed: rio-ubu, rio-air" in message


@pytest.mark.parametrize(
    ("hostname", "override", "source"),
    [("rio-air", ".", "$DSF_MACHINE_ID"), (".local", None, "its hostname")],
)
def test_an_empty_raw_name_is_no_machine(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: str,
    override: str | None,
    source: str,
) -> None:
    """Empty before its first dot: ``this_machine`` refuses naming the source, no row matches."""
    repo = _checkout(tmp_path, ALIASED)
    listed = fleet.machines(repo)
    _named(monkeypatch, hostname, override)
    with pytest.raises(fleet.MachineListError) as raised:
        _ = fleet.this_machine(repo=repo)
    assert f"this machine has no name: {source} is empty" in str(raised.value)
    assert fleet.this_machine_name(repo=repo) == ""
    assert fleet.local_machine(listed, None) is None


def test_an_empty_name_never_resolves_even_through_a_list_the_parser_did_not_check() -> None:
    nameless = dataclasses.replace(_machine("."), aliases=("",))
    assert fleet.canonical("", [nameless]) == ""
    assert fleet.canonical(".x", [nameless]) == ""


def test_this_machine_refuses_an_unreadable_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _named(monkeypatch, "rio-air")
    with pytest.raises(fleet.MachineListError):
        _ = fleet.this_machine(repo=tmp_path)


@pytest.mark.parametrize(
    ("hostname", "override", "expected"),
    [
        ("Riordens-MacBook-Air.local", None, "rio-air"),
        ("Stranger.lan", None, "stranger"),
        ("rio-air", "Fake-B", "fake-b"),
    ],
)
def test_this_machine_name_falls_back_to_the_stored_name_rule_on_an_unlisted_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    hostname: str,
    override: str | None,
    expected: str,
) -> None:
    """No row named: the raw name read through ``canonical`` (an alias: its row), never an error."""
    repo = _checkout(tmp_path, ALIASED)
    _named(monkeypatch, hostname, override)
    assert fleet.this_machine_name(repo=repo) == expected


def test_this_machine_name_never_raises_on_an_unreadable_list(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _named(monkeypatch, "Rio-Air.local")
    assert fleet.this_machine_name(repo=tmp_path) == "rio-air"


def test_the_tracked_list_resolves_each_machines_former_name() -> None:
    """Each Mac's alias, the name older records store, reads as its row."""
    assert fleet.canonical("Riordens-MacBook-Air") == "rio-air"
    assert fleet.canonical("Rios-Mac-mini.local") == "rio-mini"
    assert fleet.canonical("rio-ubu") == "rio-ubu"


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


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("rio-ubu", "rio-ubu"),
        ("Rio-Ubu.tail.ts.net", "rio-ubu"),
        ("riordens-macbook-air.local", "rio-air"),
        ("air-ssh", "rio-air"),
        ("AIR-SSH.lan", "rio-air"),
        ("stranger", None),
        ("", None),
        (".lan", None),
    ],
)
def test_a_host_name_reaches_the_row_whose_name_alias_or_ssh_host_it_is(
    tmp_path: Path,
    host: str,
    expected: str | None,
) -> None:
    repo = _checkout(
        tmp_path,
        [
            _entry("rio-ubu", "linux"),
            _entry("rio-air", "macos", ssh="air-ssh", aliases=["Riordens-MacBook-Air"]),
        ],
    )
    found = fleet.reached_as(host, fleet.machines(repo))
    assert (found.name if found is not None else None) == expected


@pytest.mark.parametrize(
    ("returncode", "stdout", "expected"),
    [
        (0, "hostname rio-ubu\nuser desk\nport 22\n", "desk"),
        (0, "hostname rio-ubu\nport 22\n", None),
        (255, "user desk\n", None),
    ],
)
def test_ssh_user_is_the_user_line_ssh_dash_g_prints(
    monkeypatch: pytest.MonkeyPatch,
    returncode: int,
    stdout: str,
    expected: str | None,
) -> None:
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, returncode, stdout, "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert fleet.ssh_user("rio-ubu") == expected
    assert calls == [["ssh", "-G", "rio-ubu"]]


@pytest.mark.parametrize("host", ["", "-oProxyCommand=x"])
def test_ssh_user_never_hands_ssh_an_option_or_nothing(
    monkeypatch: pytest.MonkeyPatch,
    host: str,
) -> None:
    def no_run(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        pytest.fail("ssh ran")

    monkeypatch.setattr(subprocess, "run", no_run)
    assert fleet.ssh_user(host) is None


@pytest.mark.parametrize("error", [OSError("no ssh"), subprocess.TimeoutExpired("ssh", 10)])
def test_ssh_user_is_none_when_ssh_is_missing_or_hangs(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
) -> None:
    def failing(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise error

    monkeypatch.setattr(subprocess, "run", failing)
    assert fleet.ssh_user("rio-ubu") is None
