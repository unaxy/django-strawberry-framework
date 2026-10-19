# DRY review: `mutation-input-reverse-map`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

The reverse map from generated input fields back to their source: field specs
plus the relation-field index, so resolvers and decode map input data back to
model fields. Provisional owner confirmed:
[inputs.py][mi-inputs]`::mutation_input_field_specs` (+
`::_relation_field_index`).

What the target owns: the bind-time derivation of per-input-field reverse
records (`input_attr` -> kind / related model / write target) plus the
Django-field index the decode consults, covering the whole materialized
(possibly merged) input class. Member files from the plan
(`mutations/inputs.py`, `mutations/sets.py`, `auth/mutations.py`) all traced;
the sweep followed the mechanism package-wide into the shared record type
(`utils/inputs.py::InputFieldSpec`), the shared decode spine
(`utils/write_values.py::decode_provided_fields`), the model decode rider
(`mutations/resolvers.py`), the form flavor (`forms/inputs.py`,
`forms/sets.py`, `forms/resolvers.py`), the serializer flavor
(`rest_framework/inputs.py`, `rest_framework/sets.py`,
`rest_framework/resolvers.py`), the budget reader
(`extensions/resource_policy.py`), the relation taxonomy
(`utils/relations.py`), and the sibling validators in `mutations/sets.py`.

Attribution pre-check (dirty paths): the ledger (`dry-0_0_15.md`
`## Owned changes`) carries no row for any family core path. Worktree dirt on
`mutations/sets.py` (the `__name__`-to-`_safe_class_name` label-rendering
swaps) and `auth/mutations.py` (same campaign plus one `_safe_arg_repr`
message reword) is the documented concurrent hostile-name hardening campaign:
every hunk verified by `git diff HEAD` content to touch only error-label
rendering, orthogonal to spec/bind/decode logic. `mutations/inputs.py` was
byte-clean vs HEAD at open and carries only this item's F1 edit now;
`tests/mutations/test_inputs.py` was clean and carries only this item's gate.
Item-scoped diff vs `ITEM_BASELINE=dfe17d62...` on the family paths names
exactly those two files (stat: inputs.py +22/-3, test_inputs.py +31); the
sets.py / auth dirt predates the item baseline, so the item diff is mine
alone and no stop arose.

The exact reverse rule (read first-hand from
[inputs.py][mi-inputs]`::mutation_input_field_specs`):

- every Strawberry field of the materialized input class gets one
  `InputFieldSpec`: `input_attr` = python name, `graphql_name` = the pinned
  alias or `graphql_camel_name(python_name)`, `target_name` = python name
  (the model attr the decode writes), `kind` from the shared classifier,
  `related_model` for relation kinds else `None`;
- a forward FK / OneToOne resolves through the bind index under its
  `<field>_id` attr and decodes to the pk stored under that same attname; a
  scalar (including one literally named `<x>_id`, e.g.
  `library.TaggedItem.object_id`) resolves through `model._meta.get_field`
  and stays under its real name (the M3-1 no-suffix-strip rule); a forward
  M2M resolves under the plain field name and decodes to a pk list;
- `GlobalID` ids decode to pks (type-check + visibility in one
  `decode_visible_relation_ids` compose); raw pks coerce through the target
  pk field; nothing is stored raw;
- `excluded_attrs` (the spec-040 D6 seam, only `password` today) records
  kind `EXCLUDED` without changing `target_name`, so the capture handler
  runs instead of the column handler;
- an attr resolving to no concrete column, or to a virtual relation (a
  `GenericForeignKey` that `get_field` still finds), is a bind-time
  `ConfigurationError`, never a request-time miss; keys are flat (model
  flavor never sets `nested_specs` / `source`).

Every reader of the reverse map (all verified in-body, all compose by name):

- `mutations/resolvers.py::_decode_relations` (via `_model_decode_step`):
  kind-routed decode into model attrs + M2M pk lists + excluded captures;
