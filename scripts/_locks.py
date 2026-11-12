"""The kernel-lock rule the fleet scripts share, and the one-pytest-at-a-time lock of a checkout.

Taking a lock
    The one contention rule of the repository's scripts: only
    :func:`is_contention` (``EAGAIN``/``EWOULDBLOCK``; ``EACCES``/``EDEADLOCK``
    from ``msvcrt``) means another holder has a lock, and any other error is
    raised, never read as a holder. :func:`try_lock` takes an exclusive,
    non-blocking kernel lock by it (``flock``; ``msvcrt.locking`` on Windows):
    ``scripts/work.py`` (``land.lock``, ``fleet.lock``, the pytest lock, each
    evidence stem's ``stem-locks/<stem>.lock``),
    ``docs/fleet/scripts/fleet_sync.py`` (``fleet.lock``) and
    ``scripts/prove_failability.py`` (its repository-root lock).
    ``scripts/workspace.py`` keeps its own ``flock`` calls (some block, some
    retry on a replaced path) and classifies their errors by
    :func:`is_contention`.

One pytest at a time
    A pytest run here is heavy enough that two at once starve the machine, so the
    scripts that start pytest (``scripts/work.py run`` for a pytest command,
    ``scripts/prove_failability.py`` for each scope it runs) take one lock per
    checkout first, waiting while another holds it: :func:`hold_pytest`.

The pytest lock
    ``.work/pytest.lock`` of the shared checkout (:func:`pytest_lock_path`,
    :func:`shared_checkout`): a clone at ``.work/clones/<name>`` and a linked
    worktree (``.work/worktrees/<name>`` or a harness's), each checked against
    the shared checkout's own ``.git``, take their shared checkout's lock, so a
    run in the shared checkout and one in any of its copies take the same
    lock. Any other checkout takes its own, even one under an unrelated
    ``.work`` folder or one whose ``.git`` points somewhere unverified. It is the kernel's
    (``flock``; ``msvcrt.locking`` on Windows), released however its holder
    ends and never taken over. Its holder writes one line naming itself
    (copy, owner, machine, pid) for the waiting line. A lock call is retried
    only while another holder has it (:func:`try_lock`).

Held by a parent
    A holder starts its children with :data:`HELD_ENV` naming the lock, and
    :func:`hold_pytest` under that variable takes nothing: a pytest started by a run
    that already holds the lock (``work.py run -- pytest`` whose tests start
    pytest again, a proof run inside a pytest run) never waits on its parent.

The gap
    A pytest started any other way (a bare ``pytest`` or ``uv run pytest``
    in a shell, an IDE, a hook) takes no lock and is not seen.

Standard library plus ``scripts/_git.py`` (a linked worktree's directories are
git's answer), so every script imports it before anything else is set up, on
the oldest supported Python too.
"""

from __future__ import annotations

import contextlib
import errno
import os
import stat
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

try:
    import _git
except ModuleNotFoundError:  # imported as ``scripts._locks`` (repo root on path)
    from scripts import _git

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping


class PytestLockError(Exception):
    """The pytest lock file could not be opened or locked for a reason but another holder."""


#: The pytest lock file's name, in the shared checkout's ``.work/``.
PYTEST_LOCK = "pytest.lock"
#: Names the lock a parent holds for its children (module docstring, "Held by a parent").
HELD_ENV = "DSF_PYTEST_LOCK_HELD"
#: Seconds between two tries while another holder has the lock.
POLL_SECONDS = 2.0
_WORK = ".work"


def is_contention(error: OSError) -> bool:
    """Return whether a failed non-blocking lock call failed only because another holder has it.

    POSIX ``flock`` says ``EAGAIN`` / ``EWOULDBLOCK``; ``msvcrt.locking`` says ``EACCES`` or
    ``EDEADLOCK``. Any other error is a real failure, never a reason to wait.
    """
    if sys.platform == "win32":
        return error.errno in {errno.EACCES, errno.EDEADLOCK}
    return error.errno in {errno.EAGAIN, errno.EWOULDBLOCK}


def try_lock(descriptor: int) -> bool:
    """Take an exclusive, non-blocking lock on ``descriptor``; return ``False`` while another holds it.

    Raises:
        OSError: the lock call failed for any reason but contention (:func:`is_contention`).

    """
    try:
        if sys.platform == "win32":
            import msvcrt  # noqa: PLC0415 - Windows only

            msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl  # noqa: PLC0415 - POSIX only

            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        if is_contention(error):
            return False
        raise
    return True


def _real(path: Path, kind: Callable[[int], bool]) -> bool:
    """Return whether ``path`` exists, is no symlink, and is of ``kind``."""
    try:
        return kind(path.lstat().st_mode)
    except OSError:
        return False


