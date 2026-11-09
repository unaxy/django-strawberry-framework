# START.md — agent handbook

You're in `django-strawberry-framework`. For agents, not users. Read once, then [AGENTS.md][agents] (law; this file = terrain). Then go. [CLAUDE.md][claude-md] exists only to make you read both.

**Standing reference, maintained not frozen.** Mechanisms, conventions, hazards that hold across releases. Where this file restates a mechanism another file owns (CI job order, hook flags, script inventories), that file is authoritative and this one is corrected to match. Never state: no version, no shipped list, no in-flight names, no counts a commit can change. State lives in [KANBAN.md][kanban], [TODAY.md][today], [docs/GLOSSARY.md][glossary]. Where a number matters, this file names where to read it. No session notes, cycle status, or "as of" facts here; a lesson lands only once release-independent.

## Reading order

1. [AGENTS.md][agents] — rules. Dense, unnumbered; cite a rule by its content.
2. This file — repo, tooling, maintainer.
3. [docs/README.md][docs-readme] — consumer how-to.
4. [docs/TREE.md][tree] — module map + ownership.
5. [KANBAN.md][kanban] — in flight / next.
6. [GOAL.md][goal] — destination every card serves.

Also: [docs/GLOSSARY.md][glossary] = capability catalog w/ shipped/planned/deferred per anchor. [TODAY.md][today] = current capability via `products` app. [BACKLOG.md][backlog] = unscheduled ideas. [CHANGELOG.md][changelog] = maintainer-owned, never edit unless told. [README.md][readme] = public pitch.

## What this repo is

DRF-shaped Django integration for Strawberry GraphQL. Pre-`1.0`, one maintainer, fast iteration. Shipped surface = glossary's job, not this file's. Version single-sourced: `__version__` in `django_strawberry_framework/__init__.py` (hatchling reads it).

Upstream checkouts for cribbing (paths pinned in [AGENTS.md][agents]): `~/projects/strawberry-django-main/strawberry_django`; `graphene_django` inside `~/projects/django-graphene-filters/.venv`. Behavior ← strawberry-graphql-django. Surface ← django-graphene-filters + DRF.

## How the maintainer communicates

Direct, decisive, reverses fast, expects same.

- Short imperatives. "Now do X." "Scratch that, Y." No hidden tone. Do the thing.
- Reverses decisions from a turn ago (moved example tests in, then straight back out; both right then). Roll with it; don't re-argue old reasoning.
- Pushback on a hidden flaw welcome, once. Surface, suggest better, defer. No lectures.
- No preamble, sycophancy, over-explanation. 12y Django + Vue.
- Status reply = result + what's broken + what's uncommitted. ≤3 sentences.
- no need to mention commit(s) are un pushed.

## Session rules you will forget

