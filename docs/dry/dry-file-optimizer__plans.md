# DRY review: `optimizer/plans.py`

Status: verified
Run: 0.0.15 2026-09-30-8
Target: `django_strawberry_framework/optimizer/plans.py` (1471 lines)
Blob: `cce985319c8833f3660653327d3003f1f03655a5` (worktree == HEAD ==
ITEM_BASELINE `fd19accc4040399d3b25977f36c8e0a5d9f13b62`; zero diff on all
three; target worktree-clean)
Item baseline: `fd19accc4040399d3b25977f36c8e0a5d9f13b62`
Ledger check: `## Owned changes` in the plan names exactly one
optimizer-area row (walker D1 seal-policy on `optimizer/walker.py`) and the
`mutation-input-reverse-map` naming-atom row (on `mutations/inputs.py`);
no row touches this item's path. `grep -n "plans.py"` over the plan finds
only the item line plus the rejected `orm-lookup-path-resolution` index
row (re-challenged fresh below as R-3, not inherited). Confirmed before
reading the target.

## System trace

The target owns the optimizer's plan vocabulary: the `OptimizationPlan`
record the walker builds and the extension applies, plus every shared
parse/render helper the nested-connection machinery composes by name —
order-ladder construction, window annotation namespace, ORM window
renderer (plain / reverse / marker / probe / keyset-free / keyset-counted),
consumer-queryset reconciliation, projection-prune, resolver-key grammar,
and the deferred-loading single reader.

Sites read (roles: definition / consumer / oracle / projection):

- Definitions owned here, consumers elsewhere: `OptimizationPlan` (+ merge
  discipline, constructed at `walker.py:166,1023` and
  `nested_planner.py:1100,1256,1420`); `append_unique*` (`walker.py`,
  `nested_fetch.py`, `nested_planner.py`); `resolver_key` /
  `runtime_path_from_info` (`walker.py`, `extension.py:652,683,1534`,
  `types/resolvers.py:55`); `deferred_loading_of`
  (`nested_planner.py:720`, `lateral_fetch.py:1165`);
  `order_entry_name_and_direction` + `order_entry_has_explicit_nulls`
  (`nested_planner.py:172,258`, `lateral_fetch.py:1136`,
  `connection.py:826,828`); `effective_connection_order` /
  `deterministic_order` / `ends_in_unique_column` (`connection.py:84,85,134,1746`,
  `nested_planner.py`); `WINDOW_*` constants (`connection.py`,
  `lateral_fetch.py:95-97,151`, `single_parent_fetch.py:63,239,286`);
  `apply_window_pagination` (sole production call
  `nested_fetch.py:317` at worktree `29ce5201…`, HEAD-identical);
  `diff_plan_for_queryset` + `lookup_paths` +
  `prune_unsupportable_select_related` (`extension.py:1239,1248,1380`,
  plus `is_empty` branches at `extension.py:1247,1250`).
- Definitions consumed (not owned here): `utils/connections.py::
  window_range_plan` / `::assert_window_fetch_mode`
  (`f549389e…` clean); `keyset.py::KeysetSeek.q` / `::build_keyset_seek_plan`
  (`df4b5e2f…` clean); `join_taxonomy.py::classify_relation_join` /
  `::WINDOWABLE_RELATION_KINDS` (HEAD `9b355a50…` vs worktree
  `e1cbb3e3…`, dirty — prose cites at 33/77 only, outside the
  175/183/200/329 hunks); `nested_fetch.py::attach_windowed_prefetch`
  (worktree `29ce5201…`, dirt confined to `resolve_strategy` hunks
  423/467, call site HEAD-identical).
- Oracles: `tests/optimizer/test_plans.py` (clean `1e09d6d…` both;
  classes `TestOptimizationPlanIsEmpty`, `TestLookupPaths`,
  `TestOptimizationPlanApply`, `TestOptimizationPlanMerge`,
  `TestOptimizationPlanFinalize`, `TestPlanHelperRelocations`,
  `TestIndexedList`, `TestFlattenSelectRelated`,
  `TestConsumerOnlyFields`, `TestDiffPlanForQueryset`,
  `TestRuntimePathFromPath`, `TestApplyWindowPagination`,
  `TestWindowPartitionForPrefetch`,
  `TestOrderEntryHasExplicitNulls`,
  `TestDeterministicOrderHoistParity`,
  `TestEffectiveConnectionOrder`, `TestReverseOrderBy`,
  `TestPruneUnsupportableSelectRelated`); `test_walker.py` lateral-plan
  + partition rows; `test_lateral_fetch.py` range rows;
  `test_nested_fetch.py` strategy rows; `test_join_taxonomy.py` shim rows.
- Projections: module + symbol docstrings (each states its contract and
  several state their reconsideration trigger); `keyset.py:185` twin
  declaration; `utils/connections.py:231,493` renderer-pair notes;
  `connection.py:130-134` re-export note; `exceptions.py:402` shim-reject
  note; archived spec-033 / spec-053. Prior-cycle records used as trigger
  checks only: the lateral_fetch file item (F-A..F-F surface + R-1
  reversal + F-H dissolution — verified, not inherited) and the
  `orm-lookup-path-resolution` rejected index row (re-challenged as R-3).

Sibling dirt (read-only; never edited): `optimizer/nested_fetch.py`
(worktree `29ce5201…` vs HEAD `4d8d37a7…`), `optimizer/nested_planner.py`
(worktree `e69dbf5f…` vs HEAD `0ad8ff5d…`, +9 advisory hunk at 609),
`optimizer/join_taxonomy.py` (worktree `e1cbb3e3…` vs HEAD
`9b355a50…`, +39 composite-pk feature). Concurrent dirt elsewhere left
alone: `connection.py` (`3c4d5dcb…` vs `93e998f2…`, hunks at 54/703/734 —
every cited line outside them, HEAD-identical text confirmed),
`list_field.py` (`d6af6164…` vs `ce682d5f…`, hunk at 235 only),
`types/resolvers.py` (`5f4cce2b…` vs `f3341e6a…`, import line intact),
`utils/relations.py` (`1cf81e58…` vs `7662b0bb…`, docstring-only +14
inside `classify_path` — bodies identical; the separation clause cited in
R-3 lives at worktree bytes, noted as such).

## Verification

### Matrix

1. Cross-flavor policy mirroring: no flavor twin. The target is
   optimizer-internal; the one shared seam it feeds (strategy selection)
   is owned by `nested_fetch.py` (F-F, inapplicable here — plans builds
   the `Prefetch` payloads strategies carry, no selection logic).
   Package-wide `def`-census finds no second window renderer, order
   ladder, plan record, or resolver-key grammar (probe_singledef: 34/34
   single). The `list_field.py::_is_deterministic_order_*` predicate
   family shares only the token "deterministic" (R-2, verified no
   `plans.deterministic_order` reference in `list_field.py`).
2. Sync/async twins: none owed. AST probe asserts zero
   `AsyncFunctionDef`; text probe finds no `async def` / `await` /
   `sync_to_async` in-file. Execution is sync-only by construction
   (QuerySet annotate/filter/order_by chains); async callers reach it
   through the shared sync boundary (family `one-sync-boundary`, owned
   at `utils/querysets.py`). The single-parent and lateral counterparts
   are likewise sync-only. Inapplicable with reason, matching lateral R5.
3. Derived rather than repeated knowledge: every derivation composes its
   owner by name — range/marker/probe decisions via
   `utils/connections.py::window_range_plan` (`apply_window_pagination`
   owns only the `Q`-object rendering); seek structure via
   `keyset.py::build_keyset_seek_plan` (count-free branch filters
   `keyset_seek.q()`, counted branch passes `seek_q` into the running
   count); join facts read from `classify_relation_join` descriptors,
   never re-walked; projection read via the single
   `deferred_loading_of` unpack. The one exception is the triple
   `prefetch_to` attribute read (F-N / D1): `_lookup_path` plus two
   inline reads that would not follow a rename by construction.
4. Inverse / round-trip pairs: (a) `window_range_plan` decisions rendered
   as ORM `Q` here vs raw SQL in `lateral_fetch.py::build_lateral_sql`
   (F-A), verified by `window_predicate_signature` + recognizers (F-E);
   (b) `KeysetSeekPlan` rendered as `Q` (`keyset_seek_q`), SQL
   (`keyset_seek_sql`), and filtered running count
   (`_apply_keyset_counted_window`) (F-B); (c) GraphQL `path` linked
   list walked once by `runtime_path_from_path` into resolver keys
   consumed at resolve time (F-H); (d) merge field inventory ↔
   `_assert_merge_field_inventory` module-level gate (F-G structural).
   The three plan shapes from the item brief — window (plain / reverse
   / marker / probe branches), seek (count-free filter branch +
   counted helper), nested (`Prefetch(queryset=windowed child)` via
   `nested_fetch.py:317` + walker/nested_planner merge discipline) —
   all compose the same two owners; `_apply_keyset_counted_window` is a
   branch helper called once (`:1081`), not a twin renderer.
5. Contracts restated in another medium: every production rule below
   lists its oracles (package tests above) and projections (docstrings
   + the prose cites above). Test/doc sites listed, never counted.
   PG-tier oracles cited where they exist, not counted.
6. Enforcement by omission: every `FetchMode` has a rendering or a named
   loud refusal in `apply_window_pagination` (COUNTED / count-free seek
   / PROBED sentinel / NONE; `reverse` + `keyset_seek` raises
   `OptimizerError`); unwindowable kinds raise in the partition shim
   while the planner refuses strategy-independently; diff/prune
   consumer-wins arms enumerated (C7/C8); the walker seal policy
   (ledgered D1) lives in `walker.py` — zero `seal` hits in this file,
   no overlap; the reverse-map naming atom lives in
   `mutations/inputs.py` — zero `python_attr` hits here, no overlap.
   No omission gap on this file's surface.

### Enumeration

Instrument: every name in `ast.Module.body` of
`django_strawberry_framework/optimizer/plans.py` (no import of the target;
Django settings never touched). Probe:
`docs/dry/temp-tests/dry-file-optimizer__plans/probe_enumeration.py` →
`top_level=53` (`FunctionDef` 32, `ClassDef` 2, `Assign` 6, `ImportFrom`
10, `Import` 1, `Expr` 2), `top_async=[]`, `async_tokens=[]`.
`probe_singledef.py` → all 34 top-level def/class names single-site
(`multi_site=NONE`). `probe_callers.py` + call-site grep disambiguate
prose mentions from real callers (used in the homes below).
`probe_lookups.py` → the three `prefetch_to` read sites (D1 evidence).

