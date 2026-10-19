# DRY review: `serializer-source-axis-normalization`

Status: verified
Run: 0.0.15 2026-10-01-10

Item kind: FAMILY (responsibility family). Verdict CONFIRM: the
`InputFieldSpec.source` recording rule had two authoritative definitions
(character-identical lines); consolidated at the re-derived owner
`rest_framework/serializer_converter.py::normalize_serializer_source`
(new symbol) with both sites composing by name plus one direct owner
test, in the same change. Seven exclusions carry contract difference +
trigger each, with the durable-home clause at the owner.

## System trace

The target owns the serializer-only `source` axis of the unified
`utils/inputs.py::InputFieldSpec` reverse-map record: how a DRF field's
`source` is RECORDED on the spec. The rule: a falsy `source`, or one
equal to the declared field name, records `None`; otherwise the
one-segment source is recorded.

Pre-edit, two authoritative definitions spelled it character-identically:

- `rest_framework/serializer_converter.py::resolve_serializer_field`
  (`source = field.source if (field.source and field.source != field_name)
  else None`, with `field_name = _bound_field_name(field)`), covering
  scalar / relation / file fields;
- `rest_framework/inputs.py::_resolve_nested_field` (identical line, with
  `field_name` the effective-dict key), covering explicitly-opted-in
  nested serializer fields.

Both lines bind the same value under the supported contract:
`rest_framework/sets.py::_validate_schema_field_map` rejects a hook map
whose key differs from the bound `field.field_name`, the walk iterates
that validated map's key-preserving narrowings, and nested recursion
reads DRF `.fields` (keys equal bound names by DRF construction) — so
the dict key always equals the bound name on every build path. The
contract source states the sameness outright: spec-039 (nested
Improvements) "A nested field with a DRF `source=` records the same
normalized one-segment source axis scalar / relation fields do".

Read whole or in the cited regions at current bytes (HEAD `5c3496e0` +
working tree; member lines byte-identical in both): both targets whole;
`utils/inputs.py::InputFieldSpec` (axis contract); `resolvers.py` axis
consumers (`_assert_field_agreement`, intent walk, M2M/FK attestation,
error re-key); `sets.py` validator + ownership walk; forms/model
`InputFieldSpec` constructions; the fingerprint; the installed DRF
`Field.bind` (bind default + `source_attrs` semantics); oracles
(`tests/rest_framework/test_converter.py`,
`tests/rest_framework/test_inputs.py`, live serializer rows); spec-039
Decision 7 + nested rows. The two file artifacts that named/adopted this
family were orientation only: every site, count, and exclusion below was
re-derived fresh at current bytes, never inherited.

Dirt: both indexed files were dirty at dispatch with concurrent
truth-migration / except-narrowing / hunt-behavior hunks (19 + 30),
all attributed by diff content to the named concurrent populations
(hunt production files, maintainer `except BaseException` deletions);
zero unattributed hunks; both member lines and all four edit regions
were clean. Own hunks (6, all on clean lines): helper insert + call
site in the converter, import + call site in `inputs.py`, import + new
test in `tests/rest_framework/test_converter.py`. Full attribution in
`## Implementation (Worker-1)`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched, all write flavors read.
   Forms (`forms/inputs.py`, spec construction) and model mutations
   (`mutations/inputs.py`, spec construction) build `InputFieldSpec`
   WITHOUT `source` (the `None` default) — correctly absent: the record's
   own contract names `source` serializer-only. No third normalization
   exists in any flavor (census below). The read side has no `source`
   concept. Sibling behavior confirms the axis is serializer-scoped, not
   a shared rule owed a shared home.
2. **Sync/async twins.** Inapplicable with reason: the rule is a pure
   finalize-time string fold. Zero `async def` / `await` /
   `sync_to_async` / `run_in_one_sync_boundary` in either host module
   (grep count 0 at current bytes); both hosts run during input-class
   construction, never across an await boundary. No colored twin exists
   to compare.
3. **Derived rather than repeated knowledge.** Found and consolidated:
   the two member lines derived the recorded axis by identical inline
   spelling. Post-edit census: `source != field_name` occurs exactly
   once package-wide (the owner); both construction sites compose by
   name. The `source or name` / `or target_name` reads share tokens but
   derive the EFFECTIVE source (which attribute to use), never the
   recording — excluded with contract differences (R1-R5), not merged.
