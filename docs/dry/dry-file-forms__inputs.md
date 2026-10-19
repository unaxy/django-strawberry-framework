# DRY review: `forms/inputs.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a reused family row (re-derived fresh, never inherited), a
file-local record with its proving challenge, or a recorded rejection with
contract difference + trigger + durable home. Zero production edits; zero
tracked files changed.

## System trace

Small target (`django_strawberry_framework/forms/inputs.py`, 914 lines, blob
`55614839ff479b3610b6026be65f2107ee560fcd`; absent from
`git status --short`, target CLEAN): the form-derived `@strawberry.input`
generation substrate (spec-038 Decision 7). It DEFINES the form operation-kind
vocabulary (`FORM` sentinel + `CREATE_SHAPED_KINDS` + the out-of-vocabulary
raises), the field-basis discovery + validation (`get_form_fields` /
`_form_field_basis` / `normalize_form_field_basis`), the shape-identity content
projection (`_related_model_of` / `_form_basis_content_identity`), the
backing-column resolution (`_model_column_for`), the per-field triple dispatch
(`_model_less_relation_annotation` / `_simple_triple` /
`_field_triple_and_spec`, constructing the single `InputFieldSpec` site), the
collision guard (`_guard_input_attr_collisions`), the single generator
(`build_form_input_class` with the partial-widening rule), the required-set +
create/partial guards (`_required_form_field_names` /
`guard_create_required_fields` /
`guard_partial_required_column_less_fields`), the pair builder
(`build_form_inputs`), and the thin narrowing + naming wrappers
(`resolve_effective_form_fields` / `form_input_type_name`). It CONTRIBUTES the
form ledger declaration + thin wrappers + registration to the
`subsystem-clear-lifecycle` family. It CONSUMES (by name, P3-proved) the shared
spines in [utils/inputs.py][utils-inputs] (`make_input_namespace`,
`resolve_effective_fields`, `name_set_input_type_name`,
`guard_dropped_required`, `iter_input_field_collisions`,
`optional_input_field`, `build_strawberry_input_class`, `InputFieldSpec`,
the kind vocabulary), the column spine in
[mutations/inputs.py][mutations-inputs] (`CREATE` / `PARTIAL`,
`model_column_input_annotation`, `model_column_write_kind`,
`annotate_queryset_relation`), the model-less table + requiredness in
[forms/converter.py][forms-converter] (`convert_form_field`,
`form_field_required`), the relation predicates in
[utils/relations.py][utils-relations] (`is_forward_concrete_relation`,
`is_forward_many_to_many`), and `graphql_camel_name` in
[utils/strings.py][utils-strings].

Connected code read for judgment, outside the item: the orders twin FIRST
(whole [orders/inputs.py][orders-inputs], 395 lines) + the filters twin
([filters/inputs.py][filters-inputs], whole read earlier this cycle via its
verified artifact) + the serializer mirror ([rf-inputs.py][rf-inputs] guard /
narrowing / namespace regions); the owners ([utils/inputs.py][utils-inputs]
full read, [mutations/inputs.py][mutations-inputs] full read,
[forms/converter.py][forms-converter] full read via its verified artifact);
the decode consumer ([forms/resolvers.py][forms-resolvers] spec regions:
`spec.target_name` routing, `InputFieldSpec.related_model` at build) + the
bind consumer ([forms/sets.py][forms-sets] full read:
`_cached_build_form_input`, `_build_and_stash_form_input`,
`_form_input_type_name_for`); the bus ([registry.py][registry]
`register_subsystem_clear` / `iter_subsystem_clears` regions); oracles in
[test-forms-inputs.py][test-forms-inputs] (whole inventory),
[test-forms-sets.py][test-forms-sets] (ledger + dedupe regions),
[test-forms-resolvers.py][test-forms-resolvers] (decode regions),
[test-forms-converter.py][test-forms-converter] (table regions, via its
artifact); contract source spec-038 Decision 7 (form-is-source-of-truth,
fail-loud shape, key-space separation); projection
[forms-init.py][forms-init] (subsystem prose).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P5, all
read-only, all green; commands under `### Challenges`).

