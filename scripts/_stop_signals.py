"""The stop-signal policy shared by the scripts that run a command and must outlive it.

``scripts/workspace.py`` and ``scripts/prove_failability.py`` each run a
command in a session of its own and stop it on a stop signal instead of
dying under it. This module owns what the two share: which signals ask a run
to stop, how close a repeat must come to count as the same stop delivered
twice, routing those signals to a handler for one run only (a signal the run
inherited as ignored stays ignored), signalling a command's whole process
group, and ending the process by the signal that stopped it. What a repeat
does is each script's own policy: ``workspace.py`` relays it to its command,
``prove_failability.py`` escalates to ``SIGKILL``. ``workspace.py`` also keeps
job control (Ctrl-Z, ``fg``) for a command in a session of its own, a suspend
that lands before the command's group is known included.

Both scripts start their command in the environment ``uv run`` resolves, but
never under ``uv run`` itself (:func:`uv_run_launch`): uv stays alive as its
command's parent and forwards every stop signal it gets, so in a group that is
signalled whole the command would get each stop twice, and pytest abandons a
teardown that a second ``SIGINT`` interrupts.

Standard library only, and no Django import, so either script imports it
before anything else is set up.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import signal
import subprocess
import threading
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Mapping, Sequence
    from pathlib import Path
    from types import FrameType

# The signals that ask a run to stop: Ctrl-C; ``kill``, a parent's ``terminate()`` or a CI
# cancel; a closed terminal; Ctrl-backslash.
STOP_SIGNALS = (
    signal.SIGINT,
    signal.SIGTERM,
    signal.SIGHUP,
    signal.SIGQUIT,
)
# A repeat stop inside this many seconds of the last one acted on is that stop delivered twice:
# ``uv run`` forwards a signal to its child that the child's whole process group already got.
STOP_REPEAT_GRACE = 1.0
# What ``uv run`` runs to report the environment it gives a command, separated by NUL bytes. A
# program, not ``python -c``: an interpreter rewrites ``LC_CTYPE`` in its own environment when
# the locale it inherits is ``C`` (PEP 538), so it would report a variable uv never set.
ENVIRONMENT_REPORT = ("env", "-0")
# The signals that suspend a job: Ctrl-Z; a background job reading from or writing to its
# terminal. A command in a session of its own is an orphaned process group, which the kernel
# never stops on these at their default action (POSIX), so a suspend reaches it as ``SIGSTOP``.
JOB_SIGNALS = (signal.SIGTSTP, signal.SIGTTIN, signal.SIGTTOU)


@contextlib.contextmanager
def routed_to(
    handler: Callable[[int, FrameType | None], None],
    *,
    group: Callable[[], int | None] | None = None,
) -> Generator[_JobControl | None, None, None]:
    """Route :data:`STOP_SIGNALS` to ``handler`` for one block, then put back what was there.

    Only the main thread may call ``signal.signal``. A signal whose
    disposition is ``SIG_IGN`` is left alone: whoever started the run asked
    for it to survive that signal, and a command the run starts inherits the
    same disposition across ``exec``.

    ``group`` names the process group of a command in a session of its own,
    or ``None`` while it has none; with it, the block keeps job control for
    that command (:class:`_JobControl`), under the same ``SIG_IGN`` rule, and
    yields the :class:`_JobControl`, whose :meth:`_JobControl.settle` the
    caller owes once ``group`` names the group. Without it the block yields
    ``None``.
    """
    routes: dict[int, Callable[[int, FrameType | None], None]] = dict.fromkeys(
        STOP_SIGNALS,
        handler,
    )
    jobs = None
    if group is not None:
        jobs = _JobControl(group)
        routes.update(dict.fromkeys(JOB_SIGNALS, jobs.suspend))
        routes[signal.SIGCONT] = jobs.resume
    previous = {
        signum: signal.signal(signum, route)
        for signum, route in routes.items()
        if signal.getsignal(signum) is not signal.SIG_IGN
    }
    try:
        yield jobs
    finally:
        for signum, restored in previous.items():
            _ = signal.signal(signum, signal.SIG_DFL if restored is None else restored)


class _JobControl:
    """Suspend and continue a command's process group along with this process.

    A suspend signal stops the group with ``SIGSTOP`` (:data:`JOB_SIGNALS`),
    then stops this process with the signal received at its default action,
    as the terminal meant; once this process is continued, the group is
    continued too. A ``SIGCONT`` sent to this process alone is passed on to
    the group as well. This process's own group is not orphaned when a shell
    runs it as a job, so it stops; when it is orphaned the kernel discards
    the stop, and the group is continued at once.

    A suspend that lands while the group is not yet known (the command is
    being started) waits in ``pending`` instead of stopping this process
    alone, and :meth:`settle` delivers it once the group is known; a
    ``SIGCONT`` before then drops it, as it would continue that stop.
    """

    def __init__(self, group: Callable[[], int | None]) -> None:
        self.group: Callable[[], int | None] = group
        self.pending: int | None = None

    def suspend(self, signum: int, _frame: FrameType | None) -> None:
        if self.group() is None:
            self.pending = signum
            return
        signal_group_id(self.group(), signal.SIGSTOP)
        _ = signal.signal(signum, signal.SIG_DFL)
        try:
            # Directed at this thread, so it lands before the call returns, never in a pump thread
            # after the handler is back.
            signal.pthread_kill(threading.get_ident(), signum)
        finally:
            _ = signal.signal(signum, self.suspend)
        signal_group_id(self.group(), signal.SIGCONT)

    def resume(self, _signum: int, _frame: FrameType | None) -> None:
        self.pending = None
        signal_group_id(self.group(), signal.SIGCONT)

    def settle(self) -> None:
        """Deliver the suspend that came before the group was known, if any, now that it is."""
        pending, self.pending = self.pending, None
        if pending is not None:
            self.suspend(pending, None)


def signal_group(
    process: subprocess.Popen[str] | subprocess.Popen[bytes] | None,
    signum: int,
) -> None:
    """Send ``signum`` to the whole process group ``process`` leads, while it runs; never raise.

    ``process`` was started with ``start_new_session=True``, so its pid names
    its group. A group already gone raises ``ProcessLookupError``; one whose
    members have all exited but whose leader is not yet reaped raises
    ``PermissionError`` on macOS. Either way nothing is left to signal, and a
    signal handler that raised would unwind from wherever it landed.
    """
    if process is not None and process.returncode is None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signum)


def signal_group_id(pgid: int | None, signum: int) -> None:
    """Send ``signum`` to process group ``pgid``; nothing for ``None``; never raise.

    Unlike :func:`signal_group` it does not ask whether the group's leader
    still runs: what the leader left behind (``sleep 60 &``) is still in the
    group. A group already gone raises ``ProcessLookupError``, one only a
    zombie leads ``PermissionError`` on macOS; either way nothing is left to
    signal.
    """
    if pgid is not None:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(pgid, signum)


def exit_with(code: int) -> NoReturn:
    """End the process with ``code``; a stop's ``128 + N`` ends it by signal ``N`` instead.

    A process that exits with status ``128 + N`` still reads as a normal exit
    to its parent, so a calling shell loop would carry on. Dying by ``N`` with
    its default action is what an unhandled stop signal does, and what the
    parent expects: a shell reports the same ``128 + N``, a ``subprocess``
    parent sees ``-N``.
    """
    if code - 128 in STOP_SIGNALS:
        _ = signal.signal(code - 128, signal.SIG_DFL)
        os.kill(os.getpid(), code - 128)
    raise SystemExit(code)


class LaunchError(Exception):
    """``uv run`` could not resolve the environment, or the command is not in it."""


def uv_run_launch(
    uv_run: Sequence[str],
    command: Sequence[str],
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> tuple[list[str], dict[str, str]]:
    """Return ``command`` and its environment as ``uv_run`` would start it, with no uv between.

    ``uv_run`` is ``uv run`` and its options; it runs, in ``cwd`` with
    ``env`` (default ``os.environ``), :data:`ENVIRONMENT_REPORT` instead of
    ``command``, which syncs the project's environment as ``uv_run command``
    would and reports the environment uv hands its command: ``VIRTUAL_ENV``,
    ``PATH`` with the environment's ``bin`` first, uv's own variables. The
    command's first word is then looked up on that ``PATH``, as uv looks it
    up, so the caller starts the very program ``uv_run command`` would have
    started, with the same ``sys.path``, plugins and settings, as the only
    process between itself and the command's own children. A word holding a
    ``/`` is a path and stays as given; a ``.py`` file runs under the
    environment's ``python``, as uv runs it. A forwarding wrapper the command
    itself starts (``sh -c "uv run ..."``) is the command's own and still
    delivers each stop twice.

    Raises:
        LaunchError: ``uv_run`` failed (the environment could not be synced or
            found), or the command's program is not on the environment's ``PATH``.

    """
    completed = subprocess.run(
        [*uv_run, "--", *ENVIRONMENT_REPORT],
        env=env,
        cwd=cwd,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"{' '.join(uv_run)} found no environment ({completed.returncode}): {detail}"
        raise LaunchError(msg)
    environment: dict[str, str] = {}
    for entry in completed.stdout.split(b"\0"):
        if entry:
            name, _, value = os.fsdecode(entry).partition("=")
            environment[name] = value
    program, *arguments = command
    if program.endswith(".py"):
        program, arguments = "python", [program, *arguments]
    if "/" not in program:
        found = shutil.which(program, path=environment.get("PATH"))
        if found is None:
            msg = f"{program} is not on the PATH {' '.join(uv_run)} gives its command"
            raise LaunchError(msg)
        program = found
    return [program, *arguments], environment