- `mutations/resolvers.py::_provided_attr_names`: the FK-to-field reversal
  (`model_fields[attr].name`) for the `full_clean(exclude=...)` carve-out;
- `mutations/resolvers.py::_explicit_null_error`: the bind-time column for
  the explicit-null guard;
- `auth/mutations.py::_register_decode_step`: the same model decode plus
  the `password` capture out of construction;
- `extensions/resource_policy.py::_mutation_input_specs`: budget
  classification of list inputs by spec kind (same records the decode
  walks, so the budget cannot disagree with the decode);
- `utils/write_values.py::decode_provided_fields`: the shared
  `spec_by_attr` walk all three write flavors ride.

## Verification

### Matrix

1. Cross-flavor mirroring - searched. The model post-merge walk
   (`mutation_input_field_specs`), the form build-time capture
   (`forms/inputs.py::_field_triple_and_spec`, specs emitted in the same
   loop as the triples), and the serializer build-time capture
   (`rest_framework/inputs.py`, specs from its descriptor walk) all read.
   The record type is already one (`utils/inputs.py::InputFieldSpec`);
   the builders differ by basis (model columns vs form fields vs
   serializer fields) and by extra axes (`target_name` semantics,
   `source`, `nested_specs`). Findings F3/R1/R2 record what is shared vs
   intentionally separate.
2. Sync/async twins - inapplicable by construction, stated reason: the
   reverse map is a finalize-time synchronous derivation stashed at bind;
   resolvers consume the stashed records inside the one sync pipeline
   boundary. No await boundary crosses spec synthesis, the index, the
   stash, or the decode walk.
3. Derived rather than repeated knowledge - searched via the mechanism
   tokens below. The `<field>_id` scheme was spelled twice (F1,
   consolidated); kind classification is composed once (F2); related
   models are read off the resolved Django fields, never re-derived.
4. Inverse / round-trip pairs - this family IS the reverse half of the
   identity family's forward shape (declaration -> input fields, verified
   already-single in `dry-rule-generated-mutation-input-identity.md`;
   re-verified its trigger resolution, not inherited). The passes stay
   separate (different lifetimes and structures, F3); the one shared atom
   is now composed (F1).
5. Contracts in another medium - oracles and projections listed under
   Sites; each counted definition excludes them per DRY.md. Contract
   sources: spec-053 Decision D3 (the bind-stashed-specs + shared-spine
   decode, landed), spec-036 (no `to_field` row: zero hits), spec-038/039
   (flavor reverse-map prose).
6. Enforcement by omission - enumerated: `delete` stashes no specs
   (`_input_field_specs is None` by construction, oracle pins it); virtual
   relations fail loud at spec synthesis (GFK oracles); merged non-column
   attrs fail loud (Rogue oracle); non-pk `to_field` is out of contract
   (C5/R3, no oracle owed). No gap.

### Enumeration

Family-item sweep instrument: `grep` for `mutation_input_field_specs`,
`_relation_field_index`, `InputFieldSpec`, `_input_field_specs`,
`_model_fields_by_attr`, `decode_provided_fields`, `target_name` across
`django_strawberry_framework/`. Every hit lands below.

Definitions (authoritative, count toward challenges):

- D1 - spec builder: [inputs.py][mi-inputs]`::mutation_input_field_specs`
  (total-coverage walk of the materialized class + Django-field index).
- D2 - relation index: [inputs.py][mi-inputs]`::_relation_field_index`
  (forward-FK-by-`<field>_id` / forward-M2M-by-name maps).
- D0 - naming atom (new, this item): [inputs.py][mi-inputs]
  `::relation_input_python_attr` (the `<field>_id`-vs-plain-name scheme;
  D1-adjacent forward triple and D2 both compose it after F1).

Consumers (compose by name; listed, not counted):

- [m-sets][m-sets]`::DjangoMutation.build_input` (stash) +
  `::_expected_input_attr_names` / `::_validate_relation_override_types`
  (compose the forward triple, never the index);
