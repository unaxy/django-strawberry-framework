# DRY review: `django_strawberry_framework/rest_framework/serializer_converter.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; one
family ADOPTED on fresh evidence (`serializer-source-axis-normalization`,
row exists, candidate owner confirmed as this file), one new family
named for Worker 0 (`generated-choice-enum-name-template`), every other
rule recorded file-local with its proving challenge, converged onto a
verified family or rejection on fresh evidence, or fresh-rejected with
contract difference + trigger. Zero production edits; zero tracked
files changed; no `## Owned changes` rows (file items land none).

HEAD at dispatch `5ee86193`, still `5ee86193` at every fingerprint
below and at finish (see `## Implementation (Worker 1)`). Target HEAD
blob `32904418a169941c2afa1c9cd6866c55debc64f3`; worktree blob
`95568390a70e6a40acad9639c24dfe2bde263ffa` (+24/-14, 6 hunks of
concurrent bug-hunt dirt, attributed by diff content below, left
untouched). The trace reads HEAD bytes throughout
(`git show HEAD:...`); connected-body claims against dirty files are
likewise judged at THEIR HEAD bytes, with both fingerprints recorded
where relied on. Never compare one method against the other:
HEAD fingerprints via `git rev-parse HEAD:<path>`, worktree via
`git hash-object <path>`.

## System trace

Target owns the serializer-flavor PER-FIELD mapping
(`django_strawberry_framework/rest_framework/serializer_converter.py`,
1060 lines at HEAD): the `serializers.Field`-keyed scalar registry
(`_BUILTIN_SCALAR_CONVERTERS`, 16 rows) + live registry
(`_SERIALIZER_FIELD_CONVERTERS`) + the sanctioned extension
(`register_serializer_field_converter`), the fail-loud dispatch
(`convert_serializer_field`: ordered prechecks, scalar MRO walk,
raising fallthrough), the extension boundary
(`_finish_serializer_conversion`), the nested detection +
fail-loud default (`is_nested_serializer_field`,
`nested_serializer_child`, `_reject_nested_serializer`) + the
serializer-only nested kinds (`NESTED_SINGLE` / `NESTED_MULTI`), the
relation gate (`_reject_unsupported_relation_field` + the cardinality
trio), the list-child recursion (`_list_child_conversion`), the
id-like-suffix naming rule (`serializer_field_graphql_name`), the
description synthesis (`serializer_field_description`), the one-segment
source guard (`require_one_segment_source`), the source-keyed backing
resolve (`backing_model_field`), the strict primary policy
(`_require_relation_primary`), the serializer-only relation routing
(`serializer_only_relation_annotation`), the type-override conflict
policy (`_model_backed_scalar_annotation` + helpers), the choice-enum
upgrade + name-keyed cache (`_serializer_choice_enum` et al), and the
dual-routing seam (`resolve_serializer_field`: model-backed vs
column-less + `InputFieldSpec` construction + the `source`-axis
normalization line).

Converter vs shaper (which owns what — verified against both bodies at
HEAD, converging with the verified [dry-inputs][dry-inputs] split on
fresh evidence): this module maps ONE field (registry + dispatch +
routing + reverse-map record construction); [rf-inputs][rf-inputs] owns
everything needing the FIELD SET (discovery, narrowing, descriptor
identity + naming + namespace lifecycle, the walk, the nested
RECURSION, the drift fingerprint, the ownership guards). The seam is
`resolve_serializer_field(field, model, type_name)`, called per field
from the walk ([rf-inputs][rf-inputs] `::_walk_serializer_fields`),
from injected-spec resolution, and from the resolvers' agreement
recompute ([rf-resolvers][rf-resolvers] `::_assert_field_agreement`
half of verified J12); the one bypass is the explicitly-opted-in
nested field, which the walk routes to `_resolve_nested_field` FIRST
(this module would reject it — the opt-in-only default). Layering is
one-directional at HEAD: [rf-inputs][rf-inputs] imports 7 names from
here (`NESTED_MULTI`, `NESTED_SINGLE`,
`is_nested_serializer_field`, `nested_serializer_child`,
`require_one_segment_source`, `resolve_serializer_field`,
`serializer_field_description`), [rf-resolvers][rf-resolvers] 7
(the 5 kinds + `nested_serializer_child` +
`resolve_serializer_field`), [rf-sets][rf-sets] 2 (the nested
detectors); zero imports flow back (the `rest_framework/inputs.py`
hits in this file are docstring/comment prose only).

Read whole at HEAD bytes: [rf-inputs][rf-inputs] regions (walk,
`_resolve_nested_field`, fingerprint, injected specs — the file is
CLEAN so worktree reads are HEAD reads), [forms-converter][forms-converter]
(full, CLEAN), [utils-converters][utils-converters] (full, CLEAN),
[types-converters][types-converters] (full, HEAD snapshot),
[mutations-inputs][mutations-inputs] (`relation_id_scalar`,
`relation_id_annotation`, `related_model_of_queryset`,
`require_queryset_related_model`, `annotate_queryset_relation`,
`relation_input_annotation`, `model_column_write_kind`,
`model_column_write_annotation`, `model_column_input_annotation` —
HEAD snapshot), [forms-inputs][forms-inputs]
(`_model_column_for`, `_model_less_relation_annotation`,
`_simple_triple`, `_field_triple_and_spec` — HEAD snapshot),
[utils-inputs][utils-inputs] (kind block, `FieldConversionBase`,
`InputFieldSpec` — HEAD snapshot), [rf-sets][rf-sets]
(`_validate_schema_field_map`, `_serializer_input_shape_for` region —
HEAD snapshot), [rf-resolvers][rf-resolvers] (agreement +
attestation source reads — HEAD snapshot), oracles
[test-converter][test-converter] (76 `def test` lines at HEAD;
header + fixtures + section pins read at HEAD bytes) +
[test-skeleton][test-skeleton] (shared-maker pins, CLEAN) +
[test-ratchet][test-ratchet] (import-identity pins, CLEAN), live
serializer rows in [test-library-api][test-library-api] (names at
HEAD; bodies via the verified [dry-inputs][dry-inputs] trace),
[lib-schema][lib-schema] (CLEAN, opt-in site, via verified trace),
contract source [spec-039][spec-039] (Decision 4 shared-helper
homes, Decision 7 mapping, Improvements nested section — CLEAN),
and the verified artifacts [dry-forms-conv][dry-forms-conv],
[dry-inputs][dry-inputs], [dry-resolvers][dry-resolvers],
[dry-clear][dry-clear] as triggers (every convergence re-derived
on fresh body evidence below, never inherited).

Dirt note (every connected-body claim below is against HEAD bytes;
worktree bytes were never relied on): target DIRTY (`32904418…` /
`95568390…` — 6 hunt hunks: `_safe_type_name` label swaps in the
three rejection helpers + `_list_child_conversion` + two BEHAVIOR
dirt hunks, child-`allow_null` widening and `allow_blank` enum
exclusion, which D3/D4 observe conditionally). Dirty-but-judged-at-HEAD
(work `…` / HEAD `…`): [rf-resolvers][rf-resolvers] `c0b54039…` /
`8024703e…`, [rf-sets][rf-sets] `70a1e1b1…` / `2c7117d6…`,
[forms-inputs][forms-inputs] `436fcf42…` / `55614839…`,
[types-converters][types-converters] `679c9448…` / `9ceb34af…`,
[utils-inputs][utils-inputs] `47b2af21…` / `ee31d360…`,
[mutations-inputs][mutations-inputs] `fcbb964d…` / `fc442047…`,
[utils-strings][utils-strings] `ffa4fee0…` / `3ec3b262…`,
[registry][registry] `612bea87…` / `9cc8bb55…`,
[test-converter][test-converter] `9d5d0eaf…` / `b12dde99…`,
[test-library-api][test-library-api] `2cd94a6a…` / `1f107fff…`.
HEAD-body snapshots were taken via `git show HEAD:<path>` before any
judgment; full blob ids sit in each finding's Freshness row. Clean
witnesses re-hashed both sides: [rf-inputs][rf-inputs]
(`9b17d952…`), [forms-converter][forms-converter] (`b717fd0f…`),
[utils-converters][utils-converters] (`5332f054…`),
[exceptions][exceptions] (`e06b0b7f…`), [scalars][scalars]
(`5e354042…`), [test-skeleton][test-skeleton] (`9799bb9b…`),
[test-ratchet][test-ratchet] (`7b198141…`), [spec-039][spec-039]
(`cf78af93…`), [lib-schema][lib-schema] (`bed9d071…`).

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched, read side FIRST then
   both write twins whole. One mapping or three? THREE (R-TABLES,
   CONVERGE with verified [dry-forms-conv][dry-forms-conv] F-reuse on
   a fresh census: 26 `models.Field` keys / 1 scalar-type key / 12
   `forms.Field` keys / 16 `serializers.Field` keys, pairwise
   disjoint roots, disjoint value contracts; what should be shared
   already is — skeleton, value shape, kind vocabulary, model-backed
   delegation by name, enum-build core). Read side:
   model-backed columns delegate to `convert_scalar` /
   `scalar_for_field` / `model_column_write_annotation` by name (0
   here-definitions, C23); the enum-build CORE is shared
   (`build_enum_from_choices`) but the enum-NAME template is spelled
   twice (FAM-ENUM, count 2). Forms twin: same skeleton, same value
   shape, same kind vocabulary (all `is`-pinned by
   [test-ratchet][test-ratchet] + [test-skeleton][test-skeleton]);
   the tables, precheck orders, fallthrough wordings, requiredness
   bases, backing resolves, and relation routings all diverge by
   flavor contract (R-FALLTHROUGH, R-REQUIRED, R-TRIPLE, R-SERONLY,
   R-BACKING, R-EXT-HOOK). Mutations twin: id-type rule
   (`relation_id_scalar`), cardinality wrap, queryset spine, column
   classifier consumed by name (0 here); naming + source +
   primary-required + conflict stay here. Set twins
   (filters/orders): no lookup/order vocabulary here (zero
   `LOOKUP`/`Ordering`/`FilterSet`/`OrderSet` tokens), no build-time
   normalizer (zero `normalize_input_value` — decode is runtime in
   [rf-resolvers][rf-resolvers]; CONVERGE with verified
   `serializer-no-build-normalizer` on fresh evidence, no new row),
   no Layer-6 surface (zero `make_dynamic_set_getter`).
2. **Sync/async twins** — inapplicable with reason: zero `async
   def`, zero `await`, zero `sync_to_async`, zero
   `run_in_one_sync_boundary` in the target (grep count 0 at HEAD);
   pure finalize-time construction over field instances + in-memory
   dict reads; no ORM execution (the `model._meta.get_field` /
   `registry.get` reads are schema-time introspection, never queries);
   the sync write pipeline lives in [rf-resolvers][rf-resolvers],
   which consumes this module's kinds/specs, never re-implements the
   mapping — no colored twin to compare.
3. **Derived rather than repeated knowledge** — searched. Canonical
   derivations owned elsewhere and composed by name: kind spellings
   ([utils-inputs][utils-inputs], `is`-pinned), value shape
   (`FieldConversionBase`, subclassed), skeleton + makers
   ([utils-converters][utils-converters], `__code__`-pinned),
   id scalar / classifier / queryset spine
   ([mutations-inputs][mutations-inputs]), read scalars + enum core
   ([types-converters][types-converters]), camel/pascal
   ([utils-strings][utils-strings]), `Upload` ([scalars][scalars]).
   Two genuine second spellings found: the source-axis
   None-normalization, character-identical here and in
   [rf-inputs][rf-inputs] `::_resolve_nested_field` (FAM-SRC,
   count 2, ADOPTED); the generated-enum name template,
   character-identical here and in
   [types-converters][types-converters] `::convert_choices_to_enum`
   (FAM-ENUM, count 2, NEW). The `source or name` effective-source
   reads (the `backing_model_field` line, resolvers
   attest/agreement reads, fingerprint tuple) share tokens with the
   normalization but answer a different question (the attribute to
   use, never `None`-from-equal) — explicitly excluded from FAM-SRC
   with the contract stated in each finding.
