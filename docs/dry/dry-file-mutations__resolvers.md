# DRY review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a family owned HERE (F1/F2, proposed for the index),
a reused consumer row re-derived fresh (F3--F10, never inherited), a
file-local record with its proving challenge (R1--R8), or a recorded
rejection with contract difference + trigger + durable home (J1--J5).
Zero production edits; zero tracked files changed.

## System trace

Target (`django_strawberry_framework/mutations/resolvers.py`, 1339 lines,
blob `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`; absent from the
item-scoped diff vs both the tasked `ITEM_BASELINE=0f030cd2...` and
`HEAD`, target CLEAN): the model-flavor write runtime and the owner of
the two cross-flavor write contracts (spec-036 Decision 8 origin,
spec-039 shared entries). It DEFINES the shared write skeleton
(`run_write_pipeline_sync`: one `transaction.atomic()` boundary +
locate preamble + authorize-before-decode ordering + payload tail,
with `decode_step` / `write_step` / `tail_step` the only per-flavor
seams), the shared entry factory (`make_resolver_entries`: the
`UNSET`-normalizing `resolve_sync` + the single-`sync_to_async`
`resolve_async` pair), the shared async delegate
(`run_pipeline_async`), the shared save mapper
(`save_or_field_errors`, ridden by the form flavor too), the model
decode/write riders (`_run_pipeline_sync`, `_model_decode_step`,
`_model_write_step` incl. the spec-040 D6 `EXCLUDED` 3/4-tuple
contract), the delete rider (`_run_delete`, `_delete_write_step`,
`_delete_or_field_errors`), the locate + lookup seams
(`locate_instance`, `coerce_lookup_id`), the exclude carve-out
(`_provided_attr_names`, `_unprovided_exclude`,
`_unique_constraint_groups`), the refetch + payload seams
(`refetch_optimized`, `build_payload`, `payload_cls_for`,
`error_payload_builder`), and the auth seam (`authorize_or_raise`).
It CONSUMES (by name, P3-proved 57/57 imports referenced, zero
upstream definitions here) the operation vocabulary in
[operations] (`operation_takes_id`, one locate-gate site), the
recourse template in [querysets] (`sync_pipeline_recourse`, one noun),
the boundary primitive in [querysets] (`run_in_one_sync_boundary`,
one-line delegate), the decode spine in [write-values]
(`decode_provided_fields`, `decode_scalar_leaf`,
`decode_visible_relation_ids`, `decoded_into`, `relation_into`),
the envelope leaves in [errors] (`field_error`,
`null_field_error`, `integrity_error_field_errors`,
`validation_error_to_field_errors`) + [write-tx] (`conflict_error`
et al.), the phase/alias machinery in [write-tx], the GlobalID
primitive in [relay] (`decode_model_global_id`), the payload slot in
[mutations-inputs] (`payload_object_slot`, `FieldError`, `EXCLUDED`),
and the auth-result contract in [mutations-permissions]
(`_require_sync_bool_auth_result`). It is CONSUMED by the form
flavor in [forms-resolvers] (skeleton + factory + `save_or_field_errors`,
P2-verified), the serializer flavor in [rf-resolvers] (skeleton +
factory, AST-verified), the register flavor in [auth-mutations]
(skeleton + `_model_write_step` repack, hand-rolled entries), and the
field dispatcher in [mutations-fields] (the `resolve_sync` /
`resolve_async` seams by name; dispatch lines untouched by the
in-flight guard-trio hunk, verified 0 hits in the diff).

Connected code read for judgment, outside the item: the form twin
([forms-resolvers] regions + its verified artifact as trigger only),
the serializer mirror ([rf-resolvers] rider/factory/recourse/save
regions via grep + AST), the register rider ([auth-mutations]
`_run_register_pipeline_sync` + `_synthesize_register_rider` +
`_register_write_step` regions), the owners ([querysets]
`sync_pipeline_recourse` + `run_in_one_sync_boundary` +
`related_visibility_queryset_or_default` + `model_for` +
`initial_queryset` + `apply_type_visibility_sync` regions,
[write-values] / [errors] / [relay] / [mutations-inputs] leaf
regions, [write-tx] phase regions), the build side
([mutations-fields] dispatch + protocol-probe regions,
[mutations-permissions] contract region), oracles in
[test-mutations-resolvers] (40-test inventory + gate + delete-ride
regions); contract sources spec-036 Decision 7/8/10/15 + spec-038 +
spec-039 via the module docstring's cited Decisions (clauses verified
member-by-member against the bodies).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P5,
all read-only, all green; commands under `### Challenges`). The
three write-resolver flavors were read FIRST, before any judgment.

