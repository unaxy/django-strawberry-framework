# DRY review: `optimizer/extension.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

Target [ext][ext] (`DjangoOptimizerExtension`, 1618 lines) is the
package's optimizer entry point: a Strawberry schema extension that,
at each operation's root resolver, walks the selection tree once via
the O2 walker, builds an `OptimizationPlan`, and applies
`select_related` / `prefetch_related` to the root queryset. It owns
no rule of its own that a second site restates; it is the composing
caller over five neighboring owners:

- Frame lifecycle + stash vocabulary + per-execution memos: [ctx][ctx].
- Per-operation extension binding + refusal protocol:
  [op-state][op-state].
- Plan build + plan record + reconcile + runtime paths: [walker][walker],
  [plans][plans], [nested-fetch][nested-fetch], [selections][selections].
- Query-source coercion + async-only row adapter:
  `utils/querysets.py::normalize_query_source`,
  `utils/querysets.py::unwrap_async_queryset_adapter`,
  `utils/querysets.py::wrap_async_queryset_adapter`.
- Model/type reverse map: `registry.py::registry`
  (`model_for_type`, `get_definition`, `iter_types`, `get`).

Downstream consumers of what this file publishes: `connection.py`
(`apply_connection_optimization` at its pre-slice tail),
`mutations/resolvers.py` (re-fetch via `mutation_payload_child_selections`
plus `apply_connection_optimization`), `types/resolvers.py` (reads
`DST_OPTIMIZER_PLANNED` + scoped relations + strictness in `_check_n1`),
and the test oracles `tests/optimizer/test_extension.py` (6117 lines)
plus live HTTP suites (`test_optimizer_auto_api`,
`test_products_visibility_api`, `test_scalars_api`,
`test_extension_isolation_api`, `test_single_parent_fastpath_api`).

Contract sources (authoritative definitions only):
[spec-002][spec-002], [spec-003][spec-003], [spec-004][spec-004]
(spec-030/033/035/036 decisions cited in the module body), and each
neighbor's module docstring + owning symbol body.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched every
`apply_connection_optimization` caller: [connection][connection]
(pre-slice tail), `mutations/resolvers.py` (post-write re-fetch with
a payload-slot extractor). Both funnel into the one
`DjangoOptimizerExtension.apply_to` tail (spec-030 Decision 11);
genuine variation (connection `edges/node` vs payload `<slot>`
navigation) is parameterized as `SelectionExtractor`, not mirrored.
No second plan-application body. Discharged.
2. **Sync/async twins.** The module holds zero `sync_to_async`
imports and exactly one `async def` (`_async_optimize`, a closure
inside `resolve` that awaits the consumer's resolver and then calls
the sync `_optimize`). `_optimize`/`apply_to`/plan-build perform no
ORM I/O (lazy queryset chaining only), so there is no colored twin
to drift: one sync body, one 3-line await adapter. Compared by
behavior: the async path returns `self._optimize(await result,
info)`, identical call, no branch. Discharged.
3. **Derived rather than repeated knowledge.** The plan-cache key
derives the document key from the printed AST plus reachable
fragment bodies (deliberately NOT the raw source body, which would
collide multi-operation documents, and NOT a hash, which could
collide plans). Origin/model derive via `registry.model_for_type`
composed by name, never re-derived from `_meta` here. The
`(doc_key, relevant_vars)` pair is derived once per execution into
the frame memo, cross-request into `_doc_key_cache`. No second
derivation site found (whole-package grep for `print_ast`,
`_collect_schema_reachable_types`, `_build_cache_key`: each defined
once). Discharged.
4. **Inverse / round-trip pairs.** `_hashable_variable_value` /
`_freeze_variable_value` are one-way identities (no unfreeze);
doc-key rendering is print-only (no parse-back); `_stash_union`
merges one way. No round-trip pair exists on this surface.
Discharged (no such surface).
5. **Contracts restated in another medium.** Oracles:
[test-ext][test-ext] (gating, cache counters, strictness, audit,
context isolation, hostile values) asserts behavior, never reads
the owner's tables (it imports callables to execute them, plus the
two documented compat aliases below). Live HTTP suites pin the wire
behavior. [spec-002][spec-002]/[spec-003][spec-003]/[spec-004][spec-004]
plus module docstrings state the decisions; [tree][tree] prose is
projection. No restatement requiring a move counted as definition.
Discharged.
6. **Enforcement by omission.** Enumerated the asymmetric members;
each asymmetry is contract-stated in the body, not a gap:
strictness sentinels publish only when `strictness != "off"`
(off = no guard); `DST_OPTIMIZER_PLAN` stays last-wins while
correctness sets union (introspection vs sentinel, stated);
nested-pagination collection only at depth >= 1 (root slicing is
post-plan, stated); `_SAFE_CACHE_SCALAR_TYPES` uses exact
`type()` so subclasses stay opaque (stated); uncacheable plans
enter the per-execution memo, never `_plan_cache` (stated);
`check_schema` skips non-relations, `SKIP`-hinted, hidden, and
orphan types (stated). The G1 evaluated-queryset guard sits on the
middleware path only; the connection path builds its queryset
inside the package pipeline (no consumer-evaluated source exists
there), and no contract source extends G1 to it -- investigated,
not a gap, no defect. Discharged.

### Enumeration

Instrument: every name in `ast.Module.body` of [ext][ext].
Count: **77** top-level statements = 1 module docstring + 39
imports + 14 assigns + 18 defs + 5 classes. Imports and the
docstring carry no rule. The 37 rule-bearing members plus 17
method-level members enumerate below; every one lands in a family
row (F-prefix, indexed name reused), a file-local row (FL-prefix),
or a rejection (R-prefix). No member unassigned.

Module assigns (14): `_child_selections`,
`_unvisited_fragment_definition`, `_named_children`,
`_node_children_with_runtime_prefix`, `_response_key`,
`_MAX_PLAN_CACHE_SIZE`, `_STRICTNESS_MODES`,
`_PAGINATION_ARG_NAMES`, `_SAFE_CACHE_SCALAR_TYPES`, `__all__`,
`_MAX_DOC_KEY_CACHE_SIZE`, `_doc_key_cache`,
`SelectionExtractor`, `_OPTIMIZER_CONFIGURATION`.

Module defs (18): `_is_valid_strictness`,
`_walk_cache_relevant_vars`, `_collect_cache_var_families`,
`_collect_directive_var_names`,
`_collect_nested_pagination_var_names`,
`_collect_cache_relevant_var_names`, `_hashable_variable_value`,
`_freeze_variable_value`, `_collect_reachable_fragment_definitions`,
`_walk_reachable_fragment_definitions`,
`_print_operation_with_reachable_fragments`, `_doc_cache_entry`,
`_root_child_selections`, `_connection_node_child_selections`,
`mutation_payload_child_selections`,
`_collect_schema_reachable_types`,
`_resolve_model_from_return_type`,
`apply_connection_optimization`.

Classes (5): `CacheInfo`, `_OriginAndModel`,
`_OptimizerOperationState` (methods: `__init__`),
`_AcceptedOptimizerConfiguration`,
`DjangoOptimizerExtension` (methods: `__init__`,
`_new_operation_state`, `_configuration`, `strictness`,
`nested_connection_strategy`, `cache_info`, `on_execute`,
`resolve`, `_optimize`, `apply_to`, `_get_or_build_plan`,
`_publish_plan_to_context`, `_stash_union`, `check_schema`,
`_build_cache_key`, `plan_relation`).

Row map: F1 `optimizer-execution-frame` takes `on_execute`,
`apply_connection_optimization` (frame discovery),
`_get_or_build_plan` (exec memo), `_build_cache_key` (key-parts
memo), `_publish_plan_to_context` + `_stash_union` (stash reads /
writes). F2 `operation-bound-extension-mechanism` takes
`DjangoOptimizerExtension` (base + refusal), `_new_operation_state`,
`_OptimizerOperationState`, `on_execute` (state read). F3
`async-only-queryset-row-adapter` takes `_optimize` (unwrap/wrap).
F4 `type-registry-model-type-map` takes
`_resolve_model_from_return_type`, `_collect_schema_reachable_types`
+ `check_schema`, `apply_connection_optimization` (model reads).
FL1 takes `_build_cache_key`, `_get_or_build_plan`, `_doc_cache_entry`,
`_doc_key_cache`, `_MAX_DOC_KEY_CACHE_SIZE`. FL2 takes
`_print_operation_with_reachable_fragments`,
`_collect_reachable_fragment_definitions`,
`_walk_reachable_fragment_definitions`. FL3 takes
`_walk_cache_relevant_vars`, `_collect_cache_var_families`,
`_collect_directive_var_names`,
`_collect_nested_pagination_var_names`,
`_collect_cache_relevant_var_names`. FL4 takes
`_hashable_variable_value`, `_freeze_variable_value`,
`_SAFE_CACHE_SCALAR_TYPES`. FL5 takes `_PAGINATION_ARG_NAMES`.
FL6 takes `_STRICTNESS_MODES`, `_is_valid_strictness`,
`_AcceptedOptimizerConfiguration`, `_OPTIMIZER_CONFIGURATION`,
`__init__` (config arm), `_configuration`, `strictness`,
`nested_connection_strategy`. FL7 takes `_MAX_PLAN_CACHE_SIZE`,
`cache_info`. FL8 takes `SelectionExtractor`,
`_root_child_selections`, `_connection_node_child_selections`,
`mutation_payload_child_selections`. FL9 takes
`_resolve_model_from_return_type`, `_OriginAndModel`. FL10 takes
`resolve`, `_optimize`. FL11 takes `apply_to`. FL12 takes
`_publish_plan_to_context`, `_stash_union`. FL13 takes
`check_schema`, `_collect_schema_reachable_types`. FL14 takes
`plan_relation`. FL15 takes `apply_connection_optimization`.
FL16 takes the five compat aliases + `__all__`. FL17 takes
`on_execute` (frame open/clear/close). FL18 takes `CacheInfo`.
R1-R4 carry the LRU-literal, hostile-eq idiom, fragment-guard, and
non-membership verdicts.

### Challenges

Authoritative definitions only (neighbor bodies + specs); consumer /
oracle / projection moves listed, never counted.

