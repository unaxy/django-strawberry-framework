# DRY review: `utils/permissions.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/permissions.py` is the neutral
permission mechanics module: request-identity resolution from
`info.context` (`request_from_info` + the Channels adapter), the
write-pipeline auth-alias derivation (`resolve_auth_aliases` +
`auth_aliases_for_permission_classes`), and the shared FilterSet /
OrderSet active-input gate walk (`run_active_input_permission_checks` +
its classifiers, gate dispatch, and flat-path parity walk).

Dirt attribution (all 14 hunks, by content — no ledger row names this
file; the [plan][plan] `## Owned changes` ledger was read whole and
covers other paths only): hunks `@@ -34` (import swap
`_safe_*` → `truth`), `@@ -47` (import tail + `lazy`), `@@ -118`
(`_scope_value`), `@@ -143` (`_channels_scope` + `_context_request`
tuple → plain), `@@ -195` (adapter call-site), `@@ -205` (new
`_is_request` + `_request_from_context`), `@@ -252`
(`request_from_info` context read), `@@ -265` (`request_from_info`
message), `@@ -274` (`_safe_get_model`), `@@ -331`
(`auth_aliases_...`), `@@ -394` (`invoke_permission_method`),
`@@ -604` (flat-walk `field_name` read), `@@ -633` (flat-walk
`child_set` check), `@@ -649` (`_related_declarations`) uniformly
replace `isinstance` →
`truth.is_instance`, `_safe_type_name` → `truth.kind` /
`truth.name`, `_safe_arg_repr` → `truth.render`, add the
`lazy.unwrap_lazy_object` request check, and delete every
`try/except BaseException` containment plus the readability-flag
protocol. That is the concurrent truthful-reads migration (untracked
`utils/truth.py`, `utils/lazy.py`), pre-baseline: the item baseline
already carries the worktree bytes (`361255a5:path` = `1c9cfd39` =
worktree; `git diff ITEM_BASELINE -- <target>` is empty), so the
item-scoped diff holds zero hunks I did not make and every
HEAD-vs-worktree hunk is concurrent-external. Per dispatch all bytes
traced below are HEAD bytes (`9889d6fe`, 767 lines); the worktree
state (`1c9cfd39`, 715 lines) is fingerprinted, never traced. Nothing
tracked was touched. HEAD is `0c0537e2`, unmoved since dispatch.

Production consumer census at HEAD bytes (every import statement read):

- `sets_mixins.py` composes 7 names (the whole walk surface +
  `request_from_info`) behind the `ActiveInputPermissionMixin` thin
  delegates both set families inherit.
- `mutations/permissions.py` composes `request_from_info`
  (`DjangoModelPermission.has_permission`, `family_label="DjangoMutation"`).
- `mutations/resolvers.py` composes `auth_aliases_for_permission_classes`
  (the one authorization-phase call site).
- `rest_framework/resolvers.py` composes `request_from_info`
  (`family_label="SerializerMutation"`).
- `auth/mutations.py` + `auth/queries.py` compose `request_from_info`
  (`family_label="AuthMutation"`); `auth/sessions.py` composes
  `ChannelsRequestAdapter` (the `isinstance` classification seam).
- `filters/sets.py` does NOT import from this module (it reads the
  walker through the mixin and `iter_input_items` from `input_values`
  directly — O1); the re-export's only in-repo consumer via this path
  is the test suite.

Oracles: `tests/utils/test_permissions.py` (HEAD `abf30ad3`, 1293
lines, 52 tests; independent literals — hostile-mapping pins,
gate-firing pins, flat-parity pins). Live wire rows in
`examples/fakeshop/test_query/test_products_api.py` (flat must not
bypass `:2108`, terminal-gate chain `:2132`, order gate `:2399`) and
`test_library_api.py` / `test_kanban_api.py` (gate-firing rows).
Projections: the module docstrings, the glossary `request_from_info` /
Channels-request-adapter anchors, the family wrapper docstrings.