- [auth-muts][auth-muts] register `build_input` (stash with `EXCLUDED`)
  + `_register_decode_step` (read);
- [m-resolvers][m-resolvers] decode rider quartet (read);
- [res-policy][res-policy]`::_mutation_input_specs` (read by
  `graphql_name`);
- [u-write-values][u-write-values]`::decode_provided_fields` (the shared
  walk; `spec_by_attr` built per call, never stored).

Shared-but-elsewhere-owned (consumer role here, never counted here):

- kind classifier `model_column_write_kind` (family
  `model-column-write-classification` owns it);
- record type `InputFieldSpec` ([u-inputs][u-inputs]; spec-038/039
  promotion);
- kind tokens (`SCALAR` et al. at [u-inputs][u-inputs]).

Oracles (independent expectations; listed, not counted):

- [t-inputs][t-inputs]: generated-input coverage (`target_name`,
  `related_model`, index identity), Rogue non-column reject, GFK reject,
  M2M classification, `EXCLUDED` marking, bare-string `excluded_attrs`
  reject, plus the new F1 gate (below);
- [t-sets][t-sets]: bind stash totality (`create_attrs` == built fields),
  `_model_fields_by_attr["category_id"] is get_field("category")`,
  delete stashes `None`;
- [t-resolvers][t-resolvers]: `object_id` M3-1 scalar mapping (provided
  names + `full_clean` attribution), GFK exclusion from the index;
- live wire: [products-api][products-api] + [library-api][library-api]
  (`categoryId` reverse-map writes reachable by real query).

Projections (describe; never own): module docstrings of
`mutations/inputs.py`, `forms/inputs.py`, `rest_framework/inputs.py`,
`mutations/resolvers.py`; spec-036/038/039 decision prose; spec-053 D3
checklist row.

Excluded on body strength: set-family `GeneratedInputFieldSpec`
(filters/orders query-side inputs, different rule); `_validate_input_class`
message prose (mentions the scheme, enforces via composition); form
column-less naming (R1); serializer declared-name/`source` naming (R2);
subsystem-clear bus rows (registration, rejected family).

### Challenges

Rule under test: one change to the reverse mapping moves exactly one
authoritative definition. Consumers/oracles/projections that also move
are listed, not counted.

- C1 - change the relation python-attr scheme (`<field>_id` -> bare
  name). Pre-change definitions forced: [inputs.py][mi-inputs]
  `::relation_input_annotation` (forward triple) AND
  `::_relation_field_index` (reverse keys). Count was **2** (the file
  item's C5 counted 1 - it never examined the index; re-derived fresh
  here, not inherited). Validators and the override lock compose the
  triple (0 edits); oracles move as media. Post-F1 count is **1**
  (D0). WS proof P1/P2.
- C2 - rename a model field (`category` -> `topic`). Both halves read
  live `_meta` at bind (forward walk + index + validator); specs are
  rebuilt every bind and overwritten in place; the shape cache keys on
  the model object, never on names. Definitions forced: **0** - the
  reverse map follows by construction.
- C3 - add a decode kind (a new column class). The classifier
  `model_column_write_kind` gains the arm; the reverse walk composes it
  (0 edits here); handler maps consume the token (listed, not counted).
  Definitions forced: **1** at the classifier (token spelling stays at
  [u-inputs][u-inputs], moves only if the token itself changes).
- C4 - merge a consumer-only attr (non-column override, or a new custom
  field). Forward triples never contain it; only the post-merge walk
  sees it and fails loud (`ConfigurationError`). Definitions forced:
  **1** (D1). This is the load-bearing proof the walk cannot be deleted
  in favor of the forward triples (F3).
