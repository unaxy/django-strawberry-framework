# DRY review: `generated-mutation-input-identity`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

Identity of generated mutation inputs = shape (which fields go in) + name
(what the type is called) + stability (same declaration leads to the same
type across rebuilds and finalize). Provisional owner confirmed:
[inputs.py][mi-inputs]`::mutation_input_shape` (+ `::MutationInputShape`,
`::mutation_input_type_name`; name grammar at [utils-inputs][u-inputs]
`::name_set_input_type_name`).

What the target owns: one derived shape descriptor per
`(model, operation_kind, frozenset(effective field names))` carrying the
selected editable fields, the full-vs-narrowed name basis, the generated
type name, and the bind cache key — so the generator, the bind cache, the
merged-input path, and the field's lazy `data:` seam can never drift apart.
Member files from the plan (`mutations/inputs.py`, `mutations/sets.py`,
`auth/mutations.py`) all traced; the sweep followed the mechanism
package-wide into the form flavor (`forms/inputs.py`, `forms/sets.py`),
the serializer flavor (`rest_framework/inputs.py`, `rest_framework/sets.py`),
the set families (`sets_mixins.py`, `filters/inputs.py`,
`orders/inputs.py`), the field factory (`mutations/fields.py`), and the
registration seam (`registry.py`).

Attribution pre-check (dirty paths): the ledger (`dry-0_0_15.md`
`## Owned changes`) carries no row for any family core path. Worktree dirt
on `mutations/sets.py` (6 hunks) and `auth/mutations.py` (5 hunks) is the
documented concurrent `__name__`-to-`_safe_class_name` hardening campaign
(plan Drift block + `mutations/sets.py` file-item pending-settle note):
every hunk verified by `git diff HEAD` content to be a label-rendering swap
(or one `_safe_arg_repr` message reword), orthogonal to shape/name logic.
`mutations/inputs.py` + `utils/inputs.py` verified byte-clean vs HEAD.
No path in this item is edited, so no stop arose; relied regions inside
dirty files confirmed disjoint from (or behavior-identical across) the
external hunks (see Freshness).

## Verification

### Matrix

1. Cross-flavor mirroring — searched. Model (`mutations/`), form
   (`forms/`), serializer (`rest_framework/`), and set (`filters/`,
   `orders/`) naming + shape-cache sites all read; findings F1/F2 record
   what is shared vs intentionally separate.
2. Sync/async twins — inapplicable by construction, stated reason: input
   identity is finalize-time (schema-build) synchronous derivation;
   resolvers consume already-materialized classes. No await boundary
   crosses shape computation, naming, ledger, or cache.
3. Derived rather than repeated knowledge — searched via the mechanism
   tokens below. The name is derived once per shape (`mutation_input_shape`
   → `mutation_input_type_name` → `name_set_input_type_name`); the seam,
   the bind, the generator, and the auth rider compose it by name. No
   second spelling of the model/form name derivation exists.
4. Inverse / round-trip pairs — the reverse map
   (`mutation_input_field_specs`) is the separate open family
   `mutation-input-reverse-map`; listed here, not counted.
5. Contracts in another medium — oracles and projections listed under
   Sites; each counted definition excludes them per DRY.md.
6. Enforcement by omission — enumerated: `delete` materializes no input
   by contract (`NON_DELETE_OPERATION_INPUT_KIND.get()` → `None`;
   `input_type_name` raises the typed reject); the plain-form `FORM`
   sentinel is create-shaped; register pins `RegisterInput`. Each has an
   oracle (delete-reject, FORM-seam, RegisterInput-SDL tests). No gap.

### Enumeration

Family-item sweep instrument: `rg` for `mutation_input_shape`,
`MutationInputShape`, `mutation_input_type_name`,
`name_set_input_type_name`, `generated_input_type_name`,
`_shape_build_cache`, and `input_type_name` across
`django_strawberry_framework/`. Every hit lands below.

