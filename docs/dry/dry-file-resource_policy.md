# DRY review: `django_strawberry_framework/resource_policy.py`

Status: verified
Run: 0.0.15 2026-09-18-1 (prior evidence only; run-7 re-trace appended at tail, `Run: 0.0.15 2026-09-29-7`)

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, trigger
re-checked fresh against its difference — never inherited) or a file-local
record with its proving challenge. Zero production edits; zero tracked files
changed.

## System trace

Large target (1359 lines, 65 top-level statements): the budget-object half of
the execution resource policy. It DEFINES the immutable record
(`resource_policy.py::ResourcePolicy`, 20 fields with fail-closed defaults),
the bound-domain gate (`resource_policy.py::_require_positive_int` plus
`resource_policy.py::_is_builtin_number` /
`resource_policy.py::_is_valid_deadline` /
`resource_policy.py::MAX_RESOURCE_BOUND`),
the construction-time resolution ladder
(`resource_policy.py::resolve_resource_policy`, delegating to the shared
driver), the narrowing contract (`resource_policy.py::ResourcePolicy.narrowed`
plus `resource_policy.py::effective_bound` plus the two constructor-site gates
`resource_policy.py::validate_collection_bound` /
`resource_policy.py::validate_trusted_flag`), the operation budget authority
(`resource_policy.py::_active_budget` ContextVar plus
`resource_policy.py::OperationLease` binding, `resource_policy.py::_RequestBudget` /
`resource_policy.py::_AdmissionVerdict` / `resource_policy.py::_BudgetScope`,
`resource_policy.py::begin_resource_budget` /
`resource_policy.py::end_resource_budget` and the mirror/read seams
`resource_policy.py::stash_resource_policy` /
`resource_policy.py::policy_from_info` /
`resource_policy.py::armed_resource_policy` /
`resource_policy.py::check_deadline` and helpers), the raw-list windowing
(`resource_policy.py::bounded_rows` over `resource_policy.py::_windowed_rows`
via `resource_policy.py::_raw_list_bound` and
`resource_policy.py::_bounds_by_its_own_slice`), its async twin
(`resource_policy.py::bounded_rows_async` over
`resource_policy.py::_windowed_rows_async` with
`resource_policy.py::_close_async_iterator` /
`resource_policy.py::_cleanup_rejected_async_iterable` /
`resource_policy.py::_attach_cleanup_note` /
`resource_policy.py::_is_cleanup_diagnostic`), and the wire rejection
(`resource_policy.py::ResourceLimitExceeded` plus
`resource_policy.py::RESOURCE_LIMIT_ERROR_CODE`), with the leaf manifest
(`__all__`, 19 names). It ENFORCES validation at construction on every path,
arming once per operation with a lease-scoped ContextVar, narrowing-only per
field, exact-type domain checks, and unconditional row bounding. It does NOT
spend the budget on documents or values — admission scanning, fragment and
value walks, collection-cost accounting, and the extension lifecycle live in
the sibling enforcement half
(`extensions/resource_policy.py::DjangoResourcePolicyExtension`), which this
file supplies with the budget object, the armed snapshot, the verdict record,
and the row/deadline primitives. Module and method docstrings additionally
STATE the sibling's, `schema.py::DjangoSchema`'s, `conf.py`'s,
`utils/policies.py`'s, `utils/context.py`'s, `utils/operation_lease.py`'s, and
`utils/querysets.py`'s contracts; those paragraphs are projections of behavior
owned elsewhere, verified against the owning bodies, not definitions here.

Connected code read for judgment, outside the item:
`django_strawberry_framework/extensions/resource_policy.py` (full read —
spending half: `scan_document_text`, `_ValueBudget`, `_DocumentBudget`,
`charge_document`, `DjangoResourcePolicyExtension`, `_AdmissionGuard`,
`restate_admission_verdict`);
`django_strawberry_framework/utils/policies.py` (full read — shared
`resolve_policy` driver plus `canonical_policy` / `copy_policy`);
`django_strawberry_framework/error_policy.py` (full read — symmetry sweep for
J2: record shape, gate, default, resolver, mint);
`django_strawberry_framework/exceptions.py::describe_value` (full read — the
consumed tail renderer plus its scope paragraph naming this file);
`django_strawberry_framework/utils/operation_lease.py` (full read —
`OperationLease` open/close contract);
`django_strawberry_framework/utils/context.py` (full read — mirror
read/write/clear/restore helpers);
`django_strawberry_framework/utils/errors.py::coded_error_extensions` (full
read — the consumed extensions-shape helper);
`django_strawberry_framework/conf.py::resource_policy_setting` and its
`RESOURCE_POLICY_KEY` block (full read — thin reader);
`django_strawberry_framework/schema.py` (enforcement record
`_SCHEMA_ENFORCEMENT` / `_FALLBACK_ENFORCEMENT`, `DjangoSchema.__init__`
resolve lines, `DjangoSchema.resource_policy` copy property,
`_consumer_extension_entries` / `_entry_resource_policy` declaration read);
`django_strawberry_framework/list_field.py` (deadline-free window callers:
`_normalize_list_arguments` ceiling check via `policy_from_info` plus
`effective_bound`, `_windowed_rows` / `_windowed_rows_async` call sites,
constructor-site `validate_collection_bound` / `validate_trusted_flag` calls);
`django_strawberry_framework/utils/connections.py` (page-ceiling seam via
`effective_bound` plus `policy_from_info`);
`django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`
(deadline seam line, read-only — file carries concurrent dirt, never edited);
`django_strawberry_framework/relay.py::DjangoNodeField` /
`::DjangoNodesField` (two deadline seams, bodies read);
`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`
(deadline seam before transaction, body read);
`django_strawberry_framework/types/resolvers.py` (row-bound consumers:
`bounded_rows` / `bounded_rows_async` call sites plus prefetch-cache
`normalized_row_source` normalization);
`django_strawberry_framework/utils/querysets.py::is_async_only_iterable`,
`::_AsyncQuerySetRows`, `::normalized_row_source`, `::_seal_or_defect`,
`::_defect_message`, `::sync_pipeline_recourse` (bodies read for F2/F3/F4/F5);
`django_strawberry_framework/extensions/operation_state.py::OperationState.rebind_on_resume`
(budget resume binding, body read);
`django_strawberry_framework/extensions/debug.py::DjangoDebugExtension.__init__`
(bool-gate lines for J1) and `django_strawberry_framework/utils/private_state.py`
(authority carrier cited by both halves);
`tests/test_resource_policy.py` (4013 lines — every oracle row, spot-read
bodies by name); `examples/fakeshop/test_query/test_resource_policy_api.py`
(3266 lines — live wire-shape matrix, spot-read bodies);
`tests/test_schema.py` (resolve/authority/copy/install rows, spot-read);
`tests/base/test_conf.py` (setting rows) and `tests/base/test_init.py`
(export rows) as projections.

