# DRY review: `django_strawberry_framework/connection.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, re-challenged
fresh on the connection side) or a file-local record with its proving
challenge, plus three recorded rejections and one external-concurrent-work
row. Zero production edits; zero tracked files changed.

## System trace

Large target (2321 lines, 79 top-level statements working tree, 77 at HEAD).
The package's Relay cursor-pagination surface. It DEFINES the connection-class
surface (`connection.py::DjangoConnection` + its `resolve_connection`
dispatch, the `first` + `last` guard, the selection-gated `totalCount`
capture, the per-target concrete-class generation with provenance cache),
the windowed-prefetch consumption surface (`connection.py::_WindowedConnectionRows`,
`connection.py::_resolve_from_window`, `connection.py::_consume_window`,
`connection.py::_consume_fallback`), the keyset slicing surface
(`connection.py::_resolve_keyset_connection`, `connection.py::_keyset_order_state`,
`connection.py::_KeysetPage`), and the composition pipeline plus resolver
factories (`connection.py::_pipeline_sync`, `connection.py::_pipeline_async`,
`connection.py::_build_connection_resolver`,
`connection.py::_build_relation_connection_resolver`,
`connection.py::DjangoConnectionField`). It ENFORCES four
consumer-`resolver=` contract guards of its own
(`connection.py::_guard_sidecar_input_against_non_queryset`,
`connection.py::_guard_non_queryset_iterable`,
`connection.py::_guard_source_not_pre_sliced`,
`connection.py::_guard_first_and_last`) and CONSUMES by name every other
rule it touches: the queryset substrate (`utils/querysets.py`),
the window grammar (`utils/connections.py`), the cursor codec
(`keyset.py`), the order grammar (`optimizer/plans.py`), the selection
primitives (`optimizer/selections.py`), the deadline, strictness,
directive, validation, optimization, and execution-mode seams.

Connected code read for judgment, outside the item:
`django_strawberry_framework/utils/querysets.py` (def lines + docstrings of
`utils/querysets.py::prepared_resolver_source`,
`utils/querysets.py::reject_awaitable_sync_source`,
`utils/querysets.py::reject_residual_async_source`,
`utils/querysets.py::reject_async_iterable_in_sync_context`,
`utils/querysets.py::apply_type_visibility_sync`,
`utils/querysets.py::apply_type_visibility_async`,
`utils/querysets.py::base_queryset`, `utils/querysets.py::model_for`,
`utils/querysets.py::_validate_post_orderset_result`,
`utils/querysets.py::is_async_only_iterable`,
`utils/querysets.py::_SealPolicy`, and the `sliced` arm;
`_pipeline_sync` / `_pipeline_async` / `_prepare_pipeline_source` bodies
read end to end here);
`django_strawberry_framework/list_field.py` (import block,
`list_field.py::_validate_relay_djangotype_target`,
`list_field.py::_model_from_definition`,
`list_field.py::_orderset_class_from_definition`,
`list_field.py::_apply_orderset_sync` / `_apply_orderset_async`,
`list_field.py::_execute_queryset_pipeline_sync` / `_async` heads,
`list_field.py::_synthesized_list_signature`,
`list_field.py::_is_deterministic_order_name` family, both
`prepared_resolver_source` call sites);
`django_strawberry_framework/utils/connections.py` (def census:
`derive_connection_window_bounds`, `derive_keyset_window_bounds`,
`split_window_rows`, `window_range_plan`, `assert_relay_pagination_bound`,
`resolve_relay_max_results`, plus the `connection.py::_resolve_from_window`
cross-citation comments);
`django_strawberry_framework/keyset.py` (def census: codec pair,
`declared_cursor_state_for_definition`, `keyset_contract_error`,
`order_fingerprint`, `_is_supported_cursor_field`, `KeysetSeek`);
`django_strawberry_framework/optimizer/plans.py`
(`optimizer/plans.py::effective_connection_order`,
`optimizer/plans.py::order_entry_name_and_direction`,
`optimizer/plans.py::order_entry_has_explicit_nulls`,
`optimizer/plans.py::ends_in_unique_column` + the
`connection.py::_resolve_from_window` citations);
`django_strawberry_framework/optimizer/selections.py`
(`optimizer/selections.py::connection_field_names`,
`optimizer/selections.py::connection_total_count_selected`,
`optimizer/selections.py::connection_has_next_page_selected`,
`optimizer/selections.py::prime_selected_fields`);
`django_strawberry_framework/utils/relations.py`
(`utils/relations.py::relation_kind`, `utils/relations.py::classify_path`
def lines); `django_strawberry_framework/types/resolvers.py`
(`types/resolvers.py::_check_n1` def line);
`django_strawberry_framework/types/finalizer.py`
(`_build_relation_connection_resolver` / `_connection_type_for` call sites);
`django_strawberry_framework/optimizer/nested_fetch.py`
(`is_sliced` classifier lines, the non-definition);
`django_strawberry_framework/resource_policy.py::check_deadline`,
`django_strawberry_framework/utils/directives.py::validated_field_directives`,
`django_strawberry_framework/utils/execution_mode.py`,
`django_strawberry_framework/utils/typing.py`,
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/exceptions.py` (def lines only);
upstream `.venv` `strawberry/relay/types.py`
(`ListConnection.resolve_connection` signature);
`tests/test_connection.py` (`_ends_in_unique_column` import + pin bodies,
guard / pre-slice oracle titles);
`examples/fakeshop/test_query/test_library_api.py` (first+last live pin);
`examples/fakeshop/test_query/test_keyset_api.py` (module head + codec import);
`docs/SPECS/spec-030-connection_field-0_0_9.md` (pointer only, body not
relied upon).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) - never touched, not in this finding's sites;
in-flight spec bodies behind the module docstring's Decision pointers
(spec-030/032/033/047 cited as pointers, defaults pinned by oracles
instead); `docs/GLOSSARY.md` connection entries (projections, not relied
upon); `optimizer/walker.py` / `optimizer/extension.py` / `optimizer/nested_planner.py`
bodies beyond the cited def lines (planner-side window construction is the
family items' surface; this item traces the consume side);
`auth/mutations.py` + `routers.py` disposal bodies (F1 owner-side count is
plan-indexed; this item verifies the connection-side consumer role only);
`utils/relations.py::classify_path` + `optimizer/plans.py` order-helper
bodies (F7 membership asserted on the shared `_meta` mechanism visible at
the def lines and at this target's call site; the family item owns the
full sweep); concurrent dirt (`tests/test_connection.py`,
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) - read where needed as oracles, never edited.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor was checked for
its own spelling of this file's rules. The `first` + `last`
mutual-exclusivity literal lives exactly once in production
(`connection.py::_guard_first_and_last`; probe `guard-literal-once`).
No list / mutation / form / rest_framework surface defines a first+last
guard, a `totalCount` capture, a windowed-row consumer, or a keyset
slicer. Shared seams are composed by name, never respelled:
`list_field.py::_validate_relay_djangotype_target` (the factory guard,
imported here), `utils/querysets.py::prepared_resolver_source` (both
collection flavors), `utils/querysets.py::apply_type_visibility_sync` /
`_async` (both pipelines), `utils/querysets.py::base_queryset` (both
default seeds). The one genuine second definition found is the pre-sliced
guard (F3). The one genuine absence is the post-OrderSet seal (F5).
The near-misses are recorded as rejections (J1, J2, J3).

**2. Sync/async twins.** Four colored pairs touch this target, all
compared by behavior: `connection.py::_pipeline_sync` /
`connection.py::_pipeline_async` (share `connection.py::_prepare_pipeline_source`,
`connection.py::_sidecar_steps`, `connection.py::_finalize_queryset`
verbatim; differ only in the awaited visibility/filter/order steps and
the async guard passed - the recorded principle-5 shape: two colored
bodies sharing only pure decisions, because consumer `async def` hooks
must be awaited); `connection.py::_attach_count_sync` /
`connection.py::_attach_count_async` (the async twin awaits the queued
connection BEFORE the guard can raise - the await-before-raise discipline
the docstring records, so a guard-raise never strands an awaitable);
`connection.py::_resolve_keyset_connection`'s `_resolve_async` closure vs
its sync tail (same `_build` / `_page` pure decisions, one await point);
`connection.py::_build_connection_resolver`'s sync vs async branches
(committed per construction because Strawberry freezes field sync/async
handling at schema-build time; the docstring records why a per-call
coroutine return cannot work here). No behavioral divergence found
between the halves of any pair (static review of all four bodies).

**3. Derived rather than repeated knowledge.** Four facts this file could
have respelled are derived once from their owner instead: the generated
connection name comes from `definition.graphql_type_name`, never from
`__name__` (docstring records the two-classes-one-`__name__` collision it
prevents); the effective order comes from
`optimizer/plans.py::effective_connection_order`, the same implementation
the planner uses (the cursor-parity invariant); the cursor prefix for the
external negativity guard is read off the resolved edge class
(`connection.py::_offset_cursor_prefix`), never assumed; the
`totalCount` GraphQL names come from the active schema converter via
`optimizer/selections.py` primitives, never from camelCase literals
(`connection.py::_total_count_requested` docstring records the
`auto_camel_case=False` bug this closed). The `_TOTAL_COUNT_ATTR`
writer is single-sited (`connection.py::_set_total_count`); the
`_dst_keyset_state` vocabulary is fixed once at class generation
(`connection.py::_generate_connection_class`), never re-read at resolve
time. No reconstructed copy found.

**4. Inverse / round-trip pairs.** Three grammars, each with one owner,
both halves composed here by name: offset cursors (Strawberry's edge
class owns prefix + base64; this file passes only the integer offset
through `edge_class.resolve_edge`, and the external guard decodes via
`from_base64` for the negativity verdict only); keyset cursors
(`keyset.py` owns `encode_keyset_cursor` / `decode_keyset_cursor`;
this file never encodes, decodes, or fingerprints itself);
window bounds (`utils/connections.py` owns
`derive_connection_window_bounds` / `derive_keyset_window_bounds` /
`window_range_plan` / `split_window_rows`; `connection.py::_consume_window`
and `connection.py::_resolve_from_window` derive through them so the
resolve-time window matches the plan-time window by construction).
No second grammar lives here.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); oracles that spell literals
directly - `tests/test_connection.py` (the `_ends_in_unique_column`
import pin, guard pins, pre-slice hostile-`is_sliced` rows, keyset /
window / count pins) plus the live tier
(`test_library_api.py::test_genre_connection_first_and_last_rejected`,
`test_keyset_api.py` round-trip / tamper / seek rows); projections (the
module / class / function docstrings, `docs/SPECS/spec-030-*` pointers).
Every oracle checked spells its expectation independently (the guard
message, the cursor bytes, the flag arithmetic) and would fail, not
follow, a production change. The `_ends_in_unique_column` re-export
exists solely so the spec-030 pins keep importing from here; it is an
assignment alias, not a copy (probe `alias-_ends_in_unique_column`).

**6. Enforcement by omission.** Three member-by-member checks.
(a) Post-OrderSet seal: `list_field.py` freezes routing intent and
re-seals through `utils/querysets.py::_validate_post_orderset_result`;
this file's two `OrderSet.apply_*` call sites do neither (probe
`absent-_validate_post_orderset_result`). The contract sources scope the
rule to the list field while the connection also windows what comes
back - ambiguous, already routed to the maintainer as D3 by the querysets item;
re-confirmed present, no new verdict here (F5).
(b) Async-shape vocabulary: this file's three async-shape branches ask
"may the async executor stream this?" (must answer yes for a QuerySet)
or admit a union - the opposite of
`utils/querysets.py::is_async_only_iterable`. Substituting the shared
predicate would misroute every queryset (F10 rejection, re-checked
fresh; F4).
(c) Slice/ordering guards: `connection.py::_guard_source_not_pre_sliced`
fires on every queryset path including the keyset slicer entry;
`connection.py::_finalize_queryset` converts unreadable-ordering and
unappliable-ordering failures to `GraphQLError` rather than leaking
Django internals; the external hunk adds the non-queryset negative-cursor
guard for the offset-fallback branch only (traced, not judged - X1).
No member lacks a guard its contract requires beyond the already-routed
D3.

### Enumeration

Instrument: `ast.parse` over the working-tree blob, counting
`ast.Module.body` members - **79 top-level statements** (77 at HEAD; the
+2 are the external hunk's two functions). Every member lands below;
every challenge in `### Challenges` ends in a family row, a file-local
record, a recorded rejection, or the external row.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (surface contract + spec pointer) | (none) | projection |
| 1-15 | imports: future, inspect, types, collections.abc, dataclass (x2), typing, strawberry, django.db, graphql, strawberry.relay, relay.types, relay.utils, strawberry.types, await_maybe | machinery names | machinery (13 also feeds X1 via `from_base64`) |
| 16 | `from .exceptions import ...` | `ConfigurationError`, `_safe_class_name`, `_safe_type_name` | consumer (R3, R6 guards) |
| 17 | `from .keyset import ...` (9 names) | codec + state + errors | consumer (R5) |
| 18 | `from .list_field import _validate_relay_djangotype_target` | factory guard | consumer (R6) |
| 19 | `from .optimizer.extension import apply_connection_optimization` | plan applier | consumer (R6) |
| 20 | `from .optimizer.nested_planner import ...` (3 names) | projection helper + attr keys | consumer (R5, R6) |
| 21 | `from .optimizer.plans import ...` (7 names) | order grammar + parity predicate | consumer (R5, R6, R-ALIAS) |
| 22 | `from .optimizer.selections import ...` (4 names) | selection primitives | consumer (R7) |
| 23 | `from .registry import register_subsystem_clear` | cache-clear wiring | consumer (R3) |
| 24 | `from .resource_policy import check_deadline` | deadline seam | consumer (dispatch) |
| 25 | `from .types.resolvers import _check_n1` | strictness seam | consumer (R6) |
| 26 | `from .utils.connections import ...` (14 names) | window grammar | consumer (R4, R5, R6) |
| 27 | `from .utils.directives import validated_field_directives` | directive gate | consumer (R6) |
| 28 | `from .utils.execution_mode import ...` | color readers | consumer (R5, R6) |
| 29 | `from .utils.querysets import ...` (7 names) | substrate runners + guards + seed | consumer (F1, F2, F6) |
| 30 | `from .utils.relations import relation_kind` | relation classifier | consumer (F7) |
| 31 | `from .utils.typing import ...` | color test + container peel | consumer (R6, R4) |
| 32 | `_ends_in_unique_column = ends_in_unique_column` | compat alias | R-ALIAS |
| 33 | `NodeType = TypeVar(...)` | generic var | machinery (R3) |
| 34 | `_TOTAL_COUNT_ATTR = "_django_total_count"` | count slot name | R2 |
| 35 | `def _keyset_connection_context` | keyset-mode read | R5 |
| 36 | `def _set_total_count` | single count writer | R2 |
| 37 | `def _empty_page_connection` | empty-page shape | R4 |
| 38 | `class _WindowedConnectionRows` | window marker | R4 |
| 39 | `def _build_windowed_fallback` | recovery factory | R4 |
| 40 | `def _window_edge_class` | edge-class peel | R4 |
| 41 | `def _resolve_from_window` | window derivation | R4 |
| 42 | `def _consume_window` | window dispatch | R4 |
| 43 | `def _offset_cursor_prefix` | prefix read | X1 external |
| 44 | `def _reject_negative_offset_cursor` | negativity verdict | X1 external |
| 45 | `def _consume_fallback` | non-window dispatch | R4 (hosts X1 guard lines) |
| 46 | `def _keyset_order_ref` | entry anchorability | R5 (+ J1) |
| 47 | `def _resolve_order_path_field` | `__`-path field resolve | F7 |
| 48 | `def _keyset_order_state` | root slicing state | R5 |
| 49 | `class _KeysetPage` (+ 2 properties) | value-domain flags | R5 |
| 50 | `def _resolve_keyset_connection` | keyset slicer | R5 (+ F4) |
| 51 | `def _guard_first_and_last` | exclusivity guard | R1 |
| 52 | `def _connection_field_requested` | shared selection walk | R7 |
| 53 | `def _total_count_requested` | count observer | R7 (serves R2) |
| 54 | `def _has_next_page_requested` | flag observer | R7 (serves R4) |
| 55 | `class DjangoConnection` (+ `resolve_connection`, `_resolves_total_count`) | dispatch base | R6 (+ R1, R2) |
| 56 | `class _CachedConnectionType` | cache entry | R3 |
| 57 | `_connection_type_cache: dict[...] = {}` | cache store | R3 |
| 58 | `def clear_connection_type_cache` | test-only clear | R3 |
| 59 | `register_subsystem_clear(...)` call | reset wiring | R3 |
| 60 | `def _generate_connection_class` | class generator | R3 |
| 61 | `def _build_total_count_connection` (+ nested `total_count`, `_populate`) | opted variant | R3 (+ R2 field) |
| 62 | `def _guard_total_count_countable` | count/iterable rule | R2 |
| 63 | `def _attach_count_sync` | sync count attach | R2 |
| 64 | `async def _attach_count_async` | async count attach | R2 |
| 65 | `def _connection_type_for` | cached class resolve | R3 |
| 66 | `def _guard_sidecar_input_against_non_queryset` | sidecar/iterable rule | R6 |
| 67 | `def _guard_non_queryset_iterable` | scalar refusal | R6 (+ F4) |
| 68 | `def _guard_source_not_pre_sliced` | pre-slice refusal | F3 |
| 69 | `def _finalize_queryset` | order + plan tail | R6 |
| 70 | `def _prepare_pipeline_source` | color-agnostic head | R6 (F1, F6 consumers) |
| 71 | `def _sidecar_steps` | sidecar step list | R6 |
| 72 | `def _pipeline_sync` | sync composition | R6 (F1, F2, F6) |
| 73 | `async def _pipeline_async` | async composition | R6 (F1, F2, F6) |
| 74 | `def _synthesized_signature` | SDL signature | R6 (+ J3) |
| 75 | `def _build_connection_resolver` (+ 2 `_resolve` branches) | root resolver | R6 |
| 76 | `def _window_rows_are_annotated` | window probe | R4 |
| 77 | `def _build_relation_connection_resolver` (+ `_resolve`) | relation resolver | R6 |
| 78 | `def DjangoConnectionField` | field factory | R6 |

