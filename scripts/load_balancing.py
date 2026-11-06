"""Pick the fleet machine a new thread in a shared project starts on.

The rule: a new thread starts on the machine with the most free CPU and memory,
weighted by that machine's preference, among the machines that clear every hard
floor. The machines are ``docs/fleet/machines.json``'s, read through
``scripts/fleet.py`` (its docstring states the list's schema): each entry names
the machine, the ssh host it is reached as, its OS, the checkout path the thread
would work in (``repo``), a preference weight per mode, the hard floors per mode
and the ``hostnames`` the machine reports for itself. A machine joins the fleet
by a row there and its block in ``docs/fleet/MACHINES.md``.

Modes
    ``light`` (the default) is an ordinary agent thread: editing, git, targeted
    tests. ``--heavy`` is a long or heavy run (a suite, a build, a multi-agent
    flow) and reads each machine's ``heavy`` weight and floors instead.

Measurement
    Every machine is measured by one probe script: the machine this script runs on
    locally (no ssh), every other one in one ssh call with the fleet's options
    (``fleet.ssh_argv``: batch mode, a 5-second connect timeout, a keepalive), all
    machines in parallel. The local machine is the one ``--here`` names, else the
    machine whose ``hostnames`` holds this host's name (``fleet.local_machine``);
    with neither, the script cannot tell which machine it is on and reaches every
    machine over ssh, its own included.

    - Linux: ``/proc/loadavg`` (1-minute load), ``nproc`` (threads),
      ``/proc/meminfo`` ``MemTotal`` and ``MemAvailable``, ``/proc/pressure/memory``
      (PSI ``full avg10``, the share of the last 10 s every task stalled on memory),
      and the running heavy jobs: ``~/.cache/heavy/slot*.job`` files whose pid is
      alive, as the machine's own ``heavy`` and ``pressure`` tools count them.
    - macOS: ``sysctl`` ``hw.logicalcpu``, ``hw.memsize``, ``vm.loadavg``,
      ``kern.memorystatus_level`` (the kernel's free-memory percentage, the figure
      ``memory_pressure`` prints; available memory is that share of ``hw.memsize``)
      and ``kern.memorystatus_vm_pressure_level`` (1 normal, 2 warn, 4 critical).
      ``memory_pressure`` itself is never run: given any argument it allocates
      memory to create pressure.
    - Windows: PowerShell ``Get-CimInstance`` ``Win32_Processor``
      (``LoadPercentage`` averaged, ``NumberOfLogicalProcessors`` summed) and
      ``Win32_OperatingSystem`` (``FreePhysicalMemory``,
      ``TotalVisibleMemorySize``), sent as ``powershell -EncodedCommand``.
    - Every OS: free disk on the filesystem holding ``repo`` (``df -Pk``, or the
      PowerShell drive's ``Free``).

    The probe also reports the OS it ran on; one that differs from the list's
    ``os`` is a misconfigured entry and the machine is excluded with that reason.
    So is a measurement no machine can have: a non-finite or negative value, no
    threads, no memory, more memory available than installed, or a count past
    ``2**63``.

Score
    ``score = weight * (cpu_free + mem_free) / 2``, where ``cpu_free`` is
    ``1 - load1 / threads`` (Windows: ``1 - LoadPercentage / 100``) clamped to
    ``[0, 1]`` and ``mem_free`` is available memory over total. Both are fractions,
    so a bigger machine wins through its weight, not its size. Highest score wins;
    a tie goes to the earlier entry in the list.

Floors (any breach disqualifies; a floor the probe could not measure is a breach)
    ``min_mem_available_gib``, ``min_disk_free_gib`` (every OS);
    ``max_psi_memory_full_avg10`` and ``heavy_slots`` (Linux: disqualified once the
    running heavy jobs fill every slot); ``max_vm_pressure_level`` (macOS). A floor
    key the entry's OS cannot measure is a machine-list error. A weight of 0
    disqualifies the machine for that mode. An unreachable machine, a failed
    probe or unreadable probe output excludes the machine with the reason; it is
    never an error.

Output
    A ranked table (default), ``--json`` (one document: the mode, the pick and
    every machine with its status, reasons, score and measurement) or ``--pick``
    (the winning machine's ssh host alone). Exit 0 when a machine qualifies, 1
    when none does, 2 for an unreadable machine list.

Standard library plus ``scripts/fleet.py``, so it runs on the oldest supported
Python with no project environment.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import dataclasses
import json
import math
import shlex
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import fleet
except ModuleNotFoundError:  # imported as ``scripts.load_balancing`` (repo root on path)
    from scripts import fleet

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

#: Seconds one probe may take, ssh connection included.
PROBE_TIMEOUT = 30.0
GIB = 1024**3
#: The bound on every measured count: past it a byte count or a thread count is no machine's.
MAX_COUNT = 2**63
KIB = 1024
#: What ``uname -s`` prints on each POSIX OS of the machine list.
UNAME_OS = {"Linux": "linux", "Darwin": "macos"}

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads

#: The tilde expansion every POSIX probe opens with: ``repo`` arrives as ``$1``.
_POSIX_PREAMBLE = """\
repo=$1
case $repo in "~"|"~/"*) repo=$HOME${repo#"~"};; esac
echo "@@ uname"; uname -s
"""
LINUX_PROBE = (
    _POSIX_PREAMBLE
    + """\
echo "@@ loadavg"; cat /proc/loadavg
echo "@@ nproc"; nproc
echo "@@ meminfo"; cat /proc/meminfo
echo "@@ psi_memory"; cat /proc/pressure/memory 2>/dev/null
echo "@@ heavy_jobs"
n=0
for j in "$HOME"/.cache/heavy/slot*.job; do
  [ -f "$j" ] && kill -0 "$(cut -d' ' -f1 "$j")" 2>/dev/null && n=$((n+1))
done
echo "$n"
echo "@@ df"; df -Pk "$repo"
"""
)
MACOS_PROBE = (
    _POSIX_PREAMBLE
    + """\
echo "@@ sysctl"
sysctl hw.logicalcpu hw.memsize vm.loadavg kern.memorystatus_level \
kern.memorystatus_vm_pressure_level
echo "@@ df"; df -Pk "$repo"
"""
)
#: ``{repo}`` is replaced by the PowerShell single-quoted checkout path.
WINDOWS_PROBE = """\
$ErrorActionPreference = 'Stop'
$repo = {repo}
if ($repo -eq '~' -or $repo.StartsWith('~/') -or $repo.StartsWith('~\\')) {
  $repo = $HOME + $repo.Substring(1)
}
$cpu = @(Get-CimInstance -ClassName Win32_Processor)
$os = Get-CimInstance -ClassName Win32_OperatingSystem
$drive = (Get-Item -LiteralPath $repo).PSDrive
Write-Output '@@ windows'
[pscustomobject]@{
  logical_processors = ($cpu | Measure-Object -Property NumberOfLogicalProcessors -Sum).Sum
  load_percentage = ($cpu | Measure-Object -Property LoadPercentage -Average).Average
  free_physical_kib = $os.FreePhysicalMemory
  total_visible_kib = $os.TotalVisibleMemorySize
  disk_free_bytes = $drive.Free
} | ConvertTo-Json -Compress
"""


class ProbeOutputError(ValueError):
    """A probe's output lacks a section or a value the parser needs."""


@dataclasses.dataclass(frozen=True)
class Measurement:
    """What one probe measured; ``None`` is a value that OS does not report or the probe lacked."""

    os: str
    threads: int
    cpu_busy: float
    mem_total_bytes: int
    mem_available_bytes: int
    disk_free_bytes: int
    psi_memory_full_avg10: float | None = None
    vm_pressure_level: int | None = None
    heavy_jobs: int | None = None

    def __post_init__(self) -> None:
        """Refuse a measurement no machine can have.

        Raises:
            ProbeOutputError: a value is non-finite, negative or past ``2**63``, the
                machine has no threads or no memory, or more memory is available
                than installed.

        """
        for label, value in (
            ("threads", self.threads),
            ("cpu load", self.cpu_busy),
            ("total memory", self.mem_total_bytes),
            ("available memory", self.mem_available_bytes),
            ("free disk", self.disk_free_bytes),
            ("PSI memory full", self.psi_memory_full_avg10),
            ("memory pressure level", self.vm_pressure_level),
            ("heavy jobs", self.heavy_jobs),
        ):
            # A NaN fails both comparisons, an infinity or a huge int the bound; no float
            # conversion runs, so an int past float range cannot overflow here.
            if value is not None and not 0 <= value < MAX_COUNT:
                msg = f"impossible {label} {value!r}"
                raise ProbeOutputError(msg)
        if self.threads == 0 or self.mem_total_bytes == 0:
            msg = f"impossible machine: {self.threads} threads, {self.mem_total_bytes} B memory"
            raise ProbeOutputError(msg)
        if self.mem_available_bytes > self.mem_total_bytes:
            msg = (
                f"impossible memory: {self.mem_available_bytes} B available of "
                f"{self.mem_total_bytes} B"
            )
            raise ProbeOutputError(msg)

    @property
    def cpu_free(self) -> float:
        """Return the idle share of the CPU, clamped to ``[0, 1]``."""
        return min(max(1.0 - self.cpu_busy, 0.0), 1.0)

    @property
    def mem_free(self) -> float:
        """Return available memory over total."""
        return self.mem_available_bytes / self.mem_total_bytes


@dataclasses.dataclass(frozen=True)
class Verdict:
    """One machine's result for a mode: ``ok``, ``disqualified`` or ``unreachable``."""

    machine: fleet.Machine
    local: bool
    status: str
    reasons: tuple[str, ...]
    score: float | None
    measurement: Measurement | None


# -- probes -------------------------------------------------------------------------------


def _powershell_literal(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def probe_command(machine: fleet.Machine, *, local: bool) -> tuple[list[str], str | None]:
    """Return the argv and stdin that measure ``machine``: one process, one ssh call if remote."""
    if machine.os == "windows":
        script = WINDOWS_PROBE.replace("{repo}", _powershell_literal(machine.repo))
        encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
        command = [
            "powershell",
            "-NoProfile",
            "-NonInteractive",
            "-EncodedCommand",
            encoded,
        ]
        if local:
            return command, None
        return fleet.ssh_argv(machine, " ".join(command)), None
    script = LINUX_PROBE if machine.os == "linux" else MACOS_PROBE
    if local:
        return [
            "sh",
            "-s",
            "--",
            machine.repo,
        ], script
    return fleet.ssh_argv(machine, f"sh -s -- {shlex.quote(machine.repo)}"), script


def _sections(output: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in output.splitlines():
        if line.startswith("@@ "):
            current = sections.setdefault(line[3:].strip(), [])
        elif current is not None and line.strip():
            current.append(line.rstrip("\r"))
    return sections


def _section(sections: Mapping[str, list[str]], name: str) -> list[str]:
    lines = sections.get(name)
    if not lines:
        msg = f"no {name} output"
        raise ProbeOutputError(msg)
    return lines


def _df_free_bytes(sections: Mapping[str, list[str]]) -> int:
    fields = _section(sections, "df")[-1].split()
    try:
        return int(fields[3]) * KIB
    except (IndexError, ValueError) as error:
        msg = f"unreadable df line {' '.join(fields)!r}"
        raise ProbeOutputError(msg) from error


def _uname_os(sections: Mapping[str, list[str]]) -> str:
    uname = _section(sections, "uname")[0].strip()
    return UNAME_OS.get(uname, uname)


def reported_os(output: str) -> str | None:
    """Return the OS a probe's output says it ran on, ``None`` when it says nothing."""
    sections = _sections(output)
    if "windows" in sections:
        return "windows"
    return _uname_os(sections) if sections.get("uname") else None


def _linux_psi(lines: list[str]) -> float | None:
    """Return the ``full avg10`` memory-pressure figure, ``None`` when the kernel reports none.

    Raises:
        ValueError: the figure is not a number (the caller reads it as unreadable output).

    """
    psi: float | None = None
    for line in lines:
        fields = line.split()
        if fields and fields[0] == "full":
            values = dict(field.split("=", 1) for field in fields[1:] if "=" in field)
            if "avg10" in values:
                psi = float(values["avg10"])
    return psi


def parse_linux(output: str) -> Measurement:
    """Parse :data:`LINUX_PROBE` output.

    Raises:
        ProbeOutputError: a section the measurement needs is missing or unreadable.

    """
    sections = _sections(output)
    meminfo: dict[str, int] = {}
    for line in _section(sections, "meminfo"):
        key, _, rest = line.partition(":")
        value = rest.split()
        if value and value[0].isdigit():
            meminfo[key.strip()] = int(value[0]) * KIB
    heavy = sections.get("heavy_jobs", [])
    try:
        psi = _linux_psi(sections.get("psi_memory", []))
        threads = int(_section(sections, "nproc")[0])
        load1 = float(_section(sections, "loadavg")[0].split()[0])
        return Measurement(
            os=_uname_os(sections),
            threads=threads,
            cpu_busy=load1 / threads,
            mem_total_bytes=meminfo["MemTotal"],
            mem_available_bytes=meminfo["MemAvailable"],
            disk_free_bytes=_df_free_bytes(sections),
            psi_memory_full_avg10=psi,
            heavy_jobs=int(heavy[0]) if heavy else None,
        )
    except (
        KeyError,
        IndexError,
        ValueError,
        ZeroDivisionError,
        OverflowError,
    ) as error:
        if isinstance(error, ProbeOutputError):
            raise
        msg = f"unreadable Linux probe output ({type(error).__name__}: {error})"
        raise ProbeOutputError(msg) from error


def parse_macos(output: str) -> Measurement:
    """Parse :data:`MACOS_PROBE` output.

    Raises:
        ProbeOutputError: a section the measurement needs is missing or unreadable.

    """
    sections = _sections(output)
    values: dict[str, str] = {}
    for line in _section(sections, "sysctl"):
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    try:
        threads = int(values["hw.logicalcpu"])
        load1 = float(values["vm.loadavg"].strip("{} ").split()[0])
        total = int(values["hw.memsize"])
        level = int(values["kern.memorystatus_level"])
        return Measurement(
            os=_uname_os(sections),
            threads=threads,
            cpu_busy=load1 / threads,
            mem_total_bytes=total,
            mem_available_bytes=total * level // 100,
            disk_free_bytes=_df_free_bytes(sections),
            vm_pressure_level=int(values["kern.memorystatus_vm_pressure_level"]),
        )
    except (
        KeyError,
        IndexError,
        ValueError,
        ZeroDivisionError,
        OverflowError,
    ) as error:
        if isinstance(error, ProbeOutputError):
            raise
        msg = f"unreadable macOS probe output ({type(error).__name__}: {error})"
        raise ProbeOutputError(msg) from error


def _int_field(document: Mapping[str, object], key: str) -> int:
    value = document.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"Windows probe output has no numeric {key}"
        raise ProbeOutputError(msg)
    if isinstance(value, float) and not math.isfinite(value):
        msg = f"impossible Windows {key} {value!r}"
        raise ProbeOutputError(msg)
    return int(value)


def parse_windows(output: str) -> Measurement:
    """Parse :data:`WINDOWS_PROBE` output (one compressed ``ConvertTo-Json`` object).

    Raises:
        ProbeOutputError: the JSON is missing, unreadable, or lacks a value.

    """
    lines = _section(_sections(output), "windows")
    try:
        raw = _loads("".join(lines))
    except ValueError as error:
        msg = f"unreadable Windows probe JSON ({error})"
        raise ProbeOutputError(msg) from error
    if not fleet.is_json_object(raw):
        msg = "Windows probe JSON is not an object"
        raise ProbeOutputError(msg)
    document = raw
    threads = _int_field(document, "logical_processors")
    load = document.get("load_percentage")
    if isinstance(load, bool) or not isinstance(load, int | float) or threads <= 0:
        msg = "Windows probe output has no numeric load_percentage"
        raise ProbeOutputError(msg)
    try:
        cpu_busy = float(load) / 100
    except OverflowError as error:
        msg = f"impossible Windows load_percentage {load!r}"
        raise ProbeOutputError(msg) from error
    return Measurement(
        os="windows",
        threads=threads,
        cpu_busy=cpu_busy,
        mem_total_bytes=_int_field(document, "total_visible_kib") * KIB,
        mem_available_bytes=_int_field(document, "free_physical_kib") * KIB,
        disk_free_bytes=_int_field(document, "disk_free_bytes"),
    )


PARSERS: Mapping[str, Callable[[str], Measurement]] = {
    "linux": parse_linux,
    "macos": parse_macos,
    "windows": parse_windows,
}


def _last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else "no output"


def measure(
    machine: fleet.Machine,
    *,
    local: bool,
    timeout: float = PROBE_TIMEOUT,
) -> Measurement | str:
    """Run ``machine``'s probe and return its measurement, or the reason it has none."""
    argv, stdin = probe_command(machine, local=local)
    try:
        completed = subprocess.run(
            argv,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"probe timed out after {timeout:g}s"
    except OSError as error:
        return f"cannot run {argv[0]}: {error}"
    if completed.returncode == fleet.SSH_FAILED and not local:
        return f"unreachable over ssh {machine.ssh}: {_last_line(completed.stderr)}"
    if completed.returncode != 0:
        return f"probe failed (exit {completed.returncode}): {_last_line(completed.stderr)}"
    reported = reported_os(completed.stdout)
    if reported is not None and reported != machine.os:
        return f"probe ran on {reported}, the machine list says {machine.os}"
    try:
        return PARSERS[machine.os](completed.stdout)
    except ProbeOutputError as error:
        return str(error)


# -- scoring ------------------------------------------------------------------------------


def floor_breaches(measurement: Measurement, floors: Mapping[str, float]) -> list[str]:
    """Return one reason per floor ``measurement`` breaches; an unmeasured floor is a breach."""
    reasons: list[str] = []
    if "min_mem_available_gib" in floors:
        need = floors["min_mem_available_gib"]
        have = measurement.mem_available_bytes / GIB
        if have < need:
            reasons.append(f"{have:.1f} GiB RAM available, floor {need:g}")
    if "min_disk_free_gib" in floors:
        need = floors["min_disk_free_gib"]
        have = measurement.disk_free_bytes / GIB
        if have < need:
            reasons.append(f"{have:.1f} GiB disk free, floor {need:g}")
    if "max_psi_memory_full_avg10" in floors:
        limit = floors["max_psi_memory_full_avg10"]
        psi = measurement.psi_memory_full_avg10
        if psi is None:
            reasons.append("PSI memory unmeasured")
        elif psi > limit:
            reasons.append(f"memory thrashing (PSI full avg10 {psi:g}%, limit {limit:g})")
    if "heavy_slots" in floors:
        slots = floors["heavy_slots"]
        jobs = measurement.heavy_jobs
        if jobs is None:
            reasons.append("heavy jobs unmeasured")
        elif jobs >= slots:
            reasons.append(f"heavy slots full ({jobs}/{slots:g})")
    if "max_vm_pressure_level" in floors:
        limit = floors["max_vm_pressure_level"]
        level = measurement.vm_pressure_level
        if level is None:
            reasons.append("memory pressure level unmeasured")
        elif level > limit:
            reasons.append(f"memory pressure level {level}, limit {limit:g}")
    return reasons


def score(measurement: Measurement, weight: float) -> float:
    """Return ``weight * (cpu_free + mem_free) / 2``."""
    return weight * (measurement.cpu_free + measurement.mem_free) / 2


def judge(
    machine: fleet.Machine,
    result: Measurement | str,
    mode: str,
    *,
    local: bool,
) -> Verdict:
    """Return ``machine``'s verdict for ``mode`` from its probe ``result``."""
    if isinstance(result, str):
        return Verdict(machine, local, "unreachable", (result,), None, None)
    weight = machine.weights[mode]
    reasons = floor_breaches(result, machine.floors[mode])
    if weight == 0:
        reasons.insert(0, f"weight {weight:g} for {mode} work")
    status = "disqualified" if reasons else "ok"
    return Verdict(machine, local, status, tuple(reasons), score(result, weight), result)


def rank(verdicts: Sequence[Verdict]) -> list[Verdict]:
    """Order qualifying machines by score (list order breaks a tie), then the rest."""
    order = {"ok": 0, "disqualified": 1, "unreachable": 2}
    indexed = sorted(
        enumerate(verdicts),
        key=lambda pair: (order[pair[1].status], -(pair[1].score or 0.0), pair[0]),
    )
    return [verdict for _, verdict in indexed]


def survey(
    machines: Sequence[fleet.Machine],
    mode: str,
    local: fleet.Machine | None,
    timeout: float = PROBE_TIMEOUT,
) -> list[Verdict]:
    """Probe every machine in parallel and return the ranked verdicts."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(machines)) as pool:
        futures = [
            pool.submit(measure, machine, local=machine is local, timeout=timeout)
            for machine in machines
        ]
        results = [future.result() for future in futures]
    return rank(
        [
            judge(machine, result, mode, local=machine is local)
            for machine, result in zip(machines, results, strict=True)
        ],
    )


# -- output -------------------------------------------------------------------------------


def _notes(measurement: Measurement) -> str:
    notes: list[str] = []
    if measurement.psi_memory_full_avg10 is not None:
        notes.append(f"psi-full {measurement.psi_memory_full_avg10:g}%")
    if measurement.heavy_jobs is not None:
        notes.append(f"heavy {measurement.heavy_jobs}")
    if measurement.vm_pressure_level is not None:
        notes.append(f"vm-pressure {measurement.vm_pressure_level}")
    return ", ".join(notes)


def render_table(verdicts: Sequence[Verdict], mode: str) -> str:
    """Return the ranked table for ``mode``."""
    header = (
        "rank",
        "machine",
        "os",
        "cpu free",
        "mem avail",
        "disk free",
        "weight",
        "score",
    )
    rows: list[tuple[str, ...]] = [header]
    details: list[str] = []
    position = 0
    for verdict in verdicts:
        machine = verdict.machine
        name = machine.name + (" (here)" if verdict.local else "")
        if verdict.status == "ok":
            position += 1
            label = str(position)
        else:
            label = "-"
        measured = verdict.measurement
        if measured is None:
            cells = ("-", "-", "-")
        else:
            cells = (
                f"{measured.cpu_free:.0%} of {measured.threads}",
                f"{measured.mem_available_bytes / GIB:.1f}/{measured.mem_total_bytes / GIB:.1f} GiB",
                f"{measured.disk_free_bytes / GIB:.1f} GiB",
            )
            note = _notes(measured)
            if note:
                details.append(f"  {machine.name}: {note}")
        rows.append(
            (
                label,
                name,
                machine.os,
                *cells,
                f"{machine.weights[mode]:g}",
                "-" if verdict.score is None else f"{verdict.score:.3f}",
            ),
        )
        for reason in verdict.reasons:
            details.append(f"  {machine.name} {verdict.status}: {reason}")
    widths = [max(len(row[column]) for row in rows) for column in range(len(header))]
    lines = [
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths, strict=True)).rstrip()
        for row in rows
    ]
    return "\n".join([f"mode: {mode}", *lines, *details])


def render_json(verdicts: Sequence[Verdict], mode: str) -> str:
    """Return the ``--json`` document for ``mode``."""
    winner = next((verdict for verdict in verdicts if verdict.status == "ok"), None)
    machines: list[dict[str, object]] = [
        {
            "name": verdict.machine.name,
            "ssh": verdict.machine.ssh,
            "os": verdict.machine.os,
            "local": verdict.local,
            "status": verdict.status,
            "reasons": list(verdict.reasons),
            "weight": verdict.machine.weights[mode],
            "score": verdict.score,
            "measurement": (
                None
                if verdict.measurement is None
                else {
                    **dataclasses.asdict(verdict.measurement),
                    "cpu_free": verdict.measurement.cpu_free,
                    "mem_free": verdict.measurement.mem_free,
                }
            ),
        }
        for verdict in verdicts
    ]
    document = {
        "mode": mode,
        "pick": None if winner is None else winner.machine.ssh,
        "machines": machines,
    }
    return json.dumps(document, indent=2)


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``main``'s ``add_argument`` calls."""

    pick: bool
    json: bool
    heavy: bool
    here: str | None
    machines: Path
    timeout: float


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI; see the module docstring."""
    parser = argparse.ArgumentParser(
        description="Rank the fleet machines for a new thread (rules: module docstring).",
    )
    output = parser.add_mutually_exclusive_group()
    _ = output.add_argument("--pick", action="store_true", help="print only the winning ssh host")
    _ = output.add_argument("--json", action="store_true", help="print one JSON document")
    _ = parser.add_argument(
        "--heavy",
        action="store_true",
        help="apply the heavy-work weights and floors",
    )
    _ = parser.add_argument(
        "--here",
        help="the machine (name or ssh host) this runs on; default: by this host's name",
    )
    _ = parser.add_argument(
        "--machines",
        type=Path,
        default=fleet.MACHINES_FILE,
        help="machine list",
    )
    _ = parser.add_argument("--timeout", type=float, default=PROBE_TIMEOUT, help="probe seconds")
    args = parser.parse_args(argv, namespace=_Args())
    mode = "heavy" if args.heavy else "light"
    try:
        machines = fleet.load_machines(args.machines)
        local = fleet.local_machine(machines, args.here)
    except fleet.MachineListError as error:
        print(f"load_balancing: {error}", file=sys.stderr)
        return 2
    verdicts = survey(machines, mode, local, args.timeout)
    winner = next((verdict for verdict in verdicts if verdict.status == "ok"), None)
    if args.pick:
        if winner is None:
            print(f"load_balancing: no machine qualifies for {mode} work", file=sys.stderr)
            for verdict in verdicts:
                print(f"  {verdict.machine.name}: {'; '.join(verdict.reasons)}", file=sys.stderr)
        else:
            print(winner.machine.ssh)
    elif args.json:
        print(render_json(verdicts, mode))
    else:
        print(render_table(verdicts, mode))
    return 0 if winner is not None else 1


if __name__ == "__main__":
    sys.exit(main())