Swept and excluded on the strength of the bodies (zero production hits for
the `ResourcePolicy` / `RESOURCE_LIMIT` / `bounded_rows` / `check_deadline` /
`effective_bound` vocabulary unless named above): `filters/`, `orders/`,
`forms/`, `rest_framework/`, `optimizer/` (except the cited walker seam),
`middleware/`, `auth/`, every other `utils/` module, `views.py`,
`routers.py`, `permissions.py`, `keyset.py`, `registry.py`, `scalars.py`,
`sets_mixins.py`, `testing/`, `management/`. Spec-047 body cited only as a
pointer (defaults pinned by oracles instead, bodies not relied upon). Prior
artifacts used only as rejected-candidate triggers, each re-checked fresh
below (`dry-file-error_policy.md` J2/J1, `dry-file-utils__querysets.md`
F2/F3/F7 families). Never read another worker's `worker-memory/`. The
`## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never touched
and are not in this finding's sites; concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor surface was swept
for the budget vocabulary (`ResourcePolicy`, `RESOURCE_LIMIT`,
`bounded_rows`, `check_deadline`, `effective_bound`): `filters/`,
`orders/`, `forms/`, `rest_framework/`, `auth/` return zero DEFINITIONS;
the only production holders are this file (budget object plus row/deadline
primitives), `extensions/resource_policy.py` (spending half),
`schema.py` (resolution plus authority), `__init__.py` (re-export),
`conf.py` (thin reader), `utils/policies.py` (driver plus precedent
pointers), `utils/context.py` plus `utils/operation_lease.py` plus
`utils/private_state.py` (consumed machinery), `exceptions.py` (scope
paragraph), `utils/errors.py` (shape helper), `extensions/debug.py`
(precedent pointer). The flavors participate by COMPOSING, never by
mirroring: `list_field.py` (window callers plus ceiling plus constructor
gates), `utils/connections.py` (page ceiling), `connection.py` plus
`relay.py` (two refetch fields) plus `mutations/resolvers.py` (write
pipeline) via `check_deadline`, `types/resolvers.py` (many-side relations)
via `bounded_rows` twins. No second budget record, second ladder, or second
code exists in any flavor. Axis discharged.

**2. Sync/async twins.** Target carries exactly four `AsyncFunctionDef`
nodes (probe: `_close_async_iterator`,
`_cleanup_rejected_async_iterable`, `_windowed_rows_async`,
`bounded_rows_async`) against 30 sync functions. Compared by BEHAVIOR, not
shape: `bounded_rows` / `bounded_rows_async` enforce the same seam — the
deadline read plus the tighter of `max_list_rows` and the field declaration
— through the one shared pure decision `resource_policy.py::_raw_list_bound`
(called by `_windowed_rows` and by `_windowed_rows_async`'s async-only
branch; probe counts two call sites), so neither color can drift onto a
different bound. The remainder is genuinely different work, kept in named
adapters the shared body calls: sync slices exact types or counts via
`islice` into a fresh list; async dispatches on
`utils/querysets.py::is_async_only_iterable`, falls back to the sync body
for sync iterables (preserving SQL `LIMIT` on querysets), and otherwise
discards `offset`, collects at most `window`, and closes the iterator early
with the `_close_async_iterator` posture (primary error preserved, ordinary
cleanup demoted to a note, control signals propagated). That is the
package's principle-5 split (one body with execution adapters for the
shared bound; two machines where await points and cleanup differ),
recorded at both owners. No async twin is owed for the record, the ladder,
the narrowing primitive, the budget arming, or the deadline helpers (pure
or construction-time). Axis discharged.

**3. Derived rather than repeated knowledge.** Each default is spelled once
in production (probe: 20 field defaults in `ResourcePolicy`, each literal
once). `DEFAULT_RESOURCE_POLICY = ResourcePolicy()` DERIVES by
construction rather than restating them. `resolve_resource_policy` passes
the default object and the field names by reference; the driver's
unknown-key check reads `fields(policy_cls)` at runtime, so the vocabulary
has one spelling. The `display_name="resource policy"` / `unit="bound"`
wording seeds live once at the call site; the driver owns producing text
from them. The derived deadline is computed once per operation in
`resource_policy.py::_absolute_deadline` and reaches both the armed budget
and the published mirror, so authority and mirror cannot disagree. The
effective bound is derived per read by `resource_policy.py::effective_bound`,
never stored. Every other spelling is a consumer, oracle, or projection,
listed never counted. No reconstructed copy found. Axis discharged.

**4. Inverse / round-trip pairs.** Five pairs in the target, each one
grammar with two halves owned here: `begin_resource_budget` /
`end_resource_budget` (arm with lease plus token / close everywhere plus
reset locally, with the adopted-binding half); `stash_resource_policy` /
`clear_resource_context` (publish mirror / remove both keys);
`record_admission_rejection` / `admission_rejection` (record verdict /
read it back in preference to the mutable published error);
`_publish_budget_mirror` / `policy_from_info` plus `armed_resource_policy`
(publish copies / read armed-first with copy-out); `_windowed_rows` /
`_windowed_rows_async` (sync window / async window behind the same caller
validation). Each pair shares the one owner named, never restated at the
consumer. The extension's `scan_document_text` / `charge_document` halves
(document tokens plus depth pre-parse / selections plus values post-parse)
are the spending twin of the budget halves here, split configuration vs
application at the import edge (see Findings). No pair is split across two
owners. Axis discharged.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); consumers composing by name (extension
imports 13 names; `schema.py` import plus resolve call plus copy property
plus declaration read; `list_field.py` 6 names; `utils/connections.py` 2
names; `connection.py` / `relay.py` / `mutations/resolvers.py` /
`types/resolvers.py` deadline plus row seams; `__init__.py` re-export);
oracles spelling literals directly and driving behavior through the public
surface (`tests/test_resource_policy.py`: per-bound rejection rows,
exact-type plus hostile-subclass rows, narrowing rows, trusted-flag rows,
budget-authority rows including `__dict__`-write and replace attempts,
deadline rows including consumer-written mirror rows, windowing rows
including subclass plus evaluated-queryset plus zero-window rows, async
cleanup rows, code plus extensions rows, resolve-ladder rows;
`test_resource_policy_api.py`: the live category matrix plus parity plus
opt-out rows; `test_schema.py`: resolve plus copy-identity plus
install-position plus fallback rows; `test_conf.py`: setting rows;
`test_init.py`: export rows) — all independent (a rename fails them, none
enumerates the owner's internals); projections (all docstrings here plus
`schema.py` authority docstrings plus `conf.py` reader docstring plus
GLOSSARY/README prose plus the spec pointer). No oracle reads the owner to
enumerate. Axis discharged.

**6. Enforcement by omission.** Three closed populations checked member by
member. (a) Validated bounds: all 20 `ResourcePolicy` fields gated
(`__post_init__` loops `fields()`: 19 via `_require_positive_int`, the
deadline via `_is_valid_deadline` or `None`); every construction path runs
the gate (direct construction by dataclass; explicit-instance override via
driver `canonical_policy` rebuild; mapping override via driver
`policy_cls(**plain)`; absent via the import-time default gated once).
(b) Deadline seams named by the `ResourcePolicy` docstring all call
`check_deadline`: `bounded_rows` both spellings (via `_raw_list_bound`),
`connection.py::DjangoConnection.resolve_connection`,
`relay.py::DjangoNodeField` plus `::DjangoNodesField`, and
`mutations/resolvers.py::run_write_pipeline_sync` before its transaction
— five call sites, five bodies read, none missing. (c) Raw-list seams:
root `DjangoListField` and generated many-side relation resolvers both
reach `bounded_rows` twins (via `_windowed_rows` family or directly) —
bodies read, none missing. (d) Trusted widening: field factories validate
via `validate_trusted_flag` at construction AND `effective_bound` admits
only `trusted is True` at enforcement, so a bypassed factory still cannot
widen by accident. Deliberate omissions with contract sources: no per-field
narrowing of the deadline except the consumer-writable mirror instant
(which narrows only); no async twin for pure decisions (axis 2); the
extension-only document/value walks (axis-4 twin). No member lacks a guard
its contract requires. Axis discharged.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **65 top-level statements** — plus, better than the minimum,
every `ResourcePolicy`-body member (23: docstring plus 20 fields plus 2
methods) and every `ResourceLimitExceeded`-body member (3). Every member
lands below; every challenge in `### Challenges` ends in a family row, a
file-local record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (budget contract: normalized-once, immutable-armed, narrowing-only, fail-closed) | (none) | projection of R1/R3/R4/R5 owners (see findings) |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `import math` | `math` | machinery for R2/R6 |
| 4 | `import time` | `time` | machinery for R5/R6 |
| 5 | `from collections.abc import Mapping` | `Mapping` | machinery for R3 |
| 6 | `from contextvars import ContextVar` | `ContextVar` | machinery for R5 |
| 7 | `from dataclasses import dataclass, fields, replace` | dataclass tools | machinery for R1/R4 |
| 8 | `from itertools import islice` | `islice` | machinery for R7 |
| 9 | `from typing import Any` | `Any` | machinery |
| 10 | `from django.db.models import QuerySet` | `QuerySet` | machinery for R7 |
| 11 | `from graphql import GraphQLError` | `GraphQLError` | machinery for R9 |
| 12 | `from .conf import resource_policy_setting` | setting reader | consumer edge to `conf.py`, R3 |
| 13 | `from .exceptions import ConfigurationError, DjangoStrawberryFrameworkError, describe_value` | guard plus base plus tail renderer | R2/R9; renderer consumed from open family `typed-rejection-value-tail`, F1 |
| 14 | `from .utils.context import clear_context_key, get_context_value, stash_on_context` | mirror helpers | consumed machinery, R5 |
| 15 | `from .utils.errors import coded_error_extensions` | extensions-shape helper | consumed machinery, R9 |
| 16 | `from .utils.operation_lease import OperationLease` | lease | consumed machinery, R5 |
| 17 | `from .utils.policies import canonical_policy, copy_policy, resolve_policy` | shared driver | R3/R5 (driver owned at `utils/policies.py`) |
| 18 | `from .utils.querysets import is_async_only_iterable, normalized_row_source` | row helpers | F2/F3 consumers (see findings) |
| 19 | `__all__ = (…19…)` | leaf manifest | R11, file-local |
| 20 | `RESOURCE_LIMIT_ERROR_CODE = "RESOURCE_LIMIT_EXCEEDED"` | wire code | R9, file-local |
| 21 | `DST_RESOURCE_POLICY = "dst_resource_policy"` | mirror key | R5, file-local |
| 22 | `DST_RESOURCE_DEADLINE = "dst_resource_deadline"` | mirror key | R5/R6, file-local |
| 23 | `class ResourceLimitExceeded` | rejection | R9 |
| 23.1 | class docstring (wire shape plus bound/limit/charged contract) | (none) | projection of R9 |
| 23.2 | `def __init__(self, bound, limit, charged, detail)` | rejection ctor | R9, file-local |
| 23.3 | `def __reduce__(self)` | pickle round-trip | R9, file-local |
| 24 | `def _is_builtin_number(value)` | exact-number predicate | R2, file-local |
| 25 | `def _is_valid_deadline(value)` | deadline domain | R2, file-local |
| 26 | `MAX_RESOURCE_BOUND = 2**63 - 1` | bound ceiling | R2, file-local |
| 27 | `def _require_positive_int(value, label)` | bound-domain rule | R2, file-local |
| 28 | `class ResourcePolicy` (`@dataclass(frozen=True)`) | budget record | R1/R2/R4 |
| 28.1 | class docstring (per-bound contracts plus deadline seam list) | (none) | field prose projection of R1; seam list projection of R6/R7 owners |
| 28.2–28.21 | 20 fields (`max_document_tokens` … `execution_deadline_seconds`) | bounds | R1, file-local |
| 28.22 | `def __post_init__(self)` | construction gate | R2, file-local |
| 28.23 | `def narrowed(self, **overrides)` | narrowing copy | R4, file-local |
| 29 | `DEFAULT_RESOURCE_POLICY = ResourcePolicy()` | package default | R3, file-local |
| 30 | `def resolve_resource_policy(explicit)` | resolution ladder | R3, file-local |
| 31 | `class _AdmissionVerdict` | verdict cell | R5, file-local |
| 32 | `class _RequestBudget` | budget triple | R5, file-local |
| 33 | `_active_budget: ContextVar[…] = ContextVar(…)` | authority carrier | R5, file-local |
| 34 | `class _BudgetScope` | lease plus token plus adoption | R5, file-local |
| 35 | `def _armed_budget()` | lease read | R5, file-local |
| 36 | `def _absolute_deadline(policy)` | derived instant | R5, file-local |
| 37 | `def _publish_budget_mirror(context, policy, deadline)` | mirror write | R5, file-local |
| 38 | `def stash_resource_policy(context, policy)` | publish-only entry | R5, file-local |
| 39 | `def _operation_policy(policy)` | canonical snapshot | R5, file-local |
| 40 | `def begin_resource_budget(context, policy)` | arm | R5, file-local |
| 41 | `def budget_resume_binding(scope)` | stream rebind triple | R5, file-local |
| 42 | `def adopt_budget_binding(scope)` | adoption mark | R5, file-local |
| 43 | `def armed_resource_policy()` | package-internal read | R5, file-local |
| 44 | `def record_admission_rejection(rejection)` | verdict write | R5, file-local |
| 45 | `def admission_rejection()` | verdict read | R5, file-local |
| 46 | `def end_resource_budget(scope)` | disarm | R5, file-local |
| 47 | `def _effective_deadline(armed, mirror)` | mirror narrowing | R6, file-local |
| 48 | `def _deadline_expired(deadline)` | clock placement | R6, file-local |
| 49 | `def clear_resource_context(context)` | mirror clear | R5, file-local |
| 50 | `def policy_from_info(info)` | request read with copy-out | R5, file-local |
| 51 | `def check_deadline(info)` | cooperative refusal | R6, file-local |
| 52 | `_SLICE_BOUNDED_ROW_TYPES = (…6…)` | slice-owned types | R7, file-local |
| 53 | `def _bounds_by_its_own_slice(result)` | exact-type predicate | R7, file-local |
| 54 | `def _raw_list_bound(info, declared, *, trusted)` | shared bound plus clock | R7, file-local |
| 55 | `def _windowed_rows(…)` | sync window | R7, file-local |
| 56 | `def bounded_rows(…)` | sync entry | R7, file-local |
| 57 | `def _attach_cleanup_note(primary_error, note)` | note attach | R8, file-local |
| 58 | `def _is_cleanup_diagnostic(error)` | control-signal split | R8, file-local |
| 59 | `async def _close_async_iterator(…)` | iterator close | R8, file-local |
| 60 | `async def _cleanup_rejected_async_iterable(…)` | rejected-source close | R8, file-local |
| 61 | `async def _windowed_rows_async(…)` | async window | R8, file-local |
| 62 | `async def bounded_rows_async(…)` | async entry | R8, file-local |
| 63 | `def validate_collection_bound(declared, *, field)` | constructor gate | R2, file-local |
| 64 | `def validate_trusted_flag(declared, *, field)` | opt-in gate | R4, file-local |
| 65 | `def effective_bound(policy_value, declared, *, trusted)` | narrowing primitive | R4, file-local |

Rules: R1 record shape plus defaults; R2 bound-domain gate; R3 package
default plus resolution ladder; R4 narrowing contract; R5 budget authority
lifecycle; R6 deadline narrowing plus expiry plus refusal; R7 sync
windowing; R8 async windowing plus cleanup; R9 wire rejection; R11 leaf
manifest. The plan's `## Responsibility index` already carries
`typed-rejection-value-tail` (open), `async-only-queryset-row-adapter`
(open), `sealed-execution-queryset` (open), `seal-defect-code-wording`
(open), `sync-boundary-recourse-wording` (rejected) — all five reused below
with triggers re-checked fresh, not renamed. No other existing family owns
a definition here (the resolve/copy/canonical sharing lives at
`utils/policies.py`, which this target only feeds and consumes). No new
family is named: R1–R11 each count 1 with no second definition site; the
two considered shared forms are rejections with contract differences plus
triggers (J1, J2).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 new bound | add a 21st bound (e.g. per-operation upload-file-name length) | **1** (declaration plus `__post_init__` arm here; driver derives the vocabulary, oracles follow) | file-local |
| C2 | R1 default | `max_list_rows` 100 → 50 | **1** (field default; `DEFAULT_RESOURCE_POLICY` derives, `list_field.py` ceiling plus `types/resolvers.py` rows follow) | file-local |
| C3 | R1 deadline default | `execution_deadline_seconds` None → 5.0 | **1** (field default; `_absolute_deadline` plus `check_deadline` follow) | file-local |
| C4 | R2 hostile value | bound of `True` / `int` subclass with raising `__lt__` / `10**5000` | **1** (this body; `describe_value` is the consumed renderer, unchanged) | file-local |
| C5 | R1+R3 vocabulary | rename a bound | **1** (the field declaration; driver's unknown-key check reads `fields()` at runtime — no second spelling to move) | file-local |
| C6 | R3 precedence | setting outranks the constructor argument | **1** at the driver (`utils/policies.py::resolve_policy` ladder; both policy resolvers follow) — **0** here | shared-driver consumer (see R3) |
| C7 | R3 display wording | rename `"resource policy"` / `"bound"` seeds | **1** (call-site kwargs here; driver produces the text; error side has its own seeds and doesn't move) | file-local |
| C8 | R4 widening | remove the `narrowed` widening refusal | **1** (method body; `effective_bound` unchanged) | file-local |
| C9 | R4 trusted truthy | `trusted="false"` widens | **0** new (`effective_bound` admits only `trusted is True`; factories validate — proves the split) | independent |
| C10 | R4 combination | `effective_bound` ignores `trusted` and always takes `min` | **1** (primitive body; `list_field.py` plus `utils/connections.py` follow) | file-local |
| C11 | R7 ceiling source | `_raw_list_bound` reads `max_page_size` instead of `max_list_rows` | **1** (helper body; both sync and async windows follow via the shared call) | file-local |
| C12 | R7 classification | add `dict` to `_SLICE_BOUNDED_ROW_TYPES` | **1** (tuple plus predicate; `normalized_row_source` rebuild still runs first) | file-local |
| C13 | R8 dispatch | drop the `not Iterable` half of the async-only test | **0** here / **1** at the owner (`utils/querysets.py::is_async_only_iterable` owns the predicate; this file's branch follows) | shared-predicate consumer (see F2) |
| C14 | R8 cleanup | propagate a cleanup `ValueError` over the primary iteration error | **1** (`_close_async_iterator` body; `_windowed_rows_async` follows) | file-local |
| C15 | R6 mirror | a later stashed instant lengthens the request | **1** (`_effective_deadline` body — the armed value stays the ceiling) | file-local |
| C16 | R6 expiry | an absent deadline rejects instead of passing | **1** (`_deadline_expired` body — `None` answers `None`, not expired) | file-local |
| C17 | R9 code | `RESOURCE_LIMIT_EXCEEDED` → another string | **1** (constant; sibling publishes it, oracles spell it literally) | file-local |
| C18 | R5 carrier | hold the authority on the request context instead of the ContextVar | **1** here (carrier plus every reader; extension resume registration follows) | file-local |
| C19 | R2 gate placement | validate in the resolve path instead of `__post_init__` | refused — one gate, not two: every driver path rebuilds through `policy_cls(…)` so the gate runs on all of them | refused |
| C20 | R1+R3 symmetry | unify `ResourcePolicy` / `ErrorPolicy` records, defaults, or resolvers | refused — J2 (shared driver already owns the ladder; remainder is distinct vocabulary) | refused |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs, of
which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-resource_policy/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 42 checks): 65-member module AST with 20-field
record plus 2 methods plus 3-member rejection (§§1–2); four async nodes
with the shared `_raw_list_bound` called twice (§§3/15); 19-name manifest
(§4); `describe_value` import plus three uses, both row helpers imported
and used, exact-type gates, lease carrier, DST keys, single code spelling,
no logger or patch lifecycle, one-way extension edge, exact-number
predicate, max bound, narrowing refusal (§§5–14); item-baseline diff empty
plus working blob equals `HEAD:` blob (§16); package population 117 (§17).
Status: `execution-verified` for every identity/count/shape/absence claim
below. Rejects the wrong results "a 66th member exists", "an async twin
owns the bound", "a second tail renderer exists", "the target drifted from
its baseline".

## Findings

No production edit is owed by a file item; the three consumed families
below are REUSED from the plan (each trigger re-checked fresh on current
evidence), two more checked and held non-members, the rest are file-local
records and two recorded rejections.

### F1 — typed rejection value tail (existing family `typed-rejection-value-tail`, status stays `open`)

- **Contract + variation.** Every typed rejection whose value came from
  outside the package renders its `got` tail through
  `exceptions.py::describe_value`, so the message cannot raise while being
  formatted. Variation: per-domain prose; the renderer fixed. This file's
  three raises are consumers (the `_require_positive_int` tail, the
  `__post_init__` deadline tail, the `validate_trusted_flag` tail), not
  definitions.
- **Sites + roles.** *Definition*:
  `exceptions.py::describe_value` (unchanged; its scope paragraph already
  names `resource_policy.py` among the in-scope rejections —
  corroborated). *Consumers verified here*: the three raises above.
  *Oracles*: the owner's hostile-tail rows (bodies cited, not
  re-litigated). *Projections*: the owner scope paragraph.
- **Challenges.** C4 → 1 at the renderer for a renderer change; **1 here**
  for a prose change (per-domain wording stays per site, which is the
  family's stated split). The tail is shared; the sentences are not.
- **Index note for Worker 0 (additive only, never an edit by this
  worker).** The plan's index row already lists `resource_policy.py` under
  Files covered — verified-correct (probe: import plus three uses; owner
  paragraph names this file). No index change owed.
- **Trigger re-checked fresh.** A second tail renderer (a site
  interpolating `{value!r}` directly for an outside-package value) would
  reopen. Swept: this file's only three tails all go through the renderer.
- **Owner + lifetime.** `exceptions.py` (unchanged). Pure derivation, never
  cached.
- **Migration / Coupling.** None.
- **Behavioral proof.** `execution-verified` for the use census (probe);
  `static-reviewed` for renderer body plus scope paragraph. Rejects "this
  file interpolates the value itself".
- **Structural gate.** The owner's hostile-tail rows (direct interpolation
  raises `ValueError` instead of `ConfigurationError`). Negative control:
  `f"{value!r}"` in `_require_positive_int` passes every small-value oracle
  and fails exactly those rows.
- **Freshness.** `django_strawberry_framework/resource_policy.py`
  `647133d23785d325856b2d1d495d18c5741dd23c`,
  `django_strawberry_framework/exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`.

### F2 — async-only queryset row adapter (existing family `async-only-queryset-row-adapter`, status stays `open`)

- **Contract + variation.** One predicate spells async-only
  (`utils/querysets.py::is_async_only_iterable`: `AsyncIterable` and not
  `Iterable`, so a queryset never classifies), one adapter carries sliced
  querysets through async completion
  (`utils/querysets.py::_AsyncQuerySetRows`, `__aiter__`-only). Variation:
  source shapes; the predicate plus the adapter fixed. This file consumes
  the PREDICATE in `resource_policy.py::_windowed_rows_async` (sync
  iterables fall back to `resource_policy.py::_windowed_rows`, preserving
  SQL `LIMIT`); it constructs no adapter.
- **Behavior/contract comparison (before calling anything here unique).**
  The predicate body was re-read: the `not Iterable` half is what keeps
  querysets on the sync path here and in `list_field.py`. Posit C13
  (drop that half): the owner moves, this branch plus the list-field
  branch follow — the predicate is the owner's contract, stated here only
  as a call. Posit a new async-only shape: the predicate moves, nothing
  here does. Distinct owners sharing an interface, not one rule twice.
- **Sites + roles.** *Definitions* (all at the owner, unchanged):
  `utils/querysets.py::is_async_only_iterable`,
  `::_AsyncQuerySetRows`, `::wrap_async_queryset_adapter`,
  `::unwrap_async_queryset_adapter`. *Consumers*: this file's async window
  plus `list_field.py`'s async-completion branch plus
  `optimizer/extension.py` (owner side). *Oracles*: the owner suite plus
  the async windowing rows (unchanged). *Projections*: the predicate
  docstring naming both consumers — corroborated.
- **Challenges.** C13 → 0 here / 1 at the owner; C11/C14 → 1 here (bound
  plus cleanup stay here). Count stays 1 per axis at exactly one owner.
- **Trigger re-checked fresh (not inherited).** The recorded trigger is a
  second async-only spelling (a local `hasattr(__aiter__)` test) or an
  adapter restated here. Measured today: still exactly one spelling
  (probe: one import, one call); zero adapter construction in the target
  (`_AsyncQuerySetRows` absent from this file). The family stays open on
  fresh evidence, with nothing owed from this file.
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation in this target.
- **Migration / Coupling.** None.
- **Behavioral proof.** `execution-verified` for the import plus use
  census (probe); `static-reviewed` for predicate body plus consumer
  branches. Rejects "this file defines async-only".
- **Structural gate.** The owner's async-only rows plus the windowing
  rows: inlining a local predicate here passes nothing new and fails the
  queryset-misclassification rows on divergence. Negative control (stated
  honestly, not run): a behavior-preserving hand copy of the predicate
  into this module passes every behavioral oracle and fails only the
  import census — so the seam's unity rests on the one-way import edge
  plus this finding, not on a behavioral gate.
- **Freshness.** Target as in F1 plus
  `django_strawberry_framework/utils/querysets.py`
  `1539b66c9ce9a659e1dc5f6bf1029b15d6868587` (predicate plus adapter
  lines).

### F3 — sealed execution queryset (existing family `sealed-execution-queryset`, status stays `open`)

- **Contract + variation.** One sealing primitive rebuilds a
  framework-owned plain queryset from validated state
  (`utils/querysets.py::_seal_or_defect`); every visibility plus row-bound
  seam runs it. Variation: seal policies plus per-surface wording; the
  rebuild fixed. This file consumes it INDIRECTLY through
  `utils/querysets.py::normalized_row_source` in
  `resource_policy.py::_windowed_rows` (a queryset subclass is rebuilt
  before classification, so a sealable subclass keeps SQL `LIMIT` and an
  unsealable one fails closed) — never by calling the seal directly.
- **Behavior/contract comparison.** The seal body plus
  `normalized_row_source` body were re-read: exact-type read, subclass
  rebuild via `_RAW_LIST_SOURCE_POLICY`, `ConfigurationError` on defect.
  Posit a new seal code: the seal plus each wording site move; this file's
  classification (`resource_policy.py::_bounds_by_its_own_slice`) does not
  — it runs AFTER the rebuild because the rebuild settles what the
  classification means. The seal is the owner's contract; the slice-vs-count
  split here is this file's contract. Distinct rules sharing a call edge.
- **Sites + roles.** *Definition*: `utils/querysets.py::_seal_or_defect`
  (unchanged). *Consumers verified here*: `normalized_row_source` import
  plus call in `_windowed_rows`. *Oracles*: the seal suite plus the
  subclass-windowing rows (unchanged). *Projections*: the
  `normalized_row_source` docstring naming the seal — corroborated.
- **Challenges.** C12 → 1 here (slice-owned set); a seal-code change → 0
  here / 1 at the owner. Count stays 1 per axis at exactly one owner.
- **Trigger re-checked fresh.** A second seal (a local subclass slice or
  a bypass around `normalized_row_source`) would reopen. Swept: this
  file's only queryset path goes through the helper (probe: one import,
  one call; `_seal_or_defect` absent from this file).
