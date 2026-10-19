# DRY review: `gate-run20`

Status: verified
Run: 0.0.15 2026-10-11-20

Freshness: HEAD c37a08a0 (detached,
unmoved); status 591 lines at
verification (584 at run-20 resume +
concurrent drift, out of scope; this
artifact adds 1 after the count);
`git stash create` f61a90e3 (gate
JSON); gate at 2026-10-11T22:46:58
+00:00; tree sha256:83cef0cd;
package sha256:f04928a4 on all 4
suites; copy_edits/shared_moves empty
on all 4. Evidence:
`evidence/gate-dry-20261011T235726-4f8da3.json`
+ `evidence/runs.jsonl:662-665` (last
4 of 665 lines) +
`evidence/logs/<run id>.log` under
`~/dry/ws/c3af387fc1324a21/dry/`.

## System trace

Gate-completion pass: the run gate
ALREADY RAN green under a prior
worker who stalled before writing the
artifact (cancelled). No suite
re-run; every figure below is
first-hand evidence re-derived from
the gate JSON, `runs.jsonl`, and the
four logs, and every run-20 port
re-checked against the live tree.
Pending sweep: items 1, 2, 4 carry
explicit `None` sections; item 3's
absence W2-ruled compliant at its
close; zero `proof:` / `gate:`
command tokens in the four. No
surviving commands.

## Results

- lint (dry-20261011T224658-59a317):
  exit 0, 13/13 `+` steps green
  (`sh -exc`, last step TREE.md up
  to date), 195.84 s wall.
- default (dry-20261011T225013-ae941d):
  exit 0, 10562 passed, 43 skipped,
  10603 collected, coverage 100.00%
  (TOTAL 20112/0), 1113.33 s wall
  (pytest 1110.57 s).
- floor (dry-20261011T230847-4ba684):
  exit 0, 10559 passed, 46 skipped,
  10603 collected, pins py3.10.22 /
  Django 5.2.16 / strawberry 0.322.2
  (log header + dist-info + JSON
  agree), 1837.04 s wall (pytest
  1834.78 s).
- sharded (dry-20261011T233924-66c53c):
  exit 0, 10583 passed, 40 skipped,
  10623 collected, 1081.71 s wall
  (pytest 1079.50 s).
- Every `====` summary line carries
  no failed/error/xfail/xpass token:
  zero failures by summary grammar.
- Counts identical to run-18 on all
  suites (10562/43, 10559/46,
  10583/40; collected 10603/10603/
  10623); skips reconcile as run-18
  (default/floor passed + skipped =
  10605, +2 over collected via the
  two module gates; sharded 10623 =
  collected). Coverage TOTAL delta
  -12 statements (20124 -> 20112,
  Miss 0), the deletion run's
  expected shrinkage, recorded not
  chased. Lint citations still 3347.
- Wall sum 4227.92 s = ~70.5 min.

## Port-intact check

All 8 run-20 ported files carry the
item hunks in live (diff vs HEAD
read hunk by hunk; adjacent hunks
are concurrent truth-conversion
work, out of scope):

- filters/__init__.py +
  orders/__init__.py: wrapper defs
  gone, bound `.clear` registered
  under the same owners.
- walker.py: 3 dead aliases + 3
  orphaned selections imports +
  deadness comment gone;
  `clear_forward_names` def gone,
  bound `_forward_names_memo.clear`
  registered with the homed
  rationale comment.
- rest_framework/sets.py: identity
  MAP + stale comment gone,
  `write_method = operation`
  present (:369).
- serializer_converter.py:
  `clear_serializer_choice_enums`
  def gone, bound
  `_SERIALIZER_CHOICE_ENUMS.clear`
  registered.
- spec-027 (2 lines) + spec-028 (2
  lines) + tests/test_registry.py
  (:2119) in bound form; zero stale
  cites of any deleted name in
  specs, board, package, tests, or
  examples.
- Note, verdict-neutral: the two
  deleted helper-wrapper names
  still match stale `.pyc` files
  under `__pycache__`; no source
  hit. Bytecode cache only.

## Resolution check

`uv run python -c "import
django_strawberry_framework as m;
print(m.__file__)"` from the
worktree root prints the live-tree
path
(`.../dry-0015/django_strawberry_framework/__init__.py`).
No stale resolution.

## Defects

None. Zero failures across 4
suites; routing untriggered (no
path failure, no `proof:`
failure, nothing to reproduce
against `git show HEAD:`).

## Pending execution

- pg cell: neither requested nor
  attempted this run (not runnable
  on the remote host per brief); the
  standing run-16 record
  (authorized-unrunnable, no
  artifact names a pg pytest
  command) carries over.
- Blocked B-* proofs: still ride
  unlanded consolidations
  (unchanged from run-18); listed,
  not run.
- Run-20 items: none (three
  explicit `None`, one W2-ruled
  compliant absence).

## Judgment

GREEN: lint + default (100.00%) +
floor + sharded all exit 0 on
run-20 bytes, every count
identical to run-18, coverage
TOTAL -12 statements with Miss 0.
All 8 ported files carry the
run-20 hunks, package resolves to
the live tree, no pending
commands survive, pg the sole
unrunnable cell. Ready for
Worker-2.

## Independent verification (gate Worker-2)

Re-derived first-hand; no suite
re-run; no source touched.
(1) Gate JSON parses: 4 cells
exit 0; exit/counts/seconds
match every artifact row
(default 10562/43/10603/1113.33,
floor 10559/46/10603/1837.04,
sharded 10583/40/10623/1081.71,
lint 195.84 s); wall sum
4227.92 s; `runs.jsonl` last 4
(665 lines) bind the same run
ids exit 0 with
copy_edits/shared_moves empty
and package `f04928a4` on all
4; stash `f61a90e3`, tree
`83cef0cd`, gate time agree.
(2) All 4 log tails re-read:
lint 13 `+` steps green
ending TREE.md up to date,
citations 3347; three
summaries carry passed/skipped
only, zero `FAILED`/`ERROR`
verdict lines (lowercase hits
are test-name tokens); default
coverage TOTAL 20112/0/100.00%;
floor pins py3.10.22 /
Django 5.2.16 / strawberry
0.322.2 agree across header,
dist-info, and JSON.
(3) HEAD still `c37a08a0`
detached; status 592 = the
artifact's 591 + this
untracked artifact itself,
zero drift since; all 8
ported files' run-20 hunks
intact in live diffs vs
HEAD, adjacent hunks
concurrent truth-conversion
work, out of scope.
(4) Grep sweep: 4 bound
`.clear` registrations
present under the same
owners; `write_method =
operation` at sets.py:369;
all 5 deleted names zero
hits in package/tests/
examples/specs (stale
`.pyc` hits noted in the
artifact are now gone too
— cache regenerated,
still verdict-neutral);
walker aliases absent.
(5) Standing claims hold:
pg authorized-unrunnable
on the remote host (no docker)
routes through the run-16
record; B-* listed-not-run
rides unchanged; items 1,
2, 4 carry explicit `None`
Pending sections, item 3's
absence W2-ruled
compliant, zero `proof:` /
`gate:` tokens in all
four; resolution check
reproduced (live-tree
path). (6) Run-18 record
re-read: counts identical
(10562/43/10603,
10559/46/10603,
10583/40/10623),
coverage TOTAL delta -12
(20124 -> 20112, Miss 0).
Corrections: none; every
figure reproduced exactly.
Verdict: `verified`.
