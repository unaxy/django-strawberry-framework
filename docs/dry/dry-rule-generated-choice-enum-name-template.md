# DRY review: `generated-choice-enum-name-template`

Status: verified
Run: 0.0.15 2026-10-01-11

Item kind: FAMILY (responsibility family). Verdict CONFIRM +
BLOCKED: the generated choice-enum name template has two
authoritative definitions (the model-side and serializer-side
template f-strings, count 2 on all three variation axes), but
the model-side line sits inside an uncommitted concurrent
except-`BaseException`-deletion hunk, so the consolidation is
blocked with the migration specified and zero edits. Eight
exclusions carry contract difference + trigger each, with
specified durable-home clauses. Zero defects.

## System trace

The target owns the generated choice-enum GraphQL name:
`<TypeName><FieldName>Enum`, where the stem is
`pascal_case(field_name)` and the suffix is the literal `Enum`.
The rule varies on suffix spelling, stem derivation, and
assembly; the two inputs (`type_name`, field name) are data,
not variation.

Pre-block, two authoritative definitions spell it:

- `django_strawberry_framework/types/converters.py::convert_choices_to_enum`
  (WT :788, HEAD :801): `enum_name =
  f"{type_name}{pascal_case(field_name)}Enum"` with `field_name
  = field.name` — the model-choice path, cached in `registry`
  by `(model, field_name)`.
- `django_strawberry_framework/rest_framework/serializer_converter.py::_serializer_choice_enum`
  (WT :961, HEAD :935): `enum_name =
  f"{type_name}{pascal_case(_bound_field_name(field))}Enum"` —
  the serializer-only `ChoiceField` path, cached in
  `_SERIALIZER_CHOICE_ENUMS` by name.

Both already compose the stem (`pascal_case`) and the build
core (`build_enum_from_choices`) by name; only the
template assembly itself is spelled twice. The name-basis
difference (`field.name` vs `_bound_field_name(field)`) is a
caller-side input difference, not a rule difference: each is
the field's own name string in its domain, and the shared
`(type_name, field_name)` signature erases it legitimately.

Read whole or in the cited regions at current bytes (HEAD
`dd0b6691` + working tree): both host modules whole; the
stem owner (`utils/strings.py::pascal_case`); the build core;
every consumer body (filter importer, model-write delegate,
form imports, `types/base.py` threading, the list-wrap and
dedupe arms); every cache body; the set-family namer; the
static-enum kind lines; all oracle bodies cited; spec-039
Slice/Decision rows; both GLOSSARY enum anchors. The file
artifacts that named this family and the f35/f36 records were
orientation only: every site, count, and exclusion below was
re-derived fresh at current bytes, never inherited.

Dirt: the two indexed files carry 35 hunks vs HEAD, all
attributed by diff content (f35 ledger 2, concurrent
truth-migration / except-narrowing / behavior /
except-`BaseException` deletions 33; zero unattributed). The
serializer template body is byte-identical across states
(zero hunks span it). The model-side template line carries
the blocking hunk (indentation changed with the deleted
`try`). Full attribution in `## Implementation (Worker-1)`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched, all write
   flavors read. Model (`types/converters.py`, D1) and
   serializer (`serializer_converter.py`, D2) each spell the
   template once. Filters compose D1 by name (local import +
   call, verified at the bodies). Model writes route through
   `convert_scalar` (verified). Forms import from
   `mutations/inputs.py` and carry zero enum machinery (0
   `Enum` hits in `forms/`, verified). `types/base.py`
   threads `type_name` into the read-output entry point
   (verified). `orders/inputs.py::Ordering` is hand-declared
   (R7). No third template exists in any flavor.
2. **Sync/async twins.** Inapplicable with reason: the rule
   is a pure string interpolation over two bound strings —
   zero `async def` / `await` / `sync_to_async` in either
   host module (grep count 0 at current bytes). Both hosts
   run at finalize / input-construction time, never across
   an await boundary. No twin exists to compare.
3. **Derived rather than repeated knowledge.** Found and
   confirmed: the two template f-strings derive the same
   name by identical inline spelling. Post-block census:
   exactly two template-expression code sites package-wide
   in both states (D1 + D2); every other `Enum` hit is a
   consumer, oracle, projection, or static enum.
