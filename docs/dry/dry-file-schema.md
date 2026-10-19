# DRY review: `django_strawberry_framework/schema.py`

Status: verified
Run: 0.0.15 2026-09-30-8

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, re-challenged
fresh on the schema side) or a file-local record with its proving
challenge, plus four recorded rejections. Zero production edits; zero tracked
files changed.

## System trace

Large target (1236 lines, 55 top-level statements): the package's schema
surface. It DEFINES the mutation completion window
(`django_strawberry_framework/schema.py::DjangoMutationExecutionContext` plus
`django_strawberry_framework/schema.py::_AcquireHandoff`,
`django_strawberry_framework/schema.py::_AsyncAliasLock`,
`django_strawberry_framework/schema.py::_async_mutation_lock` and the
`_ASYNC_MUTATION_LOCKS` store), the enforcement-record holding
(`django_strawberry_framework/schema.py::_SchemaEnforcement`,
`django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT`,
`django_strawberry_framework/schema.py::_SCHEMA_EXTENSIONS`,
`django_strawberry_framework/schema.py::_FALLBACK_ENFORCEMENT`,
`django_strawberry_framework/schema.py::_enforcement`,
`django_strawberry_framework/schema.py::DjangoSchema.__init__`,
`django_strawberry_framework/schema.py::DjangoSchema.extensions`,
`django_strawberry_framework/schema.py::DjangoSchema.resource_policy`,
`django_strawberry_framework/schema.py::DjangoSchema.error_policy`), the chain
admission (`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`,
`django_strawberry_framework/schema.py::_admitted_chain`,
`django_strawberry_framework/schema.py::_refused_chain`,
`django_strawberry_framework/schema.py::_consumer_extension_entries`,
`django_strawberry_framework/schema.py::_declared_authority`,
`django_strawberry_framework/schema.py::_entry_resource_policy`,
`django_strawberry_framework/schema.py::_entry_type`,
`django_strawberry_framework/schema.py::_extension_entry_matches`,
`django_strawberry_framework/schema.py::_is_resolvable_extension_entry`,
`django_strawberry_framework/schema.py::_is_extension`,
`django_strawberry_framework/schema.py::_claimed_authority`,
`django_strawberry_framework/schema.py::_operation_mode`), the refusal
substitution (`django_strawberry_framework/schema.py::_REFUSAL_DOCUMENTS`,
`django_strawberry_framework/schema.py::_refuse_operation_document`,
`django_strawberry_framework/schema.py::_RefusedConfiguration`,
`django_strawberry_framework/schema.py::SCHEMA_CONFIGURATION_ERROR_CODE`), and
the streamed binding (`django_strawberry_framework/schema.py::DjangoSchema.create_extensions_runner`,
`django_strawberry_framework/schema.py::DjangoSchema._stream`). It CONSUMES by
name every other rule it touches: the one-boundary primitive
(`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`),
the tail renderer (`django_strawberry_framework/exceptions.py::describe_value`),
the policy ladders (`django_strawberry_framework/resource_policy.py::resolve_resource_policy`,
`django_strawberry_framework/error_policy.py::resolve_error_policy` via
`django_strawberry_framework/utils/policies.py::resolve_policy`),
the copy primitive (`django_strawberry_framework/utils/policies.py::copy_policy`),
the private-state primitives
(`django_strawberry_framework/utils/private_state.py::PrivateAuthority`,
`django_strawberry_framework/utils/private_state.py::PrivateMembership`), the
mode fact (`django_strawberry_framework/utils/execution_mode.py::OperationMode`,
`django_strawberry_framework/utils/execution_mode.py::async_execution`), the
write-transaction seam
(`django_strawberry_framework/utils/write_transaction.py::managed_write_transaction`,
`django_strawberry_framework/utils/write_transaction.py::resolve_write_alias`),
the marker constant (`django_strawberry_framework/mutations/fields.py::MUTATION_CLASS_MARKER`),
the runner (`django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner`,
`django_strawberry_framework/extensions/operation_state.py::_OperationModeMarker`),
and the chain authorities
(`django_strawberry_framework/extensions/error_policy.py::DjangoErrorPolicyExtension`,
`django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension`,
`django_strawberry_framework/extensions/resource_policy.py::_AdmissionGuard`).

Connected code read for judgment, outside the item:
`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`
(full read, docstring plus body);
`django_strawberry_framework/exceptions.py::describe_value` (full read);
`django_strawberry_framework/utils/policies.py::copy_policy`,
`django_strawberry_framework/utils/policies.py::canonical_policy`,
`django_strawberry_framework/utils/policies.py::resolve_policy` (full reads);
`django_strawberry_framework/resource_policy.py::resolve_resource_policy` and
`django_strawberry_framework/error_policy.py::resolve_error_policy` (full reads,
precedence ladders);
`django_strawberry_framework/utils/private_state.py::PrivateAuthority` and
`django_strawberry_framework/utils/private_state.py::PrivateMembership` (full reads);
`django_strawberry_framework/utils/execution_mode.py::OperationMode`,
`django_strawberry_framework/utils/execution_mode.py::async_execution`,
`django_strawberry_framework/utils/execution_mode.py::operation_is_async` (full reads);
`django_strawberry_framework/utils/write_transaction.py::resolve_write_alias`,
`django_strawberry_framework/utils/write_transaction.py::managed_write_transaction`,
`django_strawberry_framework/utils/write_transaction.py::require_managed_write` (full reads);
`django_strawberry_framework/mutations/fields.py::MUTATION_CLASS_MARKER` (def plus
stamp line plus marker comment);
`django_strawberry_framework/extensions/operation_state.py::DjangoExtensionsRunner`,
`django_strawberry_framework/extensions/operation_state.py::_OperationModeMarker`,
`django_strawberry_framework/extensions/operation_state.py::_declared_operation_mode`
(def lines plus mode-carry docstrings);
`django_strawberry_framework/extensions/resource_policy.py::DjangoResourcePolicyExtension`
(init plus `_policy` plus `_mutation_input_specs` marker tail),
`django_strawberry_framework/extensions/resource_policy.py::_AdmissionGuard` (full read),
`django_strawberry_framework/extensions/resource_policy.py::restate_admission_verdict`
(full read);
`django_strawberry_framework/extensions/error_policy.py::DjangoErrorPolicyExtension`
(class line plus install-position docstring);
`django_strawberry_framework/scalars.py::strawberry_config` (full read, converter
absence witness);
`django_strawberry_framework/conf.py` resource/error key comments (ladder
outranks lines);
`examples/fakeshop/config/schema.py` (full read, 82 lines, composition);
`tests/test_schema.py` (full read, 2262 lines, every oracle row);
live-tier heads plus composition full read
(`test_resource_policy_api.py` head, `test_error_policy_api.py` head,
`test_extension_isolation_api.py` head, `test_mutation_atomicity.py` head,
`test_schema_composition_api.py` full 126 lines);
upstream `.venv` `strawberry/schema/schema.py::Schema.get_extensions` and
`strawberry/schema/schema.py::Schema._stream` (bodies read),
`graphql/execution/execute.py::ExecutionContext.execute_field` (body read,
resolve-plus-complete contract),
`graphql/execution/execute.py::ExecutionContext.__init__` (`errors` list shape,
no `collected_errors` on the installed release).

