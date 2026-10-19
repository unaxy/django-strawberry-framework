# DRY review: `types/converters.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Target `django_strawberry_framework/types/converters.py`: HEAD blob
`058f10813927c0691ba658d7d388820bd07cd52a` (807 lines); worktree
`f6cadb0856c725d96ce316abb4418b4c9d55bf9d` (768 lines) is
concurrent-external hunt dirt (the `truth.*` migration: `truth`
import, `_class_map_lookup` identity scan, dropped `_safe_*` /
`_field_has_choices` guards, narrowed except arms — all 14 hunks
attributed by content against `git show HEAD:<path>`; absent from
the ledger and the cycle baseline). Traced at HEAD bytes throughout;
zero production edits (file item owes none).

## System trace

The target owns read-side field conversion: Django model-field ->
Strawberry annotation. Four sub-responsibilities: (a) the scalar
pipeline (`SCALAR_MAP` + `scalar_for_field` + `convert_scalar` +
`_field_has_choices`, incl. the postgres `ArrayField` / `HStoreField`
dispatch and the `force_nullable` tri-state); (b) the choice-enum
pipeline (`_sanitize_member_name` + `_is_enum_reserved_member` +
`build_enum_from_choices` + `convert_choices_to_enum` + registry
cache); (c) the read-output entry (`FIELD_OUTPUT_TYPE_MAP` +
`FILESYSTEM_PATH_OUTPUT_TYPE_MAP` + `_field_output_type_for` +
`convert_field_output` + the five file/image output classes +
`_safe_file_attr`); (d) relation annotation
(`resolved_relation_annotation` over `FieldMeta`) plus the
diagnostic label (`_field_label`).

Consumers compose by name: [types-base][types-base] (`_build_annotations`
routes every non-relation column through `convert_field_output`;
the `filesystem_path_fields` validator composes
`_field_output_type_for`), [types-finalizer][types-finalizer]
(relation rewrite through `resolved_relation_annotation`),
[types-resolvers][types-resolvers] (`_attach_file_resolvers` through
`_field_output_type_for`), [filters-inputs][filters-inputs]
(`scalar_for_field` + `convert_choices_to_enum`, local imports),
[mutations-inputs][mutations-inputs] (`convert_scalar` with
`force_nullable=False` + `scalar_for_field` for id typing),
[rf-converter][rf-converter] (`convert_scalar` + `scalar_for_field`
+ `build_enum_from_choices`), [inspect][inspect] (converter-column
labels through `_field_output_type_for` + `SCALAR_MAP`), and
[write-values][write-values] (the member-carries-value contract).
The target itself consumes [registry][registry] (enum cache),
[utils-strings][utils-strings] (`pascal_case`), [utils-imports][utils-imports]
(postgres soft symbols), [field-meta][field-meta] (cardinality),
[scalars][scalars] (`BigInt`), and [exceptions][exceptions]
(`ConfigurationError` + the `_safe_*` renderers).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched every flavor
   converter: [rf-converter][rf-converter],
   [forms-converter][forms-converter], [filters-inputs][filters-inputs],
   [mutations-inputs][mutations-inputs],
   [utils-converters][utils-converters]. The scalar tables stay
   per-surface (R5, CONVERGE with verified R-TABLES on a fresh
   26/12/16/1 census); the extension hooks stay split (R6, CONVERGE
   with verified R-EXT-HOOK); the form-field isinstance ladder
   stays a ladder (R11); the relation rules stay input-vs-output
   (R7); the enum rule is already single-sited in
   `build_enum_from_choices` with all three flavors composing it.
   The enum-name template is the one true mirror (C-ENUM, adopted
   into the open family).
2. **Sync/async twins.** Inapplicable: the module is pure
   synchronous construction-time code (zero `await`, zero
   `async def`, zero boundary token — `async|await|sync_to_async`
   census is empty outside prose).
3. **Derived rather than repeated knowledge.** The firing-row
   derivation is spelled three times (FAM-MRO, new holding
   family): `scalar_for_field`, `_field_output_type_for`, and
   [inspect][inspect] `::_matched_scalar_key`. The `Model.field`
   label is derived guarded here vs raw inline elsewhere (R2).
   The enum name is derived identically at two sites (C-ENUM).
   The relation nullability display in [inspect][inspect] reads
   `FieldMeta` slots plus the synthesized annotation — a display
   read, not a re-derivation of `resolved_relation_annotation`'s
   decision (recorded in F-RELANN, no row).
4. **Inverse / round-trip pairs.** Sanitization is one-way by
   design (no inverse exists or is owed); enum construction is
   one-way (`member.value` carries the Django value, unwrapped
   downstream by [write-values][write-values] `::raw_choice_value`
   — a consumer of the value contract, not an inverse
   definition). The file annotation / file resolver pair
   (`convert_field_output` nullable-by-default +
   [types-resolvers][types-resolvers] `::_make_file_resolver`
   returning `None` for empty files) is a producer/consumer
   agreement over spec-037 Decision 4, each side single-sited; a
   contract change moving both is not duplication (no row).
5. **Contracts restated in another medium.** Module + function
   docstrings project every contract; two projections are stale
   (D1 dict-order mechanism, D2 consumer census). SDL carries the
   enum names + the path-field security description
   (projections). Fakeshop README / models / schema prose cite
   the file objects (projections). Test oracles pin spellings
   independently (never read the owner). The
   [test-query-readme][test-query-readme] `_safe_file_attr`
   boundary note is already corrected in place (projection, no
   action).
6. **Enforcement by omission.** Enumerated: `SCALAR_MAP` misses
   fail loud (`DurationField` / `BinaryField` documented absent,
   oracles pin both raises); `FIELD_OUTPUT_TYPE_MAP` covers both
   file field classes (`FilePathField` is deliberately a `str`
   scalar row); `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` is total over
   `_field_output_type_for`'s range by construction; postgres
   dispatch covers `ArrayField` + `HStoreField`, every other
   postgres field falls through to the raising MRO walk;
   `force_nullable` is honored at all four widening sites (array
   :457, hstore :471, scalar tail :479-480, file branch :552-553);
   `FileField(choices=...)` is partitioned OUT of the choices
   rule by the documented file-vs-scalar routing (choices
   substitution is scoped to the scalar branch) — total
   partition, no gap, no maintainer route; `_sanitize_member_name`'s
   `enum_name=None` path is exercised by direct unit oracles.

### Enumeration

Instrument: every name in `ast.Module.body` at HEAD bytes
(`058f1081`, 807 lines). Count: 40 members (1 docstring + 15
import statements binding 18 names + 24 definitions). Every
member lands below; no consolidation inside this file item.

