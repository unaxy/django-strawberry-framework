# DRY review: `mutations/sets.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

The target is the write-side declarative surface: the `DjangoMutation` base
with its nested-`Meta` contract, the validate-then-register metaclass factory,
the declaration-ledger factory, the validated-snapshot record, the promoted
cross-flavor validation vocabulary, and the phase-2.5 bind drain. It defines
the model flavor end to end and serves the form, serializer, and auth flavors
by call, inheritance, and factory instantiation — never by copy. Every shared
helper below was traced to its call sites in [forms-sets][forms-sets],
[rest-sets][rest-sets], and [auth-mutations][auth-mutations]; every consumed
grammar was traced to its owner in [inputs][mutations-inputs],
[operations][mutations-operations], [permissions][mutations-permissions],
[resolvers][mutations-resolvers], [registry][registry],
[utils-inputs][utils-inputs], [utils-typing][utils-typing], and
[exceptions][exceptions].

Sites found: the target (definition owner for the seal pair, the ledger
factory, the validation vocabulary, the model base, the bind drain);
[forms-sets][forms-sets] (second ledger, second metaclass, two overriding
`_validate_meta` matrices, `build_input` / `input_type_name` /
`resolve_sync` / `resolve_async` overrides, rider of `bind_write_declarations`
and `bind_mutation_outputs`); [rest-sets][rest-sets] (third `_validate_meta`
matrix, `build_input` / `input_type_name` / seam overrides, rider of
`build_and_stash_input`); [auth-mutations][auth-mutations] (third ledger,
duck-typed snapshot twin, head-seal twin, `check_permission` reuse by call,
`run_write_pipeline_sync` rider); [fields][mutations-fields]
(`iter_mutations` consumer, `input_type_name` / `input_module_path` reader,
own `<Name>Payload` spelling); [finalizer][finalizer] (`bind_mutations`
caller at phase 2.5); [schema][schema] (`_mutation_meta.model` reader for the
write alias); [permissions][mutations-permissions] (`_mutation_meta`
reader in the walk); decoders in [resolvers][mutations-resolvers],
[forms-resolvers][forms-resolvers], [rest-resolvers][rest-resolvers],
[resource-policy][extensions-resource-policy] (`_input_field_specs` readers).
Connected behavior examined: Meta validation at class creation, seal refusal
at runtime, input merge and shape-dedupe at bind, payload materialization,
permission-walk snapshot discipline, hostile-dunder containment.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Read all three sibling flavors
   ([forms-sets][forms-sets], [rest-sets][rest-sets],
   [auth-mutations][auth-mutations]) plus [fields][mutations-fields] and
   [resolvers][mutations-resolvers]. Every shared sub-rule (20 imported
   names into forms, 15 into rest, 4 into auth) is consumed by call or
   inheritance; per-flavor `_validate_meta` matrices differ by contract
   (model keys vs `form_class` vs `serializer_class` keys, model operation
   vs create/update-only vs model-less) with the separation recorded at
   each owner. No mirrored body found. Discharged.
2. **Sync/async twins.** The target contains zero `async def` and zero
   `await` in code (prose mentions only; verified by grep over the file).
   The `resolve_sync` / `resolve_async` pair is produced by the single
   `resolver_seams` factory (FL10); the pipeline twins live in
   [resolvers][mutations-resolvers] under `shared-write-skeleton`. No twin
   in this file. Discharged.
3. **Derived rather than repeated knowledge.** Input names derive from the
   one `mutation_input_shape` descriptor (`input_type_name`,
   `_materialize_input_for`, `_materialize_merged_input`); expected custom
   attrs derive from `editable_input_fields` + `relation_input_annotation`
   (`_expected_input_attr_names`); payload names arrive as an argument to
   `build_payload_type` (`bind_mutation_outputs`, probe P2). The single
   re-spelling (`fields.py` `f"{name}Payload"`) is routed to F3. Discharged.
4. **Inverse / round-trip pairs.** Encode lives in
   [inputs][mutations-inputs] (`build_mutation_input`,
   `materialize_mutation_input_class`); this file holds only the bind-time
   hand-off (`mutation_input_field_specs` stash in `build_input` /
   `build_and_stash_input`) that the decoders
   ([resolvers][mutations-resolvers], [forms-resolvers][forms-resolvers],
   [rest-resolvers][rest-resolvers]) read. One grammar, file holds one
   half's hand-off, no second encoder/decoder. Discharged.
