"""Set up a new Ubuntu machine as a fleet member, from one command on a machine already in it.

Usage, from ``~/projects/django-strawberry-framework`` on any fleet machine::

    python3 scripts/fleet_setup.py add <host>          # install everything on <host>
    python3 scripts/fleet_setup.py add <host> --check  # read-only: what <host> still lacks
    python3 scripts/fleet_setup.py mesh [--check]      # ssh both ways between every pair
    python3 scripts/fleet_setup.py row <host>          # a machines.json row to paste
    python3 scripts/fleet_setup.py verify <host>       # fleet_sync / fleet_stop status

and on the new machine itself (``add`` copies this file there and runs it)::

    python3 fleet_setup.py box check
    python3 fleet_setup.py box install [--only STEP,...] [--skip KIND,...]

``docs/fleet/SETUP.md`` is the procedure around it: what to do before (Tailscale, an
ssh alias, this machine's key on the box), what this script does, and what stays by hand
(the agent CLI logins, the save-sync timer).

Steps
    ``box`` runs the ordered list :data:`STEPS`. Each step has a read-only check (done, or
    what is missing) and the shell lines that make it done; ``install`` runs only the
    steps whose check fails, in order, and stops at the first that fails, so a rerun
    picks up where the last one stopped and a finished box reruns as a no-op. A step is
    one of four kinds:

    ``sudo``
        Needs root (apt packages, user lingering). Every missing ``sudo`` step runs in
        one ``sudo sh -c`` before the rest, so a run asks for the password once; ``add``
        gives the ssh session a terminal for it.
    ``keys``
        Writes ssh material (the box's own key). Part of a normal run; an agent testing
        the script passes ``--skip keys``.
    ``user``
        Everything else, in the user's home and the checkout: uv, the CPython builds,
        node through nvm, the agent CLIs, pre-commit, the clone, its ``.venv``, its
        hook, direnv.
    ``hand``
        Never run: the check reports and the step prints what the maintainer does
        (logging in to Claude Code and Codex, installing the save-sync timer).

``mesh``
    Every ordered pair of machines in ``docs/fleet/machines.json`` (``--add HOST`` adds one
    the list does not hold yet) must reach the other as ``ssh -o BatchMode=yes <name>
    true``, since ``scripts/fleet_sync.py`` and ``scripts/fleet_stop.py`` call plain ssh
    both ways. For each failing pair ``a -> b`` it makes, in order: ``a``'s own key
    (``ssh-keygen`` when missing), a ``Host <b>`` block in ``a``'s ``~/.ssh/config`` with
    ``User <account>`` when ``ssh -G <b>`` on ``a`` names another account (the account is
    the one ``ssh -G <b>`` names here; the host name is left to Tailscale's MagicDNS),
    ``a``'s public key in ``b``'s ``authorized_keys``, and ``b``'s host key in ``a``'s
    ``known_hosts`` (``StrictHostKeyChecking=accept-new``: first use over the tailnet is
    trusted). This machine is reached directly, every other machine over one ssh from
    here; a machine this one cannot reach is reported and skipped. ``--check`` prints the
    matrix and changes nothing.

``row``
    Reads the box's cores and memory and prints a ``machines.json`` row: each weight is
    the box's share of a 6-core machine with 16 GiB (light) or 32 GiB (heavy), capped at 1
    and floored at 0.1; floors are the fleet's Linux ones, lowered for a box under 16 GiB.
    The list records no account names, so the row has none.

``verify``
    Runs ``scripts/fleet_sync.py status`` here and on the box, and
    ``scripts/fleet_stop.py status`` here: read-only, nothing synced.

Standard library only, Python 3.9 (macOS's system ``python3``; Ubuntu ships a newer one),
so it runs on a box that has nothing else yet. Ubuntu is the only ``box`` OS so far.
"""

from __future__ import annotations

import argparse
import dataclasses
import getpass
import json
import os
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from typing_extensions import TypeIs

