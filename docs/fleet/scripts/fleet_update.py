"""Bring every fleet machine to the pinned tool versions, and report what drifts.

Usage, from ``~/projects/django-strawberry-framework`` on any fleet machine::

    uv run python docs/fleet/scripts/fleet_update.py check [--all] [--json]
    uv run python docs/fleet/scripts/fleet_update.py apply [--all | --deferred] [--json]
    uv run python docs/fleet/scripts/fleet_update.py schedule [--install]
    uv run python docs/fleet/scripts/fleet_update.py sudoers

Pins
    ``docs/fleet/scripts/setup/versions.json`` (``fleet_setup.VERSIONS_FILE``, read by
    ``fleet_setup.load_versions``) holds one line per tool: an exact release, or
    ``latest`` for a tool whose vendor installer takes no version (Muse, grok, Antigravity:
    ``fleet_setup.VENDOR_INSTALLERS``). Bumping a version is a one-line commit
    on main; the save-sync timers fast-forward every machine's main
    (``docs/fleet/scripts/fleet_sync.py`` "Periodic runs"), and each machine's next
    ``apply`` installs exactly that version. :data:`TOOLS` must name exactly the pinned
    tools, a vendor tool must read ``latest`` and every other tool an exact release; a file
    breaking that is refused (exit 2).

Tools
    :data:`TOOLS`, in the order ``apply`` brings them up: nvm, node, npm, Codex, Claude
    Code, uv, pre-commit, osv-scanner, OpenCode (OpenCode 2's installer,
    ``fleet_setup.OPENCODE_INSTALLER``, given the pin), then the three ``latest`` tools. nvm
    is sourced in a ``bash`` subprocess without switching node (``fleet_setup.nvm``), never in
    this process: node is nvm's ``default`` alias, and npm and Codex are read and installed
    after an explicit switch to that node (``fleet_setup.under_default``), whatever node the
    caller's ``PATH`` holds (Codex as ``@openai/codex``, a global npm package: the one way
    every machine installs it). Each tool is installed by
    ``docs/fleet/scripts/fleet_setup.py``'s line builder for it, the same lines a new box
    runs; node's carries the previous default's global packages over
    (``--reinstall-packages-from``) and sets ``nvm alias default`` to the pin.

``check``
    Read-only. One row per tool: its pin, the version installed, and a status: ``ok``,
    ``missing``, ``behind``, ``differs`` (past the pin, for a tool nothing but ``apply``
    moves), ``ahead`` (past the pin, for a tool that updates itself: Claude Code, never
    downgraded), ``drift`` (node at the pin while nvm's ``default`` alias names something
    else) or ``latest`` (a ``latest`` tool's version, compared across machines by
    ``--all``). A ``shadowed`` row names a file that runs instead of the managed tool: a
    ``codex`` on the fleet ``PATH`` other than nvm's default node's (an npm prefix of its own,
    a standalone binary), or an nvm node there other than the default (the PATH block,
    ``setup/files/path.sh``, adds the newest); it is never deleted, and the row prints the
    command that removes it. The fleet ``PATH`` (:func:`fleet_path`) is the PATH block read
    afresh over :data:`BASE_PATH`, behind nvm's default node's ``bin``, never the caller's
    own: the same for an ssh session, the timer and an interactive shell; one that cannot be
    read is an ``error`` row. Then the OS updates pending: ``apt`` (``apt list --upgradable``,
    from the lists the last ``apt-get update`` fetched) and ``snap`` (``snap refresh
    --list``) on Linux, ``brew`` (``brew outdated --greedy``, casks included, with
    Homebrew's auto-update off) and ``macos`` (``softwareupdate -l``) on macOS. On macOS an
    ``app <name>`` row per listed app installed (below, "Apps"); a ``deferred <family>`` row
    per family the last ``apply`` deferred, with how long it has waited; a ``hold <package>``
    row per package an ``apply`` held and has not unheld yet: ``held`` while that run is
    alive, ``stale`` once it ended without unholding (the next ``apply`` unholds it). Exit 1
    on drift (:func:`drifted`: :data:`DRIFT`, an app row aside); pending OS updates, a
    ``behind`` app and a deferred family are not drift.

Apps
    ``setup/versions.json``'s ``apps`` object (``fleet_setup.load_apps``) lists the desktop
    agent and dev apps, one line each: its product family (:data:`FAMILIES`), macOS bundle
    id, Homebrew cask token and Linux apt package; an app a machine lacks is skipped. macOS
    is report only: the apps are drag-installed and update themselves, so the row reads the
    installed ``CFBundleShortVersionString`` (the ``.app`` in ``/Applications`` or
    ``~/Applications`` whose ``CFBundleIdentifier`` is the bundle id) against the cask's
    version from ``brew info --cask --json=v2`` (a read), ``ok`` or ``behind`` (``report``
    under ``apply``); nothing here installs, upgrades, quits or modifies one, and
    ``brew upgrade`` leaves a listed cask alone. On Linux the vendor apt repositories'
    packages come with ``apt-get upgrade``; snapd postpones a running snap app's refresh
    itself.

Busy
    Nothing is upgraded while an agent works. A family (:data:`FAMILIES`: one product's CLI
    and desktop app, node and npm, uv and pre-commit) is busy while any process runs from one
    of its install locations: the command line's executable path (on Linux
    ``/proc/<pid>/exe``; on macOS ``lsof``'s text file for a command started by a bare
    name), or the script a node process runs, matched against the family's folders and
    files, never a loose name; a macOS app's bundle folder joins its family. ``apply``'s own
    process, its children and the launchers whose command line runs this script (``uv run``,
    the timer's shell) never count; the Claude Code session it runs in does. A tool step of
    a busy family (:class:`Tool` ``family``) that would install is skipped with a ``busy``
    row naming the family and its pids. On Linux each installed listed app of a busy family
    is held around the upgrade (``sudo -n /usr/bin/apt-mark hold <package>``, ``apt-get
    upgrade -y``, ``apt-mark unhold`` in a ``finally``); each package held is recorded in
    ``.work/update-holds.json`` before the upgrade, so a run killed mid-way is unheld by the
    next ``apply``; a package held before (``apt-mark showhold``) is neither held nor unheld.
    A hold that fails (a sudoers rule without the ``apt-mark`` lines) makes the upgrade one
    ``busy`` row: nothing is upgraded unheld. Each family a run skipped is written to
    ``.work/update-deferred.json`` with when it first waited; ``apply --deferred`` (the hourly
    retry timer) runs only those families' steps (on Linux the apt upgrade when one has a
    listed apt package) and does nothing when none waits.

``apply``
    Brings this machine to the pins, one line per step, then the OS packages: on Linux
    ``sudo -n`` runs exactly ``/usr/bin/apt-get update``, ``/usr/bin/apt-get upgrade -y``
    and ``/usr/bin/snap refresh`` (the three the sudoers rule allows, below, with the
    ``apt-mark`` holds of "Busy"); a ``sudo`` refusal is one ``refused`` row naming the
    missing rule and nothing prompts. On macOS ``brew update`` and ``brew upgrade --greedy``
    (naming the outdated formulae and casks instead when a listed app's cask is among them,
    which is left alone), then the app rows; a macOS system update is never run, only
    listed (``softwareupdate -l``). A tool already at its pin, or ``ahead``, is left
    alone; a ``latest`` tool's installer runs every time; a tool of a busy family is
    ``busy`` ("Busy"). Each install is read back: a tool not at its pin afterwards is
    ``failed``. It holds ``.work/update.lock`` (a kernel lock: a second ``apply`` on the
    machine is ``locked``), refuses while the fleet stop flag is set
    (``docs/fleet/scripts/fleet_stop.py``'s ``.work/fleet-stop``) and reads the flag again
    before every step, ending with a ``stopped`` row when it appears. Exit 1 when a step
    failed, was refused or stopped (:data:`TROUBLE`).

``--all``
    ``check`` or ``apply`` on every machine of ``docs/fleet/machines.json`` in parallel:
    this machine in-process, every other over ssh (``fleet.ssh_argv``) running that
    machine's own checkout copy of this script (``.venv`` Python, else ``python3``) with
    ``--json``; one table back. A machine ssh cannot reach is an ``unreached`` row; a
    checkout without this script yet, an ``error`` row. ``check --all`` also marks a
    ``latest`` tool older than the newest on any machine as ``drift``.

``schedule``
    Two timers, as ``fleet_sync.py schedule`` builds its own: a launchd agent each on
    macOS (``StartCalendarInterval``, missed runs fire on wake), systemd user units on Linux
    (``OnCalendar`` with ``Persistent=true``), running from the checkout's ``.venv`` Python
    ``apply`` daily at :data:`SCHEDULE_HOUR` and :data:`SCHEDULE_MINUTE` local time and
    ``apply --deferred`` hourly at :data:`RETRY_MINUTE` past the hour, each put off
    a random 0 to :data:`SCHEDULE_JITTER` seconds, killed after
    :data:`SCHEDULE_TIME_LIMIT` seconds, appending to ``.work/fleet-update.log``, and
    skipped by a shell check of the stop flag before any Python starts. ``schedule`` alone
    prints the files and the commands; ``--install`` writes and loads them (the
    maintainer's step, once per machine; again after the timer file changes).

``sudoers``
    Prints the drop-in ``setup/files/sudoers-fleet-update`` with this account rendered in
    (the tracked file names no user) and its ``@APT_MARK@`` line rendered once per command
    of :func:`hold_commands`: ``/usr/bin/apt-mark hold <package>`` and ``unhold <package>``
    for each listed app's apt package, exact, no wildcard; and one command that installs it as
    ``/etc/sudoers.d/dsf-fleet-update``: staged root-owned with mode 0440 under a dotted
    name sudo's ``includedir`` skips, validated with ``visudo -cf``, then moved into
    place; a stage that fails validation is removed. Run once per Linux machine.

Exit 0 clean, 1 drift (``check``) or a failed, refused, stopped or locked step (``apply``;
a ``busy`` step is deferred, not trouble), 2 a bad
setup (an unreadable or inconsistent ``versions.json``, an unsupported OS for
``schedule``). Standard library plus ``docs/fleet/scripts/fleet.py`` (machines, ssh),
``docs/fleet/scripts/fleet_setup.py`` (the pins and the install lines),
``docs/fleet/scripts/fleet_stop.py`` (the flag) and ``scripts/_locks.py`` (the lock).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import dataclasses
import getpass
import json
import os
import platform
import plistlib
import re
import shlex
import shutil
import subprocess
import sys
import time
import xml.parsers.expat
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

if __package__:  # imported as ``docs.fleet.scripts.fleet_update`` (repo root on path)
    from docs.fleet.scripts import fleet, fleet_setup, fleet_stop
    from scripts import _git as _git_runner
    from scripts import _locks
else:  # run or imported from its own folder: the lock and git plumbing live in scripts/
    sys.path.insert(1, str(Path(__file__).resolve().parents[3] / "scripts"))
    import _git as _git_runner
    import _locks
    import fleet
    import fleet_setup
    import fleet_stop

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Mapping, Sequence

#: ``json.loads`` and ``plistlib.loads``, their results typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads
_plist: Callable[[bytes], object] = plistlib.loads

ROOT = _git_runner.CHECKOUT_ROOT
#: This script, relative to a checkout (what ``--all`` runs on each machine).
SCRIPT = "docs/fleet/scripts/fleet_update.py"
LATEST = fleet_setup.LATEST
#: The lock ``apply`` holds, under the checkout's ``.work/``.
LOCK = "update.lock"
#: Seconds a version probe may take.
PROBE_TIMEOUT = 60.0
#: Seconds one tool's install may take.
INSTALL_TIMEOUT = 1800.0
#: Seconds one OS package step may take (an upgrade of many packages).
OS_TIMEOUT = 3600.0
#: Seconds ``--all`` waits for one machine's ``check`` and ``apply``.
REMOTE_TIMEOUT = {"check": 900.0, "apply": 4 * 3600.0}
#: What ``run`` reports for a command that could not start, and one past its time.
NOT_RUN = 127
TIMED_OUT = 124
#: The system ``PATH`` the fleet PATH block is read over (:func:`fleet_path`).
BASE_PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
#: The statuses ``check`` exits 1 on.
DRIFT = frozenset(
    {
        "missing",
        "behind",
        "differs",
        "drift",
        "shadowed",
        "error",
        "unreached",
        "stray",
        "stale",
    },
)
#: The statuses ``apply`` exits 1 on.
TROUBLE = frozenset(
    {
        "failed",
        "refused",
        "stopped",
        "locked",
        "error",
        "unreached",
    },
)
#: The statuses ``apply`` installs on.
ACTIONABLE = frozenset(
    {
        "missing",
        "behind",
        "differs",
        "drift",
        "latest",
    },
)
#: The commands ``apply`` runs as root on Linux: exactly the sudoers rule's three.
SUDO_COMMANDS = (
    ("/usr/bin/apt-get", "update"),
    ("/usr/bin/apt-get", "upgrade", "-y"),
    ("/usr/bin/snap", "refresh"),
)
#: The upgrade among them, the one a busy app's package is held around ("Busy").
UPGRADE = SUDO_COMMANDS[1]
#: ``apt-mark``, holding and unholding a package (the sudoers rule names each, exactly).
APT_MARK = "/usr/bin/apt-mark"
#: The state files under the checkout's ``.work/``: the packages held and not yet unheld,
#: and the families a run deferred.
HOLDS_STATE = "update-holds.json"
DEFERRED_STATE = "update-deferred.json"
#: An app row's item prefix (``app Claude``).
APP_ITEM = "app "
#: The most pids a ``busy`` row names.
PID_LIMIT = 8
#: The sudoers drop-in, ``@USER@`` and ``@APT_MARK@`` rendered by ``sudoers``.
SUDOERS_FILE = Path(__file__).resolve().parent / "setup" / "files" / "sudoers-fleet-update"
SUDOERS_DIR = "/etc/sudoers.d"
SUDOERS_NAME = "dsf-fleet-update"
#: An account name safe to render into the drop-in and the shell command.
ACCOUNT = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
VERSION = fleet_setup.VERSION


class UpdateError(Exception):
    """A refusal; the message says why and what to do (exit 2)."""


class LockedError(UpdateError):
    """Another ``apply`` holds the update lock, or it could not be taken."""


@dataclasses.dataclass(frozen=True)
class Ran:
    """A finished command: its exit code, stdout and stderr."""

    code: int
    out: str
    err: str

    def last_line(self) -> str:
        """Return the last non-blank line of stderr, else of stdout, else the exit code."""
        for stream in (self.err, self.out):
            lines = [line.strip() for line in stream.splitlines() if line.strip()]
            if lines:
                return lines[-1]
        return f"exit {self.code}"


def run(
    argv: Sequence[str],
    *,
    timeout: float,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> Ran:
    """Run ``argv`` with no stdin; every command this script starts goes through here.

    A command that cannot start is exit :data:`NOT_RUN`, one past ``timeout``
    :data:`TIMED_OUT` (killed); neither raises.
    """
    try:
        completed = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
            env=None if env is None else dict(env),
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        return Ran(TIMED_OUT, "", f"{argv[0]} timed out after {timeout:g}s")
    except OSError as error:
        return Ran(NOT_RUN, "", f"{argv[0]}: {error}")
    return Ran(completed.returncode, completed.stdout, completed.stderr)


@dataclasses.dataclass(frozen=True)
class Host:
    """The machine a ``check`` or ``apply`` runs on: its box, CPU and checkout."""

    box: fleet_setup.Box
    arch: str
    root: Path
    #: Its ``machines.json`` row lets ``~/projects`` hold other entries (``fleet_setup.strays``).
    other_projects: bool = False
    #: The folders a macOS app is looked for in (module docstring, "Apps").
    applications: tuple[Path, ...] = ()
    #: Linux's ``/proc``, where a process's executable is read (``None``: not read).
    proc: Path | None = None
    #: The ``apply`` process itself, whose own tree is never busy (``0``: none).
    pid: int = 0

    @classmethod
    def here(cls) -> Host:
        """Return this machine (a machine the list does not name holds no other projects)."""
        try:
            other = fleet.this_machine(repo=ROOT).other_projects
        except fleet.MachineListError:
            other = False
        box = fleet_setup.Box.here()
        linux = box.system == fleet_setup.LINUX
        return cls(
            box,
            platform.machine(),
            ROOT,
            other,
            applications=() if linux else (Path("/Applications"), box.home / "Applications"),
            proc=Path("/proc") if linux else None,
            pid=os.getpid(),
        )

    @property
    def nvm_dir(self) -> Path:
        """Return nvm's folder."""
        return self.box.home / ".nvm"

    @property
    def linux(self) -> bool:
        """Return whether this is a Linux machine (else macOS)."""
        return self.box.system == fleet_setup.LINUX

    def bash(self, script: str, timeout: float = PROBE_TIMEOUT) -> Ran:
        """Run ``script`` in ``bash -c`` with ``~/.local/bin`` first and ``NVM_DIR`` set."""
        return run(
            ["bash", "-c", script],
            timeout=timeout,
            env=fleet_setup.box_env(self.box),
            cwd=self.box.home,
        )

    def git(self, folder: Path, args: Sequence[str]) -> tuple[int, str]:
        """Run ``git -C folder args`` (``fleet_setup.git_argv``); return its code and stdout."""
        ran = run(
            fleet_setup.git_argv(folder, args),
            timeout=PROBE_TIMEOUT,
            env=fleet_setup.git_env(fleet_setup.box_env(self.box)),
        )
        return ran.code, ran.out.strip()