Definitions (authoritative, count toward challenges):

- D1 — shape record: [inputs.py][mi-inputs]`::mutation_input_shape` +
  `::MutationInputShape` (one computation of selected set, name, key).
- D2 — model name wrapper: [inputs.py][mi-inputs]
  `::mutation_input_type_name` (thin; supplies model base name +
  create-vs-partial decision).
- D3 — shared name spine: [utils-inputs][u-inputs]
  `::name_set_input_type_name` (+ `::generated_input_type_name`
  skeleton, `::pascalize_token` encoder).

Consumers (compose by name; listed, not counted):

- [sets.py][m-sets]`::_materialize_input_for` (shape → cache key via
  `get_or_store_shape_build` on `_shape_build_cache`; hands descriptor
  to `build_mutation_input`; materializes under the class name),
  `::_materialize_merged_input` (same descriptor for the canonical
  merged name; deliberately NOT cached — mutation-specific),
  `::DjangoMutation.build_input` / `::DjangoMutation.input_type_name`
  (seam reads `.type_name`).
- [inputs.py][mi-inputs]`::build_mutation_input` (`shape` param; derives
  when omitted from the same computation).
- `mutations/fields.py` (`input_type_name` + `input_module_path` seams →
  lazy `data:` ref; never spells a name).
- [auth-muts][auth-muts] register `build_input` / `input_type_name`
  (standard shape + generator; only `type_name` re-pinned to
  `RegisterInput`; specs stashed with `password` as `EXCLUDED`).
- `forms/inputs.py::form_input_type_name` + `forms/sets.py`
  `::_form_input_type_name_for` (compose D3; separate 4-tuple cache key
  incl. hook projection on `forms/sets.py::_form_shape_build_cache`).
- `rest_framework/inputs.py::serializer_input_type_name` (composes only
  the D3 skeleton with its own descriptor digest).

Oracles (independent expectations; listed, not counted):

- `tests/mutations/test_inputs.py`: full-shape canonical name,
  narrowed-shape determinism/distinctness, token-boundary non-collision,
  ledger idempotent-dedupe + distinct-class collision raise.
- `tests/mutations/test_sets.py`: bind dedupes identical full shapes
  (`is`-identity), full-spelling dedupe, complementary
  fields/exclude dedupe, merged-vs-generated collision raise, seam ==
  descriptor agreement (full + narrowed), cache co-clear, delete reject.
- `tests/forms/test_inputs.py` + `test_sets.py`, `tests/rest_framework/`
  `test_inputs.py` + `test_sets.py`, `tests/auth/test_mutations.py`
  (`RegisterInput` SDL + ledger), `tests/utils/test_inputs.py`
  (name-set spine).
- Live wire: fakeshop `test_query` suites (input shapes reachable by
  real queries stay covered there per AGENTS.md).

Projections (describe; never own): module docstrings of
`mutations/inputs.py`, `utils/inputs.py`, `forms/inputs.py`,
`rest_framework/inputs.py`; spec-036/038/039 decision prose.

Excluded on body strength: set-family
`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`
(class-derived `FooInputType`, no shape axis — separate grammar, R2);
`filters/inputs.py` range naming (leaf-scoped, R3); payload naming
(open family `mutation-payload-name`); subsystem-clear bus entries
(rejected family `subsystem-clear-lifecycle` — registration, not naming).

### Challenges

Rule under test: one change to input identity moves exactly one
authoritative definition. Consumers/oracles/projections that also move
are listed, not counted.

- C1 — new model-column flavor (or new operation kind). The auth
  register flavor is the lived precedent: it reuses D1 + the generator
  unchanged, re-pinning only `type_name`. A new create-shaped kind is a
  mapping-row declaration (`NON_DELETE_OPERATION_INPUT_KIND`); D1/D2/D3
  do not move. Definitions forced: 0 in the owner (1 declaration row
  at the flavor).
