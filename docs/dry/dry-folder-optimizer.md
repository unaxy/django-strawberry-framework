# DRY review: `optimizer/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Folder item (Worker-1, with edit rights in slot-2 only). Audits the
unassigned remainder of the `optimizer/` folder and the families that
cross its ownership boundaries at current bytes (HEAD `23b5f421` +
working tree). The fourteen member file artifacts are inputs, not
verdicts: every assignment below was re-derived fresh at WT bytes, and
every assignment the tree has falsified is flagged as a finding inside
this item for the closeout defect-homing pass. No prior artifact is
summarized and no row is reopened.

Verdict: zero-edit CONFIRM. 48 cross-file compositions hold by name
(FC-1..FC-48, each with a fresh census); 31 merges rejected with
triggers (FR-1..FR-31, 17 converging on standing member rejections
whose triggers were re-checked against current bytes); 7
tree-falsified prior assignments flagged for closeout (FF-1..FF-7,
rows not reopened); 0 FAM-N (the strongest twin — the two fetch
WHERE walks — re-traced fresh and held per-backend on residue-contract
evidence, FR-1); 0 defects; 0 Family-hold rows (no consolidation is
blocked because none is owed). The 931-row `tests/optimizer` suite
runs green in slot-2 at current bytes.

## Pins and fingerprints

HEAD `23b5f42106ffd14805936560f5155dd90d7568da` (detached, intended).
`ITEM_BASELINE=eef6b2172a21e52767db67eed9fbd5a138fa059b` (resolves;
all fourteen optimizer blobs equal the working tree as dispatched, so
BASE=WT pre-edit for every target). Slot-2
(`dry/folder-optimizer/consolidate`) verified byte-identical to WT on
all fourteen targets before tracing and again after the witness suite
(the suite wrote no source). Blob fingerprints are `git hash-object`
(WT = BASE) and `git rev-parse HEAD:<path>` (HEAD), short-8:

| File | Lines | WT = BASE | HEAD | State |
|---|---|---|---|---|
| `optimizer/__init__.py` | 29 | `d400569a` | `d400569a` | clean |
| `optimizer/_context.py` | 438 | `ae77d9d3` | `ae77d9d3` | clean |
| `optimizer/extension.py` | 1682 | `49346716` | `e18210e5` | dirty |
| `optimizer/field_meta.py` | 420 | `478419b7` | `1098cce2` | dirty |
| `optimizer/hints.py` | 274 | `26b2b5a4` | `df40ce08` | dirty |
| `optimizer/join_taxonomy.py` | 354 | `03cf1423` | `053eefeb` | dirty |
| `optimizer/lateral_fetch.py` | 1247 | `995f1aa2` | `995f1aa2` | clean |
| `optimizer/nested_fetch.py` | 506 | `67b69ebc` | `c2ccc321` | dirty |
| `optimizer/nested_planner.py` | 1558 | `a9875bbb` | `73d03184` | dirty |
| `optimizer/plans.py` | 1534 | `37e0e789` | `6f2d0c70` | dirty |
| `optimizer/predicates.py` | 469 | `9e7d80d1` | `71593939` | dirty |
| `optimizer/selections.py` | 761 | `e14e6e30` | `d8dc9d52` | dirty |
| `optimizer/single_parent_fetch.py` | 305 | `bd6beb1c` | `bd6beb1c` | clean |
| `optimizer/walker.py` | 1958 | `da114199` | `bc6bc969` | dirty |

Item-scoped diff (`ITEM_BASELINE` → WT over the folder): empty. This
item landed zero edits in slot-2 and zero in the shared tree; the
ten dirty files' WT-vs-HEAD hunks are attributed below, none made
here.

## System trace

The folder owns N+1 prevention end to end: the schema extension
(`extension.py`: root gate, plan cache, publish discipline, schema
audit), the selection walker (`walker.py`: drive surface, name
resolution, hint dispatch, alias merge, child-build seam), the nested
Relay planner (`nested_planner.py`: window derivation, strategy
dispatch, index advisory), the plan record (`plans.py`: directives,
window renderer, reconciliation), the fetch seam (`nested_fetch.py`:
strategy protocol, windowed/auto backends, skeleton, classifier), the
two recognized backends (`lateral_fetch.py`: Postgres LATERAL SQL;
`single_parent_fetch.py`: degenerate LIMIT), the join vocabulary
(`join_taxonomy.py`), the hint vocabulary (`hints.py`), the field
snapshot (`field_meta.py`), the traversal substrate (`selections.py`:
AST + converted adapters), the execution frame (`_context.py`), the
predicate kit (`predicates.py`), and the 2-name leaf manifest
(`__init__.py`). Data flows root resolver → plan-cache key → walker
(plan over converted selections, nested connections via the planner →
strategy seam) → publish → reconcile → apply. Every cross-folder seam
(registry, seal, sync boundary, queryset seeding, window arithmetic,
keyset codec, name conversion, operation runner) is owned outside and
composed by name; the folder owns no cross-folder definition it does
not already hold as a verified family owner.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init], [file-context][file-context],
[file-extension][file-extension], [file-field-meta][file-field-meta],
[file-hints][file-hints], [file-join-taxonomy][file-join-taxonomy],
[file-lateral][file-lateral], [file-nested-fetch][file-nested-fetch],
[file-nested-planner][file-nested-planner], [file-plans][file-plans],
[file-predicates][file-predicates],
[file-selections][file-selections],
[file-single-parent][file-single-parent], [file-walker][file-walker].
Where the tree falsified an assignment the record sits under Findings
as FF (flag for closeout; no row reopened, nothing re-applied).

### Attribution of the working-tree dirt (by diff content vs HEAD)

Two provenances, distinguished per hunk by content against
`git show HEAD:<path>`; neither is mine.

Ledgered DRY work (uncommitted, predates `ITEM_BASELINE`, may be
built on): the f56 `target_definition=` threading (walker.py 4 hunks:
`_build_child_queryset` signature + docstring + seal-subject read,
`_build_connection_child_queryset` signature + seam-clause docstring +
pass-through, two call sites; nested_planner.py 1 hunk: the nested
call); the f61 lenient adapter (plans.py: `_consumer_prefetch_lookups`
body + docstring + `QuerySet` runtime import +
`queryset_prefetch_lookups` import); the f65 spelling move (plans.py:
`PrefetchLookup` spelling deleted + owner import + `Prefetch` runtime
import dropped; walker.py + nested_fetch.py: `PrefetchLookup`
`TYPE_CHECKING` retargets to `utils/_queryset_private.py`).

Concurrent bug-hunt work (truth migration, hostile-guard deletions,
`except`-arm deletions, `_safe_*` removals, lenient-reader deletions,
comment rewords): every other hunk in all ten dirty files — the
`truth.*` reads and casts, the `_safe_arg_repr` / `_safe_type_name` /
`relation_attr` removals, the `except BaseException` deletions, the
`_safe_getattr` → `_attr` / `_safe_flag` → `_flag` renames, the
`_first_truthy` unguarding, the `getattr` plain-read conversions, and
the riding prose. Never edited, reverted, or tidied here; the four
clean files (`__init__.py`, `_context.py`, `lateral_fetch.py`,
`single_parent_fetch.py`) carry zero dirt of either kind.

## Verification

### Matrix

1. Cross-flavor: the optimizer is infrastructure, not a flavor. The
   write flavors consume it by name (mutations/forms/serializer
   re-fetch via `apply_connection_optimization`; filters/orders via
   the predicate kit — `attach_exists` ← `filters/sets.py`,
   `related_rows_exist` ← `filters/sets.py`, `visible_row_exists` ←
   `orders/sets.py`, each a single composer call); no flavor mirrors
   an optimizer body. The `str.__eq__` scan idiom spans two
   vocabularies (FR-10); the `relation_bool`/`getattr` read idiom is
   hunt-owned migration vocabulary, not a package rule.
   Discharged.
2. Sync/async: the folder carries exactly one `async def`
   (`extension.py::_async_optimize`, a 2-line await-then-optimize
   adapter) and one `await`. No twinship: every other body is sync,
   and the walker/planner/fetch path never awaits (async queryset
   adapters are unwrapped at the `_optimize` boundary by the
   single-owned adapter pair). Discharged.
