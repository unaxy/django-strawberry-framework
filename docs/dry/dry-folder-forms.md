# DRY review: `forms/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Verdict: zero-edit CONFIRM. 32 folder-local rules single-owned
(FL-1..FL-5); 13 cross-boundary compositions hold (FC-1..FC-13);
14 merges rejected with triggers (FR-1..FR-14); 4 tree-falsified
prior assignments flagged for the closeout defect-homing pass
(FF-1..FF-4, no row reopened, nothing re-applied); the one
pre-rowed open family touching this folder
(`mutation-discovery-own-snapshot-read`) confirmed still
blocked-on-hunt with zero edits. 0 consolidations, 0 defects.

## Pins and fingerprints

HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=f5880c40c6f4f8455f11c871db502834b9d71d8b` (before copy in
warm slot-1). Blob fingerprints are `git hash-object` (WT),
`git show HEAD:<path> | git hash-object --stdin` (HEAD),
`git show ITEM_BASELINE:<path> | git hash-object --stdin` (BASE),
short-8, re-verified after the last read:

| File | WT | HEAD | BASE | Lines WT/HEAD |
|---|---|---|---|---|
| `forms/__init__.py` | `cfd550b2` | `cfd550b2` | `cfd550b2` | 30/30 |
| `forms/converter.py` | `52b10986` | `a70fe126` | `52b10986` | 301/301 |
| `forms/inputs.py` | `df1df485` | `1b38e890` | `df1df485` | 897/950 |
| `forms/resolvers.py` | `ad4abc7b` | `ad4abc7b` | `ad4abc7b` | 676/676 |
| `forms/sets.py` | `6681c33c` | `946701af` | `6681c33c` | 1210/1182 |

BASE equals WT on all five folder files, so the item-scoped diff
(`ITEM_BASELINE` to WT) is empty: this item landed zero tracked
edits and names zero `## Owned changes` rows. `git status --short`
count 526 at dispatch, unchanged by this item (plus this new
untracked artifact). Connected owners and oracles fingerprinted
(WT/HEAD, short-8): root `b688e2fa`/`b688e2fa` (clean),
`mutations/sets.py` `6f2fa2f9`/`a123aea8`,
`mutations/inputs.py` `bb329e4d`/`f821661e`,
`mutations/resolvers.py` `9171b93f`/`bb6c630d`,
`rest_framework/inputs.py` `0e2638fd`/`b7f4a6ba`,
`rest_framework/resolvers.py` `4d05a330`/`14ffc9c8`,
`rest_framework/serializer_converter.py` `077a4ee2`/`e804b074`,
`rest_framework/sets.py` `d3a16114`/`2ecaab56`,
`utils/inputs.py` `0b8d3daa`/`c199eaa4`,
`utils/converters.py` `53ce2b2e`/`eb0f708d`,
`utils/write_values.py` `1dc426d4`/`a9d6fa32`,
`utils/errors.py` `e9572ea9`/`9cf4e952`,
`utils/strings.py` `0b1774a7`/`1a49fe42`,
`utils/relations.py` `cc68c6ba`/`63f46750`,
`utils/querysets.py` `e6660894`/`4d8a3d39`,
`utils/write_transaction.py` `50909be8`/`2b9f861c`,
`types/converters.py` `d8905d0a`/`38f102ab`,
`scalars.py` `072432e6`/`5837c6dc`,
`registry.py` `c5aa2050`/`47b52c52`,
`tests/forms/test_converter.py` `17cf3658`/`024fb6e2`,
`tests/forms/test_inputs.py` `6ad94ea1`/`3f2931ea`,
`tests/forms/test_resolvers.py` `ff318d4b`/`101fbfe8`,
`tests/forms/test_sets.py` `4270e6ad`/`fca5d0b6`,
`tests/mutations/test_resolvers.py` `4d9a03cc`/`9dd13c73`,
family artifact `dry-rule-mutation-discovery-own-snapshot-read.md`
`14782e58`.

## System trace

The folder owns the form-mutation write side end to end:
`converter.py` (model-less `forms.Field` table + kind prechecks +
requiredness + fallthrough), `inputs.py` (form-derived input
generation + basis + projection + guards + namespace),
`resolvers.py` (form-keyed decode + partial reconstruction + shared
write steps + flavor dispatch + entries), `sets.py` (two `Meta`
matrices + ledgers + metaclass + build cache + hook machinery +
bind), `__init__.py` (2-name leaf manifest + module-map prose).
Data flows declaration (`Meta` validate + register) to bind
(effective set to input class + reverse-map stash + materialize)
to resolve (locate to authorize to form-keyed decode to
construct/validate-once to write to payload). Every cross-folder
seam (namespace mechanics, narrowing/naming/collision/guard
spines, column spine, converter skeleton, kind vocabulary,
write skeleton + entries + boundary + recourse, visibility chain,
decode spine, error/success mappers, permission walk, declaration
mechanics, seal source, camel grammar, relation predicates,
clear bus) is owned outside and composed by name; the folder owns
no cross-folder definition.

Member-file inputs re-derived at current bytes, never inherited:
[file-init][file-init], [file-converter][file-converter],
[file-inputs][file-inputs], [file-resolvers][file-resolvers],
[file-sets][file-sets]. Where the tree falsified an assignment the
record sits under Findings as FF (flag for closeout; no row
reopened, nothing re-applied). The Responsibility index holds no
row with a `File forms/*` holding item: all 32 folder-local rules
below are unassigned remainder, named as new rows for Worker-0.
Cross-boundary rows holding folder members were checked at
current bytes; convergences and rejections stand except where
flagged FF.

### Attribution of the working-tree dirt (by diff content vs HEAD)

- `forms/converter.py` (WT `52b10986` vs HEAD `a70fe126`):
3 hunk headers, all truth migration (`_safe_*` to `truth.kind` /
`truth.render` + import + docstring line). Concurrent work,
untouched.
- `forms/inputs.py` (WT `df1df485` vs HEAD `1b38e890`):
32 hunk headers, all truth migration (`truth.name` /
`truth.static_attr` / `truth.is_instance` / `truth.text` /
`truth.kind` / `truth.render` + import) plus hostile-guard and
`except BaseException` arm deletions (53 net lines removed).
Concurrent work, untouched.
- `forms/sets.py` (WT `6681c33c` vs HEAD `946701af`):
20 hunk headers, all truth migration (`truth.class_dict` /
`truth.static_attr` / `truth.name` / `truth.is_subclass` /
`truth.is_exact` + `_ABSENT` sentinel + `hasattr`/`isinstance`
retargets) plus the WT-only `_require_zero_arg_form_fields_declaration`
insertion and `except BaseException` arm deletions (28 net lines
added). Concurrent work, untouched.
- `forms/__init__.py`, `forms/resolvers.py`: clean (WT = HEAD).
- No `## Owned changes` row covers any folder file; the folder
carries no item-owned edits. Every consolidation-shaped edit
considered here either dissolves on the merits (FR) or would
touch the hunks above (blocked; only the pre-rowed family
qualifies, and it stays rowed with its block confirmed).

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched, twins read at current
bytes. Converter tables are 4 key spaces with 4 contracts
(26/1/12/16, pairwise disjoint by prefix, re-derived P2;
FR-1). Namespaces split light trio (forms/mutations/serializer,
3-tuple each) vs heavy quartet (filters/orders, 4-tuple each)
with 20 disjoint clear owners (FC-1). Recourse is 1 template +
3 nouns (FC-2); entries are 1 factory + 3 bodies (FC-3);
visibility is 1 chain with per-flavor rides (FC-4); seal is 1
source with 2 instances (FC-5); ledgers/caches are disjoint
stores over shared mechanics (FC-6/FC-7); error/save mapping is
shared leaves with 1 deliberate serializer fork (FC-9). Guards,
partials, decodes, matrices, and namespaces each differ by
documented contract (FR-7..FR-11). Discharged.
2. Sync/async twins: discharged inapplicable by construction.
Instrument (P1, AST walk): zero `AsyncFunctionDef`, zero `await`
in all five folder files. The async surface is the shared
factory product running the one sync body through the shared
boundary (FC-3); no second pipeline exists to drift.
`perform_mutate` / `check_permission` are sync-only seams the
boundary wraps.
3. Derived rather than repeated knowledge: every same-token
population in the folder was walked on body strength at WT
bytes. Single definitions with by-name consumers: `FORM` +
`CREATE_SHAPED_KINDS` (1 + vocab checks), `form_field_required`
(1 def + 5 calls), `convert_form_field` (1 + 1 production call),
`InputFieldSpec(` (exactly 1 construction, inputs.py:601),
`INPUTS_MODULE_PATH` (1 pin), `_ABSENT` (1 sentinel),
`== PARTIAL` (4 decision sites over 1 vocabulary, FR-12),
`get_form_kwargs` stubs (identical pair required by the
two-hierarchy design, FR-13), `form_class` key spelling
(spelled at use, FR-14), `pipeline_write_phase()` (2
enforcement sites of 1 rule per the DRY.md vocabulary,
FC-3), `save_or_field_errors` (1 + 2), `Input`/`PartialInput`
names (1 spine + wrappers). No fact re-derived. Discharged.
4. Inverse / round-trip pairs: encode (field to spec, single
construction) pairs with decode (spec to form-keyed payload via
`target_name`/`kind`/`related_model`, read never rebuilt);
`FILE` to `files=` pairs with construction (serializer lands
in `data`, deliberate contrast, verified at rest_framework
prose + `spec.kind == FILE` arm); name pairs with bind
materialize name (seam purity pinned by
`test_input_type_name_seams`); narrow pairs with drop-detection
(guard per declaration before cache lookup, pinned by
`test_cached_build_form_input_runs_required_guard_per_declaration`);
declare pairs with bind (drain + stash). One grammar per pair,
correctly separated halves. Discharged.
5. Contracts restated in another medium: counted 1 definition
per rule; everything else classified. Contract sources:
spec-038 Decisions 4-8/10/11/13 (layout, vocabulary, guards,
matrices, bind, pipeline). Oracles: `tests/forms/*` rows spell
literals (scalar parametrize, MRO rows, kind flags, basis
rows, triple/id-type rows, guard rows, collision row, matrix
rejects, waiver rows, ledger-split rows, dedupe rows, decode
rows, pipeline rows) plus `tests/mutations/test_resolvers.py`
factory gate; none iterates an owner table. Projections:
module docstrings (clause-verified incl. MRO claims against
the 12-key table + precheck order), leaf map prose, TREE rows,
glossary entries. No medium holds an independently maintained
copy. Discharged.
6. Enforcement by omission: family enumerated per rule against
contract sources. Kind coverage total (`SCALAR` /
`RELATION_SINGLE` / `RELATION_MULTI` / `FILE`; `EXCLUDED`
unreachable by construction via `model_column_write_kind`).
Vocabulary coverage total (both builders fail loud out of
vocabulary). Seam coverage per flavor carries its Decision
(`_resolve_model` / `select_for_update` ModelForm-only,
snapshot/bind/auth/hooks/plain-only per Decision 6/8/10/11,
`with_id=False` plain-only). Unsupported fields raise
(GOAL fail-loud, oracle-pinned); excluded fields never convert
(pinned); `queryset is None` fails loud typed (pinned). No
member lacks a guard its contract requires. Discharged.

