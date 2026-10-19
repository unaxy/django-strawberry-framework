# DRY review: `django_strawberry_framework/mutations/inputs.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is routed to an open family holding item, recorded file-local with its
proving challenge, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Target (976 lines, FRESH): the write-side generation substrate
[mutations-inputs][mutations-inputs] — generated `<Model>Input` /
`<Model>PartialInput` `@strawberry.input` classes, the public `FieldError`
envelope, and the `<Name>Payload` wrapper. Pure, finalizer-free, sync-only
(probe: 0 `async def`, 0 `await`): given a model + operation kind + effective
field set + primary `DjangoType`, it produces classes; the phase-2.5 bind in
[mutations-sets][mutations-sets] calls it, the resolvers in
[mutations-resolvers][mutations-resolvers] decode against its specs. What it
owns on the WORKING tree (first-hand full read):

- `::CREATE` / `::PARTIAL` — the generator-kind tokens the descriptor table
  in [mutations-operations][mutations-operations] imports.
- `::FieldError` — the ONE public envelope member every write flavor returns.
- `::relation_id_scalar` / `::relation_id_annotation` — the Relay-`GlobalID`
  vs raw-pk id-type rule + cardinality wrap the form and serializer flavors
  ride by call.
- `::related_model_of_queryset` / `::require_queryset_related_model` /
  `::annotate_queryset_relation` — the column-less relation typing spine both
  flavors ride by call.
- `::model_column_write_kind` — the relation/file/scalar classifier both
  flavors ride by call (the KIND TOKENS stay single-sited at
  [utils-inputs][utils-inputs]; forms + serializer re-export them by name).
- `::model_column_write_annotation` / `::model_column_input_annotation` /
  `::relation_input_annotation` — the column annotation assembly the model
  generator, the form triple builder, and the serializer resolver ride.
- `::MutationInputShape` / `::mutation_input_shape` /
  `::mutation_input_type_name` — the one shape descriptor + name wrapper the
  bind, the merge path, and the `input_type_name` seam all consume.
- `::mutation_input_field_specs` / `::_relation_field_index` — the
  total-coverage reverse-map specs the bind stashes and the decode reads.
- `::build_mutation_input` — the generator body (requiredness, overrides,
  M2M-optional, empty-input guard, collision arms).
- `::build_payload_type` — the F1 MATERIALIZATION half (`type(f"{
  mutation_name}Payload", …)`); `::payload_object_slot` (uniform
  node/result slot); `::_RESERVED_PAYLOAD_ATTRS` guard.
- `::EXCLUDED` tag, `::NON_FIELD_ERROR_KEY` pin, `::INPUTS_MODULE_PATH`
  constant, namespace lifecycle trio + `register_subsystem_clear` arm,
  `::_audit_mutation_input_surface`, `::_frozenset_of_attr_names`,
  `::editable_input_fields`, `::input_field_required`,
  `::_reject_generated_input_collisions`, `::_pascalize_token` legacy alias.

EXTERNAL concurrent hunks (never edited, reverted, or tidied): working
[forms-inputs][forms-inputs] `436fcf42…` vs HEAD `55614839…` (+18/-5 in
`::_form_field_basis` hostile-guard hardening, read first-hand via
`git diff HEAD`); working [mutations-fields][mutations-fields] `8c60a5c6…`
vs HEAD `cf518361…` (guard-trio hardening); working
[filters-inputs][filters-inputs] `06797dc7…` vs HEAD/record `82b52d97…`.
Since this file item makes ZERO production edits, the dirt is not a stop:
the trace reads the WORKING tree throughout, records BOTH fingerprints per
hunk-adjacent finding, and flags hunk-touching lines explicitly. Target
itself CLEAN (`git diff HEAD` empty; `git diff` vs ITEM_BASELINE empty).