ROOT = Path(__file__).resolve().parent.parent
MACHINES_FILE = ROOT / "docs" / "fleet" / "machines.json"
#: Where every fleet machine keeps the checkout (``scripts/fleet_sync.py`` requires it).
REPO = "~/projects/django-strawberry-framework"
#: The public repository a box clones from; pushes stay the maintainer's.
REPO_URL = "https://github.com/unaxy/django-strawberry-framework.git"
#: The CPython builds every machine carries; the last is ``python3`` (MACHINES.md section 2).
PYTHONS = (
    "3.10",
    "3.11",
    "3.12",
    "3.13",
    "3.14",
)
#: The nvm release whose installer a box runs.
NVM_VERSION = "v0.40.3"
#: Apt packages a fresh Ubuntu Desktop lacks, keyed by the command each provides.
APT_PACKAGES = {
    "git": "git",
    "rsync": "rsync",
    "curl": "curl",
    "direnv": "direnv",
    "tmux": "tmux",
    "rg": "ripgrep",
}
#: Where ``add`` puts this file on the box before the checkout exists.
REMOTE_COPY = "~/.cache/dsf-fleet-setup/fleet_setup.py"
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
#: The save-sync timer ``scripts/fleet_sync.py schedule --install`` loads on Linux.
TIMER_UNIT = "dsf-fleet-pins.timer"
KINDS = (
    "sudo",
    "keys",
    "user",
    "hand",
)
DIRENV_HOOK = 'eval "$(direnv hook bash)"'
#: The probe ``row`` runs on a box: cores, then total memory in KiB.
FACTS = "nproc; awk '/MemTotal/ {print $2}' /proc/meminfo"


@dataclasses.dataclass(frozen=True)
class Box:
    """The machine ``box`` runs on: its home, account and the checkout path."""

    home: Path
    user: str
    repo: Path
    repo_url: str = REPO_URL
    python_version: str = PYTHONS[-1]

    @classmethod
    def here(cls, repo_url: str = REPO_URL, python_version: str = PYTHONS[-1]) -> Box:
        """Return this machine's box."""
        home = Path.home()
        return cls(
            home=home,
            user=getpass.getuser(),
            repo=home / REPO[2:],
            repo_url=repo_url,
            python_version=python_version,
        )

    @property
    def bin(self) -> Path:
        """Return ``~/.local/bin``, where uv, its Pythons, Claude Code and pre-commit go."""
        return self.home / ".local" / "bin"


@dataclasses.dataclass(frozen=True)
class Step:
    """One setup step: a read-only check and the shell lines that make it pass."""

    key: str
    kind: str
    title: str
    #: ``None`` when done, else what is missing.
    check: Callable[[Box], str | None]
    #: The ``bash -c`` lines that make it done (a ``hand`` step's are printed, never run).
    lines: Callable[[Box], list[str]]


def box_env(box: Box) -> dict[str, str]:
    """Return the environment steps run in: ``~/.local/bin`` first, nvm's folder set."""
    env = dict(os.environ)
    env["PATH"] = f"{box.bin}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
    env["NVM_DIR"] = str(box.home / ".nvm")
    return env


def run_quiet(argv: Sequence[str], box: Box, cwd: Path | None = None) -> tuple[int, str]:
    """Run ``argv`` with the box's ``PATH``; return its exit code and stripped stdout."""
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
            env=box_env(box),
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return completed.returncode, completed.stdout.strip()


def nvm(command: str) -> str:
    """Return a shell line running ``command`` with nvm's default node on ``PATH``."""
    return f'. "$NVM_DIR/nvm.sh" && {command}'


def missing(names: Iterable[str]) -> str | None:
    """Return the comma-joined ``names`` (``None`` when there are none)."""
    listed = list(names)
    return ", ".join(listed) if listed else None


def _check_packages(_box: Box) -> str | None:
    return missing(pkg for command, pkg in APT_PACKAGES.items() if shutil.which(command) is None)


def _lines_packages(_box: Box) -> list[str]:
    packages = " ".join(APT_PACKAGES.values())
    return ["apt-get update", f"DEBIAN_FRONTEND=noninteractive apt-get install -y {packages}"]


def _check_linger(box: Box) -> str | None:
    code, out = run_quiet(
        [
            "loginctl",
            "show-user",
            box.user,
            "-p",
            "Linger",
        ],
        box,
    )
    return None if code == 0 and out == "Linger=yes" else "user lingering off"


def _lines_linger(box: Box) -> list[str]:
    return [f"loginctl enable-linger {shlex.quote(box.user)}"]


def _check_uv(box: Box) -> str | None:
    return None if (box.bin / "uv").exists() else "uv"


def _lines_uv(_box: Box) -> list[str]:
    return ["curl -LsSf https://astral.sh/uv/install.sh | sh"]


