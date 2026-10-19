# DRY review: `write-relation-id-typing`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `write-relation-id-typing`. Provisional owner
[model-inputs][model-inputs]`::relation_id_scalar` (+
`::relation_id_annotation`) — CONFIRMED, not inherited. Known member
files [model-inputs][model-inputs], [form-inputs][form-inputs],
[serializer-converter][serializer-converter] complete — package-wide
grep for the spine vocabulary finds production typing bodies in exactly
those files (remainder below under Enumeration). Prior records only as
triggers: the mutations/forms file items (both nominate this family as
N1; every call-site claim below re-derived from the bodies, nothing
inherited) and the verified `typed-globalid-decode` (the write-side
decode pipeline is confirmed single — verified, not inherited; this
family is its typing-side counterpart). Never read any
`worker-memory/`.

Attribution: the plan's `## Owned changes` ledger holds no row on any
family path (full read of `dry-0_0_15.md`: rows cover only
`optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`, `registry.py`,
`relay.py`, `list_field.py`, `types/relay.py`, `types/finalizer.py`,
`types/resolvers.py`, `utils/relations.py`, `types/base.py`,
`management/commands/inspect_django_type.py`,
`tests/management/test_inspect_django_type.py`,
`tests/types/test_resolvers.py`, `tests/utils/test_errors.py`) —
confirmed by full read. `mutations/inputs.py` +
`rest_framework/serializer_converter.py` are clean vs both HEAD and
`ITEM_BASELINE` (`d58ac9b377be19143fcfccde1fad6d112048b448`,
verified present via `git cat-file -t`). `forms/inputs.py` carries
EXTERNAL concurrent dirt: the diff vs HEAD is the `_form_field_basis`
guarded-`isinstance` hunk only (+16/-2, comment + per-value loop),
with zero overlap against any typing site
(`_model_less_relation_annotation`, `_field_triple_and_spec`,
callers of `annotate_queryset_relation` /
`model_column_input_annotation`) — verified by hunk positions. No
dirty path was edited, so no STOP arose; reading the dirty file was
free.

## System trace

Rule: how a relation id is TYPED in a generated mutation input —
which GraphQL scalar a relation field maps to, and how cardinality,
naming, nullability, and the related-primary lookup color it per
write flavor (model / form / serializer).

The owner spine ([model-inputs][model-inputs]):

- `::relation_id_scalar` — the one id-type decision: `relay.GlobalID`
  when the related model's primary `DjangoType` is Relay-Node-shaped
  (`implements_relay_node`); otherwise the related model's raw pk
  scalar via `scalar_for_field(related_model._meta.pk)`. No third
  form: there is no model-label annotation — model labels
  (app-label strings in the GlobalID wire payload) are a decode-side
  concern of the `typed-globalid-decode` pipeline, never an input
  annotation (zero `get_model`/label hits in the typing path).
- `::relation_id_annotation` — cardinality wrap around the scalar:
  `list[id]` iff many, else bare `id`. Naming stays at each flavor.
- `::annotate_queryset_relation` — column-less spine: resolve the
  related model from `queryset.model` (fail-loud via the flavor's
  `missing`), apply the flavor's `primary_of`, package
  `relation_id_annotation` with the related model for the reverse
  map. Queryset discovery, missing-wording, primary policy, and
  naming stay at each flavor.
- `::relation_input_annotation` / `::model_column_write_annotation` /
  `::model_column_input_annotation` — model-backed assembly over the
  same spine (sibling families `column-less-relation-typing`,
  `model-column-write-classification`,
  `model-column-write-annotation` own the adjacent rules; this family
  owns only the id scalar inside them).

Exact typing rule per flavor (all through the spine, verified at
each call site):

- Model (`build_mutation_input` via `model_column_input_annotation`):
  forward FK/O2O -> `<field>_id: GlobalID | <pk-scalar>`; M2M ->
  `<name>: list[...]`. Primary lookup `registry.get` (missing ->
  raw-pk fallback). Nullability via the shared
  `optional_input_field` tail: create honors `input_field_required`
  (default/null/blank rule), M2M always optional, partial forces
  every field optional.
- Form (`_field_triple_and_spec`): backing-column arm via
  `model_column_input_annotation` (`registry.get` fallback);
  column-less arm via `_model_less_relation_annotation` over
  `annotate_queryset_relation` (`registry.get` fallback;
  `field.queryset`, `None` -> typed `ConfigurationError`). Same
  `<name>_id` / `name` naming. Nullability via the same tail with
  the shared `form_field_required` decision; partial forces
  model-backed fields optional while column-less extras keep their
  declared requiredness.
