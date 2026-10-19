# DRY review: `serializer-reverse-map-reopen`

Status: verified
Run: 0.0.15 2026-10-12-29

## System trace

The cited `_build_reverse_map` names zero bytes in the package and in
specs 036-040 (killed `7517eab2`); only cycle scratch still mentions it.
Its row's question is re-posed on current bytes: the write-flavor
spec-build trio over the shared `InputFieldSpec` spine. Spec
construction sites package-wide are exactly four: model
`mutations/inputs.py::mutation_input_field_specs` (:719, reverse walk
over the generated input via `::_relation_field_index`); serializer
`rest_framework/serializer_converter.py::resolve_serializer_field`
(:1377, leaf) + `rest_framework/inputs.py::_resolve_nested_field`
(:1541, nested recursion); form
`forms/inputs.py::_field_triple_and_spec` (:601, per-field forward).
The spine they compose: `utils/inputs.py::InputFieldSpec` (record),
`mutations/inputs.py::model_column_write_kind` (classifier),
`::model_column_write_annotation` /
`::model_column_input_annotation` / `::annotate_queryset_relation`
(annotation builders), `FieldConversionBase` + converter skeleton,
`::make_input_namespace`, `::iter_input_field_collisions`,
`::optional_input_field`, the cache pair + stash tail
(`mutations/sets.py::cached_build_input` /
`::build_and_stash_input`), and
`utils/write_values.py::decode_provided_fields` (request-time
`spec_by_attr`, the single reverse-map construction). Auth `register`
composes the model seam (`mutation_input_shape` + `build_mutation_input`
+ `mutation_input_field_specs` with `excluded_attrs`) — a fourth
consumer, not a fourth builder. Fences honored: e8 seeds untouched,
f36 guard read-only, decode trio left to its item,
`GeneratedInputFieldSpec` excluded (read-side set-family record).

## Verification

### Matrix

1. Cross-flavor: the trio + spine + auth consumer traced whole-package; no fifth builder.
2. Sync/async: zero `async`/`await` in the five spec-build modules; bind-time sync, no I/O. N/A.
3. Derived-twice: 036 one-expression applications (R1, below bar); `graphql_camel_name` single-owned.
4. Halves: model forward+reverse share one owner (standing); form/serializer co-build triple+spec.
5. Media: oracles spell wire names literally; specs 036-040 describe current shape; no dead cite in specs.
6. Omission: per-flavor axes are cache-contract separations (R5); every policy scoped by its contract. No gap.

### Challenges

C1 new field kind: classifier 1 def; converter tables per flavor (disjoint key spaces); handlers ride the decode item. Count 1.
C2 new relation shape: cardinality policies 1 def each (column-shape+M2M-optional vs declared-wins+PK-only+mismatch vs queryset-derived); 036 suffix applications 1 def + 2 one-expression sites (R1). Count 1 logic definition.
C3 new write flavor: nine shared primitives composed by name; the new build function is the adapter. No new driver pays.
C4 renamed spec key: 1 dataclass + 4 construction sites (flavor-specific axes each); a factory is the constructor with extra steps. Count 1 grammar.

## Findings

### F1: the trio is shared spine plus per-flavor adapters, not one grammar (REJECT)

Contract: per generated input field, build the reverse-map record decoding it to a flavor write target; varies on source vocabulary (model column / form field / serializer field), naming, requiredness, column resolution, and descriptor needs. Definitions: the four construction sites plus the spine owners named above. Consumers: three flavor binds (`_input_field_specs` stash), three decodes, error-key maps, agreement guards, `resolve_injected_field_specs` (composes the leaf by name), and the fenced `related_visibility_queryset` use (`rest_framework/resolvers.py::` scope body — composes the owner directly for its None arm, pin+lock without visibility, one site). Oracles: the four flavor test files (own literal expectations; composition pins bind object identity). Projections: specs 036-040 plus owner docstrings. Challenges C1-C4: every plausible change moves at most one logic-carrying definition. No move: spine stays in `utils/inputs.py` + `mutations/inputs.py` beside its first consumer; builders stay in flavor modules (flavors import the spine, never a sibling). Stash lifetime: class-creation bind, per-mutation-class immutable list, read at request decode, replaced on re-bind, cleared with subsystem reset.
Contract difference: walk directions differ (model reverse over generated input vs form/serializer forward over declared fields), key spaces differ (model attr / form name / declared+source), policies differ (required-primary, PK-only, cardinality, M2M-optional, aggregate-vs-fail-first, cache keys). A unified driver is dispatch plus adapters — barred machinery. No drift: wire names pinned identically across flavors, suites green. Trigger: a fourth spec-building flavor sharing branch-level logic with an existing builder beyond the nine spine primitives — then extract that branch, not a driver. Separations already recorded at each owner (cited per R-row) — no prose edit owed.
Behavioral proof: model oracles 80/80 plus form/serializer oracles 320/320 re-run green (execution-verified); standing pins and live write coverage static-reviewed. Negative control: none — construction-time code, no bypass threat.