4. **Inverse / round-trip pairs.** Searched: no inverse
   exists. The registry keys by `(model, field_name)` and
   never parses names; the serializer dedupe compares
   member maps, never parses; the inspect command reads
   `StrawberryEnumDefinition` for display (projection).
   `relay-node-name-decode` decodes the `GlobalID` grammar,
   a different rule. Generated enum names are write-only
   identifiers; no half is missing, no half restated.
5. **Contracts restated in another medium.** Inventoried
   with roles: production (2 definitions); contract
   sources (spec-039 serializer-enum rows; the
   `convert_choices_to_enum` docstring step 2; the
   `convert_scalar` docstring naming clause; the
   `utils/strings.py` module-docstring consumer note);
   independent oracles (2 unit name pins, 3 serializer
   enum-shape asserts + 1 non-enum exclusion assert,
   registry cache pins, 3 live SDL rows —
   all spell VALUES, none reads the template); projections
   (module docstrings, SDL names, the GLOSSARY
   `Choice enum generation` anchor, the planned-override
   anchor). A template change moves production + value
   oracles together by design; oracles listed, never
   counted.
6. **Enforcement by omission.** Enumerated: every
   enum-producing site carries the template — model path
   (D1), serializer path (D2) — or composes it (filters,
   model writes, forms-by-routing). Static enums are
   correctly ungenerated (R7). No producer lacks the rule;
   no omission defect filed.

### Enumeration

Instrument: literal + regex search over
`django_strawberry_framework/` (117 tracked `.py` files per
the run-11 census + the 2 untracked concurrent
`utils/truth.py` / `utils/lazy.py`, zero template hits in
both) at WT bytes via `muse.search` plus `git grep` over
HEAD for the same populations, plus full reads of both
hosts and every consumer / cache / oracle body cited.
Counts below are matches at current bytes unless marked
HEAD; every one homed.

- `}Enum` (template-expression spelling): 3 hits WT — 2
  code (D1 :788, D2 :961; F1) + 1 ``...`` prose (the
  docstring step 2). HEAD: 3 hits — 2 code (D1 :801, D2
  :935) + 1 prose. Same population shape, line shifts
  only. No hidden spelling.
- `Enum"` concatenation / `.format` variants: 0 both
  states (no second spelling mechanism).
- `<TypeName><FieldName>Enum` prose: 2 hits (the
  `convert_scalar` docstring clause + the `utils/strings.py`
  module note; projections).
- `pascal_case` type-name consumers: the 2 template sites
  (F1) + the Range input namer (R1) + the set-family
  namer via `pascal_case_or_raise` (R3). No other caller
  mints a type name from it.
- Enum-construction sites: 1 (`build_enum_from_choices`,
  R8, already single-owned).
- Enum-cache key spaces: 2 (registry `(model, field)` +
  `_SERIALIZER_CHOICE_ENUMS` name-keyed; R5).
- Static (hand-declared, ungenerated) enums: 10
  classes (closed `^class .*(Enum)` census; R7).
- Oracle files: 5 (2 unit files + registry + resolvers +
  1 live file; roles in F1).
- `choice_enum_names` in the package: 0 (GLOSSARY-planned
  override input, not a current site).
- Excluded on body strength (read, no second site):
  `filters/inputs.py` (consumer), `mutations/inputs.py`
  (consumer), `forms/inputs.py` (routes via mutations),
  `types/base.py` (threads `type_name`), `registry.py`
  (caching, not naming), `sets_mixins.py` (R3),
  `utils/strings.py` (stem owner), `orders/inputs.py`
  (R7), `utils/inputs.py` (R2 separation via the
  verified f36 record which stands; `pascalize_token`
  body read fresh).

### Challenges

Each rule in the family: changes posited,
authoritative-definition counts (consumers, oracles,
projections listed, never counted). Pre-consolidation
agreement is `execution-verified` (one focused run, 5
passed — both templates' documented names observed live;
command in `## Implementation`); the migration
equivalence is `static-reviewed` (pure interpolation,
same-typed inputs, no behavior axis); post-migration
oracle green is `execution-deferred` (see
`## Pending execution`).

- H1 (suffix spelling: rename `Enum`, e.g. to
  `ChoiceEnum`): count **2** — D1 :788 + D2 :961.
  Riders: the name-keyed serializer cache (keyed by the
  value, follows), value oracles, SDL projections.
- H2 (stem derivation: the template takes a different
  stem, e.g. a flattened or guarded one): count **2** —
  both `pascal_case(field_name)` call positions. (A
  `pascal_case` behavior change moves 0 here — owned by
  `utils/strings.py`, already composed by name.)
