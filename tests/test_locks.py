"""Script tests for ``scripts/_locks.py``: the shared lock rule and the pytest lock of a checkout.

A copy takes its shared checkout's lock; only contention waits, any other lock
failure is raised; a holder's children inherit the hold; and two processes
holding the lock never overlap. Its two callers (``work.py run`` and
``prove_failability.py``'s scopes) keep their own rows in ``tests/test_work.py``
and ``tests/test_prove_failability.py``. A live ``/graphql/`` request has no
wire shape for a lock, so there is no live sibling in
``examples/fakeshop/test_query/``.
"""

from __future__ import annotations

import errno
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from scripts import _git as _git_runner
from scripts import _locks


def _git(root: Path, *args: str) -> None:
    _ = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=T",
            "-c",
            "user.email=t@example.com",
            *args,
        ],
        check=True,
        capture_output=True,
        env=_git_runner.repository_env(),
    )


def _repo(path: Path) -> Path:
    """Make a git repository with one commit at ``path``."""
    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "commit", "-q", "--allow-empty", "-m", "initial")
    return path


def _lock_of(path: Path) -> Path:
    return path.resolve() / ".work" / _locks.PYTEST_LOCK


def test_a_clone_and_real_linked_worktrees_take_their_shared_checkouts_lock(
    tmp_path: Path,
) -> None:
    shared = _repo(tmp_path / "shared")
    clone = shared / ".work" / "clones" / "fix-x"
    clone.parent.mkdir(parents=True)
    _git(shared, "clone", "-q", str(shared), str(clone))
    inside = shared / ".work" / "worktrees" / "fix-w"
    harness = tmp_path / "harness" / "wt"
    for worktree in (inside, harness):
        _git(shared, "worktree", "add", "-q", "--detach", str(worktree))
    for checkout in (
        shared,
        clone,
        inside,
        harness,
    ):
        assert _locks.pytest_lock_path(checkout) == _lock_of(shared), checkout


def test_a_clone_under_a_linked_worktree_takes_the_worktrees_shared_lock(
    tmp_path: Path,
) -> None:
    """A copy made from a linked worktree's checkout serialises with the shared checkout."""
    shared = _repo(tmp_path / "shared")
    root = tmp_path / "harness" / "wt"
    _git(shared, "worktree", "add", "-q", "--detach", str(root))
    clone = root / ".work" / "clones" / "fix-x"
    clone.parent.mkdir(parents=True)
    _git(root, "clone", "-q", str(root), str(clone))
    assert _locks.pytest_lock_path(clone) == _lock_of(shared)
    spoofed = tmp_path / "spoof"
    _ = _repo(spoofed / ".work" / "clones" / "fix-y")
    _ = (spoofed / ".git").write_text(f"gitdir: {shared / '.git' / 'worktrees' / 'wt'}\n")
    assert _locks.pytest_lock_path(spoofed / ".work" / "clones" / "fix-y") == _lock_of(spoofed)


def test_a_checkout_under_an_unrelated_work_folder_takes_its_own_lock(tmp_path: Path) -> None:
    """A scratch repository in evidence, or a test's temp folder under ``.work``, is no copy."""
    shared = _repo(tmp_path / "shared")
    for scratch in (
        shared / ".work" / "evidence" / "fix-x" / "repo",
        tmp_path / ".work" / "pytest-of-me" / "repo",
        shared / ".work" / "clones" / "fix-x" / "tests",
    ):
        scratch.mkdir(parents=True)
        assert _locks.pytest_lock_path(scratch) == _lock_of(scratch)


def test_a_clone_folder_with_no_git_above_its_work_folder_is_its_own(tmp_path: Path) -> None:
    """``.work/clones/<n>`` whose ``.work`` sits in no checkout, or which has no ``.git``."""
    orphan = _repo(tmp_path / "plain" / ".work" / "clones" / "fix-x")
    assert _locks.pytest_lock_path(orphan) == _lock_of(orphan)
    shared = _repo(tmp_path / "shared")
    bare = shared / ".work" / "clones" / "fix-y"
    bare.mkdir(parents=True)
    assert _locks.pytest_lock_path(bare) == _lock_of(bare)


def test_a_foreign_worktree_in_work_worktrees_takes_its_own_repositorys_lock(
    tmp_path: Path,
) -> None:
    """A worktree of another repository placed in ``.work/worktrees`` is not this checkout's."""
    shared = _repo(tmp_path / "shared")
    other = _repo(tmp_path / "other")
    foreign = shared / ".work" / "worktrees" / "w"
    foreign.parent.mkdir(parents=True)
    _git(other, "worktree", "add", "-q", "--detach", str(foreign))
    assert _locks.pytest_lock_path(foreign) == _lock_of(other)