4. **Inverse / round-trip pairs** — searched. Encode (this module:
   field → kind + spec) vs decode ([rf-resolvers][rf-resolvers]
   `_decode_*` off the stashed specs) share ONE grammar: the kind
   constants (single-sourced in [utils-inputs][utils-inputs],
   `is`-pinned through this module's re-exports) and the ONE
   `InputFieldSpec` record (constructed here per field, stamped via
   `replace` in [rf-inputs][rf-inputs], read in
   [rf-resolvers][rf-resolvers]). One grammar, two halves, correctly
   separated (CONVERGE direction with verified resolvers J13/J18 on
   fresh evidence: FILE lands in `data`, no `EXCLUDED` arm needed —
   zero `EXCLUDED` tokens here outside one prose `is EXCLUDED`
   sentence). Build-produce vs agreement-recompute is the verified
   J12 round-trip (resolvers recompute via this module's
   `resolve_serializer_field` + compare — merging would destroy the
   check; no new row). Nested encode (`nested_specs` stamped in
   [rf-inputs][rf-inputs]) vs nested decode (resolvers recursing with
   the same per-field machinery) is one contract, two halves; this
   module owns only detection + kinds + the fail-loud default.
5. **Contracts restated in another medium** — searched. Five media:
   production code (definitions here; machinery at the eleven
   composed owners); contract source ([spec-039][spec-039] Decision
   7 mapping + precheck order + renamed-fields rule, Decision 4
   skeleton/shared-helper homes, Improvements nested section —
   read; every module-docstring decision citation re-checked, D1
   records the one dangling slot); independent oracles
   ([test-converter][test-converter] 76 tests spelling literals —
   message `match=` pins, name-pair pins, source-value pins,
   kind-flag pins, MRO pins, enum-dedupe/collision pins; the
   registry fixture snapshots/restores for hygiene, never derives
   expectations from the table; [test-skeleton][test-skeleton]
   pins the shared makers by `__code__` identity;
   [test-ratchet][test-ratchet] pins 19 shared bindings by object
   identity); live wire ([test-library-api][test-library-api]
   serializer rows, e.g. `test_create_shelf_via_serializer_happy_path`
   at HEAD); projections (module/class/function docstrings —
   verified clause-by-clause against the bodies and live DRF class
   spellings; the Decision-4 skeleton citation is defensible via the
   spec's shared-helper-homes row, D1 excepted). No test iterates an
   owner table to build expectations.
6. **Enforcement by omission** — enumerated. Serializer-only rules
   with no twin owed: `DurationField` → `str` is explicit here
   while the read map + forms table omit it (each absence is its own
   contract — [spec-039][spec-039] mandates this row; no contract
   source mandates the others — not a gap); bare-`Field` exact-type
   `str` exists forms-only (this flavor has no such case; an
   unmapped bare field raises by the fail-loud default, oracle-pinned
   — not a gap); the cardinality guard exists here only while the
   forms column arm trusts the column (no [spec-038][spec-038] row
   requires a forms check — grep count 0 for
   cardinality/mismatch — so per axis 6 NOT a defect, recorded as
   considered); description synthesis exists here only (zero
   `help_text` in `forms/` — no contract source requires a forms
   twin — not a gap); `is_input` parity exists here only (graphene
   parity row names the serializer upstream only — not a gap). No
   missing guard with a contract source behind it — no omission
   defect filed. The two HEAD-vs-dirt observations (D3/D4) are
   hunt-owned lines, filed observed-not-homed with
   closeout-conditional wording, not as omission defects.

### Enumeration

Instrument: `ast.parse` over the HEAD bytes (`/tmp` snapshot of
`git show HEAD:…`), counting `ast.Module.body` statements —
**65 top-level statements** (1 docstring + 22 imports + 41
`Assign`/`AnnAssign`/`FunctionDef`/`ClassDef` bindings + 1
`register_subsystem_clear` call) — plus the one class body member
(`__slots__`; the class carries no methods). **65 rows binding 75
module names + 1 class member**, every one homed below (F =
file-local, C = convergence onto a verified family/rejection
needing no new row, R = fresh rejection, FAM = family).
Dual-homed rows are one unit with two roles, not double counts.

| # | Statement | Binds | Home |
|---|---|---|---|
| 0 | module docstring (registry + dispatch + reverse-map prose) | (none) | prose projection, all findings (D1-adjacent slot noted) |
| 1–10 | `__future__`, `datetime`, `decimal`, `uuid`, `Callable`, `Any`, `strawberry`, `FieldDoesNotExist`, `models`, `serializers` | 10 names | consumer feeds (F-TABLE/F-BACKING/F-DISPATCH) |
| 11 | `ConfigurationError`, `_safe_arg_repr`, `_safe_type_name` import | 3 names | F-FAILLOUD/F-DESC consumers (C: composed-by-name renderers) |
| 12 | `annotate_queryset_relation`, `model_column_write_annotation`, `model_column_write_kind` import | 3 names | F-RESOLVE/F-SERONLY consumers |
| 13 | `register_subsystem_clear`, `registry` import | 2 names | F-CHOICE-ENUM + F-PRIMARY consumers |
| 14 | `Upload` import | 1 name | F-RESOLVE consumer |
| 15 | `build_enum_from_choices`, `convert_scalar`, `scalar_for_field` import | 3 names | F-CONFLICT/F-CHOICE-ENUM/F-TABLE consumers |
| 16 | `convert_with_mro`, `finish_field_conversion`, `make_kind_converter`, `make_scalar_converter` import | 4 names | F-DISPATCH/F-TABLE/F-EXTBOUND consumers |
| 17–20 | `FILE`, `RELATION_MULTI`, `RELATION_SINGLE`, `SCALAR` re-exports | 4 names | F-KINDS |
| 21 | `FieldConversionBase`, `InputFieldSpec` import | 2 names | F-SHAPE + F-RESOLVE consumers |
| 22 | `graphql_camel_name`, `pascal_case` import | 2 names | F-NAME + F-CHOICE-ENUM consumers |
| 23 | `NESTED_SINGLE` | 1 name | F-KINDS |
| 24 | `NESTED_MULTI` | 1 name | F-KINDS |
| 25 | `class SerializerFieldConversion` + `__slots__` | 1 + 1 | F-SHAPE |
| 26 | `SerializerFieldConverter` alias | 1 name | F-REG |
| 27 | `def _scalar_converter` | 1 name | F-TABLE (thin wrapper) |
| 28 | `def _model_field_converter` | 1 name | F-TABLE (ModelField row) |
| 29 | `_BUILTIN_SCALAR_CONVERTERS` (16 rows) | 1 name | F-TABLE + R-TABLES |
| 30 | `_SERIALIZER_FIELD_CONVERTERS` (live registry) | 1 name | F-REG + R-EXT-HOOK |
| 31 | `_CONVERT_RELATION_MULTI` | 1 name | F-DISPATCH |
| 32 | `_CONVERT_RELATION_SINGLE` | 1 name | F-DISPATCH |
| 33 | `_CONVERT_FILE` | 1 name | F-DISPATCH |
| 34 | `_CONVERT_MULTIPLE_CHOICE` | 1 name | F-DISPATCH |
| 35 | `def register_serializer_field_converter` | 1 name | F-REG + R-EXT-HOOK |
| 36 | `_SERIALIZER_CHOICE_ENUMS` | 1 name | F-CHOICE-ENUM + R-CACHE |
| 37 | `def clear_serializer_choice_enums` | 1 name | F-CHOICE-ENUM (C: verified `subsystem-clear-lifecycle` m17) |
| 38 | `register_subsystem_clear(...)` call | bus row `rest_framework.choice_enums` | F-CHOICE-ENUM (C) |
| 39 | `def is_nested_serializer_field` | 1 name | F-NESTED |
| 40 | `def nested_serializer_child` | 1 name | F-NESTED |
| 41 | `def _reject_nested_serializer` | 1 name | F-NESTED |
| 42 | `def _reject_unsupported_relation_field` | 1 name | F-REL-GATE |
| 43 | `def _list_child_conversion` | 1 name | F-LIST (D3 lines) |
| 44 | `def _finish_serializer_conversion` | 1 name | F-EXTBOUND |
| 45 | `def convert_serializer_field` (+ 4 closures) | 1 name | F-DISPATCH + F-FAILLOUD wiring |
| 46 | `def _unsupported_serializer_field` | 1 name | F-FAILLOUD + R-FALLTHROUGH |
| 47 | `def _relation_cardinality` | 1 name | F-REL-GATE |
| 48 | `def _model_relation_cardinality` | 1 name | F-REL-GATE + R-CARD |
| 49 | `def _reject_relation_cardinality_mismatch` | 1 name | F-REL-GATE |
| 50 | `def serializer_field_graphql_name` | 1 name | F-NAME (C: R-nestname holds) |
| 51 | `def serializer_field_description` | 1 name | F-DESC + R-EXCEPT |
| 52 | `def require_one_segment_source` | 1 name | F-SOURCE-GUARD (D1 lines) |
| 53 | `def backing_model_field` | 1 name | F-BACKING + R-BACKING |
| 54 | `def _require_relation_primary` | 1 name | F-PRIMARY |
| 55 | `def serializer_only_relation_annotation` | 1 name | F-SERONLY-REL + R-SERONLY |
| 56 | `def _is_consumer_declared` | 1 name | F-CONFLICT |
| 57 | `def _scalar_name` | 1 name | F-CONFLICT |
| 58 | `def _model_backed_scalar_annotation` | 1 name | F-CONFLICT |
| 59 | `def _is_enumerable_serializer_choice` | 1 name | F-CHOICE-ENUM (D4 lines) |
| 60 | `def _enum_member_map` | 1 name | F-CHOICE-ENUM |
| 61 | `def _serializer_choice_enum` | 1 name | F-CHOICE-ENUM + FAM-ENUM (name line) |
| 62 | `def _serializer_choice_annotation` | 1 name | F-CHOICE-ENUM |
| 63 | `def _serializer_only_scalar_annotation` | 1 name | F-CHOICE-ENUM |
| 64 | `def resolve_serializer_field` | 1 name | F-RESOLVE + FAM-SRC (source line) + R-TRIPLE (D2 lines) |

Rules: R-table scalar registry (27–29); R-reg live registry +
extension (26, 30, 35); R-dispatch precheck order + entry (31–35,
45); R-fail-loud fallthrough (46); R-nested detection (39–41);
R-relgate relation gate + cardinality (42, 47–49); R-list
list-child (43); R-extbound extension boundary (44); R-name
suffix rule (50); R-desc descriptions (51); R-srcguard one-segment
guard (52); R-backing column resolve (53); R-primary strict
primary (54); R-seronlyrel queryset routing (55); R-conflict
override policy (56–58); R-enum choice upgrade + cache (36–38,
59–63); R-resolve dual routing (64); R-shape value object (25);
R-kinds vocabulary (17–20, 23–24). One family ADOPTED (FAM-SRC),
one new family named (FAM-ENUM), nineteen file-local rows, ten
fresh rejections with difference + trigger + home (4 converging
with prior verdicts on fresh evidence), plus fourteen no-new-row
convergences (see F-NOSURF) — all named for Worker 0 (see
`## Index rows for Worker 0`).

Static probes (AST + `git grep` at HEAD, read-only):
`normalize_input_value`, `model_for`, `base_queryset`,
`type_name_for`, `make_dynamic_set_getter`, `describe_value`,
`generated_input_type_name`, `require_drf`, `Ordering`, `LOOKUP`,
`FilterSet`, `OrderSet`, `CREATE`, `PARTIAL`, `operation_kind`
appear **zero** times in the target; `coerce` / `EXCLUDED` appear
once each as docstring prose only (`no-silent-coerce` contract
sentence; `is EXCLUDED` filesystem sentence) — no second owner
for any indexed machinery, no normalize twin, no guard call, no
Layer-6 surface, no op vocabulary, no excluded-kind arm.
`InputFieldSpec(` is constructed directly **once** (row 64, every
kind); nested specs are constructed once in
[rf-inputs][rf-inputs] `::_resolve_nested_field` (verified
census, the family-external construction site).

### Challenges

Each change posited against the rule's own variation axes; the
count is authoritative definitions only. Consumers, oracles,
projections listed, never counted. All bodies judged at HEAD bytes.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-table rows | map a new DRF scalar (e.g. `HiddenField` → `str`) | **1 here** (row 29; forms/read twins are disjoint key spaces and do not move) | independent |
| C2 | R-table scalar | change one row's scalar (e.g. `UUIDField` → `str`) | **1 here** (the row) | independent |
| C3 | R-reg extension | tighten registration (e.g. forbid overriding built-ins even with `override=True`) | **1 here** (row 35; `SCALAR_MAP` bare assignment untouched) | independent + R-EXT-HOOK |
| C4 | R-dispatch order | route a new DRF kind (e.g. custom file sibling) | **1 here** (row 45 list; column-kind classifier untouched — disjoint population) | independent |
| C5 | R-fail-loud wording | respell the unsupported-field diagnostic | **1 here** (row 46; forms factory untouched) | independent + R-FALLTHROUGH |
| C6 | R-nested detection | new nested shape (e.g. DRF adds a serializer kind) | **1 here** (rows 39–41 move as one rule; recursion in [rf-inputs][rf-inputs] follows) | independent |
| C7 | R-relgate support | support a new relation kind (e.g. slug with a shape + decode) | **1 here** (row 42 + decoders move as one rule) | independent |
| C8 | R-list contract | change the list-child rule (e.g. allow file children) | **1 here** (row 43; D3 conditions the nullability axis) | independent |
| C9 | R-extbound smuggling | forbid a new smuggled shape through the scalar registry | **1 here** (row 44; forms has no registration hook) | independent |
| C10 | R-name suffix | change the id-like dedupe (e.g. `_pk` stops being id-like) | **1 here** (row 50; `relation_input_annotation` 036 scheme untouched) | independent |
| C11 | R-desc synthesis | new description axis (e.g. fold `default`) | **1 here** (row 51; no forms twin exists) | independent |
| C12 | R-srcguard detection | widen the one-segment policy (e.g. allow two-segment) | **1 here** (row 52; both consumers follow as enforcement sites) | independent |
| C13 | R-backing resolve | change source semantics (e.g. default `source` handling) | **1 here** (row 53; forms name-keyed resolve untouched) | independent + R-BACKING |
| C14 | R-primary strictness | allow the raw-pk fallback (form parity) | **1 here** (row 54; form `registry.get` untouched) | independent |
| C15 | R-seronlyrel routing | change queryset-model discovery | **1 here** (row 55; `annotate_queryset_relation` spine untouched) | independent + R-SERONLY |
| C16 | R-conflict policy | change the override rule (e.g. declared always wins) | **1 here** (rows 56–58 move as one rule) | independent |
| C17 | R-enum upgrade | change enum eligibility / cache / dedupe | **1 here** (rows 36–38, 59–63 move as one rule; build core untouched) | independent + R-CACHE |
| C18 | R-resolve routing | change the model-backed/column-less split | **1 here** (row 64; forms triple untouched) | independent + R-TRIPLE |
| C19 | R-shape value object | change `(annotation, kind, required)` | **0 here** (owned by [utils-inputs][utils-inputs] `::FieldConversionBase`) | independent — proves consumer |
| C20 | R-kinds spelling | respell a kind constant | **0 here** for the base four (owner [utils-inputs][utils-inputs]); **1 here** for the nested pair | split — proves both |
| C21 | source normalization | record equal-source explicitly (never `None`) | **2** (row 64 line + [rf-inputs][rf-inputs] `::_resolve_nested_field` line — character-identical) | ADOPT FAM-SRC |
| C22 | enum-name template | change the `<Type><Field>Enum` template | **2** (row 61 line + [types-converters][types-converters] `::convert_choices_to_enum` line — character-identical modulo the `field.` read) | NEW FAMILY FAM-ENUM |
| C23 | read scalars | change `SCALAR_MAP` / `convert_scalar` / enum core | **0 here** (read side moves; this module follows as consumer) | no surface — do not inherit |
| C24 | MRO mechanics | change the walk / maker / finish mechanics | **0 here** (owned by [utils-converters][utils-converters]) | no surface — do not inherit |
| C25 | table merge | unify all converter tables into one map | **refused** (R-TABLES: four key spaces, four contracts) | rejected-merge — proves distinct rules |
| C26 | triple merge | merge row 64 with the forms triple | **refused** (R-TRIPLE: source axis + conflict + primary + cardinality have no forms analog) | rejected-merge |
| C27 | cardinality derivation | derive cardinality from the column kind / taxonomy | **refused** (R-CARD: both shared classifiers answer a different question — reverse-FK proves it) | rejected-merge |
| C28 | enum-cache merge | route the name-keyed cache through the registry | **refused** (R-CACHE: name-keyed + member-compare vs `(model, field)` + first-wins) | rejected-merge |
| C29 | fallthrough merge | one shared unsupported-field factory | **refused** (R-FALLTHROUGH: per-subject rejection grammars) | rejected-merge — CONVERGE standing |
| C30 | except-guard merge | one shared hostile-attr guard | **refused** (R-EXCEPT: per-site catch sets + diagnostics) | rejected-merge — CONVERGE standing |
| C31 | requiredness merge | route requiredness through `form_field_required` | **refused** (R-REQUIRED: NullBoolean is forms-only; the `required_of=None` default IS this rule) | rejected-merge — CONVERGE forms |
| C32 | extension-hook merge | unify `register_*` with `SCALAR_MAP` assignment | **refused** (R-EXT-HOOK: validated register + override guard vs last-write-wins dict) | rejected-merge |
| C33 | backing merge | unify source-keyed and name-keyed column resolve | **refused** (R-BACKING: renames + dotted/star reject vs reverse/GFK guards + corrupted arms) | rejected-merge |
| C34 | colocation merge | colocate the mapping in [rf-inputs][rf-inputs] | **refused** (CONVERGE with verified `serializer-split-vs-colocated-converters` on fresh evidence — registry + dual routing + source axis) | rejected-merge — no new row |

No executable proof was run: every claim above is a byte-level
`git grep` census over HEAD blobs, an `ast.parse` enumeration, or
a body read against oracles that pin the behavior (76 converter
tests + the identity-gate twins + live rows). Nothing inspected
decides ordering beyond finalize-time construction, transactions,
async behavior, or ORM execution; the two count-2 rules are
character-identical spelling pairs whose consolidation proofs
belong to their family items. No `docs/dry/temp-tests/` scratch
was created (HEAD snapshots lived under `/tmp`, outside the repo).
All claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof.

## Findings

No production edit is owed by a file item; each finding records the
rule with the challenge that proved it has no second site
(convergences name their holding family; rejections carry difference
+ trigger; the two count-2 rules name their families for Worker 0).

### F-TABLE — serializer scalar table (file-local) + R-TABLES

- **Contract + variation.** Rows 27–29 map 16
  `serializers.Field` classes to `SCALAR`-kind converters for the
  column-less path (row 27 is the thin `field.required`
  wrapper; row 28 routes `ModelField` through its wrapped column's
  `scalar_for_field`, failing loud with no wrapped field or over an
  unsupported column). Every entry is EXPLICIT (the no-catch-all
  contract): `DictField`→`JSON` (covering `HStoreField` via the
  MRO walk), `IPAddressField`/`FilePathField`/`DurationField`→`str`
  (each shadowing a parent that would otherwise win —
  `FilePathField`'s row also keeps dynamic path choices OUT of the
  enum path), `ChoiceField`→`str` as the base the build site
  upgrades. Varies by adding/removing a serializer-field row (C1/C2
  count 1).
- **Sites + roles.** *Definition*: rows 27–29 + the row-45
  scalar-walk arm (one body, within-file factoring). *Mechanism
  consumers*: the walk (`convert_with_mro`), the value shape
  (`make_scalar_converter`, `__code__`-pinned by
  [test-skeleton][test-skeleton]), the read scalar
  (`scalar_for_field` for the ModelField row — C23 counts 0 here).
  *Kind consumer*: row 64's column-less arm + the row-43 recursion.
  *Oracles*: scalar parametrize + expanded-matrix parametrize +
  MRO-under-parent rows + ModelField trio in
  [test-converter][test-converter]. *Projections*: table comment +
  module docstring (MRO claims read against the `serializers.*`
  spellings). Rejected unification: R-TABLES.
- **Challenges.** C1 counts 1; C2 counts 1.
- **Owner + lifetime.** This file (the serializer key space lives
  nowhere else). No stored derivation beyond the module dicts (read
  per call; row 30 persists for the process by documented design).
- **Migration.** None.
- **Distinct behavior (R-TABLES).** Considered: one shared
  converter map. Difference (CONVERGE with verified
  [dry-forms-conv][dry-forms-conv] F-reuse on a fresh census, never
  inherited): [types-converters][types-converters] `::SCALAR_MAP`
  (26 `models.Field` keys, shared read-output + filter-input
  contract, choice substitution by callers, last-write-wins hook),
  [scalars][scalars] `::_PACKAGE_SCALAR_MAP` (1 scalar-TYPE key,
  registration contract), [forms-converter][forms-converter]
  `::_SCALAR_FORM_FIELDS` (12 column-less `forms.Field` keys,
  NullBoolean arm, exact-type bare-`Field` case, NO registration
  hook), this table (16 column-less `serializers.Field` keys,
  ModelField wrapped-column row, nested kinds beside it, `is_input`
  parity, consumer-registration hook). Fresh census at HEAD: 26 / 1
  / 12 / 16, key roots pairwise disjoint (`models.Field` vs scalar
  types vs `forms.Field` vs `serializers.Field`), value spaces
  disjoint (scalars vs definitions vs conversions). What should be
  shared already is: the skeleton, the value shape, the kind
  vocabulary, model-backed delegation by name, the enum-build core.
  Trigger: a new surface whose field population is a SUBSET of an
  existing table's key space with identical value contract (a new
  KIND of population keeps its own table). Durable home: each
  table's key-space prose (read and accurate) + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a key space
  overlaps another" (spelling census over HEAD blobs) and "a row
  is reached by fallthrough" (explicit-row comment + the
  catch-all-shadowing oracle).