- C5 - bind a relation on a non-pk `to_field`. The reverse map records
  only `related_model`; decode is pk-based throughout
  (`decode_visible_relation_ids`); the filter family's pk-marker
  (`filters/base.py::_relation_uses_non_pk_to_field`) is never
  consulted, and no `to_field` path is re-derived either. Definitions
  forced: **0** - unsupported and unpromised (spec-036: zero `to_field`
  hits; no fakeshop fixture; no wire input reaches it). Separation R3
  with trigger, not a defect (no contract row extends the rule here).

## Findings

### F1 - relation python-attr scheme: CONSOLIDATED (was 2, now 1)

Contract: a relation field's generated input attr is `<field.name>_id`
for forward FK / OneToOne and the plain field name for M2M. The forward
triple and the reverse index are two halves of this one grammar (matrix
axis 4): a scheme change moved both spellings
(`relation_input_annotation` line 461 + `_relation_field_index` line 506
at HEAD `bfaee91d`).

Owner (principle 7): [inputs.py][mi-inputs]
`::relation_input_python_attr` (new, pure, models.Field-keyed).
Responsibility reasoning: every legitimate consumer already depends on
`mutations.inputs` (generator, index, validator, override lock); seating
the atom in `utils/inputs.py` would drag model-domain naming
(models.Field-keyed, M2M-aware) into the neutral-mechanics module
against its stated mechanics/semantics split, reversing the dependency.
Narrowest cohesive owner every consumer can import without a cycle.

Lifetime (principle 4): pure derivation, explicitly not cached - called
twice per relation per bind (once at generation, once at indexing) and
never stored. No owner key, no publish point, no invalidation: there is
nothing to go stale, which is exactly why the two former spellings could
drift silently.

Migration: `relation_input_annotation` composes the atom for its triple;
`_relation_field_index` composes it for both dict keys. Validators
(`_expected_input_attr_names`, `_validate_relation_override_types`)
already composed the triple and move 0. Form column-less naming stays
separate (R1).

Distinct behavior kept: none changed - byte-identical outputs on every
oracle (P1). The `many` local in `relation_input_annotation` still feeds
the annotation wrap; only the attr spelling moved.