@dataclasses.dataclass(frozen=True)
class Row:
    """One line of a report: what, its pin, what is there, the status and why."""

    item: str
    pinned: str
    installed: str
    status: str
    detail: str = ""

    def as_json(self) -> dict[str, str]:
        """Return the row as a JSON object."""
        return dataclasses.asdict(self)

    @classmethod
    def from_json(cls, value: object) -> Row:
        """Return the row a JSON object holds.

        Raises:
            ValueError: ``value`` is not an object of the row's string fields.

        """
        if not fleet.is_json_object(value):
            msg = f"a row must be an object, got {value!r}"
            raise ValueError(msg)
        fields = {
            name: value.get(name, "")
            for name in (
                "item",
                "pinned",
                "installed",
                "status",
                "detail",
            )
        }
        strings = {name: text for name, text in fields.items() if isinstance(text, str)}
        if len(strings) != len(fields) or not strings["item"] or not strings["status"]:
            msg = f"a row needs string item, pinned, installed, status and detail: {value!r}"
            raise ValueError(msg)
        return cls(**strings)


@dataclasses.dataclass(frozen=True)
class Report:
    """One machine's rows."""

    machine: str
    rows: tuple[Row, ...]

    def as_json(self) -> dict[str, object]:
        """Return the report as a JSON object."""
        return {"machine": self.machine, "rows": [row.as_json() for row in self.rows]}


# --------------------------------------------------------------------------------------------
# Versions
# --------------------------------------------------------------------------------------------


version_of = fleet_setup.version_of
numbers = fleet_setup.numbers


def compare(pin: str, installed: str, *, self_updating: bool = False) -> str:
    """Return a tool's status: its ``installed`` version against its ``pin``."""
    if not installed:
        return "missing"
    if pin == LATEST:
        return "latest"
    have, want = numbers(installed), numbers(pin)
    if have == want:
        return "ok"
    if have < want:
        return "behind"
    return "ahead" if self_updating else "differs"


# --------------------------------------------------------------------------------------------
# Tools: how each installed version is read, and the lines that install a version
# --------------------------------------------------------------------------------------------


def _nvm_version(host: Host) -> str:
    ran = host.bash(fleet_setup.nvm("nvm --version"))
    return version_of(ran.out) if ran.code == 0 else ""


def _node_version(host: Host) -> str:
    ran = host.bash(fleet_setup.nvm("nvm version default"))
    return version_of(ran.out) if ran.code == 0 else ""


def _npm_version(host: Host) -> str:
    ran = host.bash(fleet_setup.under_default("npm --version"))
    return version_of(ran.out) if ran.code == 0 else ""


def _codex_version(host: Host) -> str:
    # ``npm ls`` exits 1 on any problem in the tree (an extraneous package) yet lists it.
    ran = host.bash(fleet_setup.under_default("npm ls -g --depth=0 --json"))
    try:
        listing = _loads(ran.out)
    except ValueError:
        return ""
    packages = listing.get("dependencies") if fleet.is_json_object(listing) else None
    codex = packages.get("@openai/codex") if fleet.is_json_object(packages) else None
    version = codex.get("version") if fleet.is_json_object(codex) else None
    return version if isinstance(version, str) else ""


def _binary(*parts: str) -> Callable[[Host], str]:
    """Return the probe running ``~/<parts> --version``."""

    def probe(host: Host) -> str:
        path = host.box.home.joinpath(*parts)
        if not path.exists():
            return ""
        ran = run(
            [str(path), "--version"],
            timeout=PROBE_TIMEOUT,
            env=fleet_setup.box_env(host.box),
        )
        return version_of(ran.out) if ran.code == 0 else ""

    return probe


def _node_lines(_host: Host, pin: str, installed: str) -> list[str]:
    if installed and numbers(installed) == numbers(pin):  # only the alias drifted
        return [fleet_setup.nvm(f"nvm alias default {shlex.quote(pin)}")]
    return fleet_setup.node_lines(pin, f"v{installed}" if installed else "")


def _osv_lines(host: Host, pin: str, _installed: str) -> list[str]:
    return fleet_setup.osv_lines(host.box.bin, pin, host.box.system, host.arch)


def _vendor(key: str) -> Callable[[Host, str, str], list[str]]:
    def lines(_host: Host, _pin: str, _installed: str) -> list[str]:
        return fleet_setup.vendor_lines(fleet_setup.VENDOR_INSTALLERS[key])

    return lines


@dataclasses.dataclass(frozen=True)
class Tool:
    """One pinned tool: how its installed version is read and the lines that install a pin."""

    key: str
    installed: Callable[[Host], str]
    #: The lines installing ``pin`` over ``installed`` (``""`` when absent).
    lines: Callable[[Host, str, str], list[str]]
    #: Its own updater moves it past the pin: ``ahead``, never downgraded.
    self_updating: bool = False
    #: Its status and detail from the pin and the installed reading, in place of
    #: :func:`compare` (a reference source: a tree or a clone, not a binary's version).
    assess: Callable[[Host, str, str], tuple[str, str]] | None = None
    #: The family (:data:`FAMILIES`) whose running processes defer its install (``""``: none).
    family: str = ""


