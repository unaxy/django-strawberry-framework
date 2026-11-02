# Fix loop prompt

The maintainer starts this with `Execute docs/bug_hunt/FIX-PROMPT.md`. Everything below is addressed to the session that runs it.

You are the coordinator of the tracker fix loop in this repository. The maintainer is not watching; run until the
work is done. You never implement: agents fact-find, research, implement and verify; you brief, decide, land and
commit.

## Before anything else

1. Read, in full: [AGENTS.md][agents], [START.md][start], [GOAL.md][goal], [CLAUDE.md][claude-md], [README.md][readme],
   [TODAY.md][today], [docs/README.md][docs-readme] and [docs/TREE.md][tree]. They are the law and the context for
   every decision you make.
2. Read [FIX.md][fix] (the process), the tracker [bug_hunt-0_0_15_2.md][tracker] (the items) and
   [CHANGELOGTODO.md][changelogtodo] (where a landed item's CHANGELOG entry is filed).
3. Check `git status`, `git log -1` and `git worktree list` on main. Other sessions work in this checkout at the same
   time: a dirty or untracked path you did not write is theirs, and you never revert, stash or tidy it.
4. Build the queue: every unchecked item in "To do: found along the way", then "To do: holes found re-checking the
   fixes", in file order, leaving out any item carrying a **SKIP** note. Print the queue (item numbers only) once.

## The loop

Run FIX.md's nine phases for one item, then the next item in the queue, until the queue is empty. Finish each phase
completely, with every agent it dispatched reported back, before starting the next phase. Finish each item (landed,
ticked as not a defect, or parked under "Waiting on you") before starting the next item. Never run two items at
once. After each item, print three lines in chat and continue without waiting.

Re-read the tracker before each pick: a landing can file new items, and an item filed into one of the two "To do"
sections joins the queue at its place in the file. A **SKIP** note added mid-run takes that item out of the queue.

Each agent type sets its own model and effort in `.claude/agents/<name>.md`; dispatch the type FIX.md names for the
role, never `general-purpose`. Every brief carries FIX.md's standing rules, the test budget included.

## What starting this prompt authorizes

- Dispatching the agent types FIX.md names, and the targeted, budgeted test runs FIX.md lists for them (never the
  full suite, never a whole big live module, one run at a time in the foreground).
- Writing the shared checkout only at landing: applying a verified diff plus the tracker and CHANGELOGTODO.md edits,
  committed together as the item's one commit on main. No `Co-Authored-By` or other attribution footer (AGENTS.md
  commit rule), no push, no CI dispatch, no branches, no stash, no `CHANGELOG.md` edit.
- Deciding open questions that AGENTS.md, START.md or GOAL.md settle. A question they do not settle that changes a
  public contract is the maintainer's: park it under "Waiting on you" with the evidence and move on.

It does not authorize writing `examples/fakeshop/db.sqlite3` from a probe or script (point
`DJANGO_STRAWBERRY_KANBAN_DB` at a scratch copy first), growing the type-suppression ledger, or touching another
session's scratch, worktree or dirty files.

## When to stop early

- The shared checkout has uncommitted changes in a path your landing diff touches, or `HEAD` moved under a path
  you changed: re-clone at the new `HEAD`, re-apply, rerun the targeted tests; if it still conflicts, park the item.
- The verifier blocks twice on the same item: park it with both reports.
- Something only the maintainer can do (a Postgres-tier or sharded run, a credential, a branch, a push): park the
  item with what is left to run, and continue with the next one.
- The queue is empty: print the final summary (every item: landed with its commit hash, not a defect, or parked with
  its question; plus the items filed along the way) and stop.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelogtodo]: ../../CHANGELOGTODO.md
[claude-md]: ../../CLAUDE.md
[goal]: ../../GOAL.md
[readme]: ../../README.md
[start]: ../../START.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[fix]: FIX.md
[tracker]: bug_hunt-0_0_15_2.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
