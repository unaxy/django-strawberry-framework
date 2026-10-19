# DRY review: `defects-types`

Status: verified
Run: 0.0.15 2026-10-10-15

## System trace

Batch: 9 rows (table rows 11-17 + 50 + N1) across 7 package files
(`types/{__init__,base,converters,definition,finalizer,relations,relay}.py`;
6 edited, `relations.py` untouched). Read all 7 source `## Defects` entries
in full + the folder-types adjudication (FF-1..FF-13, member-defect pins)
before touching anything; re-checked each against current worktree bytes.
Attribution: full vs-HEAD diff read hunk by hunk -- `__init__.py` and
`relations.py` CLEAN (0 hunks); converters 19, definition 8, finalizer 42,
relay 22, base 49 hunks, all hunt truth-migration except base's two
relay-pk ledgered hunks (buildable, untouched). Every touch line verified
HEAD-identical context first (unified-0 zero overlap with hunt hunks; two
adjacencies disclosed below). Cross-cutting: the homing-table summaries for
rows 11-17 + 50 name phantom phrases (8 phrases, 0 hits package-wide each,
plus `checked` 0 in `__init__.py`). The W2-verified artifact entries
governed instead; every one of them was live in current bytes. Row 50 was
reproduced pre-fix in the filed P2 shape, fixed, and proven fail-first.
Connected reads: registry runtime closure (TYPE_CHECKING-only `types.*`
edges + in-function relay read), SCALAR_MAP row order, helper-ledger
registration flags, `_field_output_type_for` caller census (4 production
sites), root load order. Developed in slot-2, gated, ported byte-identical.

## Verification

### Matrix

1. Cross-flavor mirroring -- twin prose re-read (`forms/converter.py` states the correct MRO mechanism; filters/orders helper-ledger twins re-read for row 50); each defect is family-local wording, no twin shares the false sentence.
2. Sync/async twins -- inapplicable: prose batch plus one sync-only rerun-path fix, no await boundary.
3. Derived knowledge -- every replacement claim verified at its owner (walk body, map row order, closure census, import censuses, ledger flags).
4. Round-trip pairs -- inapplicable: no encode/decode pair in the batch surface.
5. Contracts in another medium -- spec cites re-verified (spec-027 D6/D11, spec-037 D3/D4, spec-048 D1/D2); no spec edit owed.
6. Enforcement by omission -- inapplicable: prose corrections plus one compare-set widening that preserves fail-closed (genuinely unwired sets still raise).

### Freshness

HEAD `23b5f421` unmoved; ITEM_BASELINE `a001310f` (= tree at dispatch;
pre-edit diff over the 6 files empty). Pre-edit blobs: `__init__`
`1bf69028`, base `19d761b6`, converters `d8905d0a`, definition `dfad92ca`,
finalizer `8f699081`, relay `14f79e02`. Post-edit blobs: `__init__`
`f8c29b1a`, base `230bd2ab`, converters `d6e61cec`, definition `cde8437f`,
finalizer `2dbe6efc`, relay `3b4447ae`. Slot-2 post-edit == shared
post-edit (`cmp` identical all 6). Evidence: sync `581fb7`, pre-fix probe
`33ab02`, post-fix `c2278c`, final test PASS `466663`, fail-first `4de6bd`,
ruff `02ad3d` + `f56cdb`, basedpyright main `9b67ae` 0/0/0, floor `611246`
0/0/0, truthful-reads `7d1405` tier-1 0, trailing-commas `016608` 0,
citations `c5e9a2` 3320/3320, regressions `af6ac3` (10) + `a99696` (48).

## Findings

| # | defect | verdict | change |
|---|---|---|---|
| 11 | types `__init__` D1 | FIXED | parenthetical amended to the FF-4 narrowed shape (dead name out, 3 live in) |
| 12 | types converters D1 | FIXED | both dict-order claims reworded (MRO decides; listing order conventional) |
| 13 | types converters D2 | FIXED | consumer enumeration removed at both prose sites (4 sites share the walk) |
| 14 | types definition D2 | FIXED | false cycle rationale reworded to the method-local layering posture |
| 15 | types finalizer D2 | FIXED | four `four`s removed, module order fixed, driver steps aligned to fractional |
| 16 | types relations D1 | REROUTE `django_strawberry_framework/utils/relations.py` | no cite in `types/relations.py`; stale parenthetical lives at `utils/relations.py:150` |
| 17 | types relay D1 | FIXED | false cycle + mispoint replaced with the decode-local weight rationale |
| 50 | types finalizer D1 | FIXED (code) + REROUTE `tests/types/test_finalizer.py` | orphan compare widens to finalized defs' sets; oracle lands the test |
| N1 | relay-pk D-W2-1 | FIXED | `attname` -> `name` (one word) |

Row 16: both source entries + folder-types pin the owner as
`utils/relations.py::relation_kind`; `types/relations.py` (68 lines, fully
read) names no kind/sentinel consumer. Fix file outside the batch, left untouched.
Row 50: pre-fix probe FAILED with the filed orphan error verbatim; post-fix
PASSED with full recovery (B finalized, flag True); first-pass behavior is
provably unchanged (`finalized_wired` empty on a fresh pass). Test half
REROUTEd per brief; ready content + evidence kept in slot-2 `prove-row50/`.

## Defects

None.

## Judgment