def _strawberry_django_status(host: Host, pin: str, installed: str) -> tuple[str, str]:
    if not (host.box.home / fleet_setup.PROJECTS / fleet_setup.STRAWBERRY_DJANGO_DIR).exists():
        return "missing", ""
    if not installed:
        return "differs", "its pyproject.toml names no release version"
    return compare(pin, installed), ""


def _filters_status(host: Host, pin: str, _installed: str) -> tuple[str, str]:
    return fleet_setup.filters_status(host.box.home, pin, host.git)


TOOLS: tuple[Tool, ...] = (
    Tool(
        "nvm",
        _nvm_version,
        lambda _host, pin, _installed: fleet_setup.nvm_lines(pin, "/dev/null"),
    ),
    Tool("node", _node_version, _node_lines, family="node"),
    Tool(
        "npm",
        _npm_version,
        lambda _host, pin, _installed: fleet_setup.npm_global_lines("npm", pin),
        family="node",
    ),
    Tool(
        "codex",
        _codex_version,
        lambda _host, pin, _installed: fleet_setup.npm_global_lines("@openai/codex", pin),
        family="codex",
    ),
    Tool(
        "claude",
        _binary(".local", "bin", "claude"),
        lambda _host, pin, _installed: fleet_setup.claude_lines(pin),
        self_updating=True,
        family="claude",
    ),
    Tool(
        "uv",
        _binary(".local", "bin", "uv"),
        lambda _host, pin, _installed: fleet_setup.uv_lines(pin, modify_path=False),
        family="uv",
    ),
    Tool(
        "pre-commit",
        _binary(".local", "bin", "pre-commit"),
        lambda _host, pin, _installed: fleet_setup.pre_commit_lines(pin),
        family="uv",
    ),
    Tool("osv-scanner", _binary(".local", "bin", "osv-scanner"), _osv_lines),
    Tool(
        "opencode",
        _binary(".opencode", "bin", "opencode"),
        lambda _host, pin, _installed: fleet_setup.opencode_lines(pin),
        family="opencode",
    ),
    Tool("muse", _binary(".local", "bin", "muse"), _vendor("muse"), family="muse"),
    Tool("grok", _binary(".grok", "bin", "grok"), _vendor("grok"), family="grok"),
    Tool("agy", _binary(".local", "bin", "agy"), _vendor("agy"), family="antigravity"),
    Tool(
        "strawberry-django",
        lambda host: fleet_setup.strawberry_django_version(host.box.home),
        lambda _host, pin, installed: fleet_setup.strawberry_django_lines(pin, installed),
        assess=_strawberry_django_status,
    ),
    Tool(
        fleet_setup.FILTERS_DIR,
        lambda host: fleet_setup.filters_described(host.box.home, host.git),
        lambda _host, pin, _installed: fleet_setup.filters_lines(pin),
        assess=_filters_status,
    ),
    Tool(
        "graphene-django",
        lambda host: fleet_setup.graphene_django_version(host.box.home),
        lambda _host, _pin, _installed: fleet_setup.graphene_django_lines(),
    ),
)


def pins(path: Path | None = None) -> dict[str, str]:
    """Return every tool's pin, checked against :data:`TOOLS` (module docstring, "Pins").

    ``path`` defaults to ``fleet_setup.VERSIONS_FILE``.

    Raises:
        UpdateError: the file is unreadable, or it and :data:`TOOLS` disagree.

    """
    path = fleet_setup.VERSIONS_FILE if path is None else path
    try:
        pinned = fleet_setup.load_versions(path)
    except (OSError, ValueError) as error:
        msg = f"cannot read the pins: {error}"
        raise UpdateError(msg) from error
    keys = [tool.key for tool in TOOLS]
    problems = [f"no pin for {key}" for key in keys if key not in pinned]
    problems += [f"{key} is no tool this script installs" for key in pinned if key not in keys]
    for key, version in pinned.items():
        vendor = key in fleet_setup.VENDOR_INSTALLERS
        if vendor and version != LATEST:
            problems.append(f"{key} has no versioned installer: pin it {LATEST!r}")
        elif not vendor and key in keys and not numbers(version):
            problems.append(f"{key} needs an exact release, not {version!r}")
    if problems:
        msg = f"{path}: {'; '.join(problems)}"
        raise UpdateError(msg)
    return pinned


# --------------------------------------------------------------------------------------------
# Families: what makes one busy, and the apps
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Family:
    """One product family: where its processes run from, on both OSes and on each.

    A location is a path (``~/`` the home folder): a folder when it ends in ``/``, else a
    file; ``*`` stands for one path segment (a version folder). A listed macOS app adds its
    bundle's folder (:func:`app_bundles`).
    """

    name: str
    both: tuple[str, ...] = ()
    macos: tuple[str, ...] = ()
    linux: tuple[str, ...] = ()


#: The one table of the families and their install locations (module docstring, "Busy").
FAMILIES: tuple[Family, ...] = (
    Family(
        "claude",
        both=("~/.local/bin/claude", "~/.local/share/claude/"),
        macos=("~/Library/Application Support/Claude/claude-code/",),
        linux=("/usr/lib/claude-desktop/",),
    ),
    Family(
        "codex",
        both=(
            "~/.codex/",
            "~/.nvm/versions/node/*/bin/codex",
            "~/.nvm/versions/node/*/lib/node_modules/@openai/codex/",
        ),
        macos=("~/Library/Application Support/Codex/",),
        linux=("/usr/lib/chatgpt/", "~/.config/Codex/"),
    ),
    Family("opencode", both=("~/.opencode/",), linux=("/opt/OpenCode/",)),
    Family("antigravity", both=("~/.local/bin/agy",), linux=("/usr/share/antigravity/",)),
    Family("grok", both=("~/.grok/",), linux=("/opt/Grok Bot/",)),
    Family("muse", both=("~/.local/bin/muse",)),
    Family(
        "cursor",
        macos=("~/Library/Application Support/Cursor/",),
        linux=("/usr/share/cursor/",),
    ),
    Family("vscode", linux=("/usr/share/code/",)),
    Family("t3code", linux=("/opt/T3 Code (Beta)/",)),
    Family("devin", linux=("/usr/share/windsurf/",)),
    Family("warp", linux=("/opt/warpdotdev/",)),
    Family("ghostty", linux=("/usr/bin/ghostty",)),
    Family("node", both=("~/.nvm/versions/node/",)),
    Family(
        "uv",
        both=(
            "~/.local/bin/uv",
            "~/.local/bin/uvx",
            "~/.local/bin/pre-commit",
            "~/.local/share/uv/tools/pre-commit/",
        ),
    ),
)
App = fleet_setup.App


def apps(path: Path | None = None) -> tuple[App, ...]:
    """Return the listed apps (``fleet_setup.load_apps``), each family one of :data:`FAMILIES`.

    ``path`` defaults to ``fleet_setup.VERSIONS_FILE``.

    Raises:
        UpdateError: the file is unreadable, or an app names a family the table lacks.

    """
    path = fleet_setup.VERSIONS_FILE if path is None else path
    try:
        listed = fleet_setup.load_apps(path)
    except (OSError, ValueError) as error:
        msg = f"cannot read the apps: {error}"
        raise UpdateError(msg) from error
    known = {family.name for family in FAMILIES}
    unknown = [
        f"{app.name}: no family {app.family!r}" for app in listed if app.family not in known
    ]
    if unknown:
        msg = f"{path}: {'; '.join(unknown)}"
        raise UpdateError(msg)
    return listed


def location_pattern(location: str, home: Path) -> re.Pattern[str]:
    """Return the pattern a command line or executable path starting at ``location`` matches.

    A folder matches anything under it; a file itself, alone or followed by its arguments.
    """
    path = f"{home}/{location[2:]}" if location.startswith("~/") else location
    body = "[^/]*".join(re.escape(part) for part in path.split("*"))
    return re.compile(body if path.endswith("/") else f"{body}(?: |$)")


def family_patterns(
    host: Host,
    bundles: Mapping[str, Sequence[Path]],
) -> dict[str, list[re.Pattern[str]]]:
    """Return each family's location patterns on ``host``, its apps' ``bundles`` folders added."""
    patterns: dict[str, list[re.Pattern[str]]] = {}
    for family in FAMILIES:
        own = family.linux if host.linux else family.macos
        locations = [*family.both, *own, *(f"{path}/" for path in bundles.get(family.name, ()))]
        patterns[family.name] = [location_pattern(where, host.box.home) for where in locations]
    return patterns


@dataclasses.dataclass(frozen=True)
class Process:
    """One running process: its pid, its parent's, its command line and executable."""

    pid: int
    ppid: int
    args: str
    #: The executable's real path, where the OS tells it (``""``: unknown).
    exe: str = ""


def _linux_exe(proc: Path, pid: int) -> str:
    try:
        target = str((proc / str(pid) / "exe").readlink())
    except OSError:
        return ""
    return target.removesuffix(" (deleted)")


def _bare(process: Process) -> bool:
    return bool(process.args) and "/" not in process.args.split(maxsplit=1)[0]


def _macos_exes(processes: Sequence[Process]) -> dict[int, str]:
    """Return the executable of each process started by a bare name: ``lsof``'s first text file."""
    pids = [str(process.pid) for process in processes if _bare(process)]
    if not pids:
        return {}
    ran = run(
        [
            "/usr/sbin/lsof",
            "-a",
            "-d",
            "txt",
            "-Fpn",
            "-p",
            ",".join(pids),
        ],
        timeout=PROBE_TIMEOUT,
    )
    exes: dict[int, str] = {}
    pid = 0
    for line in ran.out.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            pid = int(line[1:])
        elif line.startswith("n") and pid and pid not in exes:
            exes[pid] = line[1:]
    return exes


def processes(host: Host) -> list[Process]:
    """Return the running processes (``ps``), each with its executable where the OS tells it.

    Raises:
        UpdateError: ``ps`` failed.

    """
    ran = run(
        [
            "ps",
            "-A",
            "-ww",
            "-o",
            "pid=,ppid=,args=",
        ],
        timeout=PROBE_TIMEOUT,
        env=fleet_setup.box_env(host.box),
    )
    if ran.code != 0:
        msg = f"cannot list the running processes: {ran.last_line()}"
        raise UpdateError(msg)
    found: list[Process] = []
    for line in ran.out.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            found.append(Process(int(parts[0]), int(parts[1]), parts[2] if len(parts) > 2 else ""))
    if host.proc is not None:
        proc = host.proc
        return [dataclasses.replace(each, exe=_linux_exe(proc, each.pid)) for each in found]
    if host.linux:
        return found
    exes = _macos_exes(found)
    return [dataclasses.replace(each, exe=exes.get(each.pid, "")) for each in found]


def own_tree(found: Sequence[Process], pid: int) -> set[int]:
    """Return ``pid``, its descendants, and the launchers above it that run this script."""
    children: dict[int, list[int]] = {}
    by_pid = {process.pid: process for process in found}
    for process in found:
        children.setdefault(process.ppid, []).append(process.pid)
    own = {pid}
    waiting = [pid]
    while waiting:
        for child in children.get(waiting.pop(), []):
            if child not in own:
                own.add(child)
                waiting.append(child)
    script = Path(SCRIPT).name
    current = by_pid.get(pid)
    while current is not None:
        parent = by_pid.get(current.ppid)
        if parent is None or parent.pid in own or script not in parent.args:
            break
        own.add(parent.pid)
        current = parent
    return own


