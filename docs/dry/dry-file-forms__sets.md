# DRY review: `django_strawberry_framework/forms/sets.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a reused family row (re-derived fresh, never inherited), a
file-local record with its proving challenge, or a recorded rejection with
contract difference + trigger + durable home. Zero production edits; zero
tracked files changed.

## System trace

Target (`django_strawberry_framework/forms/sets.py`, 1035 lines, blob
`36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`; absent from the item-scoped
diff vs both baselines, target CLEAN): the form-mutation write surface
(spec-038 Decisions 6/7/10/11/13). It DEFINES the two form bases'
`Meta` validation matrices
(`DjangoModelFormMutation._validate_meta` /
`DjangoFormMutation._validate_meta`), the model-less declaration ledger
(`_form_mutation_declaration_registry` + its five bound names), the
plain-form metaclass (`DjangoFormMutationMetaclass`), the per-shape
form-input build cache (`_form_shape_build_cache` +
`_cached_build_form_input`), the ten twin-shared module helpers, the
construction-hook machinery (defaults + waiver + invocation boundary +
frozen snapshot), the plain write-auth seam (`check_permission`) + write
hook (`perform_mutate`), the two `Meta` allowed-key sets, and the
model-less bind (`bind_form_mutations`). It CONSUMES (by name, P2-proved
23/23) the shared write foundation in [mutations-sets][mutations-sets]
(the two `Meta` key foundations, `DjangoMutation`, `_hook_overridden`,
`_validate_permission_classes`, `_ValidatedMutationMeta`,
`bind_write_declarations`, `build_and_stash_input`, `cached_build_input`,
`construction_kwargs`, `make_declaration_registry`,
`make_meta_validating_metaclass`, `model_backed_permission_and_lock`,
`normalize_meta_field_selection`, `reject_unknown_meta_keys`,
`require_backing_class`, `require_model_class`,
`require_non_delete_operation`, `require_subclass`,
`resolve_backed_model_or_raise`, `resolve_meta_model`,
`resolver_seams`), the kind vocabulary (`PARTIAL` in
[mutations-inputs][mutations-inputs], `FORM` in
[forms-inputs][forms-inputs]), the permission walk (`run_permission_classes`
+ `DenyAll` + `DjangoModelPermission` in
[mutations-permissions][mutations-permissions]), the bus
(`register_subsystem_clear` in [registry][registry]), the shape-cache
factory (`make_shape_build_cache` in [utils-inputs][utils-inputs]), and
the form-input generator + narrowing + naming + guards in
[forms-inputs][forms-inputs] (11 names, P2-adjacent census: all
referenced).

Connected code read for judgment, outside the item: the model twin FIRST
(whole [mutations-sets][mutations-sets], 1733 lines) + the serializer
mirror (whole [rf-sets][rf-sets], 1013 lines: one `DjangoMutation`
subclass riding the same promoted seams); the owners
([mutations-permissions][mutations-permissions] full read,
[mutations-inputs][mutations-inputs] kind regions,
[mutations-operations][mutations-operations]
`NON_DELETE_OPERATION_INPUT_KIND` region, [utils-inputs][utils-inputs]
cache-factory region, [registry][registry] bus regions); the set-family
substrate ([sets-mixins][sets-mixins] via its verified artifact, plus
`_lifecycle` absence re-proved here); the auth mirror
([auth-mutations][auth-mutations] seal regions: own `_SealedAuthHolderMeta`
+ own holder snapshot, mirroring not sharing); the build side
([forms-inputs][forms-inputs] via its verified artifact) + the decode
consumer ([forms-resolvers][forms-resolvers] via its verified artifact:
reads the stashed `_input_field_specs`, calls `check_permission`
through `authorize_or_raise`); the bind consumer
([finalizer][finalizer] `bind_mutations()` + `bind_form_mutations()`
call regions); oracles in [test-forms-sets][test-forms-sets] (66-function
inventory) and the shared-factory gates in
[test-mutations-sets][test-mutations-sets]; contract source spec-038
Decisions 6/7/10/11/13; projections [forms-init][forms-init]
(subsystem prose), the module docstring, and the glossary
`DjangoFormMutation` / `DjangoModelFormMutation` entries; live consumers
in `examples/fakeshop/apps/products/` (six `ModelForm` mutations in
`schema.py`, plain-form fixtures in `forms.py`).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P5, all
read-only, all green; commands under `### Challenges`).

