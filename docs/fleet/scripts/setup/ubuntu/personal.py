"""Personalize an Ubuntu fleet machine the way ``rio-ubu`` is: CLI tools, dotfiles, GNOME settings.

The core setup (``docs/fleet/scripts/fleet_setup.py add <host>``) makes a machine a fleet member;
this script is the optional layer on top: the extra command-line tools, the shell, tmux and git
preferences, the load-aware house tools, the agent rules file and the GNOME desktop settings. It
installs no GUI application.

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
    (root), ``tty`` (a vendor installer that asks questions and runs ``sudo`` itself: needs a
    terminal; an agent testing the script passes ``--skip tty``), ``user`` (the home folder),
    ``hand`` (reported, never run: the logins).

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
    ``toshy``
        Toshy (Mac-style keyboard shortcuts) from its release :data:`TOSHY_TAG`, through its own
        ``setup_toshy.py install``. Its keymapper service, tray icon and the user's ``input``
        group take effect at the next login.
    ``toshy-config``
        rio-ubu's Toshy choices into Toshy's own files: the ``kbtype_override`` slice of
        ``~/.config/toshy/toshy_config.py`` (the one slice rio-ubu changed; Toshy keeps slices
        across its upgrades) and ``files/toshy/preferences.json`` into its preferences database;
        then ``toshy-config.service`` restarts.
    ``shell-extensions``
        The GNOME Shell extensions rio-ubu runs (:data:`EXTENSIONS`, pinned to rio-ubu's
        versions), through ``gnome-shell-extensions install``; ``apt-cli`` adds the
        ``gnome-shell-extensions`` set. ``desktop-settings`` enables them; a new one loads at the
        next login. Runs after Toshy so Toshy's own extension install cannot shadow a version.
    ``desktop-settings``
        GNOME as ``rio-ubu`` has it, from ``files/desktop/dconf.ini`` (``dconf load /``): fonts,
        clock, mouse/keyboard/touchpad, window buttons and behaviour, keybindings, Nautilus and
        file-chooser views, Ptyxis and Text Editor, the dock (left, 40 px, fixed, full height,
        dots, cycle on scroll), desktop icons, screen blank 15 min and no sleep on AC, location
        off, and the enabled extensions list. The dock's favourites are
        ``files/desktop/favorites.txt`` less the apps the target lacks. Machine state stays out
        (monitor connectors, window sizes, profile ids, night-light coordinates, extension
        bookkeeping, and the edge-tiling keys Tiling Assistant saves and restores on every lock).
        Settings for an extension the target lacks are stored and take effect if it is added.
    ``desktop-files``
        ``~/projects`` first in the Files sidebar, four ``~/Templates`` (New Document), and the
        Nautilus "Copy Path" script on Ctrl+Alt+C (``wl-copy``, from ``wl-clipboard``).
    ``logins``
        By hand: ``gh auth login``, ``opencode``, ``muse``, ``grok`` and ``agy`` each sign in once.

Left out on purpose: desktop GUI applications (and the Claude Desktop Nautilus scripts that need
one) and rootless Docker.

Standard library only, Python 3.9, so it runs from the system ``python3`` with nothing else.
"""

from __future__ import annotations

import argparse
import dataclasses
import io
import json
import os
import re
import shlex
import shutil
import socket
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from typing_extensions import TypeIs

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
    "wl-clipboard",
    "dconf-cli",
    "gnome-shell-extensions",
)
OSV_VERSION = "v2.7.0"
KINDS = (
    "sudo",
    "tty",
    "user",
    "hand",
)
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


# Toshy (Mac-style keys) and the GNOME Shell extensions rio-ubu runs.