## Verification

### Enumeration

Instrument: `ast.Module.body` over HEAD bytes (`git show
HEAD:django_strawberry_framework/utils/permissions.py`), 32 members: 1
docstring + 10 imports + 2 assigns + 1 class + 18 functions. All 21
named definitions homed (class methods ride the class row):

| # | Symbol | Home |
|---|---|---|
| 1 | `_GATE_ASYNC_RECOURSE` | FL3 + R1 (wording twin distinguished) |
| 2 | `_check_method_name` | FL3 (name grammar) |
| 3 | `__all__` (+ re-export comment) | FL6 + O1 (stale consumer name) |
| 4 | `ChannelsRequestAdapter` (+6 methods) | FL1 (Channels identity) |
| 5 | `_channels_scope` | FL1 |
| 6 | `_context_request` | FL1 + D2 (docstring over-claim) |
| 7 | `_channels_request_adapter` | FL1 |
| 8 | `_request_from_context` | FL1 |
| 9 | `request_from_info` | FL1 + R4 (converge, context R2) |
| 10 | `_safe_get_model` | FL2 + R5 (relay twin distinguished) |
| 11 | `resolve_auth_aliases` | FL2 |
| 12 | `auth_aliases_for_permission_classes` | FL2 |
| 13 | `extract_branch_value` | FL4 |
| 14 | `invoke_permission_method` | FL3 + F-AWAIT (consumer) |
| 15 | `verbatim_path` | FL4 |
| 16 | `active_permission_targets` | FL4 |
| 17 | `active_related_branches` | FL4 |
| 18 | `_fire_gate_on_class` | FL3 |
| 19 | `_fire_flat_relation_path_gates` | FL5 |
| 20 | `_related_declarations` | FL5 + F-FA (dict arm) + R3 (else arm) + D1 (docstring over-claim) |
| 21 | `run_active_input_permission_checks` | FL4 |
| 22 | Module mechanics (docstring, 10 imports) | FL6 |

### Matrix

1. **Cross-flavor mirroring** — searched. Both set families drive the
   one walk through mixin delegates (no twin bodies); mutation /
   serializer / auth compose `request_from_info` with per-family
   labels. The recourse wording twin is distinguished (R1), the
   label-split twin is distinguished (R8). No mirrored rule.
2. **Sync/async twins** — searched, none in target. The target is
   sync-only (zero `await` expressions); both async surfaces wrap the sync walk in
   `run_in_one_sync_boundary` (`orders/sets.py:831`,
   `filters/sets.py:3497` via `_apply_common_finalize`). The
   sync/async SEAM (async-gate refusal) composes the family owner by
   name (F-AWAIT).
3. **Derived rather than repeated** — searched. Gate names derive once
   (`_check_method_name` over composed `flatten_lookup_path`); auth
   aliases derive once (router answers per model); scope/request reads
   compose `Mapping.get` / `getattr` at one site each. No re-derivation.
4. **Inverse / round-trip pairs** — searched, none. The flat-walk /
   nested-recursion gate parity is a same-direction contract (FL5),
   not an inverse; no grammar is parsed back out of a rendered form.
5. **Contracts in another medium** — searched. Oracles (above) spell
   every verdict independently; module/family docstrings, glossary
   anchors, and live wire rows are projections. A contract change
   moves 1 definition + its oracles (listed, never counted). Three
   projection sentences over-claim their bodies (D1, D2, O1).
6. **Enforcement by omission** — searched, family enumerated. Gate
   firing covers leaves + related branches + flat parity + filter
   logic (family hook); the async-guard covers the gate seam; the
   auth-alias gate covers write pipelines carrying permission
   classes; request resolution covers all four consumer families. No
   gap established against a contract source; the object-context
   pass-through arm fails closed downstream (FL1). No defect.

### Challenges

- C1 (new context shape): moves 1 ladder (FL1; 9 end paths follow).
- C2 (miss-message wording): moves 1 (`request_from_info`; labels are
  per-caller data). FL1.