| # | Member (HEAD line) | Home |
|---|---|---|
| 0 | Module docstring (:1) | F-MECH (D1 + D2 prose sites) |
| 1-15 | 15 imports, 18 names, all consumed (verified below) | F-MECH |
| 16 | `_safe_file_attr` (:82) | F-GUARD |
| 17 | `DjangoFileType` (:110) | F-FILEOBJ |
| 18 | `DjangoImageType` (:153) | F-FILEOBJ |
| 19 | `_FileSystemPathFields` (:176) | F-FILEOBJ |
| 20 | `DjangoFilePathType` (:204) | F-FILEOBJ |
| 21 | `DjangoImagePathType` (:215) | F-FILEOBJ |
| 22 | `SCALAR_MAP` (:224, 26 rows) | F-SCALARMAP |
| 23 | `FIELD_OUTPUT_TYPE_MAP` (:266) | F-OUTMAP |
| 24 | `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` (:277) | F-OUTMAP |
| 25 | `_NON_IDENT` (:282) | F-SANITIZE |
| 26 | `_GRAPHQL_RESERVED_ENUM_VALUES` (:283) | F-SANITIZE |
| 27 | `_ARRAY_FIELD_CLS` (:295) | F-POSTGRES |
| 28 | `_HSTORE_FIELD_CLS` (:299) | F-POSTGRES |
| 29 | `_field_label` (:305) | F-LABEL |
| 30 | `_field_has_choices` (:322) | F-SCALAR |
| 31 | `scalar_for_field` (:330) | F-SCALAR + FAM-MRO (walk leg) |
| 32 | `convert_scalar` (:353) | F-SCALAR + F-POSTGRES (branches) |
| 33 | `_field_output_type_for` (:484) | F-OUTMAP + FAM-MRO (walk leg) |
| 34 | `convert_field_output` (:500) | F-ENTRY |
| 35 | `_is_enum_reserved_member` (:556) | F-SANITIZE |
| 36 | `_sanitize_member_name` (:586) | F-SANITIZE |
| 37 | `build_enum_from_choices` (:628) | F-ENUMCORE |
| 38 | `convert_choices_to_enum` (:740) | F-PIPE + C-ENUM (:775 template) |
| 39 | `resolved_relation_annotation` (:795) | F-RELANN |

Import census (AST-verified, all 18 consumed):
`datetime`/`decimal`/`uuid` (map rows), `keyword` (sanitize
step 3), `re` (`_NON_IDENT`), `Enum` (core build),
`Any` (annotations), `strawberry` (decorators + `JSON`),
`models` (map keys), `ConfigurationError` (all raises),
`_safe_arg_repr` (diagnostics), `_safe_text` (`_field_label`),
`_safe_type_name` (unsupported-field message), `FieldMeta`
(F-RELANN), `registry` (enum cache), `BigInt` (64-bit rows),
`import_attr_if_importable` (sentinels), `pascal_case`
(C-ENUM template).

### Challenges

Each change posited on the rule's variation axes; counts are
AUTHORITATIVE definitions only (consumers / oracles /
projections listed in the findings, never counted).

| Id | Change posited | Count | Home |
|---|---|---|---|
| C1 | Add/remove a `SCALAR_MAP` row (new field kind) | 1 | F-SCALARMAP |
| C2 | Harden MRO dispatch to identity-scan (hostile `__hash__`) | 3 | FAM-MRO |
| C3 | Change which MRO ancestor counts as the firing row | 3 | FAM-MRO |
| C4 | Add a file/image kind to the output map | 1 | F-OUTMAP |
| C5 | Add/rename a path-bearing sibling | 1 | F-OUTMAP |
| C6 | Flip the file default-null rule | 1 | F-ENTRY (R10 split) |
| C7 | Soften a third postgres-only field class | 1 | F-POSTGRES |
| C8 | Allow nested `ArrayField` / outer choices | 1 | F-POSTGRES |
| C9 | Change tri-state collapse semantics | 1 | F-SCALAR |
| C10 | Change choice-substitution ordering vs widening | 1 | F-SCALAR |
| C11 | Accept grouped-choices form | 1 | F-ENUMCORE |
| C12 | Add a sanitize rule (new reserved class) | 1 | F-SANITIZE |
| C13 | Change the sanitize-collision verdict | 1 | F-ENUMCORE |
| C14 | Change the enum-name template | 2 | C-ENUM (open family) |
| C15 | Change read-side enum cache policy | 1 | F-PIPE (R8 split) |
| C16 | Widen/narrow the storage-guard catch list | 1 | F-GUARD |
| C17 | Add/change a file-object subfield | 1 | F-FILEOBJ |
| C18 | Change the diagnostic label shape | 1 | F-LABEL (R2 twins) |
| C19 | Change the relation annotation shape | 1 | F-RELANN (R7) |
| C20 | Reword one guard diagnostic | 1 per site | R1 (J1 CONVERGE) |
| C21 | Change the `Meta.name` reject grammar | 0 here | R3 (R18 CONVERGE) |
| C22 | Unify the four converter tables | rejected | R5 (R-TABLES CONVERGE) |
| C23 | Validate `SCALAR_MAP` registration | rejected | R6 (R-EXT-HOOK CONVERGE) |
| C24 | Change hostile-mapping gate policy | 0 here | non-member (matrix) |
| C25 | Change override-detection question | 0 here | R4 (R14 CONVERGE) |

### Freshness fingerprints

HEAD `0c0537e2`. Target HEAD `058f1081…` / worktree
`f6cadb08…` (hunt dirt, attributed by content, untouched).
Inputs inspected at HEAD bytes (`git rev-parse HEAD:<path>`):

- types siblings: `__init__` `1bf69028…` (CLEAN),
  `base` `dda91365…`, `definition` `fa6c4d33…`, `finalizer`
  `de34ae2a…`, `relay` `52439862…`, `resolvers` `72d62dc4…`,
  `relations` `5e9b5cdb…` (CLEAN).
- `registry` `81bd561c…`, `scalars` `5e354042…`,
  `utils/strings` `991f7dad…`, `utils/imports` `291ecedd…`
  (CLEAN), `exceptions` `e06b0b7f…`, `optimizer/field_meta`
  `18ea719a…`, `optimizer/nested_planner` `b4dfd4a6…`,
  `filters/inputs` `82b52d97…`, `filters/sets` `993e887a…`,
  `forms/converter` `37f3ff39…`,
  `rest_framework/serializer_converter` `6652d092…`, `conf`
  `c6ad46aa…` (byte-identical to the R18-cited blob),
  `mutations/inputs` `fc442047…`, `utils/write_values`
  `d28587c7…`, `management/commands/inspect_django_type`
  `2807d0fc…`, `utils/converters` `5332f054…`, `list_field`
  `21380eb7…`, `sets_mixins` `ad8987ea…` (byte-identical to
  the R14-cited blob), `permissions` `72102cc0…`.
- Oracles: `tests/types/test_converters.py` `c2ff9fca…`
  (2267 lines), `tests/types/test_base.py` `0d070aee…`,
  `tests/management/test_inspect_django_type.py` `9b1360d0…`,
  `test_uploads_api.py` `dcbcbf61…` (CLEAN),
  `test_library_api.py` `1f107fff…`.
- Prior verdicts re-checked (triggers only, never inherited):
  [dry-base][dry-base] R14/R18/C6,
  [dry-serializer-conv][dry-serializer-conv]
  FAM-ENUM/R-TABLES/R-EXT-HOOK.
- Modules EXCLUDED on body strength (fingerprinted above):
  `types/relay.py` (Relay identity, no conversion surface),
  `types/relations.py` (pending records, no rule overlap),
  `types/definition.py` (reject-gate legs now held by open
  `graphql-name-gate`; R3),
  `optimizer/nested_planner.py` (tuple-membership sentinel
  consumption; R9), `list_field.py` (info-path label; R2),
  `utils/write_values.py` (value-unwrap consumer; axis 4),
  `filters/sets.py` (cardinality consumer only),
  `utils/converters.py` (hardened sibling, reconciled in
  FAM-MRO, not counted).

## Findings

### F-MECH — module mechanics (file-local)

- **Contract + variation.** The module docstring states the
  public surface + the read-output-only file routing + the
  extension paths; 15 import statements bind 18 names, every
  one consumed (census above). Varies only by surface
  addition/removal.