- C2 — renamed mutation class. The generated name derives from the
  MODEL name, never the mutation class name (D2 takes
  `model.__name__`); the mutation name reaches only error labels and
  the payload (`<Name>Payload`, other family). Oracle
  `test_bind_dedupes_identical_full_shapes` (`CreateItemA` vs
  `CreateItemB` → one `ItemInput`, `is`-identical) pins this.
  Definitions forced: 0.
- C3 — two mutations over one model. Same shape → one shared class
  object (per-build `_shape_build_cache` + ledger idempotency; oracles:
  full-shape, full-spelling, complementary-exclude dedupe tests).
  Different shapes → different deterministic names (token suffix;
  oracle: narrowed `!= "ItemPartialInput"`). Same shape with two
  representations (merged vs generated) → fail-loud collision at the
  ledger (oracle:
  `test_bind_merged_and_generated_same_shape_distinct_representations_raise`).
  Definitions forced: 1 (D1).
- C4 — rebuild stability (`registry.clear()` + re-finalize).
  WS probe P1 (execution-verified): same declaration → same name
  (`ItemInput`), same wire field surface, equal-but-new object
  (per-build cache cleared; parked global overwritten in place).
  Stability contract = stable NAME within and across builds;
  object identity within a build only. Definitions forced: 1 (D1).
- C5 — new write flavor over a name set (form precedent).
  `form_input_type_name` reads D3; the per-flavor wrapper supplies base
  name + partial decision. The two wrappers (`!= CREATE` vs
  `== PARTIAL`: the `FORM` sentinel is create-shaped) are declarations,
  not copies — merging them re-spells D3's own parameters.
  Definitions forced: 1 (D3).
- C6 — same-name-set divergence in annotations/requiredness
  (serializer axis). `serializer_input_type_name` keeps its descriptor
  digest + own full-shape decision; only the suffix/branch skeleton is
  shared (D3's `generated_input_type_name`). Intentional separation R1.
  Definitions forced: 1 per side, never together.
- C7 — set inputs gain a narrowing axis. Filter/order inputs name by
  declaring class (`FooInputType` via `type_name_for`); no shape token
  exists there. Unifying with the shape-derived `<Model>Input` grammar
  would couple class identity to field-set identity. Intentional
  separation R2.

## Findings

### F1 — shape record: CONFIRMED single-owned, already-single, no edit

Contract: the identity tuple `(model, operation_kind,
frozenset(effective field names))` is computed once as
`MutationInputShape`; every reader (generator, bind cache key,
materialize name, merged-input name, `data:` seam, auth rider)
takes it from D1. Variation axes: model, operation kind, effective
set; narrowing spelling (`fields` vs `exclude`) is canonicalized away
before identity (C3 oracles).

Owner (principle 7): [inputs.py][mi-inputs]`::mutation_input_shape`.
Responsibility reasoning: every legitimate consumer already depends on
`mutations.inputs` (generator, ledger, specs); seating the record in
`utils/inputs.py` would drag model-column knowledge
(`editable_input_fields`) into the neutral-mechanics module against its
stated mechanics/semantics split, reversing the dependency. Narrowest
cohesive owner every consumer can import without a cycle.

Lifetime (principle 4): `_shape_build_cache` via
`make_shape_build_cache`, owner key `mutations.shape_cache`,
registered into `registry.clear()` (pre-bind); `_materialized_names`
ledger via `make_input_namespace`, cleared by
`clear_mutation_input_namespace` (owner `mutations.input_namespace`,
`before_bind=True`); materialized classes parked in module `__dict__`
and overwritten in place (P1 proved equal-but-new across rebuilds).
Form/serializer caches stay disjoint dicts with their own owner keys
— the guard-before-cache discipline differs per flavor (model: no
per-declaration guard; form: guard-before-lookup; serializer:
post-build key), so one shared dict would couple three invalidation
contracts. No new shared state (principle 4: pure derivation +
flavor-owned caches, already the shape).

Migration: none — all sites already compose D1 by name.

Distinct behavior kept: merged inputs bypass the cache (mutation-
specific representations) and collide loudly on the canonical name;
`delete` has no shape at all.

Behavioral proof: P1 WS probe (rebuild: same name + surface, new
object) — execution-verified, rejects "rebuild mints a new name" and
"rebuild reuses the stale object". Seam-agreement oracle
`test_model_flavor_input_seams_produce_today_defaults` pins
seam == descriptor; P2 proved it fails on a divergent hand-rolled
name (WS `+"X"` mutation → red; byte-identical restore → green).
Shared-tree witness: same test green on the live tree. No new gate:
the plausible bypass (a flavor re-deriving the name) breaks dedupe /
seam-agreement behavior observably, so existing oracles guard it; a
bespoke existence test per helper is the shape DRY.md forbids for an
already-single owner.

### F2 — naming grammar: shared spine confirmed; wrappers and neighbors rejected

Contract: full shape → stable `<Base>Input` / `<Base>PartialInput`;
narrowed shape → deterministic token name that dedupes identical
effective sets and separates distinct ones.

- Shared (already consolidated, verified not inherited):
  `mutation_input_type_name` + `form_input_type_name` both read D3
  (`name_set_input_type_name`: sorted-`pascalize_token` concatenation,
  frozenset full-vs-narrowed comparison, `generated_input_type_name`
  branch). No second spelling of the name-set derivation exists —
  the "generated-input identity rule was noted" trigger from prior
  records resolves to: already single, nothing to consolidate.
- Wrappers stay (rejection, no trigger owed beyond the standing one):
  merging D2 with the form wrapper re-spells D3's parameter list; each
  wrapper carries its flavor's partial decision (`!= CREATE` admits
  future create-shaped kinds; `== PARTIAL` keeps the `FORM` sentinel
  create-shaped). Distinct reasons to change → separate per principle 3.