- C1 (frame): posit per-execution memo keyed differently per reader.
Definitions forced: **1** ([ctx][ctx] owns the frame; this file only
calls `begin`/`end`/`clear` and reads memos). Verified sole
production caller from this side: package-wide search finds
`begin_execution_frame` called once (line 1052),
`end_execution_frame` once (line 1072), `clear_optimizer_context`
once (line 1068); all other mentions are [ctx][ctx] defs/docstrings.
- C2 (binding): posit a second construction replacing config.
Definitions forced: **1** ([op-state][op-state] owns the carrier +
refusal protocol; this file overrides `_reconstruction_refusal`
with optimizer-specific wording and `_new_operation_state` with
the stashes-carrying state). Sibling overrides (`debug.py`,
`resource_policy.py`) are distinct refusal texts, not copies.
- C3 (row adapter): posit a new async-only source shape.
Definitions forced: **1** (`utils/querysets.py::_AsyncQuerySetRows`
+ wrap/unwrap pair; this file's `finish` closure composes them).
- C4 (registry map): posit a new type-to-model mapping rule.
Definitions forced: **1** (`registry.py::registry`; this file reads
`model_for_type` twice, `get_definition`, `iter_types`/`get` once
each, all by name).
- C5 (cache key): posit a sixth key component (e.g. operation type).
Definitions forced: **1** (`_build_cache_key` tuple). Memos
(`_doc_cache_entry`, frame key-parts memo) derive from it; tests
asserting key shape are oracles.
- C6 (var families): posit a third cache-relevant variable family.
Definitions forced: **1** (`_walk_cache_relevant_vars` single
descent; three thin wrappers project it). Docstring states the
unification replaced two walkers.
- C7 (value freeze): posit a newly safe scalar type.
Definitions forced: **1** (`_SAFE_CACHE_SCALAR_TYPES` set +
`_freeze_variable_value` recursion).
- C8 (strictness): posit a fourth mode. Definitions forced: **1**
(`_STRICTNESS_MODES` + `_is_valid_strictness`; message renders the
same tuple so validator and text cannot drift). Readers
(`types/resolvers.py` via `active_strictness`) consume, never
re-spell.
- C9 (extractors): posit a third response nesting (beyond
connection edges/node and payload slot). Definitions forced: **1
per shape by design** -- extractors parameterize genuine variation
(spec-030 Decision 11, spec-036 Decision 9); the shared navigation
(`connection_node_children`, `named_children`) is owned by
[selections][selections] and composed by name.
- C10 (publish): posit a new correctness sentinel. Definitions
forced: **1** (`_publish_plan_to_context` union discipline +
`_stash_union`); key vocabulary owned by [ctx][ctx]
(`DST_OPTIMIZER_KEYS`).
- C11 (LRU bounds): change `_MAX_PLAN_CACHE_SIZE` 256 -> 512.
Definitions forced: **1** (doc-key cache keeps its own bound;
nested_planner advisory cache keeps its own). See R1.
- C12 (seal/boundary): posit the extension must seal querysets or
own a sync boundary. No definition here at all: zero seal imports,
zero `sync_to_async` imports, no ORM I/O. See R4.

All probes read-only: `ast` dumps + whole-package content search.
No mutating proof; no shared-tree pytest run (inspection decides
every row). No `## Pending execution` entries.

## Findings

### F1 `optimizer-execution-frame` (family, consumer + sole caller)

- Contract + variation: one managed execution's scratch (optimizer
instance, strategy, strictness, scoped relations, plan/key-parts/
converted memos, per-operation stashes) with lease-ended lifetime.
Varies per execution, never per resolver.
- Sites + roles: definition at [ctx][ctx] (frame, keys, reset,
accessors, stash pair, re-export). This file: SOLE production
begin/end/clear caller (C1 evidence) + composing consumer of seven
readers (`_active_optimizer`, `_execution_plan_memo`,
`_cache_key_parts_memo`, `_operation_publishes_to_context`,
`_optimizer_value`, `_publish_scoped_relations`,
`_stash_for_optimizer`). Consumers: `connection.py`,
`mutations/resolvers.py` (via `apply_connection_optimization`),
`types/resolvers.py` (strictness/scoped reads). Oracles:
[test-ext][test-ext] isolation tests + `test_extension_isolation_api`
(live). Projection: [tree][tree] optimizer rows.
- Challenges: C1, count 1.
- Owner + lifetime: [ctx][ctx] owns (see
`dry-file-optimizer___context.md`); this file holds no frame state
(plan cache is instance-bound cross-request config, not execution
state). Lifetime fields live at the owner.
- Migration: none (file item; no consolidation here).
- Distinct behavior: `converted_selections_memo` is read by
[selections][selections], never here; `active_strictness` /
`relation_is_optimizer_scoped` by `types/resolvers.py`. Reader set
stays partitioned by responsibility.
- Behavioral proof: static-reviewed (call-site census + import
list). No execution needed: begin/end/clear pairing is visible in
`on_execute`'s try/finally.
- Structural gate: owned by the family item, not this file item.
- Coupling: none.
- Freshness: [ext][ext] `49667a93`, [ctx][ctx] `3d8dcfdf`,
[op-state][op-state] `b2674a22`, `utils/context.py` `cd0adcc5`,
searched population whole `django_strawberry_framework/`.

### F2 `operation-bound-extension-mechanism` (family, consumer)

