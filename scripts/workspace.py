"""Hand the REVIEW, HUNT and DRY agentflows disposable workspace copies, so workers only review.

A scratch directory is not a sandbox: a probe there still imports the shared
package and opens the tracked ``examples/fakeshop/db.sqlite3``. Every
measurement, mutation and bench run therefore happens in a copy of the shared
tree with its own virtualenv and its own databases. This script owns all of
that. A worker names one address, ``<flow>/<item>/<role>`` (the item may
itself hold slashes, such as a package path), and never builds, checks or
deletes a copy by hand.

Worker commands
    ``run <address> [--cell default|sharded|pg] [--fresh] -- <command...>``
        Run ``<command>`` inside the address's copy as
        ``uv run --frozen --group pg`` would, in the environment it resolves
        but with no uv between this script and the command (the stop-signal
        paragraph below says why). ``<command>`` is what would follow
        ``uv run``: ``pytest <node> --no-cov``,
        ``python scripts/count_queries.py ...``. Paths inside it resolve
        against the copy. The first run of an address binds it to a copy
        synced from the shared tree as it stands at that moment; later runs
        reuse that copy as it stands, edits included. ``--fresh`` resyncs it
        from the shared tree first. Runs of one address take turns in its
        copy: a run waits while a command runs there, and decides whether to
        sync only once its turn comes, so a run started during the first sync
        reuses what that sync made and every edit since.
    ``prove <address> <manifest> [--cell ...] [--fresh] [-- <extra args>]``
        ``run`` of ``scripts/prove_failability.py`` in its workspace form:
        ``--workspace`` is the copy; ``--scratch-root`` and ``--json`` sit
        under this flow's evidence folder, never inside the copy. An extra
        argument that the proof script's own parser would read as one of
        those three (the exact flag, ``--flag=value`` or any abbreviation it
        accepts) is refused before a copy is bound: the parser keeps the last
        value, so it would move the evidence out of the flow folder, where
        ``gc`` never looks. Every other extra argument passes through. A
        proof killed while its mutation was live (``SIGKILL``) leaves the
        prover's marker, which refuses every later proof in that copy;
        ``--fresh`` resyncs the copy and removes the marker with it.
    ``path <address>``
        Print the copy's directory, binding it first when unbound, so a
        worker can read or edit files there. A copy whose sync has not
        finished is synced first, after any command running in it.
    ``diff <ITEM_BASELINE> [--output FILE | --check FILE] -- <paths...>``
        The item diff: one ``git diff-tree -p --binary`` of the
        ``<ITEM_BASELINE>`` tree (any tree-ish) against the working content
        under ``<paths>``, new files included, in path order. The content is
        read into a private index, so for every file git does not ignore the
        diff is independent of the index: staging, unstaging or ``git rm
        --cached`` never changes a byte (of the index, only whether an ignored
        file is force-added counts), and the shared ``.git/index`` is never
        rewritten. A new file is one the baseline lacks that git tracks or
        does not ignore; a moved file is found as a rename. A file the mirror
        leaves out (``is_excluded``: cycle scratch, a parked ``*-ws`` copy)
        keeps the baseline's blob, so it is never added, edited or deleted. Paths are
        repository-relative. The caller's global and system git config and the
        XDG global ignore and attributes files are ignored (git 2.32 or later,
        which reads ``GIT_CONFIG_GLOBAL``) and the repository's own config is
        honoured (``scripts/_git.py``; a checkout the caller marked
        ``safe.directory`` stays readable), so two copies of one change give
        the same bytes. The last line is ``sha256 <hex>`` of the bytes before
        it. ``--output`` writes it to a file; ``--check``
        recomputes it and exits 1 unless the file holds exactly those bytes.

Worker-0 commands
    ``baseline <flow>/<item>``
        Bind the address ``<flow>/<item>/before`` now and print
        ``ITEM_BASELINE=<sha>``: a commit of that copy as its sync left it,
        made under the copy's lock on the ``HEAD`` read after the sync, so it
        holds exactly what the copy holds (untracked files and
        ``.python-version`` included) whatever landed while the copy waited.
        No ref and no shared index entry moves. That is the one copy that must
        predate the item's first edit.
    ``release <flow>/<item> [--role <role>]... [--keep <role>]...``
        Return the item's copies to the pool; their Postgres databases are
        dropped. ``--keep before`` frees one phase's copies for the next while
        the pinned pre-edit copy stays. A release refuses while a command
        still runs in a copy it would free, and holds each copy until its
        binding is gone. A run still waiting for a copy that a release frees
        refuses when its turn comes, naming the release, if the copy no
        longer holds its address by then; it never binds its address again
        or runs in a copy bound to another address.
    ``audit <record.md>...``
        Resolve every run id a record cites against the run log. For each id
        it prints the address, cell, exit code and package digest, and whether
        the copy had been edited or the shared tree had moved. An id with no
        log entry, or whose package or database lay outside its copy, fails
        the audit. A record that cannot be read as UTF-8 text is a refusal;
        the records audited before it keep their report lines.
    ``gate <flow> [--suites lint,default,floor,sharded,pg]``
        Run the final gate suites in a gate copy that carries a git index, as
        CI's jobs do: the lint job's commands in its order, the full default
        suite (coverage floor), the floor suite, the sharded suite and the
        Postgres database-touching suite. ``--suites`` defaults to ``lint``
        alone: AGENTS.md runs the full suite, the coverage gate and the
        version matrix only in GitHub Actions, so every other suite runs only
        when named on the maintainer's word. The floor suite is CI's floor cell:
        the whole suite, without coverage, in a separate virtualenv at the
        ``requires-python`` floor with ``Django`` and ``strawberry-graphql``
        pinned to their ``[project].dependencies`` lower bounds and every soft
        dependency (``channels[daphne]``, ``cryptography``,
        ``django-debug-toolbar``, ``djangorestframework``) to its
        ``[dependency-groups].dev`` lower bound, installed the way that cell
        installs them. Only executing at the floor catches what the
        floor type check cannot see, such as an annotation a 3.10 import
        evaluates. That virtualenv is reused while its key (the install
        commands and the copy's ``pyproject.toml`` and ``uv.lock``) matches,
        and rebuilt from nothing when it does not. The result is written to
        ``evidence/gate-<run id>.json`` and bound to ``snapshot`` (a commit of
        the gate copy as synced, on its ``head``), the blob ids of
        ``pyproject.toml`` and ``uv.lock``, each suite's cell and the floor
        pins.
    ``status [<flow>]``
        Print copies, bindings, active runs and Postgres leases.
    ``gc <flow>``
        Delete everything the flow holds: copies, gate copy, run log, proof
        scratch, its ``state.json``, the prover's state directory of each copy
        (a killed proof's marker and pristine copies) and its Postgres
        databases; a flow whose folder a reboot removed still loses its state. The Postgres
        container is stopped when this script started it and no database of
        any flow remains. Run it after ``## Outcomes`` records what the
        evidence showed. It refuses while any command of the flow runs, one
        waiting for a copy included; stop that command, or wait for it, then
        run ``gc`` again.

Every run prints a provenance header on stderr before its output and a footer
after it. The header gives the run id, address, copy, the package file the
copy imports and its digest, the cell and the database ``NAME`` of every
alias. It also says whether the copy is ``fresh`` or ``modified`` since its
sync, and whether the shared tree has moved since. Stdout carries only the
command's own output. Every run is appended to ``evidence/runs.jsonl`` and
its full output kept in ``evidence/logs/<run id>.log``. A record cites the run
id; ``audit`` checks it.

Layout: ``$TMPDIR/dsf-ws/<sha16 of the repo root>/<flow>/`` holds
``slots/slot-N/`` (the copies), ``gate/``, ``gate-floor/`` (the floor
suite's virtualenv) and ``evidence/``. The flow's ``state.json`` (bindings
and item baselines) lives in the XDG state home, ``$XDG_STATE_HOME`` or
``~/.local/state`` (the prover's, ``scripts/prove_failability.py::state_home``),
at ``dsf-ws/<sha16 of that workspace folder>/<flow>/state.json``.
Both live outside the repository, keyed per checkout (so a git worktree gets
its own), and are harness-agnostic. ``DSF_WS_ROOT`` replaces
``$TMPDIR/dsf-ws``; a root inside the repository is refused, since copies of
a tree holding its own copies recurse. ``DSF_WS_SLOTS`` caps each flow's pool
(default 4: three parallel roles and the pinned ``before``). New copies are
refused below 6 GB free.

The temporary directory is cleaned behind this script's back. macOS deletes,
daily, every regular file under ``$TMPDIR`` whose creation and last access
are both over three days old, open or locked or not, and keeps every
directory; a read renews the access time only of a file written since it was
last read, so a file ages from its last write however often it is read. On
Linux the directory is ``/tmp``: often a tmpfs that every reboot empties, or
one systemd-tmpfiles cleans of entries unused for about ten days. The state
therefore lives in the state home, which neither touches: an address keeps
its copy's slot number whatever the temporary directory lost, no copy is
renumbered or resynced for another address, and no address gets two copies. A binding whose
copy's manifest is gone (the copy aged out, or a reboot took the flow folder)
is resynced into that same slot on its next run. A copy that lost files but
kept its manifest is used as it stands, and its run log may restart, so
``gc`` the flow before reusing it after an idle stretch. A ``state.json`` an
older version of this script left in the flow folder is moved to the state
home by the next command that takes ``pool.lock``. The flow's marker is a
directory, so ``gc`` still owns the folder after a purge. Every lock is a
directory too, so the purge never takes one from a command that holds it.

Guarantees, each one a hand-run failure this encodes away:

* **Exact copies.** The copy is the shared tree's ``git ls-files -co
  --exclude-standard`` listing plus ``.python-version``; like every git call
  here, the listing reads only the repository's own config and ignore rules,
  never the caller's global or system config or XDG ignore file. Cycle
  scratch is left out: ``output/``, ``docs/shadow/``, ``temp-tests/``,
  ``worker-memory/`` and any ``*-ws`` folder a harness parked in the tree. A
  resync (first bind, rebind to another address, ``--fresh``, a sync that
  never finished) mirrors that set byte for byte, deletes every other file
  except ``.venv`` (caches included), then removes the copy's
  ``scripts/prove_failability.py`` state directory: a killed proof's
  mutation of a file under ``.venv``, which the mirror keeps, is first
  restored from its pristine copy and byte compared, and every other
  mutation is gone with the mirror. A marker that cannot be read, or a file
  that cannot be restored and proved, keeps the state directory with a notice
  on stderr; the resync still completes, and the prover's own refusal keeps
  guarding ``prove`` in that copy until the marker is resolved or ``gc``.
  It then runs ``uv sync --frozen --group pg`` and asserts the copy's
  package digest equals the shared tree's. A shared file that changes
  mid-copy restarts the sync.
* **Copies are reset in place, never cloned.** A virtualenv's entry scripts
  name their own interpreter by absolute path. A cloned ``.venv/bin/pytest``
  would therefore import the other copy's package. Reuse keeps each copy at
  its own path.
* **A missing tool is a refusal.** ``git``, ``uv`` and ``docker`` are each
  looked up on ``PATH`` before the first subprocess that needs them, so one
  that is missing refuses (``<tool> is not on PATH``) before any header,
  never as a traceback.
* **A clean environment.** Every command runs without the caller's
  ``FAKESHOP_*``, ``DJANGO_*``, ``PYTEST_*``, ``COVERAGE_*`` and ``GIT_*``
  variables, ``PYTHONPATH``, ``VIRTUAL_ENV`` and the ``uv`` project
  redirects. An inherited ``DJANGO_STRAWBERRY_KANBAN_DB`` would point the
  copy's ``default`` alias at the tracked database; an inherited
  ``GIT_INDEX_FILE`` would make the copy listing read a private index.
* **Provenance is observed, not asserted.** Before the command runs, a probe
  under the same interpreter, cwd and cell resolves where the package would
  import from and every alias's ``NAME``. The command is refused when the
  package lies outside the copy, a SQLite database lies outside the copy, or
  the Postgres ``NAME`` is not the copy's own database.
* **One Postgres database per copy.** ``--cell pg`` starts the
  ``docker-compose.postgres.yml`` container when no fakeshop container runs.
  A running container is identified by its ``POSTGRES_USER`` and
  ``POSTGRES_DB``, never by port: another project's Postgres may publish the
  same container port. Each copy gets its own database
  ``ws_<repo>_<flow>_<slot>``, so pytest's ``test_<NAME>_gwN`` databases
  never collide across copies, flows or checkouts. The databases themselves
  are the leases every harness sees.
* **Evidence outlives reuse.** The run log, logs and proof scratch sit beside
  the copies, not inside them, so resyncing a copy for the next address keeps
  the evidence the last one produced.
* **Cleanup leaves nothing.** ``release`` unbinds copies and drops their
  databases; a released copy's next binding resyncs it. ``gc`` removes the
  flow folder, the flow's ``state.json`` folder, each copy's prover state
  directory (once that copy is gone, so no copy outlives the marker of a
  mutation it may hold), its databases, and the empty parent folders, in the
  temporary directory and the state home; a removal cut short keeps the
  folder's marker, so
  ``gc`` finishes it on the next run. The state directory is the one the
  prover names (``scripts/prove_failability.py::tree_state_directory``) under
  the state home this script sees, which every command inherits. A crashed
  run's locks last while its command runs and die with it; a crashed sync,
  ``--fresh`` included, resyncs on the address's next run.
* **A copy is settled under its own lock.** A run holds its copy's lock
  from before it decides whether to sync until its command ends, and reads
  its binding and the copy's sync status from ``state.json`` only once it
  holds that lock; a copy is marked ``syncing`` before every sync and
  ``ready`` only once that sync finishes.
* **Cleanup never takes work from a running command.** Every command holds a
  shared lease on its flow from its first touch of the folder to its last:
  an ``flock`` on the flow folder itself, so ``gc`` deletes no lock anyone
  can still open. ``gc`` takes that lease exclusively and keeps it until the
  folder is gone. ``release`` takes each copy's lock and keeps it while it
  unbinds the copy. Locks are taken in one order, flow lease, then copy, then
  ``pool.lock`` (which guards ``state.json``); nothing waits for a copy's
  lock while holding ``pool.lock``. Each lock is an ``flock`` on a
  directory (the flow folder, ``slots/slot-N.lock``, ``pool.lock``,
  ``gate.lock``): the ``$TMPDIR`` purge removes files, never directories, so
  no second command locks a new file at a path whose held one the purge
  removed. A lock file an older version of this script left is replaced by
  its directory under that file's own lock. ``release``, and the check that
  names a copy ``RUNNING``, try a copy's lock under ``pool.lock`` without
  waiting, so no two commands wait on each other and that check never makes
  a ``release`` refuse. The command holds its run's locks too, on the same
  open descriptions, so they last until the command and everything it
  started with them has ended, even when this script was killed first
  (``SIGKILL``); so do a copy's ``uv sync`` and the gate's floor installs. A
  process the command leaves running behind it (``sleep 60 &``) holds them
  as well: the copy reads ``RUNNING`` and ``gc`` and ``release`` refuse
  until it ends. pytest's xdist workers and the prover's scopes are
  started with ``close_fds``, so they never hold them.
* **A stop signal stops the command, then the run.** ``SIGINT``, ``SIGTERM``,
  ``SIGHUP`` and ``SIGQUIT`` to this script (Ctrl-C, ``kill`` or a parent's
  ``terminate()``, a closed terminal, Ctrl-backslash) are relayed to the
  command, which runs in a session of its own, by signalling its whole process
  group: pytest, every xdist worker and whatever they started get it once
  each. The command is started without ``uv run`` around it
  (``scripts/_stop_signals.py::uv_run_launch``), since uv would sit in that
  group and hand the command each stop a second time, ``SIGINT`` about 0.2 s
  later, which aborts a pytest teardown still running; a forwarding wrapper
  the command itself starts (``sh -c "uv run ..."``) still does. ``SIGINT``
  starts pytest's teardown, which is allowed to finish; ``SIGTERM``,
  ``SIGHUP`` and ``SIGQUIT`` end pytest without one, since pytest installs no
  handler for them. The run keeps its locks, its log and its output
  until the command and what it left holding its output have ended, then
  records the run with ``stopped_by`` and ends by that signal. A repeat
  within ``STOP_REPEAT_GRACE`` (one second) of the last relayed stop is the
  same stop delivered twice (``uv run`` forwards a signal its group already
  got) and is dropped; a later one is relayed as received, so a second
  Ctrl-C means what the command makes of it. A signal the run inherited as
  ignored (``nohup``, a background job) stays ignored, for the command too.
* **Ctrl-Z suspends the command with the run.** ``SIGTSTP`` (and ``SIGTTIN``
  / ``SIGTTOU``) to this script stops the command's whole group with
  ``SIGSTOP``, since the kernel never stops a group in a session of its own
  on those, then stops this script; ``fg`` (``SIGCONT``) continues both. One
  that lands while the command is being started waits until it has, then
  stops both.

Exit codes: ``run`` and ``prove`` return the command's own exit code, ``128 + N``
for a command that died by signal ``N``, a reader gone from the output
included: a pipe whose reader exited (``| head``) or a closed terminal, on
stdout, stderr or both. A run stopped by signal ``N``, and a
``gate`` so stopped, makes :func:`main` return ``128 + N``, and a ``128 + N``
for a stop signal ends the process by ``N``. ``125``
means this script refused before the command ran (bad address, full pool,
its copy was released while it waited, wrong provenance, Postgres
unavailable, ``uv`` or ``git`` not on ``PATH``, a ``prove`` extra argument
naming one of its own flags), with the reason on stderr. The other
commands return ``0`` on success and ``1`` on a failed audit, a failed gate
suite, a ``diff --check`` mismatch or a refusal.

POSIX only (``fcntl`` locks). Run from the shared checkout's root as
``uv run python scripts/workspace.py ...``, never from inside a copy.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, BinaryIO, NoReturn, TypedDict, cast, overload

import tomli
from typing_extensions import NotRequired, override

try:
    import _bench_common
    import _git as _git_runner
    import _stop_signals
    import prove_failability
except ModuleNotFoundError:  # imported as ``scripts.workspace`` (repo root on path)
    from scripts import _bench_common, _stop_signals, prove_failability
    from scripts import _git as _git_runner

if TYPE_CHECKING:
    import io
    from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
    from types import FrameType

    from typing_extensions import TypeIs

# ``json.loads`` returns ``Any``; this alias hands callers an ``object`` to narrow.
_loads: Callable[[str], object] = json.loads

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = "django_strawberry_framework"
COMPOSE_FILE = "docker-compose.postgres.yml"

ROOT_ENV = "DSF_WS_ROOT"
SLOTS_ENV = "DSF_WS_SLOTS"
DEFAULT_SLOTS = 4
MIN_FREE_BYTES = 6 * 1024**3
REFUSED = 125
MARKER_NAME = ".dsf-ws"
# The folder under the XDG state home (``prove_failability.py::state_home``) that holds each
# flow's ``state.json``, out of the temporary directory the OS cleans.
STATE_DIRECTORY_NAME = "dsf-ws"
# The signals that ask a run to stop (``scripts/_stop_signals.py``). A run relays each to its
# command and ends only once that has ended.
STOP_SIGNALS = _stop_signals.STOP_SIGNALS
# A repeat inside this many seconds of the last relayed stop is that stop delivered twice, so it
# is not relayed.
STOP_REPEAT_GRACE = _stop_signals.STOP_REPEAT_GRACE

#: Listing entries under these prefixes are cycle output, never tree content.
EXCLUDED_PREFIXES = ("output/", "docs/shadow/")
#: A listing entry with any of these path segments is scratch or a parked copy.
EXCLUDED_SEGMENTS = frozenset(
    {
        "temp-tests",
        "worker-memory",
        "__pycache__",
        ".pytest_cache",
    },
)
#: Gitignored files the copy still needs.
EXTRA_FILES = (".python-version",)
#: Top-level entries a resync keeps in place instead of mirroring.
PRESERVED = frozenset({".venv"})
#: Files a command leaves behind that do not count as editing the copy.
GENERATED_SEGMENTS = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "htmlcov",
    },
)

SCRUBBED_PREFIXES = (
    "FAKESHOP_",
    "DJANGO_",
    "PYTEST_",
    "COVERAGE_",
    "GIT_",
)
SCRUBBED_NAMES = frozenset(
    {
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "VIRTUAL_ENV",
        "CONDA_PREFIX",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PROJECT",
        "UV_WORKING_DIRECTORY",
        "UV_NO_SYNC",
        "UV_FROZEN",
        "UV_LOCKED",
    },
)

CELLS = ("default", "sharded", "pg")
PG_USER = "fakeshop"
PG_PASSWORD = "fakeshop"  # noqa: S105 - the throwaway compose container's documented credential
PG_PORT = "5432/tcp"
COMPOSE_PROJECT = "dsf-ws-postgres"

#: The ``lint`` job of ``.github/workflows/django.yml``, one command per ``run:`` line and in
#: its order, each without its ``uv run`` prefix. A package change that passes every pytest
#: suite still reddens CI through a stale generated doc or a layout rewrite, so the gate runs
#: these too; ``tests/test_workspace.py`` holds this list to the workflow.
LINT_COMMANDS = (
    "ruff check .",
    "ruff format --check .",
    "basedpyright",
    "basedpyright -p pyrightconfig.floor.json",
    "python scripts/check_type_suppressions.py",
    "python scripts/check_public_types.py",
    "python scripts/check_trailing_commas.py --check",
    "python scripts/check_truthful_reads.py --check",
    "python scripts/check_citations.py --check --substrings",
    "python scripts/build_kanban_tracked_path_constants.py --check",
    "python scripts/check_kanban_anchors.py",
    "python examples/fakeshop/manage.py import_spec_terms --check --skip-checks",
    "python scripts/check_all_spec_glossaries.py",
    "python scripts/build_kanban_md.py --check",
    "python scripts/build_kanban_html.py --check",
    "python scripts/build_glossary_md.py --check",
    "python scripts/build_tree_md.py --check",
)

#: The suite that runs in the floor virtualenv instead of the gate copy's own ``.venv``.
FLOOR_SUITE = "floor"
#: The ``[project].dependencies`` CI's floor cell pins to their ``>=`` lower bound, in the
#: order that cell installs them; BUILD.md "Floor verification" states the same points.
FLOOR_PACKAGES = ("Django", "strawberry-graphql")
#: The soft dependencies (``[dependency-groups].dev`` rows, never in ``[project].dependencies``)
#: CI's floor cell pins to their ``>=`` lower bound in one install after ``FLOOR_PACKAGES``,
#: each spelled with the extras its dev row declares, in the order that install names them.
SOFT_FLOOR_PACKAGES = (
    "channels[daphne]",
    "cryptography",
    "django-debug-toolbar",
    "djangorestframework",
)
#: Written into the floor virtualenv once its build succeeds; a mismatch rebuilds it.
FLOOR_KEY_NAME = "dsf-floor-key"
REQUIREMENT_PATTERN = re.compile(
    r"^\s*(?P<name>[A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[(?P<extras>[^\]]*)\])?\s*(?P<specifier>[^;]*)",
)

#: Each gate suite: the command after ``uv run`` (after ``python -m`` in the floor
#: virtualenv for ``floor``) and the cell it runs in (REVIEW.md "Final gate"). ``sh -ex``
#: stops the lint suite at the first failing command and echoes each one. ``floor`` is the
#: ``test`` job's compatibility node in ``.github/workflows/django.yml``, whose ``addopts``
#: drop ``--cov``; ``tests/test_workspace.py`` holds it to the workflow.
GATE_SUITES: dict[str, tuple[tuple[str, ...], str]] = {
    "lint": (("sh", "-exc", "\n".join(LINT_COMMANDS)), "default"),
    "default": (("pytest",), "default"),
    FLOOR_SUITE: (
        (
            "pytest",
            "-p",
            "no:cacheprovider",
            "-o",
            "addopts=-v -n auto --dist loadscope --durations=25",
        ),
        "default",
    ),
    "sharded": (("pytest", "-o", "addopts=-v -n auto --dist loadscope"), "sharded"),
    "pg": (
        (
            "pytest",
            "-o",
            "addopts=-v -n 12 --dist loadscope",
            "-m",
            "django_db or pg",
        ),
        "pg",
    ),
}

#: The one gate suite a bare ``gate`` runs: AGENTS.md keeps the full suite, the coverage gate
#: and the version matrix in GitHub Actions (the dispatched ``django.yml`` matrix and
#: ``postgres.yml``), so only CI's lint job runs locally unless ``--suites`` names more.
LOCAL_GATE_SUITE = "lint"

FLOW_PATTERN = re.compile(r"^[a-z][a-z0-9]{0,15}$")
SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_@+][A-Za-z0-9._@+-]*$")
RUN_ID_PATTERN = re.compile(r"\b([a-z][a-z0-9]{0,15})-(\d{8}T\d{6})-([0-9a-f]{6})\b")
SUMMARY_PATTERN = re.compile(r"^=+ (?P<summary>.+ in [\d.]+s(?: \([^)]*\))?) =+$")
COLLECTED_PATTERN = re.compile(r"\[(\d+) items?\]|collected (\d+) items?")

PROBE = """
import importlib, importlib.util, json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), "examples", "fakeshop"))
spec = importlib.util.find_spec("django_strawberry_framework")
settings = importlib.import_module("config.test_settings")
print(json.dumps({
    "executable": sys.executable,
    "package_file": spec.origin if spec else None,
    "databases": {
        alias: {"ENGINE": conf.get("ENGINE", ""), "NAME": str(conf.get("NAME", ""))}
        for alias, conf in settings.DATABASES.items()
    },
}))
"""


class WorkspaceError(Exception):
    """A refusal: the command never ran, and the message says why."""


class LockBusyError(WorkspaceError):
    """A copy's lock is held: a command is still running in it."""