def candidates(process: Process) -> list[str]:
    """Return what identifies ``process``: its command line, executable, a node's script."""
    found = [process.args]
    head, _, rest = process.args.partition(" ")
    if process.exe:
        found.append(process.exe)
        if process.args.startswith(f"{process.exe} "):
            head, rest = process.exe, process.args[len(process.exe) + 1 :]
    if "node" in {Path(head).name, Path(process.exe).name}:
        found.append(rest.lstrip())
    return [text for text in found if text]


def busy(host: Host, bundles: Mapping[str, Sequence[Path]]) -> dict[str, tuple[int, ...]]:
    """Return each busy family's pids: the processes running from its locations, own tree aside.

    Raises:
        UpdateError: the processes could not be listed.

    """
    found = processes(host)
    own: set[int] = own_tree(found, host.pid) if host.pid else set()
    patterns = family_patterns(host, bundles)
    running: dict[str, list[int]] = {}
    for process in found:
        if process.pid in own:
            continue
        texts = candidates(process)
        for family, compiled in patterns.items():
            if any(pattern.match(text) for pattern in compiled for text in texts):
                running.setdefault(family, []).append(process.pid)
    return {family: tuple(pids) for family, pids in running.items()}


def busy_detail(family: str, pids: Sequence[int]) -> str:
    """Return what a ``busy`` row says: the family and the pids found."""
    return f"{family} is running (pids {_names(map(str, pids), PID_LIMIT)})"


@dataclasses.dataclass(frozen=True)
class Installed:
    """A macOS app found: its bundle's path and ``CFBundleShortVersionString``."""

    path: Path
    version: str


def bundle_info(path: Path) -> tuple[str, str]:
    """Return the ``.app`` at ``path``'s bundle id and short version (``""`` each when unread)."""
    try:
        info = _plist((path / "Contents" / "Info.plist").read_bytes())
    except (OSError, ValueError, xml.parsers.expat.ExpatError):
        return "", ""
    if not fleet.is_json_object(info):
        return "", ""
    bundle = info.get("CFBundleIdentifier")
    version = info.get("CFBundleShortVersionString")
    return (bundle if isinstance(bundle, str) else "", version if isinstance(version, str) else "")


def app_bundles(host: Host, listed: Sequence[App]) -> dict[App, Installed]:
    """Return each listed app installed in ``host.applications``, found by its bundle id."""
    by_bundle = {app.bundle: app for app in listed if app.bundle}
    found: dict[App, Installed] = {}
    for folder in host.applications:
        try:
            entries = sorted(folder.glob("*.app"))
        except OSError:
            continue
        for path in entries:
            bundle, version = bundle_info(path)
            app = by_bundle.get(bundle)
            if app is not None and app not in found:
                found[app] = Installed(path, version)
    return found


def bundle_folders(found: Mapping[App, Installed]) -> dict[str, list[Path]]:
    """Return each family's app bundles among ``found``."""
    folders: dict[str, list[Path]] = {}
    for app, installed in found.items():
        folders.setdefault(app.family, []).append(installed.path)
    return folders


def cask_versions(host: Host, casks: Sequence[str]) -> tuple[dict[str, str], str]:
    """Return each cask's latest version (``brew info --cask --json=v2``, a read) and any error.

    A version reads up to its first comma (``5.1231.2,<build>``). One call for all; when it
    fails, one per cask, so an unknown token costs only its own row.
    """
    found = brew(host)
    if not found:
        return {}, "no Homebrew: the latest release is unknown"
    if not casks:
        return {}, ""

    def read(tokens: Sequence[str]) -> tuple[dict[str, str], str]:
        ran = run(
            [
                found,
                "info",
                "--cask",
                "--json=v2",
                *tokens,
            ],
            timeout=OS_TIMEOUT,
            env=_brew_env(host),
        )
        try:
            document = _loads(ran.out)
        except ValueError:
            document = None
        listed = document.get("casks") if fleet.is_json_object(document) else None
        versions: dict[str, str] = {}
        for cask in listed if fleet.is_json_array(listed) else []:
            token = cask.get("token") if fleet.is_json_object(cask) else None
            version = cask.get("version") if fleet.is_json_object(cask) else None
            if isinstance(token, str) and isinstance(version, str):
                versions[token] = version.split(",", 1)[0]
        return versions, "" if ran.code == 0 else ran.last_line()

    versions, error = read(casks)
    if not error:
        return versions, ""
    errors: list[str] = []
    for token in casks:
        one, problem = read([token])
        versions.update(one)
        if problem:
            errors.append(problem)
    return versions, "; ".join(errors)


def app_rows(host: Host, found: Mapping[App, Installed], *, applying: bool) -> list[Row]:
    """Return an ``app <name>`` row per app ``found``: installed against the cask's latest.

    ``ok`` or ``behind`` (``report`` under ``apply``); an app whose latest cannot be read is
    ``report``. Only reads: never installs, upgrades, quits or modifies an app.
    """
    latest, error = cask_versions(host, [app.cask for app in found if app.cask])
    rows: list[Row] = []
    for app, installed in found.items():
        item = f"{APP_ITEM}{app.name}"
        newest = latest.get(app.cask, "")
        if not newest:
            why = (error or f"no cask {app.cask!r} answered") if app.cask else "no cask listed"
            rows.append(Row(item, "", installed.version, "report", why))
        elif numbers(installed.version) >= numbers(newest):
            rows.append(Row(item, newest, installed.version, "ok"))
        else:
            status = "report" if applying else "behind"
            detail = f"{newest} is out; it updates itself (never upgraded here)"
            rows.append(Row(item, newest, installed.version, status, detail))
    return rows


# --------------------------------------------------------------------------------------------
# State under .work/: the packages held, the families deferred
# --------------------------------------------------------------------------------------------


def _read_state(path: Path) -> dict[str, object]:
    try:
        document = _loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as error:
        msg = f"cannot read {path}: {error}"
        raise UpdateError(msg) from error
    if not fleet.is_json_object(document):
        msg = f"{path} is not a JSON object"
        raise UpdateError(msg)
    return document


def _write_state(path: Path, document: Mapping[str, object] | None) -> None:
    """Write ``document`` to ``path`` atomically; ``None`` removes the file."""
    if document is None:
        path.unlink(missing_ok=True)
        return
    path.parent.mkdir(exist_ok=True)
    staged = path.with_name(f".{path.name}.{os.getpid()}")
    _ = staged.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    _ = staged.replace(path)


def read_holds(root: Path) -> tuple[int, list[str]]:
    """Return the pid of the run that held packages and those still held (``.work/`` state).

    Raises:
        UpdateError: the state file is unreadable.

    """
    document = _read_state(root / ".work" / HOLDS_STATE)
    pid = document.get("pid", 0)
    packages = document.get("packages", [])
    held = (
        [name for name in packages if isinstance(name, str)]
        if fleet.is_json_array(packages)
        else []
    )
    return (pid if isinstance(pid, int) else 0), held


def save_holds(root: Path, packages: Sequence[str]) -> None:
    """Record ``packages`` as held by this process (none: remove the record)."""
    document = (
        {"pid": os.getpid(), "packages": list(dict.fromkeys(packages))} if packages else None
    )
    _write_state(root / ".work" / HOLDS_STATE, document)


@dataclasses.dataclass(frozen=True)
class Waiting:
    """A deferred family: since when it waits, and the pids that last kept it busy."""

    since: float
    pids: tuple[int, ...]


def read_deferred(root: Path) -> dict[str, Waiting]:
    """Return the families the last run deferred (``.work/`` state).

    Raises:
        UpdateError: the state file is unreadable.

    """
    families = _read_state(root / ".work" / DEFERRED_STATE).get("families", {})
    waiting: dict[str, Waiting] = {}
    for name, entry in families.items() if fleet.is_json_object(families) else ():
        since = entry.get("since") if fleet.is_json_object(entry) else None
        pids = entry.get("pids") if fleet.is_json_object(entry) else None
        if isinstance(since, (int, float)):
            listed = (
                [pid for pid in pids if isinstance(pid, int)] if fleet.is_json_array(pids) else []
            )
            waiting[name] = Waiting(float(since), tuple(listed))
    return waiting


def save_deferred(root: Path, waiting: Mapping[str, Waiting]) -> None:
    """Record the families ``waiting`` (none: remove the record)."""
    document = {
        "families": {
            name: {"since": entry.since, "pids": list(entry.pids)}
            for name, entry in sorted(waiting.items())
        },
    }
    _write_state(root / ".work" / DEFERRED_STATE, document if waiting else None)


@dataclasses.dataclass
class Ledger:
    """What one ``apply`` found of each family: deferred (busy) or cleared (nothing waits)."""

    deferred: dict[str, tuple[int, ...]] = dataclasses.field(default_factory=dict)
    cleared: set[str] = dataclasses.field(default_factory=set)

    def settle(
        self,
        before: Mapping[str, Waiting],
        now: float,
        *,
        finished: bool,
    ) -> dict[str, Waiting]:
        """Return the families still waiting after the run, each keeping when it first waited.

        A family the run did not reach stays as it was unless the run ``finished``.
        """
        waiting = {
            name: Waiting(before[name].since if name in before else now, pids)
            for name, pids in self.deferred.items()
        }
        if not finished:
            for name, entry in before.items():
                if name not in waiting and name not in self.cleared:
                    waiting[name] = entry
        return waiting


def _alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def waited(seconds: float) -> str:
    """Return ``seconds`` as ``2d 3h``, ``3h 12m`` or ``12m``."""
    minutes = max(0, int(seconds // 60))
    days, rest = divmod(minutes, 24 * 60)
    hours, minutes = divmod(rest, 60)
    if days:
        return f"{days}d {hours}h"
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def state_rows(root: Path, now: float | None = None) -> list[Row]:
    """Return ``check``'s rows for the state: each deferred family and each package still held."""
    now = time.time() if now is None else now
    try:
        waiting = read_deferred(root)
        pid, held = read_holds(root)
    except UpdateError as error:
        return [Row("state", "", "", "error", str(error))]
    rows = [
        Row(
            f"deferred {name}",
            "",
            "",
            "deferred",
            f"waiting {waited(now - entry.since)}, since "
            f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(entry.since))}; "
            f"{busy_detail(name, entry.pids)}",
        )
        for name, entry in sorted(waiting.items())
    ]
    alive = _alive(pid)
    for package in held:
        detail = (
            f"held by the running apply (pid {pid})"
            if alive
            else f"its apply (pid {pid}) ended before unholding it; the next apply unholds it"
        )
        rows.append(Row(f"hold {package}", "", "", "held" if alive else "stale", detail))
    return rows


# --------------------------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------------------------


def _alias(host: Host) -> str:
    try:
        return (host.nvm_dir / "alias" / "default").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def tool_row(host: Host, tool: Tool, pin: str) -> Row:
    """Return ``tool``'s row: its pin, the installed version and the status."""
    installed = tool.installed(host)
    if tool.assess is not None:
        status, detail = tool.assess(host, pin, installed)
        return Row(tool.key, pin, installed, status, detail)
    status = compare(pin, installed, self_updating=tool.self_updating)
    detail = ""
    if tool.key == "node" and status == "ok":
        alias = _alias(host)
        if numbers(alias) != numbers(pin):
            status = "drift"
            detail = f"nvm's default alias is {alias or 'unset'}, not {pin}"
    return Row(tool.key, pin, installed, status, detail)