41 rule-bearing top-level elements (32 functions + 2 classes + 6
module assigns + the module-level inventory gate call; 47 numbered
members counting the 4 + 7 class methods — the table numbers methods
inside their owner's row except the 7 `OptimizationPlan` lifecycle
methods, which take their own rows #6–12). The 11 imports
and the module docstring are consumers/projections, not rules. Every
rule-bearing member lands in exactly one home; `OptimizationPlan`
field docstrings and the `_IndexedList` hot-loop comments are covered
inside their owner's row.

| # | Member | Home |
|---|---|---|
| 1 | `_lookup_path` | F-N `prefetch-lookup-path-read` (definition; D1-coupled) |
| 2 | `_IndexedList` (+ 4 methods) | F-G `optimization-plan-record` (dedupe sub-row) |
| 3 | `_indexed_list` | F-G (string-directive factory) |
| 4 | `_prefetch_indexed_list` | F-G (lookup-keyed factory) |
| 5 | `OptimizationPlan` record (5 directive fields + 2 path-key dicts + 3 `finalized_*` + `cacheable` + 3 inventory ClassVars) | F-G (record sub-row) |
| 6 | `is_empty` | F-G (consumer: `extension.py:1247,1250`) |
| 7 | `finalize` | F-G (lifecycle sub-row) |
| 8 | `apply` | F-G (consumer: `extension.py:1252`) |
| 9 | `merge_from` | F-G (consumers: `walker.py:1574`, `nested_planner.py:1422`) |
| 10 | `merge_metadata_from` | F-G (consumers: `walker.py:1227`, `nested_planner.py:1445`) |
| 11 | `_assert_under_construction` | F-G (merge guard) |
| 12 | `_assert_merge_field_inventory` + module call `:373` | F-G (structural gate) |
| 13 | `resolver_key` | F-H `resolver-key-grammar` (consumers: walker, extension, `types/resolvers.py:55`, connection prose, `nested_planner.py`) |
| 14 | `runtime_path_from_info` | F-H (consumers: `extension.py:652,683,1534`, walker, types/resolvers) |
| 15 | `_MAX_PATH_DEPTH` | F-H (walk bound) |
| 16 | `runtime_path_from_path` | F-H (in-file + walker-adjacent use) |
| 17 | `_flatten_select_related` | F-I `consumer-queryset-reconciliation` |
| 18 | `append_unique` | F-G (consumers: walker, nested_planner) |
| 19 | `append_unique_many` | F-G (consumers: walker, nested_planner) |
| 20 | `append_prefetch_unique` | F-G (consumers: `walker.py`, `nested_fetch.py:80`) |
| 21 | `_consumer_prefetch_lookups` | F-I |
| 22 | `deferred_loading_of` | F-E `nested-recognizer-shared-vocabulary` (definition owned here; consumers `nested_planner.py:720`, `lateral_fetch.py:1165`) |
| 23 | `_consumer_only_fields` | F-I (used by `diff_plan_for_queryset:1320`) |
| 24 | `prune_unsupportable_select_related` | F-J `select-related-prune-under-projection` (consumer: `extension.py:1239`) |
| 25 | `_consumer_projection` | F-J |
| 26 | `_select_path_traversable` | F-J (R-3-adjacent, rejected twin) |
| 27 | `_optimizer_can_absorb` | F-I (used by `_diff_prefetch_related:1416`) |
| 28–32 | `WINDOW_ROW_NUMBER` / `WINDOW_TOTAL_COUNT` / `WINDOW_ROW_NUMBER_REVERSED` / `WINDOW_ROW_NUMBER_ABS` / `WINDOW_KEYSET_SEEK_COUNT` | F-A `window-range-dual-render` (annotation namespace; F-B + F-E compose by name) |
| 33 | `order_entry_name_and_direction` | F-L `order-entry-vocabulary` (consumers: nested_planner shim, lateral `_order_columns`, connection keyset guard, `ends_in_unique_column:833`) |
| 34 | `order_entry_has_explicit_nulls` | F-L (consumers: `connection.py:826`, `nested_planner.py:258`) |
| 35 | `ends_in_unique_column` | F-K `connection-order-ladder` (consumer: `connection.py:85,134` alias) |
| 36 | `effective_connection_order` | F-K (consumers: `connection.py:1746`, nested_planner) |
| 37 | `deterministic_order` | F-K (consumer: nested_planner; R-2-adjacent, rejected twin) |
| 38 | `window_partition_for_prefetch` | F-M `window-partition-resolution` (zero production callers — tests only) |
| 39 | `apply_window_pagination` | F-A (ORM renderer; sole production call `nested_fetch.py:317`) + F-B (seek branches) |
| 40 | `_apply_keyset_counted_window` | F-B (called once at `:1081`; lateral prose cite only) |
| 41 | `_reverse_order_by` | F-A (reverse-branch helper; R-1-adjacent, rejected twin) |
| 42 | `diff_plan_for_queryset` | F-I (consumer: `extension.py:1248`) |
| 43 | `_diff_select_related` | F-I |
| 44 | `_diff_prefetch_related` | F-I |
| 45 | `lookup_paths` | F-I (consumer: `extension.py:1380`) |
| 46 | `_lookup_paths_from_parts` | F-I (used by `finalize:284` + `lookup_paths`) |
| 47 | `_prefetch_lookup_paths` | F-I (contains the second `prefetch_to` read at `:1462` — F-N-noted) |

No file-local rows: every member has a consumer, a twin candidate, or a
family home above (a row naming a second site is a family or a rejection,
never file-local). No consolidation in this file item.

### Challenges

Change challenges posit a plausible rule change and count AUTHORITATIVE
definitions that must move (consumers / oracles / projections listed, not
counted). All `static-reviewed` against the pinned blob; inspection beats
execution on every challenge (body identity + `def`-census + import
census decide each count), so no shared-tree pytest run was made.

- C1 (F-A): render offset pages with an inclusive floor (`rn > %s` →
  `rn >= %s`). Moves: `apply_window_pagination` (ORM `Q`) +
  `lateral_fetch.py::build_lateral_sql` (SQL text) = 2 bodies;
  `window_range_plan` decisions unmoved. Count: 2 bodies, 1 decision
  owner. Oracles: `TestApplyWindowPagination` + lateral range rows.
- C2 (F-A/F-E vocabulary): add a sixth window annotation. Moves: the 5-
  constant namespace (1 definition); lateral `_WINDOW_ANNOTATIONS`,
  connection reads, single-parent read follow by name. Count: 1.
- C3 (F-B): drop the redundant leading bound from the seek shape. Moves:
  `keyset_seek_q` + `keyset_seek_sql` + `_keyset_seek_quals_match` = 3
  bodies under 1 plan owner (`build_keyset_seek_plan` unmoved);
  plans seek branches + lateral adapter follow by name. Count: 1 owner.
- C4 (F-C): allow probe + count together. Moves:
  `assert_window_fetch_mode_for` = 1; both `__post_init__`s and the
  `apply_window_pagination:1078` call follow. Count: 1.
- C5 (F-G): add a sixth directive field to the plan. Moves: the
  `OptimizationPlan` declaration + inventory sets + merge arms (1 owner
  machinery; the `_assert_merge_field_inventory` gate fails until the
  field is classified); walker/nested_planner writers follow. Count: 1.
- C6 (F-H): change the resolver-key grammar (e.g. drop the `@path`
  suffix). Moves: `resolver_key` + `runtime_path_*` (1 site);
  walker/extension/types-resolvers follow. Count: 1.
- C7 (F-I): change the consumer-wins drop shape (e.g. absorb custom
  `Prefetch` subtrees). Moves: `_diff_prefetch_related` +
  `_optimizer_can_absorb` (1); extension follows. Count: 1.
- C8 (F-J): change `defer()`-mode traversability (e.g. dotted defer
  entries block). Moves: `_select_path_traversable` (1); prune follows.
  Count: 1.
- C9 (F-K): change the tiebreak column (pk attname → qualified ref).
  Moves: `deterministic_order` (1); connection + nested_planner follow;
  `list_field.py` untouched (R-2). Count: 1.
- C10 (F-L): change the dash rule (e.g. reject `"--name"`). Moves:
  `order_entry_name_and_direction` (1); nested_planner shim,
  `_order_columns`, connection guard, `ends_in_unique_column` follow.
  Count: 1.
- C11 (F-N/D1): Django renames `Prefetch.prefetch_to`. Moves:
  `_lookup_path` + `_prefetch_lookup_paths:1462` inline +
  `walker.py:1134` inline = 3 spellings across 2 files. Count: 3 (the
  D1 evidence — the centralization claim is false).
- C12 (F-M): add a new windowable relation kind. Moves:
  `WINDOWABLE_RELATION_KINDS` + `classify_relation_join` (1,
  join_taxonomy owner); the shim + `request.join.partition_expr`
  readers follow. Count: 1. (Join_taxonomy internals dirty-concurrent;
  the family item re-verifies values there.)
- C13 (R-1): swap NULLS placement on reversal. Moves: `_reverse_order_by`
  only (1); lateral `order_sql` unaffected (downgrades those shapes).
- C14 (R-2): treat `"?"` under extra-ordering as ordered. Moves:
  `list_field.py` only (1); the ladder untouched — and C9 shows the
  reverse. Independence both directions.
- C15 (R-3): return hop records instead of a bool from the prune walk.
  Moves: the prune call site only (1); `classify_path` keeps raising.
- C16 (R-4): accept relation traversal in `cursor_field`. Moves:
  `split_order_ref` only (1); the connection parser keeps returning
  `("a__b", False)` for `ends_in_unique_column` to refuse.
- C17 (R-5): rename `partition_expr`. Moves: the classifier (1);
  readers follow. Forward-M2M connector answers come from
  `_parent_join_column`, unmoved.

## Findings

Worker 0 note: families F-G..F-N are NAMED here for the plan's
`## Responsibility index`; F-A/F-B/F-C/F-E reuse the open lateral_fetch
rows (re-challenged fresh above — C1/C3 differ in method from the
lateral counts but converge on single-ownership; nothing inherited).
F-D/F-F are discharged inapplicable. No plan edit made from this item;
no consolidation in a file item — the family items decide gates.

### F-A `window-range-dual-render` (reuse; owner `utils/connections.py::window_range_plan`)

Contract: one `WindowRangePlan` decision set rendered twice — ORM `Q`
objects by `apply_window_pagination` (plain / reverse /
`add_marker_rows` / `next_page_probe` branches), raw SQL by
`lateral_fetch.py::build_lateral_sql`. Plans-side members: #39 (plus the
5-constant namespace #28–32, which F-B and F-E compose by name).
Variation axes: slice (`offset`, `limit`, `reverse`,
`next_page_probe`, `with_total_count`, `keyset_counted`). Sites:
definition `utils/connections.py`; renderer here (sole production
activation `nested_fetch.py:317`); verifier lateral recognizers;
oracles `TestApplyWindowPagination` + lateral range rows. Challenges:
C1 (2 bodies, 1 owner), C2 (1). Already-consolidated shape: the shared
plan object exists; renderers compose it by name. `_reverse_order_by`
(#41) is the reverse-branch helper of this renderer; its lateral
counterpart difference is rejected at R-1 with trigger.

### F-B `keyset-seek-dual-dialect` (reuse; owner `keyset.py::build_keyset_seek_plan`)

Contract: one `KeysetSeekPlan` rendered as ORM `Q`, SQL, and filtered
running count. Plans-side members: the count-free seek branch
(`queryset.filter(keyset_seek.q())`), #40 (called once at `:1081`),
`WINDOW_ROW_NUMBER_ABS` / `WINDOW_KEYSET_SEEK_COUNT`. Sites: definition
`keyset.py`; followers here + lateral adapter/verifier; oracles keyset
rows + `TestApplyWindowPagination` keyset shapes. Challenges: C3
(3 bodies, 1 owner). Coordination note: the family item adjudicates
against the keyset owner's own traces if any.

### F-C `window-fetch-mode-guard` (reuse; owner `utils/connections.py::assert_window_fetch_mode_for`)

Contract: probe/count mutual exclusion enforced at construction.
Plans-side member: the `:1078` enforcement call inside
`apply_window_pagination` (consumer, never a second definition).
Challenges: C4 (count 1). Already-single.

### F-E `nested-recognizer-shared-vocabulary` (reuse; owner as indexed — definition sites here noted)

Contract: the window-identity helpers every nested-fetch recognizer
composes by name. Plans-DEFINED members: #22 `deferred_loading_of`
(the single `query.deferred_loading` unpack; consumers
`nested_planner.py:720` + `lateral_fetch.py:1165`) and the `WINDOW_*`
namespace (consumers connection.py, lateral `_WINDOW_ANNOTATIONS`,
single_parent). Challenges: C2 (count 1 per change). Already-single;
the family item adjudicates the owner field between the defining module
(here) and the heaviest-consumer module (lateral) — dependency
direction permits either home, principle 11 forbids a zero-relief move.

### F-D `recognized-fetch-queryset-skeleton` / F-F `nested-fetch-strategy-seam` (inapplicable)

No member of this file defines, enforces, or mirrors either rule: the
skeleton (`RecognizedFetchQuerySet._clone`/`rebind`/`_fetch_all`) and
the strategy registry (`resolve_strategy`, `StrategySelection`) both
live in `nested_fetch.py`; plans builds the `Prefetch` payloads those
mechanisms carry. One line each, no challenge owed beyond the
`def`-census (zero hits here).

### F-G `optimization-plan-record` (new family; owner `optimizer/plans.py::OptimizationPlan`)

Contract: the construction-time plan shape — five directive sequences
(plus two path→keys coupling dicts), three derived `finalized_*`
slots, the `cacheable` flag, and the merge/finalize/apply lifecycle.
Sub-rows for Worker 0: (a) record fields + inventory ClassVars (#5);
(b) dedupe discipline — `_IndexedList` + factories + `append_*` (#2–4,
#18–20; single `def`-census, consumers walker/nested_fetch/
nested_planner by import); (c) merge discipline — `merge_from` /
`merge_metadata_from` + guards (#9–11; the `_FULL_` vs `_METADATA_`
split keeps child-queryset directives off the root plan); (d) lifecycle
— `is_empty` / `finalize` / `apply` (#6–8; consumers
`extension.py:1247,1250,1252`); (e) structural gate —
`_assert_merge_field_inventory` + module call `:373` (#12, fails loud
on unclassified fields). Challenges: C5 (count 1). The gate is the
in-tree structural pin; oracles `TestOptimizationPlan*` +
`TestIndexedList`.

### F-H `resolver-key-grammar` (new family; owner `optimizer/plans.py::resolver_key`)

Contract: branch-sensitive resolver identity — `Type.field@path`
rendering (#13), `info.path` unwrap (#14), linked-list walk with
integer-key stripping and the `_MAX_PATH_DEPTH` cycle ceiling (#15–16).
Consumers: walker, `extension.py`, `types/resolvers.py:55`.
Challenges: C6 (count 1). Oracles `TestRuntimePathFromPath` +
`test_resolver_key_includes_parent_type_and_runtime_path`.

### F-I `consumer-queryset-reconciliation` (new family; owner `optimizer/plans.py::diff_plan_for_queryset`)

Contract: reconcile the built plan against consumer-applied queryset
state without mutating the cached plan — select_related path diff
(#43 + #17), prefetch subtree absorb-or-drop (#44 + #27, with coupled
key stripping), only_fields consumer-wins (#23), lookup-path flatten
(#45–47 + #21). Consumer: `extension.py:1248,1380`. Challenges: C7
(count 1). Oracles `TestDiffPlanForQueryset` + `TestFlattenSelectRelated`
+ `TestConsumerOnlyFields` + `TestLookupPaths`. Note: #47 contains the
second `prefetch_to` read — cross-listed under F-N, not a second home.

### F-J `select-related-prune-under-projection` (new family; owner `optimizer/plans.py::prune_unsupportable_select_related`)

Contract: drop `select_related` paths a consumer projection cannot
traverse (relation-aware per-segment rule in #26, both `defer()` and
`.only()` modes via #25), surrendering the coupled resolver keys and
nested `only_fields`, returning a finalized `replace()` copy so the
cached plan stays intact. Consumer: `extension.py:1239`. Challenges: C8
(count 1). Oracles `TestPruneUnsupportableSelectRelated` +
`test_consumer_projection_and_traversal_defensive_shapes`. The
`classify_path` look-alike is rejected at R-3 with trigger.

### F-K `connection-order-ladder` (new family; owner `optimizer/plans.py::effective_connection_order`)

Contract: the precedence ladder shared by plan-time windows and the
resolve-time pipeline (cursor-parity invariant) — `cursor_field`
default (#36), pk-tiebreaker totalization (#37), unique-terminal check
(#35, hoisted from `connection.py` per spec-033 Decision 11; the
`connection.py:134` alias is a re-export for test pins, never a second
definition). Consumers: `connection.py:1746` + nested_planner.
Challenges: C9 (count 1). Oracles `TestDeterministicOrderHoistParity` +
`TestEffectiveConnectionOrder`. The `list_field.py` look-alike is
rejected at R-2; the lateral reversal difference at R-1.

### F-L `order-entry-vocabulary` (new family; owner `optimizer/plans.py::order_entry_name_and_direction`)

Contract: the single parser of the `deterministic_order` entry
vocabulary — one optional leading `-`, `OrderBy`-expression unwrap,
bare-`F` support, `None` for unresolvable (#33) — plus the explicit-
NULLS predicate (#34) so the planner advisory and the keyset cursor
path cannot disagree on what "explicit" means. Consumers:
`nested_planner.py::_order_entry_field_name` (declared thin shim,
verified body delegates) + `:258` advisory, `lateral_fetch.py::
_order_columns`, `connection.py:826,828`, `ends_in_unique_column:833`.
(`walker.py:80,84` re-export the nested_planner shims, never second
definitions.) Challenges: C10 (count 1). Oracles
`TestOrderEntryHasExplicitNulls`. The `split_order_ref` twin is
rejected at R-4 with trigger.

### F-M `window-partition-resolution` (new family; candidate owner `optimizer/join_taxonomy.py::classify_relation_join`)

Contract: the parent-side partition expression a windowed prefetch
groups by. Members: the #38 shim (classify + kind-gate + loud
`OptimizerError`, kept exported under its historical raise contract),
the parallel `nested_planner.py::_connector_only_field` shim (reads
`parent_join_column`, returns `None`), the production read
`nested_fetch.py:319` (`request.join.partition_expr`, direct —
NOT via the shim). Call-site census: the shim has ZERO production
callers (only `test_plans.py` + `test_walker.py` pins); production
flows through the pre-classified descriptor. Challenges: C12 (count 1).
Question for the family item (principle 11): the shim is a
zero-production-caller wrapper whose historical-raise contract and
test pins are its only readers — keep as a boundary name or delete and
retarget the pins at the classifier. Join_taxonomy internals are
dirty-concurrent (+39 composite-pk); values re-verified there, not here.

### F-N `prefetch-lookup-path-read` (new family; candidate owner `optimizer/plans.py::_lookup_path`)

Contract: reading the Django-private `Prefetch` lookup identity.
Three spellings: (a) `_lookup_path` — strict total read (`getattr`
with self-default, strings pass through), used as the index key fn and
by `append_prefetch_unique` / `_diff_prefetch_related`; (b)
`_prefetch_lookup_paths:1462` inline — lenient `getattr(..., None)` +
skip, needed to tolerate malformed entries during recursive flatten;
(c) `walker.py:1134` inline — `prefetch_to`-with-`prefetch_through`
fallback for rebased hinted prefetches. Challenges: C11 (3 spellings,
2 files). Excluded with reason: `utils/querysets.py:2289`
(`entry_state.get("prefetch_to")` — serialized seal-state dict keys,
different population; clean `96618fba…` both). D1 (below) couples the
prose fix to whatever the family item decides.

### Rejections

- R-1 (reversal rendering): `_reverse_order_by` (direction flip AND
  NULLS swap AND loud `OptimizerError` on unreversible terms) vs
  lateral `order_sql` (direction-only flip; expression/explicit-NULLS
  orders downgrade out at `_order_columns`). Confirms lateral W2's R-1
  fresh from this side (C13: count 1, lateral unaffected). Trigger: the
  lateral backend accepts expression/explicit-NULLS orders. Home:
  `lateral_fetch.py::build_lateral_sql` order rendering.
- R-2 (offset-guard eligibility): `list_field.py::
  _has_deterministic_ordering` family (per-term compiler-shape predicate
  on the queryset Django will run) vs F-K (entry-tuple constructor
  making total via unique-terminal + pk). Verified: zero references to
  `plans.deterministic_order` in `list_field.py` — shared token only.
  C9/C14 count 1 each, both directions. Trigger: the offset guard
  consumes `effective_connection_order`, or a caller needs
  compiled-queryset totality by uniqueness. Home:
  `list_field.py::_has_deterministic_ordering`.
- R-3 (path walkers): `_select_path_traversable` (bool traversability
  under a consumer projection, for prune) vs
  `utils/relations.py::classify_path` (immutable hop-record plan,
  raises `PathResolutionError`). Confirms the plan's rejected
  `orm-lookup-path-resolution` row fresh (C15: count 1 each). Trigger
  recorded at the owner — worktree `relations.py` docstring clause
  (concurrent +14, worktree `1cf81e58…`; bodies HEAD-identical, so the
  difference holds at both blobs). Home:
  `utils/relations.py::classify_path`.
- R-4 (order-string twins): `keyset.py::split_order_ref` (loud
  `ConfigurationError`, no traversal, no expressions — configuration
  contract) vs `order_entry_name_and_direction` string branch (total,
  `None`-returning fallback parser; `"--x"` and `"a__b"` behave
  differently by design). C16 counts 1 each. Trigger: `cursor_field`
  accepts expressions, or connection order becomes loud. Home:
  `keyset.py::split_order_ref` (twin declared at its docstring,
  clean `df4b5e2f…` both).
- R-5 (parent-link columns): `window_partition_for_prefetch`
  (`partition_expr` for `PARTITION BY`, loud) vs
  `nested_planner._connector_only_field` (`parent_join_column` for
  `.only()` projection, `None`-lenient). Coincide on reverse-FK,
  diverge on both M2M directions — different facts, one classifier.
  C17 counts 1 (classifier; readers follow). Trigger: the classifier
  unifies the two columns, or one caller needs both answers. Home:
  `join_taxonomy.py::RelationJoinDescriptor`.

## Defects

- D1 (prose-only; UNFIXED): `optimizer/plans.py::_lookup_path`
  docstring claims the helper "Centralizes the brittle Django-private
  contract for `Prefetch.prefetch_to` so a future Django rename has one
  fix", but two inline reads of the same attribute exist and would not
  follow: `plans.py:1462` (`_prefetch_lookup_paths`,
  `getattr(entry, "prefetch_to", None)` + skip) and `walker.py:1134`
  (hinted branch, `getattr(rebased_prefetch, "prefetch_to", None)` with
  a `prefetch_through` fallback; clean `9b111ed9…` both). A rename
  needs 3 edits (C11), not one. The bodies behave correctly — this is a
  false single-fix promise, not a behavior bug. Owner:
  `optimizer/plans.py::_lookup_path`. Coupling: F-N carries the
  consolidation question (unify the reads vs record the three
  contracts); the prose fix lands with whichever the family item
  decides. Blocks nothing.

No other defect bar met. Audited and cleared: `merge_from` /
`merge_metadata_from` finalized-plan guards match the documented
cache invariant; `finalize()` idempotence claim matches the
tuple-rebuild body; `diff_plan_for_queryset` "copied never mutated"
matches the early `(plan, queryset)` return + `replace()` tails;
`_IndexedList` non-index-maintaining-mutator warning matches the three
overridden entry points; the `is_empty`/`cacheable` trigger clause is
already recorded in the docstring; the "Constructed by
`plan_optimizations`" clause resolves (`walker.py:142`).

## Pending execution

None. Zero-edit file item; every proof above is `static-reviewed`
(body identity, single-`def` census, import census, call-site grep).
Read-only probes (AST/text only, target never imported, no Django
settings touched):

- `uv run python docs/dry/temp-tests/dry-file-optimizer__plans/probe_enumeration.py`
  → `top_level=53 top_async=[] async_tokens=[]` (blob `cce98531…`
  pinned via `git hash-object`, not the probe's raw sha1).
- `uv run python docs/dry/temp-tests/dry-file-optimizer__plans/probe_singledef.py`
  → `target_defs=34 multi_site=NONE`.
- `uv run python docs/dry/temp-tests/dry-file-optimizer__plans/probe_lookups.py`
  → the three `prefetch_to` read sites (D1 evidence).
- `uv run python docs/dry/temp-tests/dry-file-optimizer__plans/probe_callers.py`
  + call-site greps → prose mentions separated from real callers
  (notably: `apply_window_pagination(` has exactly one production
  caller; `window_partition_for_prefetch(` has zero).

No shared-tree pytest run: the entry command does not authorize one,
and inspection decides every count above. PG-tier (`test_lateral_pg_parity.py`)
and sharded cells stay `unverified` (need the maintainer's separate word).

## Judgment

File item discharged with zero edits: 41 top-level rule-bearing
elements (47 numbered members counting methods) assigned
(6 reused open families F-A/F-B/F-C/F-E + 2 discharged inapplicable
F-D/F-F; 8 new families F-G..F-N named for Worker 0; 5 rejections with
difference + trigger + home; no file-local rows — every member has a
consumer, a twin candidate, or a family home), matrix discharged on all
six axes (window/seek/nested shapes composed from shared owners;
sync/async inapplicable by construction), challenges counted (C1–C17,
every count 1 except the C1 2-body/1-owner and C11 3-spelling records).
One prose defect filed (D1, unfixed, owned). The file composes its
owners by name throughout; the only multi-spelling definition it
carries (F-N) is filed for the family item with its coupling defect.

## Freshness fingerprints

HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`. Target
`django_strawberry_framework/optimizer/plans.py` clean:
worktree `cce985319c8833f3660653327d3003f1f03655a5` = HEAD (1471
lines). Item-scoped diff vs `fd19accc` on target + artifact path: EMPTY
(no production edit; this artifact is the only new file, untracked).
Neighbors (worktree read; HEAD alongside where dirty): `optimizer/
walker.py` clean `9b111ed9…` both; `optimizer/extension.py` clean
`49667a93…` both; `optimizer/nested_fetch.py` worktree `29ce5201…` vs
HEAD `4d8d37a7…` (dirt in `resolve_strategy` only; `:317` call
HEAD-identical); `optimizer/nested_planner.py` worktree `e69dbf5f…` vs
HEAD `0ad8ff5d…` (hunk at 609 only; shims/merges/KeysetSeek/cacheable
lines HEAD-identical); `optimizer/join_taxonomy.py` worktree
`e1cbb3e3…` vs HEAD `9b355a50…` (prose cites at 33/77 outside the
175/183/200/329 hunks); `optimizer/single_parent_fetch.py` clean
`e995270a…` both; `optimizer/lateral_fetch.py` clean `db1ea315…` both;
`optimizer/selections.py` clean `a48f6172…` both; `keyset.py` clean
`df4b5e2f…` both; `utils/connections.py` clean `f549389e…` both;
`utils/querysets.py` clean `96618fba…` both; `connection.py` worktree
`3c4d5dcb…` vs HEAD `93e998f2…` (hunks 54/703/734; all cited lines
HEAD-identical); `list_field.py` worktree `d6af6164…` vs HEAD
`ce682d5f…` (hunk at 235 only); `types/resolvers.py` worktree
`5f4cce2b…` vs HEAD `f3341e6a…` (import line intact);
`utils/relations.py` worktree `1cf81e58…` vs HEAD `7662b0bb…`
(docstring-only +14; bodies identical); `exceptions.py` clean
`e06b0b7f…` both; `tests/optimizer/test_plans.py` clean `1e09d6d…`
both. Any fingerprint change reopens the finding.

## Independent verification (Worker 2)

Worker 2, phase 1. Target read whole before writing anything here. The phase-2
artifact sections were not opened; one grep sweep over docs/ incidentally
surfaced a single table row of the existing artifact and was excluded from all
further searches. No status is set and no verdict on Worker 1 is proposed.

### Target and scope

- Target: django_strawberry_framework/optimizer/plans.py, 1471 lines,
  worktree-clean (worktree blob equals HEAD blob; see fingerprints).
- No production edit made or owed (file item: validate coverage and assignment,
  route candidates to holding families).
- Neighbors traced where the target leads (read freely, never edited):
  optimizer/nested_fetch.py, optimizer/nested_planner.py,
  optimizer/join_taxonomy.py, optimizer/walker.py, optimizer/extension.py,
  optimizer/lateral_fetch.py, utils/connections.py, keyset.py, list_field.py,
  connection.py. Dirty ones are concurrent work; cited regions were diffed
  against HEAD and are unaffected by the concurrent hunks (see fingerprints).
- Contracts: docs/dry/DRY.md principles 4/5/7/8/11; GOAL.md success
  criterion 5 (one selection-tree walk emitting select_related /
  prefetch_related / only() cooperating with consumer querysets).

### Enumeration

Instrument: every name in ast.Module.body of the target (53 members, indices
0-52). Count confirmed by re-parse. Every member lands in exactly one home
below. Families are Worker-2-named (F-A through F-G); R-1 through R-8 are
Worker-2 rejections; file-local rows carry the challenge that found no second
site.

- F-A plan-directive-dedupe-shape: _IndexedList (13) with its methods
  __init__ / append_unique / append / extend, _indexed_list (14),
  _prefetch_indexed_list (15), append_unique (23), append_unique_many (24),
  append_prefetch_unique (25). The dedupe discipline as a property of the
  plan list shape.
- F-B plan-lifecycle: module docstring (0, projection of this family),
  OptimizationPlan (16) with all fields (select_related, prefetch_related,
  only_fields, fk_id_elisions, planned_resolver_keys,
  select_path_resolver_keys, prefetch_path_resolver_keys, _FULL_MERGE_FIELDS,
  _METADATA_MERGE_FIELDS, _DERIVED_FINALIZED_FIELDS, finalized_fk_id_elisions,
  finalized_planned_resolver_keys, finalized_lookup_paths, cacheable), methods
  is_empty / finalize / apply / merge_from / merge_metadata_from /
  _assert_under_construction / _assert_merge_field_inventory, and the
  module-level OptimizationPlan._assert_merge_field_inventory() call (17).
- F-C resolver-identity: resolver_key (18), runtime_path_from_info (19),
  runtime_path_from_path (21).
- F-D consumer-reconciliation: _flatten_select_related (22),
  _consumer_prefetch_lookups (26), deferred_loading_of (27),
  _consumer_only_fields (28), prune_unsupportable_select_related (29),
  _consumer_projection (30), _select_path_traversable (31),
  _optimizer_can_absorb (32), diff_plan_for_queryset (47),
  _diff_select_related (48), _diff_prefetch_related (49).
- F-E order-vocabulary: order_entry_name_and_direction (38),
  order_entry_has_explicit_nulls (39), ends_in_unique_column (40),
  effective_connection_order (41), deterministic_order (42).
- F-F window-rendering: WINDOW_ROW_NUMBER (33), WINDOW_TOTAL_COUNT (34),
  WINDOW_ROW_NUMBER_REVERSED (35), WINDOW_ROW_NUMBER_ABS (36),
  WINDOW_KEYSET_SEEK_COUNT (37), window_partition_for_prefetch (43),
  apply_window_pagination (44), _apply_keyset_counted_window (45),
  _reverse_order_by (46).
- F-G lookup-path-derivation: _lookup_path (12), lookup_paths (50),
  _lookup_paths_from_parts (51), _prefetch_lookup_paths (52). _lookup_path
  also serves F-A as the _prefetch_indexed_list key callable and F-D as the
  diff key reader; single home is F-G (its contract is the Django prefetch
  lookup path), the other two are recorded consumers.
- File-local, import surface, no rule defined: imports (1-11):
  __future__.annotations, contextlib, collections.abc, dataclasses, typing,
  django.core.exceptions, django.db.models, django.db.models.functions,
  exceptions::OptimizerError, utils/connections::assert_window_fetch_mode and
  window_range_plan, join_taxonomy::WINDOWABLE_RELATION_KINDS and
  classify_relation_join. Challenge "a second definition of the import
  discipline" found none; second site would be a family row, not file-local.
- File-local, single constant: _MAX_PATH_DEPTH (20). Serves only
  runtime_path_from_path (21) as the cyclic-prev-chain ceiling. Challenge
  "another path-depth bound in the package" found none.
- Rejections (Worker-2 naming, contract difference plus trigger):
  - R-1 keyset.py::split_order_ref versus F-E string branch: keyset malformed
    entry is a loud ConfigurationError, plans-parser None is a fallback
    signal; keyset forbids relation traversal. Trigger: keyset accepts
    expressions or the plans parser raises configuration errors.
  - R-2 list_field.py deterministic-order CHECKER
    (_is_deterministic_order_term and kin) versus F-E deterministic_order
    CONSTRUCTOR: certifying an existing ordering total versus making one
    total by appending the pk. Trigger: either side takes the other's job.
  - R-3 nested_planner.py::_index_leading_terms dash parse (Index.fields
    declarations) versus F-E dash rule (order_by request vocabulary):
    declaration versus request grammar. Trigger: indexes accept full
    order-entry expressions.
  - R-4 walker.py private-alias bindings (same objects from nested_planner,
    documented compatibility aliases with stated readers): alias, not
    definition. Trigger: an alias diverges into a copied body.
  - R-5 connection.py::_ends_in_unique_column alias (documented re-export of
    F-E ends_in_unique_column for spec-030 pins): same object. Trigger: same
    as R-4.
  - R-6 utils/querysets.py sealed-prefetch readers (state-dict snapshot for
    the immutability seal) versus F-D live-queryset readers (getattr on the
    queryset for planning): different objects, different responsibilities.
    Trigger: the sealer reads live queryset attributes directly.
  - R-7 merge_from versus merge_metadata_from (both F-B): full construction
    commit versus child-metadata-only commit; two operations, distinct
    contracts, shared field handling. Trigger: a third merge shape appears.
  - R-8 _consumer_only_fields versus _consumer_projection (both F-D):
    only-shape predicate versus any-projection predicate; diff drops
    only_fields on .only() while prune traverses under .defer() too.
    Trigger: .defer() starts dropping only_fields in diff.

### Matrix discharged

- Window versus seek versus nested plan shapes: three renderers, one
  decision owner. Decisions live once in
  utils/connections.py::window_range_plan (bounds, markers, probe) with
  utils/connections.py::assert_window_fetch_mode enforcing probe XOR count.
  django_strawberry_framework/optimizer/plans.py::apply_window_pagination
  owns only the ORM Q-object rendering; optimizer/lateral_fetch.py renders
  the same plan as raw SQL and explicitly downgrades the counted-keyset
  shape to windowed (lateral_fetch.py "Counted keyset seek" guard) rather
  than growing a second marker arithmetic; utils/connections.py::split_window_rows
  plus connection.py::_resolve_from_window consume. Searched: window_range_plan,
  apply_window_pagination, fetch_upper_bound/fetch_limit, split_window_rows,
  LateralWindowSpec/NestedConnectionRequest construction asserts. No second
  bounds/marker/sentinel definition in the target.
- Sync/async twins: target has zero async def and zero await (verified by
  grep); apply/merge/finalize build or transform querysets lazily and touch
  no ORM execution, so no await boundary exists to twin. The package's
  contrasting sync/async answers (single sync body behind one sync_to_async
  boundary for the write pipeline; two colored bodies in connection.py) do
  not reach this target. Axis inapplicable with reason stated.
- Round-trip pairs: runtime_path_from_info delegates to
  runtime_path_from_path (one direction, not a pair); finalize/apply are
  lifecycle steps, not inverses; lookup_paths/_lookup_paths_from_parts/
  _prefetch_lookup_paths are one derivation with two private helpers;
  finalize publishes finalized_* sets that lookup_paths prefers when
  present (fast path, same derivation). Searched: every def pair in the
  target for encode/decode, pack/unpack, build/parse shape. None found.
- Cross-flavor mirroring: the target is optimizer-internal; no sibling
  public surface (types, filters, orders, mutations, forms, rest_framework)
  carries optimizer plans. Nearest look-alikes adjudicated as R-1 (keyset
  cursor order syntax) and R-2 (list_field order certification). Searched
  sibling flavors for plan/directive/merge duplicates; none found.
- Derived rather than repeated knowledge: order-entry parsing shared via
  F-E (nested_planner, lateral_fetch, connection all call in; keyset twin
  rejected R-1); deferred-loading unpack shared via deferred_loading_of
  (lateral_fetch and nested_planner call in; claim verified true, sole
  .deferred_loading attribute read at plans.py deferred_loading_of
  "deferred_loading = getattr(query, ...)"); select_related flattening
  single (_flatten_select_related, sole query.select_related reader);
  connector/partition facts delegated to join_taxonomy
  (classify_relation_join) with thin shims. Exception: prefetch_to is read
  in three spellings (see D1 below).
- Contracts in other media: tests/optimizer/test_plans.py pins behavior
  with literal expectations (e.g. is_empty cases including the
  cacheable-flag exclusion; window_partition_for_prefetch per-kind values;
  absorb/upgrade rules) and its docstring tiers consumer-visible SQL to
  the fakeshop live tests -- independent oracles, none rewritten to read
  from the owner. Docs prose references plans symbols as projections
  (verified by filename sweep only; artifact excluded). No oracle derives
  from the owner it checks.
- Enforcement by omission: is_empty excludes cacheable (pinned by
  test_cacheable_flag_does_not_affect_empty_state with a stated revisit
  trigger), the path-key dicts (pure metadata, unreachable without their
  directives: writers always pair them, prune/diff strip them together),
  and finalized_* (derived). Merge inventory
  (OptimizationPlan._assert_merge_field_inventory, executed at import)
  forces every future field into _FULL/_METADATA/_DERIVED ownership.
  _IndexedList non-indexed mutators are a documented usage constraint with
  no wire-reachable caller (internal builders only). WINDOW_ROW_NUMBER_ABS
  and WINDOW_KEYSET_SEEK_COUNT exist only on the counted-keyset branch and
  every reader uses getattr defaults (connection.py seek_total None arm);
  lateral refuses that branch. _reverse_order_by raises OptimizerError
  (not ValueError/TypeError) so the walker cannot swallow it; same posture
  as the keyset-plus-reverse guard. No omission gap with a contract source
  establishing coverage was found; the one overclaim is D1.

### Challenges and definition counts

- C1 Django renames Prefetch.prefetch_to: _lookup_path,
  _prefetch_lookup_paths prefetch_to getattr, walker.py hinted-Prefetch
  getattr = 3 live reads (plus the sealed-state dict key in
  utils/querysets.py, adjacent layer per R-6). Count larger than 1: see D1.
- C2 new order-entry shape: order_entry_name_and_direction = 1. Consumers
  (nested_planner UNKNOWN/downgrade, lateral downgrade, connection reject)
  adapt without moving. Index-declaration parsing (R-3) unaffected.
- C3 pk-tiebreaker rule change: ends_in_unique_column = 1 (deterministic_order
  delegates; effective_connection_order composes). Connection alias (R-5) is
  the same object.
- C4 marker/sentinel arithmetic change: decided once in
  utils/connections.py::window_range_plan; target renders once in
  apply_window_pagination. Target count = 1 renderer, no second definition.
- C5 deferred_loading shape change: deferred_loading_of = 1. Lateral,
  nested_planner, _consumer_only_fields, _consumer_projection consume.
- C6 _prefetch_related_lookups change: _consumer_prefetch_lookups = 1 for
  live reads (sealed layer rejected R-6).
- C7 select_related wildcard semantics change: _flatten_select_related = 1.
- C8 resolver-key grammar change: resolver_key = 1 (runtime path helpers
  feed it; types/resolvers, walker, extension consume).
- C9 new plan directive field: the import-time inventory assert forces one
  classification into _FULL/_METADATA/_DERIVED; merge_from versus
  merge_metadata_from stay two contracts (R-7). Rule count = 1 decision
  point.
- C10 absorb-rule change (e.g. absorbing consumer Prefetch): 
  _optimizer_can_absorb = 1.
- C11 defer() drops only_fields in diff: _consumer_only_fields = 1; the
  only-versus-projection pair stays two rules (R-8).
- C12 M2M partition expression change: join_taxonomy.py::classify_relation_join
  = 1; window_partition_for_prefetch delegates (0 production callers; see
  holding route below).

### Owners Worker 2 would choose

- Dedupe discipline (F-A): plans.py _IndexedList/append_* -- plan-shape
  property; every writer already routes through it. Keep.
- Plan lifecycle and merge (F-B): OptimizationPlan with the inventory
  assert as gate. Keep.
- Resolver identity (F-C): plans.py resolver_key/runtime_path_* --
  narrowest module importable without cycles by types/resolvers, walker,
  extension. Keep.
- Consumer reconciliation (F-D): plans.py diff_plan_for_queryset and
  prune_unsupportable_select_related with their helpers. Keep.
- Order vocabulary and deterministic order (F-E):
  plans.py order_entry_*/ends_in_unique_column/effective_connection_order/deterministic_order.
  Keep; connection re-export stays an alias.
- Window rendering (F-F): decisions in utils/connections.py::window_range_plan,
  ORM rendering in plans.py::apply_window_pagination, lateral as second
  renderer of the same decisions. Keep the decide/render split; record at
  both owners (already recorded in both docstrings).
- Lookup-path derivation (F-G): plans.py lookup_paths family. Keep.
- Deferred-loading read: plans.py::deferred_loading_of. Keep (verified
  single reader).
- Join classification: join_taxonomy.py::classify_relation_join. Keep;
  route the shim below to its holding family.
- Holding-family routes (file item owes no edit): window-partition shim
  (target, zero production callers) and its neighbor twin
  nested_planner.py::_connector_only_field (zero production callers, tests
  only) belong to one holding family on join_taxonomy ownership
  (classify_relation_join), disposition deletion-versus-keep-for-pins to be
  decided there with its tests.

### Defects (Worker 2)

- D1 (Worker 2): plans.py::_lookup_path centralization docstring
  ("Centralizes the brittle Django-private contract for
  Prefetch.prefetch_to so a future Django rename has one fix") is
  contradicted by two direct readers: walker.py hinted-Prefetch branch
  (getattr prefetch_to with prefetch_through fallback) and plans.py
  _prefetch_lookup_paths (getattr prefetch_to with None default and skip).
  Contract row: DRY.md principle 10 (a wrong stated reason is worse than
  none; the next author honors the single-fix claim) and principle 6
  (compose by name). Reaching inputs, both feasible under supported public
  API: (a) any GraphQL request against a type carrying
  OptimizerHint.prefetch with a consumer Prefetch reaches the walker
  branch through the wire query; (b) any nested-connection plan carrying
  Prefetch entries reaches _prefetch_lookup_paths via lookup_paths and the
  extension context stash on every planned request. Owner:
  django_strawberry_framework/optimizer/plans.py::_lookup_path. No
  behavior divergence is claimed; the defect is the false single-fix
  ownership statement. Not fixed here (file item; Worker 0 homes it).
- Explicit attention items: (a) shims with zero production callers --
  exactly one in the target: window_partition_for_prefetch (public, defined
  plans.py window_partition_for_prefetch, called only by tests; prose
  mentions elsewhere are not calls). Neighbor twin with the same shape:
  nested_planner.py::_connector_only_field (tests only). Both routed to
  the holding family above; neither is deleted here. All other public
  target symbols have at least one production caller (searched package-wide;
  exact-match greps for _lookup_path(, runtime_path_from_path,
  _IndexedList/_indexed_list/_prefetch_indexed_list, _MAX_PATH_DEPTH, and
  every public helper). (b) centralization docstrings -- deferred_loading_of
  ("THE single reader") verified TRUE (sole .deferred_loading attribute
  read; lateral_fetch and nested_planner consume through it);
  _consumer_prefetch_lookups ("Centralizes ... _prefetch_related_lookups")
  verified TRUE for live reads (sole attribute read; sealed-state dict
  access is a different object per R-6); _lookup_path claim FALSE per D1.
  (c) triple-reads -- prefetch_to in three spellings with three different
  defaults (entry-itself, None-skip, None-or-through-fallback) per D1; no
  other same-attribute triple-read was found (descending/nulls reads all
  route through F-E except the Index-declaration vocabulary per R-3;
  deferred_loading/select_related/prefetch-lookups each have one live
  reader).

### Freshness fingerprints (HEAD bfaee91d)

HEAD blob ids (git rev-parse HEAD:path); worktree blob ids (git hash-object)
match HEAD for every clean file. Dirty files list worktree and HEAD
separately; cited regions were verified unaffected by the concurrent hunks.

- CLEAN django_strawberry_framework/optimizer/plans.py
  cce985319c8833f3660653327d3003f1f03655a5
- DIRTY django_strawberry_framework/optimizer/nested_fetch.py
  worktree=29ce5201877864b01079c849b92a1e812166affd
  HEAD=4d8d37a7f52cf94d2916f17db3a8a21393e28d57 (concurrent:
  resolve_strategy hostile-subclass hardening; cited import/call sites
  unaffected)
- DIRTY django_strawberry_framework/optimizer/nested_planner.py
  worktree=e69dbf5f30aa4623a5aad93edfacdabb391d6601
  HEAD=0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04 (concurrent: M2M
  advisory silence in _advise_composite_index; cited shims/order helpers
  unaffected)
- DIRTY django_strawberry_framework/optimizer/join_taxonomy.py
  worktree=e1cbb3e327785de3b59ccafef6b463df52e06396
  HEAD=9b355a5090ce471e373849dd0a61da8f808e78b9 (concurrent: virtual
  ForeignObject link handling; classifier ownership and shim contract
  hold in both)
- CLEAN django_strawberry_framework/optimizer/walker.py
  9b111ed938951a073a9226ccbcfacabc3af981e8
- CLEAN django_strawberry_framework/optimizer/extension.py
  49667a9370cef73fdf4a170fe9bafa3a1eb19a2a
- CLEAN django_strawberry_framework/optimizer/lateral_fetch.py
  db1ea315d774f55e893c108c6e0bc995299a9fa2
- CLEAN django_strawberry_framework/utils/connections.py
  f549389ef0ed97bfbe4b158ab21bfc993b71b714
- CLEAN django_strawberry_framework/keyset.py
  df4b5e2f105c2b9fa956eac7cea25ba8a0a8de80
- DIRTY django_strawberry_framework/list_field.py
  worktree=d6af61646784deac2f3053bb4096b8599deae2f5
  HEAD=ce682d5f79518919ff3676f2fc8bbe2bd33995a4 (concurrent:
  docstring-only reconsideration triggers; _is_deterministic_order_*
  family untouched)
- DIRTY django_strawberry_framework/connection.py
  worktree=3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a
  HEAD=93e998f2c7ea1d7f18607a6e37e394466ac75ad4 (concurrent: negative
  offset-cursor guard; cited alias, keyset helpers, WINDOW reads
  unaffected)
- CLEAN GOAL.md 7dfbef5c784519d5f95311aaeb8c6766ee966b02
- CLEAN docs/dry/DRY.md e8151123ff7e129fe9881ec342231e9e1795148e
- CLEAN docs/dry/worker-2.md 4f089ea4a58d73295638e83abf8c612bf31487f8
- CLEAN AGENTS.md e42247fa310bf7a85914d7efa7f177ee5307b860
- Tests read as oracles (not fingerprinted as inputs to a finding):
  tests/optimizer/test_plans.py, tests/optimizer/test_walker.py,
  tests/optimizer/test_join_taxonomy.py, tests/optimizer/test_extension.py,
  tests/optimizer/test_nested_fetch.py, tests/types/test_resolvers.py.

PHASE-1-TRACE-RECORDED docs/dry/dry-file-optimizer__plans.md

## Iterations (Worker 2, phase-2 reconciliation)

Verdict: verified. Phase-1 integrity: the trace above was recorded before
any artifact section was opened (one docs-wide grep row was incidentally
surfaced and excluded from all later searches); all counts, caller censuses,
and owner choices above are independent. Reconciliation below challenges
Worker 1 from that trace; agreements are convergences, not inheritances.

### Enumeration reconciliation (53 = 53)

Both instruments count 53 (32 FunctionDef, 2 ClassDef, 6 Assign, 10
ImportFrom, 1 Import, 2 Expr — cross-checked against my index dump).
Row map (mine → theirs): F-A → F-G(b) + consumers; F-B → F-G(a,c,d,e);
F-C → F-H; F-D → F-I + F-J (split accepted, see below); F-E →
F-K + F-L (split accepted) except deferred_loading_of → reused F-E
(accepted); F-F WINDOW namespace + apply_window_pagination +
_apply_keyset_counted_window + _reverse_order_by → reused F-A / F-B / guard
F-C (accepted); F-G lookup derivation → F-I (+ F-N split-out for
_lookup_path, accepted); window_partition_for_prefetch → F-M (agree).
File-local delta settled: my file-local imports are their
consumers/projections (not rules), and my file-local _MAX_PATH_DEPTH is
their F-H #15 walk-bound row — one rule with its walk, so their
"no file-local rows" holds with every member homed on both sides. Zero
unassigned either way; no consolidation in this file item (agree).

### Family-grouping verdict

Accept all Worker-1 splits: F-D → F-I (queryset-state reconciliation,
owner diff_plan_for_queryset) + F-J (projection traversability, owner
prune_unsupportable_select_related) — distinct contracts, consumers
(extension.py prune-then-diff order), and challenges C7/C8; F-E →
F-K (ladder, cursor-parity) + F-L (entry vocabulary) — distinct
challenges C9/C10; F-N split from lookup derivation — C11 counts 3
while the derivation counts 1. Accept reused-family placements
(F-A/F-B/F-C/F-E-vocabulary) and the F-D/F-F inapplicable discharges.
No merges owed; the 8 plan-index rows stand open with no corrections.

### D1 settled (merged, Worker 2 concurs)

Both filings independently name owner optimizer/plans.py::_lookup_path,
evidence (3 spellings / 2 files: _lookup_path,
_prefetch_lookup_paths inline, walker.py hinted-branch inline), and class:
prose-only (bodies correct — the through-fallback and the skip are real
per-site needs), UNFIXED, coupled to family prefetch-lookup-path-read,
blocks nothing. It does not meet the behavior-defect bar (no observable
divergence; no wire input misbehaves). Worker 0 homes it on the
prefetch-lookup-path-read family card; the prose fix lands with the
family decision.

### Shim-routing verdict

window-partition-resolution routing is correct:
window_partition_for_prefetch (target, zero production callers — my
exact-match census and probe_callers.py converge) plus the parallel
nested_planner.py::_connector_only_field (zero production callers, tests
only) under candidate owner join_taxonomy.py::classify_relation_join,
disposition (delete versus keep-as-boundary-with-pins) decided by the
family item, which must re-verify against the dirty-concurrent
join_taxonomy values. No separate family for the connector shim.

### Rejection map (mine → theirs)

R-1 = R-4 (split_order_ref, agree); R-2 = R-2 (list_field checker,
agree, both-directions independence); R-4/R-5 = in-findings alias
dispositions in F-L/F-K (same-object, concur, no rows needed);
R-6 = F-N seal-state exclusion (agree); R-7 = F-G(c) full-vs-metadata
split (agree); R-8 = the F-I/F-J only-vs-projection placement (agree).
My R-3 (nested_planner _index_leading_terms dash parse on Index.fields
vs the order-entry dash rule) is supplementary to their R-1..R-5:
declaration-vs-request grammar, homed at the nested index-advisory
family, trigger as stated in my trace.

### Proof adequacy and pending execution

Static-reviewed proofs are adequate for this zero-edit file item: every
count is decided by body identity plus def/import/call-site census on a
pinned blob, and no finding claims observable equivalence beyond what
inspection decides. No proof: entries exist (the listed probes are
orientation instruments, not deferred proofs); gate oracles for behavior
are the suite at closeout (uv run pytest) plus the live fakeshop tiers
cited as oracles, with PG/sharded cells unverified per the recorded
gate-cell note (the maintainer's word required). No pytest was authorized or needed
here; no .py path touched (ruff N/A); the artifact carries no markdown
links (zero `](` occurrences — scaffold safe). Item-scoped diff on
production paths is EMPTY.

### Freshness re-hash (HEAD bfaee91d, unchanged since phase 1)

Target plans.py CLEAN cce985319c8833f3660653327d3003f1f03655a5.
Unchanged: walker.py 9b111ed938951a073a9226ccbcfacabc3af981e8 (clean),
extension.py 49667a9370cef73fdf4a170fe9bafa3a1eb19a2a (clean),
lateral_fetch.py db1ea315d774f55e893c108c6e0bc995299a9fa2 (clean),
utils/connections.py f549389ef0ed97bfbe4b158ab21bfc993b71b714 (clean),
keyset.py df4b5e2f105c2b9fa956eac7cea25ba8a0a8de80 (clean),
nested_fetch.py worktree 29ce5201877864b01079c849b92a1e812166affd vs HEAD
4d8d37a7f52cf94d2916f17db3a8a21393e28d57,
nested_planner.py worktree e69dbf5f30aa4623a5aad93edfacdabb391d6601 vs HEAD
0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04,
join_taxonomy.py worktree e1cbb3e327785de3b59ccafef6b463df52e06396 vs HEAD
9b355a5090ce471e373849dd0a61da8f808e78b9,
list_field.py worktree d6af61646784deac2f3053bb4096b8599deae2f5 vs HEAD
ce682d5f79518919ff3676f2fc8bbe2bd33995a4,
connection.py worktree 3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a vs HEAD
93e998f2c7ea1d7f18607a6e37e394466ac75ad4. Cited regions re-confirmed
outside all concurrent hunks. Any fingerprint change reopens.

### Defects

Worker-2 D1 merges into artifact D1 (concur on owner, class, coupling,
unfixed). No additional defects found in phase 2; the audited-and-cleared
list under ## Defects matches my own checks (merge guards, finalize
idempotence, diff copy-semantics, _IndexedList mutator warning,
is_empty/cacheable trigger, plan_optimizations construction clause).

### Exact plan rows for Worker 0

- Tick file item: docs/dry/dry-0_0_15.md plan line 190
  (File optimizer/plans.py) → verified.
- Index corrections: none. Rows 458-465 (8 families) and 619-626
  (family items) stand open as written.
- D1 homing note: home artifact D1 (Worker-1 D1 + Worker-2 concurrence)
  on the prefetch-lookup-path-read family card
  (docs/dry/dry-rule-prefetch-lookup-path-read.md); prose fix coupled to
  the F-N consolidation decision; blocks nothing.
- Scratch paths (Worker 1 probes; Worker 0 removes after verified only,
  by explicit path, never recursively):
  docs/dry/temp-tests/dry-file-optimizer__plans/probe_enumeration.py,
  docs/dry/temp-tests/dry-file-optimizer__plans/probe_singledef.py,
  docs/dry/temp-tests/dry-file-optimizer__plans/probe_lookups.py,
  docs/dry/temp-tests/dry-file-optimizer__plans/probe_callers.py.

PHASE-2-RECONCILED docs/dry/dry-file-optimizer__plans.md

## Run 8 re-trace (Worker-1, scoped re-trace s11)

Prior sections are run-7 evidence only; nothing above is edited.
Every verdict below is decided fresh against HEAD bytes (blob
`fdc4b1b0`, 1541 lines, HEAD `83998e08` confirmed before the
first read and after the last — unmoved throughout). No pytest
ran and no workspace copy was needed: every claim is static (AST
census, `git show HEAD:` reads, `git rev-parse` fingerprints),
so no source-mutating proof exists to route through
`workspace.py`; the one authorized focused `--no-cov` test was
not needed because inspection decides every count below.
Item baseline:
`ITEM_BASELINE=405864034fdf3e1e65e3f4f38a0f57c99a8e92d0`.

### Subject, drift, and dirt attribution

- Target `django_strawberry_framework/optimizer/plans.py`: HEAD
  blob `fdc4b1b0868e1e0ee6d2ec8c5b9a116ae40a5344` (1541
  lines); worktree `3e00515848ee8164a37126e20ee4937aef4c06c8`
  (1542 lines, 3+/2-); pre-merge bytes
  `33140a766cd3fb2484a40fe499d466c8ced8b4a6` at `9aaaad5d`
  (1472 lines; `9aaaad5d` = "dry-0015 pre-ff snapshot", not an
  ancestor of HEAD — read-only evidence, never applied).
- `## Owned changes` names no hunk on this file (verified by
  reading the ledger: the optimizer-area row is the walker D1
  seal-policy on `optimizer/walker.py`; every other row names
  a different path), so all worktree dirt is concurrent,
  attributed by diff content vs `git show HEAD:`: (1)
  `from ..utils import truth`; (2) `resolver_key` renders
  `truth.name(parent_type)` instead of `parent_type.__name__`;
  (3) `ends_in_unique_column` reads `truth.static_attr(model,
  "_meta")` instead of `getattr(model, "_meta", None)` — the
  truthful-reads gate work (`utils/truth.py` is untracked
  concurrent work, `??` in `git status`). The `9aaaad5d`
  bytes carry this same truth adoption atop pre-drift code
  (old `(cursor_field, explicit, model)` ladder signature,
  untyped bodies); worktree dirt = HEAD + the same adoption
  re-applied on new bytes. Nothing traced outside HEAD bytes.
- Drift `0c0537e2..HEAD` on this target is five commits. One
  bears behavior: `10d2b9cd` re-signs
  `django_strawberry_framework/optimizer/plans.py::effective_connection_order`
  to `(cursor_field, query, model)`, reading its model tier
  through the new
  `django_strawberry_framework/utils/querysets.py::applied_order`
  owner (explicit-else-default). Four are typing-only
  (`999a1aab`, `b20277fe`, `849f67bc`, `fef11e64`:
  annotations, casts, `@override`, `TYPE_CHECKING`) and move
  no rule ownership; each commit message states no runtime
  behavior change, and the diffs confirm it for this target.
- Neighbors were read at HEAD bytes only via `git show HEAD:`
  wherever the worktree is dirty (all neighbors below except
  `lateral_fetch.py`, `single_parent_fetch.py`,
  `utils/connections.py`, and `tests/optimizer/test_plans.py`
  carry concurrent dirt); every body cited below gives its
  HEAD line.

### Enumeration (fresh)

Instrument: every name in `ast.Module.body` over the HEAD
bytes (`/tmp/plans-head.py` from `git show HEAD:`, no import
of the target; probe `/tmp/probe_enum_s11.py`, read-only).
Count: HEAD `top_level=59` (`FunctionDef` 32, `ClassDef` 2,
`Assign` 9, `ImportFrom` 12, `Import` 1, `If` 1, `Expr` 2),
`top_async=[]`, `async_tokens=[]`. Delta vs run 7 (53 nodes,
32 functions + 2 classes + 6 assigns + 10 `ImportFrom` + 1
`Import` + 2 `Expr`): +3 `Assign` (`_T`, `_M`, `_O`
TypeVars), +2 `ImportFrom` (`override`, `applied_order`), +1
`If` (`TYPE_CHECKING`) — all typing mechanics, no new rule.
All 34 prior def/class names present with identical
spelling; worktree `top_level=60` (+1 truth `ImportFrom`);
`9aaaad5d` `top_level=54` (prior 53 + truth `ImportFrom`).

41 rule-bearing elements (32 functions + 2 classes + 6 rule
assigns + the module-level inventory gate call; 47 numbered
members counting the 4 + 7 class methods). The 13 imports,
the `TYPE_CHECKING` block, the 3 TypeVars, and the module
docstring are consumers/projections/mechanics, not rules.
Every rule-bearing member lands in exactly one home:

| # | Member | Home |
|---|---|---|
| 1 | `_lookup_path` | F-N `prefetch-lookup-path-read` (definition; D1-coupled) |
| 2 | `_IndexedList` (+ 4 methods) | F-G `optimization-plan-record` (dedupe sub-row) |
| 3 | `_indexed_list` | F-G (string-directive factory) |
| 4 | `_prefetch_indexed_list` | F-G (lookup-keyed factory) |
| 5 | `OptimizationPlan` record | F-G (record sub-row) |
| 6 | `is_empty` | F-G (consumer: `extension.py:1331,1334` HEAD) |
| 7 | `finalize` | F-G (lifecycle sub-row) |
| 8 | `apply` | F-G (consumer: `extension.py:1336` HEAD) |
| 9 | `merge_from` | F-G (consumers: `walker.py:1827`, `nested_planner.py:1461` HEAD) |
| 10 | `merge_metadata_from` | F-G (consumers: `walker.py:1479`, `nested_planner.py:1484` HEAD) |
| 11 | `_assert_under_construction` | F-G (merge guard) |
| 12 | `_assert_merge_field_inventory` + module call `:415` HEAD | F-G (structural gate) |
| 13 | `resolver_key` | F-H `resolver-key-grammar` (consumers: walker, extension, `types/resolvers.py:318,492,745` HEAD) |
| 14 | `runtime_path_from_info` | F-H (consumers: `extension.py:703,737,1622` HEAD, walker, types/resolvers) |
| 15 | `_MAX_PATH_DEPTH` | F-H (walk bound) |
| 16 | `runtime_path_from_path` | F-H (in-file + walker-adjacent use) |
| 17 | `_flatten_select_related` | F-I `consumer-queryset-reconciliation` |
| 18 | `append_unique` | F-G (consumers: walker, nested_planner) |
| 19 | `append_unique_many` | F-G (consumers: walker, nested_planner) |
| 20 | `append_prefetch_unique` | F-G (consumers: `walker.py`, `nested_fetch.py:346` HEAD) |
| 21 | `_consumer_prefetch_lookups` | F-I (lenient live-read owner; sole-readership REVISED — new row below) |
| 22 | `deferred_loading_of` | F-E `nested-recognizer-shared-vocabulary` (consumers `nested_planner.py:742`, `lateral_fetch.py:1220` HEAD) |
| 23 | `_consumer_only_fields` | F-I (used by `diff_plan_for_queryset`) |
| 24 | `prune_unsupportable_select_related` | F-J `select-related-prune-under-projection` (consumer: `extension.py:1323` HEAD) |
| 25 | `_consumer_projection` | F-J |
| 26 | `_select_path_traversable` | F-J (R-3-adjacent, rejected twin) |
| 27 | `_optimizer_can_absorb` | F-I (used by `_diff_prefetch_related`) |
| 28–32 | `WINDOW_*` (5 constants) | F-A `window-range-dual-render` (namespace; F-B + F-E compose by name) |
| 33 | `order_entry_name_and_direction` | F-L `order-entry-vocabulary` (consumers: nested_planner shim + `:279` HEAD, lateral `_order_columns`, connection keyset guard, `ends_in_unique_column`) |
| 34 | `order_entry_has_explicit_nulls` | F-L (consumers: `connection.py:816`, `nested_planner.py:277` HEAD) |
| 35 | `ends_in_unique_column` (`:859` HEAD) | F-K `connection-order-ladder` (consumer: `connection.py:169` alias) |
| 36 | `effective_connection_order` (`:911` HEAD) | F-K (consumers: `connection.py::_finalize_queryset`, `nested_planner.py:1342` HEAD) |
| 37 | `deterministic_order` (`:942` HEAD) | F-K (composed by #36; R-2-adjacent, rejected twin) |
| 38 | `window_partition_for_prefetch` | F-M `window-partition-resolution` (zero production callers — tests only) |
| 39 | `apply_window_pagination` | F-A (ORM renderer; sole production call `nested_fetch.py:331` HEAD) + F-B (seek branches) |
| 40 | `_apply_keyset_counted_window` | F-B (called once; lateral prose cite only) |
| 41 | `_reverse_order_by` | F-A (reverse-branch helper; R-1-adjacent, rejected twin) |
| 42 | `diff_plan_for_queryset` | F-I (consumer: `extension.py:1332` HEAD) |
| 43 | `_diff_select_related` | F-I |
| 44 | `_diff_prefetch_related` | F-I |
| 45 | `lookup_paths` | F-I (consumer: `extension.py:1468` HEAD) |
| 46 | `_lookup_paths_from_parts` | F-I (used by `finalize` + `lookup_paths`) |
| 47 | `_prefetch_lookup_paths` | F-I (contains the second `prefetch_to` read at HEAD `:1532` — F-N-noted) |

No file-local rows: every member has a consumer, a twin
candidate, or a family home (a row naming a second site is a
family or a rejection, never file-local). No consolidation
in this file item.

### Matrix (fresh, on the current target)

1. Cross-flavor policy mirroring: no flavor twin. The target
   is optimizer-internal; strategy selection stays owned by
   `nested_fetch.py`. Package-wide `def`-census over HEAD
   worktree bytes (`/tmp/probe_singledef_s11.py`, 18
   target names): 17 single-site; the one pair is
   `append_unique` = module function (`:516`) +
   `_IndexedList.append_unique` method (`:118`) — one
   discipline in method/function form, not a second
   definition. No second window renderer, order ladder, plan
   record, or resolver-key grammar. `list_field.py` shares
   only the token "deterministic" (R-2): zero references to
   `plans.deterministic_order` / `effective_connection_order`
   / `ends_in_unique_column` at HEAD, and it now reads its
   model tier through `default_order` (narrowing noted at
   R-2, verdict stands).
2. Sync/async twins: none owed. HEAD AST probe asserts zero
   `AsyncFunctionDef`; text probe finds no `async def` /
   `await` / `sync_to_async` in-file. Execution is sync-only
   by construction (QuerySet chains); async callers reach it
   through `one-sync-boundary`. Inapplicable with reason.
3. Derived rather than repeated knowledge: every derivation
   composes its owner by name — the Django-compiled order
   via `utils/querysets.py::applied_order` (NEW owner,
   `10d2b9cd`; `effective_connection_order:939` HEAD is its
   composer, never a re-derivation); range/marker/probe via
   `window_range_plan` (ORM `Q` rendering only);
   `build_keyset_seek_plan` (seek structure); join facts via
   `classify_relation_join`; the `deferred_loading` unpack
   via the single `deferred_loading_of` (sole
   `"deferred_loading"` getattr site package-wide at HEAD).
   Two exceptions: the triple `prefetch_to` read (F-N / D1,
   persists) and the NEW second `_prefetch_related_lookups`
   read (walker strict forward; new row + D2 below).
4. Inverse / round-trip pairs: (a) `window_range_plan`
   decisions rendered as ORM `Q` here vs raw SQL in
   `lateral_fetch.py::build_lateral_sql`, verified by
   `window_predicate_signature` + recognizers; (b)
   `KeysetSeekPlan` rendered as `Q` (`keyset_seek_q`), SQL
   (`keyset_seek_sql`), and filtered running count
   (`_apply_keyset_counted_window`); (c) GraphQL `path`
   linked list walked once by `runtime_path_from_path` into
   resolver keys; (d) merge field inventory ↔
   `_assert_merge_field_inventory` module-level gate (HEAD
   `:415`). Window (plain / reverse / marker / probe),
   seek (count-free + counted), and nested (`Prefetch`
   via `nested_fetch.py:331` HEAD) shapes all compose the
   same owners.
5. Contracts restated in another medium: every rule below
   lists its oracles (`tests/optimizer/test_plans.py`, CLEAN
   `df714065`, incl. the re-signed 6-test
   `TestEffectiveConnectionOrder` plus intact
   `TestDeterministicOrderHoistParity`; live ReadingList
   tests in `test_library_shapes_api.py`) and projections
   (docstrings + `connection.py` step-5 + nested_planner (d)
   comment — both predate the `applied_order` naming but
   describe the by-name composition correctly). Test/doc
   sites listed, never counted.
6. Enforcement by omission: every `FetchMode` has a
   rendering or a named loud refusal (COUNTED / count-free
   seek / PROBED sentinel / NONE; `reverse` + `keyset_seek`
   raises `OptimizerError`); unwindowable kinds raise in
   the partition shim; diff/prune consumer-wins arms
   enumerated; the walker seal policy lives in `walker.py`
   (zero `seal` hits in this file at HEAD); the reverse-map
   naming atom lives in `mutations/inputs.py` (zero
   `python_attr` hits at HEAD). No omission gap on this
   file's surface.

### Findings CONFIRM/REVISE (per prior finding, fresh evidence)

- F-A `window-range-dual-render`: CONFIRM. Sole ORM
  renderer, sole production call
  `nested_fetch.py:331` HEAD; decisions still
  `window_range_plan`; lateral still the second renderer
  with the counted-keyset refusal
  (`lateral_fetch.py` "Counted keyset seek" guard, HEAD-clean
  file). C1 (2 bodies, 1 owner) and C2 (1) hold.
- F-B `keyset-seek-dual-dialect`: CONFIRM. One plan owner
  (`build_keyset_seek_plan`), three render bodies
  (`keyset_seek_q`, `keyset_seek_sql`,
  `lateral_fetch.py::_keyset_seek_quals_match:807` HEAD);
  count-free filter branch + counted helper (called once)
  intact. C3 (1 owner) holds.
- F-C `window-fetch-mode-guard`: REVISE (owner spelling;
  substance CONFIRMED). The check owner is
  `utils/connections.py::assert_window_fetch_mode` — the
  function plans calls (HEAD `:1135`) and whose docstring
  names it "the single owner of the boundary check every
  window entry point shares";
  `assert_window_fetch_mode_for` is the raw-arguments
  adapter delegating to it. Both existed and plans called
  the same one at the prior stamp, so this is a record
  correction, not drift. C4 (count 1) holds.
- F-E `nested-recognizer-shared-vocabulary`: CONFIRM.
  `deferred_loading_of` still the sole
  `"deferred_loading"` getattr site (HEAD census: exactly
  one, `plans.py:591` HEAD, the helper body);
  consumers `lateral_fetch.py:1220` and
  `nested_planner.py:742` HEAD compose by name; `WINDOW_*`
  namespace consumers unchanged (connection, lateral,
  single_parent). C2 (1) holds.
- F-D / F-F inapplicable: CONFIRM. Zero `def` hits for
  the skeleton or the strategy seam in this file; both
  still owned by `nested_fetch.py`.
- F-G `optimization-plan-record`: CONFIRM. Record fields,
  inventory ClassVars, dedupe discipline, full-vs-metadata
  merge split, lifecycle, and the import-time gate (HEAD
  `:415`) intact; consumers at HEAD bytes (walker
  constructs `:193`/`:1224`, merges `:1479`/`:1827`;
  nested_planner constructs `:1130`/`:1290`/`:1459`,
  merges `:1461`/`:1484`; extension `:1331`/`:1334`/`:1336`).
  Drift is annotations/casts/`@override` only. C5 (1) holds.
- F-H `resolver-key-grammar`: CONFIRM. Grammar, `info`
  unwrap, linked-list walk, `_MAX_PATH_DEPTH` ceiling
  intact; consumers at HEAD bytes (types/resolvers
  `:318`/`:492`/`:745`, extension `:703`/`:737`/`:1622`,
  walker). The worktree `truth.name` swap is concurrent
  dirt on an untracked module, traced nowhere. C6 (1) holds.
- F-I `consumer-queryset-reconciliation`: CONFIRM with a
  REVISED member record. The reconciliation rule (select
  diff, prefetch absorb-or-drop, only-wins, lookup
  flatten; consumer `extension.py:1332,1468` HEAD) is
  unchanged — C7 (1) holds. But member #21
  `_consumer_prefetch_lookups` is no longer the sole live
  `_prefetch_related_lookups` reader: HEAD-committed
  `walker.py::_hint_prefetch_over_pk_set:1432` (landed via
  `5c5e32c5`, after the prior stamp) forwards
  `inner._prefetch_related_lookups` directly when
  rebuilding a QuerySet around a rewritten query. Strict
  forward of a guaranteed-present tuple vs lenient
  getattr-read are different contracts sharing one
  Django-private attribute (rename-count 2) — nominated
  as a new family row below (mirror of F-N), with the
  unify-vs-record decision owed to the family item.
- F-J `select-related-prune-under-projection`: CONFIRM.
  Rule, consumer (`extension.py:1323` HEAD), and oracles
  intact; drift typing-only. C8 (1) holds.
- F-K `connection-order-ladder`: REVISE (re-signed owner;
  re-derived under Scope confirmation). Precedence intact;
  both consumers compose the re-signed function by name;
  the family gains a composed sub-owner in
  `utils/querysets.py`. C9 (1) holds for the tiebreak tier.
- F-L `order-entry-vocabulary`: CONFIRM. Parser +
  explicit-NULLS predicate unchanged (modulo annotations);
  consumers at HEAD bytes (nested_planner shim `:191`
  still a thin delegate under its historical name, advisory
  `:277`/`:279`, lateral `:1187`, connection `:816`/`:818`,
  `ends_in_unique_column` HEAD `:881`); walker aliases persist (`:107`/
  `:111` HEAD, same objects). C10 (1) holds.
- F-M `window-partition-resolution`: CONFIRM. The shim
  still has ZERO production callers (HEAD census:
  `test_plans.py` + `test_walker.py` pins plus prose
  mentions in `join_taxonomy.py`, `exceptions.py:410`
  HEAD, and its own error strings); production flows
  through `request.join.partition_expr`; the classifier
  still owns values (`WINDOWABLE_RELATION_KINDS:85`,
  `classify_relation_join:318` HEAD). The principle-11
  keep-or-delete question stays open for the family item.
  C12 (1) holds.
- F-N `prefetch-lookup-path-read`: CONFIRM. Three
  spellings persist at HEAD bytes (strict
  `plans.py:82`, lenient-skip `plans.py:1532`,
  hinted through-fallback `walker.py:1343` HEAD);
  sealed-dict exclusion re-verified
  (`utils/querysets.py:2349` HEAD reads serialized
  seal-state keys, different population). C11 (3
  spellings, 2 files) holds; D1 stays coupled.
- R-1 (reversal rendering): CONFIRM. `_reverse_order_by`
  still flips direction AND NULLS and raises loud
  `OptimizerError`; lateral `order_sql` still a
  direction-only flip over pre-downgraded concrete
  columns (`_order_columns` still refuses non-`str` /
  traversal / `?` at HEAD). Trigger stands (lateral
  accepts expression/explicit-NULLS orders).
- R-2 (offset-guard eligibility): CONFIRM with a narrowed
  trigger. The checker-vs-constructor split is intact
  (zero plans-order references in `list_field.py` at
  HEAD; C9/C14 still count 1 each, both directions).
  New since the stamp: `list_field.py::_selected_ordering`
  reads its model tier through the shared
  `default_order` (`:1163` HEAD), so the model-tier READ
  is now one rule while the checker-vs-constructor
  verdicts stay two. Standing trigger partially fired on
  the read half only; the split verdict holds.
- R-3 (path walkers): CONFIRM. `_select_path_traversable`
  (bool, prune) vs `classify_path` (hop records, raises
  `PathResolutionError` — 7 raise sites `:366`–`:415`
  HEAD) unchanged in contract. Trigger stands.
- R-4 (order-string twins): CONFIRM at HEAD bytes.
  `keyset.py::split_order_ref` still loud
  (`ConfigurationError`, no traversal, rejects `"--x"`)
  vs the total `None`-returning string branch here;
  the twin declaration persists in its docstring. The
  worktree `truth.is_instance`/`truth.render` spellings
  are concurrent dirt (HEAD uses `isinstance`/`!r`).
  Trigger stands.
- R-5 (parent-link columns): CONFIRM. `partition_expr`
  (PARTITION BY, loud) vs `parent_join_column` (`.only()`
  projection, `None`-lenient) still distinct facts from
  one classifier (`_parent_join_column:205`,
  `classify_relation_join:318` HEAD; both M2M directions
  still diverge). Trigger stands.
- W2 R-1/R-2/R-4/R-5/R-6/R-7/R-8: CONFIRM via R-4, R-2,
  the F-L/F-K alias dispositions, the F-N seal-state
  exclusion, the F-G(c) full-vs-metadata split, and the
  F-I/F-J only-vs-projection placement respectively.
  W2 R-3 (index-declaration dash parse): CONFIRM —
  `nested_planner.py::_index_leading_terms:298` HEAD
  still parses `Index.fields` declarations, a different
  grammar from the order-entry request vocabulary.
  W2 attention item (a) (zero-caller shims): CONFIRM —
  still exactly one in-target (`window_partition_for_prefetch`)
  plus the neighbor twin (`_connector_only_field`,
  tests-only). W2 attention item (b): REVISED —
  `deferred_loading_of` ("THE single reader") still TRUE;
  `_consumer_prefetch_lookups` ("Centralizes") now has
  the walker strict-forward second spelling (new row +
  D2); `_lookup_path` ("one fix") still FALSE per D1.
  W2 attention item (c): CONFIRM + extend — the
  `prefetch_to` triple persists; the
  `_prefetch_related_lookups` pair is new.

### Scope confirmation: `connection-order-ladder`

The plan rows this family (owner
`optimizer/plans.py::effective_connection_order` +
`ends_in_unique_column` + `deterministic_order`; consumers
`connection.py`, nested_planner; files plus
`utils/querysets.py`) as undispatched, with s11 owed the
scope confirmation against the `10d2b9cd` re-signed owner.
Re-derived ladder at HEAD bytes:

1. Keyset tier — `effective_connection_order:911` HEAD:
   `if cursor_field is not None and not query.order_by:
   return tuple(cursor_field)`.
2. Explicit-else-default tier — now owned by
   `utils/querysets.py::applied_order`
   (`tuple(query.order_by) or default_order(query, model)`)
   over `default_order` (`()` unless
   `query.default_ordering`, else
   `tuple(model._meta.ordering or ())`).
3. Totalization tier — `deterministic_order:942` HEAD
   appends `model._meta.pk.attname` unless
   `ends_in_unique_column:859` HEAD certifies a unique
   terminal.

Is the owner still the ladder's single home? As the
PRECEDENCE COMPOSER, yes: `effective_connection_order` is
still the only site answering "which ORDER BY does a
connection paginate under", and both tiers it does not own
it composes by name (`applied_order`, `deterministic_order`
→ `ends_in_unique_column`). As the owner of every tier, no:
tier 2 moved to `utils/querysets.py`, which now also serves
`connection.py`'s `applied` comparison and
`list_field.py::_selected_ordering`'s model tier directly.
Do the consumers compose it by name? Yes —
`nested_planner.py:1342` HEAD calls it with
`(cursor_field, child_queryset.query, related_model)` and
`connection.py::_finalize_queryset` (HEAD, guard-wrapped)
calls it with `(cursor_field, qs.query, target_model)`,
comparing against imported `applied_order`. Zero inline
rebuilds remain: HEAD census finds no `_meta.ordering`
read in either consumer file. (The worktree
`connection.py` tail drops the HEAD guard wrappers —
concurrent dirt on that file's guard posture, outside this
item; the ladder composition is identical in both states.)

Membership verdict: ENDORSE the row's owner and files with
one owner-cell adjustment for Worker-0 (no new row, no
split — the s10 "no row split" note anticipated exactly
this): owner should read
`optimizer/plans.py::effective_connection_order` (+
`ends_in_unique_column`, `deterministic_order`) composing
`utils/querysets.py::applied_order`/`default_order` for the
explicit-else-default tier. Files already list all four
modules; no files change.

### Challenges (fresh, definition counts)

All `static-reviewed` against the pinned HEAD blob; body
identity + `def`-census + import census decide each count.
C1–C8, C10, C12–C17 stand as recorded (C1 2 bodies/1
owner; C3 1 owner over 3 bodies; every other count 1;
C4's owner spelling corrected to `assert_window_fetch_mode`
with no count change). Re-derived and new:

- C9' (F-K tiebreak tier: pk attname → qualified ref).
  Moves: `deterministic_order` (1); connection +
  nested_planner follow; `list_field.py` untouched (R-2).
  Count: 1. Oracles: `TestDeterministicOrderHoistParity` +
  `TestEffectiveConnectionOrder` + live ReadingList tests.
- C9'a (F-K keyset tier: cursor_field precedence rule).
  Moves: `effective_connection_order` branch (1).
  Count: 1.
- C9'b (F-K middle tier: explicit-else-default rule, e.g.
  honoring `extra(order_by=...)`). Moves: `applied_order`
  (1); `effective_connection_order`, the connection tail,
  and `list_field.py::_selected_ordering` follow — except
  the list field deliberately classifies `extra` itself
  (stated in the `applied_order` docstring), so a change
  there is 1 definition + 1 deliberate non-consumer.
  Count: 1.
- C9'c (model-tier read: `ordering = None` / cleared
  `default_ordering` handling). Moves: `default_order`
  (1). Count: 1.
- C11 (F-N/D1, re-run): Django renames
  `Prefetch.prefetch_to`. Moves: `plans.py:82` +
  `plans.py:1532` + `walker.py:1343` HEAD = 3 spellings,
  2 files. Count: 3 (D1 evidence, unchanged).
- C18 (NEW ROW, mirror of C11): Django renames
  `QuerySet._prefetch_related_lookups`. Moves:
  `_consumer_prefetch_lookups` (lenient getattr) +
  `walker.py::_hint_prefetch_over_pk_set:1432` HEAD
  (strict forward) = 2 spellings, 2 files. The sealed
  `entry_state.get("prefetch_to")` key and
  `_sealed_prefetch_related_lookups` are a different
  population (serialized seal state, R-6) and do not
  move. Count: 2 (D2 evidence).

### New rows for Worker-0 (plan edits owed, none made here)

- Family `attached-prefetch-lookups-read` (new row):
  owner candidate
  `optimizer/plans.py::_consumer_prefetch_lookups`
  (lenient live-read) with second spelling
  `optimizer/walker.py::_hint_prefetch_over_pk_set`
  (strict forward of a guaranteed-present tuple);
  rename-count 2 (C18); family item decides unify
  (route the forward through the helper, changing its
  missing-attribute failure mode) vs record the two
  contracts. Files: `optimizer/plans.py`,
  `optimizer/walker.py`. D2 couples here.
- `connection-order-ladder` owner-cell adjustment (not a
  new row): append "composing
  `utils/querysets.py::applied_order`/`default_order` for
  the explicit-else-default tier" to the owner (basis:
  Scope confirmation above).

### Defects

- D1 (prose-only; UNFIXED; CONFIRMED persisting): the
  `_lookup_path` "one fix" promise is still false at HEAD
  (`:77` docstring; 3 spellings per C11). Owner, class,
  and F-N coupling unchanged. Blocks nothing.
- D2 (prose-only; UNFIXED; NEW): `_consumer_prefetch_lookups`
  "Centralizes the brittle Django-private contract for
  `QuerySet._prefetch_related_lookups`" (HEAD `:560`)
  overclaims the same way D1 does since `5c5e32c5`: a
  Django rename now needs 2 fixes (C18), and the next
  author honoring "Centralizes" fixes one. The bodies
  behave correctly (the strict forward is the honest
  spelling for a guaranteed-present tuple); this is a
  false single-home statement, not a behavior bug. Owner:
  `optimizer/plans.py::_consumer_prefetch_lookups`.
  Coupling: the new `attached-prefetch-lookups-read`
  family row carries the unify-vs-record question; the
  prose fix lands with whichever the family item decides.
  Blocks nothing.

No other defect bar met. Audited and cleared (re-checked
at HEAD): merge/finalize guards match the cache invariant;
`finalize()` idempotence matches the tuple-rebuild body;
`diff_plan_for_queryset` copy-semantics match the early
return + `replace()` tails; `_IndexedList` mutator warning
matches the three maintained entry points; the
`is_empty`/`cacheable` trigger clause persists; the
"Constructed by `plan_optimizations`" clause resolves
(`walker.py`, HEAD).

### Pending execution

None. Zero-edit file item; every proof above is
`static-reviewed`. Read-only probes (AST/text only, target
never imported, no Django settings touched; `/tmp`-only,
cited by content):

- `/tmp/probe_enum_s11.py` → HEAD `top_level=59`,
  worktree `60`, `9aaaad5d` `54`; `top_async=[]`,
  `async_tokens=[]` on all three.
- `/tmp/probe_singledef_s11.py` → 17/18 single-site (the
  pair is `append_unique` method + function, one
  discipline).

PG-tier and sharded cells stay `unverified` (need the maintainer's
separate word); inapplicable-by-construction is not
claimed (window SQL reaches dialect decisions).

### Freshness fingerprints

HEAD `83998e08d48c911199527ed0411ab8041805c8b5`.
Target `django_strawberry_framework/optimizer/plans.py`:
HEAD `fdc4b1b0868e1e0ee6d2ec8c5b9a116ae40a5344`
(1541 lines) vs worktree
`3e00515848ee8164a37126e20ee4937aef4c06c8` (1542
lines; exactly the 3-line truth re-adoption) vs `9aaaad5d`
`33140a766cd3fb2484a40fe499d466c8ced8b4a6` (1472
lines; truth-adopted, pre-typing, pre-resign). Item-scoped
diff vs `ITEM_BASELINE` on production paths: EMPTY (no
`.py` edits; this artifact is the only touched file).
Neighbors (worktree read; HEAD alongside where dirty;
cited regions verified HEAD-identical): `optimizer/
walker.py` worktree `9130aceb` vs HEAD `bdd9c2f1`
(cited `:107`/`:111`/`:193`/`:1224`/`:1343`/`:1432`/
`:1479`/`:1827` HEAD); `optimizer/extension.py` worktree
`dd9ad009` vs HEAD `6a6465f2` (cited `:703`/`:737`/
`:1323`/`:1331`/`:1332`/`:1334`/`:1336`/`:1468`/`:1622`
HEAD); `optimizer/nested_fetch.py` worktree `b74539d1`
vs HEAD `304e2f3e` (cited `:82`/`:331`/`:346` HEAD);
`optimizer/nested_planner.py` worktree `e5daffc5` vs HEAD
`3637dc3a` (cited `:163`/`:182`/`:191`/`:277`/`:279`/
`:298`/`:742`/`:1130`/`:1290`/`:1342`/`:1459`/`:1461`/
`:1484` HEAD); `optimizer/join_taxonomy.py` worktree
`fa4974c3` vs HEAD `6274d9a0` (cited `:85`/`:205`/`:318`
HEAD); `optimizer/lateral_fetch.py` clean `583f6d7b`
both; `optimizer/single_parent_fetch.py` clean `3a4bb89b`
both; `optimizer/selections.py` worktree `3237edec` vs
HEAD `4127d08a` (uncited); `keyset.py` worktree `49f0dfbe`
vs HEAD `8da76569` (split/triple bodies HEAD-verified);
`utils/connections.py` clean `735aa454` both;
`utils/querysets.py` worktree `cfc773ba` vs HEAD
`392e50d0` (`default_order`/`applied_order` bodies +
`:2349`/`:2443` HEAD-verified); `utils/relations.py`
worktree `6b80acac` vs HEAD `72e7ff08` (cited `:344`/
`:366`–`:415` HEAD); `connection.py` worktree `64b85d0e`
vs HEAD `3d6dd424` (cited `:93`–`:96`/`:127`/`:169`/
`:816`/`:818`/tail HEAD; worktree tail drops the HEAD
guard wrappers — concurrent, out of scope);
`list_field.py` worktree `1dcb0c43` vs HEAD `77ddb86c`
(cited `:101`/`:892`/`:1142`/`:1163`/`:1169` HEAD);
`types/resolvers.py` worktree `7a953c53` vs HEAD
`574e9768` (cited `:318`/`:492`/`:745` HEAD);
`exceptions.py` worktree `34e2e6be` vs HEAD `f27e1f91`
(cited `:410` HEAD); `tests/optimizer/test_plans.py`
clean `df714065` both. Pre-merge `9aaaad5d` neighbor
blobs: walker `d5759ef8`, connection `1fca6266`,
querysets `8fc556d5`, nested_planner `d32d1b7b`. Any
fingerprint change reopens the finding.

### Judgment

File item re-traced with zero edits: 41 rule-bearing
elements (47 numbered members) re-homed (F-A/F-B/F-C/F-E
reused + F-D/F-F inapplicable CONFIRMED save the F-C
owner-spelling correction; F-G/F-H/F-I/F-J/F-L/F-M/F-N
CONFIRMED with the F-I sole-readership REVISE; F-K
REVISED to the re-signed composer + composed querysets
sub-owner; 5 rejections + W2 R-3 CONFIRMED with R-2's
trigger narrowed; no file-local rows), matrix discharged
on all six axes against current HEAD bytes, challenges
re-counted (C9 split into four tier counts, C18 new at
count 2), scope of `connection-order-ladder` CONFIRMED
with one owner-cell adjustment (no split), one new family
row + one new prose defect (D2, UNFIXED, coupled) filed.
The file composes its owners by name throughout,
including the new `applied_order` owner; the two
multi-spelling reads it touches (F-N, new row) are filed
for their family items with coupling defects.

## Run-8 verification (Worker 2)

Run: 0.0.15 2026-09-30-8. The run-8 author section above was
read whole, then every decisive claim below was re-derived from
`git show` + AST + grep at HEAD bytes under my own invocation,
with my own counts, before judging each CONFIRM/REVISE. My
probes `/tmp/w2_enum.py`, `/tmp/w2_singledef.py`,
`/tmp/w2_top.py` (all read-only, target never imported) plus
end-to-end body reads carry the verdicts; one first-pass scare
(the `seek_q` hunk) was resolved byte-level to a cast-wrapped
identical call. Zero production edits; this section + the
`Status:` line are the only tracked changes.

### Expectation-first trace

- HEAD `83998e08` unmoved throughout; target HEAD blob
  `fdc4b1b0` (1541 lines), worktree `3e005158` (1542 lines,
  3+/2- in exactly 3 hunks). Pre-merge `9aaaad5d` read-only
  via `git show`, never applied. Item-scoped diff vs
  `ITEM_BASELINE=40586403…` on the target: 0 bytes (verified).
- `ast.Module.body` over HEAD bytes: 59 nodes = 2 `Expr` + 12
  `ImportFrom` + 1 `Import` + 1 `If` + 9 `Assign` + 32
  `FunctionDef` + 2 `ClassDef`; zero `AsyncFunctionDef`, zero
  async tokens. Delta vs run-7 53: +3 `Assign` (`_T`, `_M`,
  `_O`) +2 `ImportFrom` (`override`, `applied_order`) +1 `If`
  (`TYPE_CHECKING`) — all typing mechanics, no new rule. All
  34 run-7 def/class names present verbatim; methods 4+7. 41
  rule-bearing elements (32+2+6+gate), 47 numbered members.
  Worktree `top_level=60` (+1 truth import), pre-merge 54 (+1
  truth import) — both counts reproduced by my instrument.
- `0c0537e2..HEAD` touches this target in exactly 5 commits: 1
  behavior-bearing (`10d2b9cd`: the re-sign
  `explicit: tuple` → `query: Query`, the model tier through
  `applied_order`, docstring rewritten; read in full) + 4
  typing-only (`999a1aab`: annotations, casts, TC block, one
  consistent local rename; `b20277fe`: signatures, TypeVars,
  casts; `849f67bc`: `@override` ×2 + import; `fef11e64`:
  one cast netted out, one local annotation, comments). The
  post-resign diff was verified line by line (10 lines, all
  typing). No rule moves except the recorded re-sign.
- `## Owned changes` names no hunk on this file (grep over
  the ledger block: zero hits), so all 3 worktree hunks are
  concurrent-external, attributed by content vs
  `git show HEAD:`: the truth import, `resolver_key` via
  `truth.name`, `ends_in_unique_column` via
  `truth.static_attr` — the truthful-reads gate work on the
  untracked `utils/truth.py`. Nothing traced outside HEAD
  bytes.

### Per-row judgments (my counts)

- Enumeration: CONFIRM — my instrument reproduces 59 nodes
  with the identical kind breakdown; every #1–47 home
  re-checked against the member's contract; no file-local
  rows holds (each member has a consumer, twin candidate,
  or family home).
- Matrix 1: CONFIRM — my 34-name cross-file census finds
  zero second-file definitions; the `append_unique`
  method+function pair is one discipline (the module
  function delegates to the method for indexed lists);
  exact-zero `deterministic_order` / `effective_connection_order`
  / `ends_in_unique_column` symbol references in
  `list_field.py` at HEAD (only the local
  `_is_deterministic_order_*` family).
- Matrix 2: CONFIRM — sync-only by construction (counts
  above); inapplicable with reason.
- Matrix 3: CONFIRM — the composer call
  `deterministic_order(applied_order(query, model), model)`
  verified at HEAD `:939`; sole `"deferred_loading"`
  getattr site verified (exactly one, `:591`); the two
  exceptions are the F-N triple and the new pair, both
  re-derived below.
- Matrix 4: CONFIRM — gate module call at `:415`, sole
  production caller `nested_fetch.py:331`, zero-caller shim
  census, and the lateral second renderer (file clean both
  blobs, guard prose at `:1045`) all verified.
- Matrix 5: CONFIRM — `TestEffectiveConnectionOrder` counts
  6 tests including the two new-shape oracles
  (`ordering_none`, cleared-`default_ordering`); test file
  clean `df714065` both blobs.
- Matrix 6: CONFIRM — zero `seal` / zero `python_attr` hits
  in the target at HEAD (both censuses return 0).
- F-A: CONFIRM (C1 2 bodies/1 owner, C2 1 — recounted).
- F-B: CONFIRM (3 render bodies incl.
  `_keyset_seek_quals_match:807`, 1 owner — recounted).
- F-C: CONFIRM the REVISE — plans calls
  `assert_window_fetch_mode` at `:1135`; that function's
  docstring states it is "the single owner of the boundary
  check"; `_for` delegates to it (body read). C4 count 1.
- F-E: CONFIRM — sole read `:591`, both consumers compose
  by name (`lateral_fetch.py:1220`,
  `nested_planner.py:742`). C2 count 1.
- F-D / F-F: CONFIRM inapplicable (no skeleton/strategy
  definition among the target's 34 names).
- F-G: CONFIRM — every cited consumer line verified at HEAD
  bytes (walker constructs `:193`/`:1224`, merges
  `:1479`/`:1827`; nested_planner `:1130`/`:1290`/`:1459`,
  merges `:1461`/`:1484`; extension `:1331`/`:1334`/`:1336`;
  gate `:415`). C5 count 1.
- F-H: CONFIRM — grammar bodies intact; consumers verified
  (types/resolvers `:318`/`:492`/`:745`, extension
  `:703`/`:737`/`:1622`). C6 count 1.
- F-I: CONFIRM with the sole-readership REVISE — the
  reconciliation rule is unchanged (C7 count 1); member
  #21's second spelling verified (see focus 2).
- F-J: CONFIRM — consumer `:1323` verified; C8 count 1.
- F-K: CONFIRM the REVISE — see focus 1. C9 split into
  four tier counts, each 1 (C9'b's deliberate
  non-consumer verified in the `applied_order` docstring's
  `extra(order_by=...)` clause).
- F-L: CONFIRM — parser + predicate unchanged; consumers
  verified (shim delegate call `:191`, advisory `:277`/
  `:279`, lateral `:1187`, connection `:816`/`:818`,
  `ends_in_unique_column`; walker aliases `:107`/`:111`
  same-object). C10 count 1.
- F-M: CONFIRM — zero production callers (my census: prose
  + own error strings + test pins only); classifier owns
  values. C12 count 1.
- F-N: CONFIRM — 3 spellings at HEAD (`:82`, `:1532`,
  `walker.py:1343` with the `prefetch_through` fallback);
  sealed-dict exclusion re-verified
  (`entry_state.get("prefetch_to")` at `:2349`, snapshot
  keys, different population). C11 count 3, 2 files.
- R-1: CONFIRM — `_reverse_order_by` flips direction AND
  NULLS and raises `OptimizerError`; lateral `_order_columns`
  downgrades non-`str` / traversal / `?` (body read at
  HEAD). Trigger stands.
- R-2: CONFIRM with the narrowed trigger — split intact
  (exact-zero refs both directions, C9/C14 each 1); the
  model-tier read through `default_order` at
  `list_field.py:1163` verified, so the standing trigger
  fired on the read half only.
- R-3: CONFIRM — 7 `raise PathResolutionError` sites in
  `:366`–`:415` counted. Trigger stands.
- R-4: CONFIRM — loud `ConfigurationError`, no traversal,
  twin declared in the docstring (`keyset.py:188`–`:191`);
  HEAD uses `isinstance`/`!r` (worktree `truth.*` is
  concurrent dirt on another file). Trigger stands.
- R-5: CONFIRM — `_parent_join_column:205` vs
  `classify_relation_join:318`, both M2M directions still
  diverge per the descriptor contract. Trigger stands.
- Run-7 W2 R-1/R-2/R-4/R-5/R-6/R-7/R-8: CONFIRM via the
  rows above. W2 R-3: CONFIRM
  (`_index_leading_terms:298` parses `Index.fields`
  declarations). Attention (a): CONFIRM (still exactly
  one in-target zero-caller shim plus the neighbor twin).
  Attention (b): CONFIRM the REVISED split —
  `deferred_loading_of` TRUE (sole read), `_lookup_path`
  FALSE (D1 persists), `_consumer_prefetch_lookups` now 2
  (D2). Attention (c): CONFIRM + extend (triple persists,
  pair is new).

### Adversarial focus

1. F-K scope: the re-signed owner (body read at `:911`;
   lines `:859`/`:911`/`:942` all land as cited) still
   single-homes the precedence — it is the only site
   answering which ORDER BY a connection paginates under,
   composing both tiers it does not own by name. Both
   consumers compose it by name with the cited shapes
   (`nested_planner.py:1342` with
   `(cursor_field, child_queryset.query, related_model)`;
   `connection.py::_finalize_queryset:1745` with
   `(cursor_field, qs.query, target_model)`, guard-wrapped,
   comparing against imported `applied_order` at `:1730`).
   Zero `_meta.ordering` reads in either consumer file
   (both greps empty). No-split holds: the ladder is one
   precedence rule with a composed sub-owner, and a split
   would strand the cursor-parity invariant across two
   rows. The owner-cell adjustment text is accurate and the
   index row already lists all four files, so no files
   change.
2. New family row: both spellings read at HEAD — lenient
   `getattr(..., ()) or ()` at `:572` vs strict
   `inner._prefetch_related_lookups` forward at
   `walker.py:1432` (def at `:1398`, introduced by
   `5c5e32c5`, after the run-7 stamp). My full census finds
   exactly 2 live attribute reads package-wide; the sealer
   takes `lookups` as a parameter and contains no spelling,
   its caller reads `state.get(...)` from the `__dict__`
   snapshot at `:3733`, and `:3806` writes the attribute
   under the seal's clone-reproduction contract. Count-2
   for the read rule CONFIRMED. The unify-vs-record
   framing is sound: unifying routes a strict forward
   (loud `AttributeError` on a missing attribute) through
   a lenient helper (silent `[]`), and for a
   guaranteed-present tuple the strict spelling is the
   honest fail-loud choice — a genuine keeping-separate
   reason, so the decision is correctly left open, not
   pre-decided. Owner candidacy (lenient live-read) and
   the two-file scope are correct. One record catch: the
   C18 exclusion sentence mis-cites (see C1); the count
   and nomination stand.
3. D2: the "Centralizes" overclaim verified at `:560`; a
   rename needs 2 fixes (C18 recounted); bodies correct
   for their contracts, so prose-only, UNFIXED. Coupling
   endorsed: this item makes no production edits, the fix
   text depends on the family decision (unify restores the
   claim, record rewrites it), and the D1/F-N precedent is
   identical.
4. D1 persistence: all 3 spellings verified at HEAD bytes
   plus the `:77` "one fix" promise; sealed exclusion at
   `:2349` re-verified. Persists UNFIXED, coupling
   unchanged.

### Record correction (no resubmission)

- C1 (C18 exclusion sentence): as written it excludes "the
  sealed `entry_state.get("prefetch_to")` key and
  `_sealed_prefetch_related_lookups`" as "a different
  population … and do not move". Three faults: (a) the
  `prefetch_to` key is the wrong key for this rename — the
  seal's touchpoint that matters is
  `state.get("_prefetch_related_lookups")` at
  `utils/querysets.py:3733`; (b) `_sealed_prefetch_related_lookups`
  takes `lookups` as a parameter and contains no attribute
  spelling, so excluding it is vacuous; (c) "do not move"
  overclaims — under a genuine Django rename both `:3733`
  (snapshot key read) and the unmentioned `:3806`
  clone-write would move, but under their own seal
  contracts (snapshot discipline, clone reproduction),
  not this family's read rule — which is why the count-2
  stands per the run-7 R-6 separation precedent. Corrected
  exclusion: live reads = 2 (`plans.py:572`,
  `walker.py:1432`); seal snapshot-key read (`:3733`) and
  clone-write (`:3806`) move under seal contracts. No
  verdict, count, owner, or file-list moves.

### Proposal judgments

- New family row `attached-prefetch-lookups-read`:
  ENDORSED — owner candidate, second spelling, rename
  count, files, and the unify-vs-record question all
  verified; the failure-mode difference is real and the
  decision is genuinely open.
- `connection-order-ladder` owner-cell adjustment:
  ENDORSED — the composing clause is accurate (composer
  + sub-owner verified), files already complete, no
  split. The s10 "no row split" note anticipated exactly
  this shape.

### Defects

None found in the package by this pass. C1 is an artifact
record correction, not a package defect.

### Freshness

HEAD `83998e08` unmoved (confirmed before the first read
and after the last). Target HEAD `fdc4b1b0` vs worktree
`3e005158` (exactly the 3-line truth re-adoption). Every
cited body read via `git show HEAD:` (immune to worktree
dirt); re-hashed clean both blobs:
`optimizer/lateral_fetch.py` `583f6d7b`,
`tests/optimizer/test_plans.py` `df714065`. Any
fingerprint change reopens.

### Verdict

Verified. Every verdict row survives on independent
evidence with my own counts; zero-edit holds (item-scoped
diff 0 bytes); one record correction (C1) with no verdict
movement, no resubmission; no `.py` touched so no
ruff/mypy owed.