def _check_pythons(box: Box) -> str | None:
    uv = str(box.bin / "uv")
    absent = [
        v
        for v in PYTHONS
        if run_quiet(
            [
                uv,
                "python",
                "find",
                "--managed-python",
                v,
            ],
            box,
        )[0]
    ]
    if not (box.bin / "python3").exists():
        absent.append(f"python3 -> {PYTHONS[-1]}")
    return missing(absent)


def _lines_pythons(_box: Box) -> list[str]:
    # ``--default`` takes one version, so the default goes in a call of its own.
    return [
        f"uv python install {' '.join(PYTHONS[:-1])}",
        f"uv python install {PYTHONS[-1]} --default --preview-features python-install-default",
    ]


def _check_direnv_hook(box: Box) -> str | None:
    bashrc = box.home / ".bashrc"
    text = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
    return None if DIRENV_HOOK in text else "direnv hook in ~/.bashrc"


def _lines_direnv_hook(_box: Box) -> list[str]:
    return [f"printf '\\n%s\\n' {shlex.quote(DIRENV_HOOK)} >> ~/.bashrc"]


def _check_node(box: Box) -> str | None:
    code, _ = run_quiet(["bash", "-c", nvm("nvm which default")], box)
    return None if code == 0 else "nvm with a default node"


def _lines_node(_box: Box) -> list[str]:
    url = f"https://raw.githubusercontent.com/nvm-sh/nvm/{NVM_VERSION}/install.sh"
    return [
        f"curl -fsSL {url} | PROFILE=~/.bashrc bash",
        nvm("nvm install --lts && nvm alias default 'lts/*'"),
    ]


def _check_codex(box: Box) -> str | None:
    code, _ = run_quiet(["bash", "-c", nvm("command -v codex")], box)
    return None if code == 0 else "codex"


def _lines_codex(_box: Box) -> list[str]:
    return [nvm("npm install -g @openai/codex")]


def _check_claude(box: Box) -> str | None:
    return None if (box.bin / "claude").exists() else "claude"


def _lines_claude(_box: Box) -> list[str]:
    return ["curl -fsSL https://claude.ai/install.sh | bash"]


def _check_pre_commit(box: Box) -> str | None:
    return None if (box.bin / "pre-commit").exists() else "pre-commit"


def _lines_pre_commit(_box: Box) -> list[str]:
    return ["uv tool install pre-commit"]


def _check_ssh_key(box: Box) -> str | None:
    return None if (box.home / ".ssh" / "id_ed25519.pub").exists() else "~/.ssh/id_ed25519"


def _lines_ssh_key(_box: Box) -> list[str]:
    # No passphrase: fleet ssh runs in batch mode, where no prompt can be answered.
    return ['ssh-keygen -q -t ed25519 -N "" -C "$USER@$(hostname)" -f ~/.ssh/id_ed25519']


def _check_checkout(box: Box) -> str | None:
    return None if (box.repo / ".git").is_dir() else f"checkout at {REPO}"


def _lines_checkout(box: Box) -> list[str]:
    return [
        "mkdir -p ~/projects",
        f"git clone {shlex.quote(box.repo_url)} {shlex.quote(str(box.repo))}",
    ]


def _check_python_version(box: Box) -> str | None:
    return None if (box.repo / ".python-version").exists() else ".python-version"


def _lines_python_version(box: Box) -> list[str]:
    target = shlex.quote(str(box.repo / ".python-version"))
    return [f"printf '%s\\n' {shlex.quote(box.python_version)} > {target}"]


def _check_venv(box: Box) -> str | None:
    return None if (box.repo / ".venv" / "bin" / "python").exists() else "checkout .venv"


def _lines_venv(box: Box) -> list[str]:
    return [f"cd {shlex.quote(str(box.repo))} && uv sync --frozen"]


def _check_hook(box: Box) -> str | None:
    hook = box.repo / ".git" / "hooks" / "pre-commit"
    return None if hook.exists() else "pre-commit hook in the checkout"


def _lines_hook(box: Box) -> list[str]:
    return [f"cd {shlex.quote(str(box.repo))} && pre-commit install"]


def _check_direnv_allow(box: Box) -> str | None:
    code, _ = run_quiet(
        [
            "direnv",
            "exec",
            str(box.repo),
            "true",
        ],
        box,
        cwd=box.home,
    )
    return None if code == 0 else "direnv allow in the checkout"