Behavioral proof: P1 WS execution-verified - `test_inputs.py` 76/76
green plus the neighbor oracles `test_sets.py` + `test_resolvers.py` +
`forms/test_inputs.py` + `auth/test_mutations.py` 335/335 green on the
consolidated tree (rejects "the index keys diverge" and "the triple
diverges"). Shared-tree witness: the new gate green on the live tree.
No behavior delta exists to observe beyond the gate.

Structural gate: `test_relation_naming_scheme_is_single_sited`
(diversion test) - monkeypatches the atom to a `_zz` suffix and asserts
the built triple AND both index arms follow. Negative control P2 proved
in WS: behavior-preserving hand copies of the old inline spellings at
both sites -> gate red (`category_id` vs `category_zz`) while every
behavior oracle still passed (the copy is correct); restore proved by
matching `git hash-object` (`fcbb964d...`) -> 76/76 green. The gate
fails a bypass of the owner and nothing else.

Coupling: none - same-file edit, no import moves, no ledger collision
(the ledger has no row on this path; concurrent hostile-name hunks in
`sets.py`/`auth/mutations.py` touch disjoint lines).

Freshness: `mutations/inputs.py` HEAD `fc442047...` / worktree
`fcbb964d...` (this F1 edit, +22/-3); `tests/mutations/test_inputs.py`
HEAD `6be1b081...` / worktree `91f9460a...` (the gate, +31). Relied
regions in dirty files verified disjoint from the concurrent hunks
(spec/index/decode bodies untouched; `sets.py` + `auth/mutations.py`
hunks are label-rendering only). Searched population: whole
`django_strawberry_framework/` via the mechanism tokens. Any
fingerprint change reopens.

### F2 - kind classification: CONFIRMED already-single, no edit

Contract: a backing column classifies to `scalar` / `relation_single` /
`relation_multi` / `file` (+ model-only `excluded`) one way. The reverse
walk composes `model_column_write_kind` by name (family
`model-column-write-classification` owns it); C3 counts 1 at that
classifier. No second classification of a model column exists anywhere
in the package (the form column arm composes the same body; the
column-less paths classify model-less fields, a different basis).
Verdict: confirm-and-record; any gate belongs to the owning family,
not here.

### F3 - post-merge walk vs forward triples: CONFIRMED intentional, no edit

Contract difference (why both halves must exist): the forward triples
are an ephemeral build argument (generated remainder only, overrides
skipped, never stored); the reverse specs are a stored per-bind
derivation over the MERGED class (consumer fields included) with a
fail-loud totality contract (Rogue/GFK rejects). Different lifetimes
(triples die with the build; specs live bind-to-bind on the class) and
different structures (annotations + requiredness vs kinds + related
models + total coverage). C4 proves the walk is load-bearing: deleting
it in favor of the triples loses the merged-field verdicts. The form
and serializer flavors show the alternative shape working where it
applies (build-time capture, same loop as the triples) - the model
flavor cannot use it because its consumer half arrives as an opaque
`@strawberry.input`, not as flavor fields. Verdict: reject
consolidation of the passes; the shared atom inside them is F1.
Lifetime (principle 4) for the stored half: owner = the mutation class
(`_input_field_specs` / `_model_fields_by_attr`); validity key = the
bind that stashed them (phase-2.5 of the current finalize, overwritten
every `bind_write_declarations` pass; `delete` stays `None` by
construction); no explicit clear is owed because no decode can run
between `registry.clear()` and the re-bind that re-stashes; parked
input classes are overwritten in place like the forward ledger.

### R1 - form column-less `<name>_id` spelling stays separate

Difference: keyed on the form's declared field NAME (a `str`), with no
`models.Field` in reach (`relation_input_python_attr` is Field-keyed by
design); the reuse of the 036 suffix is a documented uniformity choice
at [f-inputs][f-inputs]`::_model_less_relation_annotation`, not a
necessity - the form path could drop the suffix while the model keeps
it (separate reasons to change, principle 3). Trigger: the scheme
re-expressed over `(name, many)`, or the column-less path gaining a
backing column (then it rides `model_column_input_annotation` and the
separation evaporates). Home: that function's docstring (already states
the reuse).

### R2 - serializer declared-name / `source` naming stays separate

Difference: the reverse map preserves the DECLARED serializer field name
(`category_pk`) with the `source` axis for DRF mapping plus
`nested_specs` recursion - a different identity basis (per-field
descriptor digest, family `model-column-write-annotation` row) and a
different naming rule (id-like-suffix, spec-039). Trigger: serializer
identity collapses to model-column naming (then it reads the model
walk). Home: [rf-inputs][rf-inputs] builder prose.

### R3 - non-pk `to_field` handling stays absent (separation, not defect)

Difference: the filter family promises GlobalID-correctness on
`to_field` relations via its pk-marker; the mutation reverse map
promises pk-joined relations only (implicit - nothing states otherwise,
nothing promises more). C5 establishes it: neither consultation nor
re-derivation, 0 definitions move. Trigger: a mutation-write contract
for `FK(to_field=...)` (then the reverse/decode must consult the
pk-marker or re-derive the column path, and a fakeshop fixture must
exist first). No defect opened: no spec-036 row extends the rule here,
no fixture exists, no wire input reaches it (GOAL.md trust boundary).

### R4 - set-family input specs stay separate

Difference: `filters`/`orders` `GeneratedInputFieldSpec` names
query-side set inputs (`FooFilterInputType`, class-derived, no
model-write basis). No shared axis with the write reverse map.
Trigger: a set family gains a model-write decode (then it reads
`InputFieldSpec`). No home edit owed beyond this row.

## Defects

None opened. While tracing, the only behavior-shaped observation was the
C5/R3 `to_field` absence, which fails the defect bar (no contract row,
no fixture, no reaching input) and is recorded as a separation with
trigger instead. The concurrent hostile-name hunks are another item's
pending-settle business, untouched here.

