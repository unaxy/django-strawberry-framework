"""Read the fleet's machine list and reach its machines: the one owner of both.

``docs/fleet/machines.json`` is the one machine list, and this module is its one
reader: every script that needs a machine (``docs/fleet/scripts/load_balancing.py`` picking
one, ``scripts/work.py`` naming a copy's home, ``docs/fleet/scripts/fleet_sync.py`` syncing
copies) takes it from here. This module is also the one place two facts are
computed: which machine this one is, what name a stored record means and which
row a host name reaches (:func:`this_machine`, :func:`this_machine_name`,
:func:`canonical`, :func:`local_machine`, :func:`reached_as`, below "Identity")
and the ssh command line every remote call runs (:data:`SSH_OPTIONS`,
:func:`ssh_argv`, :func:`ssh_command`, :func:`ssh_user`).
The checkout the list is read from defaults to ``scripts/_git.py``'s
``CHECKOUT_ROOT``, the one home of the repository root.

The list
    One JSON object whose ``machines`` is a non-empty array of entries. Each entry
    names the machine (``name``, unique), the ssh host it is reached as (``ssh``,
    never starting with ``-``, which ssh would read as an option), its OS
    (``linux``, ``macos`` or ``windows``), the checkout path a thread works in
    (``repo``, ``~`` allowed), a preference weight per mode (``weight``: ``light``
    and ``heavy``), the hard floors per mode (``floors``; only the keys the
    entry's OS can measure), its ``aliases`` (optional: other names the
    machine's stored records may carry, read only to resolve them; below) and
    ``other_projects`` (optional, ``true`` or ``false``: whether ``~/projects`` may hold
    entries beyond the checkout and the reference sources, a machine that also holds
    personal projects; ``docs/fleet/scripts/fleet_setup.py`` "Strays"). Names
    and aliases are compared up to their first dot, casefolded
    (:func:`short_hostname`); each is non-blank there, no name or alias belongs to
    two machines or appears twice (an alias never equals a row's name), and a row
    holds no ``hostnames`` key (other names go in ``aliases``). Every weight and floor is a
    finite number of at least 0. What a weight or a floor means is
    ``docs/fleet/scripts/load_balancing.py``'s rule; this module only checks their shape. A
    list breaking any of this is a :class:`MachineListError`, never a partial
    result.

Identity
    A machine has one name, its row's ``name``: every fleet script records it
    (a copy's ``home``, a handoff's ``formerhomes``, a tombstone's home and
    remover, a name claim's owner) and compares by it. This machine's raw name
    is :data:`MACHINE_ENV` (``$DSF_MACHINE_ID``) when set, else
    :func:`this_hostname` (macOS: ``scutil --get LocalHostName``, since the
    socket hostname there follows the network; elsewhere, or when scutil gives
    none, :func:`socket.gethostname`), taken up to its first dot, casefolded
    (:func:`short_hostname`). :func:`this_machine` is the row whose ``name`` is
    that raw name, and nothing else identifies it (an alias or a matching OS
    included): a machine that must act as a fleet member refuses on a host the
    list does not name. A stored name is read through :func:`canonical`: the
    row whose name or one of whose ``aliases`` it is, else the stored name
    itself (short, casefolded). :func:`this_machine_name`, for what only records
    or reports, is :func:`this_machine`'s name, else the raw name read through
    :func:`canonical`. Records are never rewritten (a tombstone is create-only
    and travels between machines): a record carrying a name other than the row's
    reads as that machine's through the row's aliases. An empty raw name (an
    override such as ``.``) names no machine. A host name another machine is
    reached as (a git remote's host) reaches the row whose name, alias or
    ``ssh`` host it is, up to its first dot, casefolded (:func:`reached_as`).

ssh
    Every remote call is ``ssh`` with :data:`SSH_OPTIONS`: batch mode (no
    password prompt can hang a run), a 5-second connect timeout, and a keepalive
    that drops a peer silent for 45 seconds, so no probe, agent call, rsync or
    fetch waits forever on a stalled machine. :func:`ssh_argv` is the argv form
    and :func:`ssh_command` the one string rsync's ``-e`` and git's
    ``GIT_SSH_COMMAND`` take. ssh exits :data:`SSH_FAILED` when the connection
    or the authentication fails. The list records no login: the account a host
    is reached as is ssh's own answer (:func:`ssh_user`, ``ssh -G``), so each
    machine's ssh configuration names it.

Standard library plus ``scripts/_git.py``, so it runs on the oldest supported
Python with no project environment.
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if __package__:  # imported as ``docs.fleet.scripts.fleet`` (repo root on path)
    from scripts import _git as _git_runner
else:  # run or imported from its own folder: ``_git.py`` lives in the checkout's scripts/
    sys.path.insert(1, str(Path(__file__).resolve().parents[3] / "scripts"))
    import _git as _git_runner

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
#: Seconds ``ssh -G`` may take to print its configuration (:func:`ssh_user`).
SSH_CONFIG_TIMEOUT = 10
#: Names this machine instead of its hostname (module docstring, "Identity"): a hostname
#: that is not its row's name, two fake machines on one host in the tests.
MACHINE_ENV = "DSF_MACHINE_ID"

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
    aliases: tuple[str, ...] = ()
    other_projects: bool = False


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


def _names(entry: Machine) -> tuple[str, ...]:
    """Return every name ``entry`` is known by, short and casefolded: its name, then its aliases.

    An empty short form (which the parser refuses) is never one of them.
    """
    return tuple(known for known in (short_hostname(entry.name), *entry.aliases) if known)


def _machine(raw: object, index: int) -> Machine:
    """Return entry ``index`` of the list as a :class:`Machine`.

    Raises:
        MachineListError: the entry breaks the schema the module docstring states.

    """
    where = f"machines[{index}]"
    entry = _object(raw, where)
    name = _text(entry, "name", where)
    if not short_hostname(name):
        msg = f"{where}.name {name!r} is empty before its first dot"
        raise MachineListError(msg)
    if "hostnames" in entry:
        msg = f"{where}: unknown key hostnames; former names go in aliases"
        raise MachineListError(msg)
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
    aliases_raw = entry.get("aliases", [])
    if not is_json_array(aliases_raw) or not all(
        isinstance(item, str) and item for item in aliases_raw
    ):
        msg = f"{where}.aliases must be a list of non-empty strings"
        raise MachineListError(msg)
    empty = [str(item) for item in aliases_raw if not short_hostname(str(item))]
    if empty:
        msg = f"{where}.aliases: {', '.join(map(repr, empty))} empty before the first dot"
        raise MachineListError(msg)
    other_projects = entry.get("other_projects", False)
    if not isinstance(other_projects, bool):
        msg = f"{where}.other_projects must be true or false"
        raise MachineListError(msg)
    return Machine(
        name=name,
        ssh=ssh,
        os=os_name,
        repo=_text(entry, "repo", where),
        weights=weights,
        floors=floors,
        aliases=tuple(short_hostname(str(item)) for item in aliases_raw),
        other_projects=other_projects,
    )


def load_machines(path: Path = MACHINES_FILE) -> tuple[Machine, ...]:
    """Return the machine list at ``path``, in file order.

    Raises:
        MachineListError: the file is missing, not JSON, or breaks the schema the
            module docstring states (names and aliases must be unique).

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
    claimed = [known for entry in parsed for known in _names(entry)]
    shared = sorted({known for known in claimed if claimed.count(known) > 1})
    if shared:
        msg = f"{path}: name(s) {', '.join(shared)} listed more than once (a name or an alias)"
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
    """Return ``hostname`` stripped, up to its first dot, casefolded: how names are compared.

    A blank name (``" "``) is ``""``, like ``"."``: the empty name no machine has.
    """
    return hostname.strip().split(".", 1)[0].casefold()