- Contract + variation: per-operation mutable state bound through a
task-local carrier; configuration frozen at construction; second
construction refused with a typed error.
- Sites + roles: definition at [op-state][op-state]
(`_OperationBoundExtension`, carrier, refusal protocol, runner).
This file: subclass `DjangoOptimizerExtension` + optimizer-worded
`_reconstruction_refusal` (strictness/strategy wording, distinct
from the base carrier wording and siblings') +
`_OptimizerOperationState(OperationState)` adding the `stashes` slot
+ `_new_operation_state` override + `_operation_state()` /
`_operation_is_nested()` reads in `on_execute`. Siblings
(`debug.py::_DebugOperationState`, `error_policy.py`,
`resource_policy.py`) are fellow consumers with their own state
shapes. Oracles: [test-ext][test-ext] nesting/isolation tests.
- Challenges: C2, count 1.
- Owner + lifetime: [op-state][op-state]; stashes mapping owned by
the runner-bound state (dies with the request; frame borrows it,
never clears it -- stated at both owners).
- Migration: none.
- Distinct behavior: each subclass's refusal text and state shape
stay separate (different config replaced); the mechanism stays one.
- Behavioral proof: static-reviewed (subclass + override census).
- Structural gate: family item.
- Coupling: none.
- Freshness: [ext][ext] `49667a93`, [op-state][op-state] `b2674a22`.

### F3 `async-only-queryset-row-adapter` (family, consumer)

- Contract + variation: async-only completion adapter exposing only
`__aiter__` so graphql-core cannot pick sync ORM iteration on a loop
thread. Varies only in the wrapped queryset.
- Sites + roles: definition at
`utils/querysets.py::_AsyncQuerySetRows` (+ wrap/unwrap pair). This
file: `unwrap_async_queryset_adapter` at `_optimize` entry,
`wrap_async_queryset_adapter` in the `finish` closure (identity
preserved for non-adapted results). Fellow consumers per index:
`list_field.py`, `resource_policy.py`, `connection.py`. Oracles:
[test-ext][test-ext] unwrap/rewrap identity tests.
- Challenges: C3, count 1.
- Owner + lifetime: `utils/querysets.py`; adapter lives for the
single `_optimize` call.
- Migration: none. Distinct behavior: `normalize_query_source`
(Manager coercion + is-queryset decision, same owner) is the
adjacent but separate contract, also composed by name here.
- Behavioral proof: static-reviewed.
- Structural gate: family item. Coupling: none.
- Freshness: [ext][ext] `49667a93`, `utils/querysets.py`
`1539b66c`.

### F4 `type-registry-model-type-map` (family, consumer)

- Contract + variation: Strawberry origin type <-> Django model
reverse map. Varies per registered type.
- Sites + roles: definition at `registry.py::registry`. This file
reads `model_for_type` in `_resolve_model_from_return_type` and
`apply_connection_optimization`, `get_definition` in the reachable
walk, `iter_types`/`get`/`get_definition` in `check_schema` -- all
by name, no local map. Full site list at the family index row.
- Challenges: C4, count 1. Owner: `registry.py`.
- Migration: none. Behavioral proof: static-reviewed.
- Structural gate: family item. Coupling: none.
- Freshness: [ext][ext] `49667a93`, `registry.py` `9cc8bb55`.

### FL1 plan-cache key + two-tier memo (file-local)

`_build_cache_key` (doc key + relevant vars + model + root path +
origin), `_get_or_build_plan` (cross-request `_plan_cache` with
LRU promotion, per-execution memo for uncacheable plans, quarter
sweep eviction), `_doc_cache_entry` (cross-request doc-key LRU) +
bounds. Proving challenge C5/C11: a sixth component moves only the
key tuple; a bound change moves only its own constant (R1). Second
site searched (whole package): none -- walker/plans never key or
evict. Oracles: [test-ext][test-ext] hit/miss/size + multi-root
separation tests. Proof: static-reviewed.

### FL2 reachable-fragment doc key (file-local)

`_print_operation_with_reachable_fragments` +
`_collect_reachable_fragment_definitions` /
`_walk_reachable_fragment_definitions` (selection-order walk,
name-only visited guard). Challenge: print reachable bodies inline
instead -- moves only this renderer. The depth-sensitive
`(name, depth)` guard (FL3) serves a different purpose; see R3.
No second renderer in the package. Proof: static-reviewed.

### FL3 cache-relevant variable sweep (file-local)

`_walk_cache_relevant_vars` single descent collecting directive
vars (all depths) + nested pagination vars (FieldNode, depth >= 1)
with `(name, depth)` cycle guard; `_collect_cache_var_families`
entry + three thin wrappers (directive-only, pagination-only,
union). Challenge C6: a third family moves only the walker; the
wrappers project it. The union caller (`_build_cache_key`) walks
once per call. No second AST descent for this purpose. Proof:
static-reviewed.

### FL4 hostile-value freeze (file-local)

`_hashable_variable_value` / `_freeze_variable_value` (tagged
structural identities; exact-type scalar allowlist;
opaque-per-value fallback; cycle tokens; `Exception`-only absorbs)
+ `_SAFE_CACHE_SCALAR_TYPES`. Challenge C7: allowlisting one more
stdlib scalar moves only the set. No second freeze site. Oracles:
[test-ext][test-ext] hostile-container tests. Proof:
static-reviewed.

### FL5 pagination argument names (file-local)

`_PAGINATION_ARG_NAMES` (first/last/before/after). Challenge: a
future `search:` extension moves this one set (stated in the
comment). Read once (FL3 line 282). Proof: static-reviewed.

### FL6 strictness vocabulary + config freeze (file-local)

`_STRICTNESS_MODES` + `_is_valid_strictness` (base-`str`-slot
content match; non-`str` rejected without a probe) +
`_AcceptedOptimizerConfiguration` + `_OPTIMIZER_CONFIGURATION`
(`PrivateAuthority` composes the shared primitive by name; the
freeze rule -- singleton-shared instance, per-request writes
forbidden -- is this file's) + read-only `strictness` /
`nested_connection_strategy` + `_configuration` safe default +
`__init__` validation (`ValueError` via `_safe_arg_repr`,
strategy via `resolve_strategy`). Challenge C8: a fourth mode
moves only the tuple. No second vocabulary (readers use
`active_strictness`). Proof: static-reviewed.

### FL7 cache bounds + best-effort introspection (file-local)

`_MAX_PLAN_CACHE_SIZE`, `_MAX_DOC_KEY_CACHE_SIZE`, quarter-sweep
eviction with `suppress(KeyError)` races, `CacheInfo` (FL18) +
`cache_info` best-effort caveat. Challenge C11. See R1 for the
shared literal. Proof: static-reviewed.

### FL8 selection extractors (file-local)

`SelectionExtractor` alias + `_root_child_selections` (union over
merged root nodes) + `_connection_node_child_selections`
(edges/node navigation via `connection_node_children` +
`connection_field_names`, one owner each) +
`mutation_payload_child_selections(slot)` closure. Challenge C9:
each shape varies genuinely (spec-030 D11, spec-036 D9); the
navigation primitives stay owned by [selections][selections].
Consumers: `connection.py` (default), `mutations/resolvers.py`
(slot). Oracles: `tests/optimizer/test_walker.py`
payload-selection tests. Proof: static-reviewed.

### FL9 return-type resolution (file-local)

`_resolve_model_from_return_type` (peel wrappers via
`unwrap_graphql_type`, schema via `strawberry_schema_from_info`,
origin via `get_type_by_name`, model via `model_for_type`) +
`_OriginAndModel` pair-or-`None` contract. Challenge: supporting a
new wrapper moves only the peel (owned by `utils/typing.py`);
callers branch on `None`. No second resolver. Proof:
static-reviewed.

### FL10 root gate + optimize pipeline (file-local)

`resolve` (`info.path.prev is None` gate + `_async_optimize`
adapter) + `_optimize` (unwrap adapter -> `normalize_query_source`
-> G1 evaluated guard via `_result_cache is not None`, placed
after Manager coercion and before return-type resolution / clone,
stated -> resolve type -> `apply_to`). Challenge: moving the G1
check before coercion would wrongly skip `Model.objects`
resolvers; the placement is the rule, single-sited. No twin body.
Oracles: [test-ext][test-ext] gating tests + live
`test_scalars_api` manager-coercion test. Proof: static-reviewed.

### FL11 plan-build-and-apply tail (file-local)

`apply_to` (thunked `ast_to_converted_selections` conversion so
cache hits skip it; `prune_unsupportable_select_related`;
`diff_plan_for_queryset` reconcile before publish; publish;
empty-plan early return; `plan.apply`). Challenge: a new reconcile
step moves only this tail; the reconcile primitives stay owned by
[plans][plans]. The thunk-vs-list parameter shape is this file's
stated call contract. Proof: static-reviewed.

### FL12 publish discipline (file-local)

`_publish_plan_to_context` (plan last-wins; FK-id + planned sets
unioned; scoped relations published every execution; strictness
sentinels gated) + `_stash_union` (frozenset/set union, subset
early-out, defensive non-set overwrite). Challenge C10: a new
sentinel moves only the publish. Key vocabulary owned by
[ctx][ctx]; readers in `types/resolvers.py`. Oracles: strictness
N+1 tests across tiers. Proof: static-reviewed.

### FL13 schema audit (file-local)

`check_schema` (reachable-only walk, exposed-relation filter, SKIP
honor, unregistered-target warnings, `(model, field)` dedupe) +
`_collect_schema_reachable_types` (roots + fields + unions +
interface implementations via `get_implementations`, orphan
exclusion). Challenge: auditing orphans too moves only the
reachable-set builder. No second audit. Oracles: [test-ext][test-ext]
audit tests + `test_definition_order.py`. Proof: static-reviewed.

### FL14 per-relation delegate seam (file-local)

`DjangoOptimizerExtension.plan_relation` delegates to
[walker][walker]`::plan_relation` unchanged. deliberately an
override seam for subclasses/tests (stated). Challenge: a strategy
parameter moves the walker signature; this seam follows.
Trigger to reconsider: seam-shape divergence (delegate gains
logic). Proof: static-reviewed.

### FL15 connection cooperation point (file-local)

`apply_connection_optimization` (model from `target_type`, active
instance from `_active_optimizer`, raw-info unwrap, short-circuit
when either missing, extractor forwarded). Challenge: optimizing
without an installed extension moves only the short-circuit --
rejected by contract (opt-in parity with the middleware path,
stated). Callers: [connection][connection],
`mutations/resolvers.py`. Oracles: `tests/test_connection.py`
short-circuit tests. Proof: static-reviewed.

### FL16 compat aliases + manifest (file-local)

Five aliases onto [selections][selections] primitives
(`_child_selections`, `_unvisited_fragment_definition`,
`_named_children`, `_node_children_with_runtime_prefix`,
`_response_key`) + `__all__` (incl. `_stash_on_context`
re-export whose canonical home is [ctx][ctx]). Challenge: dropping
an alias moves only this module + the importing tests
([test-ext][test-ext] imports two). Trigger to reconsider: test
imports migrated off the aliases -- then delete, not extract.
Proof: static-reviewed.

### FL17 execution open/clear/close (file-local)

`on_execute` (frame open with optimizer/strategy/strictness/stash
store; start-of-execution clear gated on
`_operation_publishes_to_context`; `try/finally` close). The frame
contents are F1; the open-clear-close *sequence* is this file's
only. Challenge: publishing for nested operations moves only the
gate predicate (owned by [ctx][ctx]). Proof: static-reviewed.

### FL18 plan-cache statistics record (file-local)

`CacheInfo` (hits/misses/size). Challenge: a new counter moves
only the record + `cache_info`. Proof: static-reviewed.

### Rejections

- R1 bounded-LRU eviction shape. Considered: unifying the two
`move_to_end`/`popitem(last=False)`+`suppress(KeyError)` sweeps in
this file (plan cache vs doc-key cache) and the third in
`nested_planner.py::_index_advisory_seen`. Difference: three
caches, three owners, three lifetimes (instance cross-request plan
vs module cross-request doc-key vs module advisory-seen), two
distinct bounds that happen to share the literal 256. Change C11
moves exactly one. Trigger: a shared bounded-cache primitive with
per-cache bounds + lifetime (a helper obscuring ownership is worse
today; principle 4/11).
- R2 hostile-subclass content-match idiom. Considered: unifying
`_is_valid_strictness` (base-`str`-slot scan, bool answer) with
`nested_fetch.py::resolve_strategy` (slot scan, strategy answer)
and `operation_state.py::_declared_operation_mode` (exact-type
first-match). Difference: three vocabularies, three rejection
types, three reasons to change; the `str.__eq__` slot is a Python
idiom, not a package rule. Trigger: a fourth vocabulary needing
the same discipline -- still a per-site two-liner, not a shared
matcher (a shared matcher would couple three rejection contracts).
- R3 fragment-guard disciplines. Considered: unifying the
name-only guard (FL2 reachable-body printing) with the
`(name, depth)` guard (FL3 depth-sensitive collection).
Difference: printing needs each body once in deterministic order;
collection is depth-sensitive (a root spread must not suppress a
nested spread's pagination vars -- correctness, spec-033
Decision 7). Trigger: collection protocol change -- then re-check
whether one guard serves both.
- R4 non-memberships (checked, not inherited):
`sealed-execution-queryset` -- this file never seals (zero seal
imports; plan application only; the seal policy lives in
`optimizer/walker.py::_build_child_queryset` incl. the ledgered D1
fix). `one-sync-boundary` -- this file executes no ORM work (zero
`sync_to_async` imports; single `async def` adapter). Neither
family gains a site here.

## Defects

None found while tracing. Every asymmetry checked against a
contract source in the body or a cited spec decision; the one
candidate (G1 guard middleware-only, matrix axis 6) is scoped by
its contract source (spec-035 Decision 3: consumer root-resolver
sources) with no feasible wire input reaching the connection path
with a consumer-evaluated queryset. No security-routing,
authorization, or data-exposure question arose.

## Pending execution

None. Every proof is static-reviewed: all verdicts rest on
import/call-site census, whole-package single-definition search,
and body inspection. No shared-tree pytest run was needed
(inspection beats execution on every row); no workspace proof was
needed (nothing order-, transaction-, or async-behavioral beyond
the 3-line await adapter, whose equivalence is visible).

## Judgment

Zero-edit file item. All 77 top-level members assigned: 4 family
consumer rows (3 reused index names verified from this side --
`optimizer-execution-frame` incl. the sole-caller claim,
`operation-bound-extension-mechanism` incl. refusal + state,
`async-only-queryset-row-adapter` incl. `unwrap_` -- plus
`type-registry-model-type-map`), 18 file-local rows each with its
proving challenge, 4 rejections with differences + triggers.
No consolidation lives in a file item; the two LRU sweeps and the
slot-idiom stay separate by recorded intent. Target clean at open
and at close; no production edit made or owed.

## Implementation (Worker 1)

No tracked changes. Target [ext][ext] untouched (worktree blob
`49667a93` at open and close; `git diff` on the path empty).
No tests added (oracles already pin every row at the mandated
tiers). No `ruff` run needed (no edits). No commit (the maintainer only).
Item-scoped diff: empty for production paths; this artifact is a
new untracked file only.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-002]: ../SPECS/spec-002-optimizer-0_0_2.md
[spec-003]: ../SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-004]: ../SPECS/spec-004-optimizer_beyond-0_0_3.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[ctx]: ../../django_strawberry_framework/optimizer/_context.py
[ext]: ../../django_strawberry_framework/optimizer/extension.py
[op-state]: ../../django_strawberry_framework/extensions/operation_state.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[selections]: ../../django_strawberry_framework/optimizer/selections.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py

<!-- tests/ -->
[test-ext]: ../../tests/optimizer/test_extension.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Own trace first (recorded before reading `## Findings`; reconciled after).
Target `django_strawberry_framework/optimizer/extension.py` (1618 lines,
worktree blob `49667a93`, matches W1 open/close) is a composing caller, not a
rule owner. Rules re-derived with posited changes and definition counts:

- Frame caller/consumer: posit per-execution memo keyed differently per
  reader. Count 1 (`optimizer/_context.py` owns; sole production
  begin/end/clear caller at ext lines 1052/1068/1072; package-wide grep finds
  no other production caller). Owner: `optimizer/_context.py`. Agree F1.
- Binding consumer: posit second construction replacing config. Count 1
  (`extensions/operation_state.py` owns carrier + refusal; this file's
  `_reconstruction_refusal` wording is optimizer-specific and textually
  distinct from `debug.py` and `resource_policy.py` siblings, verified by
  read). Owner: `extensions/operation_state.py`. Agree F2.
- Adapter consumer: posit new async-only source shape. Count 1
  (`utils/querysets.py::_AsyncQuerySetRows` + wrap/unwrap pair; unwrap at
  `_optimize` entry, wrap in `finish` closure). Zero `sync_to_async`
  imports; exactly one `async def` (3-line `_async_optimize` closure).
  Owner: `utils/querysets.py`. Agree F3.
- Registry consumer: posit new type-to-model mapping rule. Count 1
  (`registry.py::registry`; `model_for_type` x2, `get_definition`,
  `iter_types`/`get`, all by name, no local map). Owner: `registry.py`.
  Agree F4.
- Plan-key/memo (FL1): posit sixth key component. Count 1 (`_build_cache_key`
  tuple). File-local. Agree.