1. **Cross-flavor policy mirroring.** Searched, twins read FIRST whole.
P2 proves the namespace split: forms / mutations / serializer ride the LIGHT
`make_input_namespace` trio (3-tuple unpack each); filters / orders ride the
HEAVY `make_set_input_namespace` quartet (4-tuple each) — the documented
light-vs-heavy divergence (filters artifact R-g), not a twinship. Six
disjoint `register_subsystem_clear` owners on the bus (P2 census:
`forms.input_namespace` exactly once with `before_bind=True`, plus
mutations / rest_framework(.input_namespace + .shape_cache) / filters /
orders). Guards compared by behavior: form create/partial guards share only
the `guard_dropped_required` arithmetic with the serializer twin; the
required-SET derivations differ (form: converter requiredness + column
presence; serializer: explicit-injection subtraction) — intentional
separation (J3). Collision policy differs by documented contract (form
raises on FIRST message, serializer aggregates) — intentional (R7). Naming:
form `operation_kind == PARTIAL` vs model `operation_kind != CREATE` is the
`FORM`-sentinel consequence, one local decision (R4). What SHOULD be shared
already is: the namespace mechanics, the narrowing spine, the naming spine,
the guard arithmetic, the collision walk, the widening tail, the column
spine, the converter table, the kind vocabulary, the reverse-map record —
every one composed by name (P3: 20/20 imports referenced at or above
minimum). Verdict: one rule per surface; see R1--R9, J1--J4.
2. **Sync/async twins.** Discharged inapplicable by construction. Instrument
(P1): zero `AsyncFunctionDef`, zero `await` in the target; no
`base_queryset` / `model_for` / `run_in_one_sync_boundary` / `sync_to_async`
definition or call. Construction runs at finalize time over in-memory field
objects: `_related_model_of` reads `field.queryset.model` (attribute read,
no query execution); `_model_column_for` reads `_meta` only. The sync/async
form-resolver pipeline ([forms/resolvers.py][forms-resolvers]) consumes the
built input + specs; it does not re-implement any rule here, so there is no
colored twin to compare.
3. **Derived rather than repeated knowledge.** Searched. `INPUTS_MODULE_PATH`
pinned once, read by the namespace construction (P1 assign census). Type
names derived via `name_set_input_type_name` (P3: 1 ref, the wrapper owns
only the `is_partial` decision). `CREATE_SHAPED_KINDS` derives from the
imported `CREATE` + local `FORM` (P3: `CREATE` 1 Name ref, inside the
frozenset). The `_form_basis_content_identity` projection reads
`form_field_required` + `_model_column_for` + `_related_model_of` by name —
the SAME resolution the build site uses, so the projection cannot drift
from the build (R3). `InputFieldSpec` constructed at exactly one site
(P3: the 7 refs are the 1 construction + annotations). No fact re-derived.
4. **Inverse / round-trip pairs.** Searched, both directions verified. Encode
(field -> spec here, single construction) pairs with decode (spec ->
form-keyed payload in [forms/resolvers.py][forms-resolvers] via
`spec.target_name`, `spec.kind`, `spec.related_model` — resolver regions
read, no re-derivation of the related model from `base_fields`). Shape
identity triple (name via `form_input_type_name`, cache key via
`_form_basis_content_identity`, per-declaration guard via
`_cached_build_form_input` in [forms/sets.py][forms-sets]) composes the same
basis by name at all three sites. Narrowing (`resolve_effective_fields`
spine) pairs with drop-detection (`guard_dropped_required` spine) over the
same effective set. One grammar per pair, correctly separated halves.
5. **Contracts restated in another medium.** Counted 1 definition per rule;
everything else classified: module docstring (projection, clause-verified
incl. the `036`-discipline claims, the parked-globals pointer, the
`(form_class, kind, frozenset)` identity); [forms-init.py][forms-init]
subsystem prose (projection); spec-038 Decision 7 (contract source);
[test-forms-inputs.py][test-forms-inputs] rows (oracles spelling literals:
naming pins, required/optional shapes, id-type rows, `Upload` row,
read-side-enum row, narrowing fail-loud rows, guard rows, collision row,
basis rows — no oracle iterates an owner table; the module-path test pins
the literal path string); [test-forms-sets.py][test-forms-sets] ledger rows
(assert the clear empties the ledger and the namespaces stay disjoint —
behavior assertions, not table reads). No medium holds an independently
maintained copy of any rule.
6. **Enforcement by omission.** Family enumerated, each absence checked
against a contract source. Operation-kind coverage is total: every public
builder validates its vocabulary (`build_form_input_class` accepts
`CREATE_SHAPED_KINDS | {PARTIAL}`; `build_form_inputs` accepts
`CREATE_SHAPED_KINDS` only and always builds the partial itself) — P4
proved all three out-of-vocabulary shapes raise. Excluded unsupported
fields never convert: `_required_form_field_names` deliberately never calls
`convert_form_field` (oracle-pinned,
`test_excluded_unsupported_field_is_never_converted`) — not a gap.
`queryset is None` relation fields fail loud (typed, naming form + field),
never a bare `AttributeError` — not a gap. Exact-`NullBooleanField` forced
optional vs validating-subclass-keeps-requiredness rides the single
`form_field_required` decision on BOTH arms (converter artifact R4) — not a
gap. The `_lifecycle` / `describe_value` hits in the target are prose-only
(the absence statement; the failure-mode citation) — confirmed no
definitions (defscan + context print). No missing guard with a contract
source behind it — no defect filed.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-forms__inputs/p1_ast_census.py`), count **38**.
Every member lands below; R = file-local finding, F = reused family row
(non-membership checked, never inherited), J = recorded rejection.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | verified clause-by-clause |
| 2 | `from __future__` | machinery import | consumer |
| 3 | `import keyword` | guard import | R2 consumer |
| 4 | `typing.Any` | annotation import | consumer |
| 5 | `django.forms` | key-space import | R2/R6 consumer |
| 6 | `FieldDoesNotExist` | guard import | R5 consumer |
| 7 | exceptions import (5 names) | helper imports | R2/R5 consumers (F non-member, prose-only `describe_value` hit) |
| 8 | mutations.inputs import (5 names) | spine imports | R1 (`CREATE`/`PARTIAL`) + R6 (column spine) consumers |
| 9 | registry import (2 names) | bus imports | F1 consumers |
| 10 | `Upload` scalar | annotation import | R6 consumer |
| 11 | utils.inputs import (8 names) | spine imports | F1 + R4/R7/R8/R9 consumers (P3: all referenced) |
| 12 | utils.relations import (2 names) | predicate imports | R5 consumers (owners upstream) |
| 13 | `graphql_camel_name` import | naming import | R4/R6 consumer (F non-member: zero local defs) |
| 14 | converter import (5 names) | table imports | R6/R9 consumers (J1 member) |
| 15 | `INPUTS_MODULE_PATH` | namespace constant | F1 (REUSE contributor) |
| 16 | `FORM` | kind sentinel | R1 |
| 17 | `CREATE_SHAPED_KINDS` | kind set | R1 |
| 18 | namespace trio unpack | ledger declaration | F1 (REUSE contributor; owner product bindings) |
| 19 | `materialize_form_input_class` | thin wrapper | F1 (REUSE contributor) |
| 20 | `clear_form_input_namespace` | thin wrapper | F1 (REUSE contributor) |
| 21 | `register_subsystem_clear(...)` call | registration | F1 (REUSE contributor; `owner="forms.input_namespace"`, `before_bind=True`) |
| 22 | `get_form_fields` | discovery | R2 |
| 23 | `_form_field_basis` | basis + validation | R2 |
| 24 | `normalize_form_field_basis` | hook boundary | R2 |
| 25 | `_related_model_of` | projection helper | R3 |
| 26 | `_form_basis_content_identity` | content projection | R3 |
| 27 | `resolve_effective_form_fields` | narrowing wrapper | R4 |
| 28 | `form_input_type_name` | naming wrapper | R4 |
| 29 | `_model_column_for` | column resolution | R5 |
| 30 | `_model_less_relation_annotation` | relation wrapper | R6 |
| 31 | `_simple_triple` | naming helper | R6 (+ J2 member) |
| 32 | `_field_triple_and_spec` | per-field dispatch | R6 |
| 33 | `_guard_input_attr_collisions` | collision wrapper | R7 |
| 34 | `build_form_input_class` | single generator | R8 |
| 35 | `_required_form_field_names` | required set | R9 |
| 36 | `guard_create_required_fields` | create guard | R9 |
| 37 | `guard_partial_required_column_less_fields` | partial guard | R9 |
| 38 | `build_form_inputs` | pair builder | R8 |

No member unassigned. Prior-cycle trigger notes re-checked fresh, never
inherited: the converter item's R4 (requiredness) + R5 (value object) + kind
re-exports (this file consumes all three by name, P3); the filters item's
R-g light-vs-heavy split (P2 re-proves it from this side) and its F-reuse
rows below.

### Challenges

Authoritative definitions counted only; consumers, oracles, and projections
that move alongside are listed, not counted. Executed probes are read-only
files under `docs/dry/temp-tests/dry-file-forms__inputs/` run with
`uv run python` from the repo root; NO shared-tree pytest, NO source
mutation (so no workspace copy was owed), NO database opened by any probe
(P4/P5 run with empty `DATABASES`).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | add a 4th operation kind (or re-shape create-vs-partial) | **1** (this file: R1 sentinel + set + both vocab checks move together) | kind-spelling oracles, bind callers passing the kind |
| C2 | change the basis source or the name/value validation | **1** (R2) | hook invoker in sets.py, basis oracles |
| C3 | add a 5th shape-identity axis | **1** (R3 projection) | sets.py cache-key assembly, dedupe oracles |
| C4 | change the narrowing rule (exclusion, unknown-name, empty-set) | **0 here** (owner `resolve_effective_fields`); knob wording **1 here** | narrowing oracles |
| C5 | change the `Input`/`PartialInput` suffix or full-vs-narrowed rule | **0 here** (owner `name_set_input_type_name`); partial-decision **1 here** | naming oracles |
| C6 | change the reverse/GFK exclusion in column resolution | **1** (R5) | triple dispatch, required-set, identity projection (consumers) |
| C7 | change the Relay-vs-raw-pk id-type rule | **0 here** (owner `annotate_queryset_relation` spine); naming/missing-wording **1 here** | id-type oracles |
| C8 | change the column-vs-columnless routing or the `<name>_id` remap | **1** (R6 dispatch); a new field class **0 here** (converter table moves) | triple oracles, resolver decode |
| C9 | add a third collision arm | **0 here** (owner `iter_input_field_collisions`); wording/policy **1 here** | collision oracle |
| C10 | change the partial-widening rule (e.g. force extras optional too) | **1** (R8) | shape oracles |
| C11 | change the drop-detection arithmetic | **0 here** (owner `guard_dropped_required`); required-set filter **1 here** | guard oracles |
| C12 | add a namespace lifecycle slot | **0 here** (owner `make_input_namespace` / registry bus) | wrappers follow |
| C13 | unify the form partial rule with the serializer partial rule | **refused** (J3: disjoint populations, disjoint contracts) | -- |
| C14 | fold `_simple_triple` into the model scalar arm | **refused** (J2: different tuple shapes at different build sites) | -- |
| C15 | unify all converter tables into one map | **refused** (J1: four key spaces, four contracts) | -- |

Probe commands + what each proved (every probe `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-forms__inputs/p1_ast_census.py`
  -- 38 members, 0 async, 19 functions, 4 assigns, 13 imports (matrix axis 2
  + enumeration instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__inputs/p2_mirror.py`
  -- light trio in forms/mutations/serializer, heavy quartet in
  filters/orders; six disjoint clear owners, forms exactly once with
  `before_bind=True`. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__inputs/p3_delegation.py`
  -- 20/20 shared-spine imports referenced at or above minimum (incl.
  `form_field_required` x3, `PARTIAL` x4, `InputFieldSpec` x7,
  `graphql_camel_name` x2); ten indexed-machinery symbols have zero
  definitions here. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__inputs/p4_behavior.py`
  -- canonical vs deterministic narrowed names (`ContactFormNameInput`);
  create/partial shapes; three out-of-vocabulary raises; create + partial
  dropped-required raises; unknown/empty/mutual-exclusion raises; camel
  collision raises naming `fooBar`; keyword basis name raises typed.
  `execution-verified`, no database.