3. Derived knowledge: every same-token population in the folder was
   walked on body strength. Genuine single owners with by-name
   composers: the window-range plan (6 composers), the fetch-mode
   guard (3), the keyset plan (4-render chain), the order-entry
   parser (3), the join classifier (3), the attach projection (2),
   the deferred-loading unpack (4), the edges/node unwrap (2), the
   count observers (2 × 2 halves), the skip predicate (3), the
   strategy resolver (4), the window signature (capture + 2),
   the IN match (2), the window-qual test (2 + signature), the
   projection read (plan + 2), the parent-id dedup (2). The
   WHERE-walk pair (FR-1), the recognizer sequences (FR-2), the
   reversal dialects (FR-4), the order-walk indexes (FR-5), the
   slice adapters (FR-6), the LRU trio (FR-7), and the remaining
   twins are distinct contracts with triggers. Discharged.
4. Round-trip: the window dialects render one shared
   `WindowRangePlan` (ORM `Q` + SQL text; the counted-keyset shape
   is ORM-rendered only by capability downgrade, its decision still
   shared); the keyset dialects render one `KeysetSeekPlan`
   (`Q` + SQL + structural verifier); the `to_attr` grammar has one
   producer (f28); the visible-value build/read halves are one
   co-located grammar. Discharged.
5. Other media: package oracles (`tests/optimizer/`, 16 files,
   931 rows, all green in slot-2 at current bytes,
   `dry-20261010T041349-e78145`), live `/graphql` rows (the
   connection/visibility suites pin wire behavior), projections
   (module/class/method docstrings; the member D1s ride to closeout
   per FF-2/FF-6/FF-7 and are never fixed here). No medium carries
   a second definition of a folder rule. Discharged.
6. Omission: all fourteen files enumerated below; every member lands
   in a verified family row, a member-artifact assignment re-verified
   at current bytes, or one of this item's transcribed rows. No
   unassigned member remains. Discharged.

### Enumeration

Instrument: `ast` top-level census (`len(ast.Module.body)`, def /
assign split) over the folder at WT bytes, plus `grep` composer
censuses for every cross-file read. Every member below lands in a
verified family row (f-numbered), a member assignment re-verified at
current bytes, or one of this item's transcribed rows (T-numbers in
`## Index rows for Worker-0`).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 4 stmts, 0 defs, 1 assign (`__all__`, 2 names) | logger consumer (F1) + `optimizer-leaf-manifest` (T-31) + R1 stands |
| `_context.py` | 33 stmts, 17 defs, 8 assigns | `optimizer-execution-frame` family (F1, verified) + R1–R4 stand (zero-token claims re-proved) |
| `extension.py` | 80 stmts, 22 defs, 15 assigns | F1–F4 converge (frame / operation-bound f54 / async-adapter e6 / registry-map) + T-33..T-45 (key, strictness, bounds, extractors, pipeline, publish, audit, seams) + R1–R4 stand |
| `field_meta.py` | 13 stmts, 4 defs, 1 assign | F1/F2 converge (kind-taxonomy / instance-accessor, verified) + `field-meta-stamp` (T-32, hunt-migrated, contract intact) + R1/R3/R4/R6 stand; R2 plans-half gone (FF-3); R5 subject gone (FF-5) |
| `hints.py` | 14 stmts, 4 defs, 1 assign | f15/f16/f17 converge + L1 mechanics (rowed) + R1–R8 stand (R6/R7 contract differences re-read) |
| `join_taxonomy.py` | 20 stmts, 12 defs, 1 assign | f21/f22/f23 converge + L1 mechanics (rowed) + R1/R2/R4–R12/R14–R16 stand; R3 subject gone (FF-5); D1 gone (FF-2) |
| `lateral_fetch.py` | 46 stmts, 21 defs, 9 assigns | T-1..T-4 (range/keyset/mode/vocabulary) + f24/f18 converge (skeleton/seam, rowed) + T-46..T-50 (dialect, proof, materialization, spec builder, strategy) + R1–R5 stand |
| `nested_fetch.py` | 32 stmts, 10 defs, 3 assigns | f17/f18/f24 converge + `unwindowable-child-queryset-classification` (rowed) + L1 mechanics (rowed) + R1–R16 stand (R11–R14 twin triggers re-checked) |
| `nested_planner.py` | 68 stmts, 31 defs, 10 assigns | orchestration / slice f19 / advisory / to_attr f28 / scalar-only / keyset-projection converge + E1/E2 consumers + L1 mechanics (rowed) + R1–R13/R15–R17 stand; R14 supersession confirmed |
| `plans.py` | 60 stmts, 34 defs, 9 assigns | T-5..T-10 (record, resolver key, reconcile, prune, order vocab, lookup-path read) + f58/f61/f65 converge + F-A/F-B/F-C/F-E reuse converge onto T-1..T-4 + R-1..R-4 stand; R-5 citations stale (FF-4) |
| `predicates.py` | 29 stmts, 15 defs | T-24 (`row-preserving-predicate-attachment`) + T-25 (alias kit) + R1–R4 stand (R2/R3/R4 halves re-read) |
| `selections.py` | 31 stmts, 19 defs | F-0 converge (frame memo) + T-11..T-23 (adapters, vocabulary, unwrap, observers) + R1–R12 stand (each a count-1 confirmation) |
| `single_parent_fetch.py` | 18 stmts, 5 defs | F-D/F-E/F-F converge + FL1–FL4 (T-51..T-54) + R1–R4/R6 stand (R1 re-litigated fresh, FR-1) |
| `walker.py` | 93 stmts, 45 defs | T-26..T-30 (drive, G2, target-source, merge, scalar/elision) + f56/f57/f62 converge + f23 consumer + aliases routed (settlement holds) + R1–R12 stand |

### Challenges

Authoritative definitions only; consumers, oracles and projections
that also move are listed, never counted. Current bytes.

- C1 fetch-WHERE split change → 2 bodies, judged two rules (FR-1):
  lateral's walk (window + IN + matcher-verified residue) and
  single-parent's walk (window + IN only, residue fails closed);
  per-rule counts 1/1; shared sub-decisions (C15–C17) count 1 each.
- C2 recognizer-sequence change → 1 per backend (each step
  single-owned; sequences differ in membership: vendor/extra/keyset/
  visibility vs setting/select_related/exact-annotations).
- C3 window-range decision → 1 (`window_range_plan`; 6 composers).
- C4 fetch-mode contract → 1 (`assert_window_fetch_mode_for`; 3
  composers: request + spec post-inits + window entry).
- C5 keyset plan → 1 (`build_keyset_seek_plan`; Q + SQL + adapter +
  structural verifier compose).
- C6 order-entry parse → 1 (`order_entry_name_and_direction`; 3
  composers: planner shim, unique-terminal check, lateral columns).
- C7 connection order → 1 per rung (f58: ladder + total + terminal).
- C8 join classification → 1 (`classify_relation_join`; 3 call
  sites: planner raw + planner FieldMeta + walker FieldMeta).
- C9 attach projection → 1 (`prefetch_attach_columns`; 2 readers).
- C10 deferred-loading unpack → 1 (`deferred_loading_of`; 4 readers).
- C11 edges/node unwrap → 1 (`connection_node_children`; 2 callers).
- C12 count observability → 1 per observer (totalCount, hasNextPage;
  plan-time and resolve-time halves compose each).
- C13 hint skip → 1 (`hint_is_skip`; 3 callers: walker, planner,
  schema audit).
- C14 strategy selection → 1 (`resolve_strategy`; 4 call sites:
  extension × 2, planner override, hint factory).
- C15 window signature → 1 (`window_predicate_signature`; capture +
  2 recognizers).
- C16 parent-IN match → 1 (`_parent_in_values`; 2 walks).
- C17 window-qual test → 1 (`_is_window_qual`; 2 walks + signature).
- C18 projection read → 1 (`_select_columns`; plan freeze + 2
  recognizers).
- C19 parent-id dedup → 1 (`_deduplicate_parent_ids`; 2 executors).
- C20 resolver-key build → 1 (`resolver_key` + `runtime_path_*`
  chain; walker derivation + planner injection + resolve-time
  rebuild compose).