5. **Contracts restated in another medium.** Production (1 definition per
   rule, below); oracles: `tests/mutations/test_sets.py` (92 tests
   inventoried, each naming the typed reject or behavior it pins — oracle,
   never read from the owner); live tier `examples/fakeshop/test_query/`
   exercises the flavors over HTTP (tier cited, not enumerated — package
   surface is this item's backstop); projections: the module docstring and
   archived `docs/SPECS/spec-036-mutations-0_0_11.md`,
   `spec-038-form_mutations-0_0_12.md`, `spec-039-serializer_mutations-0_0_13.md`,
   `spec-040-auth_mutations-0_0_13.md` (describe, never own). Companion
   dirt `tests/mutations/test_sets.py` +80 (hostile-name oracles for the
   external hunk) attributed in `## Implementation (Worker 1)`.
   Discharged.
6. **Enforcement by omission.** Enumerated flavors (model, ModelForm,
   plain-form, serializer, auth-fixed) against the guard set. The model
   gate `require_model_class` is called by all three model-backed matrices
   (target, [forms-sets][forms-sets], [rest-sets][rest-sets]); permission
   defaults differ by contract (`DjangoModelPermission` vs `DenyAll` for
   the model-less flavor, spec-038 Decision 11, recorded at both owners);
   the plain form rejects any `operation` key; the serializer interleaves
   the lock/permission primitives in its own order by documented design.
   No member lacks a guard its contract requires. Discharged.

### Enumeration

Instrument: every name in `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-mutations__sets/probe_enumeration.py`).
Count: 61 top-level statements, 44 named definitional members, identical
set on the working tree and on `HEAD:`. Every member lands below; aspect
splits (`_ValidatedMutationMeta`, `bind_mutation_outputs`) are declared at
their primary row with a cross-reference.

| # | Member | Kind | Row |
|---|---|---|---|
| 1 | `COMMON_WRITE_META_KEYS` | key set | FL1 |
| 2 | `MODEL_BACKED_WRITE_META_KEYS` | key set | FL1 |
| 3 | `_ALLOWED_MUTATION_META_KEYS` | key set | FL1 |
| 4 | `_safe_frozenset_membership` | helper | FL2 |
| 5 | `require_non_delete_operation` | helper | FL3 (serves F4) |
| 6 | `reject_unknown_meta_keys` | helper | FL1 |
| 7 | `normalize_meta_field_selection` | helper | FL1 |
| 8 | `_hook_overridden` | helper | FL5 |
| 9 | `cached_build_input` | helper | FL6 |
| 10 | `build_and_stash_input` | helper | FL6 |
| 11 | `construction_kwargs` | helper | FL5 |
| 12 | `require_backing_class` | helper | FL4 |
| 13 | `require_subclass` | helper | FL4 |
| 14 | `require_model_class` | helper | FL4 |
| 15 | `resolve_meta_model` | helper | FL4 |
| 16 | `resolve_backed_model_or_raise` | helper | FL4 |
| 17 | `resolver_seams` | factory | FL10 (serves F11) |
| 18 | `_shape_build_cache` | cache instance | FL6 |
| 19 | `clear_mutation_shape_build_cache` | cache clear | FL6 |
| 20 | `DeclarationRegistry` | record | FL7 |
| 21 | `make_declaration_registry` | factory | FL7 |
| 22 | `make_meta_validating_metaclass` | head-seal factory | F2 |
| 23 | `_mutation_declaration_registry` | ledger instance | FL7 |
| 24 | `register_mutation` | ledger alias | FL7 (serves F9/F10) |
| 25 | `clear_mutation_registry` | ledger alias | FL7 (serves F9) |
| 26 | `iter_mutations` | ledger alias | FL7 |
| 27 | `_mutation_registry` | ledger store | FL7 |
| 28 | `_validate_input_class` | gate | FL12 |
| 29 | `_expected_input_attr_names` | derivation | FL12 (serves F7) |
| 30 | `_ValidatedMutationMeta` | slot-seal record | F1 (shape aspect FL8) |
| 31 | `_validate_permission_classes` | helper | FL9 |
| 32 | `validate_select_for_update` | helper | FL9 |
| 33 | `model_backed_permission_and_lock` | helper | FL9 |
| 34 | `DjangoMutationMetaclass` | metaclass binding | F2 |
| 35 | `DjangoMutation` | base (7 methods/attrs inside) | FL11 (serves F6/F11) |
| 36 | `_resolve_primary_type` | helper | FL13 (serves F8) |
| 37 | `_materialize_input_for` | helper | FL14 (serves F5) |
| 38 | `_materialize_merged_input` | helper | FL14 (serves F5) |
| 39 | `_validate_relation_override_types` | helper | FL15 (serves F7) |
| 40 | `_annotation_core_is_global_id` | helper | FL15 |
| 41 | `_strawberry_field_shape` | helper | FL15 |
| 42 | `bind_mutation_outputs` | helper | FL16 (pass-through aspect F3) |
| 43 | `bind_write_declarations` | helper | FL16 |
| 44 | `bind_mutations` | helper | FL16 (serves F10) |

`DjangoMutation` internals covered in FL11: `_resolve_model`,
`_validate_meta`, `build_input`, `input_type_name`, `resolve_sync` /
`resolve_async`, `check_permission`, `input_module_path`,
`_mutation_meta`, `_primary_type`, `_input_class`, `_payload_type_name`,
`_input_field_specs`, `_model_fields_by_attr`.

### Challenges

Each rule: posited changes with authoritative-definition counts. P1–P3 are
the executed read-only probes (`execution-verified`); oracle citations are
`static-reviewed` (suite execution is out of scope for this item: no
shared-tree pytest per dispatch, zero production edits to prove).

- **P1 enumeration identity.** Probe asserts the exact 44-name set on the
  working tree and on `HEAD:` blob `cffa29e5…`: both pass, identical.
  `execution-verified` (`uv run python
  docs/dry/temp-tests/dry-file-mutations__sets/probe_enumeration.py [path]`).