- **Structural gate.** The scalar + expanded-matrix parametrizes,
  the MRO pins, and `test_unknown_custom_field_subclass_raises`
  (fails exactly on a base-`Field` catch-all weakening); no
  failability run owed.
- **Coupling.** None.
- **Freshness.** Target HEAD `32904418…` (work `95568390…`);
  [types-converters][types-converters] HEAD `9ceb34af…` (work
  `679c9448…`); [forms-converter][forms-converter] `b717fd0f…`
  (CLEAN); [scalars][scalars] `5e354042…` (CLEAN);
  [utils-converters][utils-converters] `5332f054…` (CLEAN);
  [test-converter][test-converter] HEAD `9d5d0eaf…` (work
  `b12dde99…`); [test-skeleton][test-skeleton] `9799bb9b…`
  (CLEAN); [dry-forms-conv][dry-forms-conv] work `accdf1f1…`
  (trigger only).

### F-REG — live registry + sanctioned extension (file-local) + R-EXT-HOOK

- **Contract + variation.** Row 30 is the LIVE registry the MRO
  walk consults (seeded from row 29; row 35 mutates it); row 26 is
  the `callable(field) -> SerializerFieldConversion` signature;
  row 35 validates (`field_class` must be a `serializers.Field`
  subclass, converter must be callable) and guards re-registration
  (`override=True` or a distinct subclass — a typo fails loud
  rather than silently shadowing). Varies on the validation /
  override rule (C3 counts 1).
- **Sites + roles.** *Definition*: rows 26, 30, 35 (one rule).
  *Consumer*: the row-45 MRO walk (registered classes + their
  unregistered subclasses resolve; unregistered customs still
  raise). *Oracles*: register-then-map, MRO-subclass resolution,
  override-guard, non-field-class, non-callable rows + the
  snapshot/restore hygiene fixture in [test-converter][test-converter].
- **Challenges.** C3 counts 1.
- **Owner + lifetime.** This file. Stored derivation: the live
  registry — owner this module, validity the process, published at
  import + registration, mutated only by row 35, NOT reset by
  `registry.clear()` (documented; the fixture restores it in
  tests).
- **Migration.** None.
- **Distinct behavior (R-EXT-HOOK).** Considered: unifying with
  the read-side `SCALAR_MAP` extension hook (the module docstring
  says "Mirrors"). Difference (fresh pair, no prior verdict): this
  is a VALIDATED register function (subclass check + callable
  check + override guard, each with its own diagnostic); the
  read-side hook is last-write-wins BARE dict assignment
  (`SCALAR_MAP[FieldCls] = py_type`, no validation, silent
  shadow). Sharing the spelling would either unguard this hook or
  validate that one — opposite change responses today. Trigger:
  `SCALAR_MAP` gaining validation, or this hook dropping it.
  Durable home: the row-35 docstring mirror clause + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "an
  unregistered custom maps" (raise-then-register oracle) and "a
  double registration shadows" (override-guard oracle).
- **Structural gate.** The registration oracle rows (each fails
  its weakening: dropped subclass check admits non-fields; dropped
  override guard silently shadows); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [types-converters][types-converters] HEAD `9ceb34af…` (hook
  prose only); oracles as in F-TABLE.

### F-DISPATCH — dispatch entry + precheck order (file-local)

- **Contract + variation.** Row 45 runs the relation / file /
  list / multi-choice prechecks first (rows 31–34 values + the
  nested/relation/list closures), then the scalar registry MRO
  walk, then the raising fallthrough — never a
  `serializers.Field -> str` catch-all. `is_input` is
  accepted-and-ignored ([spec-039][spec-039] Decision 7 graphene
  parity; deliberately NO dead branch). Order is load-bearing
  where a kind subclasses a scalar entry (`MultipleChoiceField`
  under `ChoiceField`→`str`; nested serializers before `ListField`
  so a nested field is named, not list-mapped). Varies by adding a
  DRF kind (C4 counts 1).
- **Sites + roles.** *Definition*: rows 31–34 + row 45 (one body).
  *Mechanism consumer*: `convert_with_mro` (C24 counts 0 here).
  *Consumers*: row 64's column-less arm, the row-43 recursion,
  the row-58 declared-scalar reread. *Oracles*: kind-flag rows,
  `is_input` pin, MRO pins, precheck-subclass rows.
  The spec's precheck-order sentence (Decision 7) matches the body
  order exactly (verified element by element).
- **Challenges.** C4 counts 1.
- **Owner + lifetime.** This file (the DRF-field population
  owner; the forms twin covers a disjoint population with no
  nested kinds). Per-call construction (`_relation_multi` et al
  close over nothing stored).
- **Migration.** None.
- **Distinct behavior.** `del is_input` + no branch is the
  coverage-safe parity shape (a dead `if not is_input:` arm would
  gate-fail `fail_under=100`); forms has no `is_input` (its
  upstream twin has no such parameter — axis-6 considered, no twin
  owed). The `(BaseSerializer, ListSerializer)` tuple mirrors the
  spec's order sentence verbatim (redundant by inheritance,
  explicit by contract — not a defect).
- **Behavioral proof.** `static-reviewed`. Rejects "a kind loses
  to the scalar walk" (kind-flag + subclass oracles) and "the
  entry branches on `is_input`" (body read: `del` + zero
  references).
- **Structural gate.** Kind + MRO + `is_input` oracles (a reorder
  letting the walk win first yields `str` and fails them); no
  failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [utils-converters][utils-converters] `5332f054…` (CLEAN);
  [spec-039][spec-039] `cf78af93…` (CLEAN);
  [test-converter][test-converter] HEAD `9d5d0eaf…`.

### F-FAILLOUD — no-catch-all fallthrough (file-local) + R-FALLTHROUGH

- **Contract + variation.** Row 46 builds the fail-loud
  `ConfigurationError` for an unmapped field (naming field +
  class via the `_safe_*` renderers, with a `field_name`-unreadable
  backstop); row 45 wires it as the skeleton's fallthrough. Varies
  on nothing legitimate: every unmapped shape must keep raising
  (the GOAL no-silent-`String` contract, [spec-039][spec-039]
  Decision 7). This flavor has NO exact-type bare-`Field` case
  (unlike forms `_bare_form_field`) — an unmapped bare field
  raises (oracle-pinned; axis-6 considered, no contract source
  requires the forms case here).
- **Sites + roles.** *Definition*: row 46 + the wiring (one
  body). *Renderer consumers*:
  [exceptions][exceptions] `::_safe_type_name` /
  `::_safe_arg_repr` (imported by name, never redefined —
  composition, CONVERGE with the verified
  [dry-forms-conv][dry-forms-conv] R3 direction on fresh
  evidence). *Oracles*: custom-subclass raise row (+ exact
  message `match=`), hostile-name rows, unbound-field row.
- **Challenges.** C5 counts 1 (wording moves here alone).
- **Owner + lifetime.** This file (the serializer-field
  population's fail-loud boundary). Pure dispatch; nothing stored.
- **Migration.** None.
- **Distinct behavior (R-FALLTHROUGH).** Considered: one shared
  unsupported-field factory for both write flavors. Difference
  (CONVERGE with the standing per-subject-rejection-grammars
  direction — verified [utils-policies][utils-policies] R3 via
  the nested-fetch/hints trigger chain — on fresh evidence): every
  noun differs (serializer vs form field, `convert_serializer_field`
  vs `convert_form_field` self-name, `Meta.fields / Meta.exclude`
  vs `supply a custom input_class field` recourse); the SHAPE
  (factory + skeleton wiring + safe renderers) is already shared
  by construction. A shared factory would parameterize every
  noun — the grammar, not the mechanism, is the rule. Trigger: a
  cross-flavor diagnostic-normalization contract. Durable home:
  the row-46 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a catch-all
  shadows the raise" (custom-subclass oracle with exact message)
  and "a hostile field breaks the diagnostic" (hostile rows).
- **Structural gate.** `test_unknown_custom_field_subclass_raises`
  is the catch-all-shadowing pin (a base-`Field` table entry
  turns it into `String` instead of raising); no failability run
  owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [forms-converter][forms-converter] `b717fd0f…` (CLEAN, factory
  body); [exceptions][exceptions] `e06b0b7f…` (CLEAN);
  [dry-forms-conv][dry-forms-conv] work `accdf1f1…` (trigger only).

### F-NESTED — nested detection + fail-loud default (file-local)

- **Contract + variation.** Rows 39–40 detect a nested
  `Serializer` / `ListSerializer` (`BaseSerializer` test) and
  split it into `(child, many)` (BOUND child — `.child` for many,
  self for single); row 41 raises for any nested field that
  reaches the converter (the opt-in-only default, directing to
  `Meta.nested_fields` / narrow-away / PK-relation). Rows 23–24
  name the nested kinds (see F-KINDS). Varies as one rule (C6
  counts 1: detection + split + default move together).
- **Sites + roles.** *Definition*: rows 39–41 (detection +
  default; the RECURSION lives in [rf-inputs][rf-inputs],
  consumed there by name — this module has no knowledge of it,
  per both docstrings). *Consumers*: the walk's opt-in branch,
  `validate_nested_config_keys`, row 64's nested-first reject,
  the row-43 child reject, resolvers' nested decode/agreement
  (via `nested_serializer_child` + kinds). *Oracles*: nested /
  list-serializer raise rows, detection + child-shape rows, the
  nested-over-relation-column misroute row, list-child-nested
  row.
- **Challenges.** C6 counts 1.
- **Owner + lifetime.** This file (detection owner; pure
  `isinstance` reads + one raise). Nothing stored.
- **Migration.** None.
- **Distinct behavior.** Row 64 rejects nested FIRST, before the
  backing-column lookup, so a nested field over a reverse
  relation can never be misrouted as a relation-id input
  (oracle-pinned) — the same row-41 body, already one site, not a
  second definition. The row-41 wording change in worktree dirt
  is message-preserving modulo the safe-type label (verified by
  concatenating both sides) — hunt-owned, left alone.
- **Behavioral proof.** `static-reviewed`. Rejects "an unopted
  nested field builds silently" (raise rows), "a nested field
  misroutes as relation-id" (misroute row), "detection and
  recursion disagree" (single `BaseSerializer` predicate at both
  call sites).
- **Structural gate.** The nested raise + detection + misroute
  oracles (dropping the nested-first order misroutes and fails
  the misroute row); no failability run owed.
- **Coupling.** None (FAM-SRC migrates the nested SITE's source
  line, not this cluster).
- **Freshness.** Target as in F-TABLE;
  [rf-inputs][rf-inputs] `9b17d952…` (CLEAN, recursion +
  walk-branch bodies); [rf-sets][rf-sets] HEAD `2c7117d6…`
  (validator body); [spec-039][spec-039] `cf78af93…` (CLEAN,
  nested-first sentence).

### F-REL-GATE — relation gate + cardinality agreement (file-local)

- **Contract + variation.** Row 42 admits only PK relations
  (single `PrimaryKeyRelatedField`; `ManyRelatedField` of a PK
  child — a slug / URL / custom relation fails loud naming the
  field, because the package types every relation input as a
  pk-decoding id); rows 47–49 enforce serializer-vs-model
  cardinality agreement (a `many=True` field over a single
  relation, or single over a collection, fails loud naming both
  shapes — the generated input must describe the same shape the
  runtime serializer validates). Varies as one gate rule (C7
  counts 1).
- **Sites + roles.** *Definition*: rows 42, 47–49. *Consumers*:
  the row-45 relation closures + row 64's model-backed relation
  arm (both compose row 42 by name — already one body). *Oracles*:
  single/multi PK rows, slug + non-PK-child raise rows,
  model-backed slug row, mismatch row, the four
  reverse-FK/GenericRelation/reverse-O2O cardinality rows.
- **Challenges.** C7 counts 1; C27 refused (R-CARD).
- **Owner + lifetime.** This file. Pure predicates; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The model flavor derives cardinality
  from the column alone (single source — no conflict possible,
  n/a by construction); the forms column arm trusts the column
  (no [spec-038][spec-038] cardinality row — axis-6 considered,
  NOT a defect: sibling behavior never verdicts).