Connected code read for judgment, outside the item (full reads unless
noted): [mutations-operations][mutations-operations] (full 157 lines),
[mutations-permissions][mutations-permissions] (full),
[mutations-fields][mutations-fields] prediction site + seam prose (lines
270–339 first-hand), [mutations-sets][mutations-sets]
`::build_and_stash_payload` + `::bind_write_declarations` +
`::DjangoMutation.input_type_name` (grazed ranges),
[mutations-resolvers][mutations-resolvers]`::payload_cls_for` +
`EXCLUDED` dispatch arms (grazed), [auth-mutations][auth-mutations]
register/login/logout bind (grep-verified call sites),
[forms-inputs][forms-inputs]`::form_input_type_name` +
`::_field_triple_and_spec` + `::_model_less_relation_annotation` (first-hand),
[rf-inputs][rf-inputs] module contract + namespace trio (head read),
[rf-converter][rf-converter] consumer call sites (grep-verified),
[forms-converter][forms-converter] kind re-exports + `::form_field_required`
(grep-verified), [utils-inputs][utils-inputs]`::name_set_input_type_name` +
`::normalize_field_name_sequence` + `::pascalize_token` docstrings
(first-hand), [utils-errors][utils-errors]`::field_error` (first-hand),
[finalizer][finalizer]`::_audit_field_surface` + surface builder
(first-hand), [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin` +
`::ActiveInputPermissionMixin` presence (grazed),
[types-converters][types-converters] + [types-relay][types-relay]
`::implements_relay_node` ownership (grep-verified), oracles
[test-inputs][test-inputs] (79-test inventory + payload/envelope rows
first-hand) and live [products-api][products-api] payload rows
(grep-confirmed). Untouched concurrent dirt (`connection.py`,
`extensions/resource_policy.py`, `filters/sets.py` hunks, all `tests/`
companions, staged `tests/utils/test_querysets.py`, `docs/bug_hunt/`
artifact, the plan, the utils/querysets trace collision) is out of scope;
none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** [forms-inputs][forms-inputs] +
[rf-inputs][rf-inputs] read FIRST, call by call. The three write flavors
share ONE substrate by import, not by copy: id-type rule (N1), column-less
spine (N2), kind classifier (N3), column annotation (N4), reverse-map
builder (N7) are defined here and consumed by name in
[forms-inputs][forms-inputs] (`model_column_input_annotation`,
`model_column_write_kind`, `annotate_queryset_relation` call sites read
first-hand) and [rf-converter][rf-converter] (`annotate_queryset_relation`,
`model_column_write_kind`, `model_column_write_annotation` call sites
grep-verified). Per-flavor divergences stay at the flavors with concrete
contract differences: form `target_name` is the DECLARED name (a bound
Django form is keyed by form-field name), never the `<name>_id` attr (N4);
form requiredness is `converter.form_field_required` on a different key
space (R7); the `FORM` sentinel + create-shaped polarity live in
[forms-inputs][forms-inputs] (R8); the serializer names by DESCRIPTOR digest
(`serializer_input_type_name`), not name-set (R9); the three input
namespaces are disjoint ledgers by spec-038 Decision 5 (R10). The `FORM`
sentinel is defined in [forms-inputs][forms-inputs], never here — this
module knows only `CREATE`/`PARTIAL`. Auth register/login/logout ride the
model generator + payload builder by call (grep-verified).

**2. Sync/async twins.** None defined here: mechanical probe ([probe][probe],
PROBE OK) asserts 0 `async def` + 0 `await` over the working tree. Pure
sync generation; the `sync_to_async` boundary + `resolve_sync` /
`resolve_async` entry pair live in
[mutations-resolvers][mutations-resolvers] (indexed
`shared-write-entry-factory` / `shared-write-skeleton` — checked, no
surface here: no entry import, no pipeline body, R1). Compared by behavior,
not shape: nothing here awaits, suspends, or touches the executor mode.

**3. Derived rather than repeated knowledge.** Payload name
`f"{mutation_name}Payload"` is MATERIALIZED here
([mutations-inputs][mutations-inputs]`::build_payload_type`) but PREDICTED
at [mutations-fields][mutations-fields]`::_synthesized_mutation_signature`
(`f"{mutation_cls.__name__}Payload"`): two spellings of one grammar, F1
CONFIRMED (count 2, re-derived fresh from this side; consolidation + gate
owed at the family item, never here). Input names are NOT re-derived: the
bind, the merge path, and the `input_type_name` seam all read the ONE
`::mutation_input_shape` descriptor (N5); the field factory consults the
seam, never a local spelling. The slot grammar (`node`/`result`) is
single-sited at `::payload_object_slot` (F1 sub-rule, count 1). The KIND
TOKENS are single-sited at [utils-inputs][utils-inputs] (this file imports
them; forms + serializer re-export by name — 0 definitions here).

**4. Inverse / round-trip pairs.** Build (here) vs decode
([mutations-resolvers][mutations-resolvers] decode + [write-values][write-values]
pipeline): the shared contract is the `InputFieldSpec` RECORD (owner
[utils-inputs][utils-inputs]); per-flavor spec builders (model N7, form
triple, serializer resolve path) walk DIFFERENT bases with different
`target_name` semantics — adapters over one record type, not copies (N7 +
R12). Payload build (here) vs `payload_cls_for` read-back: compose by name
via the `_payload_type_name` stash (F1 consumers, 0 edits). Spec-040 D6
`EXCLUDED` tag (here) vs resolver capture handler (imports the tag by name,
0 edits — FL10). No pack/unpack or encode/decode second half lives here:
`relay.GlobalID` appears ONLY as a returned ANNOTATION (R2).

**5. Contracts restated in another medium.** Production (this file);
authoritative contract sources (spec-036/037/038/039 Decisions + spec-040
D6, cited in docstrings — cited, not re-verified against archived spec
text, per sibling-file precedent); projections (module docstring: lazy-path
contract, single-site mechanics claims, opposite-selection claim vs orders
— each verified against its body/imports); independent oracles
([test-inputs][test-inputs]: 79 tests, expectations spelled literally —
`"CreateThingPayload"`, `"DoActionPayload"`, `"node"`, `"__all__"`,
`StrawberryOptional`/`StrawberryList` shapes — never derived from owner
logic; live [products-api][products-api]`CreateItemPayload!` wire row).
A grammar change moves production once; oracles + projections follow as
their own media, not counted (all Challenges).

**6. Enforcement by omission.** Flavor family enumerated: model
create/update/delete, ModelForm create/update, serializer create/update,
plain form, auth register. Empty-input guard: model HERE
(`::build_mutation_input`, override-aware); form owns its guard
([forms-inputs][forms-inputs] empty-basis raise, read); serializer owns its
own (spec-039 shape; no surface here to omit from). `delete` materializes
no input on EVERY path (`operation_takes_data` gates the field ref;
`input_type_name` raises typed `ConfigurationError` for delete — consistent,
not an omission). `EXCLUDED` defaults to `()` (opt-in seam, not omission:
only register passesAttrs). M2M always-optional is stated in the model
generator; form/serializer carry their own cardinality contracts on
different bases (no contract source found requiring the identical rule
there — no verdict, never a defect). Fixed-auth no-input surfaces carry
their own spec-040 contract. 0 defects (see `## Defects`).

### Enumeration

Instrument: [probe][probe] (`ast.Module.body` over the WORKING file) — **52 top-level statements**.
Every member lands below; every challenge in `### Challenges` ends in a
family row, a file-local row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring | prose projection | projection (verified per claim in Matrix 1/3) |
| 1–16 | 16 imports (`__future__`, `Callable`/`Collection`, `Any`/`NamedTuple`, `strawberry`, `NON_FIELD_ERRORS`/`FieldDoesNotExist`, `models`, `relay`, `to_camel_case`, exceptions, registry, `Upload`, converters, `implements_relay_node`, utils-inputs spine, relations, `graphql_camel_name`) | compose-by-name | no rule defined (C-owners live elsewhere; 0 definitions) |
| 17 | `INPUTS_MODULE_PATH` | 1 constant | FL5 file-local (R10: sibling namespaces distinct by design) |
| 18 | `NON_FIELD_ERROR_KEY` | 1 pin | FL9 file-local |
| 19 | `EXCLUDED` | 1 tag | FL10 file-local (resolver consumer by name) |
| 20–21 | `CREATE` / `PARTIAL` | 2 kind tokens | F2 indexed `mutation-operation-descriptors` (definition role) |
| 22 | `def _frozenset_of_attr_names` | normalizer | FL1 file-local (R5: twin-rejection) |
| 23 | `class FieldError` | envelope | N6 new family `mutation-error-envelope` |
| 24 | namespace trio unpack | ledger | FL5 (arm at 28 → F3 indexed `subsystem-clear-lifecycle`) |
| 25 | `def _audit_mutation_input_surface` | audit | FL4 file-local (R11: finalizer-audit rejection) |
| 26 | `def materialize_mutation_input_class` | materialize | FL5 |
| 27 | `def clear_mutation_input_namespace` | clear | FL5 |
| 28 | `register_subsystem_clear(...)` expr | bus arm | F3 indexed `subsystem-clear-lifecycle` (consumer role) |
| 29 | `def editable_input_fields` | basis selector | FL2 file-local (R6: orders-twin rejection) |
| 30 | `def input_field_required` | requiredness | FL3 file-local (R7: key-space rejection) |
| 31 | `def relation_id_scalar` | id-type rule | N1 new family `write-relation-id-typing` |
| 32 | `def relation_id_annotation` | cardinality wrap | N1 |
| 33 | `def related_model_of_queryset` | queryset read | N2 new family `column-less-relation-typing` |
| 34 | `def require_queryset_related_model` | fail-loud | N2 |
| 35 | `def annotate_queryset_relation` | spine | N2 |
| 36 | `def relation_input_annotation` | naming triple | N4 new family `model-column-write-annotation` |
| 37 | `def model_column_write_kind` | classifier | N3 new family `model-column-write-classification` |
| 38 | `def _relation_field_index` | bind index | N7 new family `mutation-input-reverse-map` |
| 39 | `def mutation_input_field_specs` | spec builder | N7 |
| 40 | `def model_column_write_annotation` | annotation | N4 |
| 41 | `def model_column_input_annotation` | triple | N4 |
| 42 | `_pascalize_token = pascalize_token` | legacy alias | FL8 file-local (no in-repo importers) |
| 43 | `def mutation_input_type_name` | name wrapper | N5 new family `generated-mutation-input-identity` |
| 44 | `class MutationInputShape` | descriptor | N5 |
| 45 | `def mutation_input_shape` | derivation | N5 |
| 46 | `class _GeneratedInputFieldName` | collision record | FL7 file-local (spine consumer) |
| 47 | `def _reject_generated_input_collisions` | collision walk | FL7 |
| 48 | `def build_mutation_input` | generator | FL6 file-local (bind calls by name) |
| 49 | `_RESERVED_PAYLOAD_ATTRS` | slot guard | F1 indexed `mutation-payload-name` (sub-rule, count 1) |
| 50 | `def payload_object_slot` | slot rule | F1 (sub-rule, count 1) |
| 51 | `def build_payload_type` | payload builder | F1 (MATERIALIZATION half, count 2) |

### Challenges

Each rule: change posited, authoritative-definition count (consumers,
oracles, projections listed, not counted).

- **C1. Rename the payload suffix** (`Payload` → `Result`). Definitions
  forced: [mutations-inputs][mutations-inputs]`::build_payload_type`
  (`type(f"{mutation_name}Payload", …)`, probe-confirmed present) AND
  [mutations-fields][mutations-fields]`::_synthesized_mutation_signature`
  (`f"{mutation_cls.__name__}Payload"`, probe-confirmed present). Count =
  **2**. [mutations-sets][mutations-sets]`::build_and_stash_payload` passes
  `__name__` through + stashes the built name (0 edits); auth fixed names
  ride the base-name argument (0 edits); oracles spelling
  `CreateThingPayload` move as media. → F1. Re-derived fresh from THIS side;
  consolidation stays with the family item.
- **C2. Change the slot rule** (`node`/`result` → model-derived). Definitions
  forced: `::payload_object_slot` alone; `::build_payload_type` derives the
  default from it (internal, 0 edits); auth passes the explicit call result
  (0 edits); oracles pinning `node` move as media. Count = **1**. → F1
  sub-rule.
- **C3. Change the reserved payload attrs** (add `ok` to the model shape).
  Definitions forced: `::_RESERVED_PAYLOAD_ATTRS` alone (guard read inside
  the builder). Count = **1**. → F1 sub-rule.
- **C4. Change the id-type policy** (Relay target → raw pk). Definitions
  forced: `::relation_id_scalar` alone; `::relation_id_annotation` +
  `::relation_input_annotation` + `::model_column_write_annotation` ride the
  call (0 edits); form/serializer flavors ride the same call (0 edits);
  oracles pinning `GlobalID` move as media. Count = **1**. → N1.
- **C5. Change the relation naming** (`<name>_id` → bare name). Definitions
  forced: `::relation_input_annotation` alone (callers take the triple
  whole). Count = **1**. → N4.
- **C6. Add a write kind** (new column class). Definitions forced:
  `::model_column_write_kind` (classification); the KIND TOKEN spelling
  stays at [utils-inputs][utils-inputs] (separate owner, moves only if the
  token itself changes); form/serializer dispatch arms consume the token
  (0 edits). Count = **1** here. → N3.
- **C7. Change the column-less missing-model policy** (raise → raw-pk
  fallback at the spine). Definitions forced:
  `::require_queryset_related_model` (takes `missing=` — wording stays at
  flavors, 0 edits there). Count = **1**. → N2.
- **C8. Change the model requiredness rule** (blank+default stays required).
  Definitions forced: `::input_field_required` alone (only the create arm of
  the model generator consults it). Count = **1**. → FL3 (+ R7 stays
  separate).
- **C9. Change the editable basis** (admit a new column type). Definitions
  forced: `::editable_input_fields` (basis); the narrowing spine stays at
  [utils-inputs][utils-inputs]`::resolve_effective_fields` (0 edits).
  Count = **1**. → FL2 (+ R6 stays separate).
- **C10. Change the shape identity** (add a component). Definitions forced:
  `::mutation_input_shape` alone; `::mutation_input_type_name`,
  `::build_mutation_input`, the bind cache key, the merge path, and the
  `input_type_name` seam read the descriptor (0 edits). Count = **1**. → N5.
- **C11. Change the input-name grammar** (suffix / token). Definitions
  forced: [utils-inputs][utils-inputs]`::name_set_input_type_name` alone;
  this file's wrapper + form's wrapper pass through (0 edits). Count =
  **0 here, 1 at owner**. → N5 (wrapper role) + R8 (adapter twin).
- **C12. Change attr-set normalization** (reject sets, accept `None`).
  Definitions forced: `::_frozenset_of_attr_names` alone (its two call
  sites pass values through). Count = **1**. → FL1 (+ R5 stays separate).
- **C13. Change the surface-audit caser** (`to_camel_case` → package caser).
  Definitions forced: `::_audit_mutation_input_surface` alone (the in-body
  comment pins WHY the fallback must stay Strawberry's). Count = **1**. →
  FL4 (+ R11 stays separate).
- **C14. Extend the envelope** (additive member). Definitions forced:
  `::FieldError` alone; [utils-errors][utils-errors]`::field_error`
  constructs it positionally-by-contract (new defaulted member = 0 edits);
  flavor payloads carry the same class (0 edits); oracles move as media.
  Count = **1**. → N6.
- **C15. Change clear semantics** (strip parked globals). Definitions forced:
  `::clear_mutation_input_namespace` alone (bus iterates it by callback).
  Count = **1**. → FL5 (+ F3 bus role).
- **C16. Change the empty-input guard** (wording / override-awareness).
  Definitions forced: `::build_mutation_input` guard block alone (form /
  serializer guards are their own bodies on different bases). Count =
  **1**. → FL6.
- **C17. Change collision policy** (attr arm ↔ graphql arm). Definitions
  forced: `::_reject_generated_input_collisions` (arm flags); the walk
  stays at [utils-inputs][utils-inputs]`::iter_input_field_collisions`
  (0 edits); form/serializer call the SPINE with own subjects (0 edits).
  Count = **1**. → FL7.
- **C18. Change the kind-token values** (`"create"` → `"add"`). Definitions
  forced: `::CREATE` / `::PARTIAL` here; [mutations-operations][mutations-operations]
  descriptors + form/serializer imports ride by name (0 edits). Count =
  **1**. → F2 (definition role; descriptor-table changes need 0 edits here).
- **C19. Change the `EXCLUDED` tag spelling.** Definitions forced: `::EXCLUDED`
  here; [mutations-resolvers][mutations-resolvers] dispatch + register seam
  import by name (0 edits). Count = **1**. → FL10.
- **C20. Change the non-field key** (off Django's sentinel). Definitions
  forced: `::NON_FIELD_ERROR_KEY` here; [utils-errors][utils-errors] +
  resolvers import by name (0 edits); Django owns the value. Count = **1**.
  → FL9.
- **C21–C24. Checked no-surface (0 definitions here; do not inherit).**
  C21 `shared-write-entry-factory` + `shared-write-skeleton` (owners in
  [mutations-resolvers][mutations-resolvers]): R1. C22 `typed-globalid-decode`
  (owner [relay][relay]`::decode_model_global_id`): R2. C23 `set-type-naming`
  (owner [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin`): R3. C24
  `active-input-permission-facade` (owner [sets-mixins][sets-mixins]): R4.
  `type-registry-model-type-map` (`registry.get` read as injected
  `primary_of` — consumer, 0 definitions): R13. `sealed-authorization-source`,
  `one-sync-boundary`, `sync-boundary-recourse-wording`,
  `lookup-name-spelling-grammar`, `filter-logic-operators`,
  `lazy-related-class-resolution`, `related-set-target-lifecycle`,
  `converter-table-per-surface-ownership` (converters consumed by call):
  checked, no surface.

## Findings

- **F1 — `mutation-payload-name` (CONFIRMED genuine duplication, count 2;
  family item owns consolidation + gate).** Contract: the generated payload
  class is named `<MutationName>Payload` and materializes as a
  `mutations.inputs` module global. Variation axes: suffix spelling; hosting
  namespace. Sites + roles (re-derived fresh from THIS side, probe-verified
  present on the working tree): [mutations-inputs][mutations-inputs]`::build_payload_type`
  = definition (materializes, `type(f"{mutation_name}Payload", …)`);
  [mutations-fields][mutations-fields]`::_synthesized_mutation_signature` =
  second spelling (predicts at construction, bind has not run);
  [mutations-sets][mutations-sets]`::build_and_stash_payload` = consumer
  (passes `__name__`, stashes built name);
  [mutations-resolvers][mutations-resolvers]`::payload_cls_for` = consumer
  (reads the stash); oracles ([test-inputs][test-inputs] `CreateThingPayload`
  / `DoActionPayload` rows, live [products-api][products-api]
  `CreateItemPayload!` row) = media; docstring Decision-7 clauses =
  projection. Sub-rules, same family: uniform slot
  (`::payload_object_slot`, C2 count 1 — consumers call by name) +
  reserved attrs (`::_RESERVED_PAYLOAD_ATTRS`, C3 count 1). Challenges: C1
  count 2; C2/C3 count 1. Owner + lifetime: inputs.py (the materializer owns
  the grammar, principles 2/7; sibling prediction at fields.py cannot
  compose-by-name today — bind has not run at construction, only `__name__`
  exists — which is exactly why the pure `payload_type_name_for(base_name)`
  consolidation is owed, per the trigger artifact's record). Migration (for
  the family item): pure name function at inputs.py; the fields.py site
  becomes a call (timing-safe: needs only the class-name string). Distinct
  behavior: auth fixed names stay explicit arguments; model-less `{ok
  errors}` shape untouched. Behavioral proof: static-reviewed (both
  spellings read first-hand + probe-asserted present; agreement pinned by
  oracles). Structural gate: NOT established here — owed at the family item
  with its negative control (a behavior-preserving hand copy of the owner's
  body), per the file-item rule. Coupling: none. Freshness: inputs.py
  `fc442047…` (working == HEAD, target clean); fields.py work `8c60a5c6…` +
  HEAD `cf518361…` (hunk touches neither spelling — robust-to-both); sets.py
  `cffa29e5…`; resolvers.py `3fd1e571…`; test-inputs `6be1b081…`;
  products-api `eff4cd80…`.
- **F2 — `mutation-operation-descriptors` (indexed family; definition role
  here, no new row).** Contract: the write-side operation vocabulary. Sites:
  inputs.py `::CREATE`/`::PARTIAL` = kind-token definition (C18 count 1);
  [mutations-operations][mutations-operations] descriptors + predicates =
  owner (table changes need 0 edits here); forms/serializer = import
  consumers. Proof: static-reviewed (import line read first-hand at
  operations.py). Freshness: inputs.py `fc442047…`; operations.py
  `16223c6b…`. Robust-to-both (no hunk at either site).
- **F3 — `subsystem-clear-lifecycle` (indexed family; consumer role here, no
  new row).** Contract: `registry.clear()` drains per-subsystem clears.
  Sites: inputs.py `register_subsystem_clear(clear_mutation_input_namespace,
  owner="mutations.input_namespace", before_bind=True)` = registering
  consumer; the bus owns the lifecycle. Proof: static-reviewed. Freshness:
  inputs.py `fc442047…`; registry.py `9cc8bb55…`.
- **N1 — `write-relation-id-typing` (new family nomination, open).**
  Contract: a write-input relation types as Relay `GlobalID` iff the related
  model's primary `DjangoType` is Relay-Node-shaped, else the raw pk scalar;
  multi wraps as `list[id]`. Axes: id-type policy; cardinality. Sites:
  inputs.py `::relation_id_scalar` + `::relation_id_annotation` =
  definition (C4 count 1); [forms-inputs][forms-inputs]
  `::_model_less_relation_annotation` + triple builder = consumers (by
  call, first-hand); [rf-converter][rf-converter] serializer arms =
  consumers (by call, grep-verified; serializer requires a registered
  primary first — policy stays there). Challenges: C4 count 1. Owner:
  inputs.py (narrowest owner every write flavor already imports, principle
  7). Migration: none (already compose-by-name; family item records).
  Distinct behavior: DECODE stays at [relay][relay]`::decode_model_global_id`
  (R2 — type selection vs value decode, different contracts). Proof:
  static-reviewed; pinned by `test_relation_id_scalar_is_globalid_iff…` +
  `test_fk_to_relay/non_relay…` oracles (media). Gate: existing oracles
  observed gate-only; negative control owed at the family item. Coupling:
  none. Freshness: inputs.py `fc442047…`; forms-inputs work `436fcf42…` +
  HEAD `55614839…` (hunk at `::_form_field_basis`, outside the consumer
  call sites — robust); rf-converter `32904418…`; test-inputs `6be1b081…`.
- **N2 — `column-less-relation-typing` (new family nomination, open).**
  Contract: a relation with no backing model column types from
  `queryset.model`; an untyped queryset fails loud with the FLAVOR's error.
  Axes: model source; missing-wording (stays at flavors via `missing=`
  callback). Sites: inputs.py `::related_model_of_queryset` +
  `::require_queryset_related_model` + `::annotate_queryset_relation` =
  definition (C7 count 1); form + serializer column-less arms = consumers
  (by call). Challenges: C7 count 1. Owner: inputs.py (principle 7).
  Migration: none. Distinct behavior: queryset DISCOVERY (form
  `field.queryset` vs serializer `child_relation`) + naming stay at
  flavors. Proof: static-reviewed; pinned by
  `test_annotate_queryset_relation_packages…` + `test_form_and_serializer_…_share_queryset_annotation`
  (media). Gate owed at family item. Freshness: as N1.
- **N3 — `model-column-write-classification` (new family nomination, open).**
  Contract: a backing `models.Field` classifies relation→`relation_single`/
  `relation_multi`, file/image→`file`, else `scalar`. Sites: inputs.py
  `::model_column_write_kind` = definition (C6 count 1); the KIND TOKENS
  stay at [utils-inputs][utils-inputs] (0 definitions here); form triple +
  serializer resolve + internal spec/annotation paths = consumers.
  Challenges: C6 count 1. Owner: inputs.py (principle 7). Migration: none.
  Proof: static-reviewed; pinned by
  `test_model_column_write_kind_classifies…` +
  `test_form_and_serializer_column_kind_share_model_column_owner` (media —
  the oracle NAME states the ownership). Gate owed at family item.
  Freshness: as N1 + utils-inputs `ee31d360…`.
- **N4 — `model-column-write-annotation` (new family nomination, open).**
  Contract: a backing column maps to `(python_attr, graphql_name,
  annotation)` — FK/O2O→`<name>_id`, M2M→bare name, file→`Upload`, else
  read-side scalar; relation rides N1. Sites: inputs.py
  `::relation_input_annotation` + `::model_column_write_annotation` +
  `::model_column_input_annotation` = definition (C5 count 1);
  `::build_mutation_input` = internal consumer;
  [mutations-sets][mutations-sets] accepted-names + spec-synthesis reads =
  consumers (by call, grep-verified); form triple = consumer (first-hand,
  with the load-bearing divergence: form `target_name` = DECLARED name for
  the reverse map, never `<name>_id`); serializer resolve path = consumer.
  Challenges: C5 count 1. Owner: inputs.py. Migration: none. Distinct
  behavior: serializer SCALAR type-override + naming/source/primary-required
  policy stay at [rf-converter][rf-converter]. Proof: static-reviewed;
  pinned by `test_model_column_input_annotation_maps…` (media). Gate owed
  at family item. Freshness: as N1 + sets.py `cffa29e5…`.
- **N5 — `generated-mutation-input-identity` (new family nomination, open).**
  Contract: ONE derivation of shape→name→cache-key from `(model,
  operation_kind, frozenset(effective names))`; canonical `<Model>Input` /
  `<Model>PartialInput` for the full shape, deterministic shape-derived name
  when narrowed. Sites: inputs.py `::MutationInputShape` +
  `::mutation_input_shape` + `::mutation_input_type_name` = definition (C10
  count 1; wrapper over the [utils-inputs][utils-inputs] spine, C11 0 edits
  here); [mutations-sets][mutations-sets] bind + merge + `input_type_name`
  seam + [auth-mutations][auth-mutations] register = consumers (by call).
  Challenges: C10 count 1; C11 count 0 here. Owner: inputs.py (principle 4:
  derive once; descriptor carries model/kind/selected/full/effective/name/
  key with bind-scoped validity). Migration: none. Distinct behavior: the
  NAME GRAMMAR stays at the utils spine; the form twin adapter stays
  separate (R8 — different base-name source + unknown-kind polarity,
  recorded at the spine's own docstring). Proof: static-reviewed; pinned by
  `test_type_name_full/narrowed…` + `test_identical_shape_dedupes…` (media).
  Gate owed at family item. Freshness: inputs.py `fc442047…`; sets.py
  `cffa29e5…`; auth `dbe64995…`; utils-inputs `ee31d360…`.
- **N6 — `mutation-error-envelope` (new family nomination, open).**
  Contract: the shared `FieldError{field messages codes path}` envelope —
  ADDITIVE (members added, never removed/retyped), root non-field =
  `field="__all__"` + empty `path`. Sites: inputs.py `::FieldError` =
  definition (C14 count 1); [utils-errors][utils-errors]`::field_error` =
  leaf constructor consumer (function-local import, first-hand); model/form/
  serializer resolver pipelines + auth = structural consumers (by import).
  Challenges: C14 count 1. Owner: inputs.py (principle 7: the write
  substrate every flavor already depends on). Migration: none. Distinct
  behavior: code VOCABULARY (`FIELD_ERROR_CODE_*`) stays at
  [utils-errors][utils-errors]. Proof: static-reviewed; pinned by
  `test_field_error_envelope_shape` + frozen-set rows + live denial row
  (media). Gate owed at family item. Freshness: inputs.py `fc442047…`;
  utils-errors `3e25e93b…`.
- **N7 — `mutation-input-reverse-map` (new family nomination, open).**
  Contract: total-coverage specs + Django-field index for a (possibly
  merged) input so decode never `KeyError`; unresolvable attr fails loud at
  bind; `excluded_attrs` marks `EXCLUDED` kind. Sites: inputs.py
  `::mutation_input_field_specs` + `::_relation_field_index` = definition;
  [mutations-sets][mutations-sets] bind + [auth-mutations][auth-mutations]
  register = consumers (by call, grep-verified). Challenges: decode-side
  handler changes need 0 edits here (record contract, not definition).
  Owner: inputs.py. Migration: none. Distinct behavior: form/serializer
  spec builders walk DIFFERENT bases (form fields / serializer fields, R12)
  and form `target_name` ≠ input attr. Proof: static-reviewed; pinned by
  `test_mutation_input_field_specs_covers/generated…` rows (media). Gate
  owed at family item. Freshness: inputs.py `fc442047…`; sets.py
  `cffa29e5…`; auth `dbe64995…`.
- **FL1 — attr-set normalizer (file-local).** `::_frozenset_of_attr_names`
  (C12 count 1): freezes `overrides` / `excluded_attrs` to frozensets,
  consuming one-shot iterators once, rejecting bare str/bytes. No second
  site (R5: [utils-inputs][utils-inputs]`::normalize_field_name_sequence`
  returns `tuple|None` and rejects SETS + duplicates + non-strings — order-
  sensitive declared-sequence validation vs order-free attr-set freezing;
  different outputs, different rejects). Proof: static-reviewed; pinned by
  `test_consumer_override_freezes_one_shot_iterable` +
  `test_build_mutation_input_rejects_bare_string_overrides` (media).
  Freshness: inputs.py `fc442047…`.
- **FL2 — editable basis selector (file-local).** `::editable_input_fields`
  (C9 count 1): concrete editable non-pk columns + forward M2M, narrowed via
  the shared spine. No second site (R6: orders-side selector is the
  documented OPPOSITE — excludes M2M, keeps readonly — different contract,
  stated in both docstrings). Proof: static-reviewed; pinned by the
  editable/narrow/reject rows (media). Freshness: inputs.py `fc442047…`.
- **FL3 — create-requiredness predicate (file-local).**
  `::input_field_required` (C8 count 1): required iff no default + non-null
  + non-blank. No second site (R7: `form_field_required` keys on
  `forms.Field` incl. NullBoolean forcing; serializer on DRF flags +
  `optional_fields` — different key spaces, different signals). Proof:
  static-reviewed; pinned by `test_input_field_required_rule` (media).
  Freshness: inputs.py `fc442047…`.
- **FL4 — input-surface audit (file-local).** `::_audit_mutation_input_surface`
  (C13 count 1): duplicate-effective-GraphQL-name reject with the deliberate
  Strawberry `to_camel_case` fallback (package caser would MISS the
  `field_2`/`field2` collapse). No second site (R11: finalizer
  `::_audit_field_surface` audits READ-side type surfaces incl. inheritance
  merge — different population, different timing). Proof: static-reviewed;
  pinned by `test_camel_case_graphql_name_collision_is_fail_loud` +
  no-false-positive rows (media). Freshness: inputs.py `fc442047…`.
- **FL5 — namespace lifecycle + module path (file-local).**
  `::INPUTS_MODULE_PATH`, trio unpack, `::materialize_mutation_input_class`,
  `::clear_mutation_input_namespace` (C15 count 1): thin wrappers over the
  [utils-inputs][utils-inputs] ledger; parked-globals (no `delattr`) + the
  one-ledger (not `clear_generated_input_namespace`) semantics stated in
  body. No second site (R10: form/serializer trios are DISJOINT ledgers +
  namespaces by spec-038 Decision 5 — intentional separation; R13 bus role
  rides F3). Proof: static-reviewed; pinned by
  `test_inputs_module_path_constant` + dedupe/collision rows (media).
  Freshness: inputs.py `fc442047…`.
- **FL6 — generator body (file-local).** `::build_mutation_input` (C16 count
  1): triple assembly, create-vs-partial widening, M2M-always-optional,
  override skip + one-shot freeze, override-aware empty guard, dual
  collision arms. Called by name from the bind seams + auth (consumers, 0
  edits on body change — the subsystem's own entry body, cf. sibling FL5
  factory precedent). Proof: static-reviewed; pinned by required/partial/
  override/collision/empty rows (media). Freshness: inputs.py `fc442047…`.
- **FL7 — generated-collision walk (file-local).**
  `::_GeneratedInputFieldName` + `::_reject_generated_input_collisions`
  (C17 count 1): thin arm-flags over the utils spine; form/serializer call
  the SPINE with own subjects (adapters, not copies). Proof:
  static-reviewed; pinned by `test_fk_id_attr_collision_with_m2m…` +
  digit-boundary rows (media). Freshness: inputs.py `fc442047…`.
- **FL8 — token alias (file-local).** `::_pascalize_token` (spec-039
  promotion alias): zero in-repo importers (package + tests grep) — kept as
  the documented historical path, not a definition (no challenge moves it;
  deletion is a family-item question, never this item's). Freshness:
  inputs.py `fc442047…`.
- **FL9 — non-field key pin (file-local).** `::NON_FIELD_ERROR_KEY` (C20
  count 1): `= NON_FIELD_ERRORS`, single source so resolver keys match the
  `error_dict` read; [utils-errors][utils-errors] + resolvers import by name.
  Proof: static-reviewed; pinned by
  `test_non_field_error_key_is_django_all_sentinel` (media). Freshness:
  inputs.py `fc442047…`.
- **FL10 — exclusion tag (file-local).** `::EXCLUDED` (C19 count 1): the
  spec-040 D6 kind tag; [mutations-resolvers][mutations-resolvers] capture
  handler imports it by name (0 edits); register passes `password` through
  `excluded_attrs`. Proof: static-reviewed; pinned by
  `test_mutation_input_field_specs_marks_excluded_kind` (media). Freshness:
  inputs.py `fc442047…`.

### Rejected candidates

- **R1 `shared-write-entry-factory` / `shared-write-skeleton`: no surface.**
  Difference: entries normalize UNSET kwargs into a flavor pipeline body (+
  async boundary); this file builds CLASSES, never entries, with no resolver
  import (grep: zero hits). Trigger: a resolver entry or pipeline body in
  this module. (C21.)
- **R2 `typed-globalid-decode`: not inherited.** Difference: this file
  SELECTS the id TYPE (`relay.GlobalID` as a returned annotation);
  [relay][relay]`::decode_model_global_id` DECODES values to pks (consumed
  in resolvers + write-values, never here — zero decode imports/calls).
  Trigger: calling the decode primitive from this module. (C22.)
- **R3 `set-type-naming`: not inherited.** Difference:
  [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for` names
  SET classes from class + `LOOKUP_SEP` field path (`<Cls><Pascal><Suffix>`);
  `::name_set_input_type_name` names generated INPUT classes from shape
  identity (sorted-token + full-vs-narrowed + digest). Different
  populations, different mechanisms. Trigger: unifying set and input naming
  under one grammar. (C23.)
- **R4 `active-input-permission-facade`: no surface.** This file reads no
  permission hook, class, or attribute (grep: zero `permission` hits).
  Trigger: any permission read in this module. (C24.)
- **R5 `normalize_field_name_sequence`: not merged into
  `::_frozenset_of_attr_names`.** Difference: tuple-or-`None` declared-
  sequence validation (rejects sets/frozensets for order, non-strings,
  duplicates) vs frozenset attr-set freezing (ACCEPTS sets, consumes
  one-shot iterators once). Outputs, rejects, and call sites all differ.
  Trigger: unifying attr-set normalization across declared sequences and
  override/exclusion sets. (FL1.)
- **R6 orders basis selector: not merged into `::editable_input_fields`.**
  Difference: the orders side is the documented OPPOSITE selection (keeps
  readonly, drops M2M) — one rule spelled twice would lie about one side.
  Trigger: a shared column-basis abstraction both flavors can state. (FL2.)
- **R7 cross-flavor requiredness: not merged into `::input_field_required`.**
  Difference: `models.Field` default/blank/null signals vs `forms.Field`
  NullBoolean forcing vs DRF read_only/HiddenField/`optional_fields` —
  three key spaces, three signal sets. Trigger: a cross-flavor requiredness
  table keyed uniformly. (FL3.)
- **R8 `form_input_type_name`: adapter twin, not a copy.** Difference: both
  are 5-line wrappers over the shared spine, but base-name sources differ
  (model vs form class) AND unknown-kind posture differs (`!= CREATE` vs
  `== PARTIAL` — recorded at the spine owner's own docstring). Trigger: an
  identical polarity fix owed on both, or a third wrapper. (C11/N5.)
- **R9 serializer descriptor namer: not merged.** Difference:
  `serializer_input_type_name` keys on the per-field DESCRIPTOR digest
  (requiredness/descriptions/hook specs), not the name set — spec-039
  Decision 7. Trigger: converging descriptor and name-set identity. (N5.)
- **R10 form/serializer namespace trios: not merged.** Difference: three
  DISJOINT ledgers + module namespaces so `<Model>Input`, `<Form>Input`,
  `<Serializer>Input` never share a `__dict__` slot (spec-038 Decision 5).
  Trigger: merging the three namespaces. (FL5.)
- **R11 finalizer surface audit: not merged.** Difference: read-side TYPE
  surfaces with inheritance merge at finalize vs single generated/merged
  INPUT class at materialize. Trigger: a shared surface-audit spine spanning
  read types and write inputs. (FL4.)
- **R12 form/serializer spec builders: peers, not copies.** Difference: same
  `InputFieldSpec` RECORD (owner utils) assembled from different bases
  (model columns vs form `base_fields` vs serializer fields) with different
  `target_name` semantics (form: declared name, never `<name>_id`). Trigger:
  a shared spec-assembly body across bases. (N7.)
- **R13 `type-registry-model-type-map`: consumer-only.** Difference: this
  file never defines the map; it READS it through the injected `primary_of`
  (`registry.get` passed at call sites) where the rule must hold — a
  consumer, listed not counted. Trigger: defining or bypassing the map
  here. (C21.)
- **R14 read-side converter tables: consumer-only.** Difference:
  `convert_scalar` / `scalar_for_field` are owned at
  [types-converters][types-converters] and called here (symmetric wire
  contract by construction, spec-036 Decision 6). Trigger: a write-side
  scalar table here. (C21.)

## Defects

None. Axis-6 sweep: every flavor's guard present on its own basis
(model empty-guard here; form empty-guard at
[forms-inputs][forms-inputs]; `delete` input-less on all paths;
`EXCLUDED` opt-in parameterized, not omitted; M2M-optional stated where
its contract lives); the FORM-sentinel/requiredness/naming divergences
each name a supporting contract (spec-038/039 decision pointers verified
in-body) with no feasible consumer shape reaching a contradiction; no
docstring/body contradiction found (lazy-path, single-site, and
opposite-selection claims all verified at their sites); no layering
contradiction (`utils/errors.py` keeps its import function-local to avoid
the cycle, read first-hand). No security-impact findings.

## Pending execution

None. All proofs `static-reviewed`: single-owner records, compose-by-name
consumption, and inspection-grade equivalence (no ordering, transactional,
async, or ORM-query behavior is decided in this file — pure sync
generation over `_meta` + registry reads). No shared-tree pytest run made
or owed. Sharded/Postgres cells: `inapplicable by construction` — the
target opens no database, alias, or dialect decision (ledger + `_meta`
reads only; all ORM work lives in
[mutations-resolvers][mutations-resolvers] and below).

## Judgment

Zero-edit file item: 52/52 enumerated by mechanical probe (PROBE OK),
six matrix axes discharged against the real input/payload/envelope surface
with forms + serializer mirrors read first, F1 `mutation-payload-name`
CONFIRMED as genuine duplication (materialization re-derived fresh from
this side, count 2 — consolidation + gate owed at the family item, never
here), two indexed families routed as definition/consumer (F2/F3), seven
new family nominations for Worker 0 (N1–N7, all already-single-sited with
consumers by name), ten file-local rows (FL1–FL10), fourteen rejections
with contract differences + triggers, no defects, no pending execution.
Robust to all three concurrent hunks (none touches a traced line; dual
fingerprints recorded where adjacent).

## Implementation (Worker 1)

Artifact in [DRY.md][dry] shape (role delta [worker-1][worker-1]). Zero tracked changes. Item-scoped diff state: `git diff bb08045685f9e… --
django_strawberry_framework/mutations/inputs.py` empty AND `git diff HEAD
-- django_strawberry_framework/mutations/inputs.py` empty (working blob
`fc442047…` == HEAD — target CLEAN at both baselines, as tasked);
`git status --short` shows no touch by this worker under the item's paths
except two NEW untracked scratch paths below (never `git add`ed). Nothing
edited, reverted, tidied, formatted, or staged; no pytest run (forbidden in
this item); no ruff run owed (no `.py` tracked file touched; probe +
artifact are scratch/untracked).

Pending entries for Worker 0: (1) add index rows for N1–N7
(`write-relation-id-typing`, `column-less-relation-typing`,
`model-column-write-classification`, `model-column-write-annotation`,
`generated-mutation-input-identity`, `mutation-error-envelope`,
`mutation-input-reverse-map`, all owned at
`django_strawberry_framework/mutations/inputs.py`, holding items are the
respective family items); (2) add file-local rows FL1–FL10 for
`mutations/inputs.py`; (3) confirm F1/F2/F3 site records against the
fingerprints below (F1 consolidation + gate stay with the
`mutation-payload-name` family item). Scratch paths created (read-only,
untracked, for Worker 0 to remove by explicit path after verification):
`docs/dry/temp-tests/dry-file-mutations__inputs/probe_inputs_surface.py`
+ `docs/dry/dry-file-mutations__inputs.md` (this artifact).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[probe]: temp-tests/dry-file-mutations__inputs/probe_inputs_surface.py
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[relay]: ../../django_strawberry_framework/relay.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-errors]: ../../django_strawberry_framework/utils/errors.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[products-api]: ../../examples/fakeshop/test_query/test_products_api.py
[test-inputs]: ../../tests/mutations/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Role-delta reading order honored: AGENTS.md, DRY.md (canonical, HEAD
`9031cb3d`), worker-2.md, the plan item (File `mutations/inputs.py`, 976
lines, Run `0.0.15 2026-09-18-1`), the complete target (full 976-line
first-hand read), the item-scoped diff (empty, both baselines), write
mirrors FIRST (`forms/inputs.py` full 928-line read,
`rest_framework/inputs.py` full read through the shape/naming core +
`serializer_input_type_name` first-hand), then consumers, oracles, and
anything the trace needed. Never worker-memory. The trace below was
re-derived BEFORE opening `## Findings`; reconciliation follows it.

### Own trace (sites, roles, counts, owners)

Target: the write-side generation substrate — generated `<Model>Input` /
`<Model>PartialInput` classes, the public `FieldError` envelope, the
`<Name>Payload` wrapper. Pure sync generation (0 `async def`, 0 `await`
by AST walk; no resolver/entry import; only `_meta` + `registry.get`
reads — no database, alias, or dialect decision anywhere).

- Payload naming. Materializer
  `django_strawberry_framework/mutations/inputs.py::build_payload_type`
  builds `type(f"{mutation_name}Payload", …)` (definition). Predictor
  `django_strawberry_framework/mutations/fields.py::_synthesized_mutation_signature`
  spells `f"{mutation_cls.__name__}Payload"` inside a `_lazy_ref`
  (second spelling — read first-hand at the working-tree body).
  Consumers by name: `mutations/sets.py::build_and_stash_payload`
  (passes `__name__`, stashes built name) and
  `mutations/resolvers.py::payload_cls_for` (reads the stash via
  `getattr`). Posited change (rename suffix): 2 definitions move.
  Owner I would choose: inputs.py (the materializer owns the grammar;
  the fields.py site cannot compose-by-name today — bind has not run at
  construction — so a pure `payload_type_name_for(base_name)` is owed at
  the family item). Slot rule `::payload_object_slot` + guard
  `::_RESERVED_PAYLOAD_ATTRS`: 1 definition each (sub-rules, same
  family). Auth fixed names (`LoginPayload`/`LogoutPayload` at
  `auth/mutations.py`, first-hand) are literal fixed names passed as
  explicit arguments, not grammar re-spellings — 0 edits on a suffix
  change.
- Operation descriptors. `::CREATE` / `::PARTIAL` defined here (C-change
  of token values: 1 definition here);
  `mutations/operations.py` owns the descriptor table (imports the
  tokens by name — read first-hand, 157 lines) and forms/serializer
  import them. Owner: operations.py. Indexed family, definition role
  here.
- Clear/register. `register_subsystem_clear(
  clear_mutation_input_namespace, owner="mutations.input_namespace",
  before_bind=True)` is a registering consumer of the bus owned at
  `registry.py`. Indexed family, consumer role here.
- Relation-id typing. `::relation_id_scalar` (GlobalID iff related
  primary is Relay-Node-shaped else raw-pk scalar) + cardinality wrap
  `::relation_id_annotation`: 1 definition. Consumers by call: form
  `::_model_less_relation_annotation` + triple builder (first-hand),
  serializer converter arms (call sites confirmed). Posited id-policy
  change: 1 definition moves. Owner: inputs.py (narrowest owner every
  write flavor already imports).
- Column-less spine. `::related_model_of_queryset` +
  `::require_queryset_related_model` (takes `missing=`) +
  `::annotate_queryset_relation`: 1 definition. Form + serializer
  column-less arms consume by call; queryset discovery + wording stay at
  flavors. Posited missing-model-policy change: 1 definition moves.
  Owner: inputs.py.
- Column classification. `::model_column_write_kind`: 1 definition
  here; KIND TOKENS live at `utils/inputs.py` (imported, 0 definitions
  here); form triple + serializer resolve + internal paths consume the
  token. Posited new-column-class change: 1 definition moves here.
  Owner: inputs.py for classification; tokens stay at utils.
- Column annotation. `::relation_input_annotation` +
  `::model_column_write_annotation` + `::model_column_input_annotation`:
  1 definition. Internal consumer `::build_mutation_input`; external
  consumers sets.py accepted-names/spec-synthesis + form triple
  (first-hand, with the load-bearing divergence: form `target_name` is
  the DECLARED name, never `<name>_id`) + serializer resolve path.
  Posited naming change (`<name>_id` → bare): 1 definition moves.
  Owner: inputs.py.
- Input identity. `::MutationInputShape` + `::mutation_input_shape` +
  `::mutation_input_type_name` (wrapper over the utils spine
  `::name_set_input_type_name`): 1 definition; C-change of shape
  identity moves 1 here, grammar change moves 0 here (1 at utils).
  Consumers: sets.py bind + merge + `input_type_name` seam + auth
  register. Owner: inputs.py (derive once; bind-scoped validity).
- Error envelope. `::FieldError`: 1 definition;
  `utils/errors.py::field_error` is the leaf-constructor consumer
  (function-local import); flavor pipelines carry the same class.
  Posited additive-member change: 1 definition moves. Owner: inputs.py;
  code vocabulary stays at utils-errors.
- Reverse map. `::mutation_input_field_specs` + `::_relation_field_index`:
  1 definition; sets.py bind + auth register consume by call.
  Form/serializer spec builders walk DIFFERENT bases (form fields /
  serializer fields) with different `target_name` semantics — adapters
  over the one `InputFieldSpec` record (owner utils-inputs, class
  confirmed in place), not copies. Owner: inputs.py.
- Normalizer / basis / requiredness / audit / namespace / generator /
  collisions / alias / key-pin / EXCLUDED. Each 1 definition, no second
  site after the matrix (details under FL1–FL10; twin-rejections R5–R7,
  R10–R11 each carry a concrete contract difference verified in-body:
  tuple-vs-frozenset rejects, opposite orders selection stated in both
  docstrings, three requiredness key spaces, disjoint ledgers, read-side
  vs write-side audit populations).

### Reconciliation vs W1

Agree on EVERY finding row (F1–F3, N1–N7, FL1–FL10, R1–R14), every
definition count, every owner, every role, and the zero-edit judgment.
One prose-precision delta, non-verdict-affecting: the artifact states a
"79-test" oracle inventory for `tests/mutations/test_inputs.py`; my
exact count is 75 `def test` functions (0 `parametrize`, 0 test methods
— both greps agree at 75). The oracles' independence does not depend on
the headcount (expectations are literal: `"CreateThingPayload"`,
`"DoActionPayload"`, `"node"`/`"result"`, `"__all__"`,
`StrawberryOptional`/`StrawberryList` shapes; SUT calls such as
`mutation_input_type_name(…)` are exercised behaviorally —
dedupe/inequality across two calls — never tautological
`expected = owner(…)` self-agreement). Worker 0 should record 75 in
`## Outcomes`. No other difference.

### Enumeration (member-by-member, own count)

Instrument re-run independently (`ast.Module.body` over the working
file): **52 top-level statements** (indices 0–51), agreeing with W1's
52. Walked every member against W1's table: 0 docstring → projection;
1–16 sixteen imports → no rule defined (0 definitions; C-owners
elsewhere); 17 `INPUTS_MODULE_PATH` → FL5; 18 `NON_FIELD_ERROR_KEY` →
FL9; 19 `EXCLUDED` → FL10; 20–21 `CREATE`/`PARTIAL` → F2; 22
`_frozenset_of_attr_names` → FL1; 23 `FieldError` → N6; 24 namespace
trio unpack → FL5; 25 `_audit_mutation_input_surface` → FL4; 26
`materialize_mutation_input_class` → FL5; 27
`clear_mutation_input_namespace` → FL5; 28 bus arm → F3; 29
`editable_input_fields` → FL2; 30 `input_field_required` → FL3; 31–32
id-typing pair → N1; 33–35 column-less spine → N2; 36
`relation_input_annotation` → N4; 37 `model_column_write_kind` → N3;
38–39 reverse-map pair → N7; 40–41 annotation pair → N4; 42
`_pascalize_token` alias → FL8 (zero source importers — only `.pyc`
matches + docstring mentions); 43–45 identity triple → N5; 46–47
collision pair → FL7; 48 `build_mutation_input` → FL6; 49–51 payload
guard/slot/builder → F1. 52/52 homed; every challenge C1–C24 ends in a
family, file-local, or rejection row. Coverage validated; assignment
endorsed.

### Matrix (against the real surface, mirrors first)

All six axes discharged, judged on reasons not claims: (1) forms + RF
mirrors read first, call by call — one substrate by import, divergences
each with a contract difference; (2) sync-only by probe + no
entry/pipeline surface — R1 sound; (3) F1 re-derived fresh from this
side (both spellings probe-asserted present on the working tree), input
names via the one descriptor, slot single-sited, tokens at utils; (4)
build-vs-decode share the `InputFieldSpec` record (owner utils),
per-flavor builders are adapters on different bases — N7+R12 correct;
payload build vs `payload_cls_for` compose via the stash; EXCLUDED tag
imported by name (resolver dispatch arms confirmed); (5) oracles are
independent literal expectations (see headcount note); projections
verified against bodies in the full read; (6) flavor family enumerated —
delete input-less on every path (`operation_takes_data` gates the field
ref AND `input_type_name` raises typed `ConfigurationError` for delete,
both read first-hand), model/form/serializer empty-guards each on its
own basis, EXCLUDED opt-in, M2M-optional where its contract lives. No
omission gap with a contract source behind it: 0 defects.

### Rulings: the 7 new families + F1

- N1 `write-relation-id-typing`: ENDORSE. Single-sited (C4 count 1);
  consumed independently of N4 by the column-less spine, so folding
  into N4 would mix two change axes (id-policy vs naming).
- N2 `column-less-relation-typing`: ENDORSE. Single-sited (C7 count 1);
  layered consumer of N1 with its own axis (model source /
  `missing=` wording) — separate family with a call edge, not a fold.
- N3 `model-column-write-classification`: ENDORSE. Single-sited (C6
  count 1); token spellings correctly left at utils-inputs.
- N4 `model-column-write-annotation`: ENDORSE. Single-sited (C5 count
  1); the form `target_name` divergence is a recorded adapter
  difference, not a second definition.
- N5 `generated-mutation-input-identity`: ENDORSE. Single-sited (C10
  count 1, C11 0 here); R8 adapter twin correctly separated — polarity
  verified first-hand (`!= CREATE` here vs `== PARTIAL` at the form
  wrapper) on different base-name sources.
- N6 `mutation-error-envelope`: ENDORSE. Single-sited (C14 count 1);
  additive contract + vocabulary split (codes at utils-errors) correct.
- N7 `mutation-input-reverse-map`: ENDORSE. Single-sited; R12 peers
  correctly rejected (different walk bases, different `target_name`
  semantics).
- F1 `mutation-payload-name`: CONFIRMED genuine duplication, count 2,
  re-derived from this side (`type(f"{mutation_name}Payload", …)` at
  inputs.py + `f"{mutation_cls.__name__}Payload"` inside fields.py
  `::_synthesized_mutation_signature`, both present on the working
  tree). Consolidation + gate stay with the family item — correctly not
  attempted here. No over-splitting: N1/N3/N4 each move under a change
  the others ignore; no under-splitting: nothing nominated shares one
  reason to change with another nominee.

### Rejections R1–R14

Each carries its contract difference + reconsideration trigger in the
artifact; all endorsed. Spot-verified: R1 (no resolver surface — import
list has none), R2 (`relay.GlobalID` only as returned annotation; zero
decode imports/calls), R4 (0 `permission` hits), R5 (spine returns
`tuple|None` and rejects sets/frozensets for order — first-hand),
R6 (opposite selection stated in BOTH docstrings — in-body), R8/R9
(polarity + descriptor-digest namer read first-hand), R10 (three
disjoint `INPUTS_MODULE_PATH` ledgers), R13 (`registry.get` injected as
`primary_of` at call sites), R14 (converters owned at types-converters,
called here). R3/R11/R12 rest on graze+docstring evidence proportionate
to a no-surface claim; triggers are precise enough to reopen on.

### Freshness (re-hashes by Worker 2)

Working tree == HEAD for the target: inputs.py `fc442047…` at both.
Dual fingerprints for all three concurrent hunks VERIFIED to the digit:
fields.py work `8c60a5c6…` / HEAD `cf518361…` (hunk shifts
`_synthesized_mutation_signature` but the F1 spelling at the body is
byte-intact — robust); forms-inputs work `436fcf42…` / HEAD
`55614839…` (hunk at `::_form_field_basis`, outside the N1/N3/N4
consumer call sites — robust); filters-inputs work `06797dc7…` / HEAD
`82b52d97…` (no traced line — robust). Re-hashed clean:
operations.py `16223c6b…`, sets.py `cffa29e5…`, resolvers.py
`3fd1e571…`, utils-inputs `ee31d360…`, utils-errors `3e25e93b…`,
test-inputs `6be1b081…`, rf-converter `32904418…`, auth
`dbe64995…`. Probe `68ad0954…` (untracked scratch, no HEAD
counterpart). Nothing stale.

### Zero-edit, gates, pending, coupling

`git diff bb08045685f9e0882990f3727ac6d237b60b0df2 --
django_strawberry_framework/mutations/inputs.py` EMPTY (re-run by me);
`git diff HEAD -- <target>` EMPTY; `git status --short` shows no touch
under the item's paths (only W1's two untracked scratch paths + this
cycle's concurrent dirt elsewhere, all preserved). No structural gate
established here — CORRECT per the file-item rule (gates owed at family
items); the in-tree `is`-identity rows would fail a behavior-preserving
hand copy by object-identity semantics, so their future negative
controls pass by construction. `## Pending execution`: absent —
correct (all proofs `static-reviewed`; pure sync generation decides no
ordering/transactional/async/ORM behavior). Sharded/Postgres
`inapplicable by construction`: ENDORSED (no database, alias, or
dialect decision in the target). Coupling: none — correct (zero edits).

### AGENTS.md prose check

Diff empty → no code-prose risk. Artifact: `path::Symbol` citations
throughout, no `path:NN` in standing prose (the one line-range sits in
this per-cycle scratchpad where raw ranges are allowed),
reference-style links with the bottom definition block intact, no
process provenance, no test-tier movement (zero-edit: nothing added,
removed, or rewritten). PASS.

## Defects (Worker 2)

None. Axis-6 sweep found every guard on its own basis with a supporting
contract; no docstring/body contradiction in the full read (lazy-path,
single-site, opposite-selection, and parked-globals claims all verified
at their sites); no layering contradiction (the utils-errors import
stays function-local to avoid the cycle). No security-impact findings.

## Judgment (Worker 2)

`Status: verified`. Zero-edit file item: 52/52 enumerated by an
independently re-run probe-equivalent count, six matrix axes discharged
against the real surface with mirrors first, F1 duplication re-derived
fresh (count 2, family item owns consolidation + gate), F2/F3 routed as
definition/consumer, N1–N7 endorsed as single-sited nominations, FL1–FL10
file-local, R1–R14 each with difference + trigger, all fingerprints
re-hashed (dual prints verified), no defects, no pending execution.
Worker 0: tick the plan item as verified (no pending execution), land
the rows below, remove scratch by explicit path after verification.

### Exact plan rows for Worker 0

File-item tick: `- [x] File `mutations/inputs.py` —
[dry-file-mutations__inputs.md](dry-file-mutations__inputs.md) —
verified (Run 0.0.15 2026-09-18-1; zero edits, no pending execution)`

Responsibility-index rows (append):

| `write-relation-id-typing` | `django_strawberry_framework/mutations/inputs.py::relation_id_scalar` (+ `::relation_id_annotation`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Family `write-relation-id-typing` | open |
| `column-less-relation-typing` | `django_strawberry_framework/mutations/inputs.py::annotate_queryset_relation` (+ `::related_model_of_queryset`, `::require_queryset_related_model`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Family `column-less-relation-typing` | open |
| `model-column-write-classification` | `django_strawberry_framework/mutations/inputs.py::model_column_write_kind` (kind tokens at `django_strawberry_framework/utils/inputs.py`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | Family `model-column-write-classification` | open |
| `model-column-write-annotation` | `django_strawberry_framework/mutations/inputs.py::model_column_input_annotation` (+ `::relation_input_annotation`, `::model_column_write_annotation`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/mutations/sets.py` | Family `model-column-write-annotation` | open |
| `generated-mutation-input-identity` | `django_strawberry_framework/mutations/inputs.py::mutation_input_shape` (+ `::MutationInputShape`, `::mutation_input_type_name`; name grammar at `django_strawberry_framework/utils/inputs.py::name_set_input_type_name`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/auth/mutations.py` | Family `generated-mutation-input-identity` | open |
| `mutation-error-envelope` | `django_strawberry_framework/mutations/inputs.py::FieldError` (code vocabulary at `django_strawberry_framework/utils/errors.py`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/utils/errors.py`, `django_strawberry_framework/mutations/resolvers.py`, `django_strawberry_framework/auth/mutations.py` | Family `mutation-error-envelope` | open |
| `mutation-input-reverse-map` | `django_strawberry_framework/mutations/inputs.py::mutation_input_field_specs` (+ `::_relation_field_index`) | `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/auth/mutations.py` | Family `mutation-input-reverse-map` | open |
| Attr-set normalizer (`_frozenset_of_attr_names`) | `django_strawberry_framework/mutations/inputs.py::_frozenset_of_attr_names` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Editable basis selector (`editable_input_fields`) | `django_strawberry_framework/mutations/inputs.py::editable_input_fields` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Create-requiredness predicate (`input_field_required`) | `django_strawberry_framework/mutations/inputs.py::input_field_required` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Input-surface audit (`_audit_mutation_input_surface`) | `django_strawberry_framework/mutations/inputs.py::_audit_mutation_input_surface` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Namespace lifecycle + module path | `django_strawberry_framework/mutations/inputs.py::materialize_mutation_input_class` (+ `::clear_mutation_input_namespace`, `::INPUTS_MODULE_PATH`) | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Generator body (`build_mutation_input`) | `django_strawberry_framework/mutations/inputs.py::build_mutation_input` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Generated-collision walk | `django_strawberry_framework/mutations/inputs.py::_reject_generated_input_collisions` (+ `::_GeneratedInputFieldName`) | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Token alias (`_pascalize_token`) | `django_strawberry_framework/mutations/inputs.py::_pascalize_token` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Non-field key pin (`NON_FIELD_ERROR_KEY`) | `django_strawberry_framework/mutations/inputs.py::NON_FIELD_ERROR_KEY` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |
| Exclusion tag (`EXCLUDED`) | `django_strawberry_framework/mutations/inputs.py::EXCLUDED` | `django_strawberry_framework/mutations/inputs.py` | File `mutations/inputs.py` | file-local |

Families lines (append under `## Families`):

- [ ] Family `write-relation-id-typing` — [dry-rule-write-relation-id-typing.md](dry-rule-write-relation-id-typing.md)
- [ ] Family `column-less-relation-typing` — [dry-rule-column-less-relation-typing.md](dry-rule-column-less-relation-typing.md)
- [ ] Family `model-column-write-classification` — [dry-rule-model-column-write-classification.md](dry-rule-model-column-write-classification.md)
- [ ] Family `model-column-write-annotation` — [dry-rule-model-column-write-annotation.md](dry-rule-model-column-write-annotation.md)
- [ ] Family `generated-mutation-input-identity` — [dry-rule-generated-mutation-input-identity.md](dry-rule-generated-mutation-input-identity.md)
- [ ] Family `mutation-error-envelope` — [dry-rule-mutation-error-envelope.md](dry-rule-mutation-error-envelope.md)
- [ ] Family `mutation-input-reverse-map` — [dry-rule-mutation-input-reverse-map.md](dry-rule-mutation-input-reverse-map.md)

F1/F2/F3 need no new rows (already indexed; site records confirmed
against the fingerprints above). `## Outcomes` correction: oracle
inventory is 75 test functions (not 79). Scratch to remove by explicit
path after verification:
`docs/dry/temp-tests/dry-file-mutations__inputs/probe_inputs_surface.py`
(read-only probe, reused not re-run into the tree — no Worker-2 scratch
created; no pytest run made or owed).