### R1: 036-scheme consumer spellings (REJECTED, below bar)

`relation_input_python_attr` (ModelField-keyed, 1 def) plus two one-expression applications on `(name, many)` inputs the owner cannot take: form `forms/inputs.py:498` and serializer `serializer_converter.py:676` (with the serializer-only id-like-suffix dedupe). A scheme rename is implausible (frozen spec-036 wire surface; consumer input classes must follow it) and neither application carries logic (single-expression precedent). Trigger: a third application, the scheme gaining branches, or spellings diverging — then extract a `(name, many)` kernel under the owner and compose all three.

### R2: column-resolution postures (REJECTED)

Serializer `backing_model_field` (source-keyed, non-forward supported via the cardinality override) vs form `_model_column_for` (name-keyed, forward-only, rest falls to model-less) vs model index-first with reverse/fallback failing loud at bind. Three contracts, each documented at its site; the shared `get_field`-None micro-idiom is below bar. Trigger: two flavors adopting one posture.

### R3: requiredness decisions (REJECTED)

Model `input_field_required` + M2M-always-optional vs form `form_field_required(field, column)` (NullBoolean forced optional) vs serializer `field.required` minus `optional_fields`. Different inputs, different contracts; create/partial widening rides the shared `optional_input_field` at each caller. Trigger: two flavors reading one requiredness input.

### R4: input-naming rules (REJECTED)

036 `<name>_id` (model + form) vs id-like-suffix from the declared name (serializer, spec-039 Decision 7). Intentional, recorded at `serializer_field_graphql_name` and `annotate_queryset_relation` ("naming stays at each flavor"). Trigger: the serializer dropping the declared-name rule.

### R5: per-flavor axes on the shared record (REJECTED)

`annotation_repr`/`required` ride the serializer post-build descriptor key; the form keys pre-build on basis content identity; the model keys on `(model, operation, fields)` — each total, each documented (`cached_build_input`, the walk, the shape builders). `EXCLUDED` is model-only (spec-040 D6), `NESTED_*` serializer-only (nested writes are DRF-only), `related_model` is recorded from each flavor's own id-type basis (documented per site). The shared record already carries the axes as optional — a flavor needing one fills it. Trigger: a second flavor filling an axis — fill the field and pin the behavior.

## Defects

D1 (prose-only, no contract impact, unfixed — out of scope for a zero-edit consolidation item): `resolve_serializer_field` docstring states the GraphQL-name-from-declared-name sentence twice verbatim; `InputFieldSpec` docstring reads "so the the decode recurses". Owners: the two docstrings.

D2 (Worker-2) nit, non-blocking, scratchpad-local: F1 cites the fenced consumer as ``rest_framework/resolvers.py::`` (empty symbol). Repair: ``rest_framework/resolvers.py::_scope_specs_over_serializer`` (enclosing def verified; the `related_visibility_queryset` use composes the owner by name). Site identified, verdict unaffected — recorded, not revision-needed.

## Pending execution

None. All proofs executed (80 shared-tree + 320 copy). Sharded/PG cells inapplicable by construction: spec-build is bind-time code over `_meta`/field maps with no query, alias, or dialect decision; oracles ran default in-memory sqlite.

## Judgment

Zero-edit reject: the spine is already one-owned nine times over and the trio's builders are per-flavor adapters with distinct contracts. The dead cite is superseded by F1; R1-R5 carry triggers. No ledger row, no spec sentence touched.

## What shrinks

