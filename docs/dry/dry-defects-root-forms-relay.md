# DRY review: `defects-root-forms-relay`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 13 rows (31 + 33 + 40 + 41 + 44 + 45 + 56 + 57 + 58 + 59 + 60 + 61 +
65) across connection.py, consumers.py, relay.py (read-only: fix half
spent), forms/resolvers.py, root conftest.py, and 5 test files. Read every
row's `## Defects` entry in full before touching anything; re-checked each
against current bytes. Attribution by diff content vs `git show HEAD:`:
conftest.py, forms/resolvers.py, test_soft_dependency.py,
test_relations_async_api.py CLEAN; connection.py, consumers.py, relay.py,
test_resolvers.py, test_registry.py, test_products_api.py carry concurrent
(hunt/maintainer) dirt — every touch line verified HEAD-identical first, all
concurrent `+`/`-` lines preserved byte-for-byte. Table summaries for rows
33 ("GraphQL-date cite 404s"), 40 ("connection-exclusive"), 41 ("_validate")
and 45 ("defensive-unreachable") are phantom phrases (0 hits in the
governing entries); the verified entries governed. Relay.py needs no edit
(D1 half spent by concurrent reword, HEAD:323 to the live pipeline).
Developed in slot-2, proved, ported byte-identical (`cmp` clean 9/9).

## Verification

### Matrix

1. Cross-flavor mirroring — each fix is site-local; rows 33/45 share one line, fixed once.
2. Sync/async twins — no await boundary crossed; no twin surface.
3. Derived knowledge — every replacement claim verified at its owner body or live census.
4. Round-trip pairs — none owed; no encode/decode grammar touched.
5. Other media — spec-036 Decision 10 + the eager `__all__` pin read as contract sources.
6. Omission — the row-31 census is removed, not recounted; the count is not a contract.

### Freshness

HEAD `23b5f421`, ITEM_BASELINE `c38b98b7`. Post-edit WT blobs: conftest
`0544817e`, connection `3e111147`, consumers `24aa6f3d`, forms/resolvers
`bb12a611`, test_registry `5f3b5812`, test_resolvers `c88b0d9b`,
test_soft_dependency `88b5650a`, test_relations_async_api `ef648f4b`,
test_products_api `4c0ff2b3`. Slot-2 run ids in `## Implementation`.

## Findings

| # | row | verdict | change |
|---|---|---|---|
| 31 | project consumers D1 | FIXED | "two application sites" census removed (live: 3 calls) |
| 33 | e4 D1 | FIXED | forms:30 cite to public `coerce_relation_pk_or_none` |
| 40 | relation-absence D1 | FIXED | test docstring `related_` to `reverse_does_not_exist` |
| 41 | relation-instance D1 | FIXED | accessor IS `instance_accessor(field)`, not `field.name` |
| 44 | typed-globalid D1 | FIXED | test comment to `decode_visible_relation_ids` (relay half spent) |
| 45 | typed-globalid D2 | FIXED | same forms:30 line as row 33, one edit |
| 56 | multipart D1 | FIXED | probe returns `None`; multipart window unbounded, fail-loud kept |
| 57 | store D1 | FIXED | `test_clear_drops_all_state` gains definition + pending arms |
| 58 | ledger D1 | FIXED | same oracle as row 57, one change |
| 59 | typed-globalid D3 | FIXED | live exact-dict INVALID pin (message + code) |
| 60 | root D-W2-2 | FIXED | exact-set pin of the 7 lazy names |
| 61 | relation-conn D-W2-1 | ALREADY-FIXED | helper + gate + census clause gone (T3 deleted the gate) |
| 65 | e2 guard clause | FIXED | guard-vs-seal clause landed; mirror REROUTEs to querysets.py |

31: live `mask_execution_result(` calls = 3 (consumers.py:1178,
schema.py:1181, error_policy.py:410); the extension's own docstring says
"three seams", so the count is doubly stale and no contract.
44: HEAD relay.py:323 named the extinct symbol; WT cites the live pipeline.
56: on 3.14.8 the probe succeeds (deepcopy 512 < loads 262144); the repair
touches only the no-overflow case, proven by simulation + byte-identical
emission where the probe succeeds.
59: Control A flips the test via a top-level error, not the entry's predicted
NOTFOUND — OK-with-None is unreachable in shipped code (relay.py:366-368,
467-468 map every None-pk path to UNCOERCIBLE_PK), so no new defect; the
WRONG_MODEL-to-not_found mutant fails exactly at the new line.
61: `_window_to_attr_constructions` 0 hits in any `.py`; gate, module
docstring clause and `ast` import all absent — the T3 census deletion
removed the observation's subject.
65: clause drops the record's `(DRY e2: ...)` tag per the no-provenance rule;
the mirror half-sentence belongs to the seal in utils/querysets.py,
outside this batch — `REROUTE django_strawberry_framework/utils/querysets.py`.

