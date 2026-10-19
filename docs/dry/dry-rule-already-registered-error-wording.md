# DRY review: `already-registered-error-wording`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `already-registered-error-wording`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry._already_registered`.
Known member files: `django_strawberry_framework/registry.py` (only).
`HEAD` is `bfaee91d`; `ITEM_BASELINE` is
`2430304eb87e0bdcb2009b7226d67e81cf1ed5ba`.
Prior record `docs/dry/dry-file-registry.md` F10 used only as a trigger,
never a verdict; every count below re-derived. Never read any
`worker-memory/`.

## System trace

Rule: the error raised when a type/model registers twice — wording +
when it fires vs silent first-wins. Sits next to the verified siblings:
the enum first-wins rule (same choices on two models reuse per
`(model, field_name)` key) and the definition collision arm
(`register_definition` C2: same object silent, different object raises).

Attribution (before any read of content): the worktree
`django_strawberry_framework/registry.py` diff vs `HEAD` is exactly the
ledgered `relay-node-name-decode` docstring clause on
`TypeRegistry.definition_for_graphql_name` (plan `## Owned changes`,
content-matched line for line); vs `ITEM_BASELINE` the diff is empty.
Nothing else on this family's paths — confirmed. All other dirty paths
are concurrent work, read-only unless a consolidation needs them (none
does).

Sites + roles. *Wording definition*: [registry][registry]
`::TypeRegistry._already_registered` (one def; canonical
`"X is already registered <label> Y"` template; labels `against` /
`as` only). *Canonical call sites* (2): `register` reverse-collision
(same `type_cls`, different model) and `register_enum` `(model,
field_name)` collision. *Intentional inline wordings* (3, test-pinned,
docstring-recorded): `register` primary-flip (`"is already registered
for <model>; primary flag cannot be flipped on re-register"`),
`register` duplicate-primary (`"Cannot register <type> as primary for
<model>; <incumbent> is already the primary type"`),
`register_definition` rebind (`"<type> already has a registered
DjangoTypeDefinition"`). *Silent arms*: same type / same model / same
flag re-register returns `False`; same enum class re-register is a
no-op; same definition object re-register is a no-op; different class
for the same model appends (`True`) — the normal multi-type case per
[spec-018][spec-018]. *Consumers*: `convert_choices_to_enum`
(get-then-register retry), `DjangoType.__init_subclass__` (sole pair
caller), `register_with_definition` rollback (snapshot-conditional).
*Oracles*: [test-registry][test-registry] (reverse, enum, idempotence,
flip pair, duplicate-primary, rebind, rollback pack, multi-type
no-raise pair). *Projections*: the `_already_registered` docstring
(names both centralized sites + the three distinct ones), the
`register` / `register_enum` / `register_definition` docstrings,
[spec-018][spec-018] (collision rules + retired one-type message +
helper-survival note), the `ConfigurationError` docstring
(primary/ambiguity shapes). *Neighbors with own `already` wordings*,
rejected below: serializer-converter override cache, connection-class
cache, serializer choice-enum member-set guard.