1. **Cross-flavor policy mirroring.** Searched, all three resolvers
traced FIRST. P2 proves the sharing shape by behavior, not tokens:
one `make_resolver_entries(` call-site per flavor module (model
here, form, serializer; auth 0 — hand-rolled, J2), four step-pairs
riding one `run_write_pipeline_sync` (model `_run_pipeline_sync`
+ delete seam, form `_run_form_pipeline_sync`, serializer
`_run_serializer_pipeline_sync`, register
`_run_register_pipeline_sync`), three recourse constants from one
template with distinct nouns. Decode split: single + multi here
both ride the batched `decode_visible_relation_ids` compose; form
rides the per-element spine (object need, J-adjacent); serializer
rides both. Save mapping: model + form ride `save_or_field_errors`
(forms 5 hits incl. 2 call sites; rf 1 hit, comment-only —
serializer owns `_do_save`, disjoint DRF contract, no merge
posited). What SHOULD be shared already is: skeleton, entries,
boundary, recourse sentence, batched compose, scalar leaf,
handler factories, flat mappers, write phase. Verdict: F1/F2 owned
here; F3--F10 consumer edges; J1/J2 rejections.
2. **Sync/async twins.** Compared by behavior, not shape.
Instrument (P1): 30 sync defs, exactly 1 `AsyncFunctionDef`
(`run_pipeline_async`), 2 `await` nodes. The async surface is not
a twin body: `resolve_mutation_async` is the factory's entry
running the SAME `_run_pipeline_sync` through `run_pipeline_async`
(one `await run_in_one_sync_boundary(...)` line, read first-hand),
which is itself a one-line delegate of the open `one-sync-boundary`
primitive (F6). The register flavor duplicates only the entry
shape with a narrower arity (J2), not the pipeline. No twinship,
no finding beyond F2/F6.
3. **Derived rather than repeated knowledge.** Searched. AST
census: zero code-level `queryset` / `objects` / `get_field` /
`default_manager` attribute reads (the 3 text hits are docstring
prose). `related_model` is threaded as a kwonly parameter at both
relation decoders (never re-derived); specs arrive bind-stashed
(`mutation_cls._input_field_specs` x1 read, zero `InputFieldSpec(`
constructions); `model_for` / `initial_queryset` composed by name
(F9). The recourse is computed from the template (P2/P4
equality-proved), never re-spelled. No fact re-derived.
4. **Inverse / round-trip pairs.** Searched, both directions
verified. Wire GlobalID -> pk decodes server-side through the one
`decode_model_global_id` primitive here (`coerce_lookup_id` for
the top-level `id:`, `decode_visible_relation_ids` for relation
ids — F8); no second decoder. Payload construction
(`build_payload` / `payload_cls_for` + `payload_object_slot`,
F10) pairs with the field signature the factory synthesizes in
[mutations-fields] (dispatch lines verified untouched by its
hunk). One grammar per pair, correctly separated halves.
5. **Contracts restated in another medium.** Counted 1 definition
per rule; everything else classified: module docstring
(projection, all load-bearing clauses verified against bodies:
skeleton order, one boundary, recourse single-source, locate
visibility, auth seam, `full_clean` envelope, pk-without-visibility
refetch, misuse discipline); spec-036/038/039 Decisions
(contract sources, cited by the docstring); [test-mutations-resolvers]
rows (40 tests: factory gate, delete skeleton-ride monkeypatch,
exclude carve-out, envelope rows — oracles spell literals, none
iterates an owner table); live `test_products_api.py` /
`test_mutation_atomicity.py` rows (shipped verdicts). No medium
holds an independently maintained copy.
6. **Enforcement by omission.** Operation family enumerated
(create/update/delete) against every branch: create + update share
`_run_pipeline_sync` (no locate for create via `operation_takes_id`
gate), delete rides `_run_delete` (no-op decode, snapshot tail);
every error path returns through `error_payload_builder`
(rollback uniform: locate/decode/write/conflict arms all
pin `set_rollback` before the envelope — read all five). The
`EXCLUDED` 4-tuple without a flavor write step raises loudly at
the strict unpack (guard, not gap). No member lacks a guard a
contract source requires — no defect filed.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-mutations__resolvers/p1_ast_census.py`),
count **57**. Every member lands below; F = family row (ownership
or consumer edge re-derived fresh, never inherited), R = file-local
finding, J = recorded rejection.

| # | Member | Kind | Home |
|---|---|---|---|
| 0 | module docstring | projection | verified clause-by-clause vs bodies |
| 1--23 | 23 imports (`__future__`..`permissions`) | machinery/consumer imports | consumer (exempt; P3: 57/57 referenced) |
| 24 | `_MUTATION_ASYNC_RECOURSE` | recourse constant | F4 (consumer) |
| 25 | `run_write_pipeline_sync` | skeleton | F1 (OWNER here) |
| 26 | `error_payload_builder` | envelope closure | R8 |
| 27 | `_decode_relations` | model decode rider | R1 |
| 28 | `_explicit_null_error` | null guard | R1 |
| 29 | `_make_aware_if_naive` | tz coercion | R1 |
| 30 | `_decode_single_relation_id` | FK/O2O decoder | R1 (+ F5/F8 transit) |
| 31 | `_decode_relation_id_list` | M2M decoder | R1 (+ F5/F8 transit) |
| 32 | `_relation_null_error` | M2M null constructor | R1 (+ F7 composer) |
| 33 | `locate_instance` | visibility locate | R7 |
| 34 | `_provided_attr_names` | FK-reversal for exclude | R2 |
| 35 | `_unprovided_exclude` | exclude carve-out | R2 |
| 36 | `_unique_constraint_groups` | uniqueness groups | R2 |
| 37 | `_assign_m2m` | post-save M2M set | R4-member (model tail) |
| 38 | `refetch_optimized` | pk re-fetch + plan | R8 |
| 39 | `build_payload` | envelope constructor | R8 (+ F7/F10 composer) |
| 40 | `_run_pipeline_sync` | model dispatch | F1 (rider) |
| 41 | `_model_decode_step` | model decode step | R3 |
| 42 | `_model_write_step` | model write step | R3 (shared leaf: register repacks) |
| 43 | `forced_save_or_field_errors` | forced-update mapper | R6 |
| 44 | `_run_delete` | delete dispatch | F1 (rider) |
| 45 | `_delete_write_step` | snapshot-then-delete | R4 |
| 46 | `_delete_or_field_errors` | delete refusal mapper | R4 |
| 47 | `authorize_or_raise` | auth seam | R5 |
| 48 | `_full_clean_or_field_errors` | validation mapper | R6 |
| 49 | `save_or_field_errors` | shared save mapper | R6 (shared leaf: form rides) |
| 50 | `coerce_lookup_id` | id decode + check | R7 (+ F8 composer) |
| 51 | `not_found_error` | not-found constructor | R7 (+ F7 composer) |
| 52 | `_invalid_lookup_id_error` | invalid-id constructor | R7 (+ F7 composer) |
| 53 | `payload_cls_for` | payload class read | R8 (+ F10 composer) |
| 54 | `run_pipeline_async` | async delegate | F6 (consumer, one-line) |
| 55 | `make_resolver_entries` | entry factory | F2 (OWNER here) |
| 56 | `resolve_mutation_sync/async` assign | model entries | F2 (factory product) |

No member unassigned. Dual-homing of 30--32/39/42/50--53 is
consumer-edge composition (upstream leaf called by name), not a
second definition. Prior-cycle trigger notes re-checked fresh,
never inherited: the forms item's F3 (skeleton/entries/boundary
split — re-derived here as F1/F2/F6 with the register fourth
rider strengthening F1); the operations item's R3/R5/R8 (seam
mirror re-derived from this side as J3; dispatch/backstop
re-derived as F1 riders; pipeline-vs-vocabulary split confirmed:
zero resolver/transaction/async machinery in [operations]);
the utils-querysets index rows (F4/F5/F6/F9 re-derived via
P2--P4, never assumed).

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, not counted. Executed
probes are read-only files under
`docs/dry/temp-tests/dry-file-mutations__resolvers/` run with
`uv run python` from the repo root; NO shared-tree pytest, NO
source mutation (so no workspace copy was owed), NO database
opened by any probe (P4 configures empty `DATABASES`; P2's stub
body never reaches the pipeline).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | reorder the pipeline (decode-before-authorize) | **1** (F1 skeleton here; 4 riders follow) | all rider tests + live write rows |
| C2 | add a fifth write flavor (new step pair) | **1** branch (new rider here or in its module); 0 skeleton | factory product iff UNSET-shaped (else J2) |
| C3 | change `UNSET` normalization | **1** (F2 factory here; 3 products follow; register stays — J2) | factory gate |
| C4 | reword the misuse recourse sentence | **0 here** (template owner); noun **1 here** | wording oracles |
| C5 | add an id-taking operation | **0 here** (descriptors owner); gate read **1 here** (`needs_locate` follows) | locate oracles |
| C6 | change the relation visibility query | **0 here** (chain owner); decoders here follow | visibility oracles |
| C7 | count `blank=True` as nullable at decode | **1** (R1 scalar + single + multi arms move together) | null-envelope oracles |
| C8 | new uniqueness mechanism (constraint kind) | **1** (R2 groups + carve-out) | exclude oracles |
| C9 | second value-carrying excluded kind | **1** (R3 pack + guard; register repack follows) | register oracles |
| C10 | unify the three partial-update mechanisms | **refused** (J1: disjoint validation substrates) | -- |
| C11 | route register through the factory | **refused** (J2: narrower arity, `del id`) | -- |
| C12 | unify the `!= "form"` call gate with `operation_takes_id` | **refused** (J3: call vs signature gates) | -- |

Probe commands + what each proved (every probe `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-mutations__resolvers/p1_ast_census.py`
-- 57 members, 30 sync defs, 1 async def (`run_pipeline_async`),
2 awaits (matrix axis 2 instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-mutations__resolvers/p2_flavor_mirror.py`
-- one factory call-site per flavor module (model/form/serializer),
0 in auth; four step-pairs ride the skeleton; three recourse nouns
template-composed; entry `__name__` pins; factory freshness; `UNSET`
normalization through a stub body (no DB). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-mutations__resolvers/p3_delegation.py`
-- 57/57 non-future imports referenced; nine upstream machines
have zero definitions here; owner bodies (`run_write_pipeline_sync`,
`make_resolver_entries`, `run_pipeline_async`) live HERE.
`execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-mutations__resolvers/p4_behavior.py`
-- explicit-null guard arms, M2M-null clear-signal message, both
lookup error shapes, naive→aware coercion (+ aware/date
passthrough), recourse equality — empty `DATABASES`.
`execution-verified`, no database.
- `uv run python docs/dry/temp-tests/dry-file-mutations__resolvers/p5_gates.py`
-- `test_write_flavors_share_resolver_entry_factory` exists and
pins all three `__name__ == "resolve_sync"`. `execution-verified`.
- AST census (inline): zero code-level `queryset` / `objects` /
`get_field` / `default_manager` reads (3 text hits are docstring
prose); `related_model` kwonly-parameter-only at both relation
decoders; zero `InputFieldSpec(` constructions.
`execution-verified`.

## Findings

### F1 -- `shared-write-skeleton` (OWNER HERE, index: open)

- **Contract + variation.** One skeleton owns the
`transaction.atomic()` boundary + locate preamble +
authorize-before-decode ordering + payload tail; each flavor
supplies only decode/write steps (and delete its tail seam).
Varies per flavor middle (C1 counts 1 for order, C2 counts
1-branch/0-skeleton for a new flavor).
- **Sites + roles.** Owner: [mutations-resolvers]
`::run_write_pipeline_sync` (member 25; body verified HERE,
P3). Riders (each verified first-hand, P2): model
`::_run_pipeline_sync` + `::_run_delete` (members 40/44),
[forms-resolvers]`::_run_form_pipeline_sync`,
[rf-resolvers]`::_run_serializer_pipeline_sync`,
[auth-mutations]`::_run_register_pipeline_sync` (fourth rider,
strengthens the family past the three the forms item knew).
Shared leaves inside the family: `::save_or_field_errors`
(member 49; form `ModelForm`/`plain` write steps call it —
forms 5 hits incl. 2 call sites; serializer comment-only,
owns `_do_save`) and `::_model_write_step` (member 42;
register repacks `(user, m2m_assignments, exclude)` into it).
Sub-rules for Worker 0: skeleton (this row) + entry factory
(F2); the async delegate stays a consumer edge of the open
`one-sync-boundary` family (F6), not a third row — the
forms-item W2 ruling, re-derived (one-line delegate, no
second boundary).
- **Challenges.** C1 counts 1; C2 counts 1-branch/0-skeleton.
- **Owner + lifetime.** This module (principle 7: the model
pipeline is the origin; all three later flavors + register
import from it, never the reverse — dependency direction
wins). Nothing stored (closures per call).
- **Migration.** None (already composed by name; file item
owes no edit).
- **Distinct behavior.** The `_primary_type is None`
plain-form branch lives in the form rider (not here); the
delete snapshot tail lives in member 44/45; the register
`EXCLUDED` repack lives at the rider — all recorded at their
sites.
- **Behavioral proof.** P2 (rider shape) + P5-adjacent
`test_delete_pipeline_rides_shared_write_skeleton`
(monkeypatch replaces the skeleton; fails a bypass)
`execution-verified` probes + `static-reviewed` pipeline
oracles (exclude, envelope, atomicity live rows).
- **Structural gate.** The delete skeleton-ride oracle fails
a locate/auth/atomicity re-implementation (it asserts the
skeleton symbol was ridden with a snapshot tail); the
factory-sharing gate (F2) pins the entries. Negative
control: a behavior-preserving hand copy of the skeleton
passes every behavior oracle (the copy is correct) but fails
the ride test (it patches the owner symbol) — so the gate
guards bypass, not behavior.
- **Coupling.** None introduced.
- **Freshness.** Target `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`;
[forms-resolvers] `4edb984b299b4e2a71492e73382558b01865f48a`;
[rf-resolvers] `8024703ec0fb09758daeec0585e0065de1c61fc3`;
[auth-mutations] `dbe64995b87240b87a1d5119f46cc42c7cab646f`;
[test-mutations-resolvers]
`4aa8e51e8af08697b702f47be8425c36b3c8c485`;
HEAD `9031cb3d`.

### F2 -- `shared-write-entry-factory` (OWNER HERE, index: open row under the skeleton family item)

- **Contract + variation.** One factory owns the
`UNSET`-default kwarg normalization + the single-`sync_to_async`
async boundary per write flavor. Varies on arity (C3 counts 1;
register's narrower arity stays out — J2).
- **Sites + roles.** Owner: [mutations-resolvers]
`::make_resolver_entries` (member 55; body HERE, P3) +
`::run_pipeline_async` (member 54, the boundary the factory's
`resolve_async` awaits — 2 `await` nodes total, P1). Products
(P2): model `resolve_mutation_sync/async` (member 56), form
`resolve_form_sync/async`, serializer
`resolve_serializer_sync/async` — one call-site each, each
producing FRESH functions (P2 freshness-proved, so per-flavor
identity stays distinct). Consumer of the seam: [mutations-fields]
dispatches `mutation_cls.resolve_sync/async` by name (dispatch
lines verified untouched by its in-flight hunk: 0 diff hits).
Intentional separation: the register rider hand-writes its pair
(J2), not a product.
- **Challenges.** C3 counts 1.
- **Owner + lifetime.** This module (same principle-7 ground as
F1; the factory closes over the skeleton's boundary). Nothing
stored (fresh closures per call).
- **Migration.** None.
- **Distinct behavior.** Factory vs skeleton stay separate rows:
a `UNSET`-normalization change moves only the factory; a
pipeline-order change moves only the skeleton (distinct change
axes, precedent: sealed-authorization-source slot/head twin
rows). Register hand entries recorded at
[auth-mutations]`::_synthesize_register_rider` + J2.
- **Behavioral proof.** P2 (`execution-verified`) + P5 gate
witness (`execution-verified`); `static-reviewed` pipeline
oracles.
- **Structural gate.**
`test_write_flavors_share_resolver_entry_factory` fails an
entry-shape drift on any of the three flavors (pins all three
`__name__`s — the [DRY][dry]-cited name-assertion shape, which
is why it is a gate and not a consolidation: every behavior
oracle passes a hand copy). Negative control: same as F1's —
a hand-written pair with identical behavior passes behavior
oracles, fails the `__name__` pin on rename.
- **Coupling.** None.
- **Freshness.** Target as in F1; [mutations-fields] worktree
`64410c86…` vs HEAD `cf518361…` (guard-trio hunk; dispatch
lines verified 0 diff hits — claims hold on both bytes).

### F3 -- `mutation-operation-descriptors` (consumer, index: open)

Single consumer site HERE: `operation_takes_id(meta.operation)`
at the skeleton's `needs_locate` gate (member 25 body, 1 hit;
`operation_takes_data` 0 hits — signature shaping lives in
[mutations-fields]). The descriptors owner ([operations], blob
`16223c6b…`) is untouched by any concurrent hunk. No index
change proposed (row already covers this file). Challenges C5
counts 0-here. Proof: P3 (`execution-verified`).

### F4 -- `sync-boundary-recourse-wording` (consumer, index: rejected)

Member 24 is the single call
`sync_pipeline_recourse("DjangoMutation")` (P2 exact arg; P4
output equality-proved); siblings `_FORM_ASYNC_RECOURSE` /
`_SERIALIZER_ASYNC_RECOURSE` same shape. The index marks this
family `rejected` (per-flavor named constant stays; sentence
single-sourced) — this file already matches that outcome. No
change, no index change. Challenge C4 counts 0-here/1-noun.
Proof: P2 + P4 (`execution-verified`).

### F5 -- `related-object-visibility-recheck` (transitive consumer, index: open)

Every relation id resolves through the related primary's
visibility `get_queryset` two hops down: members 30/31 call
[write-values]`::decode_visible_relation_ids`, which opens with
the owner chain (`related_visibility_queryset_or_default`).
Zero visibility definitions here (P3). Hidden == missing is the
SAME field-keyed `FieldError` (module docstring Decision-10
clauses verified vs bodies). Challenge C6 counts 0-here.
**Index proposal for Worker 0:** append
`django_strawberry_framework/mutations/resolvers.py` (transitive
consumer) to this row's files-covered — the only consumer-row
file list missing this file. Proof: P2/P3 (`execution-verified`).

### F6 -- `one-sync-boundary` (consumer edge, index: open)

Member 54 is a one-line delegate:
`return await run_in_one_sync_boundary(sync_body, ...)` (read
first-hand; docstring names the model + form delegates —
serializer rides the identical line through the factory, a
prose compression released as cosmetic, see `## Defects`).
No second boundary, no per-step hops (P1: 2 awaits total).
Row already covers this file; no index change. Proof: P1
(`execution-verified`).

### F7 -- `mutation-error-envelope` (consumer, index: open)

`FieldError` owned at [mutations-inputs], code vocabulary at
[errors]; this file composes both: members 32/51/52 construct
leaves via `field_error` / `null_field_error` (P4 shape-proved:
field + codes), members 42/43/45/46/48/49 map
`ValidationError` / `IntegrityError` / `ProtectedError` /
`RestrictedError` / zero-row writes through the single-sourced
mappers. Zero envelope-type definitions here. Row already
covers this file; no index change. Proof: P4
(`execution-verified`).

### F8 -- `typed-globalid-decode` (consumer, index: open)

[relay]`::decode_model_global_id` (+ `GlobalIDDecode` statuses)
composed at two sites: member 50 maps
`DECODE_FAILED`/`WRONG_MODEL` -> invalid-id, `UNCOERCIBLE_PK` ->
not-found (status mapping read first-hand); members 30/31 inherit
the same contract through `decode_visible_relation_ids`. Zero
decode definitions here (P3). Row already covers this file; no
index change. Proof: P3/P4 (`execution-verified`).

### F9 -- `queryset-seed-and-model-read` (consumer, index: open)

`model_for(` x5 (skeleton target read, locate, delete guard,
coerce) + `initial_queryset(` x3 (locate seed, refetch seed)
composed by name; zero seeds re-derived (axis-3 census).
Row already covers this file; no index change. Proof: P3
(`execution-verified`).

### F10 -- `mutation-payload-name` (consumer, index: open)

`payload_object_slot(` x4 (skeleton slot, refetch slot) +
`_payload_type_name` x2 via member 53 (`getattr(inputs, ...)`
so field lazy-ref and resolver instantiate one object —
docstring verified vs body). The pending fields.py
consolidation does not touch these lines. Row already covers
this file; no index change. Proof: P3 (`execution-verified`).

### R1 -- Model relation decode + scalar null/tz coloring (file-local)

- **Contract + variation.** Members 27--32: bind-stashed specs
route each provided attr by kind (SCALAR/FILE ->
`scalar_and_fk_attrs`, RELATION_SINGLE/MULTI to their dests,
EXCLUDED aside); `None` on a `null=False` column/relation is a
field-keyed null `FieldError` before any DB work; naive
datetimes coerce under `USE_TZ`; M2M `null` rejects with the
clear-signal message (`[]` clears). Varies on the null
contract (C7 counts 1: scalar + single + multi arms move
together; the shared `null_field_error` leaf itself counts 0).
- **Sites + roles.** Definition here (arms + dest policy).
Spine/mapper/leaf owners upstream (all called by name, P3).
Oracles: null-envelope + decode rows in
[test-mutations-resolvers].
- **Challenges.** C7 counts 1.
- **Owner + lifetime.** This file (the model-decode home;
per-call dicts, nothing stored).
- **Distinct behavior.** Model replace-set `null`-reject vs
form empty-clear (a bound `ModelForm` follows Django form
semantics — the forms-item J3 divergence, confirmed from this
side: `_relation_null_error` exists only here).
- **Behavioral proof.** P4 (`execution-verified`, empty
`DATABASES`) + `static-reviewed` oracles.
- **Structural gate.** The null-envelope oracles fail a guard
drop (a `None` slipping to `save()` surfaces as the generic
`"__all__"` constraint envelope the oracles do not pin).
- **Freshness.** Target as in F1; [write-values]
`d28587c7…`; [errors] `3e25e93b…`.

### R2 -- Exclude carve-out (file-local)

Members 34--36: `_provided_attr_names` reverses `<field>_id`
attrs through the bind-time Django-field index (never a
suffix strip — the `object_id` case documented in the body),
`_unprovided_exclude` carves the `full_clean(exclude=...)` set
minus co-constrained members, `_unique_constraint_groups`
reads `Meta.constraints` + `unique_together` + `field.unique`.
Challenge C8 counts 1. Owner: this file (per-call sets).
Proof: `static-reviewed` exclude oracles
(`test_unprovided_exclude_*`). Freshness: target as in F1.

### R3 -- Model decode/write steps + `EXCLUDED` contract (file-local)

Members 41/42: construct-or-`setattr` + provided-set fold-in
of excluded values, then `full_clean` -> save ->
M2M-identical tail; the 4-tuple (any `EXCLUDED` spec) vs
3-tuple shape with a STRICT unpack — a bind introducing an
excluded value without a flavor write step raises here instead
of silently discarding it. Consumer: the register rider
repacks into `::_model_write_step` ([auth-mutations] region
read). Challenge C9 counts 1-here (pack + guard move
together). Owner: this file. Proof: `static-reviewed`
register + model oracles. Freshness: target + [auth-mutations]
as in F1.

### R4 -- Delete rider (file-local)

Members 44--46 (+ 37): no-op decode, snapshot-then-delete
write (optimizer-planned re-fetch `force_load=True` BEFORE the
row is deleted; deletion runs against the LOCATED instance so
the snapshot keeps `pk`/`id`), snapshot tail (no post-write
refetch — the row is gone), `PROTECT`/`RESTRICT` ->
envelope, zero-target-row -> `conflict`. Challenge: change the
delete refusal mapping — 1. Owner: this file. Proof: the
skeleton-ride oracle + protected-delete envelope oracles
(`static-reviewed`). Freshness: target as in F1.

### R5 -- Authorization seam (file-local)

Member 47: `check_permission` False -> top-level `GraphQLError`
(D15 surface, distinct from the field envelope); coroutine
returns closed + raised via the shared
`_require_sync_bool_auth_result` ([mutations-permissions]
contract, 1 call here); model-less target-name fallback.
Challenge: new auth-result shape — 1 here (decision) / 0
(contract owner). Owner: this file (the seam); contract
upstream. Proof: `static-reviewed` perm-denied rows (package
+ live). Freshness: target + [mutations-permissions]
`54f770ae…`.

### R6 -- Validation/save mappers (file-local)

Members 43/48/49: `_full_clean_or_field_errors` (constraint
duplicates caught pre-`save`, multi-field -> `"__all__"`),
`save_or_field_errors` (zero-arg callable so ONE race catch
serves model + both form flavors — F1 shared leaf),
`forced_save_or_field_errors` (update `force_update=True` +
savepoint-contained zero-row disambiguation). Challenge: change
a race mapping — 1 (all riders follow). Owner: this file.
Proof: `static-reviewed` race/conflict oracles. Freshness:
target + [write-tx] `eca9ad4d…` as in F1.

### R7 -- Locate + lookup-id decode (file-local)

Members 33/50--52: `coerce_lookup_id` (GlobalID decode +
type-check + pk-coercion against the target model, `using`
threaded explicitly), `locate_instance` (visibility
`get_queryset` + base-manager `SELECT ... FOR UPDATE`
constrained by the visibility pk subquery, `pin_write_queryset`
alias fail-closed), `not_found_error` /
`_invalid_lookup_id_error` constructors. Challenge: new id
status — 1 (map + constructors). Owner: this file.
Proof: `static-reviewed` hidden-vs-missing + wrong-model rows.
Freshness: target + [relay] `c3c5aea5…` as in F1.

### R8 -- Error closure + refetch + payload (file-local)

Members 26/38/39/53: `error_payload_builder`
(`set_rollback` BEFORE every envelope build — the no-effect
invariant, uniform over all five error returns),
`refetch_optimized` (by pk WITHOUT visibility + G2 plan via
`mutation_payload_child_selections(slot)` + write-alias pin),
`build_payload` (uniform slot), `payload_cls_for` (one
`getattr` for all flavors). Challenge: tail-shape change — 1.
Owner: this file. Proof: `static-reviewed` atomicity live
rows (`test_mutation_atomicity.py`) + payload rows. Freshness:
target + [write-tx] + [mutations-inputs] `fc442047…`.

### J1 -- Partial-mechanism unification (rejection, considered fresh)

Model `full_clean(exclude=...)` carve-out (R2) vs form
bound-data reconstruction vs serializer `partial=True`. REJECTED
from this side too: disjoint validation substrates — a new
kind of partial here cannot serve a bound form (declared fields
all validate) or a serializer (DRF owns `partial`). Trigger: a
validation substrate supporting two partial shapes at once.
Home: member 35's docstring + this clause.

### J2 -- Register through the entry factory (rejection, considered fresh)

Routing [auth-mutations]`::_synthesize_register_rider` through
`make_resolver_entries`. REJECTED: the register body arity is
`(cls, info, data)` — create-only, no `id` param — so its
hand entries `del id` where the factory threads it through;
forcing the factory would need a mode flag (principle 5: no
branch no real path reaches — the third product never drops
`id`). The async half already shares the primitive
(`run_in_one_sync_boundary` direct — same one boundary, F6).
Trigger: register gaining an id-taking operation. Home: F2 +
the rider's docstring (already states "fourth STEP PAIR, not a
fourth plumbing kit").

### J3 -- Call gate vs signature predicate (rejection, re-derived fresh)

[mutations-fields] `!= "form"` call gate (resolver-CALL
gate: every model op passes `id=`, create as `UNSET`) vs
`operation_takes_id("create") == False` (SIGNATURE + locate
gates: create exposes no `id:`, skeleton does no locate) —
create is inline-True/predicate-False BY DESIGN (verified on
both bytes: the hunk's 5 seam mentions are the protocol probe,
dispatch lines 0 diff hits). Gating the call on the predicate
would `TypeError` every create. Trigger: a flavor whose seam
shape diverges from `operation != "form"`. Home:
[mutations-fields] guard rows + family item (the operations
item's R3, confirmed from this side).

### J4 -- Converter-table unification (checked non-membership)

This file holds NO converter table (P3-adjacent census: zero
`SCALAR` / registry / `CONVERT` definitions) and computes no
column kinds — `FILE` / `RELATION_*` tokens arrive on the
bind-stashed specs via [utils-inputs] (`ee31d360…`). The plan's
`converter-table-per-surface-ownership` row needs no fifth
file. No index change proposed.

### J5 -- Seal-family membership (checked non-membership)

This file does NOT join `sealed-execution-queryset`: zero
`_seal_or_defect` / `base_queryset` / `model_for`-as-seed
definitions or seal calls (P3 counts: `base_queryset(` 0;
`model_for(` 5 + `initial_queryset(` 3 are F9 seed reads, not
seal writes). Alias-pinned execution is composed via
[write-tx] (`open_write_pipeline`, `pin_write_queryset`,
`pipeline_alias_guard`, `require_write_pipeline`) + the
visibility applier (`apply_type_visibility_sync`) — called,
never re-implemented. No index change proposed.

## Defects

None. One investigated edge released without a defect:

1. `run_pipeline_async`'s docstring names the model + form
delegates but not the serializer ("the shared async boundary
both the model ... and form ... entries delegate to"), though
all three factory products await it. Incomplete, not false —
the factory body + P2 prove the third ride; projection
wording, no behavior. Cosmetic, not filed (same release
precedent as the forms-item header compression).

Nothing routed to any owner.

## Pending execution

None. All five probes already ran green against the shared
tree; each is read-only (AST/text census + pure calls with
stub fields + short-circuit arms; no source mutation, no
database — P4 configures empty `DATABASES`). No pytest was run
in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items.
`FAKESHOP_SHARDED=1` and Postgres cells are `inapplicable by
construction`: the probes reach no database, alias, or dialect
decision (P4 proves it by running with no database
configured).

## Judgment

Backstop discharged: 57/57 `ast.Module.body` members
enumerated, 12 challenges run (C1--C12, every variation axis
of every rule), six matrix axes discharged against the real
surface (all three write resolvers + the register rider traced
FIRST; sharing proved by behavior counts, not tokens;
round-trips verified in both directions; sync/async single-body
shape verified by instrument, not assumed), two families owned
here with precise 4-rider / 3-product definitions (F1/F2),
eight consumer rows re-derived fresh (F3--F10, one proposing a
files-covered append), eight file-local records with proving
challenges (R1--R8), five rejections with difference + trigger
+ home (J1--J3 considered fresh, J4/J5 non-memberships). Zero
defects, zero pending. The target owns its rules singly: one
skeleton, one entry factory, one model decode/write pair, one
delete rider, one locate, one carve-out, one auth seam, one
mapper set, one refetch/payload tail. Zero-edit result is
legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
0f030cd261c80423fee7f020fdf4798b2e84d902 --
django_strawberry_framework/mutations/resolvers.py` is empty
(tasked baseline) and `git diff HEAD -- <same>` is empty
(working blob `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`
equals `HEAD:` — target CLEAN, so no hunk attribution was
owed; live `git stash create` at run time was `fb9c8af4...`
— the tree kept moving under concurrent sessions, but this
file is in neither delta). The artifact itself is this new
file (`docs/dry/dry-file-mutations__resolvers.md`, untracked
until Worker 0 records it). The `## Owned changes` ledger
paths (`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched. Concurrent dirt (the
`connection.py`, `extensions/resource_policy.py`,
`filters/inputs.py`, `filters/sets.py`, `forms/inputs.py`,
`mutations/fields.py`, `mutations/sets.py` hunks, staged
`tests/utils/test_querysets.py` +31,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`,
the utils/querysets duplicate-trace collision) was never
edited, reverted, or tidied — verified by content-diff scoping
(the fields.py hunk's seam mentions checked first-hand:
dispatch lines 0 diff hits, so F2's claims hold on both
bytes). Scratch (untracked, kept for Worker 2 re-run):
`docs/dry/temp-tests/dry-file-mutations__resolvers/p1_ast_census.py`,
`p2_flavor_mirror.py`, `p3_delegation.py`, `p4_behavior.py`,
`p5_gates.py` — all read-only, all green. No `ruff` run owed
(no tracked edits). No pytest run (not authorized by the entry
command). Do not commit.

## Independent verification (Worker 2)

Method note: the five probes were re-run green from this session
(P1--P5 outputs reproduced below), and every count below was
re-derived with fresh `ast`/grep instruments, not copied from
`## Findings`. Reconciliation against W1 follows the trace.

### Own trace (expectation-first)

Read order per role: target (all 1339 lines), the four rider
modules FIRST ([forms-resolvers], [rf-resolvers],
[auth-mutations], [mutations-fields] dispatch), the owners
([querysets], [write-values], [errors], [relay],
[mutations-inputs], [write-tx], [mutations-permissions],
[operations]), oracles ([test-mutations-resolvers], 40 `def
test_` rows), then `## Findings`.

- **Skeleton + 4 riders.** `run_write_pipeline_sync` body lives
  HERE (one `transaction.atomic()` via `open_write_pipeline`,
  locate preamble, authorize-before-decode, payload tail).
  Riders verified first-hand: model `::_run_pipeline_sync` +
  `::_run_delete` (this file), [forms-resolvers]
  `::_run_form_pipeline_sync` (3 skeleton mentions),
  [rf-resolvers] `::_run_serializer_pipeline_sync` (2
  mentions), [auth-mutations] `::_run_register_pipeline_sync`
  (3 mentions, repacks `(user, m2m_assignments, exclude)` into
  `resolvers._model_write_step` at line 1145). Posited change
  "reorder pipeline (decode-before-authorize)": count **1**
  (skeleton here; 4 riders follow). Owner I would choose: this
  module (origin; all riders import inward, dependency
  direction wins). Matches F1.
- **Entry factory + 3 products + register hand-roll.**
  `make_resolver_entries` body HERE; call-sites re-counted:
  model 2 (factory def + `make_resolver_entries(
  _run_pipeline_sync)` product line), form 1, serializer 1,
  auth 0. Register hand-writes its pair at
  [auth-mutations] lines 1253/1265 (`del id`, create-only
  `(cls, info, data)` arity) and already shares the one
  boundary via `run_in_one_sync_boundary` direct (6 hits in
  auth). Posited change "change `UNSET` normalization":
  count **1** (factory; 3 products follow; register stays).
  Owner: this module. Matches F2 + J2.
- **Descriptors locate-gate.** `operation_takes_id(` x2 here
  (import + `needs_locate` gate); `operation_takes_data` 0
  (signature shaping in [mutations-fields], line 291 uses
  `operation_takes_id`). Posited "add an id-taking
  operation": count **0 here** (descriptors owner). Consumer
  row. Matches F3.
- **Recourse noun.** `sync_pipeline_recourse(` x3 here
  (import + `_MUTATION_ASYNC_RECOURSE =
  sync_pipeline_recourse("DjangoMutation")` + docstring
  mention); P2/P4 equality re-proved by re-run. Posited
  "reword the sentence": **0 here**, noun **1 here**.
  Matches F4 (index `rejected`; this file already matches).
- **Visibility, transitive.** Members 30/31 call
  `decode_visible_relation_ids` (5 hits here) which calls
  `visible_related_objects` ([write-values] imports it from
  `.querysets`), which opens with
  `related_visibility_queryset_or_default` ([querysets]
  line 4017; `visible_related_objects` body confirms the
  "single-sited in `related_visibility_queryset_or_default`"
  comment). Two-hop transitive consumer; zero visibility
  definitions here (0 hits for the owner symbol). Posited
  "change the relation visibility query": **0 here**.
  Matches F5. Ruling on the append proposal: APPROVE (see
  `## Judgment` below; exact plan row at the end).
- **Boundary delegate.** `run_pipeline_async` is the single
  `AsyncFunctionDef` (P1 re-run: 30 sync defs, 1 async, 2
  awaits) with the one-line body `return await
  run_in_one_sync_boundary(...)` (read first-hand, line
  1288). Posited "second boundary": none exists. Consumer
  edge of open `one-sync-boundary`. Matches F6.
- **Envelope / decode / seed / payload consumers.**
  `field_error` x29 / `null_field_error` x3 composed (zero
  envelope-type definitions); `decode_provided_fields` /
  `decode_scalar_leaf` / `decoded_into` / `relation_into`
  composed (arms live here); `model_for(` x5 +
  `initial_queryset(` x3 composed by name (zero
  `queryset`/`objects`/`get_field`/`default_manager`
  attribute reads — fresh `ast.Attribute` census: all 0);
  `payload_object_slot(` x5 + `getattr(inputs, ...)` one-shot
  read (member 53). Counts **0 here** on every owner-side
  change. Matches F7/F8/F9/F10.
- **Relation coloring (R1).** Members 27--32: bind-stashed
  spec kinds route SCALAR/FILE/SINGLE/MULTI/EXCLUDED; the
  single `SCALAR` text hit is docstring line 383 (prose, not
  a definition); `related_model` appears only as kwonly
  parameters (lines 495/536) + pass-through kwargs
  (523/558) — never re-derived. Posited "count
  `blank=True` as nullable": **1** (scalar + single + multi
  arms move together). File-local here. Matches R1.
- **Exclude carve-out (R2).** Members 34--36 as claimed;
  `_provided_attr_names` reverses via the bind-time index
  (`model_fields[attr].name`), no suffix strip. Posited
  "new uniqueness mechanism": **1**. Matches R2.
- **`EXCLUDED` contract (R3).** Strict 3-tuple unpack at
  member 42 (`target, m2m_assignments, exclude = decoded`);
  register repacks (auth line 1145). Posited "second
  value-carrying excluded kind": **1** (pack + guard).
  Matches R3.
- **Delete rider (R4).** Members 44--46 + 37; snapshot via
  `refetch_optimized(force_load=True)` BEFORE
  `pipeline_write_phase` delete against the LOCATED
  instance. Posited "change delete refusal mapping":
  **1**. Matches R4.
- **Auth seam (R5).** Member 47: `False` -> raised
  `GraphQLError`; coroutine closed via
  `_require_sync_bool_auth_result` (1 call). Posited "new
  auth-result shape": **1 here** (decision) / 0 (contract).
  Matches R5.
- **Validation/save mappers (R6).** Members 43/48/49;
  `save_or_field_errors` ridden by form (forms 2 call
  sites at lines 509/540, verified); serializer owns
  `_do_save` (rf line 2303, disjoint DRF contract — no
  merge posited). Posited "change a race mapping":
  **1**. Matches R6.
- **Locate + lookup (R7).** Members 33/50--52; status map
  `DECODE_FAILED`/`WRONG_MODEL` -> invalid-id,
  `UNCOERCIBLE_PK` -> not-found read first-hand (lines
  1226--1230). Posited "new id status": **1**. Matches R7.
- **Envelope / refetch (R8).** Members 26/38/39/53;
  `set_rollback` before every envelope return (closure
  body, lines 361--365); refetch by pk WITHOUT visibility
  (line 761). Posited "tail-shape change": **1**.
  Matches R8.

Reconciliation: every owner I would choose equals W1's
(F1/F2 here; F3--F10 upstream owners; R1--R8 here). One
wording compression noted (W1 F5 "opens with the owner
chain": strictly the chain is
resolvers -> `decode_visible_relation_ids` ->
`visible_related_objects` -> owner; two hops, verified
above) — substance identical, transitive-consumer routing
stands. No other difference.

### Enumeration (member-by-member vs own count)

Own instrument: `ast.parse` of the target, `len(tree.body)`
= **57** (matches W1). Kind census, own dump:

- 0: module docstring (projection).
- 1--23: 23 imports (`__future__`, `datetime`, `typing`,
  `strawberry`, `django.conf`, `django.core.exceptions`,
  `django.db`, `django.db.models`, `django.utils`,
  `graphql`, `exceptions`, `optimizer.extension`, `relay`,
  `resource_policy`, `utils.errors`, `utils.inputs`,
  `utils.permissions`, `utils.querysets`,
  `utils.write_transaction`, `utils.write_values`,
  `inputs`, `operations`, `permissions`) — consumer
  machinery, exempt; P3 re-run: 57/57 non-future imports
  referenced.
- 24: `_MUTATION_ASYNC_RECOURSE` -> F4.
- 25: `run_write_pipeline_sync` -> F1 owner.
- 26--53: `error_payload_builder` (R8) through
  `payload_cls_for` (R8) in W1's table order — each name
  verified present in own dump in the same order (26
  `error_payload_builder`, 27 `_decode_relations`, 28
  `_explicit_null_error`, 29 `_make_aware_if_naive`, 30
  `_decode_single_relation_id`, 31
  `_decode_relation_id_list`, 32 `_relation_null_error`,
  33 `locate_instance`, 34 `_provided_attr_names`, 35
  `_unprovided_exclude`, 36 `_unique_constraint_groups`,
  37 `_assign_m2m`, 38 `refetch_optimized`, 39
  `build_payload`, 40 `_run_pipeline_sync`, 41
  `_model_decode_step`, 42 `_model_write_step`, 43
  `forced_save_or_field_errors`, 44 `_run_delete`, 45
  `_delete_write_step`, 46 `_delete_or_field_errors`, 47
  `authorize_or_raise`, 48 `_full_clean_or_field_errors`,
  49 `save_or_field_errors`, 50 `coerce_lookup_id`, 51
  `not_found_error`, 52 `_invalid_lookup_id_error`, 53
  `payload_cls_for`).
- 54: `run_pipeline_async` (sole `AsyncFunctionDef`) ->
  F6.
- 55: `make_resolver_entries` -> F2 owner.
- 56: `resolve_mutation_sync/async` tuple assign -> F2
  product.

57/57 land in W1's homes; no member unassigned, no extra
member. Dual-homing of 30--32/39/42/50--53 is consumer-edge
composition (upstream leaf called by name), not a second
definition — agreed.

### Matrix (vs real surface)

1. Cross-flavor: DISCHARGED. All three resolver flavors +
   register read FIRST by both workers (my greps above:
   factory call-sites 2/1/1/0; riders 4/3/2/3). Sharing
   proved by behavior counts, not tokens. Agree F1/F2
   owned here, F3--F10 consumer edges, J1/J2.
2. Sync/async: DISCHARGED. P1 re-run: 30 sync defs,
   `run_pipeline_async` only async def, 2 awaits; the
   async entry runs the SAME sync body through one
   `sync_to_async` boundary (line 1288 read first-hand).
   No twinship beyond F2/F6. Agree.
3. Derived knowledge: DISCHARGED. Fresh `ast.Attribute`
   census: `queryset`/`objects`/`get_field`/
   `default_manager` all 0; `related_model` kwonly-only;
   zero `InputFieldSpec(` constructions. Agree.
4. Round-trip: DISCHARGED. GlobalID->pk one primitive
   (`decode_model_global_id` x4: import + coerce + 2
   relation decoders via compose); payload pair
   (`build_payload`/`payload_cls_for` +
   `payload_object_slot`) vs [mutations-fields]
   signature synthesis. Agree.
5. Contracts in other media: DISCHARGED. 1 definition per
   rule; docstring = projection (load-bearing clauses
   spot-verified vs bodies: boundary, ordering, recourse
   single-source, visibility locate, auth seam,
   `full_clean` envelope, pk-without-visibility refetch);
   40-test oracle file spells literals (factory gate pins
   `__name__` thrice, never iterates an owner table);
   live atomicity/payload rows are shipped verdicts. No
   oracle rewritten (zero tracked edits — diff empty,
   confirmed below). Agree.
6. Omission: DISCHARGED. create/update share member 40
   (no locate for create via `operation_takes_id` gate,
   line 207); delete rides member 44 (no-op decode,
   snapshot tail); all five error returns pin
   `set_rollback` before the envelope (closure body);
   `EXCLUDED` 4-tuple without a flavor write step raises
   at the strict unpack (guard, not gap). No defect.
   Agree.

### Challenges + roles + equivalence

C1--C12 counts re-derived above; all agree with W1
(C1 1, C2 1-branch/0-skeleton, C3 1, C4 0-here/1-noun,
C5 0-here, C6 0-here, C7 1, C8 1, C9 1-here,
C10--C12 refused). Roles: F3--F10 are consumer edges
(definitions upstream, each verified 0-definitions-here
via P3 + censuses); R1--R8 definitions here; J4/J5 are
checked non-memberships (no converter table: sole
`SCALAR` hit is docstring prose line 383; no seal
membership: 0 `_seal_or_defect`/`base_queryset(` hits).
No oracle reads from the owner it checks (oracles spell
literals; zero edits made). Principle 8: zero production
edits, so observable behavior is unchanged by
construction; the behavior claims W1 relies on (rider
shape, recourse equality, null-guard arms, lookup error
shapes, tz coercion, `__name__` pins) were re-executed
via P1--P5 re-runs (all green, read-only, no database —
P4 configures empty `DATABASES`).

### Zero-edit + diff + routing

`git diff 0f030cd261c80423fee7f020fdf4798b2e84d902 --
django_strawberry_framework/mutations/resolvers.py` is
empty (exit 0, no output — confirmed this session);
working blob `3fd1e57199b6366a8bc0b1661518e8bc8949ece4`
equals `HEAD:` blob (target CLEAN). Coverage: 57/57
assigned; assignment validated above. Routing: F1/F2 are
owned HERE and already hold open index rows under Family
`shared-write-skeleton` (plan lines 448--449) — no new
row owed. F5 proposes appending this file to the open
`related-object-visibility-recheck` files-covered: the
row (plan line 296) lists `utils/querysets.py`,
`types/resolvers.py`, `utils/write_values.py`,
`rest_framework/resolvers.py`, `forms/resolvers.py` but
not this file, while this file composes the chain at
members 30/31 through the shared batched compose
(verified two-hop chain above). RULING: APPROVE the
append — the transitive-consumer claim is proved, and
without the append the backstop undercounts the family
population by one real consumer.

### Rejections J1--J5

- J1 (partial-mechanism unification): difference =
  disjoint validation substrates (model
  `full_clean(exclude=...)` vs bound-form reconstruction
  vs DRF `partial=True`); trigger = a substrate
  supporting two partial shapes at once. Carries both.
  Agree.
- J2 (register through factory): difference = narrower
  arity (`(cls, info, data)`, `del id` at auth lines
  1253/1265, verified first-hand); trigger = register
  gaining an id-taking operation. Carries both. Agree.
- J3 (call gate vs signature predicate): difference =
  resolver-CALL gate (`operation != "form"` at
  [mutations-fields] line 330, verified) vs SIGNATURE +
  locate gates (`operation_takes_id`); trigger = a flavor
  whose seam shape diverges from `operation != "form"`.
  Dispatch lines verified untouched by the in-flight
  fields.py hunk (hunks at `@@ -57`, `-103`, `-132`,
  `-251`; dispatch/seam lines 330/338/339 outside all
  hunks). Carries both. Agree.
- J4 (converter-table non-membership): no table, no kind
  computation here (census above). No index change.
  Agree.
- J5 (seal-family non-membership): no seal calls; the 5
  `model_for(` + 3 `initial_queryset(` hits are F9 seed
  reads, not seal writes. No index change. Agree.

Freshness re-hashed this session: target `3fd1e571…`
(matches W1 + HEAD); [forms-resolvers] `4edb984b…`,
[rf-resolvers] `8024703e…`, [auth-mutations]
`dbe64995…`, [test-mutations-resolvers] `4aa8e51e…`
(all match W1); owners [write-values] `d28587c7…`,
[errors] `3e25e93b…`, [relay] `c3c5aea5…`,
[mutations-inputs] `fc442047…`, [write-tx]
`eca9ad4d…`, [mutations-permissions] `54f770ae…`,
[operations] `16223c6b…`, [utils-inputs] `ee31d360…`
(all match W1). [mutations-fields] worktree `64410c86…`
vs HEAD `cf518361…` (guard-trio hunk; F2's claims hold
on both bytes per hunk-scope check above). The
post-ff `utils/querysets.py` move (`5907a1f7…` ->
`1539b66c…`) touches no fingerprinted site of this
artifact (no querysets blob is recorded here; F4--F6/F9
rest on P1--P4 re-proofs, re-run green). Nothing stale.

Gates + negative controls (both re-read in full):
`test_write_flavors_share_resolver_entry_factory` pins
all three `__name__ == "resolve_sync"` (P5 re-run
green); a behavior-identical hand copy passes behavior
oracles but fails the pin on rename — guards bypass,
not behavior. Agreed.
`test_delete_pipeline_rides_shared_write_skeleton`
monkeypatches the OWNER symbol
`mutation_resolvers.run_write_pipeline_sync`; a
hand-copied skeleton elsewhere is never ridden — fails
the ride. Agreed. `## Pending execution`: none; all
probes already ran green read-only with no database, so
no `execution-deferred` items; `FAKESHOP_SHARDED=1` /
Postgres `inapplicable by construction` (no probe
reaches a database/alias/dialect decision) — agreed.
Coupling: none introduced — agreed.

### AGENTS.md prose check

Artifact citations use `path::Symbol` (link-definition
block carries the 10 canonical group headers); no raw
`path:NN` citations (permitted in dry scratchpad
artifacts regardless); no process provenance in any
production surface (zero production edits); no test-tier
violation (no new tests owed for a zero-edit file item;
relied-on oracles sit at the mandated tiers:
`tests/mutations/test_resolvers.py` package tier + live
query rows). No `ruff` run owed (no `.py` edits; this
section appends to an untracked `.md` artifact only).
No violation — no `revision-needed` on prose grounds.

## Defects (Worker 2)

None. The one cosmetic edge W1 released (member 54's
docstring naming the model + form async delegates but
not the serializer, though P2 proves all three factory
products await it) was re-verified first-hand
(docstring lines 1276--1287; serializer product line at
[rf-resolvers] 2430--2431). Incomplete, not false;
projection wording, no behavior. Concurrence with
release (not filed), same precedent W1 cites. No new
defect found in this session.

## Judgment (Worker 2)

`Status: verified`. Zero-edit result legitimate:
57/57 members enumerated against an independently
re-derived count of 57, six matrix axes discharged
against the real surface (four riders traced FIRST),
C1--C12 counts reconciled 12/12, F1/F2 ownership HERE
confirmed with the exact 4-rider / 3-product shape,
F3--F10 consumer edges re-derived (F5 transitive chain
proved two hops: this file -> `decode_visible_relation_ids`
-> `visible_related_objects` ->
`related_visibility_queryset_or_default`), J1--J5 carry
difference + trigger, all freshness fingerprints
re-hash clean, both gates fail their negative controls,
no pending execution, no coupling, AGENTS.md prose
clean. Plan rows Worker 0 should write: (1) tick File
`mutations/resolvers.py` verified (Run 0.0.15
2026-09-18-1; zero edits; no pending execution);
(2) append
`django_strawberry_framework/mutations/resolvers.py`
(transitive consumer) to the
`related-object-visibility-recheck` responsibility-index
files-covered. Concurrent dirt listed in W1's
Implementation section was never touched (this session
edited only this artifact's `Status:` line plus this
section). Do not commit.

## Iterations

### Scoped re-trace (run 7, pass stale7-1) — drift `5ee86193..0c0537e2`

Charter: the prior record (Run 0.0.15 2026-09-18-1, accepted under the
2026-09-22 ruling) is evidence about `5ee86193` bytes only. This pass
adjudicates the target drift
`git diff 5ee86193..0c0537e2 -- django_strawberry_framework/mutations/resolvers.py`
(35+/15-, two commits: `ed004ebd` the arm + `e6a33c46` the docstring
first line) against the recorded claims. Findings no drift hunk touches
STAND without re-review. File item: zero production edits.

Attribution: target worktree blob `c9cff059…` vs HEAD `043a2d0b…` is
HUNT dirt (the `truth.*` name/render migration + the
`_build_wire_name_map` / `field_name_map` threading), in neither the
`## Owned changes` ledger nor the cycle baseline; per the dispatch brief
it is concurrent work — HEAD bytes traced throughout, nothing tracked
touched. The HUNT hunks and the drift hunks verified disjoint by content
(no overlapping line ranges; the drift arm at HEAD lines 1240-1244 is
identical in the worktree). `ITEM_BASELINE=7546610e…` resolves; the
item-scoped diff is this artifact only (untracked).

Target fingerprints: `5ee86193` =
`3fd1e57199b6366a8bc0b1661518e8bc8949ece4` (== recorded); HEAD =
`043a2d0bb2f68104b19a7f679abd2b267774ecdf`; worktree =
`c9cff0590157de85bd9374ab85588b00e62080e0`. HEAD file is 1359 lines
(recorded 1339 at `5ee86193`).

Drift-hunk inventory (all three in the one target file):

- H1 — module docstring: first-line reword + the locate-clause rewrite
  (HEAD lines 1, 30-35): a Relay-Node primary takes a GlobalID, a
  non-Relay primary takes the raw pk.
- H2 — imports: new member
  `from ..types.relay import implements_relay_node` (HEAD line 88) +
  `coerce_relation_pk_or_none` added to the existing write_values
  ImportFrom.
- H3 — `coerce_lookup_id` (HEAD member 51, lines 1187-1250): rewritten
  contract docstring + the 5-line non-Relay arm (HEAD lines 1240-1244).
  The Relay arm (HEAD 1245-1250) is byte-identical modulo the docstring.

Member-number convention below: "recorded N" = the artifact's
`5ee86193` numbering; "HEAD N" = renumbered (§ Enumeration REVISE).

### Judgment: the new arm is a consumer branch — zero new definitions

Both halves verified by fresh HEAD-bytes reads to compose existing
single-sourced owners by name:

- Predicate reuse: `coerce_lookup_id` branches on
  `types/relay.py::implements_relay_node` (HEAD blob `52439862…`,
  one-line body `issubclass(type_cls, relay.Node)`), and
  `mutations/inputs.py::payload_object_slot` (HEAD blob `fc442047…`,
  MATCH) picks the payload slot with the SAME predicate
  (`"node" if implements_relay_node(primary_type) else "result"`).
  The H3 docstring's "the same predicate that picks the payload's
  node/result slot" is accurate. No predicate inlined, no second
  Relay-shape check defined.
- Primitive reuse: the arm coerces via
  `utils/write_values.py::coerce_relation_pk_or_none` (HEAD blob
  `d28587c7…`, MATCH), which is the exact primitive the raw-pk
  relation-id path uses: `write_values.py::type_check_relation_id`'s
  raw-pk branch (HEAD line 155) calls it, and the batched
  `decode_visible_relation_ids` this file's relation decoders ride
  runs that check per element. The H3 docstring's "the same primitive
  a raw-pk relation id uses (`to_python` then `run_validators`)" is
  accurate (the primitive delegates to
  `querysets.py::coerce_field_value_or_none`).
- The routing rule itself ("Relay shape selects the interpretation")
  lives only in `coerce_lookup_id` — one site, no second
  shape-switched id interpretation anywhere (relation ids take BOTH
  shapes unconditionally; the `id:` signature stays `ID!` for all
  primaries). It folds into the existing R7 rule; no new family, no
  new index row.

### Enumeration (REVISE)

Fresh `ast.Module.body` census at both revisions (same instrument):
`5ee86193` = 57 members in exactly the recorded order; HEAD = 58.
Delta is exactly ONE member: HEAD #15
`from ..types.relay import implements_relay_node`. Zero removals, zero
other additions (`coerce_relation_pk_or_none` joins existing member
HEAD #21). Renumber rule: recorded N → HEAD N+1 for all N ≥ 15
(recorded imports 1--23 → HEAD 1--24; `_MUTATION_ASYNC_RECOURSE`
24→25; `coerce_lookup_id` 50→51; module entries 56→57).
Module-level sync defs stay 30, the sole module-level async def stays
`run_pipeline_async`, awaits stay 2.

New member home: consumer import, exempt — same class as recorded
members 1--23. Referenced-proof re-derived at HEAD: 60/60 non-future
imported names `ast.Name`-used (`5ee86193`: 58/58 under the same
instrument; delta exactly the two H2 names, both called in the H3
arm). No index row owed (exempt class carries none).

Fingerprints refreshed: target HEAD `043a2d0b…`.

### Matrix

1. Cross-flavor: STAND. Rider/factory/recourse/save sites all outside
   H1-H3; the relation-decode split unchanged (members 31/32 bodies
   byte-identical).
2. Sync/async: STAND. No hunk adds a def or an await (counts
   re-derived for the enumeration above).
3. Derived knowledge: CONFIRM. Hunks examined: H3's five new code
   lines contain zero attribute reads and compose both halves by name
   (predicate not inlined, coercion not re-derived); H2 adds the two
   names; H1 is prose. Recorded claims (`related_model` kwonly-only,
   zero `InputFieldSpec(`, F9 seed reads) sit outside the hunks; F9's
   counts re-derived identical (see F9).
4. Round-trip: REVISE. The recorded "no second decoder" is superseded
   for the top-level `id:`: it now has TWO composed primitives behind
   the Relay-shape predicate (Relay → `decode_model_global_id`,
   non-Relay → `coerce_relation_pk_or_none`), while relation ids keep
   the one batched compose. Revised verdict: still one DEFINITION per
   rule — both arms compose single-sourced upstream owners
   (§ Judgment); the shape routing is local to `coerce_lookup_id`
   (R7). Payload-pair half unchanged. Axis stays DISCHARGED.
5. Other media: CONFIRM. Hunks examined: the rewritten H1 id-clause
   re-verified clause-by-clause vs the H3 body (Relay→GlobalID +
   model-check, non-Relay→raw pk, uncoercible→not-found, visibility
   locate after) — accurate; the `fields.py` projection drift (11+/9-,
   both hunks inside the module docstring, HEAD lines 1-4 + 30-48)
   re-read and accurate ("a non-Relay primary ... takes the raw pk
   (an uncoercible literal is the not-found FieldError)");
   "1 definition per rule" holds per § Judgment. H2 adds no prose
   claims.
6. Omission: CONFIRM. Hunks examined: the H3 arm's
   `return None, not_found_error()` rides the skeleton's existing
   `id_error → _error_payload` path (HEAD lines 223-225, call site
   textually identical to `5ee86193` line 220), so the
   rollback-uniformity claim extends to the new path with no new
   shape; operation coverage and the EXCLUDED strict-unpack guard sit
   outside the hunks.

### Findings

- F1 shared-write-skeleton: CONFIRM. Hunks examined: the skeleton's
  `coerce_lookup_id(id, primary_type, using=using)` call is textually
  identical (line shift only); ordering/boundary/tail bodies outside
  all hunks; all four riders' drift is docstring-first-line-only (see
  fingerprint table). C1/C2 counts (1 / 1-branch-0-skeleton) cannot
  move: no hunk touches the skeleton body or adds a rider.
- F2 shared-write-entry-factory: STAND. Factory body, all three
  product lines, and the register hand-roll sit outside all target
  hunks; the `fields.py` dispatch lines sit outside that file's
  prose-only drift (hunks at docstring lines only).
- F3 operation descriptors: STAND. The `needs_locate` gate line sits
  outside the target hunks; owner `operations.py` drift is one
  docstring line.
- F4 recourse wording: STAND. Member 24→25 line outside the hunks;
  noun and template unchanged.
- F5 visibility recheck: STAND. Members 30/31→31/32 bodies outside
  the hunks; the `write_values` chain file MATCHes at `d28587c7…`.
- F6 one-sync-boundary: STAND. One-line delegate outside the hunks.
- F7 error envelope: CONFIRM. Hunks examined: `field_error(` 6/6 and
  `null_field_error(` 2/2 lines identical across the drift; H3 adds a
  third `not_found_error()` call line (HEAD 1243) reusing the
  existing member-52 constructor — no new shape, no new code
  vocabulary. The widened not-found TRIGGER set (uncoercible /
  out-of-range / GlobalID-as-literal raw pk) is owned by R7; F7's
  composition claims are unchanged.
- F8 typed-globalid-decode: REVISE. The recorded Relay-arm claims are
  unchanged (status map byte-identical; `decode_model_global_id` 4/4
  lines; `relay.py` MATCHes at `c3c5aea5…`; members 30/31→31/32
  inherit through the unchanged compose). Revision: member 50→51
  gains a sibling non-Relay arm composing
  `coerce_relation_pk_or_none` — a pk-coercion primitive, NOT a
  GlobalID decoder, hence not a second definition of this family's
  rule. The edge is a consumer edge to the write_values coercion
  primitive (no index row names it; the underlying
  `querysets.py::coerce_field_value_or_none` sits under rejected
  `field-value-coercion`, and consumers are not counted, so that
  rejection is undisturbed). Conclusion unchanged: consumer; no index
  change. Fingerprints refreshed: target HEAD `043a2d0b…`, `relay.py`
  `c3c5aea5…` (MATCH), `write_values.py` `d28587c7…` (MATCH).
- F9 seed-and-model-read: CONFIRM. Hunks examined: `model_for(` 5/5
  and `initial_queryset(` 3/3 lines identical; the coerce seed line
  (`target_model = model_for(target_type)`, HEAD 1239) is unchanged
  H3 context; the new arm reuses that binding with no new seed read.
- F10 payload-name: CONFIRM. Hunks examined: `payload_object_slot(`
  4/4, `_payload_type_name` 2/2 identical; no hunk touches a slot
  site. The H3 docstring's same-predicate claim verified at HEAD
  bytes (§ Judgment) — projection alignment, accurate.
- R1 relation decode: CONFIRM. Hunks examined: all six member bodies
  (27--32→28--33) outside the hunks; H2 touches R1's shared
  write_values ImportFrom STATEMENT but adds a name R1 does not
  consume; R1's five composed names unchanged; import census 58→60
  all-referenced (§ Enumeration).
- R2 carve-out, R3 EXCLUDED steps, R4 delete rider, R5 auth seam, R6
  mappers, R8 closure/refetch/payload: STAND. Every member body sits
  outside H1-H3 (verified by hunk line ranges vs member spans);
  connected owners MATCH (`write_transaction.py` `eca9ad4d…`,
  `mutations/permissions.py` `54f770ae…`, `mutations/inputs.py`
  `fc442047…`).
- R7 locate + lookup-id: REVISE (the drift lands here).
  - Contract (revised): `coerce_lookup_id` (HEAD member 51) is now
    shape-switched. Relay-Node primary: unchanged GlobalID decode +
    model-check + pk-coercion with the two recorded error shapes
    (`DECODE_FAILED`/`WRONG_MODEL` → invalid-id; `UNCOERCIBLE_PK` →
    not-found). Non-Relay primary (HEAD 1240-1244): raw pk via
    `coerce_relation_pk_or_none`; `None` (uncoercible or
    out-of-range, incl. a GlobalID string) → the SAME
    `not_found_error()` before any query; a coerced pk still meets
    `locate_instance`'s visibility queryset (hidden == missing
    preserved). `using` threads only to the Relay arm — correct by
    construction (no NodeID-to-pk lookup exists for a raw pk).
  - Sites + roles: definition still here (the routing rule, one
    site). New composed edges:
    `types/relay.py::implements_relay_node` (predicate, HEAD blob
    `52439862…`) and
    `utils/write_values.py::coerce_relation_pk_or_none` (primitive,
    `d28587c7…`, MATCH) — both consumer reuse (§ Judgment).
    `not_found_error` gains its third call line (HEAD 1243);
    `_invalid_lookup_id_error` stays Relay-arm-only (2/2 lines).
  - Challenge (recounted): change the id contract (new shape arm,
    moved trigger, reworded invalid/not-found split) → still **1**
    here (branch + status map + constructors move together;
    predicate/primitive owners move only on their own contract
    changes — 0 here). The two arms vary per shape but are one
    routing site.
  - Owner + lifetime: still this file, file-local. Nothing stored.
  - Behavioral proof: Relay arm — recorded oracles stand
    (`test_coerce_lookup_id_rejects_non_globalid` pins invalid-id
    incl. the raw-pk-string shape at HEAD tests lines 379-396;
    hidden-vs-missing + wrong-model rows intact). Non-Relay arm —
    NEW live oracles at HEAD, static-reviewed here (suite-executed;
    no pytest run in this pass):
    `test_uploads_api.py::test_update_with_an_uncoercible_raw_pk_is_the_not_found_field_error_over_http`
    (parametrized non-numeric / past-the-column-range /
    globalid-is-just-a-literal → `("id", ["not_found"])`, stored
    row untouched) + `..._missing_raw_pk_...` + the happy-path
    raw-pk update rows, all through non-Relay `MediaSpecimenType`
    (HEAD `scalars/schema.py` line 181, no `relay.Node`). Commit
    `ed004ebd` message confirms the carrier design.
  - Structural gate: none owned (as recorded — shape-pinning oracles
    serve).
  - Fingerprints refreshed: target HEAD `043a2d0b…`; `relay.py`
    `c3c5aea5…` (MATCH); `write_values.py` `d28587c7…` (MATCH);
    `types/relay.py` `52439862…` (new pin); `mutations/inputs.py`
    `fc442047…` (MATCH, slot-predicate cross-check).
- J1 partial mechanisms, J2 register arity, J3 call-vs-signature
  gates: STAND. Differences and triggers untouched — no hunk moves a
  validation substrate, the register arity, or either gate (the `id:`
  signature stays `ID!`; `fields.py` drift prose-only).
- J4 converter-table non-membership: STAND. New code adds no
  table/kind computation (`SCALAR` 1/1 = the recorded docstring line;
  `CONVERT` 0/0).
- J5 seal-family non-membership: STAND. New code adds no seal call or
  seed write (`base_queryset(` 0/0; `_seal_or_defect` 0/0;
  `model_for(` 5/5).
- Challenges C1--C12: STAND — no row challenges the lookup-id
  contract (R7 carries its own, recounted above).
- Defects: none recorded, none added. The one released cosmetic edge
  (member 54→55 docstring naming two of three async delegates) sits
  outside the hunks; the H1/H3 prose rewrites introduce no new
  behavior/doc contradiction (both re-verified vs bodies in
  Matrix 5).

### Fingerprint table (HEAD re-hash)

14 recorded inputs, `git rev-parse HEAD:<path>` vs recorded prefix.
7 MATCH / 7 STALE. Every recorded blob equals its `5ee86193` blob
except where noted (so STALE causes are window drift unless stated).

MATCH (all recorded==`5ee86193`, zero window drift):

- `utils/write_values.py` `d28587c7…` — underpins F5/R1/F8-REVISE/R7-REVISE.
- `utils/errors.py` `3e25e93b…` — underpins F7.
- `relay.py` `c3c5aea5…` — underpins F8/R7.
- `mutations/inputs.py` `fc442047…` — underpins F7/F10/R8 + the slot
  cross-check.
- `utils/write_transaction.py` `eca9ad4d…` — underpins R6/R8.
- `mutations/permissions.py` `54f770ae…` — underpins R5.
- `utils/inputs.py` `ee31d360…` — underpins J4.

STALE (causes by diff content; connected-input staleness is reported,
not re-adjudicated — findings no TARGET hunk touches stand per
charter):

- target `3fd1e571…` → HEAD `043a2d0b…` — the adjudicated drift
  (35+/15-); REVISEd findings re-pinned above.
- `forms/resolvers.py` → HEAD `35c282cc…` — 1+/1-,
  module-docstring first line only (`e6a33c46` class); rider/factory/
  recourse sites untouched.
- `rest_framework/resolvers.py` → HEAD `0d302782…` — 1+/1-, same
  first-line-only class.
- `auth/mutations.py` → HEAD `d1a59c44…` — 1+/1-, same
  first-line-only class.
- `mutations/operations.py` → HEAD `9fecef04…` — 1+/1-,
  module-docstring first line only; F3's descriptors owner untouched.
- `mutations/fields.py` → HEAD `d4edcbb7…` — 11+/9-, both hunks
  inside the module docstring (HEAD lines 1-4, 30-48): the id-contract
  projection rewrite (re-verified accurate, Matrix 5) + first line.
  Dispatch lines outside.
- `tests/mutations/test_resolvers.py` → HEAD `4f94c05a…` — 14+/372-.
  NOTE: recorded `4aa8e51e…` already differs at `5ee86193`
  (pre-window drift). Window cause is oracle relocation to the live
  tier (file-column, FK-null, protected-delete rows deleted here,
  added live). Recorded lookup claims intact at HEAD:
  `test_coerce_lookup_id_rejects_non_globalid` (lines 379-396, Relay
  `ItemT`), the NodeID alias pin (line 322), and both F1/F2 structural
  gates survive (`test_delete_pipeline_rides_shared_write_skeleton`
  line 1612, `test_write_flavors_share_resolver_entry_factory` line
  1647).

### Holding-family consequences (Worker-0 routes; the plan is untouched)

- `shared-write-skeleton` (verified family; F1/F2): NO consequence —
  skeleton/factory/boundary sites byte-identical, call site textually
  identical, both gates survive at HEAD. No reopen, no note.
- `typed-globalid-decode` (verified family; F8): NO verdict
  consequence — Relay-arm composition unchanged; the sibling arm is
  pk-coercion, not a second globalid decoder. Informational only:
  member 51 now composes a second primitive (recorded in the F8
  REVISE). No reopen.
- `mutation-error-envelope` (verified family; F7): NO consequence —
  no new shape; trigger widening reuses the existing constructor. No
  reopen.
- `related-object-visibility-recheck` (open family; F5): NO drift
  consequence. OBSERVED (pre-existing, not drift-caused): F5's
  W2-approved files-covered append — this file as transitive consumer
  — was never transcribed; the plan row still lists five files
  without this one. Worker-0 routes whether to transcribe.
- `one-sync-boundary` (open row, verified family artifact; F6): NO
  consequence.
- `queryset-seed-and-model-read` (open; F9): NO consequence — seed
  counts 5/3 identical.
- `sync-boundary-recourse-wording` (rejected; F4): NO consequence.
- `field-value-coercion` (rejected): NO consequence — the new arm
  consumes the write_values wrapper; consumers are not counted,
  rejection undisturbed.
- `mutation-operation-descriptors` / `mutation-payload-name` (F3/F10;
  no index row nor family item — the 09-18/19 transcription state):
  NO drift consequence.
- The five `rest_framework/resolvers.py` rejection rows citing this
  file as comparison: NO consequence — every compared-against site
  sits outside the target hunks.

### Index rows

NONE. The sole new enumeration member (HEAD #15, the
`implements_relay_node` import) is exempt-class machinery, which
carries no row; the new branch folds into the existing R7 rule (no new
rule, no new family). No literal `| ... |` texts proposed. (Note for
Worker-0: this file's F/R/J findings have no index rows at all — the
09-18/19 transcription state — so there is no R7 row to append a file
to; minting rows for the whole file is outside this scoped pass.)

### Record metadata

- Pre-edit artifact: 56687 B /
  `efc900670a13ea1a78d221ea197b9ca90fd47ec4` (recorded before this
  append; post-edit size/hash in the report-back).
- Workspace runs: none — read-only inspection in the shared tree only
  (`git show` / `git grep` / `git diff` + AST census over
  `/tmp/dry-mut-res-HEAD.py` and `/tmp/dry-mut-res-5ee.py`, which are
  read-only `git show` extracts, never executed as package code; they
  ride with the scratch-custody closeout decision).
- Ruff: none owed — zero `.py` paths touched (this artifact only).
- Plan: untouched. Status set `ready-for-verification/stale7-1` on
  completion.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[errors]: ../../django_strawberry_framework/utils/errors.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[operations]: ../../django_strawberry_framework/mutations/operations.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relay]: ../../django_strawberry_framework/relay.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-mutations-resolvers]: ../../tests/mutations/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