- Serializer (`resolve_serializer_field`): model-backed arm via
  `model_column_write_annotation` with
  `primary_of=_require_relation_primary` (missing primary ->
  `ConfigurationError`, stricter than the model/form fallback by
  documented spec-039 policy); column-less arm via
  `serializer_only_relation_annotation` over
  `annotate_queryset_relation` (same strict lookup;
  `field.queryset` / `child_relation.queryset`). Naming via the
  id-like-suffix rule (`serializer_field_graphql_name`: declared
  `category_id` kept, bare `category` -> `category_id`, multi keeps
  the plain name). Nullability via the same tail: required from
  `field.required` minus `optional_fields` (create) / all-`False`
  (partial), widened when `allow_null` or optional.

Both converter tables carry relation kinds with `annotation=None`
(form `converter.py` `_CONVERT_RELATION_*`, serializer
`_CONVERT_RELATION_*`): kind-only flags finalized at the build
sites above. Zero second id-typing bodies package-wide.

Consumers (listed, not counted): `mutations/sets.py`
`::_expected_input_attr_names` (passes `related_primary_type=None`;
naming only — the docstring states the id type is irrelevant to the
python attr) and `::_validate_relation_override_types` (reads the
emitted annotation via `relation_input_annotation` +
`_annotation_core_is_global_id`; composes the owner by name, peels
its output rather than re-deriving Relay-vs-pk). Parallel readers of
`implements_relay_node` (filter GlobalID leaves, finalizer strategy
audit, `payload_object_slot` naming) answer different contracts —
listed under Matrix 1, not counted.

Lifetime (principle 4): no stored derivation — pure per-call
annotation construction at schema build (`static-reviewed` over all
three build walks: no cache, memo, or index on the id type; the
bind caches shapes, never the scalar decision). Validity key = the
registry store lifecycle (`registry.get` reads live at finalize);
`clear()` rebuilds re-read. Mutation = store lifecycles only.

Connected sources read: [model-inputs][model-inputs] (whole file),
[form-inputs][form-inputs] (whole file),
[serializer-converter][serializer-converter] (whole file),
[serializer-inputs][serializer-inputs] (build walk + nullability +
shape identity), [mutation-sets][mutation-sets] (override
naming/shape-lock consumers), [form-converter][form-converter]
(kind-only relation rows), [relay-types][relay-types]
(`implements_relay_node`), [scalar-table][scalar-table]
(`scalar_for_field`), oracles at all four test modules below.
Excluded on strength of body: every other package module (zero
rule vocabulary over the whole-package sweep; filter/finalizer
`implements_relay_node` hits opened and classified as parallel
readers).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Model, form, and serializer
   relation annotations all ride `relation_id_scalar` (def census:
   1); column-less paths all ride `annotate_queryset_relation`
   (1 def; both flavors import the same object — pinned by the
   standing `is`-identity oracle). Flavor deltas are primary
   policy (fallback vs raise), naming (`<name>_id` vs
   id-like-suffix), nullability axis, and queryset discovery —
   each with per-site contract prose. Trigger: a flavor typing a
   relation id without the spine.
2. **Sync/async twins.** Typing is sync annotation construction at
   schema build; no `async` twin exists and none is owed.
   Trigger: an async twin of the input builders.
3. **Derived rather than repeated knowledge.** The id scalar
   derives once per call at the owner; no caller re-checks
   Relay-vs-pk (`implements_relay_node` census: exactly one
   write-typing call site) or re-reads `related_model._meta.pk`.
   A pk-scalar change moves `SCALAR_MAP` only (C1). Trigger: a
   second Relay-vs-pk branch on the write path.
4. **Inverse / round-trip pairs.** Typing (this family) vs decode
   (`typed-globalid-decode`: `decode_model_global_id` +
   `_resolve_real_pk`) share the GlobalID-vs-raw-pk contract in
   opposite directions; neither re-spells the other (typing never
   parses, decode never annotates). Oracles pin both sides.
5. **Contracts restated in another medium.** Production (spine +
   adapters); oracles (independent literals — `is relay.GlobalID`
   / `is int` / `== list[...]` over locally built Relay and
   non-Relay targets, never reading the owner body — plus the one
   `is`-identity import pin, classified honestly below);
   projections (each adapter's docstring states its delta:
   serializer strictness, form fallback, naming rules).