def home_path(path: Path, home: Path) -> str:
    """Return ``path`` as a shell word, ``"$HOME"/...`` under ``home`` (no account in a report)."""
    try:
        relative = path.relative_to(home)
    except ValueError:
        return shlex.quote(str(path))
    return f'"$HOME"/{shlex.quote(relative.as_posix())}'


def fleet_path(host: Host, node: str) -> str:
    """Return the ``PATH`` a fleet shell runs with: nvm's default node's ``bin``, then the block.

    The PATH block (``fleet_setup.PATH_BLOCK_FILE``) is read in a fresh ``bash`` holding only
    ``HOME`` and :data:`BASE_PATH`, so the answer is the same whoever asks: an ssh session
    whose ``PATH`` predates a node switch, the timer's bare ``PATH``, an interactive shell.
    ``node`` is the default's version (``""``: none).

    Raises:
        UpdateError: the block could not be read.

    """
    block = shlex.quote(str(fleet_setup.PATH_BLOCK_FILE))
    ran = run(
        [
            "bash",
            "--noprofile",
            "--norc",
            "-c",
            f'. {block} && printf "%s" "$PATH"',
        ],
        timeout=PROBE_TIMEOUT,
        env={"HOME": str(host.box.home), "PATH": BASE_PATH},
        cwd=host.box.home,
    )
    if ran.code != 0:
        msg = f"cannot read the fleet PATH: {ran.last_line()}"
        raise UpdateError(msg)
    folders = [str(host.nvm_dir / "versions" / "node" / f"v{node}" / "bin")] if node else []
    folders += [folder for folder in ran.out.split(os.pathsep) if folder]
    return os.pathsep.join(dict.fromkeys(folders))


def by_hand(command: str) -> str:
    """Return the ``bash -c`` line a person runs for ``command`` under nvm's default node."""
    return "bash -c " + shlex.quote(f'NVM_DIR="$HOME/.nvm"; {fleet_setup.under_default(command)}')


def node_shadows(host: Host, installed: str, search: str) -> list[Row]:
    """Return a ``shadowed`` row for each nvm node on ``search`` other than the default.

    ``search`` is the fleet ``PATH`` (:func:`fleet_path`); ``installed`` the default's version
    (``""``: none, so nothing shadows it). A node nvm holds that ``search`` lacks is no shadow.
    """
    versions = host.nvm_dir / "versions" / "node"
    rows: list[Row] = []
    for folder in dict.fromkeys(filter(None, search.split(os.pathsep))):
        path = Path(folder)
        if not installed or path.name != "bin" or path.parent.parent != versions:
            continue
        version = path.parent.name
        if numbers(version) == numbers(installed):
            continue
        rows.append(
            Row(
                "node shadow",
                "",
                f"~/.nvm/versions/node/{version}",
                "shadowed",
                f"not the default v{installed}, yet on the fleet PATH; "
                f"remove: {by_hand(f'nvm uninstall {shlex.quote(version)}')}",
            ),
        )
    return rows


def removal_command(path: Path, home: Path) -> str:
    """Return the command that removes the stray ``codex`` at ``path`` (printed, never run).

    One an npm prefix of its own installed (a link into ``<prefix>/lib/node_modules``) is
    uninstalled with that prefix; anything else is a file to delete.
    """
    target = Path(os.path.realpath(path))
    parts = target.parts
    if "node_modules" in parts and parts[parts.index("node_modules") - 1] == "lib":
        prefix = Path(*parts[: parts.index("node_modules") - 1])
        return by_hand(f"npm uninstall -g --prefix {home_path(prefix, home)} @openai/codex")
    return f"rm {home_path(path, home)}"


def codex_shadows(host: Host, node: str, search: str) -> list[Row]:
    """Return a ``shadowed`` row for each ``codex`` on ``search`` other than nvm's default node's.

    ``search`` is the fleet ``PATH`` (:func:`fleet_path`). A copy reached twice (a folder
    listed twice, a link to it) is one row.
    """
    managed = host.nvm_dir / "versions" / "node" / f"v{node}" / "bin" / "codex" if node else None
    wanted = os.path.realpath(managed) if managed is not None else ""
    seen: set[str] = set()
    rows: list[Row] = []
    for folder in filter(None, search.split(os.pathsep)):
        candidate = Path(folder) / "codex"
        if not os.access(candidate, os.X_OK) or candidate.is_dir():
            continue
        real = os.path.realpath(candidate)
        if real == wanted or real in seen:
            continue
        seen.add(real)
        rows.append(
            Row(
                "codex shadow",
                "",
                home_path(candidate, host.box.home).replace('"$HOME"', "~"),
                "shadowed",
                f"not nvm's codex; remove: {removal_command(candidate, host.box.home)}",
            ),
        )
    return rows


def shadows(host: Host, node: str) -> list[Row]:
    """Return the ``shadowed`` rows on the fleet ``PATH`` (an ``error`` row when it is unread)."""
    try:
        search = fleet_path(host, node)
    except UpdateError as error:
        return [Row("shadows", "", "", "error", str(error))]
    return [*node_shadows(host, node, search), *codex_shadows(host, node, search)]


def _names(lines: Iterable[str], limit: int = 5) -> str:
    listed = list(lines)
    shown = ", ".join(listed[:limit])
    return f"{shown}, ..." if len(listed) > limit else shown


def _pending(item: str, ran: Ran, names: list[str]) -> Row:
    if ran.code != 0:
        return Row(item, "", "", "error", ran.last_line())
    count = len(names)
    return Row(item, "", str(count), "pending" if count else "ok", _names(names))


def brew(host: Host) -> str:
    """Return Homebrew's ``brew`` (``""`` when absent)."""
    found = shutil.which("brew", path=fleet_setup.box_env(host.box).get("PATH"))
    for path in (found, "/opt/homebrew/bin/brew", "/usr/local/bin/brew"):
        if path and Path(path).is_file():
            return path
    return ""


def _brew_env(host: Host) -> dict[str, str]:
    env = fleet_setup.box_env(host.box)
    env["HOMEBREW_NO_AUTO_UPDATE"] = "1"
    env["NONINTERACTIVE"] = "1"
    return env


def software_updates(host: Host) -> Row:
    """Return the ``macos`` row: the system updates ``softwareupdate -l`` lists (never installed)."""
    ran = run(
        ["/usr/sbin/softwareupdate", "-l"],
        timeout=OS_TIMEOUT,
        env=fleet_setup.box_env(host.box),
    )
    labels = [
        line.split(":", 1)[1].strip()
        for line in ran.out.splitlines()
        if line.strip().startswith("* Label:")
    ]
    return _pending("macos", ran, labels)


def os_rows(host: Host) -> list[Row]:
    """Return the OS updates pending: apt and snap on Linux, brew and the system on macOS."""
    if host.linux:
        env = fleet_setup.box_env(host.box)
        apt = run(["apt", "list", "--upgradable"], timeout=OS_TIMEOUT, env=env)
        names = [
            line.split("/", 1)[0]
            for line in apt.out.splitlines()
            if "/" in line and not line.startswith("Listing")
        ]
        rows = [_pending("apt", apt, names)]
        snap = run(["snap", "refresh", "--list"], timeout=OS_TIMEOUT, env=env)
        if snap.code == NOT_RUN:
            return rows
        listed = snap.out.splitlines()
        current = "All snaps up to date" in snap.out + snap.err
        rows.append(
            _pending(
                "snap",
                Ran(0, snap.out, snap.err) if current else snap,
                [] if current else [line.split()[0] for line in listed[1:] if line.strip()],
            ),
        )
        return rows
    found = brew(host)
    if not found:
        rows = [Row("brew", "", "", "ok", "no Homebrew")]
    else:
        outdated = run(
            [
                found,
                "outdated",
                "--greedy",
                "--quiet",
            ],
            timeout=OS_TIMEOUT,
            env=_brew_env(host),
        )
        rows = [
            _pending(
                "brew",
                outdated,
                [line.strip() for line in outdated.out.splitlines() if line.strip()],
            ),
        ]
    return [*rows, software_updates(host)]


def stray_rows(host: Host) -> list[Row]:
    """Return a ``stray`` row per path ``fleet_setup.strays`` names, else one ``strays`` ``ok``."""
    home = host.box.home
    found = fleet_setup.strays(home, host.box.repo, host.git, other_projects=host.other_projects)
    if not found:
        return [Row("strays", "", "none", "ok")]
    return [
        Row(f"stray {fleet_setup.home_relative(stray.path, home)}", "", "", "stray", stray.why)
        for stray in found
    ]


def check(host: Host, pinned: Mapping[str, str], listed: Sequence[App] = ()) -> list[Row]:
    """Return this machine's rows: the tools and reference sources, shadows, strays, OS updates.

    Then, on macOS, a row per ``listed`` app installed, and the deferred families and held
    packages the state records (:func:`state_rows`).
    """
    rows = [tool_row(host, tool, pinned[tool.key]) for tool in TOOLS]
    node = next(row.installed for row in rows if row.item == "node")
    found: dict[App, Installed] = {} if host.linux else app_bundles(host, listed)
    return [
        *rows,
        *shadows(host, node),
        *stray_rows(host),
        *os_rows(host),
        *(app_rows(host, found, applying=False) if found else []),
        *state_rows(host.root),
    ]


def drifted(row: Row) -> bool:
    """Return whether ``row`` is drift ``check`` exits 1 on (an app row never is: report only)."""
    return row.status in DRIFT and not row.item.startswith(APP_ITEM)


# --------------------------------------------------------------------------------------------
# apply
# --------------------------------------------------------------------------------------------


def stop_reason(root: Path) -> str:
    """Return why the fleet is stopped at ``root`` (``fleet_stop.FLAG``), else ``""``.

    A flag that cannot be read stops the run too.
    """
    flag = root / fleet_stop.FLAG
    try:
        text = flag.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""
    except OSError as error:
        return f"unreadable stop flag ({error})"
    try:
        parsed = _loads(text)
    except ValueError:
        parsed = None
    reason = parsed.get("reason") if fleet.is_json_object(parsed) else None
    return reason if isinstance(reason, str) and reason else text or "stopped (no reason given)"


@contextlib.contextmanager
def update_lock(root: Path) -> Generator[None, None, None]:
    """Hold ``.work/update.lock`` for the block.

    Raises:
        LockedError: another ``apply`` holds it, or the lock call failed.

    """
    folder = root / ".work"
    folder.mkdir(exist_ok=True)
    lock = folder / LOCK
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            taken = _locks.try_lock(descriptor)
        except OSError as error:
            msg = f"cannot lock {lock}: {error}"
            raise LockedError(msg) from error
        if not taken:
            msg = f"another fleet_update apply holds {lock}"
            raise LockedError(msg)
        yield
    finally:
        os.close(descriptor)


def apply_tool(
    host: Host,
    tool: Tool,
    pin: str,
    before: Row | None = None,
) -> Row:
    """Bring ``tool`` to ``pin``: install when its row (``before``, else read) says so, then read it back."""
    before = tool_row(host, tool, pin) if before is None else before
    if before.status not in ACTIONABLE:
        return before
    try:
        lines = tool.lines(host, pin, before.installed)
    except ValueError as error:
        return dataclasses.replace(before, status="error", detail=str(error))
    ran = host.bash(" && ".join(f"( {line} )" for line in lines), timeout=INSTALL_TIMEOUT)
    after = tool_row(host, tool, pin)
    if ran.code != 0:
        return dataclasses.replace(after, status="failed", detail=ran.last_line())
    if after.status not in {"ok", "ahead", "latest"}:
        detail = f"still {after.installed or 'absent'} after the install ({after.status})"
        return dataclasses.replace(after, status="failed", detail=detail)
    was = before.installed or "nothing"
    moved = f"from {was}" if was != after.installed else "unchanged"
    return dataclasses.replace(after, status="updated", detail=moved)