Rules: F1-F7 reuse the plan's existing family names (no new family
named); R1-R7 + R-ALIAS are file-local; J1-J3 are recorded rejections;
X1 is external concurrent work. The plan's `## Responsibility index`
already carries all seven families with this file listed - reused, not
renamed.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 disposal | disposal must handle a third awaitable kind | **1** (`utils/querysets.py::_dispose_sync_awaitable`; this file's three consume sites follow as consumers) | consumer |
| C2 | F1 guard choice | sync pipeline must refuse a new async shape | **1** (the guard owned in querysets; `connection.py::_prepare_pipeline_source` passes a different guard per color, unchanged) | consumer |
| C3 | F2 seal | a new untrusted queryset shape must be rebuilt | **1** (the seal; this file's pipeline + finalize + keyset reads run on sealed output) | consumer |
| C4 | F3 pre-slice | pre-slice rejection must name a new source shape | **2** (the seal's `sliced` arm + `connection.py::_guard_source_not_pre_sliced`) | family-open |
| C5 | F3 error class | unify the rejection error class across surfaces | **2** (same two; `GraphQLError` at the wire vs `ConfigurationError` in the seal) | family-open |
| C6 | F4 async-shape | route this file's `AsyncIterable` branches through `is_async_only_iterable` | **refused** (would misroute every QuerySet down the sync branch; F10) | rejection |
| C7 | F5 post-apply seal | an `OrderSet.apply_*` override returns a sliced qs through a connection | **1 owned + 1 absent** (list seals via `utils/querysets.py::_validate_post_orderset_result`; this file has no call - D3, already routed, no verdict here) | ambiguous-routed |
| C8 | F6 seed | default seed must pin a new routing fact | **1** (`utils/querysets.py::base_queryset`; this file's default branch follows) | consumer |
| C9 | F6 model read | definition model read must fail loud on a hostile metaclass | **1** at the validator (`list_field.py::_model_from_definition` validates; this file relies on the factory-time validated read - J2) | consumer |
| C10 | F7 path | a new unresolvable segment kind must be classified | **2+** (`connection.py::_resolve_order_path_field` + `utils/relations.py::classify_path`; plans/querysets members for the family item to classify) | family-open |
| C11 | R1 message | reword the exclusivity message | **1** (`connection.py::_guard_first_and_last`; oracles move) | file-local |
| C12 | R1 scope | allow `first` + `last` when one is zero | **1** (same guard; the `is_supplied` reading moves with it) | file-local |
| C13 | R2 count source | unify pre-seek (keyset) and post-filter (offset) count sources | **1 owner** (both clusters live in this file; the domain difference is recorded in the slicer docstrings) | file-local |
| C14 | R2 guard | `totalCount` over a new countable shape | **1** (`connection.py::_guard_total_count_countable` + attach twins move together) | file-local |
| C15 | R3 naming | generated class name gains a namespace | **1** (`connection.py::_generate_connection_class`) | file-local |
| C16 | R3 provenance | warm-cache provenance check must compare unequal-but-equal definitions | **1** (`connection.py::_connection_type_for` identity check) | file-local |
| C17 | R4 flags | empty-page flag arithmetic changes | **1** (`connection.py::_empty_page_connection`; `ListConnection` parity re-pinned by oracles) | file-local |
| C18 | R4 classification | marker/sentinel classification changes | **1** at the owner (`utils/connections.py::split_window_rows`; this file follows as consumer) | consumer |
| C19 | R5 anchor | a new order shape must anchor value cursors | **1** (`connection.py::_keyset_order_ref` + `_keyset_order_state` move together; the codec is unchanged) | file-local |
| C20 | R5 flags | value-domain flag rule changes | **1** (`connection.py::_KeysetPage`) | file-local |
| C21 | R6 sidecar | a third sidecar kind (`search:`) ships | **1 owner** (signature + steps + both pipelines, all in this file) | file-local |
| C22 | R7 vocabulary | a GraphQL name for `totalCount` changes | **0 here** (owned at `optimizer/selections.py`; the predicates + converter follow) | consumer |
| C23 | R-ALIAS | the cursor-parity invariant changes | **1** (`optimizer/plans.py::ends_in_unique_column`; the alias follows automatically) | consumer |
| C24 | J1-J3 | the three refused shared forms (list predicates, model validators, signature synthesizer) | **0 moves - refused**, differences + triggers in findings | refused |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest - the workspace recipe is for mutating
proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-connection/probe_w1.py
```

Output (`ALL OK`, 70 checks): 79-member working AST with the HEAD 77
split; 42 working defs incl. the two external-hunk functions absent at
HEAD; 28-name family import census; 7 absence claims; 22 single-site
claims; the guard literal once; the item-baseline diff empty. One
first-draft check failed on probe precision (the `_ends_in_unique_column`
alias is an `Assign`, not a `def` - corrected to an assignment count)
and was re-verified green, substance unaffected. Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a second definition lives here", "the target
drifted from its baseline", "the external hunk is owned here".

## Findings

No production edit is owed by a file item; the seven families below are
REUSED from the plan (connection-side roles re-challenged fresh), the
rest are file-local records and three recorded rejections plus the
external row.

### F1 - awaitable refusal and disposal (existing family `awaitable-refusal-and-disposal`, stays `open`)

- **Contract + variation.** A refused awaitable is detected without
  awaiting it and released so no never-awaited warning escapes; what
  follows the disposal (which error, which sentinel) varies per seam.
- **Sites + roles.** *Definitions*: per the plan index,
  `utils/querysets.py::_dispose_sync_awaitable` plus the two inline
  detect-then-dispose sites (owner side; family item's surface).
  *Consumers here*: `connection.py::_prepare_pipeline_source` (takes the
  guard as a parameter - `reject_awaitable_sync_source` on the sync
  pipeline, `reject_residual_async_source` on the async one),
  `connection.py::_build_connection_resolver` (the
  `reject_async_iterable_in_sync_context` call on the sync branch),
  `connection.py::_attach_count_async` (await-before-raise mirrors the
  disposal discipline: the queued coroutine is resolved before the
  countable guard can raise). *Oracles*: the async-misuse rows in
  `tests/test_connection.py` plus the family gate. *Projections*: the
  pipeline docstrings' color contracts.
- **Challenges.** C1, C2 - 1 each, both at the querysets owner; zero
  definitions here.
- **Owner + lifetime.** `utils/querysets.py::_dispose_sync_awaitable`
  (unchanged). No stored derivation here.
- **Migration.** None (zero-edit item; consumer role only).
- **Distinct behavior.** The per-color guard choice stays at the caller
  (`_prepare_pipeline_source` takes `async_guard` as an argument) - a
  change to which shape the sync pipeline refuses moves the guard, not
  the head.
- **Behavioral proof.** `static-reviewed` for the consumer role (import
  block + three call sites + pipeline bodies read); `execution-verified`
  for the import/absence census (probe). Rejects "this file disposes an
  awaitable itself".
- **Structural gate.** The existing async-misuse oracles (sync field
  meeting an async `get_queryset` raises `SyncMisuseError`; async
  generator over `execute_sync` is refused). Negative control: a
  hand copy of the guard call deleted from `_prepare_pipeline_source`
  passes every happy-path oracle and fails exactly those rows.
- **Coupling.** None.
- **Freshness.** `connection.py` working `3c4d5dcb...` / HEAD
  `93e998f2...`, `utils/querysets.py` `5907a1f7...` (owner def lines
  only), `tests/test_connection.py` `e5e8990a...` (oracle titles only).

### F2 - sealed-execution queryset (existing family `sealed-execution-queryset`, stays `open`)

- **Contract + variation.** A consumer-supplied or hook-returned
  queryset is untrusted state: validated and rebuilt by the seal; policy
  variation is declared on `_SealPolicy`, not branched at consumers.
- **Sites + roles.** *Definition*: the seal in `utils/querysets.py`
  (owner side). *Consumers here*: `connection.py::_pipeline_sync` /
  `connection.py::_pipeline_async` (visibility runners),
  `connection.py::_finalize_queryset` (reads `query.order_by` and
  applies `order_by(*ordered)` on the sealed output),
  `connection.py::_keyset_order_state` /
  `connection.py::_resolve_keyset_connection` (read `query.order_by`
  and slice the sealed queryset). The `connection.py:1666`
  `source.query.is_sliced` read belongs to F3, not to this rule.
- **Challenges.** C3 - 1 at the seal; zero definitions here.
  Package-wide mechanism sweep for the seal's construction vocabulary
  (`models.QuerySet(...)`, `sql.Query`) was already run by the
  querysets item (one definition); this item re-confirms no such
  construction exists in this file (probe absence + full read).
- **Owner + lifetime.** `utils/querysets.py::_seal_or_defect`
  (unchanged). No stored derivation here.
- **Migration.** None.
- **Distinct behavior.** Nothing here rebuilds a queryset from state;
  every read is a planning question on an already-sealed object.
- **Behavioral proof.** `static-reviewed` (pipeline + finalize + keyset
  bodies read end to end); `execution-verified` for the census.
- **Structural gate.** The seal's own oracle suite plus the hostile-shape
  containment rows in `tests/test_connection.py` (a hostile `query`
  attribute answers `GraphQLError`, never a leak).
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `5907a1f7...`
  + `list_field.py` `f357eded...` (sibling consumer, def lines only).

### F3 - pre-sliced source rejection (existing family `recomposition-illegal-source-rejection`, stays `open`)

- **Contract + variation.** A source a surface will recompose onto may
  not arrive already sliced. Legitimate variation: surfaces that do not
  recompose switch the rule off (the optimizer's plan-degrading
  classifier, which is a different contract).
- **Sites + roles.** *Definitions*: `utils/querysets.py::_SealPolicy`
  `reject_sliced` arm (seal, `ConfigurationError` timing) and
  `connection.py::_guard_source_not_pre_sliced` (wire, `GraphQLError`
  naming the `resolver=` contract, fail-soft hostile-`is_sliced`
  arm). *Not a definition*:
  `optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
  (degrades a plan, never rejects - re-confirmed by reading its
  `is_sliced` lines). *Consumers of the connection guard*: the pipeline
  head (`connection.py::_prepare_pipeline_source` via
  `queryset_guard`), both pipelines, and the keyset slicer entry.
  *Oracles*: the hostile-`is_sliced` row and pre-sliced rows in
  `tests/test_connection.py`.
- **Challenges.** C4, C5 - 2 each (the count that keeps this family
  open). Both give the same stated reason; they differ in error class,
  timing (before visibility vs during the seal), and whether the read
  dispatches consumer code.
- **Owner + lifetime.** Candidate owner `utils/querysets.py::_SealPolicy`
  (family item decides adapter vs second definition). No stored
  derivation here.
- **Migration.** None (file item; the family item owns the decision).
- **Distinct behavior.** The seal already rejects the same source one
  step later, so the guard is not load-bearing for fail-closed
  behavior - its load is the wire-flavored error. Any consolidation
  owes an `execution-verified` proof that the client-visible error
  class does not change.
- **Behavioral proof.** `static-reviewed` (guard body + seal arm +
  classifier lines read); `execution-verified` for the census.
- **Structural gate.** The pre-sliced and hostile-shape oracles.
  Negative control: deleting the guard body passes every oracle except
  the wire-flavored-message rows (the seal still fails closed behind
  it with a different class) - which is exactly why the count is 2
  and not 1.
- **Coupling.** None (D3 touches the same pipeline but is an
  independent decision).
- **Freshness.** Target as in F1 + `utils/querysets.py` `5907a1f7...`
  + `optimizer/nested_fetch.py` `4d8d37a7...` (classifier lines only)
  + `tests/test_connection.py` `e5e8990a...`.

### F4 - async-shape vocabulary (existing family `async-only-queryset-row-adapter`, stays `open`)

- **Contract + variation.** `utils/querysets.py::is_async_only_iterable`
  (`AsyncIterable and not Iterable`) exists so a QuerySet (both) never
  classifies as async-only. The adapter trio around
  `utils/querysets.py::_AsyncQuerySetRows` is that family's surface.
- **Sites + roles.** This file holds NO definition and NO consumer of
  the predicate (probe `absent-is_async_only_iterable`,
  `absent-_AsyncQuerySetRows`). Its three async-shape branches ask
  different questions: `connection.py::_resolve_keyset_connection`'s
  `isinstance(nodes, (AsyncIterator, AsyncIterable))` asks "may the
  async executor stream this?" (must answer yes for a QuerySet);
  `connection.py::_guard_non_queryset_iterable` admits a union
  (`Iterable` OR `AsyncIterable` OR `__getitem__`). Both bodies read
  in full.
- **Challenges.** C6 - refused (F10 of the querysets item, re-derived
  fresh here, not inherited: substituting the shared predicate sends
  every queryset down the sync branch under async execution).
- **REJECTED shared form.** Routing this file's branches through
  `is_async_only_iterable`. Contract difference: difference vs union,
  and the opposite answer for QuerySets. Reconsideration trigger: this
  file ever needs to tell an async-only consumer source apart from a
  queryset (e.g. a sync-execution refusal for async-only connection
  sources) - that new site belongs to the shared rule. Durable home:
  the family item + this finding.
- **Owner + lifetime.** `utils/querysets.py` (unchanged).
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (all three branch bodies +
  the predicate def line read).
- **Structural gate.** The async keyset / async-iterable oracles in
  `tests/test_connection.py`; a substitution fails them by routing.
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `5907a1f7...`
  + `list_field.py` `f357eded...` + `resource_policy.py` `9205124f...`
  (confirmed consumers, def lines only).

### F5 - post-set-apply result validation (existing family `post-set-apply-result-validation`, stays `open`)

- **Contract + variation.** A public `OrderSet.apply_*` override's
  return is re-sealed (lazy, unsliced, model-row-shaped, non-combined,
  same route) before the surface windows it.
- **Sites + roles.** *Definition*:
  `utils/querysets.py::_validate_post_orderset_result`, enforced at
  `list_field.py::_apply_orderset_sync` / `_apply_orderset_async`
  (both read; freeze-then-seal). *Unguarded member*:
  `connection.py::_pipeline_sync` / `connection.py::_pipeline_async`
  invoke the same public `OrderSet.apply_sync` / `apply_async` (via
  `connection.py::_sidecar_steps`) and pass the return straight to
  `connection.py::_finalize_queryset` (probe
  `absent-_validate_post_orderset_result`; both call sites read).
- **Challenges.** C7 - 1 owned + 1 absent. No verdict (ambiguous:
  both contract sources found scope the rule to the list field while
  the connection also windows what comes back - D3, routed to the maintainer by
  the querysets item; re-confirmed present, not re-homed).
- **Owner + lifetime.** `utils/querysets.py` (unchanged).
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (both pipelines + both list
  appliers read). No consolidation depends on it.
- **Structural gate.** The list-field override-misbehavior oracles;
  no connection-side oracle exists for the unguarded member (that
  absence is the routed ambiguity).
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `5907a1f7...`
  + `list_field.py` `f357eded...`.

### F6 - queryset seed and model read (existing family `queryset-seed-and-model-read`, stays `open`)

- **Contract + variation.** A surface seeds its default queryset from
  the relation's target model on the right connection and reads the
  model off the ONE construction-time definition, so seed and seal
  cannot be answered from two different reads.
- **Sites + roles.** *Definitions*: `utils/querysets.py::model_for`
  (single `_meta` read site) + `utils/querysets.py::base_queryset`
  (seed with `using` arm). *Consumers here*:
  `connection.py::_build_connection_resolver` (`base_queryset(definition.model)`
  on the default branch) and the eleven direct `definition.model` /
  `definition.cursor_field` / sidecar-class reads, every one of which
  the docstrings record as the factory's captured read (probe
  `absent-model_for` - this file never re-reads the type). *Sibling
  consumers*: the list default seed, the walker, the filter child.
- **Challenges.** C8 (1, seed), C9 (1, at the validator - J2).
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here (the `definition` object is handed down, never
  cached beyond the call).
- **Migration.** None.
- **Distinct behavior.** The captured-read discipline (J2): this file
  relies on the factory-time validated definition rather than
  re-validating per read.
- **Behavioral proof.** `static-reviewed` (resolver builder + both
  pipelines + `_finalize_queryset` read); `execution-verified` for
  the census.
- **Structural gate.** The default-field oracles (an unseedable model
  fails at field construction, never per request).
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `5907a1f7...`
  + `list_field.py` `f357eded...` (sibling seed + validators).

### F7 - ORM lookup-path resolution (existing family `orm-lookup-path-resolution`, stays `open`)

- **Contract + variation.** Resolve a `__`-traversing lookup path
  through `Model._meta` to a terminal, rejecting shapes a downstream
  contract cannot use (nullable joins, reverse/multi-valued hops,
  non-concrete terminals).
- **Sites + roles.** *Definitions*: `utils/relations.py::classify_path`
  (owner) and `connection.py::_resolve_order_path_field` (this file's
  member: `pk`-aliasing, per-segment `get_field`, the
  `forward_single` + non-null intermediate rule via
  `utils/relations.py::relation_kind`, the concrete-non-relation
  terminal rule). *Consumer of the member*:
  `connection.py::_keyset_order_state` (raises `keyset_contract_error`
  when the member returns `None`). *Oracles*: the keyset order-shape
  rows in `tests/test_connection.py` / `test_keyset_api.py`.
- **Challenges.** C10 - 2+ (this member + the owner; the plans and
  querysets members listed in the index are for the family item to
  classify - bodies not read here, stated honestly).
- **Owner + lifetime.** `utils/relations.py::classify_path`
  (unchanged). No stored derivation here.
- **Migration.** None (file item).
- **Distinct behavior.** Fail-soft (`None`) at the member, fail-loud
  (`keyset_contract_error`) at its consumer - the layering the
  docstring records.
- **Behavioral proof.** `static-reviewed` (member body + consumer +
  both def lines read); `execution-verified` for the census.
- **Structural gate.** The unsupported-`orderBy`-under-keyset oracles
  (aggregate / nullable / JSON / explicit-nulls entries raise the
  keyset boundary error rather than paginating wrongly). Negative
  control: a member returning a field for a nullable intermediate
  passes every happy-path oracle and mints NULL-anchored cursors -
  the keyset round-trip rows catch it.
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/relations.py` `7662b0bb...`
  + `keyset.py` `df4b5e2f...` (codec, consumer side) +
  `optimizer/plans.py` `cce98531...` (cited, body excluded).

### File-local records (no second definition after the matrix)

- **R1 - `first` + `last` mutual-exclusivity guard.**
  `connection.py::_guard_first_and_last` (C11, C12 - 1 each). The
  literal lives once in production (probe); Strawberry's
  `SliceMetadata.from_arguments` applies both without the check
  (upstream body read - it has no exclusivity arm); the guard runs
  before `info` is touched so malformed pagination never reads
  selections. Trigger: a second surface needing the same exclusivity
  would make it a family. Freshness: target + `tests/test_connection.py`
  `e5e8990a...` + `test_library_api.py` `fd00388b...` (live pin).
- **R2 - selection-gated `totalCount` capture.**
  `connection.py::_TOTAL_COUNT_ATTR`, `connection.py::_set_total_count`
  (the single writer), `connection.py::_guard_total_count_countable`,
  `connection.py::_attach_count_sync` /
  `connection.py::_attach_count_async`, served by R7's
  `connection.py::_total_count_requested` (C13, C14 - 1 owner each;
  C13's two count domains live in one file so still one owner).
  The `.count`-read gating (never touch `.count` unless wanted, so
  count-less pages over exotic iterables never raise `AttributeError`)
  and the async await-before-raise are pinned by the non-queryset and
  async count rows. Trigger: a second countable surface (a list-field
  `totalCount`) would make it a family. Freshness: target +
  `tests/test_connection.py` `e5e8990a...`.
- **R3 - per-target concrete connection-class generation.**
  `connection.py::_connection_type_for`,
  `connection.py::_generate_connection_class`,
  `connection.py::_build_total_count_connection`,
  `connection.py::_CachedConnectionType`,
  `connection.py::_connection_type_cache`,
  `connection.py::clear_connection_type_cache` + the
  `register_subsystem_clear` wiring (C15, C16 - 1 each). One class per
  node type, provenance-checked on warm hits, keyset vocabulary baked
  at generation; the bare path is concrete (not an alias) so the
  `resolve_connection` override survives Strawberry's generic
  specialization (upstream signature verified identical). The
  `_resolves_total_count` class-data axis keeps the dispatch body
  single-sited. Trigger: a second per-type generated class with a
  provenance rule would make it a family. Freshness: target +
  `registry.py` `9cc8bb55...` (clear wiring, def line only).
- **R4 - windowed-row consumption and empty-page parity.**
  `connection.py::_WindowedConnectionRows`,
  `connection.py::_build_windowed_fallback`,
  `connection.py::_window_edge_class`,
  `connection.py::_resolve_from_window`,
  `connection.py::_consume_window`, `connection.py::_consume_fallback`,
  `connection.py::_empty_page_connection`,
  `connection.py::_window_rows_are_annotated`, served by R7's
  `connection.py::_has_next_page_requested` (C17 - 1 here; C18 - 1 at
  `utils/connections.py::split_window_rows`, followed as consumer).
  The marker/probe classification delegates to the shared
  `window_range_plan` predicates; only the physical-shape reads live
  here, so plan and classify cannot drift. The `last: 0` serve-all
  quirk and the conditional-count drift guard fall back per-parent
  rather than serve a wrong page. Trigger: a second window consumer
  would make it a family. Freshness: target +
  `utils/connections.py` `f549389e...` +
  `optimizer/nested_planner.py` `0ad8ff5d...` (plan side, cited
  lines only).
- **R5 - keyset slicing surface.**
  `connection.py::_keyset_connection_context`,
  `connection.py::_keyset_order_ref`,
  `connection.py::_keyset_order_state`, `connection.py::_KeysetPage`,
  `connection.py::_resolve_keyset_connection` (C19, C20 - 1 each).
  Columns, fingerprint, seek, overfetch, and both page flags are
  derived here; the codec (`keyset.py`), the order-entry parsing
  (`optimizer/plans.py`), and the path resolution (F7) are composed
  by name. The pre-seek queryset is the `totalCount` source (Relay's
  pre-pagination count); `ListConnection` is never reached for a
  keyset connection. Trigger: a second keyset slicer would make it a
  family. Freshness: target + `keyset.py` `df4b5e2f...` +
  `optimizer/plans.py` `cce98531...` + `test_keyset_api.py`
  `a5e1fbdf...` (live rows).
- **R6 - composition pipeline and resolver factories.**
  `connection.py::_prepare_pipeline_source`,
  `connection.py::_sidecar_steps`, `connection.py::_pipeline_sync` /
  `connection.py::_pipeline_async`,
  `connection.py::_finalize_queryset`, the three contract guards
  (minus F3's), `connection.py::_synthesized_signature`,
  `connection.py::_build_connection_resolver`,
  `connection.py::_build_relation_connection_resolver`,
  `connection.py::DjangoConnection` (+ `resolve_connection`),
  `connection.py::DjangoConnectionField` (C21 - 1 owner: signature,
  steps, and both pipelines move together, all in this file).
  Per-construction sync/async commitment, the `__signature__`
  synthesis with orphan-ledger registration, the per-key window
  probe, and the strictness probe via `types/resolvers.py::_check_n1`
  are each single-sited. Trigger: a second Relay collection surface
  reusing this pipeline would make it a family. Freshness: target +
  `types/finalizer.py` `77fd9a2d...` (relation-resolver call site) +
  `types/resolvers.py` `fc077f38...` + `resource_policy.py`
  `9205124f...` + `utils/directives.py` `380786cf...` (seams, def
  lines only).
- **R7 - resolve-time selection observers.**
  `connection.py::_connection_field_requested` (the one walk) +
  `connection.py::_total_count_requested` +
  `connection.py::_has_next_page_requested` (C22 - 0 here: the GraphQL
  names come from the converter via `optimizer/selections.py`
  primitives; the walk shape is the only thing owned here).
  Consumers: R2's `want_count` threading and R4's drift guards.
  Trigger: a third observer needing the same walk would extend this
  record, not a new rule. Freshness: target +
  `optimizer/selections.py` `a48f6172...`.
- **R-ALIAS - hoisted parity-predicate re-export.**
  `_ends_in_unique_column = ends_in_unique_column` (C23 - 1 at
  `optimizer/plans.py`; the alias follows automatically - an
  assignment, not a copy). Exists so the spec-030 pins keep importing
  from here (oracle import verified). Trigger: none owed (an alias
  cannot drift; deleting it breaks the pins, which is the gate).
  Freshness: target + `optimizer/plans.py` `cce98531...` +
  `tests/test_connection.py` `e5e8990a...`.

### J1 - keyset entry anchorability vs list deterministic-order predicates (rejection, not a family)

`connection.py::_keyset_order_ref` (one effective-order entry: can a
value cursor anchor here?) vs `list_field.py::_is_deterministic_order_name`
/ `_term` / `_value` / `_condition` + `_selected_ordering` /
`_has_deterministic_ordering` (is the applied ordering deterministic?).
Considered shared form: one order-entry classifier. Contract
difference: anchorability rejects unresolvable expressions and explicit
NULLS positioning per entry for cursor minting; determinism certifies a
whole applied ordering for stable pagination - a deterministic entry can
still be unanchorable (explicit nulls) and an anchorable entry says
nothing about the whole. Reconsideration trigger: the keyset slicer ever
certifies whole orderings, or the list field ever mints value cursors.
Durable home: `connection.py::_keyset_order_ref` docstring neighborhood
+ this finding (a file item lands no edit).

### J2 - captured-definition reads vs list validating readers (rejection, not a family)

This file reads `definition.model` / `definition.cursor_field` /
`definition.filterset_class` / `definition.orderset_class` /
`definition.connection` / `definition.graphql_type_name` directly off
the factory's captured read (eleven sites, all documented as one
object); `list_field.py::_model_from_definition` /
`list_field.py::_orderset_class_from_definition` validate-then-read with
fail-loud `ConfigurationError` arms. Considered shared form: routing
this file's reads through the list validators. Contract difference: the
connection factory already validates the target through
`list_field.py::_validate_relay_djangotype_target` at construction, so
per-read re-validation would double-own the failure contract and fork
the error framing (`DjangoConnectionField` vs `DjangoListField`
labels); the validators also pin list-flavored labels the connection
must not emit. Reconsideration trigger: a stateful-definition
substitution bug traced to a connection read - then the read site
gains validation, not a shared reader. Durable home: the factory +
pipeline docstrings (already record the captured-read contract) + this
finding.

### J3 - connection vs list signature synthesis (rejection, not a family)

`connection.py::_synthesized_signature` (sidecar `filter` / `order_by`
beside `root`/`info`, `Iterable[target]` return for
`ConnectionExtension.apply`) vs
`list_field.py::_synthesized_list_signature` (plain field arguments).
Considered shared form: one synthesizer for both flavors. Contract
difference: the connection signature is the `ConnectionExtension`
contract (kwargs-forwarded sidecars, reserved `root`/`info` binding,
orphan-ledger registration for the finalizer); the list signature is
the plain-field contract. They share the `filter_input_type` /
`order_input_type` helpers by name already - that sharing is the
correct level. Reconsideration trigger: a third flavor synthesizing
`ConnectionExtension`-shaped signatures. Durable home: both
synthesizers' docstrings + this finding.

### X1 - offset negative-cursor guard (external concurrent work, traced not owned)

Working-tree-only hunk (`connection.py::_offset_cursor_prefix`,
`connection.py::_reject_negative_offset_cursor`, the `from_base64`
import name, and the `_consume_fallback` non-queryset guard lines;
+64/-1 vs HEAD `93e998f2...`, working `3c4d5dcb...`). Content: the
prefix is derived from the resolved edge class (axis-3 compliant by
construction - honors custom prefixes rather than assuming one);
only the negativity verdict lives here while undecodable / foreign /
non-integer cursors fall through to `SliceMetadata`; the message
mirrors `SliceMetadata`'s foreign-cursor wording; the guard runs on the
non-queryset fallback branch only (a QuerySet answers with Django's own
negative-indexing error). No challenge is run and no verdict is
offered: it is concurrent work under another hand, attributed here by
diff content and left untouched. Trigger for this item: none - when its
owning change lands, its item owns the challenges, the oracles, and
the family-or-local assignment of both functions. Freshness: working
`3c4d5dcb...` vs HEAD `93e998f2...` recorded; probe asserts both
functions present working / absent HEAD.

## Defects

None. Every claim checked while tracing held: the guard literal once;
the alias an assignment; the seven family import censuses complete;
the seven absences absent; the window/keyset/pipeline bodies matching
their docstrings' contracts (including the `last: 0` quirk routing and
the await-before-raise); the provenance identity check present; the
captured-read discipline stated at every read. The two known
connection-adjacent rows keep their existing homes: D3 (unguarded
OrderSet return - ambiguous, already routed to the maintainer, re-confirmed
present, not re-homed) and the F10 rejection (re-derived fresh as F4).
The X1 hunk is not judged here by construction.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
whole-tree sweeps, command in `### Challenges`) already ran green
against the shared tree; they mutate no source and open no database, so
no workspace copy was owed and no `__file__`/DB `NAME` record applies.
No pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED`
or Postgres cell is owed: this artifact's claims (statement counts,
import census, absence/single-site facts, baseline diff) touch no
database, alias, or dialect decision (`inapplicable by construction` -
the target's DB-reaching paths are exercised by the oracles cited, not
by this probe).

## Independent verification (Worker 2)

Recorded before reading `## Findings` below (reconciliation follows the
trace). Instrument of my own: `ast.parse` over the working tree.

**Own trace.** Target is the Relay cursor-pagination surface. Sites I
found independently: the `first` + `last` exclusivity guard (single def,
literal once in production); the selection-gated `totalCount` cluster
(single writer plus sync/async attach twins); the per-target generated
connection class plus provenance cache plus test-only clear wiring; the
windowed-row consume side (marker/probe classification delegated to
`utils/connections.py`, physical-shape reads here); the keyset slicer
(codec, order-entry parsing, and `__`-path resolution composed by name);
the composition pipeline plus both resolver factories; three
resolve-time selection observers sharing one walk; one assignment alias
re-exporting the planner's parity predicate. Consumers by name of the
queryset substrate, window grammar, cursor codec, order grammar,
selection primitives, deadline/strictness/directive seams, and the list
factory guard. Three candidate shared forms considered and refused on
contract difference (keyset anchorability vs whole-ordering
determinism; captured-definition reads vs validating readers;
`ConnectionExtension`-shaped vs plain-field signature synthesis). One
working-tree-only hunk (cursor-guard feature) attributed by diff content
to external concurrent work, traced not judged.

**Counts per posited change (mine):** disposal/guard-choice/seal-new-shape
1 each at the querysets owner, zero here; pre-slice rename 2 (seal arm +
wire guard) and error-class unify 2 — family stays open; async-shape
substitution refused (shared predicate answers False for every
QuerySet, the branch must answer True); post-apply seal 1 owned + 1
absent (ambiguous, already routed, no verdict); seed/model-read 1 each
outside here; path-segment classification 2+ (member + relations
owner, remainder for the family item); exclusivity reword/scope 1 each;
count-source unify 1 owner; count-new-shape 1; class-naming 1;
provenance-unequal-definitions 1; empty-flag arithmetic 1 here,
marker classification 1 at the window owner; keyset anchor 1 (ref +
state move together), keyset flags 1; sidecar-kind 1 owner (signature +
steps + both pipelines co-located); selection vocabulary 0 here;
parity-invariant change 1 at the planner. **Owners I would choose:**
`utils/querysets.py` for F1/F2/F5/F6, `utils/querysets.py::_SealPolicy`
as candidate for F3 (family item decides), `utils/querysets.py` for F4,
`utils/relations.py::classify_path` for F7, file-local R1-R7 with R2
served by R7 and R4 served by R7, alias following
`optimizer/plans.py` — identical to the artifact in every row.

**Reconciliation.** No differences: 79/79 working members land where
the artifact puts them (my 0-78 numbering aligns row for row,
including the X1 pair at 43-44 and the `register_subsystem_clear`
`Expr` at 59); HEAD 77 with exactly the hunk pair extra working;
42 working def/class vs 40 at HEAD. Every fingerprint prefix re-hashed
from git matches (16 package/test paths plus both live-query pins;
working `3c4d5dcb…`, HEAD `93e998f2…`). Guard literal once, alias an
`Assign` once, all seven absences absent, all twelve consumer names
present. Probe `probe_w1.py` re-run green under my invocation (`ALL
OK`); my own read-only probe adds 46 checks green. Negative controls
are stated as static reasoning over pre-existing oracles — acceptable
here because no consolidation depends on an executed gate and the
item introduces no new gate; the final gate runs the suite. Pending
execution correctly absent (no mutating proof, no DB/alias/dialect
surface — `inapplicable by construction` judged sound). Coupling
correctly none. The one raw `connection.py:1666` citation is permitted
standing prose for this artifact class. Zero-edit accepted: item
baseline diff empty by my own `git diff`, coverage complete, every
candidate homed — a file item owes no production edit.

## Defects (Worker 2)

None. No new defect beyond the already-routed D3 ambiguity, which I
re-confirm present and correctly not re-homed.

## Judgment

Backstop discharged: 79/79 working-tree `ast.Module.body` members
enumerated (77 at HEAD + the 2-function external hunk, both fingerprinted),
24 challenges run, every rule terminating in one of the seven existing
plan families (re-challenged fresh on the connection side - F3 stays
open at count 2, F5 stays ambiguous-routed, F4/F10 stays rejected, the
rest are confirmed consumer roles), a file-local record with its proving
challenge (R1-R7, R-ALIAS), or a recorded rejection / external row with
difference + trigger + home (J1-J3, X1) - no consolidation owed, no
defect found, no new family named. Zero-edit result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: every
family this target touches is already indexed with this file listed;
the three refused shared forms live at their owner docstrings plus
this finding; X1 will arrive with its own item.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
16190bd37fad02f992840373865b84743916604d --
django_strawberry_framework/connection.py` is empty (0 bytes,
re-measured by the probe `item-diff-empty` check after all reads) -
the target's HEAD-vs-working split
(`93e998f2c7ea1d7f18607a6e37e394466ac75ad4` vs working
`3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a`: `_offset_cursor_prefix`,
`_reject_negative_offset_cursor`, the `from_base64` import name, and
the `_consume_fallback` non-queryset guard lines, +64/-1) predates the
item baseline and is attributed by content to external concurrent work
(a cursor-guard feature, touching none of the fingerprinted family
sites), left alone per the dispatch brief - this file item makes zero
production edits, so the dirt is not a stop. The working tree is traced
as the target throughout (79 statements; HEAD count 77 recorded for
the split). Before touching any path, the item-scoped paths were
verified clean of my own hunks; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were verified diff-empty vs the item baseline and
never touched; concurrent dirt (`tests/test_connection.py`,
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) was never edited, reverted, or tidied (test
files read as oracles only). `docs/dry/dry-file-connection.md` (this
artifact) is intentionally left out of `docs/dry/dry-0_0_15.md`'s
`--stat` scope - Worker 0 ticks the plan box. No commit. No ruff run
owed (no tracked `.py` edits; artifact is `.md` only; the probe is
untracked scratch under `docs/dry/temp-tests/dry-file-connection/`).
No `__file__`/DB record (no workspace copy - no mutating proof
exists). Scratch created (not tracked changes): this artifact and the
read-only probe `docs/dry/temp-tests/dry-file-connection/probe_w1.py`
(`ALL OK`, 70 checks; no source mutation, no DB, no shared-tree
pytest).

## Re-pass at 9031cb3d (Worker 1)

Bounded re-pass after the maintainer fast-forward (`f8a75753` ->
`9031cb3d`); HEAD confirmed `9031cb3d` at open. Prior sections above
remain as written; this section appends fresh evidence only.
Zero production edits; zero tracked files changed.

Scope: re-derive ONLY findings touching ff-changed files
(`utils/querysets.py`, `permissions.py`, `resource_policy.py`,
`schema.py`, `types/resolvers.py`, plus changed tests in their
populations); spot-confirm the rest; re-hash every fingerprint;
re-confirm X1. The `utils/querysets.py` seal changes themselves
(`carry_result_cache`, deferred-filter shape gates, wording) belong
to that file's re-trace, not this item - judged here only for
whether any connection-side count or absence moves.

Per-finding verdicts (one line each):

- F1: untouched by the ff (no fingerprint on a changed file) -
  spot-confirmed consumer role, no change.
- F2: CONFIRM consumer, count still 1 - fresh sweep finds zero
  `QuerySet(`/`sql.Query` constructions in the target (probe
  `F2-no-local-construction`, 0 ctor calls); the seal's new
  `carry_result_cache` arm lives on the same `_SealPolicy` owner
  and only the raw-list policy sets it, so no second definition.
- F3: CONFIRM family-open, count still 2 - guard body intact at
  `:1649` (fail-soft hostile-`is_sliced` arm plus `GraphQLError`
  raise, both read fresh) and the seal `sliced` arm intact
  (`if policy.reject_sliced and rebuilt_query.is_sliced:` still
  the one arm); neither line was touched by the ff.
- F4: CONFIRM rejection stands - both keyset
  `isinstance(nodes, (AsyncIterator, AsyncIterable))` branches and
  the `(Iterable, AsyncIterable)`-or-`__getitem__` union guard
  intact; `is_async_only_iterable` / `_AsyncQuerySetRows` still
  absent here; the shared predicate still answers the opposite
  question for QuerySets.
- F5: CONFIRM ambiguous-routed, no verdict - `_validate_post_orderset_result`
  still absent here (probe `F5-absent-here`); both list appliers
  still seal (3 mentions in `list_field.py`, blob unchanged);
  `_ORDERSET_RESULT_POLICY` untouched by the ff.
- F6: CONFIRM consumer, counts still 1 and 1 - `base_queryset`
  import plus default-branch `base_queryset(definition.model)`
  call intact; `model_for` still absent; neither owner symbol
  was touched by the ff.
- F7: CONFIRM family-open, count still 2+ - member body intact
  (pk-alias, per-segment `get_field`, `forward_single` plus
  non-null intermediate rule, concrete-non-relation terminal
  rule, all read fresh); `classify_path` side untouched
  (`7662b0bb` unchanged); `keyset.py` / `plans.py` unchanged.
- R3: CONFIRM file-local - all six class-gen members present;
  `registry.py` unchanged; X1 hunk touches none of them.
- R5: CONFIRM file-local - all five slicer members present;
  `keyset.py`, `plans.py`, `test_keyset_api.py` unchanged.
- R6: CONFIRM file-local - head, steps, both pipelines,
  finalizer, guards, signature, both resolvers, dispatch base,
  field factory all present; the `types/resolvers.py` ff hunk is
  comment-only (4 comment lines; the `cached =` code lines
  untouched) and the `resource_policy.py` ff hunks are
  docstring-only (`_windowed_rows` / `bounded_rows` prose; the
  `check_deadline` seam this item consumes untouched).
- R1/R2/R4/R7/R-ALIAS/J1-J3: spot-CONFIRM - guard def plus
  single call site present; live pin
  `test_genre_connection_first_and_last_rejected` still present
  (new blob, `:3671`); target work blob byte-identical so every
  other body is unchanged by construction.

Fingerprint table old -> new (work blob; HEAD blob matches work
except where noted):

- `connection.py` `3c4d5dcb` -> `3c4d5dcb` (work and HEAD blobs
  both unchanged: `93e998f2` at HEAD).
- `utils/querysets.py` `5907a1f7` -> `1539b66c` (ff-committed;
  work == HEAD).
- `list_field.py` `f357eded` -> `f357eded` (unchanged).
- `optimizer/nested_fetch.py` `4d8d37a7` -> unchanged.
- `resource_policy.py` `9205124f` -> `647133d2` (docstring-only;
  work == HEAD).
- `utils/relations.py` `7662b0bb` -> unchanged.
- `keyset.py` `df4b5e2f` -> unchanged.
- `optimizer/plans.py` `cce98531` -> unchanged.
- `registry.py` `9cc8bb55` -> unchanged.
- `utils/connections.py` `f549389e` -> unchanged.
- `optimizer/nested_planner.py` `0ad8ff5d` -> unchanged.
- `types/finalizer.py` `77fd9a2d` -> unchanged.
- `types/resolvers.py` `fc077f38` -> `f3341e6a` (comment-only;
  work == HEAD).
- `utils/directives.py` `380786cf` -> unchanged.
- `optimizer/selections.py` `a48f6172` -> unchanged.
- `tests/test_connection.py` work `e5e8990a` -> `e5e8990a`
  (byte-identical; HEAD side `bb5189a8` lacks the +46 working
  hunk, which is X1's own concurrent oracle, left alone).
- `test_library_api.py` `fd00388b` -> `ea74fb5d` (ff-committed;
  R1 live pin survives).
- `test_keyset_api.py` `a5e1fbdf` -> unchanged.
- `permissions.py` / `schema.py` (never fingerprinted here):
  ff hunks are wording/docstring-only on symbols no connection
  finding consumes (cascade error renderers, schema
  enforcement prose) - no finding moves.

Proof status: prior `probe_w1.py` re-run green (`ALL OK`, 70
checks, `item-diff-empty` still 0 bytes); new read-only probe
`docs/dry/temp-tests/dry-file-connection/probe_w1_repass.py`
(`ALL OK`, 41 checks: 79/77 statement split, F2 zero-ctor
sweep, F3 both ends, F4 branches plus absences, F5 absence
plus list 3-count, F6 import plus call plus absence, F7 four
body markers plus owner def, eleven R3/R5/R6 def spots, X1
six-way attribution plus +64/-1 shape, full re-hash table).
Both probes mutate no source and open no database. Oracle
bodies remain `static-reviewed`; no shared-tree pytest run.

Gate re-checks: guard literal still single-sited (prior probe
`guard-literal-once` green); alias still an assignment (prior
probe `alias-_ends_in_unique_column` green); all seven
absences still absent (re-pass probe); all consumer imports
still present (target blob identical).

Defects: none new. The already-routed D3 ambiguity
re-confirmed present (F5 absence intact, list seals intact),
not re-homed. The X1 hunk is still not judged here.

Pending execution: none (same as prior - no mutating proof,
no DB/alias/dialect surface; `inapplicable by construction`
holds unchanged since the target blob is identical).

Item-scoped diff state: `git diff e5c29a83... --
django_strawberry_framework/connection.py` is 0 bytes (own
diff empty); ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) diff
0 bytes vs the item baseline (untouched); working-vs-HEAD
split still exactly +64/-1 (`3c4d5dcb` vs `93e998f2`, the two
X1 functions plus the `from_base64` import name plus the
`_consume_fallback` non-`QuerySet` guard lines), predating the
item baseline, attributed by content to external concurrent
work, never edited, reverted, or tidied. Never-touched dirt
(`tests/test_connection.py` +46 X1 oracle,
`tests/utils/test_querysets.py` staged +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) left alone.

Scratch: prior `probe_w1.py` (re-run, still on disk) plus new
`docs/dry/temp-tests/dry-file-connection/probe_w1_repass.py`
(`ALL OK`, 41 checks). No commit. No ruff run owed (no
tracked `.py` edits; artifact is `.md` only; probes are
untracked scratch).

## Independent verification (Worker 2) — re-pass at 9031cb3d

Recorded from my own trace at HEAD `9031cb3d` before reconciling
against `## Re-pass at 9031cb3d (Worker 1)` above. Instrument of my
own: `ast.parse` over the working tree plus targeted string counts
and `git hash-object` / `git rev-parse` / `git diff` (read-only; no
Django setup, no SQL, no source mutation, no shared-tree pytest).

**Own bounded trace (affected rows only).** Target is the Relay
cursor-pagination surface. F2: fresh sweep finds zero
`models.QuerySet(` / `sql.Query` / bare `QuerySet(` constructions in
`django_strawberry_framework/connection.py::DjangoConnection`
surface (0/0/0); the seal's new `carry_result_cache` arm lives on
the same `utils/querysets.py::_SealPolicy` owner
(`carry_result_cache: bool = False`, 6 mentions total) and only the
raw-list policy sets it (`_RAW_LIST_SOURCE_POLICY` the single
`carry_result_cache=True`), so no second definition — count still 1
at the seal, zero here. F3: `connection.py::_guard_source_not_pre_sliced`
intact at `:1649` (fail-soft hostile-`is_sliced` arm via
`source.query.is_sliced` plus `GraphQLError` raise, both read fresh)
and the seal `sliced` arm intact
(`if policy.reject_sliced and rebuilt_query.is_sliced:` the one arm,
`if policy.reject_sliced` count 1); error classes differ
(`GraphQLError` at the wire vs `ConfigurationError` in the seal) and
timing differs (pipeline head vs during the seal) — count still 2,
family stays open. F4: both keyset
`isinstance(nodes, (AsyncIterator, AsyncIterable))` branches intact
(count 2) plus the `(Iterable, AsyncIterable)`-or-`__getitem__`
union guard intact; `is_async_only_iterable` / `_AsyncQuerySetRows`
still absent here (0/0); the shared predicate still answers the
opposite question for QuerySets (a QuerySet is both, so the shared
predicate answers False where the branches must answer True) —
rejection stands. F5: `_validate_post_orderset_result` still absent
here (0); both list appliers still seal (3 mentions in
`list_field.py`: import plus 2 calls); `_ORDERSET_RESULT_POLICY`
untouched by the ff — 1 owned plus 1 absent, ambiguous-routed, no
verdict. F6: `base_queryset` import plus default-branch
`base_queryset(definition.model)` call intact (2 mentions);
`model_for` still absent (0); neither owner symbol was touched by
the ff — counts still 1 and 1, consumer role. F7: member
`connection.py::_resolve_order_path_field` intact (pk-alias via
`current._meta.pk.name`, per-segment `get_field`,
`forward_single` plus non-null intermediate rule, concrete-non-relation
terminal rule, all read fresh); `utils/relations.py::classify_path`
side untouched (`7662b0bb` unchanged); `keyset.py` / `plans.py`
unchanged — count still 2 plus, family stays open. R1: guard
`connection.py::_guard_first_and_last` def plus single call site
present; full literal
`Connection arguments `+"`first` and `last`" intact once (the second
`mutually exclusive` in the file is the unrelated FetchMode comment);
live pin `test_genre_connection_first_and_last_rejected` still
present at `test_library_api.py:3671` asserting `mutually exclusive`
independently — file-local holds. R6: head, steps, both pipelines,
finalizer, guards, signature, both resolvers, dispatch base, field
factory all present; the `types/resolvers.py` ff hunk is comment-only
(4 comment lines; `cached = normalized_row_source(cached)` untouched)
and the `resource_policy.py` ff hunks are docstring-only
(`_windowed_rows` / `bounded_rows` prose; `check_deadline` seam
untouched). R3/R5/R7/R-ALIAS/J1-J3: spot-confirmed (six class-gen
members, five slicer members, one-walk observers, alias an `Assign`
once, three rejections on contract difference).

**Counts (mine):** F2 1 at the seal; F3 2; F4 refused; F5 1 owned
plus 1 absent; F6 1 and 1; F7 2 plus; R1 1; R2 1 owner; R3 1; R4 1
here plus 1 at the window owner; R5 1 plus 1; R6 1 owner; R7 0 here;
R-ALIAS 1 at the planner. **Owners I would choose:**
`utils/querysets.py` for F1/F2/F5/F6, `utils/querysets.py::_SealPolicy`
as candidate for F3 (family item decides), `utils/querysets.py` for
F4, `utils/relations.py::classify_path` for F7, file-local R1-R7
with R2 served by R7 and R4 served by R7, alias following
`optimizer/plans.py` — identical to the artifact in every row.

**Reconciliation vs W1 re-pass.** No differences: every per-finding
verdict (F2 consumer, F3 family-open 2, F4 rejection, F5
ambiguous-routed, F6 consumer 1/1, F7 family-open 2 plus, R1/R2/R3/R4/
R5/R6/R7/R-ALIAS file-local or consumer as recorded, J1-J3 refused,
X1 external) matches my re-derivation; the fingerprint table matches
my re-hash in all 17 rows (see below); the `permissions.py` /
`schema.py` wording-only adjudication is confirmed (cascade renderer
`unresolved` to `malformed` wording, schema enforcement prose —
symbols no connection finding consumes); the `test_keyset_api.py`
unchanged claim holds (`a5e1fbdf` work equals HEAD).

**Fingerprint verification (mine, work equals HEAD except where
noted):** `connection.py` work `3c4d5dcb…` vs HEAD `93e998f2…`
(split unchanged); `utils/querysets.py` `1539b66c…`;
`list_field.py` `f357eded…`; `optimizer/nested_fetch.py`
`4d8d37a7…`; `resource_policy.py` `647133d2…`;
`utils/relations.py` `7662b0bb…`; `keyset.py` `df4b5e2f…`;
`optimizer/plans.py` `cce98531…`; `registry.py` `9cc8bb55…`;
`utils/connections.py` `f549389e…`;
`optimizer/nested_planner.py` `0ad8ff5d…`; `types/finalizer.py`
`77fd9a2d…`; `types/resolvers.py` `f3341e6a…`;
`utils/directives.py` `380786cf…`; `optimizer/selections.py`
`a48f6172…`; `tests/test_connection.py` work `e5e8990a…` vs HEAD
`bb5189a8…` (plus 46, X1's own concurrent oracle, left alone);
`test_library_api.py` `ea74fb5d…`; `test_keyset_api.py`
`a5e1fbdf…`. Target 79 working / 77 HEAD members, 42/40 top-level
defs, extra pair exactly the X1 functions.

**Gates / negative controls (affected rows).** Guard literal still
single-sited (full literal count 1); alias still an `Assign` once;
all seven absences still absent; all consumer imports still present
(target blob identical). Oracles spell expectations independently:
the `first` plus `last` pins match `mutually exclusive` literally,
the hostile-`is_sliced` / pre-sliced rows name the wire flavor, the
keyset order-shape rows raise the boundary error — none reads from
the owner it checks (no oracle rewritten). Stated negative controls
stand as static reasoning: deleting the pre-slice guard body passes
every happy-path oracle and fails exactly the wire-flavored-message
rows (the seal still fails closed behind it with a different class,
which is why the count is 2); substituting the shared async
predicate misroutes every queryset down the sync branch; a member
returning a field for a nullable intermediate mints NULL-anchored
cursors the round-trip rows catch. Acceptable here because no
consolidation depends on an executed gate and the item introduces no
new gate; the final gate runs the suite. Prior probes re-run green
(`probe_w1.py` ALL OK, `probe_w1_repass.py` ALL OK 41 checks).

**Zero-edit.** `git diff e5c29a838c668fb810a0f01c3a0e538103bbd23a --
django_strawberry_framework/connection.py` is 0 bytes by my own run.
X1 re-confirmed: same hunk (`_offset_cursor_prefix`,
`_reject_negative_offset_cursor`, the `from_base64` import name, the
`_consume_fallback` non-`QuerySet` guard lines; `+64/-1`,
`3c4d5dcb` vs `93e998f2`), present working / absent HEAD, touching
none of the fingerprinted family sites — traced, not judged.
Ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) diff 0 bytes
vs the item baseline, untouched. Never-touched dirt
(`tests/test_connection.py` plus 46, staged
`tests/utils/test_querysets.py` plus 31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) left
alone.

**Pending.** None. No mutating proof, no DB / alias / dialect
surface touched by the probes (`inapplicable by construction` holds
unchanged since the target blob is identical); the oracles cited
remain `static-reviewed`; no shared-tree pytest run; no
`FAKESHOP_SHARDED` or Postgres cell owed.

**AGENTS.md prose check.** Zero production edits so no formatting /
tier / commit rules fire. Artifact citations use `path::Symbol`
throughout; the two raw `:1649` / `:3671` line refs and the one raw
`connection.py:1666` citation are permitted standing prose for the
`docs/dry/dry-*.md` artifact class. No process provenance, no
CHANGELOG, no `docs/review/` touch, no branch operations.

**Defects (Worker 2).** None. No new defect beyond the already-routed
D3 ambiguity, which I re-confirm present (F5 absence intact, list
seals intact) and correctly not re-homed. The X1 hunk is not judged
here by construction.

**Judgment.** Bounded re-pass discharged: every finding touching the
five ff-changed package files plus changed tests re-derived fresh at
`9031cb3d` with counts unchanged, full re-hash table verified,
gates and negative controls standing, pending correctly none,
zero-edit confirmed with X1 attribution unchanged. No consolidation
owed, no defect found, no new family named.

**Proof.** Read-only probe
`docs/dry/temp-tests/dry-file-connection-w2/probe_w2_repass.py`
(`W2-REPASS ALL OK`, 65 checks: 79/77 split, 42/40 defs, F2
zero-ctor plus 6-count carry arm with raw-list-only ownership, F3
both ends plus single-arm counts, F4 branches plus absences, F5
absence plus list 3-count, F6 import plus call plus absence, F7
markers plus owner defs, R1 def plus call plus literal-once plus
3671 pin, alias assign-once, R6 seams, X1 six-way attribution plus
64/1 shape, full 17-row re-hash, item-diff-empty). Mutates no source,
opens no database. Prior `probe_w1.py` / `probe_w1_repass.py`
re-run green under my invocation. No commit. No ruff run owed (no
tracked `.py` edits; artifact is `.md` only; probes are untracked
scratch).

## Bounded re-review at bfaee91d (Worker 2, Q3)

Phase-1 trace only. No status set, no verdict on prior findings proposed, zero
production edits. The artifact's other sections were not opened. Reasoning is
from HEAD bytes; worktree dirt is attributed below and excluded except where
noted. Tests were read as oracles, never executed.

### Dirt attribution (vs `git show HEAD:`)

- `django_strawberry_framework/connection.py` is dirty in the worktree. Its
  hunks are another session's cursor-guard work: a `from_base64` import widen,
  `connection.py::_offset_cursor_prefix`, `connection.py::_reject_negative_offset_cursor`,
  and a non-queryset branch in `connection.py::_consume_fallback` calling them.
  None of these touch the two subjects (list_field determinism machinery, seal
  wording/policy), so they are kept out of the trace below except for this
  attribution. All symbol claims below hold on HEAD bytes.
- `django_strawberry_framework/list_field.py` is dirty by one docstring-only
  hunk in `list_field.py::_validate_relay_djangotype_target` (reconsideration
  triggers prose). No behavior change; noted where that symbol is consumed.
- `django_strawberry_framework/utils/querysets.py` is clean (worktree equals
  HEAD). Read-only regardless; never edited.

### (1) Connection's uses of list_field's ordering/determinism machinery

Exactly one list_field symbol is consumed, and it is not ordering machinery:

- `list_field.py::_validate_relay_djangotype_target`, imported once at
  `connection.py` module top and called once in `connection.py::DjangoConnectionField`.
  Role: consumer (DRY 6, compose by name). Contract: construction-time
  DjangoType-target guard (registered target plus Relay-Node shape) with the
  caller's own relay error wording. The delta's docstring hunk does not change
  its behavior. The offset-guard rework does not touch it.

Zero consumption of the determinism classifiers. `connection.py` contains no
reference to `list_field.py::_is_deterministic_order_name`,
`list_field.py::_is_deterministic_order_term`,
`list_field.py::_is_deterministic_order_value`,
`list_field.py::_is_deterministic_order_condition`,
`list_field.py::_resolve_order_field_path`,
`list_field.py::_is_deterministic_order_field_path`,
`list_field.py::_is_deterministic_order_reference`,
`list_field.py::_approved_order_transform`,
`list_field.py::_is_deterministic_order_lookup_chain`,
`list_field.py::_is_deterministic_order_predicate_reference`,
`list_field.py::_selected_ordering`, `list_field.py::_has_deterministic_ordering`,
`list_field.py::_is_model_default_ordering_active`, `list_field.py::_READABLE_ORDER_LEAVES`,
or any `_APPROVED_ORDER_*` / `_TRANSPARENT_ORDER_EXPRESSIONS` table. No call,
no duplicate, no restatement.

Connection's ordering needs are served from a different owner:

- `optimizer/plans.py::effective_connection_order`, called once in
  `connection.py::_finalize_queryset` (resolve-time deterministic total order;
  same implementation the plan-time window order uses — the cursor-parity
  invariant). Role: consumer.
- `optimizer/plans.py::ends_in_unique_column`, re-exported as the module alias
  `connection.py::_ends_in_unique_column` for spec-030 test pins. Role: alias,
  not a definition (DRY 6 — canonical implementation lives in
  `optimizer/plans.py`).
- `optimizer/plans.py::order_entry_name_and_direction` and
  `optimizer/plans.py::order_entry_has_explicit_nulls`, called in
  `connection.py::_keyset_order_ref`. Role: consumer.

Near-miss examined and separated (not duplication): `connection.py::_keyset_order_ref`,
`connection.py::_resolve_order_path_field`, `connection.py::_keyset_order_state`
validate ordering entries for keyset cursor-anchorability (non-nullable
concrete column, supported cursor field, no explicit nulls positioning), while
the list_field classifiers certify offset-window repeatability (deterministic
total order across the two queries a window spans). Change challenge: adding an
approved deterministic form to the offset guard does not move keyset anchoring;
widening keyset-anchorable columns does not move offset certification. Distinct
contracts, distinct reasons to change — intentional separation under DRY 7.

### (2) Connection's composition of sealed querysets and seal wording

Consumed seal-boundary symbols (all from `django_strawberry_framework/utils/querysets.py`,
all as consumers, all under the default policy — no explicit `policy=` argument
is passed anywhere in `connection.py`):

- `utils/querysets.py::prepared_resolver_source`, called once in
  `connection.py::_prepare_pipeline_source` (refusal plus coercion plus
  is-queryset decision, shared with the list field's runners).
- `utils/querysets.py::apply_type_visibility_sync`, called once in
  `connection.py::_pipeline_sync`.
- `utils/querysets.py::apply_type_visibility_async`, called once in
  `connection.py::_pipeline_async`.
- `utils/querysets.py::base_queryset`, called once in
  `connection.py::_build_connection_resolver` (default-field seed).
- `utils/querysets.py::reject_awaitable_sync_source`,
  `utils/querysets.py::reject_residual_async_source`,
  `utils/querysets.py::reject_async_iterable_in_sync_context` — the three
  color guards threaded through the pipeline head and resolver branches.

Not referenced anywhere in `connection.py`: `utils/querysets.py::_SealPolicy`,
`utils/querysets.py::_DEFAULT_SEAL_POLICY`,
`utils/querysets.py::_CASCADE_SEAL_POLICY`,
`utils/querysets.py::_PREFETCH_CHILD_POLICY`,
`utils/querysets.py::_UNRECOMPOSED_CHILD_POLICY` (retired),
`utils/querysets.py::_LIST_ARGUMENT_VISIBILITY_POLICY`,
`utils/querysets.py::_seal_or_defect`,
`utils/querysets.py::_defect_message`,
`utils/querysets.py::_visibility_result_error`,
`utils/querysets.py::_raw_list_source_message`,
`utils/querysets.py::_prepared_visibility_source`,
`utils/querysets.py::_validate_post_orderset_result`,
`utils/querysets.py::_snapshot_routing_intent`. No seal message text is quoted
or depended on; connection's own `GraphQLError` wordings (sidecar-input rule,
totalCount-countable rule, pre-sliced rule, non-iterable rule, keyset contract
errors) are independently owned prose.

### (3) Definition counts

New ordering form (determinism classifiers plus approved-form tables):

- Authoritative definitions: exactly one site, `list_field.py` — 8 tables
  (`list_field.py::_READABLE_ORDER_LEAVES`,
  `list_field.py::_TRANSPARENT_ORDER_EXPRESSIONS`,
  `list_field.py::_APPROVED_ORDER_FUNCTIONS`,
  `list_field.py::_APPROVED_ORDER_AGGREGATES`,
  `list_field.py::_APPROVED_ORDER_TRANSFORMS`,
  `list_field.py::_APPROVED_ORDER_LOOKUPS`,
  `list_field.py::_APPROVED_ORDER_NODES`,
  `list_field.py::_ORDER_VALUE_CONTAINERS`) and 13 classifiers
  (`list_field.py::_resolve_order_field_path`,
  `list_field.py::_is_deterministic_order_field_path`,
  `list_field.py::_is_deterministic_order_reference`,
  `list_field.py::_is_deterministic_order_name`,
  `list_field.py::_is_deterministic_order_term`,
  `list_field.py::_is_deterministic_order_value`,
  `list_field.py::_approved_order_transform`,
  `list_field.py::_is_deterministic_order_lookup_chain`,
  `list_field.py::_is_deterministic_order_predicate_reference`,
  `list_field.py::_is_deterministic_order_condition`,
  `list_field.py::_selected_ordering`,
  `list_field.py::_has_deterministic_ordering`,
  `list_field.py::_is_model_default_ordering_active`). In `connection.py`: 0
  definitions, 0 calls.

New seal code:

- Authoritative definitions: exactly one site, `utils/querysets.py` —
  `utils/querysets.py::_SealPolicy`, 6 live policy instances
  (`utils/querysets.py::_DEFAULT_SEAL_POLICY`,
  `utils/querysets.py::_CASCADE_SEAL_POLICY`,
  `utils/querysets.py::_PREFETCH_CHILD_POLICY`,
  `utils/querysets.py::_LIST_ARGUMENT_VISIBILITY_POLICY`,
  `utils/querysets.py::_ORDERSET_RESULT_POLICY`,
  `utils/querysets.py::_RAW_LIST_SOURCE_POLICY`), `utils/querysets.py::_seal_or_defect`,
  and the renderer family (`utils/querysets.py::_raw_list_source_message`,
  `utils/querysets.py::_visibility_result_error`,
  `utils/querysets.py::_prepared_visibility_source`,
  `utils/querysets.py::_defect_message`). Retired symbol
  `utils/querysets.py::_UNRECOMPOSED_CHILD_POLICY`: 0 definitions at bfaee91d
  (was 1 at 9031cb3d); its uses were repointed to
  `utils/querysets.py::_PREFETCH_CHILD_POLICY` in the walker and in the two
  colored-runner docstrings. Deleted wording arms: 5 (one `combined` arm in
  `utils/querysets.py::_raw_list_source_message`; `evaluated` plus `routing`
  arms in each of `utils/querysets.py::_visibility_result_error` and
  `utils/querysets.py::_prepared_visibility_source`). In `connection.py`: 0
  seal definitions, 0 explicit policy references, 0 wording dependencies.

### (4) Owners I would choose (DRY 7)

- Determinism classifiers and approved-form tables: `list_field.py`. It owns
  the offset-guard contract (the only consumer via
  `list_field.py::_has_deterministic_ordering` and
  `list_field.py::_is_model_default_ordering_active`); it is the narrowest
  cohesive owner every legitimate consumer can depend on, and connection is
  not a legitimate consumer of offset-window repeatability (its order comes
  from `optimizer/plans.py`).
- Seal policies, seal mechanics, and wording dispatch: `utils/querysets.py`.
  Existing owner with that responsibility; every consumer already depends on
  it, so dependency direction confirms it. Connection stays a
  default-policy composer, never a policy author.
- Connection keeps its own guards (`connection.py::_guard_first_and_last`,
  `connection.py::_guard_source_not_pre_sliced`,
  `connection.py::_guard_sidecar_input_against_non_queryset`,
  `connection.py::_guard_total_count_countable`) — GraphQL-contract rules with
  distinct reasons to change from either upstream family.

### (5) Whether either delta breaks anything derived

Delta (a), list_field determinism rework: no breakage derived. The new
`opts`/`seen`/`prefix` parameters default (`None`/empty/`""`), preserving
every existing two-argument call shape; all intra-file call sites were updated
in the same diff; `connection.py` makes no direct calls so no call site can
drift. `_READABLE_ORDER_LEAVES` tuple-to-frozenset changes membership-test
performance only. The only shared symbol's behavior (`_validate_relay_djangotype_target`)
is untouched (worktree hunk is prose). No GOAL.md trust-boundary row is
implicated: wire cursors/offsets never reach these classifiers (connection
validates them via the first/last guard, `SliceMetadata`, the keyset codec,
and — worktree only — the cursor-guard hunk, all outside this family). No
defect: no contract row, hence no reaching input.

Delta (b), querysets seal wording plus retired policy: no breakage derived.
The 5 deleted arms render defect codes the connection-reached seals cannot
emit: `connection.py` seals only under `utils/querysets.py::_DEFAULT_SEAL_POLICY`
(where `require_unevaluated` is off by documented design — an evaluated source
re-seals to a fresh unevaluated queryset at a cost of one query, per the
`utils/querysets.py::_SealPolicy` prose — and routing/alias/combined defects
need expectations this surface never states, per the renderer docstrings), and
it never reaches `utils/querysets.py::_RAW_LIST_SOURCE_POLICY`. The retired
`utils/querysets.py::_UNRECOMPOSED_CHILD_POLICY` was never referenced by
`connection.py`; its repointing is walker-internal. Exhaustiveness is
preserved by `utils/querysets.py::_defect_message`, which still fails closed
with framework-defect wording for any code without an arm (DRY 8: same
observable behavior — same exceptions, same effects — on every
connection-reachable input). Oracle check: no live test pins a deleted wording
(`combining queries` and the deleted routing/evaluated phrasings have zero
source matches; `requires an unevaluated` matches only a stale compiled
artifact); the surviving `changed database routing intent` pins belong to
`utils/querysets.py::_validate_post_orderset_result`, a renderer
`connection.py` never calls. No defect: no contract row, hence no reaching
input.

### Freshness fingerprints

- HEAD: `bfaee91d`. Diff range established from history:
  `9031cb3d..bfaee91d` (per-file diffs read for `list_field.py` and
  `utils/querysets.py`; `connection.py` delta in range is nil at HEAD —
  its worktree hunk is uncommitted).
- Package files (worktree `git hash-object` vs `HEAD:` blob): connection.py
  `3c4d5dcb` vs `93e998f2` (dirty, attributed above); list_field.py
  `d6af6164` vs `ce682d5f` (dirty, docstring-only); utils/querysets.py
  `96618fba` vs `96618fba` (clean).
- Contract and role sources (clean, worktree equals HEAD): DRY.md `e8151123`,
  worker-2.md `4f089ea4`, GOAL.md `7dfbef5c`, AGENTS.md `e42247fa`.
- Oracles read (worktree blobs): tests/test_connection.py `e5e8990a`,
  tests/utils/test_querysets.py `8b39c9f8`, tests/test_list_field.py
  `2f77f77d`, tests/utils/test_connections.py `ba76f398`.
- Searched populations: full `connection.py` HEAD text (2321 lines, both
  halves read); `list_field.py` determinism region and module-symbol grep;
  `utils/querysets.py` seal-policy region, all three renderer bodies, and
  module-symbol grep; package-wide grep for each retired/renamed seal symbol;
  test-tree grep for every deleted wording. Any fingerprint change reopens
  this trace.

PHASE-1-TRACE-RECORDED — docs/dry/dry-file-connection.md

## Bounded re-review reconciliation at bfaee91d (Worker 2, Q3 phase 2)

Phase-1 integrity: the phase-1 section above is intact and was pre-exposure
(written before this artifact was opened; marker verified last line before
this append; all phase-1 hashes re-verified identical below). Full artifact
read authorized for this phase only (Status `verified`, Run
`0.0.15 2026-09-18-1`, both re-pass sections). Only J1/F2/F6/F3 reconciled;
all other rows stay settled. Never read any worker-memory. Zero production
edits; no commit.

(a) J1 survives. The new classifier parameters are recursion state, not a
contract change: `opts` names the model a path resolves against (the related
model while a relation expansion is being read),
`seen` is the visited `(model, path)` set refusing relation cycles Django
would reject, `prefix` names lifted references the way the outer query
resolves them — all defaulted, all threaded through existing call sites in
the same diff. `connection.py::_keyset_order_ref` is byte-untouched
(`connection.py` absent from the `9031cb3d..bfaee91d` stat) and still
composes `optimizer/plans.py::order_entry_name_and_direction` plus
`optimizer/plans.py::order_entry_has_explicit_nulls` per entry; it still
calls zero determinism classifiers. Trigger check: the keyset path still
certifies no whole ordering, the list path still mints no value cursors —
trigger not fired. Rejection stands.

(b) F2 survives. Verdict rests on the phase-1 zero-dependency plus
zero-match evidence, re-stated: `connection.py` passes no explicit seal
policy, references no seal policy symbol, and quotes no seal wording; the 5
deleted arms render codes the default-policy seals connection reaches cannot
emit; no live source pins a deleted string (only a stale compiled artifact,
not a test); the surviving routing-intent pins belong to
`utils/querysets.py::_validate_post_orderset_result`, a renderer connection
never calls. Seal count still 1 at the seal, zero here. Consumer role
stands; gate (seal suite plus hostile-shape containment rows) unchanged.

(c) F6 survives. Body-identical check run: function-text diff of
`utils/querysets.py::base_queryset` at `9031cb3d` vs `bfaee91d` shows only
docstring prose lines (the `.using().all()` spelling note condensed); the
executable body is byte-identical. The default-branch
`base_queryset(definition.model)` call and the import are intact; `model_for`
still absent here. Counts still 1 and 1, consumer role stands.

(d) F3 survives. Slicing-untouched check run: zero `is_sliced` lines in
either delta file over `9031cb3d..bfaee91d`; `connection.py` untouched in
range, so `connection.py::_guard_source_not_pre_sliced` and the seal
`sliced` arm are both intact by construction. Count still 2, family stays
open for its family item.

X1 dirt containment: the worktree cursor-guard hunk touches none of the four
findings — zero added/removed lines mentioning `_keyset_order_ref`,
`prepared_resolver_source`, `apply_type_visibility`, `base_queryset`,
`is_sliced`, `_guard_source_not_pre_sliced`, `_keyset_order_state`, or
`_finalize_queryset`; shape still exactly +64/-1. It stays traced, not
judged, and out of these findings.

Re-hashes (worktree vs HEAD): connection.py `3c4d5dcb` vs `93e998f2`
(split unchanged from X1 record); list_field.py `d6af6164` vs `ce682d5f`
(docstring-only hunk, unchanged); utils/querysets.py `96618fba` clean;
HEAD blobs list_field `ce682d5f`, querysets `96618fba`. Any change reopens.

Defects (Worker 2): none. No new defect; D3 ambiguity stays routed, not
re-homed.

Verdict: `verified` — every Q3 finding stands at `bfaee91d`; no finding
moved, no consolidation owed. Status already reads `verified`, so no Status
edit is made. Plan rows for Worker 0: tick the `dry-file-connection` item
`verified` with Q3 freshness `bfaee91d` (fingerprints above); close the Q3
reconciliation queue with J1 rejected-standing, F2/F6 consumer-standing,
F3 family-open-unchanged.

## Run-7 scoped re-trace (Worker 1, REOPENED item)

Run: 0.0.15 2026-09-28-7. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh, CONFIRMs or
REVISEs every prior finding, and assigns the drift's new shape. Zero
production edits; zero tracked files changed.

### Scope and fingerprints

Drift base `5ee86193` is an ancestor of HEAD `0c0537e2` (HEAD unmoved at
close). For THIS target the drift base already equals HEAD bytes:

- `5ee86193:connection.py` blob `4894f90f` == `HEAD:connection.py` blob
  `4894f90f` (2317 lines). `5ee86193..HEAD` delta for this file is nil.
- Committed delta since the prior stamp (`bfaee91d`, blob `93e998f2`)
  is exactly two commits, 69+/10-: `fee87ac4` (seal the OrderSet return
  at the connection field) + `c87f4f98` (seal the FilterSet return with
  the same post-sidecar seal). That is the recorded sidecar-pipeline
  rewrite: `_sidecar_steps` kind column, new
  `connection.py::_sidecar_visibility_policy`, both pipelines consuming
  `apply_filterset/orderset_sync/async` from `utils/querysets.py`.
- Worktree blob `1fca6266` (2348 lines) vs HEAD `4894f90f`: 32 hunks,
  169+/138-, all concurrent-external (no `## Owned changes` ledger row
  names this file; I made zero edits). Every hunk attributed by content
  below; the trace itself reads HEAD bytes (`git show HEAD:` + AST over
  that text), never the dirty tree.

Worktree dirt attribution (all 32 hunks, grouped by content; X1's
successor - see X1-REVISED):

- Truth-module migration (8 hunks): `from .utils import truth` import;
  `truth.class_dict` in `_keyset_connection_context`;
  `truth.IdentityMap` for `_connection_type_cache` (+ new
  `_window_edge_class_cache` / `clear_window_edge_class_cache` /
  registry wiring); `truth.name` / `truth.kind` / `truth.is_instance` /
  `truth.own_attr` replacing `_safe_class_name` / `_safe_type_name` /
  `hasattr.__getitem__` (import line drops the two `_safe_*` names).
- Cursor-guard successor (3 hunks): `from_base64` import widen; new
  `_reject_negative_offset_cursor(prefix, argument, value)` +
  `_consume_fallback` non-queryset guard lines calling it with
  `_window_edge_class(cls).CURSOR_PREFIX`. The prior X1
  `_offset_cursor_prefix` helper is gone (restructured by its owner).
- `last: 0` cap successor (2 hunks): new `_cap_offset_last_zero_page` +
  `_consume_fallback` quirk trim (sync + awaitable arms).
- Fallback laziness (3 hunks): `_build_windowed_fallback`
  `source` -> `source_factory` + docstring; `_resolve_from_window`
  condition reorder; relation-resolver `source =` moved below the
  window branch with a lambda factory at the call site.
- `_window_edge_class` memoization (1 hunk): cache read/populate around
  the existing derivation.
- Hostile-shape guard narrowing (4 hunks): try/except deleted around
  `_keyset_order_ref` parse, `_guard_source_not_pre_sliced`
  `is_sliced` read, all four `_finalize_queryset` reads/applies,
  `_window_rows_are_annotated` - bare reads now.
- Docstring/comment-only (11 hunks): `_resolve_from_window` keyset
  backend prose (2), `_consume_window` entry prose, `FieldDoesNotExist`
  hoist to module top (behavior-neutral import move),
  `_resolve_keyset_connection` + `_KeysetPage` + `resolve_connection`
  spec-Decision numbering + relation-resolver + `DjangoConnectionField`
  prose.

### Enumeration at HEAD bytes

Instrument: `ast.parse` over `git show HEAD:` text, counting
`ast.Module.body` - **78 top-level statements** (prior 77 + exactly
one: `def _sidecar_visibility_policy` at index 72, directly after
`def _sidecar_steps`; probe `policy-after-steps`). 41 top-level
def/class (prior 40 + the same one). Every other member keeps its
prior index, home, and body except the drift hunks
(`_sidecar_steps` 3-tuple, both pipelines, the querysets import
block). X1's pair is absent at HEAD (0 matches) and restructured in
the worktree (see X1-REVISED). Full 78-row table not reprinted: prior
rows 0-71 stand verbatim, new row 72
(`def _sidecar_visibility_policy` -> R6), prior rows 72-76 shift to
73-77 with homes unchanged.

Fresh HEAD-blob fingerprints (all evidence files are worktree-dirty
concurrent work, so every claim below cites the `HEAD:` blob):
connection.py `4894f90f`, utils/querysets.py `3616927d`,
list_field.py `21380eb7`, utils/relations.py `8dbc3fe6`, keyset.py
`df4b5e2f`, optimizer/plans.py `cce98531`, registry.py `81bd561c`,
utils/connections.py `f549389e`, optimizer/nested_planner.py
`b4dfd4a6`, types/finalizer.py `de34ae2a`, types/resolvers.py
`72d62dc4`, utils/directives.py `380786cf`,
optimizer/selections.py `a48f6172`, resource_policy.py `4b69e974`,
optimizer/nested_fetch.py `4d8d37a7`, utils/policies.py `8c881c0a`,
tests/test_connection.py `dcf1b382`. Any change reopens.

### CONFIRM verdicts (16, each re-proved at current bytes)

- F1 (consumer): the three color guards are still threaded by name
  (`reject_awaitable_sync_source`, `reject_residual_async_source`,
  `reject_async_iterable_in_sync_context` all present) and
  `_dispose_sync_awaitable` is still absent here. C1/C2 re-run: 1
  each at the querysets owner. CONFIRM.
- F2 (consumer, count 1): still zero `models.QuerySet(` /
  `sql.Query` constructions, zero `_seal_or_defect` /
  `_defect_message` references. Evidence change noted, verdict
  unchanged: both pipelines now pass an explicit
  `policy=_sidecar_visibility_policy(steps)` (count 2), so the prior
  "no explicit `policy=` anywhere" line is superseded - but no seal,
  policy, or wording is DEFINED here; the selection composes two
  owner policies by name (assigned file-local under R6). C3 re-run:
  1 at the seal. CONFIRM.
- F3 (family-open, count 2): `connection.py::_guard_source_not_pre_sliced`
  intact including the fail-soft hostile-`is_sliced` arm; the seal's
  `reject_sliced` arm intact in HEAD querysets (2 mentions). C4/C5
  re-run: 2 and 2 (wire `GraphQLError` vs seal `ConfigurationError`,
  head timing vs seal timing). CONFIRM.
- F4 (rejection stands): both keyset
  `isinstance(nodes, (AsyncIterator, AsyncIterable))` branches intact
  (count 2); the `(Iterable, AsyncIterable)`-or-`__getitem__` union
  guard intact; `is_async_only_iterable` / `_AsyncQuerySetRows`
  still absent. Substitution would still misroute every queryset.
  C6 re-run: refused. CONFIRM.
- F6 (consumer, 1 and 1): `base_queryset(definition.model)` default
  seed intact; `model_for` still absent. The drift extends the
  captured-read discipline (`model=definition.model` now also
  passed to the four `apply_*` entries) without adding a re-read.
  C8/C9 re-run: 1 and 1. CONFIRM.
- F7 (family-open, 2+): member intact (pk-alias via
  `current._meta.pk.name`, per-segment `get_field`, `forward_single`
  + non-null intermediate rule, concrete-non-relation terminal
  rule); `utils/relations.py::classify_path` still defined once at
  HEAD; `relation_kind` still the only relations import (2
  mentions). C10 re-run: 2+. CONFIRM.
- R1/R2/R3/R4/R5/R7/R-ALIAS (file-local or consumer as recorded):
  exclusivity guard + literal-once intact; count writer + attach
  twins intact; all six class-gen members + provenance identity
  check intact; all eight window members intact; all five slicer
  members intact; one-walk observers intact; alias still one
  `Assign`. C11-C20, C22, C23 re-run with identical counts.
  CONFIRM (7 rows).
- J1 (rejection stands): zero `_is_deterministic_order*` /
  `_has_deterministic_ordering` references here;
  `connection.py::_keyset_order_ref` still per-entry anchorability
  (composes `order_entry_name_and_direction` +
  `order_entry_has_explicit_nulls`, 4 mentions, zero determinism
  classifiers). Trigger not fired. CONFIRM.
- J2 (rejection stands): factory still validates through imported
  `list_field.py::_validate_relay_djangotype_target`; all
  definition reads still captured-reads (drift adds more of the
  same shape, no validator). Trigger (a substitution bug traced to
  a connection read) not observed. CONFIRM.
- J3 (rejection stands): `connection.py::_synthesized_signature`
  intact; no third flavor synthesizes `ConnectionExtension`-shaped
  signatures. Trigger not fired. CONFIRM.

### REVISE verdicts (3)

- F5 REVISED: ambiguous-routed -> CONSUMER (family stays `open`
  for re-census). What moved: both pipelines now route both
  sidecars through the one owner seal -
  `apply_orderset_sync/async` + `apply_filterset_sync/async`
  (imported from `utils/querysets.py`), each a thin entry over the
  single core `utils/querysets.py::_apply_sidecar_sync/_async`
  (freeze via `_snapshot_routing_intent` BEFORE the override runs,
  validate via `_validate_post_orderset_result` under
  `_SIDECAR_RESULT_POLICY`; bodies read at HEAD). The direct
  `set_class.apply_sync/async` calls are gone (0 matches); the
  kind dispatch (`apply_orderset_* if kind == "order" else
  apply_filterset_*`) is the only sidecar-apply code left here.
  C7 re-run: an override returning a sliced qs through a
  connection now forces exactly **1** definition (the owner core) -
  the D3-routed ambiguity ("list seals, connection does not") is
  RESOLVED by the landing, on both sidecar kinds (FilterSet
  returns are sealed now too - new coverage, same owner). Gate:
  committed HEAD oracles
  `test_connection_seals_a_malformed_apply_sync_result`,
  `test_connection_seals_a_malformed_filter_apply_sync_result`,
  `test_connection_visibility_rejects_a_combinator_hook_only_when_a_sidecar_runs`
  (+ healthy-override twins) spell expectations independently.
  Owner stays `utils/querysets.py`; the family item owes a
  re-census (2 surfaces x 2 kinds over 1 core).
- R6 REVISED: file-local, extended. What moved: `_sidecar_steps`
  returns `(kind, set_class, input)` 3-tuples (both appends read);
  new `_sidecar_visibility_policy(steps)` selects
  `_LIST_ARGUMENT_VISIBILITY_POLICY if steps else
  _DEFAULT_SEAL_POLICY` (body read; `_SealPolicy` used here only
  as import + return annotation); both pipelines consume the four
  owner entries by name. The conditional selection is file-local:
  package-wide HEAD sweep finds `_LIST_ARGUMENT_VISIBILITY_POLICY`
  in exactly 3 files (querysets defines it; list_field passes it
  unconditionally at 2 sites with no selection; only connection
  selects). C21 re-run (third sidecar kind): signature + steps +
  dispatch + selection move together here (**1 owner**); the seal
  needs only a thin fifth `apply_*` entry following the existing
  4-over-1 shape at the owner - the core stays 1. Sync/async twin
  re-compared by behavior: steps + policy shared verbatim, halves
  differ only in the awaited visibility/apply steps and the async
  guard - the recorded principle-5 shape, no divergence. Matrix
  axis 1 revised accordingly (connection now mirrors the list
  seal, converged through the shared owner by name - the good
  direction); axes 2-6 re-discharged unchanged (axis 5 gains the
  seal oracles above; axis 6: the D3 omission is closed, no member
  lacks a guard its contract requires).
- X1 REVISED: prior X1 hunk (+64/-1, `_offset_cursor_prefix` +
  `_reject_negative_offset_cursor`) is SUPERSEDED, still external.
  It is absent at HEAD (0 matches) and its worktree successor is
  restructured (no `_offset_cursor_prefix`; new 3-arg
  `_reject_negative_offset_cursor`) inside a larger 32-hunk
  concurrent patch (truth migration, `last: 0` cap, fallback
  laziness, edge-class memoization, guard narrowing, prose -
  every hunk attributed by content above). Still traced, not
  judged; still touches none of the drift's seal sites. No
  verdict, no challenge - its owning change carries them.

### Canonical-copy split citation

The verified File `utils/policies.py` outcome (Status: `verified`,
Run `0.0.15 2026-09-22-5`; families `schema-construction-policy-ladder`,
`policy-authority-isolation`, `hostile-mapping-hardening`) does not
touch this target: HEAD `connection.py` contains zero references to
`canonical_policy`, `_PACKAGE_*`, `DEFAULT_ERROR_POLICY`, or
`DEFAULT_RESOURCE_POLICY` (probe `no-canonical-copy`). The only
POLICY symbols here are the querysets seal policies
(`_DEFAULT_SEAL_POLICY`, `_LIST_ARGUMENT_VISIBILITY_POLICY`) - a
different family (`sealed-execution-queryset`, F2). No finding moves.

### Defects

None. No new defect; the D3 ambiguity is closed by the landing (F5
REVISED), not re-homed. Worktree dirt is concurrent-external, never
judged.

### Pending execution

None. The execution proof is the read-only probe
`/tmp/dry_conn_retrace_probe.py` (`RUN7-RETRACE ALL OK`, 74 checks:
78-member HEAD AST, def count, insertion point, F5/R6 drift-shape
markers, all CONFIRM identity/count/absence claims, J1-J3 triggers,
canonical-copy absence) - mutates no source, opens no database, runs
no pytest, so no workspace copy was owed and no `__file__`/DB record
applies. Oracle bodies remain `static-reviewed`. No sharded/PG cell
owed (`inapplicable by construction` - the probe touches no database,
alias, or dialect decision).

### Judgment

Backstop re-discharged at HEAD bytes (`4894f90f`, 78 members):
16 CONFIRM rows re-proved with fresh evidence, 3 REVISE rows (F5
D3-resolved consumer, R6 extended file-local, X1 superseded
external), 0 new families named, 0 defects. Zero-edit result stands.

### Item-scoped diff state

`git diff 6d9a0d751155d688a5f8bff40563f651024842d4 --
django_strawberry_framework/connection.py` is 0 bytes (own diff
empty - all dirt predates the item baseline); attribution is by
content vs HEAD (`git show HEAD:` + full `git diff HEAD` read, all
32 hunks grouped above): no ledger row names this file and I
authored zero hunks, so every hunk is concurrent-external and the
dirt is not a stop for this zero-edit file item. No tracked file
touched; no ruff run owed (artifact is `.md` only and the
source-layout gate reports it excluded; probe is `/tmp`-only
scratch).

## Index rows for Worker-0

CONFIRMed rows (unchanged text - families keep name, owner, files,
status; connection-side role re-proved at HEAD `4894f90f`):

- `awaitable-refusal-and-disposal` (F1 consumer) - no change.
- `sealed-execution-queryset` (F2 consumer) - no change.
- `recomposition-illegal-source-rejection` (F3 family-open, count 2)
  - no change.
- `async-only-queryset-row-adapter` (F4 rejection) - no change.
- `queryset-seed-and-model-read` (F6 consumer) - no change.
- `orm-lookup-path-resolution` (F7 family-open, count 2+) - no
  change.

REVISEd row (verdict moved; owner unchanged, re-census owed):

- `post-set-apply-result-validation` - connection role moves from
  unguarded-member (D3 ambiguity, routed) to CONSUMER of the one
  post-sidecar seal (`utils/querysets.py::_apply_sidecar_sync/_async`
  via the four `apply_*` entries; both sidecar kinds sealed).
  Family stays `open`; the family item owes a re-census (2
  surfaces x 2 kinds over 1 core) instead of the D3 routing.

New rows: none (the new `_sidecar_visibility_policy` selection is
file-local under R6; no new family named). No `## Families` item
owed; zero `## Owned changes` rows.

## Run-7 verification (Worker 2)

Run: 0.0.15 2026-09-29-7. Expectation-first: the byte-level trace
below (counts, blobs, hunks, insertion point) was derived from
`git show` + AST before the run-7 section was opened; prior sections
were then read to judge each CONFIRM/REVISE against its prior.
W1's probe was re-run green and every claim re-proved independently
by `/tmp/w2_conn_verify.py` (107 checks, ALL OK) plus body reads.
Zero production edits; this section + the `Status:` line are the
only tracked changes.

### Expectation-first trace

- HEAD `0c0537e2` unmoved; target HEAD blob `4894f90f` (2317
  lines), worktree `1fca6266` (2348 lines), 32 hunks.
- `ast.Module.body` over HEAD bytes: 78 members; `bfaee91d` bytes:
  77; delta exactly one added
  `FunctionDef:_sidecar_visibility_policy` at index 70, directly
  after `_sidecar_steps` (69); prior HEAD rows 0-69 stand, 70-76
  shift to 71-77. 41 def/class at HEAD.
- `5ee86193:connection.py` blob == HEAD blob; `5ee86193..HEAD`
  nil for this target; `bfaee91d..HEAD` exactly `fee87ac4` +
  `c87f4f98` (69+/10-).
- ITEM_BASELINE `6d9a0d75` blob == worktree blob for this target
  (32 hunks pre-date the item); item-scoped diff 0 bytes.
- No `_PACKAGE_*` / `canonical_policy` surface here (0 matches).

### Per-judgment results

1. Enumeration: STANDS on count and delta (78 = 77 + 1, same
   member, same insertion point, same def count). Locator
   sub-detail wrong, see D-W2-1 (record only; assignment
   unaffected).
2. Hunk attribution: the call STANDS - all 32 hunks
   concurrent-external (baseline-blob equality is conclusive; no
   ledger row; W1 authored zero hunks; trace reads HEAD bytes).
   Every hunk's content matches its group's description; the
   per-group arithmetic does not denote distinct-hunk counts, see
   D-W2-2 (record only; 7 bullets as written, not 8 groups).
3. Drift scope: STANDS fully - base bytes == HEAD bytes, rewrite
   exactly the two named commits since `bfaee91d`, delta shape
   confirmed.
4. CONFIRMs (16): all re-proved at HEAD bytes, substance holds
   in every row (F1 guards threaded by name with disposal
   absent; F2 zero seal/wording definitions with the new
   `policy=` x2 composing owner policies; F3 guard + seal arm
   with wire-vs-seal classes; F4 twin branches + union guard;
   F6 seed + captured reads; F7 member + single owner; R-rows
   members present with single-site counts; J1-J3 triggers
   unfired). Two parenthetical mention-counts are scoped to an
   unstated subset, see D-W2-3 (record only).
5. REVISEs (3): all ENDORSED. F5: pipelines consume the four
   thin `apply_*` entries over the one `_apply_sidecar_*` core
   (freeze before override, validate under
   `_SIDECAR_RESULT_POLICY`, both kinds, 0 direct
   `set_class.apply_*` calls); C7 re-run gives 1 definition;
   D3 closed by the landing; the three named oracles plus both
   healthy-override twins exist at HEAD tests and spell
   expectations independently. R6: steps are 3-tuples, the
   policy selection is file-local (exact 3-file sweep:
   querysets defines, list_field passes unconditionally x2,
   only connection selects), twins share steps+policy with
   colored awaits only, matrix axes re-discharged. X1: absent
   at HEAD (0 matches), worktree successor restructured (no
   `_offset_cursor_prefix`, 3-arg guard), dirt touches none of
   the drift's seal sites.
6. Canonical-copy split: correctly absent/inapplicable (0
   matches for all four symbols; the POLICY symbols here belong
   to the seal family F2).
7. Zero-defect call: STANDS. No new family owed, no target
   defect found, D3 correctly closed-not-rehomed.

### Record defects (Worker 2)

Imprecise artifact metadata; none moves any verdict, index row,
or downstream decision, so no resubmission is owed - the
corrections stand here:

- D-W2-1 (enumeration locator): "new row 72" / "prior rows
  0-71 stand / 72-76 shift to 73-77" miscoordinates the
  insertion (prior working-tree row number carried into HEAD
  coordinates). Correct: new member at index 70; prior HEAD
  rows 0-69 stand; prior HEAD rows 70-76
  (`_pipeline_sync`..`DjangoConnectionField`) shift to 71-77.
  (The "prior 72-76 shift to 73-77" member list itself names
  the right five members.)
- D-W2-2 (hunk-group arithmetic): shared hunks are counted in
  multiple bullets (the import hunk in truth + cursor-guard;
  the new-guards hunk in truth + cursor-guard + last:0) while
  "Fallback laziness (3)" describes 5 hunks (signature,
  docstring+call, reorder, call-site lambda, deferred
  `source =`) and "Docstring/comment-only (11)" names 11 of 12
  (hunk `-352,10 +360,9`, the `_resolve_from_window`
  offset-cursor docstring paragraph, unnamed). Net 32 is
  correct; per-bullet numbers are not distinct-hunk counts.
  The `-521` reorder is behavior-preserving (pure-read
  reorder) but is not laziness content.
- D-W2-3 (mention-count scope): F3 "(2 mentions)" holds for
  `policy.reject_sliced` only (bare `reject_sliced` = 8);
  J1 "4 mentions" holds for imports+calls only (file total
  3+3 = 6 with docstrings).
- D-W2-4 (nits): F6 "passed to the four `apply_*` entries" -
  `model=definition.model` appears at 4 sites but only 2 are
  apply calls (2 are visibility calls); index-row "(2 surfaces
  x 2 kinds over 1 core)" - the list surface carries only the
  order kind (no `filter:` sidecar), so 3 combos, not 4.

### Gate state

- `git diff 6d9a0d75.. -- connection.py`: 0 bytes. Ruff N/A
  (artifact `.md` only; source-layout gate reports the file
  excluded, 0 violations). All 17 cited HEAD blobs
  re-verified identical. HEAD `0c0537e2` unmoved at close.
- Verdict: `verified`, zero-edit. Index rows for Worker-0
  (6 CONFIRMed unchanged, F5 -> consumer with family
  re-census, no new rows, zero owned changes) endorsed as
  written.

## Run-8 scoped re-trace (Worker 1, REOPENED item s1)

Run: 0.0.15 2026-09-30-8. Prior sections above are prior evidence only,
preserved intact. This section re-traces HEAD bytes fresh, CONFIRMs or
REVISEs every prior finding, and assigns the drift's new shape. Zero
production edits; zero tracked files changed except this artifact.

### Scope and fingerprints

Drift base `0c0537e2`, HEAD `83998e08` (unmoved at close). For THIS target:

- `0c0537e2:connection.py` blob `4894f90f` (2317 lines, 78 members, 41
  def/class) -> `HEAD:connection.py` blob `3d6dd424` (2376 lines, 84
  members, 42 def/class). Committed delta `0c0537e2..HEAD` is 10 commits:
  4 behavior-bearing + 6 typing-only.
- Behavior-bearing (each read end to end on this target):
  `193f9946` (offset pages bounded by the effective cap via
  `utils/connections.py::offset_page_first`, then superseded; cursor
  truthiness in the window derivation), `dbf0a870` (last:0 served as the
  first:0 page via `utils/connections.py::page_arguments`; nested/keyset
  quirk arms removed), `5c5e32c5` (combined `get_queryset` served as its
  pk set via `utils/querysets.py::_seal_or_defect`; `_sidecar_visibility_policy`
  + `_LIST_ARGUMENT_VISIBILITY_POLICY` + `reject_combined` removed),
  `10d2b9cd` (default-order read consolidated into
  `utils/querysets.py::default_order` / `::applied_order`;
  `optimizer/plans.py::effective_connection_order` takes the query).
- Typing-only (annotations, casts, `TYPE_CHECKING`, `@override`, comment
  reword; moves no rule ownership): `999a1aab`, `b20277fe`, `dd3a10b1`,
  `849f67bc`, `dfbea72b`, `fef11e64`. The last splits
  `connection.py::_build_connection_resolver`'s two `_resolve` closures
  into named `connection.py::_async_connection_resolver` /
  `connection.py::_sync_connection_resolver` (inner `__name__` stays
  `_resolve`; bodies byte-identical modulo annotations).
- Worktree blob `64b85d0e` (2380 lines, 90 members, 44 def/class) vs HEAD
  `3d6dd424`: 31 hunks, 130+/126-, all concurrent-external (no
  `## Owned changes` ledger row names this file; zero edits authored
  here). Every hunk attributed by content below; the trace reads HEAD
  bytes (`git show HEAD:` + AST over that text), never the dirty tree.
- Pre-merge bytes `9aaaad5d:connection.py` blob `1fca6266` (2348 lines,
  85 members, 44 def/class): read-only evidence of the pre-merge tree,
  never applied. It carries the superseded `_cap_offset_last_zero_page`
  + `last_zero_quirk` shape plus the cursor-guard/truth/laziness dirt
  that the drift's `dbf0a870` superseded on the last:0 axis.

Worktree dirt attribution (all 31 hunks, grouped by content; X1's
successor - see X1-REVISED):

- Truth-module migration (8 hunks): `from .utils import truth` import;
  `truth.class_dict` in `_keyset_connection_context`;
  `truth.IdentityMap` for `_connection_type_cache` (+ new
  `_window_edge_class_cache` / `clear_window_edge_class_cache` /
  registry wiring); `truth.name` / `truth.kind` / `truth.is_instance` /
  `truth.own_attr` replacing `_safe_class_name` / `_safe_type_name` /
  `hasattr.__getitem__` (import line drops the two `_safe_*` names).
- Cursor-guard successor (2 hunks): `from_base64` import widen; new
  `_reject_negative_offset_cursor(prefix, argument, value)` (3-arg) +
  `_consume_fallback` non-queryset guard lines calling it with
  `_window_edge_class(cls).CURSOR_PREFIX`. No `_offset_cursor_prefix`
  helper (restructured by its owner long ago).
- Fallback laziness (2 hunks): `_build_windowed_fallback`
  `source` -> `source_factory` + docstring; relation-resolver `source =`
  moved below the window branch with a lambda factory at the call site.
- `_window_edge_class` memoization (1 hunk): cache read/populate around
  the existing derivation.
- Hostile-shape guard narrowing (4 hunks): try/except deleted around
  `_keyset_order_ref` parse, `_guard_source_not_pre_sliced`
  `is_sliced` read, all `_finalize_queryset` reads/applies,
  `_window_rows_are_annotated` - bare reads now.
- `FieldDoesNotExist` hoist (1 hunk): function-local import moved to
  module top (behavior-neutral import move).
- `_resolve_from_window` condition reorder (1 hunk): pure-read reorder
  (`not probe and not constant_false and _has_next_page_requested`),
  behavior-preserving, not laziness content.
- Docstring/comment-only (12 hunks): `_resolve_from_window` keyset
  backend prose, `_consume_window` entry prose, `_KeysetPage` +
  `_resolve_keyset_connection` + `resolve_connection` + relation-resolver
  + `DjangoConnectionField` prose, plus the `last:0` quirk-trim prose
  deletions that mirror the committed `dbf0a870` shape.

The prior run's `_cap_offset_last_zero_page` (2 hunks in the 9a bytes)
is absent in both HEAD and worktree - dropped as superseded by
`dbf0a870` (see R4-REVISED). Net 31 is correct; per-bullet numbers are
distinct-hunk counts this run.

### Enumeration at HEAD bytes

Instrument: `ast.parse` over `git show HEAD:` text, counting
`ast.Module.body` - **84 top-level statements** (base 78 + 6: one
`if TYPE_CHECKING` block, two new `TypeVar` assigns
(`_ConnectionT`, `_ModelT`), two new resolver factories
(`_async_connection_resolver`, `_sync_connection_resolver`), minus one
removed `_sidecar_visibility_policy`, plus import-block growth counted
inside the same 84). **42 top-level def/class** (base 41 - 1 removed + 2
added). Probe `RUN8-PROBE ALL OK` (136 checks) asserts the exact def
list below.

Non-def members 0-39: 0 module docstring (projection); 1-33 imports
(machinery + consumers; 31 now imports `applied_order` alongside the
four `apply_*` entries and drops the three seal-policy names; 28 now
imports `page_arguments` instead of the transient `offset_page_first`);
34 `if TYPE_CHECKING` (7 typing-only subs: 6 imports + `_SelectionPredicate`
protocol); 35 `_ends_in_unique_column` alias (R-ALIAS); 36-38 `NodeType`,
`_ConnectionT`, `_ModelT` TypeVars (machinery, R3/R6); 39
`_TOTAL_COUNT_ATTR` (R2).

Def/class members 40-83 with homes (F1-F7 reuse the plan's existing
family names; R1-R7 + R-ALIAS file-local; J1-J3 rejections; X1 external):

- 40 `def _keyset_connection_context` -> R5; 41 `def _set_total_count`
  -> R2; 42 `def _empty_page_connection` -> R4; 43
  `class _WindowedConnectionRows` -> R4; 44
  `def _build_windowed_fallback` -> R4; 45 `def _window_edge_class` ->
  R4; 46 `def _resolve_from_window` -> R4; 47 `def _consume_window` ->
  R4; 48 `def _consume_fallback` -> R4 (hosts the `page_arguments`
  rewrite call); 49 `def _keyset_order_ref` -> R5 (+ J1); 50
  `def _resolve_order_path_field` -> F7; 51 `def _keyset_order_state` ->
  R5; 52 `class _KeysetPage` (+ 2 properties, no `last_zero_quirk`) ->
  R5; 53 `def _resolve_keyset_connection` -> R5 (+ F4); 54
  `def _guard_first_and_last` -> R1; 55
  `def _connection_field_requested` -> R7; 56
  `def _total_count_requested` -> R7 (serves R2); 57
  `def _has_next_page_requested` -> R7 (serves R4); 58
  `class DjangoConnection` (+ `resolve_connection`) -> R6 (+ R1, R2);
  59 `class _CachedConnectionType` -> R3; 60 `_connection_type_cache`
  AnnAssign -> R3; 61 `def clear_connection_type_cache` -> R3; 62
  `register_subsystem_clear` Expr -> R3; 63
  `def _generate_connection_class` -> R3; 64
  `def _build_total_count_connection` -> R3 (+ R2 field); 65
  `def _guard_total_count_countable` -> R2; 66
  `def _attach_count_sync` -> R2; 67 `async def _attach_count_async` ->
  R2; 68 `def _connection_type_for` -> R3; 69
  `def _guard_sidecar_input_against_non_queryset` -> R6; 70
  `def _guard_non_queryset_iterable` -> R6 (+ F4); 71
  `def _guard_source_not_pre_sliced` -> F3; 72 `def _finalize_queryset`
  -> R6 (consumes `applied_order` + `effective_connection_order`); 73
  `def _prepare_pipeline_source` -> R6 (F1, F6 consumers); 74
  `def _sidecar_steps` -> R6; 75 `def _pipeline_sync` -> R6 (F1, F2,
  F6; no `policy=` arg); 76 `async def _pipeline_async` -> R6 (same);
  77 `def _synthesized_signature` -> R6 (+ J3); 78
  `def _async_connection_resolver` -> R6 (typing-split, see above); 79
  `def _sync_connection_resolver` -> R6 (same); 80
  `def _build_connection_resolver` -> R6 (delegates to 78/79); 81
  `def _window_rows_are_annotated` -> R4; 82
  `def _build_relation_connection_resolver` -> R6; 83
  `def DjangoConnectionField` -> R6.

No new family named; the two new resolver factories are file-local
under R6 (same owner, same rule); the removed `_sidecar_visibility_policy`
deletes R6's conditional-selection sub-row (see R6-REVISED).

Fresh HEAD-blob fingerprints (every evidence file except
`utils/connections.py` is worktree-dirty concurrent work, so every claim
cites the `HEAD:` blob): connection.py `3d6dd424`,
utils/querysets.py `392e50d0`, list_field.py `77ddb86c`,
utils/relations.py `72e7ff08`, keyset.py `8da76569`,
optimizer/plans.py `fdc4b1b0`, registry.py `9d2021eb`,
utils/connections.py `735aa454` (clean), optimizer/nested_planner.py
`3637dc3a`, types/finalizer.py `cb2dde6b`, types/resolvers.py
`574e9768`, utils/directives.py `0368ff51`, optimizer/selections.py
`4127d08a`, resource_policy.py `47befb3f`, optimizer/nested_fetch.py
`304e2f3e`, utils/policies.py `4b180e2b`, tests/test_connection.py
`615866f6`, test_library_api.py `91f0238b`, test_keyset_api.py
`315c0372`. Worktree connection `64b85d0e`; 9a bytes `1fca6266`; base
`4894f90f`. Any change reopens.

### Matrix (re-discharged at HEAD bytes)

**1. Cross-flavor policy mirroring.** The `first` + `last`
full literal lives exactly once in production
(`connection.py::_guard_first_and_last`; probe `R1-literal-once`; bare
`mutually exclusive` twice, the second the `FetchMode` comment). No
list / mutation / form / rest_framework surface defines a first+last
guard, a `totalCount` writer (single-sited
`connection.py::_set_total_count`, 8 call sites all in this file), a
windowed-row consumer (only `connection.py` consumes
`utils/connections.py::split_window_rows`), or a keyset slicer (only
`connection.py::_resolve_keyset_connection`; the one
`utils/connections.py` mention is a docstring citation). Shared seams
composed by name: `list_field.py::_validate_relay_djangotype_target`,
`utils/querysets.py::prepared_resolver_source`,
`::apply_type_visibility_sync` / `_async`, `::base_queryset`,
`::apply_orderset_*` / `::apply_filterset_*`, `::applied_order`,
`utils/connections.py::page_arguments`. The pre-slice second definition
(F3) and the async-vocabulary refusal (F4) stand; the post-sidecar seal
(F5) stays converged through the shared owner.

**2. Sync/async twins.** Four colored pairs, all compared by behavior at
HEAD: `connection.py::_pipeline_sync` / `::_pipeline_async` (share
`::_prepare_pipeline_source`, `::_sidecar_steps`, `::_finalize_queryset`
verbatim; differ only in the awaited visibility/filter/order steps and
the async guard; both now omit `policy=` so both use the one default
seal - the recorded principle-5 shape); `::_attach_count_sync` /
`::_attach_count_async` (async awaits the queued connection BEFORE the
guard - await-before-raise - so a guard-raise never strands an
awaitable); `::_resolve_keyset_connection`'s `_resolve_async` closure
vs its sync tail (same `_build` / `_page` pure decisions, one await
point; `last_zero_quirk` gone from both); `::_build_connection_resolver`'s
branches, now named `::_async_connection_resolver` /
`::_sync_connection_resolver` (bodies identical to the prior inline
closures modulo annotations; per-construction commitment rationale
preserved; `__name__` stays `_resolve`). No behavioral divergence
between the halves of any pair (static review of all bodies).

**3. Derived rather than repeated knowledge.** Four facts derived once
from their owner: the generated connection name from
`definition.graphql_type_name` (never `__name__`); the effective order
from `optimizer/plans.py::effective_connection_order` (now taking the
query; the same implementation the planner uses - cursor parity); the
applied order from `utils/querysets.py::applied_order` (explicit else
`default_order`; the separate `tuple(target_model._meta.ordering)` read
is gone); the `totalCount` GraphQL names via
`optimizer/selections.py` primitives (never camelCase literals). The
`_TOTAL_COUNT_ATTR` writer is single-sited; the `_dst_keyset_state`
vocabulary is fixed once at class generation. The cursor-prefix read
(`_window_edge_class(cls).CURSOR_PREFIX`) lives only in the worktree
cursor-guard hunk, absent at HEAD - no HEAD claim. No reconstructed
copy.

**4. Inverse / round-trip pairs.** Three grammars, each with one owner,
both halves composed here by name: offset cursors (Strawberry's edge
class owns prefix + base64; this file passes only the integer offset
through `edge_class.resolve_edge`); keyset cursors (`keyset.py` owns
`encode_keyset_cursor` / `decode_keyset_cursor` /
`order_fingerprint`; this file calls all three, defines none -
probe `R5-codec-composed`); window bounds + page arguments
(`utils/connections.py` owns `page_arguments` /
`derive_connection_window_bounds` / `derive_keyset_window_bounds` /
`window_range_plan` / `split_window_rows`; `::_consume_fallback`
rewrites `first`/`last` through `page_arguments` so the resolve-time
page matches the plan-time window by construction; the transient
`offset_page_first` is gone from both files). No second grammar lives
here.

**5. Contracts restated in another medium.** Four media: production
(target); oracles spelling literals directly -
`tests/test_connection.py` (guard pins, pre-slice hostile rows, seal
rows including the new combined-sidecar row, keyset/window/count pins)
plus the live tier (`test_library_api.py::test_genre_connection_first_and_last_rejected`,
the `last_zero_serves_the_first_zero` root/nested rows,
`test_keyset_api.py` round-trip / tamper / seek / last:0 rows,
`test_combined_visibility_api.py` pk-set rows,
`test_library_shapes_api.py` default-order rows); projections (module /
class / function docstrings, spec pointers). Every oracle checked
spells its expectation independently and would fail, not follow, a
production change. The `_ends_in_unique_column` re-export is an
assignment alias, not a copy (probe `R-ALIAS-assign`).

**6. Enforcement by omission.** Three member-by-member checks. (a)
Post-sidecar seal: both pipelines route both sidecars through the one
owner seal (`apply_*` entries over `_apply_sidecar_*` core); the D3
omission stays closed (F5). (b) Async-shape vocabulary: this file's
three async-shape branches still ask "may the async executor stream
this?" / admit a union - the opposite of
`utils/querysets.py::is_async_only_iterable`; substitution would still
misroute every queryset (F4). (c) Slice/ordering guards:
`::_guard_source_not_pre_sliced` fires on every queryset path including
the keyset slicer entry; `::_finalize_queryset` converts unreadable /
unresolvable / unappliable ordering failures to `GraphQLError`; at HEAD
there is no non-queryset negative-cursor guard (that hunk is
worktree-only X1, traced not judged). No member lacks a guard its
contract requires.

### CONFIRM verdicts (15, each re-proved at current bytes)

- F1 (consumer): three color guards threaded by name (each >= 2
  mentions), disposal absent. C1/C2 re-run: 1 each at the querysets
  owner. CONFIRM.
- F2 (consumer, count 1): zero `models.QuerySet(` / `sql.Query`
  constructions, zero `_seal_or_defect` / `_defect_message` /
  `_LIST_ARGUMENT_VISIBILITY_POLICY` references, zero `policy=` args
  (prior run-7 "policy x2" line superseded - both pipelines now omit
  the arg so every request seals under the one
  `utils/querysets.py::_DEFAULT_SEAL_POLICY`; the combined result the
  seal used to refuse is rebuilt as its pk set by the owner). C3
  re-run: 1 at the seal. CONFIRM (verdict unchanged, evidence revised).
- F3 (family-open, count 2): `::_guard_source_not_pre_sliced` intact
  including the fail-soft hostile-`is_sliced` arm; the seal's
  `reject_sliced` arm intact in HEAD querysets. C4/C5 re-run: 2 and 2
  (wire `GraphQLError` vs seal `ConfigurationError`, head timing vs
  seal timing). CONFIRM.
- F4 (rejection stands): both keyset
  `isinstance(nodes, (AsyncIterator, AsyncIterable))` branches intact
  (count 2); the `(Iterable, AsyncIterable)`-or-`__getitem__` union
  guard intact; `is_async_only_iterable` / `_AsyncQuerySetRows`
  still absent. Substitution would still misroute every queryset. C6
  re-run: refused. CONFIRM.
- F5 (consumer, D3 closed): pipelines still consume the four thin
  `apply_*` entries over the one `_apply_sidecar_*` core (freeze
  before override, validate under `_SIDECAR_RESULT_POLICY`, both
  kinds); 0 direct `set_class.apply_*` calls; kind dispatch intact
  both colors. C7 re-run: 1 (owner core). Gate: committed HEAD oracles
  `test_connection_seals_a_malformed_apply_sync_result`,
  `test_connection_seals_a_malformed_filter_apply_sync_result`,
  `test_connection_serves_a_combined_sidecar_result_as_its_primary_key_set`
  (+ healthy twins) spell expectations independently. CONFIRM (of the
  run-7 REVISE).
- F6 (consumer, 1 and 1): `base_queryset(definition.model)` default
  seed intact; `model_for` still absent; `definition.model` captured
  reads (>= 3) intact, extended to the `apply_*` + visibility calls
  without adding a re-read. C8/C9 re-run: 1 and 1. CONFIRM.
- F7 (family-open, 2+): member intact (pk-alias, per-segment
  `get_field`, `forward_single` + non-null intermediate rule,
  concrete-non-relation terminal rule); `utils/relations.py::classify_path`
  still defined once; `relation_kind` still the only relations import.
  C10 re-run: 2+. CONFIRM.
- R1/R2/R3/R7/R-ALIAS (file-local or consumer as recorded):
  exclusivity guard + full-literal-once intact (bare phrase twice,
  second the FetchMode comment); count writer + guard + attach twins
  intact; all six class-gen members + provenance identity check
  intact; one-walk observers intact; alias still one `Assign`.
  C11/C12/C13/C14/C15/C16/C22/C23 re-run with identical counts.
  CONFIRM (5 rows).
- J1 (rejection stands): zero `_is_deterministic_order*` /
  `_has_deterministic_ordering` references; `::_keyset_order_ref`
  still per-entry anchorability composing `order_entry_name_and_direction`
  + `order_entry_has_explicit_nulls`. Trigger (keyset certifies whole
  orderings, or list mints value cursors) not fired. CONFIRM.
- J2 (rejection stands): factory still validates through imported
  `::_validate_relay_djangotype_target`; all definition reads still
  captured-reads; no list validator imported. Trigger (substitution
  bug traced to a connection read) not observed. CONFIRM.
- J3 (rejection stands): `::_synthesized_signature` intact; no third
  flavor synthesizes `ConnectionExtension`-shaped signatures; list
  synthesizer not imported. Trigger not fired. CONFIRM.

### REVISE verdicts (4)

- R4 REVISED: file-local, last:0 rule re-derived. What moved
  (`193f9946` then `dbf0a870`): `::_consume_fallback` rewrites
  `first`/`last` through `utils/connections.py::page_arguments`
  (import + call + 2 docstring refs = 4 mentions; the transient
  `offset_page_first` is gone from both files), so every page is
  bounded by the already-clamped `max_results` AND `last: 0` is the
  `first: 0` page on every connection (root/nested, offset/keyset).
  Removed as unreachable: the `_resolve_from_window` reversed
  zero-limit branch (`reverse and limit == 0`, 0 matches), the
  `last: 0` fallback prose (now solely the conditional-count drift
  guard), the nested planner's `last: 0` fallback arm (owner side).
  The worktree `_cap_offset_last_zero_page` (present in 9a bytes,
  absent in HEAD and worktree) is dropped as superseded - the rewrite
  subsumes it. C17 re-run (empty-page flags): 1 here
  (`::_empty_page_connection`); C18 re-run (marker classification):
  1 at `utils/connections.py::split_window_rows`, followed as
  consumer. The eight window members stand; only the quirk content
  is gone.
- R5 REVISED: file-local, keyset rule re-derived. What moved
  (`dbf0a870`): `_KeysetPage.last_zero_quirk` deleted (0 matches);
  `has_previous_page` simplified to `(backward and overfetched) or
  after_supplied`; `backward = is_backward_shape(first, last)` (no
  quirk carve-out); `page_size = last if backward else first` (the
  `else cap` arms gone; the `cast("int")` is typing-only - the
  `page_arguments` call upstream guarantees an int); the
  `last_zero_quirk` construction + threading deleted. Columns,
  fingerprint, seek, overfetch, and both page flags still derived
  here; the codec (`keyset.py`), order-entry parsing
  (`optimizer/plans.py`), and path resolution (F7) still composed by
  name (3 codec imports, 0 codec defs). The pre-seek queryset stays
  the `totalCount` source; `ListConnection` still never reached for
  keyset. C19/C20 re-run: 1 and 1. Gate: live
  `test_root_keyset_last_zero_serves_the_first_zero_page` (+
  `with_after`, nested twins) assert the `first: 0` page.
- R6 REVISED: file-local, extended then shrunk. What moved:
  (a) Seal composition (`5c5e32c5`): `_sidecar_visibility_policy`
  deleted (0 matches; was R6's conditional selection); both pipelines
  drop `policy=` (0 `policy=` args in the file) so the visibility seal
  runs under the one default policy on every request; the docstrings
  record the new contract (a combinator `get_queryset` is served as
  its pk set, which a sidecar can narrow and re-sort). The
  `_LIST_ARGUMENT_VISIBILITY_POLICY` symbol is gone package-wide (0
  matches at HEAD); `reject_combined` axis gone with it; the owner
  `utils/querysets.py::_seal_or_defect` + `_DEFAULT_SEAL_POLICY` /
  `_SIDECAR_RESULT_POLICY` carry the whole rule (1 definition).
  (b) Order tail (`10d2b9cd`): `::_finalize_queryset` reads
  `applied = applied_order(qs.query, target_model)` (the new
  `utils/querysets.py` owner: explicit else `default_order`, honoring
  `query.default_ordering` and `Meta.ordering = None` by truthiness),
  calls `effective_connection_order(cursor_field, qs.query,
  target_model)` (new query-taking signature), and compares `ordered
  != applied` (the separate `tuple(target_model._meta.ordering)` read
  + its `GraphQLError` arm are gone). The cursor-parity invariant
  holds through the shared owner (plan-time
  `nested_planner.py::plan_connection_relation` + resolve-time tail
  call the same function). (c) Resolver split (`fef11e64`,
  typing-only): `::_async_connection_resolver` / `::_sync_connection_resolver`
  extracted with identical bodies (`__name__` unchanged); `::_build_connection_resolver`
  delegates. C21 re-run (third sidecar kind): signature + steps +
  dispatch move together here (**1 owner**); the seal needs only a
  thin fifth `apply_*` entry at the owner (4-over-1 shape intact).
  Sync/async twins re-compared: no divergence. Matrix axes 1-6
  re-discharged (axis 1: no conditional policy to mirror; axis 5
  gains the combined + last:0 + default-order oracles; axis 6: D3
  stays closed).
- X1 REVISED: prior X1 successor (32-hunk patch with
  `_cap_offset_last_zero_page`) is SUPERSEDED in shape, still
  external. At HEAD the cursor guard (`_reject_negative_offset_cursor`,
  0 matches), the edge-class cache (`_window_edge_class_cache`, 0),
  the truth migration, the fallback laziness, and the guard
  narrowing are all absent; in the worktree they form the current
  31-hunk patch (attributed above) WITHOUT the cap (0 matches in
  both HEAD and worktree; present only in the 9a pre-merge bytes).
  The cap's removal is the committed `dbf0a870` rewrite subsuming it,
  not a revert. Still traced, not judged; still touches none of the
  drift's seal/order/paging sites (zero added/removed lines mentioning
  `page_arguments`, `applied_order`, `_seal_or_defect`,
  `_SIDECAR_RESULT_POLICY`, `_apply_sidecar_`, or
  `_guard_source_not_pre_sliced`). No verdict, no challenge - its
  owning change carries them.

### Canonical-copy split citation

The verified File `utils/policies.py` outcome (Status: `verified`,
Run `0.0.15 2026-09-22-5`; families `schema-construction-policy-ladder`,
`policy-authority-isolation`, `hostile-mapping-hardening`) does not
touch this target: HEAD `connection.py` contains zero references to
`canonical_policy`, `_PACKAGE_*`, `DEFAULT_ERROR_POLICY`, or
`DEFAULT_RESOURCE_POLICY` (probe `no-canonical`). The only POLICY
symbols here are the querysets seal policies (`_DEFAULT_SEAL_POLICY`,
`_SIDECAR_RESULT_POLICY`) - a different family
(`sealed-execution-queryset`, F2). No finding moves.

### Challenges (re-run at HEAD bytes)

C1/C2 (F1): third awaitable kind / new async shape -> **1** each at
the querysets owner; zero here. C3 (F2): new untrusted shape -> **1**
at the seal; zero here (0 `policy=` args). C4/C5 (F3): pre-slice rename
/ error-class unify -> **2** and **2** (seal arm + wire guard). C6
(F4): async-shape substitution -> **refused** (misroutes every
queryset). C7 (F5): sliced sidecar return through a connection ->
**1** (owner core; D3 closed). C8/C9 (F6): seed pin / hostile model
read -> **1** and **1** outside here. C10 (F7): new segment kind ->
**2+** (member + owner). C11/C12 (R1): message reword / zero-scope ->
**1** each here. C13/C14 (R2): count-source unify / new countable
shape -> **1 owner** / **1** here. C15/C16 (R3): class naming /
provenance -> **1** each here. C17 (R4 flags): **1** here; C18 (R4
classification): **1** at the window owner. C19/C20 (R5): anchor /
flags -> **1** each here. C21 (R6 sidecar): **1 owner** here (+ thin
owner entry). C22 (R7 vocabulary): **0** here. C23 (R-ALIAS): **1** at
the planner. C24 (J1-J3): **0 moves - refused**. Counts match the
CONFIRM/REVISE verdicts above.

### Defects

None. No new defect; the D3 ambiguity stays closed by the landing (F5
CONFIRM), not re-homed. The `R5-codec-composed` probe refinement (this
file CALLS the codec trio, defines none - the prior "never encodes,
decodes" line meant "never defines") is a record correction, not a
defect. Worktree dirt is concurrent-external, never judged.

### Pending execution

None. The execution proof is the read-only probe
`/tmp/dry_conn_run8_probe.py` (`RUN8-PROBE ALL OK`, 136 checks:
84-member HEAD AST with the exact 42-def list, base 78/41 split,
insertion/removal points, F/R/J drift-shape markers, all CONFIRM
identity/count/absence claims, J1-J3 triggers, canonical-copy absence,
paging/seal/order owner checks, X1 three-state attribution, full
fingerprint table, item-diff-empty) - mutates no source, opens no
database, runs no pytest, so no workspace copy was owed and no
`__file__`/DB record applies. Oracle bodies remain `static-reviewed`.
No shared-tree pytest run (zero-edit file item). No sharded/PG cell
owed (`inapplicable by construction` - the probe touches no database,
alias, or dialect decision).

### Judgment

Backstop re-discharged at HEAD bytes (`3d6dd424`, 84 members): 15
CONFIRM rows re-proved with fresh evidence (F2 with revised
no-policy-arg evidence), 4 REVISE rows (R4 last:0-via-`page_arguments`,
R5 quirk-free keyset, R6 seal/order/resolver re-derivation, X1
31-hunk successor without the cap), 0 new families named, 0 defects.
Zero-edit result stands.

### Item-scoped diff state

`git diff b147f860bba8f71707ffd3ae1911f00f66d2d962 --
django_strawberry_framework/connection.py` is 0 bytes (own diff
empty - all dirt predates the item baseline: baseline blob equals
worktree blob `64b85d0e`); attribution is by content vs HEAD
(`git show HEAD:` + full `git diff HEAD` read, all 31 hunks grouped
above): no ledger row names this file and zero hunks were authored
here, so every hunk is concurrent-external and the dirt is not a stop
for this zero-edit file item. No tracked file touched except this
artifact; no ruff run owed (artifact is `.md` only and the
source-layout gate reports it excluded; probe is `/tmp`-only
scratch). HEAD `83998e08` unmoved at close.

## Index rows for Worker-0 (run-8)

CONFIRMed rows (unchanged text - families keep name, owner, files,
status; connection-side role re-proved at HEAD `3d6dd424`):

- `awaitable-refusal-and-disposal` (F1 consumer) - no change.
- `sealed-execution-queryset` (F2 consumer) - no change (evidence:
  0 `policy=` args, default seal always; `_LIST_ARGUMENT_VISIBILITY_POLICY`
  gone package-wide).
- `recomposition-illegal-source-rejection` (F3 family-open, count 2)
  - no change.
- `async-only-queryset-row-adapter` (F4 rejection) - no change.
- `post-set-apply-result-validation` (F5 consumer, D3 closed) - no
  change (run-7 REVISE stands; re-census still owed: 3 combos per
  D-W2-4).
- `queryset-seed-and-model-read` (F6 consumer) - no change.
- `orm-lookup-path-resolution` (F7 family-open, count 2+) - no
  change.

REVISEd rows (verdict moved or evidence re-derived; owners unchanged):

- R4/R5/R6 are file-local under this item (no index rows); their
  REVISEs change no family row. The `page_arguments` rewrite composes
  the already-indexed `window-range-fetch-derivation` owner family
  (no new row); the `default_order` / `applied_order` owners compose
  the already-indexed `connection-order-ladder` family (no new row);
  the seal composition composes the already-indexed
  `sealed-execution-queryset` family (no new row).
- X1 stays external (no index row); its owning change carries its
  family-or-local assignment.

New rows: none. No `## Families` item owed; zero `## Owned changes`
rows.

## Run-8 verification (Worker 2)

Run: 0.0.15 2026-09-30-8. Expectation-first: the byte-level trace below
(counts, blobs, hunks, commit footprints, insertion points) was derived
from `git show` + AST + grep before the run-8 author section was opened;
that section was then read to judge each CONFIRM/REVISE against its row.
The author's probe was re-run green under my invocation
(`RUN8-PROBE ALL OK`, 136/136) and every decisive claim re-proved by my
own `/tmp/w2_conn_run8_verify.py` (60 checks, ALL OK) plus body reads and
a typing-erased AST comparison. Zero production edits; this section + the
`Status:` line are the only tracked changes.

### Expectation-first trace

- HEAD `83998e08` unmoved; target HEAD blob `3d6dd424` (2376 lines),
  worktree `64b85d0e` (2380 lines), 31 hunks, 130+/126-. Base
  `0c0537e2` blob `4894f90f` (2317 lines); pre-merge `9aaaad5d` blob
  `1fca6266` (2348 lines, read-only via `git show`, never applied).
- `ast.Module.body` over HEAD bytes: 84 members; base 78; delta +7/-1
  (new `if TYPE_CHECKING`, `from types`, `from typing_extensions`,
  `_ConnectionT`, `_ModelT`, `_async_connection_resolver`,
  `_sync_connection_resolver`; removed `_sidecar_visibility_policy`).
  42 def/class at HEAD (41 - 1 + 2). Indices 40-83 match the author's
  def list name-for-name (44/44, mechanically compared); 0 docstring,
  1-33 imports, 34 `TYPE_CHECKING`, 35 alias, 36-38 TypeVars, 39 count
  slot.
- `0c0537e2..HEAD` touches this target in exactly 10 commits: 4
  behavior-bearing (`193f9946`, `dbf0a870`, `5c5e32c5`, `10d2b9cd`,
  each read end to end on this target) + 6 typing-only (`999a1aab`,
  `b20277fe`, `dd3a10b1`, `849f67bc`, `dfbea72b`, `fef11e64`). My
  typing-erased AST comparison (annotations, docstrings,
  `TYPE_CHECKING` blocks, `cast`, `@override` stripped) shows zero
  statement change for `999a1aab`/`849f67bc`/`dfbea72b`; two TypeVar
  declarations for `b20277fe`; `list[X]`/`Iterable[X]` rendered as
  `GenericAlias` for `dd3a10b1`; and the resolver-closure split for
  `fef11e64` whose inner `_resolve` bodies are AST-identical to the
  removed inline closures (963/963 and 1530/1530 chars, same inner
  name, same captured values passed as parameters). No typing commit
  moves any rule.
- Behavior footprint on this target: `193f9946` (fallback cap via the
  transient helper + import); `dbf0a870` (import swap to
  `page_arguments`, fallback rewrite, reversed zero-limit branch
  deleted, `last_zero_quirk` deleted from `_KeysetPage` + slicer,
  prose); `5c5e32c5` (seal-policy imports + `_sidecar_visibility_policy`
  deleted, both `policy=` args deleted, pipeline prose); `10d2b9cd`
  (`applied_order` import, `_finalize_queryset` tail rewrite). None of
  the four touches the guards, classifiers, seeds, observers, alias,
  validators, or synthesizers behind the CONFIRM rows.
- Dropped symbols: `_cap_offset_last_zero_page`,
  `_sidecar_visibility_policy`, `_LIST_ARGUMENT_VISIBILITY_POLICY`,
  `reject_combined`, `offset_page_first`, `last_zero_quirk`,
  `_offset_cursor_prefix` score 0 files at HEAD across package +
  tests `.py`, while the 9a bytes still carry the first four in this
  target (3/3/4/1 hits) - the absences are real, not grep misses.
  Worktree `.py` likewise carries none of them in this target (the
  only stale hits tree-wide are `__pycache__` bytecode).
- New owners, each confirmed at HEAD with its cited contract:
  `utils/connections.py::page_arguments` (single definition; `last: 0`
  without int `first` becomes `(0, None)`; neither-int becomes
  `(cap, last)`; called from both window-bound derivations and
  `connection.py::_consume_fallback`); `utils/querysets.py::_seal_or_defect`
  (calls `_pk_membership_query_or_defect`, which rebuilds a combinator
  as `filter(pk__in=<combined>.order_by().values("pk"))` keeping outer
  ordering + direction, failing closed with the `combined` defect
  otherwise); `utils/querysets.py::default_order` /
  `::applied_order` (truthiness + `default_ordering` read; explicit
  else default); `optimizer/plans.py::effective_connection_order`
  (`cursor_field, query, model` signature; docstring names the shared
  resolve-time/optimization-side ladder through `applied_order`).
- The `cast("int")` on the keyset `page_size` is provably safe by my
  own derivation: `page_arguments` returns an int `first` on every
  forward shape and an int `last` on every backward shape, so
  `last if backward else first` is always an int at that line.

### Per-judgment results (19 rows, my counts)

1. F1: CONFIRM consumer. Three guards threaded by name (2/3/3
   mentions), disposal absent. C1/C2 re-run: 1 and 1 at the querysets
   owner.
2. F2: CONFIRM consumer, count 1. Zero constructions, zero seal /
   wording / policy references, zero `policy=` args (the run-7
   `policy=` x2 line is superseded as stated). C3 re-run: 1 at the
   seal.
3. F3: CONFIRM family-open, count 2. Wire guard intact with its
   fail-soft `is_sliced` arm; seal `reject_sliced` arm intact (2
   mentions). C4/C5 re-run: 2 and 2 (class + timing differ).
4. F4: CONFIRM rejection stands. Both keyset branches intact (count
   2), union guard intact, shared predicate + adapter absent.
   Substitution still misroutes every queryset. C6 re-run: refused.
5. F5: CONFIRM consumer, D3 closed. Four thin `apply_*` entries over
   the one `_apply_sidecar_*` core, both kinds, both colors; 0 direct
   `set_class.apply_*` calls. C7 re-run: 1 (owner core). The 3-combo
   census holds (list carries order only: 2 order calls, 0 filter
   calls). The three named oracles plus both healthy twins exist at
   HEAD and spell expectations independently; the run-7 refusal row
   they replace is gone.
6. F6: CONFIRM consumer, 1 and 1. Default seed intact,
   `definition.model` captured reads intact (7 mentions), `model_for`
   absent. C8/C9 re-run: 1 and 1.
7. F7: CONFIRM family-open, 2+. Member intact (pk-alias,
   per-segment `get_field`, `forward_single` + non-null rule,
   concrete-non-relation terminal); `classify_path` defined once in
   relations; `relation_kind` the only relations import. C10: 2+.
8. R1: CONFIRM file-local. Guard + full literal once (bare phrase
   twice, second the FetchMode comment). C11/C12: 1 and 1. Live pin
   present.
9. R2: CONFIRM file-local. Writer single-sited, guard + attach twins
   intact with await-before-raise read fresh. C13/C14: 1 owner and 1.
   Count correction in D-W2-R8-4 (record only).
10. R3: CONFIRM file-local. All six class-gen members + provenance
    identity check intact. C15/C16: 1 and 1.
11. R7: CONFIRM consumer-shaped file-local. One walk + two observers
    intact. C22: 0 here.
12. R-ALIAS: CONFIRM consumer. One `Assign`, import pin intact. C23:
    1 at the planner.
13. J1: CONFIRM rejection stands. Zero determinism references here;
    anchorability still per-entry. Trigger unfired.
14. J2: CONFIRM rejection stands. Factory validation + captured
    reads intact; zero validator imports. Trigger unfired.
15. J3: CONFIRM rejection stands. Synthesizer intact; no third
    `ConnectionExtension`-shaped flavor; shared helpers still composed
    by name. Trigger unfired.
16. R4 REVISE: ENDORSED. Fallback rewrites through `page_arguments`
    (4 mentions); transient helper gone from both files; reversed
    zero-limit branch 0 matches; quirk prose gone; cap absent in both
    trees. C17: 1 here; C18: 1 at the window owner. Last:0 oracles
    (root/nested/keyset/`with_after`) assert the `first: 0` page.
17. R5 REVISE: ENDORSED. Quirk flag, carve-out, `else cap` arms, and
    threading all 0 matches; simplified `has_previous_page`,
    `backward`, and `page_size` lines read fresh; codec composed
    (3 imports, 0 defs, calls only). C19/C20: 1 and 1.
18. R6 REVISE: ENDORSED. Policy selection deleted (0 matches), 0
    `policy=` args, default-policy prose read fresh in both pipelines;
    tail reads `applied_order`, calls the query-taking
    `effective_connection_order`, compares `ordered != applied`,
    separate model-ordering read + arm gone; resolver split proved
    identical above. Twins re-compared: shared head/steps/finalizer,
    colored awaits + guard only. C21: 1 owner here.
19. X1 REVISE: ENDORSED with record corrections (D-W2-R8-1..3). Shape
    superseded, still external, still traced-not-judged, no cap in
    either tree, drift derivations intact. The 31-hunk content groups
    all check out; only the per-bullet arithmetic and two evidence
    phrases are off (below).

### Hunk attribution (mine, all 31 read end to end)

Net 31 at 130+/126- confirmed. Baseline blob equals worktree blob and
the item-scoped diff is 0 bytes, so every hunk predates the item; no
`## Owned changes` row names this file and zero hunks were authored
here - all 31 concurrent-external, conclusively. Content: truth
migration, 3-arg cursor guard + fallback call, fallback laziness
(factory + lambda + moved `source =`), edge-class memoization, 4
guard narrowings, `FieldDoesNotExist` hoist, `_resolve_from_window`
condition reorder, prose-only remainder. Drift-derivation check: 0
added/removed lines mention `page_arguments`, `_seal_or_defect`,
`_SIDECAR_RESULT_POLICY`, or `_apply_sidecar_`; the `_finalize_queryset`
narrowing preserves the `applied_order` /
`effective_connection_order` / `order_by(*ordered)` calls
byte-identical modulo indentation (D-W2-R8-1); the page rewrite call
and both pipeline bodies are untouched. My consistent exclusive
attribution (D-W2-R8-2): truth 6, guard 2, laziness 4, memoization 1,
narrowing 4, hoist 1, reorder 1, prose 10, shared 2 (the import hunk
serving three bullets, the relation-resolver hunk serving two) = 31.

### Record defects (W2, run 8)

Imprecise artifact metadata; none moves any verdict, index row, or
downstream decision, so no resubmission is owed - the corrections
stand here, following the run-7 precedent:

- D-W2-R8-1 (X1 `applied_order` parenthetical): "zero added/removed
  lines mentioning `applied_order`" is false. Actual: 1 removed + 1
  added line (the narrowing dedent preserves the call), likewise 1+1
  for `effective_connection_order`. The derivation is unchanged
  (same owner, same arguments, same comparison); only the error
  conversion is removed. Verdict substance (derivations intact)
  survives.
- D-W2-R8-2 (X1 per-bullet hunk counts): the "(8, 2, 2, 1, 4, 1, 1,
  12)" figures are fitted to sum to 31, not distinct-hunk counts:
  the import hunk is shared by three bullets, the relation-resolver
  docstring/code hunk by two; laziness content spans 4 exclusive
  hunks (5 inclusive), not 2; prose spans 10 exclusive (11
  inclusive), not 12; truth reaches 8 only inclusively. Net 31,
  shape, content descriptions, and the external call are all
  correct; use my attribution above.
- D-W2-R8-3 (X1 quirk-trim phrase): "the `last:0` quirk-trim prose
  deletions" names no hunk - no removed line in the diff mentions
  the quirk; both sides already conform to the rewritten shape.
  Drop the phrase; the prose bullet is 10 exclusive hunks.
- D-W2-R8-4 (matrix writer count): "`_set_total_count`, 8 call
  sites" overstates by one. AST count is 7 calls (all in this file)
  + the single def. Single-writer verdict unaffected.

### Gate state

- Item-scoped diff 0 bytes (own run). All 19 cited HEAD blobs
  re-hashed identical. `utils/connections.py` clean at `735aa454`
  as stated. Matrix axes re-discharged against the target's real
  surface (twin bodies read, not sampled); every oracle cited was
  confirmed present at HEAD with independently spelled
  expectations; no oracle reads from its owner. Pending correctly
  none (read-only probes, no database/alias/dialect surface -
  `inapplicable by construction` judged sound). Zero-edit
  accepted: coverage complete (84/84 homed), every candidate in a
  family row, file-local record, rejection, or the external row.
- Target defects: none. The four items above are record
  corrections, not target behavior. D3 stays closed (F5 consumer
  with the 3-combo census); no new family owed; no consolidation
  missed - the drift footprint intersects only the REVISEd rows.
- Index rows for Worker-0 (7 CONFIRMed unchanged with F2's revised
  no-`policy=` evidence + F5's 3-combo note, R4/R5/R6 file-local
  REVISEs composing already-indexed families, X1 external, no new
  rows, zero owned changes): endorsed as written.
- Verdict: `verified`, zero-edit. HEAD `83998e08` unmoved at close.
  No ruff/mypy owed (artifact `.md` only; probes `/tmp`-only).
