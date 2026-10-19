# DRY review: `django_strawberry_framework/forms/converter.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below terminates in a reused family row (trigger re-checked fresh, never
inherited), a file-local record with its proving challenge, or a recorded
rejection with contract difference + trigger + durable home. Zero production
edits; zero tracked files changed.

## System trace

Small target (292 lines, 28 top-level statements): the model-less
`forms.Field`-keyed registry mapping a plain-form field to its Strawberry
annotation + required-ness + decode kind. It DEFINES the model-less scalar
table (`converter.py::_SCALAR_FORM_FIELDS`, 12 rows), the kind-precheck order
(`converter.py::convert_form_field` isinstance list), the exact-type
bare-`Field` special case (`converter.py::_bare_form_field`), the raising
fallthrough (`converter.py::_unsupported_form_field`), the single
requiredness decision (`converter.py::form_field_required` with the
`NullBooleanField` column-backed variations), and the value-object subclass
(`converter.py::FormFieldConversion`). It CONSUMES the dispatch skeleton
(`utils/converters.py::convert_with_mro`), the value-shape makers
(`utils/converters.py::make_scalar_converter` /
`utils/converters.py::make_kind_converter` /
`utils/converters.py::finish_field_conversion`), the kind vocabulary + base
shape (`utils/inputs.py::SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` /
`FILE` / `FieldConversionBase`), and the hostile-safe renderers
(`exceptions.py::_safe_type_name` / `exceptions.py::_safe_arg_repr`). It
ENFORCES the fail-loud dispatch at `convert_form_field` call time. The
module docstring's load-bearing claims were verified against the bodies and
live Django 6.1 MROs: no base-`Field` catch-all row (P2 census: `forms.Field`
absent from the 12 keys; P3: custom subclass raises), precheck-last ordering
of the exact-type case (body order read), parent-subclass hazards named
exactly (`FloatField` / `DecimalField` under `IntegerField`, `UUIDField` /
`JSONField` under `CharField`, `ModelChoiceField` et al under `ChoiceField`
all confirmed via live MRO probe).

Connected code read for judgment, outside the item:
`django_strawberry_framework/types/converters.py` (full read; `SCALAR_MAP`
26 `models.Field` keys, `scalar_for_field` / `convert_scalar` /
`convert_choices_to_enum` ownership incl. the `BigAutoField -> int` START.md
boundary); `django_strawberry_framework/scalars.py`
(`_PACKAGE_SCALAR_MAP` 1 scalar-type key; prior J2 census cross-checked);
`django_strawberry_framework/rest_framework/serializer_converter.py`
(full registry + precheck + `resolve_serializer_field` read; 16
`serializers.Field` keys; model-backed delegation by name);
`django_strawberry_framework/utils/converters.py` (full read; skeleton +
value-shape owner); `django_strawberry_framework/utils/inputs.py`
(kind + `FieldConversionBase` + `InputFieldSpec` owner, relevant regions);
`django_strawberry_framework/forms/inputs.py` (build-site regions:
`_model_column_for`, `_field_triple_and_spec`, required-field discovery,
shape-identity projection); `django_strawberry_framework/forms/resolvers.py`
(decode-kind consumer regions) + `forms/sets.py` (reverse-map consumer
region); `django_strawberry_framework/forms/__init__.py` (projection);
`django_strawberry_framework/exceptions.py` (full read; `_safe_*` helpers
composed by name, `describe_value` scope clause);
`django_strawberry_framework/mutations/inputs.py`
(`model_column_input_annotation` / `model_column_write_kind` /
`model_column_write_annotation` / `annotate_queryset_relation` regions);
`tests/forms/test_converter.py` (337 lines, oracle inventory);
`tests/forms/test_inputs.py` (build-site oracle regions);
`tests/utils/test_converters.py` (skeleton hostile-walk oracle regions);
`docs/SPECS/spec-038-form_mutations-0_0_12.md` (Decision 7 contract source);
`docs/GLOSSARY.md` (`DjangoFormMutation` entries) + `CHANGELOG.md`
(form-mapping row) (projections).

## Verification

### Matrix

Each axis searched against the target's REAL surface (probes P1--P5,
all read-only, all green; commands under `### Challenges`).