- C3 (third Channels scope shape): moves 1 (`_channels_scope`). FL1.
- C4 (fifth auth model): moves 1 (the candidates list). FL2.
- C5 (alias rule): moves 1 (the router-answer set). FL2.
- C6 (gate-name grammar): moves 1 (`_check_method_name`; the lookup
  flatten is composed). FL3.
- C7 (gate-slot verdicts): None-vs-absent-vs-non-callable-vs-async
  moves 1 (`invoke_permission_method`); the async mechanism is
  composed (F-AWAIT). FL3.
- C8 (gate recourse reword): moves 1 constant; the mutation twin
  does NOT move (four clauses differ). R1.
- C9 (walk partition): moves 1 (`active_permission_targets`;
  `active_related_branches` delegates to it). FL4.
- C10 (flat hop matching): a new hop kind moves 1 (the flat walk;
  the nested recursion is generic over declarations). FL5.
- C11 (declaration proof): "must be `dict`" moves 1 (the shared
  front half; this tail adapts — R3's trigger). FL5.
- C12 (unbound-dict enumeration): moves with the family owner
  (F-FA converge).
- C13 (non-dict declaration enumeration): moves 1 (the else arm;
  no base slot exists). R3.
- C14 (Mapping.get threat coverage): moves the 2 reads, never FA
  (half-strength: `__getitem__` still dispatches). R2 + D2.
- C15 (containment removal): moves all 10 per-site `BaseException`
  guards (per-site detail, no shared driver). R6.
- C16 (label-split strictness): moves 1 per subject (tolerant
  partition vs fail-loud split). R8.
- C17 (re-export removal): moves 1 (`__all__` + comment); the keep
  decision is recorded at `filters/sets.py::_iter_input_items`. FL6 + O1.

## Findings

### F-AWAIT — Awaitable refusal (CONVERGE into open `awaitable-refusal-and-disposal` as consumer)

`invoke_permission_method` is the file's only awaitable seam and it
already composes the family mechanism by name:
`reject_async_in_sync_context(method(request), ...)` (`:422-428`),
which closes/cancels through the family owner
`utils/querysets.py::_dispose_sync_awaitable`. Census: exactly 1
`reject_async` call site, zero inline close/cancel spellings in this
file. No definition here, nothing to adopt, no consolidation owed —
the holding family item inherits a consumer, not a member.

Freshness: target HEAD `9889d6fe`; `querysets.py` HEAD `3616927d`.

### F-FA — Unbound dict enumeration (CONVERGE the `:672` dict arm into open `base-slot-container-reads`)

`:672` `dict.items(related)` reads a consumer container through the
unbound iteration slot so a subclass override cannot decide what the
authorization walk sees — FA's contract verbatim, the same arm shape
as the already-converged `input_values.py:91`. The eager/streaming
axis FA flagged does not split here (the read always materializes to
a tuple). The else arm and the `Mapping.get` reads are distinguished
at R2/R3, not converged.

Freshness: target HEAD `9889d6fe`; `canonical.py` HEAD `b9ded33b`;
`input_values.py` HEAD `f2566609`.

### FL1 — Request-identity resolution ladder (file-local)

`request_from_info` (family-labelled miss errors) +
`_request_from_context` (mapping/object fork) + `_context_request`
(the Mapping-vs-attribute read, once, with the readability flag) +
`_channels_request_adapter` + `_channels_scope` +
`ChannelsRequestAdapter` (user/session/scope + `__getattr__`
delegation). One ladder: 9 end paths across 4 families
compose it by name (C1, C2, C3). The mapping arm's "unreadable means
no request" vs the object arm's fall-through (including the
non-request pass-through) is one deliberately asymmetric rule with
its ordering documented at the read; downstream callers fail closed
(mutations read `user` → `None` → deny; gates receive the value and
error, never allow).

### FL2 — Auth-alias derivation (file-local)