- **P2 payload pass-through.** Probe asserts zero code-level `Payload`
  name constructions in the target on both versions: both pass.
  `execution-verified`. Rejects the "second grammar" reading of F3 with
  the wrong result being a silent `<Name>Payload` fork.
- **P3 hostile-name coverage.** Probe lists consumer-controlled
  `X.__name__` reads in code: working tree zero (pass); `HEAD:` blob
  exactly six (`_validate_meta` name, `build_input` arg,
  `input_type_name` reject, `bind_mutation_outputs` arg, two seal
  messages) — the external hunk, nothing else. `execution-verified`.
  This is the mechanical hunk-touching boundary: F2/FL11/FL16 verdicts
  are pending-settle, all other rows robust-to-both.
- **C-seal-slot (F1).** Add a snapshot slot → 1 definition
  (`_ValidatedMutationMeta` slots + init). Change seal exception →
  2 sites (target pair + auth snapshot pair; family item counts whether
  one rule or two). Change seal wording → same 2 sites.
- **C-seal-head (F2).** Add a fourth ledger consumer → 0 definitions
  (call the factory — declaration, not method). Change head-seal
  semantics → 2 sites (factory pair + auth holder-metaclass pair;
  family item counts). Hunk-touching: wording aspect pending-settle.
- **C-payload (F3).** Change `<Name>Payload` grammar → 2 definitions
  (`build_payload_type` + fields.py spelling; the family consolidation);
  target pass-through moves 0 (P2). Count stands under both versions.
- **C-descriptors (F4).** New operation kind / new input-kind mapping →
  1 definition ([operations][mutations-operations] descriptors +
  derived maps); all readers move 0.
- **C-identity (F5).** Change shape identity → 1 definition
  (`mutation_input_shape`); bind cache key, generated name, field seam
  follow.
- **C-reverse-map (F6).** Change spec shape → 1 definition
  (`mutation_input_field_specs`); bind stash + decoders follow.
- **C-annotation (F7).** Rename relation convention → 1 definition
  (`relation_input_annotation`); validator + shape-lock follow.
- **C-registry-map (F8).** Change primary resolution → 1 definition
  ([registry][registry]); `_resolve_primary_type` follows.
- **C-clear (F9).** New subsystem state → 1 registration + clear at its
  owner; bus owned by [registry][registry].
- **C-finalize-gate (F10).** Change finalize gate → [registry][registry]
  `_check_mutable` + register's `is_finalized` reject (mirror; family
  item counts whether one rule or two).
- **C-skeleton (F11).** Change pipeline order → 0 definitions here (no
  pipeline body in this file); change seam delegation shape → 1 (FL10).
- **C-locals (FL1–FL16).** Each: change semantics → exactly 1 definition
  here; flavors follow by call. Spot counts verified first-hand:
  `cached_build_input` ordering (forms rides, serializer deliberately
  inline per spec-039 — recorded divergence, not a count of 2);
  `model_backed_permission_and_lock` pairing (ModelForm rides, serializer
  interleaves the two primitives — recorded divergence); key-set trio
  (forms/rest compose, never re-spell); ledger mechanics (three disjoint
  instantiations, one factory).

## Findings

Family rows reuse indexed names; `Owner` is the existing index owner
(this file owns F1/F2 per the index). Each finding carries its
robustness flag.

- **F1 `sealed-authorization-source` (slot seal).** Contract: the validated
  `Meta` snapshot is immutable after construction (sealed
  `__setattr__`/`__delattr__` raising `ConfigurationError`), because the
  snapshot is the per-request authorization source and a
  `has_permission` hook runs with the mutation class in hand. Variation:
  which record type is sealed. Definition here:
  [sets][mutations-sets]`::_ValidatedMutationMeta`. Mirror site:
  [auth-mutations][auth-mutations]`::_AuthMutationMetaSnapshot`
  (3-slot duck-typed holder, deliberately not this record — no model;
  contract difference recorded for the family item). Consumers:
  [permissions][mutations-permissions]`::run_permission_classes` (reads
  `permission_classes` off the snapshot),
  [resolvers][mutations-resolvers]`::authorize_or_raise` (transitive),
  [schema][schema] (reads `model`). Challenges C-seal-slot. Behavioral
  proof: `static-reviewed` + oracle tier (`test_sets.py` seal tests;
  hostile-name seal oracles in the external +80). Structural gate + owner
  decision belong to the family item. Freshness: sets.py `936f5ae7…`
  (HEAD `cffa29e5…`; seal record untouched by the hunk),
  [auth-mutations][auth-mutations] `dbe64995…`,
  [permissions][mutations-permissions] `54f770ae…`. **Robust-to-both.**