def _raw_identity() -> tuple[str, str]:
    """Return this machine's raw name, short, and where it came from (module docstring, "Identity").

    :data:`MACHINE_ENV` when set (source ``$DSF_MACHINE_ID``), else :func:`this_hostname`
    (source ``its hostname``): the one place every identity check takes the name from.
    """
    override = os.environ.get(MACHINE_ENV, "")
    if override:
        return short_hostname(override), f"${MACHINE_ENV}"
    return short_hostname(this_hostname()), "its hostname"


def canonical(
    name: str,
    listed: Sequence[Machine] | None = None,
    *,
    repo: Path = _git_runner.CHECKOUT_ROOT,
) -> str:
    """Return the machine name a stored ``name`` means.

    Take ``name`` up to its first dot, casefolded (:func:`short_hostname`). When a row of
    ``listed`` (default the list of the checkout at ``repo``) has that as its name or one
    of its ``aliases``, return the row's ``name``; otherwise return the short form itself.
    An empty short form returns ``""`` and never a row. Never raises: with an unreadable
    or broken list nothing resolves, so the short form is returned.
    """
    short = short_hostname(name)
    if not short:
        return ""
    if listed is None:
        try:
            listed = machines(repo)
        except MachineListError:
            return short
    return next((entry.name for entry in listed if short in _names(entry)), short)