- Fragment key (FL2): posit inline-print change. Count 1 (renderer only).
  File-local. Agree.
- Var sweep (FL3): posit third variable family. Count 1 (single descent +
  thin wrappers). File-local. Agree.
- Value freeze (FL4): posit newly safe scalar. Count 1 (set + recursion).
  File-local. Agree.
- Pagination names (FL5), strictness/config freeze (FL6), bounds/cache
  (FL7), extractors (FL8: 1 per shape by design, navigation primitives owned
  by `optimizer/selections.py` and composed by name -- verified
  `connection_node_children` call at ext line 659 and alias-composed
  `_named_children`/`_node_children_with_runtime_prefix` calls in the
  payload closure), return-type resolution (FL9), root gate + pipeline
  (FL10), apply_to tail (FL11), publish discipline (FL12), schema audit
  (FL13), plan_relation seam (FL14), connection cooperation (FL15), compat
  aliases (FL16), open/clear/close (FL17), CacheInfo (FL18): each count 1,
  each file-local. Agree all.
- Rejections R1-R4: R1 (three LRU sweeps, three owners/lifetimes, no bare
  `256` outside the two named constants) sound; R2 (three vocabularies:
  bool-answer strictness scan vs strategy-answer registry match with
  `None`-to-setting default vs exact-type first-match mode read with no
  rejection) sound; R3 (name-only visited set vs `(name, depth)` visited
  set, verified distinct types at ext lines 501/233) sound; R4 (zero seal
  mentions and zero `sync_to_async` in target) verified. Agree all.

Enumeration (member-by-member, own AST count): 77 top-level = 1 docstring +
39 imports (35 ImportFrom + 4 Import) + 14 assigns (12 Assign + 2 AnnAssign)
+ 18 defs + 5 classes. Assign/defs/class name lists match W1 exactly;
37 rule-bearing (14 + 18 + 5); method-level 17 (16 on
`DjangoOptimizerExtension` + `__init__` on `_OptimizerOperationState`).
Every member lands in W1's row map. Note: seven members appear in both a
family row and a file-local row (`on_execute`, `_get_or_build_plan`,
`_build_cache_key`, `_publish_plan_to_context`, `_stash_union`,
`_resolve_model_from_return_type`, `check_schema`,
`apply_connection_optimization`); each is a deliberate aspect split
(family-consumed read vs file-local shape), disclosed in both rows.
Endorsed, not double-counting.