- **F2 `sealed-authorization-source` (head seal).** Contract: the class-head
  `_mutation_meta` is write-once (creation write honored, rebind/delete
  refused with `ConfigurationError`), closing the persistent bypass the
  slot seal closes at record level. Precise definition: the factory
  [sets][mutations-sets]`::make_meta_validating_metaclass` returning a
  `type` subclass whose `__new__` validates + registers, whose
  `__setattr__`/`__delattr__` guard the head, with pinned
  `__name__`/`__qualname__`/`__module__` for addressability; instances:
  `DjangoMutationMetaclass` (model ledger) and
  [forms-sets][forms-sets]`::DjangoFormMutationMetaclass` (plain ledger);
  `SerializerMutation` / `DjangoModelFormMutation` ride the model
  metaclass by inheritance (no third twin — verified). Mirror site:
  [auth-mutations][auth-mutations]`::_SealedAuthHolderMeta` (holder heads
  are framework-synthesized with pinned names `Login`/`Session`/
  `CurrentUser`, so its raw `cls.__name__` render is benign — consumer
  cannot inject a hostile name; intentional divergence, not a defect).
  Challenges C-seal-head. Freshness as F1. **Hunk-touching**
  (seal-message label expressions) → **pending-settle**; mechanism
  verdict deferred, not a defect.
