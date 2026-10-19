# DRY review: `django_strawberry_framework/exceptions.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in one EXISTING responsibility family (reused, trigger
re-checked fresh against its difference — never inherited), a file-local
record with its proving challenge, or a recorded rejection with contract
difference + trigger + durable home. Zero production edits; zero tracked
files changed.

## System trace

Small target (415 lines, 16 top-level statements): the package's exception
basement. It DEFINES the error lattice
(`exceptions.py::DjangoStrawberryFrameworkError` with call-time
`__str__`/`__repr__` guards; `exceptions.py::ConfigurationError`,
`exceptions.py::OptimizerError` as the two catch families;
`exceptions.py::PathResolutionError` /
`exceptions.py::LookupValidationError` as the typed strict-classification
pair with pickle-stable constructors) and the hostile-input rendering ladder
(`exceptions.py::_safe_type_name` kind-name root,
`exceptions.py::_unprintable` standalone placeholder grammar,
`exceptions.py::_safe_arg_repr` guarded repr,
`exceptions.py::_safe_text` guarded str with fallback,
`exceptions.py::_safe_class_name` shared class-label renderer,
`exceptions.py::_safe_model_label` /
`exceptions.py::_safe_terminal_label` owner-fallback label readers,
`exceptions.py::describe_value` typed-rejection fragment tail). It ENFORCES
nothing at runtime itself — no raise site lives here; every constructor
builds through the guarded renderers so a hostile diagnostic value cannot
replace the typed error while the message is being assembled. The module
docstring's bottom-of-the-graph claim was verified: the only import is
`__future__.annotations`; zero Django, Strawberry, or first-party imports,
so the hierarchy is raisable from anywhere without circulars.