- H3 (assembly: `<Type><Field>Enum` gains a separator or
  reorders): count **2** — both f-strings. Same riders
  as H1.
- H4 (Range input suffix change): count **0 here** — the
  Range namer moves once (R1 owner); neither F1
  definition moves. Proves R1 is not a second definition
  of THIS rule.
- H5 (provisional / input-name suffix change): count **0
  here** — the f36 owner moves once; the template
  consumes the VALUE it receives. Proves R2 is a
  consumer relationship, not a shared rule.
- H6 (set-family suffix change): count **0 here** — the
  mixin moves once (R3 owner). Proves R3 is separate.

## Findings

### F1 — generated choice-enum name template (CONFIRMED duplication, blocked)

- **Contract + variation.** The generated choice-enum
  GraphQL name `<TypeName><FieldName>Enum`: stem is
  `pascal_case(field_name)`, suffix is `Enum`,
  assembly is direct concatenation. Varies on suffix,
  stem derivation, and assembly; inputs are two plain
  strings.
- **Sites + roles.** Definitions: D1
  (`types/converters.py::convert_choices_to_enum` line)
  + D2
  (`rest_framework/serializer_converter.py::_serializer_choice_enum`
  line). Consumers (compose the VALUE or the producing
  functions by name): the `convert_scalar` choices arm,
  `_choice_enum_from_filter`, `model_column_write_annotation`,
  the form/model write paths by routing, the
  `types/base.py` `type_name` threading,
  `_serializer_choice_annotation` (list-wrap), the
  serializer dedupe arm, both caches. Oracles: 2 unit
  name pins (`FixtureTypeStatusEnum`,
  `FixtureTypeAStatusEnum`), 3 serializer enum-shape
  asserts + 1 non-enum exclusion assert, registry cache
  pins, 3 live SDL rows
  (`BookTypeCirculationStatusEnum`,
  `ShelfMetadataSerializerInputPriorityEnum`), the
  injected-choice provisional prose pin. Projections:
  the three docstring naming clauses, spec-039 rows,
  SDL names, both GLOSSARY enum anchors.
- **Challenges.** H1/H2/H3 -> **2** each (D1 + D2);
  H4/H5/H6 -> 0 here (each moves its own owner once).
- **Owner + lifetime.**
  `types/converters.py::choice_enum_name` (new, beside
  `build_enum_from_choices`) by principle 7: the module
  already owns the enum-build core both paths compose,
  owns the model-side naming today, and is the
  narrowest cohesive owner every legitimate consumer
  can import — the serializer module already imports
  three names from it, so the migration adds a NAME to
  an existing import, no new module edge, no cycle
  (`types/converters.py` imports nothing from
  `rest_framework`). Rejected: the serializer module
  (reverses the dependency AND cycles:
  `serializer_converter` imports `types.converters` at
  top level); `utils/strings.py` (substrate coupling —
  an enum-domain rule does not belong to generic
  case-conversion; the stem already composes from there
  by name); `registry.py` (owns caching, not naming,
  and only the model key space). Lifetime (principle
  4): pure derivation, not cached — no stored state, no
  validity key, no publish point.
- **Migration (specified, not applied — blocked).**
  Against current bytes the new owner beside
  `build_enum_from_choices` is `def
  choice_enum_name(type_name: str, field_name: str) ->
  str` returning `f"{type_name}{pascal_case(field_name)}Enum"`
  with the naming-responsibility docstring (carrying
  the R-home clauses below); D1 becomes `enum_name =
  choice_enum_name(type_name, field_name)`; D2 becomes
  `enum_name = choice_enum_name(type_name,
  _bound_field_name(field))` with `choice_enum_name`
  added to the existing `from ..types.converters
  import (...)` at `serializer_converter.py:80`; the
  f36-R2 clause lands on `_serializer_choice_enum`.
  Behavior-identical: same interpolation, same stem
  function, same-typed string inputs at the same
  program points (after cache lookup, before build),
  no short-circuit, exception, query, transaction,
  cancellation, or observation axis touched. The
  unblocking change reconciles the D1 line with the
  landed concurrent deletion at application time and
  lands the owner test (one direct pin of the template
  over two bases, mirroring the adjacent owner tests)
  plus the R-home clauses.
