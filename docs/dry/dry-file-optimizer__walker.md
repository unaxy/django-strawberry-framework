# DRY review: `optimizer/walker.py`

Status: verified
Run: 0.0.15 2026-09-19-1
Target: `django_strawberry_framework/optimizer/walker.py` (1574 lines)
Blob: `9b111ed938951a073a9226ccbcfacabc3af981e8` (worktree == HEAD;
`git diff HEAD --stat -- <target>` empty; target worktree-clean)
Item baseline: `8d0f234ab8388e4a466405c46990826b99c1c890` (`git stash create`
at item open)
Ledger check: `## Owned changes` in [dry-0_0_15.md][plan] names exactly one
walker row — the D1 seal-policy fix (`import _PREFETCH_CHILD_POLICY`,
`_build_child_queryset` seal policy + docstring, from File
`utils/querysets.py`, verified by Worker 2). Re-verified present below as
established fact (D1-A); no re-litigation. No other ledger row touches this
path. Item-scoped diff: zero tracked edits; one new untracked file (this
artifact).

## System trace

The target owns the optimizer's selection-walk drive surface: entry seams
(`plan_optimizations`, `plan_relation`), the recursive walk
(`_walk_selections`), cardinality dispatch (`_dispatch_single_relation`,
`_plan_select_relation`, `_plan_prefetch_relation`), and every helper the
walk spends exactly once per relation — field-map/definition source,
GraphQL-name resolution, hint dispatch, alias merge, child-queryset seam,
projection/elision, connector columns, path-key writers, and the
nested-connection delegation seam. Sibling optimizers own the vocabularies
the walk composes by name (plan record, selections, predicates,
join taxonomy, hints, nested planner); the walk defines none of them.

Sites read (roles: definition / consumer / oracle / projection):

- Definitions here, consumers elsewhere: the drive surface consumed by
  [extension.py][extension] (`plan_optimizations` at `:1319`,
  `plan_relation` delegate at `:1538-1555`); the ten-callable injection
  surface consumed by [nested_planner.py][nested-planner]
  (`plan_connection_relation` signature at `:1068-1077`, all ten callables
  spent at `:1105-1266`); re-export aliases read by
  [test_walker.py][test-walker] through this module's namespace
  (`_should_include`, `_is_fragment`, `_concrete_order_columns`,
  `_relay_max_results_from_info`, plus direct unit pins of
  `_apply_hint`, `_merge_aliased_selections`, `_resolve_selection_target`,
  `_selected_scalar_names`, `_prefetch_hint_for_path`,
  `_plan_connection_relation`, `_enable_only_for_operation`,
  `_aliased_arguments_diverge`, `_field_by_graphql_name`,
  `_graphql_names_by_python_name`, `_ensure_connector_only_fields`,
  `_record_prefetch_path_keys`, `_record_select_path_keys`,
  `_merge_runtime_prefixes`, `logger`).
- Consumers here, definitions elsewhere: [plans.py][plans] (`OptimizationPlan`,
  `append_unique`, `append_unique_many`, `append_prefetch_unique`,
  `resolver_key`, `runtime_path_from_info`, `merge_from`,
  `merge_metadata_from`, `finalize`); [selections.py][selections] (all eight
  aliased primitives); [nested_planner.py][nested-planner] (nine aliases +
  `_coerce_pagination_int` + `_plan_nested_connection_relation`);
  [join_taxonomy.py][join-taxonomy] (`classify_relation_join`);
  [hints.py][hints] (`OptimizerHint`, `hint_is_skip`);
  [field_meta.py][field-meta] (`FieldMeta`); [querysets.py][querysets]
  (`_PREFETCH_CHILD_POLICY`, `apply_type_visibility_sync`, `base_queryset`);
  [relations.py][relations] (`instance_accessor`,
  `is_many_side_relation_kind`, `relation_kind`); [strings.py][strings]
  (`snake_case`); [typing.py][typing] (`schema_config_from_info`);
  [registry.py][registry] (`registry.get`, `registry.get_definition`);
  [definition.py][definition] (slots `related_target_for`,
  `optimizer_hints`, `relation_connections`,
  `consumer_assigned_relation_fields`, `has_custom_id_resolver_for`,
  `origin_has_custom_id_resolver`); [resolvers.py][resolvers]
  (`_check_n1` resolver-key parity, `_field_meta_for_resolver` policy prose,
  `_build_fk_id_stub` column contract).
- Oracles: [test_walker.py][test-walker] (175 `def test`, blob `5bbd7a56…`
  == HEAD, worktree-clean), [test_definition_order.py][test-def-order],
  [test_field_meta.py][test-field-meta], [test_multi_db.py][test-multi-db]
  (all import from this module); live `/graphql` suites exercise the walk
  end to end (projection, visibility, multi-db alias, resource-policy).
- Projections (listed, never counted): spec-035 Decision 4 (G2
  operation gate, every projection writer); spec-033 Decisions 3/4/6/7/8
  (metadata-driven connection recognition, window planning, refusal arms,
  strictness wiring); spec-045 Decision 5 (degrade-to-unplanned; the
  `reject_sliced=False` rationale); spec-016 (field-map dual contract +
  its registry-coverage retirement trigger; KANBAN WP-D note);
  [GLOSSARY.md][glossary] (`apply_type_visibility_sync` entry names the
  optimizer walker among the sealed surfaces; `Multi-database cooperation`
  axis-3 wording — KANBAN-homed, not re-raised); KANBAN card bullets
  (`_record_relation_access`-before-elision ordering — homed, unpinned by
  test; `_optimizer_runtime_prefixes` literal grammar — homed; workstream
  vocabulary split; spec line-number citations — all homed elsewhere).
- D1 ledger row (THIS cycle's committed fix on the target itself):
  D1-A import `_PREFETCH_CHILD_POLICY` (`:17`, inside the
  `utils.querysets` import at `:16-20`); D1-B `_build_child_queryset`
  seal policy (`policy=_PREFETCH_CHILD_POLICY` at `:476`, rationale
  docstring at `:449-470` naming `reject_sliced=False` +
  `require_shared_alias=True`); D1-C `_UNRECOMPOSED_CHILD_POLICY` zero
  hits across all `*.py` (`grep -rn` clean; one stale `.pyc` match only,
  regenerable, not a source site). The fast-forward repointed the
  prefetch-child path from the deleted policy to `_PREFETCH_CHILD_POLICY`;
  the CURRENT bytes recorded under F-W3/F-C2: seed
  `base_queryset(field.related_model)` (`:447`), no `.using(...)`, custom
  hook only when `has_custom_qs`, `model=target_model` threaded (`:475`),
  alias question NOT decided here (open `child-queryset-alias-inheritance`
  family owns it).

## Verification

### Matrix

Six axes discharged against the target's real surface (searches run, not
sampled):

1. **Cross-flavor policy mirroring** — searched sibling flavors for a
   second walk/dispatch vocabulary (`relation_kind` readers,
   `get_queryset`-downgrade verdicts, `optimizer_hints` dispatches beyond
   this module + nested planner). Only consumers found, each composing the
   single owner by name: `plan_relation` verdict consumed by
   [extension.py][extension]`::plan_relation` (thin delegate, `:1555`) and
   by this module's own dispatch; `has_custom_get_queryset` verdict
   consumed by [resolvers.py][resolvers]`::_custom_visibility_type`
   (resolve-time re-check for UNPLANNED paths — different population:
   planned-child vs never-planned, R-halves recorded) and
   [finalizer.py][finalizer] (registration-time shape classification).
   No second walker. SKIP/strategy arms for nested connections live in
   [nested_planner.py][nested-planner] (different population: windowed vs
   direct, F-W6 records the split).
2. **Sync/async twins** — `grep -n "async def\|await " <target>` returns
   zero; the walk is sync-only and names its recourse in prose
   (`_build_child_queryset` docstring: async-only related `get_queryset`
   surfaces `SyncMisuseError`, consistent with the connection field's
   `relation_shapes = list` recourse). No twin to drift; the sync/async
   runner split lives in [querysets.py][querysets] (already indexed).
3. **Derived rather than repeated knowledge** — three derivations checked:
   (a) field-map fallback keys stay raw `f.name` (`:362`) while
   [base.py][types-base]`::__init_subclass__` builds `{snake_case(f.name):
   ...}` (`:686`) — different key grammar AND different population
   (unregistered-model plan-time vs Meta-declared registration-time),
   recorded separation R1, retirement trigger shared; (b) forward
   GraphQL→python resolution here vs [finalizer.py][finalizer]'s reverse
   python→graphql map (`_settled …` at `:232-279`) — opposite directions,
   opposite times, R2; (c) `.name_converter` read here (None-passthrough,
   `:241`) vs [selections.py][selections]`::connection_field_names`
   (`apply_naming_config` + `DEFAULT_CONNECTION_FIELD_NAMES` fallback,
   `:562-568`) — same source line, divergent contracts, shared owner
   [typing.py][typing]`::schema_config_from_info`, R3.
4. **Inverse / round-trip pairs** — `_prefetch_hint_for_path`
   (type-relative→full-path rebase, `:1184-1213`) has no inverse anywhere
   (one-direction adaptation; the reverse lookup never happens); resolver
   keys are ENCODED here via [plans.py][plans]`::resolver_key` and
   REBUILT at resolve time by [resolvers.py][resolvers]`::_check_n1` and
   [connection.py][connection] (`kind="connection_to_attr"`) — documented
   parity (`_resolver_identities_for` docstring `:481-503`), one grammar,
   no second encoder. `_record_path_resolver_keys` triple WRITES the
   plan's path-key maps; [plans.py][plans]`::merge_from` MERGES them
   (`:322-327`) — writer vs merger, R10.
5. **Contracts restated in another medium** — every medium move listed
   under System trace projections/oracles; none counted as a definition.
   Test oracles pin behavior without reading owner internals (literal
   selections + plan-shape assertions; the `_isolate_registry` fixture
   pins the no-custom-`get_queryset` dispatch precondition explicitly).
6. **Enforcement by omission** — full member sweep of the guard-bearing
   rules: (a) `consumer_assigned` guard (direct path `:690-694` +
   `to_attr` refusal `:1076-1092`) ABSENT on the nested path — proved
   UNREACHABLE, not a gap: [finalizer.py][finalizer]
   `:_synthesize_relation_connections` skips `consumer_authored_fields`
   (`:684-689`, implicit default; explicit raises at type creation per
   Decision 7), and `consumer_authored_fields` ⊇
   `consumer_assigned_relation_fields` ([base.py][types-base] `:779-784`),
   so no `relation_connections` entry — the nested branch's only trigger
   — can name a guarded relation. Candidate rejected (R7), no defect.
   (b) `cacheable = False` poisoning: direct custom-qs (`:905-906`) +
   hinted-prefetch (`:1127-1131`) + nested custom-qs
   ([nested_planner.py][nested-planner] `:1257`) + `_absorb_child_plan`
   propagation (`:1216-1227`, "a future third site cannot forget it") —
   every absorb site covered; no missing member. (c) `enable_only`
   threading: root + both nested recursions + nested delegation forward
   one bool; `_project_scalar_only_window` consults the gate itself
   (direct `.only()`, documented `:684-688`); every projection writer
   named in spec-035 Edge cases lands on a gated site — verified by
   reading each writer (`:649`, `:668-669`, `:963-964`, `:1336-1337`,
   `:690-691` nested). No omission found.

### Enumeration

Instrument: `ast.Module.body` top-level statement census over the CURRENT
bytes (blob `9b111ed9…`). Count: **78 statements = 1 module docstring +
23 imports + 17 alias assigns + 37 defs**. Every def lands in a family row
below (F-W1..F-W9 new for Worker 0; existing rows as consumers); every
alias lands on its owner's family as re-export/consumer; zero file-local
(all members have a second site: nested-planner injection, extension
delegate, or test-pin import); twelve rejections R1..R12 carry contract
difference + trigger. Imports are vocabulary sources, not rules.

