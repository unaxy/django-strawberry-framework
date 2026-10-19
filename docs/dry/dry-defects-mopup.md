# DRY review: `defects-mopup`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Mop-up: 4 rerouted prose fixes on ledgered package files + 3 rerouted
oracles with fresh fail-first proofs. Read every source record in full
first (row-18 D1, prefetch R2, recomposition e2 + P-d, D-NEW1, the three
file D-entries, all three probe files); re-checked each fragment against
current copy bytes before touching anything. Attribution by diff content
vs `git show HEAD:`: F1 clean (no hunk spans HEAD 70-177); F2 builds on
the batch-5 row-39 ledgered docstring hunk; F3 clean (sliced bullet
HEAD-identical, neighbor hunks at HEAD 3699/3824 disjoint); F4 builds on
the batch-1 row-7 ledgered cite hunk (blob `26c0e658` matches its pin);
F5 append + imports (hunt removed other lines only); F6/F7 pure
insertions between clean lines. Developed in slot-2, gated, ported
byte-identical (`cmp` clean 7/7).

## Verification

### Matrix

1. Cross-flavor mirroring -- each fix is site-local prose or one oracle; no twin shares the false sentence or the pinned behavior.
2. Sync/async twins -- inapplicable: no await boundary crossed; prose plus sync-path oracles only.
3. Derived knowledge -- every replacement claim verified at its owner (4 relay gates, planner merge, seal arm, classifier skip, all three fix sites).
4. Round-trip pairs -- inapplicable: no encode/decode pair in the batch surface.
5. Contracts in another medium -- no spec edit owed; oracles pin behavior, never the old wordings.
6. Enforcement by omission -- no guard added or removed; the three oracles pin already-landed fixes, nothing sibling lacks.

### Freshness

HEAD `23b5f421` unmoved; ITEM_BASELINE `662ee556` (= tree at dispatch).
Post-edit blobs: base `7e65b2bd`, walker `04f60113`, querysets `65491308`,
orders/inputs `a3417b78`, test_finalizer `001393cd`, test_resolvers
`03e9c8c0`, test_client `a0f20880`. Slot-2 == shared post-port (`cmp`
7/7). Evidence: sync `d1dad4`, oracles `569ae6` + `540032`, prove
`cd02ea` (3/3 pinned), pyright `aac4fa` + `6a5f8f` 0/0/0, truthful-reads
`c1ba56` tier-1 0, regressions `5871e1` (61) + `024a34` (176),
trailing-commas `7bc949` 0. Manifest at
`$TMPDIR/defects-mopup-failability.json` (kept).

## Findings

| # | fragment | verdict | change |
|---|---|---|---|
| F1 | row 18 | FIXED | three-censuses become universal wording; Decision-7 + shape sentences kept |
| F2 | N4 (prefetch R2) | FIXED | trigger clause landed in the absorb wrapper docstring |
| F3 | row-65 mirror | FIXED | mirror half-sentence landed at the seal's sliced arm prose |
| F4 | N5 (D-NEW1) | FIXED | false None-directions sentence deleted |
| F5 | row-50 oracle | FIXED | rerun oracle landed, fail-first pinned |
| F6 | row-49 oracle | FIXED | conflict oracle landed via the module binder, fail-first pinned |
| F7 | row-55 oracle | FIXED | uniform-guard oracle landed in the walker group, fail-first pinned |

F1: recount LEAD 5 / TAIL 4 re-verified at copy bytes; the stale
enumeration is removed, not extended, per the row-36 precedent.
F2: the planner's direct merge survives at `nested_planner.py:1540`; the
clause states pure delegation plus the specified trigger, plainly.
F3: e2 P-d gives the mirror a location but no exact text, so it is
composed fresh (no tag to drop); both directions verified true.
F5: probe fixture dropped for the module's own autouse; mutant fails with
the filed orphan error verbatim. F6: probe builder replaced by the
module binder + registry recovery + a thin Query/Mutation assembly (the
binder returns no schema); mutant 500s with a top-level GraphQLError.
F7: sanctioned suppression kept; mutant raises the filed AttributeError
verbatim.

## Independent verification (Worker-2)

Own verdicts (source records + current bodies fresh; artifact read early,
deviation disclosed — every count below re-derived, nothing trusted): F1
FIXED (LEAD 5: base.py:296/:344/:400/:474 + testing/relay.py:104; TAIL 4:
same minus relation_shapes; universal wording, Decision-7 + shape kept,
`three` 0) / F2 FIXED (clause in the absorb docstring per R2 home;
trigger verbatim; planner merge at nested_planner.py:1540 survives) / F3
FIXED (mirror at the seal sliced arm per P-d; guard GraphQLError before
seal ConfigurationError both directions true; no tag existed to drop) /
F4 FIXED (None dropped by `is_inactive_value`, backstop is the
`_active_order_terms` loop not a resolve comprehension — false twice) /
F5 FIXED (rerun oracle, tests/ tier, probe fixture correctly dropped) /
F6 FIXED (conflict oracle via module binder + registry recovery, filed
shape intact: vanished row → conflict envelope + full rollback) / F7
FIXED (uniform-guard oracle in the walker group, suppression required by
`dict[str, object]`). W1's table matches all 7; zero differences.
Failability re-run at verify-1 (slot-3): 3/3 pinned, each exactly its
oracle — F5 orphan verbatim, F6 top-level GraphQLError 500, F7
AttributeError verbatim; restores filecmp + sha256 clean. Gates at
verify-1: ruff format + check clean (7 paths), basedpyright 0/0/0 both
passes, truthful-reads tier-1 0, trailing-commas 0; regressions 61 + 176
green. Attribution: F1/F3 clean, F2 on batch-5 row-39, F4 on batch-1
row-7 (blob `26c0e658` matches), F5/F6/F7 pure insertions; no hunt line
touched. Blobs 7/7 match; HEAD unmoved; net +163/-14 exact. No defects
found (Worker-2). Verdict: verified.

## Defects

None.

## Judgment

7 of 7 fragments FIXED, 0 blocked, 0 rerouted, 0 new defects. Every
oracle green plus mutant-pinned with byte-identical restores; every
static gate 0. Net +163/-14 over ITEM_BASELINE, exactly the 8 claimed
hunks. Ready for independent verification.

## Implementation (Worker-1)

Landed (slot-2 -> shared tree byte-identical, `cmp` clean 7/7; net
+163/-14 over ITEM_BASELINE): `types/base.py` comment block (F1);
`optimizer/walker.py` `_absorb_child_plan` docstring +5 (F2);
`utils/querysets.py` sliced bullet +3 (F3); `orders/inputs.py`
`normalize_input_value` docstring -2 net (F4);
`tests/types/test_finalizer.py` imports + appended oracle (F5);
`tests/rest_framework/test_resolvers.py` oracle after the attestation
tests (F6); `tests/testing/test_client.py` oracle in the walker group
(F7). Gates in slot-2 via `heavy`: ruff check + format clean (7 paths);
basedpyright 0/0/0 both passes; truthful-reads tier-1 0;
trailing-commas 0; regressions 61 + 176 green. Shared post-port: ruff
clean, 3/3 oracles re-run green. No new suppression/cast/widening; the
F5/F6/F7 suppressions ride from the verified probes. Stale phrases
(`three`-censuses, the None sentence) score 0 post-edit.
