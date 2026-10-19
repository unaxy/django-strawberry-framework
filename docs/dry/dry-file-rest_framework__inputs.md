# DRY review: `django_strawberry_framework/rest_framework/inputs.py`

Status: verified
Run: 0.0.15 2026-09-22-6

Item kind: FILE (inventory backstop). No consolidation performed; one new
family named for Worker 0 (`serializer-source-axis-normalization`); every
other rule is recorded file-local with its proving challenge, converged onto
a verified family or rejection on fresh evidence, or is a fresh rejection
carrying contract difference + trigger. Zero production edits; zero tracked
files changed.

## System trace

Target owns the serializer-input SHAPING namespace
(`django_strawberry_framework/rest_framework/inputs.py`, 1870 lines,
worktree blob == HEAD blob `9b17d95229b312f23deb5778468e3abacf730ec2`;
CLEAN, absent from `git status` dirt): the lazy-path constant
(`SERIALIZER_INPUTS_MODULE_PATH`), the light-namespace trio + enriched
materializer + ledger clear + two `register_subsystem_clear` rows, the
schema-time discovery default (`get_serializer_for_schema`), the
hook-drift fingerprint (`serializer_schema_fingerprint` + five
`_fingerprint_*`), the writable basis + runtime-field + source-ownership
detectors + the one raise (`writable_serializer_fields`,
`runtime_validated_data_fields`, `writable_source_collisions`,
`writable_star_sources`, `raise_writable_source_ownership_errors`), the
narrowing spine (`_serializer_meta_value`, `_serializer_model`,
`resolve_effective_serializer_fields`, `resolve_optional_fields`), the
injected-field resolver (`resolve_injected_field_specs`), the descriptor
identity cluster (`SerializerInputShape`, `_SERIALIZER_SHAPE_REGISTRY`,
`describe_serializer_input`, `_related_model_token`, `_shape_token`,
`serializer_input_type_name`, `_default_full_shape_identity`,
`dedupe_serializer_input_shape`, `_dedupe_and_materialize_nested`, the
shape-build cache pair), the per-field walk + requiredness + collision
aggregate (`_walk_serializer_fields`, `_required_writable_field_names`,
`guard_create_required_serializer_fields`,
`_collect_input_attr_collision_messages`, `_aggregate_field_problems`),
the nested opt-in + recursion cluster (`NestedSerializerConfig`,
`normalize_nested_serializer_configs`,
`NESTED_STABLE_FIELDS_INSTRUCTION`, `read_nested_serializer_fields`,
`require_nested_fields_mapping`, `require_nested_serializer_config`,
`guard_nested_recursion`, `_NESTED_MAX_DEPTH`, `_resolve_nested_field`,
`validate_nested_config_keys`), and the two builders
(`build_serializer_input_class`, `build_serializer_inputs`).

Converter vs shaper (which owns what — the split is the spec-039 shape,
verified against both bodies at HEAD): [rf-converter][rf-converter] owns
the PER-FIELD mapping — the `serializers.Field`-keyed scalar registry +
MRO dispatch (`convert_serializer_field`), the model-backed vs model-less
dual routing + read-side delegation (`resolve_serializer_field`), the
reverse-map `InputFieldSpec` construction for scalar/relation/file, the
id-like-suffix GraphQL-name rule (`serializer_field_graphql_name`), the
description synthesis (`serializer_field_description`), the one-segment
source guard (`require_one_segment_source`), and nested DETECTION +
fail-loud default (`is_nested_serializer_field`,
`_reject_nested_serializer`). The target owns everything that needs the
FIELD SET rather than one field: discovery, narrowing, the descriptor
identity + naming + namespace lifecycle, the walk (requiredness,
nullability, descriptions, aggregate diagnostics), the nested RECURSION,
the drift fingerprint, and the ownership guards. The seam is
`resolve_serializer_field(field, model, provisional_name)` — the walk
calls it per field; the one exception is the explicitly-opted-in nested
field, which the walk routes to `_resolve_nested_field` FIRST (the
converter would reject it — nesting is opt-in only, and the converter
docstring states it has no knowledge of the recursion).

Read whole at HEAD bytes: [rf-converter][rf-converter] (1060 lines),
[rf-sets][rf-sets] (bind: `_checked_schema_field_map`,
`_serializer_input_shape_for`, `_validate_serializer_nested_fields`,
`_assert_schema_source_ownership`, class-creation validation),
[rf-resolvers][rf-resolvers] (decode: `_decode_serializer_data`,
`_decode_input_object`, `_decode_nested`; agreement:
`_assert_schema_runtime_agreement`, `_assert_field_agreement`,
`_assert_relation_agreement`, `_assert_nested_agreement`,
`_assert_runtime_write_source_ownership`), [forms-inputs][forms-inputs]
+ [mutations-inputs][mutations-inputs] (flavor twins, full),
[utils-inputs][utils-inputs] (the eleven composed owners:
`make_input_namespace`, `resolve_effective_fields`,
`normalize_field_name_sequence`, `guard_dropped_required`,
`iter_input_field_collisions`, `build_strawberry_input_class`,
`generated_input_type_name`, `get_or_store_shape_build`,
`make_shape_build_cache`, `optional_input_field`, `pascalize_token`, plus
the `InputFieldSpec` record), [types-converters][types-converters]
(read-side scalar/enum owners — target reaches them only through the
converter), [mutations-sets][mutations-sets] (snapshot slots +
`cached_build_input` / `build_and_stash_input` seam +
`_fingerprint` prose), [forms-sets][forms-sets] (dual-builder bind call),
[utils-converters][utils-converters] (MRO skeleton — clean), the contract
source [spec-039][spec-039] (Decision 7 + the build/stash/name seam row),
[glossary][glossary] (`SerializerMutation` anchors), oracles
[test-rf-inputs][test-rf-inputs] (1906 lines, 95 `def test` lines, CLEAN)
+ the live serializer rows in [test-library-api][test-library-api] and
[lib-schema][lib-schema] (nested `shelves` opt-in), and the verified
artifacts [dry-mutid][dry-mutid] (F2/R1 as trigger, re-derived fresh),
[dry-clear][dry-clear] (member-9/13 rows as trigger, re-derived fresh),
[dry-filters-inputs][dry-filters-inputs] (R-a/R-c/R-g as triggers),
[dry-orders-inputs][dry-orders-inputs] (R-conv/R-norm/R-build/R-guards as
triggers), [dry-rf-init][dry-rf-init] (guard census as trigger),
[dry-hook-context][dry-hook-context] (R4/R6/R7 as triggers),
[dry-reverse-map][dry-reverse-map] (orientation only — its owner symbol
is worktree-only, see R-reverse). Filters/orders twin BODIES were judged
via HEAD greps (signatures + the twin `INPUTS_MODULE_PATH` defs), not
full re-reads — the verified twin artifacts already carry the
line-level comparison, used as triggers and re-derived where cited.

Dirt note (every connected-body claim below is against HEAD bytes;
worktree bytes were never relied on): target CLEAN (`9b17d952…` both
sides). Dirty-but-judged-at-HEAD (work `…` / HEAD `…`):
[rf-converter][rf-converter] `95568390…`/`32904418…`,
[rf-sets][rf-sets] `70a1e1b1…`/`2c7117d6…`,
[rf-resolvers][rf-resolvers] `c0b54039…`/`8024703e…`,
[filters-inputs][filters-inputs] `06797dc7…`/`82b52d97…`,
[orders-inputs][orders-inputs] `889b5971…`/`6f6ec946…`,
[mutations-inputs][mutations-inputs] `fcbb964d…`/`fc442047…`,
[forms-inputs][forms-inputs] `436fcf42…`/`55614839…`,
[types-converters][types-converters] `679c9448…`/`9ceb34af…`,
[utils-inputs][utils-inputs] `47b2af21…`/`ee31d360…`,
[utils-strings][utils-strings] `ffa4fee0…`/`3ec3b262…`,
[mutations-sets][mutations-sets] `936f5ae7…`/`cffa29e5…`,
[forms-sets][forms-sets] `98ef150d…`/`36ce80b4…`,
[registry][registry] `612bea87…`/`9cc8bb55…`,
[test-library-api][test-library-api] `2cd94a6a…`/`1f107fff…` (live
claims rest on HEAD greps only; the worktree live file was never read).
HEAD-body snapshots were taken via `git show HEAD:<path>` before any
judgment; full blob ids sit in each finding's Freshness row. Clean
witnesses re-hashed both sides: [rf-init][rf-init] (`45cf7b63…`),
[hook-context][hook-context] (`f4910159…`), [pkg-root][pkg-root]
(`0ef72601…`), [exceptions][exceptions] (`e06b0b7f…`),
[utils-converters][utils-converters] (`5332f054…`),
[test-rf-inputs][test-rf-inputs] (`14c9d17e…`), [spec-039][spec-039]
(`cf78af93…`), [glossary][glossary] (`d3ef357c…`),
[lib-schema][lib-schema] (`bed9d071…`).
HEAD at dispatch `5ee86193`, still `5ee86193` at every fingerprint above.

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — searched, converter FIRST whole
   then both write twins whole. Converter owns per-field mapping,
   target owns shaping (seam `resolve_serializer_field`; the nested
   opt-in routes around the converter's fail-loud default by design).
   Mutations twin: name-SET identity (`mutation_input_shape`) vs this
   module's per-field DESCRIPTOR identity — opposite identity contracts
   (R-mutid, CONVERGE verified [dry-mutid][dry-mutid] R1 on fresh
   evidence); model reverse-map remap scheme vs nested never-remap
   (R-reverse); mutation materializer audits while this one enriches
   (F-ENRICH). Forms twin: same light namespace trio, same
   `guard_dropped_required` spine with a different requiredness basis +
   different waiver (R-guard); raise-first collisions vs collect+aggregate
   over the shared walk (R-coll); name-set narrowing vs descriptor naming
   (R-mutid covers); partial-keeps-column-less-required vs
   partial-all-optional (R-walk); forms discovery reads declared fields
   while this guards lazy `.fields` materialization (R-disc);
   out-of-vocabulary kind guard exists forms-only (R-opvocab, routed to
   the maintainer). Set twins (filters/orders): their modules colocate leaf
   conversion while the serializer flavor splits converter from shaper
   (R-split); their `normalize_input_value` has no counterpart here —
   serializer decode lives in [rf-resolvers][rf-resolvers] (R-norm);
   their `HIDE_FLAT_FILTERS`/logic/kind surfaces are absent here by
   contract (spec-039 has no lookup vocabulary — no twin owed, triggers
   inherited from verified filters R-a..R-e). Write flavors ride the
   LIGHT `make_input_namespace` — confirmed, not a set twin (verified
   filters R-g trigger checked fresh).
2. **Sync/async twins** — inapplicable with reason: zero `async def`,
   zero `await`, zero `sync_to_async` in the target (grep count 0);
   construction runs at finalize time; no `base_queryset`, `model_for`,
   or `run_in_one_sync_boundary` definition or call (the 4
   boundary-adjacent grep hits are docstring/comment prose only); the
   two `queryset` hits are one DRF-relation introspection
   (`field.queryset.model` read, never executed) + its docstring. The
   sync write pipeline lives in [rf-resolvers][rf-resolvers], never here.
3. **Derived rather than repeated knowledge** — searched. Canonical
   names via the owned [utils-inputs][utils-inputs]
   `generated_input_type_name` (three call sites are consumers, C1);
   divergent tokens via owned `_shape_token` over owned
   `pascalize_token` (C2); module path pinned once, read by name at the
   trio build + [rf-sets][rf-sets] default + oracles (C6-analog in
   F-PATH); `field_name or` fallbacks: none — the `source or name`
   rule appears as the trivial `or` inside two detectors whose star
   behavior differs by layered design (considered, released in F-WRITE);
   relation targets read off specs, never re-derived per request;
   descriptions via the converter owner; the `writable` predicate via
   owned `writable_serializer_fields` at all three in-module use sites
   (fingerprint, narrowing, required-set) plus the [rf-sets][rf-sets]
   class-creation read — never inlined (verified body by body). One genuine second spelling found:
   the source-axis None-normalization, identical in the converter and
   `_resolve_nested_field` (FAM-SRC, count 2).
4. **Inverse / round-trip pairs** — searched. Build (this module) vs
   decode ([rf-resolvers][rf-resolvers] `_decode_*`) compose through
   the ONE [utils-inputs][utils-inputs] `InputFieldSpec` record
   (single construction site here: `_resolve_nested_field`; every other
   spec arrives from the converter and is stamped via `replace`).
   Fingerprint (class validation) vs drift compare (bind) is one
   definition here + one consumer in [rf-sets][rf-sets]. Injected-field
   record (here) vs `_assert_field_agreement` (resolvers) is one
   agreement contract in two halves (C14 — already composes by name, no
   family). Nesting encode (`nested_specs` stamped at build) vs decode
   (`_decode_nested` recursing with the same per-field machinery) is one
   contract, two halves. No second half is missing and no half is
   restated.
5. **Contracts restated in another medium** — searched. Five media:
   production code (definitions here, machinery at the eleven
   [utils-inputs][utils-inputs] owners + converter + resolvers/seams);
   contract sources ([spec-039][spec-039] Decision 7 + the seam row —
   read; the `cached_build_input` non-ride + `build_and_stash_input`
   ride are verified in-tree); independent oracles
   ([test-rf-inputs][test-rf-inputs] 95 tests spelling literals —
   builder calls spell `operation_kind="create"` literally, never the
   `CREATE` constant; naming tests never read `_shape_token`/`sha1`
   (grep 0); collision/guard/fingerprint pins spell messages; the
   `CREATE` import serves only the injected-specs provisional tests;
   the `"partial"` VALUE is pinned once cross-flavor by the forms
   out-of-vocabulary oracle, behavior pinned here); live wire
   ([test-library-api][test-library-api] serializer rows incl. the
   nested `shelves` opt-in at [lib-schema][lib-schema]); projections
   (module/class/function docstrings — the F-ENRICH collision fold and
   the parked-globals paragraph cross-reference rather than restate).
   No test iterates an owner table to build expectations.
6. **Enforcement by omission** — enumerated. Serializer lacks a
   build-time normalizer (decode is runtime, R-norm — no contract source
   demands a build-time twin); lacks lookup/logic/kind surfaces
   (spec-039 has no such vocabulary — no twin owed); lacks a Layer-6
   getter/BFS (light lifecycle by verified R-g — correctly absent:
   zero `make_dynamic_set_getter`/`make_set_meta_cache_key`/`type(`
   tokens); lacks an operation-vocabulary guard its forms sibling has
   (R-opvocab — sibling behavior justifies the investigation; NO
   contract source establishes the rule here and the kind flows only
   from framework constants, so no defect is filed and the asymmetry is
   routed to the maintainer); the dual builder's guard lacks the injected-fields
   subtraction the bind's direct guard call carries (by design — the
   bind never calls the dual builder; F-BUILD). No missing guard with a
   contract source behind it — no omission defect filed.

