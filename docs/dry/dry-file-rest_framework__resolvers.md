# DRY review: `django_strawberry_framework/rest_framework/resolvers.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a converged family edge (re-derived fresh, never
inherited), one named new family, a file-local record with its proving
challenge, or a recorded rejection with contract difference + trigger +
durable home. Zero production edits; zero tracked files changed; no
`## Owned changes` rows (file items land none).

HEAD at dispatch `5ee86193`, confirmed still `5ee86193` at finish (see
`## Implementation (Worker 1)`). Target HEAD blob `8024703e`; worktree blob
`c0b54039` (+129/-77, 39 hunks of concurrent bug-hunt dirt: hostile-value
guards with `_safe_class_name` / `_safe_type_name` / `_safe_arg_repr` labels
plus `except BaseException` arms plus guard prose — attributed by diff
content, left untouched). The trace reads HEAD bytes throughout
(`git show HEAD:...`); connected-body claims against dirty files are likewise
judged at THEIR HEAD bytes, with both fingerprints recorded where relied on.

## System trace

Target ([sresolvers][sresolvers], 2432 lines at HEAD): the DRF-serializer
write runtime ([spec-039][spec-039]), third sibling of [mresolvers][mresolvers] (the 036
model pipeline) and [fresolvers][fresolvers] (the 038 form pipeline). It
RIDES the shared write skeleton as one decode/write adapter pair and OWNS
everything DRF-specific around it. Shape, verified at HEAD bytes:

- **Skeleton rider, not owner.** `_run_serializer_pipeline_sync` calls
  `run_write_pipeline_sync` with `_serializer_decode_step` /
  `_serializer_write_step` (1 of the 5 package-wide riders, census P1);
  `resolve_serializer_sync` / `resolve_serializer_async` are the shared
  `make_resolver_entries` factory product (1 of 3 module pairs, census P1).
  All serializer-only machinery (kwargs merge, agreement guards, queryset
  scoping, validator pinning, intent ledger, witness, attestation) lives
  INSIDE `write_step`, i.e. post-auth inside the skeleton order — matching
  the verified `shared-write-skeleton` W2 trace, re-derived here.
- **Decode: serializer-field-keyed, spine-composed.** `_decode_input_object`
  routes each provided input attr by `InputFieldSpec.kind` through the shared
  `decode_provided_fields` loop + `decode_field_handlers` factories (FILE
  lands in `data` — the deliberate DRF contrast with the form `files=`
  split); relation arms compose `decode_visible_relation` (single, with the
  serializer `None`-skip + `obj.pk` projection) and
  `decode_visible_relation_ids` (batched multi); nested inputs recurse via
  `extra_handlers`. Scalar leaves ride the shared leaf untouched.
- **Errors: recursive flattener, shared leaves.** `serializer_errors_to_field_errors`
  + its recursive reverse map flatten DRF's nested `detail` structure into
  the envelope, terminating in the shared `field_error` / `empty_validation_error`
  ctors with shared `FIELD_ERROR_CODE_*` constants plus DRF passthrough codes.
  Zero `FieldError(` constructions, zero literal `codes=` in the target (P1).
- **Hooks: frozen views + framework-owned merge.** The three consumer hooks
  receive frozen data views (`_frozen_hook_view`) + the frozen
  `SerializerHookContext` (sole package construction site here); reserved
  keys (`data` / `instance` / `partial` / `context["request"]` /
  `context["write_alias"]`) are framework-owned with identity/sentinel
  checks; injection must exactly match `Meta.injected_fields`; save kwargs
  must shadow neither validated data nor model fields.
- **Trust: agreement + scope + intent + witness + attestation.** The runtime
  serializer must agree with the schema write surface (presence, writability,
  source, kind, relation model, requiredness, annotation); relation
  querysets are AND-scoped to visibility and pinned/locked; validator
  querysets are pinned per instance; the intent ledger proves
  `validated_data` still carries the resolved objects by identity; the
  signal witness observes the save; the attestation proves the saved row's
  database state matches the captured intent.
- **Sync-only body.** Zero `AsyncFunctionDef`, zero `await` (P1 AST census);
  the async surface is the factory's entry running the same sync body through
  `run_pipeline_async` → `run_in_one_sync_boundary` — the DRY principle-5
  write-pipeline answer (one sync body in one boundary; the `connection.py`
  two-colored contrast stands untouched).

Sites + roles (DRY vocabulary; all censuses at HEAD):

- DEFINITIONS here: the serializer decode pair + recursive object/nested
  decode, the recursive flattener + reverse map + budget, the hook coercion /
  freeze / injection / merge, the agreement + ownership + scope + pin +
  intent + witness + attest + saved-check rules, the write-surface list, the
  decode/write step adapters. Each is the single package site (censuses P1).
- CONSUMERS here (composed by name, P3-verified referenced): skeleton +
  factory + `sync_pipeline_recourse` noun + decode spine + envelope leaf /
  mappers / sentinel / codes + `WriteAliasContext` substrate
  (`require_write_pipeline`, `pipeline_write_phase`, `pin_write_queryset`,
  `base_locked_queryset`, `pks_match`, `assert_no_target_drift`,
  `make_cross_alias_save_guard`) + `related_visibility_queryset` +
  `request_from_info` + `is_forward_many_to_many` + `optional_input_field` +
  ownership raise path + converter kinds / `nested_serializer_child` /
  `resolve_serializer_field` + `SerializerHookContext` / `UploadMetadata`
  records (this module is their sole package PRODUCER).
- No package module consumes this module's privates (P1 consumer census:
  only docstring mentions elsewhere); `rest_framework/sets.py` binds the
  module entries by name.
- ORACLES: `tests/rest_framework/test_resolvers.py` (164 test functions at
  HEAD: flattener rows spelling literals, decode rows, merge/injection/
  save-kwarg/freeze/intent/witness/attestation rows, agreement rows, the
  grep-guard against live strategy reads, the misuse oracle) + live
  serializer rows in `test_products_api.py` / `test_library_api.py` /
  `test_multi_db.py` (wire envelopes). Test bodies read for the contract
  where a finding rests on them (pop-forbidden pins, save-called-once pin,
  instance-isolation pin).
- PROJECTIONS: the module docstring (verified clause-by-clause against the
  body; two clauses feed D1's analysis), the hook-default docstrings in
  `rest_framework/sets.py` (mirror prose, read at HEAD), spec-039
  (contract source; one archived sentence is stale — see D1), the
  `serializermutation` glossary anchor.

Connected behavior examined and EXCLUDED on body evidence (all HEAD-pinned;
dirty-file claims re-verified via `git show HEAD:`):

- The model twin (whole [mresolvers][mresolvers] regions: skeleton body,
  factory, `save_or_field_errors`, `refetch_optimized` + disappearing-row
  tail, `check_instance_write_alias` router re-check, `construction_kwargs`
  owner) and the form mirror (whole [fresolvers][fresolvers]: relation
  decoders, kind-split decode, partial reconstruction, flat error mapping,
  write steps) — read FIRST, before homing any decode/error/write rule.
- The owners: [wvalues][wvalues] decode spine (full read),
  [wtx][wtx] substrate (phase/guard/pin/lock/match/drift regions),
  [querysets][querysets] recourse + visibility helpers,
  [errors][errors] leaf/mappers/codes, [mutations-inputs][mutations-inputs]
  envelope type + reverse-map region (owner absent at HEAD — see J6),
  [utils-inputs][utils-inputs] `InputFieldSpec` + `generated_input_type_name`
  (owner of FAM-NEW), [mutations-sets][mutations-sets] operation gate +
  `validate_select_for_update` default, [rf-inputs][rf-inputs] specs /
  ownership / nested / naming regions, [rf-sets][rf-sets] hook defaults +
  bind, [converter][converter] kinds / nested child / relation requirements,
  [hook-context][hook-context] records, [relations][relations] taxonomy.
- Negative censuses at HEAD (P1 + git-grep): zero `FieldError(` / literal
  `codes=` / `require_drf` / `instance_accessor` / `classify_path` /
  `EXCLUDED` / second `FieldError` shape in the target; exactly one
  package construction site per hook record; exactly one surviving
  concatenation rebuild of the provisional name (FAM-NEW).

Lifetime (principle 4): per-write ephemeral state only — the ledger (one
per write step, consumed then backstopped), the M2M snapshot (update only,
entry-to-attestation), the witness record list (context-scoped, thread-
owned), the intent manifest (captured primitives, walk-to-attestation).
Nothing cached, memoized, or stored past the write step; pipeline context
(`alias`, `lock`, `authorized_pk`) is skeleton-published and read-only here.

## Verification

### Matrix

Each axis discharged against the target's REAL surface (probe P1,
`execution-verified`; git-grep censuses at HEAD, recorded below).

1. **Cross-flavor policy mirroring.** SEARCHED — all three resolver siblings
   read first. Model / form / serializer entry pairs all come from one
   factory call each; all three recourse constants call one template with
   distinct nouns; all three ride one skeleton supplying only step adapters
   (P1 censuses: 3/3/5). Relation decode: serializer single rides the same
   spine as form single with distinct skip/project (None + `obj.pk` vs
   `empty_values` + `to_field_name` — J13); serializer multi rides the same
   batched compose as model multi with distinct None policy (pass-through
   vs reject — J17); FILE routing is the deliberate `data` vs `files=`
   contrast (J18); partial update is `partial=True` vs reconstruction vs
   setattr (J15); save mapping is the three-branch DRF/Django/integrity
   router vs the shared `IntegrityError`-only mapper (J21). Verdict: one
   rule per surface; shared rules composed by name (C1–C5).
2. **Sync/async twins.** COMPARED by behavior. Instrument (P1): zero
   `AsyncFunctionDef`, zero `await` in the target; the sole `sync_to_async`
   token is module-docstring prose. The async surface is not a twin body:
   `resolve_serializer_async` is the factory entry running the SAME
   `_run_serializer_pipeline_sync` through `run_pipeline_async` (one
   `sync_to_async(thread_sensitive=True)` call — factory body read at HEAD).
   No second serializer pipeline exists to drift; the single-sync-body shape
   is the principle-5 write-pipeline answer, and the `connection.py`
   two-colored contrast (must await consumer `async def` hooks) is preserved
   at C2, not relitigated.
3. **Derived rather than repeated knowledge.** SEARCHED. `related_model`
   arrives bind-stashed on every spec and is threaded as a parameter (zero
   `InputFieldSpec(` constructions; zero per-request serializer-field
   rediscovery — the query path reads specs + `serializer.fields` only).
   The write alias / lock / authorized pk are read from the skeleton's
   pipeline context, never re-derived (one documented direct-invocation
   `instance.pk` fallback, still pre-hook). The recourse is computed from
   the template, the request from `request_from_info`, the M2M test from
   the taxonomy, the provisional name is recomputed for verification
   (J12) — EXCEPT the provisional's suffix assembly, which restates the
   shared namer by concatenation (FAM-NEW, the one hit on this axis).
4. **Inverse / round-trip pairs.** SEARCHED, both directions verified.
   Encode (spec build in [rf-inputs][rf-inputs], single construction sites)
   pairs with decode (spec → serializer-keyed payload here via
   `target_name` / `kind` / `related_model`, read never rebuilt) and with
   error re-key (GraphQL names via `_build_reverse_map`, J6). Schema
   annotation production pairs with runtime reproduce-and-compare (J12 —
   verification must recompute; it composes the same two functions by
   name). Hook-default shape ([rf-sets][rf-sets]) pairs with reserved-rule
   enforcement here (C10/J14 — complementary halves, correctly separated).
   One grammar per pair.
5. **Contracts restated in another medium.** COUNTED 1 definition per rule;
   every other medium classified. Module docstring (projection,
   clause-verified — two clauses analyzed under D1); spec-039 Decisions 7/8
   + pipeline passage (contract source — one archived sentence stale, see
   D1); `tests/rest_framework/test_resolvers.py` rows (oracles spelling
   literals: paths, messages, codes, pins — no oracle iterates an owner
   table; the grep-guard pins the no-live-strategy-read contract);
   [test-mresolvers][test-mresolvers] factory gate (pins the shared
   entries); live wire envelopes per flavor (listed). No medium holds an
   independently maintained copy.
