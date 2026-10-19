# DRY review: `django_strawberry_framework/list_field.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, re-challenged
fresh on the list-field side) or a file-local record with its proving
challenge, plus four recorded rejections. Zero production edits; zero tracked
files changed.

## System trace

Large target (1442 lines, 63 top-level statements): the package's non-Relay
`list[T]` collection surface. It DEFINES the shared DjangoType-target
validators (`list_field.py::_validate_djangotype_target`,
`list_field.py::_validate_relay_djangotype_target`), the argument-error type
(`list_field.py::ListArgumentError` plus `list_field.py::_KNOWN_LIST_ARGUMENT_REASONS`),
the wire-name readers (`list_field.py::_published_wire_name`,
`list_field.py::_resolve_argument_wire_name` plus
`list_field.py::_DEFAULT_WIRE_NAMES`), the normalized-arguments record and
normalizer (`list_field.py::_ListArguments`,
`list_field.py::_normalize_list_arguments`), the SDL synthesizer
(`list_field.py::_synthesized_list_signature`), the deterministic-order
classification cluster (seven functions plus six constants), the validating
definition readers (`list_field.py::_model_from_definition`,
`list_field.py::_orderset_class_from_definition`), the resolver-context and
non-queryset-rejection helpers, the OrderSet applier twins with
freeze-and-re-seal (`list_field.py::_apply_orderset_sync`,
`list_field.py::_apply_orderset_async`), the offset guard plus normalization
scope, the queryset-pipeline twins, and the field factory
(`list_field.py::DjangoListField` with its four nested resolvers). It
ENFORCES two constructor guards of its own (target registration/canonicality,
resolver callability) and the whole argument/ordering/window contract at
request time. It CONSUMES by name every other rule it touches: the queryset
substrate (`django_strawberry_framework/utils/querysets.py`), the row-bound
and policy seams (`django_strawberry_framework/resource_policy.py`), the
typed-rejection renderers (`django_strawberry_framework/exceptions.py`), the
registry canonical read, the Relay-shape predicate, the directive gate, the
execution-mode color readers, and the `order_input_type` helper.

Connected code read for judgment, outside the item:
`django_strawberry_framework/connection.py` (working tree incl. the external
hunk: import block, `connection.py::_prepare_pipeline_source`,
`connection.py::_sidecar_steps`, `connection.py::_pipeline_sync` /
`connection.py::_pipeline_async`, `connection.py::_finalize_queryset`,
`connection.py::_synthesized_signature`,
`connection.py::_build_connection_resolver`,
`connection.py::DjangoConnectionField` factory tail; traced, never judged or
edited); `django_strawberry_framework/utils/querysets.py` (def lines plus
docstrings of `utils/querysets.py::model_for`,
`utils/querysets.py::base_queryset`,
`utils/querysets.py::_dispose_sync_awaitable`,
`utils/querysets.py::_snapshot_routing_intent`,
`utils/querysets.py::_validate_post_orderset_result`,
`utils/querysets.py::prepared_resolver_source`,
`utils/querysets.py::reject_awaitable_sync_source`,
`utils/querysets.py::reject_residual_async_source`,
`utils/querysets.py::reject_async_iterable_in_sync_context`,
`utils/querysets.py::is_async_only_iterable`,
`utils/querysets.py::wrap_async_queryset_adapter`,
`utils/querysets.py::apply_type_visibility_sync` /
`utils/querysets.py::apply_type_visibility_async`,
`utils/querysets.py::_SealPolicy` plus `_LIST_ARGUMENT_VISIBILITY_POLICY`
and `_ORDERSET_RESULT_POLICY` arms; `_apply_orderset` call-site census in
both flavors); `django_strawberry_framework/relay.py`
(`relay.py::_validate_node_target` wrapper);
`django_strawberry_framework/exceptions.py`
(`exceptions.py::describe_value`, `exceptions.py::_safe_arg_repr`,
`exceptions.py::_safe_class_name`, `exceptions.py::_safe_type_name` def
lines); `django_strawberry_framework/resource_policy.py`
(`resource_policy.py::policy_from_info`,
`resource_policy.py::effective_bound`,
`resource_policy.py::_windowed_rows` /
`resource_policy.py::_windowed_rows_async`,
`resource_policy.py::_cleanup_rejected_async_iterable`,
`resource_policy.py::validate_collection_bound` /
`resource_policy.py::validate_trusted_flag` def lines);
`django_strawberry_framework/registry.py` (canonical-read role);
`django_strawberry_framework/types/base.py`
(`types/base.py::_is_relay_shaped` def line);
`django_strawberry_framework/types/converters.py`
(`types/converters.py::_field_label` body, for the name-collision check);
`django_strawberry_framework/mutations/fields.py`
(`mutations/fields.py::_validate_mutation_target` body, for the same);
`django_strawberry_framework/orders/sets.py` (`OrderSet.apply_sync` /
`OrderSet.apply_async` contract sides);
`django_strawberry_framework/__init__.py` (root export of both public
symbols); `tests/test_list_field.py` (67 test functions, oracle titles plus
the validator / normalizer / signature / hostile-int / unprintable-int /
pickle rows); `examples/fakeshop/test_query/test_list_field_api.py` and
`test_list_field_async_api.py` (live-suite heads, sync/async HTTP coverage);
`docs/spec-050-list_field_arguments-0_0_15.md` (contract source for the
argument table, pipeline order, seal rule, wire-name laziness, offset
precondition; Decisions 1-3 read, remainder used as pointers only).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) - never touched, not in this finding's sites;
`optimizer/walker.py` / `optimizer/extension.py` / `optimizer/nested_planner.py`
bodies beyond the cited def lines (planner-side window construction is the
family items' surface); `auth/mutations.py` + `routers.py` disposal bodies
(F1 owner-side count is plan-indexed; this item verifies the list-side
consumer role only); `utils/relations.py::classify_path` body (no call site
here; the family item owns the full sweep); `docs/GLOSSARY.md` list entries
(projections, not relied upon); in-flight spec bodies behind the module
docstring's Decision pointers (spec-020/028/030/047 cited as pointers,
defaults pinned by oracles instead); concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) - read where needed as oracles, never edited.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** List-field vs connection-flavor
mirroring FIRST, per brief. Both flavors compose the same seams by name:
`utils/querysets.py::prepared_resolver_source` (both resolver heads),
`utils/querysets.py::apply_type_visibility_sync` / `_async` (both
pipelines), `utils/querysets.py::base_queryset` (both default seeds),
`list_field.py::_validate_relay_djangotype_target` (the factory guard,
defined here, imported by connection and relay). The genuine second-site
shapes are: the post-OrderSet seal (F4 - this file seals, connection does
not; re-derived fresh below, not re-homed); the signature synthesizers (J3 -
refused); the validating readers vs captured reads (J2 - refused); the
deterministic predicates vs keyset anchorability (J1 - refused). No list /
mutation / form / rest_framework surface defines its own target validator,
wire-name reader, normalizer, deterministic-order classifier, or offset
guard: `mutations/fields.py::_validate_mutation_target` guards a mutation
protocol (`_mutation_meta` + resolve seams), not a DjangoType registry
identity - different contract, different reasons to change (J4).
`types/converters.py::_field_label` renders `Model.field` diagnostics;
this file's `list_field.py::_field_label` renders the resolver's GraphQL
field name - same token, different contracts (J4). The `first` + `last`
guard, `totalCount` capture, windowed-row consumer, and keyset slicer live
only in connection; the offset/limit/orderBy surface lives only here.

**2. Sync/async twins.** Three colored pairs touch this target, all compared
by behavior: `list_field.py::_apply_orderset_sync` /
`list_field.py::_apply_orderset_async` (both freeze routing intent BEFORE
the override runs, then re-seal through
`utils/querysets.py::_validate_post_orderset_result`; the sync twin refuses
an awaitable return with disposal plus `SyncMisuseError`, the async twin
requires an awaitable, awaits once, and refuses a residual awaitable with
disposal plus `ConfigurationError` - the recorded principle-5 shape: two
colored bodies because the await point and the refusal class differ);
`list_field.py::_execute_queryset_pipeline_sync` /
`list_field.py::_execute_queryset_pipeline_async` (share
`list_field.py::_order_normalization_scope` and
`list_field.py::_check_nonzero_offset_guard` verbatim; differ only in the
awaited visibility step and the async guard passed, plus the sync twin's
`is_async_context` adapter tail); the factory's sync vs async `_wrap`
branches (committed per construction via
`utils/typing.py::is_async_callable` because Strawberry freezes field
sync/async handling at schema-build time; the docstring records why a
per-call coroutine return cannot work and why the sync wrapper under an
event loop returns the adapter/coroutine for the executor to complete).
No behavioral divergence found between the halves of any pair beyond the
documented color duties (static review of all six bodies).

**3. Derived rather than repeated knowledge.** Five facts this file could
have respelled are derived once from their owner instead: the target model
and orderset class come from the ONE construction-time definition the
validator returned (`list_field.py::_model_from_definition`,
`list_field.py::_orderset_class_from_definition` - fail loud, never
re-read at request time, so a stateful metaclass has no second read);
the default seed comes from `utils/querysets.py::base_queryset`
(`base_queryset(target_model)`), never rebuilt from `_meta`; the
returned-row / skip ceilings come from
`resource_policy.py::policy_from_info` plus
`resource_policy.py::effective_bound`, never recomputed from settings;
the order input annotation comes from `orders/__init__.py::order_input_type`
with the captured class (function-local import, preserving the lazy-
subpackage contract); the error wire names come from the executable
schema's published argument map
(`list_field.py::_published_wire_name`), never from re-running the
consumer-owned `NameConverter` at request time. No reconstructed copy
found.

**4. Inverse / round-trip pairs.** Two grammars, each with one owner, both
halves composed here by name: the `ListArgumentError` pickle contract
(`list_field.py::ListArgumentError.__reduce__` returns class plus complete
constructor args plus `__dict__`; `extensions` is rebuilt by `__init__`
from those args - the dual-base precedent, pinned by the pickle oracle);
the async-adapter wrap (`utils/querysets.py::wrap_async_queryset_adapter`
on the queryset branches; the unwrap side lives in the optimizer, never
respelt here). The wire-name map is read-only here (publisher is
Strawberry's schema converter at build time). No second grammar lives
here.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); oracles that spell literals directly
- `tests/test_list_field.py` (67 test functions: constructor guards,
exact-int / bool-subclass / hostile-`__lt__` / unprintable-large-int /
offset-before-limit rows, signature-shape rows, normalization-scope rows,
model-ordering-state rows, no-argument SQL-parity rows, pickle rows) plus
the live tier (`test_list_field_api.py` sync pages / orderBy / visibility-
before-order / cap / converter-naming rows, `test_list_field_async_api.py`
async completion / cleanup rows); projections (the module / class /
function docstrings, spec-050 pointers). Every oracle checked spells its
expectation independently (the reason strings, the wire spellings, the flag
arithmetic) and would fail, not follow, a production change. The
`__all__` pair (`DjangoListField`, `ListArgumentError`) is pinned by
`tests/base/test_init.py` exactly as spec-050 Slice 1 requires.

**6. Enforcement by omission.** Three member-by-member checks.
(a) Post-OrderSet seal: this file's two `OrderSet.apply_*` call sites
freeze routing intent and re-seal through
`utils/querysets.py::_validate_post_orderset_result`; connection's two
call sites (`connection.py::_pipeline_sync` /
`connection.py::_pipeline_async` via `connection.py::_sidecar_steps`) do
neither (probe `asym-conn-no-seal`, `asym-conn-no-snapshot`; one
`apply_sync(` plus one `apply_async(` each, read fresh). The contract
sources scope the rule to the list field while the connection also windows
what comes back - ambiguous, already routed to the maintainer as D3 by the querysets
item; re-confirmed present with fresh counts, no new verdict here (F4).
(b) One-sync-boundary: this file never runs a consumer hook in a worker -
`run_in_one_sync_boundary` count 0, `sync_to_async` count 0 (probe).
The boundary is owned by the visibility runners this file calls; the file
has no such surface, so the family does not cover it (`inapplicable by
construction` - checked, not inherited).
(c) Raw-body source: this file never reads an HTTP body -
`sync-adapter-raw-body-source` (process scope at `_cross_web_patches`, mount
scope at `views.py::_RawBodyRequestAdapter`) has no member here
(`inapplicable by construction`).
No member lacks a guard its contract requires beyond the already-routed
D3.

### Enumeration

Instrument: `ast.parse` over the working-tree blob, counting
`ast.Module.body` members - **63 top-level statements** (28 functions: 25
`def` plus 3 `async def`; 2 classes; first probe draft said 29 functions,
corrected to 28 after the failure named the exact list - substance
unaffected). Every member lands below; every challenge in `### Challenges`
ends in a family row, a file-local record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (surface contract + spec pointers) | (none) | projection |
| 1-13 | imports: future, contextlib, inspect, collections.abc, dataclasses, typing, strawberry, django.db, LOOKUP_SEP, Col/Star, GraphQLError, GraphQLCoreConverter, Info | machinery names | machinery |
| 14 | `from .exceptions import ...` (6 names) | rejection renderers | consumer (F6) |
| 15 | `from .registry import registry` | canonical read | consumer (R1) |
| 16 | `from .resource_policy import ...` (7 names) | policy/bound/window/cleanup | consumer (R10) |
| 17 | `from .types import DjangoType` | validator subject | machinery (R1) |
| 18 | `from .types.base import _is_relay_shaped` | Relay-shape predicate | consumer (R1) |
| 19 | `from .utils.directives import validated_field_directives` | directive gate | consumer (R10) |
| 20 | `from .utils.execution_mode import ...` | color readers | consumer (R10) |
| 21 | `from .utils.querysets import ...` (14 names) | substrate + guards + seed | consumer (F1, F2, F3, F4, F5) |
| 22 | `from .utils.typing import is_async_callable` | color test | consumer (R10) |
| 23 | `if TYPE_CHECKING:` import | type-only name | machinery |
| 24 | `__all__ = ("DjangoListField", "ListArgumentError")` | public pair | projection (R3) |
| 25 | `_KNOWN_LIST_ARGUMENT_REASONS` frozenset (5 reasons) | reason vocabulary | R3 |
| 26 | `def _validate_djangotype_target` | shared target guards | R1 |
| 27 | `def _validate_relay_djangotype_target` | Relay-shaped guard | R1 |
| 28 | `class ListArgumentError` (`__init__`, `__reduce__`) | typed rejection | R3 (+ F6) |
| 29 | `_DEFAULT_WIRE_NAMES` | error-path fallback | R4 |
| 30 | `def _published_wire_name` | published-map read | R4 |
| 31 | `def _resolve_argument_wire_name` | lazy wire resolve | R4 |
| 32 | `class _ListArguments` (5 fields) | validation record | R5 |
| 33 | `def _normalize_list_arguments` | int/ceiling validation | R5 |
| 34 | `def _synthesized_list_signature` | SDL signature | R6 (+ J3) |
| 35-38 | `_ORDER_FROM_EXTRA/EXPLICIT/MODEL_DEFAULT/NOTHING` | selection-source tags | R7 |
| 39 | `_READABLE_ORDER_LEAVES` (`Value`, `Col`, `Star`) | readable leaves | R7 |
| 40 | `_ORDER_VALUE_CONTAINERS` (list/tuple/set/frozenset) | value containers | R7 |
| 41 | `def _is_deterministic_order_name` | name resolution | R7 (+ J1) |
| 42 | `def _is_deterministic_order_term` | term classification | R7 (+ J1) |
| 43 | `def _is_deterministic_order_value` | lookup-value read | R7 (+ J1) |
| 44 | `def _is_deterministic_order_condition` | predicate read | R7 (+ J1) |
| 45 | `def _selected_ordering` | compiler-precedence read | R7 |
| 46 | `def _has_deterministic_ordering` | selected-order verdict | R7 |
| 47 | `def _is_model_default_ordering_active` | model-order verdict | R7 |
| 48 | `def _model_from_definition` | one-read model | R2 (+ F5) |
| 49 | `def _orderset_class_from_definition` | one-read sidecar | R2 (+ J2) |
| 50 | `def _field_label` | resolver label | R8 (+ J4) |
| 51 | `def _resolver_root_and_info` | call-shape guard | R8 |
| 52 | `def _argument_record` | root/info/record split | R8 |
| 53 | `def _build_non_queryset_rejection_error` | sync rejection build | R8 |
| 54 | `async def _handle_non_queryset_rejections_async` | async rejection + close | R8 (+ F1) |
| 55 | `def _require_orderset_class` | direct-call orderset gate | R8 |
| 56 | `def _apply_orderset_sync` | freeze + seal (sync) | F4 |
| 57 | `async def _apply_orderset_async` | freeze + seal (async) | F4 |
| 58 | `def _check_nonzero_offset_guard` | offset/order precondition | R9 |
| 59 | `def _order_normalization_scope` | capture scope | R9 |
| 60 | `def _execute_queryset_pipeline_sync` | sync composition | R10 |
| 61 | `async def _execute_queryset_pipeline_async` | async composition | R10 |
| 62 | `def DjangoListField` (+ nested `_default`, `_resolve_async_iterable`, sync/async `_wrap`) | field factory | R10 |

