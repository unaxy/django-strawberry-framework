"""Stop (or resume) fleet syncing on every machine with one command, from any machine.

Usage, from ``~/projects/django-strawberry-framework`` on any fleet machine::

    python3 scripts/fleet_stop.py stop --reason "what went wrong"
    python3 scripts/fleet_stop.py resume
    python3 scripts/fleet_stop.py status

``stop`` writes the stop flag ``.work/fleet-stop`` in this checkout first, then in every
checkout ``docs/fleet/machines.json`` lists, over plain ``ssh`` (its ``ssh`` name and
``repo`` path), all at once. ``resume`` removes the flags the same way; ``status``
reports each machine's flag. Each machine is reported as ``stopped`` / ``resumed`` /
``clear``, or ``unreached`` with ssh's reason; exit 0 when every machine was reached,
1 otherwise (this machine is stopped either way).

While the flag is there:

- the save-sync timer (``scripts/fleet_sync.py schedule``) checks it in its own shell
  line before it starts any Python, so a broken ``fleet_sync.py`` cannot skip it;
- ``fleet_sync.py sync``, ``fetch-pins`` and ``handoff`` refuse, naming the reason;
- the machine's sync agent answers nothing but its probe, which carries the reason, so
  a peer's run treats it as unqualified, and a run that finds a stopped peer writes
  the flag on its own machine too (a machine that was offline at ``stop`` stops itself
  the first time it meets a stopped one).

Deliberately standalone: standard library only, Python 3.9 (the system ``python3``),
nothing imported from this repository, so it runs when the rest of the scripts are
broken. Without even this file, the same stop is one line per machine::

    ssh <machine> 'cd ~/projects/django-strawberry-framework && mkdir -p .work && touch .work/fleet-stop'

and the timer itself goes with ``launchctl bootout gui/$(id -u)
~/Library/LaunchAgents/com.django-strawberry-framework.fleet-pins.plist`` (macOS) or
``systemctl --user disable --now dsf-fleet-pins.timer`` (Linux).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import re
import shlex
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from typing_extensions import TypeIs

ROOT = Path(__file__).resolve().parent.parent
MACHINES_FILE = ROOT / "docs" / "fleet" / "machines.json"
#: The flag, relative to a checkout; ``scripts/fleet_sync.py`` reads the same path.
FLAG = ".work/fleet-stop"
#: ``scripts/fleet.py``'s ``SSH_OPTIONS``, repeated (this file imports nothing).
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
#: Seconds one machine's ssh call may take.
SSH_TIMEOUT = 30
#: Names this machine instead of its hostname (``scripts/fleet.py``'s ``MACHINE_ENV``).
MACHINE_ENV = "DSF_MACHINE_ID"
#: A ``repo`` path from the machine list that is safe to put in a remote shell line.
SAFE_REPO = re.compile(r"~?[A-Za-z0-9_./-]+")

#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads


def _is_object(value: object) -> TypeIs[dict[str, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeIs[list[object]]:
    return isinstance(value, list)


def machine_rows(path: Path = MACHINES_FILE) -> list[dict[str, str]]:
    """Return each machine's ``name``, ``ssh``, ``repo`` and ``aliases`` (comma-joined)."""
    document = _loads(path.read_text(encoding="utf-8"))
    entries = document.get("machines") if _is_object(document) else None
    rows: list[dict[str, str]] = []
    for entry in entries if _is_list(entries) else []:
        if not _is_object(entry):
            continue
        name, ssh, repo = entry.get("name"), entry.get("ssh"), entry.get("repo")
        aliases = entry.get("aliases")
        if isinstance(name, str) and isinstance(ssh, str) and isinstance(repo, str):
            names = (
                [alias for alias in aliases if isinstance(alias, str)] if _is_list(aliases) else []
            )
            rows.append(
                {
                    "name": name,
                    "ssh": ssh,
                    "repo": repo,
                    "aliases": ",".join(names),
                },
            )
    return rows


def is_here(row: dict[str, str], environ: dict[str, str] | None = None) -> bool:
    """Return whether ``row`` names this machine (``DSF_MACHINE_ID``, else the hostname)."""
    source = os.environ if environ is None else environ
    me = source.get(MACHINE_ENV) or socket.gethostname().split(".")[0]
    names = {row["name"], *filter(None, row["aliases"].split(","))}
    return me.casefold() in {name.casefold() for name in names}


