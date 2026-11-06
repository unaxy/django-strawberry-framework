"""Read the fleet's machine list and reach its machines: the one owner of both.

``docs/fleet/machines.json`` is the one machine list, and this module is its one
reader: every script that needs a machine (``scripts/load_balancing.py`` picking
one, ``scripts/work.py`` naming a copy's home, ``scripts/fleet_sync.py`` syncing
copies) takes it from here. This module is also the one place two facts are
computed: which machine this one is (:func:`this_hostname`,
:func:`short_hostname`, :func:`local_machine`) and the ssh command line every
remote call runs (:data:`SSH_OPTIONS`, :func:`ssh_argv`, :func:`ssh_command`).
The checkout the list is read from defaults to ``scripts/_git.py``'s
``CHECKOUT_ROOT``, the one home of the repository root.

The list
    One JSON object whose ``machines`` is a non-empty array of entries. Each entry
    names the machine (``name``, unique), the ssh host it is reached as (``ssh``,
    never starting with ``-``, which ssh would read as an option), its OS
    (``linux``, ``macos`` or ``windows``), the checkout path a thread works in
    (``repo``, ``~`` allowed), a preference weight per mode (``weight``: ``light``
    and ``heavy``), the hard floors per mode (``floors``; only the keys the
    entry's OS can measure) and the ``hostnames`` the machine reports for itself
    (optional; no hostname belongs to two machines). Every weight and floor is a
    finite number of at least 0. What a weight or a floor means is
    ``scripts/load_balancing.py``'s rule; this module only checks their shape. A
    list breaking any of this is a :class:`MachineListError`, never a partial
    result.

Identity
    A machine's own name is :func:`this_hostname` (macOS: ``scutil --get
    LocalHostName``, since the socket hostname there follows the network;
    elsewhere, or when scutil gives none, :func:`socket.gethostname`); a
    hostname is compared and recorded up to its first dot, casefolded
    (:func:`short_hostname`). The machine this one is in the list is the entry
    whose ``hostnames`` holds that short name; nothing else (a matching OS
    included) identifies it.

ssh
    Every remote call is ``ssh`` with :data:`SSH_OPTIONS`: batch mode (no
    password prompt can hang a run), a 5-second connect timeout, and a keepalive
    that drops a peer silent for 45 seconds, so no probe, agent call, rsync or
    fetch waits forever on a stalled machine. :func:`ssh_argv` is the argv form
    and :func:`ssh_command` the one string rsync's ``-e`` and git's
    ``GIT_SSH_COMMAND`` take. ssh exits :data:`SSH_FAILED` when the connection
    or the authentication fails.

Standard library plus ``scripts/_git.py``, so it runs on the oldest supported
Python with no project environment.
"""

from __future__ import annotations

import dataclasses
import json
import math
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import _git as _git_runner
except ModuleNotFoundError:  # imported as ``scripts.fleet`` (repo root on path)
    from scripts import _git as _git_runner

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from typing_extensions import TypeIs

#: The machine list, relative to a checkout's root.
MACHINES_PATH = Path("docs") / "fleet" / "machines.json"
#: This checkout's machine list.
MACHINES_FILE = _git_runner.CHECKOUT_ROOT / MACHINES_PATH
MODES = ("light", "heavy")
OSES = ("linux", "macos", "windows")
COMMON_FLOORS = frozenset({"min_mem_available_gib", "min_disk_free_gib"})
#: The floors each OS's probe can measure.
FLOORS_BY_OS: Mapping[str, frozenset[str]] = {
    "linux": COMMON_FLOORS | {"max_psi_memory_full_avg10", "heavy_slots"},
    "macos": COMMON_FLOORS | {"max_vm_pressure_level"},
    "windows": COMMON_FLOORS,
}
#: The options every ssh call of the fleet carries (module docstring, "ssh").
SSH_OPTIONS = (
    "-o",
    "BatchMode=yes",
    "-o",
    "ConnectTimeout=5",
    "-o",
    "ServerAliveInterval=15",
    "-o",
    "ServerAliveCountMax=3",
)
#: ssh's own exit status for a connection or authentication failure.
SSH_FAILED = 255

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads


class MachineListError(ValueError):
    """The machine list is missing, unreadable, or breaks its schema, or names no such machine."""