def tool_step(
    host: Host,
    tool: Tool,
    pin: str,
    ledger: Ledger,
    bundles: Mapping[str, Sequence[Path]],
) -> Row:
    """Bring ``tool`` to ``pin`` unless its family is running (a ``busy`` row, deferred)."""
    before = tool_row(host, tool, pin)
    if not tool.family or before.status not in ACTIONABLE:
        return apply_tool(host, tool, pin, before)
    try:
        running = busy(host, bundles).get(tool.family, ())
    except UpdateError as error:
        return dataclasses.replace(before, status="error", detail=f"{error}; not installed")
    if running:
        ledger.deferred[tool.family] = running
        return dataclasses.replace(before, status="busy", detail=busy_detail(tool.family, running))
    ledger.cleared.add(tool.family)
    return apply_tool(host, tool, pin, before)


def sudoers_hint() -> str:
    """Return what a ``refused`` row tells the maintainer to do."""
    return f"the sudoers rule is missing; print it with: python3 {SCRIPT} sudoers"


def _sudo(host: Host, argv: Sequence[str]) -> Ran:
    return run(["sudo", "-n", *argv], timeout=OS_TIMEOUT, env=fleet_setup.box_env(host.box))


def _refusal(ran: Ran) -> bool:
    """Return whether ``sudo`` itself refused (a ``sudo:`` line: no rule, a password wanted)."""
    return any(line.startswith("sudo:") for line in ran.err.splitlines())


def sudo_row(host: Host, argv: Sequence[str]) -> Row:
    """Run ``argv`` through ``sudo -n``: ``done``, ``refused`` (no rule) or ``failed``."""
    item = " ".join((Path(argv[0]).name, *argv[1:]))
    ran = _sudo(host, argv)
    if ran.code == 0:
        return Row(item, "", "", "done", ran.last_line() if ran.out.strip() else "")
    if _refusal(ran):
        return Row("sudo", "", "", "refused", sudoers_hint())
    return Row(item, "", "", "failed", ran.last_line())


def installed_packages(host: Host, packages: Iterable[str]) -> set[str]:
    """Return which of ``packages`` dpkg has installed (a read)."""
    wanted = list(dict.fromkeys(packages))
    if not wanted:
        return set()
    ran = run(
        [
            "dpkg-query",
            "-W",
            "-f",
            "${Package} ${db:Status-Abbrev}\\n",
            *wanted,
        ],
        timeout=PROBE_TIMEOUT,
        env=fleet_setup.box_env(host.box),
    )
    found = {
        words[0]
        for words in (line.split() for line in ran.out.splitlines())
        if len(words) >= 2 and words[1].startswith("ii")
    }
    return found & set(wanted)


def held_packages(host: Host) -> set[str]:
    """Return the packages held now (``apt-mark showhold``, a read)."""
    ran = run(["apt-mark", "showhold"], timeout=PROBE_TIMEOUT, env=fleet_setup.box_env(host.box))
    return {line.strip() for line in ran.out.splitlines() if line.strip()}


def unhold(host: Host, packages: Sequence[str]) -> list[Row]:
    """Unhold each of ``packages`` this updater held; return a row per one that stays held.

    The holds record (``.work/update-holds.json``) keeps exactly the ones still held.
    """
    rows: list[Row] = []
    kept: list[str] = []
    for package in packages:
        ran = _sudo(host, (APT_MARK, "unhold", package))
        if ran.code != 0:
            kept.append(package)
            rows.append(Row(f"apt-mark unhold {package}", "", "", "failed", ran.last_line()))
    _, recorded = read_holds(host.root)
    save_holds(host.root, [name for name in recorded if name not in packages or name in kept])
    return rows


def release_holds(host: Host) -> list[Row]:
    """Unhold what a run killed mid-upgrade left held (the holds record); one row saying so."""
    _, held = read_holds(host.root)
    if not held:
        return []
    failed = unhold(host, held)
    released = [name for name in held if not any(row.item.endswith(f" {name}") for row in failed)]
    rows = [
        Row(
            "holds",
            "",
            "",
            "released",
            f"unheld {', '.join(released)}, left held by a run that ended mid-upgrade",
        ),
    ]
    return [*(rows if released else []), *failed]


def apt_upgrade(host: Host, listed: Sequence[App], ledger: Ledger) -> list[Row]:
    """Run ``apt-get upgrade -y``, each installed listed app of a busy family held around it.

    A package held already (``apt-mark showhold``) is left as it is. Each hold is recorded
    before the upgrade and unheld in a ``finally``. A hold that fails makes the step one
    ``busy`` row and nothing is upgraded.
    """
    item = " ".join((Path(UPGRADE[0]).name, *UPGRADE[1:]))
    installed = installed_packages(host, (app.apt for app in listed if app.apt))
    present = [app for app in listed if app.apt in installed]
    try:
        running = busy(host, {}) if present else {}
    except UpdateError as error:
        return [Row(item, "", "", "error", f"{error}; nothing upgraded")]
    waiting = [app for app in present if app.family in running]
    for app in present:
        if app.family in running:
            ledger.deferred[app.family] = running[app.family]
        else:
            ledger.cleared.add(app.family)
    if not waiting:
        return [sudo_row(host, UPGRADE)]
    already = held_packages(host)
    held: list[str] = []
    rows: list[Row] = []
    try:
        for package in dict.fromkeys(app.apt for app in waiting if app.apt not in already):
            ran = _sudo(host, (APT_MARK, "hold", package))
            if ran.code != 0:
                families = "; ".join(
                    busy_detail(family, running[family])
                    for family in dict.fromkeys(app.family for app in waiting)
                )
                why = sudoers_hint() if _refusal(ran) else ran.last_line()
                return [
                    Row(
                        item,
                        "",
                        "",
                        "busy",
                        f"{families}: nothing upgraded, apt-mark hold {package} failed ({why})",
                    ),
                ]
            held.append(package)
            save_holds(host.root, [*read_holds(host.root)[1], package])
        for app in waiting:
            how = "left held (held outside fleet_update)" if app.apt in already else "held"
            detail = f"{busy_detail(app.family, running[app.family])}: {app.apt} {how} through the upgrade"
            rows.append(Row(f"{APP_ITEM}{app.name}", "", "", "busy", detail))
        rows.append(sudo_row(host, UPGRADE))
    finally:
        rows.extend(unhold(host, held))
    return rows


def linux_steps(
    host: Host,
    listed: Sequence[App] = (),
    ledger: Ledger | None = None,
    *,
    upgrade_only: bool = False,
) -> Iterable[Callable[[], list[Row]]]:
    """Yield the Linux OS steps: each of :data:`SUDO_COMMANDS` through ``sudo -n``.

    The upgrade holds the busy apps' packages (:func:`apt_upgrade`); ``upgrade_only`` yields
    it alone. The first ``sudo`` refusal ends the list with one ``refused`` row.
    """
    ledger = Ledger() if ledger is None else ledger
    refused: list[Row] = []
    for argv in (UPGRADE,) if upgrade_only else SUDO_COMMANDS:

        def step(argv: tuple[str, ...] = argv) -> list[Row]:
            rows = apt_upgrade(host, listed, ledger) if argv == UPGRADE else [sudo_row(host, argv)]
            refused.extend(row for row in rows if row.status == "refused")
            return rows

        if refused:
            return
        yield step


def macos_steps(host: Host, listed: Sequence[App] = ()) -> Iterable[Callable[[], list[Row]]]:
    """Yield the macOS OS steps: ``brew update``, ``brew upgrade --greedy``, the system list.

    The upgrade never touches a listed app's cask: when one is outdated, it names the other
    outdated formulae and casks instead.
    """
    found = brew(host)
    casks = {app.cask for app in listed if app.cask}

    def update() -> list[Row]:
        if not found:
            return [Row("brew update", "", "", "skipped", "no Homebrew")]
        ran = run([found, "update"], timeout=OS_TIMEOUT, env=_brew_env(host))
        status = "done" if ran.code == 0 else "failed"
        return [Row("brew update", "", "", status, ran.last_line() if ran.out or ran.err else "")]

    def upgrade() -> list[Row]:
        item = "brew upgrade --greedy"
        if not found:
            return [Row(item, "", "", "skipped", "no Homebrew")]
        names: list[str] = []
        kept: list[str] = []
        if casks:
            outdated = run(
                [
                    found,
                    "outdated",
                    "--greedy",
                    "--quiet",
                ],
                timeout=OS_TIMEOUT,
                env=_brew_env(host),
            )
            if outdated.code != 0:
                return [Row(item, "", "", "failed", f"brew outdated: {outdated.last_line()}")]
            names = [line.strip() for line in outdated.out.splitlines() if line.strip()]
            kept = [name for name in names if name.rsplit("/", 1)[-1] in casks]
        rest = [name for name in names if name not in kept]
        if kept and not rest:
            return [Row(item, "", "", "done", f"left alone: {', '.join(kept)} (listed apps)")]
        ran = run(
            [
                found,
                "upgrade",
                "--greedy",
                *(rest if kept else []),
            ],
            timeout=OS_TIMEOUT,
            env=_brew_env(host),
        )
        status = "done" if ran.code == 0 else "failed"
        detail = ran.last_line() if ran.out or ran.err else ""
        if kept:
            detail = f"{detail}; left alone: {', '.join(kept)} (listed apps)".lstrip("; ")
        return [Row(item, "", "", status, detail)]

    def system() -> list[Row]:
        row = software_updates(host)
        if row.status != "pending":
            return [row]
        detail = f"{row.detail}; never installed here (softwareupdate -i by hand)"
        return [dataclasses.replace(row, status="report", detail=detail)]

    yield update
    yield upgrade
    yield system


def apply(
    host: Host,
    pinned: Mapping[str, str],
    emit: Callable[[Row], None] | None = None,
    *,
    listed: Sequence[App] = (),
    deferred_only: bool = False,
) -> list[Row]:
    """Bring this machine to the pins, then update its OS packages; return one row per step.

    Holds ``.work/update.lock``; refuses while the fleet stop flag is set and ends at the
    first step that finds it set (a ``stopped`` row). A family found running defers its
    steps ("Busy"); the families deferred are recorded for ``deferred_only``, which runs
    only their steps and nothing when none waits. ``emit`` gets each row as it is made.
    """
    rows: list[Row] = []

    def add(row: Row) -> None:
        rows.append(row)
        if emit is not None:
            emit(row)

    reason = stop_reason(host.root)
    if reason:
        add(Row("apply", "", "", "stopped", f"the fleet is stopped: {reason}"))
        return rows
    try:
        before = read_deferred(host.root)
    except UpdateError as error:
        add(Row("deferred", "", "", "error", str(error)))
        return rows
    if deferred_only and not before:
        add(Row("deferred", "", "", "ok", "no family waits: nothing to retry"))
        return rows
    try:
        with update_lock(host.root):
            ledger = Ledger()
            found: dict[App, Installed] = {} if host.linux else app_bundles(host, listed)
            bundles = bundle_folders(found)
            steps = _steps(
                host,
                pinned,
                listed,
                ledger,
                bundles,
                set(before) if deferred_only else None,
            )
            finished = True
            # Lazily: a Linux step's ``sudo`` refusal ends the steps after it.
            for step in steps:
                reason = stop_reason(host.root)
                if reason:
                    add(Row("apply", "", "", "stopped", f"the fleet stopped mid-run: {reason}"))
                    finished = False
                    break
                for row in step():
                    add(row)
            if not deferred_only and found:
                for row in app_rows(host, found, applying=True):
                    add(row)
            save_deferred(host.root, ledger.settle(before, time.time(), finished=finished))
    except LockedError as error:
        add(Row("apply", "", "", "locked", str(error)))
    except UpdateError as error:
        add(Row("apply", "", "", "error", str(error)))
    return rows


