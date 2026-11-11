"""Script tests for ``docs/fleet/scripts/load_balancing.py``, the fleet machine picker.

Each OS's probe output is parsed from text captured on a fleet machine (Windows
from the shape ``ConvertTo-Json -Compress`` prints), then scored and held to
its floors; every disk floor of the tracked machine list leaves room for a
workspace copy (the list's schema is ``tests/test_fleet.py``'s); the CLI's
``--pick``, ``--json`` and table outputs run end to end with only
``subprocess.run`` faked, which is the ssh and local probe boundary. A live
``/graphql/`` request has no wire shape for picking a machine, so there is no
live sibling in ``examples/fakeshop/test_query/``.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import subprocess
from typing import TYPE_CHECKING

import pytest

from docs.fleet.scripts import fleet, load_balancing
from scripts import workspace

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads

LINUX_OUTPUT = """\
@@ uname
Linux
@@ loadavg
3.00 0.02 0.00 1/1398 709663
@@ nproc
12
@@ meminfo
MemTotal:       48208256 kB
MemFree:        40000000 kB
MemAvailable:   43805424 kB
SwapTotal:       8388604 kB
SwapFree:        8388604 kB
@@ psi_memory
some avg10=0.00 avg60=0.00 avg300=0.00 total=53
full avg10=1.25 avg60=0.00 avg300=0.00 total=51
@@ heavy_jobs
1
@@ df
Filesystem     1024-blocks     Used Available Capacity Mounted on
/dev/nvme1n1p2   238169856 43549632 182449064      20% /
"""

MACOS_OUTPUT = """\
@@ uname
Darwin
@@ sysctl
hw.logicalcpu: 8
hw.memsize: 17179869184
vm.loadavg: { 7.22 6.70 5.52 }
kern.memorystatus_level: 51
kern.memorystatus_vm_pressure_level: 1
@@ df
Filesystem   1024-blocks      Used Available Capacity  Mounted on
/dev/disk3s5   239362496 186873464  18465632    92%    /System/Volumes/Data
"""

WINDOWS_OUTPUT = (
    "@@ windows\r\n"
    '{"logical_processors":16,"load_percentage":25.5,"free_physical_kib":8388608,'
    '"total_visible_kib":33554432,"disk_free_bytes":107374182400}\r\n'
)

GIB = 1024**3


def _measurement(**overrides: float | None) -> load_balancing.Measurement:
    values: dict[str, float | None] = {
        "threads": 10,
        "cpu_busy": 0.5,
        "mem_total_bytes": 40 * GIB,
        "mem_available_bytes": 20 * GIB,
        "disk_free_bytes": 100 * GIB,
        "psi_memory_full_avg10": 0.0,
        "vm_pressure_level": 1,
        "heavy_jobs": 0,
        **overrides,
    }

    def number(key: str) -> float:
        value = values[key]
        assert value is not None
        return value

    def optional(key: str) -> float | None:
        return values[key]

    psi = optional("psi_memory_full_avg10")
    level = optional("vm_pressure_level")
    jobs = optional("heavy_jobs")
    return load_balancing.Measurement(
        os="linux",
        threads=int(number("threads")),
        cpu_busy=number("cpu_busy"),
        mem_total_bytes=int(number("mem_total_bytes")),
        mem_available_bytes=int(number("mem_available_bytes")),
        disk_free_bytes=int(number("disk_free_bytes")),
        psi_memory_full_avg10=psi,
        vm_pressure_level=None if level is None else int(level),
        heavy_jobs=None if jobs is None else int(jobs),
    )


def _machine(
    name: str,
    os_name: str = "linux",
    *,
    light: float = 1.0,
    heavy: float = 1.0,
    floors: dict[str, dict[str, float]] | None = None,
) -> fleet.Machine:
    return fleet.Machine(
        name=name,
        ssh=f"{name}-ssh",
        os=os_name,
        repo="~/projects/repo",
        weights={"light": light, "heavy": heavy},
        floors=floors or {"light": {}, "heavy": {}},
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


# -- parsing ------------------------------------------------------------------------------


def test_linux_output_parses_into_load_memory_psi_heavy_jobs_and_disk() -> None:
    """Load over threads is busy CPU; MemAvailable, PSI full avg10, live jobs and df Available."""
    measured = load_balancing.parse_linux(LINUX_OUTPUT)
    assert measured.os == "linux"
    assert measured.threads == 12
    assert measured.cpu_busy == pytest.approx(0.25)
    assert measured.mem_total_bytes == 48208256 * 1024
    assert measured.mem_available_bytes == 43805424 * 1024
    assert measured.psi_memory_full_avg10 == pytest.approx(1.25)
    assert measured.heavy_jobs == 1
    assert measured.disk_free_bytes == 182449064 * 1024


def test_linux_output_without_psi_leaves_it_unmeasured() -> None:
    """A kernel without ``/proc/pressure`` prints an empty section: PSI is ``None``, not 0."""
    output = LINUX_OUTPUT.replace("some avg10=0.00 avg60=0.00 avg300=0.00 total=53\n", "")
    output = output.replace("full avg10=1.25 avg60=0.00 avg300=0.00 total=51\n", "")
    assert load_balancing.parse_linux(output).psi_memory_full_avg10 is None


def test_macos_output_parses_the_kernel_free_percentage_of_physical_memory() -> None:
    """Available memory is ``kern.memorystatus_level`` percent of ``hw.memsize``."""
    measured = load_balancing.parse_macos(MACOS_OUTPUT)
    assert measured.os == "macos"
    assert measured.threads == 8
    assert measured.cpu_busy == pytest.approx(7.22 / 8)
    assert measured.mem_total_bytes == 17179869184
    assert measured.mem_available_bytes == 17179869184 * 51 // 100
    assert measured.vm_pressure_level == 1
    assert measured.disk_free_bytes == 18465632 * 1024
    assert measured.psi_memory_full_avg10 is None


def test_windows_output_parses_the_cim_json() -> None:
    """LoadPercentage is busy CPU; the KiB memory counters and the drive's free bytes."""
    measured = load_balancing.parse_windows(WINDOWS_OUTPUT)
    assert measured.os == "windows"
    assert measured.threads == 16
    assert measured.cpu_busy == pytest.approx(0.255)
    assert measured.mem_available_bytes == 8 * GIB
    assert measured.mem_total_bytes == 32 * GIB
    assert measured.disk_free_bytes == 100 * GIB