- **Owner + lifetime.** `utils/querysets.py` (unchanged). No stored
  derivation here.
- **Migration / Coupling.** None.
- **Behavioral proof.** `execution-verified` for the census (probe);
  `static-reviewed` for seal plus helper bodies. Rejects "this file seals
  or slices a subclass as itself".
- **Structural gate.** The subclass-windowing rows (slicing the subclass
  itself returns every row; bypassing the helper fails them). Negative
  control: `result[:limit]` without the normalize call passes every
  exact-queryset oracle and fails exactly those rows.
- **Freshness.** Target as in F1 plus `utils/querysets.py` as in F2.

### F4 — seal defect code wording (existing family `seal-defect-code-wording`, checked, not a member)

- **Contract difference.** The seal family renders `(code, detail)` tuples
  through `utils/querysets.py::_defect_message` with a fixed position per
  code and per-site prose. This file publishes ONE wire code
  (`resource_policy.py::RESOURCE_LIMIT_ERROR_CODE`) rendered through
  `utils/errors.py::coded_error_extensions` with per-rejection
  `bound`/`limit`/`charged` detail. A seal code names an internal invariant
  for the deployment's logs; the limit code names a client-actionable
  bound for the wire. Posit adding a seal code → the seal ladders move,
  nothing here does; posit rewording the limit code (C17) → the seal
  ladders don't move. Shared form considered (one "stable code"
  vocabulary for seal defects and limit rejections): refused — different
  readers, different variation axes, opposite disclosure directions.
- **Reconsideration trigger.** A wire vocabulary shared between seal
  defects and limit rejections (a seal code published to clients verbatim
  under the limit code, or the limit rejection gaining a seal-code enum)
  — then the wording becomes one rule.
- **Durable home.** This finding plus the seal owner
  (`utils/querysets.py::_defect_message`); no edit here to record it in.
