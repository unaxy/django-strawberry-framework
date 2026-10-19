# DRY review: `prefetch-carrier-vs-attach-columns`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Four names, two rows. Source-row side: `optimizer/plans.py::_prefetch_carrier_attnames`
maps each consumer lookup's first segment (via `utils/relations.py::instance_accessor`)
to `optimizer/field_meta.py::FieldMeta.source_link_attnames`, with a duck-typed
`GenericForeignKey` arm (`ct_field`/`fk_field`) because `relation_link` answers empty
for a GFK by design. Child-row side:
`optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns` appends the
morph half to `parent_join_columns` for a `GenericRelation`. Both compose one pair
derivation: `utils/relations.py::relation_link` ("the one reader of which columns join
this relation"). Source writers: `apply_projection`, `walker.py::_record_relation_carriers`,
the `nested_planner.py` parent-row append. Child writers: `_project_scalar_only_window`,
the `walker.py` connector writer. The f23 gap is real: "carrier" occurs x0 in the
[f23 artifact][f23]. `_carrier_attnames` is HELD (foreign hunk, see H1).

## Verification

### Matrix

| Axis | Disposition |
|---|---|
| Cross-flavor | Optimizer-only concern; no filter/order/mutation/form `.only()` mirror |
| Sync/async twins | Pure derivations, no await boundary; identical both sides |
| Derived twice | The question; answered by the matrix probe: disjoint outputs, one pair-reader |
| Inverse pairs | Complementary projections of one link, not encode/decode halves |
| Other media | `spec-003/033/035` cite `source_link_attnames`; f23 owns attach; this record holds the comparison |
| Omission | GFK child side classifies `()` and callers degrade; no contract source demands more, no defect |

### Challenges

| Change posited | Definitions forced | Count |
|---|---|---|
| M2M through table retargets its source FK | `relation_link` M2M arm only; both projections follow | 1 |
| GFK `ct_field`/`fk_field` rename | None; each arm follows its own field's metadata | 0 |
| Composite-pk join shape | `relation_link` pairs + pk-membership filter once | 1 |
| Fold the GFK arm into `FieldMeta` | Moves one definition; no double owner exists today | 1 |

## Findings

### R1 (rejection): carrier and attach are opposite polarities of one link

Contract: C1 (source) "columns the source row must load so consumer-lookup attach reads
no deferred field" vs C2 (child) "columns a plan-written prefetch `.only()` must load so
attach never deferred-refetches". Same link, different rows, disjoint outputs on all 13
matrix rows (FK, reverse FK, M2M both ways, GFK, `GenericRelation`, O2O both ways,
2-column `ForeignObject` both ways, composite-pk reverse, `to_field` M2M both ways).
Variation: forward relations split carriers (source) / targets (child); reverse relations
split non-pk source targets / child carriers; M2M splits through-source targets /
related pk; generic splits nothing (source) / `object_id` + `content_type_id` (child).
Roles: definitions are `relation_link` (pairs), `source_link_attnames` (C1 rule),
`prefetch_attach_columns` (C2 rule), the plans GFK arm (single site, package census 1),
`_generic_child_attname` (single site); `_prefetch_carrier_attnames` is a C1 consumer
adapter (queryset lookups in, `FieldMeta`/GFK out); the four writers above are consumers;
oracles pin each side independently (source: `tests/optimizer/test_field_meta.py` link
rows + `tests/optimizer/test_plans.py` projection rows; child:
`tests/optimizer/test_join_taxonomy.py` + live `test_query/test_library_api.py`).
Owner/lifetime: unchanged; `FieldMeta` link slots are stamped copies of `relation_link`
valid for the snapshot's life. Distinct behavior kept: GFK (forward, source row,
`TaggedItem.content_object`) vs `GenericRelation` (reverse, child row, `Branch.tags`)
name the same physical columns through different fields on different rows; each follows
its own metadata on rename. Proof: matrix [probe][probe] execution-verified
(`uv run python docs/dry/temp-tests/prefetch-carrier-vs-attach-columns/probe.py`, exit 0;
source and child sets disjoint every row; plans output equals `source_link_attnames`
except GFK, where `FieldMeta` is `()` by design and the arm supplies both columns).
Negative control: none (under-fetch costs queries, not exposure). Coupling: none.
Freshness: HEAD `c37a08a0`; blobs `c5e7c5f6` plans, `03cf1423` taxonomy, `478419b7`
field_meta, `b0cc6c33` relations, `dc0c401c` nested_planner, `5508e486` walker,
`999604d2`/`5a95537b` proving tests; population 121 package files; no fourth
`local_related_fields`/`foreign_related_fields` reader outside `relation_link`.
Triggers: (T1) a second GFK source-column derivation appears; (T2) either side reads the
other's rule for the opposite row; (T3) a second pair-reader appears outside
`relation_link`.

