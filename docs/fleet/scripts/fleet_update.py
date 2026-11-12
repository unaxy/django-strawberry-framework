"""Bring every fleet machine to the pinned tool versions, and report what drifts.

Usage, from ``~/projects/django-strawberry-framework`` on any fleet machine::

    uv run python docs/fleet/scripts/fleet_update.py check [--all] [--json]
    uv run python docs/fleet/scripts/fleet_update.py apply [--all] [--json]
    uv run python docs/fleet/scripts/fleet_update.py schedule [--install]
    uv run python docs/fleet/scripts/fleet_update.py sudoers

Pins
    ``docs/fleet/scripts/setup/versions.json`` (``fleet_setup.VERSIONS_FILE``, read by
    ``fleet_setup.load_versions``) holds one line per tool: an exact release, or
    ``latest`` for a tool whose vendor installer takes no version (OpenCode, Muse, grok,
    Antigravity: ``fleet_setup.VENDOR_INSTALLERS``). Bumping a version is a one-line commit
    on main; the save-sync timers fast-forward every machine's main
    (``docs/fleet/scripts/fleet_sync.py`` "Periodic runs"), and each machine's next
    ``apply`` installs exactly that version. :data:`TOOLS` must name exactly the pinned
    tools, a vendor tool must read ``latest`` and every other tool an exact release; a file
    breaking that is refused (exit 2).

Tools
    :data:`TOOLS`, in the order ``apply`` brings them up: nvm, node, npm, Codex, Claude
    Code, uv, pre-commit, osv-scanner, then the four ``latest`` tools. nvm is sourced in a
    ``bash`` subprocess (``. "$NVM_DIR/nvm.sh" --no-use``), never in this process: node is
    nvm's ``default`` alias, npm and Codex are read and installed under that node (Codex as
    ``@openai/codex``, a global npm package: the one way every machine installs it). Each
    tool is installed by ``docs/fleet/scripts/fleet_setup.py``'s line builder for it, the
    same lines a new box runs; node's carries the previous default's global packages over
    (``--reinstall-packages-from``) and sets ``nvm alias default`` to the pin.

``check``
    Read-only. One row per tool: its pin, the version installed, and a status: ``ok``,
    ``missing``, ``behind``, ``differs`` (past the pin, for a tool nothing but ``apply``
    moves), ``ahead`` (past the pin, for a tool that updates itself: Claude Code, never
    downgraded), ``drift`` (node at the pin while nvm's ``default`` alias names something
    else) or ``latest`` (a ``latest`` tool's version, compared across machines by
    ``--all``). A ``shadowed`` row names a file that runs instead of the managed tool: a
    ``codex`` on ``PATH`` other than nvm's (an npm prefix of its own, a standalone binary),
    or a node under ``~/.nvm`` newer than the default (the PATH block,
    ``setup/files/path.sh``, puts the newest first); it is never deleted, and the row
    prints the command that removes it. Then the OS updates pending: ``apt`` (``apt list
    --upgradable``, from the lists the last ``apt-get update`` fetched) and ``snap``
    (``snap refresh --list``) on Linux, ``brew`` (``brew outdated --greedy``, casks
    included, with Homebrew's auto-update off) and ``macos`` (``softwareupdate -l``) on
    macOS. Exit 1 on drift (:data:`DRIFT`); pending OS updates alone are not drift.

``apply``
    Brings this machine to the pins, one line per step, then the OS packages: on Linux
    ``sudo -n`` runs exactly ``/usr/bin/apt-get update``, ``/usr/bin/apt-get upgrade -y``
    and ``/usr/bin/snap refresh`` (the three the sudoers rule allows, below); a ``sudo``
    refusal is one ``refused`` row naming the missing rule and nothing prompts. On macOS
    ``brew update`` and ``brew upgrade --greedy``; a macOS system update is never run,
    only listed (``softwareupdate -l``). A tool already at its pin, or ``ahead``, is left
    alone; a ``latest`` tool's installer runs every time. Each install is read back: a tool
    not at its pin afterwards is ``failed``. It holds ``.work/update.lock`` (a kernel lock:
    a second ``apply`` on the machine refuses), refuses while the fleet stop flag is set
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
    The daily timer, as ``fleet_sync.py schedule`` builds its own: a launchd agent on
    macOS (``StartCalendarInterval``, missed runs fire on wake), systemd user units on Linux
    (``OnCalendar`` with ``Persistent=true``), each running ``apply`` from the checkout's
    ``.venv`` Python daily at :data:`SCHEDULE_HOUR` and :data:`SCHEDULE_MINUTE` local time, put off
    a random 0 to :data:`SCHEDULE_JITTER` seconds, killed after
    :data:`SCHEDULE_TIME_LIMIT` seconds, appending to ``.work/fleet-update.log``, and
    skipped by a shell check of the stop flag before any Python starts. ``schedule`` alone
    prints the files and the commands; ``--install`` writes and loads them (the
    maintainer's step, once per machine; again after the timer file changes).

``sudoers``
    Prints the drop-in ``setup/files/sudoers-fleet-update`` with this account rendered in
    (the tracked file names no user), and one command that installs it as
    ``/etc/sudoers.d/dsf-fleet-update``: staged root-owned with mode 0440 under a dotted
    name sudo's ``includedir`` skips, validated with ``visudo -cf``, then moved into
    place; a stage that fails validation is removed. Run once per Linux machine.

Exit 0 clean, 1 drift (``check``) or a failed, refused or stopped step (``apply``), 2 a bad
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
import itertools
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

#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads

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
#: The sources ``nvm`` from ``$NVM_DIR`` without switching node (``fleet_setup.box_env`` sets it).
NVM = '. "$NVM_DIR/nvm.sh" --no-use'
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
    },
)
#: The statuses ``apply`` exits 1 on.
TROUBLE = frozenset(
    {
        "failed",
        "refused",
        "stopped",
        "busy",
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
#: The sudoers drop-in, ``@USER@`` rendered by ``sudoers``.
SUDOERS_FILE = Path(__file__).resolve().parent / "setup" / "files" / "sudoers-fleet-update"
SUDOERS_DIR = "/etc/sudoers.d"
SUDOERS_NAME = "dsf-fleet-update"
#: An account name safe to render into the drop-in and the shell command.
ACCOUNT = re.compile(r"[a-z_][a-z0-9_-]{0,31}")
VERSION = re.compile(r"\d+(?:\.\d+)+")


class UpdateError(Exception):
    """A refusal; the message says why and what to do (exit 2)."""


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

    @classmethod
    def here(cls) -> Host:
        """Return this machine."""
        return cls(fleet_setup.Box.here(), platform.machine(), ROOT)

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


def version_of(text: str) -> str:
    """Return the first dotted version in ``text`` (``v26.13.1`` reads ``26.13.1``), else ``""``."""
    found = VERSION.search(text)
    return found.group(0) if found else ""


def numbers(version: str) -> tuple[int, ...]:
    """Return ``version``'s numbers (``""`` and ``latest`` read as none)."""
    found = version_of(version)
    return tuple(int(part) for part in found.split(".")) if found else ()


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
    ran = host.bash(f"{NVM} && nvm --version")
    return version_of(ran.out) if ran.code == 0 else ""


