"""Keep agents out of the shared checkout: an edit hook for Claude Code and a pytest guard.

Every change to the package, its tests and its docs is made in a private copy
(``scripts/work.py new <name>``), tested there (``work.py run <name> -- <cmd>``) and
reaches the shared checkout through ``work.py land <name>`` (START.md "Private working
copies"). Two entry points enforce it:

- :func:`edit_refusal`, run as a Claude Code ``PreToolUse`` hook
  (``.claude/settings.json`` runs this file before each ``Edit``, ``MultiEdit``,
  ``Write`` and ``NotebookEdit``; :func:`main` reads the hook payload on stdin). It
  denies a write whose target lies in the shared checkout outside ``.work/``, unless
  the target is git-ignored or on :data:`EDITED_IN_PLACE`. It covers every Claude
  session and subagent; other harnesses meet :func:`pytest_refusal` and AGENTS.md.
- :func:`pytest_refusal`, called by the repo-root ``conftest.py``: a pytest run whose
  root is the shared checkout stops with the copy command unless a person started it
  at a terminal. The shared tree is concurrently dirty, so a result there measures
  other sessions' unfinished work, and its ``db.sqlite3`` and caches are shared.

The shared checkout is the nearest folder holding a real ``.work`` directory and a
``.git`` entry: ``.work`` is git-ignored, so no clone or worktree carries one, and a
path under ``<shared>/.work/`` (a copy, its evidence) is always allowed. CI's checkout
has no ``.work`` either. ``DSF_SHARED_EDIT=1`` / ``DSF_SHARED_PYTEST=1`` in the
environment lift each guard (a maintainer's own session).

Stdlib only, Python 3.9+: the hook runs on the system ``python3``, once per write, and
fails open (an unreadable payload or an unexpected error allows the write and says so
on stderr) so a broken guard never wedges a session.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from typing_extensions import TypeIs

#: Tools whose hook payload names a file the tool will write.
GUARDED_TOOLS = frozenset(
    {
        "Edit",
        "MultiEdit",
        "Write",
        "NotebookEdit",
    },
)

#: Shared-checkout paths (POSIX, relative to its root) the FIX coordinator edits in
#: place by design (docs/bug_hunt/FIX.md phase 8); a trailing ``/`` covers a folder.
EDITED_IN_PLACE = ("docs/bug_hunt/", "CHANGELOGTODO.md")

#: Environment variables that lift the edit guard and the pytest guard.
EDIT_OVERRIDE_ENV = "DSF_SHARED_EDIT"
PYTEST_OVERRIDE_ENV = "DSF_SHARED_PYTEST"

#: Environment variables an agent harness sets in the shells it runs commands in.
AGENT_ENV_MARKERS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT")
#: Prefixes of environment variables an agent harness sets.
AGENT_ENV_PREFIXES = ("CODEX_",)

#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads

_COPY_HOWTO = (
    "Make a private copy and work there: `uv run python scripts/work.py new <kind>-<id>-<slug> "
    "--purpose '...'` (kinds: build fix spike verify ci bench head carve deps spec ship; max 24 "
    "characters), edit under `.work/clones/<name>/`, run every command with "
    "`uv run python scripts/work.py run <name> -- <cmd>`, then `work.py land <name>` puts the "
    'change, uncommitted, in the shared working tree (START.md "Private working copies").'
)


def is_json_object(value: object) -> TypeIs[dict[str, object]]:
    """Return whether ``value`` is a decoded JSON object (whose keys are always strings)."""
    return isinstance(value, dict)


def shared_root(path: Path) -> Path | None:
    """Return the shared checkout ``path`` lies in (``path`` itself included), else ``None``.

    The checkout is the nearest folder holding a ``.git`` entry; it is the shared one
    when it also holds a real ``.work`` directory. A copy under ``<shared>/.work/`` has
    its own ``.git`` and no ``.work``, so it is never the shared checkout.
    """
    for folder in (path, *path.parents):
        if (folder / ".git").exists():
            work = folder / ".work"
            return folder if work.is_dir() and not work.is_symlink() else None
    return None


def has_terminal() -> bool:
    """Return whether this process has a controlling terminal (a person at a shell).

    Asked of ``/dev/tty`` rather than of stdin, which pytest's capture replaces while
    conftests load; an agent harness runs commands with no controlling terminal.
    """
    try:
        descriptor = os.open("/dev/tty", os.O_RDONLY)
    except OSError:
        return False
    os.close(descriptor)
    return True


def is_ignored(root: Path, relative: str) -> bool:
    """Return whether git ignores ``relative`` in the checkout at ``root`` (a tracked file never is)."""
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "check-ignore",
            "-q",
            "--",
            relative,
        ],
        capture_output=True,
        check=False,
    )
    return completed.returncode == 0


def edit_refusal(payload: Mapping[str, object], environ: Mapping[str, str]) -> str | None:
    """Return why the write a ``PreToolUse`` ``payload`` describes is refused, else ``None``."""
    if environ.get(EDIT_OVERRIDE_ENV) == "1" or payload.get("tool_name") not in GUARDED_TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not is_json_object(tool_input):
        return None
    raw = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not isinstance(raw, str) or not raw:
        return None
    target = Path(raw)
    if not target.is_absolute():
        cwd = payload.get("cwd")
        target = (Path(cwd) if isinstance(cwd, str) else Path.cwd()) / target
    target = Path(os.path.realpath(target))
    root = shared_root(target.parent)
    if root is None:
        return None
    relative = target.relative_to(root).as_posix()
    if relative.startswith(".work/"):
        return None
    if any(
        relative == entry or (entry.endswith("/") and relative.startswith(entry))
        for entry in EDITED_IN_PLACE
    ):
        return None
    if is_ignored(root, relative):
        return None
    return (
        f"Refused: {relative} is in the shared checkout ({root}), which no agent edits directly. "
        f"{_COPY_HOWTO} Only docs/bug_hunt/*.md and CHANGELOGTODO.md are edited in place."
    )


def runs_under_agent(environ: Mapping[str, str]) -> bool:
    """Return whether ``environ`` carries an agent harness's marker."""
    return any(name in environ for name in AGENT_ENV_MARKERS) or any(
        name.startswith(AGENT_ENV_PREFIXES) for name in environ
    )