- **Distinct behavior (R-CARD).** Considered, two refused
  derivations of row 48 (fresh, no prior verdict). (a) Derive
  the collection answer from the shared
  [mutations-inputs][mutations-inputs] `::model_column_write_kind`:
  refused — the classifier answers "which decode kind"
  (`many_to_many` only), while row 48 answers "collection-valued
  side" (`many_to_many` OR `one_to_many`); they DELIBERATELY
  disagree on a reverse FK / GenericRelation (classifier says
  single, cardinality says many), and row 64's MULTI override
  exists precisely because of that disagreement — deriving one
  from the other would reintroduce the single-for-many mis-emit
  the override fixes. (b) Route the read through the
  relation-kind taxonomy: refused — the taxonomy answers "which
  relation kind" for fetch planning over Django `_meta`; row 48
  answers a boolean agreement question for a serializer-vs-model
  check. Different questions, different consumers. Trigger: the
  classifier gaining the collection-shape answer, or the
  taxonomy gaining an agreement-check consumer. Durable home:
  the row-64 override comment + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a non-PK
  relation type-checks" (raise rows) and "a cardinality mismatch
  emits" (mismatch + reverse-shape rows).
- **Structural gate.** The gate + cardinality oracle rows (each
  fails its weakening: admitting slug emits an id the decoder
  misreads; dropping the guard emits single-for-many); no
  failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [spec-039][spec-039] `cf78af93…` (Decision 7 PK-only sentence);
  [spec-038][spec-038] work `e6844a37…` (cardinality grep: 0 hits).

### F-LIST — list-child recursion (file-local)

- **Contract + variation.** Row 43 maps `ListField(child)` to
  `list[<scalar child>]` by recursing the child through row 45;
  a missing child (incl. DRF's `_UnvalidatedField`), a nested
  child, a relation child, or a non-scalar-resolving child raises
  `ConfigurationError` (a relation list is
  `PrimaryKeyRelatedField(many=True)`, never a `ListField` — the
  [spec-039][spec-039] no-back-door rule). At HEAD bytes the
  element is exactly `list[<child scalar>]` — no `allow_null`
  widening (D3 observes the hunt-owned delta conditionally).
  Varies on the child contract (C8 counts 1).
- **Sites + roles.** *Definition*: row 43 (one body; the nested /
  relation rejects compose rows 41–42 by name — already one site
  each). *Consumer*: the row-45 `_list` precheck. *Oracles*:
  scalar-child row, multi-choice row, relation/nested/file-child
  raise rows, no-child row.
- **Challenges.** C8 counts 1.
- **Owner + lifetime.** This file (no forms twin — the forms
  converter has no list kind). Pure recursion; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The child recursion re-enters the SAME
  registry (so a registered custom scalar child resolves); the
  `_UnvalidatedField` name check is the DRF-version-pinned
  sentinel read (one site). The worktree dirt's element
  widening + docstring paragraph are hunt-owned behavior, judged
  in D3, never relied on here.
- **Behavioral proof.** `static-reviewed`. Rejects "a relation
  child list-maps" (raise rows) and "an untyped child emits"
  (no-child row).
- **Structural gate.** The list-child oracle rows (admitting a
  relation child emits a shape the decoder misreads and fails
  them); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE (row-43 dirt is hunt-owned:
  label swaps + D3 widening).

### F-EXTBOUND — scalar-extension boundary (file-local)

- **Contract + variation.** Row 44 finishes one registry result:
  finished conversions pass through; registry callables invoke
  via the shared `finish_field_conversion` (a consumer raise is
  wrapped as `ConfigurationError` naming converter + field, never
  leaking `AttributeError` later); a non-`SerializerFieldConversion`
  return raises; a non-`SCALAR` kind raises (a registered scalar
  converter cannot smuggle a relation / file kind past the
  framework-owned prechecks + build-site metadata). Varies on the
  smuggled-shape rule (C9 counts 1).
- **Sites + roles.** *Definition*: row 44 (one body).
  *Mechanism consumer*: `finish_field_conversion` (C24 counts 0
  here). *Consumer*: row 45's return path (every dispatch result
  passes through it). *Oracles*: malformed-return,
  exception-wrap, and relation-kind-smuggle rows in
  [test-converter][test-converter].
- **Challenges.** C9 counts 1.
- **Owner + lifetime.** This file (forms has no registration
  hook — no twin exists). Pure guard; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The `except ConfigurationError: raise`
  passthrough keeps typed consumer errors typed (only UNtyped
  raises wrap) — the wrap/preserve split is one site.
- **Behavioral proof.** `static-reviewed`. Rejects "a malformed
  extension leaks `AttributeError`" (wrap row) and "a relation
  kind smuggles through" (smuggle row).
- **Structural gate.** The three boundary oracle rows (each fails
  its weakening); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [utils-converters][utils-converters] `5332f054…` (CLEAN).

### F-NAME — id-like-suffix naming rule (file-local)

- **Contract + variation.** Row 50 derives `(input_attr,
  graphql_name)` from the DECLARED serializer field name (never
  `source`): non-relations camel-case with no suffix; single
  relations keep an id-like tail (`_id` / `_pk`) or gain the 036
  `<name>_id` scheme (no doubled `...IdId` / `...PkId`); multi
  relations keep the plain declared name (already a collection of
  ids, matching `relation_input_annotation`). Varies on the dedupe
  (C10 counts 1).
- **Sites + roles.** *Definition*: row 50 (one body).
  *Mechanism consumer*: [utils-strings][utils-strings]
  `::graphql_camel_name` (composed by name — C-change moves once
  upstream). *Consumers*: row 64 (all three arms), row 55, the
  walk (via row 64), resolvers' recompute (via row 64). The
  verified `serializer-nested-name-vs-suffix-rule` rejection
  holds from this side on fresh evidence: nested names compose
  `graphql_camel_name` directly because nested kinds sit OUTSIDE
  the relation suffix contract (no new row — the inputs-side row
  stands). *Oracles*: the id-like parametrize + multi-name rows.
- **Challenges.** C10 counts 1.
- **Owner + lifetime.** This file. Pure function; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The scalar arm and the multi arm share
  an identical body by CONTRACT COINCIDENCE (no-suffix-by-rule vs
  already-a-collection-by-rule) — a multi-naming change must not
  move scalar naming, so the split documents two rules; folding
  them would couple distinct reasons to change (within-file
  intentional separation, not a defect).
- **Behavioral proof.** `static-reviewed`. Rejects "a declared
  `_id` doubles" (parametrize) and "naming reads `source`"
  (signature takes the name string only).
- **Structural gate.** The naming oracle rows (dropping the
  dedupe doubles `category_id` → `categoryIdId` and fails them);
  no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [utils-strings][utils-strings] HEAD `3ec3b262…` (work
  `ffa4fee0…`); [rf-inputs][rf-inputs] `9b17d952…` (CLEAN,
  nested-name body).

### F-DESC — description synthesis (file-local) + R-EXCEPT

- **Contract + variation.** Row 51 threads DRF validation
  metadata into SDL DOCUMENTATION (never a second validator):
  `help_text` head + coherent constraint summary (`min_*` /
  `max_*`, `allow_blank` when permitted, `allow_empty` when
  forbidden); no metadata yields `None` (field undescribed).
  Hostile metadata raises typed `ConfigurationError` (never a raw
  leak). Varies on the summary axes (C11 counts 1).
- **Sites + roles.** *Definition*: row 51 (one body; no forms
  twin — zero `help_text` in `forms/` at HEAD, axis-6
  considered, no contract source requires one). *Consumers*: the
  walk (emitted descriptions), the fingerprint (description
  discriminant), the shape identity. *Oracles*: combine-head,
  none-without-metadata, bounds, allow-empty, hostile-metadata,
  unreadable-name rows.
- **Challenges.** C11 counts 1.
- **Owner + lifetime.** This file. Pure read; nothing stored.
- **Migration.** None.
- **Distinct behavior (R-EXCEPT).** Considered: one shared
  hostile-attr guard for the row-51 `BaseException` wrap, the
  row-46 name backstop, and the read-side/forms twins.
  Difference (CONVERGE with the standing shared-except-guard
  direction — verified `_request_body.py` J1 via the
  hints/nested-fetch/nested-planner/join-taxonomy trigger chain
  — on fresh evidence): catch SETS differ (broad metadata wrap
  vs narrow name backstop vs storage-shaped vs corrupted-internal
  arms) and DIAGNOSTICS differ per subject (description-render
  vs fallthrough vs label vs column-resolve nouns). The
  `except-then-typed-raise` SHAPE is an idiom, not a rule; sharing
  it would couple independent catch contracts. Trigger: a
  cross-module catch-set + diagnostic normalization contract.
  Durable home: the row-51 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a hostile
  `help_text` leaks raw" (hostile rows) and "an empty field
  emits a dangling description" (none-row).
- **Structural gate.** The description oracle rows (each fails
  its weakening); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [exceptions][exceptions] `e06b0b7f…` (CLEAN);
  [rf-inputs][rf-inputs] `9b17d952…` (CLEAN, consumer bodies).

### F-SOURCE-GUARD — one-segment source detection (file-local)

- **Contract + variation.** Row 52 raises when a bound field's
  `source_attrs` is not exactly one segment (`source="*"` →
  `[]`; dotted → multi-element); an unbound field (no
  `source_attrs`) passes. `field_label` / `must_map_to` keep the
  diagnostic nouns at each call site without a second predicate
  copy. Varies on the segment policy (C12 counts 1).
- **Sites + roles.** *Definition*: row 52 (the ONE detection —
  `source_attrs` appears nowhere else in the package outside one
  prose mention + this body). *Consumers*: row 53 (column
  resolve) + [rf-inputs][rf-inputs] `::_resolve_nested_field`
  (nested writes) — both enforcement sites, counted once under
  C12. *Oracles*: star/dotted reject rows (column path) + nested
  dotted/star rows (nested path).
- **Challenges.** C12 counts 1 (both consumers follow).
- **Owner + lifetime.** This file (already the shared owner —
  no consolidation owed). Pure predicate; nothing stored.
- **Migration.** None.
- **Distinct behavior.** D1 records the docstring's dangling
  second citation slot (`(spec-039 Decision 7 / )` — the nested
  half lives in the spec's unnumbered Improvements section, so
  the slot has no number to cite; fix by naming the section or
  dropping the `/ `).
- **Behavioral proof.** `static-reviewed`. Rejects "a second
  `source_attrs` predicate exists" (package census: 1 body) and
  "a dotted source resolves" (reject rows on both paths).
- **Structural gate.** The star/dotted oracle rows on both
  paths (a second predicate copy drifting would fail one side);
  no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE (row-52 lines CLEAN —
  untouched by hunt dirt); [rf-inputs][rf-inputs] `9b17d952…`
  (CLEAN, nested consumer); [spec-039][spec-039] `cf78af93…`
  (CLEAN, renamed-fields + nested rows).

### F-BACKING — source-keyed backing resolve (file-local) + R-BACKING

- **Contract + variation.** Row 53 resolves the backing
  `models.Field` through the field's `source` (one-segment or
  equal to the declared name — a rename resolves its target
  column); no model, or a source naming no concrete column,
  yields `None` (caller routes the model-less path); dotted /
  star sources reject via row 52 (composed, not re-spelled).
  Varies on source semantics (C13 counts 1).
- **Sites + roles.** *Definition*: row 53 (one body). *Consumer*:
  row 64 (the dual-routing branch). The effective-source line
  (`field.source if field.source else field.field_name`) is a
  READ (the attribute to resolve, never `None`-from-equal) —
  explicitly NOT a FAM-SRC member (different contract: C21 moves
  the normalization pair, never this line). *Oracles*:
  renamed-scalar, renamed-relation, nonexistent-column-`None`
  rows + the dotted/star rows.
- **Challenges.** C13 counts 1.
- **Owner + lifetime.** This file. Pure resolve; nothing stored.
- **Migration.** None.
- **Distinct behavior (R-BACKING).** Considered: unifying with
  the forms name-keyed
  [forms-inputs][forms-inputs] `::_model_column_for`. Difference
  (fresh pair, no prior verdict): this resolves through the DRF
  `source` axis (renames resolve their target; dotted/star
  reject; `FieldDoesNotExist` → `None`); the forms twin resolves
  through the FORM FIELD NAME with reverse-relation / GFK /
  non-concrete guards + corrupted-internals typed arms the DRF
  path has no analog of (and the DRF path's rename + star
  semantics have no forms analog). Opposite populations, opposite
  guards. Trigger: a shared declared-name→column contract.
  Durable home: the row-53 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a rename
  resolves its declared name" (rename rows assert the target
  column) and "a dotted source resolves" (reject rows).
- **Structural gate.** The rename + `None` + reject oracle rows
  (name-keyed resolve fails the rename rows); no failability run
  owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [forms-inputs][forms-inputs] HEAD `55614839…` (work
  `436fcf42…`, twin body).

### F-PRIMARY — strict relation-primary policy (file-local)

- **Contract + variation.** Row 54 returns the related model's
  primary `DjangoType`, raising a class-creation
  `ConfigurationError` when none is registered (STRICTER than
  the form / model raw-pk fallback, [spec-039][spec-039]
  Decision 7: a serializer relation is meaningless without a
  typed decode target). Varies on the strictness (C14 counts 1).
- **Sites + roles.** *Definition*: row 54 (one body). *Consumers*:
  row 64's model-backed relation arm + row 55 (both as the
  `primary_of` adapter over the shared id-type spine — already
  one body). *Oracles*: missing-primary raise row + the
  Relay-vs-raw-pk id-type rows.
- **Challenges.** C14 counts 1.
- **Owner + lifetime.** This file. Registry read + raise; nothing
  stored.
- **Migration.** None.
- **Distinct behavior.** The form fallback (`registry.get`,
  may be `None`) is left byte-unchanged per the row-54 docstring
  (its own non-goal — axis-6 considered, no contract source
  unifies the postures). The id TYPE still rides the shared
  `relation_id_scalar` spine (a non-Relay primary legitimately
  uses raw pk — what is forbidden is a MISSING primary, not a
  non-Relay one).
- **Behavioral proof.** `static-reviewed`. Rejects "a missing
  primary degrades to raw pk" (raise row) and "a non-Relay
  primary raises" (raw-pk id rows).
- **Structural gate.** The missing-primary + id-type oracle rows
  (a fallback weakening fails the raise row); no failability run
  owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE; [registry][registry] HEAD
  `9cc8bb55…` (work `612bea87…`, `get` owner);
  [mutations-inputs][mutations-inputs] HEAD `fc442047…` (spine
  bodies).

### F-SERONLY-REL — serializer-only relation routing (file-local) + R-SERONLY

- **Contract + variation.** Row 55 maps a column-less relation
  to `(python_attr, annotation, related_model)`: related model
  from `field.queryset.model` (single) or
  `field.child_relation.queryset.model` (multi); id type via the
  shared `annotate_queryset_relation` spine after the row-54
  primary gate; naming via row 50; a relation with neither
  column nor concrete queryset raises naming the field. Varies
  on the discovery (C15 counts 1).
- **Sites + roles.** *Definition*: row 55 (the flavor adapter;
  the spine — resolve + primary-apply + package — is
  [mutations-inputs][mutations-inputs]
  `::annotate_queryset_relation`, C-counted 0 here). *Consumer*:
  row 64's column-less relation arm. *Oracles*: queryset-model
  resolve, Relay-`GlobalID`, no-column-no-queryset raise rows.
- **Challenges.** C15 counts 1 (spine untouched).
- **Owner + lifetime.** This file (flavor adapter). Pure routing;
  nothing stored.