## Defects

None. No new defect found while tracing.

## Judgment

12 rows FIXED (7 prose-only, 1 fixture repair, 3 oracle landings closing 4
rows), 1 ALREADY-FIXED, 0 blocked, 0 rerouted edits (1 carried mirror note).
All behavioral proofs green in the copy with 5/5 failability mutants pinned;
statics 0 across every gate.

## Implementation (Worker-1)

Landed (slot-2 to shared tree byte-identical, `cmp` clean 9/9; +75/-26
over ITEM_BASELINE): connection.py rows 41 + 65; consumers.py row 31;
forms/resolvers.py rows 33 + 45; conftest.py row 56; test_registry.py rows
57 + 58; test_resolvers.py row 44; test_soft_dependency.py row 60;
test_relations_async_api.py row 40; test_products_api.py row 59. Relay.py
read, untouched (spent half); tests/base/test_init.py read, unused
(alternate row-60 home). Gates in slot-2 via `heavy`: ruff check --fix +
format clean (9 files); docstring-stripped AST vs slot-1 before-copy
IDENTICAL 3/3 (slot-1 == shared pre-port, 9/9 at port); basedpyright 0/0/0
both passes; truthful-reads tier-1 0; trailing-commas 0. Proofs: 7/7
focused green in copy + 7/7 re-run green in shared post-port;
prove_failability 5/5 pinned (both manifests + row56-sim.py + ast-ident.py
at $TMPDIR, referenced, kept). No new cast/suppression/pragma; `@override`
untouched; citations `path::Symbol`; no banned test words; live-first
tiers honored.

## Independent verification (Worker-2)

Own verdicts (pre-Findings, from source entries + current bodies only):
31 FIXED (count deleted; HEAD:1423 said two vs 1 live site :1483-84 — entry's
"3 calls" stale, fix figure-independent). 33 FIXED + 45 FIXED, one hunk (same
cite; def write_values.py:110; underscore 0 hits). 40 FIXED (reverse closure
binds reverse_does_not_exist :763/:777/:792; forward binds related_). 41 FIXED
(list reads instance_accessor(field) :657; finalizer passes it :769; S3 pins
divergence). 44 FIXED-split (test half fixed; relay half spent: live-pipeline
reword, 0 hits, relay untouched by item). 56 FIXED* (loud failure kept for
pathological_json_text; unbounded window + proven-parseable for deepcopy arm).
57 FIXED* + 58 FIXED* (definition + pending arms in clear() pin; tests/ tier,
no live sibling). 59 FIXED* (live pins exact INVALID envelope; live tier
right). 60 FIXED* (exact-set on live table, real import, 7 literals, no
AST/source read). 61 ALREADY-FIXED (helper/gate/prose/ast-import/f28 refs all
0; owner survives as delegates). 65 FIXED + REROUTE utils/querysets.py (clause
verbatim minus provenance tag; seal sliced arm :3259 outside batch).
(* = pending my execution proofs below.)

Reconciliation: concur 13/13. (a) Row 31: W1's cross-module census
(consumers :1178 + schema :1181 + extensions/error_policy :410, "three
seams" :16) supersedes my consumers-only count — re-derived each site;
the deleted count was wrong under either figure. (b) Row 59: W1's
Control-A top-level error confirmed by my re-run (:1194, "unexpected
error"); middle link is the slots KeyError at relay.py:465 — W1's guards
prove the shipped invariant, the run proves the flip doesn't apply.

Execution at verify-1 (copy fresh, shared unmoved): row 56 — both
refusal tests green (b650b9, 2 passed, py3.14.8) + my None-sim
(loads-accepted/deepcopy-overflowed; pathological still raises). Oracles:
my 4/4 pinned (definition :392, pending :393, Control-A :1194,
W2Probe :179) + mapping mutant pinned at the new :1197. Statics: ruff
clean (9); AST-identical 3/3, conftest differs intended; +75/-26 exact
scope; basedpyright main + floor 0/0/0; truthful-reads tier-1 0;
trailing-commas 0; no banned words, no .py provenance, tiers correct.

Attribution: all 27 removed lines HEAD-identical; 2 context-only
adjacencies to pre-baseline concurrent dirt (guard one-liner, DONE-033
reflow — both in baseline bytes, neither edited). No (Worker-2) defects.
Verdict: verified.