@pytest.mark.parametrize(
    "spoof",
    [
        "missing",
        "relative-escape",
        "symlink",
        "not-mine",
    ],
)
def test_an_unverified_git_pointer_proves_nothing(tmp_path: Path, spoof: str) -> None:
    """A ``.git`` file is followed only when its target exists and points back at it."""
    shared = _repo(tmp_path / "shared")
    real = tmp_path / "real-wt"
    _git(shared, "worktree", "add", "-q", "--detach", str(real))
    spoofed = shared / ".work" / "worktrees" / "spoof"
    spoofed.mkdir(parents=True)
    dot_git = spoofed / ".git"
    if spoof == "missing":
        _ = dot_git.write_text(f"gitdir: {shared / '.git' / 'worktrees' / 'gone'}\n")
    elif spoof == "relative-escape":
        _ = dot_git.write_text("gitdir: ../../../.git/worktrees/real-wt\n")
    elif spoof == "symlink":
        dot_git.symlink_to(real / ".git")
    else:
        _ = dot_git.write_text(f"gitdir: {shared / '.git' / 'worktrees' / 'real-wt'}\n")
    assert (shared / ".git" / "worktrees" / "real-wt").is_dir()
    assert _locks.pytest_lock_path(spoofed) == _lock_of(spoofed)
    assert _locks.pytest_lock_path(real) == _lock_of(shared)


@pytest.mark.parametrize(
    ("code", "contention"),
    [
        (errno.EAGAIN, True),
        (errno.EWOULDBLOCK, True),
        (errno.ENOLCK, False),
        (errno.EBADF, False),
    ],
)
def test_only_another_holder_is_contention(code: int, *, contention: bool) -> None:
    assert _locks.is_contention(OSError(code, os.strerror(code))) is contention


@pytest.mark.parametrize("stage", ["open", "lock"])
def test_a_failure_taking_the_lock_is_a_pytest_lock_error_and_never_waits(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    def broken(*_args: object) -> int:
        raise OSError(errno.ENOLCK, "no locks available")

    def no_wait(_seconds: float) -> None:
        pytest.fail("a lock failure that is not contention waited")

    monkeypatch.setattr(_locks, "try_lock", broken)
    monkeypatch.setattr(time, "sleep", no_wait)
    if stage == "open":
        monkeypatch.setattr(os, "open", broken)
    with (
        pytest.raises(_locks.PytestLockError, match="no locks available") as raised,
        _locks.hold_pytest(tmp_path, "me", say=print, environ={}),
    ):
        pass
    assert isinstance(raised.value.__cause__, OSError)


def test_an_error_the_block_raises_passes_through_unchanged(tmp_path: Path) -> None:
    """A command the holder runs failing (pytest missing) is never read as the lock failing."""
    missing = FileNotFoundError(errno.ENOENT, "no such program", "pytest")
    with (
        pytest.raises(FileNotFoundError) as raised,
        _locks.hold_pytest(tmp_path, "me", say=print, environ={}),
    ):
        raise missing
    assert raised.value is missing
    descriptor = os.open(_locks.pytest_lock_path(tmp_path), os.O_RDWR)
    try:
        assert _locks.try_lock(descriptor)
    finally:
        os.close(descriptor)


def test_a_held_variable_naming_another_lock_is_no_hold(tmp_path: Path) -> None:
    """Only this checkout's lock is inherited; the lock is then taken and handed down."""
    other = tmp_path / "other" / ".work" / _locks.PYTEST_LOCK
    lines: list[str] = []
    with _locks.hold_pytest(
        tmp_path,
        "me pid 1",
        say=lines.append,
        environ={_locks.HELD_ENV: str(other)},
    ) as held:
        lock = _locks.pytest_lock_path(tmp_path)
        assert held == {_locks.HELD_ENV: str(lock)}
        assert lock.read_text(encoding="utf-8") == "me pid 1\n"
        descriptor = os.open(lock, os.O_RDWR)
        try:
            assert not _locks.try_lock(descriptor)
        finally:
            os.close(descriptor)
    assert lines == []


_HOLDER = """
import sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import _locks
with _locks.hold_pytest(Path(sys.argv[2]), sys.argv[3], say=lambda line: None, environ={}):
    started = time.monotonic()
    time.sleep(0.5)
    ended = time.monotonic()
print(started, ended)
"""


def test_two_holders_never_overlap(tmp_path: Path) -> None:
    """Two proof runs (or runs) started at once: the second starts only after the first ends."""
    scripts = str(Path(_locks.__file__).parent)
    runs = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                _HOLDER,
                scripts,
                str(tmp_path),
                f"run-{index}",
            ],
            stdout=subprocess.PIPE,
            text=True,
        )
        for index in range(2)
    ]
    spans = sorted(tuple(map(float, run.communicate(timeout=60)[0].split())) for run in runs)
    assert all(run.returncode == 0 for run in runs)
    (_first_start, first_end), (second_start, _second_end) = spans
    assert second_start >= first_end