### Enumeration

Instrument: `ast.parse` over the worktree bytes (= HEAD bytes),
counting `ast.Module.body` statements — **64 top-level statements**
(1 docstring + 13 imports + 48 `Assign`/`AnnAssign`/`FunctionDef`/
`ClassDef` bindings + 2 `register_subsystem_clear` calls) — plus every
member of the two class bodies — **13 members** (4 config fields; 8
shape fields + `cache_key`). **50 binding rows binding 51 module names
+ 13 class members = 64 names**, every one homed below
(F = file-local incl. proposed, C = convergence onto a verified
family/rejection, R = fresh rejection). Dual-homed rows are one unit
with two roles, not double counts.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring (substrate + namespace + shape prose) | (none) | prose projection, all findings |
| 2–14 | 13 import statements (stdlib 4, DRF 2, package 7) | machinery names | consumer feeds (F-NS/F-SHAPE/F-WALK/F-NEST/F-NARROW/F-FP/F-WRITE) |
| 15 | `SERIALIZER_INPUTS_MODULE_PATH` | 1 constant | F-PATH + R-path |
| 16 | namespace trio unpack `= make_input_namespace(...)` | `_materialized_names`, `_materialize_input`, `_clear_input_namespace` | F-NS (C: verified `subsystem-clear-lifecycle`) |
| 17 | `def materialize_serializer_input_class` | 1 name | F-ENRICH (+ F-NS ledger write) |
| 18 | `def clear_serializer_input_namespace` | 1 name | F-NS (C: verified `subsystem-clear-lifecycle` member 9) |
| 19 | `register_subsystem_clear(...)` call | bus row, owner `rest_framework.input_namespace` | F-NS (C) |
| 20 | `_NESTED_MAX_DEPTH` | 1 constant | F-NEST |
| 21 | `class NestedSerializerConfig` + 4 fields (`fields`, `exclude`, `optional_fields`, `nested_fields`) | 1 + 4 | F-NEST |
| 22 | `def normalize_nested_serializer_configs` | 1 name | F-NEST |
| 23 | `NESTED_STABLE_FIELDS_INSTRUCTION` | 1 constant | F-NEST |
| 24 | `def read_nested_serializer_fields` | 1 name | F-NEST + R-fpread |
| 25 | `def require_nested_fields_mapping` | 1 name | F-NEST |
| 26 | `def require_nested_serializer_config` | 1 name | F-NEST |
| 27 | `def get_serializer_for_schema` | 1 name | F-DISC + R-disc |
| 28 | `def _fingerprint_relation_target` | 1 name | F-FP |
| 29 | `def _fingerprint_choices` | 1 name | F-FP |
| 30 | `def _fingerprint_converter_extra` | 1 name | F-FP |
| 31 | `def _fingerprint_nested` | 1 name | F-FP + R-fpread |
| 32 | `def _fingerprint_field_map` | 1 name | F-FP |
| 33 | `def serializer_schema_fingerprint` | 1 name | F-FP |
| 34 | `def _serializer_meta_value` | 1 name | F-NARROW |
| 35 | `def _serializer_model` | 1 name | F-NARROW |
| 36 | `def writable_serializer_fields` | 1 name | F-WRITE |
| 37 | `def runtime_validated_data_fields` | 1 name | F-WRITE |
| 38 | `def writable_source_collisions` | 1 name | F-WRITE |
| 39 | `def writable_star_sources` | 1 name | F-WRITE |
| 40 | `def raise_writable_source_ownership_errors` | 1 name | F-WRITE |
| 41 | `def resolve_effective_serializer_fields` | 1 name | F-NARROW + R-narrow |
| 42 | `def resolve_optional_fields` | 1 name | F-NARROW |
| 43 | `def resolve_injected_field_specs` | 1 name | F-INJ + R-stamp |
| 44 | `class SerializerInputShape` + 8 fields + `cache_key` | 1 + 9 | F-SHAPE + R-mutid |
| 45 | `_SERIALIZER_SHAPE_REGISTRY` | 1 name | F-SHAPE (+ F-NS clear row) |
| 46 | `def describe_serializer_input` | 1 name | F-SHAPE |
| 47 | `def _related_model_token` | 1 name | F-SHAPE |
| 48 | `def _shape_token` | 1 name | F-SHAPE |
| 49 | `def serializer_input_type_name` | 1 name | F-SHAPE + R-mutid |
| 50 | `def _required_writable_field_names` | 1 name | F-WALK + R-guard |
| 51 | `def guard_create_required_serializer_fields` | 1 name | F-WALK + R-guard |
| 52 | `def _collect_input_attr_collision_messages` | 1 name | F-WALK + R-coll |
| 53 | `def _aggregate_field_problems` | 1 name | F-WALK + R-coll |
| 54 | `def _walk_serializer_fields` | 1 name | F-WALK + R-walk + R-stamp |
| 55 | `def guard_nested_recursion` | 1 name | F-NEST |
| 56 | `def dedupe_serializer_input_shape` | 1 name | F-SHAPE |
| 57 | `def _dedupe_and_materialize_nested` | 1 name | F-SHAPE |
| 58 | `def _resolve_nested_field` | 1 name | F-NEST + FAM-SRC (new family) + R-nestname |
| 59 | `def validate_nested_config_keys` | 1 name | F-NEST |
| 60 | `def _default_full_shape_identity` | 1 name | F-SHAPE |
| 61 | `def build_serializer_input_class` | 1 name | F-BUILD |
| 62 | `def build_serializer_inputs` | 1 name | F-BUILD |
| 63 | shape-cache pair unpack `= make_shape_build_cache()` | `_serializer_shape_build_cache`, `clear_serializer_shape_build_cache` | F-SHAPE + F-NS (C: member 13) |
| 64 | `register_subsystem_clear(...)` call | bus row, owner `rest_framework.shape_cache` | F-NS (C) |

Rules: R-path lazy-module constant (15); R-ns namespace lifecycle
(16–19, 63–64); R-enrich collision enrichment (17); R-disc default
discovery (27); R-fp hook-drift fingerprint (28–33); R-write writable
basis + ownership (36–40); R-narrow narrowing + optional (34–35, 41–42);
R-inj injected specs (43); R-shape descriptor identity (44–49, 56–57,
60, 63); R-walk walk + guards (50–54); R-nest nested opt-in + recursion
(20–26, 55, 58–59); R-build builders (61–62). One new family named
(FAM-SRC, the count-2 source normalization); twelve file-local rows;
fourteen fresh rejections with difference + trigger + home (R-mutid +
R-norm converge with prior verdicts on fresh evidence; R-opvocab routed
to the maintainer); five adopted convergences needing no new row (verified
`subsystem-clear-lifecycle` bus members 9 + 13, guard posture,
frozen-record idiom, filters R-g, orders R-conv direction) — all named
for Worker 0 (see `## Index rows for Worker 0`).