`resolve_auth_aliases` (router answers over the user + Permission +
Group + ContentType candidate set) + `_safe_get_model` (fail-soft
skip) + `auth_aliases_for_permission_classes` (empty-classes gate).
One derivation, one production caller (C4, C5). The relay
`apps.get_model` twin is distinguished at R5.

### FL3 — Gate dispatch (file-local)

`invoke_permission_method` (dedup set + slot read + non-callable
refusal + async-guard composition) + `_check_method_name`
(`lru_cache`d grammar over composed `flatten_lookup_path`) +
`_fire_gate_on_class` (bare-instance + per-class set) +
`_GATE_ASYNC_RECOURSE` (the wording). One dispatch: every gate fire
in both families routes through it (C6, C7). The async mechanism is
F-AWAIT's; the wording twin is R1's.

### FL4 — Walk orchestration (file-local)

`run_active_input_permission_checks` (gate loop + related recursion
with the shared depth budget via composed
`assert_set_traversal_depth`) + `active_permission_targets`
(single-pass leaf/branch partition) +
`active_related_branches` (thin delegate) + `extract_branch_value`
(inactive-collapse over composed `input_field_value` /
`is_inactive_value`) + `verbatim_path` (shared identity fallback).
One orchestration: the partition is single-pass by construction
(C9); both families' recursion re-enters the one body.

### FL5 — Flat-path gate parity (file-local)

`_fire_flat_relation_path_gates` (longest-match hop walk firing the
nested twin's gate chain) + `_related_declarations` (shared front
half + authorization tail). One parity contract, live-pinned
(`test_products_api.py:2108`, `:2132`): a flat leaf fires the same
gates as its nested spelling (C10, C11). The `:672` dict arm rides
F-FA; the else arm is R3.

### FL6 — Module mechanics (file-local)

Charter docstring (accurate against every body read — the two
over-claiming sentences are D1/D2, not charter drift), 10 imports
(no family package — the cycle-free contract holds), 11-name
`__all__` with the `iter_input_items` compat re-export (C17, O1).

### R1 — Gate recourse vs mutation recourse (rejected)

`_GATE_ASYNC_RECOURSE` vs
`mutations/permissions.py::_PERMISSION_ASYNC_RECOURSE` — CONVERGE
with the rejected `sync-boundary-recourse-wording` direction on
fresh evidence: both owner prose (the `sync_pipeline_recourse`
docstring declines these two; the mutation comment counts four
differing clauses) re-read verbatim at HEAD, and C8 confirms a
template would pin nothing. Trigger: either wording generalized to
the other's subject.

### R2 — `Mapping.get` reads vs FA (rejected)

`_scope_value` (`Mapping.get(self._scope, key)`) and
`_context_request` (`Mapping.get(context, "request")`) are
half-strength: the unbound call defeats a `get` override, but the
slot's own body is `return self[key]` (CPython
`collections.abc` source read verbatim), so a `__getitem__`
override still runs and decides the read — FA's contract ("never
through the instance's overridable attribute") fails. Different
threat coverage, not a missed merge (C14). Trigger: the family
item ruling half-strength lookup in, or the reads hardening past
`Mapping.get`.

### R3 — Non-dict fallback vs FA (rejected)

`:672` else arm (`related.items()` for non-dict mappings) has no
base slot to read through — arbitrary `Mapping` offers no unbound
`items` — CONVERGE with the `input_values.py` R4 direction (same
"no base slot" line, same trigger). The code shape is correct;
only the prose over-claims (D1). Trigger: related declarations
constrained to `dict`.

### R4 — Request identity vs key storage (rejected)

CONVERGE with verified `request-context-vs-request-identity-decode`
(File `utils/context.py` R2) on fresh evidence: this file resolves
request IDENTITY from `info` (fail-loud, family-labelled); that
module stores opaque KEYS on a resolved context (fail-closed,
info-agnostic). Opposite failure postures on both bodies re-read.
Trigger: the standing trigger (a spec unifying resolution with
key storage).

