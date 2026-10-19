# DRY review: `defects-artifacts-standing`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 8 rows (table rows 37 + 46 + 72-75 + N2/N3 carried by batch 1) across 3 spec
files, 3 per-cycle artifacts, DRY.md §2. Read all 8 source `## Defects` entries in full
before touching anything; re-checked each against current worktree bytes and HEAD.
Attribution: all 4 tracked targets clean vs HEAD at dispatch and at port (zero concurrent
hunks, so no BLOCKED-ON-HUNT); the 3 per-cycle artifacts are untracked single-writer
records. Developed in slot-2, gated, ported byte-identical (`cmp` 6/6). Rows 74 + N3
spent before dispatch (pass-2 self-repair; maintainer spec sweep `c51910d1`). One new
prose defect filed (orders normalize docstring vs its body). No `.py` touched by design.

## Verification

### Matrix

1. Cross-flavor mirroring -- each restatement checked against its sibling-medium twins (docstring/oracle/spec); no twin shares the false sentence after the fix.
2. Sync/async twins -- inapplicable: prose-only batch, no executable surface, no await boundary crossed.
3. Derived knowledge -- every replacement cite verified at its owner (code bodies + oracles read at HEAD and worktree bytes).
4. Round-trip pairs -- inapplicable: no encode/decode pair in the batch surface.
5. Contracts in another medium -- the batch IS the medium sweep: spec/artifact prose restated to committed code truth; DONE D17 echo noted once, closed history untouched.
6. Enforcement by omission -- inapplicable: prose corrections, no guard added or removed.

### Freshness

HEAD `23b5f421` unmoved; ITEM_BASELINE `a17145ab` (= tree at dispatch; pre-edit diff over
the 6 touched files empty). Post-edit blobs: spec-004 `74a46cd6`, spec-003-rat `b40884a5`,
spec-028 `d8931115`, DRY.md `d9493ea6`, f17 `c8610ff9`, relay-guard `d48a49fe`. Slot-1
before == shared pre-edit; slot-2 == shared post-edit (`cmp` 6/6). Evidence: sync
`dry-20261010T234605-263d27`, commas `dry-20261010T234701-5d8c82`, citations
`dry-20261010T234707-51d041` (both gates re-run green on the shared tree after port).

## Findings

| # | defect | verdict | change |
|---|---|---|---|
| 37 | hint-dispatch D1 (spec-004 B4 Test surface) | FIXED | force-select sentence restated as the plan-time raise |
| 46 | attached D3 (spec-003 rationale flattening) | FIXED | reader restated as the owner + lenient adapter |
| 72 | f18 D1+O3 (f17 axes 3+4) | FIXED | both axes restated as one telemetry read, no decision reader |
| 73 | relay-target D-W2-1 (freshness labels) | FIXED | three rows relabeled to the entry's mapping |
| 74 | folder-auth D1 (request-resolution 5→4) | ALREADY-FIXED | pass-2 repair stands verified; recount 4/4 |
| 75 | sets_mixins D1 (DRY.md §2 parenthetical) | FIXED | parenthetical restated as the spelled-oracle truth |
| N2 | spec-028 slice-2 BFS echo | FIXED | emission restated through the base's module-local call |
| N3 | spec-028 Edge-case None-locus echo | ALREADY-FIXED | `c51910d1` restated the locus; wording matches the classifier skip |

Row 37: corroborated three ways at current bytes — HEAD `walker.py:1426-1432` raises,
HEAD `test_walker.py:1996` pins it, spec-033:309 agrees; worktree drift is line numbers only.
Row 46: fix shape is the entry's verbatim; DONE D17 (`build-003-0_0_2.md:195`) carries the stale
"single reader" phrase and stays as written (closed history, noted once). Row 72: f18 O3 names
the axes but states no falsehood (diagnosis + homing instruction, both true post-fix), so it is
untouched per 5g not-re-examination; f17 `Status:`/verdict intact. Row 73: relabeled to the
entry's item-time values per its "no re-trace" — current blobs differ only because the whole
block is item-time (HEAD `bfaee91d` era); mixing current `.md` pins among item-time `.py` pins
would falsify the era. Row 74: both census lines already read 4 with W2 pass-2 confirmation;
remaining "5"s are the D1 text + pass notes (historical record, must stay); the brief's "actual
5" is refuted by recount (WT 572/805/1024+101, HEAD 3+1). Row 75: the entry's second option —
the test is the correct independent oracle per DRY.md Vocabulary (spells, never reads), so the
parenthetical, not the test, was wrong. N2: base `_build_class_type` calls module-local
`build_strawberry_input_class` (`utils/inputs.py:1575`); the orders factory never imports the
alias. N3: normalize drops `None` via the `iter_active_fields` classifier (`is_inactive_value`);
`_active_order_terms` is the defensive backstop for direct/override callers, never the wire-path
locus — naming it instead would falsify the spec.

## Defects

