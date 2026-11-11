"""Personalize an Ubuntu fleet machine the way ``rio-ubu`` is set up: CLI tools and dotfiles only.

The core setup (``docs/fleet/scripts/fleet_setup.py add <host>``) makes a machine a fleet member;
this script is the optional layer on top: the extra command-line tools, the shell, tmux and git
preferences, the load-aware house tools and the agent rules file. It installs no GUI application
and writes no desktop setting.

Usage, from ``~/projects/django-strawberry-framework`` on any fleet machine::

    python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host> --check  # what <host> lacks
    python3 docs/fleet/scripts/setup/ubuntu/personal.py apply <host>          # install it

and on the machine itself (``apply`` copies this folder there and runs it)::

    python3 personal.py box check
    python3 personal.py box install [--only STEP,...] [--skip KIND,...] [--git-name N --git-email E]

``apply`` copies this folder (``personal.py`` and ``files/``) to
``~/.cache/dsf-fleet-setup/setup/ubuntu/`` on the target, then runs ``box`` there over ``ssh``
(``-t`` for ``install``, so ``sudo`` can ask once). It passes the git ``user.name`` and
``user.email`` of the machine it runs on, so no identity is stored in this public repository.

Steps
    Ordered like ``fleet_setup.py``'s: each has a read-only check and the shell lines that make it
    pass; ``install`` runs the ``sudo`` steps first in one ``sudo sh -c``, then every other failing
    step in order, and stops at the first that still fails, so a rerun resumes. Kinds: ``sudo``
    (root), ``user`` (the home folder), ``hand`` (reported, never run: the logins).

    ``apt-cli``
        ``build-essential unzip zip jq fd-find btop gnupg stress-ng lm-sensors``.
    ``gh``
        GitHub's CLI from GitHub's own apt repository (keyring in ``/etc/apt/keyrings``).
    ``tailscale-operator``
        ``tailscale set --operator=<user>``: manage Tailscale without ``sudo``.
    ``path-block``
        A marked block at the top of ``~/.bashrc``, above Ubuntu's interactive-only guard, putting
        ``~/.local/bin``, ``~/.opencode/bin``, ``~/.grok/bin`` and the newest nvm node on ``PATH`` for
        non-interactive ``ssh`` commands too. Silent, so ssh pipes, rsync and git stay clean.
    ``interactive-block``
        A marked block at the end of ``~/.bashrc``: interactive ssh logins attach to tmux session
        ``main``; interactive ssh or tmux shells print the shared-box banner and ``pressure --short``.
    ``tmux-conf``
        ``~/.tmux.conf`` (mouse, 100k history, 256 colours, windows from 1). A different file there
        is kept as ``~/.tmux.conf.bak-<seconds>`` first.
    ``gitconfig``
        ``init.defaultBranch main``, plus ``user.name`` / ``user.email`` when given.
    ``house-tools``
        ``heavy`` (a slot-limited, low-priority job gate), ``pressure`` (a PSI/load/RAM verdict),
        ``agent-status`` and ``git-autosync`` in ``~/.local/bin``. ``heavy`` and ``pressure`` are
        rendered for this machine (:func:`limits`): slots = threads / 4 (at least 1), the RAM floor =
        RAM / 10 GiB (at least 2), YELLOW under twice that, load YELLOW above 3/4 of the threads and
        RED above 3/2. ``git-autosync`` takes a repository's ``.work/land.lock`` (without waiting)
        across its fast-forward, so it never moves a checkout while ``work.py land`` or
        ``fleet_sync.py`` writes it.
    ``autosync-timer``
        ``git-autosync`` every 3 minutes as a systemd user timer (lingering, which the core setup
        turns on, keeps it running logged out).
    ``opencode``, ``muse``, ``grok``, ``agy``, ``osv-scanner``
        Each vendor's own installer (``osv-scanner``: its release binary, :data:`OSV_VERSION`).
    ``rules``
        ``~/MACHINE.md``, ``~/AGENTS_READ_THIS_FIRST.md``, ``~/projects/AGENTS.md`` and
        ``~/projects/AGENTS_READ_THIS_FIRST.md``: one agent rules file rendered from
        ``files/MACHINE.md.in`` with this machine's measured facts.
    ``logins``
        By hand: ``gh auth login``, ``opencode``, ``muse``, ``grok`` and ``agy`` each sign in once.

Left out on purpose: GUI applications, GNOME settings and rootless Docker.

Standard library only, Python 3.9, so it runs from the system ``python3`` with nothing else.
"""