6. **Enforcement by omission.** ENUMERATED. Kind coverage against the
   builder: `SCALAR` (shared leaf fallback), `RELATION_SINGLE` /
   `RELATION_MULTI` (relation arms), `FILE` (data-routed), `NESTED_SINGLE` /
   `NESTED_MULTI` (recursion) — total. `EXCLUDED` (spec-040 D6) would fall
   to the scalar handler, but serializer specs can never carry it (the
   converter stamps only its own kinds; zero `EXCLUDED` in the serializer
   build — J19, unreachable by construction, mirroring the verified form
   verdict). The serializer-only guards (agreement, intent, witness,
   attestation, saved-check) have no model/form counterpart — each answers
   a DRF trust boundary (custom validators / create / update / save) with
   no contract source extending it to the other flavors (spec-039 owns
   them; axis-6 probes recorded per finding, no defect). Delete needs no
   arm (bind-rejected via `require_non_delete_operation`, re-verified at
   HEAD). Two defects filed (D1 message-vs-behavior, D2 vanished-row
   raw raise) — both WITH a contract source + feasible shape + reaching
   input, per the Trust-boundary bar.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` over HEAD bytes (probe P1,
`docs/dry/temp-tests/dry-file-rest_framework__resolvers/p1_census.py`),
count **86**: 1 docstring + 32 imports (25 `ImportFrom` + 7 `Import`) +
45 `FunctionDef` + 1 `ClassDef` + 4 `Assign` + 3 `AnnAssign`; plus 15
nested defs (11 plain + 4 `_RelationIntentLedger` methods), each homed with
its parent. Every member lands below; C = converged family edge (fresh
evidence cited, prior verdict never inherited), FAM = the one named new
family, R = file-local finding, J = recorded rejection. No member
unassigned; no sampling.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | R21 (clause-verified; 2 clauses feed D1) |
| 2 | `from __future__` | machinery import | R22 (unreferenceable; census-exempt) |
| 3 | `import copy` | import | C (validator-copy consumer, R9) |
| 4 | `import datetime` | import | C (leaf-table consumer, R3) |
| 5 | `import decimal` | import | C (leaf-table consumer, R3) |
| 6 | `import enum` | import | C (leaf-table consumer, R3) |
| 7 | `import fractions` | import | C (leaf-table consumer, R3) |
| 8 | `import threading` | import | C (witness-owner consumer, R17) |
| 9 | `import uuid` | import | C (leaf-table consumer, R3) |
| 10 | `Iterator, Mapping` | import | C (`Mapping`: R3/J4 gates; `Iterator`: R17) |
| 11 | `contextmanager` | import | C (R17 decorator) |
| 12 | `MappingProxyType` | import | C (R3 freeze) |
| 13 | `typing.Any` | annotation import | R22 (annotation use; P3-referenced) |
| 14 | `FieldDoesNotExist` | guard import | C (R15/R16 serializer-only-relation skip) |
| 15 | `DjangoValidationError` | guard import | C (R19 flat-mapper branch) |
| 16 | `File` | key-space import | C (R3 upload-leaf test) |
| 17 | `IntegrityError, transaction` | guard import | C (R19 savepoint + branch) |
| 18 | `post_save, pre_save` | signal import | C (R17 witness) |
| 19 | `serializers` | DRF import | C (R6/R8/R9/R13/R18 shape tests) |
| 20 | `DRFValidationError` | guard import | C (R19 DRF-first branch) |
| 21 | `ConfigurationError, _safe_type_name` | guard import | C (all guards + messages) |
| 22 | `NON_FIELD_ERROR_KEY, FieldError` | envelope import | C3 (sentinel consumer; `FieldError` annotation-only) |
| 23 | `make_resolver_entries, run_write_pipeline_sync` | skeleton import | C1 (rider + factory) |
| 24 | errors import (7 names) | envelope import | C3 (leaf/mappers/codes/path) |
| 25 | `optional_input_field` | inputs import | C (J12 recompose by name) |
| 26 | `request_from_info` | context import | C (R5 framework request) |
| 27 | `related_visibility_queryset, sync_pipeline_recourse` | substrate import | C5 + C4 (visibility member + recourse template) |
| 28 | `is_forward_many_to_many` | taxonomy import | C8 (R15 M2M test) |
| 29 | write_transaction import (7 names) | substrate import | C9 (phase/guard/pin/lock/match/drift) |
| 30 | write_values import (5 names) | spine import | C (R1/R2 loop + handlers + spines) |
| 31 | `SerializerHookContext, UploadMetadata` | record import | C12 (sole package producer here) |
| 32 | ownership import (2 names) | inputs import | C6 (R7 raise-path consumer) |
| 33 | converter import (7 names) | kind import | C (kinds + nested child + re-resolve) |
| 34 | `_OMITTED` | sentinel | R21 (merge + ledger-consume omission mark) |
| 35 | `_SERIALIZER_ASYNC_RECOURSE` | recourse constant | C4 (template consumer) |
| 36 | `_DRF_NON_FIELD_KEY` | configured key | R21 (bucket normalization) |
| 37 | `_decode_relation_single` | relation decoder | R1 (+ J13/J17) |
| 38 | `_decode_relation_multi` | relation decoder | R1 (+ J16/J17) |
| 39 | `_decode_serializer_data` | decode entry | R1 |
| 40 | `_decode_input_object` | recursive decode | R1 (+ `_field_path` nested) |
| 41 | `_decode_nested` | nested recursion | R2 (+ J10) |
| 42 | `serializer_errors_to_field_errors` | recursive flattener | C3 (+ J3) |
| 43 | `_ERROR_FLATTEN_NODE_BUDGET` | node budget | C3 (with 42) |
| 44 | `_error_node_children` | expansion rule | C3 (with 42) |
| 45 | `_error_leaf` | shared leaf | C3 (with 42) |
| 46 | `_error_detail_codes` | code reader | C3 (+ J7) |
| 47 | `_rekey_segment` | segment re-key | C3 (with 42) |
| 48 | `_build_reverse_map` | recursive map | C3 (+ J6) |
| 49 | `_upload_metadata` | upload descriptor | R3 (sole `UploadMetadata` producer) |
| 50 | `_hook_mapping` | hook coercion | C11 (adopted member) + J4 |
| 51 | `_IMMUTABLE_LEAF_TYPES` | freeze allow-list | R3 (with 53) |
| 52 | `_FROZEN_VIEW_CONTAINERS` | freeze containers | R3 (with 53) |
| 53 | `_frozen_hook_view` | frozen view | R3 (+ J3; 5 nested homed here) |
| 54 | `_injected_serializer_data` | injection collect | R4 |
| 55 | `_merged_serializer_kwargs` | reserved merge | R5 (+ J4/J11) |
| 56 | `_relation_model_of` | model read | R6 (+ J20) |
| 57 | `_assert_schema_runtime_agreement` | agreement walk | R6 |
| 58 | `_assert_runtime_write_source_ownership` | ownership recursion | R7 (+ C6) |
| 59 | `_assert_field_agreement` | per-field agreement | R6 + FAM-NEW (provisional f-string) |
| 60 | `_assert_relation_agreement` | relation agreement | R6 |
| 61 | `_assert_nested_agreement` | nested agreement | R6 (+ J1) |
| 62 | `_scope_relation_querysets_to_visibility` | scope entry | C5 + R8 |
| 63 | `_pin_validator_querysets` | validator pin | R9 (+ J1; 2 nested homed here) |
| 64 | `_scope_specs_over_serializer` | scope body | C5 + R8 (+ J1) |
| 65 | `_assert_save_kwargs_no_shadow` | shadow guard | R10 (+ J5) |
| 66 | `_assert_save_kwargs_not_model_fields` | model-field guard | R10 (+ J5) |
| 67 | `_write_surface_specs` | spec list | R11 |
| 68 | `_RelationIntentLedger` | ledger record | R12 (4 methods homed here) |
| 69 | `_relation_object_identity` | identity capture | R12 |
| 70 | `_relation_intent_snapshot` | intent snapshot | R12 |
| 71 | `_relation_identity_intact` | identity compare | R12 |
| 72 | `_instrument_relation_intent` | instrument entry | R13 |
| 73 | `_instrument_intent_specs` | instrument recursion | R13 (+ J1) |
| 74 | `_record_field_intent` | validation wrap | R13 (+ `_recording` nested) |
| 75 | `_assert_relation_intent` | intent walk entry | R14 |
| 76 | `_assert_intent_specs` | intent walk body | R14 (+ J1; D1 lives here) |
| 77 | `_m2m_membership_snapshot` | M2M snapshot | R15 |
| 78 | `_attestable_m2m_fields` | M2M census | R15 (+ C8) |
| 79 | `_attest_saved_relations` | attestation | R16 (D2 lives here) |
| 80 | `_write_witness` | signal witness | R17 (+ `_record` nested) |
| 81 | `_checked_saved_result` | saved validation | R18 (+ J8/J9) |
| 82 | `_serializer_write_step` | write step | R19 (skeleton adapter) |
| 83 | `_guarded_serializer_write` | write body | R19 (+ J21; `_do_save` nested) |
| 84 | `_serializer_decode_step` | decode step | R20 (skeleton adapter) |
| 85 | `_run_serializer_pipeline_sync` | flavor dispatch | C1 (skeleton rider) |
| 86 | `resolve_serializer_sync, resolve_serializer_async` | module entries | C1 (factory product) |

Nested defs homed with parents (15): `_field_path` (40), `_freeze_leaf` /
`_entries` / `_new_acc` / `_finalize` / `_place` (53), `_pinned` /
`_pin_field` (63), `__init__` / `record` / `consume` /
`assert_fully_consumed` (68), `_recording` (74), `_record` (80),
`_do_save` (83). R22 records the import-reference check (P3): all 32
import members are referenced at HEAD (each import row above names its
consumer).

### Challenges

Authoritative definitions counted only; consumers, oracles, and projections
that move alongside are listed, never counted. Probe P1 (census,
`execution-verified`, no package import, no database opened); P2 (dirt
attribution: `git diff HEAD` hunk census, read-only); P3 (import-reference
check over HEAD bytes, read-only — every import member above names its
consumer; the check script is P1's sibling run, recorded under
`## Implementation (Worker 1)`).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| H1 | new decode kind (a third nested shape) | **0** new token defs (kinds single-sourced in [converter][converter]); **6** per-discipline dispatch decisions (decode/agreement/scope/instrument/intent/ownership — each answers for its own contract, J1) | kind oracles per discipline |
| H2 | change relation-decode visibility | **0 here** (spine owner); skip/project **1 here** (R1) | form + serializer decoders follow the spine |
| H3 | change the flattener (new bucket/shape) | **1 here** (C3 walk + map) | leaf/code/path owners stay; flattener oracles |
| H4 | change the recourse sentence | **0 here** (template owner); noun **1 here** (C4) | wording oracles |
| H5 | change the pipeline order | **0 here** (skeleton owner) | all five riders follow |
| H6 | change the provisional-name suffix rule | **2** (the shared namer + the guard f-string) → FAM-NEW | build call sites follow the namer; agreement oracles |
| H7 | change pk-drift equality | **1** (`pks_match`; both enforcement sites follow — J9) | skeleton backstop + R18 oracles |
| H8 | change a reserved-key rule | **1 here** (R5 merge) | hook-default prose; merge oracles |
| H9 | change the write-alias guard | **0 here** (substrate owner); message halves **1 here** (R17) | witness oracles |
| H10 | change the alias/pin/lock discipline | **0 here** (substrate owners); composition **1 here** (R8) | scope oracles |
| H11 | unify the nested-structure walks | **refused** (J1: distinct subjects + threading) | — |
| H12 | unify the None arms | **refused** (J2: element vs list vs nested vs object positions) | — |
| H13 | unify the cycle walkers | **refused** (J3: error walk vs data freeze) | — |
| H14 | add a second `FieldError(` site | **refused** (envelope T-construct holds; 0 sites here) | — |

Probe commands + what each proved (all `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-rest_framework__resolvers/p1_census.py`
  — HEAD `5ee86193`, HEAD blob `8024703e`, worktree `c0b54039`; 86 members
  (1/25/7/45/1/4/3 by kind); 0 async defs, 0 awaits, 15 nested defs; 3
  factory sites, 5 skeleton riders, 3 recourse sites; 0 `FieldError(`
  constructions, 0 literal `codes=`, 1 hook-record construction each;
  `require_drf` / `instance_accessor` / `classify_path` absent; 2
  conditional-suffix sites (namer + guard f-string).
- `git diff HEAD -- <target>` hunk census (P2, read-only) — 39 hunks,
  +129/-77, all hostile-value-guard dirt (`_safe_*` labels, `except
  BaseException` arms, guard prose); zero overlap with any skeleton /
  factory / spine / envelope site, and one naming-site touch: the FAM-NEW
  line's base-name half only (its suffix-conditional half is
  byte-identical).
- Import-reference check (P3, read-only, HEAD bytes) — all 32 import
  members referenced (each enumeration row names its consumer); `FieldError`
  annotation-only (no construction — T-construct holds).

## Findings

Converged family edges first (C1–C12; each re-derived on FRESH HEAD-byte
evidence — prior verdicts only told me where to look), then the one named
new family (FAM-NEW), then file-local rules (R1–R22), then rejections
(J1–J21). Freshness fingerprints for every relied-on file sit under
`## Implementation (Worker 1)`; any fingerprint change reopens the finding
that cites it.

### C1 — `shared-write-skeleton` + `shared-write-entry-factory` (rider + product; CONVERGE fresh)

- **Contract + variation.** Locate → authorize → decode → write → tail
  inside one nested transaction, authorize-before-decode fixed; entries are
  the `(resolve_sync, resolve_async)` factory pair. Varies in the three
  seams only (`decode_step` / `write_step` / `tail_step`).
- **Sites + roles.** Owner: [mresolvers][mresolvers]`::run_write_pipeline_sync`
  + `::make_resolver_entries`. Target role: RIDER — member 85 calls the
  skeleton with the serializer step pair (1 of exactly 5 package riders,
  P1); member 86 is a factory product (1 of exactly 3 module pairs, P1);
  members 82/83/84 are the step adapters. All serializer-only machinery
  sits INSIDE `write_step` (post-auth by construction) — re-derived here,
  matching the verified family W2 trace line for this rider.
- **Challenges.** H5 → 0 here (phase reorder moves the skeleton only);
  new-flavor → 0 orchestration defs (register precedent stands).
- **Behavioral proof.** `static-reviewed` (rider census P1, body read at
  HEAD, dirt-disjoint per P2). No new index row (both rows already held by
  the verified [family item][skelfam]).

### C2 — `one-sync-boundary` (transitive consumer; CONVERGE fresh)

- **Contract.** One `sync_to_async(thread_sensitive=True)` worker per async
  operation; ORM never interleaves with awaits inside a transaction.
- **Sites + roles.** Owner: [querysets][querysets]`::run_in_one_sync_boundary`.
  Target role: transitive consumer — member 86's async entry routes through
  `run_pipeline_async`; the target spells no boundary itself (0 async
  defs, 0 awaits, P1). Principle-5 contrast preserved: this flavor is one
  sync body in one boundary; `connection.py` keeps two colored bodies
  because it must await consumer `async def` hooks (R4 of the verified
  [family][bdfam], cited here, untouched there).
- **Challenges.** Boundary retune → 0 here (owner moves; all three flavor
  pairs follow). No new index row.

### C3 — `mutation-error-envelope` (flattener adapter; CONVERGE fresh)

- **Contract + variation.** One `errors: [FieldError!]!` envelope across
  flavors; per-condition leaf wrappers stay ([family][envfam] R1 names
  "the DRF flattener"); recursive flattener vs flat Django mapper is
  recorded distinct behavior (nested vs flat contracts).
- **Sites + roles.** Owners: [mutations-inputs][mutations-inputs]`::FieldError`
  (type), [errors][errors] leaf + code table, skeleton envelope assembly.
  Target role: ADAPTER — members 42–48 (flattener + budget + expansion +
  leaf + code reader + re-key + recursive map) terminate in the shared
  `field_error` / `empty_validation_error` ctors with shared constants +
  DRF passthrough codes. Fresh trigger checks: T-construct HOLDS (0
  `FieldError(` sites, P1); T-shape HOLDS (no `errors` field declared
  here); T-code HOLDS (0 literal `codes=`, P1). `_build_reverse_map`
  covers input specs only — injected fields key verbatim by their declared
  name, which is the only honest key (they own no GraphQL input name);
  considered, correct, no defect.
- **Challenges.** H3 → 1 here (walk + map); leaf/code/path retune → 0 here.
  No new index row.

### C4 — `sync-boundary-recourse-wording` (consumer; rejected family, CONVERGE fresh)

- **Contract.** The three write flavors raise one `SyncMisuseError`
  sentence, byte-identical except the flavor subject; the sentence is
  template-owned, the per-flavor named constant + noun stay.
- **Sites + roles.** Owner: [querysets][querysets]`::sync_pipeline_recourse`
  (body read at HEAD — the docstring names all three constants). Target
  role: consumer — member 35 is the single call with `"serializer
  mutation"` (1 of exactly 3 package calls, P1). The index rejection
  stands on fresh evidence; this file already matches that outcome.
- **Challenges.** H4 → 0-here/1-noun. No index change.

### C5 — `related-object-visibility-recheck` (member; open family, no change)

- **Contract.** The `registry.get` resolve + visibility-scope call is
  single-sited; each surface keeps its own None-handling (tails diverge).
