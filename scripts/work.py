"""Make, list, pin, land and remove the private working copies an agent works in.

An agent that needs a tree of its own (a fix, a spike, a pristine-HEAD
attribution run, a carved commit to gate) works in a private copy under the
git-ignored ``.work/`` folder at the repository root, never in the shared
checkout and never in a copy it built by hand. This script owns that folder.
The REVIEW, HUNT and DRY flows keep ``scripts/workspace.py``, one manager per
flow; a name of kind ``review``, ``hunt`` or ``dry`` is refused here.

Layout (all under ``.work/``, which ``.gitignore`` lists)
    ``clones/<name>/``
        A ``git clone --no-hardlinks -o parent`` of the shared checkout, its
        ``HEAD`` detached at the start commit, its push URL ``no-push``, no
        ``branch.<name>.*`` tracking config (nothing in it tracks a branch). A
        clone has its own hooks, stash, config and refs: use one for a
        ref-rewriting experiment, a hook run or a move to another machine.
    ``worktrees/<name>/``
        A ``git worktree add --detach``, locked with the reason
        ``dsf-work <name>`` so ``git worktree prune`` never drops its
        metadata. A worktree has its own index, so ``git ls-files`` census
        gates work in it; it shares the shared checkout's hooks, refs and
        stash list.
    ``evidence/<stem>/``
        What a copy's work produced and must outlive it (proof scratch,
        pre-edit snapshots, database copies); a repro test belongs in the
        copy's own ``tests/`` tree, where its conftest applies. Keyed by the name's
        stem, so a ``-verify`` or ``-rN`` sibling shares its purpose's folder.
        Deleted only when asked (``rm --evidence``, ``evidence-rm``), on every
        fleet machine, never by age.
    ``names/<name>/``
        The claim on a name, one namespace for clones, worktrees and adopted
        copies, taken before anything else: a folder holding its owner
        (``<machine> <pid>``) renamed into place in one step, so no claim is seen
        without its owner and of two commands racing for one name (whatever
        form each asks for) only one wins. ``rm`` releases it; ``repair``
        releases a claim whose owner is known dead and reports any other claim
        with no copy.
    ``pins.git``
        A bare repository holding every pin (below). Pins live here, never in
        the shared repository, so no push of the shared repository (``git push
        --mirror`` included) can publish a snapshot of uncommitted work.
    ``trash/``
        Where ``rm`` moves a copy before deleting it, so a copy is never left
        half deleted under its own name. A replica ``fleet_sync.py`` removes
        stays there as ``<name>-<seconds>-kept`` for 7 days
        (``TRASH_RETENTION_SECONDS``), restorable, until ``gc`` deletes it; so
        does deleted evidence, as ``evidence-<stem>-<seconds>-kept`` (restore it
        with ``evidence-restore``, which gives each file a fresh mtime: a file moved
        back by hand keeps its recorded state and is deleted again unless touched).
    ``tombstones/<name>@<digest>.json``
        One per copy its home removed (``rm``, ``rm --discard``, ``gc``): the
        name, the home, the copy's identity (its note's ``incarnation``, else
        ``<start>@<created>``; the digest is of it, plus the home and handoff
        generation once a handoff moved it), the removal time and the machine,
        the copy's handoff lineage (``generation``, ``formerhomes``), whether
        ``--drop-saves`` dropped its saves, and the pins the removal dropped. A
        removal off the copy's home writes none; an ``rm`` of a name holding
        pins alone, and ``gc`` dropping start or landed pins, write one
        recording the pins dropped (identity ``pins@<digest>``).
        ``fleet_sync.py`` carries them to every machine,
        removes a replica only by one whose identity is the replica's and
        whose home is the replica's or a later home of it, never carries a
        recorded pin back, and drops one wherever no copy holds the name; ``gc``
        deletes them after 30 days (``TOMBSTONE_RETENTION_SECONDS``). A later
        copy under the same name has another identity, so an old tombstone
        never removes it.
    ``evidence-tombstones/<stem>@<digest>.json``
        One per explicit evidence deletion (``rm --evidence``, ``evidence-rm``):
        the stem, the machine, the moment, whether the whole folder went, the
        removed copy, and each deleted file's ``[size, mtime]``.
        ``fleet_sync.py`` carries them and, in a full sync, moves a file holding
        exactly a recorded state to the trash on every machine (a changed or later
        file is never touched) and carries none back; ``gc`` deletes them after 90
        days (``EVIDENCE_TOMBSTONE_RETENTION_SECONDS``). Apart from
        ``tombstones/``, so an older script never reads them. A state is a size and
        a whole-second mtime, not content: a file rewritten in the same second at
        the same size matches, and the trash keeps such a false match restorable.
        The record also names the removed copy's incarnation (its note's identity)
        and the pins it owned at the removal: that name, left holding pins alone,
        uses the stem nowhere only while every pin under it is one of those (a
        later copy's save under the name keeps the evidence; a record without
        them exempts no name). Only recorded files ever move, never a folder
        tree: a stem folder they leave empty is removed with ``rmdir``, one
        left holding other files stays, and so do files no sync carries
        (:data:`UNSYNCED`: a ``.venv``, caches), reported, for ``evidence-rm``
        there. Known limit: each move checks the stem folder by path, so one
        swapped for a symlink between that check and the rename (a concurrent
        layout change; a standing symlink is refused) can redirect it.
    ``stem-locks/<stem>.lock``
        The lifecycle lock of one evidence stem (:func:`stem_lock`): ``new``
        and ``adopt`` hold it while the name becomes a user of the stem,
        ``rm --evidence`` and ``evidence-rm`` while they check the users and
        delete, and a fleet sync's apply from its user check to its last move
        (tried once; held, the stem waits for the next full sync). A kernel
        lock, released however its holder ends; the files are never deleted.
    ``land.lock``
        A file one ``land`` (or ``repair``) at a time holds an exclusive kernel
        lock on (``flock``; ``msvcrt.locking`` on Windows): released however
        its holder ends, never taken over.
    ``pytest.lock``
        The kernel lock one pytest at a time holds across every copy of this
        checkout (``scripts/_locks.py``, which ``run`` and
        ``scripts/prove_failability.py`` both take); it holds its holder's
        copy, owner, machine and pid for the waiting line.
    ``land-journal.json``
        Every touched path's state before and after a landing, written
        (atomically) before the first path is; a landing that fails or is
        killed is undone from it by the next ``land`` or ``repair``. A path that
        cannot be read or written then keeps its entry (and the journal) until a
        later run can undo it.
    ``fleet/``, ``fleet.lock``
        ``docs/fleet/scripts/fleet_sync.py``'s holder token and evidence manifests, and the
        kernel lock one ``fleet_sync.py`` run (or one remote run's hold) takes.
    ``.git``
        A file holding ``gitdir: /nonexistent/dsf-work-sentinel``. A copy whose
        own ``.git`` is missing (or any folder under ``.work/`` without one)
        then makes git fail (exit 128) instead of silently
        resolving to the shared checkout around it. ``new`` and ``repair``
        write it.

``.work``, each folder above and each copy folder must be a real directory
under the real ``.work`` (no symlink anywhere on the way): every command
refuses a layout that is not, and a copy that is not is never read or changed.
``.work`` is kept ``0700``.

Every copy gets its own ``.venv`` (``uv sync --frozen``), its own copy of the
git-ignored ``.python-version``, ``core.longpaths=true`` and
``core.autocrlf=false`` in its own config (the worktree's ``--worktree``
config), and a Postgres database name of its own (``run`` rewrites
``FAKESHOP_PG_DSN`` to ``dsfw_<name>``). A clone also gets the pre-commit hook
(``pre-commit install`` when ``pre-commit`` is on ``PATH``); a failed sync or
hook install fails the ``new``.

Names say the purpose, never who made it: ``<kind>[-<id>]-<slug>[-verify|-rN]``,
lowercase ``[a-z0-9-]``, at most 24 characters (the Windows path budget), no
empty segment. Kinds: ``build``, ``fix``, ``spike``, ``verify``, ``ci``,
``bench``, ``head``, ``carve``, ``deps``, ``spec``, ``ship``. The id is
tracker-prefixed and records the number at creation: ``c051`` (card),
``i681`` (tracker item), ``s051`` (spec), ``u25`` (upstream item),
``g<sha7>`` (a commit), ``v0-0-15-2`` (a release, its dots as hyphens). A
second copy for one purpose takes ``-verify`` or ``-r2``; the stem (the name
without that suffix) keys the evidence folder.

The registry is derived, never a file: the folders under ``.work/``, ``git
worktree list --porcelain`` and the pins. Each copy's note (``dsf-work.*``:
name, form, purpose, owner, host, home, start commit, startshared (whether a
shared ref reached the start at ``new``; ``adopt`` records false), created,
incarnation (a random id ``new`` and ``adopt`` write), adopted, landed, pins
(the ``leaf=commit`` pins it published, :func:`record_pin`; ``new`` and
``adopt`` write it holding only the ``start`` pin they publish, so a pin another
copy left or a sync carried under the name is never this copy's; only a note
older than the key attributes by :func:`legacy_pins`), and the handoff
lineage ``fleet_sync.py handoff`` writes: generation, formerhomes)
lives in its own git config: the clone's ``.git/config``, the worktree's
``config.worktree`` (``extensions.worktreeConfig``, which ``new`` turns on
when it is off, first moving a repository-level ``core.worktree`` or
``core.bare = true`` into the main worktree's ``config.worktree`` as git's
documentation prescribes). Each copy folder is one record, whatever name
addresses it: a worktree's note names its folder (its git lock included). A note
naming an invalid copy name or a name other than its folder's, and a name two
folders claim, make every record involved unsafe: listed, never touched by
``rm``, ``gc`` or ``repair`` (``--discard`` included), and left for the
maintainer to fix by hand.

Every copy has one home machine, the only one that edits it: ``home`` in its note
(:func:`machine_id`; a note older than ``home`` reads its ``host``); machines are
named, and stored names read, by ``docs/fleet/scripts/fleet.py``'s rule (its "Identity").
``docs/fleet/scripts/fleet_sync.py`` keeps a replica of it on every
other fleet machine, marked ``replica=true`` with ``home``, ``syncedtree`` (its
content when last synced), ``syncedhead``, ``syncedfrom`` and ``syncedat``.
``save``, ``land`` and ``rm`` refuse a replica and name its home; ``rm
--discard`` alone removes one (this machine's replica, never the home's copy,
kept in ``.work/trash`` for 7 days), ``gc`` never does, and
``fleet_sync.py handoff <name>`` moves the home to this machine first.

Pins are refs in ``.work/pins.git``, not branches:
``refs/work/<name>/start`` (the commit a copy started from),
``refs/work/<name>/save-N`` (a snapshot of the copy's content: a commit whose
parent is the copy's ``HEAD``, built in a private index, so no index is
touched), ``refs/work/<name>/landed`` (what the last ``land`` applied) and
``refs/work/<name>/landed-copy`` (the copy's own content at that landing). A
``start`` or ``save-N`` pin is created only where none exists (``update-ref``
against an empty old value): two racing saves get two numbers, and no save is
ever replaced. ``landed`` and ``landed-copy`` are replaced on each landing by
compare-and-swap (``update-ref`` against the value read before), so a racing
landing is never overwritten. A
pinned commit survives its copy. Restore one with ``new <name> --from
refs/work/<old>/save-N``: the new copy starts at the save's parent and holds
the saved content as uncommitted work, so it lands like any other copy;
``landed`` and ``landed-copy`` restore the same way. Such a pin whose parent is not
on the shared main is refused (its copy could never land); ``--from`` a ``start``
pin starts at that commit itself.

A copy's content (what ``save`` pins, ``land`` applies and ``rm`` checks) is
read into a fresh private index from ``HEAD``, so the copy index's
``assume-unchanged`` bits, its stat cache and ``core.fsmonitor`` never hide an
edited file. A sparse checkout or a ``skip-worktree`` entry is refused: its
missing files would read as deletions.

Commands
    ``new <name> [--worktree] [--from REV] [--purpose TEXT] [--owner TEXT] [--no-setup]``
        Claim ``<name>``, then make a clone (default) or a worktree at ``REV``
        (default the shared ``HEAD``; the copy starts from committed content
        only, or from a pin as above), check git reads it as its own checkout,
        write its note, pin ``start``, copy ``.python-version``, run ``uv sync
        --frozen`` and, for a clone, ``pre-commit install``. ``--no-setup``
        skips the sync and the hook. ``--purpose`` (what the copy is for) and
        ``--owner`` (the session or agent, free text; default
        ``$DSF_WORK_OWNER``) are refused holding a newline or another control
        character. Refused for a name in use or claimed, a
        name with pins left from an earlier copy, below 6 GB free disk, and a
        kind ``workspace.py`` owns. A failure part way removes what it made.
        The claim and the copy folder are made under the stem's lock
        (``stem-locks/``), refused with nothing made when a fleet sync deleting
        the stem's evidence holds it past 10 s; ``adopt`` registers under it too.
    ``adopt <path> <name> [--purpose TEXT] [--owner TEXT]``
        Register, in place, a copy another tool made (``--purpose`` and
        ``--owner``, as for ``new``, hold no newline or other control
        character): a harness worktree
        (Claude Desktop ``.claude/worktrees/*``, Codex, Cursor, T3, OpenCode,
        Muse ``--workspace``) anywhere, or a clone already at
        ``.work/clones/<name>`` whose remote is this checkout (a local path) or
        a fleet machine's checkout over SSH (``<host>:<path>`` or
        ``ssh://<host>/<path>``, the host reaching a row of
        ``docs/fleet/machines.json`` as ``docs/fleet/scripts/fleet.py`` reads it (the
        row's name, an alias or its ``ssh`` host, any case or domain form); the
        account the one ssh logs in to that host as (``ssh -G``): no user part
        or that login; the port none or 22; the path that row's ``repo`` for
        that account, canonical). A broken machine list, or a host ``ssh -G``
        names no account for, refuses. Writes the note with ``adopted=true``
        and pins the copy's ``HEAD``. Never moves, locks or re-branches it:
        the harness keeps its own cleanup, and a branch the harness made is the
        harness's, not an agent-created branch. ``rm`` never deletes an
        adopted copy outside ``.work/``.
    ``list [--json]``
        Every known copy: name, form, state (``live``, ``landed``,
        ``folder-gone``, ``pins-only``, ``broken``, ``unsafe``), ``HEAD``,
        pins, path, purpose and owner (``owner=``, shell-quoted). ``pins.git``
        says which pins exist and the note which are the copy's: ``pins=`` the
        copy's own, ``foreign-pins=`` others under its name (an earlier copy's,
        a sync's), ``missing-pins=`` ones its note records that ``pins.git`` no
        longer holds (``--json``: ``pins``, ``foreign``, ``missing``; ``-``
        for none). A copy with no note owns every pin under its name.
    ``save <name>``
        Pin the copy's content as the next ``save-N``. Content equal to
        ``HEAD`` with ``HEAD`` still at the start pin saves nothing.
    ``land <name> [--dry-run] [--patch FILE] [--from-start]``
        Patch landing, the default way work reaches the shared checkout:
        copies do not commit. One ``land`` runs at a time (``land.lock``).
        The copy's content is diffed (``--binary``, new and deleted files
        included) against the copy's ``HEAD``, which must be on the shared
        ``main`` (so no committed work in the copy is dropped); the shared
        ``HEAD`` must be ``refs/heads/main``. After a landing it is diffed
        against the ``landed-copy`` pin instead (the copy's whole content at
        its last landing): only the copy's work since then lands, and a path
        unchanged since is never re-applied, whatever main did to it. Such an
        earlier-landed path that neither the shared ``HEAD`` nor the shared
        working tree holds as landed (reverted, never committed, changed
        since) is named in a note; ``--from-start`` diffs against the copy's
        ``HEAD`` again to land it. Without ``--from-start`` a copy whose note
        records a landing whose ``landed`` or ``landed-copy`` pin is missing,
        another copy's or incomplete refuses, and so does a path the copy put
        back at its ``HEAD`` entry (``reset --hard``, ``checkout --``) where
        its last landing held other content and the shared ``HEAD`` is not
        at that start entry (``--from-start`` lands the rest and leaves those
        paths as main holds them); a reset path main also has at the start
        changes nothing. An edit back to the start in part of a file lands like any
        edit. A path the shared tree already
        holds exactly as the copy does is skipped; every other touched path must
        hold exactly its ``HEAD`` entry there (bytes hashed and mode read from
        disk, index entry too, so an ``assume-unchanged`` bit hides nothing),
        and nothing lands under a folder that is a symlink in the
        shared checkout (refused when planning and again right before each
        write, so a write never follows a link out of it; a path that is
        itself a symlink blob is written as a link). The patch is first
        applied to a private index read from the shared ``HEAD``: that is the
        expected result, merged with whatever main changed since, and a patch
        that does not apply there refuses with nothing written, naming each
        path whose own patch does not apply. ``examples/fakeshop/db.sqlite3``
        is never a binary patch: the shared ``HEAD``'s database takes only the
        rows the copy changed since the patch's start (``scripts/_sqlite_rows.py``;
        printed as ``rows:`` under the path), so main's own rows and the copy's
        freelist residue stay out; a schema change, a row main changed too, a
        live ``-wal`` or ``-journal`` beside either database, or a result
        failing a constraint refuses with nothing written, and bytes that moved
        with no row skip the path. The journal is written, then
        each path (deletions first) is written into the working tree only
        (never the shared index): the new bytes go to a temporary file beside
        it, the path is re-hashed against its state before, and one
        ``os.replace`` publishes it. A path that changed, a failed write, or a
        branch or ``HEAD`` that moved puts every path holding what the landing
        wrote back as it was, keeps another writer's bytes untouched, names
        them, and refuses. The window between the last re-hash and the replace
        stays open: no protocol binds a plain editor in another session. On
        success the copy is marked landed and ``refs/work/<name>/landed`` pins
        the merged result on that ``HEAD`` (``landed-copy`` the copy's own
        content). ``--dry-run`` checks and reports without writing;
        ``--patch`` also writes the patch (the merged database as its binary
        diff from ``HEAD``). The maintainer commits; main stays
        linear.
    ``rm <name> [--discard] [--drop-saves] [--evidence]``
        Remove one copy: move it into ``.work/trash/`` (one rename, which a
        running process holding a file refuses on Windows), then delete it,
        granting the owner ``rwx`` on its folders (never a file's mode, which a
        hard link shares outside ``.work``; on Windows a read-only file with no
        other link gets its write bit), drop its worktree metadata, its start pin
        and its name claim. Files git ignores in the copy are not content:
        ``rm`` and ``gc`` delete them without a refusal. Refused for an unsafe path (above), a copy a process
        has its current directory in or one the process census cannot vouch
        for, a copy modified in the last 10 minutes and after its last save or
        landing, a copy holding ``scripts/workspace.py`` pool or state folders
        or ``scripts/prove_failability.py`` state, a worktree locked by anyone
        but this script, content that is neither ``HEAD``, a save nor the
        landed pin, a ``HEAD`` commit made in the copy that neither a shared
        branch, tag or remote-tracking ref nor a pin ``rm`` keeps reaches (a
        save pins it; a ``HEAD`` still at a start ``new`` found shared passes
        after main is amended past it), a ref that dies with the copy on such a
        commit (every ref of a clone, its ``refs/remotes/parent/`` ones passing
        while the shared repository holds their commit; a worktree's
        ``refs/bisect/``, ``refs/worktree/`` and ``refs/rewritten/``, its
        folder present or gone: its other refs are the shared repository's and
        outlive it; a commit only a reflog reaches counts as discarded), and
        content that cannot be read at all (a missing or broken
        ``.git``, a sparse checkout); ``--discard`` drops only those last four.
        Save and landed pins stay unless ``--drop-saves``; either way ``rm``
        drops only the pins the copy's own note attributes to it (its ``start``,
        and the ``pins`` it recorded publishing), so a pin under the name it
        cannot prove its own (an earlier copy's, or one a fleet sync carried
        in) is kept and named, for ``rm <name> --drop-saves`` of the name it then holds alone
        once checked; the evidence folder
        stays unless ``--evidence`` and no other name of the stem remains (a
        sibling copy or a name holding pins alone; the copy's own saves do not
        count, a pin under its name it cannot prove its own does), which then,
        holding ``.work/fleet.lock`` (waiting up to 60 s, else refusing with
        nothing removed) and the stem's lock (10 s), records an evidence
        tombstone naming the copy and the pins it owned and moves
        the folder to ``.work/trash/evidence-<stem>-<seconds>-kept``, in that
        order, as ``evidence-rm`` does. ``--evidence`` on a replica is refused with
        nothing removed: evidence is deleted from the copy's home. So is a name
        holding pins alone whose pins this machine cannot vouch it published (no
        tombstone of its own removal of that copy, made after every pin under the
        name: a replica's ``rm --discard`` leaves the home's pins and no tombstone).
        On the copy's home (``--discard`` included) it leaves a tombstone; on a
        replica (``--discard``) it removes this machine's replica alone and keeps
        it in ``.work/trash/<name>-<seconds>-kept`` for 7 days (a replica may be
        the last copy of its work), restorable, until ``gc`` deletes it.
        A copy moved to the trash that cannot be deleted is reported, its
        metadata, pins and claim dropped as for a removal, and it stays in
        ``.work/trash/`` for ``gc``; ``rm`` exits 1.
    ``evidence-rm <stem> [--file REL]... [--adopt-missing] [--dry-run]``
        Delete one stem's evidence on every fleet machine, for a stem no name
        uses (refused otherwise, a name holding pins alone included; a stem only
        a replica here uses is deleted from that copy's home): holding
        ``.work/fleet.lock`` as ``rm --evidence`` does, record the files in an
        evidence tombstone, then move them to the trash (the folder in one
        rename; with ``--file``, only those files, ``whole`` false, a path that
        is not plain and relative or that passes a symlink refused).
        ``--adopt-missing`` records the files removed here by hand that the peer
        manifests (``.work/fleet/evidence-<peer>.json``) still list, at their
        last synced states, one record per manifest; refused when
        ``.work/evidence`` itself is missing (a wipe is no deletion) or the stem
        folder is a symlink. ``--dry-run`` reports and writes nothing.
    ``evidence-restore <trash-entry-or-stem> [--dry-run]``
        Move the files of one ``.work/trash/evidence-<stem>-<seconds>-kept``
        entry (named, or the one entry a stem has) back into
        ``.work/evidence/<stem>/``, refusing with nothing moved when a file is
        already there, and give each restored file a fresh mtime (a second no
        evidence tombstone records for it), so no record matches it and the fleet
        sync carries it as a live file. Tombstones are never changed. Holds
        ``.work/fleet.lock`` as ``evidence-rm`` does; ``--dry-run`` reports and
        moves nothing.
    ``gc [--dry-run]``
        Remove only what is finished: a landed copy whose landed content the
        shared ``HEAD`` holds (each ``rm`` refusal still applies), worktree
        metadata of this script's copies whose folder is gone, start and
        landed pins of names with no copy left once the shared ``HEAD`` holds
        them, ``.work/trash/`` entries whose ``rm`` is no longer running (a
        ``-kept`` entry once 7 days have passed), tombstones older than 30
        days and evidence tombstones older than 90. A landed copy it removes
        leaves a tombstone as ``rm`` does, and the pins it drops by age a
        pins-only one, so no sync carries them back.
        Never a replica (its note ``replica``, or a home other than this
        machine, as a former home a handoff demoted): ``fleet_sync.py`` removes
        a replica, by its home's tombstone. Never a live copy that is not landed,
        never a landing main has not
        committed, never a save pin, never evidence. A copy or trash entry it
        cannot delete, or a trash folder it cannot list, is reported (exit 1)
        and the rest still runs. A landed copy whose landing the shared
        ``HEAD`` does not hold (not committed yet, or a later commit changed a
        landed path) is kept with a ``keep <name>: <reason>`` line in both
        modes, exit unchanged: ``rm`` it once checked.
    ``repair``
        Rewrite the ``.work/.git`` sentinel, repair worktree links (``git
        worktree repair``), restore a clone's ``no-push`` URL and every copy's
        ``core.longpaths`` / ``core.autocrlf``, re-pin a missing start pin
        from the note, release a stale claim (its ``new`` died), and report
        what it cannot fix: an unsafe copy (never touched), a copy without
        ``.git``, a leftover ``index.lock`` (never deleted), stray
        ``.coverage.*`` files at the shared root. Exits 1 while a problem it
        cannot fix remains.
    ``run <name> -- <command...>``
        Run ``<command>`` in the copy: current directory the copy, its
        ``.venv`` first on ``PATH`` and as ``VIRTUAL_ENV``, without the
        caller's ``GIT_*``, ``DIRENV_*``, ``DJANGO_*``, ``PYTEST_*``,
        ``COVERAGE_*`` variables, ``PYTHONPATH``, uv's project redirects and
        any other virtualenv's ``bin`` on ``PATH`` (direnv's activation of the
        shared ``.venv`` included); ``PROJECT_ROOT`` is the copy and
        ``FAKESHOP_PG_DSN``, when set, names the copy's own database.
        ``PYTHONPATH`` is cleared by design: a repro test goes in the copy's
        own ``tests/`` tree (a private clone, so its conftest applies), and
        ``.work/evidence/<stem>/`` holds only proof that must outlive the
        copy. Before the command runs, the copy's interpreter must import
        ``django_strawberry_framework`` from inside the copy, else the run is
        refused; then one line on stderr names where it runs (``work: run
        <name> in <copy> (.venv <venv>)``). A command any of whose words is
        ``pytest``, ``py.test`` (a path to one included) or ``-mpytest`` (so
        ``-m pytest`` and ``uv run --group pg pytest`` too) runs one at a time
        per checkout: it waits on ``.work/pytest.lock`` with one stderr line
        naming the holder, and starts with ``DSF_PYTEST_LOCK_HELD`` so a
        pytest it starts again never waits on it (``scripts/_locks.py``).
        A pytest started outside ``run`` and ``prove_failability.py`` takes no
        lock and is not seen. A copy
        whose git directory holds ``dsf-work-venv-stale`` (``fleet_sync.py``
        writes it on a replica, whose ``.venv`` never travels) has its
        ``.venv`` rebuilt with ``uv sync --frozen`` first. Returns the
        command's exit code (``128 + N`` for death by signal ``N``).
    ``check-name <name>``
        Validate a name and print its kind, id, slug and stem.

The process census behind ``rm``: Linux reads ``/proc/<pid>/cwd``, other
systems ask ``lsof -d cwd``. A census that fails, cannot read one of this
user's own processes, or does not see the process running it is incomplete,
and an incomplete census refuses, naming why (an unreadable process by pid
and command). The kernel hides the folder of a process that is not dumpable
or holds credentials or capabilities the caller lacks, which every Linux
login starts (``systemd --user``, ``(sd-pam)``, ``sshd-session``,
``ssh-agent``): an own process is skipped only when its ``comm`` and
``cmdline``, which stay readable, name one of ``CENSUS_SKIPPED_DAEMONS``,
login and agent daemons that run no user's work and hold no file under their
folder. Another user's process it cannot read (and ``lsof`` never lists) is
skipped only while a folder above the copy is this user's and closed to
everyone else (``.work`` is ``0700``), since no other non-root user can then
be inside; otherwise the census is incomplete. Root's processes stay
invisible.

A copy holding a nested repository or a submodule is refused by ``save``,
``land`` and ``rm`` (``rm --discard`` aside): no tree carries that
repository's uncommitted work.

Landing a copy from another machine: on that machine, clone with this
machine's checkout as the ``parent`` remote over SSH (``git clone
--no-hardlinks -o parent <ssh-host>:<checkout path> .work/clones/<name>``, the
host and path from ``docs/fleet/machines.json``, then ``git remote set-url
--push parent no-push``), work
there, and bring the work back as a patch (``git diff --binary HEAD`` after
``git add -N .``) applied here by the coordinator, the same rule ``land``
follows. ``docs/fleet/scripts/fleet_sync.py`` replicates a whole copy (its ``.git`` included)
under its own rules (one writer per copy, never while a process works in it);
never rsync a ``.git`` by hand.

Every command refuses while ``GIT_DIR``, ``GIT_WORK_TREE`` or
``GIT_INDEX_FILE`` is set: a command run mid-carve against a private index
would read or write the wrong repository or index. A folder the registry
cannot list (``.work/clones``, ``.work/worktrees``) refuses; a copy folder
that cannot be looked into lists as broken. Exit codes: ``0`` success,
``1`` a refusal or failure (the reason on stderr, an operating-system error
too), ``2`` a usage error; ``run``
returns the command's code and ``125`` when it refused before starting it.

Standard library and ``scripts/_git.py`` only for the git and copy work;
``scripts/workspace.py`` and ``scripts/prove_failability.py`` are read only to
find their state folders for a copy, so the two scripts and this one name the
same paths. Run from the shared checkout as ``uv run python scripts/work.py
...``. A ``work.py`` started inside a copy (``.work/clones/<name>``,
``.work/worktrees/<name>``) works on the shared checkout around it for ``list``,
``save``, ``run`` and ``check-name``, and refuses every other command (``run work.py
from the shared checkout <path>``): those write the shared tree or other copies, never
from a copy's own, perhaps edited, script. Another interpreter is refused in one line
naming ``uv run python``: below Python 3.10 before anything runs, and one lacking a
module a command reads (a bare ``python3`` has no ``tomli``) once it needs it.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import hashlib
import json
import math
import os
import re
import secrets
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, NoReturn
from urllib.parse import urlsplit, urlunsplit

if __package__:  # imported as ``scripts.work`` (repo root on path)
    from docs.fleet.scripts import fleet
    from scripts import _git as _git_runner
    from scripts import _locks, _sqlite_rows
else:  # run or imported from its own folder: fleet.py lives in the checkout's docs/fleet/scripts/
    sys.path.insert(1, str(Path(__file__).resolve().parents[1] / "docs" / "fleet" / "scripts"))
    import _git as _git_runner
    import _locks
    import _sqlite_rows
    import fleet

if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Generator, Iterable, Mapping, Sequence

#: ``json.loads``, its result typed ``object`` for the caller to narrow.
_loads: Callable[[str], object] = json.loads

REPO_ROOT = _git_runner.CHECKOUT_ROOT
#: How work.py runs: ``uv run`` gives it the project's Python and every module it reads.
RUN_AS = "run work.py as `uv run python scripts/work.py ...`"
# ``requires-python``: the module below needs 3.10 to load. ``hexversion``, since the checkers
# take that floor as given and read a ``version_info`` test as dead code; a bare ``python3`` does not.
if sys.hexversion < 0x030A0000:
    raise SystemExit(f"work: {sys.executable} is Python {sys.version.split()[0]}; {RUN_AS}")
WORK_DIR = ".work"
CLONES = "clones"
WORKTREES = "worktrees"
EVIDENCE = "evidence"
NAMES = "names"
TRASH = "trash"
PIN_STORE = "pins.git"
LAND_LOCK = "land.lock"
LAND_JOURNAL = "land-journal.json"
#: The kernel lock one pytest at a time holds (``scripts/_locks.py``).
PYTEST_LOCK = _locks.PYTEST_LOCK
JOURNAL_KEPT = "the journal is kept for the next land or repair"
#: ``docs/fleet/scripts/fleet_sync.py``'s folder (its holder token, evidence manifests) and its
#: lock.
FLEET = "fleet"
FLEET_LOCK = "fleet.lock"
#: Where a home's removal of a copy leaves its tombstone, the one record a replica is removed by.
TOMBSTONES = "tombstones"
#: Where an explicit evidence deletion leaves its record (:class:`EvidenceTombstone`), apart
#: from the copy tombstones so a script that predates it never reads, relays or strips one.
EVIDENCE_GRAVES = "evidence-tombstones"
#: One lock file per evidence stem (:func:`stem_lock`), never deleted.
STEM_LOCKS = "stem-locks"
DIR_CONTAINERS = (
    CLONES,
    WORKTREES,
    EVIDENCE,
    NAMES,
    TRASH,
    PIN_STORE,
    FLEET,
    TOMBSTONES,
    EVIDENCE_GRAVES,
    STEM_LOCKS,
)
FILE_ENTRIES = (
    LAND_LOCK,
    LAND_JOURNAL,
    FLEET_LOCK,
    PYTEST_LOCK,
)
SENTINEL_TEXT = "gitdir: /nonexistent/dsf-work-sentinel\n"
PIN_PREFIX = "refs/work/"
INCOMING_PREFIX = "refs/work-incoming/"
START_PIN = "start"
LANDED_PIN = "landed"
LANDED_COPY_PIN = "landed-copy"
CLAIM_GRACE_SECONDS = 60
SAVE_PIN = re.compile(r"^save-(\d+)$")
NOTE_SECTION = "dsf-work"
#: The note key listing the pins a copy published (``leaf=commit``, comma-separated): what
#: tells its own pins from those another copy left under the name (:func:`pin_belongs`).
PINS_NOTE = "pins"
LOCK_REASON_PREFIX = "dsf-work "
LANDING_BRANCH = "refs/heads/main"
#: The shared repository's own refs: a commit one of them reaches outlives every copy.
SHARED_REFS = ("refs/heads/", "refs/tags/", "refs/remotes/")
#: A clone's remote-tracking refs of the shared repository it was cloned from.
PARENT_REFS = "refs/remotes/parent/"
#: The refs git keeps per worktree, in its metadata: they die with the worktree.
PER_WORKTREE_REFS = ("refs/bisect/", "refs/worktree/", "refs/rewritten/")
NO_PUSH = "no-push"
#: A file in a copy's git directory: its ``.venv`` came from another machine or none exists,
#: so ``run`` rebuilds it (``uv sync --frozen``) first.
VENV_STALE = "dsf-work-venv-stale"
#: Tracked SQLite databases ``land`` merges row by row (``scripts/_sqlite_rows.py``), never
#: as a binary patch.
ROW_MERGED_PATHS = frozenset({"examples/fakeshop/db.sqlite3"})
MIN_FREE_BYTES = 6 * 1024**3
RECENT_SECONDS = 10 * 60
#: How long a replica ``fleet_sync.py`` removed stays restorable in ``.work/trash`` before
#: ``gc`` deletes it.
TRASH_RETENTION_SECONDS = 7 * 24 * 60 * 60
#: How long ``gc`` keeps a tombstone: past the trash retention, and long enough for a machine
#: that was offline to come back and drop its replica.
TOMBSTONE_RETENTION_SECONDS = 30 * 24 * 60 * 60
#: How long ``gc`` keeps an evidence tombstone: a machine offline for less still deletes the
#: files when it returns, one offline longer brings them back.
EVIDENCE_TOMBSTONE_RETENTION_SECONDS = 90 * 24 * 60 * 60
#: Seconds ``rm --evidence`` and ``evidence-rm`` wait for ``.work/fleet.lock`` before refusing.
EVIDENCE_LOCK_WAIT_SECONDS = 60.0
#: Seconds ``new``, ``adopt``, ``rm --evidence`` and ``evidence-rm`` wait for a stem's lock
#: (:func:`stem_lock`) before refusing; a fleet sync's apply never waits for one.
STEM_LOCK_WAIT_SECONDS = 10.0
#: The first moment no record may carry (2106): a ``removedat`` is a real time below it.
RECORD_MOMENT_LIMIT = 2.0**32
#: Regenerable or per-platform files no transfer carries and no evidence listing holds.
UNSYNCED = (
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "node_modules",
    "*.pyc",
)
#: The last part of a trash entry kept for :data:`TRASH_RETENTION_SECONDS`, not deleted at once.
KEPT_TRASH = "kept"
#: Whether a read-only file refuses its own delete (Windows); elsewhere its folder decides.
READ_ONLY_FILES_BLOCK_DELETE = os.name == "nt"
REFUSED = 125
LOCATING_NAMES = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
EXTRA_FILES = (".python-version",)
COPY_CONFIG = (("core.longpaths", "true"), ("core.autocrlf", "false"))
#: Index trust a content read never takes from the copy's config.
UNTRUSTED_CACHES = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.untrackedCache=false",
)
#: Lets ``pins.git`` fetch a commit by id from a copy that holds no ref to it.
FETCH_BY_ID = ("-c", "uploadpack.allowAnySHA1InWant=true")
#: Folders never read when deciding when a copy was last modified.
UNWATCHED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "node_modules",
    },
)
SCRUBBED_PREFIXES = (
    "GIT_",
    "DIRENV_",
    "DJANGO_",
    "PYTEST_",
    "COVERAGE_",
)
SCRUBBED_NAMES = frozenset(
    {
        "PYTHONPATH",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "VIRTUAL_ENV",
        "VIRTUAL_ENV_PROMPT",
        "CONDA_PREFIX",
        "PROJECT_ROOT",
        "UV_PROJECT_ENVIRONMENT",
        "UV_PROJECT",
        "UV_WORKING_DIRECTORY",
        "UV_NO_SYNC",
        "UV_FROZEN",
        "UV_LOCKED",
    },
)
PG_DSN_ENV = "FAKESHOP_PG_DSN"
PACKAGE = "django_strawberry_framework"
SAVE_IDENTITY = {
    "GIT_AUTHOR_NAME": "work.py",
    "GIT_AUTHOR_EMAIL": "work@localhost",
    "GIT_COMMITTER_NAME": "work.py",
    "GIT_COMMITTER_EMAIL": "work@localhost",
}
MAX_SAVE_ATTEMPTS = 100

KINDS = (
    "build",
    "fix",
    "spike",
    "verify",
    "ci",
    "bench",
    "head",
    "carve",
    "deps",
    "spec",
    "ship",
)
WORKSPACE_KINDS = ("review", "hunt", "dry")
MAX_NAME_LENGTH = 24
SEGMENT = re.compile(r"^[a-z0-9]+$")
ID_SEGMENT = re.compile(r"^(?:c\d+|i\d+|s\d+|u\d+|g[0-9a-f]{7})$")
VERSION_HEAD = re.compile(r"^v\d+$")
DIGITS = re.compile(r"^\d+$")
SUFFIX_SEGMENT = re.compile(r"^(?:verify|r\d+)$")


class WorkError(Exception):
    """A refusal or failure; the message says why and what to do."""


# --------------------------------------------------------------------------------------------
# Names
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Name:
    """A parsed copy name: ``<kind>[-<id>]-<slug>[-<suffix>]``."""

    text: str
    kind: str
    id: str | None
    slug: str
    suffix: str | None

    @property
    def stem(self) -> str:
        """Return the name without its ``-verify`` / ``-rN`` suffix, which keys the evidence."""
        return self.text if self.suffix is None else self.text[: -len(self.suffix) - 1]


def parse_name(text: str) -> Name:
    """Parse ``text`` as a copy name.

    Raises:
        WorkError: ``text`` breaks the grammar; the message names the rule.

    """
    if not text or len(text) > MAX_NAME_LENGTH:
        msg = f"name {text!r} must be 1 to {MAX_NAME_LENGTH} characters"
        raise WorkError(msg)
    segments = text.split("-")
    if not all(SEGMENT.fullmatch(segment) for segment in segments):
        msg = f"name {text!r} must be lowercase [a-z0-9] segments joined by single hyphens"
        raise WorkError(msg)
    kind, rest = segments[0], segments[1:]
    if kind in WORKSPACE_KINDS:
        msg = f"kind {kind!r} belongs to scripts/workspace.py (one manager per flow)"
        raise WorkError(msg)
    if kind not in KINDS:
        msg = f"name {text!r} must start with a kind: {', '.join(KINDS)}"
        raise WorkError(msg)
    identifier: str | None = None
    if rest and ID_SEGMENT.fullmatch(rest[0]):
        identifier, rest = rest[0], rest[1:]
    elif rest and VERSION_HEAD.fullmatch(rest[0]):
        taken = 1
        while taken < len(rest) and DIGITS.fullmatch(rest[taken]):
            taken += 1
        identifier, rest = "-".join(rest[:taken]), rest[taken:]
    suffix: str | None = None
    if len(rest) > 1 and SUFFIX_SEGMENT.fullmatch(rest[-1]):
        suffix, rest = rest[-1], rest[:-1]
    if not rest:
        msg = f"name {text!r} needs a slug saying the purpose after the kind and id"
        raise WorkError(msg)
    return Name(text, kind, identifier, "-".join(rest), suffix)


def _valid(name: str) -> bool:
    try:
        _ = parse_name(name)
    except WorkError:
        return False
    return True


# --------------------------------------------------------------------------------------------
# Machines: a copy's home, a replica
# --------------------------------------------------------------------------------------------


def machine_id() -> str:
    """Return this machine's name for a record (``fleet.this_machine_name``, this checkout's list)."""
    return fleet.this_machine_name(repo=REPO_ROOT)


def canonical(name: str) -> str:
    """Return the machine a stored ``name`` means (``fleet.canonical`` of this checkout's list)."""
    return fleet.canonical(name, repo=REPO_ROOT)


def home_of(note: Mapping[str, str]) -> str:
    """Return the machine a copy's note names as its home (a note older than ``home``: its host).

    Read through :func:`canonical`, so a home stored under a machine's alias is that machine.
    """
    return canonical(note.get("home") or note.get("host", ""))


def is_replica(note: Mapping[str, str]) -> bool:
    """Return whether the note marks the copy a replica ``fleet_sync.py`` keeps of its home's copy."""
    return note.get("replica") == "true"


def refuse_replica(copy: Copy, verb: str) -> None:
    """Refuse ``verb`` on a replica: only its home edits, saves, lands or removes it.

    Raises:
        WorkError: the copy is a replica; the message names its home and the handoff.

    """
    if not is_replica(copy.note):
        return
    home = home_of(copy.note)
    msg = (
        f"{copy.name} is a replica of {home}'s copy: {verb} it on {home}, or move its home "
        f"here first (`uv run python docs/fleet/scripts/fleet_sync.py handoff {copy.name}`)"
    )
    raise WorkError(msg)


def copy_identity(note: Mapping[str, str]) -> str:
    """Return what tells this incarnation of a copy from a later copy reusing its name.

    The note's ``incarnation`` (a random id ``new`` and ``adopt`` write), else, for a note
    older than it, ``<start>@<created>``; ``""`` when the note holds neither. A replica
    carries these keys from its home, so both name one incarnation alike.
    """
    incarnation = note.get("incarnation", "")
    if incarnation:
        return incarnation
    start, created = note.get("start", ""), note.get("created", "")
    return f"{start}@{created}" if start and created else ""


def handoff_generation(note: Mapping[str, str]) -> int:
    """Return how many handoffs moved the copy's home (``generation``; ``0`` before any)."""
    raw = note.get("generation", "")
    return int(raw) if raw.isdigit() else 0


def former_homes(note: Mapping[str, str]) -> tuple[str, ...]:
    """Return the machines a handoff moved the copy's home away from (:func:`canonical`), oldest first."""
    return tuple(canonical(home) for home in note.get("formerhomes", "").split(",") if home)


def later_home(newer: Mapping[str, str], older: Mapping[str, str]) -> bool:
    """Return whether ``newer`` names a later home of the copy ``older`` names.

    The home ``older`` records is one ``newer`` lists as former (``formerhomes``) and
    ``newer`` is the later handoff (``generation``): a replica a handoff missed (its machine
    offline) still records the home it was synced from, and the newest home wins. Callers
    check the identity (``fleet_sync.same_copy``).
    """
    return home_of(older) in former_homes(newer) and handoff_generation(
        newer,
    ) > handoff_generation(older)


def record_moment(value: object) -> float | None:
    """Return a record's ``removedat`` as seconds when it is a real time, else ``None``.

    A number (no bool), finite, from ``0`` up to :data:`RECORD_MOMENT_LIMIT`: retention
    compares it (:func:`past_retention`), and a NaN or an infinity would keep a record for
    ever or reap it at once. The record holding another value is refused whole.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not 0 <= value < RECORD_MOMENT_LIMIT or not math.isfinite(value):
        return None
    return float(value)


@dataclasses.dataclass(frozen=True)
class Tombstone:
    """A home's record that it removed one incarnation of a copy (``.work/tombstones/``).

    ``generation`` and ``former_homes`` are the copy's handoff lineage at the removal (its
    note's ``generation`` and ``formerhomes``), so the removal reaches a replica a handoff
    missed; ``saves_dropped`` says ``rm --drop-saves`` dropped its saves, and
    ``dropped_pins`` (``(leaf, commit)`` pairs) are the pins the removal dropped, which no
    sync carries back and which a machine holding no copy under the name drops too.
    ``home`` and ``removed_by`` are the names the file stores (its digest covers ``home``):
    compare them through :func:`canonical`, never as stored.
    """

    name: str
    home: str
    identity: str
    removed_at: float
    removed_by: str
    generation: int = 0
    former_homes: tuple[str, ...] = ()
    saves_dropped: bool = False
    dropped_pins: tuple[tuple[str, str], ...] = ()

    @property
    def file_name(self) -> str:
        """Return the tombstone's file name: one per name, incarnation and handoff generation.

        A removal before any handoff keeps the name the identity alone gives (tombstones
        older than handoff lineage), a later one adds its home and generation, so two homes
        of one incarnation (a handoff forced while its home was offline) never share a file.
        """
        key = self.identity
        if self.generation:
            key = f"{self.identity}\0{self.home}\0{self.generation}"
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return f"{self.name}@{digest}.json"

    def buries(self, name: str, note: Mapping[str, str]) -> bool:
        """Return whether this tombstone removes the replica ``name`` whose note is ``note``.

        Same name and identity, and the replica records this home (from no later
        generation) or a former home of it (:func:`later_home`): the newest home's removal
        reaches a replica a handoff missed, an older home's never reaches a newer one's.
        """
        identity = copy_identity(note)
        if not identity or name != self.name or identity != self.identity:
            return False
        if home_of(note) == canonical(self.home):
            return self.generation >= handoff_generation(note)
        return later_home(
            {
                "home": self.home,
                "generation": str(self.generation),
                "formerhomes": ",".join(self.former_homes),
            },
            note,
        )

    def as_json(self) -> dict[str, object]:
        """Return the tombstone as its JSON document."""
        return {
            "name": self.name,
            "home": self.home,
            "identity": self.identity,
            "removedat": self.removed_at,
            "removedby": self.removed_by,
            "generation": self.generation,
            "formerhomes": list(self.former_homes),
            "savesdropped": self.saves_dropped,
            "droppedpins": dict(self.dropped_pins),
        }

    @classmethod
    def parse(cls, raw: object) -> Tombstone | None:
        """Return the tombstone a JSON document holds, ``None`` for anything else."""
        if not fleet.is_json_object(raw):
            return None
        fields = [
            raw.get(key)
            for key in (
                "name",
                "home",
                "identity",
                "removedby",
            )
        ]
        strings = [field for field in fields if isinstance(field, str) and field]
        removed_at = record_moment(raw.get("removedat"))
        if len(strings) != len(fields) or not _valid(strings[0]) or removed_at is None:
            return None
        name, home, identity, removed_by = strings
        generation = raw.get("generation", 0)
        formers = raw.get("formerhomes", [])
        dropped = raw.get("savesdropped", False)
        pinned = raw.get("droppedpins", {})
        if (
            isinstance(generation, bool)
            or not isinstance(generation, int)
            or generation < 0
            or not isinstance(dropped, bool)
            or not fleet.is_json_array(formers)
            or not fleet.is_json_object(pinned)
        ):
            return None
        homes = [entry for entry in formers if isinstance(entry, str) and entry]
        pairs = [(leaf, sha) for leaf, sha in pinned.items() if isinstance(sha, str)]
        if len(homes) != len(formers) or len(pairs) != len(pinned):
            return None
        return cls(
            name,
            home,
            identity,
            removed_at,
            removed_by,
            generation,
            tuple(homes),
            dropped,
            tuple(sorted(pairs)),
        )


def tombstones(repo: Path) -> list[Tombstone]:
    """Return every readable tombstone under ``.work/tombstones`` (a broken file is skipped)."""
    folder = work_dir(repo) / TOMBSTONES
    if not folder.is_dir():
        return []
    found = (read_tombstone(repo, path.name) for path in sorted(folder.glob("*.json")))
    return [tombstone for tombstone in found if tombstone is not None]


def _record_file(folder: Path, file_name: str) -> Path | None:
    """Return ``folder / file_name`` for a record's own file name, ``None`` for any other name.

    A record's name is one plain ``*.json`` file name (no separator, not a staged dot name),
    so a name another machine sends never reaches a path outside ``folder``.
    """
    if (
        not file_name.endswith(".json")
        or file_name.startswith(".")
        or Path(file_name).name != file_name
        or "\\" in file_name
        or "\0" in file_name
    ):
        return None
    return folder / file_name


def _record_text(folder: Path, file_name: str) -> object:
    """Return the JSON the record file ``file_name`` holds, ``None`` when it is unreadable."""
    path = _record_file(folder, file_name)
    if path is None:
        return None
    try:
        return _loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def read_tombstone(repo: Path, file_name: str) -> Tombstone | None:
    """Return the tombstone published as ``file_name``, ``None`` when none reads back as it.

    A file whose body names another file (:attr:`Tombstone.file_name`) is no tombstone.
    """
    tombstone = Tombstone.parse(_record_text(work_dir(repo) / TOMBSTONES, file_name))
    return tombstone if tombstone is not None and tombstone.file_name == file_name else None


def past_retention(removed_at: float, retention: float, now: float | None = None) -> bool:
    """Return whether a record removed at ``removed_at`` outlived ``retention`` seconds.

    ``gc`` deletes such a record, and no fleet sync carries one to a machine lacking it, so a
    record ``gc`` deleted never comes back from a machine that has not run ``gc`` yet.
    """
    return removed_at < (time.time() if now is None else now) - retention


def write_tombstone(repo: Path, tombstone: Tombstone) -> bool:
    """Publish ``tombstone`` create-only; return whether it wrote the file.

    The document is staged in full, then hard-linked into place (``os.link`` fails on an
    existing name, so no writer replaces a tombstone another already published, and no
    reader sees a half-written one). A file already there is never replaced: one holding
    this very tombstone is success (``False``, nothing to write).
    """
    return _publish_once(
        _container(repo, TOMBSTONES, create=True),
        tombstone.file_name,
        tombstone.as_json(),
    )


def _publish_once(folder: Path, file_name: str, document: Mapping[str, object]) -> bool:
    """Write ``document`` to ``folder / file_name`` create-only; return whether it wrote it.

    Staged in full under a dot name, then hard-linked into place: ``os.link`` fails on an
    existing name, so nothing replaces a published file and no reader sees half of one.
    """
    target = folder / file_name
    staged = folder / f".{file_name}.{_token()}"
    _ = staged.write_text(json.dumps(document, sort_keys=True), encoding="utf-8")
    try:
        os.link(staged, target)
    except FileExistsError:
        return False
    finally:
        staged.unlink(missing_ok=True)
    return True


def _bury(
    repo: Path,
    copy: Copy,
    dropped: Mapping[str, str],
    *,
    saves_dropped: bool,
) -> None:
    """Leave a tombstone for a copy its home removes; a replica or another's copy gets none.

    ``dropped`` are the pins the removal drops (leaf to commit). A name holding pins alone
    has no home: when its ``rm`` drops pins, a tombstone of identity ``pins@<digest of
    them>`` (no copy's) records them, so no sync brings them back.
    """
    here = machine_id()
    pinned = tuple(sorted(dropped.items()))
    if copy.form == "pins":
        bury_pins(repo, copy.name, dropped, saves_dropped=saves_dropped)
        return
    identity = copy_identity(copy.note)
    if not identity or is_replica(copy.note) or home_of(copy.note) != here:
        return
    tombstone = Tombstone(
        copy.name,
        here,
        identity,
        time.time(),
        here,
        handoff_generation(copy.note),
        former_homes(copy.note),
        saves_dropped,
        pinned,
    )
    _ = write_tombstone(repo, tombstone)


def bury_pins(
    repo: Path,
    name: str,
    dropped: Mapping[str, str],
    *,
    saves_dropped: bool,
) -> None:
    """Leave a pins-only tombstone recording the ``dropped`` pins (leaf to commit) of ``name``.

    Its identity is ``pins@<digest of them>``, no copy's, so it removes no replica; it only
    stops every sync carrying those pins back and drops them wherever no copy holds the name.
    Nothing dropped writes none.
    """
    pinned = tuple(sorted(dropped.items()))
    if not pinned:
        return
    here = machine_id()
    tombstone = Tombstone(
        name,
        here,
        pins_identity(dropped),
        time.time(),
        here,
        saves_dropped=saves_dropped,
        dropped_pins=pinned,
    )
    _ = write_tombstone(repo, tombstone)


def pins_identity(pinned: Mapping[str, str]) -> str:
    """Return the identity of a name holding the pins ``pinned`` alone: ``pins@<digest of them>``."""
    listed = "\0".join(f"{leaf}={sha}" for leaf, sha in sorted(pinned.items()))
    return f"pins@{hashlib.sha256(listed.encode('utf-8')).hexdigest()[:16]}"


def drop_buried_pins(repo: Path, name: str) -> list[str]:
    """Drop each pin of ``name`` a tombstone records its removal dropped; return the leaves.

    Only while no copy holds the name here (pins alone may), and only a pin still at the
    commit the tombstone records: a later copy's pin under the leaf is another commit.
    """
    copy = discover(repo).get(name)
    if copy is not None and copy.form != "pins":
        return []
    held = pins(repo).get(name, {})
    dropped: list[str] = []
    for grave in tombstones(repo):
        if grave.name != name:
            continue
        for leaf, sha in grave.dropped_pins:
            if leaf not in dropped and held.get(leaf) == sha:
                drop_pin(repo, name, leaf, sha)
                dropped.append(leaf)
    return dropped


# --------------------------------------------------------------------------------------------
# Evidence tombstones: an explicit deletion of evidence files, carried by the fleet sync
# --------------------------------------------------------------------------------------------


def stem_of(name: str) -> str:
    """Return the evidence stem a copy name keys (a name outside the grammar is its own stem)."""
    return parse_name(name).stem if _valid(name) else name


def valid_stem(stem: str) -> bool:
    """Return whether ``stem`` is a plain folder name under ``.work/evidence``.

    Not the copy-name grammar: evidence folders such as ``lead-merge`` or
    ``load-balancer.patch`` exist. Refused: empty, a leading dot (``.``, ``..``, a staged
    file), a path separator, a control character.
    """
    return (
        bool(stem)
        and not stem.startswith(".")
        and not any(char in "/\\" or ord(char) < 32 for char in stem)
    )


def evidence_rel(rel: str) -> bool:
    """Return whether ``rel`` is a canonical relative POSIX path (no ``.``, ``..`` or root)."""
    path = PurePosixPath(rel)
    return (
        bool(rel)
        and "\0" not in rel
        and not path.is_absolute()
        and path.as_posix() == rel
        and not {".", ".."}.intersection(path.parts)
    )


def file_state(info: os.stat_result) -> tuple[int, int]:
    """Return a file's evidence state: its size and whole-second mtime (what rsync ``-t`` keeps)."""
    return info.st_size, int(info.st_mtime)


@dataclasses.dataclass(frozen=True)
class EvidenceTombstone:
    """An explicit deletion of evidence files (``.work/evidence-tombstones/``).

    ``files`` holds ``(rel, size, mtime)`` for every file deleted: another machine deletes a
    file only while it holds exactly that state, so a file changed since, or a later file at
    the same path, is never touched, whatever any clock says. ``removed_at`` serves retention
    alone. ``whole`` says the stem folder itself went (``rm --evidence``, ``evidence-rm
    <stem>``), not chosen files (``--file``). ``copy`` names the copy whose ``rm`` wrote it
    (``""`` for ``evidence-rm``), ``identity`` that incarnation (:func:`copy_identity`;
    :func:`pins_identity` for a name holding pins alone) and ``pins`` the ``(leaf, commit)``
    pairs it owned at the removal (:class:`RemovedCopy`): that name holding pins alone uses
    the stem nowhere while every pin under it is one of those. A record without an
    ``identity`` exempts no name.

    The file name digests the stem, the moment and the files, never ``whole``, ``copy``,
    ``identity`` or ``pins``: an older script that relays the record drops the fields it does
    not know under the same name, and the stripped record exempts nothing.
    """

    stem: str
    home: str
    removed_at: float
    removed_by: str
    files: tuple[tuple[str, int, int], ...]
    whole: bool
    copy: str = ""
    identity: str = ""
    pins: tuple[tuple[str, str], ...] = ()

    @property
    def removed(self) -> RemovedCopy | None:
        """Return the removed copy this record exempts, ``None`` for an ``evidence-rm``."""
        return RemovedCopy(self.copy, self.identity, self.pins) if self.copy else None

    @property
    def states(self) -> dict[str, tuple[int, int]]:
        """Return ``{rel: (size, mtime)}``."""
        return {rel: (size, mtime) for rel, size, mtime in self.files}

    @property
    def file_name(self) -> str:
        """Return the record's file name: one per stem, moment and file set."""
        listed = {rel: [size, mtime] for rel, size, mtime in self.files}
        key = f"{self.stem}\0{json.dumps(self.removed_at)}\0{json.dumps(listed, sort_keys=True)}"
        return f"{self.stem}@{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}.json"

    def matches(
        self,
        rel: str,
        size: int,
        mtime: int,
    ) -> bool:
        """Return whether ``rel`` holding ``(size, mtime)`` is a state this record deleted."""
        return self.states.get(rel) == (size, mtime)

    def as_json(self) -> dict[str, object]:
        """Return the record as its JSON document."""
        return {
            "kind": "evidence",
            "stem": self.stem,
            "home": self.home,
            "removedat": self.removed_at,
            "removedby": self.removed_by,
            "whole": self.whole,
            "copy": self.copy,
            "identity": self.identity,
            "pins": dict(self.pins),
            "files": {rel: [size, mtime] for rel, size, mtime in self.files},
        }

    @classmethod
    def parse(cls, raw: object) -> EvidenceTombstone | None:
        """Return the record a JSON document holds, ``None`` for anything else.

        A stem that is no plain folder name, any path that is not canonical and relative, or a
        moment that is no real time (:func:`record_moment`) refuses the whole record: it comes
        from another machine and fails closed. A record older than ``identity`` and ``pins``
        reads with neither.
        """
        if not fleet.is_json_object(raw) or raw.get("kind") != "evidence":
            return None
        stem, home, removed_by = (raw.get(key) for key in ("stem", "home", "removedby"))
        removed_at, whole, copy = (
            record_moment(raw.get("removedat")),
            raw.get("whole"),
            raw.get("copy", ""),
        )
        identity, pinned, listed = raw.get("identity", ""), raw.get("pins", {}), raw.get("files")
        if (
            not isinstance(stem, str)
            or not valid_stem(stem)
            or not isinstance(home, str)
            or not home
            or not isinstance(removed_by, str)
            or not removed_by
            or removed_at is None
            or not isinstance(whole, bool)
            or not isinstance(copy, str)
            or not isinstance(identity, str)
            or not fleet.is_json_object(pinned)
            or not fleet.is_json_object(listed)
        ):
            return None
        pairs = [(leaf, sha) for leaf, sha in pinned.items() if isinstance(sha, str) and sha]
        if len(pairs) != len(pinned):
            return None
        files: list[tuple[str, int, int]] = []
        for rel, state in listed.items():
            if not evidence_rel(rel) or not fleet.is_json_array(state) or len(state) != 2:
                return None
            size, mtime = state
            if (
                isinstance(size, bool)
                or isinstance(mtime, bool)
                or not isinstance(size, int)
                or not isinstance(mtime, int)
                or size < 0
            ):
                return None
            files.append((rel, size, mtime))
        return cls(
            stem,
            home,
            removed_at,
            removed_by,
            tuple(sorted(files)),
            whole,
            copy,
            identity,
            tuple(sorted(pairs)),
        )


@dataclasses.dataclass(frozen=True)
class RemovedCopy:
    """The incarnation of a copy an ``rm --evidence`` removed, and the pins it owned then.

    ``identity`` is its note's (:func:`copy_identity`; :func:`pins_identity` for a name
    holding pins alone), ``pins`` the ``(leaf, commit)`` pairs under the name it owned at
    the removal (:func:`removed_copy`).
    """

    name: str
    identity: str
    pins: tuple[tuple[str, str], ...] = ()

    def left_alone(self, name: str, held: Mapping[str, str]) -> bool:
        """Return whether ``name`` holding the pins ``held`` (leaf to commit) is this copy's rest.

        Only with an identity, under its own name, and while every pin ``held`` is one it
        owned: a later copy's save under the name is another commit, so that name still uses
        the stem.
        """
        owned = set(self.pins)
        return (
            bool(self.identity)
            and name == self.name
            and bool(held)
            and all((leaf, sha) in owned for leaf, sha in held.items())
        )


def removed_copy(repo: Path, copy: Copy) -> RemovedCopy:
    """Return what an evidence record says of ``copy``, read before its ``rm``: identity, own pins.

    A copy's own pins are those its note attributes to it (:func:`pin_belongs`); a name
    holding pins alone owns every pin under it.
    """
    held = pins(repo).get(copy.name, {})
    if copy.form == "pins":
        return RemovedCopy(copy.name, pins_identity(held), tuple(sorted(held.items())))
    note = attributed_note(repo, copy.note)
    owned = {leaf: sha for leaf, sha in held.items() if pin_belongs(note, leaf, sha)}
    return RemovedCopy(copy.name, copy_identity(copy.note), tuple(sorted(owned.items())))


def evidence_tombstones(repo: Path) -> list[EvidenceTombstone]:
    """Return every readable evidence tombstone (a broken or misnamed file is skipped)."""
    folder = work_dir(repo) / EVIDENCE_GRAVES
    if not folder.is_dir():
        return []
    found = (read_evidence_tombstone(repo, path.name) for path in sorted(folder.glob("*.json")))
    return [grave for grave in found if grave is not None]


def read_evidence_tombstone(repo: Path, file_name: str) -> EvidenceTombstone | None:
    """Return the evidence tombstone published as ``file_name`` (as :func:`read_tombstone`)."""
    grave = EvidenceTombstone.parse(_record_text(work_dir(repo) / EVIDENCE_GRAVES, file_name))
    return grave if grave is not None and grave.file_name == file_name else None


def write_evidence_tombstone(repo: Path, grave: EvidenceTombstone) -> bool:
    """Publish ``grave`` create-only (as :func:`write_tombstone`); return whether it wrote it."""
    return _publish_once(
        _container(repo, EVIDENCE_GRAVES, create=True),
        grave.file_name,
        grave.as_json(),
    )


def evidence_files(folder: Path) -> dict[str, tuple[int, int]]:
    """Return ``{relative path: [size, mtime seconds]}`` for every synced file under ``folder``.

    :data:`UNSYNCED` folders and ``*.pyc`` files are left out; a file that cannot be
    ``lstat``-ed is too.
    """
    files: dict[str, tuple[int, int]] = {}
    for directory, dirnames, filenames in os.walk(folder):
        dirnames[:] = [name for name in dirnames if name not in UNSYNCED]
        for name in filenames:
            if name.endswith(".pyc"):
                continue
            path = Path(directory) / name
            with contextlib.suppress(OSError):
                files[path.relative_to(folder).as_posix()] = file_state(path.lstat())
    return files


def evidence_manifest(path: Path) -> dict[str, dict[str, tuple[int, int]]]:
    """Return a fleet evidence manifest (``{stem: {rel: (size, mtime)}}``), ``{}`` if unreadable."""
    try:
        document = _loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    manifest: dict[str, dict[str, tuple[int, int]]] = {}
    for stem, files in (document if fleet.is_json_object(document) else {}).items():
        entries: dict[str, tuple[int, int]] = {}
        for rel, state in (files if fleet.is_json_object(files) else {}).items():
            if fleet.is_json_array(state) and len(state) == 2:
                size, mtime = state
                if isinstance(size, int) and isinstance(mtime, int):
                    entries[rel] = (size, mtime)
        manifest[stem] = entries
    return manifest


def inside(root: Path, relative: str) -> Path:
    """Return ``root / relative``, refusing a path that could name a file outside ``root``.

    Each folder on the way is ``lstat``-ed: a symlinked (or non-folder) one, an absolute path
    and a ``..`` part are refused; a folder that is not there leaves a path to no file.

    Raises:
        WorkError: the path is absolute, climbs with ``..`` or passes a symlinked folder.

    """
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).is_absolute() or ".." in parts:
        msg = f"{relative!r} is no path inside {root.name}"
        raise WorkError(msg)
    folder = root
    for part in parts[:-1]:
        folder /= part
        try:
            mode = folder.lstat().st_mode
        except (FileNotFoundError, NotADirectoryError):
            break
        if not stat.S_ISDIR(mode):
            msg = f"{relative!r} passes {folder.relative_to(root).as_posix()}, no real folder"
            raise WorkError(msg)
    return root.joinpath(*parts)


def evidence_users(repo: Path, stem: str, *, removed: RemovedCopy | None = None) -> list[str]:
    """Return the names whose stem is ``stem``: copies, replicas and names holding pins alone.

    ``removed``, the copy an ``rm --evidence`` removed, is no user while its name holds
    only pins it owned at the removal (:meth:`RemovedCopy.left_alone`): its own saves never
    keep the evidence its ``rm`` deletes, a later copy's under the name do. A ``-verify`` or
    ``-rN`` sibling, and any other name holding pins alone, is one.
    """
    found = discover(repo)
    held = pins(repo) if removed is not None else {}
    return sorted(
        name
        for name, copy in found.items()
        if stem_of(name) == stem
        and not (
            removed is not None
            and copy.form == "pins"
            and removed.left_alone(name, held.get(name, {}))
        )
    )


@contextlib.contextmanager
def fleet_lock(repo: Path, wait: float | None = None) -> Generator[None, None, None]:
    """Hold ``.work/fleet.lock`` for the block, waiting up to ``wait`` seconds for it.

    An evidence deletion takes it so no fleet sync's transfer races its record and its move.

    Raises:
        WorkError: a fleet sync (or a peer's hold) kept it the whole wait.

    """
    _ = ensure_sentinel(repo)
    lock = work_dir(repo) / FLEET_LOCK
    check_layout(repo)
    deadline = time.monotonic() + (EVIDENCE_LOCK_WAIT_SECONDS if wait is None else wait)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        while True:
            try:
                locked = _locks.try_lock(descriptor)
            except OSError as error:
                msg = f"cannot lock {lock}: {error}"
                raise WorkError(msg) from error
            if locked:
                break
            if time.monotonic() >= deadline:
                msg = f"a fleet sync holds {lock}; nothing deleted, run it again once it ends"
                raise WorkError(msg)
            time.sleep(0.2)
        yield
    finally:
        os.close(descriptor)


class StemBusyError(WorkError):
    """Another command holds the stem's lock (:func:`stem_lock`) for the whole wait."""


@contextlib.contextmanager
def stem_lock(repo: Path, stem: str, wait: float) -> Generator[None, None, None]:
    """Hold ``.work/stem-locks/<stem>.lock`` for the block, waiting up to ``wait`` seconds.

    The stem's lifecycle lock: who uses a stem changes (``new``, ``adopt``) or its evidence
    is deleted (``rm --evidence``, ``evidence-rm``, a fleet sync's ``evidence-apply``) only
    under it, so an owner check and the moves it allows see one owner set. A kernel lock
    (``scripts/_locks.py::try_lock``), released however its holder ends, never taken over.
    The file is never deleted: one unlinked while a waiter has it open would give the next
    opener another file, and two holders.

    Raises:
        StemBusyError: another holder kept it the whole wait (``0``: tried once).
        WorkError: ``stem`` is no plain folder name, or the lock cannot be opened or taken.

    """
    if not valid_stem(stem):
        msg = f"{stem!r} is no evidence folder name"
        raise WorkError(msg)
    lock = _container(repo, STEM_LOCKS, create=True) / f"{stem}.lock"
    deadline = time.monotonic() + wait
    try:
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
    except OSError as error:
        msg = f"cannot open {lock}: {error}"
        raise WorkError(msg) from error
    try:
        while True:
            try:
                locked = _locks.try_lock(descriptor)
            except OSError as error:
                msg = f"cannot lock {lock}: {error}"
                raise WorkError(msg) from error
            if locked:
                break
            if time.monotonic() >= deadline:
                msg = (
                    f"evidence {stem}: another command (a fleet sync deleting its evidence, a "
                    f"`work.py new`, `adopt` or `rm --evidence`) holds {lock}; nothing changed, "
                    "run it again once that ends"
                )
                raise StemBusyError(msg)
            time.sleep(0.1)
        yield
    finally:
        os.close(descriptor)


@contextlib.contextmanager
def evidence_locks(repo: Path, stem: str) -> Generator[None, None, None]:
    """Hold ``.work/fleet.lock`` (:func:`fleet_lock`), then the stem's lock, for an evidence deletion.

    Always in that order, and a fleet sync's apply (under the sync's hold of
    ``fleet.lock``) never waits for a stem's lock, so no two holders wait on each other.

    Raises:
        WorkError: either lock stayed held for its whole wait (:class:`StemBusyError` for the stem's).

    """
    with fleet_lock(repo), stem_lock(repo, stem, STEM_LOCK_WAIT_SECONDS):
        yield


def evidence_trash_entry(repo: Path, stem: str, *, make: bool) -> Path:
    """Return a fresh ``.work/trash/evidence-<stem>-<seconds>-kept`` entry (made when ``make``).

    ``gc`` keeps a ``-kept`` entry :data:`TRASH_RETENTION_SECONDS` from its seconds. A name
    taken already moves on a second, so two deletions never share an entry; the callers hold
    ``.work/fleet.lock`` (``work.py``) or the fleet sync's hold (its agent), so none races.
    """
    trash = _container(repo, TRASH, create=True)
    stamp = int(time.time())
    while True:
        entry = trash / f"evidence-{stem}-{stamp}-{KEPT_TRASH}"
        if make:
            try:
                entry.mkdir()
            except FileExistsError:
                stamp += 1
                continue
            return entry
        if not _present(trash, entry):
            return entry
        stamp += 1


def _prune_empty(root: Path, folder: Path) -> None:
    """Remove ``folder`` and each emptied folder above it, up to (never) ``root``."""
    while folder != root and _is_within(folder, root):
        try:
            folder.rmdir()
        except OSError:
            return
        folder = folder.parent


def move_evidence_file(
    folder: Path,
    rel: str,
    state: tuple[int, int],
    entry: Callable[[], Path],
) -> str:
    """Move ``folder/rel`` into the trash entry ``entry()`` when it holds exactly ``state``.

    Returns ``"moved"``, ``"gone"`` (no file there) or ``"changed"`` (another state, a folder,
    or written while it moved and put back). The file is ``lstat``-ed before the rename and
    again after it (the same inode, the same state); emptied folders are pruned, ``folder``
    itself never.

    Raises:
        WorkError: ``rel`` leaves ``folder`` (:func:`inside`), or the file changed while it
            moved and its place is taken again (it stays in the entry).
        OSError: the rename failed (the file stays where it was).

    """
    path = inside(folder, rel)
    try:
        before = path.lstat()
    except (FileNotFoundError, NotADirectoryError):
        return "gone"
    if stat.S_ISDIR(before.st_mode) or file_state(before) != state:
        return "changed"
    target = entry() / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    _ = path.rename(target)
    after = target.lstat()
    same = (after.st_ino, after.st_dev) == (before.st_ino, before.st_dev)
    if not same or file_state(after) != state:
        if _present(path.parent, path):
            msg = f"{rel} changed while it moved to the trash; it stays in {target}"
            raise WorkError(msg)
        _ = target.rename(path)
        return "changed"
    _prune_empty(folder, path.parent)
    return "moved"


def discard_evidence(
    repo: Path,
    stem: str,
    *,
    removed: RemovedCopy | None = None,
) -> tuple[EvidenceTombstone, Path]:
    """Record every file of ``.work/evidence/<stem>`` in a tombstone, then move the folder to the trash.

    The record is written first: a crash after it leaves the files for the next full fleet
    sync to move (it applies this machine's own records too); before it nothing happened. The
    folder goes into a fresh ``evidence-<stem>-<seconds>-kept`` entry in one rename. The record
    names ``removed``, the copy an ``rm --evidence`` removed. The caller holds
    ``.work/fleet.lock`` and the stem's lock (:func:`evidence_locks`).

    Raises:
        WorkError: the folder could not be moved (the record stands; the files stay).

    """
    folder = work_dir(repo) / EVIDENCE / stem
    here = machine_id()
    listed = evidence_files(folder)
    files = tuple(sorted((rel, size, mtime) for rel, (size, mtime) in listed.items()))
    owner = removed or RemovedCopy("", "")
    grave = EvidenceTombstone(
        stem,
        here,
        time.time(),
        here,
        files,
        whole=True,
        copy=owner.name,
        identity=owner.identity,
        pins=owner.pins,
    )
    _ = write_evidence_tombstone(repo, grave)
    entry = evidence_trash_entry(repo, stem, make=False)
    try:
        _ = folder.rename(entry)
    except OSError as error:
        msg = (
            f"evidence {stem}: recorded in {EVIDENCE_GRAVES}/{grave.file_name} but not moved to "
            f"the trash ({error.strerror or error}); the next full fleet sync moves its files"
        )
        raise WorkError(msg) from None
    return grave, entry


def _gc_evidence_tombstones(repo: Path, *, dry_run: bool) -> int:
    """Delete evidence tombstones older than their retention; return 1 on a failure."""
    status = 0
    now = time.time()
    for grave in evidence_tombstones(repo):
        if not past_retention(grave.removed_at, EVIDENCE_TOMBSTONE_RETENTION_SECONDS, now):
            continue
        if dry_run:
            print(f"would delete evidence tombstone {grave.file_name}")
            continue
        try:
            (work_dir(repo) / EVIDENCE_GRAVES / grave.file_name).unlink()
        except OSError as error:
            print(f"cannot delete evidence tombstone {grave.file_name}: {error}", file=sys.stderr)
            status = 1
        else:
            print(f"deleted evidence tombstone {grave.file_name}")
    return status


# --------------------------------------------------------------------------------------------
# Git
# --------------------------------------------------------------------------------------------


def refuse_locating_env(environ: Mapping[str, str] | None = None) -> None:
    """Refuse while a variable that relocates git's repository or index is set.

    Raises:
        WorkError: one of :data:`LOCATING_NAMES` is set.

    """
    source = os.environ if environ is None else environ
    present = [name for name in LOCATING_NAMES if name in source]
    if present:
        msg = (
            f"{', '.join(present)} set: unset it first (a command run against a private "
            "index or another repository would read or write the wrong one)"
        )
        raise WorkError(msg)


def _git_bytes(
    root: Path,
    *args: str,
    env: Mapping[str, str] | None = None,
    stdin: bytes | None = None,
) -> bytes:
    """Run ``git -C root args`` in the repository-only environment; return stdout bytes.

    Raises:
        WorkError: git exits non-zero; the message carries its stderr.

    """
    if shutil.which("git") is None:
        msg = "git is not on PATH"
        raise WorkError(msg)
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "--no-pager",
            *args,
        ],
        capture_output=True,
        input=stdin,
        env=_git_runner.repository_env(**dict(env or {})),
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        msg = f"git {' '.join(args)} failed ({completed.returncode}): {detail}"
        raise WorkError(msg)
    return completed.stdout