| # | Member | Home |
|---|---|---|
| 1 | `plan_optimizations` (`:142`) | F-W1 `walker-drive-surface` (definition) |
| 2 | `plan_relation` (`:185`) | F-W1 (definition; extension delegate = consumer) |
| 3 | `_walk_selections` (`:520`) | F-W1 (definition) |
| 4 | `_dispatch_single_relation` (`:751`) | F-W1 (definition; two hint branches = consumers) |
| 5 | `_plan_select_relation` (`:805`) | F-W1 (definition) |
| 6 | `_plan_prefetch_relation` (`:866`) | F-W1 (definition) |
| 7 | `_record_relation_access` (`:937`) | F-W1 (definition; KANBAN-homed ordering invariant cited, not re-filed) |
| 8 | `_plan_connection_relation` (`:1539`) | F-W1 (definition; nested-planner signature = consumer) |
| 9 | `_enable_only_for_operation` (`:121`) | F-W2 `operation-gated-projection` (definition) |
| 10 | `_build_child_queryset` (`:411`) | F-W3 `prefetch-child-build-seam` (definition) + consumer of `sealed-execution-queryset` + `child-queryset-alias-inheritance` (D1 bytes recorded, alias undecided) |
| 11 | `_build_prefetch_child_queryset` (`:968`) | F-W3 (definition) |
| 12 | `_build_prefetch_child_queryset_from_base` (`:1005`) | F-W3 (definition; nested planner injects = consumer) |
| 13 | `_absorb_child_plan` (`:1216`) | F-W3 (definition) |
| 14 | `_resolve_selection_target` (`:292`) | F-W4 `selection-target-resolution` (definition) |
| 15 | `_field_by_graphql_name` (`:262`) | F-W4 (definition; also spent by `_selected_scalar_names` = same-family consumer) |
| 16 | `_graphql_names_by_python_name` (`:244`) | F-W4 (definition) |
| 17 | `_schema_name_converter` (`:239`) | F-W4 (definition; R3 separates selections' connection-vocabulary read) |
| 18 | `_resolve_field_map` (`:328`) | F-W5 `relation-target-definition-source` (definition; R1/R4 separate base.py + resolver-side reads) |
| 19 | `_resolve_relation_target` (`:366`) | F-W5 (definition; nested planner injects = consumer) |
| 20 | `_target_has_custom_get_queryset` (`:215`) | F-W5 (definition; `plan_relation` + both prefetch paths + nested spend it = consumers) |
| 21 | `_resolve_optimizer_hints` (`:404`) | F-W5 (definition; nested planner injects = consumer) |
| 22 | `_has_custom_id_resolver` (`:1293`) | F-W5 (definition; registered-vs-fallback halves share one free function, R12) |
| 23 | `_apply_hint` (`:1038`) | F-W6 `optimizer-hint-dispatch` (definition; nested SKIP/strategy arms = separate population) |
| 24 | `_prefetch_hint_for_path` (`:1184`) | F-W6 (definition) |
| 25 | `_merge_aliased_selections` (`:1352`) | F-W7 `aliased-selection-merge` (definition; composes `included_field_selections`, R9) |
| 26 | `_record_response_key_arguments` (`:1431`) | F-W7 (definition) |
| 27 | `_normalized_alias_payload` (`:1463`) | F-W7 (definition) |
| 28 | `_response_key_arguments_conflict` (`:1485`) | F-W7 (definition; nested planner injects = consumer) |
| 29 | `_aliased_arguments_diverge` (`:1496`) | F-W7 (definition; nested planner injects = consumer) |
| 30 | `_selection_runtime_prefixes` (`:1518`) | F-W7 (definition; literal grammar shared with selections noted for the family item) |
| 31 | `_merge_runtime_prefixes` (`:1526`) | F-W7 (definition) |
| 32 | `_resolver_identities_for` (`:481`) | F-W7 (definition; nested planner injects = consumer; parity with `_check_n1` documented, not duplicated) |
| 33 | `_selected_scalar_names` (`:1230`) | F-W8 `scalar-projection-and-fk-elision` (definition; sole production caller `_plan_select_relation`, verified by grep) |
| 34 | `_ensure_connector_only_fields` (`:1314`) | F-W9 `prefetch-attach-column-projection` (consumer of join-taxonomy descriptor; sibling consumer `_project_scalar_only_window`) |
| 35 | `_record_path_resolver_keys` (`:91`) | consumer of `resolver-key-grammar` (writer; merger lives in plans) |
| 36 | `_record_prefetch_path_keys` (`:103`) | consumer of `resolver-key-grammar` |
| 37 | `_record_select_path_keys` (`:112`) | consumer of `resolver-key-grammar` |
| A1..A8 | selections aliases (`:63-70`) | re-export/consumers: `_should_include`→`converted-directive-evaluation`; `_is_fragment`→`converted-fragment-discriminator` (+ module-body reads `:1371,1382`); `_response_key`/`_response_keys`→`response-key-grammar` (body reads `:512,1394,1418,1423`); `_included_field_selections`→`fragment-inlining-flatten` (body reads `:569,1265`); `_named_children`→`fragment-descending-name-match`; `_node_children_with_runtime_prefix`→`edges-node-unwrap`; `_with_runtime_prefix`→`runtime-prefix-cloning` (last three: NO code reader in this module — assignment-only, verified by grep; readers take the first two from [extension.py][extension], per the module docstring, verified) |
| A9..A17 | nested-planner aliases (`:80-88`) | holding: File `optimizer/nested_planner.py` (unticked; families TBD by that item). Verified by grep: 8/9 have NO code read in this module (pure re-exports for test pins: `_concrete_order_columns`, `_relay_max_results_from_info` read BY tests through this namespace at [test_walker.py][test-walker] `:2484,3108`; the other seven read from [nested_planner.py][nested-planner] directly — [connection.py][connection] `:77-78`, [test_keyset_connection.py][test-keyset] `:68-71`). `_coerce_pagination_int` is a DIRECT import (`:29`, not an alias) with one code read (`:1481`) — consumer of nested-planner order vocabulary, outside the nine-alias accounting (docstring scope verified consistent, no defect). `_plan_nested_connection_relation` (`:30-32`) spent once (`:1554`) — seam consumer, F-W1. |

### Challenges

One posited change per rule family, variation axes exercised, definition
counts recorded (consumers/oracles/projections listed, never counted):

- C1 (F-W1; cardinality): add a second many-side shape (e.g. a new
  virtual relation kind) → `is_many_side_relation_kind`
  ([relations.py][relations], owner) moves once; `plan_relation` composes
  it → **count 1**.
- C2 (F-W3/seal; policy fields): flip `require_shared_alias` on the child
  policy → `_SealPolicy` record ([querysets.py][querysets]) moves once;
  walker passes the policy by name (`:476`) → **count 1**. (Alias
  BEHAVIOR undecided here — open family owns it.)
- C3 (F-W2; gate semantics): change which operations project (e.g. gate
  subscriptions differently) → `_enable_only_for_operation` moves once;
  every writer takes the bool → **count 1**. Contrast: extension's
  `_build_cache_key` reads `info.operation` directly (`:1495`) for a
  DIFFERENT rule (cache identity, R8) → not a second definition.
- C4 (F-W7/keys; grammar): change the resolver-key grammar →
  [plans.py][plans]`::resolver_key` moves once; walker, nested planner,
  resolvers compose → **count 1**.
- C5 (F-W7/merge; conflict states): add a third alias-payload state →
  walker merge trio moves once (single module); nested planner spends via
  injection → **count 1**.
- C6 (F-W6/hints; new flag): add a fifth hint shape → shape record
  ([hints.py][hints]`::OptimizerHint`) moves once; dispatch = 1 walker
  arm (direct) + nested SKIP/strategy arms (windowed) — two
  population-specific dispatches, same shape/different decisions
  (window vs plain `Prefetch`), intentional split, **not count 2**.
- C7 (F-W9/connectors; column set): add a morph half →
  `prefetch_attach_columns` ([join_taxonomy.py][join-taxonomy]) moves once;
  walker + `_project_scalar_only_window` compose → **count 1**.
- C8 (F-W5/verdict source): answer custom-qs from the origin instead of
  the captured definition → `_target_has_custom_get_queryset` moves once;
  `plan_relation` + both prefetch paths + nested spend it → **count 1**.
- C9 (F-W5/fallback keys): re-key the unregistered-model fallback →
  `_resolve_field_map` fallback moves once ([base.py][types-base]
  registration build is a different population, R1) → **count 1**.
- C10 (F-W5/retirement): land the registry-coverage gate (delete the
  fallback) → 1 site + its docstring paragraph + spec-016 bounded-exception
  bullet (projections) → **count 1**, trigger recorded at R1.
- C11 (F-W4/naming): change digit-boundary camelization handling →
  `_field_by_graphql_name` moves once; both spend sites
  (`_resolve_selection_target`, `_selected_scalar_names`) compose it →
  **count 1**.
- C12 (F-W8/elision): change the elision precondition (e.g. drop the
  custom-id-resolver arm) → `_plan_select_relation` condition moves once;
  `_build_fk_id_stub` ([resolvers.py][resolvers]) READS the projected
  column, it does not restate the condition → **count 1**.

All challenges static-reviewed (single-module bodies composed by name,
injection seams read off the nested-planner signature, parity prose
verified against resolve-side rebuilds). No execution owed: nothing
ordering, transactional, or async is at issue; the one behavior question
(child alias) is fenced out by item scope.

## Findings

Nine new families named for Worker 0 (no consolidation in this file item;
each names owner + members + consumers + lifetime where stored state is
involved). Rejections R1..R12 follow with contract difference + trigger.

### F-W1 `walker-drive-surface` (NEW; owner `optimizer/walker.py`)

Contract: walk a converted selection tree into an `OptimizationPlan` —
root entry with source-type override, relation-namespace resolution
(connection-first, then field, then Relay-pk/custom-pk fallbacks),
cardinality dispatch, select vs prefetch planners with shared connector
recording, consumer-assigned refusal, and atomic nested-connection
delegation. Members: `plan_optimizations`, `plan_relation`,
`_walk_selections`, `_dispatch_single_relation`, `_plan_select_relation`,
`_plan_prefetch_relation`, `_record_relation_access`,
`_plan_connection_relation`. Consumers: [extension.py][extension] (entry +
delegate), [nested_planner.py][nested-planner] (delegation target),
test/live oracles. Variation axes: new relation cardinality, new
selection namespace, new refusal arm. Lifetime: no stored derivation —
`OptimizationPlan` built per call, `finalize()`d at handoff (`:178-182`;
immutability rationale in prose). Challenges C1/C12 (count 1 each).
Behavioral proof: static-reviewed (175-test oracle tier + live suites pin
the surface; happy-path-only changes would still need execution, none
proposed). Structural gate: none proposed (drive surface, not a bypassable
helper — bypass population is "anyone reimplementing the walk", open-ended;
a bespoke existence test per entry point is refused per DRY.md gate-only
rule). Freshness: target blob `9b111ed9…` (== HEAD); extension cite
`49667a93…`; nested-planner cites fingerprinted worktree+HEAD separately
(see Freshness).

### F-W2 `operation-gated-projection` (NEW; owner `optimizer/walker.py::_enable_only_for_operation`)

Contract (spec-035 Decision 4): derive the projection bool ONCE from
`info.operation` (None/partial-double → enabled default, `:121-139`) and
thread it through every walk recursion, child plan, and scalar-only
window. Consumers: all projection writers in this module + nested
planner's `enable_only` params + `_project_scalar_only_window`'s
self-consult. Challenge C3 (count 1). Trigger for reconsideration: a
projection writer that must read `info.operation` ITSELF (e.g. a
three-state gate) — today every writer takes the bool.

### F-W3 `prefetch-child-build-seam` (NEW; owner `optimizer/walker.py`)

Contract: the queryset-boundary abstraction — visibility/default-manager
base built once (`_build_child_queryset`), child plan applied onto it
(`_build_prefetch_child_queryset_from_base`), metadata + cacheability
absorbed (`_absorb_child_plan`, incl. the cannot-forget
`merge_metadata_from` coupling, `:1216-1227`). Consumers: nested planner
via `build_child_queryset` / `build_prefetch_child_queryset_from_base`
injection. D1 bytes recorded (import `:17`, policy `:476`, rationale
`:449-470`); seal POLICY owned by `sealed-execution-queryset`, alias
BEHAVIOR owned by open `child-queryset-alias-inheritance` — this family
owns only the seam. Challenges C2/C8 (count 1 each). Lifetime: plan-local
`OptimizationPlan` pairs (parent/child), absorbed before return, never
cached mid-build (cacheability poisoned, never stored).

### F-W4 `selection-target-resolution` (NEW; owner `optimizer/walker.py`)

Contract: forward GraphQL-name → Django-field resolution — connection
namespace first (metadata-driven, never name-pattern guessing), exact
snake reversal, authoritative-converter scan on a miss (lossy
digit-boundary + custom converters). Members: `_resolve_selection_target`,
`_field_by_graphql_name`, `_graphql_names_by_python_name`,
`_schema_name_converter`. Consumers: `_walk_selections`,
`_selected_scalar_names` (scalar subset, connection form unreachable by
construction — documented `:1275-1278`). Challenge C11 (count 1).
R2/R3 separate the reverse map and the connection-vocabulary read.

### F-W5 `relation-target-definition-source` (NEW; owner `optimizer/walker.py`)

Contract (the one-definition rule): every decision about a relation
target spends ONE captured `DjangoTypeDefinition` — field map
(`_resolve_field_map`, incl. the spec-016 fallback), target pair
(`_resolve_relation_target`, registry-only fallback in the same shape),
custom-qs verdict (`_target_has_custom_get_queryset`), hints map
(`_resolve_optimizer_hints`), id-resolver check
(`_has_custom_id_resolver`, both halves share
[definition.py][definition]`::origin_has_custom_id_resolver`, R12).
Consumers: nested planner via four injected callables. Challenges
C8/C9/C10 (count 1). Retirement trigger (fallback): registry-coverage
gate lands → delete fallback + docstring paragraph + spec-016
bounded-exception bullet together (KABAN WP-D note).

### F-W6 `optimizer-hint-dispatch` (NEW; owner `optimizer/walker.py::_apply_hint`)

Contract: the four configurable hint shapes + empty-hint fallthrough —
SKIP (True, unplanned), `prefetch_obj` (validate-before-mutate `:1101-1109`,
`to_attr` refused unless consumer-assigned, rebased onto the accessor,
non-cacheable mark + B8 key attribution), `force_select` (many-side
refused, custom-qs downgrade preserved), `force_prefetch`. Nested
SKIP/strategy arms live in nested planner (different population:
windowed vs direct, C6). Challenge C6 (1 shape + intentional split).
Trigger: a hint shape needing window semantics on the DIRECT path (or
vice versa) re-opens the split.

### F-W7 `aliased-selection-merge` (NEW; owner `optimizer/walker.py`)

Contract: same-field merge preserving every response key — fast path
(`:1369-1378`), `SimpleNamespace` rebuild with `_optimizer_response_keys`
/ `_optimizer_runtime_prefixes` / per-key argument map, conflict flag
(`_record_response_key_arguments`), pagination-normalized comparison
(`_normalized_alias_payload`), scheme selector
(`_aliased_arguments_diverge`), prefix union
(`_merge_runtime_prefixes`), identity emission
(`_resolver_identities_for`, incl. the connection-vocabulary key-parity
contract with `_check_n1`, `:481-503`). Consumers: nested planner via
three injected callables. Challenges C4/C5 (count 1). Note for the family
item: `_optimizer_runtime_prefixes` crosses into
[selections.py][selections] as a kwarg (`connection_node_children`) with
NO named constant (KANBAN-homed); the literal occurs twice here, both
inside `getattr` — consolidation, if any, belongs to the family item, not
this file.

### F-W8 `scalar-projection-and-fk-elision` (NEW; owner `optimizer/walker.py`)

Contract: which COLUMNS load — Relay custom-pk `id` projection via
`FieldMeta` name/attname scan (NOT `in field_map`, `:625-633`),
default-pk/scalar appends, FK-id elision triple-condition
(`fk_id_elision_eligible` + no custom-qs + no custom id resolver +
scalar-set == `{target_pk_name}`, `:839-847`), `_selected_scalar_names`
(sole production caller verified; nested-only audit invariant, no merge,
documented `:1239-1263`). Column CONSUMER
[resolvers.py][resolvers]`::_build_fk_id_stub` reads `obj.<fk>_id` — reads
the projected column, never restates the condition (C12, count 1).
`_record_relation_access`-before-elision ordering cited (KANBAN-homed,
unpinned — referenced, not re-filed).

### F-W9 `prefetch-attach-column-projection` (NEW; owner `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`)

Contract: attach-complete connector projection (connector + GenericRelation
morph half) under the G2 gate. Two consumers composing ONE descriptor
reader: `_ensure_connector_only_fields` (here, `:1340`) and
`_project_scalar_only_window` ([nested_planner.py][nested-planner] `:700`,
same-owner comment at `:695-699`). Challenge C7 (count 1). Adjacency:
`window-partition-resolution` (same candidate owner, different rule —
partition expression vs attach columns); `_connector_only_field` shim
(`parent_join_column`, single-valued) vs `_record_relation_access`
attname append — different columns, different joins (R5).

### Rejections (investigated, single-ownership or split-correct stands)

- R1 field-map fallback vs [base.py][types-base] collection build:
  different key grammar (raw `f.name` vs `snake_case(f.name)`), different
  population (unregistered-model plan-time vs Meta-declared
  registration-time). Trigger: registry-coverage gate (shared with F-W5).
- R2 forward resolution (F-W4) vs finalizer reverse map: opposite
  directions, opposite times (request vs finalization). Trigger: a
  request-time need for the reverse direction outside finalization.
- R3 `_schema_name_converter` (None-passthrough) vs
  `connection_field_names` (converter + `apply_naming_config` + default
  fallback): same source line, divergent contracts; shared owner
  [typing.py][typing]`::schema_config_from_info`. Trigger: a change to
  the default semantics both sites must share.
- R4 whole-map `_resolve_field_map` vs `_field_meta_for_resolver`
  single-field resolve-time read: different shapes/consumers; "keep in
  sync" prose is policy, not shared body. Trigger: shared with R1.
- R5 `_connector_only_field` shim vs `_record_relation_access` attname:
  different columns for different joins; both compose join_taxonomy by
  name. Trigger: a join needing BOTH columns from one call site.
- R6 `plan_relation` vs extension delegate: delegate, not a second
  definition (same args, no branch). No trigger (delegation is the shape).
- R7 nested-path `consumer_assigned` absence: unreachable by
  construction (finalizer skip ⊇ guard population; Matrix axis 6 proof).
  Trigger: a `relation_connections` entry for a consumer-authored
  relation (today raises at type creation).
- R8 gate vs cache-key `info.operation` read: different rules
  (projection vs identity). Trigger: none (different reasons to change).
- R9 merge (F-W7) vs `included_field_selections` flatten: merge AFTER
  flatten (`:569`) — composition, not duplication. Trigger: none.
- R10 path-key writers vs `merge_from` map-merge: writer vs merger.
  Trigger: a third writer bypassing the triple.
- R11 `_selected_scalar_names` forward-resolve vs
  `_resolve_selection_target`: shared primitive composed by name (same
  module); connection-namespace absence is constructional (single-valued
  elision). Trigger: elision over a connection child.
- R12 `_has_custom_id_resolver` halves: one free function both paths
  (registered memoized check vs lazy-import fallback) — one rule by
  construction. Trigger: a third id-customization shape the free
  function cannot see.

## Defects

None filed. Investigated-but-clear records (kept so the next cycle does
not re-litigate):

- I1 nested-path `consumer_assigned` absence → unreachable by
  construction (Matrix axis 6 proof: finalizer skip ⊇ guard population).
  Not an enforcement gap; R7 carries the trigger.
- I2 alias-docstring scope (`_coerce_pagination_int` read at `:1481`
  outside the nine-alias accounting) → consistent on a strict read: the
  "only two are read" sentence scopes to the `:80-88` aliases; the
  line-`:29` direct import is separate machinery with its own reader.
  Verified 8/9 aliases assignment-only by grep; test-pin reads verified
  at [test_walker.py][test-walker] `:2484,3108`; direct-from-owner reads
  verified at [connection.py][connection] `:77-78` and
  [test_keyset_connection.py][test-keyset] `:68-71`.
- I3 `_walk_selections` docstring naming `_build_prefetch_child_queryset`
  (wrapper) rather than `_build_prefetch_child_queryset_from_base`
  (direct recursion site) → operative claim (nested calls omit
  `source_type`, nested targets route to the primary) true of the whole
  subtree; naming a wrapper is not a contradiction. Below the defect bar.
- I4 `_UNRECOMPOSED_CHILD_POLICY` one stale `.pyc` match
  (`tests/utils/__pycache__`) → regenerable artifact, not a source site;
  zero `*.py` hits. The sealed family verified the retire; recorded here
  only for the alias family holding the behavior question.
- I5 KANBAN-homed prose already owned elsewhere (recorded under System
  trace projections, not re-filed): `_record_relation_access` ordering
  unpinned by test; `_optimizer_runtime_prefixes` literal grammar;
  GLOSSARY axis-3 unqualified wording; workstream vocabulary; spec
  line-number citations.

## Pending execution

None. No `proof:` entries (every challenge `static-reviewed`; nothing
ordering, transactional, or async is at issue, and the child-alias
behavior question is fenced to the open family by item scope). No `gate:`
entries. Deliberately no focused `--no-cov` run: execution cannot beat
inspection on any open claim — alias readers settled by grep over closed
populations, D1 bytes read directly, guard reachability proved through
the synthesis-gate code chain, docstring claims checked against the
citing bodies. `uv run pytest` not run (AGENTS.md: no pytest after
edits; zero source edits made in any case).

## Judgment

Zero-edit file item, ready for verification. The walk defines nine rule
clusters (F-W1..F-W9, named above for Worker 0's index) and consumes
eleven indexed families plus four holding vocabularies owned by unticked
items (nested planner, hints, join taxonomy beyond F-W9's descriptor,
plan/strategy/selection/predicate rows verified-not-inherited per the
plan's trigger note). Every one of the 37 defs and 17 aliases is homed;
twelve rejections carry contract differences + triggers; no defect meets
the bar; no execution is owed. D1 ledger row re-verified present on the
target; CURRENT prefetch-child bytes traced and recorded
(`base_queryset(field.related_model)` seed, no `.using()`,
`model=target_model`, `policy=_PREFETCH_CHILD_POLICY`) with the alias
question explicitly undecided here.

## Freshness fingerprints

(`git hash-object` worktree; `HEAD:` where dirty. Any change reopens.)

- Target [walker.py][walker]: `9b111ed938951a073a9226ccbcfacabc3af981e8`
  (worktree == HEAD == ITEM_BASELINE-era; `git diff HEAD --stat` empty).
- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
  ITEM_BASELINE: `8d0f234ab8388e4a466405c46990826b99c1c890`.
- EXTERNAL concurrent dirt, fingerprinted separately per cited site,
  never edited; cited regions re-confirmed outside every hunk:
  [nested_fetch.py][nested-fetch] worktree
  `29ce5201877864b01079c849b92a1e812166affd` vs HEAD
  `4d8d37a7f52cf94d2916f17db3a8a21393e28d57` (+28 resolve_strategy);
  [nested_planner.py][nested-planner] worktree
  `e69dbf5f30aa4623a5aad93edfacdabb391d6601` vs HEAD
  `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04` (+9 advisory; injection
  signature + `:1097-1098,1126-1145,1241-1266` spends read off CURRENT
  worktree bytes); [join_taxonomy.py][join-taxonomy] worktree
  `e1cbb3e327785de3b59ccafef6b463df52e06396` vs HEAD
  `9b355a5090ce471e373849dd0a61da8f808e78b9` (+39 composite-pk;
  `classify_relation_join` + `prefetch_attach_columns` bodies outside it);
  [hints.py][hints] worktree
  `8064af14930636d6b12a538a996603ccadfdb420` vs HEAD
  `da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74` (+13 hostile-guard;
  `OptimizerHint` + `hint_is_skip` outside it); [connection.py][connection]
  worktree `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` vs HEAD
  `93e998f2c7ea1d7f18607a6e37e394466ac75ad4` (hunks at `:54,:703,:734`;
  cited `:77-78,:2170-2249` untouched, diff-verified); [registry.py][registry]
  worktree `612bea87fdcf5e5a254caf70c9947b9535f638c3` vs HEAD
  `9cc8bb553fd417fc465809a541769a8383469cda` (+4 docstring lines in
  `definition_for_graphql_name`; `get`/`get_definition` untouched).
- Clean cites (worktree == HEAD): [plans.py][plans]
  `cce985319c8833f3660653327d3003f1f03655a5`; [selections.py][selections]
  `a48f6172c6f04331740d1b110d742f17701ff846`; [extension.py][extension]
  `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`;
  [field_meta.py][field-meta]
  `7215c887aa26b1d828503ca30dd3b02546fe68b3`; [querysets.py][querysets]
  `96618fba4eafb6a87e73414770014e3aee5b41ef`;
  [relations.py][relations]
  `1cf81e5820eca5930905601b77844e93398b8b1a`;
  [strings.py][strings]
  `3ec3b262ea8666d4ba36cf83807ca377fee5a680`;
  [typing.py][typing]
  `de6309f6cb5915e9f42d0e19f564f4e67226e334`;
  [resolvers.py][resolvers]
  `5f4cce2b1bb37b75af4239f264ed0049a9faa5c9`;
  [definition.py][definition]
  `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`;
  [finalizer.py][finalizer]
  `f4266a153313b5f0de21eccead5d175edb586e77`;
  [types-base][types-base]
  `bc8dcdb6d25b9bff815ac596e6fd21fa76eb39b1`;
  [test_walker.py][test-walker]
  `5bbd7a567f045e7d3870a10702ac22a5738cb8c0` (== HEAD; one intermediate
  hash differed transiently mid-item — concurrent touch or misread —
  re-hashed stable twice after; recorded values are artifact-write-time).
- Populations searched: `django_strawberry_framework/**/*.py` (whole-tree
  greps for `has_custom_get_queryset`, `consumer_assigned`,
  `from_django_field`, `prefetch_path_resolver_keys`,
  `schema_config_from_info`, `_merge_aliased`, walker importers,
  `_UNRECOMPOSED_CHILD_POLICY`); `tests/optimizer/test_walker.py`
  (import list + pin sites); live suites by suite-map (not re-run);
  [GLOSSARY.md][glossary], KANBAN bullets, spec-016/032/033/035/045
  decision text as contract sources. Modules EXCLUDED from every family
  on body strength: all non-optimizer flavors (no walk vocabulary found
  by the searches above).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[plan]: dry-0_0_15.md

<!-- docs/ -->
[glossary]: GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[definition]: ../../django_strawberry_framework/types/definition.py
[extension]: ../../django_strawberry_framework/optimizer/extension.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[hints]: ../../django_strawberry_framework/optimizer/hints.py
[join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[selections]: ../../django_strawberry_framework/optimizer/selections.py
[strings]: ../../django_strawberry_framework/utils/strings.py
[types-base]: ../../django_strawberry_framework/types/base.py
[typing]: ../../django_strawberry_framework/utils/typing.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-def-order]: ../../tests/optimizer/test_definition_order.py
[test-field-meta]: ../../tests/optimizer/test_field_meta.py
[test-keyset]: ../../tests/test_keyset_connection.py
[test-multi-db]: ../../tests/optimizer/test_multi_db.py
[test-walker]: ../../tests/optimizer/test_walker.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->





## Independent verification (Worker 2)

Phase-1 independent trace. The artifact's other sections were not opened; no
status is set and no verdict on Worker 1 is offered. All citations are
`path::Symbol` symbol paths (no line numbers).

### Target condition and D1 re-verification (not re-litigated)

- `django_strawberry_framework/optimizer/walker.py` is worktree-clean:
  worktree blob `9b111ed938951a073a9226ccbcfacabc3af981e8` ==
  `HEAD:django_strawberry_framework/optimizer/walker.py` blob, 1574 lines.
  HEAD is `bfaee91d`.
- The committed D1 seal-policy fix is present in both HEAD and worktree bytes
  and is re-verified present only:
  `optimizer/walker.py::_build_child_queryset` imports
  `utils/querysets.py::_PREFETCH_CHILD_POLICY` and
  `utils/querysets.py::apply_type_visibility_sync`, and calls the latter with
  `model=target_model` and `policy=_PREFETCH_CHILD_POLICY`. The surrounding
  comment records the two policy facts (`reject_sliced=False` for the
  designed degrade-to-unplanned path, `require_shared_alias=True` so the
  generated child leaves unrouted). No challenge to D1 is raised here.

### Enumeration (Worker 2, own instrument)

Instrument: every name in `ast.Module.body` of the target (imports spelled
out, not sampled). Count: 78 members (indices 0-77).

- 0: module docstring -> file-local (projection prose; describes the
  delegation contract, owns nothing).
- 1-23: `ImportFrom` edges -> consumers. The target consumes (never defines):
  `optimizer/selections.py` traversal primitives, `optimizer/plans.py` plan
  shape + key grammar, `optimizer/nested_planner.py` window planning,
  `optimizer/hints.py` hint shape, `optimizer/join_taxonomy.py` join
  classification, `utils/querysets.py` seeds + seals, `utils/relations.py`
  cardinality/accessor vocabulary, `registry.py`, `types` converters
  indirectly. No import is a second definition.
- 24-28: `_should_include`, `_is_fragment`, `_response_key`, `_response_keys`,
  `_included_field_selections` -> consumers of the `optimizer/selections.py`
  owner. `_response_keys` and `_included_field_selections` are read through
  this module's own bodies (`walker.py::_resolver_identities_for`,
  `walker.py::_walk_selections`, `walker.py::_selected_scalar_names`,
  `walker.py::_merge_aliased_selections`); `_should_include` / `_is_fragment`
  are additionally imported from `optimizer/walker.py` by
  `tests/optimizer/test_walker.py` (oracle-by-alias; see axis 5 observation,
  not a defect).
- 29-31: `_named_children`, `_node_children_with_runtime_prefix`,
  `_with_runtime_prefix` -> file-local dead re-exports. No reader through
  this module (stated in the module header); look-alike importers take the
  first two from `optimizer/extension.py`, which carries its own aliases.
  No behavior depends on them; removal would break no production path.
  Trigger to revisit: a future body reads one of them.
- 32, 40: `_concrete_order_columns`, `_relay_max_results_from_info` ->
  consumers (re-export shims off `optimizer/nested_planner.py`, read through
  `optimizer/walker.py` only by `tests/optimizer/test_walker.py`).
- 33-39: `_connection_window_slice_from_arguments`,
  `_extend_only_projection`, `_keyset_window_slice_from_arguments`,
  `_order_entry_field_name`, `_project_scalar_only_window`,
  `_relation_connection_to_attr`, `_relation_connection_to_attr_for_key` ->
  file-local dead re-exports. No reader through this module; production and
  test importers use `optimizer/nested_planner.py` directly (stated in the
  module header). Trigger to revisit: a future body or oracle reads one
  through the walker.
- 41-77: 37 `FunctionDef` members, every one assigned below. No
  `AsyncFunctionDef`, no `ClassDef` in the target.

Family assignment of the 37 definitions (Worker-2-local family names; file
item owes no production edit, so candidates route to holding families):

- F-W2-DRIVE (walker-drive surface, 5):
  `walker.py::plan_optimizations`, `walker.py::_walk_selections`,
  `walker.py::plan_relation`, `walker.py::_dispatch_single_relation`,
  `walker.py::_plan_connection_relation`.
- F-W2-PROJ (projection rules, 6): `walker.py::_enable_only_for_operation`,
  `walker.py::_plan_select_relation`, `walker.py::_plan_prefetch_relation`,
  `walker.py::_record_relation_access`,
  `walker.py::_ensure_connector_only_fields`,
  `walker.py::_selected_scalar_names`.
- F-W2-HINT (hint dispatch, 2): `walker.py::_apply_hint`,
  `walker.py::_prefetch_hint_for_path`.
- F-W2-ALIAS (alias merging, 8): `walker.py::_merge_aliased_selections`,
  `walker.py::_record_response_key_arguments`,
  `walker.py::_normalized_alias_payload`,
  `walker.py::_response_key_arguments_conflict`,
  `walker.py::_aliased_arguments_diverge`,
  `walker.py::_selection_runtime_prefixes`,
  `walker.py::_merge_runtime_prefixes`, `walker.py::_resolver_identities_for`.
- F-W2-CHILD (prefetch-child building, 5):
  `walker.py::_build_child_queryset`,
  `walker.py::_build_prefetch_child_queryset`,
  `walker.py::_build_prefetch_child_queryset_from_base`,
  `walker.py::_absorb_child_plan`,
  `walker.py::_target_has_custom_get_queryset`.
- F-W2-RESOLVE (name/field resolution, 8):
  `walker.py::_schema_name_converter`,
  `walker.py::_graphql_names_by_python_name`,
  `walker.py::_field_by_graphql_name`,
  `walker.py::_resolve_selection_target`, `walker.py::_resolve_field_map`,
  `walker.py::_resolve_relation_target`,
  `walker.py::_resolve_optimizer_hints`,
  `walker.py::_has_custom_id_resolver`.
- F-W2-KEYS (path-key ledgers, 3):
  `walker.py::_record_path_resolver_keys`,
  `walker.py::_record_prefetch_path_keys`,
  `walker.py::_record_select_path_keys`.
- 5 + 6 + 2 + 8 + 5 + 8 + 3 = 37. Nothing unassigned.

Rejections of Worker-2 naming (sites considered, kept separate):

- R-W2-A (alias vs owner): the 24-28 aliases stay consumers of
  `optimizer/selections.py`; the walker must not own fragment/directive/
  response-key semantics. Contract difference: selections.py serves two
  populations (AST + converted) while the walker serves one; merging would
  couple the walker to the extension's cache-key vocabulary.
  Trigger: selections.py changes a primitive's contract -> aliases follow.
- R-W2-B (hint validation vs hint dispatch): `optimizer/hints.py::OptimizerHint`
  owns shape + construction-time rejection; `walker.py::_apply_hint` owns
  plan-time effect. The dispatch priority order is documentation-only because
  `__post_init__` already rejects every conflict the order would arbitrate.
  Contract difference: build-time configuration error vs plan-time directive.
  Trigger: a new hint shape whose plan-time branches genuinely collide ->
  arbitration would become load-bearing and the two sites would be one rule.
- R-W2-C (routed candidate, not decided): `types/resolvers.py::_field_meta_for_resolver`
  vs `walker.py::_resolve_field_map` share one stated policy (prefer the
  canonical definition-backed metadata, fall back when unreachable; the
  walker docstring says "Keep the policy in sync"). Posited change "new
  fallback metadata source" moves both sites (definition count 2), but the
  call sites differ (resolver-time single field vs plan-time whole map).
  Routed to holding family F-W2-RESOLVE for phase 2; no consolidation
  demanded by this file item either way.
- R-W2-D (seed vocabularies): `utils/querysets.py::base_queryset`
  (model-keyed) vs `utils/querysets.py::initial_queryset` (type-keyed) are
  two documented questions, not one rule twice; the walker uses the former
  for relation-target children. Trigger: a caller seeds a relation child
  through the registered type -> the seed answers a different question and
  the distinction collapses.
- R-W2-E (connection structural names): model-field GraphQL names
  (`walker.py::_graphql_names_by_python_name`) vs connection structural
  names (`optimizer/selections.py::connection_field_names`) are disjoint
  vocabularies with different owners. Trigger: a model field literally named
  `edges`/`pageInfo` collides -> one resolution must win and the split ends.

### Matrix (discharged per axis; searches run)

Searches run (all `--include="*.py"` over the package unless noted):
S1 `plan_optimizations` references; S2 `_walk_selections` references;
S3 `plan_relation` references; S4 converted-selection primitives
(`included_field_selections`, `should_include`, `is_fragment`,
`response_key`, `named_children`, `node_children_with_runtime_prefix`,
`with_runtime_prefix`, `connection_node_children`); S5 projection writers
(`.only(`, `only_fields`, `select_related`, `prefetch_related` in the
walker); S6 prefetch-child alias bytes (`Prefetch(`, `to_attr`,
`instance_accessor`, `lookup_path`, `prefetch_to`, `prefetch_through` in the
walker); S7 HEAD-vs-worktree blob fingerprint loop over all inspected files;
S8 D1 witness grep over `HEAD:optimizer/walker.py`; S9 policy grep over
`HEAD:utils/querysets.py`; S10 oracle surface (`tests/optimizer/test_walker.py`
import block + selected bodies; `tests/optimizer/` listing;
`examples/fakeshop/test_query/` listing).

1. Cross-flavor policy mirroring: discharged. The walker-drive surface is:
   sole production caller `optimizer/extension.py::_get_or_build_plan` (via
   `optimizer/extension.py::apply_to`, reached by the middleware
   `optimizer/extension.py::_optimize` and by
   `optimizer/extension.py::apply_connection_optimization` for connection
   fields and the mutation re-fetch); the override seam
   `optimizer/extension.py::plan_relation` delegating to
   `optimizer/walker.py::plan_relation`; the nested delegate
   `optimizer/nested_planner.py::plan_connection_relation` receiving walker
   callables (hints/target/identities/child-builders) as parameters.
   Who else walks converted selections: `optimizer/nested_planner.py` (node
   children via the shared `optimizer/selections.py::connection_node_children`)
   and `connection.py` count detection
   (`optimizer/selections.py::direct_child_selected`) — both compose the
   selections owner by name; neither re-implements traversal. The extension
   AST seam operates on graphql-core AST nodes (distinct population, same
   selections owner). No sibling flavor (filters/orders/mutations/forms)
   walks selections. No second converted-selection walk found.
2. Sync/async twins: discharged by instrument — zero `AsyncFunctionDef` in
   the target. The walker is sync-only; async execution is adapted around it
   (`optimizer/extension.py::_optimize` async wrapper,
   `utils/querysets.py::apply_type_visibility_sync` raising `SyncMisuseError`
   for async-only hooks with the documented `relation_shapes = list`
   recourse). `connection.py`'s two colored bodies are a separate,
   principle-5-justified decision outside this file item. No twin in scope.
3. Derived rather than repeated knowledge: discharged with one routed
   candidate. One field-map derivation (`walker.py::_resolve_field_map`,
   R-W2-C records the documented sync with the resolver-side reader); one
   relation-target resolution threaded as an `(origin, definition)` pair
   (`walker.py::_resolve_relation_target`, spent by the `get_queryset`
   downgrade, the child visibility model, and the cursor vocabulary without
   re-reads); one lossy-name forward resolver
   (`walker.py::_field_by_graphql_name`, reused by
   `walker.py::_selected_scalar_names`); one key grammar
   (`optimizer/plans.py::resolver_key`, composed by walker, resolvers, and
   connection). Seed-model question split is R-W2-D (rejected).
4. Inverse / round-trip pairs: discharged. `Prefetch` lookup paths are read
   through `optimizer/plans.py::_lookup_path` (single owner of the
   `prefetch_to` private contract); window `to_attr` grammar is owned by
   `optimizer/nested_planner.py::relation_connection_to_attr` (walker holds
   consumer aliases only); alias-payload normalization is owned by
   `walker.py::_normalized_alias_payload` (single comparator for the
   divergence selector and the same-key conflict detector). No second half
   found elsewhere.
5. Contracts restated in another medium: discharged. Oracles assert
   `OptimizationPlan` outputs (tuples), not owner internals:
   `tests/optimizer/test_walker.py` drives `walker.py::plan_optimizations`
   and asserts `select_related` / `prefetch_related` / `only_fields` /
   `fk_id_elisions` / `planned_resolver_keys` (bodies read for the elision
   and FK-column oracles below; G2-gate oracle names recorded below).
   Observation (not a defect, routed to F-W2-RESOLVE): the test module
   imports walker private aliases (`_should_include`, `_is_fragment`,
   `_concrete_order_columns`, `_relay_max_results_from_info`,
   `_plan_connection_relation`, …) — oracle-by-alias pins re-export names,
   so dropping a dead alias breaks a test without any behavior change.
   Trigger: alias removal -> oracle update with no production movement.
   Walker docstrings are projections, not definitions.
6. Enforcement by omission: discharged with one routed question. Verified
   present on both related sites: `plan.cacheable = False` is set for
   custom-`get_queryset` children (`walker.py::_plan_prefetch_relation`)
   and for consumer-`Prefetch` hints (`walker.py::_apply_hint`); the G2 gate
   is consulted by every projection writer P1-P7 below (single derivation,
   all writers threaded). Consumer-assigned relations are left unplanned
   without a hint on the list path; whether the nested-connection delegate
   enforces the same consumer-assigned rule was not established from the
   phase-1 reads (the delegate checks `hint_is_skip`; no consumer-assigned
   read was confirmed there) — routed as a question to holding family
   F-W2-HINT with trigger "a consumer-assigned relation exposed only as a
   synthesized connection is planned windowed" (not a defect: no contract
   source establishing the rule covers connections, no reaching input
   executed).

### Definition counts per posited change (rules found)

- R-W2-DRIVE (one selection-tree walk produces the plan): posit "a new root
  selection wrapper (second root field node, mutation payload slot)". The
  walk body is 1 definition (`walker.py::_walk_selections`); the two
  extractors (`optimizer/extension.py::_root_child_selections`,
  `optimizer/extension.py::_connection_node_child_selections`) are consumers
  that shape its input. Count = 1. Owner chosen: the walker (GOAL criterion
  5 names the one walk; the extension owns input shaping).
- R-W2-PROJ (operation-gated projection): posit "a new operation kind that
  must suppress column masks". Only `walker.py::_enable_only_for_operation`
  moves (count = 1); posit "a new projection writer" — the writer must take
  the threaded `enable_only`, so the gate stays 1 definition with N
  consumer writers. Owner chosen: the walker (derives once in
  `walker.py::plan_optimizations`); `optimizer/nested_planner.py` owns its
  two direct-queryset writers (`_project_scalar_only_window`,
  `_extend_only_projection`) as consumers of the threaded bool.
- R-W2-HINT (direct hints vs nested SKIP/strategy — two dispatches, one
  rule each): posit "a new direct-hint shape" — `optimizer/hints.py`
  validation + `walker.py::_apply_hint` branch move (count = 2, distinct
  contracts per R-W2-B). Posit "a new nested strategy refusal" —
  `optimizer/nested_planner.py::plan_connection_relation` moves alone
  (count = 1); nested SKIP is read through the shared
  `optimizer/hints.py::hint_is_skip` predicate, not a second dispatch.
  Owners chosen: hints own shape/validation; walker owns direct effect;
  nested planner owns connection refusals and strategy selection.
- R-W2-ALIAS (conflict/diverge/identity): posit "a new per-alias comparison
  axis". Merge (`walker.py::_merge_aliased_selections`), per-key record
  (`walker.py::_record_response_key_arguments`), divergence
  (`walker.py::_aliased_arguments_diverge`), same-key conflict
  (`walker.py::_response_key_arguments_conflict`), normalization
  (`walker.py::_normalized_alias_payload`) all live in the walker
  (count = 1); the nested planner receives two of them as injected
  callables (consumer). Owner chosen: the walker.
- R-W2-CHILD (boundary / seal / alias — three facts, three owners): posit
  "a new child-seal fact" — `utils/querysets.py::_SealPolicy` moves alone
  (count = 1; walker passes the policy, `optimizer/nested_fetch.py` gate
  classifies the result). Boundary ownership (walker builds the base seed),
  seal (querysets policy), alias vocabulary (`utils/relations.py`)
  stay with their current owners. No move proposed.
- R-W2-RESOLVE (one name-resolution path): posit "another lossy camel
  boundary". `walker.py::_graphql_names_by_python_name` +
  `walker.py::_field_by_graphql_name` move together inside the walker
  (count = 1 rule); `walker.py::_selected_scalar_names` reuses the latter
  (consumer). Connection structural names stay with
  `optimizer/selections.py::connection_field_names` (R-W2-E). Owner chosen:
  the walker for model-field names.
- R-W2-KEYS (directive-to-metadata coupling): posit "a new directive kind
  needing strictness coupling". The three `_record_*_path_keys` writers move
  together in the walker (count = 1 family); `optimizer/plans.py::merge_from`
  merges the maps (owns merge mechanics, consumes the coupling schema).
  Owners chosen: walker writes, plans owns the container + merge.

### Projection-correctness hazards (each rule proved or filed)

A wrong `select_related` / `only` / `prefetch` decision causes N+1 or wrong
data (GOAL criterion 5). Each projection writer is proved safe by code order
read in phase 1; reaching wire input is given per rule. No projection defect
is filed.

- P1 scalar-leaf mask (`walker.py::_walk_selections` scalar branch): reaching
  input `{ items { name } }` over QUERY appends `only("name")`; under
  MUTATION/SUBSCRIPTION the append is skipped while the field stays
  accounted for. Wrong decision (mask on mutation) would defer-load inside
  resolvers. Proof: single `enable_only` derivation + unconditional
  `continue`. Oracle: `test_plan_collects_only_fields_for_selected_scalars`.
- P2 Relay custom-pk column (id branch): reaching input a Relay
  `DjangoType` with non-`id` pk attname selecting `{ id }` projects the real
  column (FK primary keys project the attname, e.g. `user_id`, never the
  relation name that would drag the row back). Proof: attname-or-name scan +
  gate conjunction read. Oracles:
  `test_plan_relay_id_projects_real_pk_attname_when_not_id`,
  `test_plan_relay_id_projects_attname_when_pk_is_relation`.
- P3 connector column before elision (`walker.py::_record_relation_access`
  vs `walker.py::_plan_select_relation` elision check): reaching input
  `{ items { category { id } } }` yields `only("category_id")` + elision and
  no JOIN. Proof: the access recorder runs BEFORE the elision check by
  documented, load-bearing order (moving it after would drop the FK column
  on the elided path and reintroduce the N+1). Oracle bodies READ:
  `test_plan_elides_forward_fk_when_child_selection_is_id_only`
  (`only_fields == ("name", "category_id")`, elision + planned keys set) and
  `test_plan_includes_fk_columns_in_only_fields`.
- P4 gate threading: reaching input any MUTATION whose resolver returns a
  queryset — root plan, generated `Prefetch` children, and scalar-only
  windows share the one bool derived in `walker.py::plan_optimizations`
  (both recursions forward it; the nested delegate receives it). Proof:
  derivation-once + three forward sites read. Oracle names recorded (bodies
  not individually verified in phase 1):
  `test_mutation_queryset_drops_only_keeps_select_prefetch`,
  `test_mutation_refetch_plan_drops_only_keeps_relations`,
  `test_mutation_to_one_relation_applies_no_only`,
  `test_mutation_scalar_only_connection_window_no_only`,
  `test_enable_only_defaults_enabled_without_info`,
  `test_mutation_id_only_relation_still_records_elision`.
- P5 child attach completeness
  (`walker.py::_ensure_connector_only_fields` via
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`):
  reaching input a `GenericRelation` list prefetch loads both `object_id`
  and `content_type_id`; masking either half deferred-refetches per row.
  Proof: single classify call, attach-key order, early return under a closed
  gate. Oracle tier: `tests/optimizer/test_join_taxonomy.py` + live
  `examples/fakeshop/test_query/` suites (individual bodies not verified in
  phase 1).
- P6 scalar-only window
  (`optimizer/nested_planner.py::_project_scalar_only_window`): reaching
  input `{ items { booksConnection { totalCount } } }` (no node children)
  restricts the window to pk + attach columns + concrete order columns.
  Proof: owner-named column sets read; gate short-circuits before touching
  the queryset. Oracle tier: nested-planner + live connection suites
  (individual bodies not verified in phase 1).
- P7 keyset cursor survival
  (`optimizer/nested_planner.py::_extend_only_projection`): reaching input a
  keyset page whose ordering columns are not selected keeps cursor minting
  off the lazy-load path under both `.only()` (union) and `.defer()`
  (clear-and-restore-minus-cursors) masks via the shared
  `optimizer/plans.py::deferred_loading_of` unpack. Oracle tier: keyset
  suites (individual bodies not verified in phase 1).
- P8 consumer-projection reconciliation (outside the walker, traced as the
  backstop): reaching input a consumer queryset carrying `.only("name")`
  with planned `select_related("category")` — `optimizer/plans.py::
  prune_unsupportable_select_related` drops the path AND its coupled keys
  (else `FieldError` or masked N+1); a consumer `Prefetch` that wins drops
  coupled keys via `prefetch_path_resolver_keys` in the extension reconcile
  step. Proof: prune + diff call sites read in
  `optimizer/extension.py::apply_to`. Oracle tier: `tests/optimizer/test_plans.py`
  + `tests/optimizer/test_extension.py` (individual bodies not verified in
  phase 1).

### Prefetch-child alias behavior (current bytes, open question NOT decided)

Recorded without deciding the open child-alias question:

- Seed: `walker.py::_build_child_queryset` builds
  `utils/querysets.py::base_queryset(field.related_model)` with no `using=`
  argument — an unpinned seed. The walker's documented position is that the
  child's effective alias entering the visibility hook is `None` on this
  path and the hook cannot pin one of its own.
- Seal: the hook runs only when the captured definition reports a custom
  `get_queryset`, through
  `utils/querysets.py::apply_type_visibility_sync` with
  `model=target_model` (the same definition's model) and
  `policy=_PREFETCH_CHILD_POLICY`, where HEAD bytes define
  `_PREFETCH_CHILD_POLICY = _SealPolicy(reject_sliced=False,
  require_shared_alias=True)`.
- Install: the generated child is installed as
  `Prefetch(lookup_path, queryset=child_queryset)` with no `to_attr`
  argument (Django default accessor attach); `lookup_path` is built with
  `utils/relations.py::instance_accessor`, not `field.name`.
- Consumer contrast in the same bytes: a hinted `Prefetch(..., to_attr=...)`
  on a non-consumer-assigned relation raises `ConfigurationError` loudly
  (`walker.py::_apply_hint`); only a consumer-assigned resolver may hint
  with `to_attr`.
- What is NOT stated here: whether the generated child should pin, carry,
  or inherit any alias. That decision is left entirely to phase 2.

### Defects (Worker 2): none filed

No defect meeting the AGENTS.md bar (contract row + feasible project shape
under supported public API + reaching wire/configuration input) was
established in phase 1. In particular: no projection-correctness defect
(P1-P8 proved above to the stated evidence level); no seal-policy defect
(D1 re-verified present, not re-litigated); the two routed items (R-W2-C
sync obligation; axis-5 oracle-by-alias imports; axis-6 nested
consumer-assigned question) are candidates/questions for holding families,
not defects. Tests were read as oracles only; no oracle was rewritten and
no production edit is owed by this file item.

### Freshness fingerprints

HEAD `bfaee91d`. `git hash-object` (worktree) vs `git show HEAD:<path> |
git hash-object --stdin` (HEAD bytes); dirty ones list both separately.
Attribute-vs-HEAD rule honored: behavior cited from a dirty file names the
side it was read from (phase-1 citations from dirty neighbors are
worktree-side unless marked HEAD).

| path | worktree blob | HEAD blob | state |
| --- | --- | --- | --- |
| `django_strawberry_framework/optimizer/walker.py` | `9b111ed938951a073a9226ccbcfacabc3af981e8` | `9b111ed938951a073a9226ccbcfacabc3af981e8` | clean |
| `django_strawberry_framework/optimizer/extension.py` | `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a` | `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a` | clean |
| `django_strawberry_framework/optimizer/plans.py` | `cce985319c8833f3660653327d3003f1f03655a5` | `cce985319c8833f3660653327d3003f1f03655a5` | clean |
| `django_strawberry_framework/optimizer/selections.py` | `a48f6172c6f04331740d1b110d742f17701ff846` | `a48f6172c6f04331740d1b110d742f17701ff846` | clean |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | `db1ea315d774f55e893c108c6e0bc995299a9fa2` | `db1ea315d774f55e893c108c6e0bc995299a9fa2` | clean |
| `django_strawberry_framework/optimizer/predicates.py` | `4e87c733f19b43b67c67d3b97d920013e164bb1f` | `4e87c733f19b43b67c67d3b97d920013e164bb1f` | clean |
| `django_strawberry_framework/utils/querysets.py` | `96618fba4eafb6a87e73414770014e3aee5b41ef` | `96618fba4eafb6a87e73414770014e3aee5b41ef` | clean (HEAD bytes read separately; never edited) |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `29ce5201877864b01079c849b92a1e812166affd` | `4d8d37a7f52cf94d2916f17db3a8a21393e28d57` | DIRTY (concurrent work; cited worktree-side) |
| `django_strawberry_framework/optimizer/nested_planner.py` | `e69dbf5f30aa4623a5aad93edfacdabb391d6601` | `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04` | DIRTY (concurrent work; cited worktree-side) |
| `django_strawberry_framework/optimizer/join_taxonomy.py` | `e1cbb3e327785de3b59ccafef6b463df52e06396` | `9b355a5090ce471e373849dd0a61da8f808e78b9` | DIRTY (concurrent work; cited worktree-side) |
| `django_strawberry_framework/optimizer/hints.py` | `8064af14930636d6b12a538a996603ccadfdb420` | `da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74` | DIRTY (concurrent work; cited worktree-side) |
| `django_strawberry_framework/types/converters.py` | `679c94481741291a015868dc1bfd3220aca1351d` | `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75` | DIRTY (concurrent work; cited worktree-side) |
| `django_strawberry_framework/connection.py` | `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` | `93e998f2c7ea1d7f18607a6e37e394466ac75ad4` | DIRTY (concurrent work; cited worktree-side) |

Reading-only inputs (no fingerprints required beyond content hashes):
`AGENTS.md` `e42247fa310bf7a85914d7efa7f177ee5307b860`,
`docs/dry/DRY.md` `e8151123ff7e129fe9881ec342231e9e1795148e`,
`docs/dry/worker-2.md` `4f089ea4a58d73295638e83abf8c612bf31487f8`,
`GOAL.md` `7dfbef5c784519d5f95311aaeb8c6766ee966b02`.
Applicable contracts: DRY.md principles 4 (derivation lifetime: the
`enable_only` bool derived once, threaded, never stored), 5 (shared walk
body with named relation adapters; sync-only, no twin), 7 (owners chosen
per rule above; dependency direction preserved — every consumer can import
its owner), 8 (observable behavior: query effects + strictness visibility,
not Boolean agreement; ordering constraints P3 recorded), 11 (dead
re-export aliases 29-31/33-39 noted as deletable only by their owning
change, not by this item); GOAL criterion 5 (one selection-tree walk) and
the trust-boundary bar for defects. Concurrent dirt above (including the
contested querysets-adjacent work, which fingerprinted clean) is preserved;
nothing was edited, staged, or committed.

PHASE-1-TRACE-RECORDED — `docs/dry/dry-file-optimizer__walker.md`


## Independent verification (Worker 2) — Phase 2 reconciliation

Verdict: `verified`. Zero production edits owed; no `proof:` / `gate:`
entries from this item. What follows reconciles every difference between
the phase-1 trace above and Worker 1's record explicitly. Citations are
`path::Symbol` symbol paths; hashes are `git hash-object` worktree blobs
unless marked HEAD.

### 1. Phase-1 integrity (stated)

The phase-1 trace was written without opening any other artifact section
and appended blind (worktree `9b111ed9…` target never touched; confirmed
still clean below). Its 7 families, 2 file-local groups, 5 rejections, 1
routed candidate, P1–P8, and child-alias bytes stand as written except
where this section explicitly corrects them (dead-alias label; routed
candidate now answered; freshness corrections). Nothing in phase 1 is
erased or rewritten.

### 2. Enumeration: 78 = 78 agreed; dead-alias dispute settled for Worker 1

Count agrees exactly: 1 docstring + 23 imports + 17 alias assigns + 37
defs; my 37 defs partition identically onto Worker 1's F-W1..F-W9 (see §3).
On the 17 aliases: Worker 1 is right about the LABEL and I correct mine.
DRY.md's backstop rule ("a row whose finding names a second site is a
family or a rejection, never `file-local`") forbids my `file-local` tag —
each alias names its owner in `optimizer/selections.py` or
`optimizer/nested_planner.py`. Substance was never in dispute (both traces:
no production reader through the walker for A29–A31/A33–A39; removal breaks
no production path) and stands. Resolution: A1..A8 join their selections
owner families as consumer rows (accepted); A9..A17 route to the holding
File `optimizer/nested_planner.py` item (accepted as legitimate routing,
not a placeholder — with the Worker-0 note below that the nested-planner
item must actually home them, else they reopen here). The
`_coerce_pagination_int` direct import is a consumer (one code read), agreed.

### 3. Family-grouping verdict: the 9-family split stands; my 7 dissolve

My 7 families map onto Worker 1's 9 without remainder, and the finer split
is accepted as more precise (each split carries a distinct contract and,
for F-W9, a distinct owner):

- my F-W2-DRIVE (5) + my F-W2-PROJ's `_plan_select_relation`,
  `_plan_prefetch_relation`, `_record_relation_access` → F-W1 (8).
- my F-W2-PROJ's `_enable_only_for_operation` → F-W2 (1); my
  `_selected_scalar_names` → F-W8 (1); my `_ensure_connector_only_fields`
  → F-W9 (consumer of the join-taxonomy descriptor).
- my F-W2-HINT (2) → F-W6 exactly. my F-W2-ALIAS (8) → F-W7 exactly.
- my F-W2-CHILD (5) → F-W3 (4) + `_target_has_custom_get_queryset` → F-W5
  (accepted: verdict-spending belongs with the definition source).
- my F-W2-RESOLVE (8) → F-W4 (4 naming) + F-W5 (4 definition-source):
  exact partition, accepted.
- my F-W2-KEYS (3) → consumers of the existing `resolver-key-grammar`
  family (accepted as the better home — grammar owned by
  `optimizer/plans.py::resolver_key`; R10 writer-vs-merger stands).

Coupling note for the family items (not a correction): C12's count-1
spans F-W1 (elision condition in `_plan_select_relation`) + F-W8 (scalar
inputs); R11's trigger (elision over a connection child) would move both
together. No plan-index correction: my 7 families were never added to the
index, so nothing stale exists; the 9 open rows (plan lines 480–488,
items 664–672, all present and open — verified by grep) stand unchanged.

### 4. Routed candidate answered: accept R4, withdraw holding-family routing

My R-W2-C (`types/resolvers.py::_field_meta_for_resolver` vs
`walker.py::_resolve_field_map`) is Worker 1's R4 with a superset
justification (different shapes/consumers; "keep in sync" prose is policy,
not shared body; shared trigger R1). I withdraw the F-W2-RESOLVE holding
route and accept R4 as a rejection. No consolidation is demanded by either
trace.

### 5. R-map (R1–R12 judged; R7 proved sound by fresh Worker-2 reads)

- R1 accept (spot-verified current worktree bytes:
  `types/base.py` builds `{snake_case(f.name): …}`; region outside the two
  concurrent hunks). R2 accept (spot-verified: `types/finalizer.py` builds
  `{python_name: graphql_name}` at finalization — reverse direction,
  opposite time). R3 accept (identical to my R-W2-E).
- R4 accept (see §4). R5 accept (new information beyond phase 1;
  consistent with my reads — both sites compose join-taxonomy by name).
  R6 accept (consistent with my consumer-seam treatment of the extension
  delegate).
- R7 judged SOUND — not absence-as-proof but a constructive gate chain,
  every link re-read by Worker 2 in current worktree bytes: (a) the nested
  branch triggers only on `relation_connections` entries
  (`optimizer/walker.py::_resolve_selection_target` + `_walk_selections`
  connection-first branch, phase-1 read); (b) the sole writer of that map
  is `types/finalizer.py::_synthesize_relation_connections` (init/assign/
  pop are the only production writes — full-package grep; declaration in
  `types/definition.py`; walker reads); (c) synthesis skips
  `consumer_authored_fields` under the implicit default
  (`types/finalizer.py::_synthesize_relation_connections` guard);
  (d) an explicit `relation_shapes` key naming a consumer-authored
  relation raises `ConfigurationError` at type creation
  (`types/base.py` validation); (e)
  `consumer_authored_fields ⊇ consumer_assigned_relation_fields`
  (`types/base.py` union, re-read). Post-finalization mutation of the
  private map is outside supported public API (GOAL.md trust boundary).
  My phase-1 nested-consumer-assigned question is therefore answered:
  unreachable via supported API; R7's trigger stands as the correct
  instrument. No defect.
- R8 accept (matches my C3 contrast: cache identity vs projection).
  R9 accept (matches my composition note). R10 accept (matches my
  R-W2-KEYS ownership split). R11 accept. R12 accept (re-verified current
  bytes: `types/definition.py::has_custom_id_resolver_for` delegates to
  `types/definition.py::origin_has_custom_id_resolver`, which the walker's
  fallback calls — the post-Worker-1 concurrent hardening touched only the
  `_normalize_pk_name` / `_resolves_id_off_pk` helpers below, never the
  two R12 halves).

### 6. I1–I5 judgment: none defect-shaped; no filing

- I1 clear (R7, §5). I2 clear (scope verified:
  `optimizer/walker.py` line-29 direct import vs the alias block —
  the "only two are read" sentence reads correctly on a strict parse).
- I3 clear (operative claim true of the whole subtree; wrapper-naming is
  not a contradiction — below the defect bar, agreed).
- I4 clear with a population qualifier Worker 1's text lacks: zero hits
  under package + tests source (re-grepped by Worker 2); the only `*.py`
  hits are other items' scratch probes under `docs/dry/temp-tests/`
  (querysets-item experiments, one of which asserts the current retired
  state). Substance stands; no source site exists.
- I5 clear (KANBAN-homed prose, agreed owned elsewhere).
No `(Worker 2)` defect is filed; `## Defects` is left untouched.

### 7. D1 + child-alias confirmation

Both traces confirm D1 present on identical bytes
(`optimizer/walker.py::_build_child_queryset` import + policy +
rationale); the target is still worktree-clean (`9b111ed9…`), so D1 stands
unreopened. Child-alias bytes: both traces recorded-without-deciding with
matching content (unpinned `base_queryset` seed, `_PREFETCH_CHILD_POLICY`
facts, accessor-lookup `Prefetch` without `to_attr`, loud consumer
`to_attr` refusal). Agreed: the question stays with the open
`child-queryset-alias-inheritance` family; nothing here pre-decides it.

### 8. Proof adequacy + `## Pending execution` (agreed empty)

Static-only challenges are adequate for this zero-edit file item: every
challenge is a structural claim over a closed, grep-enumerated population
(single derivation, threading sites, call-before-check ordering,
single-writer maps, synthesis-gate chain) with nothing ordering,
transactional, or async at issue — and no behavior change is proposed, so
no equivalence proof is owed. The execution backstop is the plan's final
gate (`uv run pytest`), which runs the fixed-count oracle tiers:
`tests/optimizer/test_walker.py` (175 tests — count re-verified — incl.
the G2-gate rows named in phase 1), `django_assert_num_queries` rows in
`tests/optimizer/test_extension.py`, and the live
`examples/fakeshop/test_query/` suites. Postgres/sharded cells belong to
the gate item per DRY.md (this item makes no alias/dialect decision
beyond the fenced child-alias bytes). No `proof:` / `gate:` entries from
this item — Worker 1's empty section is endorsed.

### 9. AGENTS.md prose on the empty diff + freshness corrections

Item-scoped diff: zero tracked edits (target `git diff HEAD --stat`
empty); the artifact is the only change (untracked, as at Worker-1
time). Hence: no ruff run owed (no `.py` touched), no tests owed
(zero-edit item), citations with raw numbers are permitted in
`docs/dry/dry-*.md` scratchpad artifacts per AGENTS.md, and no process
provenance is present (baselines/fingerprints are required DRY content).

Corrections to Worker 1's freshness section (recorded here; Worker 1's
text is preserved): `types/finalizer.py`, `types/base.py`, and
`types/resolvers.py` were already worktree-dirty at Worker-1 time, not
clean as labeled — but every region Worker 1 cited therein was verified
by Worker 2 to lie outside the concurrent hunks (finalizer hunk at
`finalize_django_types` globalid block; base hunks at
`_is_suppressed_relay_pk` + `_meta_optimizer_hints` hardening; resolvers
hunks at `run_in_one_sync_boundary` import + async branches), and the
load-bearing regions (R7 chain, R1, R4/R12 halves, C12 stub) were
re-read in current bytes above. Additionally `types/definition.py`
changed after Worker 1's read (worktree `01f78d93…` vs cited `fa6c4d33…`;
 hostile-guard hardening); F-W5/R12 claims were re-verified against the