- **Distinct behavior.** Nothing stays separate inside
  F1: each call site keeps passing its own name basis
  (`field.name` vs `_bound_field_name`); only the
  assembly composes the owner.
- **Behavioral proof.** `execution-verified`
  (pre-consolidation agreement): the focused 5-node run
  observes both templates' documented names live (2
  model unit pins + the serializer live SDL pin +
  both serializer shape paths). Rejects "the two sites
  spell different grammars" (all five green on the
  same bytes) and "the serializer template output
  differs from its SDL contract" (the live row pins
  the exact SDL name). `static-reviewed` (migration
  equivalence): closed two-site census at both states
  + the pure-interpolation legs above. `execution-deferred`
  (post-migration oracle green) → the `proof:` entry.
- **Structural gate (specified, not landed — blocked).**
  A spelling census over the package: exactly one
  template-expression spelling outside ``...`` prose
  (the owner body), plus both call sites composing
  `choice_enum_name` by name. Negative control: a
  behavior-preserving hand copy of the owner body at
  one call site passes every behavior oracle (it
  computes the same string) and fails ONLY the census
  — proving the census, not the behavior pins, guards
  the single-sourcing. The unblocking change lands it
  beside the migration and shows it red-then-green via
  `prove_failability.py`. Not landed now: a count-1
  census would be born red (count is 2 today), and a
  gate born red gets weakened, not fixed.
- **Coupling.** None with any other family: one new
  function + two one-line call-site swaps + one import
  name. Blocked solely on the concurrent hunk below
  resolving (landing or the maintainer ruling); the migration must
  not be hand-applied over uncommitted concurrent bytes.
- **Freshness.** Indexed 2: `types/converters.py` WT
  `97f3399e` HEAD `312bd290`; `serializer_converter.py`
  WT `a22dcbe3` HEAD `469a4959` (`git hash-object` WT
  vs `git rev-parse HEAD:path`; HEAD `dd0b6691`
  unmoved; dispatch pins match). Copy (slot-2, fresh):
  identical to WT on both files. Connected pins + the
  no-new-files statement in `## Implementation
  (Worker-1)`. Any fingerprint change reopens this
  finding.
- **Blocked on concurrent dirt (exact hunk, nothing
  touched).** The consolidation must rewrite the D1
  line, whose worktree bytes carry an uncommitted
  concurrent except-`BaseException`-deletion hunk (the
  expression identical, the `try` wrappers gone):

```diff
@@ -784,31 +779,14 @@ def convert_choices_to_enum(field: "ConcreteField", type_name: str) -> type[Enum
-    try:
-        model = field.model
-        field_name = field.name
-        choices = field.choices
-    except BaseException as exc:
-        raise ConfigurationError(
-            f"Could not inspect choices for {_field_label(field)}.",
-        ) from exc
-
+    model = field.model
+    field_name = field.name
     cached = registry.get_enum(model, field_name)
     if cached is not None:
         return cached

-    try:
-        enum_name = f"{type_name}{pascal_case(field_name)}Enum"
-    except BaseException as exc:
-        raise ConfigurationError(
-            f"Could not derive an enum name for {_field_label(field)}.",
-        ) from exc
-    try:
-        choice_source = choices or []
-    except BaseException as exc:
-        raise ConfigurationError(
-            f"Could not inspect choices for {_field_label(field)}.",
-        ) from exc
+    enum_name = f"{type_name}{pascal_case(field_name)}Enum"
+    choice_source = field.choices or []
     enum_cls = build_enum_from_choices(
```

Attribution: pure `except BaseException` arm deletion
(three `try` wrappers removed, zero `truth.` vocabulary
introduced, zero ledger match) — the maintainer's named
concurrent deletion population. The template line itself
moved from 8-space (HEAD :801, inside `try`) to 4-space
(WT :788) with the hunk, so the exact line the
consolidation must rewrite carries uncommitted
concurrent bytes. Per the binding concurrency rule the
item stops here: hunk recorded, tree untouched. Every
viable owner shape rewrites this line (verified for the
serializer-module, `utils/strings.py`, and
`types/converters.py` placements alike), so no partial
landing exists.

### R1 — Range / prefix input naming (REJECTED, stays at the namer)