def _node_version(host: Host) -> str:
    ran = host.bash(f"{NVM} && nvm version default")
    return version_of(ran.out) if ran.code == 0 else ""


def under_default(command: str) -> str:
    """Return a ``bash`` line running ``command`` with nvm's default node first on ``PATH``."""
    return f"{NVM} && nvm use --silent default >/dev/null && {command}"


def _npm_version(host: Host) -> str:
    ran = host.bash(under_default("npm --version"))
    return version_of(ran.out) if ran.code == 0 else ""


def _codex_version(host: Host) -> str:
    # ``npm ls`` exits 1 on any problem in the tree (an extraneous package) yet lists it.
    ran = host.bash(under_default("npm ls -g --depth=0 --json"))
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


TOOLS: tuple[Tool, ...] = (
    Tool(
        "nvm",
        _nvm_version,
        lambda _host, pin, _installed: fleet_setup.nvm_lines(pin, "/dev/null"),
    ),
    Tool("node", _node_version, _node_lines),
    Tool(
        "npm",
        _npm_version,
        lambda _host, pin, _installed: fleet_setup.npm_global_lines("npm", pin),
    ),
    Tool(
        "codex",
        _codex_version,
        lambda _host, pin, _installed: fleet_setup.npm_global_lines("@openai/codex", pin),
    ),
    Tool(
        "claude",
        _binary(".local", "bin", "claude"),
        lambda _host, pin, _installed: fleet_setup.claude_lines(pin),
        self_updating=True,
    ),
    Tool(
        "uv",
        _binary(".local", "bin", "uv"),
        lambda _host, pin, _installed: fleet_setup.uv_lines(pin, modify_path=False),
    ),
    Tool(
        "pre-commit",
        _binary(".local", "bin", "pre-commit"),
        lambda _host, pin, _installed: fleet_setup.pre_commit_lines(pin),
    ),
    Tool("osv-scanner", _binary(".local", "bin", "osv-scanner"), _osv_lines),
    Tool("opencode", _binary(".opencode", "bin", "opencode"), _vendor("opencode")),
    Tool("muse", _binary(".local", "bin", "muse"), _vendor("muse")),
    Tool("grok", _binary(".grok", "bin", "grok"), _vendor("grok")),
    Tool("agy", _binary(".local", "bin", "agy"), _vendor("agy")),
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


def _newest_node(host: Host) -> str:
    folder = host.nvm_dir / "versions" / "node"
    try:
        found = [entry.name for entry in folder.iterdir() if numbers(entry.name)]
    except OSError:
        return ""
    return max(found, key=numbers, default="")


def node_shadow(host: Host, installed: str) -> Row | None:
    """Return a ``shadowed`` row when a node newer than the default leads the PATH block."""
    newest = _newest_node(host)
    if not installed or not newest or numbers(newest) <= numbers(installed):
        return None
    command = "bash -c " + shlex.quote(f'. "$HOME/.nvm/nvm.sh" && nvm uninstall {newest}')
    return Row(
        "node shadow",
        "",
        f"~/.nvm/versions/node/{newest}",
        "shadowed",
        f"newer than the default v{installed}, so first on the PATH block; remove: {command}",
    )


def removal_command(path: Path, home: Path) -> str:
    """Return the command that removes the stray ``codex`` at ``path`` (printed, never run).

    One an npm prefix of its own installed (a link into ``<prefix>/lib/node_modules``) is
    uninstalled with that prefix; anything else is a file to delete.
    """
    target = Path(os.path.realpath(path))
    parts = target.parts
    if "node_modules" in parts and parts[parts.index("node_modules") - 1] == "lib":
        prefix = Path(*parts[: parts.index("node_modules") - 1])
        line = (
            f'. "$HOME/.nvm/nvm.sh" && npm uninstall -g --prefix {home_path(prefix, home)} '
            "@openai/codex"
        )
        return "bash -c " + shlex.quote(line)
    return f"rm {home_path(path, home)}"


def codex_shadows(host: Host, node: str, search: str | None = None) -> list[Row]:
    """Return a ``shadowed`` row for each ``codex`` on ``PATH`` other than nvm's default node's.

    ``search`` is the ``PATH`` searched (default this process's). A copy reached twice (a
    folder listed twice, a link to it) is one row.
    """
    managed = host.nvm_dir / "versions" / "node" / f"v{node}" / "bin" / "codex" if node else None
    wanted = os.path.realpath(managed) if managed is not None else ""
    seen: set[str] = set()
    rows: list[Row] = []
    path = os.environ.get("PATH", "") if search is None else search
    for folder in filter(None, path.split(os.pathsep)):
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


def check(host: Host, pinned: Mapping[str, str]) -> list[Row]:
    """Return this machine's rows: every tool against its pin, the shadows, the OS updates."""
    rows = [tool_row(host, tool, pinned[tool.key]) for tool in TOOLS]
    node = next(row.installed for row in rows if row.item == "node")
    shadow = node_shadow(host, node)
    rows += [*([shadow] if shadow else []), *codex_shadows(host, node)]
    return [*rows, *os_rows(host)]


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
        UpdateError: another ``apply`` holds it, or the lock call failed.

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
            raise UpdateError(msg) from error
        if not taken:
            msg = f"another fleet_update apply holds {lock}"
            raise UpdateError(msg)
        yield
    finally:
        os.close(descriptor)


def apply_tool(host: Host, tool: Tool, pin: str) -> Row:
    """Bring ``tool`` to ``pin``: install when its row says so, then read it back."""
    before = tool_row(host, tool, pin)
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


def sudoers_hint() -> str:
    """Return what a ``refused`` row tells the maintainer to do."""
    return f"the sudoers rule is missing; print it with: python3 {SCRIPT} sudoers"


def linux_steps(host: Host) -> Iterable[Callable[[], Row]]:
    """Yield the Linux OS steps: each of :data:`SUDO_COMMANDS` through ``sudo -n``.

    The first ``sudo`` refusal (a ``sudo:`` line on stderr: no rule, a password wanted)
    ends the list with one ``refused`` row.
    """
    refused: list[Row] = []
    for argv in SUDO_COMMANDS:
        item = " ".join((Path(argv[0]).name, *argv[1:]))

        def step(argv: tuple[str, ...] = argv, item: str = item) -> Row:
            ran = run(["sudo", "-n", *argv], timeout=OS_TIMEOUT, env=fleet_setup.box_env(host.box))
            if ran.code == 0:
                return Row(item, "", "", "done", ran.last_line() if ran.out.strip() else "")
            if any(line.startswith("sudo:") for line in ran.err.splitlines()):
                refused.append(Row("sudo", "", "", "refused", sudoers_hint()))
                return refused[-1]
            return Row(item, "", "", "failed", ran.last_line())

        if refused:
            return
        yield step


def macos_steps(host: Host) -> Iterable[Callable[[], Row]]:
    """Yield the macOS OS steps: ``brew update``, ``brew upgrade --greedy``, the system list."""
    found = brew(host)
    for words in (("update",), ("upgrade", "--greedy")):

        def step(words: tuple[str, ...] = words) -> Row:
            item = " ".join(("brew", *words))
            if not found:
                return Row(item, "", "", "skipped", "no Homebrew")
            ran = run([found, *words], timeout=OS_TIMEOUT, env=_brew_env(host))
            status = "done" if ran.code == 0 else "failed"
            return Row(item, "", "", status, ran.last_line() if ran.out or ran.err else "")

        yield step

    def system() -> Row:
        row = software_updates(host)
        if row.status != "pending":
            return row
        detail = f"{row.detail}; never installed here (softwareupdate -i by hand)"
        return dataclasses.replace(row, status="report", detail=detail)

    yield system


def apply(
    host: Host,
    pinned: Mapping[str, str],
    emit: Callable[[Row], None] | None = None,
) -> list[Row]:
    """Bring this machine to the pins, then update its OS packages; return one row per step.

    Holds ``.work/update.lock``; refuses while the fleet stop flag is set and ends at the
    first step that finds it set (a ``stopped`` row). ``emit`` gets each row as it is made.
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
        with update_lock(host.root):
            steps: list[Callable[[], Row]] = [
                (lambda tool=tool: apply_tool(host, tool, pinned[tool.key])) for tool in TOOLS
            ]
            steps.append(lambda: _shadows_after(host))
            os_steps = linux_steps(host) if host.linux else macos_steps(host)
            # Lazily: a Linux step's ``sudo`` refusal ends the steps after it.
            for step in itertools.chain(steps, os_steps):
                reason = stop_reason(host.root)
                if reason:
                    add(Row("apply", "", "", "stopped", f"the fleet stopped mid-run: {reason}"))
                    break
                add(step())
    except UpdateError as error:
        add(Row("apply", "", "", "busy", str(error)))
    return rows


def _shadows_after(host: Host) -> Row:
    """Return one row summing up the shadows ``check`` names (``ok`` when none)."""
    node = _node_version(host)
    found = [
        *([shadow] if (shadow := node_shadow(host, node)) else []),
        *codex_shadows(host, node),
    ]
    if not found:
        return Row("shadows", "", "", "ok")
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
    except UpdateError as error:
        return Report(name, (Row("pins", "", "", "error", str(error)),))
    rows = check(host, pinned) if action == "check" else apply(host, pinned)
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


def schedule_line(root: Path = ROOT, jitter: int = 0) -> str:
    """Return the shell line a scheduled run executes (``fleet_sync.schedule_line``'s shape).

    It checks the stop flag before any Python starts, sleeps a random ``0..jitter`` seconds
    (launchd only: systemd's timer has ``RandomizedDelaySec``) and checks it again, then runs
    ``apply`` under ``perl``'s ``alarm`` so a run past :data:`SCHEDULE_TIME_LIMIT` seconds is
    killed.
    """
    python = shlex.quote(str(root / ".venv" / "bin" / "python"))
    command = f"{python} {SCRIPT} apply"
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


def schedule_files(
    home: Path,
    root: Path = ROOT,
    platform_name: str = sys.platform,
) -> dict[Path, str]:
    """Return the timer files running ``apply`` daily (module docstring, ``schedule``).

    Raises:
        UpdateError: ``platform_name`` is neither macOS nor Linux.

    """
    log = root / ".work" / SCHEDULE_LOG
    if platform_name == "darwin":
        agent = {
            "Label": SCHEDULE_LABEL,
            "ProgramArguments": ["/bin/sh", "-c", schedule_line(root, SCHEDULE_JITTER)],
            "WorkingDirectory": str(root),
            "StartCalendarInterval": {"Hour": SCHEDULE_HOUR, "Minute": SCHEDULE_MINUTE},
            "StandardOutPath": str(log),
            "StandardErrorPath": str(log),
            "EnvironmentVariables": {"PATH": schedule_path(), "HOME": str(home)},
        }
        plist = home / "Library" / "LaunchAgents" / f"{SCHEDULE_LABEL}.plist"
        return {plist: plistlib.dumps(agent).decode()}
    if platform_name.startswith("linux"):
        command = f"{{ {schedule_line(root)}; }} >> {shlex.quote(str(log))} 2>&1"
        units = home / ".config" / "systemd" / "user"
        title = "Update django-strawberry-framework's fleet tools to their pins"
        service = (
            f"[Unit]\nDescription={title}\n\n"
            f"[Service]\nType=oneshot\nWorkingDirectory={root}\n"
            f"Environment=PATH={schedule_path()}\nTimeoutStartSec={SCHEDULE_TIME_LIMIT}\n"
            f"ExecStart=/bin/sh -c {shlex.quote(command)}\n"
        )
        timer = (
            f"[Unit]\nDescription={title}\n\n"
            f"[Timer]\nOnCalendar=*-*-* {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d}:00\n"
            f"Persistent=true\nRandomizedDelaySec={SCHEDULE_JITTER}s\nAccuracySec=1s\n\n"
            "[Install]\nWantedBy=timers.target\n"
        )
        return {
            units / f"{SCHEDULE_UNIT}.service": service,
            units / f"{SCHEDULE_UNIT}.timer": timer,
        }
    msg = f"schedule writes a launchd agent (macOS) or systemd user units (Linux), not {platform_name}"
    raise UpdateError(msg)


def schedule_commands(
    files: Mapping[Path, str],
    platform_name: str = sys.platform,
) -> list[list[str]]:
    """Return the commands that (re)load ``files``' timer."""
    if platform_name == "darwin":
        domain = f"gui/{os.getuid()}"
        plist = str(next(iter(files)))
        return [
            [
                "launchctl",
                "bootout",
                domain,
                plist,
            ],
            [
                "launchctl",
                "bootstrap",
                domain,
                plist,
            ],
        ]
    return [
        ["systemctl", "--user", "daemon-reload"],
        [
            "systemctl",
            "--user",
            "enable",
            "--now",
            f"{SCHEDULE_UNIT}.timer",
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


def sudoers_text(user: str, template: Path = SUDOERS_FILE) -> str:
    """Return the sudoers drop-in with ``user`` rendered in.

    Raises:
        UpdateError: ``user`` is no plain account name.

    """
    if not ACCOUNT.fullmatch(user):
        msg = f"refusing to render the account {user!r} into a sudoers rule"
        raise UpdateError(msg)
    return template.read_text(encoding="utf-8").replace("@USER@", user)


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
    schedule = commands.add_parser("schedule", help="print (or --install) the daily timer")
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
        report = Report(fleet.this_machine_name(repo=ROOT), tuple(check(Host.here(), pins())))
        if args.json:
            _print_json(report.as_json())
        else:
            print("\n".join(machine_table(report)))
        rows = list(report.rows)
    return 1 if any(row.status in DRIFT for row in rows) else 0


def cmd_apply(args: _Args) -> int:
    """Bring this machine (or every machine) to the pins; exit 1 when a step went wrong."""
    if args.all:
        reports = run_all("apply")
        if args.json:
            _print_json({"machines": [report.as_json() for report in reports]})
        else:
            print("\n".join(apply_table(reports)))
        rows = [row for report in reports for row in report.rows]
    else:
        pinned = pins()
        name = fleet.this_machine_name(repo=ROOT)
        stamp = time.strftime("%Y-%m-%d %H:%M:%S %Z")

        def emit(row: Row) -> None:
            print(step_line(row), flush=True)

        if not args.json:
            print(f"== fleet_update apply on {name} at {stamp}", flush=True)
        rows = apply(Host.here(), pinned, None if args.json else emit)
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
        f"installed: apply daily at {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} (+0-{SCHEDULE_JITTER}s)",
    )
    return 0


def cmd_sudoers(_args: _Args) -> int:
    """Print the sudoers drop-in for this account and the command that installs it."""
    text = sudoers_text(getpass.getuser())
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