new bytes in §5 and stand. No finding reopens: no cited region's content
changed under its claim. Re-hashed this phase (worktree == HEAD unless
paired): walker `9b111ed9…` clean; extension `49667a93…`, plans
`cce98531…`, selections `a48f6172…`, lateral `db1ea315…`, predicates
`4e87c733…`, querysets `96618fba…` (read-only, never edited), test_walker
`5bbd7a56…` (matches Worker 1) all clean; DIRTY (concurrent, preserved):
nested_fetch `29ce5201…` vs HEAD `4d8d37a7…`, nested_planner `e69dbf5f…`
vs HEAD `0ad8ff5d…`, join_taxonomy `e1cbb3e3…` vs HEAD `9b355a50…`, hints
`8064af14…` vs HEAD `da46ef89…`, converters `679c9448…` vs HEAD
`9ceb34af…`, connection `3c4d5dcb…` vs HEAD `93e998f2…`, finalizer
`f4266a15…` vs HEAD `77fd9a2d…`, base `bc8dcdb6…` vs HEAD `91c58747…`,
resolvers `5f4cce2b…` vs HEAD `f3341e6a…`, definition `01f78d93…` vs
HEAD `fa6c4d33…`. HEAD `bfaee91d…` (unchanged since phase 1). No scratch
was created by either worker for this item (no
`docs/dry/temp-tests/*walker*` entries; other items' scratch untouched).

### Exact plan rows for Worker 0 (no plan file edited — Worker 0 owns it)

- Tick: `- [ ] File optimizer/walker.py` → `- [x] File
  optimizer/walker.py` (`docs/dry/dry-file-optimizer__walker.md`,
  `Status: verified`, no pending execution).
- Index corrections: none. The 9 `dry-rule-*` rows stand open under
  `File optimizer/walker.py` with the F-W1↔F-W8 coupling note (§3) and the
  nested-planner-holding discharge note (§2) carried as family-item
  instructions, not index edits.
- Scratch paths to remove at closeout: none for this item.

PHASE-2-RECONCILIATION-RECORDED — `docs/dry/dry-file-optimizer__walker.md`

## Run-7 scoped re-trace (Worker 1, REOPENED item)

Run: 0.0.15 2026-09-29-7. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh, CONFIRMs or
REVISEs every prior finding, and assigns the drift's new shape. Zero
production edits; zero tracked files changed.

### Scope and fingerprints

Drift base `5ee86193` is an ancestor of HEAD `0c0537e2`
(`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`, verified at start and again
unmoved at finish). Three states fingerprinted (`git hash-object` /
`git rev-parse`; line counts from `git show` bytes):

- Prior stamp `bfaee91d:optimizer/walker.py` blob `9b111ed9` (1574 lines,
  78 `ast.Module.body` statements).
- Drift base `5ee86193:optimizer/walker.py` blob `e8d80005` (1622 lines,
  79 statements).
- HEAD `optimizer/walker.py` blob `75f9c6b6` (1729 lines, 85 statements).
- Worktree blob `d5759ef8` (1730 lines) vs HEAD: 7 hunks, 7+/6-, all
  truth-migration by content (attributed below); `ITEM_BASELINE=3d7016d8`
  resolves and its walker blob equals the worktree blob, so every hunk
  pre-dates the item. No `## Owned changes` ledger row names this file
  beyond D1, and D1 reads byte-identical at both states (see below).

Committed delta since the prior stamp is exactly four commits. Prior to
the drift base, `44712901` (the recorded drift: 10 `-U0` hunks, 54+/6-)
gives `optimizer/walker.py::_build_child_queryset` a `policy` parameter
defaulting to `_LIST_RELATION_CHILD_POLICY`, adds the
`optimizer/walker.py::_build_connection_child_queryset` seam spending
`_PREFETCH_CHILD_POLICY`, and repoints the nested-planner injection at
the seam. Drift-base to HEAD is exactly three commits (18 `-U0` hunks):
`e6a33c46` (module-docstring first line), `e1ba094e`
(`_resolve_field_map` docstring: both paths keyed by raw `f.name`), and
`53a50bf7` (memoized GraphQL-name table: `_ForwardNames`,
`_forward_names_memo`, `clear_forward_names` + bus registration,
`_build_forward_names`, `_forward_names`; `_field_by_graphql_name` and
`_resolve_selection_target` recomposed onto the table;
`_walk_selections` and `_selected_scalar_names` thread `definition`).

Method: every claim below reads HEAD bytes (`git show HEAD:` + AST over
that text via `/tmp/w7/enum.py` and `/tmp/w7/bodycmp.py`, pure probes, no
Django import, no SQL, no workspace), never the dirty tree. Regions
outside the drift hunks are AST-identical across all three states (34 of
42 def/class bodies hash-equal PRIOR/BASE/HEAD; the 8 that differ are
exactly the drift members). Oracles: `tests/optimizer/test_walker.py`
175 (prior) -> 177 (base) -> 180 (HEAD, blob `587cb9f4`).

Evidence fingerprints (`git rev-parse HEAD:`, short; MATCH = unchanged
across `5ee86193..HEAD`, STALE = drifted in range, each scoped below):

- Target `optimizer/walker.py` `75f9c6b6` STALE (the 3 commits above).
- MATCH (9): `optimizer/plans.py` `cce98531`,
  `optimizer/selections.py` `a48f6172`,
  `optimizer/nested_planner.py` `b4dfd4a6`,
  `optimizer/nested_fetch.py` `4d8d37a7`,
  `optimizer/join_taxonomy.py` `9b355a50`, `optimizer/hints.py`
  `da46ef89`, `utils/typing.py` `de6309f6`, `connection.py` `4894f90f`,
  `types/definition.py` `fa6c4d33`.
- STALE (10): `optimizer/extension.py` `e0e53a8e` (delegate :1577,
  entry :1358, reconcile :1278/:1282, cache-key op read :1534, all
  re-read); `optimizer/field_meta.py` `18ea719a` (one docstring hunk);
  `utils/querysets.py` `3616927d` (verified run 7; F2 + F8 cited below);
  `utils/relations.py` `8dbc3fe6` (docstring-only; verified run 7);
  `utils/strings.py` `991f7dad` (verified run 7; lossy boundaries
  intact, docstring names the walker fallback);
  `registry.py` `81bd561c` (one docstring hunk; get/get_definition/clear
  identical); `types/base.py` `dda91365` (field-map build :637, union
  :730, stage-2 raise, all re-read); `types/finalizer.py` `de34ae2a`
  (skip :683, surface names :230, synthesis order :1048 before flip
  :1147, all re-read); `types/resolvers.py` `72d62dc4` (origin hunk in
  `_make_relation_resolver` only; cited readers outside it);
  `tests/optimizer/test_walker.py` `587cb9f4` (+3 memo oracles incl. the
  `registry.clear()`-empties-memo pin at :575). Any change reopens.

### Enumeration at HEAD bytes

Instrument: `ast.parse` over `git show HEAD:` text, counting
`ast.Module.body` — **85 top-level statements** (prior 78 + exactly 7,
zero removals, zero renames): 1 module docstring + 23 imports + 17 alias
assigns + 1 class + 41 defs + 1 annotation (`_forward_names_memo`) + 1
call (`register_subsystem_clear`). The 7 additions: index 62
`_build_connection_child_queryset` (recorded drift, after
`_build_child_queryset`); index 50 `_ForwardNames`, 51
`_forward_names_memo`, 52 `clear_forward_names`, 53 the bus
registration, 54 `_build_forward_names`, 55 `_forward_names` (one
contiguous block after `_graphql_names_by_python_name`). Import deltas
(`NamedTuple`, `register_subsystem_clear`) are vocabulary, not rules.

Homes: `_build_connection_child_queryset` joins REVISEd F-W3;
`_ForwardNames`, `_build_forward_names`, `_forward_names`,
`_forward_names_memo`, `clear_forward_names` join REVISEd F-W4, with the
bus-registration half carried as a file-local convergence row onto
verified `subsystem-clear-lifecycle` (see `## Index rows for Worker-0`).
Every other member keeps its prior home; the twelve rejections keep
theirs except R1 (REVISEd). Zero file-local (unchanged rule: every
member has a second site).

### Worktree-dirt attribution (all 7 hunks, by content)

All concurrent-external (no ledger row; all pre-date the item via
`ITEM_BASELINE`), all truth-migration, all behavior-preserving on every
feasible project shape (`utils/truth.py` is untracked concurrent work,
read here only to judge equivalence):

- H1 (`@@ -15,0 +16`, +1): `from ..utils import truth` import.
- H2 (`plan_relation` logger): `target_type.__name__` ->
  `truth.name(target_type)`. Same string for every real class; on the
  `target_type=None` corner the worktree names `NoneType` where HEAD
  would raise `AttributeError` inside the debug call — strictly more
  robust. No supported-API input establishing that corner was found (the
  walk pairs origin+definition from one answer), so this stays an
  observation, not a defect.
- H3 (`_graphql_names_by_python_name`): three-arg `getattr` ->
  `truth.static_attr` (default `None`). Same answer for real classes
  and for `None`; metaclass-hook answers no longer consulted, which is
  the migration's stated point.
- H4 (`_walk_selections` Relay-id branch): `type_cls is not None and
  issubclass(type_cls, relay.Node)` -> `truth.is_subclass(type_cls,
  relay.Node)`. Same verdict; `False` for non-classes either way.
- H5-H7 (`_apply_hint`, three sites): `type_cls.__name__` ->
  `truth.name(type_cls)` in two error strings and one `type_name=`
  pass-through. Same strings; the function's own comment establishes
  `type_cls` is not `None` on this path.

### D1 re-verification (not re-litigated)

The ledger's D1 content (import `_PREFETCH_CHILD_POLICY`;
`_build_child_queryset` seal policy + docstring, from File
`utils/querysets.py`) reads byte-identical at HEAD and worktree: the
extracted regions (import block, `policy` default, unrouted seed,
shared-alias rationale + `policy=policy` call, full
`_build_connection_child_queryset` seam) hash `3ab15f00` at both states
(modulo the +1 import shift). No owned hunk in the HEAD->worktree diff.
D1-A (import :18) / D1-B (policy spend :525/:602/:630 + rationale
:529-603) / D1-C (zero `_UNRECOMPOSED_CHILD_POLICY` hits in tracked HEAD
`*.py`) all CONFIRM. The seal-policy facts now live across the builder
default + the seam (recorded drift), which the verified File
`utils/querysets.py` run-7 F8 re-pinned independently
(`require_shared_alias=True` in both policies; default :525, seed :562,
`policy=policy` :602, seam :607/:630, wired :1726, plain-list default
:1141 — every pin matches this trace). D1 stands unreopened.