### R5 — Fail-soft model read vs relay decode (rejected)

`_safe_get_model` (skip uninstalled: `None`) vs
`types/relay.py::decode_global_id` (fail-loud `ConfigurationError`
on `LookupError`): same stdlib call, opposite postures for
opposite subjects (deployment-optional auth models vs a
client-supplied GlobalID that must resolve). C16-adjacent; no
shared helper relieves either change. Trigger: either side
changing posture.

### R6 — Standing guard triggers re-checked (rejected)

J1 (shared `except` driver): 10 `BaseException` guards, each
translating with per-site wording — CONVERGE with `_request_body`
J1 (no second driver; C15 moves all 10). J2 (exact-type gate):
unfired — 13 `isinstance` uses, zero exact-type gates. Trigger: a
detail-less guard, or an exact-type gate appearing here.

### R7 — Deployment-mapping hardening vs identity reads (rejected)

The open `hostile-mapping-hardening` contract (materialize-once +
key-guard + vocabulary rejection over deployment mappings)
shares no rule with this file's reads (request/scope identity,
declaration enumeration — no vocabulary, no deployment subject).
Distinct populations. Trigger: a vocabulary-validated mapping
read appearing here.

### R8 — Label-split twins (rejected)

`AUTH_USER_MODEL.partition(".")` (tolerant: a missing dot yields
an empty model name the fail-soft read skips) vs relay's
`type_name.split(".", 1)` (fail-loud decode for a malformed
payload): same dot grammar, opposite failure postures bound to
their subjects' contracts (C16). Trigger: a third label-split, or
either side changing posture.