## Independent verification (Worker-2) — stale7 re-trace

Run `0.0.15 2026-09-28-7`, address
`dry/dry-file-mutations__resolvers-stale7/verify-1`. Traced HEAD
bytes (`0c0537e2`; target HEAD blob `043a2d0b`, worktree
`c9cff059` hunt dirt — every citation below re-derived from
`git show HEAD:<path>`, never the worktree). This `### Own trace`
plus `### Fingerprints` were written BEFORE opening W1's
`## Iterations`; reconciliation follows separately.

### Own trace (re-derived before reconciling)

Drift re-derived (`git diff 5ee86193..0c0537e2`, own read):

- Target (35+/15-, two commits: `ed004ebd` code + `e6a33c46`
  first line): module-docstring first line + locate-bullet
  rewrite (shape-switched prose); one new member
  `from ..types.relay import implements_relay_node`; one new
  name `coerce_relation_pk_or_none` inside the existing
  `utils.write_values` import; `coerce_lookup_id` docstring
  rewrite + the non-Relay raw-pk arm (5 code lines). No
  other target hunk.
- `mutations/fields.py` (11+/9-, same `ed004ebd`): docstring
  prose only, restating the shape-switched contract from the
  field side ("a Relay-Node primary takes a GlobalID ... a
  non-Relay primary ... takes the raw pk"). Projection of
  the rule owned here; consistent with the new arm.
- Commit `ed004ebd` media: `docs/README.md` both-id-rules
  prose (projection), examples (`MediaSpecimenType` non-Relay
  again; live `updateMediaSpecimen` raw-pk / uncoercible /
  out-of-range / GlobalID-as-literal / missing-pk rows in
  `test_uploads_api.py` + payload `node`→`result` moves —
  oracles spelling literals). No `tests/mutations/` change
  in that commit.
- Riders/owners prose-only: `forms/resolvers.py`,
  `rest_framework/resolvers.py`, `auth/mutations.py`,
  `mutations/operations.py` each differ by exactly the
  `e6a33c46`-class first-line hunk (own `grep ^[+-]`
  census: 4 docstring lines, zero code). Relied-on regions
  (factory call-sites, riders, recourse nouns, descriptors)
  byte-untouched.

Predicate / primitive identity (own HEAD reads):

- `implements_relay_node` is ONE predicate
  (`types/relay.py::implements_relay_node`,
  `issubclass(type_cls, relay.Node)`): the payload slot
  (`mutations/inputs.py::payload_object_slot`, HEAD line
  917) imports it from `..types.relay` (line 52) and the
  new arm imports it from the same owner. Same predicate
  both seams — the docstring's "same predicate" claim is
  exact.
- `coerce_relation_pk_or_none` is the shared raw-pk
  primitive (`utils/write_values.py::coerce_relation_pk_or_none`,
  HEAD line 97: thin compose over
  `coerce_field_value_or_none`), already ridden by the
  relation path (`type_check_relation_id`, HEAD line 155).
  The new arm calls it and maps `None` to the existing
  `not_found_error()` leaf — no coercion re-implemented.

Definition counts + owner judgments (expectations):

- The non-Relay arm is a CONSUMER BRANCH, not a second
  definition of the lookup-id rule: the rule "coerce the
  top-level `id:` to a pk by the target primary's Relay
  shape" is defined once in `coerce_lookup_id`; the arm
  adds one predicate call + one primitive call + the
  pre-existing error leaf. Zero new definitions anywhere
  in the drift.
- R7 challenge stays 1: "new id status / third primary
  shape" moves `coerce_lookup_id` only; a change to
  either composed primitive moves its owner (0 here).
  R7 text needs the shape-switched contract (REVISE
  wording, count unchanged).
- Axis 4 needs REVISE (one-definition-per-rule now via
  TWO composed primitives); axes 3/5/6 need CONFIRM
  (new names composed-by-name, never re-derived; the
  rewritten docstrings are still projections and the new
  live rows are literal-spelling oracles; BOTH primary
  shapes now carry a guard — no omission).
- F8 needs REVISE (second composed primitive at member
  50; the Relay arm is byte-untouched). F1/F7/F9/F10/R1
  need CONFIRM (skeleton calls a widened callee, riders
  untouched; same envelope leaves; same `model_for` seed
  line; the slot predicate is now shared with lookup;
  R1's raw-pk primitive is now also ridden by lookup —
  each examined, no verdict moves). Everything else
  (F2/F3/F4/F5/F6, R2/R3/R4/R5/R6/R8, J1–J5,
  defects-none) SHOULD STAND — no drift hunk reaches it.
- Enumeration: HEAD `ast.Module.body` is 58 by own
  `ast.parse` (was 57): exactly one added member, the
  `types.relay` ImportFrom (exempt class); the
  `coerce_relation_pk_or_none` name joins an existing
  import (no member). Expect REVISE 57→58 with renumber
  and zero removals.
- Holding families: no consequence expected — every
  verified family's definition is byte-untouched; the
  delta is one consumer branch plus projections/oracles.
- Index rows: none owed — the one addition is an exempt
  import composing existing owners.

### Fingerprints (own method: `git rev-parse HEAD:<path>`)

| Path | Prior pin | HEAD blob | Verdict |
|---|---|---|---|
| target | `3fd1e571` | `043a2d0b` | STALE (drift arm + docstrings) |
| forms/resolvers.py | `4edb984b` | `35c282cc` | STALE (one prose line) |
| rf/resolvers.py | `8024703e` | `0d302782` | STALE (one prose line) |
| auth/mutations.py | `dbe64995` | `d1a59c44` | STALE (one prose line) |
| tests/test_resolvers.py | `4aa8e51e` | `4f94c05a` | STALE (window rewrite 14+/372-; both relied-on gates survive at HEAD lines 1612/1647; prior pin resolves as a blob but equals neither baseline `a70b44dd` nor HEAD) |
| utils/write_values.py | `d28587c7` | `d28587c7` | MATCH |
| utils/errors.py | `3e25e93b` | `3e25e93b` | MATCH |
| relay.py | `c3c5aea5` | `c3c5aea5` | MATCH |
| mutations/inputs.py | `fc442047` | `fc442047` | MATCH |
| utils/write_transaction.py | `eca9ad4d` | `eca9ad4d` | MATCH |
| mutations/permissions.py | `54f770ae` | `54f770ae` | MATCH |
| mutations/operations.py | `16223c6b` | `9fecef04` | STALE (one prose line) |
| utils/inputs.py | `ee31d360` | `ee31d360` | MATCH |
| mutations/fields.py | HEAD `cf518361` | `d4edcbb7` | STALE (drift prose restating this contract) |

7 MATCH / 7 STALE expected. Worktree target `c9cff059`
(`git hash-object`, never mixed with `rev-parse`) is hunt
dirt: `truth.*` migration + `_build_wire_name_map` /
`field_name_map` threading, all absent from HEAD bytes
traced here. F5 note (pre-read): plan line 296
`related-object-visibility-recheck` files-covered lists
five files, NOT this one — the approved append is indeed
untranscribed; endorsement judgment after reading W1.

### Reconciliation (every difference, explicitly)

Read W1's `## Iterations` AFTER writing the trace above. There are
no differences of judgment; per-finding verdicts, each re-derived
with own instruments before comparing:

- Judgment (consumer branch, zero new definitions): AGREE.
  Predicate identity re-proved (`inputs.py:52` imports from
  `..types.relay`, slot at `:917`; blob `52439862` matches my
  `rev-parse`); primitive identity re-proved (line 97, ridden
  at line 155); routing rule one site. The "relation ids take
  BOTH shapes" contrast is exact (`type_check_relation_id`
  two-branch body).