### CONFIRM verdicts (families)

- F-W1 `walker-drive-surface` (owner `optimizer/walker.py`): the eight
  drive members keep their contract. `_walk_selections` differs only by
  one comment reword + the `definition=definition` pass-through;
  `_plan_connection_relation` differs only by the F-W3-owned injection
  repoint; the other six are AST-identical. Consumers re-pinned: the
  extension delegate stays thin (`optimizer/extension.py::plan_relation`
  :1577, same args, no branch), the entry still calls
  `plan_optimizations` (:1358), and the nested planner still accepts all
  eight injected callables
  (`optimizer/nested_planner.py::plan_connection_relation` :1048).
  Record note: the prior "ten-callable" phrasing miscounts — eight
  `Callable` params observed (the ten counts the non-callable args);
  contract unaffected. C1/C12 re-run: count 1 each. CONFIRM.
- F-W2 `operation-gated-projection` (owner
  `optimizer/walker.py::_enable_only_for_operation`): derivation
  AST-identical; root + both recursions + delegation forward the one
  bool (re-pinned :167-179, :1009-1017, :1178-1186, :1719); the nested
  self-consult lives in MATCH `nested_planner.py`. C3 re-run: count 1;
  the R8 contrast still holds (see below). CONFIRM.
- F-W5 `relation-target-definition-source` (owner
  `optimizer/walker.py`): `_resolve_field_map` differs by docstring
  only (the R1-facing prose); the other four members are AST-identical.
  C8/C10 re-run: count 1 each; C9 re-runs 1 with the revised reading
  (re-keying the fallback moves one site; the registration build is a
  different population — selected vs all fields). Retirement trigger
  still open (fallback intact :464-470). CONFIRM.