8 of 9 rows fixed (7 prose-only + 1 behavior fix with fail-first proof),
1 rerouted with the exact owner path, 1 test half rerouted with ready
content. No hunt line touched (unified-0 zero overlap). No behavior changed
except the filed orphan false-positive. No new defects.

## Implementation (Worker-1)

Landed (slot-2 -> shared tree byte-identical, `cmp` clean all 6; net
+40/-33 over ITEM_BASELINE): `types/__init__.py` module docstring (11);
`types/converters.py` module docstring bullet (12+13), map comment (12),
`_field_output_type_for` docstring (13); `types/definition.py`
`related_target_for` comment (14); `types/finalizer.py` module docstring +
`_SidecarBindingSpec` + `_bind_sidecar_sets` docstring + `_bind_ordersets` +
`_bind_filtersets` docstrings (15) and subpass-1/compare code (50);
`types/relay.py` `decode_global_id` comment (17); `types/base.py`
`_build_annotations` Args (N1). Gates in slot-2 via `heavy`: ruff check +
format clean; basedpyright 0/0/0 both passes; truthful-reads tier-1 0;
trailing-commas 0; citations 3320/3320; inverse proof (docstring-stripped
AST slot-2 vs shared pre-edit) IDENTICAL on the 5 prose files, finalizer
delta scoped to `_bind_sidecar_sets` only (all other members identical).
Adjacencies (touched lines HEAD-identical throughout): row-14 comment sits
in context of a truth-migration hunk; row-15 driver renumber abuts the
hunt-rewritten step-2 lines (untouched); row-50 compare line abuts the hunt
sort-key line (untouched). No new suppression/cast/widening in production.
REROUTE row 16 (`utils/relations.py::relation_kind` docstring): drop the
`(and the registry's typed PendingRelation sentinel)` parenthetical or
retarget it to the FieldMeta/optimizer kind readers. REROUTE row-50 test
(`tests/types/test_finalizer.py`, append): `test_finalize_rerun_after_phase3_
raise_keeps_finalized_sets_wired`, content at slot-2
`tests/types/test_zz_row50_probe.py` (gate-clean incl. one sanctioned
suppression; needs `strawberry`, `MissingReturnAnnotationError`, `FilterSet`,
`filter_input_type` imports in the target module).

## Independent verification (Worker-2)

Sequencing: own verdicts below from fresh reads (7 source entries +
folder-types FF-1..FF-13 + WT bodies + HEAD + baseline bytes) predating
any Findings read; reconciliation appended after.
Own verdicts: 11 FIXED (parenthetical now exactly the 5 live `..utils`
names; `RelationKind` imported + annotated, bare `relation_kind` zero
importers). 12 FIXED (MRO-decides wording true of
`types/converters.py::_class_map_lookup`; PositiveBigInteger-after-Integer
analogy verified at :258/:263). 13 FIXED (single-walk statement true; 4
production consumers re-censused; no direct map reads). 14 FIXED
(no-cycle claim true: registry `types.*` edges TYPE_CHECKING-only, relay
read in-function at :546). 15 FIXED (fractional 1/2/2.5/3/4 at all six
sites; remaining "four"s unrelated prose). 16 REROUTE
`utils/relations.py` (parenthetical persists at :150, outside batch). 17
FIXED (cycle claim replaced by the verified in-function account;
mispoint gone). 50 FIXED (compare widens exactly per the entry's fix
direction; `bind_owner` never writes `finalized`, so the
filters-then-orders call order is safe; first pass provably unchanged).
N1 FIXED (`_meta.pk.name` reads at :1714/:2007).
Reconciliation: zero differences -- all 9 match W1 exactly.
Phantom: own searches at HEAD + WT -- "strictest-first", "only return
site", "split into two commits", "3rd of 3", "pre-split", "assert is
the guard", "silently-satisfied" 0 hits package-wide; "checked" 0 in
`__init__.py`. Table summaries phantom; entries governed and were live.
Removed censuses non-contract: every test cite of the walk/map/attach
sites is behavioral (resolution assertions, direct calls); none pins a
consumer count or the old prose.
Row 50 fail-first re-derived with own probe (filed P2 shape, own
names): pre-fix rerun FAILED with the filed orphan error verbatim;
post-fix PASSED; existing `tests/types/test_finalizer.py` 10/10 green
(slot-3 `4ae52e` fail / `4b24cb` 11 pass; probe removed after).
Oracle REROUTE correct: `tests/types/test_finalizer.py` owned by no 6d
batch (only batch 6 lists test files, and not this one); W1's slot-2
probe read, judged non-portable as briefed, fix judged on its own.
Attribution: all 33 removed lines HEAD-identical; unified-0 W1-vs-hunt
ranges (both baseline coordinates) zero overlap all 6 files;
`__init__.py` hunt-free. The 3 disclosed adjacencies adjudicated clean
(changed lines disjoint in each); one undisclosed gap-1 (row-13
docstring abutting the hunt-rewritten walk body) likewise clean --
observation, not a defect.
Gates (slot-3 verify-1, fresh): docstring-stripped AST IDENTICAL on the
5 prose files; finalizer delta is module docstring + `_bind_sidecar_sets`
only; ruff format --check + ruff check clean on all 6; basedpyright
0/0/0 (`26103b`) + floor 0/0/0 (`befa55`); truthful-reads tier-1 0
(`fcd524`). Freshness blobs 12/12 match.
No defects found (Worker-2). Verdict: verified.