# --------------------------------------------------------------------------------------------
# Addresses
# --------------------------------------------------------------------------------------------


def _check_flow(flow: str, text: str) -> None:
    if not FLOW_PATTERN.fullmatch(flow):
        msg = f"{text!r}: flow {flow!r} must be lowercase letters and digits, at most 16"
        raise WorkspaceError(msg)


def _check_segments(segments: Sequence[str], text: str) -> None:
    for segment in segments:
        if not SEGMENT_PATTERN.fullmatch(segment) or segment in {".", ".."}:
            msg = f"{text!r}: segment {segment!r} is not a plain name"
            raise WorkspaceError(msg)


@dataclasses.dataclass(frozen=True)
class ItemRef:
    """``<flow>/<item>``; the item may hold slashes."""

    flow: str
    item: str

    @classmethod
    def parse(cls, text: str) -> ItemRef:
        """Parse ``<flow>/<item>``."""
        parts = text.strip("/").split("/")
        if len(parts) < 2:  # flow + at least one item segment
            msg = f"{text!r}: expected <flow>/<item>"
            raise WorkspaceError(msg)
        _check_flow(parts[0], text)
        _check_segments(parts[1:], text)
        return cls(parts[0], "/".join(parts[1:]))


@dataclasses.dataclass(frozen=True)
class Address:
    """``<flow>/<item>/<role>``: the first segment is the flow, the last the role."""

    flow: str
    item: str
    role: str

    @classmethod
    def parse(cls, text: str) -> Address:
        """Parse ``<flow>/<item>/<role>``."""
        parts = text.strip("/").split("/")
        if len(parts) < 3:  # flow + item + role
            msg = f"{text!r}: expected <flow>/<item>/<role>"
            raise WorkspaceError(msg)
        _check_flow(parts[0], text)
        _check_segments(parts[1:], text)
        return cls(parts[0], "/".join(parts[1:-1]), parts[-1])

    @override
    def __str__(self) -> str:
        """Return the address as ``<flow>/<item>/<role>``."""
        return f"{self.flow}/{self.item}/{self.role}"

    @property
    def evidence_slug(self) -> str:
        """Return a one-segment folder name for this address's item."""
        return self.item.replace("/", "__")


# --------------------------------------------------------------------------------------------
# Environment, git, locks
# --------------------------------------------------------------------------------------------


def clean_env(base: dict[str, str] | None = None, **extra: str) -> dict[str, str]:
    """Return ``base`` (default ``os.environ``) without every redirecting variable, plus ``extra``."""
    source = os.environ if base is None else base
    env = {
        name: value
        for name, value in source.items()
        if name not in SCRUBBED_NAMES and not name.startswith(SCRUBBED_PREFIXES)
    }
    env.update(extra)
    return env


# ``commit-tree`` needs an identity the isolated config no longer supplies.
SCRATCH_IDENTITY: Mapping[str, str] = MappingProxyType(
    {
        "GIT_AUTHOR_NAME": "workspace",
        "GIT_AUTHOR_EMAIL": "workspace@localhost",
        "GIT_COMMITTER_NAME": "workspace",
        "GIT_COMMITTER_EMAIL": "workspace@localhost",
    },
)


def require_on_path(tool: str, consequence: str) -> None:
    """Refuse, before any subprocess starts it, a ``tool`` that is not on ``PATH``.

    Every command runs under :func:`clean_env`, which keeps the caller's
    ``PATH``, so the lookup reads the ``PATH`` the subprocess would search.

    Raises:
        WorkspaceError: ``tool`` is not on ``PATH``; ``consequence`` says what cannot run.

    """
    if shutil.which(tool) is None:
        msg = f"{tool} is not on PATH, so {consequence}"
        raise WorkspaceError(msg)


def _git(
    repo_root: Path,
    *args: str,
    env: Mapping[str, str] | None = None,
    stdin: bytes | None = None,
) -> str:
    """Run ``git -C repo_root args`` in :func:`clean_env` made repository-only; return its stdout.

    The repository-only layer is ``scripts/_git.py::repository_env``: the caller's global and
    system config and XDG ignore and attributes files never reach a result, a ``status`` never
    rewrites the index, and the caller's ``safe.directory`` trust is kept. ``env`` adds
    variables on top (a private ``GIT_INDEX_FILE``, an identity); ``stdin`` feeds the command
    (``update-index -z --stdin``).
    """
    require_on_path("git", "the shared tree cannot be listed, copied or diffed")
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            *args,
        ],
        capture_output=True,
        input=stdin,
        env=_git_runner.repository_env(clean_env(), **dict(env or {})),
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"git {' '.join(args)} failed ({completed.returncode}): {detail}"
        raise WorkspaceError(msg)
    return completed.stdout.decode("utf-8", "surrogateescape")


def snapshot_commit(
    repo_root: Path,
    copy: Path,
    manifest: _Manifest,
    parent: str,
    preserved: frozenset[str] = PRESERVED,
) -> str:
    """Return a commit of ``copy`` as it holds the mirrored files now, on ``parent``.

    Call it with the copy's lock held and the manifest of the sync just made: the sha then names
    the copy a command runs in, not the shared tree as it stood before the copy waited for its
    lock. The tree is ``parent``'s with every mirrored file replaced by the copy's content and
    every ``parent`` file the copy lacks dropped, built through a private index; no ref and no
    shared index entry moves. A file the mirror leaves out (:func:`is_excluded`) keeps
    ``parent``'s blob.

    Raises:
        WorkspaceError: a mirrored file changed in the copy since the sync.

    """
    listing = _git(repo_root, "ls-tree", "-r", "-z", "--name-only", parent)
    held = [name for name in _null_separated(listing) if not is_excluded(name)]
    names = {*manifest["entries"], *held}
    tree = content_tree(repo_root, parent, names=names, work_tree=copy)
    if edited := copy_edits(copy, manifest, preserved):
        msg = f"{copy} changed while it was snapshotted: {edited[:5]}"
        raise WorkspaceError(msg)
    return _git(
        repo_root,
        "commit-tree",
        tree,
        "-p",
        parent,
        "-m",
        f"workspace snapshot of {copy.name}",
        env=SCRATCH_IDENTITY,
    ).strip()


def _null_separated(listing: str) -> list[str]:
    return [name for name in listing.split("\0") if name]


def _stdin_names(names: Iterable[str]) -> bytes:
    return "".join(f"{name}\0" for name in names).encode("utf-8", "surrogateescape")


@contextlib.contextmanager
def content_index(
    repo_root: Path,
    base: str,
    pathspecs: Sequence[str] = (),
    *,
    names: Iterable[str] | None = None,
    work_tree: Path | None = None,
    excluded: Callable[[str], bool] | None = None,
) -> Generator[dict[str, str], None, None]:
    """Yield the environment of a private index: ``base`` overlaid with the working content.

    The index lives in a temporary directory, so the shared ``.git/index`` is neither used for
    its stat data nor rewritten, and what the private one holds is a function of ``base`` and
    the files on disk. ``base`` is any tree-ish. ``names`` (default: every ``base`` entry under
    ``pathspecs``, every path when empty, plus every file there that the shared index tracks or
    git does not ignore, a read-only listing that keeps a force-added ignored file, less every
    name ``excluded`` reports) are refreshed from ``work_tree`` (default ``repo_root``); one
    that is no longer a file or link there is dropped. A default name ``excluded`` reports
    keeps its ``base`` entry, or stays absent; explicit ``names`` are never filtered. A file
    ``base`` holds that is now a directory, and the reverse, both resolve; a link to a
    directory stays a link, and a nested repository the shared index tracks stays a gitlink at
    its checked-out commit. By default, a file a sparse checkout leaves out of the work tree
    keeps its ``base`` entry.
    """
    with tempfile.TemporaryDirectory(prefix="dsf-index-") as scratch:
        env = {"GIT_INDEX_FILE": str(Path(scratch) / "index")}
        if work_tree is not None:
            env["GIT_WORK_TREE"] = str(work_tree)
        _ = _git(repo_root, "read-tree", base, env=env)
        root = repo_root if work_tree is None else work_tree
        if names is None:
            held = _git(repo_root, "ls-files", "-z", "-c", "--", *pathspecs, env=env)
            live = _git(
                repo_root,
                "ls-files",
                "-z",
                "-c",
                "-o",
                "--exclude-standard",
                "--",
                *pathspecs,
            )
            # ``-o`` lists an untracked nested repository as ``name/``: it stays out, as git
            # leaves it out of ``git add -A``.
            names = {
                *_null_separated(held),
                *(name for name in _null_separated(live) if not name.endswith("/")),
            }
            # A sparse checkout's skip-worktree entries are absent by design, never deleted.
            tagged = _git(repo_root, "ls-files", "-z", "-t", "--", *pathspecs)
            names -= {
                entry[2:]
                for entry in _null_separated(tagged)
                if entry.startswith("S ") and not os.path.lexists(root / entry[2:])
            }
            if excluded is not None:
                names = {name for name in names if not excluded(name)}
        present: list[str] = []
        gone: list[str] = []
        for name in sorted(names):
            path = root / name
            # A link is a file to git, and a directory holding ``.git`` is a gitlink.
            is_entry = os.path.lexists(path) and (
                path.is_symlink() or not path.is_dir() or (path / ".git").exists()
            )
            (present if is_entry else gone).append(name)
        for flags, group in (("--force-remove", gone), ("--add", present)):
            if group:
                _ = _git(
                    repo_root,
                    "update-index",
                    "-z",
                    flags,
                    "--replace",
                    "--stdin",
                    env=env,
                    stdin=_stdin_names(group),
                )
        yield env