- R1 — serializer descriptor naming stays separate. Difference:
  identity basis is per-field (annotation/required/kind/source/target/
  description) digest, not a name set; full-shape is an explicit
  caller flag, not a set comparison. Trigger: serializer identity
  collapses to a pure name set (then it reads D3 directly). Home:
  `rest_framework/inputs.py::serializer_input_type_name` docstring
  (already states the D3 boundary).
- R2 — set-family `type_name_for` stays separate. Difference:
  class-derived (`FooFilterInputType`), no shape axis; one declaring
  class → one input. Trigger: a set family gains a narrowing-derived
  name axis (then it reads D3). Home: `sets_mixins.py`
  `::ClassBasedTypeNameMixin` (family `set-type-naming` owns the row).
- R3 — filter range naming (`<Field>RangeInputType`, leaf-scoped)
  stays separate. Difference: names a lookup leaf, not a declaration
  shape. Trigger: range names derive from a field SET rather than one
  field. Home: `filters/inputs.py` range builder.

Coupling: none — zero edits, no import moves.

Freshness: worktree=HEAD blobs `mutations/inputs.py` `fc442047…`,
`utils/inputs.py` `ee31d360…`, `rest_framework/inputs.py`
`9b17d952…`, `sets_mixins.py` `ad8987ea…`,
`tests/mutations/test_inputs.py` `6be1b081…`; dirty-but-attributed
`mutations/sets.py` worktree `936f5ae7…` / HEAD `cffa29e5…`,
`auth/mutations.py` worktree `200805d2…` / HEAD `dbe64995…`,
`forms/inputs.py` worktree `436fcf42…` / HEAD `55614839…`,
`forms/sets.py` worktree `98ef150d…` / HEAD `36ce80b4…`,
`tests/mutations/test_sets.py` worktree `8574a349…` / HEAD
`2dc45288…`. Relied regions in dirty files verified disjoint from
external hunks except `sets.py` identity-label lines (1243/1282),
where the concurrent swap is label-rendering-only and preserves the
shape/name logic byte-for-behavior. Searched population: whole
`django_strawberry_framework/` via the mechanism tokens above.
Any fingerprint change reopens.

