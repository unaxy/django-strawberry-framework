# DRY review: `gate-run17`

Status: verified
Run: 0.0.15 2026-10-11-17

Freshness: HEAD c37a08a0 (detached, unmoved from
pre-gate `git log` to post-gate HEAD read); pre-gate
status 575 lines; pre-gate `git stash create`
e1f06497; gate synced_at 2026-10-11T14:36:10+00:00;
tree sha256:366f11ef; package sha256:3d5ff9ca on all
4 suites, equal to W2's pascalize verify-run digest;
copy_edits/shared_moves empty on all 4. Evidence:
`runs.jsonl:585-588` + `evidence/logs/<run id>.log`
under `~/dry/ws/c3af387fc1324a21/dry/`.

## System trace

Ran `heavy uv run python scripts/workspace.py gate dry
--suites lint,default,floor,sharded` (pg neither
requested nor attempted: not runnable on the remote host).
Machine GREEN at launch, no other heavy job; the tool
serialized the 4 suites (~70.5 min wall). Shell died
after launch (runtime attestation failure, retries
4/4); every figure below is first-hand evidence read
from the gate logs, never the truncated session copy.
Pending sweep: the 4 run-17 artifacts report none (2
explicit `None` sections, 2 `correctly absent` /
`none owed`, all 4 carry Worker-2 sections); run-16's
255-artifact reconciliation stands per the drift rule.

## Results

- lint (dry-20261011T143610-301530): exit 0, 13/13
  steps green, 194.99 s wall.
- default (dry-20261011T143925-9dd9b9): exit 0,
  10562 passed, 43 skipped, 10603 collected,
  coverage 100.00% (TOTAL 20124/0, all 121 files
  100%), 1116.94 s wall (pytest 1114.13 s).
- floor (dry-20261011T145802-620348): exit 0,
  10559 passed, 46 skipped, 10603 collected,
  pins py3.10.22 / Django 5.2.16 /
  strawberry 0.322.2 (venv-read), 1831.32 s wall
  (pytest 1829.12 s).
- sharded (dry-20261011T152833-4f80cb): exit 0,
  10583 passed, 40 skipped, 10623 collected,
  1086.31 s wall (pytest 1083.91 s).
- Every summary line carries no failed/error/xfail/
  xpass token: zero failures by summary grammar.
- Identical to run-16 on all counts (10562/43,
  10559/46, 10583/40); coverage TOTAL -1 (20124 vs
  20125) = the deleted alias binding, Miss 0.
  Skips reconcile as run-16: default 41+2 module,
  floor 44+2 module, sharded 40. Lint citations
  still 3347 (the prose-only spec edit removed
  none).

## Defects

None. Zero failures across 4 suites; routing
untriggered (no path failure, no `proof:` failure,
nothing to reproduce against `git show HEAD:`).
- OBSERVED record-only, verdict-neutral, for
  Worker-0 to home or dismiss (not a gate finding,
  item stays closed): the run-17 deletion orphaned
  two `_pascalize_token` prose spellings in
  `rest_framework/inputs.py` (live comment:1068 +
  docstring:1105; accurate at HEAD:1078/1115 where
  the alias existed). The same comment block already
  uses the new `pascalize_token` spelling (:1075),
  so the block is now internally inconsistent. Zero
  importers, zero suite impact (W2's census
  correctly classified both as non-importers).

## Pending execution

- pg cell: neither requested nor attempted this run
  (not runnable on the remote host per brief); the standing
  run-16 record (authorized-unrunnable, no artifact
  names a pg pytest command) carries over.
- Blocked B-* proofs: still ride unlanded
  consolidations (unchanged from run-16); listed,
  not run.
- Run-17 items: none (all four report none,
  W2-concurred each).

## Judgment

GREEN: lint + default (100.00%) + floor + sharded all
exit 0 on run-17 bytes, every count identical to
run-16 except coverage TOTAL -1 (the deleted alias
line), no pending commands survive, pg the sole
unrunnable cell. Ready for Worker-2.

## Independent verification (Worker-2)