TOSHY = FILES / "toshy"
TOSHY_TAG = "Toshy_v26.11.0"
TOSHY_CONFIG = ".config/toshy/toshy_config.py"
TOSHY_PREFERENCES = ".config/toshy/toshy_user_preferences.sqlite"
SLICE = "kbtype_override"
EGO = (
    "https://extensions.gnome.org/download-extension/{uuid}.shell-extension.zip?version_tag={tag}"
)
#: uuid -> (version its metadata.json names, download URL); rio-ubu's versions, GNOME Shell 50.
EXTENSIONS = {
    "Vitals@CoreCoding.com": ("86", EGO.format(uuid="Vitals@CoreCoding.com", tag=76696)),
    "executor@raujonas.github.io": (
        "32",
        EGO.format(uuid="executor@raujonas.github.io", tag=77158),
    ),
    "clipboard-indicator@tudmotu.com": (
        "72",
        EGO.format(uuid="clipboard-indicator@tudmotu.com", tag=77939),
    ),
    "focused-window-dbus@flexagoon.com": (
        "12",
        EGO.format(uuid="focused-window-dbus@flexagoon.com", tag=76809),
    ),
    "moveclock@kuvaus.org": ("11", EGO.format(uuid="moveclock@kuvaus.org", tag=75265)),
    "pinned-apps-in-appgrid@brunosilva.io": (
        "9",
        EGO.format(uuid="pinned-apps-in-appgrid@brunosilva.io", tag=75582),
    ),
    "workspace-islands@danielbernalo.github.io": (
        "0.1.2",
        (
            "https://github.com/danielbernalo/gnome-workspace-islands/releases/download/v0.1.2/"
            "workspace-islands%40danielbernalo.github.io.shell-extension.zip"
        ),
    ),
}
SLICE_BLOCK = re.compile(
    rf"(^###  SLICE_MARK_START: {SLICE}  ###[^\n]*\n)(.*?)(^###  SLICE_MARK_END: {SLICE}  ###)",
    re.DOTALL | re.MULTILINE,
)


#: ``json.loads`` and an sqlite row read, their results typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads


def _is_object(value: object) -> TypeIs[dict[str, object]]:
    return isinstance(value, dict)


def _rows(connection: sqlite3.Connection, query: str) -> list[tuple[object, ...]]:
    cursor = connection.execute(query)
    rows: list[tuple[object, ...]] = cursor.fetchall()
    return rows


def _check_toshy(box: Box) -> str | None:
    if not (box.home / TOSHY_CONFIG).exists():
        return "Toshy not installed"
    enabled = _read(
        [
            "systemctl",
            "--user",
            "is-enabled",
            "toshy-config.service",
        ],
    )
    return None if enabled == "enabled" else "toshy-config.service not enabled"


def _lines_toshy(_box: Box) -> list[str]:
    folder = f"{REMOTE_ROOT}/toshy"
    archive = f"https://codeload.github.com/RedBearAK/toshy/tar.gz/refs/tags/{TOSHY_TAG}"
    return [
        f"rm -rf {folder} && mkdir -p {folder}",
        f"curl -fsSL --retry 3 --proto '=https' {archive} | tar -xzf - --strip-components=1 -C {folder}",
        # Toshy's own installer: it asks before each change and runs sudo itself.
        f"cd {folder} && ./setup_toshy.py install --admin-capable yes --skip-update-check",
    ]


def toshy_preferences() -> dict[str, str]:
    """Return rio-ubu's Toshy preferences (``files/toshy/preferences.json``)."""
    loaded = _loads((TOSHY / "preferences.json").read_text(encoding="utf-8"))
    if not _is_object(loaded):
        msg = "preferences.json must hold one object"
        raise TypeError(msg)
    return {str(key): str(value) for key, value in loaded.items()}


def _slice_body() -> str:
    return "\n" + (TOSHY / f"{SLICE}.slice").read_text(encoding="utf-8").strip("\n") + "\n\n\n"


def with_slice(config: str) -> str:
    """Return Toshy's config with this repo's ``kbtype_override`` slice (unchanged without one)."""
    return SLICE_BLOCK.sub(
        lambda match: match.group(1) + _slice_body() + match.group(3),
        config,
        count=1,
    )


def _stored_preferences(box: Box) -> dict[str, str]:
    path = box.home / TOSHY_PREFERENCES
    if not path.exists():
        return {}
    connection = sqlite3.connect(str(path))
    try:
        rows = _rows(connection, "SELECT name, value FROM config_preferences")
    except sqlite3.Error:
        return {}
    finally:
        connection.close()
    return {str(row[0]): str(row[1]) for row in rows}


def _check_toshy_config(box: Box) -> str | None:
    config = _text(box.home / TOSHY_CONFIG)
    if not config:
        return "no Toshy config (the toshy step installs it)"
    gaps = [] if with_slice(config) == config else [SLICE]
    stored = _stored_preferences(box)
    gaps += [name for name, value in toshy_preferences().items() if stored.get(name) != value]
    return ", ".join(gaps) if gaps else None


def _lines_toshy_config(_box: Box) -> list[str]:
    return [f"python3 {shlex.quote(str(Path(__file__).resolve()))} box toshy-sync"]