### Challenges

Authoritative definitions counted only; consumers, oracles, and
projections that move alongside are listed, never counted.
Read-only probes live under `$TMPDIR/dry-folder-forms/`
(`p1_census.py` AST + async census, `p2_tables.py` /
`p2b_prefix.py` table census, plus `rg` censuses quoted below);
all ran green against WT bytes (no package import, no DB).
No shared-tree pytest run (zero-edit item; WT carries hunt WIP
that owns every delta, so a WT suite result would measure the
hunt, not this item; proof rides the named permanent oracles
via the `gate:` entries). No `docs/dry/temp-tests/` scratch
(scratch confined to `$TMPDIR` per the brief).

| Id | Change posited | Definitions forced |
|---|---|---|
| C1 | Map a new forms scalar (e.g. `DurationField` to `str`) | 1 (table; serializer twin disjoint, does not move) |
| C2 | Change one row's scalar (e.g. `UUIDField` to `str`) | 1 (the row) |
| C3 | Change the NullBoolean requiredness rule | 1 (`form_field_required`; 5 call sites follow) |
| C4 | Change the NullBoolean annotation match | 1 (`_null_boolean_converter`) |
| C5 | Route a new forms relation/file class | 1 (precheck list; build finalization follows) |
| C6 | Respell a kind constant | 0 here (owner `utils/inputs.py`; 4 re-exports follow) |
| C7 | Change the `(annotation, kind, required)` shape | 0 here (owner `FieldConversionBase`) |
| C8 | Change the MRO-walk mechanics | 0 here (owner `convert_with_mro`) |
| C9 | Unify all converter tables into one map | refused (FR-1: 26/1/12/16 disjoint key spaces, 4 contracts) |
| C10 | Add/reshape an operation kind | 1 here (sentinel + set + vocab checks; `CREATE`/`PARTIAL` upstream) |
| C11 | Change the basis source or name/value validation | 1 (R2 trio) |
| C12 | Add a 5th shape-identity axis | 1 (R3 projection; cache assembly follows) |
| C13 | Change the narrowing rule | 0 here (spine); knob wording 1 here |
| C14 | Change the suffix/full-vs-narrowed rule | 0 here (spine); `== PARTIAL` decision 1 here |
| C15 | Change the reverse/GFK exclusion | 1 (R5) |
| C16 | Change the id-type rule | 0 here (spine); naming/missing-wording 1 here |
| C17 | Change column routing or the `<name>_id` remap | 1 (R6 dispatch); new field class 0 here (table moves) |
| C18 | Add a third collision arm | 0 here (walk owner); wording/policy 1 here |
| C19 | Change the partial-widening rule | 1 (R8) |
| C20 | Change the drop-detection arithmetic | 0 here; required-set filter 1 here |
| C21 | Add a namespace lifecycle slot | 0 here (bus + trio owners) |
| C22 | Unify form/serializer partial rules | refused (disjoint populations; FR-7/FR-10) |
| C23 | Fold `_simple_triple` into the model scalar arm | refused (FR-11: tuple shapes differ) |
| C24 | Change the empty-value skip | 1 (R1 single + multi move together) |
| C25 | Change the `to_field_name` projection | 1 (R1 helper + both decoders) |
| C26 | Change FILE routing (`files=` vs `data=`) | 1 (R2 `file_dest`) |
| C27 | Change the reconstruction shape | 1 (R3) |
| C28 | Change the form-error mapping | 1 (R4 bridge) |
| C29 | Add a third form base (new dispatch arm) | 1 (R5 branch; skeleton + factory stay) |
| C30 | Change the recourse sentence | 0 here (template); noun 1 here |
| C31 | Change the pipeline order | 0 here (skeleton owner) |
| C32 | Change the visibility query | 0 here (chain owner); projection 1 here (C25) |
| C33 | Unify the three partial-update mechanisms | refused (FR-7: 3 substrates) |
| C34 | Batch the form multi decode onto `pk__in` | refused (FR-8: object need) |
| C35 | Unify null-M2M with the model reject | refused (FR-9: Django form semantics) |
| C36 | Add a form `delete` operation | 1 (R1 matrix; owner widens only if it widens) |
| C37 | Give the plain flavor an operation | 1 (R2 presence-reject + sentinel + bind) |
| C38 | Change a permission default | 1 per flavor (model-backed call vs `DenyAll` default + reject) |
| C39 | Add a ledger lifecycle slot | 0 here (factory + bus); disjointness config 1 here |
| C40 | Add a 5th cache-key axis | 0 here (projection owner); assembly 1 here |
| C41 | Change guard-before-cache ordering | 0 here (owner `cached_build_input`) |
| C42 | Change the waiver rule | 1 (R7; serializer unaffected) |
| C43 | Change a default construction body | 1 (R7 shared default; both flavors follow) |
| C44 | Change the permission walk | 0 here (walk owner); seam presence 1 here |
| C45 | Change the input-name grammar | 0 here (naming owner); kind decision 1 here |
| C46 | Change a `Meta` key set | 1 per set (local arm); foundations 0 here |
| C47 | Reword a seal message | 0 here (factory + record owners) |
| C48 | Unify the twins behind a mode flag | refused (FR-3: every seam forks) |
| C49 | Merge the two matrices into one validator | refused (FR-4: disjoint keys, opposite rules) |
| C50 | Name form inputs via the set-family rule | refused (FR-2: different source domains) |
| C51 | Put write flavors on heavy `_lifecycle` | refused (FR-6: nothing beyond ledgers to reset) |
| C52 | Ride the plain flavor on `DjangoMutation` | refused (FR-5: model-backed base contract) |
| C53 | Expose a 3rd form base | 1 (home definition; leaf + root consumer rows follow) |
| C54 | Rename a base | 1 (home; manifests follow) |
| C55 | Move a base out of `sets.py` | 1 (owner move; one import line follows) |
| C56 | Un-root the pair (leaf stays) | 0 here (root rows move; proves separation) |
| C57 | Change what a sibling module owns | 0 here (stale prose only; proves projection) |
| C58 | Extract the `== PARTIAL` predicate (4 sites) | refused (FR-12: 4 decisions, 1 vocabulary) |
| C59 | Share the `get_form_kwargs` stub via a mixin | refused (FR-13: hierarchy coupling) |
| C60 | Unify the `form_class` key spelling under a constant | refused (FR-14: spelled at use, S1 direction) |
| C61 | Unify the hook-basis diagnostics into one message helper | released (within R2; distinct conditions, no sync contract) |

Probe commands and what each proved (census figures
`execution-verified`; ownership verdicts `static-reviewed` with
named oracles):

- `uv run python $TMPDIR/dry-folder-forms/p1_census.py`: AST
member counts 4/31/40/28/45; 0 async defs, 0 awaits, all five
files (matrix axis 2 + FF-4 delta).
- `uv run python $TMPDIR/dry-folder-forms/p2_tables.py` +
`p2b_prefix.py`: 26/1/12/16 keys; `models.*` / `BigInt` /
`forms.*` / `serializers.*` prefixes pairwise disjoint; no bare
`forms.Field`, no file rows in the form table; `BigAutoField`
to `int` (FR-1).
- `rg make_input_namespace\(|make_set_input_namespace\(`:
light 3-tuple in forms/mutations/serializer, heavy 4-tuple in
filters/orders (FC-1).
- `rg register_subsystem_clear\(` + owner census: 20 owners,
each once; `forms.input_namespace` (with `before_bind=True`),
`forms.declarations`, `forms.shape_cache` exactly once (FC-1).
- `rg sync_pipeline_recourse\(`: 1 def + 3 calls with distinct
nouns (FC-2). `rg make_resolver_entries\(`: 1 def + 3 calls
with own sync bodies (FC-3). `rg make_declaration_registry\(`:
model + plain + auth rides (FC-6).
`rg make_shape_build_cache\(\)`: 3 flavors + def (FC-7).
- 43 `def <helper>` greps: every composed owner present in
exactly one file (FC-8/FC-11/FC-12).
- `rg InputFieldSpec\(` in `forms/`: exactly 1 (inputs.py:601).
`rg form_field_required\(`: 1 def + 5 calls.
`rg convert_form_field\(`: 1 def + 1 production call.
`rg == PARTIAL`: exactly 4 in `forms/` (inputs.py:419/688,
sets.py:335/341) + 1 `!= CREATE` in the model flavor (FR-12).
`rg = object\(\)` in `forms/`: exactly 1 (`_ABSENT`, hunt).
- Twin axes: `_relation_null_error` (mutations 675/689),
`partial=True` + `_merged_serializer_kwargs` (serializer
947/2393), `decode_visible_relation_ids` (write_values:290),
`file_dest=provided_files` (forms:335) vs serializer in-data
routing (prose 367/378 + `spec.kind == FILE` arm 1216),
`_guarded_serializer_write` (serializer:2359) vs
`save_or_field_errors` (mutations:1328, ridden ×2 in forms)
(FR-7..FR-10).
- `diff` of the two `get_form_kwargs` TYPE_CHECKING stubs
(sets.py 766-775 vs 1085-1094): byte-identical (FR-13).
- Oracle existence sweep: all 9 cited gate oracles present at
the pinned test paths (Pending execution).