def _git(root: Path, *args: str, env: Mapping[str, str] | None = None) -> str:
    """Run ``git -C root args`` (see :func:`_git_bytes`); return stdout as text."""
    return _git_bytes(root, *args, env=env).decode("utf-8", "surrogateescape")


def _git_ok(root: Path, *args: str) -> bool:
    """Return whether ``git -C root args`` exits 0, output discarded."""
    completed = _git_runner.run_git(root, *args)
    return completed.returncode == 0


def _config_values(root: Path, *scope: str) -> dict[str, str]:
    """Return the ``dsf-work.*`` note at ``scope`` (``--local``, ``--worktree``, ``-f F``).

    Only a clean exit 1 (no ``dsf-work`` key) is an empty note. git also exits 1 for a
    config file it cannot read, but warns on stderr; that, and every other failure, is no
    note read, never an empty one.

    Raises:
        WorkError: git could not read the config at ``scope``.

    """
    completed = _git_runner.run_git(
        root,
        "config",
        *scope,
        "-z",
        "--get-regexp",
        rf"^{re.escape(NOTE_SECTION)}\.",
    )
    if completed.returncode == 1 and not completed.stderr.strip():
        return {}
    if completed.returncode != 0:
        msg = (
            f"cannot read the dsf-work note of {root} ({' '.join(scope)}): "
            f"{completed.stderr.strip() or f'git config exited {completed.returncode}'}"
        )
        raise WorkError(msg)
    note: dict[str, str] = {}
    for record in completed.stdout.split("\0"):
        if not record:
            continue
        key, _, value = record.partition("\n")
        note[key.removeprefix(f"{NOTE_SECTION}.")] = value
    return note