def toshy_sync(box: Box) -> int:
    """Write the slice and the preferences into Toshy's own files, then restart its keymapper."""
    config = box.home / TOSHY_CONFIG
    text = _text(config)
    if not text:
        print("personal: no Toshy config to edit", file=sys.stderr)
        return 1
    _ = config.write_text(with_slice(text), encoding="utf-8")
    connection = sqlite3.connect(str(box.home / TOSHY_PREFERENCES))
    try:
        _ = connection.execute(
            "CREATE TABLE IF NOT EXISTS config_preferences (name TEXT PRIMARY KEY, value TEXT)",
        )
        _ = connection.executemany(
            "INSERT OR REPLACE INTO config_preferences (name, value) VALUES (?, ?)",
            sorted(toshy_preferences().items()),
        )
        connection.commit()
    finally:
        connection.close()
    try:  # no systemd user manager (or no Toshy service yet): nothing to restart
        return subprocess.run(
            [
                "systemctl",
                "--user",
                "try-restart",
                "toshy-config.service",
            ],
            check=False,
        ).returncode
    except OSError:
        return 0


def _extension_folder(box: Box, uuid: str) -> Path:
    return box.home / ".local" / "share" / "gnome-shell" / "extensions" / uuid


def _extension_version(folder: Path) -> str:
    meta = folder / "metadata.json"
    if not meta.exists():
        return ""
    loaded = _loads(meta.read_text(encoding="utf-8"))
    if not _is_object(loaded):
        return ""
    version = loaded.get("version-name") or loaded.get("version")
    return str(version) if version is not None else ""


def _missing_extensions(box: Box) -> list[str]:
    return [
        uuid
        for uuid, (version, _url) in EXTENSIONS.items()
        if _extension_version(_extension_folder(box, uuid)) != version
    ]


def _check_extensions(box: Box) -> str | None:
    absent = _missing_extensions(box)
    return ", ".join(absent) if absent else None


def _lines_extensions(box: Box) -> list[str]:
    folder = f"{REMOTE_ROOT}/extensions"
    lines = [f"mkdir -p {folder}"]
    for uuid in _missing_extensions(box):
        zipped = f"{folder}/{uuid}.zip"
        url = shlex.quote(EXTENSIONS[uuid][1])
        lines.append(
            f"curl -fsSL --retry 3 --proto '=https' -o {zipped} {url} "
            f"&& gnome-extensions install --force {zipped}",
        )
    return lines


# The GNOME desktop: settings and Nautilus extras, no application installed.

DESKTOP = FILES / "desktop"
#: Folders a ``.desktop`` file may live in; a dock favourite is kept only when one holds it.
APPLICATION_DIRS = (
    "/usr/share/applications",
    "/usr/local/share/applications",
    "/var/lib/snapd/desktop/applications",
    "/var/lib/flatpak/exports/share/applications",
    "~/.local/share/flatpak/exports/share/applications",
    "~/.local/share/applications",
)
BOOKMARK = "file://{home}/projects projects"
ACCEL = "<Control><Alt>c Copy Path"