6. **Enforcement by omission.** Every write relation id on all
   three flavors funnels through the spine (census below); no
   member lacks the typing its contract requires. The raw-pk
   fallback on model/form for unregistered primaries is the
   documented contract (not a gap); the serializer's raise is its
   own documented contract. No defect.

### Enumeration

Instrument: whole-package grep for `relation_id_scalar |
relation_id_annotation | annotate_queryset_relation |
serializer_only_relation_annotation | _model_less_relation_annotation |
_require_relation_primary | model_column_write_annotation` (56
matches, each classified) + `implements_relay_node` census +
`to_field|target_field|_GLOBALID_RELATION_PK_ATTR` zero-hit proof
over the four write-input files. Population: 117 `.py` (plan
count; no adds/renames).

| # | Site | Role |
|---|---|---|
| 1 | [model-inputs][model-inputs]`::relation_id_scalar` (1 def) | definition (id-type rule) |
| 2 | [model-inputs][model-inputs]`::relation_id_annotation` (1 def) | definition (cardinality wrap) |
| 3 | [model-inputs][model-inputs]`::annotate_queryset_relation` (1 def) | definition (column-less spine) |
| 4 | [model-inputs][model-inputs]`::relation_input_annotation` / `::model_column_write_annotation` (1 def each) | consumers of 1–2 (model-backed assembly; sibling families own naming/classification) |
| 5 | [form-inputs][form-inputs]`::_model_less_relation_annotation` (1 def) | consumer (calls 3 by name; owns naming + missing-wording + fallback) |
| 6 | [serializer-converter][serializer-converter]`::serializer_only_relation_annotation` (1 def) | consumer (calls 3 by name; owns naming + missing-wording + strict lookup) |
| 7 | [serializer-converter][serializer-converter]`::_require_relation_primary` (1 def) | adapter (strict primary policy; flavor-local by contract) |
| 8 | [serializer-converter][serializer-converter]`::resolve_serializer_field` relation arms | consumers (call owner's column/column-less entries by name) |
| 9 | [mutation-sets][mutation-sets] naming/shape-lock readers | consumers (read owner's output by name; listed, not counted) |
| 10 | Filter/finalizer/payload `implements_relay_node` readers | parallel readers, different contracts (listed, not counted) |
| 11 | Oracles: [test-model-inputs][test-model-inputs] owner-unit + build rows, [test-form-inputs][test-form-inputs] column-backed + column-less rows, [test-serializer-inputs][test-serializer-inputs] + [test-serializer-converter][test-serializer-converter] relation rows (21 executed, below) | oracles |
| 12 | Adapter docstrings at 5/6/7 + spine docstrings | projections (verified against bodies) |

### Challenges

Counts are authoritative definitions only; adapters, oracles,
projections listed, never counted. Workspace proofs map onto
P0–P1 (21-test selection `execution-verified` in the copy and in
the shared tree; control below `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New relation kind needing a different id scalar (new DRF `RelatedField` subclass; new Django relation shape) | **1** (`relation_id_scalar`; kind *detection* is the sibling families' — converter prechecks / `model_column_write_kind` — listed, not counted). All three flavors follow by name. |
| C2 | Relay-vs-non-Relay policy change (e.g. id scalar no longer keys on the primary's Node shape) | **1** (the `implements_relay_node` arm in `relation_id_scalar`; the single write-typing call site per the census). |
| C3 | `to_field` relation — does the TYPING change with the target column? | **0** — typing never consults the target column: the scalar is always `related_model._meta.pk`-based (or `GlobalID`); zero `to_field`/`target_field` hits in all four write-input files. Non-pk NodeIDs are handled at DECODE (`_resolve_real_pk`), never at typing. |
| C4 | The pk-marker family just confirmed filter-side column logic — does write-side TYPING consult the same marker or re-derive? | **0** — zero `_GLOBALID_RELATION_PK_ATTR` / marker-reader hits in the write path. Different populations by construction (predicate-column derivation vs annotation construction); the marker trigger ("a marker read in the write pipeline") is confirmed unfired. |

**Experiments (executed, disposable workspace).** Copy per [dry][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --frozen --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/write-relation-id-typing
uv run --frozen --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --frozen --directory "$WS" pytest <21-test selection> --no-cov -n0 -q
```

- P0 (positive): 21 passed in the copy; 21 passed shared-tree
  (the one authorized focused run, zero member edits in flight):
  owner-unit rows (scalar iff-Relay, list wrap, queryset spine),
  the `is`-identity import pin, model build rows (FK/O2O/M2M ×
  Relay/non-Relay/`Meta.interfaces`), form column-backed +
  column-less rows, serializer column-less + strictness +
  naming + cardinality-mismatch rows. Copy `__file__`:
  `.../dry-ws/write-relation-id-typing/django_strawberry_framework/__init__.py`;
  DB `NAME` resolved from inside `$WS`:
  `.../dry-ws/write-relation-id-typing/examples/fakeshop/db.sqlite3`
  (the copy's own tree and database). No source mutation in the
  proof.
- P1 (negative control: behavior-preserving hand copy bypassing
  the owner — `_model_less_relation_annotation` rerouted through
  a local byte-identical scalar + spine copy, WS copy only):
  21 passed, including the `is`-identity import pin (the module
  attribute binding is untouched; only the call path reroutes).
  Standing oracles cannot pin call-unity: sharing rests on the
  def census + the identity pin, never on behavior. Recorded as
  the proved reason for deferring a structural gate, not as
  oracle cover.

## Findings

### F1 — write relation-id typing (CONFIRMED single-owned: no consolidation owed)

- **Contract + variation.** A write-input relation types as
  `relay.GlobalID` iff the related primary is Relay-Node-shaped,
  else the related pk scalar; `list[...]` iff many. Varies on:
  primary-source policy (fallback vs raise), naming
  (`<name>_id` vs id-like-suffix), nullability axis
  (requiredness source + `allow_null`), queryset discovery.
  Never varies on: model labels (no such annotation form),
  `to_field` target column (C3: 0), pk-marker state (C4: 0).
- **Sites + roles.** Definitions 1–3 (1 def each, all at the
  provisional owner); model-backed assembly + both flavor
  adapters compose by name (Enumeration rows 4–9); consumers /
  oracles / projections as listed.
- **Challenges.** C1 → 1; C2 → 1; C3 → 0; C4 → 0. Count > 1
  nowhere in one rule.
- **Owner + lifetime (principles 7, 4).**
  [model-inputs][model-inputs]`::relation_id_scalar` (+
  `::relation_id_annotation` / `::annotate_queryset_relation`)
  stands: the Relay-vs-pk decision is write-input-specific (the
  read side never types relation ids this way; the filter side
  types GlobalID *filter* leaves under its own contract); every
  flavor already depends on it without reversing a dependency
  (form and serializer import the owner — a sibling flavor
  module, never a child — and the owner imports neither);
  the scalar/cardinality/queryset-model triple is meaningless
  outside this contract, so splitting it would orphan the
  pieces. Stored-derivation lifetime: not cached (see System
  trace).
- **Migration.** None — both flavors already compose the spine
  by name at HEAD (imports present at HEAD, pre-`ITEM_BASELINE`;
  item-scoped diff on all member paths is empty). Zero
  production edits.
- **Distinct behavior (stays separate).** Per-flavor primary
  policy (serializer raise vs model/form fallback — spec-039
  policy difference, each recorded at its own docstring);
  naming rules (`relation_input_annotation` triple vs
  id-like-suffix dedupe); nullability sources
  (`input_field_required` vs `form_field_required` vs
  `field.required`/`optional_fields` + `allow_null`); queryset
  discovery (`field.queryset` vs `child_relation.queryset`);
  `mutations/sets.py` naming-only (`None` primary) vs
  shape-lock (live primary) reads. Triggers: a flavor typing a
  relation id without the spine (T-bypass); a third annotation
  form beside GlobalID/raw-pk (T-form); a marker or
  `to_field` read in the typing path (T-column, confirms
  C3/C4 still 0). Durable homes: this finding + the
  per-adapter docstrings (already present — no projection edit
  owed).
- **Behavioral proof.** `execution-verified` for the typing
  rule on all three flavors, the fallback/strict split, naming,
  and the column-less sharing (WS 21 passed + authorized
  shared-tree 21 passed, zero member edits in flight).
  `static-reviewed` for the def/call censuses, the zero-hit
  `to_field`/marker proofs, oracle-body independence (local
  Relay/non-Relay targets + literals), and the adapter prose.
  Control P1 rejects "a gate could pin unity".
- **Structural gate.** Deferred with proved reason: P1 shows a
  correct hand copy passes every standing oracle including the
  `is`-identity pin, so unity is pinnable only by a bespoke
  AST/name-cardinality shape — forbidden per [dry][dry]
  ("never a bespoke existence test per helper"). Same standard
  as the verified decode, pk-marker, name-decode,
  definition-store, enum-cache, and subscription-masking items.
  Coverage that stays: the owner-unit rows (fail a lost arm),
  the per-flavor Relay/non-Relay build rows, the strictness
  raise rows, the cardinality-mismatch row, the `is`-identity
  import pin.
- **Coupling.** None. Zero production edits; nothing to land
  together. Adjacent open families (`column-less-relation-typing`,
  `model-column-write-classification`,
  `model-column-write-annotation`) untouched.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `mutations/inputs.py` `fc442047…` (== HEAD, == baseline),
  `rest_framework/serializer_converter.py` `32904418…` (==
  HEAD, == baseline), `forms/inputs.py` `436fcf42…` (vs HEAD
  `55614839…`: external `_form_field_basis` hunk only, typing
  lines untouched), `rest_framework/inputs.py` `9b17d952…`
  (clean), `mutations/sets.py` `936f5ae7…`,
  `forms/converter.py` `b717fd0f…`, `types/relay.py`
  `c333c785…`, `types/converters.py` `9ceb34af…`,
  `utils/inputs.py` `ee31d360…`,
  `tests/mutations/test_inputs.py` `6be1b081…`,
  `tests/forms/test_inputs.py` `33d40193…`,
  `tests/rest_framework/test_inputs.py` `14c9d17e…`,
  `tests/rest_framework/test_converter.py` `9d5d0eaf…`.
  `HEAD` `bfaee91d`; `ITEM_BASELINE` `d58ac9b3…` (member-path
  diff empty). Searched population: whole package (117 `.py`)
  for the rule tokens. Any fingerprint change reopens the
  finding.
- **Reconsideration triggers (recorded here).** T-bypass fires
  if a write relation id bypasses the spine; T-form fires on a
  third annotation form; T-column fires on a marker/`to_field`
  read in the typing path.

## Defects

None filed. Considered and released with reason (not dropped):
the model/form raw-pk fallback for unregistered primaries beside
the serializer raise is a documented spec-039 policy split both
docstrings state — per axis 6 an intentional separation with
triggers above, not a defect (no contract source extends the
raise to model/form). The `mutations/sets.py` shape-lock leaving
raw-pk relations alone is likewise documented at its docstring
(no visibility contract to defeat). No `to_field` typing gap:
no contract source requires target-column-sensitive write
annotations, and the decode backstop (`_resolve_real_pk`) is the
owned adjacent behavior.

## Pending execution

None. Every proof is `execution-verified` above (workspace
`__file__` + DB `NAME` recorded; the shared-tree run was the
single authorized focused test). No `execution-deferred` items.
`FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: typing is annotation construction at schema
build — no database, alias, or dialect decision (every executed
claim is class/enum/dict work; the oracles run on the default
test database). Full-suite gate business is deferred to the
final-gate item with reason: the entry authorizes workspace runs
plus one focused `--no-cov` test, and a green unmutated suite
would discharge no failability proof for a confirmation that
proposes no gate.

## Judgment

Write-side relation-id typing is already one rule: one scalar
decision (`relation_id_scalar`), one cardinality wrap, one
column-less spine, composed by name on all three flavors, with
per-flavor adapters (primary policy, naming, nullability,
queryset discovery) carrying documented contract differences.
Challenges count 1/1/0/0; lifetime stated; separations carry
triggers; no defect meets the bar. Zero production edits;
artifact only.

## Implementation (Worker 1)

Tracked changes: this artifact only (new file, untracked until
Worker 0 records it). Item-scoped diff vs `ITEM_BASELINE`
`d58ac9b3…` on all member paths plus this artifact path is empty
for the members (`git diff <baseline> --` the four write-input
paths prints nothing); the `forms/inputs.py` worktree-vs-HEAD
hunk predates-or-equals the baseline window and is external
concurrent dirt, attributed by content, untouched.
`## Owned changes` ledger confirms nothing on any family path.
No dirty path edited → no STOP arose. No `CHANGELOG.md` touch;
no commit.

Hygiene: `grep -c truncated` == 0 (shared tree). Ruff: touched
paths are `.md`-only (outside ruff's corpus);
`python3 scripts/check_trailing_commas.py --check` on this
artifact (below). No pytest after edits (the only shared-tree
run is the pre-artifact authorized focused test, 21 passed).

Scratch paths (removal is Worker 0's, after `verified`, by
explicit path): `WS`
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/write-relation-id-typing`
(left on disk holding its own `.venv` + the P1-mutated WS-only
`forms/inputs.py`; the shared tree was never mutated).

Worker 0 rows (exact): tick Family `write-relation-id-typing`
(`docs/dry/dry-0_0_15.md` responsibility row + `## Families`
list) as verified, Run `0.0.15 2026-09-19-1`, CONFIRMED
single-owned, zero production edits, no pending execution; no
`## Owned changes` row (no tracked edit landed); home nothing
(zero defects).

## Independent verification (Worker 2)

Own trace recorded from the bodies before reading `## Findings`
(plan item Family `write-relation-id-typing`, Run `0.0.15
2026-09-19-1`, provisional owner
[model-inputs][model-inputs]`::relation_id_scalar`; HEAD `bfaee91d`;
`ITEM_BASELINE` `d58ac9b3…` present; current `92def2b3…`
present; never read any `worker-memory/`).

Rule per flavor (all through the spine, confirmed at each call
site): the write-input relation id is `relay.GlobalID` iff the
related primary `DjangoType` is Relay-Node-shaped, else the
related pk scalar; `list[…]` iff many.

- Model ([model-inputs][model-inputs]`::build_mutation_input` via
  `::model_column_input_annotation`): FK/O2O -> `<field>_id`,
  M2M -> plain name; primary lookup `registry.get` with raw-pk
  fallback; nullability via `utils/inputs.py::optional_input_field`
  over `::input_field_required` (M2M always optional, partial
  all-optional).
- Form ([form-inputs][form-inputs]`::_field_triple_and_spec`):
  backing-column arm via `::model_column_input_annotation`
  (`registry.get` fallback); column-less arm via
  `::_model_less_relation_annotation` over
  `::annotate_queryset_relation` (`registry.get` fallback,
  `field.queryset`, missing -> typed `ConfigurationError`); same
  `<name>_id` / plain naming; nullability over
  `converter.py::form_field_required` (partial: model-backed
  forced optional, column-less extras keep declared).
- Serializer
  ([serializer-converter][serializer-converter]`::resolve_serializer_field`):
  model-backed arm via `::model_column_write_annotation` with
  `primary_of=::_require_relation_primary` (missing primary ->
  `ConfigurationError`); column-less arm via
  `::serializer_only_relation_annotation` over
  `::annotate_queryset_relation` (same strict lookup,
  `field.queryset` / `child_relation.queryset`); naming via
  `::serializer_field_graphql_name` (id-like-suffix dedupe);
  nullability from `field.required` / `optional_fields` +
  `allow_null` via the same `optional_input_field` tail.

Every annotation-computing site (def census via whole-package
grep, each opened): [model-inputs][model-inputs]`::relation_id_scalar`
(1 def), `::relation_id_annotation` (1 def),
`::annotate_queryset_relation` (1 def),
`::relation_input_annotation` (1 def),
`::model_column_write_annotation` (1 def),
`::model_column_input_annotation` (1 def);
[form-inputs][form-inputs]`::_model_less_relation_annotation` (1
def, calls `::annotate_queryset_relation` by name);
[serializer-converter][serializer-converter]`::serializer_only_relation_annotation`
(1 def, calls `::annotate_queryset_relation` by name),
`::_require_relation_primary` (1 def, strict policy only),
`::resolve_serializer_field` (1 def, both arms call the owner
entries by name). Model-backed assembly, both adapters, and both
`resolve_serializer_field` arms compose the spine by name; no
site re-derives Relay-vs-pk or `related_model._meta.pk`.

Second-bodies sweep (Worker 2 own): form
[form-converter][form-converter]`::convert_form_field` relation
prechecks emit kind-only conversions via
`utils/converters.py::make_kind_converter` (default
`annotation=None`); serializer
[serializer-converter][serializer-converter]`::convert_serializer_field`
relation prechecks do the same (`_CONVERT_RELATION_*` carry
`annotation=None`, finalized at the build sites). Zero second
id-typing bodies package-wide. Adapters compute nothing beside
the spine: naming, missing-wording, primary policy, and
queryset discovery only.

Owner I would choose:
[model-inputs][model-inputs]`::relation_id_scalar` (+
`::relation_id_annotation` / `::annotate_queryset_relation`).
The Relay-vs-pk decision is write-input-specific (read never
types relation ids this way; filter GlobalID leaves answer a
different contract); every flavor already depends on it without
reversing a dependency (form and serializer import the owner,
the owner imports neither); the scalar/cardinality/queryset
triple is meaningless outside this contract. Pure per-call
construction at schema build, no stored derivation. Agree with
the artifact owner (principle 7; principle 4 lifetime as
stated).

Enumeration (member-by-member against own count): rows 1-3
definitions (1 each, agree); rows 4-8 consumers/adapters by
name (agree — verified imports and call sites, including the
`is`-identity import pin); row 9
[mutation-sets][mutation-sets] naming/shape-lock readers consume
output by name (agree — `None` primary for naming only,
live primary for the shape-lock, peels owner output); row 10
filter/finalizer/payload `implements_relay_node` hits are
parallel readers under different contracts (agree — opened and
classified); row 11 oracles are independent literals plus the
one honestly-classified `is`-identity pin (agree); row 12
projections verified against bodies (agree).

Matrix: axis 1 cross-flavor mirroring discharged (three
flavors all ride the spine; deltas below); axis 2 sync/async
inapplicable by construction (sync schema-build annotation, no
await boundary — judged correct); axis 3 derived knowledge
single-sited (one Relay-vs-pk arm, one pk read — agree);
axis 4 round-trip pair correctly split (typing never parses,
`typed-globalid-decode` never annotates — agree); axis 5
media correctly classified (production / oracles /
projections; the `is` pin honestly marked as pin, not
behavior — agree); axis 6 omission discharged (every write
relation id funnels through the spine; raw-pk fallback and
serializer raise are documented contracts, not gaps — agree).

C3/C4 zeros challenged (Worker 2 re-derivation):
`relay.py::_resolve_real_pk` + the annotation for a `to_field`
relation opened. Annotation is column-independent
(`related_model._meta.pk`-based or `GlobalID`; zero
`to_field`/`target_field` hits in the four write-input files,
reconfirmed). Decode yields the same pk (`decode_model_global_id`
-> `_resolve_real_pk` NodeID-attr -> pk -> `pk__in`
visibility; assignment as `<field>_id` pk). Annotation and
decode AGREE (both pk-centric): typing `GlobalID` names the
row, decode resolves the NodeID column to the pk. CORRECT, not
a gap. A `ForeignKey(to_field=…)` stores the `to_field` value
rather than the pk, but no contract source requires
target-column-sensitive write annotations, no fakeshop fixture
carries such a relation, and any residual write-column question
would belong to the decode/write pipeline (adjacent behavior),
not to this typing rule. C3 count 0 stands. C4 marker consult
0 stands: zero `_GLOBALID_RELATION_PK_ATTR` hits in the write
path (reconfirmed); filter predicate-column derivation vs
annotation construction are different populations; trigger
unfired. C1 -> 1 and C2 -> 1 reconfirmed (kind detection and
the single Relay-vs-pk arm).

Separations judged genuinely per-flavor: strict-vs-fallback
primary (serializer raise vs model/form fallback is spec-039
policy, each docstring states its own reason); naming
(`<name>_id` vs id-like-suffix dedupe handles the serializer
`source`/declared-name axis the model never has); nullability
(`input_field_required` vs `form_field_required` vs
`field.required`/`optional_fields` + `allow_null` track
Django-model vs Django-form vs DRF requiredness); queryset
discovery (`field.queryset` vs `child_relation.queryset`
tracks the two APIs). Each carries its own change reason and
trigger; none is a shared decision in flavor clothes. No
model-label annotation form (reconfirmed zero hits).

Gate judged: P1 negative control (hand copy passes all 21
including the `is` pin) proves unity is pinnable only by a
bespoke AST/name shape, forbidden per [dry][dry]. Deferral
holds the same bar as the verified decode, pk-marker,
name-decode, definition-store, enum-cache, and
subscription-masking items. Standing cover (owner-unit rows,
per-flavor Relay/non-Relay builds, strictness raises,
cardinality-mismatch row, `is` pin) stays.

Freshness re-hashed (Worker 2 `git hash-object` now):
[model-inputs][model-inputs] `fc442047…` (== HEAD, == W1),
[serializer-converter][serializer-converter] `95568390…`
(drifted from W1 `32904418…`: concurrent `_safe_type_name`
wording + scalar `ListField` `allow_null` + choice
`allow_blank` hunks, zero overlap with any typing site —
preserved, untouched),
[form-inputs][form-inputs] `436fcf42…` (W1 external
`_form_field_basis` hunk, typing lines untouched —
preserved), [serializer-inputs][serializer-inputs]
`9b17d952…` (== W1), [mutation-sets][mutation-sets]
`936f5ae7…` (== W1),
[form-converter][form-converter] `b717fd0f…` (== W1),
[relay-types][relay-types] `c333c785…` (== W1),
[scalar-table][scalar-table] `9ceb34af…` (== W1),
`utils/inputs.py` `ee31d360…` (== W1),
[test-model-inputs][test-model-inputs] `6be1b081…` (== W1),
[test-form-inputs][test-form-inputs] `33d40193…` (== W1),
[test-serializer-inputs][test-serializer-inputs]
`14c9d17e…` (== W1),
[test-serializer-converter][test-serializer-converter]
`b12dde99…` (drifted from W1 `9d5d0eaf…`: concurrent +116
companion rows, zero overlap with the P0 21). HEAD
`bfaee91d`; `ITEM_BASELINE` `d58ac9b3…`; current
`92def2b3…`. Item-owned tracked edits: zero. The
`forms/inputs.py` hunk predates the baseline window; the
`serializer-converter` + test hunks landed after the current
baseline as concurrent work (attributed by hunk position,
typing sites untouched). Searched population: whole package
for the rule tokens. Any further fingerprint change reopens.

`## Pending execution` judged: none owed. All proofs remain
`execution-verified` as recorded (WS `__file__` + DB `NAME`
bound; shared-tree focused 21 passed with zero member edits
in flight at that time). The post-proof concurrent hunks add
no new proof obligation for this confirmation (zero overlap).
`FAKESHOP_SHARDED=1` / Postgres `inapplicable by
construction` stands (annotation construction reaches no
database, alias, or dialect decision — judged correct).
Full-suite gate stays with the final-gate item.

AGENTS.md prose on the diff: touched paths are this artifact
only (`.md`-only, outside ruff corpus);
`uv run ruff format --check` + `uv run ruff check` pass;
`scripts/check_trailing_commas.py` excludes this path by
design; citations are `path::Symbol` via the link block (no
raw `path:NN`); no process provenance; oracles stay at
`tests/` (pure annotation construction, strongest tier for
this rule); no `CHANGELOG.md` touch; concurrent dirt
preserved; no commit.

Defects: none new (Worker 2). The fallback/raise split,
raw-pk leniency, and shape-lock raw-pk skip remain
documented policy separations, not defects. C3 agreement
above is not a defect.

Reconciliation per point: definitions 1/1/1 — agree;
spine composition by name — agree; `mutations/sets.py`
readers — agree; parallel `implements_relay_node` readers —
agree; converter `annotation=None` zero second bodies —
agree; C1 1 / C2 1 / C3 0 / C4 0 — agree (C3/C4
independently re-derived above); owner + pure per-call
lifetime — agree; CONFIRMED single-owned, no consolidation —
agree; per-flavor deltas as triggered separations — agree; no
model-label form — agree; no defects — agree; no pending
execution with deferred gate + inapplicable cells — agree;
zero item-owned tracked edits with external dirt zero-overlap
— agree (with the one update: `serializer-converter` +
test companions drifted after W1, same zero-overlap
verdict).

Judgment: the rule is single-owned at the spine, composed by
name on all flavors, separations triggered, proofs
`execution-verified`, gate deferral proved. `Status:
verified`, no `## Owned changes` row, home nothing.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[form-converter]: ../../django_strawberry_framework/forms/converter.py
[form-inputs]: ../../django_strawberry_framework/forms/inputs.py
[model-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutation-sets]: ../../django_strawberry_framework/mutations/sets.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[scalar-table]: ../../django_strawberry_framework/types/converters.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[serializer-inputs]: ../../django_strawberry_framework/rest_framework/inputs.py

<!-- tests/ -->
[test-form-inputs]: ../../tests/forms/test_inputs.py
[test-model-inputs]: ../../tests/mutations/test_inputs.py
[test-serializer-converter]: ../../tests/rest_framework/test_converter.py
[test-serializer-inputs]: ../../tests/rest_framework/test_inputs.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