Excluded with reason: the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) — never touched, not in this finding's sites;
concurrent dirt (`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) — left untouched, none in this item's paths
(schema.py clean vs both baselines);
in-flight spec bodies behind the module docstrings' Decision pointers
(spec-036 one-worker boundary, spec-047 resource policy, spec-048 error
policy — cited as pointers, defaults pinned by oracles instead);
`docs/GLOSSARY.md` schema entries (projections, not relied upon);
optimizer/list/connection bodies beyond the cited def lines (family items'
surface; this item traces the schema-side consumer role only).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor was checked for
its own spelling of this file's rules. No list / connection / mutation /
form / rest_framework surface defines a schema class, an execution context,
an admitted/refused chain, a refusal document, or an enforcement record.
Package-wide sweeps (probe §§12–14 plus §11): `class DjangoSchema(` once,
`class DjangoMutationExecutionContext(` once, `def _admitted_chain(` once,
`def _refused_chain(` once, `class _AsyncAliasLock:` once,
`class _AcquireHandoff:` once, `class _SchemaEnforcement:` once,
`class _RefusedConfiguration(` once, `def _refuse_operation_document(` once,
`def _consumer_extension_entries(` once, `def _is_extension(` once,
`def _claimed_authority(` once, `def _operation_mode(` once,
`def _stream(` once (this file's override of upstream). Shared seams are
composed by name, never respelled: `MUTATION_CLASS_MARKER` imported once
here plus once in `extensions/resource_policy.py` (J1, rejected as upstream
traversal, not a package rule); `DjangoErrorPolicyExtension` /
`DjangoResourcePolicyExtension` / `_AdmissionGuard` imported and constructed
fresh per operation (R4); `DjangoExtensionsRunner` / `_OperationModeMarker`
imported and built per operation (R6); `resolve_resource_policy` /
`resolve_error_policy` each called once here (consumers of the shared
`resolve_policy` driver — nothing to consolidate here); `copy_policy` called
twice here (the two copy-per-read properties, consumers of one body).
The `SCHEMA_CONFIGURATION_ERROR_CODE` definition lives once here; its only
other production hits are the `__init__.py` re-export lines (consumers,
listed never counted). No second definition of any schema rule exists
outside this file.

**2. Sync/async twins.** Three colored pairs touch this target, all compared
by behavior, not shape:
(a) `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_sync`
vs `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`
— share `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._rollback_for_new_errors`,
`managed_write_transaction`, and the `atomic` enter/exit vocabulary
verbatim; differ only in WHERE the atomic runs (calling thread vs
`run_in_one_sync_boundary` worker) and where the completion await sits
(inside `super().execute_field` vs between enter and exit on the loop).
Upstream `ExecutionContext.execute_field` was read: sync completion happens
inside the call, async completion returns an awaitable — so the split is the
recorded principle-5 shape (one window, two execution adapters, because the
ORM must not interleave with awaits inside the transaction and the async
window must hold the worker's connection across the await). No behavioral
divergence beyond the documented thread/await placement (static review of
both bodies plus upstream body).
(b) `django_strawberry_framework/schema.py::_AsyncAliasLock.__aenter__` vs
`__aexit__` — acquire-with-handoff vs release; the cancellation hand-off
(`_AcquireHandoff.acquired` / `.abandon`) is the exact-once ownership rule,
both sides read in full.
(c) `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`
`sync=True` vs `sync=False` — one flag, one
`django_strawberry_framework/schema.py::_operation_mode` body, admitted and
refused chains both threading it behind both authorities (probe §§7–8).
No twin drifts; the async window's three `run_in_one_sync_boundary` calls
are three uses of one body (F1), not three definitions.

**3. Derived rather than repeated knowledge.** Four facts this file could
have respelled are derived once from their owner instead: the write alias
comes from `resolve_write_alias(model)`, never from `router.db_for_write`
inline (one call site); the mode comes from the `sync` flag upstream passed,
never from sampling the ambient loop (one `_operation_mode` body — the
docstring records why the loop disagrees inside a nested sync call); the
policy objects come from `resolve_*_policy` plus `copy_policy` per read,
never from reading settings or spelling defaults inline (probe §6: one
`resolve_resource_policy(` call, one `resolve_error_policy(` call, two
`return copy_policy(` lines); the mutation class comes from the imported
`MUTATION_CLASS_MARKER` constant, never from a respelled string (one
`MUTATION_CLASS_MARKER, None)` read). The `strawberry-definition` extension
key appears here as a literal while `extensions/resource_policy.py` holds it
as `_STRAWBERRY_DEFINITION_BACKREF` — both consume upstream Strawberry's key,
neither owns it (J1). No reconstructed copy found.

**4. Inverse / round-trip pairs.** Four grammars, each with one owner, both
halves composed here by name: settle/recall
(`_SCHEMA_ENFORCEMENT.settle` twice — construction record plus
extensions-settled flag — vs `recall` once plus `settled` once; probe §10);
accept/recall (`_SCHEMA_EXTENSIONS.accept` once vs `recall` twice);
admit/refuse (`_admitted_chain` vs `_refused_chain`, same four authorities,
refusal in place of the consumer middle); parse/refuse
(`_REFUSAL_DOCUMENTS` three pre-parsed constants vs
`_refuse_operation_document` selection plus `_provided_operation_name`
clearing). The `extensions` setter accepts once and refuses thereafter; the
`get_extensions` resolver reads once per operation through upstream and
checks what came back without calling a factory a second time (oracle pins
the single-call count). No second grammar lives here.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); oracles that spell literals directly —
`tests/test_schema.py` (construction shapes, hostile `__class__` /
metaclass / `__bool__` rows, subclass/hybrid refusals, lock-identity row,
rollback probe rows with hostile `len`, factory-count row, wire-code
absence rows, one-shot/hostile-bool policy rows, substitute-document rows,
slotted-factory rows, GC rows) plus the live tier
(`test_resource_policy_api.py` kwarg/setting/narrowing rows,
`test_error_policy_api.py` masking matrix plus copy-attribute row,
`test_extension_isolation_api.py` wire-refusal plus still-bounded rows,
`test_mutation_atomicity.py` completion-rollback rows,
`test_schema_composition_api.py` manifest plus per-app introspection rows,
`config/schema.py` optimizer-singleton-factory composition);
projections (module/class/function docstrings, spec Decision pointers).
Every oracle checked spells its expectation independently (the wire code,
the chain order, the probe-row absence, the `tuple`-exact snapshot) and
would fail, not follow, a production change. The `__init__.py` re-export of
`SCHEMA_CONFIGURATION_ERROR_CODE` is an assignment re-export, not a copy.

**6. Enforcement by omission.** Three member-by-member checks.
(a) Mutation window: only TOP-LEVEL generated mutation fields are wrapped
(`_marked_mutation_class` returns `None` for non-mutation parents, empty
nodes, introspection, unmarked fields, non-dict parents — each pinned by a
`test_marked_mutation_class_safe_*` row). Queries, consumer-written
mutations, and nested payload fields execute as stock graphql-core by
construction. No member lacks a guard its contract requires.
(b) Chain admission: every resolved member is typed (`_is_extension`) and
authority-checked (`_claimed_authority`); every entry is resolvability-checked
at construction (`_is_resolvable_extension_entry`); a factory product is
typed at resolution (factory-count oracle pins single-call). No entry shape
passes without a check.
(c) Refusal: all three `OperationType` values have a substitute document
(probe §8); the empty-policy case stays refusing (upstream-error oracle
pins it); the one-shot policy is snapshotted once into an exact `tuple`
(oracle pins `type(...) is tuple` plus single traversal); `__bool__` never
runs (hostile-bool oracle pins it). No operation type or policy shape lacks
its refusal path.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **55 top-level statements** — plus, better than the minimum,
every method of the six classes (3 + 4 + 6 + 0 + 5 + 8 = 26). Every member
lands below; every challenge in `### Challenges` ends in a family row, a
file-local record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (atomicity contract + sync/async split + serial-mutation independence + marker scope) | (none) | projection (R1/R2) |
| 1 | `from __future__ import annotations` | annotations | machinery |
| 2 | `import asyncio` | `asyncio` | machinery (R2 `to_thread`/`shield`) |
| 3 | `import threading` | `threading` | machinery (R2 locks/guards) |
| 4 | `from collections.abc import Iterator, Mapping` | `Iterator`, `Mapping` | machinery (R4/R5 signatures) |
| 5 | `from dataclasses import dataclass, replace` | `dataclass`, `replace` | machinery (R3 record + flag) |
| 6 | `from typing import Any` | `Any` | machinery |
| 7 | `import strawberry` | `strawberry` | machinery (R3 base) |
| 8 | `from django.db import transaction` | `transaction` | machinery (R1 atomic) |
| 9 | `from graphql import GraphQLError, parse` | `GraphQLError`, `parse` | machinery (R5 refusal) |
| 10 | `from graphql.execution.execute import ExecutionContext` | `ExecutionContext` | machinery (R1 base) |
| 11 | `from strawberry.extensions.base_extension import SchemaExtension` | `SchemaExtension` | machinery (R4/R5 checks) |
| 12 | `from strawberry.types.graphql import OperationType` | `OperationType` | machinery (R5 docs) |
| 13 | `from . import logger` | `logger` | consumer (refusal log line; owner `__init__.py::logger`) |
| 14 | `from .error_policy import DEFAULT_ERROR_POLICY, ErrorPolicy, resolve_error_policy` | policy ladder | consumer (R3; driver `resolve_policy`) |
| 15 | `from .exceptions import ConfigurationError, describe_value` | guard + renderer | consumer (F2; R4 raises) |
| 16 | `from .extensions.error_policy import DjangoErrorPolicyExtension` | masking authority | consumer (R4) |
| 17 | `from .extensions.operation_state import DjangoExtensionsRunner, _OperationModeMarker` | runner + marker | consumer (R6/R4) |
| 18 | `from .extensions.resource_policy import DjangoResourcePolicyExtension, _AdmissionGuard` | budget authority + guard | consumer (R4) |
| 19 | `from .mutations.fields import MUTATION_CLASS_MARKER` | marker constant | consumer (R1; J1) |
| 20 | `from .resource_policy import DEFAULT_RESOURCE_POLICY, ResourcePolicy, resolve_resource_policy` | policy ladder | consumer (R3; driver `resolve_policy`) |
| 21 | `from .utils.execution_mode import OperationMode, async_execution` | mode fact + dispatch | consumer (R1/R4) |
| 22 | `from .utils.policies import copy_policy` | copy primitive | consumer (R3) |
| 23 | `from .utils.private_state import PrivateAuthority, PrivateMembership` | storage primitives | consumer (R3) |
| 24 | `from .utils.querysets import run_in_one_sync_boundary` | one-boundary primitive | consumer (F1) |
| 25 | `from .utils.write_transaction import managed_write_transaction, resolve_write_alias` | write seam + alias | consumer (R1) |
| 26 | `class _AcquireHandoff` (26.1 `__init__`, 26.2 `acquired`, 26.3 `abandon`) | cancel hand-off | R2, file-local |
| 27 | `class _AsyncAliasLock` (27.1 `__init__`, 27.2 `_acquire_for`, 27.3 `__aenter__`, 27.4 `__aexit__`) | cross-loop mutex | R2, file-local |
| 28 | `_ASYNC_MUTATION_LOCKS: dict[str, _AsyncAliasLock] = {}` | per-alias store | R2, file-local |
| 29 | `_ASYNC_MUTATION_LOCKS_GUARD = threading.Lock()` | store guard | R2, file-local |
| 30 | `def _async_mutation_lock(alias)` | per-alias accessor | R2, file-local |
| 31 | `class DjangoMutationExecutionContext` (31.1 `execute_field`, 31.2 `_marked_mutation_class`, 31.3 `_execution_errors`, 31.4 `_rollback_for_new_errors`, 31.5 `_execute_mutation_field_sync`, 31.6 `_execute_mutation_field_async`) | completion window | R1, file-local |
| 32 | `SCHEMA_CONFIGURATION_ERROR_CODE = "SCHEMA_CONFIGURATION_UNAVAILABLE"` | wire code | R5, file-local |
| 33 | `@dataclass(frozen=True) class _SchemaEnforcement` (`resource_policy`, `error_policy`, `extensions_settled`) | enforcement record | R3, file-local |
| 34 | `_SCHEMA_ENFORCEMENT: PrivateAuthority[_SchemaEnforcement] = PrivateAuthority()` | record authority | R3, file-local |
| 35 | `_SCHEMA_EXTENSIONS: PrivateMembership[Any] = PrivateMembership("_django_extensions")` | entry membership | R3, file-local |
| 36 | `_FALLBACK_ENFORCEMENT = _SchemaEnforcement(...)` | unconstructed answer | R3, file-local |
| 37 | `def _enforcement(schema)` | record read | R3, file-local |
| 38 | `_UNREADABLE_CONFIGURATION = (...)` | refusal message | R5, file-local |
| 39 | `_UNRESOLVED_CHAIN = (...)` | refusal message | R5, file-local |
| 40 | `_REFUSAL_DOCUMENTS = {QUERY/MUTATION/SUBSCRIPTION}` | substitute docs | R5, file-local |
| 41 | `def _refuse_operation_document(execution_context)` | doc/name/policy snapshot | R5, file-local |
| 42 | `class _RefusedConfiguration` (42.1 `__init__`, 42.2 `on_parse`, 42.3 `on_validate`, 42.4 `on_execute`, 42.5 `_refusal`) | refusal extension | R5, file-local |
| 43 | `def _refused_chain(message, reason, *, sync)` | refused chain | R4, file-local |
| 44 | `def _operation_mode(*, sync)` | executor fact | R4, file-local |
| 45 | `class DjangoSchema` (45.1 `__init__`, 45.2 `extensions` getter, 45.3 `extensions` setter, 45.4 `resource_policy`, 45.5 `error_policy`, 45.6 `get_extensions`, 45.7 `create_extensions_runner`, 45.8 `_stream`) | schema surface | R3 (45.1–45.5) / R4 (45.6) / R6 (45.7–45.8), file-local |
| 46 | `def _is_resolvable_extension_entry(entry)` | entry shape | R4, file-local |
| 47 | `def _is_extension(extension, extension_type)` | resolved-member test | R4, file-local |
| 48 | `def _claimed_authority(member)` | resolved claim | R4, file-local |
| 49 | `def _admitted_chain(resolved, *, sync)` | admitted chain | R4, file-local |
| 50 | `def _consumer_extension_entries(extensions)` | entry split + fold | R4, file-local |
| 51 | `def _declared_authority(entry)` | entry declaration | R4, file-local |
| 52 | `def _entry_resource_policy(entry)` | entry policy read | R4, file-local |
| 53 | `def _entry_type(entry)` | entry class read | R4, file-local |
| 54 | `def _extension_entry_matches(extension, extension_type)` | entry match w/o factory call | R4, file-local |

Rules: F1 `one-sync-boundary` and F2 `typed-rejection-value-tail` reuse
the plan's existing family names (schema-side roles re-challenged fresh,
not inherited); R1–R6 are file-local (each counts 1 with no second
definition site — challenges below); J1–J4 are recorded rejections with
contract differences + triggers. The plan's `## Responsibility index`
already carries F1 and F2 with this file listed — reused, not renamed. No
new family is named: the marker-tail (J1), exact-type idiom (J2),
pre-execution publishing (J3), and converter/boundary/raw-body (J4)
considerations each refuse the shared form for the recorded reasons.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | F1 boundary kind | third awaitable kind needs disposal inside the async window | **1** (`utils/querysets.py::run_in_one_sync_boundary` owner; this file's three `await` sites follow as consumers) | consumer |
| C2 | F1 discipline | boundary must stop being `thread_sensitive=True` single-worker | **1** (same owner; the async enter/exit/clean wrappers follow) | consumer |
| C3 | F2 tail grammar | tail must carry a new fragment (e.g. value length) | **1** (`exceptions.py::describe_value`; this file's five call sites follow) | consumer |
| C4 | F2 hostile value | new hostile shape (raising `__repr__`, int-digit bomb, raising type name) | **1** (same owner; the factory-exception oracles move) | consumer |
| C5 | R1 error container | graphql-core ships a third error-container shape | **1** (`_execution_errors` arms; the before/after length rule follows) | file-local |
| C6 | R1 dispatch | new executor (e.g. sync-from-loop must refuse, not guess) | **1** (`execute_field` `async_execution()` branch; the mode readers follow) | file-local |
| C7 | R1 scope | wrap nested generated fields too, not top-level only | **1** (`_marked_mutation_class` parent/root/nodes/fields arms move together) | file-local |
| C8 | R2 granularity | serialize per model, not per alias | **1** (`_async_mutation_lock` store + guard move together; the acquire/release bodies follow) | file-local |
| C9 | R2 cancellation | hand-off must survive a third ordering (e.g. teardown-cancel) | **1** (`_AcquireHandoff` acquired/abandon pair) | file-local |
| C10 | R3 third authority | a third enforcement kind joins the record | **1** (`_SchemaEnforcement` fields + settle sites + properties move together, one file) | file-local |
| C11 | R3 tamper | new write shape (`__dict__` clear, attribute delete, carrier swap) | **1** (no attribute answers with the record; the `__dict__`-content census oracle moves) | file-local |
| C12 | R4 entry shape | new resolvable shape (e.g. async factory) | **1** (`_is_resolvable_extension_entry` + `get_extensions` single-call rule move together) | file-local |
| C13 | R4 claim | third claim kind (new enforcement role) | **1** (`_claimed_authority` resolved half + `_declared_authority` entry half: one rule in two functions, same file) | file-local |
| C14 | R4 order | swap the error-first / resource-last positions | **1** (`_admitted_chain` list; the install-position oracles move) | file-local |
| C15 | R5 operation type | fourth operation type needs a substitute | **1** (`_REFUSAL_DOCUMENTS` map + snapshot selection move together) | file-local |
| C16 | R5 policy read | transport policy gains a new hostile shape (e.g. raising `__iter__`) | **1** (`_refuse_operation_document` one-read-no-truthiness snapshot) | file-local |
| C17 | R5 wire code | rename the configuration code | **1** (the constant; the wire-code oracles move) | file-local |
| C18 | R6 runner | subclass builds a non-package runner | **1** (`_stream` `issubclass(type(...), DjangoExtensionsRunner)` passthrough) | file-local |
| C19 | R6 resume | streamed frames need a new binding (e.g. new lease kind) | **1** (`create_extensions_runner` + `_stream` wrapper move together) | file-local |
| C20 | J1–J4 | the four refused shared forms (marker tail, exact-type idiom, pre-execution shape, converter/boundary/raw-body) | **0 moves — refused**, differences + triggers in findings | refused |

**Experiment.** Read-only probe (no source mutation, no SQL, no Django
setup, no shared-tree pytest — the workspace recipe is for mutating proofs,
of which this item has none):

```shell
uv run python docs/dry/temp-tests/dry-file-schema/probe_w1.py
```

Output (`ALL OK`, 54 checks): 55-member module AST with kinds (probe
§§1–2); six classes with exact method lists plus fourteen top-level funcs
plus nine assigns (§§3–5); five `describe_value(` sites, three
`await run_in_one_sync_boundary(` sites, two managed-write sites, one
alias/mode/resolve site each, two `copy_policy` reads (§6); admitted vs
refused chain orders verbatim (§7); three refusal documents (§8); seven
absence claims (§9: no `SCALAR_MAP`, no `strawberry_config`, no
`_BOUNDARY_METHOD`, no `_RawBodyRequestAdapter`, no
`require_optional_module`, no `MAX_REQUEST_BODY_BYTES`, no
`_PACKAGE_SCALAR_MAP` in the target); settle/recall/accept balance (§10);
population 117 `.py` files (§11); fourteen single-definition sweeps plus the
two owner-side singletons (§12). One first-draft check failed on probe
precision (enforcement `recall` is once, not twice — `settled` is the
second read) and was corrected to the body — re-verified green, substance
unaffected. Status: `execution-verified` for every identity/count/shape/
absence claim below. Rejects the wrong results "a second schema/context/
chain/refusal definition lives elsewhere", "the target drifted from its
baseline", "a converter/boundary/body surface lives here".

## Findings

No production edit is owed by a file item; the two families below are REUSED
from the plan (schema-side roles re-challenged fresh), the rest are
file-local records and four recorded rejections.

### F1 — one sync boundary (existing family `one-sync-boundary`, stays `open`)

- **Contract + variation.** Every async surface that must keep sync ORM work
off the event loop runs it in exactly one
`sync_to_async(thread_sensitive=True)` worker. Legitimate variation: which
callable is wrapped per seam (permission check, filter body, write pipeline,
session auth, mutation-window enter/exit).
- **Sites + roles.** *Definition*:
`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`
(single `async def`, owner side; family item's surface). *Consumers here*:
`django_strawberry_framework/schema.py::_execute_mutation_field_async` — three
`await` sites (atomic enter, error-exit, clean-exit) sharing the worker the
pipeline's queries run on, so open/pipeline/close share one thread and one
Django connection (probe §6). *Sibling consumers* (listed, never counted):
`auth/mutations.py` (4 sites), `permissions.py`, `orders/sets.py`,
`filters/sets.py`, `mutations/resolvers.py`, `types/resolvers.py`,
`testing/client.py` (per the plan index). *Oracles*: the async-window
hostile-container row plus the async exception-rollback row in
`tests/test_schema.py` (both drive through the worker; bodies read).
*Projections*: the one-boundary docstrings at both ends.
- **Challenges.** C1, C2 → 1 each, both at the querysets owner; zero
definitions here.
- **Owner + lifetime.** `utils/querysets.py::run_in_one_sync_boundary`
(unchanged). No stored derivation here (each `await` is call-local).
- **Migration.** None (zero-edit item; consumer role only).
- **Distinct behavior.** The three window calls are not three boundaries by
accident: enter, error-exit, and clean-exit must each run on the same
thread-sensitive worker as the pipeline, or the transaction opens on one
connection and closes on another. A per-step hop would still be "one worker
per call" and would break atomicity — which is why the discipline is one
worker per resolution, stated at the owner.
- **Behavioral proof.** `static-reviewed` for the consumer role (import plus
three call sites plus both window bodies read; upstream `execute_field`
confirms the await must sit between enter and exit); `execution-verified`
for the import/call census (probe §6). Rejects "this file defines its own
boundary".
- **Structural gate.** The existing async-window oracles (hostile-container
rollback without leaking the transaction; async crash rollback). Negative
control: replacing one `await run_in_one_sync_boundary(...)` with a direct
call passes every sync oracle and fails exactly the async rows (event-loop
ORM refusal / wrong-connection close).
- **Coupling.** None.
- **Freshness.**
`django_strawberry_framework/schema.py`
`2f72732123ca1156c4eb122ce7b53de6269de95e`,
`django_strawberry_framework/utils/querysets.py`
`1539b66c9ce9a659e1dc5f6bf1029b15d6868587` (owner def lines only),
`tests/test_schema.py`
`57fa76782f02aabcbb86c5667d62c5f89f0c4e82` (async-window oracle bodies only).

### F2 — typed rejection value tail (existing family `typed-rejection-value-tail`, stays `open`)

- **Contract + variation.** Every typed rejection on a deployment-supplied
value renders its tail through one never-raising renderer, so the message
assembly cannot replace the promised error. Legitimate variation: which
rejection prose each seam carries; the tail grammar itself does not vary.
- **Sites + roles.** *Definition*:
`django_strawberry_framework/exceptions.py::describe_value` (owner side).
*Consumers here*: five call sites in this file — the unresolvable-entry
refusal, the factory-raised containment, the two resolved-member refusals,
and the subclass-declaration refusal (probe §6 counts five). *Sibling
consumers* (listed, never counted): `views.py`, `routers.py`,
`error_policy.py`, `resource_policy.py`, `extensions/debug.py`,
`utils/policies.py`, `utils/sessions.py`, `consumers.py`, `list_field.py`
(per sweeps plus the plan index). *Oracles*: the factory-exception rows
(ordinary / raising-`__repr__` / raising-arg / raising-type-name) in
`tests/test_schema.py`, each asserting the wire message stays the constant
(bodies read). *Projections*: the renderer docstring's scope clause (which
explicitly names the transport-boundary plus schema-construction policy
rejections as the routed population).
- **Challenges.** C3, C4 → 1 each, both at the exceptions owner; zero
definitions here.
- **Owner + lifetime.** `exceptions.py::describe_value` (unchanged). No
stored derivation here.
- **Migration.** None.
- **Distinct behavior.** The five sites share the tail but not the prose:
each names its own object/population (entry, factory exception, member,
subclass) while the tail stays byte-identical in shape. Changing one
sentence moves one site; changing the tail moves the owner.
- **Behavioral proof.** `static-reviewed` for the consumer role (five call
sites read; owner body read); `execution-verified` for the five-count
census (probe). Rejects "this file renders a tail of its own".
- **Structural gate.** The existing hostile-renderer oracles (a raising
`__repr__`/`__str__`, a raising argument, a raising type name each still
refuse with the stable code). Negative control: interpolating one site with
`{exc!r}` passes every happy-path oracle and fails exactly the hostile
rows for that site.
- **Coupling.** None.
- **Freshness.** Target as in F1 +
`django_strawberry_framework/exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` (owner def only) +
`tests/test_schema.py` as in F1.

### File-local records (no second definition after the matrix)

- **R1 — completion-spanning mutation window.**
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext`
(`execute_field`, `_marked_mutation_class`, `_execution_errors`,
`_rollback_for_new_errors`, `_execute_mutation_field_sync`,
`_execute_mutation_field_async`) plus the consumed alias/marker/mode/write
seams (C5, C6, C7 → 1 each). The two `managed_write_transaction` blocks are
two uses of one seam, not copies; the `resolve_write_alias` call is the one
router read per operation; the `async_execution()` branch is the one
dispatch. Upstream `execute_field` (read) confirms the sync/async placement:
sync completes inside the call so the atomic wraps it directly; async
returns an awaitable so the window must span the await on the worker. The
`_execution_errors` dual arms (`collected_errors.errors` vs `errors`) are
one compatibility rule in one function — the installed graphql-core carries
only the latter, the former is forward cover, both append-only so the
before/after length comparison holds on either. Trigger: a second
completion-spanning window (e.g. a subscription payload window) would make
it a family. Freshness: target +
`django_strawberry_framework/utils/write_transaction.py`
`eca9ad4d3f765964df05884e080eb3ea63190ca8` (seam defs only) +
`django_strawberry_framework/mutations/fields.py`
`cf518361d7884b8b71550cb6b73bff0c1a64549e` (marker def only) +
`django_strawberry_framework/utils/execution_mode.py`
`9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` (dispatch def only) +
`tests/test_schema.py` as in F1 +
`examples/fakeshop/test_query/test_mutation_atomicity.py`
`f0321799063f90eee9aba390d6a73dd6ff5c653a` (live rollback rows).
- **R2 — async alias serialization.**
`django_strawberry_framework/schema.py::_AcquireHandoff`,
`django_strawberry_framework/schema.py::_AsyncAliasLock`,
`django_strawberry_framework/schema.py::_async_mutation_lock`,
`django_strawberry_framework/schema.py::_ASYNC_MUTATION_LOCKS`,
`django_strawberry_framework/schema.py::_ASYNC_MUTATION_LOCKS_GUARD`
(C8, C9 → 1 each; the store plus guard plus accessor are one rule in three
statements, same file). Process-wide per-alias because the default
thread-sensitive executor is process-wide and separate loops share its
worker; distinct aliases stay independent. The hand-off (`acquired` vs
`abandon` under one guard, exactly one side releases) is the whole
cancellation contract — both orderings read in full. Trigger: a second
cross-loop mutation mutex would make it a family. Freshness: target +
`tests/test_schema.py` as in F1 (lock-identity + context-manager rows).
- **R3 — enforcement-record holding.**
`django_strawberry_framework/schema.py::_SchemaEnforcement`,
`django_strawberry_framework/schema.py::_SCHEMA_ENFORCEMENT`,
`django_strawberry_framework/schema.py::_SCHEMA_EXTENSIONS`,
`django_strawberry_framework/schema.py::_FALLBACK_ENFORCEMENT`,
`django_strawberry_framework/schema.py::_enforcement`,
`django_strawberry_framework/schema.py::DjangoSchema.__init__`,
`django_strawberry_framework/schema.py::DjangoSchema.extensions`,
`django_strawberry_framework/schema.py::DjangoSchema.resource_policy`,
`django_strawberry_framework/schema.py::DjangoSchema.error_policy`
(C10, C11 → 1 each; the record shape, the two stores, the fallback, the
settle/recall/accept balance in probe §10, the re-init and post-construction
setter refusals, and the two copy-per-read properties move together, one
file). The `resolve_*_policy` calls are consumers of the shared driver
(`utils/policies.py::resolve_policy` — already consolidates both ladders,
nothing owed here); the `copy_policy` reads are consumers of one body; the
`PrivateAuthority`/`PrivateMembership` uses are consumers of those owners.
The `error_policy.py` / `resource_policy.py` `schema.py::_SCHEMA_ENFORCEMENT`
mentions are prose citations (projections), not code. Trigger: a second
schema-held enforcement record would make it a family. Freshness: target +
`django_strawberry_framework/utils/private_state.py`
`08088b820ac20579e471915644a931953362fca8` (primitive defs only) +
`django_strawberry_framework/utils/policies.py`
`860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e` (driver defs only) +
`django_strawberry_framework/resource_policy.py`
`647133d23785d325856b2d1d495d18c5741dd23c` (ladder def only) +
`django_strawberry_framework/error_policy.py`
`fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91` (ladder def only) +
`django_strawberry_framework/conf.py`
`c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` (outranks comments only) +
`tests/test_schema.py` as in F1 (record/GC/copy/tamper rows).
- **R4 — chain admission.**
`django_strawberry_framework/schema.py::DjangoSchema.get_extensions`,
`django_strawberry_framework/schema.py::_admitted_chain`,
`django_strawberry_framework/schema.py::_refused_chain`,
`django_strawberry_framework/schema.py::_consumer_extension_entries`,
`django_strawberry_framework/schema.py::_declared_authority`,
`django_strawberry_framework/schema.py::_entry_resource_policy`,
`django_strawberry_framework/schema.py::_entry_type`,
`django_strawberry_framework/schema.py::_extension_entry_matches`,
`django_strawberry_framework/schema.py::_is_resolvable_extension_entry`,
`django_strawberry_framework/schema.py::_is_extension`,
`django_strawberry_framework/schema.py::_claimed_authority`,
`django_strawberry_framework/schema.py::_operation_mode`
(C12, C13, C14 → 1 each; the entry halves (`_declared_authority` at
construction vs `_claimed_authority` at resolution) are one claim rule in
two functions, same file — a factory is opaque until called, so the check
splits by lifecycle, not by authority). Error-first / resource-last /
guard-behind-consumers / marker-behind-guard is the contract both chains
share (probe §7 orders verbatim); the refused chain keeps both package
authorities and drops every consumer hook (refusal-still-bounded oracle
pins it). Exact-type (`type()` / `issubclass(type(...))`) throughout is the
hostile-`__class__` posture, stated at each body. Trigger: a second chain
builder (e.g. a subscription-only chain) would make it a family.
Freshness: target +
`django_strawberry_framework/extensions/operation_state.py`
`b2674a22d2dfd58ff97c51a02e16068bb22032e9` (marker/runner defs only) +
`django_strawberry_framework/extensions/resource_policy.py`
`52084078ac166d8116b9e4bb2522e8ce193251ea` (authority/guard defs only) +
`django_strawberry_framework/extensions/error_policy.py`
`baea073f5615aaddc82c1f463071998bee7a6b62` (authority def only) +
`tests/test_schema.py` as in F1 (chain-order, factory-count, hybrid,
slotted, lying-class rows) +
`examples/fakeshop/test_query/test_extension_isolation_api.py`
`6901fd034c365bed2fd76799da1129135613c879` (live wire-refusal rows) +
`examples/fakeshop/test_query/test_resource_policy_api.py`
`94d9d079ced496c41e66dafd0384e7b5819b31d6` (chain-behavior rows) +
`examples/fakeshop/test_query/test_error_policy_api.py`
`5dbcf2013f98b10567b0dc8efddd9705141fa6c7` (masking-position rows).
- **R5 — refusal substitution.**
`django_strawberry_framework/schema.py::SCHEMA_CONFIGURATION_ERROR_CODE`,
`django_strawberry_framework/schema.py::_REFUSAL_DOCUMENTS`,
`django_strawberry_framework/schema.py::_refuse_operation_document`,
`django_strawberry_framework/schema.py::_RefusedConfiguration`,
`django_strawberry_framework/schema.py::_UNREADABLE_CONFIGURATION`,
`django_strawberry_framework/schema.py::_UNRESOLVED_CHAIN`
(C15, C16, C17 → 1 each; the three documents, the one-read snapshot, the
name clearing, and the parse/validate/execute triple move together, one
file). The documents are parsed once at import so no refused request runs
a parser (no-parser oracle pins `parsed == []`); the policy snapshot is an
exact `tuple` put back on the context so upstream reads the same fact
(oracle pins `type(...) is tuple` plus single traversal); `__bool__` never
runs (hostile-bool oracle pins it). The wire carries only the stable code;
the reason stays in the deployment log (`logger.error` line). Trigger: a
second refusal substitution (e.g. a transport-level refusal) would make it
a family. Freshness: target + `tests/test_schema.py` as in F1 (every-
document, every-name, one-shot, no-parser, no-`__bool__`, no-representation
rows).
- **R6 — streamed-operation binding.**
`django_strawberry_framework/schema.py::DjangoSchema.create_extensions_runner`,
`django_strawberry_framework/schema.py::DjangoSchema._stream`
(C18, C19 → 1 each; the runner factory plus the resume wrapper move
together, one file). The narrowest seam already receiving the exact runner
and the raw iterator; a non-package runner passes through untouched
(upstream-runner oracle pins both halves). The mode marker travels in the
chain the runner reads, so refused and admitted streams bind identically.
Trigger: a second streamed-binding wrapper would make it a family.
Freshness: target +
`django_strawberry_framework/extensions/operation_state.py` as in R4
(runner/resume defs only) + `tests/test_schema.py` as in F1 (streamed-
refusal + foreign-runner rows).

### J1 — marker-tail read (rejection, not a family)

`django_strawberry_framework/schema.py::DjangoMutationExecutionContext._marked_mutation_class`
tail (`extensions["strawberry-definition"].base_resolver.wrapped_func` plus
`MUTATION_CLASS_MARKER` getattr) vs
`django_strawberry_framework/extensions/resource_policy.py::_mutation_input_specs`
tail (same three reads plus `_input_field_specs` map). Considered shared
form: one `mutation_cls_for_field_def(field_def)` helper owned by
`mutations/fields.py`. Contract differences: the schema tail answers "does
this TOP-LEVEL execution open a transaction window" (needs parent-type,
field-nodes, introspection, and non-dict guards around the tail); the
resource tail answers "what spec map classifies this walker's field's
input lists" (needs the bind-time specs map after the tail, `None` for
every non-generated field). A change to either head (nested-field scope vs
relation-vs-membership classification) moves exactly one body; the shared
three lines consume upstream Strawberry's extension storage plus the
imported marker constant — upstream idiom, not a package rule. Posit the
upstream key rename → both move, but that change is upstream's, counted at
neither owner. Reconsideration trigger: a third field_def-to-marker reader
arriving with the same tail and neither head (then the tail becomes the
shared rule with this finding as its seed). Durable home: this finding (a
file item lands no edit).

### J2 — exact-type idiom (rejection, not a family)

`django_strawberry_framework/schema.py::_is_extension` /
`django_strawberry_framework/schema.py::_entry_type` /
`django_strawberry_framework/schema.py::_extension_entry_matches` (hostile-
`__class__` posture for the chain) vs
`django_strawberry_framework/extensions/operation_state.py::_is_operation_bound`
(same `issubclass(type(...))` posture for runner binding, explicitly citing
the schema predicate as precedent). Considered shared form: one
`is_exact_type(obj, cls)` helper. Contract differences: different predicates
(chain membership vs runner binding), different refused outcomes (operation
refusal vs missing-binding `ConfigurationError`), independent retirement
(C12/C13 move the chain halves alone; a runner-binding change moves the
operation-state predicate alone). The shared token is Python `type()`
idiom, not a package rule (the conf C31 precedent). Reconsideration
trigger: a mechanism change (e.g. a third hostile-metadata shape the idiom
must cover) touching three or more predicates at once. Durable home: the
per-site docstrings (each already records the `__class__` reason) plus this
finding.

### J3 — pre-execution-error publishing shape (rejection, not a family)

`django_strawberry_framework/schema.py::_RefusedConfiguration` (`on_parse` /
`on_validate` publishing `[refusal]`, `on_execute` raising) vs
`django_strawberry_framework/extensions/resource_policy.py::restate_admission_verdict`
plus `DjangoResourcePolicyExtension` charging hooks (publishing
`[rejection]`, restating behind consumers, raising at execute). Considered
shared form: one `publish_rejection(context, error)` helper. Contract
differences: refusal (configuration broken, nothing runs, still bounded by
the package's own resource extension) vs admission (over-budget document,
nothing runs, verdict recorded in the budget lease for later stages to
read); different triggers, different messages, different verdict stores
(record vs lease). The shared field name
(`ExecutionContext.pre_execution_errors`) is upstream graphql-core's
contract, not a package rule — both compose it, neither defines it.
Reconsideration trigger: upstream renames the field or splits the seam
(then both call sites move as consumers of one upstream change, still not
a package family). Durable home: both modules' docstrings (each already
records why publishing vs raising) plus this finding.

### J4 — converter / boundary / raw-body surfaces (inapplicable, not families)

Three candidates the plan item named with question marks, each checked fresh
and refused as inapplicable to this target (probe §9 absences, §12 sweeps):
(a) `converter-table-per-surface-ownership` — the rule owns per-surface
scalar tables (`types/converters.py::SCALAR_MAP`,
`scalars.py::_PACKAGE_SCALAR_MAP`, `forms/converter.py`,
`rest_framework/serializer_converter.py`); this target holds no table, maps
no field, and calls neither `strawberry_config()` nor any converter
(`strawberry_config` absent here; `SCALAR_MAP` absent here). A new scalar
moves zero definitions here.
(b) `request-body-boundary-protocol-marks` — the rule owns mark constants in
`_boundary_ordering.py` with writers/readers in `views.py` /
`middleware/request_body.py`; this target holds no mark and enforces no
boundary (`_BOUNDARY_METHOD` absent here).
(c) `sync-adapter-raw-body-source` — the rule owns the process-vs-mount body
source split (`_cross_web_patches.py::_patched_body` vs
`views.py::_RawBodyRequestAdapter`); this target reads no body
(`_RawBodyRequestAdapter` absent here; `MAX_REQUEST_BODY_BYTES` absent
here). The `DjangoSchema(resource_policy=...)` outranks-setting ladder the
item description points at lives at the shared driver
(`utils/policies.py::resolve_policy`), consumed once per policy here (R3)
— already consolidated, nothing owed here. Reconsideration trigger for any
of the three: this file gaining a table/mark/body read it must keep in sync
with the owner. Durable home: this finding (probe absences are the gate).

## Defects

None. Every claim checked while tracing held: the 55/26 counts plus method
lists (probe §§1–5); the five-tail / three-boundary / two-write / one-alias /
one-dispatch / two-copy / one-resolve-each censuses (probe §6); both chain
orders verbatim (probe §7); three refusal documents (probe §8); seven
absences (probe §9); settle/recall/accept balance (probe §10); fourteen
single-definition sweeps (probe §12); the sync-inside / async-awaitable
upstream placement (upstream body read); the `errors`-only installed
container with forward-cover dual arms (upstream `__init__` read); the
copy-per-read discipline at both properties (bodies read); the one-shot
`tuple`-exact plus no-`__bool__` snapshot (oracle bodies read); the
`config/schema.py` optimizer-singleton-factory composition (full read). The
two known schema-adjacent ambiguities keep their existing homes: no new
unguarded member was found (matrix axis 6), and the J1/J2/J3 similarities
are recorded above as rejections with triggers, not as defects. Nothing
routed to any owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
whole-tree sweeps, command in `### Challenges`) already ran green against
the shared tree; they mutate no source and open no database, so no
workspace copy was owed and no `__file__`/DB `NAME` record applies. No
pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED` or
Postgres cell is owed: this artifact's claims (statement counts, import
census, absence/single-site facts, chain-order literals, baseline diff)
touch no database, alias, or dialect decision (`inapplicable by
construction` — the only DB-adjacent strings are the alias parameter name
threaded through the window, never resolved here; alias resolution itself
is owned at `resolve_write_alias`).

## Judgment

Backstop discharged: 55/55 `ast.Module.body` members enumerated plus all 26
class-body members, 20 challenges run, every rule terminating in the two
existing families it belongs to (`one-sync-boundary`, `typed-rejection-
value-tail` — triggers re-checked fresh, both stay open, no new row owed),
a file-local record with its proving challenge (R1–R6), or a recorded
rejection with difference + trigger + owner home (J1–J4) — no consolidation
owed, no defect found, no new family named. Zero-edit result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only
families this target touches are already indexed with this file listed; the
four refused shared forms live at their owner docstrings plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
43d4bfed53e37a7a9e33c4715a8765be87f44ef2 --
django_strawberry_framework/schema.py` is empty (0 bytes, re-measured after
the probe run); the working blob
`2f72732123ca1156c4eb122ce7b53de6269de95e` equals `HEAD:` — the target is
clean, so no hunk attribution was owed. Before touching any path, the
item-scoped paths were verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied. Dirt elsewhere left alone, not a stop. No
commit. Untracked scratch created (not tracked changes): this artifact
`docs/dry/dry-file-schema.md` and the read-only probe
`docs/dry/temp-tests/dry-file-schema/probe_w1.py` (`ALL OK`, 54 checks; no
source mutation, no DB, no shared-tree pytest). No ruff run owed (no
tracked `.py` edits; artifact is `.md` only; probe is untracked scratch).
No `__file__`/DB record (no workspace copy — no mutating proof exists).

## Independent verification (Worker 2)

Own trace, derived before reconciling with the findings above. Reading
order kept: AGENTS.md, DRY.md, worker-2.md, the plan item, the full
target (1236 lines, read in two passes), the item-scoped diff plus
`git status --short`, the probe, every consumer/owner site below, then
the findings.

Sites and roles I derive: the target DEFINES six rules and CONSUMES
the rest by name. R1 completion window
(`DjangoMutationExecutionContext` with its six methods plus the
`managed_write_transaction` / `resolve_write_alias` / `async_execution`
/ `MUTATION_CLASS_MARKER` seams) — definition here, one site.
R2 async alias serialization (`_AcquireHandoff`, `_AsyncAliasLock`,
`_ASYNC_MUTATION_LOCKS` plus guard, `_async_mutation_lock`) —
definition here, one site. R3 enforcement-record holding
(`_SchemaEnforcement`, `_SCHEMA_ENFORCEMENT`, `_SCHEMA_EXTENSIONS`,
`_FALLBACK_ENFORCEMENT`, `_enforcement`, `DjangoSchema.__init__`,
the `extensions` getter/setter, `resource_policy`,
`error_policy`) — definition here, one site; the `resolve_*_policy`
calls consume the shared `resolve_policy` driver and the property
reads consume `copy_policy`. R4 chain admission (`get_extensions`,
`_admitted_chain`, `_refused_chain`, `_consumer_extension_entries`,
`_declared_authority`, `_entry_resource_policy`, `_entry_type`,
`_extension_entry_matches`, `_is_resolvable_extension_entry`,
`_is_extension`, `_claimed_authority`, `_operation_mode`) —
definition here, one site. R5 refusal substitution
(`SCHEMA_CONFIGURATION_ERROR_CODE`, `_REFUSAL_DOCUMENTS`,
`_refuse_operation_document`, `_RefusedConfiguration`,
`_UNREADABLE_CONFIGURATION`, `_UNRESOLVED_CHAIN`) — definition
here, one site. R6 streamed binding (`create_extensions_runner`,
`_stream`) — definition here, one site. F1 one-sync-boundary:
definition at `utils/querysets.py::run_in_one_sync_boundary`
(single `async def`, body read), three consumers here (atomic
enter, error-exit, clean-exit). F2 typed tail: definition at
`exceptions.py::describe_value` (body read), five consumers here.
Owners I would choose: unchanged in every case — the boundary
primitive stays on its neutral substrate (read-side reuse without
a root-into-subpackage import, stated at its docstring), the tail
stays at the exceptions owner, R1–R6 stay file-local. Posited
changes and counts: third awaitable kind (1, owner), boundary
discipline change (1, owner), tail grammar extension (1, owner),
new hostile value shape (1, owner), third error-container shape
(1, `_execution_errors`), new executor (1, dispatch branch),
nested-field scope (1, marker guards), per-model granularity
(1, lock store), third cancellation ordering (1, hand-off pair),
third authority (1, record), new write shape (1, no-attribute
posture), new entry shape (1, entry halves), third claim kind
(1, two halves one file), chain reorder (1, list), fourth
operation type (1, map plus selection), new hostile policy shape
(1, snapshot), wire-code rename (1, constant). Reconciliation
vs W1: full agreement on every rule, role, count, and owner;
one nuance only (wire-code oracle note below), which changes
no count and names no second site.

Enumeration, member by member against my own AST dump: 55
module statements (1 docstring + 25 imports + 6 classes +
14 top-level functions + 9 assigns = 55) and 26 class-body
methods (3 + 4 + 6 + 0 + 5 + 8). Method lists match exactly
(`__init__`/`acquired`/`abandon`;
`__init__`/`_acquire_for`/`__aenter__`/`__aexit__`; the six
execution-context methods; none on the frozen record; the five
refusal methods; the eight schema methods with `extensions`
twice for getter/setter). Table rows 0–54 home every member;
no member unassigned. Matrix vs the real surface: axis 1 swept
package-wide (own sweep: each schema-side `class`/`def` token
hits once; `MUTATION_CLASS_MARKER` hits only its owner plus
two by-name consumers; the wire code hits only its definition
plus the `__init__.py` re-export); axis 2 compared by behavior
(sync-inside vs async-awaitable placement, acquire vs release,
one flag two chains); axis 3 confirmed derived (alias, mode,
policies, marker each read once from their owner); axis 4
confirmed paired by name (settle/recall, accept/recall,
admit/refuse, parse/refuse); axis 5 classified (oracles spell
chain order, tuple-exactness, and absence literally; see the
wire-code nuance); axis 6 checked member by member (marker
guards, admission typing, refusal paths — all present, body
read). No axis excused by an unsearched claim.

Counts plus roles: F1 1 definition plus 3 consumers here;
F2 1 definition plus 5 consumers here; sibling consumers
listed never counted. No oracle rewritten in this item
(zero edits). One accuracy nuance on the findings prose:
the `tests/test_schema.py` wire-code rows compare against
the imported `SCHEMA_CONFIGURATION_ERROR_CODE` constant, so
a pure value rename is pinned literally only once in the
wider population
(`tests/test_error_policy.py::test_a_callable_policy_entry_cannot_become_the_masking_authority`
asserts the literal string) — presence, shape, and order
are pinned literally everywhere. This changes no definition
count and routes no new work; the value is still guarded
against silent drift at population level.

Equivalence (principle 8): the sync/async window split is
the required shape — upstream `Schema.get_extensions` takes
the `sync` flag (signature read) and upstream
`ExecutionContext.execute_field` exists with the
resolve-plus-complete contract, so sync must wrap the call
and async must span the await on the worker; the
dual-arm error container is one compatibility rule (installed
graphql-core is 3.2.8, `errors`-only, confirmed — the second
arm is append-only forward cover); copy-per-read, the
one-shot `tuple` snapshot with no `__bool__`, and both chain
orders were confirmed verbatim. Zero-edit confirmed myself:
item-scoped diff empty (0 bytes), working blob equals
`HEAD` equals the pinned `2f7273…`; coverage and assignment
validate; no candidate routes to a new family (the refused
forms keep the homes recorded below).

Rejections: J1 marker-tail refused — different heads (window
scope with parent/node/introspection guards vs specs-map
classification), shared lines are upstream idiom plus the
imported constant; trigger (third reader with neither head)
sound. J2 exact-type idiom refused — chain membership vs
runner binding, different outcomes, idiom not a package rule;
trigger (third hostile-metadata shape) sound. J3
pre-execution publishing refused — refusal/record vs
admission/lease, upstream field name owned by neither;
trigger (upstream rename) sound. J4 inapplicable — judged,
not taken on word: all seven absences re-swept by me
(absent), and the ladder-at-driver claim confirmed
(`resource_policy.py::resolve_resource_policy` and
`error_policy.py::resolve_error_policy` both delegate to
`utils/policies.py::resolve_policy`; schema consumes each
once). Fingerprints: all 19 blob ids re-hashed by me —
every one matches, so nothing went stale. Gates: the relied-
upon oracles exist with reasoned negative controls (direct
call for the boundary, `{exc!r}` interpolation for the
tail); their failability proofs properly belong to the still-
open family items F1/F2, so `## Pending execution` absent is
correct here. Pending absent; coupling none — both confirmed.
Sharded/Postgres inapplicability reason judged sound: the
artifact's claims touch no database, alias, or dialect
decision (the alias name is threaded, resolution owned
elsewhere).

AGENTS.md prose check: no raw `path:NN` citations (swept:
none); every source ref in `path::Symbol` form; the link
block carries all 10 canonical groups; no process provenance
(baseline hashes are required diff state); existing oracles
sit at the mandated tiers (`tests/` plus live
`test_query/`); zero-edit so no new tests owed.

Defects (Worker 2): none. The wire-code note above is a
prose-precision observation on already-verified substance,
not a defect: it names no second definition, no missing
guard, and no contract breach, so nothing is routed.

Scratch: read-only probe
`docs/dry/temp-tests/dry-file-schema-w2/probe_w2.py`
(`W2 ALL OK`, 64 checks; AST plus text sweeps only, no
source mutation, no DB, no shared-tree pytest). Upstream
signature reads via `uv run python -c` (no tree writes).
No workspace copy owed (no mutating proof). Concurrent dirt
(`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`, untracked sibling artifacts) left
untouched. No commit.

Judgment (Worker 2): backstop discharged, every rule in its
existing family (F1, F2 — both stay open, no new rows) or a
challenged file-local record (R1–R6) or a rejection with
difference plus trigger (J1–J4). Zero-edit legitimate.
`Status: verified`, no pending execution.

## Re-trace at bfaee91d (Worker 1)

Run 0.0.15 2026-09-19-1. Prior pass verified at `9031cb3d`
(target blob `2f727321…`, 1236 lines); this pass re-traces the target at
`bfaee91d` (worktree blob `c2e1b748…`, 1319 lines) after the reopen.
Prior reasoning above is untouched; what follows reconciles against it.

### Scope of the delta

Exactly one commit in `9031cb3d..bfaee91d` touches the target
(`git log 9031cb3d..bfaee91d -- django_strawberry_framework/schema.py`
names only `ffce6f29 fix(list_field, schema): expand relation orderings
at the offset guard and mask hook failures`, +84/-1 per the item).
Its schema.py bytes are one rule only: the hook-failure masking seam
(`execute_sync` / `execute` overrides plus `_masked_return`, the
four-name import expansion, one class-docstring paragraph). The
relation-ordering expansion at the offset guard lives entirely in
`list_field.py` (that file item's surface): this target holds no
ordering, offset, or compiler logic — probe absences
`find_ordering_name`, `resolve_ref`, `Meta.ordering`,
`_resolve_order_field_path` all hold, with only prose hits left
(`_AcquireHandoff` docstring "orderings", `_admitted_chain` docstring
"order"). So the commit's "expand relation orderings" half is
inapplicable here (neither duplication nor composition: no bytes), and
the "mask hook failures" half is a compose-by-name seam over
`extensions/error_policy.py`. No other target bytes moved: every other
member below is byte-identical to the prior blob (the diff carries only
the import hunk, the docstring paragraph, and the three methods).

Baselines: `HEAD` is `bfaee91d`; `ITEM_BASELINE`
`cb47e6b6213f67f8cb0deb37fbb12004e149aa32` exists and
`git diff <baseline> -- django_strawberry_framework/schema.py` is empty;
`git rev-parse HEAD:django_strawberry_framework/schema.py` is
`c2e1b748…`, equal to the worktree hash — target clean, no hunk
attribution owed. The plan's `## Owned changes` ledger carries no row
on this path (six rows: walker/test companions plus three gate-only
test pins, all read in full). Concurrent dirt (package hunks,
test companions, staged entries, sibling artifacts) left untouched.

### Enumeration reconciliation (fresh instrument at the new bytes)

Instrument as before: `ast.parse` over the pinned blob, `ast.Module.body`
plus every class-body method. **55 top-level statements (delta 0)** —
the import expansion adds names to statement 16, not a statement; the
three new methods are class-body members, not module members.
**Class-body methods 26 → 29 (+3, all named)**: `DjangoSchema` 8 → 11
with `execute_sync`, `execute`, `_masked_return` joining `__init__`,
`extensions` ×2, `resource_policy`, `error_policy`, `get_extensions`,
`create_extensions_runner`, `_stream`; the other five classes keep
3 / 4 / 6 / 0 / 5. Member mapping vs the prior table rows 0–54: rows
0–15, 17–45, 46–54 unchanged (row 45 gains 45.9 `execute_sync`,
45.10 `execute`, 45.11 `_masked_return`); row 16
(`.extensions.error_policy` import) gains four names
(`degraded_result`, `is_maskable_result`, `mask_execution_result`,
`masking_is_active` beside `DjangoErrorPolicyExtension`); the
`DjangoSchema` class docstring gains one paragraph (projection, R7).
No member added, removed, or re-homed beyond the +3 and the import
row; every prior home (F1, F2, R1–R6, J1–J4) is re-confirmed below.

### Matrix re-discharge (against the real new surface)

**1. Cross-flavor.** Package-wide single-definition sweeps re-run:
`def _masked_return(` once (here), `def degraded_result(` once
(`extensions/error_policy.py`), no second schema class / execution
context / chain / refusal definition anywhere (population still
117 `.py`, probe re-counted). The overrides call
`super().execute_sync` / `super().execute` once each — upstream
composition, not a second executor. The offset-guard classifier has
no spelling here (absences above); nothing to consolidate with
`list_field.py` from this side.

**2. Sync/async twins.** New pair `execute_sync` vs `execute`: one
`super()` call plus one `_masked_return(` each, differing only in
where the await sits — compared by behavior, no drift. Upstream bodies
both read this pass: sync `execute_sync` coerces a hook exception into
a fresh `ExecutionResult` in the `except` outside
`extensions_runner.operation()` (teardown already unwound,
`execution_context.result` still `None`); async `execute` is
symmetric (`async with` inside `try`, result built in the outer
`except`). The split is the recorded principle-5 adapter shape, same
as R1's. `subscribe`/`stream` untouched: `subscribe` is a thin
`stream` wrapper upstream, and `_stream` yields every hook failure as
a frame inside the lifecycle (upstream `_stream` body re-read), so
streamed hook failures reach the per-event seam, never this one.

**3. Derived knowledge.** Four compositions, zero restatements: the
policy comes from `_enforcement(self).error_policy` (the R3 record,
not settings, not the per-read copy); active/shape/mask/floor come
from the four imported gates (one call each, probe-counted); the
pre-read floor `DEFAULT_ERROR_POLICY` is the imported constant, not a
respelling; the seam builds no `GraphQLError` /
`StrawberryExecutionResult` (probe: constructor absent from target).
The `except Exception → degraded_result(policy)` posture mirrors the
teardown's fail-closed direction but delegates the floor shape to the
owner.

**4. Round-trip.** Mask-twice idempotence is structural, not a flag:
a teardown-masked error carries `original_error=None`, which the
owner's classifier reads as deliberate — the identity oracle
(`test_the_return_seam_passes_an_already_masked_result_through_by_identity`)
pins `is`-identity, proving no second id minted or logged. No second
grammar lives here.

**5. Other media.** Oracles spell literals independently and would
fail, not follow, a seam change: three package rows in
`tests/test_error_policy.py` (identity no-op, degrade-on-unanswerable-
gate with log-record assertion, disabled-policy no-op — bodies read);
six live hook rows in `test_error_policy_api.py` over both views
(masked-like-resolver, correlation-id log, one-entry-one-log,
DEBUG=True control, opt-out, deliberate GraphQLError untouched —
heads plus the `_HookFailure` extension read); projections in the
class/method docstrings, the extension module's three-seam docstring,
the `consumers.py` docstring delta, and the `docs/README.md`
paragraph (all read). The `__init__.py` surface is untouched by this
delta.

**6. Enforcement by omission.** Executor × hook-escape census:
`execute` / `execute_sync` returns masked here; streamed frames
(incl. subscription setup failures, which upstream `_stream` yields
as frames inside `on_stream_result`) masked per event at the
transport source (`consumers.py::_stop_aware_results`, the open
`subscription-per-event-error-masking` family's surface); teardown
results masked by the extension as before; `subscribe` needs no
override (delegates to `stream` → `_stream`). The plain-
`strawberry.Schema`-plus-extension boundary (no seam there) is stated
in both docstrings, not an omission. No member lacks a guard its
contract requires — no defect.

### Challenges

C1–C20 re-verified at the new bytes: the schema-side sites each
counts are intact (five `describe_value(`, three non-import
`run_in_one_sync_boundary(`, two `return copy_policy(`, both chain
orders verbatim — probe execution-verified); the R1–R6 bodies are
byte-identical; J1–J4 triggers re-checked (no third marker reader,
no third hostile-metadata shape, no upstream field rename, no
table/mark/body read gained). Counts stand: 1 at each owner, 0 here.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C21 | R7 maskable shape | a new result shape must (not) mask | **1** (`is_maskable_result` owner; seam follows) | consumer |
| C22 | R7 floor shape | degrade must publish a new shape | **1** (`degraded_result` owner; seam + teardown follow) | consumer |
| C23 | R7 executor entry | a new sync/async entry needs return masking | **1** (this seam's override pair) | file-local |
| C24 | R7 policy source | the record a return is masked under changes | **1** (R3 record; seam reads it) | consumer of R3 |
| C25 | ordering terms | a new ordering-term kind must classify | **0 here** (inapplicable surface; home: `list_field.py` item) | — |

Probe: `uv run python
docs/dry/temp-tests/dry-file-schema/probe_w1_retrace.py` → `ALL OK`
(23 checks). Two first-draft probe bugs (path depth, AST `module`
spelling for relative imports) failed on probe precision, were
corrected to the tree, re-ran green — substance unaffected.
`execution-verified` for every count/shape/absence/single-site claim
above. Then `uv run ruff check --fix` + `uv run ruff format` on the
probe until both pass. No source mutation, no DB, no shared-tree
pytest. Rejects "a second masking/ordering definition lives here"
and "the target drifted from its baseline".

### Findings

F1 (`one-sync-boundary`) and F2 (`typed-rejection-value-tail`)
reused from the plan with schema-side roles re-challenged fresh
(C1–C4 → 1 each at the owners, zero definitions here); both stay
`open`, no new rows. R1–R6 stand file-local (C5–C19 → 1 each, same
file); the import-row change touches R3's consumer imports only and
its finding text stays accurate. J1–J4 stand rejected with triggers
unfired.

### R7 — returned-result masking seam (new file-local record)

- **Contract + variation.** Every `execute` / `execute_sync` return
is passed through the error-policy masking under the extension
module's gates, because a hook-escaping exception becomes a result
only after every teardown unwound. Legitimate variation: which
executor entries are wrapped (today the two non-streamed ones;
streamed frames are excluded by contract, matrix axis 6).
- **Sites + roles.** *Definition here*:
`django_strawberry_framework/schema.py::DjangoSchema._masked_return`
plus the two one-line overrides (probe: `def _masked_return(`
single-sited package-wide). *Consumed owners* (listed, never
counted): `masking_is_active`, `is_maskable_result`,
`mask_execution_result`, `degraded_result` (all
`extensions/error_policy.py`), the R3 enforcement record, the
`DEFAULT_ERROR_POLICY` floor constant. *Sibling enforcement sites*
of the same mask owner: the extension teardown and the transport
per-event seam. *Oracles*: the three package seam tests plus the six
live hook rows (matrix axis 5). *Projections*: the four docstring
sites (class paragraph, two method docstrings, seam docstring).
- **Challenges.** C21, C22, C24 → 1 each at the named owners;
C23 → 1 here.
- **Owner + lifetime.** This seam (placement is schema-responsibility:
only the schema sees the returned value). No stored derivation (each
return is call-local; the floor constant is read, not cached).
- **Migration.** None (file item; zero edits).
- **Distinct behavior.** The seam never double-masks (structural
no-op, identity oracle) and never falls back to the unmasked result
(fail-closed floor, degrade oracle); streamed operations are out of
scope by stated contract.
- **Behavioral proof.** `static-reviewed` for placement (both
override bodies plus both upstream `except` bodies read);
`execution-verified` for the call census and single-site sweeps
(probe). Rejects "this file restates the masking".
- **Structural gate.** The identity oracle (bypassing the seam
leaves hook failures raw on exactly the hook rows), the degrade
oracle (unanswerable gate publishes the floor), the disabled-policy
oracle. Negative control: replacing one override's
`self._masked_return(` with a bare `super()` return passes every
non-hook oracle and fails exactly the masked-hook rows for that
executor. Failability proof belongs to the holding family item.
- **Coupling.** None.
- **Freshness.**
`django_strawberry_framework/schema.py`
`c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`,
`django_strawberry_framework/extensions/error_policy.py`
`16f475471a8b8295117640f7b14d949603d7bbc0` (three-seam docstring,
`degraded_result`, teardown call sites),
`django_strawberry_framework/consumers.py`
`936210e2993ddca4b77ffebf65e728f59d17079c` (docstring delta only),
`tests/test_error_policy.py`
`9ff5328eaed329a5fd69ac2e7002cf0052452241` (three seam rows),
`examples/fakeshop/test_query/test_error_policy_api.py`
`9a425677bb9763cb05776e0521afa06ad4197307` (six hook rows),
`docs/README.md`
`c32da2366faadee08f40d6a90237cdcdc74e8bc1` (seam paragraph only),
`django_strawberry_framework/error_policy.py`
`fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
`django_strawberry_framework/exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`,
`django_strawberry_framework/utils/querysets.py`
`96618fba4eafb6a87e73414770014e3aee5b41ef` (F1 consumer sites only;
owner body unchanged for the cited seam),
`django_strawberry_framework/list_field.py`
`ce682d5f79518919ff3676f2fc8bbe2bd33995a4` (ordering-expansion home,
absence witness). Upstream read from the installed checkout
(`.venv/.../strawberry/schema/schema.py::Schema.execute`,
`::Schema.execute_sync`, `::Schema.subscribe`, `::Schema._stream`);
installed release has no version attribute to pin.
- **Proposed index row for Worker 0** (file-local, per the backstop):
`Returned-result masking seam` —
owner `django_strawberry_framework/schema.py::DjangoSchema._masked_return`
— files `django_strawberry_framework/schema.py` — holding item
File `schema.py` — status `file-local` (challenge: C23 moves only
this seam; C21/C22/C24 move the named owners).
- **Proposed family-site update for Worker 0** (no new family):
`subscription-per-event-error-masking` (owner
`extensions/error_policy.py::mask_execution_result`) gains this
file as a third enforcement site alongside the teardown and the
transport source; the same commit's `degraded_result` extraction
(two inline whole-response floors → one owner, both prior call
sites converted plus this seam as a new consumer) is supporting
evidence for that family item, recorded here only as orientation.

The masking-vs-teardown similarity is not a consolidation candidate:
two enforcement sites of one definition (challenges count 1 at the
owner per axis). The ordering-expansion similarity is inapplicable:
zero bytes here, trigger would be this file gaining ordering logic.
No new family is named.

### Defects

None. Every re-checked claim held (counts, orders, absences,
upstream placement, oracle independence); the axis-6 streamed
exclusion and the plain-Schema boundary are both contracted in prose
at both ends, not gaps. Nothing routed to any owner.

### Pending execution

None. The execution proofs (read-only probe, command above) already
ran green against the shared tree; they mutate no source and open no
database, so no workspace copy was owed and no `__file__`/DB `NAME`
record applies. No pytest in the shared tree, per item rules; oracle
bodies are `static-reviewed`. No `execution-deferred` items. No
`FAKESHOP_SHARDED` or Postgres cell owed: this re-trace's claims
(statement/method counts, import/call census, absences, chain-order
literals, baseline diff) touch no database, alias, or dialect
decision (`inapplicable by construction`).

### Judgment

Backstop re-discharged at the new bytes: 55/55 module members plus
29/29 class-body members enumerated, prior homes reconciled
explicitly (delta +3 methods named, +4 import names named, all else
identical), matrix re-run against the real new surface, C1–C20
re-verified plus C21–C25 counted, one new file-local record (R7)
with its proving challenges, one family-site update proposed, zero
production edits. The +84 is a compose-by-name seam, not a second
masking; the ordering half of the commit has no bytes here.

### Item-scoped diff state

Tracked: none — `git diff
cb47e6b6213f67f8cb0deb37fbb12004e149aa32 --
django_strawberry_framework/schema.py` empty;
`git diff HEAD --stat -- django_strawberry_framework/schema.py` empty.
Untracked scratch created by this pass (not tracked changes): this
artifact's new section, plus the read-only probe
`docs/dry/temp-tests/dry-file-schema/probe_w1_retrace.py`
(`ALL OK`, 23 checks; ruff check + format both pass on it). Prior
scratch (`probe_w1.py`, `dry-file-schema-w2/`) left untouched. No
commit. `Status: ready-for-verification/1`.

## Re-trace verification at bfaee91d (Worker 2)

Expectation-first: the trace below was derived from my own instruments
before reconciling with the W1 re-trace findings. Instruments run myself:
`ast.parse` dump of the worktree target (module members plus every
class-body method list); `grep -c` censuses for the four gate calls, the
F1/F2/C-copy sites, the ordering absences, and the J-trigger sweeps;
`git hash-object` re-hashes of all ten freshness blobs; `git diff`
emptiness checks vs `ITEM_BASELINE` and vs `HEAD`; full read of
`extensions/error_policy.py` (460 lines) plus the `consumers.py`
per-event seam and the three seam-test bodies; upstream
`strawberry/schema/schema.py::Schema.execute`, `::Schema.execute_sync`,
and `::Schema.subscribe` bodies from the installed checkout; re-run of
`probe_w1_retrace.py` (`ALL OK`, 23 checks). Prior sections untouched.

Own trace. The target DEFINES six rules and CONSUMES the rest by name,
as before: R1 completion window, R2 alias serialization, R3
enforcement-record holding, R4 chain admission, R5 refusal substitution,
R6 streamed binding — definitions here, one site each. F1
one-sync-boundary: definition at
`utils/querysets.py::run_in_one_sync_boundary`, three consumers here.
F2 typed tail: definition at `exceptions.py::describe_value`, five
consumers here. New surface: the `execute_sync` / `execute` override
pair plus `_masked_return` — placement owned here (only the schema sees
the returned value), every classification/replacement/floor decision
consumed by name from `extensions/error_policy.py`. Owners I would
choose: unchanged everywhere, including the masking rule
(`mask_execution_result` owner) and the R7 placement seam (here).
Posited changes and counts agree with W1 on all of C1–C25.

Enumeration, member by member against my own dump: 55 module statements
(1 docstring + 25 imports + 6 classes + 14 top-level functions + 9
assigns) and 29 class-body methods (3 + 4 + 6 + 0 + 5 + 11). Delta from
the prior 26 reconciled exactly: `DjangoSchema` 8 → 11 with
`execute_sync`, `execute`, `_masked_return` in that order after
`create_extensions_runner`; import row 16 gains exactly the four gate
names beside `DjangoErrorPolicyExtension`; rows 0–15, 17–45, 46–54 map
unchanged (row 45 gains 45.9–45.11; `extensions` counted twice for
getter/setter). Table rows 0–54 home every member; no member
unassigned, none re-homed. Counts re-censused myself:
`describe_value(` ×5, `await run_in_one_sync_boundary(` ×3,
`return copy_policy(` ×2, both chain orders verbatim per the re-run
probe. Matrix judged against the real new surface, not taken on word:
axis 1 (`def _masked_return(` single-sited package-wide, no second
schema/context/chain/refusal definition, population 117 re-counted by
the probe); axis 2 (new `execute_sync` vs `execute` pair compared by
behavior — one `super()` call plus one `_masked_return(` each, await
placement the only difference); axis 3 (policy from the R3 record, the
four gates by name, floor from the imported constant, no constructor);
axis 4 (mask-twice structural identity, oracle pins `is`-identity);
axis 5 (oracles below spell literals independently); axis 6 (executor ×
hook-escape census — returns masked here, streamed frames at the
transport source, teardown results by the extension, `subscribe`
delegates to `stream` so no override owed, plain-Schema boundary stated
in both docstrings).

Masking-seam definition/consumer judgment (esp. vs `error_policy.py`).
The seam is a CONSUMER of the masking rule, not a second definition.
Evidence read from the bodies: `_masked_return` calls
`masking_is_active` / `is_maskable_result` / `mask_execution_result` /
`degraded_result` once each and constructs nothing — the file's single
`GraphQLError(` site is R5 `_refusal`, and `ExecutionResult(` is absent
entirely. Classification (`_is_unexpected`, incl. the
`original_error=None`-is-deliberate arm the no-op rests on),
replacement (`_masked`), floor shapes (`_degraded`,
`degraded_result`), and both gates all live in `error_policy.py`. The
owner module claims this site itself: its docstring names the three
seams and cites `schema.py::DjangoSchema._masked_return` as the third.
The seam's own `except → degraded_result(policy)` guard is layering,
not duplication: it covers only what the owner never sees (the R3
record read plus the two gate calls made before `mask_execution_result`
is entered), while the owner's internal guards cover classification and
masking reads — and the floor SHAPE is delegated to the owner in both
cases. The policy-source difference is reasoned, not drift: the seam
reads the R3 authority (unreachable to resolvers) rather than the
per-read copy or `schema_error_policy` (which exists for plain
`strawberry.Schema` hosts this seam never serves). No machinery is
duplicated, so no family candidate: R7 as a file-local placement rule
(C23 → 1 here; C21/C22/C24 → 1 each at the named owners) stands.

Site-addition judgment. `schema.py` joins
`subscription-per-event-error-masking` as a third ENFORCEMENT SITE
(consumer), not a definition. `mask_execution_result(` has exactly three
consumer call sites package-wide: the teardown
(`extensions/error_policy.py`, line 410), the transport per-event seam
(`consumers.py`, line 1385), and this seam (`schema.py`, line 1083) —
each a placement the other two cannot reach (torn-down result,
streamed frame, returned value). The plan index row update below is
confirmed.

C25 split judgment. The ff commit's ordering-expansion half has zero
bytes here: `find_ordering_name`, `resolve_ref`, `Meta.ordering`, and
`_resolve_order_field_path` all count 0 in this target (re-swept), the
ff `--stat` puts +201 ordering lines in `list_field.py` vs +85
masking-only lines here, and `list_field.py` carries 9 ordering-machinery
hits as the C25 home. C25 = 0 here is correct; no bytes routes to this
file item.

Proof-adequacy judgment. `## Pending execution` empty is correct and
the item is `verified` (not pending execution). The seam's observable
wire behavior (stable message text, `correlationId` extensions, one
entry plus one log record, DEBUG/opt-out/deliberate controls) is pinned
by permanent oracles already in the tree — the three package seam tests
(identity no-op, unanswerable-gate degrade with log assertion,
disabled-policy no-op; bodies read, literals spelled independently of
the owner) plus the six live hook rows over both colors (masked shape,
correlation-id log join, one-entry-one-log, DEBUG control, opt-out,
deliberate `GraphQLError` untouched; bodies read). They landed with the
ff commit as the intentional contract change and CI executes them; the
final gate's full suite re-runs them. Nothing in any finding depends on
an unrun command: placement equivalence is established by both upstream
`except` bodies read (hook exception coerced into a FRESH result after
teardown unwound, on both executors) plus the existing oracles, and the
probe execution-verifies every count/shape/absence/single-site claim.
Sharded/Postgres cells stay `inapplicable by construction` — every
re-trace claim touches no database, alias, or dialect decision (the
alias name is threaded, resolution owned at `resolve_write_alias`).
No `proof:` entries owed; no `gate:` entries owed by a file item.

AGENTS.md prose on the empty diff. `git diff <ITEM_BASELINE> --
django_strawberry_framework/schema.py` is 0 bytes and `git diff HEAD
--stat -- django_strawberry_framework/schema.py` is empty; worktree blob
`c2e1b748…` equals `HEAD:` — target clean, no hunk attribution owed,
zero production edits confirmed. The artifact's re-trace section carries
no raw `path:NN` citations (swept: none), every source ref is in
`path::Symbol` form, no reference-style links were introduced (link
block untouched), no process provenance beyond required diff state, and
existing oracles sit at the mandated tiers (`tests/` plus live
`test_query/`). `uv run ruff check` passes and `uv run ruff format
--check` is clean on the probe; no tracked `.py` edits exist to lint.
Concurrent dirt (package hunks, test companions, staged entries,
sibling artifacts, prior scratch) left untouched; no commit.

Per-claim agreement/difference. 55/55 module members (delta 0) plus
29/29 methods (26→29, `execute_sync` / `execute` / `_masked_return`
named): AGREE, own dump identical. F1/F2 re-challenged fresh and stay
open: AGREE (C1–C4 → 1 each at owners; 5/3/2 site counts re-censused).
New file-local row `Returned-result masking seam` owned by
`DjangoSchema._masked_return`: AGREE, with the consumer-not-definition
reading above. `schema.py` as third enforcement site on
`subscription-per-event-error-masking`: AGREE. Four gates composed by
name, 1 call each, seam builds no result: AGREE. Mask-twice structural
no-op: AGREE (classifier arm plus identity oracle both read).
Streamed frames excluded by stated upstream contract: AGREE
(`subscribe`-wraps-`stream` plus per-stage frame `except`s read;
per-event seam read). Ordering-expansion half zero bytes here, four
absences: AGREE, re-swept. C1–C20 intact, C21–C25 counted with C25 = 0
here and home `list_field.py`: AGREE. J1–J4 triggers unfired: AGREE
(marker readers still owner + 2, no third hostile-metadata shape, no
upstream field rename, no table/mark/body read gained). No defects: AGREE.
No pending execution, sharded/PG inapplicable: AGREE. Zero production
edits: AGREE. Probe 23 checks ALL OK: AGREE, re-ran green. No
differences; the only nuance is the explicit layering analysis above,
which confirms rather than weakens the file-local reading.

Freshness re-hashed at `bfaee91d` (all match W1): target
`c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`;
`extensions/error_policy.py`
`16f475471a8b8295117640f7b14d949603d7bbc0`;
`consumers.py` `936210e2993ddca4b77ffebf65e728f59d17079c`;
`list_field.py` `ce682d5f79518919ff3676f2fc8bbe2bd33995a4`;
`error_policy.py` `fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`;
`exceptions.py` `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
`utils/querysets.py`
`96618fba4eafb6a87e73414770014e3aee5b41ef`;
`tests/test_error_policy.py`
`9ff5328eaed329a5fd69ac2e7002cf0052452241`;
`test_error_policy_api.py`
`9a425677bb9763cb05776e0521afa06ad4197307`;
`docs/README.md` `c32da2366faadee08f40d6a90237cdcdc74e8bc1`.
Upstream read from the installed checkout (no version attribute to pin).

Defects (Worker 2): none. Every re-checked claim held; the layering
nuance above names no second definition, no missing guard, and no
contract breach, so nothing is routed.

Judgment (Worker 2): backstop re-discharged at the new bytes — 55/55
module members plus 29/29 class-body members enumerated with my own
instruments, delta reconciled by name, matrix re-run against the real
new surface, C1–C25 counted, R7 confirmed file-local with its proving
challenges, the family site addition confirmed as consumer-only, C25
correctly out of this file, proofs adequate with none deferred.
`Status: verified`, no pending execution.

Exact plan rows for Worker 0 (plan edits are Worker 0's alone; Worker 2
touches no plan line):

Tick (replaces the line 85 `REOPENED` row):

- [x] File `schema.py` — [dry-file-schema.md](dry-file-schema.md) —
  verified (Run 0.0.15 2026-09-19-1 re-trace at `bfaee91d`; zero edits,
  no pending execution)

Index row (new file-local row, `## Responsibility index` file-local
table alongside the other `schema.py` rows):

| `returned-result-masking-seam` | `django_strawberry_framework/schema.py::DjangoSchema._masked_return` | `django_strawberry_framework/schema.py` | File `schema.py` | file-local |

Index update (existing family row: append this file to the covered set,
owner/holding/status unchanged):

| `subscription-per-event-error-masking` | `extensions/error_policy.py::mask_execution_result` | `extensions/error_policy.py`, `consumers.py`, `schema.py` | Family `subscription-per-event-error-masking` | open |

## Run-7 re-trace at `0c0537e2` (Worker-1)

Run 0.0.15 2026-09-29-7. The verified record above is prior
evidence only; what follows re-traces fresh at HEAD bytes with the
worktree delta scoped and attributed. Zero production edits; one
defect recorded for routing.

### Scope of the delta

Fingerprints: drift base `5ee86193` blob `19f90bf5` (1319
lines), HEAD `0c0537e2` blob `e6b52335` (1410 lines), worktree
blob `f4e807e9` (1437 lines). HEAD unmoved for the whole pass.

Drift-base-to-HEAD is a real delta of 11 hunks (275+/184-) in
exactly two commits. `1b6a09b1` (8 hunks) replaces the async
alias-lock machinery with the per-window thread and adds the
second window failure rule: module-docstring async rewrite,
import block, `_AcquireHandoff` / `_AsyncAliasLock` /
`_ASYNC_MUTATION_LOCKS` / `_async_mutation_lock` replaced by
`_CLOSED_WINDOW_MESSAGE` / `_close_thread_connections` /
`_MutationWindowThread`, plus `_refuse_uncommitted_window` /
`_exit_window` and the sync/async window-body rewrites.
`982537c3` (3 hunks) reworks extension-entry classification by
real type: `_is_resolvable_extension_entry` and `_is_extension`
docstrings, and the `_entry_resource_policy` /
`_entry_type` / `_extension_entry_matches` tail (total `_entry_type`,
dropped `None`/guard arms). The recorded drift
(`django_strawberry_framework/schema.py::_FALLBACK_ENFORCEMENT`
and `django_strawberry_framework/schema.py::DjangoSchema._masked_return`
reading the `_PACKAGE_*` canonical copies) is confirmed already
present at the drift base, not part of either commit.

HEAD-to-worktree is 23 hunks (`-U0`; 19 at `-U3`), 58+/31-,
all concurrent-external: no `## Owned changes` ledger row names
this file, and every hunk's content matches the package-wide
truth migration (new untracked
`django_strawberry_framework/utils/truth.py` plus 246
render-family call sites across 30+ modules) or docstring
touch-ups. Attribution table below names all 23.

Enumeration, fresh instrument (`ast.parse` over each state's
bytes, `ast.Module.body` plus every class-body method):
drift base 55 members (6 classes, 14 functions, 9 assigns, 25
imports, docstring) with 29 class-body methods (3 + 4 + 6 + 0 +
5 + 11); HEAD 56 members (28 imports, `_CLOSED_WINDOW_MESSAGE`,
`_close_thread_connections`, `_MutationWindowThread`,
`DjangoMutationExecutionContext` grown 6 to 8 methods) with 32
class-body methods (5 + 8 + 0 + 5 + 11); worktree 57 members
(`truth` import added, `describe_value` import dropped,
`DjangoSchema` grown 11 to 12 methods with `_subscribe`) with
33 class-body methods (5 + 8 + 0 + 5 + 12). Population 117
`.py` at HEAD, 119 in worktree (untracked `utils/truth.py` and
`utils/lazy.py`).

### Hunk attribution (HEAD-to-worktree, all 23 by content)

Truth-migration hunks (14): the `describe_value` import drop,
the `truth` import, `execute_field` reading `_mutation_meta`
through `truth.static_attr`, five `describe_value` to
`truth.describe` conversions (extensions-setter refusal,
factory-exception reason, two resolved-member reasons,
subclass-declaration refusal), three `issubclass(type(...))`
to `truth.is_instance` conversions (`_stream`,
`_is_resolvable_extension_entry`, `_is_extension`) plus the new
`_subscribe`'s own check (same hunk as the `_stream` one),
two to `truth.is_type` (`_entry_resource_policy`,
`_entry_type`), one to `truth.is_subclass`
(`_extension_entry_matches`). Prose hunks (9): the `0.0.14`
drop, the execution-split header, the context and refusal
class-docstring first lines, the graphql-core `3.2.9` to
`3.2.10` claim, the two-flags to a-flag fix, the
population to claimed-authority noun fix, the factory-comment
rewrite, the `_stream` floor-band paragraph. New surface (1,
inside hunk 17): `DjangoSchema._subscribe`. Every hunk is
concurrent-external; none was touched.

### Prior-finding verdicts

CONFIRM (6, three with notes): R3 enforcement-record holding
(canonical-copy note, policies F2 cited); R5 refusal
substitution (two prose touch-ups; `coded-error-extensions-shape`
bypass still present, errors F9 cited); R7 masking seam
(canonical-floor note, policies F2 cited); J1 marker-tail;
J3 pre-execution publishing; J4 inapplicable surfaces
(all eleven absences re-swept at worktree: `SCALAR_MAP`,
`strawberry_config`, `_BOUNDARY_METHOD`,
`_RawBodyRequestAdapter`, `require_optional_module`,
`MAX_REQUEST_BODY_BYTES`, `_PACKAGE_SCALAR_MAP`,
`find_ordering_name`, `resolve_ref`, `Meta.ordering`,
`_resolve_order_field_path`).

REVISE (7): F1 one-sync-boundary (schema.py no longer
consumes; prose mention only); F2 typed-rejection-value-tail
(owner deleted in worktree; sites read `truth.describe`;
contract difference is Defect D1); R1 completion window
(two failure rules plus `_exit_window`); R2 alias
serialization (CLOSED at HEAD, replaced by file-local R2'
per-window thread); R4 chain admission (real-type
classification plus truth predicates); R6 streamed binding
(`_subscribe` twin); J2 exact-type idiom (trigger fired
externally; predicates now consume `utils/truth.py`).

### Matrix re-discharge (fresh, HEAD bytes plus worktree delta)

**1. Cross-flavor.** Single-definition sweeps re-run over
119 files: `DjangoSchema`, `DjangoMutationExecutionContext`,
`_admitted_chain`, `_refused_chain`, `_MutationWindowThread`,
`_close_thread_connections`, `_SchemaEnforcement`,
`_RefusedConfiguration`, `_refuse_operation_document`,
`_masked_return`, `_subscribe`, `_exit_window`,
`_refuse_uncommitted_window` each hit once; the deleted
`_AsyncAliasLock`, `_AcquireHandoff`, `_async_mutation_lock`
hit zero. `MUTATION_CLASS_MARKER` readers are still owner
plus two (schema tail, resource tail). New consumption is
by name only: `truth.*` (13 sites), the four mask gates,
`copy_policy` twice, one `resolve_*_policy` call each.

**2. Sync/async twins.** Three pairs, compared by behavior:
`_execute_mutation_field_sync` vs `_execute_mutation_field_async`
(now sharing `_exit_window`, differing only in thread/await
placement — the recorded principle-5 shape, with the async
final transition surviving repeated cancellation);
`execute_sync` vs `execute` (one `super()` call plus one
`_masked_return` each, unchanged); `_stream` vs `_subscribe`
(byte-identical wrappers, firing on complementary upstream
bands). No drift beyond the D1 contract difference.

**3. Derived knowledge.** Alias from `resolve_write_alias`,
mode from the upstream `sync` flag, policies from the resolve
ladder plus `copy_policy` per read, marker from the imported
constant, identity facts from `truth.*`, fallback and floor
from the `_PACKAGE_*` canonical copies — zero restatements.

**4. Round-trip pairs.** Settle/recall/accept, admit/refuse,
parse/refuse, mask-twice identity all intact; the
`_stream`/`_subscribe` pair adds one wrapper under two
upstream names, not two grammars.

**5. Other media.** Oracles at HEAD still pin the window
(hostile-container, completion-rollback live rows),
the chain (factory-count, hybrid, slotted rows), the
snapshot (`tuple`-exact, one-shot, no-parser rows), and the
masking seam (identity, degrade, hook rows). Worktree oracle
turnover is concurrent-external and recorded, not judged:
the 4-case hostile factory-exception oracle collapsed to
one ordinary case (D1 evidence), the hostile-`__class__`
unit oracle and the two claiming-instance construction
params moved to `tests/utils/test_truth.py` (untracked, 931
lines), one `_subscribe` passthrough row added; 72 test defs
at both states.

**6. Enforcement by omission.** Member-by-member census:
marked-mutation guards intact; every entry shape typed and
claim-checked; all three operation types refused; streamed
frames bound on both bands; executor-by-hook-escape census
unchanged. One gap found: the five refusal/rejection message
sites no longer contain a hostile render (Defect D1) —
a broken guard, not a missing one.

### Challenges

C1–C2 are moot here (F1 left this file: HEAD census is one
prose mention, zero code sites; the owner and sibling
consumers are alive). C3–C4 move to the `truth.describe`
owner (C32). C5–C19 stand as mapped in the findings, with
C5 widened by the second failure rule and C12–C14
re-confirmed post-`982537c3`. New:

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C26 | R1' closed-connection rule | new uncommitted-window shape | **1** (`_refuse_uncommitted_window`) | file-local |
| C27 | R1' exit sharing | third failure rule | **1** (`_exit_window`) | file-local |
| C28 | R2' thread ownership | shared-executor window | **1** (`_MutationWindowThread`) | file-local |
| C29 | R2' connection close | backend-handle rule change | **1** (`_close_thread_connections`) | file-local |
| C30 | R4' claim halves | third claim kind | **1** (resolved + entry halves, one file) | file-local |
| C31 | R6' resume binding | new frame binding | **1** (`_stream` + `_subscribe`, one file) | file-local |
| C32 | render contract | never-raising tail | **1** (`truth.describe` owner; 5 sites follow) | consumer + D1 |
| C33 | predicate mechanism | new hostile-metadata shape | **1** (`truth` owner; 7 sites follow) | consumer |

Read-only probe `/tmp/schema_retrace_enum.py` plus grep
censuses, all static against the three states; upstream
reads from the installed tree (strawberry-graphql 0.324.0,
graphql-core 3.2.8, asgiref 3.11.1).

### Findings

**F1 — one-sync-boundary (REVISED: this file left the family).**
Contract unchanged at the owner
(`django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`,
alive with sibling consumers in `filters/sets.py`,
`types/resolvers.py`, `auth/mutations.py`). Schema-side: the
import and all three `await` sites are gone at HEAD
(`1b6a09b1`); the one remaining mention is docstring prose
naming the pipeline's seam. Challenges C1–C2 count 1 at the
owner with zero sites here. Proposed index update: drop
`schema.py` from the family row (the family item already
flags census 6 to 5). Freshness: target HEAD `e6b52335`
(prose line only) plus owner `3616927d`.

**F2 — typed-rejection-value-tail (REVISED: owner deleted in
worktree, sites re-homed to `truth.describe`).** At HEAD the
prior record holds verbatim: five `describe_value(` sites,
never-raising owner, 4-case hostile oracle. In worktree
`exceptions.py::describe_value` and its `_safe_*` helpers
are deleted with zero package-wide callers, and all five
sites call `truth.describe` — whose `render` runs a
non-scalar's own `__repr__` with exceptions propagating
(owner docstring read). That is a different contract on the
containment seam, recorded as Defect D1. No plan row names
this family; the family item, when queued, must decide
against the truth owner, not the deleted one. Freshness:
target HEAD `e6b52335` (5 sites) / worktree `f4e807e9`
(5 converted sites), owner HEAD `e06b0b7f` (deleted in
worktree `93401220`), `utils/truth.py` untracked
`d5c96bc8`.

**R1' — completion-spanning mutation window (REVISED,
file-local).** `DjangoMutationExecutionContext` now enforces
two failure rules through `_exit_window`: the error rule
(`_rollback_for_new_errors`, unchanged logic) and the
closed-connection rule (`_refuse_uncommitted_window` with
`_CLOSED_WINDOW_MESSAGE`, failing the field with a located
error when `closed_in_transaction` is set, since Django
skips such a commit without raising). Both adapters share
the exit; the sync path holds the atomic on the calling
thread, the async path runs enter/pipeline/exit on the
window thread and drives the final transition to completion
across cancellation. C5–C7 re-mapped (C5 widened), C26–C27
count 1 here. Behavioral proof `static-reviewed` (both
bodies plus `_exit_window` read; upstream `execute_field`
placement as previously read); oracles are the window live
rows plus `tests/mutations/test_write_transaction.py`
closed-connection rows (identical at HEAD and worktree).
Trigger: a second completion-spanning window.

**R2 — async alias serialization (CLOSED) / R2' — per-window
thread (new file-local record).** The lock, guard, store,
and accessor are deleted at HEAD with zero package-wide
hits and zero surviving oracles; the old record closes.
`_MutationWindowThread` (private single-thread executor
under a fresh thread-sensitive context key, caller's
executor under a blocked sync caller, `run` under ordinary
cancellation, `close` surviving repeated cancellation,
`_final` retiring the executor from its own thread,
`_release` uninstalling the key) plus
`_close_thread_connections` (close plus raw-handle drop,
`DatabaseError` suppressed) is one rule in two members,
same file. C8–C9 are superseded by C28–C29 (1 each here).
No second window thread exists. Trigger: a second
cross-operation thread owner.

**R3 — enforcement-record holding (CONFIRMED with
canonical-copy note, file-local).** Record shape, stores,
`_enforcement` read, settle/accept balance, re-init and
setter refusals, and both copy-per-read properties are
byte-identical in logic across all three states. The
fallback record and both properties now participate in the
verified canonical-copy split (File `utils/policies.py`
F2 `policy-authority-isolation`: `DEFAULT_*` is the
unread template, `_PACKAGE_*` the canonical fallback, the
resolved policy canonicalized at resolution, every
consumer-reachable handout a `copy_policy` duplicate):
`_FALLBACK_ENFORCEMENT` reads both `_PACKAGE_*` copies and
the properties hand out copies — the exact classification
that outcome records for this file. The worktree
two-flags to a-flag comment fix is accurate (one flag
field). C10–C11 stand.

**R4' — chain admission (REVISED, file-local).**
Post-`982537c3` the entry half classifies by real type
(`_entry_type` total over `type()`, `_extension_entry_matches`
a bare `issubclass`, `_entry_resource_policy` guarding
classes via the same idiom) and the resolved half types
every member and claim; worktree converts seven predicate
sites to `truth.is_instance` / `truth.is_type` /
`truth.is_subclass` without changing the admitted/refused
orders (verified verbatim at both states). The two halves
remain one rule in one file (factories opaque until
called). `type(policy) is ResourcePolicy` and
`isinstance(parent_fields, dict)` are the two unconverted
exact-type sites — same idiom, narrower inputs, no second
rule. C12–C14 re-confirmed (C30). The claiming-instance
boundary params moved to the truth owner's tests; the
subclass/hybrid/factory-count/slotted pins stay at this
boundary.

**R5 — refusal substitution (CONFIRMED with notes,
file-local).** Machinery byte-identical across all three
states; worktree touches only a comment noun and a
docstring first line. The `_refusal`
`extensions={"code": ...}` spelling remains the recorded
bypass of NEW FAMILY `coded-error-extensions-shape`
(File `utils/errors.py` F9; family item undispatched,
owns any migration). C15–C17 stand.

**R6' — streamed-operation binding (REVISED, file-local).**
`_stream` gains the floor-band paragraph and the
`truth.is_instance` check; `_subscribe` is its twin for
strawberry-graphql below 0.319. Against the installed
0.324.0 the twin is dead (upstream has no `_subscribe`;
`subscribe` delegates to `stream`, bodies read) and
harmless (nothing calls it); its passthrough oracle
patches the seam with `create=True`. One wrapper
(`resumed_stream`) under two upstream names; C18–C19 plus
C31 count 1 here. Trigger: a second streamed-binding
wrapper.

**R7 — returned-result masking seam (CONFIRMED with
canonical-floor note, file-local).** Overrides, gates, and
fail-closed floor byte-identical in logic; the pre-read
floor is the `_PACKAGE_ERROR_POLICY` canonical copy per
the policies F2 split. Third enforcement site of
`subscription-per-event-error-masking` stands. C21–C24
stand.

**J1 — marker-tail read (CONFIRMED, trigger unfired).**
Both tails byte-identical; readers still owner plus two
(package-wide `MUTATION_CLASS_MARKER` census re-run).
The `truth.static_attr` conversion touches the
`_mutation_meta` head read in `execute_field`, not the
tail. Trigger (third reader with neither head) unfired.

**J2 — exact-type idiom (REVISED: trigger fired
externally).** The reconsideration trigger (a mechanism
change touching three or more predicates at once) fired
via the concurrent truth migration, which consolidated
seven sites in this file under
`django_strawberry_framework/utils/truth.py` — a broader
owner than the refused `is_exact_type` helper, also
covering `__instancecheck__`, metaclass `__eq__`, and
namespace reads. Schema-side predicates are now consumers
(C33 counts 1 at the owner). The per-site `__class__`
docstrings stay accurate (the reason still holds; the
mechanism moved). No consolidation is owed by this file
item; the owner needs a plan item (file untracked).

**J3 — pre-execution publishing (CONFIRMED).**
`restate_admission_verdict` alive at both states;
refusal/record vs admission/lease difference unchanged;
upstream field unrenamed. Trigger unfired.

### Defects

**D1 — refusal/rejection messages no longer contain a
hostile render (5 sites, worktree-only).** The five
`truth.describe` sites build refusal reasons and typed
rejections from consumer-controlled objects (factory
exception, resolved member, unresolvable entry, subclass
entry) with a renderer whose non-scalar path propagates
`__repr__` exceptions. Contract row broken: R4 "a factory
that RAISES is refused rather than allowed to escape",
pinned at HEAD by the 4-case hostile oracle
(`ordinary-exception`, `raising-repr-and-str`,
`raising-argument-representation`, `raising-type-name`)
plus the removed containment comment. Feasible shape: a
factory raising an exception with a raising `__repr__`
(the HEAD oracle constructs exactly this). Wire input:
any operation against such a schema — `get_extensions`
is called outside upstream's converting `try` (upstream
bodies read), so the render failure escapes `execute` /
`execute_sync` raw instead of refusing with the stable
code; the two `ConfigurationError` sites fail likewise at
construction. The concurrent oracle rewrite (single
ordinary case) follows production rather than pinning the
contract. Routing: the truth-migration owner (File
`utils/truth.py` when queued, else the migration card);
maintainer decides containment-restored vs
propagation-accepted. No security-path routing: fail-open
on a diagnostic seam, reproduction already in HEAD's
deleted oracle, no new exploit shape.

### Pending execution

None. Every claim is static against the three states
(AST dumps, censuses, body reads, upstream reads); the
read-only probe mutates no source and opens no database,
so no workspace copy was owed. No pytest ran (not
authorized). No sharded/Postgres cell owed: the claims
are definition counts, single-site facts, and prose
statements touching no database, alias, or dialect
decision.

### Judgment

Backstop re-discharged: 56/56 HEAD members plus 32/32
methods enumerated with the drift-base and worktree
reconciliation above, matrix re-run against the real new
surface, 6 prior findings CONFIRMed (3 with notes), 7
REVISEd with proving challenges, one file-local record
closed (R2) with its successor recorded (R2'), one defect
routed, zero production edits. The drift delta is two
mechanism changes (window thread, real-type
classification); the worktree delta is the truth
migration plus prose.

### Item-scoped diff state

`git diff HEAD -- django_strawberry_framework/schema.py`
is 58+/31- in 23 hunks, every hunk attributed above by
content to concurrent-external work (truth migration plus
prose); the `## Owned changes` ledger names no hunk on
this path. No tracked file was edited except this
artifact; no commit. Scratch is untracked under `/tmp`
only. `Status: ready-for-verification/1`.

## Index rows for Worker-0

(Worker-0 alone edits the plan; rows named here for
transcription.)

- Family-site update `one-sync-boundary`: drop
  `schema.py` from the covered files (zero code sites at
  HEAD; one docstring prose mention). Owner, holding,
  status unchanged.
- Family-site confirm `policy-authority-isolation`:
  `schema.py` sites verified at HEAD and worktree (two
  `copy_policy` handouts, two `_PACKAGE_*` fallback
  reads) per the cited F2 split. No change.
- Family-site confirm `coded-error-extensions-shape`:
  `schema.py::_refusal` bypass verified at both states.
  No change.
- Family-site confirm
  `subscription-per-event-error-masking`: `schema.py`
  third enforcement site verified at both states. No
  change.
- Family-site confirm `carried-operation-executor-mode`
  and `async-execution-dispatch-decision`: `schema.py`
  consumption (`OperationMode`, `async_execution`,
  `_operation_mode`) verified at both states. No change.
- File-local REVISE `completion-spanning-mutation-window`:
  owner
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext`
  (two failure rules, `_exit_window`).
- File-local CLOSE `async-alias-serialization` (lock
  machinery deleted at HEAD) and ADD
  `per-window-mutation-thread`: owner
  `django_strawberry_framework/schema.py::_MutationWindowThread`
  (with `_close_thread_connections`).
- File-local REVISE `chain-admission`: owner
  `django_strawberry_framework/schema.py::DjangoSchema.get_extensions`
  (real-type entry half, truth predicates).
- File-local REVISE `streamed-operation-binding`: owner
  `django_strawberry_framework/schema.py::DjangoSchema._stream`
  (with the `_subscribe` twin).
- File-local CONFIRM `enforcement-record-holding`,
  `refusal-substitution`, `returned-result-masking-seam`
  (canonical-copy notes, no structural change).
- Consumer row (new owner needed): `schema.py` consumes
  `django_strawberry_framework/utils/truth.py` identity
  reads (7 predicate sites, 5 render sites, 1 static-attr
  site in worktree) — holding item TBD (file untracked;
  queue File `utils/truth.py`).
- Rejection REVISE `exact-type-idiom` (J2): trigger fired
  externally; schema-side refusal superseded by the
  truth-module consumer row above.
- Defect D1 (hostile-render containment loss, 5 sites):
  route to the truth-migration owner; maintainer decides
  containment-restored vs propagation-accepted.

## Run-7 verification at `0c0537e2` (Worker-2)

Run 0.0.15 2026-09-29-7, queue item d7. Expectation-first
re-derivation at HEAD bytes plus the worktree delta; W1's
conclusions were checked, not inherited. Bound inputs held for
the whole pass: HEAD `0c0537e2` unmoved, drift blob
`19f90bf5`, HEAD blob `e6b52335`, worktree blob `f4e807e9`
(all re-hashed), line counts 1319 / 1410 / 1437.

### Independent trace (Worker-2 instruments)

`ast.parse` census per state: drift base 55 members (6 classes,
14 functions, 9 assigns, 25 imports, docstring) with 29 methods
(3 + 4 + 6 + 0 + 5 + 11); HEAD 56 members (28 imports) with 29
methods (5 + 8 + 0 + 5 + 11); worktree 57 members (29 imports)
with 30 methods (5 + 8 + 0 + 5 + 12). Population 117 `.py` at
HEAD, 119 in worktree (untracked
`django_strawberry_framework/utils/truth.py` `d5c96bc8` and
`django_strawberry_framework/utils/lazy.py`). Drift-to-HEAD: 11
hunks (`-U3`), 275+/184-, exactly two commits (`982537c3`,
`1b6a09b1`). HEAD-to-worktree: 23 hunks (`-U0`, 19 at `-U3`),
58+/31-.

Single-definition sweeps over all 119 files:
`django_strawberry_framework/schema.py::DjangoSchema`,
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext`,
`django_strawberry_framework/schema.py::_admitted_chain`,
`django_strawberry_framework/schema.py::_refused_chain`,
`django_strawberry_framework/schema.py::_MutationWindowThread`,
`django_strawberry_framework/schema.py::_close_thread_connections`,
`django_strawberry_framework/schema.py::_SchemaEnforcement`,
`django_strawberry_framework/schema.py::_RefusedConfiguration`,
`django_strawberry_framework/schema.py::_refuse_operation_document`,
`django_strawberry_framework/schema.py::_masked_return`,
`django_strawberry_framework/schema.py::_subscribe`,
`django_strawberry_framework/schema.py::_exit_window`,
`django_strawberry_framework/schema.py::_refuse_uncommitted_window`
each defined once; `django_strawberry_framework/schema.py::_AsyncAliasLock`,
`django_strawberry_framework/schema.py::_AcquireHandoff`,
`django_strawberry_framework/schema.py::_async_mutation_lock` hit
zero everywhere (all tracked files at HEAD included). Truth
census in worktree `schema.py`: 13 sites (1 `static_attr`, 5
`describe`, 4 `is_instance`, 2 `is_type`, 1 `is_subclass`).
Upstream reads from the installed tree (strawberry-graphql
0.324.0, graphql-core 3.2.8, asgiref 3.11.1): no `_subscribe`
in upstream `Schema`; `subscribe` delegates to `stream`;
`get_extensions` is called before the converting `try` in both
`execute` and `execute_sync`.

### Required judgments

- **F1 REVISED (left the family): CONFIRMED.** One
  `run_in_one_sync_boundary` mention at HEAD, inside the
  `_execute_mutation_field_async` docstring; zero code sites.
  Owner `django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`
  alive (HEAD blob `3616927d`); the plan's family row still
  lists `schema.py`, so the drop is genuinely owed, and the
  `6→5` note matches the plan's run-7 querysets entry.
- **F2 REVISED (owner deleted): CONFIRMED.** HEAD: five
  `describe_value(` sites plus the never-raising owner
  (`try`/`except BaseException`, owner blob `e06b0b7f`).
  Worktree: owner and `_safe_*` helpers gone from
  `django_strawberry_framework/exceptions.py` (blob `93401220`),
  zero package-wide `describe_value` callers, all five sites
  calling `truth.describe`, whose `render` runs a non-scalar's
  own `__repr__` with propagation stated in its docstring and
  body. No plan row names this family.
- **R1' REVISED (two failure rules): CONFIRMED.** Both rules
  read at HEAD (`_rollback_for_new_errors`,
  `_refuse_uncommitted_window` over `closed_in_transaction`
  with `_CLOSED_WINDOW_MESSAGE`), shared through `_exit_window`
  by both adapters; context grown 6 to 8 methods. The
  closed-connection oracle rows are untouched by the worktree
  diff (the file differs elsewhere).
- **R2 CLOSED / R2' ADDED: CONFIRMED.** Old machinery deleted
  with zero hits at HEAD; `_MutationWindowThread` plus
  `_close_thread_connections` single-sited in this file at
  both states. One rule, two members, one file.
- **R4' REVISED (real-type halves): CONFIRMED.** `982537c3`'s
  three schema hunks read (two docstrings; total `_entry_type`,
  bare-`issubclass` `_extension_entry_matches`, dropped
  `None`/guard arms). Seven predicate sites converted in
  worktree; admitted/refused orders byte-identical at both
  states; exactly two unconverted code sites (`type(policy) is
  ResourcePolicy`, `isinstance(parent_fields, dict)`; the two
  further hits are comment/docstring prose). Claiming-instance
  coverage exists at the truth owner; subclass / hybrid /
  called-once / slotted pins stay at this boundary.
- **R6' REVISED (`_subscribe` twin): CONFIRMED.** Zero
  `_subscribe` at HEAD; worktree twin body identical to
  `_stream` modulo the `super()` seam name; dead and callerless
  at the installed ceiling, live on the supported floor band
  (`strawberry-graphql>=0.316.0`); its oracle patches the seam
  with `create=True`.
- **J2 REVISED (trigger fired): CONFIRMED.** Seven predicate
  conversions exceed the three-or-more trigger; the truth owner
  covers `__instancecheck__`, metaclass `__eq__` (identity
  reads), and namespace reads per its bodies and docstrings.
- **D1 DEFECT: CONFIRMED as a DRY-scope defect.** All five
  raise paths read: two build `ConfigurationError` messages at
  construction (setter, `_declared_authority`), three build
  refusal reasons inside `get_extensions` with no further
  conversion. A raising `__repr__` now propagates where HEAD's
  renderer contained it: out of `get_extensions` it escapes
  `execute`/`execute_sync` raw (verified outside upstream's
  converting `try` on both paths) instead of refusing with the
  stable code. Contract row: the prior F2
  never-raising-containment row (see erratum E2, label only).
  Feasible shape under supported public API: a factory raising
  an exception with a raising `__repr__` under
  `DjangoSchema(extensions=[factory])` — HEAD's own 4-case
  hostile oracle (`ordinary-exception`,
  `raising-repr-and-str`, `raising-argument-representation`,
  `raising-type-name`) constructs exactly this and asserts the
  wire message stays the constant; the worktree collapse to one
  ordinary case follows production. Reaching input: any
  operation against such a schema, plus the two construction
  configs. Routing endorsed: truth-migration owner,
  maintainer-decided containment-restored vs
  propagation-accepted; no security-path routing (diagnostic
  seam, fail-open shape already in HEAD's oracle).
- **CONFIRMs R3/R5/R7/J1/J3/J4: CONFIRMED.** R3 logic
  byte-identical (one comment-only hunk, itself accurate: one
  flag field); fallback reads both `_PACKAGE_*` copies and both
  properties hand out `copy_policy` duplicates at both states,
  matching verified File `utils/policies.py` F2
  (re-verified fresh here since F2's schema fingerprint is the
  drift base). R5 `_refusal` spelling byte-identical at both
  states; the bypass home (verified File `utils/errors.py` F9,
  family undispatched) endorses "no change". R7 `_masked_return`
  byte-identical with the `_PACKAGE_ERROR_POLICY` floor. J1
  owner-plus-two with the head/tail distinction intact. J3
  alive 1/1 at both states, shared field unrenamed on both
  sides. J4 all eleven absences at zero in worktree.
- **Hunk attribution (23/23): CONFIRMED.** Each hunk mapped by
  content: 14 truth-migration (2 import, 1 `static_attr`, 5
  render, 4 `is_instance` incl. the twin's own check, 2
  `is_type`, 1 `is_subclass`), 9 prose, `_subscribe` inside
  hunk 17. The `## Owned changes` ledger names no hunk on this
  path; every hunk matches the concurrent truth migration or
  concurrent prose. No hunk touched.
- **Challenges C26–C33: CONFIRMED.** Each counts 1 at the
  stated site/owner per the censuses above; C3–C4 re-home to
  the `truth.describe` owner; C1–C2 moot with zero code sites
  here.
- **Index bullets (13/13): ENDORSED as stated.** Each bullet
  was discharged by the judgments above; Worker-0 may
  transcribe them verbatim.

### Errata corrected to the body (substance unaffected)

- **E1 — method totals.** W1's "32 class-body methods (5 + 8 +
  0 + 5 + 11)" and "33 (5 + 8 + 0 + 5 + 12)" mis-sum their own
  correct decompositions: HEAD is 29, worktree 30
  (method-name listing re-derived independently). Coverage is
  unaffected — every member change is accounted in the
  attributed delta — but the totals and the Judgment's
  "32/32" should read 29/30.
- **E2 — D1 contract-row label.** The never-raising
  containment row W1 quotes ("factory-raised ... refused
  rather than allowed to escape") is the prior F2
  (`typed-rejection-value-tail`) contract — "renders its tail
  through one never-raising renderer, so the message assembly
  cannot replace the promised error", with "the
  factory-raised containment" a named pinned site — not R4
  (chain order/admission). The defect, shape, and reaching
  input are unchanged; only the finding label moves to F2
  (F2-at-R4's-site).

### Taken on trust (judgment-neutral)

The exact 0.319 upstream band boundary (concurrent prose;
either side of it the twin counts 1 here); the
migration-wide "246 render-family sites" (mine is 259 over 53
modules at this worktree instant — concurrent drift in
scene-setting, not in any verdict).

### Gates and execution

Zero-edit file item: no production edits by either worker, no
`proof:`/`gate:` owed. Every claim above is static against the
three states plus installed-upstream reads; probes were
read-only under `/tmp` and opened no database, so no workspace
copy and no sharded/Postgres cell were owed. No pytest ran
(not authorized). `uv run ruff check` and `uv run ruff format
--check` on the touched path (this artifact only): clean (no
Python files under it). Prose rules hold: `path::Symbol`
citations, no process provenance.

### Judgment

Backstop re-discharged fresh: every REVISE re-derived, the R2
closure and R2' addition confirmed, D1 confirmed routable, all
23 hunks attributed concurrent-external, all 13 index bullets
endorsed, two errata corrected to the body with no judgment
affected. `Status: verified`, no pending execution.

Exact plan rows for Worker-0 (plan edits are Worker-0's alone;
Worker-2 touches no plan line):

Tick (replaces the line-85 `REOPENED` row):

- [x] File `schema.py` — [dry-file-schema.md](dry-file-schema.md) —
  verified (Run 0.0.15 2026-09-29-7 at `0c0537e2`; zero edits,
  D1 routed, no pending execution; W2 errata E1 method totals
  29/30, E2 D1 row F2 — both judgment-neutral)

Index rows: the 13 `## Index rows for Worker-0` bullets in the
run-7 W1 section above, endorsed verbatim (one-sync-boundary
drop; three family-site confirms plus the executor-mode pair;
three file-local REVISEs; the R2 CLOSE plus per-window-thread
ADD; three file-local CONFIRMs; the truth-consumer row with
File `utils/truth.py` queueing; the J2 rejection REVISE; D1
routing).

## Run-8 re-trace at `83998e08` (Worker-1)

Run 0.0.15 2026-09-30-8. The verified record above through run-7
verification is prior evidence only; what follows re-traces fresh at
HEAD bytes with the worktree delta scoped and attributed. Zero
production edits; one worktree-only defect persists (D1, run-7,
still routed).

### Scope of the delta

Fingerprints: drift base `0c0537e2` blob `e6b52335` (1410 lines),
HEAD `83998e08` blob `bba03d7d` (1366 lines), worktree blob
`abad5795` (1367 lines), pre-merge `9aaaad5d` blob `f4e807e9`
(1437 lines). HEAD unmoved for the whole pass. `ITEM_BASELINE`
`219de42d9c750ff9f9e8f5c86ce7d4b6ce151e13` diffs empty (0 bytes)
on this path: the HEAD-to-worktree dirt below predates the item.

Drift-base-to-HEAD is five commits on this target. `005b1f53`
(behavior, the only one): the async mutation window is now one
sync call on its own thread via a shared `_run_window` body that
sync and async both use; `_MutationWindowThread` (with its
repeated-cancellation wait loop and entered bookkeeping) is
removed; this module gains its first code-level
`sync_to_async`/`async_to_sync` call sites (window mechanics,
two sites in
`django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`,
distinct from the per-resolution boundary). The four typing
commits move no rule ownership: `999a1aab` (`NoReturn` on
`on_execute`), `b20277fe` (narrowest-true annotations,
`TYPE_CHECKING` block, `_WindowT` TypeVar, `_stream` cast),
`849f67bc` (`@override` markers), `dfbea72b`
(`GraphQLObjectType | None`). Floor
`strawberry-graphql>=0.316.0` to `>=0.322.2` lands at HEAD with
no schema.py hunk; the `DjangoSchema._subscribe` twin is dead
across the supported band (upstream has no `_subscribe`;
`subscribe` delegates to `stream`, bodies read at installed
0.324.0).

HEAD-to-worktree is 31+/30-, every hunk concurrent-external: no
`## Owned changes` ledger row names this file. By content: the
`cast` import drop plus the `truth` import (2 import hunks); one
`truth.static_attr` head read (`execute_field`); five
`describe_value` to `truth.describe` conversions (extensions
setter, factory-exception reason, two resolved-member reasons,
subclass-declaration refusal); three `issubclass(type(...))` to
`truth.is_instance` conversions (`_stream`,
`_is_resolvable_extension_entry`, `_is_extension`); two to
`truth.is_type` (`_entry_resource_policy`, `_entry_type`); one
to `truth.is_subclass` (`_extension_entry_matches`); nine prose
hunks (the `0.0.14` drop, the execution-split header, the
context and refusal docstring first lines, the graphql-core
`3.2.9` to `3.2.10` claim, the two-flags to a-flag fix, the
population to claimed-authority noun fix, the factory-comment
rewrite, the `_stream` narrowing-comment drop with the cast).
No `_subscribe` in either state (0 hits package-wide at both).
Every hunk left untouched.

### Enumeration (fresh instrument)

Instrument: `ast.parse` over each state's pinned bytes,
`ast.Module.body` plus every class-body method. HEAD: **58
members** (1 docstring + 25 `ImportFrom` + 4 `Import` + 1
`If` (`TYPE_CHECKING`, 7 names) + 7 `Assign` + 2 `AnnAssign` +
14 top-level `FunctionDef` + 4 `ClassDef`) with **25 methods**
(9 + 0 + 5 + 11). Worktree: **59 members** (26 `ImportFrom`,
same otherwise) with **25 methods** (same lists).
Pre-merge `9aaaad5d`: **57 members** (25 `ImportFrom` + 4
`Import`, no `If`, 6 `Assign`, 5 `ClassDef`) with **30 methods**
(5 + 8 + 0 + 5 + 12). Population 117 `.py` at HEAD, 119 in
worktree (untracked `utils/truth.py` plus `utils/lazy.py`,
neither in HEAD).

HEAD member homes (0-57; methods in parentheses count
`extensions` twice for getter/setter): 0 module docstring
projection (R1''/R2''); 1 `__future__` machinery; 2 `asyncio`
machinery (R2'' `CancelledError`); 3 `contextlib` machinery
(R2'' suppress); 4 `functools` machinery (R1'' sync partial);
5 `collections.abc` machinery; 6 `ThreadPoolExecutor`
machinery (R2''); 7 `dataclasses` machinery (R3); 8 `typing`
machinery (annotations + `_stream` cast); 9 `strawberry`
machinery (R3 base); 10 `asgiref.sync` machinery (R2''
mechanics, distinct from F1); 11 `django.db` machinery (R1''
atomic + R2'' close); 12 `TransactionManagementError`
machinery (R1''); 13 `graphql` machinery (R5 + R1''); 14
`ExecutionContext` machinery (R1 base); 15 `SchemaExtension`
machinery (R4/R5); 16 `OperationType` machinery (R5); 17
`override` machinery (typing); 18 `logger` consumer (owner
`__init__.py::logger`); 19 error-policy ladder consumer (R3/R7;
driver `resolve_policy`); 20 `ConfigurationError` +
`describe_value` guard + renderer (F2 + R4 raises); 21
masking-authority + four gates consumer (R4/R7); 22 runner +
marker consumer (R6''/R4); 23 budget-authority + guard consumer
(R4); 24 `MUTATION_CLASS_MARKER` consumer (R1''; J1); 25
resource-policy ladder consumer (R3); 26 mode fact + dispatch
consumer (R1''/R4); 27 `copy_policy` consumer (R3); 28
private-state primitives consumer (R3); 29 write seam + alias
consumer (R1''); 30 `If TYPE_CHECKING` machinery (typing-only);
31 `_WindowT` machinery (typing TypeVar); 32
`_CLOSED_WINDOW_MESSAGE` R1'' file-local; 33
`_close_thread_connections` R2'' file-local; 34
`DjangoMutationExecutionContext` (9: `execute_field`,
`_marked_mutation_class`, `_execution_errors`,
`_rollback_for_new_errors`, `_refuse_uncommitted_window`,
`_exit_window`, `_run_window`, `_execute_mutation_field_sync`,
`_execute_mutation_field_async`) R1'' + R2'' file-local; 35
wire code R5 file-local; 36 `_SchemaEnforcement` R3 file-local;
37 `_SCHEMA_ENFORCEMENT` R3 file-local; 38 `_SCHEMA_EXTENSIONS`
R3 file-local; 39 `_FALLBACK_ENFORCEMENT` R3 file-local; 40
`_enforcement` R3 file-local; 41-43 refusal messages + docs R5
file-local; 44 `_refuse_operation_document` R5 file-local; 45
`_RefusedConfiguration` (5) R5 file-local; 46 `_refused_chain`
R4 file-local; 47 `_operation_mode` R4 file-local; 48
`DjangoSchema` (11: `__init__`, `extensions` x2,
`resource_policy`, `error_policy`, `get_extensions`,
`create_extensions_runner`, `execute_sync`, `execute`,
`_masked_return`, `_stream`) R3/R4/R6''/R7 file-local; 49-57
the nine chain helpers R4 file-local. No member unassigned.

Delta reconciliation naming every change: run-7 HEAD (56
members, 29 methods 5+8+0+5+11) to current HEAD (58, 25
9+0+5+11): minus `Class _MutationWindowThread` (5 methods)
per `005b1f53`; plus `If TYPE_CHECKING` and `Assign _WindowT`
per `b20277fe`; plus `def _run_window` in the context (8 to 9)
per `005b1f53`; plus `override`/`NoReturn`/annotation-only
edits inside existing members per the typing commits. Current
HEAD to worktree (59, 25): plus `from .utils import truth`
(26th `ImportFrom`); minus the `describe_value` name from row
20 and the `cast` name from row 8; method lists identical.
`9aaaad5d` (57, 30 5+8+0+5+12) carries the pre-merge pair:
`_MutationWindowThread` plus the `_subscribe` twin, both gone
at HEAD and worktree (0 hits package-wide at both).

### Matrix re-discharge (HEAD bytes plus worktree delta)

**1. Cross-flavor.** Single-definition sweeps re-run at both
states over 117/119 files: `DjangoSchema`,
`DjangoMutationExecutionContext`, `_admitted_chain`,
`_refused_chain`, `_SchemaEnforcement`,
`_RefusedConfiguration`, `_refuse_operation_document`,
`_masked_return`, `_run_window`, `_close_thread_connections`,
`_exit_window`, `_refuse_uncommitted_window`,
`_operation_mode`, `_stream` each hit once;
`_subscribe`, `_MutationWindowThread`, `_AcquireHandoff`,
`_AsyncAliasLock`, `_async_mutation_lock` hit zero.
`MUTATION_CLASS_MARKER` readers still owner plus two (schema
tail, resource tail; 7 hits at both). `copy_policy` two call
sites, one `resolve_*_policy` call each, at both. The wire
code hits only its definition plus its use plus the two
`__init__.py` re-export lines (4 hits at both). No second
schema rule outside this file.

**2. Sync/async twins.** Three pairs, compared by behavior.
(a) `_execute_mutation_field_sync` vs
`_execute_mutation_field_async`: now sharing one `_run_window`
body (sync passes a `functools.partial` over
`super().execute_field` on the calling thread; async passes
`async_to_sync(complete)` on a private single-thread
executor, or the blocked caller's thread when
`AsyncToSync.executors.current` is set). The split is the
recorded principle-5 shape with one body plus execution
adapters: the only code-level `sync_to_async`/`async_to_sync`
sites in this module (import once, each called once) are the
async adapter's thread mechanics, not a second boundary.
Upstream `execute_field` placement (sync completes inside the
call, async returns an awaitable) still forces the adapter
split; the atomic lives on the thread's own stack so
cancellation cannot strand it. (b) `execute_sync` vs
`execute`: one `super()` call plus one `_masked_return` each,
unchanged. (c) `get_extensions` `sync=True` vs `sync=False`:
one flag, one `_operation_mode` body, both chains threading
it. The `_stream`/`_subscribe` twin pair is gone: `_stream`
alone covers every streamed operation (`subscribe` delegates
to `stream` upstream). No drift beyond the D1 contract
difference (worktree-only).

**3. Derived knowledge.** Alias from `resolve_write_alias`,
mode from the upstream `sync` flag, policies from the resolve
ladder plus `copy_policy` per read, marker from the imported
constant, fallback and floor from the `_PACKAGE_*` canonical
copies, identity facts from `truth.*` in worktree (12 sites)
versus the `issubclass(type(...))` idiom at HEAD (6 sites):
zero restatements at either state.

**4. Round-trip pairs.** Settle/recall/accept balance intact
at HEAD (`settle` twice, `recall` once plus `settled` once;
`accept` once, `recall` twice); admit/refuse orders verbatim
at both (error-first, resource-last, guard-behind-consumers,
marker-behind-guard; refused keeps both package authorities);
parse/refuse (three documents, one-read `tuple` snapshot, name
clearing); mask-twice identity. No second grammar; the twin
wrappers collapse to one.

**5. Other media.** HEAD oracles still pin the window
(hostile-container rows, completion-rollback live rows), the
chain (factory-count, hybrid, slotted rows), the snapshot
(`tuple`-exact, one-shot, no-parser rows), the masking seam
(identity, degrade, hook rows), and the streamed binding (the
`_stream` passthrough row plus refused-stream rows). Worktree
oracle turnover is concurrent-external and recorded, not
judged: the 4-case hostile factory-exception oracle collapsed
to one ordinary case (D1 evidence; 64 defs at HEAD, 63 in
worktree), the `_subscribe` passthrough row is gone with its
seam (0 hits at both), the claiming-instance params live at
the truth owner's tests. Every HEAD oracle spells its
expectation independently and would fail, not follow, a
production change.

**6. Enforcement by omission.** Marked-mutation guards
intact; every entry shape typed and claim-checked; all three
operation types refused; streamed frames bound through
`_stream` on every transport (`subscribe` needs no override);
executor-by-hook-escape census unchanged. One gap persists:
the five refusal/rejection message sites have no hostile
render in worktree (Defect D1, run-7, worktree-only) -- a
broken guard, not a missing one. No new gap at HEAD.

### Prior-finding verdicts (fresh evidence)

CONFIRM (10, verdicts stand; counts re-censused): F1
left-the-family (HEAD 1 prose mention, 0 code sites; owner
`utils/querysets.py::run_in_one_sync_boundary` alive; the two
window-mechanics call sites are distinct, counted under
R2''); F2 owner-deleted-in-worktree (HEAD 5 `describe_value`
sites plus the never-raising owner plus the 4-case oracle;
worktree 5 `truth.describe` sites with the propagating
`render`, oracle collapsed; D1 persists); R3
enforcement-record (logic byte-identical modulo annotations;
`_PACKAGE_*` split intact; two `copy_policy` handouts); R4'
chain admission (real-type halves intact; admitted/refused
orders verbatim at both; worktree 6 truth predicates; the two
unconverted exact-type sites narrowed, same idiom); R5 refusal
(machinery identical; `_refusal` bypass of
`coded-error-extensions-shape` intact); R7 masking seam
(overrides, gates, fail-closed floor identical; third
enforcement site stands); J1 marker-tail (owner plus two,
trigger unfired; `truth.static_attr` touches the head, not
the tail); J2 exact-type idiom (trigger fired externally via
6 worktree conversions; HEAD idiom stands rejected; per-site
`__class__` docstrings accurate); J3 pre-execution publishing
(`restate_admission_verdict` alive, field unrenamed, trigger
unfired); J4 inapplicable surfaces (all 11 absences re-swept
at zero in both states).

REVISE (3): R1' completion window to R1'' (shared `_run_window`
body; twin verdicts below); R2' per-window thread to R2''
(re-derived without `_MutationWindowThread`); R6' streamed
binding to R6'' (re-derived without the `_subscribe` twin).
R2 stays CLOSED. No new family named.

Window-body twin judgment: main's consolidation (two window
bodies sharing `_exit_window` into one `_run_window` body
with two one-line adapters) strengthens the file-local
verdict on both twins. A change to the window logic (error
counting, alias threading, atomic enter/exit, failure-rule
wiring) now moves 1 definition (`_run_window`) instead of 2;
the sync/async split that remains is the forced adapter
(calling thread vs private thread plus await placement),
which no single body can absorb without interleaving ORM
work with awaits inside the transaction. F1 stays out (0 code
sites; the async adapter's `sync_to_async`/`async_to_sync`
are thread mechanics for the window itself, not the
per-resolution boundary the pipeline consumes). No twin
drifts; no new family.

### Challenges

C1-C2 moot here (0 code sites; 1 each at the querysets
owner). C3-C4 to 1 each (HEAD `describe_value` owner;
worktree `truth.describe` owner with D1). C5-C7, C10-C11,
C12-C14 (C30 same), C15-C17, C18-C19 (C31 same), C21-C24
stand at 1 each as mapped. C20 refused (0). C25 0 here (home
`list_field.py`). C8-C9 stay superseded.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C26 | R1'' closed-connection rule | new uncommitted-window shape | **1** (`_refuse_uncommitted_window`) | file-local |
| C27 | R1'' exit sharing | third failure rule | **1** (`_exit_window`) | file-local |
| C28 | R2'' thread ownership (REVISED) | shared-executor window | **1** (`_execute_mutation_field_async` mechanics + `_close_thread_connections`, one file; was `_MutationWindowThread`) | file-local |
| C29 | R2'' connection close | backend-handle rule change | **1** (`_close_thread_connections`) | file-local |
| C30 | R4' claim halves | third claim kind | **1** (resolved + entry halves, one file) | file-local |
| C31 | R6'' resume binding (REVISED) | new frame binding | **1** (`create_extensions_runner` + `_stream` alone, one file; twin gone) | file-local |
| C32 | render contract | never-raising tail | **1** (HEAD `describe_value` owner; worktree `truth.describe` owner with D1; 5 sites follow) | consumer + D1 |
| C33 | predicate mechanism | new hostile-metadata shape | **1** (worktree `truth` owner, 6 sites follow; 0 here at HEAD, refused idiom) | consumer |
| C34 | R1'' shared body (NEW) | window must carry a new fact through both adapters | **1** (`_run_window`; sync partial + async `window()` follow) | file-local |

Read-only probes only (`ast.parse` dumps, `git grep` /
`grep -rn` censuses against pinned bytes, `git show` body
reads, installed-upstream reads at strawberry-graphql 0.324.0
/ graphql-core 3.2.8 / asgiref 3.11.1, floor
`strawberry-graphql>=0.322.2` from `pyproject.toml`). No
source mutation, no database, no shared-tree pytest, no
workspace copy owed.

### Findings (run-8 deltas)

**R1'' -- completion-spanning mutation window (REVISED,
file-local).** Contract unchanged (one
`transaction.atomic(using=alias)` per top-level generated
mutation field, held through completion; two failure rules:
new errors roll back, closed-in-transaction fails the field
with a located error). Sites: `execute_field` (dispatch),
`_marked_mutation_class` (scope + J1 tail), `_execution_errors`
(dual-arm container), `_rollback_for_new_errors` (error
rule), `_refuse_uncommitted_window` (closed-connection rule),
`_exit_window` (shared exit), `_run_window` (shared body,
NEW), `_execute_mutation_field_sync` (sync adapter),
`_execute_mutation_field_async` (async adapter + R2''
mechanics). Challenges C5-C7, C26-C27, C34 to 1 each here.
Owner stays this context (only layer seeing resolve plus
completion). Behavioral proof `static-reviewed` (all nine
bodies plus upstream `execute_field` placement read) with the
window live rows plus the hostile-container rows as oracles
(`005b1f53` records behavior plus assertions unchanged).
Gate: the hostile-container rollback rows (bypassing the
window leaves the write committed on exactly those rows).
Trigger: a second completion-spanning window.

**R2'' -- per-window thread mechanics (REVISED, file-local;
successor to R2').** Contract: one async window's ORM work
runs on one thread nothing outside it shares (private
single-thread executor outside a blocked sync caller; the
caller's thread under one, nesting in its transaction), and
the private thread's connections close when the window ends.
Sites: `_execute_mutation_field_async` (caller detection via
the one asgiref attribute `AsyncToSync.executors.current`,
executor ownership, `cancelled` flag plus `SyncToAsync`
propagation, `shutdown(wait=False)`) plus
`_close_thread_connections` (close plus raw-handle drop,
`DatabaseError` suppressed). `_MutationWindowThread` (5
methods) is deleted with 0 hits package-wide at both states;
the old R2' record closes with it. Challenges C28-C29 to 1
each here. No second window thread exists. Trigger: a second
cross-operation thread owner.

**R6'' -- streamed-operation binding (REVISED, file-local).**
Contract: every streamed frame resumes with this operation's
extensions bound. Sites: `create_extensions_runner` (runner
factory) plus `_stream` (resume wrapper with the
non-package-runner passthrough). `_subscribe` is gone (0
definitions package-wide at both states; upstream has no
`_subscribe`; `subscribe` delegates to `stream`). Challenges
C18-C19 plus C31 to 1 here. The mode marker travels in the
chain the runner reads, so refused and admitted streams bind
identically. Trigger: a second streamed-binding wrapper.

CONFIRM notes (fresh evidence, verdicts stand): F1 0 code
sites at both (1 prose mention); F2 5 sites at both with the
HEAD 4-case oracle intact; R3 record/stores/settle/accept
plus two `copy_policy` handouts intact; R4' orders verbatim
at both with 6 worktree truth predicates; R5 three documents
plus `tuple`-exact snapshot intact; R7 overrides plus four
gates plus fail-closed floor intact; J1 owner-plus-two
intact; J2 6-site worktree consolidation (HEAD idiom
rejected); J3 1/1 alive at both; J4 11/11 absences at zero at
both.

Freshness (full blobs): target HEAD
`bba03d7de419beb36cb2a53bf6ad9400bc01c452` (1366 lines),
worktree `abad57953367b35b23d7102ca01bfe30011cee65` (1367
lines), pre-merge `9aaaad5d`
`f4e807e9e64c1a38e03942705299f5636ba2dd35` (1437 lines);
`exceptions.py` HEAD
`f27e1f91d4021a6a1f8310f9a20d59b1e03f83a8` / worktree
`34e2e6be57e8e173200e35193ce397aca4e58b69`;
`utils/truth.py` worktree
`cc4bbe014c2a66b27751df1b56e28931f5773bab`
(untracked, no HEAD); `utils/querysets.py` HEAD
`392e50d085c5b5a15c850a9a69b0f1b50e8529a4` / worktree
`cfc773ba8d4fa2d5f79b70d4cd0539f33b7166bd`;
`tests/test_schema.py` HEAD
`20d542ac25570c1ab9721ced4726e45b032cb747` / worktree
`4c695dd9d65230bab8a906cda5a993b108b75e1b`;
`utils/policies.py` HEAD `4b180e2b` / work `8d02c54b`;
`resource_policy.py` HEAD `47befb3f` / work `927b89a2`;
`error_policy.py` HEAD `000f594c` / work `c55a23d8`;
`extensions/error_policy.py` HEAD `2ccfde1b` / work
`641b1ed1`; `extensions/resource_policy.py` HEAD `5cc373ec`
/ work `8944e79e`; `extensions/operation_state.py` HEAD
`8df7d2e6` / work `50526c85`; `utils/private_state.py` HEAD
`ec4d8fc8` / work `613a28ca`; `utils/execution_mode.py`
`b86a08cd` (clean); `utils/write_transaction.py` HEAD
`c0a12b34` / work `49102e69`; `mutations/fields.py` HEAD
`8d3ce7e2` / work `c6da2e54`; `conf.py` HEAD `10096f84` /
work `8092d80b`; `__init__.py` `8b165672` (clean). Searched
population 117 `.py` at HEAD, 119 in worktree. Upstream
installed strawberry-graphql 0.324.0, graphql-core 3.2.8,
asgiref 3.11.1; floor `strawberry-graphql>=0.322.2`.

### Defects

**D1 persists (run-7, worktree-only, 5 sites).** The five
`truth.describe` sites build refusal reasons and typed
rejections from consumer-controlled objects with a renderer
whose non-scalar path propagates `__repr__` exceptions
(`utils/truth.py::render` docstring plus body read). Contract
row: the prior F2 never-raising-containment row (run-7 erratum
E2 label). Feasible shape: a factory raising an exception
with a raising `__repr__` under
`DjangoSchema(extensions=[factory])` (HEAD's own 4-case
hostile oracle constructs exactly this). Reaching input: any
operation against such a schema (`get_extensions` runs
outside upstream's converting `try`, bodies read at installed
0.324.0) plus the two construction configs. Routing stands:
truth-migration owner (File `utils/truth.py` still untracked,
still blocked); maintainer decides containment-restored vs
propagation-accepted. No security-path routing (diagnostic
seam, shape already in HEAD's oracle). No new defect found at
HEAD: every re-checked claim held, no new unguarded member,
no new missing guard.

### Pending execution

None. Every claim is static against the three states plus
installed-upstream reads; probes were read-only, mutated no
source and opened no database, so no workspace copy was owed.
No pytest ran (none authorized beyond the one focused
`--no-cov` allowance, which this zero-edit item did not
need). No sharded/Postgres cell owed: definition counts,
single-site facts, chain-order literals, and prose statements
touch no database, alias, or dialect decision
(`inapplicable by construction`; alias resolution owned at
`resolve_write_alias`).

### Judgment

Backstop re-discharged: 58/58 HEAD members plus 25/25 methods
enumerated with the worktree (59/25) and pre-merge (57/30)
reconciliation above, matrix re-run against the real current
surface, 10 prior findings CONFIRMed with fresh censuses, 3
REVISEd with proving challenges (R1'' shared body, R2''
without `_MutationWindowThread`, R6'' without `_subscribe`),
one worktree-only defect persisting routed, zero production
edits. The drift delta is one mechanism consolidation plus
typing-only plus the floor-raised twin death; the worktree
delta is the truth migration plus prose.

### Item-scoped diff state

`git diff 219de42d9c750ff9f9e8f5c86ce7d4b6ce151e13 --
django_strawberry_framework/schema.py` is empty (0 bytes);
`git diff HEAD -- django_strawberry_framework/schema.py` is
31+/30-, every hunk attributed above by content to
concurrent-external work (truth migration plus prose); the
`## Owned changes` ledger names no hunk on this path. No
tracked file edited except this artifact; no commit. Scratch
is read-only probes only (no files written). `Status:
ready-for-verification/1`.

## Index rows for Worker-0 (run-8)

(Worker-0 alone edits the plan; rows named here for
transcription. Prior run-7 rows stand except as revised
below.)

- File-local REVISE `completion-spanning-mutation-window`:
  owner
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext`
  (two failure rules, `_exit_window`, shared `_run_window`
  body with sync/async adapters).
- File-local REVISE `per-window-mutation-thread`: owner
  `django_strawberry_framework/schema.py::DjangoMutationExecutionContext._execute_mutation_field_async`
  (with `_close_thread_connections`;
  `_MutationWindowThread` deleted at `005b1f53`).
- File-local REVISE `streamed-operation-binding`: owner
  `django_strawberry_framework/schema.py::DjangoSchema._stream`
  (with `create_extensions_runner`; `_subscribe` twin dead
  at the `0.322.2` floor, 0 hits).
- Family-site confirm `one-sync-boundary`: `schema.py` stays
  out (0 code sites at HEAD and worktree, 1 docstring prose
  mention; the two window-mechanics `sync_to_async` /
  `async_to_sync` sites are distinct, counted under
  `per-window-mutation-thread`). No change.
- Consumer-row update `truth` consumption: `schema.py` uses
  12 `truth.*` sites in worktree (1 `static_attr`, 5
  `describe`, 3 `is_instance`, 2 `is_type`, 1 `is_subclass`),
  0 at HEAD -- holding File `utils/truth.py` still untracked,
  still blocked.
- Defect D1 persists (5 sites, worktree-only): route stands
  to the truth-migration owner; maintainer decides
  containment-restored vs propagation-accepted.
- File-local CONFIRM `enforcement-record-holding`,
  `chain-admission`, `refusal-substitution`,
  `returned-result-masking-seam` (typing/prose only, no
  structural change); family-site confirms
  `policy-authority-isolation`, `coded-error-extensions-shape`,
  `subscription-per-event-error-masking`,
  `carried-operation-executor-mode`,
  `async-execution-dispatch-decision` stand with no change.

## Independent verification (run 8)

Expectation-first at HEAD bytes (`83998e08`, confirmed unmoved
at finish). Read order kept: the governing docs, the queue
record's run-8 section, the owned-changes ledger, the full
target at HEAD bytes (1366 lines, read whole), the five
drift-base-to-HEAD commits on the target in full, the
HEAD-to-worktree diff in full (23 hunks at -U0), the connected
sources at HEAD bytes, both oracle files, the installed
upstream plus the 0.322.2 floor wheel. Then the run-8
submission, reconciled row by row below. Instruments (all
read-only, `/tmp`-only, no Django import, no DB, no source
mutation, no pytest): `/tmp/w2_schema_probe.py` (AST
enumeration + token censuses), an `ast` member-order dump,
scoped `git grep` / `grep` censuses, a 17-path freshness
re-hash, the floor-wheel `_subscribe` check. No sibling-role
scratch under `docs/dry/` was opened.

### Own trace (drift delta at HEAD bytes)

Drift base `0c0537e2` to HEAD on the target is exactly 5
commits, one carrying behavior (`git log` names `005b1f53` +
4 typing commits; no other commit touches the target).
`005b1f53` (6 hunks, read whole): module-docstring async
rewrite; import block (`contextvars` out, `functools` in,
asgiref `SyncToAsync` / `ThreadSensitiveContext` out,
`async_to_sync` / `sync_to_async` in);
`_close_thread_connections` docstring line;
`_MutationWindowThread` deleted whole (5 methods); `_run_window`
added with the sync adapter reduced to a `functools.partial`
plus one call; the async adapter rewritten as `complete()` +
`window()` + private-executor mechanics. Nothing in the commit
reaches the enforcement record, the chains, the refusal
machinery, the runner binding, or the masking seam (hunk line
ranges checked). The 4 typing commits move no rule: `999a1aab`
is 2 lines (`NoReturn` import + `on_execute` retype);
`849f67bc` is `@override` markers + one ignore comment;
`dfbea72b` is 1 annotation; `b20277fe` (129 changed lines, read
whole) is annotations, the `TYPE_CHECKING` block, `_WindowT`,
and one `cast` (runtime identity) with its comment. The floor
`strawberry-graphql>=0.322.2` lands with no schema.py hunk; the
floor wheel itself carries `def _subscribe` zero times, so the
twin is dead at the floor, not only at installed 0.324.0.

Window mechanics, my reads: `_run_window` (def + exactly 2
calls, one per adapter) holds errors-before, alias atomic
enter, `managed_write_transaction` around `run()`,
BaseException exit + raise, `_exit_window`, return. Sync
adapter: partial + call. Async adapter:
`getattr(AsyncToSync.executors, "current", None)` caller
detect; private single-thread executor only without a caller;
`sync_to_async(window, thread_sensitive=executor is None,
executor=executor)()`; `cancelled` flag set on
`CancelledError` and raised on `complete()` entry;
`executor.shutdown(wait=False)` in `finally`; `window()`
closes thread connections only without a caller.
`_close_thread_connections` kept: per-connection close,
raw-handle drop, `DatabaseError` suppressed. `sync_to_async(`
once in code, `async_to_sync(` once in code (a second hit of
each is docstring prose), both inside the async adapter.

### Per-row judgments (13 rows, my counts)

- **F1 CONFIRM (stays out).** 0 code sites, 1 docstring mention
  at both states; no boundary import; owner a single `async
  def` alive at both. The 2 mechanics sites are R2'' thread
  ownership, not the shared-thread discipline (judgment below).
- **F2 CONFIRM.** HEAD: 5 `describe_value(` calls plus the
  never-raising owner (`def` + `except BaseException` arms
  read) plus the 4-case hostile oracle intact. Worktree: owner
  deleted, 0 package-wide `describe_value` hits, 5
  `truth.describe(` sites, oracle collapsed to 1 ordinary case.
  D1 persists (below).
- **R3 CONFIRM.** Fallback reads both `_PACKAGE_*` copies; 2
  `return copy_policy(` handouts; 1 `resolve_*_policy(` call
  each; settle twice / recall thrice / accept once / settled
  once; untouched by `005b1f53`, annotations-only typing.
- **R4' CONFIRM.** Admitted / refused orders verbatim identical
  at both (`[error, *resolved, resource, guard, marker]` /
  `[error, refused, resource, marker]`); one `_operation_mode`
  body; flag threaded through all `get_extensions` paths; 6
  converted predicates + exactly 2 unconverted checks
  (`type(policy) is`, `isinstance(parent_fields, dict)`).
- **R5 CONFIRM.** 3 `OperationType` documents; `tuple(...)`
  snapshot; refusal extension 5 methods; `_refusal` bypass
  spelling intact.
- **R7 CONFIRM.** 4 gates called once each; fail-closed floor;
  `def _masked_return(` single-sited; third-enforcement-site
  structure intact.
- **R1'' REVISE.** Shared `_run_window` body + 2 adapters; C34
  = 1 (def + the 2 adapter calls, my grep). Two failure rules
  + `_exit_window` intact. Window live rows + hostile-container
  rows stand as oracles.
- **R2'' REVISE.** `_MutationWindowThread` 0 hits package-wide
  at both; `ThreadSensitiveContext` / `contextvars` 0 in code
  (2 prose mentions); mechanics as traced above; C28 / C29 = 1
  each, one file.
- **R6'' REVISE.** `_subscribe` bare symbol 0 package-wide at
  both (3 `handle_subscribe` hits in `consumers.py` are the
  other symbol); floor + installed upstream carry no
  `_subscribe`, `subscribe` delegates to `stream`; factory +
  `_stream` with the non-package passthrough; foreign-runner
  row + refused-stream rows stand; C31 = 1.
- **J1 CONFIRM.** Marker 7 hits at both (owner 2 + resource 3
  + schema 2); schema tail intact; `truth.static_attr` touches
  the `execute_field` head read, not the tail; trigger unfired.
- **J2 CONFIRM.** 6 worktree predicate conversions meet the
  three-or-more trigger; HEAD idiom stands refused; per-site
  `__class__` docstrings read accurate.
- **J3 CONFIRM.** `def restate_admission_verdict` + 2 calls at
  both; shared upstream field unrenamed; trigger unfired.
- **J4 CONFIRM.** All 11 absences at 0 in both states, my
  census.

### Enumeration

My instrument (`ast.parse`, `Module.body` + every class body
counting `AsyncFunctionDef` as a method): HEAD 58 members (1
docstring + 25 `ImportFrom` + 4 `Import` + 1 `If` + 7 `Assign`
+ 2 `AnnAssign` + 14 `FunctionDef` + 4 `ClassDef`) with 25
methods (9 + 0 + 5 + 11); worktree 59 / 25; pre-merge 57 / 30
(5 + 8 + 0 + 5 + 12). Member order 0-57 reproduces the
submission's table index for index; method-name lists match in
order. (A first instrument counting `FunctionDef` only gave
23 / 23 / 26; adding the async defs reproduces 25 / 25 / 30.
The correction is in the instrument; the totals were right.)
Delta naming agrees: minus the thread class, plus `If` +
`_WindowT`, plus `_run_window`, plus in-member typing edits;
worktree adds the `truth` import and drops 2 names. 58 / 58
homed, none unassigned.

### Hunks (23 / 23 concurrent-external)

The item-baseline diff on the target is 0 bytes; the
HEAD-to-worktree dirt (31+ / 30-, 20 hunks at -U3, 23 at -U0)
predates the item. The ledger names no hunk on this target. My
content map: 3 import-region hunks (cast drop, `describe_value`
drop, `truth` add), 1 `static_attr` head read, 5 render
conversions, 6 predicate conversions, 8 prose-only hunks (the
`_stream` narrowing-comment removal rides fused with its
predicate hunk at -U0; the submission counts 2 + 9 where I
count 3 + 8 — same 23, grouping only). Every hunk matches the
package-wide truth migration or concurrent prose; none touches
`_run_window`, the adapters, `_exit_window`,
`_close_thread_connections`, the chains, the refusal documents,
or the masking seam; the `cast` removal is runtime-identity.
Chain orders re-verified verbatim after the conversions. No
hunk moves any fingerprinted verdict.

### F1 judgment (file evidence for the s20 re-trace)

The left-the-family call survives the new mechanics sites. The
owner body is one line — `await
sync_to_async(fn, thread_sensitive=True)(...)` — running a
callable on the ambient shared thread: one shared thread per
resolution, the discipline every async surface shares. The
window adapter instead creates, owns, and destroys its own
executor (or borrows the blocked caller's thread) and drives
completion through `async_to_sync`: it is the thread the
boundary's work lands on, named as such in its own docstring
(the pipeline's boundary work runs on the window thread).
Disjoint contracts, disjoint reasons to change: a boundary
discipline change moves the owner only; a window-ownership
change moves the adapter only. 0 compositions here at both
states. s20 censuses the consumers; this file contributes none.

### Index texts (3 REVISE + carries)

ENDORSE all three: `completion-spanning-mutation-window`
(shared `_run_window` + adapters, two rules, `_exit_window`)
matches HEAD bytes; `per-window-mutation-thread` (owner the
async adapter with `_close_thread_connections`, thread class
deleted at `005b1f53`) matches; `streamed-operation-binding`
(factory + `_stream`, twin 0 hits, dead at the floor wheel too)
matches. The carries stand as judged: `one-sync-boundary`
stays out (0 code sites, mechanics distinct); truth consumption
12 sites in worktree (1 + 5 + 3 + 2 + 1, my census), 0 at HEAD;
CONFIRM rows unchanged.

### Defects

**D1 persists as stated (5 sites, worktree-only).** `describe`
composes `render`, whose non-scalar path runs the object's own
`__repr__` with propagation stated in docstring + body (read).
All five raise paths re-read: two `ConfigurationError`
messages at construction, three refusal reasons inside
`get_extensions`, which runs before the converting `try` on
both upstream executors (call at line 22, first `try` at 34 /
35, installed 0.324.0). HEAD's 4-case hostile oracle constructs
the feasible shape and pins the constant; the worktree single
ordinary case follows production. Routing stands: the
truth-migration owner (File `utils/truth.py` still untracked,
still blocked); containment vs propagation is the maintainer's
call. No security-path routing (diagnostic seam, shape already
in HEAD's oracle). No new defect at HEAD: every re-checked
claim held, no new unguarded member, matrix axis 6 re-run
clean.

### Gates and execution

Zero-edit file item: no production edits by either role, no
`proof:` / `gate:` owed. All claims above are static against
the three states plus installed-upstream and floor-wheel reads;
probes read-only under `/tmp`, no database, no workspace copy
owed, no sharded / Postgres cell owed (definition counts and
single-site facts touch no database, alias, or dialect
decision). No pytest ran (none authorized). Freshness re-hash:
all 17 cited blobs (target HEAD / worktree / pre-merge,
exceptions, querysets, test_schema, policies, resource, error,
both extensions, operation_state, private_state,
execution_mode, write_transaction, mutations/fields, conf, root
init, truth.py) reproduce the submission exactly. HEAD unmoved
at finish. Prose rules hold: `path::Symbol` citations, no new
links (scaffold untouched), no process provenance.

### Judgment

Zero-edit file re-trace verified: drift delta owned at HEAD
bytes (window consolidation + twin death + inert typing), 58 /
58 members homed with 25 / 25 methods, 13 / 13 rows survive
with independent counts (10 CONFIRM + 3 REVISE, no ownership
moves), 23 / 23 hunks concurrent-external, F1-out judgment with
file evidence for s20, 3 corrected index texts endorsed, D1
persists routed, no new defect, no pending execution.
`Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
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