- F-W6 `optimizer-hint-dispatch` (owner
  `optimizer/walker.py::_apply_hint`): both members AST-identical;
  shape owner MATCH `hints.py`; nested SKIP/strategy arms in MATCH
  `nested_planner.py`. C6: same intentional window-vs-direct split.
  CONFIRM.
- F-W7 `aliased-selection-merge` (owner `optimizer/walker.py`): all
  eight members AST-identical. C4/C5 re-run: count 1 each (grammar +
  merge owners MATCH/composed; nested planner receives two injected
  callables). The `_optimizer_runtime_prefixes` note for the family item
  stands. CONFIRM.
- F-W8 `scalar-projection-and-fk-elision` (owner
  `optimizer/walker.py`): `_plan_select_relation` AST-identical; the
  before-elision recorder order intact (:985 before :993);
  `_selected_scalar_names` differs only by threading `definition`
  (unpack :1401 + pass :1438); sole production caller re-verified by
  package grep (def :1384 + the one call :997); the column consumer
  `types/resolvers.py::_build_fk_id_stub` sits outside that file's
  origin hunk. C12 re-run: count 1. CONFIRM.
- F-W9 `prefetch-attach-column-projection` (owner
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`):
  `_ensure_connector_only_fields` AST-identical; owner + sibling
  consumer both in MATCH files. C7 re-run: count 1. The undispatched
  family item's boundary is unchanged. CONFIRM.

### CONFIRM verdicts (rejections R2-R12, investigated-clear I1-I5)

- R2 accept (re-pinned): forward request-time resolution vs
  `types/finalizer.py::_field_surface_names` (`{python_name:
  graphql_name}` :230, finalization-time). Opposite directions,
  opposite times. Trigger untriggered.
- R3 accept: `_schema_name_converter` AST-identical;
  `connection_field_names` and its shared owner
  `utils/typing.py::schema_config_from_info` both in MATCH files.
  Trigger untriggered.
- R4 accept: `_resolve_field_map` body identical (whole-map,
  plan-time); `types/resolvers.py::_field_meta_for_resolver` outside
  that file's origin hunk; "keep in sync" prose intact (:459-462).
  Trigger (shared with R1) untriggered.
- R5 accept: `_record_relation_access` AST-identical; both compose
  join-taxonomy by name in MATCH files. Trigger untriggered.
- R6 accept: extension delegate thin (:1577, no branch). No trigger.
- R7 accept (re-proved at HEAD, every link re-read): (a) the nested
  branch triggers only on `relation_connections` (connection-first
  preserved in the recomposed resolver); (b) the sole writer is
  `_synthesize_relation_connections` (both `_record_relation_connection`
  call sites inside synthesis); (c) synthesis skips
  `consumer_authored_fields` under the implicit default (:683, Decision
  7 comment intact); (d) the explicit key raises at type creation
  (stage-2 `_validate_relation_shape_targets` consumer-authored arm in
  `types/base.py`); (e) the union still covers the guard population
  (`types/base.py` :730-734). Post-finalization map mutation runs only
  from `registry.clear()` teardown, which drops the definitions too.
  Trigger untriggered.
- R8 accept (re-pinned): projection gate vs cache identity; the
  extension still reads `info.operation` directly (:1534) for a
  different rule. No trigger.
- R9 accept: merge-after-flatten order intact (:722). No trigger.
- R10 accept: triple writers AST-identical; `merge_from` in MATCH
  `plans.py`; no third writer (package grep: only the plans merge arm
  + the walker triple). Trigger untriggered.
- R11 accept: `_selected_scalar_names` still composes
  `_field_by_graphql_name` by name (now via the table); the
  connection-form absence stays constructional. Trigger untriggered.
- R12 accept: `_has_custom_id_resolver` AST-identical; both halves +
  the free function in MATCH `definition.py`. Trigger untriggered.
- I1 clear (R7 re-proof above). I2 clear (`_coerce_pagination_int`
  import :31 + single read :1636; docstring scope still strict-correct).
  I3 clear (wrapper-naming docstring untouched; operative claim true of
  the subtree). I4 clear (zero tracked-HEAD `*.py` hits, re-grepped).
  I5 clear (KANBAN-homed prose, still owned elsewhere).

Worker-2 P1-P8 re-pinned at HEAD bytes (P1 :813-824; P2 :790-812; P3
order :985/:993; P4 threading :167-179/:1009-1017/:1178-1186/:1719;
P5-P7 in MATCH files; P8 reconcile :1278/:1282 re-read): no projection
defect; the phase-1 proofs stand with shifted pins. The oracle-by-alias
observation stands (test imports of walker privates re-verified) as an
observation, not a defect.

### REVISE verdicts

- F-W3 `prefetch-child-build-seam` (REVISE: one builder, two
  call-site-chosen seals; owner unchanged). Revised contract: the
  queryset-boundary abstraction answers TWO child seals from one
  builder — the plain-list default (`policy` parameter defaulting to
  `_LIST_RELATION_CHILD_POLICY`) and the nested-connection seam
  (`_build_connection_child_queryset` spending `_PREFETCH_CHILD_POLICY`
  at the one call site whose gate premise holds). Members:
  `_build_child_queryset`, `_build_connection_child_queryset`,
  `_build_prefetch_child_queryset` (takes the default :1141),
  `_build_prefetch_child_queryset_from_base`, `_absorb_child_plan`.
  Consumer: the nested planner via injection (repointed :1726). Seal
  POLICY stays owned by `sealed-execution-queryset` (verified
  querysets run-7 F2: 6-field record, byte-identical flags); alias
  BEHAVIOR stays with open `child-queryset-alias-inheritance`. C2/C8
  re-run: count 1 each. New challenge C13: a third child path needing
  a third seal adds one call-site argument (+ the policy record only
  if new flags are needed) — count 1 + record. Lifetime unchanged:
  plan-local pairs absorbed before return, cacheability poisoned,
  never stored.
- F-W4 `selection-target-resolution` (REVISE: memoized connection+field
  table; owner unchanged). Revised contract: forward GraphQL-name
  resolution across BOTH namespaces from one built table —
  `_build_forward_names` maps each connection's and field's GraphQL
  name to its target with first-declaration-wins (`setdefault`,
  declaration order), `_resolve_selection_target` answers connections
  before fields from that table after the exact-reversal fast path,
  and `_field_by_graphql_name` reads the fields half. Members:
  `_resolve_selection_target`, `_field_by_graphql_name` (signature
  `graphql_names` -> `definition`), `_graphql_names_by_python_name`,
  `_schema_name_converter`, `_ForwardNames`, `_build_forward_names`,
  `_forward_names`, `_forward_names_memo`, `clear_forward_names`.
  Equivalence: the old inline connection loop (first match wins,
  authoritative-name-or-camel) and the old linear field scan equal the
  two `setdefault` loops over the same iterations in the same order,
  with the same connection-before-field precedence — restructure +
  memoization, no behavior change (the commit's "plan shapes are
  unchanged" verified structurally; the three new oracles pin shapes +
  build counts + the clear). Lifetime (principle 4): owner the walker;
  validity key `(type_cls, id(converter))` with the converter held
  strongly by the value and the type by the key; publish point
  `_forward_names` on finalized+converter calls only; insert-only,
  never mutated in place (readers `.get`); invalidated by
  `registry.clear()` through the bus (`owner="optimizer.forward_names"`);
  uncacheable calls build fresh. Premise chain verified: synthesis
  :1048 runs before the finalized flip :1147; synthesis skips
  finalized types; `field_map` is write-once (zero post-creation
  writers package-wide); `relation_connections` post-flip mutation
  runs only from clear()-ordered teardown (teardowns before the
  subsystem fan-out), which also drops the definitions. C11 re-run:
  a digit-boundary change moves the table build once — count 1. New
  challenge C14: a validity change (e.g. key by definition) moves
  `_forward_names` once — count 1. R2/R3 separations stand (above).
- R1 (REVISE: key grammar converged; rejection stands on
  population+time). `fix(types)` re-keyed the registration build to
  raw `f.name` (`types/base.py` :637), identical to the fallback
  (`optimizer/walker.py` :469, same `FieldMeta.from_django_field`
  values). The contract difference is now: Meta-selected fields at
  registration time vs all model fields at plan time for unregistered
  models. Consolidation would need registration knowledge (the Meta
  selection) inside the fallback that exists precisely where that
  knowledge is absent — still a rejection. Same trigger
  (registry-coverage gate; fallback intact).

### Matrix re-discharge (all six axes, at HEAD bytes)

1. Cross-flavor: no second walk (single `_walk_selections`; nested
   node-children compose MATCH `selections.py`); extension delegate +
   entry re-pinned; custom-qs verdict consumers unchanged (resolvers
   reader outside the origin hunk; finalizer shape read :681
   re-verified). Discharged.
2. Sync/async: zero `async def`/`await` (re-grepped); the
   `SyncMisuseError` recourse prose intact (:547-554); the runner
   split still lives in verified `utils/querysets.py`. Discharged.
3. Derived knowledge: (a) R1 REVISEd above; (b) R2 CONFIRM; (c) R3
   CONFIRM. Discharged.
4. Round-trip: `_prefetch_hint_for_path` AST-identical with no inverse
   (MATCH planner adds none); key parity prose identical (:640-656);
   writers-vs-merger per R10. Discharged.
5. Other media: oracles 180 (every prior pin kept; +2 recorded-drift
   shape tests, +3 memo tests pinning shapes, per-converter answers,
   finalization gating, and the clear); oracle-by-alias imports
   re-verified (observation, not defect); spec/GLOSSARY/KANBAN
   projections move with unchanged bodies. Discharged.
6. Omission sweep: (a) `consumer_assigned` — R7 re-proved, unreachable
   not absent; (b) `cacheable` poisoning — all four sites re-pinned
   (direct :1059-1060, hint :1285, nested in MATCH planner,
   `_absorb_child_plan` identical); (c) `enable_only` — P4 threading
   re-pinned. No omission. Discharged.

Challenges C1-C12 re-run (counts: C1 1, C2 1, C3 1, C4 1, C5 1, C6
intentional split, C7 1, C8 1, C9 1 revised reading, C10 1, C11 1 via
the table build, C12 1) plus new C13/C14 (1 each): all
static-reviewed — structural claims over closed, grep-enumerated
populations with no behavior change proposed, so no equivalence proof
is owed.

### Defects

None filed. The H2 logger hardening (worktree names `NoneType` where
HEAD would raise on a `None` target with a custom-qs definition) is
recorded under hunk attribution as an observation: no supported-API
input reaching that corner was established, so it stays below the
defect bar, and the worktree side is concurrent hunt-owned work in any
case.

### Pending execution

None. No `proof:` entries (every challenge `static-reviewed`; nothing
ordering, transactional, or async is at issue, and the child-alias
behavior question stays fenced to its open family). No `gate:` entries.
`uv run pytest` not run (no pytest after edits; zero source edits made
in any case). The execution backstop is the plan's final gate (180
walker oracles + the live suites).

### Judgment

Zero-edit file item, ready for verification. The drift adds one seam
member (F-W3 REVISEd), one memoized name-table block (F-W4 REVISEd),
and converges the field-map key grammar (R1 REVISEd); everything else
CONFIRMs at HEAD bytes with re-pinned cites. The memo's bus row
converges lawfully onto verified `subsystem-clear-lifecycle`. D1 stands
unreopened and byte-identical across the worktree. No new family, no
defect, no execution owed.

## Index rows for Worker-0

New row (exact text; file-local convergence, mirrors the extension
doc-key row):

- `forward-name-memo-clear-row` —
  `django_strawberry_framework/optimizer/walker.py::clear_forward_names`
  + bus registration (`owner="optimizer.forward_names"`, declaration
  here; lawful convergence onto verified `subsystem-clear-lifecycle`
  as a drift-new full-clear member) —
  `django_strawberry_framework/optimizer/walker.py` — File
  `optimizer/walker.py` — file-local.

Revised rows (exact replacement text; no prior rows exist for these —
transcribe as new with the revised wording):

- `prefetch-child-build-seam` —
  `django_strawberry_framework/optimizer/walker.py::_build_child_queryset`
  (+ `_build_connection_child_queryset` seam,
  `_build_prefetch_child_queryset`,
  `_build_prefetch_child_queryset_from_base`, `_absorb_child_plan`;
  one builder, two call-site-chosen seals: plain-list default
  `_LIST_RELATION_CHILD_POLICY`, nested-connection
  `_PREFETCH_CHILD_POLICY`) —
  `django_strawberry_framework/optimizer/walker.py`,
  `django_strawberry_framework/optimizer/nested_planner.py` — Family
  `prefetch-child-build-seam` — open.
- `selection-target-resolution` —
  `django_strawberry_framework/optimizer/walker.py::_resolve_selection_target`
  (+ `_field_by_graphql_name`, `_graphql_names_by_python_name`,
  `_schema_name_converter`, `_ForwardNames`, `_build_forward_names`,
  `_forward_names`, `_forward_names_memo`, `clear_forward_names`;
  memoized per finalized type+converter, cleared on the subsystem bus)
  — `django_strawberry_framework/optimizer/walker.py` — Family
  `selection-target-resolution` — open.
- `walker-fallback-vs-registration-field-map` (rejection recorded here;
  REVISEd — same raw-`f.name` key grammar both paths since `e1ba094e`;
  difference is population+time: Meta-selected at registration vs all
  model fields at plan time for unregistered models; trigger:
  registry-coverage gate) —
  `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`,
  `django_strawberry_framework/types/base.py` — File
  `optimizer/walker.py` — rejected.

CONFIRM notes (no new text; transcribe from the prior artifact where a
row is still missing): F-W1, F-W2, F-W5, F-W6, F-W7, F-W8 unchanged in
contract (re-pinned cites above); F-W9 unchanged (open family item
stands); R2-R12 unchanged in verdict (R2/R8 re-pinned); I1-I5 stay
clear; D1 stands. No `## Owned changes` rows (zero-edit re-trace).

## Independent verification (Worker-2) — run-7 re-trace

Verdict: `verified`. Zero production edits owed; no `proof:` / `gate:`
entries from this item. Every REVISE, the new row, all three revised
row texts, and every index bullet below were judged fresh at HEAD
bytes (`git show HEAD:` + AST probes under `/tmp`, never the dirty
tree); W1's conclusions were re-derived, not inherited. Citations are
`path::Symbol` symbol paths; `path:NN` pins name HEAD bytes and are
confined to this per-cycle artifact (allowed). Prior sections above
are preserved intact; the one correction (§9) is recorded here only.

### 1. Fingerprints and drift shape (all re-derived, all match)

- HEAD `0c0537e2` verified at start and unmoved at finish. Drift base
  `5ee86193` is an ancestor of HEAD.
- Target: prior `9b111ed9` (1574 lines) / base `e8d80005` (1622) /
  HEAD `75f9c6b6` (1729) / worktree `d5759ef8` (1730); HEAD->worktree
  is exactly 7 hunks, 7+/6-. `ITEM_BASELINE=3d7016d8` resolves and
  its walker blob equals the worktree blob, so every hunk pre-dates
  the item.
- Committed delta: exactly 4 commits — `44712901` before the base
  (10 `-U0` hunks, 54+/6-, re-read in full: `policy` parameter +
  seam + injection repoint + comment restatement) and exactly 3
  base-to-HEAD (`e6a33c46` docstring line, `e1ba094e` field-map
  docstring, `53a50bf7` memo block; 18 `-U0` hunks total, recounted).
  `53a50bf7` touches only the walker + its tests.
- All 19 evidence blobs re-hashed and match W1 short-for-short: 9
  MATCH byte-identical base-to-HEAD, 10 STALE genuinely drifted.
  Oracles 175 -> 177 -> 180 by `def test_` count; HEAD test blob
  `587cb9f4`.
- Ledger: exactly one `## Owned changes` row names the walker (D1);
  nothing else to attribute.

### 2. Enumeration at HEAD bytes (re-derived, agrees)

Own `ast.Module.body` census over HEAD bytes: **85 statements** = 1
module docstring + 23 imports + 17 aliases + 1 class + 41 defs + 1
annotation + 1 bus-registration call. Delta vs prior is exactly +7
with zero removals and zero renames: the seam plus the six-member
memo block (class, memo, clear, registration, build, read). Homes
agreed: seam to F-W3, memo block to F-W4 with the bus-registration
half carried as the file-local convergence row; every other member
keeps its prior home. Zero file-local stands.

### 3. F-W3 REVISE — endorsed (one builder, two seals)

Re-read at HEAD: `policy` default `:525`, unpinned seed `:562`,
`policy=policy` spend `:602`, seam `:607-630` spending
`_PREFETCH_CHILD_POLICY`, plain-list call `:1141` taking the default,
nested injection repointed `:1726`. Seal record re-read:
`_PREFETCH_CHILD_POLICY` admits the slice, `_LIST_RELATION_CHILD_POLICY`
refuses it, both `require_shared_alias=True` — differ on
`reject_sliced` alone, matching the one-gate premise split in the
commit message. Consumers, C2/C8 (count 1 each), new C13 (third seal
= one call-site argument + the record only if new flags are needed),
and the unchanged lifetime all hold as written. The querysets run-7
F8 cross-pins match every walker-side site. Owner unchanged, correct.

### 4. F-W4 REVISE — endorsed (memoized table, same answers)

Equivalence re-derived by reading both bodies, not by trusting the
commit message: the prior inline connection loop (first match wins,
authoritative-name-or-camel over `relation_connections.items()`)
and the prior linear field scan equal the two `setdefault` loops in
`_build_forward_names` over the same iterations in the same order,
with the same connection-before-field precedence and the same
exact-reversal fast path ahead of both. The memoized path builds
connections from `definition.relation_connections`, which is the
same object the one production call site passes
(`getattr(definition, ...) or {}`); `_field_by_graphql_name` builds
the identical table under the same `(type_cls, id(converter))` key,
so both readers share one entry. Lifetime chain re-verified link by
link at HEAD: synthesis `:1048` runs before the finalized flip
`:1147`; synthesis skips finalized types; `field_map` is built once
and never written post-creation (reads only, package-wide);
`relation_connections` post-flip mutation runs solely from the
teardown closure replayed by `registry.clear()` before the
definitions drop and before the subsystem fan-out; the memo holds
its converter strongly so the `id` key cannot be reused; uncacheable
calls build fresh. C11/C14 (count 1 each) hold; R2/R3 separations
stand. The three memo oracles pin shapes, per-converter answers,
finalization gating, and the clear (`registry.clear()` empties the
memo). Owner unchanged, correct.

### 5. R1 REVISE — endorsed (grammar converged, rejection re-grounded)

`types/base.py` `:637` now keys the registration build by raw
`f.name` (the `snake_case` application removed by `e1ba094e`,
re-read in the commit diff); the walker fallback `:469` keys by raw
`f.name` with the same `FieldMeta.from_django_field` values. The
remaining difference is population+time exactly as restated:
Meta-selected fields (`_select_fields` over the fields/exclude spec)
at registration time vs all `model._meta.get_fields()` at plan time
for unregistered models. The impossibility argument holds:
consolidation would need the Meta selection inside the fallback
that exists precisely where that knowledge is absent. Same trigger
(registry-coverage gate), fallback intact. Rejection stands.

### 6. New row — endorsed verbatim (lawful convergence)

`clear_forward_names` + `register_subsystem_clear(...,
owner="optimizer.forward_names")` is exactly the verified
`subsystem-clear-lifecycle` C1 adapter shape (one declaration line
+ one one-liner `.clear()` callback, default full-clear flag, bus
unchanged), and the subsystem's own clear test pins its row as C1/P6
require. Prior-to-HEAD bus-token delta is exactly the two drift-new
sites (extension doc-key + this row); no census oracle names the
newcomer, so no family text moves. The row text mirrors the
extension doc-key row already transcribed in the plan. File-local
home correct: the declaration lives here, the lifecycle lives with
the verified family.

### 7. Revised row texts — endorsed verbatim (3/3)

- `prefetch-child-build-seam`: members complete (builder + seam +
  both prefetch builders + absorb), both seals named on the correct
  paths, files and open-family home correct.
- `selection-target-resolution`: all nine members named (four prior
  + `_ForwardNames`, `_build_forward_names`, `_forward_names`,
  `_forward_names_memo`, `clear_forward_names`), memo/clear gloss
  accurate, home correct.
- `walker-fallback-vs-registration-field-map`: revised grammar note,
  population+time difference, and trigger all match §5; rejected
  home correct.
- CONFIRM notes: no transcription owed; the no-new-text claim is
  accurate and the standing rows need no edit.

### 8. CONFIRM sweep, hunk attribution, D1, defects (all endorsed)

- Own docstring-stripped body comparison confirms every CONFIRM
  member: F-W2/F-W6/all-eight F-W7/F-W9 bodies identical across all
  three states; F-W1 differs only by the F-W3-owned repoint +
  definition pass-through; F-W5 differs by docstring only; F-W8
  differs only by definition threading with sole production caller
  re-verified (def + one call) and the before-elision order intact.
  The eight-`Callable` correction to the prior "ten-callable"
  phrasing is accurate (eight observed; contract unaffected).
- R2 re-pinned (reverse map, opposite time), R7 re-proved end to end
  (sole writer's both call sites inside synthesis, `:683` skip with
  Decision 7 comment, stage-2 type-creation raise, `:730-734` union
  covering the guard population, post-flip mutation only from
  clear-ordered teardown), R8/R9/I2/P3/P4/P8 pins re-read at HEAD.
  R3/R4/R5/R6/R10/R11/R12 hold via AST-identity plus MATCH owners;
  no third key-map writer exists. Matrix axes 1-6 re-discharged;
  policy spenders outside the seal owner are exactly the default +
  the seam; memo symbols are read outside the walker only by the
  oracle pin. No drift-new duplication found.
- All 7 worktree hunks re-attributed by content: truth-migration,
  concurrent-external, behavior-preserving on every feasible project
  shape. H2 (`truth.name` in the `plan_relation` logger) hardens the
  `target_type=None` + custom-qs-definition corner (names `NoneType`
  where HEAD raises `AttributeError` inside the debug call); no
  supported-API input reaches it — the walk pairs origin+definition
  from one answer and the public delegate defaults the definition to
  `None`, which short-circuits the verdict before the logger — so
  the observation disposition (below the defect bar) is correct.
  (Read note: H4's `truth.is_subclass` uses real-MRO semantics, so a
  hypothetical virtual `relay.Node` subclass would diverge from
  `issubclass`; no supported shape produces one. Hunt-owned work in
  any case; equivalence on feasible shapes agreed.)
- D1 stands unreopened: the HEAD->worktree diff touches none of the
  D1 regions (byte-identical modulo the +1 import shift, verified by
  diff exclusion rather than W1's extraction script, same result);
  D1-A/B/C pins and zero tracked-HEAD `_UNRECOMPOSED_CHILD_POLICY`
  hits re-verified. No owned hunk in the diff.
- Zero-defect call endorsed. `## Pending execution` correctly empty:
  all challenges are structural claims over closed, grep-enumerated
  populations with no behavior change proposed; the backstop is the
  plan's final gate (180 walker oracles + live suites).
  Sharded/pg cells stay with the gate item (no alias/dialect
  decision here beyond the fenced child-alias bytes).

### 9. One correction (recorded here; W1's text preserved)

W1's Method parenthetical ("34 of 42 def/class bodies hash-equal
PRIOR/BASE/HEAD; the 8 that differ are exactly the drift members")
mislabels a BASE/HEAD comparison as a three-state one. Re-derived
values: 31 of 42 docstring-stripped bodies are identical across all
three states (30 of 42 raw, adding the `_resolve_field_map`
docstring hunk); the 11 that differ are the five drift-new members
plus `_build_child_queryset`, `_plan_connection_relation`,
`_field_by_graphql_name`, `_resolve_selection_target`,
`_selected_scalar_names`, `_walk_selections`. The 34/8 split holds
for BASE/HEAD only. Substance is unaffected — every one of the 11
lies inside the four drift commits, and the three gap members (the
`44712901` trio) are fully covered by the F-W3 REVISE and the F-W1
CONFIRM — so no verdict, trigger, row text, or index instruction
moves. No W1 re-pass needed for this alone.

### Exact plan rows for Worker-0 (no plan file edited)

- Tick: `- [ ] File optimizer/walker.py` -> `- [x] File
  optimizer/walker.py` (`docs/dry/dry-file-optimizer__walker.md`,
  `Status: verified`, no pending execution).
- Transcribe verbatim from `## Index rows for Worker-0`: the new
  `forward-name-memo-clear-row` plus the three revised rows
  (`prefetch-child-build-seam`, `selection-target-resolution`,
  `walker-fallback-vs-registration-field-map`). CONFIRM notes
  transcribe nothing. No `## Owned changes` rows (zero-edit
  re-trace). Carry the F-W1/F-W8 coupling note and the §9 count
  correction as record, not as index edits.
- Scratch paths to remove at closeout: none for this item (probes
  under `/tmp` only).

RUN-7-VERIFY-RECORDED — `docs/dry/dry-file-optimizer__walker.md`

### Nothing-else-changed

Pre-edit artifact 1712 lines / 102853 B; the item-scoped delta is
exactly the `Status:` line swap plus this EOF append. No production
edit, no test edit, no plan edit, no new tracked file, zero `.py`
touched, so no ruff run owed. Appended prose checked against
AGENTS.md: `path::Symbol` cites, `path:NN` confined to this
per-cycle artifact (allowed), no process provenance beyond the
DRY.md-mandated role labels, no cross-file links (no scaffold
owed). No `(Worker-2)` defect (none found). Concurrent dirt left
alone; no commit.

## Run-8 scoped re-trace (Worker 1, s12)

Run: 0.0.15 2026-09-30-8. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh, CONFIRMs or
REVISEs every run-7 finding (23 CONFIRM + 3 REVISE baseline), homes the
drift's new shape, and confirms the s11/s10 carried evidence from this
file's side. Zero production edits; zero tracked files changed.

### Scope and fingerprints

Drift base `0c0537e2` is an ancestor of HEAD `83998e08`
(`83998e08d48c911199527ed0411ab8041805c8b5`, verified at start and again
unmoved at finish). Three states fingerprinted (`git hash-object` /
`git rev-parse`; line counts from `git show` bytes):

- Drift base `0c0537e2:optimizer/walker.py` blob `75f9c6b6` (1729 lines,
  85 `ast.Module.body` statements; == run-7 HEAD).
- HEAD `optimizer/walker.py` blob `bdd9c2f1` (1827 lines, 88 statements).
- Worktree blob `9130aceb` (1826 lines, 89 statements) vs HEAD: 8 hunks,
  9+/10-, all truth-migration by content (attributed below);
  `ITEM_BASELINE=1ca0e747` resolves and its walker blob equals the
  worktree blob, so every hunk pre-dates the item.
- Pre-merge `9aaaad5d:optimizer/walker.py` blob `d5759ef8` (1730 lines,
  86 statements; == run-7 worktree: truth-adopted, pre-drift).

Committed delta since the drift base is exactly four commits
(`git log --oneline 0c0537e2..HEAD -- <target>`): `5c5e32c5`
(behavior-bearing: 44+/1-, combined `get_queryset` served as its pk set;
adds `optimizer/walker.py::_hint_prefetch_over_pk_set` + the
`_apply_hint` reroute + `_COMBINED_WHAT` /
`_pk_membership_query_or_defect` imports) and three typing-only
rewrites: `999a1aab` (68+/24-), `b20277fe` (111+/100-, incl. the
`_relay_max_results_from_info` rebind to
`utils/connections.py::relay_max_results_from_info`), `fef11e64`
(1+/1-, one annotation). Total drift `0c0537e2..HEAD`: 213+/115-.

Method: every claim below reads HEAD bytes (`git show HEAD:` + AST over
that text via `/tmp/probe_*_s12.py`, pure probes, no Django import, no
SQL), never the dirty tree; worktree-state claims read the disposable
copy at `dry/walker-retrace-s12/consolidate` (runs
`dry-20260930T163413-475558`, `dry-20260930T163422-db453c`: copy census
1826 lines / 89 top-level / zero async / hint fn present; all 8
worktree truth sites + the strict forward + the absorb seam confirmed
in-copy). Stripped-body comparison (annotations, `cast`, docstrings,
`AnnAssign` normalized) across drift-base vs HEAD: 41 of 42 def/class
bodies identical; the delta is exactly ADDED `_hint_prefetch_over_pk_set`
plus the `_apply_hint` reroute (isolated by stripped AST diff: the
`_prefetch_hint_for_path` first arg gains the
`_hint_prefetch_over_pk_set(...)` wrap, nothing else). All other hunks
are annotation/cast/comment-only (`typing.cast` is runtime identity;
no runtime `Any` use remains — the two `Any` hits are prose). Oracles:
`tests/optimizer/test_walker.py` 180 (base, blob `587cb9f4`) -> 181
(HEAD, blob `3f5e19a5`, worktree-clean): -2 last-zero tests (s10's
`dbf0a870` removal) + 3 combined tests (rewrite `:1630`, refusal
`:1680`, combined-child `:5757`). Live tier:
`examples/fakeshop/test_query/test_combined_visibility_api.py`
(`1648cc48`) pins the served-rows behavior end to end.

Evidence fingerprints (`git rev-parse HEAD:`, short): every neighbor
is STALE vs the drift base (the typing commits touched all 19 files),
so each cited region was re-derived by stripped-body comparison rather
than inherited: target `bdd9c2f1`; `optimizer/plans.py` `fdc4b1b0`
(s11 verified); `optimizer/selections.py` `4127d08a`;
`optimizer/nested_planner.py` `3637dc3a` (s10 verified);
`optimizer/nested_fetch.py` `304e2f3e`; `optimizer/join_taxonomy.py`
`6274d9a0`; `optimizer/hints.py` `f6776564`; `utils/typing.py`
`1ce032f1`; `connection.py` `3d6dd424`; `types/definition.py`
`5bf257c3`; `optimizer/extension.py` `6a6465f2`; `optimizer/field_meta.py`
`efb763d1`; `utils/querysets.py` `392e50d0` (s16 queued);
`utils/relations.py` `72e7ff08`; `utils/strings.py` `a326167d`;
`registry.py` `9d2021eb`; `types/base.py` `d160998a`;
`types/finalizer.py` `cb2dde6b`; `types/resolvers.py` `574e9768`;
`utils/connections.py` `735aa454` (worktree-clean). Worktree (short):
walker `9130aceb`, plans `3e005158`, extension `dd9ad009`,
nested_planner `e5daffc5`, querysets `cfc773ba`, connection `64b85d0e`,
base `909c25a7`, finalizer `7d354e77`, resolvers `7a953c53`,
definition `936ab86f`, selections `3237edec`, relations `6b80acac`,
strings `f5ce0784`, typing `5083bdb3`, registry `57fa18ae`, hints
`ee68ae03`, join_taxonomy `fa4974c3`, field_meta `bf70debe`,
nested_fetch `b74539d1`, test_walker `3f5e19a5` (clean). All citations
below are HEAD-side; worktree dirt outside the target is concurrent and
left alone. Any fingerprint change reopens.

### Enumeration at HEAD bytes

Instrument: `ast.parse` over `git show HEAD:` text, counting
`ast.Module.body` — **88 top-level statements** (base 85 + exactly 3,
zero removals, zero renames): 2 Expr (docstring + bus-registration
call) + 24 imports + 1 `TYPE_CHECKING` If + 17 alias assigns + 1 class
+ 42 defs + 1 AnnAssign (`_forward_names_memo`). The 3 additions: the
`relay_max_results_from_info` import (`:16`), the `TYPE_CHECKING` block,
and `_hint_prefetch_over_pk_set` (`:1398`, after `_apply_hint`).
Module-level alias delta vs base: only `_relay_max_results_from_info`
(`:115`) rebinds from `_nested_planner._relay_max_results_from_info` to
the direct `utils/connections.py` import — the same function object
(`optimizer/nested_planner.py:45` HEAD is itself
`from ..utils.connections import relay_max_results_from_info as
_relay_max_results_from_info`), so behavior-preserving; s10 recorded
this shape from the planner side. The alias-block docstring (`:97-105`)
keeps its operative claims (which two are read through this module, by
whom; other seven unread) — see O1 for the one stale preamble word.

Homes: `_hint_prefetch_over_pk_set` joins REVISEd F-W6 (below); the
`TYPE_CHECKING` block and `relay_max_results_from_info` import are
vocabulary, not rules. Every other member keeps its run-7 home. Zero
file-local (unchanged rule: every member has a second site —
`_hint_prefetch_over_pk_set` is spent by `_apply_hint` and pinned by
two oracles). Zero `async def` / `await` (re-grepped on all three
states).

### Worktree-dirt attribution (all 8 hunks, by content)

All concurrent-external (no `## Owned changes` ledger row names this
file beyond committed D1; all pre-date the item via `ITEM_BASELINE`),
all truth-migration (`from ..utils import truth`, H1), all
behavior-preserving on every feasible project shape (`utils/truth.py`
is still untracked concurrent work, worktree `cc4bbe01`, read here only
to judge equivalence):

- H1 (`@@ -13,6 +13,7`, +1): the `truth` import.
- H2 (`plan_relation` logger): 3-line comment + `cast("type",
  target_type).__name__` -> `truth.name(target_type)`. Same string for
  every real class; on the `target_type=None` corner the worktree names
  `NoneType` where HEAD raises `AttributeError` inside the debug call —
  strictly more robust, still an observation (no supported-API input
  reaches it: the walk pairs origin+definition from one answer; run-7
  W2's delegate-defaults-`None` short-circuit re-verified at
  `optimizer/extension.py::plan_relation` `:1626-1643` HEAD).
- H3 (`_graphql_names_by_python_name`): three-arg `getattr` ->
  `truth.static_attr` (default `None`). Same answer for real classes;
  metaclass-hook answers no longer consulted (the migration's point).
- H4 (`_walk_selections` Relay-id branch): `type_cls is not None and
  issubclass(type_cls, relay.Node)` -> `truth.is_subclass(type_cls,
  relay.Node)`. Same verdict; `False` for non-classes either way
  (run-7 W2's virtual-subclass read note still stands; no supported
  shape produces one).
- H5-H7 (`_apply_hint`, three sites): `type_cls.__name__` ->
  `truth.name(type_cls)` in two error strings and the two `type_name=`
  pass-throughs (incl. the drift-new reroute call). Same strings; the
  function's own comment establishes `type_cls` is not `None` here.
- H8 (`_hint_prefetch_over_pk_set` refusal, drift-new function):
  `inner.model.__name__` -> `truth.name(inner.model)`. `inner` is a
  real queryset (guarded non-`None`), so `inner.model` is a real model
  class and the strings are identical.

### D1 re-verification (not re-litigated)

The ledger's D1 content (import `_PREFETCH_CHILD_POLICY`;
`_build_child_queryset` seal policy + docstring, from File
`utils/querysets.py`) reads intact at HEAD: D1-A import `:20`;
D1-B builder default `:556`, unpinned seed `:594`,
`policy=policy` spend `:635`, full rationale (`:557-633` docstring +
comments), seam `:640-664` spending `_PREFETCH_CHILD_POLICY`, wired
`:1824`; D1-C zero `_UNRECOMPOSED_CHILD_POLICY` hits in tracked HEAD
`*.py` (re-grepped). The seal record at HEAD
(`utils/querysets.py::_SealPolicy` `:2869-2874`: six fields incl.
`rewrite_combined=True` default) keeps the D1/F-W3 premise:
`_PREFETCH_CHILD_POLICY` (`reject_sliced=False`,
`require_shared_alias=True`) and `_LIST_RELATION_CHILD_POLICY`
(`require_shared_alias=True`) differ on `reject_sliced` alone
(`:2897`/`:2928`, same-axis comments re-read). No owned hunk in the
HEAD->worktree diff. D1 stands unreopened.

### Carried confirmations (s11 + s10, walker side)

- s11 `attached-prefetch-lookups-read` second spelling CONFIRMED:
  `optimizer/walker.py::_hint_prefetch_over_pk_set:1432` HEAD
  (`).prefetch_related(*inner._prefetch_related_lookups)`) is the
  strict forward of a guaranteed-present tuple (`inner` is a real
  `QuerySet`: non-`None` + `query.combinator` read just above, so the
  attribute exists; strict-read-raises is the honest spelling here).
  Count-2 C18 recounted from this side: package-wide `git grep` at HEAD
  finds exactly two live-attribute code reads —
  `optimizer/plans.py:572` (`_consumer_prefetch_lookups`, lenient
  `getattr(..., ()) or ()`) and walker `:1432` (strict); the rest are
  docstrings/comments/def-names. The failure-mode difference is real
  (lenient-silent vs strict-fails-loud) and the unify-vs-record question
  stays with the already-rowed family (plan line 1290; no new row owed
  here — `:1432` is recorded as this family's second spelling, and
  F-W6 below carries it as a composed read). Corrected exclusion
  verified: the seal snapshot-key read
  (`utils/querysets.py:3733`, `state.get("_prefetch_related_lookups")`)
  and clone-write (`:3806`,
  `sealed._prefetch_related_lookups = sealed_prefetch`) move under seal
  contracts (snapshot discipline, clone reproduction), not this
  family's read rule — the count-2 stands per the run-7 R-6
  separation precedent. The `:1630` oracle pins the forwarded tuple
  (`("entries",)`) and the served rows; the `:1680` oracle pins the
  plan-time refusal.
- s10 absorb-seam evidence CONFIRMED: `optimizer/walker.py::_absorb_child_plan`
  (`:1468-1479` HEAD) is still docstring + one
  `parent_plan.merge_metadata_from(child_plan)` call (stripped-identical
  to base); the planner's direct composition
  (`optimizer/nested_planner.py:1484`,
  `plan.merge_metadata_from(sub_plan)`) is intact, alongside the
  full-merge `:1461` (`plan.merge_from(strategy_plan)`, different
  rule). The R12 trigger (the seam gaining a step outside
  `merge_metadata_from`) is unmet; the import-direction constraint
  (walker-imports-planner) still forbids composing the seam from the
  planner. s10's F1 order-read note needs nothing from this file (the
  walker never calls `effective_connection_order`; the planner's
  `(cursor_field, query, model)` composition is s10/s11-verified).

### CONFIRM verdicts (families: 7 of run-7's 7 + both revised)

- F-W1 `walker-drive-surface`: all eight drive members stripped-identical
  across base/HEAD (the `_apply_hint` reroute is F-W6-owned and changes
  no drive contract). Consumers re-pinned: extension entry
  (`optimizer/extension.py:1403`), thin delegate
  (`optimizer/extension.py::plan_relation` `:1626-1643`, same args, no
  branch), nested signature
  (`optimizer/nested_planner.py::plan_connection_relation` `:1074`,
  still eight `Callable` params + `enable_only`, all spent at the
  delegation call `:1807-1826`) with atomic `merge_from` (`:1827`).
  C1/C12 re-run: count 1 each. CONFIRM.
- F-W2 `operation-gated-projection`: derivation stripped-identical;
  root (`:192`/`:203`) + both recursions (`:919`, `:942`) + both
  planners (`:1031`, `:1057`, `:1096`, `:1125`) + delegation (`:1817`)
  forward the one bool; the nested self-consult persists in s10-verified
  nested_planner. C3 re-run: count 1; R8 contrast re-pinned (extension
  `:1583` reads `info.operation` for cache identity). CONFIRM.
- F-W3 `prefetch-child-build-seam` (run-7 REVISEd contract): all five
  members stripped-identical; the seal record keeps the one-axis split
  (D1 section above); the runner still takes `model=` + `policy=`
  (`utils/querysets.py::apply_type_visibility_sync` impl `:4368-4377`
  HEAD; overloads added, call contract kept) and the combined rewrite
  is inherited by composition — exactly the `5c5e32c5` design, owned by
  `sealed-execution-queryset` (s16 queued), not restated here. C2/C8/C13
  re-run: count 1 each. CONFIRM.
- F-W4 `selection-target-resolution` (run-7 REVISEd contract): all nine
  members stripped-identical; lifetime chain re-pinned (synthesis
  `:633-843` before the finalized flip `:1167`, both in
  `types/finalizer.py`; synthesis-skip-finalized `:691`; `field_map`
  write-once — every `field_map[` hit package-wide is a read;
  `relation_connections` sole writer `:556` via the `:541` recorder,
  both call sites (`:766`, `:836`) inside synthesis; teardown closure
  `:587-630` replayed by `registry.clear()`; bus row `:328` intact).
  C11/C14 re-run: count 1 each. CONFIRM.
- F-W5 `relation-target-definition-source`: all five members
  stripped-identical. C8/C9/C10 re-run: count 1 each (C9 under the
  revised reading; registration build still raw `f.name` at
  `types/base.py:698`, fallback still raw `f.name` at walker `:500`).
  Retirement trigger still open. CONFIRM.
- F-W7 `aliased-selection-merge`: all eight members stripped-identical;
  `_coerce_pagination_int` still one direct import (`:34`) + one code
  read (`:1734`); nested planner still receives two injected callables.
  C4/C5 re-run: count 1 each. The `_optimizer_runtime_prefixes` note for
  the family item stands. CONFIRM.
- F-W8 `scalar-projection-and-fk-elision`: stripped-identical; the
  before-elision order intact (`:1026` before `:1035`); sole production
  caller re-verified by package grep (def `:1482` + the one call
  `:1038`; test hits are oracle pins); the column consumer
  (`types/resolvers.py::_build_fk_id_stub` `:131`, stripped-identical)
  still reads the projected column. C12 re-run: count 1. CONFIRM.
- F-W9 `prefetch-attach-column-projection`: `_ensure_connector_only_fields`
  stripped-identical; owner
  (`optimizer/join_taxonomy.py::classify_relation_join`,
  stripped-identical) + sibling consumer
  (`optimizer/nested_planner.py::_project_scalar_only_window`,
  stripped-identical) unchanged. C7 re-run: count 1. CONFIRM.

### CONFIRM verdicts (rejections R1-R12, investigated-clear I1-I5)

- R1 (run-7 REVISEd rejection): stands on population+time. The
  `_select_fields` base-vs-HEAD delta is typing-only (return annotation
  + one `cast`; the unknown-names raise predates the drift base).
  Registration (`types/base.py:698`) and fallback (walker `:500`) key by
  raw `f.name` with the same `FieldMeta.from_django_field` values; the
  Meta selection still cannot live in the fallback that exists where
  that knowledge is absent. Trigger untriggered.
- R2 accept (re-pinned: `types/finalizer.py::_field_surface_names`,
  stripped-identical; opposite directions/times). R3 accept
  (`_schema_name_converter` stripped-identical; `connection_field_names`
  + `utils/typing.py::schema_config_from_info` stripped-identical).
  R4 accept (`_resolve_field_map` stripped-identical;
  `types/resolvers.py::_field_meta_for_resolver` `:354`,
  stripped-identical; sync prose intact). R5 accept (both sites compose
  stripped-identical join-taxonomy). R6 accept (delegate `:1643`, no
  branch). R7 accept (re-proved end to end at HEAD: (a) connection-first
  intact in the stripped-identical resolver; (b) sole writer's both call
  sites (`:766`, `:836`) inside synthesis (`:633-843`); (c) skip `:702`;
  (d) type-creation raise `:1830-1831` in
  `types/base.py::_validate_relation_shape_targets`; (e) union
  `:792-796` covering the guard population; post-flip mutation only
  from clear-ordered teardown). R8 accept (re-pinned `:1583` vs the
  gate). R9 accept (merge-after-flatten intact). R10 accept (triple
  stripped-identical; `merge_from` stripped-identical; no third writer —
  `select_path_resolver_keys` hits are decl + merge arm + prune rebuild
  + the walker triple). R11 accept (composition via the table intact).
  R12 accept (`_has_custom_id_resolver` stripped-identical; halves +
  free function stripped-identical in MATCH-by-body `definition.py`).
  All triggers untriggered.
- I1 clear (R7 re-proof). I2 clear (import `:34` + single read `:1734`;
  docstring scope strict-correct). I3 clear (wrapper-naming docstring
  intact at `:724`). I4 clear (zero tracked-HEAD `*.py` hits,
  re-grepped). I5 clear (KANBAN-homed prose, still owned elsewhere).

Worker-2 P1-P8 re-pinned at HEAD bytes (P1 scalar branch `:850-865`;
P2 id branch `:821-849`; P3 order `:1026`/`:1035`; P4 threading
`:192`/`:203`/`:919`/`:942`/`:1817`; P5 attach via stripped-identical
descriptor read; P6/P7 in s10-verified nested_planner at stripped-identical
bodies; P8 reconcile `:1323`/`:1332` re-read, `diff_plan_for_queryset`
+ `prune_unsupportable_select_related` stripped-identical): no
projection defect. The oracle-by-alias observation stands (import block
`:25-42` + late pins `:2726`/`:3308`/`:3330` re-verified) as an
observation, not a defect.

### REVISE verdicts

- F-W6 `optimizer-hint-dispatch` (REVISE: combined-hint rewrite member;
  owner unchanged). Revised contract: the four configurable hint shapes
  + empty-hint fallthrough, with the `prefetch_obj` arm routing through
  `_hint_prefetch_over_pk_set` — a combined hinted queryset takes the
  same pk-set rewrite a sealed `get_queryset` result takes
  (`utils/querysets.py::_pk_membership_query_or_defect`, composed by
  name), keeping alias, routing hints and nested prefetches (strict
  forward `:1432`, the s11 second spelling carried as a composed read),
  while a combinator the pk set cannot represent
  (`union(all=True)`, annotated/extra/values branches, outer
  values/non-column ordering/slice) fails at plan time with the verbose
  combined `ConfigurationError`; any other `Prefetch` returns unchanged.
  Members: `_apply_hint`, `_hint_prefetch_over_pk_set`,
  `_prefetch_hint_for_path`. All other arms (SKIP, `force_select`,
  `force_prefetch`, fallthrough, `to_attr` refusal, cacheable mark, B8
  attribution) stripped-identical. Nested SKIP/strategy arms stay in
  s10-verified nested_planner (same intentional window-vs-direct split;
  C6 re-run). New challenge C15: change the combined-hint rewrite rule
  (e.g. a newly servable shape) → the querysets-owned
  `_pk_membership_query_or_defect` moves once; walker + every seal
  surface compose it → count 1. Trigger: a hint shape needing window
  semantics on the DIRECT path (or vice versa) re-opens the split —
  unchanged. Oracles: `:1630` (rewrite + alias + nested lookups +
  served rows), `:1680` (refusal text), plus the live combined suite.

### Matrix re-discharge (all six axes, at HEAD bytes)

1. Cross-flavor: no second walk (single `_walk_selections`,
   stripped-identical); extension delegate + entry re-pinned; custom-qs
   verdict consumers re-pinned (resolvers `_custom_visibility_type`
   `:381`/`:402` for UNPLANNED paths; finalizer shape read `:1395`;
   different populations, unchanged). Discharged.
2. Sync/async: zero `async def`/`await` on all three states; the
   `SyncMisuseError` recourse prose intact (`:578-585`); the runner
   split still lives in `utils/querysets.py`. Discharged.
3. Derived knowledge: (a) R1 stands (above); (b) R2 CONFIRM; (c) R3
   CONFIRM. Discharged.
4. Round-trip: `_prefetch_hint_for_path` stripped-identical with no
   inverse; key parity prose + writers-vs-merger per R10; the new
   `:1432` forward pairs with s11's lenient read under the already-rowed
   family (count-2, not a second rule). Discharged.
5. Other media: oracles 181 (every prior pin kept; -2 last-zero, +3
   combined pinning the drift's shapes + refusal + clear behavior);
   oracle-by-alias imports re-verified (observation, not defect);
   spec/GLOSSARY/KANBAN projections move with unchanged bodies.
   Discharged.
6. Omission sweep: (a) `consumer_assigned` — R7 re-proved, unreachable
   not absent; (b) `cacheable` poisoning — all four sites re-pinned
   (direct `:1101`, hint `:1337`, nested `:1292`, `_absorb_child_plan`
   stripped-identical); (c) `enable_only` — P4 threading re-pinned. No
   omission. Discharged.

Challenges C1-C14 re-run (C1 1, C2 1, C3 1, C4 1, C5 1, C6 intentional
split, C7 1, C8 1, C9 1 revised reading, C10 1, C11 1 via the table
build, C12 1, C13 1, C14 1) plus new C15 (1): all static-reviewed —
structural claims over closed, grep-enumerated populations with no
behavior change proposed, so no equivalence proof is owed. (C18 is
s11's count, recounted from this side under Carried confirmations.)

### Defects

None filed.

- O1 (observation, below the defect bar): the alias-block preamble
  ("the implementations live in `optimizer/nested_planner.py`", `:97`)
  is now imprecise for 1 of 9 names — `_relay_max_results_from_info`
  is defined in `utils/connections.py` (`:773`) and merely re-exported
  through nested_planner (`:45`, import-as). The block's operative
  claims (which two are read through this module, by `test_walker.py`;
  the other seven unread here, `connection.py`/`test_keyset_connection`
  reading from nested_planner directly) all still hold — verified by
  grep at HEAD — so this is stale-preamble prose, not a contract break:
  no contract row, no feasible project shape, no reaching input. A
  future touch of that comment should say eight live in nested_planner
  and one in `utils/connections.py`.
- The H2 logger hardening (worktree names `NoneType` where HEAD raises
  on a `None` target with a custom-qs definition) is recorded under
  hunk attribution as an observation, as in run-7: no supported-API
  input reaches it, and the worktree side is concurrent hunt-owned work.

### Pending execution

None. No `proof:` entries (every challenge `static-reviewed`; nothing
ordering, transactional, or async is at issue, and the child-alias
behavior question stays fenced to its open family). No `gate:` entries.
`uv run pytest` not run (no pytest after edits; zero source edits made
in any case). The execution backstop is the plan's final gate (181
walker oracles + the live suites, incl. the combined-visibility rows).

### Judgment

Zero-edit file item, ready for verification. The drift adds one hint-path
member (F-W6 REVISEd: combined-hint pk-set rewrite + plan-time refusal,
composing the querysets-owned rewrite, carrying s11's strict-forward
second spelling) and rebinds one alias to the same function object (O1
preamble note); everything else CONFIRMs at HEAD bytes with re-pinned
cites. D1 stands unreopened and intact across the worktree. No new
family (the `:1432` read belongs to s11's already-rowed
`attached-prefetch-lookups-read`), one revised row text below, no
defect, no execution owed.

## Index rows for Worker-0 (run-8 s12)

Revised row (exact replacement text; no prior row exists for this family —
transcribe as new with the revised wording):

- `optimizer-hint-dispatch` —
  `django_strawberry_framework/optimizer/walker.py::_apply_hint`
  (+ `_hint_prefetch_over_pk_set`, `_prefetch_hint_for_path`; four
  shapes + fallthrough; combined hint querysets rewritten to their pk
  set via `utils/querysets.py::_pk_membership_query_or_defect`,
  unservable shapes refused at plan time; `:1432` carries the
  `attached-prefetch-lookups-read` strict-forward second spelling as a
  composed read) —
  `django_strawberry_framework/optimizer/walker.py`,
  `django_strawberry_framework/utils/querysets.py`,
  `django_strawberry_framework/optimizer/nested_planner.py` (windowed
  SKIP/strategy arms, intentional split) — Family
  `optimizer-hint-dispatch` — open.

CONFIRM notes (no new text; transcribe from the prior artifact where a
row is still missing): F-W1, F-W2, F-W3, F-W4, F-W5, F-W7, F-W8 unchanged
in contract (re-pinned cites above); F-W9 unchanged (open family item
stands); R1-R12 unchanged in verdict (R1/R2/R7/R8 re-pinned); I1-I5 stay
clear; O1 is prose-only, no row; D1 stands. The s11
`attached-prefetch-lookups-read` row (plan line 1290) already names this
file's second spelling — no edit. No `## Owned changes` rows (zero-edit
re-trace).

## Run-8 verification (Worker 2)

Verdict: `verified`. Zero production edits owed; no `proof:` / `gate:`
entries from this item. Every verdict row (25 CONFIRM + 1 REVISE), the
revised row text, both carried confirmations, O1, D1, all 8 worktree
hunks, and all three fingerprints were re-derived expectation-first at
HEAD bytes with Worker-2-owned instruments (`/tmp/w2s12/` probes run
via `dry/walker-retrace-s12/verify`; `git show HEAD:` bytes plus the
disposable copy, never the dirty tree for state claims); W1's
conclusions were re-derived, not inherited. Citations are
`path::Symbol`; `path:NN` pins name HEAD bytes and are confined to
this per-cycle artifact (allowed). Prior sections above are preserved
intact; the three corrections (§9) are recorded here only.

### 1. Fingerprints and drift shape (all re-derived, all match)

- HEAD `83998e08` verified at start and unmoved at finish. Drift base
  `0c0537e2` is an ancestor of HEAD.
- Target: base `75f9c6b6` (1729 lines) / HEAD `bdd9c2f1` (1827) /
  worktree `9130aceb` (1826); HEAD->worktree is exactly 8 hunks,
  9+/10-. Pre-merge `9aaaad5d` walker blob `d5759ef8` (== run-7
  worktree). `ITEM_BASELINE=1ca0e747` resolves and its walker blob
  equals the worktree blob, so every hunk pre-dates the item.
- Committed delta: exactly 4 commits touching the target —
  `5c5e32c5` (44+/1-), `999a1aab` (68+/24-), `b20277fe`
  (111+/100-), `fef11e64` (1+/1-); net `0c0537e2..HEAD` 213+/115-.
- All 21 HEAD blobs re-hashed and match W1 short-for-short (target +
  19 neighbors + test_walker `3f5e19a5`); all 19 neighbors are STALE
  vs base (base shorts match the run-7 record); worktree shorts for
  all 19 match; `utils/connections.py` and `test_walker.py` are
  worktree-clean. Live suite blob `1648cc48`. `utils/truth.py` is
  untracked concurrent work (`cc4bbe01`), read only to judge hunk
  equivalence.
- Ledger: exactly one `## Owned changes` row names the walker (D1);
  nothing else to attribute.

### 2. Enumeration at HEAD bytes (re-derived, agrees)

Own `ast.Module.body` census: base 85 = 2 Expr + 23 ImportFrom + 17
Assign + 41 FunctionDef + 1 ClassDef + 1 AnnAssign; HEAD **88** = 2
Expr + 24 ImportFrom + 1 If + 17 Assign + 1 class + 42 defs + 1
AnnAssign; worktree 89 (the extra `truth` import). Delta vs base is
exactly +3 with zero removals and zero renames (member-name diff):
the `relay_max_results_from_info` import (`:16`), the
`TYPE_CHECKING` block (`:57`, imports + one `Protocol` —
typing-only by construction), and `_hint_prefetch_over_pk_set`
(`:1398`). Module-level diff holds nothing else: the querysets
import gains `_COMBINED_WHAT` + `_pk_membership_query_or_defect`
(the `5c5e32c5` behavior imports), `typing` swaps `Any` for
`TYPE_CHECKING` + `cast`, and `_relay_max_results_from_info`
(`:115`) rebinds to the direct import — the same function object
(`nested_planner.py:45` re-exports it from `utils/connections.py`,
defined `:773`), so behavior-preserving. No runtime `Any` use
(the three `\bAny\b` hits at `:379`/`:1413`/`:1618` are prose;
see §9). Zero `async def` / `await` on all three states (AST
census; `git grep` confirms no match). Homes agreed: new function
to F-W6, import + `TYPE_CHECKING` block are vocabulary. Zero
file-local stands.

### 3. Drift scoping (own stepwise stripped comparison)

Own normalizer (annotations, `cast`, docstrings stripped;
`AnnAssign` normalized; defaults/decorators kept) across the commit
chain: base -> `5c5e32c5` adds `_hint_prefetch_over_pk_set` and
reroutes `_apply_hint` (41 identical); `5c5e32c5` -> `999a1aab`,
-> `b20277fe`, -> `fef11e64`, -> HEAD are each 43/43
stripped-identical. The `_apply_hint` delta is exactly the
`_hint_prefetch_over_pk_set(...)` wrap as the first arg of
`_prefetch_hint_for_path`. So `5c5e32c5` is the one
behavior-bearing commit and the three typing commits are
typing-only on this target — derived, not inherited.

Neighbor drift (same instrument over all 19 pairs): every cited
member is stripped-identical except where W1 re-pins rather than
claims identity. Each differing member was characterized: typing
machinery (`@override`, base-class subscriptions, `cast`-alias
locals such as `excluded`/`model_meta`/`annotation_keys`,
`getattr` for duck-typed reads, Protocol/Enum shapes,
annotation narrowings) or s10/s11-owned connection behavior
(`last: 0` arm removal, order-composition shape) that no walker
member reads (verified by package grep per symbol). Nothing cited
by any walker row moved behaviorally.

### 4. F-W6 REVISE — endorsed (combined-hint rewrite member)

Read at HEAD bytes: `_apply_hint` `:1240` with the reroute
`:1315-1324`; `_hint_prefetch_over_pk_set` `:1398-1433`.
Non-combined input returns unchanged (`:1416-1418`); a combined
inner composes `utils/querysets.py::_pk_membership_query_or_defect`
(`:1419`, signature `(query, model)` matches the call); an
unservable shape raises the verbose plan-time `ConfigurationError`
(`:1420-1425`, `_COMBINED_WHAT.format(model=..., detail=...)`
matches the `:3973` template); the rewrite keeps model, alias
(`using=inner._db`), routing hints, and nested prefetches via the
strict `:1432` forward, preserving `prefetch_through` + `to_attr`
(`:1426-1433`). The refusal-shape parenthetical was spot-checked
against `_combined_lost_property` (`union(all=True)`, outer
non-column ordering/slice/values, branch
annotations/extra/values — all present; full ownership stays with
s16). All other arms stripped-identical. C15 holds: the rewrite
has exactly two production call sites (walker `:1419`, seal
`:3770`), so a rule change moves the querysets record once and
both compose it — count 1. Oracles read: `:1630` pins the rewrite
(combinator gone), alias (`_db`), forwarded tuple (`("entries",)`),
and served rows; `:1680` pins the exact refusal text; `:5757`
pins the combined child under both strategies. Owner unchanged,
correct.

Row text endorsed verbatim: three members complete and correct;
four-shapes-plus-fallthrough accurate (SKIP, `prefetch_obj`,
`force_select`, `force_prefetch`, empty fallthrough all read);
pk-set composition + plan-time refusal accurate; the `:1432`
carried-spelling clause accurate (see §5); file list correct
(walker + querysets + nested planner windowed arms, split
verified present via `hint_is_skip` `:1157` and strategy
selection); no prior row exists in the plan, so transcribe-as-new
is correct. The unchanged arm mechanics (validate-before-mutate,
`to_attr` refusal, cacheable mark, B8 attribution) rest in this
artifact's REVISE record, verified stripped-identical.

### 5. s11 carried confirmation — endorsed (strict forward, count-2)

`:1432` re-read: past the `:1417` guard `inner` is a real
`QuerySet` (`non-None` + `query.combinator` read), on which
`_prefetch_related_lookups` always exists — strict-read-raises is
the honest spelling. Count-2 recounted package-wide at HEAD: the
only live-attribute code reads are `plans.py:572` (lenient
`getattr(..., ()) or ()`, load-bearing for its `object`-typed
population) and walker `:1432` (strict); all other hits are
docstrings/comments/def-names. The `:3733`/`:3806` exclusion is
correct in kind (snapshot-dict string-key read + clone write
under seal contracts, not this family's read rule) and in pin.
The failure-mode difference is real and population-grounded.
Plan line 1290 already rows this file's second spelling — no new
row owed, agreed.

### 6. s10 carried confirmation — endorsed (absorb seam)

`_absorb_child_plan` (def `:1467`) is still docstring + one
`parent_plan.merge_metadata_from(child_plan)` call
(stripped-identical); planner side intact with full merge
`:1461` (`merge_from`, different rule) alongside direct
composition `:1484`. The R12 trigger (a seam step outside
`merge_metadata_from`) is unmet; the walker-imports-planner
direction still forbids composing the seam from the planner
(no walker import in the planner module). The walker never
mentions `effective_connection_order`; the planner composes it
from plans. Nothing needed from this file, agreed.

### 7. CONFIRM sweep (8 families + R1-R12 + I1-I5, all endorsed)

One instrument underpins every family CONFIRM: the §3 stripped
comparison proves each CONFIRM member identical base-to-HEAD
(F-W1's eight, F-W2's derivation, F-W3's five, F-W4's nine,
F-W5's five, F-W7's eight, F-W8's members, F-W9's consumer).
Re-pins re-read at HEAD bytes, all matching: F-W1 entry
`:1403`, thin delegate `:1626-1643` (single return, no branch
— R6), planner signature `:1074` (eight `Callable` + one
`enable_only`), delegation `:1807-1826` with atomic merge
`:1827`; F-W2 derivation `:192`, forwards `:203`/`:919`/`:942`/
`:1031`/`:1057`/`:1096`/`:1125`/`:1817`, R8 contrast `:1583`;
F-W3 seal split (see §8), runner overloads + impl `:4368-4377`
with `model=` + `policy=` kept, combined rewrite inherited
(neither child policy overrides the `rewrite_combined`
default); F-W4 synthesis call `:1068` before flip `:1167`,
skip-finalized `:691`, field-map write-once (every `field_map[`
hit package-wide is a read), sole writer `:556` via recorder
`:541` with both call sites (`:766`, `:836`) inside synthesis,
teardown `:587-630`, bus row `:328`; F-W5 registration `:698`
and fallback `:500` both raw `f.name` with identical values,
trigger open; F-W7 coerce import `:34` + single read `:1734`,
two injected callables on the verified signature; F-W8 order
`:1026` before `:1035`, sole production caller (def `:1482` +
one call `:1038`; test hits are oracle pins), stub `:131`
identical; F-W9 owner + sibling identical. R1 stands on
population+time (`_select_fields` delta is return annotation +
one `cast`, read raw; unknown-names raise intact in both
branches); R2 re-pinned (`:240`, opposite directions/times);
R3 via identical owners; R4 (`:354` identical, sync prose
`:493` intact); R5 via identical join-taxonomy; R7 re-proved
end to end (connection-first `:757` + resolver precedence,
sole-writer grep, skip `:702`, type-creation raise
`:1830-1831`, union `:792-796` covering the guard population,
post-flip mutation teardown-only); R8/R9 (`:756` composition)
/R10 (writer census: decl + merge arm + prune rebuilds +
walker triple, no third writer)/R11/R12 (definition 6/6
identical) hold. I1-I5 clear (`:724` wrapper docstring,
`:34`/`:1734` scope, zero `*.py` hits, KANBAN-homed prose).
P1-P8 re-pinned (`:850-865`, `:821-849`, `:1026`/`:1035`,
threading, identical descriptor, identical P6/P7 bodies,
`:1323`/`:1332` with identical callees): no projection defect.
Matrix axes 1-6 re-discharged (custom-qs consumers `:381`/
`:402`/`:1395` on unchanged populations; recourse prose
`:578-585`; cacheable `:1101`/`:1337`/`:1292` + identical
absorb). Oracle census 180 -> 181 = -2 `dbf0a870` last-zero
tests + 3 `5c5e32c5` combined tests (names re-read from both
commit diffs); oracle-by-alias imports (`:25-42`,
`:2726`/`:3308`/`:3330`) stand as an observation. O1 endorsed:
preamble imprecise for exactly the rebound name (defined
`utils/connections.py:773`, re-exported `nested_planner.py:45`),
all operative claims grep-verified (two test-pinned reads, seven
assignment-only here, direct-from-planner readers in
`connection.py` + `test_keyset_connection.py`) — stale-preamble
prose, no contract row, no row owed (pin corrected in §9).

### 8. Hunk attribution (8/8, by content) + D1

All concurrent-external (no ledger row beyond D1; all pre-date
the item via `ITEM_BASELINE`), all truth-migration, all
behavior-preserving on every feasible project shape
(`truth.py` semantics read in-copy: `name` answers the
`__name__` slot for real classes and `NoneType` for `None`;
`static_attr` skips metaclass hooks/descriptors;
`is_subclass` is real-MRO membership, `False` for
non-classes): H1 import; H2 logger (same string; `None` corner
hardens — unreachability re-proved: definition-backed verdicts
pair origin+definition from one answer whose enumerated shapes
never yield `(None, definition)`, and the public
definition-`None` path short-circuits on `target_type is not
None` before the logger); H3 same answer, metaclass answers no
longer consulted (the migration's point); H4 same verdict
(virtual-subclass/non-class divergences need shapes outside
supported API); H5-H7 same strings (`type_cls` non-`None` per
the function's own comment, incl. the drift-new reroute pair);
H8 identical (`inner.model` is always a real class). All 8
sites plus the strict forward, absorb seam, hint function, and
D1 regions confirmed in-copy (1826 lines, `truth.name(` x6).
D1 stands unreopened: import `:20`, default `:556`, seed
`:594`, `policy=policy` `:635`, rationale + seam `:640-664`,
wired `:1824`; six-field record `:2869-2874`; the two child
policies differ on `reject_sliced` alone (values re-read;
LIST pin corrected in §9); D1-C zero hits re-grepped.

### 9. Three corrections (recorded here; W1's text preserved)

- C-V2-1: W1's D1 pin `:2928` names `reject_sliced=False` inside
  `_RAW_LIST_SOURCE_POLICY`, not `_LIST_RELATION_CHILD_POLICY`
  (which is `:2909`; `:2897` for the PREFETCH arm is correct).
  Corrected pair: `:2897`/`:2909`. The one-axis split itself is
  verified true.
- C-V2-2: W1's O1 pin `:97` names the last selections alias; the
  preamble sentence sits at `:98-99`. Corrected pin: `:98-99`.
- C-V2-3: W1's "two `Any` hits" miscounts — three `\bAny\b` hits
  (`:379`/`:1413`/`:1618`), all prose. The no-runtime-`Any`
  substance holds.
No verdict, trigger, row text, or index instruction moves on any
of the three. No W1 re-pass needed for these alone.

### 10. Defects, pending execution, plan rows

Zero-defect call endorsed (H2 and O1 are observations below the
bar, both re-proved). `## Pending execution` correctly empty:
every challenge is a structural claim over a closed,
grep-enumerated population with no behavior change proposed, so
no equivalence proof is owed; the backstop is the plan's final
gate (181 walker oracles + live suites incl. the combined
rows). Sharded/pg cells stay with the gate item.

Exact plan rows for Worker-0 (no plan file edited — Worker 0
owns it): tick `- [ ] File optimizer/walker.py` ->
`- [x] File optimizer/walker.py` (this artifact,
`Status: verified`, no pending execution); transcribe verbatim
the revised `optimizer-hint-dispatch` row from
`## Index rows for Worker-0 (run-8 s12)`; CONFIRM notes
transcribe nothing; no `## Owned changes` rows (zero-edit
re-trace). Carry the §9 corrections as record, not index edits.

RUN-8-VERIFY-RECORDED — `docs/dry/dry-file-optimizer__walker.md`

### Nothing-else-changed

Pre-edit artifact 2368 lines / 139842 B (untracked, as at W1
time); the item-scoped delta is exactly the `Status:` line swap
plus this EOF append. No production edit, no test edit, no plan
edit, no new tracked file, zero `.py` touched, so no ruff run
owed. Appended prose checked against AGENTS.md: `path::Symbol`
cites, `path:NN` confined to this per-cycle artifact (allowed),
no process provenance beyond the DRY.md-mandated role labels, no
cross-file links (no scaffold owed). No `(Worker-2)` defect
(none found). Concurrent dirt left alone; no commit.