- **No `pytest` after edits.** Format only. The maintainer says "run tests" / "run the full pipeline" when wanted. Binds agent briefs and scratch copies too: a brief allows ruff, `check_trailing_commas.py` and basedpyright only; agents list the tests and mutation probes they would run and wait for the maintainer's go.
- After edits: `uv run ruff check --fix .`, `uv run ruff format .`, stop. No `pytest`, `manage.py check`, `uv build`.
- The maintainer commits. Never auto-commit unless explicitly asked. **NEVER `Co-Authored-By` or any attribution footer.** Message = change description only.
- **Commit auth covers ONE batch.** Doesn't carry to next batch/task, nor via a compaction summary. Rule is *no auto-commit*, not *never commit*; re-read AGENTS.md when a rule seems to forbid what the maintainer explicitly asks.
- **NEVER create/switch branches without explicit auth.** Commit request ≠ branch auth. Commit on current branch; flag oddities after. (Once branched "helpfully" → misrouted the maintainer's concurrent commit.)
- Before committing: `uvx pre-commit run --files <paths>`. Hooks check things ruff doesn't. See "Pre-commit and CI gates".
- Temp files → session scratchpad dir; copies of the tree → `.work/` through [scripts/work.py][work] ("Private working copies"). Never the tracked tree, never bare `/tmp`. `work.py rm` a copy and delete temp files the moment their work lands (a uv-synced copy runs to hundreds of MB; `.venv` alone is most of it). Delete only what you created: a brief saying "delete your scratch files" once emptied a whole shared scratchpad (gate kit + venv), so briefs say "delete only files you created". Never touch another session's scratch.

## Concurrent sessions

The maintainer runs several sessions on this checkout, same branch, same time. Normal.

- Unexpected dirty/untracked files, commits you didn't make = other session. Never revert/"tidy". Never reset `examples/fakeshop/db.sqlite3` while another session may write it.
- `git add <path>` only; `-A` sweeps their WIP into your commit. Reverse too: your edits may land in THEIR commit; check `git log --stat` before assuming your work is unstaged. Swallowed file can be MIXED (their hunks + yours); back out hunk-wise, not file-wise. Your file missing from the dirty list is the signal: `git show HEAD:<path> | grep -c <your marker>` before concluding the work was lost; if it landed, commit nothing for it and re-add nothing.
- No `git stash` / `checkout --` / `restore` on shared tree; the one sanctioned exception is `git checkout HEAD -- docs/review/` to restore that protected directory. Diff your change vs `git show HEAD:<path>` written to scratchpad.
- Never apply an existing stash: the local ones are dead WIP older than shipped work, and applying one reverts it. A partial `stash apply` lands the untracked half (`stash@{N}^3`) w/ no conflict marker and no `git status` signal (dead DRAFT specs once sat at `docs/` top level that way, breaking the one-WIP-spec invariant). An untracked file older than the work in flight is a stash leak until `git log --all --follow -- <path>` says otherwise.
- Before landing a fix, check for a parallel one: `git log main` (`-S<symbol>`), `work.py list`, `git worktree list`, open sessions. A spun-off follow-up task the maintainer starts becomes a second implementation of the same defect; two sessions have fixed one defect from the same base and found out only at landing.
- Landing from a copy is patch landing (`work.py land <name>`, "Private working copies"): the copy never commits; its content applies to the shared WORKING tree as one `git diff --binary` onto paths clean there (or already identical), never the shared index, and the maintainer commits on main, which stays linear (no merge commit, no side branch, no pushed branch). Main moved under the copy → `land` applies onto it when the patch still applies; otherwise make a fresh copy at the new `HEAD`, re-apply the saved work, re-gate. After a landing, the same copy's next `land` patches from its `landed-copy` pin (its whole content at that landing): only its work since lands, and a path it has not changed since is never re-applied, whatever main did to it; one main no longer holds as landed (reverted, never committed, changed since) is named in a note, and `land --from-start` patches from the copy's `HEAD` to land it again. `land` refuses, nothing applied, a copy whose note records a landing whose `landed` or `landed-copy` pin is missing, another copy's or incomplete, and a path the copy put back at its start (`reset --hard`, `checkout --`) where its last landing held other content and main's `HEAD` is not at the start there, even where main reverted the landing and edited the file since; `--from-start` patches from the copy's start instead, re-applying an unheld landing in the first case and in the second landing the rest while leaving the reset paths as main holds them. A reset path main has at the start changes nothing. An edit back to the start in part of a file lands like any edit. A path the patch touches that another session holds dirty stops `land` with nothing applied: wait for their commit, or carve by hand from a private index (below). Ask before `git push`, then `git merge-base --is-ancestor <sha> origin/main`.
- `git mv` stages instantly; concurrent commit can adopt your rename while its content edits stay dirty. Rewrite content first vs plain `mv`, `git add` both together, verify `git log --stat` (swept rename vanishes from `git status`).
- Other session may rewrite main history (amend/rebase). Prove your commit landed: `git merge-base --is-ancestor <sha> HEAD`. Not memory.
- Commit out of a concurrently-dirty tree w/o touching their hunks OR their staged entries: build intended blob (`git show HEAD:<path>` + your diff), `git hash-object -w`; then in a PRIVATE index — `GIT_INDEX_FILE=<scratch>/idx git read-tree HEAD`, `GIT_INDEX_FILE=<scratch>/idx git update-index --add --cacheinfo <mode>,<blob>,<path>`, `GIT_INDEX_FILE=<scratch>/idx git commit` naming NO paths (`--only <paths>` re-reads the WORKING tree, swallowing their hunks back). The shared index is never the commit source, so whatever another session staged before or after your preflight can't ride along. Afterwards `git update-index --cacheinfo` the same entries into the shared index so it matches new HEAD. Slow; stages only your bytes. Verify `git ls-tree HEAD <path>`, not `git status`.
- MIXED **sqlite** carve: destination = exact copy of `git show HEAD:<db>` in scratch; `ATTACH` the dirty working copy as `wt`; decide the owned rows UP FRONT (table + explicit pk list); `UPDATE main.<t> SET <col> = (SELECT <col> FROM wt.<t> WHERE pk = main.<t>.pk), ... WHERE pk IN (...)` with columns named from `pragma_table_info`, never inferred from `.dump` text diffs (commas, quotes, repeated values, and multi-column edits all misread) — never `DELETE`+`INSERT SELECT` (cascades). Proof: `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, and a per-table `.dump` diff vs HEAD showing 0 lines in every non-owned table. Why from HEAD: copying the working DB and reverting foreign rows leaves their text in freelist pages, so the commit still ships it (`strings` finds it, no query does).
- Export generated from a carved DB: prove consistency by reading the renderer's selection set, not by arguing. `_kanban_lib` selects `term { id title anchor statusText }`, never `GlossaryTerm.body` ⇒ a `GlossaryTerm.body`-only edit can't reach `KANBAN.md`; it DOES select `allKanbanBoardDocs { body }`, so a `BoardDoc.body` edit is a board render change.
- `git diff --cached --name-status` before any `git add`: index may hold their staged work; one commit ships it under your message. If they staged whole tree, `git diff -- <path>` shows your file clean; use `git diff HEAD -- <path>`.
- Carve-out commit: first grep your new files' imports for symbols ABSENT at HEAD. Rewired onto their refactor → no standalone commit exists; leave dirty, say so.
- Before recommending push: `git rev-list --left-right --count origin/main...main`. "Tests failing" but local green → `gh run list` first; red job may not be a test job.
- Final-gate failure in committed code may be the maintainer's own rewrite of your fix. Diff your verified version vs HEAD before editing; broken test inside their in-flight refactor ≠ your regression. One collection ERROR in one test module drops coverage across every file its tests build schemas through → scattered misses usually = one broken module.
- Don't regenerate rendered docs while their feature work is mid-flight (publishes half-landed surface).
- Attribute dirty files by DIFF CONTENT, not "files my task touched". Regenerated doc/DB = CONSEQUENCE of a code change; belongs to whoever caused it.

## Private working copies

An agent that needs a tree of its own works in a copy under the git-ignored `.work/` at the repo root, made and removed only by [scripts/work.py][work] (its docstring is the full contract). The REVIEW, HUNT and DRY flows keep `workspace.py`; one manager per flow.

- **Layout.** `.work/clones/<name>/` (`git clone --no-hardlinks -o parent`, push URL `no-push`, `HEAD` detached, no branch tracking config), `.work/worktrees/<name>/` (`git worktree add --detach`, locked `dsf-work <name>`), `.work/evidence/<stem>/` (what must outlive the copy: proof scratch, pre-edit snapshots, database copies; a copy's repro tests go in its own `tests/` tree, where its conftest applies), `.work/names/<name>/` (the claim on a name, one namespace for every form, published with its owner in one rename), `.work/pins.git` (the pins, below), `.work/trash/` (`rm` renames in, then deletes), `.work/tombstones/` (a home's removal record, below). `.work`, its folders and every copy folder must be real directories under the real `.work` (no symlink on the way): every command refuses a layout that is not and never reads or changes an unsafe copy; `.work` is kept `0700`. `.work/.git` is a sentinel file (`gitdir: /nonexistent/...`): a copy whose own `.git` went missing makes git fail instead of resolving to the shared checkout. Every copy gets its own `.venv` (`uv sync --frozen`), its own `.python-version`, `core.longpaths=true`, `core.autocrlf=false`, a Postgres database name of its own under `run`, and (clones) the pre-commit hook. A worktree has its own index, so `git ls-files` gates work there; take a clone for its own hooks, stash, config or refs, a ref-rewriting experiment, or a move to another machine.
- **Names say the purpose, never the author.** `<kind>[-<id>]-<slug>[-verify|-rN]`, `[a-z0-9-]`, max 24 chars (Windows path budget). Kinds `build fix spike verify ci bench head carve deps spec ship` (`review`/`hunt`/`dry` belong to `workspace.py`). Ids are tracker-prefixed and record the number at creation: `c051` card, `i681` item, `s051` spec, `u25` upstream item, `g<sha7>` commit, `v0-0-15-2` release. A second copy for one purpose takes `-verify` or `-r2` and shares the stem's evidence. `work.py check-name` validates.
- **Registry = folders + `git worktree list --porcelain` + the pins**; the note (purpose, owner, host, start, adopted, landed) lives in the copy's own git config. Pins are `refs/work/<name>/...` refs in the bare `.work/pins.git`, never in the shared repository (so no push of it, `--mirror` included, publishes a snapshot), and never branches: `new`/`adopt` pin `start`; `save` pins the content as `save-N` (a commit built in a private index, no index touched); `land` pins the merged result as `landed` and the copy's own content as `landed-copy`. A pin counts as keeping content only while `pins.git` holds every object it reaches. A `start` or `save-N` pin is created only where none exists, so racing saves get two numbers and none is replaced; `landed` and `landed-copy` are replaced on each landing by compare-and-swap against the value read before, so a racing landing is never overwritten. `new <name> --from refs/work/<old>/save-N` starts at the save's parent with the saved content as uncommitted work. A copy's content is read into a fresh private index from `HEAD`, so `assume-unchanged`, the stat cache and `core.fsmonitor` never hide an edit; a case-only rename keeps its new spelling; a sparse or `skip-worktree` copy, and one holding a nested repository or submodule, is refused by `save`, `land` and `rm` (`rm --discard` aside).
- **Commands.** `new <name> [--worktree] [--from REV] [--purpose TEXT] [--owner TEXT]` (exclusive `mkdir` claims the name; e.g. `new fix-i681-slug --purpose "repro i681" --owner "bug-hunt session"`, owner = the session or agent name, free text, shown by `list`), `adopt`, `list`, `save`, `land`, `rm`, `gc`, `repair`, `run <name> -- <cmd>`, `check-name`. Every command refuses while `GIT_DIR`, `GIT_WORK_TREE` or `GIT_INDEX_FILE` is set. `run` scrubs `GIT_*`, `DIRENV_*`, `DJANGO_*`, `VIRTUAL_ENV`, `PYTHONPATH` and the shared `.venv/bin` (direnv activates it in the parent tree), runs from the copy with its venv, and refuses unless the package imports from inside the copy: `uv run` in a copy's evidence folder walks up to the shared `pyproject.toml` and its `.venv`. It prints `work: run <name> in <copy> (.venv <path>)` on stderr. One pytest at a time per checkout ([scripts/_locks.py][locks]): `run` of a command with a `pytest`/`py.test`/`-mpytest` word and each `prove_failability.py` scope wait on `.work/pytest.lock`, a copy's included; a pytest they start inherits the hold; a pytest started any other way is not seen. `--purpose`/`--owner` refuse control characters.
- **Landing = patch landing** (Concurrent sessions), one `land` at a time (a kernel lock on `.work/land.lock`, released however its holder ends). `land` refuses a copy whose `HEAD` is not on the shared main (copies do not commit), a shared `HEAD` other than `refs/heads/main`, a change to `examples/fakeshop/db.sqlite3` (carve it), any touched path the shared tree holds otherwise than its `HEAD` (bytes hashed from disk, so an `assume-unchanged` bit hides nothing), and a patch that does not apply onto the shared `HEAD` (applied first in a private index: the expected result, merged with what main changed since; after a landing the patch starts at the copy's `landed-copy` pin, so a path unchanged since is never re-applied, and `--from-start` starts it at the copy's `HEAD`; a recorded landing with an unusable pin, and a path the copy put back at its start where main moved off it, refuse too, as in Concurrent sessions). It journals every touched path (`.work/land-journal.json`), writes each one to a temporary file, re-hashes the target and publishes it with one `os.replace`, working tree only; a changed path, a failed write or a moved branch or `HEAD` puts back every path holding what it wrote and keeps (and names) another writer's bytes, and a killed `land` is undone by the next `land` or `repair`. The window between the last re-hash and the replace stays open: nothing binds a plain editor, so land while no other session edits the paths it touches. `git fetch <clone> main` from a detached clone fetches the old main: never a landing.
- **Cleanup.** The agent that made a copy removes it (`rm`) once its work lands or is saved; `rm` refuses a path outside `.work/`, a copy a process has its cwd in (or one an incomplete process census cannot vouch for; another user's unreadable process is skipped only because `.work` is `0700`, root's stay invisible), one modified in the last 10 minutes after its last save or landing (unless its content still equals its start), one holding `workspace.py` pool/state or `prove_failability.py` state, a worktree someone else locked, and content neither `HEAD`, a save nor the landed pin, or unreadable (a broken `.git`; `--discard`). Files git ignores in a copy are not content: `rm` and `gc` delete them without a refusal. `gc` removes only landed copies whose landing the shared `HEAD` holds, gone worktrees' metadata and pins main holds; never a live session's copy, an uncommitted landing, a save, or evidence. Only `gc` deletes by age: a fleet-removed replica's `-kept` trash entry after 7 days and a tombstone after 30; otherwise disk is the maintainer's to watch.
- **Proofs and floor runs.** Run `prove_failability.py` from inside the copy (`work.py run <name> -- python scripts/prove_failability.py ... --scratch-root <shared root>/.work/evidence/<stem>/proofs`): from the shared checkout it refuses a scratch root inside the repo. A floor venv goes in the scratchpad or `.work/evidence/<stem>/`, never the tracked tree (`.venv-floor/` at the root is not ignored).
- **Harness copies are adopted in place.** A Claude Desktop `.claude/worktrees/*`, Codex, Cursor, T3, OpenCode or Muse `--workspace` worktree is registered with `work.py adopt <path> <name>`, never moved or locked; its harness-made branch is the harness's, not an agent-created branch, and `rm` leaves it to the harness.
- **Cross-machine.** `adopt` takes a clone at `.work/clones/<name>` whose remote is a fleet checkout over SSH (`<host>:<path>` or `ssh://<host>/<path>`, the host a row of `docs/fleet/machines.json` by name, alias or `ssh` host, the account the one `ssh -G <host>` names; the registry tracks no usernames). A copy on another fleet machine is a clone there whose `parent` remote is the source checkout over SSH (`git clone --no-hardlinks -o parent <ssh-host>:<checkout path> .work/clones/<name>`, then `git remote set-url --push parent no-push`), under that machine's own `.work/`, never a sibling folder under `~/projects/` (autosync fast-forwards those). Its work comes back as a patch the coordinator lands; never rsync a `.git` by hand ("Syncing the fleet" replicates whole copies under its own rules).
- **Forbidden in the shared checkout:** `git clean -x`, `git clean -X`, `git clean -ff` (each removes `.work/evidence`, or every copy) and `git stash -a` / `--all` (sweeps `.work/` into a stash); never `git push --mirror` of the shared checkout (it publishes every ref there). A record that cites evidence cites something in git (`git show <sha>:<path>`), never a path only `.work/` holds.

### Syncing the fleet

[scripts/fleet_sync.py][fleet-sync] keeps every fleet machine's `.work/` in step (its docstring is the full rule; machines in [docs/fleet/MACHINES.md][machines]). `uv run python scripts/fleet_sync.py` (= `status`, read-only), `sync [--dry-run] [--machine M] [--copy NAME] [--main-only]`, `handoff <name> [--to M] [--force-offline-home]`, `--json` on each; exit `0` clean, `1` conflict or skipped work, `2` bad setup.

- **Who it reaches.** Tailscale peers online plus this machine, matched to a `machines.json` row by its name or an alias (else reached by MagicDNS name and reported with a suggested row); a machine is its row's name in every record, stored names read through the row's aliases ([scripts/fleet.py][fleet] "Identity"), and `sync`/`handoff` refuse on a host no row names; a peer qualifies only with its checkout at `~/projects/django-strawberry-framework`, the same root commit, `.work/` ignored there, `rsync`, and its own `scripts/fleet_sync.py` (the agent each call runs there, so both ends apply one rule). Windows is reported, never half synced. A run only handles pairs that include the machine it runs on.
- **One writer per copy.** A copy's `home` (work.py note) is the only machine that edits it; every other machine holds a replica (`replica=true`, `syncedtree`), refreshed from home, never synced back; work.py `save` and `land` refuse a replica, `rm` too unless `--discard` (which removes this machine's replica alone, into `.work/trash`), and `gc` never removes one (a former home a handoff demoted included). To continue a copy on another machine run `handoff <name>` there (or `--to M`): a fresh sync (the home's pins under the name included), then the home flips everywhere it reaches, each note it reaches taking the handoff's lineage (`generation`, `formerhomes`), so a replica it missed (machine offline) is later refreshed, re-pointed and removed by the newest home. A handoff whose home is not reached refuses unless `--force-offline-home`; the returning old home is then a conflict naming the newer one, nothing overwritten. A replica edited since its last sync, two homes for one name, or one pin ref with two commits stops that copy and is reported, both sides kept.
- **What moves.** Clones whole (no `.venv`, caches, `*.pyc`, nor the git directory's `config`, hooks and locks), their `parent` pointed at the target's own checkout, push `no-push`, venv marked stale for `work.py run` to rebuild; worktrees as a `git worktree add --detach` at the same commit plus their files; pins create-only both ways (one the target's pins already reach is linked with no bundle; a pin a tombstone records dropping never comes back, and `rm --drop-saves` at home drops the replicas' pins with them; a name left holding pins alone blocks `work.py new` until `work.py rm <name> --drop-saves`, which the next sync carries to every machine holding no copy under it); evidence as a never-deleting union; main by fast-forward only (HEAD on main, no land, no merge or rebase in progress, `git merge --ff-only`), diverged reported. A replica is removed (into `.work/trash`, kept 7 days) only when its home's tombstone matches it (written by the home's `work.py rm` or `gc` for that very copy, its note's identity; carried both ways like evidence) and it is unchanged since its last sync and idle; otherwise it is kept and reported. A home that merely lacks the copy (wiped, restored from an old backup) removes nothing, and the replica is kept and reported (`handoff <name>` there, or `work.py rm --discard <name>`); a new home copy reusing an older replica's name never overwrites it (the old identity's tombstone removes the replica first and the next run replicates the new copy; without one it is a conflict). A removed replica, `work.py rm --discard` of a replica included, waits in `.work/trash/<name>-<seconds>-kept`: restore a clone with `mv` back to `.work/clones/<name>`, `work.py repair`, then `fleet_sync.py handoff <name>` before the next sync; a worktree's files are copied into a fresh `work.py new`. Writes need work.py's process census to vouch on the side written; the home is only read.
- **Periodic runs** are the maintainer's to install (cron, a systemd user timer beside the desktop's `git-autosync`, a launchd agent); overlapping runs skip on `.work/fleet.lock`.
- **Known gaps.**
  - An edit made in a replica while a sync runs can be lost: replicas are not workspaces, one writer per copy.
  - A home that saves the same file twice within one transfer can leave the replica stuck as changed until `work.py rm --discard <name>` there (which keeps it in trash).
  - A replica made before `syncedrefs` existed refuses once `git gc` packs its refs (`packed-refs` reads newer than its last sync).
  - Gitignored files in a replica are not content: a refresh replaces or deletes them.

## Toolchain

- **`uv`** owns env. `uv sync` = dev group; `uv sync --group pg` adds psycopg. Everything via `uv run`. Never `pip install` into `.venv`; `uv pip install` w/o `--python <path>` lands there.
- **`ruff`** format + lint (`pyproject.toml`: line 99, E501 graced 110, Google docstrings). `hunt-ws/` excluded from lint and format (`extend-exclude`), `*.md` from format (fenced blocks are verbatim examples); `force-exclude` binds both to a path named explicitly or via `--stdin-filename`, for `ruff check` and `ruff format`.
- **`basedpyright`** (`uv run basedpyright`, no args): the one type checker. `[tool.basedpyright]` owns scope (every `.py` in the repo minus the trees its `exclude` lists; basedpyright does not read `.gitignore`; `tests/` stays in the root environment with `examples/fakeshop` as an extra path, since an environment rooted at `tests/` lets `tests/rest_framework` and `tests/types` shadow DRF and the stdlib), the Python it checks against (lowest its stubs support, NOT the package floor; below it every stub `-> Self` reads as `Unknown`) and the rules; `all` mode minus an explicit off-list (five off by design, each w/ its reason in the comment above them; the rest a ratchet: enable one to list its sites; a rule can be enabled area by area, the rest of the scope keeping it off by a per-environment override on the `scripts` / `examples/fakeshop` execution environments, or per file by a `# pyright: <rule>=false` line at the top of the file, deleted once that file's sites are fixed), a warning fails; no plugin (stubs + packages' own annotations only, never the fakeshop settings). The one suppression is `# pyright: ignore[<rule>]` with a `# basedpyright: <why>` line above; `# type: ignore` is not read (`enableTypeIgnoreComments = false`) and an unneeded suppression fails (`reportUnnecessaryTypeIgnoreComment`); a comment opening `# pyright:` is parsed as a directive and errors. It never narrows on `hasattr` and follows a TypeGuard through a local. The venv runs a newer Python w/ lazy annotations, so an unquoted `TYPE_CHECKING`-only name passes the checker AND local tests yet `NameError`s on the floor; a 3.11+ stdlib or `typing` name (`BaseException.add_note`, `typing.Never`) passes the main run; `pyrightconfig.floor.json` (extends the table, same scope, `pythonVersion` 3.10, unneeded-suppression rule off since a suppression the 3.11 pass needs can be moot at 3.10; every `reportUnknown*` rule is off there too, since a stub `-> Self` reads as `Unknown` at 3.10 and those rules would measure the stubs, not the code) catches the name; ruff `TC004` catches it statically for a `TYPE_CHECKING`-only import (not a name defined in the block), the floor run of `tests/base/test_init.py` at runtime for both.
- **`pytest`** + pytest-django/xdist/cov/asyncio. Config in `pytest.ini`, not pyproject. See "Tests".
- **`uvx pre-commit`**: `install` once per clone; `run --files <paths>` pre-commit; `--all-files` sweep. Install the git hook from a stable interpreter (`uv tool install pre-commit && pre-commit install`; first run rebuilds the hook envs, minutes): `uvx pre-commit install` bakes uvx's cached interpreter into `.git/hooks/pre-commit`, and once uv evicts it the hook falls back to a `pre-commit` on PATH or fails "`pre-commit` not found".
- **`rg`** for search. Always print population size: empty grep ≡ grep that ran on nothing.
- **`gh`** for CI runs / Dependabot PRs. Workflows in `.github/workflows/`.
- **`docker compose -f docker-compose.postgres.yml up -d`** → local Postgres for `FAKESHOP_PG_DSN`.
- Interpreter pinned by `.python-version`. Shared `.venv` = NEWEST supported, not the floor.
- Subagents inherit the ACTIVE mode: spawned from Plan mode they return a plan, not edits, so clear mode (or spawn from Default) before dispatching implementers; do not fall back to inline work.
- Subagent effort comes only from the agent type's `effort:` frontmatter (AGENTS.md); a "Reasoning effort: X" line in a prompt sets nothing. A newly written agent type is dispatchable only once the harness lists it: wait, never fall back to `general-purpose`. The Agent `model` parameter overrides the definition's model; its `effort:` still applies.
- Subagents return reports as text in their final message, never as report files; persist each to the scratchpad on arrival.
- `ruff format`/`--fix` during a test run invalidates that run's coverage map. Format before/after, not during.

## Support matrix: floor and ceiling

Never state a version from memory. Read it:

| Axis | Floor | Ceiling |
|---|---|---|
| Python | `requires-python`, `pyproject.toml` | highest `Programming Language :: Python` classifier; CI "latest" cell |
| Django | `Django>=` pin, `[project].dependencies` | resolved `django` in `uv.lock`; `Framework :: Django` classifiers = tested majors |
| strawberry-graphql | `strawberry-graphql>=` pin (adjacent comment = why) | resolved entry, `uv.lock` |
| graphql-core | `graphql-core>=` pin (adjacent comment = why) | resolved entry, `uv.lock`; `<3.4` cap in the same pin |
| django-filter | `django-filter>=` pin | resolved entry, `uv.lock` |

Exact point a floor run installs = policy in [docs/builder/BUILD.md][build] "Floor verification"; moves together with `pyproject.toml`.

Django range spanning a Python-floor boundary → `uv.lock` carries TWO Django resolutions behind `python_full_version` markers. Check which one a given Python gets before claiming "latest Django".

Soft deps (never in `[project].dependencies`; tests cover present AND absent): `cryptography` (`Meta.cursor_field` keyset only), `channels[daphne]` (ASGI router), `django-debug-toolbar` (toolbar middleware), `djangorestframework` (`SerializerMutation`). Floor = `>=` bound of its `[dependency-groups].dev` row; every floor run installs it exactly. Absence = `sys.modules[name] = None` sentinel via `tests/_soft_dependency.py`.

CI: exact-floor cell + latest cell every push/PR. Every cell runs as two shard jobs on separate runners: `library-keyset` (`test_library_api.py` + `test_keyset_api.py`, `--dist load`) and `remainder` (the rest, `--dist loadscope`); one runner no longer fits the suite in the 45-minute timeout. Latest's shards trace coverage; the `coverage` job combines them and owns the gate + Coveralls. Full matrix + sharded-DB variant = manual dispatch + weekly schedule (Mon 05:41 UTC). Floor cell = API-compat probe, never a deployment recommendation.

**Floor is executed, never reasoned.** Newer source / changelog / classifier ≠ answer. Throwaway venv outside the tracked tree (scratchpad, or the shared checkout's `.work/evidence/<stem>/`), explicit interpreter, focused tests:

```shell
uv venv <scratch>/dsf-floor --python <floor python>
uv pip install --python <scratch>/dsf-floor/bin/python -e . --group dev
uv pip install --python <scratch>/dsf-floor/bin/python 'django==<floor>' 'strawberry-graphql==<floor>'
uv pip install --python <scratch>/dsf-floor/bin/python '<each soft dep>==<floor>'
<scratch>/dsf-floor/bin/python -m pytest <focused scope> --no-cov
```

Floor values from BUILD.md "Floor verification" at run time.

Never mutate shared `.venv` for a matrix check; silently changes floor for every concurrent session (`UV_PROJECT_ENVIRONMENT` redirects `uv sync`/`uv run`, NOT `uv pip install`). Restore w/ `uv sync --frozen`. Launch pg tier as `uv run --group pg pytest` (group pinned at launch; a parallel `uv sync` strips psycopg mid-run). Postgres CI's `uv sync --upgrade-package Django` rewrites `uv.lock` whenever a Django newer than the lock exists (what it moves: the comment on `postgres.yml`'s "Install dependencies with latest Django" step), if copied locally → revert lock after.

Change depends on WHICH upstream attribute/body (wrapped seam, patch target)? Enumerate every published release floor→latest, fetch each wheel, grep the module. Installed version ≠ consumer's. Pin result as version→names table beside the contract + a SET of audited bodies so an unseen third fails closed. Upstream bump "regression": read WHICH assertion failed in a multi-assert test; stale SQL-text expectation looks identical to a broken boundary.

## Tests: where, how

Four trees, one `pytest.ini`. Locally, run targeted selections only (`uv run pytest -n0 --no-cov <files or node ids>`); the full suite runs in GitHub Actions.

| Tree | Target | Style |
|---|---|---|
| `tests/` | package | in-process; fakeshop models OK as fixtures; `tests/base/` = exactly `test_init.py` + `test_conf.py` |
| `examples/fakeshop/test_query/` | any package line reachable by a real query | live `/graphql/` HTTP via `examples/fakeshop/graphql_client.py`; **FIRST place to add a test** |
| `examples/fakeshop/apps/<app>/tests/` | one app's models/admin/services/commands | in-process `schema.execute_sync`; packages `apps.<app>.tests` |
| `examples/fakeshop/tests/` | project/config only (urls, settings guard, schema export) | not a package |

- **Live-first, both verdicts.** Reachable from a real query → MUST be in `test_query/`. Promoting to live DELETES the package-only stand-in, same change, after proving redundancy empirically. A plan can pin a predicate's rejection live and leave acceptance package-only: check which VERDICT each live row proves. "Fixture can't reach it" = fixture gap, not unreachability. The live-tier README suite map indexes every `test_query/test_*.py`; the module docstring is the authoritative description, the map is the index.
- **First line of every catalog/auth test:** `seed_data(N)` / `create_users(N)` from `apps.products.services`. Library acceptance tests: inline `Model.objects.create(...)`.
- **Parallel default.** `addopts = -v -n auto --dist loadscope --cov --cov-report=term-missing`. `loadscope` keeps a module on one worker (registry-isolation fixtures; expensive live schema rebuild). Worker = process w/ own registry + in-memory SQLite. Single test: `uv run pytest -n0 tests/test_x.py::test_name`.
- **Machine budget.** The maintainer's Mac: 16 GB, 8 cores, no swap. Never run the full suite locally: the full suite, the coverage gate and the version matrix run in GitHub Actions (`django.yml` on every push; `gh workflow run django.yml` dispatches the full matrix, `FAKESHOP_SHARDED=1` rows included; `postgres.yml` is the Postgres tier). Targeted runs and basedpyright start without waiting for an idle machine. A new thread or heavy run starts on the fleet machine `scripts/load_balancing.py --pick` names (`--heavy` for heavy work; [MACHINES.md][machines] "Picking a machine"). Copies live in the git-ignored `.work/`, which no reboot or temp purge touches; a copy's state worth keeping is pinned (`work.py save`), never fetched as `git fetch <clone> main` (from a detached clone that fetches the old main and lands nothing). The `workspace.py` pool lives under `$TMPDIR` (`dsf-ws`, or `dsf-ws-<uid>` when the temp dir is not this user's own, e.g. Linux `/tmp`; a symlink or another user's folder there is refused), which macOS purges daily of regular files whose creation and last access are both over 3 days old, keeping directories; a read renews a file only when it was written since its last read, so files age from their last write. Linux temp is `/tmp`: often a tmpfs every reboot empties, or aged out by systemd-tmpfiles (~10 days). Slot copies, their manifests and proof evidence vanish; each flow's `state.json` lives in the XDG state home (`$XDG_STATE_HOME` or `~/.local/state`, under `dsf-ws/`) and survives both, so a binding keeps its slot: a copy that vanished with its manifest resyncs into that same slot, and one whose manifest vanished while files remain (an edit, or any file written in the last 3 days) is refused until `--fresh` or `gc`. Copy evidence worth keeping out at cycle close; after an idle stretch `gc` the flow before reuse (`gc` cleans only the checkout it runs from, its state home folder included).
- **A split suite is not a coverage gate on a live tree.** Parts that combine below 100% while one full run is 100% = split artifact first: a split recomputed per part on a tree another session edits reshuffles bins, so some modules run in no part. A module at 0% cannot come from a killed tracer (xdist collection imports every module on every worker). Freeze the module lists once, assert their union equals the full collected list, gate a `head-<slug>` copy (`work.py new head-<slug>`, then `work.py run head-<slug> -- ...`, then `work.py rm head-<slug>`); a statement count that changes between parts = source moved under the run.
- **Warnings are errors** (`filterwarnings = error`). Never weaken. `tests/conftest.py` closes async SQLite connections that would leak `ResourceWarning`; root `conftest.py` same for Postgres. Test extension hooks are generators: a plain-method hook goes through Strawberry's `from_callable`, whose `asyncio.iscoroutinefunction` call is deprecated on the venv's Python and fails the test that reaches it.
- **Coverage:** `fail_under = 100`, `django_strawberry_framework` only. Example apps/tests run, never count. `pragma: no cover` only for runner-unreachable branches. Statement coverage can't see fail-open EXPRESSIONS (`max(x, 0)`, `getattr(..., default)`, `x or fallback`, broad `except`); find by reading, BUILD.md "Fail-open shapes".
- **Order independence is a contract.** Fakeshop schema composes all apps; harness reloading one app after `registry.clear()` → order-dependent `LazyType KeyError` / `DuplicatedTypeName`. Use `examples/fakeshop/schema_reload.py`; adding an app → grep WHOLE test tree for private schema-module lists, sync each. Invisible in isolation, single-worker, `-n0`; verify w/ the full parallel suite in GitHub Actions.
- **Channels communicator tests:** `django_db`-marked + `wait()`, else order-dependent flake.
- **Postgres surfaces pk-magnitude bugs SQLite hides.** SQLite per-test DBs = single-digit pks forever; PG sequences never rewind. PG-tier test failing order-dependently but passing alone = pk-magnitude bug before pollution. Repro: `ALTER SEQUENCE ... RESTART WITH <big>` in one test.
- **Attribute a failing SELECTION at pristine HEAD.** Pollution rides the selection; rows failing in a 3-module run pass alone. Re-run same selection in a copy at HEAD (`work.py new head-<slug>`, then `work.py run head-<slug> -- pytest -n0 --no-cov -p no:randomly <selection>`, then `work.py rm head-<slug>`: `gc` removes only landed copies), never by reverting files one at a time. The copy must import the package from itself: on the shared `.venv` the editable install resolves the live repo first, so a run there measures nothing; `work.py run` asserts it before the command runs. basedpyright in a copy needs `extraPaths = ["."]` on the `examples/fakeshop` execution environment, or it checks the examples against the live package. The copy (a detached clone, or `--worktree`) carries an index of its own, so `tests/test_ci_governance.py`'s census rows and `build_kanban_tracked_path_constants.py --check` read its files, not the shared checkout's.
- **Uncovered line = claim nobody tested.** Read the claim before a test blesses it; branch may be uncovered because its reasoning is wrong. Two agents disagree on a boundary → settle vs live code, never average, never confidence.
- **Soft-dep absence:** `sys.modules[name] = None` via `tests/_soft_dependency.py`. Never patch `builtins.__import__` (guards use `importlib.import_module`; block silently passes).
- **Env knobs** (`examples/fakeshop/config/settings.py`): `FAKESHOP_SHARDED=1` → adds `shard_b` (`db_shard_b.sqlite3`) beside `default` (`db.sqlite3`), un-skips sharded tests. `FAKESHOP_PG_DSN=postgres://...` → `default` = Postgres, un-skips `@pytest.mark.pg` (needs `--group pg`). `DJANGO_STRAWBERRY_KANBAN_DB=<path>` → render scripts read a COPY of board DB. Sharded ⊥ PG.
- **CI tiers:** `django.yml` sqlite, every push/PR, two shard jobs per cell, `coverage` job owns coverage. `postgres.yml` manual + weekly (Mon 05:53 UTC), path-disjoint shards, oversubscribed workers, no coverage. `kanban-pages.yml` republishes board to Pages when INPUTS change. `dependency-audit.yml` osv-scanner over `uv.lock`, daily. `publish.yml` `v*` tag → `uv build` + tag-vs-`__version__` check → `pypi` environment approval → Trusted Publishing upload (no token; PyPI's publisher binding names the file and the environment). Every CI `uv sync` is `--locked`; `postgres.yml`'s upgrade sync is the exception (its comment owns the reason); `tests/test_ci_governance.py` owns the rules. Dependabot rewrites `uv.lock` + action SHAs weekly; re-read its branch after every rebase (floor-raise vs lock-only can flip).

## Pre-commit and CI gates

Local hooks, `.pre-commit-config.yaml`, run order. All via `uv run` (shared ruff). Config file wins over this list.

1. **kanban-tracked-path-constants** (`scripts/build_kanban_tracked_path_constants.py`) — REWRITES constants module from `git ls-files`. Add/delete a tracked package/test file → the hook rewrites the module and fails the commit until the rewritten module is staged too. `always_run: true`, `pass_filenames: false`, no `files:` key (deleted paths never appear in the staged list). Sees a new file only once STAGED; `--all-files` before `git add` proves nothing. Unblock: `git add` the rewritten constants module alongside the add/delete, rerun the hooks, commit once; no constants-only sync commit.
2. **source-layout** (`scripts/check_trailing_commas.py --fix`) — trailing-comma explode-at-threshold (4; 2 in `models.py`), ASCII-only `.py`, `.md` link-def scaffold, JSON/GraphQL brace explosion. Auto-fixes, looping comma edit + `ruff format` to a fixpoint (no fixpoint = `unfixable` error); a rewrite fails the run so you re-stage. Refuses to explode a line ending in `# noqa` / `# pyright: ignore` / `# type: ignore` (`unfixable`): put the suppression on the element. ASCII rule `.py`-only; em dashes fine in `.md`. Ruff interplay: [docs/ruffing.md][ruffing] "Custom formatter interplay".
3. **ruff-check --fix**, 4. **ruff-format**.
5. **basedpyright** (`uv run basedpyright`, whole scope, `pass_filenames: false`) — fires on any staged `.py`, `pyproject.toml` or `uv.lock` (a lock-only stubs bump moves the verdict); a signature change reddens callers in files you aren't committing.
6. **basedpyright-floor** (`uv run basedpyright -p pyrightconfig.floor.json`) — the same scope at 3.10; fires on the `basedpyright` hook's files plus its own config.
7. **check-type-suppressions** (`scripts/check_type_suppressions.py`, whole tree, `pass_filenames: false`) — refuses an ignore naming a rule `[tool.basedpyright]` marks `# Locked`, any file-level `# pyright:` directive, and any per-site count off the generated ledger `scripts/type_suppressions.toml` (site = innermost `path::QualifiedName`; kinds = `cast` and each ignored rule) in EITHER direction: above or at an unlisted site = fix the diagnostic, below = run `--write` in the same change. `--write` only lowers or drops entries; `--write --allow-new` records a new or moved suppression (a renamed symbol moves its entries), a deliberate line in the ledger diff. Never edit the ledger by hand. CI adds `--since <pushed-over commit or PR base>`: a commit raising any kind's total (casts, or one rule's ignores) fails unless its message carries a `Suppression-Growth-Approved: <reason>` trailer; a move between sites keeps the totals and passes. A rule cleared to zero leaves the ledger and, once on in every environment, gains `# Locked`.
8. **check-public-types** (`scripts/check_public_types.py`) — basedpyright's trigger + its own source (allowlist edit); installs the package NON-editable in a temp env and requires `basedpyright --verifytypes` at 100% with zero diagnostics (warnings included: a public symbol's missing docstring or `...` default fails it) outside its exact-match `ALLOWED_DIAGNOSTICS`, each entry w/ its reason; an entry no longer reported fails as stale.
9. **truthful-reads** (`scripts/check_truthful_reads.py --check`) — identity facts about consumer objects read through `django_strawberry_framework/utils/truth.py`, never by dunder attribute lookup, `getattr_static` or an `in` test of `type(x)`, and whether a subclass overrides a base's hook through `truth.overrides`, never an `is` between two class-attribute reads; no handler (or `contextlib.suppress`) swallows `BaseException`/`SystemExit`/`KeyboardInterrupt`/`GeneratorExit`, no `finally` exits early. Package-wide from `[tool.truthful_reads]` in `pyproject.toml` (`pass_filenames: false`; fires on a staged package `.py`, the gate script, or `pyproject.toml`). `# truth: ok <reason>` on the flagged line suppresses it; `--report` lists every marker plus the report-only heuristics.
10. **annotation-subscripts** (`scripts/check_annotation_subscripts.py`, whole package, `pass_filenames: false`) — no package annotation (parameter, return, annotated assignment at any scope, string annotation, unquoted `typing.cast` argument) subscripts a class without a runtime `__class_getitem__` absent `django_stubs_ext` (`Options`, `Field`, `Lookup`, `ModelForm`, ...) where anything can evaluate it: subscript it in a module-private `if TYPE_CHECKING:` alias with a bare-class `else:`. Evaluated subscripts resolving to Django imports (including constructors, base classes, default arguments and function-local assignments) are checked too; ordinary container indexing is outside that expression sweep. A never-evaluated site (function-local annotation, `if TYPE_CHECKING:` body) passes only at its audited count in the script's `AUDITED_SITES`; an unaudited subscripted name fails closed until `SUBSCRIPTABLE` lists it, and `tests/base/test_init.py` re-audits that table at runtime on every CI cell.
11. **check-kanban-anchors** (`scripts/check_kanban_anchors.py`) — card↔card slug, card↔glossary anchor, render-id collisions. Reads DB → fires on a retitle no staged file names.
12. **import-spec-terms-check** (`manage.py import_spec_terms --check --skip-checks`) — every done card's glossary rows equal its terms CSV. Reads DB + CSVs → always runs.
13. **check-spec-glossaries** (`scripts/check_all_spec_glossaries.py`) — `check_spec_glossary.py` over EVERY spec (`docs/spec-*.md`, `docs/SPECS/spec-*.md`) and its terms CSV: each row's anchor is a rendered `docs/GLOSSARY.md` heading the spec links, no anchor repeats; a terms CSV no spec owns fails by name. In-process, whole tree, always runs (a `GLOSSARY.md` heading rename fails a spec nobody staged).
14. **check-citations** (`scripts/check_citations.py --substrings`) — every `path::Symbol`, `spec-NNN Decision N` and `#"substring"` pinpoint in first-party source, the board and the spec corpus (`docs/spec-*.md`, `docs/SPECS/**/*.md` incl. `appx/`, minus the process doc `docs/SPECS/NEXT.md`) must resolve, a Decision against a `Decision N` heading in the spec of that number (rationale companions don't count); in board and spec text a cited file or spec that does not exist yet is no signal (planned work), an existing file missing the symbol or spec missing the heading fails; a pinpoint's quoted text must occur in the cited symbol's source span (`path::Symbol #"..."`) or anywhere in the file (`path #"..."`), and one occurring more than once only warns. Runs last, whole tree (a rename rots citations in files you aren't committing). Other `docs/` prose out of scope. A citation wrapped across two lines is joined (break after `::` or `/`, before `::` or `#"`, around `Decision`), except two spellings that fail in every corpus whatever they cite: a `#"` pinpoint whose quote does not close on its line, and a bare file path split after a `/`. A split after a `.` inside a symbol stays invisible (reads as a sentence end).

CI `lint` job (`django.yml` is authoritative for the order): `ruff check` / `ruff format --check`, `basedpyright`, the floor `basedpyright -p pyrightconfig.floor.json`, `check_type_suppressions.py`, `check_public_types.py`, source-layout `--check`, truthful-reads `--check`, annotation subscripts, citations `--check --substrings`, tracked-path constants `--check`, kanban anchors, `import_spec_terms --check`, `check_all_spec_glossaries.py`, then `--check` on every generator (`build_kanban_md`, `build_kanban_html`, `build_glossary_md`, `build_tree_md`). Hand-edit to a rendered doc goes red THERE, not locally.

`--check` measures WORKING TREE. Passes in a dirty tree w/ stale HEAD → CI red, local green. Measure HEAD: `work.py new head-<slug>` and run the generator's `--check` inside that copy (`work.py run head-<slug> -- python <generator> --check`), then `work.py rm head-<slug>`. Swapping only `DJANGO_STRAWBERRY_KANBAN_DB` to a HEAD database still executes dirty renderer code, settings, migrations and, for `TREE.md`, dirty module docstrings, so it cannot say what HEAD renders.

- **The git hook stashes.** Run as the commit hook (no `--files`), pre-commit stashes unstaged changes around its run, momentarily reverting another session's work on disk; `run --files <paths>` never stashes. In a concurrently dirty tree: `uvx pre-commit run --files <staged paths>` by hand, then commit `--no-verify`.
- **`--no-verify` skips hook 1 and nothing renders `TREE.md`.** After adding/removing a tracked file, run `build_kanban_tracked_path_constants.py` and `build_tree_md.py` by hand. Both read the INDEX (`git ls-files`), so in a private-index commit that adds a file run them and their `--check` w/ `GIT_INDEX_FILE=<private idx>` (+ `DJANGO_STRAWBERRY_KANBAN_DB=<scratch copy>`). `git diff --check` has the same untracked-file blind spot.
- **Verify a carved commit by running it.** Materialize the commit's tree (`git write-tree` of the private index, then `git commit-tree`) into `work.py new carve-<slug> --worktree --from <that commit>` and gate there. A hunk mixing your comment edit w/ their executable change splits line by line. `KANBAN.html` embeds each row's `updatedDate`: regenerate after the final DB replay.

## `scripts/`

`uv run python scripts/<name>.py`; `--help` = flags + defaults. Module docstring is the manual; this is the map.

| Script | Use |
|---|---|
| `build_kanban_md.py`, `build_kanban_html.py` | render `KANBAN.md` / `KANBAN.html` from kanban DB (`--check`; `--md`/`--html` write elsewhere). HTML Vue shell hand-edited; only data block regenerates |
| `build_glossary_md.py` | render `docs/GLOSSARY.md` from glossary DB |
| `build_tree_md.py` | render `docs/TREE.md` from module docstrings + board predicted-path rows; missing module docstring fails it |
| `build_kanban_tracked_path_constants.py` | hook 1; run after adding/removing any tracked package/test file |
| `check_trailing_commas.py` | hook 2; `--check` CI, `--fix` local (loops to a fixpoint or exits `unfixable`); owns `EXEMPT_MD_SCAFFOLD_NAMES`, `LINK_DEF_CATEGORIES`. Default = repo-wide AUTO-FIX → always pass explicit paths (else rewrites other session's untracked files) |
| `check_type_suppressions.py` | hook 7; CI lint. Locked rules, no file-level directive, the per-site ledger (`scripts/type_suppressions.toml`); whole tree only. `--write` lowers the ledger, `--write --allow-new` records a new or moved suppression; `--since REV` (CI) refuses a commit raising a total without the `Suppression-Growth-Approved:` trailer |
| `check_public_types.py` | hook 8; CI lint. Builds its own non-editable env (`--verifytypes` can't see the editable `.venv`); a fresh env w/o `--reinstall-package` gets uv's cached build of OLDER source |
| `check_truthful_reads.py` | hook 9; `--check` CI; `--report` = full inventory (tier-2 heuristics, every `# truth: ok` marker, per-code/per-file counts), exit 0. Reads `paths`/`exempt` from `[tool.truthful_reads]` |
| `check_annotation_subscripts.py` | hook 10; CI lint. Static sweep for a subscripted class without a runtime subscript hook; owns `SUBSCRIPTABLE`, `CHECKER_ONLY`, `AUDITED_SITES` |
| `check_citations.py` | hook 14; `--check --substrings` CI |
| `check_kanban_anchors.py` | hook 11 |
| `check_spec_glossary.py --spec <path>` | one spec's `-terms.csv` → real glossary anchors (a link counts only where it renders); `--auto-link` links each term's first open prose mention (NEXT.md) |
| `check_all_spec_glossaries.py` | hook 13; CI lint. `check_spec_glossary.py` over every spec + its CSV in one process, never `--auto-link`; fails on a CSV no spec owns; `--root <dir>` for another checkout |
| `check_alpha_parity.py` | every non-internal Alpha card carries parity link + justification |
| `prove_failability.py <manifest.json>` | mutate boundary, run, restore, prove by byte compare. THE way to prove a test can fail. Scope each entry to the tests that exercise the mutated boundary (every entry reruns its scope; four test trees per entry costs minutes each); one blocking command, no polling waiters |
| `workspace.py run <flow>/<item>/<role> [--cell] -- <cmd>` | agentflow workspace copies (REVIEW, HUNT, DRY): reusable per-flow pool outside the tree, exact mirror of the shared tree + own `.venv` + own databases (per-copy Postgres DB), clean env, observed provenance header + run id; `prove`, `path`, `diff <ITEM_BASELINE> [--output F | --check F] -- <paths>` (the item diff: the working content vs the baseline tree, new files included (a name `is_excluded` reports keeps its baseline blob), independent of the index for every file git does not ignore (only a force-added ignored file counts), sha256-sealed; `--check` re-verifies), read-only `audit`; Worker-0's `baseline`/`release`/`gate` (CI's lint job by default; the default, floor, sharded and pg suites only when `--suites` names them, since they run in GitHub Actions)/`gc`. A stop signal (INT/TERM/HUP/QUIT) to the wrapper alone stops the command first (relayed to its whole process group; the run then ends by that signal); Ctrl-Z suspends the command with the wrapper and `fg` resumes both; the run's leases last while the command runs, even past a SIGKILLed wrapper, and a process it leaves running (`cmd &`) keeps them until it ends. Never copy the tree by hand |
| `fleet_sync.py [status\|sync\|handoff]` | keep every fleet machine's `.work/` copies, pins, evidence and main in step over Tailscale + ssh ("Syncing the fleet"); module docstring = the full rule |
| `work.py <command> <name>` | private working copies (`new`, `adopt`, `list`, `save`, `land`, `rm`, `gc`, `repair`, `run`, `check-name`) under `.work/` ("Private working copies"); module docstring = the full rule |
| `review_inspect.py <file> --output-dir <scratch>/inspect` | AST-only overview + stripped source (`--all` = package); never imports. `--code-digest <rev>:<path> <path>` = docstring-stripped AST digest, the one-command inverse proof for a prose-only edit. Always pass `--output-dir` into the session scratchpad: the script's default writes flat into `docs/shadow/`, whose four subfolders each have one owner (AGENTS.md) |
| `review_historical_package_snapshot_at_commit.py <sha>` | package snapshot at commit → `docs/shadow/current/` |
| `review_changed_python_diffs_against_head.py <sha>` | stripped per-file diffs commit→HEAD → `docs/shadow/old|new|diff/` |
| `bug_hunt.py` | generates `docs/bug_hunt/bug_hunt-<ver>.md` progress file (HUNT.md) |
| `list_package_python_changes_by_commit.py` | package `.py` files per commit, for spec attribution |
| `clean_up.py` | deletes cycle scratch (`docs/shadow/`, `temp-tests/`, `worker-memory/`, `bld-*.md`, `bug_hunt-*.md`). `bld-*.md` glob also eats deliberately-kept finals + other cycle's live artifacts → never use to tidy a cycle; delete by explicit path |
| `bench_plan_cache.py`, `bench_optimizer_walk.py`, `bench_nested_fetch.py` | optimizer benches (plan cache warm/cold; walker cold path; nested-fetch strategies on PG) |
| `count_queries.py` | one operation's query count at several parent cardinalities + verdict (`batched` / `scales with cardinality`); `--compare` before/after |
| `importtime_report.py --rounds 5` | per-module import-time minimum across rounds, never a single `-X importtime` reading |
| `review_plan.py` `plan`, `resume`, `scope`, `reconcile` | REVIEW plan generator (`--changed` = the release's own committed changes) + inventory reconciler |
| `census_test_models.py` | counts Django model classes declared under `tests/`, closing over MTI/proxy bases |
| `_kanban_lib.py`, `_bench_common.py`, `_plan_common.py`, `_markdown_lex.py`, `_git.py` | shared plumbing, not entry points; `_markdown_lex.py` = the stdlib-only CommonMark lexer both glossary-link writers share (`build_kanban_md.py`, `check_spec_glossary.py`); `_git.py` = the one git runner every script reads the checkout through (repository config only, caller's `GIT_INDEX_FILE`/`GIT_DIR` and `safe.directory` trust kept, `status` never rewrites the index) |

## Rendered docs — fix the source

Generated; hand edits clobbered next render + CI generator `--check` red:

- [docs/TREE.md][tree] ← module docstrings + kanban DB predicted-path rows.
- [docs/GLOSSARY.md][glossary] ← fakeshop `glossary` app DB (`GlossaryTerm` bodies). Shipping slice folds behavior in via DB, then renders.
- [KANBAN.md][kanban] / `KANBAN.html` ← fakeshop `kanban` app DB: `BoardDoc` = prose, `Card` = identity, `CardItem`/`CardReference`/`ParityClaim` = bodies + links.

```shell
uv run python examples/fakeshop/manage.py shell -c "<ORM edit>"
uv run python scripts/build_kanban_md.py && uv run python scripts/build_kanban_html.py
uv run python scripts/build_glossary_md.py && uv run python scripts/build_tree_md.py
```

- `examples/fakeshop/db.sqlite3` = tracked source for both apps + concurrent-writer hotspot. Same-size binary diff ≠ no-op: compare `iterdump()` by table vs `git show HEAD:`, leave foreign rows, disclose what rode along. Never `git checkout` it as "tool drift". Hand-edited render? Re-render, compare bytes; never infer from dirty list. Any script outside pytest, even on `config.test_settings`, runs against this tracked file: a migrate, seed or `.delete()` there rewrites committed rows (one `Branch.objects.all().delete()` cascaded to tracked shelves and books) and shows only as a same-size binary diff. Point `DJANGO_STRAWBERRY_KANBAN_DB` at a scratch copy before anything that writes, and tell dispatched agents so.
- DB edits: script in scratchpad piped into `manage.py shell`. `shell -c '<single-quoted>'` can't carry apostrophes → mangled chars in render. Guard inserts w/ marker-absence assert (re-run can't duplicate). A board row: `apps.kanban.services.append_card_item(card, Section.objects.get(key="scope"), text)`, then both KANBAN builders, then `check_kanban_anchors.py`.
- DB stores only each bullet's FIRST line; multi-paragraph items lost on import. A claim you expect on the board may never have been imported.
- Never write literal `{{card_ref:N}}` into stored prose, even in backticks (md render resolves server-side, HTML shell by numeric index). Card ids in prose = FK-backed placeholders, can't rot; only literal ids typed in text are a sweep population.
- `KANBAN.md` (and every spec) is in citation gate corpus: `path::Symbol` in a card item checked every render, must name DEFINING class, can't quote another doc's illustrative citation.
- Two glossary gates, different inputs: `check_spec_glossary.py` → RENDERED `GLOSSARY.md` headings; `manage.py import_spec_terms --check` → DB. A rendered H2 may be a section heading w/ no `GlossaryTerm` row. One row per anchor (the model forbids two terms per anchor; `check_spec_glossary.py` refuses a repeat). Every done card's `GlossarySpecMention` + `CardGlossaryTerm` rows are a copy of its terms CSV: a CSV edit, a spec archive or a card flipped done owes the writing `manage.py import_spec_terms` in the same change (it writes only rows that differ); `--check` (hook 12, CI lint) names every row that run would change.
- A renumber keeps a card's pk and `Card.uuid` (its `UUIDModel` side-row); `card_id` = property over `number`, not a column, so it changes. Pre-map by pk/title, retarget refs in place, use `services.move_card_number`. Done cards always contiguous, completion order.
- Card numerals rot in 3 grammars: card ids, `spec-NNN` stems, bare prose numerals (incl. `CardReference.raw_text`, `Card.planning_note`). Renumber sweeps all 3 + regenerates `docs/TREE.md`.
- Board items cite docs by `path #"substring"`. Move/reword quoted text → broken; hook 14 fails the board row (the same pinpoint in other `docs/` prose stays ungated). Grep `spec-<NNN>` + quoted substrings across `docs/` BEFORE moving text. Cite stable neighbourhood, never the phrase a catalogued fix will rewrite.
- `is_blocked` ignores Done targets: `blocked_by` → shipped card renders unblocked. Retype to `dependency`, reword.
- `BigAutoField → Int` + duplicate GraphQL name in kanban schema: intentional, load-bearing. Don't "fix".

## Agentflows

Five standing process docs. The maintainer invokes by name ("run the builder on the active spec", "start a DRY cycle"); none self-starts. All re-read AGENTS.md + this file first, none commit, each closes own scratch.

| Flow | Doc | Does | Per-cycle artifacts |
|---|---|---|---|
| **Spec authoring** | [docs/SPECS/NEXT.md][next] | strict ordered steps: orient, summarize, normalize board to exactly one WIP card, write `docs/spec-<NNN>-<topic>-<0_0_X>.md` + `-terms.csv`, anchor terms to glossary, archive prior specs → `docs/SPECS/` (+`appx/` companions), rewrite every xref | new spec at `docs/` |
| **Builder** | [docs/builder/BUILD.md][build] + [ARTIFACT.md][artifact] + `worker-0..3.md` | spec slice by slice. W0 (main thread) dispatches fresh subagents per pass: W1 plans/owns spec/final-verifies, W2 implements, W3 reviews + DRY. Artifact `Status:` drives dispatch. Pre-flight moves spec rationale → `-rationale.md` (smaller spec per spawn). Failability proofs, floor verification, hot-path budget, review rounds under ownership partition, cross-slice integration, closeout | `docs/builder/build-<NNN>-*.md` (plan), `bld-*.md`, `temp-tests/`, `worker-memory/` |
| **Review** | [docs/review/REVIEW.md][review] + `worker-0..2.md` | `Execute docs/review/REVIEW.md (You are Worker-0)` [`scope: <paths>`]: three axes (Performance, Mechanics, Comments) per package file; W0 coordinates, three W1 review one axis each and record Proof lines before any edit, W2 implements all three axes in order, fresh W1s verify expectation-first; default scope = the release's committed changes (`review_plan.py --changed`); folder + project integration passes; final `workspace.py gate review` | `docs/review/review-<ver>.md` (plan + baselines + ledger + outcomes), `rev-*.md` (main artifact + one record per axis), `temp-tests/<stem>/`, `workspace.py` copies |
| **DRY** | [docs/dry/DRY.md][dry] + `worker-0..2.md` | `Execute docs/dry/DRY.md (You are Worker-0)`: autonomous three-role consolidation cycle (W0 coordinates, W1 traces + consolidates, fresh W2 verifies expectation-first) + design principles every builder pass reads; responsibility families over a file-inventory backstop; mandatory probing matrix; change challenge counts authoritative definitions only (consumers, oracles, projections listed, not counted); owner chosen by responsibility; finding record w/ behavioral proof, structural gate + freshness fingerprints; cycle-owned edits ledgered, attributed by content; rejections carry contract difference + trigger, recorded at the owner; `docs/dry/export_dry_review.py plan|audit|check` = plan (release from the package) + orientation, never findings | `docs/dry/dry-<ver>.md` (plan + cycle baseline + responsibility index + owned changes + outcomes = durable record), `dry-file|rule|folder-*.md`, `dry-project.md`, `temp-tests/`, `worker-memory/` |
| **Bug hunt** | [docs/bug_hunt/HUNT.md][hunt] + `worker-0..2.md` | `Execute docs/bug_hunt/HUNT.md (You are Worker-0)`: autonomous three-role hunt (W0 coordinates + mechanical evidence checks, W1 hunts in a disposable workspace copy + fixes, fresh W2 verifies expectation-first); contract row before every probe; file items = inventory, standing + discovered scenario items = cross-file contracts; evidence record per claim; `dicta.md` = maintainer probing questions | `docs/bug_hunt/bug_hunt-<ver>.md` (progress + cycle baseline + owned changes + outcomes = durable record), `temp-tests/`, `workspace.py` copies |

Shared mechanics:

- **Isolation non-waivable.** Author never approves own code. Workers never read each other's `worker-memory/` mid-cycle; all info via artifact + diff.
- **Claims proven mechanically.** Passing suite = evidence only if it could fail (`prove_failability.py`). Review's prescribed fix = hypothesis. Finding's grep vocabulary ≠ its population; re-derive a catalog before acting.
- **Builder corpus grows by mechanism, never restatement** (BUILD.md "corpus ratchet"): any edit to `BUILD.md`/`ARTIFACT.md`/`worker-*.md` reports `wc -c` before/after + names what it subsumes. Never edit a process doc while a worker is mid-pass. Role files = pointer + role delta, never restated procedure.
- **Failability aggregates OUTSIDE the guard under test.** Inside, guard absorbs the failures being measured; plausible-wrong count graded by nobody.
- **Harvesting items from a doc about to be deleted** = enumerate-and-tick over source's own numbering, then grep each item at destination w/ a NAMED owning card. Section sweep looks complete, leaves items unhomed.
- **Ad hoc agent sweeps (outside the five flows).** Digging report first, the maintainer decides; implementers get DISJOINT file ownership and one shared brief file in the scratchpad. Before an implementer's context dies, SendMessage it for helpful / misleading / missing; fold the answers into the standing doc; have one fresh agent use the doc cold; vet that agent's findings against the code and act only on what is true.
- **Per-cycle scratch closes w/ cycle.** `review-*.md`, `rev-*.md`, `dry-*.md`, `bld-*.md`, `build-*.md` (live + `DONE/`), `bug_hunt-*.md`: exempt from `path::Symbol` rule (raw `path:NN` OK), no style cleanup. Include in repo-wide greps for drift; edit only if cycle in flight. `clean_up.py` removes generated ones only.
- **Closeout consistency.** Shipped card: realign opener + `Status:` (boxes stay unticked; Status = truth); correct wrong Decision/Test-plan/DoD prose. Clean `git status` ≠ finished cycle; read artifact `Status:` chain.

## docs/

| Path | Purpose |
|---|---|
| `docs/README.md` | consumer how-to (install, quick start, read/write, transport, production profile) |
| `docs/GLOSSARY.md`, `docs/TREE.md` | rendered, see above |
| `docs/spec-*.md` (+`-terms.csv`, `-rationale.md`) | THE one in-flight spec + companions; invariant = exactly one WIP spec at top level |
| `docs/SPECS/` | archived specs + `NEXT.md`; `appx/` = their companions. Link defs for `appx/` still under `<!-- docs/SPECS/ -->` |
| `docs/builder/` | builder flow: `BUILD.md`, `ARTIFACT.md`, `worker-0..3.md` (tracked standing); active `build-*.md` + `bld-*.md` (tracked, active cycle only); `DONE/` (closed plans); `temp-tests/`, `worker-memory/` (untracked scratch) |
| `docs/review/` | `REVIEW.md`, `worker-0..2.md` + per-release `review-<ver>.md`. Committed truth: never bulk-delete/overwrite; restore `git checkout HEAD -- docs/review/` |
| `docs/dry/` | `DRY.md`, `worker-0..2.md` (tracked standing); `export_dry_review.py`; `dry-<ver>.md` (tracked plan, the cycle's durable record); `dry-file|rule|folder-*.md`, `dry-project.md` (per-cycle artifacts); `temp-tests/`, `worker-memory/` (untracked scratch) |
| `docs/bug_hunt/` | `HUNT.md`, `worker-0..2.md` (tracked standing); maintainer `dicta.md` (stays); generated `bug_hunt-<ver>.md` (the hunt's durable record); `pbugs.md` (leads w/ provenance); `temp-tests/` (untracked scratch) |
| `docs/shadow/` | regenerable static-analysis output; sibling folders, one owning script each (`current/` ← snapshot; `old|new|diff/` ← diff). Read-only; never commit or cite its line numbers |
| `docs/feedback*.md` | maintainer review inputs for in-flight work. Staged WITH the work they drove; never named in commit message, code, or DB |
| other loose `docs/*.md` | standing design records for subsystems that outgrew a spec; each opens w/ its own purpose statement |

## Example project

`examples/fakeshop/` = acceptance fixture + board DB host. **Never deploy**: `DEBUG=True`, checked-in `SECRET_KEY`, GraphiQL, toolbar, deliberate `permission_classes = []` demos. Settings refuse to load w/ `DEBUG` off.

- Apps: `library` (primary acceptance: FK/reverse FK/O2O/M2M, Relay, optimizer hints, FilterSet/OrderSet on every type), `products` (canonical consumer app, TODAY.md; all mutation flavors), `scalars` (converter table, file/image, `Upload`), `accounts` (session auth), `kanban` + `glossary` (docs-as-data).
- Commands: `seed_data`, `create_users`, `delete_data`, `delete_users`, `seed_shards` (products); `import_card_files --kind changed|predicted` (kanban); `import_spec_terms` (glossary).
- `config/schema.py` composes all apps into one `DjangoSchema`. Change app list → sync every schema-module list harnesses carry (`schema_reload.py`, test READMEs).
- `graphql_client.py` sync-only, no shared async helper; async suites drive `django_strawberry_framework.testing.AsyncTestClient` against their own `AsyncDjangoGraphQLView` mount + `django_db(transaction=True)` + registered types; a bare `AsyncClient` post owes a stated exemption.
- Choices = `TextChoices` (`library/models.py`); text columns = `TextField`.

## Instruments that lie

Each produced a clean-looking pass while measuring nothing. Check instrument before reading.

- **Walkers that ignore `.gitignore` see every copy.** The agent shell's `find` (bfs), a harness's file glob and a bare `rglob` from the root descend `.work/`; a hit under `.work/clones/<name>/` is that copy's file, not the shared one. VS Code excludes it in `.vscode/settings.json`; `rg`, ruff, basedpyright and the repo's walkers honour the ignore file or prune dot folders.
- **zsh word-splitting.** `for f in $FILES` = ONE iteration, whole string; grep errs to stderr; sweep prints nothing ≡ clean repo. Array: `files=(${(f)"$(...)"})`. Quote globs (unmatched glob aborts). Always print population size. No `timeout` here. A word starting `=` is a command lookup (`echo ======` errors: "= not found"); quote it. Multi-file sweeps: `uv run python - <<'PY'` heredoc, assert the count.
- **Shared sqlite cursor.** One cursor for outer `sqlite_master` loop + inner query → outer result set discarded after table 1 → "no hits, 0 skipped". `.fetchall()` outer first; print tables/columns examined; positive control (rendered artifact carries the string ⇒ DB does).
- **Positive-vocabulary census.** Sweep for `only`/`sole`/`no other` misses `every`/`all`/`each`. Both polarities. Don't swap a rotted census for a fresh one: quantify over the file's own closed set (`_meta.local_fields`), not a population it can't see.
- **`git log -S<symbol>`** fail-open for "when did this ship" if symbol had an earlier name. Attribution from it = hypothesis.
- **`for` loop inside one test = ONE node id.** Widening loop never raises failability count above 1; parametrize. Never assert cardinality fixture size can satisfy by accident; assert id-list membership.
- **`--check` in dirty tree** measures working tree (see gates).
- **Control that cannot fail** ≡ passing proof; control that didn't run ≡ one that passed. Control mutation from EXECUTABLE code (docstring token can't move a docstring-stripped digest); break it, watch fail, restore. Comment/docstring-only edit owes INVERSE proof: AST identity w/ docstrings stripped. Its reference is a pre-edit copy, never `git show HEAD:` when a concurrent session holds executable hunks in the same files; a control in one file says nothing about the others; an anchor occurring 0 times aborts the control, never reads as a pass.
- **`prove_failability.py` restores from a copy taken before it mutated.** An edit to the target (or any file in the running scope) while an entry is live is silently reverted at restore, and the byte compare still passes. A live proof run locks those files; re-grep your own edit afterwards.
- **`grep` in the agent shell is a function wrapping ugrep.** A left-anchored `(^|[^A-Za-z0-9_-])TOKEN` alternation returns 0 where `rg` and `command grep` find the hits; the false 0 reads as a finished sweep. Use `rg` (or Python) for any published figure.
- **Census blind spots.** Unbounded right edge (`M2` inside `M2M`); a right `\b` that misses `P3a`; per-line matching misfiles a citation wrapped across two lines; ASCII `-` vs en-dash ranges; a vocabulary glob blind to half its population (`Md1`, `SR-3`, bare `High`); a spec glob missing `appx/` AND ids outside its numeral range (two blind spots at once: naming one leaves the other); a HEAD figure for a MIXED file read from the working tree (read `git show HEAD:`). Positive control that must return >0, plus a second instrument built differently. A ratchet or manifest comes from measured imports at HEAD, never a dispatch list or a spec's own table.
- **A live count of a population the same write edits** is wrong on arrival; summing a DB w/ its own renders counts one fact three times. Date the count, exclude the recording surface's own occurrences.
- **A negative-control token published in the artifact that uses it** makes the rerun return 1, not 0. Randomize the token per run; never publish the literal.
- **`strings db.sqlite3 | grep -c` counts freelist residue** no query returns. Count board text through the ORM (`CardItem.text`).
- **Count right in every digit, wrong in SUBJECT.** Focused-run scope promoted to "what the card owns" passes arithmetic. State owned population + run scope separately. Stub's lost contract often in a deleted planning doc: `git show <commit>^:<path>`.
- **Round's self-reported deferral = claim.** Re-derive before homing.
- **Derived descriptions outlive sources.** Reconciliation defects = false descriptions of findings, not missed facts. Describe by content, never line number.
- **Partial claim fix = dominant residual defect.** One spelling fixed, parallel site (other README, glossary body, board item) still live → cycle reopens. Shortest DISTINCTIVE phrase, count occurrences (not lines: two hits/line read as one), prove retirement = 0.
- **Green checker = evidence only for what it reads.** Two gates agreeing ≠ corroboration when one can't see the other's failure. State instrument input before trusting output; state PATTERN as parameter of any published figure.
- **Enumerate, never grep-count, before writing.** Assert every site exists before touching any; partial match aborts w/ nothing written.
- **Retiring a per-cycle artifact strands inbound refs.** Same pass: de-link to code span keeping prose, or retarget standing pointer at `git show <commit>:<path>`. Re-audit orphaned defs / undefined refs.
- **Two death commits ⇒ two pointers.** Earlier commit holds a stale copy of whatever outlived it. Archived path may also name an earlier cycle's deleted file — say which.

## Style the maintainer cares about

- **Meta classes on every consumer surface.** Stacked Strawberry decorators on a consumer-facing class = strawberry-graphql-django API = the reason this package exists. Strawberry = engine; DRF = shape.
- Model text fields = `TextField`, never `CharField`, even short. Codified in example models.
- **Workers are hyphenated:** Worker-0 / Worker-1 / Worker-2 / Worker-3, never "Worker 0", in replies and every doc. Closed history (`docs/SPECS/`, builder `DONE/`, per-cycle records) stays as written.
- **Never widen a PUBLIC parameter to `object` to keep a guard reachable.** Keep the precise type and read the guarded value through a `utils/_narrowing.py` typed read (`read_attr`, `list_of`, ...), which types it `object` and leaves the guard live; where no typed read applies, suppress the guard w/ a `# basedpyright: trust boundary: <why>` line; private helpers may take `object`.
- **No process provenance in code or standing prose.** Comments/docstrings/test names/error strings state the invariant, never how the change came to be. Banned: severity labels (High/P0/H1), review-round/worker attribution, DRY-pass/slice numbering, plan/commit banners, board residue, review-doc filenames, "as of 0.0.N", "previously". Gate: `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_carries_a_provenance_phrase` refuses `pre-fix`, `post-fix`, `before the fix`, `after the fix`, `formerly`, `exactly as before`, `used to`, `previously`, `as of 0.0.`, `the hardening pass`, `(hardened)`, `(hardening)`, `pre-0.0.`, `the old implementation`, `the previous implementation`, `task report`, `finding-`, `pre-NNN` (a three-digit spec number), `pre-1.0`, `back-compat` (and `backward(s) compatible/compatibility`), `independently grew`, `grew separately`, `historically`, `byte-unchanged`, `moved verbatim`, `net-new`, `now-fixed` and `the original implementation` in every comment, docstring, other string statement and def/class name of the sweep corpus plus every package runtime string (case-insensitive, word-bounded, matched across line wraps; no exclusion, no marker: rephrase the sentence); its sibling `test_no_comment_docstring_name_or_package_string_carries_a_release_of_this_package` refuses a release of this package (every series up to `__version__`'s) or a release-carrying card id in that same prose plus every package runtime string, the `__version__` value excepted (name the spec or the topic instead); a third row, `test_no_comment_docstring_name_or_package_string_carries_an_optimizer_plan_label`, refuses the optimizer plan labels (`B1`-`B8`, `O1`-`O6`, `G1`-`G3`, the spec-002, spec-004 and spec-035 heading names) in that same prose and package strings, def/class names read at underscores and camel-case boundaries, outside an inline code span quoting a value (name the behaviour; cite a spec-035 guard as `spec-035 Decision N`; quote a label-shaped value as its literal, ``"B1"``); the rest of this list is judged by hand. Removed attribution carried the WHY → restate as one plain clause from the code. Kept: spec decision pointers, glossary anchors, upstream tickets (Django Trac, Strawberry issues, RFCs, CVEs), audited-release-range vocabulary, live `TODO(spec-NNN slice N)` anchors. Verify a label vs its spec before deleting.
- Source refs: `path::QualifiedName`, `path::QualifiedName #"unique substring"`, `path #"unique substring"`. Never `path:NN` outside per-cycle scratch. `#"substring"` breaks on reflow AND reword (hook 14 fails it in its corpus; a quote left open at a line end is a finding too): quote text on ONE source line; never wrap a citation or a path across lines (shorten prose, not path; a path split after a `/` is a gate finding); after editing a cited file, sweep every citer as POSTCONDITION. Rationale move breaks citations in OTHER specs while links still resolve: grep `spec-<NNN>` across `docs/` before, repair same pass. Cite contract by CONTENT, never ordinal ("shape 4"); heading rewrite strands every ordinal. `spec-NNN Decision N` is the one gated ordinal: renumbering a spec's decisions owes the citers in the same change. Gate: `tests/test_ci_governance.py::test_no_comment_docstring_name_or_package_string_cites_a_spec_section_by_number` refuses a Definition-of-done, Goal or Slice ordinal (`DoD 4(c)`, `Goal 4`, `Slices 1-2`) in the sweep corpus and package strings, a live `TODO(spec-NNN slice N)` anchor excepted; a Decision's step and a module's own numbered list are judged by hand.

## Reconciling a spec with the tree

Specs = contracts concurrent work silently falsifies.

- **Specs sum to the current code; history does not matter.** Every spec, in flight (`docs/spec-*.md`) or archived (`docs/SPECS/`, `appx/` companions included), describes the code as it is NOW, and together they add up to it. Required anticipation for EVERY modification: before editing, grep `docs/spec-*.md docs/SPECS/` for each symbol, signature, setting and behavior you will touch, and in the same change rewrite every spec sentence, row, citation and example that the edit falsifies (deleted code → delete the spec text describing it; changed code → restate it as it now is; new surface → it belongs in the spec that owns the subsystem). Never a "superseded"/"previously"/"was removed in" note and never history kept for its own sake; git holds history. A spec citation to a symbol that no longer exists is a defect, archived or not.
- **A gate graded at HEAD X answers nothing about HEAD X+1.** Before saying "no spec edits needed", `git log --oneline -1` and `git show --stat` every commit landed since, and re-grade each decision whose symbols it touches. Publish test counts as floors w/ the unit named.
- **Grade against HEAD, not a concurrently dirty tree.** An uncommitted guard is not a shipped contract: read `git show HEAD:<path>` into scratch and prove the pristine copy by line arithmetic. A green sweep in a dirty tree can be green because of another session's uncommitted files while HEAD is red; gate the commit's own files in a `head-<slug>` copy (`work.py new head-<slug>`, then `work.py run head-<slug> -- <gate>`, then `work.py rm head-<slug>`).
- **Removing a label vocabulary (P1/P2, rev6) from a spec is a RENAME.** Sweep every citer (`.py` comments, tests, BACKLOG) in the same pass; no gate reads them (the plan-label and spec-section-ordinal rows read only their own vocabularies).
- **Verify `Status:` vs tree before building from it.** PLANNED spec can be half-shipped by concurrent DRY work. `Status:` line = truth; checkboxes stay unticked by convention.
- **Citation proves symbol, not sentence.** Open body, check the specific asserted property (query count, plan decision, SQL fragment, wire shape). Vanished test ≠ dropped deliverable until you grep live-tier docstrings; replacement usually names ancestor.
- **Five homes per contract:** Decision, slice checklist, `## Edge cases`, `## Test plan`, `## Definition of done`. Redundancy designed; two disagreeing = defect. Cross-checking them = the one instrument no single slice runs. Enumeration = count claim w/o number; count members.
- **Doc quotes a generated body → diff quotation vs render.** A "quotation" existing nowhere in the render can be sole warrant for a superseded framing.
- **Sweep both files of a pair.** Sweeping only the edited file leaves partner (other README, spec companion) falsified; blanket rewrite can hit the one sentence DESCRIBING the old spelling. Never write present-tense byte/line count of a file a later slice edits.
- **Gate's name ≠ its coverage.** `check_spec_glossary.py` compares term + anchor only; `notes` prose beside them drifts ungated. Read what a gate compares before trusting green.
- **Bare `Decision N` / `DoD N` = repo-wide convention, not defect.** Grade by ANCHOR presence, never distance: defect only when nothing on the reader's path establishes which spec.
- **Test plan can specify an unrunnable test** (`aclose()` on never-advanced async gen enters no `finally`). Check mechanism vs runtime before pinning a row. Later work falsifies a card's DoD → amend the CARD; spec silently reinterpreting it leaves board demanding the opposite.
- **Stale-sentence taxonomy:** code moved / doc moved / count's subject changed / FALSE ON ITS OWN DATE. Only the last needs no code change; check w/ `git show HEAD:` before blaming the move.

## Verified and rejected — don't re-raise

Investigated, explained, kept. Skip when sweeping.

- **`SCALAR_MAP[models.BigAutoField] = int`, not `BigInt`.** 32-bit `Int` cap → graphql-core rejects out-of-range pks at boundary, never reach DB / overflow param binding; M2M/FK existence path relies on it.
- **`finalize_django_types()` allows two types w/ one GraphQL name.** Finalize = process-global; collision = per-schema; Strawberry's own duplicate-name error at schema build is the accurate catch. Real broken case (two field names camel-casing to one) already fails loud in field audits.
- **`FilterSet._branch_visibility_seed` seeds every active branch (nested, or walked by a flat leaf) from child filterset's own `_default_manager`**, not connection field's `initial_queryset(target_type)`. Owner binding lets target model be strict SUBCLASS of filterset model; seeds differ in a visibility seam.
- **Generated `Prefetch` `to_attr` never contains `__`.** Django splits `prefetch_to` on it; descent silently breaks; only executing catches it. Grammar = `$` delimiter, `_`→`$` escape; read w/ `getattr`/`setattr`.
- **Cascade flips that look like bugs:** cycles raise, `fields=[]` = re-entry escape, MTI parents included, GFKs preflighted, unregistered relation target fails loud. Read glossary before "fixing".
- **Visibility boundary = sealed-execution queryset, not blacklist.** Prove-then-clone was whack-a-mole; never reintroduce a blacklist. Process-wide monkeypatching unsupported; fingerprint ≠ trust boundary.
- **ty and pyrefly are not the type gate.** basedpyright alone has `reportAny` / `reportUnknown*` and `--verifytypes`. ty has no Any-ban (astral-sh/ty#622) and no verifytypes; pyrefly has no `reportAny` equivalent and no verifytypes, and its strict-mode extras were checker gaps, not defects. Re-evaluate only when one of those lands.

## Markdown link convention

Every .md w/ cross-file links = **reference-style**: body `[text][ref-id]`; all defs in one bottom block. Exempt: [AGENTS.md][agents], [CLAUDE.md][claude-md] only (`EXEMPT_MD_SCAFFOLD_NAMES` in [scripts/check_trailing_commas.py][check-commas]); its `source-layout` hook enforces scaffold on every other .md + auto-appends missing markers. Don't hand-fight it. Specs additionally: [scripts/check_spec_glossary.py][check-spec-glossary] validates project terms → real `GLOSSARY.md` anchors, inline + reference forms.

Block opens `<!-- LINK DEFINITIONS -->`, then all 10 group headers, this order, present even empty:

`<!-- Root -->`, `<!-- docs/ -->`, `<!-- docs/SPECS/ -->`, `<!-- docs/builder/ -->`, `<!-- django_strawberry_framework/ -->`, `<!-- tests/ -->`, `<!-- examples/ -->`, `<!-- scripts/ -->`, `<!-- .venv/ -->`, `<!-- External -->`.

Defs alphabetical within group: `[ref-id]: path/from/this/file`.

Why: file moves → inline uses untouched; only bottom paths re-relativize. ~75% cheaper than scattered `](path)`.

Group = where TARGET lives, not source. `examples/fakeshop/README.md` → `docs/GLOSSARY.md` goes under `<!-- docs/ -->`. Empty groups stay (one-scan "links to nothing in `tests/`").

Ten headers = closed list (`LINK_DEF_CATEGORIES`); subdir shares parent's group. `docs/SPECS/appx/` defs under `<!-- docs/SPECS/ -->`.

Stays inline: URLs; in-page anchors (`](#heading)`); anything in fenced code.

New xref: `[text][ref-id]` inline + `[ref-id]: path` in correct group, alphabetical, path from source file's dir. No drift back to `](path)`.

Moving a .md: only bottom paths change. Disk-exists-check each path, but that alone is fail-open: same-named file one level up MASKS depth rot (`../README.md` from a subdir resolves to `docs/README.md`). Also check each def's group header + label vs intended target; every `][label]` has a def, every def a use; sweep bare backticked sibling filenames (a move into `DONE/`/archive breaks those too). GitHub slug: lowercase, drop backticks, strip non-word except hyphens, each surviving space → its OWN hyphen (dotted version → `007`; em-dash heading → double hyphen). Don't collapse whitespace runs in a verifier; strip fenced blocks + code spans before sweeping.

## AGENTS.md

Editing it: dense. No blank lines, no periods, no code blocks.

## Past mistakes

- **Don't pre-populate `conf.py` w/ future settings.** The maintainer trimmed it hard. Key lands with its feature.
- **Don't restore deleted files on assumption.** Ask. (Restored `schema.py` + `test_schema_smoke.py` the maintainer had removed on purpose.)
- **Don't add example-app coverage to the gate.** Rolled back once. Package = 100%; example exercises via real flows, doesn't gate.
- **Don't second-guess `field_name` patterns** in files translated from `django-graphene-filters`. Mirror old shape.
- **Don't over-harden a rule after context loss.** *No auto-commit* ≠ *never commit*. Re-read AGENTS.md when a rule seems to forbid what the maintainer asks.
- **Don't auto-revert a live-tree regression.** No-revert rule covers DIRTY files you didn't author; regression in COMMITTED code → root-cause fix, not checkout.
- **No defer-the-real-fix sequencing.** No test-only fix when prod code is the wrong abstraction, no `pragma: no cover` workaround, no follow-up card as substitute.
- **Rule w/o gate rots.** Repairing a forbidden form → root-cause fix = the missing gate, not the sites. Gate fails open one level up at every level: corpus silently empty (`git ls-files` in ignored dir exits 0, empty stdout), required-file list shrinks, region bounds unpinned. Ask for the next level up before the reviewer does.
- **Item routed forward w/o NAMED owner dies.** Home every deferred finding on a specific card, in DB, before closing.
- **Surface w/ no owning spec silently inverts the specs describing it.** Spec heading rewrite strands every prose citation.
- **Reconciliation slice introduces contradictions it can't see.** Integration pass owes the divergence INVENTORY, not the consistency of the discharging text.

## Strategic advice

- Package rebuilds the overlap of `graphene-django` ∩ `strawberry-graphql-django`, DRF-shaped. Both provide it = foundational. One = optional, later spec.
- Behavior ← `strawberry-graphql-django` (esp. optimizer's downgrade-to-`Prefetch` when target type has custom `get_queryset`). Surface ← `django-graphene-filters` Meta API. Be honest which side a decision falls.
- Build in slices; fork a subsystem to its own spec when a slice passes ~one module. Mechanics: [docs/builder/BUILD.md][build].
- Resist scope creep. Early versions of this file deferred filters, orders, aggregates, permissions, full connection field; each later shipped in its own slice. That's the point. What's still deferred = board's job. No "while I'm here".
- Coverage is a feature. Line uncoverable via the example = smell (too-clever code / wrong abstraction).
- Security: cancel request ≠ termination protocol; lock private to one layer ≠ synchronization contract. Boundary is transactional, not lexical; wrapper must PERMIT, not filter.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: AGENTS.md
[backlog]: BACKLOG.md
[changelog]: CHANGELOG.md
[claude-md]: CLAUDE.md
[goal]: GOAL.md
[kanban]: KANBAN.md
[readme]: README.md
[today]: TODAY.md

<!-- docs/ -->
[docs-readme]: docs/README.md
[dry]: docs/dry/DRY.md
[glossary]: docs/GLOSSARY.md
[hunt]: docs/bug_hunt/HUNT.md
[machines]: docs/fleet/MACHINES.md
[review]: docs/review/REVIEW.md
[ruffing]: docs/ruffing.md
[tree]: docs/TREE.md

<!-- docs/SPECS/ -->
[next]: docs/SPECS/NEXT.md

<!-- docs/builder/ -->
[artifact]: docs/builder/ARTIFACT.md
[build]: docs/builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[check-commas]: scripts/check_trailing_commas.py
[check-spec-glossary]: scripts/check_spec_glossary.py
[fleet]: scripts/fleet.py
[locks]: scripts/_locks.py
[fleet-sync]: scripts/fleet_sync.py
[work]: scripts/work.py

<!-- .venv/ -->

<!-- External -->