def _lines_direnv_allow(box: Box) -> list[str]:
    return [f"direnv allow {shlex.quote(str(box.repo))}"]


def _check_logins(box: Box) -> str | None:
    # Existence only: a credential file is never opened.
    files = {
        "Claude Code": box.home / ".claude" / ".credentials.json",
        "Codex": box.home / ".codex" / "auth.json",
    }
    return missing(name for name, path in files.items() if not path.exists())


def _lines_logins(_box: Box) -> list[str]:
    return ["claude    # log in once, then /exit", "codex login"]


def _check_timer(box: Box) -> str | None:
    code, _ = run_quiet(
        [
            "systemctl",
            "--user",
            "is-enabled",
            TIMER_UNIT,
        ],
        box,
    )
    return None if code == 0 else TIMER_UNIT


def _lines_timer(box: Box) -> list[str]:
    repo = shlex.quote(str(box.repo))
    return [f"cd {repo} && uv run python scripts/fleet_sync.py schedule --install"]


STEPS: tuple[Step, ...] = (
    Step("packages", "sudo", "apt packages", _check_packages, _lines_packages),
    Step("linger", "sudo", "user lingering", _check_linger, _lines_linger),
    Step("uv", "user", "uv in ~/.local/bin", _check_uv, _lines_uv),
    Step("pythons", "user", "CPython builds via uv", _check_pythons, _lines_pythons),
    Step("direnv-hook", "user", "direnv in bash", _check_direnv_hook, _lines_direnv_hook),
    Step("node", "user", "node LTS via nvm", _check_node, _lines_node),
    Step("codex", "user", "Codex CLI", _check_codex, _lines_codex),
    Step("claude", "user", "Claude Code CLI", _check_claude, _lines_claude),
    Step("pre-commit", "user", "pre-commit uv tool", _check_pre_commit, _lines_pre_commit),
    Step("ssh-key", "keys", "this box's ssh key", _check_ssh_key, _lines_ssh_key),
    Step("checkout", "user", "the checkout", _check_checkout, _lines_checkout),
    Step(
        "python-version",
        "user",
        ".python-version",
        _check_python_version,
        _lines_python_version,
    ),
    Step("venv", "user", "uv sync --frozen", _check_venv, _lines_venv),
    Step("hook", "user", "pre-commit install", _check_hook, _lines_hook),
    Step("direnv-allow", "user", "direnv allow", _check_direnv_allow, _lines_direnv_allow),
    Step("logins", "hand", "agent CLI logins", _check_logins, _lines_logins),
    Step("timer", "hand", "save-sync timer", _check_timer, _lines_timer),
)


def select(only: Sequence[str], skip: Sequence[str]) -> list[Step]:
    """Return the steps ``only`` names (every step when empty), less the kinds ``skip`` names."""
    keys = {step.key for step in STEPS}
    unknown = [key for key in only if key not in keys]
    unknown += [kind for kind in skip if kind not in KINDS]
    if unknown:
        msg = f"unknown step or kind: {', '.join(unknown)}"
        raise ValueError(msg)
    return [step for step in STEPS if (not only or step.key in only) and step.kind not in skip]


def check(box: Box, steps: Sequence[Step]) -> list[tuple[Step, str | None]]:
    """Return each step with what it is missing (``None`` when done)."""
    return [(step, step.check(box)) for step in steps]


def report(results: Sequence[tuple[Step, str | None]]) -> list[str]:
    """Return one line per step: ``ok`` or ``missing``, its kind, key and what is missing."""
    width = max((len(step.key) for step, _ in results), default=0)
    lines: list[str] = []
    for step, gap in results:
        state = "ok     " if gap is None else "missing"
        tail = "" if gap is None else f"  {gap}"
        lines.append(f"{state} {step.kind:<4} {step.key:<{width}}{tail}".rstrip())
    return lines


def run_lines(lines: Sequence[str], box: Box, *, sudo: bool = False) -> int:
    """Run ``lines`` as one ``bash -c`` (``sudo sh -c`` for root); return its exit code."""
    script = " && ".join(f"( {line} )" for line in lines)
    argv = (
        [
            "sudo",
            "sh",
            "-c",
            script,
        ]
        if sudo
        else ["bash", "-c", script]
    )
    print(f"+ {script}", flush=True)
    try:
        return subprocess.run(argv, check=False, cwd=box.home, env=box_env(box)).returncode
    except OSError as error:
        print(f"fleet_setup: {error}", file=sys.stderr)
        return 127