- **Migration.** None.
- **Distinct behavior (R-SERONLY).** Considered: merging with
  the forms [forms-inputs][forms-inputs]
  `::_model_less_relation_annotation` beyond the shared spine.
  Difference (fresh pair, no prior verdict): queryset discovery
  differs (`child_relation` unwrap vs direct read), `primary_of`
  differs (row-54 raise vs `registry.get` fallback), naming
  differs (row-50 id-like dedupe vs 036 `<name>_id`), missing
  wording differs per subject — the SHARABLE spine is already
  one body (`annotate_queryset_relation`, whose docstring names
  both flavors as riders). What remains is four flavor adjectives
  with no shared rule between them. Trigger: the discovery /
  primary / naming adjectives converging. Durable home: the
  row-55 docstring analog clause + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "the spine
  is re-spelled here" (single `annotate_queryset_relation(`
  call with the four flavor args) and "an untyped relation
  emits" (raise row).
- **Structural gate.** The serializer-only relation oracle rows
  (a discovery weakening mis-types multi relations and fails
  them); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [forms-inputs][forms-inputs] HEAD `55614839…` (twin body);
  [mutations-inputs][mutations-inputs] HEAD `fc442047…` (work
  `fcbb964d…`, spine body).

### F-CONFLICT — type-override conflict policy (file-local)

- **Contract + variation.** Rows 56–58 resolve a model-backed
  serializer SCALAR: auto-generated fields ride the read-side
  `convert_scalar` (enum symmetry); consumer-DECLARED fields
  (row 56: bound `field_name in
  type(parent)._declared_fields`, unbound → not-declared) must
  AGREE with the column scalar or fail loud naming field +
  source + both scalars (row 57 names them); declared
  `ChoiceField`/`MultipleChoiceField` emits the generated
  serializer-only enum even over a plain column (declared
  choices are a schema-affecting override); choices columns
  skip the check (both sides intend the enum); non-scalar
  declared conversions defer to the model annotation. Varies as
  one policy (C16 counts 1).
- **Sites + roles.** *Definition*: rows 56–58 (one rule).
  *Mechanism consumers*: `convert_scalar` / `scalar_for_field`
  (C23 counts 0 here), row 45 (the declared-scalar reread),
  row 62 (the declared-choice arm). *Oracles*: disagree-raise,
  agree-ok, unbound-as-auto, non-scalar-defer, auto-not-checked,
  declared-choice-over-column, disagree-with-choices-column
  rows.
- **Challenges.** C16 counts 1.
- **Owner + lifetime.** This file (no twin: the model flavor
  has no declared contract; the forms column arm takes the
  column annotation without comparing — axis-6 considered, no
  [spec-038][spec-038] row requires a forms check, NOT a
  defect). Pure policy; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The `source` in the diagnostic tells a
  benign rename apart from a true mismatch (a str-vs-str rename
  agrees and passes — oracle-pinned).
- **Behavioral proof.** `static-reviewed`. Rejects "a disagreeing
  declared scalar silently takes the column" (raise rows) and
  "declared choices collapse to `String`" (declared-choice row).
- **Structural gate.** The conflict oracle rows (silently
  picking the column fails the disagree rows); no failability
  run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [types-converters][types-converters] HEAD `9ceb34af…`
  (scalar/enum bodies).

### F-CHOICE-ENUM — choice-enum upgrade + name-keyed cache (file-local) + R-CACHE

