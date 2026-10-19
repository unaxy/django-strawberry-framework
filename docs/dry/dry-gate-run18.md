# DRY review: `gate-run18`

Status: verified
Run: 0.0.15 2026-10-11-18

Freshness: HEAD c37a08a0 (detached, unmoved from
pre-gate `git log` to post-gate worktree HEAD
read); pre-gate status 581 lines (575 at run 17
+ concurrent drift, out of scope); pre-gate
`git stash create` 9bb455e4; gate synced_at
2026-10-11T17:27:05+00:00; tree sha256:59f87006;
package sha256:1a836da4 on all 4 suites (differs
from run 17's 3d5ff9ca by concurrent dirt, not
chased); copy_edits/shared_moves empty on all
4. Evidence: `evidence/runs.jsonl:589-592` +
`evidence/logs/<run id>.log` under
`~/dry/ws/c3af387fc1324a21/dry/`.
Lines 593-596 (synced 19:02:14) are a later
concurrent gate, not this run's.

## System trace

Ran `heavy uv run python scripts/workspace.py gate dry
--suites lint,default,floor,sharded` (pg neither
requested nor attempted: not runnable on the remote host).
Pressure GREEN at launch, no other heavy job;
the tool serialized the 4 suites (~70.8 min
wall). Shell died after the gate result landed
(runtime attestation failure, retries 4/4);
every figure below is first-hand evidence read
from the gate logs and `runs.jsonl`, never the
truncated session copy. Pending sweep: items
1-3 carry explicit `None` sections, items 4-5
correctly absent (item 4's placeholder deleted
at closeout per its D1; item 5's absence
W2-confirmed); the only `proof:` / `gate:`
tokens in the five are prose ("Behavioral
proof", "Inverse proof:") and one negation. No
surviving commands.

## Results

- lint (dry-20261011T172705-0ced9a): exit 0,
  13/13 steps green, 195.84 s wall.
- default (dry-20261011T173021-2f2b2e): exit 0,
  10562 passed, 43 skipped, 10603 collected,
  coverage 100.00% (TOTAL 20124/0), 1117.97 s
  wall (pytest 1115.31 s).
- floor (dry-20261011T174859-30a9b4): exit 0,
  10559 passed, 46 skipped, 10603 collected,
  pins py3.10.22 / Django 5.2.16 /
  strawberry 0.322.2 (log + dist-info read),
  1845.86 s wall (pytest 1843.75 s).
- sharded (dry-20261011T181945-cbaa80): exit 0,
  10583 passed, 40 skipped, 10623 collected,
  1090.07 s wall (pytest 1087.84 s).
- Every summary line carries no failed/error/
  xfail/xpass token: zero failures by summary
  grammar.
- Identical to run-17 on all counts (10562/43,
  10559/46, 10583/40; collected 10603/10603/
  10623); coverage TOTAL delta 0 (20124 =
  20124, Miss 0), as a comment-only change
  requires. Skips reconcile as run-17:
  default/floor passed + skipped = 10605 (+2
  over collected via the two module gates),
  sharded 10623 same mechanism. Lint citations
  still 3347.

## Defects

None. Zero failures across 4 suites; routing
untriggered (no path failure, no `proof:`
failure, nothing to reproduce against `git show
HEAD:`).
- (Worker-2) Record-only, verdict-neutral, no
  gate impact: the two prose nuances in `##
  Independent verification (Worker-2)`
  (digest-move attribution, `Proof:`
  enumeration). Zero failures stand.

## Pending execution

- pg cell: neither requested nor attempted this
  run (not runnable on the remote host per brief); the
  standing run-16 record (authorized-unrunnable,
  no artifact names a pg pytest command)
  carries over.
- Blocked B-* proofs: still ride unlanded
  consolidations (unchanged from run-17);
  listed, not run.
- Run-18 items: none (three explicit `None`,
  two correctly absent, W2-concurred each).

## Judgment

GREEN: lint + default (100.00%) + floor +
sharded all exit 0 on run-18 bytes, every
count and the coverage TOTAL identical to
run-17. The run-18 owned change is exactly one
6-line docstring prose hunk in
`django_strawberry_framework/utils/querysets.py::_apply_sidecar_sync`
(+6/-0, zero test/fixture changes), which
cannot change test outcomes: AST-identical per
the item-3 inverse proof
(`docs/dry/dry-rule-sidecar-sync-refusal-vs-generic.md`,
Implementation, AST digest identical pre/post
`2a148c2f…`; cited, not re-run). No pending
commands survive, pg the sole unrunnable cell.
Ready for Worker-2.

## Independent verification (Worker-2)

Re-derived first-hand from
`evidence/runs.jsonl:589-592`, the four logs, and
the independently found gate JSON
`gate-dry-20261011T183755-452097.json` (the record
cites runs.jsonl + logs; the JSON corroborates
every figure). All four exits 0; run ids 0ced9a /
2f2b2e / 30a9b4 / cbaa80; synced_at
2026-10-11T17:27:05+00:00; package
`sha256:1a836da4…` + tree `sha256:59f87006…`
uniform on all 4; `copy_edits` / `shared_moves`
empty. Lint: 13 `+` steps green, 195.84 s,
citations 3347. Default: 10562 passed + 43
skipped, collected 10603 (`4 workers [10603
items]`), TOTAL 20124/0/100%, 1117.97 s wall
(pytest 1115.31 s). Floor: 10559 + 46 / 10603,
pins py3.10.22 + Django 5.2.16 (log header) +
strawberry 0.322.2 (dist-info + JSON pins),
1845.86 s (pytest 1843.75 s). Sharded: 10583 +
40 / 10623, 1090.07 s (pytest 1087.84 s). The
three `====` summary lines carry no
failed/error/xfail/xpass token; lint's 4
error-tokens are `0 errors` zeros, the pytest
logs' are test/coverage filenames. Wall sum
4249.74 s = ~70.8 min. Lines 593-596 correctly
fenced: synced 19:02:14, the later attempt-2
gate.

Run-17 comparison confirmed verbatim,
cross-checked against gate JSON `a49396`, not
just the record: counts and TOTAL identical on
all suites; default/floor passed + skipped =
10605 (+2 over collected 10603 via the two
module gates), sharded 10623 = collected (the
gates collect under sharded) — the run-17 W2
arithmetic; citations still 3347. Digest move
3d5ff9ca -> 1a836da4 verdict-neutral (identical
counts/TOTAL; only owned change AST-identical
prose). Nuance, verdict-neutral: Freshness
attributes the move to "concurrent dirt, not
chased" while the owned +6 prose also
contributes; the Judgment names that prose, so
the record as a whole accounts for it.

Attempt-2 cross-check: MATCH on everything
verdict-relevant. Gate JSON `e1f0c4` + logs +
runs.jsonl:593-596 show identical package bytes
(1a836da4), identical counts/TOTAL, identical
head/blobs/floor pins. Verdict-neutral
differences only: tree digest (59f87006 vs
3d0c4637, prose drift between syncs), wall
times (all within ~1%), stash shas, synced_at.
Both runs GREEN.

Pending sweep re-run: items 1-3 carry explicit
`None` sections; item 4 correctly absent (D1:
placeholder deleted at closeout); item 5
correctly absent (W2: "absent `## Pending
execution`"). All five still `verified`. Token
sweep finds the record's two prose hits + one
negation, plus one more prose `Proof:`
(item 3:74) the record doesn't enumerate —
verdict-neutral: none is a `proof:`/`gate:`
command. No surviving commands; pg +
blocked-B* carryovers correctly fenced (run-17
standing-record wording).

Prose hunk confirmed: diff `63991bbd…` scoped
to package/tests/examples is exactly one file,
+6/-0, a docstring paragraph in
`utils/querysets.py::_apply_sidecar_sync`; zero
test/fixture changes. The item-3 inverse proof
exists in Implementation and says what the
record claims ("AST digest identical pre/post
(`2a148c2f…`)"; W2 there re-derived equality).
The ledger's sole run-18 row is this hunk.

Owed-work adjudication: no ruff pass owed —
the lint suite's first two steps are `ruff
check .` ("All checks passed!") and `ruff
format --check .` ("506 files already
formatted"), green in the cited log. Post-gate
status count taken: 582 = pre-gate 581 + this
artifact (untracked). Nothing verdict-changing
owed.

Anchors: HEAD `c37a08a0` detached, unmoved
(full sha matches gate JSON); `9bb455e4`
(record's pre-gate claim) and `edd8bb27` (gate
JSON) share tree `35584f7e` (timestamp-only
difference, the run-17 pattern); live
`pyproject.toml` / `uv.lock` blobs equal the
JSON pins (`21cccc6d` / `8fb5f01c`).

AGENTS.md / DRY.md: the shell-death narration
is fence-delimited evidence-handling ("every
figure below is first-hand evidence read from
the gate logs and `runs.jsonl`"), the same
shape as run-17's accepted fence note — not
process provenance. Symbol citations
`path::Symbol`; `path:NN` allowed in `dry-*.md`.
Shape short, figures + judgments. Verdict:
verified.