- C21 plan-cache key → 1 (`_build_cache_key`; sole insertion site
  `_get_or_build_plan`).
- C22 child-seal choice → 1 per path (f56: builder default +
  connection seam).
- C23 alias-merge scheme → 1 (`_merge_aliased_selections` chain;
  conflict + divergence + prefix union compose).
- C24 `to_attr` spelling → 1 (`relation_connection_to_attr`; f28).
- C25 window-slice bounds → 1 per vocabulary (f19: offset + keyset
  adapters over shared derivations).
- C26 advisory coverage → 1 (`_advise_composite_index` chain;
  tri-state + inventory + dedup compose).
- C27 predicate attach → 1 (`attach_exists`; filters composes).
- C28 related-rows test → 1 (`related_rows_exist`; filters composes).
- C29 visible-row test → 1 (`visible_row_exists`; orders composes).
- C30 converted mirror → 1 (`ast_to_converted_selections`;
  extension + `prime_selected_fields` + connection compose).
- C31 strictness validation → 1 (`_is_valid_strictness`; 1 caller).
- C32 G2 gate → 1 (`_enable_only_for_operation`; threaded bool).
- C33 field stamp → 1 (`FieldMeta._from_field_shape`; 2 entries).
- C34 frame publish → 1 per accessor (17 accessors over 1 frame;
  per-member declarations).

## Findings

### Compositions (each holds by name at current bytes)

Fetch seam and backends. FC-1 strategy seam: the protocol,
`resolve_strategy`, the windowed floor, and the windowed/auto
strategies live once in `nested_fetch.py`; lateral and the planner
compose by name (f17/f18 converge). FC-2 skeleton:
`RecognizedFetchQuerySet` owns the clone-surviving spec + signature +
`_fetch_all` contract (f24 converges); the two subclasses declare
only their spec slot and recognizer (FR-8). FC-3 recognizer
vocabulary: `_is_window_qual`, `window_predicate_signature`,
`_parent_in_values`, `_deduplicate_parent_ids`, `_select_columns`
are defined once in `lateral_fetch.py`; `single_parent_fetch.py`
imports all five and `nested_fetch.rebind` the signature (census:
2 files touch the first pair, 3 the signature). FC-4 window-range
plan: one owner (`utils/connections.py`), 6 composers (2 renderers
+ spec eligibility + planner loop + resolve side + internal).
FC-5 fetch-mode guard: one owner, 3 composers (both post-inits +
window entry). FC-6 keyset dialects: `build_keyset_seek_plan` owns
the plan; `KeysetSeek.plan` composes it, `keyset_seek_q` /
`keyset_seek_sql` render it, the lateral adapter binds it and the
structural verifier proves it. FC-7 order vocabulary: the parser
and the explicit-nulls predicate own the entry contract; the
planner shim, the terminal check, and the lateral columns compose.
FC-8 connection ladder, FC-9 join taxonomy, FC-22 child seam, FC-29
unwindowable classifier: verified families (f58, f21/f22/f23, f56,
classifier row) — composition censuses re-derived fresh and matching
(C7–C9, C22).

Plans and reconciliation. FC-16 plan record: `OptimizationPlan` +
merge discipline + `_IndexedList` + append trio own the shape; the
walker, the planner, and the windowed floor compose. FC-17 child
seam threading (f56: builder + connection seam + planner call).
FC-18 application chain: prune → diff → apply, sole caller
`apply_to`. FC-19 deferred-loading unpack: one owner, 4 readers
(only-set, projection, keyset extension, lateral columns). FC-20
spelling alias and FC-21 attached-lookups read: f65/f61 converge
(the WT hunks ARE the ledgered landings). FC-23 window
annotations: `WINDOW_*` owned once in `plans.py`; lateral,
single-parent, and the connection fast path read. FC-25
resolver-key grammar: `resolver_key` + `runtime_path_*` own the
vocabulary; walker derivation, planner injection, and the
resolve-time rebuild compose. FC-26 lookup-path read: `_lookup_path`
owns the `prefetch_to` spelling; index key, append, diff, and
release compose. FC-28 merge discipline: `merge_from` (strategy
accept + planner-result absorb) vs `merge_metadata_from` (child +
sub-plan absorb) — two operations, one owner each. FC-30
select-related flatten: one owner, release + diff compose. FC-46
prefetch-path flatten: one owner, absorb-check + lookup-paths
compose. FC-47 indexed lists: factories own the shapes; plan
defaults + append dispatch compose. FC-48 path-key ledgers: one
writer trio, merged by `merge_from`, consumed by prune/diff.

Traversal and naming. FC-10 converted adapter: 8 helpers owned once
in `selections.py`; walker (aliases + bodies), planner, extension,
and the count observers compose. FC-11 AST adapter: 3 helpers owned
once; the two extension walks + the mirror compose. FC-12
connection vocabulary: `connection_field_names` owns forward
resolution; planner (once per build), extractor, and observers
compose (default for direct callers). FC-13 count observers: one
walk each; plan-time and resolve-time halves compose. FC-14
edges/node unwrap: one owner, 2 callers (planner adapter +
connection extractor). FC-27 G2 gate: one predicate, one threaded
bool, every projection writer gated.

Drive and lifecycle. FC-15 execution frame: verified family; the
extension opens/closes/publishes, `active_strategy` and the
converted memo read, the walker holds zero frame tokens (grep
clean). FC-24 `to_attr` grammar, FC-31 advisory chain, FC-32 scalar/keyset
projections, FC-34 window-slice bounds, FC-35 orchestration: verified
convergences (f28, F3, F5/F6, f19, F1). FC-33 `to_attr` compat chain:
owner + 2 delegates + walker aliases, all by name.
FC-36 strategy override: `_select_nested_strategy` owns the
hint-else-active read; the plan loop calls once. FC-37 cache key:
`_build_cache_key` owns the 5-part key; sole insertion site;
doc-key LRU + per-execution memo compose. FC-38 stash discipline:
`_stash_union` owns unioning (3 calls); publish owns the
last-wins/union split; `clear_optimizer_context` owns the reset.
FC-39 strictness: vocabulary + validator + settled config +
frame publish, one owner each. FC-40 schema audit: reachable-type
walk + skip read + registry, one owner each. FC-41 return-type
resolution: pair + tracer, sole caller `_optimize`. FC-42
pipeline: `resolve` → `_optimize` → `apply_to`, plus the
connection/mutation seam discovering the active instance. FC-43
extractors: root + connection + payload-slot, one owner each,
forwarded not hardcoded. FC-44 field stamp: `from_django_field` +
`_from_field_shape` own the stamp (hunt-migrated reads, contract
intact); type creation, walker map-build, and the resolver
fallback compose. FC-45 predicate kit: attach + roots + tests +
alias kit owned once; filters/orders compose, the two remaining
`querysets.py`/`exceptions.py` hits are docstring projections.

### FAM verdict: none raised

Thirty-one twin hypotheses were traced to a verdict; every one
resolves to single ownership, a standing rejection with an unmet
trigger, or a distinct contract (FR-1..FR-31). The load-bearing
near-miss is FR-1: the two fetch WHERE walks are byte-parallel
control flow (root-AND check, window-qual skip, first-IN-wins)
modulo residue disposition (collect-for-matching vs fail-closed
`None`), and the code's own docstring calls them structural twins.
Fresh trace holds them per-backend: the residue contracts differ
and that difference is load-bearing — lateral's residue feeds the
keyset structural matcher and the visibility byte-equal prover
while single-parent has no residue consumers — and the one
historical walk-structure change (residue collection for the
keyset/visibility arms) touched lateral only, which is what a
shared walk would have forced single-parent to absorb or
parameterize. Shared sub-decisions already count 1 each (C15–C17).
No Family-hold rows are owed: no consolidation is blocked because
none is owed.

### Rejections (each re-derived fresh; triggers re-checked)

- FR-1 WHERE-walk skeleton (CONVERGE single_parent R1): two
  per-backend proof clauses, residue contracts differ (matcher-fed
  vs fail-closed). Trigger: a third recognizer needing the shared
  core. Searched population: whole package for `__in`-walkers
  (2 hits, both homed).