1. **Cross-flavor policy mirroring.** Searched, not assumed unique.
Table census fresh from this side (P2): `SCALAR_MAP` 26 keys, all
`models.Field` subclasses; `_PACKAGE_SCALAR_MAP` 1 key (scalar type, not
a field); `_SCALAR_FORM_FIELDS` 12 keys, all `forms.Field` subclasses;
`_SERIALIZER_FIELD_CONVERTERS` 16 keys, all `serializers.Field`
subclasses; all four key spaces pairwise disjoint. Behavior compared
first, not shape: the read side maps a *backing column* to a scalar with
choice substitution layered by callers; this table maps a *column-less
form field* to annotation + decode kind with relation/file annotations
deferred to the build site (`annotation=None`, P5); the serializer twin
maps a *column-less serializer field* with its own nested-serializer
kinds, `is_input` parity parameter, and consumer-registration hook this
file deliberately lacks. `Upload` reaches no flavor by table row: the
form build site finalizes `FILE` to `Upload` (`forms/inputs.py`
`_field_triple_and_spec` column-less arm), the read side keeps file
columns `str` in `SCALAR_MAP`. What SHOULD be shared already is: the
dispatch skeleton (`utils/converters.py::convert_with_mro`, separate key
spaces), the value shape (`FieldConversionBase` + `make_*_converter`,
P5 `is`-proofs), the kind vocabulary (single-sourced in
`utils/inputs.py`, P5 `is`-proofs), and model-backed columns delegating
to the read side by name at the build site (`_field_triple_and_spec`
column arm -> `model_column_input_annotation` -> `convert_scalar`,
read). Verdict: one rule per surface; see J2.
2. **Sync/async twins.** Discharged inapplicable by construction.
Instrument (P1): zero `AsyncFunctionDef`, zero ORM access, zero await.
Pure in-memory dispatch over field instances; the async form-resolver
pipeline (`forms/resolvers.py`) consumes the converter's *output kinds*,
it does not re-implement the mapping, so there is no colored twin to
compare.
3. **Derived rather than repeated knowledge.** Searched. Requiredness is
derived once: `form_field_required` is the single decision consumed at
the annotation path (`_null_boolean_converter`, `_scalar_converter` /
`_kind_converter` via `required_of`), the build site
(`_field_triple_and_spec` both arms), required-field discovery, and the
shape-identity projection (all list `form_field_required` by name;
consumers, counted once under C3). The reverse-map record is constructed
exactly once per field at the build site (`InputFieldSpec(` count in
this file is 0). Scalar annotations are the table itself, stated once;
no second site derives `forms.Field` -> annotation (full-package grep:
one `def convert_form_field`, one `_SCALAR_FORM_FIELDS`).
4. **Inverse / round-trip pairs.** The pair (field -> kind here;
kind -> form payload in `forms/resolvers.py` via `InputFieldSpec`) shares
one grammar: the kind constants are `is`-identical to
`utils/inputs.py` (P5), and the scalar/relation/file store-into-dest
handlers are the shared `utils/write_values.py::decode_field_handlers`.
One grammar, two halves, correctly separated: this module owns the
encode half's table + order, the resolver owns the decode, neither
restates the kind vocabulary. No second grammar here.
5. **Contracts restated in another medium.** Counted 1 definition per
rule; everything else classified: module docstring + `forms/__init__.py`
subsystem prose (projections, verified clause-by-clause incl. all MRO
claims); `CHANGELOG.md` form-mapping row + `GLOSSARY.md`
`DjangoFormMutation` entries (projections); `tests/forms/test_converter.py`
rows (oracles spelling literals: 17-case scalar parametrize, MRO
under-parent rows, JSON-not-`str` row, exact-vs-subclass NullBoolean
rows, bare-`Field` row, custom-subclass raise row, hostile-repr row,
column-backed requiredness matrix, precheck-subclass rows, unsupported
quartet row); `tests/forms/test_inputs.py` rows (oracles for the
build-site-finalized id types the converter deliberately leaves
`None`); spec-038 Decision 7 (contract source: model-less case,
fail-loud shape, key-space separation). No medium holds an independently
maintained copy of any rule.
6. **Enforcement by omission.** Family enumerated, each absence checked
against a contract source. `DurationField` / `MultiValueField` /
`SplitDateTimeField` / `ComboField` raise: the GOAL-mandated fail-loud
default, oracle-pinned, no spec/glossary row requiring a mapping
(spec-038 names no `DurationField`; adding a row changes what is
accepted, never behavior-preserving) -- not a gap. `FileField` /
`ImageField` absent from the scalar table: intentional, the kind
prechecks own them (P2 absence + P3 `FILE` proof) -- not a gap.
`TypedChoiceField` / `FilePathField` / `GenericIPAddressField` have no
own rows: intentional MRO inheritance under `ChoiceField` / `CharField`
(parity, oracle-pinned) -- not a gap. Exact-`NullBooleanField` forced
optional vs validating-subclass-keeps-requiredness: both branches
oracle-pinned with live form-validation cross-checks -- not a gap.

### Enumeration

Instrument: `ast` dump of `ast.Module.body` (probe P1,
`docs/dry/temp-tests/dry-file-forms__converter/p1_ast_census.py`), count
28. Every member lands below; R = file-local finding, F = reused family
row (non-membership checked), J = recorded rejection.

| # | Member | Kind | Home |
|---|---|---|---|
| 1 | module docstring | projection | R1/R2/R3/R4/R5 prose verified |
| 2 | `from __future__` | machinery import | R consumer |
| 3 | `import datetime` | annotation import | R1 consumer |
| 4 | `import decimal` | annotation import | R1 consumer |
| 5 | `import uuid` | annotation import | R1 consumer |
| 6 | `typing.Any` import | annotation import | R consumer |
| 7 | `import strawberry` | engine import | R1 consumer (`JSON`) |
| 8 | `django.forms` import | key-space import | R1/R2 consumer |
| 9 | `ConfigurationError`, `_safe_arg_repr`, `_safe_type_name` import | helper imports | R3 consumers (F non-member) |
| 10 | `MRO_CONTINUE`, `convert_with_mro`, `finish_field_conversion`, `make_kind_converter`, `make_scalar_converter` import | skeleton + value-shape imports | R1/R2/R5 consumers (owners in `utils/converters.py`) |
| 11 | `FILE` re-export | kind re-export | R6 |
| 12 | `RELATION_MULTI` re-export | kind re-export | R6 |
| 13 | `RELATION_SINGLE` re-export | kind re-export | R6 |
| 14 | `SCALAR` re-export | kind re-export | R6 |
| 15 | `FieldConversionBase` import | shape import | R5 consumer (owner in `utils/inputs.py`) |
| 16 | `FormFieldConversion` | conversion subclass | R5 |
| 17 | `form_field_required` | requiredness decision | R4 |
| 18 | `_null_boolean_converter` | NullBoolean arm | R4 |
| 19 | `_scalar_converter` | table-value factory | R5 (thin wrapper) |
| 20 | `_kind_converter` | precheck-value factory | R5 (thin wrapper) |
| 21 | `_SCALAR_FORM_FIELDS` | scalar table (12 rows) | R1 (+ J2 member) |
| 22 | `_bare_form_field` | exact-type special case | R3 |
| 23 | `_CONVERT_RELATION_MULTI` | kind precheck value | R2 |
| 24 | `_CONVERT_RELATION_SINGLE` | kind precheck value | R2 |
| 25 | `_CONVERT_FILE` | kind precheck value | R2 |
| 26 | `_CONVERT_MULTIPLE_CHOICE` | kind precheck value | R2 |
| 27 | `convert_form_field` | dispatch entry | R1/R2/R3 (composes all three) |
| 28 | `_unsupported_form_field` | fallthrough factory | R3 |