- Enumeration 57→58: AGREE member-by-member. Own `ast.parse`
  at both revisions: 57 in recorded order → 58; delta exactly
  HEAD #15 (`types.relay` ImportFrom, re-dumped); renumber
  N→N+1 for N≥15 verified; zero removals; sync defs 30/30,
  one async def, awaits 2/2. Exempt-class home AGREE.
- Matrix: AGREE 6/6 (STAND 1/2, CONFIRM 3/5/6, REVISE 4) with
  W1's reasons. Axis-6 call-site identity re-verified
  first-hand (HEAD 222-225 == `5ee86193` 219-222 modulo
  shift); fields.py projection re-read accurate.
- F1/F7/F9/F10/R1 CONFIRM: AGREE, each on W1's stated
  reason. Token counts re-derived identical across the
  drift: `field_error(` 6/6, `null_field_error(` 2/2,
  `model_for(` 5/5, `initial_queryset(` 3/3,
  `payload_object_slot(` 4/4, `_payload_type_name` 2/2.
- F8 REVISE / R7 REVISE (challenge still 1): AGREE. Relay
  arm byte-identical across the drift (re-diffed 6/6
  lines); `decode_model_global_id` 4/4; R7's "new shape
  arm" recount to 1 follows (routing site one; owners 0
  here). R7 oracle cites verified at HEAD tests bytes:
  `test_coerce_lookup_id_rejects_non_globalid` at line
  379, NodeID alias pin at line 322, gates at 1612/1647;
  live carrier cites verified (`test_uploads_api.py:712`
  + `:737`, `scalars/schema.py:181` non-Relay).