- **Freshness.** Target as in F1 (no second site visited beyond the
  family's own record; bodies not re-litigated).

### F5 — sync boundary recourse wording (existing family `sync-boundary-recourse-wording`, checked, not a member)

- **Contract difference.** The recourse family generates per-hook remedy
  sentences naming hooks and remedies
  (`utils/querysets.py::sync_pipeline_recourse` plus decliners). This
  file's prose names no hook and offers no remedy; its rejections name the
  offending bound and stop, and its cleanup notes name the caller. Posit
  rewording a recourse sentence → nothing here moves; posit rewording a
  limit sentence → no recourse sentence moves. The family's standing
  rejection (rejected in the index) is corroborated, not inherited: only
  one clause is ever shared, and this file doesn't share even that.
- **Reconsideration trigger.** A recourse sentence quoting the budget
  contract (a sync-misuse remedy pointing at `ResourcePolicy`) — then the
  shared clause becomes the rule.
- **Durable home.** This finding plus the recourse owners
  (`utils/querysets.py::sync_pipeline_recourse` and its decliners).
- **Freshness.** Target as in F1.

### File-local records (no second definition after the matrix)

- **R1 — budget record shape plus fail-closed defaults.**
  `resource_policy.py::ResourcePolicy` (20 fields: document 5, collection
  2, value 12, deadline 1; frozen). C1, C2, C3, C5 → 1 each (declaration;
  driver derives vocabulary, `DEFAULT_RESOURCE_POLICY` derives values,
  sibling reads by attribute, oracles spell literally). The class-docstring
  seam list (which collection seam reads the deadline) is projection of
  R6/R7 owners, verified against those bodies. Trigger: a second budget
  record with the same bounds the package must keep in sync would make it
  a family (see J2 for why the error policy isn't that). Freshness:
  target plus `tests/test_resource_policy.py`
  `8d2fe4f832dee326e1dab733359dc5b12ee454ba` (default plus per-bound
  rows).
- **R2 — bound-domain gate.**
  `resource_policy.py::_require_positive_int` (exact-`int`, `>=1`,
  `<=MAX_RESOURCE_BOUND`, tail via `describe_value`, F1) plus
  `resource_policy.py::_is_builtin_number` (exact `int`/`float`) plus
  `resource_policy.py::_is_valid_deadline` (exact plus finite plus
  positive, `OverflowError` → `False`) plus
  `resource_policy.py::MAX_RESOURCE_BOUND` (64-bit ceiling with query plus
  render rationale) plus `resource_policy.py::ResourcePolicy.__post_init__`
  (one loop over `fields()`: deadline special, rest via the shared
  helper) plus `resource_policy.py::validate_collection_bound`
  (constructor-site spelling of the same rule). C4 → 1; C19 refused (one
  gate: every driver path rebuilds through `policy_cls(…)`, so direct,
  explicit-instance, mapping, and default paths all run this same body —
  verified in `utils/policies.py::canonical_policy` /
  `::resolve_policy`). The helper is already shared IN-FILE between the
  record gate and the field gate (not copied). Trigger: a second validator
  over these same bounds would make it a family. Freshness: target plus
  `exceptions.py` as in F1 plus `utils/policies.py`
  `860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`.
- **R3 — package default plus resolution ladder.**
  `resource_policy.py::DEFAULT_RESOURCE_POLICY` (single construction from
  the field defaults) plus `resource_policy.py::resolve_resource_policy`
  (explicit argument over setting over default; instance → `canonical_policy`
  duplicate; mapping over defaults; rejections at the driver). C6 → 0 here
  / 1 at the driver; C7 → 1 (the `display_name`/`unit` seeds); C5 → 1.
  The ladder BEHAVIOR is the shared `resolve_policy` driver (already
  consolidated — nothing owed here); this function is the resource-side
  declaration feeding it. The thin reader
  `conf.py::resource_policy_setting` validates nothing by its documented
  split. Trigger: a third schema-construction policy arriving with the
  same ladder would feed the same driver (the driver's own trigger, not a
  new row here). Freshness: target plus `utils/policies.py` plus
  `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25` plus `schema.py`
  `2f72732123ca1156c4eb122ce7b53de6269de95e` (resolve plus authority
  lines).
- **R4 — narrowing contract.** `resource_policy.py::ResourcePolicy.narrowed`
  (unknown-name refusal, `replace` rebuild re-validating, per-field
  widening refusal with deadline `None` handling) plus
  `resource_policy.py::effective_bound` (`None` → policy, `trusted is True`
  → declared, else `min`) plus
  `resource_policy.py::validate_trusted_flag` (exact-`bool` constructor
  gate). C8, C10 → 1 each; C9 → 0 new (the `is True` plus factory-gate
  split proves the two halves). The `trusted is True` (not truthiness) is
  load-bearing because this is the one primitive whose answer can exceed
  the policy. Trigger: a second narrowing primitive over these bounds
  would make it a family. Freshness: target plus `list_field.py`
  `f357eded3d96fcffe17e6fd84bceb8cd12af98d5` plus
  `utils/connections.py` `f549389ef0ed97bfbe4b158ab21bfc993b71b714`
  (both `effective_bound` consumers).
- **R5 — budget authority lifecycle.**
  `resource_policy.py::_active_budget` (lease-carrying ContextVar) plus
  `::_AdmissionVerdict` / `::_RequestBudget` / `::_BudgetScope` plus
  `::_armed_budget` / `::_absolute_deadline` / `::_publish_budget_mirror` /
  `::stash_resource_policy` / `::_operation_policy` /
  `::begin_resource_budget` / `::budget_resume_binding` /
  `::adopt_budget_binding` / `::armed_resource_policy` /
  `::record_admission_rejection` / `::admission_rejection` /
  `::end_resource_budget` / `::clear_resource_context` /
  `::policy_from_info`. C18 → 1 (carrier plus every reader move together;
  the extension's `rebind_on_resume` registration follows). The
  ContextVar-over-stash idiom plus the lease (not the token) as authority
  plus copy-out on every consumer-visible read (`copy_policy` at mirror
  publish, `policy_from_info`, schema property) plus off-schema authority
  (`schema.py::_SCHEMA_ENFORCEMENT`) are one boundary with one reason: a
  resolver must be able neither to replace nor to mutate the budget. The
  extension split is configuration vs application (this file owns the
  object; `extensions/resource_policy.py` spends it; the dependency runs
  one way — probe: 13 imports there, zero here — so no cycle can form).
  Trigger: a second budget authority for the same operation would make it
  a family. Freshness: target plus `utils/operation_lease.py`
  `10c164b731b381d2b62adb5e2c5ce6b694a53fd0` plus `utils/context.py`
  `cd0adcc509a3a40e5b46ba761c6cbfec2c44359c` plus `utils/policies.py` as
  in R2 plus `schema.py` as in R3 plus
  `extensions/resource_policy.py`
  `52084078ac166d8116b9e4bb2522e8ce193251ea` (spending half) plus
  `extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9` (resume binding).
- **R6 — deadline narrowing plus expiry plus refusal.**
  `resource_policy.py::_effective_deadline` (non-builtin mirror ignored;
  `None` armed answers mirror; else the tighter) plus
  `resource_policy.py::_deadline_expired` (exact-builtin only against the
  clock; non-finite expired; subclass numeric expired; absent/cleared/bool
  /non-numeric not-a-deadline) plus `resource_policy.py::check_deadline`
  (armed ceiling else mirror alone; reports the CONFIGURED budget with
  `ceil` plus one, never the monotonic instant). C15, C16 → 1 each. The
  five deadline call sites (R5 plus matrix axis 6) compose this by name.
  Trigger: a second clock-placement rule would make it a family.
  Freshness: target plus `connection.py`
  `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` (working, carries concurrent
  cursor-guard dirt — read-only, never edited) plus `relay.py`
  `c3c5aea52768cbdb3a849c5944cb4b2245db5fde` plus
  `mutations/resolvers.py` `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`
  plus `types/resolvers.py` `f3341e6a9f52659925762bce097033bac67e3b51`.
- **R7 — sync windowing.** `resource_policy.py::_SLICE_BOUNDED_ROW_TYPES`
  (6 exact types) plus `::_bounds_by_its_own_slice` (`type()` membership,
  never `isinstance`) plus `::_raw_list_bound` (deadline plus
  `effective_bound` over `max_list_rows`, shared by both colors) plus
  `::_windowed_rows` (None passthrough, `normalized_row_source` rebuild
  BEFORE classification, slice-owned vs `islice`-counted halves,
  offset/limit window with zero-width arm) plus `::bounded_rows`
  (coordinate-free entry). C11, C12 → 1 each. The coordinate validation
  stays at `list_field.py::_normalize_list_arguments` by stated contract
  (this seam cannot check the caller's claim). Trigger: a second
  slice-vs-count classifier would make it a family. Freshness: target plus
  `utils/querysets.py` as in F2/F3 plus `list_field.py` as in R4.
- **R8 — async windowing plus cleanup.**
  `resource_policy.py::_windowed_rows_async` (async-only dispatch with sync
  fallback, rejected-source cleanup, early close, offset discard plus
  window collect) plus `::bounded_rows_async` (entry) plus
  `::_close_async_iterator` (primary-preserved close) plus
  `::_cleanup_rejected_async_iterable` (acquire-plus-close with caller-named
  notes) plus `::_attach_cleanup_note` (`__notes__`-list write for 3.10
  range) plus `::_is_cleanup_diagnostic` (`Exception`-only demotion).
  C14 → 1. The `caller="bounded_rows_async"` naming is what tells parallel
  seams apart in notes. Trigger: a second async-iterator cleanup posture
  would make it a family. Freshness: target plus `utils/querysets.py` as
  in F2 plus `list_field.py` as in R4 (async caller).
- **R9 — wire rejection.** `resource_policy.py::RESOURCE_LIMIT_ERROR_CODE`
  (single code with sync/async/subscription rendering rationale) plus
  `resource_policy.py::ResourceLimitExceeded` (multiple-inherits
  `GraphQLError` plus package base; `bound`/`limit`/`charged`/`detail`
  with `coded_error_extensions`; `__reduce__` for pickle). C17 → 1 (the
  constant; the sibling publishes it, the extension renders it, oracles
  spell it). The pre-parse scan raising vs the admission publishing is the
  stated boundary, not a second code. Trigger: a second limit code would
  make it a family. Freshness: target plus `utils/errors.py`
  `3e25e93bf2265209f79b03d4b17670814f25d676` (shape helper).
- **R11 — leaf manifest.** `__all__` (19 names; every public helper
  exported, nothing else). Imported by name at the root and by `schema.py`
  plus `list_field.py` plus `utils/connections.py` plus
  `types/resolvers.py` plus the sibling. A 20th public helper would extend
  this tuple in one place. Trigger: a second manifest over these names
  would make it a family. Freshness: target plus
  `django_strawberry_framework/__init__.py` (re-export lines).

### J1 — shared security-bool helper (refused shared form, recorded here)

Three bool gates share the `must be a bool; got {tail}` token shape:
`resource_policy.py::validate_trusted_flag` (exact `type(x) is not bool`,
no default, guards a widening opt-in),
`error_policy.py::ErrorPolicy.__post_init__`'s `enabled` arm (`not
isinstance`, default `True`, guards a masking switch),
`extensions/debug.py::DjangoDebugExtension.__init__`'s acknowledgement
(`not isinstance`, default `False`, guards a disclosure). Posit rewording
one message → exactly one moves; posit flipping one default → exactly one
moves (two defaults point opposite ways, the third has none, so no shared
default exists to own); posit tightening one check to exact-type → the
other two don't move (this side already proves the stricter spelling is a
per-site decision, and `effective_bound` independently admits only `True`
so a bypassed factory still cannot widen). The per-site prose names the
deployment danger each refusal prevents (silent widening vs silent opt-out
vs armed disclosure) — unifying the helper would couple three unrelated
dangers to one sentence. Reconsideration trigger: a fourth security-bool
gate arriving with identical rationale AND no per-site danger prose — then
the mechanism (not the messages) becomes the shared rule with this finding
as its seed. Durable home: this finding plus each owner's own rationale
paragraph (all three already state their danger; no edit owed). No new
index row today.

### J2 — error/resource policy unification (refused shared form, re-derived from THIS side)

Both policies carry a `DEFAULT_*`, a frozen dataclass, an extension, and a
`resolve_*` — the symmetry the task named to sweep, not assume. Pair by
pair from THIS side: the ladders already share one driver
(`utils/policies.py::resolve_policy` — C6 proves it: one precedence change
moves the driver, both resolvers follow); copies share
`utils/policies.py::copy_policy` (mirror publish, `policy_from_info`,
schema properties on both sides); canonicalization shares
`utils/policies.py::canonical_policy` (`_operation_policy` here);
tails share `exceptions.py::describe_value` (F1 plus the error side's two
tails). What remains per policy is distinct vocabulary, not shared
mechanism: ~20 numeric bounds with a deadline plus narrowing plus windowing
plus budget authority here vs three string/bool options with a neutral
message there; `display_name`/`unit` seeds differing per side
(`"resource policy"`/`"bound"` vs `"error policy"`/`"option"` — C7 proves
the split); install positions inverse by lifecycle (budget appends to set
up last with a trailing guard, masking prepends to tear down last — each
docstring records the other's direction); `narrowed` plus `effective_bound`
plus windowing plus deadline existing only on this side (an error policy
has no maximums to tighten, so the omission is deliberate, not a gap —
the error item's axis-6 omission (a) re-checked and corroborated). Posit
C20 (one base record): the driver would own the mechanism but pin neither
vocabulary, and a change to either side's fields (C1 vs a new error
option) moves exactly one body today. Reconsideration trigger: a third
schema-construction policy arriving with the identical
declare→canonicalize→resolve→copy shape — then the SHAPE (not the fields)
becomes a family with the driver as its owner. Durable home: this finding
plus the driver's module docstring (already states the two-resolver
contract) plus each resolver's "structural twin" paragraph. No new index
row today.

## Defects

None. Every claim checked while tracing held: all 20 defaults match their
documented values with single production spellings (probe); the
import-direction edge runs one way (sibling imports 13 names from here,
never the reverse); every construction path runs the one gate (driver
bodies read); the copy/off-schema/lease boundary prose matches `schema.py`
bodies (`copy_policy` per read, `_SCHEMA_ENFORCEMENT` holding the
authority, `_FALLBACK_ENFORCEMENT` carrying this default) and the lease
bodies (close everywhere, reset locally, adopted half); the armed-first
plus exact-type plus fail-closed prose matches `policy_from_info`;
the five deadline seams all call `check_deadline` (bodies read); both
row-bound colors share `_raw_list_bound`; the subclass rebuild runs before
classification; the async cleanup preserves the primary and propagates
control signals; the trusted primitive admits only `True`; oracles pin
each behavior they describe. Nothing routed to any owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
117-file sweeps, command in `### Challenges`) already ran green against the
shared tree; they mutate no source, open no database, and import no Django,
so no workspace copy was owed and no `__file__`/DB `NAME` record applies.
No pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED` or
Postgres cell is owed for the probe (`inapplicable by construction` — the
probe opens no database and resolves no alias or dialect; the windowing
plus deadline paths that DO reach the database are cited as oracles,
`static-reviewed` here, with their live rows owning the database cells at
the gate).

## Judgment

Backstop discharged: 65/65 `ast.Module.body` members enumerated plus all 23
`ResourcePolicy`-body members plus all 3 `ResourceLimitExceeded`-body
members, 20 challenges run, every rule terminating in one of the three
consumed families it touches (each trigger re-checked fresh —
`typed-rejection-value-tail` as the consumed renderer,
`async-only-queryset-row-adapter` as the consumed predicate,
`sealed-execution-queryset` as the consumed rebuild; `seal-defect-code-wording`
plus `sync-boundary-recourse-wording` both checked and held non-members),
a file-local record with its proving challenge (R1–R9/R11), or a recorded
rejection with difference plus trigger plus owner home (J1, J2) — no
consolidation owed, no defect found, no new family named. The
error/resource symmetry is already consolidated at the shared driver plus
the shared copy plus the shared tail; what remains per side is distinct
vocabulary with opposite lifecycle positions, and the budget/spend split
across the extension edge is configuration vs application, not duplication.
Zero-edit result is legitimate.

No new `## Responsibility index` rows proposed for Worker 0: every family
this target touches is already indexed (F1 carries no index change; F2/F3
already list this file); the two refused shared forms live at their owner
paragraphs plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
82f50470f59dc3eb283684c43f5de37d77a9d31f --
django_strawberry_framework/resource_policy.py` is empty (0 bytes,
re-measured after the probe run via probe §16); the working blob
`647133d23785d325856b2d1d495d18c5741dd23c` equals the item baseline, the
cycle-baseline member, and `HEAD:` — the target is clean, so no hunk
attribution was owed. Before touching any path, the item-scoped paths were
verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`
hunk `3c4d5dcb…` vs `HEAD` `93e998f2…`, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py` +31 `a466270b`,
`docs/bug_hunt/bug_hunt-0_0_15.md` `MM`, `docs/dry/dry-0_0_15.md` `M`) was
never edited, reverted, or tidied, and no other dirty path was written
(sibling `dry-file-*.md` untracked artifacts and the
`dry-file-utils__querysets.md` modification are other items' work, left
alone). Dirt elsewhere left alone, not a stop. No commit. Untracked scratch
created (not tracked changes): this artifact
`docs/dry/dry-file-resource_policy.md` and the read-only probe
`docs/dry/temp-tests/dry-file-resource_policy/probe_w1.py` (`W1 PROBE: ALL
OK`, 42 checks; no source mutation, no Django import, no DB, no
shared-tree pytest). No ruff run owed (no tracked `.py` edits; artifact is
`.md` only; probe is untracked scratch). No `__file__`/DB record (no
workspace copy — no mutating proof exists).

## Independent verification (Worker 2)

Own trace recorded BEFORE reading `## Findings` above (expectation-first;
the artifact past this point was read only afterwards for reconciliation).
Instrument: fresh `ast.parse` + text census of my own
(`docs/dry/temp-tests/dry-file-resource_policy-w2/probe_w2.py`,
`W2 PROBE: ALL OK`, 25 checks, read-only, no Django import, no DB, no
pytest). Every expectation below was fixed before opening W1's findings;
agreements and the one arithmetic note follow the trace.

### Own re-derivation (rules, counts, owners I would choose)

- **Record + defaults.** One frozen dataclass
  `resource_policy.py::ResourcePolicy` with 20 annotated bounds (document 5,
  collection 2, value 12, deadline 1) plus `DEFAULT_RESOURCE_POLICY`
  derived by construction. Posited: 21st bound; default flip 100 → 50;
  rename one bound (driver reads `fields(policy_cls)` at runtime, confirmed
  in `utils/policies.py`). Count 1 each. Owner: this file. (W1 R1 — agree.)
- **Domain gate.** `resource_policy.py::_require_positive_int` (exact-`int`,
  `>= 1`, `<= MAX_RESOURCE_BOUND`) + `resource_policy.py::__post_init__`
  loop over `fields()` + `resource_policy.py::validate_collection_bound`
  as the constructor-site spelling of the same rule, sharing the helper
  in-file. Posited: `True` / hostile-`int`-subclass / `10**5000` bound.
  Count 1. Owner: this file. (W1 R2 — agree.)
- **Resolve ladder vs `utils/policies.py` driver.** Precedence change
  posited → 0 here / 1 at `utils/policies.py::resolve_policy`; seed-wording
  change → 1 here. The ladder behavior is already consolidated at the
  driver; this file feeds it a declaration. Owner: driver for the ladder,
  this file for the declaration. (W1 R3 — agree.)
- **Narrowing / factory.** `resource_policy.py::narrowed` (widening
  refusal), `resource_policy.py::effective_bound` (`trusted is True`
  only), `resource_policy.py::validate_trusted_flag` (exact-`bool`).
  Posited: drop the refusal; `trusted="false"` (0 new — proves the
  `is True` + factory-gate split); ignore `trusted` (1). Owner: this
  file. (W1 R4 — agree.)
- **Authority ContextVar / lease.** `resource_policy.py::_active_budget`
  lease-carrying ContextVar + scope / verdict / budget cells + arm / mirror
  / read seams. Posited: move authority to the request context → 1 here
  (carrier plus every reader; extension resume registration follows).
  Owner: this file. (W1 R5 — agree.)
- **Deadline trio.** `resource_policy.py::_effective_deadline` (armed
  ceiling over consumer mirror), `resource_policy.py::_deadline_expired`
  (exact-builtin only; absent/non-numeric → not-a-deadline),
  `resource_policy.py::check_deadline`. Seams re-counted myself: 5 call
  sites — `_raw_list_bound` (covers both raw-list spellings),
  `connection.py::DjangoConnection.resolve_connection` (1),
  `relay.py::DjangoNodeField` / `::DjangoNodesField` (2),
  `mutations/resolvers.py::run_write_pipeline_sync` (1). All bodies
  confirmed via search. Owner: this file. (W1 R6 — agree.)
- **Sync window.** `resource_policy.py::_windowed_rows` over
  `resource_policy.py::_raw_list_bound` +
  `resource_policy.py::_bounds_by_its_own_slice` (6 exact types,
  `type()`-membership). Posited: ceiling-source swap (1, both colors
  follow via the shared call); `dict` into the slice set (1). Owner: this
  file. (W1 R7 — agree.)
- **Async window + cleanup.** `resource_policy.py::_windowed_rows_async`
  (async-only dispatch, sync fallback preserving SQL `LIMIT`, early close,
  rejected-source cleanup) + `resource_policy.py::_close_async_iterator`
  (primary-preserved) + `resource_policy.py::_is_cleanup_diagnostic`
  (`Exception`-only demotion). The async-only predicate itself is NOT
  defined here (absent from the file; consumed once). Owner: this file
  for window + cleanup, `utils/querysets.py` for the predicate. (W1
  R8 + F2 — agree.)
- **Rejection code + extensions.** Single
  `resource_policy.py::RESOURCE_LIMIT_ERROR_CODE` spelling +
  `resource_policy.py::ResourceLimitExceeded` (`bound`/`limit`/`charged`
  via `utils/errors.py::coded_error_extensions`, `__reduce__` for pickle).
  Posited: code reword → 1. Owner: this file. (W1 R9 — agree.)
- **Manifest.** `__all__`, 19 names, counted myself. Owner: this file.
  (W1 R11 — agree.)
- **Consumer roles for tail / adapter / seal families.** The three raises
  consume `exceptions.py::describe_value` (import + exactly 3 uses, no
  local tail definition); the async window consumes
  `utils/querysets.py::is_async_only_iterable` (one call, no local
  spelling, no adapter construction); the sync window consumes
  `utils/querysets.py::normalized_row_source` (one call, no local seal).
  All three stay owned where W1 says
  (`typed-rejection-value-tail`, `async-only-queryset-row-adapter`,
  `sealed-execution-queryset`, all `open`). (Agree.)
- **error_policy mirror question from this side.** Both resolvers delegate
  to `utils/policies.py::resolve_policy` with per-side
  `display_name`/`unit` seeds (`"resource policy"`/`"bound"` vs
  `"error policy"`/`"option"`, confirmed in both bodies); copies share
  `copy_policy`; canonicalization shares `canonical_policy`; tails share
  `describe_value`. Remainder is distinct vocabulary with inverse install
  positions. Refuse unification. (W1 J2 — agree.)

### Enumeration check (member-by-member, own count)

My count: 65 `ast.Module.body` members (verified item-by-item against the
dump: docstring + 17 imports + `__all__` + code/keys + 2 classes + 42
functions, of which 4 async) — matches W1's 65. `ResourcePolicy` body:
23 = 1 docstring + 20 `AnnAssign` fields + 2 methods
(`__post_init__`, `narrowed`). `ResourceLimitExceeded` body: 3 =
1 docstring + `__init__` + `__reduce__`. Every row of W1's table (§§1–65,
28.1–28.23, 23.1–23.3) matches a member I counted; no member is
unassigned.

**Arithmetic note (the 20+2=22 vs 23 question): W1 is correct.** 20 fields
+ 2 methods = 22 *code* members; + 1 class docstring = 23 body members.
W1's `### Enumeration` header states exactly this ("23: docstring plus 20
fields plus 2 methods"); the job brief's "20+2=22" shorthand drops the
docstring the header counts. My probe guards the decomposition
(`w2-rp-arithmetic`: 20+2+1=23, ALL OK). No correction owed.

### Counts + roles; oracles

- All C1–C20 definition counts re-derived above: agree on every row,
  including C6 (0 here / 1 driver), C9 (0 new), C13 (0 here / 1 owner),
  C19 (refused — one gate; driver bodies confirm every path rebuilds
  through `policy_cls(…)`), C20 (refused — J2).
- Roles: consumers (`extensions/resource_policy.py` 13-name import,
  verified by AST; `list_field.py` 6 names, verified; `schema.py`,
  `utils/connections.py`, `types/resolvers.py`, `connection.py`,
  `relay.py`, `mutations/resolvers.py` seams, all confirmed by search),
  oracles (`tests/test_resource_policy.py` 4013 lines, live
  `test_resource_policy_api.py`, `test_schema.py`, `test_conf.py`,
  `test_init.py`), projections (module/class docstrings, GLOSSARY/README,
  spec pointer). All agree.
- **No oracle rewritten:** `tests/test_resource_policy.py` contains zero
  occurrences of `fields(ResourcePolicy)`, `fields(ErrorPolicy)`,
  `resource_policy.__all__`, or `RESOURCE_POLICY_KEY` — oracles spell
  literals and drive the public surface; a rename fails them. Agree.

### Equivalence (principle 8) + zero-edit validation

Zero production edits ⇒ no observable behavior exists to compare; the
equivalence obligation is the diff itself. Confirmed myself:
`git diff 82f50470f59dc3eb283684c43f5de37d77a9d31f --
django_strawberry_framework/resource_policy.py` is 0 bytes, and the
working blob `647133d23785d325856b2d1d495d18c5741dd23c` equals both the
item baseline and `HEAD:` (probe `w2-item-diff-empty`,
`w2-blob-647133d2`). Coverage + assignment validated (enumeration above:
65/65 + 23 + 3, every member in a family row, file-local row, or
rejection). No consolidation candidate found on my own sweep
(`class ResourcePolicy` defined exactly once package-wide; 10 files
naming it are the consumer/driver/projection set W1 names plus the
`extensions/__init__.py` re-export and the `private_state.py` citation —
neither a definition). A file item owes no production edit; none is
demanded. No new family named; nothing to route.

### Rejections, fingerprints, gates, Pending, coupling

- **J1** (shared security-bool helper refused): difference re-checked —
  exact-`type(x) is not bool` with no default guarding a widening opt-in
  here vs `not isinstance` with defaults `True` (masking switch) and
  `False` (disclosure) on the other sides; opposite defaults ⇒ no shared
  default to own. Trigger (fourth gate with identical rationale and no
  per-site danger prose) is concrete. Agree.
- **J2** (policy unification refused): difference re-checked from this
  side (see mirror question above); trigger (third policy with the
  identical declare→canonicalize→resolve→copy shape) is concrete. Agree.
- **F4** (seal-defect wording, non-member): seal codes name internal
  invariants for logs; the limit code names a client-actionable bound for
  the wire; C17 moves only here. Trigger (shared wire vocabulary) is
  concrete. Agree.
- **F5** (recourse wording, non-member): recourse sentences name hooks +
  remedies; limit sentences name the bound and stop. Trigger (a remedy
  quoting the budget contract) is concrete. Agree.
- **Fingerprints re-hashed by me** (working tree, this run): target
  `647133d2…` ✓, `exceptions.py` `e06b0b7…` ✓, `utils/querysets.py`
  `1539b66c…` ✓, `utils/policies.py` `860b181f…` ✓, `conf.py`
  `c6ad46aa…` ✓, `schema.py` `2f727321…` ✓, `list_field.py`
  `f357eded…` ✓, `utils/connections.py` `f549389e…` ✓, `relay.py`
  `c3c5aea5…` ✓, `mutations/resolvers.py` `3fd1e571…` ✓,
  `types/resolvers.py` `f3341e6a…` ✓, `utils/operation_lease.py`
  `10c164b7…` ✓, `utils/context.py` `cd0adcc5…` ✓,
  `extensions/resource_policy.py` `52084078…` ✓,
  `extensions/operation_state.py` `b2674a22…` ✓, `utils/errors.py`
  `3e25e93b…` ✓, `tests/test_resource_policy.py` `8d2fe4f8…` ✓ — all
  18 match W1's record. `connection.py` `3c4d5dcb…` is the known
  concurrent cursor-guard dirt (working-only, read-only here, never
  edited). Nothing stale, nothing reopened.
- **Gates + negative controls** (`static-reviewed`; no pytest is
  authorized to a verifier outside a workspace copy, and this zero-edit
  item has no mutating proof to run): F1 hostile-tail rows, F3
  subclass-windowing rows (`test_a_windowed_queryset_subclass_is_windowed_on_the_rebuilt_queryset`,
  plus zero-width variants), R4 trusted rows
  (`test_only_the_literal_true_widens…`, `test_a_falsy_non_bool_opt_in…`),
  R6 deadline rows (armed-ceiling + mirror-narrowing + subclass
  fail-closed), R8 async-cleanup rows (primary-preserved, cancellation
  precedence), R3 resolve rows — every cited oracle row was confirmed to
  exist by name in `tests/test_resource_policy.py`, and each stated
  negative control (direct `{value!r}` interpolation; `result[:limit]`
  without the normalize call; truthiness for `trusted`; a lengthened
  mirror instant; a propagated cleanup `ValueError`) would fail exactly
  those rows by construction. F2's control is disclosed honestly as
  import-edge rather than behavioral (a hand-copied predicate passes
  every behavioral oracle and fails only the one-import census) — that
  disclosure is correct and sufficient for a reused, already-open family
  with no consolidation. `prove_failability.py` needs no run: no new gate
  is introduced (all gates are pre-existing oracle rows).
- **`## Pending execution` absent — correct:** the only executed proofs
  are the read-only AST/text probes (no source mutation, no Django, no
  DB ⇒ no workspace copy owed, no `__file__`/DB record applies);
  `inapplicable by construction` is properly claimed for sharded/Postgres
  cells on the probe, with the database-reaching paths cited as
  `static-reviewed` oracles whose live rows the gate owns. No
  `execution-deferred` items. Agree.
- **Coupling:** none claimed, none owed (zero edits, no shared form
  adopted). Agree.

### AGENTS.md prose check

Item-scoped diff is empty ⇒ no production/test prose to check. Artifact:
102 `path::Symbol` citations, zero raw `path:NN` cites, zero markdown
cross-file links (empty link-definition scaffolding is correct — nothing
to link), no process provenance (the single "worker-memory" mention is
the required non-reading attestation, not provenance), tests cited at
their mandated tiers with no new tests added. The `docs/dry/dry-0_0_15.md`
`M` dirt and the sibling untracked `dry-file-*.md` artifacts are other
items' work, left alone. Pass.

## Defects (Worker 2)

None. Every body I re-read matched its prose: defaults single-spelled,
one-way extension edge (13 names in, zero back), one gate on all
construction paths, copy-out on every consumer-visible read, 5/5 deadline
seams calling `check_deadline`, both colors sharing `_raw_list_bound`,
subclass rebuild before classification, primary-preserved async cleanup,
`trusted is True` load-bearing. No defect to route to any owner.

## Judgment (Worker 2)

`Status: verified`, no pending execution. Zero-edit file item: matrix
discharged against the real surface, 65/65 + 23 + 3 enumerated with the
20+2+1=23 arithmetic holding, all counts and roles reconciled, all 18
fingerprints re-hashed matching, all four rejections carrying difference
+ trigger, gates confirmed against existing oracle rows with the one
honest import-edge disclosure, prose rules clean. The error/resource
symmetry is consolidated at the driver + copy + tail; the budget/spend
split is configuration vs application. For Worker 0: tick
`File resource_policy.py` as verified (Run 0.0.15 2026-09-18-1); no
`## Responsibility index` rows (every touched family already indexed —
F1 needs no change, F2/F3 already list this file; J1/J2 live at their
owner paragraphs + this finding); no `## Owned changes` rows (zero
tracked edits). Scratch left on disk for Worker 0 to remove by explicit
path: `docs/dry/temp-tests/dry-file-resource_policy-w2/` (mine) alongside
W1's `docs/dry/temp-tests/dry-file-resource_policy/`. No commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review at bfaee91d (Worker 2, Q6)

Phase-1 trace only. Fresh derivation from current (`bfaee91d`) HEAD bytes; the
artifact's other sections were not opened. Zero edits made, no `Status:` set,
no verdict on prior findings proposed. Dependency direction throughout is
established from HEAD import lists and call sites, not from prose.

### 1. Resource-policy's uses of the three files' machinery

(a) `django_strawberry_framework/list_field.py`. Direction is
list_field-into-resource_policy, never the reverse.
`django_strawberry_framework/resource_policy.py` imports zero symbols from
`list_field.py` (HEAD import list: `__future__`, `math`, `time`,
`collections.abc`, `contextvars`, `dataclasses`, `itertools`, `typing`,
`django.db.models`, `graphql`, `.conf`, `.exceptions`, `.utils.context`,
`.utils.errors`, `.utils.operation_lease`, `.utils.policies`,
`.utils.querysets` only). Its four `list_field` mentions are prose: the
accepted-`offset` ceiling comment, the `_windowed_rows` coordinate-ownership
docstring naming `list_field.py::_normalize_list_arguments` as the single
owner of coordinate validation, and the `bounded_rows` docstrings naming
`DjangoListField`. It neither calls nor duplicates any offset-guard or
determinism-classifier symbol (no read of `_selected_ordering`,
`_has_deterministic_ordering`, `_is_model_default_ordering_active`,
`_is_deterministic_order_term`, or any `_APPROVED_ORDER_*` /
`_TRANSPARENT_ORDER_EXPRESSIONS` table). Conversely `list_field.py` consumes
resource-policy by name: `resource_policy.py::policy_from_info` (read the
request policy for `offset_ceiling` / `effective_ceiling`),
`resource_policy.py::effective_bound` (limit ceiling),
`resource_policy.py::_windowed_rows` / `resource_policy.py::_windowed_rows_async`
(bounding/windowing behind validated coordinates),
`resource_policy.py::_cleanup_rejected_async_iterable` (async rejection
cleanup), `resource_policy.py::validate_collection_bound` /
`resource_policy.py::validate_trusted_flag` (construction-time checks). Each
is a consumer call into the owner, not a second definition.

(b) `django_strawberry_framework/utils/querysets.py` (READ-ONLY; never edited).
`resource_policy.py` calls exactly two of its symbols, both by name:
`utils/querysets.py::normalized_row_source` (called once, in
`resource_policy.py::_windowed_rows`, before shape classification, because the
classification is what the rebuild settles) and
`utils/querysets.py::is_async_only_iterable` (called once, in
`resource_policy.py::_windowed_rows_async`, to dispatch async-only sources to
the collecting path while sync iterables including `QuerySet` fall back to
`_windowed_rows`). Contracts composed, not duplicated: the rebuild returns an
exact `models.QuerySet` unchanged, rebuilds a `QuerySet` subclass through the
seal or raises `ConfigurationError`, and passes every other shape through for
the counting path; the predicate answers `AsyncIterable` and not `Iterable` so
a `QuerySet` (both) never classifies async-only. Resource-policy holds no seal
policy of its own, no `_seal_or_defect` copy, no seal-wording arm.

(c) `django_strawberry_framework/schema.py`. `resource_policy.py` imports zero
symbols from it; mentions are prose only (`schema.py::DjangoSchema`,
`schema.py::_SCHEMA_ENFORCEMENT`, `resolve_resource_policy` at construction).
The runtime link runs through `info`: `schema.py::DjangoSchema` calls
`resource_policy.py::resolve_resource_policy` once at construction and arms
the per-operation budget the seams read via `policy_from_info` /
`_armed_budget`. The delta's three new methods (`schema.py::DjangoSchema.execute_sync`,
`schema.py::DjangoSchema.execute`, `schema.py::DjangoSchema._masked_return`)
read `_enforcement(self).error_policy` and the `extensions/error_policy.py`
gates/implementation (`masking_is_active`, `is_maskable_result`,
`mask_execution_result`, `degraded_result`) only; they read no resource-policy
symbol, recompute no bound, and touch no row path.

### 2. Row-bound contract (current source)

Ownership taken: exact `models.QuerySet` is sliced so the bound rides into SQL
as `LIMIT`; a `QuerySet` subclass is rebuilt by `normalized_row_source` under
`_RAW_LIST_SOURCE_POLICY` (`require_model_rows=False`,
`reject_sliced=False`, `carry_result_cache=True`) into a plain
framework-owned queryset and sliced there, carrying fetched rows forward, so a
sealable subclass keeps its SQL `LIMIT` and an evaluated one is windowed from
held rows at no second query; exact `list`/`tuple`/`str`/`bytes`/`bytearray`
(`resource_policy.py::_SLICE_BOUNDED_ROW_TYPES`, tested by exact
`type(result)` in `resource_policy.py::_bounds_by_its_own_slice`, never
`isinstance`) are sliced in Python; every other shape (a subclass of those, a
mapping, a bare iterable, a relation proxy, an async-only iterable) is bounded
by COUNTING (`islice` into a package-built list; async sources collected into
an own list with early close), which cannot return more items than asked for
whatever the source does; `None` passes through; a zero-width window answers
the empty slice / `[]` rather than a consumer subscript. Refusals (fail
closed, typed `ConfigurationError`): a subclass whose state cannot be
faithfully rebuilt, and a queryset whose instance state is unreadable.
Coordinate discipline: `offset`/`requested_limit` are accepted-coordinate and
returned-row ceilings, not physical-scan guarantees; `_windowed_rows` is
package-private and validates nothing, with `list_field.py::_normalize_list_arguments`
as the single validating owner (exact-`int`, non-negative, over-ceiling with
typed argument-named errors). Wire-controlled sizes stay untrusted per the
GOAL.md trust boundary; configuration is validated at construction, then
trusted.

### 3. Definition counts

- Budget/rule: 1 authoritative definition.
`resource_policy.py::ResourcePolicy.max_list_rows` declares the ceiling and
`resource_policy.py::effective_bound` is the one narrowing primitive
(`None` governs by policy; only literal `True` widens); `_raw_list_bound`
(deadline check plus the tighter bound, spelled once for both colors) and
`_windowed_rows` enforce by name. `list_field.py` computes `offset_ceiling`
as a plain attribute read and `effective_ceiling` via `effective_bound`; both
are consumers. No second budget, ceiling, or `min()` spelling exists in any of
the three delta files. The deltas add zero budget definitions.
- Row-source shape: 1 + 1, split by responsibility, neither duplicated. The
slice-vs-count decision is owned once by
`resource_policy.py::_SLICE_BOUNDED_ROW_TYPES` +
`resource_policy.py::_bounds_by_its_own_slice`; the subclass rebuild is owned
once by `utils/querysets.py::normalized_row_source` under
`_RAW_LIST_SOURCE_POLICY`. `list_field.py` holds zero row-source definitions
(no `islice`, no type-tuple, no rebuild, no `__getitem__` reasoning). The
deltas add zero row-source shapes.

### 4. Owners I would choose (DRY.md principle 7)

Collection budget: `resource_policy.py::ResourcePolicy` (declaration) +
`resource_policy.py::effective_bound` (narrowing primitive); wire-coordinate
validation stays at `list_field.py::_normalize_list_arguments` (distinct
responsibility with its own typed-error contract; already depends on the
budget owner, so no reversed dependency). Row-source ownership split as in
the counts above (transport/bound decision at the bound module, queryset
rebuild at the queryset module every visibility boundary already seals
through). Determinism classifier (offset guard, approved-form tables,
`opts`/`seen`/`prefix` recursion): `list_field.py`, which alone consumes the
sealed queryset's ordering. Seal policies and seal wording:
`utils/querysets.py`. Schema enforcement record and the new return-masking
seam: `schema.py::DjangoSchema` with the masking implementation owned by
`extensions/error_policy.py`.

### 5. Whether any delta breaks anything derived

No delta breaks anything derived here; no defect is recorded, so no contract
row plus reaching input is owed. Per delta:

(a) `list_field.py` offset-guard rework (490 insertions, 48 deletions, six
hunks: imports, five guard tables with `_READABLE_ORDER_LEAVES` now a
`frozenset`, `_ORDER_VALUE_CONTAINERS` unchanged below them, and the four
classifier signatures each gaining `(opts=None, seen=frozenset(),
prefix="")` plus five new helpers). Resource-policy reads none of these
symbols, so there is nothing to drift against. The rework can only move which
positive offsets the guard authorizes under exotic orderings (its own owned
contract); whatever passes is still bounded by `_windowed_rows` to the
tighter of `max_list_rows` and the declared maximum at validated coordinates.
Observably still bounded: hostile sequence subclasses counted, zero-width
windows empty, queryset subclasses rebuilt-or-rejected (oracles read:
`tests/test_resource_policy.py` slice/count/hostile-`__getitem__`/window
cases; `examples/fakeshop/test_query/test_resource_policy_api.py` live
budget cases).

(b) `utils/querysets.py` (16 insertions, 42 deletions). The body of
`_RAW_LIST_SOURCE_POLICY` is untouched, as are `normalized_row_source` and
`is_async_only_iterable` (no hunk touches them; the `base_queryset` hunk is
docstring prose only). Deleted wording arms are unreachable-defect arms only:
`combined` in `_raw_list_source_message` (that policy switches combinators
off), `evaluated`/`routing` in `_visibility_result_error` and
`_prepared_visibility_source` (surfaces that never state those expectations);
removing arms for defects the raw-list seal cannot produce cannot change the
reachable path. The retired `_UNRECOMPOSED_CHILD_POLICY` is repointed at its
only consumers, the optimizer walker's prefetch-child plan path, to
`_PREFETCH_CHILD_POLICY` (same no-recomposition licence plus the shared-alias
requirement) — not resource-policy's path. Observably still bounded: the
seal-or-`ConfigurationError` behavior on unsealable subclasses is byte-identical.

(c) `schema.py` (84 insertions, 1 deletion — said loudly: the single removed
line is the one-line `DjangoErrorPolicyExtension` import replaced by its
parenthesized seven-line form; the additions are one docstring paragraph plus
exactly three methods, `execute_sync` / `execute` / `_masked_return`; all
else byte-identical). The new seam is error-masking only and shares the
extension's one implementation by call; it neither reads nor writes any
resource-policy state. Said loudly in the other direction too:
`django_strawberry_framework/resource_policy.py` has an empty diff across
`9031cb3d..bfaee91d` — the target itself did not move.

Behavioral note under DRY.md principle 8: short-circuit order, exceptions
raised (`ListArgumentError` at the field boundary, `ResourceLimitExceeded` at
the seams, `ConfigurationError` fail-closed on unsealable rows), SQL effects
(`LIMIT` via owned slice), and the observation points (deadline read before
fetch, bound read per call) are all unchanged on every path resource-policy
owns.

### 6. Freshness fingerprints

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e` (branch untouched, no
commit). Base of delta window: `9031cb3d`.
- HEAD blobs (`git rev-parse HEAD:<path>`): `resource_policy.py`
`647133d23785d325856b2d1d495d18c5741dd23c`; `list_field.py`
`ce682d5f79518919ff3676f2fc8bbe2bd33995a4`; `utils/querysets.py`
`96618fba4eafb6a87e73414770014e3aee5b41ef`; `schema.py`
`c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`.
- Worktree (`git hash-object`): `resource_policy.py`, `utils/querysets.py`,
`schema.py` match HEAD (clean); `list_field.py` is dirty under concurrent
work (worktree `d6af61646784deac2f3053bb4096b8599deae2f5` vs HEAD
`ce682d5f…`) so this trace was taken from `git show HEAD:` bytes, never the
worktree copy. Dirt elsewhere left untouched.
- Delta window numstat `9031cb3d..bfaee91d`: `list_field.py` 490/48,
`schema.py` 84/1, `utils/querysets.py` 16/42, `resource_policy.py` empty.
- Contracts read at HEAD blobs: `GOAL.md`
`7dfbef5c784519d5f95311aaeb8c6766ee966b02` (trust boundary),
`docs/dry/DRY.md` `e8151123ff7e129fe9881ec342231e9e1795148e` (principles 7/8),
`docs/dry/worker-2.md` `4f089ea4a58d73295638e83abf8c612bf31487f8`.
- Oracles read (HEAD blobs, execution not run per zero-edit re-review
constraint): `tests/test_resource_policy.py`
`8d2fe4f832dee326e1dab733359dc5b12ee454ba`,
`examples/fakeshop/test_query/test_resource_policy_api.py`
`3b1210cc1ff20a0c29b439aa671417f2577d561b`,
`tests/test_list_field.py` `2f77f77d67366373390458c681e33fd59cf42c92`,
`tests/utils/test_querysets.py` `977a81df44b5cede99b2be9b8dcc5be76db0f03a`.
- Artifact itself never opened: only existence/size confirmed
(`docs/dry/dry-file-resource_policy.md`, untracked, 72053 bytes); this section
was appended blind. Any fingerprint change above reopens this trace.

PHASE-1-TRACE-RECORDED `docs/dry/dry-file-resource_policy.md`

## Run-7 scoped re-trace (Worker-1, REOPENED queue item d3)

Run: 0.0.15 2026-09-29-7. Everything above this section is PRIOR EVIDENCE
ONLY (09-18/19 artifact, `Status: verified` at its stamp, plus the Q6
bounded re-review). This section re-traces the target fresh at HEAD bytes
and issues a CONFIRM or REVISE verdict for every prior finding, with fresh
evidence for each. No consolidation beyond this file item; no production
edits; no plan edits.

### Scope, attribution, fingerprints

Three states fingerprinted, all by blob id over exact bytes:

- Drift base `5ee86193:django_strawberry_framework/resource_policy.py` =
  `4b69e974decbd45916bd55f444f4b5f86724a07a`. Worker-0's measurement
  (base bytes == HEAD bytes) VERIFIED independently: identical blob id
  via `git rev-parse` plus byte `cmp` of both dumps.
- HEAD (`0c0537e2`, movement re-checked at close):
  `HEAD:django_strawberry_framework/resource_policy.py` = `4b69e974…`
  (1383 lines). All tracing below is against these bytes.
- Worktree: `5b4a80f0e03674b3ae105a03bb21774b602bfa38` (1376 lines;
  `git status` M). `git diff HEAD` shows exactly 13 hunks, 32+/39-.
- ITEM_BASELINE `3cc94208` (a merge commit,
  `Merge: 0c0537e2 febe1132`) carries blob `5b4a80f0…` for the target =
  the worktree bytes. The dirt sits inside the item baseline; this
  worker made none of it.

Attribution of all 13 worktree hunks by content. No `## Owned changes`
ledger row names this file, so every hunk below is concurrent-external;
the trace runs on HEAD bytes and touches nothing tracked:

- Truthful-reads migration (11 hunks, one vocabulary): the import
  split (`describe_value` dropped, `from .utils import truth` added);
  `describe_value` -> `truth.describe` at all three tails;
  `__reduce__` (`self.__class__` -> `type(self)` plus the
  `# truth: ok` marker); `_deadline_expired` (explicit early
  `None` return plus `isinstance` -> `truth.is_instance`);
  `_attach_cleanup_note` rewritten via `truth.static_attr` /
  `truth.is_exact` with `_is_cleanup_diagnostic` deleted and both
  cleanup sites moving from `except BaseException` + predicate to
  `except Exception` + comment. Behavior-preserving on every path.
- `ResourcePolicy` docstring seam list gaining the
  `types/resolvers.py` single-object resolvers: the docstring half of
  the concurrent worktree-only `check_deadline` seams there (import +
  5 call sites present in the worktree, zero at HEAD).
- `check_deadline` docstring reword ("this module" -> "the admission
  walk"): prose, same concurrent stream.
- `narrowed` else-branch
  `widens = value is not None and current is not None and value > current`
  -> `widens = value > current`: a simplification that is NOT
  behavior-preserving on the None-override path (HEAD answers
  `ConfigurationError` via the `replace` rebuild; the hunk answers
  `TypeError`). Observed, not homed — worktree dirt owned by
  whoever lands it; flagged for Worker-0 under
  `### Defects (run-7 re-trace)`.

Delta scoped fresh, prior stamp `647133d2` -> HEAD `4b69e974`: exactly
the five regions of commit `9350eb8d` ("Canonicalize the default policy
path and close ErrorPolicy to str subclasses"), nothing else: (a) the
module-docstring "reads back DEFAULT" -> "reads back the package's own
baseline"; (b) the `DEFAULT_RESOURCE_POLICY` comment rewritten
(template-not-authority) plus the new
`_PACKAGE_RESOURCE_POLICY = canonical_policy(DEFAULT_RESOURCE_POLICY, policy_cls=ResourcePolicy, display_name="resource policy")`
declaration; (c) `resolve_resource_policy` `default=` retargeted;
(d) `policy_from_info` docstring miss-path prose; (e)
`policy_from_info` miss arm `else DEFAULT_RESOURCE_POLICY` ->
`else _PACKAGE_RESOURCE_POLICY`. This matches the recorded drift
exactly. `git log 5ee86193..HEAD -- <target>` is empty, so history
confirms drift base == HEAD independently of the blob comparison.

### Enumeration (run-7 re-trace, HEAD bytes)

Instrument: `/tmp/rp-retrace/probe_run7.py` (read-only `ast.parse` +
text census over the dumped HEAD bytes; 20 checks, ALL OK; no Django
import, no DB, no pytest). **66 top-level statements** (prior 65 plus
the `_PACKAGE_RESOURCE_POLICY` declaration): docstring + 17 imports +
8 assigns + 1 annassign + 5 classes + 30 sync functions + 4 async
functions. `ResourcePolicy` body still 23 (docstring + 20 fields +
`__post_init__` + `narrowed`); `ResourceLimitExceeded` body still 3.

Member map vs the prior table: prior #1–29 identical (same binds,
same order); new #30 `_PACKAGE_RESOURCE_POLICY` -> R3 (a declaration
feeding the shared driver; converges onto the already-open family
`policy-authority-isolation`, which already lists this file); prior
#30–65 shift to #31–66 with binds and homes unchanged. 66/66 land in
a family row (the F1/F2/F3 consumptions), a file-local record
(R1–R9/R11), or a recorded rejection (J1/J2).

### Matrix (run-7 re-trace)

1. Cross-flavor policy mirroring — CONFIRM + extend. HEAD `git grep`
   for the budget vocabulary shows the same holder set, no second
   budget record in any flavor; the error side mirrors with its own
   `_PACKAGE_ERROR_POLICY` in distinct vocabulary (see J2 REVISE).
   Consumer censuses re-taken at HEAD bytes: sibling 13 names
   (membership swapped `DEFAULT_RESOURCE_POLICY` ->
   `_PACKAGE_RESOURCE_POLICY`, count still 13 — prior-stamp import
   list compared member by member); `list_field.py` 7 names (the
   prior "6" was an undercount: the 7-name membership predates the
   stamp, verified byte-identical at blob `f357eded`);
   `utils/connections.py` 2 names (unchanged);
   `schema.py` import gains `_PACKAGE_RESOURCE_POLICY`.
2. Sync/async twins — CONFIRM. Same 4 async nodes, same names;
   `_raw_list_bound` def + exactly 2 call sites (probe); the delta
   carries no async surface.
3. Derived knowledge — CONFIRM + extend. The 20 defaults are still
   single-spelled (empty diff across the record region);
   `_PACKAGE_*` derives from the template at import (no restated
   values); `DEFAULT_*` is code-read exactly once package-wide (the
   build at line 458; the other in-file hits are `__all__` + prose,
   and `__init__.py` carries import + `__all__` only).
4. Round-trip pairs — CONFIRM. Same 5 pairs, same owners; the miss
   arm still returns `copy_policy(…)` — a handout, asymmetric by
   design per the verified `utils/policies.py` F2 record.
5. Other media — REVISE census, CONFIRM roles. Consumers as in axis
   1; oracles grow the tamper/identity pins (live
   `test_a_written_exported_default_cannot_widen_an_unconfigured_schema`
   at `test_resource_policy_api.py:2813` HEAD; `is not
   DEFAULT_RESOURCE_POLICY` pins in `tests/test_resource_policy.py`);
   projections grow the rewritten comment blocks. No oracle reads
   the owner to enumerate (the pins compare identity, never
   `fields()`).
6. Enforcement by omission — CONFIRM. 20/20 fields gated (gate
   region byte-identical); deadline seams still exactly 5 call sites
   at HEAD (`_raw_list_bound`, `connection.py:1276`,
   `relay.py:477` + `:561`, `mutations/resolvers.py:204`;
   `types/resolvers.py` zero at HEAD — its worktree seams are the
   concurrent-external change attributed above, outside this
   trace); the trusted split unchanged (`trusted is True` +
   factory gate, both byte-identical).

### Challenges (run-7 re-trace)

C1–C20 re-counted at HEAD bytes; every definition count is unchanged:
C1 1, C2 1 (a default flip now flows template -> canonical -> seams,
still one edit), C3 1, C4 1, C5 1, C6 0 here / 1 driver, C7 1, C8 1,
C9 0 new, C10 1, C11 1, C12 1, C13 0 here / 1 owner, C14 1, C15 1,
C16 1, C17 1, C18 1, C19 refused, C20 refused. All CONFIRM.

New-shape challenges for the drift (variation axes of the
template/canonical split):

- C21 (tamper): write
  `DEFAULT_RESOURCE_POLICY.__dict__["max_list_rows"] = 999`
  post-import -> 0 enforcement definitions move: all 4 fallback
  readers (resolve default, `policy_from_info` miss arm, extensions
  fallback, schema `_FALLBACK_ENFORCEMENT`) name
  `_PACKAGE_RESOURCE_POLICY`, built once at import. Count 1: the
  declaration. Converges onto open family
  `policy-authority-isolation` (verified File `utils/policies.py`
  canonical-copy split, cited under R3 REVISE).
- C22 (rename a bound): the field declaration moves; the
  `_PACKAGE_*` build passes `policy_cls` by reference and the
  driver reads `fields()` at runtime -> 1. File-local, no new row.
- C23 (re-derive the authority per read instead of once at import):
  the declaration is the one definition; the 4 readers compose it
  by name (principle 6 — the same treatment as R9's C17: a
  constant plus N readers counts 1). No second definition.

### Findings (run-7 re-trace): one verdict per prior finding

- F1 (`typed-rejection-value-tail`, consumer) — CONFIRM. Import +
  exactly 3 `describe_value(` calls at HEAD (probe; lines
  255/396/1356). Owner `exceptions.py` blob identical to the
  stamp. Trigger re-swept: no `{value!r}` tail for an
  outside-package value.
- F2 (`async-only-queryset-row-adapter`, consumer) — CONFIRM. 1
  import + 1 `is_async_only_iterable(` call; zero adapter
  construction (`_AsyncQuerySetRows` absent). Trigger unfired.
- F3 (`sealed-execution-queryset`, consumer) — CONFIRM. 1 import +
  1 `normalized_row_source(` call; `_seal_or_defect` absent.
  Trigger unfired.
- F4 (`seal-defect-code-wording`, non-member) — CONFIRM. Code
  single-spelled (probe), still rendered via
  `coded_error_extensions`; the delta adds no code, so no shared
  wire vocabulary arises. Trigger unfired.
- F5 (`sync-boundary-recourse-wording`, non-member) — CONFIRM. The
  new prose names tamper scenarios, no hook and no remedy.
  Trigger unfired.
- R1 (record shape + defaults) — CONFIRM. 20 fields, frozen,
  defaults region byte-identical (empty diff); the class-docstring
  seam list byte-identical at HEAD (the `types/resolvers.py`
  sentence is worktree dirt).
- R2 (bound-domain gate) — CONFIRM. Gate region byte-identical:
  `_require_positive_int`, both exact predicates,
  `MAX_RESOURCE_BOUND`, the `__post_init__` loop,
  `validate_collection_bound`. The every-path-rebuilds claim
  re-cited via the verified `utils/policies.py` record (the
  canonical arms rebuild through `policy_cls(…)`).
- R3 (package default + resolution ladder) — REVISE.
  `DEFAULT_RESOURCE_POLICY` is now the exported value TEMPLATE
  (consumer-held; a deployment reads it to learn the bounds and
  copies it to build its own); `_PACKAGE_RESOURCE_POLICY =
  canonical_policy(…)` is the import-time canonical copy and the
  one baseline every fallback reads.
  `resolve_resource_policy` passes `default=_PACKAGE_RESOURCE_POLICY`;
  ladder behavior stays 100% driver-owned (C6: 0 here). Seeds
  unchanged (C7: 1). This converges onto the already-open family
  `policy-authority-isolation` (owner
  `utils/policies.py::canonical_policy` + `::copy_policy`), per
  the verified File `utils/policies.py` outcome: "each flavor
  keeps three object roles. `DEFAULT_*` is the exported value
  TEMPLATE, consumer-held, read by no enforcement seam …
  `_PACKAGE_*` is the import-time canonical copy … The resolved
  per-schema policy is canonicalized at resolution … and every
  consumer-reachable surface answers with a `copy_policy`
  duplicate" (`docs/dry/dry-file-utils__policies.md`
  `## System trace`, "The canonical-copy split"). Readers of the
  declaration: the resolve default, the `policy_from_info` miss
  arm, the extensions unconfigured-schema fallback
  (`extensions/resource_policy.py:1486`), and schema
  `_FALLBACK_ENFORCEMENT` (`schema.py:567`).