- FR-2 recognizer sequences: per-backend membership (vendor, extra
  aliases, keyset, visibility vs setting, select_related,
  exact-annotation set); every step single-owned. Trigger: both
  sequences take identical ordered membership.
- FR-3 extractor pattern: connection (edges/node) vs payload-slot
  navigation share primitives; the tuple-append accumulation is
  syntax, not a rule (4th spelling in `_resolver_identities_for`).
  Trigger: a third extractor with the same accumulation.
- FR-4 order-reversal dialects (CONVERGE plans R-1): entry flip +
  NULLS swap + loud refusal vs SQL direction-only rendering over
  pre-refused strings. Trigger: lateral accepts
  expression/explicit-NULLS orders (still refused at
  `_order_columns`).
- FR-5 order-walk indexes (CONVERGE planner R1/R6): skip-unknown
  (projection) vs None-on-unknown (advisory) vs None + table-check
  (lateral); postures re-read at current bytes. Trigger: the
  postures converge.
- FR-6 slice-adapter twins: offset engine vs value-cursor codec;
  coercion + cap + bounds helpers already shared; the remainder is
  per-vocabulary. Trigger: a third window vocabulary.
- FR-7 LRU trio (CONVERGE extension R1 + planner R7): three stores,
  three lifetimes, three eviction rules (quarter-sweep vs
  single-oldest vs single-oldest + promotion); the two `256`
  bounds coincide. Trigger: a shared bounded-cache primitive.
- FR-8 subclass declarations (CONVERGE lateral R2): two 3-line
  subclass declarations over the f24 skeleton; declarations, not
  definitions. Trigger: a third backend with a different clone
  contract.
- FR-9 wrap lambdas (CONVERGE nested_fetch R12): one-line
  compositions of the floor with different receivers. Trigger: a
  wrap adds logic or a third wrap shape appears.
- FR-10 hostile-`str` scans (CONVERGE extension R2): strictness
  bool vs strategy instance + setting read + instance acceptance;
  census still 2 `str.__eq__` vocabularies. Trigger: a fourth
  vocabulary (would still be a per-site two-liner absent a shared
  reason to change; both regions hunt-dirty).
- FR-11 post-init twins (CONVERGE nested_fetch R11): two one-line
  composers of the fetch-mode guard. Trigger: either body adds
  logic beyond the delegation.
- FR-12 spec-builder subclass arms (CONVERGE nested_fetch R13):
  eligibility vs expressibility gates; v1 scope re-checked
  unchanged (single-parent still refuses keyset, counted,
  reversed, M2M, subclass). Trigger: v1 scope change.
- FR-13 row constructors (CONVERGE nested_fetch R14): pristine-clone
  synthesis vs `from_db` + converters + aliases; distinct
  mechanisms, one attribute contract (F-F). Trigger: a shared row
  source.
- FR-14 plan-gate arm sets (CONVERGE lateral R4): expressibility vs
  reproducibility vs strategy-independent safety; all three sets
  present with distinct contracts. Triggers per arm (unchanged).
- FR-15 `check_schema` hints default: `definition.optimizer_hints
  or {}` after a presence check vs `_resolve_optimizer_hints`'s
  None-definition arm — different absences; a cross-module private
  import for a None-default couples without relieving a change
  obligation. Trigger: hints resolution gains a second step.
- FR-16 connection adapters: planner `(sel, runtime_paths, names)`
  vs extractor-protocol `(selections, info)` — two call-shaped
  adapters over the one unwrap owner. Trigger: prefix sourcing
  unifies.
- FR-17 AST walk pair (CONVERGE extension R3): name-keyed body
  printing vs depth-sensitive variable collection; the resolve
  guard is already shared, the walks differ in accumulation.
  Trigger: collection protocol change.
- FR-18 keyset verifier vs owner (CONVERGE lateral F-B
  sub-rejection): fetch-time tree-identity proof vs plan-time
  shape proof. Trigger: a seek representation both sides could
  import without losing the time-of-check distinction.
- FR-19 dialect merge (CONVERGE lateral R1): range decisions live
  once in the shared plan; the ORM/SQL pair renders. Trigger: a
  range decision expressible in one dialect only (the
  counted-keyset ORM-only rendering is a capability downgrade,
  its decision still shared — trigger not fired).
- FR-20 `_require_*` twins (CONVERGE hints R1): Prefetch-type vs
  strategy-name-plus-None invariants; bodies re-read, contracts
  differ. Trigger: a shared invariant.
- FR-21 construction matrix vs dispatch (CONVERGE hints R6):
  `__post_init__` rejects every conflict the walker's priority
  order would arbitrate; order is documentation. No trigger
  (documented split, both halves verified).
- FR-22 connector-load appends: planner prefix-load (refusal arms'
  per-parent resolution) vs walker record (planned relations) —
  two 3-line consumers of the one `source_link_attnames` owner.
  Trigger: a third load site or the append gains logic.
- FR-23 absorb seam vs direct merge: `_absorb_child_plan` (one
  caller) names the accepted-child contract; the planner calls the
  one owner directly. One owner either way. No trigger.
- FR-24 response-key accumulation: 4 tuple-append spellings across
  3 navigations; syntax, not a rule. Trigger: accumulation gains
  logic.
- FR-25 frame accessors: 6 uniform 2-line accessors over distinct
  members; per-member declarations (f-verified shape). No trigger.
- FR-26 subsystem-clear callbacks: 3 one-line store clears over
  the single registry mechanism; per-store declarations. No
  trigger.
- FR-27 strategy class shapes: 3 protocol implementations (name +
  plan); declarations. No trigger.
- FR-28 IN-sibling idioms (CONVERGE predicates R2): correlated
  `EXISTS` vs parent-pk `IN` subquery; docstring-recorded
  equivalent siblings with different seeding; a helper would be a
  mode flag over two SQL shapes. Trigger: measured divergence.
- FR-29 alias grammars (CONVERGE predicates R1): predicate
  `_dst_predicate_*` (occupancy scan) vs order `_dst_order_*`
  (positional index); nothing shared but the word "alias".
  Trigger: a third grammar or a joint registry forced by Django.
- FR-30 base-manager starts (CONVERGE predicates R3): executing
  write-path reads vs the never-executing correlation root;
  extracting the one line couples write and read paths.
  Trigger: a fourth start matching a tail.
- FR-31 taxonomy-through-`FieldMeta` (CONVERGE field_meta R1 +
  join_taxonomy R2): the taxonomy needs `remote_field`/`through`,
  still absent from the 24 `FieldMeta` slots at current bytes;
  the `FieldMeta` leg reads precomputed slots, not a re-stamp.
  Trigger: `FieldMeta` gains `remote_field`/`through` carriage.

### Falsifications (record-only; no row reopened, nothing re-applied)

- FF-1 bogus blob pins: seven `File optimizer/*` plan lines pin
  commit `5ee86193` as a target blob (`__init__.py`, `_context.py`,
  `field_meta.py`, `lateral_fetch.py`, `predicates.py`,
  `selections.py`, `single_parent_fetch.py`) — the same bogus-pin
  class as forms FF-1. Current HEAD troupes are `d400569a`,
  `ae77d9d3`, `1098cce2`, `995f1aa2`, `71593939`, `d8dc9d52`,
  `bd6beb1c`. Closeout correction owed: re-pin or drop.