def favorites(box: Box) -> str:
    """Return the dock's favourites as a GVariant list: rio-ubu's order, installed apps only."""
    wanted = [
        line.strip()
        for line in (DESKTOP / "favorites.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    folders = [Path(folder.replace("~", str(box.home), 1)) for folder in APPLICATION_DIRS]
    kept = [name for name in wanted if any((folder / name).exists() for folder in folders)]
    return "[" + ", ".join(f"'{name}'" for name in kept) + "]" if kept else "@as []"


def dconf_text(box: Box) -> str:
    """Return the desktop settings rendered for ``box`` (dconf's own keyfile form)."""
    mapping = {"HOME": str(box.home), "FAVORITES": favorites(box)}
    return render((DESKTOP / "dconf.ini").read_text(encoding="utf-8"), mapping)


def dconf_keys(text: str) -> dict[str, str]:
    """Return every ``/path/key`` and its value in a dconf keyfile."""
    keys: dict[str, str] = {}
    section = ""
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif "=" in line and section:
            key, value = line.split("=", 1)
            keys[f"/{section}/{key}"] = value
    return keys


def _check_desktop_settings(box: Box) -> str | None:
    if not shutil.which("dconf"):
        return "no dconf command (the apt-cli step installs dconf-cli)"
    wrong = [
        path
        for path, value in dconf_keys(dconf_text(box)).items()
        if _read(["dconf", "read", path]) != value
    ]
    return f"{len(wrong)} desktop settings ({wrong[0]} ...)" if wrong else None


def _lines_desktop_settings(box: Box) -> list[str]:
    staged = box.home / ".cache" / "dsf-fleet-setup" / "desktop.ini"
    return [write_line(staged, dconf_text(box)), f"dconf load / < {shlex.quote(str(staged))}"]


def _desktop_files(box: Box) -> dict[Path, tuple[str, str]]:
    """Return each Nautilus extra's path, content and mode."""
    files: dict[Path, tuple[str, str]] = {}
    for source in sorted((DESKTOP / "templates").iterdir()):
        # A template a project gate would read as code or docs is stored as ``<name>.tmpl``.
        name = source.name.removesuffix(".tmpl")
        files[box.home / "Templates" / name] = (source.read_text(encoding="utf-8"), "644")
    scripts = box.home / ".local" / "share" / "nautilus" / "scripts"
    for source in sorted((DESKTOP / "nautilus-scripts").iterdir()):
        files[scripts / source.name] = (source.read_text(encoding="utf-8"), "755")
    accels = box.home / ".config" / "nautilus" / "scripts-accels"
    # One binding per script name (Nautilus keeps the last): drop every other line for this script.
    script = ACCEL.split(None, 1)[1]
    lines = [
        line
        for line in _text(accels).splitlines()
        if line.strip() and line.strip().split(None, 1)[1:] != [script]
    ]
    files[accels] = ("\n".join([ACCEL, *lines]) + "\n", "644")
    bookmarks = box.home / ".config" / "gtk-3.0" / "bookmarks"
    mark = BOOKMARK.format(home=box.home)
    rest = [line for line in _text(bookmarks).splitlines() if line.strip() and line != mark]
    files[bookmarks] = ("\n".join([mark, *rest]) + "\n", "644")
    return files


def _check_desktop_files(box: Box) -> str | None:
    stale = [
        path.name
        for path, (body, mode) in _desktop_files(box).items()
        if not path.exists() or _text(path) != body or path.stat().st_mode & 0o777 != int(mode, 8)
    ]
    return ", ".join(stale) if stale else None


def _lines_desktop_files(box: Box) -> list[str]:
    return [write_line(path, body, mode) for path, (body, mode) in _desktop_files(box).items()]


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
    Step("toshy", "tty", _check_toshy, _lines_toshy),
    Step("toshy-config", "user", _check_toshy_config, _lines_toshy_config),
    Step("shell-extensions", "user", _check_extensions, _lines_extensions),
    Step("desktop-settings", "user", _check_desktop_settings, _lines_desktop_settings),
    Step("desktop-files", "user", _check_desktop_files, _lines_desktop_files),
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
    # dconf writes through the session bus; over ssh there is none in the environment.
    _ = env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path=/run/user/{os.getuid()}/bus")
    print(f"+ {script[:ECHO_LIMIT]}{' ...' if len(script) > ECHO_LIMIT else ''}", flush=True)
    try:
        return subprocess.run(argv, check=False, cwd=box.home, env=env).returncode
    except OSError as error:
        print(f"personal: {error}", file=sys.stderr)
        return 127


def install(box: Box, steps: Sequence[Step]) -> int:
    """Run every failing step, ``sudo`` ones first in one call; stop at one that still fails.

    Each other step is checked just before its turn, not once up front: an earlier step can undo
    a later one (Toshy's installer rewrites a GNOME keybinding ``desktop-settings`` owns) or do
    it (one ``.bashrc`` write serves two steps).
    """
    root = [step for step in steps if step.kind == "sudo" and step.check(box) is not None]
    if root:
        print(f"== sudo: {', '.join(step.key for step in root)}", flush=True)
        if run_lines([line for step in root for line in step.lines(box)], box, sudo=True):
            return 1
    for step in steps:
        if step.kind == "sudo":
            continue
        gap = step.check(box)
        if gap is None:
            continue
        if step.kind == "hand":
            print(f"== {step.key}: by hand ({gap}):")
            print("\n".join(f"   {line}" for line in step.lines(box)))
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
    parser = argparse.ArgumentParser(
        description="Personalize an Ubuntu fleet machine (no GUI app installed).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    box_parser = sub.add_parser("box", help="run on the machine itself")
    _ = box_parser.add_argument("action", choices=["check", "install", "toshy-sync"])
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
    if args.action == "toshy-sync":
        return toshy_sync(box)
    if args.action == "check":
        lines, done = report(box, steps)
        print("\n".join(lines))
        return 0 if done else 1
    return install(box, steps)


if __name__ == "__main__":
    sys.exit(main())