- `uv run python docs/dry/temp-tests/dry-file-forms__inputs/p5_clear.py`
  -- the forms clear is on the bus and in the pre-bind subset; ledger reset
  empties the dict without touching parked globals. `execution-verified`,
  no database.
- Defscan (inline): none of `type_name_for` / `make_dynamic_set_getter` /
  `GeneratedInputArgumentsFactory` / `_permission` / `model_for` /
  `base_queryset` / `run_in_one_sync_boundary` / `register_subsystem_clear`
  / `get_filterset_class` / `Ordering` / `_ensure_field_specs` is DEFINED
  in the target (registration is call-only). `execution-verified`.

## Findings

### F1 -- `subsystem-clear-lifecycle` (REUSE, index: open)

- **Contract + variation.** Every subsystem reset rides the registry bus;
  generated-input namespaces reset ledgers only, never parked module
  globals. Varies by adding a lifecycle slot (C12 counts 0 here).
- **Sites + roles.** Owners: [registry.py][registry]`::register_subsystem_clear`
  (bus) + [utils/inputs.py][utils-inputs]`::make_input_namespace` (light
  mechanics). Target role: state contributor — member 15 (path constant the
  trio pins), member 18 (ledger declaration over the owner product), members
  19--20 (thin wrappers), member 21 (registration; verified
  `owner="forms.input_namespace"`, `before_bind=True`, disjoint from the
  five sibling owners in the P2 census). No local clear body (verified: the
  wrapper calls `_clear_input_namespace()` only).
- **Challenges.** C12 counts 0 here.
- **Owner + lifetime.** Bus + trio owner (principle 7: the narrowest owner
  every flavor can depend on without importing a sibling). Lifetime: the
  parked-globals paragraph on `make_input_namespace` (ledgers reset,
  `__dict__` entries overwritten in place) — projection, not restated here.
- **Migration.** None (already compose by name; file item owes no edit).
- **Distinct behavior.** Light clear (`ledger.clear()` only) vs the set
  families' heavy clear (factory caches + `_lifecycle` binding) — the
  write flavors have neither a BFS cache nor per-set state (filters R-g,
  re-proved P2).
- **Behavioral proof.** P2 + P5 (`execution-verified`: disjoint owners,
  pre-bind membership, ledger reset). Ledger assertions in
  [test-forms-sets.py][test-forms-sets] `static-reviewed`.
- **Structural gate.** The ledger emptiness + namespace-disjointness rows
  fail any bypass that parks state outside the ledger (a second dict would
  survive the clear and the emptiness assertion breaks).