Rule: write-flavor reverse-map spec build (model + serializer + form over `InputFieldSpec`). Change: none — one-grammar consolidation rejected (F1); five sub-rules rejected with triggers (R1-R5). Owner before/after: unchanged — spine in `utils/inputs.py` + `mutations/inputs.py`, builders in flavor modules, fenced consumer composing `related_visibility_queryset` by name.
Net lines: 0 package, 0 tests, 0 specs. Machinery attestation: no new helper, wrapper, constant, driver, or edit of any kind — the live tree carries only this artifact.
Attribution: no source path touched, so no ledger/hunk attribution owed; the workspace copy was never written (read-only trace plus test executions).
Freshness (HEAD `c37a08a0`, ITEM_BASELINE `5cc1dbcd`): `mutations/inputs.py` `5e99a667`, `forms/inputs.py` `df1df485`, `serializer_converter.py` `ec8feaad`, `rest_framework/inputs.py` `edf5f0c2`, `utils/inputs.py` `0fae4a0e`, `utils/write_values.py` `947325a4`, `rest_framework/resolvers.py` `274610bf`, `mutations/sets.py` `6f2fa2f9`, `tests/mutations/test_inputs.py` `e19514e0`, `tests/forms/test_inputs.py` `6ad94ea1`, `tests/rest_framework/test_converter.py` `f450459e`, `tests/rest_framework/test_inputs.py` `a0177083`, spec-036 `22926ba8`, spec-037 `2ed196ff`, spec-038 `58c2581f`, spec-039 `29f54d5f`, spec-040 `0a821df6`; population 118 tracked package files (+3 untracked, covered by working-tree grep); contract sources spec-036 Decisions 6-7 + spec-037 + spec-038 Decision 7 + spec-039 Decision 7 + spec-040 D6; focused runs 80/80 shared-tree (`heavy uv run pytest tests/mutations/test_inputs.py --no-cov -n0 -q`) + 320/320 copy (`heavy uv run python scripts/workspace.py run dry/serializer-reverse-map-reopen/consolidate -- pytest tests/forms/test_inputs.py tests/rest_framework/test_converter.py tests/rest_framework/test_inputs.py --no-cov -n0 -q`).
Index rows for Worker-0: `serializer-reverse-map-reopen` → rejected (F1 trigger: fourth flavor sharing branch logic beyond the spine); `write-spec-build-spine` → consolidated CONFIRM (nine primitives + fenced consumer, no edit); `model-forward-reverse-halves` → consolidated CONFIRM (standing owner + co-build halves need none); `write-036-scheme-consumer-spellings` → rejected (R1 trigger); `write-column-resolution-postures` → rejected (R2 trigger); `write-flavor-requiredness` → rejected (R3 trigger); `write-input-naming-rules` → rejected (R4 trigger); `write-spec-per-flavor-axes` → rejected (R5 trigger). The dead-cite rows (`build-reverse-map-vs-mutation-input-reverse-map`, `nested-structure-walk-unification`) are superseded by this verdict — retirement is the plan's call.

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

## Independent verification (Worker-2)

### Own trace (recorded before reading `## Findings`; only headers + this tail anchor sighted)

Method: full read of the four spec-build sites, the spine, and the decode consumers;
`InputFieldSpec(` census; `_build_reverse_map` grep over the live package; diff state.

Sites + roles (mine). Four builders, four definitions:

- DEFINITION `django_strawberry_framework/mutations/inputs.py::mutation_input_field_specs`
  — model builder, REVERSE direction (built input class + model -> specs via
  `_relation_field_index` + `_meta.get_field`); total-coverage walk, fail-loud on an
  unresolvable attr; owns the `EXCLUDED` capture seam.
- DEFINITION `django_strawberry_framework/forms/inputs.py::_field_triple_and_spec`
  — form builder, FORWARD (per form field -> triple + spec); column arm composes
  `model_column_input_annotation`, column-less arm composes `convert_form_field` +
  `_model_less_relation_annotation`; `target_name` is the declared form name.
- DEFINITION `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`
  — serializer builder, FORWARD + `source` axis; model-backed arm composes
  `model_column_write_kind` / `model_column_write_annotation` + the type-override
  conflict policy; column-less arm composes `convert_serializer_field` +
  `serializer_only_relation_annotation`; primary-required policy; id-like-suffix naming.