@pytest.mark.parametrize(
    ("parser", "output"),
    [
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.split("@@ df", maxsplit=1)[0],
            id="linux-no-df",
        ),
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.replace("MemAvailable", "MemSomething"),
            id="linux-no-memavailable",
        ),
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.replace("\n12\n", "\n0\n"),
            id="zero",
        ),
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.replace("full avg10=1.25", "full avg10=oops"),
            id="linux-psi-not-a-number",
        ),
        pytest.param(
            load_balancing.parse_macos,
            MACOS_OUTPUT.replace("kern.memorystatus_level: 51\n", ""),
            id="macos-no-level",
        ),
        pytest.param(load_balancing.parse_windows, "@@ windows\n{not json\n", id="windows-json"),
        pytest.param(load_balancing.parse_windows, "@@ windows\n[1]\n", id="windows-array"),
        pytest.param(
            load_balancing.parse_windows,
            WINDOWS_OUTPUT.replace('"load_percentage":25.5', '"load_percentage":null'),
            id="windows-no-load",
        ),
        pytest.param(load_balancing.parse_windows, "", id="windows-empty"),
        pytest.param(
            load_balancing.parse_windows,
            WINDOWS_OUTPUT.replace("107374182400", "1e400"),
            id="windows-infinite-disk",
        ),
        pytest.param(
            load_balancing.parse_windows,
            WINDOWS_OUTPUT.replace("25.5", "1" + "0" * 400),
            id="windows-huge-load",
        ),
        pytest.param(
            load_balancing.parse_windows,
            WINDOWS_OUTPUT.replace("8388608", "99999999"),
            id="windows-more-free-than-total",
        ),
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.replace("MemTotal:       48208256", "MemTotal:       0"),
            id="linux-no-memory",
        ),
        pytest.param(
            load_balancing.parse_linux,
            LINUX_OUTPUT.replace("3.00 0.02", "NaN 0.02"),
            id="linux-nan-load",
        ),
    ],
)
def test_unreadable_probe_output_raises_probe_output_error(
    parser: Callable[[str], load_balancing.Measurement],
    output: str,
) -> None:
    """Every missing or malformed value the measurement needs is a ``ProbeOutputError``."""
    with pytest.raises(load_balancing.ProbeOutputError):
        _ = parser(output)


# -- scoring and floors -------------------------------------------------------------------