Rules: F1-F6 reuse the plan's existing family names (no new family named);
R1-R10 are file-local; J1-J4 are recorded rejections. The plan's
`## Responsibility index` already carries all six families with this file
listed - reused, not renamed.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 disposal | disposal must handle a third awaitable kind | **1** (`utils/querysets.py::_dispose_sync_awaitable`; this file's three consume sites follow as consumers) | consumer |
| C2 | F1 guard choice | sync pipeline must refuse a new async shape | **1** (the guard owned in querysets; this file passes a different guard per color, unchanged) | consumer |
| C3 | F2 seal | a new untrusted queryset shape must be rebuilt | **1** (the seal; this file's pipelines + appliers run on sealed output) | consumer |
| C4 | F3 async-shape | route this file's `is_async_only_iterable` uses through a new predicate | **1** (the predicate; the four use sites here follow) | consumer |
| C5 | F4 post-apply seal | the post-apply contract gains an axis (e.g. allow evaluated) | **1 owned + 1 absent** (this file's twins seal via `utils/querysets.py::_validate_post_orderset_result`; connection has no call - D3, already routed, no verdict here) | ambiguous-routed |
| C6 | F5 seed | default seed must pin a new routing fact | **1** (`utils/querysets.py::base_queryset`; this file's default branch follows) | consumer |
| C7 | F5 model read | definition model read must fail loud on a hostile metaclass | **1** at the validator (`list_field.py::_model_from_definition` validates; pipelines rely on the factory-time read - J2) | consumer |
| C8 | F6 rejection tail | a new hostile value kind must render safely | **1** (`exceptions.py::describe_value` family; this file's six render sites follow) | consumer |
| C9 | R1 registry rule | registry identity comparison changes | **1** (`list_field.py::_validate_djangotype_target`; connection + relay follow as consumers) | file-local |
| C10 | R1 Relay-shape rule | Relay-shaped spelling gains a third arm | **1** (`list_field.py::_validate_relay_djangotype_target`) | file-local |
| C11 | R3 reason vocabulary | a sixth `ListArgumentError` reason ships | **1** (frozenset + `__init__` arm + `__reduce__` passthrough move together) | file-local |
| C12 | R4 wire fallback | a fourth published argument needs a default spelling | **1** (`list_field.py::_DEFAULT_WIRE_NAMES` + both readers move together) | file-local |
| C13 | R5 validation axis | offset gains a new check (e.g. max-skip discount) | **1** (`list_field.py::_normalize_list_arguments`; the record gains the field) | file-local |
| C14 | R6 signature | a fourth SDL argument kind ships | **1** (`list_field.py::_synthesized_list_signature`) | file-local |
| C15 | R7 volatile leaf | a new volatile expression leaf must classify un-readable | **1 owner** (the seven-function cluster + six constants move together, all in this file) | file-local |
| C16 | R7 precedence | the compiler's collection precedence changes | **1** (`list_field.py::_selected_ordering`; both verdicts follow) | file-local |
| C17 | R8 call shape | the resolver accepts a new positional input | **1** (`list_field.py::_resolver_root_and_info` + `_argument_record` move together) | file-local |
| C18 | R8 non-queryset kind | a new non-queryset source kind must be rejected | **1 owner** (builder + async handler move together) | file-local |
| C19 | R9 order source | a third eligible order source ships | **1 owner** (guard + scope move together) | file-local |
| C20 | R10 pipeline step | a new pipeline step (e.g. post-window hook) ships | **1 owner, two bodies** (sync + async twins move together by color) | file-local |
| C21 | J1-J4 | the four refused shared forms | **0 moves - refused**, differences + triggers in findings | refused |
| C22 | one-sync-boundary / raw-body | the file gains a worker-run hook / body read | **0** (no such surface; probe absences) | inapplicable |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest - the workspace recipe is for mutating
proofs, of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-list_field/probe_w1.py
```

Output (`ALL OK`, 42 checks): 63-member module AST; 28 functions + 2
classes (`ListArgumentError` 3 members, `_ListArguments` 5 fields);
querysets 14-name / resource_policy 7-name / exceptions 6-name import
census; 7 absence claims; single-site claims (reason frozenset, wire
fallback, order constants, `LIST_ARGUMENT_INVALID` once); the OrderSet
seal asymmetry (connection 0 seal + 0 snapshot with 1 `apply_sync(` + 1
`apply_async(`; list 3 + 3); consumer-role positive claims (async-only 4,
adapter-wrap 6, default seed, visibility twins, prepared 3, dispose 3,
windowed pair, policy pair); shared-validator export shape (defined here,
consumed by connection + relay); twin scope/guard sharing (3 + 3);
item-baseline diff empty. One first-draft check failed on probe precision
(function count 29 vs the true 28 - corrected) and one on census precision
(resource_policy 6 vs the true 7 - corrected); both re-verified green,
substance unaffected. Status: `execution-verified` for every
identity/count/shape/absence claim below. Rejects the wrong results "a
second definition lives here", "the target drifted from its baseline",
"the connection seals too".

## Findings

No production edit is owed by a file item; the six families below are
REUSED from the plan (list-side roles re-challenged fresh), the rest are
file-local records and four recorded rejections.

### F1 - awaitable refusal and disposal (existing family `awaitable-refusal-and-disposal`, stays `open`)

- **Contract + variation.** A refused awaitable is detected without
  awaiting it and released so no never-awaited warning escapes; what
  follows the disposal (which error, which sentinel) varies per seam.
- **Sites + roles.** *Definitions*: per the plan index,
  `utils/querysets.py::_dispose_sync_awaitable` plus the two inline
  detect-then-dispose sites (owner side; family item's surface).
  *Consumers here*: `list_field.py::_apply_orderset_sync` (disposes an
  awaitable `apply_sync` return, raises `SyncMisuseError`),
  `list_field.py::_apply_orderset_async` (disposes a residual awaitable,
  raises `ConfigurationError`), `list_field.py::DjangoListField` sync
  `_wrap` (the `reject_async_iterable_in_sync_context` call plus
  `prepared_resolver_source` with `reject_awaitable_sync_source`),
  async `_wrap` (`prepared_resolver_source` with
  `reject_residual_async_source`),
  `list_field.py::_handle_non_queryset_rejections_async` (cleanup via
  `resource_policy.py::_cleanup_rejected_async_iterable` on every
  rejecting exit, including builder failure). *Oracles*: the hostile-int /
  async-misuse rows in `tests/test_list_field.py` plus the family gate.
  *Projections*: the applier and factory docstrings' color contracts.
- **Challenges.** C1, C2 - 1 each, both at the querysets owner; zero
  definitions here.
- **Owner + lifetime.** `utils/querysets.py::_dispose_sync_awaitable`
  (unchanged). No stored derivation here.
- **Migration.** None (zero-edit item; consumer role only).
- **Distinct behavior.** The per-color guard choice stays at the caller
  (each pipeline passes its `async_guard` explicitly) - a change to which
  shape the sync pipeline refuses moves the guard, not the head.
- **Behavioral proof.** `static-reviewed` for the consumer role (import
  block + five call sites + applier bodies read); `execution-verified`
  for the import/absence census (probe). Rejects "this file disposes an
  awaitable itself".
- **Structural gate.** The existing async-misuse oracles (sync applier
  meeting an awaitable raises `SyncMisuseError`; async iterable over
  `execute_sync` is refused; rejected async-only source is closed).
  Negative control: a hand copy of the guard call deleted from the sync
  `_wrap` passes every happy-path oracle and fails exactly those rows.
- **Coupling.** None.
- **Freshness.** `django_strawberry_framework/list_field.py`
  `f357eded3d96fcffe17e6fd84bceb8cd12af98d5`,
  `django_strawberry_framework/utils/querysets.py`
  `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`,
  `django_strawberry_framework/resource_policy.py`
  `647133d23785d325856b2d1d495d18c5741dd23c`,
  `tests/test_list_field.py`
  `e68ffe2b3270435775bf768e727ad3a4980d8ccd` (oracle titles only).

### F2 - sealed-execution queryset (existing family `sealed-execution-queryset`, stays `open`)

- **Contract + variation.** A consumer-supplied or hook-returned
  queryset is untrusted state: validated and rebuilt by the seal; policy
  variation is declared on `_SealPolicy`, not branched at consumers.
- **Sites + roles.** *Definition*: the seal in `utils/querysets.py`
  (owner side). *Consumers here*:
  `list_field.py::_execute_queryset_pipeline_sync` /
  `list_field.py::_execute_queryset_pipeline_async` (visibility runners,
  default-policy no-arg branch vs `_LIST_ARGUMENT_VISIBILITY_POLICY`
  argument branch), `list_field.py::_apply_orderset_sync` /
  `list_field.py::_apply_orderset_async` (freeze-then-seal, F4).
  Package-wide mechanism sweep for the seal's construction vocabulary
  (`models.QuerySet(`, `sql.Query`) finds zero hits in this file (probe
  absence); every read here (`query.annotations`, `query.extra`,
  `query.extra_order_by`, `query.order_by`, `query.default_ordering`,
  `query.group_by`) is a planning question on an already-sealed object.
- **Challenges.** C3 - 1 at the seal; zero definitions here.
- **Owner + lifetime.** `utils/querysets.py::_seal_or_defect`
  (unchanged). No stored derivation here.
- **Migration.** None.
- **Distinct behavior.** Nothing here rebuilds a queryset from state;
  the deterministic-order cluster classifies the sealed queryset's
  already-selected ordering rather than re-deriving it per collection.
- **Behavioral proof.** `static-reviewed` (both pipelines + both
  appliers + all seven classifier bodies read); `execution-verified`
  for the census.
- **Structural gate.** The seal's own oracle suite plus the combined /
  sliced hostile-shape rows reaching the argument-bearing branch (a
  combined source is accepted omission-mode and rejected argument-mode -
  the spec-050 `offset: 0` mode distinction the package tier pins).
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `1539b66c…`.

### F3 - async-only queryset row adapter (existing family `async-only-queryset-row-adapter`, stays `open`)

- **Contract + variation.** `utils/querysets.py::is_async_only_iterable`
  (`AsyncIterable and not Iterable`) exists so a QuerySet (both) never
  classifies as async-only. The adapter trio around
  `utils/querysets.py::_AsyncQuerySetRows` completes a final sliced
  queryset under async execution without synchronous ORM iteration.
- **Sites + roles.** This file holds NO definition (probe
  `absent-_validate_post_orderset-local-def` analog holds for the adapter:
  no `class _AsyncQuerySetRows`, no `def wrap_` here). *Consumers here*:
  `is_async_only_iterable` at four sites (sync `_wrap` async-only branch,
  both exits of `list_field.py::_handle_non_queryset_rejections_async`),
  `wrap_async_queryset_adapter` at six sites (every queryset return: both
  no-arg branches, both windowed tails, both async-iterable cleanups read
  through). *Sibling consumers*: the optimizer extension unwrap side.
- **Challenges.** C4 - 1 at the predicate; zero definitions here.
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here (the adapter object is returned, never cached).
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (all four predicate sites +
  all six wrap sites read); `execution-verified` for the census.
- **Structural gate.** The async live-suite rows
  (`test_list_field_async_api.py`: safe async completion without
  `DJANGO_ALLOW_ASYNC_UNSAFE`, async-iterable cleanup with zero advances
  and exactly one close); a substitution routing querysets down the
  sync branch fails them by construction.
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `1539b66c…` +
  `examples/fakeshop/test_query/test_list_field_async_api.py`
  `c3e268b6245ed46adf0d91e99b1a87367551c0c9`.

### F4 - post-set-apply result validation (existing family `post-set-apply-result-validation`, stays `open`)

- **Contract + variation.** A public `OrderSet.apply_*` override's
  return is re-sealed (lazy, unsliced, model-row-shaped, non-combined,
  same route) before the surface windows it. The freeze must precede the
  override (it can mutate the handed object, so a post-call read is not a
  baseline).
- **Sites + roles.** *Definition*:
  `utils/querysets.py::_validate_post_orderset_result`, enforced at
  `list_field.py::_apply_orderset_sync` / `_apply_orderset_async`
  (both read fresh: freeze via
  `utils/querysets.py::_snapshot_routing_intent`, then the seal with
  `model=` the factory's captured model). *Unguarded member* (re-derived
  fresh here, not inherited): `connection.py::_pipeline_sync` /
  `connection.py::_pipeline_async` invoke the same public
  `OrderSet.apply_sync` / `apply_async` (via
  `connection.py::_sidecar_steps`) and pass the return straight to
  `connection.py::_finalize_queryset` (probe `asym-conn-no-seal`,
  `asym-conn-no-snapshot`; one `apply_sync(` plus one `apply_async(`
  each, both call sites read). This file DOES seal; the asymmetry is
  confirmed present.
- **Challenges.** C5 - 1 owned + 1 absent. No verdict (ambiguous: both
  contract sources found scope the rule to the list field - spec-050 Edge
  cases plus `_SealPolicy.require_unevaluated` prose reasoning from "the
  list field invoked that ordering method one step earlier and takes its
  window on what comes back" - while the connection also windows what
  comes back via Relay slicing; D3, routed to the maintainer by the querysets item;
  re-confirmed present, not re-homed per brief).
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here beyond the per-call frozen intent (handed to the
  validator, never cached).
- **Migration.** None (file item; the family item owns the decision).
- **Behavioral proof.** `static-reviewed` (both appliers + both
  connection pipelines read). No consolidation depends on it.
- **Structural gate.** The list-field override-misbehavior oracles; no
  connection-side oracle exists for the unguarded member (that absence is
  the routed ambiguity).
- **Coupling.** None (D3 touches the same pipeline as nothing else here).
- **Freshness.** Target as in F1 + `utils/querysets.py` `1539b66c…` +
  `django_strawberry_framework/connection.py` working `3c4d5dcb…` / HEAD
  `93e998f2…` (call-site census only; the external hunk touches none of
  the fingerprinted sites).

### F5 - queryset seed and model read (existing family `queryset-seed-and-model-read`, stays `open`)

- **Contract + variation.** A surface seeds its default queryset from the
  captured model and reads the model off the ONE construction-time
  definition, so seed and seal cannot be answered from two different
  reads.
- **Sites + roles.** *Definitions*: `utils/querysets.py::model_for`
  (single `_meta` read site) + `utils/querysets.py::base_queryset`
  (seed with `using` arm). *Consumers here*:
  `list_field.py::DjangoListField` default branch
  (`base_queryset(target_model)`) and the `model=` threading through both
  pipelines into both visibility seals and the post-OrderSet seal (probe
  `consumer-base_queryset`; `model_for` / `initial_queryset` absent here
  by construction - the factory seeds from its validated definition
  read, not from the type key). *Sibling consumers*: the connection
  default seed, the walker, the filter child.
- **Challenges.** C6 (1, seed), C7 (1, at the validator - J2).
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here (the `definition` object is handed down at
  construction, never cached beyond the field closure).
- **Migration.** None.
- **Distinct behavior.** The captured-read discipline (J2): this file
  validates once at construction and threads the answers; per-read
  re-validation would double-own the failure contract.
- **Behavioral proof.** `static-reviewed` (factory + both pipelines
  read); `execution-verified` for the census.
- **Structural gate.** The default-field oracles (an unseedable model
  fails at field construction, never per request) plus the no-argument
  SQL-parity rows.
- **Coupling.** None.
- **Freshness.** Target as in F1 + `utils/querysets.py` `1539b66c…`.

### F6 - typed rejection value tail (existing family `typed-rejection-value-tail`, stays `open`)

- **Contract + variation.** Every deployment-supplied value in a
  rejection message renders through the guarded helpers, so a hostile
  `__repr__` / metaclass `__name__` / un-stringifiable int cannot detonate
  message assembly and replace the typed rejection with a raw error.
- **Sites + roles.** *Definition*: `exceptions.py::describe_value`
  (plus `exceptions.py::_safe_arg_repr`,
  `exceptions.py::_safe_class_name`, `exceptions.py::_safe_type_name`).
  *Consumers here* (six render sites, all read): the validator messages
  (`_safe_arg_repr` non-class arm, `_safe_class_name` class arms),
  `list_field.py::ListArgumentError.__init__` (`describe_value` on the
  `non_integer` arm, `_safe_arg_repr` on the numeric arms),
  `list_field.py::_normalize_list_arguments` (same split),
  `list_field.py::_model_from_definition` /
  `list_field.py::_orderset_class_from_definition` (fail-loud reads),
  `list_field.py::_check_nonzero_offset_guard` and the non-queryset
  rejection builder (wire-name + value renders). *Oracles*: the
  hostile-repr / hostile-name / unprintable-large-int rows in
  `tests/test_list_field.py`.
- **Challenges.** C8 - 1 at the exceptions owner; zero definitions here.
- **Owner + lifetime.** `django_strawberry_framework/exceptions.py`
  (unchanged). No stored derivation here.
- **Migration.** None.
- **Behavioral proof.** `static-reviewed` (all six render sites read);
  `execution-verified` for the census.
- **Structural gate.** The hostile-value oracles (a hostile `__repr__`
  still yields the typed rejection; `10**10000` still yields
  `non_integer` rather than a raw `ValueError`).
- **Coupling.** None.
- **Freshness.** Target as in F1 +
  `django_strawberry_framework/exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` +
  `tests/test_list_field.py` `e68ffe2b…`.

### File-local records (no second definition after the matrix)

- **R1 - shared DjangoType-target validators.**
  `list_field.py::_validate_djangotype_target` (class check, subclass
  check, contained definition read, registry-identity canonicality,
  resolver callability) plus
  `list_field.py::_validate_relay_djangotype_target` (delegates, then the
  Relay-Node-shaped guard) (C9, C10 - 1 each). Single definition here;
  connection and relay compose it by name (probe `defines-*` plus both
  `*-consumes`). The order is load-bearing (each check assumes the
  previous passed); the identity comparison (not `hasattr`, not `==`)
  rejects fabricated same-origin lookalikes, copies, and never-registered
  definitions at the constructing line. Trigger: a fourth collection
  factory entering through the same validator extends the consumer list,
  not the rule. Freshness: target +
  `django_strawberry_framework/connection.py` `3c4d5dcb…`/`93e998f2…` +
  `django_strawberry_framework/relay.py` `c3c5aea5…` +
  `django_strawberry_framework/registry.py` `9cc8bb55…`.
- **R2 - validating definition readers.**
  `list_field.py::_model_from_definition` (fail-loud model read with
  Django-model check) plus
  `list_field.py::_orderset_class_from_definition` (fail-loud sidecar
  read) (C7 - 1 each here). Called exactly once per field at
  construction from the validator's ONE returned object; seed, seals,
  signature, and dispatch all run on those two captured values. Trigger:
  a new captured sidecar (e.g. a filter class read the same way) joins
  this record, not a new rule. Freshness: target (+ J2 for the
  connection-side contrast).
- **R3 - typed argument-error vocabulary.**
  `list_field.py::ListArgumentError` plus
  `list_field.py::_KNOWN_LIST_ARGUMENT_REASONS` (5 reasons) plus the
  `__reduce__` pickle contract (C11 - 1). Unknown reasons fail closed
  with `ValueError`; `extensions` carries the stable `code`/`argument`/
  `reason` plus `value`/`ceiling` where the contract says; the GraphQL
  wire spelling (not the Python parameter name) is what `argument`
  carries. Trigger: a sixth reason extends the frozenset plus one
  `__init__` arm. Freshness: target +
  `django_strawberry_framework/__init__.py` `0ef72601…` (root export) +
  `tests/test_list_field.py` `e68ffe2b…` (pickle/reason rows).
- **R4 - lazy wire-name resolution.**
  `list_field.py::_published_wire_name` (executable-schema map read with
  `DEFINITION_BACKREF` identity) plus
  `list_field.py::_resolve_argument_wire_name` (fallback to
  `list_field.py::_DEFAULT_WIRE_NAMES` when no schema metadata rides the
  call) (C12 - 1). Only invoked on error paths, so successful requests
  pay zero lookups; the consumer-owned `NameConverter` is never invoked
  at request time. Trigger: a fourth argument joins the fallback map.
  Freshness: target.
- **R5 - normalized-arguments record.**
  `list_field.py::_ListArguments` (5 fields keeping supplied-ness,
  window, order-supplied, and mode apart by construction) plus
  `list_field.py::_normalize_list_arguments` (exact-`int` gate rejecting
  `bool` and subclasses before any hook can run, offset-before-limit
  order, offset ceiling from the request policy, limit ceiling from the
  effective bound) (C13 - 1). `any_argument_supplied` selects the
  argument-bearing pipeline and the reject-combined admissibility - a
  MODE decision, never a window comparison (`offset: 0` is window-equal
  to omission, mode-different). Trigger: a fourth argument extends the
  record plus one normalizer branch. Freshness: target +
  `tests/test_list_field.py` `e68ffe2b…` (normalizer rows).
- **R6 - list SDL synthesizer.**
  `list_field.py::_synthesized_list_signature` (`root` positional plus
  keyword-only `info`/`offset`/`limit`, conditional `order_by` from the
  captured class via a function-local `order_input_type` import; empty
  return annotation so the class-attribute annotation keeps sole
  ownership of outer nullability) (C14 - 1; J3 for the connection-twin
  refusal). Trigger: a fourth SDL argument extends this builder alone.
  Freshness: target + `tests/test_list_field.py` `e68ffe2b…`
  (signature-shape rows).
- **R7 - deterministic-order classification cluster.**
  Seven functions (`list_field.py::_is_deterministic_order_name`,
  `list_field.py::_is_deterministic_order_term`,
  `list_field.py::_is_deterministic_order_value`,
  `list_field.py::_is_deterministic_order_condition`,
  `list_field.py::_selected_ordering`,
  `list_field.py::_has_deterministic_ordering`,
  `list_field.py::_is_model_default_ordering_active`) plus six constants
  (four `_ORDER_FROM_*` sources, `list_field.py::_READABLE_ORDER_LEAVES`,
  `list_field.py::_ORDER_VALUE_CONTAINERS`) (C15, C16 - 1 owner each).
  One classification of the already-sealed queryset read two ways (is the
  selected order deterministic; is the model's own ordering that order),
  mirroring `SQLCompiler._order_by_pairs` precedence (extra wins,
  explicit next, model default only when nothing explicit stands).
  Extra/raw leaves are opaque (fail closed, never certified); compositions
  are transparent down to columns and literals; containers are read one
  bracket deeper. Trigger: a new volatile leaf or a compiler-precedence
  change moves this cluster alone. Freshness: target (+ J1 for the
  keyset contrast).
- **R8 - resolver invocation and non-queryset rejection.**
  `list_field.py::_field_label` (hostile-descriptor-contained label),
  `list_field.py::_resolver_root_and_info` (positional/keyword shape
  guard), `list_field.py::_argument_record` (root/info/record split),
  `list_field.py::_build_non_queryset_rejection_error` (sync build:
  `queryset_required` on any supplied `order_by`, `order_required` on
  positive offset), `list_field.py::_handle_non_queryset_rejections_async`
  (async twin: same close on EVERY rejecting exit including builder
  failure), `list_field.py::_require_orderset_class` (direct-call-only
  gate for ordering without a sidecar) (C17, C18 - 1 owner each).
  Trigger: a new resolver input or a new non-queryset source kind moves
  this record. Freshness: target.
- **R9 - offset precondition and its capture scope.**
  `list_field.py::_check_nonzero_offset_guard` (positive offset needs a
  materially active order - supplied `orderBy` with surviving terms on an
  ordered deterministically-ordered queryset, or still-effective model
  `Meta.ordering` with `default_ordering is True` and no `group_by`) plus
  `list_field.py::_order_normalization_scope` (one conditional task-local
  capture spanning public ordering and the guard, opened only when a
  positive offset arrives WITH an `orderBy` AND a captured OrderSet)
  (C19 - 1 owner). No pk tiebreaker, no `DISTINCT` - ordered offset, not
  stable pagination. Trigger: a third eligible order source moves both
  together. Freshness: target + `examples/fakeshop/test_query/test_list_field_api.py`
  `bf0c02dd…` (offset/order live rows).
- **R10 - queryset pipelines and field factory.**
  `list_field.py::_execute_queryset_pipeline_sync` /
  `list_field.py::_execute_queryset_pipeline_async` (visibility, then
  OrderSet, then the offset guard, then the one raw-list slice; no-arg
  fast paths keep byte-identical SQL) plus `list_field.py::DjangoListField`
  (construction validation, ONE definition read, captured model/sidecar,
  directive validation, per-construction sync/async commitment, default
  vs consumer-resolver branches, signature assignment, `strawberry.field`
  return) (C20 - 1 owner, two bodies by color). Seams composed by name:
  `resource_policy.py` window/bound/policy/cleanup,
  `utils/directives.py::validated_field_directives`,
  `utils/execution_mode.py` readers, `utils/typing.py::is_async_callable`.
  Trigger: a new pipeline step moves the twins together. Freshness:
  target + `django_strawberry_framework/resource_policy.py`
  `647133d2…` + `django_strawberry_framework/utils/directives.py`
  `380786cf…` + `django_strawberry_framework/utils/execution_mode.py`
  `9805cdaf…` + `django_strawberry_framework/utils/typing.py`
  `de6309f6…` + both live suites.

### J1 - deterministic-order predicates vs keyset entry anchorability (rejection, not a family)

`list_field.py::_is_deterministic_order_name` / `_term` / `_value` /
`_condition` plus `list_field.py::_selected_ordering` /
`list_field.py::_has_deterministic_ordering` (is the applied ordering
deterministic for an offset window?) vs
`connection.py::_keyset_order_ref` (can a value cursor anchor on this one
effective-order entry?). Considered shared form: one order-entry
classifier. Contract difference (re-derived fresh from the list side, not
inherited): anchorability rejects unresolvable expressions and explicit
NULLS positioning per entry for cursor minting; determinism certifies a
whole applied ordering for skip pagination - a deterministic entry can
still be unanchorable (explicit nulls) and an anchorable entry says
nothing about the whole. Reconsideration trigger: the keyset slicer ever
certifies whole orderings, or the list field ever mints value cursors.
Durable home: this finding (a file item lands no edit).

### J2 - validating definition readers vs captured direct reads (rejection, not a family)

`list_field.py::_model_from_definition` /
`list_field.py::_orderset_class_from_definition` (validate-then-read with
fail-loud `ConfigurationError` arms, called once at construction) vs this
file's consumers in connection (`definition.model`,
`definition.cursor_field`, `definition.filterset_class`,
`definition.orderset_class`, `definition.connection`,
`definition.graphql_type_name` read directly off the factory's captured
object). Considered shared form: routing connection's reads through the
list validators. Contract difference: the connection factory already
validates through `list_field.py::_validate_relay_djangotype_target` at
construction, so per-read re-validation would double-own the failure
contract and fork the error framing (`DjangoConnectionField` vs
`DjangoListField` labels); the validators pin list-flavored labels the
connection must not emit. Reconsideration trigger: a
stateful-definition substitution bug traced to a connection read - then
that site gains validation, not a shared reader. Durable home: the
factory + pipeline docstrings (already record the captured-read
contract) + this finding.

### J3 - list vs connection signature synthesis (rejection, not a family)

`list_field.py::_synthesized_list_signature` (plain-field arguments
`offset`/`limit`/conditional `order_by`, empty return annotation) vs
`connection.py::_synthesized_signature` (sidecar `filter` / `order_by`
beside `root`/`info`, `Iterable[target]` return for
`ConnectionExtension.apply`). Considered shared form: one synthesizer for
both flavors. Contract difference: the connection signature is the
`ConnectionExtension` contract (kwargs-forwarded sidecars, reserved
`root`/`info` binding, orphan-ledger registration for the finalizer);
the list signature is the plain-field contract with sole-ownership of
outer nullability kept at the class attribute. They share the
`filter_input_type` / `order_input_type` helpers by name already - that
sharing is the correct level. Reversing the import edge would close a
module cycle (connection already imports the relay-target guard from
here). Reconsideration trigger: a third flavor synthesizing
`ConnectionExtension`-shaped signatures. Durable home: both
synthesizers' docstrings + this finding.

### J4 - same-token different-contract neighbors (rejection, not a family)

`list_field.py::_field_label` (resolver `info.field_name` with
`DjangoListField` default) vs `types/converters.py::_field_label`
(`Model.field` diagnostic); `list_field.py::_validate_djangotype_target`
(DjangoType registry identity) vs
`mutations/fields.py::_validate_mutation_target` (mutation-protocol duck
type). Considered shared forms: one label helper, one target validator.
Contract differences: resolver-label vs model-diagnostic inputs and
defaults; registry-identity vs protocol-membership subjects. Merging
either would couple independent failure contracts to one spelling.
Reconsideration trigger: a caller needing the other contract's answer
(e.g. a resolver label in `Model.field` form). Durable home: this
finding.

## Defects

None. Every claim checked while tracing held: the validator order and
identity comparison present; the one-read discipline stated at every
capture; the exact-int gate ahead of every hook; the wire-name laziness
(success paths perform zero lookups); the compiler-precedence selection
read once and classified twice; the guard's empty-queryset allowance
confined to the active-input branch as documented; the scope opening
exactly on the guard's handoff precondition; both pipelines running
visibility before OrderSet before guard before window; the applier twins
freezing before the override and sealing after; the factory committing
color per construction with the event-loop completion discipline
recorded. The one known list-adjacent row keeps its existing home: D3
(connection runs `OrderSet.apply_*` with no post-apply seal - ambiguous,
already routed to the maintainer, re-confirmed present with fresh counts, not
re-homed per brief). No new defect is routed to any owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
whole-tree sweeps, command in `### Challenges`) already ran green
against the shared tree; they mutate no source and open no database, so
no workspace copy was owed and no `__file__`/DB `NAME` record applies.
No pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED`
or Postgres cell is owed: this artifact's claims (statement counts,
import census, absence/single-site facts, baseline diff, call-site
censuses) touch no database, alias, or dialect decision (`inapplicable
by construction` - the target's DB-reaching paths are exercised by the
oracles cited, not by this probe).

## Judgment

Backstop discharged: 63/63 working-tree `ast.Module.body` members
enumerated, 22 challenges run, every rule terminating in one of the six
existing plan families (re-challenged fresh on the list side - F4 stays
ambiguous-routed at 1 owned + 1 absent, F1/F2/F3/F5/F6 confirmed consumer
roles), a file-local record with its proving challenge (R1-R10), or a
recorded rejection with difference + trigger + home (J1-J4) - no
consolidation owed, no defect found, no new family named. Zero-edit result
is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: every family
this target touches is already indexed with this file listed; the four
refused shared forms live at their owner docstrings plus this finding.

## Independent verification (Worker 2)

Own trace, re-derived fresh (probe `docs/dry/temp-tests/dry-file-list_field-w2/probe_w2.py`,
`ALL OK` 45/45, read-only: AST + token census, no Django setup, no DB, no
mutation, no shared-tree pytest). Instrument of my own: `ast.parse` over the
working-tree blob.

**Counts (mine).** 63 `ast.Module.body` statements; 28 functions (25 `def` +
3 `async def`: `_handle_non_queryset_rejections_async`,
`_apply_orderset_async`, `_execute_queryset_pipeline_async`); 2 classes
(`ListArgumentError` with exactly `__init__` + `__reduce__`,
`_ListArguments` with 5 `AnnAssign` fields). Import census: querysets block
14 names, resource_policy block 7, exceptions block 6. Vocabulary: 5 reasons
in the frozenset literal, `LIST_ARGUMENT_INVALID` once, 3-key wire fallback.
Absences: `run_in_one_sync_boundary` 0, `sync_to_async` 0,
`models.QuerySet(` 0, `class _AsyncQuerySetRows` 0, `model_for` 0,
`initial_queryset` 0, raw-body reads 0. Consumer occurrences (incl. import
line): `is_async_only_iterable` 4, `wrap_async_queryset_adapter` 6,
`prepared_resolver_source` 3, `_dispose_sync_awaitable` 3,
`_LIST_ARGUMENT_VISIBILITY_POLICY` 3, scope 3, guard 3, seal uses 2,
snapshot uses 2. Asymmetry: connection seal 0 + snapshot 0 with
`apply_sync(` 1 + `apply_async(` 1. Export shape: base validator defined
once here, imported by connection; relay defines its `_validate_node_target`
wrapper. J-premises: connection `_keyset_order_ref` present,
mutation-protocol guard present with `_mutation_meta` subject, converter
`_field_label` present, connection synthesizer present with
`ConnectionExtension` contract. Target blob
`f357eded3d96fcffe17e6fd84bceb8cd12af98d5`; item diff empty; target clean.

**Owners I would choose (before opening Findings).** Validators: this file
(narrowest module both connection and relay already import from; relay +
connection consume by name). Definition readers: this file's factory
closure (one-read discipline). Error vocab, wire names, arguments record,
SDL synthesizer, deterministic cluster (7 fns + 6 consts move together),
resolver-invocation group, offset guard + scope, pipeline twins + factory:
all this file (no second site found on any axis). Disposal, seal,
async-only predicate/adapter, default seed, rejection tail: owners in
`utils/querysets.py` / `exceptions.py`, this file consumer only. Post-apply
seal: querysets owner; connection's missing call is a real asymmetry with
ambiguous scope (both contract sources name the list field while the
connection also windows) - route, don't consolidate. Sync-boundary and
raw-body: no surface here, inapplicable by construction. No new family
named; no consolidation candidate found anywhere on the six axes.

**Reconciliation vs W1.** Agree on every row: 63 members; 6 reused families
(F1/F2/F3/F5/F6 consumer, F4 1-owned-plus-1-absent ambiguous-routed);
R1-R10 file-local; J1-J4 refused; zero defects; zero pending. Precision
notes, none verdict-affecting: (a) "wrap at six sites" counts 6
occurrences (1 import + 4 code uses + 1 docstring mention) - true call
sites are 4; consumer role and no-definition claim unaffected. (b) "67
test functions" confirmed via AST walk (60 `def` + 7 `async def`); a naive
`^def` grep undercounts at 60. (c) J3's "durable home: both synthesizers'
docstrings" overstates slightly - neither docstring names the twin (each
records its own contract; the connection side records the
`ConnectionExtension` requirement that IS the contract difference); the
separation itself lives in this finding, which Worker 0 carries to
closeout Outcomes. Not a defect: no contract row breaks, no wire input
reaches it.

**Enumeration.** Checked member-by-member against my own parse: all 28
named functions + 2 classes + 4 order-source tags + 2 order constants +
`__all__` + `TYPE_CHECKING` + 13 import statements + module docstring land
in W1's rows 0-62 exactly as assigned. No unassigned member.

**Matrix.** Judged on reasons, not inherited: axis 1 traced against the
real connection working tree incl. the external hunk (mirroring claims
hold; hunk touches none of the fingerprinted sites); axis 2 compared all
three colored pairs by behavior (differences are color duties: await
point, refusal class, per-color guard, adapter tail); axis 3 verified five
derivations reach their owners; axis 4 verified pickle round-trip halves
and the adapter wrap with no second grammar here; axis 5 verified oracles
spell literals (`tests/test_list_field.py` 67 fns, live sync/async suites,
`tests/base/test_init.py` literal `__all__` pin) and read no owner table;
axis 6 ran three member checks with the D3 asymmetry re-derived fresh
(0/0 vs 1/1) and both inapplicability claims confirmed by zero counts.

**Equivalence (principle 8).** No behavior change proposed or made; twin
halves differ only where color requires (documented duties above).
Census/shape/absence claims are `execution-verified` by the W2 probe;
oracle bodies stay `static-reviewed`, which is the honest label for a
zero-edit item.

**Gates / Pending / coupling.** Structural gates are the pre-existing
oracle rows plus reasoned negative controls (hand-copy, substitution);
none executed via `prove_failability.py`, none claimed executed - the
artifact labels them accordingly, so no `## Pending execution` entry is
owed and none exists. Freshness: all 14 blob ids re-hashed by me, all
match (target `f357eded…`, querysets `1539b66c…`, resource_policy
`647133d2…`, exceptions `e06b0b7f…`, connection working `3c4d5dcb…` /
HEAD `93e998f2…`, relay `c3c5aea5…`, registry `9cc8bb55…`, root
`0ef72601…`, directives `380786cf…`, execution_mode `9805cdaf…`, typing
`de6309f6…`, package tests `e68ffe2b…`, live suites `bf0c02dd…` /
`c3e268b6…`). Coupling: none marked, none needed (zero edits).

**AGENTS.md prose.** Item diff empty (re-measured myself); no process
provenance in the artifact (no `path:NN`, no tool log); `path::Symbol`
citations throughout; zero edits so no format/test-tier/commit rules
trigger; concurrent dirt (`connection.py` hunk, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
plan file) untouched. W2 scratch is read-only under
`docs/dry/temp-tests/dry-file-list_field-w2/` (fresh dir, no shared-tree
pytest).

**Defects (Worker 2).** None.

**Verdict.** `verified`, no pending execution. File-item coverage complete:
63/63 assigned, every challenge homed, no production edit owed.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
a5b0ad48730735748bc473d421dd18d12501c5df --
django_strawberry_framework/list_field.py` is empty (0 bytes, re-measured
by the probe `item-diff-empty` check after all reads) - the target blob
`f357eded3d96fcffe17e6fd84bceb8cd12af98d5` equals the item baseline, the
cycle baseline member, and `HEAD:` (`9031cb3d`), so the target is CLEAN
and no hunk attribution was owed. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt
(`django_strawberry_framework/connection.py` working `3c4d5dcb…` vs HEAD
`93e998f2…`, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied (connection read working-tree-incl.-hunk for
the mirroring pass: traced, never judged; test files read as oracles
only). No commit. No ruff run owed (no tracked `.py` edits; artifact is
`.md` only; the probe is untracked scratch under
`docs/dry/temp-tests/dry-file-list_field/`). No `__file__`/DB record (no
workspace copy - no mutating proof exists). Scratch created (not tracked
changes): this artifact `docs/dry/dry-file-list_field.md` and the
read-only probe `docs/dry/temp-tests/dry-file-list_field/probe_w1.py`
(`ALL OK`, 42 checks; no source mutation, no DB, no shared-tree pytest).

read-only probe `docs/dry/temp-tests/dry-file-list_field/probe_w1.py`
(`ALL OK`, 42 checks; no source mutation, no DB, no shared-tree pytest).

## Re-trace at bfaee91d (Worker 1)

Run `0.0.15 2026-09-19-1`. Prior pass verified at `9031cb3d`
(target blob `f357eded3d96fcffe17e6fd84bceb8cd12af98d5`, 1442 lines,
63 members); this pass re-traces the target at `bfaee91d` (worktree
blob `ce682d5f79518919ff3676f2fc8bbe2bd33995a4`, 1884 lines, 79
members) after the reopen. Prior reasoning above is untouched; what
follows reconciles against it. No consolidation in a file item; zero
production edits.

### Scope of the delta

Four commits in `9031cb3d..bfaee91d` touch the target
(`git log` names only `ffce6f29`, `0b110b51`, `319a1ec0`,
`737b971b`; diff `+490/-48`, ~+500 lines per the item): `ffce6f29`
relation-ordering expansion at the offset guard plus hook-failure
masking, `0b110b51` both sides of the conditional ordering
predicate, `319a1ec0` named-expression certification,
`737b971b` ordering-term-by-resolved-form. The hook-failure masking
half has zero bytes here (no `execute`/`execute_sync` override, no
`mask_execution_result` import, no `GraphQLError`-floor builder in
this file; probe `schema-absent-*` holds from the other side too):
from this side the whole delta is the offset-guard classifier. The
guard entry itself
(`list_field.py::_check_nonzero_offset_guard`,
`list_field.py::_order_normalization_scope`, both pipelines, the
factory) is byte-identical; only what the guard classifies moved.

Baselines: `HEAD` is `bfaee91d`; `ITEM_BASELINE`
`8b606af372bdb87d71dc0250f55404935a6a3cce` exists and
`git diff <baseline> -- django_strawberry_framework/list_field.py`
is empty (0 bytes, probe `item-diff-empty`); `git diff HEAD --`
the same path is empty; `git rev-parse
HEAD:django_strawberry_framework/list_field.py` is `ce682d5f…`,
equal to the worktree hash: target clean, no hunk attribution
owed. The plan's `## Owned changes` ledger carries no row on this
path (six rows: walker/test companions plus three gate-only test
pins, all read in full): confirmed, nothing on this path.
Concurrent dirt (notably `connection.py` working `3c4d5dcb…` vs
`HEAD` `93e998f2…`, a cursor-guard hunk touching none of the
fingerprinted sites) left untouched; connection read
working-tree-incl.-hunk for the mirroring pass, traced never
judged, exactly as the prior pass.

### Enumeration reconciliation (fresh instrument at the new bytes)

Instrument as before: `ast.parse` over the worktree blob,
counting `ast.Module.body` members: **79 top-level statements
(delta +16)**. No member removed. Added: 4 import statements
(`django.core.exceptions::FieldDoesNotExist`, the
`related_lookups`, `functions`, and `lookups` vocabularies; the
`expressions` line is CHANGED in place from `Col, Star` to the
7-name form); 6 constants
(`list_field.py::_TRANSPARENT_ORDER_EXPRESSIONS`,
`list_field.py::_APPROVED_ORDER_FUNCTIONS`,
`list_field.py::_APPROVED_ORDER_AGGREGATES`,
`list_field.py::_APPROVED_ORDER_TRANSFORMS`,
`list_field.py::_APPROVED_ORDER_LOOKUPS`,
`list_field.py::_APPROVED_ORDER_NODES`); 6 functions
(`list_field.py::_resolve_order_field_path`,
`list_field.py::_is_deterministic_order_field_path`,
`list_field.py::_is_deterministic_order_reference`,
`list_field.py::_approved_order_transform`,
`list_field.py::_is_deterministic_order_lookup_chain`,
`list_field.py::_is_deterministic_order_predicate_reference`).
Changed: `list_field.py::_is_deterministic_order_name`,
`list_field.py::_is_deterministic_order_term`,
`list_field.py::_is_deterministic_order_value`,
`list_field.py::_is_deterministic_order_condition` (each gains
the `opts`/`seen`/`prefix` expansion scope and a rewritten body);
`list_field.py::_READABLE_ORDER_LEAVES` (tuple to frozenset plus
the exact-type docstring). Functions 28 to 34 (+6, all named);
async count stays 3; classes stay 2 with identical members.
Mapping vs the prior rows 0-62: rows 0-7 unchanged; old row 8-10
shift for the new import + expanded expression line; rows for
`__all__` through `_synthesized_list_signature` unchanged;
old rows 35-38 (`_ORDER_FROM_*`) unchanged; `_READABLE_ORDER_LEAVES`
changed; `_ORDER_VALUE_CONTAINERS` unchanged; the four
classifier rows changed; all rows from
`list_field.py::_selected_ordering` through
`list_field.py::DjangoListField` unchanged. Every prior home
(F1-F6, R1-R10, J1-J4) is re-confirmed below; the delta lives
entirely inside R7 plus two new rejections (J5, J6).

### Matrix re-discharge (against the real new surface)

**1. Cross-flavor policy mirroring.** List vs connection first,
per brief, at the new bytes. Both flavors still compose the same
seams by name (`utils/querysets.py::prepared_resolver_source`,
`utils/querysets.py::apply_type_visibility_sync`/`_async`,
`utils/querysets.py::base_queryset`,
`list_field.py::_validate_relay_djangotype_target` defined here,
consumed by connection and relay). New question: does the
ordering-term resolution duplicate `connection.py`'s
`connection.py::_resolve_order_path_field` /
`utils/querysets.py` path resolution or compose them by name.
It does neither: this file defines its own
`list_field.py::_resolve_order_field_path` and imports none of
the neighbours (probe `no-import-classify_path`,
`no-import-conn-resolver`, `no-import-prefetch-target` all hold;
each neighbour still defined exactly once at its owner). The
considered shared forms are refused as J5 (path walkers) and J6
(spelling grammar), each re-challenged fresh below with per-change
counts. The prior four refusals J1-J4 retrigger-checked, unfired.
No list/mutation/form/rest surface defines its own target
validator, wire-name reader, normalizer, deterministic classifier,
or offset guard.

**2. Sync/async twins.** The three colored pairs are unchanged
and re-compared by behavior (applier twins, pipeline twins,
factory `_wrap` branches): differences remain color duties only
(await point, refusal class, per-color guard, adapter tail).
The classifier delta adds no color: every new and changed
classifier is pure sync code called identically from both
pipelines through the shared scope/guard (`_order_normalization_scope`
3 hits, `_check_nonzero_offset_guard` 3 hits, probe-verified).

**3. Derived rather than repeated knowledge.** The five prior
derivations hold (captured model/sidecar, `base_queryset` seed,
policy/bound ceilings, `order_input_type` annotation,
published-map wire names). New facts are owned, not restated:
the approved-form sets are the classifier's own boundary (J5/J6
record why they are not the neighbours'); the `opts`/`seen`/
`prefix` scope is threaded, never rebuilt from `_meta` at a
second site.

**4. Inverse / round-trip pairs.** Unchanged: the
`ListArgumentError` pickle contract and the async-adapter wrap
with no second grammar here. No new pair.

**5. Contracts restated in another medium.** Production (target);
oracles spelling literals directly: `tests/test_list_field.py`
(76 test functions at the new bytes; 10 new classifier rows plus
the parametrize, all read) plus the live tier
(`test_list_field_api.py` +15 rows, `test_list_field_async_api.py`
+10 rows, both verdicts per branch, heads plus key bodies read);
projections (module/class/function docstrings plus spec-050
Decision 6, read at the new bytes: the string-vs-reference rule,
the approved-form list, and the two-sided predicate rule are all
stated there). Every oracle spells its expectation independently
(reason strings, wire spellings, row SQL absence, `OFFSET 1`
presence) and would fail, not follow, a classifier change. The
per-branch accept+reject pins are enumerated under Findings; a
guard branch with only acceptance pins would be half-proved, and
no branch here is.

**6. Enforcement by omission.** Member-by-member at the new
bytes. (a) Offset guard: every list-field member that can
receive `offset` runs it. `_default` and both `_wrap` branches
normalize through `list_field.py::_argument_record`; queryset
sources flow into `list_field.py::_execute_queryset_pipeline_sync`/
`_async`, which call `list_field.py::_check_nonzero_offset_guard`
after OrderSet inside the shared scope; non-queryset sources with
arguments flow into
`list_field.py::_build_non_queryset_rejection_error` (sync) or
`list_field.py::_handle_non_queryset_rejections_async` (async),
which reject `order_by_supplied` (`queryset_required`) and
positive `offset` (`order_required`) on the same wire names; the
no-argument fast path carries no offset so the guard returns
early by construction. No member accepts a positive offset
without the guard. (b) Post-OrderSet seal asymmetry (D3):
re-derived fresh, still 3/3 here vs 0/0 in connection with 1
`apply_sync(` + 1 `apply_async(` each; ambiguous scope unchanged,
already routed to the maintainer, no verdict here (F4). (c)
`one-sync-boundary`: 0 hits here (probe); the file runs no
consumer hook in a worker, inapplicable by construction.
(d) Raw-body source: no body read here, inapplicable by
construction. No member lacks a guard its contract requires
beyond the already-routed D3.

### Challenges

C1-C20 re-verified at the new bytes (import/absence censuses,
twin scope/guard sharing, seal asymmetry, consumer roles intact;
counts stand: 1 at each owner, 0 here). New challenges posit the
brief's three axes plus the four family re-challenges; the count
is authoritative definitions only, consumers/oracles/projections
listed never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C21 | relation expansion | a new relation shape must expand (e.g. GFK path) | **1** (`list_field.py::_is_deterministic_order_field_path` + `list_field.py::_resolve_order_field_path` move together; connection/relations/prefetch untouched) | file-local (R7) |
| C22 | predicate lookup side | a new conditional predicate shape must read (e.g. `__hashtable` lookup) | **1** (`list_field.py::_is_deterministic_order_predicate_reference` + `list_field.py::_is_deterministic_order_lookup_chain` move together) | file-local (R7) |
| C23 | named-expression form | a new ordering form must certify (e.g. `TruncSecond`) | **1** (the `_APPROVED_*` set holding its kind; the term dispatch follows) | file-local (R7) |
| C24 | resolved-form dispatch | a new reference kind must dispatch (e.g. third reference form) | **1** (`list_field.py::_is_deterministic_order_term` dispatch arms) | file-local (R7) |
| C25 | ordering terms (schema side) | a new ordering-term kind must classify | **0 here for schema.py, 1 HERE** (this file owns the classifier; schema.py holds zero bytes, confirmed from this side) | file-local (R7) |
| C26 | hostile cursor string | a forged cursor must stay out of the offset classifier | **0** (no cursor vocabulary here: `from_base64`/`CURSOR_PREFIX`/`SliceMetadata` absent; the connection keyset path is a different contract, J1 stands) | inapplicable |
| C27 | `orm-lookup-path-resolution` | a new path segment kind must resolve | **1** at `utils/relations.py::classify_path` (this file's walker follows, unchanged) | rejected (J5) |
| C28 | `lookup-name-spelling-grammar` | a new lookup spelling must render | **1** at `filters/inputs.py::LOOKUP_NAME_MAP` (this file matches lookup CLASSES, never spellings) | rejected (J6) |
| C29 | `one-sync-boundary` | the classifier must run a hook in a worker | **0** (no such surface; probe absences) | inapplicable |
| C30 | `typed-rejection-value-tail` | a new hostile value kind must render safely | **1** (`exceptions.py::describe_value` owner; this file's six render sites follow) | consumer (F6) |

Probe: `uv run python
docs/dry/temp-tests/dry-file-list_field/probe_w1_retrace.py` to
`ALL OK` (96 checks). Two `ruff --fix` applications touched the
probe only (scratch); the probe re-ran green afterwards.
Substance unaffected. `execution-verified` for every
identity/count/shape/absence/oracle-presence claim above. No
source mutation, no DB, no shared-tree pytest: inspection beats
execution here (the classifier is pure sync logic over sealed
query state; every DB-reaching path is exercised by the cited
oracles, whose bodies are `static-reviewed`). Rejects "a second
definition lives here", "the target drifted from its baseline",
"the connection seals too", "schema.py classifies orderings".

### Findings

F1 (`awaitable-refusal-and-disposal`), F2
(`sealed-execution-queryset`), F3
(`async-only-queryset-row-adapter`), F5
(`queryset-seed-and-model-read`), F6
(`typed-rejection-value-tail`) reused from the plan with
list-side roles re-challenged fresh at the new bytes (C1-C4,
C6-C8, C30: 1 each at the owners, zero definitions here); all
stay `open`, no new rows. F4
(`post-set-apply-result-validation`) stays 1-owned-plus-1-absent
ambiguous-routed (C5; D3 re-confirmed present with fresh counts,
not re-homed). R1-R6, R8-R10 stand file-local (bodies
byte-identical; prior challenges stand). R7 expands in place
(C21-C25: 1 owner). J1-J4 stand rejected with triggers unfired.
J5 and J6 are new rejections with differences, triggers, homes.
No new family is named. Every finding carries `bfaee91d`
fingerprints below.

### R7 - deterministic-order classification cluster (expanded file-local record, owner `django_strawberry_framework/list_field.py`)

Thirteen functions plus twelve constants (prior seven-plus-six,
all named under Enumeration) move together as one rule: is the
order Django will compile deterministic for an offset window.
The delta is four trust-boundary branches, each with its wire
input and BOTH verdict oracles (GOAL.md: "a bounded raw list" is
the package guarantee; wire offsets/cursors are untrusted):

- **Relation expansion** (`ffce6f29`).
Wire input: `offset > 0` with a string ordering term (or model
`Meta.ordering` term) ending on a relation. Accept:
`test_holder_offset_accepts_a_relation_default_that_expands_to_a_stable_order`
(relation under a column default pages with `OFFSET 1`),
`test_holder_offset_accepts_a_relation_attname_over_a_random_related_default`
(`branch_id` stays a column order),
`test_holder_offset_accepts_an_expression_reference_to_a_relation`
(three `F` spellings stay column orders); package accepts:
`test_order_term_classifier_reads_a_reverse_relation_target_ordering`
stable half,
`test_order_term_classifier_follows_a_chain_of_relation_defaults`
stable half,
`test_order_reference_classifier_keeps_an_expanded_reference_a_column_order`.
Reject:
`test_holder_offset_rejects_a_relation_default_that_expands_to_a_random_order`
(`order_required`, zero row SQL) plus the async twin;
package rejects: the same two tests' random halves, plus
`test_order_term_classifier_refuses_a_relation_ordering_cycle`
(infinite loop refused) and
`test_order_term_classifier_refuses_a_piece_that_is_not_a_field`
(transform/lookup piece refused). Duplication verdict: composes
nothing, duplicates nothing (J5); C21 counts 1 here per change.
- **Predicate both sides** (`0b110b51`). Wire input: `offset >
0` with a `Case`/`When` conditional ordering. Accept:
`test_holder_offset_accepts_a_conditional_order_over_a_column_alias_predicate`,
`test_holder_offset_accepts_a_conditional_order_over_a_plain_column_predicate`;
package accepts:
`test_order_predicate_classifier_reads_the_annotation_under_a_transform_chain`
readable-alias half. Reject:
`test_holder_offset_rejects_a_conditional_order_over_a_random_predicate`
(alias and annotate spellings, zero row SQL) plus the async
twin; package rejects:
`test_order_predicate_classifier_refuses_an_unresolvable_reference`.
Duplication verdict: own rule (J5/J6); C22 counts 1 here.
- **Named-expression certification** (`319a1ec0`). Wire input:
`offset > 0` with an expression ordering term or a predicate
chain link. Accept:
`test_holder_offset_reads_an_expression_by_its_approved_form`
controls,
`test_holder_offset_accepts_a_predicate_chain_of_approved_forms`,
`test_holder_offset_accepts_a_predicate_chain_ending_in_a_transform`,
`test_holder_offset_reads_a_predicate_nested_inside_a_predicate`;
package accepts:
`test_order_term_classifier_admits_only_named_forms` approved
rows (function, aggregate, row-count, reference, predicate).
Reject:
`test_holder_offset_rejects_a_predicate_chain_of_project_sql`,
`test_holder_offset_refuses_a_reference_naming_an_extra_select_alias`;
package rejects: the parametrize's subclass/unapproved/window
rows. Duplication verdict: own boundary (J5); C23 counts 1 here.
- **Resolved-form dispatch** (`737b971b`). Wire input:
`offset > 0` with an `F`/`Q` subclass or a `str` carrying
`resolve_expression`. Accept+reject in one parametrize:
`test_order_term_classifier_admits_only_named_forms`
(`reference` vs `subclass-of-reference`, `predicate` vs
`subclass-of-predicate`, `name-that-resolves` refused) and the
live pair
`test_holder_offset_reads_a_term_by_the_form_it_resolves_into` /
`test_holder_offset_reads_a_conditional_predicate_by_its_exact_type`
(both colors for the latter). Duplication verdict: own dispatch
(J5); C24 counts 1 here. C26 (hostile cursor string) counts 0
here: no cursor vocabulary in this file.

Trigger: a new volatile leaf, a compiler-precedence change, a
new relation/predicate/expression shape, or a new reference kind
moves this cluster alone. Freshness: target `ce682d5f…` +
`tests/test_list_field.py` `2f77f77d…` + live sync
`dd75f921…` + live async `49e423ea…` + spec-050
`f07c7f3d…` (Decision 6 at the new bytes) +
`orders/sets.py` `6044ab1a…` (capture/attestation consumer seam,
unchanged) + owner-adjacent `utils/relations.py` `7662b0bb…` +
`connection.py` working `3c4d5dcb…`/`HEAD` `93e998f2…` (census
only; the hunk touches none of these sites).

### J5 - order-field path walkers (rejection, not a family)

`list_field.py::_resolve_order_field_path` (walk `opts` pieces
via `get_field` with `pk` alias; a non-field piece is a
transform/lookup this package does not read: `None`; returns the
terminal `(field, related opts)` for the expansion to classify)
vs `connection.py::_resolve_order_path_field` (walk `__` pieces
to a terminal concrete non-relation column with
nullable/reverse/multi guards for cursor anchoring) vs
`utils/relations.py::classify_path` (strict plan with hops,
`path_infos` traversal, typed `PathResolutionError`) vs
`utils/querysets.py::_prefetch_relation_target_or_none` (walk to
the terminal relation MODEL, fail-open `None`, accessor-map
fallback). Considered shared form: one `_meta` path walker.
Contract differences: different subjects (ordering-term
certification vs cursor-column anchoring vs relation plan vs
prefetch target), different failures (refuse vs keyset contract
error vs typed path error vs fail-open `None`), different
separator/terminal rules (`LOOKUP_SEP` field-or-`None` vs `__`
column-only vs plan hops vs model-or-`None`). A change to one
terminal rule (e.g. the keyset nullability guard) moves exactly
one body (C27 counts 1 at the relations owner for its axis; C21
counts 1 here for expansion). Reconsideration trigger: a caller
needing another walker's answer (e.g. the guard anchoring
cursors). Durable home: this finding (a file item lands no
edit); the family item for `orm-lookup-path-resolution` owns the
full sweep.

### J6 - lookup spelling grammar vs lookup-class identity (rejection, not a family)

`filters/inputs.py::LOOKUP_NAME_MAP` (Django lookup to GraphQL
spelling grammar) vs
`list_field.py::_is_deterministic_order_lookup_chain` /
`list_field.py::_approved_order_transform` (resolve each trailing
piece via `get_transform`/`get_lookup` and match the resulting
CLASS by exact type against `_APPROVED_ORDER_TRANSFORMS` /
`_APPROVED_ORDER_LOOKUPS`). Considered shared form: one lookup
vocabulary. Contract difference: spelling production vs
class-identity certification; a new lookup spelling moves the map
(C28 counts 1 there), a new certifiable class moves the sets
(C23 counts 1 here); neither follows the other. Reconsideration
trigger: the guard ever certifying by spelling. Durable home:
this finding.

### C25 confirmation from this side (schema.py zero bytes)

The schema.py re-trace verified the ordering-expansion half has
zero bytes in `schema.py` and C25 lives here. Confirmed from
this side: `schema.py` at `bfaee91d` (`c2e1b748…`) contains none
of `_resolve_order_field_path`, `_is_deterministic_order_*`,
`_APPROVED_ORDER_*`, `_TRANSPARENT_ORDER_*`,
`find_ordering_name`, `resolve_ref` (probe re-swept, all absent);
the `ffce6f29` stat puts the ordering lines in this file and
masking-only lines there; this file carries the 6+6+4
ordering-machinery members as its C25 home. C25 counts 0 for
`schema.py`, 1 here.

### Defects

None. Every claim checked while tracing held: the 79/34/2
counts; the six-plus-six additions named; the four changed
signatures; the frozenset boundary; the exact-type dispatch with
both old `isinstance` forms gone; the guard/scope/pipeline entry
stability; the four non-imports; the neighbour single-sites; the
schema absences; the D3 asymmetry re-derived fresh; the
per-branch both-verdict oracle presence (names probed green,
bodies `static-reviewed`); the `## Owned changes` emptiness on
this path; the baseline diff emptiness. The one known
list-adjacent row keeps its existing home: D3 (connection runs
`OrderSet.apply_*` with no post-apply seal: ambiguous, already
routed to the maintainer, re-confirmed present, not re-homed). No new
defect is routed to any owner. Bugs found while tracing would go
here UNFIXED; none were found.

### Pending execution

None. The execution proof (read-only probe driving the AST plus
whole-tree sweeps, command under Challenges) already ran green
against the shared tree; it mutates no source and opens no
database, so no workspace copy was owed and no `__file__`/DB
`NAME` record applies. No pytest was run in the shared tree, per
item rules; oracle bodies are `static-reviewed`, which is the
honest label for a zero-edit item. No `execution-deferred`
items. No `FAKESHOP_SHARDED` or Postgres cell is owed: this
re-trace's claims (statement/function counts, import census,
absence/single-site facts, baseline diffs, call-site and oracle-
presence censuses) touch no database, alias, or dialect decision
(`inapplicable by construction`; the classifier reads sealed
query state, and the DB-reaching paths are exercised by the
cited oracles, not by this probe).

### Judgment

Backstop re-discharged at the new bytes: 79/79
`ast.Module.body` members enumerated, delta reconciled by name
(+4 imports, +6 constants, +6 functions, 4 changed, 0 removed),
matrix re-run against the real new surface, C1-C20 re-verified
plus C21-C30 counted, every rule terminating in one of the six
existing plan families (re-challenged fresh on the list side:
F1/F2/F3/F5 consumer, F6 consumer via C30, F4 stays
ambiguous-routed), the expanded file-local R7 with its proving
challenges, the four standing rejections J1-J4, or two new
rejections with differences plus triggers plus homes (J5, J6):
no consolidation owed, no defect found, no new family named.
Zero-edit result is legitimate.

### Item-scoped diff state

Tracked: none. `git diff
8b606af372bdb87d71dc0250f55404935a6a3cce --
django_strawberry_framework/list_field.py` empty (0 bytes,
probe `item-diff-empty`); `git diff HEAD --stat --
django_strawberry_framework/list_field.py` empty; worktree blob
`ce682d5f…` equals `HEAD:`. `## Owned changes` ledger: nothing
on this path (confirmed). Concurrent dirt left untouched. No
commit. Untracked scratch created by this pass (not tracked
changes): this artifact's new section plus the read-only probe
`docs/dry/temp-tests/dry-file-list_field/probe_w1_retrace.py`
(`ALL OK`, 96 checks; `ruff format` applied to the probe only,
re-ran green; no source mutation, no DB, no shared-tree pytest).
Prior scratch (`probe_w1.py`, `dry-file-list_field-w2/`) left
untouched. Freshness fingerprints (`git hash-object` at
`bfaee91d`): target `ce682d5f79518919ff3676f2fc8bbe2bd33995a4`;
`connection.py` working `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a`
/ `HEAD` `93e998f2c7ea1d7f18607a6e37e394466ac75ad4`;
`schema.py` `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`;
`utils/querysets.py`
`96618fba4eafb6a87e73414770014e3aee5b41ef`;
`utils/relations.py`
`7662b0bb669c4dfba4a437f3b8f309357f718dca`;
`orders/sets.py`
`6044ab1a11c77a42b715f0d0722fe7c9695064bc`;
`exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
`resource_policy.py`
`647133d23785d325856b2d1d495d18c5741dd23c`;
`relay.py`
`c3c5aea52768cbdb3a849c5944cb4b2245db5fde`;
`registry.py`
`9cc8bb553fd417fc465809a541769a8383469cda`;
`utils/directives.py`
`380786cf7b3213603a592717cc65386892d7bf50`;
`utils/execution_mode.py`
`9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`;
`utils/typing.py`
`de6309f6cb5915e9f42d0e19f564f4e67226e334`;
root `__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`tests/test_list_field.py`
`2f77f77d67366373390458c681e33fd59cf42c92`;
live sync `dd75f921d4796ffd54f8b5212a91353646186c58`;
live async `49e423ea593b8883c4c07593accd822390e82468`;
spec-050 `f07c7f3dd4dc73f7f9e5b1fae0033e2c3c5c95fa`.
`Status: ready-for-verification/1`.

## Re-trace verification at bfaee91d (Worker 2)

Run `0.0.15 2026-09-19-1`. HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
Method note: the required order puts the artifact after the target, and I
read the full artifact (including the W1 re-trace) before running my own
instruments — so this section re-derives every count, sweep, and oracle
below with independent commands rather than inheriting W1's numbers, and
reconciles each difference explicitly.

### Own trace (independent instruments)

`ast.parse` over the worktree blob, my own enumeration: **79
`ast.Module.body` members (indices 0-78)** — 1 module docstring, 26 import
statements (indices 1-26: 17 std/third-party incl. the 4 new Django
vocabularies `FieldDoesNotExist`, `related_lookups`, `functions`,
`lookups`, plus the 9 unchanged local imports), 1 `TYPE_CHECKING` guard,
`__all__`, 12 constants, 34 functions (31 `def` + 3 `async def`:
`_handle_non_queryset_rejections_async`, `_apply_orderset_async`,
`_execute_queryset_pipeline_async`), 2 classes (`ListArgumentError`
`__init__` + `__reduce__`, `_ListArguments` 5 fields). Constants:
4 `_ORDER_FROM_*` (unchanged) + `_READABLE_ORDER_LEAVES` (changed
tuple-to-frozenset) + `_TRANSPARENT_ORDER_EXPRESSIONS` (new) +
`_APPROVED_ORDER_FUNCTIONS`/`_AGGREGATES`/`_TRANSFORMS`/`_LOOKUPS` (new) +
`_APPROVED_ORDER_NODES` (new union) + `_ORDER_VALUE_CONTAINERS`
(unchanged) = 12. New functions (6): `_resolve_order_field_path`,
`_is_deterministic_order_field_path`, `_is_deterministic_order_reference`,
`_approved_order_transform`, `_is_deterministic_order_lookup_chain`,
`_is_deterministic_order_predicate_reference`. Changed (4):
`_is_deterministic_order_name`/`_term`/`_value`/`_condition` (each gains
`opts`/`seen`/`prefix`). 0 removed.

Guard-cluster sites + roles (mine): the 6 `_APPROVED_*`/`_TRANSPARENT_*`
tables plus `_READABLE_ORDER_LEAVES` plus 13 classifier functions are ONE
definition owned by `django_strawberry_framework/list_field.py` — the
certification rule "is the order Django will compile deterministic for an
offset window". Sibling sweep for a second certification list: all 21
`_APPROVED_ORDER|_TRANSPARENT_ORDER|_READABLE_ORDER|_ORDER_VALUE_CONTAINERS`
hits in the package sit in this one file; `orders/` holds no order-function
allow-list (only frozenset canonicalization plus
`orders/factories.py::_RESERVED_FACTORY_KEYS`); `connection.py` holds no
deterministic classifier and no offset guard (its offset vocabulary is
cursor/pagination math); `filters/inputs.py::LOOKUP_NAME_MAP` is spelling
production, not certification, and the concurrent worktree hunk there
touches `_normalize_range_value` only (no `LOOKUP_NAME_MAP` line in
`git diff HEAD -- filters/inputs.py`). No-import edges confirmed from this
side: `list_field.py` references none of `classify_path`,
`_prefetch_relation_target_or_none`, `connection.py::_resolve_order_path_field`,
or `LOOKUP_NAME_MAP` (only Django's own field APIs `get_transform`/
`get_lookup` plus the local `order_input_type` import). Owners I would
choose: classifier cluster here; disposal/seal/adapter/seed/rejection-tail
at `utils/querysets.py` / `exceptions.py` with this file consumer-only;
post-apply seal asymmetry routed, not consolidated. No new family named.

### Enumeration vs W1

Agree: 79 members, delta +16 reconciled by name (4 imports + 6 constants +
6 functions, 0 removed, 4 changed + `_READABLE_ORDER_LEAVES` changed).
Precision addendum (non-verdict): W1's "Functions 28 to 34" reads as 34
total (31 sync + 3 async) under my parse; prior 28 + 6 = 34 holds.

### J5 re-judged HARD: concur, distinct-contracts, no candidate

Four walkers, each read at its body: `list_field.py::_resolve_order_field_path`
(`LOOKUP_SEP` pieces via `opts.get_field`, `pk` alias, non-field piece
yields `None`, returns terminal `(field, related opts)` for expansion
classification — subject: ordering-term certification, failure: refuse);
`connection.py::_resolve_order_path_field` (`__` pieces via
`model._meta.get_field`, `pk` alias, nullable/reverse/multi guards,
terminal must be concrete non-relation column — subject: cursor anchoring,
failure: `None` → keyset contract error); `utils/relations.py::classify_path`
(strict plan, hops, `path_infos` traversal, typed `PathResolutionError` —
subject: relation plan); `utils/querysets.py::_prefetch_relation_target_or_none`
(walk to terminal MODEL, fail-open `None` — subject: prefetch target).
Change challenge applied myself: a new relation-hop form (e.g. GFK) reaches
each walker and each answers per its own contract (refuse / cannot-anchor /
typed path error / skip-prefetch) — one shared walker would need
terminal-rule + failure-mode flags, a principle-5 mode-flag violation, to
reproduce four behaviors the loop text (~10 lines of Django idiom) does not
share. Keeping four walkers is correct. No consolidation candidate exists,
so nothing routes anywhere; the holding family for the rule remains
`orm-lookup-path-resolution` (plan index: owner
`utils/relations.py::classify_path`, status `open`), which owns the full
sweep. J6 concurred on the same basis (C28 moves the map, C23 moves the
sets; neither follows the other).

### Oracle spot-check (accept + reject, independence + tier)

Reject (live, HTTP via `Client` test mount through `_post_sync`):
`test_holder_offset_rejects_a_relation_default_that_expands_to_a_random_order`
spells literals `reason == "order_required"`, `argument == "offset"`,
`shelf_sql == []` — fails if the classifier ever certifies the random
expansion; reads no owner table. Accept (live):
`test_holder_offset_accepts_a_relation_default_that_expands_to_a_stable_order`
spells row literal `"Bravo-1"`, `"OFFSET 1" in statement`,
`_RANDOM_ORDER_SQL not in statement`. Package pins:
`test_order_term_classifier_refuses_a_relation_ordering_cycle`
(`is False` against monkeypatched `Meta.ordering` literals) and the
reverse-relation stable/random halves (`is False` / `is True`).
Tier-correct: the guard is wire-reachable (`offset` + `orderBy` over HTTP),
so AGENTS.md mandates live pins — present (sync + async suites) alongside
the 76 package functions (count re-derived by my own grep: 76). Bodies
`static-reviewed`, which is the honest label for a zero-edit item.

### F4 judgment: "ambiguous-routed" is sound

Meaning: 1 owned definition (the querysets seal, enforced at this file's
applier twins — both bodies read: freeze via `_snapshot_routing_intent`
before the override, `_validate_post_orderset_result` after) + 1 absent
member (connection's `apply_sync`/`apply_async` call sites, 1 each,
re-counted — with 0 seal + 0 snapshot, re-counted). Ambiguous because both
contract sources scope the rule to the list field while the connection also
windows what comes back; under DRY.md axis 6 that ambiguity routes to the maintainer
(D3, already homed by the querysets item), never a local verdict. Sound.

### Proof adequacy: `## Pending execution` empty, concur

The DRY verdict (definition counts, single-sites, absences) needs no
execution and the read-only probe shape is the right instrument; I
re-derived its substance with independent commands instead of re-running
W1's scratch. The guard's *behavioral* proof rests on the existing oracles
above (package 76 + live sync/async suites), which the final gate executes
— precisely: the gate's `uv run pytest` run covering
`tests/test_list_field.py`,
`examples/fakeshop/test_query/test_list_field_api.py`, and
`examples/fakeshop/test_query/test_list_field_async_api.py`. No
`execution-deferred` item exists, so no `proof:` entry is owed; sharded/PG
cells inapplicable by construction (no DB, alias, or dialect decision in
any counted claim). Static review + gate-executed oracles is adequate;
nothing is deferred silently.

### Per-claim agreement / difference

Enumeration 79 (+16: 4 imports + 6 consts + 6 fns; 4 changed;
`_READABLE_ORDER_LEAVES` tuple-to-frozenset; 0 removed): agree, reconciled
by name. 0 new families: agree (sibling sweep clean). F1/F2/F3/F5/F6
consumer, F4 ambiguous-routed: agree (seal asymmetry re-counted fresh:
connection 0/0 with 1+1 apply sites). J5/J6 rejections: concur with
reasons re-derived above, not inherited. R7 expanded file-local (13 fns +
12 consts; four guard branches each with wire input + accept AND reject
oracles): agree — every cited oracle name resolved to a real `def` at its
file (live relation/predicate/expression/dispatch rows plus package
classifier halves). C25 here / 0 schema: agree (schema absences re-swept
by W1; `ffce6f29` stat direction consistent with this file carrying the
machinery). R1-R6/R8-R10 + J1-J4 stand: agree (bodies outside the delta
byte-identical per the empty diff; twin scope/guard sharing re-verified by
my grep of both pipelines). No defects: agree. Zero production edits:
agree (item diff empty, re-measured below).

### Freshness re-hashed at bfaee91d (mine, `git hash-object`)

Target `ce682d5f79518919ff3676f2fc8bbe2bd33995a4` (== `HEAD:` — clean);
`connection.py` work `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a`;
`schema.py` `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`;
`utils/querysets.py` `96618fba4eafb6a87e73414770014e3aee5b41ef`;
`utils/relations.py` `7662b0bb669c4dfba4a437f3b8f309357f718dca`;
`orders/sets.py` `6044ab1a11c77a42b715f0d0722fe7c9695064bc`;
`exceptions.py` `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
`resource_policy.py` `647133d23785d325856b2d1d495d18c5741dd23c`;
`relay.py` `c3c5aea52768cbdb3a849c5944cb4b2245db5fde`;
`registry.py` `9cc8bb553fd417fc465809a541769a8383469cda`;
`utils/directives.py` `380786cf7b3213603a592717cc65386892d7bf50`;
`utils/execution_mode.py` `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9`;
`utils/typing.py` `de6309f6cb5915e9f42d0e19f564f4e67226e334`;
root `0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`tests/test_list_field.py`
`2f77f77d67366373390458c681e33fd59cf42c92`; live sync
`dd75f921d4796ffd54f8b5212a91353646186c58`; live async
`49e423ea593b8883c4c07593accd822390e82468`; spec-050
`f07c7f3dd4dc73f7f9e5b1fae0033e2c3c5c95fa` — all match W1. Addition:
`filters/inputs.py` worktree `06797dc7db04e4fc78cfbc478094ecada273c533`
(concurrent hunk; `LOOKUP_NAME_MAP` untouched). Item-scoped diff
`git diff 8b606af372bdb87d71dc0250f55404935a6a3cce --
django_strawberry_framework/list_field.py` empty (re-measured); `git diff
HEAD --` same path empty.

### AGENTS.md prose on the empty diff

Tracked diff empty → no production edits → no test-tier, format, or commit
obligations fire (no ruff run owed: the only touched path is this `.md`
artifact plus no scratch created by me). Artifact prose: no `path:NN`
citations (swept the W1 re-trace range, zero hits), `path::Symbol`
throughout, no process provenance, concurrent dirt untouched, no commit.
The empty diff is not an omission — for a file item whose every rule
terminates in an existing family or a file-local record with its proving
challenge, zero edits is the legitimate result per DRY.md.

## Defects

None. (Worker 2) None — every independently re-derived claim held; the one
known list-adjacent row stays D3, already routed to the maintainer, not re-homed.

**Verdict.** `Status: verified`, no pending execution. Backstop
re-discharged at `bfaee91d`: 79/79 members enumerated by an independent
parse, delta reconciled by name, matrix re-run against the real new
surface, every rule homed, J5 concurred distinct-contracts with its
holding family named, oracles spot-checked accept + reject at the
wire-correct tier, F4 routing sound, freshness re-hashed, empty diff
legitimate.

## Scoped re-trace (run 7) — Worker 1

Scoped run: `0.0.15 2026-09-28-7`. HEAD `0c0537e2` at start,
verified unmoved at finish. Prior text above is prior evidence only
and stands untouched; this section appends. Zero production edits; a
file item owes none.

### Scope of the delta (drift base → HEAD → worktree)

Drift base `5ee86193` blob == HEAD blob `21380eb7` (nil
`5ee86193`→HEAD delta; the range diff on the target is empty). The
recorded drift — the OrderSet applier twins deleted in favour of
`utils/querysets.py::apply_orderset_sync` /
`::apply_orderset_async` — landed before the drift base. Against the
prior trace (`bfaee91d`, blob `ce682d5f`) the target delta is exactly
that move, 7 hunks, 10+/88-: `list_field.py::_require_orderset_class`
plus `list_field.py::_apply_orderset_sync` /
`list_field.py::_apply_orderset_async` deleted (78 lines); the
querysets import drops `SyncMisuseError`,
`_dispose_sync_awaitable`, `_snapshot_routing_intent`,
`_validate_post_orderset_result` and gains the two shared appliers;
the exceptions import drops `_safe_type_name` (its two uses lived in
the deleted async twin); both pipeline call sites and two docstring
pointers re-point to the querysets owners. Every byte outside those
hunks is identical to the bytes the prior trace adjudicated.

HEAD → worktree is 42 hunks (`-U0`), 82+/136-, worktree blob
`f5b0183e`. Hunk attribution by content: ONE owned hunk, the ledger's
adopted orphan `relay-node-target-guard` rejection-trigger docstring
on `list_field.py::_validate_relay_djangotype_target` (pure additive,
+8); the other 41 are concurrent-external and untouched — 29
`utils/truth.py`-migration code and prose hunks (safe-helper renders
to `truth.*`, contained reads to `truth.static_attr` /
`truth.is_subclass`, `vars(self)` / `type(self)` in `__reduce__`),
4 wire-name defensive-`try` removals, 3 `Count`-aggregate docstring
hunks, 1 Relay-node-factory docstring widening, 1 pk-tiebreaker
docstring, 3 comment touch-ups (synthesizer trim, `spec-050`
prefix, `spec-020` number fix). None touches the deleted twins'
region, the pipelines' applier call sites, or the O1 spelling.

Enumeration at HEAD bytes (`ast.Module.body` over `git show`
bytes): **76 members** (was 79; exactly the 3 deleted functions,
zero other changes) — 31 functions (29 `def` + 2 `async def`; the
async twin `_apply_orderset_async` is the third deletion),
2 classes with identical members (`ListArgumentError`
`__init__` + `__reduce__`, `_ListArguments` 5 fields), exceptions
import 6→5 names, resource_policy import still 7. Worktree counts
77 (+1 `truth` import statement; named members identical).

### Matrix re-discharge (at HEAD bytes)

**1. Cross-flavor policy mirroring.** Both flavors now enter the ONE
post-sidecar seal: `connection.py` imports and calls the shared
`apply_orderset_sync` / `apply_orderset_async` (plus the
`apply_filterset_*` pair), as this file's pipelines do. The seal
asymmetry is gone (F4). The genuine second-site shapes from the prior
pass re-check clean: signature synthesizers (J3), validating readers
vs captured reads (J2), deterministic predicates vs keyset
anchorability (J1) — all premises re-read at HEAD, all refused
again. New: the supplied-spelling at `list_field.py::_normalize_list_arguments`
(`x is not None and x is not strawberry.UNSET`, ×3) is the exact
inverse of the package's one active-input rule while every connection
surface already composes `utils/connections.py::is_supplied` (O1,
F-NEW below).

**2. Sync/async twins.** Two colored pairs remain (was three): the
pipeline twins and the factory `_wrap` branches, both byte-identical
outside the two re-pointed applier calls; differences stay color
duties only (awaited visibility step, per-color guard, adapter
tail). The deleted applier twins' duties (freeze, dispose,
refuse-by-color, seal) now live once in
`utils/querysets.py::_apply_sidecar_sync` / `_async`, read at HEAD:
bodies carry the freeze-before-override comment, the
`SyncMisuseError` vs `ConfigurationError` refusal split, and the
`_SIDECAR_RESULT_POLICY` seal verbatim.

**3. Derived rather than repeated knowledge.** The five prior
derivations hold (captured model/sidecar, `base_queryset` seed,
policy/bound ceilings, `order_input_type` annotation, published-map
wire names). New: the supplied-spelling derives nothing — it
re-states the active-input rule instead of composing it (F-NEW). The
`require_orderset_class` reword (`DjangoListField target` → `Field
target`) confirms the guard is flavor-shared, not list-flavored.

**4. Inverse / round-trip pairs.** Unchanged: the
`ListArgumentError` pickle contract and the async-adapter wrap, no
second grammar here.

**5. Contracts restated in another medium.** Oracles at HEAD:
`tests/test_list_field.py` still 76 test functions (one marker-only
hunk since the drift base), spelling literals directly; the
orderset-gate oracle now imports `require_orderset_class` from its
querysets owner and pins the new `Field target ...` message (name
unchanged, body re-pointed — no staleness); live sync suite +122/-6
to 99 test functions (additive combined-source rows), live async
suite byte-identical to the drift base. `spec-050` rewords
post-`OrderSet` to post-sidecar consistently with the move.

**6. Enforcement by omission.** (a) Post-apply seal: both flavors
seal via the shared appliers — D3 RESOLVED-fixed per the verified
File `utils/querysets.py` run-7 outcome (the `_SealPolicy` prose now
states the rule for "the list field and the Relay connection
alike"); no absent member remains. (b) `one-sync-boundary`: 0 hits
here, inapplicable by construction. (c) Raw-body source: no body
read here, inapplicable by construction.

### Challenges

C1–C4, C6–C20 re-verified at HEAD bytes (counts stand: 1 at each
owner, 0 here). C5 is superseded by C-O1's family below and the F4
revise. New:

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C-O1 | supplied spelling | a third inactive spelling ships (or the sentinel binding moves) | **2** (`utils/input_values.py::is_inactive_value`, 1; this file's ×3 hand-spelling, 1 — one function, moves together) | candidate (F-NEW) |

Whole-package census at HEAD: the hand-spelling exists exactly once
outside a docstring (this file); `is_supplied` is defined exactly
once; the connections docstring's "15 sites" is history. Every other
`is not None` in this file is a None-only check (no UNSET arm), out
of the rule's contract.

Probe: read-only AST + token census over `git show` bytes, scratch
under `/tmp` only (`/tmp/lf_run7_probe.py`, `ALL OK` 46/46: 76/77
member counts, class members, import censuses, ×3 spelling lines
plus 5 sentinel defaults, applier call sites 1 per color, 10
absences, guard/scope/prepared/policy counts, owned-hunk presence).
No Django import, no SQL, no source mutation, no workspace, no
pytest. `execution-verified` for every identity/count/shape/absence
claim in this section; oracle bodies stay `static-reviewed`, the
honest label for a zero-edit item. Three first-draft expectations
failed on probe precision (async count 3 vs the true 2, UNSET total
3 vs the true 8, call sites 2 vs the true 1 per color) and were
corrected to the HEAD truth, substance unaffected.

### Findings: CONFIRM / REVISE ledger

16 CONFIRM, 6 REVISE. Every prior finding re-checked against HEAD
bytes; revisions carry `b68be0e3→3616927d`-era re-pins where the
owner moved under the verified querysets re-trace.

- F1 (`awaitable-refusal-and-disposal`): REVISE, verdict stands
  (consumer, 0 definitions). The two applier dispose+refuse sites
  moved into the shared `_apply_sidecar_*`; remaining here: the sync
  `_wrap` guard pair, the async `_wrap` guard, the async-rejection
  cleanup. C1/C2 still count 1 at the querysets owner.
- F2 (`sealed-execution-queryset`): REVISE, verdict stands
  (consumer). The applier freeze-then-seal sites moved with the
  twins; the pipelines still consume the visibility seals, and the
  construction-vocabulary sweep still finds zero hits here. C3 still
  counts 1 at the seal.
- F3 (`async-only-queryset-row-adapter`): CONFIRM (untouched; 4
  predicate sites + wrap sites byte-identical).
- F4 (`post-set-apply-result-validation`): REVISE, verdict changes
  to consumer. This file seals via the shared appliers; the
  connection does too; the 1-owned-plus-1-absent asymmetry and D3
  are closed (verified querysets run-7 D3 disposition). C5 is
  retired, superseded by the one-seal composition both flavors
  share.
- F5 (`queryset-seed-and-model-read`): CONFIRM (seed branch,
  `model=` threading, captured reads untouched).
- F6 (`typed-rejection-value-tail`): CONFIRM, re-pinned (all six
  render sites byte-identical; exceptions import 6→5 names with the
  twin-only `_safe_type_name` gone).
- R1–R4: CONFIRM (validators, readers, error vocabulary, wire
  fallback — byte-identical; registry drift is docstring-only).
- R5 (normalized-arguments record): REVISE. The record, the
  exact-`int` gate, the ceiling sources, and the mode decision
  stand; the supplied-computation gains the F-NEW candidate below
  (O1, discharged from routed to named).
- R6: CONFIRM. R7: CONFIRM (13 functions + 12 constants
  byte-identical; C25 re-swept: zero classifier bytes in
  `schema.py` at HEAD).
- R8 (resolver invocation and rejection): REVISE, 6→5 members.
  `list_field.py::_require_orderset_class` is deleted; the
  direct-call gate is owned at
  `utils/querysets.py::require_orderset_class` (same fail-closed
  contract, flavor-shared message), consumed by both appliers. The
  oracle follows the owner. Remainder (label, shape guard, record
  split, sync builder, async handler) byte-identical.
- R9: CONFIRM (guard + scope byte-identical; docstring pointer
  only). R10: REVISE (pipelines compose the shared appliers by
  name; twin structure, step order, no-arg fast paths unchanged).
- J1–J6: CONFIRM, triggers unfired, premises re-read at HEAD:
  keyset anchorability still rejects explicit nulls per entry (J1);
  connection still reads `definition.model` / `.cursor_field` /
  `.connection` / sidecar classes directly off the validated object
  (J2); the connection synthesizer still serves the
  `ConnectionExtension` contract (J3); the mutation guard still
  subjects `_mutation_meta` and the converter label still renders
  `Model.field` (J4); all four path walkers keep their subjects and
  failure modes (J5; relations drift is docstring-only outside
  `classify_path`); `LOOKUP_NAME_MAP` still produces spellings
  while the guard certifies lookup classes (J6).

### F-NEW — `list-argument-supplied-spelling` (candidate for Worker-0; O1 discharged)

- **Contract + variation.** An argument counts supplied unless it is
  `None` or the `UNSET` sentinel — the package's one active-input
  rule. Binding the sentinel varies per layer (traversal primitives
  stay strawberry-free; schema layers bind `strawberry.UNSET`).
- **Sites + roles.** *Definitions*: 2 —
  `utils/input_values.py::is_inactive_value` (the rule, 1) with its
  `utils/connections.py::is_supplied` binding, versus
  `list_field.py::_normalize_list_arguments` :466–468 (the ×3
  hand-spelling, 1). *Consumers*: 20+ `is_inactive_value` sites plus
  the consolidated connection surfaces (per the verified
  input_values artifact). *Oracles*: normalizer supplied-ness rows
  in `tests/test_list_field.py`.
- **Challenges.** C-O1 counts 2. Composing costs the list side one
  import it can already reach (`utils/connections.py` imports only
  lower layers — no cycle) or a direct inverted
  `is_inactive_value` call; the family item decides the spelling
  (`is_supplied`'s docstring currently claims a connection
  argument).
- **Holding.** New family (transcribe 1 row): never homed — outside
  the verified `unset-bindings-across-families` census, and that
  index row is `rejected`, so it is not an adoption target.
  Possible converge with the `input-values-active-rule` file-local
  row is Worker-0's call.
- **Freshness.** Target HEAD `21380eb7` + `utils/connections.py`
  HEAD `f549389e` + `utils/input_values.py` HEAD `f2566609`.

### Defects

None. Every claim checked while tracing held: the 76/31/2 counts;
the 7-hunk drift reconciled by name with zero bytes outside it; the
shared appliers carrying freeze, both refusal classes, disposal,
and the seal; the D3 closure confirmed from both flavors' call
sites; the oracle re-pointed to the owner with the new message; no
stale reference to any deleted name in production, tests, or
examples; the O1 spelling verified verbatim as the sole remaining
hand-spelling. The one known list-adjacent row, D3, is resolved,
not re-homed.

### Pending execution

None. The execution proof is the read-only probe cited under
Challenges (no source mutation, no database, no workspace owed, no
`__file__`/DB record applies). No pytest in the shared tree per
item rules. No `FAKESHOP_SHARDED` or Postgres cell is owed: every
counted claim touches no database, alias, or dialect decision
(inapplicable by construction; DB-reaching paths are exercised by
the cited oracles, whose bodies are `static-reviewed`).

### Item-scoped diff state and fingerprints

Tracked: none — zero production edits, zero test edits. The target's
worktree dirt is 1 owned hunk (ledgered, adopted, never re-verified)
plus 41 concurrent-external hunks, all left untouched; every claim
above is traced at HEAD bytes, never the worktree. `HEAD`
`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62` unmoved (start and
finish). `git diff 5ee86193 HEAD -- <target>` empty (nil drift).

Target fingerprints: drift base
`21380eb72364caef0da05ca3ee3f26c0134e3904` == HEAD
`21380eb72364caef0da05ca3ee3f26c0134e3904`; worktree
`f5b0183e290322952fd2dad1f76ab9b2de9736ba`.

Connected inputs (drift → HEAD → worktree, short ids):
`connection.py` `4894f90f` MATCH `4894f90f` / `1fca6266`;
`utils/querysets.py` `b68be0e3` → `3616927d` / `8fc556d5` (in-range
drift adjudicated by the verified querysets run-7);
`utils/relations.py` `7662b0bb` → `8dbc3fe6` (docstring-only) /
`05ff55b0`; `utils/input_values.py` `f2566609` MATCH / `18992b79`;
`utils/connections.py` `f549389e` MATCH / `efcf749a`;
`exceptions.py` `e06b0b7f` MATCH / `93401220`;
`resource_policy.py` `4b69e974` MATCH / `5b4a80f0`; `relay.py`
`c3c5aea5` MATCH / `f5760b45`; `registry.py` `9cc8bb55` →
`81bd561c` (docstring-only) / `27358cbc`; `utils/directives.py`
`380786cf` MATCH / `84f770d4`; `utils/execution_mode.py`
`9805cdaf` MATCH / `9805cdaf`; `utils/typing.py` `de6309f6` MATCH
/ `a672cd6b`; root `__init__.py` `0ef72601` MATCH / `0ef72601`;
`orders/sets.py` `6044ab1a` MATCH / `60859f2d`;
`filters/inputs.py` `82b52d97` MATCH / `a932dbf8`;
`mutations/fields.py` `cf518361` → `d4edcbb7` (docstring-only) /
`0e4d5ed1`; `types/converters.py` `9ceb34af` → `058f1081`
(docstring-only) / `f6cadb08`; `types/base.py` `91c58747` →
`dda91365` (outside `_is_relay_shaped`) / `dc67f084`; `schema.py`
`19f90bf5` → `e6b52335` (C25 re-swept zero) / `f4e807e9`;
`tests/test_list_field.py` `d3bfa877` → `038e69ce` (marker-only)
 / `d78aa5e7`; live sync `e2ed442c` → `4c85f779` (additive) /
`4c85f779`; live async `49e423ea` MATCH / `49e423ea`; `spec-050`
`0febc4c8` → `73fe1127` (lifecycle + post-sidecar reword) /
`73fe1127`.

### Judgment

Backstop re-discharged at HEAD bytes: 76/76 members enumerated,
drift reconciled by name (7 hunks, exactly the recorded applier
move), matrix re-run against the real current surface, 16 prior
findings CONFIRMed and 6 REVISEd (F1/F2 site lists, F4 to consumer
with D3 closed, R5/R8/R10 for the move), 6 rejections standing
with premises re-read at HEAD, one new count-2 candidate named for
Worker-0 (F-NEW `list-argument-supplied-spelling`, O1 discharged),
no defect found, no consolidation owed by this file item.
Zero-edit result is legitimate.
## Run-7 verification (Worker 2)

Run: 0.0.15 2026-09-28-7. HEAD `0c0537e2` at start,
verified unmoved at finish. Expectation-first with a method note:
the required order puts the artifact after the target, and I read
the full artifact (including the run-7 W1 section) before running my
own instruments — so every count, sweep, and fingerprint below was
re-derived with independent probes rather than inherited, and each
difference is reconciled explicitly. Instruments: three read-only
probes under `/tmp` (`/tmp/lf_w2_part1.py` 30/30,
`/tmp/lf_w2_part2.py` 49/49, `/tmp/lf_w2_part3.py` 81/81 — 160/160
green, all target claims against `git show HEAD:` bytes) plus
read-only `git diff` / `git grep` / `git rev-parse` / `git
hash-object` reads. No Django import, no SQL, no source mutation,
no workspace, no pytest. Three first-draft expectations failed on
probe precision (connection alias-call shape, a test-name substring
match, keyword hunk buckets) and were corrected to the HEAD truth
after reading the bytes; substance unaffected in all three cases.

### Own trace (independent instruments)

`ast.parse` over HEAD bytes, my own enumeration: **76
`ast.Module.body` members** — 31 functions (29 `def` + 2 `async
def`: `_execute_queryset_pipeline_async`,
`_handle_non_queryset_rejections_async`; the third async, the
deleted applier twin, is gone), 2 classes (`ListArgumentError`
`__init__` + `__reduce__`, `_ListArguments` 5 fields), exceptions
import 5 names (no `_safe_type_name`), resource_policy import 7
names, querysets import carrying `apply_orderset_sync` /
`apply_orderset_async` and none of `SyncMisuseError`,
`_dispose_sync_awaitable`, `_snapshot_routing_intent`,
`_validate_post_orderset_result`. Worktree parses to 77 (+1 `truth`
import statement; named members identical). Deletion inventory at
HEAD: no `def _require_orderset_class`, no
`_apply_orderset_sync(`/`_apply_orderset_async` definitions or
calls, no `_snapshot_routing_intent`, no `_dispose_sync_awaitable`,
no `_validate_post_orderset_result`; exactly 2 docstring pointers
to `utils/querysets.py::require_orderset_class` and exactly 1
`apply_orderset_sync(` + 1 `apply_orderset_async(` pipeline call
each. Per-symbol AST comparison PRIOR (`bfaee91d`) → HEAD: removed
exactly the 3 deleted functions, added 0, changed exactly 4 (the 2
pipeline call-site re-points + the 2 docstring re-points) — every
other named symbol byte-identical, so every prior CONFIRM rides on
unchanged bytes, not on recollection.

Owners I would choose (before reconciling): applier duties
(freeze, dispose, refuse-by-color, seal) at
`utils/querysets.py::_apply_sidecar_sync` / `_async` (bodies read:
freeze-before-override comment, `SyncMisuseError` vs
`ConfigurationError` split, `_dispose_sync_awaitable`,
`_SIDECAR_RESULT_POLICY` seal all present); the direct-call gate
at `utils/querysets.py::require_orderset_class` (same fail-closed
contract, `Field target ...` message); disposal, seal, async-only
predicate/adapter, default seed, rejection tail at their querysets
/ exceptions owners with this file consumer-only; validators,
readers, error vocabulary, wire names, arguments record (plus the
O1 candidate below), SDL synthesizer, deterministic cluster,
resolver-invocation remainder, offset guard + scope, pipeline twins
+ factory all here. No new family named by me; one candidate
received (O1) and judged below.

### REVISE reconciliation (all 6, re-derived)

- F1 (`awaitable-refusal-and-disposal`): REVISE concur, verdict
  stands (consumer, 0 definitions). The 2 applier dispose+refuse
  sites are gone with the twins; remaining here re-counted fresh:
  sync `_wrap` guard pair
  (`reject_async_iterable_in_sync_context` + `prepared_resolver_source`
  with `reject_awaitable_sync_source`), async `_wrap` guard
  (`reject_residual_async_source`), async-rejection cleanup ×2 via
  `_cleanup_rejected_async_iterable`. C1/C2 still count 1 at the
  querysets owner.
- F2 (`sealed-execution-queryset`): REVISE concur, verdict stands
  (consumer). Applier freeze-then-seal sites moved with the twins;
  pipelines still consume the visibility seals; the
  construction-vocabulary sweep re-run at HEAD finds zero
  `models.QuerySet(` / `sql.Query` here. C3 still counts 1 at the
  seal.
- F4 (`post-set-apply-result-validation`): REVISE concur, verdict
  moves to consumer. This file's pipelines call the shared
  appliers (1 per color); connection selects the same shared
  `apply_orderset_sync` / `apply_orderset_async` per kind (`apply
  = ... if kind == "order" else ...`, then `qs = apply(...)` /
  `qs = await apply(...)` in both pipelines, bodies read) and no
  direct `OrderSet.apply_*` call remains there. One seal, two
  consumers. C5 retired, correctly.
- R5 (normalized-arguments record): REVISE concur. Record,
  exact-`int` gate, ceiling sources, mode decision byte-identical
  (per-symbol comparison); the ×3 supplied-spelling verified
  verbatim at HEAD lines 466-468 and nowhere else outside a
  docstring package-wide (AST-filtered census). Genuinely gains
  the F-NEW candidate.
- R8 (resolver invocation and rejection): REVISE concur, 6→5.
  `_require_orderset_class` deleted; the gate re-derived at its
  querysets owner with the flavor-shared `Field target ...`
  message; the oracle `test_require_orderset_class_rejects_a_target_without_one`
  re-read (name unchanged, calls the owner, pins the new
  message — no staleness). Remainder byte-identical.
- R10 (pipelines and factory): REVISE concur. Pipelines compose
  the shared appliers by name; the pipeline diffs are exactly the
  one-line call re-points each (full `bfaee91d`→HEAD delta read:
  7 hunks, 10+/88-), twin structure, step order, and no-arg fast
  paths untouched.

16 CONFIRM + J1–J6 standing: concur. Premises re-read at HEAD
(keyset `_keyset_order_ref` present; connection direct
`definition.*` reads; connection synthesizer with
`ConnectionExtension`; mutation `_mutation_meta` subject;
converter `Model.field` label; all four J5 walkers present;
`LOOKUP_NAME_MAP` vs class-identity sets; `classify_path` body
identical drift→HEAD; schema.py zero classifier bytes re-swept).
Triggers unfired.

### D3 closure: sound

The querysets run-7 record carries D3 as RESOLVED-fixed standing
(landed pre-drift, prose note discharged by the drift); this side
independently confirms both flavors now enter the one shared seal
(F4 evidence above) and the `_SealPolicy` prose states the rule
for the list field and the Relay connection alike. No absent
member remains; nothing routes anywhere. W1's reliance on the
verified querysets outcome is legitimate (owner-side adjudication
cited, list-side call sites re-derived, not inherited).

### F-NEW candidacy: real, name it

C-O1 re-derived at 2: `utils/input_values.py::is_inactive_value`
(the rule: `None` or `unset_sentinel`, docstring claiming the
single active-input rule, body read) versus the ×3 hand-spelling
(one function, moves together — correctly 1, not 3). Exact
inverse confirmed (`x is not None and x is not strawberry.UNSET`
≡ `not is_inactive_value(x, unset_sentinel=strawberry.UNSET)`).
Sole-remaining-hand-spelling census re-derived (package-wide,
docstring-filtered). Never homed: outside the
`unset-bindings-across-families` census and that plan row is
`rejected`, so not an adoption target; converge with the
`input-values-active-rule` file-local row properly left to
Worker-0. O1 provenance confirmed (routed from File
`utils/input_values.py`, lines 466-468 cited there match HEAD
bytes exactly). The `is_supplied` docstring's connection-argument
claim and "15 sites" history note both verified verbatim, so the
family item genuinely owes the spelling decision. Name
`list-argument-supplied-spelling` is descriptive and collision-free
(the plan's only mention is Worker-0's dispatch summary of this
submission).

Transcription owed (exact): there is no literal `## Index rows
for Worker-0` section in the run-7 W1 text — the transcribable
content is carried by the F-NEW record as "transcribe 1 row".
Judged sufficient, not revision-worthy: the dispatch brief did not
require that section shape, all row facts are present, and no
other transcription is owed (no plan row is held by this file;
every family row covering it keeps name/owner/files/status
except F4's, which already carries the run-7 consumer note
transcribed from the connection re-trace — this item's F4 revise
agrees, no further edit). Literal row for verbatim transcription:

| `list-argument-supplied-spelling` | TBD by family item (candidates: `django_strawberry_framework/utils/input_values.py::is_inactive_value` as the rule with its `django_strawberry_framework/utils/connections.py::is_supplied` binding) | `django_strawberry_framework/list_field.py`, `django_strawberry_framework/utils/input_values.py`, `django_strawberry_framework/utils/connections.py` | Family `list-argument-supplied-spelling` | open (C-O1 counts 2: the rule + the ×3 hand-spelling at `list_field.py::_normalize_list_arguments`; sole remaining hand-spelling package-wide) |

Worker-0 also owns the `## Families` queue entry for Family
`list-argument-supplied-spelling` (undispatched, holding the
F-NEW consolidation).

### Hunks, fingerprints, proof adequacy

Hunk attribution re-derived by reading every hunk body: 42 = 1
owned + 41 external. The owned hunk (`@@ -234,0 +213,8 @@`)
is pure-additive +8, the ledger's adopted-orphan
`relay-node-target-guard` trigger docstring on
`_validate_relay_djangotype_target` (ledger text matched). The 41
classify by content exactly as W1: 29 `utils/truth.py`-migration
(code + prose + `vars`/`type` + stateful-metaclass trims), 4
wire-name defensive-`try` removals, 3 `Count` docstrings, 1
Relay-node-factory widening, 1 pk-tiebreaker, 3 comment touch-ups
(synthesizer trim, `spec-050` prefix, `spec-020` number fix) — each
hunk keyed and tallied in `/tmp/lf_w2_part3.py` L6–L17. Dirt
avoids the deleted-twins region, both applier call sites, and the
O1 spelling (swept). Drift base blob == HEAD blob re-hashed
(`21380eb7`, nil delta); `bfaee91d`→HEAD delta re-measured (7
hunks, 10+/88-, prior blob `ce682d5f`). All 24 connected-input
fingerprints (drift → HEAD → worktree) re-hashed: 24/24 match
W1's short ids.

Matrix re-discharge concurred on reasons (both flavors compose
the one seal; 2 colored pairs remain with color-only duties; five
prior derivations hold; pickle + adapter pairs unchanged; oracles
spell literals with the gate oracle re-pointed, live sync additive
to 99 test functions re-counted, live async byte-identical to the
drift base; omission sweep clean). Equivalence (principle 8):
zero edits proposed or made. `## Pending execution` empty,
concur — read-only probes need no workspace, oracle bodies stay
`static-reviewed`, sharded/PG cells inapplicable by construction
(no DB, alias, or dialect decision in any counted claim).

AGENTS.md prose: this verdict touches the artifact (`.md`) only —
no `.py` touched, so no ruff run owed; `path::Symbol` citations
throughout; `path:NN` confined to this per-cycle artifact
(allowed); no process provenance; concurrent dirt untouched; no
commit.

### Defects (Worker 2)

None. The one known list-adjacent row, D3, is resolved, not
re-homed.

**Verdict.** `Status: verified`, no pending execution. Backstop
re-discharged at HEAD bytes: 76/76 members enumerated by an
independent parse, drift reconciled by name, all 6 REVISEs
re-derived, D3 closure sound, F-NEW candidacy real with the
literal transcription row above, 42/42 hunks attributed, 24/24
fingerprints matched, zero-defect call concurred, zero edits
legitimate.

## Scoped re-trace (run 8) — Worker 1

Scoped run: `0.0.15 2026-09-30-8`. HEAD `83998e08` at start,
verified unmoved at finish (`git rev-parse HEAD` both times).
Prior text above is prior evidence only and stands untouched;
this section appends. Zero production edits; a file item owes
none. Every claim below is traced at HEAD bytes unless marked
worktree; the worktree is read only for hunk attribution.

### Scope of the delta (drift base → HEAD → worktree → pre-merge)

Drift base `0c0537e2` → HEAD `83998e08` on the target is 9
commits, 82 `-U0` hunks, 148+/125-. Two are behavior-bearing,
both re-read in full:

- `5c5e32c5` (3 hunks): the pipelines drop the seal-policy
  selection. Both `_execute_queryset_pipeline_sync` /
  `_async` hoist ONE `apply_type_visibility_*` call with the
  default policy above the `any_argument_supplied` branch; the
  `_LIST_ARGUMENT_VISIBILITY_POLICY` argument branch and the
  import are deleted. Package-wide the name is gone (0 hits in
  package + tests + examples at HEAD; the 6 remaining hits are
  docs-only: builder DONE, one bld carry note, the querysets
  DRY artifact, spec-050 rationale — history and projections,
  never production) and `reject_combined` is 0 in
  package + tests + examples.
- `10d2b9cd` (2 hunks): `_selected_ordering` reads its model
  tier through the new `utils/querysets.py::default_order`
  owner (`ordering = default_order(query, queryset.model)`),
  replacing the inline `default_ordering` + `get_meta()`
  `.ordering` read. The `extra` / `explicit` / `nothing`
  tiers stay here.

The other 7 commits are proved non-behavioral on this target:
`999a1aab`, `b20277fe`, `849f67bc`, `dfbea72b` are `clean`
under the typing-erased AST proof (`/tmp/dry_ast2.py`, the
run-8 instrument); `dd3a10b1` is the `list[X] | None` →
`GenericAlias(list, (X,)) | None` spelling (proved `==` at
runtime); `fef11e64` is the `_async_wrap` / `_sync_wrap`
split whose inner `_wrap` bodies are AST-identical to the
removed inline closures (full `ast.dump` equality, both
colors; one closure still produced per construction,
`__name__` still `_wrap`); `5f440a93` declares the reason
vocabulary once as `_ListArgumentReason` (`Literal`) with
`_KNOWN_LIST_ARGUMENT_REASONS` derived via `get_args`
(proved `==` to the old literal, same 5 members; the runtime
membership check stays).

Per-symbol normalized comparison (annotations stripped)
drift base → HEAD: 33/33 named symbols present both sides, 0
added, 0 removed; 13 differ, all classified — the 2
pipelines + `_selected_ordering` (the behavior hunks), the
factory (wrap split), the synthesizer (GenericAlias), and 8
cast/annotation/`@override`-only bodies
(`ListArgumentError`, `_validate_djangotype_target`,
`_published_wire_name`, `_resolve_argument_wire_name`,
`_resolve_order_field_path`, `_approved_order_transform`,
`_is_deterministic_order_lookup_chain`, `_field_label`;
`cast` is a runtime identity, local annotations and
`@override` are runtime no-ops). Module level: +3 members
(`GenericAlias` import, `override` import,
`_ListArgumentReason`), the querysets import swaps the
removed policy for `default_order` (12 names), every order
constant and `_DEFAULT_WIRE_NAMES` / `__all__` untouched.

HEAD → worktree is 44 `-U0` hunks, 85+/143-, worktree blob
`1dcb0c43`. Hunk attribution by content, every hunk read:
ONE owned hunk, the ledger's adopted orphan
`relay-node-target-guard` trigger docstring on
`list_field.py::_validate_relay_djangotype_target`
(`@@ -243,0 +220,8 @@`, pure-additive +8, byte-identical to
the `9aaaad5d` bytes line for line); the other 43 are
concurrent-external and untouched — 31 `utils/truth.py`-
migration hunks (import collapse, `+from .utils import
truth`, `truth.*` renders/reads, `type(self)`,
`vars(self)`, contained-read trims), 4 wire-name
defensive-`try` removals, 3 `Count`-aggregate docstrings, 1
Relay-node-factory docstring widening, 1 pk-tiebreaker
docstring, 3 comment touch-ups (synthesizer trim, `spec-050`
prefix, `spec-020` number fix). None touches the pipelines'
visibility/applier call sites, `_selected_ordering` /
`default_order`, or the O1 spelling lines.

Pre-merge bytes `9aaaad5d` (read-only evidence via `git
show`, never applied): target hash `f5b0183e` (1752 lines),
equal to the run-7 worktree hash — it preserves the run-7
ledger bytes this re-proof checks against. HEAD is 1829
lines, worktree 1771.

### Enumeration (fresh instrument at HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes: **79
top-level statements** (indices 0–78): 1 module docstring, 28
import statements (indices 1–28: `GenericAlias` and
`override` are the drift additions; querysets block 12
names, resource_policy 7, exceptions 5), 1 `TYPE_CHECKING`
guard, 16 constants (`__all__`, `_ListArgumentReason` new,
`_KNOWN_LIST_ARGUMENT_REASONS`, `_DEFAULT_WIRE_NAMES`, 4
`_ORDER_FROM_*`, `_READABLE_ORDER_LEAVES`,
`_TRANSPARENT_ORDER_EXPRESSIONS`, 4 `_APPROVED_ORDER_*`
sets, `_APPROVED_ORDER_NODES`,
`_ORDER_VALUE_CONTAINERS`), 31 functions (29 `def` + 2
`async def`: `_handle_non_queryset_rejections_async`,
`_execute_queryset_pipeline_async`), 2 classes
(`ListArgumentError` with `__init__` + `__reduce__`,
`_ListArguments` with 5 fields). Delta vs run-7's 76 is
exactly the +3 above; 0 removed.

Every member lands in a home; every challenge below ends in
one:

| Members | Home |
|---|---|
| 0 docstring | projection |
| 1–28 imports, 29 guard | machinery / consumers (F1–F6, R10) |
| 30 `__all__` | projection (R3) |
| 31–32 reason Literal + frozenset, 35 error class | R3 (+ F6) |
| 33–34 validators | R1 (+ J4) |
| 36–38 wire fallback + readers | R4 |
| 39–40 arguments record + normalizer | R5 (+ F-NEW) |
| 41 synthesizer | R6 (+ J3) |
| 42–53 order constants, 54–66 classifier fns | R7 (+ J1, J5, J6) |
| 67–68 definition readers | R2 (+ J2, F5) |
| 69–73 resolver invocation + rejection | R8 (+ F1, F3, J4) |
| 74–75 guard + scope | R9 |
| 76–77 pipeline twins | R10 (+ F1–F5) |
| 78 factory | R10 (+ F1, F3, F5) |

No new family named; the one open candidate (F-NEW) is
already plan-indexed with its Family queue entry.

### Matrix re-discharge (at HEAD bytes)

**1. Cross-flavor policy mirroring.** Both flavors compose
the same seams by name and both enter the ONE post-sidecar
seal: this file's pipelines call `apply_orderset_sync` /
`_async` (1 per color); connection imports the same pair
(plus the filterset pair and `applied_order`) and selects
per kind (`apply = apply_orderset_sync if kind == "order"
else ...`, then `qs = apply(...)` / `qs = await apply(...)`
in both pipelines, bodies read). The model-tier order read
is now a composed triple with one owner per tier:
`utils/querysets.py::default_order` (model tier),
`utils/querysets.py::applied_order` (explicit else default,
consumed by connection `:1730` and `optimizer/plans.py`
`:939`, whose docstring states the `extra` tier is outside
it), `list_field.py::_selected_ordering` (extra >
explicit > model > nothing dispatch — the only site
classifying `extra`). Validators defined here, consumed by
connection + relay by name (both import lines re-read).
J1–J6 premises all re-read at HEAD (counts under
Challenges); the supplied-spelling inverse pair (F-NEW)
re-censused below.

**2. Sync/async twins.** Two colored pairs remain (the
applier twins live once in `utils/querysets.py::
_apply_sidecar_sync` / `_async` since before the drift
base): the pipeline twins (differ only in the awaited
visibility step, the per-color guard, and the sync twin's
`is_async_context` adapter tail; share scope + guard 3
hits each) and the factory `_wrap` branches (inner bodies
AST-identical across the `fef11e64` split, proved above;
differences are color duties: `await user_resolver` vs
direct call, residual vs awaitable guard,
`_resolve_async_iterable` coroutine return vs sync
`_windowed_rows`). The `_apply_sidecar_sync` body re-read:
freeze-before-override comment, `_dispose_sync_awaitable`
+ `SyncMisuseError`, `_SIDECAR_RESULT_POLICY` seal with
the pk-set note — duties intact.

**3. Derived rather than repeated knowledge.** The five
prior derivations hold (captured model/sidecar,
`base_queryset` seed, policy/bound ceilings,
`order_input_type` annotation via function-local import,
published-map wire names). New since run-7: the reason
vocabulary is declared once (`Literal`, derived via
`get_args`); the model-default tier is derived from
`default_order` rather than re-read. Still hand-written:
the ×3 supplied-spelling (F-NEW, 1 definition here).

**4. Inverse / round-trip pairs.** Unchanged: the
`ListArgumentError` pickle contract (class + 6 constructor
args + `__dict__`, `extensions` rebuilt by `__init__`)
and the async-adapter wrap (6 occurrences: 1 import + 4
code + 1 docstring; true call sites 4). No second grammar
here.

**5. Contracts restated in another medium.** Oracles at
HEAD spell literals directly: `tests/test_list_field.py`
76 test functions (unchanged count), live sync suite 99
(unchanged), live async suite 53; the orderset-gate oracle
still imports `require_orderset_class` from its querysets
owner and pins the `Field target ...` message (name,
import line, and match string re-read — no staleness);
the `__all__` pair pinned by `tests/base/test_init.py`
(both names + identity assert re-read); `spec-050`
byte-identical across drift, HEAD, worktree, and pre-merge
(`73fe1127` ×4).

**6. Enforcement by omission.** (a) Post-sidecar seal: no
absent member — both flavors seal via the shared appliers
(counts above); D3 stays closed. (b) `one-sync-boundary`:
0 hits here, inapplicable by construction. (c) Raw-body
source: no body read here, inapplicable by construction.
(d) Offset guard: every offset path re-verified at HEAD —
`_default` and both `_wrap` queryset branches flow into
the pipelines (guard after OrderSet inside the shared
scope); non-queryset sources flow into the sync builder /
async handler (same `queryset_required` /
`order_required` wire names); the no-argument fast path
carries no offset so the guard returns early by
construction. No member lacks a guard its contract
requires.

### Challenges (definition counts, authoritative only)

C1–C4, C6–C8, C30 re-verified at HEAD bytes (1 at each
owner, 0 here); C5 stays retired (run-7); C21–C30 stand
(classifier untouched except 2 cast-only helpers).
Re-pointed and new:

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C-F2 | visibility seal | a new untrusted shape must be rebuilt | **1** (`utils/querysets.py::_seal_or_defect`; no policy selection remains in the pipelines) | consumer |
| C-F4 | post-sidecar contract | the contract gains an axis | **1** (`_SIDECAR_RESULT_POLICY` + `_apply_sidecar_*`; both flavors follow) | consumer |
| C-O1 | supplied spelling | a third inactive spelling ships | **2** (`utils/input_values.py::is_inactive_value`, 1; the ×3 here at `:482-484`, 1) | candidate (F-NEW, open) |
| C-R3 | reason vocabulary | a sixth reason ships | **1** (`_ListArgumentReason` + derived frozenset + `__init__` arm + `__reduce__` passthrough move together) | file-local |
| C-R7a | collection precedence | the extra/explicit precedence changes | **1** (`list_field.py::_selected_ordering`) | file-local |
| C-R7b | model-tier semantics | the default-order read changes | **1** (`utils/querysets.py::default_order`; list, `applied_order`, connection follow) | consumer |
| C-R10 | pipeline step | a new step ships | **1** owner, two bodies (twins move together by color) | file-local |

Sole-site census at HEAD (package-wide, `git grep`):
`is not strawberry.UNSET` hits exactly 3 in this file
plus 1 docstring mention in `utils/connections.py` —
the ×3 is the sole remaining hand-spelling. Exact
inverse re-proved against the rule body (`value is None
or value is unset_sentinel`): `x is not None and x is not
strawberry.UNSET` ≡ `not is_inactive_value(x,
unset_sentinel=strawberry.UNSET)`. `is_supplied`'s
docstring still claims a connection argument with the
"15 sites" history note, so the Family item still owes
the spelling decision.

Probes: read-only AST + token census over `git show`
bytes, scratch under `/tmp` only (`/tmp/lf_r8_probe*.py`,
`/tmp/lf_wrapproof.py`, `/tmp/lf_symdiff.py`,
`/tmp/lf_symshow.py`, `/tmp/lf_testcensus.py`, plus the
run-8 `/tmp/dry_ast2.py` instrument); no Django import,
no SQL, no source mutation, no workspace, no pytest.
`execution-verified` for every identity / count / shape /
absence claim in this section; oracle bodies stay
`static-reviewed`, the honest label for a zero-edit item.
Two first-draft probe expectations failed on precision
(class-member printer on `AnnAssign`, an over-broad
`default_order` substring also matching
`default_ordering`) and were corrected to the HEAD truth;
substance unaffected.

### Findings: CONFIRM / REVISE ledger (18 + 4)

Every run-7 finding re-checked against HEAD bytes with
fresh evidence; anything citing the removed policy or the
old per-site ordering read is re-derived below.

- F1 (`awaitable-refusal-and-disposal`): CONFIRM (consumer,
  0 definitions). Guard pair + async guard + async-rejection
  cleanup re-censused (prepared 3, async-only 4); sidecar
  dispose/refusal duties re-read in `_apply_sidecar_*`.
- F2 (`sealed-execution-queryset`): REVISE, verdict stands
  (consumer). The pipelines no longer select a policy: one
  default-policy visibility call sits above the branch in
  each twin (visibility census 3→2 per color). A combined
  hook result is now served as its pk set by
  `_seal_or_defect` under `rewrite_combined` (default on);
  the run-7 "argument-branch policy" and "combined rejected
  argument-mode" prose is superseded. Construction-vocabulary
  sweep still 0 here.
- F3 (`async-only-queryset-row-adapter`): CONFIRM
  (predicate 4 + wrap 6, bodies untouched).
- F4 (`post-set-apply-result-validation`): CONFIRM
  (consumer, both flavors). List 1+1 applier calls,
  connection kind-selected shared appliers, both bodies
  read; `_SIDECAR_RESULT_POLICY` still `require_unevaluated`
  with the one-seal-for-both-flavors prose; post-sidecar
  combined now also pk-served (record precision). D3 stays
  closed; nothing routes anywhere.
- F5 (`queryset-seed-and-model-read`): CONFIRM (default
  seed + `model=` threading untouched; `model_for` /
  `initial_queryset` still absent by construction).
- F6 (`typed-rejection-value-tail`): CONFIRM at HEAD (all
  six render sites intact; the worktree `truth.*` rewrite
  is concurrent dirt, never HEAD).
- R1–R2: CONFIRM (validators: annotation + `cast`-only
  delta, guard order and identity checks intact;
  relay + connection consume by name; readers untouched).
- R3: REVISE, verdict stands (file-local). Vocabulary
  declared once as `_ListArgumentReason`, frozenset
  derived, runtime check stays; same 5 members proved
  equal; +1 module member.
- R4: CONFIRM (wire fallback + readers; `cast` /
  annotation-only delta; laziness intact).
- R5: CONFIRM (record, exact-`int` gate, ceilings, mode
  decision untouched; ×3 verbatim at `:482-484`; F-NEW
  still attached).
- R6: CONFIRM (synthesizer; `GenericAlias` spelling
  proved runtime-equal).
- R7: REVISE, verdict stands (file-local with noted
  composition). 13 functions + 12 constants intact; the
  model tier composes `utils/querysets.py::default_order`
  by name (C-R7a vs C-R7b: two sub-rules, one owner
  each — dispatch here, model-tier read there — never
  two definitions of one rule). `10d2b9cd` records the
  guard already read both rules correctly, so no list-side
  behavior moves.
- R8: CONFIRM (5 members, bodies untouched).
- R9: CONFIRM (guard + scope untouched; the model-order
  question routes through `default_order` with preserved
  semantics).
- R10: REVISE, verdict stands (file-local). Pipelines
  hoist the single default-policy call (step order, twin
  structure, fast paths unchanged); factory wrap split is
  runtime-equal with AST-identical inner bodies.
- J1–J6: CONFIRM, triggers unfired, premises re-read at
  HEAD: keyset `_keyset_order_ref` present; connection
  direct `definition.*` reads present; connection
  synthesizer still `ConnectionExtension`-shaped; mutation
  guard still subjects `_mutation_meta`; converter label
  still `Model.field`; all four J5 walkers present
  (`_resolve_order_field_path` here,
  `_resolve_order_path_field` in connection,
  `classify_path`, `_prefetch_relation_target_or_none`);
  `LOOKUP_NAME_MAP` still produces spellings (3 hits)
  while the guard certifies lookup classes.
- F-NEW (`list-argument-supplied-spelling`): CONFIRM
  candidate, still count-2 (C-O1 re-proved with fresh
  census + inverse proof above). The plan already carries
  the family row and the undispatched Family queue entry;
  no new transcription is owed by this item.

Seal-composition rule (re-derived, new owners): every
visibility seal in the pipelines runs
`apply_type_visibility_*(..., policy=_DEFAULT_SEAL_POLICY)`
(model rows, unsliced, combinator → pk set, one alias);
post-sidecar results run `_SIDECAR_RESULT_POLICY`
(`require_unevaluated` added); both policies execute in
`utils/querysets.py::_seal_or_defect`, which owns the
combined rewrite (`_combined_lost_property` fail-closed
arms) and the routing comparison. Ordering rule
(re-derived, new owners): `default_order` owns the
model-tier read (falsy while `default_ordering` is off or
`Meta.ordering` is empty/`None`); `applied_order` owns
explicit-else-default; `_selected_ordering` owns the
four-way dispatch including the `extra` tier no other
reader classifies.

### Defects

None. Every claim checked while tracing held: the 79/31/2
counts; the +3 reconciled by commit; the 13-symbol
normalized delta classified with zero unexplained bodies;
the wrap-split identity; the Literal and GenericAlias
equalities; the policy removal (0 package hits) with the
hoisted single call per twin; the model-tier composition
with its three single-owned sub-rules; the ×3 verbatim
with the sole-site census; the gate oracle re-pointed
without staleness; the 44 worktree hunks attributed
(1 owned byte-identical + 43 concurrent, none on a
fingerprinted behavior site); D3 staying closed from both
flavors' call sites. No new defect is routed to any owner.

### Pending execution

None. The execution proofs are the read-only probes cited
under Challenges (no source mutation, no database, no
workspace owed, no `__file__`/DB record applies). No
pytest in the shared tree per item rules (the one
authorized focused `--no-cov` test is unneeded: a zero-edit
census item has no behavior delta to pin). No
`FAKESHOP_SHARDED` or Postgres cell is owed: every counted
claim touches no database, alias, or dialect decision
(inapplicable by construction; DB-reaching paths are
exercised by the cited oracles, whose bodies are
`static-reviewed`).

### Item-scoped diff state and fingerprints

Tracked: none beyond this artifact — zero production
edits, zero test edits. `HEAD` `83998e08` unmoved (start
and finish). `ITEM_BASELINE=
ebf572a24db4be485d42e59dd029a0a95dff4b23`
(resolves; the item's diff on package + tests is 0 bytes —
verified by re-running `git diff` on those trees after all
reads).

Target fingerprints: drift base
`21380eb72364caef0da05ca3ee3f26c0134e3904` → HEAD
`77ddb86cf8467c695ecf1f89722bbccfa74315fa`; worktree
`1dcb0c433fd8950dc49f530a14de6ce31e06ca37`;
pre-merge `9aaaad5d`
`f5b0183e290322952fd2dad1f76ab9b2de9736ba`
(read-only evidence only).

Connected inputs (drift → HEAD → worktree → pre-merge,
short ids): `connection.py` `4894f90f` → `3d6dd424` /
`64b85d0e` / `1fca6266`; `utils/querysets.py` `3616927d`
→ `392e50d0` / `cfc773ba` / `8fc556d5`;
`utils/relations.py` `8dbc3fe6` → `72e7ff08` / `6b80acac`
/ `05ff55b0`; `utils/input_values.py` `f2566609` →
`3c17224f` / `f07708b4` / `18992b79`;
`utils/connections.py` `f549389e` → `735aa454` /
`735aa454` (clean) / `efcf749a`; `exceptions.py`
`e06b0b7f` → `f27e1f91` / `34e2e6be` / `93401220`;
`resource_policy.py` `4b69e974` → `47befb3f` / `927b89a2`
/ `5b4a80f0`; `relay.py` `c3c5aea5` → `a09485a1` /
`fd88aafa` / `f5760b45`; `registry.py` `81bd561c` →
`9d2021eb` / `57fa18ae` / `27358cbc`;
`utils/directives.py` `380786cf` → `0368ff51` / `bbbf3b42`
/ `84f770d4`; `utils/execution_mode.py` `9805cdaf` →
`b86a08cd` / `b86a08cd` (clean) / `9805cdaf`;
`utils/typing.py` `de6309f6` → `1ce032f1` / `5083bdb3` /
`a672cd6b`; root `__init__.py` `0ef72601` → `8b165672` /
`8b165672` (clean) / `0ef72601`; `orders/sets.py`
`6044ab1a` → `c4564c08` / `125d808c` / `60859f2d`;
`filters/inputs.py` `82b52d97` → `2c853e24` / `c933bb5d`
/ `a932dbf8`; `mutations/fields.py` `d4edcbb7` →
`8d3ce7e2` / `c6da2e54` / `0e4d5ed1`;
`types/converters.py` `058f1081` → `d146b23f` / `6d4d71e8`
/ `f6cadb08`; `types/base.py` `dda91365` → `d160998a` /
`909c25a7` / `dc67f084`; `schema.py` `e6b52335` →
`bba03d7d` / `abad5795` / `f4e807e9`;
`tests/test_list_field.py` `038e69ce` → `9efccda3` /
`6d74fcd1` / `d78aa5e7`; live sync `4c85f779` →
`cc1838ce` / `cc1838ce` (clean) / `4c85f779`; live async
`49e423ea` → `4a570915` / `4a570915` (clean) / `49e423ea`;
`spec-050` `73fe1127` → `73fe1127` (unchanged all four
states).

### Judgment

Backstop re-discharged at HEAD bytes: 79/79 members
enumerated, drift reconciled by name and by normalized
per-symbol diff (2 behavior hunks + 7 proved-typing
commits, zero unexplained bodies), matrix re-run against
the real current surface, 18 prior findings CONFIRMed and
4 REVISEd (F2 seal composition, R3 Literal vocabulary, R7
model-tier composition, R10 pipeline hoist), 6 rejections
standing with premises re-read at HEAD, F-NEW candidacy
re-proved count-2 with the plan row already transcribed,
no defect found, no consolidation owed by this file item.
Zero-edit result is legitimate.

No new `## Responsibility index` rows proposed for
Worker-0: every family this target touches is already
indexed; `list-argument-supplied-spelling` keeps its open
row and undispatched Family queue entry.

## Run-8 verification

Run: 0.0.15 2026-09-30-8. HEAD `83998e08` at start,
verified unmoved at finish. Expectation-first with a method note:
the required order puts the artifact after the target, and I read
the full artifact (including the run-8 W1 section) before running my
own instruments — so every count, census, and fingerprint below was
re-derived with independent probes rather than inherited, and each
difference is reconciled explicitly. Instruments: read-only probes
under `/tmp` (`/tmp/lf_w2_r8_a.py` ALL OK, `/tmp/lf_w2_r8_b.py`
ALL OK, `/tmp/lf_w2_r8_c.py` + `/tmp/lf_w2_r8_c2.py` ALL OK — AST +
token census over `git show` bytes) plus read-only `git diff` /
`git grep` / `git rev-parse` / `git hash-object` reads. No Django
import, no SQL, no source mutation, no workspace, no pytest. Three
first-draft expectations failed on probe precision (an import-alias
vs `Name` count, an `ast.dump` call on a list, a `__name__`
docstring hit) and were corrected to the HEAD truth after reading
the bytes; substance unaffected in all three cases.

### Own trace (independent instruments)

`ast.parse` over HEAD bytes, my own enumeration: **79
`ast.Module.body` members** — 1 module docstring, 28 import
statements, 1 `TYPE_CHECKING` guard, 16 constants (`__all__`,
`_ListArgumentReason`, `_KNOWN_LIST_ARGUMENT_REASONS`,
`_DEFAULT_WIRE_NAMES`, 4 `_ORDER_FROM_*`,
`_READABLE_ORDER_LEAVES`, `_TRANSPARENT_ORDER_EXPRESSIONS`, 4
`_APPROVED_ORDER_*` sets, `_APPROVED_ORDER_NODES`,
`_ORDER_VALUE_CONTAINERS`), 31 functions (29 `def` + 2 `async
def`: `_handle_non_queryset_rejections_async`,
`_execute_queryset_pipeline_async`), 2 classes
(`ListArgumentError` with `__init__` + `__reduce__`,
`_ListArguments` with 5 fields: `offset`, `limit`, `order_by`,
`order_by_supplied`, `any_argument_supplied`). Delta vs run-7's 76
is exactly +3 (`GenericAlias` import `:14`, `override` import
`:72`, `_ListArgumentReason` `:122`); 0 removed. Import census:
querysets block 12 names (carries `default_order`, not the removed
policy), resource_policy 7, exceptions 5.

Drift `0c0537e2..83998e08` on the target re-measured: 9 commits,
82 `-U0` hunks, 148+/125-. Both behavior commits read in full:
`5c5e32c5` (3 hunks: the policy import line gone; each pipeline twin
hoists one default-policy visibility call above the
`any_argument_supplied` branch; the argument branch deleted);
`10d2b9cd` (2 hunks: `default_order` import; `_selected_ordering`
model tier through it). Normalized per-symbol comparison of my own
(annotations, returns, decorators, top docstring, `cast` stripped):
33/33 named symbols present both sides, 0 added, 0 removed; the
union of my 9 differing with W1's 13 is exactly W1's 13, every
residual classified — the 2 pipelines + `_selected_ordering` (the
behavior hunks), the factory (wrap split, proved identical below),
the synthesizer (`GenericAlias`, proved equal below), and 8
annotation/`cast`/`@override`-only bodies (4 absorbed by my strip;
the other 4 residuals printed and shown to be local-annotation-only:
`Assign` → `AnnAssign` ×3 plus one bare local declaration, all
runtime no-ops; the single `@`-line in the whole drift diff is
`@override` on `__reduce__`).

Owners I would choose (before reconciling): the visibility seal,
the post-sidecar seal, disposal, and the default-order read at
`utils/querysets.py` with this file consumer-only; validators,
readers, error vocabulary, wire names, arguments record, SDL
synthesizer, classifier dispatch, resolver invocation, offset guard
+ scope, pipeline twins + factory here. No new family named by me;
one candidate received (F-NEW) and judged below.

### Per-row judgments (22 + F-NEW, my counts)

- F1 (`awaitable-refusal-and-disposal`): CONFIRM (consumer, 0
  definitions). Guard pair + async guard + async-rejection cleanup
  re-censused (`prepared_resolver_source` 3, `is_async_only_iterable`
  4, `wrap_async_queryset_adapter` 6); wire-reader + cleanup call
  graph stable 15 → 15 across the drift; sidecar dispose/refusal
  duties re-read at the owner (`_dispose_sync_awaitable` +
  `SyncMisuseError`, the documented refusal split, snapshot before
  the override in both `_apply_sidecar_*` bodies, the
  `_SIDECAR_RESULT_POLICY` seal). C1/C2 still count 1 at the owner.
- F2 (`sealed-execution-queryset`): REVISE, concur (consumer). The
  hoist proved by AST: each twin's `body[0]` is the single
  default-policy call, `body[1]` the `any_argument_supplied` branch;
  1 call per twin (2 occurrences per color = import + call). The
  removed policy is 0 hits in package + tests + examples; the 6
  remaining hits enumerated docs-only (DONE build-050, one bld carry
  note, the querysets DRY artifact ×2, spec-050 rationale ×2).
  `reject_combined` likewise 0 in package + tests + examples. The
  pk-set serving re-derived at its owner (`rewrite_combined`
  defaults `True`, `_combined_lost_property` fail-closed arms, all
  executed in `_seal_or_defect`). Construction vocabulary still 0
  here. C-F2 counts 1 at the seal.
- F3 (`async-only-queryset-row-adapter`): CONFIRM. Predicate 4 +
  wrap 6; no local definition (`class _AsyncQuerySetRows` 0,
  `def wrap_` absent).
- F4 (`post-set-apply-result-validation`): CONFIRM (consumer, both
  flavors). List 1+1 applier calls; connection kind-selects the same
  shared appliers (`:1907` / `:1954`, then `qs = apply(...)` / `qs =
  await apply(...)` with `model=definition.model`);
  `_SIDECAR_RESULT_POLICY` still `require_unevaluated` with the
  one-policy-for-both-sidecars prose. D3 stays closed; nothing routes
  anywhere.
- F5 (`queryset-seed-and-model-read`): CONFIRM. Default seed +
  `model=` threading intact; `model_for` 0, `initial_queryset` 0.
- F6 (`typed-rejection-value-tail`): CONFIRM at HEAD. Exceptions
  import 5; all six render sites intact (host symbols identical under
  the normalized diff except `ListArgumentError`'s annotation-only
  delta); the worktree `truth.*` rewrite is dirt on non-HEAD bytes.
- R1–R2: CONFIRM. Validators absorbed by the normalized strip
  (annotation/`cast`-only; guard order and identity checks intact);
  relay (`:64`) + connection (`:82`) import the relay guard by name;
  readers byte-identical.
- R3: REVISE, concur (file-local). Vocabulary declared once as
  `_ListArgumentReason` (`Literal`), frozenset derived via
  `get_args`; proved equal by my own runtime check
  (`frozenset(get_args(...))` == the old 5-literal, 5 members); the
  old literal gone; the runtime `if reason not in` check stays; +1
  module member. C-R3 counts 1 here.
- R4: CONFIRM. Wire fallback + readers; `cast`/annotation-only
  delta; laziness intact (call graph stable per F1 counts).
- R5: CONFIRM. Record, exact-`int` gate, ceilings, mode decision
  untouched; the ×3 verbatim at `:482-484`; F-NEW still attached.
- R6: CONFIRM. Synthesizer; the `GenericAlias` line verbatim;
  proved runtime-equal by my own check (`==`, same type, same under
  `| None`).
- R7: REVISE, concur (file-local with noted composition). 13
  functions + 12 constants intact (the 2 differing helpers are
  annotation-only: `_approved_order_transform` absorbed by my strip,
  `_is_deterministic_order_lookup_chain` local-annotation-only);
  the model tier is 1 import alias + 1 call in `_selected_ordering`
  (`:1163`); `default_order` body read (falsy while
  `default_ordering` is off or `Meta.ordering` is empty/`None`);
  `applied_order` owns explicit-else-default with the
  extra-tier-outside prose, consumed by connection (`:1730`) and
  `optimizer/plans.py` (`:939`); `effective_connection_order`
  takes `(cursor_field, query, model)` — the query, not a pre-read
  tuple. C-R7a here, C-R7b at the owner: two sub-rules, one owner
  each, never two definitions of one rule.
- R8: CONFIRM. 5 members; only `_field_label` differs
  (local-annotation-only, printed).
- R9: CONFIRM. Guard + scope absent from the normalized diff set;
  the model-order question routes through `default_order` with
  preserved semantics (the commit message records the guard already
  read both rules correctly).
- R10: REVISE, concur (file-local). Pipelines hoist the single
  default-policy call (F2 proof; step order, twin structure, fast
  paths unchanged); the factory wrap split proved runtime-equal —
  inner `_wrap` bodies AST-identical per color across `fef11e64`
  (annotation-stripped full-dump equality), 2 `def _wrap` + 2
  `return _wrap` at HEAD, each maker called once per construction,
  no `__name__` rebind (the single hit is docstring prose).
  Differences stay color duties. C-R10 counts 1 owner, two bodies.
- J1–J6: CONFIRM each, triggers unfired, premises re-read at HEAD:
  keyset `_keyset_order_ref` present (J1); connection direct
  `definition.model` ×7 / `cursor_field` / 11 sidecar reads (J2);
  connection synthesizer still `ConnectionExtension`-shaped (J3);
  mutation guard still subjects `_mutation_meta` and exactly two
  `def _field_label` exist (J4); all four J5 walkers present (J5);
  `LOOKUP_NAME_MAP` still produces spellings (3 hits in
  `filters/inputs.py`) while the guard certifies lookup classes
  (J6).
- F-NEW (`list-argument-supplied-spelling`): CONFIRM candidate,
  still count-2. The rule body read (`return value is None or value
  is unset_sentinel`); the exact inverse of the ×3 proved by reading
  both sides; production two-arm census = the ×3 + 1 docstring
  mention; `is_supplied`'s docstring still claims a connection
  argument with the "15 sites" history note, so the Family item
  still owes the spelling decision. Precision note (verdict
  unaffected): the raw token `is not strawberry.UNSET` carries one
  more hit in `tests/rest_framework/test_sets.py:853` — a single-arm
  default-identity assertion in a test, identical at the drift base,
  outside the rule's contract — so the rule-contract census (two
  arms, production) is exactly as stated. The cycle record already
  carries the family row and the undispatched Family queue entry;
  no new transcription owed.

### Matrix, equivalence, gates, hunks, fingerprints

Matrix concurred on reasons: both flavors compose the one seal by
name with kind-selected shared appliers; 2 colored pairs remain with
color-only duties; the five derivations hold plus the 2 new
compositions (Literal vocabulary, model-tier read); pickle +
adapter pairs unchanged (wrap = 1 import + 4 code + 1 docstring);
oracles spell literals (76 / 99 / 53 test functions re-counted, gate
oracle re-pointed without staleness, `__all__` pair pinned by
identity assert, spec-050 byte-identical across all four states);
omission census clean (D3 closed, boundary/body inapplicable by
construction at 0 counts, every offset path re-verified).

Equivalence (principle 8): zero edits proposed or made; twin halves
differ only where color requires. `## Pending execution` empty,
concur — read-only probes need no workspace, oracle bodies stay
`static-reviewed`, sharded/PG cells inapplicable by construction (no
DB, alias, or dialect decision in any counted claim). Coupling: none
marked, none needed.

Hunk attribution re-derived by reading every hunk body: 44 = 1 owned
+ 43 external. The owned hunk (`@@ -243,0 +220,8 @@`, pure-additive
+8, the ledger's `relay-node-target-guard` trigger docstring) is
byte-identical to the `9aaaad5d` bytes (`cmp` clean in both
directions: hunk-vs-pre-merge and worktree-region-vs-pre-merge).
My independent buckets match W1's 31 / 4 / 3 / 1 / 1 / 3 exactly
(`utils/truth.py`-migration incl. import collapse, `truth.*`
renders/reads, `type(self)`, `vars(self)`, contained-read trims;
wire-name defensive-`try` removals; `Count` docstrings; Relay
node-factory widening; pk-tiebreaker; comment touch-ups). Range
check: no hunk touches the O1 spelling (`:482-484`),
`_selected_ordering` (`:1142-1167`), or the pipelines
(`:1451-1560`); the worktree keeps the ×3, the hoisted single calls,
and the `default_order` composition verbatim.

Freshness re-hashed by me, all match: target drift `21380eb7` →
HEAD `77ddb86c`, worktree `1dcb0c43`, pre-merge `f5b0183e`; all 22
connected inputs × 4 states match W1's short ids; spec-050
`73fe1127` ×4. HEAD `83998e08` unmoved at finish; item-scoped diff
`git diff ebf572a24db4be485d42e59dd029a0a95dff4b23 --
django_strawberry_framework/list_field.py` re-measured at 0 bytes.

AGENTS.md prose: the item diff is empty (tracked change is this
artifact only), so no test-tier, format, or commit obligations fire
and no ruff/mypy run is owed; `path::Symbol` citations throughout
with `path:NN` confined to this per-cycle artifact (allowed); no
process provenance; concurrent dirt untouched; no commit.

### Defects

None. Every independently re-derived claim held; D3 stays closed,
not re-homed.

**Verdict.** `Status: verified`, no pending execution. Backstop
re-discharged at HEAD bytes: 79/79 members enumerated by an
independent parse, drift reconciled by name and by normalized
per-symbol diff (2 behavior hunks + typing-only rest, zero
unexplained bodies), all 22 rows plus F-NEW judged with my own
counts, J1–J6 triggers unfired, the removed policy gone
production-wide with its new owners re-derived, 44/44 hunks
attributed, freshness re-hashed, zero-defect call concurred, zero
edits legitimate.

[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