Re-derived first-hand from the tool evidence, never
inherited from the record above. Gate JSON
`gate-dry-20261011T154639-a49396.json`: all four
exits 0; run ids 301530 / 9dd9b9 / 620348 / 4f80cb;
summaries 10562 passed + 43 skipped (1114.13 s),
10559 + 46 (1829.12 s), 10583 + 40 (1083.91 s);
coverage TOTAL 20124 / 0 / 100.00%; seconds 194.99 /
1116.94 / 1831.32 / 1086.31 (sum 4229.56 s = ~70.5
min wall). Log tails match every summary verbatim;
the only `error` tokens in the default tail are
coverage-table filenames (`error_policy.py`,
`errors.py`); lint tail shows all 13 `+` steps green
with citations 3347. `evidence/runs.jsonl:585-588`
are the four gate run ids in order, each exit 0,
`copy_edits` / `shared_moves` empty, package
`sha256:3d5ff9ca` + tree `sha256:366f11ef` uniform
(record's `runs.jsonl` path reads short for
`evidence/runs.jsonl`; lines and content exact).

Anchors: HEAD `c37a08a0` detached and unmoved;
`e1f06497` (record's pre-gate claim) and `f64a2781`
(gate JSON) both exist with the identical tree
`4cbc6dd7` (hashes differ by commit timestamp only);
live `pyproject.toml` / `uv.lock` blobs equal the
JSON pins (`21cccc6d` / `8fb5f01c`); floor venv
reads py3.10.22 / Django 5.2.16 / strawberry 0.322.2;
pre-gate status 575 corroborated by the plan's own
`575 = 571 + 4` line, current 576 = +1 (this gate
artifact, prose, non-invalidating). Package digest
also confirmed on item-4's three W2 verify runs
(`d809c4` / `9f3ac0` / `8c2f59`, exit 0) — the
three-way match holds on the package leg (tree legs
differ by prose drift, which DRY.md exempts).

Pending sweep: all four run-17 artifacts re-read —
item 3 and item 4 carry explicit `None` sections,
items 1-2 `none owed` / `correctly absent`; the only
`proof:` / `gate:` tokens tree-wide in the four are
a negation and a prose "Behavioral proof". No
surviving commands; run-16's 255-artifact
reconciliation stands per the drift rule.

OBSERVED note verdict: the two spellings exist
exactly as cited (worktree `:1068` / `:1105`, HEAD
`:1078` / `:1115` via `git show HEAD:`, shift from
concurrent dirt in that file) beside the new
spelling at `:1075`; my own repo-wide sweep finds
no import, attribute read, `getattr`, or `__all__`
use — the `test_inputs.py` hit is a substring of
the new-spelling test name. Stale shape-terms in
prose are not existence claims and not importers,
so nothing verified is falsified: the 0-importer
claim, the +3/-14 attribution, and the fence stand.
Item 4 already adjudicated exactly these two sites
(W1 Census + Judgment, W2 "Fenced scope ... STANDS";
What-shrinks discloses "two ungated token-shape
term uses"). AGREE with Worker-0's dismissal: a
rewording relieves no change obligation under the
DRY.md bar, and prose never owns per DRY.md
vocabulary. Verdict-neutral, correctly homed as
record-only.

Scheduled-vs-outcomes +2, re-derived and closed
exactly: default/floor collect 10603 but report
passed + skipped = 10605 because two
collection-time module gates
(`test_multi_db.py:67`,
`test_generic_connection_sharded.py:31`) report one
skip each without collecting. Under sharded those
modules collect 1 + 19 test functions (no
parametrize) = +20 collected (10623), and one
test-level `skipif` (`test_permissions.py:681`)
flips skip to pass: 10562 + 20 + 1 = 10583 passed,
43 - 2 - 1 = 40 skipped. Floor 10559 + 46 = 10605
same mechanism. Counts identical to run-16 on all
four suites; TOTAL -1 (20124 vs 20125, Miss 0) is
the deleted alias line.

DRY.md gate conformance: sharded authorized and pg
unrunnable per the plan; bound inputs still match;
no pending commands existed to run; zero failures
so routing untriggered. Verdict: verified.