### H1 (held): `_carrier_attnames` + taxonomy reader arms under concurrent edit

The working-tree hunk `relation_link(field, lenient=True)` to `relation_link(field)`
(plus sibling rewords in `_forward_join_columns`, `_m2m_join_columns`,
`_generic_child_attname`, `classify_relation_join`) matches no `## Owned changes` row:
foreign concurrent work. This sub-site is read for polarity only, not consolidated.
Trigger: the concurrent truth-migration lands; then re-verify the `FieldMeta`-slot
fallbacks still compose by name and re-run the matrix probe.

## Defects

None.

## Judgment

One link fact, two row polarities, one pair-reader; every challenge counts at most one.
The f23 comparison gap is now recorded with triggers. Zero edits; separation prose
already lives at each owner.

## What shrinks

Rule: "link columns Django's prefetch attach reads" (asked as one fact across
`plans.py::_prefetch_carrier_attnames`, `join_taxonomy.py::prefetch_attach_columns`,
`join_taxonomy.py::_carrier_attnames`, `FieldMeta.source_link_attnames`). Change: none;
rejected with contract difference (source-row vs child-row polarity, disjoint outputs on
all 13 matrix rows) plus held sub-site H1. Owner: unchanged (`relation_link` owns the
pairs; `source_link_attnames` owns the source rule; `prefetch_attach_columns` owns the
child rule). Net package lines: 0. Machinery attestation: no new helper, wrapper,
constant, driver, or flag; no file added or removed in the package.

## Independent verification (Worker-2)

Own trace (pre-findings). Polarity: C1 answers "which columns must load on the row the
queryset returns", C2 "which columns must load on the rows a prefetch fetches"; the rows
live in different tables, so even equal strings would be different facts. Hand-worked:
(1) forward FK `LnkSlugChild.parent` (`to_field="slug"`): C1 `("parent_id",)` (carrier
stored on the source row) vs C2 `("slug",)` (target on the related row) -- opposite sides
of one `relation_link` pair. (2) `TaggedItem.content_object` (GFK) vs `Branch.tags`
(`GenericRelation`): disjoint descriptor populations -- plans' GFK arm reads
`ct_field`/`fk_field` off the source row's virtual field, taxonomy's generic arm resolves
`object_id`/`content_type` off the child table via `_meta.get_field`; neither side ever
sees the other's field. Counts: M2M retarget 1 (`relation_link` M2M arm, both follow);
GFK-side rename at most 1 (whichever Django slot moved; consumer value renames 0);
composite-join 1 (`relation_link` pairs or the `_non_pk_attnames` filter, never both);
`to_field` attach-key change 1 (C2 arm only). `_prefetch_carrier_attnames` is a C1
consumer; the plans GFK arm and `_generic_child_attname` are single-site definitions.
Own pre-read verdict: reject, zero-edit.

Reconciliation. "Both compose `relation_link`": confirmed at WT bytes --
`optimizer/plans.py::_prefetch_carrier_attnames` via `FieldMeta.source_link_attnames`
(stamp lines unchanged by the foreign hunks), taxonomy `_carrier_attnames` /
`_forward_join_columns` direct plus `FieldMeta`-slot fallbacks; the generic arms are
bespoke per side but disjoint by input population, as W1 records. "Disjoint all 13 rows":
FALSE as committed -- row 10 looks up nonexistent `lnkpairchild_set` (`related_name` is
`pair_children`) and the probe's `try/except-continue` swallows it, so W1 executed 12
rows. Cured below: the corrected row resolves and is disjoint. "GFK rename 0" reads as a
consumer-value rename (a Django slot rename would be 1, plans arm); verdict unaffected
either way. No other differences.