- **Sites + roles.** *Definition*: members 0-15. *Consumers*:
  every function below. No oracle pins the docstring text.
- **Challenges.** Surface change moves the docstring + code
  together (count 1; intentional co-change, not duplication).
- **Owner + lifetime.** This file. No stored derivation.
- **Migration.** None.
- **Distinct behavior.** D1 + D2 record the two stale prose
  claims; the remainder of the docstring was read against the
  bodies and holds.
- **Behavioral proof.** `static-reviewed` (AST import-use
  census 18/18; docstring claims checked per finding).
- **Structural gate.** None owed (mechanics, no bypass).
- **Coupling.** D1, D2 (prose repairs at this owner).
- **Freshness.** Target `058f1081…`.

### F-GUARD — storage-failure guard (file-local)

- **Contract + variation.** `_safe_file_attr` reads one
  storage attr, degrading exactly `(ValueError, OSError,
  NotImplementedError)` to `None`; everything else —
  notably `SuspiciousFileOperation` — propagates (spec-037
  Decision 4). Varies on the catch list only (C16 counts 1).
- **Sites + roles.** *Definition*: member 16. *Consumers*:
  all 6 nullable subfield resolvers (size/url/width/height/
  path). *Oracles*: live `test_uploads_api.py` degradation
  rows + the introspection pin
  (`test_file_output_objects_publish_nullable_subfields_over_http`).
  *Projections*: the function docstring.
- **Challenges.** C16 counts 1. C20 counts 1 per site (R1).
- **Owner + lifetime.** This file (storage-failure semantics
  live with the file objects). Pure function; not cached.
- **Migration.** None.
- **Distinct behavior.** The narrow catch is the deliberate
  contrast with the package's broad hostile-metadata guards
  (R1): storage signals degrade, security signals surface.
- **Behavioral proof.** `static-reviewed` for the count (one
  body; `NotImplementedError` catch census package-wide =
  this site only).
- **Structural gate.** The live degradation oracles (each
  fails if its subfield stops guarding; the test-query README
  records the failability history).
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; live oracle
  `dcbcbf61…` (CLEAN).

### F-FILEOBJ — file/image output objects (file-local)

- **Contract + variation.** `DjangoFileType` (name non-null
  direct + size/url nullable guarded), `DjangoImageType`
  (adds guarded width/height by inheritance),
  `_FileSystemPathFields` (the single decorated-mixin `path`
  with the security description), and the two path-bearing
  compositions. Varies per subfield (C17 counts 1 — the mixin
  single-sites `path` across both compositions).
- **Sites + roles.** *Definition*: members 17-21.
  *Consumers*: the output maps (F-OUTMAP), the root export
  surface, [types-resolvers][types-resolvers] (resolver
  pairing prose). *Oracles*: `test_converters.py`
  file-object rows + live uploads rows. *Projections*:
  class docstrings + fakeshop README/models/schema prose.
- **Challenges.** C17 counts 1 (mixin inheritance; Strawberry
  collects only from decorated bases — the decoration is
  load-bearing, stated in the mixin docstring and accurate).
- **Owner + lifetime.** This file. Class objects; no cached
  derivation.
- **Migration.** None.
- **Distinct behavior.** Nullability deliberately diverges
  from upstream's all-non-null shape (spec-037 Decision 4);
  `path` is opt-in only (spec-048 Decision 1).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The no-path-by-default + security-
  description oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; oracles `c2ff9fca…`,
  `dcbcbf61…` (CLEAN).

### F-SCALARMAP — shared scalar table (file-local)

- **Contract + variation.** `SCALAR_MAP` maps 26
  `models.Field` classes to scalars, incl. the deliberate
  `FileField`/`ImageField -> str` rows that keep the shared
  filter-input path scalar; mutable last-write-wins read per
  call (no caching); subclass-by-construction extension plus
  bare-dict-assignment hook; `DurationField`/`BinaryField`
  documented absent. Varies per row / hook posture (C1
  counts 1).
- **Sites + roles.** *Definition*: member 22. *Mechanism
  consumers*: `scalar_for_field`, [inspect][inspect]
  `::_matched_scalar_key` (walk legs in FAM-MRO).
  *Contract consumers*: read + filter-input + write paths
  (all resolve through the composed functions, never the
  dict directly — except oracles asserting rows).
  *Oracles*: subclass-resolution, unknown-raises,
  Duration/Binary-raises, `BigAutoField -> int` rows.
  *Projections*: table comments + module docstring.
- **Challenges.** C1 counts 1.
- **Owner + lifetime.** This file (the model-field key
  space lives nowhere else). Stored derivation: the module
  dict — owner this module, validity the process, published
  at import, mutated only by consumer assignment, never
  cleared (documented; registry `clear()` resets enums, not
  this table).
- **Migration.** None.
- **Distinct behavior.** R5 (tables stay per-surface), R6
  (hook stays unvalidated), R11 (form ladder stays a
  ladder).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The subclass + fallthrough oracles
  (each fails its weakening: a base-`Field` catch-all row
  would shadow the raise).
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; oracle `c2ff9fca…`.

### F-OUTMAP — output-object maps (file-local)

- **Contract + variation.** `FIELD_OUTPUT_TYPE_MAP`
  (`ImageField`/`FileField` -> default output objects) and
  `FILESYSTEM_PATH_OUTPUT_TYPE_MAP` (default -> path-bearing
  sibling, keyed on the resolved output so the MRO walk is
  never duplicated). Varies per row (C4/C5 count 1).
- **Sites + roles.** *Definition*: members 23-24.
  *Consumers*: `_field_output_type_for` (walk leg in
  FAM-MRO), `convert_field_output` (swap site), the four
  `_field_output_type_for` call sites. *Oracles*: output-map
  resolution + MRO-precedence + path-swap rows.
- **Challenges.** C4/C5 count 1.
- **Owner + lifetime.** This file. Module dicts; read per
  call; never cleared.
- **Migration.** None.
- **Distinct behavior.** The output-keying (not field-
  keying) of the path map is the load-bearing shape (oracle
  pins the consumer-subclass case at :2248).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The MRO-precedence + swap oracles.
- **Coupling.** D1 (the dict-order prose at the map
  comment); FAM-MRO (walk legs).
- **Freshness.** Target `058f1081…`; oracle `c2ff9fca…`.

### F-SCALAR — scalar pipeline (file-local)

- **Contract + variation.** `scalar_for_field` (MRO lookup,
  raising), `_field_has_choices` (hostile-tolerant choices
  flag), `convert_scalar` (tri-state collapse to
  `effective_null` once; postgres dispatch before the walk;
  choice substitution before widening; widen on
  `effective_null`). Varies per axis (C9/C10 count 1 —
  every widening site reads the collapsed boolean).
- **Sites + roles.** *Definition*: members 30-32 (walk leg
  of 31 rides FAM-MRO; postgres branches ride F-POSTGRES).
  *Consumers*: `convert_field_output`,
  [filters-inputs][filters-inputs], [mutations-inputs][mutations-inputs],
  [rf-converter][rf-converter]. *Oracles*: tri-state rows,
  choice-widening rows, subclass rows, hostile-metadata
  rows. *Projections*: function docstrings.
- **Challenges.** C9/C10 count 1. C2/C3 walk facets ride
  FAM-MRO.
- **Owner + lifetime.** This file. Pure derivation; not
  cached.
- **Migration.** None.
- **Distinct behavior.** The `force_nullable` override
  leaves inner `ArrayField` nullability untouched
  (documented, oracle-pinned).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The tri-state + ordering oracles.