def test_score_is_the_weighted_mean_of_free_cpu_and_free_memory() -> None:
    """``weight * (cpu_free + mem_free) / 2``, CPU clamped when the load exceeds the threads."""
    assert load_balancing.score(_measurement(cpu_busy=0.25), 0.5) == pytest.approx(
        0.5 * (0.75 + 0.5) / 2,
    )
    assert load_balancing.score(_measurement(cpu_busy=1.5), 1.0) == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"cpu_busy": float("nan")}, "impossible cpu load nan"),
        ({"cpu_busy": float("inf")}, "impossible cpu load inf"),
        ({"cpu_busy": -0.1}, "impossible cpu load"),
        ({"threads": 0}, "0 threads"),
        ({"mem_total_bytes": 0, "mem_available_bytes": 0}, "0 B memory"),
        ({"mem_available_bytes": 41 * GIB}, "available of"),
        ({"disk_free_bytes": -1}, "impossible free disk"),
        ({"psi_memory_full_avg10": float("nan")}, "impossible PSI memory full"),
        ({"heavy_jobs": -1}, "impossible heavy jobs"),
        ({"vm_pressure_level": -1}, "impossible memory pressure level"),
    ],
)
def test_a_measurement_no_machine_can_have_is_refused(
    overrides: dict[str, float | None],
    message: str,
) -> None:
    """Non-finite, negative, empty or self-contradicting values never reach a score."""
    with pytest.raises(load_balancing.ProbeOutputError, match="impossible") as raised:
        _ = _measurement(**overrides)
    assert message in str(raised.value)


def test_a_count_past_float_range_is_refused_without_overflowing() -> None:
    """A probe's integer too large for a float is an impossible value, not an ``OverflowError``."""
    with pytest.raises(load_balancing.ProbeOutputError, match="impossible free disk"):
        _ = _measurement(disk_free_bytes=float(2**63))
    output = LINUX_OUTPUT.replace("182449064", "9" * 400)
    with pytest.raises(load_balancing.ProbeOutputError, match="impossible free disk"):
        _ = load_balancing.parse_linux(output)


@pytest.mark.parametrize(
    ("floors", "overrides", "reason"),
    [
        ({"min_mem_available_gib": 21}, {}, "20.0 GiB RAM available, floor 21"),
        ({"min_disk_free_gib": 101}, {}, "100.0 GiB disk free, floor 101"),
        ({"max_psi_memory_full_avg10": 5}, {"psi_memory_full_avg10": 6.5}, "memory thrashing"),
        ({"max_psi_memory_full_avg10": 5}, {"psi_memory_full_avg10": None}, "PSI memory"),
        ({"heavy_slots": 3}, {"heavy_jobs": 3}, "heavy slots full (3/3)"),
        ({"heavy_slots": 3}, {"heavy_jobs": None}, "heavy jobs unmeasured"),
        ({"max_vm_pressure_level": 1}, {"vm_pressure_level": 2}, "memory pressure level 2"),
        ({"max_vm_pressure_level": 1}, {"vm_pressure_level": None}, "pressure level unmeasured"),
    ],
)
def test_each_floor_breach_names_its_reason(
    floors: dict[str, float],
    overrides: dict[str, float | None],
    reason: str,
) -> None:
    """A breached or unmeasured floor yields exactly one reason naming it."""
    reasons = load_balancing.floor_breaches(_measurement(**overrides), floors)
    assert len(reasons) == 1
    assert reason in reasons[0]


def test_a_measurement_clearing_every_floor_has_no_breach() -> None:
    """At the floor is not under it; jobs below the slot count leave a slot."""
    floors = {
        "min_mem_available_gib": 20.0,
        "min_disk_free_gib": 100.0,
        "max_psi_memory_full_avg10": 0.0,
        "heavy_slots": 3.0,
        "max_vm_pressure_level": 1.0,
    }
    assert load_balancing.floor_breaches(_measurement(heavy_jobs=2), floors) == []


def test_judge_disqualifies_a_breach_or_a_zero_weight_and_keeps_the_score() -> None:
    """A disqualified machine still reports its score; an unreachable one reports none."""
    machine = _machine("a", heavy=0.0, floors={"light": {"min_disk_free_gib": 500}, "heavy": {}})
    light = load_balancing.judge(machine, _measurement(), "light", local=False)
    heavy = load_balancing.judge(machine, _measurement(), "heavy", local=False)
    gone = load_balancing.judge(machine, "unreachable over ssh a-ssh: x", "light", local=False)
    assert (light.status, light.score) == ("disqualified", pytest.approx(0.5))
    assert heavy.status == "disqualified"
    assert heavy.reasons == ("weight 0 for heavy work",)
    assert (gone.status, gone.score, gone.measurement) == ("unreachable", None, None)