- **Contract + variation.** Rows 59–63 upgrade an enumerable
  serializer-only `ChoiceField`→ generated enum /
  `MultipleChoiceField`→`list[<enum>]` (row 59 excludes
  `FilePathField` — dynamic path choices, stays `str`; D4
  observes the hunt-owned `allow_blank` delta conditionally);
  row 61 builds via the shared `build_enum_from_choices` core
  and caches by descriptor-derived name (two inputs sharing one
  choice field share ONE enum object; a name reused with a
  DIFFERENT member set — row 60's map compare — fails loud);
  rows 36–38 own the cache + the `registry.clear()` reset (bus
  row `rest_framework.choice_enums`, verified
  [dry-clear][dry-clear] member 17 — lawful convergence, no new
  row). Varies as one rule (C17 counts 1).
- **Sites + roles.** *Definition*: rows 36–38, 59–63 (one rule;
  the row-61 NAME template line is FAM-ENUM's member). *Mechanism
  consumers*: the enum-build core (C-counted 0 here),
  `pascal_case` (FAM-ENUM), the clear bus (member 17).
  *Consumers*: row 63 (column-less arm), row 58 (declared-choice
  arm — the SAME enum whether or not a column backs the field).
  *Oracles*: enum/list-enum/filepath-stays-str/dedupe/collision
  rows.
- **Challenges.** C17 counts 1 (core + bus untouched).
- **Owner + lifetime.** This file. Stored derivation: the
  name-keyed cache — owner this module, validity the finalize
  pass, published at row 61, mutated only by row 61 / reset by
  row 37, invalidated by `registry.clear()` pre-bind (member 17).
- **Migration.** None (FAM-ENUM migrates the name line only).
- **Distinct behavior (R-CACHE).** Considered: routing the
  cache through `registry.register_enum` / `get_enum` (the
  read-side enum cache). Difference (fresh pair, no prior
  verdict): this cache is NAME-keyed (a serializer-only choice
  has no model, so the `(model, field_name)` registry key
  cannot address it) with member-COMPARE on reuse (a divergent
  reuse fails loud); the registry cache is `(model, field_name)`
  keyed with FIRST-WINS (siblings receive the cached enum
  unchanged). Different keys, different collision contracts —
  the registry API cannot express this cache. Trigger: a
  model-less enum key joining the registry API. Durable home:
  the row-36 comment + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "two inputs
  sharing a choice field mint two enums" (dedupe row) and "a
  divergent name reuse silently reuses" (collision row).
- **Structural gate.** The dedupe + collision oracle rows +
  the member-17 bus-membership gate (owned by the family item);
  no failability run owed.
- **Coupling.** None (FAM-ENUM owns the name line).
- **Freshness.** Target as in F-TABLE (row-59 dirt is
  hunt-owned: D4 exclusion);
  [types-converters][types-converters] HEAD `9ceb34af…` (core
  body); [registry][registry] HEAD `9cc8bb55…` (bus owner);
  [dry-clear][dry-clear] work `cf16088b…` (member-17 census,
  trigger only).

### F-RESOLVE — dual-routing seam + spec construction (file-local) + R-TRIPLE

- **Contract + variation.** Row 64 resolves one field to
  `(python_attr, base_annotation, InputFieldSpec)`: nested-first
  reject (never misrouted); model-backed arm (kind via the
  shared column classifier; relations re-gated + cardinality
  checked + kind overridden to MULTI for serializer-many over a
  collection-shaped non-M2M column, annotation via the shared
  column writer with the row-54 primary adapter; file via the
  shared writer; scalar via rows 56–58); column-less arm (kind
  via row 45; FILE→`Upload`; relations via row 55; scalars via
  row 63); naming ALWAYS from the declared name via row 50;
  the spec records `target_name` = declared name,
  `source` = the FAM-SRC normalized axis, `related_model` for
  relations (decode reads it off the bind-stashed map, never
  re-discovers per request). Returns the BASE annotation (the
  caller applies requiredness + `allow_null` widening). Varies
  on the routing (C18 counts 1).
- **Sites + roles.** *Definition*: row 64 (one body; the
  `source = …` line is FAM-SRC's member). *Mechanism consumers*:
  rows 41–42, 45, 50, 53–55, 58, 63 (all composed by name) +
  the shared classifier/writer/`Upload`/`InputFieldSpec` (0
  here). *Consumers*: the walk, injected-spec resolution,
  resolvers' recompute (verified J12 halves — no new row).
  *Oracles*: rename pair, cardinality quartet, file pair,
  relation/primary/enum/conflict rows (most converter oracles
  route through here).
- **Challenges.** C18 counts 1.
- **Owner + lifetime.** This file (the seam owner). Pure
  routing; nothing stored.
- **Migration.** None (FAM-SRC migrates the source line only).
- **Distinct behavior (R-TRIPLE).** Considered: merging with
  the forms [forms-inputs][forms-inputs]
  `::_field_triple_and_spec`. Difference (fresh pair, no prior
  verdict): this routes on the `source` axis (renames, dotted /
  star reject) with declared-name naming, the type-override
  conflict policy, the strict primary gate, and the cardinality
  override; the forms twin routes on the field NAME with the
  036 scheme, the shared requiredness decision, and no conflict
  / primary / cardinality rules. The SHARABLE parts (column
  classifier, column writer, queryset spine, `Upload`,
  `InputFieldSpec`) are already composed by name on both sides;
  what remains is the flavor routing, which shares no rule.
  Trigger: the source axis / conflict / primary rules
  converging across flavors. Durable home: the row-64 docstring
  analog clause + this artifact. D2 records the opaque `#6:`
  comment marker on the column-less scalar arm (sole `# #N`
  package-wide; the origin commit's bullets do not resolve it —
  expand or drop).
- **Behavioral proof.** `static-reviewed`. Rejects "a renamed
  field names from `source`" (rename rows), "a many-over-reverse
  emits single" (reverse-FK/GenericRelation rows), "the decode
  re-discovers the model" (`related_model is` assertion row).
- **Structural gate.** The rename + cardinality + file +
  `related_model` oracle rows (each fails its routing
  weakening); no failability run owed.
- **Coupling.** FAM-SRC (one line of row 64).
- **Freshness.** Target as in F-TABLE (row-64 lines CLEAN);
  [forms-inputs][forms-inputs] HEAD `55614839…` (twin body);
  [mutations-inputs][mutations-inputs] HEAD `fc442047…`
  (classifier/writer bodies); [rf-inputs][rf-inputs] `9b17d952…`
  (CLEAN, walk + injected call sites);
  [rf-resolvers][rf-resolvers] HEAD `8024703e…` (recompute call
  site, verified J12).

### F-SHAPE — conversion value object (file-local)

- **Contract + variation.** Row 25 subclasses the shared
  `FieldConversionBase` with `__slots__ = ()`: relation / file
  kinds carry `annotation=None` (finalized at row 64 where the
  id type / `Upload` is known — only the kind is authoritative);
  the `kind=SCALAR` default is what consumer-registered
  converters rely on. Varies only in the flavor binding (C19
  counts 0 here; C31 refused the forms merge).
- **Sites + roles.** *Definition*: the subclass binding here.
  *Shape owner*: [utils-inputs][utils-inputs]
  `::FieldConversionBase`. *Sibling (intentional separation)*:
  [forms-converter][forms-converter] `::FormFieldConversion`
  (R-REQUIRED). *Consumers*: every registry value + precheck in
  this file. *Oracles*: `annotation is None` assertions on the
  relation/file rows + the subclass-shape rows in
  [test-skeleton][test-skeleton].
- **Challenges.** C19 counts 0 here; C31 refused.
- **Owner + lifetime.** Shape owned upstream; this file owns
  only the subclass binding. Short-lived per-call instances;
  nothing stored.
- **Migration.** None.
- **Distinct behavior (R-REQUIRED).** Considered: routing
  requiredness through the forms `form_field_required` (the
  `required_of` variation the makers admit). Difference
  (CONVERGE with verified [dry-forms-conv][dry-forms-conv]
  R4/R5 on fresh evidence): `form_field_required` answers the
  NullBoolean question (exact-`NullBooleanField` + column-null
  arms) — a `forms.Field`-only concept no serializer field can
  present; the `required_of=None` default (plain
  `field.required`) IS this flavor's requiredness rule, and the
  row-27/31–34 wrappers rely on the default. Merging would
  couple the NullBoolean rule to a flavor that must never see
  it. Trigger: a serializer field gaining NullBoolean-like
  requiredness semantics. Durable home: the row-27 docstring
  contrast clause + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a relation
  carries a premature annotation" (`is None` rows) and "a
  consumer converter must import the kind" (default-kind
  register rows).
- **Structural gate.** The `annotation-is-None` + subclass
  oracles (a hand-rolled tuple return or premature annotation
  fails them); no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (work
  `47b2af21…`, shape body);
  [forms-converter][forms-converter] `b717fd0f…` (CLEAN,
  sibling body); [test-ratchet][test-ratchet] `7b198141…`
  (CLEAN, identity pins).

### F-KINDS — kind vocabulary + serializer-only pair (file-local)

- **Contract + variation.** Rows 17–20 re-export the four base
  kinds (`as`-form, so the resolver + tests keep addressing
  them on this module); rows 23–24 DEFINE the serializer-only
  `NESTED_SINGLE` / `NESTED_MULTI` pair (an explicitly-opted-in
  nested `Serializer` / `ListSerializer`). No variation on the
  base four (C20 counts 0 here); the nested pair varies here
  alone.
- **Sites + roles.** *Owner*: [utils-inputs][utils-inputs] for
  the base four (one conceptual enum — [utils-inputs][utils-inputs]' own
  comment names this module's nested pair as the serializer
  extension); this module for the nested pair. *Re-export here*;
  *consumers*: [rf-inputs][rf-inputs], [rf-resolvers][rf-resolvers],
  [test-converter][test-converter] (all import the kinds from
  `.serializer_converter` — verified import census). *Oracles*:
  kind-flag rows + the [test-ratchet][test-ratchet] identity pins.
- **Challenges.** C20 splits 0/1 as stated.
- **Owner + lifetime.** Upstream for the base; this file for the
  pair. Module constants; nothing stored.
- **Migration.** None.
- **Distinct behavior.** The nested pair is the documented
  extension point (utils prose + this module's comment agree) —
  not a per-flavor copy of the base vocabulary. The model
  flavor's `EXCLUDED` is likewise its own extension (zero
  `EXCLUDED` tokens here outside prose — verified J19 holds:
  unreachable by construction, no new row).
- **Behavioral proof.** `static-reviewed`. Rejects "a kind is
  re-spelled here" (identity pins) and "a nested kind routes
  without opt-in" (raise rows).
- **Structural gate.** The identity pins + kind-flag oracles;
  no failability run owed.
- **Coupling.** None.
- **Freshness.** Target as in F-TABLE;
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (kind block);
  [test-ratchet][test-ratchet] `7b198141…` (CLEAN).

### FAM-SRC — `serializer-source-axis-normalization` (ADOPTED on fresh evidence)

The plan row exists (`open`, candidate owner this file, both
files covered — no new row; Worker 0 transcription: none, the
row stands as the adoption record's home).

- **Contract + variation.** The `InputFieldSpec.source` axis
  normalization: a falsy `source`, or one equal to the declared
  name, records `None` (terse, form-symmetric reverse map);
  otherwise records the one-segment source. Varies only as the
  axis contract.
- **Sites + roles.** *Definitions (2)*, character-identical
  lines verified at HEAD bytes: row 64 (`source = field.source
  if (field.source and field.source != field_name) else None`,
  with `field_name = field.field_name`) and
  [rf-inputs][rf-inputs] `::_resolve_nested_field` (identical
  line, with `field_name` the effective-dict key). Same value
  under the supported contract: [rf-sets][rf-sets]
  `::_validate_schema_field_map` REJECTS a hook map whose key
  differs from the bound `field.field_name` (body re-verified
  fresh: the `name_mismatch` arm), the walk iterates that
  validated map, and nested recursion reads DRF `.fields`
  (keys == bound names by DRF construction) — so key ==
  `field_name` on every build path. *Consumers*: every
  `spec.source` reader (resolvers decode + agreement guards,
  `describe_serializer_input`, source-value oracles). *Prose*:
  the nested docstring claims sameness ("records the SAME
  normalized one-segment source") — the code asserts one rule,
  the bodies spell it twice. EXCLUDED on fresh evidence: the
  row-53 effective-source READ (different contract — the
  attribute to resolve, never `None`-from-equal; C21 never moves
  it), the resolvers:1910 runtime read (different contract —
  runtime field read with spec fallback for attestation), the
  fingerprint raw-`source` tuple (deliberately unnormalized
  input), and every `spec.source or target` COMPARE (consumers,
  not definitions). Census: `field.source if` spellings = 4
  package-wide (2 members + 2 excluded); `source != field_name`
  = exactly the 2 members.
- **Challenges.** C21 → **2** (a normalization change moves both
  lines; consumers follow). Re-verified, not inherited, from the
  [dry-inputs][dry-inputs] C10 count.
- **Owner + lifetime.** CONFIRMED candidate: this file (owns the
  source axis — row 52, row 53, and the axis construction for
  every other kind; the nested site already composes row 52 +
  rows 39–40 by name — only the normalization is inlined). No
  stored derivation (pure expression). The family item makes the
  final ownership decision.
- **Migration (sketch for the family item).** This module exposes
  the normalization next to row 52; the nested site calls it;
  both spec-construction sites read one expression. Oracles stay
  (they pin axis VALUES, never the spelling).
- **Distinct behavior.** The nested `require_one_segment_source`
  call above the line stays (dotted/star rejection precedes
  normalization on both paths — already shared, not in this
  family).
- **Behavioral proof.** `static-reviewed` for the COUNT (both
  lines read at HEAD bytes, character-identical; key==name
  enforcement re-verified in the validator body; exclusion
  contracts read). Consolidation proof owed by the family item.
- **Structural gate.** Owed by the family item (a two-site
  spelling gate with its negative control).
- **Coupling.** F-NESTED's consumer cluster (the nested site
  hosts one line); F-RESOLVE (row 64 hosts the other).
- **Freshness.** Target HEAD `32904418…` (both member lines
  CLEAN — untouched by hunt dirt); [rf-inputs][rf-inputs]
  `9b17d952…` (CLEAN, member line + walk-branch + fingerprint
  bodies); [rf-sets][rf-sets] HEAD `2c7117d6…` (validator body);
  [rf-resolvers][rf-resolvers] HEAD `8024703e…` (excluded
  runtime reads); [dry-inputs][dry-inputs] work `368150c9…`
  (trigger only).

### FAM-ENUM — `generated-choice-enum-name-template` (NEW FAMILY for Worker 0)

- **Contract + variation.** The GraphQL name of a generated
  choice enum from `(owning-type-name, field-name)`:
  `f"{type_name}{pascal_case(field_name)}Enum"`. Varies only as
  the template (suffix, infix, helper).
- **Sites + roles.** *Definitions (2)*, character-identical
  modulo the `field.` read, verified at HEAD bytes: row 61
  (`enum_name = f"{type_name}{pascal_case(field.field_name)}Enum"`,
  inputs `(generated-input-name, serializer-field-name)`) and
  [types-converters][types-converters]
  `::convert_choices_to_enum`
  (`enum_name = f"{type_name}{pascal_case(field_name)}Enum"`,
  inputs `(DjangoType-name, model-field-name)`). Same template
  over opaque strings; both compose the ONE `pascal_case`.
  Census: `}Enum"` code spellings = exactly these 2
  package-wide (+ 1 docstring restatement inside
  `convert_choices_to_enum`'s own docstring — projection, not a
  definition). *Consumers*: the enum-build core calls +
  name-keyed / registry caches (caching is R-CACHE, explicitly
  NOT in this family). Disambiguation pressure is nil by
  construction (input names vs type names keep the populations
  apart), so no per-flavor fork reason exists today; the only
  plausible template change (a global generated-enum naming
  policy) moves both.
- **Challenges.** C22 → **2** (a template change moves both
  lines; oracles pinning enum names follow as consumers).
- **Owner + lifetime.** Candidate:
  [types-converters][types-converters] (owns the enum-build core
  + already imports `pascal_case`; this module already imports
  the core from it — no dependency reversal). Pure expression;
  no stored derivation. The family item decides.
- **Migration (sketch for the family item).** A
  `generated_choice_enum_name(type_name, field_name)` helper at
  the owner; both sites call it. Oracles stay (they pin emitted
  NAMES, never the spelling).
- **Distinct behavior.** Caching stays split (R-CACHE):
  name-keyed + member-compare here vs `(model, field_name)` +
  first-wins there. The template is the shared rule; the caches
  are deliberately distinct rules.
- **Behavioral proof.** `static-reviewed` for the COUNT (both
  lines read at HEAD bytes; census greps; the template inputs
  verified opaque strings at both call sites). Consolidation
  proof owed by the family item.
- **Structural gate.** Owed by the family item (a two-site
  spelling gate with its negative control: a hand copy passing
  the enum-name oracles).
- **Coupling.** F-CHOICE-ENUM (row 61 hosts one line).
- **Freshness.** Target HEAD `32904418…` (member line CLEAN);
  [types-converters][types-converters] HEAD `9ceb34af…` (work
  `679c9448…`, member line); [utils-strings][utils-strings] HEAD
  `3ec3b262…` (helper owner).

### F-NOSURF — verified no-surface routings (converge, no new rows)

Checked on fresh grep + body evidence; the target neither defines
nor enforces these rules (all token censuses at HEAD bytes):

- `serializer-split-vs-colocated-converters` (CONVERGE, no new
  row): the split IS this file's architecture — public registry
  (rows 26/30/35) + dual routing (row 64) + source axis have no
  set-flavor analog; the verified inputs-side row stands.
- `serializer-no-build-normalizer` (CONVERGE, no new row): zero
  `normalize_input_value` here; decode is runtime in
  [rf-resolvers][rf-resolvers] (verified J12 halves) — the
  inputs-side row stands.
- `serializer-nested-name-vs-suffix-rule` (CONVERGE, no new row):
  recorded under F-NAME — the inputs-side row stands.
- `subsystem-clear-lifecycle` member 17 (CONVERGE, no new row):
  rows 36–38 are the censused member (`rest_framework.choice_enums`,
  full clear of the name-keyed dict) — the verified family census
  stands, re-derived fresh.
- `write-relation-id-typing` (consumer, no row): the id-type rule
  is composed via `model_column_write_annotation` /
  `annotate_queryset_relation` — `GlobalID` appears here only in
  two docstring prose mentions (id-type contrast clauses), zero code
  spellings.
- `canonical-input-provisional-name` (consumer, no row): row 64
  RECEIVES `type_name` as a parameter; the name restatement the
  verified FAM-NEW carves out lives in inputs + resolvers, never
  here.
- `mutation-input-reverse-map` (non-member, no row): this module
  stamps `InputFieldSpec`s, never remaps input attrs (the nested
  never-remap is inputs-side, verified R-reverse).
- `hostile-mapping-hardening` (non-member, no row): no
  trust-boundary MAPPING gate here (the row-51 guard reads DRF
  field ATTRS; `field.choices.items()` is framework-internal
  state, not a crossing) — family contract reread fresh.
- Per-message `describe_value` tail (non-member, no row): zero
  `describe_value` here; diagnostics render via the composed
  `_safe_*` pair (CONVERGE with the verified
  [dry-forms-conv][dry-forms-conv] non-membership direction on
  fresh evidence — no contract source routes a
  schema-construction diagnostic through `describe_value`).
- `field-value-coercion` (non-member, no row): fields map to
  annotations here; runtime values are never touched (the one
  `coerce` hit is the no-silent-coerce contract sentence).
- `set-type-naming` (non-member, no row): no set/input type names
  built here (zero `type_name_for`; enum names are FAM-ENUM, a
  different rule).
- `one-sync-boundary` / `sealed-execution-queryset` /
  `sync-boundary-recourse-wording` (non-members, no row): zero
  boundary/seed/recourse tokens (axis-2 reason).
- `serializer-operation-vocabulary` (non-member, no row): zero
  `CREATE` / `PARTIAL` / `operation_kind` here — the routed-to-the maintainer
  asymmetry lives entirely in [rf-inputs][rf-inputs] +
  [forms-inputs][forms-inputs].
- `converter-table-per-surface-ownership` trigger (folded into
  R-TABLES): the verified [dry-forms-conv][dry-forms-conv] F-reuse
  names a plan row this cycle's index does not carry; this
  artifact's R-TABLES row (CONVERGE on fresh evidence, homed at
  this file) is the current-cycle record — no second row.

## Defects

Two minor HEAD defects on CLEAN lines (normal homing owed at
closeout) plus two HEAD-vs-dirt observations on HUNT-OWNED lines
(observed-not-homed with closeout-conditional wording — each closes
itself if the concurrent hunt dirt lands, else it needs a home).
Nothing security-routed (no authorization / routing / exposure
impact).

- **D1 (minor).** `require_one_segment_source`'s docstring cites
  `(spec-039 Decision 7 / )` — a dangling second slot with no
  referent. The column half is Decision 7 (renamed-fields rule);
  the nested half lives in the spec's UNNUMBERED Improvements
  section ("Explicit opt-in nested serializer input support"),
  so the slot has no decision number to cite. Fix by naming the
  section or dropping the `/ `. Lines CLEAN at HEAD (hunt dirt
  touches neither the docstring nor the body). Owner:
  `django_strawberry_framework/rest_framework/serializer_converter.py`.
- **D2 (minor).** `resolve_serializer_field`'s column-less scalar
  arm carries a `#6:` comment marker opaque to every reader: the
  sole `# #N` spelling package-wide (census: 1 hit), and the
  origin commit (`951945b7`) lists seven test-scope bullets none
  of which names the enum-upgrade line it annotates. Fix by
  expanding the pointer or dropping the marker (the sentence it
  prefixes is accurate). Line CLEAN at HEAD. Owner: same file.
- **D3 (observed-not-homed, hunt-owned).** At HEAD bytes,
  `_list_child_conversion` emits `list[<child scalar>]` with no
  `allow_null` widening: a `None` element DRF accepts (child
  `allow_null=True`) is rejected at GraphQL coercion — the
  generated input under-admits the shape the runtime serializer
  validates (contrast the walk's outer-`allow_null` widening and
  the row-49 rationale). The concurrent hunt dirt on THESE EXACT
  LINES adds the `inner | None` widening + docstring paragraph.
  CLOSEOUT-CONDITIONAL: if that dirt lands, this observation
  closes with no home; if it is reverted or reshaped away, this
  needs a home (owner would be this file). No verdict on the
  dirt's shape is offered here — the hunt owns it.
- **D4 (observed-not-homed, hunt-owned).** At HEAD bytes,
  `_is_enumerable_serializer_choice` upgrades ANY `ChoiceField`
  (minus `FilePathField`) to a generated enum — including an
  `allow_blank=True` field whose DRF contract admits `""`, which
  no GraphQL enum member can represent, so a valid DRF input is
  unreachable through the generated shape. The concurrent hunt
  dirt on THESE EXACT LINES adds the `allow_blank` exclusion +
  docstring paragraph. CLOSEOUT-CONDITIONAL: if that dirt lands,
  this observation closes with no home; if it is reverted or
  reshaped away, this needs a home (owner would be this file).
  No verdict on the dirt's shape is offered here.

## Pending execution

None. Every proof is `static-reviewed` (body inspection at HEAD
bytes, package-wide `git grep` censuses, `ast.parse` enumeration,
oracle reads). Inspection suffices because the target decides no
ordering beyond finalize-time construction, no transactions, no
async behavior, and no ORM execution; the two count-2 rules are
character-identical spelling pairs whose consolidation proofs
belong to their family items. No failability run is owed by this
zero-edit file item. `FAKESHOP_SHARDED=1` and Postgres cells are
`inapplicable by construction`: the target's code path reaches no
database, alias, or dialect decision (pure dispatch over in-memory
field instances + in-memory dict reads + schema-time
introspection).

## Judgment

Backstop discharged: 65/65 `ast.Module.body` statements
enumerated (75 module names + 1 class member, every one homed),
34 challenges run with definition counts (C1–C34, every variation
axis of every rule), six matrix axes discharged against the real
surface (read-side table + forms twin + mutations spine read whole
at HEAD bytes; set twins via verified artifacts + HEAD greps;
sync/async absence and fourteen no-new-row convergences verified
by grep and body reads, not assumed), nineteen file-local records with proving
challenges, ten fresh rejections with difference + trigger + home
(4 converging with prior verdicts on fresh evidence), one family
ADOPTED with narrowed exclusions (FAM-SRC), one new family named
(FAM-ENUM), two minor HEAD defects on clean lines + two
observed-not-homed hunt-conditional notes, zero pending. The target
owns its per-field mapping singly: one table, one registry, one
dispatch order, one fail-loud boundary, one nested default, one
relation gate, one naming rule, one source guard, one conflict
policy, one enum cache, one seam — and exactly two lines that
restate a rule owned jointly with one other site each.

## Index rows for Worker 0

Family, owner, files covered, holding item, status — Worker 0 alone
edits the plan; these rows are proposed transcriptions. FAM-SRC
needs NO transcription (its row exists with both files covered and
`open` status — this artifact is the adoption record). Also for
Worker 0: add `## Families` item `Family
generated-choice-enum-name-template` (no artifact on disk;
undispatched). No `## Owned changes` rows (file item; zero
production edits).

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `generated-choice-enum-name-template` | `django_strawberry_framework/types/converters.py` (candidate; owns the enum-build core) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/types/converters.py` | Family `generated-choice-enum-name-template` | open |
| `serializer-scalar-registry` | `django_strawberry_framework/rest_framework/serializer_converter.py::_BUILTIN_SCALAR_CONVERTERS` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-converter-registration` | `django_strawberry_framework/rest_framework/serializer_converter.py::register_serializer_field_converter` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-dispatch-order` | `django_strawberry_framework/rest_framework/serializer_converter.py::convert_serializer_field` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-fail-loud-fallthrough` | `django_strawberry_framework/rest_framework/serializer_converter.py::_unsupported_serializer_field` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-nested-detection` | `django_strawberry_framework/rest_framework/serializer_converter.py::_reject_nested_serializer` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-relation-gate` | `django_strawberry_framework/rest_framework/serializer_converter.py::_reject_unsupported_relation_field` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-list-child` | `django_strawberry_framework/rest_framework/serializer_converter.py::_list_child_conversion` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-extension-boundary` | `django_strawberry_framework/rest_framework/serializer_converter.py::_finish_serializer_conversion` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-id-like-suffix-naming` | `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_graphql_name` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-description-synthesis` | `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_description` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-one-segment-source-guard` | `django_strawberry_framework/rest_framework/serializer_converter.py::require_one_segment_source` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-backing-column-resolve` | `django_strawberry_framework/rest_framework/serializer_converter.py::backing_model_field` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-required-primary` | `django_strawberry_framework/rest_framework/serializer_converter.py::_require_relation_primary` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-only-relation-annotation` | `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_only_relation_annotation` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-type-override-conflict` | `django_strawberry_framework/rest_framework/serializer_converter.py::_model_backed_scalar_annotation` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-choice-enum-upgrade` | `django_strawberry_framework/rest_framework/serializer_converter.py::_serializer_choice_enum` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-field-resolve` | `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-conversion-shape` | `django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConversion` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-kind-vocabulary` | `django_strawberry_framework/rest_framework/serializer_converter.py::NESTED_SINGLE` | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | file-local |
| `serializer-table-vs-surface-tables` | `django_strawberry_framework/rest_framework/serializer_converter.py::_BUILTIN_SCALAR_CONVERTERS` (rejection recorded here; CONVERGE with verified forms-converter F-reuse on fresh evidence) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/forms/converter.py`, `django_strawberry_framework/scalars.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-extension-hook-vs-scalar-map` | `django_strawberry_framework/rest_framework/serializer_converter.py::register_serializer_field_converter` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/types/converters.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-fallthrough-vs-form-fallthrough` | `django_strawberry_framework/rest_framework/serializer_converter.py::_unsupported_serializer_field` (rejection recorded here; CONVERGE with the standing per-subject-rejection-grammars direction on fresh evidence) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/forms/converter.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-except-guard-vs-shared` | `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_field_description` (rejection recorded here; CONVERGE with the standing shared-except-guard direction on fresh evidence) | `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-resolve-vs-form-triple` | `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-only-relation-vs-model-less` | `django_strawberry_framework/rest_framework/serializer_converter.py::serializer_only_relation_annotation` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-cardinality-vs-shared-classifiers` | `django_strawberry_framework/rest_framework/serializer_converter.py::_model_relation_cardinality` (rejection recorded here; fresh, two refused derivations, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/mutations/inputs.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-enum-cache-vs-registry-cache` | `django_strawberry_framework/rest_framework/serializer_converter.py::_SERIALIZER_CHOICE_ENUMS` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/registry.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-requiredness-vs-form-requiredness` | `django_strawberry_framework/rest_framework/serializer_converter.py::SerializerFieldConversion` (rejection recorded here; CONVERGE with verified forms-converter R4/R5 on fresh evidence) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/forms/converter.py` | File `rest_framework/serializer_converter.py` | rejected |
| `serializer-backing-vs-form-column` | `django_strawberry_framework/rest_framework/serializer_converter.py::backing_model_field` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/serializer_converter.py` | rejected |

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff
34bb4b17e04ceebaf0cbd02276aa06c18645a65f --
django_strawberry_framework/rest_framework/serializer_converter.py`
is EMPTY (the 6 hunt hunks vs HEAD predate the item baseline, so
the window diff shows nothing — no hunk authored here, no
attribution owed); the artifact itself is this new untracked file.
The `## Owned changes` ledger paths were never
touched. Concurrent dirt (200+ paths, incl. 47 under
`django_strawberry_framework/`) was never edited, reverted, or
tidied. No `ruff` run owed (no `.py` created or edited; the one new
file is markdown). No `docs/dry/temp-tests/` scratch created (HEAD
snapshots lived under `/tmp/sc*`, outside the repo). HEAD is
`5ee86193` at finish, unmoved since dispatch. Do not commit.

## Independent verification (Worker 2)

Recorded BEFORE opening `## Findings` (expectation-first; the
Verification sections above were read, Findings/Defects/Judgment
were not). All body claims below are re-derived at HEAD bytes by
Worker 2 in `/tmp/sc-w2/` snapshots; HEAD is `5ee86193`,
unmoved (verified `git rev-parse HEAD` this session).

### W2 trace (own)

Target: `django_strawberry_framework/rest_framework/serializer_converter.py`,
1060 lines at HEAD. Blob fingerprints (Worker 2, fresh):
HEAD `32904418a169941c2afa1c9cd6866c55debc64f3`, worktree
`95568390a70e6a40acad9639c24dfe2bde263ffa`. Worktree-vs-HEAD
is 6 hunks, all in `_reject_nested_serializer`,
`_reject_unsupported_relation_field` (2 sites),
`_list_child_conversion`, `_is_enumerable_serializer_choice`:
`type(x).__name__` to `_safe_type_name(x)` label swaps plus two
behavior hunks (child-`allow_null` widening, `allow_blank` enum
exclusion). None is ledgered; all left untouched. Window diff
vs `34bb4b17e04ceebaf0cbd02276aa06c18645a65f` names exactly 3
paths: the plan (Worker-0 dispatch block, 1 hunk),
`django_strawberry_framework/schema.py` (1 hunk: async
cancellation-handoff around the atomic enter),
`tests/test_schema.py` (2 hunks: sqlite/threading imports +
handoff commit-probe tests). Zero `serializ|rest_framework|
converter` tokens in the two code diffs; target dir diff vs
baseline is empty. Attribution: all-concurrent, no scope
violation.

Enumeration (Worker 2, own `ast.parse` over the HEAD
snapshot): **65** `ast.Module.body` statements (1 docstring +
22 imports + 41 bindings + 1 `register_subsystem_clear` call;
30 FunctionDef + 1 ClassDef + 18 ImportFrom + 4 Import + 5
Assign + 5 AnnAssign + 2 Expr), binding **75** module names +
1 class member (`__slots__`). Row-by-row check against
`### Enumeration` follows in Reconciliation; the headline
counts agree.

Sites + roles (Worker 2): the module DEFINES the
`serializers.Field`-keyed scalar table (16 rows), the live
registry + validated extension, the precheck order + entry,
the raising fallthrough factory, nested detection + opt-in
default, the PK-relation gate + cardinality trio, list-child
recursion, the scalar-extension boundary, the id-like-suffix
naming rule, description synthesis, the one-segment source
guard, source-keyed backing resolve, the strict primary
policy, serializer-only relation routing, the declared-vs-
column conflict policy, the choice-enum upgrade + name-keyed
cache, the dual-routing seam + spec construction, the
`NESTED_*` kind pair. It CONSUMES by name: the dispatch
skeleton + makers + finish (`utils/converters.py`), the value
shape + spec record + base-four kinds (`utils/inputs.py`),
read scalars + enum-build core (`types/converters.py`), the
column classifier + write annotation + queryset spine
(`mutations/inputs.py`), camel/pascal (`utils/strings.py`),
`Upload`, the clear bus (member row
`rest_framework.choice_enums`), `registry.get` (primary
lookup), `_safe_*` renderers. Layering verified one-way at
HEAD bodies: `rest_framework/inputs.py` imports 7 names,
`rest_framework/resolvers.py` 7, `rest_framework/sets.py` 2,
zero back-imports, sibling mentions prose-only. Oracles pin
literals (76 `def test` in
`tests/rest_framework/test_converter.py` at HEAD bytes; the
registry fixture snapshot/restores for hygiene only; 19
`SHARED_BINDINGS` identity pins; live serializer rows incl.
`test_create_shelf_via_serializer_happy_path` at HEAD).

Definition counts per posited change (Worker 2, HEAD bodies):
new-DRF-scalar row 1; row-scalar change 1; registration
tightening 1 (`SCALAR_MAP` bare assignment untouched);
precheck reorder/routing 1; fallthrough respell 1; nested
shape 1 (detectors move as one rule); relation-kind support
1; list-child rule 1; smuggled-shape forbid 1; suffix-dedupe
change 1; description axis 1; one-segment widening 1 (two
enforcement consumers follow); source-semantics change 1;
primary-fallback allow 1; queryset-discovery change 1
(spine untouched); override-rule change 1; enum
eligibility/cache/dedupe 1 (build core untouched);
model-backed/column-less split 1; value-shape change 0 here
(owner `utils/inputs.py::FieldConversionBase`); kind respell
0 here for the base four, 1 here for the nested pair. Two
count-2 pairs: (a) the `source`-axis None-normalization line,
character-identical here
(`resolve_serializer_field`, HEAD line 977) and in
`rest_framework/inputs.py::_resolve_nested_field` (HEAD line
1511) — same bound value under the supported contract (top-
level key==name enforced by
`rest_framework/sets.py::_validate_schema_field_map` lines
194-206, re-read; nested keys are DRF `.fields` keys by
construction; call site passes the effective-dict key);
(b) the `<Type><Field>Enum` name template, character-
identical modulo the field-name read here
(`_serializer_choice_enum`, HEAD line 885) and in
`types/converters.py::convert_choices_to_enum` (HEAD line
775) — package-wide `git grep` census finds exactly these 2
code sites (filters `_pascal_case` builds `RangeInputType`
names, a different grammar). Owner calls (Worker 2): (a)
this file (owns `require_one_segment_source`,
`backing_model_field`, every other axis construction; the
nested site already composes the guard by name); (b)
`types/converters.py` (the read-side majority site; the
template is name-grammar shared by both enum builders).
Merge refusals (Worker 2, fresh bodies): four key spaces
(26/1/12/16: `SCALAR_MAP` 26 `models.` rows re-counted,
`scalars.py::_PACKAGE_SCALAR_MAP` 1 row, forms 12 rows,
target 16 rows — pairwise disjoint roots, disjoint value
contracts); triple merge refused (source axis + conflict +
strict primary + cardinality have no forms analog; shared
shape already `InputFieldSpec` + spine calls);
cardinality-from-column refused (`model_column_write_kind`
answers single for a reverse FK — re-read — while the
guard pair answers serializer-vs-model agreement; the
taxonomy answers a 5-kind topology, not the 2-valued
agreement); enum-cache merge refused (name-keyed +
member-compare vs `(model, field)` + first-wins identity);
fallthrough merge refused (per-subject nouns + the
name-read `try/except` arm exists target-only);
hostile-attr-guard merge refused (per-site catch sets +
diagnostics); requiredness merge refused (NullBoolean is
forms-only; the `required_of=None` default IS the
serializer rule — re-read in the maker body);
extension-hook merge refused (validated register +
override guard vs last-write-wins assignment); backing
merge refused (source-keyed + dotted/star reject vs
name-keyed + reverse/GFK guards + corrupted arms);
colocation refused (registry + dual routing + source axis
are the spec-039 split). Convergences I would take with
no new row: skeleton/makers/finish, value shape, kind
vocabulary, read scalars + enum core, id spine +
classifier, camel/pascal, `Upload`, clear-bus m17 (member
17 `rest_framework.choice_enums` confirmed in the family
artifact + 17 call sites censused), no-build-normalizer,
converter/shaper split, nested-name-vs-suffix (nested
keeps the plain name — re-read), encode/decode kind
grammar + J12 agreement round-trip (recompute via
`resolve_serializer_field` re-read at resolvers HEAD
line 1210).

Matrix (Worker 2): axis 1 searched (26/1/12/16 census;
zero `LOOKUP`/`Ordering`/`FilterSet`/`OrderSet`/
`normalize_input_value`/`make_dynamic_set_getter` tokens
re-grepped); axis 2 inapplicable with reason (zero
`async def`/`await`/`sync_to_async`/
`run_in_one_sync_boundary` re-grepped; schema-time
introspection only); axis 3 searched (two genuine second
spellings above; the `source or name` effective-source
reads — `backing_model_field` HEAD line 706, resolvers
attest/agreement reads, fingerprint tuple, collision
`source or name` arms — answer "which attribute",
never None-from-equal, over already-normalized or
differently-starred domains: excluded); axis 4 searched
(one kind grammar + one spec record, two halves
correctly separated; zero `EXCLUDED` outside the one
prose sentence re-grepped; `InputFieldSpec(` constructed
once re-grepped); axis 5 searched (spec-039 Decision 4
+ 7 + nested section re-read; oracles spell literals;
no expectation derives from an owner table); axis 6
enumerated (Duration/bare-Field/cardinality/description/
`is_input` asymmetries each lack a contract source on
the missing side — zero `help_text` in `forms/`,
zero cardinality/mismatch in spec-038, zero `is_input`
in the forms converter, spec-039 parity row names the
serializer upstream only — all re-grepped; no omission
defect).

Defect pre-registrations (Worker 2, before Findings):
W2-P1 — `require_one_segment_source` docstring cites
`(spec-039 Decision 7 / )` with a dangling `/ )` slot
(HEAD lines 665-666; sibling cites well-formed; spec-039
Decision 7 exists; clean lines, no hunt hunk touches
them). W2-P2 — `# #6:` opaque marker at HEAD line 1046:
sole `# #<n>` in the package at HEAD (census 1) and
untouched by hunt hunks; origin commit `951945b7`
(`-S '#6:'`). W2-P3 — at HEAD,
`_list_child_conversion` emits `list[child]` with no
child-`allow_null` widening while DRF accepts `None`
elements under child `allow_null=True` (installed DRF
3.18.0 `validate_empty_values` re-read); the hunt hunk
sits on those exact lines (HEAD 387-391). W2-P4 — at
HEAD, `_is_enumerable_serializer_choice` upgrades an
`allow_blank=True` `ChoiceField` to an enum built from
`.choices` only, while DRF accepts `''` outside
`.choices` (installed DRF `ChoiceField.to_internal_value`
early-`''` return re-read); the hunt hunk sits on those
exact lines (HEAD 861-864). W2-P3/P4 disposition:
observed-not-homed with closeout-conditional wording
(hunt-owned lines; each closes if the dirt lands) — no
verdict on the dirt's shape.

Record-accuracy note (Worker 2, pre-Findings): the dirt
note's `[test-converter]` pair is transposed — HEAD is
`9d5d0eaf` (`git rev-parse HEAD:`), worktree is
`b12dde99` (`git hash-object`), not work-then-HEAD as
printed. Every other fingerprint in the dirt note
re-verified exact (11/12). Whether the transposition
recurs in Findings Freshness rows is checked in
Reconciliation.

### Reconciliation (Worker 2, after Findings)

Enumeration: checked MEMBER BY MEMBER against my own
`ast.parse` dump (65 statements, 75 + 1 names) — every row
0–64 names the right statement and binds the right count
(import rows 1–10/11/12/13/14/15/16/17–20/21/22 =
10/3/3/2/1/3/4/4/2/2 re-added to 34; non-import names to
41; total 75 + `__slots__`). All homed; dual-homed rows
are one unit. AGREE 65/65.

Matrix: all six axes discharged against the real surface.
Every census number re-grepped fresh at HEAD bytes and
exact: 26/1/12/16 key spaces (the `1` is
`scalars.py::_PACKAGE_SCALAR_MAP`, re-read); zero-token
claims for all 15 axis-1/2/4/6 instruments; `EXCLUDED` 1
(prose), `InputFieldSpec(` 1, `GlobalID` 2 (prose),
`describe_value`/`seed_*`/`boundary_*` 0; 76 `def test`;
19 `SHARED_BINDINGS`; key==name validator arms; J12
recompute call; live happy-path row. Axis-2/5/6
inapplicability reasons judged sound (schema-time
construction only; oracles spell literals; each
asymmetry lacks a contract source on the missing side —
`help_text` 0 in `forms/`, cardinality 0 in spec-038,
`is_input` 0 in the forms converter, spec-039 parity
row serializer-only).

Challenges C1–C34: every count agrees with my
independent counts (C19/C20/C23/C24 the 0-here proofs;
C21/C22 the two count-2 pairs; C25–C34 the ten
merge refusals). Verdicts agree throughout.

Findings: all 19 file-local records accepted (each
challenge re-derived; roles correct — no oracle
rewritten, zero production edits); all 10 rejections
accepted with difference + trigger + home verified
(R-TABLES, R-FALLTHROUGH, R-EXCEPT, R-REQUIRED
converging on fresh evidence — the forms-conv
F-reuse/R3/R4/R5, `_request_body` J1 +
four-optimizer chain, utils-policies R3 + hints chain
all re-located; R-EXT-HOOK, R-CARD (both refused
derivations — the reverse-FK single-vs-many proof
re-read in `model_column_write_kind`), R-BACKING,
R-SERONLY, R-CACHE, R-TRIPLE fresh). All 14 F-NOSURF
bullets accepted (each re-grepped or re-read; the
folded table-trigger claim verified — the plan index
carries no such row). FAM-SRC adoption ENDORSED:
character-identical pair re-read at both HEAD lines,
key==name enforcement re-verified in the validator
body + DRF-construction path, candidate owner
confirmed as this file, narrowed exclusions sound
(`field.source if` = exactly 4 package-wide with the
two excluded sites' contracts read; `source !=
field_name` = exactly the 2 members; fingerprint raw
read + resolvers:1910 runtime read + compares all
different-question). FAM-ENUM new family ENDORSED:
count 2 tested hard (package-wide `}Enum"` census =
exactly the 2 code sites + 1 own-docstring
projection; filters range-name grammar excluded on
fresh evidence); neither side consumes the other at
HEAD; candidate owner `types/converters.py`
dependency-clean (this module already imports the
enum core from it). Index rows: 30 = 1 + 19 + 10,
all well-formed (`path::Symbol` cites throughout;
no banned provenance words re-grepped).

Defects: D1 merges with W2-P1 (dangling slot +
unnumbered Improvements section both re-verified —
section head at spec line 3764 under line 3472);
D2 merges with W2-P2 (sole `# #N` re-censused;
origin commit + its seven test-scope bullets
re-read); D3 merges with W2-P3, D4 with W2-P4 (HEAD
behavior claims re-derived against installed DRF
3.18.0 bodies; hunt hunks sit on the exact HEAD
lines 387–391 / 861–864; closeout-conditional
observed-not-homed is the right disposition — no
verdict offered on the dirt's shape). No new Worker 2
defects: the `036` backtick spelling is the spec's
own convention (spec-039 Decision 2 title), not a
defect. Pending execution: none, correctly —
`static-reviewed` suffices (no ordering/txn/async/ORM
decisions); sharded/PG inapplicability-by-construction
judged sound. Ruff: item-touched paths clean
(target `All checks passed` + formatted; artifact is
markdown, layout-exempt); tree-wide errors all in
`hunt-ws/` scratch + the two concurrent window paths —
confirmed out of scope, never fixed here.

Revision feedback (record-accuracy ONLY — every
finding verdict above is accepted; no re-trace owed):

- W2-C1 (dirt note, line 125): the `[test-converter]`
  pair is transposed. `git rev-parse
  HEAD:tests/rest_framework/test_converter.py` =
  `9d5d0eaf`; `git hash-object` (worktree) =
  `b12dde99`. The printed work-first order has them
  backwards. The F-TABLE/F-DISPATCH Freshness rows
  (lines 489–490, 583) are already correct —
  single-spot fix in the dirt note only.
- W2-C2 (F-REL-GATE Freshness, line 737):
  `[spec-038] work e6844a37…` matches no object
  (`git cat-file -t` fails); the file is CLEAN with
  HEAD == worktree == `fb1ba405`. Substance
  re-verified true (0 cardinality/mismatch hits at
  HEAD bytes) — fingerprint fix only.

### Verdict (Worker 2)

`revision-needed`, record-accuracy only (W2-C1–C2
above, each pinned execution-verified). All finding
verdicts accepted: 65/65 homed, C1–C34 counts agree,
19 file-local, 10 rejections, 14 convergences,
FAM-SRC adoption + FAM-ENUM new family endorsed,
D1–D4 merged with W2-P1–P4, window attribution
confirmed all-concurrent. W1 revision pass: apply
the two fingerprint corrections, nothing else;
resubmission returns to this trace (same Worker 2
per the revision rule where context persists).

## Iterations (Worker 1, revision pass 2)

Run `0.0.15 2026-09-28-7`. HEAD `0c0537e2` at dispatch and at
finish, unmoved (verified `git rev-parse HEAD` this session).
`ITEM_BASELINE=e270e666bcf86ecbe5bea944ce1f371b5ad22192`
resolves. Record: pre-edit artifact 119094 B, sha256
`d022113e1aadb908efaf707e8830ec2f0afb976dd970714c3d3a7afe0a249df4`
(1997 lines; verified zero `## Iterations` headers before
writing — the dead run-6 revision pass left no partial edits).
This block was inserted immediately before the
`<!-- LINK DEFINITIONS -->` block (pre-edit line 1951); the only
other change is the `Status:` line (`revision-needed` ->
`ready-for-verification/2`). No prior section rewritten. No
tracked file touched: this item's edit set is this untracked
artifact only — the target, oracle, and spec paths below were
read, never written, so the ledger / cycle-baseline STOP check
passes vacuously (neither holds a row for them, and no hunk was
authored on any tracked path). No workspace run was needed: every
probe below is read-only in the shared tree (`git rev-parse`,
`git hash-object`, `git show`, `git diff`, `git cat-file -t`,
`ast.parse` over blob snapshots in /tmp, removed after use) — no
source mutated, no pytest, no ruff owed (zero `.py` paths
touched). All run-6 finding verdicts accepted, as scoped; no
re-trace performed.

### I-C1 — W2-C1: `[test-converter]` transposed pair (dirt note, line 125)

The dirt note's convention is work-first (`work ... / HEAD ...`,
lines 116-117), so line 125's `` `9d5d0eaf...` / `b12dde99...` ``
asserts work=`9d5d0eaf`, HEAD=`b12dde99`. Transposition
confirmed: `git rev-parse
5ee86193:tests/rest_framework/test_converter.py` =
`9d5d0eaf7087bf46bda189e9f117fff343bf0f5f` — HEAD was
`9d5d0eaf` at run-6 bytes, exactly as W2 pinned. Corrected
record at CURRENT bytes, each side by its own method (tracked
HEAD via `git rev-parse HEAD:<path>`, worktree via
`git hash-object <path>`, never one against the other): HEAD
`4d5055405857c5117114c299a83ba62b8e1c709a`, worktree
`bb585a38519330e2de546250cfe9aecfa52c2b0a` — in the note's
work-first order, `` `bb585a38...` / `4d505540...` ``. The
F-TABLE (lines 489-490) and F-DISPATCH (line 583) rows were
already HEAD-first and correct at run-6 bytes; at current bytes
they re-pin to HEAD `4d505540...` (work `bb585a38...`).
Disclosure, not a re-trace: the oracle's HEAD drifted 28+/45-
(`5ee86193..0c0537e2`) and its worktree is dirty; verdicts stand
on the run-6 trace and this correction is record-accuracy only,
as W2 scoped it.

### I-C2 — W2-C2: F-REL-GATE `[spec-038]` phantom hash (line 737)

Line 737's `[spec-038] work `e6844a37...`` matches no object at
current bytes either (`git cat-file -t e6844a37` fails: not a
valid object name). The file
`docs/SPECS/spec-038-form_mutations-0_0_12.md` is CLEAN:
`git rev-parse HEAD:<path>` and `git hash-object <path>` both
equal `fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`, and
`git diff 5ee86193..HEAD -- <path>` is empty — byte-identical
since run 6, so W2's substance re-verification (0
cardinality/mismatch hits) still describes these bytes.
Corrected record: `[spec-038] CLEAN `fb1ba405...`` (full
`fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`).

### I-C3 — target fingerprint re-pin (`32904418` -> `6652d092`)

Current pins, each side by its own method: HEAD
`6652d092544ebfc618ab1805d23e8c055c39c5d7` (`git rev-parse
HEAD:django_strawberry_framework/rest_framework/serializer_converter.py`),
worktree `96d2b56a043e7f17000a654d1b6320bec39fdac3`
(`git hash-object` on the path). Every W1 pin site re-pins to
this pair: header lines 17-18, dirt note lines 112-113, F-TABLE
line 484 (every `Target as in F-TABLE` row inherits it), FAM-SRC
line 1368, FAM-ENUM line 1424. W2's trace pins (lines
1646-1647) stand as W2's run-6 record. The worktree dirt evolved
since run-6 (+24/-14 over 6 hunks then; 82+/78- over 17 hunks
now, `truth.` vocabulary 30 hits vs 0 at HEAD bytes) —
hunt-attributed by content, absent from the ledger and the cycle
baseline, left untouched.