def flag_text(reason: str, by: str) -> str:
    """Return the flag's content: who stopped the fleet, when and why, as one JSON line."""
    when = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return json.dumps({"reason": reason, "by": by, "at": when}) + "\n"


def remote_line(action: str, repo: str, text: str) -> str:
    """Return the shell line ``ssh`` runs on a machine to set, clear or read its flag."""
    if not SAFE_REPO.fullmatch(repo):
        msg = f"unsafe repo path {repo!r} in the machine list"
        raise ValueError(msg)
    where = "$HOME" + repo[1:] if repo.startswith("~") else repo
    go = f'cd "{where}" || exit 3'
    if action == "stop":
        return (
            f"{go} && mkdir -p .work && printf %s {shlex.quote(text)} > .work/.fleet-stop.tmp "
            f"&& mv .work/.fleet-stop.tmp {FLAG}"
        )
    if action == "resume":
        return f"{go} && rm -f {FLAG}"
    return f"{go} && if [ -e {FLAG} ]; then cat {FLAG}; else echo clear; fi"


def apply_here(action: str, text: str, root: Path = ROOT) -> str:
    """Set, clear or read this checkout's flag; return the row's result."""
    flag = root / FLAG
    if action == "stop":
        flag.parent.mkdir(parents=True, exist_ok=True)
        temporary = flag.with_name(".fleet-stop.tmp")
        _ = temporary.write_text(text, encoding="utf-8")
        _ = temporary.replace(flag)
        return "stopped"
    if action == "resume":
        flag.unlink(missing_ok=True)
        return "resumed"
    return flag.read_text(encoding="utf-8").strip() if flag.exists() else "clear"


def apply_remote(row: dict[str, str], action: str, text: str) -> str:
    """Set, clear or read ``row``'s flag over ssh; return the row's result."""
    command = [
        "ssh",
        *SSH_OPTIONS,
        row["ssh"],
        remote_line(action, row["repo"], text),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=SSH_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"unreached ({type(error).__name__}: {error})"
    if completed.returncode != 0:
        last = (completed.stderr or completed.stdout).strip().splitlines()
        return f"unreached (exit {completed.returncode}: {last[-1] if last else 'no output'})"
    if action == "status":
        return completed.stdout.strip() or "clear"
    return {"stop": "stopped", "resume": "resumed"}[action]


def run(
    action: str,
    reason: str,
    rows: Sequence[dict[str, str]],
    root: Path = ROOT,
) -> tuple[list[str], bool]:
    """Apply ``action`` here first, then on every other row at once; return lines and success."""
    here = [row for row in rows if is_here(row)]
    me = here[0]["name"] if here else socket.gethostname().split(".")[0]
    text = flag_text(reason, me)
    lines = [f"{me} (this machine): {apply_here(action, text, root)}"]
    others = [row for row in rows if not is_here(row)]

    def reach(row: dict[str, str]) -> tuple[str, str]:
        return row["name"], apply_remote(row, action, text)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(others))) as pool:
        results = list(pool.map(reach, others))
    lines += [f"{name}: {result}" for name, result in results]
    return lines, not any(result.startswith("unreached") for _name, result in results)


class _Args(argparse.Namespace):
    """The parsed command line, typed."""

    action: str
    reason: str


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``stop``, ``resume`` or ``status``; exit 0 when every machine was reached."""
    parser = argparse.ArgumentParser(description="Stop or resume fleet syncing everywhere.")
    _ = parser.add_argument("action", choices=["stop", "resume", "status"])
    _ = parser.add_argument("--reason", default="stopped by hand", help="why (stop only)")
    args = parser.parse_args(argv, namespace=_Args())
    action, reason = args.action, args.reason
    lines, reached = run(action, reason, machine_rows())
    for line in lines:
        print(line)
    if action == "stop":
        print("resume with: python3 scripts/fleet_stop.py resume")
    return 0 if reached else 1


if __name__ == "__main__":
    sys.exit(main())