1. **Cross-flavor policy mirroring.** Searched, the model twin read whole
FIRST. P2 proves the sharing shape by behavior, not tokens: one
`make_declaration_registry` call per ledger (two disjoint stores, no
code-level cross-reads); one `make_shape_build_cache` unpack per flavor
(three disjoint dicts with the model/serializer flavors); `Meta` key
sets composed by frozenset union from the shared foundations (never
re-spelled); two metaclasses from one factory (ModelForm rides the
model metaclass by inheritance, plain instantiates it over its own
ledger); both binds ride one `bind_write_declarations` drain with the
only per-ledger divergence injected (`resolve_object_type`: primary
`DjangoType` vs `None`); all four write bases expose `resolve_sync` /
`resolve_async` from one `resolver_seams` factory (`with_id=False`
only for the model-less flavor); both construction defaults share the
`construction_kwargs` instance-clause; both `check_permission` bodies
share `run_permission_classes`; the serializer mirror rides
`cached_build_input` / `build_and_stash_input` / `resolver_seams` /
`construction_kwargs` without redefining any (P2 step 7). What stays
per flavor is the documented variation: the two `Meta` matrices (R1/R2),
the operation vocabularies (`create`/`update` vs the `FORM` sentinel),
the permission defaults (`DjangoModelPermission` vs `DenyAll`), and the
payload shape (object slot vs pinned `{ ok errors }`). Verdict: one rule
per surface; see F1--F3, R1--R8, J1--J5.
2. **Sync/async twins.** Discharged inapplicable by construction.
Instrument (P1): zero `AsyncFunctionDef`, zero `await` in the target.
The async surface is not a twin body: both `resolve_async` entries are
the shared factory's product running the same sync pipeline through the
shared async boundary (the DRY.md principle-5 single-sync-body shape
the [forms-resolvers][forms-resolvers] artifact already pins: no awaits
may interleave inside the transaction). No second form pipeline to
drift; `perform_mutate` / `check_permission` are sync-only seams the
boundary wraps. No twinship, no finding.
3. **Derived rather than repeated knowledge.** Searched. Input names
derive via `form_input_type_name` (P4 naming-purity: both
`input_type_name` seams equal the factory derivation byte-for-byte, no
local spelling). Effective field sets derive via
`resolve_effective_form_fields`: the snapshot stores the normalized
pair, the bind re-resolves it — one walk, never re-derived (P3 routing:
the hook resolves once in `_build_and_stash_form_input` and flows down
as a parameter). `Meta.operation` presence follows normal attribute
lookup (`hasattr`, MRO-visible) deliberately, matching the ModelForm
flavor's inherited-operation posture (body-read + P4 inherited-arm
proof). `Meta.permission_classes` defaults derive per flavor from the
shared validator (different `unset_default` args, one body). No fact
re-derived.
4. **Inverse / round-trip pairs.** Searched, both directions verified.
Declare (metaclass validate + register) pairs with bind (drain +
materialize + stash). Field set → input (build) pairs with input →
form-keyed payload (decode in [forms-resolvers][forms-resolvers] via
the stashed `_input_field_specs`, never rebuilt). Name
(`input_type_name`) pairs with bind materialize name (oracle
`test_input_type_name_seams`, static-reviewed; P4 proves the seam side
is a pure delegation). Narrow (`Meta.fields` / `Meta.exclude`) pairs
with drop-detection (guard runs per declaration BEFORE the per-shape
cache lookup via `cached_build_input`, so a waiving mutation cannot
suppress a later guard — body-read + oracle
`test_cached_build_form_input_runs_required_guard_per_declaration`,
static-reviewed). One grammar per pair, correctly separated halves.
5. **Contracts restated in another medium.** Counted 1 definition per
rule; everything else classified: module docstring (projection,
clause-verified incl. the two-base split, the disjoint matrices, the
waiver wiring, the reverse-map stash); [forms-init][forms-init]
subsystem prose (projection); spec-038 Decisions 6/7/10/11/13
(contract sources); [test-forms-sets][test-forms-sets] rows (oracles
spelling literals: matrix rejects, hook-boundary rejects, waiver rows,
ledger-split rows, dedupe rows — no oracle iterates an owner table;
the narrowed-name determinism oracle pins the `FORM`-sentinel shape);
[test-mutations-sets][test-mutations-sets] factory gates (pin the
shared mechanics both flavors ride); glossary entries (projections);
live products mutations (consumers riding the seams). No medium holds
an independently maintained copy of any rule.
6. **Enforcement by omission.** Seam coverage enumerated per flavor
against the twin census (P3): eight seam names both bases carry
(`get_form_fields`, `_validate_meta`, `build_input`,
`input_type_name`, `get_form_kwargs`, `get_form`,
`_input_field_specs`, `input_module_path`); each divergence carries
its contract source — `_resolve_model` ModelForm-only (Decision 6:
plain is model-less), snapshot/bind attrs plain-only (ModelForm
inherits them from `DjangoMutation`), `check_permission` /
`perform_mutate` plain-only (ModelForm inherits the check and saves
via `form.save()` in the resolver — Decision 6/8), `with_id=False`
plain-only (no row to locate), `select_for_update` ModelForm-only
(plain locates no row; constructor default `False`), operation
vocabulary split (Decision 10: `create`/`update` vs reject-any). The
`None`-valued `operation` and inherited-`Meta.operation` rejects
close the presence-check omission case (P4 both arms). No missing
guard with a contract source behind it — no defect filed.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-forms__sets/p1_ast_census.py`), count
**36**. Every member lands below; R = file-local finding, F = reused
family row (non-membership checked, never inherited). Class members
(11 ModelForm + 16 plain, P3-pinned) land via their class row.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | verified clause-by-clause |
| 2 | `from __future__` | machinery import | consumer |
| 3 | `typing.Any` | annotation import | consumer |
| 4 | `django.forms` | key-space import | R1/R2 consumer |
| 5 | exceptions import (2 names) | helper imports | R6/R7 consumers |
| 6 | mutations.inputs import (`PARTIAL`) | kind import | R4 consumer (owner upstream) |
| 7 | mutations.permissions import (3 names) | auth imports | R2/R7 consumers (owners upstream) |
| 8 | mutations.sets import (23 names) | spine imports | F1/F2/F3 + R1/R2/R4/R6/R7/R8 consumers (P2: all 23 referenced) |
| 9 | registry import (1 name) | bus import | F1 consumer |
| 10 | utils.inputs import (1 name) | factory import | F1/R4 consumer (owner upstream) |
| 11 | .inputs import (11 names) | generator imports | R4/R5/R6/R8 consumers (owners in forms-inputs) |
| 12 | .inputs `INPUTS_MODULE_PATH` import | namespace import | R8 consumer |
| 13 | `_ALLOWED_MODELFORM_META_KEYS` | key set | R8 |
| 14 | `_ALLOWED_PLAIN_FORM_META_KEYS` | key set | R8 |
| 15 | `_form_mutation_declaration_registry` | ledger declaration | R3 (F1 contributor) |
| 16 | `register_form_mutation` | bound name | R3 |
| 17 | `clear_form_mutation_registry` | bound name | R3 + F1 |
| 18 | `iter_form_mutations` | bound name | R3 |
| 19 | `_form_mutation_registry` | backing store | R3 |
| 20 | `register_subsystem_clear(...)` forms.declarations | registration | F1 (REUSE contributor) |
| 21 | `_form_shape_build_cache, clear_form_shape_build_cache` | cache pair | R4 (F1 contributor) |
| 22 | `register_subsystem_clear(...)` forms.shape_cache | registration | F1 (REUSE contributor) |
| 23 | `_default_mutation_get_form_fields` | default hook | R7 |
| 24 | `_mutation_form_fields` | hook boundary | R7 |
| 25 | `_cached_build_form_input` | cache + guard | R4 |
| 26 | `_resolve_effective_form_field_names` | narrowing wrapper | R5 |
| 27 | `_normalized_form_field_selection` | selection wrapper | R5 |
| 28 | `_form_kwargs_overridden` | waiver detection | R7 |
| 29 | `_default_get_form_kwargs` | default hook | R7 |
| 30 | `_default_get_form` | default hook | R7 |
| 31 | `_build_and_stash_form_input` | build tail | R6 |
| 32 | `_form_input_type_name_for` | name tail | R6 |
| 33 | `DjangoModelFormMutation` (11 members, P3) | ModelForm base | R1 |
| 34 | `DjangoFormMutationMetaclass` | metaclass | R3 (F2 consumer) |
| 35 | `DjangoFormMutation` (16 members, P3) | plain base | R2 (+ R7 for its auth/hook members) |
| 36 | `bind_form_mutations` | bind drain | R3 (F3 rider) |

No member unassigned. Prior-cycle trigger notes re-checked fresh, never
inherited: the sets_mixins item's F1--F8 + population rows (each
checked below as reuse or non-membership, P1/P2 re-proved from this
side); the converter item's table rejection (this file holds no table —
F12); the inputs item's R3 projection (this file assembles the
4-component key consuming member 26's owner by name — R4); the
resolvers item's F3 skeleton + entry-factory split (this file rides
the drain, takes the factory product — F3).

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, not counted. Executed
probes are read-only files under
`docs/dry/temp-tests/dry-file-forms__sets/` run with `uv run python`
from the repo root; NO shared-tree pytest, NO source mutation (so no
workspace copy was owed), NO database opened by any probe (P4/P5 run
with empty `DATABASES`; the Group model class is read, never
queried).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | add a form `delete` pipeline (new ModelForm operation) | **1** (R1 matrix + `require_non_delete_operation` owner move together only if the owner widens; plain unaffected) | operation oracles, bind seams |
| C2 | give the plain flavor an operation | **1** (R2 presence-reject + `FORM` sentinel + bind `operation_kind`) | plain oracles, payload shape |
| C3 | change a permission default | **1** per flavor (R1 `model_backed_permission_and_lock` call vs R2 `DenyAll` default + model-permission reject) | permission oracles |
| C4 | add a ledger lifecycle slot | **0 here** (factory + bus owners); disjointness config **1 here** | wrappers follow |
| C5 | add a 5th cache-key axis | **0 here** for the projection (owner `forms/inputs.py`); assembly **1 here** (R4 key tuple) | dedupe oracles |
| C6 | change guard-before-cache ordering | **0 here** (owner `cached_build_input`); this file follows as consumer | guard oracles |
| C7 | change the waiver rule | **1** (R7; serializer unaffected — `Meta.injected_fields` only) | waiver oracles |
| C8 | change a default construction body | **1** (R7 shared default; both flavors follow) | construction oracles |
| C9 | change the permission walk | **0 here** (owner `run_permission_classes`); plain seam presence **1 here** | auth oracles |
| C10 | change the input-name grammar | **0 here** (owner `form_input_type_name`); kind decision **1 here** | naming oracles |
| C11 | change a `Meta` key set | **1** per set here (R8; foundations 0 here) | typo-guard oracles |
| C12 | reword a seal message | **0 here** (factory + snapshot owners); both flavors follow by construction | seal oracles |
| C13 | unify the twins behind a mode flag | **refused** (J1: every seam forks) | -- |
| C14 | merge the two matrices into one parametrized validator | **refused** (J2: disjoint key sets, opposite operation/permission rules) | -- |
| C15 | name form inputs via the set-family rule | **refused** (J3: different source domains) | -- |
| C16 | put write flavors on the heavy `_lifecycle` | **refused** (J4: nothing to reset beyond ledgers) | -- |
| C17 | ride the plain flavor on `DjangoMutation` | **refused** (J5: model-less has no model/operation/object slot) | -- |

Probe commands + what each proved (every probe `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-forms__sets/p1_ast_census.py`
  -- 36 members, 0 async defs, 0 awaits, 11 module functions, 2 classes
  (11 + 16 members), 11 imports, 27-clause non-membership def-scan
  (matrix axes 2 + enumeration instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__sets/p2_write_mirror.py`
  -- 23/23 shared-seam imports referenced; disjoint ledgers, caches,
  and code-level store reads; composed key sets; metaclass split;
  shared drain; serializer seam-sharing; no set-family substrate in
  any write flavor. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__sets/p3_form_twins.py`
  -- 8 shared seam names on both bases; designed divergences
  (`_resolve_model`, snapshot/bind attrs, `check_permission`,
  `perform_mutate`, `with_id=False`); hook-once-then-parameter
  routing. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__sets/p4_behavior.py`
  -- plain matrix (operation presence incl. `None` + inherited,
  ModelForm-first, non-Form, missing, unknown key, model-permission
  reject), plain `DenyAll` default + `[]` opt-out + `FORM` sentinel,
  ModelForm matrix (delete, missing operation, plain-Form redirect,
  missing `form_class`) + Group resolution + model-permission default,
  head seals on BOTH metaclass products (rebind + delete raise), slot
  seal (write + delete raise), waiver detection (default False,
  either-hook override True), naming purity (both seams equal the
  factory derivation), registry split (disjoint ledgers, abstract
  bases nowhere), self-cleaning (stores empty after). 35 checks,
  `execution-verified`, no database.
