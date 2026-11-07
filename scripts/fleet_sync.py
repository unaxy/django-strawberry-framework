"""Keep the private working copies, their pins and evidence, and main's commits in step across the fleet.

Every fleet machine online in Tailscale that holds this repository at
``~/projects/django-strawberry-framework`` gets the same copies under its own
``.work/`` (``scripts/work.py`` owns that folder; its docstring is the copy
contract), so an agent never has to remember where work lives. Agents work
independently, each in its own copy, so syncing is copying: a copy goes from the
one machine that edits it to every other machine, never back.

Machines
    Tailscale's peers with ``Online`` true, plus this machine (``tailscale status
    --json``; the binary on ``PATH``, else ``/usr/local/bin/tailscale``,
    ``/usr/bin/tailscale`` or the macOS app's). A peer matches a
    ``docs/fleet/machines.json`` row when its hostname or MagicDNS name resolves to
    the row (``fleet.canonical``: its name or one of its aliases); it is then
    reached as the row's ``ssh`` alias, else as its MagicDNS name. Every remote
    call is one ssh with the fleet's options (``fleet.ssh_argv``: batch mode, a
    connect timeout, a keepalive) running the peer's own ``scripts/fleet_sync.py
    agent`` (its ``.venv`` Python, else ``python3``), so both ends apply the same
    rules; ``--remote-scripts DIR`` runs the scripts in
    ``DIR`` on the peer instead, for a peer whose main predates this script. A
    peer qualifies when that call answers, its checkout is at
    ``~/projects/django-strawberry-framework`` (a repository elsewhere is reported,
    never synced), it shares this checkout's root commit, its checkout ignores
    ``.work/`` (else every copy would dirty its tree and stop the desktop's
    ``git-autosync``), and it has ``rsync``. A Windows peer is reported "not
    supported yet" and never half synced: work.py's process census and locks,
    ``sh`` and ``rsync`` are POSIX here. A qualifying peer no row lists is synced
    and reported with a suggested ``machines.json`` row; the list is never written.
    Machines are named, and stored names read, by ``scripts/fleet.py``'s rule (its
    "Identity"): a listed machine is its row's name everywhere, and ``sync`` and
    ``handoff`` refuse on a host no row names.

One writer per copy
    Every copy has a home machine (``home`` in its work.py note; an older note's
    ``host``). Every other qualifying machine holds a replica: the same folder
    under its own ``.work/``, its note ``replica=true`` with ``home``,
    ``syncedtree`` (work.py's content tree of what the last sync wrote),
    ``syncedhead``, a clone's ``syncedrefs`` (a digest of every ref, loose or
    packed, ``refs/stash`` included), ``syncedfrom`` and ``syncedat``. A replica
    is never synced back, and work.py's ``save``, ``land`` and ``rm`` refuse it
    (naming its home). A replica has changed since its last sync when its content
    tree is not ``syncedtree``, its ``HEAD`` is not ``syncedhead`` or its refs are
    not ``syncedrefs`` (a commit, a side branch or a stash counts even when the
    content and ``HEAD`` are as they were; a note without ``syncedhead`` is not
    judged by it, and a clone's note without ``syncedrefs``, written before it
    existed, counts any ref file newer than ``syncedat`` as changed: the transfer
    gave every ref it brought the home's mtime, so a newer one, a stash or a side
    branch made here, is a ref a fresh replica would not hold, and an unreadable
    ``syncedat`` counts as changed). A worktree's branches and stash live in
    its machine's own repository, which no sync replaces, so only a clone's refs
    are judged.
    ``handoff <name> [--to M]`` moves the home (default: to this machine): it
    first syncs the copy fresh from its home and carries the home's pins under
    its name that ``M`` lacks (so the pin record the promotion writes names no pin
    ``M``'s store lacks), then marks the home's copy a replica of ``M`` and
    promotes ``M``'s, then re-points every other replica it reaches. A replica
    with commits or edits since its last sync while the home's copy did not
    change (content and ``HEAD``) is promoted as it is (its work is kept, nothing
    is overwritten). Each handoff writes its lineage into every note it
    reaches (``generation`` one up, the old home appended to ``formerhomes``; both
    carried to replicas): a replica a handoff missed (its machine offline) still
    records a former home, and is taken as the newest home's replica (refreshed and
    re-pointed by that home's next sync, removed by that home's tombstone) because
    the home it records is one the newer note lists as former and its generation is
    lower (``work.later_home``). With no home reached, a replica whose recorded home
    is not reached (offline) is promoted only with ``--force-offline-home``; when the
    old home returns, the two homes are a conflict that names the newer handoff,
    nothing overwritten.

What a run moves, home to replica (only pairs that include this machine: a copy
two other machines hold is reported, for their own runs)
    Clones: the whole folder minus ``.venv``, ``__pycache__``, ``.pytest_cache``,
    ``.ruff_cache``, ``.mypy_cache``, ``node_modules`` and ``*.pyc``, and minus the
    git directory's per-machine files (``config``, ``hooks/``, ``*.lock``,
    ``dsf-work-*``). A new replica starts as ``git init`` (this platform's
    ``core.*``), then receives the objects, refs, ``HEAD`` and index; its
    ``parent`` remote is pointed at this machine's own checkout (the same layout
    on every machine), push ``no-push``, work.py's copy config applied, the start
    pin set, and ``dsf-work-venv-stale`` written in its git directory so
    ``work.py run`` rebuilds the ``.venv`` with ``uv sync --frozen`` (no venv is
    built during a sync). Worktrees: their ``.git`` file points at the source
    repository, so it never travels; the target gets the worktree's ``HEAD``
    commit (a bundle over the ssh pipe, no ref created), ``git worktree add
    --detach`` at the same path and commit, work.py's lock reason, then the
    working files with the same exclusions. ``rsync -rlpt --delete`` inside the
    copy folder; the receiver's excluded files (its ``.venv``, its config) stay.
    Before the transfer the replica is marked ``syncing`` with the moment
    (``syncingat``, taken before the replica is checked, less 2 s for a filesystem
    or an rsync that keeps whole-second mtimes), its ``HEAD`` then, and the home's
    ``HEAD``, content tree and refs the transfer brings, and its content paths then
    are listed in its git directory (``dsf-work-syncing-paths``, which no transfer
    carries). ``finish`` marks it synced and clears them only when the replica then
    holds exactly what the transfer brought; a commit, edit or ref written on
    either side during the transfer leaves it ``syncing`` with its last sync's
    marks and is reported as a conflict, for the next run to judge. The run then
    asks the home at once for its digest of each path the replica holds as neither
    tree has it, and the replica records each it still holds exactly so
    (``dsf-work-syncing-written``): a home save the transfer copied, so a home that
    saves that file again before the next run leaves nothing in doubt. A replica
    still ``syncing`` (cut short, or so left) is completed by the next run while it
    holds no work of its own: its ``HEAD`` the one before the transfer, the one it
    brought or the home's now; its refs either recorded one, the home's now, or no
    ref file newer than ``syncingat``; its content the last sync's, the
    transfer's, or else (half written) each content file whose mode and blob are
    the last sync's or the transfer's entry for it or what the record says the
    transfer wrote, and each other content file and listed path now gone exactly
    as the home holds it now (the home's digest of those paths, asked for in the
    run). Content is judged by blob and mode, not mtime, so a ``chmod`` or a ``cp
    -p`` here is doubted like any edit. A commit, a ref, an edit, a mode change or
    a deletion the home does not hold makes it changed, kept and reported. Gaps,
    each keeping more or losing nothing: a home that saves a file twice during one
    transfer, or a record the run could not make (the home unreached after the
    transfer), reads as local work; a tree object the replica's store lacks (a
    transfer cut short before the objects) puts every file that differs from the
    other tree in doubt, which the home's digests settle; a ref file a clock ahead
    of this one's wrote reads as written here; a ref deleted here while
    ``syncing`` leaves no newer file, and the transfer brings it back; a mode
    change git does not read (``core.fileMode`` off) is no content.

    Pins: every ``refs/work/<name>/<leaf>`` of ``.work/pins.git`` both ways,
    create-only; one ref with different commits on two machines is a conflict, both
    kept. A pin whose commit the target's pins already reach is linked there with no
    bundle; the rest travel as a bundle over the ssh pipe whose negatives (the
    target's pin commits) leave out any a tip is an ancestor of, so a copy made at an
    older main never makes an empty bundle (the copy's ``HEAD`` bundle for a worktree
    likewise). A pin a tombstone records dropping (that leaf at that commit), and any
    pin of a name held by a replica of an incarnation whose home ran ``rm
    --drop-saves``, is never carried, so a dropped save never comes back.

    Evidence: ``.work/evidence/<stem>/`` file by file, both ways, union, never
    deleted. A file on one side only is copied over; one that differs moves from
    the side that changed since the last sync with that peer to the side that did
    not, when it is also the newer; otherwise it is reported. The last sync's
    state per peer is ``.work/fleet/evidence-<peer>.json`` on this machine.

    Main: commits only, never working-tree state. Each peer's ``main`` is fetched
    into this repository's object store (no ref, no ``FETCH_HEAD``). A peer
    strictly ahead fast-forwards this machine's main only while ``HEAD`` is
    ``refs/heads/main``, no work.py ``land`` runs (its lock is held across the
    fast-forward), no merge, rebase, cherry-pick, revert or bisect is in progress,
    and ``git merge --ff-only`` accepts it (it refuses when a dirty path would
    change). A peer behind is left to that peer's own run; diverged is reported,
    never merged. Coexists with the Linux desktop's ``git-autosync`` (fast-forward
    from origin while clean): both only fast-forward, and ``.work/`` is ignored.

    Tombstones: ``.work/tombstones/`` file by file, both ways, before any copy is
    planned; union, create-only, never deleted by a sync (``work.py gc`` prunes
    them after 30 days). A home's ``work.py rm`` (``--discard`` and ``gc``
    included) writes one: name, home, the copy's identity (its note's
    ``incarnation``, else ``<start>@<created>``), its handoff lineage, whether
    ``--drop-saves`` dropped its saves, the pins it dropped, when and by whom (an
    ``rm`` of a name holding pins alone writes one recording those pins). A machine
    a tombstone reaches drops the pins it records while it holds no copy under the
    name.

    Deletions: a replica is removed only by a tombstone its home (or a later home
    of it, above) left for the replica's own identity, so a later copy reusing the
    name is never removed by an older one's tombstone; a tombstone saying
    ``--drop-saves`` drops the replica's pins under the name with it. A home that
    lacks the copy and left no such tombstone (its ``.work/`` wiped, lost or
    restored from an old backup) removed nothing:
    the replica, maybe the last copy, is kept and reported (``handoff <name>`` to
    make it the home, or ``work.py rm --discard <name>`` there, which keeps it in
    the trash as below). A home holding a later copy under an older replica's
    name (:func:`same_copy` false: another ``incarnation``, or for a note without
    one another ``start`` or ``created``) never overwrites that replica: with the
    tombstone of the replica's identity the replica is removed first and the new
    copy replicated by the next run, without one the copy is a conflict. A tombstoned
    replica is removed through work.py's own ``remove`` (census and checks) only
    while it is unchanged since its last sync and nothing works in it, otherwise
    reported; the agent checks the tombstone again on its own side, and the
    folder is kept in ``.work/trash/<name>-<seconds>-kept`` for 7 days
    (``work.TRASH_RETENTION_SECONDS``), restorable, before ``work.py gc``
    deletes it.

Conflicts (that copy stops; both sides kept and reported with how to resolve)
    A replica with commits or edits since its last sync (``HEAD``, a side branch
    and a stash count, a sync cut short included, and a commit or edit made while
    a transfer ran); a replica whose home lacks it with no
    tombstone for it; a replica of an earlier copy under the name its home now
    uses for another, with no tombstone for it; two machines that both hold a copy as its home; a replica
    of a third machine where this one is home; a pin ref with different commits
    on two machines; evidence both sides changed.

Safety
    Nothing is written while a process has its current directory in it (work.py's
    census on the machine written: a replica refreshed or removed, a home demoted
    by a handoff; a census that cannot tell skips the copy). A home's copy is only
    read, busy or not: what the replica received is compared with the home's
    content as read before the transfer, and a read that raced an edit is
    reported and completed by the next run. Nothing is
    synced with a machine while a ``work.py land`` runs on either side. One run per
    machine at a time: ``.work/fleet.lock``, a kernel lock this run holds, and on
    each peer a ``hold`` the peer's agent keeps for the run's length (released
    when the ssh pipe closes, however the run ends); every write a peer's agent
    makes checks the hold's token. A run deletes nothing outside ``.work/`` and
    writes the main working tree only through the guarded fast-forward.

Known gaps
    - An edit made in a replica while a sync runs can be lost: the census sees
      only processes whose current directory is in the copy, and replicas are
      not workspaces (one writer per copy).
    - A home that saves the same file twice within one transfer reads as local
      work on the replica, which stays changed (kept and reported) until
      ``work.py rm --discard <name>`` there, which keeps it in the trash.
    - A clone replica whose note predates ``syncedrefs`` is judged by ref mtimes,
      so once ``git gc`` packs its refs (a newer ``packed-refs``) it reads as
      changed and every sync refuses it.
    - Gitignored files in a replica are not content: a refresh (``rsync
      --delete``) replaces or deletes them.

Commands
    ``status`` (default)
        Read-only: machines found, qualified or why not; per copy its home, its
        replicas with freshness (``fresh``, ``stale``, ``changed``, ``syncing``)
        and conflicts; main ahead or behind per machine (commits a peer has and
        this machine lacks read ``unknown`` until a sync fetches them).
    ``sync [--dry-run] [--machine M]... [--copy NAME]... [--main-only]``
        Sync with every qualifying peer (or those ``--machine`` names: a row
        name, ssh alias or machine name). ``--copy`` limits the run to those copies
        (their pins and evidence) and leaves main alone; ``--main-only`` syncs
        main alone. ``--dry-run`` writes nothing but fetches peers' main commits
        into the object store so it can say what a fast-forward would do.
    ``handoff <name> [--to M] [--force-offline-home]``
        Move a copy's home (above).
    ``--json`` on each prints one document for agents. Exit codes: ``0`` synced
    or clean, ``1`` a conflict or skipped work, ``2`` bad setup (no Tailscale, an
    unreadable machine list, a checkout outside ``~/projects``, Windows here, and
    for ``sync`` and ``handoff`` a host no row names).

Running it periodically
    Nothing installs a schedule; the maintainer decides. A cron line
    (``*/10 * * * * cd ~/projects/django-strawberry-framework &&
    .venv/bin/python scripts/fleet_sync.py sync --json >> ~/.cache/fleet-sync.log
    2>&1``), a
    systemd user timer beside ``git-autosync.timer`` on Linux, or a launchd
    agent with ``StartInterval`` on macOS each fit; a run that finds another
    holding the lock skips, so overlapping runs are harmless.

Standard library plus ``scripts/work.py``, ``scripts/fleet.py`` and
``scripts/_git.py`` for the copy, machine and git rules (``scripts/fleet.py``
owns the machine list and the ssh options, ``scripts/_git.py`` the repository root). Every agent, this
machine's included, runs on its checkout's ``.venv`` Python (``python3`` when there
is none): removing a replica goes through work.py's ``remove``, which reads
``scripts/workspace.py`` and needs the project's packages. Run it from the
checkout as ``uv run python scripts/fleet_sync.py``.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import dataclasses
import hashlib
import json
import os
import selectors
import shlex
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path, PurePosixPath
from typing import IO, TYPE_CHECKING, NoReturn

try:
    import _git as _git_runner
    import fleet
    import work
except ModuleNotFoundError:  # imported as ``scripts.fleet_sync`` (repo root on path)
    from scripts import _git as _git_runner
    from scripts import fleet, work

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable, Mapping, Sequence

#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads

REPO_ROOT = _git_runner.CHECKOUT_ROOT
#: Where the checkout lives on every machine, relative to the home folder.
CHECKOUT = PurePosixPath("projects") / "django-strawberry-framework"
TAILSCALE_PATHS = (
    "/usr/local/bin/tailscale",
    "/usr/bin/tailscale",
    "/Applications/Tailscale.app/Contents/MacOS/Tailscale",
)
#: Tailscale's ``OS`` values for the machines a fleet checkout can live on.
TAILSCALE_OS = {"macos": "macos", "linux": "linux", "windows": "windows"}
#: The remote wrapper's own exit codes.
NO_CHECKOUT = 103
NO_SCRIPT = 104
HOLDER = "holder"
#: Regenerable or per-platform files no transfer carries.
EXCLUDES = (
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "*.pyc",
)
#: A clone's git-directory files that belong to the machine, not the copy.
CLONE_GIT_EXCLUDES = (
    "/.git/config",
    "/.git/hooks/",
    "/.git/**.lock",
    "/.git/dsf-work-*",
)
#: A worktree's ``.git`` file names its own machine's repository.
WORKTREE_GIT_EXCLUDES = ("/.git",)
#: Note keys a replica carries over from its home's copy.
NOTE_CARRIED = (
    "name",
    "form",
    "purpose",
    "owner",
    "host",
    "start",
    "created",
    "incarnation",
    "generation",
    "formerhomes",
    "adopted",
    "restoredfrom",
    work.PINS_NOTE,
)
IN_PROGRESS = (
    "MERGE_HEAD",
    "rebase-merge",
    "rebase-apply",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_LOG",
)
#: Note keys ``prepare`` writes for one transfer and ``finish`` clears: ``syncing``, when it
#: started (``syncingat``, this machine's clock), the ``HEAD`` before it, the home's ``HEAD``,
#: content tree and refs fingerprint (:func:`refs_fingerprint`) it brings.
SYNCING_KEYS = (
    "syncing",
    "syncingat",
    "syncingfrom",
    "syncinghead",
    "syncingtree",
    "syncingrefs",
)
#: The replica's content paths before a transfer (NUL separated), in its git directory where no
#: transfer reaches (``dsf-work-*``): a path it lost while ``syncing`` is a deletion to judge.
SYNCING_PATHS = "dsf-work-syncing-paths"
#: What a transfer that left the replica ``syncing`` wrote (JSON ``{path: file_digest}``, ``""``
#: a deletion), each entry the home held and the replica still held right after it: a path still
#: so is the transfer's, not local work, though the home has saved it again since.
SYNCING_WRITTEN = "dsf-work-syncing-written"
#: Seconds ``syncingat`` is set back: an mtime a filesystem or an rsync truncates to the whole
#: second still reads as newer than a transfer that began within it.
MTIME_MARGIN = 2.0
#: Agent operations that write, each checked against the hold's token. The read operations
#: (``probe``, ``inventory``, ``digests``, ``pins-export``, ``head-export``) are not: the
#: token binds a write to the held run, it is no access control (ssh is), and a read changes
#: nothing a run could race.
WRITES = frozenset(
    {
        "prepare",
        "finish",
        "transferred",
        "remove",
        "set-home",
        "pins-import",
        "commit-import",
        "prepare-evidence",
        "tombstones-import",
        "pins-link",
    },
)
CALL_TIMEOUT = 600.0
PROBE_TIMEOUT = 60.0
#: Seconds a peer's ``hold`` may take to print its token.
HOLD_TIMEOUT = 60.0
#: Seconds rsync may go without moving data before it gives up (its ``--timeout``).
RSYNC_IO_TIMEOUT = 120
#: Seconds one ``git fetch`` of a peer's main may take.
FETCH_TIMEOUT = 600.0

#: The wrapper a peer runs: find the checkout and its scripts, then the agent.
REMOTE_WRAPPER = """\
repo=$HOME/projects/django-strawberry-framework
[ -d "$repo/.git" ] || { echo "no checkout at $repo" >&2; exit 103; }
scripts=$1
shift
case $scripts in
  "") scripts=$repo/scripts ;;
  "~/"*) scripts=$HOME/${scripts#"~/"} ;;
esac
[ -f "$scripts/fleet_sync.py" ] || { echo "no fleet_sync.py in $scripts" >&2; exit 104; }
py=$repo/.venv/bin/python
[ -x "$py" ] || py=python3
exec "$py" "$scripts/fleet_sync.py" agent --repo "$repo" "$@"
"""


class FleetError(Exception):
    """A refusal or failure; the message says why and what to do."""


class SetupError(FleetError):
    """The run cannot start here (exit 2)."""


class ConflictError(FleetError):
    """A replica holds work of its own the transfer would overwrite; reported as a conflict."""


# --------------------------------------------------------------------------------------------
# JSON narrowing
# --------------------------------------------------------------------------------------------


def _object(value: object) -> dict[str, object]:
    return value if fleet.is_json_object(value) else {}


def _string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _strings(value: object) -> list[str]:
    return [item for item in value if isinstance(item, str)] if fleet.is_json_array(value) else []


def _string_map(value: object) -> dict[str, str]:
    return {key: item for key, item in _object(value).items() if isinstance(item, str)}


def _decode(raw: bytes, where: str) -> dict[str, object]:
    try:
        document = _loads(raw.decode("utf-8", "replace"))
    except ValueError:
        msg = f"{where} printed no JSON: {_last_line(raw)}"
        raise FleetError(msg) from None
    return _object(document)


def _last_line(raw: bytes) -> str:
    lines = [line.strip() for line in raw.decode("utf-8", "replace").splitlines() if line.strip()]
    return lines[-1] if lines else "no output"


# --------------------------------------------------------------------------------------------
# Locks
# --------------------------------------------------------------------------------------------


def _lock_busy(path: Path) -> bool:
    """Return whether another process holds the kernel lock on ``path`` (a missing file: no)."""
    if not path.is_file():
        return False
    descriptor = os.open(path, os.O_RDWR)
    try:
        work._lock_file(descriptor)
    except OSError:
        return True
    finally:
        os.close(descriptor)
    return False


@contextlib.contextmanager
def holding(repo: Path) -> Generator[str, None, None]:
    """Hold ``.work/fleet.lock`` and publish a fresh holder token; yield the token.

    Raises:
        FleetError: another run (or another machine's hold) has it, or a ``land`` runs.

    """
    _ = work.ensure_sentinel(repo)
    lock = work.work_dir(repo) / work.FLEET_LOCK
    work.check_layout(repo)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            work._lock_file(descriptor)
        except OSError:
            msg = f"another fleet_sync run holds {lock}; this one skips"
            raise FleetError(msg) from None
        if _lock_busy(work.work_dir(repo) / work.LAND_LOCK):
            msg = "a work.py land is in progress; no sync until it ends"
            raise FleetError(msg)
        folder = work._container(repo, work.FLEET, create=True)
        token = work._token()
        holder = folder / HOLDER
        _ = holder.write_text(token, encoding="utf-8")
        try:
            yield token
        finally:
            holder.unlink(missing_ok=True)
    finally:
        os.close(descriptor)


def check_token(repo: Path, token: str) -> None:
    """Refuse a write unless the run that holds ``.work/fleet.lock`` published ``token``.

    Raises:
        FleetError: no run holds the lock, or another run does.

    """
    holder = work.work_dir(repo) / work.FLEET / HOLDER
    try:
        published = holder.read_text(encoding="utf-8")
    except OSError:
        published = ""
    if not token or published != token or not _lock_busy(work.work_dir(repo) / work.FLEET_LOCK):
        msg = "this write is not part of the fleet_sync run holding this machine's lock"
        raise FleetError(msg)


# --------------------------------------------------------------------------------------------
# Agent: the operations each machine runs on its own .work/
# --------------------------------------------------------------------------------------------


def _git(root: Path, *args: str) -> str:
    return work._git(root, *args)


def _rsync_version() -> str:
    rsync = shutil.which("rsync")
    if rsync is None:
        return ""
    completed = subprocess.run(
        [rsync, "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.splitlines()[0].strip() if completed.stdout else "rsync"


def agent_probe(repo: Path) -> dict[str, object]:
    """Return what qualifies this machine: identity, checkout, main, locks, tools."""
    roots = _git_runner.run_git(repo, "rev-list", "--max-parents=0", "HEAD").stdout.split()
    ignored = _git_runner.run_git(repo, "check-ignore", "-q", f"{work.WORK_DIR}/")
    expected = Path.home() / CHECKOUT
    return {
        "id": work.machine_id(),
        "os": {"darwin": "macos", "win32": "windows"}.get(sys.platform, sys.platform),
        "repo": str(repo),
        "at_checkout": repo.resolve() == expected.resolve(),
        "roots": sorted(roots),
        "branch": work._branch(repo),
        "main": work._resolve_commit(repo, work.LANDING_BRANCH),
        "ignored": ignored.returncode == 0,
        "land_busy": _lock_busy(work.work_dir(repo) / work.LAND_LOCK),
        "fleet_busy": _lock_busy(work.work_dir(repo) / work.FLEET_LOCK),
        "rsync": _rsync_version(),
        "python": ".".join(str(part) for part in sys.version_info[:3]),
    }


def _stem(name: str) -> str:
    return work.parse_name(name).stem if work._valid(name) else name


def copy_record(repo: Path, copy: work.Copy) -> dict[str, object]:
    """Return what a sync needs to know of one copy: home, replica state, content, users.

    The carried note always holds ``work.PINS_NOTE``: for a note older than the key, the pins
    ``work.legacy_pins`` attributes to the copy from this machine's pins.
    """
    note = copy.note
    carried = work.attributed_note(repo, note)
    record: dict[str, object] = {
        "name": copy.name,
        "form": copy.form,
        "path": str(copy.path) if copy.path is not None else "",
        "home": work.home_of(note) if note else "",
        "replica": work.is_replica(note),
        "syncing": note.get("syncing") == "true",
        "syncedtree": note.get("syncedtree", ""),
        "syncedhead": note.get("syncedhead", ""),
        "changed": False,
        "doubts": {},
        "note": {key: carried[key] for key in NOTE_CARRIED if key in carried},
        "head": "",
        "tree": "",
        "refs": "",
        "problem": "",
        "ignored": False,
        "users": None,
    }
    container = work.work_dir(repo) / (work.CLONES if copy.form == "clone" else work.WORKTREES)
    if copy.hazard is not None:
        record["problem"] = f"unsafe, never touched: {copy.hazard}"
    elif copy.path is None or not copy.present:
        record.update(problem="its folder is gone", ignored=True)
    elif work._abs(copy.path).parent != work._abs(container):
        record.update(problem=f"a harness copy at {copy.path}, outside .work/", ignored=True)
    elif not note.get("name"):
        record.update(problem="an unregistered folder (no work.py note)", ignored=True)
    elif not copy.healthy:
        record["problem"] = "its .git is missing or broken (work.py repair)"
    else:
        record["head"] = head = work._head(copy.path)
        try:
            record["tree"] = tree = work.content_tree(copy.path)
            record["refs"] = refs_fingerprint(copy.path, copy.form)
            if work.is_replica(note):
                doubts = replica_doubts(note, copy.path, tree, head, copy.form)
                record["changed"] = doubts is None or doubts.any
                record["doubts"] = {} if doubts is None else doubts.as_json()
        except (work.WorkError, FleetError) as error:
            record["problem"] = f"its content cannot be read: {error}"
        record["users"] = work.cwd_users(copy.path)
    return record


def _evidence_files(folder: Path) -> dict[str, list[int]]:
    """Return ``{relative path: [size, mtime seconds]}`` for every file under ``folder``."""
    files: dict[str, list[int]] = {}
    for directory, dirnames, filenames in os.walk(folder):
        dirnames[:] = [name for name in dirnames if name not in EXCLUDES]
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            path = Path(directory) / name
            with contextlib.suppress(OSError):
                info = path.lstat()
                files[path.relative_to(folder).as_posix()] = [info.st_size, int(info.st_mtime)]
    return files


def agent_inventory(repo: Path, names: Sequence[str]) -> dict[str, object]:
    """Return every copy (or those ``names``), their pins and their evidence."""
    work.check_layout(repo)
    wanted = set(names)
    copies = {
        name: copy_record(repo, copy)
        for name, copy in work.discover(repo).items()
        if copy.form != "pins" and (not wanted or name in wanted)
    }
    pin_map = {
        f"{name}/{leaf}": sha
        for name, leaves in work.pins(repo).items()
        if not wanted or name in wanted
        for leaf, sha in leaves.items()
    }
    stems = {_stem(name) for name in wanted}
    evidence: dict[str, object] = {}
    root = work.work_dir(repo) / work.EVIDENCE
    if root.is_dir():
        for folder in sorted(root.iterdir()):
            if work.copy_hazard(repo, folder, work.EVIDENCE) is not None or not folder.is_dir():
                continue
            if not wanted or folder.name in stems:
                evidence[folder.name] = _evidence_files(folder)
    graves = [
        tombstone.as_json()
        for tombstone in work.tombstones(repo)
        if not wanted or tombstone.name in wanted
    ]
    return {
        "copies": copies,
        "pins": pin_map,
        "evidence": evidence,
        "tombstones": graves,
    }


def _copy_or_none(repo: Path, name: str) -> work.Copy | None:
    copy = work.discover(repo).get(name)
    return None if copy is None or copy.form == "pins" else copy


def _unset_note(copy_root: Path, form: str, key: str) -> None:
    _ = _git_runner.run_git(
        copy_root,
        "config",
        work._scope(form),
        "--unset",
        f"{work.NOTE_SECTION}.{key}",
    )


def _refuse_in_use(copy_root: Path, what: str) -> None:
    users = work.cwd_users(copy_root)
    if users is None and os.name != "nt":
        msg = f"{what}: the process census cannot tell whether a process works in it"
        raise FleetError(msg)
    if users:
        msg = f"{what}: process {', '.join(users)} has its current directory inside it"
        raise FleetError(msg)


def _content_paths(copy_root: Path) -> list[str]:
    """Return the copy's content paths: every file git tracks or does not ignore."""
    listed = work._git(
        copy_root,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )
    return list(dict.fromkeys(path for path in listed.split("\0") if path))


def _newer(path: Path, since: float) -> bool:
    try:
        return path.lstat().st_mtime > since
    except FileNotFoundError:
        return False


def _inside(copy_root: Path, relative: str) -> Path:
    """Return ``copy_root / relative``, refusing a path that could name a file outside the copy.

    Each folder on the way is ``lstat``-ed: a symlinked (or non-folder) one, an absolute path
    and a ``..`` part are refused; a folder that is not there leaves a path to no file.

    Raises:
        FleetError: the path is absolute, climbs with ``..`` or passes a symlinked folder.

    """
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).is_absolute() or ".." in parts:
        msg = f"{relative!r} is no path inside the copy"
        raise FleetError(msg)
    folder = copy_root
    for part in parts[:-1]:
        folder /= part
        try:
            mode = folder.lstat().st_mode
        except (FileNotFoundError, NotADirectoryError):
            break
        if not stat.S_ISDIR(mode):
            msg = f"{relative!r} passes {folder.relative_to(copy_root).as_posix()}, no real folder"
            raise FleetError(msg)
    return copy_root.joinpath(*parts)


def file_digest(copy_root: Path, relative: str) -> str:
    """Return a digest of a copy's file as a transfer writes it, ``""`` when there is none.

    Its kind (link, executable, plain) and bytes, read raw on both machines: rsync copies the
    bytes and the mode, so a file the transfer wrote has the digest the home's file has.

    Raises:
        FleetError: ``relative`` could name a file outside the copy (:func:`_inside`).

    """
    path = _inside(copy_root, relative)
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            kind, data = "l", os.fsencode(path.readlink())
        elif stat.S_ISREG(info.st_mode):
            kind, data = ("x" if info.st_mode & 0o111 else "f"), path.read_bytes()
        else:
            return ""
    except (FileNotFoundError, NotADirectoryError):
        return ""
    return f"{kind}{hashlib.sha256(data).hexdigest()}"


def _tree_entries(copy_root: Path, tree: str) -> dict[str, str] | None:
    """Return ``{path: "<mode> <blob>"}`` of every file ``tree`` holds, ``None`` without it.

    ``None`` when the copy's object store lacks the tree (or a subtree): a transfer cut short
    before the objects, or a pruned one.
    """
    if not tree:
        return None
    try:
        listed = work._git(copy_root, "ls-tree", "-r", "-z", "--full-tree", tree)
    except work.WorkError:
        return None
    entries: dict[str, str] = {}
    for record in listed.split("\0"):
        meta, _tab, path = record.partition("\t")
        if path:
            mode, oid = meta.partition(" ")[0], meta.rpartition(" ")[2]
            entries[path] = f"{mode} {oid}"
    return entries


def _written(copy_root: Path) -> dict[str, str]:
    """Return what a transfer recorded writing (:data:`SYNCING_WRITTEN`), ``{}`` when nothing."""
    try:
        raw = work._git_path(copy_root, SYNCING_WRITTEN).read_bytes()
    except FileNotFoundError:
        return {}
    return _string_map(_decode(raw, SYNCING_WRITTEN))


def refs_fingerprint(copy_root: Path, form: str) -> str:
    """Return a digest of every ref of a clone (``refs/stash`` included), ``""`` for a worktree.

    A worktree's branches and stash live in its machine's own repository, which no transfer
    replaces, so only a clone's refs (loose and packed alike) are a replica's to keep.
    """
    if form != "clone":
        return ""
    listed = work._git(copy_root, "for-each-ref", "--format=%(objectname) %(refname)")
    return hashlib.sha256(listed.encode("utf-8")).hexdigest()


def _refs_written_since(copy_root: Path, since: float) -> bool:
    """Return whether a clone's loose ref or ``packed-refs`` is newer than ``since``."""
    if _newer(work._git_path(copy_root, "packed-refs"), since):
        return True
    for directory, _dirnames, filenames in os.walk(work._git_path(copy_root, "refs")):
        if any(_newer(Path(directory) / name, since) for name in filenames):
            return True
    return False


def _syncing_paths(copy_root: Path) -> list[str]:
    try:
        raw = work._git_path(copy_root, SYNCING_PATHS).read_bytes()
    except FileNotFoundError:
        return []
    return [path for path in os.fsdecode(raw).split("\0") if path]


@dataclasses.dataclass(frozen=True)
class Doubts:
    """What a replica holds since a transfer that began (``syncing``) only its home can vouch for.

    A ``HEAD`` that is neither the one before the transfer nor the one it brought (``head``), a
    clone's refs that are neither and were written after the transfer began (``refs``), and,
    content being neither tree (``tree``), each content file newer than the transfer's start or
    lost since it (``paths``: path to :func:`file_digest`, ``""`` for a lost one). All are the
    transfer's while the home holds them so now: then nothing local is lost by completing it.
    """

    head: str = ""
    refs: str = ""
    tree: str = ""
    paths: Mapping[str, str] = dataclasses.field(default_factory=dict[str, str])

    @property
    def any(self) -> bool:
        """Return whether anything needs the home's word."""
        return bool(self.head or self.refs or self.paths)

    def as_json(self) -> dict[str, object]:
        """Return the doubts as a JSON object."""
        return {
            "head": self.head,
            "refs": self.refs,
            "tree": self.tree,
            "paths": dict(self.paths),
        }

    @classmethod
    def parse(cls, raw: object) -> Doubts:
        """Return the doubts an inventory entry carries."""
        record = _object(raw)
        return cls(
            head=_string(record, "head"),
            refs=_string(record, "refs"),
            tree=_string(record, "tree"),
            paths=_string_map(record.get("paths")),
        )

    def vouched(
        self,
        head: str,
        tree: str,
        refs: str,
        digests: Mapping[str, str],
    ) -> bool:
        """Return whether a home at ``head``, ``tree`` and ``refs`` holds all of it.

        ``digests`` are the home's :func:`file_digest` of the doubted paths (needed only while
        the replica's content is not the home's whole ``tree``).
        """
        return (
            (not self.head or self.head == head)
            and (not self.refs or self.refs == refs)
            and (
                not self.paths
                or self.tree == tree
                or all(
                    path in digests and digests[path] == digest
                    for path, digest in self.paths.items()
                )
            )
        )


def same_copy(home: Mapping[str, str], replica: Mapping[str, str]) -> bool:
    """Return whether the ``replica`` note names the copy the ``home`` note does.

    Both carry an ``incarnation``: equal ones. Otherwise (a note older than it) its
    ``start`` and ``created`` both match; two notes without any of the three are taken as
    one copy, as before identities existed.
    """
    ours, theirs = home.get("incarnation", ""), replica.get("incarnation", "")
    if ours and theirs:
        return ours == theirs
    return all(home.get(key, "") == replica.get(key, "") for key in ("start", "created"))


def leftover_pins_detail(name: str, where: str, leftover: Mapping[str, str]) -> str:
    """Return why ``name`` gets no replica ``where``: it holds the ``leftover`` pins of another copy."""
    listed = ", ".join(f"{leaf} {sha[:12]}" for leaf, sha in sorted(leftover.items()))
    return (
        f"{name} {where} holds leftover pins from an earlier copy ({listed}), which "
        f"`work.py new` refuses the name for; no replica made, nothing dropped: `work.py rm "
        f"{name} --drop-saves` there to drop them, or rename"
    )


def _homed(note: Mapping[str, str], home: str) -> dict[str, str]:
    """Return ``note`` (a carried note, which holds no ``home``) with its copy's ``home``."""
    return {**note, "home": home}


def replica_doubts(
    note: Mapping[str, str],
    copy_root: Path,
    tree: str,
    head: str,
    form: str,
) -> Doubts | None:
    """Return what a replica holds since its last sync: ``None`` work of its own, else :class:`Doubts`.

    Settled: its content ``tree`` differs from ``syncedtree``, its ``head`` from
    ``syncedhead`` (a note without it is not judged by it) or a clone's refs
    (:func:`refs_fingerprint`) from ``syncedrefs`` (a note without it: a ref file newer than
    ``syncedat``, :func:`_refs_since_sync`): its own work, no doubt. While ``syncing`` (a
    transfer that may have been cut short, or one whose result differed from what its home
    held when read) only the home can tell: :class:`Doubts`, empty when the replica is as
    before the transfer or as it brought it. Each content file whose mode and blob are
    neither the last sync's nor the transfer's entry, nor the digest the transfer recorded
    writing (:data:`SYNCING_WRITTEN`), was written here or saved at home during the transfer;
    a content path listed before the transfer (:data:`SYNCING_PATHS`) and gone now was
    deleted here or by the transfer. rsync ``-t`` gives every ref file it writes the home's
    mtime, so a ref file newer than ``syncingat`` was written here or at home meanwhile.
    """
    if note.get("syncing") != "true":
        synced_head = note.get("syncedhead", "")
        synced_refs = note.get("syncedrefs", "")
        if form != "clone":
            refs_changed = False
        elif synced_refs:
            refs_changed = refs_fingerprint(copy_root, form) != synced_refs
        else:
            refs_changed = _refs_since_sync(copy_root, note)
        changed = (
            tree != note.get("syncedtree")
            or (bool(synced_head) and head != synced_head)
            or refs_changed
        )
        return None if changed else Doubts()
    try:
        since = float(note.get("syncingat", ""))
    except ValueError:
        return None
    head_doubt = "" if head in {note.get("syncingfrom", ""), note.get("syncinghead", "")} else head
    refs_doubt = ""
    known_refs = {note.get("syncedrefs", ""), note.get("syncingrefs", "")} - {""}
    if form == "clone":
        refs = refs_fingerprint(copy_root, form)
        if refs not in known_refs and _refs_written_since(copy_root, since):
            refs_doubt = refs
    paths: dict[str, str] = {}
    if tree not in {note.get("syncedtree", ""), note.get("syncingtree", "")} - {""}:
        current = _tree_entries(copy_root, tree)
        if current is None:
            return None
        known = [
            entries
            for entries in (
                _tree_entries(copy_root, note.get(key, ""))
                for key in ("syncedtree", "syncingtree")
            )
            if entries is not None
        ]
        written = _written(copy_root)
        for relative, entry in current.items():
            if any(entries.get(relative) == entry for entries in known):
                continue
            digest = file_digest(copy_root, relative)
            if written.get(relative) != digest:
                paths[relative] = digest
        for relative in _syncing_paths(copy_root):
            if relative not in current and written.get(relative) != "":
                paths[relative] = ""
    return Doubts(head_doubt, refs_doubt, tree if paths else "", paths)


def _refs_since_sync(copy_root: Path, note: Mapping[str, str]) -> bool:
    """Return whether a clone's ref file is newer than its last sync (``syncedat``).

    For a note older than ``syncedrefs``: the transfer gave each ref it brought the home's
    mtime, so a newer ref file (a stash, a side branch, a tag made here) is one a fresh replica
    would not hold. An unreadable ``syncedat`` counts as newer.
    """
    try:
        since = float(note.get("syncedat", ""))
    except ValueError:
        return True
    return _refs_written_since(copy_root, since)


def _replica_unchanged(
    copy: work.Copy,
    copy_root: Path,
    home: tuple[str, str, str] = ("", "", ""),
    digests: Mapping[str, str] | None = None,
) -> str:
    """Return the replica's content tree, refusing one with commits or edits since its last sync.

    ``home`` (``HEAD``, content tree, refs fingerprint) and ``digests`` (:func:`file_digest`
    per doubted path) are what its home holds now, which vouches for :class:`Doubts`.

    Raises:
        FleetError: the replica holds work of its own, or doubts its home does not vouch for.

    """
    tree = work.content_tree(copy_root)
    doubts = replica_doubts(copy.note, copy_root, tree, work._head(copy_root), copy.form)
    if doubts is None or (doubts.any and not doubts.vouched(*home, digests or {})):
        msg = f"{copy.name}: the replica has commits or edits since its last sync; they are kept"
        raise FleetError(msg)
    return tree


def agent_prepare(
    repo: Path,
    name: str,
    form: str,
    home: str,
    head: str,
    tree: str,
    carried: Mapping[str, str],
    refs: str = "",
    digests: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Ready ``name`` as a replica of ``home`` at ``head``: made when new, marked ``syncing``.

    The mark records the moment, the ``HEAD`` before the transfer, and the home's ``head``,
    content ``tree`` and ``refs`` it brings (:data:`SYNCING_KEYS`), and the content paths
    before it (:data:`SYNCING_PATHS`): what :func:`replica_doubts` needs to tell a run cut
    short from local work after it, and :func:`agent_finish` to tell what the transfer
    brought. ``digests`` are the home's :func:`file_digest` of the paths an earlier transfer
    left in doubt. ``carried`` is the home copy's note (:data:`NOTE_CARRIED`): an existing
    replica of another copy under the name (:func:`same_copy`) is never refreshed. A replica
    of this copy recording a former home of ``home`` (a handoff its machine missed:
    ``work.later_home``) is taken as ``home``'s and re-pointed.

    A name holding pins ``carried`` does not attribute to the copy (``work.pin_belongs``:
    pins an earlier copy left, which ``work.py new`` refuses the name for) gets no replica:
    removing it would drop them (:func:`leftover_pins_detail`).

    Raises:
        FleetError: the folder holds a copy that is not an unchanged replica of ``home``'s
            copy, the name holds another copy's pins, or a process works in it.

    """
    _ = work.parse_name(name)
    if not work._resolve_commit(repo, head) and form == "worktree":
        return {"need_commit": True}
    copy = _copy_or_none(repo, name)
    container = work.CLONES if form == "clone" else work.WORKTREES
    path = work.work_dir(repo) / container / name
    if copy is None:
        leftover = work.foreign_pins(carried, work.pins(repo).get(name, {}))
        if leftover:
            raise FleetError(leftover_pins_detail(name, "here", leftover))
        _ = work.ensure_sentinel(repo)
        _ = work.claim_name(repo, name)
        try:
            _ = work._container(repo, container, create=True)
            path.mkdir()
            _make_replica(repo, name, form, path, head)
            work.write_note(
                path,
                form,
                {
                    "name": name,
                    "form": form,
                    "home": home,
                    "replica": "true",
                    **_syncing_note("", head, tree, refs, time.time()),
                },
            )
        except BaseException:
            work._undo_new(repo, form, path, name)
            raise
        return {"path": str(path), "created": True}
    copy_root = work._live(copy)
    recorded = work.home_of(copy.note)
    former = (
        recorded != home
        and same_copy(carried, copy.note)
        and work.later_home(_homed(carried, home), copy.note)
    )
    if copy.form != form or not work.is_replica(copy.note) or (recorded != home and not former):
        msg = (
            f"{name} here is not a replica of {home}'s {form} "
            f"(home {recorded}, replica {work.is_replica(copy.note)})"
        )
        raise FleetError(msg)
    if not same_copy(carried, copy.note):
        msg = f"{name} here is a replica of an earlier copy under that name; not overwritten"
        raise FleetError(msg)
    _refuse_in_use(copy_root, name)
    # Taken before the check: a ref or a path written between the check and the mark is newer
    # than ``syncingat`` (or listed), never one the transfer is taken to have brought.
    started = time.time() - MTIME_MARGIN
    listed = "".join(f"{path}\0" for path in _content_paths(copy_root))
    _ = _replica_unchanged(copy, copy_root, (head, tree, refs), digests)
    _ = work._git_path(copy_root, SYNCING_PATHS).write_bytes(os.fsencode(listed))
    values = _syncing_note(work._head(copy_root), head, tree, refs, started)
    if former:
        values["home"] = home
    work.write_note(copy_root, form, values)
    if form == "worktree" and work._head(copy_root) != head:
        _ = _git(copy_root, "reset", "--quiet", head)
    return {"path": str(copy_root), "created": False}


def _syncing_note(
    before: str,
    head: str,
    tree: str,
    refs: str,
    started: float,
) -> dict[str, str]:
    """Return the :data:`SYNCING_KEYS` note of a transfer that began at ``started``."""
    return {
        "syncing": "true",
        "syncingat": str(started),
        "syncingfrom": before,
        "syncinghead": head,
        "syncingtree": tree,
        "syncingrefs": refs,
    }


def _unset_syncing(copy_root: Path, form: str) -> None:
    for key in SYNCING_KEYS:
        _unset_note(copy_root, form, key)
    work._git_path(copy_root, SYNCING_PATHS).unlink(missing_ok=True)
    work._git_path(copy_root, SYNCING_WRITTEN).unlink(missing_ok=True)


def _make_replica(
    repo: Path,
    name: str,
    form: str,
    path: Path,
    head: str,
) -> None:
    """Make the empty replica a transfer fills: ``git init`` (clone) or a detached worktree."""
    if form == "clone":
        _ = _git(path, "init", "--quiet")
        return
    work._ensure_worktree_config(repo)
    _ = _git(repo, "worktree", "add", "--quiet", "--detach", str(path), head)
    _ = _git(repo, "worktree", "lock", "--reason", f"{work.LOCK_REASON_PREFIX}{name}", str(path))


def agent_finish(
    repo: Path,
    name: str,
    home: str,
    source: str,
    carried: Mapping[str, str],
) -> dict[str, object]:
    """Finish a transfer: the clone's remote and config, the note, the start pin, the stale venv.

    The replica is marked synced (``syncedtree``, ``syncedhead``, a clone's ``syncedrefs``)
    only while its content, ``HEAD`` and refs are what ``prepare`` recorded the transfer
    brings; otherwise (an edit or commit on either side during the transfer) it stays
    ``syncing`` with its last sync's marks, so the next run judges it (:func:`replica_doubts`)
    instead of taking work made here meanwhile as synced. ``synced`` in the answer says which;
    ``doubts`` (:func:`file_digest` per path, ``""`` a deletion) are the paths the next run
    would doubt, for the run to ask the home about at once (:func:`agent_transferred`).

    Raises:
        FleetError: ``name`` is not a replica of ``home`` this run is filling.

    """
    copy = _copy_or_none(repo, name)
    if copy is None or not work.is_replica(copy.note) or work.home_of(copy.note) != home:
        msg = f"{name} is no replica of {home} here"
        raise FleetError(msg)
    copy_root = work._live(copy)
    if copy.form == "clone":
        remotes = _git(copy_root, "remote").split()
        if "parent" in remotes:
            _ = _git(copy_root, "remote", "set-url", "parent", str(repo))
        else:
            _ = _git(copy_root, "remote", "add", "parent", str(repo))
        _ = _git(copy_root, "remote", "set-url", "--push", "parent", work.NO_PUSH)
    work._apply_copy_config(copy_root, copy.form)
    tree, head = work.content_tree(copy_root), work._head(copy_root)
    refs = refs_fingerprint(copy_root, copy.form)
    note = copy.note
    expected_refs = note.get("syncingrefs", "")
    synced = (
        note.get("syncing") == "true"
        and tree == note.get("syncingtree")
        and head == note.get("syncinghead")
        and (not expected_refs or refs == expected_refs)
    )
    values = {key: value for key, value in carried.items() if key in NOTE_CARRIED}
    values.update({"home": home, "replica": "true"})
    if synced:
        values.update(
            {
                "syncedtree": tree,
                "syncedhead": head,
                "syncedfrom": source,
                "syncedat": str(time.time()),
            },
        )
        if refs:
            values["syncedrefs"] = refs
    work.write_note(copy_root, copy.form, values)
    doubted: Mapping[str, str] = {}
    if synced:
        _unset_syncing(copy_root, copy.form)
    else:
        doubts = replica_doubts(note, copy_root, tree, head, copy.form)
        doubted = {} if doubts is None else doubts.paths
    _ = work._git_path(copy_root, work.VENV_STALE).write_text("", encoding="utf-8")
    start = values.get("start", "")
    if start and work._resolve_commit(copy_root, start):
        _ = work.publish_pin(repo, copy_root, start, name, work.START_PIN)
    return {
        "path": str(copy_root),
        "tree": tree,
        "synced": synced,
        "doubts": dict(doubted),
    }


def agent_transferred(
    repo: Path,
    name: str,
    home: str,
    digests: Mapping[str, str],
) -> dict[str, object]:
    """Record each path of ``digests`` the replica still holds so as the transfer's own writing.

    ``digests`` are the paths :func:`agent_finish` doubted whose digest the home held right
    after the transfer: a home save the transfer copied. Each the replica still holds exactly
    so (``""``: still gone) is added to :data:`SYNCING_WRITTEN`, which :func:`replica_doubts`
    then takes as the transfer's, though the home saves the file again; one changed here since
    is left out, so it stays in doubt. Nothing is recorded unless the replica is ``syncing``.

    Raises:
        FleetError: ``name`` is not a replica of ``home`` here.

    """
    copy = _copy_or_none(repo, name)
    if copy is None or not work.is_replica(copy.note) or work.home_of(copy.note) != home:
        msg = f"{name} is no replica of {home} here"
        raise FleetError(msg)
    copy_root = work._live(copy)
    if copy.note.get("syncing") != "true":
        return {"recorded": 0}
    current = set(_content_paths(copy_root))
    kept = {
        path: digest
        for path, digest in digests.items()
        if digest == (file_digest(copy_root, path) if path in current else "")
    }
    if kept:
        record = {**_written(copy_root), **kept}
        target = work._git_path(copy_root, SYNCING_WRITTEN)
        _ = target.write_text(json.dumps(record, sort_keys=True), encoding="utf-8")
    return {"recorded": len(kept)}


def agent_digests(repo: Path, name: str, data: bytes) -> dict[str, object]:
    """Return :func:`file_digest` of each content path a JSON ``paths`` list names (``""``: none).

    A read, so not token-checked (:data:`WRITES`). A path that could name a file outside the
    copy (:func:`_inside`: absolute, ``..``, a symlinked folder on the way) refuses the call.

    Raises:
        FleetError: no copy ``name`` here, or a path could name a file outside it.

    """
    copy = _copy_or_none(repo, name)
    if copy is None:
        msg = f"no copy {name} here"
        raise FleetError(msg)
    copy_root = work._live(copy)
    wanted = _strings(_decode(data, "paths").get("paths"))
    for path in wanted:
        _ = _inside(copy_root, path)
    content = set(_content_paths(copy_root))
    return {
        "digests": {
            path: file_digest(copy_root, path) if path in content else "" for path in wanted
        },
    }


def agent_remove(
    repo: Path,
    name: str,
    home: str,
    identity: str,
) -> dict[str, object]:
    """Move a replica of ``home`` its home removed into ``.work/trash`` (work.py's ``remove``).

    Only while this machine holds a tombstone that buries it (``work.Tombstone.buries``: the
    replica's own identity, ``identity``, from ``home`` or a later home of it) and the replica
    is unchanged since its last sync; the folder stays in the trash for
    ``work.TRASH_RETENTION_SECONDS``. A tombstone saying ``--drop-saves`` drops the replica's
    pins under the name too: those its note attributes to it and those the tombstones record;
    another copy's pins under the name stay, answered as ``kept`` (``{leaf: commit}``).

    Raises:
        FleetError: it is no replica of ``home``, no tombstone of ``home`` names its
            identity, it changed since its sync, or work.py refuses.

    """
    copy = _copy_or_none(repo, name)
    if copy is None:
        return {"removed": False}
    if not work.is_replica(copy.note) or work.home_of(copy.note) != home:
        msg = f"{name} here is not a replica of {home}; not removed"
        raise FleetError(msg)
    own = work.copy_identity(copy.note)
    graves = [grave for grave in work.tombstones(repo) if grave.buries(name, copy.note)]
    if not own or own != identity or not graves:
        msg = (
            f"{name}: no tombstone of {home} or a later home of it names this replica; not removed"
        )
        raise FleetError(msg)
    _ = _replica_unchanged(copy, work._live(copy))
    kept = work.remove(
        repo,
        copy,
        discard=True,
        drop_saves=any(grave.saves_dropped for grave in graves),
        keep_in_trash=True,
    )
    return {"removed": True, "kept": kept}


def agent_tombstones_import(repo: Path, data: bytes) -> dict[str, object]:
    """Write every tombstone a JSON list carries that this machine lacks; return their files.

    Each new tombstone's recorded pins are dropped here while no copy holds the name
    (``work.drop_buried_pins``).
    """
    created: list[str] = []
    listed = _decode(data, "tombstones").get("tombstones")
    names: set[str] = set()
    for raw in listed if fleet.is_json_array(listed) else []:
        tombstone = work.Tombstone.parse(raw)
        if tombstone is not None and work.write_tombstone(repo, tombstone):
            created.append(tombstone.file_name)
            names.add(tombstone.name)
    dropped = [
        f"{name}/{leaf}" for name in sorted(names) for leaf in work.drop_buried_pins(repo, name)
    ]
    return {"created": created, "dropped": dropped}


def agent_set_home(
    repo: Path,
    name: str,
    home: str,
    *,
    replica: bool,
    expect_tree: str,
    expect_head: str,
    lineage: tuple[str, str] = ("", ""),
    carried: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Point ``name``'s note at ``home``: demote to (or re-point) a replica, or promote it.

    ``lineage`` (``generation``, ``formerhomes``), when given, is the handoff's, written too.
    A promotion writes the old home's pin record ``carried`` holds (``work.PINS_NOTE``), so the
    new home attributes every pin the old one published, a replica kept unrefreshed (its own
    edits) included.

    Raises:
        FleetError: the content is not ``expect_tree`` or ``HEAD`` not ``expect_head``, a
            process works in a copy being demoted, or a promotion names another machine.

    """
    copy = _copy_or_none(repo, name)
    if copy is None:
        msg = f"no copy {name} here"
        raise FleetError(msg)
    copy_root = work._live(copy)
    tree = work.content_tree(copy_root)
    if (expect_tree and tree != expect_tree) or (
        expect_head and work._head(copy_root) != expect_head
    ):
        msg = f"{name} changed since the handoff read it; nothing moved"
        raise FleetError(msg)
    generation, former = lineage
    marks = {"generation": generation, "formerhomes": former} if generation else {}
    if not replica:
        if home != work.machine_id():
            msg = f"a promotion names this machine, not {home}"
            raise FleetError(msg)
        values = {"home": home, "replica": "false", **marks}
        if carried is not None and work.PINS_NOTE in carried:
            values[work.PINS_NOTE] = carried[work.PINS_NOTE]
        work.write_note(copy_root, copy.form, values)
        _unset_syncing(copy_root, copy.form)
        return {"tree": tree}
    values = {"home": home, "replica": "true", **marks}
    if not work.is_replica(copy.note):
        _refuse_in_use(copy_root, name)
        values.update({"syncedtree": tree, "syncedhead": work._head(copy_root)})
        values["syncedat"] = str(time.time())
        refs = refs_fingerprint(copy_root, copy.form)
        if refs:
            values["syncedrefs"] = refs
    work.write_note(copy_root, copy.form, values)
    return {"tree": tree}


def _write_bundle(repo: Path, folder: Path, args: Sequence[str]) -> bytes:
    """Return the bundle ``git bundle create`` makes of ``args`` in ``folder``, or ``b""``."""
    target = work._container(repo, work.FLEET, create=True) / f"out-{work._token()}.bundle"
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(folder),
                "bundle",
                "create",
                "--quiet",
                str(target),
                *args,
            ],
            capture_output=True,
            env=_git_runner.repository_env(),
            check=False,
        )
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", "replace").strip()
            msg = f"git bundle create failed: {detail}"
            raise FleetError(msg)
        return target.read_bytes()
    finally:
        target.unlink(missing_ok=True)


def _present(root: Path, oids: Iterable[str]) -> list[str]:
    return [oid for oid in oids if work._resolve_commit(root, oid)]


def _negatives(root: Path, tips: Iterable[str], haves: Iterable[str]) -> list[str]:
    """Return ``^<have>`` for each present have no tip is (or is an ancestor of).

    A tip a negative reaches is excluded from the bundle (a copy made at an older main, a
    start pin under a stale save), and a bundle left with nothing ``git bundle`` refuses
    ("Refusing to create empty bundle").
    """
    wanted = {tip for tip in tips if tip}
    return [
        f"^{oid}"
        for oid in _present(root, haves)
        if not any(work._is_ancestor(root, tip, oid) for tip in wanted)
    ]


def agent_pins_export(repo: Path, refs: Sequence[str], haves: Sequence[str]) -> bytes:
    """Return a bundle of the pin ``refs`` (``<name>/<leaf>``), less what ``haves`` reach."""
    store = work.pin_store(repo)
    if store is None or not refs:
        return b""
    full = [f"{work.PIN_PREFIX}{ref}" for ref in refs]
    tips = [work._resolve_commit(store, ref) for ref in full]
    return _write_bundle(repo, store, [*full, *_negatives(store, tips, haves)])


def _reached(store: Path, oid: str) -> bool:
    """Return whether a pin of ``store`` reaches ``oid`` (so every object it needs is there)."""
    if not work._resolve_commit(store, oid):
        return False
    listed = _git(
        store,
        "for-each-ref",
        "--count=1",
        "--contains",
        oid,
        "--format=%(refname)",
        work.PIN_PREFIX,
    )
    return bool(listed.strip())


def agent_pins_link(repo: Path, data: bytes) -> dict[str, object]:
    """Create each pin a JSON ``{"pins": {ref: commit}}`` names whose commit a pin here reaches.

    Such a pin needs no bundle (the objects are here); the answer lists those ``created``,
    the ``conflicts`` (held at another commit) and the ``missing`` a bundle must bring.
    """
    wanted = _string_map(_decode(data, "pins").get("pins"))
    store = work.pin_store(repo)
    created: list[str] = []
    conflicts: list[str] = []
    missing: list[str] = []
    for ref, oid in sorted(wanted.items()):
        name, _, leaf = ref.partition("/")
        if not work._valid(name) or not leaf or "/" in leaf:
            continue
        full = f"{work.PIN_PREFIX}{ref}"
        existing = work._resolve_commit(store, full) if store is not None else ""
        if existing:
            if existing != oid:
                conflicts.append(ref)
        elif (
            store is not None
            and _reached(store, oid)
            and work._git_ok(store, "update-ref", full, oid, "")
        ):
            created.append(ref)
        else:
            missing.append(ref)
    return {"created": created, "conflicts": conflicts, "missing": missing}


def _import_bundle(repo: Path, data: bytes) -> Path:
    folder = work._container(repo, work.FLEET, create=True)
    path = folder / f"in-{work._token()}.bundle"
    _ = path.write_bytes(data)
    return path


def agent_pins_import(repo: Path, data: bytes) -> dict[str, object]:
    """Create every pin a bundle carries that this store lacks; report the ones it holds otherwise."""
    if not data:
        return {"created": [], "conflicts": []}
    store = work.make_pin_store(repo)
    bundle = _import_bundle(repo, data)
    incoming = f"{work.INCOMING_PREFIX}{work._token()}/"
    created: list[str] = []
    conflicts: list[str] = []
    try:
        heads = _git(store, "bundle", "list-heads", str(bundle))
        _ = _git(
            store,
            "fetch",
            "--quiet",
            "--no-tags",
            "--no-write-fetch-head",
            str(bundle),
            f"{work.PIN_PREFIX}*:{incoming}*",
        )
        for line in heads.splitlines():
            oid, _, ref = line.partition(" ")
            if not ref.startswith(work.PIN_PREFIX):
                continue
            existing = work._resolve_commit(store, ref)
            if not existing and work._git_ok(store, "update-ref", ref, oid, ""):
                created.append(ref.removeprefix(work.PIN_PREFIX))
            elif work._resolve_commit(store, ref) != oid:
                conflicts.append(ref.removeprefix(work.PIN_PREFIX))
    finally:
        bundle.unlink(missing_ok=True)
        for ref in _git(store, "for-each-ref", "--format=%(refname)", incoming).split():
            _ = _git_runner.run_git(store, "update-ref", "-d", ref)
    return {"created": created, "conflicts": conflicts}


def agent_head_export(repo: Path, name: str, haves: Sequence[str]) -> bytes:
    """Return a bundle of the copy's ``HEAD`` commit, less what ``haves`` reach."""
    copy = _copy_or_none(repo, name)
    if copy is None:
        msg = f"no copy {name} here"
        raise FleetError(msg)
    copy_root = work._live(copy)
    head = work._head(copy_root)
    return _write_bundle(repo, copy_root, ["HEAD", *_negatives(copy_root, [head], haves)])


def agent_commit_import(repo: Path, data: bytes) -> dict[str, object]:
    """Bring a bundle's commit into the shared repository's objects: no ref, no ``FETCH_HEAD``."""
    bundle = _import_bundle(repo, data)
    try:
        heads = _git(repo, "bundle", "list-heads", str(bundle)).split()
        _ = _git(
            repo,
            "fetch",
            "--quiet",
            "--no-tags",
            "--no-write-fetch-head",
            str(bundle),
            "HEAD",
        )
    finally:
        bundle.unlink(missing_ok=True)
    return {"commit": heads[0] if heads else ""}


def agent_prepare_evidence(repo: Path, stem: str) -> dict[str, object]:
    """Make (or check) ``.work/evidence/<stem>`` for a transfer into it; return its path.

    Raises:
        FleetError: the folder is unsafe.

    """
    _ = work.ensure_sentinel(repo)
    folder = work._container(repo, work.EVIDENCE, create=True) / stem
    hazard = work.copy_hazard(repo, folder, work.EVIDENCE)
    if hazard is not None or "/" in stem or stem in {"", ".", ".."}:
        msg = f"evidence {stem}: {hazard or 'not a folder name'}"
        raise FleetError(msg)
    folder.mkdir(exist_ok=True)
    return {"path": str(folder)}


def agent_hold(repo: Path, stdin: IO[bytes], stdout: IO[str]) -> int:
    """Hold this machine's fleet lock until ``stdin`` closes; print the token first."""
    try:
        with holding(repo) as token:
            _ = stdout.write(json.dumps({"token": token}) + "\n")
            stdout.flush()
            _ = stdin.read()
    except (FleetError, work.WorkError) as error:
        _ = stdout.write(json.dumps({"error": str(error)}) + "\n")
        return 1
    return 0


def run_agent(args: _Args) -> int:
    """Run one agent operation against ``--repo``; JSON (or a bundle) on stdout."""
    repo = Path(args.repo).resolve()
    work.REPO_ROOT = repo
    # A peer names machines by its own list, which may predate this one's: read them here.
    args.home, args.source = work.canonical(args.home), work.canonical(args.source)
    args.former = ",".join(work.canonical(home) for home in args.former.split(",") if home)
    output: dict[str, object] | bytes
    try:
        work.refuse_locating_env()
        work.check_layout(repo)
        operation = args.operation
        if operation == "hold":
            return agent_hold(repo, sys.stdin.buffer, sys.stdout)
        if operation in WRITES:
            check_token(repo, args.token)
        output = _agent_output(repo, args)
    except (
        FleetError,
        work.WorkError,
        ImportError,
        OSError,
    ) as error:
        print(json.dumps({"error": f"{type(error).__name__}: {error}"}))
        return 1
    if isinstance(output, bytes):
        _ = sys.stdout.buffer.write(output)
        _ = sys.stdout.buffer.flush()
    else:
        print(json.dumps(output))
    return 0


def _agent_output(repo: Path, args: _Args) -> dict[str, object] | bytes:
    operation = args.operation
    if operation == "probe":
        return agent_probe(repo)
    if operation == "inventory":
        return agent_inventory(repo, args.copy)
    if operation in {"prepare", "finish"}:
        carried = _string_map(_decode(args.note.encode("utf-8"), "--note"))
        if operation == "finish":
            return agent_finish(repo, args.name, args.home, args.source, carried)
        return agent_prepare(
            repo,
            args.name,
            args.form,
            args.home,
            args.head,
            args.expect_tree,
            carried,
            args.refs,
            _string_map(_decode(args.digests.encode("utf-8"), "--digests")),
        )
    if operation == "digests":
        return agent_digests(repo, args.name, sys.stdin.buffer.read())
    if operation == "transferred":
        written = _string_map(_decode(args.digests.encode("utf-8"), "--digests"))
        return agent_transferred(repo, args.name, args.home, written)
    if operation == "remove":
        return agent_remove(repo, args.name, args.home, args.identity)
    if operation == "tombstones-import":
        return agent_tombstones_import(repo, sys.stdin.buffer.read())
    if operation == "set-home":
        return agent_set_home(
            repo,
            args.name,
            args.home,
            replica=args.replica == "yes",
            expect_tree=args.expect_tree,
            expect_head=args.head,
            lineage=(args.generation, args.former),
            carried=_string_map(_decode(args.note.encode("utf-8"), "--note")),
        )
    if operation == "pins-export":
        return agent_pins_export(repo, args.ref, args.have)
    if operation == "pins-import":
        return agent_pins_import(repo, sys.stdin.buffer.read())
    if operation == "pins-link":
        return agent_pins_link(repo, sys.stdin.buffer.read())
    if operation == "head-export":
        return agent_head_export(repo, args.name, args.have)
    if operation == "commit-import":
        return agent_commit_import(repo, sys.stdin.buffer.read())
    return agent_prepare_evidence(repo, args.name)


# --------------------------------------------------------------------------------------------
# Endpoints: this machine or a peer, reached the same way
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Endpoint:
    """A machine the run talks to: this one (``ssh`` empty) or a peer over ssh."""

    machine: str
    label: str
    ssh: str
    scripts: str = ""

    @property
    def local(self) -> bool:
        """Return whether this is the machine the run is on."""
        return not self.ssh

    def argv(self, *args: str) -> list[str]:
        """Return the argv that runs ``fleet_sync.py agent args`` on this machine."""
        if self.local:
            venv = REPO_ROOT / ".venv" / "bin" / "python"
            return [
                str(venv) if venv.is_file() else sys.executable,
                str(Path(__file__).resolve()),
                "agent",
                "--repo",
                str(REPO_ROOT),
                *args,
            ]
        command = " ".join(
            [
                "sh",
                "-c",
                shlex.quote(REMOTE_WRAPPER),
                "fleet-sync",
                shlex.quote(self.scripts),
                *(shlex.quote(arg) for arg in args),
            ],
        )
        return fleet.ssh_argv(self.ssh, command)

    def run(
        self,
        *args: str,
        stdin: bytes | None = None,
        timeout: float = CALL_TIMEOUT,
    ) -> subprocess.CompletedProcess[bytes]:
        """Run one agent operation; return the completed process (bytes)."""
        try:
            return subprocess.run(
                self.argv(*args),
                input=stdin,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            msg = f"{self.label}: `{args[0]}` timed out after {timeout:g}s"
            raise FleetError(msg) from None

    def call(self, *args: str, stdin: bytes | None = None) -> dict[str, object]:
        """Run one agent operation and return its JSON answer.

        Raises:
            FleetError: the call failed or the agent refused; the message says why.

        """
        completed = self.run(*args, stdin=stdin)
        if completed.returncode not in {0, 1}:
            msg = f"{self.label}: `{args[0]}` failed: {_last_line(completed.stderr)}"
            raise FleetError(msg)
        answer = _decode(completed.stdout, f"{self.label} `{args[0]}`")
        error = _string(answer, "error")
        if error or completed.returncode != 0:
            msg = f"{self.label}: {error or _last_line(completed.stderr)}"
            raise FleetError(msg)
        return answer

    def bytes_of(self, *args: str) -> bytes:
        """Run one agent operation whose answer is raw bytes (a bundle).

        Raises:
            FleetError: the call failed.

        """
        completed = self.run(*args)
        if completed.returncode != 0:
            detail = _last_line(completed.stdout) if completed.stdout else ""
            msg = f"{self.label}: `{args[0]}` failed: {detail or _last_line(completed.stderr)}"
            raise FleetError(msg)
        return completed.stdout

    def spec(self, path: str) -> str:
        """Return ``path`` as rsync names it on this machine."""
        return path if self.local else f"{self.ssh}:{path}"

    @contextlib.contextmanager
    def hold(self, local_token: str) -> Generator[str, None, None]:
        """Hold this machine's fleet lock for the block; yield the token its writes carry.

        Raises:
            FleetError: the machine is busy (another run, a land) or the hold failed.

        """
        if self.local:
            yield local_token
            return
        with subprocess.Popen(
            self.argv("hold"),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as process:
            try:
                line = (
                    _read_line(process.stdout, HOLD_TIMEOUT) if process.stdout is not None else b""
                )
                if line is None:
                    process.kill()
                    msg = f"{self.label}: the hold printed nothing in {HOLD_TIMEOUT:g}s"
                    raise FleetError(msg)
                try:
                    answer = _object(_loads(line.decode(errors="replace")))
                except ValueError:
                    answer = {}
                token = _string(answer, "token")
                if not token:
                    detail = _string(answer, "error") or "the hold printed no token"
                    msg = f"{self.label}: {detail}"
                    raise FleetError(msg)
                yield token
            finally:
                try:
                    _ = process.communicate(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    _ = process.communicate()


def _read_line(stream: IO[bytes], timeout: float) -> bytes | None:
    """Return ``stream``'s first line (without its newline), or ``None`` past ``timeout``.

    A stream that ends first returns what it held.
    """
    deadline = time.monotonic() + timeout
    descriptor = stream.fileno()
    data = b""
    with selectors.DefaultSelector() as selector:
        _ = selector.register(descriptor, selectors.EVENT_READ)
        while b"\n" not in data:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not selector.select(remaining):
                return None
            chunk = os.read(descriptor, 4096)
            if not chunk:
                break
            data += chunk
    return data.split(b"\n", 1)[0]


# --------------------------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Probe:
    """One machine's ``probe`` answer."""

    id: str
    os: str
    repo: str
    at_checkout: bool
    roots: tuple[str, ...]
    branch: str
    main: str
    ignored: bool
    land_busy: bool
    fleet_busy: bool
    rsync: str

    @classmethod
    def parse(cls, answer: Mapping[str, object]) -> Probe:
        """Return the probe an agent's JSON answer describes."""
        return cls(
            id=_string(answer, "id"),
            os=_string(answer, "os"),
            repo=_string(answer, "repo"),
            at_checkout=answer.get("at_checkout") is True,
            roots=tuple(_strings(answer.get("roots"))),
            branch=_string(answer, "branch"),
            main=_string(answer, "main"),
            ignored=answer.get("ignored") is True,
            land_busy=answer.get("land_busy") is True,
            fleet_busy=answer.get("fleet_busy") is True,
            rsync=_string(answer, "rsync"),
        )


@dataclasses.dataclass
class Machine:
    """One machine Tailscale lists: how it is reached and whether it qualifies."""

    label: str
    ssh: str
    os: str
    local: bool
    row: str
    reason: str = ""
    probe: Probe | None = None
    endpoint: Endpoint | None = None
    labels: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        """Return the machine's name: its row's, else its probe's, else its tailnet label.

        A listed machine is its row's name (:attr:`label` too), whatever it reports.
        """
        if self.row:
            return self.row
        return self.probe.id if self.probe is not None else (self.labels or ("?",))[0]

    @property
    def qualified(self) -> bool:
        """Return whether the run syncs with this machine."""
        return not self.reason and self.endpoint is not None

    def suggested_row(self) -> dict[str, object]:
        """Return a ``machines.json`` row for a qualifying machine no row lists."""
        return {
            "name": self.id,
            "ssh": self.ssh,
            "os": self.os,
            "repo": f"~/{CHECKOUT}",
            "weight": {"light": 1.0, "heavy": 1.0},
            "floors": {"light": {"min_mem_available_gib": 2, "min_disk_free_gib": 6}},
            "aliases": [],
        }


def tailscale_status() -> dict[str, object]:
    """Return ``tailscale status --json``.

    Raises:
        SetupError: no Tailscale binary, or it fails.

    """
    binary = shutil.which("tailscale") or next(
        (path for path in TAILSCALE_PATHS if Path(path).is_file()),
        None,
    )
    if binary is None:
        msg = "no tailscale binary (PATH, " + ", ".join(TAILSCALE_PATHS) + ")"
        raise SetupError(msg)
    try:
        completed = subprocess.run(
            [binary, "status", "--json"],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        msg = f"tailscale status failed: {error}"
        raise SetupError(msg) from None
    if completed.returncode != 0:
        msg = f"tailscale status failed: {_last_line(completed.stderr)}"
        raise SetupError(msg)
    return _decode(completed.stdout, "tailscale status")


def _labels(peer: Mapping[str, object]) -> tuple[str, ...]:
    dns = _string(peer, "DNSName").rstrip(".")
    found = [fleet.short_hostname(dns)] if dns else []
    host = _string(peer, "HostName")
    if host:
        found.append(fleet.short_hostname(host))
    return tuple(dict.fromkeys(label for label in found if label))


def discover_machines(
    status: Mapping[str, object],
    rows: Sequence[fleet.Machine],
    scripts: str,
) -> list[Machine]:
    """Return this machine and every online peer, each matched to its ``machines.json`` row."""
    machines: list[Machine] = []
    entries = [(_object(status.get("Self")), True)]
    entries += [(_object(peer), False) for peer in _object(status.get("Peer")).values()]
    for peer, local in entries:
        if not local and peer.get("Online") is not True:
            continue
        labels = _labels(peer)
        named = {fleet.canonical(label, rows) for label in labels}
        row = next((row for row in rows if row.name in named), None)
        os_name = TAILSCALE_OS.get(_string(peer, "OS").casefold(), _string(peer, "OS"))
        machine = Machine(
            label=row.name if row is not None else (labels or ("?",))[0],
            ssh="" if local else (row.ssh if row is not None else (labels or ("",))[0]),
            os=os_name,
            local=local,
            row=row.name if row is not None else "",
            labels=labels,
        )
        if os_name == "windows":
            machine.reason = (
                "Windows: not supported yet (work.py's process census and locks, sh and "
                "rsync are POSIX here); never half synced"
            )
        elif os_name not in TAILSCALE_OS:
            machine.reason = f"{os_name or 'unknown OS'}: not a fleet computer"
        elif not local and not machine.ssh:
            machine.reason = "no ssh name (no machines.json row and no MagicDNS name)"
        else:
            machine.endpoint = Endpoint(
                machine=machine.id if row is not None or labels else "",
                label=machine.label,
                ssh=machine.ssh,
                scripts="" if local else scripts,
            )
        machines.append(machine)
    return machines


def _named_by(machine: Machine, typed: str, rows: Sequence[fleet.Machine] | None = None) -> bool:
    """Return whether a ``--machine`` or ``--to`` value ``typed`` names ``machine``.

    As typed: its label, ssh name, row, id or a tailnet label. Or read as a stored name
    (``fleet.canonical`` of ``rows``, default this checkout's list): a row's alias, or a
    row's name or the id in any case or with a domain. An empty or blank ``typed`` names
    no machine, and no empty value of the machine's is matched.
    """
    if not typed.strip():
        return False
    known = {
        machine.label,
        machine.ssh,
        machine.row,
        machine.id,
        *machine.labels,
    } - {""}
    if typed in known:
        return True
    resolved = fleet.canonical(typed, rows, repo=REPO_ROOT)
    return bool(resolved) and resolved in {machine.row, machine.id}


def _this_member(rows: Sequence[fleet.Machine]) -> fleet.Machine:
    """Return this machine's row (``fleet.this_machine``).

    Raises:
        SetupError: no row is this machine; the message names it and the rows.

    """
    try:
        return fleet.this_machine(rows)
    except fleet.MachineListError as error:
        msg = f"not a fleet machine: {error}"
        raise SetupError(msg) from None


def qualify(machine: Machine, local: Probe | None) -> None:
    """Probe ``machine`` and record why it does not qualify (``reason``), if it does not."""
    endpoint = machine.endpoint
    if endpoint is None:
        return
    completed = endpoint.run("probe", timeout=PROBE_TIMEOUT)
    if completed.returncode == fleet.SSH_FAILED and not machine.local:
        machine.reason = f"unreachable over ssh {machine.ssh}: {_last_line(completed.stderr)}"
    elif completed.returncode == NO_CHECKOUT:
        machine.reason = f"no checkout at ~/{CHECKOUT} (a repository elsewhere is never synced)"
    elif completed.returncode == NO_SCRIPT:
        machine.reason = (
            "lacks scripts/fleet_sync.py (its main predates it); run with --remote-scripts"
        )
    elif completed.returncode != 0:
        machine.reason = f"probe failed: {_last_line(completed.stdout + completed.stderr)}"
    if machine.reason:
        machine.endpoint = None
        return
    try:
        probe = Probe.parse(_decode(completed.stdout, f"{machine.label} probe"))
    except FleetError as error:
        machine.reason = str(error)
        machine.endpoint = None
        return
    machine.probe = probe
    machine.endpoint = dataclasses.replace(endpoint, machine=machine.id)
    reasons = _disqualifications(probe, local)
    if reasons:
        machine.reason = "; ".join(reasons)
        if not machine.local:
            machine.endpoint = None


def _disqualifications(probe: Probe, local: Probe | None) -> list[str]:
    reasons: list[str] = []
    if not probe.at_checkout:
        reasons.append(f"its checkout {probe.repo} is not ~/{CHECKOUT}")
    if local is not None and probe is not local and set(probe.roots) != set(local.roots):
        reasons.append("another repository (its root commit differs)")
    if not probe.ignored:
        reasons.append(
            "its checkout does not ignore .work/ (copies would dirty its tree and stop "
            "git-autosync); its main needs the .gitignore rule first",
        )
    if not probe.rsync:
        reasons.append("no rsync")
    if probe.land_busy:
        reasons.append("a work.py land is in progress there")
    if probe.fleet_busy:
        reasons.append("another fleet_sync run holds its lock")
    return reasons


def find_machines(
    scripts: str,
    only: Sequence[str],
    *,
    member: bool = False,
) -> tuple[Machine, list[Machine]]:
    """Return this machine and every other machine Tailscale lists, probed in parallel.

    ``member`` (``sync``, ``handoff``: what writes records naming this machine) requires
    this machine to be a row of the list (``fleet.this_machine``) and Tailscale's ``Self``
    to resolve to that row; ``status`` only reads, so an unlisted host still reports.

    Raises:
        SetupError: Windows here, no Tailscale, an unreadable machine list, this checkout
            outside ``~/projects``, this machine unqualified, or (``member``) no row is this
            machine or Tailscale names it as another.

    """
    if sys.platform == "win32":
        msg = "fleet_sync.py does not run on Windows yet"
        raise SetupError(msg)
    try:
        rows = fleet.machines(REPO_ROOT)
    except fleet.MachineListError as error:
        msg = f"machine list: {error}"
        raise SetupError(msg) from None
    me = _this_member(rows) if member else None
    machines = discover_machines(tailscale_status(), rows, scripts)
    here = next((machine for machine in machines if machine.local), None)
    if here is None:
        msg = "tailscale lists no Self"
        raise SetupError(msg)
    if me is not None and here.row != me.name:
        msg = (
            f"Tailscale names this machine {here.label!r}, which resolves to "
            f"{here.row or 'no row'}, but this machine is {me.name!r}: give it its row's name "
            f"in Tailscale"
        )
        raise SetupError(msg)
    qualify(here, None)
    if (
        here.probe is None
        or not here.probe.at_checkout
        or not here.probe.ignored
        or not here.probe.rsync
    ):
        msg = f"this machine cannot sync: {here.reason or 'no probe'}"
        raise SetupError(msg)
    others = [machine for machine in machines if not machine.local]
    if only:
        others = [
            machine for machine in others if any(_named_by(machine, typed, rows) for typed in only)
        ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(len(others), 1)) as pool:
        for future in [pool.submit(qualify, machine, here.probe) for machine in others]:
            future.result()
    return here, others


# --------------------------------------------------------------------------------------------
# Inventories and the plan
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class CopyInfo:
    """One copy as one machine's inventory reports it."""

    name: str
    form: str
    path: str
    home: str
    replica: bool
    syncing: bool
    syncedtree: str
    syncedhead: str
    #: Whether a replica may hold commits or edits since its last sync (:func:`replica_doubts`,
    #: judged on the machine that holds it): work of its own, or :attr:`doubts`.
    changed: bool
    #: What only the home can vouch for in a replica a transfer began in.
    doubts: Doubts
    head: str
    tree: str
    #: A clone's :func:`refs_fingerprint` (``""`` for a worktree or an older agent).
    refs: str
    problem: str
    ignored: bool
    users: tuple[str, ...] | None
    note: Mapping[str, str]

    @classmethod
    def parse(cls, name: str, raw: object) -> CopyInfo:
        """Return the copy an inventory entry describes."""
        record = _object(raw)
        users = record.get("users")
        replica = record.get("replica") is True
        changed = record.get("changed")
        return cls(
            name=name,
            form=_string(record, "form"),
            path=_string(record, "path"),
            home=work.canonical(_string(record, "home")),
            replica=replica,
            syncing=record.get("syncing") is True,
            syncedtree=_string(record, "syncedtree"),
            syncedhead=_string(record, "syncedhead"),
            # An agent that judges no ``changed`` keeps every replica it cannot vouch for.
            changed=changed if isinstance(changed, bool) else replica,
            doubts=Doubts.parse(record.get("doubts")),
            head=_string(record, "head"),
            tree=_string(record, "tree"),
            refs=_string(record, "refs"),
            problem=_string(record, "problem"),
            ignored=record.get("ignored") is True,
            users=None if users is None else tuple(_strings(users)),
            note=_string_map(record.get("note")),
        )

    @property
    def identity(self) -> str:
        """Return the copy's identity (work.py's ``copy_identity`` of its carried note)."""
        return work.copy_identity(self.note)

    @property
    def homed_note(self) -> dict[str, str]:
        """Return the carried note with the copy's ``home`` (what lineage rules read)."""
        return _homed(self.note, self.home)

    @property
    def generation(self) -> int:
        """Return the copy's handoff generation (``work.handoff_generation``)."""
        return work.handoff_generation(self.note)

    def later_home_of(self, other: CopyInfo) -> bool:
        """Return whether this copy's home is a later home of the same copy ``other`` records."""
        return same_copy(self.note, other.note) and work.later_home(
            self.homed_note,
            other.homed_note,
        )

    def fresh_against(self, home: CopyInfo) -> bool:
        """Return whether this replica holds exactly ``home``'s content, ``HEAD`` and pin record.

        The pin record (``work.recorded_pins`` of the carried note) is what tells the copy's
        own pins from another's once this replica is its home (a handoff): a home ``save`` of
        unchanged content adds a pin but changes neither content nor ``HEAD``, so a replica
        lacking it is refreshed.
        """
        return (
            not self.syncing
            and self.syncedtree == home.tree
            and self.head == home.head
            and work.recorded_pins(self.note) == work.recorded_pins(home.note)
        )

    def may_be_unchanged(self, home: CopyInfo) -> bool:
        """Return whether ``home`` may vouch for every change this replica holds.

        Its ``HEAD`` and refs doubts are judged against ``home``'s here; doubted paths need the
        home's digests (:func:`vouch`) unless the content is ``home``'s whole tree.
        """
        doubts = self.doubts
        return not self.changed or (
            doubts.any
            and (not doubts.head or doubts.head == home.head)
            and (not doubts.refs or doubts.refs == home.refs)
        )

    def synced_with(self, home: CopyInfo) -> bool:
        """Return whether ``home`` holds what this replica's last sync brought (content and ``HEAD``)."""
        return self.syncedtree == home.tree and (
            not self.syncedhead or self.syncedhead == home.head
        )

    def busy(self) -> str:
        """Return why a process may work in the copy, else ``""``."""
        if self.users is None:
            return "the process census cannot tell whether a process works in it"
        if self.users:
            return f"process {', '.join(self.users)} works in it"
        return ""


@dataclasses.dataclass(frozen=True)
class Inventory:
    """One machine's copies, pins and evidence."""

    copies: Mapping[str, CopyInfo]
    pins: Mapping[str, str]
    evidence: Mapping[str, Mapping[str, tuple[int, int]]]
    tombstones: Mapping[str, work.Tombstone]

    @classmethod
    def read(cls, endpoint: Endpoint, names: Sequence[str]) -> Inventory:
        """Ask ``endpoint`` for its inventory (of ``names`` only, when given)."""
        args = ["inventory"]
        for name in names:
            args += ["--copy", name]
        answer = endpoint.call(*args)
        evidence: dict[str, dict[str, tuple[int, int]]] = {}
        for stem, files in _object(answer.get("evidence")).items():
            entries: dict[str, tuple[int, int]] = {}
            for rel, state in _object(files).items():
                if fleet.is_json_array(state) and len(state) == 2:
                    size, mtime = state
                    if isinstance(size, int) and isinstance(mtime, int):
                        entries[rel] = (size, mtime)
            evidence[stem] = entries
        graves = answer.get("tombstones")
        parsed = [
            work.Tombstone.parse(raw) for raw in (graves if fleet.is_json_array(graves) else [])
        ]
        return cls(
            copies={
                name: CopyInfo.parse(name, raw)
                for name, raw in _object(answer.get("copies")).items()
            },
            pins=_string_map(answer.get("pins")),
            evidence=evidence,
            tombstones={grave.file_name: grave for grave in parsed if grave is not None},
        )


@dataclasses.dataclass(frozen=True)
class Step:
    """One thing a run does (or reports) for one copy between this machine and a peer."""

    kind: str
    name: str
    detail: str = ""
    source: Endpoint | None = None
    target: Endpoint | None = None
    info: CopyInfo | None = None
    other: CopyInfo | None = None


def plan_copy(
    name: str,
    mine: CopyInfo | None,
    theirs: CopyInfo | None,
    here: Endpoint,
    peer: Endpoint,
    graves: Sequence[work.Tombstone],
    pins: tuple[Mapping[str, str], Mapping[str, str]],
) -> Step:
    """Decide what one copy needs between this machine (``here``) and ``peer``.

    ``graves`` are the tombstones either side holds: the only record a replica is removed by.
    ``pins`` are each side's pins (``<name>/<leaf>`` to commit, this machine's first): a
    side holding another copy's pins under the name gets no replica of it.
    """
    held = [_live_pins(name, side, graves) for side in pins]
    for info, where in ((mine, here), (theirs, peer)):
        if info is not None and info.problem:
            kind = "note" if info.ignored else "skip"
            return Step(kind, name, f"on {where.label}: {info.problem}; never synced")
    if mine is not None and theirs is not None and not mine.replica and not theirs.replica:
        return Step("conflict", name, _two_homes_detail(name, (mine, here), (theirs, peer)))
    if mine is not None and not mine.replica:
        return _plan_home(name, mine, theirs, (here, peer), graves, held[1])
    if theirs is not None and not theirs.replica:
        return _plan_home(name, theirs, mine, (peer, here), graves, held[0])
    if mine is not None and theirs is not None:
        newer = next(
            (
                info
                for info, other in ((mine, theirs), (theirs, mine))
                if info.later_home_of(other)
            ),
            None,
        )
        if newer is not None:
            return Step(
                "none",
                name,
                f"replicas of {newer.home} (one still names a former home); {newer.home} "
                "syncs them",
            )
        if mine.home != theirs.home:
            return Step(
                "conflict",
                name,
                f"replicas disagree on its home ({here.label}: {mine.home}, {peer.label}: "
                f"{theirs.home}); sync from its home, or `handoff {name}`",
            )
        return Step("none", name, f"replicas of {mine.home} on both; its home syncs them")
    if mine is not None:
        return _plan_lone(name, mine, here, peer, graves)
    if theirs is not None:
        return _plan_lone(name, theirs, peer, here, graves)
    return Step("none", name)


def _live_pins(
    name: str,
    pins: Mapping[str, str],
    graves: Iterable[work.Tombstone],
) -> dict[str, str]:
    """Return the pins under ``name`` (leaf to commit) of ``pins`` no tombstone records dropping."""
    held: dict[str, str] = {}
    for ref, sha in pins.items():
        owner, _, leaf = ref.partition("/")
        if owner == name and not any(
            grave.name == name and (leaf, sha) in grave.dropped_pins for grave in graves
        ):
            held[leaf] = sha
    return held


def _two_homes_detail(
    name: str,
    first: tuple[CopyInfo, Endpoint],
    second: tuple[CopyInfo, Endpoint],
) -> str:
    """Return the conflict line of a copy two machines hold as its home.

    When one is a later home of the other (a handoff forced while the old home was offline,
    ``handoff --force-offline-home``), the newer handoff wins and the line says so; the
    older home's copy is never overwritten.
    """
    (one, one_at), (two, two_at) = first, second
    for newer, newer_at, older_at in ((one, one_at, two_at), (two, two_at, one_at)):
        older = two if newer is one else one
        if newer.later_home_of(older):
            return (
                f"{newer_at.label} and {older_at.label} both hold {name} as its home; "
                f"{newer_at.label} holds the newer handoff (generation {newer.generation}), "
                f"{older_at.label} the home it replaced: nothing overwritten; take what "
                f"{older_at.label}'s copy holds that {newer_at.label}'s lacks by hand "
                f"(`work.py save {name}` there first), then `work.py rm --discard {name}` "
                f"on {older_at.label}, and the next sync replicates {newer_at.label}'s"
            )
    return (
        f"{one_at.label} and {two_at.label} both hold {name} as its home (made separately, "
        f"or a handoff cut short): keep the one to continue and `work.py save` then "
        f"`rm` the other, or restore its save under a new name"
    )


def _plan_lone(
    name: str,
    replica: CopyInfo,
    where: Endpoint,
    other: Endpoint,
    graves: Iterable[work.Tombstone],
) -> Step:
    """Plan a replica only ``where`` holds.

    Removed only by a tombstone its home left for this very incarnation (its identity);
    a home ``other`` that lacks the copy without one (wiped, lost, restored from an old
    backup) removed nothing, so the replica, maybe the last copy, is kept and reported.
    """
    grave = _tombstone_for(name, replica, graves)
    if grave is not None:
        return _plan_removal(name, replica, where, grave)
    if replica.home == other.machine:
        return Step(
            "conflict",
            name,
            f"{other.label}, the home its note names, no longer holds it, and no tombstone "
            f"either side holds removes this copy (a handoff its machine missed may have "
            f"moved the home: sync with the newer home first): kept on {where.label}; "
            f"`fleet_sync.py handoff {name}` there to make this replica the home, or "
            f"`work.py rm --discard {name}` there (kept in .work/trash)",
        )
    return Step("none", name, f"a replica of {replica.home} on {where.label} only")


def _tombstone_for(
    name: str,
    replica: CopyInfo,
    graves: Iterable[work.Tombstone],
) -> work.Tombstone | None:
    """Return the tombstone that removes this very replica, else ``None``.

    Its identity, from the home it records or a later home of it (``work.Tombstone.buries``):
    the newest home's removal reaches a replica a handoff missed.
    """
    note = replica.homed_note
    return next((grave for grave in graves if grave.buries(name, note)), None)


def _plan_home(
    name: str,
    home: CopyInfo,
    replica: CopyInfo | None,
    ends: tuple[Endpoint, Endpoint],
    graves: Iterable[work.Tombstone],
    target_pins: Mapping[str, str],
) -> Step:
    """Plan a copy ``source`` holds as its home against ``target``'s replica (or none).

    ``ends`` are ``(source, target)``; ``target_pins`` are ``target``'s pins under the name
    (leaf to commit) no tombstone records dropping. With no replica there, a pin ``home``'s
    note does not attribute to it (``work.pin_belongs``: an earlier copy's leftover, which
    ``work.py new`` refuses the name for) is a conflict, no replica made: removing that
    replica later would drop the pin.

    A replica of an earlier copy under the name (:func:`same_copy` false) is never
    overwritten: its home's tombstone for it removes it first (the next run replicates the
    new copy), and without one the copy is a conflict. A replica recording a former home of
    ``home`` (``work.later_home``: a handoff its machine missed) is ``home``'s and is
    refreshed, which re-points its note, fresh or not.
    """
    source, target = ends
    if home.home != source.machine:
        return Step(
            "skip",
            name,
            f"{source.label} holds it as no replica but its note names {home.home} as home",
        )
    leftover = work.foreign_pins(home.note, target_pins) if replica is None else {}
    if leftover:
        return Step("conflict", name, leftover_pins_detail(name, f"on {target.label}", leftover))
    if replica is not None and replica.home != source.machine and not home.later_home_of(replica):
        return Step(
            "conflict",
            name,
            f"{target.label} holds a replica of {replica.home}, but {source.label} holds it "
            f"as home: `handoff {name}` from the machine that should continue it",
        )
    if replica is not None and not same_copy(home.note, replica.note):
        grave = _tombstone_for(name, replica, graves)
        if grave is not None:
            return _plan_removal(name, replica, target, grave)
        return Step(
            "conflict",
            name,
            f"{source.label} holds a new copy under the name, {target.label} a replica of an "
            f"earlier one its home left no tombstone for (maybe the last copy of that work): "
            f"nothing overwritten; take what it holds, then `work.py rm --discard {name}` on "
            f"{target.label} (kept in .work/trash) and sync again",
        )
    if replica is not None and not replica.may_be_unchanged(home):
        return Step(
            "conflict",
            name,
            _changed_detail(name, home, replica, source, target),
            source,
            target,
            home,
            replica,
        )
    current = replica is not None and (replica.home, replica.generation) == (
        home.home,
        home.generation,
    )
    if replica is not None and current and replica.fresh_against(home):
        return Step("fresh", name, f"replica on {target.label} is fresh", source, target, home)
    if replica is not None and replica.busy():
        return Step("skip", name, f"on {target.label}: {replica.busy()}")
    return Step(
        "replicate",
        name,
        f"{source.label} -> {target.label}",
        source,
        target,
        home,
        replica,
    )


def _changed_detail(
    name: str,
    home: CopyInfo,
    replica: CopyInfo,
    source: Endpoint,
    target: Endpoint,
) -> str:
    """Return the conflict line of a replica with commits or edits since its last sync."""
    fix = (
        f"keep its edits with `fleet_sync.py handoff {name} --to {target.label}` "
        "(the home did not change since)"
        if replica.synced_with(home)
        else f"both changed: `work.py save {name}` on {source.label}, take the "
        "replica's edits as a patch there by hand, then hand off"
    )
    return (
        f"its replica on {target.label} has commits or edits since its last sync; "
        f"nothing overwritten: {fix}"
    )


def vouch(
    source: Endpoint,
    home: CopyInfo,
    replica: CopyInfo,
    target: Endpoint,
) -> dict[str, str]:
    """Return the home's digests of the paths ``replica`` doubts, refusing what it does not hold.

    Raises:
        ConflictError: the replica holds a change its home does not (its own work).
        FleetError: the home cannot be asked.

    """
    doubts = replica.doubts
    digests: dict[str, str] = {}
    if replica.changed and doubts.paths and doubts.tree != home.tree:
        paths = json.dumps({"paths": sorted(doubts.paths)}).encode("utf-8")
        answer = source.call("digests", replica.name, stdin=paths)
        digests = _string_map(answer.get("digests"))
    if not replica.may_be_unchanged(home) or (
        replica.changed and not doubts.vouched(home.head, home.tree, home.refs, digests)
    ):
        raise ConflictError(_changed_detail(replica.name, home, replica, source, target))
    return digests


def _plan_removal(
    name: str,
    replica: CopyInfo,
    where: Endpoint,
    grave: work.Tombstone,
) -> Step:
    removed = f"its home {work.canonical(grave.home)} removed it"
    if replica.changed:
        return Step(
            "conflict",
            name,
            f"{removed}, but its replica on {where.label} has commits or edits since its "
            f"last sync: kept; `fleet_sync.py handoff {name}` there keeps them as its home, "
            f"`work.py rm --discard {name}` there moves them to .work/trash",
        )
    busy = replica.busy()
    if busy:
        return Step("skip", name, f"{removed}; on {where.label}: {busy}")
    days = work.TRASH_RETENTION_SECONDS // 86400
    return Step(
        "remove",
        name,
        f"{removed}; kept in .work/trash for {days} days",
        None,
        where,
        replica,
    )


# --------------------------------------------------------------------------------------------
# Transfers
# --------------------------------------------------------------------------------------------


def rsync(
    source: Endpoint,
    source_path: str,
    target: Endpoint,
    target_path: str,
    *,
    excludes: Sequence[str] = (),
    files: Sequence[str] | None = None,
) -> None:
    """Copy ``source_path`` into ``target_path`` with rsync over ssh (``--delete`` unless ``files``).

    Raises:
        FleetError: rsync fails.

    """
    argv = ["rsync", "-rlpt", f"--timeout={RSYNC_IO_TIMEOUT}"]
    argv += [f"--exclude={pattern}" for pattern in excludes]
    argv += ["-e", fleet.ssh_command()]
    listing: Path | None = None
    if files is None:
        argv.append("--delete")
    else:
        folder = work._container(REPO_ROOT, work.FLEET, create=True)
        listing = folder / f"files-{work._token()}"
        _ = listing.write_bytes(b"".join(f"{path}\0".encode() for path in files))
        argv += ["--from0", f"--files-from={listing}"]
    argv += [
        source.spec(source_path.rstrip("/") + "/"),
        target.spec(target_path.rstrip("/") + "/"),
    ]
    try:
        completed = subprocess.run(argv, capture_output=True, check=False)
    finally:
        if listing is not None:
            listing.unlink(missing_ok=True)
    if completed.returncode != 0:
        msg = f"rsync {source.label} -> {target.label} failed: {_last_line(completed.stderr)}"
        raise FleetError(msg)


def replicate(step: Step, tokens: Mapping[str, str], target_main: str) -> str:
    """Make or refresh the replica a ``replicate`` step names; return the result line.

    A replica a transfer began in is refreshed only once its home vouches for what it holds
    (:func:`vouch`), and is marked synced only when it received what the home held when read.

    Raises:
        ConflictError: the replica holds work of its own, or changed during the transfer.
        FleetError: a call or the transfer failed.

    """
    source, target, info = step.source, step.target, step.info
    if source is None or target is None or info is None:
        msg = f"{step.name}: a replicate step without its endpoints"
        raise FleetError(msg)
    digests = vouch(source, info, step.other, target) if step.other is not None else {}
    token = tokens[target.machine]
    prepare = [
        "prepare",
        step.name,
        "--form",
        info.form,
        "--home",
        info.home,
        "--head",
        info.head,
        "--expect-tree",
        info.tree,
        "--refs",
        info.refs,
        "--digests",
        json.dumps(digests),
        "--note",
        json.dumps(dict(info.note)),
        "--token",
        token,
    ]
    ready = target.call(*prepare)
    if ready.get("need_commit") is True:
        bundle = source.bytes_of(
            "head-export",
            step.name,
            *(["--have", target_main] if target_main else []),
        )
        _ = target.call("commit-import", "--token", token, stdin=bundle)
        ready = target.call(*prepare)
        if ready.get("need_commit") is True:
            msg = f"{target.label} cannot obtain {info.head[:12]}, the worktree's commit"
            raise FleetError(msg)
    path = _string(ready, "path")
    excludes = [
        *EXCLUDES,
        *(CLONE_GIT_EXCLUDES if info.form == "clone" else WORKTREE_GIT_EXCLUDES),
    ]
    rsync(source, info.path, target, path, excludes=excludes)
    finished = target.call(
        "finish",
        step.name,
        "--home",
        info.home,
        "--from",
        source.machine,
        "--note",
        json.dumps(dict(info.note)),
        "--token",
        token,
    )
    if finished.get("synced") is not True:
        _record_transferred(step.name, source, target, info.home, token, finished)
        msg = (
            f"transferred to {target.label}, but its content, HEAD or refs then were not what "
            f"{source.label} held when read (a commit or edit on either side during the "
            "transfer): not marked synced; the next sync completes it unless the replica "
            "holds work of its own"
        )
        raise ConflictError(msg)
    return f"synced {source.label} -> {target.label}"


def _record_transferred(
    name: str,
    source: Endpoint,
    target: Endpoint,
    home: str,
    token: str,
    finished: Mapping[str, object],
) -> None:
    """Have the replica record each doubted path the home holds just so as the transfer's.

    Asked right after the transfer, while the home most likely still holds what it copied: a
    home save the transfer copied then needs no vouching from a home that saved it again. Best
    effort: a call that fails leaves the paths in doubt, which keeps more.
    """
    doubted = _string_map(finished.get("doubts"))
    if not doubted:
        return
    with contextlib.suppress(FleetError):
        paths = json.dumps({"paths": sorted(doubted)}).encode("utf-8")
        held = _string_map(source.call("digests", name, stdin=paths).get("digests"))
        same = {path: digest for path, digest in doubted.items() if held.get(path) == digest}
        if same:
            _ = target.call(
                "transferred",
                name,
                "--home",
                home,
                "--digests",
                json.dumps(same),
                "--token",
                token,
            )


def buried_pin(
    ref: str,
    commit: str,
    holder: Inventory,
    graves: Iterable[work.Tombstone],
) -> bool:
    """Return whether the pin ``ref`` at ``commit``, which ``holder`` holds, is never carried.

    A tombstone recorded dropping it (``dropped_pins``: that leaf at that commit, so a later
    copy's pin under the leaf is another commit and still moves), or ``holder`` keeps a
    replica of an incarnation whose home ran ``rm --drop-saves`` (its pins are that
    incarnation's, whatever their commits: the replica kept, changed or busy, while the
    tombstone's removal waits).
    """
    name, _, leaf = ref.partition("/")
    copy = holder.copies.get(name)
    for grave in graves:
        if grave.name != name:
            continue
        if (leaf, commit) in grave.dropped_pins:
            return True
        if (
            grave.saves_dropped
            and copy is not None
            and copy.replica
            and grave.buries(name, copy.homed_note)
        ):
            return True
    return False


def sync_pins(
    here: Endpoint,
    peer: Endpoint,
    mine: Inventory,
    theirs: Inventory,
    tokens: Mapping[str, str],
    *,
    dry_run: bool,
) -> list[Row]:
    """Copy every pin one side lacks to it, create-only; report refs that differ.

    A pin a tombstone buries (:func:`buried_pin`) never moves and is no conflict. A pin
    whose commit the target's pins already reach is linked there without a bundle
    (``pins-link``); a bundle brings the rest. A direction that fails is a ``failed`` row,
    after the rows of the pins it carried before failing; the other still runs.
    """
    graves = [*mine.tombstones.values(), *theirs.tombstones.values()]
    rows = [
        Row(
            ref,
            peer.label,
            "conflict",
            f"pin differs: {mine.pins[ref][:12]} on {here.label}, {theirs.pins[ref][:12]} on "
            f"{peer.label}; both kept (inspect with `git -C .work/pins.git show "
            f"refs/work/{ref}` on each)",
        )
        for ref in sorted(set(mine.pins) & set(theirs.pins))
        if mine.pins[ref] != theirs.pins[ref]
        and not buried_pin(ref, mine.pins[ref], mine, graves)
        and not buried_pin(ref, theirs.pins[ref], theirs, graves)
    ]
    for source, target, held, have, want in (
        (
            here,
            peer,
            mine,
            mine.pins,
            theirs.pins,
        ),
        (
            peer,
            here,
            theirs,
            theirs.pins,
            mine.pins,
        ),
    ):
        missing = sorted(
            ref for ref in set(have) - set(want) if not buried_pin(ref, have[ref], held, graves)
        )
        if not missing:
            continue
        if dry_run:
            rows.extend(
                Row(ref, peer.label, "would", f"pin {source.label} -> {target.label}")
                for ref in missing
            )
            continue
        carried: list[Row] = []
        try:
            _carry_pins(source, target, missing, have, want, tokens, peer, carried)
        except (FleetError, work.WorkError) as error:
            carried.append(Row("pins", peer.label, "failed", str(error)))
        rows += carried
    return rows


def _carry_pins(
    source: Endpoint,
    target: Endpoint,
    missing: Sequence[str],
    have: Mapping[str, str],
    want: Mapping[str, str],
    tokens: Mapping[str, str],
    peer: Endpoint,
    rows: list[Row],
) -> None:
    """Carry the ``missing`` pins ``source`` holds (``have``) to ``target``, appending to ``rows``.

    ``want`` is what ``target``'s pins hold. Each step's rows are appended as it answers, so
    the pins ``pins-link`` created stay reported when the bundle step after it raises.
    """
    token = tokens[target.machine]
    document = json.dumps({"pins": {ref: have[ref] for ref in missing}}).encode("utf-8")
    linked = target.call("pins-link", "--token", token, stdin=document)
    rows += _pin_rows(linked, source, target, peer)
    rest = [ref for ref in _strings(linked.get("missing")) if ref in have]
    if rest:
        args = ["pins-export"]
        for ref in rest:
            args += ["--ref", ref]
        for oid in sorted(set(want.values())):
            args += ["--have", oid]
        bundle = source.bytes_of(*args)
        answer = target.call("pins-import", "--token", token, stdin=bundle)
        rows += _pin_rows(answer, source, target, peer)


def _pin_rows(
    answer: Mapping[str, object],
    source: Endpoint,
    target: Endpoint,
    peer: Endpoint,
) -> list[Row]:
    """Return the rows of one ``pins-link`` or ``pins-import`` answer: created, then conflicts."""
    return [
        *(
            Row(ref, peer.label, "synced", f"pin {source.label} -> {target.label}")
            for ref in _strings(answer.get("created"))
        ),
        *(
            Row(ref, peer.label, "conflict", f"pin differs on {target.label}; both kept")
            for ref in _strings(answer.get("conflicts"))
        ),
    ]


def sync_tombstones(
    here: Endpoint,
    peer: Endpoint,
    mine: Inventory,
    theirs: Inventory,
    tokens: Mapping[str, str],
    *,
    dry_run: bool,
) -> list[Row]:
    """Copy every tombstone one side lacks to it, both ways; never delete one."""
    rows: list[Row] = []
    for source, target, have, want in (
        (
            here,
            peer,
            mine.tombstones,
            theirs.tombstones,
        ),
        (
            peer,
            here,
            theirs.tombstones,
            mine.tombstones,
        ),
    ):
        missing = [have[key] for key in sorted(set(have) - set(want))]
        if not missing:
            continue
        if dry_run:
            rows.extend(
                Row(grave.name, peer.label, "would", f"tombstone {source.label} -> {target.label}")
                for grave in missing
            )
            continue
        document = json.dumps({"tombstones": [grave.as_json() for grave in missing]})
        answer = target.call(
            "tombstones-import",
            "--token",
            tokens[target.machine],
            stdin=document.encode("utf-8"),
        )
        created = set(_strings(answer.get("created")))
        rows.extend(
            Row(grave.name, peer.label, "synced", f"tombstone {source.label} -> {target.label}")
            for grave in missing
            if grave.file_name in created
        )
    return rows


def _manifest_path(peer: str) -> Path:
    return work._container(REPO_ROOT, work.FLEET, create=True) / f"evidence-{peer}.json"


def _read_manifest(peer: str) -> dict[str, dict[str, tuple[int, int]]]:
    path = work.work_dir(REPO_ROOT) / work.FLEET / f"evidence-{peer}.json"
    try:
        document = _object(_loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {}
    manifest: dict[str, dict[str, tuple[int, int]]] = {}
    for stem, files in document.items():
        entries: dict[str, tuple[int, int]] = {}
        for rel, state in _object(files).items():
            if fleet.is_json_array(state) and len(state) == 2:
                size, mtime = state
                if isinstance(size, int) and isinstance(mtime, int):
                    entries[rel] = (size, mtime)
        manifest[stem] = entries
    return manifest


def _evidence_moves(
    mine: Mapping[str, tuple[int, int]],
    theirs: Mapping[str, tuple[int, int]],
    last: Mapping[str, tuple[int, int]],
) -> tuple[list[str], list[str], list[str]]:
    """Return the files to push, to pull and in conflict for one evidence folder."""
    push: list[str] = []
    pull: list[str] = []
    clash: list[str] = []
    for rel in sorted(set(mine) | set(theirs)):
        a, b = mine.get(rel), theirs.get(rel)
        if a == b:
            continue
        if b is None:
            push.append(rel)
        elif a is None:
            pull.append(rel)
        elif a != last.get(rel) and b == last.get(rel) and a[1] >= b[1]:
            push.append(rel)
        elif b != last.get(rel) and a == last.get(rel) and b[1] >= a[1]:
            pull.append(rel)
        else:
            clash.append(rel)
    return push, pull, clash


def sync_evidence(
    here: Endpoint,
    peer: Endpoint,
    mine: Inventory,
    theirs: Inventory,
    tokens: Mapping[str, str],
    *,
    dry_run: bool,
) -> list[Row]:
    """Union every evidence folder with ``peer``, file by file; never delete."""
    manifest = _read_manifest(peer.machine)
    rows: list[Row] = []
    for stem in sorted(set(mine.evidence) | set(theirs.evidence)):
        a, b = mine.evidence.get(stem, {}), theirs.evidence.get(stem, {})
        push, pull, clash = _evidence_moves(a, b, manifest.get(stem, {}))
        rows.extend(
            Row(
                f"{stem}/{rel}",
                peer.label,
                "conflict",
                f"evidence differs on {here.label} and {peer.label} and both changed since "
                "the last sync: both kept; copy one over by hand",
            )
            for rel in clash
        )
        if dry_run:
            if push or pull:
                rows.append(
                    Row(stem, peer.label, "would", f"evidence: {len(push)} out, {len(pull)} in"),
                )
            continue
        for source, target, files in ((here, peer, push), (peer, here, pull)):
            if not files:
                continue
            folder = _string(
                target.call("prepare-evidence", stem, "--token", tokens[target.machine]),
                "path",
            )
            source_folder = str(work.work_dir(Path(_repo_of(source))) / work.EVIDENCE / stem)
            rsync(source, source_folder, target, folder, files=files)
        if push or pull:
            rows.append(
                Row(stem, peer.label, "synced", f"evidence: {len(push)} out, {len(pull)} in"),
            )
        merged = {**b, **a}
        merged.update({rel: b[rel] for rel in pull})
        merged.update({rel: a[rel] for rel in push})
        manifest[stem] = {rel: state for rel, state in merged.items() if rel not in clash}
    if not dry_run:
        path = _manifest_path(peer.machine)
        staged = path.with_name(f".{path.name}.{work._token()}")
        document = {
            stem: {rel: list(state) for rel, state in files.items()}
            for stem, files in manifest.items()
        }
        _ = staged.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
        _ = staged.replace(path)
    return rows


_REPOS: dict[str, str] = {}


def _repo_of(endpoint: Endpoint) -> str:
    """Return the checkout path ``endpoint``'s probe reported."""
    return str(REPO_ROOT) if endpoint.local else _REPOS[endpoint.machine]


# --------------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------------


def _count(repo: Path, left: str, right: str) -> tuple[int, int]:
    counts = _git(repo, "rev-list", "--left-right", "--count", f"{left}...{right}").split()
    return int(counts[0]), int(counts[1])


def fetch_main(machine: Machine) -> bool:
    """Bring ``machine``'s main commit into this repository's objects (no ref); return success."""
    probe = machine.probe
    if probe is None or not probe.main:
        return False
    if work._resolve_commit(REPO_ROOT, probe.main):
        return True
    try:
        completed = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "--no-pager",
                "fetch",
                "--quiet",
                "--no-tags",
                "--no-write-fetch-head",
                f"{machine.ssh}:{probe.repo}",
                work.LANDING_BRANCH,
            ],
            capture_output=True,
            env=_git_runner.repository_env(GIT_SSH_COMMAND=fleet.ssh_command()),
            timeout=FETCH_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return False
    return completed.returncode == 0 and bool(work._resolve_commit(REPO_ROOT, probe.main))


def main_relation(machine: Machine, *, fetch: bool) -> tuple[str, str]:
    """Return ``(state, detail)`` for ``machine``'s main against this machine's."""
    probe = machine.probe
    local = work._resolve_commit(REPO_ROOT, work.LANDING_BRANCH)
    if probe is None or not probe.main or not local:
        return "unknown", "no main to compare"
    if probe.main == local:
        return "same", f"main {local[:12]} on both"
    if not work._resolve_commit(REPO_ROOT, probe.main) and not (fetch and fetch_main(machine)):
        return (
            "unknown",
            f"{machine.label}'s main {probe.main[:12]} is not here (a sync fetches it)",
        )
    here_only, there_only = _count(REPO_ROOT, local, probe.main)
    if here_only and there_only:
        return "diverged", (
            f"diverged: {here_only} here only, {there_only} on {machine.label} only; "
            "reported, never merged"
        )
    if there_only:
        return "ahead", f"{machine.label} is {there_only} ahead ({probe.main[:12]})"
    return "behind", f"{machine.label} is {here_only} behind; its own run fast-forwards it"


def fast_forward(target: str, *, dry_run: bool) -> tuple[str, str]:
    """Fast-forward this machine's main to ``target`` under every guard; return the result."""
    branch = work._branch(REPO_ROOT)
    if branch != work.LANDING_BRANCH:
        return (
            "skip",
            f"HEAD is {branch or 'detached'}, not {work.LANDING_BRANCH}: not fast-forwarded",
        )
    busy = [name for name in IN_PROGRESS if work._git_path(REPO_ROOT, name).exists()]
    if busy:
        return "skip", f"{', '.join(busy)} in progress: not fast-forwarded"
    if dry_run:
        return "would", f"would fast-forward main to {target[:12]}"
    try:
        with work.land_lock(REPO_ROOT):
            completed = _git_runner.run_git(REPO_ROOT, "merge", "--ff-only", "--quiet", target)
    except work.WorkError:
        return "skip", "a work.py land is in progress: not fast-forwarded"
    if completed.returncode != 0:
        return "skip", f"git merge --ff-only refused: {_last_line(completed.stderr.encode())}"
    return "synced", f"fast-forwarded main to {target[:12]}"


def sync_main(peers: Sequence[Machine], *, dry_run: bool) -> list[Row]:
    """Fast-forward main from each peer strictly ahead; report the rest."""
    rows: list[Row] = []
    for machine in peers:
        state, detail = main_relation(machine, fetch=True)
        result = {
            "same": "fresh",
            "behind": "fresh",
            "unknown": "skip",
            "diverged": "conflict",
        }
        if state != "ahead" or machine.probe is None:
            rows.append(Row("main", machine.label, result.get(state, "skip"), detail))
            continue
        outcome, message = fast_forward(machine.probe.main, dry_run=dry_run)
        rows.append(Row("main", machine.label, outcome, f"{detail}: {message}"))
    return rows


# --------------------------------------------------------------------------------------------
# Runs
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Row:
    """One line of a run's report."""

    subject: str
    machine: str
    result: str
    detail: str

    def as_json(self) -> dict[str, str]:
        """Return the row as a JSON object."""
        return dataclasses.asdict(self)


#: Results that make a run exit 1.
TROUBLE = frozenset({"conflict", "skip", "failed"})


def _endpoint(machine: Machine) -> Endpoint:
    if machine.endpoint is None:
        msg = f"{machine.label} is not reached: {machine.reason}"
        raise FleetError(msg)
    return machine.endpoint


def sync_with_peer(
    here: Machine,
    peer: Machine,
    local_token: str,
    args: _Args,
) -> list[Row]:
    """Sync every copy, pin and evidence folder (or ``--copy``'s) between this machine and ``peer``."""
    rows: list[Row] = []
    try:
        _sync_pair(here, peer, local_token, args, rows)
    except (FleetError, work.WorkError) as error:
        rows.append(Row("sync", peer.label, "failed", str(error)))
    return [row for row in rows if row.result != "none"]


def _sync_pair(
    here: Machine,
    peer: Machine,
    local_token: str,
    args: _Args,
    rows: list[Row],
) -> None:
    """Do :func:`sync_with_peer`'s work, appending each row to ``rows`` as it is made.

    A failure part way (a bundle, a call) keeps the rows already made: the removals and
    replications done before it are reported, not lost with it.
    """
    mine_end, their_end = _endpoint(here), _endpoint(peer)
    hold = contextlib.nullcontext("") if args.dry_run else their_end.hold(local_token)
    with hold as remote_token:
        tokens = {mine_end.machine: local_token, their_end.machine: remote_token}
        mine = Inventory.read(mine_end, args.copy)
        theirs = Inventory.read(their_end, args.copy)
        rows += sync_tombstones(mine_end, their_end, mine, theirs, tokens, dry_run=args.dry_run)
        graves = [*mine.tombstones.values(), *theirs.tombstones.values()]
        names = sorted(set(mine.copies) | set(theirs.copies))
        steps = [
            plan_copy(
                name,
                mine.copies.get(name),
                theirs.copies.get(name),
                mine_end,
                their_end,
                graves,
                (mine.pins, theirs.pins),
            )
            for name in names
        ]
        for step in sorted(steps, key=lambda step: step.kind != "remove"):
            rows.append(_run_step(step, tokens, peer, dry_run=args.dry_run))
        mine = Inventory.read(mine_end, args.copy) if not args.dry_run else mine
        theirs = Inventory.read(their_end, args.copy) if not args.dry_run else theirs
        rows += sync_pins(mine_end, their_end, mine, theirs, tokens, dry_run=args.dry_run)
        rows += sync_evidence(mine_end, their_end, mine, theirs, tokens, dry_run=args.dry_run)


def _run_step(
    step: Step,
    tokens: Mapping[str, str],
    peer: Machine,
    *,
    dry_run: bool,
) -> Row:
    if step.kind in {
        "none",
        "note",
        "fresh",
        "skip",
        "conflict",
    }:
        return Row(step.name, peer.label, step.kind, step.detail)
    if dry_run:
        return Row(step.name, peer.label, "would", f"would {step.kind}: {step.detail}")
    try:
        if step.kind == "remove":
            message = remove_replica(step, tokens)
        else:
            target_main = (
                peer.probe.main
                if peer.probe is not None and step.target is _endpoint(peer)
                else ""
            )
            message = replicate(step, tokens, target_main or _local_main())
    except ConflictError as error:
        return Row(step.name, peer.label, "conflict", str(error))
    except (FleetError, work.WorkError) as error:
        return Row(step.name, peer.label, "failed", str(error))
    return Row(step.name, peer.label, "synced", message)


def remove_replica(step: Step, tokens: Mapping[str, str]) -> str:
    """Remove the replica a ``remove`` step names (its home removed the copy); return the result.

    Raises:
        FleetError: the step lacks its replica, or the replica's machine refuses.

    """
    if step.target is None or step.info is None:
        msg = f"{step.name}: a remove step without its replica"
        raise FleetError(msg)
    answer = step.target.call(
        "remove",
        step.name,
        "--home",
        step.info.home,
        "--identity",
        step.info.identity,
        "--token",
        tokens[step.target.machine],
    )
    kept = _string_map(answer.get("kept"))
    return f"removed on {step.target.label}: {step.detail}{work.kept_pins_note(step.name, kept)}"


def _local_main() -> str:
    return work._resolve_commit(REPO_ROOT, work.LANDING_BRANCH)


def machine_rows(here: Machine, others: Sequence[Machine]) -> list[dict[str, object]]:
    """Return every machine's report entry."""
    entries: list[dict[str, object]] = []
    for machine in [here, *others]:
        entry: dict[str, object] = {
            "machine": machine.label,
            "id": machine.id,
            "ssh": machine.ssh,
            "os": machine.os,
            "local": machine.local,
            "qualified": machine.qualified,
            "reason": machine.reason,
            "listed": bool(machine.row),
        }
        if machine.qualified and not machine.row:
            entry["suggested_row"] = machine.suggested_row()
        entries.append(entry)
    return entries


def _render(document: Mapping[str, object], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(document, indent=2))
        return
    print("machines")
    machines = document.get("machines")
    for raw in machines if fleet.is_json_array(machines) else []:
        entry = _object(raw)
        where = "this machine" if entry.get("local") is True else f"ssh {_string(entry, 'ssh')}"
        state = (
            "qualified"
            if entry.get("qualified") is True
            else f"not synced: {_string(entry, 'reason')}"
        )
        print(f"  {_string(entry, 'machine'):<22} {where:<24} {state}")
        if "suggested_row" in entry:
            print(f"    not in machines.json; suggested row: {json.dumps(entry['suggested_row'])}")
    for section in ("copies", "rows"):
        items = document.get(section)
        if not fleet.is_json_array(items) or not items:
            continue
        print(section if section == "copies" else "results")
        for raw in items:
            entry = _object(raw)
            if section == "copies":
                copy, home = _string(entry, "copy"), _string(entry, "home")
                print(f"  {copy:<24} home {home:<22} {_string(entry, 'detail')}")
            else:
                print(
                    f"  {_string(entry, 'result'):<8} {_string(entry, 'subject'):<32} "
                    f"{_string(entry, 'machine'):<14} {_string(entry, 'detail')}",
                )


def _scope_args(args: _Args) -> list[str]:
    return list(args.copy)


def cmd_status(args: _Args) -> int:
    """Report machines, copies and main without writing anything."""
    here, others = find_machines(args.remote_scripts, args.machine)
    reached = [machine for machine in others if machine.qualified]
    inventories: dict[str, Inventory] = {
        here.label: Inventory.read(_endpoint(here), _scope_args(args)),
    }
    rows: list[Row] = []
    for machine in reached:
        try:
            inventories[machine.label] = Inventory.read(_endpoint(machine), _scope_args(args))
        except FleetError as error:
            rows.append(Row("inventory", machine.label, "failed", str(error)))
    copies = copy_overview(inventories)
    for machine in reached:
        state, detail = main_relation(machine, fetch=False)
        rows.append(Row("main", machine.label, state, detail))
    trouble = any(entry.get("conflict") for entry in copies) or any(
        row.result == "failed" for row in rows
    )
    document = {
        "machines": machine_rows(here, others),
        "copies": copies,
        "rows": [row.as_json() for row in rows],
    }
    _render(document, as_json=args.json)
    return 1 if trouble else 0


def copy_overview(inventories: Mapping[str, Inventory]) -> list[dict[str, object]]:
    """Return, per copy, its home, each replica's freshness and whether it is in conflict."""
    names = sorted({name for inventory in inventories.values() for name in inventory.copies})
    overview: list[dict[str, object]] = []
    for name in names:
        held = {
            label: inv.copies[name] for label, inv in inventories.items() if name in inv.copies
        }
        homes = {label: info for label, info in held.items() if not info.replica}
        home = next(iter(homes.values()), None)
        replicas: dict[str, str] = {}
        for label, info in held.items():
            if not info.replica:
                continue
            if info.changed and (home is None or not info.may_be_unchanged(home)):
                replicas[label] = "changed"
            elif info.syncing:
                replicas[label] = "syncing"
            elif home is not None and info.fresh_against(home):
                replicas[label] = "fresh"
            else:
                replicas[label] = "stale"
        conflict = len(homes) > 1 or "changed" in replicas.values()
        detail = ", ".join(f"{label} {state}" for label, state in sorted(replicas.items()))
        overview.append(
            {
                "copy": name,
                "home": home.home if home is not None else next(iter(held.values())).home,
                "home_machines": sorted(homes),
                "replicas": replicas,
                "conflict": conflict,
                "detail": ("CONFLICT: two homes " if len(homes) > 1 else "")
                + (f"replicas: {detail}" if detail else "no replica"),
            },
        )
    return overview


def cmd_sync(args: _Args) -> int:
    """Sync with every qualifying peer."""
    here, others = find_machines(args.remote_scripts, args.machine, member=True)
    rows = [
        Row("machine", machine.label, "skip", machine.reason)
        for machine in others
        if machine.reason and args.machine
    ]
    peers = [machine for machine in others if machine.qualified]
    for machine in peers:
        if machine.probe is not None:
            _REPOS[machine.id] = machine.probe.repo
    lock = contextlib.nullcontext("") if args.dry_run else holding(REPO_ROOT)
    try:
        with lock as local_token:
            if not args.main_only:
                for machine in peers:
                    rows += sync_with_peer(here, machine, local_token, args)
            if not args.copy:
                rows += sync_main(peers, dry_run=args.dry_run)
    except FleetError as error:
        rows.append(Row("sync", here.label, "skip", str(error)))
    document = {"machines": machine_rows(here, others), "rows": [row.as_json() for row in rows]}
    _render(document, as_json=args.json)
    return 1 if any(row.result in TROUBLE for row in rows) else 0


def cmd_handoff(args: _Args) -> int:
    """Move a copy's home to ``--to`` (default this machine)."""
    here, others = find_machines(args.remote_scripts, [], member=True)
    peers = [machine for machine in others if machine.qualified]
    for machine in peers:
        if machine.probe is not None:
            _REPOS[machine.id] = machine.probe.repo
    everyone = [here, *peers]
    target = here
    if args.to:
        named = [m for m in everyone if _named_by(m, args.to)]
        if not named:
            msg = f"--to {args.to!r} names no qualifying machine"
            raise SetupError(msg)
        target = named[0]
    rows: list[Row] = []
    try:
        with holding(REPO_ROOT) as local_token, contextlib.ExitStack() as stack:
            tokens = {_endpoint(here).machine: local_token}
            for machine in peers:
                tokens[_endpoint(machine).machine] = stack.enter_context(
                    _endpoint(machine).hold(local_token),
                )
            rows = handoff(
                args.name,
                here,
                peers,
                target,
                tokens,
                force_offline_home=args.force_offline_home,
            )
    except (FleetError, work.WorkError) as error:
        rows.append(Row(args.name, here.label, "failed", str(error)))
    _render(
        {"machines": machine_rows(here, others), "rows": [row.as_json() for row in rows]},
        as_json=args.json,
    )
    return 1 if any(row.result in TROUBLE for row in rows) else 0


def _next_lineage(info: CopyInfo) -> tuple[str, str]:
    """Return the ``generation`` and ``formerhomes`` a handoff away from ``info``'s home writes."""
    former = dict.fromkeys([*work.former_homes(info.note), info.home])
    return str(info.generation + 1), ",".join(home for home in former if home)


def handoff(
    name: str,
    here: Machine,
    peers: Sequence[Machine],
    target: Machine,
    tokens: Mapping[str, str],
    *,
    force_offline_home: bool = False,
) -> list[Row]:
    """Sync ``name`` fresh from its home to ``target``, then make ``target`` its home.

    Every note it writes takes the handoff's lineage (:func:`_next_lineage`: ``generation``
    one up, the old home added to ``formerhomes``), so a replica it cannot reach (offline)
    is later taken as the new home's (``work.later_home``) and the newest home wins. With
    no reached home, a replica whose recorded home is not reached (offline, maybe holding
    newer work) is promoted only with ``force_offline_home``; the old home, when it returns,
    is then a second home reported as a conflict (never overwritten), the newer handoff named.

    Raises:
        FleetError: a call failed part way; what moved is in the notes and ``status`` shows it.

    """
    held: dict[str, tuple[Machine, CopyInfo]] = {}
    inventories: dict[str, Inventory] = {}
    for machine in [here, *peers]:
        inventory = Inventory.read(_endpoint(machine), [name])
        inventories[machine.id] = inventory
        info = inventory.copies.get(name)
        if info is not None:
            held[machine.id] = (machine, info)
    homes = [machine_id for machine_id, (_m, info) in held.items() if not info.replica]
    if len(homes) > 1:
        (one_machine, one), (two_machine, two) = (held[homes[0]], held[homes[1]])
        detail = _two_homes_detail(
            name,
            (one, _endpoint(one_machine)),
            (two, _endpoint(two_machine)),
        )
        return [Row(name, target.label, "conflict", f"{detail}; resolve that first")]
    if not held:
        return [Row(name, target.label, "failed", "no reached machine holds it")]
    if homes and homes[0] == target.id:
        return [Row(name, target.label, "fresh", "already its home")]
    for _machine, info in held.values():
        if info.problem:
            return [Row(name, _machine.label, "skip", info.problem)]
    target_info = held.get(target.id, (target, None))[1]
    rows: list[Row] = []
    lineage = ("", "")
    #: The home's pin record, for the promoted target to attribute what the home published.
    pinned: dict[str, str] = {}
    if homes:
        home_machine, home_info = held[homes[0]]
        lineage = _next_lineage(home_info)
        if work.PINS_NOTE in home_info.note:
            pinned[work.PINS_NOTE] = home_info.note[work.PINS_NOTE]
        if here.id not in {home_machine.id, target.id}:
            return [
                Row(
                    name,
                    target.label,
                    "skip",
                    f"run the handoff on {home_machine.label} or {target.label}",
                ),
            ]
        busy = home_info.busy()
        if busy:
            return [Row(name, home_machine.label, "skip", f"its home: {busy}")]
        target_changed = target_info is not None and target_info.changed
        if target_info is not None and target_changed:
            with contextlib.suppress(ConflictError):
                _ = vouch(_endpoint(home_machine), home_info, target_info, _endpoint(target))
                target_changed = False
        if target_info is not None and target_changed and not target_info.synced_with(home_info):
            return [
                Row(
                    name,
                    target.label,
                    "conflict",
                    "both the home and this replica changed since the last sync",
                ),
            ]
        if target_info is None or (
            not target_changed and not target_info.fresh_against(home_info)
        ):
            step = Step(
                "replicate",
                name,
                "",
                _endpoint(home_machine),
                _endpoint(target),
                home_info,
                target_info,
            )
            target_main = target.probe.main if target.probe is not None else ""
            rows.append(Row(name, target.label, "synced", replicate(step, tokens, target_main)))
            target_info = Inventory.read(_endpoint(target), [name]).copies.get(name)
            if target_info is None or not target_info.fresh_against(home_info):
                rows.append(
                    Row(
                        name,
                        target.label,
                        "failed",
                        "the home changed during the transfer; retry",
                    ),
                )
                return rows
        try:
            rows += handoff_pins(
                (_endpoint(home_machine), inventories[home_machine.id]),
                (_endpoint(target), inventories[target.id]),
                tokens,
            )
        except (FleetError, work.WorkError) as error:
            rows.append(Row(name, target.label, "failed", f"{error}; nothing handed off"))
            return rows
        _ = _endpoint(home_machine).call(
            "set-home",
            name,
            "--home",
            target.id,
            "--replica",
            "yes",
            "--expect-tree",
            home_info.tree,
            "--head",
            home_info.head,
            *_lineage_args(lineage),
            "--token",
            tokens[_endpoint(home_machine).machine],
        )
        rows.append(Row(name, home_machine.label, "synced", f"now a replica of {target.label}"))
    elif target_info is None or target_info.changed:
        return [
            Row(
                name,
                target.label,
                "failed",
                "no machine holds it as home and this one has no clean replica",
            ),
        ]
    else:
        reached = {machine.id for machine in [here, *peers]}
        if target_info.home not in reached and not force_offline_home:
            return [
                Row(
                    name,
                    target.label,
                    "skip",
                    f"its home {target_info.home} is not reached (offline?) and may hold work "
                    f"this replica lacks: run the handoff while {target_info.home} is online, "
                    f"or `handoff {name} --force-offline-home` to promote this replica anyway "
                    f"(when {target_info.home} returns, both are homes: a conflict naming this "
                    "newer one, nothing overwritten)",
                ),
            ]
        lineage = _next_lineage(target_info)
    _ = _endpoint(target).call(
        "set-home",
        name,
        "--home",
        target.id,
        "--replica",
        "no",
        "--note",
        json.dumps(pinned),
        *_lineage_args(lineage),
        "--token",
        tokens[_endpoint(target).machine],
    )
    rows.append(Row(name, target.label, "synced", "now its home"))
    for machine_id, (machine, info) in held.items():
        if machine_id in {target.id, *homes} or not info.replica:
            continue
        _ = _endpoint(machine).call(
            "set-home",
            name,
            "--home",
            target.id,
            "--replica",
            "yes",
            *_lineage_args(lineage),
            "--token",
            tokens[_endpoint(machine).machine],
        )
        rows.append(Row(name, machine.label, "synced", f"re-pointed to {target.label}"))
    return rows


def handoff_pins(
    home: tuple[Endpoint, Inventory],
    target: tuple[Endpoint, Inventory],
    tokens: Mapping[str, str],
) -> list[Row]:
    """Carry the pins the home holds under the copy's name and ``target`` lacks, create-only.

    Each side's inventory is of the handed-off name alone, so only that copy's pins move:
    the pin record the promotion writes then names no pin the new home's store lacks (a
    home ``save`` no sync carried yet). A pin a tombstone buries (:func:`buried_pin`) stays.
    """
    (source, mine), (peer, theirs) = home, target
    graves = [*mine.tombstones.values(), *theirs.tombstones.values()]
    missing = sorted(
        ref
        for ref in set(mine.pins) - set(theirs.pins)
        if not buried_pin(ref, mine.pins[ref], mine, graves)
    )
    rows: list[Row] = []
    if missing:
        _carry_pins(source, peer, missing, mine.pins, theirs.pins, tokens, peer, rows)
    return rows


def _lineage_args(lineage: tuple[str, str]) -> list[str]:
    generation, former = lineage
    return (
        [
            "--generation",
            generation,
            "--former",
            former,
        ]
        if generation
        else []
    )


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``build_parser``'s ``add_argument`` calls."""

    command: str
    json: bool
    remote_scripts: str
    dry_run: bool
    machine: list[str]
    copy: list[str]
    main_only: bool
    name: str
    to: str
    force_offline_home: bool
    repo: str
    operation: str
    form: str
    home: str
    head: str
    token: str
    source: str
    note: str
    replica: str
    expect_tree: str
    refs: str
    digests: str
    identity: str
    generation: str
    former: str
    ref: list[str]
    have: list[str]


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").partition("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    shared = argparse.ArgumentParser(add_help=False)
    _ = shared.add_argument("--json", action="store_true", help="one JSON document")
    _ = shared.add_argument(
        "--remote-scripts",
        default="",
        help="run the scripts in this folder on each peer (a peer whose main predates them)",
    )
    commands = parser.add_subparsers(dest="command")

    status = commands.add_parser("status", parents=[shared], help="read-only report (default)")
    _ = status.add_argument("--machine", action="append", default=[])
    _ = status.add_argument("--copy", action="append", default=[])

    sync = commands.add_parser("sync", parents=[shared], help="sync with every qualifying peer")
    _ = sync.add_argument("--dry-run", action="store_true")
    _ = sync.add_argument("--machine", action="append", default=[], help="only this peer")
    _ = sync.add_argument("--copy", action="append", default=[], help="only this copy (no main)")
    _ = sync.add_argument("--main-only", action="store_true", help="main alone")

    handoff_parser = commands.add_parser("handoff", parents=[shared], help="move a copy's home")
    _ = handoff_parser.add_argument("name")
    _ = handoff_parser.add_argument("--to", default="", help="the new home (this machine)")
    _ = handoff_parser.add_argument(
        "--force-offline-home",
        action="store_true",
        help="promote a replica whose home is not reached (that home becomes a conflict)",
    )

    agent = commands.add_parser("agent", help=argparse.SUPPRESS)
    _ = agent.add_argument("--repo", required=True)
    _ = agent.add_argument(
        "operation",
        choices=(
            "probe",
            "hold",
            "inventory",
            "prepare",
            "finish",
            "transferred",
            "digests",
            "remove",
            "set-home",
            "pins-export",
            "pins-import",
            "head-export",
            "commit-import",
            "prepare-evidence",
            "tombstones-import",
            "pins-link",
        ),
    )
    _ = agent.add_argument("name", nargs="?", default="")
    _ = agent.add_argument("--copy", action="append", default=[])
    _ = agent.add_argument("--form", default="clone", choices=("clone", "worktree"))
    _ = agent.add_argument("--home", default="")
    _ = agent.add_argument("--head", default="")
    _ = agent.add_argument("--token", default="")
    _ = agent.add_argument("--from", dest="source", default="")
    _ = agent.add_argument("--note", default="{}")
    _ = agent.add_argument("--replica", default="yes", choices=("yes", "no"))
    _ = agent.add_argument("--expect-tree", default="")
    _ = agent.add_argument("--refs", default="")
    _ = agent.add_argument("--digests", default="{}")
    _ = agent.add_argument("--identity", default="")
    _ = agent.add_argument("--generation", default="")
    _ = agent.add_argument("--former", default="")
    _ = agent.add_argument("--ref", action="append", default=[])
    _ = agent.add_argument("--have", action="append", default=[])
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one command; exit 0 clean, 1 conflicts or skipped work, 2 bad setup."""
    words = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    if not words or (words[0].startswith("-") and words[0] not in {"-h", "--help"}):
        words = ["status", *words]
    args = parser.parse_args(words, namespace=_Args())
    if args.command == "agent":
        return run_agent(args)
    handlers: dict[str, Callable[[_Args], int]] = {
        "status": cmd_status,
        "sync": cmd_sync,
        "handoff": cmd_handoff,
    }
    try:
        work.refuse_locating_env()
        work.check_layout(REPO_ROOT)
        return handlers[args.command](args)
    except (SetupError, work.WorkError) as error:
        print(f"fleet_sync: {error}", file=sys.stderr)
        return 2
    except FleetError as error:
        print(f"fleet_sync: {error}", file=sys.stderr)
        return 1


def _cli() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    _cli()
