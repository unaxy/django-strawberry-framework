# DRY review: `forms/resolvers.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a reused family row (re-derived fresh, never inherited),
a file-local record with its proving challenge, or a recorded rejection with
contract difference + trigger + durable home. Zero production edits; zero
tracked files changed.

## System trace

Target (`django_strawberry_framework/forms/resolvers.py`, 605 lines, blob
`4edb984b299b4e2a71492e73382558b01865f48a`; absent from the item-scoped
diff, target CLEAN): the form-flavor write runtime (spec-038 Decision 8),
the sibling of [mutations-resolvers] (the 036 model pipeline) and
[rf-resolvers] (the 039 serializer pipeline). It DEFINES the form relation
decode coloring (`_decode_form_relation_single` /
`_decode_form_relation_multi` over `empty_values` skip +
`to_field_name` projection), the kind-split decode into
`provided_data` / `provided_files` (`_decode_form_data`), the
partial-update reconstruction (`_reconstruct_partial_data`), the form
error mapping (`_form_errors_to_field_errors`), the shared decode/write
steps (`_modelform_decode_step`, `_bound_form_or_field_errors`,
`_modelform_write_step`, `_plain_form_write_step`), and the flavor
dispatch (`_run_form_pipeline_sync` on `mutation_cls._primary_type`).
It CONSUMES (by name, P3-proved 15/15) the skeleton + entries +
save-mapper in [mutations-resolvers] (`run_write_pipeline_sync`,
`make_resolver_entries`, `save_or_field_errors`), the recourse template
in [querysets] (`sync_pipeline_recourse`), the write phase in
[write-tx] (`pipeline_write_phase`), the decode spine in [write-values]
(`decode_field_handlers`, `decode_provided_fields`,
`decode_visible_relation`, `materialize_relation_id_container`), the
flat error mapper in [errors] (`validation_error_to_field_errors`,
lazy import), and `model_to_dict`. It is CONSUMED by the bind in
[forms-sets] (which delegates both bases' `resolve_sync` /
`resolve_async` seams here by name) and by the input builder in
[forms-inputs] (which stashes the `InputFieldSpec` reverse map this
file reads, never rebuilds).

Connected code read for judgment, outside the item: the model twin FIRST
(whole [mutations-resolvers], 1339 lines) + the serializer mirror
(whole [rf-resolvers], 2432 lines); the owners ([write-values] full
read, [write-tx] `pipeline_write_phase` region, [querysets]
`sync_pipeline_recourse` + `visible_related_object` /
`related_visibility_queryset_or_default` regions, [errors]
`validation_error_to_field_errors` region, [mutations-inputs]
`model_column_write_kind` region); the build side ([forms-inputs]
whole read earlier this cycle via its verified artifact,
[forms-sets] delegation regions); oracles in
[test-forms-resolvers] (66-function inventory) and the factory gate in
[test-mutations-resolvers]
(`test_write_flavors_share_resolver_entry_factory`); contract source
spec-038 Decision 7/8 (relation visibility on every branch, authorize
before decode, partial transport not partial validation, one boundary).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P5, all
read-only, all green; commands under `### Challenges`).