No member unassigned. Prior-cycle trigger note: the scalars-item J2
table already records member 21 as one of four per-surface tables; it
was re-derived fresh from this side (probe P2: 26/1/12/16 disjoint key
spaces + contract comparison) and the rejection is CONFIRMED below, not
inherited.

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, not counted. Executed
probes are read-only files under
`docs/dry/temp-tests/dry-file-forms__converter/` run with `uv run python`
from the repo root; NO shared-tree pytest, NO source mutation (so no
workspace copy was owed), NO database opened by any probe (minimal
in-memory Django settings for field instantiation only).

| Id | Change posited | Definitions forced | Consumers/oracles/projections moving along (not counted) |
|---|---|---|---|
| C1 | map a new forms scalar (e.g. `DurationField` -> `str`) | **1** (this table; serializer twin's own `DurationField` row is a disjoint key space with its own wire contract and does not move) | converter oracles gain a row |
| C2 | change one row's scalar (e.g. `UUIDField` -> `str`) | **1** (the row) | scalar parametrize oracle |
| C3 | change the NullBoolean requiredness rule | **1** (`form_field_required`; annotation path + build site + discovery + shape projection follow as consumers) | requiredness-matrix + subclass oracles, build-site oracles |
| C4 | change the NullBoolean annotation to match requiredness | **1** (`_null_boolean_converter`; the "forced `False`" docstring shorthand is projection) | NullBoolean annotation oracles + SDL row |
| C5 | route a new forms relation/file class (e.g. custom `ModelChoiceField` sibling) | **1** (precheck list; build-site finalization follows as consumer; model-backed kind via `model_column_write_kind` is a separate population keyed on `models.Field` and does not move for a forms-only class) | kind-flag oracles, id-type oracles |
| C6 | respell a kind constant | **0 here** (owned by `utils/inputs.py`; the four re-exports follow) | resolver + builder consumers |
| C7 | change the `(annotation, kind, required)` shape | **0 here** (owned by `utils/inputs.py::FieldConversionBase`; both flavor subclasses inherit) | flavor tables |
| C8 | change the MRO-walk mechanics | **0 here** (owned by `utils/converters.py::convert_with_mro`) | all three riding converters |
| C9 | unify all converter tables into one map | **refused** (J2: four key spaces, four contracts) | -- |
| C10 | merge `FormFieldConversion` into `SerializerFieldConversion` | **refused** (R5: NullBoolean `required_of` is form-only; shape already shared via the base) | -- |

Probe commands + what each proved (every probe `execution-verified`):

- `uv run python docs/dry/temp-tests/dry-file-forms__converter/p1_ast_census.py`
  -- 28 members, 0 async, 1 class def (matrix axis 2 +
  enumeration instrument). `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__converter/p2_table_census.py`
  -- key-space populations (26/1/12/16), pairwise disjointness, form
  table file-row absence, `BigAutoField -> int` vs 64-bit -> `BigInt`
  read-side pins. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__converter/p3_dispatch.py`
  -- 17 scalar rows + JSON + 2 multi-choice; 4 kind prechecks with
  `annotation=None`; bare-`Field` -> `str`; custom subclass raises with
  the exact message; 5 precheck-subclass resolutions; unsupported
  quartet raises; hostile `__repr__` still typed. `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__converter/p4_requiredness.py`
  -- 12-cell requiredness matrix; exact-NullBoolean `bool | None` +
  forced-optional; validating-subclass `bool` + required.
  `execution-verified`.
- `uv run python docs/dry/temp-tests/dry-file-forms__converter/p5_kind_identity.py`
  -- four kind `is`-identities (form + serializer -> `utils/inputs.py`);
  both conversion subclasses share `FieldConversionBase`;
  `annotation=None` exactly for relation/file. `execution-verified`.
- Live-MRO check (inline `uv run python -c`, Django 6.1): `FloatField` /
  `DecimalField` under `IntegerField`; `UUIDField` / `JSONField` under
  `CharField`; `ModelChoiceField` et al under `ChoiceField`;
  `ImageField` under `FileField`; `TypedChoiceField` / `FilePathField`
  under `ChoiceField` -- every docstring MRO claim holds.
  `execution-verified`.

## Findings

### R1 -- Model-less scalar table + MRO walk (file-local)

- **Contract + variation.** `_SCALAR_FORM_FIELDS` maps 12 `forms.Field`
  classes to `SCALAR`-kind converters for the column-less path. Varies
  by adding/removing a forms-field row (C1/C2 count 1). Explicit rows
  exist exactly where the MRO would otherwise mis-resolve: `FloatField`
  / `DecimalField` (parent `IntegerField` -> `int`), `UUIDField` /
  `JSONField` (parent `CharField` -> `str`); `ChoiceField` -> `str` is
  the model-less default while a model-backed `choices` column routes
  through the read-side enum at the build site.
- **Sites + roles.** Definition: `forms/converter.py::_SCALAR_FORM_FIELDS`
  + `forms/converter.py::convert_form_field` scalar-walk arm (one body,
  within-file factoring). Mechanism consumer: the walk itself is
  `utils/converters.py::convert_with_mro` (C8 counts 0 here). Kind
  consumer: `forms/inputs.py::_field_triple_and_spec` column-less arm
  (kind + scalar annotation; relation/file finalized there). Oracles:
  scalar parametrize + MRO + JSON rows in `tests/forms/test_converter.py`.
  Projections: table comment + module docstring (MRO claims verified
  live). Rejected unification: J2.
- **Challenges.** C1 counts 1; C2 counts 1.
- **Owner + lifetime.** This file (the model-less key space lives
  nowhere else; the read-side `SCALAR_MAP` cannot accept `forms.Field`
  keys without merging disjoint contracts). No stored derivation (module
  dict read per call; no cache).
- **Migration.** None (no consolidation in a file item).
- **Distinct behavior.** Model-backed columns never reach this table:
  `_model_column_for` resolves the `models.Field` first and the column
  arm delegates to the read side, so a `ChoiceField` over model
  `choices` yields the SAME enum object the read `DjangoType`
  synthesizes (symmetric wire contract, read at
  `mutations/inputs.py::model_column_input_annotation`).
- **Behavioral proof.** P2 (`execution-verified`: 12 keys, disjointness,
  file-row absence) + P3 (`execution-verified`: 20 scalar resolutions).
  Oracles `static-reviewed` (suite not run per item rules).
- **Structural gate.** Scalar parametrize + `test_json_field_maps_to_json_scalar_not_charfield_str`
  + `test_float_and_decimal_do_not_collapse_to_integer_parent` each fail
  a distinct table weakening (dropped JSON row collapses to `str`;
  `IntegerField`-first walk mis-maps floats); negative control is the
  MRO-walk design (each row names the parent it shadows).
- **Freshness.** Target `b717fd0f68bba4c50ee9883ed4a9ccd59b700a51`;
  `types/converters.py`
  `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`;
  `mutations/inputs.py`
  `fc4420475f404297822d7d94bee7bdd275700803`;
  `tests/forms/test_converter.py`
  `08529b369791697d1d9a7faab563c7e605ca998c`.

### R2 -- Kind-precheck order (file-local)

- **Contract + variation.** Five ordered `isinstance` prechecks run
  before the scalar walk: `ModelMultipleChoiceField` ->
  `relation_multi`, `ModelChoiceField` -> `relation_single`,
  `FileField` (covers `ImageField`) -> `file`,
  `MultipleChoiceField` -> `list[str]` scalar, then the exact-type
  bare-`Field` case. Order is load-bearing where a kind subclasses a
  scalar entry (`ModelChoiceField` under `ChoiceField` -> `str`). Varies
  by adding a forms relation/file class (C5 counts 1).
- **Sites + roles.** Definition here (list + four `_CONVERT_*` values).
  Annotation consumers: `forms/inputs.py::_field_triple_and_spec`
  (relation id-type via `_model_less_relation_annotation`, file via
  `Upload`) + `_model_column_for`-gated column arm (untouched by this
  list). Value-shape consumers: `_kind_converter` over
  `utils/converters.py::make_kind_converter` with
  `required_of=form_field_required` (C8/C7 count 0 here). Oracles:
  kind-flag + precheck-subclass rows.
- **Challenges.** C5 counts 1.
- **Owner + lifetime.** This file (forms-field population owner; the
  serializer twin's precheck list covers `serializers.Field`, a disjoint
  population with nested kinds this list has no analogue for).
  Per-call construction; nothing stored.
- **Behavioral proof.** P3 (`execution-verified`: precheck wins,
  subclass resolutions, `annotation=None` for relation/file via P5).
- **Structural gate.** `test_model_choice_field_is_relation_single` /
  `test_model_multiple_choice_field_is_relation_multi` /
  `test_file_and_image_fields_are_file_kind` /
  `test_custom_subclasses_of_precheck_kinds` fail any reorder that lets
  the scalar walk win first (e.g. moving `ModelChoiceField` after the
  walk yields `str`).
- **Freshness.** Target as in R1; `forms/inputs.py`
  `55614839ff479b3610b6026be65f2107ee560fcd`.

### R3 -- No-catch-all fail-loud dispatch (file-local)

- **Contract + variation.** A bare `forms.Field` (exact type only) ->
  `str`; any subclass with no supported ancestor RAISES
  `ConfigurationError` naming the class + field. Varies on nothing
  legitimate: every unmapped shape must keep raising (the GOAL
  no-silent-`String` contract, spec-038 Decision 7).
- **Sites + roles.** Definition: `forms/converter.py::_bare_form_field`
  (exact-type gate returning `MRO_CONTINUE` for subclasses) +
  `forms/converter.py::_unsupported_form_field` (message factory) + the
  `convert_with_mro` fallthrough wiring. Renderer consumers:
  `exceptions.py::_safe_type_name` / `exceptions.py::_safe_arg_repr`
  (imported by name, never redefined; F non-member below). Oracles:
  bare-`Field` row, custom-subclass raise row, hostile-repr row,
  unsupported-quartet row.
- **Challenges.** Registering `forms.Field` -> `str` in the table counts
  as breaking 1 definition (the raise it shadows); the challenge that
  proves the contract is the custom-subclass oracle (P3 re-ran it).
- **Owner + lifetime.** This file (the forms-field population's
  fail-loud boundary). Pure dispatch; nothing stored.
- **Behavioral proof.** P3 (`execution-verified`: exact-type hit,
  custom-subclass raise with exact message, hostile `KeyboardInterrupt`
  repr contained as `unprintable HostileField`, four unsupported raises).
- **Structural gate.** `test_unknown_custom_field_subclass_raises` is the
  catch-all-shadowing regression pin: a base-`Field` table entry turns
  it green-for-the-wrong-reason into `String` instead of raising; the
  test fails exactly on that weakening.
- **Freshness.** Target as in R1; `exceptions.py`
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`.

### R4 -- Single requiredness decision (file-local)

- **Contract + variation.** `form_field_required(field, *, column)`:
  non-`NullBooleanField` returns `field.required` ignoring the column;
  exact `NullBooleanField` returns `False` unless backed by a non-null
  column (no-op `validate` is meaningless, except a non-null column
  rejects `None` downstream and GraphQL non-null `bool` already rejects
  omission). `_null_boolean_converter` keeps the annotation in step:
  `bool` when required, `bool | None` when optional. Varies on the
  NullBoolean reading (C3/C4 count 1).
- **Sites + roles.** Definition here. Consumers (compose by name, listed
  not counted): `convert_form_field` annotation path (column `None`),
  `forms/inputs.py::_field_triple_and_spec` (both arms, one call),
  required-field discovery, shape-identity projection (all read
  `form_field_required` with the resolved column). Oracles: forced-optional
  rows, validating-subclass rows (with SDL `Boolean!` + omission-rejection
  pin), column-backed matrix row.
- **Challenges.** C3 counts 1; C4 counts 1.
- **Owner + lifetime.** This file (the forms requiredness home; pure
  attribute + `isinstance` read, never converts, so discovery over
  excluded unsupported fields cannot raise). Nothing stored.
- **Behavioral proof.** P4 (`execution-verified`: 12-cell matrix +
  annotation match both directions).
- **Structural gate.**
  `test_null_boolean_validating_subclass_generates_required_input` fails
  a tabular weakening that always emits `bool | None` (SDL goes
  `Boolean` while the dataclass still requires the keyword, and the
  omission-rejection assertion breaks); the column-backed matrix row
  fails a column-ignoring simplification.
- **Freshness.** Target as in R1; `forms/inputs.py` as in R2.

### R5 -- Conversion value object (file-local)

- **Contract + variation.** `FormFieldConversion` carries
  `(annotation, kind, required)`; relation/file kinds carry
  `annotation=None` (finalized at the build site where the id type /
  `Upload` is known). The `(annotation, kind, required)` shape is the
  shared `utils/inputs.py::FieldConversionBase` (C7 counts 0 here); the
  table values are `make_scalar_converter` / `make_kind_converter`
  callables sharing the `required_of=form_field_required` wiring (C8
  counts 0 here). Varies only in the form-only requiredness wiring
  (C10 refused: merging with `SerializerFieldConversion` would couple
  the NullBoolean rule to a flavor that must never see it).
- **Sites + roles.** Definition: the subclass + two thin factories here.
  Shape + maker owners: `utils/inputs.py` / `utils/converters.py`.
  Sibling (intentional separation, not a copy):
  `rest_framework/serializer_converter.py::SerializerFieldConversion`
  (default `field.required`, no `required_of`; nested kinds unknown
  here). Consumers: every registry value + precheck in this file.
- **Challenges.** C7 counts 0 here; C8 counts 0 here; C10 refused.
- **Owner + lifetime.** Shape owned upstream; this file owns only the
  subclass binding + the form `required_of` wiring. Short-lived per-call
  instances; nothing stored.
- **Distinct behavior.** A validating-`NullBooleanField` subclass keeps
  `required=True` with `annotation=bool` so GraphQL cannot permit
  omission while the dataclass requires the value (P4 + SDL oracle).
- **Behavioral proof.** P5 (`execution-verified`: subclass relation,
  `__slots__`, `annotation=None` exactly for relation/file).
- **Structural gate.** The subclass + annotation-shape oracles
  (`annotation is None` assertions on the relation/file rows) fail a
  hand-rolled tuple return or a premature relation annotation.
- **Freshness.** Target as in R1; `utils/inputs.py`
  `ee31d360c1dbc7acb9fe30c868a35ac6f7a64ec0`;
  `utils/converters.py`
  `5332f0542c0bd180aee30de95ec091933b54ee34`;
  `serializer_converter.py`
  `32904418a169941c2afa1c9cd6866c55debc64f3`.

### R6 -- Kind re-exports for stable addressing (file-local)

- **Contract + variation.** `FILE` / `RELATION_MULTI` /
  `RELATION_SINGLE` / `SCALAR` are re-exported (`as`-form) so the form
  resolver, the input builder, and the tests keep addressing them on
  this module (spec-038 Decision 7). No variation: the spelling is owned
  upstream (C6 counts 0 here).
- **Sites + roles.** Owner: `utils/inputs.py` (one conceptual enum).
  Re-export here; consumers: `forms/inputs.py`, `forms/resolvers.py`,
  `tests/forms/test_converter.py` (all import from `.converter`).
- **Behavioral proof.** P5 (`execution-verified`: four `is`-identities,
  form + serializer sides).
- **Freshness.** Target as in R1; `utils/inputs.py` as in R5.

### F-reuse -- `converter-table-per-surface-ownership` (rejection CONFIRMED, re-derived fresh)

This file's table is one of the four members; the unification candidate
is REJECTED again from this side (P2 census + behavior comparison, never
inherited from the scalars item).

- **Contract differences.** `types/converters.py::SCALAR_MAP`:
  `models.Field` -> scalar, shared read-output + filter-input contract
  with choice substitution layered by callers, mutable
  last-write-wins extension hook. `scalars.py::_PACKAGE_SCALAR_MAP`:
  scalar TYPE -> `ScalarDefinition`, schema-registration contract.
  This table: column-LESS `forms.Field` -> annotation + decode kind,
  no `BigInt`/file rows by design (P2), relation/file annotations
  deferred to the build site. Serializer table: serializer-ONLY
  `serializers.Field` -> conversion with nested kinds, `is_input`
  parity parameter, and a consumer-registration hook this file has no
  analogue for. Key spaces pairwise disjoint (P2: 26/1/12/16); value
  spaces disjoint (scalars vs definitions vs conversions). What SHOULD
  be shared already is: model-backed write columns delegate to the read
  side by name (R1 distinct-behavior, read at the build site), and the
  walks share `convert_with_mro` with separate key spaces.
- **Trigger (re-checked fresh).** A new surface whose field population is
  a SUBSET of an existing table's key space with identical value
  contract and lifecycle (e.g. a second `models.Field`-keyed scalar map)
  reopens the count. A new KIND of field population keeps its own table.
- **Durable home.** Each table's module docstring already states its key
  space and non-membership (this file's header + kind comment, the
  read-side file-row comment, the serializer mirror comment, the
  scalars contrast clause) -- verified by reading, plus this finding.
  Plan index row already covers all four files -- no index change
  proposed.
- **Freshness.** Target as in R1; `types/converters.py`,
  `serializer_converter.py`, `utils/converters.py` as above;
  `scalars.py` `5e354042d405040f6137cebd39abe9c042ffece8`.

### F-reuse -- `set-type-naming` (checked non-membership)

This file does NOT join the family: it builds no type names (zero hits
for `type_name_for` / `graphql_camel_name` / `pascal` in the target;
input-class naming lives at `forms/inputs.py::form_input_type_name`
over `utils/inputs.py::name_set_input_type_name`). No index change
proposed.

### F-reuse -- `field-value-coercion` (checked non-membership)

This file does NOT join the family: it maps fields to annotations and
never touches a runtime value (zero `coerce` definitions; the one prose
hit is the no-silent-coerce contract sentence). Value coercion lives at
`utils/querysets.py::coerce_field_value_or_none` and the resolver
decoders. No index change proposed.

### F-reuse -- `typed-rejection-value-tail` (checked non-membership)

This file does NOT join the family: the unsupported-field diagnostic
renders through `exceptions.py::_safe_type_name` /
`exceptions.py::_safe_arg_repr` (imported by name, never redefined --
composition, not membership) and `describe_value` appears zero times in
the target. The message shape (class name + field repr, both
never-raise incl. the hostile-repr and huge-int-attr cases via the
`BaseException` guards) is pinned by its own oracles; no contract
source routes this schema-construction diagnostic through
`describe_value` (the family's named schema-construction scope is
`error_policy.py` / `resource_policy.py` / `extensions/debug.py`, and
its docstring leaves other `got {...}` tails as a separate change).
Not a defect: rewording would change the pinned message and what is
accepted is unchanged either way. No index change proposed.

## Defects

None. Every claim checked while tracing held: the 28-member census; the
four key-space populations and their disjointness; every docstring MRO
claim against live Django 6.1 MROs; the precheck order against the
subclass hazards; the exact-type-vs-catch-all distinction (custom
subclass raises); the 12-cell requiredness matrix with annotation match
both directions; the four kind `is`-identities and the shared base;
the model-backed delegation to the read side at the build site. The
investigated boundaries (unmapped `DurationField` et al raising, file
rows absent from the scalar table, `describe_value` not ridden) each
lack a contract source requiring the alternative and each alternative
changes what is accepted, so none is filed. Nothing routed to any owner.

## Pending execution

None. All five probes already ran green against the shared tree; each
is read-only (imports + in-memory field instances + pure calls; no
source mutation, no database, Django settings configured in-memory for
field instantiation only). No pytest was run in the shared tree, per
item rules; oracle bodies are `static-reviewed`. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells are
`inapplicable by construction`: the target's code path reaches no
database, alias, or dialect decision (pure dispatch over in-memory
field instances + in-memory dict reads).

## Judgment

Backstop discharged: 28/28 `ast.Module.body` members enumerated, 10
challenges run (C1--C10, every variation axis of every rule), six
matrix axes discharged against the real surface (read-side table +
serializer twin compared by behavior + contract first), six file-local
records with proving challenges (R1--R6), three families checked as
non-membership with the consumer relationship named, one rejection
re-derived fresh with difference + trigger + home (J2 CONFIRMED, no
index change: the plan row already covers all four files), zero
defects, zero pending. The target owns its rules singly: one
model-less table, one precheck order, one fail-loud boundary, one
requiredness decision, one value-object binding, one re-export point.
Zero-edit result is legitimate.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff c17f632023971a4cdd9499dfbce14a4c8c7c9af5 -- django_strawberry_framework/forms/converter.py`
is empty for the target (working blob
`b717fd0f68bba4c50ee9883ed4a9ccd59b700a51` equals the item baseline
member and `HEAD:` -- target CLEAN, so no hunk attribution was owed);
the artifact itself is this new file. The `## Owned changes` ledger
paths (`optimizer/walker.py`, `test_products_visibility_api.py`,
`test_multi_db.py`) were never touched. Concurrent dirt
(`django_strawberry_framework/connection.py` hunk,
`django_strawberry_framework/extensions/resource_policy.py`,
`tests/test_connection.py`, `tests/test_resource_policy.py`, staged
`tests/utils/test_querysets.py`, `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md`, `docs/dry/dry-file-utils__querysets.md`,
`examples/fakeshop/test_query/test_resource_policy_api.py`,
`examples/fakeshop/db.sqlite3`) was never edited, reverted, or tidied,
verified by content-diff scoping (`git status --short` scoped to the
item paths shows no entry before and after). Scratch (ignored, kept for
Worker 2 re-run):
`docs/dry/temp-tests/dry-file-forms__converter/p1_ast_census.py`,
`p2_table_census.py`, `p3_dispatch.py`, `p4_requiredness.py`,
`p5_kind_identity.py`. No `ruff` run owed (no tracked edits). Do not
commit.

## Independent verification (Worker 2)

Own trace, recorded before opening `## Findings` (re-derived from the
target plus its real neighbors, read-side and serializer twins first).

Target: `django_strawberry_framework/forms/converter.py`, 292 lines,
28 `ast.Module.body` members, 0 `AsyncFunctionDef` (re-counted
independently; member-by-member map under `### Enumeration` below).
Pure in-memory dispatch: no ORM access, no await, no database.

Rules re-derived from this side, with the owner I would choose:

- Model-less scalar table + MRO walk. `_SCALAR_FORM_FIELDS` holds 12
  `forms.Field`-keyed rows; `convert_form_field` walks
  `type(field).__mro__` against it via the shared
  `utils/converters.py::convert_with_mro` skeleton. Explicit rows sit
  exactly where the MRO would otherwise mis-resolve (live-MRO
  re-check: `FloatField` / `DecimalField` under `IntegerField`;
  `UUIDField` / `JSONField` under `CharField`; `ModelChoiceField` et
  al under `ChoiceField`; `ImageField` under `FileField`). Owner:
  this file (the column-less key space lives nowhere else). Count:
  C1/C2 each force 1 definition. Agree with R1.
- Kind-precheck order. Five ordered `isinstance` prechecks run before
  the scalar walk (`ModelMultipleChoiceField`, `ModelChoiceField`,
  `FileField`, `MultipleChoiceField` -> `list[str]`, then the
  exact-type bare-`Field` case); order is load-bearing where a kind
  subclasses a scalar entry. Owner: this file. Count: C5 forces 1.
  Agree with R2.
- Fail-loud dispatch. Bare `forms.Field` by exact type -> `str` via
  `_bare_form_field` returning `MRO_CONTINUE` for subclasses; anything
  unregistered raises `ConfigurationError` from
  `_unsupported_form_field` through the skeleton fallthrough. No
  base-`Field` table row (census: `forms.Field` absent from the 12
  keys); custom-subclass raise re-proved by re-running P3. Owner: this
  file. Agree with R3.
- Requiredness decision. `form_field_required(field, *, column)` is the
  single decision: non-`NullBooleanField` returns `field.required`;
  exact `NullBooleanField` returns `False` unless backed by a non-null
  column. Consumed at the annotation path, both build-site arms, and
  required-field discovery (all by name; 12-cell matrix re-proved by
  re-running P4). `_null_boolean_converter` keeps the annotation in
  step (`bool` vs `bool | None`). Owner: this file. Counts: C3/C4 each
  1. Agree with R4.
- Conversion value object + makers. `FormFieldConversion` subclasses
  the shared `utils/inputs.py::FieldConversionBase` (verified
  `issubclass`, both flavors); table values are thin
  `make_scalar_converter` / `make_kind_converter` wrappers with
  `required_of=form_field_required`. Shape and makers owned upstream;
  this file owns only the subclass binding + the form
  `required_of` wiring. C7/C8 count 0 here; C10 refused (merging with
  `SerializerFieldConversion` would couple the NullBoolean rule to a
  flavor that must never see it). Agree with R5.
- Kind re-exports. `FILE` / `RELATION_MULTI` / `RELATION_SINGLE` /
  `SCALAR` are `as`-form re-exports, `is`-identical to
  `utils/inputs.py` on both the form and serializer sides (re-proved
  by re-running P5). Spelling owned upstream; C6 counts 0 here. Agree
  with R6.

Converter-table rejection, re-derived from this side (not inherited):
`types/converters.py::SCALAR_MAP` (26 `models.Field` keys, read
output + filter input contract, choice substitution by callers),
`scalars.py::_PACKAGE_SCALAR_MAP` (1 scalar-type key, registration
contract), this table (12 column-less `forms.Field` keys, annotation
+ decode kind, relation/file deferred), serializer table (16
`serializers.Field` keys plus nested kinds, `is_input` parity, and a
consumer-registration hook this file has no analogue for). P2
re-run from this side confirms 26/1/12/16 with pairwise-disjoint key
spaces and no file rows in the form table. What should be shared
already is: the skeleton, the value shape, the kind vocabulary, and
model-backed columns delegating to the read side by name at the
build site (`forms/inputs.py::_field_triple_and_spec` column arm).
Trigger and durable home as stated in F-reuse are adequate; plan
index row `converter-table-per-surface-ownership` already covers all
four files so no index change is owed. CONFIRMED.

Reconciliation vs W1: agree on every rule, every count (C1--C10),
every owner, every role, and the rejection. One difference: the
freshness literal for `serializer_converter.py` (see Verdict).

### Enumeration

Independent `ast` recount: 28 members, 0 async, 1 class def (P1
re-run green). Member-by-member map (mine 0-indexed -> W1 1-indexed):
docstring -> 1; `__future__` -> 2; `datetime` -> 3; `decimal` -> 4;
`uuid` -> 5; `Any` -> 6; `strawberry` -> 7; `django.forms` -> 8;
exceptions import (3 names) -> 9; converters import (5 names) -> 10;
`FILE` -> 11; `RELATION_MULTI` -> 12; `RELATION_SINGLE` -> 13;
`SCALAR` -> 14; `FieldConversionBase` -> 15; `FormFieldConversion` ->
16; `form_field_required` -> 17; `_null_boolean_converter` -> 18;
`_scalar_converter` -> 19; `_kind_converter` -> 20;
`_SCALAR_FORM_FIELDS` -> 21; `_bare_form_field` -> 22;
`_CONVERT_RELATION_MULTI` -> 23; `_CONVERT_RELATION_SINGLE` -> 24;
`_CONVERT_FILE` -> 25; `_CONVERT_MULTIPLE_CHOICE` -> 26;
`convert_form_field` -> 27; `_unsupported_form_field` -> 28. No
member unassigned; no sample-based check. Agree: 28/28.

### Matrix

Axis 1 judged on behavior first: read-side and serializer twins read
in full before any verdict (census + contract comparison re-derived,
not inherited). Axes 2--6 checked against the target's real surface:
axis 2 inapplicable by construction (0 async, no ORM; resolver
pipeline consumes output kinds, no colored twin); axis 3 single
derivation verified by name-grep at the build site; axis 4 one
grammar with `is`-identical kinds; axis 5 one definition per rule
with oracles spelling literals (no oracle reads `_SCALAR_FORM_FIELDS`
or any owner table); axis 6 absences each tied to a contract source
(spec-038 Decision 7 / GOAL fail-loud) with the alternative changing
what is accepted. Agree on all six.

### Counts, roles, equivalence

C1--C10 counts confirmed as stated (definitions only; consumers,
oracles, projections listed not counted). No oracle rewritten to read
from its owner. Zero production edits, so observable equivalence
(DRY.md principle 8) holds trivially; current behavior re-proved by
re-running all five probes green (P1--P5, read-only, no database, no
shared-tree pytest, no source mutation so no workspace copy was
owed). `FAKESHOP_SHARDED=1` / Postgres `inapplicable by
construction`: target reaches no database, alias, or dialect decision.
Pending: none outstanding -- agree. Coupling: none -- agree.

### Baselines, fingerprints, gates, prose

- Baseline-hash note: RULING -- resolved, no verdict impact. Dispatch
  `ITEM_BASELINE 31061a57e3b25e353bc73878ff33d04c570c12a0` and W1's
  `c17f632023971a4cdd9499dfbce14a4c8c7c9af5` are both `git stash
  create` objects on HEAD `9031cb3d`; verified myself that `git diff`
  against EITHER baseline for the target path is empty, and the only
  delta between the two stash objects is concurrent dirt in
  `docs/bug_hunt/bug_hunt-0_0_15.md`. Same snapshot content for this
  item; equivalent.
- Zero-edit confirmed at the dispatch baseline: `git diff
  31061a57... -- django_strawberry_framework/forms/converter.py` empty;
  worktree blob `b717fd0f...` equals `HEAD:` blob. No hunk
  attribution owed. Coverage + assignment validated above; no
  candidate needs routing to another family (converter-table
  candidate stays rejected, no index change -- judged above).
- Fingerprint re-hashes (via `git hash-object`): target `b717fd0f…`
  match; `types/converters.py 9ceb34af…` match;
  `mutations/inputs.py fc442047…` match; `tests/forms/test_converter.py
  08529b36…` match; `forms/inputs.py 55614839…` match;
  `exceptions.py e06b0b7f…` match; `utils/inputs.py ee31d360…` match;
  `utils/converters.py 5332f054…` match; `scalars.py 5e354042…`
  match. MISMATCH: `rest_framework/serializer_converter.py` -- the
  artifact prints `32904418a169941c2afa1c99debc64f3` (32 chars, not a
  valid blob id) while worktree and `HEAD:` both hash to
  `32904418a169941c2afa1c9cd6866c55debc64f3` (40 chars). File is clean
  (`git status` shows no entry), so this is a transcription typo in
  the artifact, not drift -- but a corrupt fingerprint cannot guard a
  future comparison, so it must be corrected (see Verdict).
- Negative controls: gates named per finding with the weakening each
  oracle fails (scalar parametrize + JSON row + float/decimal row;
  kind-flag + precheck-subclass rows; custom-subclass raise pin;
  NullBoolean SDL + column-backed matrix rows; annotation-`is`-`None`
  assertions). No executed `prove_failability.py` run -- acceptable
  here, matching the verified zero-edit file-item standard (probes
  execution-verified, oracle bodies static-reviewed, no shared-tree
  pytest per item rules). No gate relies on an unproven bypass.
- AGENTS.md prose check: item-scoped diff empty at both baselines and
  `HEAD`, so no process-provenance / citation / tier violation from
  edits. Artifact uses `path::Symbol` refs with no line numbers;
  the bottom link block keeps all 10 canonical group headers. No
  package defects found; no `(Worker 2)` entries owed under
  `## Defects` (the one artifact typo is dispositioned under Verdict,
  not as a package defect).
- Scratch: W1's five probe files kept on disk for re-run (re-ran them
  above); Worker 0 removes `docs/dry/temp-tests/dry-file-forms__converter/`
  by explicit path only after `verified`.