- DEFINITION `django_strawberry_framework/rest_framework/inputs.py::_resolve_nested_field`
  — nested builder, RECURSIVE (nested input via `build_serializer_input_class`,
  records `nested_specs`); DRF-only by construction.
- DEFINITION (spine, each single-owned): `utils/inputs.py::InputFieldSpec`; the kind
  vocabulary (`SCALAR` / `RELATION_SINGLE` / `RELATION_MULTI` / `FILE`, flavor
  extensions `NESTED_*` / `EXCLUDED` at their flavors); `model_column_write_kind`,
  `model_column_write_annotation`, `model_column_input_annotation`,
  `relation_id_scalar` + `relation_id_annotation`, `relation_input_python_attr`,
  `relation_input_annotation`, `annotate_queryset_relation` (all
  `mutations/inputs.py`); `utils/write_values.py::decode_provided_fields` (+
  `decode_field_handlers`, `scalar_into` / `relation_into` / `file_into` /
  `decoded_into`); `utils/inputs.py::optional_input_field` +
  `::iter_input_field_collisions`; `utils/relations.py::is_forward_many_to_many` +
  `::is_forward_concrete_relation`; `normalize_serializer_source` /
  `require_one_segment_source` (serializer_converter).
- CONSUMER: `mutations/sets.py` + `auth/mutations.py` bind calls (model builder);
  `forms/inputs.py::build_form_input_class`,
  `rest_framework/inputs.py::_walk_serializer_fields` +
  `::resolve_injected_field_specs` (compose builders by name);
  `mutations/resolvers.py` + `forms/resolvers.py` + `rest_framework/resolvers.py`
  decode calls (via `decode_provided_fields`);
  `rest_framework/resolvers.py` `related_visibility_queryset` use (in-fence, pure
  consumer of the `utils/querysets.py` owner).