- STAND set (F2/F3/F4/F5/F6, R2/R3/R4/R5/R6/R8, J1–J5,
  C1–C12, defects-none): AGREE on stated hunk-scope
  reasons. J4/J5 censuses re-derived: `SCALAR` 1/1,
  `CONVERT` 0/0, `base_queryset(` 0/0, `_seal_or_defect`
  0/0.
- Fingerprints: AGREE 14/14 digit-for-digit (own table
  above, `git rev-parse HEAD:<path>` throughout). Every
  STALE cause AGREE: four prose-only singles (own
  `grep ^[+-]` census: 4 docstring lines, zero code),
  fields 11+/9- docstring projection, target drift, tests
  14+/372- oracle relocation with gates surviving. The
  tests pin-correction note is accurate: recorded
  `4aa8e51e` resolves as a blob but equals neither
  baseline `a70b44dd` nor HEAD `4f94c05a` (pre-window
  run-2 pin, superseded).
- Holding-family consequences (10 rows): AGREE, no
  consequence anywhere. The five rf-resolvers rejection
  rows name save/partial/null-mapper sites, none in
  H1–H3 scope. The F3/F10 "no index row" note verified
  (zero plan hits).
- Index rows NONE: AGREE — exempt import + no new rule;
  the querysets narrow-pass precedent does not apply
  (that pass added non-exempt members).