### Verdict

`revision-needed` on exactly ONE literal: R5 `**Freshness**`
`serializer_converter.py` fingerprint (referenced again by F-reuse
`as above`) must read
`32904418a169941c2afa1c9cd6866c55debc64f3`. Reproducible check:
`git hash-object
django_strawberry_framework/rest_framework/serializer_converter.py`.
Everything else in the artifact is verified as written; resubmission
needs no re-trace, only the corrected literal, and returns to this
verifier. No ruff run owed (markdown-only artifact edit, no `.py`
touched, no new tracked files); concurrent dirt listed in
`## Implementation (Worker 1)` plus `git status --short` at
verification time left untouched; do not commit.

### Pass-2 note (Worker 2)

Resubmission verified: R5 Freshness line 427 now reads the correct
40-char blob id `32904418a169941c2afa1c9cd6866c55debc64f3`, reproduced
via `git hash-object` against the clean worktree path (equals `HEAD:`
blob). The sole remaining corrupt-literal hit is the verbatim quote
inside this section's own pass-1 record, correctly left historical.
My pass-1 sections otherwise untouched; Worker 1's only changes are
the literal, the `## Iterations (pass 2)` paragraph, and the Status
line. Item-scoped diff vs dispatch baseline
`31061a57e3b25e353bc73878ff33d04c570c12a0` still empty; HEAD still
`9031cb3d`; no re-trace owed, no pytest owed. `Status: verified`, no
pending execution.

## Iterations (pass 2)

Pass 2 replaced the corrupt 32-char R5 Freshness fingerprint for `serializer_converter.py` with the Worker-0-verified 40-char blob id `32904418a169941c2afa1c9cd6866c55debc64f3` (reproduced via `git hash-object` on the clean worktree path), confirmed the F-reuse Freshness needs no second swap since it follows via `as above`, and set `Status: ready-for-verification/2` with no other artifact, production, or ledger changes.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