Static probe (AST + `git grep` at HEAD, read-only): `type_name_for`,
`make_dynamic_set_getter`, `make_set_meta_cache_key`, `model_for`,
`base_queryset`, `run_in_one_sync_boundary`, `resolve_lazy_class`,
`normalize_input_value`, `require_drf`, `Ordering` appear **zero** times
as definitions or calls in the target — no second owner for any indexed
machinery, no normalize twin, no guard call, no Layer-6 surface.
`InputFieldSpec(` is constructed directly **once** (row 58, nested
kinds only); every other spec arrives from the converter and is stamped
via `replace` (rows 43, 54).

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. All bodies judged at HEAD bytes.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | R-shape suffix | canonical suffix rule change (`Input`/`PartialInput` spelling) | **0 here, 1** at [utils-inputs][utils-inputs] `generated_input_type_name` (3 call sites follow) | independent — proves consumer |
| C2 | R-shape token | new descriptor axis (e.g. fold an emitted-nullability flag) | **1 here** (`_shape_token` + shape + namer move as one rule) | independent |
| C3 | R-shape description axis | drop the description discriminant | **1 here** (token + identity + gate walk move together) | independent |
| C4 | R-shape relation token | target-model identifier change | **1 here** (`_related_model_token`; converter + mutations untouched) | independent |
| C5 | R-ns lifecycle | new reset slot / replay posture | **1** (bus + `make_input_namespace`; 0 here — unpack + wrappers + rows follow) | independent — proves single ownership |
| C6 | R-enrich wording | collision-enrichment reword | **1 here** (mutation audit + form thin pass-through untouched) | independent |
| C7 | R-disc discovery | lazy-`.fields` guard reword/rescope | **1 here** (forms `get_form_fields` untouched) | independent + R-disc |
| C8 | R-fp fingerprint | new SDL-affecting axis (e.g. fold `default`) | **1 here** (cluster + [rf-sets][rf-sets] compare follows) | independent |
| C9 | R-nest opt-in | new config axis (e.g. per-field description override) | **1 here** (record + normalize + walk + validate + fingerprint gate move as one rule) | independent |
| C10 | R-nest source axis | source-None-normalization change | **2** (converter line + row 58 line — identical spellings) | NEW FAMILY FAM-SRC |
| C11 | R-write ownership | star/collision wording or `source or name` core change | **1 here** (detectors + raise; [rf-sets][rf-sets]/[rf-resolvers][rf-resolvers] follow as enforcement sites) | independent |
| C12 | R-narrow basis | drop-rule change (e.g. `HiddenField` becomes input) | **1 here** (`writable_serializer_fields`; form basis untouched) | independent + R-narrow |
| C13 | R-narrow optional | partial honors `optional_fields` | **1 here** (zeroing arm + namer flag move together) | independent |
| C14 | R-inj agreement | new agreement axis (e.g. check annotation too) | **1 rule, 2 halves** (record here + `_assert_field_agreement` — already compose by name, no family) | independent — round-trip pair |
| C15 | R-walk requiredness | partial keeps required column-less (form parity) | **1 here** (walk arm; form walk untouched) | independent + R-walk |
| C16 | R-walk collisions | raise-first instead of collect | **1 here** (policy; `iter_input_field_collisions` spine untouched) | independent + R-coll |
| C17 | R-build dual | one-shot-selector normalization change | **1 here** (pre-pass; singular re-normalizes follow) | independent |
| C18 | R-nest naming | nested suffix scheme (e.g. `items_input`) | **1 here** (row 58 pair; converter suffix rule untouched) | independent + R-nestname |
| C19 | R-norm merge | unify with filters/orders `normalize_input_value` | separation stands (different phase: build-time value walk vs runtime decode — opposite modules under opposite changes today) | rejected-merge — proves distinct rules |
| C20 | R-shape merge | unify with mutation name-set identity | separation stands (per-field digest + explicit full-flag vs frozenset + set comparison — CONVERGE verified mutid R1) | rejected-merge — proves distinct rules |
| C21 | R-guard merge | unify with forms create guard | separation stands (DRF required-with-no-default + injected subtraction vs form required + override waiver over the shared spine) | rejected-merge — proves distinct rules |
| C22 | scalar mapping | new DRF field kind / read scalar change | **0 here** (converter registry + [types-converters][types-converters] move; target has no mapping table) | no surface — do not inherit |
| C23 | op vocabulary | third operation kind | 3 bipartitions here + [rf-sets][rf-sets] + constants move (no count claimed — routed to the maintainer, R-opvocab) | route to the maintainer |
| C24 | boundary/seed/coercion checks | change `one-sync-boundary` / seed / recourse / coercion rules | **0 here** (verified negatives: no colored pair, no seed call, no recourse/coerce token) | no surface — do not inherit |

No executable proof was run: the target is declarations + thin
wrappers + single-walk/single-predicate functions whose every behavior
is pinned by the 95 read oracles in [test-rf-inputs][test-rf-inputs]
plus the live serializer rows, and every census above is a byte-level
`git grep` over HEAD blobs or an `ast.parse` enumeration — all
read-only, none mutating, none capable of distinguishing anything the
cited oracles do not already pin. No `docs/dry/temp-tests/` scratch was
created (HEAD snapshots lived under `/tmp`, outside the repo). All
claims below are therefore `static-reviewed`; there is no
`execution-deferred` proof.

## Findings

No production edit is owed by a file item; each finding records the rule
with the challenge that proved it has no second site (convergences name
their holding family; rejections carry difference + trigger; the one
count-2 rule names its family for Worker 0).

### F-PATH — lazy-module-path constant (file-local) + R-path

- **Contract + variation.** `SERIALIZER_INPUTS_MODULE_PATH` pins the
  `"django_strawberry_framework.rest_framework.inputs"` string once so
  the trio build, every `strawberry.lazy(...)` forward ref, and
  `materialize_serializer_input_class` stay in sync. Legitimate
  variation: the string value only.
- **Sites + roles.** *Definition*: row 15 (the literal occurs exactly
  once as a definition — every other hit is an import path, prose, or
  oracle pin). *Readers*: the trio build (row 16), [rf-sets][rf-sets]
  `input_module_path` default, the literal oracle pin. *Mirrors*: the
  four `INPUTS_MODULE_PATH` flavor constants (R-path).
- **Challenges.** Module-rename → 1 here (all readers follow by name).
- **Owner + lifetime.** This constant (existing owner: the module whose
  path it names). No lifetime fields owed.
- **Migration.** None.
- **Distinct behavior (R-path).** Considered: one shared path constant.
  Difference: the VALUES must differ per family (disjoint module
  `__dict__` slots are the rule — five constants, not one). The
  serializer NAME also differs (`SERIALIZER_INPUTS_MODULE_PATH` vs
  `INPUTS_MODULE_PATH` × 4) — incidental, no contract behind it, not a
  defect. Trigger: the families merging into one input namespace.
  Durable home: the row-15 comment + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a reader re-derives
  the path" (census: one literal definition).
- **Structural gate.** The pre-existing literal-pin oracle (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); twin defs at
  [mutations-inputs][mutations-inputs] HEAD `fc442047…`,
  [forms-inputs][forms-inputs] HEAD `55614839…`,
  [filters-inputs][filters-inputs] HEAD `82b52d97…`,
  [orders-inputs][orders-inputs] HEAD `6f6ec946…` (all worktree-dirty,
  judged at HEAD def lines only); [rf-sets][rf-sets] HEAD `2c7117d6…`.

### F-NS — namespace lifecycle trio + two bus rows (CONVERGE verified `subsystem-clear-lifecycle`)

- **Contract + variation.** The light one-ledger lifecycle the mutation
  + form + serializer flavors share: ledger declaration (row 16),
  idempotent materialize + distinct-class raise (row 17, enriched — see
  F-ENRICH), ledger-only clear + shape-registry reset (row 18), and two
  pre-bind bus rows (rows 19, 64). Varies only at the owner.
- **Sites + roles.** *Definitions*: [utils-inputs][utils-inputs]
  `make_input_namespace` / `make_shape_build_cache` + the
  [registry][registry] bus. *Declarations*: rows 16, 18–19, 63–64. The
  verified [dry-clear][dry-clear] census already lists this module's two
  rows (member 9 `rest_framework.input_namespace` incl. the "one extra
  dict", member 13 `rest_framework.shape_cache`) — re-derived fresh:
  both rows verified `before_bind=True` under disjoint owners, no local
  clear body beyond the owner products + the one registry reset.
- **Challenges.** C5 → 0 here-definitions (owner moves once).
- **Owner + lifetime.** The bus + namespace owners (existing); this file
  owns its two row declarations. Stored derivations: the ledger + shape
  registry + build cache — owner this module, validity the finalize
  pass, published at materialize/build, mutated only by the trio/clear
  pair, invalidated by `registry.clear()` pre-bind.
- **Migration.** None (zero-edit item): declarations stand.
- **Distinct behavior.** The `clear_*` shape differs per flavor only in
  the serializer's one extra dict (member-9 census) — declared, not a
  second clear rule.
- **Behavioral proof.** `static-reviewed`. Rejects "a local clear body
  re-spells the ledger reset" (both clears call only owner products).
- **Structural gate.** The verified family's bus-membership gate (owned
  by the family item) + the pre-existing idempotency/collision oracles.
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); [utils-inputs][utils-inputs]
  HEAD `ee31d360…` (work `47b2af21…`); [registry][registry] HEAD
  `9cc8bb55…` (work `612bea87…`); family artifact `cf16088b`.

### F-ENRICH — collision enrichment with the registered shape (file-local)

- **Contract + variation.** On a distinct-class name collision, row 17
  re-raises with the shape registered under the name (via row 46) so a
  descriptor-derived clash is diagnosable. Legitimate variation: the
  enrichment wording only.
- **Sites + roles.** *Definition*: row 17 (the `try`/`except` enrichment;
  the idempotency + raise contract stays at the owner trio).
  *Consumers*: the phase-2.5 bind (via row 57 + [rf-sets][rf-sets]
  `build_and_stash_input`). *Siblings*: the mutation wrapper audits
  first, the form wrapper is a thin pass-through — each wrapper's extra
  is flavor-specific (the enrichment needs the serializer-only shape
  registry; sharing it would couple the flavors over nothing).
- **Challenges.** C6 → 1 here (both sibling wrappers untouched —
  opposite change responses prove distinct rules).
- **Owner + lifetime.** Row 17 (existing owner: the module holding the
  shape registry). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** Considered: a shared enriching materializer.
  Difference: enrichment reads `_SERIALIZER_SHAPE_REGISTRY`, which only
  this flavor has. Trigger: a second flavor gaining a shape registry.
  Durable home: the row-17 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "the enrichment
  masks the owner raise" (it chains with `from exc` and re-raises
  verbatim when no shape is registered).
- **Structural gate.** The pre-existing distinct-descriptor-collision
  oracle (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN);
  [mutations-inputs][mutations-inputs] HEAD `fc442047…`,
  [forms-inputs][forms-inputs] HEAD `55614839…` (both judged at the
  wrapper bodies only).

### F-SHAPE — descriptor identity + naming + dedupe (file-local) + R-mutid

- **Contract + variation.** The `SerializerInputShape` DESCRIPTOR is the
  single derived identity of a generated serializer input: ordered
  per-field `(spec, emitted annotation, description, requiredness)` +
  normalized `optional_fields` + operation + serializer class. The
  canonical `<Serializer>Input` name is reserved for the DEFAULT full
  shape only (explicit caller flag after a default-identity comparison,
  row 60); any divergence takes a deterministic descriptor-derived name
  (row 49 over row 48 tokens + row 47 relation tokens); identical
  descriptors dedupe through the post-build cache protocol (row 56,
  shared by top-level and nested builds) and the materialize ledger.
  Legitimate variation: the descriptor axes, the token digest, the
  canonical-vs-divergent gate.
- **Sites + roles.** *Definition*: rows 44–49, 56–57, 60, 63 (one rule,
  one module). *Consumers*: [rf-sets][rf-sets]
  `_serializer_input_shape_for` (build + dedupe, never pokes the cache
  directly — verified comment + body), `build_and_stash_input`
  (materialize-then-stash per the [spec-039][spec-039] seam row),
  `input_type_name` priming; row 57 (nested builds ride the SAME cache);
  the root lazy export of row 46. *Oracles*: distinct-descriptor-name
  pins (annotation / allow_null / description / relation-target
  differences), identical-dedupe pin, self-cache-key pin, sole-protocol
  pin — all spelling literals, never reading the token bodies.
- **Challenges.** C1 → 0 here (suffix owned at
  `generated_input_type_name`); C2/C3/C4 → 1 here each.
- **Owner + lifetime.** This cluster (existing owner by responsibility:
  the narrowest site the bind + nested builds + debug export can all
  depend on). Stored derivations: `_SERIALIZER_SHAPE_REGISTRY`
  (name → shape; validity the finalize pass; published at build;
  mutated only by row 61 + clear; invalidated pre-bind) and the
  shape-build cache (descriptor → pair; same lifecycle; primed
  pre-finalize by `input_type_name`, hence the pre-bind row).
- **Migration.** None.
- **Distinct behavior (R-mutid).** Considered: unify with the mutation
  name-SET identity (`mutation_input_shape` over
  `name_set_input_type_name`). Difference, re-derived fresh: identity
  basis is a per-field digest (annotation/required/kind/source/target/
  description), not a name set; full-shape is an explicit caller flag
  after a default-identity comparison, not a frozenset comparison.
  CONVERGE with verified [dry-mutid][dry-mutid] R1 on fresh evidence
  (its difference + trigger + home all re-derived identical; its
  freshness already cites this target blob). Trigger (standing):
  serializer identity collapses to a pure name set. Durable home: the
  row-49 docstring (already states the D3 boundary) + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "two distinct
  descriptors share a class" (cache key IS the descriptor; ledger
  raises on distinct-class collision) and "a hook-varied full shape
  claims the canonical name" (row 60 gate + pin).
- **Structural gate.** The pre-existing descriptor-name + dedupe +
  sole-protocol oracles (no failability run owed).