- **Coupling.** F-POSTGRES (branches), FAM-MRO (walk leg).
- **Freshness.** Target `058f1081…`; consumers
  `82b52d97…`, `fc442047…`, `6652d092…`, `dda91365…`;
  oracle `c2ff9fca…`.

### F-POSTGRES — soft postgres dispatch (file-local)

- **Contract + variation.** `_ARRAY_FIELD_CLS` /
  `_HSTORE_FIELD_CLS` soft symbols via the shared optional-
  import owner; `None` = driver absent (walk falls through
  to the raising MRO path); `ArrayField` rejects nesting +
  outer choices, recurses on `base_field` (unset override),
  wraps `list[inner]`; `HStoreField` rejects choices,
  returns `JSON`. Varies per field/branch (C7/C8 count 1).
- **Sites + roles.** *Definition*: members 27-28 + the two
  `convert_scalar` branches. *Mechanism consumer*: the
  shared [utils-imports][utils-imports] owner (this module
  composes it; the planner's `_PostgresBTreeIndex` is the
  sibling consumer — R9). *Oracles*: fake-sentinel rows +
  real-field compatibility rows + sentinel-`None` rows.
- **Challenges.** C7/C8 count 1.
- **Owner + lifetime.** This file (dispatch posture);
  soft-import mechanics owned by [utils-imports][utils-imports].
  Sentinel `None`-ness is import-time process state.