- **F3 `mutation-payload-name`.** Contract: `<Name>Payload` grammar owned
  by [inputs][mutations-inputs]`::build_payload_type`. Pass-through site
  here: `bind_mutation_outputs` passes `_safe_class_name(mutation_cls)`
  as the base name and never spells `Payload` (P2, both versions).
  Second spelling at [fields][mutations-fields]`::_lazy_ref` call site
  (family item's consolidation). **Robust-to-both.**
- **F4 `mutation-operation-descriptors`.** Contract: operation vocabulary
  owned by [operations][mutations-operations] (descriptors + five derived
  maps). Enforcement sites here: `require_non_delete_operation` (FL3),
  `_validate_meta` operation gate, `_OPERATION_INPUT_OVERRIDE_ATTR`
  loop, `NON_DELETE_OPERATION_INPUT_KIND` reads. Note:
  [forms-sets][forms-sets] and [rest-sets][rest-sets] import
  `NON_DELETE_OPERATION_INPUT_KIND` *through* this module's import
  binding rather than from `mutations.operations` — same object, no
  second definition; layering wrinkle for the family item, not a count.
  **Robust-to-both.**
- **F5 `generated-mutation-input-identity`.** Consumed in
  `_materialize_input_for` / `_materialize_merged_input` /
  `input_type_name` via the one `mutation_input_shape` descriptor (cache
  key + type name + field seam single-sourced). **Robust-to-both.**
- **F6 `mutation-input-reverse-map`.** Consumed in `build_input`
  (`mutation_input_field_specs` stash + `_model_fields_by_attr`) and
  `build_and_stash_input`; read by the three flavor decoders. **Robust-to-both.**
- **F7 `model-column-write-annotation`.** Consumed in
  `_expected_input_attr_names` and `_validate_relation_override_types`
  via `relation_input_annotation` (registry-dependent id type passed
  `None` for the registry-independent name check, `registry.get(...)`
  for the bind-time shape lock). **Robust-to-both.**
- **F8 `type-registry-model-type-map`.** Consumed in
  `_resolve_primary_type` via `registry.get` + `registry.types_for`
  (zero-type vs ambiguous-type phrasing). **Robust-to-both.**
- **F9 `subsystem-clear-lifecycle`.** Enforcement: two
  `register_subsystem_clear` rows (`mutations.declarations`,
  `mutations.shape_cache`); bus owned by [registry][registry].
  **Robust-to-both.**
- **F10 `type-registry-finalize-gate`.** Enforcement: register's
  post-finalize reject (mirrors `TypeRegistry._check_mutable`) and the
  phase-2.5 `bind_mutations` entry called by
  [finalizer][finalizer]. **Robust-to-both.**
- **F11 `shared-write-skeleton`.** Relationship: consumer only — no
  pipeline body in this file. `check_permission` delegates to
  `run_permission_classes`; `resolve_sync`/`resolve_async` delegate to
  the flavor resolver entries via FL10; [auth-mutations][auth-mutations]
  rides `run_write_pipeline_sync` by call. **Robust-to-both.**
- **FL1 Meta-shape vocabulary.** One key-set trio + typo guard +
  field-selection normalize; forms/rest compose their allowed sets from
  these (never re-spell); per-flavor existence/exclusion checks stay at
  callers by recorded design. Challenge: new shared key → 1 edit here +
  per-flavor matrices opt in. **Robust-to-both.**
- **FL2 Hostile-hash membership.** `_safe_frozenset_membership` answers
  `False` when hashing the probe raises; two call sites in this file.
  No second site (permission-container parity in
  `_validate_permission_classes` is a different mechanism — R2).
  **Robust-to-both.**
- **FL3 Non-delete operation gate.** `require_non_delete_operation`
  owns the getattr + membership + shared-reject lookup for the form and
  serializer matrices. **Robust-to-both.**
- **FL4 Backing resolution + type-gate kit.** Five helpers; each called
  by both form and serializer matrices (verified call sites); the
  serializer's second ModelSerializer-specific gate stays local by
  design. **Robust-to-both.**
- **FL5 Construction-hook shape.** `_hook_overridden` (form waiver
  rides; serializer deliberately does not — auditable
  `Meta.injected_fields` instead, recorded at owner) +
  `construction_kwargs` (form + serializer defaults ride).
  **Robust-to-both.**
- **FL6 Per-shape build-cache discipline.** `cached_build_input`
  (guard-before-lookup; form seam rides), `build_and_stash_input`
  (materialize-then-stash tail; form + serializer ride), the model
  `_shape_build_cache` instance over
  [utils-inputs][utils-inputs]`::make_shape_build_cache` /
  `get_or_store_shape_build`; per-flavor dicts stay disjoint by design.
  **Robust-to-both.**
- **FL7 Declaration-registry mechanics + model ledger.**
  `make_declaration_registry` + `DeclarationRegistry` single-source the
  dedup / post-finalize reject / clear mechanics over three disjoint
  stores (model here, plain-form, auth); identity-scan dedup never
  dispatches consumer `__eq__` (pinned by hostile-eq oracles).
  **Robust-to-both.**
- **FL8 Snapshot record shape.** The `__slots__` tuple + constructor is
  the one place a new cross-flavor slot lands (form/serializer slots
  ride with `None` defaults on the model path — byte-unchanged by
  construction). Seal behavior belongs to F1. **Robust-to-both.**
- **FL9 Permission + lock validation.** `_validate_permission_classes`
  (immutable-tuple normalization, `DenyAll` parameterization for the
  model-less flavor) + `validate_select_for_update` +
  `model_backed_permission_and_lock` pairing. **Robust-to-both.**
- **FL10 Seam factory.** `resolver_seams` is the single site for the
  eight seam bodies (identity semantics asserted by routing tests);
  `with_id=False` serves the model-less flavor. **Robust-to-both.**
- **FL11 Model-flavor base.** `DjangoMutation`: `_resolve_model` seam,
  `_validate_meta` model matrix, `build_input`, `input_type_name`,
  seam assignment, `check_permission` delegation, `input_module_path`,
  bind slots. Form/serializer flavors override seams (different
  contracts, recorded at each override). **Hunk-touching**
  (`_validate_meta` label, `build_input` arg, `input_type_name` reject)
  → **pending-settle**.
- **FL12 Custom-input naming gate.** `_validate_input_class` +
  `_expected_input_attr_names`: strawberry-input check + generated-scheme
  conformance, single-sourced with the generator. No flavor twin (grep:
  definitions only here). **Robust-to-both.**
- **FL13 Primary-type error shapes.**
  `_resolve_primary_type` distinguishes zero-type from ambiguous-primary.
  No second site (auth's user-model bind carries its own actionable
  message by documented design). **Robust-to-both.**
- **FL14 Materialize pair.** `_materialize_input_for` (cache-by-shape,
  delete short-circuit) + `_materialize_merged_input` (inheritance
  merge under the canonical shape name; collisions fail loud).
  **Robust-to-both.**
- **FL15 Override shape-lock trio.** `_validate_relation_override_types`
  + `_annotation_core_is_global_id` + `_strawberry_field_shape`: bind-time
  GlobalID-core + list-depth lock. No second site. **Robust-to-both.**
- **FL16 Bind-drain trio.** `bind_mutation_outputs` + the shared
  `bind_write_declarations` drain (model + model-less riders) +
  `bind_mutations` model entry. **Hunk-touching**
  (`bind_mutation_outputs` payload-name arg) → **pending-settle**.

### Rejected candidates

- **R1 fields.py identity-scan twin.** [fields][mutations-fields]
  ``::_is_registered_mutation_target`` repeats the `is`-scan shape with
  an explicit prose pointer at this module's scan. Contract difference:
  registration dedup-append over a live ledger vs routing
  membership-test over a bind snapshot — different inputs, outputs, and
  reasons to change. Trigger: a shared `identity_contains` primitive
  proposed to cover both call shapes.
- **R2 Hostile-container banner.** `_safe_frozenset_membership`
  (hash-probe), `_validate_permission_classes` iteration/`getattr`
  tolerance, [exceptions][exceptions] renderers (attr-read) share a
  motive, not a mechanism. Trigger: one primitive parameterized over
  probe kind covering all three call shapes.
- **R3 querysets `_safe_class_name` twin.** Prior rejection re-checked
  first-hand: [utils-querysets][utils-querysets]`::_safe_class_name` is
  deliberately stricter (no `qualified` flag; non-string degrades to
  `_safe_type_name`, never `repr`). This file consumes the
  [exceptions][exceptions] variant. Trigger: the sealed-boundary variant
  relaxes to the repr fallback. Durable home: the querysets owner (prior
  artifact); recorded here so the hunk is not re-litigated as a fork.

## Defects

None. Two dissolved candidates, recorded so they are not re-raised:
(1) the auth head-seal twin's raw `cls.__name__` — benign because holder
names are framework-pinned literals (`Login`/`Session`/`CurrentUser`;
verified call sites), unlike consumer-declared mutation classes;
(2) hunk completeness — probe P3 shows zero remaining
consumer-controlled `__name__` reads in the working tree, so the six-site
conversion is complete within this file (sibling modules' renders are
outside this item).

## Pending execution

No `execution-deferred` behavioral proofs: probes P1–P3 ran
`execution-verified`; all other proofs are `static-reviewed` structural
counts with oracle citations, sufficient for a zero-edit file item. One
settle-gated re-run is owed (not a proof of this artifact's counts, but
of the hunk's landing): re-run P3 plus the hostile-name oracle file
after the external hunk settles —
`uv run python docs/dry/temp-tests/dry-file-mutations__sets/probe_safe_name_coverage.py`
(expect pass) and the `tests/mutations/test_sets.py` hostile-name
selection (needs a test-run authorization outside this item).

## Judgment

Zero-edit file item: 44 members enumerated and assigned (11 reused family
rows, 17 file-local rows, 3 rejections with triggers). The file owns the
`sealed-authorization-source` pair precisely (slot record + head-seal
factory, both defined, mirrors enumerated with contract differences for
the family item); serves the write-skeleton, payload-name, descriptor,
input-identity, reverse-map, annotation, registry-map, clear-lifecycle,
and finalize-gate families as a consumer/enforcement site only; holds no
second definition of any indexed rule. Three findings (F2/FL11/FL16) are
hunk-touching and carry pending-settle flags; all other rows are
robust-to-both. No defects. Ready for independent verification.

## Implementation (Worker 1)

Zero tracked changes made and none owed — file item, no consolidation in
scope. Own diff state: `git diff 1452f8ce02a9777931a6e2069b77cebbf2a6aa2d
-- django_strawberry_framework/mutations/sets.py
docs/dry/dry-file-mutations__sets.md` is empty (the artifact itself is
untracked, so outside the tracked diff by construction); no
`## Owned changes` ledger rows appended.

External hunk attributed first-hand (never edited/reverted/tidied):
working blob `936f5ae7…` vs HEAD blob `cffa29e5…` (HEAD commit
`9031cb3d`), six wording-only substitutions of raw `__name__` renders to
[exceptions][exceptions]`::_safe_class_name` at the seal-message pair,
the `_validate_meta` label, the `build_input` argument, the
`input_type_name` delete reject, and the `bind_mutation_outputs`
payload-name argument (full diff read; probe P3 reproduces the six sites
against the `HEAD:` blob mechanically). Companion dirt, likewise
untouched: `tests/mutations/test_sets.py` +80 hostile-name oracles
(worktree `8574a349…`) pinning the post-hunk wording; all other dirty
paths (`connection.py`, `extensions/resource_policy.py`,
`filters/inputs.py`, `filters/sets.py`, `forms/inputs.py`,
`mutations/fields.py` + test companions, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`) never inspected for content except
[fields][mutations-fields] lines 175–304 (worktree `64410c86…`,
external guard-trio hunk) read as a consumer/oracle neighbor. Per-finding
robustness flags are recorded in `## Findings`; F2/FL11/FL16 are
pending-settle (verdicts deferred to the hunk landing or reverting), all
other rows robust-to-both.

Item-scoped scratch (untracked, left for Worker 2):
`docs/dry/temp-tests/dry-file-mutations__sets/probe_enumeration.py`,
`probe_payload_spelling.py`, `probe_safe_name_coverage.py`,
`head_sets.py` (`git show HEAD:` dump for the dual-blob runs).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Read order kept: AGENTS.md, DRY.md,
worker-2.md, plan row (`mutations/sets.py`, unticked), working
target (1733 lines, blob `936f5ae7…`), item-scoped diff (0 bytes vs
`1452f8ce…`; HEAD-vs-work hunk +6/-6 read in full: wording-only
`__name__` to `_safe_class_name`, external concurrent work, untouched),
seal consumers first-hand (permission walk, finalizer, schema,
form/auth riders), then `## Findings`. No worker-memory read. No
source mutated (one `/tmp` dump of the `HEAD:` blob for dual-blob
probe runs only). No pytest per AGENTS.md: read-only probes +
inspection. Verdict: **verified** — full agreement, no blocking
correction. Settle rule stated explicitly below.

### Own trace (independently derived, own instruments)

Rules re-derived on the WORKING tree, with the count each posited
change forces and the owner I would choose:

| # | Rule | Sites + roles (mine) | Count | Owner (mine) |
|---|---|---|---|---|
| T1 | Slot seal (snapshot immutability) | [sets][mutations-sets]`::_ValidatedMutationMeta` (defines: slots + init + `__setattr__`/`__delattr__` seal); [auth-mutations][auth-mutations]`::_AuthMutationMetaSnapshot` (mirror: 3-slot duck holder, no model — different contract); [mutations-permissions][mutations-permissions]`::run_permission_classes` + [schema][schema] (consumers, read snapshot) | 1 here (+1 mirror at family) | sets.py |
| T2 | Head seal (class-head write-once) | [sets][mutations-sets]`::make_meta_validating_metaclass` (defines factory); `::DjangoMutationMetaclass` (model-ledger instance); [forms-sets][forms-sets]`::DjangoFormMutationMetaclass` (second instance = factory CALL, declaration not definition); [auth-mutations][auth-mutations]`::_SealedAuthHolderMeta` (separate holder; raw `cls.__name__` benign — holder names are pinned literals `Login`/`Session`, verified at call sites) | 1 here | sets.py |
| T3 | Payload-name grammar | [mutations-inputs][mutations-inputs]`::build_payload_type` (defines); here `::bind_mutation_outputs` (pass-through: passes `_safe_class_name(mutation_cls)` as arg, zero `Payload` spellings — P2 re-run); [mutations-fields][mutations-fields]`::_lazy_ref` call site (second spelling → family consolidation) | 2 (owner + fields site) | inputs.py |
| T4 | Operation descriptors | [mutations-operations][mutations-operations] (defines); here `::require_non_delete_operation` + `_validate_meta` gate + override-attr loop (consumers, 0 edits); forms/rest import `NON_DELETE_OPERATION_INPUT_KIND` through this module's binding (same object — layering wrinkle, not a count) | 1 at owner | operations.py |
| T5 | Input identity | [mutations-inputs][mutations-inputs]`::mutation_input_shape` (defines); here `::_materialize_input_for` / `::_materialize_merged_input` / `::input_type_name` (consumers: cache key + name + seam single-sourced) | 1 at owner | inputs.py |
| T6 | Input reverse map | [mutations-inputs][mutations-inputs]`::mutation_input_field_specs` (defines); here `::build_input` / `::build_and_stash_input` (stash); three flavor decoders (readers) | 1 at owner | inputs.py |
| T7 | Write annotation | [mutations-inputs][mutations-inputs]`::relation_input_annotation` (defines); here `::_expected_input_attr_names` (registry-independent name check, `None`) + `::_validate_relation_override_types` (bind-time shape lock, `registry.get`) | 1 at owner | inputs.py |
| T8 | Registry map + finalize gate + clear | [registry][registry] (defines: `get`/`types_for`, `_check_mutable`, clear bus); here `::_resolve_primary_type` (consumer), register post-finalize reject (mirror), `::bind_mutations` (phase-2.5 entry called by [finalizer][finalizer]), two `register_subsystem_clear` rows (enforcement) | 1 at owner per sub-rule | registry.py |
| T9 | Write skeleton | [mutations-resolvers][mutations-resolvers] (defines pipeline); here `::check_permission` (delegates to `run_permission_classes`), `resolve_sync`/`resolve_async` (delegate via `::resolver_seams` factory); auth rides `run_write_pipeline_sync` by call | 0 here | resolvers.py |
| T10 | Local rows FL1–FL16 | Each single-defined here; flavors compose by call (verified: `_validate_meta` overrides at forms:548,768 + rest:509; `build_input`/`input_type_name` overrides; three disjoint ledger instantiations over one factory) | 1 each here | sets.py (file-local) |

Reconciliation vs W1: full agreement on every home, count,
owner, and robustness flag. **Seal-ownership ruling:** yes,
slot+head are both defined HERE — the record class at `:754`
and the factory at `:568`, instantiated as
`DjangoMutationMetaclass` at `:1006`. The forms site is a
factory call (declaration, not a definition); the auth site is
a deliberately divergent holder, not a twin.

### Enumeration (member-by-member, own count 44)

Own `ast.Module.body` dump on the working tree: 61 statements,
44 names, in this order: `COMMON_WRITE_META_KEYS`,
`MODEL_BACKED_WRITE_META_KEYS`, `_ALLOWED_MUTATION_META_KEYS`,
`_safe_frozenset_membership`, `require_non_delete_operation`,
`reject_unknown_meta_keys`, `normalize_meta_field_selection`,
`_hook_overridden`, `cached_build_input`, `build_and_stash_input`,
`construction_kwargs`, `require_backing_class`, `require_subclass`,
`require_model_class`, `resolve_meta_model`,
`resolve_backed_model_or_raise`, `resolver_seams`,
`_shape_build_cache`, `clear_mutation_shape_build_cache`,
`DeclarationRegistry`, `make_declaration_registry`,
`make_meta_validating_metaclass`, `_mutation_declaration_registry`,
`register_mutation`, `clear_mutation_registry`, `iter_mutations`,
`_mutation_registry`, `_validate_input_class`,
`_expected_input_attr_names`, `_ValidatedMutationMeta`,
`_validate_permission_classes`, `validate_select_for_update`,
`model_backed_permission_and_lock`, `DjangoMutationMetaclass`,
`DjangoMutation`, `_resolve_primary_type`, `_materialize_input_for`,
`_materialize_merged_input`, `_validate_relation_override_types`,
`_annotation_core_is_global_id`, `_strawberry_field_shape`,
`bind_mutation_outputs`, `bind_write_declarations`,
`bind_mutations`. Identical to W1's table row-for-row; the
probe `EXPECTED` set passes on both blobs, so working set ==
`HEAD:` set. `DjangoMutation` internals land in FL11 as
declared. No unassigned member. Agree.

### Matrix (judged on the real surface)

1. Cross-flavor: forms/rest/auth read first-hand; 20/15/4-name
shared vocabulary imported FROM sets.py by call/inheritance;
`_validate_meta` matrices disjoint by contract (model keys vs
`form_class` vs `serializer_class`). Agree.
2. Sync/async: zero `async def` / `await` in code (one prose
mention at `:1329`). Seams via the FL10 factory; pipeline
twins live in resolvers. Agree.
3. Derived knowledge: names via `mutation_input_shape`;
expected attrs via `editable_input_fields` +
`relation_input_annotation`; payload base passed as an
argument. Single re-spelling routed to F3. Agree.
4. Round-trip: encode in inputs.py; this file holds only the
bind-time stash hand-off the decoders read. Agree.
5. Media: oracles `tests/mutations/test_sets.py` (92 `def
test` counted) assert literal messages (e.g.
`match="sealed and cannot be rebound"`), never read the
owner; test imports are scenario-setup (factories/validators
to build cases), expectations are literals — no oracle
rewritten. Live tier cited; projections are the module
docstring + archived specs. `+80` hostile-name companion
dirt confirmed external. Agree.
6. Omission: model gate shared by all three model-backed
matrices; permission defaults differ by contract (`DenyAll`
model-less, spec-038 Decision 11); plain form rejects any
`operation`; serializer interleaves by documented design.
Agree — 0 defects.

### Counts, roles, equivalence

All definition counts confirmed; spot-verified first-hand:
ledger = three disjoint instantiations over one factory;
key-set trio composed-never-respelled; cache
guard-before-lookup ordering as documented; permission/lock
pairing divergence (serializer interleaves) recorded, not a
second definition. Equivalence (principle 8): vacuous-accept
— zero-edit item, no consolidation proposed, nothing
ordering/transactional/async decided here.

### Zero-edit + routing

Own-diff `git diff 1452f8ce… --
django_strawberry_framework/mutations/sets.py` is 0 bytes;
`git status` dirt under the item's paths is the external hunk
plus this untracked artifact — nothing by this item. 11
family rows all already indexed; 17 file-local rows recorded;
3 rejections with triggers. A file item owes no production
edit; none demanded.

### Rejections: agree all three (verified first-hand)

- **R1 identity-scan twin: agree.** Prose pointer exists at
fields.py `:177` docstring → `sets.py::make_declaration_registry`
#"Identity-scan dedup". Contract difference real (ledger
dedup-append vs routing membership over a bind snapshot);
trigger (shared `identity_contains` primitive) concrete.
- **R2 hostile-container banner: agree.** Motive, not
mechanism: hash-probe vs iteration/`getattr` tolerance vs
attr-read renderers. Trigger (one primitive parameterized
over probe kind) concrete.
- **R3 querysets `_safe_class_name` twin: agree.** Strictness
difference verified at both docstrings (querysets `:142`
deliberately stricter, no `qualified` flag, degrades to
`_safe_type_name`; exceptions `:105` shared variant with
`repr` fallback); target consumes the exceptions variant
(`:55` import). Trigger concrete; durable home is the
querysets owner. The hunk is not a fork.

### Fingerprints (re-hashed myself; dual blobs)

W1's three match: sets.py work `936f5ae7…`, `HEAD:`
`cffa29e5…` (via `git rev-parse HEAD:` — agrees),
[auth-mutations][auth-mutations] `dbe64995…`,
[mutations-permissions][mutations-permissions] `54f770ae…`.
P3 dual-blob re-run: work zero hits (pass); `HEAD:` exactly
six at `:642`, `:651`, `:1105`, `:1243`, `:1282`, `:1661` =
W1's six sites. Extended worktree hashes (consumer context):
inputs `fc442047…`, operations `16223c6b…`, fields
`64410c86…` (external hunk, neighbor only), resolvers
`3fd1e571…`, registry `9cc8bb55…`, finalizer `77fd9a2d…`,
schema `2f727321…`, forms-sets `98ef150d…`, rest-sets
`2c7117d6…`, exceptions `e06b0b7f…`, utils-inputs
`ee31d360…`, utils-typing `de6309f6…`, querysets
`1539b66c…` (post-ff, external).

### Gates, Pending, settle ruling

No gates owed at a zero-edit file item — correct. F1/F3
honestly defer structural gate + negative control to the
family items; accepted as carry (`sealed-authorization-source`
+ `mutation-payload-name` owe them). `## Pending execution`
lists one settle-gated re-run with exact commands — accepted
as the settle instruction, NOT a deferred proof of this
artifact's counts (every proof is discharged: P1–P3
`execution-verified`, the rest `static-reviewed`). Ruling:
plain `verified` per the fields.py precedent, NOT `verified,
pending execution`. **Settle rule:** F2/FL11/FL16 are
verified-on-working-bytes-only; the hunk landing or
reverting is a fingerprint change that reopens those three
rows — Worker 0 then re-runs P3 plus the hostile-name oracle
selection and re-verifies them. All other rows are
robust-to-both and stand without re-run.

### AGENTS.md prose: clean

Item diff empty → no production prose risk. Artifact reuses
existing link ids only (no new definitions); citations are
`path::Symbol`; oracles at the package tier
(`tests/mutations/test_sets.py`, inline construction —
library acceptance, no services surface) with the live tier
cited. Concurrent dirt preserved; no commit.

## Defects (Worker 2)

None. The two dissolved candidates stay dissolved: (1) auth
head-seal raw `__name__` confirmed benign (holder names are
framework-pinned literals — `Login` / `Session` verified at
[auth-mutations][auth-mutations] call sites); (2) hunk
completeness confirmed (P3: zero remaining
consumer-controlled `__name__` reads in the working tree).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[extensions-resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rest-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[schema]: ../../django_strawberry_framework/schema.py
[sets]: ../../django_strawberry_framework/mutations/sets.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-typing]: ../../django_strawberry_framework/utils/typing.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