`filters/inputs.py` mints
`f"{prefix}{_pascal_case(field_name)}RangeInputType"` for
per-field range inputs. Shared form considered: one
`<Type><Field><Suffix>` helper — refused: different
suffix, different subject (range inputs vs enums),
different reasons to change (filter-input identity vs
enum identity). Challenge H4 moves only the Range namer
(count 1). **Contract difference:** range-input naming
vs enum naming. **Trigger:** a flavor unifying enum
names with input names, or a second `<Type><Field>Enum`
producer. **Durable home (specified):** one clause on
the new owner ("range / bag / set input names are their
owners' rules; only the `Enum` template lives here").

### R2 — provisional / input naming (REJECTED, consumer relationship)

`generated_input_type_name` (`<Base>Input` /
`<Base>PartialInput`, the f36 owner) and the divergent
deriver produce the `type_name` VALUES the template
consumes. Shared form considered: route enum naming
through the provisional owner — refused: the template
consumes a string, never derives partiality or shape;
it cannot distinguish a provisional from any other
`type_name`. Challenge H5 moves only the f36 owner
(count 1). The sibling `pascalize_token` encoder feeds
the divergent digest token, never a type name
(body-read: escape-heavy token encoding, deliberately
distinct from `pascal_case`; 0 enum production).
**Contract difference:** enum derivation
from a name vs provisional-name production. **Trigger:**
a second enum-name producer (per the verified f36 R2,
which named this family as its durable home).
**Durable home (specified):** one clause on
`_serializer_choice_enum` ("the `type_name` arrives
precomputed; this template never derives partiality")
— rides this family, lands with the unblock.

### R3 — set-family `InputType` naming (REJECTED, different rule)

`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`
owns `{cls}InputType` (+ per-field `{cls}{Pascal}InputType`)
for set families (cookbook parity). Shared form
considered: one cross-family naming helper — refused:
different suffix, different subject (set classes vs
generated enums), different reasons to change. Challenge
H6 moves only the mixin (count 1). **Contract
difference:** set-class naming vs enum naming.
**Trigger:** a flavor unifying set names with enum
names. **Durable home (specified):** covered by the R1
owner clause ("set input names are their owners'
rules").

### R4 — member-name sanitization (REJECTED, different grammar)

`_sanitize_member_name` owns the member grammar (value
coercion, ASCII rewrite, digit / keyword / reserved /
enum-private rewrites). Shared form considered: one
enum-spelling helper — refused: member spelling vs
enum-name assembly vary independently (a new reserved
word moves only the member rule; H1–H3 move only the
template). The member rule already takes `enum_name`
for the private-namespace check — a read, not a
definition. **Contract difference:** member grammar vs
name template. **Trigger:** a member-spelling change
that must move the template, or the template deriving
from member state. **Durable home (specified):** one
clause on the new owner ("member spelling lives at
`_sanitize_member_name`; only the enum-name assembly
lives here").

### R5 — enum cache keyings (REJECTED, storage vs naming)

`registry` `(model, field_name)` keying vs
`_SERIALIZER_CHOICE_ENUMS` name keying. Shared form
considered: one enum cache — refused (already rejected
at the file artifact as
`serializer-enum-cache-vs-registry-cache`, re-derived
here on fresh bytes): a serializer-only choice has no
model, so the key spaces are intentionally separate;
caching answers WHERE the enum is kept, the template
answers WHAT it is named. **Contract difference:**
storage keying vs name assembly. **Trigger:** a
model-less enum gaining a `(model, field)` key or vice
versa. **Durable home:** existing (both cache
docstrings + the file-artifact rejection); no new
clause owed.

### R6 — `type_name` inputs (REJECTED, inputs not definitions)

Declared class names, provisional names, `__name__`
reads — every value the template interpolates. Shared
form considered: template deriving its own base —
refused: each input site owns its base vocabulary (the
f36 separation generalized); H5 proves a base-vocabulary
change moves the producer once with the template
following as a consumer. **Contract difference:**
base-vocabulary production vs template assembly.
**Trigger:** an input site recomputing the template
instead of passing the base. **Durable home
(specified):** one clause on the new owner ("callers
supply `type_name` from their own vocabulary; only the
assembly lives here").

### R7 — static enums (REJECTED, ungenerated by kind)

`_request_body.py::_Probe`, `auth/sessions.py::Transport`,
`optimizer/join_taxonomy.py::LateralJoinShape`,
`orders/inputs.py::Ordering`,
`registry.py::_GlobalIDSettingUnset`,
`relay.py::GlobalIDDecode`,
`types/converters.py::_Missing`,
`utils/connections.py::FetchMode`,
`utils/execution_mode.py::OperationMode`,
`utils/querysets.py::_WalkState` — the closed
`^class .*(Enum)` census (10 classes), all
hand-declared, none generated, none spelling the
template (the `}Enum` census proves it). **Contract
difference:** declared vocabulary vs generated naming.
**Trigger:** a static enum becoming generated.
**Durable home:** none owed (kind difference, recorded
here).

### R8 — enum build core (REJECTED, already single-owned)

`build_enum_from_choices` owns the build grammar
(empty / grouped-form rejection, value sanitization,
collision guard, `Enum` construction + `strawberry.enum`
decoration). It takes `enum_name` as a PARAMETER and
never derives a name — the template is its caller-side
input, not part of it. **Contract difference:** build
grammar vs name input. **Trigger:** the core deriving
a default name. **Durable home:** none owed (the
parameter shape IS the contract; both paths already
compose it).

No new sub-rule index rows owed: the family is atomic
(F1); R1/R3 home to their existing file-local rows, R5
to its existing rejected row, R2 to the verified f36
record, R4/R6 to specified owner clauses, R7/R8 to no
row by kind. Worker-0 adds nothing.

## Defects

None found. The trace covered both template sites, the
stem, the build core, both caches, every consumer,
every oracle body, the kind vocabulary, and both
contract sources — no docstring contradicts its body,
no producer lacks the template, no layering claim
fails. Examined and cleared (not filed): the empty-stem
edge (both bases are non-empty by construction — a
bound Django field name / bound DRF field name is never
empty, so `pascal_case` never yields `""` here); the
serializer same-name-different-members arm (fails loud
by design); the model first-`DjangoType`-wins naming
(the documented contract, with the planned
`Meta.choice_enum_names` override anchor). Concurrent
dirt is concurrent work, not filed.

## Pending execution

- `proof: uv run python scripts/workspace.py run
  dry/genenum-f37/consolidate -- pytest
  tests/types/test_converters.py
  tests/rest_framework/test_converter.py
  "examples/fakeshop/test_query/test_library_api.py::test_create_shelf_via_metadata_serializer_expanded_input_type_system_over_http"
  -n0 --no-cov -q` (discharges F1's post-migration
  behavioral proof once the block clears: both oracle
  files + the live serializer-enum SDL row green
  post-migration; runnable only after the unblocked
  consolidation lands; nodes validated by existence —
  5/5 executed green in the agreement probe).
- Sharded cell: `unverified` but `inapplicable by
  construction` (Worker-2 judges): the rule is a pure
  string derivation — both template lines and the
  specified owner touch no database, alias, or dialect
  decision (both caches are in-process dicts). PG cell:
  same reasoning, `unverified` / `inapplicable by
  construction`.
- No `gate:` witness owed: a green unmutated suite would
  discharge nothing for a blocked finding.

## Judgment

The family is one real duplication plus settled
single-ownership. F1 CONFIRMED: the model-side and
serializer-side template f-strings spell the same
`<Type><Field>Enum` rule with no load-bearing
difference on any of the three variation axes — but
the model-side line carries an uncommitted concurrent
hunk, so the consolidation is blocked, recorded above,
with zero files changed. Eight rejections (R1–R8) each
carry a concrete contract difference, a trigger, and a
specified (or existing) durable home. No defect, no
ticked row disturbed, no new index row owed.

## Implementation (Worker-1)

Tracked changes: NONE (blocked on concurrent dirt;
zero edits). The item diff vs
`ITEM_BASELINE=3a98ee6593b25eb74d1ab3c59d204e74a2142ac5`
on every touched path is empty (the only baseline
delta tree-wide is Worker-0's own +146 plan lines);
the artifact is untracked (`??`). Every other delta in
the tree is concurrent dirt, attributed below by diff
content and left alone.

Attribution (35 hunks vs HEAD across the 2 indexed
files — full diffs read hunk by hunk; zero
unattributed):

- `types/converters.py` (14 hunks): all concurrent —
  the maintainer's `except BaseException` arm
  deletions (incl. the blocking `@@ -784,31 +779,14
  @@`) plus hunt truth-migration vocabulary
  (`truth.*`, `_safe_*` removal, `_class_map_lookup`
  machinery with 0 hits at HEAD) and hunt
  except-narrowing. Zero ledger rows cover this path.
- `rest_framework/serializer_converter.py` (21 hunks):
  2 are the f35 ledger (`normalize_serializer_source`
  def hunk + the `resolve_serializer_field` call-site
  swap — both match the `## Owned changes` rows
  verbatim, built on by nothing, never re-touched).
  The other 19 are the concurrent campaign:
  truth-migration swaps, `except BaseException`
  deletions, hunt behavior (`allow_null` list-child
  widening, `allow_blank` enum exclusion, `_scalar_name`
  re-derivation). The `_serializer_choice_enum` body
  (WT :948–979) is byte-identical to HEAD (:922–953).

Fingerprints (HEAD `dd0b6691` unmoved; dispatch pins
match; copy = slot-2 fresh, shared unmoved since
sync; `git hash-object` WT/Copy vs `git rev-parse
HEAD:path`):

| Path | HEAD | WT | Copy |
|---|---|---|---|
| `.../types/converters.py` | `312bd290` | `97f3399e` | identical to WT |
| `.../rest_framework/serializer_converter.py` | `469a4959` | `a22dcbe3` | identical to WT |

Connected pins (WT / HEAD): `filters/inputs.py`
`993f365c` / `08516597`; `forms/inputs.py` `65ac558f` /
`0ba0d9a5`; `forms/converter.py` `52b10986` /
`a70fe126`; `mutations/inputs.py` `fe2218dd` /
`fd0f17d8`; `types/base.py` `e7a62d32` / `e0ad32aa`;
`utils/strings.py` `f5ce0784` / `a326167d`;
`utils/inputs.py` `0826c9d4` / `0b7d353c` (token-encoder
body only); `registry.py` `e95c39e7` / `5480c2eb`;
`sets_mixins.py` `c496feb2` / `42e8c862`;
`orders/inputs.py` `2f6e1a2c` / `c7a91946`;
`tests/types/test_converters.py` `ddf24f59` /
`c2ff9fca`; `tests/rest_framework/test_converter.py`
`6a105426` / `4d505540` (WT matches the f35 post-edit
pin); `tests/test_registry.py` `55b3aed8` /
`b1fbede4`; `tests/rest_framework/test_resolvers.py`
`0c64d6d4` / `a9162094`;
`examples/fakeshop/test_query/test_library_api.py`
`77eeacca` / `434c639e`; `docs/GLOSSARY.md` `cf0ad0bf`
/ `cf0ad0bf` (clean);
`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`
`cf78af93` / `cf78af93` (clean). Untracked
`utils/lazy.py` (40 lines): 0 `Enum`, 0 `pascal_case`
(direct grep; `git grep` is blind to untracked files).

Proof (which venv ran what): focused `uv run pytest
--no-cov -n0 -q` over the 5 agreement nodes (2 model
name pins + 2 serializer shape paths + the live
serializer-enum SDL row) — 5 passed in 3.05s (shared
tree, shared venv; the single authorized run). Type
gates in the workspace copy (slot-2): `basedpyright`
0 errors, 0 warnings, 0 notes (run
`dry-20261001T161746-1b523c`); `check_any.py` 128 uses
at 89 sites, matches the run-11 baseline (run
`dry-20261001T161756-c27e33`); `check_truthful_reads.py
--check` tier-1 0, errors 0 (run
`dry-20261001T161756-0a7af7`). Ruff vacuous (zero
tracked `.py` touched). No cast, `Any`, or suppression
added or needed; no `ALLOWED_ANY` move owed (no
symbol moved). mypy never run (gone).

Ledger proposal for Worker-0 (plan untouched by
Worker-1): no `## Owned changes` rows (zero edits); no
new index rows (family atomic, §R-home note above);
family row → blocked pending the concurrent hunk
(Wording is Worker-0's; f33/f36 precedent is the
`blocked-on-hunt` record shape with an exact hunk).

## Independent verification (Worker-2)

Own trace, derived before opening `## Findings`
(HEAD `dd0b6691` + working tree, both host modules read
whole). Instrument `}Enum` over the package: 3 WT (2
code + 1 docstring prose) / 3 HEAD, same shape, line
shifts only. Concat / `.format` spellings 0.
`pascal_case(` type-name minters: exactly the 2
template sites + the Range namer + the set-family
namer (both via `pascal_case_or_raise`). Enum
construction 1 site (the build core). No inverse
parse anywhere. Forms carries 0 `Enum` hits and
routes via `mutations/inputs.py`; filters, model
writes, the serializer model-backed arm, and the
`inputs.py` provisional threading all consume the
producing functions or the name VALUE by name.

Definitions: D1 the model-side f-string
(`types/converters.py::convert_choices_to_enum`,
WT :788 / HEAD :801 inside `try`), D2 the
serializer-side f-string
(`rest_framework/serializer_converter.py::_serializer_choice_enum`,
WT :961 / HEAD :935) — count 2. Own challenges: C1
suffix rename, C2 stem-rule change, C3
prefix/assembly change — 2/2/2, riders (name-keyed
cache, value oracles, SDL projections) listed never
counted. Owner I choose: new
`types/converters.py::choice_enum_name(type_name,
field_name)` — the module owns the enum-build core
both paths already compose, the serializer module
already imports three names from it (migration adds
a NAME, no new edge, no cycle), narrowest cohesive
owner; `utils/strings.py` refused (generic
substrate; the rule is enum-domain). Block I
re-derive from `git diff HEAD`: hunk
`@@ -784,31 +779,14 @@` is an
except-`BaseException` deletion moving the D1 line
8sp→4sp; zero ledger rows cover the file, so it is
concurrent (the maintainer campaign); the
serializer file carries 19 concurrent + 2
f35-ledgered hunks with the D2 body byte-identical.
Zero legal partial landings: every owner placement
rewrites the D1 line or edits a file with external
hunks, and an owner without call-site composition
relieves no change obligation.

Reconciliation: full agreement on sites, both-state
lines, counts, owner + principle-7 reasoning, and
the rejection set (R1/R3/R4/R5/R7/R8 named
independently; R2/R6 accepted as legitimate
adjacent exclusions, each with contract difference
+ trigger). Non-defect notes: (a) the `+146 plan
lines` count is stale by Worker-0's later
`W1 submitted` paragraph (I measure +169) —
Worker-0's own section, already validated; (b) the
`3 live SDL rows` map to the three SDL-name value
rows; oracles are never counted; (c) W1's `family
row → blocked` proposal is wording only — f33/f36
precedent ticks this shape `verified` /
`verified, pending execution`; with one `proof:`
entry remaining the plan marking should be
`verified, pending execution` (Worker-0's edit, not
mine).

Checks run by me: Enumeration re-derived
member-by-member — all rows match (3/3 spelling, 0
variants, 2 prose, 4 stem consumers, 1 build site,
2 caches, 10 static enums matched by name, 5
oracle files, 0 `choice_enum_names`, exclusions
re-verified at the key bodies). Matrix: axis 1
searched, axis 2 inapplicability confirmed (0
async markers in both hosts), axis 3 = F1, axis 4
searched (inspect reads `StrawberryEnumDefinition`
for display only), axis 5 inventoried with oracle
independence verified (values spelled, never
computed via `pascal_case`), axis 6 enumerated (no
producer lacks the rule). Freshness: indexed pins
re-hashed same-kind (`hash-object` WT
`97f3399e`/`a22dcbe3`, `rev-parse HEAD:path`
`312bd290`/`469a4959`) — match; 5 connected pins
spot-re-hashed — match. Gates re-run in the shared
venv: basedpyright 0/0/0, check_any 128/89,
truthful-reads tier-1 0 errors 0 — all match the
run-11 baseline and W1's slot-2 results; mypy
never run; ruff vacuous (zero tracked `.py`
touched). Agreement probe re-run by me: 5 passed
in 3.02s (same 5 nodes). `proof:` entry typed
correctly with nodes existing (2 files + 1 live
test def); not executed (meaningful only
post-migration); no `gate:` owed — correct.
Sharded/PG `inapplicable by construction`
ENDORSED (pure string derivation, in-process
caches). Structural gate specified-not-landed
judged CORRECT (a count-1 census is born red;
negative-control reasoning sound). R1–R8 each
carry contract difference + trigger +
specified/existing home; specified homes ride the
unblocking change. Zero-edit confirmed (item diff
vs `ITEM_BASELINE` is the plan edit alone; no new
`.py` from W1; no oracle rewritten). Banned-word
sweep: artifact hits are DRY-mandated role labels
only; zero test/production violations. Defects:
none (W1's 3 examined-and-cleared endorsed).

Verdict: verified (pending execution via the one
`proof:` entry).

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