def this_machine(
    listed: Sequence[Machine] | None = None,
    *,
    repo: Path = _git_runner.CHECKOUT_ROOT,
) -> Machine:
    """Return the row of the machine this script runs on (module docstring, "Identity").

    The row (``listed``, default the list of the checkout at ``repo``) whose ``name`` is
    this machine's raw name: :data:`MACHINE_ENV` when set, else :func:`this_hostname`, both
    up to the first dot, casefolded. An alias never identifies the live machine: aliases
    exist so stored records resolve, and a host answering to one, or to a name the list
    does not hold, refuses until its hostname or the list names its row. Every machine
    then records and compares by the one row name, never by whatever hostname it reports.

    Raises:
        MachineListError: the raw name is empty (an override such as ``.``), the list is
            unreadable or broken (:func:`load_machines`), or no row is named the raw name;
            the message names it and its source (and the rows).

    """
    raw, source = _raw_identity()
    if not raw:
        msg = (
            f"this machine has no name: {source} is empty before its first dot; set "
            f"${MACHINE_ENV} to its row's name"
        )
        raise MachineListError(msg)
    if listed is None:
        listed = machines(repo)
    found = next((entry for entry in listed if short_hostname(entry.name) == raw), None)
    if found is None:
        msg = (
            f"this machine is {raw!r} ({source}), which no row of the machine list names "
            f"(listed: {', '.join(entry.name for entry in listed)}); give the host its row's "
            f"name, add its row, or set ${MACHINE_ENV} to the row's name"
        )
        raise MachineListError(msg)
    return found


def this_machine_name(*, repo: Path = _git_runner.CHECKOUT_ROOT) -> str:
    """Return this machine's name for a record: :func:`this_machine`'s, else :func:`canonical`'s.

    Lenient where :func:`this_machine` is strict: on a host no row names, the raw name
    (:data:`MACHINE_ENV`, else :func:`this_hostname`) read through :func:`canonical`, so
    a host answering to an alias records its row's name, an unlisted one its own short
    name and an empty raw name ``""``. Never raises.
    """
    try:
        return this_machine(repo=repo).name
    except MachineListError:
        return canonical(_raw_identity()[0], repo=repo)


def local_machine(
    listed: Sequence[Machine],
    here: str | None,
    hostname: str | None = None,
) -> Machine | None:
    """Return the machine this script runs on, or ``None`` when no entry is this one.

    ``here`` names it outright: a row's name or ssh host, or a name :func:`canonical`
    resolves to a row (an alias included). Otherwise it is the row whose ``name`` is
    ``hostname`` when given, else this machine's raw name as :func:`this_machine` takes
    it (:data:`MACHINE_ENV`, else :func:`this_hostname`), up to its first dot, compared
    without case: an alias never identifies the live machine, and neither does a machine
    of the same OS. Unlike :func:`this_machine`, no row is ``None``, never an error.

    Raises:
        MachineListError: ``here`` names no machine of the list.

    """
    if here is not None:
        wanted = canonical(here, listed)
        for entry in listed:
            if here in {entry.name, entry.ssh} or wanted == entry.name:
                return entry
        msg = f"--here {here!r} names no machine of the list"
        raise MachineListError(msg)
    short = _raw_identity()[0] if hostname is None else short_hostname(hostname)
    return next((entry for entry in listed if short_hostname(entry.name) == short), None)


def reached_as(host: str, listed: Sequence[Machine]) -> Machine | None:
    """Return the row of ``listed`` the host name ``host`` reaches, or ``None``.

    ``host`` up to its first dot, casefolded (:func:`short_hostname`), is the row's name,
    one of its ``aliases`` or its ``ssh`` host: any case or domain form of a machine's
    names reaches it. An empty short form reaches no row.
    """
    short = short_hostname(host)
    if not short:
        return None
    return next(
        (
            entry
            for entry in listed
            if short in _names(entry) or short == short_hostname(entry.ssh)
        ),
        None,
    )


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


def ssh_user(host: str) -> str | None:
    """Return the login ssh uses for ``host`` (``ssh -G``'s ``user`` line), or ``None``.

    ``None`` when ssh cannot say: ``host`` empty or starting with ``-`` (an option to
    ssh), ssh missing, failing or slower than :data:`SSH_CONFIG_TIMEOUT`, or no ``user``
    line. ``ssh -G`` prints the configuration and connects nowhere.
    """
    if not host or host.startswith("-"):
        return None
    try:
        result = subprocess.run(
            ["ssh", "-G", host],
            capture_output=True,
            text=True,
            check=False,
            timeout=SSH_CONFIG_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        key, _, value = line.strip().partition(" ")
        if key.casefold() == "user" and value.strip():
            return value.strip()
    return None