## Findings

Proof status throughout: `static-reviewed` (zero-edit item;
composition by name verified textually at WT bytes; behavior
pinned by the named permanent oracles, re-run via the `gate:`
entries). Census figures are `execution-verified` (probes
above). Freshness for every finding: the Pins table (all five
folder files in WT/HEAD/BASE) plus the connected-owner/oracle
fingerprints there; per-finding deltas noted inline.

### FC-1 — input-namespace lifecycle (CONFIRM contributor posture)

Light 3-tuple unpacks in forms/mutations/serializer
(inputs.py:139 + twins), heavy 4-tuple in filters/orders;
20 `register_subsystem_clear` owners package-wide, each once;
`forms.input_namespace` (with `before_bind=True`),
`forms.declarations`, `forms.shape_cache` exactly once. The
form wrappers call the owner products only (verified bodies).
New row `forms-input-namespace-row` carries the declaration
(lawful convergence onto the bus family, `serializer-…` shape);
ledger/cache declarations converge via R3/R4 rows. Zero new
sites.

### FC-2 — recourse template + nouns (CONFIRM rejected-family outcome)

1 def (`sync_pipeline_recourse`) + 3 calls with distinct nouns
(`DjangoMutation` / `serializer mutation` / `form mutation`,
forms at resolvers.py:161). The sentence is single-sourced;
the per-flavor named constant stays by design. Existing
`sync-boundary-recourse-wording` row (already lists
`forms/resolvers.py`) stands; zero new sites.

### FC-3 — write skeleton + entries + boundary (CONFIRM rider posture)

1 factory def + 3 calls with own sync bodies (model / form at
resolvers.py:676 / serializer); 1 skeleton def ridden by all;
2 `pipeline_write_phase()` sites in forms are enforcement
sites of the one rule (DRY.md vocabulary), not copies; 0
awaits in the folder. The single-sync-body shape holds at
current bytes. No plan row names this family for forms; the
posture is recorded at the owner module + FC-3 here. Zero new
sites.

### FC-4 — visibility chain (CONFIRM transitive consumer)

Form decoders call `decode_visible_relation` (1 call site),
which calls `visible_related_object`, which opens with the
chain owner (read end to end at WT blobs). The per-element
(not batched) ride is the documented object need
(`to_field_name` projection). Existing
`related-object-visibility-recheck` row (already lists
`forms/resolvers.py`) stands; zero new sites.

### FC-5 — seal source sharing (CONFIRM consumer on both flavors)

1 factory def + 2 instances (model metaclass + plain
metaclass at sets.py:838) over disjoint ledgers; both
flavors snapshot the shared `_ValidatedMutationMeta`
record (11 use sites in sets.py, verified). The plain
metaclass is a second instance sharing the seal source,
not a second seal. No plan row names this share; the auth
mirror row (`auth-sealed-slot-mirror`) records the
mirror-vs-share direction. Zero new sites.

### FC-6 — declaration-ledger disjointness (CONFIRM)

3 rides of `make_declaration_registry` (model/plain/auth)
+ def; plain store read only by its own bind/co-clear and
its tests (1 prose mention of the model ledger, 0 code
reads). The `ModelForm` flavor rides the model registry
with zero local bind code. Zero new sites.

### FC-7 — shape-build caches (CONFIRM disjoint dicts, one factory)

3 pairs (forms/serializer/mutations) + def; guard runs per
declaration before lookup via `cached_build_input`
(sets.py:367); key excludes `guard_required` by design.
Zero new sites.

### FC-8 — column spine delegation (CONFIRM by-name composition)

Column-backed fields route through
`model_column_input_annotation` / `model_column_write_kind`
(inputs.py:566/571) and relation id-types through
`annotate_queryset_relation` (inputs.py:495); each owner
present once (43-def sweep). The symmetric wire contract
(same enum object both sides) rides these calls. Zero new
sites.

### FC-9 — error/success mappers (CONFIRM shared leaves + 1 fork)

Form error bridge calls `validation_error_to_field_errors`
(resolvers.py:473); both write steps call
`save_or_field_errors` (resolvers.py:561/596); serializer
keeps its own `_guarded_serializer_write` (2359) for the
disjoint DRF exception contract. Existing
`errors-flat-django-mapper` / `errors-three-save-mappers`
rows stand; zero new sites.

### FC-10 — kind vocabulary single-source (CONFIRM re-export posture)

4 `as`-form re-exports (converter.py:69-72) address the one
conceptual enum in `utils/inputs.py`; `is`-identity holds
by import-system construction (same module attribute).
Relation/file kinds carry `annotation=None` (verified
`_kind_converter` default + P5-shape call sites). Zero new
sites.

### FC-11 — input-build spines (CONFIRM by-name composition)

Narrowing, naming, guard arithmetic, collision walk,
widening tail, input-class builder, MRO skeleton + value
makers, decode walk + handlers + container guard: every
owner present once, every form call site composes by name
(43-def sweep + per-rule call censuses). Zero new sites.

### FC-12 — grammar + predicates (CONFIRM by-name composition)

`graphql_camel_name` (inputs.py:521/592),
`is_forward_concrete_relation` /
`is_forward_many_to_many` (inputs.py:458-463): owners
once, calls by name. Existing
`strings-camel-forward-grammar` / `utils-relations-column-screens`
rows stand; zero new sites.

### FC-13 — pre-rowed blocked family (CONFIRM block persists)

`mutation-discovery-own-snapshot-read` (open, run
2026-10-01-11) names `forms/sets.py @@ -194,55 +199,78 @@`
+ the serializer hunk as blocked-on-hunt. Re-derived at
current bytes: the forms region is still hunt dirt
(`truth.class_dict` / `truth.static_attr` ×2 /
`truth.name` rewrite + `_require_zero_arg…` insertion +
arm deletions; current WT `6681c33c` vs the family's
`b8643610`, same region, same ownership). Migration stays
specified-not-landed; zero edits; the row stays open with
its block. No new row.

### FL-1 — leaf manifest + map prose (2 rules, single-owned)

- `forms-leaf-manifest`: 2-name surface composed by name
from `sets.py`; `__all__` mirrors in-file (one edit
region). C53/C54/C55 count 1 (home); C56 counts 0 here
(root moves; proves separation). Consumers: leaf lines +
root import/`__all__`. Oracles: explicit-name imports
(`tests/forms/*`, root tuple pin). Gate: dropped binding
fails loud as `ImportError` on every suite run.
- `forms-module-map-prose`: docstring maps 4 modules per
Decisions 4-5. C57 counts 0 here (proves projection).
Owner: each sibling for its contract. Statements verified
against the 31/40/28/45-member bodies at WT.

### FL-2 — converter rules (6 rules, single-owned)

- Scalar table + MRO walk: 12 `forms.*` keys (re-derived,
no bare `Field`, no file rows); C1/C2 count 1. Gate:
scalar parametrize + JSON + float/decimal rows.
- Kind-precheck order: 5 ordered prechecks (relation ×2,
file, multi-choice, exact-type bare); C5 counts 1. Gate:
kind-flag + precheck-subclass rows.
- Fail-loud dispatch: exact-type bare to `str`, custom
subclass raises (message now via `truth.kind`/`truth.render`,
hunt-owned wording on a stable rule). Challenge: registering
a base-`Field` row breaks the raise. Gate:
`test_unknown_custom_field_subclass_raises`.
- Requiredness: 1 def + 5 by-name calls (2 converter +
3 inputs). C3/C4 count 1. Gate: NullBoolean subclass SDL
+ omission rows + column-backed matrix row.
- Value object: subclass + 2 thin factories over the
shared shape (C7/C8 count 0 here). Gate: `annotation is
None` assertions on relation/file rows.
- Kind re-exports: 4 `as`-form re-exports (C6 counts 0
here). New rows 3-8.

### FL-3 — input-substrate rules (10 rules, single-owned)