- **Coupling.** None (FAM-SRC touches row 58 only, outside this
  cluster's naming rule).
- **Freshness.** Target `9b17d952…` (CLEAN);
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (work `47b2af21…`);
  [rf-sets][rf-sets] HEAD `2c7117d6…` (work `70a1e1b1…`);
  [mutations-inputs][mutations-inputs] HEAD `fc442047…` (work
  `fcbb964d…`); [forms-inputs][forms-inputs] HEAD `55614839…` (work
  `436fcf42…`, twin wrapper); [pkg-root][pkg-root] `0ef72601…` (CLEAN,
  lazy-export table); family artifact `7533c0cf`.

### F-DISC — default schema-time discovery (file-local) + R-disc

- **Contract + variation.** Row 27 constructs the serializer no-arg and
  reads `.fields`, translating ANY failure into the override-contract
  `ConfigurationError` (Decision 7: the guard wraps the lazy `.fields`
  materialization, not the constructor). Legitimate variation: the guard
  scope + wording.
- **Sites + roles.** *Definition*: row 27. *Consumers*: the
  `SerializerMutation.get_serializer_for_schema()` classmethod default
  ([rf-sets][rf-sets]), every isolated builder call (`field_map=None`
  arms), the default-identity gate (row 60). *Twin*: forms
  `get_form_fields` (R-disc).
- **Challenges.** C7 → 1 here (forms twin untouched).
- **Owner + lifetime.** Row 27 (existing owner: the module whose
  builders consume the map). No stored derivation (returns a fresh
  `dict` snapshot per call).
- **Migration.** None.
- **Distinct behavior (R-disc).** Considered: unify with forms
  `get_form_fields`. Difference: DRF builds `.fields` LAZILY
  (context-requiring `get_fields()` raises at first access — hence the
  materialization guard), while a form's declared fields are a plain
  read; the failure modes + override contracts differ. Trigger: DRF
  fields becoming constructor-materialized. Durable home: the row-27
  docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "constructor
  failures escape raw" (both construction + `.fields` read sit inside
  the guard) — pinned by the kwarg/context oracles.
- **Structural gate.** The pre-existing loud-rejection oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN);
  [forms-inputs][forms-inputs] HEAD `55614839…` (wrapper + twin body);
  [rf-sets][rf-sets] HEAD `2c7117d6…` (hook + validator).

### F-FP — hook-drift fingerprint (file-local) + R-fpread

- **Contract + variation.** Rows 28–33 capture every SDL-affecting axis
  per WRITABLE field (name, class, source, write flag, required,
  allow_null, relation target, description inputs, choice members,
  converter discriminants, recursive opted-in nested shape) so the bind
  recomputes it and raises on a nondeterministic hook. Scoped to the
  writable set via owned row 36 (never inlined — verified in row 32)
  and gated on the opt-in tree (unopted nested records a shallow marker
  WITHOUT reading child `.fields`). Legitimate variation: the captured
  axes + the recursion bound.
- **Sites + roles.** *Definition*: rows 28–33. *Consumers*:
  class-creation capture + bind compare ([rf-sets][rf-sets]
  `_checked_schema_field_map`), the `_ValidatedMutationMeta`
  `schema_fingerprint` slot ([mutations-sets][mutations-sets] —
  prose + slot only, never a second computation). No twin: the keyset
  `order_fingerprint` binds cursor order (different responsibility);
  the orders/factories `fingerprint` mention is prose.
- **Challenges.** C8 → 1 here (compare + slot follow).
- **Owner + lifetime.** This cluster (existing owner: the module whose
  SDL the fingerprint guards). No stored derivation (pure tuple
  derivation, recomputed per window; the slot's lifetime is the
  validated-Meta snapshot, owned at [mutations-sets][mutations-sets]).
- **Migration.** None.
- **Distinct behavior (R-fpread).** Considered: row 31 reads
  `child.fields` directly with its own phase message instead of calling
  row 24. Difference: the framings are deliberately phase-specific
  ("for the determinism fingerprint" vs "under no-arg construction")
  so the consumer knows WHICH pass failed; the shared core (the row-23
  instruction + `ConfigurationError` passthrough) is already
  single-sited. Same-file intentional separation, recorded at the
  owner (row 23). Trigger: the two framings converging to one message.
- **Behavioral proof.** `static-reviewed`. Rejects "a read-only nested
  serializer's `.fields` is read" (writable drop precedes descent, both
  callers pass narrowed maps) and "an unopted nested drift goes
  undetected" (shallow marker still flips on nested↔scalar change).
- **Structural gate.** The pre-existing drift-detection oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); [rf-sets][rf-sets] HEAD
  `2c7117d6…` (work `70a1e1b1…`); [mutations-sets][mutations-sets] HEAD
  `cffa29e5…` (work `936f5ae7…`, slot + prose only);
  [keyset][keyset] `df4b5e2f…` (CLEAN; exclusion by signature +
  docstring read — order binding, not hook drift);
  [orders-factories][orders-factories] `4f35b66b…` (CLEAN; prose-only
  mention).

### F-WRITE — writable basis + runtime fields + source ownership (file-local)

- **Contract + variation.** Row 36 is the ONE writable basis
  (`read_only` + `HiddenField` drop) for inputs, injected validation,
  and collision checks; row 37 adds default-supplying runtime fields
  (non-partial only); rows 38–39 detect duplicate writable sources
  (`source or name`, `*` excluded) and whole-object `source="*"` fields;
  row 40 is the ONE raise path for schema-time ([rf-sets][rf-sets]) and
  runtime ([rf-resolvers][rf-resolvers]) ownership checks. Legitimate
  variation: the writable predicate, the default-supply rule, the
  wordings.
- **Sites + roles.** *Definitions*: rows 36–40 (detection + raise both
  here; rows 38–39 have zero production callers outside row 40 —
  census: target + tests only). *Enforcement sites (consumers)*:
  [rf-sets][rf-sets] `_assert_schema_source_ownership` (schema-time,
  root + nested) and [rf-resolvers][rf-resolvers]
  `_assert_runtime_write_source_ownership` (runtime) — two sites
  calling ONE raise, not two definitions. *Oracles*: drop/guard/star
  pins spelling literals.