CONFIRMED by reference (no rows): `unset-bindings-across-families`
(this file consumes `is_inactive_value` by name — FL4);
`traversal-depth-cap-check` (this file consumes the owner
candidate `assert_set_traversal_depth` — FL4);
`one-sync-boundary` (verified; both async surfaces wrap this
file's sync walk — matrix axis 2).

## Defects

- D1 — O3 verdict: DEFECT (doc-only). The
  `input_values.py:301-303` sentence ("the permission walker
  materializes it through the UNBOUND `dict.items`") and the local
  `_related_declarations` docstring (`:650-654`, same unconditional
  claim) contradict the `:672` body, which reads unbound only for
  `dict` and falls back to instance `.items()` for other mappings.
  Realistic declarations are dicts so nothing breaks; the fix is
  prose narrowing (the code stands — R3: no base slot exists for
  arbitrary `Mapping`). No wire input reaches the gap
  (declarations are consumer class attributes), so the normal
  closeout-homing path applies, not the security path. Pending
  closeout homing (touches verified File `utils/input_values.py`
  prose + this file's docstring).
- D2 — fresh find: DEFECT (doc-only). The `_context_request`
  docstring (`:167-170`) claims a subclass's "`get` /
  `__getitem__` override never runs"; `Mapping.get`'s body is
  `return self[key]`, so a `__getitem__` override DOES run (only
  `get` overrides are defeated). Fix is prose narrowing to the
  `get` half plus the containment the guards provide. Not
  wire-reachable (contexts are server-constructed or
  consumer-supplied; a lying mapping attacks its own deployment).
  Pending closeout homing.
- O1 — observed, not homed: the re-export comment (`:80-84`) names
  `filters/sets.py` as an existing consumer via this path, but it
  imports `iter_input_items` from `input_values` directly; the only
  in-repo consumer via this path is the test suite. The shim's
  keep decision stands (historical external paths, recorded at
  `FilterSet._iter_input_items`). No defect: a stale name in a
  comment, not a contradicted contract.

## Pending execution

None. All conclusions are static against HEAD bytes; no probe, no
pytest, no workspace runs. Sharded and Postgres cells are
inapplicable by construction: the target is in-memory traversal
plus request-identity reads reaching no database, alias, or
dialect decision (`router.db_for_read` answers are read, never
queried — `resolve_auth_aliases` issues zero SQL).

## Judgment

Zero-edit file item. All 21 named definitions homed: 6 file-local,
2 convergences into open families (`awaitable-refusal-and-disposal`
as consumer, `base-slot-container-reads` dict arm), 8 rejections
(4 converging with standing verdicts), 2 doc-only defects pending
closeout homing, 1 observation. No consolidation inside this file
item; no production edits.

## Index rows for Worker-0

F-AWAIT converges into the already-open family and F-FA converges
into the already-open family (existing plan rows stand, holding
items unchanged). All rows below are new for the [plan][plan]
`## Responsibility index`.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `permissions-request-identity-ladder` | `django_strawberry_framework/utils/permissions.py::request_from_info` | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL1; covers `ChannelsRequestAdapter`, `_channels_scope`, `_context_request`, `_channels_request_adapter`, `_request_from_context`; C1 + C2 + C3 count 1; D2 on the docstring) |
| `permissions-auth-alias-derivation` | `django_strawberry_framework/utils/permissions.py::resolve_auth_aliases` | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL2; covers `_safe_get_model`, `auth_aliases_for_permission_classes`; C4 + C5 count 1) |
| `permissions-gate-dispatch` | `django_strawberry_framework/utils/permissions.py::invoke_permission_method` | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL3; covers `_check_method_name`, `_fire_gate_on_class`, `_GATE_ASYNC_RECOURSE`; C6 + C7 count 1; mechanism in F-AWAIT, wording in R1) |
| `permissions-walk-orchestration` | `django_strawberry_framework/utils/permissions.py::run_active_input_permission_checks` | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL4; covers `active_permission_targets`, `active_related_branches`, `extract_branch_value`, `verbatim_path`; C9 count 1) |
| `permissions-flat-path-parity` | `django_strawberry_framework/utils/permissions.py::_fire_flat_relation_path_gates` | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL5; covers `_related_declarations`; C10 + C11 count 1; dict arm in F-FA, else arm in R3, D1 on the docstring) |
| `permissions-module-mechanics` | `django_strawberry_framework/utils/permissions.py` (docstring + imports + `__all__`) | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | file-local (FL6; C17; O1 stale consumer name) |
| `permissions-gate-recourse-vs-mutation-twin` | `django_strawberry_framework/utils/permissions.py::_GATE_ASYNC_RECOURSE` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/mutations/permissions.py` | File `utils/permissions.py` | rejected (R1; CONVERGE with rejected `sync-boundary-recourse-wording`; C8; trigger: either wording generalized) |
| `permissions-mapping-get-vs-base-slot` | `django_strawberry_framework/utils/permissions.py::_context_request` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | rejected (R2; half-strength: `__getitem__` dispatches; C14; trigger: family ruling half-strength in, or reads hardening) |
| `permissions-nondict-fallback-vs-base-slot` | `django_strawberry_framework/utils/permissions.py::_related_declarations` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py` | File `utils/permissions.py` | rejected (R3; CONVERGE with `input_values` R4 no-base-slot direction; C13; trigger: declarations constrained to `dict`) |
| `permissions-identity-vs-key-storage` | `django_strawberry_framework/utils/permissions.py::request_from_info` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/utils/context.py` | File `utils/permissions.py` | rejected (R4; CONVERGE with verified context R2; trigger: standing trigger) |
| `permissions-safe-model-read-vs-relay-decode` | `django_strawberry_framework/utils/permissions.py::_safe_get_model` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/types/relay.py` | File `utils/permissions.py` | rejected (R5; fail-soft skip vs fail-loud raise; trigger: either side changing posture) |
| `permissions-standing-guard-triggers` | `django_strawberry_framework/utils/permissions.py` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/_request_body.py` | File `utils/permissions.py` | rejected (R6; CONVERGE with J1, J2 unfired; C15; trigger: detail-less guard or new exact-type gate) |
| `permissions-reads-vs-hostile-mapping` | `django_strawberry_framework/utils/permissions.py::request_from_info` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/utils/policies.py` | File `utils/permissions.py` | rejected (R7; identity/declaration reads vs deployment-mapping validation; trigger: vocabulary-validated read appearing here) |
| `permissions-label-split-vs-relay-split` | `django_strawberry_framework/utils/permissions.py::resolve_auth_aliases` (rejection recorded here) | `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/types/relay.py` | File `utils/permissions.py` | rejected (R8; tolerant partition vs fail-loud split; C16; trigger: third split or posture change) |