@dataclasses.dataclass(frozen=True)
class Machine:
    """One entry of the machine list."""

    name: str
    ssh: str
    os: str
    repo: str
    weights: Mapping[str, float]
    floors: Mapping[str, Mapping[str, float]]
    hostnames: tuple[str, ...] = ()


# -- decoded JSON -------------------------------------------------------------------------


def is_json_object(value: object) -> TypeIs[dict[str, object]]:
    """Return whether ``value`` is a decoded JSON object (whose keys are always strings)."""
    return isinstance(value, dict)


def is_json_array(value: object) -> TypeIs[list[object]]:
    """Return whether ``value`` is a decoded JSON array."""
    return isinstance(value, list)


# -- the machine list ---------------------------------------------------------------------


def _number(value: object, where: str) -> float:
    """Return ``value`` as a finite number of at least 0 (JSON admits ``NaN`` and overflow)."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        msg = f"{where} must be a number, got {value!r}"
        raise MachineListError(msg)
    try:
        number = float(value)
    except OverflowError as error:
        msg = f"{where} must be finite, got {value!r}"
        raise MachineListError(msg) from error
    if not math.isfinite(number) or number < 0:
        msg = f"{where} must be a finite number of at least 0, got {value!r}"
        raise MachineListError(msg)
    return number


def _text(entry: Mapping[str, object], key: str, where: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        msg = f"{where}.{key} must be a non-empty string"
        raise MachineListError(msg)
    return value


def _object(value: object, where: str) -> dict[str, object]:
    if not is_json_object(value):
        msg = f"{where} must be an object"
        raise MachineListError(msg)
    return value


def _machine(raw: object, index: int) -> Machine:
    """Return entry ``index`` of the list as a :class:`Machine`.

    Raises:
        MachineListError: the entry breaks the schema the module docstring states.

    """
    where = f"machines[{index}]"
    entry = _object(raw, where)
    name = _text(entry, "name", where)
    os_name = _text(entry, "os", where)
    if os_name not in OSES:
        msg = f"{where}.os {os_name!r} is not one of {', '.join(OSES)}"
        raise MachineListError(msg)
    weights_raw = _object(entry.get("weight"), f"{where}.weight")
    floors_raw = _object(entry.get("floors"), f"{where}.floors")
    weights: dict[str, float] = {}
    floors: dict[str, dict[str, float]] = {}
    for mode in MODES:
        if mode not in weights_raw:
            msg = f"{where}.weight has no {mode!r} weight"
            raise MachineListError(msg)
        weights[mode] = _number(weights_raw[mode], f"{where}.weight.{mode}")
        mode_floors = _object(floors_raw.get(mode, {}), f"{where}.floors.{mode}")
        unknown = sorted(set(mode_floors) - FLOORS_BY_OS[os_name])
        if unknown:
            msg = f"{where}.floors.{mode}: {', '.join(unknown)} cannot be measured on {os_name}"
            raise MachineListError(msg)
        floors[mode] = {
            key: _number(value, f"{where}.floors.{mode}.{key}")
            for key, value in mode_floors.items()
        }
    extra = sorted(set(weights_raw) - set(MODES)) + sorted(set(floors_raw) - set(MODES))
    if extra:
        msg = f"{where}: unknown mode(s) {', '.join(extra)}"
        raise MachineListError(msg)
    ssh = _text(entry, "ssh", where)
    if ssh.startswith("-"):
        msg = f"{where}.ssh {ssh!r} starts with '-', which ssh reads as an option"
        raise MachineListError(msg)
    hostnames_raw = entry.get("hostnames", [])
    if not is_json_array(hostnames_raw) or not all(
        isinstance(item, str) and item for item in hostnames_raw
    ):
        msg = f"{where}.hostnames must be a list of non-empty strings"
        raise MachineListError(msg)
    return Machine(
        name=name,
        ssh=ssh,
        os=os_name,
        repo=_text(entry, "repo", where),
        weights=weights,
        floors=floors,
        hostnames=tuple(short_hostname(str(item)) for item in hostnames_raw),
    )


def load_machines(path: Path = MACHINES_FILE) -> tuple[Machine, ...]:
    """Return the machine list at ``path``, in file order.

    Raises:
        MachineListError: the file is missing, not JSON, or breaks the schema the
            module docstring states (names must be unique).

    """
    try:
        document = _loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        msg = f"{path}: {error}"
        raise MachineListError(msg) from error
    entries = _object(document, str(path)).get("machines")
    if not is_json_array(entries) or not entries:
        msg = f"{path}: 'machines' must be a non-empty list"
        raise MachineListError(msg)
    parsed = tuple(_machine(raw, index) for index, raw in enumerate(entries))
    names = [entry.name for entry in parsed]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        msg = f"{path}: duplicate machine name(s) {', '.join(duplicates)}"
        raise MachineListError(msg)
    claimed = [hostname for entry in parsed for hostname in entry.hostnames]
    shared = sorted({hostname for hostname in claimed if claimed.count(hostname) > 1})
    if shared:
        msg = f"{path}: hostname(s) {', '.join(shared)} belong to more than one machine"
        raise MachineListError(msg)
    return parsed


def machines(repo: Path = _git_runner.CHECKOUT_ROOT) -> tuple[Machine, ...]:
    """Return the machine list of the checkout at ``repo``, in file order.

    Raises:
        MachineListError: as :func:`load_machines`.

    """
    return load_machines(repo / MACHINES_PATH)


def machine(name: str, repo: Path = _git_runner.CHECKOUT_ROOT) -> Machine:
    """Return the machine the list of the checkout at ``repo`` names ``name``.

    A name the list does not hold is refused like a broken list, never a
    ``KeyError`` or a ``None`` for the caller to forget.

    Raises:
        MachineListError: the list is unreadable or broken (:func:`load_machines`),
            or no entry is named ``name``.

    """
    listed = machines(repo)
    found = next((entry for entry in listed if entry.name == name), None)
    if found is None:
        msg = (
            f"{repo / MACHINES_PATH}: no machine named {name!r} "
            f"(listed: {', '.join(entry.name for entry in listed)})"
        )
        raise MachineListError(msg)
    return found


# -- identity -----------------------------------------------------------------------------


def this_hostname() -> str:
    """Return this machine's own name, stable across the networks it joins.

    macOS: ``scutil --get LocalHostName``, since :func:`socket.gethostname` there
    follows the network (a DHCP lease renames the Mac ``mac.lan`` at home); when
    scutil fails, :func:`socket.gethostname`. Elsewhere :func:`socket.gethostname`.
    """
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["scutil", "--get", "LocalHostName"],
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            result = None
        if result is not None and result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    return socket.gethostname()


def short_hostname(hostname: str) -> str:
    """Return ``hostname`` up to its first dot, casefolded: how a machine is matched and named."""
    return hostname.split(".", 1)[0].casefold()


def local_machine(
    listed: Sequence[Machine],
    here: str | None,
    hostname: str | None = None,
) -> Machine | None:
    """Return the machine this script runs on, or ``None`` when no entry is this one.

    ``here`` names it outright (a name or an ssh host); otherwise it is the machine
    whose ``hostnames`` holds ``hostname`` (default :func:`this_hostname`) up to its
    first dot, compared without case. Nothing else identifies it: a machine of the
    same OS is not this one.

    Raises:
        MachineListError: ``here`` names no machine of the list.

    """
    if here is not None:
        for entry in listed:
            if here in {entry.name, entry.ssh}:
                return entry
        msg = f"--here {here!r} names no machine of the list"
        raise MachineListError(msg)
    short = short_hostname(this_hostname() if hostname is None else hostname)
    return next((entry for entry in listed if short in entry.hostnames), None)


# -- ssh ----------------------------------------------------------------------------------


def ssh_argv(target: Machine | str, command: str) -> list[str]:
    """Return the argv that runs the remote ``command`` on ``target`` over ssh.

    ``target`` is a machine of the list (reached as its ``ssh`` host) or a host
    name no row lists (a peer reached by its MagicDNS name). ``command`` is one
    string the remote shell reads, quoted by the caller.
    """
    host = target.ssh if isinstance(target, Machine) else target
    return [
        "ssh",
        *SSH_OPTIONS,
        host,
        command,
    ]


def ssh_command() -> str:
    """Return the ssh command line, options included, as rsync's ``-e`` and ``GIT_SSH_COMMAND`` take it."""
    return shlex.join(["ssh", *SSH_OPTIONS])