- FF-2 join_taxonomy D1 gone at HEAD: the defect ("input contract
  denies the production `FieldMeta` leg") no longer holds —
  `classify_relation_join(field: ModelField | FieldMeta)` (HEAD
  `:305`), the "A `FieldMeta` classifies too" docstring clause
  (HEAD `:52-53`), and `_precomputed_attnames` (HEAD `:214`) are
  all committed; the D1-cited `reverse_connector_attname` /
  `target_field_attname` arms no longer exist under those names.
  The plan line "D1 HEAD defect pending closeout homing" is stale
  → closeout retires the homing.
- FF-3 field_meta R2 plans-half gone: `plans.py::window_partition_
  for_prefetch` has zero hits package-wide and in tests (the shim
  was deleted); the `_raw_relation_field` half stands (present,
  contract unchanged). Verdict intact; citations stale → closeout
  refreshes.
- FF-4 plans R-5 subjects gone: both cited members
  (`window_partition_for_prefetch`, `nested_planner.
  _connector_only_field` singular) no longer exist; the underlying
  verdict (partition vs attach are different facts, one
  classifier) holds at current bytes (`partition_expr` vs
  `parent_join_columns` / `prefetch_attach_columns` slots on
  `RelationJoinDescriptor`). Citations stale → closeout refreshes.
- FF-5 lenient-policy subjects deleted by concurrent work:
  `utils/relations.py::relation_attr` has zero hits (deleted);
  `relation_bool` lost its `lenient` axis
  (`(field, name, default=False)`, strict); `_safe_getattr` /
  `_safe_flag` / `_safe_truthy` became `_attr` / `_flag` / inline
  truth. field_meta R5's home (the `relation_attr` docstring) and
  join_taxonomy R3's subject ("already one body" across the
  lenient axis) are gone with them; both verdicts (no shared
  lenient-readers module) hold vacuously. Record-only.
- FF-6 nested_planner D1 shape absent at HEAD bytes: the cited
  M2M child-table composite recommendation cannot fire — the
  cross-table early return (`_advise_composite_index` `:672-673`,
  HEAD-identical) keeps the advisory silent on through-table
  shapes. D1 was observed-not-homed → rides to closeout (not
  closed here).
- FF-7 hints D1 + nested_fetch D1 cited shapes absent at WT bytes:
  the bare-`isinstance` gates both D1s cite now read through
  `truth.*` on hunt-dirty lines. Both were observed-not-homed →
  ride (not closed here).

## Defects

None found while tracing. Checks run: every module docstring's
load-bearing contract re-read against its body (no
contradiction); every guard family enumerated for omission
against its contract source (no missing member — the skip,
seal, slice-licence, and fetch-mode arms each cover their
population); the `check_schema` never-raises contract holds
(`_validate_optimizer_hints` rejects every non-`OptimizerHint`
value at schema build, so `hint_is_skip`'s unguarded read cannot
meet a raising descriptor); layering claims hold (no reverse
imports: walker/extension source selections, never each other;
frame readers never import the extension). Prior observed items
(FF-2/FF-6/FF-7) ride to closeout as recorded above.