def _linked_shared(root: Path) -> Path | None:
    """Return the shared checkout of the linked worktree at ``root``, ``None`` if it is none.

    Its ``.git`` is a real file, git follows it to a git directory
    ``<common>/worktrees/<n>`` (``_git.git_dirs``: it exists and its ``commondir``
    resolves), that directory's ``gitdir`` file points back at this very ``.git`` file, and
    ``<common>`` is a real ``.git`` folder of a checkout. A pointer failing any of this
    (missing, escaping, another worktree's, a symlinked ``.git``) proves nothing.
    """
    dot_git = root / ".git"
    if not _real(dot_git, stat.S_ISREG):
        return None
    dirs = _git.git_dirs(root)
    if dirs is None:
        return None
    git_dir, common = dirs
    if git_dir.parent != common / "worktrees" or common.name != ".git":
        return None
    try:
        back = (git_dir / "gitdir").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    try:  # ``worktree.useRelativePaths`` writes it relative to the git directory
        if not back or not (git_dir / back).samefile(dot_git):
            return None
    except OSError:
        return None
    shared = common.parent
    return shared if _real(common, stat.S_ISDIR) else None


def shared_checkout(root: Path) -> Path:
    """Return the checkout whose ``.work/`` holds the pytest lock of the checkout at ``root``.

    ``root`` is a checkout's root, never a folder inside one. A linked worktree anywhere
    (``.work/worktrees/<name>`` or a harness's) gives its shared checkout when its pointer
    checks out both ways (:func:`_linked_shared`); a clone at
    ``<root>/.work/clones/<name>`` with its own ``.git`` folder gives ``<root>``'s own
    shared checkout when ``<root>`` holds a real ``.git`` (a folder, or the file of a
    linked worktree, whose pointer rule then applies). Any other checkout is its own: one that happens
    to sit under some ``.work`` folder (a scratch repository in a copy's evidence, a test's
    temporary folder), and one whose ``.git`` is a symlink or an unverified pointer.
    """
    resolved = root.resolve()
    linked = _linked_shared(resolved)
    if linked is not None:
        return linked
    folder = resolved.parent
    above = folder.parent.parent
    if (
        folder.name == "clones"
        and folder.parent.name == _WORK
        and _real(resolved / ".git", stat.S_ISDIR)
        and (_real(above / ".git", stat.S_ISDIR) or _real(above / ".git", stat.S_ISREG))
    ):
        # The checkout holding ``.work`` may be a linked worktree itself: its own rule.
        return shared_checkout(above)
    return resolved


def pytest_lock_path(root: Path) -> Path:
    """Return the pytest lock of the checkout at ``root``: its :func:`shared_checkout`'s."""
    return shared_checkout(root) / _WORK / PYTEST_LOCK


def _holder_of(lock: Path) -> str:
    """Return the holder line the lock file holds, or ``unknown``."""
    try:  # Windows: the holder's locked byte cannot be read
        return lock.read_text(encoding="utf-8", errors="replace").strip() or "unknown"
    except OSError:
        return "unknown"


def _acquire(
    descriptor: int,
    lock: Path,
    holder: str,
    *,
    say: Callable[[str], None],
    check: Callable[[], None] | None,
) -> None:
    """Wait for the lock on ``descriptor`` (:func:`hold_pytest`), then write ``holder`` into it.

    Raises:
        PytestLockError: locking or writing failed for a reason but contention.

    """
    said = False
    try:
        while not try_lock(descriptor):
            if not said:
                say(f"waiting for another pytest in this checkout ({_holder_of(lock)})")
                said = True
            if check is not None:
                check()
            time.sleep(POLL_SECONDS)
        os.ftruncate(descriptor, 0)
        _ = os.lseek(descriptor, 0, os.SEEK_SET)
        _ = os.write(descriptor, f"{holder}\n".encode())
    except OSError as error:
        msg = f"cannot take the pytest lock {lock}: {error}"
        raise PytestLockError(msg) from error


@contextlib.contextmanager
def hold_pytest(
    root: Path,
    holder: str,
    *,
    say: Callable[[str], None],
    check: Callable[[], None] | None = None,
    environ: Mapping[str, str] | None = None,
) -> Generator[dict[str, str], None, None]:
    """Hold the pytest lock of the checkout at ``root`` (:func:`pytest_lock_path`) for one pytest run.

    While another holder has it, ``say`` gets one line naming that holder and the lock is
    tried again every :data:`POLL_SECONDS`, ``check`` (when given) called before each wait
    so a stop request ends the wait. Once held, the file holds ``holder``. Yields the
    variables a child is started with (:data:`HELD_ENV`); under ``environ`` (default
    ``os.environ``) whose :data:`HELD_ENV` names this lock a parent holds it, so nothing is
    taken and the same variables are yielded.

    Only taking the lock is wrapped: an error the block itself raises (its command missing,
    say) passes through unchanged.

    Raises:
        PytestLockError: the lock file cannot be opened or locked for a reason but
            contention (the ``OSError`` chained).

    """
    lock = pytest_lock_path(root)
    held = {HELD_ENV: str(lock)}
    inherited = (os.environ if environ is None else environ).get(HELD_ENV, "")
    if inherited and Path(inherited) == lock:
        yield held
        return
    try:
        lock.parent.mkdir(mode=0o700, exist_ok=True)  # two first holders may race to make it
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except OSError as error:
        msg = f"cannot open the pytest lock {lock}: {error}"
        raise PytestLockError(msg) from error
    try:
        _acquire(descriptor, lock, holder, say=say, check=check)
        yield held
    finally:
        os.close(descriptor)