- **Freshness.** Target `55614839ff479b3610b6026be65f2107ee560fcd`;
  [utils/inputs.py][utils-inputs]
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`;
  [registry.py][registry] `9cc8bb553fd417fc465809a541769a8383469cda`;
  twin [orders/inputs.py][orders-inputs]
  `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516`;
  [rf-inputs.py][rf-inputs] `9b17d95229b312f23deb5778468e3abacf730ec2`;
  HEAD `9031cb3d`.

### F2 -- `set-type-naming` (checked non-membership)

This file does NOT join the family: it builds no type names (P3 defscan:
zero `type_name_for` definitions; the one naming act is member 28
delegating to `name_set_input_type_name`). The create-vs-partial decision
(`operation_kind == PARTIAL`, the `FORM`-sentinel consequence) is the
wrapper's own one-line rule (R4), not a naming rule. No index change
proposed.

### F3 -- `set-arguments-factory-bfs` (checked non-membership)

This file does NOT join the family: no BFS walk, no per-class collision
check, no idempotent factory cache, no subclass-rejection guard (defscan
clean; `ArgumentsFactory` zero hits). Write flavors derive from one
declaration's field set, not a related-set graph. The per-shape dedupe
lives at [forms/sets.py][forms-sets]`::_cached_build_form_input` (consumer
of member 26), not here. No index change proposed.

### F4 -- `dynamic-set-class-getter` (checked non-membership)

This file does NOT join the family: no Layer-6 getter, no meta cache, no
reserved keys, no `type(...)` skeleton (defscan clean). The deferred surface
lives in the set-family factories. No index change proposed.

### F5 -- `active-input-permission-facade` (checked non-membership)

This file does NOT join the family: zero `permission` / `traversal` hits;
no `_permission` definition; no `_field_specs` provenance table (the form
reverse map is a stashed LIST of `InputFieldSpec`, not a keyed ledger).
Permission defaults live in [forms/sets.py][forms-sets] (`DenyAll` for the
plain flavor, model-backed default for the `ModelForm` flavor). No index
change proposed.

### R1 -- Form operation-kind vocabulary (file-local)

- **Contract + variation.** Members 16--17 + the vocab checks in members
  34/38: `FORM = "form"` is the fixed shape-identity component a plain
  `DjangoFormMutation` carries in place of a model operation;
  `CREATE_SHAPED_KINDS = frozenset({CREATE, FORM})` names the
  create-shaped set; anything else fails loud naming the form + value.
  Varies by adding/reshaping a kind (C1 counts 1).
- **Sites + roles.** Definition here (one body: sentinel + set + two
  checks). `CREATE` / `PARTIAL` imported by name from
  [mutations/inputs.py][mutations-inputs] (consumers, P3). Oracles: the
  module-path/kinds pin + both out-of-vocabulary rows (P4 re-proved all
  three raises).
- **Challenges.** C1 counts 1.
- **Owner + lifetime.** This file (the form-kind population lives nowhere
  else; the model flavor never sees `FORM`). Nothing stored (module
  constants read per call).
- **Behavioral proof.** P4 (`execution-verified`: `FORM` builds
  create-shaped, `PARTIAL` builds partial-shaped, three foreign kinds
  raise).
- **Structural gate.** The two out-of-vocabulary oracles fail a vocabulary
  widening that silently resolves to create-shaped.
- **Freshness.** Target as in F1; [mutations/inputs.py][mutations-inputs]
  `fc4420475f404297822d7d94bee7bdd275700803`;
  [test-forms-inputs.py][test-forms-inputs]
  `2c72da6334de068bc2b26895e24a279a79e7925e`.

### R2 -- Field-basis discovery + validation (file-local)

- **Contract + variation.** Members 22--24: `get_form_fields` reads
  `base_fields` with NO instantiation (kwarg-requiring forms stay
  discoverable); `_form_field_basis` validates the mapping (non-mapping
  source, non-identifier/keyword names, non-`forms.Field` values all raise
  typed naming the form, hostile `__repr__` contained via `_safe_arg_repr`);
  `normalize_form_field_basis` is the hook boundary (rejects `None`). Varies
  on the source/validation (C2 counts 1).
- **Sites + roles.** Definition here. Consumers: the hook invoker in
  [forms/sets.py][forms-sets]`::_mutation_form_fields` (calls member 24 by
  name) + every downstream member (26, 27, 34, 35). Oracles: discovery +
  corruption + keyword + hostile-name rows (P4 re-proved the keyword arm).
- **Challenges.** C2 counts 1.
- **Owner + lifetime.** This file (the form-basis home; pure reads, the
  `dict()` copy keeps later passes from observing caller mutation).
  Nothing stored.
- **Behavioral proof.** P4 (`execution-verified`) + basis oracles
  `static-reviewed`.
- **Structural gate.** The corrupted-basis + keyword-name oracles fail a
  validation weakening that lets a bad basis reach `build_strawberry_input_class`
  as a raw `TypeError` / `SyntaxError`.
- **Freshness.** Target as in F1; [forms/sets.py][forms-sets]
  `36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`;
  [exceptions.py][exceptions] `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`.

### R3 -- Shape-identity content projection (file-local)

- **Contract + variation.** Members 25--26: the hashable projection of the
  hook basis the per-shape build cache keys on — per-field converter type,
  the ONE requiredness decision (same `form_field_required` + resolved
  column the build uses), and the column-less relation target. Identical
  projections dedupe onto one class object; any content difference builds
  separately and stays loud at the materialize ledger. Varies by adding an
  axis (C3 counts 1).
- **Sites + roles.** Definition here. Consumer: the cache-key assembly in
  [forms/sets.py][forms-sets]`::_cached_build_form_input` (reads member 26
  by name). Oracles: shared-hook dedupe + stateful-hook loudness rows in
  [test-forms-sets.py][test-forms-sets] (`static-reviewed`).
- **Challenges.** C3 counts 1.
- **Owner + lifetime.** This file (the projection of R2's basis; pure
  per-call tuple, nothing stored).
- **Behavioral proof.** Static-reviewed (projection reads the same three
  quantities the build consumes — verified name-by-name in P3); dedupe
  oracles pin both directions.
- **Structural gate.** The shared-hook dedupe oracle fails a projection
  that drops an axis (two content-different bases collapse onto one class).
- **Freshness.** Target as in F1; [forms/converter.py][forms-converter]
  `b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`;
  [forms/sets.py][forms-sets] as in R2.

### R4 -- Narrowing + naming wrappers over shared spines (file-local)

- **Contract + variation.** Members 27--28: member 27 supplies the form
  basis + message knobs to `resolve_effective_fields`; member 28 supplies
  the form-class base name + the create-vs-partial decision
  (`operation_kind == PARTIAL`, so `FORM` is create-shaped) to
  `name_set_input_type_name`. Varies only in the knobs/decision (C4 knob
  wording counts 1 here; C5 partial-decision counts 1 here; spine changes
  count 0 here).
- **Sites + roles.** Definitions: the knobs + the `== PARTIAL` decision.
  Spine owners: [utils/inputs.py][utils-inputs]. Consumers: members 34/38
  + [forms/sets.py][forms-sets]`::_form_input_type_name_for` (reads member
  28 by name). Oracles: narrowing fail-loud + naming pins (P4 re-proved
  unknown/empty/mutual-exclusion + canonical/deterministic names).
- **Challenges.** C4 counts 0-here/1-knob; C5 counts 0-here/1-decision.
- **Owner + lifetime.** Knobs + decision here; spines upstream. Nothing
  stored.
- **Behavioral proof.** P3 (`execution-verified`: single refs, composed by
  name) + P4 (`execution-verified`: names + narrowing raises).
- **Structural gate.** The narrowed-name determinism oracle fails a
  decision change that maps `FORM` to the partial suffix.
- **Freshness.** Target as in F1; [utils/inputs.py][utils-inputs] as in F1;
  [utils/strings.py][utils-strings]
  `3ec3b262ea8666d4ba36cf83807ca377fee5a680`.

### R5 -- Backing-column resolution (file-local)

- **Contract + variation.** Member 29: a `ModelForm` field with a forward
  concrete column / M2M resolves through `model._meta.get_field(name)`; a
  plain `Form`, an extra field, or a reverse/GFK/GenericRelation name
  yields `None` (model-less path). Corrupted `_meta` / `get_field`
  internals fail loud typed, never raw or silent-`None`. Varies on the
  exclusion rule (C6 counts 1).
- **Sites + roles.** Definition here. Predicate consumers:
  `is_forward_many_to_many` / `is_forward_concrete_relation` read by name
  (owners in [utils/relations.py][utils-relations], P3). Consumers of the
  resolution: members 26/32/34/35 (all by name). Oracles: reverse-relation
  + GFK + extra-field rows.
- **Challenges.** C6 counts 1.
- **Owner + lifetime.** This file (the form column-resolution home; the
  taxonomy it screens through is owned upstream). Nothing stored.
- **Behavioral proof.** Static-reviewed against the bodies + the
  `relation_kind` contract read in full; column-backed oracles pin the
  arms.
- **Structural gate.** The reverse-relation oracle (`items` staying
  scalar) fails an exclusion weakening that mis-emits a relation id input.
- **Freshness.** Target as in F1; [utils/relations.py][utils-relations]
  `7662b0bb669c4dfba4a437f3b8f309357f718dca`.

### R6 -- Per-field triple dispatch (file-local)

- **Contract + variation.** Members 30--32: member 32 routes a column-backed
  field through `model_column_input_annotation` /
  `model_column_write_kind` (symmetric wire contract with the read
  `DjangoType`) and a column-less field through `convert_form_field` (the
  model-less table), finalizing relation id-types via member 30 (over
  `annotate_queryset_relation`) and files via `Upload`; ONE
  `form_field_required` call serves both arms; the single `InputFieldSpec`
  construction records `target_name` = form name + the SAME `related_model`
  the id type derived from. Varies on routing/remap (C8 counts 1); a new
  field class counts 0 here (converter table moves); the id-type rule
  counts 0 here (C7).
- **Sites + roles.** Definition here (dispatch + record). Spine/table
  owners: [mutations/inputs.py][mutations-inputs],
  [forms/converter.py][forms-converter] (all composed by name, P3).
  Consumer: the decode in [forms/resolvers.py][forms-resolvers] (reads
  `target_name` / `kind` / `related_model`, never re-derives).
- **Challenges.** C7 counts 0-here/1-wording; C8 counts 1-routing/0-table.
- **Owner + lifetime.** This file (the form build site; per-call triples,
  nothing stored).
- **Distinct behavior.** `target_name` is always the declared form name,
  never the `<name>_id` attr (bound forms key by form name) — recorded at
  the construction site.
- **Behavioral proof.** P4 (`execution-verified`: relay-vs-raw-pk rows via
  the id-type oracles' build paths, `Upload` row, read-side-enum row)
  + triple oracles `static-reviewed`.
- **Structural gate.** The `categoryId`-lands-under-form-key oracle fails a
  `target_name` change to the remapped attr; the queryset-`None` oracle
  fails a fail-loud weakening.
- **Freshness.** Target as in F1; [mutations/inputs.py][mutations-inputs]
  + [forms/converter.py][forms-converter] as above;
  [forms/resolvers.py][forms-resolvers]
  `4edb984b299b4e2a71492e73382558b01865f48a`;
  [scalars.py][scalars] `5e354042d405040f6137cebd39abe9c042ffece8`.

### R7 -- Collision guard (file-local)

- **Contract + variation.** Member 33: raises on the FIRST
  `iter_input_field_collisions` message with the form nouns (both the
  `<name>_id` input-attr clash and the camel-case GraphQL-name clash fail
  loud instead of silently dropping a field). Varies in wording/policy (C9
  counts 1 here); a new arm counts 0 here.
- **Sites + roles.** Definition: policy + nouns here. Walk owner:
  [utils/inputs.py][utils-inputs]. Intentional contrast: the serializer
  aggregates instead (spec-039; different consumption policy, same walk).
- **Challenges.** C9 counts 0-here/1-here.
- **Owner + lifetime.** Policy here; walk upstream. Nothing stored.
- **Behavioral proof.** P4 (`execution-verified`: `foo_bar` + `fooBar`
  raises naming `fooBar`).
- **Structural gate.** That oracle fails a guard removal (Strawberry
  silently collapses the two onto one schema field).
- **Freshness.** Target as in F1; [utils/inputs.py][utils-inputs] as in F1.

### R8 -- Single generator + pair builder (file-local)

- **Contract + variation.** Members 34/38: member 34 builds ONE input —
  requiredness from the converter flag on create, model-backed fields
  forced optional on partial while column-less extras keep theirs
  (spec-038 Decision 7), widened via `optional_input_field` to `T | None` +
  `UNSET`; member 38 builds the create+partial pair (freezing one-shot
  `fields`/`exclude` iterables into `effective_names` so the second
  resolution cannot consume an exhausted iterator). Varies on the
  widening/pair rules (C10 counts 1).
- **Sites + roles.** Definition here. Tail/build owners:
  [utils/inputs.py][utils-inputs] (`optional_input_field`,
  `build_strawberry_input_class`, P3). Consumers: the bind via
  [forms/sets.py][forms-sets]`::_cached_build_form_input`. Oracles: shape
  + partial-extra-required + one-shot-freeze rows (P4 re-proved the shapes).
- **Challenges.** C10 counts 1.
- **Owner + lifetime.** This file (the form generator home). Nothing stored
  (the per-shape cache lives in sets.py).
- **Behavioral proof.** P4 (`execution-verified`) + shape oracles
  `static-reviewed`.
- **Structural gate.** The partial-extra-still-required oracle fails a
  widening change that forces extras optional; the one-shot-freeze oracle
  fails a direct pass-through of the raw iterables.
- **Freshness.** Target as in F1; [utils/inputs.py][utils-inputs] as in F1;
  [forms/sets.py][forms-sets] as in R2.

### R9 -- Required-set + create/partial guards (file-local)

- **Contract + variation.** Members 35--37: member 35 derives the required
  set via the shared `form_field_required` + resolved column (never
  converting, so excluded unsupported fields cannot raise); member 36
  rejects a create narrowing dropping a required field; member 37 rejects a
  partial narrowing dropping a required COLUMN-LESS field only (model-backed
  required fields reconstruct from the row). Drop-detection rides
  `guard_dropped_required`. Varies in the required-set filter (C11 counts 1
  here); arithmetic counts 0 here.
- **Sites + roles.** Definitions: the set derivation + the column-less
  filter here. Arithmetic owner: [utils/inputs.py][utils-inputs].
  Intentional contrast: the serializer twin subtracts
  `Meta.injected_fields` (a mechanism forms lack — J3). Per-declaration
  (not per-shape) execution is enforced by the sets.py cache ordering.
- **Challenges.** C11 counts 0-here/1-here.
- **Owner + lifetime.** Set + filter here; arithmetic upstream. Nothing
  stored.
- **Behavioral proof.** P4 (`execution-verified`: both guards raise naming
  the field; model-backed partial drop allowed by oracle).
- **Structural gate.** The two drop-rejection oracles + the
  model-backed-partial-allowance oracle fail either a guard removal or a
  blanket reuse of the create guard on partial.
- **Freshness.** Target as in F1; [utils/inputs.py][utils-inputs] as in F1;
  [forms/converter.py][forms-converter] as in R3.

### J1 -- `converter-table-per-surface-ownership` (rejection CONFIRMED, re-derived fresh)

This file holds NO table (P3-adjacent census: zero `_SCALAR` /
`scalar_registry` / `_CONVERT_` definitions; the only registry touch is
CALLING `convert_form_field`). The unification candidate is REJECTED again
from this side — never inherited from the converter item.

- **Contract differences.** Read side: `models.Field` -> scalar (shared
  read/filter contract). This consumer's two key spaces stay disjoint by
  construction: member 29 resolves the `models.Field` FIRST and the column
  arm delegates to the read side (same enum object on both sides,
  R6 distinct-behavior); column-less fields hit the `forms.Field`-keyed
  table via `convert_form_field`. Four key spaces, four contracts (converter
  artifact P2: 26/1/12/16, pairwise disjoint — cited, not re-run; this
  side's contribution is the no-table census + the resolve-first ordering
  read in member 29/32).
- **Trigger (re-checked fresh).** A new surface whose field population is a
  SUBSET of an existing table's key space with identical value contract
  reopens the count. A new KIND of field population keeps its own table.
- **Durable home.** The module docstring's key-space clause + the converter
  header (both read); the plan index row already covers all four files — no
  index change proposed.
- **Freshness.** Target as in F1; [forms/converter.py][forms-converter] +
  [mutations/inputs.py][mutations-inputs] as above.

### J2 -- Scalar-naming-pair shared form (rejection, considered fresh)

Member 31 (`python_attr = name; graphql_name = graphql_camel_name(name)`)
reads like the model scalar arm in
[mutations/inputs.py][mutations-inputs]`::model_column_input_annotation`.
REJECTED: both are one-line compositions of the OWNED `graphql_camel_name`
(consumers, not definitions); the tuple shapes differ (form carries `kind`
as a 4th element for the dispatch; model carries 3 + classifies via a
separate `model_column_write_kind` call); unifying would couple two build
sites' triple construction to save zero change obligations (C5/C8 each
already count at their own site). Trigger: a third naming shape that must
stay byte-identical across both build sites. Home: this clause.

### J3 -- Partial-requiredness unification with the serializer (rejection, considered fresh)

Member 34's partial rule (model-backed optional, column-less extra keeps
required) vs the serializer partial rule (own `optional_fields` /
nullability axes). REJECTED: disjoint populations with disjoint reasons to
change — a form extra cannot reconstruct from a model row
(`model_to_dict` returns columns only; member 37's docstring), while
serializer fields have no backing-row reconstruction at all. Positing the
serializer rule here (C13) would wrongly force required extras optional.
Trigger: a write flavor whose partial path reconstructs dropped fields
from a backing row exactly like the form path. Home: member 34 + member 37
docstrings (already state the reconstruction reason).

### J4 -- Guard-merge with the serializer guard (rejection, considered fresh)

Members 36--37 vs
[rf-inputs.py][rf-inputs]`::guard_create_required_serializer_fields`.
REJECTED as a merge: the drop-detection already IS one body
(`guard_dropped_required`, C11 counts 0 here); what differs is only the
required-set derivation (form: no injected-field mechanism, so no `waived`
set; serializer: subtracts `Meta.injected_fields`). Merging the derivations
would thread a `waived` knob the form path can never fill. Trigger: the
form flavor gaining an injected-field mechanism. Home:
[utils/inputs.py][utils-inputs]`::guard_dropped_required` docstring (already
names the split).

## Defects

None. Three investigated edges released without a defect:

1. The `resolve_effective_form_fields` unknown-name subject reads
   `"DjangoFormMutation for ..."` on the `ModelForm` path too. Pinned
   wording (narrowing oracles assert it); changing it alters no accepted
   shape — cosmetic, not a contract break.
2. `build_form_input_class` reads the hook basis twice per build (once via
   the narrowing, once for `full_field_names`). A deliberately stateful
   hook could split the two reads — but the documented contract already
   routes that to dedupe-or-LOUD at the materialize ledger (R3), and the
   worst case is a loud collision, never a silently wrong shape. No
   contract row broken.
3. `form_input_type_name` reads `form_class.__name__` unguarded while
   hook-supplied data is hostile-guarded everywhere. Class identity is not
   hook data; no contract source requires a typed error for a hostile
   class object, and adding one changes nothing accepted. Robustness row
   at most — not filed.

Nothing routed to any owner.

## Pending execution

None. All five probes already ran green against the shared tree; each is
read-only (imports + AST + in-memory form instances + pure calls; no source
mutation, no database — P4/P5 run with empty `DATABASES`). No pytest was
run in the shared tree, per item rules; oracle bodies are
`static-reviewed`. No `execution-deferred` items. `FAKESHOP_SHARDED=1` and
Postgres cells are `inapplicable by construction`: the target's code path
reaches no database, alias, or dialect decision (pure dispatch over
in-memory field instances + `_meta` reads; P4/P5 prove it by running with
no database configured).

## Judgment

Backstop discharged: 38/38 `ast.Module.body` members enumerated, 15
challenges run (C1--C15, every variation axis of every rule), six matrix
axes discharged against the real surface (orders twin + serializer mirror
read first whole; light-vs-heavy namespace split re-proved executable;
round-trips verified in both directions; sync/async absence verified by
instrument, not assumed), nine file-local records with proving challenges
(R1--R9), five families checked as non-membership/contribution with the
consumer relationship named (F1 contributor, F2--F5 correctly withheld),
four rejections with difference + trigger + home (J1 re-derived fresh, no
index change: the plan row already covers all four files). Zero defects,
zero pending. The target owns its rules singly: one kind vocabulary, one
basis, one projection, one column resolution, one dispatch, one guard
policy per axis, one generator, one guard pair. Zero-edit result is
legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
ff9f4d543edd88bb4abcf6f87a3e9e2fecc79db1 --
django_strawberry_framework/forms/inputs.py` is empty for the target
(working blob `55614839ff479b3610b6026be65f2107ee560fcd` equals the item
baseline member and `HEAD:` — target CLEAN, so no hunk attribution was
owed); the artifact itself is this new file
(`docs/dry/dry-file-forms__inputs.md`, untracked until Worker 0 records
it). The `## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never touched.
Concurrent dirt (`django_strawberry_framework/connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`, plus the
further working-tree dirt listed in `git status --short` at run time) was
never edited, reverted, or tidied, verified by content-diff scoping (the
item-scoped diff shows no entry before and after). Scratch (untracked, kept
for Worker 2 re-run):
`docs/dry/temp-tests/dry-file-forms__inputs/p1_ast_census.py`,
`p2_mirror.py`, `p3_delegation.py`, `p4_behavior.py`, `p5_clear.py` — all
read-only, all green. Concurrent edit observed mid-task and left untouched:
`django_strawberry_framework/filters/inputs.py` moved in the worktree from
`82b52d97b8f8b26d2846df24dabcabb793507c87` (the bytes read for this item)
to `06797dc7db04e4fc78cfbc478094ecada273c533` via a single external hunk
confined to `_normalize_range_value` (range-patch fail-loud hardening; the
only `@@` in `git diff HEAD`). No site this item depends on changed — the
heavy-quartet shape (P2), the light-vs-heavy split, and the converter
census are byte-identical — so no finding reopens; Worker 2 re-hashes the
twin before relying on it. No `ruff` run owed (no tracked edits). No pytest run
(not authorized by the entry command). Do not commit.

## Independent verification (Worker 2)

Worker 2 read, in order: `AGENTS.md`, `docs/dry/DRY.md`,
`docs/dry/worker-2.md`, the plan item (File `forms/inputs.py` in
`docs/dry/dry-0_0_15.md`, Run `0.0.15 2026-09-18-1`), the complete target
(`django_strawberry_framework/forms/inputs.py`, 914 lines), the item-scoped
diff, the probes, then this artifact's `## Findings`. No worker-memory read.
No production edit made; no commit; all concurrent dirt preserved.