- `uv run python docs/dry/temp-tests/dry-file-forms__sets/p5_bus.py`
  -- both clears on the bus with owners `forms.declarations` /
  `forms.shape_cache`; owner-disjointness (8 loaded owners, each
  once); registration identity; no-op safety.
  `execution-verified`, no database.
- Source census (inline): 17 `register_subsystem_clear` call sites
  package-wide incl. both target rows with distinct owners; zero
  `type_name_for` / `expanded_once` / `_lifecycle` / `traversal` /
  `ActiveInput` definitions or code uses in the target (the 16
  `_permission` hits are all the `permission_classes` Meta key, never
  the facade record; the 3 `type_name_for` hits are the distinct
  `_form_input_type_name_for`). `execution-verified`.

## Findings

### F1 -- `subsystem-clear-lifecycle` (REUSE, index: open)

- **Contract + variation.** Every subsystem reset rides the registry
  bus; generated-input namespaces reset ledgers only, never parked
  module globals. Varies by adding a lifecycle slot (C4 counts 0
  here).
- **Sites + roles.** Owners: [registry][registry]`::register_subsystem_clear`
  (bus) + [mutations-sets][mutations-sets]`::make_declaration_registry`
  / `::make_shape_build_cache` via [utils-inputs][utils-inputs]
  (mechanics). Target role: state contributor — member 15 (ledger
  declaration over the owner product), member 17 (clear bound name),
  member 19 (backing store), member 20 (registration,
  `owner="forms.declarations"`), member 21 (cache pair), member 22
  (registration, `owner="forms.shape_cache"`). No local clear body
  (both clears are factory-bound bound names; P5 identity-proved).
  Sibling contributors: the model ledger + cache in [mutations-sets][mutations-sets],
  the input namespaces in `forms/inputs.py` / `mutations/inputs.py` /
  serializer inputs (P5 owner census: 8 loaded owners, each once;
  source census: 20 registration sites, all disjoint owners).
- **Challenges.** C4 counts 0-here/1-config.
- **Owner + lifetime.** Bus + factory owners (principle 7: the
  narrowest owners every flavor can depend on without importing a
  sibling). Lifetime: per-pass build caches cleared at bind-drain
  top + co-cleared from `registry.clear()`; ledgers cleared from
  `registry.clear()` only (projections at the factory docstrings,
  not restated here).
- **Migration.** None (already compose by name; file item owes no
  edit).
- **Distinct behavior.** Light clear (ledger `.clear()` + cache-dict
  clear only) vs the set families' heavy clear (factory caches +
  `_lifecycle` binding state) — the write flavors have neither a BFS
  cache nor per-set expansion state (J4).
- **Behavioral proof.** P5 (`execution-verified`: owners, disjointness,
  identity, no-op safety). Ledger + cache emptiness rows in
  [test-forms-sets][test-forms-sets]
  (`test_form_shape_build_cache_clears_via_registry_and_direct_clear`)
  `static-reviewed`.
- **Structural gate.** The cache/ledger emptiness oracles fail any
  bypass that parks state outside the registered objects (a second
  dict would survive the clear and the emptiness assertion breaks).
- **Freshness.** Target `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`;
  [mutations-sets][mutations-sets] `cffa29e52002e1cfef94a032366524fb69c9d258`;
  [registry][registry] `9cc8bb553fd417fc465809a541769a8383469cda`;
  [utils-inputs][utils-inputs] `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`;
  [forms-inputs][forms-inputs] `55614839ff479b3610b6026be65f2107ee560fcd`;
  HEAD `9031cb3d`.

### F2 -- `sealed-authorization-source` (REUSE as consumer, index: open)

- **Contract + variation.** The validated authorization snapshot is
  sealed at two levels: the slot seal (no attribute write/delete on
  the record) and the head seal (no rebind/delete of the class head
  holding the record). Varies by rewording (C12 counts 0 here).
- **Sites + roles.** Owners: [mutations-sets][mutations-sets]
  `::_ValidatedMutationMeta` (slot seal) +
  `::make_meta_validating_metaclass` (head seal). Target role:
  consumer on both flavors — the ModelForm flavor rides the model
  metaclass by inheritance (head seal inherited) and snapshots the
  shared record class (slot seal by construction); the plain flavor
  instantiates the SAME factory over its own ledger (member 34; a
  second metaclass instance sharing the seal source, not a second
  seal definition) and snapshots the same record class. Checked, not
  assumed: P4 proves both seals fire on BOTH flavors' live products
  (rebind + delete raise on each head; write + delete raise on a
  plain snapshot). The auth mirror ([auth-mutations][auth-mutations]
  `::_SealedAuthHolderMeta` + holder snapshot) deliberately MIRRORS
  rather than shares — different record shape (3 slots vs 15), same
  threat model, recorded at its own seam; this file does not mirror,
  it shares. No index change proposed (rows already cover the two
  owners; this file is a covered consumer).
- **Challenges.** C12 counts 0 here.
- **Owner + lifetime.** Factory + record class upstream (principle 7:
  the narrowest owner all write flavors can import without a sibling
  dependency). Lifetime: snapshot sealed at `__init__` end; head
  sealed after the creation-time write; both immutable for the
  process lifetime.
- **Migration.** None (already shared by construction; file item owes
  no edit).
- **Distinct behavior.** None within the family — the plain flavor's
  separate metaclass INSTANCE is storage disjointness (Decision 13),
  not a seal fork: the seal source is identical.
- **Behavioral proof.** P4 (`execution-verified`: both seals on both
  flavors) + the model-side seal oracles
  (`test_whole_record_swap_and_deletion_on_a_real_mutation_class_are_sealed`)
  + the factory gate
  (`test_make_meta_validating_metaclass_validates_registers_and_skips_abstract`)
  `static-reviewed`.
- **Structural gate.** The model-side seal oracles fail a seal
  weakening at the shared source (both flavors ride the same bodies,
  so a fork here cannot hide from them); P4 pins the plain-flavor
  participation directly.
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [auth-mutations][auth-mutations]
  `dbe64995b87240b87a1d5119f46cc42c7cab646f`;
  [test-mutations-permissions][test-mutations-permissions]
  `9cef2100fcb72adef7fd214deef91179a66cddde`;
  [test-auth-mutations][test-auth-mutations] `6390492979efe8ee6f9268a355b1f75404bbdbc6`.

### F3 -- `shared-write-skeleton` (REUSE as rider, index: open)

- **Contract + variation.** One drain owns the per-pass cache clear +
  iterate + `build_input` seam + payload tail; one entry factory owns
  the `UNSET` normalization + the single-`sync_to_async` async
  boundary. Varies per flavor middle (C-ordering/C-boundary count 0
  here for drain/boundary, 1 here for the flavor branch).