(Worker 2: no additional defects. The `sets.py` / `auth/mutations.py`
worktree hunks were re-diffed against HEAD in this pass: every hunk is
the hostile-name campaign (`__name__` to `_safe_class_name`,
`_safe_arg_repr` message rewords, one import); no spec, index, decode,
or naming body is touched. The `register_mutation` protected-field
message reword drops the raw `protected` interpolation for the
safe-rendered list, which is the campaign's stated purpose, not a
behavior defect of this family.)

## Pending execution

None. WS proofs P1 (consolidation green: 76 + 335) and P2 (negative
control red-then-restore-green, restore by matching `git hash-object`)
are execution-verified; the single authorized shared-tree focused test
(`tests/mutations/test_inputs.py::test_relation_naming_scheme_is_single_sited
-n0 --no-cov`) ran green on the live tree. Gate business deferred with
reason: the full `uv run pytest` gate belongs to the plan's Final test
gate item (Worker 0 dispatch); this item's entry authorizes only the
disposable-workspace proofs plus one focused test, and the consolidation
is covered by the existing oracle tiers in WS.

## Judgment

The reverse map is one stored derivation (D1 + D2) over a shared record
type, composing the shared kind classifier, with a single two-spelling
defect in the relation naming atom - now consolidated to D0 with a
proved structural gate. The forward pass and the reverse pass stay
separate (different lifetimes, different structures, merged-input
totality), the kind/record owners stay where they are, and the form,
serializer, set-family, and `to_field` separations carry contract
differences with triggers. Verdict: partial consolidation + confirmed
rejections. Status `ready-for-verification/1`.

## Implementation (Worker 1)

Tracked changes (2 files, same change as the finding):

- `django_strawberry_framework/mutations/inputs.py` - new
  `relation_input_python_attr` owner + 2 compose sites
  (`relation_input_annotation`, `_relation_field_index`) + 1 docstring
  composition note. Net +22/-3.
- `tests/mutations/test_inputs.py` - gate
  `test_relation_naming_scheme_is_single_sited` (+31; ruff removed the
  unused direct import, the gate addresses the module attribute).

Item-scoped diff vs `ITEM_BASELINE=dfe17d62...` names exactly these two
files; `git status --short` adds only this new untracked artifact.
`## Owned changes` row owed at verification (Worker 0 appends):
`django_strawberry_framework/mutations/inputs.py` - Family
`mutation-input-reverse-map` - `relation_input_python_attr` (new owner;
`relation_input_annotation` + `_relation_field_index` compose);
`tests/mutations/test_inputs.py` - same family - gate test. After edits:
`uv run ruff check --fix` + `uv run ruff format` clean on both paths
(1 unused-import fix applied by ruff), `format --check` + `ruff check`
pass, `scripts/check_trailing_commas.py --check` exit 0 on both paths.
No commit (maintainer commits).

Scratch: disposable WS
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/reverse-map`
(copy of the live tree per DRY.md Tests; docs/ excluded) - execution
proofs ran there with package `__file__`
`.../dry-ws/reverse-map/django_strawberry_framework/__init__.py` and DB
`NAME` `.../dry-ws/reverse-map/examples/fakeshop/db.sqlite3` recorded
before any verdict; saved byte-copy
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/inputs_consolidated.py`
for the P2 restore proof. Removal by explicit path is Worker 0's at
`verified`.

## Independent verification (Worker 2)

Trace derived from the HEAD and worktree bodies before this artifact's
`## Findings` was opened; reconciled after. Citations are
`path::Symbol` with no line numbers.

### Own pre/post account (C1 2 to 1)