def content_tree(
    repo_root: Path,
    base: str,
    pathspecs: Sequence[str] = (),
    *,
    names: Iterable[str] | None = None,
    work_tree: Path | None = None,
    excluded: Callable[[str], bool] | None = None,
) -> str:
    """Return the tree id of ``base`` overlaid with the working content (see :func:`content_index`).

    The tree is written to the repository's object store, so it outlives the private index.
    """
    with content_index(
        repo_root,
        base,
        pathspecs,
        names=names,
        work_tree=work_tree,
        excluded=excluded,
    ) as env:
        return _git(repo_root, "write-tree", env=env).strip()


def item_diff(repo_root: Path, baseline: str, paths: Sequence[str]) -> bytes:
    """Return an item's diff since ``baseline`` under ``paths``, ending ``sha256 <hex>``.

    One ``git diff-tree -p --binary`` of the ``baseline`` tree against :func:`content_tree`'s tree
    of the working content under ``paths``, new files included, in path order. A file the mirror
    leaves out (:func:`is_excluded`) keeps ``baseline``'s blob, the rule :func:`snapshot_commit`
    applies, so cycle scratch or a parked copy is never the item's addition, edit or deletion.
    Renames and deletions are found by content, and for every file git does not ignore the diff is
    independent of the index: neither staging, unstaging nor ``git rm --cached`` moves a byte (only
    whether an ignored file is force-added counts), and the shared ``.git/index`` is never written.
    Paths are repository-relative, :func:`_git` keeps the caller's global and system config out,
    and the flags fix colour, prefixes, rename detection and the external diff and textconv drivers
    whatever the repository's config says, so two copies of one change give the same bytes.
    """
    if not paths:
        msg = "diff needs at least one path after --"
        raise WorkspaceError(msg)
    tree = content_tree(repo_root, baseline, paths, excluded=is_excluded)
    text = _git(
        repo_root,
        "diff-tree",
        "-r",
        "-p",
        "--binary",
        "--no-color",
        "--no-ext-diff",
        "--no-textconv",
        "--find-renames",
        "--src-prefix=a/",
        "--dst-prefix=b/",
        baseline,
        tree,
        "--",
        *paths,
    )
    body = text.encode("utf-8", "surrogateescape")
    return body + f"sha256 {hashlib.sha256(body).hexdigest()}\n".encode("ascii")


def _still_names(path: Path, descriptor: int) -> bool:
    """Return whether ``path`` still names the file or directory ``descriptor`` holds open."""
    try:
        return os.path.samestat(os.fstat(descriptor), path.stat())
    except FileNotFoundError:
        return False


def _flock(path: Path, flags: int, operation: int) -> int:
    """Lock what ``path`` names and return the descriptor holding it.

    A file or directory removed or replaced while this call waited on it is
    opened again, so a holder always sits on what the path names now, never
    on an inode the path no longer reaches.

    Raises:
        BlockingIOError: ``operation`` carries ``LOCK_NB`` and another
            descriptor holds a conflicting lock.
        FileNotFoundError: ``path`` is missing and ``flags`` cannot create it.
        NotADirectoryError: ``flags`` carries ``O_DIRECTORY`` and ``path``
            names a file.

    """
    while True:
        descriptor = os.open(path, flags, 0o644)
        try:
            fcntl.flock(descriptor, operation)
        except BaseException:
            os.close(descriptor)
            raise
        if _still_names(path, descriptor):
            return descriptor
        os.close(descriptor)


def _replace_lock_file(path: Path, operation: int) -> None:
    """Replace a lock file an older version of this script left at ``path`` with its directory.

    The file is locked first, with ``operation``, so a command still holding
    it keeps it until it ends; the directory takes its place before that lock
    is let go. A command of the older version waiting on the file then finds
    the path naming a directory and fails, never holding a second lock beside
    the directory's holder.

    Raises:
        BlockingIOError: ``operation`` carries ``LOCK_NB`` and the file is held.

    """
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except FileNotFoundError:
        return
    try:
        fcntl.flock(descriptor, operation)
        if _still_names(path, descriptor) and stat.S_ISREG(os.fstat(descriptor).st_mode):
            path.unlink()
            # A command of either version may make the path again first.
            with contextlib.suppress(FileExistsError):
                path.mkdir()
    finally:
        os.close(descriptor)


def _lock_directory(path: Path, operation: int, *, create: bool) -> int:
    """Lock the directory ``path``; return the descriptor holding it.

    ``create`` makes the directory. A lock file found at ``path`` is replaced
    by the directory (:func:`_replace_lock_file`) with or without ``create``:
    that replaces a lock, it never brings back one ``gc`` removed.

    Raises:
        BlockingIOError: ``operation`` carries ``LOCK_NB`` and the lock is held.
        FileNotFoundError: ``path`` is missing and ``create`` is false.

    """
    while True:
        try:
            return _flock(path, os.O_RDONLY | os.O_DIRECTORY, operation)
        except NotADirectoryError:
            _replace_lock_file(path, operation)
        except FileNotFoundError:
            if not create:
                raise
            # A file an older version made here is replaced on the next pass.
            with contextlib.suppress(FileExistsError):
                path.mkdir()


@contextlib.contextmanager
def file_lock(
    path: Path,
    *,
    blocking: bool = True,
    create: bool = True,
) -> Generator[int, None, None]:
    """Hold an exclusive ``flock`` on the lock ``path``; yield the descriptor holding it.

    The lock is an empty directory, never a file: the macOS ``$TMPDIR`` purge
    deletes a file it finds old enough even while a command holds it, and a
    later command would then lock a new file at the same path beside that
    holder; it never deletes a directory. A lock file an older version of
    this script left is replaced by the directory under that file's own lock.

    The kernel drops the lock once every descriptor sharing it is closed: when
    this block ends and no command it was handed to (:func:`stream`) runs.

    ``create`` makes the lock, and its folder, but never the folder above:
    only :func:`flow_lease` creates a flow folder, so a lock taken after
    ``gc`` removed one raises instead of bringing it back. Without ``create``
    a missing lock raises ``FileNotFoundError``.
    """
    if create:
        path.parent.mkdir(exist_ok=True)
    try:
        descriptor = _lock_directory(
            path,
            fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB),
            create=create,
        )
    except BlockingIOError:
        msg = f"{path} is held: a command is still running there"
        raise LockBusyError(msg) from None
    try:
        yield descriptor
    finally:
        os.close(descriptor)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def new_run_id(flow: str) -> str:
    """Return ``<flow>-<UTC timestamp>-<6 hex>``, the id a record cites."""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    return f"{flow}-{stamp}-{secrets.token_hex(3)}"


def _is_within(path: Path, root: Path) -> bool:
    return path.resolve().is_relative_to(root.resolve())


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    _ = temporary.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _ = temporary.replace(path)


def _is_json_object(value: object) -> TypeIs[dict[str, object]]:
    """Return whether a decoded JSON value is an object (JSON object keys are always strings)."""
    return isinstance(value, dict)


def _is_json_array(value: object) -> TypeIs[list[object]]:
    """Return whether a decoded JSON value is an array."""
    return isinstance(value, list)


def _object_field(document: Mapping[str, object], key: str) -> dict[str, object]:
    """Return the JSON object ``document`` holds under ``key``, or an empty one."""
    value = document.get(key)
    return value if _is_json_object(value) else {}


def _array_field(document: Mapping[str, object], key: str) -> list[object]:
    """Return the JSON array ``document`` holds under ``key``, or an empty one."""
    value = document.get(key)
    return value if _is_json_array(value) else []


def _read_text_if_present(path: Path) -> str | None:
    """Return the text of ``path``, or ``None`` when no file is there as it is read.

    The read is the existence check: a file a ``gc`` or the ``$TMPDIR`` purge
    removes after a separate check would raise instead.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None


@overload
def _read_json_object(path: Path, default: Mapping[str, object]) -> Mapping[str, object]: ...


@overload
def _read_json_object(path: Path, default: None) -> Mapping[str, object] | None: ...


def _read_json_object(
    path: Path,
    default: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    """Return the JSON object this script wrote at ``path``, or ``default`` when it is absent.

    A file removed while this runs reads as absent.
    """
    text = _read_text_if_present(path)
    if text is None:
        return default
    document = _loads(text)
    if not _is_json_object(document):
        msg = f"{path} holds a JSON {type(document).__name__}, not the object this script writes"
        raise WorkspaceError(msg)
    return document


# --------------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------------


def repo_key(repo_root: Path) -> str:
    """Return the 16-hex key that separates one checkout's workspaces from another's."""
    return hashlib.sha256(str(repo_root.resolve()).encode("utf-8")).hexdigest()[:16]


def check_shared_checkout(repo_root: Path) -> None:
    """Refuse a root that is a workspace copy rather than the shared checkout."""
    for parent in (repo_root, *repo_root.parents):
        if (parent / MARKER_NAME).exists():
            msg = f"{repo_root} is inside a workspace folder; run this from the shared checkout"
            raise WorkspaceError(msg)
    if not (repo_root / ".git").exists():
        msg = f"{repo_root} has no .git; run this from the shared checkout, not a copy"
        raise WorkspaceError(msg)


def workspace_base(repo_root: Path, environ: dict[str, str] | None = None) -> Path:
    """Return ``<root>/<repo key>``, refusing any root inside the repository."""
    source = os.environ if environ is None else environ
    raw = source.get(ROOT_ENV)
    parent = Path(raw).expanduser() if raw else Path(tempfile.gettempdir()) / "dsf-ws"
    base = parent.resolve() / repo_key(repo_root)
    if _is_within(base, repo_root):
        msg = (
            f"workspace root {base} is inside the repository {repo_root}; copies of a tree "
            f"that holds its own copies recurse. Point {ROOT_ENV} outside it."
        )
        raise WorkspaceError(msg)
    return base


def state_root(base: Path) -> Path:
    """Return the folder under the XDG state home that holds the flows' state of ``base``.

    It is ``<state home>/dsf-ws/<sha16 of base>``, ``base`` being the
    checkout's workspace folder (:func:`workspace_base`), so two checkouts, or
    two ``DSF_WS_ROOT`` folders of one checkout, never share a flow's state.
    The state home is the prover's (:func:`prove_failability.state_home`), read
    from this process's environment.
    """
    return prove_failability.state_home().resolve() / STATE_DIRECTORY_NAME / repo_key(base)


def pool_size(environ: dict[str, str] | None = None) -> int:
    """Return the per-flow copy cap from ``DSF_WS_SLOTS`` (default 4)."""
    raw = (os.environ if environ is None else environ).get(SLOTS_ENV, "")
    if not raw:
        return DEFAULT_SLOTS
    if not raw.isdigit() or int(raw) < 1:
        msg = f"{SLOTS_ENV}={raw!r} must be a positive integer"
        raise WorkspaceError(msg)
    return int(raw)


@dataclasses.dataclass(frozen=True)
class Layout:
    """Where one flow's copies, locks, state and evidence live."""

    repo_root: Path
    base: Path
    flow: str

    @classmethod
    def for_flow(cls, flow: str, repo_root: Path = REPO_ROOT) -> Layout:
        """Return the layout for ``flow`` under this checkout's workspace root."""
        _check_flow(flow, flow)
        return cls(repo_root, workspace_base(repo_root), flow)

    @property
    def flow_dir(self) -> Path:
        """The flow's folder under the workspace root; ``gc`` removes it and :attr:`state_dir`."""
        return self.base / self.flow

    @property
    def state_dir(self) -> Path:
        """The flow's folder under the XDG state home, holding :attr:`state_path` alone."""
        return state_root(self.base) / self.flow

    @property
    def state_path(self) -> Path:
        """Bindings and item baselines, out of the temporary directory the OS cleans."""
        return self.state_dir / "state.json"

    @property
    def legacy_state_path(self) -> Path:
        """Where an older version of this script kept :attr:`state_path`, in the flow folder."""
        return self.flow_dir / "state.json"

    @property
    def pool_lock(self) -> Path:
        """Guards ``state.json`` and the upgrade of a marker file to the marker directory.

        A directory, as every lock :func:`file_lock` takes is.
        """
        return self.flow_dir / "pool.lock"

    @property
    def evidence(self) -> Path:
        """Run log, per-run logs, proof scratch and gate results."""
        return self.flow_dir / "evidence"

    @property
    def run_log(self) -> Path:
        """One JSON line per run."""
        return self.evidence / "runs.jsonl"

    @property
    def gate_dir(self) -> Path:
        """The gate copy, outside the pool."""
        return self.flow_dir / "gate"

    @property
    def floor_venv(self) -> Path:
        """The floor suite's virtualenv, beside the gate copy so a resync never mirrors it."""
        return self.flow_dir / "gate-floor"

    def slot_dir(self, slot: str) -> Path:
        """Return one copy's directory."""
        return self.flow_dir / "slots" / slot

    def slot_lock(self, slot: str) -> Path:
        """Return the lock a run holds on its copy, a directory beside it (:func:`file_lock`)."""
        return self.flow_dir / "slots" / f"{slot}.lock"

    def manifest_path(self, slot: str) -> Path:
        """Return the record of what the copy was last synced to."""
        return self.flow_dir / "slots" / f"{slot}.manifest.json"

    def db_name(self, slot: str) -> str:
        """Return the copy's own Postgres database name."""
        return f"ws_{repo_key(self.repo_root)[:12]}_{self.flow}_{slot.replace('-', '')}"

    @property
    def db_prefix(self) -> str:
        """Every database this flow owns starts with this (after an optional ``test_``)."""
        return f"ws_{repo_key(self.repo_root)[:12]}_{self.flow}_"

    def ensure_marked(self) -> None:
        """Create the flow folder with the marker that lets ``gc`` prove it owns it.

        The marker is an empty directory, since the macOS ``$TMPDIR`` purge
        deletes files and keeps every directory, so the proof outlives an idle
        stretch. A marker file is replaced by the directory under
        ``pool.lock``, so two commands upgrading it at once never collide.
        """
        self.flow_dir.mkdir(parents=True, exist_ok=True)
        marker = self.flow_dir / MARKER_NAME
        if marker.is_dir():
            return
        with file_lock(self.pool_lock):
            if not marker.is_dir():
                marker.unlink(missing_ok=True)
                marker.mkdir()


def _make_flow_dir(flow_dir: Path) -> None:
    """Create the flow folder and its parents, again while a ``gc`` removes the empty parents.

    A ``gc`` of another flow of this checkout removes the parents it finds
    empty; a ``mkdir`` racing that removal fails with ``ENOENT``, or on macOS
    ``EINVAL``, or finds the folder gone right after ``EEXIST``.
    """
    while True:
        try:
            flow_dir.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            if os.path.lexists(flow_dir):
                raise
        except OSError as error:
            if error.errno not in {errno.ENOENT, errno.EINVAL}:
                raise
        else:
            return


def _lock_flow_dir(layout: Layout, operation: int, *, create: bool) -> int | None:
    """Lock the flow folder itself; return the descriptor, or ``None`` when there is none.

    ``create`` makes the folder first, again if a ``gc`` removed it while this
    call waited.

    Raises:
        BlockingIOError: ``operation`` carries ``LOCK_NB`` and the lock is held.

    """
    while True:
        if create:
            _make_flow_dir(layout.flow_dir)
        try:
            return _flock(layout.flow_dir, os.O_RDONLY | os.O_DIRECTORY, operation)
        except FileNotFoundError:
            if not create:
                return None


@dataclasses.dataclass(frozen=True)
class FlowLease:
    """A held flow lease: whether the flow is marked, and the descriptor holding the lease.

    ``holding`` is that descriptor for a command that must hold the lease too
    (:func:`stream`); empty when the flow folder does not exist, so no lease
    is held.
    """

    marked: bool
    holding: tuple[int, ...]


@contextlib.contextmanager
def flow_lease(layout: Layout, *, create: bool = True) -> Generator[FlowLease, None, None]:
    """Hold a shared lease on the flow for a whole command; yield it and whether the flow is marked.

    The lease is an ``flock`` on the flow folder itself, so no lock file sits
    in what ``gc`` removes. ``gc`` takes it exclusively and keeps it until the
    folder is gone; a command that waited out a ``gc`` finds the path naming a
    new folder, or none, and locks that. ``create`` makes and marks the
    folder; without it nothing is created and an absent folder yields
    ``False``.
    """
    descriptor = _lock_flow_dir(layout, fcntl.LOCK_SH, create=create)
    if descriptor is None:
        yield FlowLease(marked=False, holding=())
        return
    try:
        if create:
            layout.ensure_marked()
        yield FlowLease(marked=(layout.flow_dir / MARKER_NAME).exists(), holding=(descriptor,))
    finally:
        os.close(descriptor)