def test_rank_orders_qualifying_by_score_then_disqualified_then_unreachable() -> None:
    """Ties keep list order."""
    first, second, third, fourth = (_machine(name) for name in "abcd")
    verdicts = [
        load_balancing.judge(first, "down", "light", local=False),
        load_balancing.judge(
            _machine("x", floors={"light": {"min_disk_free_gib": 999}, "heavy": {}}),
            _measurement(),
            "light",
            local=False,
        ),
        load_balancing.judge(second, _measurement(cpu_busy=0.9), "light", local=False),
        load_balancing.judge(third, _measurement(cpu_busy=0.1), "light", local=False),
        load_balancing.judge(fourth, _measurement(cpu_busy=0.1), "light", local=False),
    ]
    ranked = [verdict.machine.name for verdict in load_balancing.rank(verdicts)]
    assert ranked == [
        "c",
        "d",
        "b",
        "x",
        "a",
    ]


# -- machine list -------------------------------------------------------------------------


def test_every_disk_floor_leaves_room_for_a_workspace_copy() -> None:
    """A thread may bind a ``workspace.py`` copy, which refuses under its free-disk guard."""
    guard = workspace.MIN_FREE_BYTES / GIB
    for machine in fleet.load_machines():
        for mode in fleet.MODES:
            assert machine.floors[mode].get("min_disk_free_gib", 0) >= guard, (machine.name, mode)


# -- probe commands and the subprocess boundary -------------------------------------------


def test_a_remote_probe_is_one_fleet_ssh_call_with_the_script_on_stdin() -> None:
    """The fleet's ssh options (batch mode, connect timeout, keepalive); ``repo`` is shell-quoted."""
    argv, stdin = load_balancing.probe_command(_machine("l"), local=False)
    assert argv == [
        "ssh",
        *fleet.SSH_OPTIONS,
        "l-ssh",
        "sh -s -- '~/projects/repo'",
    ]
    assert "ServerAliveInterval=15" in argv
    assert stdin == load_balancing.LINUX_PROBE


def test_a_local_probe_runs_the_same_script_without_ssh() -> None:
    """The local machine is measured by ``sh`` directly."""
    argv, stdin = load_balancing.probe_command(_machine("m", "macos"), local=True)
    assert argv == [
        "sh",
        "-s",
        "--",
        "~/projects/repo",
    ]
    assert stdin == load_balancing.MACOS_PROBE


def test_a_windows_probe_is_an_encoded_powershell_command_holding_the_quoted_repo() -> None:
    """The script travels UTF-16LE base64, the repo as a PowerShell single-quoted literal."""
    machine = dataclasses.replace(_machine("w", "windows"), repo="C:\\it's\\repo")
    argv, stdin = load_balancing.probe_command(machine, local=False)
    assert stdin is None
    assert argv[:-1] == ["ssh", *fleet.SSH_OPTIONS, "w-ssh"]
    words = argv[-1].split()
    assert words[:4] == [
        "powershell",
        "-NoProfile",
        "-NonInteractive",
        "-EncodedCommand",
    ]
    script = base64.b64decode(words[4]).decode("utf-16-le")
    assert "$repo = 'C:\\it''s\\repo'" in script
    assert "Get-CimInstance -ClassName Win32_Processor" in script
    local_argv, _ = load_balancing.probe_command(machine, local=True)
    assert local_argv == words


class _FakeRun:
    """``subprocess.run`` answering each argv from a host-to-result table."""

    def __init__(self, results: dict[str, tuple[int, str, str] | BaseException]) -> None:
        self.results: dict[str, tuple[int, str, str] | BaseException] = results
        self.calls: list[list[str]] = []

    def host(self, argv: list[str]) -> str:
        return argv[1 + len(fleet.SSH_OPTIONS)] if argv[0] == "ssh" else "local"

    def __call__(self, argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(argv))
        result = self.results[self.host(argv)]
        if isinstance(result, BaseException):
            raise result
        code, stdout, stderr = result
        return subprocess.CompletedProcess(argv, code, stdout, stderr)


def _patch(monkeypatch: pytest.MonkeyPatch, fake: _FakeRun) -> None:
    """Route every subprocess to ``fake``, on a host no machine list names (no scutil call)."""
    monkeypatch.setattr(subprocess, "run", fake)
    monkeypatch.setattr(fleet, "this_hostname", lambda: "stranger")
    monkeypatch.delenv(fleet.MACHINE_ENV, raising=False)