- Kind vocabulary (`FORM` + `CREATE_SHAPED_KINDS` + 2
vocab checks): C10 counts 1. Gate: out-of-vocabulary rows.
- Basis discovery + validation (3 fns): C11 counts 1
(validation now via `truth.text`/`truth.is_instance`,
hunt-owned spelling on a stable rule). Gate: corruption +
keyword + hostile-name rows. C61 released inside this rule
(2 identical + 1 variant diagnostic, distinct conditions,
no sync contract; trigger: an oracle/spec requiring
byte-identity).
- Shape-identity projection (2 fns): C12 counts 1
(hunt removed the guard wrapper; projection quantities
unchanged). Gate: shared-hook dedupe + stateful-hook
loudness rows.
- Narrowing + naming wrappers (2 fns): C13/C14 count
0-here/1-knob-or-decision. Gate: narrowed-name
determinism + narrowing fail-loud rows.
- Column resolution (1 fn): C15 counts 1 (hunt removed
the corrupted-internals arms; exclusion rule unchanged).
Gate: reverse-relation scalar row.
- Triple dispatch (3 fns, single `InputFieldSpec`
construction at inputs.py:601): C16 counts 0-here/1-wording,
C17 counts 1-routing/0-table. Gate: `categoryId`-under-form-key
+ queryset-`None` rows.
- Collision guard (first-raise policy over the shared
walk): C18 counts 0-here/1-here. Gate: camel-collision row.
- Generator + pair builder (2 fns): C19 counts 1. Gate:
partial-extra-required + one-shot-freeze rows.
- Required-set + guards (3 fns over shared arithmetic):
C20 counts 0-here/1-here. Gate: drop-rejection pair +
model-backed-partial-allowance row.
- Namespace contributor (path + trio + 2 wrappers +
registration): C21 counts 0 here (FC-1). New rows 9-18.

### FL-4 — resolver rules (5 rules, single-owned; file clean)

- Relation decode coloring (skip + projection + per-element
shape over the shared spine): C24/C25 count 1. Gate:
`to_field_name`-preservation + empty/clear rows.
- Kind-split decode (dest split + threading): C26 counts 1.
Gate: split-landing + file-exclusion rows.
- Partial reconstruction (scalar/`to_field_name`/M2M/file
shapes): C27 counts 1. Gate: omitted-M2M-with-`to_field_name`
row.
- Error mapping (`as_data()` bridge over the flat mapper):
C28 counts 1. Gate: envelope-keying rows.
- Shared steps + dispatch (decode step, construct/validate
helper, 2 write steps, `_primary_type` rider): C29 counts
1-branch/0-skeleton. Gate: factory-sharing + skeleton-ride
oracles. New rows 19-23.

### FL-5 — set-surface rules (9 rules, single-owned)

- ModelForm matrix (7 arms over shared validators): C36
counts 1-here for flavor arms. Gate: delete-reject +
plain-Form-redirect rows.
- Plain matrix (presence-reject + targeted gates +
`DenyAll` default + model-permission reject): C37/C38 count
1 here (presence now via `truth.static_attr` + `_ABSENT`,
hunt-owned spelling on a stable rule). Gate:
inherited-operation + `DenyAll`-default rows.
- Ledger + metaclass + bind (2nd disjoint ledger, factory
metaclass instance, plain drain with `object_type=None`):
C39 counts 0-here/1-config. Gate: ledger-split +
abstract-nowhere rows.
- Build cache + guard ordering (pair + 4-component key +
per-declaration guard): C40 counts 0-here/1-assembly, C41
counts 0 here. Gate: guard-per-declaration + stateful-hook
loudness rows.
- Validation helpers (2 wrappers over shared walks):
spine changes 0 here. Gate: unknown-name row.
- Build + name tails (2 tails, flavor args differ): flavor
changes 1 here, tail bodies 0 here. Gate:
`test_input_type_name_seams`.
- Hook machinery (5 stable helpers; WT-only
`_require_zero_arg…` is concurrent work joining this rule
when it lands): C42/C43 count 1 here (invocation now
checks-then-calls with propagation, hunt-owned shape on a
stable contract site). Gate: boundary + waiver rows.
- Key sets + namespace (2 unions + 2 bindings): C46 counts
1-here for the local arm. Gate: known-key rows.
- Plain auth seam + write hook (walk-composing seam +
plain-only hook): walk 0 here, presence 1 here. Gate: seam
+ default-`perform_mutate` rows. New rows 24-32.

### FR-1 — converter-table unification (REJECTED, re-derived fresh)

C9 refused. 26 `models.*` to scalar (+enum layering by
callers, mutable extension hook) vs 1 scalar-type to
definition (registration contract) vs 12 column-less
`forms.*` to annotation + kind (relation/file deferred)
vs 16 `serializers.*` to conversion (nested kinds,
`is_input` parity, consumer hook). Key spaces disjoint,
value spaces disjoint; model-backed columns already
delegate to the read side by name; walks share the
skeleton with separate key spaces. Converges with the
existing `types-converters-table-vs-surface-tables` +
`serializer-table-vs-surface-tables` rows (26/12/16/1
re-derived exact). Trigger: a new surface whose field
population is a subset of an existing table's key space
with identical value contract. Home: each table's header
prose + this record.

### FR-2 — set-family naming merge (REJECTED)

C50 refused. Write inputs derive from a form class +
operation kind over `name_set_input_type_name`, never
from a set class; zero `type_name_for` definitions in
the folder (defscan clean; the 3 hits are the distinct
`_form_input_type_name_for`). Unifying needs a
from-what mode flag. Trigger: write inputs deriving
from set classes. Home: `_form_input_type_name_for`
docstring + this record.

### FR-3 — single base with a mode flag (REJECTED)

C48 refused. Every seam forks on the mode:
metaclass/ledger/bind, operation vocabulary (require vs
reject), permission default (`DjangoModelPermission` vs
`DenyAll` + reject), resolver signature (`with_id` vs
not), snapshot shape (`model` + `select_for_update` vs
`None` + sentinel). A flag saves zero obligations (C36/
C37/C38 each still move one arm) and buys a branch at
every consumer. Trigger: a third flavor sharing one side
of every fork. Home: module docstring two-base split.

### FR-4 — merged `_validate_meta` (REJECTED)

C49 refused. Disjoint key sets, opposite operation rules
(require-membership vs reject-presence), opposite
permission defaults, opposite `ModelForm` gate direction
(require vs redirect-reject). Shared arms already are
shared (R5 helpers + all spine validators). Trigger: an
arm whose rule becomes flavor-independent. Home: both
`_validate_meta` docstrings (disjoint matrices).

### FR-5 — plain flavor on `DjangoMutation` (REJECTED)

C52 refused. The base contract is model-backed
(`_resolve_model`, model-column `build_input`, primary
payload, `DjangoModelPermission` default); a `None`-model
subclass carries every model seam as dead weight plus
`None`-guards while still needing its own ledger,
operation reject, and payload shape. Trigger: a
model-backed behavior the plain flavor must inherit
rather than mirror. Home: plain class docstring
(model-LESS clause).

### FR-6 — heavy `_lifecycle` on write flavors (REJECTED)

C51 refused. Write flavors derive from one declaration's
field set (no BFS graph, no lazy targets, no per-set
expansion cache); zero `_lifecycle` / `traversal` /
`ActiveInput` definitions in the folder (defscan clean).
Nothing to reset beyond ledgers + per-pass caches.
Trigger: a write flavor gaining lazy related-set
expansion. Home: `make_input_namespace` light-clear
docstring.

### FR-7 — partial-mechanism unification (REJECTED)

C33 refused. Three substrates: model `setattr` +
`full_clean(exclude=…)` vs form bound-data reconstruction
(`model_to_dict` + `to_field_name`/M2M arms, full-form
revalidation) vs serializer `partial=True` + framework
merge (`_merged_serializer_kwargs`, verified present).
No shared body; positing one rule here (C22) wrongly
forces required extras optional. Trigger: a write flavor
whose partial path reconstructs dropped fields from a
backing row exactly like the form path. Home: R3/R8
docstrings (reconstruction reason).

### FR-8 — batched multi decode (REJECTED)

C34 refused. Form maps single per element because it
needs the OBJECT for the `to_field_name` projection;
the model/serializer batched `pk__in` compose
(`decode_visible_relation_ids`, verified present) never
materializes objects. Different needs, different rides
of one spine family. Trigger: the form no longer
projecting through `to_field_name`. Home: multi-decoder
docstring + spine docstring.

### FR-9 — null-M2M unification (REJECTED)