def _steps(
    host: Host,
    pinned: Mapping[str, str],
    listed: Sequence[App],
    ledger: Ledger,
    bundles: Mapping[str, Sequence[Path]],
    only: set[str] | None,
) -> Iterable[Callable[[], list[Row]]]:
    """Yield ``apply``'s steps: every one, or (``only``) those of the families named."""
    if host.linux:
        yield lambda: release_holds(host)
    for tool in TOOLS:
        if only is None or tool.family in only:
            yield lambda tool=tool: [tool_step(host, tool, pinned[tool.key], ledger, bundles)]
    if only is None:
        yield lambda: [_shadows_after(host)]
        yield from linux_steps(host, listed, ledger) if host.linux else macos_steps(host, listed)
    elif host.linux and any(app.apt and app.family in only for app in listed):
        yield from linux_steps(host, listed, ledger, upgrade_only=True)


def _shadows_after(host: Host) -> Row:
    """Return one row summing up the shadows ``check`` names (``ok`` when none)."""
    found = shadows(host, _node_version(host))
    if not found:
        return Row("shadows", "", "", "ok")
    if found[0].status == "error":
        return found[0]
    return Row(
        "shadows",
        "",
        "",
        "shadowed",
        "; ".join(f"{row.installed}: {row.detail}" for row in found),
    )


# --------------------------------------------------------------------------------------------
# --all: every machine, one table
# --------------------------------------------------------------------------------------------


def remote_command(machine: fleet.Machine, action: str) -> str:
    """Return the shell line running ``action --json`` with ``machine``'s own checkout copy.

    Raises:
        UpdateError: the machine list's ``repo`` is no path a shell line can carry safely.

    """
    repo = machine.repo
    if not fleet_stop.SAFE_REPO.fullmatch(repo):
        msg = f"unsafe repo path {repo!r} for {machine.name} in the machine list"
        raise UpdateError(msg)
    where = f'"$HOME"/{repo[2:]}' if repo.startswith("~/") else repo
    return (
        f'cd {where} || exit 3; py=.venv/bin/python; [ -x "$py" ] || py=python3; '
        f'exec "$py" {SCRIPT} {action} --json'
    )


def parse_report(machine: str, ran: Ran) -> Report:
    """Return the report a machine's ``--json`` run printed, else one row saying why not."""
    if ran.code == fleet.SSH_FAILED:
        return Report(machine, (Row("ssh", "", "", "unreached", ran.last_line()),))
    try:
        document = _loads(ran.out)
        rows = document.get("rows") if fleet.is_json_object(document) else None
        parsed = tuple(Row.from_json(row) for row in rows) if fleet.is_json_array(rows) else ()
    except ValueError:
        parsed = ()
    if parsed:
        return Report(machine, parsed)
    detail = ran.last_line()
    if "fleet_update.py" in detail and "No such file" in detail:
        detail = f"its checkout has no {SCRIPT} yet (main not synced there)"
    return Report(machine, (Row("run", "", "", "error", detail),))


def reach(machine: fleet.Machine, action: str) -> Report:
    """Run ``action`` on ``machine`` over ssh; return its report."""
    try:
        command = remote_command(machine, action)
    except UpdateError as error:
        return Report(machine.name, (Row("run", "", "", "error", str(error)),))
    ran = run(fleet.ssh_argv(machine, command), timeout=REMOTE_TIMEOUT[action])
    return parse_report(machine.name, ran)


def local(action: str, name: str) -> Report:
    """Run ``action`` on this machine, in-process; return its report."""
    host = Host.here()
    try:
        pinned = pins()
        listed = apps()
    except UpdateError as error:
        return Report(name, (Row("pins", "", "", "error", str(error)),))
    rows = check(host, pinned, listed) if action == "check" else apply(host, pinned, listed=listed)
    return Report(name, tuple(rows))


def run_all(action: str, listed: Sequence[fleet.Machine] | None = None) -> list[Report]:
    """Run ``action`` on every machine of the list at once, this one in-process; list order."""
    machines = fleet.machines(ROOT) if listed is None else listed
    try:
        me = fleet.this_machine(machines).name
    except fleet.MachineListError:
        me = ""

    def one(machine: fleet.Machine) -> Report:
        return local(action, machine.name) if machine.name == me else reach(machine, action)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(machines))) as pool:
        return list(pool.map(one, machines))


def latest_drift(reports: Sequence[Report]) -> list[Report]:
    """Return ``reports`` with each ``latest`` tool older than the fleet's newest marked ``drift``."""
    newest: dict[str, str] = {}
    for report in reports:
        for row in report.rows:
            if row.status == "latest" and numbers(row.installed) > numbers(
                newest.get(row.item, ""),
            ):
                newest[row.item] = row.installed

    def mark(row: Row) -> Row:
        top = newest.get(row.item, "")
        if row.status != "latest" or numbers(row.installed) >= numbers(top):
            return row
        return dataclasses.replace(row, status="drift", detail=f"the fleet's newest is {top}")

    return [Report(report.machine, tuple(mark(row) for row in report.rows)) for report in reports]


# --------------------------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------------------------