Convergences by reference (no rows): open
`awaitable-refusal-and-disposal` (F-AWAIT: consumer, already
composed), open `base-slot-container-reads` (F-FA: `:672` dict arm),
verified `unset-bindings-across-families` (FL4 consumes the rule),
open `traversal-depth-cap-check` (FL4 consumes the owner
candidate), verified `one-sync-boundary` (async surfaces wrap this
walk).

## Independent verification (Worker-2)

Expectation-first trace (recorded from HEAD bytes `9889d6fe` +
worktree read before opening `## Findings`): a neutral permission
mechanics module in four rules — request-identity ladder
(`request_from_info` + Channels adapter + context reads),
auth-alias derivation, gate dispatch (name grammar + slot verdicts
+ async-guard composition), walk orchestration (single-pass
partition + related recursion + flat-path parity). Expected: 32
`ast.Module.body` members / 21 named definitions over HEAD bytes;
all worktree-vs-HEAD hunks one external migration (new untracked
`truth.py` / `lazy.py` consumers); async-guard seam a consumer of
the open awaitable family; `:672`-shaped unbound `dict.items` arm
a consumer of the open base-slot family; the `_context_request`
UNBOUND prose suspicious against `Mapping.get`'s `self[key]` body.

Reconciliation — all seven required judgments STAND in substance:

1. Enumeration: my independent AST count over HEAD bytes is 32
   members (1 docstring + 10 imports + 2 assigns + 1 class + 18
   functions) and 21 named definitions; every table row 1-21 +
   mechanics checked member by member against HEAD symbols
   (adapter has 6 methods). C1-C17 all carry counts.
2. Hunks: 14/14 re-verified by content as the single coherent
   truthful-reads migration (`isinstance`/`_safe_*` →
   `truth.*`, `+unwrap_lazy_object`, containment + readability
   protocol deleted). `ITEM_BASELINE`-vs-worktree diff is empty;
   `truth.py`/`lazy.py` are untracked and absent at HEAD; the
   [plan][plan] `## Owned changes` ledger was read whole — no row
   names this file. Concurrent-external CONFIRMED. Notation nit
   below (E2); attribution itself is complete.
3. Convergences: F-AWAIT — exactly 1 `reject_async` call site
   (`:422`), owner `_dispose_sync_awaitable` exists and is
   called by it, zero inline close/cancel spellings; consumer
   role correct. F-FA — `:672` `dict.items(related)` matches the
   FA contract verbatim and the `input_values.py:91` arm shape;
   the eager axis correctly judged non-splitting (tuple). Both
   families open; nothing to transcribe.
4. Rejections (all 8 probed independently): R1 — wordings differ,
   owner docstring declines these two, mutation "four clauses"
   comment verbatim, family rejected. R2 — `Mapping.get` body is
   `self[key]` (CPython source), so half-strength vs FA's
   never-through-instance-attribute contract is a real
   difference. R3 — no base slot for arbitrary `Mapping`; same
   line + trigger as verified input_values R4. R4 — opposite
   postures re-read on both bodies (fail-loud labelled raise vs
   default-returning key storage); target verified. R5 —
   fail-soft `None` vs fail-loud `ConfigurationError` on
   `LookupError` (relay `:787-794`). R6 — 10
   `except BaseException` sites counted, per-site wording; 13
   `isinstance`, zero exact-type gates. R7 — hostile-mapping
   contract (materialize + key-guard + vocabulary over
   deployment mappings) shares no rule here. R8 — tolerant
   partition + fail-soft vs fail-loud (wording nit E3).