### I-C4 — drift confirmation: no finding moves (re-read, not assumed)

The drift, re-read this session (`git diff
5ee86193..0c0537e2` on the target — one hunk, `@@ -1,4 +1,4 @@`):
old line 1 ends `reverse map (spec-039).`, new line 1 ends
`reverse map.` — the `(spec-039)` title suffix is dropped and
nothing else. Both blobs are 1060 lines (1-for-1 swap, zero line
shift, so every `:NNN` pin in this artifact still addresses the
same bytes at current HEAD). `ast.parse` over both blobs: 65/65
top-level statements (agreeing with the Enumeration's 65 and
W2's recount); module-docstring-normalized `ast.dump` identical;
31/31 def/class. No code moved. Category walk: findings (19
file-local + FAM-SRC + FAM-ENUM + 10 rejections + 14
convergences) — none cites line 1 or its suffix; the three
module-docstring claims cite other spans (enumeration row 0,
docstring-as-prose, still prose; F-TABLE projections, the
MRO-claims paragraphs at target lines 19-41; R-EXT-HOOK, the
`Mirrors` clause at target lines 37-38 — all outside the hunk).
Challenge counts C1-C34 count code definitions and behaviors; a
prose-title edit moves none (the two count-2 member lines, 977
and 885, sit outside the hunk, unshifted). Family assignments
and the 30 index rows cite `path::Symbol` — symbols untouched.
Defects D1-D4 cite lines 665-666, 1046, 387-391, 861-864 — all
outside the hunk, byte-identical, unshifted. Nothing moves; no
silent adjustment was made.

Resubmission returns to a FRESH Worker-2 (the run-6 W2 context
is gone) per the run-7 re-dispatch.

## Independent verification (Worker-2) re-pass (run 7)

Re-pass scope only: the run-6 Worker-2 trace above stands as the
prior-verdict record (65/65 homing, C1–C34 counts, verdict
endorsements — all accepted, no re-trace). This section re-derives
the two corrected record values plus the target re-pin at current
bytes, each side by its own method, then verifies the
`## Iterations` claims and the append-only record. Run
`0.0.15 2026-09-28-7`; HEAD `0c0537e2` at first probe and at
finish, unmoved (`git rev-parse HEAD`);
`ITEM_BASELINE=e270e666bcf86ecbe5bea944ce1f371b5ad22192`
resolves. Address
`dry/dry-file-rest_framework__serializer_converter/verify-2`; no
workspace run was needed (every probe read-only in the shared
tree), so no run id is cited.

### W2 re-pass trace (own, before re-reading `## Findings`)

- Target `django_strawberry_framework/rest_framework/serializer_converter.py`:
  HEAD `6652d092544ebfc618ab1805d23e8c055c39c5d7`
  (`git rev-parse HEAD:<path>`), worktree
  `96d2b56a043e7f17000a654d1b6320bec39fdac3`
  (`git hash-object <path>`); run-6 HEAD
  `32904418a169941c2afa1c9cd6866c55debc64f3`
  (`git rev-parse 5ee86193:<path>`).
- Oracle `tests/rest_framework/test_converter.py`: HEAD
  `4d5055405857c5117114c299a83ba62b8e1c709a`, worktree
  `bb585a38519330e2de546250cfe9aecfa52c2b0a`, run-6 HEAD
  `9d5d0eaf7087bf46bda189e9f117fff343bf0f5f` (same three
  methods); HEAD drift `5ee86193..0c0537e2` is 28+/45- and
  the worktree is dirty (79+/60-).
- `e6844a37`: no object (`git cat-file -t` fails, exit 128).
  `docs/SPECS/spec-038-form_mutations-0_0_12.md`: HEAD and
  worktree both `fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`
  (each by its own method); `git diff 5ee86193..HEAD` empty;
  `git status` clean.
- Target drift `5ee86193..0c0537e2`: one hunk (`@@ -1,4 +1,4 @@`),
  line 1 drops the `(spec-039)` title suffix, nothing else;
  1060/1060 lines; `ast.parse` 65/65 top-level, 31/31
  def/class, module-docstring-normalized `ast.dump` identical.
- Target worktree dirt vs HEAD: 82+/78- over 17 hunks,
  `truth.` 30 hits vs 0 at HEAD bytes — hunt-attributed by
  content (including the two behavior-adjacent hunks on the
  lines D3/D4 observe), absent from the ledger and the cycle
  baseline, left untouched.

### Re-pass verdicts

- I-C1 (W2-C1 `[test-converter]` pair): AGREE. The dirt note's
  work-first convention (lines 116-117) with line 125's
  `` `9d5d0eaf…` / `b12dde99…` `` asserts work=`9d5d0eaf`;
  run-6 HEAD was `9d5d0eaf` — transposition confirmed on W2's
  pins. Corrected work-first record `` `bb585a38…` /
  `4d505540…` `` matches my independent pair. F-TABLE
  (lines 489-490) and F-DISPATCH (line 583) are HEAD-first
  and were correct at run-6 bytes; both re-pin to HEAD
  `4d505540…` (work `bb585a38…`). Census: no other
  `[test-converter]` pin site exists.
- I-C2 (W2-C2 `[spec-038]` hash): AGREE. `e6844a37` is no
  object at current bytes either; the spec file is CLEAN at
  `fb1ba405…` (full
  `fb1ba405cb1af5e6194ab79cc5b49b7210ee68d5`),
  byte-identical since run 6 — W2's 0-hit substance
  re-verification still describes these bytes.
- I-C3 (target re-pin): AGREE. Pair matches my independent
  pins. All 5 W1 pin sites named and covered (header 17-18,
  dirt note 112-113, F-TABLE 484 with its 18 inheriting
  `Target as in F-TABLE` rows, FAM-SRC 1368, FAM-ENUM 1424);
  census of both old prefixes finds nothing else outside
  W2's run-6 history (lines 1646-1647, correctly standing)
  and the correction note itself.
- I-C4 (drift, nothing moves): AGREE. One docstring hunk,
  re-read; 1-for-1 swap, zero shift, code-identical by
  normalized AST. No finding cites line 1 or its suffix
  (zero hits outside `## Iterations`); the three
  docstring-citing claims sit at other spans (enumeration
  row 0 prose; F-TABLE MRO paragraphs at HEAD lines 19-41;
  R-EXT-HOOK `Mirrors` clause at HEAD line 37 — each
  re-read at HEAD bytes); count-2 member lines 977/885,
  defect lines 665-666/1046/387-391/861-864, and all 30
  `path::Symbol` index rows sit outside the hunk on
  byte-identical unshifted lines.

Nothing else changed: removing lines 1951-2057 plus the
`Status:`-line revert reconstructs exactly W1's recorded
pre-edit bytes (119094 B, 1997 lines, sha256 `d022113e…`
full match; zero `## Iterations` headers) — no finding,
verdict, or defect text altered. No tracked file touched
(window diff vs baseline names only the plan: Worker-0's
33-addition re-dispatch block, zero deletions); target
worktree blob stable at `96d2b56a…` across brief, W1, and
this pass; no plan edit; no `temp-tests/` scratch; no
`/tmp/dry-ws`; `/tmp/sc*` absent.

Checks: zero `.py` paths touched (edit set is this untracked
markdown artifact), so no ruff run is owed. The appended text
carries no process provenance (no session/agent/path tokens;
`this session` ×2 matches run-6 precedent), adds no links,
cites `path::Symbol` where symbols are named (`:NNN` pins are
allowed in `dry-*.md`), and adds no test-tier obligation
(zero-edit file item; `## Pending execution` stays none).

`Status: verified` — record-accuracy revision accepted; all
run-6 finding verdicts stand endorsed without re-trace.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-clear]: dry-rule-subsystem-clear-lifecycle.md
[dry-forms-conv]: dry-file-forms__converter.md
[dry-inputs]: dry-file-rest_framework__inputs.md
[dry-resolvers]: dry-file-rest_framework__resolvers.md

<!-- docs/SPECS/ -->
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[forms-converter]: ../../django_strawberry_framework/forms/converter.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[scalars]: ../../django_strawberry_framework/scalars.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-policies]: ../../django_strawberry_framework/utils/policies.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-converter]: ../../tests/rest_framework/test_converter.py
[test-ratchet]: ../../tests/rest_framework/test_dry_import_ratchet.py
[test-skeleton]: ../../tests/utils/test_converters.py

<!-- examples/ -->
[lib-schema]: ../../examples/fakeshop/apps/library/schema.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