- R4 (narrowing contract) — CONFIRM. `narrowed` /
  `effective_bound` / `validate_trusted_flag` byte-identical
  (guard probe OK; `trusted is True` still the only widener).
- R5 (budget authority lifecycle) — REVISE. The miss path
  `policy_from_info` returns
  `copy_policy(… else _PACKAGE_RESOURCE_POLICY)` — a copy of the
  canonical, never the export. The copy-out set (mirror publish,
  `policy_from_info` both arms, both schema properties) is
  unchanged in mechanism, retargeted in source.
  `_FALLBACK_ENFORCEMENT` carries the `_PACKAGE_*` copies
  (`schema.py:567`; both properties copy per read, `:980`/`:994`).
  Verdict record, lease, carrier, and every arm/disarm seam
  byte-identical. C18 still 1. Trigger unchanged.
- R6 (deadline trio) — CONFIRM. Trio byte-identical; 5 seams
  re-counted at HEAD (matrix axis 6).
- R7 (sync windowing) — CONFIRM. Region byte-identical.
- R8 (async windowing + cleanup) — CONFIRM. Region byte-identical
  at HEAD: `_is_cleanup_diagnostic` present, both cleanup sites
  still `except BaseException` + predicate (their rewrite is
  worktree dirt).
- R9 (wire rejection) — CONFIRM. Region byte-identical;
  `__reduce__` still spells `self.__class__` at HEAD (the
  `type(self)` swap is worktree dirt).