Connected code read for judgment, outside the item:
`django_strawberry_framework/utils/querysets.py` (the
`SyncMisuseError(ConfigurationError, RuntimeError)` dual marker +
`reject_async_in_sync_context`/`_disposed_awaitable`/`_dispose_sync_awaitable`
awaitable machinery + the stricter local `_safe_class_name` twin, full read
of the cited regions); `django_strawberry_framework/list_field.py`
(`ListArgumentError(GraphQLError, DjangoStrawberryFrameworkError)` + its
`describe_value`/`_safe_arg_repr`/`_safe_class_name` tails);
`django_strawberry_framework/resource_policy.py`
(`ResourceLimitExceeded(GraphQLError, DjangoStrawberryFrameworkError)` +
`describe_value` tails); `django_strawberry_framework/utils/errors.py`
(write-error envelope composing `_safe_text`/`_unprintable` by name);
`django_strawberry_framework/types/converters.py` (`_field_label`
composing `_safe_text`; `ConfigurationError` raise sites);
`django_strawberry_framework/scalars.py` (`_safe_scalar_map_key_label`
third class-label spelling + parity note);
`django_strawberry_framework/types/finalizer.py` (consumer of
`_safe_class_name`/`_safe_arg_repr`/`_safe_type_name` by name; local
`_safe_qualified_class_name`/`_safe_field_label`/`_safe_str` examined);
`django_strawberry_framework/utils/relations.py` (sole raise sites of
`PathResolutionError`/`LookupValidationError`: `classify_path`,
`validate_lookup_expr`, `path_traverses_to_many` lenient ladder);
`django_strawberry_framework/utils/policies.py`,
`django_strawberry_framework/utils/sessions.py`,
`django_strawberry_framework/error_policy.py`,
`django_strawberry_framework/extensions/debug.py`,
`django_strawberry_framework/schema.py`,
`django_strawberry_framework/consumers.py`,
`django_strawberry_framework/views.py`,
`django_strawberry_framework/routers.py` (all ten `describe_value`
consumer sites, import + raise lines); `django_strawberry_framework/__init__.py`
(root manifest + `_DRF_SOFT_EXPORTS`/`__getattr__` guard + `SyncMisuseError`
re-export chain); `django_strawberry_framework/connection.py`,
`django_strawberry_framework/types/relay.py`,
`django_strawberry_framework/filters/base.py`,
`django_strawberry_framework/forms/inputs.py`,
`django_strawberry_framework/mutations/sets.py`,
`django_strawberry_framework/orders/base.py` (remaining `_safe_class_name`
consumers); `tests/test_exceptions.py` (full read, 678 lines — every oracle
row); `tests/utils/test_querysets.py` (strict-twin oracle row, spot-read),
`tests/types/test_finalizer.py` + `tests/types/test_relay_interfaces.py` +
`tests/test_scalars.py` (shared-renderer oracle rows, spot-read).
Swept and excluded on the strength of the bodies: every other package module
imports or mentions the exception names only as noted in the matrix; name-only
lookalikes with no shared rule (`utils/inputs.py::_safe_import`,
`utils/permissions.py::_safe_get_model`, `testing/_wrap.py` safe-wrap) share
the `safe` token, not a contract. Prior artifacts used only as
rejected-candidate triggers, each re-derived fresh below (plan index
`typed-rejection-value-tail` row, plan index hostile-`_safe_class_name`
REJECTED row, `dry-file-error_policy.md` F2 scope note,
`dry-file-utils__querysets.md` seal/recourse/awaitable families). Never read
another worker's `worker-memory/`. The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched and hold none of this finding's
sites; concurrent dirt (`connection.py` hunk, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** The error-raising surface was swept
package-wide by mechanism, not by neighbor. `raise ConfigurationError`
appears in 54 files (schema construction, Meta validation, registry, every
set family, resolvers, policies — the package's default typed rejection);
`raise OptimizerError` in exactly 5 modules, 14 sites
(`optimizer/field_meta.py` 3 input-guard rejections,
`optimizer/plans.py` 4 window/partition rejections,
`optimizer/predicates.py` 3 attach-exists caller-contract guards,
`types/resolvers.py` 1 strictness-`"raise"` N+1 guard,
`utils/connections.py` 3 window bounds/mode rejections);
`raise PathResolutionError` 7 sites + `raise LookupValidationError` 10
sites, all inside `utils/relations.py::classify_path` /
`::validate_lookup_expr`; `raise SyncMisuseError` 5 sites
(`utils/querysets.py` 3, `utils/execution_mode.py` 1, `list_field.py` 1);
bare `raise GraphQLError` in 5 modules
(`connection.py`, `filters/base.py`, `filters/sets.py`,
`mutations/resolvers.py`, `relay.py` — wire-facing argument/pagination
denials); bare `ValueError`/`TypeError` at the scalar factory
(`scalars.py::strawberry_config`, BigInt parse/serialize) and the
`ListArgumentError` reason gate. The dual-inheritance markers come in
exactly two shapes, each owned outside this file: 2 ×
`(GraphQLError, DjangoStrawberryFrameworkError)` (`list_field.py`,
`resource_policy.py`) for wire-visible bound rejections, 1 ×
`(ConfigurationError, RuntimeError)` (`utils/querysets.py::SyncMisuseError`)
for sync-boundary misuse. This file defines NEITHER pair — it owns only the
bases the pairs compose (`DjangoStrawberryFrameworkError`,
`ConfigurationError`). No flavor mirrors an error taxonomy of its own; all
flavors raise the shared lattice. Axis discharged.

**2. Sync/async twins.** Target has no async surface (probe: zero
`AsyncFunctionDef`, zero `Await`). The renderers are pure total functions;
the lattice is sync construction; pickle `__reduce__` is sync by pickle
contract. The one color-adjacent behavior — `located_error` calling
`str()` on the exception at the GraphQL boundary — is color-free (a sync
render either way) and is exactly what the call-time guards own. No twin
owed. Axis discharged by absence with the stated reason.

**3. Derived rather than repeated knowledge.** Each rendering fact is
derived once: kind-name at `_safe_type_name` (its class-names-itself rule:
a class contributes its own `__name__`, any other object its type's, so a
Django model never reports `ModelBase`); the standalone placeholder at
`_unprintable` (single home of the `<unprintable {T}>` grammar, consumed by
`_safe_arg_repr`, `_safe_text`, and the base `__str__` fallback —
`tests/test_exceptions.py::test_safe_text_is_single_sourced_across_consumer_modules`
pins the import identity); the fragment tail at `describe_value`.
`_safe_model_label`/`_safe_terminal_label` each read their own metadata
slot once (`_meta.label`, `.name`); no second reader of either slot exists
in production for diagnostics. `_safe_class_name`'s `qualified` flag
derives `__qualname__` vs `__name__` from one parameter, not two bodies.
Every other spelling is a consumer (36 files import `_safe_arg_repr`, 34
`_safe_type_name`, 10 `describe_value`, 8 `_safe_class_name`, 5
`_safe_text`), an oracle spelling literals directly, or a projection. The
guarded-normalization idiom (try + base-`str`-slot strip + `or` fallback)
recurs across the sibling renderers with per-site fallback SUBJECTS
(placeholder vs owner name vs metaclass label vs repr) — shared means,
distinct contracts, each subject oracle-pinned (see R6 challenges). Axis
discharged.

**4. Inverse / round-trip pairs.** The exception half has no inverse by
contract: rendering is lossy and one-way (hostile values collapse to
placeholders; nothing parses a placeholder back). The round-trips that DO
exist are owned here and tested: `PathResolutionError.__reduce__` /
`LookupValidationError.__reduce__` preserve constructor args + instance
`__dict__` across pickle/copy/deepcopy (parametrized oracle rows), and
`ResourceLimitExceeded.__reduce__` at its own owner. `str`/`repr` have no
parse twin anywhere (sweep: no consumer parses a rendered placeholder).
Axis discharged by absence with the stated reason.

**5. Contracts restated in another medium.** Four media carry this file's
contracts: production code (target); consumers composing by name (the
import census above; `utils/errors.py` + `types/converters.py` import the
ONE `_safe_text`, pinned by identity assertion); oracles spelling literals
directly and driving behavior through construction
(`tests/test_exceptions.py`: lattice row, identity-through-`located_error`
rows, laziness/recompute rows, hostile-metadata rows, huge-int row,
per-helper rows — all independent: a spelling change fails them, none
enumerates the owner's internals); projections (every docstring here,
notably the `describe_value` scope paragraph and the twin-split clauses in
both `_safe_class_name` docstrings; GLOSSARY prose where it names error
codes). No oracle reads the owner to enumerate. Axis discharged.

**6. Enforcement by omission.** The guarded population was enumerated
member by member, not by search: every typed error constructor in this file
routes its hostile-capable inputs through a guarded renderer
(`PathResolutionError.__init__` via `_safe_model_label` + `_safe_arg_repr`;
`LookupValidationError.__init__` via `_safe_terminal_label` +
`_safe_arg_repr`; base `__str__`/`__repr__` via `_safe_arg_repr` +
`_safe_type_name`). The ten `describe_value` consumers cover every raise
whose value arrives from outside the package (transport cap, WS window,
router factories/consumers, both policy `__post_init__` gates, debug flag,
session engine, schema extension entries, list-field bounds). Deliberate
omissions with contract sources: (a) dozens of in-package `got {...}`
tails interpolate their own values — the `describe_value` scope paragraph
explicitly defers routing them ("a separate change ... deliberately not
claimed here"), so their rawness is recorded scope, not a gap; (b) the
scalar factory raises bare `ValueError` by its documented Strawberry
contract (spec-025 Decision 4), not a typed error; (c) wire denials raise
bare `GraphQLError` by the masking classifier's contract (a deliberate,
audited non-masking). No member lacks a guard its contract requires. Axis
discharged.

### Enumeration

Instrument: `ast.parse` over the pinned blob, counting `ast.Module.body`
members — **16 top-level statements** — plus, better than the minimum,
every class-body member (2 + 0 + 2 + 2 + 0). Every member lands below;
every challenge in `### Challenges` ends in a family row, a file-local
record, or a recorded rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (bottom-of-graph + no-circular-import contract) | (none) | projection of the import census (R8); verified: sole import is `__future__` |
| 2 | `from __future__ import annotations` | annotations | machinery |
| 3 | `__all__ = (…5…)` | leaf manifest | R8, file-local |
| 4 | `def _safe_type_name` | kind-name root renderer | R1, file-local |
| 5 | `def _unprintable` | standalone placeholder grammar | R2, file-local |
| 6 | `def _safe_arg_repr` | guarded repr renderer | R3, file-local |
| 7 | `def _safe_text` | guarded str renderer + fallback | R4, file-local |
| 8 | `def _safe_class_name` | shared class-label renderer | R5, file-local (+ J1 twin) |
| 9 | `def _safe_model_label` | model-label reader, owner fallback | R6, file-local |
| 10 | `def _safe_terminal_label` | terminal-label reader, owner fallback | R6, file-local |
| 11 | `def describe_value` | typed-rejection fragment tail | F1 (existing family `typed-rejection-value-tail`) |
| 12 | `class DjangoStrawberryFrameworkError` | package base + call-time guards | R7, file-local |
| 12.1 | `def __str__` | lazy safe render, single-arg placeholder arm | R7 |
| 12.2 | `def __repr__` | lazy safe render, typename + guarded args | R7 |
| 13 | `class ConfigurationError` | configuration-family root | R7, file-local |
| 14 | `class PathResolutionError` | strict-path typed error | R7, file-local |
| 14.1 | `def __init__` | guarded ctor, attribute retention | R7 |
| 14.2 | `def __reduce__` | pickle/copy stability | R7 |
| 15 | `class LookupValidationError` | lookup typed error | R7, file-local |
| 15.1 | `def __init__` | guarded ctor, attribute retention | R7 |
| 15.2 | `def __reduce__` | pickle/copy stability | R7 |
| 16 | `class OptimizerError` | planning-failure family root | R7, file-local |

Rules: R1 kind-name root; R2 placeholder grammar; R3 guarded repr; R4
guarded str; R5 shared class label; R6 owner-fallback label readers; R7
lattice + call-time guards + typed ctors; R8 leaf manifest. The plan's
`## Responsibility index` already carries `typed-rejection-value-tail`
(open, owner here), `awaitable-refusal-and-disposal` (open),
`seal-defect-code-wording` (open), `sync-boundary-recourse-wording`
(rejected), `drf-soft-export-guard` (open) — all five reused below with
triggers re-checked fresh, not renamed. No other existing family owns a
definition here. One pre-existing rejection re-derived fresh (J1). No new
family is named: R1–R8 each count 1 per change axis with no second
definition site; the considered shared forms stay refused with contract
differences + triggers (J1, R4-note, R6-note).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R1 kind-name policy | classes stop naming themselves (report metaclass) | **1** (`_safe_type_name`; 34 consumer files + all sibling renderers follow) | file-local |
| C2 | R2 placeholder spelling | `<unprintable {T}>` → another standalone grammar | **1** (`_unprintable`; `_safe_arg_repr`, `_safe_text`, base `__str__`, `utils/errors.py` envelope follow by call) | file-local |
| C3 | F1 fragment spelling | `an unprintable {T}` → another fragment grammar | **1** (`describe_value` except-arm; unifying with C2 refused in-docstring — fragment vs standalone) | family (F1) |
| C4 | R3 repr policy | truncate/bound hostile reprs | **1** (`_safe_arg_repr`) | file-local |
| C5 | R4 str policy | change the `tp_str`-leak strip or empty→fallback rung | **1** (`_safe_text`; `utils/errors.py` + `types/converters.py` compose by name) | file-local |
| C6 | R5 label policy | `qualified` gains a third (module) arm | **1** (`_safe_class_name`; 8 consumers follow; finalizer's `_safe_qualified_class_name` already layers module handling on top by call) | file-local |
| C7 | R6 fallback subject | model-label fallback names the label type, not the model | **1** (`_safe_model_label`; terminal reader doesn't move — proves the pair shares means, not rule) | file-local |
| C8 | R6 slot | `_meta.label` shape changes | **1** (`_safe_model_label`; `_safe_terminal_label` reads `.name`, doesn't move) | file-local |
| C9 | R7 base guards | render at construction (sanitize `args`) instead of call time | refused — call-time is the contract: stateful-later failure + `args` reassignment + locale-lazy rows pin it (oracles fail a sanitize-at-construction body) | refused |
| C10 | R7 family split | `PathResolutionError` subclasses `OptimizerError` | **1** here (base list; `utils/relations.py` raise sites unchanged, still caught via base) — plus every `except ConfigurationError` consumer re-derives; the split is documented intent (definition-time vs planning failure) | file-local |
| C11 | R7 wire pair | third `(GraphQLError, DjangoStrawberryFrameworkError)` bound rejection | **0** here / **1** at the new pair's module (this file owns only the bases) | independent |
| C12 | R7 sync pair | second `(ConfigurationError, RuntimeError)` misuse marker | **0** here / **1** at its module (same: bases owned here, pair owned there) | independent |
| C13 | R8 manifest | new public error name | **1** (`__all__` tuple + class decl; root re-export is a separate surface decision) | file-local |
| C14 | J1 strictness | sealed boundary tolerates repr-dispatch on the rejected object | **1** at `utils/querysets.py` (strict twin relaxes to the shared spelling; shared body doesn't move) | rejection stands |
| C15 | J1 grammar | shared renderer adopts the strict never-repr fallback | **0** (refused — 8 consumer modules' `<unprintable>`/repr rows pin the repr rung; the strict test pins the typename rung) | refused |

**Experiment.** Read-only probe (no source mutation, no Django setup, no
DB, no shared-tree pytest — the workspace recipe is for mutating proofs, of
which this zero-edit item has none):

```shell
python3 docs/dry/temp-tests/dry-file-exceptions/probe_w1.py
```

Output (`W1 PROBE: ALL OK`, 63 checks): 16-member module AST with
function/class census (§§1–2); 5-name manifest (§3); lattice bases + member
lists (§4); zero async nodes (§5); absence markers for all four foreign
families + no raise in target (§6: each cross-family token appears exactly
once, in docstrings only); dual-marker census — 1 sync pair, 2 wire pairs
(§7); `describe_value` def once + 11-file census = 10 consumers + def site
(§8); functional lattice + printable/hostile/huge-int tails + fallback
grammars + twin-AST contrast (§9); item-baseline diff empty + working blob
equals `HEAD:` blob (§10); package population 117 (§11). Status:
`execution-verified` for every identity/count/shape/absence claim below.
Rejects the wrong results "a second tail renderer exists", "an awaitable/
seal/recourse/drf definition lives here", "the target drifted from its
baseline", "the strict twin shares the repr rung".

## Findings

No production edit is owed by a file item; the one family below is REUSED
from the plan (trigger re-checked fresh on current evidence), four more are
checked non-members, the rest are file-local records and one recorded
rejection (confirm-and-extend).

### F1 — typed rejection value tail (existing family `typed-rejection-value-tail`, status stays `open`)

- **Contract + variation.** Every typed rejection whose value came from
outside the package renders its `got` tail through
`exceptions.py::describe_value` — `f"{_safe_type_name(value)} {value!r}"`
collapsing hostile-`__repr__` AND huge-int (`sys.get_int_max_str_digits()`)
failures to `an unprintable {T}` — so the message cannot raise while being
formatted at the raise site, before any exception object (and its
`__str__` guard) exists. Variation: per-domain prose; the renderer fixed.
Precise rule: `{TypeName} {value!r}` on success, `an unprintable
{TypeName}` on ANY `BaseException` from the f-string (display must never
propagate `SystemExit`/`KeyboardInterrupt`).
- **Sites + roles.** *Definition*: `exceptions.py::describe_value`
(unchanged). *Consumers* (all compose by name, listed never counted):
`consumers.py` (WS revalidation window), `views.py` (body-cap),
`routers.py` (3 factory + 1 consumer + 1 application rejections),
`error_policy.py` (2 `__post_init__` gates), `resource_policy.py` (3
policy gates), `extensions/debug.py` (bool gate), `utils/policies.py` (2
driver gates), `utils/sessions.py` (engine gate), `schema.py` (4
extension-entry gates), `list_field.py` (3 bound tails). *Oracles*: the
huge-int/hostile-`__repr__`/`BaseException` rows at the owner
(`tests/test_exceptions.py`, bodies cited). *Projections*: the scope
paragraph on the owner.
- **Challenges.** C3 → 1 at the renderer for a renderer change; prose
changes → 1 per consumer site (per-domain wording stays per site, the
family's stated split). A second tail renderer interpolating `{value!r}`
for an outside-package value would reopen — swept: all ten consumers route
through the renderer (probe §8).
- **Index note for Worker 0 (additive only).** The plan's index row lists
`exceptions.py`, `consumers.py`, `views.py`, `routers.py`,
`error_policy.py` under Files covered. The owner's scope paragraph names
those five plus `resource_policy.py` and `extensions/debug.py`; this trace
establishes four further consumers: `utils/policies.py`,
`utils/sessions.py`, `schema.py`, `list_field.py`. Whether the row's file
list gains them is Worker 0's call; no definition count changes either
way. The scope paragraph's "stated exactly" list names 6 of the 10 — the
other 4 satisfy its forward rule ("a new rejection whose value came from
outside the package belongs on this helper") but aren't enumerated; true
but incomplete, noted here, not a defect (no contradiction).
- **Owner + lifetime.** `exceptions.py` (unchanged). Pure derivation, never
cached.
- **Migration / Coupling.** None (zero-edit item).
- **Behavioral proof.** `execution-verified` for def/use census + tail
shapes incl. the 10**5000 collapse (probe §§8–9); `static-reviewed` for
consumer bodies + scope paragraph. Rejects "a consumer interpolates the
value itself".
- **Structural gate.** The owner's hostile-tail rows (direct interpolation
raises `ValueError` instead of `ConfigurationError`). Negative control:
`f"{value!r}"` at any consumer passes every small-value oracle and fails
exactly those rows.
- **Freshness.** `django_strawberry_framework/exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`,
`django_strawberry_framework/consumers.py`
`18f3ea161b6081a91445796902a9635cb7e2e3bc`,
`django_strawberry_framework/views.py`
`9f85b0df26a17e800ec392aa13f6848e07633895`,
`django_strawberry_framework/routers.py`
`a18c5001471d4a937bb81d2ff41a2e442e7d2dad`,
`django_strawberry_framework/error_policy.py`
`fa94fcd9e952c4a33dd32d9b1b26ef3de475cc91`,
`django_strawberry_framework/resource_policy.py`
`647133d23785d325856b2d1d495d18c5741dd23c`,
`django_strawberry_framework/schema.py`
`2f72732123ca1156c4eb122ce7b53de6269de95e`,
`django_strawberry_framework/list_field.py`
`f357eded3d96fcffe17e6fd84bceb8cd12af98d5`,
`django_strawberry_framework/utils/policies.py`
`860b181fa8c0a8e5fd18e0e4c114e9bde9292c9e`,
`django_strawberry_framework/utils/sessions.py`
`f0d9297c942a4915ca08ac0714cee73f6042af34`,
`django_strawberry_framework/extensions/debug.py`
`bf25c146111337ee0af590e7496b34c010c2f7be`,
`tests/test_exceptions.py`
`a87e487224689504693103ab4058504d82128f07`.

### F2 — awaitable refusal and disposal (existing family `awaitable-refusal-and-disposal`, checked, not a member)

- **Contract difference.** The family detects an awaitable returned from a
sync pipeline seam, disposes it (close coroutine / cancel future), then
raises at the caller (`utils/querysets.py::_dispose_sync_awaitable`,
`::_disposed_awaitable`, `::reject_async_in_sync_context`). This target
holds none of it: zero `isawaitable`, zero `_dispose`, zero coroutine
vocabulary outside no mention at all (probe §6). Its only intersection is
downstream: three of the family's raise sites raise the
`SyncMisuseError` whose `ConfigurationError` half is owned here (R7).
Sharing a base class is composition, not a second definition of the
refusal.
- **Reconsideration trigger.** An awaitable detect/dispose/raise body
arriving in this module (a second `_dispose_sync_awaitable`) — then it
becomes a member row.
- **Durable home.** This finding + the owner
(`utils/querysets.py::_dispose_sync_awaitable`); nothing to record here.
- **Freshness.** Target as in F1 +
`django_strawberry_framework/utils/querysets.py`
`1539b66c9ce9a659e1dc5f6bf1029b15d6868587`.

### F3 — seal defect code wording (existing family `seal-defect-code-wording`, checked, not a member)

- **Contract difference.** The seal family renders `(code, detail)` tuples
through `utils/querysets.py::_defect_message` with a fixed position per
code for deployment logs. This file publishes no code vocabulary: zero
`_defect_message`, zero `_seal_or_defect`, zero `SealPolicy` (probe §6);
the lone `seal` token is the docstring clause pointing AT the twin (J1).
Its stable strings are typenames and placeholders, never defect codes.
- **Reconsideration trigger.** A `(code, detail)` defect vocabulary
arriving here (a seal code formatted by these renderers into a shared
table) — then the wording becomes one rule.
- **Durable home.** This finding + the seal owner; nothing here.
- **Freshness.** Target as in F1 + querysets blob as in F2.

### F4 — sync boundary recourse wording (existing family `sync-boundary-recourse-wording`, checked, not a member)

- **Contract difference.** The recourse family generates per-hook remedy
sentences (`utils/querysets.py::sync_pipeline_recourse` + decliners
naming `has_permission` / `check_permission` and remedies). This file's
prose names no hook and offers no remedy: zero `recourse`, zero
`sync_pipeline` (probe §6). The family's standing index rejection is
corroborated, not inherited — this target doesn't share even the one
clause other modules share.
- **Reconsideration trigger.** A remedy sentence quoting an error contract
owned here (a recourse pointing at `ConfigurationError` wording) — then
the shared clause becomes the rule.
- **Durable home.** This finding + the recourse owners; nothing here.
- **Freshness.** Target as in F1 + querysets blob as in F2.

### F5 — DRF soft-export guard (existing family `drf-soft-export-guard`, checked, not a member)

- **Contract difference.** The guard resolves DRF-optional public names
lazily by NAME through the shared `require_drf` gate
(`django_strawberry_framework/__init__.py::_DRF_SOFT_EXPORTS` +
`__getattr__`, deliberately absent from `__all__`). This file holds none
of it: zero `require_drf`, zero `_DRF_SOFT`, zero module `__getattr__`
(probe §6). Its own `__all__` is a plain 5-name leaf manifest (R8) with
the opposite polarity — everything public is listed, nothing is lazy —
because this module has no optional dependencies to guard.
- **Reconsideration trigger.** An optional-dependency name arriving here
behind a lazy gate — then it becomes a consumer row.
- **Durable home.** This finding + the root owner; nothing here.
- **Freshness.** Target as in F1 +
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`.

### File-local records (no second definition after the matrix)

- **R1 — kind-name root.** `exceptions.py::_safe_type_name` (a class
contributes its own `__name__`, any other object its type's; unreadable or
non-string names fall back to the metaclass label, then `"object"`; `str`
subclass names stripped through the base slot). C1 → 1. Every sibling
renderer and 34 consumer files derive from it by call. Trigger: a second
kind-name rule (e.g. qualname-first diagnostics) would make it a family.
Freshness: target as in F1.
- **R2 — standalone placeholder grammar.**
`exceptions.py::_unprintable` (single home of `<unprintable {T}>`,
consumed by `_safe_arg_repr`, `_safe_text`, base `__str__`, and
`utils/errors.py` by import — identity-pinned). C2 → 1. The FRAGMENT
spelling (`an unprintable {T}`) is deliberately NOT unified (F1/C3): two
spellings across standalone vs interpolated sites is the recorded cost of
the grammatical difference — "do not unify them, or one of the sites reads
wrongly" (owner docstring). Trigger: a second standalone grammar would
make it a family. Freshness: target + `utils/errors.py`
`3e25e93bf2265209f79b03d4b17670814f25d676` as in F1.
- **R3 — guarded repr.** `exceptions.py::_safe_arg_repr`
(`repr(value)` through the base `str` slot, else `_unprintable`). C4 → 1.
36 files compose it by name. Trigger: a second guarded-repr body would
make it a family. Freshness: target as in F1.
- **R4 — guarded str.** `exceptions.py::_safe_text` (str-slot read for
`str` inputs, guarded `str()` + base-slot re-strip for the `tp_str`-leak
case, empty→`fallback`, raising→`_unprintable`). C5 → 1. Consumers by
name: `utils/errors.py` (envelope path/message coercion),
`types/converters.py` (`Model.field` labels), `types/base.py`,
`forms/sets.py`, `forms/inputs.py`. Examined and held distinct:
`types/finalizer.py::_safe_str` (trusts subclass `str()` unless it raises
— no strip, no fallback) and `::_safe_field_label` (DELIBERATELY runs
subclass `__str__`, oracle-pinned) compose `_safe_arg_repr`/`_safe_type_name`
by name but own simpler contracts for finalization-time labels; unifying
them here would couple the write-error envelope's leak-proofing to label
plainness. Trigger: a third guarded-str-with-fallback body, or a leak fix
needing identical edits in two bodies, would name the family (finalizer
item verifies its members). Freshness: target + `types/converters.py`
`9ceb34afec591a554fd71b7b3f3b9eae4f37fa75` + envelope blob as in R2.
- **R5 — shared class label.** `exceptions.py::_safe_class_name`
(`__name__`/`__qualname__` via `getattr`, base-slot strip, empty→repr,
non-string→guarded repr, unreadable→`_safe_type_name`). C6 → 1. Eight
consumer modules compose it by name (connection, filters/base,
forms/inputs, list_field, mutations/sets, orders/base, types/finalizer,
types/relay). The stricter twin lives in J1. Trigger: a second shared
(class-label, repr-fallback, qualified) body would make it a family.
Freshness: target + `types/finalizer.py`
`77fd9a2dd229eb9de5f29188c5058035d3606323` + `types/relay.py`
`5243986223547af7bcab691032e1d6792655fd9d` + `connection.py` working blob
`3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` (concurrent cursor-guard hunk,
left alone; `HEAD:` blob `93e998f2c7ea1d7f18607a6e37e394466ac75ad4` —
neither fingerprinted site overlaps the concurrent hunk, verified by
content: `_guard_source_not_pre_sliced` region untouched).
- **R6 — owner-fallback label readers.** `exceptions.py::_safe_model_label`
(`_meta.label`, owner-name fallback) + `::_safe_terminal_label` (`.name`,
owner-name fallback), each used exactly once (the two typed ctors). C7/C8
→ 1 each — the pair shares MEANS (guarded normalization skeleton) but not
RULE: fallback subject (model vs terminal identity) and slot differ, each
oracle-pinned to name the actionable owner rather than the label object
(routing through `_safe_text` would print `<unprintable …>` naming the
label type and break those rows). Trigger: a third owner-fallback reader,
or an idiom fix provably needing identical edits in both bodies, would
name the family. Freshness: target as in F1.
- **R7 — lattice + call-time guards + typed ctors.**
`exceptions.py::DjangoStrawberryFrameworkError` (identity-authoritative
`args`; `__str__`/`__repr__` recompute safely per call so
graphql-core `located_error`'s `str()` never replaces the typed error —
C9 refused: sanitize-at-construction fails the stateful-later,
args-reassignment, and lazy rows), `::ConfigurationError` (family root
for ~54 raising files), `::PathResolutionError` /
`::LookupValidationError` (strict-classification pair, raises SOLELY in
`utils/relations.py`, caught via base; C10 → 1 here for a base change),
`::OptimizerError` (14 raise sites in 5 planner modules, never a
`ConfigurationError` — lattice row pins the non-subclassing). The two
dual-inheritance pairs are owned at their modules (C11/C12 → 0 here):
wire pair at `list_field.py`/`resource_policy.py`, sync pair at
`utils/querysets.py` (re-exported through the root + `types.relay` for
back-compat). Trigger: a third catch family or a second base-guard body
would make it a family. Freshness: target + `utils/relations.py`
`7662b0bb669c4dfba4a437f3b8f309357f718dca` + planner blobs
(`optimizer/field_meta.py`
`7215c887aa26b1d828503ca30dd3b02546fe68b3`,
`optimizer/plans.py`
`cce985319c8833f3660653327d3003f1f03655a5`,
`optimizer/predicates.py`
`4e87c733f19b43b67c67d3b97d920013e164bb1f`,
`utils/connections.py`
`f549389ef0ed97bfbe4b158ab21bfc993b71b714`,
`types/resolvers.py`
`f3341e6a9f52659925762bce097033bac67e3b51`) + oracle blob as in F1.
- **R8 — leaf manifest + graph-bottom projection.** `__all__` (5 error
names; every public class exported). The 8 helpers stay out by the
underscore convention except `describe_value`, which is public-by-name,
imported by 10 modules, yet absent from the tuple — no oracle pins either
spelling and no star-import exists anywhere, so the absence is an
unpinned observation, not a gap (trigger: an oracle or doc claiming the
star surface would rule it). The bottom-of-graph projection (module
docstring) verified against the body: sole import `__future__`. C13 → 1.
Trigger: a second manifest over these names would make it a family.
Freshness: target as in F1.

### J1 — hostile-metaclass-safe class-name rendering (pre-existing plan REJECTION row, re-derived fresh: CONFIRMED, extended with a third site)

Three bodies spell nearby rules; each encodes a distinct contract with its
own reasons to change:

| Site | Signature | Empty `__name__` | Non-string `__name__` | Unreadable | `qualified` |
|---|---|---|---|---|---|
| `exceptions.py::_safe_class_name` (shared) | `(value, *, qualified=False)` via `getattr` | → repr (`"''"`) | → guarded repr of the NAME | → `_safe_type_name` | yes |
| `utils/querysets.py::_safe_class_name` (strict twin) | `(value)` via `value.__name__` | accepted as-is | → `_safe_type_name` (metaclass label; NEVER reprs the name object) | → `_safe_type_name` | no |
| `scalars.py::_safe_scalar_map_key_label` (factory twin) | `(key)` via `getattr(key, "__name__", None)` | accepted as-is | → guarded repr of the KEY | → repr (`None`) | no |

- **Contract differences.** The shared body labels classes inside
`ConfigurationError` prose across 8 modules: the repr rung keeps SOME
rendering for malformed metadata (oracle: `_MalformedName` → `"42"`), and
`qualified` serves finalizer binding diagnostics. The strict twin labels
the consumer queryset the sealed boundary is REJECTING: repr-dispatch on
that very object could run hostile consumer code mid-rejection, so the
fallback never touches the name object (oracle:
`_MalformedName` → `"_NonStringNameMeta"` — the two oracles DIVERGE by
specification, C15). The factory twin labels a dict KEY inside a factory
`ValueError` (not a framework error at all): `None`-name and non-string
both degrade to repr-of-key, and its `sorted()` call-site additionally
needs `__lt__`-safety the error-message sites never face. C14 → 1 at the
twin; unifying the strict rung into the shared body fails the strict
oracle; unifying the shared repr rung into the strict body fails the
shared oracle.
- **Trigger re-checked fresh (not inherited).** The plan row's trigger
stands, extended: a change that removes the sealed boundary's
never-dispatch constraint (boundary no longer rejects hostile objects),
or a `strict=` parameter the 8 shared consumers provably never set, or a
fourth spelling arriving with identical fallback + qualification — any of
these reopens the count. Measured today: constraints intact, oracles
still diverge, third site found (factory twin) with its own `sorted()` +
`ValueError` reasons.
- **Durable home.** CONFIRMED at the existing homes — the split clause in
`exceptions.py::_safe_class_name`'s docstring ("the sealed-queryset
boundary … deliberately keeps a stricter local variant") and the
`STRICTER` clause in `utils/querysets.py::_safe_class_name`'s docstring —
plus this finding. Index note for Worker 0: the plan row's Files covered
(`utils/querysets.py`, `exceptions.py`) may gain `scalars.py` (third
spelling, `scalars.py::_safe_scalar_map_key_label`); no definition count
changes. The factory twin's own durable clause (its parity note) is its
file item's to verify.
- **Freshness.** Target as in F1 + querysets blob as in F2 +
`django_strawberry_framework/scalars.py`
`5e354042d405040f6137cebd39abe9c042ffece8` +
`tests/utils/test_querysets.py` strict-twin row (staged +31 hunk left
alone) + `tests/types/test_relay_interfaces.py` shared row (spot-read).

## Defects

None. Every claim checked while tracing held: the bottom-of-graph import
census (sole `__future__` import); the lattice rows (all six assertions);
args-identity + laziness + stateful-later + `BaseException`-swallow rows;
both typed-ctor hostile-metadata rows; pickle/copy/deepcopy rows;
single-sourcing identity rows (`_safe_text` shared across
`utils/errors.py`/`types/converters.py`); all ten consumer import/use
sites; both twin docstring clauses matching their bodies (empty-string
acceptance, fallback subjects, `qualified` support verified against each
body, not assumed); the dual-marker census (1 sync pair, 2 wire pairs, no
pair defined here); the raise-site census by mechanism (54 / 5-modules-14 /
7+10 / 5 / 5-modules-bare / scalar-`ValueError`). Nothing routed to any
owner.

## Pending execution

None. The execution proofs (read-only probe driving the AST plus the
package-wide text census plus direct module-load behavior checks, command
in `### Challenges`) already ran green against the shared tree; they
mutate no source, open no database, and configure no Django, so no
workspace copy was owed and no `__file__`/DB `NAME` record applies. No
pytest was run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. No `FAKESHOP_SHARDED` or
Postgres cell is owed: the target's code path reaches no database, alias,
or dialect decision (`inapplicable by construction` — pure total
functions plus exception construction; the only settings-adjacent values
are string-key defaults resolved elsewhere).

## Judgment

Backstop discharged: 16/16 `ast.Module.body` members enumerated plus all 6
class-body members, 15 challenges run, every rule terminating in the one
existing family it touches (`typed-rejection-value-tail` as the owned
definition with 10 verified consumers and an additive index note),
a file-local record with its proving challenge (R1–R8), a checked
non-member verdict with contract difference (F2–F5, each trigger
re-checked fresh), or a recorded rejection with difference + trigger +
durable home (J1 — the plan's hostile-class-name rejection CONFIRMED on
fresh derivation and extended with the factory third site). The
error-raising matrix (54-file `ConfigurationError` sea, 14-site
`OptimizerError`, relations-owned typed pair, 5-site `SyncMisuseError`,
bare wire `GraphQLError`s, scalar `ValueError`s, exactly two
dual-inheritance shapes owned outside this file) shows this target owns
the bases and the renderers and nothing else. Zero-edit result is
legitimate.

No new `## Responsibility index` rows proposed for Worker 0: the only
family this target touches is already indexed (F1 carries one additive
Files-covered note); J1 carries one additive Files-covered note on an
already-rejected row; the R4/R6 near-twin notes name no second definition
and live at their owner paragraphs plus this finding.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
be9476561fa0646d952a0bd13baf211af0b2912a --
django_strawberry_framework/exceptions.py` is empty (0 bytes, re-measured
after the probe run via probe §10); the working blob
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` equals the item baseline, the
cycle-baseline member, and `HEAD:` — the target is clean, so no hunk
attribution was owed. Before touching any path, the item-scoped paths were
verified clean; the `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched; concurrent dirt (`connection.py`
hunk, `tests/test_connection.py`, staged `tests/utils/test_querysets.py`
+31, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) was never
edited, reverted, or tidied, and no other dirty path was written (sibling
`dry-file-*.md` untracked artifacts are other items' work, left alone).
Dirt elsewhere left alone, not a stop. No commit. Untracked scratch
created (not tracked changes): this artifact
`docs/dry/dry-file-exceptions.md` and the read-only probe
`docs/dry/temp-tests/dry-file-exceptions/probe_w1.py` (`W1 PROBE: ALL OK`,
63 checks; no source mutation, no Django import, no DB, no shared-tree
pytest). No ruff run owed (no tracked `.py` edits; artifact is `.md`
only; probe is untracked scratch). No `__file__`/DB record (no workspace
copy — no mutating proof exists).

## Independent verification (Worker 2)

Expectation-first trace, derived before reconciling with `## Findings`
(W2 probe: `docs/dry/temp-tests/dry-file-exceptions-w2/probe_w2.py`,
`W2 PROBE: ALL OK`, 71 checks; read-only AST + text census + module load
by path; no Django setup, no DB, no source mutation, no shared-tree
pytest; `HEAD` `9031cb3d`, target blob
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` == `HEAD:` blob, item-baseline
diff empty re-measured by W2).

**Own lattice.** Five classes, one base: `exceptions.py::DjangoStrawberryFrameworkError(Exception)`
with call-time `__str__`/`__repr__` guards; `exceptions.py::ConfigurationError`
and `exceptions.py::OptimizerError` as the two catch families (both extend
only the base — verified `not issubclass(OptimizerError, ConfigurationError)`);
`exceptions.py::PathResolutionError` / `exceptions.py::LookupValidationError`
both extend `ConfigurationError` (definition-time pair, raises solely in
`utils/relations.py`). No raise site lives in the target (zero
`raise ConfigurationError` / `raise OptimizerError`). Owner I would choose
for the lattice: this file (bottom-of-graph verified: sole import is
`__future__.annotations`; zero Django/Strawberry/first-party imports).

**Own renderer ladder.** Eight functions, each one body: kind-name root
`exceptions.py::_safe_type_name` (class contributes its own `__name__`, any
other object its type's; unreadable/non-string/empty fall through to
metaclass label then `"object"`; `str`-subclass names base-stripped);
standalone placeholder `exceptions.py::_unprintable` (single home of the
`<unprintable {T}>` grammar); guarded repr `exceptions.py::_safe_arg_repr`
(base-slot `repr`, else `_unprintable`); guarded str `exceptions.py::_safe_text`
(str-slot read for `str` inputs, guarded `str()` + base-slot re-strip for the
`tp_str`-leak case, empty→`fallback`, raising→`_unprintable`); shared
class-label `exceptions.py::_safe_class_name` (`(value, *, qualified=False)`,
`getattr` for `__name__`/`__qualname__`, base-strip, empty→repr `"''"`,
non-string→guarded repr of the NAME, unreadable→`_safe_type_name`);
owner-fallback readers `exceptions.py::_safe_model_label` (`_meta.label`,
owner fallback) and `exceptions.py::_safe_terminal_label` (`.name`, owner
fallback), each file-local (no importer outside the def site; each called
exactly once, from its typed ctor); fragment tail `exceptions.py::describe_value`
(`{TypeName} {value!r}` collapsing ANY `BaseException` from the f-string to
`an unprintable {T}`). Owners I would choose: this file for all eight
(file-local except the tail, which belongs to the already-indexed
`typed-rejection-value-tail` family owned here).

**Own counts (AST, not assumed).** `describe_value`: 10 importers AND 10
`Call` sites, exactly `consumers.py` (1), `views.py` (1), `routers.py` (6
calls over 5 raises), `error_policy.py` (2), `resource_policy.py` (3),
`extensions/debug.py` (1), `utils/policies.py` (2), `utils/sessions.py` (1),
`schema.py` (5), `list_field.py` (3) — plus the def site = 11 token files.
`_safe_class_name`: 8 importers (`connection.py`, `filters/base.py`,
`forms/inputs.py`, `list_field.py`, `mutations/sets.py`, `orders/base.py`,
`types/finalizer.py`, `types/relay.py`) + def + the strict twin in
`utils/querysets.py` = 10 token files. `_safe_text`: 5 importers
(`forms/inputs.py`, `forms/sets.py`, `types/base.py`, `types/converters.py`,
`utils/errors.py`) + def = 6 token files. `_safe_arg_repr`: 35 AST importers
+ def = 36 token files. `_safe_type_name`: 33 AST importers + def = 34 token
files. `_unprintable`: def + `utils/errors.py` only. Manifest: `__all__`
5 names (`ConfigurationError`, `DjangoStrawberryFrameworkError`,
`LookupValidationError`, `OptimizerError`, `PathResolutionError`);
`describe_value` public-by-name yet absent — unpinned (no star-import
anywhere, no oracle claims the star surface), not a gap.

**Marker base-pair pattern (own).** Exactly two shapes, both owned outside
this file: 1 × `(ConfigurationError, RuntimeError)`
(`utils/querysets.py::SyncMisuseError`, the sync-boundary marker,
re-exported through the root); 2 ×
`(GraphQLError, DjangoStrawberryFrameworkError)` (`list_field.py`,
`resource_policy.py`, wire-visible bound rejections). This file defines
NEITHER pair — it owns only the bases the pairs compose. Any third pair
would be `0 here / 1 at its module`.

**Reconciliation vs W1.** Agreement on every ownership and every census
that matters: 16-module / 6-class-body enumeration, 10 tail consumers by
name, 8 shared-label consumers by name, 5 guarded-str consumers by name,
file-local R1–R8, F1 family reuse, F2–F5 non-membership, J1 rejection with
extension. Three immaterial prose deltas, none blocking: (a) W1 matrix
"36 files import `_safe_arg_repr` / 34 `_safe_type_name`" counts token files
(def included); AST importers are 35 / 33 — convention only, both totals
reproduced exactly; (b) W1 routers shorthand ("3 factory + 1 consumer + 1
application") compresses 6 `Call` nodes over 5 raises (the factory-return
rejection carries two calls: factory + received) — file-level census
unaffected; (c) W1 J1 table cell "factory unreadable → repr (`None`)" is
shorthand for the verified body `return _safe_arg_repr(key)` (guarded repr
of the KEY; the unreadable-`__name__` oracle renders `<class '…'>`, the
hostile-`__repr__` oracle `<unprintable _HostileKey>`) — corrected below,
conclusion unaffected. See rulings.

### Enumeration (Worker 2, member-by-member)

Own instrument: `ast.parse` over the working blob. 16 `ast.Module.body`
members: docstring, `__future__` import, `__all__`, 8 functions, 5 classes.
Class-body members: base 2 (`__str__`, `__repr__`), config 0, path 2
(`__init__`, `__reduce__`), lookup 2 (`__init__`, `__reduce__`), optimizer 0 —
6 total. Every member lands where W1 puts it (R1–R8 + F1 + machinery +
projection); no member unassigned, no second definition missed. The
`### Challenges` C1–C15 each terminate in a family row, a file-local record,
or a recorded rejection — confirmed against the bodies, not sampled.

### Matrix (Worker 2, against the real surface)

1. Cross-flavor: reproduced the raise census exactly — `raise ConfigurationError`
54 files / 523 sites; `raise OptimizerError` 5 modules / 14 sites
(`optimizer/field_meta.py` 3, `optimizer/plans.py` 4,
`optimizer/predicates.py` 3, `types/resolvers.py` 1, `utils/connections.py` 3);
`raise PathResolutionError` 7 + `raise LookupValidationError` 10, all in
`utils/relations.py`; `raise SyncMisuseError` 5 sites in 3 files
(`utils/querysets.py` 3, `utils/execution_mode.py` 1, `list_field.py` 1);
bare `raise GraphQLError` 5 modules (`connection.py`, `filters/base.py`,
`filters/sets.py`, `mutations/resolvers.py`, `relay.py`); scalar
`ValueError`/`TypeError` at the factory/parses. No flavor owns a mirror
taxonomy. Discharged. 2. Twins: zero `AsyncFunctionDef`, zero `Await` in the
target (probe); `located_error` `str()` is color-free and is exactly what the
call-time guards own. Discharged by absence with reason. 3. Derived knowledge:
kind-name once, placeholder once, tail once; model/terminal slots read once
each with no second diagnostic reader; `qualified` derives from one parameter.
The guarded-normalization skeleton recurs with per-site fallback SUBJECTS
(placeholder vs owner name vs metaclass label vs repr) — shared means,
distinct contracts, each oracle-pinned (R6 pair: model fallback names the
model, terminal names the terminal; routing either through `_safe_text` would
print the label type and break those rows). Discharged. 4. Round-trips: no
inverse by contract (lossy one-way collapse); the existing round-trips
(`PathResolutionError.__reduce__`, `LookupValidationError.__reduce__`,
`ResourceLimitExceeded.__reduce__` at its owner) preserve ctor args +
`__dict__`; nothing parses a placeholder. Discharged by absence with reason.
5. Other media: consumers compose by name (AST-verified above);
`tests/test_exceptions.py::test_safe_text_is_single_sourced_across_consumer_modules`
pins import identity (`is`, not equality); oracles spell literals directly
(`"42"`, `"an unprintable …"`, `"<unprintable …>"`) and drive behavior
through construction — never enumerate the owner; projections are the
docstrings (scope paragraph + twin-split clauses, both verified against the
bodies). No oracle rewritten to read the owner it checks. Discharged.
6. Omission: every typed ctor routes hostile-capable inputs through a guarded
renderer (path ctor via `_safe_model_label` + `_safe_arg_repr`; lookup ctor
via `_safe_terminal_label` + `_safe_arg_repr`; base guards via
`_safe_arg_repr` + `_safe_type_name`); the 10 tail consumers cover every raise
whose value arrives from outside the package. Deliberate omissions hold with
contract sources: in-package `got {...}` tails deferred by the scope paragraph
(recorded scope, not a gap); scalar `ValueError` per Strawberry contract;
wire `GraphQLError` per the masking classifier. No member lacks a required
guard. Discharged.

### Counts, roles, oracles (Worker 2)

Definition counts C1–C8/C13 each 1 here; C11/C12 each 0 here + 1 at the pair's
module (bases owned here, pairs owned there — independent, not duplication);
C9 refused on contract (call-time vs sanitize-at-construction pinned by the
stateful-later, args-reassignment, and lazy-locale oracle rows);
C14 1 at the twin, C15 0 (refused — the two oracles diverge by specification).
Roles confirmed: 1 definition (`describe_value` F1; R1–R8 file-local singles;
J1 three definitions of three rules); consumers compose by name (import +
`Call` verified per file above); oracles are independent (literal spellings,
identity `is` gate, hostile/huge-int/`BaseException` rows); projections are
the docstrings + GLOSSARY prose. The finalizer near-twins
(`types/finalizer.py::_safe_qualified_class_name` layers module handling on
top BY CALL to `_safe_class_name(qualified=True)`; `::_safe_field_label`
deliberately runs subclass `__str__`; `::_safe_str` trusts `str()` unless it
raises) compose the shared renderers by name but own simpler finalization-time
contracts — unifying them here would couple the write envelope's leak-proofing
to label plainness. Held distinct, correctly.

### Equivalence (principle 8) + zero-edit

No production edit was made or is owed (file item; item-scoped diff
`git diff be9476561fa0646d952a0bd13baf211af0b2912a --
django_strawberry_framework/exceptions.py` empty, 0 bytes, re-measured by W2;
working blob == `HEAD:` blob `e06b0b7f…`). Observable behavior therefore
identical on every axis (raised types, messages, transaction effects,
cancellation, observation points) — vacuously preserved, with the positive
evidence being the 71-check execution-verified census + functional tails
(printable/hostile/huge-int/`BaseException`, `str`-subclass strip, `"42"`
repr rung) and the static-reviewed oracle bodies. Coverage + assignment
validated (`### Enumeration` complete; every rule in F1 / file-local / checked
non-member / rejection — no candidate left homeless, no production edit
demanded of a file item). No candidate routes to a new family: the R4/R6
near-twin notes name no second definition and live at their owner paragraphs.

### Rulings

**J1 third site — EXTENSION HOLDS (with one cell correction).** Independently
verified bodies: shared `(value, *, qualified=False)` via `getattr`,
empty→`_safe_arg_repr(name)` (`"''"`), non-string→`_safe_arg_repr(name)`
(repr of the NAME), unreadable→`_safe_type_name`, qualified yes; strict twin
`(value)` via `value.__name__`, empty accepted, non-string→`_safe_type_name`
(never reprs the name object), unreadable→`_safe_type_name`, no qualified;
factory twin `(key)` via `getattr(key, "__name__", None)`, empty accepted,
non-string→`_safe_arg_repr(key)` (repr of the KEY), unreadable→same
`_safe_arg_repr(key)` arm (proven by
`tests/test_scalars.py::test_scalar_collision_label_falls_back_when_class_name_metadata_is_unreadable`
rendering `<class '…'>` and
`::test_strawberry_config_collision_message_survives_hostile_key` rendering
`<unprintable _HostileKey>`), no qualified, plus a `sorted()` call-site
needing `__lt__`-safety the message sites never face, inside a factory
`ValueError` (not a framework error at all). Divergence proof: shared oracle
(`tests/types/test_relay_interfaces.py::test_safe_class_name_renders_non_string_metaclass_name_metadata`
→ `"42"`) vs strict oracle
(`tests/utils/test_querysets.py::test_safe_class_name_falls_back_for_non_string_metaclass_name_metadata`
→ metaclass label) DIVERGE by specification — unifying either direction fails
the other's oracle; the factory twin diverges from both on fallback subject
(KEY vs NAME vs TYPENAME) and on the `sorted()` + `ValueError` reasons.
W1's table cell for the factory unreadable arm should read "guarded repr of
the KEY" rather than "repr (`None`)"; the rejection, its triggers, and its
durable homes stand as written.

**Tail Files-covered — PLAN UNDERCOVERS BY 6, W1's 4 FURTHER CONFIRMED.**
The 10-consumer census is proven (import + `Call` per file, counts above).
The plan index row for `typed-rejection-value-tail` lists 5 files
(`exceptions.py`, `consumers.py`, `views.py`, `routers.py`, `error_policy.py`);
the verified population is 11 (def + 10 consumers). The owner's scope paragraph
already names 7 of the 11 (those 5 + `resource_policy.py` +
`extensions/debug.py`); W1 establishes the remaining 4 (`utils/policies.py`,
`utils/sessions.py`, `schema.py`, `list_field.py`). All four satisfy the
scope's forward rule (outside-package values) and each carries 1–5
`describe_value(` `Call` nodes — they are members, not lookalikes. Worker 0
correction is additive-only; no definition count changes either way. Exact row
to write is under `## Exact plan rows for Worker 0`.

### Fingerprints (Worker 2 re-hashes, working tree)

All 25 W1 freshness blobs re-hashed and MATCH the working tree (hence `HEAD`,
the target and all consumer files being clean): `exceptions.py` `e06b0b7f…`,
`consumers.py` `18f3ea16…`, `views.py` `9f85b0df…`, `routers.py` `a18c5001…`,
`error_policy.py` `fa94fcd9…`, `resource_policy.py` `647133d2…`, `schema.py`
`2f727321…`, `list_field.py` `f357eded…`, `utils/policies.py` `860b181f…`,
`utils/sessions.py` `f0d9297c…`, `extensions/debug.py` `bf25c146…`,
`tests/test_exceptions.py` `a87e4872…`, `utils/querysets.py` `1539b66c…`,
`__init__.py` `0ef72601…`, `utils/errors.py` `3e25e93b…`,
`types/converters.py` `9ceb34af…`, `types/finalizer.py` `77fd9a2d…`,
`types/relay.py` `52439862…`, `utils/relations.py` `7662b0bb…`,
`optimizer/field_meta.py` `7215c887…`, `optimizer/plans.py` `cce98531…`,
`optimizer/predicates.py` `4e87c733…`, `utils/connections.py` `f549389e…`,
`types/resolvers.py` `f3341e6a…`, `scalars.py` `5e354042…`. Package
population 117 `.py` files re-counted. `connection.py` concurrent hunk
re-verified: working `3c4d5dcb…` vs `HEAD:` `93e998f2…` touches only the
`from_base64` import + the new offset-cursor guard + fallback branch (hunks at
import/`_consume_window`/`_consume_fallback`); the fingerprinted
`_safe_class_name` site is untouched — attribution as external concurrent work
stands, left alone.

### Negative controls (Worker 2)

F1 gate (owner hostile-tail rows: direct `f"{value!r}"` interpolation raises
`ValueError` instead of `ConfigurationError`): negative control is that same
direct interpolation at any consumer — passes every small-value oracle, fails
exactly the hostile/huge-int rows. J1 mutual controls: shared body fails the
strict oracle (`"42"` vs metaclass label); strict body fails the shared oracle;
factory body fails both (KEY vs NAME subject). Identity gate
(`_safe_text is _safe_text` across `utils/errors.py`/`types/converters.py`):
a hand copy passes behavior oracles, fails the `is` assertion. No bespoke
per-helper existence test was or is owed (gate-only findings need a justified
population, never one test per helper).

### AGENTS.md prose check (Worker 2)

Item-scoped diff is empty (production) + untracked artifact/probe only: no
process provenance, no `feedback.md` mention, no CHANGELOG edit, no commit, no
branch operation, no bulk-delete under `docs/review/`, no `docs/shadow/`
touch, `path::Symbol` citations throughout, no raw `path:NN` in standing
prose (blob ids + probe `§§` only), ASCII-only, no test-tier issue (no tests
added or removed; oracles untouched), no ruff run owed (no tracked `.py`
edits). Concurrent dirt (`connection.py` hunk, `tests/test_connection.py`,
staged `tests/utils/test_querysets.py` +31, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`, sibling `dry-file-*.md` artifacts) never edited,
reverted, or tidied. Violation: none — not `revision-needed` on prose.

### Scratch (Worker 2)

Read-only, no workspace copy owed (no mutating proof exists; probe configures
no Django, opens no DB): `docs/dry/temp-tests/dry-file-exceptions-w2/probe_w2.py`
(`W2 PROBE: ALL OK`, 71 checks). No shared-tree pytest ran. No `__file__`/DB
`NAME` record applies. `FAKESHOP_SHARDED=1` / Postgres cells: `inapplicable by
construction` (pure total renderers + exception construction; no database,
alias, or dialect decision reachable) — W1's reason judged sound.

### Exact plan rows for Worker 0

Additive-only; no status or owner changes:

1. `## Responsibility index` row `typed-rejection-value-tail` — replace Files
covered `exceptions.py`, `consumers.py`, `views.py`, `routers.py`,
`error_policy.py` with the full 11-file list: `exceptions.py`,
`consumers.py`, `views.py`, `routers.py`, `error_policy.py`,
`resource_policy.py`, `extensions/debug.py`, `utils/policies.py`,
`utils/sessions.py`, `schema.py`, `list_field.py`.
2. `## Responsibility index` hostile-`_safe_class_name` REJECTED row — append
`scalars.py` to Files covered (`utils/querysets.py`, `exceptions.py` →
`utils/querysets.py`, `exceptions.py`, `scalars.py`); durable homes stay as
W1 records (split clause in `exceptions.py::_safe_class_name` docstring +
`STRICTER` clause in `utils/querysets.py::_safe_class_name` docstring + factory
parity note verified as its file item's own).

### Judgment (Worker 2)

Backstop discharged independently (16/16 + 6/6, 15 challenges confirmed,
matrix re-derived against the real surface, 10-consumer census proven import +
call per file, J1 extension proven with divergence oracles, all fingerprints
re-hashed green, no oracle rewritten, no pending execution, prose clean).
Zero-edit stands. Verdict: **verified**.

## Defects (Worker 2)

None. Every claim checked while tracing held (bottom-of-graph import census;
lattice bases + non-subclassing; args-identity + laziness + stateful-later +
`BaseException`-swallow; both typed-ctor hostile-metadata rows;
pickle/copy/deepcopy shape; single-sourcing `is` identity; all 10 consumer
import/use sites with per-file `Call` counts; twin docstring clauses matching
their bodies; dual-marker census 1 + 2 with no pair defined here; raise-site
census 54 / 14-in-5 / 7+10 / 5-in-3 / bare-5 / scalar-`ValueError`). The J1
"repr (`None`)" cell and the 36/34-vs-35/33 import-count phrasing above are
artifact shorthand recorded under `## Independent verification (Worker 2)`,
not production defects, and change no owner, count, or trigger. Nothing routed
to any owner.

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
## Bounded re-review at bfaee91d (Worker 2, Q5)

Scope: exception-vocabulary freshness after deltas in interacting files. HEAD `bfaee91d` bytes throughout; base `9031cb3d` for delta establishment. Target `django_strawberry_framework/exceptions.py` whole file (HEAD bytes; clean -- confirmed). Deltas: (a) `django_strawberry_framework/list_field.py` determinism classifiers plus guard tables, diff `9031cb3d..bfaee91d`, current bodies read at HEAD; (b) `django_strawberry_framework/utils/querysets.py` READ-ONLY (HEAD bytes read, never edited); (c) `django_strawberry_framework/consumers.py` plus `django_strawberry_framework/schema.py` deltas confirmed outside vocabulary behavior. Method: HEAD `git show` reads, `9031cb3d..bfaee91d` diffs, AST `Raise` census over classifier and new-method bodies, import census via `git grep` at HEAD, oracle reads of `tests/test_exceptions.py` and seal/determinism-adjacent tests. Zero source edits. This section is the sole artifact write for this phase; no prior section was opened.

### (1) Exception vocabulary at HEAD with raisers per class

`django_strawberry_framework/exceptions.py` defines five exception classes (`__all__` lists exactly these five) plus eight message-rendering helpers. No other exception class is defined in this file.

- `django_strawberry_framework/exceptions.py::DjangoStrawberryFrameworkError`: package base, subclasses `Exception`. Never raised directly (no `raise DjangoStrawberryFrameworkError` site in package source at HEAD). Caught as the single-catch base. Subclassed by `ConfigurationError`, `OptimizerError`, and by transport shapes defined elsewhere (`django_strawberry_framework/list_field.py::ListArgumentError` which is `GraphQLError` plus this base; `django_strawberry_framework/resource_policy.py::ResourceLimitExceeded` same shape). Its `__str__` / `__repr__` overrides are the call-time safe renderers.
- `django_strawberry_framework/exceptions.py::ConfigurationError`: subclasses the base. The configuration/definition family. Raised from many modules, including `django_strawberry_framework/auth/mutations.py`, `django_strawberry_framework/auth/sessions.py`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/list_field.py` (config validation and visibility/seal call sites, never inside the determinism classifiers), `django_strawberry_framework/utils/querysets.py` (seal call sites listed below), `django_strawberry_framework/schema.py` (construction-time validation), `django_strawberry_framework/routers.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/error_policy.py`, and related surface wiring. Catchable through the base.
- `django_strawberry_framework/exceptions.py::PathResolutionError`: subclasses `ConfigurationError`. Strict path-classification error carrying `model`, `field_path`, `segment`. Raised only from `django_strawberry_framework/utils/relations.py::classify_path` (segment rejected by `Model._meta.get_field`, non-relation non-terminal segment, forward `GenericForeignKey` segment, empty `path_infos` relation segment). Consumed (caught) in `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/orders/sets.py`, and the lenient walk in `django_strawberry_framework/utils/relations.py::path_traverses_to_many` / related fallback which answers `False` on this error.
- `django_strawberry_framework/exceptions.py::LookupValidationError`: subclasses `ConfigurationError`. Lookup-expression error carrying `terminal`, `lookup_expr`, `part`. Raised only from `django_strawberry_framework/utils/relations.py::validate_lookup_expr` (empty expression, empty split part, non-final part with no transform, final part with neither lookup nor trailing-transform-under-implicit-exact).
- `django_strawberry_framework/exceptions.py::OptimizerError`: subclasses the base directly, deliberately not `ConfigurationError`. Planner/traversal failure. Raised from `django_strawberry_framework/optimizer/field_meta.py::FieldMeta.from_django_field` (non-field descriptor stamp guard), `django_strawberry_framework/optimizer/plans.py::window_partition_for_prefetch` (non-windowable join kind / unresolvable parent partition), `django_strawberry_framework/optimizer/plans.py::apply_window_pagination` (reversed keyset-seek window), `django_strawberry_framework/optimizer/predicates.py::attach_exists` (three caller-contract guards: inner/outer model mismatch, alias mismatch, outer combinator), `django_strawberry_framework/types/resolvers.py` (strictness-`raise` unplanned N+1 list-relation guard), `django_strawberry_framework/utils/connections.py::window_range_plan` (negative offset/limit) and `django_strawberry_framework/utils/connections.py::assert_window_fetch_mode` (count-free probe plus partition-count annotation).
- Factories / renderers defined in `exceptions.py` (not exception classes, not raised; called while assembling messages): `django_strawberry_framework/exceptions.py::describe_value` (shared `got <type> <repr>` tail renderer for transport-boundary and schema-construction policy rejections; callers include `django_strawberry_framework/consumers.py`, `django_strawberry_framework/routers.py`, `django_strawberry_framework/schema.py`, `django_strawberry_framework/error_policy.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/extensions/debug.py`, `django_strawberry_framework/list_field.py`), `django_strawberry_framework/exceptions.py::_safe_type_name`, `django_strawberry_framework/exceptions.py::_unprintable`, `django_strawberry_framework/exceptions.py::_safe_arg_repr`, `django_strawberry_framework/exceptions.py::_safe_text`, `django_strawberry_framework/exceptions.py::_safe_class_name`, `django_strawberry_framework/exceptions.py::_safe_model_label`, `django_strawberry_framework/exceptions.py::_safe_terminal_label`.
- Adjacent exceptions NOT defined in `exceptions.py` (named to prevent miscount): `django_strawberry_framework/utils/querysets.py::SyncMisuseError` (defined in `querysets.py`, multiple-inherits `ConfigurationError` plus `RuntimeError`, re-exported at package root; raise sites in `querysets.py` and `list_field.py` and `utils/execution_mode.py`); `django_strawberry_framework/list_field.py::ListArgumentError` (defined in `list_field.py`, `GraphQLError` plus base; raise sites only in `list_field.py` outside the classifiers); `django_strawberry_framework/resource_policy.py::ResourceLimitExceeded` (defined in `resource_policy.py`).

Oracles read: `tests/test_exceptions.py` pins the lattice (`ConfigurationError` and `OptimizerError` under base; `PathResolutionError` and `LookupValidationError` under `ConfigurationError`; `SyncMisuseError` under `ConfigurationError`, base, and `RuntimeError`; `OptimizerError` not under `ConfigurationError`), `.args` identity, call-time render guards, pickle/copy fidelity, `located_error` type preservation, and the `describe_value` / `_safe_*` contracts.

### (2) Changed regions exception references

- List-field determinism classifiers (HEAD bodies read in full): `django_strawberry_framework/list_field.py::_resolve_order_field_path`, `django_strawberry_framework/list_field.py::_is_deterministic_order_field_path`, `django_strawberry_framework/list_field.py::_is_deterministic_order_reference`, `django_strawberry_framework/list_field.py::_is_deterministic_order_name`, `django_strawberry_framework/list_field.py::_is_deterministic_order_term`, `django_strawberry_framework/list_field.py::_is_deterministic_order_value`, `django_strawberry_framework/list_field.py::_approved_order_transform`, `django_strawberry_framework/list_field.py::_is_deterministic_order_lookup_chain`, `django_strawberry_framework/list_field.py::_is_deterministic_order_predicate_reference`, `django_strawberry_framework/list_field.py::_is_deterministic_order_condition`. AST census: zero `Raise` nodes in all ten bodies; zero imports in all ten bodies. The only `raise` tokens in that line span are two docstring prose occurrences (`certify` / `FieldError` discussion), not code. The classifiers return `bool` and refuse unreadable terms with `False`. Module-level `exceptions.py` imports (`ConfigurationError`, `DjangoStrawberryFrameworkError`, `_safe_arg_repr`, `_safe_class_name`, `_safe_type_name`, `describe_value`) plus `SyncMisuseError` exist at the top of `list_field.py` but no classifier body references any of them. New guard tables in the delta (`_READABLE_ORDER_LEAVES` as `frozenset`, `_TRANSPARENT_ORDER_EXPRESSIONS`, `_APPROVED_ORDER_FUNCTIONS`, `_APPROVED_ORDER_AGGREGATES`, `_APPROVED_ORDER_TRANSFORMS`, `_APPROVED_ORDER_LOOKUPS`, `_APPROVED_ORDER_NODES`) are pure membership sets; no exception reference. `ListArgumentError` raise-site count in the `9031cb3d..bfaee91d` diff for `list_field.py` is zero (class and all raise sites unchanged).
- Seal paths (HEAD bytes, READ-ONLY): deleted wording arms are five dict entries passed to `django_strawberry_framework/utils/querysets.py::_defect_message` -- one `combined` arm in `django_strawberry_framework/utils/querysets.py::_raw_list_source_message`, one `evaluated` plus one `routing` arm in `django_strawberry_framework/utils/querysets.py::_visibility_result_error`, one `evaluated` plus one `routing` arm in `django_strawberry_framework/utils/querysets.py::_prepared_visibility_source` -- plus one retired seal-policy symbol `django_strawberry_framework/utils/querysets.py::_UNRECOMPOSED_CHILD_POLICY` (a `_SealPolicy` instance, not an exception). No deleted arm was itself a `raise`; each site still raises the same `ConfigurationError` wrapper around `_defect_message`, whose exhaustive fallback for unrendered codes is unchanged, so an unlisted code still fail-closes with the framework-defect wording. `SyncMisuseError` definition and its `querysets.py` raise sites are untouched by the delta. `_SealPolicy` / `_DEFAULT_SEAL_POLICY` / `_CASCADE_SEAL_POLICY` / `_PREFETCH_CHILD_POLICY` / `_LIST_ARGUMENT_VISIBILITY_POLICY` / `_RAW_LIST_SOURCE_POLICY` remain; the retired child policy is superseded by `_PREFETCH_CHILD_POLICY` (`reject_sliced=False` plus `require_shared_alias=True`) at the prefetch-child call site.
- `django_strawberry_framework/consumers.py`: delta is docstring-only (two prose hunks: hook-exception masking now names `django_strawberry_framework/schema.py::DjangoSchema._masked_return`; `is_maskable_result` gate phrasing). Confirmed by `9031cb3d..bfaee91d` diff showing only `-`/`+` comment lines and zero added `raise` / `class` / `import` lines, plus HEAD grep showing the module still imports `ConfigurationError` and `describe_value` only for the untouched `::_unusable_window_error` path.
- `django_strawberry_framework/schema.py`: delta is one import expansion (`degraded_result`, `is_maskable_result`, `mask_execution_result`, `masking_is_active` from `extensions/error_policy.py`) plus three new methods `django_strawberry_framework/schema.py::DjangoSchema.execute_sync`, `django_strawberry_framework/schema.py::DjangoSchema.execute`, `django_strawberry_framework/schema.py::DjangoSchema._masked_return`. Confirmed outside vocabulary behavior by diff plus AST: zero `Raise` nodes in all three new bodies; zero new exception classes; zero added `raise ConfigurationError`; zero `describe_value` message rewords. The new seam delegates gates and wording to `extensions/error_policy.py` by name, returns early on non-active / non-maskable results, and fail-closes any gate failure to `degraded_result` with a `logger.exception` (catches `Exception`, raises nothing).
- Import census at HEAD: `list_field.py` imports `ConfigurationError`, `DjangoStrawberryFrameworkError`, `_safe_arg_repr`, `_safe_class_name`, `_safe_type_name`, `describe_value`, `SyncMisuseError`; `utils/querysets.py` imports `ConfigurationError`, `_safe_arg_repr`, `_safe_type_name` and defines `SyncMisuseError`; `consumers.py` and `schema.py` each import `ConfigurationError` plus `describe_value`. No classifier or seal-deleted arm adds or removes an `exceptions.py` import.

### (3) Definition counts

- New exception definitions in scope: zero. No new `ClassDef` in `exceptions.py` (file byte-identical across `9031cb3d..bfaee91d`); no new exception class in any delta (`ListArgumentError`, `SyncMisuseError`, `ResourceLimitExceeded` all pre-date the range and are unchanged; `schema.py` adds methods only; `querysets.py` retires a policy instance, not a class).
- Reworded messages in `exceptions.py`: zero (same byte-identity fact).
- Non-vocabulary wording movement noted separately and not counted as exception definitions: five deleted unreachable seal dict arms plus one retired policy symbol (counts above); expanded classifier docstrings; two `consumers.py` docstring sentences; `schema.py` new masking docstrings plus one new fail-closed log line owned by the `extensions/error_policy.py` seam.

### (4) Owners I would choose (DRY principle 7; principle 2 where noted)

- Exception lattice plus safe renderers plus `describe_value`: `django_strawberry_framework/exceptions.py`. Responsibility is package-wide typed-failure identity plus never-raising message assembly; the module sits at the bottom of the import graph (no Django, no Strawberry, no internal package imports) so every legitimate consumer can depend on it without reversing a dependency. This matches the module docstring contract.
- Determinism classifiers plus approved-form tables: `django_strawberry_framework/list_field.py`. Responsibility is offset-window repeatability (whether one ordering reads down to columns/literals); the decision mirrors `SQLCompiler` / `Query` resolution internals and has no second consumer. Tables stay beside the predicates that read them.
- Seal policies plus per-surface wording: `django_strawberry_framework/utils/querysets.py`. Each message function (`_raw_list_source_message`, `_visibility_result_error`, `_prepared_visibility_source`) owns its own prose per the `::_defect_message` docstring (shared dispatch and exhaustiveness only, never shared wording -- principle 2 applied to dispatch, not to prose). `_SealPolicy` owns the option set; `_defect_message` owns the closed-code fallback.
- `SyncMisuseError`: `django_strawberry_framework/utils/querysets.py` (narrowest cohesive owner with the sync-boundary execution responsibility; the dual `ConfigurationError` plus `RuntimeError` catch contract is documented at the class and in `exceptions.py` prose).
- `ListArgumentError`: `django_strawberry_framework/list_field.py` (wire reason vocabulary owned by the list surface; base catchability composed by name through `DjangoStrawberryFrameworkError`).
- Masking seam: `django_strawberry_framework/extensions/error_policy.py` owns masking implementation, gates, and wording; `django_strawberry_framework/schema.py::DjangoSchema._masked_return` and the `consumers.py` stream seam are consumers by name (principle 6), not second definitions.
- Path/lookup error classes: `exceptions.py` owns the types; `django_strawberry_framework/utils/relations.py::classify_path` and `django_strawberry_framework/utils/relations.py::validate_lookup_expr` own their respective raise sites as the classifying authorities.

### (5) Whether any delta breaks anything derived

No breakage derived in this trace; no defect entry is made here. `exceptions.py` is unchanged and clean, the classifiers raise nothing and reference no `exceptions.py` symbol, the seal deletions remove only unreachable wording arms behind an unchanged exhaustive fail-closed dispatch and retire a duplicated child-policy licence now covered by `_PREFETCH_CHILD_POLICY`, the `consumers.py` delta is prose-only, and the `schema.py` delta adds a delegating, fail-closed masking seam that raises nothing and rewords no `exceptions.py` message. Under the GOAL trust boundary (a defect must name the contract row it breaks, a feasible project shape under supported public API, and the wire or configuration input that reaches it) and DRY principles 2/7, there is no contract row plus reaching input to name: consumers catching `DjangoStrawberryFrameworkError`, `ConfigurationError` (including `SyncMisuseError`, `PathResolutionError`, `LookupValidationError` through it), `OptimizerError`, `ListArgumentError`, or `ResourceLimitExceeded` through the base see an identical lattice, identical construction signatures, and identical catchability before and after the range, and no wire/config input reaches a changed raise because no reachable raise was added, removed, or reworded. No status is set and no verdict on prior findings is proposed in this phase.

### (6) Freshness fingerprints (HEAD `bfaee91d` unless noted)

- `django_strawberry_framework/exceptions.py`: HEAD `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`, worktree `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` (clean; `git diff HEAD` empty; absent from `git status --short`). Base `9031cb3d` blob identical `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` (vocabulary bytes unchanged across the range).
- `django_strawberry_framework/list_field.py`: HEAD `ce682d5f79518919ff3676f2fc8bbe2bd33995a4`; base `9031cb3d` blob `f357eded3d96fcffe17e6fd84bceb8cd12af98d5`; worktree `d6af61646784deac2f3053bb4096b8599deae2f5` (dirty, concurrent: `git diff HEAD` is one `+8` docstring hunk in `::_validate_relay_djangotype_target` outside the classifiers and outside vocabulary behavior; preserved, not reverted).
- `django_strawberry_framework/utils/querysets.py`: HEAD `96618fba4eafb6a87e73414770014e3aee5b41ef`, worktree identical (clean; READ-ONLY, never edited). Base `9031cb3d` blob `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`.
- `django_strawberry_framework/consumers.py`: HEAD `936210e2993ddca4b77ffebf65e728f59d17079c`, worktree identical (clean).
- `django_strawberry_framework/schema.py`: HEAD `c2e1b748c26c31d944f5a7a12e45b399c81f7ea5`, worktree identical (clean).
- `django_strawberry_framework/utils/relations.py` (raise-site owner): HEAD `7662b0bb669c4dfba4a437f3b8f309357f718dca`.
- Oracles read: `tests/test_exceptions.py` HEAD `de4d3bdfc65efdb63b5d7adc9cf2e659911a500c` (worktree clean); `tests/utils/test_querysets.py` HEAD `977a81df44b5cede99b2be9b8dcc5be76db0f03a` (worktree has staged concurrent modification, preserved); `tests/test_list_field.py` HEAD `2f77f77d67366373390458c681e33fd59cf42c92` (worktree clean for the inspected range).
- Contract sources: `GOAL.md` HEAD `7dfbef5c784519d5f95311aaeb8c6766ee966b02`; `docs/dry/DRY.md` HEAD `e8151123ff7e129fe9881ec342231e9e1795148e`; `docs/dry/worker-2.md` HEAD `4f089ea4a58d73295638e83abf8c612bf31487f8`; `AGENTS.md` HEAD `e42247fa310bf7a85914d7efa7f177ee5307b860`.
- Diffs established from `9031cb3d..bfaee91d` for `list_field.py`, `utils/querysets.py`, `consumers.py`, `schema.py` (stat plus full hunk reads for the named regions); classifier and new-method bodies additionally verified by AST `Raise`/import census at HEAD bytes.

PHASE-1-TRACE-RECORDED -- artifact `docs/dry/dry-file-exceptions.md`