@pytest.mark.parametrize(
    ("result", "reason"),
    [
        ((255, "", "ssh: connect to host l-ssh: Operation timed out\n"), "unreachable over ssh"),
        ((1, "", "df: /nope: No such file\n"), "probe failed (exit 1): df: /nope"),
        ((0, "@@ uname\nLinux\n", ""), "no meminfo output"),
        ((0, MACOS_OUTPUT, ""), "probe ran on macos, the machine list says linux"),
        (subprocess.TimeoutExpired(["ssh"], 30), "probe timed out after 30s"),
        (FileNotFoundError(2, "No such file", "ssh"), "cannot run ssh"),
    ],
)
def test_a_failed_probe_is_a_reason_never_an_exception(
    monkeypatch: pytest.MonkeyPatch,
    result: tuple[int, str, str] | BaseException,
    reason: str,
) -> None:
    """The ssh exit 255, a probe error, bad output, a wrong OS, a timeout and a missing ssh."""
    _patch(monkeypatch, _FakeRun({"l-ssh": result}))
    measured = load_balancing.measure(_machine("l"), local=False)
    assert isinstance(measured, str)
    assert reason in measured


# -- CLI ----------------------------------------------------------------------------------


def _fleet(tmp_path: Path) -> Path:
    return _write_list(
        tmp_path,
        [
            _entry(
                "desk",
                "linux",
                weight={"light": 1, "heavy": 1},
                floors={"heavy": {"heavy_slots": 1}},
            ),
            _entry("mac", "macos", weight={"light": 0.5, "heavy": 0.1}),
            _entry("win", "windows"),
        ],
    )