Consolidation search (independent, 4 candidates). (a) GFK arms: disjoint inputs/outputs
over separate Django APIs -- fails; trigger: one link-metadata reader both could call.
(b) `source_link_attnames` vs `parent_join_columns` string equality: different tables,
coincidence not contract -- fails; trigger: attach reading one side's columns off the
other row. (c) Writer pairs (2 source + 2 child + `apply_projection`): all compose their
owner by name in ~5 logic-free lines -- consumers, below bar; trigger: a third writer or
per-shape branching at a writer. (d) Fold the GFK arm into `FieldMeta`: plants a decision
no planned consumer can reach (`spec-001` refuses GFK fields) against `relation_link`'s
explicit empty-for-GFK contract -- fails; trigger: a second GFK source-row consumer
(= T1). No candidate survives.

Matrix/axis-6: "no contract source" holds and strengthens -- `spec-001` refuses GFK as a
GraphQL field so taxonomy never meets a GFK on a planned path, and a GFK prefetch's
children span tables, making child-side GFK columns undefinable while source-side `ct/fk`
are well-defined. Axis-5 cites verified (`spec-003`/`spec-033` link-columns prose,
`spec-035` carries the name). f23 "carrier x0" reproduced. Oracle cites hold
(`test_field_meta` pins C1 incl. the FO pair, `test_join_taxonomy` pins C2 incl. the morph
pair, `test_plans` covers projection machinery, live
`test_generic_relation_tags_resolve_over_http_with_optimizer` exercises the child side
over HTTP with captured SQL).

Execution. Workspace pool 6/6 bound (all concurrent items; releases are Worker-0's), so
both probes ran read-only in the shared tree per `DRY.md` (no source mutation, no DB
writes). W1 probe: exit 0, 12/12 resolved rows disjoint (row-10 erratum above). W2
extension (`probe_w2.py`, lint-clean, assert-based): exit 0 -- FK-`to_field` fwd/rev (W1
covered only M2M-`to_field`) plus corrected FO-reverse-2-col, all disjoint with polarity
assertions holding. True matrix: 15 resolved rows, disjoint throughout. Whole-package
grep: `local_related_fields`/`foreign_related_fields` read only inside `relation_link` --
no fourth reader.

H1: foreign confirmed -- `join_taxonomy.py` carries no `## Owned changes` row and is
absent from the cycle baseline; the hunks are the concurrent truth-migration. The hold is
correct (no consolidation may touch taxonomy mid-rewrite) and must not block R1:
rejection edits nothing, and the probe executes against WT bytes including the foreign
hunk, so R1's evidence already binds the migrated read mechanics. Trigger measurable.

Triggers T1-T3 firable (census/grep-observable, each names its tripwire). Freshness
re-hash at WT: 5/6 package pins + both test pins hold; the `nested_planner` pin is
pre-port -- WT differs only by the ledgered item-B hunk in a disjoint region (delegates,
F targets untouched); item-scoped diff on all four F core files is byte-empty.
Pending-absent correct (nothing deferred). Coupling none. Robustness note, not a defect
(no wire input reaches it): the scalar-window writer appends attach columns without the
walker's degrade log while taxonomy prose says callers "log and degrade".

`AGENTS.md` prose: no process provenance, `path::Symbol` cites, sanctioned temp-probe
tier. Shape within caps. Ruff: no touched package paths (zero-edit); W1's probe left
byte-identical as referenced evidence, W2's probe lint-clean.

Verdict: verified. R1's rejection stands with the row-10 erratum cured in-record; H1's
hold stands and does not block.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[f23]: dry-rule-prefetch-attach-column-projection.md
[probe]: temp-tests/prefetch-carrier-vs-attach-columns/probe.py

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