4. **Inverse / round-trip pairs.** Searched: recording (build, this
   family) vs denormalizing reads (resolvers agreement/intent/attestation
   plus the inputs collision `source_of`, all `spec.source or
   spec.target_name`) form one grammar in two directions, correctly
   separated — the readers consume the AXIS, none recomputes the fold.
   The runtime attestation read additionally prefers the live runtime
   field with spec fallback (which attribute to attest, a different
   contract — R3). No half is missing, no half is restated.
5. **Contracts restated in another medium.** Inventoried with roles:
   production (the owner + two by-name calls); contract sources
   (spec-039 Decision 7 mapping + nested "same normalized one-segment
   source axis" row; the `InputFieldSpec.source` docstring);
   independent oracles (value pins at both call sites plus the new
   three-arm owner pin — all spell VALUES, none reads the owner);
   projections (converter module-docstring source-axis paragraph, the
   nested docstring sameness sentence, call-site comments — describe,
   never own). A recording change moves production + value oracles
   together by design; oracles listed, never counted.
6. **Enforcement by omission.** Enumerated: all five `InputFieldSpec(`
   constructions package-wide (forms, mutations, converter,
   nested-input; the fifth hit is the distinct `GeneratedInputFieldSpec`
   record, excluded by type). Exactly the two serializer sites set
   `source`, and post-edit both call the owner. No member lacks the
   normalization; no omission defect filed.

### Enumeration

Instrument: literal + regex search over `django_strawberry_framework/`
(100 files) and the rest-framework oracle files, plus full reads of both
host functions and every candidate body; counts below are matches at
current bytes, every one homed.

| # | Population | Count | Home |
|---|---|---|---|
| 1 | `source != field_name` | 1 (owner :720; pre-edit 2) | F1 |
| 2 | `field.source if` | 3 (`backing_model_field` resolve, owner, resolvers attestation read) | F1 + R1 + R3 |
| 3 | `InputFieldSpec(` setting `source=` | 2 (both call the owner) | F1 |
| 4 | `InputFieldSpec(` never setting `source` | 2 (forms, model) | R6 (correctly absent) |
| 5 | `require_one_segment_source` def + calls | 1 def, 2 calls (both hosts compose it already) | R7 (separate rule) |
| 6 | effective-source `or` reads (spec- or field-side) | 8 (resolvers x6, inputs collision `source_of`, `writable_source_collisions` write key) | R2/R3/R5 (consumers) |
| 7 | raw/unfolded axis inputs | 5 (fingerprint tuple, sets map, resolvers runtime map, describe check, shape token) | R4/R5 |
| 8 | oracle pins of axis VALUES | 8+ (both call sites + owner) | oracles (listed) |
| 9 | `GeneratedInputFieldSpec(` | 1 (different record) | excluded by type |

### Challenges

Counts are authoritative definitions only. Consumers, oracles,
projections listed, never counted. Pre-edit counts re-derived at
current bytes before the consolidation; post-edit counts verified after.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | recording | record equal-source explicitly (never `None`) | pre-edit **2** (both member lines); post-edit **1** (owner) | CONFIRM — the driver |
| C2 | recording | drop the falsy arm (empty source recorded explicitly) | pre-edit **2**; post-edit **1** | CONFIRM |
| C3 | recording | change the comparison basis (e.g. normalized-name compare) | pre-edit **2**; post-edit **1** | CONFIRM |
| C4 | effective resolve | `backing_model_field` default handling change | **1** (the resolve; C1-C3 never move it) | exclusion R1 |
| C5 | ownership detect | `source or name` write-key change | **1** (the detector) | exclusion R2 |
| C6 | decode/attest | effective-source read change | **1** per read | exclusions R3/R5 |
| C7 | fingerprint | fold the fingerprinted source | **0 here** (deliberately raw input) | exclusion R4 |
| C8 | guard | fuse dotted/star rejection into the fold | refused (raising guard vs pure fold) | exclusion R7 |

Under C1 the `or target` consumers do NOT move (same effective value
either way — the fold is internal terseness); the `source=None` oracles
move as oracles. Under C2 the `source=''` arm is pinned only by the new
owner test (no call-site oracle covers it — verified by census).

## Findings

### F1 — source-axis recording (CONFIRMED, consolidated)

- **Contract + variation.** `InputFieldSpec.source` records the
  one-segment DRF `source`, folded to `None` when falsy or equal to the
  declared field name (terse, form-symmetric reverse map). Varies only
  as the recording contract (falsy handling, equal handling, comparison
  basis). The spec's nested row asserts the sameness: one rule for
  scalar/relation and nested fields.
- **Sites + roles.** *Definitions, pre-edit (2)*: converter
  `::resolve_serializer_field` line and inputs `::_resolve_nested_field`
  line (character-identical; both read at HEAD + WT bytes, byte-equal).
  *Definition, post-edit (1)*: converter
  `::normalize_serializer_source` (new); both former sites compose by
  name. *Consumers*: every effective-source read (row 6-7 populations —
  decode, agreement, attestation, describe, shape token, collisions).
  *Oracles*: value pins at both call sites (converter renamed-scalar,
  renamed-relation, declared-choice; inputs nested single+many,
  identity-None) plus the new three-arm owner pin; the live serializer
  rows cover both hosts (prior traces + serializer/live-test presence
  re-grepped here, not re-executed). *Projections*: module-docstring axis
  paragraph, nested sameness sentence, call-site comments.
- **Challenges.** C1-C3 count 2 pre-edit, 1 post-edit. Consumers do not
  move under any of them (effective value unchanged); oracles move as
  oracles.
- **Owner + lifetime.** `rest_framework/serializer_converter.py` by
  responsibility (principle 7): it already owns the source axis (the
  one-segment guard both sites compose, the source-keyed column
  resolve, the axis construction for every non-nested kind), and
  layering is one-directional (inputs imports 8 names from the
  converter, zero flow back). `inputs.py` would reverse that
  dependency; `utils/inputs.py` would couple the shared substrate to
  DRF-only vocabulary for an axis two flavors never set. Pure
  expression; no stored derivation, no lifetime fields owed.
- **Migration.** Converter exposes `normalize_serializer_source(field,
  field_name)` beside the guard; both spec-construction sites call it
  with their in-scope `(field, field_name)`; the recorded value is
  byte-identical on every path (same expression, same comparison basis
  — the spec's declared name, validated equal to the bound name).
  Oracles unchanged (they pin values, never spelling).
- **Distinct behavior.** The dotted/star guard calls above both lines
  stay (already shared, separate rule R7); the effective-source reads
  stay (R1-R5); forms/model construction stays sourceless (R6).
- **Behavioral proof.** `execution-verified`: one focused run, 8
  passed — the new three-arm pin plus the pre-existing value pins at
  both call sites and both adjacent-guard pins (command + venv in
  `## Implementation`). Rejects "either site records a different axis
  value than before" (every pre-existing pin passed unmodified after
  the consolidation) and "an arm folds wrong" (renamed/default/falsy
  each pinned). No `proof:` entry remains. Cells: sharded/pg
  inapplicable by construction — a pure construction-time string fold
  with no queryset, alias, or dialect decision (Worker-2 judges).
- **Structural gate.** None added, deliberately: a spelling census
  would pin non-behavioral form and rot on any owner rewording, and a
  future third site inlining a CORRECT copy is future duplication, not
  a behavioral divergence — no test can prevent it, only the next cycle
  can consolidate it. Protection is composition by name (visible at
  both sites) plus value oracles at both sites plus the owner pin.
- **Coupling.** None: the edit touches only clean lines; no finding
  depends on another item's landing.
- **Freshness.** Converter HEAD `40cb765a` / WT `d90b4a00` / copy
  `d90b4a00`; inputs HEAD `dfedd0e5` / WT `a4dbdb90` / copy `a4dbdb90`;
  test HEAD `4d505540` / WT `6a105426` / copy `6a105426` (full ids in
  `## Implementation`). Searched population: whole package (100
  files) + oracle files + installed DRF `Field.bind` + spec-039.
  Excluded by body: rows 4-7 populations (each read, not grep-judged).

### Exclusions (contract difference + reconsideration trigger each)

- **R1 — `backing_model_field` effective resolve.** Difference: answers
  which attribute to RESOLVE (`field.source if field.source else name`),
  never folds — C1-C3 never move it. Trigger: the resolve needing the
  default-vs-renamed distinction. Home: owner docstring clause.
- **R2 — `writable_source_collisions` write key.** Difference: the
  ownership-detection write key over raw maps (`source or name`,
  star-excluding), a different domain from spec recording. Trigger:
  ownership detection moving onto normalized specs. Home: owner
  clause (via the `or target` consumers).
- **R3 — resolvers decode/attestation reads.** Difference: which
  attribute to USE/attest, with live-runtime preference and spec
  fallback — denormalizing consumers, never a second fold. Trigger: a
  decode needing the folded form. Home: owner clause.
- **R4 — fingerprint raw `field.source`.** Difference: deliberately
  UNNORMALIZED drift input — folding would blind it to hook changes.
  Trigger: the fingerprint comparing normalized shapes (a contract
  change, not a refactor). Home: owner clause.
- **R5 — describe / shape-token / `source_of` / raw maps.**
  Difference: value readers and detector inputs, not recorders.
  Trigger: any of them recomputing the fold. Home: owner clause.
- **R6 — forms/model sourceless construction.** Difference: correctly
  absent — the record contract names the axis serializer-only.
  Trigger: a form/model field gaining a source-like remap. Home:
  owner clause ("form/model specs never set the axis").
- **R7 — `require_one_segment_source` guard.** Difference: a RAISING
  guard with call-site nouns vs a pure fold — different verbs; both
  hosts already compose it. Fusing would hide diagnostics or impurify
  the fold. Trigger: a third site needing guard-then-fold as one
  noun-sharing step. Home: owner clause.

## Defects

None. One examined-and-cleared edge: the falsy arm's reachability.
Installed DRF `Field.bind` defaults `None` to the field name but an
explicit `source=''` survives (and an explicit equal source asserts),
so the falsy arm is the `source=''` path and the equal arm is the bind
default — both reachable, both pinned, no defect.

## Pending execution

None. No `proof:` entry (behavioral proof is `execution-verified`;
failability beyond the green run is argued from distinct
input/outcome pairs per arm, and no gate is relied on) and no `gate:`
entry.

## Judgment

One rule, two spellings, now one owner: the source-axis recording
fold lives in `normalize_serializer_source` with both construction
sites composing by name, all value oracles green unmodified, and every
lookalike excluded on a read contract difference with its trigger at
the owner.

## Implementation (Worker-1)

Tracked changes (6 hunks, all on lines clean at HEAD+WT; no concurrent
hunk touched):

- `django_strawberry_framework/rest_framework/serializer_converter.py`
  — new owner `normalize_serializer_source(field, field_name)` after
  `require_one_segment_source` (+21 incl. docstring with the
  durable-home clause); `resolve_serializer_field` call site is now one
  by-name call (1-line swap).
- `django_strawberry_framework/rest_framework/inputs.py` — import the
  owner (alphabetical slot); `_resolve_nested_field` call site is now
  one by-name call (1-line swap).
- `tests/rest_framework/test_converter.py` — import the owner;
  `test_normalize_serializer_source_records_explicit_source_else_none`
  pins renamed/default/falsy directly (mirrors the adjacent
  one-segment-guard owner test).

Dirt attribution (by diff content vs `git show HEAD:<path>`): the 19 +
30 + 6 pre-existing hunks in the touched paths are all named concurrent
work — truth-migration vocabulary (`truth.*`, `_safe_*` removal,
`type(x).__name__` rewrites), hunt except-narrowing + behavior
(`allow_null` widening, `allow_blank` enum exclusion,
`NESTED_STABLE_FIELDS_INSTRUCTION` removal, speculative-discovery
guard, fingerprint consolidation), and maintainer `except BaseException`
arm deletions. Zero unattributed hunks; the item never stopped.

Fingerprints (HEAD `5c3496e0`; pre-edit WT matched dispatch pins
`6eb7da3a`/`015916f6`):

| Path | HEAD | WT (post-edit) | Copy (slot-2, fresh) |
|---|---|---|---|
| `.../rest_framework/serializer_converter.py` | `40cb765a48f47be79b768415c56bd9ed0f279176` | `d90b4a00f14d4095c686b3d3c62fb1d7474ba928` | identical to WT |
| `.../rest_framework/inputs.py` | `dfedd0e52901b0e344cf421887509caf2dcf663f` | `a4dbdb9023021e5b524d22784b411b020ed0d76e` | identical to WT |
| `tests/rest_framework/test_converter.py` | `4d5055405857c5117114c299a83ba62b8e1c709a` | `6a1054261a6829880c75044601ee08cdec6fb78e` | identical to WT |

Proof (which venv ran what): `uv run ruff check --fix` + `uv run ruff
format` scoped to the three touched paths, then `format --check` +
`check` on all three — pass (shared venv; the one reformat joined only
my own added assert). `uv run mypy` — clean, 119 files (shared venv;
slot-2 cannot run it — `mypy_extensions` missing from the damaged
venv). `uv run basedpyright` — 0/0/0 (shared venv; slot-2 reports only
missing-import noise from the same damage). `uv run python
scripts/check_any.py` — 130 uses at 90 sites, matches baseline
(workspace copy slot-2, run `dry-20261001T142301-9472ec`). Focused
`uv run pytest --no-cov -n0 -q` over the new pin + both call sites'
value pins + both adjacent-guard pins — 8 passed (shared tree, shared
venv; the single authorized run; the later docstring-only addition
changed zero code lines so the run stands on identical behavioral
bytes). No cast, `Any`, or suppression added; no `ALLOWED_ANY` move
owed (new symbol, no `Any`).

Ledger proposal for Worker-0 (plan untouched by Worker-1): three
`## Owned changes` rows (converter owner + composed site; inputs
composed site + import; test pin + import); index row
`serializer-source-axis-normalization` → `consolidated`; family row
ticked on verification.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (expectation-first; reconciled after).

### Own trace

Rule: the `source`-axis RECORDING rule — a serializer field's
`InputFieldSpec.source` is the one-segment `source` when explicitly
renamed, else `None` (falsy `source` or `source` equal to the declared
name folds to `None`; keeps the reverse map terse and form-symmetric).

Sites (pre-item bytes at `ITEM_BASELINE`, confirmed via
`git show <baseline>:<path>` + `git grep`):

- D1 (definition):
  `django_strawberry_framework/rest_framework/serializer_converter.py::resolve_serializer_field`
  — inline
  `source = field.source if (field.source and field.source != field_name) else None`
  (baseline `:1029`); `field_name` from `_bound_field_name(field)`.
- D2 (definition):
  `django_strawberry_framework/rest_framework/inputs.py::_resolve_nested_field`
  — byte-identical inline (baseline `:1515`); `field_name` is the walk
  effective-dict key passed as the `field_name` parameter.
- Guard (distinct rule):
  `django_strawberry_framework/rest_framework/serializer_converter.py::require_one_segment_source`
  — RAISING dotted/`source="*"` detection; both paths call it BEFORE the
  fold. Raises vs pure fold: different contract, stays separate.
- Effective-source resolver (distinct read):
  `django_strawberry_framework/rest_framework/serializer_converter.py::backing_model_field`
  `#"source = field.source if field.source else"` — answers WHICH
  attribute to resolve (falls back to the bound name, never folds to
  `None`); feeds `model._meta.get_field`. Different contract from the
  recording fold.
- Consumers of recorded `spec.source` (compose the value, never restate
  the fold): `django_strawberry_framework/rest_framework/resolvers.py`
  `#"schema_source = spec.source or target"` (+ `:1220`, `:1878`,
  `:1992`, `:2042`, `:2513` re-key basis);
  `django_strawberry_framework/rest_framework/inputs.py`
  `#"source_of=lambda spec: spec.source or spec.target_name"` (collision
  arm) + descriptor-identity reads (`:969`, `:1044`).
- Raw readers (never fold): fingerprint
  `django_strawberry_framework/rest_framework/inputs.py #"_fingerprint_field_map"`
  (`field.source` verbatim, `:522`); collision maps over raw
  `field.source` (`inputs.py` `:645`/`:664`, `sets.py` `:418`,
  `resolvers.py` `:1157`).

Definition counts per posited change (pre-item → post-item):

- C1 (drop the equal-name arm: record an equal `source` explicitly):
  D1 + D2 move → 2 → 1.
- C2 (falsy `source` records the declared name instead of `None`):
  D1 + D2 move → 2 → 1.
- C3 (change the comparison basis): the two sites spell different basis
  expressions (walk key vs `_bound_field_name`), both move → 2 → 1.
- Post-item sweep (own `grep` over the package + `git grep` at baseline):
  baseline carries the fold spelling exactly twice (`inputs.py:1`,
  `serializer_converter.py:1`); current tree carries it exactly once
  (the owner body). Remaining `source !=` / `!= field_name` hits are
  unrelated (`sets.py` key-match gate, `resolvers.py` agreement compare,
  `_strawberry_patches.py` / `list_field.py` non-serializer compares).
  No third spelling.

Owner I would choose:
`django_strawberry_framework/rest_framework/serializer_converter.py`,
as `normalize_serializer_source(field, field_name)`. It already owns
the source axis (`require_one_segment_source`, `backing_model_field`,
`resolve_serializer_field`), and `inputs.py` already imports converter
helpers (`is_nested_serializer_field`, `nested_serializer_child`,
`require_one_segment_source`) — housing the owner in `inputs.py` or a
third module would reverse or split that dependency. Threading
`field_name` as a parameter (not reading `field.field_name` inside) is
the correct shape: the two sites' bases are textually different
expressions.

Walk-key == bound-name claim (load-bearing for "one rule", verified
from the package's own build paths, not inherited):

- `effective` preserves keys end to end: `resolve_effective_fields`
  (`exclude`/un-narrowed re-emit basis keys; `fields`-branch selects
  `basis[name]`) ← `writable_serializer_fields` (key-preserving
  comprehension) ← one of three maps.
- The three maps all guarantee key == bound `field_name`: the hook map
  via `django_strawberry_framework/rest_framework/sets.py::_validate_schema_field_map`
  (`:204`-`:210` raises on mismatch);
  `get_serializer_for_schema` (`dict(serializer.fields)`) and
  `read_nested_serializer_fields` (`dict(serializer.fields)`) via DRF
  itself — installed `BindingDict.__setitem__` unconditionally runs
  `field.bind(field_name=key, ...)`, so every `.fields` key equals its
  field's bound name. Test `field_map=` values are likewise
  `dict(...().fields)`.
- `resolve_serializer_field` derives its basis internally via
  `_bound_field_name` on ALL three call paths (walk `:1337`, injected
  `:856`, runtime-agreement `resolvers.py:1303`), so it never depends
  on a dict key. Only `_resolve_nested_field` takes the walk key — and
  that key provably equals the bound name on every package build path.
- DRF `Field.bind` (installed source): explicit `source == field_name`
  asserts (redundant-source error), so the equal arm fires only on the
  bind default (`source=None` → `field_name`); `source=""` stays `""`
  (only `None` defaults), so the falsy arm is reachable and
  meaningful, and `""` yields `source_attrs == [""]` (passes the
  one-segment guard consistently on both paths).

Equivalence judgment (principle 8): the fold expression moved VERBATIM
(double `field.source` read included) into the owner; both call sites
evaluate it at the same program point (after the one-segment guard,
before spec construction) with the same argument values as before.
No short-circuit, exception, query/transaction, cancellation, or
observation axis is touched — the fold is a pure value-level
expression over already-bound attributes. Both sites pass `str`
bases. Behavior-preserving by construction; the new 3-arm test pins
the owner directly (see reconciliation).

### Reconciliation

Read `## Findings` after recording the trace above. Verdict: agree on
every material point; one record-precision correction applied in place
(not a defect).

- **Sites / roles / counts.** W1's D1 + D2 match mine exactly (same two
  baseline lines `:1029` / `:1515`, same bases). My C1-C3 and W1's C1-C3
  posit the same three changes with the same 2→1 counts. My guard /
  resolver / consumer / raw-reader distinctions map onto R7 / R1 /
  R2+R3+R5 / R4+R5 with no remainder; R6 (forms/model correctly absent)
  I had held at matrix axis 1 — agree it deserves the exclusion row,
  and its durable-home clause is present verbatim in the owner
  docstring (`#"form/model specs never set the axis"`).
- **Enumeration (all 9 rows re-derived member by member).** Row 1: 1
  post-edit, 2 pre-edit (confirmed via `git grep` at baseline) — but
  the cited `:712` is a docstring line at final bytes; the fold return
  is `:720` (the +8 shift is consistent with the post-run docstring
  expansion W0 flagged). Corrected in place. Row 2: exactly the 3
  `field.source if` sites (owner, `backing_model_field`, resolvers
  attestation). Row 3: 2 `source=` constructions (converter `:1131`,
  nested `:1531`), both fed by the owner. Row 4: 2 sourceless
  constructions (forms `:587`, mutations `:605` — bodies read, no
  `source` kwarg). Row 5: 1 def + 2 calls (converter `:745` via the
  column resolve, nested `:1511`). Row 6: 8 `or` reads (resolvers x6 —
  `:1219`, `:1220`, `:1878`, `:1992`, `:2043`, `:2513` — plus the
  collision `source_of` and the `write_source = source or name` key).
  Row 7: 5 raw readers (fingerprint, sets map, resolvers runtime map,
  describe check, shape token — all five bodies read). Row 8: 9
  value-pin asserts across the two call sites + owner (W1's "8+"
  holds). Row 9: 1 `GeneratedInputFieldSpec` by type. No row sampled.
- **Matrix.** All six axes re-derived: axis 1 read both flavors'
  constructions (sourceless, correct per the record contract); axis 2
  zero-count corroborated (0 async tokens in either host); axis 3 the
  consolidation itself; axis 4 the denormalizing readers consume the
  axis without recomputing the fold (verified at each body); axis 5
  oracles spell literal values (the new pin asserts `"name"`/`None`
  literals — it exercises the owner, it does not derive expectations
  from it); axis 6 the five constructions enumerated (4 + 1 by type).
- **Ownership.** Same owner, same principle-7 reasoning. Corroborated
  the load-bearing details W1 cites: `inputs.py` imports exactly 8
  names from the converter (counted), and the converter imports from
  no sibling `inputs` module (only `..mutations.inputs` /
  `..utils.inputs`) — the dependency is one-directional, so the
  converter is the narrowest owner no consumer is barred from.
  Threading `field_name` as a parameter is the correct shape for two
  textually different bases.
- **Equivalence + the walk-key claim.** Agree, verified independently
  (see trace): key-preserving narrowing over three maps that each
  guarantee key == bound name (hook map by explicit validator raise,
  `.fields` maps by DRF `BindingDict` unconditional re-bind), plus
  `resolve_serializer_field` deriving its basis internally on all
  three call paths. The fold moved verbatim to the same program
  point; no principle-8 axis is touched.
- **Exclusions.** R1-R7 each carry contract difference + trigger +
  durable-home clause; every home clause verified present in the
  owner docstring (recording-vs-reads paragraph, dotted/star
  paragraph, form/model sentence).
- **Proof / cells / gate.** Behavioral proof re-executed by me: 8/8
  green on my own re-derived node list (new pin + 3 converter value
  pins + nested-axis + identity-None + both guard pins) at final
  bytes. Cells `inapplicable by construction` accepted: a pure
  construction-time string fold reaches no queryset, alias, or
  dialect decision. No-gate accepted: a spelling census would be the
  bespoke existence test DRY.md forbids, and a correct future copy is
  future duplication rather than divergence — consistent with the
  cycle bar (sibling no-gate findings verified on the same reasoning).
  Absent `## Pending execution` is correct: nothing deferred, no gate
  relied on.
- **W0 point (a) (docstring after the test run).** MOOT: my own
  focused run executed at final bytes (WT pins unchanged since W1's
  table), so the verdict rests on fresh execution, not on the
  identical-behavioral-bytes argument. The argument is additionally
  consistent with the evidence (`:712`→`:720` shift matches a
  docstring expansion above the return).
- **W0 point (b) (shared venv for mypy/basedpyright).** ENDORSED: the
  gates read shared-tree source, which is the bytes under review
  (WT == W1's table 3/3, copy == WT 3/3 re-verified by me read-only,
  HEAD unmoved at `5c3496e0`); a copy run would measure identical
  bytes through a damaged venv. Re-ran all three myself in the
  shared venv: mypy clean (119 files), basedpyright 0/0/0, check_any
  130/90 — all match W1. No new cast/`Any`/suppression in the item
  diff; no `ALLOWED_ANY` move owed.
- **Diff hygiene.** Item diff vs `ITEM_BASELINE` is exactly the 6
  claimed hunks (+ plan line); converter shows 21 HEAD hunks vs 2
  item hunks, all item hunks on clean lines. Banned-token sweep of
  the item diff: zero hits. Citations use `path::Symbol`. New test
  pins the owner (not the old spelling), mirrors the adjacent
  guard-owner test, and sits at the correct tier: the owner line is a
  straight-line return already executed by every pre-existing live
  serializer build (renamed-source fixtures exist in fakeshop), so
  the `tests/` pin adds arm precision, not uncovered lines. No
  existing oracle was touched, let alone rewritten to read the owner.
- **Defects.** None found; nothing filed. The examined-and-cleared
  falsy-arm note is endorsed (DRF `bind` semantics verified against
  the installed source: explicit `source=""` survives, explicit
  equal-source asserts).

W2 verdict: `verified` (plain — no `proof:` entry remains).

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