def test_pick_prints_the_winning_ssh_host_after_one_probe_per_machine(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The local Mac runs without ssh; each remote host gets exactly one ssh call."""
    fake = _FakeRun(
        {
            "local": (0, MACOS_OUTPUT, ""),
            "desk": (0, LINUX_OUTPUT, ""),
            "win": (255, "", "ssh: connect to host win port 22: Connection refused\n"),
        },
    )
    _patch(monkeypatch, fake)
    code = load_balancing.main(
        [
            "--pick",
            "--machines",
            str(_fleet(tmp_path)),
            "--here",
            "mac",
        ],
    )
    assert (code, capsys.readouterr().out) == (0, "desk\n")
    assert sorted(fake.host(call) for call in fake.calls) == ["desk", "local", "win"]


def test_heavy_pick_with_no_qualifying_machine_exits_nonzero_and_says_why(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Slots full on the desktop and critical memory pressure on the Mac leave no pick."""
    busy_mac = MACOS_OUTPUT.replace(
        "memorystatus_vm_pressure_level: 1",
        "memorystatus_vm_pressure_level: 4",
    )
    path = _write_list(
        tmp_path,
        [
            _entry("desk", "linux", floors={"heavy": {"heavy_slots": 1}}),
            _entry("mac", "macos", floors={"heavy": {"max_vm_pressure_level": 2}}),
        ],
    )
    _patch(monkeypatch, _FakeRun({"local": (0, busy_mac, ""), "desk": (0, LINUX_OUTPUT, "")}))
    code = load_balancing.main(
        [
            "--pick",
            "--heavy",
            "--machines",
            str(path),
            "--here",
            "mac",
        ],
    )
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert "no machine qualifies for heavy work" in captured.err
    assert "heavy slots full (1/1)" in captured.err
    assert "memory pressure level 4, limit 2" in captured.err


def test_json_reports_every_machine_with_status_reasons_and_measurement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """One document: the mode, the pick, then each machine in rank order."""
    _patch(
        monkeypatch,
        _FakeRun(
            {
                "local": (0, LINUX_OUTPUT, ""),
                "mac": (0, MACOS_OUTPUT, ""),
                "win": (0, WINDOWS_OUTPUT, ""),
            },
        ),
    )
    code = load_balancing.main(
        [
            "--json",
            "--machines",
            str(_fleet(tmp_path)),
            "--here",
            "desk",
        ],
    )
    document = _loads(capsys.readouterr().out)
    assert code == 0
    assert fleet.is_json_object(document)
    assert document["mode"] == "light"
    assert document["pick"] == "desk"
    machines = document["machines"]
    assert fleet.is_json_array(machines)
    rows = [row for row in machines if fleet.is_json_object(row)]
    assert [(row["name"], row["status"], row["local"]) for row in rows] == [
        ("desk", "ok", True),
        ("win", "ok", False),
        ("mac", "ok", False),
    ]
    measurement = rows[0]["measurement"]
    assert fleet.is_json_object(measurement)
    assert measurement["heavy_jobs"] == 1
    assert measurement["cpu_free"] == pytest.approx(0.75)


def test_the_table_ranks_qualifying_machines_and_lists_every_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Qualifying rows are numbered, the rest show ``-`` and their reasons below."""
    _patch(
        monkeypatch,
        _FakeRun(
            {
                "local": (0, MACOS_OUTPUT, ""),
                "desk": (0, LINUX_OUTPUT, ""),
                "win": (255, "", "ssh: Could not resolve hostname win\n"),
            },
        ),
    )
    code = load_balancing.main(
        [
            "--heavy",
            "--machines",
            str(_fleet(tmp_path)),
            "--here",
            "mac",
        ],
    )
    lines = capsys.readouterr().out.splitlines()
    assert code == 0
    assert lines[0] == "mode: heavy"
    assert lines[1].split()[:3] == ["rank", "machine", "os"]
    assert lines[2].split()[:3] == ["1", "mac", "(here)"]
    assert lines[3].split()[:2] == ["-", "desk"]
    assert lines[4].split()[:2] == ["-", "win"]
    assert "  desk disqualified: heavy slots full (1/1)" in lines
    assert (
        "  win unreachable: unreachable over ssh win: ssh: Could not resolve hostname win" in lines
    )


def test_an_unidentified_host_measures_every_machine_over_ssh(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No ``--here`` and no row named this host (an alias is none): no probe runs locally."""
    path = _write_list(
        tmp_path,
        [_entry("desk", "linux", aliases=["stranger"]), _entry("mac", "macos")],
    )
    fake = _FakeRun({"desk": (0, LINUX_OUTPUT, ""), "mac": (0, MACOS_OUTPUT, "")})
    _patch(monkeypatch, fake)
    monkeypatch.setattr(fleet, "this_hostname", lambda: "stranger")
    code = load_balancing.main(["--pick", "--machines", str(path)])
    assert (code, capsys.readouterr().out) == (0, "desk\n")
    assert sorted(fake.host(call) for call in fake.calls) == ["desk", "mac"]


def test_the_machine_override_names_the_local_machine_as_it_names_this_one(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``$DSF_MACHINE_ID`` is the identity rule's raw name here too: that row runs locally."""
    path = _write_list(tmp_path, [_entry("desk", "linux"), _entry("mac", "macos")])
    fake = _FakeRun({"local": (0, LINUX_OUTPUT, ""), "mac": (0, MACOS_OUTPUT, "")})
    _patch(monkeypatch, fake)
    monkeypatch.setenv(fleet.MACHINE_ENV, "Desk")
    code = load_balancing.main(["--pick", "--machines", str(path)])
    assert (code, capsys.readouterr().out) == (0, "desk\n")
    assert sorted(fake.host(call) for call in fake.calls) == ["local", "mac"]


def test_an_impossible_measurement_excludes_the_machine_with_its_reason(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A NaN load or an infinite Windows disk is a reason in the table, never a crash or a pick."""
    path = _write_list(tmp_path, [_entry("desk", "linux"), _entry("win", "windows")])
    _patch(
        monkeypatch,
        _FakeRun(
            {
                "desk": (0, LINUX_OUTPUT.replace("3.00 0.02", "NaN 0.02"), ""),
                "win": (0, WINDOWS_OUTPUT.replace("107374182400", "1e400"), ""),
            },
        ),
    )
    code = load_balancing.main(["--pick", "--machines", str(path)])
    captured = capsys.readouterr()
    assert code == 1
    assert captured.out == ""
    assert "desk: impossible cpu load nan" in captured.err
    assert "impossible Windows disk_free_bytes inf" in captured.err


def test_a_nan_weight_or_floor_in_the_list_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``NaN`` is valid JSON to ``json.loads`` but never a weight or a floor."""
    path = tmp_path / "machines.json"
    entry = json.dumps(_entry("a", "linux")).replace('"light": 1', '"light": NaN', 1)
    _ = path.write_text('{"machines": [' + entry + "]}", encoding="utf-8")
    assert load_balancing.main(["--machines", str(path)]) == 2
    assert "weight.light must be a finite number" in capsys.readouterr().err


def test_an_unreadable_machine_list_exits_two(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """No probe runs; the error names the file."""
    code = load_balancing.main(["--machines", str(tmp_path / "absent.json")])
    assert code == 2
    assert "absent.json" in capsys.readouterr().err