1. **Cross-flavor policy mirroring.** Searched, all three resolvers read
whole FIRST. P2 proves the sharing shape by behavior, not tokens: all
three module-entry pairs come from one `make_resolver_entries` call
each (model `_run_pipeline_sync`, form `_run_form_pipeline_sync`,
serializer `_run_serializer_pipeline_sync`); all three recourse
constants are calls of one `sync_pipeline_recourse` template with
distinct nouns (`"DjangoMutation"` / `"form mutation"` /
`"serializer mutation"`); all three ride one
`run_write_pipeline_sync` skeleton supplying only decode/write
steps. Decode spine per flavor: form + serializer ride
`decode_visible_relation` (per-element, object-returning);
model + serializer ride `decode_visible_relation_ids` (batched
`pk__in`); model alone never touches the single spine, form alone
never touches the batched compose — each absence is the documented
projection need (form needs the object for `to_field_name`). Save
mapping: model + form ride `save_or_field_errors`; serializer owns
its three-branch save mapper (DRF `ValidationError.detail` vs
Django `ValidationError` vs `IntegrityError` — disjoint exception
contracts, J-adjacent, no merge posited). What SHOULD be shared
already is: skeleton, entries, boundary, recourse sentence,
kind-walk, single spine, scalar leaf, container guard, flat mappers,
write phase. Verdict: one rule per surface; see F1--F3, R1--R5,
J1--J3.
2. **Sync/async twins.** Compared by behavior, not shape. Instrument
(P1): zero `AsyncFunctionDef`, zero `await` in the target. The async
surface is not a twin body: `resolve_form_async` is the factory's
entry running the SAME `_run_form_pipeline_sync` through the shared
`run_pipeline_async` boundary (one
`sync_to_async(thread_sensitive=True)` call — factory body read).
There is no second form pipeline to drift; the single-sync-body
shape is the DRY.md principle-5 write-pipeline answer (no awaits
may interleave inside the transaction). No twinship, no finding.
3. **Derived rather than repeated knowledge.** Searched. The
`related_model` is threaded as a parameter at both relation
decoders (never re-derived: zero code-level `queryset` reads in
the target — every `queryset` hit is docstring prose; zero
`InputFieldSpec(` constructions — specs arrive bind-stashed via
`mutation_cls._input_field_specs`). `get_form_fields()` is read
by name at both consumers (`_decode_form_data`,
`_reconstruct_partial_data`). The recourse is computed from the
template (P4 equality-proved), never re-spelled. No fact
re-derived.
4. **Inverse / round-trip pairs.** Searched, both directions
verified. Encode (field -> spec in [forms-inputs],
single construction site) pairs with decode (spec -> form-keyed
payload here via `spec.target_name` / `spec.kind` /
`spec.related_model`, read never rebuilt). File routing pairs
with construction: `FILE` -> `provided_files` here lands in the
bound form's `files=` (`_bound_form_or_field_errors`), the
deliberate DRF contrast (serializer lands FILE in `data`). One
grammar per pair, correctly separated halves.
5. **Contracts restated in another medium.** Counted 1 definition
per rule; everything else classified: module docstring
(projection, clause-verified incl. the authorize-before-decode
ordering, the per-element rationale, the null-M2M divergence,
the G2 re-fetch ride); spec-038 Decisions 7/8 (contract source);
[test-forms-resolvers] rows (oracles spelling literals: form-key
landing, visibility rejection, `to_field_name` preservation,
file exclusion, empty-value pass-through, container errors,
one-shot generators — no oracle iterates an owner table);
[test-mutations-resolvers] factory gate (pins the shared
entries). No medium holds an independently maintained copy.
6. **Enforcement by omission.** Kind coverage enumerated against
the builder: `SCALAR` (default scalar handler), `RELATION_SINGLE`
/ `RELATION_MULTI` (relation handlers), `FILE` (`file_dest`)
— total. `EXCLUDED` (spec-040 D6) falls to the scalar handler,
but form specs can never carry it: the form builder classifies
via `model_column_write_kind`, which returns only the four
kinds (region read; `EXCLUDED` is stashed only by the
register path the form builder never calls) — unreachable by
construction, not a gap. Null/empty arms covered per decoder
(P4 re-proved the DB-free arms); the plain flavor's missing
locate is the skeleton's `_primary_type is None` branch, not an
omission here. No missing guard with a contract source — no
defect filed.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-forms__resolvers/p1_ast_census.py`),
count **24**. Every member lands below; R = file-local finding,
F = reused/proposed family row (non-membership checked, never
inherited), J = recorded rejection.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | verified clause-by-clause |
| 2 | `from __future__` | machinery import | consumer (exempt) |
| 3 | `typing.Any` | annotation import | consumer |
| 4 | `django.forms` | key-space import | R3 consumer |
| 5 | `FieldDoesNotExist, ObjectDoesNotExist, ValidationError` | guard imports | R1/R3/R4 consumers |
| 6 | `model_to_dict` | reconstruction import | R3 consumer |
| 7 | mutations.resolvers import (3 names) | skeleton imports | F3 consumers |
| 8 | `sync_pipeline_recourse` import | template import | F1 consumer |
| 9 | `pipeline_write_phase` import | phase import | R5 consumer (owner upstream) |
| 10 | write_values import (4 names) | spine imports | R1/R2 consumers (P3: all referenced) |
| 11 | `_FORM_ASYNC_RECOURSE` | recourse constant | F1 (REUSE consumer) |
| 12 | `_to_form_key_value` | projection helper | R1 |
| 13 | `_is_empty_form_value` | skip helper | R1 |
| 14 | `_decode_form_relation_single` | relation decoder | R1 |
| 15 | `_decode_form_relation_multi` | relation decoder | R1 (+ J3 member) |
| 16 | `_decode_form_data` | kind-split decode | R2 |
| 17 | `_reconstruct_partial_data` | partial reconstruction | R3 (+ J1 member) |
| 18 | `_form_errors_to_field_errors` | error mapping | R4 |
| 19 | `_modelform_decode_step` | shared decode step | R2/R3 composition |
| 20 | `_bound_form_or_field_errors` | construct/validate helper | R5 |
| 21 | `_modelform_write_step` | ModelForm write step | R5 |
| 22 | `_plain_form_write_step` | plain write step | R5 |
| 23 | `_run_form_pipeline_sync` | flavor dispatch | R5 + F3 (rider) |
| 24 | `resolve_form_sync, resolve_form_async` assign | module entries | F3 (factory product) |

No member unassigned. Prior-cycle trigger notes re-checked fresh,
never inherited: the converter item's requiredness/value-object
rows (this file consumes neither table nor decision — kind only,
via specs); the inputs item's R6 (this file reads
`target_name`/`kind`/`related_model` without re-derivation,
re-proved by grep); the utils-querysets index rows below (F1/F2
re-derived from this side via P2--P4, never assumed).

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, not counted. Executed
probes are read-only files under
`docs/dry/temp-tests/dry-file-forms__resolvers/` run with
`uv run python` from the repo root; NO shared-tree pytest, NO
source mutation (so no workspace copy was owed), NO database opened
by any probe (P4 runs with empty `DATABASES`, DB-free arms only).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | change the empty-value skip (e.g. `""` becomes a decodable id) | **1** (R1: single + multi move together) | serializer `None`-only skip stays; skip oracles |
| C2 | change the `to_field_name` projection rule | **1** (R1 helper + both decoders) | serializer `obj.pk` projection stays; preservation oracles |
| C3 | change FILE routing (`files=` vs `data=`) | **1** (R2 `file_dest`) | serializer `data` routing stays (deliberate contrast); file oracles |
| C4 | change the reconstruction shape (new relation kind) | **1** (R3) | model `setattr` / serializer `partial=True` stays (J1); reconstruction oracles |
| C5 | change the form-error mapping (new bucket) | **1** (R4) | flat mapper owner + serializer recursive flattener stay; envelope oracles |
| C6 | add a third form base (new dispatch arm) | **1** (R5 branch) | skeleton + factory stay; pipeline oracles |
| C7 | change the recourse sentence | **0 here** (template owner); noun **1 here** | wording oracles |
| C8 | change the pipeline order (authorize-before-decode) | **0 here** (skeleton owner) | all three riders follow |
| C9 | change the visibility query | **0 here** (chain owner); projection **1 here** (counted C2) | form + serializer decoders follow |
| C10 | unify the three partial-update mechanisms | **refused** (J1: disjoint validation substrates) | -- |
| C11 | batch the form multi decode onto the `pk__in` compose | **refused** (J2: form needs the object) | -- |
| C12 | unify null-M2M with the model reject | **refused** (J3: Django form semantics) | -- |

Probe commands + what each proved (every probe `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-forms__resolvers/p1_ast_census.py`
  -- 24 members, 0 async defs, 0 awaits (matrix axis 2 +
  enumeration instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__resolvers/p2_flavor_mirror.py`
  -- one factory call per flavor with its own sync body; three
  recourse calls with distinct nouns; skeleton ridden by all
  three; single spine in form+serializer only, batched compose in
  model+serializer only, `save_or_field_errors` in model+form
  only. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__resolvers/p3_delegation.py`
  -- 15/15 non-future imports referenced (incl.
  `save_or_field_errors` x2, `pipeline_write_phase` x2); eleven
  indexed-machinery symbols have zero definitions here.
  `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__resolvers/p4_behavior.py`
  -- recourse equals the template output; default/custom/hostile
  empty-values; `to_field_name` set/unset/guarded-failure arms;
  multi null/empty clear + text-container in-envelope rejection,
  all with empty `DATABASES`. `execution-verified`, no database.
- `uv run python docs/dry/temp-tests/dry-file-forms__resolvers/p5_gates.py`
  -- the factory-sharing oracle exists and pins all three entries
  to `__name__ == 'resolve_sync'`. `execution-verified`.
- Grep (inline): zero code-level `queryset` reads, zero
  `InputFieldSpec(` constructions, `related_model` threaded as a
  parameter only. `execution-verified`.

## Findings

### F1 -- `sync-boundary-recourse-wording` (REUSE as consumer, index: rejected)

- **Contract + variation.** The three write flavors raise one
  `SyncMisuseError` sentence, byte-identical except the flavor
  subject. Varies by rewording (C7 counts 0 here) or renaming a
  subject (counts 1 here).
- **Sites + roles.** Owner:
  [querysets]`::sync_pipeline_recourse` (template). Target role:
  consumer — member 11 is the single call
  `sync_pipeline_recourse("form mutation")` (P2: exact arg;
  P4: output equality-proved). Siblings:
  [mutations-resolvers]`::_MUTATION_ASYNC_RECOURSE`,
  [rf-resolvers]`::_SERIALIZER_ASYNC_RECOURSE` (same shape,
  P2). The index marks this family `rejected`: the
  per-flavor named constant stays (a full merge into one
  constant would erase the subject); the sentence is
  single-sourced. This file already matches that outcome —
  no change proposed, no index change proposed.
- **Challenges.** C7 counts 0-here/1-noun.
- **Owner + lifetime.** Template upstream (principle 7: the
  narrowest owner all three flavors can import without a
  sibling dependency). Nothing stored (module constant read
  per raise).
- **Migration.** None (already compose by name; file item owes
  no edit).
- **Distinct behavior.** None within the family — the noun is
  the documented variation, not a divergence.
- **Behavioral proof.** P2 + P4 (`execution-verified`).
  Misuse oracles in [test-forms-resolvers]
  (`test_sync_create_meeting_async_get_queryset_raises_sync_misuse`)
  `static-reviewed`.
- **Structural gate.** The misuse oracle fails a wording drift
  that drops the recourse (it asserts the message).
- **Freshness.** Target
  `4edb984b299b4e2a71492e73382558b01865f48a`;
  [querysets] `1539b66c9ce9a659e1dc5f6bf1029b15d6868587`;
  HEAD `9031cb3d`.

### F2 -- `related-object-visibility-recheck` (transitive consumer, index: open)

- **Contract + variation.** Every relation id resolves through
  the related primary's visibility `get_queryset`; hidden and
  missing are indistinguishable. Varies on the query (C9
  counts 0 here).
- **Sites + roles.** Owner: [querysets]
  `::related_visibility_queryset_or_default` (via
  `::related_visibility_queryset`). Target role: transitive
  consumer, two hops — member 14 calls
  [write-values]`::decode_visible_relation`, which calls
  [querysets]`::visible_related_object`, which opens with
  the owner (chain read end to end; P3: zero visibility
  definitions here). The per-element (not batched) ride is
  deliberate: the form needs the OBJECT for the
  `to_field_name` projection (J2). No index change proposed
  (row already covers this file).
- **Challenges.** C9 counts 0-here/1-projection (C2).
- **Owner + lifetime.** Chain upstream. Nothing stored.
- **Migration.** None.
- **Distinct behavior.** Per-element mapping vs the
  model/serializer batched `pk__in` — the object need,
  recorded at the spine
  ([write-values]`::decode_visible_relation` docstring) and
  the module docstring.
- **Behavioral proof.** P2 (spine-use shape) +
  `static-reviewed` visibility oracles
  (`test_relation_visibility_relay_multi_hidden_rejected`,
  `test_decode_form_relation_single_uncoercible_raw_pk_is_field_error`,
  `test_visible_related_object_no_primary_uses_default_manager`).
- **Structural gate.** The hidden-rejected oracle fails a
  visibility bypass (a hidden id attaching would return
  `ok: true` where the oracle pins the envelope).
- **Freshness.** Target as in F1;
  [write-values] `d28587c7c8d9f0d25e0a01bf289a63d9c3291728`;
  [querysets] as in F1.

### F3 -- `shared-write-skeleton` (PROPOSED family; rider, not owner)

- **Contract + variation.** One skeleton owns the
  `transaction.atomic()` boundary + locate preamble +
  authorize-before-decode ordering + payload tail; each flavor
  supplies only decode/write steps (and delete its tail seam).
  One entry factory owns the `UNSET` normalization + the
  single-`sync_to_async` async boundary. Varies per flavor
  middle (C6/C8 count 0 here for order/boundary, 1 here for
  the branch).
- **Sites + roles.** Owner:
  [mutations-resolvers]`::run_write_pipeline_sync` (skeleton),
  `::make_resolver_entries` (entries),
  `::run_pipeline_async` (boundary). Target role: rider —
  member 23 supplies the form decode/write closures keyed on
  `_primary_type`; member 24 takes the factory product
  (P2: `make_resolver_entries(_run_form_pipeline_sync)`).
  Sibling riders: model (`_run_pipeline_sync` + delete
  seam), serializer (`_run_serializer_pipeline_sync`).
  Sub-rules for Worker 0 to index separately: skeleton,
  entry factory, async boundary.
- **Challenges.** C6 counts 1-branch/0-skeleton; C8 counts 0
  here.
- **Owner + lifetime.** Skeleton module (principle 7: the
  model pipeline is the origin; both later flavors import
  from it, never the reverse — dependency direction wins).
  Nothing stored (closures per call).
- **Migration.** None (already composed by name; file item
  owes no edit).
- **Distinct behavior.** The `_primary_type is None`
  plain-form branch (no locate, no object slot, `{ ok: true }`
  tail) vs the ModelForm branch — recorded at member 23's
  docstring.
- **Behavioral proof.** P2 (rider shape) + P5 (gate witness)
  (`execution-verified`); `static-reviewed` pipeline oracles
  (`test_plain_form_pipeline_rides_shared_write_skeleton`,
  `test_plain_form_expired_deadline_rejects_before_perform_mutate_write`).
- **Structural gate.** The factory-sharing oracle
  (`test_write_flavors_share_resolver_entry_factory`)
  fails an entry-shape drift on any flavor (it pins all
  three `__name__`s); the skeleton-ride oracle fails a
  boundary re-implementation.
- **Coupling.** None introduced.
- **Freshness.** Target as in F1;
  [mutations-resolvers]
  `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`;
  [rf-resolvers]
  `8024703ec0fb09758daeec0585e0065de1c61fc3`;
  [test-mutations-resolvers]
  `4aa8e51e8af08697b702f47be8425c36b3c8c485`.

### F4 -- `one-sync-boundary` (checked non-membership)

This file does NOT join the family beyond the F3 boundary
ride: zero `run_in_one_sync_boundary` / `run_pipeline_async`
definitions or calls (P3 defscan clean); the async boundary
participation is composed via the factory product (member 24),
whose body lives in the covered [mutations-resolvers]. No
index change proposed.

### F5 -- `sealed-execution-queryset` (checked non-membership)

This file does NOT join the family: zero seal / `base_queryset`
/ `model_for` / `initial_queryset` definitions or calls (P3
counts: all zero); the alias-pinned execution context is
opened by the skeleton, not here. No index change proposed.

### F6 -- `active-input-permission-facade` (checked non-membership)

This file does NOT join the family: zero `permission` /
`traversal` machinery definitions; authorization lives in the
skeleton's `authorize_or_raise` seam (called, never
re-implemented). No index change proposed.

### R1 -- Form relation decode coloring (file-local)

- **Contract + variation.** Members 12--15: every relation id
  (Relay `GlobalID` or raw pk) is type-checked, resolved to
  the visible object, and projected to the form-key value —
  with the form coloring: the `empty_values` skip (member 13;
  explicit null/empty is a clear/no-value for the bound form's
  own validation to decide) and the `to_field_name`
  projection (member 12; `serializable_value(to_field_name)`
  else `obj.pk`, failures guarded to `pk`). Multi maps
  single per element (first error short-circuits); an
  empty/null whole value clears to `[]` without iterating
  `None`. Varies on skip/projection (C1/C2 count 1).
- **Sites + roles.** Definition here (skip + projection +
  per-element shape). Spine owner: [write-values]
  (type-check + visibility + store). Oracles: empty-value
  pass-through, `to_field_name` preservation (M2M + FK),
  hostile-`serializable_value`, unhashable-empty,
  one-shot-generator, non-collection rejection rows (P4
  re-proved the DB-free arms).
- **Challenges.** C1/C2 count 1.
- **Owner + lifetime.** This file (the form-coloring home;
  per-call values, nothing stored).
- **Distinct behavior.** Null-M2M clears where the model
  path rejects (`_relation_null_error` — "use `[]`, not
  `null`"): a bound `ModelForm` follows Django form
  semantics (empty clears optional, required errors via
  `is_valid()`), not the model replace-set stance. Recorded
  at member 15's docstring (J3).
- **Behavioral proof.** P2 (spine-use shape) + P4
  (`execution-verified`) + decode oracles
  `static-reviewed`.
- **Structural gate.** The `to_field_name`-preservation
  oracles fail a projection change to bare `pk`; the
  required-extra-omit oracle fails a skip widening that
  swallows clears into decode errors.
- **Freshness.** Target as in F1; [write-values] as in F2;
  [test-forms-resolvers]
  `badff5f4cadf453608ff4ad1b01bea5a60d66efd`.

### R2 -- Kind-split decode into data/files (file-local)

- **Contract + variation.** Members 16/19: the bound input
  walks `UNSET`-stripped fields through the bind-stashed
  reverse map; `SCALAR`/`RELATION_*` land form-keyed in
  `provided_data`, `FILE` lands in `provided_files` (never
  `data=` — a bound form reads uploads from `files=`).
  Scalar leaf rides `decode_scalar_leaf` via the shared
  handler factories. Varies on routing (C3 counts 1).
- **Sites + roles.** Definition here (dest split +
  `extra` form-field threading). Walk/handler owners:
  [write-values]. Consumer: member 19 feeds member 20.
  Oracles: split-landing, choice-enum unwrap, file-flavor
  exclusion rows.
- **Challenges.** C3 counts 1.
- **Owner + lifetime.** This file (the form-dest home;
  per-call dicts, nothing stored).
- **Distinct behavior.** `FILE` -> `files=` vs the
  serializer `FILE` -> `data` — the deliberate Django/DRF
  contrast, recorded at member 16's docstring.
- **Behavioral proof.** P3 (`execution-verified`: handler
  composition by name) + decode oracles `static-reviewed`.
- **Structural gate.** The split-landing oracle
  (`..._lands_under_form_key_not_id_attr` family) fails a
  `target_name` or dest change.
- **Freshness.** Target as in F1; [write-values] as in F2;
  [forms-inputs] `55614839ff479b3610b6026be65f2107ee560fcd`.

### R3 -- Partial-update reconstruction (file-local)

- **Contract + variation.** Member 17: for update, every
  non-file declared form field the input did not provide is
  supplied from the located row under the form field name,
  then `provided_data` overlays; `model_to_dict` for
  scalars + `to_field_name`-less FK, `_to_form_key_value`
  for M2M and `to_field_name` FKs, files excluded
  (`initial`-preserved). Full-form revalidation follows —
  untouched-but-now-invalid stored values block (partial
  transport, not partial validation). Varies on shape (C4
  counts 1).
- **Sites + roles.** Definition here. Consumers: member 19
  (update arm). Oracles: M2M/FK `to_field_name`
  preservation, file-exclusion, narrowed-excluded-FK,
  reverse-relation, dangling-FK rows.
- **Challenges.** C4 counts 1.
- **Owner + lifetime.** This file (the reconstruction home;
  per-call dict, nothing stored).
- **Distinct behavior.** Reconstruction vs model `setattr`
  + `full_clean(exclude=...)` vs serializer `partial=True`:
  three substrates, no shared body (J1).
- **Behavioral proof.** `static-reviewed` reconstruction
  oracles (both `to_field_name` directions pin
  omitted-vs-provided byte-compatibility).
- **Structural gate.** The omitted-M2M-with-`to_field_name`
  oracle fails a `model_to_dict`-only simplification (bound
  form would reject the instance-shaped member).
- **Freshness.** Target as in F1.

### R4 -- Form error mapping (file-local)

- **Contract + variation.** Member 18: a failed form maps
  `form.errors.as_data()` through the reused flat
  `validation_error_to_field_errors` over a synthesized
  `ValidationError` — `NON_FIELD_ERRORS` lands on the
  `"__all__"` sentinel byte-identically to a model
  `full_clean()` failure. No parallel mapper. Varies on
  mapping (C5 counts 1).
- **Sites + roles.** Definition here (the `as_data()`
  bridge). Mapper owner: [errors]. Contrast: the
  serializer recursive flattener (nested DRF structure —
  disjoint input shape, no merge posited).
- **Challenges.** C5 counts 1.
- **Owner + lifetime.** This file (the bridge home; pure
  call, nothing stored).
- **Behavioral proof.** `static-reviewed` envelope oracles
  (invalid + constraint rows assert the sentinel).
- **Structural gate.** The `__all__`-sentinel rows fail a
  mapper change that re-keys non-field errors.
- **Freshness.** Target as in F1; [errors]
  `3e25e93bf2265209f79b03d4b17670814f25d676`.

### R5 -- Flavor dispatch + write hooks (file-local)

- **Contract + variation.** Members 20--23: one shared
  construct/validate helper (`get_form` -> single
  `is_valid()`); the persist hook diverges — `form.save()`
  (ModelForm, returns `form.instance` for the skeleton
  re-fetch tail) vs `perform_mutate` (plain, returns the
  `True` sentinel for the `{ ok: true }` tail); both writes
  run inside `pipeline_write_phase` through
  `save_or_field_errors` (one catch, never a top-level
  `GraphQLError` at the write). Dispatch keys on
  `_primary_type is None`. Varies on the branch (C6
  counts 1).
- **Sites + roles.** Definitions: branch + hook choice here.
  Mapper/phase/skeleton owners upstream (all called by
  name, P3). Hook bodies live in [forms-sets] (`get_form`,
  `perform_mutate` defaults). Oracles: plain-skeleton ride,
  `perform_mutate`-only-on-success, write-outside-phase
  rejection, deadline-before-write rows.
- **Challenges.** C6 counts 1.
- **Owner + lifetime.** This file (the form-write home;
  closures per call, nothing stored).
- **Behavioral proof.** `static-reviewed` write oracles.
- **Structural gate.** The write-outside-phase oracle fails
  a phase-scope narrowing; the only-on-success oracle fails
  a hook-ordering change.
- **Freshness.** Target as in F1; [write-tx]
  `eca9ad4d3f765964df05884e080eb3ea63190ca8`;
  [forms-sets] `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`.

### J1 -- Partial-mechanism unification (rejection, considered fresh)

Model `full_clean(exclude=...)` carve-out vs form bound-data
reconstruction vs serializer `partial=True` solve the same
problem three ways. REJECTED: disjoint validation substrates
— a Django form cannot validate a partial `data=` (every
declared field validates, so the row must supply the rest);
`full_clean` natively supports `exclude`; DRF natively
supports `partial`. Positing the model/serializer rule here
(C10) would bind an incomplete form that rejects every
partial update. Trigger: a validation substrate supporting
two partial shapes at once. Home: member 17's docstring
(already states the transport-not-validation contract) +
this clause.

### J2 -- Batched form multi-decode (rejection, considered fresh)

Mapping member 15 onto the shared `decode_visible_relation_ids`
`pk__in` compose (one query instead of N). REJECTED: the form
needs the resolved OBJECT per element for the `to_field_name`
projection; the batched compose returns pks. Batching here
would re-fetch each object afterwards — same N+1 with extra
steps, or a silent projection change to bare `pk`.
Trigger: the decode no longer needing the object (projection
removed). Home: [write-values]`::decode_visible_relation`
docstring (already states the per-element vs batched split) +
member 15's docstring.

### J3 -- Null-M2M unification with the model path (rejection, considered fresh)

Adopting [mutations-resolvers]`::_relation_null_error`
(reject explicit `null` M2M) in member 15. REJECTED: a bound
`ModelForm` follows Django form semantics, where an empty
value clears an optional M2M (and a required one errors via
its own required-ness); imposing the model replace-set stance
would mis-report a decode-level error for a legitimate
nullable clear and block it. Trigger: either path changing
its null contract (model accepting null-clear, or forms
abandoning form semantics). Home: member 15's docstring
(already states the divergence + Decision 8 step 1) + this
clause.

### J4 -- Converter-table unification (checked non-membership)

This file holds NO converter table (P3-adjacent census: zero
`_SCALAR` / registry / `_CONVERT_` definitions; it does not
even call `convert_form_field` — kinds arrive on the
bind-stashed specs). The plan's
`converter-table-per-surface-ownership` row already covers
its four files; this file is not a fifth. No index change
proposed.

## Defects

None. Two investigated edges released without a defect:

1. `EXCLUDED`-kind specs would fall through to the scalar
handler — unreachable by construction (the form builder
classifies via `model_column_write_kind`, which returns
only the four kinds; verified against the body). Not a gap.
2. The module header's "both form flavors ride
`run_write_pipeline_sync` for that boundary" compresses the
async wrap (owned by the factory's `run_pipeline_async`) —
the dispatch section states it precisely; projection
wording, no behavior. Cosmetic, not filed.

Nothing routed to any owner.

## Pending execution

None. All five probes already ran green against the shared
tree; each is read-only (AST/text census + pure calls with
stub fields + short-circuit arms; no source mutation, no
database — P4 runs with empty `DATABASES`). No pytest was run
in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items.
`FAKESHOP_SHARDED=1` and Postgres cells are `inapplicable by
construction`: the probes reach no database, alias, or dialect
decision (P4 proves it by running with no database
configured).

## Judgment

Backstop discharged: 24/24 `ast.Module.body` members
enumerated, 12 challenges run (C1--C12, every variation axis
of every rule), six matrix axes discharged against the real
surface (all three write resolvers read whole FIRST; sharing
proved by behavior counts, not tokens; round-trips verified
in both directions; sync/async single-body shape verified by
instrument, not assumed), five file-local records with
proving challenges (R1--R5), three families reused-as-consumer
(F1/F2, re-derived fresh) plus one proposed family with
sub-rules for Worker 0 to index (F3 `shared-write-skeleton`:
skeleton + entry factory + async boundary), three checked
non-memberships (F4--F6), four rejections with difference +
trigger + home (J1--J3 considered fresh, J4 non-membership).
Zero defects, zero pending. The target owns its rules singly:
one relation coloring, one dest split, one reconstruction,
one error bridge, one dispatch. Zero-edit result is legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
ed0f20caae1a71b75a0f5474466422b7c067b9b7 --
django_strawberry_framework/forms/resolvers.py` is empty for
the target (working blob
`4edb984b299b4e2a71492e73382558b01865f48a`
equals `HEAD:` — target CLEAN, so no hunk attribution was
owed); the artifact itself is this new file
(`docs/dry/dry-file-forms__resolvers.md`, untracked until
Worker 0 records it). The `## Owned changes` ledger paths
(`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched. Concurrent dirt (the
`connection.py` hunk, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, in-flight `filters/inputs.py`
range hunk + `tests/filters/test_inputs.py` companion,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`,
plus the further working-tree dirt in `git status --short`
at run time) was never edited, reverted, or tidied, verified
by content-diff scoping (the item-scoped diff shows no entry
before and after). Scratch (untracked, kept for Worker 2
re-run):
`docs/dry/temp-tests/dry-file-forms__resolvers/p1_ast_census.py`,
`p2_flavor_mirror.py`, `p3_delegation.py`, `p4_behavior.py`,
`p5_gates.py` — all read-only, all green. Concurrent edit
observed and left untouched:
`django_strawberry_framework/filters/inputs.py` worktree blob
`06797dc7db04e4fc78cfbc478094ecada273c533`
vs HEAD/record (single external hunk confined to
`_normalize_range_value`, range-shape fail-loud hardening).
No site this item depends on changed — the target imports
nothing from `filters/inputs.py` (import census P3: the
nine non-future imports name no filters symbol), so the
finding set is robust to both versions of the hunk; Worker 2
re-hashes the twin only if it relies on it (it need not —
no finding cites range behavior). No `ruff` run owed (no
tracked edits). No pytest run (not authorized by the entry
command). Do not commit.

## Independent verification (Worker 2)

Expectation-first trace, recorded BEFORE reading `## Findings` (reconciled
after). Target read whole (605 lines); all three write resolvers read whole
FIRST ([mutations-resolvers] 1339 lines, [rf-resolvers] 2432 lines); owners
([write-values] whole, [querysets] recourse + boundary regions, [errors]
leaf regions, [write-tx] phase region) + build side ([forms-sets]
delegation/`_primary_type` regions, [forms-inputs] reverse-map regions) +
oracles ([test-forms-resolvers], [test-mutations-resolvers] gate region) read
for judgment. All five probes re-run green from the repo root
(`uv run python .../p1..p5`, P1/P2/P3/P5 output re-captured, P4 `P4 OK`).

### Own trace (8 rules, counts, owners I would choose)

| # | Rule (own wording) | Defs / posited change | Owner I choose |
|---|---|---|---|
| T1 | write-pipeline async-misuse recourse sentence (flavor noun varies) | 0 here (sentence) / 1 here (noun: rename subject) | [querysets]`::sync_pipeline_recourse` (template); per-flavor named constant stays |
| T2 | relation id resolves through related primary visibility; hidden == missing | 0 here (query) / 1 here (projection) | [querysets]`::related_visibility_queryset_or_default` chain; target is transitive consumer via [write-values]`::decode_visible_relation` |
| T3 | form relation coloring: `empty_values` skip + `to_field_name` projection, per-element multi | 1 (skip or projection change moves single + multi together) | here (`_to_form_key_value` / `_is_empty_form_value` / both decoders) |
| T4 | kind-split decode: SCALAR/RELATION_* to `provided_data`, FILE to `provided_files` | 1 (routing change) | here (dest split + `extra` threading); walk/handlers owned by [write-values] |
| T5 | partial-update reconstruction from located row, form-keyed, files excluded, full revalidation | 1 (shape change) | here (`_reconstruct_partial_data`) |
| T6 | form-error bridge: `as_data()` through reused flat mapper, `"__all__"` sentinel | 1 (mapping change) | here (bridge); mapper owned by [errors] |
| T7 | construct/validate-once + persist-hook split (`form.save` vs `perform_mutate`), `_primary_type` dispatch | 1 (new base = new branch) | here (branch + hook choice); hooks live in [forms-sets] |
| T8 | shared write skeleton (boundary + locate + authorize-before-decode + tail) + entry factory + async boundary | 0 here for order/boundary (rider, not owner) | [mutations-resolvers]`::run_write_pipeline_sync` (skeleton), `::make_resolver_entries` (entries); boundary delegates to `one-sync-boundary` primitive (see ruling) |

Reconciliation vs W1: T1=F1, T2=F2, T3=R1, T4=R2, T5=R3, T6=R4,
T7=R5, T8=F3 — agree on all eight, with ONE refinement on F3's
sub-rule split (below). No candidate of mine lacks a home; no W1 home
lacks a rule of mine.

### Enumeration (member-by-member vs own count)

Own instrument (`ast.Module.body` length + def names): **24**, identical
to W1. Member-by-member: 1 docstring (projection) / 2-3 machinery+annotation
imports (consumer-exempt) / 4-6 key-space+guard+reconstruction imports (R3/R1
consumers) / 7 skeleton imports (F3 consumers) / 8 template import (F1
consumer) / 9 phase import (R5 consumer) / 10 spine imports (R1/R2
consumers, P3 4/4 referenced) / 11 recourse constant (F1) / 12-15 coloring
helpers + decoders (R1) / 16 kind-split decode (R2) / 17 reconstruction (R3)
 / 18 error bridge (R4) / 19 decode step (R2/R3 composition) / 20-22
construct/validate + two write steps (R5) / 23 dispatch rider (R5+F3) /
24 factory product (F3). Dual-homing of 19/23 is composition/rider, not a
second definition. No member unassigned; agree 24/24.

### Matrix (vs real surface)

1. Cross-flavor: agree — all three resolvers read whole FIRST by both of
us; P2 re-run confirms one factory call per flavor, three recourse nouns,
skeleton ridden by all three (+ auth register as FOURTH rider,
[auth-mutations]`::_run_register_pipeline_sync` — strengthens F3, still
zero-edit). Decode split (single spine form+serializer; batched compose
model+serializer; `save_or_field_errors` model+form) re-captured exactly.
2. Sync/async: agree — own count 0 `AsyncFunctionDef` / 0 `await`; async
surface is the factory product through the shared boundary. No twin.
3. Derived knowledge: agree — own check: zero code-level `queryset`
attribute reads (all 8 hits docstring/prose), zero `InputFieldSpec(`
constructions, `related_model` parameter-only.
4. Round-trip: agree — encode (forms-inputs single site) / decode (spec
fields read never rebuilt); FILE->`files=` vs serializer FILE->`data`
contrast documented at both ends.
5. Contracts medium: agree — 1 definition per rule; docstring clauses,
spec-038, and oracles all classified, none independently maintained.
Oracle independence spot-held: zero `LOOKUP_NAME_MAP` reads in
[test-forms-resolvers]; oracles spell literals, none iterates an owner table.
6. Omission: agree — 4 kinds enumerated; `EXCLUDED` unreachable verified
against `model_column_write_kind` body (returns only the four kinds);
plain-flavor locate absence is the skeleton's `_primary_type is None`
branch. No gap, no defect.

### Counts, roles, equivalence

C1-C12 map to rows exactly as W1 claims (C1/C2->1 via R1; C3->1 via R2;
C4->1 via R3; C5->1 via R4; C6->1 branch via R5; C7 0-here/1-noun;
C8/C9 0-here; C10-C12 refused with J1-J3 differences). Roles hold:
template/spine/walk/mapper/phase/skeleton owners upstream, all composed by
name (P3 15/15 re-captured, zero definitions of ridden machinery here).
No oracle rewritten. Principle 8: zero-edit entails no observable-behavior
change; the only behavior-adjacent claims (skip/projection/routing) are
DB-free arms re-proved by P4 with empty `DATABASES`.

### Zero-edit, F3 ruling, hunk independence

Item-scoped diff re-confirmed empty (`git diff
ed0f20caae1a71b75a0f5474466422b7c067b9b7 --
django_strawberry_framework/forms/resolvers.py` exit 0, no output; working
blob `4edb984b…` == `HEAD:` == W1 record; `HEAD` `9031cb3d` canonical).
File-item zero-edit is legitimate: coverage 24/24, every rule homed.

F3 `shared-write-skeleton` ruling — ENDORSE as one new family item with
TWO index rows (skeleton, entry factory), REJECT the third sub-row (async
boundary) as duplicative: `run_pipeline_async` is a one-line delegate of
`run_in_one_sync_boundary` (already an open family whose file list includes
[mutations-resolvers]); the write-specific wiring (which flavors use the
boundary) collapses into the entry factory, which already wires
`resolve_async`. Skeleton vs factory stay separate rows (not one row: a
UNSET-normalization change moves only the factory; a pipeline-order change
moves only the skeleton — distinct change axes, precedent:
sealed-authorization-source slot/head twin rows). Not folding into any
existing family (no family owns the write orchestration or the entry
normalization). Not rejecting (4 riders — model, form, serializer, auth
register — ride one skeleton by name; a fifth flavor copying the
boundary/order/tail would be the exact drift this family prevents).
Fourth rider [auth-mutations] belongs in the family file list at sweep time.

Filters hunk independence — CONFIRMED: target contains zero `filters`
references (grep exit 1); hunk confined to
`filters/inputs.py::_normalize_range_value` range-shape hardening; no
finding cites range behavior; robust to both worktree `06797dc7…` and
HEAD/record `82b52d97…`.

### Rejections, fingerprints, gates, pending, coupling

J1/J2/J3 carry difference + trigger + durable home (verified against
bodies: `partial=True`, `full_clean(exclude=...)`, batched compose,
`_relation_null_error` all exist where cited); J4/F4/F5/F6 non-memberships
re-proved by own census (zero converter/permission/seal/`base_queryset`/
`model_for`/`run_in_one_sync_boundary`/`run_pipeline_async`/
`decode_visible_relation_ids` definitions or code uses; `seal` token absent
file-wide). All 11 freshness fingerprints re-hashed and MATCH
(target `4edb984b…`, querysets `1539b66c…`, write-values `d28587c7…`,
mutations-resolvers `3fd1e571…`, rf-resolvers `8024703e…`, errors
`3e25e93b…`, write-tx `eca9ad4d…`, forms-sets `36ce80b4…`, forms-inputs
`55614839…`, test-forms `badff5f4…`, test-mutations `4aa8e51e…`).
Gates exist with correct pins (factory `__name__` x3 body-read;
skeleton-ride monkeypatch body-read; misuse/visibility/`to_field_name`/
split-landing/omitted-M2M/`__all__`/phase-scope/only-on-success oracle
names present); each fails its guarded divergence (rename drift, skeleton
bypass, recourse drop, visibility bypass, pk-projection change, dest
change, sentinel re-key, phase narrowing, hook reorder) — static-reviewed;
`prove_failability.py` correctly NOT run (mutates the shared tree; no
workspace owed for a zero-edit file item with no source mutation).
`## Pending execution` absent-correct: P4 proves DB-free (empty
`DATABASES`), so sharded/Postgres are `inapplicable by construction` with
stated reason — Worker 1 states it, I judge it sound. Coupling: none
(zero-edit). No `## Owned changes` rows owed.

### AGENTS.md prose check

Link block: reference-style with all 10 canonical group headers incl.
`External`; citations are `path::Symbol` (13 `::` uses), zero raw
`path:NN`; no process provenance (only technical `dispatch`); oracles at
the mandated `tests/` package tier; no ruff/pytest owed (no tracked edits,
no authorized test run). Pass.

### Defects (Worker 2)

None. Both W1-released edges re-examined and released again: EXCLUDED
fall-through unreachable by construction (body-read); header compressing
the async wrap is projection wording with the precise statement at the
dispatch section — cosmetic, no behavior. No new defect found.

### Verdict

`verified`, no pending execution. Exact plan rows for Worker 0 below
(Families + two Responsibility-index rows; boundary aspect stays a
consumer edge of the open `one-sync-boundary` family, no row).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[errors]: ../../django_strawberry_framework/utils/errors.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