D-1 (Worker-2, doc-only): `plans.py::order_entry_name_and_direction`
docstring enumerates three consumers ("Shared by the nested planner's
order-column projection, the unique-terminal check, and the lateral
backend's column resolution, so the three cannot disagree") while the
tree holds five live composers — `nested_planner.py::_concrete_order_terms`
(advisory terms) and `connection.py::_keyset_order_ref` (keyset cursor
ref) are unlisted. The normative rule sentence (single parser of the
entry vocabulary) is correct and holds; only the enumeration is stale.
Owner: `optimizer/plans.py` (order-entry-vocabulary). Routes to Worker-0
homing; verdict-neutral (see CC-1).

## Pending execution

No `proof:` owed (zero-edit: nothing to prove beyond the green
witness already run). `gate:` entries for the final gate:

- `gate:` `uv run python scripts/workspace.py run
  dry/folder-optimizer/verify-1 -- python -m pytest
  tests/optimizer -q --no-cov -p no:cacheprovider` (re-run the
  931-row witness; ran green in slot-2 as
  `dry-20261010T041349-e78145`).
- `gate:` the final gate's live `/graphql` suites covering
  optimizer wire behavior (connection windows, visibility
  scoping, strictness) — named by the gate, not re-run here.
- Cells `unverified` with inapplicability correctly NOT claimed:
  the lateral backend renders Postgres-only SQL and the fetch
  paths thread real aliases (`queryset.db`, `.using()`), so
  sharded + pg reach is real; both cells await the maintainer's word.

## Judgment

The folder is at single ownership: 48 compositions hold by name
with fresh censuses, 31 twin hypotheses resolve without a second
definition, and the witness suite runs 931/931 green at current
bytes. The unassigned remainder that motivated this item — seven
member files whose rules never reached the plan index — is
transcribed below as T-1..T-85 for Worker-0 to row. Zero edits,
zero defects, zero blocked consolidations.

## Index rows for Worker-0

One line per row; Worker-0 alone edits the plan. Holding item for
all: Folder integration `optimizer/`. Freshness: WT blobs in `## Pins
and fingerprints` (BASE = WT); HEAD troupes listed there for the
ten dirty files.

Convergences (fresh CONFIRM single-owned, zero-edit):

- T-1 `window-range-dual-render` — owner
  `utils/connections.py::window_range_plan` — files `plans.py`,
  `lateral_fetch.py`, `single_parent_fetch.py`,
  `nested_planner.py`, `connection.py` — consolidated (C3: 1
  decision, 6 composers; ORM + SQL renderers; FR-19).
- T-2 `keyset-seek-dual-dialect` — owner
  `keyset.py::build_keyset_seek_plan` — files `keyset.py`,
  `lateral_fetch.py`, `plans.py` — consolidated (C5: Q + SQL +
  adapter + verifier compose; FR-18).
- T-3 `window-fetch-mode-guard` — owner
  `utils/connections.py::assert_window_fetch_mode_for` — files
  `nested_fetch.py`, `lateral_fetch.py`, `plans.py` —
  consolidated (C4: 3 composers; FR-11).
- T-4 `nested-recognizer-shared-vocabulary` — owner
  `lateral_fetch.py` (5 helpers) — files `lateral_fetch.py`,
  `single_parent_fetch.py`, `nested_fetch.py` — consolidated
  (C15–C19: 1 each; single_parent imports all five).
- T-5 `optimization-plan-record` — owner
  `plans.py::OptimizationPlan` (+ merge discipline, `_IndexedList`,
  append trio) — files `plans.py`, `walker.py`,
  `nested_planner.py`, `nested_fetch.py`, `extension.py` —
  consolidated (FC-16/FC-28/FC-47).
- T-6 `resolver-key-grammar` — owner `plans.py::resolver_key` (+
  `runtime_path_*` chain) — files `plans.py`, `walker.py`,
  `nested_planner.py`, `connection.py` — consolidated (C20).
- T-7 `consumer-queryset-reconciliation` — owner
  `plans.py::diff_plan_for_queryset` (+ diff pair, absorb rule,
  path flatten) — files `plans.py`, `extension.py` —
  consolidated (FC-18/FC-30/FC-46).
- T-8 `select-related-prune-under-projection` — owner
  `plans.py::prune_unsupportable_select_related` (+ projection +
  traversability readers) — files `plans.py`, `extension.py` —
  consolidated (FC-18).
- T-9 `order-entry-vocabulary` — owner
  `plans.py::order_entry_name_and_direction` (+ explicit-nulls
  predicate) — files `plans.py`, `nested_planner.py`,
  `lateral_fetch.py`, `keyset.py` — consolidated (C6; FR-4).
- T-10 `prefetch-lookup-path-read` — owner `plans.py::_lookup_path`
  — files `plans.py` — consolidated (FC-26: 4 composers).
- T-11 `anonymous-safe-converted-mirror` — owner
  `selections.py::ast_to_converted_selections` (+
  `prime_selected_fields`) — files `selections.py`,
  `extension.py`, `connection.py` — consolidated (C30; faithful
  mirror + memo).
- T-12 `ast-child-iteration` — owner
  `selections.py::ast_child_selections` — files `selections.py`,
  `extension.py` — consolidated (FC-11).
- T-13 `fragment-visit-guard` — owner
  `selections.py::resolve_unvisited_fragment` (both key shapes) —
  files `selections.py`, `extension.py` — consolidated (FC-11;
  FR-17).
- T-14 `ast-directive-variable-extraction` — owner
  `selections.py::directive_variable_names` — files
  `selections.py`, `extension.py` — consolidated (FC-11).
- T-15 `converted-fragment-discriminator` — owner
  `selections.py::is_fragment` — files `selections.py`,
  `walker.py`, `extension.py`, `connection.py` — consolidated
  (FC-10).
- T-16 `converted-directive-evaluation` — owner
  `selections.py::should_include` — files `selections.py`,
  `walker.py`, `nested_planner.py` — consolidated (FC-10).
- T-17 `response-key-grammar` — owner `selections.py::response_key`
  (+ `response_keys`) — files `selections.py`, `walker.py`,
  `nested_planner.py`, `extension.py` — consolidated (FC-10;
  FR-24).
- T-18 `fragment-inlining-flatten` — owner
  `selections.py::included_field_selections` — files
  `selections.py`, `walker.py` — consolidated (FC-10).
- T-19 `fragment-descending-name-match` — owner
  `selections.py::named_children` — files `selections.py`,
  `walker.py`, `extension.py`, `connection.py` — consolidated
  (FC-10/FC-13).
- T-20 `runtime-prefix-cloning` — owner
  `selections.py::with_runtime_prefix` (+
  `node_children_with_runtime_prefix`) — files `selections.py`,
  `walker.py`, `nested_planner.py`, `extension.py` —
  consolidated (FC-10/FC-14).
- T-21 `connection-vocabulary-resolution` — owner
  `selections.py::connection_field_names` (+ record + default) —
  files `selections.py`, `nested_planner.py`, `extension.py`,
  `connection.py` — consolidated (FC-12).
- T-22 `edges-node-unwrap` — owner
  `selections.py::connection_node_children` — files
  `selections.py`, `nested_planner.py`, `extension.py` —
  consolidated (C11; FR-16).
- T-23 `count-observer-walks` — owner
  `selections.py::direct_child_selected` (+ totalCount +
  hasNextPage observers) — files `selections.py`,
  `nested_planner.py`, `connection.py` — consolidated (C12).
- T-24 `row-preserving-predicate-attachment` — owner
  `predicates.py::attach_exists` (+ roots, tests, value kit) —
  files `predicates.py`, `filters/sets.py`, `orders/sets.py` —
  consolidated (C27–C29; FR-28/FR-30).
- T-25 `predicates-reserved-alias-kit` — owner
  `predicates.py::_next_reserved_alias` (+ namespace reader) —
  files `predicates.py` — file-local (FR-29).
- T-26 `walker-drive-surface` — owner `walker.py::plan_optimizations`
  (+ `_walk_selections`, dispatch, select/prefetch planners,
  relation-access record, connection seam) — files `walker.py`,
  `nested_planner.py`, `extension.py` — consolidated (FC-42).
- T-27 `operation-gated-projection` — owner
  `walker.py::_enable_only_for_operation` (threaded bool) — files
  `walker.py`, `nested_planner.py` — consolidated (C32; every
  projection writer gated).
- T-28 `relation-target-definition-source` — owner
  `walker.py::_resolve_relation_target` (one-definition rule) —
  files `walker.py`, `nested_planner.py` — consolidated (f56
  adjacency; single resolution spent everywhere).
- T-29 `aliased-selection-merge` — owner
  `walker.py::_merge_aliased_selections` (+ payload record,
  conflict, divergence, prefix union) — files `walker.py`,
  `nested_planner.py` — consolidated (C23).
- T-30 `scalar-projection-and-fk-elision` — owner
  `walker.py::_selected_scalar_names` (+ elision branch) — files
  `walker.py` — consolidated (forward-resolve + set contract).
- T-31 `optimizer-leaf-manifest` — owner
  `optimizer/__init__.py::__all__` (2 names + omission clause) —
  files `optimizer/__init__.py` — file-local (R1 stands).
- T-32 `field-meta-stamp` — owner `field_meta.py::_from_field_shape`
  (+ `from_django_field`, guards, slots) — files `field_meta.py`,
  `types/base.py`, `types/resolvers.py`, `walker.py` — file-local
  (C33; hunt-migrated reads, contract intact; FF-3/FF-5).
- T-33 `plan-cache-key-machinery` — owner
  `extension.py::_build_cache_key` (+ doc-key print, var sweep,
  value freeze, pagination names, both memos) — files
  `extension.py`, `selections.py`, `_context.py` — consolidated
  (C21; converges with the rowed clear rows, which own only the
  resets).
- T-34 `extension-strictness-config` — owner
  `extension.py::_is_valid_strictness` (+ vocabulary, settled
  config, read-only properties) — files `extension.py`,
  `_context.py` — file-local (C31; FR-10).
- T-35 `plan-cache-bound-and-introspection` — owner
  `extension.py::_MAX_PLAN_CACHE_SIZE` (+ quarter-sweep eviction,
  best-effort counters, `CacheInfo`) — files `extension.py` —
  file-local (FR-7; converges with the rowed clear row).
- T-36 `root-selection-extractors` — owner
  `extension.py::_root_child_selections` (+ connection + payload
  extractors, `SelectionExtractor`) — files `extension.py`,
  `connection.py`, `mutations/resolvers.py` — consolidated
  (FC-43; FR-3).
- T-37 `return-type-resolution` — owner
  `extension.py::_resolve_model_from_return_type` (+ pair) — files
  `extension.py` — file-local (FC-41; sole caller).
- T-38 `root-gate-and-optimize-pipeline` — owner
  `extension.py::resolve` (+ `_optimize`: adapter unwrap,
  normalize, G1 evaluated passthrough, combined passthrough) —
  files `extension.py` — file-local (FC-42).
- T-39 `plan-build-and-apply-tail` — owner
  `extension.py::apply_to` (+ deferred thunk, prune, diff,
  publish, apply) — files `extension.py`, `connection.py` —
  file-local (FC-18/FC-42).
- T-40 `plan-publish-discipline` — owner
  `extension.py::_publish_plan_to_context` (+ `_stash_union`,
  last-wins vs union split) — files `extension.py`, `_context.py`
  — file-local (FC-38).
- T-41 `schema-relation-audit` — owner
  `extension.py::check_schema` (+ reachable-type walk, skip read,
  dedup) — files `extension.py` — file-local (FC-40; never-raises
  holds).
- T-42 `per-relation-delegate-seam` — owner
  `extension.py::DjangoOptimizerExtension.plan_relation`
  (delegate to `walker.plan_relation`) — files `extension.py`,
  `walker.py` — file-local (delegate, not a definition).
- T-43 `connection-cooperation-point` — owner
  `extension.py::apply_connection_optimization` (frame discovery
  + raw-info unwrap + forward) — files `extension.py`,
  `connection.py` — file-local (FC-42).
- T-44 `extension-compat-aliases-and-manifest` — owner
  `extension.py` (5 underscore aliases + `__all__`) — files
  `extension.py`, `selections.py` — file-local (by-name
  compositions; tests read 2 through here).
- T-45 `execution-open-clear-close` — owner
  `extension.py::on_execute` (frame open + conditional clear +
  close) — files `extension.py`, `_context.py`,
  `extensions/operation_state.py` — file-local (FC-15/FC-38).
- T-46 `lateral-sql-dialect` — owner
  `lateral_fetch.py::build_lateral_sql` (+ `LateralWindowSpec`,
  keyset adapter, `LATERAL_SQL_STEM` namespace) — files
  `lateral_fetch.py`, `keyset.py` — file-local (C3 renderer half).
- T-47 `lateral-fetch-proof` — owner
  `lateral_fetch.py::_recognize_lateral_fetch` (+ executor,
  keyset/visibility matchers, carrier) — files `lateral_fetch.py`
  — file-local (FR-1/FR-2; clean lines).
- T-48 `lateral-row-materialization` — owner
  `lateral_fetch.py::_instantiate_row` (+ converter chain) — files
  `lateral_fetch.py` — file-local (FR-13).
- T-49 `lateral-spec-builder` — owner
  `lateral_fetch.py::_build_lateral_spec` (+ order/projection/
  where gates, bindable set, annotation set) — files
  `lateral_fetch.py` — file-local (FR-12/FR-14).
- T-50 `lateral-strategy-object` — owner
  `lateral_fetch.py::LateralPrefetchStrategy` (+ singleton) —
  files `lateral_fetch.py`, `nested_fetch.py` — file-local
  (downgrade-inside-plan contract; FR-9/FR-27).
- T-51 `single-parent-spec-record` — owner
  `single_parent_fetch.py::SingleParentWindowSpec` — files
  `single_parent_fetch.py` — file-local (frozen plan-time facts).
- T-52 `single-parent-eligibility` — owner
  `single_parent_fetch.py::single_parent_spec` (6 arms) — files
  `single_parent_fetch.py` — file-local (FR-12/FR-14).
- T-53 `single-parent-where-walk` — owner
  `single_parent_fetch.py::_single_parent_where_ids` — files
  `single_parent_fetch.py`, `lateral_fetch.py` — file-local
  (FR-1; residue fails closed).
- T-54 `single-parent-executor` — owner
  `single_parent_fetch.py::_fetch_single_parent_rows` (9 gates +
  pristine re-query + synthesis) — files
  `single_parent_fetch.py` — file-local (FR-2).

Rejections (folder-scope merges considered; each with trigger):

- T-55 `fetch-where-walk-merge` (FR-1; CONVERGE single_parent R1) —
  files `lateral_fetch.py`, `single_parent_fetch.py` — rejected
  (matcher-fed vs fail-closed residue; trigger: third
  recognizer).
- T-56 `recognizer-sequence-merge` (FR-2) — files
  `lateral_fetch.py`, `single_parent_fetch.py` — rejected
  (per-backend membership; trigger: identical ordered
  membership).
- T-57 `extractor-pattern-merge` (FR-3) — files `extension.py`,
  `selections.py`, `walker.py` — rejected (navigation differs;
  accumulation is syntax; trigger: third extractor).
- T-58 `order-reversal-dialect-merge` (FR-4; CONVERGE plans R-1) —
  files `plans.py`, `lateral_fetch.py` — rejected (flip+NULLS+loud
  vs direction-only over pre-refused strings; trigger: lateral
  accepts expressions).
- T-59 `order-walk-index-merge` (FR-5; CONVERGE planner R1/R6) —
  files `nested_planner.py`, `lateral_fetch.py` — rejected
  (skip vs None vs None+table postures; trigger: postures
  converge).
- T-60 `slice-adapter-driver` (FR-6) — files `nested_planner.py` —
  rejected (offset vs keyset vocabularies; shared helpers already
  factored; trigger: third vocabulary).
- T-61 `bounded-lru-driver` (FR-7; CONVERGE extension R1 + planner
  R7) — files `extension.py`, `nested_planner.py` — rejected
  (three stores/lifetimes/evictions; trigger: shared primitive).
- T-62 `recognizer-subclass-merge` (FR-8; CONVERGE lateral R2) —
  files `lateral_fetch.py`, `single_parent_fetch.py` — rejected
  (declarations over f24; trigger: third clone contract).
- T-63 `rebind-wrap-merge` (FR-9; CONVERGE nested_fetch R12) —
  files `nested_fetch.py`, `lateral_fetch.py`,
  `single_parent_fetch.py` — rejected (one-line compositions;
  trigger: logic or third shape).
- T-64 `hostile-str-scan-driver` (FR-10; CONVERGE extension R2) —
  files `extension.py`, `nested_fetch.py`,
  `extensions/operation_state.py` — rejected (three vocabularies;
  census 2 `str.__eq__` sites; trigger: fourth vocabulary).
- T-65 `fetch-mode-post-init-merge` (FR-11; CONVERGE nested_fetch
  R11) — files `nested_fetch.py`, `lateral_fetch.py` — rejected
  (two one-line composers; trigger: logic beyond delegation).
- T-66 `spec-subclass-arm-merge` (FR-12; CONVERGE nested_fetch R13)
  — files `single_parent_fetch.py`, `lateral_fetch.py` — rejected
  (eligibility vs expressibility; v1 scope re-checked; trigger:
  scope change).
- T-67 `fetch-row-constructor-merge` (FR-13; CONVERGE nested_fetch
  R14) — files `single_parent_fetch.py`, `lateral_fetch.py` —
  rejected (synthesis vs from_db; trigger: shared row source).
- T-68 `plan-gate-arm-merge` (FR-14; CONVERGE lateral R4) — files
  `lateral_fetch.py`, `single_parent_fetch.py`,
  `nested_planner.py` — rejected (three contracts; triggers per
  arm).
- T-69 `schema-hints-default-compose` (FR-15) — files
  `extension.py`, `walker.py` — rejected (different absences;
  coupling without change relief; trigger: second resolution
  step).
- T-70 `connection-adapter-merge` (FR-16) — files
  `nested_planner.py`, `extension.py` — rejected (two call shapes
  over one owner; trigger: prefix sourcing unifies).
- T-71 `ast-walk-merge` (FR-17; CONVERGE extension R3) — files
  `extension.py`, `selections.py` — rejected (printing vs
  depth-sensitive collection; guard already shared; trigger:
  protocol change).
- T-72 `keyset-verifier-merge` (FR-18; CONVERGE lateral F-B) —
  files `lateral_fetch.py`, `keyset.py` — rejected (fetch-time vs
  plan-time proof; trigger: shared seek representation).
- T-73 `range-dialect-merge` (FR-19; CONVERGE lateral R1) — files
  `plans.py`, `lateral_fetch.py` — rejected (decisions once in
  the plan; trigger: one-dialect-only decision, not fired).
- T-74 `require-guard-merge` (FR-20; CONVERGE hints R1) — files
  `hints.py` — rejected (Prefetch-type vs strategy-name+None;
  trigger: shared invariant).
- T-75 `hint-matrix-dispatch-merge` (FR-21; CONVERGE hints R6) —
  files `hints.py`, `walker.py` — rejected (rejection vs
  documentation; no trigger).
- T-76 `connector-load-writer` (FR-22) — files `nested_planner.py`,
  `walker.py`, `field_meta.py` — rejected (two consumers of one
  owner; trigger: third site or logic).
- T-77 `absorb-seam-spelling` (FR-23) — files `walker.py`,
  `nested_planner.py`, `plans.py` — rejected (named seam + direct
  call, one owner; no trigger).
- T-78 `response-key-accumulation-helper` (FR-24) — files
  `selections.py`, `walker.py`, `extension.py` — rejected
  (syntax; trigger: logic).
- T-79 `frame-accessor-driver` (FR-25) — files `_context.py` —
  rejected (per-member declarations; no trigger).
- T-80 `subsystem-clear-driver` (FR-26) — files `extension.py`,
  `walker.py`, `nested_planner.py`, `registry.py` — rejected
  (per-store declarations over one mechanism; no trigger).
- T-81 `strategy-shape-driver` (FR-27) — files `nested_fetch.py`,
  `lateral_fetch.py` — rejected (protocol declarations; no
  trigger).
- T-82 `exists-in-idiom-merge` (FR-28; CONVERGE predicates R2) —
  files `predicates.py`, `filters/sets.py` — rejected (two SQL
  shapes + seeding; helper would mode-flag; trigger: measured
  divergence).
- T-83 `reserved-alias-counter` (FR-29; CONVERGE predicates R1) —
  files `predicates.py`, `orders/sets.py` — rejected (scan vs
  positional; trigger: third grammar or forced registry).
- T-84 `base-manager-start-helper` (FR-30; CONVERGE predicates R3)
  — files `predicates.py`, `utils/write_transaction.py`,
  `rest_framework/resolvers.py` — rejected (read vs write paths;
  trigger: fourth matching start).
- T-85 `taxonomy-fieldmeta-routing` (FR-31; CONVERGE field_meta R1
  + join_taxonomy R2) — files `join_taxonomy.py`, `field_meta.py`
  — rejected (`remote_field`/`through` still uncarried; trigger:
  carriage).

Closeout notes (not rows): FF-1 (re-pin 7 plan lines), FF-2
(retire join_taxonomy D1 homing), FF-3/FF-4 (refresh R2/R-5
citations), FF-5 (record lenient-subject deletion), FF-6/FF-7
(prior observed D1s ride).

<!-- LINK DEFINITIONS -->
<!-- Root -->
<!-- docs/ -->
[file-context]: dry-file-optimizer___context.md
[file-extension]: dry-file-optimizer__extension.md
[file-field-meta]: dry-file-optimizer__field_meta.md
[file-hints]: dry-file-optimizer__hints.md
[file-init]: dry-file-optimizer____init__.md
[file-join-taxonomy]: dry-file-optimizer__join_taxonomy.md
[file-lateral]: dry-file-optimizer__lateral_fetch.md
[file-nested-fetch]: dry-file-optimizer__nested_fetch.md
[file-nested-planner]: dry-file-optimizer__nested_planner.md
[file-plans]: dry-file-optimizer__plans.md
[file-predicates]: dry-file-optimizer__predicates.md
[file-selections]: dry-file-optimizer__selections.md
[file-single-parent]: dry-file-optimizer__single_parent_fetch.md
[file-walker]: dry-file-optimizer__walker.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->

## Independent verification (Worker-2)

Verdict: verified (plain). Zero-edit CONFIRM stands: every pin,
census, and composer count re-derived from the tree; every FC/FR/FF
checked against current bytes; the witness suite re-run green in
slot-3 (`dry-20261010T042607-c47c96`, 931 passed). Nine record
corrections (CC-1..CC-9, exact fixes below, all verdict-neutral, no
W1 rework owed — Worker-0 applies at transcription) and one
doc-only defect (D-1 under `## Defects`). No missed FAM-N: the one
twin my sweep surfaced beyond W1's FR list (`split_order_ref` vs
the entry parser) is already rejected by standing plans R-4 with
an unmet trigger.

