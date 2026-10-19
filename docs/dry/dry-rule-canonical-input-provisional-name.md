# DRY review: `canonical-input-provisional-name`

Status: verified
Run: 0.0.15 2026-10-01-10

Item kind: FAMILY (responsibility family). Verdict CONFIRM +
BLOCKED: the canonical-input provisional-name rule has two
authoritative definitions (the shared namer + the guard's
concatenation restatement, count 2 on all three variation axes),
but the restated line carries an uncommitted hunt hunk, so the
consolidation is `blocked-on-hunt` with the migration specified
and zero edits. Six exclusions carry contract difference +
challenge + trigger each, with specified durable-home clauses.
Zero defects.

## System trace

The target owns the canonical generated-input provisional name:
`<Base>Input` / `<Base>PartialInput` for the full shape, seeding
serializer-only choice-enum names during the field walk. The rule
varies on `is_partial` only; the base is input, not variation.

Pre-block, two authoritative definitions spell it:

- `django_strawberry_framework/utils/inputs.py::generated_input_type_name`
  (WT :1065-1088, HEAD :1058-1081, byte-identical): the documented
  "load-bearing skeleton the three flavors' input-name derivers
  share" - suffix conditional + full-vs-divergent branching.
- `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`
  (WT :1306, HEAD :1294): the runtime-agreement guard rebuilds the
  same name by concatenation,
  `f"{<base>}{'PartialInput' if operation == 'update' else 'Input'}"`,
  as the `type_name` argument to its `resolve_serializer_field`
  re-derivation - the literal principle-6 violation shape ("never
  rebuilds the name by concatenation").

Five composed calls (census closed in both states, every one read):
`rest_framework/inputs.py` walk provisional (WT :1710, HEAD :1711),
injected-specs provisional (WT :843, HEAD :853), `serializer_input_type_name`
return (WT :1110, HEAD :1120), `describe_serializer_input` diagnostic
recompute (WT :943, HEAD :953), and the `name_set_input_type_name`
spine (WT :1111, HEAD :1104) through which the model
(`mutations/inputs.py:722`) and form (`forms/inputs.py:403`) namers
route. No other `generated_input_type_name` caller exists
package-wide (1 def + 1 import + 1 docstring mention + 5 calls).

Equivalence (re-derived at current bytes, all three legs):

- Base: the guard's `serializer` is constructed two phases earlier
  as `serializer_class(**kwargs)` (:2410) from
  `mutation_cls._mutation_meta.serializer_class` (:2322), so
  `type(serializer)` is that exact class, the same class object the
  build passes. Nested: the build re-enters
  `build_serializer_input_class(nested_class, ...)` (:1518) while the
  guard recurses `_assert_field_agreement(mutation_cls,
  child_serializer, child_spec)` (:1400-1402) - both re-derive under
  the child's own class name at every depth.
- Partiality: `operation == "update"` (guard, reading `meta.operation`)
 iff `operation_kind == PARTIAL` (build). The map is closed and
  single-owned: `NON_DELETE_OPERATION_INPUT_KIND[meta.operation]`
  (`sets.py:863`) over descriptors whose only non-None `input_kind`
  members are create->CREATE / update->PARTIAL
  (`mutations/operations.py:35-55`), and serializer
  `Meta.operation in {"create", "update"}` (`sets.py:468`).
- Full-shape triple: the build binds `is_full_shape=True, token=""`
  at all three build sites (walk, injected, and the nested
  re-entry through the same builder); the divergent
  descriptor-derived name is computed AFTER the walk (build comment
  WT :1707-1709). The guard re-derives the RUNTIME annotation, which
  is seeded from that same canonical provisional - the
  injected-specs docstring (WT :827-838) states the sameness
  outright, and the choice-enum seeding makes it load-bearing for
  the `repr()` comparison.

Read whole or in the cited regions at current bytes (HEAD `5c3496e0`
+ working tree): the owner + spine whole; the guard + its walk entry
+ nested recursion; all four serializer call sites + the nested
re-entry; the operation descriptors + kind map + `Meta.operation`
gate; the choice-enum template (`_serializer_choice_enum`);
oracles (`tests/rest_framework/test_resolvers.py` agreement rows +
the injected-choice provisional pin,
`tests/rest_framework/test_inputs.py` serializer-name pins,
`tests/utils/test_inputs.py` spine pins, the live injected-status
update row); spec-039 Slice 1 / Decision 7. The file artifact that
named this family was orientation only: every site, count, and
exclusion below was re-derived fresh, never inherited.

Dirt: the three indexed files carry 107 hunks vs HEAD, all
attributed by diff content (f35 ledger 2, hunt truth-migration /
except-narrowing / behavior + maintainer `except BaseException`
deletions 105; zero unattributed). The owner body is byte-identical
across states (zero hunks span it). The guard's suffix half is
byte-identical across states; its base half carries the blocking
hunt hunk. Full attribution in `## Implementation (Worker-1)`.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Searched, all write flavors
   read. Model (`mutations/inputs.py:722`) and form
   (`forms/inputs.py:403`) namers route through the
   `name_set_input_type_name` spine, which calls the owner; the
   serializer divergent-name deriver (`serializer_input_type_name`,
   WT :1110) calls the owner for the assembly while computing its
   own token + full-shape decision (R1). No flavor restates the
   suffix rule; the guard restatement is the one hit on this axis.
2. **Sync/async twins.** Inapplicable with reason: the rule is a
   four-line pure string derivation (suffix conditional + two
   returns; the whole body read - no await point can exist in it).
   All five composed calls and the guard run at finalize or inside
   the sync write pipeline; the name rule itself is colorless. No
   twin exists to compare.
3. **Derived rather than repeated knowledge.** Found and confirmed:
   the guard derives the provisional by inline concatenation
   instead of composing the owner. Post-block census: exactly two
   conditional-suffix code sites package-wide in both states (owner
   + guard); every other `PartialInput` hit is ``...`` prose.
4. **Inverse / round-trip pairs.** Searched: provisional (walk) ->
   choice-enum names (`type_name` threaded through
   `resolve_serializer_field`) -> recorded `annotation_repr` ->
   guard re-derive + `repr()` compare form one grammar in two
   directions, correctly separated - production vs verification
   (standing J12: verification must recompute; R4). The divergent
   name is computed post-walk from the resolved specs (R1); the
   `describe_serializer_input` diagnostic recomputes the canonical
   name for its canonical-vs-derived note (consumer). No half is
   missing, no half restated beyond F1.
5. **Contracts restated in another medium.** Inventoried with roles:
   production (owner + 5 by-name calls + 1 restatement); contract
   sources (owner docstring "load-bearing skeleton" clause; build
   comment "the canonical name; the descriptor-derived divergent
   name is computed after the field walk"; injected-specs
   docstring sameness passage; spec-039 Slice 1 canonical-vs-divergent
   NAME contract - adjacent, not the provisional mechanism);
   independent oracles (spine value pins, serializer `"ItemSerPartialInput"`
   pin, 22 agreement-guard rows, the injected-choice provisional
   pin spelling `"PartialInput"` literally, one live update row -
   all spell VALUES, none reads the owner); projections (module
   docstrings, SDL enum names on the wire, the `orders/sets.py`
   `InputType` docstring passage - R3). A suffix change moves
   production + value oracles together by design; oracles listed,
   never counted. GLOSSARY carries no provisional anchor (0 hits).
6. **Enforcement by omission.** Enumerated: every provisional-needing
   site binds the canonical full-shape triple - walk (:1710),
   injected (:843), diagnostic (:943), nested re-entry (same
   builder), guard (:1306) - except the divergent deriver, which
   computes its own token + decision by contract (R1). No member
   lacks the rule; no omission defect filed.

### Enumeration

Instrument: literal + regex search over
`django_strawberry_framework/` (117 tracked `.py` files + the 2
untracked concurrent `utils/truth.py` / `utils/lazy.py`, zero hits
in every sweep below) at WT bytes via `muse.search`, `git grep`
over HEAD for the same populations, plus
full reads of the owner, the spine, the guard tower, all four
serializer call sites, the nested re-entry, the kind map, the
enum template, and every oracle body cited. Counts below are
matches at current bytes unless marked HEAD; every one homed.

- `generated_input_type_name`: 8 hits - 1 def (F1 owner), 1 import
  (rf-inputs :70), 1 docstring mention (spine :1103), 5 calls (F1
  composed). Closed at both states (HEAD: def :1058 + import :69 +
  docstring :1096 + calls :853/:953/:1120/:1711 + spine :1104).
- `PartialInput`: 36 hits WT - 2 code (owner :1085, guard :1306;
  F1) + 34 ``...``/comment prose (projections). HEAD: 36 hits -
  2 code (owner :1078, guard :1294) + 34 prose. Same population
  shape, line shifts only.
- Suffix-assembly sweep (`}Input`, `PartialInput'`/`"PartialInput`,
  `}Partial`, `+ "Input"`): 3 hits - the 2 code sites + the
  `orders/sets.py:368` docstring passage (R3). No hidden spelling.
- `name_set_input_type_name`: 9 hits - def + 2 imports + 4
  docstring mentions + 2 calls (model namer
  `is_partial=operation_kind != CREATE` at
  `mutations/inputs.py:724`, form namer
  `is_partial=operation_kind == PARTIAL` at
  `forms/inputs.py:405`; spine composes the owner).
- `operation == "update"` in the guard module: 2 hits - :1277
  (requiredness rule: update implies effectively-optional;
  examined-and-cleared, a different rule sharing only the
  `operation` read) + :1306 (F1 restatement).
- `NON_DELETE_OPERATION_INPUT_KIND` + `MutationOperationDescriptor`
  trio: the operation->input-kind vocabulary (single-owned map;
  input to the rule, R5).
- Oracle sweep: spine pins (2 tests), serializer-name pins
  (`"ItemSerPartialInput"` + direct-deriver exercise), 27 guard
  references / 22 name-matched agreement rows
  (`def test.*agreement*` census; the injected-choice provisional
  pin + live row cited separately), 1 live update row - all
  independent (literal spellings).
- `provisional` in GLOSSARY: 0. In spec-039: 0 (the archived spec
  pins the canonical-vs-divergent NAME contract, never the
  provisional mechanism - the code prose owns it).
- Excluded on body strength (read, no second site):
  `mutations/operations.py` (vocabulary, not naming),
  `rest_framework/sets.py` (map consumer), `mutations/inputs.py` +
  `forms/inputs.py` (spine consumers), `orders/sets.py` +
  `sets_mixins.py` (R3), `types/finalizer.py:1049` (comment
  projection), `serializer_converter.py::_serializer_choice_enum`
  (R2 value consumer), `utils/inputs.py::pascalize_token` (token
  encoder feeding the divergent token, not the suffix).

### Challenges

Each rule in the family: changes posited, authoritative-definition
counts (consumers, oracles, projections listed, never counted).
No experiment executed: the equivalence is body-readable
(closed vocabularies + exact construction), so every proof is
`static-reviewed`; execution belongs to the unblocking change
(see `## Pending execution`).

- H1 (suffix spelling: rename `PartialInput`, e.g. to `PatchInput`):
  count **2** - owner :1085 + guard f-string :1306. Riders: 5
  composed calls (unchanged text, new behavior), value oracles,
  SDL + enum-name projections.
- H2 (full-shape assembly: `<Base><suffix>` gains a prefix):
  count **2** - owner `if is_full_shape` branch + guard f-string
  (base+suffix concatenation). Same riders as H1.
- H3 (partiality gains a third state): count **2** - owner
  signature + conditional + guard conditional. Riders: the
  per-site `is_partial` input spellings (R5) as consumers.
- H4 (operation vocabulary gains a member, e.g. `patch`):
  count **0 here** - the kind map + descriptors move once
  (vocabulary owner); the per-site input spellings follow as
  consumers; neither F1 definition moves. Proves R5 is not a
  second definition of THIS rule.
- H5 (full-shape meaning changes, e.g. canonical needs a token):
  count **1** - the owner body only; the four full-shape call
  triples follow the signature mechanically. Proves R6 is a call
  convention, not a definition.

## Findings

### F1 - canonical-input provisional name (CONFIRMED duplication, blocked-on-hunt)

- **Contract + variation.** The canonical provisional name
  (`<Base>Input` / `<Base>PartialInput`) seeding serializer-only
  choice-enum names during the field walk. Varies on `is_partial`
  only; always the full-shape skeleton.
- **Sites + roles.** Definition (owner):
  `utils/inputs.py::generated_input_type_name`. Definition
  (restatement): the `_assert_field_agreement` f-string
  (WT :1306, HEAD :1294). Consumers (compose by name): the 5
  calls (walk, injected, divergent-deriver return, diagnostic,
  name-set spine). Oracles: spine pins, serializer-name pins, 22
  agreement rows, the injected-choice provisional pin, 1 live
  row. Projections: owner/build/injected docstrings, spec-039
  Slice 1, SDL enum names.
- **Challenges.** H1/H2/H3 -> **2** each (owner + guard f-string);
  H4 -> 0 here; H5 -> 1 (owner only).
- **Owner + lifetime.** `utils/inputs.py::generated_input_type_name`
  by principle 7: the existing owner with exactly this
  responsibility ("Single-sited so the suffix rule + the
  full-vs-derived branching cannot drift between flavors"), and
  the narrowest cohesive owner every legitimate consumer can
  import - the guard module already imports `..utils.inputs`, so
  the migration adds a NAME to an existing import, no new module
  edge, no cycle (`utils/inputs.py` imports only `..exceptions`
  upward). Lifetime (principle 4): pure derivation, not cached -
  no stored state, no validity key, no publish point.
- **Migration (specified, not applied - blocked).** Against HEAD
  bytes the guard line becomes
  `generated_input_type_name(type(serializer).__name__,`
  `is_partial=(operation == "update"), is_full_shape=True,`
  `token="")`, with `generated_input_type_name` added to the
  existing `from ..utils.inputs import (...)` at
  `resolvers.py:154`. Behavior-identical by the three-leg
  equivalence in `## System trace` (exact construction, closed
  map, full-shape triple at every depth incl. nested re-entry).
  The unblocking change reconciles the base rendering with the
  landed hunt (WT currently `truth.name(...)`) at application
  time and lands the R-home clauses below.
- **Distinct behavior.** Nothing stays separate inside F1: the
  guard keeps its recompute-and-compare contract (R4) - only the
  provisional-name INPUT to its re-derivation composes the owner.
- **Behavioral proof.** `static-reviewed`: closed-population
  censuses at both states (2 code sites, 5 calls, 34 prose each)
  + the three-leg equivalence, each leg pinned to an exact
  construction (:2322/:2410), a closed map, or a same-builder
  re-entry. Rejects the wrong result "the guard needs a divergent
  name" (the build comment + injected-specs docstring + nested
  re-entry forbid it) and "base/partiality can disagree" (exact
  construction + closed vocabulary forbid it). Execution - the
  agreement + name oracles green post-migration - is deferred to
  the `proof:` entry in `## Pending execution`.
- **Structural gate (specified, not landed - blocked).** A
  spelling census over the package: exactly one
  `"PartialInput" if` conditional outside ``...`` prose (the
  owner body), plus the guard composing the owner by name.
  Negative control: a behavior-preserving hand copy of the owner
  body at the guard passes every behavior oracle (it computes the
  same string) and fails ONLY the census - proving the census,
  not the behavior pins, guards the single-sourcing. The
  unblocking change lands it beside the migration and shows it
  red-then-green via `prove_failability.py`.
- **Coupling.** None with any other family: one line + one import
  name. Blocked solely on the hunt hunk below resolving (landing
  or the maintainer ruling); the migration must not be hand-applied over
  uncommitted concurrent bytes.
- **Freshness.** Indexed 3: `utils/inputs.py` WT `0575e9b2` HEAD
  `0caa3416`; `rest_framework/inputs.py` WT `a4dbdb90` HEAD
  `dfedd0e5`; `rest_framework/resolvers.py` WT `074d6e4b` HEAD
  `fc9d8ee5` (`git hash-object` WT vs `git rev-parse HEAD:path`;
  HEAD `5c3496e0` unmoved; dispatch pins match). Connected pins +
  no-workspace-copy statement in `## Implementation (Worker-1)`.
  Any fingerprint change reopens this finding.
- **Blocked-on-hunt (exact hunk, nothing touched).** The
  consolidation must rewrite the guard line, whose worktree bytes
  carry uncommitted hunt truth-migration dirt on the base half
  (suffix half byte-identical):

```diff
@@ -1291,7 +1303,7 @@ def _assert_field_agreement(
         _python_attr, runtime_annotation, _runtime_spec = resolve_serializer_field(
             runtime,
             meta.model,
-            f"{type(serializer).__name__}{'PartialInput' if operation == 'update' else 'Input'}",
+            f"{truth.name(type(serializer))}{'PartialInput' if operation == 'update' else 'Input'}",
         )
```

Attribution: `from ..utils import truth` is absent at HEAD (0
`truth.` hits in HEAD `utils/inputs.py` vs 42 WT; `utils/truth.py`
untracked) - the campaign is the hunt's uncommitted
truth-migration, a named concurrent population. Per the dispatch
procedure the item stops here: hunk recorded, tree untouched.

### R1 - divergent descriptor-derived naming (REJECTED, stays at the deriver)

`serializer_input_type_name` computes its own per-field digest
token + full-shape decision, then calls the owner for the
assembly. Shared form considered: fold the digest into the owner
- refused: per-field descriptor identity (annotation /
requiredness / kind / source / relation target / description) is
a serializer-only contract; the name-set flavors pass a sorted
name set through the spine instead. Challenge: same-name-set
divergence (hook returns same names, different annotation) moves
only the deriver (count 1); suffix rename moves only the owner
(count 1) - the decisions vary independently. **Contract
difference:** descriptor identity vs name assembly. **Trigger:**
a second descriptor-identity consumer, or a name-set flavor
needing per-field digests. **Durable home (specified):** the
owner docstring already carries it ("the serializer still
supplies its own descriptor digest and full-shape decision") -
stands, no new clause owed.

### R2 - choice-enum name template (REJECTED, stays at the template)

`_serializer_choice_enum` builds
`f"{type_name}{pascal_case(...)}Enum"` from the provisional VALUE
it receives. Shared form considered: route enum naming through
the provisional owner - refused: the template consumes a string,
never the partiality/shape rule; it cannot distinguish a
provisional from any other `type_name`. Challenge: enum-suffix
rename moves only the template (count 1); provisional-suffix
rename moves only F1 (count 1). **Contract difference:** enum
derivation from a name vs provisional-name production.
**Trigger:** a second enum-name producer. **Durable home
(specified):** one clause on `_serializer_choice_enum` ("the
`type_name` arrives precomputed; this template never derives
partiality") - rides the open `generated-choice-enum-name-template`
family item, which owns the template.

### R3 - set-family `InputType` naming (REJECTED, different rule)

`sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` owns the
`{cls.__name__}InputType` rule for set families (cited at
`orders/sets.py:368`). Shared form considered: one cross-family
naming helper - refused: different suffix, different subject
(set classes vs generated inputs), different reasons to change
(cookbook parity vs input identity). Challenge: set-suffix change
moves only the mixin (count 1). **Contract difference:**
set-class naming vs generated-input naming. **Trigger:** a flavor
unifying set names with input names. **Durable home (specified):**
one clause on `type_name_for` ("set naming only; generated-input
names live at `generated_input_type_name`").

### R4 - build-vs-guard recompute halves (REJECTED, halves stay apart)

The build produces the annotation; the guard re-derives it via
the same two functions and compares (standing J12). Shared form
considered: guard reads the build's recorded annotation -
refused: verification must recompute independently, or the check
cannot fail. F1 is carved OUT of this rejection: only the
provisional-name INPUT composes the owner; the recompute contract
is untouched. Challenge: a third annotation production site would
force a producer/consumer decision (today: 2 halves, count 1
each). **Contract difference:** production vs verification.
**Trigger:** a third annotation production site. **Durable home
(specified):** one clause on `_assert_field_agreement` ("the
annotation is re-derived, never read back; only the provisional
name composes the shared namer").

### R5 - per-site `is_partial` input spellings (REJECTED, reads not definitions)

Seven decision sites feed `is_partial` in four spellings:
`operation == "update"` (guard), `operation_kind == PARTIAL`
(walk-local, injected, divergent-deriver, form namer),
`operation_kind != CREATE` (model namer),
`shape.operation_kind == PARTIAL` (diagnostic); the spine and the
walk pass a param through. Shared form considered: one partiality
helper - refused: each is a read of owned vocabulary (the closed
kind map + descriptors), not a definition of the
operation->partiality rule; H4 proves a vocabulary change moves
the map once with all seven following as consumers. **Contract
difference:** vocabulary read vs rule definition. **Trigger:**
the operation vocabulary gains a member (re-audit all seven as
consumers). **Durable home
(specified):** one clause on the owner ("callers derive
`is_partial` from their own operation vocabulary; only the
suffix mapping lives here").

### R6 - full-shape call triple (REJECTED, convention not definition)

Four sites bind `(is_full_shape=True, token="")` (walk, injected,
diagnostic, guard-post-migration). Shared form considered: a
`canonical_provisional_name(base, is_partial)` wrapper - refused:
H5 proves a full-shape-meaning change moves the owner body only,
with all four following the signature mechanically; the triple
has no variation axis of its own. **Contract difference:** call
convention vs rule. **Trigger:** the canonical provisional gains
a parameter only some full-shape sites bind differently.
**Durable home (specified):** one clause on the owner ("the
full-shape triple is a call convention; full-shape meaning lives
in the branch below").

## Defects

None found. The trace covered the guard tower, the build legs,
the kind vocabulary, the enum template, and every oracle body -
no docstring contradicts its body, no flavor lacks a contracted
guard, no layering claim fails. Concurrent dirt is concurrent
work, not filed.

## Pending execution

- `proof: uv run python scripts/workspace.py run
  dry/canonname-f36/consolidate -- pytest
  tests/rest_framework/test_resolvers.py
  tests/rest_framework/test_inputs.py tests/utils/test_inputs.py
  -n0 --no-cov -q` (discharges F1's behavioral proof once the
  block clears: guard agreement + serializer-name + spine pins
  green post-migration; runnable only after the unblocked
  consolidation lands).
- Sharded cell: `unverified` but `inapplicable by construction`
  (Worker-2 judges): the rule is a pure string derivation - the
  owner body and the restatement touch no database, alias, or
  dialect decision; the guard's DB work (visibility scoping,
  validator pinning) sits outside the renamed line. PG cell:
  same reasoning, `unverified` / `inapplicable by construction`.
- No `gate:` witness owed: a green unmutated suite would
  discharge nothing for a blocked finding.

## Judgment

The family is one real duplication plus settled single-ownership.
F1 CONFIRMED: the guard's provisional f-string re-spells the
shared namer's suffix rule + full-shape assembly with no
load-bearing difference on any of the three variation axes - but
the line carries an uncommitted hunt hunk, so the consolidation
is `blocked-on-hunt`, recorded above, with zero files changed.
Six rejections (R1-R6) each carry a challenge, a concrete
contract difference, a trigger, and a specified durable-home
clause. No defect, no ticked row disturbed.

## Implementation (Worker-1)

Tracked changes: NONE (blocked-on-hunt; zero edits). The item diff
vs `ITEM_BASELINE=ec703a50` on the three indexed files is empty;
the artifact is untracked (`??`). Every other delta in the tree is
concurrent dirt, attributed below by diff content and left alone.

Attribution (107 hunks vs HEAD, `/tmp/f36/diffs.patch` - vocabulary
census + manual read of all 19 classifier-unknowns, all 14
except-vocabulary hunks, both F35 hunks, and every family-site
region; zero unattributed):

- `utils/inputs.py` (29 hunks): all hunt truth-migration /
  except-narrowing. Includes 6 hunks deleting or narrowing
  `except BaseException` arms (shared with the maintainer's
  `except BaseException` deletion population - several hunks are
  merge-combined, truth renames + arm deletion in the same hunk,
  author-split not decidable per line, both populations named and
  concurrent); 1 reworded prose line riding a campaign hunk's
  function; new `_is_one_of` / `_UNORDERED_TYPES` /
  `_META_CONTAINER_TYPES` / `_META_ABSENT` machinery (0 hits at
  HEAD - WT campaign support). Zero ledger hunks.
- `rest_framework/inputs.py` (32 hunks): 2 are the f35 ledger
  (`+    normalize_serializer_source,` import hunk;
  `source = normalize_serializer_source(field, field_name)` call
  site - both match the `## Owned changes` rows verbatim, built
  on by content only, never re-touched). The other 30 are the
  hunt campaign: truth-migration swaps (incl. all four F1
  call-site base lines - consumers, not edited), three
  guard-narrowing hunks (`except Exception` -> `except KeyError`
  + `read_nested_serializer_fields` delegation +
  `NESTED_STABLE_FIELDS_INSTRUCTION` deletion), one probe
  `except Exception` addition (`_default_full_shape_identity`),
  and 2 docstring hunks riding the campaign (one same-function,
  one module prose describing the narrowed guard).
- `rest_framework/resolvers.py` (46 hunks): all concurrent campaign
  (zero ledger). Truth-migration swaps incl. the blocking guard
  hunk (F1, exact text above); `TypeIs` import + `_is_one_of` /
  `_is_frozen_container` support; two `except BaseException` arm
  deletions merge-combined with truth renames (maintainer + hunt);
  `except Exception` -> `except TypeError` / `(AttributeError,
  OSError)` narrowings; one hunt Area-D behavior hunk
  (`validation_error_to_field_errors` gains `field_name_map` -
  record at `docs/bug_hunt/bug_hunt-0_0_15.md:1869`). Committed
  `_safe_type_name` (3 hits at HEAD) is baseline, not dirt.

Family-site dirt state: owner body CLEAN (no hunk spans HEAD
:1058-1081 - neighbors :943 / :1146 - and the extracted bodies are
byte-identical); guard suffix half byte-identical, base half
hunt-dirtied (the block); all four serializer call-site base lines
truth-dirtied (consumers, untouched).

Type gates (shared venv, tree-state - zero edits, so these record
the concurrently-dirty tree, not a change): `uv run mypy` clean
(119 files); `uv run basedpyright` 0 errors, 0 warnings, 0 notes;
`uv run python scripts/check_any.py` 130 uses at 90 sites (matches
the run-9 baseline). No ruff runs owed (no `.py` touched).
Source-layout `--check` on the artifact: excluded (per-cycle
artifact), exit 0. No workspace copy created (no source-mutating
proof ran); censuses were read-only searches plus source reads in
the shared tree. The entry's one authorized focused test was not
spent. HEAD `5c3496e0` at finish, unmoved since dispatch.

Freshness - connected pins (`git hash-object` WT /
`git rev-parse HEAD:path`; HEAD `5c3496e0`):

- `rest_framework/serializer_converter.py` WT `d90b4a00` HEAD
  `40cb765a`; `rest_framework/sets.py` WT `f2e353b6` HEAD
  `b0894760`; `mutations/operations.py` WT `612c458d` HEAD
  `0d9ee2e9`; `mutations/inputs.py` WT `e73c7878` HEAD `d11b8745`;
  `forms/inputs.py` WT `65ac558f` HEAD `0ba0d9a5`;
  `orders/sets.py` WT `8ce11495` HEAD `a8cd33c7`;
  `types/finalizer.py` WT `0807fea7` HEAD `662826eb`;
  `sets_mixins.py` WT `c496feb2` HEAD `42e8c862`.
- Oracles + contracts: `tests/rest_framework/test_resolvers.py` WT
  `0c64d6d4` HEAD `a9162094`;
  `tests/rest_framework/test_inputs.py` WT `fa60df50` HEAD
  `e6636d41`; `tests/utils/test_inputs.py` WT `42bfb6a7` HEAD
  `598f1440`; `test_query/test_library_api.py` WT `099e25b9`
  HEAD `91f0238b`; spec-039 `cf78af93` both states (clean);
  GLOSSARY `95cd34f3` both states (clean).

Worker 0 transcriptions (exact text; Worker 0 alone edits the
plan): (1) index row `canonical-input-provisional-name` status ->
`open (f36: F1 CONFIRMED count-2 but blocked-on-hunt, migration
specified, zero edits; R1-R6 with triggers + specified homes;
verified, pending execution)`; (2) `## Families` row ->
``- [ ] Family `canonical-input-provisional-name` -
[dry-rule-canonical-input-provisional-name.md](dry-rule-canonical-input-provisional-name.md)
- run 10 f36 fresh trace (CONFIRMED but blocked-on-hunt - guard
restatement count 2, hunt hunk on the line, migration specified,
zero edits; R1-R6 exclusions with triggers + specified homes;
0 defects)``. No new index rows (no sub-rules; R2 rides the
existing open `generated-choice-enum-name-template` row). No
`## Owned changes` rows (zero edits).

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (skeleton + `## Judgment` /
`## Implementation` headers seen for placement only; verdict shape
was already in the dispatch note). Fresh trace at HEAD `5c3496e0`
+ WT, fingerprints below.

### Own trace

Rule: the canonical-input provisional name - `<Base>Input` /
`<Base>PartialInput` for the full shape, `<Base><token><suffix>`
for a divergent shape - owned by
`django_strawberry_framework/utils/inputs.py::generated_input_type_name`
(`suffix = "PartialInput" if is_partial else "Input"`, full-shape
`<Base><suffix>` branch, token branch).

Sites (package-wide `PartialInput` sweep: exactly 2 executable
suffix spellings; every other hit is docstring prose):

- D1 (definition, owner candidate):
  `django_strawberry_framework/utils/inputs.py::generated_input_type_name`
  - the suffix rule + full-vs-derived assembly.
- D2 (definition, restatement):
  `django_strawberry_framework/rest_framework/resolvers.py::_assert_field_agreement`
  guard f-string (`f"{truth.name(type(serializer))}{'PartialInput'
  if operation == 'update' else 'Input'}"`) - re-spells the suffix
  rule + full-shape assembly by concatenation.
- Consumers (compose by name, never counted):
  `rest_framework/inputs.py` 4 call sites (injected-specs
  provisional, `describe_serializer_input` canonical, the
  `serializer_input_type_name` spine, the build provisional);
  `mutations/inputs.py::mutation_input_type_name` and
  `forms/inputs.py::form_input_type_name` via
  `utils/inputs.py::name_set_input_type_name`; nested builds
  recurse through the same builder; the `_walk_serializer_fields`
  `provisional_name` threading into `resolve_serializer_field`.
- Oracles: `tests/utils/test_inputs.py`
  `::test_name_set_input_type_name_canonical_and_narrowed`
  (literal `"ItemInput"` / `"ItemPartialInput"` expectations);
  live `test_query/test_library_api.py`
  `::test_serializer_update_injected_field_contract_over_http`
  (update succeeds only if the guard's `PartialInput`
  provisional agrees with the schema-time one). No oracle reads
  the owner (`resolve_serializer_field` test calls pass
  literals). Converter call-site family enumerated: exactly 3
  production callers (`rest_framework/inputs.py` injected +
  walk, `rest_framework/resolvers.py` guard), all
  operation-aware; no fourth site omits the provisional.
- Projections: `<Base>Input` / `<Base>PartialInput` grammar
  restated in module + function docstrings; no inverse grammar
  (no suffix-strip parse; `describe_serializer_input` is a
  registry lookup by exact name, not a parse).

Challenges (each forces D1 + D2, count 2):

- C1 suffix spelling (`Input` / `PartialInput` renamed): owner
  line + guard f-string move; all composed sites follow.
- C2 full-shape assembly (`<Base><suffix>` reshaped): owner
  full branch + guard f-string move.
- C3 suffix arms (a third operation shape): owner gains an arm
  + guard gains an arm; the per-site `is_partial` input
  mappings stay local (distinct vocabularies, not the rule).

Owner I would choose: `utils/inputs.py::generated_input_type_name`
(existing responsibility owner; `rest_framework/resolvers.py`
already imports from `..utils.inputs`, so no new dependency
edge; narrowest valid owner every consumer can import).

Migration I would specify (unapplied): guard line becomes
`generated_input_type_name(truth.name(type(serializer)),
is_partial=operation == "update", is_full_shape=True, token="")`
+ extend the existing `..utils.inputs` import. Keeps local: the
base-name read off the runtime instance (load-bearing for the
agreement check) and the partial decision in `operation`
(`create` / `update`) vocabulary. Principle-8: pure string
function, byte-identical output for every input, no
exception / query / transaction / cancellation delta, the
`truth.name` call stays at the same program point.

Matrix (own discharge): (1) cross-flavor - model + form + serializer
namers all read, all compose via the owner; (2) sync/async -
inapplicable by reason (pure name grammar, no execution color,
no await boundary); (3) derived knowledge - the package-wide
sweep IS this axis, count 2; (4) round-trip - no inverse grammar
(registry lookup only); (5) other media - docstring projections
+ literal oracles listed above; (6) omission - converter
call-site family enumerated (3/3 operation-aware), nested
recurses through the same builder.

Block call (own): BLOCKED-ON-HUNT. Exact hunk
`@@ -1291,7 +1303,7 @@` rewrites the guard line itself (HEAD
`type(serializer).__name__` -> WT `truth.name(type(serializer))`,
hunt truth-migration vocabulary); the import block the migration
needs is likewise hunt-dirtied (`@@ -134,13 +134,14 @@`).
No ledger row covers `rest_framework/resolvers.py`, so both
hunks are concurrent. Zero legal partial landings: the call-site
edit AND the import edit each land on hunt dirt; prose-only is
not the consolidation. Zero edits required.

Rejections I independently clear before reading: descriptor-token
computation (different identity grammar per deriver, shared
assembly already composed); choice-enum `<Type><Field>Enum`
template (different grammar, consumes the provisional as input);
set-family `InputType` naming (read-side filter/order args, not
write inputs); build-vs-guard recompute halves (the guard must
re-derive to check agreement - sharing would vacate the check);
per-site `is_partial` spellings (vocabulary reads, not the
rule); the full-shape call triple (usage convention, no change
obligation). Triggers + home clauses to judge against W1's.

### Reconciliation with Findings

Read `## Findings` after recording the trace above. Verdicts
AGREE on every point; two convention-only deltas, no
disagreement:

- F1 count-2 CONFIRMED (own sweep: exactly 2 executable suffix
  spellings WT + HEAD, 36/36 total each; same D1/D2, same
  owner, same principle-7 reasoning incl. the existing
  `..utils.inputs` import edge; no-cycle claim verified -
  `utils/inputs.py` imports only `..exceptions` upward).
  Challenges H1/H2/H3 match my C1/C2/C3; H4 (0 here) and H5
  (owner-only) are sound discriminators proving R5/R6.
- Blocked-on-hunt CONFIRMED: W1's recorded hunk is byte-identical
  to my independently derived `@@ -1291,7 +1303,7 @@`; no ledger
  row covers the file; the import-block edit is likewise
  hunt-dirtied. Zero legal partial landings. Zero edits correct.
- Migration: W1 specifies against HEAD bytes
  (`type(serializer).__name__`) with an explicit reconcile-with-
  landed-hunt instruction; my sketch used WT bytes. Same
  migration, W1's base convention is the right one.
  Principle-8 legs verified: base construction pinned at
  :2322/:2410 (re-read, exact), closed kind map + `Meta.operation`
  gate read, full-shape triple at every depth incl. the nested
  same-builder re-entry (re-traced). The guard keeps its
  runtime-instance base read + operation-vocabulary partial
  decision - both load-bearing, both kept local.
- Enumeration re-derived member by member: 8/8 namer hits (HEAD
  lines 853/953/1120/1711 + spine 1104 verified), 36/36
  `PartialInput` both states (code at WT 1085/1306, HEAD
  1078/1294), suffix sweep (my executable-only 2 = W1's 3 minus
  the R3-homed docstring passage - same conclusion), 9/9 spine
  hits, 2/2 `operation == "update"` (1277 cleared as the
  requiredness rule), 7/7 R5 spellings, 117 tracked `.py` +
  2 untracked instrument, GLOSSARY 0 + spec-039 0.
- Oracles verified independent: `"ItemSerPartialInput"` literal
  pin, 22/22 agreement rows, injected-choice pin (+ negative),
  live update row; none reads the owner. R4 converges with
  standing file-artifact J12 (carve-out already recorded there).
- R1-R6 each carry contract difference + trigger + specified
  home; R1's quoted home clause verified verbatim at the owner
  docstring; R2's template shape verified
  (`f"{type_name}{pascal_case(...)}Enum"`, consumes a string);
  R2 rides the open `generated-choice-enum-name-template` row
  (no new index row owed).
- Freshness: all 12 connected pins + spec-039 + GLOSSARY
  re-hashed, match exactly. HEAD unmoved, 3/3 WT pins match
  dispatch - nothing stale.
- `proof:` entry correctly typed `execution-deferred` (no edit
  may land before the block clears) and runnable: the exact
  three-file command passes 336/336 at baseline in the shared
  venv (paths valid, oracles green pre-migration). Sharded/PG
  `inapplicable by construction` ENDORSED - the renamed line is
  a pure string derivation reaching no database, alias, or
  dialect. Structural gate correctly specified-not-landed (a
  count-1 census would be born red against the count-2 tree).
- Item diff: plan edit alone (dispatch + submission note);
  artifact untracked; ruff vacuous (zero tracked `.py`
  touched). Gates re-run green in the shared venv: mypy 119
  clean, basedpyright 0/0/0, check_any 130/90. No workspace copy
  created (no source-mutating proof needed). No defects found;
  `## Defects` stays empty.

Worker-0 transcriptions in `## Implementation (Worker-1)` stand
as written (index row + Families row texts, no new rows, no
ledger rows). Plan item will read `verified, pending execution`
(one `proof:` entry remains).

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