def _resolve_commit(root: Path, rev: str) -> str:
    """Return the full commit id ``rev`` names in ``root``, ``""`` when it names none."""
    completed = _git_runner.run_git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
    return completed.stdout.strip() if completed.returncode == 0 else ""


def _common_dir(repo: Path) -> Path:
    """Return the shared checkout's common git directory, absolute (``_git.git_dirs``).

    Raises:
        WorkError: git reads no repository at ``repo``.

    """
    dirs = _git_runner.git_dirs(repo)
    if dirs is None:
        msg = f"git reads no repository at {repo}"
        raise WorkError(msg)
    return dirs[1]


def _git_path(root: Path, name: str) -> Path:
    """Return ``root``'s ``$GIT_DIR/<name>``, absolute."""
    return Path(_git(root, "rev-parse", "--path-format=absolute", "--git-path", name).strip())


def _is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """Return whether ``ancestor`` is ``descendant`` or reachable from it in ``repo``."""
    return _git_ok(repo, "merge-base", "--is-ancestor", ancestor, descendant)


def _token() -> str:
    """Return a name part no other process uses at this moment."""
    return f"{os.getpid()}-{time.time_ns()}"


# --------------------------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------------------------


def work_dir(repo: Path) -> Path:
    """Return ``<repo>/.work``."""
    return repo / WORK_DIR


def check_layout(repo: Path) -> None:
    """Refuse a ``.work`` (or an entry of it) that is a symlink, the wrong kind, or not under the repo.

    Raises:
        WorkError: the layout is unsafe to read or write.

    """
    work = work_dir(repo)
    entries = [(work, True)]
    entries += [(work / name, True) for name in DIR_CONTAINERS]
    entries += [(work / name, False) for name in FILE_ENTRIES]
    for path, is_folder in entries:
        mode = _mode(repo, path)
        if mode is not None and stat.S_ISLNK(mode):
            msg = f"{path} is a symlink; .work and its entries must be real"
            raise WorkError(msg)
        if mode is not None and stat.S_ISDIR(mode) != is_folder:
            msg = f"{path} is not a {'directory' if is_folder else 'regular file'}"
            raise WorkError(msg)
    if _present(repo, work) and work.resolve() != repo.resolve() / WORK_DIR:
        msg = f"{work} resolves to {work.resolve()}, outside {repo.resolve()}"
        raise WorkError(msg)


def _container(repo: Path, name: str, *, create: bool = False) -> Path:
    """Return ``.work/<name>``, made when ``create``, after checking the layout again."""
    path = work_dir(repo) / name
    if create:
        path.mkdir(parents=True, exist_ok=True)
    check_layout(repo)
    return path


def copy_hazard(repo: Path, path: Path, container: str) -> str | None:
    """Return why the copy folder ``path`` under ``.work/<container>`` is unsafe, else ``None``."""
    real = (repo.resolve() / WORK_DIR / container).resolve()
    try:
        mode = _mode(repo, path)
    except WorkError as error:
        return str(error)
    if mode is not None and stat.S_ISLNK(mode):
        return f"{path} is a symlink"
    if mode is not None and path.resolve().parent != real:
        return f"{path} resolves outside {real}"
    return None


def ensure_sentinel(repo: Path) -> bool:
    """Write the ``.work/.git`` sentinel when it is missing or wrong; return whether it wrote.

    ``.work`` is also kept ``0700``: no other (non-root) user can then enter a copy, which
    is what lets the process census skip processes it may not read.
    """
    check_layout(repo)
    work = work_dir(repo)
    work.mkdir(mode=0o700, parents=True, exist_ok=True)
    check_layout(repo)
    if work.stat().st_uid == os.getuid() and work.stat().st_mode & 0o077:
        work.chmod(0o700)
    sentinel = work / ".git"
    mode = _mode(repo, sentinel)
    if mode is not None and not stat.S_ISREG(mode):
        msg = f"{sentinel} is not a plain file; the sentinel must be one (remove it by hand)"
        raise WorkError(msg)
    if mode is not None and sentinel.read_text(encoding="utf-8") == SENTINEL_TEXT:
        return False
    _ = sentinel.write_text(SENTINEL_TEXT, encoding="utf-8")
    return True


# --------------------------------------------------------------------------------------------
# Name claims
# --------------------------------------------------------------------------------------------


def claim_name(repo: Path, name: str) -> Path:
    """Claim ``name``: a folder holding its owner, renamed into ``.work/names/<name>`` in one step.

    The owner file is written before the rename publishes the claim, so no claim is ever
    seen without its owner, and of two commands racing for one name only one rename wins.

    The owner is ``<machine> <pid>``; a machine with no name (``$DSF_MACHINE_ID`` such as
    ``.``) is refused, since an owner without one could never be known dead.

    Raises:
        WorkError: this machine has no name, or another command holds the claim.

    """
    _ = parse_name(name)
    owner = machine_id()
    if not owner:
        msg = (
            f"this machine has no name (${fleet.MACHINE_ENV}, else its hostname, is empty "
            f"before its first dot): set ${fleet.MACHINE_ENV} to its row's name"
        )
        raise WorkError(msg)
    claims = _container(repo, NAMES, create=True)
    claim = claims / name
    staged = claims / f".{name}.{_token()}"
    staged.mkdir()
    _ = (staged / "owner").write_text(
        f"{owner} {os.getpid()}\n",
        encoding="utf-8",
    )
    try:
        if claim.exists() or claim.is_symlink():
            raise FileExistsError(claim)
        _ = staged.rename(claim)
    except OSError:
        delete_tree(staged)
        msg = f"{name!r} is claimed (in use, or a `new` is making it now)"
        raise WorkError(msg) from None
    return claim


def release_name(repo: Path, name: str) -> None:
    """Drop the claim on ``name`` when there is one.

    Raises:
        WorkError: ``name`` breaks the name grammar (it would name a path outside the
            claims), or the claims cannot be looked into.

    """
    _ = parse_name(name)
    claim = work_dir(repo) / NAMES / name
    if _is_kind(repo, claim, stat.S_ISDIR):
        delete_tree(claim)


def _claim_is_stale(claim: Path) -> bool:
    """Return whether the command that took ``claim`` is known dead.

    Dead means: its owner is this machine (:func:`canonical`) and its pid is gone, or it never
    wrote an owner and is older than :data:`CLAIM_GRACE_SECONDS`. A claim from another machine
    is never known dead.
    """
    try:
        host, pid = (claim / "owner").read_text(encoding="utf-8").split()
    except FileNotFoundError:
        with contextlib.suppress(OSError):
            return time.time() - claim.stat().st_mtime > CLAIM_GRACE_SECONDS
        return False
    except (OSError, ValueError):
        return False
    here = machine_id()
    return bool(here) and canonical(host) == here and pid.isdigit() and not _pid_alive(int(pid))


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# --------------------------------------------------------------------------------------------
# Pins
# --------------------------------------------------------------------------------------------


def pin_store(repo: Path) -> Path | None:
    """Return ``.work/pins.git``, ``None`` while it does not exist.

    Raises:
        WorkError: the folder exists but is no repository (its pins cannot be read); ``repair``
            re-initializes it, which keeps every ref and object still there.

    """
    store = work_dir(repo) / PIN_STORE
    check_layout(repo)
    if not _present(repo, store):
        return None
    if not _is_kind(repo, store / "HEAD", stat.S_ISREG):
        msg = f"{store} is damaged (no HEAD); run `repair` before trusting any pin"
        raise WorkError(msg)
    return store


def make_pin_store(repo: Path) -> Path:
    """Return ``.work/pins.git``, initializing the bare repository first when it is missing."""
    store = work_dir(repo) / PIN_STORE
    check_layout(repo)
    if _is_kind(repo, store / "HEAD", stat.S_ISREG):
        return store
    _ = ensure_sentinel(repo)
    store.mkdir(exist_ok=True)
    check_layout(repo)
    _ = _git(store, "init", "--quiet", "--bare")
    return store


def pins(repo: Path) -> dict[str, dict[str, str]]:
    """Return ``{name: {leaf: commit}}`` for every ``refs/work/<name>/<leaf>`` pin."""
    store = pin_store(repo)
    if store is None:
        return {}
    listing = _git(store, "for-each-ref", "--format=%(objectname) %(refname)", PIN_PREFIX)
    found: dict[str, dict[str, str]] = {}
    for line in listing.splitlines():
        sha, _, ref = line.partition(" ")
        name, _, leaf = ref.removeprefix(PIN_PREFIX).partition("/")
        if leaf:
            found.setdefault(name, {})[leaf] = sha
    return found


def save_numbers(leaves: Mapping[str, str]) -> list[int]:
    """Return the ``N`` of every ``save-N`` leaf, ascending."""
    return sorted(
        int(match.group(1)) for leaf in leaves if (match := SAVE_PIN.fullmatch(leaf)) is not None
    )


def _pin_ref(name: str, leaf: str) -> str:
    return f"{PIN_PREFIX}{name}/{leaf}"


def publish_pin(
    repo: Path,
    source: Path,
    commit: str,
    name: str,
    leaf: str,
    *,
    replacing: str = "",
) -> bool:
    """Point the pin ``<name>/<leaf>`` at ``commit``, fetched from ``source``.

    The pin is set only while it holds ``replacing`` (``""``: only while it does not
    exist), so a racing writer is never overwritten; returns whether it was set.
    """
    store = make_pin_store(repo)
    incoming = f"{INCOMING_PREFIX}{_token()}"
    _ = _git(
        store,
        *FETCH_BY_ID,
        "fetch",
        "--quiet",
        "--no-tags",
        "--no-write-fetch-head",
        str(source),
        f"{commit}:{incoming}",
    )
    try:
        return _git_ok(store, "update-ref", _pin_ref(name, leaf), commit, replacing)
    finally:
        _ = _git_runner.run_git(store, "update-ref", "-d", incoming)


def publish_next_save(
    repo: Path,
    source: Path,
    commit: str,
    name: str,
) -> str:
    """Pin ``commit`` as the first free ``save-N`` of ``name``; return that ref.

    Raises:
        WorkError: no number could be reserved.

    """
    for _attempt in range(MAX_SAVE_ATTEMPTS):
        numbers = save_numbers(pins(repo).get(name, {}))
        leaf = f"save-{(numbers[-1] if numbers else 0) + 1}"
        if publish_pin(repo, source, commit, name, leaf):
            return _pin_ref(name, leaf)
    msg = f"could not reserve a save number for {name!r}"
    raise WorkError(msg)


def drop_pin(
    repo: Path,
    name: str,
    leaf: str,
    old: str = "",
) -> None:
    """Delete one pin (only while it is at ``old``, when given)."""
    store = pin_store(repo)
    if store is not None:
        _ = _git(store, "update-ref", "-d", _pin_ref(name, leaf), *([old] if old else []))


def fetch_pinned(repo: Path, target: Path, commit: str) -> None:
    """Bring ``commit`` (and its history) from ``pins.git`` into the repository at ``target``."""
    store = pin_store(repo)
    if store is None:
        msg = "there is no pins.git"
        raise WorkError(msg)
    _ = _git(
        target,
        *FETCH_BY_ID,
        "fetch",
        "--quiet",
        "--no-tags",
        "--no-write-fetch-head",
        str(store),
        commit,
    )


def landing_on_main(repo: Path, landed: str) -> bool:
    """Return whether the shared ``HEAD`` holds every path the pinned landing changed, entry for entry.

    An entry is mode, type and object id, so a mode-only landing main undid reads as not held.
    """
    store = pin_store(repo)
    if store is None:
        return False
    base = _resolve_commit(store, f"{landed}^")
    if not base:
        return False
    names = _git(store, "diff-tree", "-r", "-z", "--no-renames", "--name-only", base, landed)
    paths = [entry for entry in names.split("\0") if entry]
    return _tree_entries(store, landed, paths) == _tree_entries(repo, "HEAD", paths)


def _tree_entries(root: Path, rev: str, paths: Sequence[str]) -> dict[str, str]:
    """Return ``{path: "mode type oid"}`` for each of ``paths`` present in ``rev``."""
    if not paths:
        return {}
    listing = _git(root, "ls-tree", "-z", "--full-tree", rev, "--", *paths)
    entries: dict[str, str] = {}
    for record in (entry for entry in listing.split("\0") if entry):
        header, _, path = record.partition("\t")
        entries[path] = header
    return entries


# --------------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class WorktreeEntry:
    """One ``git worktree list --porcelain`` record."""

    path: Path
    head: str | None
    branch: str | None
    locked: str | None
    prunable: bool