- **Migration.** None.
- **Distinct behavior.** R9 (consumption differs from the
  planner's tuple-membership use).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The sentinel-`None` + rejection
  oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; owner `291ecedd…`
  (CLEAN); sibling `b4dfd4a6…`; oracle `c2ff9fca…`.

### F-ENTRY — read-output entry point (file-local)

- **Contract + variation.** `convert_field_output` routes
  file/image columns to the output object (nullable by
  DEFAULT, `force_nullable` wins when set; path swap on
  the validated opt-in flag) and delegates every other
  column to `convert_scalar` unchanged. Varies per arm
  (C6 counts 1).
- **Sites + roles.** *Definition*: member 34. *Consumer*:
  [types-base][types-base] `::_build_annotations` (every
  non-relation column). *Oracles*: file/image routing,
  default-null, override, delegation, scalar-on-filter-
  path rows. *Projections*: the function docstring.
- **Challenges.** C6 counts 1.
- **Owner + lifetime.** This file. Pure routing; not
  cached.
- **Migration.** None.
- **Distinct behavior.** R10 (the default-`True` vs
  column-`null` split is spec-037 Decision 4, same-file
  intentional separation).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The default-null + delegation
  oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; consumer
  `dda91365…`; oracle `c2ff9fca…`.

### F-SANITIZE — enum-member sanitization (file-local)

- **Contract + variation.** `_NON_IDENT` (ASCII
  non-identifier -> `_`), `_GRAPHQL_RESERVED_ENUM_VALUES`
  (`true`/`false`/`null` casefold set),
  `_is_enum_reserved_member` (`mro` / `_sunder_` /
  class-private shapes mirroring `enum`'s private
  predicates), `_sanitize_member_name` (the 4-step ordered
  rewrite over the raw VALUE, never the label; order
  load-bearing for collision categorization). Varies per
  rule (C12 counts 1 — one body, one call site in the
  core).
- **Sites + roles.** *Definition*: members 25-26, 35-36.
  *Consumer*: `build_enum_from_choices` (sole production
  call site, always with `enum_name`). *Oracles*: direct
  unit rows + reserved-shape + GraphQL-reserved schema
  rows. *Projections*: docstrings.
- **Challenges.** C12 counts 1.
- **Owner + lifetime.** This file. Pure functions; not
  cached.
- **Migration.** None.
- **Distinct behavior.** R3 (sanitize vs reject vs
  introspect); value-not-label stability is the
  load-bearing input choice.
- **Behavioral proof.** `static-reviewed` (sole-call-site
  census; `MEMBER_` spelling census = this file +
  its oracles only).
- **Structural gate.** The direct unit + collision oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; oracle `c2ff9fca…`.

### F-ENUMCORE — shared enum-build core (file-local)

- **Contract + variation.** `build_enum_from_choices`
  (reject empty / malformed pairs; reject grouped form
  detected on the LABEL slot; sanitize values; reject
  sanitize collisions with a sorted diagnostic; build +
  `strawberry.enum`). Single `Enum(`/`strawberry.enum(`
  construction site package-wide. Varies per guard (C11/
  C13 count 1).
- **Sites + roles.** *Definition*: member 37. *Consumers*:
  `convert_choices_to_enum` (read side) and
  [rf-converter][rf-converter] `::_serializer_choice_enum`
  (serializer side) — the already-consolidated sharing
  this core exists for. *Oracles*: malformed / grouped /
  collision / hostile-value rows. *Projections*: the core
  docstring (both callers cite it). Core oracles live in
  [test-converters][test-converters].
- **Challenges.** C11/C13 count 1.
- **Owner + lifetime.** This file. Pure construction; the
  CALLERS own caching (R8).
- **Migration.** None.
- **Distinct behavior.** R8 (caches stay split by key
  space); the label-slot detection is the load-bearing
  grouped-form distinction.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The grouped / collision oracles on
  BOTH flavors (serializer-side rows exercise the same
  core).
- **Coupling.** C-ENUM (name input), R8 (cache split).
- **Freshness.** Target `058f1081…`; consumer
  `6652d092…`; oracle `c2ff9fca…`.

### F-PIPE — read-side enum pipeline (file-local)

- **Contract + variation.** `convert_choices_to_enum`
  (hostile-tolerant metadata read; `(model, field_name)`
  cache check; template name; core delegation; registry
  register; first-wins across sibling types). Varies per
  step (C15 counts 1 — cache mechanics composed from
  [registry][registry] by name).
- **Sites + roles.** *Definition*: member 38 (template
  line :775 rides C-ENUM). *Mechanism consumers*:
  `registry.get_enum` / `register_enum`, `pascal_case`,
  the core. *Contract consumers*: `convert_scalar`,
  [filters-inputs][filters-inputs]. *Oracles*: generation,
  cache-key, sibling-sharing, empty/collision raises,
  hostile-metadata rows.
- **Challenges.** C15 counts 1. C14 rides C-ENUM.
- **Owner + lifetime.** This file (pipeline order);
  cache storage owned by [registry][registry] (verified
  `type-registry-enum-cache`; `clear()` resets it).
- **Migration.** None.
- **Distinct behavior.** R8 (first-wins registry cache
  vs name-keyed member-compare cache).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The cache-key + sibling-sharing
  oracles.
- **Coupling.** C-ENUM (template line).
- **Freshness.** Target `058f1081…`; registry
  `81bd561c…`; strings `991f7dad…`; oracle `c2ff9fca…`.

### F-LABEL — diagnostic label (file-local)

- **Contract + variation.** `_field_label` renders
  `Model.field` from a field object, tolerating unbound
  (`<unbound>`) and hostile metadata (per-slot
  `BaseException` fallback + `_safe_text`). Varies on the
  shape only (C18 counts 1).
- **Sites + roles.** *Definition*: member 29. *Consumers*:
  every converter diagnostic. *Oracles*: hostile-metadata
  rows. *Projections*: [exceptions][exceptions] cites this
  rule as a `_safe_text` consumer.
- **Challenges.** C18 counts 1.
- **Owner + lifetime.** This file. Pure render; not
  cached.
- **Migration.** None.
- **Distinct behavior.** R2 (guarded object-label vs raw
  inline compositions vs string renderer vs info label).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The unreadable-metadata oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; oracle `c2ff9fca…`.

### F-RELANN — relation annotation (file-local)

- **Contract + variation.** `resolved_relation_annotation`
  renders `list[target]` on `FieldMeta.is_many_side`,
  else `target | None` on `FieldMeta.nullable`, else
  bare `target`; `field_meta=None` builds fresh from the
  field (the sole `or FieldMeta` seam package-wide).
  Varies on the shape (C19 counts 1).
- **Sites + roles.** *Definition*: member 39.
  *Consumers*: [types-finalizer][types-finalizer] (always
  with `field_map` meta), direct/test callers (default
  seam). *Oracles*: `tests/types/test_base.py` widening
  row + finalizer relation rows. The [inspect][inspect]
  nullability column reads `FieldMeta` slots + the
  synthesized annotation for DISPLAY — it reimplements
  nothing (verified at :300-336).
- **Challenges.** C19 counts 1.
- **Owner + lifetime.** This file (read-output shape);
  cardinality/nullability sourced from [field-meta][field-meta]
  (verified `optimizer-hint-shape` neighbor, not this rule).
  Pure derivation; not cached.
- **Migration.** None.
- **Distinct behavior.** R7 (output shape vs input
  id-triple).
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** The widening + finalizer oracles.
- **Coupling.** None.
- **Freshness.** Target `058f1081…`; consumer
  `de34ae2a…`; meta `18ea719a…`; oracles `0d070aee…`,
  `c2ff9fca…`.

### C-ENUM — `generated-choice-enum-name-template` (ADOPT into the OPEN family)

Following the verified serializer-FAM-SRC / base-C6 precedent
(adoption record; the family item decides the owner with this
member in its sweep):

- **Contract.** The GraphQL name of a generated choice enum
  from `(owning-type-name, field-name)`:
  `f"{type_name}{pascal_case(field_name)}Enum"`.
- **Sites + roles.** Owner: TBD by the family item
  (candidate [types-converters][types-converters], which owns
  the enum-build core + already imports `pascal_case`). This
  target's role: MEMBER — the :775 definition line. Fresh
  evidence at HEAD: `}Enum"` code-spelling census
  package-wide = exactly 2 (:775 here with
  `(DjangoType-name, model-field-name)` inputs;
  [rf-converter][rf-converter] :885 with
  `(generated-input-name, serializer-field-name)` inputs —
  both opaque strings composing the ONE `pascal_case`) + 1
  docstring restatement (:744 — projection, not a
  definition). Caching is explicitly NOT in this family
  (R8).
- **Worker 0 transcription:** none — the family row already
  covers `types/converters.py`. The census above rides with
  the adoption for the family sweep. No new family.
- **Challenges.** C14 counts 2 (a template change moves
  both lines; enum-name oracles follow as consumers).
- **Behavioral proof.** `static-reviewed` (both lines read
  at HEAD bytes; census re-derived, matching the recorded
  2+1).
- **Coupling.** F-PIPE (hosts the line), R8 (cache split).
- **Freshness.** Target `058f1081…`; member peer
  `6652d092…`; helper `991f7dad…`.

### FAM-MRO — `mro-map-key-lookup` (NEW FAMILY for Worker-0)

- **Contract + variation.** The first class in
  `type(field).__mro__` keying a class map (or absence).
  Varies as the lookup (scan order, membership test,
  hardening); the three fallthrough postures (raise /
  `None` / fallback name) stay per site.
- **Sites + roles.** *Definitions (3)*, same question
  spelled thrice at HEAD bytes: `scalar_for_field` :343-345
  (value-or-raise over `SCALAR_MAP`),
  `_field_output_type_for` :494-496 (value-or-`None` over
  `FIELD_OUTPUT_TYPE_MAP`), [inspect][inspect]
  `::_matched_scalar_key` :480-483 (key-NAME-or-concrete-
  name over `SCALAR_MAP` — the naming predictor over the
  same dispatch). Hardened sibling (listed, not counted):
  [utils-converters][utils-converters] `::convert_with_mro`
  :131-135 (identity scan + hostile-MRO-safe read inside
  flavor dispatch with prechecks — the posture a hardening
  change converges toward). Excluded on body strength:
  the override-detection scan + declaration scan (verified
  R14 — different questions), the form-field ladder (R11).
  *Consumers*: every `scalar_for_field` /
  `_field_output_type_for` call site; the CLI converter
  column. *Oracles*: MRO-subclass rows on both halves
  (read + CLI).
- **Challenges.** C2 counts 3 (identity-scan hardening
  must move all three or they disagree); C3 counts 3 (a
  firing-row rule change moves all three; the CLI would
  otherwise misattribute). The skeleton arm already
  embodies the hardened posture (listed, not counted).
- **Owner + lifetime.** Candidate: this module via a
  `_mro_key_for(mapping, field)`-shaped helper both maps
  and the CLI compose ([inspect][inspect] already imports
  from here — no dependency reversal). The family item
  decides (the [utils-converters][utils-converters]
  alternative is open). Pure lookup; no stored derivation.
- **Migration (sketch for the family item).** One key
  lookup at the owner; `scalar_for_field` raises on miss,
  `_field_output_type_for` returns `None`, the CLI takes
  the name. Fallthrough verdicts stay per site (the
  standing per-subject direction). Oracles stay (they pin
  resolutions + names, never the spelling).
- **Distinct behavior.** The three fallthroughs are
  per-subject verdicts, not lookup facets; the skeleton's
  prechecks + fallthrough factory stay flavor dispatch.
- **Behavioral proof.** `static-reviewed` for the COUNT
  (all three walks read at HEAD bytes). Consolidation
  proof owed by the family item.
- **Structural gate.** Owed by the family item (a
  three-site spelling gate with its negative control: a
  hand copy passing the resolution oracles).
- **Coupling.** BLOCKED-ON-HUNT for the two same-file
  legs: the worktree carries the hunt's in-flight
  unification (`_class_map_lookup` identity scan at
  worktree `f6cadb08…`, hunks 3/4/9 of the dirt diff —
  3 the helper intro, 4 + 9 the two leg rewrites) —
  the family item reconciles with the hunt before
  consolidating those legs; the CLI leg's hunt dirt
  (worktree `truth.mro` read, membership still plain) is
  likewise hunt-owned.
- **Freshness.** Target `058f1081…` (work `f6cadb08…`);
  [inspect][inspect] `2807d0fc…`;
  [utils-converters][utils-converters] `5332f054…`;
  oracles `c2ff9fca…`, `9b1360d0…`.

### R1 — except arms vs shared guard (rejected)

The eleven `BaseException` arms here (three fallbacks in
`_field_label`, eight `ConfigurationError` wraps — seven
per-subject messages; the three choices-inspection guards
(:326/:765/:782) share one wording over three distinct
guarded reads with no sync obligation, so no family) vs
one shared guard driver. Contract
difference: per-site verdict + per-subject message, each
failing exactly its own weakening. CONVERGE with the
verified `_request_body.py` J1 shared-except-guard direction
on fresh evidence (arms re-censused at HEAD bytes).
Reconsideration trigger: the standing J1 trigger (a guard
whose verdict + message are identical across sites).
Freshness: target `058f1081…`.

### R2 — diagnostic label vs raw compositions (rejected)

`_field_label` (guarded `Model.field` from a field OBJECT:
unbound + hostile tolerance) vs the raw inline
`{model.__name__}.{field.name}` f-strings (bound-field
assumption: [permissions][permissions],
[rf-converter][rf-converter] :573/:842,
[types-base][types-base] :1944, [registry][registry] :571) vs
[types-finalizer][types-finalizer] `::_safe_field_label`
(plain-STRING renderer, different input) vs
[list-field][list-field] `::_field_label` (GraphQL-info-path
label — same name, different contract). Contract
differences: guarded vs bound-assumed vs string-input vs
info-input. Fresh pair, no prior verdict. Reconsideration
trigger: one owned label helper every diagnostic site
composes. Freshness: target `058f1081…`, finalizer
`de34ae2a…`, list-field `21380eb7…`.

### R3 — sanitize vs reject gates (rejected)

Enum-member sanitization (invalid -> `MEMBER_`-prefix,
never raise) vs the `Meta.name` / derived-name reject gates
(invalid -> raise, now held by open `graphql-name-gate`)
vs [conf][conf] `__getattr__` dunder short-circuit
(introspection safety). Contract differences: sanitize vs
reject vs introspect — three rules sharing only the `__`
token. CONVERGE with verified R18 on fresh evidence
([conf][conf] byte-identical to the cited blob; sanitize
body re-read; the reject legs' family move changes
nothing here). Reconsideration trigger: the standing R18
trigger (one owned name-safety rule). Freshness: target
`058f1081…`, conf `c6ad46aa…` (CLEAN at the cited bytes).

### R4 — dispatch walks vs override/collection scans (rejected)

The `SCALAR_MAP` / output-map dispatch walks (type->value
lookup) vs `_detect_custom_get_queryset` (override
detection) vs the sets-mixins declaration scan (attr
collection). Contract difference: three different questions
asked of three different MROs. CONVERGE with verified R14
on fresh evidence. Reconsideration trigger: the standing
R14 trigger re-checked UNFIRED — no owned bare-MRO helper
exists at HEAD (`convert_with_mro` is flavor dispatch with
prechecks, not a key lookup; FAM-MRO names the key-lookup
candidate separately and excludes R14's three-question
spread). Freshness: target `058f1081…`.

### R5 — scalar table vs surface tables (rejected)

One shared converter map across [types-converters][types-converters]
`::SCALAR_MAP`, [scalars][scalars] `::_PACKAGE_SCALAR_MAP`,
[forms-converter][forms-converter] `::_SCALAR_FORM_FIELDS`,
[rf-converter][rf-converter] `::_BUILTIN_SCALAR_CONVERTERS`.
Difference: key roots pairwise disjoint (`models.Field` vs
scalar types vs `forms.Field` vs `serializers.Field`),
value spaces disjoint (scalars vs definitions vs
conversions), contracts disjoint (shared read/filter +
last-write-wins hook vs registration vs column-less +
NullBoolean/exact-type arms vs column-less + ModelField row
+ validated hook). CONVERGE with verified R-TABLES on a
fresh census (26/12/16/1 — exact match). Reconsideration
trigger: the standing trigger (a new surface whose
population is a SUBSET of an existing key space with
identical value contract). Freshness: target `058f1081…`,
scalars `5e354042…`, forms `37f3ff39…`, serializer
`6652d092…`.

### R6 — bare hook vs validated register (rejected)

`SCALAR_MAP[FieldCls] = py_type` (last-write-wins bare dict
assignment, no validation, silent shadow) vs
[rf-converter][rf-converter] `::register_serializer_field_converter`
(subclass + callable + override-guard validation, each with
its own diagnostic). Difference: unguarded vs validated —
sharing the spelling would unguard that hook or validate
this one (opposite change responses today). CONVERGE with
verified R-EXT-HOOK on fresh evidence (both bodies
re-read). Reconsideration trigger: the standing trigger
(`SCALAR_MAP` gaining validation, or the register hook
dropping it). Freshness: target `058f1081…`, serializer
`6652d092…`.

### R7 — relation annotation vs input triple (rejected)

`resolved_relation_annotation` (OUTPUT shape:
`list[target]` / `target | None` / `target` over the
resolved target TYPE) vs [mutations-inputs][mutations-inputs]
`::relation_input_annotation` (INPUT shape: `<field>_id` /
plain-name triple over the id SCALAR — `GlobalID` vs raw
pk). Contract difference: output object shape vs input id
shape (different names, different scalars, different
nullability sources). Fresh pair, no prior verdict.
Reconsideration trigger: one relation-shape rule spanning
output + input. Freshness: target `058f1081…`, mutations
`fc442047…`.

### R8 — read enum cache vs serializer enum cache (rejected)

`(model, field_name)` + first-wins + registry storage here
vs descriptor-name-keyed + member-set-compare + module-dict
storage at [rf-converter][rf-converter]. Difference: the key
spaces are disjoint by construction (model columns vs
serializer-only fields can never collide), so one cache
would key two populations that never meet. CONVERGE with
the FAM-ENUM-recorded R-CACHE split on fresh evidence
(both bodies re-read). Reconsideration trigger: a choice
source addressable in both key spaces. Freshness: target
`058f1081…`, serializer `6652d092…`, registry
`81bd561c…`.

### R9 — postgres sentinel consumptions (rejected)

`None`-check + `isinstance` dispatch here (branch to
array/hstore conversion) vs `None`-check + tuple
membership in [nested-planner][nested-planner]
(`_BTREE_INDEX_TYPES` construction). Difference: dispatch
consumption vs membership consumption over the ONE shared
[utils-imports][utils-imports] owner — the sharing already
exists at the import; the consumptions answer different
questions. Fresh pair, no prior verdict. Reconsideration
trigger: one postgres-optional consumption rule.
Freshness: target `058f1081…`, owner `291ecedd…`
(CLEAN), planner `b4dfd4a6…`.

### R10 — file default-null vs column-null (rejected)

Same-file intentional separation (spec-037 Decision 4):
the file branch defaults nullable (`True` when the
tri-state is unset — the resolver returns `None` for an
empty `FieldFile`, reachable even on `null=False`
columns) vs the scalar branch following `field.null`.
Contract difference: resolver-shape nullability vs column
nullability. Reconsideration trigger: the file resolver
stops returning `None` for empty files. Freshness:
target `058f1081…`, resolver peer `72d62dc4…`.

### R11 — MRO dispatch vs form-field ladder (rejected)

The MRO-walk dispatch (most-specific registered ancestor
wins, miss raises) vs [filters-inputs][filters-inputs]
`::_scalar_from_form_field` (linear `isinstance` ladder
over django-filter FORM fields with a `str` fallback +
kept-explicit `CharField` branch per spec-027 Decision 4).
Contract difference: model-field dispatch with fail-loud
miss vs form-field fallback typing (the ladder exists
precisely where no model field backs the filter).
Fresh pair, no prior verdict. Reconsideration trigger:
one scalar-resolution rule spanning model + form fields.
Freshness: target `058f1081…`, filters `82b52d97…`.

## Defects

Two minor doc-only HEAD defects on CLEAN lines (normal
closeout homing; owner the target's prose in both). No
security routing (no authorization / routing / exposure).

- **D1 — dict-order mechanism misstated (module docstring
  :26-28 + map comment :259-265).** Both claim `ImageField`
  is "listed BEFORE FileField SO the MRO walk hits it
  first". The walks iterate `type(field).__mro__` and only
  membership-test the dict (`SCALAR_MAP` is never iterated
  package-wide — verified by census), so dict order is
  irrelevant; MRO order decides. The map comment's own
  analogy disproves it: `PositiveBigIntegerField` is listed
  AFTER `IntegerField` (:235-240) yet resolves first.
  [forms-converter][forms-converter] states the correct
  mechanism ("regardless of dict insertion order"). Fix =
  reword the reason (MRO order decides; most-specific-first
  dict order is conventional), not reorder. Owner:
  `types/converters.py` prose.
- **D2 — consumer census understated (module docstring
  :26-30 + `_field_output_type_for` docstring :491-492).**
  Both claim the walk is shared by `convert_field_output`
  and `resolvers._attach_file_resolvers` ONLY. Two more
  production call sites compose it at HEAD:
  [types-base][types-base] :1679 (the `filesystem_path_fields`
  validator) and [inspect][inspect] :401 (the converter
  column) — 4 production consumers, not 2. Owner:
  `types/converters.py` prose.

## Judgment

Zero-edit file item, ready for verification. All 40
`ast.Module.body` members homed: 13 file-local findings,
1 adoption into open `generated-choice-enum-name-template`
(C14 count 2, census re-derived 2+1), 1 new holding family
`mro-map-key-lookup` (C2/C3 count 3, hunt-coupled), 11
rejections (6 CONVERGE on fresh trigger checks, 5 fresh
pairs). Two minor doc-only defects filed for normal
closeout homing. No consolidation inside the file item;
no production edits; no `## Pending execution` (all proofs
`static-reviewed` from read-only inspection — no workspace
runs were needed or made).

## Index rows for Worker-0

- `| types-converters-module-mechanics | django_strawberry_framework/types/converters.py (module docstring + 15 import statements binding 18 names, all consumed) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-storage-guard | django_strawberry_framework/types/converters.py::_safe_file_attr | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-file-output-objects | django_strawberry_framework/types/converters.py::DjangoFileType (+ DjangoImageType, _FileSystemPathFields, DjangoFilePathType, DjangoImagePathType) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-scalar-map | django_strawberry_framework/types/converters.py::SCALAR_MAP (26 rows incl. file-str rows + bare-assignment hook) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-output-maps | django_strawberry_framework/types/converters.py::FIELD_OUTPUT_TYPE_MAP (+ FILESYSTEM_PATH_OUTPUT_TYPE_MAP; walk legs ride mro-map-key-lookup) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-scalar-pipeline | django_strawberry_framework/types/converters.py::convert_scalar (+ scalar_for_field, _field_has_choices, force_nullable tri-state) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-postgres-dispatch | django_strawberry_framework/types/converters.py::_ARRAY_FIELD_CLS (+ _HSTORE_FIELD_CLS + convert_scalar array/hstore branches) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-read-output-entry | django_strawberry_framework/types/converters.py::convert_field_output | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-enum-sanitization | django_strawberry_framework/types/converters.py::_sanitize_member_name (+ _is_enum_reserved_member, _NON_IDENT, _GRAPHQL_RESERVED_ENUM_VALUES) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-enum-build-core | django_strawberry_framework/types/converters.py::build_enum_from_choices | django_strawberry_framework/types/converters.py, django_strawberry_framework/rest_framework/serializer_converter.py | File types/converters.py | file-local |`
- `| types-converters-choice-enum-pipeline | django_strawberry_framework/types/converters.py::convert_choices_to_enum (cache-check + name + core delegation + register; template line rides generated-choice-enum-name-template) | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-diagnostic-label | django_strawberry_framework/types/converters.py::_field_label | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| types-converters-relation-annotation | django_strawberry_framework/types/converters.py::resolved_relation_annotation | django_strawberry_framework/types/converters.py | File types/converters.py | file-local |`
- `| mro-map-key-lookup | TBD by family item (candidate: django_strawberry_framework/types/converters.py via a _mro_key_for(mapping, field)-shaped helper; utils/converters.py alternative open; blocked-on-hunt for the two same-file legs) | django_strawberry_framework/types/converters.py, django_strawberry_framework/management/commands/inspect_django_type.py | Family mro-map-key-lookup | open |`
- `| types-converters-except-arms-vs-shared-guard | django_strawberry_framework/types/converters.py (rejection recorded here; CONVERGE with the verified shared-except-guard J1 direction on fresh evidence — 11 per-site arms, 3 fallbacks + 8 wraps) | django_strawberry_framework/types/converters.py | File types/converters.py | rejected |`
- `| types-converters-label-vs-raw-compositions | django_strawberry_framework/types/converters.py::_field_label (rejection recorded here; fresh — guarded object-label vs bound-assumed inline vs string renderer vs info label) | django_strawberry_framework/types/converters.py, django_strawberry_framework/types/finalizer.py, django_strawberry_framework/list_field.py, django_strawberry_framework/permissions.py, django_strawberry_framework/rest_framework/serializer_converter.py, django_strawberry_framework/registry.py, django_strawberry_framework/types/base.py | File types/converters.py | rejected |`
- `| types-converters-sanitize-vs-name-gates | django_strawberry_framework/types/converters.py::_sanitize_member_name (rejection recorded here; CONVERGE with verified R18 on fresh evidence — sanitize vs reject vs introspect; conf byte-identical) | django_strawberry_framework/types/converters.py, django_strawberry_framework/types/base.py, django_strawberry_framework/types/definition.py, django_strawberry_framework/conf.py | File types/converters.py | rejected |`
- `| types-converters-dispatch-vs-override-scans | django_strawberry_framework/types/converters.py::scalar_for_field (rejection recorded here; CONVERGE with verified R14 on fresh evidence — three questions, three MROs; trigger re-checked unfired; sets_mixins byte-identical) | django_strawberry_framework/types/converters.py, django_strawberry_framework/types/base.py, django_strawberry_framework/sets_mixins.py | File types/converters.py | rejected |`
- `| types-converters-table-vs-surface-tables | django_strawberry_framework/types/converters.py::SCALAR_MAP (rejection recorded here; CONVERGE with verified R-TABLES on fresh evidence — 26/12/16/1 census exact match) | django_strawberry_framework/types/converters.py, django_strawberry_framework/scalars.py, django_strawberry_framework/forms/converter.py, django_strawberry_framework/rest_framework/serializer_converter.py | File types/converters.py | rejected |`
- `| types-converters-hook-vs-validated-register | django_strawberry_framework/types/converters.py::SCALAR_MAP (rejection recorded here; CONVERGE with verified R-EXT-HOOK on fresh evidence — bare last-write-wins vs validated register) | django_strawberry_framework/types/converters.py, django_strawberry_framework/rest_framework/serializer_converter.py | File types/converters.py | rejected |`
- `| types-converters-relation-annotation-vs-input-triple | django_strawberry_framework/types/converters.py::resolved_relation_annotation (rejection recorded here; fresh pair — output shape vs input id-triple, no prior verdict) | django_strawberry_framework/types/converters.py, django_strawberry_framework/mutations/inputs.py | File types/converters.py | rejected |`
- `| types-converters-enum-cache-vs-serializer-cache | django_strawberry_framework/types/converters.py::convert_choices_to_enum (rejection recorded here; CONVERGE with the FAM-ENUM-recorded R-CACHE split on fresh evidence — disjoint key spaces) | django_strawberry_framework/types/converters.py, django_strawberry_framework/rest_framework/serializer_converter.py, django_strawberry_framework/registry.py | File types/converters.py | rejected |`
- `| types-converters-postgres-sentinel-vs-planner-sentinel | django_strawberry_framework/types/converters.py::_ARRAY_FIELD_CLS (rejection recorded here; fresh pair — isinstance dispatch vs tuple membership over the one shared owner) | django_strawberry_framework/types/converters.py, django_strawberry_framework/optimizer/nested_planner.py, django_strawberry_framework/utils/imports.py | File types/converters.py | rejected |`
- `| types-converters-file-null-vs-column-null | django_strawberry_framework/types/converters.py::convert_field_output (rejection recorded here; same-file intentional separation — resolver-shape vs column nullability, spec-037 Decision 4) | django_strawberry_framework/types/converters.py, django_strawberry_framework/types/resolvers.py | File types/converters.py | rejected |`
- `| types-converters-form-ladder-vs-mro-walk | django_strawberry_framework/types/converters.py::scalar_for_field (rejection recorded here; fresh pair — model-field dispatch vs form-field fallback ladder) | django_strawberry_framework/types/converters.py, django_strawberry_framework/filters/inputs.py | File types/converters.py | rejected |`

## Families

Worker-0 must add one `## Families` item:

- `Family mro-map-key-lookup — dry-rule-mro-map-key-lookup.md — no artifact on disk; undispatched (named by File types/converters.py FAM-MRO; blocked-on-hunt for the two same-file legs)`

## Independent verification (Worker-2)

Traced at HEAD bytes (`058f1081…`, 807 lines) before
opening `## Findings`; worktree `f6cadb08…` (768 lines,
14-hunk hunt dirt) used only for dirt attribution. No
workspace runs (read-only `git show` / `git grep`
inspection; zero-edit file item, all counts static).
No `.py` touched — no ruff owed. Sharded/PG:
inapplicable by construction (pure construction-time
conversion; no database, alias, or dialect surface).

### My pre-findings trace

AST enumeration at HEAD: 40 `Module.body` members
(1 docstring + 15 imports binding 18 names + 24
definitions); member names and lines match the
artifact's table row-for-row (#16 `_safe_file_attr`
:82 through #39 `resolved_relation_annotation`
:795). All 18 import names consumed (each use
verified). Homes I chose before reading: 13
file-local groups (mechanics / guard / file objects /
scalar map / output maps / scalar pipeline / postgres
/ entry / sanitize / enum core / enum pipeline /
label / relation annotation); enum-name template →
adopt into open `generated-choice-enum-name-template`
(transcribes nothing — the plan row already covers
both files); MRO dispatch → new family.

My `}Enum"` census (fresh): exactly 2 code sites
(`types/converters.py:775`,
`rest_framework/serializer_converter.py:885`, both
`f"{type_name}{pascal_case(<name>)}Enum"` over the
ONE `utils/strings::pascal_case`) + 1 docstring
projection (:744) + 1 test comment
(`tests/types/test_converters.py:898`, immaterial).

My `__mro__` sweep (all 11 code sites): the two
same-file value walks (`scalar_for_field` :343-345
raise-on-miss, `_field_output_type_for` :494-496
None-on-miss); `inspect::_matched_scalar_key`
:480-483 (key-NAME derivation over `SCALAR_MAP`);
`utils/converters::convert_with_mro` :131-135
(hardened identity scan inside flavor dispatch);
override detection (`types/base.py:868`,
`types/definition.py:385`), declaration collection
(`sets_mixins.py:334`, `types/finalizer.py:248`),
membership filter (`types/relay.py:146`), defect
scan (`utils/querysets.py:1110`). Zero `mro()`
calls; zero `SCALAR_MAP` iterations (membership
tests only); `SCALAR_MAP[` read directly only by
`scalar_for_field` itself plus oracle row asserts.
I first picked the skeleton arm as the third leg
and `_matched_scalar_key` as a projection; on the
change-challenge test I REVISE to W1's population
(see reconciliation). Consumer map re-derived:
`scalar_for_field` → filters/mutations/serializer
inputs; `convert_scalar` → mutations/serializer
inputs; `convert_field_output` → `types/base`;
`build_enum_from_choices` → serializer choice arm;
`convert_choices_to_enum` → filters inputs;
`resolved_relation_annotation` → finalizer;
`_field_output_type_for` → base :1679, resolvers
:880, inspect :401, plus the internal entry call.

### Reconciliation (every difference explicit)

- Third leg (mine skeleton-arm vs W1 CLI-leg):
  W1 CORRECT. `_matched_scalar_key` re-derives the
  firing row by the same means over the same map and
  must move with C2/C3 or misattribute — a
  definition under axis 3, not a projection. The
  skeleton arm is generic (parameter registry,
  foreign field universes, staged precheck +
  fallthrough contract) and already embodies C2's
  outcome (contributes 0 to the headline
  challenge); absorbing it would need mode flags
  (principle 5). Listing it uncounted with the
  alternative open is sound routing; the family
  item re-sweeps the mechanism.
- R1 census: W1 wrote 9 arms / 6 wraps; HEAD has
  11 / 8 (E-W2-1, corrected in place). The
  three same-message choices guards share wording
  over distinct reads with no sync obligation —
  no family owed. CONVERGE conclusion stands.
- FAM-MRO hunk cite: W1 wrote 3/9/14; hunk 14 is
  the `convert_choices_to_enum` guard-drop, not an
  MRO leg (E-W2-2, corrected in place to 3/4/9).
  Substance (both legs hunt-rewritten) holds; the
  CLI leg's worktree `truth.mro` read with plain
  membership verified byte-for-byte.
- J1 trigger wording: W1 paraphrases; the standing
  text ("a new guard needing the same
  position-state classification") likewise does
  not fire here. Stands.
- All else: zero differences. Enumeration 40/40,
  all six matrix axes (axis 2 inapplicable: zero
  async tokens verified; axis 6: 4 widening sites,
  Duration/Binary + default-`enum_name` oracles,
  FileField-choices partition all verified),
  C-ENUM adoption, all six convergences (R-TABLES
  26/12/16/1 re-derived exact; R-EXT-HOOK,
  R-CACHE, R18, R14 triggers re-checked unfired
  at current bytes), all five fresh rejections
  (R2/R7/R9/R10/R11 bodies re-read), all five
  proof censuses (`MEMBER_`, `NotImplementedError`,
  `or FieldMeta`, `Enum(`, no-iteration), all 31
  fingerprints digit-for-digit, all 4 CLEAN
  claims, 25/25 index rows + Families item
  matching their findings.

### Errata (Worker-2, non-verdict-moving)

- E-W2-1: R1 census corrected in place (finding +
  index row): 9 → 11 arms (3 fallbacks + 8
  wraps), with the shared-wording triple
  reconciled above. Rejection stands.
- E-W2-2: FAM-MRO coupling hunk cite corrected
  in place: 3/9/14 → 3/4/9. Blocked-on-hunt
  stands.

### Defects / window / verdict

No new target defect (no `## Defects` entry owed).
Window vs `ITEM_BASELINE=5345c9e0…`: the plan hunk
(Worker-0's dispatch record) + the
`review-0_0_15.md` hunks (review-flow conf.py tick,
ledger rows, drift line) are both concurrent /
out-of-scope by content, left alone; the only
other window content is this untracked artifact.
`## Pending execution` correctly absent (all
proofs `static-reviewed`). Verdict: `verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-base]: dry-file-types__base.md
[dry-serializer-conv]: dry-file-rest_framework__serializer_converter.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[permissions]: ../../django_strawberry_framework/permissions.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py

<!-- examples/ -->
[test-query-readme]: ../../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