from __future__ import annotations

import argparse
import dataclasses
import io
import os
import re
import shlex
import socket
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

HERE = Path(__file__).resolve().parent
FILES = HERE / "files"
#: Where ``apply`` puts this folder on the target (the path below it mirrors this repository's).
REMOTE_ROOT = "~/.cache/dsf-fleet-setup"
REMOTE_DIR = f"{REMOTE_ROOT}/setup/ubuntu"
APT_PACKAGES = (
    "build-essential",
    "unzip",
    "zip",
    "jq",
    "fd-find",
    "btop",
    "gnupg",
    "stress-ng",
    "lm-sensors",
)
OSV_VERSION = "v2.7.0"
KINDS = ("sudo", "user", "hand")
#: How much of each shell script ``install`` echoes (rendered files make long lines).
ECHO_LIMIT = 400
PATH_MARK = "dsf-fleet path"
INTERACTIVE_MARK = "dsf-fleet interactive"
PLACEHOLDER = re.compile(r"@[A-Z_]+@")
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


@dataclasses.dataclass(frozen=True)
class Box:
    """The machine ``box`` runs on, with what this script reads from it."""

    home: Path
    user: str
    facts: dict[str, str]
    git_name: str = ""
    git_email: str = ""

    @property
    def bin(self) -> Path:
        """Return ``~/.local/bin``."""
        return self.home / ".local" / "bin"


@dataclasses.dataclass(frozen=True)
class Step:
    """One step: a read-only check (``None`` when done) and the shell lines that make it pass."""

    key: str
    kind: str
    check: Callable[[Box], str | None]
    lines: Callable[[Box], list[str]]


def _read(argv: Sequence[str], *, any_exit: bool = False) -> str:
    """Return ``argv``'s stripped stdout ('' when it fails; ``any_exit`` keeps a non-zero's)."""
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return completed.stdout.strip() if any_exit or completed.returncode == 0 else ""