def table(header: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    """Return ``rows`` under ``header`` as left-aligned columns."""
    widths = [max(len(line[index]) for line in (header, *rows)) for index in range(len(header))]
    return [
        "  ".join(cell.ljust(width) for cell, width in zip(line, widths, strict=True)).rstrip()
        for line in (header, *rows)
    ]


def machine_table(report: Report) -> list[str]:
    """Return one machine's rows as a table: item, pin, installed, status, detail."""
    header = (
        "item",
        "pinned",
        "installed",
        "status",
        "detail",
    )
    lines = table(
        header,
        [
            (
                row.item,
                row.pinned,
                row.installed,
                row.status,
                row.detail,
            )
            for row in report.rows
        ],
    )
    return [f"== {report.machine}", *lines]


def _cell(row: Row | None) -> str:
    if row is None:
        return "-"
    shown = row.installed or "-"
    return shown if row.status in {"ok", "latest"} else f"{shown} {row.status}"


def fleet_table(reports: Sequence[Report]) -> list[str]:
    """Return ``check --all``'s one table: an item per line, a machine per column, then notes."""
    items: list[str] = []
    pinned: dict[str, str] = {}
    for report in reports:
        for row in report.rows:
            if row.item not in items:
                items.append(row.item)
            if row.pinned:
                _ = pinned.setdefault(row.item, row.pinned)
    found = {(report.machine, row.item): row for report in reports for row in report.rows}
    body = [
        (
            item,
            pinned.get(item, ""),
            *(_cell(found.get((report.machine, item))) for report in reports),
        )
        for item in items
    ]
    lines = table(("item", "pinned", *(report.machine for report in reports)), body)
    notes = [
        f"{report.machine}: {row.item}: {row.installed + ': ' if row.status == 'shadowed' else ''}"
        f"{row.detail}"
        for report in reports
        for row in report.rows
        if row.detail
    ]
    return [*lines, *([""] if notes else []), *notes]


def apply_table(reports: Sequence[Report]) -> list[str]:
    """Return ``apply --all``'s one table: a machine and a step per line."""
    return table(
        (
            "machine",
            "step",
            "pinned",
            "installed",
            "status",
            "detail",
        ),
        [
            (
                report.machine,
                row.item,
                row.pinned,
                row.installed,
                row.status,
                row.detail,
            )
            for report in reports
            for row in report.rows
        ],
    )


def step_line(row: Row) -> str:
    """Return one ``apply`` step as the one line it prints."""
    version = f"{row.installed or '-'} (pin {row.pinned})" if row.pinned else row.installed
    return "  ".join(
        part
        for part in (
            f"{row.item:<14}",
            f"{row.status:<9}",
            version,
            row.detail,
        )
        if part
    ).rstrip()


# --------------------------------------------------------------------------------------------
# schedule
# --------------------------------------------------------------------------------------------

#: The launchd label (macOS) and systemd unit name (Linux) of the daily update timer.
SCHEDULE_LABEL = "com.django-strawberry-framework.fleet-update"
SCHEDULE_UNIT = "dsf-fleet-update"
#: The tools ``apply`` calls; their folders lead the timer's ``PATH``.
SCHEDULE_TOOLS = (
    "bash",
    "curl",
    "git",
    "sudo",
    "brew",
    "perl",
)
#: The log every scheduled run appends to, under the checkout's ``.work/`` (git-ignored).
SCHEDULE_LOG = "fleet-update.log"
#: The local time a day's run is due, before its jitter.
SCHEDULE_HOUR = 4
SCHEDULE_MINUTE = 30
#: The most seconds a run is put off at random, so the fleet never updates in lockstep.
SCHEDULE_JITTER = 1800
#: Seconds a scheduled run may take before it is killed.
SCHEDULE_TIME_LIMIT = 5400
#: The hourly retry of the deferred families (``apply --deferred``): its launchd label,
#: systemd unit and the minute past each hour it is due, before the same jitter.
RETRY_LABEL = f"{SCHEDULE_LABEL}-retry"
RETRY_UNIT = f"{SCHEDULE_UNIT}-retry"
RETRY_MINUTE = 0


def schedule_path() -> str:
    """Return the ``PATH`` a scheduled run gets: each tool's folder as found now, then the system's."""
    folders: list[str] = []
    found = [shutil.which(tool) for tool in SCHEDULE_TOOLS]
    system = [
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
    ]
    for folder in [*(str(Path(path).parent) for path in found if path), *system]:
        if folder not in folders:
            folders.append(folder)
    return os.pathsep.join(folders)


def schedule_line(root: Path = ROOT, jitter: int = 0, action: str = "apply") -> str:
    """Return the shell line a scheduled run executes (``fleet_sync.schedule_line``'s shape).

    It checks the stop flag before any Python starts, sleeps a random ``0..jitter`` seconds
    (launchd only: systemd's timer has ``RandomizedDelaySec``) and checks it again, then runs
    ``action`` (``apply``, or the retry's ``apply --deferred``) under ``perl``'s ``alarm`` so
    a run past :data:`SCHEDULE_TIME_LIMIT` seconds is killed.
    """
    python = shlex.quote(str(root / ".venv" / "bin" / "python"))
    command = f"{python} {SCRIPT} {action}"
    limit = f"perl -e 'alarm shift @ARGV; exec @ARGV or die' {SCHEDULE_TIME_LIMIT}"
    stop = f"[ -e {fleet_stop.FLAG} ] && exit 0; "
    pause = (
        "n=$(od -An -N2 -tu2 /dev/urandom 2>/dev/null | tr -dc 0-9); "
        f"sleep $(( ${{n:-0}} % {jitter + 1} )); {stop}"
        if jitter
        else ""
    )
    return (
        f"cd {shlex.quote(str(root))} || exit 1; {stop}{pause}"
        f"command -v perl >/dev/null 2>&1 && exec {limit} {command}; exec {command}"
    )


#: The two timers: label or unit, the ``apply`` they run, the launchd calendar entry and the
#: systemd ``OnCalendar`` value.
TIMERS = (
    (
        SCHEDULE_LABEL,
        SCHEDULE_UNIT,
        "apply",
        {"Hour": SCHEDULE_HOUR, "Minute": SCHEDULE_MINUTE},
        f"*-*-* {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}:00",
    ),
    (
        RETRY_LABEL,
        RETRY_UNIT,
        "apply --deferred",
        {"Minute": RETRY_MINUTE},
        f"*-*-* *:{RETRY_MINUTE:02d}:00",
    ),
)


def schedule_files(
    home: Path,
    root: Path = ROOT,
    platform_name: str = sys.platform,
) -> dict[Path, str]:
    """Return the timer files: ``apply`` daily, ``apply --deferred`` hourly (module docstring).

    Raises:
        UpdateError: ``platform_name`` is neither macOS nor Linux.

    """
    log = root / ".work" / SCHEDULE_LOG
    files: dict[Path, str] = {}
    if platform_name == "darwin":
        for label, _unit, action, calendar, _when in TIMERS:
            agent = {
                "Label": label,
                "ProgramArguments": [
                    "/bin/sh",
                    "-c",
                    schedule_line(root, SCHEDULE_JITTER, action),
                ],
                "WorkingDirectory": str(root),
                "StartCalendarInterval": calendar,
                "StandardOutPath": str(log),
                "StandardErrorPath": str(log),
                "EnvironmentVariables": {"PATH": schedule_path(), "HOME": str(home)},
            }
            plist = home / "Library" / "LaunchAgents" / f"{label}.plist"
            files[plist] = plistlib.dumps(agent).decode()
        return files
    if platform_name.startswith("linux"):
        units = home / ".config" / "systemd" / "user"
        for _label, unit, action, _calendar, when in TIMERS:
            command = (
                f"{{ {schedule_line(root, action=action)}; }} >> {shlex.quote(str(log))} 2>&1"
            )
            title = (
                "Update django-strawberry-framework's fleet tools to their pins"
                if action == "apply"
                else "Retry the fleet tool updates deferred while their agents ran"
            )
            files[units / f"{unit}.service"] = (
                f"[Unit]\nDescription={title}\n\n"
                f"[Service]\nType=oneshot\nWorkingDirectory={root}\n"
                f"Environment=PATH={schedule_path()}\nTimeoutStartSec={SCHEDULE_TIME_LIMIT}\n"
                f"ExecStart=/bin/sh -c {shlex.quote(command)}\n"
            )
            files[units / f"{unit}.timer"] = (
                f"[Unit]\nDescription={title}\n\n"
                f"[Timer]\nOnCalendar={when}\n"
                f"Persistent=true\nRandomizedDelaySec={SCHEDULE_JITTER}s\nAccuracySec=1s\n\n"
                "[Install]\nWantedBy=timers.target\n"
            )
        return files
    msg = f"schedule writes a launchd agent (macOS) or systemd user units (Linux), not {platform_name}"
    raise UpdateError(msg)


def schedule_commands(
    files: Mapping[Path, str],
    platform_name: str = sys.platform,
) -> list[list[str]]:
    """Return the commands that (re)load ``files``' timers."""
    if platform_name == "darwin":
        domain = f"gui/{os.getuid()}"
        commands: list[list[str]] = []
        for path in files:
            commands.append(
                [
                    "launchctl",
                    "bootout",
                    domain,
                    str(path),
                ],
            )
            commands.append(
                [
                    "launchctl",
                    "bootstrap",
                    domain,
                    str(path),
                ],
            )
        return commands
    return [
        ["systemctl", "--user", "daemon-reload"],
        [
            "systemctl",
            "--user",
            "enable",
            "--now",
            *(f"{unit}.timer" for _label, unit, _action, _calendar, _when in TIMERS),
        ],
    ]


def load_schedule(commands: Sequence[Sequence[str]]) -> None:
    """Run ``commands``; a ``launchctl bootout`` of an agent not loaded yet fails and is ignored.

    Raises:
        UpdateError: any other command failed.

    """
    for command in commands:
        ran = run(command, timeout=PROBE_TIMEOUT)
        if ran.code != 0 and command[1] != "bootout":
            msg = f"{shlex.join(command)} failed: {ran.last_line()}"
            raise UpdateError(msg)


# --------------------------------------------------------------------------------------------
# sudoers
# --------------------------------------------------------------------------------------------


def hold_commands(listed: Sequence[App]) -> list[tuple[str, ...]]:
    """Return the ``apt-mark`` commands ``apply`` runs as root: hold, unhold, per apt package."""
    return [
        (APT_MARK, verb, package)
        for package in dict.fromkeys(app.apt for app in listed if app.apt)
        for verb in ("hold", "unhold")
    ]


def sudoers_text(user: str, listed: Sequence[App] = (), template: Path = SUDOERS_FILE) -> str:
    """Return the sudoers drop-in with ``user`` rendered in, ``@APT_MARK@`` per hold command.

    A template line holding ``@APT_MARK@`` is repeated once per command of
    :func:`hold_commands`, each exact (absolute path, the package named, no wildcard).

    Raises:
        UpdateError: ``user`` is no plain account name, or a package is not plain.

    """
    if not ACCOUNT.fullmatch(user):
        msg = f"refusing to render the account {user!r} into a sudoers rule"
        raise UpdateError(msg)
    commands = [" ".join(argv) for argv in hold_commands(listed)]
    pattern = fleet_setup.APP_VALUES["apt"]
    odd = [app.apt for app in listed if app.apt and not pattern.fullmatch(app.apt)]
    if odd:
        msg = f"refusing to render the packages {odd!r} into a sudoers rule"
        raise UpdateError(msg)
    lines: list[str] = []
    for line in template.read_text(encoding="utf-8").replace("@USER@", user).splitlines():
        if "@APT_MARK@" in line:
            lines.extend(line.replace("@APT_MARK@", command) for command in commands)
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def sudoers_command(text: str) -> str:
    """Return the one command installing ``text`` as the drop-in, validated before it is live.

    The file is staged root-owned, mode 0440, under a dotted name (sudo's ``includedir`` skips
    a name with a dot), checked by ``visudo -cf``, then renamed into place; the stage is
    removed whatever happened, so a rule that fails the check never takes effect.
    """
    staged = f"{SUDOERS_DIR}/.{SUDOERS_NAME}.new"
    target = f"{SUDOERS_DIR}/{SUDOERS_NAME}"
    return (
        f"t=$(mktemp) && printf '%s' {shlex.quote(text)} > \"$t\" && "
        f'sudo install -o root -g root -m 0440 "$t" {staged} && '
        f"sudo visudo -cf {staged} && sudo mv {staged} {target}; "
        f's=$?; rm -f "$t"; sudo rm -f {staged}; [ "$s" -eq 0 ] && echo "installed {target}"'
    )


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


class _Args(argparse.Namespace):
    """The parsed command line, typed."""

    command: str
    all: bool
    json: bool
    install: bool
    deferred: bool


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").partition("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("check", "read-only: pinned versus installed, OS updates pending"),
        ("apply", "install the pins and the OS package updates"),
    ):
        sub = commands.add_parser(name, help=text)
        _ = sub.add_argument("--all", action="store_true", help="every machine, in parallel")
        _ = sub.add_argument("--json", action="store_true", help="one JSON document")
        if name == "apply":
            _ = sub.add_argument(
                "--deferred",
                action="store_true",
                help="only the families the last run deferred (the hourly retry)",
            )
    schedule = commands.add_parser(
        "schedule",
        help="print (or --install) the daily timer and the hourly retry",
    )
    _ = schedule.add_argument("--install", action="store_true", help="write the timer and load it")
    _ = commands.add_parser("sudoers", help="print the Linux sudoers rule and its install command")
    return parser


def _print_json(document: object) -> None:
    print(json.dumps(document, indent=2))


def cmd_check(args: _Args) -> int:
    """Report pinned versus installed here, or on every machine; exit 1 on drift."""
    if args.all:
        reports = latest_drift(run_all("check"))
        if args.json:
            _print_json({"machines": [report.as_json() for report in reports]})
        else:
            print("\n".join(fleet_table(reports)))
        rows = [row for report in reports for row in report.rows]
    else:
        report = Report(
            fleet.this_machine_name(repo=ROOT),
            tuple(check(Host.here(), pins(), apps())),
        )
        if args.json:
            _print_json(report.as_json())
        else:
            print("\n".join(machine_table(report)))
        rows = list(report.rows)
    return 1 if any(drifted(row) for row in rows) else 0


def cmd_apply(args: _Args) -> int:
    """Bring this machine (or every machine) to the pins; exit 1 when a step went wrong."""
    deferred = args.deferred
    if args.all and deferred:
        msg = "--deferred retries this machine's own deferred families (its timer); not with --all"
        raise UpdateError(msg)
    if args.all:
        reports = run_all("apply")
        if args.json:
            _print_json({"machines": [report.as_json() for report in reports]})
        else:
            print("\n".join(apply_table(reports)))
        rows = [row for report in reports for row in report.rows]
    else:
        pinned = pins()
        listed = apps()
        name = fleet.this_machine_name(repo=ROOT)
        stamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")

        def emit(row: Row) -> None:
            print(step_line(row), flush=True)

        if not args.json:
            what = "apply --deferred" if deferred else "apply"
            print(f"== fleet_update {what} on {name} at {stamp}", flush=True)
        rows = apply(
            Host.here(),
            pinned,
            None if args.json else emit,
            listed=listed,
            deferred_only=deferred,
        )
        if args.json:
            _print_json(Report(name, tuple(rows)).as_json())
    return 1 if any(row.status in TROUBLE for row in rows) else 0


def cmd_schedule(args: _Args) -> int:
    """Print (or with ``--install`` write and load) this machine's daily update timer."""
    files = schedule_files(Path.home())
    commands = schedule_commands(files)
    if not args.install:
        for path, text in files.items():
            print(f"# {path}\n{text}")
        print("# then:")
        for command in commands:
            print(shlex.join(command))
        return 0
    for path, text in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    load_schedule(commands)
    print(
        f"installed: apply daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}, apply --deferred "
        f"hourly at :{RETRY_MINUTE:02d} (each +0-{SCHEDULE_JITTER}s)",
    )
    return 0


def cmd_sudoers(_args: _Args) -> int:
    """Print the sudoers drop-in for this account and the command that installs it."""
    text = sudoers_text(getpass.getuser(), apps())
    print(f"# {SUDOERS_DIR}/{SUDOERS_NAME} (Linux; once per machine):")
    print(text, end="" if text.endswith("\n") else "\n")
    print("# install it (validated with visudo before it takes effect):")
    print(sudoers_command(text))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one command; exit 0 clean, 1 drift or a failed step, 2 bad setup."""
    args = build_parser().parse_args(argv, namespace=_Args())
    handlers: dict[str, Callable[[_Args], int]] = {
        "check": cmd_check,
        "apply": cmd_apply,
        "schedule": cmd_schedule,
        "sudoers": cmd_sudoers,
    }
    try:
        return handlers[args.command](args)
    except (UpdateError, fleet.MachineListError) as error:
        print(f"fleet_update: {error}", file=sys.stderr)
        return 2


def _cli() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    _cli()