def install(box: Box, steps: Sequence[Step]) -> int:
    """Run every step whose check fails, ``sudo`` ones first in one call; stop at a failure."""
    gaps = check(box, steps)
    root = [step for step, gap in gaps if gap is not None and step.kind == "sudo"]
    if root:
        print(f"== sudo: {', '.join(step.key for step in root)}", flush=True)
        if run_lines([line for step in root for line in step.lines(box)], box, sudo=True):
            return 1
    for step, gap in gaps:
        if gap is None or step.kind == "sudo":
            continue
        if step.kind == "hand":
            print(f"== {step.key}: by hand ({gap}):")
            print("\n".join(f"   {line}" for line in step.lines(box)))
            continue
        print(f"== {step.key}: {step.title}", flush=True)
        if run_lines(step.lines(box), box) or step.check(box) is not None:
            print(f"fleet_setup: step {step.key} failed; rerun after fixing it", file=sys.stderr)
            return 1
    left = [step.key for step, gap in check(box, steps) if gap is not None]
    print("done" if not left else f"done except: {', '.join(left)}")
    return 0


# The fleet side: run in a checkout on a machine already in the fleet.


#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads


def _is_object(value: object) -> TypeIs[dict[str, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeIs[list[object]]:
    return isinstance(value, list)


def machine_names(path: Path = MACHINES_FILE) -> list[str]:
    """Return the ``name`` of every row in the machine list."""
    document = _loads(path.read_text(encoding="utf-8"))
    rows = document.get("machines") if _is_object(document) else None
    names: list[str] = []
    for entry in rows if _is_list(rows) else []:
        name = entry.get("name") if _is_object(entry) else None
        if isinstance(name, str):
            names.append(name)
    return names


def this_name(names: Sequence[str]) -> str:
    """Return this machine's fleet name (``DSF_MACHINE_ID``, else its local hostname)."""
    raw = os.environ.get("DSF_MACHINE_ID", "")
    if not raw and sys.platform == "darwin":
        completed = subprocess.run(
            ["scutil", "--get", "LocalHostName"],
            capture_output=True,
            text=True,
            check=False,
        )
        raw = completed.stdout.strip()
    raw = raw or socket.gethostname().split(".")[0]
    return next((name for name in names if name.casefold() == raw.casefold()), raw)


def on(
    host: str | None,
    command: str,
    *,
    tty: bool = False,
    stdin: str | None = None,
) -> tuple[int, str]:
    """Run ``command`` here (``host`` ``None``) or on ``host`` over ssh; return code and output."""
    if host is None:
        argv = ["bash", "-c", command]
    else:
        argv = [
            "ssh",
            *(("-t",) if tty else SSH_OPTIONS),
            host,
            command,
        ]
    if tty:
        return subprocess.run(argv, check=False).returncode, ""
    try:
        completed = subprocess.run(
            argv,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return 255, str(error)
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def reachable(host: str) -> bool:
    """Return whether ``ssh -o BatchMode=yes <host> true`` works from here."""
    return on(host, "true")[0] == 0


def box_command(action: str, extra: Sequence[str] = ()) -> str:
    """Return the shell line running this file's ``box`` command from :data:`REMOTE_COPY`."""
    words = " ".join(shlex.quote(word) for word in extra)
    return f"python3 {REMOTE_COPY} box {action} {words}".rstrip()


def push_self(host: str) -> int:
    """Copy this file to :data:`REMOTE_COPY` on ``host``; return ssh's exit code."""
    folder = REMOTE_COPY.rsplit("/", 1)[0]
    line = f"mkdir -p {folder} && cat > {REMOTE_COPY}"
    return on(host, line, stdin=Path(__file__).read_text(encoding="utf-8"))[0]


def https_url(url: str) -> str:
    """Return a GitHub ``git@`` remote as its https URL (a box clones without a key)."""
    prefix = "git@github.com:"
    return "https://github.com/" + url[len(prefix) :] if url.startswith(prefix) else url


def origin_url() -> str:
    """Return this checkout's ``origin`` as an https URL, else :data:`REPO_URL`."""
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "remote",
            "get-url",
            "origin",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return https_url(completed.stdout.strip()) or REPO_URL


def local_python_version() -> str:
    """Return this checkout's ``.python-version``, else the newest of :data:`PYTHONS`."""
    pinned = ROOT / ".python-version"
    return pinned.read_text(encoding="utf-8").strip() if pinned.exists() else PYTHONS[-1]


def add(host: str, *, dry: bool, skip: Sequence[str]) -> int:
    """Copy this file to ``host`` and run ``box check`` (``dry``) or ``box install`` there."""
    if not reachable(host):
        print(
            f"fleet_setup: ssh -o BatchMode=yes {host} true fails from here; "
            f"see docs/fleet/SETUP.md 'Before the script' (ssh-copy-id {host})",
            file=sys.stderr,
        )
        return 2
    code, release = on(host, ". /etc/os-release 2>/dev/null && echo $ID")
    if code or release != "ubuntu":
        print(f"fleet_setup: {host} is not Ubuntu ({release or 'unknown'})", file=sys.stderr)
        return 2
    if push_self(host):
        print(f"fleet_setup: could not copy this script to {host}", file=sys.stderr)
        return 2
    options = [
        "--repo-url",
        origin_url(),
        "--python-version",
        local_python_version(),
    ]
    options += [f"--skip={','.join(skip)}"] if skip else []
    if dry:
        code, out = on(host, box_command("check", options))
        print(out)
        return code
    return on(host, box_command("install", options), tty=True)[0]


def account(host: str) -> str:
    """Return the account ``ssh -G <host>`` logs in as from here ('' when it names none)."""
    code, out = on(None, f"ssh -G {shlex.quote(host)}")
    users = [line[5:] for line in out.splitlines() if line.startswith("user ")]
    return users[0] if code == 0 and users else ""


def mesh(names: Sequence[str], *, dry: bool) -> int:
    """Make every ordered pair of ``names`` reach the other over batch-mode ssh."""
    me = this_name(names)
    where = {name: (None if name == me else name) for name in names}
    up = [name for name in names if name == me or reachable(name)]
    for name in names:
        if name not in up:
            print(f"skipped {name}: unreached from {me}")
    accounts = {name: getpass.getuser() if name == me else account(name) for name in up}
    failed = 0
    for a in up:
        for b in up:
            if a == b:
                continue
            probe = f"ssh {' '.join(SSH_OPTIONS)} {shlex.quote(b)} true"
            if on(where[a], probe)[0] == 0:
                print(f"ok      {a} -> {b}")
            elif dry:
                print(f"missing {a} -> {b}")
                failed += 1
            elif link(where[a], b, where[b], accounts[b]) and on(where[a], probe)[0] == 0:
                print(f"fixed   {a} -> {b}")
            else:
                print(f"failed  {a} -> {b}")
                failed += 1
    return 1 if failed else 0


def link(
    a: str | None,
    b_name: str,
    b: str | None,
    b_account: str,
) -> bool:
    """Give ``a`` a key, a ``Host b`` block, its key in ``b``'s list and ``b``'s host key."""
    keygen = 'test -f ~/.ssh/id_ed25519.pub || ssh-keygen -q -t ed25519 -N "" -f ~/.ssh/id_ed25519'
    if on(a, keygen)[0]:
        return False
    code, key = on(a, "cat ~/.ssh/id_ed25519.pub")
    if code or not key.startswith("ssh-"):
        return False
    quoted = shlex.quote(b_name)
    code, resolved = on(a, f"ssh -G {quoted} | sed -n 's/^user //p'")
    if code == 0 and b_account and resolved != b_account:
        block = shlex.quote(f"Host {b_name}\n  User {b_account}\n")
        line = (
            f"mkdir -p ~/.ssh && printf '%s' {block} >> ~/.ssh/config && chmod 600 ~/.ssh/config"
        )
        if on(a, line)[0]:
            return False
    k = shlex.quote(key)
    grant = (
        "mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && "
        f"(grep -qxF {k} ~/.ssh/authorized_keys || printf '%s\\n' {k} >> ~/.ssh/authorized_keys)"
    )
    if on(b, grant)[0]:
        return False
    accept = f"ssh -o StrictHostKeyChecking=accept-new -o BatchMode=yes {quoted} true"
    return on(a, accept)[0] == 0


def suggest_row(name: str, cores: int, mem_kib: int) -> dict[str, object]:
    """Return a ``machines.json`` row for a Linux box with ``cores`` and ``mem_kib``."""
    gib = mem_kib / 1024 / 1024

    def share(memory_scale: float) -> float:
        return round(max(0.1, min(1.0, cores / 6, gib / memory_scale)), 1)

    small = gib < 16
    return {
        "name": name,
        "ssh": name,
        "os": "linux",
        "repo": REPO,
        "weight": {"light": share(16), "heavy": share(32)},
        "floors": {
            "light": {
                "min_mem_available_gib": 2 if small else 4,
                "min_disk_free_gib": 6,
                "max_psi_memory_full_avg10": 5,
            },
            "heavy": {
                "min_mem_available_gib": 3 if small else 8,
                "min_disk_free_gib": 12,
                "max_psi_memory_full_avg10": 5,
            },
        },
        "aliases": [],
    }


def row(host: str) -> int:
    """Print a ``machines.json`` row for ``host`` from its measured cores and memory."""
    code, out = on(host, FACTS)
    values = out.split()
    if code or len(values) != 2 or not all(value.isdigit() for value in values):
        print(f"fleet_setup: could not read {host}'s cores and memory: {out}", file=sys.stderr)
        return 2
    print(json.dumps(suggest_row(host, int(values[0]), int(values[1])), indent=2))
    return 0


def verify(host: str) -> int:
    """Run ``fleet_sync.py status`` here and on ``host``, and ``fleet_stop.py status`` here."""
    here = shlex.quote(str(ROOT))
    checks = [
        ("here", None, f"cd {here} && uv run python scripts/fleet_sync.py status"),
        (host, host, f"cd {REPO} && .venv/bin/python scripts/fleet_sync.py status"),
        ("here", None, f"cd {here} && python3 scripts/fleet_stop.py status"),
    ]
    worst = 0
    for label, where, command in checks:
        print(f"== {label}: {command}", flush=True)
        code, out = on(where, command)
        print(out)
        worst = max(worst, code)
    return worst


def _csv(text: str) -> list[str]:
    return [part for part in text.split(",") if part]


class _Args(argparse.Namespace):
    """The parsed command line, typed."""

    command: str
    action: str
    host: str
    check: bool
    only: str
    skip: str
    add: list[str]
    repo_url: str
    python_version: str


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command; exit 0 on success, 1 on a missing step or pair, 2 on bad setup."""
    parser = argparse.ArgumentParser(description="Set up a new fleet machine.")
    sub = parser.add_subparsers(dest="command", required=True)
    box_parser = sub.add_parser("box", help="run on the new machine itself")
    _ = box_parser.add_argument("action", choices=["check", "install"])
    _ = box_parser.add_argument("--only", default="", help="comma-separated step keys")
    _ = box_parser.add_argument("--skip", default="", help="comma-separated kinds")
    _ = box_parser.add_argument("--repo-url", default=REPO_URL)
    _ = box_parser.add_argument("--python-version", default=PYTHONS[-1])
    add_parser = sub.add_parser("add", help="set up <host> from this fleet machine")
    _ = add_parser.add_argument("host")
    _ = add_parser.add_argument("--check", action="store_true", help="report only")
    _ = add_parser.add_argument("--skip", default="", help="comma-separated kinds")
    mesh_parser = sub.add_parser("mesh", help="ssh both ways between every pair")
    _ = mesh_parser.add_argument("--check", action="store_true", help="report only")
    _ = mesh_parser.add_argument("--add", action="append", default=[], help="an unlisted host")
    for name in ("row", "verify"):
        _ = sub.add_parser(name).add_argument("host")
    args = parser.parse_args(argv, namespace=_Args())
    if args.command == "box":
        try:
            steps = select(_csv(args.only), _csv(args.skip))
        except ValueError as error:
            parser.error(str(error))
        box = Box.here(args.repo_url, args.python_version)
        if args.action == "check":
            results = check(box, steps)
            print("\n".join(report(results)))
            return 0 if all(gap is None for _, gap in results) else 1
        return install(box, steps)
    if args.command == "add":
        return add(args.host, dry=args.check, skip=_csv(args.skip))
    if args.command == "mesh":
        names = machine_names()
        return mesh([*names, *(host for host in args.add if host not in names)], dry=args.check)
    return row(args.host) if args.command == "row" else verify(args.host)


if __name__ == "__main__":
    sys.exit(main())