def worktree_entries(repo: Path) -> list[WorktreeEntry]:
    """Return every linked worktree of ``repo`` (the main worktree left out)."""
    text = _git(repo, "worktree", "list", "--porcelain", "-z")
    entries: list[WorktreeEntry] = []
    for block in text.split("\0\0"):
        fields = [field for field in block.split("\0") if field]
        if not fields or not fields[0].startswith("worktree "):
            continue
        values: dict[str, str] = {}
        for field in fields:
            key, _, value = field.partition(" ")
            values[key] = value
        entries.append(
            WorktreeEntry(
                path=Path(values["worktree"]),
                head=values.get("HEAD"),
                branch=values.get("branch"),
                locked=values.get("locked"),
                prunable="prunable" in values,
            ),
        )
    main = repo.resolve()
    return [entry for entry in entries if entry.path.resolve() != main]


def _abs(path: Path) -> Path:
    """Return ``path`` made absolute without following symlinks (a gone folder cannot resolve)."""
    return Path(os.path.abspath(path))  # noqa: PTH100 - resolve() would follow symlinks


def _admin_dirs(repo: Path) -> dict[Path, Path]:
    """Map each linked worktree's path to its ``<common>/worktrees/<id>`` metadata folder."""
    common = _common_dir(repo)
    admin_root = common / "worktrees"
    found: dict[Path, Path] = {}
    if not _is_kind(common, admin_root, stat.S_ISDIR):
        return found
    for admin in sorted(admin_root.iterdir()):
        gitdir = admin / "gitdir"
        if not _is_kind(common, gitdir, stat.S_ISREG):
            continue
        dot_git = Path(gitdir.read_text(encoding="utf-8").strip())
        if not dot_git.is_absolute():
            dot_git = (admin / dot_git).resolve()
        found[_abs(dot_git.parent)] = admin
    return found


@dataclasses.dataclass(frozen=True)
class Copy:
    """One registered copy, live or not."""

    name: str
    form: str
    path: Path | None
    note: Mapping[str, str]
    admin: Path | None = None
    locked: str | None = None
    hazard: str | None = None

    @property
    def present(self) -> bool:
        """Return whether the copy's folder exists (links followed).

        Raises:
            WorkError: the folder's parent cannot be looked into: it is never read as gone.

        """
        if self.path is None:
            return False
        mode = _mode(self.path.parent, self.path, follow=True)
        return mode is not None and stat.S_ISDIR(mode)

    @property
    def adopted(self) -> bool:
        """Return whether another tool made the copy and ``adopt`` registered it."""
        return self.note.get("adopted") == "true"

    @property
    def healthy(self) -> bool:
        """Return whether git reads the folder as its own checkout (its ``.git`` is intact)."""
        if self.hazard is not None or not self.present or self.path is None:
            return False
        return _is_own_checkout(self.path)


def _is_own_checkout(path: Path) -> bool:
    """Return whether git, run in ``path``, finds ``path`` itself as the toplevel."""
    completed = _git_runner.run_git(path, "rev-parse", "--show-toplevel")
    return completed.returncode == 0 and _git_runner.same_directory(completed.stdout.strip(), path)


def _looks_like(path: Path, kind: Callable[[int], bool]) -> bool:
    """Return whether ``path`` (links followed) is there and of ``kind``.

    A path that cannot be looked up (its folder is unreadable) answers ``False`` on every
    Python, as ``Path.is_dir()`` does only from 3.14: the copy then reads as broken.
    """
    try:
        return kind(path.stat().st_mode)
    except OSError:
        return False


def _clone_note(path: Path) -> dict[str, str]:
    """Return a clone's note, ``{}`` when its ``.git`` is missing or cannot be looked up."""
    if not _looks_like(path / ".git", stat.S_ISDIR):
        return {}
    return _config_values(path, "--local")


def _worktree_note(path: Path | None, admin: Path | None) -> dict[str, str]:
    """Return a worktree's note, read from its folder or, once that is gone, its metadata.

    A folder git cannot read (its ``.git`` broken) falls back to the metadata's
    ``config.worktree``, the file the note lives in; that file is read strictly.

    Raises:
        WorkError: the metadata folder cannot be looked into, or its ``config.worktree``
            cannot be read.

    """
    if path is not None and _looks_like(path / ".git", stat.S_ISREG):
        with contextlib.suppress(WorkError):
            note = _config_values(path, "--worktree")
            if note:
                return note
    if admin is not None and _is_kind(admin, admin / "config.worktree", stat.S_ISREG):
        return _config_values(admin, "-f", str(admin / "config.worktree"))
    return {}


def _copy_folders(folder: Path) -> list[Path]:
    """Return the entries of the copy container ``folder``, ``[]`` when it is not there.

    Raises:
        WorkError: the container is there but cannot be listed.

    """
    if not _is_kind(folder.parent, folder, stat.S_ISDIR):
        return []
    try:
        return sorted(folder.iterdir())
    except OSError as error:
        msg = f"cannot read {folder}: {error.strerror or error}"
        raise WorkError(msg) from error


def _worktree_hazard(path: Path) -> str | None:
    """Return why the registered worktree at ``path`` is unsafe, else ``None``.

    Its folder must be one that can be looked up: one that cannot is never read as gone.
    """
    try:
        _ = _mode(path.parent, path)
    except WorkError as error:
        return str(error)
    return None


def _name_problems(
    copy: Copy,
    folder: str | None,
    claims: Mapping[str, Sequence[Copy]],
) -> list[str]:
    """Return why the names ``copy`` claims make it unsafe (empty = they do not).

    ``folder`` is the copy's folder name when it sits in a ``.work`` container. The note
    must name a valid copy name, the folder's own when there is one, and no other record
    may claim any name this one claims.
    """
    noted = copy.note.get("name")
    problems: list[str] = []
    if noted is not None and not _valid(noted):
        problems.append(f"its note names {noted!r}, not a valid copy name")
    elif noted is not None and folder is not None and noted != folder:
        problems.append(f"its note names {noted!r} but its folder is {folder!r}")
    for name in _claimed(copy, folder):
        others = [str(other.path) for other in claims[name] if other is not copy]
        if others:
            problems.append(f"{name!r} is also claimed by {', '.join(others)}")
    return problems


def _claimed(copy: Copy, folder: str | None) -> list[str]:
    """Return every name ``copy`` claims: its folder name in a container, then its note's."""
    return [name for name in dict.fromkeys((folder, copy.note.get("name"))) if name is not None]


def _by_name(found: Sequence[tuple[Copy, str | None]]) -> dict[str, Copy]:
    """Key each found record (a copy and its folder name in a container) by every name it claims.

    A record whose names conflict (:func:`_name_problems`) is marked unsafe and stays
    under each of its names, so neither a folder name nor a note name can address it as a
    safe copy, nor leave its pins and claim to a ``pins`` record. A record whose every
    name an earlier record took is listed under its name and path.
    """
    claims: dict[str, list[Copy]] = {}
    for copy, folder in found:
        for name in _claimed(copy, folder):
            claims.setdefault(name, []).append(copy)
    records: list[tuple[Copy, list[str]]] = []
    for copy, folder in found:
        record = copy
        problems = _name_problems(copy, folder, claims)
        if problems:
            hazard = "; ".join(problems) + "; fix the note or the folder by hand"
            record = dataclasses.replace(
                copy,
                hazard=hazard if copy.hazard is None else f"{copy.hazard}; {hazard}",
            )
        records.append((record, _claimed(copy, folder)))
    copies: dict[str, Copy] = {}
    keyless: list[Copy] = []
    for record, names in records:
        free = [name for name in names if name not in copies]
        for name in free:
            copies[name] = record
        if not free:
            keyless.append(record)
    for record in keyless:
        copies[f"{record.name} ({record.path})"] = record
    return copies


def discover(repo: Path) -> dict[str, Copy]:
    """Derive the registry: ``.work`` folders, linked worktrees and the pins.

    Each folder is one record. A copy folder that is unsafe (:func:`copy_hazard`, which
    includes one that cannot be looked up) is listed with its hazard and never read; one
    that cannot be looked into lists as broken. A worktree whose note names a folder is
    that folder's record (git's lock on it included), never a second one under the folder
    name. A record whose note names an invalid copy name, a name other than its folder's,
    or a name another record claims is unsafe, listed under every name it claims: such a
    name is never used as a path, and ``rm``, ``gc`` and ``repair`` never touch it.

    Raises:
        WorkError: ``.work/clones`` or ``.work/worktrees`` cannot be listed, or a
            worktree's note cannot be read.

    """
    check_layout(repo)
    found: list[tuple[Copy, str | None]] = []
    clones = work_dir(repo) / CLONES
    for path in _copy_folders(clones):
        hazard = copy_hazard(repo, path, CLONES)
        if hazard is not None:
            found.append((Copy(path.name, "clone", path, {}, hazard=hazard), path.name))
        elif _is_kind(clones, path, stat.S_ISDIR):
            note = _clone_note(path)
            found.append((Copy(note.get("name", path.name), "clone", path, note), path.name))
    worktrees = work_dir(repo) / WORKTREES
    worktrees_abs = _abs(worktrees)
    worktree_folders = _copy_folders(worktrees)
    unsafe_worktrees: dict[str, str] = {}
    for path in worktree_folders:
        hazard = copy_hazard(repo, path, WORKTREES)
        if hazard is not None:
            unsafe_worktrees[path.name] = hazard
    admins = _admin_dirs(repo)
    registered: set[str] = set()
    for entry in worktree_entries(repo):
        path = _abs(entry.path)
        inside = path.parent == worktrees_abs
        admin = admins.get(path)
        if inside:
            registered.add(path.name)
        if inside and path.name in unsafe_worktrees:
            note: dict[str, str] = {}
            with contextlib.suppress(WorkError):
                note = _worktree_note(None, admin)
            hazard = unsafe_worktrees[path.name]
            record = Copy(path.name, "worktree", path, note, admin, entry.locked, hazard)
            found.append((record, path.name))
            continue
        note = _worktree_note(path, admin)
        if not inside and "name" not in note:
            continue
        record = Copy(
            note.get("name", path.name),
            "worktree",
            path,
            note,
            admin,
            entry.locked,
            _worktree_hazard(path),
        )
        found.append((record, path.name if inside else None))
    for path in worktree_folders:
        if path.name in registered:
            continue
        if path.name in unsafe_worktrees:
            hazard = unsafe_worktrees[path.name]
            found.append((Copy(path.name, "worktree", path, {}, hazard=hazard), path.name))
        elif _is_kind(worktrees, path, stat.S_ISDIR):
            found.append((Copy(path.name, "worktree", path, {}), path.name))
    copies = _by_name(found)
    for name in pins(repo):
        if name not in copies:
            copies[name] = Copy(name, "pins", None, {})
    return copies


def locate(repo: Path, name: str) -> Copy:
    """Return the registered copy called ``name``.

    Raises:
        WorkError: no copy, folder or pin has that name.

    """
    copy = discover(repo).get(name)
    if copy is None:
        msg = f"no copy named {name!r} (see `work.py list`)"
        raise WorkError(msg)
    return copy


def _live(copy: Copy) -> Path:
    """Return the folder of a safe copy git reads as its own checkout.

    Raises:
        WorkError: the copy is unsafe, its folder is gone or its ``.git`` is broken.

    """
    if copy.hazard is not None:
        msg = f"copy {copy.name!r} is unsafe, never touched: {copy.hazard}"
        raise WorkError(msg)
    if copy.path is None or not copy.present:
        msg = f"copy {copy.name!r} has no folder"
        raise WorkError(msg)
    if not copy.healthy:
        msg = f"copy {copy.name!r} at {copy.path} has a missing or broken .git; run `repair`"
        raise WorkError(msg)
    return copy.path


# --------------------------------------------------------------------------------------------
# Content, notes
# --------------------------------------------------------------------------------------------


def _refuse_sparse(copy_root: Path) -> None:
    """Refuse a sparse checkout or ``skip-worktree`` entries: missing files would read deleted.

    Raises:
        WorkError: the copy is sparse.

    """
    sparse = _git_runner.run_git(copy_root, "config", "--bool", "core.sparseCheckout")
    if sparse.stdout.strip() == "true":
        msg = f"{copy_root} is a sparse checkout; its content cannot be read whole"
        raise WorkError(msg)
    listing = _git(copy_root, "ls-files", "-t", "-z")
    if any(entry.startswith("S ") for entry in listing.split("\0")):
        msg = f"{copy_root} has skip-worktree entries; its content cannot be read whole"
        raise WorkError(msg)


def _unreadable(copy_root: Path, where: Path, error: OSError) -> WorkError:
    """Return the refusal for ``where``, a folder or file there but unreadable.

    ``where`` is named relative to ``copy_root`` when it lies below it, else in full.
    """
    if where == copy_root or not where.is_relative_to(copy_root):
        return WorkError(f"cannot read {where}: {error.strerror or error}")
    relative = where.relative_to(copy_root).as_posix()
    return WorkError(f"cannot read {relative} in {copy_root}: {error.strerror or error}")


def _mode(copy_root: Path, path: Path, *, follow: bool = False) -> int | None:
    """Return ``path``'s mode (``lstat``, links followed when ``follow``), ``None`` when absent.

    Only ``FileNotFoundError`` / ``NotADirectoryError`` is absent. ``Path.exists()``,
    ``is_file()``, ``is_dir()`` and ``is_symlink()`` cannot serve: before Python 3.14 they
    raise ``PermissionError`` for a path in a folder that cannot be entered, and from 3.14
    they answer ``False``, which reads a present path as gone.

    Raises:
        WorkError: ``path``'s folder cannot be looked into (named relative to ``copy_root``).

    """
    try:
        return (path.stat() if follow else path.lstat()).st_mode
    except (FileNotFoundError, NotADirectoryError):
        return None
    except OSError as error:
        raise _unreadable(copy_root, path.parent, error) from error


def _present(copy_root: Path, path: Path) -> bool:
    """Return whether ``path`` is there (a dangling symlink is); see :func:`_mode`.

    Raises:
        WorkError: ``path``'s folder cannot be looked into.

    """
    return _mode(copy_root, path) is not None


def _is_kind(copy_root: Path, path: Path, kind: Callable[[int], bool]) -> bool:
    """Return whether ``path`` (``lstat``) is there and of ``kind``; see :func:`_mode`.

    Raises:
        WorkError: ``path``'s folder cannot be looked into.

    """
    mode = _mode(copy_root, path)
    return mode is not None and kind(mode)


def _misspelled(copy_root: Path, paths: Sequence[str]) -> list[str]:
    """Return the tracked ``paths`` the folder does not hold under exactly that spelling.

    Only a folder or file that is not there (``FileNotFoundError``,
    ``NotADirectoryError``) reads as absent; one that is there but cannot be read would
    record its tracked files as deleted, so it refuses.

    Raises:
        WorkError: a folder on a tracked path cannot be listed, or a tracked path in it
            cannot be looked up.

    """
    listings: dict[Path, set[str]] = {}

    def holds(folder: Path, name: str) -> bool:
        if folder not in listings:
            try:
                listings[folder] = {entry.name for entry in folder.iterdir()}
            except (FileNotFoundError, NotADirectoryError):
                listings[folder] = set()
            except OSError as error:
                raise _unreadable(copy_root, folder, error) from error
        return name in listings[folder]

    missing: list[str] = []
    for path in paths:
        here = copy_root
        for part in PurePosixPath(path).parts:
            if not holds(here, part):
                missing.append(path)
                break
            here = here / part
        else:
            if not _present(copy_root, here):
                missing.append(path)
    return missing


def _refuse_unreadable(copy_root: Path, env: Mapping[str, str]) -> None:
    """Refuse a folder git would scan for untracked files but cannot list.

    ``git add -A`` only warns on such a folder and stages nothing from it, so new work
    there would silently miss the tree. Ignored folders git never opens are skipped.

    Raises:
        WorkError: a folder git would scan cannot be listed.

    """
    listing = _git(
        copy_root,
        *UNTRUSTED_CACHES,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "--directory",
        "-z",
        env=env,
    )
    ignored = {entry.rstrip("/") for entry in listing.split("\0") if entry.endswith("/")}

    pending = [copy_root]
    while pending:
        folder = pending.pop()
        try:
            with os.scandir(folder) as entries:
                children = [
                    Path(entry.path)
                    for entry in entries
                    if entry.is_dir(follow_symlinks=False) and entry.name != ".git"
                ]
        except OSError as error:
            raise _unreadable(copy_root, folder, error) from error
        pending.extend(
            child for child in children if child.relative_to(copy_root).as_posix() not in ignored
        )


def _refuse_nested(copy_root: Path) -> None:
    """Refuse an untracked folder that is a repository of its own (git would stage it as a gitlink).

    Raises:
        WorkError: the copy holds one, or a folder git lists cannot be looked into.

    """
    listing = _git(copy_root, "ls-files", "--others", "--exclude-standard", "--directory", "-z")
    nested = [
        entry
        for entry in listing.split("\0")
        if entry.endswith("/") and _present(copy_root, copy_root / entry / ".git")
    ]
    if nested:
        msg = (
            f"{copy_root} holds a nested repository or submodule at {', '.join(nested)}; "
            "its uncommitted work cannot be saved or landed"
        )
        raise WorkError(msg)


def content_tree(copy_root: Path) -> str:
    """Return the tree of the copy's working content, read into a fresh private index.

    The index starts from ``HEAD`` with no stat data or trust bits, so every tracked
    file is hashed from its bytes (``assume-unchanged``, the stat cache and
    ``core.fsmonitor`` never hide an edit); a tracked path the folder holds under no
    exact spelling is dropped first, so a case-only rename reads as that rename on a
    case-insensitive filesystem; untracked files git does not ignore are added and
    deletions honoured. The copy's own index is never read or written.

    Raises:
        WorkError: the copy is sparse (:func:`_refuse_sparse`), holds a gitlink or a nested
            repository (whose uncommitted work no tree can carry), holds a folder or
            tracked path that exists but cannot be read (:func:`_misspelled`,
            :func:`_refuse_unreadable`), or git fails.

    """
    _refuse_sparse(copy_root)
    private = _git_path(copy_root, f"dsf-work-index-{_token()}")
    env = {"GIT_INDEX_FILE": str(private)}
    try:
        _ = _git(copy_root, "read-tree", "HEAD", env=env)
        tracked = [path for path in _git(copy_root, "ls-files", "-z", env=env).split("\0") if path]
        misspelled = _misspelled(copy_root, tracked)
        if misspelled:
            _ = _git_bytes(
                copy_root,
                "update-index",
                "--force-remove",
                "-z",
                "--stdin",
                env=env,
                stdin="".join(f"{path}\0" for path in misspelled).encode(
                    "utf-8",
                    "surrogateescape",
                ),
            )
        _refuse_nested(copy_root)
        _refuse_unreadable(copy_root, env)
        _ = _git(copy_root, *UNTRUSTED_CACHES, "add", "-A", env=env)
        staged = _git(copy_root, "ls-files", "-s", "-z", env=env)
        nested = [
            record.partition("\t")[2]
            for record in staged.split("\0")
            if record.startswith("160000 ")
        ]
        if nested:
            msg = (
                f"{copy_root} holds a nested repository or submodule at {', '.join(nested)}; "
                "its uncommitted work cannot be saved or landed"
            )
            raise WorkError(msg)
        return _git(copy_root, "write-tree", env=env).strip()
    finally:
        private.unlink(missing_ok=True)


def _head(copy_root: Path) -> str:
    """Return the copy's ``HEAD`` commit."""
    return _resolve_commit(copy_root, "HEAD")


def _tree_of(root: Path, rev: str) -> str:
    """Return the tree id of ``rev``."""
    return _git(root, "rev-parse", f"{rev}^{{tree}}").strip()


def _snapshot(
    copy_root: Path,
    tree: str,
    parent: str,
    message: str,
) -> str:
    """Return a commit of ``tree`` on ``parent`` made in the copy (no ref, no index)."""
    return _git(
        copy_root,
        "commit-tree",
        tree,
        "-p",
        parent,
        "-m",
        message,
        env=SAVE_IDENTITY,
    ).strip()


def _scope(form: str) -> str:
    return "--local" if form == "clone" else "--worktree"


def write_note(copy_root: Path, form: str, values: Mapping[str, str]) -> None:
    """Write ``values`` into the copy's note (``--local`` for a clone, ``--worktree`` else)."""
    for key, value in values.items():
        _ = _git(copy_root, "config", _scope(form), f"{NOTE_SECTION}.{key}", value)


def recorded_pins(note: Mapping[str, str]) -> dict[str, str]:
    """Return the ``{leaf: commit}`` pins the note records the copy publishing (:data:`PINS_NOTE`)."""
    recorded: dict[str, str] = {}
    for entry in note.get(PINS_NOTE, "").split(","):
        leaf, _, commit = entry.partition("=")
        if leaf and commit:
            recorded[leaf] = commit
    return recorded


def record_pin(
    repo: Path,
    copy_root: Path,
    form: str,
    leaf: str,
    commit: str,
) -> None:
    """Record in the copy's note that it published the pin ``leaf`` at ``commit``.

    Read from the config at the write (not a note read earlier), so two pins one command
    publishes both stay recorded; a later pin under the leaf (``landed``) replaces it. A note
    older than :data:`PINS_NOTE` first records the pins :func:`legacy_pins` attributes to
    it, so its earlier saves stay its own once the key exists.
    """
    recorded = recorded_pins(attributed_note(repo, _config_values(copy_root, _scope(form))))
    recorded[leaf] = commit
    listed = ",".join(f"{key}={value}" for key, value in sorted(recorded.items()))
    write_note(copy_root, form, {PINS_NOTE: listed})


def pin_belongs(note: Mapping[str, str], leaf: str, commit: str) -> bool:
    """Return whether the note attributes the pin ``leaf`` at ``commit`` to its copy.

    Its ``start`` pin at the note's ``start``, or a pin it recorded publishing
    (:func:`recorded_pins`); anything else under the name is another copy's or cannot be
    told apart from one, and is never the copy's to drop.
    """
    if recorded_pins(note).get(leaf) == commit:
        return True
    return leaf == START_PIN and bool(commit) and commit == note.get("start", "")


def foreign_pins(note: Mapping[str, str], held: Mapping[str, str]) -> dict[str, str]:
    """Return the pins of ``held`` (``{leaf: commit}``) the note does not attribute to its copy."""
    return {leaf: commit for leaf, commit in held.items() if not pin_belongs(note, leaf, commit)}


def legacy_pins(repo: Path, note: Mapping[str, str]) -> dict[str, str]:
    """Return the pins a note older than :data:`PINS_NOTE` attributes to its copy (``{}`` else).

    Such a copy never recorded what it published. Its ``save-N``, ``landed`` and
    ``landed-copy`` pins under the name are taken as its own when their commit strictly
    descends from the note's ``start`` (every save and landing is built on the copy's
    ``HEAD``) and was committed no earlier than the note's ``created``: an earlier copy's
    pins under the name predate this copy, so they stay another's.
    """
    name, start, created = (note.get(key, "") for key in ("name", "start", "created"))
    if PINS_NOTE in note or not name or not start or not created.isdigit():
        return {}
    store = pin_store(repo)
    if store is None:
        return {}
    listing = _git(
        store,
        "for-each-ref",
        "--format=%(objectname) %(committerdate:unix) %(refname)",
        f"{PIN_PREFIX}{name}/",
    )
    found: dict[str, str] = {}
    for line in listing.splitlines():
        commit, stamp, ref = line.split(" ", 2)
        leaf = ref.removeprefix(f"{PIN_PREFIX}{name}/")
        if (
            (SAVE_PIN.fullmatch(leaf) or leaf in {LANDED_PIN, LANDED_COPY_PIN})
            and commit != start
            and stamp.isdigit()
            and int(stamp) >= int(created)
            and _is_ancestor(store, start, commit)
        ):
            found[leaf] = commit
    return found


def attributed_note(repo: Path, note: Mapping[str, str]) -> dict[str, str]:
    """Return ``note`` holding :data:`PINS_NOTE`: a note older than the key gets :func:`legacy_pins`."""
    attributed = dict(note)
    if PINS_NOTE not in attributed and attributed.get("name"):
        legacy = legacy_pins(repo, note)
        attributed[PINS_NOTE] = ",".join(f"{leaf}={sha}" for leaf, sha in sorted(legacy.items()))
    return attributed


def _apply_copy_config(copy_root: Path, form: str) -> None:
    """Set :data:`COPY_CONFIG` in the copy's own config."""
    for key, value in COPY_CONFIG:
        _ = _git(copy_root, "config", _scope(form), key, value)


def _ensure_worktree_config(repo: Path) -> None:
    """Turn ``extensions.worktreeConfig`` on in the shared checkout when it is off.

    Git's documented procedure first: a repository-level ``core.worktree`` (and a
    ``core.bare = true``) moves into the main worktree's ``config.worktree``, or every
    linked worktree would read them and resolve to the main tree.
    """
    completed = _git_runner.run_git(repo, "config", "--bool", "extensions.worktreeConfig")
    if completed.stdout.strip() == "true":
        return
    worktree = _git_runner.run_git(repo, "config", "--local", "core.worktree").stdout.strip()
    bare = _git_runner.run_git(repo, "config", "--local", "--bool", "core.bare").stdout.strip()
    _ = _git(repo, "config", "extensions.worktreeConfig", "true")
    if worktree:
        _ = _git(repo, "config", "--worktree", "core.worktree", worktree)
        _ = _git(repo, "config", "--local", "--unset", "core.worktree")
    if bare == "true":
        _ = _git(repo, "config", "--worktree", "core.bare", "true")
        _ = _git(repo, "config", "--local", "--unset", "core.bare")


# --------------------------------------------------------------------------------------------
# Environment
# --------------------------------------------------------------------------------------------


def _bin_dir(venv: Path) -> Path:
    return venv / ("Scripts" if os.name == "nt" else "bin")


def copy_database_name(name: str) -> str:
    """Return the Postgres database name a copy's ``run`` uses: ``dsfw_<name>``."""
    return "dsfw_" + name.replace("-", "_")


def clean_env(copy_root: Path, name: str, base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return the environment ``run`` gives a command in the copy at ``copy_root``.

    The caller's repository-locating, direnv, Django, pytest and coverage variables,
    ``PYTHONPATH`` and uv's project redirects are dropped, every other virtualenv's
    ``bin`` leaves ``PATH``, the copy's ``.venv`` leads it, and ``FAKESHOP_PG_DSN`` (when
    set) names the copy's own database.
    """
    source = os.environ if base is None else base
    env = {
        key: value
        for key, value in source.items()
        if key not in SCRUBBED_NAMES and not key.startswith(SCRUBBED_PREFIXES)
    }
    foreign = {
        str(_bin_dir(Path(source["VIRTUAL_ENV"]))) if "VIRTUAL_ENV" in source else "",
        str(_bin_dir(shared_root(REPO_ROOT) / ".venv")),
    }
    venv = copy_root / ".venv"
    entries = [
        entry
        for entry in source.get("PATH", os.defpath).split(os.pathsep)
        if entry and entry not in foreign
    ]
    env["PATH"] = os.pathsep.join([str(_bin_dir(venv)), *entries])
    env["VIRTUAL_ENV"] = str(venv)
    env["PROJECT_ROOT"] = str(copy_root)
    dsn = source.get(PG_DSN_ENV)
    if dsn:
        parts = urlsplit(dsn)
        env[PG_DSN_ENV] = urlunsplit(parts._replace(path=f"/{copy_database_name(name)}"))
    return env


def _setup_env() -> dict[str, str]:
    """Return the environment ``uv sync`` and ``pre-commit install`` run in for a new copy."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in SCRUBBED_NAMES and not key.startswith(SCRUBBED_PREFIXES)
    }