def measure() -> dict[str, str]:
    """Return this machine's facts: host, OS, CPU, threads, RAM and home disk size."""
    meminfo = Path("/proc/meminfo")
    kib = 0
    if meminfo.exists():
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                kib = int(line.split()[1])
    cpu = ""
    for line in _read(["lscpu"]).splitlines():
        if line.startswith("Model name:"):
            cpu = line.split(":", 1)[1].strip()
    release = Path("/etc/os-release")
    pretty = ""
    if release.exists():
        for line in release.read_text(encoding="utf-8").splitlines():
            if line.startswith("PRETTY_NAME="):
                pretty = line.split("=", 1)[1].strip('"')
    disk = _read(
        [
            "df",
            "-h",
            "--output=size",
            str(Path.home()),
        ],
    ).splitlines()
    return {
        "HOST": socket.gethostname().split(".")[0],
        "OS": pretty or "Linux",
        "CPU": cpu or "unknown CPU",
        "THREADS": str(os.cpu_count() or 1),
        "RAM_GIB": str(kib // (1024 * 1024)),
        "DISK": disk[-1].strip() if disk else "unknown",
    }


def limits(threads: int, ram_gib: int) -> dict[str, str]:
    """Return ``heavy``/``pressure``'s limits (rio-ubu's 12 threads, 45 GiB: 3, 4, 8, 9, 18)."""
    floor = max(2, ram_gib // 10)
    return {
        "SLOTS": str(max(1, threads // 4)),
        "MIN_FREE_GIB": str(floor),
        "YELLOW_FREE_GIB": str(floor * 2),
        "LOAD_YELLOW": str(max(1, threads * 3 // 4)),
        "LOAD_RED": str(max(2, threads * 3 // 2)),
    }


def values(box: Box) -> dict[str, str]:
    """Return every template placeholder's value for ``box``."""
    return {**box.facts, **limits(int(box.facts["THREADS"]), int(box.facts["RAM_GIB"]))}


def render(template: str, mapping: dict[str, str]) -> str:
    """Fill ``@NAME@`` placeholders; refuse one ``mapping`` lacks."""
    text = template
    for name, value in mapping.items():
        text = text.replace(f"@{name}@", value)
    left = sorted(set(PLACEHOLDER.findall(text)))
    if left:
        msg = f"unfilled placeholders: {', '.join(left)}"
        raise ValueError(msg)
    return text


def block(mark: str, body: str) -> str:
    """Return ``body`` between the ``# >>> mark >>>`` and ``# <<< mark <<<`` lines."""
    return f"# >>> {mark} >>>\n{body.rstrip()}\n# <<< {mark} <<<\n"


def with_block(
    text: str,
    mark: str,
    body: str,
    *,
    top: bool,
) -> str:
    """Return ``text`` holding exactly one ``mark`` block with ``body``, at the top or the end."""
    wanted = block(mark, body)
    pattern = re.compile(
        rf"# >>> {re.escape(mark)} >>>\n.*?# <<< {re.escape(mark)} <<<\n",
        re.DOTALL,
    )
    if top:  # above the interactive guard: always first, wherever an older copy sits
        rest = pattern.sub("", text).lstrip("\n")
        return wanted + "\n" + rest
    if pattern.search(text):
        return pattern.sub(lambda _match: wanted, text, count=1)
    return text + ("" if not text or text.endswith("\n") else "\n") + "\n" + wanted


# Desired file contents, shared by each step's check and its lines.


def house_tools(box: Box) -> dict[str, str]:
    """Return each house tool's name and its rendered content."""
    mapping = values(box)
    tools: dict[str, str] = {}
    for source in sorted((FILES / "bin").iterdir()):
        name = source.name.removesuffix(".in")
        tools[name] = render(source.read_text(encoding="utf-8"), mapping)
    return tools


def rules_targets(box: Box) -> list[Path]:
    """Return every path the agent rules file is written to."""
    projects = box.home / "projects"
    return [
        box.home / "MACHINE.md",
        box.home / "AGENTS_READ_THIS_FIRST.md",
        projects / "AGENTS.md",
        projects / "AGENTS_READ_THIS_FIRST.md",
    ]


def rules_text(box: Box) -> str:
    """Return the agent rules file rendered for ``box``."""
    return render((FILES / "MACHINE.md.in").read_text(encoding="utf-8"), values(box))


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_line(path: Path, content: str, mode: str = "644") -> str:
    """Return a shell line writing ``content`` to ``path`` atomically with ``mode``."""
    target = shlex.quote(str(path))
    temporary = shlex.quote(f"{path}.dsf-tmp")
    return (
        f"mkdir -p {shlex.quote(str(path.parent))} && printf '%s' {shlex.quote(content)} > {temporary}"
        f" && chmod {mode} {temporary} && mv {temporary} {target}"
    )


def _check_apt(_box: Box) -> str | None:
    # dpkg-query exits 1 when any package is unknown; its answer for the rest still counts.
    status = _read(
        [
            "dpkg-query",
            "-W",
            "-f=${Package} ${Status}\\n",
            *APT_PACKAGES,
        ],
        any_exit=True,
    )
    installed = {line.split()[0] for line in status.splitlines() if line.endswith(" installed")}
    absent = [name for name in APT_PACKAGES if name not in installed]
    return ", ".join(absent) if absent else None


def _lines_apt(_box: Box) -> list[str]:
    packages = " ".join(APT_PACKAGES)
    return [
        "apt-get update",
        (
            "DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get -o DPkg::Lock::Timeout=300 "
            f"install -y {packages}"
        ),
    ]


def _check_gh(_box: Box) -> str | None:
    return None if _read(["sh", "-c", "command -v gh"]) else "gh"


def _lines_gh(_box: Box) -> list[str]:
    keyring = "/etc/apt/keyrings/githubcli-archive-keyring.gpg"
    source = (
        f"deb [arch=$(dpkg --print-architecture) signed-by={keyring}] "
        "https://cli.github.com/packages stable main"
    )
    return [
        "install -d -m 0755 /etc/apt/keyrings",
        f"curl -fsSL --retry 3 https://cli.github.com/packages/githubcli-archive-keyring.gpg -o {keyring}",
        f"chmod go+r {keyring}",
        f'echo "{source}" > /etc/apt/sources.list.d/github-cli.list',
        "apt-get update",
        "DEBIAN_FRONTEND=noninteractive apt-get -o DPkg::Lock::Timeout=300 install -y gh",
    ]


def _check_operator(box: Box) -> str | None:
    prefs = _read(["tailscale", "debug", "prefs"])
    return None if f'"OperatorUser": "{box.user}"' in prefs else "tailscale operator"


def _lines_operator(box: Box) -> list[str]:
    return [f"tailscale set --operator={shlex.quote(box.user)}"]


def _bashrc(box: Box) -> Path:
    return box.home / ".bashrc"


def _wanted_bashrc(box: Box) -> str:
    text = _text(_bashrc(box))
    text = with_block(text, PATH_MARK, _text(FILES / "bashrc-path.sh"), top=True)
    return with_block(text, INTERACTIVE_MARK, _text(FILES / "bashrc-interactive.sh"), top=False)


def _check_path_block(box: Box) -> str | None:
    text = _text(_bashrc(box))
    wanted = block(PATH_MARK, _text(FILES / "bashrc-path.sh"))
    return None if text.startswith(wanted) else "PATH block at the top of ~/.bashrc"


def _check_interactive_block(box: Box) -> str | None:
    wanted = block(INTERACTIVE_MARK, _text(FILES / "bashrc-interactive.sh"))
    return None if wanted in _text(_bashrc(box)) else "tmux and banner block in ~/.bashrc"


def _lines_bashrc(box: Box) -> list[str]:
    backup = f"cp -p ~/.bashrc ~/.bashrc.bak-{int(time.time())}"
    return [f"{backup} 2>/dev/null || true", write_line(_bashrc(box), _wanted_bashrc(box))]


def _check_tmux(box: Box) -> str | None:
    wanted = _text(FILES / "tmux.conf")
    return None if _text(box.home / ".tmux.conf") == wanted else "~/.tmux.conf"


def _lines_tmux(box: Box) -> list[str]:
    target = box.home / ".tmux.conf"
    keep = f"[ ! -e ~/.tmux.conf ] || cp -p ~/.tmux.conf ~/.tmux.conf.bak-{int(time.time())}"
    return [keep, write_line(target, _text(FILES / "tmux.conf"))]


def _git_wanted(box: Box) -> dict[str, str]:
    wanted = {"init.defaultBranch": "main"}
    if box.git_name:
        wanted["user.name"] = box.git_name
    if box.git_email:
        wanted["user.email"] = box.git_email
    return wanted


def _check_git(box: Box) -> str | None:
    wrong = [
        key
        for key, value in _git_wanted(box).items()
        if _read(
            [
                "git",
                "config",
                "--global",
                "--get",
                key,
            ],
        )
        != value
    ]
    return ", ".join(wrong) if wrong else None


def _lines_git(box: Box) -> list[str]:
    return [
        f"git config --global {key} {shlex.quote(value)}"
        for key, value in _git_wanted(box).items()
    ]


def _check_house(box: Box) -> str | None:
    stale = [name for name, body in house_tools(box).items() if _text(box.bin / name) != body]
    return ", ".join(stale) if stale else None


def _lines_house(box: Box) -> list[str]:
    return [write_line(box.bin / name, body, "755") for name, body in house_tools(box).items()]


def _units(box: Box) -> dict[Path, str]:
    folder = box.home / ".config" / "systemd" / "user"
    return {
        folder / unit.name: unit.read_text(encoding="utf-8")
        for unit in sorted((FILES / "systemd").iterdir())
    }


def _check_timer(box: Box) -> str | None:
    if any(_text(path) != body for path, body in _units(box).items()):
        return "git-autosync units"
    enabled = _read(
        [
            "systemctl",
            "--user",
            "is-enabled",
            "git-autosync.timer",
        ],
    )
    return None if enabled == "enabled" else "git-autosync.timer not enabled"


def _lines_timer(box: Box) -> list[str]:
    writes = [write_line(path, body) for path, body in _units(box).items()]
    return [
        *writes,
        "systemctl --user daemon-reload",
        "systemctl --user enable --now git-autosync.timer",
    ]


def _exists(*parts: str) -> Callable[[Box], str | None]:
    def check(box: Box) -> str | None:
        return None if box.home.joinpath(*parts).exists() else "/".join(("~", *parts))

    return check


def _installer(url: str) -> Callable[[Box], list[str]]:
    def lines(_box: Box) -> list[str]:
        return [f"curl -fsSL --retry 3 --proto '=https' {url} | bash"]

    return lines


def _lines_osv(box: Box) -> list[str]:
    base = "https://github.com/google/osv-scanner/releases/download"
    target = shlex.quote(str(box.bin / "osv-scanner"))
    url = f"{base}/{OSV_VERSION}/osv-scanner_linux_amd64"
    return [
        f"mkdir -p {shlex.quote(str(box.bin))}",
        (
            f"curl -fsSL --retry 3 -o {target}.dsf-tmp {url} && chmod 755 {target}.dsf-tmp "
            f"&& mv {target}.dsf-tmp {target}"
        ),
    ]


def _check_rules(box: Box) -> str | None:
    wanted = rules_text(box)
    stale = [str(path) for path in rules_targets(box) if _text(path) != wanted]
    return ", ".join(stale) if stale else None


def _lines_rules(box: Box) -> list[str]:
    text = rules_text(box)
    return [write_line(path, text) for path in rules_targets(box)]


def _check_logins(_box: Box) -> str | None:
    return None if _read(["sh", "-c", "gh auth status >/dev/null 2>&1 && echo ok"]) else "gh"


def _lines_logins(_box: Box) -> list[str]:
    return [
        "gh auth login",
        "opencode auth login",
        "muse",
        "grok",
        "agy",
    ]


STEPS: tuple[Step, ...] = (
    Step("apt-cli", "sudo", _check_apt, _lines_apt),
    Step("gh", "sudo", _check_gh, _lines_gh),
    Step("tailscale-operator", "sudo", _check_operator, _lines_operator),
    Step("path-block", "user", _check_path_block, _lines_bashrc),
    Step("interactive-block", "user", _check_interactive_block, _lines_bashrc),
    Step("tmux-conf", "user", _check_tmux, _lines_tmux),
    Step("gitconfig", "user", _check_git, _lines_git),
    Step("house-tools", "user", _check_house, _lines_house),
    Step("autosync-timer", "user", _check_timer, _lines_timer),
    Step(
        "opencode",
        "user",
        _exists(".opencode", "bin", "opencode"),
        _installer("https://opencode.ai/install"),
    ),
    Step(
        "muse",
        "user",
        _exists(".local", "bin", "muse"),
        _installer("https://dev.meta.ai/install.sh"),
    ),
    Step(
        "grok",
        "user",
        _exists(".grok", "bin", "grok"),
        _installer("https://x.ai/cli/install.sh"),
    ),
    Step(
        "agy",
        "user",
        _exists(".local", "bin", "agy"),
        _installer("https://antigravity.google/cli/install.sh"),
    ),
    Step("osv-scanner", "user", _exists(".local", "bin", "osv-scanner"), _lines_osv),
    Step("rules", "user", _check_rules, _lines_rules),
    Step("logins", "hand", _check_logins, _lines_logins),
)


def select(only: Sequence[str], skip: Sequence[str]) -> list[Step]:
    """Return the steps ``only`` names (all when empty), less the kinds ``skip`` names."""
    keys = {step.key for step in STEPS}
    unknown = [key for key in only if key not in keys] + [
        kind for kind in skip if kind not in KINDS
    ]
    if unknown:
        msg = f"unknown step or kind: {', '.join(unknown)}"
        raise ValueError(msg)
    return [step for step in STEPS if (not only or step.key in only) and step.kind not in skip]


def report(box: Box, steps: Sequence[Step]) -> tuple[list[str], bool]:
    """Return one line per step and whether every step is done."""
    width = max((len(step.key) for step in steps), default=0)
    lines: list[str] = []
    done = True
    for step in steps:
        gap = step.check(box)
        done = done and gap is None
        state = "ok     " if gap is None else "missing"
        lines.append(f"{state} {step.kind:<4} {step.key:<{width}}  {gap or ''}".rstrip())
    return lines, done


def run_lines(lines: Sequence[str], box: Box, *, sudo: bool = False) -> int:
    """Run ``lines`` as one shell script (``sudo sh -c`` for root); return its exit code."""
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
    env = dict(os.environ)
    env["PATH"] = f"{box.bin}{os.pathsep}{env.get('PATH', '/usr/bin:/bin')}"
    print(f"+ {script[:ECHO_LIMIT]}{' ...' if len(script) > ECHO_LIMIT else ''}", flush=True)
    try:
        return subprocess.run(argv, check=False, cwd=box.home, env=env).returncode
    except OSError as error:
        print(f"personal: {error}", file=sys.stderr)
        return 127


def install(box: Box, steps: Sequence[Step]) -> int:
    """Run every failing step, ``sudo`` ones first in one call; stop at one that still fails."""
    gaps = [(step, step.check(box)) for step in steps]
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
        if step.check(box) is None:  # an earlier step's lines made it pass (one .bashrc write)
            continue
        print(f"== {step.key}", flush=True)
        if run_lines(step.lines(box), box) or step.check(box) is not None:
            print(f"personal: step {step.key} failed; rerun after fixing it", file=sys.stderr)
            return 1
    left = [step.key for step in steps if step.check(box) is not None]
    print("done" if not left else f"done except: {', '.join(left)}")
    return 0


# The fleet side: run on a machine already in the fleet.


def bundle() -> bytes:
    """Return this folder (``personal.py`` and ``files/``) as a tar under ``setup/ubuntu``."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as archive:
        for path in sorted(HERE.rglob("*")):
            if "__pycache__" in path.parts or path.is_dir():
                continue
            archive.add(path, arcname=f"setup/ubuntu/{path.relative_to(HERE).as_posix()}")
    return buffer.getvalue()


def _git_identity() -> list[str]:
    words: list[str] = []
    for key, flag in (("user.name", "--git-name"), ("user.email", "--git-email")):
        value = _read(
            [
                "git",
                "config",
                "--global",
                "--get",
                key,
            ],
        )
        if value:
            words += [flag, value]
    return words


def apply(
    host: str,
    *,
    dry: bool,
    skip: Sequence[str],
    only: Sequence[str],
) -> int:
    """Copy this folder to ``host`` and run ``box check`` (``dry``) or ``box install`` there."""
    if host.startswith("-") or not re.fullmatch(r"[A-Za-z0-9._-]+", host):
        print(f"personal: refusing host {host!r}", file=sys.stderr)
        return 2
    unpack = f"rm -rf {REMOTE_DIR} && mkdir -p {REMOTE_ROOT} && tar -C {REMOTE_ROOT} -xf -"
    copied = subprocess.run(
        [
            "ssh",
            *SSH_OPTIONS,
            host,
            unpack,
        ],
        input=bundle(),
        capture_output=True,
        check=False,
    )
    if copied.returncode:
        print(f"personal: could not copy this folder to {host}", file=sys.stderr)
        return 2
    words = ["--skip", ",".join(skip)] if skip else []
    words += ["--only", ",".join(only)] if only else []
    words += [] if dry else _git_identity()
    command = f"python3 {REMOTE_DIR}/personal.py box {'check' if dry else 'install'} "
    command += " ".join(shlex.quote(word) for word in words)
    argv = [
        "ssh",
        *(() if dry else ("-t",)),
        *SSH_OPTIONS,
        host,
        command,
    ]
    return subprocess.run(argv, check=False).returncode


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
    git_name: str
    git_email: str


def main(argv: Sequence[str] | None = None) -> int:
    """Run one command; exit 0 when done, 1 on a missing or failed step, 2 on bad setup."""
    parser = argparse.ArgumentParser(description="Personalize an Ubuntu fleet machine (CLI only).")
    sub = parser.add_subparsers(dest="command", required=True)
    box_parser = sub.add_parser("box", help="run on the machine itself")
    _ = box_parser.add_argument("action", choices=["check", "install"])
    apply_parser = sub.add_parser("apply", help="run on <host> from this fleet machine")
    _ = apply_parser.add_argument("host")
    _ = apply_parser.add_argument("--check", action="store_true", help="report only")
    for each in (box_parser, apply_parser):
        _ = each.add_argument("--only", default="", help="comma-separated step keys")
        _ = each.add_argument("--skip", default="", help="comma-separated kinds")
    _ = box_parser.add_argument("--git-name", default="")
    _ = box_parser.add_argument("--git-email", default="")
    args = parser.parse_args(argv, namespace=_Args())
    try:
        steps = select(_csv(args.only), _csv(args.skip))
    except ValueError as error:
        parser.error(str(error))
    if args.command == "apply":
        return apply(args.host, dry=args.check, skip=_csv(args.skip), only=_csv(args.only))
    box = Box(
        home=Path.home(),
        user=os.environ.get("USER") or _read(["id", "-un"]),
        facts=measure(),
        git_name=args.git_name,
        git_email=args.git_email,
    )
    if args.action == "check":
        lines, done = report(box, steps)
        print("\n".join(lines))
        return 0 if done else 1
    return install(box, steps)


if __name__ == "__main__":
    sys.exit(main())