### Own trace (recorded before opening `## Findings`)

Re-derived from the target alone plus the owners it names:

1. **Kind vocabulary** — `FORM = "form"` sentinel, `CREATE_SHAPED_KINDS =
frozenset({CREATE, FORM})`, plus the two out-of-vocabulary raises in
`build_form_input_class` and `build_form_inputs`. One body: a new kind moves
the sentinel/set/checks together. Owner I would choose: this file (the
`FORM` population lives nowhere else; the model flavor never sees it).
Count per change C1: **1**.
2. **Field-basis discovery + validation** — `get_form_fields` (class-level
`base_fields`, no instantiation), `_form_field_basis` (mapping/identifier/
keyword/`forms.Field`-value validation, hostile-`__repr__` contained),
`normalize_form_field_basis` (`None` boundary). Change the source or the
validation: **1** definition here. Owner: this file.
3. **Shape-identity content projection** — `_related_model_of` (column-less
relation target, guarded to `None`) + `_form_basis_content_identity`
(per-field converter type, the ONE `form_field_required` decision with the
resolved column, related model). Add an axis: **1** here; the per-shape cache
in [forms/sets.py][forms-sets]`::_cached_build_form_input` is a consumer, not
a second definition. Owner: this file.
4. **Narrowing + naming wrappers** — `resolve_effective_form_fields`
(basis + message knobs over the shared spine) and `form_input_type_name`
(base name + `operation_kind == PARTIAL` decision over the shared spine).
Spine changes count **0** here (owners in
[utils/inputs.py][utils-inputs]`::resolve_effective_fields` and
`::name_set_input_type_name`); knob/decision wording counts **1** here.
Owners: knobs + decision here, spines upstream.
5. **Backing-column resolution** — `_model_column_for` (`_meta.model` read,
`get_field`, forward-concrete/M2M screen via the upstream predicates,
reverse/GFK/GenericRelation exclusion, corrupted-internals typed raises).
Change the exclusion: **1** here. Owner: this file.
6. **Per-field triple dispatch + `InputFieldSpec` site** —
`_model_less_relation_annotation` (column-less relation over
`annotate_queryset_relation`), `_simple_triple` (shared non-relation pair),
`_field_triple_and_spec` (column-backed vs column-less routing, ONE
`form_field_required` call for both arms, single `InputFieldSpec`
construction with `target_name` = form name and the SAME `related_model`
the id type derived from). New field class: **0** here (converter table
moves); routing/remap change: **1** here; id-type rule: **0** here (spine).
Owner: this file. The decode in
[forms/resolvers.py][forms-resolvers] reads `target_name`/`kind`/
`related_model` without re-deriving — consumer.
7. **Collision guard** — `_guard_input_attr_collisions` (first-message raise
with form nouns over `iter_input_field_collisions`). New arm: **0** here;
wording/policy: **1** here. Owner: policy here, walk upstream.
8. **Single generator + pair builder** — `build_form_input_class`
(create honors the converter flag; partial forces model-backed optional
while column-less extras keep theirs; widening via `optional_input_field`)
+ `build_form_inputs` (freezes one-shot iterables into `effective_names`,
create-side vocab check). Change the widening/pair rule: **1** here.
Owner: this file.
9. **Required-set + guards** — `_required_form_field_names` (shared
requiredness + resolved column, never converting),
`guard_create_required_fields` (reject create narrowing dropping a required
field), `guard_partial_required_column_less_fields` (partial drops only
reject column-less required; model-backed reconstruct from the row).
Arithmetic: **0** here (owner
[utils/inputs.py][utils-inputs]`::guard_dropped_required`); set/filter:
**1** here. Owners: set + filter here, arithmetic upstream.
10. **Namespace lifecycle** — path constant, ledger trio unpack, two thin
wrappers, bus registration. No local clear body (wrapper calls
`_clear_input_namespace()` only). Contributor to the open
`subsystem-clear-lifecycle` family; bus + trio own the mechanics.