- R11 (leaf manifest) — CONFIRM. 19 names, membership identical;
  `_PACKAGE_RESOURCE_POLICY` deliberately unexported (private by
  design — reachability from no exported name is what makes
  enforcing a tampered default impossible).
- J1 (shared security-bool helper, refused) — REVISE the
  difference, verdict stands. Sides at HEAD: this arm exact
  (`type(x) is not bool`), no default, guards a widening opt-in
  (unchanged); the error arm NOW exact
  (`type(self.enabled) is not bool`, default `True`, guards the
  masking switch — drift via `9350eb8d`, verified in the
  error_policy run-7 re-trace); the debug arm still
  `not isinstance`, default `False`, guards a disclosure. The
  "exact here vs `not isinstance` on both other sides" clause
  retires for the error side — and the debug docstring's "same
  rule … `ErrorPolicy.__post_init__`" sentence is now literally
  true. The refusal stands on the surviving differences:
  defaults still point three ways (none / `True` / `False`, so
  no shared default exists to own) and the per-site prose still
  names three unrelated deployment dangers (silent widening vs
  silent opt-out vs armed disclosure). Trigger unchanged.
- J2 (error/resource unification, refused) — REVISE the symmetry,
  verdict stands. The shared mechanism grows symmetrically: both
  sides now carry DEFAULT-template + `_PACKAGE_*`-canonical +
  resolve-default retarget + miss/fallback reads (error side at
  blob `1a19cd7d`, verified in its run-7 re-trace), still shared
  at the same owners (driver, copy, canonical, tail). What
  remains per side is still distinct vocabulary (~20 numeric
  bounds + deadline + narrowing + windowing + budget authority
  here vs 3 string/bool options there), still differing seeds,
  still inverse install positions (all byte-identical). Posit
  C20 again: a change to either side's fields still moves
  exactly one body. Trigger unchanged (a third policy with the
  identical declare→canonicalize→resolve→copy shape).