The forward shape is [mi-inputs][mi-inputs]`::relation_input_annotation`:
it maps one relation field to its `(python_attr, graphql_name,
annotation)` triple. The reverse index is [mi-inputs][mi-inputs]
`::_relation_field_index`: it maps a model to `(fk_by_attr,
m2m_by_name)`, the input-attr-keyed Django-field maps the spec walk
reads. The naming atom D0 is [mi-inputs][mi-inputs]
`::relation_input_python_attr` (new, this item).

PRE (HEAD `bfaee91d`, whose blobs equal the item-baseline blobs for
both touched paths): the triple spelled `field.name if many else
f"{field.name}_id"` while the index spelled `field.name` on its M2M
arm and `f"{field.name}_id"` on its FK arm. Two independently
maintained namings of the spec-036 scheme: one scheme change (bare
name, another suffix) forces both bodies. Count 2. The file item's C5
counted 1, but its C5 names the triple alone and never examines the
index (confirmed at `dry-file-mutations__inputs.md` C5), so the 2 here
is re-derived, not inherited.

POST (worktree): the triple composes D0 for its attr, and the index
composes D0 on BOTH arms (M2M plain-name arm included, so the M2M
half of the scheme is consolidated too, not just the `_id` half). A
package-wide grep for remaining inline spellings finds exactly one
`field.name}_id` hit: D0's own return. Nothing passes pre-computed
attr strings around D0; all three code sites pass Django fields.
Count 1. The forward triple plus the reverse index compose D0.

### Builders and readers (own inventory)

Generator chain: `build_mutation_input` via
`model_column_input_annotation` (relation arm calls the triple).
Bind stash: [m-sets][m-sets]`::DjangoMutation.build_input` stashes
`_input_field_specs` + `_model_fields_by_attr` from [mi-inputs][mi-inputs]
`::mutation_input_field_specs`; [auth-muts][auth-muts] register
`build_input` rides the same walk with the `EXCLUDED` seam.
Validators compose the triple by name (never the index):
`::_expected_input_attr_names` (python-attr arm) and
`::_validate_relation_override_types` (attr plus annotation core and
depth arms). Decode: [m-resolvers][m-resolvers] `_decode_relations`
quartet via [u-write-values][u-write-values]`::decode_provided_fields`
(the shared kind-routed walk; `spec_by_attr` built per call, never
stored), with `_provided_attr_names` and `_explicit_null_error`
reading the stashed field map. Policy: [res-policy][res-policy]
`::_mutation_input_specs` reads the same stashed records. Classifier
`model_column_write_kind`, record type `InputFieldSpec`, and kind
tokens are shared-but-elsewhere-owned: consumers here, counted at
their owning families, never here.

### Definitions, roles, owner (own choice)

D1 specs-walk, D2 relation index, D0 naming atom: three roles, and
after F1 exactly one naming definition. The owner I would choose is
D0 at [mi-inputs][mi-inputs]: every legitimate consumer already
depends on `mutations.inputs`, while seating a `models.Field`-keyed,
M2M-aware naming rule in `utils/inputs.py` would drag model-domain
naming into the neutral-mechanics module against its stated split and
reverse the dependency, so dependency direction wins over narrowness.
Lifetime: pure derivation, explicitly not cached (called twice per
relation per bind, never stored; nothing to go stale, which is why
the two former spellings could drift silently). Stored half lives on
the mutation class (`_input_field_specs` / `_model_fields_by_attr`),
validity key the bind that stashed them. Same owner, same lifetime:
agree.

### Challenges and findings judged

C1 agree (2 to 1, proved at the bodies above). C2 agree (0: both
halves read live `_meta` at bind; specs rebuilt and overwritten every
bind; the shape cache keys on the model object, never on names).
C3 agree (1 at the classifier; the walk composes it). C4 agree (1 at
D1: the Rogue non-column oracle rejects at the post-merge walk only,
which is the load-bearing proof the walk cannot be deleted in favor
of the forward triples). C5 agree (0: `to_field` unsupported and
unpromised; zero spec-036 hits, no fixture, no wire input reaches
it).