- **Sites + roles.** Owners: [mutations-sets][mutations-sets]
  `::bind_write_declarations` (drain), `::make_resolver_entries`
  (entries), `::run_write_pipeline_sync` (skeleton, covered by the
  [forms-resolvers][forms-resolvers] artifact). Target role: rider —
  member 36 drains the disjoint plain ledger with
  `resolve_object_type=lambda _mutation_cls, _meta: None` (selecting
  the pinned `{ ok errors }` payload and keeping `_primary_type`
  `None`); the ModelForm flavor rides `bind_mutations()` with zero
  local bind code; members 33/35 take the `resolver_seams` factory
  product (P2/P3: two calls, `with_id=False` only for the model-less
  flavor). Sibling riders: model, serializer (whole-read), auth
  register (per the resolvers artifact's fourth-rider note). Sub-rule
  split per that artifact's W2 ruling: skeleton vs entry factory stay
  separate rows; the async boundary stays a consumer edge of the open
  `one-sync-boundary` family (no row here: zero
  `run_in_one_sync_boundary` / `run_pipeline_async` definitions or
  calls, P1-adjacent census).
- **Challenges.** Drain/boundary changes count 0 here; a new flavor
  branch counts 1 here (R1/R2 `build_input`).
- **Owner + lifetime.** Drain/skeleton modules (principle 7: the model
  pipeline is the origin; both later flavors import from it, never
  the reverse — dependency direction wins). Nothing stored (per-pass
  cache cleared at drain top; materialization ledgers reset once by
  the finalizer, not per pass — projection at the drain docstring).
- **Migration.** None (already composed by name; file item owes no
  edit).
- **Distinct behavior.** The `object_type=None` plain branch (no
  locate, no object slot, `{ ok: true }` tail) vs the model-backed
  branch — recorded at member 36's docstring.
- **Behavioral proof.** P2 (rider shape: shared drain call, divergent
  resolver, per-pass cache arg) (`execution-verified`);
  `static-reviewed` bind oracles
  (`test_modelform_registers_in_mutation_registry`,
  `test_plain_form_registers_in_disjoint_form_registry`,
  `test_modelform_bind_materializes_form_input_into_forms_namespace`,
  `test_plain_form_bind_materializes_input_and_ok_errors_payload`,
  `test_form_bind_is_retry_idempotent_after_fixable_later_phase_failure`).
- **Structural gate.** The ledger-split oracles fail a drain
  divergence that binds one ledger through the other's object-type
  resolution (a plain mutation bound with a primary would stash a
  non-`None` `_primary_type` where the `{ ok errors }` rows pin
  `None`); the factory-sharing oracle
  (`test_write_flavors_share_resolver_entry_factory`) fails an
  entry-shape drift.
- **Coupling.** None introduced (zero-edit).
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [rf-sets][rf-sets] `2c7117d6410ecab315abde0d56f861938ba6ab1b`;
  [finalizer][finalizer] `77fd9a2dd229eb9de5f29188c5058035d3606323`;
  [test-forms-sets][test-forms-sets] `5c3b964c20306f56b6cc8a99e860b4d104f28ed7`;
  [test-mutations-sets][test-mutations-sets] `2dc45288a616137283bac8504ca072e33218b21e`.

### F4 -- `set-type-naming` (checked non-membership)

This file does NOT join the family: it builds no type names (P1
def-scan: zero `type_name_for` definitions; the 3 text hits are the
distinct `_form_input_type_name_for`). Both `input_type_name` seams
delegate to `form_input_type_name` over the shared naming spine
(P4 purity). The create-vs-partial kind decision each seam passes is
the wrapper's own one-line rule (R6/C10), not a naming rule. The
family's R2 intentional-separation home already names this file's
seam — CONFIRMED from this side, no index change proposed.

### F5 -- `related-set-target-lifecycle` (checked non-membership)

This file does NOT join the family: zero `_target_attr` /
`_owner_attr` / `_bind_owner` / `_resolved_target` / `_set_target` /
`_validate_target` definitions or code uses (P1-adjacent census).
Model resolution here is the `_resolve_model` seam (one backing
class's model, no lazy related-set graph, no owner bind, no gate).
No index change proposed.

### F6 -- `related-declaration-collection` (checked non-membership)

This file does NOT join the family: the metaclass factory collects a
single `Meta` per class (validate-then-register), never a related
declaration graph; zero `collect_related_declarations` definitions
or calls. The two ledgers collect declarations, not relations. No
index change proposed.

### F7 -- `set-expansion-once-skeleton` (checked non-membership)

This file does NOT join the family: no class-level expansion cache,
no reentry guard, no `_build` closure (P1 def-scan clean). The
per-shape INPUT build cache (R4) is a different contract: it dedupes
generated input class objects across declarations by shape identity,
not one class's expansion published once under a guard. No index
change proposed.

### F8 -- `set-expansion-cache-write-gate` (checked non-membership)

This file does NOT join the family: zero `should_cache_expansion`
definitions or calls. The create-required waiver (R7) is a
per-declaration guard-skip on hook identity, not a cache-write
predicate on resolution state. No index change proposed.

### F9 -- `re-readable-field-declaration-gate` (checked non-membership)

This file does NOT join the family: `Meta.fields` shape validation
rides `resolve_effective_form_fields` / `normalize_field_name_sequence`
by name (members 26/27; owners in [forms-inputs][forms-inputs] /
[utils-inputs][utils-inputs]), never a local re-spelling of the
re-walkability predicate. No index change proposed.

### F10 -- `active-input-permission-facade` (checked non-membership)

This file does NOT join the family: zero `ActiveInput*` / `traversal`
definitions or code uses; no `_permission` record (the 16 text hits
are all the `permission_classes` Meta key, verified in context).
Authorization here is the write-auth seam (`Meta.permission_classes`
+ `check_permission` over `run_permission_classes`, R2/R7), not the
read-side input-permission facade over related branches. The family
index row does not list this file — CONFIRMED correct, no index
change proposed.

### F11 -- `type-registry-model-type-map` (checked non-membership)

This file does NOT join the family: zero `registry.get` /
`types_for` / `definition_for` reads (P1-adjacent census). Primary-type
resolution for the ModelForm flavor happens inside the ridden
`bind_mutations()` drain (F3), never here; the plain drain resolves
`None`. No index change proposed.

### F12 -- `converter-table-per-surface-ownership` (checked non-membership)

This file holds NO converter table (P1-adjacent census: zero
`_SCALAR` / `_CONVERT_` / registry definitions; it does not even call
`convert_form_field` — field conversion lives in the owned generator).
The plan's row already covers its four files; this file is not a
fifth. No index change proposed.

### R1 -- ModelForm `Meta` matrix (file-local)

- **Contract + variation.** Member 33's `_validate_meta`: unknown-key
  typo guard over `_ALLOWED_MODELFORM_META_KEYS`; missing
  `form_class` presence; `forms.ModelForm` type gate BEFORE model
  resolution (clean error, never raw `AttributeError`); no-resolvable
  model raise; `require_model_class` gate; `create`/`update` operation
  via `require_non_delete_operation` (`delete` rejected — no form
  delete pipeline, Decision 10); narrowing fail-loud via the shared
  machinery; `DjangoModelPermission` default + `FOR UPDATE` lock via
  `model_backed_permission_and_lock`. Varies per arm (C1/C3/C11
  count 1 here for the flavor's arms; spine changes count 0 here).
- **Sites + roles.** Definition here (the matrix). Spine owners:
  [mutations-sets][mutations-sets] (all 23 composed by name, P2).
  Consumers: the metaclass validation call, the bind, the resolver.
  Oracles: `test_modelform_missing_form_class_raises`,
  `test_modelform_with_plain_form_raises`,
  `test_modelform_with_no_resolvable_model_raises`,
  `test_modelform_non_model_meta_model_raises_at_class_creation`,
  `test_modelform_delete_operation_rejected`,
  `test_modelform_missing_operation_rejected`,
  `test_modelform_unknown_meta_key_raises`,
  `test_modelform_fields_and_exclude_both_raises`,
  `test_modelform_unset_permission_classes_keeps_model_permission_default`
  (P4 re-proved the delete/missing/plain-Form arms + Group
  resolution + model-permission default).
- **Challenges.** C1/C3/C11 count 1-here for flavor arms, 0-here for
  spine bodies.
- **Owner + lifetime.** This file (the ModelForm-validation home;
  per-call snapshot, nothing stored beyond the sealed record).
- **Behavioral proof.** P4 (`execution-verified`) + matrix oracles
  `static-reviewed`.
- **Structural gate.** The delete-reject + plain-Form-redirect oracles
  fail a matrix weakening that lets a delete or a plain form through
  (the bind would materialize a `PARTIAL`-less shape or a model-less
  input through the model drain).
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [test-forms-sets][test-forms-sets] as in F3.

### R2 -- Plain-form `Meta` matrix (file-local)

- **Contract + variation.** Member 35's `_validate_meta`: ANY
  `Meta.operation` rejected FIRST by KEY PRESENCE (`hasattr`,
  MRO-visible — so an inherited `operation` from a shared `Meta`
  parent is rejected too, and explicit `None` does not slip through;
  Decision 10); unknown-key guard over the allowed set PLUS
  `{"operation"}` (no double-report); missing `form_class` presence;
  `forms.ModelForm` checked FIRST with the targeted redirect naming
  `DjangoModelFormMutation` (a bare `forms.Form` gate would
  mis-report a `ModelForm`, since both are siblings under
  `forms.BaseForm`); general `forms.Form` gate; narrowing fail-loud;
  `permission_classes` via `_validate_permission_classes` with
  `unset_default=(DenyAll,)` (deny-by-default, Decision 11); explicit
  `DjangoModelPermission`(+subclass) reject at class creation (it
  would crash at request time, not deny). Snapshot carries
  `model=None` + the `FORM` operation sentinel. Varies per arm (C2/C3
  count 1 here).
- **Sites + roles.** Definition here. Consumers: the plain metaclass,
  the plain drain, the plain pipeline. Oracles: the 66-suite's plain
  rows (P4 re-proved operation presence/`None`/inherited,
  ModelForm-first, non-Form, missing, unknown-key incl. the `model`
  key, model-permission reject, `DenyAll` default, `[]` opt-out).
- **Challenges.** C2 counts 1; C3 counts 1-here.
- **Owner + lifetime.** This file (the model-less-validation home;
  per-call snapshot, nothing stored beyond the sealed record).
- **Distinct behavior.** `DenyAll` default vs the model-backed
  `DjangoModelPermission` default — the model-less flavor cannot
  inherit a model-reading default (it would crash, not deny);
  recorded at the call site + the `DenyAll` docstring.
- **Behavioral proof.** P4 (`execution-verified`, 12 plain arms) +
  matrix oracles `static-reviewed`.
- **Structural gate.** The inherited-operation oracle
  (`test_plain_base_rejects_inherited_meta_operation`) fails a
  `vars(meta)`-only presence check (a shared-`Meta` parent carrying
  `operation` would finalize as if absent); the `DenyAll`-default
  oracle fails a default change that ships an open write surface.
- **Freshness.** Target as in F1;
  [mutations-permissions][mutations-permissions]
  `54f770ae5aa1238327246cd2dcb141e8aac14965`;
  [test-forms-sets][test-forms-sets] as in F3.

### R3 -- Declaration ledger + metaclass + model-less bind (file-local)

- **Contract + variation.** Members 15--19/34/36: the SECOND disjoint
  ledger from the shared factory (dedup / post-finalize reject /
  clear mechanics single-sourced, storage separate — Decision 13);
  the plain metaclass instance (validate-then-register lifecycle,
  abstract-base skip); `bind_form_mutations()` draining the plain
  ledger through the shared drain with `object_type=None`. Varies by
  ledger config (C4 counts 1-here for the declaration; mechanics 0
  here).
- **Sites + roles.** Definitions: the ledger instantiation + bound
  names + metaclass call + drain call here. Mechanics owners: the
  factory + drain in [mutations-sets][mutations-sets]. Consumers: the
  finalizer (`bind_form_mutations()` call, phase 2.5),
  `registry.clear()` (co-clear), `DjangoMutationField`, the tests
  introspecting `_form_mutation_registry`. Oracles: the ledger-split
  rows (P4 re-proved disjoint registration + idempotency shape +
  abstract-nowhere).
- **Challenges.** C4 counts 0-here/1-config.
- **Owner + lifetime.** Ledger + metaclass call here; mechanics
  upstream (principle 7). Lifetime: declarations recorded at class
  creation; drained per finalize pass; cleared from
  `registry.clear()`.
- **Behavioral proof.** P2 (disjointness) + P4 (split + abstract
  bases) (`execution-verified`) + bind oracles `static-reviewed`.
- **Structural gate.** `test_plain_form_registers_in_disjoint_form_registry`
  + `test_abstract_bases_register_nowhere` fail a ledger merge (a
  plain mutation landing in the model drain would resolve a primary
  it must never have) or a metaclass skip-drop.
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [finalizer][finalizer] as in F3.

### R4 -- Per-shape build cache + guard-before-cache (file-local)

- **Contract + variation.** Member 21 (cache pair) + member 25: the
  4-component shape key (`form_class`, `operation_kind`, effective
  frozenset, basis content identity) through `cached_build_input` —
  the guard runs PER declaration BEFORE the cache lookup (the key
  excludes `guard_required`, Decision 7), so a waiving mutation that
  materializes first cannot suppress a later non-waiving guard; the
  create path routes through `build_form_inputs` with
  `guard_required=False` (already guarded), `PARTIAL` builds the
  partial directly (never create-guarded — model-backed fields widen
  optional). Returns the `(input_cls, field_specs)` pair so the
  reverse map survives the dedupe. Varies on key assembly (C5 counts
  1-here) and the per-flavor `operation_kind`/`base` args (C-counts
  with R6).
- **Sites + roles.** Definitions: the pair instantiation + key tuple
  + guard/build closures here. Owners: `cached_build_input` +
  `make_shape_build_cache` + the identity projection upstream.
  Consumers: both flavors' `build_input` via member 31. Oracles: the
  dedupe/guard rows (P2-adjacent: shared-hook siblings dedupe,
  stateful-hook drift stays loud; guard-per-declaration row
  `static-reviewed`).
- **Challenges.** C5 counts 0-here/1-assembly; C6 counts 0 here.
- **Owner + lifetime.** Assembly here; ordering + projection
  upstream. Lifetime: per-pass cache cleared at drain top +
  co-cleared from `registry.clear()` (a `registry.clear()`-only
  reset, NOT a pre-bind input clear — recorded at the pair comment).
- **Behavioral proof.** Static-reviewed against the bodies + the
  `cached_build_input` ordering contract; dedupe/guard oracles pin
  both directions.
- **Structural gate.** The guard-per-declaration oracle fails an
  ordering change that guards only on cache miss (a waiving-first
  sequence would bless an unvalidatable schema); the stateful-hook
  loudness oracle fails a key-axis drop (content-different bases
  collapsing onto one class).
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [forms-inputs][forms-inputs] as in F1.

### R5 -- Shared validation helpers (file-local)

- **Contract + variation.** Members 26/27: member 26 routes effective
  names through `resolve_effective_form_fields` so `_validate_meta`
  never re-spells the narrowing walk; member 27 shape-normalizes via
  `normalize_meta_field_selection` then fail-loud-validates, storing
  the normalized pair for the bind to re-resolve. Varies only in the
  routing (C-counts 0-here for spine bodies).
- **Sites + roles.** Definitions: the two wrappers here. Spine owners:
  [forms-inputs][forms-inputs] / [utils-inputs][utils-inputs].
  Consumers: both `_validate_meta` matrices + both name tails.
  Oracles: unknown-name / empty-set / mutual-exclusion rows.
- **Challenges.** Spine changes count 0 here.
- **Owner + lifetime.** Wrappers here; walks upstream. Nothing stored
  (the snapshot stores the normalized pair; the walk itself is pure).
- **Behavioral proof.** P3 (routing by name) (`execution-verified`)
  + narrowing oracles `static-reviewed`.
- **Structural gate.** The unknown-name oracle
  (`test_modelform_unknown_field_name_routes_through_slice1_narrowing`)
  fails a re-spelled walk that diverges from the generator's
  effective set.
- **Freshness.** Target as in F1; [forms-inputs][forms-inputs] as in
  F1; [utils-inputs][utils-inputs] as in F1.

### R6 -- Twin-shared build + name tails (file-local)

- **Contract + variation.** Members 31/32: member 31 builds +
  materializes via `build_and_stash_input` (materialize into
  `forms.inputs`, stash `field_specs` as `_input_field_specs`;
  `specs_of` is identity — the form payload IS the specs list) with
  the per-flavor `operation_kind` (`CREATE`/`PARTIAL` for ModelForm
  via `NON_DELETE_OPERATION_INPUT_KIND`, `FORM` sentinel for plain)
  and waiver `base`; member 32 derives the generated name via
  `form_input_type_name` over the same effective set + full basis,
  single-sited with the bind's name choice. Varies per flavor args
  (1 here); tail bodies 0 here.
- **Sites + roles.** Definitions: the two tails here (differing only
  by injected args). Tail owners: [mutations-sets][mutations-sets];
  generator/naming owners in [forms-inputs][forms-inputs]. Consumers:
  both flavors' `build_input` / `input_type_name` seams. Oracles: the
  bind-materialize rows + `test_input_type_name_seams` (P4 proves the
  seam side is a pure delegation).
- **Challenges.** Flavor-arg changes count 1 here; tail-body changes
  count 0 here.
- **Owner + lifetime.** Tails here; bodies upstream. Nothing stored
  (per-call build; the stash lands on the mutation class via the
  shared tail).
- **Behavioral proof.** P3 (routing) + P4 (naming purity)
  (`execution-verified`) + bind oracles `static-reviewed`.
- **Structural gate.** `test_input_type_name_seams` fails a name-tail
  drift from the bind's materialize name (the lazy `data:` ref would
  point at a class the bind never pinned).
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [forms-inputs][forms-inputs] as in F1;
  [mutations-operations][mutations-operations]
  `16223c6b8a477bec61da690d08f1c1a01125d8ec`.

### R7 -- Construction-hook machinery (file-local)

- **Contract + variation.** Members 23/24/28/29/30: member 23 reads
  the frozen `_mutation_meta` snapshot when stamped, else the live
  `Meta` (validation runs before the stamp, so the one validation
  window reads the live declaration; every later call uses the
  frozen class — a post-declaration `Meta` mutation cannot change
  the shape); member 24 is the single typed hook-invocation boundary
  (non-callable / raising hook → `ConfigurationError`, mirroring the
  inputs-side `BaseException` catch; a hook-body `ConfigurationError`
  re-raises unchanged); member 28 detects an override of EITHER hook
  via the shared `_hook_overridden` identity check (the coarse
  Decision-7 waiver, caveat recorded at its docstring: an override
  taken for an unrelated reason while narrowing a required field
  re-opens the hole — the spec accepts the trust); members 29/30 are
  the single-sourced default bodies (29 via `construction_kwargs`:
  `instance` only on update; 30 as `form_class(**get_form_kwargs())`).
  Varies per default/waiver/boundary (C7/C8 count 1 here).
- **Sites + roles.** Definitions here (all five). Hook owners: the
  consumers' overrides; identity primitive + kwargs clause upstream.
  Consumers: both flavors' `get_form_fields` / `get_form_kwargs` /
  `get_form` assignments + member 31's waiver arg + the resolver's
  construction calls. Oracles: frozen-snapshot, hook-boundary (5
  rows), waiver (2 rows), guard-basis rows (P4 re-proved waiver
  detection both directions).
- **Challenges.** C7/C8 count 1 here.
- **Owner + lifetime.** This file (the hook home; per-call reads and
  constructions, nothing stored).
- **Distinct behavior.** The documented coarse-waiver caveat
  (Decision 7) — recorded at member 28's docstring, not re-argued
  here.
- **Behavioral proof.** P4 (`execution-verified`) + hook oracles
  `static-reviewed`.
- **Structural gate.** The non-callable-hook + raising-body oracles
  fail a boundary removal (a hostile hook would escape as a raw
  `TypeError` instead of the typed error every neighboring hook
  rejection raises); the waiver-trip oracle fails a detection change
  that guards waived shapes.
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [forms-inputs][forms-inputs] as in F1.

### R8 -- `Meta` key sets + input namespace (file-local)

- **Contract + variation.** Members 13/14: the ModelForm flavor keeps
  `operation` + `select_for_update` (model-backed writes —
  `MODEL_BACKED_WRITE_META_KEYS`); the plain flavor drops them
  (model-less, Decision 10 — `COMMON_WRITE_META_KEYS`); both add
  exactly `form_class`. The form-input namespace
  (`FORMS_INPUTS_MODULE_PATH` re-export, member 12) is carried as
  `input_module_path` on BOTH bases so the lazy `data:` ref resolves
  the form-derived input, never a model-column input. Varies per set
  (C10/C11 count 1-here for the local `form_class` arm + namespace
  binding; foundations 0 here).
- **Sites + roles.** Definitions: the two unions + two namespace
  bindings here. Foundation owners: [mutations-sets][mutations-sets];
  path owner in [forms-inputs][forms-inputs]. Consumers: both
  `_validate_meta` typo guards + the field factory's lazy ref.
  Oracles: known-key acceptance rows + namespace materialize rows.
- **Challenges.** C10 counts 0-here/1-decision; C11 counts 1-here for
  the local arm.
- **Owner + lifetime.** Sets + bindings here; foundations + path
  upstream. Nothing stored (frozensets read per validation).
- **Behavioral proof.** P2 (composition shape) (`execution-verified`)
  + key/namespace oracles `static-reviewed`.
- **Structural gate.** The known-key rows
  (`test_modelform_form_class_accepted_as_known_key`,
  `test_plain_form_class_accepted_as_known_key`) fail a set change
  that drops `form_class` (every declaration would typo-reject).
- **Freshness.** Target as in F1; [mutations-sets][mutations-sets] as
  in F1; [forms-inputs][forms-inputs] as in F1.

### R-auth -- Plain write-auth seam + write hook (file-local, R2/R7-adjacent)

Recorded under R2 (permission defaults) and R7 (hook shape) with no
separate count: `check_permission` mirrors the `036` default over the
shared `run_permission_classes` body (C9 counts 0-here/1-presence —
the seam must exist because the plain flavor is not a
`DjangoMutation` subclass, Decision 6); `perform_mutate` defaults to
`form.save()`-when-present else no-op, overridable for the model-less
side effect, wrapped by the pipeline's `save_or_field_errors`
(contract at [forms-resolvers][forms-resolvers]). Oracles:
`test_plain_form_check_permission_seam` +
`test_plain_form_default_perform_mutate_calls_form_save`
`static-reviewed`. No separate family, no separate challenge axis —
the walk is F-shared (owner upstream), the hook is R7-shaped.

### J1 -- Single base with a mode flag (rejection, considered fresh)

One `FormMutation` base with `model_backed: bool` (or an
`operation=None`-means-plain rule) instead of the two bases.
REJECTED: every seam forks on the mode — metaclass/ledger/bind
(model registry + primary payload vs disjoint ledger + `{ ok
errors }`), operation vocabulary (require vs reject), permission
default (`DjangoModelPermission` vs `DenyAll` + the model-permission
reject), resolver signature (`with_id` vs not), snapshot shape
(`model` + `select_for_update` vs `None` + sentinel). A flag saves
zero change obligations (C1/C2/C3 each still move one arm) and buys
a branch at every consumer. Trigger: a third flavor sharing one side
of every fork. Home: the module docstring (two-base split) + this
clause.

### J2 -- Merged `_validate_meta` (rejection, considered fresh)

One parametrized matrix (`_validate_meta(meta, *, model_backed)`)
instead of the two overrides. REJECTED: disjoint key sets
(`operation`/`select_for_update`/`model` vs none), opposite
operation rules (require-membership vs reject-presence), opposite
permission defaults, opposite `ModelForm` gate direction (require vs
redirect-reject). The shared arms already ARE shared (R5 helpers +
all spine validators); what remains differs per arm. Trigger: an arm
whose rule becomes flavor-independent. Home: both `_validate_meta`
docstrings (disjoint matrices) + this clause.

### J3 -- Set-family naming unification (rejection CONFIRMED, re-derived fresh)

Name form inputs via
[sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin.type_name_for`.
REJECTED again from this side (never inherited from the sets_mixins
item): write inputs derive from a form class + operation kind (or the
mutation shape descriptor), never from a set class; unifying needs a
from-what mode flag. Difference + trigger + home as in that item's
R2 (homes: `::_form_input_type_name_for`,
`::DjangoMutation.input_type_name`, and the rest-framework twin).
No index change proposed.

### J4 -- Heavy `_lifecycle` on write flavors (rejection CONFIRMED, re-derived fresh)

Put every write family on `SetLifecycleAttrs` + factory caches.
REJECTED again from this side: write flavors derive inputs from one
declaration's field set (no BFS graph, no lazy targets, no per-set
expansion cache), so there is nothing to reset beyond the ledger +
per-pass build cache; the light-clear rationale is cross-referenced
by all three write `inputs` modules (P2 step 8: no set-family
substrate in any write flavor). Difference + trigger + home as in
that item's R3 (home: `::make_input_namespace` light-clear
docstring). Trigger: a write flavor gaining lazy related-set graph
expansion. No index change proposed.

### J5 -- Plain flavor on `DjangoMutation` (rejection, considered fresh)

Make `DjangoFormMutation` a `DjangoMutation` subclass with
`model=None`. REJECTED: the base contract is model-backed
(`_resolve_model` → `Meta.model`, `build_input` → model columns,
bind → primary payload, `DjangoModelPermission` default) — a
`None`-model subclass would carry every model seam as dead weight
plus `None`-guards, while still needing its own ledger (Decision 13
disjointness), its own operation reject, and its own payload shape.
The inheritance already present is exactly the shareable part (the
ModelForm flavor IS the subclass). Trigger: a model-backed behavior
the plain flavor must inherit rather than mirror. Home: the plain
class docstring (model-LESS clause) + this clause.

## Defects

None. Two investigated edges released without a defect:

1. The plain `_validate_meta` docstring lists the `operation` reject
   twice (the FIRST-presence bullet and a later outright-reject
   bullet restating the same rule). Single-docstring restatement, no
   second maintained copy, no accepted shape changes either way —
   cosmetic, not a contract break.
2. The module header's "`resolve_*` -> the form pipeline" compresses
   the sync+async seam pair (owned by the `resolver_seams` factory).
   The per-flavor seam sites state the pair precisely (incl.
   `with_id=False`) — projection wording, no behavior. Cosmetic, not
   filed.

Nothing routed to any owner.

## Pending execution

None. All five probes already ran green against the shared tree; each
is read-only (AST/text census + pure calls + in-memory form instances
+ class-creation validation only; no source mutation, no database —
P4/P5 run with empty `DATABASES`, the Group model class is read never
queried, and P4 removes every test class from both registry stores by
identity, verified empty after). No pytest was run in the shared tree,
per item rules; oracle bodies are `static-reviewed`. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells are
`inapplicable by construction`: the target's code path reaches no
database, alias, or dialect decision (P4/P5 prove it by running with
no database configured).

## Judgment

Backstop discharged: 36/36 `ast.Module.body` members enumerated (11
module helpers + 2 bases with P3-pinned 11/16 members + ledger +
metaclass + bind fully assigned), 17 challenges run (C1--C17, every
variation axis of every rule), six matrix axes discharged against the
real surface (model twin + serializer mirror read whole FIRST;
sharing proved by behavior counts, not tokens; round-trips verified
in both directions; sync/async absence verified by instrument, not
assumed), eight file-local records with proving challenges (R1--R8 +
R-auth adjacency), three families reused-as-contributor/consumer/rider
(F1/F2/F3, re-derived fresh) plus nine checked non-memberships
(F4--F12), five rejections with difference + trigger + home (J1/J2/J5
considered fresh, J3/J4 re-derived fresh, no index changes: the plan
rows already cover their files). Zero defects, zero pending. The
target owns its rules singly: two disjoint matrices, one ledger, one
cache assembly, one hook suite, one key-set pair, with every shareable
mechanism composed by name from the model foundation. Zero-edit result
is legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
fd8c06a24bd1bca8726ad9a87ea7826b78c02357 --
django_strawberry_framework/forms/sets.py` is empty for the target
(working blob `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25` equals the
item baseline member and `HEAD:` — target CLEAN, so no hunk
attribution was owed); the artifact itself is this new file
(`docs/dry/dry-file-forms__sets.md`, untracked until Worker 0 records
it). The `## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never
touched. Concurrent dirt (the `connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
in-flight `filters/inputs.py` range hunk +
`tests/filters/test_inputs.py` companion,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, plus the
further working-tree dirt in `git status --short` at run time) was
never edited, reverted, or tidied, verified by content-diff scoping
(the item-scoped diff shows no entry before and after). Scratch
(untracked, kept for Worker 2 re-run):
`docs/dry/temp-tests/dry-file-forms__sets/p1_ast_census.py`,
`p2_write_mirror.py`, `p3_form_twins.py`, `p4_behavior.py`,
`p5_bus.py` — all read-only, all green. Concurrent edit observed and
left untouched: `django_strawberry_framework/filters/inputs.py`
worktree hunk confined to `_normalize_range_value` (range-shape
fail-loud hardening) plus `tests/filters/test_inputs.py` — no site
this item depends on changed (the target imports nothing from
`filters/inputs.py`; P1-adjacent census: zero `filters` code
references outside comments), so the finding set is robust to both
versions of the hunk. Target blob re-hashed after the final probe
run: `36ce80b4` unchanged (read-only as claimed). No `ruff` run owed
(no tracked edits). No pytest run (not authorized by the entry
command). Do not commit.

## Independent verification (Worker 2)

Own trace, derived from the target + the mirror read FIRST
(whole [mutations-sets][mutations-sets], 61 members, 0 async;
whole [rf-sets][rf-sets], 21 members; owners, bus, build/decode
sides; oracles; spec-038 Decisions 6/7/10/11/13). Counts are
authoritative definitions per posited change; consumers, oracles,
projections move along, never counted.

- **Clear registrations.** Two bus registrations
  (`forms.declarations`, `forms.shape_cache`), ledger + cache
  declared here, mechanics upstream. A lifecycle-slot change
  counts 0 here (bus + factory owners), disjointness config 1
  here. Owners I choose: bus + factories upstream, config here.
  Matches F1 (contributor). Agree.
- **Seal, both flavors, metaclass non-fork.** Slot seal via the
  shared record class, head seal via the same factory; the plain
  metaclass is a second INSTANCE over a disjoint ledger, seal
  source identical (P4 re-ran: rebind + delete raise on both
  heads; write + delete raise on the snapshot). Reword counts 0
  here. Owners upstream. Matches F2 (consumer). Agree.
- **Skeleton rider.** One drain (`bind_write_declarations`,
  plain call injects `resolve_object_type=None` + the form
  cache), `resolver_seams` twice (`with_id=False` only plain),
  entry factory taken as product; finalizer calls
  `bind_mutations()` then `bind_form_mutations()` in phase 2.5.
  Drain/boundary changes 0 here; a flavor branch 1 here.
  Owners upstream. Matches F3 (rider). Agree.
- **Matrices.** Two disjoint `_validate_meta` bodies: ModelForm
  (unknown-key guard, presence, `ModelForm` gate before model
  resolution, `require_model_class`, `create`/`update` only,
  narrowing, model-permission default + lock) vs plain
  (presence-reject of ANY `Meta.operation` via `hasattr`,
  unknown-key guard, `ModelForm`-first redirect, `Form` gate,
  narrowing, `DenyAll` default + model-permission reject,
  `model=None` + `FORM` sentinel). Per-arm changes 1 here,
  spine bodies 0 here. Owners here. Matches R1/R2. Agree.
- **Ledger + plain metaclass + bind.** Second disjoint ledger
  (1 factory call per side, no code-level cross-reads), 1
  metaclass factory call here, drain call here. Config 1 here,
  mechanics 0 here. Matches R3. Agree.
- **Shape key + guard ordering.** 4-component key assembled here
  (identity projection upstream), guard-per-declaration before
  cache lookup via `cached_build_input`. Key assembly 1 here,
  ordering 0 here. Matches R4. Agree.
- **Narrowing/selection wrappers.** Two thin routers here,
  walks upstream. 0 here. Matches R5. Agree.
- **Build + name tails.** Two tails differing only by injected
  `operation_kind` + waiver `base`; bodies upstream. Flavor
  args 1 here. Matches R6. Agree. (Import-site note: all 23
  `mutations.sets` imports resolve upstream; 22 defined there,
  `NON_DELETE_OPERATION_INPUT_KIND` defined in
  [mutations-operations][mutations-operations] and re-exported
  through the sets module, whose true owner R6 fingerprints.)
- **Hook machinery.** Frozen-snapshot default hook, typed
  invocation boundary, `_hook_overridden` waiver detection,
  two shared default bodies (kwargs clause via
  `construction_kwargs`). 1 here. Matches R7. Agree.
- **Key-set pair + namespace.** Two frozenset unions here
  (`form_class` the only local arm), namespace binding here,
  foundations + path upstream. Local arm 1 here. Matches R8
  (+ R-auth adjacency: seam presence 1 here, walk 0 here).
  Agree.

### Enumeration (member-by-member vs own count)

Own instrument: `ast` over `ast.Module.body` = **36** (docstring
+ 11 imports + 2 key sets + 5 ledger bindings + 2 bus
registrations + 1 cache pair + 10 helpers + 2 classes +
1 metaclass + 1 bind). Classes: ModelForm **11**, plain **16**
(P3 re-ran, member names match). Module functions **11**
(10 helpers + bind). Imports **11**. `AsyncFunctionDef` **0**,
`await` **0**. Every row 1--36 lands where W1 puts it; no
member unassigned, none double-counted. The 23-name spine
import is fully referenced (P2 re-ran 23/23). Oracle census:
66 top-level `test_` functions (71 top-level defs total),
matching the claimed 66-suite. Agree on all counts.

### Counts, roles, oracles

Definition counts C1--C17 reproduce mine exactly (0-here for
upstream bodies, 1-here for local arms/config, refused for
C13--C17). Roles confirmed: target defines matrices /
ledger-config / key-assembly / tails-args / hooks / key-sets
and consumes every shared mechanism by name. No oracle
rewritten to read its owner: spot-checked oracles spell
literals (`ItemModelFormInput`, `operation is not supported`,
`DenyAll` identity, dedupe identity) and read only behavior
(ledger contents, stash state, sealed raises); the two
`_form_basis_content_identity` mentions are comments, the
`_materialized_names` reads assert materialization behavior,
never derive expectations from an owner table.

### Equivalence (principle 8)

Zero production edits, so the obligation is that every
behavioral claim holds: P1--P5 re-ran green read-only from
the shared tree (no source mutation, so no workspace copy
owed; P4/P5 with empty `DATABASES`, Group class read never
queried). Matrix arms, both seals on both flavors, waiver
both directions, naming purity, registry split, bus
disjointness all execution-verified; bind/materialize rows
static-reviewed honestly. No happy-input-only agreement:
guard ordering, inherited-`Meta.operation`, stateful-hook
loudness each pin a failing direction.

### Zero-edit + family routing

`git diff fd8c06a24bd1bca8726ad9a87ea7826b78c02357 --
django_strawberry_framework/forms/sets.py` is empty (re-run);
target blob `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`
equals baseline and `HEAD:`; file absent from `git status`.
36/36 assigned, 17 challenges run, strongest rejections carry
difference + trigger + home. Reuse routing confirmed:
clear-contributor (F1), seal-consumer (F2), skeleton-rider
(F3). Withholdings judged one by one, all correct: naming
(F4, form class + kind vs set class), target-lifecycle (F5,
no lazy graph), declaration-collection (F6, single `Meta`
per class), expansion-skeleton (F7, cross-declaration dedupe
vs publish-once), cache-write-gate (F8, guard-skip vs
resolution predicate), re-readable gate (F9, ridden walk),
permission-facade (F10, write seam vs read facade),
model-type-map (F11, resolution inside the ridden drain),
converter-table (F12, no table, no convert call). A file item
owes no production edit; none demanded.

### Rejections, fingerprints, gates, pending, coupling

J1--J5 each carry contract difference + trigger + durable
home; J3/J4 re-derived from this side, no index change owed.
All five rejections sustained (J1 every seam forks; J2
disjoint keys + opposite operation/permission rules with
shared arms already shared; J3 different source domains; J4
nothing to reset; J5 dead-weight model seams).

Fingerprint re-hash at `HEAD 9031cb3d` (working = `HEAD:` for
all): target, mutations-sets, registry, utils-inputs,
forms-inputs, rf-sets, auth-mutations, mutations-permissions
all match; the two short prefixes expand correctly
(`9cef2100fcb7` -> `9cef2100fcb72adef7fd214deef91179a66cddde`,
`6390492979ef` ->
`6390492979efe8ee6f9268a355b1f75404bbdbc6`). **Four
mismatches, all invalid git objects (transcription, not
drift; files clean):** finalizer claims
`77fd9a2d…94d411…`, actual
`77fd9a2dd229eb9de5f29188c5058035d3606323`;
test-forms-sets claims `5c3b964c…bd9d0`, actual
`5c3b964c20306f56b6cc8a99e860b4d104f28ed7`;
test-mutations-sets claims `2dc45288…492b9`, actual
`2dc45288a616137283bac8504ca072e33218b21e`;
mutations-operations claims `16223c6b…372ee88`, actual
`16223c6b8a477bec61da690d08f1c1a01125d8ec`.
Affects F3 + R6 (R1--R3 inherit via `as in F3`). See
D-W2-1; verdict follows it.

Gates: every finding names its failing oracle + the bypass
it breaks (inherited-operation vs `vars(meta)`-only,
`DenyAll` default vs open surface, guard-per-declaration vs
miss-only guard, stateful-hook loudness vs dropped key axis,
ledger-split vs merged drain, name-seam vs drifted bind
name). Failability is argued statically, not executed via a
mutating prover: acceptable for a zero-edit file item with
no new gate (execution belongs to the family items + final
gate); statuses honestly recorded. `## Pending execution`
correctly absent: all probes ran green, none deferred;
`FAKESHOP_SHARDED=1`/Postgres inapplicable by construction
(probes prove no database, alias, or dialect in the path).
Coupling correctly none.

### AGENTS.md prose check

No `path:NN` citations (scan: zero); `path::Symbol` form
with the bottom link block (10 canonical groups present);
no process provenance (`token(s)` hits are DRY vocabulary);
no new tests owed by a zero-edit file item (oracles at the
`tests/` library tier, literals spelled); no ruff/pytest owed
(no tracked edits; runs not authorized). The two cosmetic
edges W1 released (double-listed `operation` bullet,
compressed `resolve_*` header) stay released: single-medium
restatements, no accepted shape changes either way. Pass.

### Concurrent dirt

Untouched. In-flight `filters/inputs.py` hunk confirmed
independent: confined to `_normalize_range_value`
(range-shape fail-loud hardening + companion test); target
carries zero `filters` references at code or comment level,
so the finding set is robust to both versions. All other
`git status` dirt (connection, resource-policy, filters
sets, bug-hunt artifact, plan, staged querysets test) never
opened.

## Defects (Worker 2)

- **D-W2-1 (record defect, revision driver).** Four
  freshness fingerprints in `## Findings` are invalid git
  objects: F3 finalizer / test-forms-sets /
  test-mutations-sets, R6 mutations-operations (correct
  values under `## Independent verification (Worker 2)`
  "Rejections, fingerprints, gates, pending, coupling").
  Owner: this item (Worker 1 strings-only re-pass, no
  re-trace, no production edit). Non-blocking note: expand
  the two F2 short prefixes to the full hashes above for
  comparability.

## Judgment (Worker 2)

Everything verifies except the record: ownership, counts,
roles, matrix, withholdings, rejections, gates, pending,
prose, and independence all agree with zero differences;
the four bad fingerprints make F3/R6 (and their `as in`
dependents) uncomparable as written. `Status:
revision-needed`, scope strings-only; resubmission returns
to this trace. Do not commit.

Pass-2 note (Worker 2): re-hashed all six fingerprinted files
myself at unchanged `HEAD 9031cb3d` (working = `HEAD:`);
all four corrected literals match byte-for-byte, both F2
prefixes expanded to full, zero bad-string occurrences, my
sections untouched, F3/R6 freshness lines confirmed carrying
the corrected values, item-scoped diff still empty, target
blob unchanged, concurrent dirt preserved. D-W2-1 closed.
`Status: verified`. No pending execution. Do not commit.

## Iterations (pass 2)

Strings-only pass per D-W2-1: replaced four transcribed freshness fingerprints with Worker 0's `git hash-object` values (finalizer `77fd9a2d…` to `77fd9a2dd229eb9de5f29188c5058035d3606323`, test-forms-sets `5c3b964c…` to `5c3b964c20306f56b6cc8a99e860b4d104f28ed7`, test-mutations-sets `2dc45288…` to `2dc45288a616137283bac8504ca072e33218b21e`, mutations-operations `16223c6b…` to `16223c6b8a477bec61da690d08f1c1a01125d8ec`) and expanded the two F2 short prefixes to full; no production edits, no re-trace.

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
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-permissions]: ../../django_strawberry_framework/mutations/permissions.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-forms-sets]: ../../tests/forms/test_sets.py
[test-mutations-permissions]: ../../tests/mutations/test_permissions.py
[test-mutations-sets]: ../../tests/mutations/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