C35 refused. Form clears on empty (bound-form Django
semantics: optional clears, required errors via
`is_valid()`); model rejects explicit `null`
(`_relation_null_error`, verified present: "use `[]`,
not `null`"). A bound `ModelForm` follows form
semantics, not the replace-set stance. Trigger: Django
form semantics changing, or the model path adopting
clear-on-empty. Home: multi-decoder docstring.

### FR-10 — guard-merge with the serializer guard (REJECTED)

Drop-detection already is one body
(`guard_dropped_required`, C20 counts 0 here); what
differs is only the required-set derivation (form: no
`waived` set, no injected-field mechanism; serializer:
subtracts `Meta.injected_fields`, verified present with
the hardened contract). Merging threads a `waived` knob
the form path can never fill. Trigger: the form flavor
gaining an injected-field mechanism. Home: the shared
spine docstring (already names the split).

### FR-11 — scalar-naming-pair shared form (REJECTED)

C23 refused. Both arms compose the owned
`graphql_camel_name` (consumers, not definitions); tuple
shapes differ (form carries `kind` as a 4th element;
model classifies via a separate `model_column_write_kind`
call). Unifying couples two build sites to save zero
obligations (C14/C17 each already count at their site).
Trigger: a third naming shape that must stay
byte-identical across both sites. Home: this record.

### FR-12 — `== PARTIAL` predicate extraction (REJECTED, folder-new)

C58 refused. Exactly 4 `== PARTIAL` sites (naming:419,
widening:688, guard:335, build:341; all clean lines) over
the 1 vocabulary (R1 + upstream `CREATE`/`PARTIAL`): 4
decisions (suffix, widening, guard selection, build
routing) with separate reasons to change, keyed on the
validated vocabulary downstream of the fail-loud
boundary. A new kind's posture per decision is 4 separate
design choices; a shared predicate pre-decides all 4 the
same way and couples them. The shared token (`PARTIAL`)
is already single-owned upstream. Trigger: a 4th kind
specified as partial-shaped in all four decisions at
once. Home: this record + R1 vocabulary.

### FR-13 — `get_form_kwargs` stub mixin (REJECTED, folder-new)

C59 refused. The two TYPE_CHECKING stubs are
byte-identical (10 lines, `diff` clean), but each class
must declare the hook by language design (two
intentionally separate hierarchies per FR-3/FR-5); the
`get_form` stubs already diverge by return
(`ModelForm[Any]` vs `BaseForm`) and the resolver
`_FormBuilder` Protocol is a third generic spelling for
its own use-site. A mixin couples the hierarchies to
save one stub sync, against the J1/J5 direction; drift
between stub and default is visible in review (adjacent
`else` bindings name the shared default). Trigger: the
hooks gaining a shared base for another reason, or a
stub-drift bug. Home: the "type checker reads…" comments
+ this record.

### FR-14 — `form_class` key-name constant (REJECTED, folder-new)

C60 refused. The `Meta` key name is spelled at use (2
set arms + `key="form_class"` args + `static_attr`
reads + snapshot fields + consumer declarations) by
language design: a constant breaks the grep census and
relieves no rename obligation (consumers + docs move
regardless). Same direction as the verified
`mutation-snapshot-slot-name` S1 rejection. Trigger: the
key must vary per flavor or be computed at runtime.
Home: this record.

### FF-1 — plan blob pins cite a commit, not blobs (FLAG for closeout)

The five `File forms/*` plan rows each say "target blob
unchanged at `5ee86193`". `5ee86193` is a commit sha
(`test(connection): give the repeated rejection assertion
a name`), not a blob: no byte comparison is possible.
Current WT/HEAD blobs (Pins) differ from every recorded
verification blob (`a76a4f79`/`b717fd0f`/`55614839`/
`4edb984b`/`36ce80b4`). Record-only: closeout re-pins or
drops the pins. No row reopened, nothing re-applied.

### FF-2 — member-count drift since file verification (FLAG for closeout)

P1 re-derived 4/31/40/28/45 top-level statements vs the
file artifacts' 4/28/38/24/36 (HEAD re-derived 4/30/39/28/41).
`__init__.py` 4/4 stands; converter +3 (+2 committed:
`Callable` import + `FormFieldConverter` alias; +1 hunt:
`truth` import); inputs +2 (+1 committed: TYPE_CHECKING
block; +1 hunt: `truth` import; WT 897 vs HEAD 950 vs old
914); resolvers +4 all committed (676 vs old 605); sets +9
(+5 committed; +4 hunt: 2 imports + `_ABSENT` +
`_require_zero_arg…`). The file enumerations do not match
current bytes. Record-only for the closeout defect-homing
pass: no row reopened (the index holds no `File forms/*`
rows to reopen); the 32 new rows below supersede the stale
enumerations.

### FF-3 — routed asymmetry's form-side wrap gone at WT (FLAG for closeout)

`serializer-hook-invocation-typed-wrap` records the
form-side "typed-invocation rule" at
`forms/sets.py::_mutation_form_fields`. At HEAD the hook
call sits in a `try` mapping `BaseException` to
`ConfigurationError`; at WT (hunt hunk `@@ -234,12 +272,2 @@`)
the call is checks-then-call with propagation ("whatever
a well-declared hook raises propagates unchanged"). The
row's form-side description holds at HEAD, is falsified
at WT. Hunt WIP on a routed-to-the maintainer row: no action here,
no reopen; closeout re-grades the asymmetry once the
migration settles.

### FF-4 — sessions-tail row's forms site deleted at WT (FLAG for closeout)

`utils-sessions-exception-tail-spelling` lists
`forms/inputs.py` as a participant (the `type(exc).__name__`
tail in `_form_basis_content_identity`'s `BaseException`
catch). At WT that catch is deleted (hunt hunks
`@@ -358,10 +334,7 @@` + `@@ -369,9 +342,2 @@`):
zero `BaseException` handlers remain in `forms/inputs.py`.
Membership holds at HEAD, is falsified at WT. Hunt WIP:
no action here, no reopen; closeout refreshes the row's
census once the migration settles.

## Defects

None. Four investigated edges released without a defect
(cosmetic or contracted, no contract row broken): the
plain-matrix docstring restates the operation reject in
two bullets (single-docstring restatement); the module
header compresses the sync+async seam pair (per-flavor
sites state it precisely); the unknown-name subject reads
`DjangoFormMutation for …` on the `ModelForm` path too
(pinned oracle wording, no accepted shape changes); the
per-build double basis read degrades to a loud ledger
collision, never a silently wrong shape (R3 contract).
The WT-only hook-behavior deltas (propagation, `_ABSENT`
presence, `_require_zero_arg…`) are concurrent hunt WIP,
observed never filed.

## Pending execution

No `proof:` entries (zero `execution-deferred` proofs;
every finding is `static-reviewed` by kind with
ordering/async pinned by the named pre-existing oracles).
Gate entries for the final gate (re-run as listed; results
bind to the tree state at gate time):

- `gate: uv run python scripts/workspace.py run dry/folder-forms/consolidate -- basedpyright`
- `gate: uv run python scripts/workspace.py run dry/folder-forms/consolidate -- basedpyright -p pyrightconfig.floor.json`
- `gate: uv run python scripts/workspace.py run dry/folder-forms/consolidate -- python scripts/check_truthful_reads.py --check`
- `gate: uv run pytest -n0 tests/forms/test_converter.py -q --no-cov`
- `gate: uv run pytest -n0 tests/forms/test_inputs.py -q --no-cov`
- `gate: uv run pytest -n0 tests/forms/test_resolvers.py -q --no-cov`
- `gate: uv run pytest -n0 tests/forms/test_sets.py -q --no-cov`

Cells: `sharded` and `pg` stay `unverified` (the resolver
pipeline locates rows, issues visibility-scoped queries,
writes under the pinned-alias phase, and re-fetches:
database, alias, and dialect reach are all real, so
inapplicable-by-construction is correctly NOT claimed).
They need the maintainer's separate word per the brief.

## Judgment

Zero-edit folder item. The folder owns its 32 rules singly
(FL-1..FL-5, C1-C61 all count ≤1 at their owner with
spines/templates/chains upstream); every cross-boundary
composition re-derived at WT bytes holds (FC-1..FC-13,
censuses 26/1/12/16, 20 owners, 3+1 recourse/entries,
43 single owners, exact construction/call counts);
every plausible merge dissolves on a contract difference
with a trigger (FR-1..FR-14); the one pre-rowed open
family touching the folder stays blocked on hunt-owned
lines this item never touched (FC-13); four prior
assignments the tree falsified are flagged for closeout
homing without reopening (FF-1..FF-4). No consolidation
is owed, no defect found, no ledger row landed.
Submission `ready-for-verification/1`.

## Index rows for Worker-0

32 new `file-local` rows (holding item `Folder forms/`;
all re-derived at WT bytes `cfd550b2`/`52b10986`/`df1df485`/
`ad4abc7b`/`6681c33c`; transcribe verbatim):

| `forms-leaf-manifest` | per-symbol home module (`__all__` manifest at `django_strawberry_framework/forms/__init__.py`) | `django_strawberry_framework/forms/__init__.py` (+1 owner module) | Folder `forms/` | file-local |
| `forms-module-map-prose` | spec-038 Decisions 4-5 (mechanism: sibling modules) | `django_strawberry_framework/forms/__init__.py` | Folder `forms/` | file-local |
| `forms-scalar-table-mro-walk` | `django_strawberry_framework/forms/converter.py::_SCALAR_FORM_FIELDS` + `::convert_form_field` scalar arm (12 `forms.*` keys, no bare-`Field` row) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-kind-precheck-order` | `django_strawberry_framework/forms/converter.py::convert_form_field` precheck list (relation x2, file, multi-choice, exact-type bare) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-fail-loud-dispatch` | `django_strawberry_framework/forms/converter.py::_bare_form_field` + `::_unsupported_form_field` (exact-type `str`, subclass raises) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-requiredness-decision` | `django_strawberry_framework/forms/converter.py::form_field_required` (1 def, 5 by-name calls) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-conversion-value-object` | `django_strawberry_framework/forms/converter.py::FormFieldConversion` + thin factories (shape owned by `FieldConversionBase`) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-kind-reexports` | `django_strawberry_framework/utils/inputs.py` kind vocabulary (re-exported `as`-form at `django_strawberry_framework/forms/converter.py`) | `django_strawberry_framework/forms/converter.py` | Folder `forms/` | file-local |
| `forms-operation-kind-vocabulary` | `django_strawberry_framework/forms/inputs.py::FORM` + `::CREATE_SHAPED_KINDS` + vocab checks (`CREATE`/`PARTIAL` upstream) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-field-basis-discovery` | `django_strawberry_framework/forms/inputs.py::get_form_fields` + `::_form_field_basis` + `::normalize_form_field_basis` | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-shape-identity-projection` | `django_strawberry_framework/forms/inputs.py::_form_basis_content_identity` + `::_related_model_of` | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-narrowing-naming-wrappers` | `django_strawberry_framework/forms/inputs.py::resolve_effective_form_fields` + `::form_input_type_name` (knobs + `== PARTIAL` decision; spines upstream) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-backing-column-resolution` | `django_strawberry_framework/forms/inputs.py::_model_column_for` (predicates upstream) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-triple-dispatch` | `django_strawberry_framework/forms/inputs.py::_field_triple_and_spec` + `::_model_less_relation_annotation` + `::_simple_triple` (single `InputFieldSpec` site) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-collision-guard` | `django_strawberry_framework/forms/inputs.py::_guard_input_attr_collisions` (first-raise policy; walk upstream) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-generator-pair-builder` | `django_strawberry_framework/forms/inputs.py::build_form_input_class` + `::build_form_inputs` (partial-widening + one-shot freeze) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-required-guards` | `django_strawberry_framework/forms/inputs.py::_required_form_field_names` + `::guard_create_required_fields` + `::guard_partial_required_column_less_fields` (sets; arithmetic upstream) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-input-namespace-row` | `django_strawberry_framework/registry.py` bus + `django_strawberry_framework/utils/inputs.py::make_input_namespace` (declaration here: path + trio + wrappers + `forms.input_namespace` registration; lawful convergence onto the bus family) | `django_strawberry_framework/forms/inputs.py` | Folder `forms/` | file-local |
| `forms-relation-decode-coloring` | `django_strawberry_framework/forms/resolvers.py::_decode_form_relation_single` + `::_decode_form_relation_multi` + skip/projection helpers (spine upstream) | `django_strawberry_framework/forms/resolvers.py` | Folder `forms/` | file-local |
| `forms-kind-split-decode` | `django_strawberry_framework/forms/resolvers.py::_decode_form_data` (dest split; walk/handlers upstream) | `django_strawberry_framework/forms/resolvers.py` | Folder `forms/` | file-local |
| `forms-partial-reconstruction` | `django_strawberry_framework/forms/resolvers.py::_reconstruct_partial_data` | `django_strawberry_framework/forms/resolvers.py` | Folder `forms/` | file-local |
| `forms-error-mapping` | `django_strawberry_framework/forms/resolvers.py::_form_errors_to_field_errors` (bridge; flat mapper upstream) | `django_strawberry_framework/forms/resolvers.py` | Folder `forms/` | file-local |
| `forms-shared-decode-write-steps` | `django_strawberry_framework/forms/resolvers.py::_modelform_decode_step` + `::_bound_form_or_field_errors` + `::_modelform_write_step` + `::_plain_form_write_step` + `::_run_form_pipeline_sync` (flavor dispatch; skeleton/factory upstream) | `django_strawberry_framework/forms/resolvers.py` | Folder `forms/` | file-local |
| `forms-modelform-meta-matrix` | `django_strawberry_framework/forms/sets.py::DjangoModelFormMutation._validate_meta` (flavor arms; spine validators upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-plain-meta-matrix` | `django_strawberry_framework/forms/sets.py::DjangoFormMutation._validate_meta` (presence-reject + gates + `DenyAll` default) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-plain-ledger-metaclass-bind` | `django_strawberry_framework/forms/sets.py` ledger instantiation + `DjangoFormMutationMetaclass` + `bind_form_mutations` (disjoint config; mechanics upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-shape-cache-assembly` | `django_strawberry_framework/forms/sets.py::_cached_build_form_input` (key + guard/build closures; ordering + projection upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-validation-helpers` | `django_strawberry_framework/forms/sets.py::_resolve_effective_form_field_names` + `::_normalized_form_field_selection` (wrappers; walks upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-build-name-tails` | `django_strawberry_framework/forms/sets.py::_build_and_stash_form_input` + `::_form_input_type_name_for` (flavor args; tail bodies upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-construction-hook-machinery` | `django_strawberry_framework/forms/sets.py::_default_mutation_get_form_fields` + `::_mutation_form_fields` + `::_form_kwargs_overridden` + `::_default_get_form_kwargs` + `::_default_get_form` (WT-only `_require_zero_arg…` is concurrent work joining on landing) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-meta-key-sets-namespace` | `django_strawberry_framework/forms/sets.py::_ALLOWED_MODELFORM_META_KEYS` + `::_ALLOWED_PLAIN_FORM_META_KEYS` + `input_module_path` bindings (unions; foundations + path upstream) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |
| `forms-plain-auth-seam` | `django_strawberry_framework/forms/sets.py::DjangoFormMutation.check_permission` + `::perform_mutate` (seam presence; walk upstream; hook plain-only) | `django_strawberry_framework/forms/sets.py` | Folder `forms/` | file-local |

### Corrections to existing rows

1. The five `File forms/*` plan rows each pin "target blob
unchanged at `5ee86193`" — `5ee86193` is a commit sha, not a
blob (FF-1). Closeout should re-pin each row to its real
target blob or drop the pin. No row reopened.

## Independent verification (Worker-2)

Sequencing note: this trace was written before opening `## Findings`, `### Matrix`,
`### Challenges`, `## System trace` bodies, `## Defects`, `## Pending execution`,
or `## Index rows`. Before writing I observed only: the file's header verdict
block (lines 1-14), the `##`/`###` heading titles via `grep -n` (which encode
Worker-1's topic labels and CONFIRM/REJECTED/FLAG directions but no counts,
reasons, or evidence), the `## Judgment` paragraph, and the link-defs tail
scaffold as an edit anchor. Every count, owner choice, contract difference, and
trigger below is my own derivation from the target bodies plus the greps named.

### Pins and scoped diff (own derivation)

- HEAD `23b5f421`; `ITEM_BASELINE=f5880c40` is a commit whose three forms blobs
  equal WT (`52b10986`, `df1df485`, `6681c33c`). Package-only
  `git diff ITEM_BASELINE -- django_strawberry_framework/forms/` is 0 lines:
  zero-edit CONFIRMED at the item baseline. `__init__.py` (`cfd550b2`) and
  `resolvers.py` (`ad4abc7b`) are clean vs HEAD.
- HEAD-vs-WT dirt on `converter.py` (+10/-), `inputs.py`, `sets.py` is the bug
  hunt's truth migration by diff content (`_safe_*` -> `truth.*` reads,
  `except BaseException` -> `(TypeError, ValueError)`), matching the
  dispatch's concurrent-work description. It sits inside ITEM_BASELINE, so
  Worker-1 authored none of it. Artifact is untracked (expected new file).

### Enumeration (own AST census, WT bytes)

`__init__.py` 4 top-level (docstring, future import, sets import, `__all__`);
`converter.py` 31; `inputs.py` 40; `resolvers.py` 28; `sets.py` 45.
Substantive members: converter 12 (record, alias, 4 functions, 12-row table,
bare-field, 4 prechecks, dispatcher, fallthrough) + 4 kind re-exports;
inputs 24 (3 constants, namespace trio + 2 wrappers + register, 17 functions);
resolvers 14 (recourse const, 12 functions, 1 entry pair); sets 24 (2 key sets,
sentinel, registry quad + store + register, cache trio + register, 11
functions, 2 bases + metaclass branch, bind). No member left unhomed below.

### Cross-boundary compositions (my labels W2-C1..C23)

Each: posit the change, count authoritative definitions (=1), name the owner.

- W2-C1 namespace mechanics: change the materialize ledger/clear contract ->
  `utils/inputs.py::make_input_namespace` only (forms, mutations, serializer,
  auth declare disjoint ledgers + thin wrappers). Owner `utils/inputs.py`.
- W2-C2 recourse template: reword the sync-pipeline recourse -> template in
  `utils/querysets.py::sync_pipeline_recourse` only (3 noun call sites:
  `mutations/resolvers.py`, `forms/resolvers.py`, `rest_framework/resolvers.py`).
- W2-C3 write skeleton: reorder locate/authorize/decode/write/payload ->
  `mutations/resolvers.py::run_write_pipeline_sync` only (form/model/delete/
  serializer/auth riders pass callbacks). Same for `pipeline_write_phase`.
- W2-C4 resolver entries: change UNSET-normalize or the `sync_to_async`
  boundary -> `mutations/resolvers.py::make_resolver_entries` only (4 rider
  pairs). Forms has zero `async def`/`await` bodies (grep-verified); the
  async surface is the factory wrap, so no twin can drift.
- W2-C5 single-relation spine: change type-check/visibility/project order ->
  `utils/write_values.py::decode_visible_relation` only (form + serializer
  colorings pass skip/project lambdas).
- W2-C6 provided-fields walk: change UNSET-strip/kind-dispatch ->
  `utils/write_values.py::decode_provided_fields` + `decode_field_handlers`
  only (3 flavor riders). Same for `materialize_relation_id_container`.
- W2-C7 column mapping: change relation-id/file/scalar typing or write kinds
  -> `mutations/inputs.py::model_column_input_annotation` /
  `model_column_write_kind` only (forms delegates for column-backed fields).
- W2-C8 queryset id typing: change GlobalID-vs-pk rule ->
  `mutations/inputs.py::annotate_queryset_relation` only (forms
  `_model_less_relation_annotation` adds the None-queryset diagnostic).
- W2-C9 error mappers: change envelope/keying ->
  `utils/errors.py::validation_error_to_field_errors` + `build_error_key_map`
  only (forms wraps `form.errors.as_data()`); save mapping ->
  `mutations/resolvers.py::save_or_field_errors` only.
- W2-C10 kind vocabulary: rename a decode kind ->
  `utils/inputs.py` only (`forms/converter.py` re-exports 4 names via `as`).
- W2-C11 input spines: change build/optional/guard/collision/narrow/name ->
  `utils/inputs.py` (`build_strawberry_input_class`, `optional_input_field`,
  `guard_dropped_required`, `iter_input_field_collisions`,
  `resolve_effective_fields`, `name_set_input_type_name`) only; forms wrappers
  supply nouns/knobs. `mutation_input_type_name` is the sibling wrapper, not
  a second spine.
- W2-C12 declaration mechanics: change register/dedup/clear/iter ->
  `mutations/sets.py::make_declaration_registry` only (model/form/auth
  disjoint stores). Same factory shape for `make_meta_validating_metaclass`.
- W2-C13 shape-cache plumbing: change dict/clear shape ->
  `utils/inputs.py::make_shape_build_cache` only (3 disjoint dicts).
- W2-C14 guard-before-cache: change per-declaration-guard-before-lookup ->
  `mutations/sets.py::cached_build_input` only (forms `_cached_build_form_input`
  rides it; serializer documents why it cannot).
- W2-C15 stash sequence: change materialize-and-stash ->
  `mutations/sets.py::build_and_stash_input` only (form + serializer riders).
- W2-C16 bind drain: change declaration draining ->
  `mutations/sets.py::bind_write_declarations` only (`bind_mutations` +
  `bind_form_mutations` riders).
- W2-C17 seam factory: change seam signatures ->
  `mutations/sets.py::resolver_seams` only (forms calls it twice, with/without
  id; serializer + model once each).
- W2-C18 converter skeleton: change precheck/walk/fallthrough order ->
  `utils/converters.py::convert_with_mro` + `finish_field_conversion` +
  `make_scalar_converter` + `make_kind_converter` only; record shape ->
  `utils/inputs.py::FieldConversionBase` only.
- W2-C19 grammar/predicates: `graphql_camel_name`, `is_forward_*`,
  `construction_kwargs`, `normalize_meta_field_selection`,
  `reject_unknown_meta_keys`, `require_*`, `resolve_*`,
  `run_permission_classes`, `NON_DELETE_OPERATION_INPUT_KIND`,
  `backing_model_of`, `register_subsystem_clear` — each called by name from
  its upstream owner; zero re-spellings found by grep.
- W2-C20 meta-key foundations: change the shared write keys ->
  `mutations/sets.py::COMMON_WRITE_META_KEYS` /
  `MODEL_BACKED_WRITE_META_KEYS` only; each flavor owns only its
  `| frozenset({...})` composition (forms x2, serializer, model).
- W2-C21 form-hook identity: per-hook override detection ->
  `mutations/sets.py::_hook_overridden` only (forms waiver ORs two calls).
- W2-C22 reverse-map record: change the build->decode contract ->
  `utils/inputs.py::InputFieldSpec` only (forms writes `target_name`/
  `related_model` at build, reads at decode; never re-derives).
- W2-C23 open family: `mutation-discovery-own-snapshot-read` F1 is count 2
  (forms `sets.py::_default_mutation_get_form_fields` snapshot read vs the
  serializer counterpart; `snapshot_or_meta_backing` has 0 WT hits, helper
  not landed). Owner if consolidated: `mutations/sets.py`. Block stands iff
  the touching hunks are hunt-owned (checked post-Findings against the
  ledger + diff content).

### Folder-local rules (my grouping, each count 1 with its proving challenge)

- Leaf (2): `__all__` + re-export manifest (challenge: add a third export ->
  1 manifest); module-map docstring (challenge: add a module -> 1 prose map).
- Converter (6): `FormFieldConversion` record; `form_field_required`
  (challenge: NullBoolean-on-non-null-column -> 1 decision; sole `def`,
  2 consumer files); 12-row `_SCALAR_FORM_FIELDS` (challenge: add a scalar
  field class -> 1 row); `convert_form_field` order (challenge: reorder a
  precheck -> 1 dispatcher); `_bare_form_field` exact-type case (challenge:
  change base-Field typing -> 1 arm); `_unsupported_form_field` factory
  wording (challenge: reword -> 1 factory).
- Inputs (10): namespace identity (path + ledger + wrappers + pre-bind
  register); operation vocabulary (`FORM` + `CREATE_SHAPED_KINDS`);
  discovery/basis validation (`get_form_fields` + `_form_field_basis` +
  `normalize_form_field_basis` as one gate chain); content-identity
  projection (challenge: add a consumed quantity -> 1 tuple slot);
  `_model_column_for` (challenge: admit reverse/GFK names -> 1 predicate;
  opposite polarity from `definition.py::related_target_for`);
  model-less relation annotation (challenge: change fallback -> 1 function);
  triple routing (`_field_triple_and_spec` + `_simple_triple`; challenge:
  remap an attr -> 1 site); raise-first collision guard (challenge: aggregate
  instead -> 1 loop, vs serializer's aggregating twin by contract);
  create/partial requiredness + build (`build_form_input_class`,
  `build_form_inputs`, `_required_form_field_names`, both guards as one
  requiredness family; challenge: drop-guard scope change -> the named guard
  only; each `== PARTIAL` read is an enforcement site of the closed
  3-kind vocabulary, not a second vocabulary definition).
- Resolvers (5): `to_field_name` projection; empty-values check; relation
  decoders (single coloring + per-element multi + null-clears policy as one
  decoder family); kind-split decode (`data=` vs `files=` routing);
  partial reconstruction (`model_to_dict` + `to_field_name` + M2M +
  file-exclusion as one transport). Pipeline riders (decode_step, bound
  helper, 2 write steps, `_run_form_pipeline_sync`) compose W2-C3, not local.
- Sets (9): allowed-key compositions; plain declaration ledger storage;
  shape-cache key/value shape; snapshot-read default hook; hook-contract
  enforcement (`_require_zero_arg...` + `_mutation_form_fields`); cached
  build (guard-per-declaration + kind routing + 4-key); waiver
  (`_form_kwargs_overridden` coarse trust + caveat); shared construction
  defaults (`_default_get_form_kwargs`/`_default_get_form`); the two
  `Meta` matrices + flavor seams (`DjangoModelFormMutation` 6-arm matrix,
  `DjangoFormMutation` operation-reject/ModelForm-reject/DenyAll matrix,
  `perform_mutate`, `check_permission` delegation, `bind_form_mutations`).
  Total 2+6+10+5+9 = 32. `_ABSENT`, `FormFieldConverter`, `_scalar/_kind`
  factories, `_resolve_effective...`/`_normalized...`/`_build_and_stash...`/
  `_form_input_type_name_for` are typed calls on owned spines, not rules.

### Merges I considered and would reject (my labels W2-M1..M14)

- M1 table unification (12/26/16/1 across forms/types/serializer/scalars):
  distinct key spaces (`forms.Field` vs `models.Field` vs DRF field vs
  scalar def) and subjects; trigger: one key space must serve two subjects.
- M2 name-wrapper merge: sibling thin adapters over the shared W2-C11 spine;
  trigger: a third wrapper needing logic, not nouns.
- M3 single base + mode flag: disjoint lifecycles (registry, bind, payload,
  permission default); a flag adds branches no path reaches (principle 5).
- M4 merged `_validate_meta`: disjoint matrices (operation required vs
  presence-rejected; ModelForm vs Form gates; permission defaults differ).
- M5 plain-on-`DjangoMutation`: model-less has no model/operation/primary;
  inheritance would drag model machinery plus a no-op delete surface.
- M6 heavy `_lifecycle` on write flavors: no binding state to reset (light
  ledger clear only); trigger: a write flavor gains cached per-set state.
- M7 partial-mechanism unification: bound-data reconstruction vs
  instance-`setattr` vs kwargs-merge are distinct mechanisms with distinct
  validation consequences (full-form revalidation vs field assignment).
- M8 batched multi decode: form needs per-element `to_field_name`
  projection; trigger: the batched decoder grows a projection hook AND the
  form's empty/null policy converges.
- M9 null-M2M unification: form null-clears per Django form semantics vs
  model null-rejects; trigger: one spec row unifying the stance.
- M10 guard merge: distinct required sets (form-required vs
  serializer-required-minus-injected) and wordings over the shared spine.
- M11 naming-pair extraction (`_simple_triple`): one 2-line pairing at a
  single call family; extraction relieves no change obligation (principle 11).
- M12 `== PARTIAL` extraction: 3 reads are enforcement sites of the closed
  vocabulary (W2-C11 wrapper + kind guard own it); trigger: a second
  partial-shaped kind lands.
- M13 kwargs-stub mixin: TYPE_CHECKING stubs differ by contract (ModelForm
  vs BaseForm return); runtime already single-sourced.
- M14 `form_class` key constant: attribute names spelled at use by language
  design; a constant breaks the grep census (same direction as the
  slot-name S1 rejection); trigger: the key must vary or compute.

### Matrix (own discharge)

1. Cross-flavor: greps above cover mutations/rest_framework/types/filters/
   orders/utils twins for every forms rule; no unexamined sibling.
2. Sync/async: inapplicable by construction — zero `async def`/`await`
   bodies in `forms/` (grep-verified); one sync body + factory entries.
3. Derived knowledge: `_model_column_for` vs `backing_model_field` differ
   in inputs/polarity; `related_model` recorded once, never re-derived;
   requiredness decided once. No second derivation found.
4. Round-trip: `InputFieldSpec` written at build, read at decode + error
   keying; collision guard at build; single record type (W2-C22).
5. Other media: docstrings are projections (verified against bodies while
   reading); test expectations spell literals (spot-checked `categoryId`
   style oracles in `tests/forms/` + live `test_query/`), never read owner
   maps. Consumers/oracles/projections listed, never counted.
6. Omission: enumerated single+multi decode, empty-skip both, file routing,
   create+partial guards, both-flavor permission defaults, both write
   steps under `pipeline_write_phase` — every member enforces; prior
   routed asymmetries stay routed (no contract source found by me either).

### Consolidation search statement

I searched for a real consolidation before accepting zero-edit: the greps
above re-derive every cross-boundary census from WT bytes; the only count-2
found is W2-C23 (pre-rowed, blocked). No folder-internal pair shares one
contract with the same reasons to change. Zero-edit is my own conclusion,
not a rubber stamp.

### Reconciliation (post-Findings)

Every difference between my trace and Worker-1's record, resolved:

- D1 entry pairs: I wrote 4 riders (W2-C4); FC-3 says 3. W1 CORRECT —
  `make_resolver_entries` has exactly 3 call sites (mutations:1545,
  forms:676, rest_framework:2613); auth rides the skeleton directly.
  My error, corrected; ownership unchanged.
- D2 `== PARTIAL`: I wrote 3 reads; FR-12 says 4
  (inputs:419/688, sets:335/341; prose:415 excluded; model `!= CREATE`
  at mutations/inputs:825). W1 CORRECT. Rejection stands on the
  corrected count (4 decisions, 1 vocabulary).
- D3 inputs count: I listed 9 under a "(10)" label and left
  `resolve_effective_form_fields` + `form_input_type_name` unhomed
  (my total 31, not 32). W1's FL-3 (10, "Narrowing + naming wrappers")
  CORRECT. My arithmetic/classification error.
- D4 wrapper homing: I classed sets.py's validation/build tails, the
  kind re-exports, and the pipeline riders as pure consumers; W1 rows
  them (rows 8, 18, 23, 28, 29). W1 CORRECT per the inventory
  backstop (every member must land; wrappers carry knob/flavor
  decisions). I endorse W1's 32-partition over my trace's.
- D5 C61 census: W1 says "2 identical + 1 variant"; the population is
  4 sites (inputs.py:218/244 identical, :269 invalid-entries variant,
  :284 normalize-None variant). MY correction to W1. The release
  stands (4 distinct conditions, no sync contract; the stated trigger
  covers all 4). Record-only; closeout transcribes nothing for C61.
- D6 hunk counts 3/32/20 reproduce exactly with `git diff -U0`
  (default context gives 2/17/10). Unstated instrument flag, not an
  error. Attribution content confirmed hunk by hunk.
- D7 owner singletons: I swept 51 composed-helper names (a superset
  of W1's 43); 49 single, 2 with `@overload` typing twins over one
  implementation each. Consistent; no second body anywhere.
- D8–D9 censuses confirmed exact: 20 clear owners (22 `owner=` lines
  minus 2 `SetLifecycleAttrs` placeholders); tables 26/1/12/16 by AST;
  `InputFieldSpec(` ×1 at inputs.py:601; `form_field_required` 1+5;
  `convert_form_field` 1+1; `_ValidatedMutationMeta` 11 uses + import;
  stubs byte-identical; zero `type_name_for`/`_lifecycle`/`ActiveInput`
  defs in-folder; zero `BaseException` in WT inputs.py; every FR pin
  line verified at WT bytes (675/689, 947/2393, :290, :1328, :2359,
  prose 367/378, arm 1216).
- D10 freshness: pins (5 folder + 19 connected + family `14782e58`)
  exceed the run precedent (filters pinned 5+1) and cover every
  load-bearing quoted module. The un-fingerprinted grep scopes
  (auth/filters/orders inputs for FC-1/FC-6 census words) are named
  populations; no finding's verdict turns on their bytes. Complete.
- D11 "no plan row" claims (FC-3/FC-5): verified — zero index rows
  name the skeleton/entries owners or the metaclass
  factory/snapshot record (the `shared-write-skeleton` family item
  exists but carries no index row naming the form rider).
- D12 bus members: the bus artifact enumerates forms members 8
  (`forms.input_namespace`), 12 (`forms.shape_cache`), 15
  (`forms.declarations`). W1's row 18 omits the number and rows
  26/27 omit convergence. Corrections below (transcription polish).
- D13 holding-item wording: NORMALIZE all 32 rows to
  `Folder integration \`forms/\`` — 84 prior folder rows use the full
  style with zero shorthand cells, and it matches the plan item title
  verbatim (line 134). The shorthand would be the sole outlier and
  breaks the `Folder integration` grep census.
- FF-1..FF-4: each flag's evidence re-derived and confirmed
  (commit-not-blob `5ee86193`; WT 4/31/40/28/45 = my own AST census
  and HEAD 4/30/39/28/41; HEAD typed-wrap vs WT propagation with the
  row ROUTED TO MAINTAINER; HEAD 7 catches vs WT 0 with the row listing
  forms/inputs.py). Non-reopening correct in all four: record-only /
  superseded enumeration with zero `File forms/*` rows to reopen /
  routed row under hunt WIP / census refresh — all owned by closeout.
- FC-13 block: family pins `forms/sets.py @@ -194,55 +199,78 @@` at
  WT `b8643610`; current WT `6681c33c` is the same region, hunt dirt
  by content, with zero `## Owned changes` rows covering any folder
  file and the helper at 0 WT hits. Block persists; zero edits hold.
- Pending execution: no `proof:` is correct (zero `execution-deferred`;
  composition-by-name findings are `static-reviewed` per DRY.md, with
  ordering/async pinned by named pre-existing oracles). The 7 `gate:`
  entries are complete and correctly typed: 3 workspace type/lint
  gates at the consolidate address + the folder's 4 test files. The
  cross-boundary corroborating oracles (3-flavor factory test,
  verified to assert all three entries; live API tests) run in the
  final full suite; no finding depends solely on an unlisted oracle.
- Cells: `unverified` with inapplicability NOT claimed is right and
  complete — resolvers.py locates rows, issues visibility-scoped
  queries, writes under the pinned-alias phase, and re-fetches
  through the optimizer (database, alias, and dialect reach all
  real). Maintainer word still needed per the brief.
- Gates in my copy (slot-2, fresh, post-W1 sync): basedpyright
  all-mode 0/0/0 exit 0 (69s); floor 0/0/0 exit 0 (69.6s);
  truthful-reads `--check` 120 files 0 errors exit 0. Ruff: zero-edit
  means the touched-`.py` set is empty — stated explicitly, nothing
  to run. No pytest run: WT is hunt WIP by attribution, so a suite
  result would measure the hunt, not this item (W1's reasoning,
  verified); oracles verified present by def-grep; final gate
  re-runs via the `gate:` entries. No new structural gate was
  introduced, so no fresh negative control is owed; the cited
  pre-existing oracles carry their own landed failability.
- AGENTS.md prose on the item-scoped diff: the tracked diff is empty
  (the only new file is this artifact); no code provenance, no
  citations, no tests to tier. Artifact header block matches the
  DRY.md template (title/Status/Run/trace/verification/findings/
  defects/pending/judgment plus Pins/Index/IV extras); link-defs
  scaffold 10/10; `path:NN` citations allowed in `dry-*.md` scratch.
- Defects: none found by me; the 4 released edges are correctly
  released (single-docstring restatement, per-site precision,
  pinned wording, loud-collision contract). No `(Worker-2)` entries.

### Row rulings (32 index rows + wording)

Holding-item wording for all 32: NORMALIZE to
`Folder integration \`forms/\`` per D13 (transcription instruction,
not a row defect).

- Rows 1–7 (`forms-leaf-manifest`, `forms-module-map-prose`,
  `forms-scalar-table-mro-walk`, `forms-kind-precheck-order`,
  `forms-fail-loud-dispatch`, `forms-requiredness-decision`,
  `forms-conversion-value-object`): ENDORSE. Symbols verified at WT;
  row 2's spec-first owner cell matches the `auth-structural-opt-in`
  precedent; row 7's upstream-shape parenthetical is accurate.
- Row 8 (`forms-kind-reexports`): ENDORSE. Contributor row correctly
  owned upstream with the `as`-form declaration named.
- Rows 9–17 (inputs rules through `forms-required-guards`): ENDORSE.
  Each homes verified-verbatim symbols; row 14's `== PARTIAL` note
  and row 16's single-construction note are accurate at WT.
- Row 18 (`forms-input-namespace-row`): CORRECT — append bus member
  number: `... + \`forms.input_namespace\` registration (bus member 8;
  lawful convergence onto the bus family)`. Reason: original members
  cite numbers per the serializer precedent; 8 re-derived from the
  bus artifact.
- Rows 19–25 (resolver rules): ENDORSE. Row 23 correctly gathers the
  5 pipeline riders with skeleton/factory upstream.
- Row 26 (`forms-plain-ledger-metaclass-bind`): CORRECT — append
  `(bus member 15)` to the ledger-instantiation clause. Reason: the
  disjoint ledger's clear registration is bus member 15 (bus
  artifact); makes the convergence greppable from the index.
- Row 27 (`forms-shape-cache-assembly`): CORRECT — widen the owner
  cell to name the pair: `` `.../sets.py::_form_shape_build_cache` pair
  + `::_cached_build_form_input` (key + guard/build closures;
  ordering + projection upstream; bus member 12) ``. Reason: as
  worded the row homes only the build function while FL-5 R4's pair
  declaration + bus member 12 ride on the files column alone.
- Rows 28–29 (`forms-validation-helpers`, `forms-build-name-tails`):
  ENDORSE. Thin wrappers correctly rowed with walks/tails upstream
  (per D4 this homing is required, not optional).
- Row 30 (`forms-construction-hook-machinery`): ENDORSE. The 5 stable
  helpers verified; the WT-only `_require_zero_arg…` caveat is
  honest about concurrent work.
- Row 31 (`forms-meta-key-sets-namespace`): ENDORSE. Both unions +
  both bindings verified; foundations/path upstream correctly noted.
- Row 32 (`forms-plain-auth-seam`): ENDORSE. Seam presence + walk
  upstream + plain-only hook accurately split.

Verdict: `verified`. Zero-edit CONFIRM stands: 32 rules single-owned
(with 3 transcribe-with-correction polish notes + the global wording
normalization), 13 compositions hold, 14 merges rejected with
contract differences + triggers, 1 pre-rowed block persists, 4 flags
correctly non-reopening, 7 `gate:` entries complete, cells honestly
unverified. No ledger row, no defect, no re-pass owed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[file-converter]: dry-file-forms__converter.md
[file-init]: dry-file-forms____init__.md
[file-inputs]: dry-file-forms__inputs.md
[file-resolvers]: dry-file-forms__resolvers.md
[file-sets]: dry-file-forms__sets.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