Sequencing disclosure: the dispatch ordered reading the full
artifact before anything, so Findings were seen before tracing
(deviation from expectation-first). Mitigated throughout: every
claim below was fixed by my own greps/pins/censuses first, then
compared against W1's record; the corrections list is the proof
the comparison ran (five undercounts/overcounts W1's prose missed
were caught, not inherited).

Re-derived (never trusted): all fourteen WT/HEAD blob pins plus
line counts (match W1 exactly); the AST top-level census
(stmts+defs match on all fourteen; assigns match where stated);
the async surface (exactly one `async def`, one await expression —
`isawaitable`/prose matches excluded); zero-edit (item diff vs
`ITEM_BASELINE` empty over package/tests/examples; the only delta
is Worker-0's +8 plan bookkeeping; status 532 = 531 + this
artifact); slot-3 byte-identity on all fourteen targets; FR-1
(both WHERE walks read in full, residue consumers censused,
five-helper vocabulary ownership + touch populations, the
`deeb53b4` residue history); C1 (concur: two rules — details
below); all seven FFs against `git show HEAD` bytes; f56/f61/f65
vs hunt attribution (markers + deletion classes present; exactly
the ten claimed dirty files); every numbered composer census in
C1..C34 and FC-1..FC-48 (call-site greps, enclosing-role
resolution); all 85 T-row owners/files (mechanical AST existence
sweep: 0 failures) plus semantic files-list audits of the
composer-complete rows; FR↔T cross-reference (31/31) and C1..C34
sequencing (no gaps); R14 supersession (guards gone, single
`last == 0` site); the `check_schema` never-raises chain;
layering directions; PG/alias reachability. Trusted with sampled
re-checks: member-artifact interior evidence behind CONVERGE rows
(triggers re-checked on the load-bearing R-4/R2/R1/R14; the rest
sampled structurally, not re-traced line by line) and FC prose
beyond the numbered claims (owner-existence + structural level).