- Q6 bounded re-review — historical (blob `647133d2` era), kept
  as prior evidence. Its definition counts (budget 1, row-source
  1+1) re-confirmed at HEAD by C21–C23 and F2/F3.

Verdict totals: 13 CONFIRM (F1–F5, R1, R2, R4, R6, R7, R8, R9,
R11), 4 REVISE (R3, R5, J1, J2), 0 new families, 0 new findings.
The drift's new shape (the `_PACKAGE_RESOURCE_POLICY`
declaration plus the retargeted readers) converges onto the
already-verified, already-indexed open family
`policy-authority-isolation`; the resolver retarget converges
onto the already-open `schema-construction-policy-ladder`.

### Freshness (run-7 re-trace)

HEAD blobs (`git rev-parse HEAD:<path>`, HEAD `0c0537e2`):

- target `4b69e974decbd45916bd55f444f4b5f86724a07a`
- `exceptions.py` `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`
  (identical to stamp)
- `utils/querysets.py`
  `3616927de2bc8a7bead38f255ece8695064d5de0`
- `utils/policies.py`
  `8c881c0a165dc31022051dd628d6e36d99d44eca`
- `conf.py` `c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25`
  (identical to stamp)
- `schema.py` `e6b52335b1d12260474c1630792c15c5e6847919`
- `list_field.py`
  `21380eb72364caef0da05ca3ee3f26c0134e3904`
- `utils/connections.py`
  `f549389ef0ed97bfbe4b158ab21bfc993b71b714`
  (identical to stamp)
- `relay.py` `c3c5aea52768cbdb3a849c5944cb4b2245db5fde`
  (identical to stamp)
- `mutations/resolvers.py`
  `043a2d0bb2f68104b19a7f679abd2b267774ecdf`
- `types/resolvers.py`
  `72d62dc4ebfe90aa1ed13e6786c63f9d76873e59`