F1 CONSOLIDATED agree (forward triple plus reverse index compose D0;
+22/-3; structural gate below). F2 agree (already-single; the walk
composes the classifier; any gate belongs to the owning family, not
here). F3 agree (passes stay separate: ephemeral build triples over
the generated remainder versus stored per-bind specs over the merged
class with fail-loud totality; C4 carries the proof). R1 agree (form
column-less naming keyed on a declared-name string with no field in
reach; separate reasons to change; trigger stated at the function).
R2 agree (serializer declared-name, `source`, nested basis; different
identity and naming rule). R3 agree (separation with trigger, not a
defect: no contract row extends the rule here, so the GOAL.md trust
boundary of contract row plus feasible shape plus reaching input is
not met). R4 agree (set-family `GeneratedInputFieldSpec` is
query-side with no shared axis). No defects.

### Gate judged (re-ran P2 fresh)

Tier correct: `tests/mutations/test_inputs.py` is the mandated
package tier for a construction-time structural pin that no real
query can express (the live [products-api][products-api] and
[library-api][library-api] oracles cover the behavior). The gate pins
singularity, not existence: it monkeypatches D0 to a `_zz` suffix and
asserts the built triple AND both index arms follow, so a
hand-inlined copy at either site ignores the diversion and fails.
P2 was re-run in a FRESH workspace copy
(`reverse-map-w2` under the scratch `dry-ws` root; package `__file__`
and database `NAME` both resolved from inside the copy to the copy,
never the shared tree): gate green pre-mutation; hand copies of the
old inline spellings at all three compose sites turned the gate red
(`AssertionError` on the diverted attr) while 75 of 75 behavior
oracles stayed green (the copy is correct); restore by file copy
re-hashed to the worktree blob and returned 76 of 76 green. P1
neighbors were re-run in the same copy: 335 of 335 green. The focused
gate also runs green on the shared tree. Gate accepted.

### Freshness and pending execution

Re-hashed: worktree `mutations/inputs.py` and
`tests/mutations/test_inputs.py` blobs match this artifact's record
and the current baseline stash object; HEAD blobs equal the item
baseline blobs, so the item-scoped diff is worktree-only, exactly the
two files, and every hunk in them is this item's (new atom, two
compose sites, one docstring composition note, one gate test). The
`sets.py` / `auth/mutations.py` dirt is concurrent, disjoint, and
untouched. `## Pending execution` as stated (none) is adequate:
naming is construction-time, the WS 76 plus 335 plus the shared-tree
focused run cover the consolidation, and the full `uv run pytest`
gate belongs to the plan's Final test gate item. No `proof:` entry
remains, so the item is `verified` without a pending-execution mark.

### Prose and layout checks (run in this pass)

`uv run ruff format --check` and `uv run ruff check` pass on both
touched paths; `scripts/check_trailing_commas.py --check` exits 0 on
both. The diff carries no process provenance, cites symbols by
`path::Symbol`, and the gate sits at the mandated package tier (a
structural pin unreachable from a real query; behavior stays covered
at the live wire oracles named above). Verdict: `verified`. The
`## Owned changes` ledger row is owed at plan update (Worker 0
appends).


<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-036]: SPECS/spec-036-mutations-0_0_11.md
[spec-038]: SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-053]: SPECS/spec-053-boundary_dry_squeeze-0_0_15.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-muts]: ../../django_strawberry_framework/auth/mutations.py
[f-inputs]: ../../django_strawberry_framework/forms/inputs.py
[m-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[m-sets]: ../../django_strawberry_framework/mutations/sets.py
[mi-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[res-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[u-inputs]: ../../django_strawberry_framework/utils/inputs.py
[u-write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[t-inputs]: ../../tests/mutations/test_inputs.py
[t-resolvers]: ../../tests/mutations/test_resolvers.py
[t-sets]: ../../tests/mutations/test_sets.py

<!-- examples/ -->
[library-api]: ../../examples/fakeshop/test_query/test_library_api.py
[products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