Evidence highlights (all at WT bytes unless noted). FC-3: five
helpers defined once in `lateral_fetch.py`; touch populations 2/2
(first pair), 3 (signature, incl. `nested_fetch.rebind`), 2, 2 —
exact. FC-4: six `window_range_plan(` call sites (2 renderers +
spec + planner loop + resolve side + internal); the seventh file
hit is an `exceptions.py` docstring projection. FC-5: three
composers across two spellings (both `__post_init__` via `_for`,
`plans.py` window entry via the plan form) — but see CC-3. FR-1:
single-parent fails closed to `None` on second unrecognized
child; lateral collects residue for `_keyset_seek_quals_match` /
`_visibility_quals_match`, both lateral-only (one `keyset.py`
docstring projection); the docstring's "structural twin ... minus
the keyset/visibility arms" is accurate. FF-2: union signature,
"classifies too" clause, and `_precomputed_attnames` all committed
at HEAD; cited arms zero hits. FF-5: `relation_attr` /
`_safe_getattr` / `_safe_flag` / `_safe_truthy` zero hits;
`relation_bool(field, name, default=False)` strict. Witness:
`tests/optimizer` 16 test files, 931/931 green in slot-3.

Corrections for Worker-0 (transcription fixes, verdict-neutral):

- CC-1 C6/FC-7/T-9 undercount: `order_entry_name_and_direction`
  has five live composers, not three — add `nested_planner.py:268`
  (`_concrete_order_terms`) and `connection.py:871`
  (`_keyset_order_ref`, called at `:962`). T-9 files:
  `plans.py, nested_planner.py, lateral_fetch.py, connection.py`
  (drop `keyset.py` — docstring twin-mention only); parenthetical
  gains "standing plans R-4 (`split_order_ref` loud-vs-fallback
  twin) re-checked, trigger unmet". Count-1 verdict intact (see
  D-1 for the stale docstring enumeration W1 inherited).
- CC-2 T-6 files wrong both ways: drop `connection.py` (only a
  `:2280` docstring projection); add `types/resolvers.py` (three
  live `resolver_key(` rebuilds at `:373/:551/:869`). C20/FC-25
  prose already describes the rebuild — files list only.
- CC-3 T-3 owner precision: the rule owner is
  `utils/connections.py::assert_window_fetch_mode` (its docstring:
  "The single owner of the boundary check"); `..._for` is the
  raw-args adapter. Owner line should name the plan form first.
- CC-4 FC-44/T-32 fourth composer: add
  `types/converters.py:958` (`resolved_relation_annotation`
  fallback) to the `from_django_field` composer list and T-32
  files. C33's "2 entries" (into `_from_field_shape`) still exact.
- CC-5 FR-31/T-85: "24 `FieldMeta` slots" → 20 (AST-counted at WT
  and HEAD; `remote_field`/`through` absent either way — the
  load-bearing claim holds).
- CC-6 FF-6 citation: HEAD `:672-673` → `:671-672` (`if` at 671).
- CC-7 converge count: "17 converging" → 20 (FR-1, 4, 5, 7, 8, 9,
  10, 11, 12, 13, 14, 17, 18, 19, 20, 21, 28, 29, 30, 31).
- CC-8 `## Defects` layering sentence contradicts T-42:
  "walker/extension ... never each other" → "extension→walker
  one-way (T-42 delegate at `extension.py:133`); walker never
  imports extension; both source selections; no runtime
  extension import inside the folder besides the leaf".
- CC-9 T-2 files incomplete by W1's own composer-complete
  convention: add `connection.py` (`KeysetSeek.q()` ORM-dialect
  consumers at `:1097/:1106`), `nested_planner.py` (carrier
  builds), `nested_fetch.py` (request threading).

Concurred without correction: C1 two-rules judgment (residue
contracts differ and the difference is load-bearing — lateral-only
matcher/prover consumers; shared sub-decisions already count 1;
history confirms single-parent was born fail-closed while lateral
grew residue arms); all other FC/C counts as censused (incl. FC-26
as four roles over six call expressions, T-52 as six documented
conditions over five branches — both readings defensible as
stated); all FR contract differences + triggers (FR-4 refusal
still at `_order_columns`; FR-5 three postures re-read; FR-7
256/256/512 bounds; FR-10 two slot-users + exact-type third;
FR-12 v1 refusals incl. DIRECT_FK-only + exact-QuerySet;
FR-31 trigger); R14 SUPERSEDE endorsed (both guards removed by
`dbf0a870`, rule single-sited at `page_arguments`); sharded/pg
cells correctly left `unverified` without an inapplicability claim
(Postgres-only LATERAL renderer + `connections[queryset.db]` /
`.using(queryset.db)` alias threading — reach is real, awaiting
the maintainer's word); `## Pending execution` (no `proof:` owed on
zero-edit; both `gate:` entries well-formed; the witness gate now
additionally discharged by this pass's re-run).

Gates: item diff empty (zero-edit confirmed); witness suite green
in slot-3 as cited; ruff format/check vacuous (zero `.py` paths
touched); no new tests owed (nothing to prove beyond the re-run
witness). Markdown/link conventions of the artifact preserved (no
new cross-file links added by this section).