# --------------------------------------------------------------------------------------------
# Mirroring the shared tree
# --------------------------------------------------------------------------------------------


def is_excluded(name: str) -> bool:
    """Report whether a listing entry is cycle scratch or a parked copy, not tree content."""
    if name.startswith(EXCLUDED_PREFIXES):
        return True
    parts = name.split("/")
    return any(part in EXCLUDED_SEGMENTS or part.endswith("-ws") for part in parts[:-1])


def wanted_files(repo_root: Path) -> dict[str, Path]:
    """Return ``{relative name: path}`` for every file a copy must hold.

    Raises:
        WorkspaceError: the listing does not include the package's
            ``__init__.py``, so it enumerated something other than this tree.

    """
    listing = _git(repo_root, "ls-files", "-z", "-co", "--exclude-standard")
    names = {name for name in listing.split("\0") if name}
    names.update(name for name in EXTRA_FILES if os.path.lexists(repo_root / name))
    result: dict[str, Path] = {}
    for name in sorted(names):
        path = repo_root / name
        if is_excluded(name) or not os.path.lexists(path):
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        result[name] = path
    if f"{PACKAGE_DIR}/__init__.py" not in result:
        msg = f"git listed no {PACKAGE_DIR}/__init__.py under {repo_root}; refusing to copy"
        raise WorkspaceError(msg)
    return result


def file_hash(path: Path) -> str:
    """Return a sha1 of a file's bytes, or of a symlink's target text."""
    if path.is_symlink():
        # os.readlink keeps the link text verbatim; Path.readlink() would normalize it.
        target = os.readlink(path).encode("utf-8", "surrogateescape")  # noqa: PTH115
        return "link:" + hashlib.sha1(target, usedforsecurity=False).hexdigest()
    digest = hashlib.sha1(usedforsecurity=False)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stat_key(path: Path) -> tuple[int, int] | None:
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return None
    return (status.st_size, status.st_mtime_ns)


def _same_entry(destination: Path, source: Path, source_hash: str) -> bool:
    # Each read of ``destination`` is its existence check: a copy file the $TMPDIR
    # purge removes after a separate check reads as not the same, so it is copied.
    present = _stat_key(destination)
    if present is None:
        return False
    if source.is_symlink() != destination.is_symlink() or destination.is_dir():
        return False
    if not source.is_symlink() and present[0] != os.lstat(source).st_size:
        return False
    try:
        return file_hash(destination) == source_hash
    except FileNotFoundError:
        return False


def _copy_entry(source: Path, destination: Path, repo_root: Path) -> None:
    if os.path.lexists(destination):
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination)
        else:
            destination.unlink(missing_ok=True)
    parent = destination.parent
    if os.path.lexists(parent) and not parent.is_dir():
        parent.unlink()
    parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        # os.readlink keeps the link text verbatim; Path.readlink() would normalize it.
        target = os.readlink(source)  # noqa: PTH115
        if Path(target).is_absolute() and _is_within(Path(target), repo_root):
            msg = f"{source} links into the shared tree by absolute path; a copy would share it"
            raise WorkspaceError(msg)
        destination.symlink_to(target)
    else:
        _ = shutil.copy2(source, destination)


def _remove_unwanted(
    destination: Path,
    wanted: dict[str, Path],
    preserved: frozenset[str],
) -> None:
    for directory, dirnames, filenames in os.walk(destination):
        here = Path(directory)
        relative_dir = here.relative_to(destination).as_posix()
        prefix = "" if relative_dir == "." else f"{relative_dir}/"
        keep_dirs: list[str] = []
        for name in dirnames:
            relative = f"{prefix}{name}"
            if not prefix and name in preserved:
                continue
            if (here / name).is_symlink():
                (here / name).unlink()
                continue
            if relative in wanted:
                shutil.rmtree(here / name)
                continue
            keep_dirs.append(name)
        dirnames[:] = keep_dirs
        for name in filenames:
            relative = f"{prefix}{name}"
            if not prefix and name in preserved:
                continue
            if relative not in wanted:
                (here / name).unlink(missing_ok=True)


def _prune_empty_dirs(destination: Path, preserved: frozenset[str]) -> None:
    for directory, _dirnames, _filenames in os.walk(destination, topdown=False):
        here = Path(directory)
        if here == destination:
            continue
        top = here.relative_to(destination).parts[0]
        if top in preserved:
            continue
        with contextlib.suppress(OSError):
            here.rmdir()


def tree_digest(entries: dict[str, list[str | int]]) -> str:
    """Return a sha256 over every ``(name, content hash)`` pair, in name order."""
    digest = hashlib.sha256()
    for name in sorted(entries):
        digest.update(f"{name}\0{entries[name][0]}\n".encode("utf-8", "surrogateescape"))
    return f"sha256:{digest.hexdigest()}"


def mirror_tree(
    repo_root: Path,
    destination: Path,
    *,
    preserved: frozenset[str] = PRESERVED,
    attempts: int = 3,
) -> dict[str, list[str | int]]:
    """Make ``destination`` an exact copy of the shared tree's wanted files.

    Returns ``{name: [content hash, size, shared mtime_ns, copy mtime_ns]}``,
    the manifest drift reports compare against.

    Raises:
        WorkspaceError: the shared tree kept changing during every attempt.

    """
    raced: list[str] = []
    for _attempt in range(attempts):
        wanted = wanted_files(repo_root)
        destination.mkdir(parents=True, exist_ok=True)
        _remove_unwanted(destination, wanted, preserved)
        entries: dict[str, list[str | int]] = {}
        raced = []
        for name, source in wanted.items():
            before = _stat_key(source)
            source_hash = file_hash(source)
            target = destination / name
            if not _same_entry(target, source, source_hash):
                _copy_entry(source, target, repo_root)
                if file_hash(target) != source_hash:
                    raced.append(name)
            after = _stat_key(source)
            if before != after or after is None:
                raced.append(name)
                continue
            copied = _stat_key(target)
            entries[name] = [
                source_hash,
                after[0],
                after[1],
                copied[1] if copied else 0,
            ]
        _prune_empty_dirs(destination, preserved)
        if not raced:
            return entries
    msg = f"the shared tree kept changing while it was copied: {sorted(set(raced))[:5]}"
    raise WorkspaceError(msg)