- `utils/operation_lease.py`
  `10c164b731b381d2b62adb5e2c5ce6b694a53fd0`
  (identical to stamp)
- `utils/context.py`
  `cd0adcc509a3a40e5b46ba761c6cbfec2c44359c`
  (identical to stamp)
- `extensions/resource_policy.py`
  `19e2309d06bdb3bf9441bd102b5755e55ab561a1`
- `extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`
  (identical to stamp)
- `utils/errors.py`
  `3e25e93bf2265209f79b03d4b17670814f25d676`
  (identical to stamp)
- `connection.py`
  `4894f90fb2963a44d25b0eabc649c67d04afa587`
- `error_policy.py`
  `1a19cd7d9c15964847ae21122b3032d27f60d546`
- `tests/test_resource_policy.py`
  `9206e8127a045737263152efcc98339d02ec52d4`
  (oracle census only)

Connected-source bytes were read from `git show HEAD:` (never the
dirty worktree) wherever the worktree disagrees with HEAD. Any
fingerprint change above reopens this re-trace.

### Defects (run-7 re-trace)

None at HEAD bytes. Every re-read body matched its prose; the four
`_PACKAGE_*` fallback readers all name the canonical copy and no
enforcement seam reads the export.

Not a defect, flagged for Worker-0 (concurrent-external worktree
dirt, observed-not-homed): worktree hunk 6 (`narrowed`
else-branch guard drop) changes the None-override path from
`ConfigurationError` to `TypeError`. It belongs to whoever lands
the worktree truth-migration stream, not to this item; this trace
neither endorses nor blocks it.

### Pending execution (run-7 re-trace)

None. The only executed proof is the read-only AST/text probe
(`/tmp/rp-retrace/probe_run7.py`, ALL OK — a `/tmp`-only path cited
by content, like the run-7 `utils/querysets.py` entry-3 probe); it
mutates no source, imports no Django, opens no database, so no
workspace copy was owed and no `__file__`/DB record applies. No
pytest run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. `FAKESHOP_SHARDED` / Postgres cells
`inapplicable by construction` for the probe, with the
database-reaching windowing/deadline paths cited as
`static-reviewed` oracles whose live rows the gate owns.

## Judgment (run-7 re-trace)

Backstop re-discharged at HEAD bytes: 66/66 module members + 23/23
`ResourcePolicy`-body members + 3/3 `ResourceLimitExceeded`-body
members enumerated, matrix re-discharged on all six axes, C1–C20
re-counted + C21–C23 new-shape challenges, every prior finding
CONFIRMed (13) or REVISed (4) with fresh evidence. The drift since
the prior stamp is exactly the recorded canonical-copy split (plus
the error-side exact-type gates J1 cites from the mirror item);
both converge onto already-verified, already-indexed families, so
no new family, no consolidation, no defect, and no production edit
is owed. Zero-edit result is legitimate for a file item.

## Index rows for Worker-0

(Worker-0 alone edits the plan; rows named here for transcription.
No plan-index text changes: every family the drift touches already
lists `resource_policy.py` under Files covered, and no new family
is named.)

- CONFIRMed, unchanged text: `typed-rejection-value-tail` (open;
  F1 consumer census re-verified); `async-only-queryset-row-adapter`
  (open; F2 predicate-only consumption re-verified);
  `sealed-execution-queryset` (open; F3 indirect consumption
  re-verified); `seal-defect-code-wording`,
  `sync-boundary-recourse-wording` (checked, still non-members);
  `schema-construction-policy-ladder` (open; R3 ladder behavior
  still driver-owned, file already listed).
- REVISEd at artifact level, no transcription owed:
  `policy-authority-isolation` (open; the `_PACKAGE_RESOURCE_POLICY`
  declaration plus the four retargeted readers converge onto the
  verified canonical-copy record, file already listed); R3/R5
  file-local text (template/canonical split); J1 refusal text
  (error-side exact-type drift); J2 refusal text (symmetric
  template/canonical split on both sides).
- New rows: none.

## Run-7 verification (Worker-2, REOPENED queue item d3)

Run: 0.0.15 2026-09-29-7. Expectation-first: from the dispatch record
(plan drift note: new `_PACKAGE_RESOURCE_POLICY` plus the retargeted
miss path; mirror error-side drift: canonical-copy split plus
exact-type gates) I expected a +1-member enumeration with the new
declaration converging onto the indexed policy family, a
template/authority re-homing of R3/R5, evidence-only revisions to
J1 (error-side exactness) and J2 (symmetric split), CONFIRM
everywhere the drift does not reach, and a fully concurrent-external
worktree attribution — then checked every claim below against HEAD
bytes independently (own `ast.parse`, own `git show HEAD:` censuses,
own blob diffs, one stdlib mechanism replica; never W1's probe,
never worker-memory).

### 1. Enumeration — STANDS

Own AST run over `git show HEAD:` bytes: **66** `ast.Module.body`
members (docstring + 17 imports + 8 assigns + 1 annassign + 5
classes + 30 sync functions + 4 async functions), `ResourcePolicy`
body **23** (docstring + 20 `AnnAssign` + `__post_init__` +
`narrowed`), `ResourceLimitExceeded` body **3** (docstring +
`__init__` + `__reduce__`). New #30 is exactly
`_PACKAGE_RESOURCE_POLICY`; prior #1–29 identical in bind and
order, prior #30–65 shifted to #31–66 unchanged. The four async
names match. 66/66 land in W1's map. HEAD is 1383 lines,
worktree 1376.

### 2. Hunk attribution — STANDS, one subtotal corrected

`git diff HEAD` shows exactly **13** `@@` hunks, 32+/39-; worktree
blob `5b4a80f0`, HEAD blob `4b69e974`, HEAD `0c0537e2` unmoved
(checked at open and close). Content verdict, independent: 10
truth-migration hunks (import split; `describe_value` ->
`truth.describe` at all three tails; `__reduce__`
`self.__class__` -> `type(self)` + marker; `_deadline_expired`
early-`None` + `isinstance` -> `truth.is_instance`;
`_attach_cleanup_note` rewrite with `_is_cleanup_diagnostic`
deleted; both cleanup sites to `except Exception`), plus the
`ResourcePolicy`-docstring seam sentence, the `check_deadline`
docstring reword, and the `narrowed` else-branch simplification.
W1's "11 hunks" for the truth group itemizes as 10 — arithmetic
slip, substance and 13-total correct. The early-`None` hunk is
behavior-preserving (HEAD already answers `None` for `None` by the
fall-through arm). Ledger check: no `## Owned changes` row names
this file. ITEM_BASELINE `3cc94208` carries `5b4a80f0` for this
path, so the dirt predates the item; W1 made none of it. All 13
concurrent-external, correctly left untouched, trace correctly on
HEAD bytes.

### 3. Drift scope — STANDS

`git diff 647133d2..4b69e974` is byte-identical to commit
`9350eb8d`'s target diff: exactly W1's five regions (module-docstring
baseline sentence; DEFAULT comment rewrite + `_PACKAGE_*`
declaration; resolve `default=` retarget; miss-path docstring;
miss arm). `git log 5ee86193..HEAD -- <target>` is empty and both
revs resolve to `4b69e974`, confirming base == HEAD twice over.
Error-side exact-type gates verified at HEAD bytes independently
(`error_policy.py:114` `type(self.enabled) is not bool`, `:120`
`type(value) is not str`), stated in the same commit message, and
carried by the verified mirror re-trace (plan: blob `1a19cd7d` ==
HEAD).

### 4. The 13 CONFIRMs — ALL STAND (independently probed)

F1: import + exactly 3 `describe_value(` calls at HEAD lines
255/396/1356; owner blob `e06b0b7f` unchanged. (The one `{value!r}`
hit at line 430 sits in `narrowed`, untouched by the drift, so the
trigger-sweep stands as scoped.) F2: 1 import + 1 call, zero
adapter construction. F3: 1 import + 1 call, `_seal_or_defect`
absent. F4: code single-spelled, still via
`coded_error_extensions`; drift adds no code. F5: new prose names
tamper scenarios only, no hook, no remedy. R1: frozen, 20 fields,
record region outside the drift. R2: gate region outside the
drift. R4: trio outside the drift; `trusted is True` the only
widener. R6: trio outside the drift; seams re-counted myself at
HEAD — `_raw_list_bound:990`, `connection.py:1276`,
`relay.py:477` + `:561`, `mutations/resolvers.py:204` — with
`types/resolvers.py` at zero, so exactly 5. R7: region outside the
drift; `_raw_list_bound` def + exactly 2 calls. R8: at HEAD
`_is_cleanup_diagnostic` present and both predicate cleanup sites
present (the two further `except BaseException` sites are the
window-collect rejection/primary-error paths, correctly outside
the claim). R9: `self.__class__` at HEAD. R11: 19 names,
membership unchanged, `_PACKAGE_*` unexported. Consumer censuses
re-taken: sibling 13 names with the `DEFAULT_*` ->
`_PACKAGE_*` swap verified member-by-member against stamp blob
`52084078`; `list_field.py` 7 names verified present already at
stamp blob `f357eded` (prior "6" was an undercount, as W1 says);
`DEFAULT_*` code-read exactly once package-wide (the line-458
build; all other hits `__all__`/prose/re-export); `schema.py:95`
import gains `_PACKAGE_*`. All 18 freshness blobs re-hashed from
`HEAD:` — every short id matches W1's record.

### 5. The 4 REVISEs — ALL ENDORSED

R3 (template/canonical split): declaration + retarget verified at
HEAD; all four fallback readers name the canonical (resolve
default, miss arm, `extensions/resource_policy.py:1486`,
`schema.py:567`, both schema properties copying per read).
Converges onto indexed open `policy-authority-isolation`, whose
owner record is verified (File `utils/policies.py`, run 5, blob
`8c881c0a` == HEAD). Endorsed.
R5 (miss path copies the canonical): miss arm verified in the
drift diff; copy-out mechanism elsewhere untouched. Endorsed.
J1 (security-bool refusal, difference revised): all three sides
verified at HEAD — this arm exact with no default, error arm now
exact (`error_policy.py:114`, default `True` at `:95`), debug arm
still `not isinstance` (`debug.py:693`, default `False` at `:672`).
Refusal stands on the surviving differences (defaults none /
`True` / `False`; three unrelated deployment dangers). Trigger
unchanged. Endorsed.
J2 (unification refusal, symmetry revised): both sides carry
template + canonical at HEAD blobs, shared owners unchanged,
remainder distinct (record regions untouched both sides), seeds
and install positions untouched. C20 re-count agreed. Endorsed.

### 6. Family convergence — STANDS, precisely read

`policy-authority-isolation` and `schema-construction-policy-ladder`
are indexed, `open`, and already list this file; their owner
record (File `utils/policies.py`) is verified at the HEAD blob —
that verified record is what "already-verified" denotes, matching
the mirror item's accepted wording (the family items themselves
remain undispatched, as W1's rows state). `sealed-execution-queryset`
and `async-only-queryset-row-adapter` are indexed, `open`, file
listed. `seal-defect-code-wording` (open) and
`sync-boundary-recourse-wording` (rejected) are indexed;
non-membership preserved. Observation for Worker-0 (pre-existing,
drift-untouched, not a blocker):
`typed-rejection-value-tail` has no plan row at all — a de facto
cross-artifact name whose transcription never landed, predating
this drift (F1's region is byte-identical). W1's "(open...)"
parenthetical inherits the prior artifact's belief; the F1
substance itself is verified correct.

### 7. No plan-index text changes — ENDORSED

Every family the drift touches already lists this file; no new
family is named; J1/J2 text updates are artifact-level. The
§6 observation predates the drift and is outside this re-trace's
scope to repair.

### 8. Zero-defect call plus hunk-6 flag — SPLIT: call endorsed, flag corrected

Zero defects at HEAD bytes: endorsed — every re-read body matched
its prose, all four fallback readers name the canonical, and no
enforcement seam reads the export (DEFAULT census above).
Attribution of worktree hunk 6 to the concurrent stream, not this
item: endorsed. Its stated mechanism ("None-override answers
`TypeError` instead of `ConfigurationError`") is rejected as
written: `candidate = replace(self, **overrides)` runs
`__post_init__` BEFORE the widening loop in both versions, so a
`None` override raises `ConfigurationError` at the `replace` line
in both — proven empirically with a stdlib replica (HEAD:
ConfigurationError; worktree: ConfigurationError). The only
reachable divergence is tampered-`self` (`self.__dict__` holding
`None`), where HEAD silently returns the candidate and the hunk
raises `TypeError`. Recorded here as the correction; the flag was
explicitly observed-not-homed and non-blocking, so no verdict
changes.

### Challenges, matrix, prose

C1–C20 re-counts all agree at HEAD bytes (C2's flow is now
template -> canonical -> seams, still one edit); C21–C23 agree
(tamper: 1 declaration + 4 named readers; rename: 1 via
`policy_cls` by reference; re-derive: 1 + readers per principle
6). All six matrix axes agree with the censuses re-taken in §4.
Artifact prose: `path::Symbol` citations with raw line numbers
only in this per-cycle scratchpad context, as allowed; no process
provenance; no new tests (none owed for a zero-edit file item);
no tracked `.py` touched, so no ruff run owed; no pytest run
(read-only probes only); sharded/Postgres `inapplicable by
construction` for the probes stands. Status placement: the header
`Status: verified` was the prior stamp's and the trailer
`Status: ready-for-verification/1` was the run-7 submission; with
everything standing, the header line is re-earned for run 7 and
the trailer is removed (mirror-item normalization).

### Verdict (Worker-2, run 7)

**Verified.** Backstop re-discharged at HEAD bytes (66/66 + 23/23
+ 3/3, six axes, 20 re-counted + 3 new-shape challenges, 13
CONFIRM + 4 REVISE each with fresh evidence, drift converging
onto already-indexed families with a verified owner record, zero
defects). Zero-edit result legitimate for a file item. For
Worker-0: tick File `resource_policy.py` as verified
(Run 0.0.15 2026-09-29-7); no `## Responsibility index` rows; no
`## Owned changes` rows; two record-accuracy corrections (§2
subtotal, §8 mechanism) and one transcription observation (§6)
above, none verdict-changing. HEAD `0c0537e2` unmoved at close.
No commit.