D-NEW1 (prose; owner `orders/inputs.py::normalize_input_value` docstring): the "`None` directions are
preserved ... filters them in its `direction.resolve(...)` comprehension" sentence is false twice: the body
drops `None` via the classifier, and `_active_order_terms` (not a comprehension) backstops it — delete it.

## Judgment

6 rows fixed prose-only on clean lines, 2 spent before dispatch with fixing evidence, 1 genuine
new prose defect filed with its owner. Every corrected artifact keeps its `Status:`/verdict; no
behavior changed, no tests owed, no REROUTE. The brief's row-74 "actual 5" is the only dispatch
claim current bytes refute.

## Implementation (Worker-1)

Landed (prose-only; slot-2 -> shared tree byte-identical, `cmp` 6/6):
`docs/SPECS/spec-004-optimizer_beyond-0_0_3.md:107` (force-select → plan-time raise);
`docs/SPECS/appx/spec-003-optimizer_nested_prefetch_chains-0_0_2-rationale.md:88-91` (reader →
owner + adapter); `docs/SPECS/spec-028-orders-0_0_8.md:60` (emission → base-local call);
`docs/dry/DRY.md:135-138` (parenthetical → spelled-oracle + hand-added-line consequence; §2 only,
links + scaffold intact); `docs/dry/dry-rule-nested-connection-strategy-selection.md:152-158`
(axes 3+4 → telemetry wording, verdict claims verbatim);
`docs/dry/dry-rule-relay-node-target-guard.md:427-428` (three-label rotation applied).
Net over ITEM_BASELINE: +8/-6 tracked (specs + DRY.md) + 2 untracked artifact fixes. Gates:
trailing-commas 0 violations (per-cycle artifacts excluded by rule), citations 3321/3321 resolve.
No `.py` touched → ruff/basedpyright/truthful-reads vacuous, not run; no pytest per AGENTS.md.

## Independent verification (Worker-2)

Order note: `## Findings` read before source entries were finished (deviation, disclosed);
every verdict below re-derived fresh from source bytes (own rg/census/diff/commit reads at WT+HEAD).

Own verdicts (source entry + current bytes, before reconciling): 37 FIXED — spec sentence false
against walker raise + oracle + spec-033, restatement matches all three. 46 FIXED — owner body +
adapter body match the entry's verbatim shape; D17 stale phrase confirmed present in closed DONE
history. 72 FIXED — exactly-1 telemetry census reproduced at both states, feeds a log call only;
both axes reworded, verdict claims verbatim. 73 FIXED — applied labels equal the entry's mapping
exactly; current `.md` blobs (`bd15daf7`/`51b1c956`/`6b715fe9`) match neither side, proving the
block is item-time (header HEAD `bfaee91d`) and the entry-time mapping is the era-true correction.
74 ALREADY-FIXED — own recount 4/4 (WT 572/805/1024+101, HEAD 662/891/1110+101); both census lines
read 4; remaining "5"s are D1 text + pass notes (history). 75 FIXED — entry sanctions the
parenthetical fix as its second option; test spells the slot 3x with zero `binding_attrs` reads,
so Vocabulary (oracle spells, never reads) picks the parenthetical, not the test, as the wrong
half; new wording states exactly that + the hand-added-line consequence. N2 FIXED — base
`_build_class_type` calls module-local `build_strawberry_input_class` (:1575 exact); orders factory
imports only base/`_build_input_fields`/`OrderSet`; package-wide zero production uses of the alias.
N3 ALREADY-FIXED — `c51910d1` (maintainer sweep) restated the Edge-case locus `get_flat_orders` →
normalize-emits-no-term; body drops `None` in the classifier (`is_inactive_value`: `None` →
inactive) before the leaf arm, `_active_order_terms` backstops direct callers. Reconciliation: 8/8
concur with W1; zero differences.
Adversarial points: row-73 era holds (above); row-74 "actual 5" refuted by the recount; N3 wording
matches the classifier skip; row-75 second option is entry-sanctioned and Vocabulary-true.
Reverse check: no other sentence in the 4 touched files is falsified by these edits (neighbors
verified true; spec-028 adapters line mirrors the declared return annotation, untouched).
Untracked diffs (slot-1 vs shared): exactly the claimed hunks (f17 axes 3+4, relay-guard 3-label
rotation); both keep `Status: verified`; f18/folder-auth + all 5 other source artifacts
cmp-identical. DRY.md: one hunk, worked-example parenthetical only; LINK DEFINITIONS + all 10
group headers present; no process-text change.
Gates (heavy, shared tree): trailing-commas 0 violations (4 checked, 3 per-cycle excluded by
rule); citations 3321/3321 resolve. Slot-2 == shared 6/6; blobs match W1 pins; net +8/-6 tracked.
D-NEW1 CONFIRMED genuine: body drops `None` via the classifier (leaf comment says so), filter site
is `_active_order_terms` (a validating classmethod loop, not a resolve comprehension) → mop-up N5.
No `.py` touched → ruff/basedpyright/truthful-reads vacuous, not run; no pytest per AGENTS.md.
Verdict: verified.