## Defects

None opened. The schema-break hazard named in the brief (input-identity
collision across mutations) already has its oracle:
`test_bind_merged_and_generated_same_shape_distinct_representations_raise`
plus the ledger distinct-class raise pinned in
`tests/mutations/test_inputs.py`. No non-duplication bug surfaced while
tracing; the concurrent hostile-name hunks are another item's
pending-settle business (file `mutations/sets.py` row), untouched here.

## Pending execution

None. Both WS proofs are execution-verified (P1 rebuild probe; P2 oracle
green → mutated red → restored green, restore proved by matching
`sha256`). The single authorized shared-tree focused test ran green
(`tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults -n0 --no-cov`).
Gate business deferred with reason: the full `uv run pytest` gate belongs
to the plan's Final test gate item (Worker 0 dispatch); this item's entry
authorizes only the disposable-workspace proofs plus one focused test,
and a zero-edit finding owes no regression sweep.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff vs `ITEM_BASELINE=bb8f7e45…` on
the family paths is empty; `git status --short` names only this new
untracked artifact. No production, test, or doc edit beyond it; no
`## Owned changes` row owed. No ruff run owed (no `.py` touched); the
artifact's link scaffold is validated by the trailing-commas check below.

## Judgment

Mutation-input identity is already single-owned: D1
(`mutation_input_shape`) owns shape, D3 (`name_set_input_type_name`)
owns the name-set grammar, thin per-flavor wrappers declare their
decisions, and the serializer + set families are intentionally separate
grammars with recorded differences, triggers, and homes. Challenges
C1–C7 all count ≤1 definition per change. Verdict: no consolidation;
finding is confirm-and-record. Status `ready-for-verification/1`.

## Independent verification (Worker 2)

Recorded from my own package sweep before reconciling with
`## Findings` above. Sources read first-hand:
`mutations/inputs.py` (full), `utils/inputs.py` (full),
`mutations/sets.py` (bind pair, seams, cache, lifetime),
`auth/mutations.py` (register rider), `mutations/fields.py`
(lazy seam), `forms/inputs.py` (`form_input_type_name`,
generator), `forms/sets.py` (4-tuple cache,
`cached_build_input`), `rest_framework/inputs.py`
(`serializer_input_type_name`, descriptor cache),
`registry.py` + `types/finalizer.py` (clear routing);
oracle bodies `tests/mutations/test_sets.py`
(dedupe/collision/seam/retry arms) and
`tests/mutations/test_inputs.py` (naming arms).

### Own trace: shape record + naming grammar

- D1 — shape record. Exactly one computation of
  `(model, operation_kind, frozenset(effective field names))`:
  `mutations/inputs.py::mutation_input_shape` returning
  `mutations/inputs.py::MutationInputShape` (`selected`,
  `full_field_names`, `effective_field_names`, `type_name`,
  `cache_key=(model, operation_kind, effective frozenset)`).
- D2 — model name wrapper.
  `mutations/inputs.py::mutation_input_type_name`: supplies
  `model.__name__` + `is_partial=(operation_kind != CREATE)`,
  delegates to D3. One body; no second spelling.
- D3 — shared name spine.
  `utils/inputs.py::name_set_input_type_name` (sorted-`pascalize_token`
  concatenation, frozenset full-vs-narrowed comparison) over
  `utils/inputs.py::generated_input_type_name` (suffix/branch
  skeleton) with `utils/inputs.py::pascalize_token` (token
  encoder). `mutations/inputs.py::_pascalize_token` is a bare
  alias binding, not a definition.

Every builder/namer found, with the role I assign:

- Builders that CONSUME D1 (not second shapes):
  `mutations/inputs.py::build_mutation_input` (`shape` param,
  derives via D1 when omitted);
  `mutations/sets.py::_materialize_input_for` (D1 → cache key
  via `get_or_store_shape_build` on `_shape_build_cache`,
  hands descriptor to the generator) +
  `::_materialize_merged_input` (same descriptor for the
  canonical merged name; deliberately uncached);
  `auth/mutations.py` register `build_input` (D1 + generator,
  only `type_name` re-pinned to `RegisterInput`).
- Namers that COMPOSE D3 (not second grammars):
  `forms/inputs.py::form_input_type_name` (form base name +
  `is_partial=(== PARTIAL)`); `forms/sets.py`
  `::_form_input_type_name_for` (thin read-through);
  `rest_framework/inputs.py::serializer_input_type_name`
  (descriptor digest + own full-shape flag; composes only the
  D3 skeleton).
- Sibling flavors, intentionally separate rules (different
  identity basis, not second definitions of this rule): form
  4-tuple cache key `(form_class, operation_kind,
  frozenset(effective), basis-content-identity)` over form
  `base_fields` (not model columns);
  `SerializerInputShape` descriptor identity (per-field
  annotation/required/kind/source/target/description digest).
- Excluded neighbors (different contracts, verified on body
  strength): `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`
  (class-derived `FooInputType`, no shape axis);
  `mutations/inputs.py::build_payload_type` (`<Name>Payload`,
  keyed by mutation name, own open family); filter range
  naming (leaf-scoped); `make_input_namespace` /
  `make_shape_build_cache` / `get_or_store_shape_build` /
  `cached_build_input` / `build_and_stash_input` (shared
  plumbing, not this rule's definition); `INPUTS_MODULE_PATH`
  constants (addresses, not grammars); subsystem-clear bus
  rows (registration, rejected family).
- Sweep result: NO second builder of model-input shape and NO
  second spelling of the name-set derivation anywhere in the
  package. Form 4-tuple key and serializer descriptor are
  sibling-flavor identities over different populations, not
  rival owners of `(model, operation, effective-set)`.

Definition counts per posited change (mine): new flavor /
rename 0; two-over-one-model 1 (D1); rebuild 1 (D1); new
name-set flavor 1 (D3); serializer divergence 1 per side,
never together; set-narrowing N/A (no shared axis).

Owners I would choose (pre-findings): shape at
`mutations/inputs.py::mutation_input_shape` — every
legitimate consumer already depends on `mutations.inputs`,
and seating the record in `utils/inputs.py` would drag
model-column knowledge (`editable_input_fields`) into the
neutral-mechanics module against its stated
mechanics/semantics split; grammar at
`utils/inputs.py::name_set_input_type_name` — neutral,
cycle-free, both model and form depend without sibling
imports. Split stays.

### Item-scoped diff (Worker 0 ground truth checked)

EMPTY confirmed. `git diff ITEM_BASELINE --` on all four
family paths (plus worktree-vs-ITEM) prints nothing;
`mutations/inputs.py` (`fc442047…`) and `utils/inputs.py`
(`ee31d360…`) are byte-identical across ITEM / HEAD /
worktree; `mutations/sets.py` / `auth/mutations.py` dirt
predates ITEM (ITEM→current diff empty there) and is
concurrent, untouched. Zero tracked edits; no
`## Owned changes` row owed. The artifact file itself is the
only new path (`??`, untracked).

### Enumeration check (member by member)

D1/D2/D3 as defined match my sweep exactly; every consumer
listed (`_materialize_input_for`, `_materialize_merged_input`,
`build_input`/`input_type_name` seams, `build_mutation_input`,
fields lazy seam, auth rider, form wrapper + 4-tuple cache,
serializer skeleton-only) is a by-name composer in the
bodies I read; every oracle cited exists at the named path;
all four exclusions verified on body strength (set
`type_name_for`, range naming, payload naming, clear-bus).
No hit from the mechanism tokens is unassigned; no second
definition found. AGREE throughout, no difference.

### Challenges reconciled

- C1 (new flavor 0), C2 (rename 0): AGREE. C2's oracle
  (`CreateItemA` vs `CreateItemB` → one `ItemInput`,
  `is`-identical, body opened) pins model-derived naming.
- C3 (two-over-one → 1, D1): AGREE, with the resolution
  layered as follows. It is BOTH a shape dedupe and a name
  guard, and D1 resolves both because one descriptor yields
  the cache key AND the type name: (a) same effective set
  (any spelling) → `_shape_build_cache` hit on
  `(model, op, frozenset)` → SAME class object reused, the
  ledger sees `(name, cls)` idempotently — oracles
  `test_bind_dedupes_identical_full_shapes` (`is`-identity,
  body opened), `..._full_set_fields_with_bare_create`,
  `..._fields_with_complementary_exclude`; (b) same shape
  with two representations (merged vs generated) → merged
  path bypasses the cache by design → ledger
  distinct-class raise under the canonical name — oracle
  `test_bind_merged_and_generated_same_shape_distinct_representations_raise`
  (body opened). One definition moves on any identity-axis
  change. No difference.
- C4 (rebuild → 1, D1): AGREE — equal-but-new, not same
  object. Caches key by NAME/shape, never by built object:
  `_shape_build_cache` key `(model, op, frozenset)` → class,
  `_materialized_names` key name-string → class; the
  per-pass `cache.clear()` at the bind top plus the
  pre-bind ledger reset rebuild fresh, parked globals
  overwritten in place via `setattr`. No `is` comparison
  spans a rebuild: dedupe `is` arms sit inside one
  finalize; the retry oracle asserts `_input_class is
  _materialized_names[...]` within build 2, not across
  builds. Nothing holds cross-rebuild identity. No
  difference.
- C5 (new name-set flavor → 1, D3), C6 (serializer 1 per
  side never together), C7 (set-narrowing N/A): AGREE on
  all counts and triggers.

### F2 wrappers-stay judged

AGREE — genuinely distinct, not shared-with-flag. The
partial decisions differ on a real vocabulary gap: model
`!= CREATE` over `{CREATE, PARTIAL}` (delete
short-circuits before naming) vs form `== PARTIAL` over
`{CREATE, FORM, PARTIAL}` with the `FORM` sentinel
create-shaped. A merged wrapper would need a FORM-mode
flag — the branch-no-real-path-reaches shape principle 5
forbids — while D3 already holds everything actually
shared. Separate reasons to change (a new create-shaped
model kind breaks `!= CREATE`; dropping `FORM` leaves
`== PARTIAL` correct). Stay separate per principle 3.

### No-gate reasoning judged (F1)

AGREE — same standard as the verified single-owned
siblings (e.g. `subscription-per-event-error-masking`,
`relay-node-name-decode`: no gate where a hand-copy passes
every behavior oracle). The named oracles DO fail a real
divergent bypass: a re-derived name breaks the dedupe
`is` arms (two objects) and the seam narrowed arm, and a
re-derived cache key breaks dedupe or trips a spurious
ledger collision; P2 demonstrated the seam oracle going
red on a `+"X"` divergence and green on byte-identical
restore (logic re-checked against the oracle body: the
narrowed arm compares seam output to the D1 descriptor,
so divergence fails; the literal arms `== "ItemInput"`
/ `!= "ItemPartialInput"` independently pin absolute
names, so the suite does not merely read the owner it
checks). The only bypass that evades them is a
byte-identical copy, which passes by construction — the
exact case DRY.md forbids a bespoke existence test for.
No gate owed; finding is confirm-and-record, not
gate-only.

### Lifetime

AGREE. Shape cache: per-pass `cache.clear()` at the bind
top + `registry.clear()` co-clear (`mutations.shape_cache`;
not a `before_bind` row — the per-pass clear is what makes
retry rebuild fresh); input namespace: `before_bind=True`
row (`mutations.input_namespace`); parked globals
overwritten in place (P1 equal-but-new); flavor caches
three disjoint dicts with distinct owner keys and distinct
guard disciplines (model: none per-declaration; form:
guard-before-lookup; serializer: post-build key +
inline guard-before-dedupe) — one shared dict would couple
invalidation contracts. One wording note (not a defect, no
contract row breaks, no wire input reaches it): F1's
"(pre-bind)" gloss on the shape-cache registration is
loose — the shape cache clears per-pass-top and on full
`registry.clear()`, while only the namespace ledger is a
`before_bind=True` row. Behavior account is exact.

### R1/R2/R3 + matrix

AGREE on all three rejections (difference + trigger + home
each: serializer descriptor digest at
`serializer_input_type_name`; set `type_name_for` at the
`set-type-naming` family; range leaf naming at
`filters/inputs.py`). Matrix axes discharged against the
real surface; axis 2 inapplicable-by-construction reason
(finalize-time sync derivation, no await boundary) judged
sound; axis 6 omission enumeration (delete typed reject,
`FORM` create-shaped, `RegisterInput` pin) each has its
oracle. No unsearched axis, no second-site candidate left
unrouted.

### Freshness re-hashed (Worker 2, current tree)

All ten fingerprints match the artifact record: clean
`mutations/inputs.py` `fc442047…`, `utils/inputs.py`
`ee31d360…`, `rest_framework/inputs.py` `9b17d952…`,
`sets_mixins.py` `ad8987ea…`,
`tests/mutations/test_inputs.py` `6be1b081…` (worktree ==
HEAD == record); dirty-but-attributed `mutations/sets.py`
`936f5ae7…`/`cffa29e5…`, `auth/mutations.py`
`200805d2…`/`dbe64995…`, `forms/inputs.py`
`436fcf42…`/`55614839…`, `forms/sets.py`
`98ef150d…`/`36ce80b4…`, `tests/mutations/test_sets.py`
`8574a349…`/`2dc45288…` (worktree and HEAD both match).
ITEM→current drift (3 files: `rest_framework/resolvers.py`,
`bug_hunt-0_0_15.md`, `test_resolvers.py`) touches no
family site. Relied regions in dirty files confirmed
disjoint from the concurrent hunks (model/form/serializer
spelling, cache keys, seam bodies untouched; `sets.py`
identity-label lines are label-rendering-only). Nothing
stale; nothing reopens.

### Pending execution judged

AGREE — `None` is correct. P1 (rebuild equal-but-new) and
P2 (seam oracle green→red→restore, restore by matching
`sha256`) are execution-verified WS proofs; the one
authorized shared-tree focused witness
(`tests/mutations/test_sets.py::test_model_flavor_input_seams_produce_today_defaults
-n0 --no-cov`) ran green on the live tree at W1 and I
re-ran it in the current (concurrently dirty) tree: 1
passed. Full `uv run pytest` belongs to the plan's Final
gate, not this zero-edit item. No `proof:` entry remains.

### AGENTS.md prose check

Zero production/test/doc edits: no ruff run owed (no `.py`
touched — vacuous pass on worker-2.md item 7). Citations
are `path::Symbol` via the link refs; the 10 canonical
link groups are present; no process provenance (no
worker-memory, no scratch paths; the `ITEM_BASELINE`
mention is empty-diff evidence, not provenance); cited
oracles sit at the mandated `tests/` tier with the live
`test_query` wire tier named. Concurrent dirt preserved;
nothing committed.

### Verdict

No second shape or naming definition exists; owners split
stays (D1 at `mutations.inputs`, D3 grammar at neutral
`utils.inputs`); C3/C4 counts and oracles confirmed
against opened bodies; F2 separation and no-gate reasoning
meet the sibling standard; freshness re-hashed clean;
pending execution empty with the witness re-green. No
defects.

Status: verified (zero edits, no pending execution).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-muts]: ../../django_strawberry_framework/auth/mutations.py
[m-sets]: ../../django_strawberry_framework/mutations/sets.py
[mi-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[u-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

