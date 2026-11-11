"""Keep agents out of the shared checkout: an edit hook for Claude Code and a pytest guard.

Every change to the package, its tests and its docs is made in a private copy
(``scripts/work.py new <name>``), tested there (``work.py run <name> -- <cmd>``) and
reaches the shared checkout through ``work.py land <name>`` (START.md "Private working
copies"). Two entry points enforce it:

- :func:`edit_refusal`, run as a Claude Code ``PreToolUse`` hook
  (``.claude/settings.json`` runs this file before each ``Edit``, ``MultiEdit``,
  ``Write`` and ``NotebookEdit``; :func:`main` reads the hook payload on stdin). It
  denies a write whose target lies in the shared checkout outside ``.work/``, unless
  the target is an untracked git-ignored file or :func:`edited_in_place`. Each rule
  reads the target as the filesystem spells it (:func:`canonical`), and an exempt
  target is refused anyway when it is, by file identity, a tracked file not itself
  exempt (:func:`reaches_tracked`, asked of the checkout's own index), so no case or
  Unicode alias, hard link or inherited ``GIT_*`` variable reaches one. It covers
  every Claude session and subagent; other harnesses meet :func:`pytest_refusal` and
  AGENTS.md.
- :func:`pytest_refusal`, called by the repo-root ``conftest.py`` with its own folder:
  a pytest run that loads the shared checkout's conftest (whatever ``--rootdir`` or
  ``-c`` says) stops with the copy command. A terminal proves nothing (``ssh -t``
  gives an agent one), so only the override lets it run. The shared tree is
  concurrently dirty, so a result there measures other sessions' unfinished work, and
  its ``db.sqlite3`` and caches are shared.

The shared checkout is the nearest folder holding a real ``.work`` directory and a
``.git`` entry: ``.work`` is git-ignored, so no clone or worktree carries one, and a
path under ``<shared>/.work/`` (a copy, its evidence) is always allowed. CI's checkout
has no ``.work`` either. ``DSF_SHARED_EDIT=1`` / ``DSF_SHARED_PYTEST=1`` in the
environment lift each guard (the maintainer's own session).

Stdlib only, Python 3.9+: the hook runs on the system ``python3``, once per write, and
fails closed: an unreadable payload or an error classifying the target (git missing, a
failed lookup) denies the write, names the error, and points at ``DSF_SHARED_EDIT=1``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath
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

#: Shared-checkout files (POSIX, relative to its root) the FIX coordinator edits in
#: place by design (docs/bug_hunt/FIX.md phase 8).
EDITED_IN_PLACE = frozenset({"CHANGELOGTODO.md"})
#: The folder whose own ``*.md`` files (not its subfolders') are edited in place too.
EDITED_IN_PLACE_FOLDER = "docs/bug_hunt"

#: Environment variables that lift the edit guard and the pytest guard.
EDIT_OVERRIDE_ENV = "DSF_SHARED_EDIT"
PYTEST_OVERRIDE_ENV = "DSF_SHARED_PYTEST"

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


def edited_in_place(relative: str) -> bool:
    """Return whether ``relative`` is a file the FIX coordinator edits in the shared tree."""
    path = PurePosixPath(relative)
    return relative in EDITED_IN_PLACE or (
        path.parent.as_posix() == EDITED_IN_PLACE_FOLDER and path.suffix == ".md"
    )


def canonical(root: Path, target: Path) -> Path:
    """Return ``target`` (under ``root``) spelled as the filesystem stores each component.

    On a case-insensitive or normalization-insensitive filesystem ``DOCS/Fix.MD`` names
    the stored ``docs/FIX.md``: a component whose name is not listed takes the one
    entry that is the same file and equal under caseless matching. Hard links make an
    identity ambiguous, so with none or several such entries the given name stays, as
    does a missing tail.
    """
    current = root
    parts = target.relative_to(root).parts
    for index, part in enumerate(parts):
        try:
            held = (current / part).lstat()
            names = [entry.name for entry in current.iterdir()]
        except FileNotFoundError:
            return current.joinpath(*parts[index:])
        current = current / (part if part in names else _stored_name(current, names, part, held))
    return current


def _stored_name(
    folder: Path,
    names: list[str],
    part: str,
    held: os.stat_result,
) -> str:
    """Return the one entry of ``folder`` that is ``held`` and folds as ``part``, else ``part``."""
    found = [
        name
        for name in names
        if _identity((folder / name).lstat()) == _identity(held) and _fold(name) == _fold(part)
    ]
    return found[0] if len(found) == 1 else part


def _identity(status: os.stat_result) -> tuple[int, int]:
    return (status.st_dev, status.st_ino)


def _fold(relative: str) -> str:
    """Return ``relative`` for caseless comparison (Unicode canonical caseless match)."""
    return unicodedata.normalize("NFD", unicodedata.normalize("NFD", relative).casefold())


def _normal(relative: str) -> str:
    """Return ``relative`` for comparison on a case-sensitive filesystem (normalization only)."""
    return unicodedata.normalize("NFD", relative)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    """Run git in ``root`` with no inherited ``GIT_*`` variable (no caller's index or dir)."""
    env = {name: value for name, value in os.environ.items() if not name.startswith("GIT_")}
    return subprocess.run(
        [
            "git",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        check=False,
        env=env,
    )


def tracked_names(root: Path) -> list[str]:
    """Return every path ``root``'s own index tracks.

    Raises:
        OSError: ``git ls-files`` failed, or the index is missing in a repository with
            a commit (an empty answer there is not "nothing is tracked").

    """
    listed = _git(root, "ls-files", "-z")
    if listed.returncode != 0:
        msg = f"git ls-files failed: {listed.stderr.decode(errors='replace').strip()}"
        raise OSError(msg)
    names = [name for name in os.fsdecode(listed.stdout).split("\0") if name]
    if not names and _git(root, "rev-parse", "--verify", "-q", "HEAD").returncode == 0:
        index = _git(root, "rev-parse", "--git-path", "index")
        where = root / os.fsdecode(index.stdout).strip()
        if index.returncode != 0 or not where.is_file():
            msg = f"the index of {root} is missing, so what it tracks is unknown"
            raise OSError(msg)
    return names


def _case_insensitive(root: Path) -> bool:
    """Return whether ``root``'s filesystem reads ``.WORK`` as its ``.work`` folder."""
    alias = root / ".WORK"
    return alias.exists() and alias.samefile(root / ".work")


def _never(_name: str) -> bool:
    return False


def reaches_tracked(root: Path, relative: str, exempt: Callable[[str], bool] = _never) -> bool:
    """Return whether writing ``relative`` writes a tracked file whose own name is not ``exempt``.

    An existing target is matched by file identity against every tracked path, so a
    hard link or any alias the filesystem resolves counts. A missing target counts
    when a tracked name equals it, or folds as it (case-insensitive filesystems) or
    normalizes as it (case-sensitive ones) while that tracked file is missing too.

    Raises:
        OSError: the index or a path cannot be read (:func:`tracked_names`).

    """
    target = root / relative
    names = [name for name in tracked_names(root) if not exempt(name)]
    try:
        held = target.stat()
    except FileNotFoundError:
        key = _fold if _case_insensitive(root) else _normal
        return any(
            name == relative or (key(name) == key(relative) and not (root / name).exists())
            for name in names
        )
    for name in names:
        try:
            status = (root / name).stat()
        except (FileNotFoundError, NotADirectoryError):
            continue
        if _identity(status) == _identity(held):
            return True
    return False


def is_ignored(root: Path, relative: str) -> bool:
    """Return whether a git ignore rule matches ``relative`` (tracked or not).

    ``check-ignore --no-index`` reads ``relative`` as a name, never matching it against
    the index (a literal ``*.local.json`` is a file name here); :func:`reaches_tracked`
    asks about tracking.
    """
    return _git(root, "check-ignore", "--no-index", "-q", "--", relative).returncode == 0


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
    relative = canonical(root, target).relative_to(root).as_posix()
    if relative.startswith(".work/"):
        return None
    if edited_in_place(relative):
        if not reaches_tracked(root, relative, edited_in_place):
            return None
    elif is_ignored(root, relative) and not reaches_tracked(root, relative):
        return None
    return (
        f"Refused: {relative} is in the shared checkout ({root}), which no agent edits directly. "
        f"{_COPY_HOWTO} Only docs/bug_hunt/*.md and CHANGELOGTODO.md are edited in place."
    )


def pytest_refusal(checkout: Path, environ: Mapping[str, str]) -> str | None:
    """Return why a pytest run loading the conftest in ``checkout`` is refused, else ``None``.

    Refused when ``checkout`` is in the shared checkout and ``DSF_SHARED_PYTEST=1`` is
    unset. The root ``conftest.py`` passes its own folder, not ``config.rootpath``,
    which ``--rootdir`` and ``-c`` move while the shared tests and conftest still load.
    """
    if environ.get(PYTEST_OVERRIDE_ENV) == "1":
        return None
    root = shared_root(Path(os.path.realpath(checkout)))
    if root is None:
        return None
    return (
        f"Refused: pytest in the shared checkout ({root}). Its tree is concurrently "
        f"dirty and its database shared, so a run there measures other sessions' work. "
        f"{_COPY_HOWTO} To test a commit (after a landing, or a parent), use "
        "`work.py new carve-<id>-<slug> --worktree --from <sha>`. The maintainer's own run: "
        f"`{PYTEST_OVERRIDE_ENV}=1 pytest ...`."
    )


def _payload(text: str) -> dict[str, object]:
    """Return the hook payload ``text`` decodes to.

    Raises:
        ValueError: ``text`` is not JSON.
        TypeError: it is not a JSON object.

    """
    payload = _loads(text)
    if not is_json_object(payload):
        msg = f"the hook payload is a {type(payload).__name__}, not an object"
        raise TypeError(msg)
    return payload


def main() -> int:
    """Run as the ``PreToolUse`` hook: print a deny decision when the write is refused.

    An unreadable payload (``ValueError``), an unexpected shape (``TypeError``) or a
    failed path or git lookup (``OSError``) denies the write, naming the error.
    """
    if os.environ.get(EDIT_OVERRIDE_ENV) == "1":
        return 0
    try:
        reason = edit_refusal(_payload(sys.stdin.read()), os.environ)
    except (ValueError, TypeError, OSError) as error:
        reason = (
            f"Refused: shared_checkout_guard could not classify this write ({error!r}), so it "
            f"denies it. Fix the cause, or set {EDIT_OVERRIDE_ENV}=1 in the maintainer's own session."
        )
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