def pytest_refusal(rootdir: Path, environ: Mapping[str, str], *, interactive: bool) -> str | None:
    """Return why a pytest run rooted at ``rootdir`` is refused, else ``None``.

    Refused when ``rootdir`` is the shared checkout and the run is not a person's at a
    terminal (``interactive`` false, :func:`has_terminal` in production, or an agent
    harness's environment) and
    ``DSF_SHARED_PYTEST=1`` is unset.
    """
    if environ.get(PYTEST_OVERRIDE_ENV) == "1":
        return None
    root = shared_root(Path(os.path.realpath(rootdir)))
    if root is None or (interactive and not runs_under_agent(environ)):
        return None
    return (
        f"Refused: pytest rooted at the shared checkout ({root}). Its tree is concurrently "
        f"dirty and its database shared, so a run there measures other sessions' work. "
        f"{_COPY_HOWTO} To test a commit (after a landing, or a parent), use "
        "`work.py new carve-<id>-<slug> --worktree --from <sha>`."
    )


def main() -> int:
    """Run as the ``PreToolUse`` hook: print a deny decision when the write is refused.

    An unreadable payload (``ValueError``), an unexpected shape (``TypeError``) or a
    failed path or git lookup (``OSError``) allows the write and says so on stderr.
    """
    try:
        payload = _loads(sys.stdin.read())
        reason = edit_refusal(payload, os.environ) if is_json_object(payload) else None
    except (ValueError, TypeError, OSError) as error:
        print(f"shared_checkout_guard: allowing after an error: {error!r}", file=sys.stderr)
        return 0
    if reason is not None:
        decision = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
        }
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