- **Challenges.** C11 → 1 here (both enforcement sites follow).
  Considered: the walk's `source_of` lambda (`spec.source or
  spec.target_name`, row 52) vs row 38's `source or name` — released,
  not a twin: the `or` is Python semantics, not a package rule, and the
  star behavior differs by layered design (star never reaches the walk;
  the converter rejects it first). The row-52 docstring already
  cross-references row 38 — the recorded-at-owner pattern.
- **Owner + lifetime.** Rows 36–40 (existing owner: the module both
  enforcement sites already import). No stored derivation.
- **Migration.** None.
- **Distinct behavior.** None beyond the released `or` above; no twin
  in any sibling flavor (forms/model flavors have no `source` axis).
- **Behavioral proof.** `static-reviewed`. Rejects "a narrowed-out
  defaulted field escapes ownership" (row 37 feeds row 40 at runtime)
  and "a star field is collision-exempt" (row 39 rejects it first).
- **Structural gate.** The pre-existing ownership oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); [rf-sets][rf-sets] HEAD
  `2c7117d6…` (work `70a1e1b1…`); [rf-resolvers][rf-resolvers] HEAD
  `8024703e…` (work `c0b54039…`).

### F-NARROW — narrowing + optional-fields override (file-local) + R-narrow

- **Contract + variation.** Rows 34–35 read the serializer's own
  `Meta.model` (or `None` for a plain serializer — the model-less
  routing basis, load-bearing for nested plain serializers); row 41
  drops to the writable basis then narrows via the shared
  `resolve_effective_fields` spine with serializer message knobs
  (read-only/`HiddenField` names fail loud in EITHER selector; empty
  set raises); row 42 normalizes + validates `Meta.optional_fields`
  against the effective set (create-only; zeroed for partial AFTER
  validation so update shapes dedupe). Legitimate variation: the
  Meta keys, the drop basis, the knobs.
- **Sites + roles.** *Definitions*: rows 34–35, 41–42 (the drop basis +
  knobs; the spine is owned at [utils-inputs][utils-inputs]).
  *Consumers*: rows 60–62, [rf-sets][rf-sets] (bind + class creation).
  Row 35 is the single code reader of `serializer_class.Meta.model`
  for conversion routing ([rf-sets][rf-sets] resolves the MUTATION's
  model through `resolve_meta_model`/`resolve_backed_model_or_raise` +
  `require_model_class` — a must-resolve validation, vs row 35's
  may-be-`None` routing read; different contracts, verified bodies).
- **Challenges.** C12 → 1 here (form basis untouched); C13 → 1 here.
- **Owner + lifetime.** Rows 34–35, 41–42 (existing owner). No stored
  derivation.
- **Migration.** None.
- **Distinct behavior (R-narrow).** Considered: unify row 41 with forms
  `resolve_effective_form_fields`. Difference: the drop basis differs
  (`read_only`/`HiddenField` vs the form basis incl. its
  suitability rule) and the message knobs differ (serializer nouns +
  non-writable wording); only the spine is shared — already composed
  by name. Trigger: the two bases converging to one predicate.
  Durable home: the row-41 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "excluding a
  read-only field is a silent no-op" (fails loud — pinned) and "the
  serializer's own `Meta.optional_fields` is read" (only the
  mutation's — pinned).
- **Structural gate.** The pre-existing narrowing/optional oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN);
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (work `47b2af21…`);
  [forms-inputs][forms-inputs] HEAD `55614839…` (twin body);
  [rf-sets][rf-sets] HEAD `2c7117d6…` (model seam).

### F-INJ — injected-field specs (file-local) + R-stamp

- **Contract + variation.** Row 43 resolves each
  `Meta.injected_fields` name to its schema-time `InputFieldSpec` from
  the SAME field map the input build used, under the operation's OWN
  provisional name (so a serializer-only choice enum matches the
  runtime-agreement re-derivation), holding injected values to the
  present/writable/source/kind/relation-model agreement — requiredness
  deliberately unset (present by construction). Legitimate variation:
  the resolved axes + the provisional rule.
- **Sites + roles.** *Definition*: row 43. *Consumers*:
  [rf-sets][rf-sets] stash; [rf-resolvers][rf-resolvers]
  `_assert_field_agreement` re-derives under the same provisional (the
  C14 round-trip pair — already composes by name, no family).
- **Challenges.** C14 → 1 rule, 2 halves (no consolidation owed — the
  halves sit in different phases by construction).
- **Owner + lifetime.** Row 43 (existing owner). No stored derivation
  (resolved per bind from the threaded map).
- **Migration.** None.
- **Distinct behavior (R-stamp).** Considered: row 43's
  `replace(spec, annotation_repr=...)` vs row 54's
  `replace(spec, annotation_repr=..., required=...)` — same tokens,
  different stamp contracts: injected records the BASE annotation with
  requiredness UNSET (agreement is present/writable/source/kind/model),
  the walk records the EMITTED post-widening annotation + requiredness
  (descriptor identity needs generated nullability). Same-file
  intentional separation. Trigger: the two stamp contracts converging.
- **Behavioral proof.** `static-reviewed`. Rejects "an update mutation
  with an injected choice field raises spuriously" (operation-kind
  provisional — pinned by the docstring's own scenario).
- **Structural gate.** The pre-existing injected-spec oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); [rf-sets][rf-sets] HEAD
  `2c7117d6…`; [rf-resolvers][rf-resolvers] HEAD `8024703e…`.

### F-WALK — the per-field walk + requiredness + aggregate diagnostics (file-local) + R-walk/R-coll/R-guard

- **Contract + variation.** Row 54 resolves each effective field (nested
  opt-ins recurse via row 58, everything else via the converter),
  computes effective requiredness (create honors `field.required`
  minus `optional_fields`; partial forces ALL optional),
  nullability-widens via owned `optional_input_field` (`allow_null`
  OR optional → `T | None` + `UNSET`; required non-null gets no
  default so GraphQL enforces presence), threads converter-owned
  descriptions, stamps the EMITTED annotation repr (so an
  `allow_null`-only hook difference diverges the descriptor), and
  aggregates EVERY per-field conversion error + input-attr/GraphQL-name/
  source collision (row 52 over the shared walk + row 53 verbatim-single
  / bulleted-multi) into ONE `ConfigurationError`. Rows 50–51 are the
  per-DECLARATION create-required guard (required − effective −
  injected via the shared spine, own wording). Legitimate variation:
  the requiredness rule, the widening rule, the diagnostic policy.
- **Sites + roles.** *Definitions*: rows 50–54 (the walk + guard +
  aggregate; the widening tail, collision walk, and drop-detection are
  owned at [utils-inputs][utils-inputs] and composed by name).
  *Consumers*: rows 60–62, [rf-sets][rf-sets] (per-declaration guard
  call — the cache key excludes injection state, so the guard rides the
  declaration, not the shape; the
  [forms-inputs][forms-inputs]`::guard_create_required_fields`
  per-declaration precedent, verified fresh).
- **Challenges.** C15 → 1 here (R-walk); C16 → 1 here (R-coll); C21 →
  1 here (R-guard).
- **Owner + lifetime.** Rows 50–54 (existing owner). No stored
  derivation (the walk returns fresh lists per build).
- **Migration.** None.
- **Distinct behavior.** Three separations: (R-walk) form partial keeps
  a required COLUMN-LESS field required (reconstruction cannot supply
  it) while serializer partial forces every field optional —
  [spec-038][spec-038] vs [spec-039][spec-039] contract difference
  (mutations partial matches serializer: all-optional — verified).
  Trigger: one flavor adopting the other's partial rule. (R-coll) form
  + model flavors raise on the FIRST collision while this flavor
  collects + aggregates — diagnostic policy differs, walk shared.
  Trigger: a package-wide diagnostic policy. (R-guard) the form guard's
  requiredness basis (converter/form required incl. NullBoolean/column
  policy) + blanket-override waiver vs this guard's DRF
  required-with-no-default + per-field injected subtraction — different
  bases + different waivers over the shared spine. Trigger: the bases
  converging. Durable homes: the row-51/52/54 docstrings + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "a nullable required
  field is GraphQL-required" (omittable + resolver strips `UNSET` →
  DRF raises field-keyed — pinned), "a second same-shape declaration
  suppresses the guard" (per-declaration call — pinned), "a single
  problem changes wording" (verbatim-single — pinned).
- **Structural gate.** The pre-existing requiredness/guard/collision
  oracles (no failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN);
  [utils-inputs][utils-inputs] HEAD `ee31d360…` (work `47b2af21…`);
  [forms-inputs][forms-inputs] HEAD `55614839…`,
  [mutations-inputs][mutations-inputs] HEAD `fc442047…` (twin bodies);
  [rf-converter][rf-converter] HEAD `32904418…` (work `95568390…`);
  [rf-sets][rf-sets] HEAD `2c7117d6…`.

### F-NEST — nested opt-in + recursion (file-local) + R-nestname

- **Contract + variation.** Row 21 is the explicit opt-in record (row 22
  normalizes one-shot selectors once; rows 25–26 + 59 fail loud on
  non-mapping values / non-nested keys at EVERY level); row 24 is the
  one read-or-reject path for an opted-in child's `.fields`; row 55 +
  row 20 enforce the cycle/depth backstops; row 58 builds the nested
  input RECURSIVELY through row 61 (threading the config's narrowing +
  deeper opt-ins), dedupes + materializes it (row 57, same cache +
  ledger as top-level), and stamps the recursive `nested_specs`
  reverse map; the framework never auto-saves nested data (the parent
  serializer's own `create()`/`update()` owns the write, override
  required at class creation). Legitimate variation: the config axes,
  the guards, the recursion threading.
- **Sites + roles.** *Definition*: rows 20–26, 55, 58–59 (+ row 23's
  shared instruction). *Consumers*: [rf-sets][rf-sets]
  (`_validate_serializer_nested_fields` via rows 25–26,
  `_assert_schema_source_ownership` via rows 24/41/55);
  [rf-resolvers][rf-resolvers] (`_decode_nested`,
  `_assert_nested_agreement` — decode/agreement halves composing via
  `nested_specs`); the row-31 fingerprint gate (opt-in-gated descent).
  *Kind owners*: [rf-converter][rf-converter] (`NESTED_SINGLE`/
  `NESTED_MULTI` names + detection; the recursion lives here — the
  converter docstring states it has no knowledge of it).
- **Challenges.** C9 → 1 here (record + walk + validate + gate move as
  one rule); C18 → 1 here (R-nestname); C10 → 2 — the source line
  inside row 58 is FAM-SRC (below), the ONLY count-2 member of this
  cluster.
- **Owner + lifetime.** Rows 20–26, 55, 58–59 (existing owner: the
  module owning the recursive build). No stored derivation (the config
  tree is an immutable consumer declaration; recursion state is
  call-local).
- **Migration.** None (FAM-SRC migrates one line of row 58, not the
  cluster).
- **Distinct behavior (R-nestname).** Considered: row 58 pairs
  `(field_name, graphql_camel_name(field_name))` inline instead of
  calling [rf-converter][rf-converter]`::serializer_field_graphql_name`.
  Difference: nested kinds sit OUTSIDE the relation suffix contract
  (never remapped — input_attr is always the declared name); the inline
  equals the converter's non-relation arm result, and both compose the
  ONE [utils-strings][utils-strings]`::graphql_camel_name` — a change
  to the camel rule moves once. Trigger: nested fields joining a suffix
  scheme. Durable home: the row-58 docstring + this artifact.
- **Behavioral proof.** `static-reviewed`. Rejects "an unopted nested
  field builds silently" (falls through to the converter raise —
  pinned), "a nested cycle recurses forever" (cycle marker in
  fingerprint + loud guard in build — pinned), "nested data bypasses
  the serializer's write" (passed to `create()`/`update()` inside the
  pipeline transaction — live-pinned via the `shelves` opt-in).
- **Structural gate.** The pre-existing nested + live `shelves` oracles
  (no failability run owed).
- **Coupling.** FAM-SRC (one line of row 58; the family item owns it).
- **Freshness.** Target `9b17d952…` (CLEAN);
  [rf-converter][rf-converter] HEAD `32904418…` (work `95568390…`);
  [rf-sets][rf-sets] HEAD `2c7117d6…` (work `70a1e1b1…`);
  [rf-resolvers][rf-resolvers] HEAD `8024703e…` (work `c0b54039…`);
  [lib-schema][lib-schema] `bed9d071…` (CLEAN, opt-in site);
  [test-library-api][test-library-api] HEAD `1f107fff…` (live rows).

### F-BUILD — the single + dual builders (file-local)

- **Contract + variation.** Row 61 builds ONE `@strawberry.input` +
  descriptor (narrow → validate nested keys → resolve optional (zeroed
  for partial AFTER validation) → provisional-name walk → canonical
  gate → class + shape + registry record; nested classes materialize
  during the walk, the top class stays unmaterialized for the bind).
  Row 62 builds BOTH shapes with the create-required guard: it
  pre-normalizes every one-shot selector ONCE and threads the stable
  tuples into both passes so the create pass cannot exhaust an iterator
  before the partial pass. Legitimate variation: the build order, the
  pre-normalization set.
- **Sites + roles.** *Definitions*: rows 61–62. *Consumers*: row 61 —
  [rf-sets][rf-sets] `_serializer_input_shape_for` (per shape per
  declaration, with the separate per-declaration guard) + row 58
  (nested recursion); row 62 — package tests ONLY (HEAD census: target
  + [test-rf-inputs][test-rf-inputs]; zero production callers, unlike
  [forms-sets][forms-sets] which calls the form dual builder with
  `guard_required=False` after its own per-declaration guard).
- **Challenges.** C17 → 1 here.
- **Owner + lifetime.** Rows 61–62 (existing owner). No stored
  derivation (row 61 records into the F-SHAPE registries, owned there).
- **Migration.** None. Principle-11 keep-note for row 62 (recorded
  here at the owner so it is not re-raised): the zero-production-caller
  dual builder is NOT dead indirection — it is the documented isolated-
  build entry whose load-bearing responsibility is the one-shot-selector
  pre-normalization across the pair (the bind does not need it because
  class creation stores normalized Meta tuples). Deleting it would push
  iterator-safety onto every isolated caller. Keep.
- **Distinct behavior.** The dual builder's guard carries NO
  injected-fields subtraction (unlike the bind's direct guard call) —
  by design: isolated builds have no declaration to subtract from, and
  the bind never calls row 62. Not a defect (verified call graph).
- **Behavioral proof.** `static-reviewed`. Rejects "the partial pass
  sees an exhausted selector" (pre-normalized tuples — pinned, incl.
  the nested-config one-shot pin) and "an update `optional_fields`
  perturbs the partial name" (zeroed after validation — pinned).
- **Structural gate.** The pre-existing dual-build oracles (no
  failability run owed).
- **Coupling.** None.
- **Freshness.** Target `9b17d952…` (CLEAN); [rf-sets][rf-sets] HEAD
  `2c7117d6…` (bind path); [forms-sets][forms-sets] HEAD `36ce80b4…`
  (work `98ef150d…`, dual-call precedent);
  [test-rf-inputs][test-rf-inputs] `14c9d17e…` (CLEAN).

### F-NOSURF — verified no-surface routings (converge, no new rows)

Four standing verdicts re-derived fresh against this target's REAL
surface (each a trigger checked, never inherited):

- Guard posture: target makes ZERO `require_drf` calls (grep 0) —
  each submodule imports DRF directly and relies on the leaf
  `__init__` executing first. CONVERGE with verified
  `rest-framework-per-module-guard-calls` (durable home the leaf
  docstring) on fresh evidence. No guard owed here.
- Frozen-record idiom: rows 21/44 are frozen dataclasses like
  `UploadMetadata` / `CandidateFilterMetadata` — the frozen shape is
  an idiom, not a rule (disjoint fields, disjoint lifecycles).
  CONVERGE with verified `hook-upload-metadata-vs-sibling-records`
  on fresh evidence (negative census re-derived: zero
  `HookContext`/`UploadMetadata` tokens here).
- Scalar/type mapping: target holds NO mapping table — every annotation
  arrives from [rf-converter][rf-converter] (which routes model-backed
  fields through the read-side converters). C22 → 0 here. No
  `types/converters.py` family lists this file; correctly absent.
- Set-family machinery: zero BFS/collision/cache/`type(...)`/Layer-6
  tokens (static probe) — the light lifecycle, not a set twin.
  CONVERGE with verified filters R-g on fresh evidence.

### FAM-SRC — `serializer-source-axis-normalization` (NEW FAMILY for Worker 0)

- **Contract + variation.** The `InputFieldSpec.source` axis
  normalization: a field's `source` that is falsy or equal to the
  declared name records `None` (keeps the reverse map terse and
  form-symmetric); otherwise records the one-segment source. Varies
  only as the axis contract (e.g. empty-source handling, explicit
  equal-source recording).
- **Sites + roles.** *Definitions (2)*: [rf-converter][rf-converter]
  `::resolve_serializer_field` (`source = field.source if
  (field.source and field.source != field_name) else None`, with
  `field_name = field.field_name`) and row 58 (`_resolve_nested_field`,
  character-identical line, with `field_name` the effective-dict key).
  The two bind the same value under the supported contract:
  [rf-sets][rf-sets]`::_validate_schema_field_map` REJECTS a hook map
  whose key differs from the bound `field.field_name`, so key ==
  `field_name` on every bind-path build (verified body). *Consumers*:
  every `spec.source` reader (resolvers decode + agreement guards,
  `describe_serializer_input`, tests pinning `source=None` vs
  explicit). *Prose*: row 58's own docstring claims sameness
  ("records the SAME normalized one-segment source scalar / relation
  fields do") — the code asserts one rule, the bodies spell it twice.
- **Challenges.** C10 → **2** (a normalization change moves both
  lines; consumers follow). No other spelling exists package-wide
  (the `source or name` detectors in rows 38/52 are the trivial `or`
  over different domains with different star behavior — explicitly
  excluded, see F-WRITE).
- **Owner + lifetime.** Candidate: [rf-converter][rf-converter]
  (owns the source axis: `require_one_segment_source`,
  `backing_model_field`, and the axis construction for every other
  kind; row 58 already composes the guard by name — only the
  normalization is inlined). No stored derivation (pure expression).
- **Migration (sketch for the family item).** Converter exposes the
  normalization next to `require_one_segment_source`; row 58 calls it;
  both spec-construction sites read one expression. Oracles stay (they
  pin the axis VALUES, never the spelling).
- **Distinct behavior.** The nested `require_one_segment_source` call
  above the line stays (dotted/star rejection precedes normalization
  on both paths — already shared, not part of this family).
- **Behavioral proof.** `static-reviewed` for the COUNT (both lines
  read at HEAD bytes, character-identical; the key==name enforcement
  verified in the validator body). Consolidation proof owed by the
  family item (existing source-axis oracles + a failability run).
- **Structural gate.** Owed by the family item (a two-site spelling
  gate with its negative control: a hand copy passing behavior oracles).
- **Coupling.** F-NEST (row 58 host).
- **Freshness.** Target `9b17d952…` (CLEAN);
  [rf-converter][rf-converter] HEAD
  `32904418a169941c2afa1c9cd6866c55debc64f3` (work `95568390…`);
  [rf-sets][rf-sets] HEAD `2c7117d6…` (validator body).

### Remaining rejections (difference + trigger + home)

- **R-split** (converter-vs-shaper split vs filters/orders colocated
  converters). Considered: colocate the DRF leaf mapping in the target
  as filters/orders do. Difference: serializer conversion carries a
  PUBLIC extension registry (`register_serializer_field_converter`)
  + model-backed/model-less dual routing + the source axis — machinery
  the `Ordering`-leaf / kind-ladder converters have no analog of; the
  split IS the [spec-039][spec-039] shape (converter module + shaping
  module + bind + pipeline). Trigger: the registry + dual routing
  collapsing away. Home: the row-1 module docstring + this artifact.
  CONVERGE direction checked against verified filters R-a/R-c +
  orders R-conv (leaf-shape divergences) on fresh evidence.
- **R-norm** (no build-time normalizer here). Considered: unify with
  filters/orders `normalize_input_value`. Difference: different PHASE —
  their normalizer walks input VALUES at build/normalize time; the
  serializer flavor decodes at RUNTIME in [rf-resolvers][rf-resolvers]
  off the stashed reverse map (C19: opposite modules under opposite
  changes today). Trigger: serializer gaining a build-time value
  normalizer. Home: [rf-resolvers][rf-resolvers]`::_decode_input_object`
  + this artifact. CONVERGE with verified orders R-norm (same-name
  pair, fresh same-name non-pair here) + filters R-a on fresh evidence.
- **R-reverse** (nested spec construction vs the model relation-remap
  scheme). Considered: unify row 58's direct `InputFieldSpec(`
  construction with the relation input-attr remap rule. Difference:
  nested kinds NEVER remap (`input_attr` is always the declared name;
  no `_id` suffix, no id-type selection) while the remap scheme exists
  exactly for relations; row 58 is the ONLY direct construction here
  (census: 1 site) and every other spec arrives from the converter.
  HEAD-note: the verified `mutation-input-reverse-map` owner's symbol
  (`relation_input_python_attr`) exists 5× in worktree dirt but 0× at
  HEAD — this rejection is judged at HEAD bytes against the
  HEAD-resident scheme ([rf-converter][rf-converter]
  `::serializer_field_graphql_name` + row 58). Trigger: nested fields
  joining a remap scheme, or the model scheme covering nested kinds.
  Home: the row-58 docstring + this artifact. Family artifact
  `b901d083` read as orientation only.
- **R-opvocab** (no operation-vocabulary guard; ROUTED TO MAINTAINER).
  Considered: the forms out-of-vocabulary guard
  (`CREATE_SHAPED_KINDS`, pinned oracle) has no serializer counterpart
  — `operation_kind == PARTIAL` bipartitions thrice here (rows 43, 46,
  61) plus one derived op-kind (row 54), and any typo'd kind silently
  builds create-shaped. Difference: the serializer vocabulary has TWO
  kinds (total bipartition) vs forms' THREE (where `PARTIAL` to the
  dual builder degenerates); the kind flows ONLY from framework
  constants ([rf-sets][rf-sets] bind + row-54 derivation), never from
  wire or consumer config; zero oracles pin bad-kind behavior either
  way. No contract source ([spec-039][spec-039], glossary, owner prose)
  establishes the guard here — so per axis 6 this is NOT a defect and
  NOT a quiet rejection: Worker 0 surfaces the forms-asymmetry to the maintainer.
  Trigger: a third serializer kind, a consumer-supplied kind path, or
  the maintainer ruling the bipartition must fail loud. Home: this artifact +
  the maintainer's ruling.
- **R-fpread** — see F-FP (phase-specific nested-read framings).
- **R-stamp** — see F-INJ (injected-BASE vs walk-EMITTED stamps).
- **R-nestname** — see F-NEST (nested name pair vs suffix rule).
- **R-disc** — see F-DISC (lazy-`.fields` guard vs declared read).
- **R-narrow** — see F-NARROW (writable-drop bases).
- **R-walk** — see F-WALK (partial semantics).
- **R-coll** — see F-WALK (collect vs raise-first).
- **R-guard** — see F-WALK (requiredness bases + waivers).
- **R-mutid** — see F-SHAPE (descriptor vs name-set identity).
- **R-path** — see F-PATH (per-family path values).

## Defects

None. Five probed edges released without a defect: (1) the missing
operation-vocabulary guard is ROUTED TO MAINTAINER (R-opvocab), not a defect —
no contract source establishes it and the kind flows only from
framework constants; (2) the dual builder's zero production callers is
a kept isolated-build entry per principle 11 (F-BUILD), not dead code;
(3) the nested name-pair inline composes the shared `graphql_camel_name`
owner (R-nestname), not a second derivation; (4) the
`SERIALIZER_INPUTS_MODULE_PATH` name variance vs `INPUTS_MODULE_PATH`
× 4 is incidental with no contract behind it (R-path), not a defect;
(5) the two `InputFieldSpec` stamp calls share tokens but not contracts
(BASE-unset vs EMITTED-set — R-stamp), not a twin.

## Pending execution

None. Every proof is `static-reviewed` (body inspection at HEAD bytes,
package-wide `git grep` censuses, `ast.parse` enumeration, oracle
reads). Inspection suffices because the target decides no ordering
beyond finalize-time construction, no transactions, no async behavior,
and no ORM execution; the one count-2 rule (FAM-SRC) is a
character-identical spelling pair whose consolidation proof belongs to
the family item. No failability run is owed by this zero-edit file
item.

## Judgment

Zero-edit result with one new family: matrix discharged against the
real surface (converter + both write twins read whole at HEAD bytes;
set twins via verified artifacts + HEAD greps; sync/async absence and
ten machinery non-memberships verified by grep, not assumed), 64/64
names homed (1 new family, 12 file-local rows, 14 fresh rejections with
difference + trigger + home — 2 converging with prior verdicts on fresh
evidence, 1 routed to the maintainer — plus 5 adopted convergences needing no new
row), challenges recorded with definition counts (one count-2: FAM-SRC;
one route-to-the maintainer: R-opvocab), no defect with a contract source behind it. The target is a well-factored shaping layer:
eleven shared mechanics composed by name, one enriched wrapper, one
kept isolated entry, and exactly one line that restates a converter
rule.

## Index rows for Worker 0

Family, owner, files covered, holding item, status — Worker 0 alone
edits the plan; these rows are proposed transcriptions.

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `serializer-source-axis-normalization` | `django_strawberry_framework/rest_framework/serializer_converter.py` (candidate; owns the source axis) | `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/rest_framework/inputs.py` | Family `serializer-source-axis-normalization` | open |
| `serializer-input-module-path` | `django_strawberry_framework/rest_framework/inputs.py::SERIALIZER_INPUTS_MODULE_PATH` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-namespace-lifecycle-rows` | `django_strawberry_framework/registry.py` bus + `django_strawberry_framework/utils/inputs.py::make_input_namespace` (declarations here; lawful convergence onto verified `subsystem-clear-lifecycle` members 9 + 13) | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-collision-enrichment` | `django_strawberry_framework/rest_framework/inputs.py::materialize_serializer_input_class` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-descriptor-identity` | `django_strawberry_framework/rest_framework/inputs.py::SerializerInputShape` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-schema-discovery` | `django_strawberry_framework/rest_framework/inputs.py::get_serializer_for_schema` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-hook-drift-fingerprint` | `django_strawberry_framework/rest_framework/inputs.py::serializer_schema_fingerprint` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-writable-source-ownership` | `django_strawberry_framework/rest_framework/inputs.py::raise_writable_source_ownership_errors` | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-effective-narrowing` | `django_strawberry_framework/rest_framework/inputs.py::resolve_effective_serializer_fields` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-injected-field-specs` | `django_strawberry_framework/rest_framework/inputs.py::resolve_injected_field_specs` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-input-walk` | `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-nested-opt-in-recursion` | `django_strawberry_framework/rest_framework/inputs.py::NestedSerializerConfig` | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/rest_framework/sets.py`, `django_strawberry_framework/rest_framework/resolvers.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-dual-builder` | `django_strawberry_framework/rest_framework/inputs.py::build_serializer_inputs` | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | file-local |
| `serializer-identity-vs-mutation-shape` | `django_strawberry_framework/rest_framework/inputs.py::serializer_input_type_name` (rejection recorded here; CONVERGE with verified `generated-mutation-input-identity` R1 on fresh evidence) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/mutations/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-discovery-vs-form-read` | `django_strawberry_framework/rest_framework/inputs.py::get_serializer_for_schema` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-fingerprint-framings` | `django_strawberry_framework/rest_framework/inputs.py::NESTED_STABLE_FIELDS_INSTRUCTION` (rejection recorded here; same-file intentional separation) | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-narrowing-vs-form-basis` | `django_strawberry_framework/rest_framework/inputs.py::resolve_effective_serializer_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-spec-stamp-contracts` | `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields` (rejection recorded here; same-file intentional separation) | `django_strawberry_framework/rest_framework/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-partial-vs-form-partial` | `django_strawberry_framework/rest_framework/inputs.py::_walk_serializer_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-collisions-vs-raise-first` | `django_strawberry_framework/rest_framework/inputs.py::_collect_input_attr_collision_messages` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/mutations/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-guard-vs-form-guard` | `django_strawberry_framework/rest_framework/inputs.py::guard_create_required_serializer_fields` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-nested-name-vs-suffix-rule` | `django_strawberry_framework/rest_framework/inputs.py::_resolve_nested_field` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-no-build-normalizer` | `django_strawberry_framework/rest_framework/resolvers.py::_decode_input_object` (rejection recorded here; CONVERGE with verified orders R-norm + filters R-a direction on fresh evidence) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/orders/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-split-vs-colocated-converters` | `django_strawberry_framework/rest_framework/inputs.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/orders/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-spec-construction-vs-remap` | `django_strawberry_framework/rest_framework/inputs.py::_resolve_nested_field` (rejection recorded here; judged at HEAD bytes where the reverse-map owner is absent; family artifact orientation only) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-operation-vocabulary` | `django_strawberry_framework/forms/inputs.py::CREATE_SHAPED_KINDS` (asymmetry recorded here; ROUTED TO MAINTAINER — no contract source; trigger: a third serializer kind, a consumer-supplied kind path, or the maintainer's ruling) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/forms/inputs.py` | File `rest_framework/inputs.py` | rejected |
| `serializer-path-vs-flavor-paths` | `django_strawberry_framework/rest_framework/inputs.py::SERIALIZER_INPUTS_MODULE_PATH` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/rest_framework/inputs.py`, `django_strawberry_framework/mutations/inputs.py`, `django_strawberry_framework/forms/inputs.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/orders/inputs.py` | File `rest_framework/inputs.py` | rejected |

Also for Worker 0: add `## Families` item `Family
serializer-source-axis-normalization` (no artifact on disk;
undispatched). No `## Owned changes` rows (file item; zero production
edits). R-opvocab (`serializer-operation-vocabulary`) is flagged
ROUTE-TO-MAINTAINER in its finding — surface the forms-asymmetry to the maintainer rather
than treating the rejection as quietly closed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-clear]: dry-rule-subsystem-clear-lifecycle.md
[dry-filters-inputs]: dry-file-filters__inputs.md
[dry-hook-context]: dry-file-rest_framework__hook_context.md
[dry-mutid]: dry-rule-generated-mutation-input-identity.md
[dry-orders-inputs]: dry-file-orders__inputs.md
[dry-reverse-map]: dry-rule-mutation-input-reverse-map.md
[dry-rf-init]: dry-file-rest_framework____init__.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exceptions]: ../../django_strawberry_framework/exceptions.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[hook-context]: ../../django_strawberry_framework/rest_framework/hook_context.py
[keyset]: ../../django_strawberry_framework/keyset.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-factories]: ../../django_strawberry_framework/orders/factories.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[pkg-root]: ../../django_strawberry_framework/__init__.py
[registry]: ../../django_strawberry_framework/registry.py
[rf-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[rf-init]: ../../django_strawberry_framework/rest_framework/__init__.py
[rf-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[test-rf-inputs]: ../../tests/rest_framework/test_inputs.py

<!-- examples/ -->
[lib-schema]: ../../examples/fakeshop/apps/library/schema.py
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

### Trace-first record (written before opening `## Findings`)

Blindness: this section was written after reading the artifact header,
`## System trace`, `## Verification` (Matrix/Enumeration/Challenges), and
the `## Index rows for Worker 0` scaffolding (needed to locate the append
point), but BEFORE opening `## Findings` (lines 372-1084). The family /
rejection short-names below (FAM-SRC, R-mutid, R-norm, R-opvocab, R-fpread,
R-stamp) were already named in the Worker-2 dispatch brief, so their
appearance here is not inherited reasoning — every judgment cites fresh
evidence re-derived below. `## Findings` reconciliation follows in a
separate section after this one.

Target state: HEAD `5ee86193` at W2 start (verified:
`git rev-parse HEAD` → `5ee8619330e7e236b61060a1ec9cb9e62b7061aa`);
target `django_strawberry_framework/rest_framework/inputs.py` CLEAN —
worktree blob == HEAD blob `9b17d95229b312f23deb5778468e3abacf730ec2`,
1870 lines. Connected-body judgments below rest on HEAD bytes throughout
(`git show HEAD:<path>` snapshots under `/tmp/w2-inputs-head/`): the
worktree copies of `serializer_converter.py` (`95568390…`), `sets.py`
(`70a1e1b1…`), `resolvers.py` (`c0b54039…`), `filters/inputs.py`
(`06797dc7…`), `orders/inputs.py` (`889b5971…`), `forms/inputs.py`
(`436fcf42…`), `mutations/inputs.py` (`fcbb964d…`), `utils/inputs.py`
(`47b2af21…`) are hunt-dirty and were never relied on; HEAD blobs match
W1's dirt-note table 8/8 on independent re-derivation.

Window attribution (ITEM_BASELINE `4887f7947f9cd9570b0d0e10b84721184a13c1cc`):
`git diff --name-only <baseline> -- .` names exactly 2 paths —
`docs/dry/dry-0_0_15.md` (one hunk: the Worker-0 dispatch record for this
item) + `docs/bug_hunt/bug_hunt-0_0_15.md` (two hunks: hunt Worker-0 authz
scenario Iteration-2 accounting + the 18:56 UTC fold note). All three
hunks attributed hunk-by-hunk to Worker-0 / concurrent hunt bytes; zero
package/test paths; the artifact itself is the expected new untracked
file. Item NOT stopped.

#### (a) Own enumeration (instrument: `ast.parse`, worktree == HEAD bytes)

64 top-level statements (docstring + 13 imports + 48
Assign/AnnAssign/FunctionDef/ClassDef + 2 bare
`register_subsystem_clear(...)` Expr calls), independently listed 0-63
and mapped 1:1 onto the artifact's rows 1-64 (my 0 = row 1 … my 63 =
row 64; verified each row's symbol name matches). Class members: 13
named (`NestedSerializerConfig`: 4 AnnAssign fields;
`SerializerInputShape`: 8 AnnAssign fields + `cache_key` property) plus
2 class docstrings. Arithmetic verified: 51 module names bound by the 50
binding rows + 13 class members = 64 names. Member-by-member home check
is recorded in (g) after the Findings read; the COUNTS agree exactly.

#### (b) Own site/role map (13 rule clusters I would home)

- R-path: `SERIALIZER_INPUTS_MODULE_PATH` — definition (the string pinned
  once); readers are consumers (trio build, sets default, oracles).
- R-ns: trio unpack + thin wrappers + 2 bus rows — declarations
  following `utils/inputs.py::make_input_namespace` + the
  `registry.py` clear bus; the file owns no lifecycle body.
- R-enrich: `materialize_serializer_input_class` — definition (the
  try/enrich/re-raise wrapper); the wrapped `_materialize_input` is the
  composed owner.
- R-shape: `SerializerInputShape` + registry + describe + token helpers
  + namer + default-identity gate + dedupe pair + shape-cache pair —
  one descriptor-identity rule; spine consumers of
  `generated_input_type_name` / `pascalize_token` / `get_or_store_shape_build`.
- R-disc: `get_serializer_for_schema` — definition (lazy-`.fields`
  guard around default discovery).
- R-fp: `serializer_schema_fingerprint` + 5 `_fingerprint_*` —
  definition (recursive SDL-axis fingerprint); consumer in
  `rest_framework/sets.py` (drift compare).
- R-write: `writable_serializer_fields` (the ONE writable predicate —
  exactly one inline `read_only`/`HiddenField` spelling at `:604`,
  called at `:527`/`:752`/`:1128`, never inlined elsewhere) +
  `runtime_validated_data_fields` (a DIFFERENT rule: runtime
  contributors incl. defaults/HiddenField, `read_only`-only gate) +
  the two detectors + the one raise — definitions here; sets/resolvers
  are enforcement sites.
- R-narrow: `_serializer_meta_value` / `_serializer_model` /
  `resolve_effective_serializer_fields` / `resolve_optional_fields` —
  definitions; spine consumers of `resolve_effective_fields` /
  `normalize_field_name_sequence`.
- R-inj: `resolve_injected_field_specs` — definition (schema-time spec
  resolver); agreement consumer in resolvers.
- R-walk: `_required_writable_field_names` /
  `guard_create_required_serializer_fields` /
  `_collect_input_attr_collision_messages` / `_aggregate_field_problems`
  / `_walk_serializer_fields` — one walk rule; spine consumers of
  `guard_dropped_required` / `iter_input_field_collisions` /
  `optional_input_field`.
- R-nest: `NestedSerializerConfig` + normalize + instruction constant +
  readers + require-pair + depth constant + recursion guard + nested
  resolver + key validator — one opt-in-recursion rule; detection
  (`is_nested_serializer_field`) + child peel
  (`nested_serializer_child`) + one-segment guard composed from the
  converter by name.
- R-build: `build_serializer_input_class` + `build_serializer_inputs` —
  definitions (single + dual entries); the dual pre-pass owns
  one-shot-selector normalization.
- FAM-SRC (new family, endorsed below): the source-axis
  None-normalization, count 2, candidate owner
  `rest_framework/serializer_converter.py` (owns the source axis:
  `require_one_segment_source`, `backing_model_field`,
  `resolve_serializer_field`).

#### (c) Matrix judged against the real surface

1. Cross-flavor: searched (converter whole at HEAD; forms + mutations
   twins whole at HEAD; filters/orders twins via HEAD signature greps +
   the verified twin artifacts as triggers). Every mirror W1 names
   exists where named; the seam reading (per-field mapping in the
   converter, field-set shaping here) matches both bodies.
2. Sync/async: inapplicable, reason SOUND — 0 `async def`, 0 `await`,
   0 `sync_to_async` (grep-verified); finalize-time construction only.
3. Derived knowledge: searched; the `_shape_token` / path / writable /
   description derivations are single-sited as claimed. One genuine
   second spelling found independently: the source-axis
   None-normalization (inputs `:1511` + converter `:977` at HEAD —
   character-identical modulo indent; package-wide `git grep` for
   `field.source != field_name` returns exactly these 2). Neither side
   consumes the other (the nested path explicitly routes around
   `resolve_serializer_field`, which rejects nested first at converter
   `:972`; the scalar path never calls `_resolve_nested_field`), and no
   existing helper performs the normalization (`require_one_segment_source`
   is the guard, not the normalization; `backing_model_field` `:706`
   uses the different lookup spelling `field.source or field_name` — a
   different contract: lookup key must be non-None vs reverse-map scalar
   terse-None — so it is a separation, not a third member). The
   `spec.source or spec.target_name` readers (resolvers `:1749`/`:1860`/
   `:1911`, collisions `:641`/`:1234`) are CONSUMERS of the recorded
   scalar, not definitions. Count 2 STANDS; new family warranted.
4. Round-trip: searched; build vs decode compose through the ONE
   `InputFieldSpec` — direct construction exactly once (`:1526`,
   nested kinds only), `replace` stamps at `:856`/`:1380` (both
   verified by grep). Fingerprint vs drift-compare is one definition +
   one consumer. No missing half, no restatement.
5. Other media: searched. Oracles pin literals (spot-verified: builder
   tests spell `operation_kind="create"` literally; `sha1`/`_shape_token`
   absent from the test file — grep 0). No oracle reads an owner table.
6. Omission: enumerated. Operation vocabulary (forms guards, serializer
   lacks) investigated below in (e); writable-basis coverage verified
   single-predicate in (b); nested opt-in coverage (unopted → fail-loud,
   not silent skip) verified in the walk body (`:1319` routes around
   only when opted in, else falls to the converter's loud reject).

Sharded/PG cells inapplicable by construction — reason SOUND: the target
imports no `django.db`, touches no queryset/alias/dialect decision (the
2 `queryset` hits are one DRF-relation attribute read + its docstring);
`model._meta.get_field` is class metadata, not a database read.

#### (d) Convergences judged on fresh evidence (before reading Findings)

- Verified `subsystem-clear-lifecycle` members 9 + 13: the family
  artifact's census table VERBATIM names row 9
  `rest_framework.input_namespace` ("light clear + one extra dict")
  and row 13 `rest_framework.shape_cache` ("narrow … primed
  pre-finalize"), matching this file's two `register_subsystem_clear`
  calls + the two-dict clear body + the priming comment. Lawful
  convergence transcribing nothing — ENDORSED.
- Verified `generated-mutation-input-identity` R1 ("serializer
  descriptor naming stays separate; identity basis per-field digest,
  full-shape explicit caller flag; trigger: collapse to a pure name
  set"): this file's `serializer_input_type_name` still takes
  `is_full_shape` as an explicit caller flag and still builds its
  token from per-field `_shape_token` digests — the trigger has NOT
  fired, the difference holds verbatim. CONVERGE on fresh evidence —
  ENDORSED.
- Verified orders R-norm (same-named `normalize_input_value` pair are
  different rules: whole-value walk + direction check vs per-instance
  kind dispatch) + filters R-a (no leaf-shape divergence per spec-028
  Decision 5): this file defines NO `normalize_input_value` (grep 0)
  and performs NO build-time value normalization — serializer decode
  is runtime in resolvers. The candidate "serializer walk vs set
  normalizers" fails on the same contract differences (different
  phase, different signature/return/recursion) — CONVERGE direction
  ENDORSED (exact R-norm wording judged after the Findings read).

#### (e) R-opvocab route-to-the maintainer judged (fresh evidence, pre-read)

- Forms HAS the guard (HEAD `forms/inputs.py` `:686` full-vocabulary
  reject + `:880` create-side reject, both fail-loud with the
  received value); serializer + mutations LACK it (every serializer
  use is `== PARTIAL`, every mutations use `==`/`!= CREATE`).
- Kind sources are ALL framework constants: sets bind derives from
  `NON_DELETE_OPERATION_INPUT_KIND[meta.operation]` (fixed dict;
  `meta.operation` validated upstream at `mutations/operations.py`),
  the dual builder passes CREATE/PARTIAL literals, the nested path
  derives from the `is_partial` boolean. No Meta key, no wire input
  feeds `operation_kind` — a bad kind is reachable only by a direct
  internal-generator call with a wrong literal.
- Contract sources checked fresh: spec-039 contains NO
  operation-vocabulary guard requirement (only `operation_kind` hit is
  the build/stash/seam row about guard-before-cache ordering);
  glossary contains NO `operation_kind` entry; no owner prose or
  oracle establishes the rule for the serializer flavor. The "no
  contract source" reading is CORRECT.
- Disposition per axis 6: NOT a defect (no contract row broken — a
  defect would need a feasible project shape + wire/config input
  reaching a bad kind, and none exists); NOT a quiet clean rejection
  (the forms precedent + the exact silent-create-shaped failure mode
  forms guards against make the asymmetry a genuine open posture
  question — 1 of 3 flavors guards, and the guarded one is not the
  senior flavor). ROUTE-TO-MAINTAINER is the right disposition. ENDORSED.

#### (f) Owner/family calls I would make (pre-read)

- FAM-SRC: NEW FAMILY `serializer-source-axis-normalization`,
  candidate owner `serializer_converter.py` (owns every other source-
  axis verb; the nested path already composes its guard by name, so a
  `normalize_source_scalar`-shaped helper there is dependency-clean).
- Everything else: file-local or converge/reject as in (b) — no second
  new family; no holding-family route owed (the convergences name
  verified families whose rows already cover this file).

#### (g) Enumeration home check — DEFERRED to reconciliation

The 64+13 counts agree exactly (see (a)); each row's HOME is checked
member-by-member against `## Findings` in the reconciliation section
next, never by sample.

### Reconciliation (after reading `## Findings`) + verdict

Read `## Findings` lines 372–1084 whole after the trace-first record
above. Reconciliation is member-by-member, never by sample.

#### (h) Enumeration homes (rows 1–64 + 13 members — every row checked)

- Rows 1 (docstring → prose), 2–14 (imports → consumer feeds): AGREE.
- Row 15 → F-PATH + R-path; 16 → F-NS; 17 → F-ENRICH (+ F-NS ledger
  write); 18–19 → F-NS (member 9): AGREE — each home's finding names
  the row and its role.
- Rows 20–26 → F-NEST (row 23's instruction cited in F-NEST sites; row
  24 dual-homed with R-fpread in F-FP): AGREE.
- Row 27 → F-DISC + R-disc; rows 28–33 → F-FP (row 31 dual-homed with
  R-fpread): AGREE.
- Rows 34–35 → F-NARROW; rows 36–40 → F-WRITE; row 41 → F-NARROW +
  R-narrow; row 42 → F-NARROW; row 43 → F-INJ + R-stamp: AGREE.
- Row 44 (+ 8 fields + `cache_key`) → F-SHAPE + R-mutid; rows 45–49 →
  F-SHAPE (row 45 dual-homed with the F-NS clear row; row 49 dual-homed
  with R-mutid): AGREE.
- Rows 50–51 → F-WALK + R-guard; rows 52–53 → F-WALK + R-coll; row 54 →
  F-WALK + R-walk + R-stamp; row 55 → F-NEST; rows 56–57 → F-SHAPE; row
  58 → F-NEST + FAM-SRC + R-nestname; row 59 → F-NEST; row 60 →
  F-SHAPE; rows 61–62 → F-BUILD; row 63 → F-SHAPE + F-NS (member 13);
  row 64 → F-NS: AGREE.
- The 13 class members ride inside rows 21/44, both homed: AGREE.

Result: 64/64 statements + 13/13 members homed, zero orphans, zero
double-counts (dual homes are one unit with two roles, as labeled).
My rule clusters in (b) match W1's F-findings 1:1 (R-path→F-PATH …
R-build→F-BUILD, FAM-SRC identical).

#### (i) Findings vs my trace (each difference explicit)

- F-PATH/R-path, F-DISC/R-disc, F-FP/R-fpread, F-WRITE, F-NARROW/R-narrow,
  F-INJ/R-stamp, F-WALK/R-walk/R-coll/R-guard, F-NEST/R-nestname, F-BUILD:
  AGREE on contract, sites/roles, challenges, and triggers. Spot
  re-derivations fresh: the R-nestname inline equals the converter's
  non-relation arm (`serializer_converter.py:605` returns
  `field_name, graphql_camel_name(field_name)` — identical pair, one
  shared owner); the R-walk partial difference holds verbatim at HEAD
  (forms `:725` keeps column-less required, mutations `:90` + this
  `:1343` force all-optional); the R-stamp BASE-vs-EMITTED difference
  holds (`:856` vs `:1380`–`:1384`); the R-fpread phase framings differ
  as quoted; detectors have zero production callers outside row 40
  (census: defs + `:677`/`:692` + 2 test pins).
- F-NS (CONVERGE clear-lifecycle): AGREE — members 9 + 13 re-derived
  verbatim from the family census; transcribes nothing.
- F-SHAPE/R-mutid (CONVERGE mutid R1): AGREE — difference + trigger +
  home re-derived identical; trigger not fired.
- R-norm (CONVERGE orders R-norm + filters R-a): AGREE — no
  `normalize_input_value` here (grep 0); different-phase difference
  stands; converge direction sound.
- F-NOSURF + R-split's fifth: AGREE on all five adopted convergences —
  guard posture (0 `require_drf` calls, direct DRF import, leaf-first
  reliance — matches the verified row), frozen idiom (0
  `HookContext`/`UploadMetadata` tokens, disjoint fields/lifecycles),
  scalar mapping (C22, 0 here — correctly a no-surface, not a row),
  filters R-g (light lifecycle, zero Layer-6 tokens), orders R-conv
  direction (leaf-shape divergences stay separate).
- FAM-SRC: AGREE — count 2 re-derived package-wide (exact-spelling
  `git grep` returns exactly inputs `:1511` + converter `:977`);
  character-identical modulo indent; neither side consumes the other
  (verified both directions); no existing normalizing helper (the
  guard is not the normalization; `:706` is the different lookup
  contract); `spec.source or …` readers are consumers. The key==name
  binding equivalence holds under the supported contract — the
  sets-validator body (`_validate_schema_field_map`, sets.py
  `:192`–`:206` at HEAD) rejects key≠`field_name`, verified fresh.
  Candidate owner `serializer_converter.py` endorsed (owns every
  other source-axis verb; dependency-clean).
- R-split, R-reverse: AGREE. R-reverse's HEAD-note verified exactly:
  `relation_input_python_attr` 0× at HEAD package-wide, 5× in
  worktree `mutations/inputs.py` source (plus 2 stale `.pyc`
  echoes) — judging at HEAD bytes against the HEAD-resident scheme
  with the family artifact as orientation-only is the correct
  handling of adopted-but-unlanded dirt.
- R-opvocab (ROUTED TO MAINTAINER): AGREE — "no contract source" re-derived
  (spec-039 / glossary / owner-prose / oracle sweep all negative);
  kind-from-constants-only re-derived (bind map + dual literals +
  boolean derivation); forms-guard/mutations-unguarded census
  re-derived (1-of-3 guards, guarded one is not senior). Route
  disposition correct per axis 6; not a defect, not a quiet close.
- `## Defects` (none + 5 released edges): AGREE on all five — (1)
  routed, not filed; (2) dual builder kept per principle 11 (zero
  production callers re-censused: def + tests only, zero examples
  hits); (3) nestname composes the owner; (4) path-name variance
  incidental; (5) stamps share tokens, not contracts. No edge breaks
  a contract row.
- `## Pending execution` (none) + static-only proofs: AGREE —
  finalize-time construction, no ordering/transaction/async/ORM
  decisions; FAM-SRC consolidation proof correctly deferred to the
  family item. Sharded/PG inapplicability-by-construction SOUND
  (no `django.db`, no alias/dialect surface).
- Freshness rows: every cited blob re-hashed where load-bearing —
  target `9b17d952`, converter full
  `32904418a169941c2afa1c9cd6866c55debc64f3`, test file `14c9d17e`
  (CLEAN, 95 `def test`, `sha1`/`_shape_token` 0), lib-schema
  `bed9d071` (CLEAN), family artifacts `cf16088b`/`7533c0cf`/
  `b901d083` — ALL character-identical. Connected files judged at
  HEAD per the dirt note (8/8 dirt pairs match my re-derivation).

#### (j) Differences (2 — both evidence-precision, neither structural)

- W2-C1: C1 + matrix axis 3 say "three call sites" for
  `generated_input_type_name` — there are FOUR (`:838`, `:938`,
  `:1105`, `:1692`). The `:938` site (`describe_serializer_input`'s
  canonical-name recompute) also follows a suffix change. Definition
  count (0 here, 1 owner) STANDS; consumer-count erratum only.
- W2-C2: R-opvocab + C23 say the `== PARTIAL` bipartition appears
  "thrice (rows 43, 46, 61)" — it appears FOUR times (rows 43, 46,
  49, 61: `:840`, `:940`, `:1107`, `:1679`) plus the row-54
  derivation (`:1310`). Row 49 (`serializer_input_type_name`) was
  missed. The route STANDS (a fourth bipartition strengthens, not
  weakens, the asymmetry census); verdict unaffected.

No other differences. My probe initially undercounted the `replace(`
stamps (single-line substring vs the `:1380` multi-line call) — an
instrument defect in MY probe, repaired (now counts `replace(` lines),
final `ALL OK (26 checks)`; W1's "two stamps" claim was correct throughout.

#### (k) Contract gates

- Zero-edit: item diff is the new untracked artifact only; no
  production/test/doc edit; no oracle rewritten; no `pragma: no cover`.
- Citations: `path::Symbol` form throughout; `:NNN` pins appear only in
  this DRY artifact (permitted scratchpad form); no symbol rename, no
  sweep owed.
- Provenance words: `sweep`/`restored`/`hardening`/`previously`/
  `grader`/`feedback` 0; `plan` 1 ("edits the plan" — the DRY plan
  document); `audit` 3 (production-wrapper behavior, "materializer
  audits"); `worker` 14 (all DRY.md-mandated `Worker 0/1/2` role
  references). No violation.
- Link scaffold: all 10 canonical group headers present with one
  bottom definitions block.
- Ruff: the item touched no `.py` (artifact is `.md`) — no ruff run
  owed for the item. My one created probe
  (`docs/dry/temp-tests/dry-file-rest_framework__inputs-w2/census.py`,
  4 KB) passes scoped `ruff check` + `ruff format --check` (iterated
  `--fix`+format per AGENTS.md until both green) and runs
  `ALL OK (26 checks)` read-only. No source-mutating proof was needed
  (static-decidable throughout); no disposable workspace built.
- `## Defects` (Worker 2): none — no new defect found; nothing to append.

#### (l) Verdict

`verified`. Zero-edit; 64/64 + 13/13 homed; 1 new family (FAM-SRC,
count 2 tested hard from both directions + package-wide sweep), 12
file-local (incl. the lawful clear-lifecycle convergence), 5 adopted
convergences transcribing nothing, 14 rejections (2 converge + 11
fresh + 1 correctly routed to the maintainer); no defects; no pending execution.
HEAD `5ee86193` at finish (unmoved throughout). Scratch kept small at
`docs/dry/temp-tests/dry-file-rest_framework__inputs-w2/` (one 4 KB
probe, ruff-clean, green) for Worker-0 explicit-path removal.