Connected sources read for judgment: [converters][converters]
(`convert_choices_to_enum` only), [serializer-converter][serializer-converter]
(converter-registration + choice-enum blocks),
[connection][connection] (connection-cache collision arm),
[exceptions][exceptions] (`ConfigurationError` contract prose),
[spec-018][spec-018] (Decision 3 + survival note), the three verified
siblings (boundary statements checked, not inherited). Excluded on
strength of body: every other package module (zero
`_already_registered` / canonical-template vocabulary over the 117-file
sweep); filter/form/serializer input builders (no registration
vocabulary); the finalizer ambiguity audit (build-time enforcement,
consumer of the map, not a registration wording).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** No flavor keeps a second
type/model registry (117-file sweep: one `_already_registered` def,
two call sites, both in `registry.py`). The serializer-converter and
connection caches are different subjects (field-converter slot with an
`override=True` escape; generated-artifact identity guard), not second
spellings — R-D/R-E.
2. **Sync/async twins.** Zero `AsyncFunctionDef` in `registry.py`
(re-verified by AST in the workspace probe; every method is in-memory
dict work). Registration is import-time-only (`_check_mutable`); no
ORM I/O, no awaits. Trigger: a registration path touching the DB or
awaiting.
3. **Derived rather than repeated knowledge.** The canonical template
is spelled once (the helper's single f-string); each call site passes
only its label + operands. The three inline wordings spell different
violations with different identifiers — three grammars, not three
copies (C1 probe). Trigger: a new cross-key collision reusing the
template vs a new violation needing its own identifiers.
4. **Inverse / round-trip pairs.** raise-vs-silent per aspect:
idempotent re-register (`False` / no-op), flip/collision raises with
preservation, multi-type append, rollback atomicity — all pinned by
the oracles above plus the 36/36 workspace probes. No un-register
wording besides `unregister`/`clear()` by design.
5. **Contracts restated in another medium.** Production (helper + two
call sites + three inline arms); oracles (independent literals, plain
test classes, no owner reads); projections (docstrings verified
against bodies; [spec-018][spec-018] pins the rules and the helper's
survival). No consumer restates the template: every cross-key raise
calls the helper.
6. **Enforcement by omission.** Every mute arm has its loud twin
audited: same-object silent vs different-object raise on all three
aspects; append-silent vs duplicate-primary raise on the map; every
raise preserves the incumbent (asserted in the oracle bodies + E3/D2/M7
probes). No member lacks the arm its contract requires: no defect.

### Enumeration

Instrument: `ast.parse` of the worktree target + token sweeps over the
117-file package population (`git ls-files django_strawberry_framework`
= 117, re-counted in the workspace copy). Every wording member
assigned; every challenge ends in the family row or a recorded
rejection (no file-local row — each overlap has its owning family or
rejection recorded).

- `TypeRegistry._already_registered`: exactly 1 def; exactly 2 code
call sites (`register` reverse arm, `register_enum` collision arm);
zero production callers outside `registry.py` (package-wide
`_already_registered(` census: def + 2 calls only; prose mentions in
specs/docs excluded by line shape).
- Canonical labels: exactly `{"against", "as"}` (one each).
- Inline `ConfigurationError(` raises in `registry.py`: primary-flip,
duplicate-primary, definition-rebind (3, each test-pinned by
substring); guard/teardown/decode-miss/ambiguity raises are
family-external (different violations, listed not counted).
- Silent arms: map idempotent (`return False`), enum same-class store,
definition same-object store, multi-type append (`return True`) — one
each, probe-pinned M2/E2/D1/M5.
- Neighbor `already` wordings: serializer-converter override (1),
connection-cache identity guard (1), serializer choice-enum member-set
guard (1) — all different grammars, R-D/R-E/R-F.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes map one-to-one
onto C1–C3 (36/36 `execution-verified`) plus the N1 negative control.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Rephrase the canonical `"X is already registered <label> Y"` form (e.g. rename the verb) | **1** (`_already_registered`; both call sites follow by construction; the 3 inline + 3 neighbor wordings are untouched — different grammars). Oracle pair: `test_register_same_class_against_two_models_raises` + `test_register_enum_different_class_for_same_key_raises`. Probe W-series. |
| C2 | Flip the same-key same-object policy on ONE aspect (e.g. enum same-class re-register now raises) | **1** (that aspect's arm only — `register_enum`; the map and definition retry contracts serve different callers and keep their silence). Oracle: `test_register_enum_same_class_is_idempotent` (+ map/definition idempotence rows as contrast). Probes E2 vs M2/D1. |
| C3 | Flip second-type-same-model from silent-append back to raise (restore the retired one-type rule) | **1** (the map append arm only; enum/definition keys never see this shape — different keys, different callers). Oracles: `test_register_two_types_same_model_without_primary_allows_both_in_types_for` + `test_register_second_type_for_same_model_no_longer_raises_collision`. Probe M5. |

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/already-registered-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_already_registered.py
```

Proof (`CHECKS_PASSED=36/36`): wording singularity (1 def / 2
call sites / labels / template / 3 inline arms / 3 neighbors /
package-wide census), map arms (first-True, idempotent-False,
both flip directions, append, duplicate-primary + no-append,
reverse + preservation), enum arms (round-trip, both miss arms,
same-class noop, collision + preservation), definition arms
(same-object noop, rebind + preservation, pair atomicity + pin
survival). Status: `execution-verified`. Rejects "a second canonical
site exists", "an aspect silently overwrites", "a raise drops the
incumbent". Copy `__file__`:
`.../dry-ws/already-registered-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/already-registered-w1/examples/fakeshop/db.sqlite3`
(copy's own tree and database; never the shared tree; the probes open
no DB at all). No source mutation in the proof; searched population
inside the copy: 117 `.py` (matches the shared tree).

**Negative control N1 (executed, disposable workspace, copy only).**
Hand-inlined the helper at both call sites (identical f-strings, helper
left in place), re-ran the behavior arms: reverse + enum collisions
raise with byte-identical wording (both PASS); only the source census
(W2 two-call-sites) fails. Restores N/A (copy is disposable; shared
tree never touched). Status: `execution-verified`. Proves no
behavioral gate can pin wording unity — the copy is correct, so every
behavior oracle passes it; only a source census detects the bypass.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "<10 wording/
idempotence/flip/primary/rebind/rollback/multi-type rows>"` → 10
passed (reverse, enum idempotence + collision, map idempotence, flip
pair, duplicate-primary, rebind, rollback, multi-type no-raise).

## Findings

### F1 — already-registered error wording (REJECTED consolidation: single-owned template, per-aspect policy intentionally separate)

- **Contract + variation.** Cross-key collisions share one template
`"X is already registered <label> Y"` with exactly two labels
(`against` = same class against a second model; `as` = same
`(model, field)` key holding a different enum class). Same-key
same-object re-register is silent on all three aspects; every
different-object collision raises and preserves the incumbent.
Second class for the same model appends silently (multi-type normal);
only the primary-slot collisions raise.
- **Sites + roles.** *Definitions*: the helper + its 2 call sites
(one each). *Per-aspect arms*: map idempotent/flip/append/
duplicate-primary/reverse; enum noop/collision; definition
noop/rebind (+ pair rollback). *Consumers / oracles / projections*:
as listed in System trace.
- **Challenges.** C1 → 1; C2 → 1 per aspect (no single change moves
more than its own arm); C3 → 1. Count > 1 nowhere in one rule: no
duplication.
- **Owner + lifetime (principles 7, 4).**
`django_strawberry_framework/registry.py::TypeRegistry._already_registered`
stands: narrowest cohesive owner every raiser can reach without a new
import (both call sites are its own methods; the reverse — a shared
wording module — would be machinery serving two lines). Stateless
pure constructor: no lifetime fields owed. The raise-vs-reuse DECISION
is deliberately NOT owned here: each aspect (map / definitions /
enums) owns its own identity predicate because each answers a
different retry question (re-import idempotence, converter cache
retry, pair-rollback pin) with a different key and different
preservation duty. Unifying the decision behind one predicate would
need a per-aspect mode flag hiding three behaviors.
- **Migration.** None (zero-edit rejection: no behavior hunk, no test
hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** Canonical pair (cross-key,
shared template) vs three inline wordings (each names the violation +
the identifiers triage needs: flip names type+model+rule;
duplicate-primary names attempt+model+incumbent; rebind names
type+record kind) vs three neighbor wordings (override escape,
artifact identity, member-set diff). Collapsing the inline three into
the template drops the identifiers the duplicate-primary oracle pins
(`AdminItemType`, `Item`, `ItemType` — grep-from-stack-trace needs
each one); collapsing the neighbors imports foreign policies
(`override=True`, member-set compare) into the registry.
- **Behavioral proof.** `execution-verified` for singularity, all
raise/silent arms, preservation on every raise, pair atomicity
(workspace 36/36 + the authorized 10-passed focused run).
`static-reviewed` for oracle-body independence (plain test classes,
independent literals, no owner reads) and docstring-vs-body prose.
Observable behavior pinned: rewording the template moves exactly the
two cross-key messages; flipping one aspect's silence moves only that
aspect; the retired one-type raise stays retired. Rejects every
duplication direction in C1–C3.
- **Structural gate.** Deferred with reason (N1-proved): a
behavior-preserving hand copy of the owner passes every standing
oracle by construction (identical wording, identical identity
semantics — N1 executed exactly this and both behavior arms passed),
so no behavioral gate can pin unity; only a source census could, and
that is a bespoke existence test per helper, which [DRY.md][dry]
forbids for gate-only findings (same bar as the verified enum-cache,
definition-store, model-type-map, taxonomy, and accessor items).
Unity rests on the two-call-site shape (census, not a gate) plus the
recorded triggers below. Coverage that stays (each fails a real
break — the focused run is green on the unmutated tree): the reverse
row (fails a lost guard), the enum collision row (fails a lost
collision arm or dropped preservation), the idempotence rows (fail a
lost no-op), the flip pair (fail a lost direction), the
duplicate-primary row (fails a lost incumbent name), the rebind +
rollback rows (fail a lost pin/atomicity), the multi-type no-raise
pair (fail a restored one-type rule).
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`):
`registry.py`
`612bea87fdcf5e5a254caf70c9947b9535f638c3` (vs `HEAD`
`9cc8bb55…`: only the ledgered name-decode clause; vs
`ITEM_BASELINE` empty), `types/converters.py`
`9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`,
`rest_framework/serializer_converter.py`
`32904418a169941c2afa1c9cd6866c55debc64f3`,
`connection.py`
`3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` (vs `HEAD`
`93e998f2…`: the concurrent cursor-guard hunk, outside every cited
line — never edited), `exceptions.py`
`e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b`,
`tests/test_registry.py`
`e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10`,
`docs/dry/dry-file-registry.md`
`4350662b62d009cf4da67f59181458cd757d419f`,
[spec-018][spec-018]
`404f7c83b4a6ecaa244e006536b15ca407de6306`.
Searched population: whole package (117 `.py`, both trees). Any
fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owners).** The template
stays single-owned until one fires: T-wording fires if a third
cross-key collision wants the canonical form (add its label call site
— the helper grows one line, no new template); T-unify fires if two
inline wordings ever need to change for the same reason (today each
changes for its own triage need — flip rule, primary slot, record
kind); T-decision fires if one retry caller must share another
aspect's predicate (today re-import, converter retry, and pair pin
are independent). Durable homes: the `_already_registered` docstring
(both centralized sites + the three distinct phrasings),
[spec-018][spec-018] (rules + helper-survival note), this finding.
The plan's `## Responsibility index` row for
`already-registered-error-wording` already covers the member file; no
new row owed.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A primary-flip vs canonical pair. Difference: same-key
declaration conflict (flag flipped on re-register), not a cross-key
collision — names type + model + the immutability rule; the template's
labels (`against`/`as`) cannot name it. Trigger: a flip that becomes
a cross-key event (T-unify). Home: the helper docstring's distinct
phrasing clause + the `register` docstring arm.
- R-B duplicate-primary vs canonical pair. Difference: slot contention
between two live registrations (attempt + model + incumbent — all
three pinned by the oracle for stack-trace triage), not a key already
held by one object. Trigger: primary contention expressible as a key
hold (T-unify). Home: the helper docstring clause + the oracle pinning
all three identifiers.
- R-C definition-rebind vs canonical pair. Difference: record-identity
conflict on one type key (same class, different collected object —
pair-rollback pin), not a cross-key hold. Trigger: definitions keyed
by anything but `type_cls` (T-decision). Home: the helper docstring
clause + `register_definition` asymmetry note.
- R-D serializer-converter override cache vs registry template.
Difference: slot with an `override=True` escape (typo/double
registration fails loud but replaceable by intent); registry
collisions have no override — a stale primary must never be shadowed
by a flag. Different grammar (`"A serializer-field converter is
already registered for ...; pass override=True ..."`), different
policy, different owner. Trigger: converter slots losing the override
escape. Home: the `register_serializer_field_converter` docstring.
- R-E connection-class identity guard vs registry template.
Difference: generated-artifact provenance check (cached definition `is
not` the caller's — one node type, one connection shape), not a
registration event. Trigger: connection classes registered by key
rather than derived from definitions. Home: the
`_connection_type_cache` provenance comment block.
- R-F serializer choice-enum member-set guard vs registry enum arm.
Difference: same-name/different-members (name-keyed, member-set
compare, rename-or-align fix) vs same-key/different-class (tuple-keyed,
identity, first-wins). Disjoint key types by construction (model-less
choices cannot name the registry key). Trigger: one key able to name
both spaces. Home: the `_serializer_choice_enum` docstring + the
`_SERIALIZER_CHOICE_ENUMS` comment block.

## Defects

None meeting the [AGENTS.md][agents] bar (contract row + feasible
shape + wire/config input). Asymmetries checked while tracing that
hold: every raise preserves its incumbent (oracle-asserted); the
retired one-type-per-model message stays retired (multi-type pair
oracles pin the inverse); the `clear()`/rollback interplay keeps the
definition pin intact (D3 probe + rollback pack); the concurrent
`connection.py` cursor-guard hunk lies outside every cited line.

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace (36/36 + N1, copy `__file__` + copy DB `NAME` recorded, no
source mutation of the shared tree, `grep -c truncated` == 0); the one
authorized shared-tree focused test ran green post-trace (10 passed)
with zero edits in flight, so no run is invalidated. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells
`inapplicable by construction`: every executed claim is in-memory dict
work plus pure class/enum construction; the probes open no DB
(recorded `NAME` is the copy's own file, never touched). Full-suite
gate business is deferred to the final-gate item with reason: the entry
command authorizes workspace runs plus one focused `--no-cov` test,
and a green unmutated suite would discharge no failability proof for a
rejection that proposes no gate.

## Judgment

Single-owned template (one helper, two call sites), per-aspect
raise-vs-reuse policies intentionally separate (map / definitions /
enums each move alone under C1–C3), three inline wordings and three
neighbor wordings intentionally distinct with differences, triggers,
and existing homes. Consolidation rejected; zero edits; no new tests
owed (standing oracles at the mandated tier pin every challenged arm;
the wording-unity arm additionally carries N1's proved shape).

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`2430304eb87e0bdcb2009b7226d67e81cf1ed5ba`) is empty for
`django_strawberry_framework/registry.py` (and for every other family
path — the family owns that one file only); vs `HEAD` the single hunk
is the ledgered `relay-node-name-decode` docstring clause,
content-attributed before the first read, never edited. The only new
path is this artifact (untracked, owned by this item). The plan's
`## Owned changes` ledger holds exactly that one row on the family
path — confirmed by full read; nothing else to attribute, no stop
triggered. Dirty paths read but never edited: `connection.py`
(cursor-guard hunk outside all cited lines),
`rest_framework/serializer_converter.py`,
`types/converters.py`, `exceptions.py` (all clean vs `HEAD`
except as fingerprinted). No commit per standing rule.

After the (zero) edits: `uv run ruff check` +
`uv run ruff format --check` on the member path — all green, already
formatted (proves the no-edit claim mechanically; `.md` artifacts are
excluded from format). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/already-registered-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_already_registered.py` holding the 36 executed checks + N1).
No manifest (no `prove_failability.py` run — no gate added, N1 run
directly against the copy instead).

Worker 0 rows: tick Family `already-registered-error-wording` (this
artifact); no `## Responsibility index` change (provisional owner +
member file already covered, status `open` → `rejected`); no
`## Owned changes` append (zero tracked edits); no defect homing
(none found).

## Independent verification (Worker 2)

Exposure note: a docs-wide grep for the census string `already registered`
returned 5 snippet lines from this artifact, and insertion-point lookup read
only the `##`/`###` headings plus the `## Judgment` / `## Implementation
(Worker 1)` tail. The `## System trace`, `### Matrix`, `### Enumeration`,
`### Challenges`, `## Findings` (incl. `### F1`, `### Rejections`),
`## Defects`, and `## Pending execution` bodies were unopened at trace time.
Every site, wording, count, and owner claim below derives from the source,
test, and spec reads listed under Freshness, not from artifact prose.

### Sites and wordings (own census)

Searched population: every `.py` under `django_strawberry_framework/` for
`already registered` (5 hits) plus a case-insensitive `already` sweep for
neighbor grammars; `tests/` for `already registered`; `docs/SPECS/
spec-018-meta_primary-0_0_6.md` as the contract source for the map arms.
All other package modules excluded on the strength of the grep (no raise
producer), not by name.

Template definition (1): `django_strawberry_framework/registry.py::
TypeRegistry._already_registered` builds
`f"{name} is already registered {label} {existing_name}"`.

Canonical consumers (2), both by name through the owner:
- `registry.py::TypeRegistry.register` reverse-collision:
  `self._already_registered("against", type_cls.__name__,
  existing_model.__name__)` — same class, different model.
- `registry.py::TypeRegistry.register_enum` collision:
  `self._already_registered("as", f"{model.__name__}.{field_name}",
  existing.__name__)` — same `(model, field_name)` key, different enum
  class.

Inline wordings intentionally outside the template (3):
- `register` primary-flip: `f"{type} is already registered for {model};
  primary flag cannot be flipped on re-register"` (grammar: `for` +
  semicolon clause; both flip directions raise).
- `register` duplicate-primary: `f"Cannot register {type} as primary for
  {model}; {incumbent} is already the primary type"` (grammar:
  `Cannot register` lead + `is already the primary type` tail; attempt
  does not append).
- `register_definition` rebind: `f"{type} already has a registered
  DjangoTypeDefinition"` (grammar: `already has a registered`, no `is
  already registered`; same-object re-store is a no-op).

Neighbor wordings intentionally outside the family (3):
- `rest_framework/serializer_converter.py::
  register_serializer_field_converter`: `"A serializer-field converter is
  already registered for {field!r}; pass override=True to replace it, or
  register a distinct subclass."` Difference: replace affordance
  (`override=True`) vs the registry's fail-loud no-override policy.
- `registry.py::TypeRegistry.register_type_teardown`:
  `"Cannot register class teardown for unregistered type {name}"`.
  Difference: opposite polarity (`unregistered`, not `already`), different
  trigger (unknown type, not collision).
- `registry.py::TypeRegistry.definition_for_graphql_name` miss/ambiguity:
  `"No registered Relay-Node DjangoType has GraphQL type name {name!r}"` /
  `"... is ambiguous across multiple Relay-Node DjangoTypes (...)"`.
  Difference: lookup miss/ambiguity on `graphql_type_name`, not a
  registration collision.
- Prose only, not a raise: `types/base.py` comment `"whichever type was
  already registered at __init_subclass__ time"` (explanation of the
  import-order trap closed by spec-018); `_check_mutable` finalized guard
  (`"TypeRegistry is finalized; ..."`) carries no already-registered
  spelling.

Test pins (oracles, read not rewritten): `tests/test_registry.py::
test_register_same_class_against_two_models_raises` (reverse),
`test_register_enum_different_class_for_same_key_raises` (enum),
`test_register_enum_same_class_is_idempotent` (enum noop),
`test_register_same_type_twice_is_idempotent` +
`test_register_returns_false_for_idempotent_re_register` (map noop),
`test_register_same_type_re_register_with_flipped_primary_false_raises` /
`..._flipped_primary_true_raises` (flip both directions),
`test_register_two_primaries_for_same_model_raises_configuration_error`
(duplicate-primary, asserts non-append),
`test_register_definition_rejects_different_definition_for_same_type`
(rebind, asserts same-object noop + preserved pin),
`test_register_with_definition_rolls_back_register_on_definition_failure`
/ `..._rollback_clears_primary` /
`..._rollback_restores_pre_existing_primary` /
`..._idempotent_re_register_does_not_corrupt_state` /
`..._idempotent_re_register_preserves_primary` (rollback matrix);
`tests/rest_framework/test_converter.py` pins the serializer-converter
wording separately (`"already registered for 'CharField'"`).

### Raise-vs-reuse per aspect (own decision)

- Map (`register`): append-True (new type, no primary conflict, incl. the
  normal multi-type case per spec-018) / idempotent-False (same type, same
  model, flag matches stored state) / flip-raise (same type, flag mismatch
  either direction — primary is a declaration, not mutable) /
  duplicate-primary-raise (different type, `primary=True` against an
  occupied slot) / reverse-raise via template (same class, different
  model — `_models` stays one-to-one). Each arm moves alone.
- Enum (`register_enum`): same-class-noop (falls through to the same store;
  keeps the `get_enum`-then-`register_enum` retry pattern working) /
  different-raise via template. Moves alone.
- Definition (`register_definition` + `register_with_definition`):
  same-object-noop / rebind-raise, plus snapshot-conditional rollback in
  `register_with_definition` (`pre_primary` + `appended`: pop vs restore
  vs no-op). Moves alone.

Divergence judgment — the map-idempotent-False vs definition-rebind-raise
"same" re-registration is CORRECT, not a hidden inconsistency. Concrete
sequence hitting both arms on one object pair:

1. `r = TypeRegistry()`; `r.register(Category, T)` returns True.
2. `r.register_definition(T, d1)` stores `d1`.
3. `r.register(Category, T)` returns False, no raise (map arm:
   link already exists, flag matches).
4. `r.register_definition(T, d2)` with `d2 is not d1` raises
   `ConfigurationError("... already has a registered
   DjangoTypeDefinition")` (definition arm: object identity differs).
5. Via the pair entry: `r.register_with_definition(Category, T, d2)`
   internally gets `appended=False` from step-3-shaped `register`, then
   raises from `register_definition`, skips rollback, and preserves
   `(Category, T, d1)` intact — pinned by
   `test_register_with_definition_idempotent_re_register_does_not_corrupt_state`.

Contract-stated per arm: `register`'s docstring promises idempotent
no-op on matching re-register; `register_definition`'s body promises
raise only on `existing is not definition`; `register_with_definition`'s
docstring promises only-THIS-call state rolls back; spec-018 pins the
map arms (multi-type allowed, flip raises either direction, reverse
collides, per-model collision retired). Two stores (type-model link vs
type-definition object), two reasons to change. No behavior defect; the
separation is the policy, and unifying the outcomes (e.g. making the map
rebind-raise or the definition silently rebind) would break the pinned
oracles above.

### Definition counts (own challenges)

- C1 reword the canonical `"X is already registered <label> Y"` form: 1
  (`_already_registered`; both call sites follow by construction; the 3
  inline + 3 neighbor wordings are untouched — different grammars).
- C2 silence (or flip the sense of) one aspect, e.g. make primary-flip a
  no-op: 1 (that branch only; template, enum, definition, rollback
  untouched).
- C3 restore the retired per-model `"<model> is already registered as
  <type>"` collision: 1 (a new branch in `register`; template untouched;
  spec-018 keeps it retired — the multi-type case must not raise).

### Owner I would choose

`django_strawberry_framework/registry.py::TypeRegistry._already_registered`
— the narrowest cohesive owner: stateless pure factory, both legitimate
consumers are already `TypeRegistry` methods (no dependency reversal, no
sibling import), responsibility is exactly the cross-key collision
phrasing. The 3 inline wordings stay at their raise sites (distinct
contracts, distinct triggers, distinct change reasons); the 3 neighbors
stay with their owners (replace affordance / polarity / lookup vs
collision). No broader or higher owner is importable without reversing an
edge.

### Wording census result

Package-wide `is already registered` producers: exactly the template (2
call sites, 1 spelling) + the flip inline (`is already registered for
...; primary...`) + the duplicate-primary tail (`is already the primary
type`) + the serializer-converter hook (`is already registered for ...;
pass override=True`). No stray spelling: the definition rebind uses
`already has a registered` (correctly outside the census), teardown uses
`unregistered`, name-decode uses `No registered`/`ambiguous`. Tests pin
each spelling by substring at the mandated tier; docs (spec-018) pins
the retired message as retired, so no resurrection risk.

### No-gate reasoning (own judgment)

No structural gate owed, same standard as the verified siblings
(model-type-map, definition-store, pending-ledger, enum-cache,
finalize-gate, relay-node-name-decode): a hand copy of the one-line
f-string passes every behavior oracle (substring match), so a gate would
have to be a bespoke name/existence assertion per helper — forbidden by
`DRY.md` "Deciding and consolidating / The finding record / Structural
gate" (`gate-only` needs a justified bypass population; none is shown:
the population is 2 call sites in one class, the bypass is implausible
to drift silently since any rewording still matches the pinned
substrings). Standing oracles already fail on bypass-by-rewording only
insofar as a contract change should fail them — that is oracle duty, not
gate duty.

### Freshness (re-hashed by Worker 2)

- `django_strawberry_framework/registry.py`: worktree
  `612bea87fdcf5e5a254caf70c9947b9535f638c3`, HEAD
  `9cc8bb553fd417fc465809a541769a8383469cda`; delta is the ledgered
  sibling `relay-node-name-decode` docstring clause only (verified by
  `git diff HEAD --`).
- `tests/test_registry.py`: worktree ==
  HEAD `e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10` (clean).
- `django_strawberry_framework/rest_framework/serializer_converter.py`:
  `32904418a169941c2afa1c9cd6866c55debc64f3` == HEAD (clean).
- `django_strawberry_framework/exceptions.py`:
  `e06b0b7f776e2f182bc9bfd9e2ee2836e660f55b` == HEAD (clean).
- `django_strawberry_framework/types/base.py`: worktree
  `4bd9ad163eeb692ab9d3ae55c3d18a08088f94a7` vs HEAD
  `91c587477ff8257e80dbb9a9c79859f34c5b4c7e` (dirty); hunk is the
  ledgered `relay-pk-suppression-read-mirror` consolidation
  (`_is_suppressed_relay_pk` extraction); cited lines (the
  `register_with_definition` call and the `already registered` comment)
  untouched — verified by diff-grep; concurrent work, left alone.
- `tests/rest_framework/test_converter.py`:
  `9d5d0eaf7087bf46bda189e9f117fff343bf0f5f` == HEAD (clean).
- Contract source `docs/SPECS/spec-018-meta_primary-0_0_6.md`:
  `404f7c83b4a6ecaa244e006536b15ca407de6306`.
- Consumers confirmed live: `types/base.py` (`register_with_definition`
  from `DjangoType.__init_subclass__`), `types/converters.py`
  (`register_enum` from `convert_choices_to_enum`, `get_enum`-then-register
  pattern).

### Pending execution (Worker 2 expectation)

None owed from this trace: pure in-memory wording + branch policy,
observable behavior fully pinned by standing oracles at the mandated
tier; inspection is the strongest evidence (no ordering, transactional,
async, or timing axis per principle 8). Any `proof:` entry would be
over-claiming; will confirm the artifact lists zero `proof:`/`gate:`
commands on read. Sharded/Postgres cells inapplicable by construction
(no database, alias, or dialect decision on these paths).

### AGENTS.md prose on the empty diff

Item-scoped diff vs `ITEM_BASELINE`
(`2430304eb87e0bdcb2009b7226d67e81cf1ed5ba`) is empty for
`django_strawberry_framework/registry.py` (verified: `git diff <item> --`
the path prints nothing — worktree matches the item entry state). Vs
`HEAD` (`bfaee91d`) the single hunk is the ledgered sibling
`relay-node-name-decode` trigger clause, content-attributed to the
plan's `## Owned changes` row before the first read, never edited by
this item. Zero production edits is the correct outcome for a
single-owned-template rejection. `uv run ruff format --check` +
`uv run ruff check` on the member path both pass. No commit, no
`CHANGELOG.md` touch, concurrent dirt preserved.

### Reconciliation (Worker 2, after reading the artifact)

Verdict: `verified`. Agreement or difference per reconciliation point:

1. Wording definition (`_already_registered`, single f-string) — AGREE.
2. Canonical consumers (`register` reverse-collision label `against`,
   `register_enum` collision label `as`) — AGREE (2 call sites, mine
   match line for line).
3. Per-aspect policy arms intentionally separate (map
   idempotent-False/flip-raise/append-True/duplicate-primary/reverse;
   enum same-class-noop/different-raise; definition
   same-object-noop/rebind-raise + rollback) — AGREE. Divergence
   judgment: the map-idempotent-False vs definition-rebind-raise split
   on the "same" re-registration is contract-stated per arm
   (`register` docstring idempotence + `register_definition` identity
   body + `register_with_definition` snapshot-conditional rollback +
   spec-018 map rules), demonstrated by the concrete
   register-then-rebind sequence in this section — NOT a defect.
4. Challenges C1 reword → 1, C2 flip-silence one aspect → 1, C3
   restore-per-model-raise → 1 — AGREE (same posits, same counts).
5. Owner stands (narrowest, stateless, no dependency reversal) — AGREE.
6. REJECT shape (template + policy + 3 inline + 3 neighbor wordings,
   each with difference + trigger + home) — AGREE on verdict and on
   the inline triple. DIFFERENCE on neighbor composition, no verdict
   change: my token-scoped census named serializer-converter-override
   (matches R-D), teardown-`unregistered`, and name-decode
   miss/ambiguity; the artifact's mechanism sweep names R-D plus the
   connection-class identity guard (R-E,
   `"already has a generated connection class ..."`) and the
   serializer choice-enum member-set guard (R-F,
   `"... two different member sets ..."`), neither of which carries
   the `already registered` literal so my grep could not see them.
   The artifact's triple is the mechanism-correct neighbor set and
   each rejection's difference + trigger + home is valid; my two
   alternates are additionally family-external (different polarity /
   lookup-vs-collision) and equally correctly excluded. No missed
   consolidation either way.
7. Zero edits — AGREE (both diffs re-verified by Worker 2: empty vs
   `ITEM_BASELINE`, single ledgered sibling hunk vs `HEAD`).
8. No defects — AGREE (no `(Worker 2)` entries appended; the point-6
   composition difference breaks no contract row and reaches no wire
   input, so it is a trace-strength note, not a defect).
9. No pending execution (36/36 + N1 executed; 1 focused run 10
   passed; sharded/PG inapplicable) — AGREE. The `## Pending
   execution` record is well-formed (zero `proof:`/`gate:` entries,
   copy `__file__` + copy DB `NAME` bound, no shared-tree mutation,
   full-suite deferral reasoned from the entry command's scope).
   Worker 2 ran no workspace copy and no pytest: for a zero-edit
   rejection with an executed N1 and green standing oracles,
   re-execution would add no evidence. Sharded/Postgres
   inapplicability is sound (in-memory dict paths; probes open no
   DB). `uv run ruff format --check` + `uv run ruff check` on the
   member path both pass (re-run by Worker 2, green).

Freshness re-hash (Worker 2): every artifact fingerprint matches the
worktree — `registry.py` `612bea87…`, `types/converters.py`
`9ceb34af…`, `serializer_converter.py` `32904418…`, `connection.py`
`3c4d5dcb…` (concurrent cursor-guard hunk, outside all cited lines),
`exceptions.py` `e06b0b7f…`, `tests/test_registry.py` `e330cf…`,
`spec-018` `404f7c83…`. Extra Worker-2 pins: `types/base.py`
worktree `4bd9ad16…` vs HEAD `91c58747…` is the ledgered
`relay-pk-suppression-read-mirror` consolidation (cited lines
untouched); `tests/rest_framework/test_converter.py` `9d5d0eaf…`
clean. No oracle was rewritten to read from the owner (independent
literals, plain test classes). AGENTS.md prose rules hold: no
process provenance, `path::Symbol` citations, tests at the mandated
tier, no commit, concurrent dirt preserved.

Exact plan rows for Worker 0 (Worker 0 alone edits the plan):
- Tick `## Families`: `- [ ] Family already-registered-error-wording`
  → `- [x] Family already-registered-error-wording — verified (Run
  0.0.15 2026-09-19-1; REJECTED single-owned template, per-aspect
  policy separate, 3 inline + 3 neighbor rejections with triggers, no
  gate; zero edits; no pending execution)`.
- Index status: the `already-registered-error-wording` row status
  `open` → `rejected` (owner + member file already covered, no new
  row).
- `## Owned changes`: no append (zero tracked edits).
- Scratch paths (Worker 0 removal, by explicit path, after `verified`):
  `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/already-registered-w1`
  (Worker 1 WS tree incl. `probe_already_registered.py`). Worker 2
  created no scratch (static verification + shared-tree ruff only;
  no `docs/dry/temp-tests/` dir, no workspace copy).


<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->
[spec-018]: ../SPECS/spec-018-meta_primary-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[converters]: ../../django_strawberry_framework/types/converters.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[registry]: ../../django_strawberry_framework/registry.py
[serializer-converter]: ../../django_strawberry_framework/rest_framework/serializer_converter.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