- **Sites + roles.** Owner: [querysets][querysets]`::related_visibility_queryset`
  (docstring read at HEAD — names this module's scope walk as a caller).
  Target role: member — `_scope_specs_over_serializer` (member 64) calls
  it and ANDs the result as a `pk__in` subquery (None = pin + lock only,
  the surface's own tail). This file is already listed on the open index
  row; the membership re-verifies, nothing to add. Note: the index row
  names the `_or_default` wrapper; this surface correctly calls the
  inner helper — the wrapper's default-manager tail is the wrong
  contract here (None skips visibility; it does not default it).
- **Challenges.** Visibility-resolve change → 0 here (owner moves);
  composition change → 1 here (R8). No index change.

### C6 — ownership raise-path (runtime consumer of inputs `serializer-writable-source-ownership`)

- **Contract.** One raise path for schema-time (sets) and runtime
  (resolvers) source-ownership checks; detection in
  `writable_star_sources` / `writable_source_collisions`.
- **Sites + roles.** Owner: [rf-inputs][rf-inputs]`::raise_writable_source_ownership_errors`
  (+ `::runtime_validated_data_fields` for the runtime field set) — the
  verified inputs F-WRITE row. Target role: runtime consumer — member 58
  walks the instantiated serializer (+ opted-in nested recursion) and
  calls the raise path with a runtime `location` phrase. Exactly 2
  package call sites per helper (sets schema arm + resolvers runtime arm,
  git-grep census).
- **Challenges.** Message/detection change → 0 here (owner moves); runtime
  walk change → 1 here (R7). No new index row (consumer edge of a
  file-local row).

### C7 — nested opt-in recursion (consumer of inputs `serializer-nested-opt-in-recursion`)

- **Contract.** Nesting is opt-in only (`NestedSerializerConfig`); the
  build records `nested_specs` per opted-in field; the query side recurses
  with the same per-field machinery.
- **Sites + roles.** Owner: the [rf-inputs][rf-inputs] nested build
  (`NestedSerializerConfig`, `_resolve_nested_field`, cycle/depth guard) —
  the verified inputs F-NEST row. Target role: consumer — `nested_specs`
  threaded through decode (41), agreement (61), scope (64), instrumentation
  (73), intent (76), ownership (58), reverse map (48), always descended via
  the shared `nested_serializer_child` (8 package call sites: 3 schema-side +
  5 here, census).
- **Challenges.** Opt-in/config change → 0 here (build moves); per-walk
  recursion change → 1 per walk (J1 refuses unification). No new row.

### C8 — `relation-kind-taxonomy` (consumer; CONVERGE fresh)

- **Contract.** One classifier for Django relation kinds; forward-M2M
  detection single-sited.
- **Sites + roles.** Owner: [relations][relations]`::is_forward_many_to_many`
  (verified family). Target role: consumer — `_attestable_m2m_fields`
  (member 78) calls it once to bound the attestation census to writable
  direct M2Ms. No second forward-M2M test here (J20 records the DRF-side
  read as a different rule).
- **Challenges.** Taxonomy change → 0 here. No new row.

### C9 — `sealed-execution-queryset` substrate (consumer; CONVERGE fresh)

- **Contract.** Sealed/pinned/locked execution querysets; phase-gated alias
  enforcement; canonical pk equality; drift snapshots.
- **Sites + roles.** Owner: [wtx][wtx] (`require_write_pipeline`,
  `pipeline_write_phase`, `pin_write_queryset`, `base_locked_queryset`,
  `pks_match`, `assert_no_target_drift`, `make_cross_alias_save_guard`).
  Target role: consumer — 12 call sites across R8/R9/R14/R16/R17/R18/R19
  (census; every call composes by name with serializer message halves at
  most). The seal policy itself is never restated.
- **Challenges.** H9/H10/H7 → 0 here on mechanism; composition/message
  halves → 1 here each (R8/R17/R18). No new row.

### C10 — guard posture (no per-module `require_drf`; rejected, CONVERGE fresh)

- **Contract.** The verified `rest_framework/__init__.py` item rejected
  per-module guard calls (durable home: the leaf docstring): the leaf
  import-time guard covers the flavor; member modules carry no guard of
  their own.
- **Sites + roles.** Target role: consistent non-caller — zero
  `require_drf` tokens (P1). The DRF import at member 19 rides the leaf
  posture; no third guard shape exists.
- **Challenges.** Guard-policy change → 0 here (leaf moves). No index
  change (rejection stands).

### C11 — `hostile-mapping-hardening` (ADOPT into the open family)

- **Contract.** Mappings crossing a trust boundary are type-gated,
  materialized defensively, and key-gated where downstream code splats
  them — never a raw `TypeError` into GraphQL.
- **Sites + roles.** Owner: TBD by the family item (currently
  `utils/policies.py`, `conf.py`, `types/base.py`). Target role: MEMBER —
  member 50 (`Mapping` gate + `dict()` materialize + non-`str` key
  rejection, invoked at all three hook boundaries) plus the R5 context
  materialization (J4 records its contract difference, not a second
  definition of this rule). Fresh evidence: the `str`-key gate exists
  precisely because the gated mappings become `**kwargs`/`data` keys.
- **Worker 0 transcription:** append `django_strawberry_framework/rest_framework/resolvers.py`
  to the `hostile-mapping-hardening` index row's Files covered; the family
  item decides the owner with this member in its sweep. No new family.
- **Challenges.** Gate-policy change → moves with the family owner once
  chosen. Proof `static-reviewed` (body + 3 call sites + oracle pins for
  non-mapping / unmaterializable / non-string-key returns).

### C12 — hook-record production (sole producer; CONVERGE with hook_context rows fresh)

- **Contract.** `SerializerHookContext` (operation / write_alias /
  instance_pk) and `UploadMetadata` (name / size / content_type) are the
  frozen hook-surface records, defined once in [hook-context][hook-context].
- **Sites + roles.** Owner: the record definitions (verified file-local
  rows). Target role: sole package PRODUCER — member 82 constructs the one
  `SerializerHookContext` per write step (operation from validated meta,
  alias + authorized-pk snapshot); member 49 constructs `UploadMetadata`
  per file value. Census: exactly 1 package construction site each (P1);
  every other construction is a `tests/` oracle. No package code reads
  `.operation` / `.write_alias` / `.instance_pk` off the record (consumer
  overrides do — one in-tree).
- **Challenges.** Record-shape change → 0 here on shape (owner moves);
  producer call → 1 here. No new row.

### FAM-NEW — `canonical-input-provisional-name` (NEW FAMILY for Worker 0)

- **Contract + variation.** The canonical generated-input provisional name
  (`<Base>Input` / `<Base>PartialInput`) that seeds serializer-only
  choice-enum names during the field walk. Varies on `is_partial` only;
  always the full-shape skeleton (the divergent descriptor-derived name is
  computed AFTER the walk — build comment read at HEAD).
- **Sites + roles.** Owner: [utils-inputs][utils-inputs]`::generated_input_type_name`
  (the documented "load-bearing skeleton the three flavors' input-name
  derivers share"). Composed calls (5): [rf-inputs][rf-inputs] walk
  provisional, injected-specs provisional, `serializer_input_type_name`,
  `describe_serializer_input` diagnostic, `name_set_input_type_name`
  spine. RESTATEMENT (1): member 59's
  `f"{type(serializer).__name__}{'PartialInput' if operation == 'update'
  else 'Input'}"` — a concatenation rebuild of the namer, the literal
  principle-6 violation shape ("never rebuilds the name by concatenation").
  Population closed: exactly 2 conditional-suffix sites package-wide (P1).
  Dirt note: the guard line carries a hunt hunk on its BASE-name half
  (`type(serializer).__name__` → `_safe_type_name(serializer)`); the
  SUFFIX-conditional half (the restatement) is byte-identical, and the
  finding is judged at HEAD bytes. The family item reconciles the base
  rendering with the landed hunt at consolidation time.
- **Equivalence (why the restatement is exactly the namer).** Base:
  `type(serializer).__name__` == `serializer_class.__name__` (the
  serializer is constructed from that exact class two phases earlier);
  `is_partial` ⟺ `operation == "update"` (closed create/update vocabulary,
  upstream-validated); `is_full_shape=True, token=""` (build uses the
  canonical provisional on EVERY walk — top, injected, and nested, the
  nested build re-entering the same builder — verified at all three build
  bindings). The guard needs no divergent name: it re-derives the RUNTIME
  annotation, which is seeded from the same canonical provisional at every
  depth (nested early-return covers containers; children re-derive under
  their own class name, matching the nested build).
- **Challenges.** H6 → **2** (suffix-rule change moves namer + f-string).
  Consumers/oracles moving along (not counted): 5 composed calls, agreement
  oracles. No relation to the verified inputs F-SHAPE row (that row owns
  the DIVERGENT descriptor-derived naming, still single-sited in
  [rf-inputs][rf-inputs]); this family owns the canonical provisional +
  its restatement — a sub-rule whose second site sits outside that item's
  target, so no verified row is contradicted.
- **Migration (for the family item, not this file item).** The f-string
  becomes `generated_input_type_name(type(serializer).__name__,
  is_partial=(operation == "update"), is_full_shape=True, token="")` —
  dependency-clean (this module already imports `..utils.inputs`), behavior
  identical by the equivalence above. The family item sweeps the naming
  population fresh, lands the call, and shows the agreement oracles green.
- **Worker 0 transcription:** index row `| canonical-input-provisional-name |
  django_strawberry_framework/utils/inputs.py::generated_input_type_name |
  django_strawberry_framework/utils/inputs.py,
  django_strawberry_framework/rest_framework/inputs.py,
  django_strawberry_framework/rest_framework/resolvers.py | Family
  canonical-input-provisional-name | open |` plus the `## Families` item
  `Family canonical-input-provisional-name`.
- **Freshness.** Owner blob + member blobs under `## Implementation
  (Worker 1)`. Proof `static-reviewed` (body equivalence + closed
  population census); execution belongs to the family item.

### R1 — serializer relation decode coloring (file-local)

Members 37–40: the single decoder (spine call with `None`-skip + `obj.pk`
projection), the batched multi decoder (whole-`None` pass-through + empty
list clear, else the shared compose), the top entry over the bind-stashed
map, and the recursive object decode (UNSET-strip walk + kind dispatch via
the shared loop, `field_name` dotted-path closure, nested `extra_handlers`,
non-dataclass → `field_error`). The relation `GlobalID` decodes against
the RECORDED `effective_globalid_strategy` inside `type_check_relation_id`
— the module performs zero live strategy/settings reads (the only settings
read is the non-field bucket key, R21; the grep-guard oracle pins this).
**Proving challenge:** H2 — visibility change moves the spine (0 here);
skip/project/path change moves only these arms (1 here); package census
finds no second serializer-field-keyed decoder (the form twin differs per
J13, the model twin per J16/J17). Scalar leaves add no serializer rule
(the shared leaf rides untouched). Axis 6: `EXCLUDED` unreachable (J19).

### R2 — nested decode recursion (file-local)

Member 41: single nested dataclass → one decoded dict; multi list → per-item
dicts with index-pathed errors; `None` passes through for the parent
serializer's own validation; non-list multi → in-band "Expected a list of
items" (J10). Wired into member 40 via `decoded_into` + `extra_handlers`.
**Proving challenge:** H1 — no second nested-input decoder exists
package-wide (nesting is a serializer-only axis; the build side in
[rf-inputs][rf-inputs] produces, this consumes — C7). Nested relations are
visibility-checked and nested scalars Unicode-preflighted exactly like
top-level ones, by recursion, not by restatement.

### R3 — hook data views: freeze + upload metadata + tables (file-local)

Members 49/51/52/53: the frozen upload descriptor (guarded `name`/`size`/
`content_type` reads, `None` on failure), the immutable-leaf allow-list,
the descended-container tuple, and the iterative post-order freeze
(dict→`MappingProxyType`, list/tuple→tuple, set→frozenset,
bytearray→bytes, uploads→metadata; shared references stay shared;
cycles fail loud; opaque leaves fail closed). **Proving challenge:** no
second freeze exists (the flattener's iterative walk differs per J3);
table change → 1 here. Axis 6: non-`dict` mappings and opaque leaves fail
closed by contract (oracles pin the full value algebra + depth beyond the
recursion limit).

### R4 — injection exact-match (file-local)

Member 54: the hook return (mapping-coerced via C11) must EXACTLY equal
`Meta.injected_fields` — a missing declared field or an undeclared extra
key is a `ConfigurationError`. **Proving challenge:** no second injection
rule exists (the schema-side narrowing disjointness is class validation in
[rf-sets][rf-sets], a different phase of the same contract — complementary
halves, not two definitions); exactness change → 1 here.

### R5 — constructor-kwarg reserved merge (file-local)

Member 55: `data` (omitted or the identical frozen object — sentinel +
identity, never equality), `instance` (any key rejected — hooks receive
the frozen context instead), `partial` (any key rejected — injected for
update only), `context["request"]` (different object rejected, same
tolerated), `context["write_alias"]` (conflicting value rejected).
**Proving challenge:** H8 → 1 here; no second reserved-key rule exists
(the [rf-sets][rf-sets] default docstring DESCRIBES the rule — projection,
verified consistent at HEAD — and the form/model construction seams take
live instances by their own contracts, J14). J4/J11 record the two
considered unifications.

### R6 — schema/runtime agreement (file-local)

Members 56/57/59/60/61: the write-surface walk, the per-field contract
(present + writable + same source + kind-compatible + relation shape over
the same model + requiredness + annotation), the relation/nested
recursions, and the runtime relation-model read. Requiredness honors DRF
partial semantics (update → effectively optional); the annotation check
re-derives via the same two build functions (J12) except the provisional
f-string (FAM-NEW). **Proving challenge:** agreement change → 1 here; no
second agreement rule exists (the only sibling confronting two field maps
is the model/form bind, which constructs rather than verifies).
Extra runtime fields are tolerated by contract (only write-surface fields
are held).

### R7 — runtime write-source ownership recursion (file-local walk, C6 raise path)

Member 58: walks the INSTANTIATED serializer (schema discovery cannot see
`get_fields()` dynamics) + opted-in nested children, unioning supplied
child keys, and calls the C6 raise path per level with a runtime `location`
phrase. **Proving challenge:** walk change → 1 here; message/detection
change → 0 here (C6 owner). The schema arm ([rf-sets][rf-sets]) and this
runtime arm are complementary phases sharing one raise path — not two
definitions.

### R8 — relation-queryset AND-scope discipline (file-local composition, C5 member)

Members 62/64: author queryset stays the base (pinned; cross-alias fails
closed), visibility AND-ed as a `pk__in` subquery (never a replacement),
raw-pk relations pinned without visibility, lock composed via
`base_locked_queryset` (never `select_for_update()` on the author's shape),
recursed into nested serializers. **Proving challenge:** H10 → 0 on
mechanism (substrate owners), 1 here on composition; no second scoping
discipline exists (the DECODE visibility query resolves ids→objects — a
different contract: resolution vs constraining DRF's second lookup).

### R9 — validator queryset pinning (file-local)

Member 63: recursively pins every queryset-backed DRF validator (field,
serializer-level, nested, `child`/`child_relation`) to the write alias on
shallow per-instance copies (DRF shares validator objects). **Proving
challenge:** pin change → 1 here; no second validator walk exists (J1
records why the field-walk shape stays separate from the spec-walks).

### R10 — save-kwarg guards (file-local pair)

Members 65/66: reject a save kwarg shadowing any ACTUAL top-level
`validated_data` key (covers renamed/injected/defaulted/hidden keys —
read off the object, never reconstructed) and any `_meta` field name or
attname. **Proving challenge:** guard change → 1 here each; no second
save-kwarg rule exists (DRF merges save kwargs over validated data with
no validation — the guards ARE the contract). J5 records the same-file
split (supplied-keys vs model-field universe).

### R11 — write-surface spec list (file-local)

Member 67: the one concatenated list (GraphQL input specs + injected
specs, disjoint by class validation) every top-level per-field discipline
walks — agreement, ownership, scoping, instrumentation, intent, M2M
snapshot, attestation (7 call sites, census). **Proving challenge:**
membership change → 1 here; every discipline follows by construction
(the pre-listing shape would force 7).

### R12 — relation-intent ledger + snapshot + compare (file-local)

Members 68–71: the per-write record (dotted path → ordered snapshots),
immutable `(object, pk, alias)` capture, list-aware snapshot, and the
identity-plus-primitives comparison (catches in-place pk/alias mutation
that a bare `is` check would miss). **Proving challenge:** ledger/record/
compare change → 1 here each; no second intent-record rule exists (the
skeleton's `target_state` snapshot answers row-drift, not relation
identity — different subjects).

### R13 — relation-intent instrumentation (file-local)

Members 72–74: per-instance `run_validation` shadow recording the return
snapshot, installed post-scope pre-`is_valid()` over the write-surface
specs with nested recursion. **Proving challenge:** instrumentation change
→ 1 here; no second recording rule exists (the witness R17 records ORM
writes, not field resolutions — different events).

### R14 — relation-intent walk + attestation manifest (file-local)

Members 75/76: post-`is_valid()` proof that `validated_data` still carries
the recorded objects by identity (renamed sources, injected relations,
lists length + pairwise, nested item order), pop/injection/substitution
all failing closed, plus the top-level captured-pk manifest for R16 and
the fully-consumed backstop. **Proving challenge:** walk change → 1 here;
no second intent-verification rule exists. D1 lives in member 76's
substitute-branch message.

### R15 — M2M snapshot + attestable census (file-local)

Members 77/78: pre-hook membership snapshot for top-level direct-M2M
write-surface specs on update (serializer-only relations skipped via
`FieldDoesNotExist`; forward-M2M tested via C8). **Proving challenge:**
snapshot/census change → 1 here; no second membership rule exists (the
attestation R16 CONSUMES the snapshot — producer/consumer halves, not two
definitions; member 78's C8 consumer edge is recorded at C8, no separate
row owed).

### R16 — post-save relation attestation (file-local)

Member 79: the DATABASE state of every supplied top-level FK/OneToOne
(one `values()` read, canonical `pks_match`) and M2M (set equality —
explicit-empty-list-clears and duplicate-collapse preserved) must match
the captured manifest; every omitted partial-update M2M must equal its
R15 snapshot. Custom nested persistence stays trusted by contract
(documented). **Proving challenge:** attestation change → 1 here; no
second attestation rule exists (no sibling flavor attests — the model
flavor has no consumer code between validate and save to distrust). D2
lives in member 79's FK read.

### R17 — signal write witness (file-local)

Member 80: thread-owned `pre_save` cross-alias blocker (body composed
from `make_cross_alias_save_guard`, serializer actor/recourse halves)
plus the backing-model `post_save` recorder with pk snapshots. Signal-less
same-alias bulk writes fail closed for create; the skeleton's statement
guard covers signal-less cross-alias paths (documented layering, verified
at the substrate). **Proving challenge:** H9 → 0 on the guard body, 1
here on halves/scope/record; no second witness exists.

### R18 — saved-result validation (file-local)

Member 81: correct model, `serializer.instance` identity, non-null pk +
not-adding, exact pinned alias, update pk == immutable `authorized_pk`
snapshot (canonical `pks_match`), create/update witnessed INSERT/UPDATE
by pk snapshot. **Proving challenge:** check change → 1 here; no second
saved-validation rule exists (the skeleton tail backstop is the shared
late enforcement — J9 records this site as the lawful early one; the
router re-check differs — J8).

### R19 — write step + guarded body (file-local skeleton adapters)

Members 82/83: snapshot fallback + hook-context construction + witness
span (82); M2M snapshot, frozen view, injection merge, kwargs merge,
construct, agreement, ownership, scope, pin, instrument, `is_valid()`
→ flattener, intent walk, save-kwarg hook + drift check + save inside
the value-preserving closure in a nested-atomic savepoint with the
three-branch DRF-first exception router, saved-check, attestation (83).
**Proving challenge:** step order/content → 1 here (the skeleton owns
the ORDER AROUND the steps — H5 → 0 here); no second serializer write
body exists. J21 records the save-mapper distinction.

### R20 — decode step (file-local skeleton adapter)

Member 84: `_decode_serializer_data` then wrap the single `FieldError`
in a list (the skeleton maps it). The located `instance` is correctly
NOT threaded (partial semantics live at construction). **Proving
challenge:** decode-adapter change → 1 here; no second serializer decode
entry exists.

### R21 — module scalar contracts + docstring projection (file-local)

Members 1/34/36: the omission sentinel (keeps explicit `data=None` /
`instance=None` distinguishable from omission in R5, and marks
ledger-exhaustion in R12 — one sentinel, two documented uses, same
"absent vs present-null" contract); the DRF non-field bucket key read
once from `api_settings` (single code site, git-grep census — normalizes
whatever key
the static configuration uses; production settings are fixed before
import, so no staleness reaches a request); the module docstring
(projection — every invariant clause verified against its body; the
authorize-before-decode, single-spine, and single-body clauses match;
two hook/intent clauses analyzed under D1). **Proving challenge:**
sentinel/key change → 1 here each; no second omission mark or bucket-key
read exists.

### R22 — import-reference totality (file-local mechanics)

Members 2–33: all 32 import members referenced at HEAD (P3) — each row in
`### Enumeration` names its consumer; `FieldError` is annotation-only
(zero constructions — envelope T-construct holds); no import exists for
re-export (this module owns no `__all__` leaf surface — consistent with
the verified leaf-guard posture). **Proving challenge:** an unreferenced
import would be dead code (principle 11) — the census finds none.

### J1 — nested-structure walk unification (REJECTED, fresh)

Seven recursions descend nested serializers: ownership over `(specs,
serializer, data)` with child-data union (58); scope over `(specs,
serializer, info)` with queryset rewrite (64); instrumentation over
`(specs, serializer, ledger)` with path threading (73); intent over
`(specs, serializer, validated_data, ledger)` with manifest + per-item
consume (76); nested-agreement delegating per child to field agreement
(61); reverse-map build over bare specs (48); validator pin over live
`serializer.fields` (63, no specs at all). Shared form considered: one
generic nested walker with per-level callbacks — owns only the
descend-via-`nested_serializer_child` skeleton (~4 lines each); the
remainder (subject, threading, per-node work, error contract) stays per
walk, and the callbacks would need mode flags for manifest/consume vs
rewrite vs union (principles 5/11: machinery hiding distinct behavior).
**Contract difference:** same traversal SHAPE, seven distinct contracts.
**Trigger:** a new walk sharing one walk's subject + threading + error
contract exactly (then it rides that walk's body). **Home:** this finding
(plus the per-walk docstrings, which already name their discipline).

### J2 — None-arm unification (REJECTED, fresh)

Four `None` policies: element skip in single decode (the spine's `skip`
slot — serializer's `None`-only skip), whole-list `None` pass-through in
multi decode (vs `[]` = valid clear, decided inside the shared compose),
nested `None` pass-through (parent validation decides), top-level
`data=None` → `{}` (empty provided data → required-field errors in-band).
Shared form considered: one `None`-guard helper — owns 2 lines × 3 plus a
divergent fourth arm; each arm answers a different decoder POSITION
(element vs list vs nested vs object) with a different downstream decider
(spine skip vs compose vs parent serializer vs `is_valid()`).
**Contract difference:** four positions, four deciders, one coinciding
spelling. **Trigger:** a decoder position whose `None` handling must move
in lockstep with another's (a shared `None`-semantics change). **Home:**
this finding.

### J3 — cycle-walker unification (REJECTED, fresh)

Two iterative cycle-guarded walks: the flattener (error nodes expanded via
`_error_node_children`, budget-capped with a `truncated` marker, no memo)
and the freeze (data containers finalized via `_finalize`, memo-shared
diamonds, no budget). Shared form considered: one cycle-guarded traversal
driver — owns the stack + active-set skeleton; node expansion, leaf
handling, memo-vs-budget, and failure contracts (fail-loud cyclic details
vs fail-closed opaque leaves) all stay per walk. **Contract difference:**
error-structure walk vs data-structure freeze; budget-vs-memo is a
per-walk necessity (fan-out cap vs sharing preservation). **Trigger:** a
third walk needing one walk's exact expansion + failure contract. **Home:**
this finding.

### J4 — context-gate vs `_hook_mapping` (REJECTED, fresh)

Member 55's nested `context` coercion (`isinstance` + `dict()`, `None` →
`{}`, no key gate) sits beside member 50's hook-return coercion (`None` →
error, non-`str` keys → error). Shared form considered: routing `context`
through `_hook_mapping` — wrong on all three axes: different input domain
(nested value vs hook return; the "must return a mapping" message misnames
the subject), different `None` policy (`{}` default vs malformed), and the
key gate is correctly ABSENT (context keys are never `**`-splatted, so no
downstream consumer can be destabilized — the documented reason the gate
exists). **Contract difference:** nested optional value vs hook return;
`None`-tolerant vs `None`-rejecting; unsplatted vs splatted keys.
**Trigger:** a nested hook value that IS splatted downstream (then it
takes the key gate too). **Home:** this finding + C11.

### J5 — shadow-guard vs model-field-guard split (REJECTED unification, fresh)

Members 65 (supplied-keys universe: the ACTUAL `validated_data` keys) and
66 (`_meta` universe: every field name + attname) overlap on supplied
model fields yet neither subsumes the other: 65 catches non-model
collisions (renamed inputs, defaults, hidden fields) that 66 cannot see;
66 catches unsupplied model fields (the unaudited-injection channel) that
65 cannot see. Shared form considered: one guard over the union — owns
the set-intersection spelling; the two universes + two messages (silent-
override vs unaudited-injection) stay. **Contract difference:** supplied
keys vs model-field universe; different failure meanings. **Trigger:** DRF
changing save-kwarg merge precedence (then exactly one guard moves).
**Home:** this finding.

### J6 — `_build_reverse_map` vs `mutation-input-reverse-map` (REJECTED, fresh)

The verified `mutation-input-reverse-map` family owns the model
field→`python_attr` triple — BUT its owner (`relation_input_python_attr`)
is ABSENT at HEAD bytes (present only as uncommitted adopted worktree
dirt: 5 hits worktree, 0 at HEAD), so this rejection is judged at HEAD,
converging only with the verified inputs-item DIRECTION (spec-construction
vs remap), never the unapplied consolidation. At HEAD the model mapping is
inline per-call (`field.name` / `f"{field.name}_id"` + camel); member 48
builds the RECURSIVE serializer-field→GraphQL-name + child-map for error
re-key at every depth. Shared form considered: one reverse-map rule —
different directions (build-time python naming vs error-time GraphQL
re-key), different shapes (flat triple vs recursive child maps), different
consumers (input construction vs flattener). **Contract difference:**
naming construction vs error re-key. **Trigger:** the family owner landing
at HEAD (then this finding re-checks against the landed owner). **Home:**
this finding.

### J7 — DRF vs Django code readers (REJECTED, fresh)

Member 46 reads `ErrorDetail.code` off DRF leaves (list/tuple walk +
bare); [errors][errors]`::_validation_codes` reads Django
`ValidationError` codes. Shared form considered: one code extractor —
the leaf SHAPES are disjoint upstream contracts (DRF `str`-subclass
leaves vs Django `error_dict`/`messages` structures); the readers already
terminate in one shared `field_error(codes=...)` sink. **Contract
difference:** DRF leaf codes vs Django validation codes. **Trigger:** a
leaf shape both readers must accept. **Home:** this finding.

### J8 — saved-alias check vs router re-check (REJECTED, fresh)

Member 81's `saved._state.db != alias` (state equality: the returned row
must live on the pinned alias) sits beside
`check_instance_write_alias` (router determinism: `db_for_write` with the
instance must repeat the no-instance answer). The member-81 docstring says
"mirroring" — the PURPOSE rhymes, the predicates differ: state-vs-pin vs
router-vs-pin. Shared form considered: calling the router check on the
saved row — answers a different question (the saved row's `_state.db` is
an observed fact about where the write LANDED; the router answer is a
routing DECISION). **Contract difference:** landed-state equality vs
routing determinism. **Trigger:** a saved row whose `_state.db` and router
answer must be checked as one predicate. **Home:** this finding.

### J9 — pk-drift early enforcement vs skeleton backstop (REJECTED consolidation, fresh)

Member 81 checks `pks_match(model, saved.pk, authorized_pk)` on update;
the skeleton tail checks `reject_substituted_row(model, saved.pk,
authorized_pk)` on update — same values, two positions. This is a lawful
SECOND ENFORCEMENT SITE, not a second definition: the equality is
single-sourced (`pks_match`, H7 → 1), the snapshot is skeleton-published,
and the positions differ (fail BEFORE attestation DB reads with a
serializer-specific message vs the flavor-independent backstop before the
re-fetch). Removing this site would let a drifted save run attestation
queries pointlessly; removing the backstop would unguard every flavor.
**Contract difference:** early flavor-positioned enforcement vs shared
late backstop; one equality. **Trigger:** a third enforcement site, or
either site diverging from `pks_match`. **Home:** this finding.

### J10 — nested-container error vs relation-id container error (REJECTED, fresh)

Member 41's "Expected a list of items" (a `NESTED_MULTI` value that is not
a list) sits beside `materialize_relation_id_container`'s text-atom guard
(a relation-id value that is not an id list). Shared form considered: one
container classifier — different subjects (nested input dataclass list vs
relation-id list), different atom rules (any iterable-of-inputs vs the
`RELATION_ID_ATOM_TYPES` exclusion set), different error contracts.
**Contract difference:** nested-input shape vs id-container shape.
**Trigger:** a value that is both (impossible today — kinds are
disjoint). **Home:** this finding.

### J11 — operation-discrimination shapes (REJECTED, fresh)

Three "am I an update?" lenses: `operation == "update"` (member 59,
operation string), `operation_kind == PARTIAL` (build-time kind
constant), `instance is not None` (member 55, located-instance presence).
Shared form considered: one `is_update` helper — machinery over a CLOSED
two-value vocabulary (upstream-validated); each site reads the artifact
its phase provides (build kind vs operation string vs skeleton locate
result). **Contract difference:** three phases, three artifacts, one
closed vocabulary. **Trigger:** a third operation kind, or a site holding
two artifacts and picking inconsistently. **Home:** this finding.

### J12 — annotation recompute vs build produce (round-trip halves; REJECTED merge, fresh)

Member 59 re-derives the runtime annotation via `resolve_serializer_field`
+ `optional_input_field` and compares `repr()` against the recorded
`annotation_repr` — the build's production half ([rf-inputs][rf-inputs]
walk) vs this verification half. Merging them (guard reads the build's
recorded annotation instead of recomputing) would destroy the check: a
verification MUST recompute independently. The halves already compose the
same two functions by name; only the provisional-name input restates
(FAM-NEW — carved out, not part of this rejection). Requiredness honors
DRF `partial=True` semantics on the runtime side (update → effectively
optional), not the schema side. **Contract difference:** production vs
verification; recompute-and-compare is the contract. **Trigger:** a third
annotation production site. **Home:** this finding.

### J13 — serializer-vs-form decode mirror (REJECTED; CONVERGE with forms R1 + skeleton distinct, fresh)

Member 37–40 mirror the 038 form decoders field-for-field (spine call,
keyed payload, visibility on every branch) with three deliberate
colorings: serializer-field-keyed (`spec.target_name` for DRF `source`
mapping) vs form-field-keyed; `None`-only skip vs `empty_values` skip;
`obj.pk` projection vs `to_field_name` projection. Shared form considered:
one parametrized decoder — the key spaces, skip contracts, and projection
needs are per-flavor validation contracts (DRF reads `data` by declared
name; forms need the object for `to_field_name`). Fresh evidence: both
decoders read whole at HEAD; the spine already owns everything shared
(H2 → 0/1). **Contract difference:** DRF data contract vs Django form
contract. **Trigger:** a decoder needing the other flavor's key space.
**Home:** this finding.

### J14 — frozen hook record vs live-instance hooks (REJECTED; CONVERGE with hook_context R5, fresh)

The three serializer hooks receive the frozen `SerializerHookContext`
(`instance_pk`, never the row) while model `check_permission` and the form
seams take the live instance / bare operation string. Shared form
considered: one cross-flavor hook context — the frozen posture is
serializer-only by contract (spec-039 Decision 8; hooks here run
post-auth pre-write with mutation power over reserved merge keys, so the
row must be unreachable). Fresh evidence: hook signatures + call sites
read at HEAD in all three flavors; the one genuine sharing at the seam
(`construction_kwargs`, used by the form default and the serializer
default) is already single-sited. **Contract difference:** frozen
post-auth mutation seam vs live read/permission seams. **Trigger:** a
sibling flavor adopting the frozen posture. **Home:** this finding.

### J15 — partial-update mechanisms (REJECTED; CONVERGE with forms J1, fresh)

Serializer `partial=True` injection (member 55, update only) vs form
`_reconstruct_partial_data` (full bound `data=` rebuild) vs model
`setattr`-on-located-row. Shared form considered: one partial mechanism —
disjoint validation substrates (DRF partial validation vs Django form
binding vs model attribute assignment); each mechanism is owned by the
substrate that validates it. Fresh evidence: all three mechanisms read at
HEAD. **Contract difference:** three substrates, three partial
semantics. **Trigger:** a substrate change collapsing two mechanisms.
**Home:** this finding.

### J16 — batched vs per-element multi decode (REJECTED; CONVERGE with forms J2, fresh)

Member 38 rides the batched `pk__in` compose (one visibility query —
needs only pks for `PrimaryKeyRelatedField`); the form multi decoder maps
the single spine per element (needs each OBJECT for `to_field_name`).
Shared form considered: batching the form arm — the form's projection
need forbids it (documented at the spine: "it needs the object").
**Contract difference:** pk-needing vs object-needing consumers.
**Trigger:** a consumer needing both (then the spine gains a third shape).
**Home:** this finding.

### J17 — null-M2M / None policies (REJECTED; CONVERGE with forms J3 + envelope distinct, fresh)

Serializer `None` pass-through (single skip, whole-list, nested — the
serializer's own validation decides required-ness) vs form `empty_values`
skip vs model whole-list-`None` reject. Shared form considered: one null
policy — per-flavor validation contracts (DRF `is_valid()` owns
required-ness here; Django form emptiness there; model construction
rejects). Fresh evidence: all three policies read at HEAD; the spine
docstring records the split ("Flavor null policy stays at the caller").
**Contract difference:** three validation contracts. **Trigger:** a flavor
surrendering required-ness to another's contract. **Home:** this finding.

### J18 — FILE routing `data` vs `files=` (REJECTED; CONVERGE with forms R2/axis-4, fresh)


Member 40 calls `decode_field_handlers` WITHOUT `file_dest`, so FILE lands
in `provided_data` (DRF reads uploads from `data`); the form flavor passes
`file_dest=provided_files` (Django `files=`). Shared form considered: one
FILE destination — the destinations ARE the per-substrate contracts, and
the factory already owns the variation (`file_dest` parameter — H1 axis).
Fresh evidence: both call sites read at HEAD. **Contract difference:** DRF
`data` vs Django `files=`. **Trigger:** a substrate accepting the other's
destination. **Home:** this finding.

### J19 — `EXCLUDED` unreachability (REJECTED gap; mirror of forms axis-6, fresh)

`decode_provided_fields` falls unknown kinds back to the scalar handler, so
an `EXCLUDED` serializer spec would mis-decode — but serializer specs can
never carry `excluded`: the converter stamps only its own kinds (zero
`EXCLUDED` tokens in the serializer build at HEAD; the one prose mention
concerns enum exclusion, not the kind). Unreachable by construction, not a
gap — no defect. **Trigger:** a serializer spec stamping `excluded` (then
the fallback needs a kind arm). **Home:** this finding.

### J20 — `_relation_model_of` vs taxonomy reads (REJECTED, fresh)

Member 56 reads `field.queryset.model` (or `child_relation.queryset.model`)
off a DRF relation field — a DRF-runtime shape read. The relation-kind
taxonomy classifies DJANGO model fields; the instance accessor resolves
Django descriptors. Shared form considered: routing the read through the
taxonomy — the subjects are disjoint layers (DRF field objects vs Django
`_meta`). **Contract difference:** DRF runtime shape vs Django model
shape. **Trigger:** a DRF field whose target model must be classified as
a Django relation kind. **Home:** this finding.

### J21 — three-branch save mapper vs `save_or_field_errors` (REJECTED; CONVERGE with the forms-artifact note, fresh)

Member 83 routes save-time failures by exception CLASS in three branches
(DRF-first): DRF `ValidationError.detail` → recursive flattener; Django
`ValidationError` → flat mapper (`error_dict`/`messages`, never
`.detail`); `IntegrityError` → shared integrity mapper. The shared
`save_or_field_errors` maps `IntegrityError` only. Shared form considered:
routing the serializer save through it — the DRF/Django validation
branches are disjoint exception contracts the shared mapper cannot see
(it takes a zero-arg callable and catches one class); only the
`IntegrityError` arm composes (it calls the same shared mapper by name).
Fresh evidence: both bodies + the save-time oracle rows read at HEAD
(recursive-vs-flat pins, rollback pin, exactly-once pin). **Contract
difference:** three-class router vs one-class mapper; one shared arm.
**Trigger:** a fourth save-time exception class (then exactly one router
moves). **Home:** this finding.

## Defects

Non-duplication bugs found while tracing, each with the owner it routes
to. Never fixed inside the item; Worker 0 homes each on a NAMED owning
card before closeout.

### D1 — substitute-branch message permits `pop`, but popping fails closed (HEAD defect)

- **What.** Member 76 raises three intent `ConfigurationError`s. The pop
  branch says "Validators may reject a supplied relation, never pop it";
  the fully-consumed backstop says "never drop it"; but the
  SUBSTITUTE-branch message says "Validators may reject or pop a
  relation, never substitute it." Popping always raises (the direct-pop
  guard + the backstop, both unconditional), so the "or pop" clause
  misstates the enforced contract: an author who follows it pops the
  relation and hits the pop error next.
- **Contract row.** The intent-walk contract as enforced: pop fails
  closed — pinned by oracles in [test-rfresolvers][test-rfresolvers]
  (`test_object_validator_popping_a_supplied_relation_is_rejected`
  matching "removed from validated_data by a validator";
  `test_nested_relation_nulled_after_validation_is_rejected` matching
  "removed from validated_data before the write") plus the two sibling
  messages.
  Likely origin: the archived spec-039 sentence "A validator may reject
  or pop a relation (popping reverts to omitted semantics)" matches the
  wrong clause — the code + tests moved to fail-closed while the sentence
  (and this clause) stayed. Whether the archived spec needs an amendment
  note is the maintainer's call at homing.
- **Feasible shape + reaching input.** Any `SerializerMutation` with a
  relation + a validator that substitutes a resolved row → the substitute
  branch fires on a real create/update mutation, and its guidance is
  wrong. The defect is guidance text, not behavior: behavior is correct
  (fail closed on pop AND on substitute).
- **Fix shape (for the owner, not this item).** Drop "or pop" from the
  substitute-branch message (one clause); optionally amend the archived
  spec sentence.
- **Dirt note.** The enclosing message's FIRST line carries a hunt hunk
  (class-name safe rendering); the clause line itself is byte-identical
  HEAD-vs-worktree. Filed as a HEAD defect with normal homing; closeout
  re-verifies the clause survives the hunt's rewrite.
- **Owner.** File `rest_framework/resolvers.py` (R14 intent-walk rule).

### D2 — attestation FK read raises raw `DoesNotExist` on a vanished row under `select_for_update=False` (HEAD defect)

- **What.** Member 79's FK attestation reads the saved row with
  `model._base_manager.using(alias).values(...).get(pk=saved.pk)` — a
  bare `.get()` with no `DoesNotExist` handling. It runs AFTER the save
  and BEFORE the skeleton tail. If the row vanishes between the save and
  this read (a concurrent delete committing in the window), the read
  raises raw `DoesNotExist` (a top-level 500) instead of reaching the
  tail's disappearing-row `conflict` envelope.
- **Contract row.** The skeleton tail's disappearing-row contract
  ([mresolvers][mresolvers] tail: "a concurrent delete this transaction
  could not see" → in-band `conflict` envelope + rollback). The model and
  form flavors reach that envelope (they run no post-save `.get()`); the
  serializer flavor bypasses it at this site.
- **Feasible shape + reaching input.** `SerializerMutation` update with
  `Meta.select_for_update=False` (a supported, validated opt-out; the
  default `True` closes the window via the locate lock, which is why the
  suite never sees this) + a client-supplied single relation (so
  `fk_checks` is non-empty) + a concurrent delete committing between the
  save and the attestation read → a real update mutation 500s instead of
  returning `conflict`. Window is microseconds, but the tail's own comment
  establishes the scenario is in-contract.
- **Fix shape (for the owner, not this item).** Treat the vanished row at
  this site the way the tail does (skip attestation and let the tail
  conflict, or map to the conflict envelope) — a design decision for the
  fixer; the defect is the unhandled `.get()`, on clean lines (between
  hunt hunks, byte-identical).
- **Owner.** File `rest_framework/resolvers.py` (R16 attestation rule).

### Candidates examined and cleared (not defects)

- Injected-field errors key verbatim by declared name (reverse map covers
  input specs only): the only honest key — injected fields own no GraphQL
  input name (C3).
- `_relation_model_of` returning `None` when the runtime queryset is
  `None`: unreachable downstream — the build fails loud without a
  concrete `queryset.model`, so the agreement mismatch fires first (R6).
- `_DRF_NON_FIELD_KEY` read once at import: production settings are fixed
  before import; no test overrides the DRF key (R21).
- Hostile hook values (`__eq__` / `__repr__` raising inside merge/compare
  paths): no contract row establishes the failure mode, and the concurrent
  hunt owns the hostile-value population — left to that cycle, not filed
  here.

## Pending execution

None. All proofs above are `static-reviewed` (HEAD-byte censuses P1–P3,
bodies read at HEAD, dirt-disjoint per P2) — no `proof:` entry is owed,
and no `gate:` witness routes anywhere. Sharded and Postgres cells are
inapplicable by construction: no probe opens a database (P1 imports
nothing and reads only git bytes), so no executed claim can vary by
alias or dialect; the DB-touching oracles cited (live envelopes, scope
pins) belong to the plan's final-gate item, not this one.

## Judgment

The serializer write runtime is a disciplined skeleton rider: one shared
lifecycle (skeleton + factory + boundary + envelope + spine + substrate,
all composed by name) with genuinely serializer-only adapters (decode
coloring, nested recursion, recursive flattener, hook hardening,
agreement, scoping, intent, witness, attestation) — each single-sited,
each defended by a proving challenge. One real duplication found (the
provisional-name restatement → FAM-NEW for a family item); one adoption
into an open family (C11); everything else converges fresh, stays
file-local, or rejects with a contract difference + trigger. Two defects
filed (D1 message-vs-behavior, D2 vanished-row raw raise), both meeting
the Trust-boundary bar. Zero tracked edits; the item-scoped diff is the
new artifact only.

## Implementation (Worker 1)

Tracked changes: NONE (file item; no production edits, no ledger rows).
The item-scoped diff vs `ITEM_BASELINE=2759e0a1` is the new untracked
artifact only; every other delta in the tree is concurrent dirt,
attributed by content and left alone (P2: the target's own 39-hunk
+129/-77 worktree delta is the hostile-value-guard campaign, disjoint
from every skeleton / factory / spine / envelope site; the one
naming-site touch is the FAM-NEW line's base-name half, whose
suffix-conditional half is byte-identical).

- HEAD at dispatch `5ee86193`, confirmed still `5ee86193` at finish
  (`git rev-parse HEAD` immediately before writing this section).
- Target fingerprints: HEAD blob `8024703e` (`git rev-parse
  HEAD:<path>`), worktree blob `c0b54039` (`git hash-object <path>`) —
  never compared across methods.
- Connected-file fingerprints (HEAD blob via `git rev-parse HEAD:<path>`
  / worktree blob via `git hash-object <path>`; DIRTY files were judged
  at HEAD bytes — `git show HEAD:<path>` — throughout):

| State | HEAD | Worktree | Path |
|---|---|---|---|
| DIRTY | `3fd1e571` | `a322d17a` | `django_strawberry_framework/mutations/resolvers.py` |
| CLEAN | `4edb984b` | `4edb984b` | `django_strawberry_framework/forms/resolvers.py` |
| CLEAN | `d28587c7` | `d28587c7` | `django_strawberry_framework/utils/write_values.py` |
| DIRTY | `3e25e93b` | `6bb0ad3f` | `django_strawberry_framework/utils/errors.py` |
| DIRTY | `eca9ad4d` | `9ad493b6` | `django_strawberry_framework/utils/write_transaction.py` |
| DIRTY | `b68be0e3` | `e0b0651a` | `django_strawberry_framework/utils/querysets.py` |
| DIRTY | `ee31d360` | `47b2af21` | `django_strawberry_framework/utils/inputs.py` |
| CLEAN | `9889d6fe` | `9889d6fe` | `django_strawberry_framework/utils/permissions.py` |
| DIRTY | `7662b0bb` | `1cf81e58` | `django_strawberry_framework/utils/relations.py` |
| DIRTY | `fc442047` | `fcbb964d` | `django_strawberry_framework/mutations/inputs.py` |
| DIRTY | `cffa29e5` | `936f5ae7` | `django_strawberry_framework/mutations/sets.py` |
| CLEAN | `9b17d952` | `9b17d952` | `django_strawberry_framework/rest_framework/inputs.py` |
| DIRTY | `2c7117d6` | `70a1e1b1` | `django_strawberry_framework/rest_framework/sets.py` |
| DIRTY | `32904418` | `95568390` | `django_strawberry_framework/rest_framework/serializer_converter.py` |
| CLEAN | `f4910159` | `f4910159` | `django_strawberry_framework/rest_framework/hook_context.py` |
| CLEAN | `45cf7b63` | `45cf7b63` | `django_strawberry_framework/rest_framework/__init__.py` |
| CLEAN | `e06b0b7f` | `e06b0b7f` | `django_strawberry_framework/exceptions.py` |
| DIRTY | `8dc889fd` | `b8ce1dfd` | `tests/rest_framework/test_resolvers.py` |

- Searched populations (all at HEAD): whole-package `git grep` censuses
  for factory riders (3), skeleton riders (5), recourse calls (3),
  spine consumers (form + serializer factories; model + serializer
  batched; form + serializer single), hook-record constructions (1 each),
  hook-default call sites (2 `construction_kwargs`), visibility-helper
  calls, ownership/nested call sites, conditional-suffix sites (2),
  plus the P1 AST census (86/0/0/15). Any fingerprint change reopens the
  findings citing that file.
- Scratch created (untracked, kept small, removal is Worker 0's after
  `verified`, by explicit path):
  `docs/dry/temp-tests/dry-file-rest_framework__resolvers/p1_census.py`
  (read-only census; `ruff check` + `ruff format` clean on exactly that
  path, format last). No workspace copy was owed (no source-mutating
  proof); no `pytest` run (not authorized by the entry).
- Worker 0 transcriptions (exact text; Worker 0 alone edits the plan):
  (1) FAM-NEW index row + `## Families` item as spelled in FAM-NEW;
  (2) C11 coverage append (`.../rest_framework/resolvers.py` onto the
  `hostile-mapping-hardening` index row); (3) home D1 + D2 on NAMED
  owning cards before closeout (both owned by File
  `rest_framework/resolvers.py` rules R14/R16).

## Independent verification (Worker 2)

Recorded BEFORE opening `## Findings` (headings + dispatch brief only;
all bytes below are my own HEAD trace).

Target `django_strawberry_framework/rest_framework/resolvers.py` at HEAD
`5ee86193`: blob `8024703e` (`git rev-parse HEAD:<path>`), 2432 lines,
86 `ast.Module.body` members (45 `FunctionDef` + 1 `ClassDef` + 4
`Assign` + 3 `AnnAssign` + 1 docstring `Expr` + 32 imports), 15 nested
`def`s (6 under `_frozen_hook_view`, 4 `_RelationIntentLedger` methods,
2 under `_pin_validator_querysets`, 1 each under
`_decode_input_object`, `_record_field_intent`, `_write_witness`).
Worktree blob `c0b54039` (+129/-77, 39 hunks); every hunk I sampled is
hostile-value-guard dirt (`isinstance` armor, `_safe_*` renderers,
`BaseException` arms, guard prose) — concurrent hunt work, absent from
the ledger, left alone. Window `git diff 2759e0a1 --name-only` names
ONLY `docs/dry/dry-0_0_15.md` (Worker-0 dispatch accounting, 22
insertions) — nothing to re-attribute. Connected files judged at HEAD
bytes via `git show HEAD:<path>` throughout (`mutations/resolvers.py`
`3fd1e571`, `forms/resolvers.py` `4edb984b`, `utils/write_values.py`
`d28587c7`, `utils/errors.py` `3e25e93b`, `utils/write_transaction.py`
`eca9ad4d`, `utils/querysets.py` `b68be0e3`, `utils/inputs.py`
`ee31d360`, `rest_framework/inputs.py` `9b17d952`,
`rest_framework/serializer_converter.py` `32904418`,
`rest_framework/hook_context.py` `f4910159` — each re-hashed by me,
each matching W1's table where it names them).

My trace, by responsibility (sites + roles + counts + the owner call I
would make):

- Skeleton rider (consumer). `_run_serializer_pipeline_sync` passes
  `decode_step`/`write_step` lambdas to
  `mutations/resolvers.py::run_write_pipeline_sync` (owner; docstring
  names the serializer flavor explicitly). Package census: 5 rider call
  sites (mutations x2, forms, auth, serializer) — enforcement sites,
  not definitions. Posit "authorize-after-decode": count 1 (the owner).
- Entry factory (product). `resolve_serializer_sync/_async =
  make_resolver_entries(_run_serializer_pipeline_sync)`; 3 package
  riders (model/form/serializer), each call producing fresh functions.
  Posit "UNSET-default change": count 1 (the factory).
- Async boundary (transitive consumer). No `sync_to_async` import or
  call in the target (only docstring/comment mentions); the async entry
  rides factory -> `run_pipeline_async` ->
  `utils/querysets.py::run_in_one_sync_boundary` (owner). Posit
  "thread-sensitivity change": count 1.
- Recourse wording (consumer). `_SERIALIZER_ASYNC_RECOURSE =
  sync_pipeline_recourse("serializer mutation")`, used at 3 sites
  (single/multi decode, scope walk); 3 flavor constants package-wide,
  all computed from the `utils/querysets.py` template. Posit
  "recourse reword": count 1 (the template); per-flavor nouns stay.
- Decode spine (coloring consumer). `_decode_relation_single/_multi`
  wrap `decode_visible_relation`/`decode_visible_relation_ids`;
  `_decode_input_object` composes `decode_provided_fields` +
  `decode_field_handlers` + `decoded_into` with `extra_handlers` for
  nested; scalar leaf rides the shared handler. The form twin
  (`forms/resolvers.py::_decode_form_data`) composes the same spine
  with different coloring (`file_dest=provided_files`, `to_field_name`
  arms). Posit "UNSET-strip change": count 1 (the spine).
- Error envelope (adapter consumer). `serializer_errors_to_field_errors`
  + `_error_node_children`/`_error_leaf`/`_error_detail_codes`/
  `_rekey_segment` terminate in the shared `field_error` leaf ctor +
  `NON_FIELD_ERROR_KEY` + `join_error_path` (`utils/errors.py` owners);
  save-time Django/Integrity failures call the flat `036` mappers by
  name. The recursive-vs-flat split is a contract difference (nested
  DRF detail vs flat Django error), not two definitions of one rule.
  Posit "leaf shape change": count 1 (the ctor).
- Write-transaction substrate (consumer). `require_write_pipeline`,
  `pipeline_write_phase` (5th enforcement site: forms x2, mutations
  x2, serializer x1 — the DRY.md five-flavors shape), `pin_write_queryset`,
  `base_locked_queryset`, `make_cross_alias_save_guard`, `pks_match`,
  `assert_no_target_drift` all called by name. Posit "phase-guard
  change": count 1 (the substrate).
- Visibility (consumer). `_scope_specs_over_serializer` calls
  `related_visibility_queryset` (owner `utils/querysets.py`) and ANDs
  it as `pk__in`; decode-side visibility rides the spine's
  `visible_related_object` path. Posit "visibility-query change":
  count 1.
- Taxonomy (consumer). `_attestable_m2m_fields` calls
  `utils/relations.py::is_forward_many_to_many` by name (also consumed
  by forms/inputs + mutations/inputs). `_relation_model_of` reads
  `queryset.model` off DRF relation fields — a different read (target
  model of a serializer field vs M2M-shape predicate), not a second
  taxonomy definition. Posit either change: count 1 each.
- Inputs rows (consumers). `raise_writable_source_ownership_errors` +
  `runtime_validated_data_fields` (`rest_framework/inputs.py` owners),
  `nested_serializer_child` + kind constants
  (`serializer_converter.py` owners), `optional_input_field` +
  `generated_input_type_name` (`utils/inputs.py` owners),
  `request_from_info` (`utils/permissions.py` owner) — all composed by
  name; the target's recursion/ownership/agreement walks are the
  serializer-colored enforcement, not restatements.
- Hook record (sole producer). Exactly one `SerializerHookContext(...)`
  construction package-wide (target L2190); the frozen record +
  `UploadMetadata` are owned by `hook_context.py`. Posit "context
  field change": count 1 (the record).
- Hostile-mapping gate (family member). `_hook_mapping` (Mapping gate
  -> `dict()` materialize -> non-string-key offenders -> typed
  `ConfigurationError`) shares the materialize-once + key-guard
  mechanism with the OPEN `hostile-mapping-hardening` family
  (`utils/policies.py`, `conf.py`, `types/base.py`; owner TBD; no
  artifact on disk). It lacks the closed-vocabulary arm, so partial
  membership at most — the family item's decision. I would adopt this
  site into that family's member list.
- Provisional name (REAL DUPLICATION, count 2). Target HEAD L1213
  builds `f"{...}{'PartialInput' if operation == 'update' else
  'Input'}"` inline; the canonical owner is
  `utils/inputs.py::generated_input_type_name` (suffix rule +
  full-vs-derived branching), composed by name at every other site
  (`name_set_input_type_name`, `serializer_input_type_name`, both
  `rest_framework/inputs.py` provisional builds). Package-wide
  suffix-spelling census: exactly 2 sites. Posit "suffix rename":
  count 2. The target could call the owner with
  `(base, is_partial=..., is_full_shape=True, token="")`. This is a
  NEW family for Worker 0; a file item routes it, never edits it.
- File-local (my calls, each count 1 after a package census): the
  relation-decode coloring pair, nested recursion + list-shape guard,
  the iterative flattener + node budget + cycle guard, the freeze
  tables + iterative `_frozen_hook_view` + upload descriptor, the
  injection exact-match, the constructor-kwarg reserved merge
  (sentinel + identity + context gates), the schema/runtime agreement
  tower (field/relation/nested + requiredness/annotation), the runtime
  ownership recursion, the queryset AND-scope walk, validator pinning,
  the save-kwarg shadow/model-field pair, the write-surface spec list,
  the intent ledger + snapshot + identity compare + instrumentation +
  walk + manifest, the M2M snapshot + attestable census, the post-save
  attestation, the signal witness, the saved-result checks, the two
  skeleton-adapter steps, module constants + docstring projection.
- Rejections I would record (contract difference + trigger): recursive
  flattener vs flat mappers; freeze vs copy; `_hook_mapping` vs the
  context-mapping arm (open hook kwargs vs framework-owned context
  merge — hmm, actually the context arm inside `_merged_serializer_kwargs`
  re-spells Mapping-gate + materialize; I need to check whether that is
  a second definition of the `_hook_mapping` rule before I accept any
  rejection of it); shadow vs model-field save guards (supplied-key
  collision vs unaudited injection — different predicates); reverse-map
  build vs input reverse maps (error re-key vs decode routing —
  different directions); DRF vs Django save-time mappers (`.detail` vs
  `error_dict` — different exception contracts); pk-drift early check
  vs skeleton backstop (serializer-specific vs flavor-independent —
  layering, keep both); FILE-into-`data` vs form `files=` (DRF vs
  Django contract — deliberate contrast).
- Defects I found on my own trace (Trust-boundary bar):
  (W2-a) The substitute-branch message "Validators may reject or pop a
  relation, never substitute it." contradicts the pop branch ("never
  pop it") and `_assert_relation_intent`'s "only rejection is" —
  message-vs-behavior; contract row = the pop guard's fail-closed
  behavior; reaches any consumer validator that substitutes. Clause
  line byte-identical HEAD-vs-worktree; enclosing `f"SerializerMutation
  ..."` line hunt-dirtied (`_safe_class_name`).
  (W2-b) `_attest_saved_relations` FK read-back is a bare
  `.values(...).get(pk=saved.pk)`: under the supported
  `Meta.select_for_update = False` opt-out a concurrent delete between
  save and attestation raises raw `DoesNotExist` (500) instead of
  reaching the tail's disappearing-row `conflict` envelope — no
  `except` wraps `write_step` in the skeleton, and the tail contract
  (same race, save -> re-fetch) proves the envelope is the intended
  outcome. Clean HEAD lines.

Matrix judgment (my own discharge): axis 1 read the model/form twins +
  spine + envelope + substrate (done above); axis 2 the target is a
  sync-only body behind the factory boundary — no twin, inapplicable
  by construction (no `async def`, no direct `sync_to_async`); axis 3
  the provisional-name restatement is the one derived-knowledge hit
  (count 2, family-routed), everything else composes by name; axis 4
  the annotation round-trip (build-produce vs guard-recompute) and the
  reverse maps are halves held apart by contract (producer vs
  checker), not duplicated grammars; axis 5 oracles (tests) + docstring
  projections move with intent, never as definitions — no oracle
  rewrite owed or made; axis 6 the write-surface walks + ledger
  backstop + omitted-M2M attestation show the enforcement population
  is enumerated per discipline (omission would be a defect with a
  contract source, none found beyond W2-b's missing miss-arm, which is
  filed, not silently added).

(End of pre-Findings trace. What follows was written AFTER opening
`## Findings`, reconciling each difference explicitly.)

### Reconciliation (post-Findings)

**Enumeration: ACCEPTED member-by-member with 1 correction.** My own AST
dump over HEAD bytes gives the identical population: 86 members
(1/25/7/45/1/4/3 by kind — verified again by executing P1, output
matches the artifact record line for line) + the identical 15 nested
defs. Every homing cell matches a home I would assign; the nested list
names all 15. Correction W2-C1: row 24 says "(8 names)" — the errors
import carries **7** names at HEAD L142-150 (recounted by hand and
pinned by my W2 probe). Polish (optional): rows 2 (`from __future__`)
and 13 (`typing.Any`) home to "consumer (exempt)"/"consumer" without a
named row; R22's "all 32 import members" sentence covers them
transitively, but naming R22 in those two cells would close the
backstop literally.

**Matrix: ACCEPTED on all six axes.** Each was discharged against the
target's real surface, and my pre-Findings discharge independently
reached the same verdicts: axis 1 (twins + spine + envelope + substrate
read first — I re-read the same bodies), axis 2 (sync-only body, factory
boundary; my grep confirms zero `sync_to_async` code tokens), axis 3
(the provisional restatement is the one hit — my package census agrees
it is exactly 2 sites), axis 4 (round-trip halves held apart by
contract), axis 5 (oracles/projections classified; no oracle rewritten —
and none owed), axis 6 (kind coverage total; guards serializer-scoped by
contract). The sharded/PG "inapplicable by construction" attaches to
the static proofs (AST + git-grep censuses open no database), with the
DB-touching oracles routed to the final gate — accepted for this
zero-edit item.

**C1–C12: ALL ACCEPTED (verdicts), each re-derived on fresh evidence.**

- C1: rider + product confirmed (5 riders / 3 pairs re-censused; the
  skeleton docstring names the serializer flavor; all machinery sits
  inside `write_step` post-auth). Converge accepted.
- C2: transitive consumer confirmed (no boundary spelled here; factory
  body read at HEAD routes through `run_pipeline_async`). The
  principle-5 contrast citation is accurate. Accepted.
- C3: adapter confirmed. The T-construct/T-shape/T-code trigger names
  are real (envelope artifact L345-351, which also names "the DRF
  flattener" and the recursive-vs-flat split); all three hold fresh
  (P1 re-executed). The injected-verbatim note is correct (reverse map
  built from `_input_field_specs` only, HEAD L2175). Accepted.
- C4: consumer confirmed (3 calls re-censused; template body read at
  HEAD). The "rejected family" posture matches the recorded rejection
  (per-flavor constants stay, sentence single-sourced) and the forms F1
  converge. Accepted.
- C5: membership confirmed (the helper docstring names this module's
  scope walk; None-tail is pin + lock only). Note, no change required:
  W1 names the directly-called `related_visibility_queryset` while the
  index row names the `_or_default` wrapper — correct, because the
  wrapper's default-manager tail is the wrong contract for this surface
  (this surface skips visibility on None, it does not default it). A
  one-line note of that hierarchy would preempt confusion (optional).
- C6: runtime consumer confirmed (2 call sites per helper re-censused:
  sets schema arm + resolvers runtime arm; defs in `rf-inputs`).
  Accepted.
- C7: consumer confirmed (5 target sites re-censused; all compose by
  name). Correction W2-C2: the package total is **8**, not 7 — W1
  omits the schema-time call at `rest_framework/sets.py:431` (class-
  creation ownership walk, nested recursion). Correct split: 3
  schema-side (inputs x2 + sets x1) + 5 here. Pinned by my W2 probe.
- C8: consumer confirmed (taxonomy owner read; single call here; J20
  correctly separates the DRF-side read). Accepted.
- C9: consumer confirmed — all 12 call sites re-censused exactly
  (pin x3, require x2, lock x1, match x3, guard x1, drift x1, phase
  x1). Accepted.
- C10: non-caller posture confirmed (zero tokens, P1 re-executed).
  Accepted.
- C11: ADOPTION ACCEPTED. `_hook_mapping` (Mapping gate -> `dict()`
  materialize -> non-`str`-key reject -> typed `ConfigurationError`)
  shares the open family's materialize-once + key-guard mechanism; the
  three hook-boundary call sites + the oracle pins for all three
  rejection shapes verified fresh. It lacks the closed-vocabulary arm,
  so partial membership — correctly left to the family item, whose
  transcription only appends the file. J4 (accepted below) correctly
  separates the R5 context arm rather than folding it in. Accepted.
- C12: sole producer confirmed (exactly 1 package construction per
  record re-censused; no package production read of the record
  attributes; the one in-tree consumer read is the fakeshop library
  override). Accepted.

**FAM-NEW: ACCEPTED with 1 correction.** The restatement is real
duplication, count 2: package-wide conditional-suffix census is exactly
2 (owner + guard f-string, P1 re-executed); the equivalence argument
verified fresh (top base equality; closed create/update vocabulary,
`rf-sets.py:468`; nested re-entry through the same builder with its own
class-name provisional, matching the guard's per-level re-derive; the
`describe_serializer_input` diagnostic aside, every other site composes
by name). The migration call is dependency-clean and behavior-identical
by that equivalence. No verified row is contradicted (F-SHAPE owns the
divergent name, a different sub-rule). Correction W2-C3: composed calls
are **5**, not 4 — W1 omits `describe_serializer_input`
(`rf-inputs.py:938`, diagnostic canonical-name recompute, calls the
owner by name). H6's "4 composed calls" moves with it. Pinned by my W2
probe. The family-item transcription (index row + Families item) is
otherwise exact.

**R1–R22: ALL ACCEPTED.** Each carries a proving challenge with a
count-1 (or counted-0-here) outcome I independently agree with; the
censuses I re-derived match (R11: 7 call sites; R21: single bucket-key
code read, sentinel's two uses; R22: my own P3 redo finds all 63
imported names referenced except the unreferenceable `__future__`
symbol). No second site exists for any of them on the populations I
swept. The ledger/attestation producer-consumer split (R12/R14/R15/R16)
is correctly recorded as halves, not definitions.

**J1–J21: ALL ACCEPTED.** Every rejection carries a contract difference
+ trigger + home. The ones I stress-tested hardest:

- J4 (context-gate vs `_hook_mapping`): accepted — I independently
  derived the same three axes (nested-value vs hook-return domain,
  None-tolerant vs None-rejecting, unsplatted vs splatted keys) before
  opening Findings; folding would need a mode flag (principle 5) and
  would ADD a rejection (behavior change, not preservation).
- J6: accepted — owner absent at HEAD (0 hits) vs 5 worktree-dirt hits
  verified; judging at HEAD and converging only with the inputs-item
  direction is exactly right.
- J9: accepted — lawful second enforcement site, one equality
  (`pks_match`), positions differ with reason (pre-attestation vs
  pre-refetch).
- J12: accepted — verification must recompute; FAM-NEW correctly carved
  out rather than folded in.
- J13/J15/J16/J17/J18/J21: accepted — each twin cite verified at HEAD
  bodies (form `empty_values` + `to_field_name`, `construction_kwargs`
  single-siting with the two defaults, spine "needs the object" +
  "Flavor null policy stays at the caller" docstrings, form
  `file_dest=provided_files` vs target's absent arg, `EXCLUDED`
  single-prose-mention, `save_or_field_errors` zero-arg +
  IntegrityError-only).
- J1/J2/J3/J5/J7/J8/J10/J11/J19/J20: accepted — shared forms considered
  with per-finding counts, differences genuine, triggers concrete.

**D1: ACCEPTED as a HEAD defect (Trust-boundary bar met).** Message-vs-
behavior: the substitute branch's "or pop" contradicts the pop branch
("never pop it"), the backstop ("never drop it"), and the intent-walk's
"only rejection is". Contract row = the enforced pop-fails-closed
behavior, pinned by both named oracles (verified present at HEAD,
L4167/L4669, in the 164-function file). Feasible shape + reaching input
(any relation-carrying serializer mutation whose validator substitutes)
verified. Likely origin confirmed stronger than stated: the archived
spec-039 sentence (SPECS L2035) matches the wrong clause verbatim while
its "never substitute or inject" half is still current — the fix
(drop "or pop") aligns message with code exactly. Line attribution
confirmed: clause line byte-identical HEAD-vs-worktree (context line in
the hunt diff), enclosing first line hunt-dirtied
(`_safe_class_name`). Normal homing; closeout re-verify owed. My
pre-Findings W2-a is the same defect — merged into D1, no separate
entry.

**D2: ACCEPTED as a HEAD defect (Trust-boundary bar met, strengthened).**
Bare `.get()` in the FK attestation (HEAD L1926-1931) with no
`DoesNotExist` handling, running post-save pre-tail. No `except` wraps
`write_step` in the skeleton (body read whole at HEAD) — the raise
escapes as a top-level 500 and never reaches the tail's disappearing-row
`conflict` envelope. Contract row confirmed twice over: the tail comment
("a concurrent delete this transaction could not see" → `conflict` +
rollback) AND `validate_select_for_update`'s docstring, which promises
the opt-out surfaces races "as the in-band `conflict` envelope instead
of waiting on the lock" — D2 is exactly that promise broken at this
site. Supported opt-out confirmed (`mutations/sets.py:955`, shared
validator, bool-gated). Feasible shape confirmed (update + opt-out +
supplied single relation + concurrent delete in the save→attestation
window — the same race the tail already covers for save→re-fetch).
Model/form contrast confirmed (both return the saved object with no
post-save read). Lines clean (between hunt hunks `-1903` and `-1944`,
byte-identical). Normal homing; the fix design (skip-and-let-tail-
conflict vs map-here) belongs to the fixer. My pre-Findings W2-b is the
same defect — merged into D2, no separate entry.

**Cleared candidates: all 4 dispositions ACCEPTED.** Injected-verbatim
(the only honest key — no GraphQL name exists); `_relation_model_of`
None (unreachable — agreement mismatch fires first since None `is not`
the recorded model); import-time DRF key (settings fixed pre-import;
no test overrides the key — grep-verified); hostile hook values (no
contract row establishes the mode; the concurrent hunt owns that
population — correctly left, not filed, and correctly kept on-record).

**Window attribution: CONFIRMED.** `git diff 2759e0a1 --name-only`
names only `docs/dry/dry-0_0_15.md` (22-insertion Worker-0 dispatch
block). Target worktree delta (+129/-77, 39 hunks default-diff) sampled
across regions — all hostile-value-guard dirt, disjoint from every
finding's lines except the noted first-line touches whose clause lines
are byte-identical. Nothing else to attribute.

**No new defects (Worker 2).** My two pre-Findings candidates merged
into D1/D2 as the same defects; nothing further found. No `## Defects`
entry owed by me.

### Verdict: `revision-needed` (record-accuracy only)

All finding verdicts — 12 convergences, FAM-NEW, 22 file-locals, 21
rejections, D1/D2, the 4 cleared — are ACCEPTED. No re-trace is owed.
The revision corrects three auxiliary census numbers (each pinned by my
W2 probe, execution-verified below) so the permanent record transcribes
exactly:

- W2-C1 (Enumeration row 24): "(8 names)" → 7 names (HEAD L142-150).
- W2-C2 (C7): "7 package call sites: 2 build + 5 here" → 8 (3
  schema-side: `rf-inputs.py:458` + `rf-inputs.py:1500` +
  `rf-sets.py:431`, + 5 here at `:1082/:1299/:1426/:1657/:1755`).
- W2-C3 (FAM-NEW + H6): "Composed calls (4)" → 5 (add
  `describe_serializer_input`, `rf-inputs.py:938`).

Optional polish in the same pass (not required for `verified`): home
Enumeration rows 2/13 to R22 explicitly; add one C5 line noting the
`_or_default`-wrapper vs inner-helper hierarchy.

W2 probes: `docs/dry/temp-tests/dry-file-rest_framework__resolvers-w2/w2_recensus.py`
(`execution-verified`, `ruff check` + `ruff format` clean on exactly
that path, format last). W1's P1 re-executed green by me; W1's probe
path re-verified `ruff format --check` + `ruff check` clean. Item
touched paths re-check: artifact (.md, reference-style links only, all
10 link-definition headers present, `path::Symbol` citations, no
process-provenance violation, no banned mentions) + W1 probe (clean) +
my W2 probe (clean). HEAD `5ee86193` at W2 finish (unmoved); target
HEAD blob `8024703e`, worktree `c0b54039` (unchanged).

### Re-pass (Worker 2, fresh context)

Pass-1 W2 context is terminal, so this re-pass re-derives every check at
HEAD bytes (`git show HEAD:` reads + HEAD-pinned greps, static-decidable;
no probe created, no new scratch scope). All finding verdicts stood
ACCEPTED in pass 1 and are not re-litigated. Prior reasoning above is
untouched.

- **W2-C1: AGREE — row 24 reads "(7 names)", correct.** Independent
  recount of the errors import at HEAD L142-150:
  `FIELD_ERROR_CODE_INVALID`, `FIELD_ERROR_CODE_TRUNCATED`,
  `empty_validation_error`, `field_error`,
  `integrity_error_field_errors`, `join_error_path`,
  `validation_error_to_field_errors` — 7, one per line. Row 24 now
  reads "(7 names)". (The two remaining "(7 names)" cells are rows 29
  and 33, unrelated imports.)
- **W2-C2: AGREE — C7 reads 8 package call sites, correct.**
  `git grep -n "nested_serializer_child" HEAD` over
  `django_strawberry_framework` yields 12 hits: 1 def
  (`rest_framework/serializer_converter.py::nested_serializer_child`,
  L283) + 3 imports (`inputs.py:84`, `resolvers.py:185`,
  `sets.py:114`) + exactly 8 calls: `inputs.py:458`
  (fingerprint), `inputs.py:1500` (nested build), `sets.py:431`
  (inside `rest_framework/sets.py::_assert_schema_source_ownership`,
  def at L396 — schema-time ownership walk recursing into nested
  children, a genuine call), plus the 5 here at `:1082/:1299/:1426/`
  `:1657/:1755`. Split 3 schema-side + 5 here confirmed. Sweep for
  "7 package" / "2 build": zero remaining outside W2's quoted
  pass-1 correction (prior reasoning, stays).
- **W2-C3: AGREE — FAM-NEW reads 5 composed calls, correct.**
  `git grep -n "generated_input_type_name" HEAD` yields 1 def
  (`utils/inputs.py::generated_input_type_name`, L995) + 1 import +
  1 docstring mention + exactly 5 calls: `inputs.py:838`,
  `:938`, `:1105`, `:1692`, `utils/inputs.py:1041`
  (`name_set_input_type_name` spine). `inputs.py:938` read at HEAD
  bytes: inside `describe_serializer_input` (def L924), it calls the
  owner by name with `(shape.serializer_class.__name__,
  is_partial=..., is_full_shape=True, token="")` for the
  canonical-vs-descriptor diagnostic — a genuine composed call. No
  model/form direct calls (they route through the spine), so the
  population is closed at 5. FAM-NEW lists all five including the
  diagnostic; Challenges line reads "5 composed calls"; H6 names no
  composed-call number, so no edit was owed there. Sweep for
  "4 composed": zero remaining outside W2's quoted correction.
- **Polish: CONFIRMED present and accurate.** Rows 2/13 home to R22
  explicitly; C5 carries the wrapper-vs-inner note. Hierarchy
  re-verified at HEAD bytes:
  `utils/querysets.py::related_visibility_queryset_or_default`
  calls the inner helper and falls back to the default manager on
  None, while member 64 calls
  `utils/querysets.py::related_visibility_queryset` directly
  (L1447) and skips the AND on None (L1444-1446) — the wrapper tail
  is indeed the wrong contract for this surface.
- **Nothing-else-changed: CONFIRMED.** All finding headers present
  with verdicts matching the pass-1 accepted record (12
  convergences, FAM-NEW, 22 file-locals, 21 rejections, D1/D2 HEAD
  defects, 4 cleared); spot-checked counts unchanged (H6 → 2, C9
  12 sites, C6 2 per helper, R11 7 sites, H1–H14 table intact);
  D1/D2/Judgment text matches the accepted record. Deltas from the
  pass-1 record are exactly the three corrected numbers + the two
  polish items + `## Iterations` + the Status line.
- **Window attribution: CONFIRMED.** `git diff 2759e0a1 --name-only`
  names ONLY `docs/dry/dry-0_0_15.md` (43 insertions, purely
  additive Worker-0 dispatch/submission/verdict/resubmission
  accounting — the +9 since W1's resubmission note is the fresh
  re-pass dispatch paragraph, also Worker-0's). Artifact is
  untracked; pass 2 touched nothing tracked.
- **Touched-path checks:** both probe scopes re-verified clean
  (`uv run ruff format --check` → 2 files already formatted;
  `uv run ruff check` → all passed). Artifact prose: 10 link-group
  headers + LINK DEFINITIONS block present, `path::Symbol`
  citations, no banned mentions.
- **Fingerprints:** HEAD `5ee86193` at finish (unmoved since
  dispatch); target HEAD blob `8024703e`, worktree `c0b54039`
  (unchanged). No finding reopened.

Verdict: `verified`.

## Iterations

### Pass 2 (Worker 1 revision; record-accuracy only, no verdict changes)

Scope per the revision brief: correct W2-C1, W2-C2, W2-C3, each
re-derived by me against HEAD bytes (never copied from W2's numbers),
plus the two optional-polish items. No finding verdict, challenge
count, or rejection touched — all stand accepted. Prior reasoning
above (pass 1 + W2) is untouched; the in-place number fixes below are
errata. No `.py` probe was owed (every re-check is a `git show HEAD:`
read or a HEAD-pinned grep); no scratch created or modified.

- **W2-C1 (Enumeration row 24): AGREE — 7 names, corrected.**
  Independent recount at HEAD bytes
  (`git show HEAD:django_strawberry_framework/rest_framework/resolvers.py`,
  L142-150): `FIELD_ERROR_CODE_INVALID`,
  `FIELD_ERROR_CODE_TRUNCATED`, `empty_validation_error`,
  `field_error`, `integrity_error_field_errors`, `join_error_path`,
  `validation_error_to_field_errors` — 7, one per line, no
  continuation. Row 24 now reads "(7 names)". (My pass-1 "8" was a
  transcription slip; the P1 census counted import STATEMENTS, and
  the per-name hand count was never re-checked until W2.)
- **W2-C2 (C7 nested opt-in recursion census): AGREE — 8 calls,
  corrected.** Independent re-derive at HEAD bytes via
  `git grep -n "nested_serializer_child" HEAD --
  django_strawberry_framework` plus per-file `git show HEAD:`
  contexts: owner def
  `django_strawberry_framework/rest_framework/serializer_converter.py::nested_serializer_child`
  (1, not a call site) + imports (3, not call sites) + calls at
  `rest_framework/inputs.py:458`
  (`_fingerprint_nested` opt-in fingerprint),
  `rest_framework/inputs.py:1500`
  (`_resolve_nested_field` nested build),
  `rest_framework/sets.py:431` (the schema-time
  `_assert_schema_source_ownership` class-creation ownership walk —
  docstring "One recursive walker for the class-creation ownership
  check", recursing at L442 — the site my pass-1 census missed),
  and the 5 here at `:1082` (`_assert_runtime_write_source_ownership`),
  `:1299` (`_assert_nested_agreement`), `:1426`
  (`_scope_specs_over_serializer`), `:1657`
  (`_instrument_intent_specs`), `:1755` (`_assert_intent_specs`),
  each confirmed a call (not def/import/comment) in its shown
  context. Total 8 = 3 schema-side (inputs x2 + sets x1) + 5 here.
  C7 now reads "(8 package call sites: 3 schema-side + 5 here,
  census)". No other text repeated the old total (verified by grep
  for "7 package" / "2 build": zero remaining outside W2's
  quoted correction, which is prior reasoning and stays).
- **W2-C3 (FAM-NEW + H6 composed calls): AGREE — 5, corrected.**
  Independent re-derive at HEAD bytes via
  `git grep -n "generated_input_type_name" HEAD --
  django_strawberry_framework`: owner def
  `django_strawberry_framework/utils/inputs.py::generated_input_type_name`
  (L995) + 1 import + 1 docstring mention + exactly 5 calls:
  `rest_framework/inputs.py:838` (`resolve_injected_field_specs`
  injected-specs provisional), `:938`
  (`describe_serializer_input` — verified at HEAD bytes L924-943:
  it calls the owner by name with
  `(shape.serializer_class.__name__, is_partial=...,
  is_full_shape=True, token="")` to recompute the canonical name
  for its "canonical vs descriptor-derived" diagnostic note, then
  compares `name == canonical_name` — a genuine composed call my
  pass-1 census missed), `:1105`
  (`serializer_input_type_name` return), `:1692`
  (`build_serializer_input_class` walk provisional), and
  `utils/inputs.py:1041` (`name_set_input_type_name` spine).
  Model/form namers route through the spine (no direct calls), so
  the population is closed at 5. FAM-NEW "Sites + roles" now reads
  "Composed calls (5)" with the `describe_serializer_input`
  diagnostic listed, and the FAM-NEW Challenges line now reads "5
  composed calls". (The H6 table row itself names no composed-call
  number — "build call sites follow the namer" — so no edit was
  owed there; verified by grep for "4 composed": zero remaining
  outside W2's quoted correction.)
- **Optional polish (taken, both items).** (1) Enumeration rows 2
  (`from __future__`) and 13 (`typing.Any`) now home to R22
  explicitly ("unreferenceable; census-exempt" /
  "annotation use; P3-referenced"), closing the backstop
  literally; no homing meaning changed. (2) C5 carries one new
  line noting the `_or_default`-wrapper vs inner-helper
  hierarchy — verified by me at HEAD bytes, not copied:
  `django_strawberry_framework/utils/querysets.py::related_visibility_queryset_or_default`
  (L4211) calls the inner
  `::related_visibility_queryset` (L4182) and falls back to the
  default manager on None, while member 64 calls the inner helper
  directly (L1447) and on None skips the AND (L1444-1446 comment:
  "no visibility contract to AND on - the pin + lock still
  apply") — so the wrapper's default-manager tail is indeed the
  wrong contract for this surface.
- **Window attribution vs
  `ITEM_BASELINE=2759e0a1b12260101af978450531cc62bc2c79c1`.**
  `git diff <baseline> --name-only` names ONLY
  `docs/dry/dry-0_0_15.md` (34 insertions, purely additive,
  inspected: Worker-0's dispatch/submission/verdict accounting
  block for this item — not mine, I never edit the plan). The
  artifact is untracked (`??`, zero `git ls-files` hits), so my
  pass-2 edits touch nothing tracked. Target fingerprints
  unchanged: HEAD blob `8024703e`, worktree `c0b54039`.
- **HEAD at finish:** `5ee86193` (`git rev-parse HEAD`
  immediately before this section) — unmoved since dispatch and
  since W2's finish. No fingerprint change; no finding reopened.
- **Scratch:** untouched. W1 scope
  (`docs/dry/temp-tests/dry-file-rest_framework__resolvers/`)
  and W2 scope (`...-w2/`) both exist on disk from prior passes;
  this pass created, modified, and deleted nothing in either
  (read-only `git show` / `git grep` probes only, no workspace
  copy — no source-mutating proof was owed).

Status set to `ready-for-verification/2` for return to the same
Worker 2.

### Pass 3 — index-row appendix (mechanical, no judgments)

Mechanical derivation only: no verdict, count, challenge, rejection, or defect touched.
Family = kebab-cased finding title (underscores/slashes to hyphens, leading
underscores stripped, code punctuation dropped); Owner = the finding's stated
member symbol(s) in the finding's own order (`+`-joined; module-level where
the finding names no member: R22 import block, J14 hook posture, J19 gap
probe); Files covered = the files where the rule's sides live per the
verified text (all R rows target-only — no R finding establishes a second
site; J vs-side files via the artifact's stated flavor/file links);
Holding item = File `rest_framework/resolvers.py`; Status = file-local (R)
/ rejected (J). Fresh-J parentheticals and CONVERGE targets copied verbatim
from the J headers. Three J file lists omit an unstated vs-side file rather
than invent it: J10 (`materialize_relation_id_container`), J14 (model
`check_permission`), J20 (instance accessor) — each named once in the
artifact with no file. No gap notes owed beyond those three omissions.

| `serializer-relation-decode-coloring` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_multi` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `nested-decode-recursion` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_nested` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `hook-data-views-freeze-upload-metadata-tables` | `django_strawberry_framework/rest_framework/resolvers.py::_upload_metadata` + `django_strawberry_framework/rest_framework/resolvers.py::_IMMUTABLE_LEAF_TYPES` + `django_strawberry_framework/rest_framework/resolvers.py::_FROZEN_VIEW_CONTAINERS` + `django_strawberry_framework/rest_framework/resolvers.py::_frozen_hook_view` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `injection-exact-match` | `django_strawberry_framework/rest_framework/resolvers.py::_injected_serializer_data` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `constructor-kwarg-reserved-merge` | `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `schema-runtime-agreement` | `django_strawberry_framework/rest_framework/resolvers.py::_relation_model_of` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_schema_runtime_agreement` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_relation_agreement` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_nested_agreement` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `runtime-write-source-ownership-recursion` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_runtime_write_source_ownership` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `relation-queryset-and-scope-discipline` | `django_strawberry_framework/rest_framework/resolvers.py::_scope_relation_querysets_to_visibility` + `django_strawberry_framework/rest_framework/resolvers.py::_scope_specs_over_serializer` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `validator-queryset-pinning` | `django_strawberry_framework/rest_framework/resolvers.py::_pin_validator_querysets` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `save-kwarg-guards` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_save_kwargs_no_shadow` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_save_kwargs_not_model_fields` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `write-surface-spec-list` | `django_strawberry_framework/rest_framework/resolvers.py::_write_surface_specs` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `relation-intent-ledger-snapshot-compare` | `django_strawberry_framework/rest_framework/resolvers.py::_RelationIntentLedger` + `django_strawberry_framework/rest_framework/resolvers.py::_relation_object_identity` + `django_strawberry_framework/rest_framework/resolvers.py::_relation_intent_snapshot` + `django_strawberry_framework/rest_framework/resolvers.py::_relation_identity_intact` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `relation-intent-instrumentation` | `django_strawberry_framework/rest_framework/resolvers.py::_instrument_relation_intent` + `django_strawberry_framework/rest_framework/resolvers.py::_instrument_intent_specs` + `django_strawberry_framework/rest_framework/resolvers.py::_record_field_intent` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `relation-intent-walk-attestation-manifest` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_relation_intent` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_intent_specs` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `m2m-snapshot-attestable-census` | `django_strawberry_framework/rest_framework/resolvers.py::_m2m_membership_snapshot` + `django_strawberry_framework/rest_framework/resolvers.py::_attestable_m2m_fields` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `post-save-relation-attestation` | `django_strawberry_framework/rest_framework/resolvers.py::_attest_saved_relations` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `signal-write-witness` | `django_strawberry_framework/rest_framework/resolvers.py::_write_witness` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `saved-result-validation` | `django_strawberry_framework/rest_framework/resolvers.py::_checked_saved_result` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `write-step-guarded-body` | `django_strawberry_framework/rest_framework/resolvers.py::_serializer_write_step` + `django_strawberry_framework/rest_framework/resolvers.py::_guarded_serializer_write` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `decode-step` | `django_strawberry_framework/rest_framework/resolvers.py::_serializer_decode_step` | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `module-scalar-contracts-docstring-projection` | `django_strawberry_framework/rest_framework/resolvers.py::_OMITTED` + `django_strawberry_framework/rest_framework/resolvers.py::_DRF_NON_FIELD_KEY` (+ module docstring) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `import-reference-totality` | `django_strawberry_framework/rest_framework/resolvers.py` (import block, members 2–33) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | file-local |
| `nested-structure-walk-unification` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_runtime_write_source_ownership` + `django_strawberry_framework/rest_framework/resolvers.py::_scope_specs_over_serializer` + `django_strawberry_framework/rest_framework/resolvers.py::_instrument_intent_specs` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_intent_specs` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_nested_agreement` + `django_strawberry_framework/rest_framework/resolvers.py::_build_reverse_map` + `django_strawberry_framework/rest_framework/resolvers.py::_pin_validator_querysets` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `none-arm-unification` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_multi` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_nested` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `cycle-walker-unification` | `django_strawberry_framework/rest_framework/resolvers.py::serializer_errors_to_field_errors` + `django_strawberry_framework/rest_framework/resolvers.py::_frozen_hook_view` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `context-gate-vs-hook-mapping` | `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs` + `django_strawberry_framework/rest_framework/resolvers.py::_hook_mapping` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `shadow-guard-vs-model-field-guard-split` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_save_kwargs_no_shadow` + `django_strawberry_framework/rest_framework/resolvers.py::_assert_save_kwargs_not_model_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `build-reverse-map-vs-mutation-input-reverse-map` | `django_strawberry_framework/rest_framework/resolvers.py::_build_reverse_map` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/mutations/inputs.py` | File `rest_framework/resolvers.py` | rejected |
| `drf-vs-django-code-readers` | `django_strawberry_framework/rest_framework/resolvers.py::_error_detail_codes` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/utils/errors.py` | File `rest_framework/resolvers.py` | rejected |
| `saved-alias-check-vs-router-re-check` | `django_strawberry_framework/rest_framework/resolvers.py::_checked_saved_result` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/mutations/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `pk-drift-early-enforcement-vs-skeleton-backstop` | `django_strawberry_framework/rest_framework/resolvers.py::_checked_saved_result` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/mutations/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `nested-container-error-vs-relation-id-container-error` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_nested` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `operation-discrimination-shapes` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` + `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/resolvers.py` | rejected |
| `annotation-recompute-vs-build-produce` | `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/resolvers.py` | rejected |
| `serializer-vs-form-decode-mirror` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_multi` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_serializer_data` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object` (rejection recorded here; CONVERGE with forms R1 + skeleton distinct on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `frozen-hook-record-vs-live-instance-hooks` | `django_strawberry_framework/rest_framework/resolvers.py` (rejection recorded here; CONVERGE with hook_context R5 on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `partial-update-mechanisms` | `django_strawberry_framework/rest_framework/resolvers.py::_merged_serializer_kwargs` (rejection recorded here; CONVERGE with forms J1 on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/mutations/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `batched-vs-per-element-multi-decode` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_multi` (rejection recorded here; CONVERGE with forms J2 on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `null-m2m-none-policies` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_single` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_relation_multi` + `django_strawberry_framework/rest_framework/resolvers.py::_decode_nested` (rejection recorded here; CONVERGE with forms J3 + envelope distinct on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py`, `django_strawberry_framework/mutations/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `file-routing-data-vs-files` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object` (rejection recorded here; CONVERGE with forms R2/axis-4 on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/resolvers.py` | File `rest_framework/resolvers.py` | rejected |
| `excluded-unreachability` | `django_strawberry_framework/rest_framework/resolvers.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/utils/write_values.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/resolvers.py` | rejected |
| `relation-model-of-vs-taxonomy-reads` | `django_strawberry_framework/rest_framework/resolvers.py::_relation_model_of` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/utils/relations.py` | File `rest_framework/resolvers.py` | rejected |
| `three-branch-save-mapper-vs-save-or-field-errors` | `django_strawberry_framework/rest_framework/resolvers.py::_guarded_serializer_write` (rejection recorded here; CONVERGE with the forms-artifact note on fresh evidence) | `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/mutations/resolvers.py` | File `rest_framework/resolvers.py` | rejected |

### Pass-3 confirmation (Worker 2, fresh context)

Light confirmation only: no verdict, count, challenge, rejection, or defect
re-litigated. Checked the pass-3 appendix (43 pipe rows) against the
artifact's `## Findings` headers + stated owners/sites/postures and the
plan's `## Responsibility index` format. Prior reasoning untouched.

- **Count + order: PASS.** Exactly 43 rows: 22 file-local (R order) then
  21 rejected (J order), each in finding order. Every family name is the
  mechanical kebab-case of its finding title (leading underscores
  stripped, `/` and `=` punctuation dropped); no concept renames.
- **File-local rows: PASS.** Each R row's owner symbol(s) are exactly the
  members its finding states (R1: 37–40; R3: 49/51/52/53; R6: 56/57/59/60/61;
  R12: 68–71; R21: sentinel + bucket key + docstring; R22: import block;
  all others single/pair members as stated). All owner defs spot-confirmed
  at HEAD bytes (`git show HEAD:` — 39 defs + `_RelationIntentLedger` +
  module constants, none invented). All files-covered target-only, inside
  each finding's Sites (no R finding establishes a second site). Holding
  item + `file-local` status correct on all 22.
- **Rejection rows: PASS.** All 14 fresh-J parentheticals read
  `(rejection recorded here; fresh pair, no prior verdict)` with no
  converge target — matching the `(REJECTED, fresh)` headers. All 7
  converge targets verified verbatim against their J headers: J13 `forms
  R1 + skeleton distinct`, J14 `hook_context R5`, J15 `forms J1`, J16
  `forms J2`, J17 `forms J3 + envelope distinct`, J18 `forms R2/axis-4`,
  J21 `the forms-artifact note` (each + `on fresh evidence`, the plan's
  standing tail). Files-covered inside each finding's named files; the
  three disclosed vs-side omissions (J10/J14/J20) name symbols the
  artifact states without a file. `rejected` status correct on all 21.
- **Format: PASS.** 5-column pipe rows, backticked family/owner/files,
  `File \`rest_framework/resolvers.py\`` holding form, `path::Symbol`
  owners (module-level form only where the finding names no member:
  R22, J14, J19 — matching plan convention). No provenance words in rows.
- **Window: PASS.** `git diff 2759e0a1 --name-only` names ONLY
  `docs/dry/dry-0_0_15.md`; artifact untracked — pass 3 touched nothing
  tracked. HEAD `5ee86193` at finish, unmoved.
- **Nothing-else-changed: PASS.** All finding headers + verdict words
  match the pass-1 accepted record (C1–C12, FAM-NEW, R1–R22, J1–J21,
  D1/D2, 4 cleared, judgment); W2-C1/C2/C3 corrections + polish present.
  Delta is the appendix + pass-3 record + Status line only.

Verdict: `verified`. No probe created; no scratch scope.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[bdfam]: dry-rule-one-sync-boundary.md
[envfam]: dry-rule-mutation-error-envelope.md
[skelfam]: dry-rule-shared-write-skeleton.md

<!-- docs/SPECS/ -->
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[errors]: ../../django_strawberry_framework/utils/errors.py
[fresolvers]: ../../django_strawberry_framework/forms/resolvers.py
[hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[mresolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[sresolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[wtx]: ../../django_strawberry_framework/utils/write_transaction.py
[wvalues]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-mresolvers]: ../../tests/mutations/test_resolvers.py
[test-rfresolvers]: ../../tests/rest_framework/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