5. D1: contradiction verified at all three HEAD sites
   (input_values `:301-303`, local `:651-654`, body `:672`).
   Docstring-contradicts-body is a named DRY.md defect class;
   doc-only, closeout homing touching verified input_values
   prose + this docstring. DEFECT verdict STANDS.
6. D2: `:168-170` "`get` / `__getitem__` override never runs"
   vs `Mapping.get` = `self[key]` — the `__getitem__` half is
   false at HEAD bytes. Same defect class, doc-only. DEFECT
   verdict STANDS.
7. O1: `filters/sets.py` imports `iter_input_items` from
   `input_values` directly (`:67-76`, `:2114` delegate
   docstring); no production importer takes it via this path
   (7-name `sets_mixins` block excludes it); the test suite
   does (`:16-29`). Stale-name-in-comment, keep decision
   reasonable. Observed-not-homed STANDS.

Also verified: consumer census (7 production importers, no
stale entry); oracle size (1293 lines, 52 tests) + independence
spot rows; live wire rows exist by content (`:2108` flat,
terminal-chain, order-gate — worktree line drift only); matrix
axes 1-6 each judged against the real surface (axis 2 wrap
sites `orders/sets.py:831`, `filters/sets.py:3497` confirmed);
all freshness blobs re-hashed byte-identical
(`9889d6fe`/`1c9cfd39`/`3616927d`/`b9ded33b`/`f2566609`/`abf30ad3`);
`## Pending execution` empty is correct (static-only; sharded/PG
inapplicable by construction — zero SQL issued); no AGENTS.md
prose violation (`:NNN` allowed in per-cycle artifacts, no
banned provenance, link scaffold intact); ruff vacuous
(zero-edit, only the `.md` artifact); HEAD `0c0537e2` unmoved
from dispatch through this verdict.

Revision feedback (record accuracy only; no judgment moves, no
re-trace needed — same-W1-context resubmission). Four false
record claims to fix in-artifact:

- E1 (FL6): "`9-name` `__all__`" is false — HEAD `:85-97`
  lists 11 names. Reproduce: `git show
  HEAD:django_strawberry_framework/utils/permissions.py | sed -n
  '85,97p'`. Fix to "11-name".
- E2 (System trace): the hunk list names 12 headers for "all 14
  hunks", folds `-47`/`-265`/`-633`, and cites phantom `@@
  -162` (a HEAD line ref inside the `@@ -143` hunk, not a
  header). Reproduce: `git diff HEAD --
  django_strawberry_framework/utils/permissions.py | grep '^@@'`.
  Fix: name the 14 real headers (`-34`, `-47`, `-118`, `-143`,
  `-195`, `-205`, `-252`, `-265`, `-274`, `-331`, `-394`,
  `-604`, `-633`, `-649`).
- E3 (R8): "fail-loud unpack" misnames the mechanism — relay
  `:785-786` guards with `"." in type_name`; the fail-loudness
  is the empty-slot / `LookupError` / unregistered raises.
  Fix to "fail-loud decode".
- E4 (Matrix axis 2): "zero `await`" is token-false — the token
  appears in 3 prose lines (`:56` comment, `:60` recourse
  string, `:383` docstring). Substance (sync-only) stands.
  Fix to "zero `await` expressions".

Verdict: `revision-needed` on E1-E4 alone. Everything else
stands as written.

Re-pass on `ready-for-verification/2` (Worker-2, same context):
E1 "11-name" reproduces (HEAD `:83-95`, 11 names `:84-94`); E2
names the 14 mechanical `@@` headers with the phantom dropped;
E3 reads "fail-loud decode"; E4 reads "zero `await` expressions".
Substance untouched (22 enum rows, 14 index rows, Judgment and
D1/D2/O1 identical, this section intact; no `## Iterations`
appended — noted, not blocking). Target diff vs ITEM_BASELINE
still empty; HEAD `0c0537e2` unmoved. Verdict: `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