- F5 pre-existing observation: ENDORSE. Plan line 296
  lists five files without this one; the run-2 approval
  stands unexecuted. Worker-0: transcribe
  `django_strawberry_framework/mutations/resolvers.py`
  (transitive consumer) into the
  `related-object-visibility-recheck` files-covered.

One immaterial instrument note (not errata): W1's
referenced-import census reads 60/60 vs 58/58 where my
module-body instrument reads 59/59 vs 57/57. The 1-name
delta is the function-local `from . import inputs` (HEAD
line 1284, inside `payload_cls_for`), which W1 counts
tree-wide; both instruments agree everything is
referenced and the delta is exactly the two H2 names.
No verdict depends on the absolute.

### Nothing-else-changed

- W1's change: `## Iterations` plus the `Status:` swap;
  all base sections read internally consistent with the
  run-2 verified record, no interleaved edits visible.
- My change: this `## Independent verification
  (Worker-2) — stale7 re-trace` section, EOF append only
  (76263 B → 82727 B → post-reconciliation size below).
- No production edit, no plan edit, no tracked file
  touched by either worker: window `git diff
  7546610e --name-only` names only `docs/dry/dry-0_0_15.md`
  (Worker-0's). Zero `.py` touched → no ruff owed.
- AGENTS.md prose: both appends use `path::Symbol`
  citations; `HEAD <line>` cites are permitted raw
  numbers in `dry-*.md` scratchpad artifacts; no process
  provenance, no test-tier issue, no feedback-file
  mention. My section adds no reference-style links, so
  the link-definition block needs no entry.
- Scratch: `/tmp/dry-w2-head.py`, `/tmp/dry-w2-base.py`
  (`git show` extracts, read-only census inputs) ride
  with the scratch-custody closeout decision, as do
  W1's cited `/tmp/dry-mut-res-*.py`.

`Status: verified`. Zero-edit scoped re-trace: drift
adjudicated at HEAD blob `043a2d0b`, REVISE set +
CONFIRM set + STAND rest all AGREE-re-derived, 7/7
MATCH + 7/7 STALE fingerprints digit-for-digit, F5
append endorsed for transcription, no holding-family
consequence, no index rows owed, no pending execution.