Fingerprints re-hashed: ext `49667a93` match; `_context.py` `3d8dcfdf`
match; `operation_state.py` `b2674a22` match; `utils/context.py`
`cd0adcc5` match; `utils/querysets.py` `1539b66c` match; `registry.py`
`9cc8bb55` match. No staleness. Concurrent dirt (connection.py,
mutations/*, filters/*, forms/*, resource_policy.py, auth/mutations.py)
touches consumers only, never a fingerprinted definition site; target blob
unchanged; left alone.

Matrix judged against real surface: axis 1 callers confirmed
(connection.py:1783, mutations/resolvers.py:762 funnel into `apply_to`);
axis 2 one sync body + one 3-line await adapter, no ORM I/O; axis 3 single
definitions confirmed by package grep; axis 4 no round-trip surface exists;
axis 5 oracles assert behavior (`_MAX_PLAN_CACHE_SIZE` monkeypatch sets a
knob on the owning module, never computes expectations from it; compat
aliases imported as behavior entry points with FL16 deletion trigger
recorded); axis 6 asymmetries each contract-stated in the body.

Gates: no per-row gate owed here -- all findings are single-owner with the
gate owned by the holding family item (stated per finding); inventing
bespoke existence tests would violate principle 11. Oracles cited exist
(G1 tests, strictness tests, audit tests, isolation tests in
`tests/optimizer/test_extension.py`, 6117 lines). Negative controls owed at
family items, not here.

Pending absent: adequate. Zero-edit result (no behavior changed, so
principle-8 equivalence is trivial); nothing order-, transaction-, or
async-behavioral beyond the 3-line adapter whose equivalence is visible;
read-only AST + package-wide content search discharged every row. No probe
owed for a 1618-line zero-edit file item once census + search + inspection
all agree -- and my independent trace found no missed second site either.

Defects (Worker 2): none. The G1-guard scoping question is NOT a defect:
spec-035 Decision 3 plus the spec's Current state scope the G1 guard to
`_optimize` explicitly ("out of G1 scope ... G1 lands in `_optimize`
only"), and the connection path is mechanically guarded upstream of the
optimizer tail by the visibility seal (`connection.py` pipeline runs
`apply_type_visibility_*` before `_finalize_queryset`, and an evaluated
source seals to a fresh unevaluated queryset or is rejected -- never
silently re-executed). No contract row broken, so per AGENTS.md it cannot
be a release-blocking defect. W1 correct to release without a defect entry.

AGENTS.md prose: link block carries the 10 canonical groups; citations use
`path::Symbol`; raw line numbers appear only in this `dry-*.md` scratchpad
artifact (permitted); no process provenance; test tiers match mandate
(`tests/optimizer/` + live HTTP suites); no changelog/pytest/commit action.

Zero-edit confirmed by me: `git diff
3dae2a32082913ae587f1ab27c74e2d7fc68bf80 --
django_strawberry_framework/optimizer/extension.py` empty; HEAD pinned at
`9031cb3d`.

Verdict: verified, no pending execution.

## Bounded re-review at bfaee91d (Worker 2, Q10)

Phase 1 of a two-phase bounded re-reconciliation (queue Q10). No prior
diagnosis was opened: every consume, key input, and count below was
re-derived from current source. The three dirty neighbors were read in
full at worktree bytes and their worktree-vs-HEAD hunks were read for
attribution; they were never edited. This section records the trace
only. It sets NO status and proposes NO verdict on any prior finding.

### Scope and method

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`. No branch switch, no commit.
- Complete targets for this phase: `django_strawberry_framework/optimizer/extension.py`
  (whole target, current bytes; verified clean, see fingerprints) plus the
  three dirty neighbors read freely for attribution only:
  (a) `django_strawberry_framework/optimizer/hints.py` (+13 hunk),
  (b) `django_strawberry_framework/optimizer/join_taxonomy.py` (+39 hunk),
  (c) `django_strawberry_framework/optimizer/nested_fetch.py` (+28 hunk).
- Read in full: `optimizer/extension.py`, `optimizer/hints.py`,
  `optimizer/join_taxonomy.py`, `optimizer/nested_fetch.py`.
- Traced by symbol search (no second read of full bodies):
  `optimizer/walker.py`, `optimizer/plans.py`, `optimizer/nested_planner.py`
  (import and call sites only, to place the extension's transitive consumes).
- Oracles READ (headers and contract docstrings only, no execution):
  `tests/optimizer/test_hints.py`, `tests/optimizer/test_join_taxonomy.py`,
  `tests/optimizer/test_nested_fetch.py`, `tests/optimizer/test_extension.py`.
  Their module docstrings state the tier split relied on below (unit-level
  validation here; shipped SQL over HTTP in the fakeshop live suite).
- Applicable contracts: DRY.md principle 4 (lifetimes), principle 7 (owner
  by responsibility).

### 1. The extension's consumes of the three neighbors

Each consume names role (definition / consumer / oracle / projection) and
contract. The extension DEFINES none of the three vocabularies.

#### (a) Hints vocabulary (`optimizer/hints.py`)

- Direct consume (sole import): `optimizer/extension.py::DjangoOptimizerExtension`
  imports `optimizer/hints.py::hint_is_skip` and calls it exactly once, in
  `optimizer/extension.py::DjangoOptimizerExtension.check_schema`, at the
  `OptimizerHint.SKIP` opt-out probe (`hint_is_skip(hints.get(field_name))`).
- Role: extension is a CONSUMER of the hint-shape contract; the authoritative
  DEFINITION is `optimizer/hints.py::OptimizerHint` (fields, factories,
  `__post_init__` rejection, `SKIP` sentinel) plus its two single-owner
  validators `optimizer/hints.py::_require_prefetch` and
  `optimizer/hints.py::_require_strategy` and the dispatch helper
  `optimizer/hints.py::hint_is_skip` itself.
- Contract consumed: SKIP means "exclude this exposed relation from the
  schema audit"; `hint_is_skip` centralises the
  `is OptimizerHint.SKIP or .skip` dispatch and degrades defensively
  (`None` -> False; missing `.skip` -> False; raising descriptor ->
  False) so `check_schema` keeps its never-raises audit posture. The
  extension does NOT consume `_require_prefetch`, `_require_strategy`,
  `OptimizerHint.strategy`, `OptimizerHint.prefetch`, or any factory
  directly.
- What the dirt touches: the +13 hunk hardens `_require_prefetch` (guarded
  `isinstance` against a hostile `__class__`, rejection label via
  `_safe_type_name`). That validator runs at `Meta.optimizer_hints` build
  time (factory `prefetch(obj)` and `__post_init__` direct construction),
  NOT on the extension's `check_schema` path. The extension's one call
  site (`hint_is_skip`) is outside the hunk.
- No duplication in the extension: no second SKIP predicate, no second
  prefetch-type check, no re-spelling of the hint field set. The
  extension's own `_STRICTNESS_MODES` / `_is_valid_strictness` vocabulary
  (`"off" | "warn" | "raise"`) is a deliberately separate rule (different
  inputs, outputs, reasons to change) sharing only the hostile-dunder
  slot discipline as technique, not as rule. Distinct decisions stay at
  adapters; no consolidation owed across the two validators.

#### (b) Join taxonomy (`optimizer/join_taxonomy.py`)

- Direct consume: NONE. `optimizer/extension.py` has no import from
  `optimizer/join_taxonomy.py` (verified by symbol search: zero matches
  for `classify_relation_join`, `RelationJoinDescriptor`,
  `LateralJoinShape`, `_partition_expr`, `_parent_join_column`,
  `_child_link_is_virtual`, `WINDOWABLE_RELATION_KINDS` in the extension
  module).
- Transitive consumes (two hops, both through modules the extension
  already calls by name):
  - `optimizer/extension.py::_get_or_build_plan` calls
    `optimizer/walker.py::plan_optimizations`; the walker imports and
    calls `optimizer/join_taxonomy.py::classify_relation_join` (attach
    columns) and `optimizer/hints.py::hint_is_skip` /
    `optimizer/hints.py::OptimizerHint`.
  - The same build path reaches `optimizer/plans.py::lookup_paths`,
    `optimizer/plans.py::prune_unsupportable_select_related`,
    `optimizer/plans.py::diff_plan_for_queryset`, and
    `optimizer/plans.py::window_partition_for_prefetch` (shim over
    `classify_relation_join`); and the nested pipeline reaches
    `optimizer/nested_planner.py::plan_connection_relation`, which calls
    `classify_relation_join` for `join.partition_expr` /
    `join.parent_join_column` / `prefetch_attach_columns` and resolves
    per-field strategy overrides.
- Role: extension is an INDIRECT consumer (plan-application layer); the
  authoritative DEFINITION for every join-derived fact (`windowable`,
  `partition_expr`, `parent_join_column`, `through_model`,
  `lateral_shape`, `parent_link_field`, `through_child_field`,
  `content_type_column`, `prefetch_attach_columns`) is
  `optimizer/join_taxonomy.py::classify_relation_join` with its private
  readers (`_partition_expr`, `_parent_join_column`, `_through_model`,
  `_through_link_fields`, `_generic_child_attname`) and the new
  `_child_link_is_virtual` predicate.
- Contract consumed transitively: pure, side-effect-free, never-raises
  classification of one raw Django relation field; unresolvable shapes
  degrade (`windowable=False` / `None` columns) and the CALLER decides
  the fallback posture. The extension duplicates none of it: no
  `remote_field.attname`, no `reverse_connector_attname`, no
  `concrete is False` read of its own.
- What the dirt touches: the +39 hunk adds `_child_link_is_virtual`
  (positive `concrete is False` test) and three degrade-to-per-parent
  arms (`_partition_expr` returns `None` for virtual reverse links;
  `_parent_join_column` returns `None` for virtual reverse links;
  `classify_relation_join` clears `parent_link_field` for virtual
  links). All three sit strictly inside the taxonomy owner; no arm
  lands in the extension.

#### (c) Nested-fetch strategies (`optimizer/nested_fetch.py`)

- Direct consumes (two symbols):
  - `optimizer/nested_fetch.py::resolve_strategy`, called at exactly two
    sites: `optimizer/extension.py::DjangoOptimizerExtension.__init__`
    (`resolve_strategy(nested_connection_strategy)` pins the
    instance-bound strategy at construction) and
    `optimizer/extension.py::DjangoOptimizerExtension._configuration`
    (the subclass-skipped-constructor fallback
    `resolve_strategy(None)` reads the `NESTED_CONNECTION_STRATEGY`
    setting, defaulting to windowed).
  - `optimizer/nested_fetch.py::StrategySelection`, used as the
    annotation on the `__init__` `nested_connection_strategy` parameter
    (the `_AcceptedOptimizerConfiguration.nested_connection_strategy`
    slot itself is typed `Any` holding the resolved instance).
- Producer direction (same seam, opposite flow): `on_execute` publishes
  the pinned instance into the execution frame
  (`strategy=self.nested_connection_strategy`); the walker reads it back
  through `optimizer/nested_fetch.py::active_strategy` (frame value or
  `WINDOWED_STRATEGY` default). The extension therefore CONSUMES the
  validator and PRODUCES the per-execution strategy value; it never
  selects a backend per request.
- Role: extension is a CONSUMER of strategy validation and the
  instance-binding lifecycle; the authoritative DEFINITIONS
  (`NestedConnectionStrategy` protocol, `StrategySelection` alias,
  `WINDOWED_STRATEGY` / `AUTO_STRATEGY` singletons, `_builtin_strategies`
  registry, `resolve_strategy`, `active_strategy`,
  `attach_windowed_prefetch`, `WindowedPrefetchStrategy`,
  `AutoNestedConnectionStrategy`) all live in `optimizer/nested_fetch.py`
  (with the Postgres backend in `optimizer/lateral_fetch.py` behind the
  registry). The extension defines zero strategies and zero registry.
- Contract consumed: strategy selection is fixed per extension INSTANCE
  at construction; the plan cache is instance-bound so one cache never
  mixes plans from two strategies; `"auto"` is one stable
  lateral-capable windowed strategy whose queryset selects by fetch-time
  alias (cached plans stay backend-neutral); per-field
  `OptimizerHint.strategy(...)` overrides are schema-static and need no
  plan-cache-key change. Unknown names raise typed `ConfigurationError`
  at construction, not at query time.
- What the dirt touches: the +28 hunk hardens `resolve_strategy`'s two
  interrogations (`type()` + `issubclass(type(value), str)` instead of
  `isinstance(value, str)`; guarded `isinstance(value, type)` for the
  class check) so hostile `__class__` values degrade to the typed
  `ConfigurationError` instead of escaping raw. Both hardened gates sit
  on the extension's exact call path (construction-time selection).

### 2. Plan-cache key inputs (does any key input come from the dirtied regions?)

No. Derived from `optimizer/extension.py::DjangoOptimizerExtension._build_cache_key`
(current bytes):

- Key tuple (5 elements): (1) `doc_key`: `print_ast(operation)` plus the
  printed reachable fragment bodies
  (`_print_operation_with_reachable_fragments` /
  `_collect_reachable_fragment_definitions`; cross-request memoized in
  `_doc_key_cache` keyed by `(source.body, operation_name)`, with a
  no-`loc` direct-compute fallback); (2) `relevant_vars`: frozenset of
  `(name, _hashable_variable_value(value))` for the union of directive
  (`@skip` / `@include`) and nested-pagination (`first | last | before |
  after` on depth >= 1 field nodes) variable NAMES, resolved against
  `info.variable_values` (per-execution memoized in the frame's
  `_cache_key_parts_memo` by `id(operation)`); (3) `target_model`;
  (4) `runtime_path_from_info(info)` (root response path); (5) `origin`
  (resolver's Strawberry return type, `None` for direct/test callers).
- Dirt-region audit against the key path:
  - Hints dirt (`_require_prefetch` guard): construction-time validator;
    never called during `_build_cache_key`. `hint_is_skip` (the
    extension's only hints call) is audit-time, not key-time.
  - Join-taxonomy dirt (`_child_link_is_virtual` + degrade arms):
    affects planned plan CONTENT (windowed vs per-parent fallback) via
    the walker/planner, never a key element. Join descriptors are not
    keyed.
  - Nested-fetch dirt (`resolve_strategy` hardening): affects which
    strategy INSTANCE the extension is bound to (and hence which cache
    object exists), never a key element. Strategy is DELIBERATELY
    excluded from the key by the instance-bound-cache contract: one
    instance serves one strategy, so keying it would be redundant; a
    per-field `nested_strategy` override is schema-static (same hint ->
    same plan for the same document key).
- Therefore no key input comes from any dirtied region, and no key-shape
  change is owed by any of the three hunks. (Lifetime note under
  principle 4: the cross-request `_plan_cache` owner is the extension
  instance; validity key is the 5-tuple above; publish point is
  `_get_or_build_plan` insertion iff `plan.cacheable` with quarter-LRU
  eviction; the per-execution `_execution_plan_memo` reuses uncacheable
  plans within one execution only and never touches hit/miss counters.)

### 3. Definition counts

Counts are authoritative DEFINITIONS (independently maintained
implementations/declarations); consumers, oracles, and prose are listed
separately and not counted.

- New hint form: 0. The hunk adds a guard, not a form. Authoritative hint
  vocabulary remains single-owned in `optimizer/hints.py`: one
  `OptimizerHint` record (5 directive slots: `force_select`,
  `force_prefetch`, `prefetch_obj`, `skip`, `nested_strategy`), one
  `SKIP` sentinel, one `_require_prefetch`, one `_require_strategy`, one
  `hint_is_skip`. The extension defines 0 hint forms and calls 1 helper
  (`hint_is_skip`); the walker is the second consumer (validation +
  `_apply_hint` dispatch), not a second definition. Oracles:
  `tests/optimizer/test_hints.py` (unit) and the live
  `test_library_optimizer_hints_are_observable_over_http` envelope named
  in its docstring.
- New join shape: 0. `LateralJoinShape` still has exactly 3 members
  (`DIRECT_FK`, `THROUGH_TABLE`, `UNSUPPORTED`); no `GENERIC` arm was
  added (generic stays `DIRECT_FK` with `parent_link_field=None` by
  design). The hunk adds one private predicate
  (`_child_link_is_virtual`) and three degrade arms inside existing
  readers, all inside the single owner `optimizer/join_taxonomy.py`.
  The extension defines 0 join classifiers and imports 0 join symbols;
  `walker.py` / `plans.py` / `nested_planner.py` consume by name through
  `classify_relation_join` (plus the `WINDOWABLE_RELATION_KINDS`
  membership set shared with the `window_partition_for_prefetch` shim).
  Oracles: `tests/optimizer/test_join_taxonomy.py` (unit) plus the live
  single-parent-fastpath and auto-strategy API suites named in its
  docstring.
- New fetch strategy: 0. The hunk hardens selection, adds no backend.
  Built-in registry still resolves exactly 2 names (`windowed`,
  `lateral`) plus the stable `"auto"` singleton
  (`WINDOWED_STRATEGY`, `AUTO_STRATEGY`; `LATERAL_STRATEGY` owned in
  `lateral_fetch.py`). One `StrategySelection` alias, one
  `resolve_strategy`, one `active_strategy`, all owned in
  `optimizer/nested_fetch.py`. The extension defines 0 strategies and
  consumes 2 symbols (`resolve_strategy`, `StrategySelection` annotation);
  `hints.py` consumes the same 2 at runtime for the `nested_strategy`
  field/factory (verified acyclic: `nested_fetch` never imports `hints`).
  Oracles: `tests/optimizer/test_nested_fetch.py` (unit) plus the live
  `test_optimizer_auto_api` routed-SQL suite named in its docstring.
- Near-duplicate judged, not counted: `extension.py::_is_valid_strictness`
  (strictness vocabulary gate) vs `nested_fetch.py::resolve_strategy`
  (strategy selection gate) share the base-`str`-slot technique for
  hostile dunders but own disjoint vocabularies with disjoint reasons to
  change (N+1 strictness modes vs fetch backends). Similar-looking is
  not duplication; both stay.

### 4. Owners I would choose (principle 7; lifetimes under principle 4)

- Hints vocabulary: `optimizer/hints.py` (existing owner). It already
  carries the responsibility every consumer needs (typed declaration,
  construction-time rejection, shape dispatch), and both legitimate
  consumers (`walker.py` for planning, `extension.py::check_schema` for
  audit) can depend on it without reversing any dependency. The
  extension stays a `hint_is_skip` consumer. No stored derivation here;
  `SKIP` is a frozen sentinel with process lifetime, not a cache.
- Join taxonomy: `optimizer/join_taxonomy.py` (existing owner). It is the
  narrowest cohesive owner every fetch strategy and planner can depend
  on (raw-field in, descriptor out, never raises); the extension must
  NOT gain a direct join import (that would reverse the layering:
  plan-application reaching past the walker/planner into field
  internals). Transitive consumption by name stays. Lifetime: the
  descriptor is a pure per-plan derivation with plan lifetime only
  (no cache of its own); the plan it feeds is owned as in the key
  section above.
- Fetch strategies: `optimizer/nested_fetch.py` (existing owner). It owns
  the protocol, the registry, validation, and the active-strategy seam
  beside the strategy that needs them; the extension is the lifecycle
  owner of exactly one thing: the instance-bound pin
  (`_OPTIMIZER_CONFIGURATION` private authority + `_plan_cache` +
  counters) with process lifetime, published per execution through the
  frame `on_execute` opens. Strategy values themselves are stateless
  singletons (process lifetime, shared). No per-request strategy state
  is stored anywhere, by contract.
- In short: change nothing about ownership. Each family already has
  exactly one authoritative definition, and the extension already
  composes all three by name (direct for hints/strategy validation,
  transitive for joins).

### 5. Whether any dirt breaks anything derived

No dirt breaks anything derived below. No defect is proposed (a defect
requires a named contract row plus a reaching wire/config input; none
obtains). Planner-adjacent observable behavior is stated explicitly
because planner changes are N+1/correctness-adjacent.

- (a) Hints +13 (`_require_prefetch` hostile-`__class__` guard +
  `_safe_type_name` rendering). Holds: `check_schema` output for every
  reachable input is unchanged (its only hints call is `hint_is_skip`,
  untouched); walker hint dispatch for `SKIP` / force / prefetch /
  strategy forms is unchanged; the sole observable delta is at the typed
  boundary itself: a `prefetch(obj)` / `prefetch_obj=` value whose
  `__class__` raises now raises the documented typed
  `ConfigurationError` (with a safe label) instead of escaping the raw
  `__class__` exception. Reaching input: a consumer passing such a
  hostile object in `Meta.optimizer_hints` at type-declaration time.
  That is the intended hardening, not a break; no cache, audit, or plan
  behavior moves.
- (b) Join taxonomy +39 (`_child_link_is_virtual` + degrade arms for
  multi-column ForeignObject / composite-pk links). Holds: every
  previously plannable single-column shape classifies byte-identically
  (the virtual test requires positively-declared `concrete is False`,
  so duck-typed doubles keeping the historical truthy-attname read are
  unaffected); the newly-degraded shape (virtual child link) resolves
  `partition_expr=None` / `parent_join_column=None` /
  `parent_link_field=None`, hence `windowable=False`, and the caller
  degrades to per-parent resolution instead of planning a window over a
  poisoned attname (the same poisoned-attname shape
  `field_meta.py::_from_field_shape` drops). Reaching input: a nested
  Relay connection over a multi-column `ForeignObject` (composite-pk
  reference). Observably: correctness holds (no mis-windowed page, no
  wrong attach); cost moves the honest direction (per-parent queries,
  strictness-visible) until a composite-aware planner lands. No
  plan-cache-key change is owed (key carries no join facts; the
  in-memory LRU does not survive a deploy, so no stale-plan interlock).
- (c) Nested fetch +28 (`resolve_strategy` hardening). Holds: all
  previously valid selections (`None` -> setting -> windowed default,
  `"windowed" | "lateral" | "auto"`, custom instance with callable
  `plan`) resolve to the identical instance; all previously invalid
  names/instances still raise the identical typed `ConfigurationError`.
  The sole observable delta is for hostile selections (raising/spoofed
  `__class__`, hostile `__eq__`/`__hash__`/`__repr__`/raising `plan`
  descriptor): they now deterministically reach the typed
  `ConfigurationError` instead of escaping raw or forcing a false
  registry match. Reaching inputs: `nested_connection_strategy=` at
  `DjangoOptimizerExtension(...)` construction, or
  `OptimizerHint.strategy(name)` at hint construction (which routes
  through the same resolver). No cached plan changes identity (strategy
  is instance-bound, not keyed), so no key or invalidation work is owed.
- Net for the extension surface: root gating, return-type tracing,
  `_optimize`/`apply_to`/`_get_or_build_plan`/`_publish_plan_to_context`
  behavior, strictness vocabulary, pagination/directive key families,
  and the 5-tuple key shape all still hold at current bytes. Three
  hardenings compose without touching the extension body (which is
  clean).

### 6. Freshness fingerprints

Commit: `bfaee91dcd332a5f86250fff90ab21b377bc674e`.

| Path | HEAD blob | Worktree blob | State |
| --- | --- | --- | --- |
| `django_strawberry_framework/optimizer/extension.py` | `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a` | `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a` | clean, confirmed (hashes equal) |
| `django_strawberry_framework/optimizer/hints.py` | `da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74` | `8064af14930636d6b12a538a996603ccadfdb420` | dirty (+13, attributed above) |
| `django_strawberry_framework/optimizer/join_taxonomy.py` | `9b355a5090ce471e373849dd0a61da8f808e78b9` | `e1cbb3e327785de3b59ccafef6b463df52e06396` | dirty (+39, attributed above) |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `4d8d37a7f52cf94d2916f17db3a8a21393e28d57` | `29ce5201877864b01079c849b92a1e812166affd` | dirty (+28, attributed above) |

Transitive/oracle files touched only for symbol placement or header
contracts (concurrent dirt noted, NOT attributed, left preserved):

| Path | HEAD blob | Worktree blob | State |
| --- | --- | --- | --- |
| `django_strawberry_framework/optimizer/walker.py` | `9b111ed938951a073a9226ccbcfacabc3af981e8` | `9b111ed938951a073a9226ccbcfacabc3af981e8` | clean |
| `django_strawberry_framework/optimizer/plans.py` | `cce985319c8833f3660653327d3003f1f03655a5` | `cce985319c8833f3660653327d3003f1f03655a5` | clean |
| `django_strawberry_framework/optimizer/nested_planner.py` | `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04` | `e69dbf5f30aa4623a5aad93edfacdabb391d6601` | dirty, concurrent, out of scope |
| `tests/optimizer/test_hints.py` | `d3e413bdc0e93d791399c023a442f6701416b5a1` | `90253a19a5c9b3a0515eba78ab2d4241899f9e24` | dirty, concurrent, out of scope |
| `tests/optimizer/test_join_taxonomy.py` | `481294c323dd0ef2e8f7bf974802858c3b5b428c` | `5c269157afcccc668d80a96f9c4021a1c4a20991` | dirty, concurrent, out of scope |
| `tests/optimizer/test_nested_fetch.py` | `7fbd957b4f8c4fe64c7c7f7f997605545a86edea` | `58902461189cbe64454de1eb3f5811c2e85c4a31` | dirty, concurrent, out of scope |
| `tests/optimizer/test_extension.py` | `4e60f0b7ab8777dc0fd9c95bdf3950884ca937b5` | `883720eed4aed462d3804d0106db71749abd74ac` | dirty, concurrent, out of scope |

Blob method: `git hash-object <worktree path>` for worktree bytes;
`git rev-parse HEAD:<path>` for the verified baseline. Any fingerprint
change reopens this trace. No status set; no verdict on prior findings
proposed.

PHASE-1-TRACE-RECORDED plus the artifact path:
`docs/dry/dry-file-optimizer__extension.md`

## Iterations

### Scoped re-trace (run 7, stale7-1) — drift `5ee86193..0c0537e2`

Prior sections stand as evidence about `5ee86193` bytes (target blob
`49667a93`, reproduced). This pass traces HEAD `0c0537e2` bytes only
(target blob `e0e53a8e`; worktree `39a8739c` is hunt dirt, left alone,
fingerprinted here and never read for verdicts). No tracked path
touched; no workspace run needed (read-only `git show` / `git grep`
against `0c0537e2` plus AST dumps of both blobs to OS temp).

Drift `git diff 5ee86193..0c0537e2 --
django_strawberry_framework/optimizer/extension.py` (45+/5-, two
commits: `59f8b105` clear members, `982537c3` combined passthrough),
hunks by content:

- H1: `from ..registry import registry` widens to `from ..registry
  import register_subsystem_clear, registry` (import line only).
- H2: new module def `clear_document_key_cache()` (one-line
  `_doc_key_cache.clear()` body plus docstring) followed by the
  module-level Expr `register_subsystem_clear(clear_document_key_cache,
  owner="optimizer.document_key_cache")`, inserted between the
  `_doc_key_cache` assign and `def _doc_cache_entry`.
- H3: new method `DjangoOptimizerExtension.cache_clear()` (clears
  `self._plan_cache`, zeroes both counters, plus docstring),
  inserted between `cache_info` and `on_execute`.
- H4: `_optimize` docstring gains one sentence ("A combined queryset
  passes through `apply_to` unplanned."). Prose only.
- H5: `apply_to` docstring gains the combined arm (returns unchanged
  when combined; Django `NotSupportedError` rationale; no plan
  published; strictness-visible via `_check_n1`) plus the code arm
  `if queryset.query.combinator:` with a `logger.debug` and early
  `return queryset`, placed between the `field_nodes` early return
  and the walker-selection build.
- H6: `apply_connection_optimization` docstring gains the
  pass-through clause. Prose only.

Hunks examined for every disposition below; unrelated hunks are
excluded per finding with the reason. Fingerprints refreshed to HEAD
blobs on every REVISE.

#### Dispositions

- Enumeration: REVISE. Same instrument (`ast.Module.body`) re-run on
  both blobs. Base reproduces the record exactly (77 = 1 docstring +
  39 imports + 14 assigns + 18 defs + 5 classes; name lists match).
  HEAD: **79** = 1 docstring + 39 imports + 14 assigns (same names,
  same order) + **19 defs** (+`clear_document_key_cache`) + 5 classes
  + 1 registration Expr (H2's `register_subsystem_clear(...)` call;
  homed with the def it registers, not a named member). Method-level
  17 -> **18** (+`cache_clear` on `DjangoOptimizerExtension`; all
  other method lists identical). H1 moves no count (import widens in
  place); H4/H5/H6 move no count (arm + prose inside existing
  members). New-member homes: `clear_document_key_cache` +
  registration Expr -> FL1-REVISE (lifecycle adapter over the doc-key
  memo; lawful convergence onto verified `subsystem-clear-lifecycle`,
  index row R-NEW1 below); `cache_clear` -> FL7-REVISE (reset half of
  the introspection pair, index row R-NEW2 below). No member
  unassigned at HEAD.
- FL1 plan-cache key + two-tier memo: REVISE (extend, count stays
  1). H2 clears FL1's `_doc_key_cache` but defines no second memo:
  the callback is a lifecycle adapter in exactly the holding
  family's C1 shape (one register line + its callback; the bus needs
  no change). Challenge: "drain the doc-key memo on registry clear"
  -> 1 (this callback + line). The memo rule itself (`_doc_cache_entry`
  + cache + bound + key tuple) is untouched: the single diff line
  naming `_doc_cache_entry` is a context line (the unchanged `def`
  below the insertion), and no hunk names `_build_cache_key`,
  `relevant_vars`, or the 5-tuple. H1/H3/H4/H5/H6 do not invalidate:
  H1 is the import the registration composes by name; H3 clears the
  disjoint instance plan cache (FL7 side); H4/H5/H6 live in the
  plan-application tail, downstream of keying. Oracles: drift-new
  `test_registry_clear_empties_the_document_key_cache`
  (bus-membership pin + emptying; satisfies the family P6 row-pin
  requirement). Freshness: ext `e0e53a8e`.
- FL7 cache bounds + best-effort introspection: REVISE (extend,
  count stays 1). H3 joins `cache_info` as the reset half of the
  instance plan-cache pair (bound + eviction + read + reset, one
  rule). Challenge: "reset semantics change (e.g. clear preserves
  counters)" -> 1 (this method). Zero production callers at HEAD
  (public maintenance affordance, like `cache_info`); oracle:
  drift-new `test_cache_clear_makes_the_next_request_build_its_plan_again`
  (counters + rebuild, literal expectations). Same-name
  `cache_clear`s in `utils/relations.py` /
  `utils/strings.py` are attached functools-cache clears on pure
  derivations (attribute assignment, different mechanism, owners,
  state): similar-looking, not duplication. H1/H2/H4/H5/H6 do not
  invalidate: H2 clears the disjoint module doc-key memo (FL1 side);
  the rest are import/prose/tail. Freshness: ext `e0e53a8e`.
- FL11 plan-build-and-apply tail: REVISE (extend, count stays 1).
  H5 adds a third return-unchanged arm (no field nodes / combined /
  empty plan). The arm is a **consumer branch**, not a definition:
  it reads Django's own `Query.combinator` slot (framework
  vocabulary, not a package rule) and reuses the tail's stated
  return-unchanged shape. Challenge: "a combined root must plan"
  -> 1 (this arm). No second definition of one rule: the three
  sibling executable combinator reads at HEAD have disjoint
  contracts, verified at HEAD bytes --
  `nested_fetch.py::unwindowable_child_queryset_reason` classifies to
  a reason string (`"combined"`/`None`, lenient `getattr` reads);
  `predicates.py::attach_exists` raises `OptimizerError` when
  attachment is required; `utils/querysets.py` seal machinery returns
  a `("combined", ...)` defect tuple under `reject_combined` --
  versus this arm's silent passthrough + debug log + no publish.
  Different inputs, outputs, and reasons to change; the shared slot
  read is Django's. H1/H2/H3/H4/H6 do not invalidate: H4/H6 are prose
  projections of this same arm; H1/H2/H3 clear caches, never branch
  the tail. Oracle: drift-new
  `test_apply_to_returns_a_combined_queryset_unplanned` (identity +
  zero misses + log wording; `field_nodes` non-empty so the skip is
  the combinator check). Freshness: ext `e0e53a8e`.
- F1 `optimizer-execution-frame`: CONFIRM. Sole-caller census
  re-derived at HEAD: `begin`/`clear`/`end` called only from
  extension.py (HEAD lines 1078/1094/1098; no other production caller
  package-wide). The "holds no frame state" sentence stands,
  extended: H2/H3 are lifecycle adapters over the cross-request
  module memo and the instance plan cache respectively; neither
  enters the frame. H4/H5/H6 do not invalidate (tail interior +
  prose, frame calls untouched). Freshness: ext `e0e53a8e`,
  [ctx][ctx] `dbc30630` (STALE-bytes, prose-only docstring first
  line, conclusion untouched).
- FL10 root gate + optimize pipeline: CONFIRM. H4 is a one-sentence
  docstring projection of the FL11 arm onto `_optimize`; the G1
  placement rule (after Manager coercion, before resolution/clone)
  and its lines are untouched. No other hunk names `_optimize`.
- FL15 connection cooperation point: CONFIRM. H6 is a docstring-only
  projection of the FL11 arm; no code. Caller census re-derived at
  HEAD: executable calls only from `connection.py:1727` and
  `mutations/resolvers.py:765` (same two; remaining matches are
  imports/docstring mentions). No hunk touches the short-circuit or
  the extractor forwarding.
- Matrix axis 1 (callers): CONFIRM. `apply_to` callers re-derived at
  HEAD: `_optimize` (line 1198) + `apply_connection_optimization`
  (line 1652), same two; `SelectionExtractor` parameterization
  untouched. No hunk adds a plan-application body.
- Matrix axis 3 (derivations): CONFIRM. Doc-key derivation still
  single (`_doc_cache_entry` untouched, key tuple untouched);
  `clear_document_key_cache` derives nothing (pure `.clear()`);
  registry reads still composed by name (H1 adds
  `register_subsystem_clear` to the composed set; no local map).
- Matrix axis 5 (oracles): CONFIRM. Three drift-new oracles, all
  behavior-asserting with literal expectations: identity/counters/
  rebuild, membership pin + emptying (the family-prescribed P6
  row-pin, not a bespoke gate), log wording. The memo test resets the
  module global via `monkeypatch` and asserts `len` emptiness --
  behavior observation, never computes expectations from owner
  tables. The one deleted package test
  (`test_optimizer_prefetches_reverse_fk_without_related_name`,
  walker-owned accessor-lookup behavior no finding cites) was
  promoted to the live tier per the module-docstring rewrite
  (`test_library_inheritance_api.py`, present at HEAD): no oracle
  loss.
- Matrix axis 6 (omission): CONFIRM. H5 adds one stated asymmetry
  (combined -> unplanned + unpublished, strictness-visible via
  `_check_n1`, fail-loud direction), same verdict shape as the
  standing rows. The G1 scoping verdict stands: no hunk changes
  where either path's queryset comes from, so no consumer-evaluated
  source is introduced on the connection path; the unpublished-plan
  consequence is stated in the body and pinned by the oracle.
  Investigated, not a gap, no defect.
- Q10 Phase-1 trace: CONFIRM (extension-side cells), one flag. Key
  tuple untouched (context-line-only match, see FL1); no join import
  in extension.py at HEAD (zero matches); `hint_is_skip` still
  imported once + called once (`check_schema`, line 1487);
  `resolve_strategy` still two call sites (`__init__` line 974,
  `_configuration` line 1000) + `StrategySelection` annotation (line
  939; the third match is pre-existing docstring prose);
  nested_planner still imports/calls `classify_relation_join` and
  resolves `nested_strategy` overrides at HEAD. New-form counts stay
  0/0/0 (no hint form, join shape, or strategy in the drift).
  FLAG for Worker-0 (not adjudicated here): Q10 walker-interior
  cells (transitive-consume detail, caller-degrades behavior) sit on
  walker.py bytes STALE under the separately REOPENED walker item;
  they ride with that item's re-trace.
- STAND without re-review (no drift hunk touches their reasoning):
  F2, F3 (querysets-drift spot-check as diligence only: the
  63+/35- names none of `_AsyncQuerySetRows` /
  `wrap_async_queryset_adapter` / `unwrap_async_queryset_adapter`,
  and the single `normalize_query_source` diff line is unchanged
  docstring context), F4, FL2, FL3, FL4, FL5, FL6, FL8, FL9, FL12,
  FL13, FL14, FL16 (`__all__` untouched -- neither new member is
  exported; tests import the module directly), FL17, FL18, R1 (no
  eviction change), R2, R3, R4 (neither non-membership gains a site;
  the new bus membership is FL1's convergence, not an R4 family),
  matrix axes 2 and 4, `## Defects` (none; none found).

#### Definition-count judgments

- The new clear member moves NO definition count; it extends the
  verified `subsystem-clear-lifecycle` membership census only. Bus
  mechanism still one definition set (`registry.py`: dict + register
  + iter + `clear()` replay tail; registry drift is a prose-only
  `discard_pending` docstring reword, `9cc8bb55` -> `81bd561c`).
  The family's own C1 ("new subsystem with caches -> 1, the bus
  needs no change") predicts exactly this outcome, so the drift
  confirms the family verdict rather than disturbing it: H2 is the
  18th adapter row (`optimizer.document_key_cache`, full-clear,
  one-liner `.clear()` over `_doc_key_cache`, same shape as family
  rows 1-4/17), with its own row-pinning test per P6. Family
  observation (c)'s trigger fires constructively (a concrete cache
  appeared WITH registration + its test): still no card owed.
  HEAD census note: production `register_subsystem_clear(` call
  sites total 19 = family 17 + this row + one walker.py row that is
  likewise drift-new (absent at `5ee86193`) and owned by the
  separately REOPENED walker item -- Worker-0 routes that half.
  Holding-family consequence: verified `subsystem-clear-lifecycle`
  verdict stands; census note owed (recommend flagged-not-reopened,
  same handling as the querysets re-trace's `one-sync-boundary`
  flag). Worker-0 transcribes; nothing authored here.
- The combined passthrough is a consumer branch of the single-owned
  FL11 tail (see FL11-REVISE): a definition count of 1, unchanged.
  It is neither a new definition nor (the "neither" horn) a no-op:
  it adds executable behavior (early return + log + no publish) to
  the one existing tail. No holding family exists for it; FL11 stays
  file-local.

#### Fingerprint table (re-hashed at HEAD `0c0537e2`)

Findings inputs (recorded at `5ee86193`-era bytes):

| Input | Recorded | HEAD now | State |
|---|---|---|---|
| `optimizer/extension.py` | `49667a93` | `e0e53a8e` | STALE (this drift, adjudicated here) |
| `optimizer/_context.py` | `3d8dcfdf` | `dbc30630` | STALE (1-line docstring prose; F1 untouched) |
| `extensions/operation_state.py` | `b2674a22` | `b2674a22` | MATCH |
| `utils/context.py` | `cd0adcc5` | `cd0adcc5` | MATCH |
| `utils/querysets.py` | `1539b66c` | `3616927d` | STALE (63+/35-, adjudicated by item b1 verified; F3 symbols untouched, see above) |
| `registry.py` | `9cc8bb55` | `81bd561c` | STALE (prose-only `discard_pending` reword; F4 reads untouched) |

Q10 inputs (recorded at `bfaee91d`):

| Input | Recorded | HEAD now | State |
|---|---|---|---|
| `optimizer/hints.py` | `da46ef89` | `da46ef89` | MATCH |
| `optimizer/join_taxonomy.py` | `9b355a50` | `9b355a50` | MATCH |
| `optimizer/nested_fetch.py` | `4d8d37a7` | `4d8d37a7` | MATCH |
| `optimizer/walker.py` | `9b111ed9` | `75f9c6b6` | STALE (144+/37-, REOPENED walker item; Q10 walker-interior cells flagged above) |
| `optimizer/plans.py` | `cce98531` | `cce98531` | MATCH |
| `optimizer/nested_planner.py` | `0ad8ff5d` | `b4dfd4a6` | STALE pre-window (`bfaee91d..5ee86193`, zero drift in `5ee86193..0c0537e2`; verified run 5 at this blob; Q10 cells re-verified at HEAD above) |
| `tests/optimizer/test_hints.py` | `d3e413bd` | `d3e413bd` | MATCH |
| `tests/optimizer/test_join_taxonomy.py` | `481294c3` | `481294c3` | MATCH |
| `tests/optimizer/test_nested_fetch.py` | `7fbd957b` | `7fbd957b` | MATCH |
| `tests/optimizer/test_extension.py` | `4e60f0b7` | `912cd47f` | STALE (77+/83-: 3 new oracles + import/docstring; 85-line deletion is the live-promoted accessor test, no oracle loss) |

Result: 6 MATCH / 10 STALE, every STALE with its cause; no finding
rests on unexamined bytes.

#### Index rows (literal, 5-column, for Worker-0 verbatim transcription)

The plan carries no rows held by File `optimizer/extension.py`; these
two cover the drift-new enumeration members (challenges recorded
under FL1-REVISE / FL7-REVISE above):

| Document-key memo clear row on the subsystem-clear bus | `django_strawberry_framework/optimizer/extension.py::clear_document_key_cache` + bus registration (declaration here; lawful convergence onto verified `subsystem-clear-lifecycle` as a drift-new full-clear member) | `django_strawberry_framework/optimizer/extension.py` | File `optimizer/extension.py` | file-local |
| Instance plan-cache clear plus counter reset | `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.cache_clear` | `django_strawberry_framework/optimizer/extension.py` | File `optimizer/extension.py` | file-local |

#### Attribution and sandbox

Item touches the artifact only (untracked `??`, purely additive; no
`## Owned changes` path, no cycle-baseline path, no stop). Every hunk
relied on is committed drift attributed by diff content above
(H1-H6); worktree dirt (303 paths incl. target `39a8739c`) left
alone. No source-mutating probe: zero workspace runs (read-only
inspection per the sandbox rule), zero `.py` touched so no ruff owed.
`ITEM_BASELINE=919e9ef4...` resolves; window diff vs baseline must
name only the plan (Worker-0's) plus this artifact.

## Independent verification (Worker-2) — stale7 re-trace

Verdict: `verified`. Scoped run `0.0.15 2026-09-28-7`, HEAD
`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62` at start and finish,
unmoved. Target HEAD blob `e0e53a8e`, worktree `39a8739c` (hunt
dirt, concurrent work); every claim below traced at HEAD bytes via
`git show HEAD:<path>`, `git rev-parse HEAD:<path>`, and `git grep`,
plus read-only AST dumps of both blobs to `/tmp/` (cited by content;
OS temp, rides with the scratch-custody closeout decision). No
workspace built, no run id exists, no pytest spent: nothing mutates
source and every claim is decided by HEAD-byte inspection. The
dispatch brief summarized W1's dispositions, so true blindness was
unavailable; every number below was re-derived by my own commands,
never trusted from W1's record.

### Own trace (re-derived before reconciling)

Drift hunks, own derivation. `git diff 5ee86193..0c0537e2 --
django_strawberry_framework/optimizer/extension.py` is 45+/5- over
two commits (`59f8b105` clear members, `982537c3` combined
passthrough): H1 import widens to include
`register_subsystem_clear`; H2 new `clear_document_key_cache` def +
registration Expr; H3 new `cache_clear` method; H4 `_optimize`
docstring sentence; H5 `apply_to` docstring + `if
queryset.query.combinator` arm; H6
`apply_connection_optimization` docstring. Regions outside the hunks
are byte-identical to the base.

Per-finding expectations, own: REVISE enumeration (77→79, 17→18) +
FL1 (clear adapter) + FL7 (reset half) + FL11 (consumer branch);
CONFIRM F1/FL10/FL15 + axes 1/3/5/6 + Q10 extension-side cells;
STAND the rest incl. defects-none.

Three judgments the dispatch names, own answers. (1) The doc-key
clear is a lifecycle adapter, not a second memo: the callback is a
one-line `.clear()` over FL1's existing `_doc_key_cache` and the
registration is a bus declaration; the memo rule
(`_doc_cache_entry` + cache + bound + key tuple) is untouched (the
single `_doc_cache_entry` diff line is unchanged context, and no
hunk names `_build_cache_key`, `relevant_vars`, or the 5-tuple).
(2) `cache_clear` is the reset half of the introspection pair, not
a new definition: bound + eviction + read (`cache_info`) + reset
(this method) is one rule; zero production callers (public
maintenance affordance); the same-name clears in
`utils/relations.py` / `utils/strings.py` are attached lru-cache
clears (attribute assignment, different mechanism, owners, state).
(3) The combined passthrough is a consumer branch of the
single-owned FL11 tail, count 1: it reads Django's own
`Query.combinator` slot and reuses the tail's stated
return-unchanged shape; it adds executable behavior (early return +
log + no publish) so it is not the "neither" horn. The three
sibling executable combinator reads share no package rule:
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
classifies to a reason string (`"combined"`/`None`, lenient
`getattr` reads); `optimizer/predicates.py::attach_exists` raises
`OptimizerError` when attachment is required;
`utils/querysets.py` seal machinery returns a `("combined", ...)`
defect tuple under `reject_combined` — versus this arm's silent
passthrough + debug log + no publish. Disjoint inputs, outputs,
and reasons to change; the shared slot read is Django's.
Package-wide census finds exactly these four executable reads
(prose/comment mentions excluded).

Enumeration, own instrument (`ast.Module.body`): base 77 = 1
docstring + 39 imports (4 Import + 35 ImportFrom) + 14 assigns (12
Assign + 2 AnnAssign) + 18 defs + 5 classes; HEAD 79 = 1 docstring
+ 39 imports + 14 assigns (same names, same order) + 19 defs
(+`clear_document_key_cache`) + 5 classes + 1 registration Expr.
Method-level 17→18 (+`cache_clear` between `cache_info` and
`on_execute`). Zero removals, zero renames. Homes:
`clear_document_key_cache` + Expr → FL1 (lifecycle adapter, lawful
convergence onto verified `subsystem-clear-lifecycle`);
`cache_clear` → FL7 (reset half).

Matrix: no axis reopens beyond the drift scope — no new
plan-application body (callers still two), no new colored pair
(both clears sync, the arm sync), no new derived fact (the clear
derives nothing), no new round-trip half, no new medium
(docstrings project the arm), one new stated asymmetry (combined,
fail-loud direction).

### Reconciliation (every difference, explicitly)

AGREE on all: REVISE enumeration/FL1/FL7/FL11, CONFIRM
F1/FL10/FL15 + axes 1/3/5/6 + Q10 extension-side cells, STAND the
rest. Zero verdict or count differences. Three immaterial
STALE-cause completions (no home, count, or verdict moves):

1. Querysets recorded `1539b66c` predates the window (base at
   `5ee86193` is `b68be0e3`; pre-window `9031cb3d..5ee86193` is
   259+/64-). Both ranges name none of `_AsyncQuerySetRows` /
   wrap / unwrap (window zero hits re-derived; pre-window zero
   hits by my own grep), and the single `normalize_query_source`
   window line is unchanged docstring context. F3 STAND holds;
   the cause should cite both ranges.
2. Walker recorded `9b111ed9` (bfa) → `e8d80005` (5ee, 54+/6-
   pre-window) → `75f9c6b6` (HEAD, 144+/37- window). The cause
   cites the window only; the pre-window part also exists. The
   disposition (FLAG walker-interior cells to ride with the
   walker item) is correct regardless — that item traces HEAD
   bytes.
3. Tests/extension recorded `4e60f0b7` (bfa) → `be2b64d6` (5ee,
   64+/407- pre-window tier migration, SQL facts live) →
   `912cd47f` (HEAD, 77+/83- window). The cause cites the window
   only. The tier split still stands in the HEAD module
   docstring (plan/cache/construction here, SQL live); no oracle
   loss (pre-window moves are tier migration, the window
   deletion is promoted live to
   `test_library_inheritance_api.py`). Axis-5 CONFIRM holds; the
   cause should cite both ranges.

F3's diligence spot-check endorsed (window zero hits re-derived;
pre-window zero hits by my extra grep). The axis-6 new asymmetry
endorsed (stated in the body, fail-loud via `_check_n1`, pinned
by the identity + zero-miss + log oracle; the strictness-raise
consequence follows from the standing strictness tests).

### Fingerprints (own method: `git rev-parse HEAD:<path>`, never mixed)

All 16 HEAD blobs re-derived and MATCH W1's table digit-for-digit:
`extension.py` `e0e53a8e`, `_context.py` `dbc30630`,
`operation_state.py` `b2674a22` MATCH, `utils/context.py`
`cd0adcc5` MATCH, `querysets.py` `3616927d`, `registry.py`
`81bd561c`, `hints.py` `da46ef89` MATCH, `join_taxonomy.py`
`9b355a50` MATCH, `nested_fetch.py` `4d8d37a7` MATCH, `walker.py`
`75f9c6b6`, `plans.py` `cce98531` MATCH, `nested_planner.py`
`b4dfd4a6`, `test_hints.py` `d3e413bd` MATCH,
`test_join_taxonomy.py` `481294c3` MATCH, `test_nested_fetch.py`
`7fbd957b` MATCH, `test_extension.py` `912cd47f`. All 6 MATCH rows
are byte-identical to their baselines (own `git rev-parse
<base>:<path>` comparison; for Q10 MATCH rows bfa=HEAD implies
zero drift across the full range). Every STALE cause judged
correct in its window part, with the three pre-window
completions above (immaterial). The nested-planner pre-window
attribution is correct (zero drift in-window re-derived via an
empty diff stat; run 5 verified at `b4dfd4a6` per the plan).

### Family-consequence judgments (Worker-0 routes on these)

Endorse both. (1) `subsystem-clear-lifecycle` (verified) —
flagged-not-reopened is correct. The bus mechanism is one
definition set (dict + register + iter + `clear()` replay tail;
registry drift is prose-only), H2 is the 18th adapter in the
family's own C1 shape (one register line + its callback, the bus
needs no change) with its own P6 row-pin test, and HEAD
production sites total 19 = family 17 + this row + one walker row
(drift-new, owned by the separately REOPENED walker item).
Census note owed, verdict stands. (2) Q10 walker-interior cells
ride with the walker item — correct. Extension-side cells are
re-verified at HEAD (key tuple untouched, zero join imports,
`hint_is_skip` imported once + called once, `resolve_strategy`
two calls + annotation, nested_planner still classifies and
resolves overrides, new-form counts 0/0/0); walker-interior
detail sits on STALE walker bytes under the separately REOPENED
item.

### Index rows

2/2 literal texts match their findings with no correction: row 1
adopts `clear_document_key_cache` + registration as the
drift-new full-clear member converging onto verified
`subsystem-clear-lifecycle` (FL1-REVISE challenge "drain the
doc-key memo on registry clear" → 1); row 2 records
`DjangoOptimizerExtension.cache_clear` file-local (FL7-REVISE
challenge "reset semantics change" → 1). Both 5-column,
verbatim-ready.

### Nothing-else-changed

Window vs `ITEM_BASELINE=919e9ef4...` holds exactly the plan
(Worker-0's 36+/1- dispatch + submission record) — nothing to
re-attribute. Prior sections untouched (pre-edit 1400 lines /
76915 B / `8d161bcc...` matches the dispatch record; the Status
swap + this EOF append is the whole delta). No production edit,
no test edit, no plan edit, no new tracked file, zero `.py`
touched (`--name-only -- '*.py'` empty) so no ruff run owed.
Appended prose checked against AGENTS.md: `path::Symbol` cites
present, `path:NN` confined to this per-cycle artifact (allowed),
no process provenance beyond the DRY.md-mandated role labels, no
cross-file links (no scaffold owed). No `(Worker-2)` defect (none
found). `FAKESHOP_SHARDED=1` and pg cells stay `unverified`.
Concurrent dirt left alone; no commit.