**Reconciliation vs W1.** One-to-one agreement: my rules 1--9 map onto
W1's R1--R9 with identical counts (C1--C12 as tabled, C13--C15 refused)
and identical owners (here for definitions, upstream for the four spines +
walk + arithmetic + bus/trio). My rule 10 maps onto W1's F1 (contributor,
not owner). No difference to reconcile.

### Concurrent-hunk independence ruling

Claim under test (W1 `## Implementation (Worker 1)`): the in-flight
`django_strawberry_framework/filters/inputs.py` hunk touches no site this
item depends on. **Confirmed first-hand.** The worktree diff vs `HEAD` is a
single hunk confined to `_normalize_range_value` (range-shape fail-loud
hardening: unknown-axes and non-range raises). Text search of this artifact
for `_normalize_range_value` hits only W1's implementation-scope note, never
a finding; no finding cites range-shape behavior; the target itself has zero
`range` hits (case-insensitive). The only twin-relationship this item relies
on is the light-vs-heavy namespace split, and I re-ran P2 against the
CURRENT worktree bytes: filters/orders still heavy quartet, forms/mutations/
serializer still light trio, six disjoint clear owners. **The finding set is
robust to both versions of the hunk — no revision, no reopen.**
Worktree blob observed at verification time:
`06797dc7db04e4fc78cfbc478094ecada273c533` — concurrent in-flight work,
not cycle-owned (item baseline `ff9f4d543edd88bb4abcf6f87a3e9e2fecc79db1`
vs `HEAD` shows it plus its `tests/filters/test_inputs.py` companion as
external edits; neither path is in this item's scope).

### Enumeration (member-by-member vs own count)

Re-ran the instrument independently: `ast.Module.body` count **38**,
**0** `AsyncFunctionDef`, **0** `await` — matching W1. Walked all 38
against the table: 1 docstring (projection), 13 imports (1 `__future__` +
12 real), 4 assigns (3 annotated constants + the namespace trio unpack),
1 registration call-expression, 19 function defs. Every member lands in
W1's home column with no reassignment owed: members 15/18--21 to F1,
member 28's `type_name_for` absence to F2 (defscan clean, confirmed),
members 22--24 to R2, 25--26 to R3, 27--28 to R4, 29 to R5, 30--32 to R6
(member 31 additionally a J2 member), 33 to R7, 34/38 to R8, 35--37 to R9,
16--17 to R1. Imports claimed as consumers check out (members 2--14 all
consumed by name; `describe_value` hit is prose-only, no definition).
**38/38 assigned, no gap, no surplus.**

### Matrix vs real surface

Mirrors read FIRST as required: the orders twin whole
([orders/inputs.py][orders-inputs]) plus the filters twin and the
serializer mirror guard/narrowing/namespace regions (W1's read logged in
`## System trace`; the light/heavy census I re-executed above proves the
current bytes, not memory). Axis verdicts, judged on reasons not samples:
(1) mirroring — searched, twins compared by behavior (namespace trio vs
quartet, guard-set derivations, first-raise vs aggregate policy, `==
PARTIAL` vs `!= CREATE` as the `FORM` consequence); everything shareable
already composed by name; (2) sync/async — inapplicable by construction,
instrument-proved (0 async defs/awaits, finalize-time construction over
in-memory fields, no query execution; the resolver pipeline consumes, never
re-implements); (3) derived knowledge — searched, no re-derivation (path
pinned once, names/sets/projections composed by name, single
`InputFieldSpec` construction); (4) round-trips — both directions verified
(encode here/decode via `target_name`/`kind`/`related_model`; name/cache/
guard triple over one basis; narrowing/detection over one effective set);
(5) other media — 1 definition per rule, oracles spell literals without
iterating owner tables, ledger rows assert behavior; (6) omission —
enumerated with contract sources, every absence justified (total vocab
coverage, deliberate non-conversion in the required set, fail-loud
`queryset is None`, single requiredness decision on both arms,
prose-only `_lifecycle`/`describe_value` hits). **All six discharged; no
axis owes more search.**

### Counts, roles, oracles

Definition counts confirmed per challenge table (C1--C3, C6, C8, C10 at 1
here; C4/C5/C7/C9/C11 split 0-here/1-knob as tabled; C12 0 here;
C13--C15 refused). Roles confirmed: definitions here for R1--R3, R5, R6,
R8, set/filter halves of R4/R7/R9; consumers by name for every spine, table,
predicate, bus, and downstream (sets.py hook invoker, cache assembly, name
reader; resolvers decode). Oracle check: item-scoped diff is empty so no
oracle was touched, let alone rewritten to read from an owner; the cited
oracles spell wire literals and behavior pins
([test-forms-inputs.py][test-forms-inputs] naming/shape/id-type/`Upload`/
narrowing/guard/collision/basis rows,
[test-forms-sets.py][test-forms-sets] ledger/dedupe rows). **No oracle
rewritten.**

### Equivalence (principle 8)

Zero-edit item: no observable behavior to preserve across a migration, so
the principle-8 burden is the probes' behavioral coverage of the claimed
rules, not a before/after proof. P4 re-ran green here (canonical vs
deterministic narrowed names, create/partial shapes, three
out-of-vocabulary raises, both dropped-required raises, unknown/empty/
mutual-exclusion raises, camel collision naming `fooBar`, keyword basis
raise — no database). P5 re-ran green (bus membership, pre-bind subset,
ledger reset without touching parked globals). P2/P3 re-ran green (split +
20/20 delegation). Oracle bodies `static-reviewed` is the correct ceiling
for a file item with no consolidation. **Equivalence burden discharged.**

### Zero-edit validation + family routing (judgment on W1's calls)

Item-scoped diff confirmed empty by my own run (`git diff
ff9f4d543edd88bb4abcf6f87a3e9e2fecc79db1 --
django_strawberry_framework/forms/inputs.py` = 0 bytes; target absent from
`git status --short`; worktree blob
`55614839ff479b3610b6026be65f2107ee560fcd` equals W1's). Five probes
present at `docs/dry/temp-tests/dry-file-forms__inputs/` and all re-ran
green. Coverage is complete (38/38, 15 challenges, six axes) and every
assignment terminates correctly: F1 clear-contributor (state contributor
with disjoint `owner="forms.input_namespace"`, `before_bind=True`) —
**agree**; F2--F5 withheld (no type names, no BFS factory, no Layer-6
getter, no permission facade — defscans confirmed) — **agree, no index
change**; J1 converter-table confirmed (no-table census + resolve-first
ordering; four key spaces, four contracts) — **agree, no index change
(the plan row already covers all four files)**; J2 scalar-naming pair
refused (different tuple shapes, zero change obligation saved) —
**agree**; J3 partial-requiredness refused (form extras reconstruct from
the row, serializer fields have no row — C13 correctly refused) —
**agree**; J4 guard-merge refused (arithmetic already one body; only the
derivations differ and forms has no `waived` to fill) — **agree**. A file
item never owes a production edit; none is owed here.

### Rejections, fingerprints, gates, Pending, coupling

Rejections J1--J4 each carry contract difference + reconsideration trigger
+ durable home (J1 at the key-space prose + converter header; J2 here; J3
at members 34/37 docstrings; J4 at the shared spine docstring) — **pass**.
Freshness re-hashed at verification time, all matching W1 (target
`55614839ff479b3610b6026be65f2107ee560fcd`;
[utils/inputs.py][utils-inputs]
`ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`;
[registry.py][registry] `9cc8bb553fd417fc465809a541769a8383469cda`;
[orders/inputs.py][orders-inputs]
`6f6ec946351fb56d92637a3c7e75a9fd8fc0b516`;
[rf-inputs.py][rf-inputs] `9b17d95229b312f23deb5778468e3abacf730ec2`;
[mutations/inputs.py][mutations-inputs]
`fc4420475f404297822d7d94bee7bdd275700803`;
[test-forms-inputs.py][test-forms-inputs]
`2c72da6334de068bc2b26895e24a279a79e7925e`;
[forms/sets.py][forms-sets]
`36ce80b4fef4f9e62db22d933ff7bb10b1ea4e25`;
[exceptions.py][exceptions] `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`;
[forms/converter.py][forms-converter]
`b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`;
[utils/strings.py][utils-strings]
`3ec3b262ea8666d4ba36cf83807ca377fee5a680`;
[utils/relations.py][utils-relations]
`7662b0bb669c4dfba4a437f3b8f309357f718dca`;
[forms/resolvers.py][forms-resolvers]
`4edb984b299b4e2a71492e73382558b01865f48a`;
[scalars.py][scalars] `5e354042d405040f6137cebd39abe9c042ffece8`;
`HEAD` `9031cb3d`; filters twin cited only under the concurrent-hunk
ruling above at worktree blob `06797dc7…`). Gates: each finding's gate is
an existing permanent oracle row that fails the bypass it guards
(vocabulary widening, validation weakening, projection-axis drop, `FORM`
suffix mis-map, exclusion weakening, `target_name` remap, fail-loud
weakening, guard removal, narrowed-name drift) — no bespoke per-helper
existence test, populations justified. Negative controls are argued by
oracle shape (a bypass flipping the guarded behavior breaks the pinned
row); no separate mutation proof was owed for a zero-edit file item and
none is claimed as run. `## Pending execution` absent — **correct**: all
probes `execution-verified`, read-only, no database; sharded/Postgres
cells `inapplicable by construction` with the reason stated (pure dispatch
over in-memory fields + `_meta` reads). Coupling: none introduced, none
to mark — correct for zero-edit.

### AGENTS.md prose check

Item-scoped diff touches no `.py`, so formatting/lint gates are
untouched; no `ruff` run owed for this verification append (markdown-only,
untracked artifact). Citations use `path::Symbol` throughout, never raw
`path:NN` outside the allowed scratchpad shape; no process provenance
narrated; no test-tier obligation arises (zero-edit file item, no new
fixture needed); link scaffold preserved (this section reuses existing
ref-ids, adds none). **Pass.**

### Defects (Worker 2)

None. I endorse W1's release of all three investigated edges without a
defect: (1) the `DjangoFormMutation`-worded unknown-name subject on the
`ModelForm` path is pinned oracle wording altering no accepted shape —
cosmetic; (2) the double basis read per build degrades to a loud ledger
collision, never a silently wrong shape — no contract row broken; (3) the
unguarded `form_class.__name__` read is class identity, not hook data, with
no contract source demanding a typed error — robustness at most. No new
defect found on my trace (no docstring/body contradiction, no missing
guard with a contract source, no layering violation in the imports).

### Verdict

`Status: verified`, no pending execution. Zero-edit result legitimate:
one owner per rule, every member assigned, every challenge counted,
matrix discharged against the real surface, rejections durable,
fingerprints fresh, concurrent work untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-init]: ../../django_strawberry_framework/forms/__init__.py
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[scalars]: ../../django_strawberry_framework/scalars.py

<!-- tests/ -->
[test-forms-converter]: ../../tests/forms/test_converter.py
[test-forms-inputs]: ../../tests/forms/test_inputs.py
[test-forms-resolvers]: ../../tests/forms/test_resolvers.py
[test-forms-sets]: ../../tests/forms/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