def _run_checked(command: Sequence[str], env: dict[str, str], holding: Sequence[int] = ()) -> None:
    """Run one environment-building command; a non-zero exit is a refusal with its stderr.

    The command holds the ``holding`` descriptors (the locks it builds
    under), so a lock lasts while the command runs, even past this process.
    """
    require_on_path(command[0], "no copy can be synced")
    completed = subprocess.run(
        list(command),
        capture_output=True,
        env=env,
        check=False,
        pass_fds=tuple(holding),
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"{shlex.join(command)} failed ({completed.returncode}): {detail}"
        raise WorkspaceError(msg)


def _uv_sync(destination: Path, holding: Sequence[int] = ()) -> None:
    command = [
        "uv",
        "sync",
        "--directory",
        str(destination),
        "--frozen",
        "--group",
        "pg",
        "-q",
    ]
    _run_checked(command, clean_env(), holding)


def _lower_bound(specifier: str, what: str) -> str:
    for clause in specifier.split(","):
        stripped = clause.strip()
        if stripped.startswith(">="):
            return stripped.removeprefix(">=").strip()
    msg = f"{what} in pyproject.toml states no >= floor: {specifier!r}"
    raise WorkspaceError(msg)


def _normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_key(name: str, extras: str | None, *, with_extras: bool) -> str:
    """Return a requirement's normalized name, with its sorted extras when ``with_extras``."""
    key = _normalized(name)
    if with_extras and extras and extras.strip():
        key += (
            "[" + ",".join(sorted(_normalized(extra.strip()) for extra in extras.split(","))) + "]"
        )
    return key


def _floor_declarations(
    loads: Callable[[str], Mapping[str, object]],
    text: str,
) -> tuple[str, list[str], list[str]]:
    """Return ``requires-python``, ``[project].dependencies`` and the dev group from ``pyproject``.

    Raises:
        KeyError: a key is missing.
        TypeError: a table is not a table or a dependency list is not an array.

    """
    document = loads(text)
    project = document["project"]
    if not _is_json_object(project):
        msg = f"[project] is a {type(project).__name__}, not a table"
        raise TypeError(msg)
    dependencies = project["dependencies"]
    if not _is_json_array(dependencies):
        msg = f"[project].dependencies is a {type(dependencies).__name__}, not an array"
        raise TypeError(msg)
    groups = document["dependency-groups"]
    if not _is_json_object(groups):
        msg = f"[dependency-groups] is a {type(groups).__name__}, not a table"
        raise TypeError(msg)
    dev = groups["dev"]
    if not _is_json_array(dev):
        msg = f"[dependency-groups].dev is a {type(dev).__name__}, not an array"
        raise TypeError(msg)
    return (
        str(project["requires-python"]),
        [str(requirement) for requirement in dependencies],
        [str(requirement) for requirement in dev],
    )


def _requirement_parts(name: str) -> tuple[str, str | None]:
    """Split one of the floor package spellings into its name and extras."""
    match = REQUIREMENT_PATTERN.match(name)
    if match is None:
        msg = f"not a requirement name: {name!r}"
        raise WorkspaceError(msg)
    return match["name"], match["extras"]


def _lower_bounds(
    requirements: Sequence[str],
    names: Sequence[str],
    *,
    with_extras: bool,
    where: str,
) -> dict[str, str]:
    """Return each of ``names``' ``>=`` lower bound in ``requirements``, keyed and ordered by ``names``.

    A name matches a requirement by its normalized name, and by its extras too
    when ``with_extras``, so a dev row that drops an extra the floor install
    names matches nothing rather than installing without it.

    A name two or more requirements match (rows split by environment marker,
    each with its own bound) is refused: the floor install pins one version per
    package, so choosing one of several floors would be a silent guess.

    Raises:
        WorkspaceError: a name matches no requirement, more than one, or one
            with no ``>=`` bound.

    """
    wanted = {
        _requirement_key(*_requirement_parts(name), with_extras=with_extras): name
        for name in names
    }
    rows: dict[str, list[tuple[str, str]]] = {name: [] for name in names}
    for requirement in requirements:
        match = REQUIREMENT_PATTERN.match(requirement)
        if match is None:
            continue
        key = _requirement_key(match["name"], match["extras"], with_extras=with_extras)
        if key in wanted:
            rows[wanted[key]].append((requirement, match["specifier"]))
    missing = [name for name in names if not rows[name]]
    if missing:
        msg = f"{where} lists no {', '.join(missing)}"
        raise WorkspaceError(msg)
    repeated = {name: matched for name, matched in rows.items() if len(matched) > 1}
    if repeated:
        listed = "; ".join(
            f"{name} in {len(matched)} rows ({', '.join(repr(row) for row, _ in matched)})"
            for name, matched in repeated.items()
        )
        msg = f"{where} states more than one floor for {listed}"
        raise WorkspaceError(msg)
    return {name: _lower_bound(rows[name][0][1], rows[name][0][0]) for name in names}


def floor_pins(pyproject: Path) -> dict[str, str]:
    """Return the floor ``python`` and each floor package's pin, read from ``pyproject``.

    ``pyproject.toml`` is the source of the dependency floor (BUILD.md "Floor
    verification"): ``requires-python``'s ``>=`` bound is the interpreter,
    each of ``FLOOR_PACKAGES``' ``>=`` bound in ``[project].dependencies`` and
    each of ``SOFT_FLOOR_PACKAGES``' in ``[dependency-groups].dev`` is the
    exact point the floor run installs, the same points that section states.
    Each package must have exactly one such row: one split by environment
    marker states several floors, and the floor run installs one.
    """
    try:
        requires_python, dependencies, dev = _floor_declarations(
            tomli.loads,
            pyproject.read_text(encoding="utf-8"),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        tomli.TOMLDecodeError,
    ) as error:
        msg = (
            "[project] requires-python / dependencies or [dependency-groups].dev "
            f"unreadable from {pyproject}: {error!r}"
        )
        raise WorkspaceError(msg) from error
    return {
        "python": _lower_bound(requires_python, "requires-python"),
        **_lower_bounds(
            dependencies,
            FLOOR_PACKAGES,
            with_extras=False,
            where=f"[project].dependencies in {pyproject}",
        ),
        **_lower_bounds(
            dev,
            SOFT_FLOOR_PACKAGES,
            with_extras=True,
            where=f"[dependency-groups].dev in {pyproject}",
        ),
    }


def floor_install_commands(copy: Path, venv: Path, pins: Mapping[str, str]) -> list[list[str]]:
    """Return the floor cell's install, aimed at ``venv`` (``UV_PROJECT_ENVIRONMENT``).

    The ``test`` job of ``.github/workflows/django.yml`` syncs the lock at the
    floor Python, then replaces Django and strawberry-graphql with the exact
    floor points, then every soft dependency in one install; the lock resolves
    newer releases of each for that Python, so they are installed over the
    sync rather than beside it.
    """
    python = str(venv / "bin" / "python")
    pip = [
        "uv",
        "pip",
        "install",
        "--directory",
        str(copy),
        "--python",
        python,
        "-q",
    ]
    django, strawberry = FLOOR_PACKAGES
    return [
        [
            "uv",
            "sync",
            "--directory",
            str(copy),
            "--frozen",
            "--python",
            pins["python"],
            "-q",
        ],
        [
            *pip,
            "--upgrade-package",
            django,
            f"{django}=={pins[django]}",
        ],
        [*pip, f"{strawberry}=={pins[strawberry]}"],
        [*pip, *(f"{name}=={pins[name]}" for name in SOFT_FLOOR_PACKAGES)],
    ]


class _FloorVenv(TypedDict):
    """The floor virtualenv the floor suite ran in, as the gate result records it."""

    python: str
    pins: dict[str, str]
    key: str
    reused: bool


def ensure_floor_venv(layout: Layout, holding: Sequence[int] = ()) -> _FloorVenv:
    """Reuse the gate copy's floor virtualenv while its key matches; else rebuild it whole.

    The key covers the install commands (so the pins and the interpreter) and
    the copy's ``pyproject.toml`` and ``uv.lock``. Package edits need no
    rebuild: the copy is installed editable. The key is written only after
    every command succeeded, so a failed build is rebuilt on the next gate.
    Each install holds ``holding``, the gate's locks (:func:`_run_checked`).
    """
    copy = layout.gate_dir
    venv = layout.floor_venv
    pins = floor_pins(copy / "pyproject.toml")
    commands = floor_install_commands(copy, venv, pins)
    key = hashlib.sha256(
        json.dumps(
            {
                "commands": commands,
                "pyproject.toml": file_hash(copy / "pyproject.toml"),
                "uv.lock": file_hash(copy / "uv.lock"),
            },
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    python = venv / "bin" / "python"
    key_path = venv / FLOOR_KEY_NAME
    reused = python.exists() and _read_text_if_present(key_path) == key
    if not reused:
        if venv.is_symlink() or venv.is_file():
            venv.unlink()
        elif venv.exists():
            shutil.rmtree(venv)
        env = clean_env(UV_PROJECT_ENVIRONMENT=str(venv))
        for command in commands:
            _run_checked(command, env, holding)
        _ = key_path.write_text(key, encoding="utf-8")
    return {
        "python": str(python),
        "pins": pins,
        "key": key,
        "reused": reused,
    }


class _Manifest(TypedDict):
    """What :func:`sync_copy` returns and a slot's ``.manifest.json`` holds."""

    synced_at: str
    tree_digest: str
    package_digest: str
    entries: dict[str, list[str | int]]


def sync_copy(
    repo_root: Path,
    destination: Path,
    *,
    preserved: frozenset[str] = PRESERVED,
    holding: Sequence[int] = (),
) -> _Manifest:
    """Mirror, ``uv sync`` and digest-check one copy; return its manifest.

    ``uv sync`` holds ``holding``, the locks the copy is synced under
    (:func:`_run_checked`).
    """
    entries = mirror_tree(repo_root, destination, preserved=preserved)
    # The mirror rewrote every file outside ``preserved``; a killed proof's mutation inside it is
    # restored from the marker's pristine copy before the marker goes.
    forget_proof_state(destination, preserved)
    _uv_sync(destination, holding)
    copy_digest = _bench_common.package_digest(destination / PACKAGE_DIR)
    shared_digest = _bench_common.package_digest(repo_root / PACKAGE_DIR)
    if copy_digest != shared_digest:
        msg = (
            f"package digest of {destination} ({copy_digest}) differs from the shared tree's "
            f"({shared_digest}); a package file changed during the sync, run again"
        )
        raise WorkspaceError(msg)
    return {
        "synced_at": _now(),
        "tree_digest": tree_digest(entries),
        "package_digest": copy_digest,
        "entries": entries,
    }


def forget_proof_state(copy: Path, preserved: frozenset[str]) -> None:
    """Remove the ``scripts/prove_failability.py`` state directory of ``copy``, if any.

    A proof run killed while its mutation was live leaves its pristine copies
    and ``ACTIVE-MUTATION.json`` there, and that marker refuses every later
    proof in the copy. The caller holds the lock that keeps any command out of
    the copy and has just mirrored it from the shared tree or deleted it. The
    mirror rewrites every file except the top-level ``preserved`` directories
    (``.venv``), which a proof may also have mutated, so each marker file
    under one of them is first restored from its pristine copy and byte
    compared (:func:`_restore_preserved_mutations`); every other mutation is
    gone with the mirror, and its restore command would only write stale bytes
    over fresh ones. After a deletion ``preserved`` is empty: nothing is left
    to restore. A marker that cannot be read, or a file it names that cannot
    be restored and proved, keeps the whole state directory, with one notice
    on stderr: the resync still completes, so ``run`` keeps working in the
    copy, while the prover's own marker refusal keeps guarding ``prove``
    there until the marker is resolved or ``gc`` deletes the copy. The path is
    the prover's own (:func:`prove_failability.tree_state_directory`) for the
    root a run in the copy resolves, under the state home this process sees,
    which the clean environment hands every command unchanged. A
    ``prove_failability`` directory that is not a real directory owned by this
    user (a symlink, another user's) is left alone, as the prover refuses to
    use it.
    """
    directory = prove_failability.tree_state_directory(copy.resolve())
    parent = directory.parent
    try:
        status = parent.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(status.st_mode) or status.st_uid != os.getuid():
        return
    if directory.is_symlink() or directory.is_file():
        directory.unlink()
        return
    if not directory.exists():
        return
    marker = directory / prove_failability.ACTIVE_MARKER_NAME
    if preserved and marker.exists():
        kept = _restore_preserved_mutations(copy.resolve(), marker, preserved)
        if kept is not None:
            _ = sys.stderr.write(f"workspace: kept live-mutation marker {marker}: {kept}\n")
            return
    shutil.rmtree(directory)


def _restore_preserved_mutations(
    copy: Path,
    marker: Path,
    preserved: frozenset[str],
) -> str | None:
    """Restore each file ``marker`` names under a ``preserved`` directory of ``copy``.

    Every entry is parsed before any file is written. Returns ``None`` once each such file
    is restored from its pristine copy and compares equal byte for byte, else why the
    marker must be kept: it is unreadable or not the prover's shape, an entry names a path
    outside the copy or the copy itself, or a pristine copy is missing or its restore does
    not compare equal.
    """
    try:
        document = _loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return f"it cannot be read ({error})"
    files = document.get("files") if _is_json_object(document) else None
    if not _is_json_array(files) or not files:
        return "it names no files"
    restores: list[tuple[Path, Path]] = []
    for item in files:
        mutated = item.get("mutated_file") if _is_json_object(item) else None
        pristine = item.get("restore_from") if _is_json_object(item) else None
        if not isinstance(mutated, str) or not isinstance(pristine, str):
            return "an entry lacks its mutated_file or restore_from"
        target = Path(mutated).resolve()
        if not _is_within(target, copy) or target == copy:
            return f"it names {target}, which is not a file inside {copy}"
        if target.relative_to(copy).parts[0] in preserved:
            restores.append((target, Path(pristine)))
    for target, source in restores:
        try:
            original = source.read_bytes()
            _ = target.write_bytes(original)
            restored = target.read_bytes()
        except OSError as error:
            return f"{target} could not be restored from {source} ({error})"
        if restored != original:
            return f"{target} does not match {source} after its restore"
    return None


def _is_generated(relative: str) -> bool:
    parts = relative.split("/")
    return any(part in GENERATED_SEGMENTS for part in parts) or parts[-1].startswith(".coverage")


def copy_edits(
    destination: Path,
    manifest: _Manifest,
    preserved: frozenset[str] = PRESERVED,
) -> list[str]:
    """Return the names a copy changed, added or deleted since its sync, caches excluded."""
    entries: dict[str, list[str | int]] = manifest.get("entries", {})
    changed: list[str] = []
    for name, (
        content_hash,
        size,
        _shared_mtime,
        copy_mtime,
    ) in entries.items():
        path = destination / name
        key = _stat_key(path)
        if key is None or (key != (size, copy_mtime) and file_hash(path) != content_hash):
            changed.append(name)
    for directory, dirnames, filenames in os.walk(destination):
        here = Path(directory)
        relative_dir = here.relative_to(destination).as_posix()
        prefix = "" if relative_dir == "." else f"{relative_dir}/"
        dirnames[:] = [
            name
            for name in dirnames
            if not (not prefix and name in preserved) and name not in GENERATED_SEGMENTS
        ]
        for name in filenames:
            relative = f"{prefix}{name}"
            if relative not in entries and not _is_generated(relative):
                changed.append(relative)
    return sorted(changed)


def shared_moves(repo_root: Path, manifest: _Manifest) -> list[str]:
    """Return the names the shared tree changed, added or deleted since the copy's sync."""
    entries: dict[str, list[str | int]] = manifest.get("entries", {})
    wanted = wanted_files(repo_root)
    moved = sorted(set(wanted) ^ set(entries))
    for name in set(wanted) & set(entries):
        content_hash, size, shared_mtime, _copy_mtime = entries[name]
        key = _stat_key(wanted[name])
        if key != (size, shared_mtime) and file_hash(wanted[name]) != content_hash:
            moved.append(name)
    return sorted(moved)


# --------------------------------------------------------------------------------------------
# Postgres
# --------------------------------------------------------------------------------------------


class Postgres:
    """The fakeshop compose container, found by identity, and the per-copy databases in it."""

    def __init__(self, repo_root: Path) -> None:
        """Bind to the checkout whose compose file starts the container."""
        self.repo_root: Path = repo_root
        self._container: tuple[str, str, str] | None = None

    def _docker(self, *args: str, check: bool = True) -> str:
        require_on_path("docker", "the Postgres cell cannot run")
        completed = subprocess.run(
            ["docker", *args],
            capture_output=True,
            env=clean_env(),
            check=False,
        )
        if check and completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", "replace").strip()
            msg = f"docker {args[0]} failed ({completed.returncode}): {detail}"
            raise WorkspaceError(msg)
        return completed.stdout.decode("utf-8", "replace")

    def attach(self) -> bool:
        """Remember the running fakeshop container; report whether one runs."""
        self._container = self.find()
        return self._container is not None

    def find(self) -> tuple[str, str, str] | None:
        """Return ``(container id, host port, compose project)`` of the fakeshop container."""
        ids = self._docker("ps", "-q").split()
        if not ids:
            return None
        found: list[tuple[str, str, str]] = []
        inspected = _loads(self._docker("inspect", *ids))
        if not _is_json_array(inspected):
            msg = f"docker inspect printed no JSON array: {inspected!r:.200}"
            raise WorkspaceError(msg)
        for info in inspected:
            if not _is_json_object(info):
                msg = f"docker inspect printed a non-object container entry: {info!r:.200}"
                raise WorkspaceError(msg)
            config = _object_field(info, "Config")
            env = set(_array_field(config, "Env"))
            if f"POSTGRES_USER={PG_USER}" not in env or f"POSTGRES_DB={PG_USER}" not in env:
                continue
            bindings = _array_field(
                _object_field(_object_field(info, "NetworkSettings"), "Ports"),
                PG_PORT,
            )
            if not bindings:
                continue
            container_id = info.get("Id")
            first = bindings[0]
            host_port = first.get("HostPort") if _is_json_object(first) else None
            project = _object_field(config, "Labels").get("com.docker.compose.project", "")
            if not (
                isinstance(container_id, str)
                and isinstance(host_port, str)
                and isinstance(project, str)
            ):
                msg = f"docker inspect reported an unexpected container shape: {info!r:.200}"
                raise WorkspaceError(msg)
            found.append((container_id[:12], host_port, project))
        if len(found) > 1:
            msg = f"{len(found)} fakeshop Postgres containers run ({found}); stop all but one"
            raise WorkspaceError(msg)
        return found[0] if found else None

    def ensure(self) -> tuple[str, str, str]:
        """Return the running container, starting the compose one when none runs."""
        if self._container is None:
            self._container = self.find()
        if self._container is None:
            compose = self.repo_root / COMPOSE_FILE
            _ = self._docker(
                "compose",
                "-p",
                COMPOSE_PROJECT,
                "-f",
                str(compose),
                "up",
                "-d",
                "--wait",
            )
            self._container = self.find()
            if self._container is None:
                msg = f"docker compose started {COMPOSE_FILE} but no fakeshop container is found"
                raise WorkspaceError(msg)
        user = self.sql("SELECT current_user").strip()
        if user != PG_USER:
            msg = f"container {self._container[0]} answers as {user!r}, not {PG_USER!r}"
            raise WorkspaceError(msg)
        return self._container

    def sql(self, statement: str, database: str = "postgres") -> str:
        """Run one statement through ``psql`` inside the container."""
        container = self._container or self.find()
        if container is None:
            msg = "no fakeshop Postgres container runs"
            raise WorkspaceError(msg)
        return self._docker(
            "exec",
            container[0],
            "psql",
            "-U",
            PG_USER,
            "-d",
            database,
            "-v",
            "ON_ERROR_STOP=1",
            "-tAc",
            statement,
        )

    def dsn(self, database: str) -> str:
        """Return the DSN of ``database`` on the running container."""
        _container, port, _project = self.ensure()
        return f"postgres://{PG_USER}:{PG_PASSWORD}@127.0.0.1:{port}/{database}"

    def recreate(self, database: str) -> None:
        """Drop ``database`` and every pytest database derived from it, then create it empty."""
        _ = self.drop_matching(database, exact=True)
        _ = self.sql(f'CREATE DATABASE "{database}"')

    def databases(self, prefix: str = "ws_", *, exact: bool = False) -> list[str]:
        """Return the container's databases named ``prefix...`` or ``test_prefix...``.

        With ``exact`` the name is ``prefix`` itself, plus the ``test_<prefix>``
        and ``test_<prefix>_gwN`` databases pytest-django derives from it, so
        ``slot1`` never matches ``slot10``.
        """
        rows = self.sql("SELECT datname FROM pg_database ORDER BY datname")
        names = [row for row in rows.splitlines() if row]
        if exact:
            return [
                name
                for name in names
                if name in {prefix, f"test_{prefix}"} or name.startswith(f"test_{prefix}_gw")
            ]
        return [name for name in names if name.startswith((prefix, f"test_{prefix}"))]

    def drop_matching(self, prefix: str, *, exact: bool = False) -> list[str]:
        """Drop every database ``databases`` returns for ``prefix``; return their names."""
        names = self.databases(prefix, exact=exact)
        for name in names:
            _ = self.sql(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        return names

    def stop_if_idle(self) -> str:
        """Stop the container when this script started it and no workspace database remains."""
        container = self.find()
        if container is None:
            return "no fakeshop Postgres container runs"
        self._container = container
        remaining = self.databases()
        if remaining:
            return f"Postgres kept: {len(remaining)} workspace database(s) remain"
        if container[2] != COMPOSE_PROJECT:
            return f"Postgres kept: container {container[0]} was not started by this script"
        compose = self.repo_root / COMPOSE_FILE
        _ = self._docker("compose", "-p", COMPOSE_PROJECT, "-f", str(compose), "down")
        return f"Postgres stopped: container {container[0]}"


def _running_postgres(repo_root: Path) -> Postgres | None:
    """Return a handle when docker answers and a fakeshop container runs, else ``None``."""
    postgres = Postgres(repo_root)
    try:
        return postgres if postgres.attach() else None
    except WorkspaceError:
        return None


# --------------------------------------------------------------------------------------------
# The copy pool, bindings and syncs
# --------------------------------------------------------------------------------------------


class _SlotBinding(TypedDict):
    """One bound copy in the pool state; a sync adds its digests."""

    address: str
    item: str
    role: str
    bound_at: str
    status: str
    synced_at: NotRequired[str]
    tree_digest: NotRequired[str]
    package_digest: NotRequired[str]


class _ItemBaseline(TypedDict):
    """One item's pinned ``ITEM_BASELINE`` in the pool state."""

    item_baseline: str
    at: str


class _PoolState(TypedDict):
    """The pool state file: every slot's binding (``None`` when free) and item baselines."""

    version: int
    repo_root: str
    slots: dict[str, _SlotBinding | None]
    items: dict[str, _ItemBaseline]


def _load_state(layout: Layout) -> _PoolState:
    """Return the pool state: the state home's file, else an older version's, else an empty pool.

    The older version's file (:attr:`Layout.legacy_state_path`) is read until
    a command holding ``pool.lock`` moves it (:func:`_held_state`); one moved
    between the two reads is found by reading the state home's file again.
    """
    document = _read_json_object(layout.state_path, None)
    if document is None:
        document = _read_json_object(layout.legacy_state_path, None)
    if document is None:
        document = _read_json_object(
            layout.state_path,
            {
                "version": 1,
                "repo_root": str(layout.repo_root),
                "slots": {},
                "items": {},
            },
        )
    # Only this script writes the state file, always from a ``_PoolState``.
    return cast("_PoolState", document)


def _held_state(layout: Layout) -> _PoolState:
    """Return the pool state to a caller holding ``pool.lock``, an older version's file moved first.

    A flow an older version of this script bound keeps its bindings in the
    flow folder; they are written to the state home and that file removed,
    so the slot numbers its copies hold carry over and no copy is renumbered
    and resynced.
    """
    state = _load_state(layout)
    if not layout.state_path.exists() and layout.legacy_state_path.exists():
        _write_state(layout, state)
    return state


def _make_state_dir(layout: Layout) -> None:
    """Make the flow's state folder and each missing parent with the XDG mode, as the prover does.

    Each level gets ``STATE_DIRECTORY_MODE`` (``0o700``), and the levels are
    made again when a ``gc`` of another flow removed the empty parents
    meanwhile (``ENOENT``, or on macOS ``EINVAL``, or a level gone right after
    ``EEXIST``).
    """
    mode = prove_failability.STATE_DIRECTORY_MODE
    home = prove_failability.state_home().resolve()
    levels = (home / STATE_DIRECTORY_NAME, layout.state_dir.parent, layout.state_dir)
    while True:
        try:
            home.mkdir(mode=mode, parents=True, exist_ok=True)
            for level in levels:
                level.mkdir(mode=mode, exist_ok=True)
        except FileExistsError:
            if all(os.path.lexists(level) for level in (home, *levels)):
                raise
        except OSError as error:
            if error.errno not in {errno.ENOENT, errno.EINVAL}:
                raise
        else:
            return


def _write_state(layout: Layout, state: _PoolState) -> None:
    """Write the pool state to the state home; the caller holds ``pool.lock``.

    Its folder is made (:func:`_make_state_dir`), and an older version's
    file in the flow folder goes.
    """
    _make_state_dir(layout)
    _write_json(layout.state_path, state)
    layout.legacy_state_path.unlink(missing_ok=True)


@dataclasses.dataclass(frozen=True)
class Binding:
    """One address bound to one copy; :func:`lease` decides whether the copy needs a sync."""

    slot: str
    directory: Path


@dataclasses.dataclass(frozen=True)
class Lease:
    """An address's copy while this process holds its lock, synced for that address.

    ``holding`` is every descriptor holding the run's locks, the copy's last,
    for a command that must hold them too (:func:`stream`).
    """

    slot: str
    directory: Path
    manifest: _Manifest
    holding: tuple[int, ...]


def _free_bytes(path: Path) -> int:
    probe = path
    while not probe.exists():
        probe = probe.parent
    return shutil.disk_usage(probe).free


def bind(layout: Layout, address: Address) -> Binding:
    """Bind ``address`` to a copy: its existing one, a free warm one, or a new one.

    A new binding is recorded ``syncing``: the copy holds no sync for this
    address yet.

    Raises:
        WorkspaceError: every copy is bound to another address, or a new copy
            would drop free disk below the guard.

    """
    layout.ensure_marked()
    with file_lock(layout.pool_lock):
        state = _held_state(layout)
        slots = state["slots"]
        for slot, bound in slots.items():
            if bound and bound["address"] == str(address):
                return Binding(slot, layout.slot_dir(slot))
        free = sorted((slot for slot, bound in slots.items() if not bound), key=_slot_number)
        if free:
            slot = free[0]
        elif len(slots) < pool_size():
            if _free_bytes(layout.base) < MIN_FREE_BYTES:
                msg = f"under {MIN_FREE_BYTES // 1024**3} GB free at {layout.base}; no new copy"
                raise WorkspaceError(msg)
            slot = f"slot-{max((_slot_number(name) for name in slots), default=0) + 1}"
        else:
            listing = ", ".join(
                f"{slot} {bound['address']}" for slot, bound in slots.items() if bound
            )
            msg = (
                f"{layout.flow}: all {len(slots)} copies are bound ({listing}). Release a "
                f"finished item: uv run python scripts/workspace.py release {layout.flow}/<item>"
            )
            raise WorkspaceError(msg)
        slots[slot] = {
            "address": str(address),
            "item": address.item,
            "role": address.role,
            "bound_at": _now(),
            "status": "syncing",
        }
        _write_state(layout, state)
        return Binding(slot, layout.slot_dir(slot))


def _slot_number(name: str) -> int:
    return int(name.rpartition("-")[2])


def _admit(
    layout: Layout,
    address: Address,
    slot: str,
    *,
    fresh: bool,
) -> _Manifest | None:
    """Decide, with ``slot``'s lock held, whether the copy needs a sync before this run uses it.

    ``state.json`` is read now, not when the address was bound. A sync is
    recorded ``syncing`` before it starts, so a sync that dies part way,
    ``fresh`` or not, resyncs on the address's next run.

    Returns:
        The manifest of a copy already synced for ``address``, read here, so a
        manifest that is gone by then means a sync; ``None`` when the copy
        needs one.

    Raises:
        WorkspaceError: ``slot`` no longer holds ``address``: a ``release``
            freed it while the run waited for its lock.

    """
    with file_lock(layout.pool_lock):
        state = _held_state(layout)
        bound = state["slots"].get(slot)
        if not bound or bound["address"] != str(address):
            msg = f"{address}: {slot} was released while this command waited for it; run it again"
            raise WorkspaceError(msg)
        if not fresh and bound["status"] == "ready":
            synced = _read_json_object(layout.manifest_path(slot), None)
            if synced is not None:
                # Only ``sync_slot`` writes a slot's manifest file, always from a ``_Manifest``.
                return cast("_Manifest", synced)
        if bound["status"] != "syncing":
            bound["status"] = "syncing"
            _write_state(layout, state)
        return None


@contextlib.contextmanager
def lease(
    layout: Layout,
    address: Address,
    *,
    fresh: bool = False,
    holding: tuple[int, ...] = (),
) -> Generator[Lease, None, None]:
    """Hold ``address``'s copy, bound and synced for it, until the block ends.

    The caller holds the flow's lease, on the ``holding`` descriptors. The
    copy's sync holds that lease and the copy's lock too. The run waits for
    the copy's lock and decides only then, from ``state.json`` and the copy's
    manifest read under it, whether to sync: a copy already synced for the
    address is used as it stands, edits included, however long the run
    waited; a copy still ``syncing`` (a new binding, or a sync that never
    finished), one whose manifest is gone, or one ``fresh`` asks for is
    resynced.

    Raises:
        WorkspaceError: the copy no longer holds ``address``: a release freed
            it while the run waited for its lock. The run never binds the
            address again.

    """
    slot = bind(layout, address).slot
    with file_lock(layout.slot_lock(slot)) as descriptor:
        held = (*holding, descriptor)
        synced = _admit(layout, address, slot, fresh=fresh)
        manifest = sync_slot(layout, slot, address, held) if synced is None else synced
        yield Lease(slot, layout.slot_dir(slot), manifest, held)


def copy_path(layout: Layout, address: Address) -> Path:
    """Return ``address``'s copy for reading or editing, bound and synced for it.

    A copy whose sync for the address finished is returned at once, even while
    a command runs in it: ``state.json`` is replaced whole, so that read needs
    no lock. Anything else (unbound, still ``syncing``, its manifest gone) is
    settled by :func:`lease`, after any command running in the copy. The
    caller holds the flow's lease.
    """
    for slot, bound in _load_state(layout)["slots"].items():
        if (
            bound
            and bound["address"] == str(address)
            and bound["status"] == "ready"
            and layout.manifest_path(slot).exists()
        ):
            return layout.slot_dir(slot)
    with lease(layout, address) as held:
        return held.directory


def _mark_synced(
    layout: Layout,
    slot: str,
    address: Address,
    manifest: _Manifest,
) -> None:
    """Record ``manifest`` as the sync of ``slot`` for ``address``.

    Raises:
        WorkspaceError: ``slot`` no longer holds ``address``; no other binding
            is ever stamped with this sync.

    """
    with file_lock(layout.pool_lock):
        state = _held_state(layout)
        bound = state["slots"].get(slot)
        if not bound or bound["address"] != str(address):
            msg = f"{slot} no longer holds {address}: it was released during the sync"
            raise WorkspaceError(msg)
        bound.update(
            status="ready",
            synced_at=manifest["synced_at"],
            tree_digest=manifest["tree_digest"],
            package_digest=manifest["package_digest"],
        )
        _write_state(layout, state)


def sync_slot(
    layout: Layout,
    slot: str,
    address: Address,
    holding: Sequence[int] = (),
) -> _Manifest:
    """Resync one copy from the shared tree for ``address`` and drop its Postgres databases.

    ``uv sync`` holds ``holding``, the run's locks (:func:`sync_copy`).
    """
    postgres = _running_postgres(layout.repo_root)
    if postgres is not None:
        _ = postgres.drop_matching(layout.db_name(slot), exact=True)
    manifest = sync_copy(layout.repo_root, layout.slot_dir(slot), holding=holding)
    _write_json(layout.manifest_path(slot), manifest)
    _mark_synced(layout, slot, address, manifest)
    return manifest


# --------------------------------------------------------------------------------------------
# Running a command
# --------------------------------------------------------------------------------------------


def cell_env(layout: Layout, slot: str, cell: str) -> tuple[dict[str, str], str | None]:
    """Return the clean environment for ``cell`` and the copy's Postgres database, if any."""
    if cell == "default":
        return clean_env(), None
    if cell == "sharded":
        return clean_env(FAKESHOP_SHARDED="1"), None
    database = layout.db_name(slot)
    postgres = Postgres(layout.repo_root)
    _ = postgres.ensure()
    if not postgres.databases(database, exact=True):
        postgres.recreate(database)
    return clean_env(FAKESHOP_PG_DSN=postgres.dsn(database)), database


class _ProbeDatabase(TypedDict):
    """One alias's settings as ``PROBE`` reports them."""

    ENGINE: str
    NAME: str


class _ProbeResult(TypedDict):
    """The JSON line ``PROBE`` prints inside a copy."""

    executable: str
    package_file: str | None
    databases: dict[str, _ProbeDatabase]


def uv_run_in(directory: Path) -> list[str]:
    """Return the ``uv run`` that resolves ``directory``'s environment, ``pg`` group included."""
    return [
        "uv",
        "run",
        "--directory",
        str(directory),
        "--frozen",
        "--group",
        "pg",
    ]


def uv_launch(
    directory: Path,
    command: Sequence[str],
    env: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    """Return ``command`` and its environment as :func:`uv_run_in` would start them, with no uv between.

    ``uv run`` syncs the copy's environment and reports it
    (``scripts/_stop_signals.py::uv_run_launch``); the caller then starts the
    command itself, in ``directory`` as ``uv run --directory`` would, so a
    relayed stop reaches it once.
    """
    require_on_path("uv", "nothing can run in a copy")
    try:
        return _stop_signals.uv_run_launch(uv_run_in(directory), command, env, directory)
    except _stop_signals.LaunchError as error:
        raise WorkspaceError(str(error)) from error


def probe(directory: Path, env: dict[str, str]) -> _ProbeResult:
    """Resolve, inside the copy, where the package imports from and each alias's database."""
    require_on_path("uv", "nothing can run in a copy")
    completed = subprocess.run(
        [
            *uv_run_in(directory),
            "python",
            "-c",
            PROBE,
        ],
        capture_output=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"the provenance probe failed in {directory}: {detail}"
        raise WorkspaceError(msg)
    return _probe_result(_loads(completed.stdout.decode("utf-8").strip().splitlines()[-1]))


def _probe_result(document: object) -> _ProbeResult:
    """Return the ``PROBE`` JSON line as a :class:`_ProbeResult`, refusing any other shape."""
    if not _is_json_object(document):
        msg = f"the provenance probe printed a non-object: {document!r:.200}"
        raise WorkspaceError(msg)
    executable = document.get("executable")
    package_file = document.get("package_file")
    raw_databases = document.get("databases")
    if not (
        isinstance(executable, str)
        and (package_file is None or isinstance(package_file, str))
        and _is_json_object(raw_databases)
    ):
        msg = f"the provenance probe printed an unexpected shape: {document!r:.200}"
        raise WorkspaceError(msg)
    databases: dict[str, _ProbeDatabase] = {}
    for alias, conf in raw_databases.items():
        engine = conf.get("ENGINE") if _is_json_object(conf) else None
        name = conf.get("NAME") if _is_json_object(conf) else None
        if not isinstance(engine, str) or not isinstance(name, str):
            msg = f"the provenance probe printed an unexpected alias {alias!r}: {conf!r:.200}"
            raise WorkspaceError(msg)
        databases[alias] = {"ENGINE": engine, "NAME": name}
    return {"executable": executable, "package_file": package_file, "databases": databases}


def provenance_faults(
    found: _ProbeResult,
    directory: Path,
    cell: str,
    database: str | None,
) -> list[str]:
    """Return why a probe result is not this copy's provenance; empty when it is."""
    faults: list[str] = []
    package = found.get("package_file")
    if not package or not _is_within(Path(package), directory):
        faults.append(f"package would import from {package}, outside {directory}")
    executable = found.get("executable") or ""
    if not _is_within(Path(executable).parent, directory / ".venv"):
        faults.append(f"interpreter {executable} is not the copy's .venv")
    for alias, conf in found["databases"].items():
        name, engine = conf["NAME"], conf["ENGINE"]
        if "postgresql" in engine:
            if cell != "pg" or name != database:
                faults.append(f"alias {alias!r} opens Postgres {name!r}, not {database!r}")
        elif not _bench_common.is_memory_db_name(name) and not _is_within(Path(name), directory):
            faults.append(f"alias {alias!r} opens {name}, outside {directory}")
    default = found["databases"].get("default")
    if cell == "pg" and (None if default is None else default["NAME"]) != database:
        faults.append(f"cell pg did not select {database!r} for the default alias")
    return faults


def _pump(
    source: io.BufferedReader,
    sink: BinaryIO,
    log: BinaryIO,
    lock: threading.Lock,
) -> None:
    """Copy ``source`` to ``sink`` and the log until the command closes it.

    A sink that fails is dropped and the log keeps every byte, so the
    command never blocks on a pipe nobody drains. A sink whose reader is
    gone (``EPIPE``: a pipe whose reader exited; ``EIO``: a closed terminal)
    goes quiet first (:func:`_quiet_dead_sink`), so this process still ends
    with the command's code; any other failure (a full disk) only drops it.
    """
    echo: BinaryIO | None = sink
    for chunk in iter(lambda: source.read1(1 << 16), b""):
        if echo is not None:
            try:
                _ = echo.write(chunk)
                echo.flush()
            except OSError as error:
                if error.errno in {errno.EPIPE, errno.EIO}:
                    _quiet_dead_sink(echo)
                echo = None
        with lock:
            _ = log.write(chunk)


def _quiet_dead_sink(sink: BinaryIO) -> None:
    """Point the sink's descriptor, and stdout or stderr on the same dead file, at ``os.devnull``.

    What the failed write left buffered is flushed again as the process
    exits, and the run's footer goes to stderr; either failing on the dead
    file would end the process with ``120`` or a traceback instead of the
    command's code. Never raises: a descriptor that cannot be read or
    repointed is left as it is.
    """
    with contextlib.suppress(OSError, ValueError):
        fd = sink.fileno()
        dead = os.fstat(fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            for target in dict.fromkeys((fd, 1, 2)):
                with contextlib.suppress(OSError):
                    found = os.fstat(target)
                    if (found.st_dev, found.st_ino) == (dead.st_dev, dead.st_ino):
                        _ = os.dup2(devnull, target)
        finally:
            os.close(devnull)


@dataclasses.dataclass(frozen=True)
class Finished:
    """How a streamed command ended: its exit code, and the stop signal its run relayed, if any."""

    code: int
    stopped_by: int | None = None


class _StopRelay:
    """Relay stop signals to one command's process group; record the first.

    The handler never raises, so nothing unwinds: the locks, the log and the
    pumps stay until the command has ended and its output is drained. The
    first stop is sent to the command's whole group as received, as a
    terminal sends Ctrl-C to its foreground group; a repeat inside
    :data:`STOP_REPEAT_GRACE` of the last one relayed is that one delivered
    twice and is dropped, and a later one is relayed as received, so a
    command's own answer to a second Ctrl-C holds. The group is signalled
    until the output is drained, after the command itself has exited too, so
    a stop reaches what it left holding its output (``sleep 60 &``). A stop
    that lands before the command is recorded waits in ``pending`` until it
    is (:meth:`started`); a suspend that lands then waits likewise, in the
    job control (``_stop_signals._JobControl``).

    ``clock`` is what the grace is measured on, ``time.monotonic`` unless a
    caller hands it another clock in seconds.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock: Callable[[], float] = clock
        self.signum: int | None = None
        self.relayed_at: float = 0.0
        self.pending: int | None = None
        self.group_id: int | None = None

    def __call__(self, signum: int, _frame: FrameType | None) -> None:
        now = self.clock()
        if self.signum is not None and now - self.relayed_at < STOP_REPEAT_GRACE:
            return
        if self.signum is None:
            self.signum = signum
        self.relayed_at = now
        if self.group_id is None:
            self.pending = signum
        else:
            _stop_signals.signal_group_id(self.group_id, signum)

    def group(self) -> int | None:
        """Return the command's process group once it is recorded: its pid, as it leads a session."""
        return self.group_id

    def started(self, process: subprocess.Popen[bytes]) -> None:
        """Record the command's group, then send it the stop that came before it, if any."""
        self.group_id = process.pid
        pending, self.pending = self.pending, None
        if pending is not None:
            _stop_signals.signal_group_id(self.group_id, pending)


def stream(
    command: Sequence[str],
    env: dict[str, str],
    log_path: Path,
    header: str,
    cwd: Path | None = None,
    *,
    holding: Sequence[int] = (),
) -> Finished:
    """Run ``command`` in ``cwd``, copying its stdout and stderr through while logging both.

    The command runs in a session of its own and holds the ``holding``
    descriptors (the run's leases), so a lease lasts while anything the
    command started with it runs, even past this process. A stop signal is
    relayed to the command's whole process group (:class:`_StopRelay`), and
    Ctrl-Z suspends that group with this process (``fg`` continues both),
    one that lands while the command is being started once it has; this
    returns once the command has ended and its output is drained. A
    command that died by signal ``N`` reads as exit ``128 + N``. The
    command's pipes are closed on every path, each only once its reader has
    finished; an error out of the run first kills the command's process
    group, so the command never outlives the run holding its leases.
    """
    require_on_path(command[0], "nothing can run in a copy")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    relay = _StopRelay()
    with (
        log_path.open("wb") as log,
        _stop_signals.routed_to(relay, group=relay.group) as jobs,
    ):
        _ = log.write(header.encode("utf-8"))
        log.flush()
        out_sink, err_sink = sys.stdout.buffer, sys.stderr.buffer
        with subprocess.Popen(  # the worker's own command, in its copy
            list(command),
            env=env,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            pass_fds=tuple(holding),
        ) as process:
            lock = threading.Lock()
            pumps = [
                threading.Thread(
                    target=_pump,
                    args=(
                        process.stdout,
                        out_sink,
                        log,
                        lock,
                    ),
                ),
                threading.Thread(
                    target=_pump,
                    args=(
                        process.stderr,
                        err_sink,
                        log,
                        lock,
                    ),
                ),
            ]
            try:
                relay.started(process)
                if jobs is not None:
                    jobs.settle()
                for pump in pumps:
                    pump.start()
                code = process.wait()
            except BaseException:
                _stop_signals.signal_group_id(process.pid, signal.SIGKILL)
                raise
            finally:
                for pump in pumps:
                    if pump.is_alive():
                        pump.join()
    return Finished(128 - code if code < 0 else code, relay.signum)


def _short(names: list[str], limit: int = 4) -> str:
    shown = ", ".join(names[:limit])
    return f"{shown}, +{len(names) - limit} more" if len(names) > limit else shown


class _RunRecord(TypedDict):
    """One run :func:`execute` logs; ``exit`` and ``seconds`` land when the command ends."""

    run_id: str
    address: str
    item: str
    role: str
    slot: str
    directory: str
    synced_at: str
    tree_digest: str
    package_file: str | None
    package_digest: str
    cell: str
    databases: dict[str, str]
    copy_edits: list[str]
    shared_moves: list[str]
    command: list[str]
    log: str
    started: str
    exit: NotRequired[int]
    seconds: NotRequired[float]
    stopped_by: NotRequired[str]


def render_header(record: _RunRecord) -> str:
    """Return the provenance header a run prints before its output."""
    edits = record["copy_edits"]
    moves = record["shared_moves"]
    databases = ", ".join(f"{alias}={name}" for alias, name in record["databases"].items())
    lines = [
        f"workspace run {record['run_id']}",
        f"  address  {record['address']}",
        f"  copy     {record['directory']} ({record['slot']}, synced {record['synced_at']})",
        f"  package  {record['package_file']}",
        f"  digest   {record['package_digest']}",
        f"  cell     {record['cell']}: {databases}",
        f"  copy is  {'fresh' if not edits else f'modified: {len(edits)} ({_short(edits)})'}",
        "  shared   "
        + ("unmoved since sync" if not moves else f"moved: {len(moves)} ({_short(moves)})"),
        f"  command  {' '.join(record['command'])}",
        f"  log      {record['log']}",
    ]
    return "\n".join(lines) + "\n"


def execute(
    layout: Layout,
    address: Address,
    build_command: Callable[[Path, str], list[str]],
    *,
    cell: str = "default",
    fresh: bool = False,
) -> int:
    """Lease the address's copy, probe, then run the command in it."""
    check_shared_checkout(layout.repo_root)
    with flow_lease(layout) as flow:
        return _execute_leased(
            layout,
            address,
            build_command,
            cell=cell,
            fresh=fresh,
            holding=flow.holding,
        )


def _execute_leased(
    layout: Layout,
    address: Address,
    build_command: Callable[[Path, str], list[str]],
    *,
    cell: str,
    fresh: bool,
    holding: tuple[int, ...],
) -> int:
    with lease(layout, address, fresh=fresh, holding=holding) as held:
        manifest = held.manifest
        env, database = cell_env(layout, held.slot, cell)
        found = probe(held.directory, env)
        faults = provenance_faults(found, held.directory, cell, database)
        if faults:
            raise WorkspaceError("wrong tree: " + "; ".join(faults))
        run_id = new_run_id(layout.flow)
        command = build_command(held.directory, run_id)
        launch, launch_env = uv_launch(held.directory, command, env)
        log_path = layout.evidence / "logs" / f"{run_id}.log"
        record: _RunRecord = {
            "run_id": run_id,
            "address": str(address),
            "item": address.item,
            "role": address.role,
            "slot": held.slot,
            "directory": str(held.directory),
            "synced_at": manifest.get("synced_at"),
            "tree_digest": manifest.get("tree_digest"),
            "package_file": found["package_file"],
            "package_digest": _bench_common.package_digest(held.directory / PACKAGE_DIR),
            "cell": cell,
            "databases": {alias: conf["NAME"] for alias, conf in found["databases"].items()},
            "copy_edits": copy_edits(held.directory, manifest),
            "shared_moves": shared_moves(layout.repo_root, manifest),
            "command": command,
            "log": str(log_path),
            "started": _now(),
        }
        header = render_header(record)
        _ = sys.stderr.write(header)
        _ = sys.stderr.flush()
        started = time.monotonic()
        finished = stream(
            launch,
            launch_env,
            log_path,
            header,
            held.directory,
            holding=held.holding,
        )
        seconds = round(time.monotonic() - started, 2)
        record.update(exit=finished.code, seconds=seconds)
        stopped = ""
        if finished.stopped_by is not None:
            record["stopped_by"] = signal.Signals(finished.stopped_by).name
            stopped = f", stopped by {record['stopped_by']}"
    layout.evidence.mkdir(parents=True, exist_ok=True)
    with layout.run_log.open("a", encoding="utf-8") as handle:
        _ = handle.write(json.dumps(record, sort_keys=True) + "\n")
    _ = sys.stderr.write(
        f"workspace run {record['run_id']} exit {finished.code} in {seconds}s{stopped}\n",
    )
    return finished.code if finished.stopped_by is None else 128 + finished.stopped_by


def _worker_command(raw: Sequence[str]) -> list[str]:
    command = list(raw)
    if not command:
        msg = "no command given; put it after --"
        raise WorkspaceError(msg)
    if command[0] == "uv":
        msg = "give the command that follows `uv run`, not `uv ...`; the copy's uv run resolves it"
        raise WorkspaceError(msg)
    return command


# --------------------------------------------------------------------------------------------
# Worker-0: release, gc, status, audit, gate
# --------------------------------------------------------------------------------------------


def release(
    layout: Layout,
    item: str,
    roles: Sequence[str] = (),
    keep: Sequence[str] = (),
) -> list[str]:
    """Unbind the item's copies and drop their databases.

    ``roles`` limits the release to those roles; ``keep`` spares those roles,
    so ``keep=("before",)`` frees one phase's copies for the next phase while
    the pinned pre-edit copy stays. Only a whole-item release forgets the
    item's ``ITEM_BASELINE``.

    Each copy's lock is taken without waiting and kept until its binding is
    gone from ``state.json``, so no command enters a copy this release is
    freeing; one that was bound but still waiting for the copy refuses when
    it gets the lock, unless its address holds that copy again by then. A
    flow whose folder is gone (a reboot emptied the temporary directory)
    while its state lives on gets the folder back to hold those locks.

    Raises:
        LockBusyError: a command still runs in one of them.

    """
    with flow_lease(layout, create=_folder_gone_state_kept(layout)) as flow:
        if not flow.marked:
            return []
        with file_lock(layout.pool_lock), contextlib.ExitStack() as leases:
            state = _held_state(layout)
            chosen = [
                slot
                for slot, bound in state["slots"].items()
                if bound
                and bound["item"] == item
                and (not roles or bound["role"] in roles)
                and bound["role"] not in keep
            ]
            busy: list[str] = []
            for slot in chosen:
                try:
                    _ = leases.enter_context(file_lock(layout.slot_lock(slot), blocking=False))
                except LockBusyError:
                    busy.append(slot)
            if busy:
                msg = f"{layout.flow}/{item}: a command still runs in {', '.join(busy)}"
                raise LockBusyError(msg)
            postgres = _running_postgres(layout.repo_root)
            released: list[str] = []
            for slot in chosen:
                if postgres is not None:
                    _ = postgres.drop_matching(layout.db_name(slot), exact=True)
                # ``chosen`` holds only bound slots.
                bound = cast("_SlotBinding", state["slots"][slot])
                released.append(f"{slot} {bound['address']}")
                state["slots"][slot] = None
            forgot = not roles and not keep and state["items"].pop(item, None) is not None
            if released or forgot:
                _write_state(layout, state)
    return released


def running_slots(layout: Layout, slots: Iterable[str]) -> list[str]:
    """Return which of ``slots`` a command holds, without making any lock look held.

    Each slot lock is tried without waiting, under ``pool.lock``: ``release``
    tries slot locks only under ``pool.lock`` too, so this check never makes
    it refuse, and a run waiting for its copy waits a moment longer. Nothing
    is created, though a lock file an older version left is replaced by its
    directory; a lock that is gone reads as free.
    """
    busy: list[str] = []
    try:
        with file_lock(layout.pool_lock, create=False):
            for slot in slots:
                try:
                    with file_lock(layout.slot_lock(slot), blocking=False, create=False):
                        pass
                except LockBusyError:
                    busy.append(slot)
                except FileNotFoundError:
                    continue
    except FileNotFoundError:
        return []
    return busy


def _empty_folder(folder: Path, keep: str | None = None) -> None:
    """Remove every entry of ``folder`` but ``keep``; a symlink is unlinked, never followed."""
    for entry in folder.iterdir():
        if entry.name == keep:
            continue
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink(missing_ok=True)


def _remove_flow_dir(flow_dir: Path) -> None:
    """Remove the flow folder, its marker last, so a removal that fails can be run again.

    The marker is a directory, or a file nothing has upgraded yet. Its existence
    proves ownership, so whatever another program left inside it (a Finder
    ``.DS_Store``) is cleared with it.
    """
    _empty_folder(flow_dir, keep=MARKER_NAME)
    marker = flow_dir / MARKER_NAME
    if marker.is_dir() and not marker.is_symlink():
        _empty_folder(marker)
        marker.rmdir()
    else:
        marker.unlink(missing_ok=True)
    flow_dir.rmdir()


def _folder_gone_state_kept(layout: Layout) -> bool:
    """Report whether the flow's state outlives its folder, which a reboot or a cleaner removed."""
    return layout.state_path.exists() and not os.path.lexists(layout.flow_dir)


def _forget_state(layout: Layout) -> None:
    """Remove the flow's folder under the state home; its empty parents go at the end of ``gc``."""
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(layout.state_dir)


def _copies(layout: Layout) -> list[Path]:
    """Return every copy directory the flow folder holds: its slots and its gate copy."""
    slots = layout.flow_dir / "slots"
    found = [
        path
        for path in (slots.iterdir() if slots.is_dir() else ())
        if path.is_dir() and not path.is_symlink() and not path.name.endswith(".lock")
    ]
    gate_dir = layout.gate_dir
    if gate_dir.is_dir() and not gate_dir.is_symlink():
        found.append(gate_dir)
    return sorted(found)


def gc(layout: Layout) -> list[str]:
    """Delete the flow folder and its databases; stop Postgres when this script owns it idle.

    The flow's lease is taken exclusively without waiting and kept until the
    folder is gone, so ``gc`` refuses while any command of the flow runs, a
    command waiting for a copy included, and no command starts inside it.
    The flow's state goes with the folder. A flow whose folder is gone (a
    reboot emptied the temporary directory) while its state lives on gets the
    folder back, marked, so its state is removed under that same lease.

    Raises:
        LockBusyError: a command of the flow still runs.
        WorkspaceError: the folder carries no marker of this script.

    """
    report: list[str] = []
    flow_dir = layout.flow_dir
    recreate = _folder_gone_state_kept(layout)
    try:
        descriptor = _lock_flow_dir(layout, fcntl.LOCK_EX | fcntl.LOCK_NB, create=recreate)
    except BlockingIOError:
        state = _load_state(layout)
        busy = running_slots(layout, sorted(state["slots"], key=_slot_number))
        where = f" ({', '.join(busy)})" if busy else ""
        msg = f"a command still runs in {layout.flow}{where}; wait for it to finish"
        raise LockBusyError(msg) from None
    try:
        if recreate and descriptor is not None:
            layout.ensure_marked()
        if descriptor is not None and not (flow_dir / MARKER_NAME).exists():
            msg = f"{flow_dir} carries no {MARKER_NAME} marker; refusing to delete it"
            raise WorkspaceError(msg)
        postgres = _running_postgres(layout.repo_root)
        if postgres is not None:
            dropped = postgres.drop_matching(layout.db_prefix)
            report.append(f"dropped {len(dropped)} Postgres database(s)")
        if descriptor is not None:
            # A file the $TMPDIR purge removes after its check counts as already gone.
            present = (
                _stat_key(path)
                for path in flow_dir.rglob("*")
                if path.is_file() and not path.is_symlink()
            )
            size = sum(facts[0] for facts in present if facts is not None)
            # Each copy goes before its proof state, so no copy outlives the marker of a
            # mutation it may still hold, whichever removal is cut short.
            for copy in _copies(layout):
                resolved = copy.resolve()
                shutil.rmtree(copy)
                forget_proof_state(resolved, frozenset())
            _forget_state(layout)
            _remove_flow_dir(flow_dir)
            report.append(f"removed {flow_dir} ({size / 1024**2:.0f} MB)")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    # The default ``dsf-ws`` parent is this script's to remove; a DSF_WS_ROOT folder is not.
    parents = [layout.base] if os.environ.get(ROOT_ENV) else [layout.base, layout.base.parent]
    # The state home's ``dsf-ws`` folders are this script's whatever the root; the flow's own
    # goes too when a crash between making it and writing its state left it empty.
    parents.extend((layout.state_dir, layout.state_dir.parent, layout.state_dir.parent.parent))
    for parent in parents:
        with contextlib.suppress(OSError):
            parent.rmdir()
    if postgres is not None:
        report.append(postgres.stop_if_idle())
    return report


def status(repo_root: Path, flow: str | None) -> list[str]:
    """Describe every flow's copies, bindings, active runs and Postgres leases."""
    base = workspace_base(repo_root)
    lines = [f"root {base}"]
    # A flow whose folder a reboot removed is listed from its state, so it can be released or gc'd.
    marked = {p.name for p in base.glob("*") if (p / MARKER_NAME).exists()}
    stored = {p.name for p in state_root(base).glob("*") if (p / "state.json").exists()}
    flows = [flow] if flow else sorted(marked | stored)
    for name in flows:
        layout = Layout(repo_root, base, name)
        state = _load_state(layout)
        lines.append(f"{name}: {len(state['slots'])} of {pool_size()} copies")
        running = set(running_slots(layout, state["slots"]))
        for slot, bound in sorted(state["slots"].items(), key=lambda pair: _slot_number(pair[0])):
            running_text = " RUNNING" if slot in running else ""
            where = f"{bound['address']} ({bound.get('status')})" if bound else "free (warm)"
            lines.append(f"  {slot}  {where}{running_text}")
        for item, entry in sorted(state["items"].items()):
            lines.append(f"  item {item}  ITEM_BASELINE={entry['item_baseline']}")
    postgres = _running_postgres(repo_root)
    container = None if postgres is None else postgres.find()
    if postgres is None or container is None:
        lines.append("postgres: no fakeshop container runs")
    else:
        leases = postgres.databases()
        lines.append(f"postgres: container {container[0]}, {len(leases)} workspace database(s)")
        lines.extend(f"  {name}" for name in leases)
    return lines


class _LoggedRun(TypedDict):
    """The run log fields :func:`load_runs` and :func:`audit_record` read; every run writes them."""

    run_id: str
    address: str
    directory: str
    package_file: str | None
    package_digest: str
    cell: str
    databases: dict[str, str]
    copy_edits: list[str]
    shared_moves: list[str]
    exit: int | None


def load_runs(layout: Layout) -> dict[str, _LoggedRun]:
    """Return every logged run of the flow by id.

    A run log removed while this runs (a ``gc`` of the flow) holds no runs.
    """
    text = _read_text_if_present(layout.run_log)
    if text is None:
        return {}
    runs: dict[str, _LoggedRun] = {}
    for line in text.splitlines():
        if line.strip():
            record = _logged_run(_loads(line), layout.run_log)
            runs[record["run_id"]] = record
    return runs


def _logged_run(document: object, run_log: Path) -> _LoggedRun:
    """Return one run log line as a :class:`_LoggedRun`, refusing any other shape.

    ``package_file`` is ``None`` when the probe resolved no package, and ``exit``
    is ``None`` for a run whose command never reported back.
    """
    if not _is_json_object(document):
        msg = f"{run_log}: a run log line is not a JSON object: {document!r:.200}"
        raise WorkspaceError(msg)
    run_id = document.get("run_id")
    address = document.get("address")
    directory = document.get("directory")
    package_digest = document.get("package_digest")
    cell = document.get("cell")
    package_file = document.get("package_file")
    exit_code = document.get("exit")
    raw_databases = document.get("databases")
    copy_edits = document.get("copy_edits")
    shared_moves = document.get("shared_moves")
    if not (
        isinstance(run_id, str)
        and isinstance(address, str)
        and isinstance(directory, str)
        and isinstance(package_digest, str)
        and isinstance(cell, str)
        and (package_file is None or isinstance(package_file, str))
        and (exit_code is None or (isinstance(exit_code, int) and not isinstance(exit_code, bool)))
        and _is_json_object(raw_databases)
        and all(isinstance(name, str) for name in raw_databases.values())
        and _is_str_array(copy_edits)
        and _is_str_array(shared_moves)
    ):
        msg = f"{run_log}: a run log line has an unexpected shape: {document!r:.200}"
        raise WorkspaceError(msg)
    return {
        "run_id": run_id,
        "address": address,
        "directory": directory,
        "package_file": package_file,
        "package_digest": package_digest,
        "cell": cell,
        "databases": {alias: str(name) for alias, name in raw_databases.items()},
        "copy_edits": copy_edits,
        "shared_moves": shared_moves,
        "exit": exit_code,
    }


def _is_str_array(value: object) -> TypeIs[list[str]]:
    """Return whether a decoded JSON value is an array of strings."""
    return _is_json_array(value) and all(isinstance(entry, str) for entry in value)


def audit_record(repo_root: Path, record_path: Path) -> tuple[list[str], bool]:
    """Resolve every run id ``record_path`` cites; return report lines and whether all bind."""
    try:
        text = record_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        msg = f"audit {record_path}: {error}"
        raise WorkspaceError(msg) from error
    cited = list(dict.fromkeys(match.group(0) for match in RUN_ID_PATTERN.finditer(text)))
    lines = [f"{record_path}: {len(cited)} run id(s) cited"]
    base = workspace_base(repo_root)
    runs: dict[str, _LoggedRun] = {}
    for flow in {match.group(1) for match in RUN_ID_PATTERN.finditer(text)}:
        runs.update(load_runs(Layout(repo_root, base, flow)))
    ok = True
    for run_id in cited:
        run = runs.get(run_id)
        if run is None:
            lines.append(f"  FAIL {run_id}: no run log entry (never ran here, or gc removed it)")
            ok = False
            continue
        directory = Path(run["directory"])
        faults: list[str] = []
        package_file = run["package_file"]
        if package_file is None:
            faults.append("no package `__file__` was recorded")
        elif not _is_within(Path(package_file), directory):
            faults.append(f"package {package_file} outside {directory}")
        for alias, name in run["databases"].items():
            inside = _is_within(Path(name), directory) or _bench_common.is_memory_db_name(name)
            if not inside and not name.startswith("ws_"):
                faults.append(f"alias {alias} opened {name}")
        edits, moves = run["copy_edits"], run["shared_moves"]
        verdict = "FAIL" if faults else "ok  "
        ok = ok and not faults
        lines.append(
            f"  {verdict} {run_id}: {run['address']} cell={run['cell']} exit={run['exit']} "
            f"digest={run['package_digest'][:19]} copy={'fresh' if not edits else f'modified {len(edits)}'} "
            f"shared={'unmoved' if not moves else f'moved {len(moves)}'}"
            + (f" [{'; '.join(faults)}]" if faults else ""),
        )
    return lines, ok


def build_gate_git(repo_root: Path, gate_dir: Path) -> str:
    """Give the gate copy its own git index of ``HEAD``, borrowing the shared object store.

    The suite's census asks git for the committable file list. A standalone
    repository whose objects come from the shared store (read-only alternates)
    answers it without the copy touching the shared index or a worktree's
    ``gitdir`` pointer. ``HEAD`` is detached at the shared ``HEAD`` commit, so
    ``git status`` in the copy reports the working tree's changes against it.
    """
    git_dir = gate_dir / ".git"
    if git_dir.is_dir() and not git_dir.is_symlink():
        shutil.rmtree(git_dir)
    elif os.path.lexists(git_dir):
        git_dir.unlink()
    _ = _git(gate_dir, "init", "-q")
    common = Path(
        _git(repo_root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip(),
    )
    (git_dir / "objects" / "info").mkdir(parents=True, exist_ok=True)
    _ = (git_dir / "objects" / "info" / "alternates").write_text(
        f"{common / 'objects'}\n",
        encoding="utf-8",
    )
    exclude = common / "info" / "exclude"
    if exclude.exists():
        (git_dir / "info").mkdir(parents=True, exist_ok=True)
        _ = shutil.copy2(exclude, git_dir / "info" / "exclude")
    head = _git(repo_root, "rev-parse", "HEAD").strip()
    _ = _git(gate_dir, "update-ref", "--no-deref", "HEAD", head)
    _ = _git(gate_dir, "read-tree", head)
    return head


class _SuiteSummary(TypedDict):
    """What :func:`summarize_suite` reads out of one suite's pytest output."""

    summary: str | None
    collected: int | None
    coverage: list[str]


class _GateRun(_SuiteSummary):
    """One gate suite that ran: its command, exit code, log and pytest summary."""

    run_id: str
    cell: str
    command: list[str]
    exit: int
    seconds: float
    database: str | None
    log: str


class _GateUnverified(TypedDict):
    """One gate suite whose cell could not be set up, so it never ran."""

    run_id: str
    cell: str
    command: list[str]
    exit: None
    unverified: str


def summarize_suite(log_text: str) -> _SuiteSummary:
    """Pull pytest's summary, collected count and coverage lines out of one suite's output."""
    summary = None
    collected = None
    coverage: list[str] = []
    for line in log_text.splitlines():
        stripped = line.strip()
        match = SUMMARY_PATTERN.match(stripped)
        if match:
            summary = match.group("summary")
        found = COLLECTED_PATTERN.search(stripped)
        if found:
            collected = int(found.group(1) or found.group(2))
        if stripped.startswith("TOTAL ") or "Required test coverage" in stripped:
            coverage.append(stripped)
    return {"summary": summary, "collected": collected, "coverage": coverage}


def gate(layout: Layout, suites: Sequence[str]) -> int:
    """Run the gate suites in the gate copy; write and print the bound result."""
    check_shared_checkout(layout.repo_root)
    repo_root = layout.repo_root
    with (
        flow_lease(layout) as flow,
        file_lock(layout.flow_dir / "gate.lock", blocking=False) as gate_lock,
    ):
        if not layout.gate_dir.exists() and _free_bytes(layout.base) < MIN_FREE_BYTES:
            msg = f"under {MIN_FREE_BYTES // 1024**3} GB free at {layout.base}; no gate copy"
            raise WorkspaceError(msg)
        holding = (*flow.holding, gate_lock)
        manifest = sync_copy(
            repo_root,
            layout.gate_dir,
            preserved=PRESERVED | {".git"},
            holding=holding,
        )
        head = build_gate_git(repo_root, layout.gate_dir)
        bound_to = snapshot_commit(
            repo_root,
            layout.gate_dir,
            manifest,
            head,
            PRESERVED | {".git"},
        )
        suite_results: dict[str, _GateRun | _GateUnverified] = {}
        result: dict[str, object] = {
            "flow": layout.flow,
            "at": _now(),
            "snapshot": bound_to,
            "head": head,
            "blobs": {
                name: _bench_common.git_blob_id(repo_root / name)
                for name in ("pyproject.toml", "uv.lock")
            },
            "tree_digest": manifest["tree_digest"],
            "package_digest": manifest["package_digest"],
            "suites": suite_results,
        }
        all_passed = True
        stopped_by: int | None = None
        for suite in suites:
            arguments, cell = GATE_SUITES[suite]
            run_id = new_run_id(layout.flow)
            log_path = layout.evidence / "logs" / f"{run_id}.log"
            try:
                env, database = gate_env(layout, cell)
                if suite == FLOOR_SUITE:
                    floor = ensure_floor_venv(layout, holding)
                    result["floor"] = floor
                    launch = [floor["python"], "-m", *arguments]
                else:
                    launch, env = uv_launch(layout.gate_dir, arguments, env)
            except WorkspaceError as error:
                suite_results[suite] = {
                    "run_id": run_id,
                    "cell": cell,
                    "command": list(arguments),
                    "exit": None,
                    "unverified": str(error),
                }
                all_passed = False
                _ = sys.stderr.write(f"gate {suite}: unverified: {error}\n")
                continue
            header = f"workspace gate {run_id} suite={suite} cell={cell} copy={layout.gate_dir}\n"
            _ = sys.stderr.write(header)
            started = time.monotonic()
            finished = stream(
                launch,
                env,
                log_path,
                header,
                cwd=layout.gate_dir,
                holding=holding,
            )
            code = finished.code
            ran: _GateRun = {
                "run_id": run_id,
                "cell": cell,
                "command": list(arguments),
                "exit": code,
                "seconds": round(time.monotonic() - started, 2),
                "database": database,
                "log": str(log_path),
                **summarize_suite(log_path.read_text(encoding="utf-8", errors="replace")),
            }
            suite_results[suite] = ran
            all_passed = all_passed and code == 0
            _append_gate_run(layout, ran, suite, manifest)
            if finished.stopped_by is not None:
                stopped_by = finished.stopped_by
                result["stopped_by"] = signal.Signals(stopped_by).name
                break
        if "pg" in suites:
            postgres = _running_postgres(repo_root)
            if postgres is not None:
                _ = postgres.drop_matching(layout.db_name("gate"), exact=True)
        result_path = layout.evidence / f"gate-{new_run_id(layout.flow)}.json"
        _write_json(result_path, result)
    print(f"gate {layout.flow}: bound to {bound_to}; result {result_path}")
    for suite, entry in suite_results.items():
        summary = entry.get("summary") or ("passed" if entry["exit"] == 0 else "failed")
        verdict = entry.get("unverified") or f"exit {entry['exit']}: {summary}"
        print(f"  {suite:<8} {entry['run_id']}  {verdict}")
        for line in entry.get("coverage", []):
            print(f"           {line}")
    if stopped_by is not None:
        print(f"  stopped by {signal.Signals(stopped_by).name}; later suites did not run")
        return 128 + stopped_by
    return 0 if all_passed else 1


def gate_env(layout: Layout, cell: str) -> tuple[dict[str, str], str | None]:
    """Return the gate copy's environment for ``cell`` and its Postgres database, if any."""
    if cell != "pg":
        return cell_env(layout, "gate", cell)
    database = layout.db_name("gate")
    postgres = Postgres(layout.repo_root)
    _ = postgres.ensure()
    postgres.recreate(database)
    return clean_env(FAKESHOP_PG_DSN=postgres.dsn(database)), database


def _append_gate_run(
    layout: Layout,
    entry: _GateRun,
    suite: str,
    manifest: _Manifest,
) -> None:
    record = {
        "run_id": entry["run_id"],
        "address": f"{layout.flow}/gate/{suite}",
        "item": "gate",
        "role": suite,
        "slot": "gate",
        "directory": str(layout.gate_dir),
        "synced_at": manifest["synced_at"],
        "tree_digest": manifest["tree_digest"],
        "package_file": str(layout.gate_dir / PACKAGE_DIR / "__init__.py"),
        "package_digest": manifest["package_digest"],
        "cell": entry["cell"],
        "databases": {"default": entry["database"]} if entry.get("database") else {},
        "copy_edits": [],
        "shared_moves": [],
        "command": entry["command"],
        "log": entry["log"],
        "exit": entry["exit"],
        "seconds": entry["seconds"],
    }
    layout.evidence.mkdir(parents=True, exist_ok=True)
    with layout.run_log.open("a", encoding="utf-8") as handle:
        _ = handle.write(json.dumps(record, sort_keys=True) + "\n")


# --------------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------------


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``build_parser``'s ``add_argument`` calls.

    ``name`` and ``handler`` are set by every subcommand and ``tail`` by ``main``; each
    other field is set only by the subcommands that declare it, and a handler reads only
    its own.
    """

    name: str
    handler: Callable[[_Args], int]
    tail: list[str]
    address: str
    cell: str
    fresh: bool
    manifest: str
    item: str
    baseline: str
    output: str | None
    check: str | None
    role: list[str] | None
    keep: list[str] | None
    records: list[str]
    flow: str
    suites: str
    status_flow: str | None


def _cmd_run(args: _Args) -> int:
    address = Address.parse(args.address)
    command = _worker_command(args.tail)
    layout = Layout.for_flow(address.flow)
    return execute(
        layout,
        address,
        lambda _directory, _run_id: command,
        cell=args.cell,
        fresh=args.fresh,
    )


def _cmd_prove(args: _Args) -> int:
    address = Address.parse(args.address)
    manifest = Path(args.manifest).expanduser().resolve()
    if not manifest.is_file():
        msg = f"manifest {manifest} is not a file"
        raise WorkspaceError(msg)
    extra = list(args.tail)
    overrides = prove_failability.workspace_options_in(extra)
    if overrides:
        msg = (
            f"prove passes --workspace, --scratch-root and --json itself, so the proof's "
            f"evidence stays in the flow folder; drop {', '.join(overrides)} from the "
            "arguments after --"
        )
        raise WorkspaceError(msg)
    layout = Layout.for_flow(address.flow)
    scratch = layout.evidence / "proofs" / address.evidence_slug / address.role

    def build(directory: Path, run_id: str) -> list[str]:
        return [
            "python",
            "scripts/prove_failability.py",
            str(manifest),
            "--workspace",
            str(directory),
            "--scratch-root",
            str(scratch),
            "--json",
            str(scratch / f"{run_id}.json"),
            *extra,
        ]

    return execute(layout, address, build, cell=args.cell, fresh=args.fresh)


def _cmd_path(args: _Args) -> int:
    address = Address.parse(args.address)
    layout = Layout.for_flow(address.flow)
    check_shared_checkout(layout.repo_root)
    with flow_lease(layout):
        directory = copy_path(layout, address)
    print(directory)
    return 0


def _cmd_baseline(args: _Args) -> int:
    ref = ItemRef.parse(args.item)
    layout = Layout.for_flow(ref.flow)
    check_shared_checkout(layout.repo_root)
    address = Address(ref.flow, ref.item, "before")
    with flow_lease(layout):
        with lease(layout, address, fresh=True) as held:
            manifest = held.manifest
            head = _git(layout.repo_root, "rev-parse", "HEAD").strip()
            sha = snapshot_commit(layout.repo_root, held.directory, manifest, head)
        with file_lock(layout.pool_lock):
            state = _held_state(layout)
            state["items"][ref.item] = {"item_baseline": sha, "at": _now()}
            _write_state(layout, state)
    print(f"ITEM_BASELINE={sha}")
    print(
        f"before: {address} -> {held.directory} "
        f"(tree {manifest['tree_digest']}, package {manifest['package_digest']})",
    )
    return 0


def _cmd_diff(args: _Args) -> int:
    check_shared_checkout(REPO_ROOT)
    diff = item_diff(REPO_ROOT, args.baseline, args.tail)
    if args.check:
        try:
            recorded = Path(args.check).read_bytes()
        except OSError as error:
            msg = f"--check {args.check}: {error}"
            raise WorkspaceError(msg) from error
        if recorded != diff:
            print(f"{args.check}: does not match the tree; tree gives {diff.splitlines()[-1]!r}")
            return 1
        print(f"{args.check}: matches")
    elif args.output:
        _ = Path(args.output).write_bytes(diff)
    else:
        _ = sys.stdout.buffer.write(diff)
    return 0


def _cmd_release(args: _Args) -> int:
    ref = ItemRef.parse(args.item)
    released = release(Layout.for_flow(ref.flow), ref.item, args.role or (), args.keep or ())
    print(f"released {len(released)} copy(ies)" + "".join(f"\n  {line}" for line in released))
    return 0


def _cmd_gc(args: _Args) -> int:
    for line in gc(Layout.for_flow(args.flow)):
        print(line)
    return 0


def _cmd_status(args: _Args) -> int:
    for line in status(REPO_ROOT, args.status_flow):
        print(line)
    return 0


def _cmd_audit(args: _Args) -> int:
    all_ok = True
    for record in args.records:
        lines, ok = audit_record(REPO_ROOT, Path(record))
        print("\n".join(lines))
        all_ok = all_ok and ok
    return 0 if all_ok else 1


def _cmd_gate(args: _Args) -> int:
    suites = [suite.strip() for suite in args.suites.split(",") if suite.strip()]
    unknown = sorted(set(suites) - set(GATE_SUITES))
    if unknown or not suites:
        msg = f"--suites takes a subset of {', '.join(GATE_SUITES)}; got {args.suites!r}"
        raise WorkspaceError(msg)
    return gate(Layout.for_flow(args.flow), suites)


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").partition("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="name", required=True)

    run = commands.add_parser(
        "run",
        help="run a command in the address's copy",
        usage="%(prog)s <address> [--cell CELL] [--fresh] -- <what follows `uv run`>",
    )
    _ = run.add_argument("address", help="<flow>/<item>/<role>")
    _ = run.add_argument("--cell", choices=CELLS, default="default")
    _ = run.add_argument(
        "--fresh",
        action="store_true",
        help="resync the copy from the shared tree first",
    )
    run.set_defaults(handler=_cmd_run)

    prove = commands.add_parser(
        "prove",
        help="run prove_failability.py in the address's copy",
        usage="%(prog)s <address> <manifest> [--cell CELL] [--fresh] [-- <extra args>]",
    )
    _ = prove.add_argument("address", help="<flow>/<item>/<role>")
    _ = prove.add_argument("manifest", help="proof manifest (JSON)")
    _ = prove.add_argument("--cell", choices=CELLS, default="default")
    _ = prove.add_argument(
        "--fresh",
        action="store_true",
        help="resync the copy from the shared tree first",
    )
    prove.set_defaults(handler=_cmd_prove)

    path = commands.add_parser("path", help="print the address's copy directory")
    _ = path.add_argument("address", help="<flow>/<item>/<role>")
    path.set_defaults(handler=_cmd_path)

    baseline = commands.add_parser("baseline", help="ITEM_BASELINE + the pinned before copy")
    _ = baseline.add_argument("item", help="<flow>/<item>")
    baseline.set_defaults(handler=_cmd_baseline)

    diff_parser = commands.add_parser(
        "diff",
        help="an item's diff since its baseline, new files included, sha256-sealed",
        usage="%(prog)s <ITEM_BASELINE> [--output FILE | --check FILE] -- <paths...>",
    )
    _ = diff_parser.add_argument("baseline", help="the item's ITEM_BASELINE sha")
    diff_target = diff_parser.add_mutually_exclusive_group()
    _ = diff_target.add_argument("--output", help="write the diff here instead of stdout")
    _ = diff_target.add_argument(
        "--check",
        help="exit 1 unless this file holds exactly the diff the tree gives now",
    )
    diff_parser.set_defaults(handler=_cmd_diff)

    release_parser = commands.add_parser("release", help="return an item's copies to the pool")
    _ = release_parser.add_argument("item", help="<flow>/<item>")
    _ = release_parser.add_argument(
        "--role",
        action="append",
        help="release only this role's copy (repeatable)",
    )
    _ = release_parser.add_argument(
        "--keep",
        action="append",
        help="release every copy but this role's (repeatable), e.g. --keep before",
    )
    release_parser.set_defaults(handler=_cmd_release)

    audit = commands.add_parser("audit", help="bind every run id a record cites")
    _ = audit.add_argument("records", nargs="+", help="record files to audit")
    audit.set_defaults(handler=_cmd_audit)

    gate_parser = commands.add_parser("gate", help="run the final gate suites in a gate copy")
    _ = gate_parser.add_argument("flow")
    _ = gate_parser.add_argument(
        "--suites",
        default=LOCAL_GATE_SUITE,
        help=(
            f"comma-separated subset of {', '.join(GATE_SUITES)} (default: {LOCAL_GATE_SUITE}; "
            "the other suites run in GitHub Actions unless the maintainer names them)"
        ),
    )
    gate_parser.set_defaults(handler=_cmd_gate)

    status_parser = commands.add_parser("status", help="describe copies, runs and leases")
    _ = status_parser.add_argument("status_flow", metavar="flow", nargs="?")
    status_parser.set_defaults(handler=_cmd_status)

    gc_parser = commands.add_parser("gc", help="delete everything the flow holds")
    _ = gc_parser.add_argument("flow")
    gc_parser.set_defaults(handler=_cmd_gc)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one command; a refusal prints its reason and exits 125 (run/prove) or 1.

    Everything after the first ``--`` is the worker's command (``run``),
    extra ``prove_failability.py`` arguments (``prove``) or the paths
    (``diff``), split off before parsing so options such as ``--cell`` may
    follow the address.
    """
    words = list(sys.argv[1:] if argv is None else argv)
    tail: list[str] = []
    if "--" in words:
        split = words.index("--")
        words, tail = words[:split], words[split + 1 :]
    parser = build_parser()
    args = parser.parse_args(words, namespace=_Args())
    args.tail = tail
    if tail and args.name not in {"run", "prove", "diff"}:
        parser.error(f"{args.name} takes nothing after --")
    try:
        return args.handler(args)
    except WorkspaceError as error:
        print(f"workspace: {error}", file=sys.stderr)
        return REFUSED if args.name in {"run", "prove"} else 1


def _cli() -> NoReturn:
    """Run :func:`main` as the script does, ending by the stop signal that stopped the run.

    :func:`main` returns ``128 + N`` for in-process callers; the process then
    dies by ``N`` (``scripts/_stop_signals.py::exit_with``).
    """
    _stop_signals.exit_with(main())


if __name__ == "__main__":
    _cli()