- ORACLE: existing behavior suites (W1's executed proofs judged below).
- PROJECTION: per-builder docstrings incl. the "analog of" cross-clauses; plan rows.

Definition counts per posited change (mine):

- P1 new `InputFieldSpec` axis -> 1 (the record); per-flavor population only where
  the axis applies. P2 column-kind reclassification -> 1
  (`model_column_write_kind`; all builders compose). P3 `<name>_id` core-scheme
  rename -> 3 spellings (`relation_input_python_attr`, the form column-less
  inline, the `serializer_field_graphql_name` arm) — the CLOSEST pair; my verdict:
  below bar (key domains differ — ModelField vs free declared-name strings; the
  serializer dedupe arms stay regardless; the shared token is one f-string, not
  real logic at each site; extraction = a new cross-module helper = machinery).
  P4 decode-dispatch change -> 1 (`decode_provided_fields`; its inline
  `spec_by_attr` dict is its single site, not a second reverse-map owner). P5
  id-typing change -> 1 (`relation_id_scalar`; wrap + flavors compose). P6 M2M
  screening change -> 1 per predicate (`utils/relations.py` owners; callers
  compose). P7 model-rider-via-`decode_field_handlers` -> not an obligation (the
  rider's FILE/M2M/EXCLUDED policies replace every default; forcing it through
  the factory needs a new scalar-decode seam = machinery). P8 nested/form new
  capability -> single-flavor by construction. P9 source-axis change -> 1
  (`normalize_serializer_source`; nested + column paths compose). P10
  collision-policy change -> N/A (three deliberately different contracts:
  form raise-first, serializer aggregate, model audit; prior rejections stand).

Owner I would choose: none new. The spine stays where owned; the 4 builders stay
at their flavor modules (they key on flavor-private field objects — ModelField
vs forms.Field vs DRFField — so any shared driver needs mode flags). Zero-edit
accept iff every rejected pair carries contract difference + trigger.

Matrix (mine): axis 1 = this trace (the item IS the cross-flavor question).
Axis 2 inapplicable (build is bind-time pure; the decode loop is sync-shared; no
twin). Axis 3 clean (`related_model` / `target_name` recorded once per builder,
never re-derived; injected specs compose by name). Axis 4 = this family (forward
triple vs reverse decode; the model arm runs reversed by construction). Axis 5 =
docstring projections + oracles (D1 judged below). Axis 6 enumerated (4
builders; nested `related_model=None` is correct omission — a nested field has
no column target; every column-relation arm records its model).

Independent consolidation search: `InputFieldSpec(` census = exactly the 4
builders (plus read-family `GeneratedInputFieldSpec`, out of population);
`_build_reverse_map` = 0 bytes in the live package (only the
`docs/shadow/current/` snapshot + `docs/dry/temp-tests/` scratch, outside the
population); the `spec_by_attr` dict = one inline site in
`decode_provided_fields`. No candidate found — zero-edit stands on my trace too.

### Reconciliation (read after recording the above)

- Builders: agree 4/4, same sites; auth register = consumer (verified
  `excluded_attrs=_REGISTER_EXCLUDED_INPUT_FIELDS` at its bind). No difference.
- Spine count: W1's "nine" is a grouping, not the whole spine. Verified
  single-owned beyond the nine: the kind vocabulary,
  `relation_id_scalar`/`relation_id_annotation`, `relation_input_python_attr`
  (named in R1), `relation_input_annotation`,
  `is_forward_many_to_many`/`is_forward_concrete_relation`,
  `normalize_serializer_source`/`require_one_segment_source`. Verified as named:
  `FieldConversionBase`, `make_input_namespace`,
  `cached_build_input`/`build_and_stash_input`, `iter_input_field_collisions`,
  `optional_input_field`. The union is all single-owned — strengthens the
  reject; verdict unchanged.
- R1 = my P3 (same pair, same below-bar call, compatible trigger). R2-R5: each
  contract claim re-verified at its body (`backing_model_field` source-keyed
  with no forward gate; the `form_field_required` NullBoolean rule; the
  serializer dedupe arms; the descriptor-key split — `annotation_repr`
  post-build vs basis-identity pre-build vs `(model, operation, fields)`;
  `EXCLUDED`/`NESTED_*` flavor-only; `related_model` from each flavor's own
  basis). Triggers carried on all five. No difference.
- C1-C4 compatible with my P1-P10 (every plausible change moves at most one
  logic-carrying definition; collision policies = prior rejections). Owner:
  agree, none new. No difference.
- Matrix: axis 2 zero-`async`/`await` re-grepped clean; axis 5 no dead cite in
  specs re-grepped clean and oracles literal (spot:
  `graphql_name == "categoryId"`); axis 6 nested `related_model=None` is
  correct omission (no column target), consistent with R5. No difference.
- D1: both typos confirmed at their docstrings; prose-only,
  unfixed-out-of-scope, homing owed — sound, non-blocking. No difference.
- Pending execution: none + sharded/PG inapplicable-by-construction (bind-time
  `_meta`/field-map code, no query/alias/dialect) — reason judged sound.
- Failability: no `prove_failability` manifest, none owed — a zero-edit reject
  consolidates nothing, so no equivalence proof exists to fail; the oracles
  carry literal expectations that fail on a wrong result (run-29 bar met). No
  `proof:`/`gate:` entries remain.

### Checks

- Scoped diff: package empty — the artifact is the only change (untracked);
  17/17 freshness hashes match live bytes, so no item edit and no concurrent
  drift on the touched surface. Population 118 tracked `.py` + 3 untracked
  re-counted exact. HEAD `c37a08a0` unmoved.
- Proofs re-executed: shared-tree `tests/mutations/test_inputs.py` 80/80 (this
  pass's one allowed run) + own verify-copy `tests/forms/test_inputs.py` +
  `tests/rest_framework/test_converter.py` + `tests/rest_framework/test_inputs.py`
  320/320 (`dry-20261012T143622-a55f1b`, exit 0). Tier `tests/` = mandated for
  package targets. Behavioral, literal expectations.
- AGENTS.md prose: no process provenance; `path::Symbol` form throughout (plus
  `:NNN`, permitted in `dry-*.md` scratchpads); no tests owed (no code);
  artifact 93 lines + What shrinks, under cap. `ruff check` + `ruff format
  --check` exit 0 (N/A for `.md`); scaffold check clean, 10 canonical headers
  present.
- One (Worker-2) prose nit filed under `## Defects` (dangling `::`, concrete
  repair named); de minimis — site identified, verdict unaffected,
  scratchpad-local; not revision-needed.

### Verdict

`verified`. Zero-edit reject stands on both traces; every rejection carries
contract difference + trigger; D1 homes as prose-only.
