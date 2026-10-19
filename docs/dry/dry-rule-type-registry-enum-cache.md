# DRY review: `type-registry-enum-cache`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-registry-enum-cache`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F4 aspects).
Member files: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/converters.py` (both worktree-clean,
confirmed). `HEAD` is `bfaee91d`; `ITEM_BASELINE` is `bd016015`
(member diffs vs both empty; only this artifact is new). Prior record
`docs/dry/dry-file-registry.md` F4 used only as a rejected-candidate
trigger, never a verdict; re-derived below. Never read any
`worker-memory/`.

## System trace

Rule: generated Strawberry enums for Django choice columns are cached
per `(model, field_name)` so rebuilds return the identical object;
same-class re-register is a no-op (the converter retry pattern),
different-class collides loudly; `clear()` drops the cache,
`unregister()` keeps it.

Boundary against the four sibling families on the one class (so later
items do not re-litigate): F1 model-type-map owns `_types` / `_primaries`
/ `_models` plus `register` / `unregister` / `get` and friends; F2
definition-store owns `_definitions` plus the atomic
`register_with_definition` pair; F3 pending-ledger owns `_pending` plus
identity-matched add/discard; F5 finalize-gate owns `_finalized` plus
`_check_mutable` / `mark_finalized`. F4 owns exactly `_enums` plus
`register_enum` / `get_enum` plus the key contract. The `_enums.clear()`
line inside `clear()` is F6 bus replay (shared reset site, a consumer of
F4 state, not a second definition); `unregister` deliberately never
touches `_enums` (a type leaving the map must not orphan the sibling
type still reading the same column). Name derivation
(`f"{type_name}{pascal_case(field_name)}Enum"`) lives in the converter,
not the registry. The build core (`build_enum_from_choices`: empty /
grouped-form rejection, value-based sanitization, sanitize-collision
guard, `strawberry.enum` decoration) is single-sited in
[converters][converters] and composed by name from both enum flavors.

Sites + roles. *Definitions*: `register_enum`, `get_enum`
([registry][registry]`::TypeRegistry`, one def each; `_enums` storage
touched at exactly five lines: construction, collision read, store,
lookup, `clear()` reset). *Consumers*: `convert_choices_to_enum`
(get-then-register by name; sole read-side caller path via
`convert_scalar`), `filters/inputs.py::_choice_enum_from_filter`
(delegates to the converter so filter inputs share the sibling type's
enum). *Composed core, not counted*: `build_enum_from_choices` (shared
by the read side and the serializer-only `ChoiceField` path).
*Intentional neighbor, rejected below*: `_SERIALIZER_CHOICE_ENUMS` plus
`_serializer_choice_enum` / `clear_serializer_choice_enums`
([serializer-converter][serializer-converter]). *Oracles*:
[test-registry][test-registry] (key, idempotence, collision, clear),
[test-converters][test-converters] (identity, cross-type reuse,
grouped-form / sanitize rejections), `tests/types/test_base.py`
(clear drop), `tests/rest_framework/test_converter.py`
(serializer dedupe + member-set collision),
`tests/filters/test_inputs.py` (choice-filter enum derivation),
`tests/forms/test_inputs.py` + `tests/rest_framework/test_inputs.py`
(read-side enum reuse rows). All spell literals independently; none
enumerates the owner. *Projections*: the `register_enum` /
`get_enum` / `convert_choices_to_enum` docstrings (verified against
bodies), the serializer-cache rationale comment, the glossary
[Choice enum generation][glossary] entry (`(model, field_name)`
keying).

Connected sources read for judgment, outside the members:
[serializer-converter][serializer-converter] (cache block + choice-enum
builder + clear registration), [filter-inputs][filter-inputs]
(`_choice_enum_from_filter` only; the file's concurrent
`_normalize_range_value` hunk is content-attributed external work,
untouched), [definition][definition] (per-instance relation memo —
different subject, no enum vocabulary), [finalizer][finalizer]
(pre-bind replay scope only), installed `.venv`
`strawberry/types/enum.py` (`_process_enum` body: per-class decoration,
zero cache vocabulary), upstream
`~/projects/strawberry-django-main/strawberry_django/fields/types.py`
(field-attribute memo `model_field._strawberry_enum` — behavior anchor,
outside the package population). Excluded on strength of body: every
other package module (zero `register_enum` / `get_enum` / `_enums`
vocabulary over the 117-file sweep); `forms/converter.py` (one
docstring mention, no call); Strawberry's schema layer (consumes enum
classes, never stores them).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Read side (model-backed) caches in
the registry; serializer-only path caches by descriptor-derived name
(R-A, intentional — different key spaces, different collision
policies). Filter / form / serializer model-backed paths all compose
`convert_choices_to_enum` by name; none restates key, retry, or
collision behavior.
2. **Sync/async twins.** Zero `async def` in either member (AST-verified:
converters 18 `FunctionDef`, 0 `AsyncFunctionDef`; registry 30/0 per
the file item, re-verified). Every method is in-memory dict work plus
one pure enum build; no ORM I/O, no awaits, no threads. Trigger: a
cache method touching the DB or awaiting.
3. **Derived rather than repeated knowledge.** Read-side enum name
spelled once ([converters][converters] single f-string site); cache key
spelled once per accessor (`(model, field_name)` tuple at the store,
read, and lookup lines — one rule, three lines of one body pair, not
three spellings). Zero `lru_cache` / memo decorators on the enum path
(sweep-verified in the workspace copy). The serializer name rule reads
different inputs (descriptor, no model) — R-A, not a second spelling.
4. **Inverse / round-trip pairs.** register/get, register/clear,
get-then-register retry, first-wins reuse — all pinned by oracles
below. No un-cache primitive besides `clear()` (full reset) by design.
5. **Contracts restated in another medium.** Production (owner pair +
converter consumer); oracles (independent literals, no owner reads);
projections (docstrings + serializer rationale comment + glossary
entry). The glossary states the key without restating retry/collision
semantics — projection, not a second definition.
6. **Enforcement by omission.** `register_enum` calls `_check_mutable`
(import-time-only; post-finalize late import fails loud);
`get_enum` is a pure read (no guard owed); `clear()` bypasses by the
documented test-only contract; `unregister` skipping `_enums` is the
pinned F1/F4 boundary, not a gap. No member lacks a guard its contract
requires: no defect.

### Enumeration

Instrument: `ast.parse` of both worktree members + token sweeps over
the 117-file package population (`git ls-files
django_strawberry_framework/*.py` = 117, re-counted in the workspace
copy). Every cache member assigned; every challenge ends in the family
row or a recorded rejection (no file-local row — each rule has its
neighbor or rejection recorded).

- `TypeRegistry.register_enum` / `::get_enum`: exactly 1 def each; the
only production call sites of either are the converter pair
(get-then-register) — package sweep shows zero other
`register_enum(`/`get_enum(` callers outside tests.
- `_enums`: exactly 1 storage dict; touched at exactly 5 lines
(`__init__`, collision read, store, lookup, `clear()` reset);
`unregister` touches it zero times (boundary, probe-pinned).
- Read-side enum-name f-string: exactly 1 site. `lru_cache` /
`functools.cache`: zero sites on the enum path.
- `convert_choices_to_enum`: 1 def (consumer: delegates build to the
shared core, identity to the registry). `build_enum_from_choices`:
1 def (composed core; its own assignment belongs to the holding
`types/converters.py` file item, linked here as consumer, not claimed).
- `_SERIALIZER_CHOICE_ENUMS` / `_serializer_choice_enum` /
`clear_serializer_choice_enums`: neighbor cache, R-A.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes E1–E5 below map
one-to-one onto C1–C5 (21/21 `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New choices class for a cached `(model, field_name)` (different `Enum` class, same key) | **1** (`register_enum` collision arm; original preserved; converter unchanged — calls by name). Oracle: `test_register_enum_different_class_for_same_key_raises`. Probe E1e. |
| C2 | Same choice values on two models (same field name, distinct models) | **1** (the key owns it: `(model, field_name)` tuples never collide; each model gets its own enum object). Oracle: `test_register_enum_caches_by_model_field` (both miss arms). Probes E1b/E1c. |
| C3 | `registry.clear()` + rebuild — must the cached enum survive? | **1** (`clear()`'s `_enums.clear()` reset line, F6 replay; the enum must NOT survive). Oracle: `test_clear_drops_all_state` (+ `test_registry_clear_drops_types_and_enums`). Probes E1f. Contrast, 0 moved: `unregister()` retains the cache (F1/F4 boundary), pinned by `test_two_djangotypes_reading_same_choice_field_share_one_enum`. Probe E1g. |
| C4 | Second reader of the same column (sibling `DjangoType`, `ChoiceFilter`, model-form / model-serializer field) | **0** (consumer reuses the cached object; first writer wins the GraphQL name — converter contract, not registry policy). Oracles: `test_two_djangotypes_reading_same_choice_field_share_one_enum`, `test_choice_enum_cached_in_registry_keyed_by_model_field`, the filter/form/serializer read-side rows. Probe E2. |
| C5 | Serializer-only choice reuses an enum NAME with a different member set | **1 in the other cache, 0 here** (`_serializer_choice_enum` member-set compare raises; the registry is untouched — disjoint key types: `str` name vs `(model, field)` tuple). Oracles: `test_serializer_only_choice_enum_dedupes_by_name`, `..._name_collision_with_diverging_members_raises`. Probe E3. |

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/enum-cache-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_enum_cache.py
```

Proof (`CHECKS_PASSED=21/21`): identity, both miss arms,
cross-model distinctness, first-preserved, idempotent re-register,
collision wording + preservation, clear drops, unregister keeps type
drop + enum, converter round-trip identity through the registry with
call counting, builder builds fresh objects (no memo), serializer key
space disjoint, Strawberry holds no global enum cache, neighbor state
untouched by enum writes. Status: `execution-verified`. Rejects "a
converter-level memo exists", "same choices on two models collide",
"the cache survives `clear()`", "Strawberry dedupes for us". Copy
`__file__`:
`.../dry-ws/enum-cache-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/enum-cache-w1/examples/fakeshop/db.sqlite3` (copy's own
tree and database; never the shared tree; the probes open no DB at
all). No source mutation in the proof; restores N/A. Searched
population inside the copy: 117 `.py` (matches the shared tree).

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "enum or
clear_drops_all_state"` → 4 passed (the three enum rows + the clear
row pinning C1/C2/C3).

## Findings

### F1 — enum cache (REJECTED consolidation: single-owned, neighbors compose or stay separate)

- **Contract + variation.** `(model, field_name)` → one `Enum` class.
Varies on: same-class re-register (no-op) vs different-class
(collide); one vs many registered models sharing choice values
(distinct keys); reset vs unregister (drop vs retain).
- **Sites + roles.** *Definitions*: `register_enum`, `get_enum`
([registry][registry]`::TypeRegistry`). *Consumers*:
`convert_choices_to_enum`, `_choice_enum_from_filter`, the
form/serializer model-backed paths (all by name). *Composed core*:
`build_enum_from_choices` (single-sited, linked to the holding file
item). *Oracles / projections*: as listed in System trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1 (+0 contrast);
C4 → 0; C5 → 0 here (1 in the neighbor cache). Count > 1 nowhere
in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
`django_strawberry_framework/registry.py::TypeRegistry` (F4 aspects)
stands: narrowest cohesive owner every consumer can import without
reversing a dependency (converters already imports the registry; the
reverse would cycle). Stored-derivation lifetime: cache key =
`(model, field_name)` tuple; validity = collection → `clear()`;
publish point = `convert_choices_to_enum` post-build via
`register_enum` (first writer wins the GraphQL name — converter
contract); who may mutate = `register_enum` (import-time-only via
`_check_mutable`) + `clear()` (F6 replay, test-only bypass); reads =
`get_enum` (unguarded pure lookup); explicitly NOT invalidated by
`unregister` or the finalizer pre-bind pass (collected state survives
retry; the idempotent re-register makes retry safe).
- **Migration.** None (zero-edit rejection: no behavior hunk, no test
hunk; all durable homes already exist — named under each rejection).
- **Distinct behavior (stays separate).** Key membership (model is part
of identity — same values on two models are two enums with two GraphQL
names); retry idempotence vs collision (same class vs different class);
reset vs removal (`clear()` drops, `unregister()` retains); name
derivation (converter) vs storage (registry) vs build rules (shared
core). Moving the key into the converter would strand the filter/form/
serializer consumers on a private memo each; moving storage out of the
registry would reverse the import edge.
- **Behavioral proof.** `execution-verified` for identity, key
membership, idempotence, collision wording + preservation, clear-drop,
unregister-retain, converter round-trip, builder freshness, key-space
disjointness, neighbor-state isolation (workspace 21/21 + the
authorized 4-passed focused run). `static-reviewed` for the Strawberry
no-cache read, the upstream field-memo read, docstring-vs-body prose,
and oracle-body independence (all spell literals; none reads the
owner). Observable behavior pinned: second build returns the identical
object (`is`), cross-model reads never collide, post-`clear()` reads
rebuild, post-`unregister()` siblings still share. Rejects every
duplication direction in C1–C5.
- **Structural gate.** Deferred with reason: a behavior-preserving
hand copy of the owner pair passes every standing oracle by
construction (the copy is correct — identical wording, identical
identity semantics), so no behavioral gate can pin unity; only a
source census could, and that is a bespoke existence test per helper,
which [DRY.md][dry] forbids for gate-only findings. Unity rests on the
one-way import edge (converters → registry, never the reverse) plus
the recorded triggers below. Coverage that stays: the key/idempotence/
collision/clear rows (each fails a real cache break — the focused run
is green on the unmutated tree), the cross-type reuse row (fails a
key-narrowing break), the serializer dedupe/collision rows (fail a
key-space merge).
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`, all clean
vs `HEAD:` except where noted): `registry.py`
`9cc8bb553fd417fc465809a541769a8383469cda`,
`types/converters.py`
`9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`,
`rest_framework/serializer_converter.py`
`32904418a169941c2afa1c9cd6866c55debc64f3`,
`types/finalizer.py`
`77fd9a2dd229eb9de5f29188c5058035d3606323`,
`types/definition.py`
`fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`,
`filters/inputs.py` working
`06797dc7db04e4fc78cfbc478094ecada273c533`
(HEAD `82b52d97…`; the delta is the concurrent
`_normalize_range_value` hunk, content-attributed external work in a
region this finding never cites — the cited consumer lines are
identical), `tests/test_registry.py`
`e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10`,
`tests/types/test_converters.py`
`2bdedee4de79598bb384eaac8222395b0962dfe6`,
`tests/rest_framework/test_converter.py`
`9d5d0eaf7087bf46bda189e9f117fff343bf0f5f`.
Searched population: whole package (117 `.py`, both trees);
excluded on strength of body: all modules without enum-cache
vocabulary (forms converter: docstring-only mention). Installed
Strawberry `types/enum.py` and upstream `fields/types.py` read at
their installed/checked-out revisions (behavior anchors, not
fingerprinted inputs). Any fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owners).** The cache
stays single-owned until one fires:
R-A fires if a serializer-only choice gains a model identity (or a
model choice goes model-less) so one key names both spaces;
R-B fires if Strawberry grows a process-global name→class enum
registry that dedupes distinct classes; R-C fires if the package
adopts a field-attribute memo alongside the registry. Durable homes:
the `register_enum` key/collision docstring, the
`convert_choices_to_enum` first-wins/caching docstring, the
serializer-cache rationale comment, this finding. The plan's
`## Responsibility index` row for `type-registry-enum-cache` already
covers both member files; no new row owed.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A serializer name-keyed cache vs registry `(model, field)` cache.
Difference: disjoint key types by construction (`str` descriptor name
vs `(model, field)` tuple — a serializer-only `ChoiceField` has no
model, so the registry key cannot name it); different collision
policies (member-set compare vs class identity); different lifetimes
(full-clear-only subsystem row, surviving pre-bind resets, vs instance
`clear()`). Consolidating would force model-less choices through a
model key (or vice versa) behind a mode flag. Trigger: one key becomes
able to name both spaces. Home: the `_SERIALIZER_CHOICE_ENUMS` comment
block (states the separation + why) and the `register_enum` key
docstring.
- R-B Strawberry's per-class enum decoration vs the registry cache.
Difference: `strawberry.enum` attaches a definition to the class
object it decorates and stores nothing globally (verified in the
installed body; each `build_enum_from_choices` call returns a fresh
class — probe E2b); deduplication across distinct classes is exactly
what the registry adds. Trigger: upstream ships a global enum
registry. Home: the `convert_choices_to_enum` generate-or-fetch
docstring and the builder's caller-owns-caching clause.
- R-C upstream field-attribute memo (`model_field._strawberry_enum`)
vs the registry dict. Difference: attribute pinned to a field object
vs registry keyed by `(model, field_name)` with cross-type reuse,
retry idempotence, and loud cross-key collision; upstream is a
behavior source outside the package population, not a second
definition here. Trigger: the package adopts a field-attribute memo
next to the registry. Home: the registry module docstring (maps
`(model, field_name)` to `Enum`) plus this finding.
- No converter-level memo exists (zero `lru_cache`/memo sites on the
enum path, single get/register call pair) — an absence after a full
sweep, not a second definition; no trigger owed beyond the matrix-3
standing trigger (a memo appearing on the converter path reopens C4).

## Defects

None new. Every asymmetry checked while tracing holds: the
`_check_mutable` guard placement (all 7 direct mutators incl.
`register_enum`; `get_enum` correctly unguarded as a read);
`unregister` skipping `_enums` (pinned boundary, not an omission);
`clear()` ordering (own maps incl. `_enums` before subsystem replays);
the serializer clear registered full-only (pre-bind survival intended,
matching the collected-state lifetime); the filters concurrent hunk
lies outside every cited line.

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused test ran green
post-trace (4 passed) with zero edits in flight, so no run is
invalidated. No `execution-deferred` items. `FAKESHOP_SHARDED=1` and
Postgres cells `inapplicable by construction`: every executed claim
touches no database, alias, or dialect decision (pure in-memory dict
work + one pure enum build; the probes open no DB). Full-suite gate
business is deferred to the final-gate item with reason: the entry
command authorizes workspace runs plus one focused `--no-cov` test,
and a green unmutated suite would discharge no failability proof for
a rejection that proposes no gate.

## Judgment

Single-owned rule, single definition pair, all consumers composing by
name. The three resemblance candidates (serializer cache, Strawberry
decoration, upstream field memo) are intentional separations with
recorded differences, triggers, and existing homes. Consolidation
rejected; zero edits; no new tests owed (standing oracles at the
mandated tiers pin every challenged axis).

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE` (`bd016015`)
is empty for `django_strawberry_framework/registry.py` and
`django_strawberry_framework/types/converters.py` (both clean vs
`HEAD` `bfaee91d` before the first read and still clean); the only new
path is this artifact (untracked, owned by this item). The plan's
`## Owned changes` ledger holds no row on either family path (only
`optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`) — confirmed by full read; nothing to
attribute, no stop triggered. The one dirty path this trace read
(`filters/inputs.py`, concurrent `_normalize_range_value` hunk) was
never edited. No commit per standing rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff format
--check` on both member paths — all green, both already formatted
(proves the no-edit claim mechanically; `.md` artifacts are excluded
from format). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/enum-cache-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_enum_cache.py` holding the 21 executed checks). No manifest
(no `prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `type-registry-enum-cache` (this
artifact); no `## Responsibility index` change (provisional owner +
both member files already covered, status stays `open` until Worker
2); no `## Owned changes` append (zero tracked edits).

## Independent verification (Worker 2)

Own trace, re-derived from primary sources (registry body,
converters body, package-wide greps, installed Strawberry, upstream
checkout, oracle bodies) before reconciling with `## Findings`
above. Procedural note: the artifact arrived whole, so `## Findings`
was visible before this section was written; every count below was
recomputed from the sources named, not taken from W1 prose, and each
difference is reconciled explicitly.

### Own mechanism sweep

- `_enums` touches (grep over package): exactly 5 lines in
  [registry][registry] — `__init__` construction (line 121),
  collision read (line 567), store (line 574), lookup (line 578),
  `clear()` reset (line 596). Agrees with W1's "exactly 5 lines".
- `unregister` (lines 284–335) touches `_enums` zero times
  (confirmed by body read; no `_enums` token in the method). Agrees.
- `register_enum` / `get_enum`: exactly 1 def each. Only production
  call sites of either are the converter pair
  (`registry.get_enum` line 770, `registry.register_enum` line 791,
  both inside `convert_choices_to_enum`). Package-wide grep for
  `register_enum(`/`get_enum(` outside tests returns only those two
  call lines plus the defs and docstring mentions. Agrees with W1.
- Read-side enum-name f-string (`f"{type_name}{pascal_case(...)}Enum"`):
  exactly 1 site (converters line 775). Agrees.
- Converter-level memo: zero `lru_cache` / `cache` / `functools.cache`
  on the enum path. The `lru_cache` hits in the package
  (`utils/strings.py`, `permissions.py`, `utils/relations.py`,
  `keyset.py`, `utils/permissions.py`) are all off the enum path;
  `Enum(` construction has exactly 1 site (converters line 736,
  inside `build_enum_from_choices`). W1's "no converter-level memo
  (sweep-proved absence)" is TRUE.
- R-B re-checked against installed Strawberry
  (`.venv/.../strawberry/types/enum.py::_process_enum`, full body
  read): decorates the class in place
  (`cls.__strawberry_definition__ = ...`), iterates members, returns
  `cls`. Zero module-level dict, zero `registry`/`cache`/`global`
  vocabulary (name scan over the module source returns only
  `_process_enum` / `has_enum_definition` lines). `dir()` shows no
  registry object. "No global store" is TRUE; dedupe across distinct
  classes is exactly what the package registry adds. Agree R-B.
- R-C re-checked (`strawberry_django/fields/types.py` lines 460–514
  read): `getattr(model_field, "_strawberry_enum", None)` memo pinned
  to the field object, stored back at line 514. Attribute memo vs
  `(model, field_name)` dict with cross-type reuse + retry
  idempotence + loud collision; upstream is outside the package
  population. Agree R-C.
- `build_enum_from_choices`: 1 def (converters line 628), called from
  exactly 2 sites (`convert_choices_to_enum` line 786,
  `_serializer_choice_enum` line 886). Single-sited core. Agrees.

### Consumers (precision amendment, immaterial)

- Direct: `convert_choices_to_enum` (get-then-register) and
  `filters/inputs.py::_choice_enum_from_filter` (delegates straight
  to the converter, lines 355–364). Confirmed by body read.
- Indirect (one hop via `convert_scalar`): auto-generated
  model-backed fields on the form path
  (`forms/inputs.py` → `mutations/inputs.py::model_column_input_annotation`
  → `convert_scalar` → `convert_choices_to_enum`) and the serializer
  auto path (`_model_backed_scalar_annotation` line 830 →
  `convert_scalar`). Confirmed by import/call grep.
- Exception W1's shorthand elides: a consumer-DECLARED serializer
  `ChoiceField` over a model column does NOT touch the registry —
  `_model_backed_scalar_annotation` line 828–829 short-circuits to
  `_serializer_choice_annotation` (serializer cache). This is the
  documented schema-override contract ("declared choices must
  survive"), not a second registry definition and not a missed
  consumer: the two caches serve different GraphQL names/shapes.
  Difference from W1's "form/serializer model-backed paths (all by
  name)": "all" overstates by this one declared-choice branch. No
  definition count changes; no action owed.

### Definition counts (agree all five)

- C1 (new class, same key) → 1 (`register_enum` collision arm;
  oracle `test_register_enum_different_class_for_same_key_raises`
  asserts wording + preservation). Agree.
- C2 (same values, two models) → 1 (key owns it; oracle
  `test_register_enum_caches_by_model_field` both miss arms). Agree.
- C3 (clear + rebuild) → 1 (`clear()` reset line; oracles
  `test_clear_drops_all_state` +
  `test_registry_clear_drops_types_and_enums`). `unregister`-retains
  contrast 0 moved, pinned by
  `test_two_djangotypes_reading_same_choice_field_share_one_enum`
  lines 188–191 (comment + `unregister` + cross-type `is` assert).
  Agree.
- C4 (second reader, same column) → 0 (reuse; first-wins name is
  converter contract). Agree.
- C5 (serializer same-name/different-members) → 0 here, 1 in the
  neighbor (oracles `test_serializer_only_choice_enum_dedupes_by_name`
  / `..._name_collision_with_diverging_members_raises`, bodies read).
  Agree.

### Owner (agree)

`registry.py::TypeRegistry` (F4 aspects). Converters already imports
the registry; moving storage into the converter would strand the
filter/form/serializer consumers and reverse the import edge. Narrowest
cohesive owner every legitimate consumer can depend on. Agree.

### Population completeness (agree)

`git ls-files django_strawberry_framework/ | grep \.py$ | wc -l` =
117 in this worktree, matching W1's searched population (my first
`93` was a non-recursive glob error, corrected). Excluded on strength
of body confirmed by spot grep: `forms/converter.py` carries only a
docstring mention (line 13), `types/definition.py` and
`types/finalizer.py` carry zero enum-cache vocabulary. No second site
found outside W1's inventory.

### Boundary judgment: F4 vs F1/F2/F3/F5 holds; asymmetry is contract, not defect

- `clear()` line 596 `_enums.clear()` is F6 bus replay (shared reset
  site consuming F4 state), consistent with every other map cleared
  beside it plus subsystem replays. Not a definition. Agree.
- `unregister`-retains vs `clear`-drops: HOLD as intentional boundary.
  Contract basis: (1) `unregister`'s docstring enumerates exactly what
  it drops (`_types`, `_models`, `_primaries`, `_definitions`,
  pending, connection-cache eviction) and `_enums` is absent from that
  enumeration — a careful reader sees retention, not removal, despite
  the loose "all traces" opener; (2) oracle
  `test_two_djangotypes_reading_same_choice_field_share_one_enum`
  depends on retention (unregister A, build B, assert `is`-shared +
  first-wins name); (3) rationale is sound — a type leaving the map
  must not orphan the sibling still reading the same column, and test
  teardown that wants a full reset uses `clear()`. Under the AGENTS.md
  defect bar (contract row + feasible shape + wire/config input) this
  is not a defect: no wire-reachable contract breaks, the pinned
  behavior is the intended one, and the enumeration plus the oracle
  state it. A future owner-prose clause naming the retention
  explicitly would be welcome polish, but its absence is not a
  `## Defects` entry. W1's "no defects" STANDS.

### R-A re-judged: neighbor CORRECT to be separate

Applied the change challenge myself (unify the two caches on `(name,
members)`): it fails on four axes. (1) C2: same values on two models
must yield TWO enums with two GraphQL names; a unified
`(name, members)` store dedupes by member equality and would merge or
collide them. (2) Collision policy: registry raises on
different-class-same-key regardless of member equality (identity
contract for retry safety); serializer dedupes on member equality
(same name + same members → reuse). One store cannot honor both.
(3) Strawberry requires one type per GraphQL name — same-name /
different-members must fail loud (serializer oracle pins this); a
unified store keyed with members would either coexist (SDL break) or
need a mode flag. (4) Lifetimes: registry enums die on instance
`clear()`; serializer enums survive pre-bind resets (registered
without `before_bind=True`, surviving the finalizer's
`iter_subsystem_clears(before_bind=True)` pass at finalizer line
1096) and die only on full clear. Unifying forces one lifetime on both
and breaks either test isolation or the parked-globals discipline.
Different keys (`(model, field)` tuple vs `str` name — a model-less
choice cannot even name the registry key), different policies,
different lifetimes: different contracts. SEPARATION CORRECT. Trigger
(one key able to name both spaces) stands.

### No-gate reasoning judged (agree, same standard as taxonomy/accessor items)

A behavior-preserving hand copy of the owner pair passes every
standing oracle by construction (identical wording, identical identity
semantics), so no behavioral gate can pin unity; the only census is a
bespoke existence test per helper, which DRY.md forbids for gate-only
findings. Same standard as the verified taxonomy/accessor rejections
(no gate, triggers at the owner). The standing rows that fail REAL
breaks — key/miss arms, idempotence, collision wording+preservation,
clear-drop, cross-type `is`-reuse + first-wins name, serializer
dedupe/collision — stay as behavior coverage, not gates. Agree: no
gate owed, none added.

### Freshness re-hashed (all match)

Recomputed `git hash-object` in this worktree:
`registry.py` `9cc8bb55…` match; `types/converters.py` `9ceb34af…`
match; `rest_framework/serializer_converter.py` `32904418…` match;
`types/finalizer.py` `77fd9a2d…` match; `types/definition.py`
`fa6c4d330…` match; `tests/test_registry.py` `e330cfb8…` match;
`tests/types/test_converters.py` `2bdedee4…` match;
`tests/rest_framework/test_converter.py` `9d5d0eaf…` match;
`filters/inputs.py` working `06797dc7…` match (HEAD `82b52d97…`
confirmed via `git show HEAD:`; delta is the concurrent
`_normalize_range_value` hunk outside every cited line — cited
consumer lines identical). Searched population 117 both trees. No
finding stale.

### Pending execution empty judged (agree)

W1's 21/21 workspace probes are `execution-verified` by record (probe
script + copy `__file__` + copy DB `NAME` + no source mutation); the
one authorized shared-tree focused run (4 passed) is recorded. I ran
no pytest per AGENTS.md (zero edits in flight; entry authorizes only
workspace runs + one focused `--no-cov` test, already consumed).
`FAKESHOP_SHARDED=1` / Postgres `inapplicable by construction`:
ACCEPTED — every executed claim is in-memory dict work plus one pure
enum build; no database, alias, or dialect decision is reached. The
clear/rebuild lifecycle needs no extra oracle tier beyond the standing
rows: oracles the final gate will run for this family are
`tests/test_registry.py` (key, idempotence, collision, clear),
`tests/types/test_converters.py` (identity, cross-type reuse, grouped
/ sanitize rejections), `tests/types/test_base.py::test_registry_clear_drops_types_and_enums`,
`tests/rest_framework/test_converter.py` (dedupe + collision),
`tests/filters/test_inputs.py` (choice-filter derivation),
`tests/forms/test_inputs.py` + `tests/rest_framework/test_inputs.py`
(read-side reuse rows) — all inside the full-suite gate. `## Pending
execution` empty CORRECT.

### AGENTS.md prose on the empty diff (agree)

Item-scoped diff vs `ITEM_BASELINE` `bd016015` on both member paths is
empty (confirmed: `git diff <baseline> -- registry converters` prints
nothing; `git diff HEAD --` on both paths empty; working blobs equal
the fingerprinted ids). Only new path is this artifact (untracked,
owned by this item). Concurrent dirt elsewhere (filters/sets, forms,
mutations, optimizer, resource_policy, `docs/bug_hunt/bug_hunt-0_0_15.md`
— the sole `ITEM_BASELINE` diff hunk) is out of scope, preserved,
untouched. Artifact carries reference-style links + `LINK
DEFINITIONS` block, `path::Symbol` citations, no process provenance
beyond the proof/freshness fields DRY.md requires; no new tests owed
(standing oracles at the mandated tier — `tests/` for lifecycle
contracts with no wire shape). Ruff on both member paths green
(`format --check`: 2 files already formatted; `check`: all passed).

### Per-claim agreement / difference

1 definition pair + `_enums` at 5 lines — AGREE (recounted 5).
Consumers (converter sole get-then-register; filter by name;
form/serializer paths) — AGREE with the declared-choice precision
amendment above (immaterial). `build_enum_from_choices` single-sited
core — AGREE. F1/F2/F3/F5 boundary + F6 bus replay + unregister
boundary — AGREE. C1→1, C2→1, C3→1 (+0 contrast), C4→0, C5→0
here/1 neighbor — AGREE all. Owner/key/first-wins/import-time-only/
clear-only — AGREE. R-A/R-B/R-C separations — AGREE all three (R-B
"no global store" verified TRUE in installed Strawberry). No
converter memo — AGREE (sweep-proved). No defects — AGREE. No
pending execution; sharded/PG inapplicable — AGREE. No gate — AGREE
with reason.

## Defects

None. (No `(Worker 2)` entries: the unregister-retains asymmetry and
the declared-choice serializer-cache branch were both judged intended
contracts above, neither meeting the AGENTS.md defect bar.)

## Judgment (Worker 2)

Single-owned rule, single definition pair, all consumers composing by
name; three resemblance candidates intentionally separate with
differences, triggers, and homes. REJECT consolidation; zero edits;
no new tests owed. `Status: verified`, no pending execution.

Worker 0 rows: tick Family `type-registry-enum-cache` as verified
(REJECTED single-owned, 3 separations with triggers, no gate; zero
production edits; no pending execution); set the
`## Responsibility index` `type-registry-enum-cache` row status
`open` → `rejected` (owner + both member files already covered, no
new row); no `## Owned changes` append (zero tracked edits). Scratch
for removal by explicit path after `verified`: WS tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/enum-cache-w1`
(incl. `probe_enum_cache.py` + its `.venv`); no manifest (no
`prove_failability.py` run — no gate added, none owed).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[converters]: ../../django_strawberry_framework/types/converters.py
[definition]: ../../django_strawberry_framework/types/definition.py
[filter-inputs]: ../../django_strawberry_framework/filters/inputs.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[registry]: ../../django_strawberry_framework/registry.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