def package_location(copy_root: Path, env: Mapping[str, str]) -> Path:
    """Return where the copy's interpreter imports the package from, in ``env`` and the copy.

    Raises:
        WorkError: the copy has no interpreter, or the import fails.

    """
    python = _bin_dir(copy_root / ".venv") / ("python.exe" if os.name == "nt" else "python")
    if not python.exists():
        msg = (
            f"{copy_root} has no .venv; run `uv sync --frozen` in it (or `new` without --no-setup)"
        )
        raise WorkError(msg)
    completed = subprocess.run(
        [str(python), "-c", f"import {PACKAGE}; print({PACKAGE}.__file__)"],
        cwd=copy_root,
        env=dict(env),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        msg = f"the copy's interpreter cannot import {PACKAGE}: {completed.stderr.strip()}"
        raise WorkError(msg)
    return Path(completed.stdout.strip()).resolve()


# --------------------------------------------------------------------------------------------
# Safety checks
# --------------------------------------------------------------------------------------------


def _is_within(path: Path, root: Path) -> bool:
    try:
        _ = path.relative_to(root)
    except ValueError:
        return False
    return True


# The login and agent daemons the ``/proc`` census skips when it cannot read their working
# folder, keyed by ``/proc/<pid>/comm`` (the executable's base name, cut by the kernel to 15
# characters), each with the pattern its ``/proc/<pid>/cmdline`` (arguments joined by spaces)
# must match. Both files are readable for every process; ``cwd`` is not for a process that is
# not dumpable or holds credentials or capabilities this one lacks, and every Linux login
# starts some of these. ``/proc/<pid>/status`` cannot stand in for the names: ``(sd-pam)``
# and ``sshd-session`` show ids and capabilities equal to any shell's, since dumpability is
# not in it. Nor can a start time: a process older than the copy can still enter it. None of
# these runs a user's work (a login shell is a child, read and counted like any other) or
# holds a file under its working folder, so a copy one of them sits in loses no work.
CENSUS_SKIPPED_DAEMONS: dict[str, re.Pattern[str]] = {
    # The user's service manager: started by PID 1 in the home folder, never changes folder;
    # unreadable because it holds a capability (``CAP_WAKE_ALARM``) a shell lacks.
    "systemd": re.compile(r"(?:/usr)?/lib/systemd/systemd --user"),
    # The user manager's PAM helper: forked as root and dropped to the user (so not
    # dumpable), it only waits to close the PAM session.
    "(sd-pam)": re.compile(r"\(sd-pam\)"),
    # OpenSSH's per-connection process (9.8 and later), dropped from root to the user and
    # marked not dumpable; it relays the session, whose shell is its child.
    "sshd-session": re.compile(r"sshd-session: \S+@(?:pts/\d+|notty)"),
    # The same process before OpenSSH 9.8.
    "sshd": re.compile(r"sshd: \S+@(?:pts/\d+|notty)"),
    # Key agents: setgid, not dumpable or holding a capability to guard the keys they keep in
    # memory; their sockets live in the runtime or GnuPG folder; a forking start moves to /.
    "ssh-agent": re.compile(r"(?:\S*/)?ssh-agent(?: .*)?"),
    "gpg-agent": re.compile(r"(?:\S*/)?gpg-agent(?: .*)?"),
    "gnome-keyring-d": re.compile(r"(?:\S*/)?gnome-keyring-daemon(?: .*)?"),
}


@dataclasses.dataclass(frozen=True)
class CensusGap:
    """Why the process census cannot vouch for a folder: it is incomplete."""

    reason: str


def _proc_command(entry: Path) -> tuple[str, str] | None:
    """Return a process's ``comm`` and its arguments joined by spaces; ``None`` once it is gone.

    Both read as empty when the kernel will not show them, which matches no daemon.
    """
    try:
        comm = (entry / "comm").read_bytes()
        argv = (entry / "cmdline").read_bytes()
    except (FileNotFoundError, ProcessLookupError):
        return None
    except OSError:
        return "", ""
    return (
        comm.decode(errors="replace").removesuffix("\n"),
        " ".join(part.decode(errors="replace") for part in argv.rstrip(b"\0").split(b"\0")),
    )


def _unreadable_gap(entry: Path, *, others_shut_out: bool) -> CensusGap | None:
    """Return the gap a process whose cwd cannot be read leaves; ``None`` when it is skipped.

    Another user's is skipped while ``others_shut_out`` (``.work`` is ``0700``, so no other
    non-root user can be inside), one of this user's own only when it is a daemon of
    :data:`CENSUS_SKIPPED_DAEMONS`.
    """
    try:
        own = entry.stat().st_uid == os.getuid()
    except OSError:
        return None
    if not own and others_shut_out:
        return None
    command = _proc_command(entry)
    if command is None:
        return None
    comm, cmdline = command
    if own:
        daemon = CENSUS_SKIPPED_DAEMONS.get(comm)
        if daemon is not None and daemon.fullmatch(cmdline) is not None:
            return None
        whose = "one of this user's own processes that is not a known login daemon"
    else:
        whose = "another user's, while no folder above the copy shuts others out"
    shown = "".join(char if char.isprintable() else "?" for char in cmdline or comm) or "?"
    return CensusGap(f"cannot read the working folder of pid {entry.name} ({shown}), {whose}")


def _proc_users(proc: Path, target: Path, *, others_shut_out: bool) -> list[str] | CensusGap:
    """Census ``/proc``: the pids whose cwd lies in ``target``, or why it cannot tell.

    A process whose cwd cannot be read is unknown: skipped or a gap by
    :func:`_unreadable_gap`.
    """
    users: list[str] = []
    seen_self = False
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            cwd = (entry / "cwd").readlink()
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            gap = _unreadable_gap(entry, others_shut_out=others_shut_out)
            if gap is not None:
                return gap
            continue
        if int(entry.name) == os.getpid():
            seen_self = True
        elif _is_within(cwd, target):
            users.append(entry.name)
    return users if seen_self else CensusGap("/proc does not list this process")


def _lsof_users(lsof: str, target: Path, *, others_shut_out: bool) -> list[str] | CensusGap:
    """Census through ``lsof -d cwd``; a gap when it fails, misses this process, or cannot cover.

    ``lsof`` lists only what this user may see, so it vouches for a copy only while no
    other (non-root) user can enter it (``others_shut_out``).
    """
    if not others_shut_out:
        return CensusGap(
            "lsof lists only this user's processes, and no folder above the copy shuts others out",
        )
    completed = subprocess.run(
        [
            lsof,
            "-n",
            "-w",
            "-d",
            "cwd",
            "-F",
            "pn",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return CensusGap(f"lsof exited {completed.returncode}")
    users: list[str] = []
    seen_self = False
    pid = ""
    for line in completed.stdout.splitlines():
        if line.startswith("p"):
            pid = line[1:]
            seen_self = seen_self or pid == str(os.getpid())
        elif line.startswith("n") and pid != str(os.getpid()):
            with contextlib.suppress(OSError, ValueError):
                if _is_within(Path(line[1:]).resolve(), target):
                    users.append(pid)
    return users if seen_self else CensusGap("lsof does not list this process")


def others_shut_out(path: Path) -> bool:
    """Return whether a folder at or above ``path`` is this user's and closed to everyone else."""
    for folder in (path, *path.parents):
        with contextlib.suppress(OSError):
            info = folder.stat()
            if info.st_uid == os.getuid() and not info.st_mode & 0o077:
                return True
    return False


def process_census(path: Path) -> list[str] | CensusGap:
    """Return the processes whose current directory lies in ``path``, or why it cannot tell.

    Linux reads ``/proc/<pid>/cwd``; elsewhere ``lsof -d cwd`` is asked. A census that
    fails, cannot read a process it has to vouch for, or does not list the process asking
    (a census that ran at all sees its own caller) is incomplete: a :class:`CensusGap`.
    Root's processes stay invisible to both.
    """
    target = path.resolve()
    shut = others_shut_out(target)
    proc = Path("/proc")
    if proc.is_dir() and (proc / "self" / "cwd").exists():
        return _proc_users(proc, target, others_shut_out=shut)
    lsof = shutil.which("lsof")
    if lsof is None:
        return CensusGap("this machine has neither /proc nor lsof")
    return _lsof_users(lsof, target, others_shut_out=shut)


def cwd_users(path: Path) -> list[str] | None:
    """Return :func:`process_census`'s pids for ``path``; ``None`` when it cannot tell."""
    found = process_census(path)
    return None if isinstance(found, CensusGap) else found


def newest_mtime(path: Path) -> float:
    """Return the newest modification time of any file or folder in ``path``.

    ``.git``, ``.venv`` and tool caches are skipped: a sync or a git read moves them
    without anyone editing the copy.
    """
    newest = path.stat().st_mtime
    for directory, dirnames, filenames in os.walk(path):
        dirnames[:] = [name for name in dirnames if name not in UNWATCHED_DIRS]
        for name in (*dirnames, *filenames):
            with contextlib.suppress(OSError):
                newest = max(newest, (Path(directory) / name).lstat().st_mtime)
    return newest


def _workspace_state(copy_root: Path) -> list[Path]:
    """Return the ``workspace.py`` pool and state folders that exist for ``copy_root``.

    ``scripts.workspace`` is the fallback only when ``workspace`` itself is not on the
    path (``work`` imported as ``scripts.work``); a module ``workspace.py`` needs and
    lacks (``tomli`` under a bare interpreter) is raised under its own name.
    """
    try:
        import workspace  # noqa: PLC0415 - read only for a copy's state paths
    except ModuleNotFoundError as error:
        if error.name != "workspace":
            raise
        from scripts import workspace  # noqa: PLC0415 - imported as ``scripts.work``
    resolved = copy_root.resolve()
    try:
        base = workspace.workspace_base(resolved)
    except workspace.WorkspaceError as error:
        msg = f"cannot tell whether workspace.py holds state for {copy_root}: {error}"
        raise WorkError(msg) from None
    return [path for path in (base, workspace.state_root(base)) if _present(path.parent, path)]


def _prove_state(copy_root: Path) -> Path | None:
    """Return the ``prove_failability.py`` state folder of ``copy_root`` when it exists."""
    try:
        import prove_failability  # noqa: PLC0415 - read only for a copy's state path
    except ModuleNotFoundError:
        from scripts import prove_failability  # noqa: PLC0415 - imported as ``scripts.work``
    directory = prove_failability.tree_state_directory(copy_root.resolve())
    return directory if _present(directory.parent, directory) else None


def _settled_at(note: Mapping[str, str]) -> float:
    """Return when the copy's content was last pinned, landed or synced (epoch seconds), else 0."""
    stamps = [note.get("savedat", ""), note.get("landedat", ""), note.get("syncedat", "")]
    return max((float(stamp) for stamp in stamps if stamp), default=0.0)


def _untouched(copy: Copy) -> bool:
    """Return whether the copy's content is still the tree it started at (no edit yet).

    A fresh copy's own checkout and setup move its mtimes without anyone editing it, so
    only content that differs from the ``start`` the note records counts as a recent edit.
    An unreadable copy is never untouched.
    """
    start = copy.note.get("start", "")
    if not start or copy.path is None or not copy.healthy:
        return False
    try:
        return content_tree(copy.path) == _tree_of(copy.path, start)
    except WorkError:
        return False


def _complete(store: Path, commit: str) -> bool:
    """Return whether ``pins.git`` holds every object ``commit`` reaches (its whole content)."""
    listing = _git_runner.run_git(store, "rev-list", "--objects", "--missing=error", commit)
    if listing.returncode != 0:
        return False
    ids = "".join(f"{line.split(' ', 1)[0]}\n" for line in listing.stdout.splitlines() if line)
    checked = _git_runner.run_git(
        store,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        stdin=ids,
    )
    return checked.returncode == 0 and not any(
        line.endswith(" missing") for line in checked.stdout.splitlines()
    )


def _keeping_leaf(leaf: str) -> bool:
    """Return whether a pin leaf outlives ``rm`` (a save or landing pin, never ``start``)."""
    return leaf in {LANDED_PIN, LANDED_COPY_PIN} or bool(SAVE_PIN.fullmatch(leaf))


def _pinned_trees(repo: Path, name: str) -> set[str]:
    """Return the trees of every save and landing pin of ``name`` whose content ``pins.git`` holds whole."""
    store = pin_store(repo)
    if store is None:
        return set()
    return {
        _tree_of(store, sha)
        for leaf, sha in pins(repo).get(name, {}).items()
        if _keeping_leaf(leaf) and _complete(store, sha)
    }


def _shared_ref_reaches(repo: Path, commit: str) -> bool:
    """Return whether a branch, tag or remote-tracking ref of the shared repository reaches ``commit``.

    The ``refs/work/`` pins live in ``pins.git``, never here, so none of them counts; a
    commit the shared repository does not hold (one made in a clone) is reached by none.
    """
    listing = _git_runner.run_git(
        repo,
        "for-each-ref",
        f"--contains={commit}",
        "--count=1",
        "--format=%(refname)",
        *SHARED_REFS,
    )
    return listing.returncode == 0 and bool(listing.stdout.strip())


def _at_durable_start(repo: Path, copy: Copy, head: str) -> bool:
    """Return whether ``head`` is the copy's start commit and that start is shared work.

    A start is shared when ``new`` found a shared ref reaching it (the note's
    ``startshared = true``), or when one reaches it now. The first keeps a pristine copy
    removable after main is amended or rebased past its start: the commit was the shared
    repository's, and its owner dropped it there. A start is not durable by being one:
    ``adopt`` pins whatever ``HEAD`` the copy holds (a commit made in it included), and
    ``new --from`` can start at a commit only another copy or a pin ``gc`` later drops
    reaches; both record ``startshared = false``, and such a start is work, kept only as
    :func:`_head_kept` keeps any other commit. A note older than the flag has only the
    current check.
    """
    start = pins(repo).get(copy.name, {}).get(START_PIN) or copy.note.get("start", "")
    if not head or head != start:
        return False
    recorded = copy.note.get("startshared") == "true" and head == copy.note.get("start")
    return recorded or _shared_ref_reaches(repo, start)


def _commit_kept(repo: Path, commit: str) -> bool:
    """Return whether ``commit`` outlives every copy.

    It does when a branch, tag or remote-tracking ref of the shared repository reaches it
    (:func:`_shared_ref_reaches`), or when a save or landing pin of any copy reaches it and
    ``pins.git`` holds that pin whole. No ``start`` pin counts, another copy's included:
    ``rm`` drops a removed copy's ``start`` pin, so a commit only a ``start`` pin reaches
    dies with that copy (:func:`_keeping_leaf`).
    """
    if _shared_ref_reaches(repo, commit):
        return True
    store = pin_store(repo)
    if store is None:
        return False
    listing = _git_runner.run_git(
        store,
        "for-each-ref",
        f"--contains={commit}",
        "--format=%(objectname) %(refname)",
        PIN_PREFIX,
    )
    if listing.returncode != 0:
        return False
    for line in listing.stdout.splitlines():
        sha, _, ref = line.partition(" ")
        if _keeping_leaf(ref.rpartition("/")[2]) and _complete(store, sha):
            return True
    return False


def _head_kept(repo: Path, copy: Copy, head: str) -> bool:
    """Return whether the copy's ``HEAD`` commit outlives the copy.

    It does when it is the commit the copy started from and a shared ref reaches that
    start (:func:`_at_durable_start`, as ``save`` agrees), or when :func:`_commit_kept`
    keeps it (a shared branch or tag, ``main`` among them, or a whole save or landing pin).
    """
    return _at_durable_start(repo, copy, head) or _commit_kept(repo, head)


def _shared_holds(repo: Path, commit: str) -> bool:
    """Return whether the shared repository's object store holds ``commit``."""
    found = _git_runner.run_git(repo, "cat-file", "-e", f"{commit}^{{commit}}")
    return found.returncode == 0


def _lost_ref_refusal(
    repo: Path,
    copy: Copy,
    root: Path,
    listing_args: Sequence[str],
    patterns: Sequence[str],
    hint: str,
) -> str | None:
    """Return why a ref that dies with ``copy`` holds commits nothing durable keeps, else ``None``.

    ``git -C root <listing_args> for-each-ref <patterns>`` lists exactly the refs that die
    with the copy; each must point at a commit :func:`_commit_kept` keeps, or at the
    copy's start while :func:`_at_durable_start` keeps it (the branch ``git clone`` leaves
    at it, a pristine copy's own ref). An annotated tag is read through to the commit it
    names. A ``refs/remotes/parent/`` ref mirrors the shared repository it was fetched
    from, so one whose commit that repository still holds loses nothing the shared
    repository's owner has not already dropped there (main amended or rebased past it, a
    branch deleted); one on a commit made in the clone, or any other remote's ref, is
    judged like every other ref. ``hint`` says how to keep it.
    """
    listing = _git_runner.run_git(
        root,
        *listing_args,
        "for-each-ref",
        "--format=%(refname) %(objectname) %(*objectname)",
        *patterns,
    )
    if listing.returncode != 0:
        return f"its refs cannot be listed ({listing.stderr.strip()}); pass --discard"
    start = copy.note.get("start", "")
    verdicts: dict[str, bool] = {}
    for line in listing.stdout.splitlines():
        ref, _, ids = line.partition(" ")
        if not ref:
            continue
        target, _, peeled = ids.partition(" ")
        commit = peeled.strip() or target
        if commit not in verdicts:
            verdicts[commit] = (commit == start and _at_durable_start(repo, copy, commit)) or (
                _commit_kept(repo, commit)
            )
        if not verdicts[commit] and not (
            ref.startswith(PARENT_REFS) and _shared_holds(repo, commit)
        ):
            return (
                f"its ref {ref} {commit[:12]} holds commits neither main nor a pin reaches: "
                f"{hint}, or pass --discard"
            )
    return None


def _clone_ref_refusal(repo: Path, copy: Copy, copy_root: Path) -> str | None:
    """Return why a ref of the clone ``copy`` at ``copy_root`` holds unkept commits, else ``None``.

    Every ref of a clone (branches, tags, ``refs/stash``, its remote-tracking refs, any
    other) lives in its folder and dies with it (:func:`_lost_ref_refusal`). ``save``
    pins only ``HEAD`` and the content, so a side ref is kept by checking it out and
    saving it, or by deleting it.
    """
    return _lost_ref_refusal(
        repo,
        copy,
        copy_root,
        (),
        (),
        "check it out and `save` it, delete the ref",
    )


def _worktree_ref_refusal(repo: Path, copy: Copy) -> str | None:
    """Return why a per-worktree ref of the worktree ``copy`` holds unkept commits, else ``None``.

    A worktree's branches and tags are the shared repository's and outlive it, but its
    per-worktree refs (``refs/bisect/``, ``refs/worktree/``, ``refs/rewritten/``) live in
    its metadata and die with it (:func:`_lost_ref_refusal`). They are read through the
    metadata (``--git-dir``), which holds them whether the folder is present or gone; a
    worktree whose metadata git does not list is read from its folder.
    """
    if copy.admin is not None and _is_kind(copy.admin.parent, copy.admin, stat.S_ISDIR):
        root, listing_args = repo, (f"--git-dir={copy.admin}",)
    elif copy.path is not None and copy.present:
        root, listing_args = copy.path, ()
    else:
        return None
    return _lost_ref_refusal(
        repo,
        copy,
        root,
        listing_args,
        PER_WORKTREE_REFS,
        "check it out in a copy and `save` it, delete the ref",
    )


def _content_refusal(repo: Path, copy: Copy) -> str | None:
    """Return why the copy's content is not known safe to delete, else ``None``.

    Safe means the content is a tree something keeps (``HEAD``'s, or a whole save or
    landing pin's) and the ``HEAD`` commit itself outlives the copy (:func:`_head_kept`):
    a commit made in the copy that nothing kept reaches is work, and ``save`` pins it. A
    clone's refs die with its folder, so each must reach only kept commits
    (:func:`_clone_ref_refusal`); a worktree's branches and tags live in the shared
    repository, which removing the worktree leaves as they are, but its per-worktree refs
    die with it (:func:`_worktree_ref_refusal`). A commit only a reflog reaches (one a
    ``git reset --hard`` moved past) counts as discarded by its owner: no reflog is read.
    """
    if not copy.healthy or copy.path is None:
        return (
            "its content cannot be read (missing or broken .git): `repair` it, or pass --discard"
        )
    try:
        tree = content_tree(copy.path)
    except WorkError as error:
        return f"its content cannot be read ({error}); pass --discard"
    if tree != _tree_of(copy.path, "HEAD") and tree not in _pinned_trees(repo, copy.name):
        return (
            "its content is neither HEAD, a save nor the landed pin: `save` or `land` it, "
            "or pass --discard"
        )
    head = _head(copy.path)
    if not _head_kept(repo, copy, head):
        return (
            f"its HEAD {head[:12]} is a commit made in the copy that neither main nor a pin "
            "reaches: `save` it, or pass --discard"
        )
    if copy.form == "clone":
        return _clone_ref_refusal(repo, copy, copy.path)
    return _worktree_ref_refusal(repo, copy)


def _admin_head(repo: Path, admin: Path) -> str:
    """Return the commit a worktree's metadata records as its ``HEAD``, ``""`` when it names none.

    A symbolic ``HEAD`` (``ref: refs/heads/<branch>``) is resolved in the shared repository.
    """
    try:
        recorded = (admin / "HEAD").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return ""
    if recorded.startswith("ref:"):
        recorded = recorded.removeprefix("ref:").strip()
    return _resolve_commit(repo, recorded) if recorded else ""


def _gone_folder_refusal(repo: Path, copy: Copy) -> str | None:
    """Return why a copy whose folder is gone must not be forgotten, else ``None``.

    A worktree keeps its objects in the shared repository and its ``HEAD`` in its
    metadata, so a commit made in it survives its folder until that metadata goes: it is
    refused unless :func:`_head_kept` keeps that ``HEAD`` and every per-worktree ref the
    metadata holds reaches only kept commits (:func:`_worktree_ref_refusal`). A clone held
    its objects in its own folder, so a clone whose folder is gone left nothing to keep and
    is never refused.
    """
    if (
        copy.form != "worktree"
        or copy.admin is None
        or not _is_kind(copy.admin.parent, copy.admin, stat.S_ISDIR)
    ):
        return None
    head = _admin_head(repo, copy.admin)
    if not head:
        return "its folder is gone and its metadata names no readable HEAD; pass --discard"
    if not _head_kept(repo, copy, head):
        return (
            f"its folder is gone but its HEAD {head[:12]} is a commit made in the copy that "
            f"neither main nor a pin reaches: `new <name> --from {head}` and `save` it, or "
            "pass --discard"
        )
    return _worktree_ref_refusal(repo, copy)


def removal_refusals(repo: Path, copy: Copy, *, discard: bool) -> list[str]:
    """Return every reason ``rm`` must not remove ``copy`` (empty = removable)."""
    if copy.hazard is not None:
        return [f"unsafe, never touched: {copy.hazard}"]
    if not _valid(copy.name):
        return [f"{copy.name!r} is not a valid copy name; remove it by hand"]
    if copy.path is None:
        return []
    allowed = (work_dir(repo) / (CLONES if copy.form == "clone" else WORKTREES)).resolve()
    if (
        _is_kind(copy.path.parent, copy.path, stat.S_ISLNK)
        or copy.path.resolve().parent != allowed
    ):
        return [f"{copy.path} is not a folder directly under {allowed}"]
    reasons: list[str] = []
    if copy.locked is not None and not copy.locked.startswith(LOCK_REASON_PREFIX):
        reasons.append(f"its worktree is locked by someone else: {copy.locked or '(no reason)'}")
    if not copy.present:
        refusal = None if discard else _gone_folder_refusal(repo, copy)
        return reasons if refusal is None else [*reasons, refusal]
    users = process_census(copy.path)
    if isinstance(users, CensusGap):
        if os.name != "nt":
            reasons.append(
                f"the process census is incomplete: {users.reason}, so it cannot tell "
                "whether a process works in it",
            )
    elif users:
        reasons.append(f"process {', '.join(users)} has its current directory inside it")
    modified = newest_mtime(copy.path)
    if (
        modified > _settled_at(copy.note)
        and time.time() - modified < RECENT_SECONDS
        and not _untouched(copy)
    ):
        reasons.append(
            f"modified {int(time.time() - modified)}s ago, after its last save or landing "
            f"(wait {RECENT_SECONDS // 60} minutes, or `save` it)",
        )
    reasons.extend(
        f"scripts/workspace.py holds {path} for it; run `workspace.py gc <flow>` in the copy"
        for path in _workspace_state(copy.path)
    )
    proof = _prove_state(copy.path)
    if proof is not None:
        reasons.append(
            f"scripts/prove_failability.py state {proof} exists (a proof may be live or "
            "unproved); resolve it first",
        )
    if not discard:
        refusal = _content_refusal(repo, copy)
        if refusal is not None:
            reasons.append(refusal)
    return reasons


def _grant_owner(path: Path) -> None:
    """Give the owner what a delete needs where it is missing: ``rwx`` on a folder.

    A folder without ``r``/``x`` cannot be listed or entered and one without ``w`` cannot
    lose entries. A file's mode is never changed where its folder alone decides its
    delete, since a hard-linked file shares that mode with every other link to it,
    outside ``.work`` too; where a read-only file refuses its delete
    (:data:`READ_ONLY_FILES_BLOCK_DELETE`), only a file with no other link gets the
    owner's write bit. A symlink is never followed. A refused grant is left for the
    delete to report.
    """
    with contextlib.suppress(OSError):
        info = path.lstat()
        mode = info.st_mode
        if stat.S_ISDIR(mode):
            wanted = stat.S_IRWXU
        elif stat.S_ISREG(mode) and READ_ONLY_FILES_BLOCK_DELETE and info.st_nlink == 1:
            wanted = stat.S_IWRITE
        else:
            return
        if mode & wanted != wanted:
            path.chmod(stat.S_IMODE(mode) | wanted)


def delete_tree(path: Path) -> None:
    """Delete ``path`` recursively, first granting the owner every bit a delete needs.

    The walk is top-down and never follows a symlink, so each folder is granted before
    it is listed: a mode-000 folder anywhere in the tree is opened, not skipped. A
    symlink at ``path`` (read with ``lstat``) is unlinked alone: its target is never
    walked, granted or deleted.
    """
    if stat.S_ISLNK(path.lstat().st_mode):
        path.unlink()
        return
    _grant_owner(path)
    for directory, dirnames, filenames in os.walk(path):
        for name in (*dirnames, *filenames):
            _grant_owner(Path(directory) / name)
    shutil.rmtree(path)


# --------------------------------------------------------------------------------------------
# new, adopt
# --------------------------------------------------------------------------------------------


def free_bytes(path: Path) -> int:
    """Return the free bytes on ``path``'s filesystem."""
    return shutil.disk_usage(path).free


def _say(message: str) -> None:
    print(f"work: {message}", file=sys.stderr)


def cmd_check_name(args: _Args) -> int:
    """Print a valid name's parts, or refuse it."""
    name = parse_name(args.name)
    print(
        f"kind={name.kind} id={name.id or '-'} slug={name.slug} suffix={name.suffix or '-'} "
        f"stem={name.stem}",
    )
    return 0


def _run_setup_step(command: Sequence[str], copy_root: Path) -> None:
    """Run one setup command in the copy; a failure is the ``new``'s failure.

    Raises:
        WorkError: the command exits non-zero; the message carries its stderr.

    """
    completed = subprocess.run(
        list(command),
        cwd=copy_root,
        env=_setup_env(),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        msg = f"{' '.join(command)} failed in {copy_root} ({completed.returncode}): {detail}"
        raise WorkError(msg)


def _setup(copy_root: Path, form: str) -> None:
    """Sync the copy's venv and, for a clone, install the pre-commit hook."""
    if shutil.which("uv") is None:
        msg = "uv is not on PATH, so the copy's .venv cannot be built"
        raise WorkError(msg)
    _run_setup_step(
        (
            "uv",
            "sync",
            "--frozen",
            "--quiet",
        ),
        copy_root,
    )
    if form != "clone":
        return
    if shutil.which("pre-commit") is None:
        _say("pre-commit is not on PATH; the clone has no hook (`pre-commit install` there)")
        return
    _run_setup_step(("pre-commit", "install"), copy_root)


@dataclasses.dataclass(frozen=True)
class Start:
    """Where a new copy starts: its base commit, and pinned content to lay over it."""

    base: str
    restore: str | None


def resolve_start(repo: Path, rev: str) -> Start:
    """Resolve ``--from``: a shared revision, or a pin.

    A ``start`` pin is a commit to start at. Every other pin (``save-N``, ``landed``,
    ``landed-copy``) is content on its parent: the copy starts at that parent with the
    pinned content as uncommitted work, so the parent must be on the shared main.

    Raises:
        WorkError: ``rev`` names no commit, or a pin's parent cannot be found or is not
            on the shared main.

    """
    if rev.startswith(PIN_PREFIX):
        store = pin_store(repo)
        commit = "" if store is None else _resolve_commit(store, rev)
        if not commit or store is None:
            msg = f"{rev!r} names no pin"
            raise WorkError(msg)
        leaf = rev.rsplit("/", 1)[-1]
        if leaf == START_PIN:
            fetch_pinned(repo, repo, commit)
            return Start(commit, None)
        base = _resolve_commit(store, f"{commit}^")
        if not base:
            msg = f"{rev!r} has no parent commit to start from"
            raise WorkError(msg)
        on_main = _git_ok(repo, "cat-file", "-e", f"{base}^{{commit}}") and _is_ancestor(
            repo,
            base,
            LANDING_BRANCH,
        )
        if not on_main:
            msg = (
                f"{rev!r} is content pinned on {base[:12]}, which is not on the shared "
                "main, so a copy started there could never land; start from a save or "
                "landing pinned on main"
            )
            raise WorkError(msg)
        fetch_pinned(repo, repo, commit)
        return Start(base, commit)
    commit = _resolve_commit(repo, rev)
    if not commit:
        msg = f"{rev!r} names no commit in {repo}"
        raise WorkError(msg)
    return Start(commit, None)


def _make_copy(
    repo: Path,
    name: Name,
    form: str,
    path: Path,
    start: Start,
) -> None:
    """Fill the claimed, empty ``path`` with a ``form`` copy of ``repo`` at ``start``.

    Raises:
        WorkError: git fails, or git does not read the new copy as its own checkout.

    """
    if form == "clone":
        _ = _git(
            repo,
            "clone",
            "--quiet",
            "--no-hardlinks",
            "--no-checkout",
            "-o",
            "parent",
            str(repo),
            str(path),
        )
        if start.restore is not None:
            fetch_pinned(repo, path, start.restore)
        cloned = _git_runner.run_git(path, "symbolic-ref", "--quiet", "--short", "HEAD")
        _ = _git(path, "checkout", "--quiet", "--detach", start.base)
        _ = _git(path, "remote", "set-url", "--push", "parent", NO_PUSH)
        branch = cloned.stdout.strip() if cloned.returncode == 0 else ""
        if branch:
            # The clone's HEAD is detached: nothing there tracks the branch the clone made.
            _ = _git(path, "config", "--local", "--remove-section", f"branch.{branch}")
    else:
        _ensure_worktree_config(repo)
        _ = _git(repo, "worktree", "add", "--quiet", "--detach", str(path), start.base)
        _ = _git(
            repo,
            "worktree",
            "lock",
            "--reason",
            f"{LOCK_REASON_PREFIX}{name.text}",
            str(path),
        )
    if not _is_own_checkout(path):
        msg = f"git does not read {path} as its own checkout; nothing was made"
        raise WorkError(msg)
    _apply_copy_config(path, form)
    if start.restore is not None:
        _ = _git(path, "read-tree", "-u", "--reset", start.restore)
        _ = _git(path, "reset", "--quiet", "-N")


def _undo_new(
    repo: Path,
    form: str,
    path: Path,
    name: str,
) -> None:
    """Remove what a failed ``new`` made: the folder, its worktree metadata, its pin, its claim."""
    if form == "worktree":
        _ = _git_runner.run_git(repo, "worktree", "unlock", str(path))
        _ = _git_runner.run_git(repo, "worktree", "remove", "--force", "--force", str(path))
    if path.exists() and not path.is_symlink():
        delete_tree(path)
    store = pin_store(repo)
    if store is not None:
        _ = _git_runner.run_git(store, "update-ref", "-d", _pin_ref(name, START_PIN))
    release_name(repo, name)


def _refuse_taken(repo: Path, name: str, path: Path | None = None) -> None:
    """Refuse a ``name`` another copy, folder or pin already holds (``path`` itself excepted).

    Raises:
        WorkError: the name is taken.

    """
    existing = discover(repo).get(name)
    if existing is None or (path is not None and existing.path == path):
        return
    if existing.form == "pins":
        leaves = ", ".join(sorted(pins(repo).get(name, {})))
        msg = (
            f"{name!r} already has pins left from an earlier copy ({leaves}): `work.py rm "
            f"{name} --drop-saves` drops them here and, at the next `fleet_sync.py sync`, on "
            f"every fleet machine holding no copy under the name; restore a save first with "
            f"`new <other name> --from refs/work/{name}/save-N`, or take a -verify / -r2 name"
        )
        raise WorkError(msg)
    msg = (
        f"{name!r} already has a copy; `rm` it (with --drop-saves to free the name) "
        "or take a -verify / -r2 name"
    )
    raise WorkError(msg)


def _pin_start(
    repo: Path,
    path: Path,
    commit: str,
    name: str,
) -> None:
    """Pin ``start`` for a new or adopted copy.

    Raises:
        WorkError: a start pin already exists for the name.

    """
    if not publish_pin(repo, path, commit, name, START_PIN):
        msg = f"{_pin_ref(name, START_PIN)} already exists"
        raise WorkError(msg)


def _build_copy(
    repo: Path,
    name: Name,
    form: str,
    path: Path,
    args: _Args,
) -> None:
    """Make, note, pin and set up the copy at the claimed ``path``."""
    start = resolve_start(repo, args.from_rev)
    _make_copy(repo, name, form, path, start)
    note = {
        "name": name.text,
        "form": form,
        "purpose": args.purpose,
        "owner": args.owner,
        "host": fleet.this_hostname(),
        "home": machine_id(),
        "start": start.base,
        "startshared": "true" if _shared_ref_reaches(repo, start.base) else "false",
        "created": str(int(time.time())),
        "incarnation": secrets.token_hex(8),
        PINS_NOTE: f"{START_PIN}={start.base}",
    }
    if start.restore:
        note["restoredfrom"] = start.restore
    write_note(path, form, note)
    _pin_start(repo, path, start.base, name.text)
    for extra in EXTRA_FILES:
        if (repo / extra).is_file() and not (path / extra).exists():
            _ = shutil.copy2(repo / extra, path / extra)
    if not args.no_setup:
        _setup(path, form)


def refuse_control_text(args: _Args) -> None:
    """Refuse a ``--purpose`` or ``--owner`` holding a newline or another control character.

    A control character (Unicode ``Cc``) or a line or paragraph separator (``Zl``, ``Zp``).

    Both are written into the note and printed on one ``list`` line, so a control character
    would split or rewrite that line.

    Raises:
        WorkError: one of them holds a control character.

    """
    for option, value in (("--purpose", args.purpose), ("--owner", args.owner)):
        if any(unicodedata.category(character) in {"Cc", "Zl", "Zp"} for character in value):
            msg = f"{option} {value!r} holds a newline or another control character"
            raise WorkError(msg)


def cmd_new(args: _Args) -> int:
    """Claim a name and make its copy."""
    repo = REPO_ROOT
    name = parse_name(args.name)
    refuse_control_text(args)
    form = "worktree" if args.worktree else "clone"
    if free_bytes(repo) < MIN_FREE_BYTES:
        msg = f"less than {MIN_FREE_BYTES // 1024**3} GB free; free disk before making a copy"
        raise WorkError(msg)
    _ = ensure_sentinel(repo)
    container = CLONES if form == "clone" else WORKTREES
    path = work_dir(repo) / container / name.text
    # The stem's lock until the folder makes the name a user of the stem's evidence.
    with stem_lock(repo, name.stem, STEM_LOCK_WAIT_SECONDS):
        _ = claim_name(repo, name.text)
        try:
            _refuse_taken(repo, name.text)
            _ = _container(repo, container, create=True)
            path.mkdir()
        except BaseException:
            release_name(repo, name.text)
            raise
    try:
        _build_copy(repo, name, form, path, args)
    except BaseException:
        _undo_new(repo, form, path, name.text)
        raise
    evidence = _container(repo, EVIDENCE, create=True) / name.stem
    evidence.mkdir(exist_ok=True)
    print(path)
    _say(f"evidence: {evidence}")
    return 0


def _ssh_parts(url: str) -> tuple[str | None, str, int | None, str] | None:
    """Split ``ssh://[user@]host[:port]/path`` or scp-style ``[user@]host:path``: user, host, port, path."""
    if url.startswith("ssh://"):
        parts = urlsplit(url)
        if not parts.hostname:
            return None
        path = parts.path[1:] if parts.path.startswith("/~") else parts.path
        return parts.username, parts.hostname, parts.port, path
    if "://" in url or ":" not in url:
        return None
    login, _, path = url.partition(":")
    if "/" in login or not login or not path:
        return None
    user, _, host = login.rpartition("@")
    return user or None, host, None, path


def _checkout_matches(path: str, checkout: str, login: str) -> bool:
    """Return whether the remote ``path`` names the fleet ``checkout`` for the account ``login``.

    The path must be canonical (no ``.`` or ``..`` part, one trailing ``/`` at most); a
    ``~`` checkout matches ``~/...`` or ``login``'s own home (``/Users/<login>``,
    ``/home/<login>``), never another account's.
    """
    trimmed = path.removesuffix("/")
    parts = PurePosixPath(trimmed).parts
    if any(part in {".", ".."} for part in trimmed.split("/")) or "//" in trimmed:
        return False
    if trimmed == checkout:
        return True
    if not checkout.startswith("~/"):
        return False
    rest = PurePosixPath(checkout[2:]).parts
    return (
        PurePosixPath(trimmed).is_absolute()
        and len(parts) == len(rest) + 3
        and parts[1] in {"Users", "home"}
        and parts[2] == login
        and parts[3:] == rest
    )


def _fleet_rows(repo: Path) -> tuple[fleet.Machine, ...]:
    """Return the machine list of the checkout at ``repo`` (``fleet.machines``).

    Raises:
        WorkError: the list is missing, unreadable or broken (``fleet.MachineListError``).

    """
    try:
        return fleet.machines(repo)
    except fleet.MachineListError as error:
        raise WorkError(str(error)) from error


def is_parent_url(repo: Path, url: str) -> bool:
    """Return whether a remote ``url`` names this checkout: a local path, or a fleet one over SSH.

    Over SSH the host must reach a row of the machine list (``fleet.reached_as``: its
    name, an alias or its ``ssh`` host, any case or domain form), the port none or 22, the
    account the one ssh logs in to that host as (``fleet.ssh_user``: no user part, or
    that login) and the path that row's ``repo`` for that account.

    Raises:
        WorkError: the machine list is broken, or ssh cannot say which account it logs in
            to a host a row names as (``ssh -G`` failed).

    """
    ssh = _ssh_parts(url)
    if ssh is None:
        local = url.removeprefix("file://")
        return Path(local).expanduser().resolve() == repo.resolve()
    user, host, port, path = ssh
    if port not in {None, 22}:
        return False
    row = fleet.reached_as(host, _fleet_rows(repo))
    if row is None:
        return False
    login = fleet.ssh_user(host)
    if login is None:
        msg = (
            f"cannot tell which account ssh logs in to {host} as (`ssh -G {host}` gave no "
            f"user), so {url} cannot be checked against {row.name}'s checkout"
        )
        raise WorkError(msg)
    return user in {None, login} and _checkout_matches(path, row.repo, login)


def _adoptable(repo: Path, name: Name, path: Path) -> tuple[str, list[str]]:
    """Return the form of the copy at ``path`` and, for a clone, its remotes naming this checkout.

    Raises:
        WorkError: ``path`` is no adoptable copy.

    """
    if not path.is_dir():
        msg = f"{path} is not a folder"
        raise WorkError(msg)
    if path in {_abs(entry.path) for entry in worktree_entries(repo)}:
        inside = path.parent == _abs(work_dir(repo) / WORKTREES)
        if inside and (copy_hazard(repo, path, WORKTREES) or path.name != name.text):
            msg = f"a worktree under .work/worktrees is adopted as a real folder by its name {path.name!r}"
            raise WorkError(msg)
        return "worktree", []
    git = path / ".git"
    if not (_present(path, git) and git.is_dir()):
        msg = f"{path} is neither a worktree of {repo} nor a clone"
        raise WorkError(msg)
    real = path.parent == (work_dir(repo) / CLONES).resolve() and path.name == name.text
    if copy_hazard(repo, path, CLONES) or not real:
        msg = (
            f"a clone is adopted only as a real folder at .work/clones/{name.text}; "
            f"make a new copy for {path}"
        )
        raise WorkError(msg)
    parents = [
        remote
        for remote in _git(path, "remote").split()
        if is_parent_url(repo, _git(path, "remote", "get-url", remote).strip())
    ]
    if not parents:
        msg = (
            f"{path} has no remote pointing at {repo} (a local path, or a fleet checkout over SSH)"
        )
        raise WorkError(msg)
    return "clone", parents


def _register(
    repo: Path,
    name: Name,
    path: Path,
    form: str,
    parents: Sequence[str],
    args: _Args,
) -> None:
    """Write an adopted copy's note, fence its push, pin its ``HEAD``."""
    _refuse_taken(repo, name.text, path)
    if form == "worktree":
        _ensure_worktree_config(repo)
    head = _head(path)
    write_note(
        path,
        form,
        {
            "name": name.text,
            "form": form,
            "purpose": args.purpose,
            "owner": args.owner,
            "host": fleet.this_hostname(),
            "home": machine_id(),
            "start": head,
            "startshared": "false",
            "created": str(int(time.time())),
            "incarnation": secrets.token_hex(8),
            "adopted": "true",
            PINS_NOTE: f"{START_PIN}={head}",
        },
    )
    if form == "clone":
        for remote in parents:
            _ = _git(path, "remote", "set-url", "--push", remote, NO_PUSH)
        _apply_copy_config(path, form)
    _pin_start(repo, path, head, name.text)


def cmd_adopt(args: _Args) -> int:
    """Register a copy another tool made, in place."""
    repo = REPO_ROOT
    name = parse_name(args.name)
    refuse_control_text(args)
    path = _abs(Path(args.path).expanduser())
    form, parents = _adoptable(repo, name, path)
    note = _clone_note(path) if form == "clone" else _worktree_note(path, None)
    if note.get("name"):
        msg = f"{path} is already registered"
        raise WorkError(msg)
    _ = ensure_sentinel(repo)
    with stem_lock(repo, name.stem, STEM_LOCK_WAIT_SECONDS):
        _ = claim_name(repo, name.text)
        try:
            _register(repo, name, path, form, parents, args)
        except BaseException:
            release_name(repo, name.text)
            raise
    print(path)
    return 0


# --------------------------------------------------------------------------------------------
# list, save
# --------------------------------------------------------------------------------------------


def _state(copy: Copy) -> str:
    if copy.hazard is not None:
        return "unsafe"
    if copy.form == "pins":
        return "pins-only"
    if not copy.present:
        return "folder-gone"
    if not copy.healthy:
        return "broken"
    return "landed" if copy.note.get("landed") else "live"


def _listed_pins(repo: Path, copy: Copy, held: Mapping[str, str]) -> tuple[str, str, str]:
    """Return the copy's pins for ``list``: its own, foreign, and recorded but missing.

    ``pins.git`` says which pins exist (``held``, ``{leaf: commit}``); the note says which
    are the copy's (:func:`pin_belongs` against :func:`attributed_note`). Each part is a
    comma list, ``-`` when empty. A copy with no note (pins left alone) owns every pin.
    """
    if not copy.note:
        return ",".join(sorted(held)) or "-", "-", "-"
    note = attributed_note(repo, copy.note)
    own = sorted(leaf for leaf, commit in held.items() if pin_belongs(note, leaf, commit))
    foreign = sorted(foreign_pins(note, held))
    missing = sorted(leaf for leaf in recorded_pins(note) if leaf not in held)
    return ",".join(own) or "-", ",".join(foreign) or "-", ",".join(missing) or "-"


def cmd_list(args: _Args) -> int:
    """Print every known copy."""
    repo = args.repo
    all_pins = pins(repo)
    rows: list[dict[str, str]] = []
    for name, copy in sorted(discover(repo).items()):
        head = _head(copy.path) if copy.path is not None and copy.healthy else "-"
        own, foreign, missing = _listed_pins(repo, copy, all_pins.get(name, {}))
        rows.append(
            {
                "name": name,
                "form": copy.form,
                "state": _state(copy),
                "head": head[:12],
                "pins": own,
                "foreign": foreign,
                "missing": missing,
                "adopted": "yes" if copy.adopted else "no",
                "home": home_of(copy.note) if copy.note else "",
                "replica": "yes" if is_replica(copy.note) else "no",
                "purpose": copy.note.get("purpose", ""),
                "owner": copy.note.get("owner", ""),
                "path": str(copy.path) if copy.path is not None else "-",
            },
        )
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    for row in rows:
        print(
            f"{row['name']:<24} {row['form']:<8} {row['state']:<11} {row['head']:<12} "
            f"pins={row['pins']} "
            + (f"foreign-pins={row['foreign']} " if row["foreign"] != "-" else "")
            + (f"missing-pins={row['missing']} " if row["missing"] != "-" else "")
            + f"adopted={row['adopted']} "
            + (f"replica-of={row['home']} " if row["replica"] == "yes" else "")
            + (f"owner={shlex.quote(row['owner'])} " if row["owner"] else "")
            + row["path"]
            + (f"  # {row['purpose']}" if row["purpose"] else ""),
        )
    return 0


def save(repo: Path, copy: Copy) -> str | None:
    """Pin the copy's content as the next ``save-N``; return the ref, or ``None`` if nothing new."""
    copy_root = _live(copy)
    head = _head(copy_root)
    tree = content_tree(copy_root)
    if tree == _tree_of(copy_root, "HEAD"):
        if _at_durable_start(repo, copy, head):
            return None
        commit = head
    else:
        commit = _snapshot(copy_root, tree, head, f"work.py save of {copy.name}")
    ref = publish_next_save(repo, copy_root, commit, copy.name)
    record_pin(repo, copy_root, copy.form, ref.rpartition("/")[2], commit)
    write_note(copy_root, copy.form, {"savedat": str(time.time())})
    return ref


def cmd_save(args: _Args) -> int:
    """Pin a copy's uncommitted content."""
    copy = locate(args.repo, args.name)
    refuse_replica(copy, "save")
    ref = save(args.repo, copy)
    if ref is None:
        _say(f"{args.name}: nothing to save (content equals its start commit)")
        return 0
    print(ref)
    return 0


# --------------------------------------------------------------------------------------------
# land
# --------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Change:
    """One path a copy's patch touches: its new mode and blob, or ``None`` for a deletion."""

    path: str
    mode: str | None
    blob: str | None

    @property
    def state(self) -> tuple[str, str] | None:
        """Return ``(mode, blob)``, or ``None`` for a deletion."""
        return None if self.mode is None or self.blob is None else (self.mode, self.blob)


def copy_changes(copy_root: Path, base: str, tree: str) -> list[Change]:
    """Return every path that differs between ``base`` and ``tree`` in the copy."""
    raw = _git(copy_root, "diff-tree", "-r", "-z", "--no-renames", base, tree)
    fields = [field for field in raw.split("\0") if field]
    changes: list[Change] = []
    for header, path in zip(fields[0::2], fields[1::2], strict=True):
        _old_mode, new_mode, _old, new_blob, status = header.lstrip(":").split(" ")
        if status == "D":
            changes.append(Change(path, None, None))
        else:
            changes.append(Change(path, new_mode, new_blob))
    return changes


State = tuple[str, str] | None


def spelled_exactly(root: Path, path: str) -> bool:
    """Return whether ``path`` exists under ``root`` with exactly this spelling.

    A case-insensitive filesystem answers ``Case.txt`` for ``case.txt``; each component
    is looked up in its folder's listing instead. Only a folder that is not there
    (``FileNotFoundError``, ``NotADirectoryError``) reads as absent.

    Raises:
        WorkError: a folder on ``path`` is there but cannot be listed.

    """
    here = root
    for part in PurePosixPath(path).parts:
        try:
            names = {entry.name for entry in here.iterdir()}
        except (FileNotFoundError, NotADirectoryError):
            return False
        except OSError as error:
            raise _unreadable(root, here, error) from error
        if part not in names:
            return False
        here = here / part
    return True


def symlinked_folder(root: Path, path: str) -> str | None:
    """Return the first folder on ``path`` under ``root`` that is a symlink (``lstat``), else ``None``.

    Only the folders above ``path`` are read: ``path`` itself may be a symlink (a link
    blob is written as a link, never followed). A folder that is not there ends the walk.

    Raises:
        WorkError: a folder on ``path`` is there but cannot be looked into.

    """
    here = root
    for part in PurePosixPath(path).parts[:-1]:
        here = here / part
        mode = _mode(root, here)
        if mode is None:
            return None
        if stat.S_ISLNK(mode):
            return here.relative_to(root).as_posix()
    return None


def refuse_symlinked_folder(root: Path, path: str) -> None:
    """Refuse a ``path`` that a symlinked folder of the checkout at ``root`` would carry outside it.

    Raises:
        WorkError: a folder on ``path`` is a symlink, or cannot be looked into.

    """
    link = symlinked_folder(root, path)
    if link is not None:
        msg = (
            f"{path}: its folder {link} in the shared checkout is a symlink, so writing it "
            "would follow the link; nothing written (remove the link, or land it by hand)"
        )
        raise WorkError(msg)


def working_state(root: Path, path: str) -> State:
    """Return ``(mode, blob)`` of ``path`` as the working tree at ``root`` holds it, else ``None``.

    The bytes are hashed as they are (no index, no trust bit): a regular file or a symlink,
    found by its exact spelling; anything else (absent, a folder) is ``None``.

    Raises:
        WorkError: a folder on ``path`` is there but cannot be listed or looked into.

    """
    if not spelled_exactly(root, path):
        return None
    target = root / path
    mode = _mode(root, target)
    if mode is not None and stat.S_ISLNK(mode):
        link = str(target.readlink()).encode("utf-8", "surrogateescape")
        blob = _git_bytes(root, "hash-object", "--stdin", stdin=link).decode().strip()
        return ("120000", blob)
    if mode is None or not stat.S_ISREG(mode):
        return None
    mode = "100755" if os.access(target, os.X_OK) else "100644"
    return (mode, _git(root, "hash-object", f"--path={path}", "--", path).strip())


def _tree_states(root: Path, rev: str, paths: Sequence[str]) -> dict[str, State]:
    """Return each of ``paths`` as ``rev``'s tree holds it (``None`` when absent).

    Raises:
        WorkError: a path is a gitlink (a nested repository's commit).

    """
    states: dict[str, State] = dict.fromkeys(paths)
    if not paths:
        return states
    listing = _git(root, "ls-tree", "-z", "--full-tree", rev, "--", *paths)
    for record in (entry for entry in listing.split("\0") if entry):
        header, _, path = record.partition("\t")
        mode, kind, oid = header.split(" ")
        if kind == "commit":
            msg = f"{path} is a gitlink (a nested repository); land it by hand"
            raise WorkError(msg)
        if path in states:
            states[path] = (mode, oid)
    return states


def _index_states(
    root: Path,
    paths: Sequence[str],
    env: Mapping[str, str] | None = None,
) -> dict[str, State]:
    """Return each of ``paths`` as an index holds it at stage 0 (``None`` when absent)."""
    states: dict[str, State] = dict.fromkeys(paths)
    if not paths:
        return states
    listing = _git(root, "ls-files", "-s", "-z", "--", *paths, env=env)
    for record in (entry for entry in listing.split("\0") if entry):
        header, _, path = record.partition("\t")
        mode, blob, _stage = header.split(" ")
        if path in states:
            states[path] = (mode, blob)
    return states


def unclean_paths(repo: Path, head: str, paths: Sequence[str]) -> list[str]:
    """Return which of ``paths`` the shared tree holds otherwise than ``head``: bytes, mode or index.

    The working bytes are hashed directly, so an ``assume-unchanged`` or
    ``skip-worktree`` bit, which hides an edit from ``git status``, hides nothing here.
    """
    committed = _tree_states(repo, head, paths)
    staged = _index_states(repo, paths)
    return sorted(
        path
        for path in paths
        if working_state(repo, path) != committed[path] or staged[path] != committed[path]
    )


@dataclasses.dataclass(frozen=True)
class LandPlan:
    """What ``land`` would do, against which shared ``HEAD``, with which expected result."""

    patch: bytes
    applied: list[Change]
    skipped: list[str]
    tree: str
    merged: str
    base: str
    head: str
    before: dict[str, State]
    expected: dict[str, State]
    unheld: list[str]
    rows: dict[str, list[_sqlite_rows.RowChange]] = dataclasses.field(default_factory=dict)


def _branch(repo: Path) -> str:
    return _git_runner.run_git(repo, "symbolic-ref", "-q", "HEAD").stdout.strip()


def _refuse_off_main(repo: Path, copy_root: Path) -> tuple[str, str]:
    """Return ``(shared HEAD, copy HEAD)``, refusing a shared checkout off main or a committing copy.

    Raises:
        WorkError: the shared ``HEAD`` is not ``main`` or the copy's ``HEAD`` is not on it.

    """
    branch = _branch(repo)
    if branch != LANDING_BRANCH:
        msg = f"the shared checkout's HEAD is {branch or 'detached'}, not {LANDING_BRANCH}"
        raise WorkError(msg)
    head = _resolve_commit(repo, "HEAD")
    base = _head(copy_root)
    if not _git_ok(repo, "cat-file", "-e", f"{base}^{{commit}}") or not _is_ancestor(
        repo,
        base,
        head,
    ):
        msg = (
            f"the copy's HEAD {base[:12]} is not on the shared main: copies do not commit "
            "(their work lands as a patch); move the commits out (`git reset --soft` to the "
            "start pin in the copy) or rebase the copy onto main"
        )
        raise WorkError(msg)
    return head, base


def _pin_readable(store: Path, commit: str, *, parent: bool) -> bool:
    """Return whether ``pins.git`` holds ``commit`` and its trees (and its parent, when asked)."""
    return (
        _git_ok(store, "cat-file", "-e", f"{commit}^{{commit}}")
        and _git_ok(store, "ls-tree", "-r", "--full-tree", commit)
        and (not parent or _git_ok(store, "cat-file", "-e", f"{commit}^^{{commit}}"))
    )


def _landing_pins(repo: Path, copy: Copy) -> tuple[Path | None, str, str, list[str]]:
    """Return ``(pins.git, landed-copy, landed, problems)`` for the copy's landing pins.

    ``problems`` names each landing pin that is missing, not this copy's
    (:func:`pin_belongs` against the attributed note) or incomplete in ``pins.git``;
    ``pins.git`` is ``None`` when there is none. Nothing is fetched, and a pin that
    fails a check is reported, not raised.

    Raises:
        WorkError: ``pins.git``, its refs or a legacy copy's pins cannot be read
            (:func:`pin_store`, :func:`pins`, :func:`attributed_note`).

    """
    note = attributed_note(repo, copy.note)
    store = pin_store(repo)
    held = pins(repo).get(copy.name, {})
    merged, own = held.get(LANDED_PIN, ""), held.get(LANDED_COPY_PIN, "")
    problems = [
        _pin_ref(copy.name, leaf)
        for leaf, commit in ((LANDED_PIN, merged), (LANDED_COPY_PIN, own))
        if store is None
        or not commit
        or not pin_belongs(note, leaf, commit)
        or not _pin_readable(store, commit, parent=leaf == LANDED_PIN)
    ]
    return store, own, merged, problems


def _landing_wrote(store: Path, merged: str) -> set[str]:
    """Return the paths the landing pinned as ``merged`` wrote (its diff from its parent)."""
    names = _git(
        store,
        "diff-tree",
        "-r",
        "-z",
        "--no-renames",
        "--name-only",
        f"{merged}^",
        merged,
    )
    return {entry for entry in names.split("\0") if entry}


def own_landing_paths(
    repo: Path,
    copy: Copy,
    head: str,
    paths: Sequence[str],
) -> list[str]:
    """Return which of ``paths`` the shared tree holds exactly as the copy's last landing wrote them.

    Strict, since it only words a refusal: a path counts only where the ``landed`` pin
    wrote it (its diff from its parent), the shared working tree holds that pin's entry
    (bytes and mode; a deleted path counts while absent), the shared ``head`` still holds
    the pin parent's entry, so main has not moved there since, and the shared index holds
    either of those two entries (``land`` writes the working tree alone; a maintainer may
    have staged the landing). Bytes another writer made identical to the landing read
    as the copy's, and only the last landing counts: a path an earlier uncommitted
    landing wrote reads as another writer's. Only pins passing
    :func:`earlier_landing`'s checks count: a copy that never landed, or whose landing
    pins are missing, not its own or incomplete, owns none. A path that fails any test
    reads as another writer's.

    Raises:
        WorkError: ``pins.git`` or its refs cannot be read (:func:`_landing_pins`).

    """
    if not paths or not copy.note.get("landed"):
        return []
    store, _own, merged, problems = _landing_pins(repo, copy)
    if store is None or problems:
        return []
    wrote = _landing_wrote(store, merged)
    landed = _tree_states(store, merged, paths)
    before = _tree_states(store, f"{merged}^", paths)
    committed = _tree_states(repo, head, paths)
    staged = _index_states(repo, paths)
    return [
        path
        for path in paths
        if path in wrote
        and committed[path] == before[path]
        and staged[path] in (before[path], landed[path])
        and working_state(repo, path) == landed[path]
    ]


def earlier_landing(repo: Path, copy: Copy, copy_root: Path) -> tuple[Path, str, str] | None:
    """Return ``(pins.git, landed-copy, landed)`` for the copy's last landing, else ``None``.

    ``None`` only for a copy whose note records no landing. Only pins the note attributes
    to this copy count (:func:`pin_belongs`), so another copy's landing under the name is
    never a patch base. The ``landed-copy`` commit is fetched into the copy when its
    objects are not there, so its tree can be diffed.

    Raises:
        WorkError: the note records a landing but a landing pin is missing, is not this
            copy's, or ``pins.git`` lacks its objects: patching from the start instead
            could re-apply that landing over main without a word (``land --from-start``
            is the explicit choice).

    """
    if not copy.note.get("landed"):
        return None
    store, own, merged, problems = _landing_pins(repo, copy)
    if store is None or problems:
        verb = "is" if len(problems) == 1 else "are"
        msg = (
            f"{copy.name} records a landing, but {', '.join(problems)} {verb} missing, not "
            "this copy's, or incomplete in pins.git, so its work since that landing cannot be "
            "told apart; nothing applied (`land --from-start` patches from the copy's "
            "start, re-applying what main does not hold)"
        )
        raise WorkError(msg)
    if not _git_ok(copy_root, "cat-file", "-e", f"{own}^{{commit}}"):
        fetch_pinned(repo, copy_root, own)
    return store, own, merged


@dataclasses.dataclass(frozen=True)
class PatchBase:
    """The tree a landing's patch starts from, its changes, and what ``land`` must name."""

    since: str
    changes: list[Change]
    unheld: list[str]
    reset: list[str]


def patch_base(
    repo: Path,
    copy: Copy,
    copy_root: Path,
    tree: str,
    *,
    from_start: bool,
) -> PatchBase:
    """Return where the copy's patch to ``tree`` starts, and which changes it carries.

    A copy that never landed, or ``from_start``, patches from its ``HEAD``. After a
    landing the patch is the copy's work since then: ``landed-copy`` (the copy's whole
    content at its last landing, so every earlier landing and every path skipped as
    already there) to ``tree``; a copy whose note records a landing whose pins are
    missing, not its own or incomplete is refused (:func:`earlier_landing`), never
    patched from its start unasked. A path unchanged since that landing is never in the
    patch, whatever main did to it. A path counts as held as landed where it is as the
    copy held it then, or, for a path the last landing wrote, as that landing left it.
    ``unheld`` names the untouched paths the copy's landings changed from its ``HEAD``
    that neither the shared ``HEAD`` nor the shared working tree holds as landed, for
    ``land`` to note; ``reset`` names the patch's paths the copy put back at its
    ``HEAD`` entry (a ``reset --hard`` or ``checkout --`` in the copy) where its last
    landing held other content and the shared ``HEAD`` is not at that start entry
    either, which :func:`plan_landing` refuses rather than undo that landing on main
    (also where main reverted it and edited the file since: ``land --from-start``
    lands the rest and leaves those paths as main holds them). Where the shared
    ``HEAD`` is at the start too, the patch
    changes nothing there; a file the start lacks is never among them (neither command
    puts it back, so deleting a landed new file is ordinary work). Only the whole-path
    return to the start is guarded: an edit back to the start in part of a file lands
    like any edit.
    """
    base = _head(copy_root)
    landing = None if from_start else earlier_landing(repo, copy, copy_root)
    if landing is None:
        return PatchBase(base, copy_changes(copy_root, base, tree), [], [])
    store, own, merged = landing
    since = _tree_of(copy_root, own)
    changes = copy_changes(copy_root, since, tree)
    touched = [change.path for change in changes]
    earlier = sorted(
        change.path
        for change in copy_changes(copy_root, base, since)
        if change.path not in set(touched)
    )
    wrote = _landing_wrote(store, merged)
    paths = [*earlier, *touched]
    at_head = _tree_states(repo, "HEAD", paths)
    owned = _tree_states(store, own, paths)
    landed = _tree_states(store, merged, paths)
    started = _tree_states(copy_root, base, touched)

    def as_landed(path: str) -> set[State]:
        return {owned[path], *([landed[path]] if path in wrote else [])}

    unheld = [
        path
        for path in earlier
        if at_head[path] not in as_landed(path)
        and working_state(repo, path) not in as_landed(path)
    ]
    reset = [
        change.path
        for change in changes
        if started[change.path] is not None
        and change.state == started[change.path]
        and owned[change.path] != started[change.path]
        and at_head[change.path] != started[change.path]
    ]
    return PatchBase(since, changes, unheld, reset)


def _diff(
    copy_root: Path,
    base: str,
    tree: str,
    paths: Sequence[str],
) -> bytes:
    """Return the binary patch from ``base`` to ``tree`` over ``paths`` (empty for none)."""
    if not paths:
        return b""
    return _git_bytes(
        copy_root,
        "diff",
        "--binary",
        "--full-index",
        "--no-renames",
        "--no-color",
        "--no-ext-diff",
        base,
        tree,
        "--",
        *paths,
    )


def _not_applying(
    repo: Path,
    copy_root: Path,
    base: PatchBase,
    plan: tuple[str, Sequence[str], Mapping[str, str]],
) -> list[str]:
    """Return which of the paths' own patches do not apply onto the private index alone.

    ``plan`` is ``(tree, paths, env)``; ``--check`` writes nothing.
    """
    tree, paths, env = plan
    failing: list[str] = []
    for path in paths:
        try:
            _ = _git_bytes(
                repo,
                "apply",
                "--cached",
                "--check",
                "--whitespace=nowarn",
                "-",
                env=env,
                stdin=_diff(copy_root, base.since, tree, [path]),
            )
        except WorkError:
            failing.append(path)
    return failing


def _unclean_message(unclean: Sequence[str], own: Sequence[str]) -> str:
    """Return ``land``'s refusal for ``unclean`` paths, naming those that hold ``own`` landing.

    The copy's own uncommitted landing waits for the maintainer's commit; any other
    path is another writer's change, to commit or carve first.
    """
    mine = [path for path in unclean if path in own]
    other = [path for path in unclean if path not in own]
    parts: list[str] = []
    if mine:
        parts.append(
            f"the shared tree holds this copy's own uncommitted landing in {', '.join(mine)} "
            "(the maintainer commits it first)",
        )
    if other:
        parts.append(
            f"the shared tree holds other changes in {', '.join(other)} "
            "(land after they are committed, or carve)",
        )
    return f"{'; '.join(parts)}; nothing applied"


def plan_landing(
    repo: Path,
    copy: Copy,
    index: Path,
    *,
    from_start: bool = False,
) -> LandPlan:
    """Return the copy's landing plan; ``index`` receives the expected result.

    The patch starts where :func:`patch_base` says: the copy's ``HEAD`` before its first
    landing (or with ``from_start``), its ``landed-copy`` pin after one.

    Raises:
        WorkError: the shared ``HEAD`` is not ``main``, the copy's ``HEAD`` is not on it,
            the copy's landing pins cannot be trusted (:func:`earlier_landing`), a
            row-merged database has a live journal (:func:`refuse_live_journals`), the patch
            changes a database row main changed too or its schema (:func:`merge_database`),
            puts a path back at the copy's start where its last landing held other content
            and the shared ``HEAD`` is not at that start (``PatchBase.reset``), or touches a
            path the shared tree holds otherwise than its ``HEAD`` (paths holding the copy's
            own uncommitted landing, :func:`own_landing_paths`, are named apart from another
            writer's), or the patch does not apply onto the shared ``HEAD`` (the paths whose
            own patch does not apply are named).

    """
    copy_root = _live(copy)
    head, base = _refuse_off_main(repo, copy_root)
    refuse_live_journals(repo, copy_root)
    tree = content_tree(copy_root)
    # A write committed between the check and the capture sits in a journal the
    # captured file lacks: checked again, so a capture is used only if none appeared.
    refuse_live_journals(repo, copy_root)
    start = patch_base(repo, copy, copy_root, tree, from_start=from_start)
    if start.reset:
        msg = (
            f"the copy is back at its start in {', '.join(start.reset)}, where its last "
            "landing held other content, and main is not at that start; nothing applied "
            "(`land --from-start` lands the rest and leaves those paths as main holds them)"
        )
        raise WorkError(msg)
    changes = start.changes
    for change in changes:
        refuse_symlinked_folder(repo, change.path)
    applied = [change for change in changes if working_state(repo, change.path) != change.state]
    skipped = [change.path for change in changes if change not in applied]
    paths = [change.path for change in applied]
    unclean = unclean_paths(repo, head, paths)
    if unclean:
        own = own_landing_paths(repo, copy, head, unclean)
        raise WorkError(_unclean_message(unclean, own))
    env = {"GIT_INDEX_FILE": str(index)}
    _ = _git(repo, "read-tree", head, env=env)
    merged_rows = [change for change in applied if change.path in ROW_MERGED_PATHS]
    rows = {
        change.path: merge_database(repo, copy_root, (start.since, head, index), change)
        for change in merged_rows
    }
    for change in merged_rows:
        if not rows[change.path]:
            applied.remove(change)
            skipped.append(change.path)
    paths = [change.path for change in applied]
    patched = [path for path in paths if path not in ROW_MERGED_PATHS]
    patch = _diff(copy_root, start.since, tree, patched)
    if patch:
        try:
            _ = _git_bytes(
                repo,
                "apply",
                "--cached",
                "--whitespace=nowarn",
                "-",
                env=env,
                stdin=patch,
            )
        except WorkError as error:
            failing = _not_applying(repo, copy_root, start, (tree, patched, env))
            named = f" in {', '.join(failing)}" if failing else ""
            msg = (
                f"the copy's patch does not apply onto the shared HEAD {head[:12]}{named}; "
                f"nothing written ({error})"
            )
            raise WorkError(msg) from None
    merged = _git(repo, "write-tree", env=env).strip()
    patch += _diff(repo, head, merged, [path for path in paths if path in ROW_MERGED_PATHS])
    expected = _index_states(repo, paths, env)
    before = _tree_states(repo, head, paths)
    return LandPlan(
        patch,
        applied,
        skipped,
        tree,
        merged,
        base,
        head,
        before,
        expected,
        start.unheld,
        {path: changed for path, changed in rows.items() if changed},
    )


def refuse_live_journals(repo: Path, copy_root: Path) -> None:
    """Refuse a row-merged database, in the copy or the shared tree, with a live journal.

    A ``-wal`` or ``-journal`` file beside it holds committed rows its file does not, so
    the file git captures is not its content (``scripts/_sqlite_rows.py``).
    :func:`plan_landing` checks before and after capturing the copy's content, so a
    write committed in between refuses too; the sidecars are git-ignored, so none
    lands as a file of its own.

    Raises:
        WorkError: naming each such journal.

    """
    live = [
        journal
        for root in (copy_root, repo)
        for path in sorted(ROW_MERGED_PATHS)
        if (journal := _sqlite_rows.live_journal(root / path)) is not None
    ]
    if live:
        msg = (
            f"{', '.join(str(journal) for journal in live)} holds database writes its file "
            "does not (a connection is open or was not checkpointed); close it and run "
            "`PRAGMA wal_checkpoint(TRUNCATE)`; nothing applied"
        )
        raise WorkError(msg)


def merge_database(
    repo: Path,
    copy_root: Path,
    where: tuple[str, str, Path],
    change: Change,
) -> list[_sqlite_rows.RowChange]:
    """Stage in the private index the shared ``HEAD``'s database plus the copy's rows; return them.

    ``where`` is ``(since, head, index)``: the tree the copy's patch starts from, the
    shared ``HEAD`` and the private index. The result starts as a byte copy of the
    ``HEAD`` database and takes only the rows the copy changed since (``scripts/_sqlite_rows.py``),
    so nothing else the copy's file holds lands, freelist residue included. An empty
    list stages nothing: the copy changed no row.

    Raises:
        WorkError: the copy deleted the database or added it, the schemas differ, a row
            conflicts with main's, or the result fails a constraint or an integrity check.

    """
    since, head, index = where
    path = change.path
    started = _tree_states(copy_root, since, [path])[path]
    held = _tree_states(repo, head, [path])[path]
    if change.state is None or started is None or held is None:
        msg = f"{path} was added or deleted: carve it by hand (START.md), land the rest after"
        raise WorkError(msg)
    folder = Path(tempfile.mkdtemp(prefix="dsf-work-db-", dir=index.parent))
    try:
        files = {
            "base": (copy_root, started),
            "ours": (copy_root, change.state),
            "theirs": (repo, held),
        }
        for name, (root, (_mode, oid)) in files.items():
            _ = (folder / name).write_bytes(_git_bytes(root, "cat-file", "blob", oid))
        out = folder / "merged"
        try:
            rows = _sqlite_rows.merge(folder / "base", folder / "ours", folder / "theirs", out)
        except _sqlite_rows.MergeError as error:
            msg = f"{path}: {error}; nothing applied"
            raise WorkError(msg) from None
        if rows:
            blob = _git(repo, "hash-object", "-w", "--no-filters", str(out)).strip()
            _ = _git(
                repo,
                "update-index",
                "--add",
                "--cacheinfo",
                f"{held[0]},{blob},{path}",
                env={"GIT_INDEX_FILE": str(index)},
            )
        return rows
    finally:
        shutil.rmtree(folder, ignore_errors=True)


def rows_summary(rows: Sequence[_sqlite_rows.RowChange]) -> str:
    """Return each table's changed rows as ``table: update 463, insert 901``."""
    tables: dict[str, list[_sqlite_rows.RowChange]] = {}
    for row in rows:
        tables.setdefault(row.table, []).append(row)
    parts: list[str] = []
    for table, changed in sorted(tables.items()):
        kinds = ", ".join(f"{row.kind} {row.key}" for row in changed)
        parts.append(f"{table}: {kinds}")
    return "; ".join(parts)


@contextlib.contextmanager
def land_lock(repo: Path) -> Generator[None, None, None]:
    """Hold an exclusive lock on ``.work/land.lock`` for one ``land`` (or ``repair``).

    The file stays; the lock is the kernel's (``flock``, ``msvcrt.locking`` on Windows),
    so it is released however its holder ends, and nothing ever takes it over.

    Raises:
        WorkError: another process holds it.

    """
    _ = ensure_sentinel(repo)
    lock = work_dir(repo) / LAND_LOCK
    check_layout(repo)
    descriptor = os.open(lock, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            locked = _locks.try_lock(descriptor)
        except OSError as error:
            msg = f"cannot lock {lock}: {error}"
            raise WorkError(msg) from error
        if not locked:
            msg = f"another land holds {lock}; wait for it"
            raise WorkError(msg)
        yield
    finally:
        os.close(descriptor)


def _blob_bytes(repo: Path, path: str, state: tuple[str, str]) -> bytes:
    """Return what the working file for ``state`` holds: the smudged blob, or a link target."""
    mode, oid = state
    if mode == "120000":
        return _git_bytes(repo, "cat-file", "blob", oid)
    return _git_bytes(repo, "cat-file", "--filters", f"--path={path}", oid)


def _prune_empty_parents(repo: Path, folder: Path) -> None:
    """Remove the empty folders a deletion left, up to (never including) ``repo``."""
    while folder != repo and _is_within(folder, repo):
        try:
            folder.rmdir()
        except OSError:
            return
        folder = folder.parent


def put_path(
    repo: Path,
    path: str,
    state: State,
    preimage: State,
) -> bool:
    """Make ``path`` hold ``state`` only while it still holds ``preimage``; return whether it did.

    The new bytes go to a temporary file beside the target first; the target is
    re-hashed right before the one ``os.replace`` (or ``unlink``) that publishes the
    change, so an edit another session made at any earlier moment is never overwritten.
    The window between that last hash and the replace stays open: no lock binds a
    plain editor. A symlinked folder on ``path`` is refused before anything is written
    and again right before the replace or unlink, so the write never follows a link
    out of the checkout; ``path`` itself as a symlink is replaced as a link.

    Raises:
        WorkError: a folder on ``path`` is a symlink, or cannot be looked into.

    """
    target = repo / path
    refuse_symlinked_folder(repo, path)
    if working_state(repo, path) != preimage:
        return False
    if state is None:
        refuse_symlinked_folder(repo, path)
        target.unlink(missing_ok=True)
        _prune_empty_parents(repo, target.parent)
        return True
    target.parent.mkdir(parents=True, exist_ok=True)
    refuse_symlinked_folder(repo, path)
    staged = target.parent / f".{target.name}.dsf-work-{_token()}"
    data = _blob_bytes(repo, path, state)
    try:
        if state[0] == "120000":
            staged.symlink_to(data.decode("utf-8", "surrogateescape"))
        else:
            _ = staged.write_bytes(data)
            staged.chmod(0o755 if state[0] == "100755" else 0o644)
        if working_state(repo, path) != preimage:
            return False
        refuse_symlinked_folder(repo, path)
        if _is_kind(repo, target, stat.S_ISDIR):
            target.rmdir()
        _ = staged.replace(target)
    finally:
        if _present(repo, staged):
            staged.unlink()
    return True


def _journal(repo: Path) -> Path:
    return work_dir(repo) / LAND_JOURNAL


def _store_journal(repo: Path, head: object, entries: Mapping[str, object]) -> None:
    """Publish the journal for ``entries`` (path to its state before and after) with one rename."""
    journal = _journal(repo)
    staged = journal.with_name(f".{journal.name}.{_token()}")
    _ = staged.write_text(json.dumps({"head": head, "paths": entries}), encoding="utf-8")
    _ = staged.replace(journal)


def _write_journal(repo: Path, plan: LandPlan) -> None:
    """Record every touched path's state before and after, atomically, before writing any."""
    entries = {
        path: {"before": plan.before[path], "after": plan.expected[path]} for path in plan.expected
    }
    _store_journal(repo, plan.head, entries)


def _journal_state(value: object) -> State:
    if fleet.is_json_array(value) and len(value) == 2:
        mode, oid = value
        if isinstance(mode, str) and isinstance(oid, str):
            return (mode, oid)
    return None


@dataclasses.dataclass(frozen=True)
class Recovery:
    """What undoing a journaled landing left: another writer's paths, and paths it could not undo."""

    foreign: tuple[str, ...] = ()
    stuck: tuple[str, ...] = ()

    def summary(self) -> str | None:
        """Return what was left undone, ``None`` when the undo was complete."""
        parts: list[str] = []
        if self.foreign:
            parts.append(f"{', '.join(self.foreign)}, which another writer changed")
        if self.stuck:
            parts.append(f"{'; '.join(self.stuck)}; {JOURNAL_KEPT}")
        return "; ".join(parts) or None


def _inside(path: str) -> bool:
    """Return whether ``path`` is a normalized relative path that stays inside the checkout."""
    pure = PurePosixPath(path)
    return (
        bool(path)
        and not pure.is_absolute()
        and not PureWindowsPath(path).drive
        and str(pure) == path
        and not any(part in {"", ".", ".."} for part in pure.parts)
    )


def recover_landing(repo: Path) -> Recovery:
    """Undo a landing the journal shows unfinished; return what it had to leave.

    Each path holding what that landing wrote goes back to its state before; a path
    holding its state before needs nothing; any other bytes are another writer's and
    stay. A path that cannot be read or written stays unresolved and keeps its entry:
    the journal is rewritten to hold only those, and deleted once none is left.

    Raises:
        WorkError: the journal names a path outside the checkout (absolute, holding ``..``
            or not normalized); nothing is written and the journal is kept for a human.

    """
    journal = _journal(repo)
    if not _is_kind(repo, journal, stat.S_ISREG):
        return Recovery()
    document = _loads(journal.read_text(encoding="utf-8"))
    entries = document.get("paths") if fleet.is_json_object(document) else None
    hostile = sorted(
        path for path in (entries if fleet.is_json_object(entries) else {}) if not _inside(path)
    )
    if hostile:
        msg = (
            f"the land journal names a path outside the checkout: {', '.join(hostile)}; "
            f"fix or remove {journal} by hand"
        )
        raise WorkError(msg)
    foreign: list[str] = []
    stuck: list[str] = []
    unresolved: dict[str, object] = {}
    for path, entry in sorted(entries.items()) if fleet.is_json_object(entries) else []:
        if not fleet.is_json_object(entry):
            continue
        before, after = _journal_state(entry.get("before")), _journal_state(entry.get("after"))
        try:
            current = working_state(repo, path)
            if current == before:
                continue
            if current != after or not put_path(repo, path, before, after):
                foreign.append(path)
        except WorkError as error:
            stuck.append(f"{path}: {error}")
            unresolved[path] = entry
        except OSError as error:
            stuck.append(f"cannot write {path}: {error.strerror or error}")
            unresolved[path] = entry
    if unresolved:
        head = document.get("head") if fleet.is_json_object(document) else None
        _store_journal(repo, head, unresolved)
    else:
        journal.unlink()
    return Recovery(tuple(foreign), tuple(stuck))


def _drifted(repo: Path, plan: LandPlan, states: Mapping[str, State]) -> list[str]:
    """Return what no longer matches: the branch, ``HEAD``, or a path versus ``states``."""
    drift: list[str] = []
    if _branch(repo) != LANDING_BRANCH:
        drift.append("the shared checkout left main")
    if _resolve_commit(repo, "HEAD") != plan.head:
        drift.append("the shared HEAD moved")
    drift.extend(
        f"{path} changed" for path, state in states.items() if working_state(repo, path) != state
    )
    return drift


def _put_all(repo: Path, plan: LandPlan) -> None:
    """Write every expected path (deletions first), then check the checkout did not move.

    Raises:
        WorkError: a path changed under the landing, or the checkout moved while it wrote.

    """
    order = sorted(plan.expected, key=lambda path: (plan.expected[path] is not None, path))
    for path in order:
        if not put_path(repo, path, plan.expected[path], plan.before[path]):
            msg = f"{path} changed under the landing"
            raise WorkError(msg)
    drift = _drifted(repo, plan, plan.expected)
    if drift:
        msg = "; ".join(drift)
        raise WorkError(msg)


def _write_landing(repo: Path, plan: LandPlan) -> None:
    """Write the landing, journaled first; undo all of it on any failure or interruption.

    Raises:
        WorkError: :func:`_put_all` refused; every path holding what this landing wrote is
            put back, and a path another writer changed meanwhile is named and kept.

    """
    _write_journal(repo, plan)
    try:
        _put_all(repo, plan)
    except (WorkError, OSError) as error:
        recovery = recover_landing(repo)
        kept = (
            f"; another writer's bytes kept untouched in {', '.join(recovery.foreign)}"
            if recovery.foreign
            else ""
        )
        stuck = (
            f"; not undone: {'; '.join(recovery.stuck)}; {JOURNAL_KEPT}" if recovery.stuck else ""
        )
        msg = f"rolled back: {error} while landing{kept}{stuck}"
        raise WorkError(msg) from None
    except BaseException:
        _ = recover_landing(repo)
        raise
    _journal(repo).unlink()


def cmd_land(args: _Args) -> int:
    """Apply a copy's content to the shared working tree, all or nothing."""
    repo = REPO_ROOT
    with land_lock(repo):
        if _journal(repo).is_file():
            _say("undoing an interrupted landing from its journal first")
        left = recover_landing(repo).summary()
        if left is not None:
            msg = f"an interrupted landing was undone except {left}"
            raise WorkError(msg)
        copy = locate(repo, args.name)
        index = _git_path(repo, f"dsf-work-land-{_token()}")
        try:
            return _land(repo, copy, args, index)
        finally:
            index.unlink(missing_ok=True)


def _land(
    repo: Path,
    copy: Copy,
    args: _Args,
    index: Path,
) -> int:
    refuse_replica(copy, "land")
    plan = plan_landing(repo, copy, index, from_start=args.from_start)
    if args.patch:
        _ = Path(args.patch).write_bytes(plan.patch)
    if plan.unheld:
        _say(
            f"not re-applied: main does not hold the copy's earlier landing of "
            f"{', '.join(plan.unheld)} (reverted, never committed, or changed since), and "
            "the copy has not changed it since; `land --from-start` patches from the copy's "
            "start to land it again",
        )
    for path in plan.skipped:
        _say(f"already there: {path}")
    if not plan.applied:
        _say(f"{copy.name}: nothing to land")
        return 0
    if args.dry_run:
        for change in plan.applied:
            print(f"would land: {change.path}")
            if change.path in plan.rows:
                print(f"  rows: {rows_summary(plan.rows[change.path])}")
        return 0
    drift = _drifted(repo, plan, plan.before)
    if drift:
        msg = f"nothing written: {'; '.join(drift)} since the landing was planned"
        raise WorkError(msg)
    _write_landing(repo, plan)
    _pin_landing(repo, copy, plan)
    for change in plan.applied:
        print(f"landed: {change.path}")
        if change.path in plan.rows:
            print(f"  rows: {rows_summary(plan.rows[change.path])}")
    return 0


def _pin_landing(repo: Path, copy: Copy, plan: LandPlan) -> None:
    """Pin what landed: the merged result on the shared ``HEAD``, and the copy's own content."""
    copy_root = _live(copy)
    leaves = pins(repo).get(copy.name, {})
    merged = _snapshot(repo, plan.merged, plan.head, f"work.py landing of {copy.name}")
    own = _snapshot(copy_root, plan.tree, plan.base, f"work.py content of {copy.name} at landing")
    for source, commit, leaf in ((repo, merged, LANDED_PIN), (copy_root, own, LANDED_COPY_PIN)):
        if not publish_pin(repo, source, commit, copy.name, leaf, replacing=leaves.get(leaf, "")):
            _say(f"{_pin_ref(copy.name, leaf)} moved meanwhile; the copy keeps what landed")
            continue
        record_pin(repo, copy_root, copy.form, leaf, commit)
    write_note(
        copy_root,
        copy.form,
        {"landed": plan.head, "landedtree": plan.tree, "landedat": str(time.time())},
    )


# --------------------------------------------------------------------------------------------
# rm, gc, repair, run
# --------------------------------------------------------------------------------------------


def _trash_path(repo: Path, name: str, *, kept: bool = False) -> Path:
    """Return a fresh path in ``.work/trash`` for the copy ``name``.

    ``<name>-<seconds>-<pid>`` while ``rm`` deletes it; ``<name>-<seconds>-kept`` for a copy
    kept there for :data:`TRASH_RETENTION_SECONDS`.

    Raises:
        WorkError: ``name`` breaks the name grammar (it would name a path outside the trash).

    """
    _ = parse_name(name)
    trash = _container(repo, TRASH, create=True)
    return trash / f"{name}-{int(time.time())}-{KEPT_TRASH if kept else os.getpid()}"


def remove(
    repo: Path,
    copy: Copy,
    *,
    discard: bool,
    drop_saves: bool,
    keep_in_trash: bool = False,
) -> dict[str, str]:
    """Remove ``copy`` after every safety check (see :func:`removal_refusals`).

    Drops its ``start`` pin, and with ``drop_saves`` every other pin under the name, but only
    the pins its note attributes to it (:func:`pin_belongs`): a pin another copy left under
    the name (an earlier copy's, or one a fleet sync carried in) is kept and returned
    (``{leaf: commit}``) for the caller to name. A name holding pins alone has no note: its
    ``rm`` is the request to drop them, and drops them all.

    On the copy's home (its note no replica, its ``home`` this machine) a tombstone records
    the removal for ``docs/fleet/scripts/fleet_sync.py`` to carry. A replica
    (``rm --discard``, or the fleet sync's removal) and ``keep_in_trash`` leave the folder
    in ``.work/trash`` for ``gc`` to delete once :data:`TRASH_RETENTION_SECONDS` pass: a
    replica may be the last copy of its work.

    Raises:
        WorkError: a check refused (the message lists every reason), or the copy, moved
            to the trash, could not be deleted there.

    """
    reasons = removal_refusals(repo, copy, discard=discard)
    if reasons:
        msg = f"{copy.name}: not removed: " + "; ".join(reasons)
        raise WorkError(msg)
    undeleted: str | None = None
    keep_in_trash = keep_in_trash or is_replica(copy.note)
    if copy.path is not None and copy.present:
        trash = _trash_path(repo, copy.name, kept=keep_in_trash)
        try:
            _ = copy.path.rename(trash)
        except OSError as error:
            msg = f"{copy.name}: cannot move it to {trash} ({error}); is a process holding it?"
            raise WorkError(msg) from None
        if copy.form == "worktree":
            # Unlocked only once moved: a refused move leaves the worktree locked as it was.
            # git finds the worktree by the path its metadata records, so the moved folder
            # is still the one unlocked.
            _ = _git_runner.run_git(repo, "worktree", "unlock", str(copy.path))
        try:
            if not keep_in_trash:
                delete_tree(trash)
        except OSError as error:
            undeleted = (
                f"cannot delete {trash}: {error.strerror or error}; it stays in .work/trash"
            )
    wanted = {
        leaf: sha
        for leaf, sha in pins(repo).get(copy.name, {}).items()
        if leaf == START_PIN or drop_saves
    }
    kept = {} if copy.form == "pins" else foreign_pins(attributed_note(repo, copy.note), wanted)
    dropped = {leaf: sha for leaf, sha in wanted.items() if leaf not in kept}
    _bury(repo, copy, dropped, saves_dropped=drop_saves)
    if copy.admin is not None and _is_kind(copy.admin.parent, copy.admin, stat.S_ISDIR):
        delete_tree(copy.admin)
    for leaf, sha in dropped.items():
        drop_pin(repo, copy.name, leaf, sha)
    buried = drop_buried_pins(repo, copy.name)
    kept = {leaf: sha for leaf, sha in kept.items() if leaf not in buried}
    release_name(repo, copy.name)
    if undeleted is not None:
        msg = f"{copy.name}: removed, but {undeleted}" + kept_pins_note(copy.name, kept)
        raise WorkError(msg)
    return kept


def kept_pins_note(name: str, kept: Mapping[str, str]) -> str:
    """Return the sentence naming the pins a removal kept as not provably its own, ``""`` for none."""
    if not kept:
        return ""
    listed = ", ".join(f"{leaf} {sha[:12]}" for leaf, sha in sorted(kept.items()))
    return (
        f"; kept pins this copy cannot prove are its own: {listed}; check them, then "
        f"`work.py rm {name} --drop-saves` drops them"
    )


def cmd_rm(args: _Args) -> int:
    """Remove one copy."""
    repo = REPO_ROOT
    _ = ensure_sentinel(repo)
    copy = locate(repo, args.name)
    if (
        copy.adopted
        and copy.path is not None
        and not _is_within(copy.path.resolve(), work_dir(repo).resolve())
    ):
        msg = f"{copy.name} is a harness copy at {copy.path}; its harness removes it, not this script"
        raise WorkError(msg)
    stem = stem_of(copy.name)
    if args.evidence:
        refuse_replica_evidence(repo, stem, [copy])
    if not args.discard:
        refuse_replica(copy, "remove (or `rm --discard`, which drops the replica alone)")
    with evidence_locks(repo, stem) if args.evidence else contextlib.nullcontext():
        removed = removed_copy(repo, copy) if args.evidence else None
        kept = remove(repo, copy, discard=args.discard, drop_saves=args.drop_saves)
        days = TRASH_RETENTION_SECONDS // 86400
        trashed = f" (a replica: kept in .work/trash for {days} days)"
        trashed = trashed if is_replica(copy.note) else ""
        print(f"removed {copy.name}{trashed}{kept_pins_note(copy.name, kept)}")
        if removed is not None:
            _rm_evidence(repo, stem, removed)
    return 0


def _rm_evidence(repo: Path, stem: str, removed: RemovedCopy) -> None:
    """Delete the stem's evidence fleet-wide after ``rm --evidence`` unless another name uses it.

    Raises:
        WorkError: the folder could not be moved to the trash (:func:`discard_evidence`).

    """
    evidence = work_dir(repo) / EVIDENCE / stem
    users = evidence_users(repo, stem, removed=removed)
    if users:
        _say(f"evidence {evidence} kept: {', '.join(users)} still use it")
    elif evidence.is_dir() and copy_hazard(repo, evidence, EVIDENCE) is None:
        grave, entry = discard_evidence(repo, stem, removed=removed)
        print(_discarded(grave, entry))


def refuse_replica_evidence(repo: Path, stem: str, copies: Iterable[Copy]) -> None:
    """Refuse deleting ``stem``'s evidence while this machine holds its copies as replicas alone.

    ``copies`` are the stem's users here. A name holding pins alone counts as a replica
    unless this machine published its pins (:func:`pins_published_here`): the pins a
    replica's ``rm --discard`` left, or a sync carried in, are another home's. Evidence is
    deleted fleet-wide from the copy's home: a replica's ``whole`` record would trash files
    the home still writes, and a home skips a stem its copy uses on every full sync.

    Raises:
        WorkError: every copy among ``copies`` (one at least) is a replica; nothing is removed.

    """
    held = [
        copy for copy in copies if copy.form != "pins" or not pins_published_here(repo, copy.name)
    ]
    replicas = [copy for copy in held if copy.form == "pins" or is_replica(copy.note)]
    if not replicas or len(replicas) < len(held):
        return
    here = machine_id()
    graves = [grave for grave in tombstones(repo) if not grave.identity.startswith("pins@")]
    homes = {home_of(copy.note) for copy in replicas if copy.form != "pins"}
    for copy in replicas:
        if copy.form == "pins":
            named = {canonical(grave.home) for grave in graves if grave.name == copy.name}
            homes |= (named - {here}) or {"another machine"}
    names = ", ".join(copy.name for copy in replicas)
    msg = (
        f"evidence {stem}: {names} here is a replica of {', '.join(sorted(homes))}'s copy; "
        "evidence is deleted from the copy's home: run it there"
    )
    raise WorkError(msg)


def pins_published_here(repo: Path, name: str) -> bool:
    """Return whether this machine published the pins the name holding them alone keeps.

    The copy's note, which recorded them, went with the copy; what remains is the tombstone
    its home's ``rm`` or ``gc`` left (a replica's removal leaves none). One whose home and
    remover are this machine, of a copy (not ``pins@``) and made no earlier than every pin
    under the name, vouches for them: a later copy reusing the name pins only after it.
    """
    here = machine_id()
    store = pin_store(repo)
    if store is None:
        return False
    listing = _git(
        store,
        "for-each-ref",
        "--format=%(committerdate:unix)",
        f"{PIN_PREFIX}{name}/",
    )
    stamps = [int(stamp) for stamp in listing.split() if stamp.isdigit()]
    return any(
        grave.name == name
        and not grave.identity.startswith("pins@")
        and canonical(grave.home) == here
        and canonical(grave.removed_by) == here
        and all(stamp <= grave.removed_at for stamp in stamps)
        for grave in tombstones(repo)
    )


def _discarded(grave: EvidenceTombstone, entry: Path | None) -> str:
    """Return the line naming an evidence deletion's record and its trash entry."""
    days = TRASH_RETENTION_SECONDS // 86400
    moved = f", moved to .work/trash/{entry.name} for {days} days" if entry is not None else ""
    return (
        f"evidence {grave.stem}: {len(grave.files)} files recorded in "
        f".work/{EVIDENCE_GRAVES}/{grave.file_name}{moved}; the fleet sync deletes them everywhere"
    )


def cmd_evidence_rm(args: _Args) -> int:
    """Delete one stem's evidence (or some of its files) on every fleet machine."""
    repo = REPO_ROOT
    _ = ensure_sentinel(repo)
    stem = args.name
    if not valid_stem(stem):
        msg = f"{stem!r} is no evidence folder name"
        raise WorkError(msg)
    if args.file and args.adopt_missing:
        msg = "--file and --adopt-missing exclude each other"
        raise WorkError(msg)
    root = work_dir(repo) / EVIDENCE
    folder = root / stem
    hazard = copy_hazard(repo, folder, EVIDENCE)
    if hazard is not None:
        msg = f"evidence {stem}: {hazard}; never touched"
        raise WorkError(msg)
    with contextlib.nullcontext() if args.dry_run else evidence_locks(repo, stem):
        users = evidence_users(repo, stem)
        if users:
            found = discover(repo)
            refuse_replica_evidence(repo, stem, [found[name] for name in users if name in found])
            msg = (
                f"evidence {stem}: {', '.join(users)} still use it (a name holding pins alone "
                "too); `work.py rm <name> --evidence` removes a copy with its evidence"
            )
            raise WorkError(msg)
        if args.adopt_missing:
            return _adopt_missing(repo, stem, dry_run=args.dry_run)
        if not _is_kind(root, folder, stat.S_ISDIR):
            msg = f"no evidence folder {folder}"
            raise WorkError(msg)
        if args.file:
            return _evidence_rm_files(repo, stem, folder, args.file, dry_run=args.dry_run)
        if args.dry_run:
            print(f"would record and trash evidence {stem}: {len(evidence_files(folder))} files")
            return 0
        grave, entry = discard_evidence(repo, stem)
        print(_discarded(grave, entry))
    return 0


def _evidence_rm_files(
    repo: Path,
    stem: str,
    folder: Path,
    rels: Sequence[str],
    *,
    dry_run: bool,
) -> int:
    """Record the files ``rels`` of ``folder`` in a tombstone (``whole`` false), then trash them.

    Raises:
        WorkError: a path is not canonical, leaves the folder or names no file; or a file
            changed while it moved.

    """
    states: dict[str, tuple[int, int]] = {}
    for rel in rels:
        if not evidence_rel(rel):
            msg = f"{rel!r} is no plain relative path inside evidence {stem}"
            raise WorkError(msg)
        path = inside(folder, rel)
        mode = _mode(folder, path)
        if mode is None or stat.S_ISDIR(mode):
            msg = f"evidence {stem} holds no file {rel}"
            raise WorkError(msg)
        states[rel] = file_state(path.lstat())
    if dry_run:
        print(f"would record and trash {len(states)} files of evidence {stem}")
        return 0
    here = machine_id()
    files = tuple(sorted((rel, size, mtime) for rel, (size, mtime) in states.items()))
    grave = EvidenceTombstone(stem, here, time.time(), here, files, whole=False)
    _ = write_evidence_tombstone(repo, grave)
    made: list[Path] = []

    def entry() -> Path:
        if not made:
            made.append(evidence_trash_entry(repo, stem, make=True))
        return made[0]

    changed = [
        rel
        for rel, state in sorted(states.items())
        if move_evidence_file(folder, rel, state, entry) != "moved"
    ]
    print(_discarded(grave, made[0] if made else None))
    if changed:
        msg = f"evidence {stem}: changed while it moved, kept here: {', '.join(changed)}"
        raise WorkError(msg)
    return 0


def _adopt_missing(repo: Path, stem: str, *, dry_run: bool) -> int:
    """Record the files of ``stem`` the peer manifests list and this machine lacks (``rm -rf``).

    One tombstone per peer manifest holding such files, each with that manifest's states (the
    states last synced with that peer); ``whole`` when the stem folder itself is gone. The
    caller holds ``.work/fleet.lock`` unless ``dry_run``.

    Raises:
        WorkError: ``.work/evidence`` itself is missing (a wipe, not a deletion), or no
            manifest lists a file missing here.

    """
    root = work_dir(repo) / EVIDENCE
    if not _is_kind(work_dir(repo), root, stat.S_ISDIR):
        msg = f"{root} is missing: a wiped evidence root is no deletion; nothing adopted"
        raise WorkError(msg)
    folder = root / stem
    gone = not _present(root, folder)
    local = {} if gone else evidence_files(folder)
    found: list[dict[str, tuple[int, int]]] = []
    fleet_folder = work_dir(repo) / FLEET
    for manifest in sorted(fleet_folder.glob("evidence-*.json")) if fleet_folder.is_dir() else []:
        listed = evidence_manifest(manifest).get(stem, {})
        missing = {rel: state for rel, state in listed.items() if rel not in local}
        if missing and all(evidence_rel(rel) for rel in missing):
            found.append(missing)
    if not found:
        msg = f"evidence {stem}: no peer manifest lists a file missing here; nothing adopted"
        raise WorkError(msg)
    if dry_run:
        count = len({rel for missing in found for rel in missing})
        print(f"would record {count} files of evidence {stem} removed by hand")
        return 0
    here = machine_id()
    removed_at = time.time()
    for missing in found:
        files = tuple(sorted((rel, size, mtime) for rel, (size, mtime) in missing.items()))
        grave = EvidenceTombstone(stem, here, removed_at, here, files, whole=gone)
        _ = write_evidence_tombstone(repo, grave)
        print(_discarded(grave, None))
    return 0


def evidence_entry_stem(name: str) -> str | None:
    """Return the stem an ``evidence-<stem>-<seconds>-kept`` trash entry name holds, else ``None``."""
    prefix, suffix = "evidence-", f"-{KEPT_TRASH}"
    if not name.startswith(prefix) or not name.endswith(suffix):
        return None
    stem, _, seconds = name[len(prefix) : -len(suffix)].rpartition("-")
    return stem if seconds.isdigit() and valid_stem(stem) else None


def _restore_entry(repo: Path, text: str) -> tuple[Path, str]:
    """Return the evidence trash entry ``text`` names (an entry, or a stem with one) and its stem.

    Raises:
        WorkError: ``text`` names no entry, or a stem with none or several.

    """
    trash = _container(repo, TRASH)
    stem = evidence_entry_stem(text)
    if stem is not None and _is_kind(trash, trash / text, stat.S_ISDIR):
        return trash / text, stem
    if not valid_stem(text):
        msg = f"{text!r} is no evidence trash entry or stem"
        raise WorkError(msg)
    listed = sorted(trash.iterdir()) if _is_kind(work_dir(repo), trash, stat.S_ISDIR) else []
    entries = [
        entry
        for entry in listed
        if evidence_entry_stem(entry.name) == text and _is_kind(trash, entry, stat.S_ISDIR)
    ]
    if not entries:
        msg = f"no .work/trash/evidence-{text}-<seconds>-{KEPT_TRASH} entry to restore"
        raise WorkError(msg)
    if len(entries) > 1:
        names = ", ".join(entry.name for entry in entries)
        msg = f"evidence {text} has several trash entries ({names}); name the one to restore"
        raise WorkError(msg)
    return entries[0], text


def _entry_files(entry: Path) -> list[str]:
    """Return the relative path of every file (a link included, never followed) under ``entry``."""
    files: list[str] = []
    folders = [entry]
    while folders:
        folder = folders.pop()
        for child in sorted(folder.iterdir()):
            if _is_kind(folder, child, stat.S_ISDIR):
                folders.append(child)
            else:
                files.append(child.relative_to(entry).as_posix())
    return sorted(files)


def _fresh_mtime(size: int, buried: Collection[tuple[int, int]]) -> int:
    """Return the current second, or the first later one, at which ``size`` is no buried state."""
    stamp = int(time.time())
    while (size, stamp) in buried:
        stamp += 1
    return stamp


def cmd_evidence_restore(args: _Args) -> int:
    """Move one evidence trash entry's files back, each with a fresh mtime no record holds."""
    repo = REPO_ROOT
    _ = ensure_sentinel(repo)
    entry, stem = _restore_entry(repo, args.name)
    root = work_dir(repo) / EVIDENCE
    folder = root / stem
    hazard = copy_hazard(repo, folder, EVIDENCE)
    if hazard is not None:
        msg = f"evidence {stem}: {hazard}; nothing restored"
        raise WorkError(msg)
    with contextlib.nullcontext() if args.dry_run else fleet_lock(repo):
        rels = _entry_files(entry)
        taken = [rel for rel in rels if _present(folder, inside(folder, rel))]
        if taken:
            msg = (
                f"evidence {stem} already holds {', '.join(taken)}; nothing restored from "
                f".work/trash/{entry.name}"
            )
            raise WorkError(msg)
        if args.dry_run:
            print(
                f"would restore {len(rels)} files of evidence {stem} from .work/trash/{entry.name}",
            )
            return 0
        buried: dict[str, set[tuple[int, int]]] = {}
        for grave in evidence_tombstones(repo):
            if grave.stem == stem:
                for rel, size, mtime in grave.files:
                    buried.setdefault(rel, set()).add((size, mtime))
        lutime = os.utime in os.supports_follow_symlinks
        for rel in rels:
            target = inside(folder, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            _ = inside(entry, rel).rename(target)
            info = target.lstat()
            if lutime or not stat.S_ISLNK(info.st_mode):
                stamp = _fresh_mtime(info.st_size, buried.get(rel, ()))
                os.utime(target, (stamp, stamp), follow_symlinks=not lutime)
        for directory, _dirnames, _filenames in os.walk(entry, topdown=False):
            with contextlib.suppress(OSError):
                Path(directory).rmdir()
    print(
        f"evidence {stem}: {len(rels)} files restored from .work/trash/{entry.name} with fresh "
        "mtimes; the fleet sync carries them as live files",
    )
    return 0


def _gc_pins(repo: Path, name: str, *, dry_run: bool) -> None:
    """Drop the start and landed pins of a name with no copy once the shared ``HEAD`` holds them.

    The pins dropped are recorded in a pins-only tombstone (:func:`bury_pins`), so a replica's
    machine holding them drops them too and no sync carries them back.
    """
    head = _resolve_commit(repo, "HEAD")
    leaves = pins(repo).get(name, {})
    dropping: dict[str, str] = {}
    start = leaves.get(START_PIN)
    if start is not None and _is_ancestor(repo, start, head):
        print(f"{'would drop' if dry_run else 'dropped'} start pin of {name}")
        dropping[START_PIN] = start
    landed = leaves.get(LANDED_PIN)
    if landed is not None and landing_on_main(repo, landed):
        print(f"{'would drop' if dry_run else 'dropped'} landed pins of {name}")
        dropping[LANDED_PIN] = landed
        if LANDED_COPY_PIN in leaves:
            dropping[LANDED_COPY_PIN] = leaves[LANDED_COPY_PIN]
    if dry_run:
        return
    bury_pins(repo, name, dropping, saves_dropped=False)
    for leaf, sha in dropping.items():
        drop_pin(repo, name, leaf, sha)


def _gc_copy(
    repo: Path,
    name: str,
    copy: Copy,
    *,
    dry_run: bool,
) -> int:
    """Remove one landed copy whose landing main holds; return 1 when a removal refused.

    A landed copy whose landing main does not hold is kept and says why (``keep <name>:``),
    in both modes and without a failing exit: the maintainer checks it and removes it with ``rm``.
    """
    landed = pins(repo).get(name, {}).get(LANDED_PIN)
    if landed is None:
        print(f"keep {name}: its note says landed but it has no landed pin; `rm` it once checked")
        return 0
    if not landing_on_main(repo, landed):
        print(
            f"keep {name}: the shared HEAD does not hold its landing (not committed yet, or a "
            "later commit changed a landed path); `rm` it once checked",
        )
        return 0
    if dry_run:
        reasons = removal_refusals(repo, copy, discard=False)
        print(f"would remove {name}" if not reasons else f"keep {name}: {'; '.join(reasons)}")
        return 0
    try:
        kept = remove(repo, copy, discard=False, drop_saves=False)
    except WorkError as error:
        _say(str(error))
        return 1
    except OSError as error:
        _say(f"{name}: not fully removed: {error}")
        return 1
    print(f"removed {name} (landed){kept_pins_note(name, kept)}")
    _gc_pins(repo, name, dry_run=False)
    return 0


def _gc_gone_worktree(
    repo: Path,
    name: str,
    copy: Copy,
    admin: Path,
    *,
    dry_run: bool,
) -> int:
    """Prune a worktree whose folder is gone; return 1 when its ``HEAD`` keeps it."""
    reasons = removal_refusals(repo, copy, discard=False)
    if reasons:
        if dry_run:
            print(f"keep {name}: {'; '.join(reasons)}")
            return 0
        _say(f"{name}: not pruned: {'; '.join(reasons)}")
        return 1
    print(f"{'would prune' if dry_run else 'pruned'} {name} (folder gone)")
    if not dry_run:
        delete_tree(admin)
        release_name(repo, name)
    return 0


def cmd_gc(args: _Args) -> int:
    """Remove only what is finished."""
    repo = REPO_ROOT
    _ = ensure_sentinel(repo)
    status = 0
    for name, copy in sorted(discover(repo).items()):
        if copy.hazard is not None:
            continue
        if copy.form == "pins":
            _gc_pins(repo, name, dry_run=args.dry_run)
        elif not copy.present:
            if copy.form == "worktree" and copy.admin is not None and not copy.adopted:
                status |= _gc_gone_worktree(repo, name, copy, copy.admin, dry_run=args.dry_run)
        elif copy.note.get("landed") and not copy.adopted:
            if is_replica(copy.note) or home_of(copy.note) != machine_id():
                print(f"keep {name}: a replica of {home_of(copy.note)}; fleet_sync.py removes it")
                continue
            status |= _gc_copy(repo, name, copy, dry_run=args.dry_run)
    trash = work_dir(repo) / TRASH
    try:
        entries = sorted(trash.iterdir()) if trash.is_dir() else []
    except OSError as error:
        _say(f"cannot read {trash}: {error.strerror or error}")
        return 1
    for entry in entries:
        rest, _, pid = entry.name.rpartition("-")
        if pid == KEPT_TRASH:
            stamp = rest.rpartition("-")[2]
            if stamp.isdigit() and time.time() - int(stamp) < TRASH_RETENTION_SECONDS:
                until = time.strftime(
                    "%Y-%m-%d",
                    time.localtime(int(stamp) + TRASH_RETENTION_SECONDS),
                )
                what = (
                    "evidence an explicit deletion moved"
                    if entry.name.startswith("evidence-")
                    else "a replica the fleet sync removed"
                )
                print(f"keep trash {entry.name}: {what}, until {until}")
                continue
        elif pid.isdigit() and _pid_alive(int(pid)) and int(pid) != os.getpid():
            continue
        if args.dry_run:
            print(f"would delete trash {entry.name}")
            continue
        try:
            if entry.is_dir() and not entry.is_symlink():
                delete_tree(entry)
            else:
                entry.unlink()
        except OSError as error:
            print(f"cannot delete trash {entry.name}: {error}", file=sys.stderr)
            status = 1
        else:
            print(f"deleted trash {entry.name}")
    status |= _gc_tombstones(repo, dry_run=args.dry_run)
    return status | _gc_evidence_tombstones(repo, dry_run=args.dry_run)


def _gc_tombstones(repo: Path, *, dry_run: bool) -> int:
    """Delete tombstones older than :data:`TOMBSTONE_RETENTION_SECONDS`; return 1 on a failure."""
    status = 0
    now = time.time()
    for tombstone in tombstones(repo):
        if not past_retention(tombstone.removed_at, TOMBSTONE_RETENTION_SECONDS, now):
            continue
        if dry_run:
            print(f"would delete tombstone {tombstone.file_name}")
            continue
        try:
            (work_dir(repo) / TOMBSTONES / tombstone.file_name).unlink()
        except OSError as error:
            print(f"cannot delete tombstone {tombstone.file_name}: {error}", file=sys.stderr)
            status = 1
        else:
            print(f"deleted tombstone {tombstone.file_name}")
    return status


def _repair_copy(
    repo: Path,
    name: str,
    copy: Copy,
    all_pins: Mapping[str, Mapping[str, str]],
) -> int:
    """Repair one copy; return the number of problems it could not fix."""
    if copy.hazard is not None:
        print(f"{name}: unsafe, left untouched: {copy.hazard}")
        return 1
    if copy.form == "pins" or not copy.present or copy.path is None:
        return 0
    if not copy.healthy:
        print(f"{name}: {copy.path} has a missing or broken .git; git there now fails closed")
        return 1
    if copy.form == "clone" and not copy.adopted:
        _ = _git(copy.path, "remote", "set-url", "--push", "parent", NO_PUSH)
    if not copy.adopted:
        _apply_copy_config(copy.path, copy.form)
    start = copy.note.get("start")
    if (
        start
        and START_PIN not in all_pins.get(name, {})
        and publish_pin(repo, copy.path, start, name, START_PIN)
    ):
        print(f"{name}: re-pinned {_pin_ref(name, START_PIN)}")
    lock = _git_path(copy.path, "index.lock")
    if lock.exists():
        print(f"{name}: {lock} left by a crashed git; delete it only once no git runs there")
        return 1
    return 0


def _repair_claims(repo: Path, copies: Mapping[str, Copy]) -> int:
    """Release dead claims, re-claim live copies that lost theirs; return the claims left unresolved."""
    claims = work_dir(repo) / NAMES
    problems = 0
    if claims.is_dir():
        for claim in sorted(claims.iterdir()):
            known = claim.name in copies and copies[claim.name].form != "pins"
            if known:
                continue
            if _claim_is_stale(claim):
                delete_tree(claim)
                print(f"released dead claim {claim.name}")
            elif not claim.name.startswith("."):
                print(
                    f"claim {claim.name} has no copy and its owner is not known dead; resolve it by hand",
                )
                problems += 1
    for name, copy in sorted(copies.items()):
        if (
            copy.form != "pins"
            and copy.hazard is None
            and _valid(name)
            and copy.present
            and not _present(repo, claims / name)
        ):
            _ = claim_name(repo, name)
            print(f"re-claimed {name}")
    return problems


def cmd_repair(_args: _Args) -> int:
    """Fix what is safe to fix; report the rest."""
    repo = REPO_ROOT
    problems = 0
    if ensure_sentinel(repo):
        print(f"wrote {work_dir(repo) / '.git'}")
    store = work_dir(repo) / PIN_STORE
    if store.is_dir() and not (store / "HEAD").is_file():
        _ = make_pin_store(repo)
        print(f"re-initialized {store}; its refs and objects are kept")
    worktrees = work_dir(repo) / WORKTREES
    real = [
        path
        for path in _copy_folders(worktrees)
        if copy_hazard(repo, path, WORKTREES) is None and path.is_dir()
    ]
    if real:
        _ = _git_runner.run_git(repo, "worktree", "repair", *(str(path) for path in real))
    all_pins = pins(repo)
    copies = discover(repo)
    for name, copy in sorted(copies.items()):
        problems += _repair_copy(repo, name, copy, all_pins)
    problems += _repair_claims(repo, copies)
    with land_lock(repo):
        if _journal(repo).is_file():
            print("undoing an interrupted landing from its journal")
        left = recover_landing(repo).summary()
    if left is not None:
        print(f"an interrupted landing was undone except {left}")
        problems += 1
    for stray in sorted(repo.glob(".coverage.*")):
        print(f"stray coverage file {stray}; delete it once no test run writes it")
        problems += 1
    return 1 if problems else 0


def is_pytest(argv: Sequence[str]) -> bool:
    """Return whether ``argv`` may run pytest (``run`` serialises those, ``scripts/_locks.py``).

    Any word whose last path part, less ``.exe``, is ``pytest`` or ``py.test``, or the word
    ``-mpytest``: the program itself, ``-m pytest``, and whatever a wrapper hands on
    (``uv run --group pg pytest``, ``uv tool run pytest``). A false positive only waits.
    """
    return any(
        word == "-mpytest"
        or PurePosixPath(word.replace("\\", "/")).name.removesuffix(".exe")
        in {"pytest", "py.test"}
        for word in argv
    )


@contextlib.contextmanager
def _pytest_lock_held(repo: Path, holder: str) -> Generator[dict[str, str], None, None]:
    """Hold this checkout's pytest lock for one ``run`` (``scripts/_locks.py::hold_pytest``).

    Yields the variables the command is started with, so a pytest it starts again never
    waits on this run.

    Raises:
        WorkError: the lock cannot be opened or taken for a reason but another holder.

    """
    _ = ensure_sentinel(repo)
    check_layout(repo)
    try:
        with _locks.hold_pytest(
            repo,
            f"{holder} {machine_id()} pid {os.getpid()}",
            say=_say,
        ) as held:
            yield held
    except _locks.PytestLockError as error:
        raise WorkError(str(error)) from error


def cmd_run(args: _Args) -> int:
    """Run a command in a copy's own environment."""
    if not args.tail:
        msg = "run needs a command after --"
        raise WorkError(msg)
    copy = locate(args.repo, args.name)
    copy_root = _live(copy).resolve()
    stale = _git_path(copy_root, VENV_STALE)
    if stale.exists():
        _say(f"{copy.name}: its .venv came from another machine or is missing; rebuilding it")
        _setup(copy_root, "worktree")  # the venv alone: a replica takes no hook
        stale.unlink()
    env = clean_env(copy_root, copy.name)
    location = package_location(copy_root, env)
    if not _is_within(location, copy_root):
        msg = f"{PACKAGE} imports from {location}, outside the copy {copy_root}"
        raise WorkError(msg)
    executable = shutil.which(args.tail[0], path=env["PATH"]) or args.tail[0]
    _say(f"run {copy.name} in {copy_root} (.venv {env['VIRTUAL_ENV']})")
    no_hold: dict[str, str] = {}
    serialise = (
        _pytest_lock_held(args.repo, f"{copy.name} {copy.note.get('owner') or '-'}")
        if is_pytest(args.tail)
        else contextlib.nullcontext(no_hold)
    )
    with serialise as held:
        env.update(held)
        completed = subprocess.run(
            [executable, *args.tail[1:]],
            cwd=copy_root,
            env=env,
            check=False,
        )
    return 128 - completed.returncode if completed.returncode < 0 else completed.returncode


# --------------------------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------------------------


#: The commands a copy's own ``work.py`` runs on the shared checkout around it: they read, pin
#: create-only or run in a copy. The rest write the shared tree or other copies, so they run
#: only from the shared checkout's own ``work.py``, never a copy's (perhaps edited) one.
FROM_COPY_COMMANDS = frozenset(
    {
        "list",
        "save",
        "run",
        "check-name",
    },
)


def shared_root(root: Path) -> Path:
    """Return the shared checkout whose copy ``root`` is, else ``root`` itself.

    A copy is ``.work/clones/<name>`` or ``.work/worktrees/<name>`` of a checkout, so a
    ``work.py`` started from inside one finds the registry, the pins and the locks there.
    """
    work = root.parent.parent
    in_copy = root.parent.name in {CLONES, WORKTREES} and work.name == WORK_DIR
    return work.parent if in_copy and (work.parent / ".git").exists() else root


def checkout_for(command: str) -> Path:
    """Return the shared checkout ``command`` works on (:func:`shared_root` of this script's).

    Raises:
        WorkError: this script is a copy's and ``command`` is not in :data:`FROM_COPY_COMMANDS`.

    """
    repo = shared_root(REPO_ROOT)
    if repo != REPO_ROOT and command not in FROM_COPY_COMMANDS:
        msg = (
            f"{command} from the work.py of the copy {REPO_ROOT} is refused; run work.py "
            f"from the shared checkout {repo}"
        )
        raise WorkError(msg)
    return repo


class _Args(argparse.Namespace):
    """The parsed command line, typed field by field after ``build_parser``'s ``add_argument`` calls."""

    command: str
    handler: Callable[[_Args], int]
    tail: list[str]
    name: str
    path: str
    worktree: bool
    from_rev: str
    purpose: str
    owner: str
    no_setup: bool
    json: bool
    dry_run: bool
    patch: str | None
    from_start: bool
    discard: bool
    drop_saves: bool
    evidence: bool
    file: list[str]
    adopt_missing: bool
    repo: Path


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").partition("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    owner = os.environ.get("DSF_WORK_OWNER", "")

    new = commands.add_parser("new", help="claim a name and make its copy")
    _ = new.add_argument("name")
    _ = new.add_argument("--worktree", action="store_true", help="a worktree, not a clone")
    _ = new.add_argument(
        "--from",
        dest="from_rev",
        default="HEAD",
        help="start commit or pin (HEAD)",
    )
    _ = new.add_argument("--purpose", default="", help="what the copy is for")
    _ = new.add_argument("--owner", default=owner, help="session or agent (DSF_WORK_OWNER)")
    _ = new.add_argument("--no-setup", action="store_true", help="skip uv sync and pre-commit")
    new.set_defaults(handler=cmd_new)

    adopt = commands.add_parser("adopt", help="register a harness-made copy in place")
    _ = adopt.add_argument("path")
    _ = adopt.add_argument("name")
    _ = adopt.add_argument("--purpose", default="")
    _ = adopt.add_argument("--owner", default=owner)
    adopt.set_defaults(handler=cmd_adopt)

    listing = commands.add_parser("list", help="every known copy")
    _ = listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=cmd_list)

    save_parser = commands.add_parser("save", help="pin a copy's uncommitted content")
    _ = save_parser.add_argument("name")
    save_parser.set_defaults(handler=cmd_save)

    land = commands.add_parser("land", help="apply a copy's content to the shared tree")
    _ = land.add_argument("name")
    _ = land.add_argument("--dry-run", action="store_true")
    _ = land.add_argument("--patch", default=None, help="also write the patch to this file")
    _ = land.add_argument(
        "--from-start",
        action="store_true",
        help="patch from the copy's start, not its last landing",
    )
    land.set_defaults(handler=cmd_land)

    rm = commands.add_parser("rm", help="remove one copy")
    _ = rm.add_argument("name")
    _ = rm.add_argument(
        "--discard",
        action="store_true",
        help="drop unsaved or unreadable content",
    )
    _ = rm.add_argument(
        "--drop-saves",
        action="store_true",
        help="also delete its save and landed pins",
    )
    _ = rm.add_argument(
        "--evidence",
        action="store_true",
        help="also delete its evidence on every machine",
    )
    rm.set_defaults(handler=cmd_rm)

    evidence_rm = commands.add_parser(
        "evidence-rm",
        help="delete a stem's evidence (or some files) on every machine",
    )
    _ = evidence_rm.add_argument("name", metavar="stem")
    _ = evidence_rm.add_argument(
        "--file",
        action="append",
        default=[],
        help="only this file (relative to the stem folder)",
    )
    _ = evidence_rm.add_argument(
        "--adopt-missing",
        action="store_true",
        help="record the files removed here by hand that peers still hold",
    )
    _ = evidence_rm.add_argument("--dry-run", action="store_true")
    evidence_rm.set_defaults(handler=cmd_evidence_rm)

    evidence_restore = commands.add_parser(
        "evidence-restore",
        help="move deleted evidence back from the trash with fresh mtimes",
    )
    _ = evidence_restore.add_argument("name", metavar="trash-entry-or-stem")
    _ = evidence_restore.add_argument("--dry-run", action="store_true")
    evidence_restore.set_defaults(handler=cmd_evidence_restore)

    gc = commands.add_parser("gc", help="remove only what is finished")
    _ = gc.add_argument("--dry-run", action="store_true")
    gc.set_defaults(handler=cmd_gc)

    repair = commands.add_parser("repair", help="fix the safe things, report the rest")
    repair.set_defaults(handler=cmd_repair)

    run = commands.add_parser(
        "run",
        help="run a command in a copy's own environment",
        usage="%(prog)s <name> -- <command...>",
    )
    _ = run.add_argument("name")
    run.set_defaults(handler=cmd_run)

    check = commands.add_parser("check-name", help="validate a name")
    _ = check.add_argument("name")
    check.set_defaults(handler=cmd_check_name)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch one command; a refusal prints its reason and exits 1 (``run``: 125).

    An operating-system error no command turned into a refusal (an unreadable folder
    under ``.work``), and a module the interpreter lacks (``tomli`` outside ``uv run``), is
    printed the same way, never as a traceback; the command has already stopped, so this
    only formats the error and decides nothing. A ``work.py`` inside a copy works on the
    shared checkout around it (:func:`shared_root`) for :data:`FROM_COPY_COMMANDS` alone.
    """
    words = list(sys.argv[1:] if argv is None else argv)
    tail: list[str] = []
    if "--" in words:
        split = words.index("--")
        words, tail = words[:split], words[split + 1 :]
    parser = build_parser()
    args = parser.parse_args(words, namespace=_Args())
    args.tail = tail
    if tail and args.command != "run":
        parser.error(f"{args.command} takes nothing after --")
    try:
        refuse_locating_env()
        args.repo = checkout_for(args.command)
        if args.command != "check-name":
            check_layout(args.repo)
        return args.handler(args)
    except (WorkError, OSError) as error:
        print(f"work: {error}", file=sys.stderr)
        return REFUSED if args.command == "run" else 1
    except ModuleNotFoundError as error:
        print(f"work: {sys.executable} lacks the module {error.name}; {RUN_AS}", file=sys.stderr)
        return REFUSED if args.command == "run" else 1


def _cli() -> NoReturn:
    raise SystemExit(main())


if __name__ == "__main__":
    _cli()
