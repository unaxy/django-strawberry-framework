# DRY review: `optimizer-hint-shape`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the optimizer hint shape: the `OptimizerHint` record
(fields, defaults, sentinel, factories), its construction-time validation,
and how producers and consumers share its meaning (the
`Meta.optimizer_hints` container contract, storage, and every read).

Traced at HEAD bytes (`5c3496e0`) through `git show HEAD:<path>` and
`git grep ... HEAD`. That instrument choice is load-bearing: all five
indexed files are dirty in the working tree with the concurrent bug-hunt
truth/lazy migration (hints 12+/18-, walker 13+/11-, nested_planner 11+/1-,
types/base 228+/232-, types/definition 59+/101-, none of it in the plan's
`## Owned changes` ledger), so working-tree reads do not show the bytes
this verdict is about. Every line cited below is a HEAD line; every
fingerprint is a HEAD blob except the worktree/ITEM_BASELINE pins recorded
for attribution. The working tree equals ITEM_BASELINE (`cac31c9e...`) on
all five indexed files, so every dirty hunk predates dispatch. Prior
file/family records were read as orientation and adjudicated fresh;
nothing below is inherited.

Sites found, by role. One definition; everything else composes it by name.

- Definition. `django_strawberry_framework/optimizer/hints.py::OptimizerHint`
  (`:115`: frozen dataclass, five fields `:143`-`:147`, `SKIP` declaration
  `:155`, `__post_init__` `:157`, factories `strategy` `:216` /
  `select_related` `:230` / `prefetch_related` `:235` / `prefetch` `:240`,
  post-body `SKIP` assignment `:280`), with `::_require_prefetch` (`:65`)
  and `::_require_strategy` (`:83`).
- Container producer/validators (`types/base.py`). `::_meta_optimizer_hints`
  (`:1092`: None-to-`{}`, Mapping gate, live str-key guard, `dict()` copy);
  `::_validate_optimizer_hints` (`:1510`: str-key re-check, model-surface
  typo guard, selected-relation gate, `isinstance(v, OptimizerHint)` value
  gate); `::_ValidatedMeta.optimizer_hints` (`:1310`, pre-validation
  `dict[str, object]`); the `__init_subclass__` call site (`:706`) and the
  definition construction with cast (`:880`).
- Storage. `types/definition.py::DjangoTypeDefinition.optimizer_hints`
  (`:177`, `dict[str, OptimizerHint]` annotation).
- Consumers. `optimizer/walker.py::_resolve_optimizer_hints` (`:541`,
  None-definition to `{}`, falsy-hints `or {}`) with `hints_map` reads
  (`:741`, `:888`, `:904` into the sibling dispatch);
  `optimizer/nested_planner.py` strategy read (`::_select_nested_strategy`
  `:224` via `getattr(hint, "nested_strategy", None)` plus sibling
  re-resolution) and map reads (`:1165`-`:1166`, `:1426`) through the
  injected `resolve_optimizer_hints` callable (`:1092`, bound to the walker
  helper at `walker.py:1843`); `optimizer/extension.py::check_schema`
  inline read (`:1549`, `definition.optimizer_hints or {}` after a
  None-definition guard); the package-root re-export (`__init__.py:34` +
  `:158`).
- Oracles. `tests/optimizer/test_hints.py` (sentinel, four factories,
  frozen immutability, equality, every conflict arm, hostile selections,
  runtime annotation resolution); `tests/optimizer/test_walker.py`
  (empty-hint no-op `:1896`, consumer-assigned gates);
  `tests/types/test_base.py` (container gates including the direct
  `_validate_optimizer_hints({123: ...})` second-gate pin `:2536`);
  `tests/optimizer/test_extension.py` (audit skip `:4502`); live suites
  (`test_library_api.py`, `test_optimizer_auto_api.py`,
  `test_combined_visibility_api.py`); hints-as-input rows in
  `test_nested_fetch.py`, `test_multi_db.py`, `test_lateral_pg_parity.py`,
  and `test_relay_connection.py`; `tests/base/test_init.py` (root export
  gate). Example schemas (`library`, `glossary`, `kanban`) declare hints
  as consumers.
- Projections. The definition docstrings (record, factories, helpers,
  sentinel); the `conf.py` None-stance paragraph (`:25`, naming the
  `Meta.optimizer_hints = None` coercion as documented contract);
  `types/__init__.py:18` module docstring line; one-line mention comments
  in `lateral_fetch.py:57`, `nested_fetch.py:8`, `utils/querysets.py:3520`,
  and the `finalizer.py:172` typo-formatter cross-reference; GLOSSARY
  anchors, README, specs, KANBAN.

Connected behavior examined: the sibling skip predicate (`hint_is_skip`,
call sites in walker/nested_planner/extension), the sibling strategy
selection (`nested_fetch.py::resolve_strategy` plus `StrategySelection`,
extension kwarg), the sibling hint dispatch (`walker.py::_apply_hint` with
its plan-time refusals), the sibling prefetch-lookups read, and the
`test_hints.py` hostile oracles pinning the validation boundary. Each is
excluded with a contract difference under Findings, never absorbed.

## Verification

### Matrix

1. Cross-flavor policy mirroring. SEARCHED, complete. Every other public
   surface was censused for a per-field override record: the frozen
   dataclasses in filters/orders/mutations/forms/rest_framework/types are
   per-subject records (input triples, operation envelopes, hook contexts)
   with no field-override member, and `Meta.relation_shapes` is a
   string-valued key, not a record. No twin vocabulary exists; hints are
   optimizer-only.
2. Sync/async twins. INAPPLICABLE with reason: the target has no async
   surface. `async def` / `await` censused at zero sites across
   `optimizer/hints.py`, `optimizer/walker.py`, and
   `optimizer/nested_planner.py` at HEAD; construction and validation are
   pure synchronous dataclass machinery and every plan-time read runs in
   synchronous planning.
3. Derived rather than repeated knowledge. SEARCHED, complete. Every
   consumer reads the shape directly (attribute reads, `hints_map.get`,
   one `getattr` with default for a None-able input). Field-keyword
   constructions (`force_select=` / `force_prefetch=` / `prefetch_obj=` /
   `skip=` / `nested_strategy=`) censused package-wide: the production
   sites are exactly the four factories plus the `SKIP` assignment (the
   `skip=` hits in forms/rest_framework resolvers are unrelated filter
   lambdas). No site rebuilds a hint from its fields, re-derives the
   field set, or recomputes a default.
4. Inverse / round-trip pairs. INAPPLICABLE with reason: hints have no
   serialized form. `to_dict` / `from_dict` / `asdict` / `astuple`
   censused at zero sites in `optimizer/hints.py`; nothing encodes,
   packs, or parses a hint.
5. Contracts restated in another medium. SEARCHED, complete. Production
   (the definition plus container gates), oracles (every `test_hints.py`
   class spells its expectation independently, plus walker/base/extension
   and live rows), example declarations, and projections (docstrings, the
   `conf.py` paragraph, GLOSSARY/README/specs) are classified above; each
   medium moves for its own reason (an intentional contract change
   legitimately moves production + oracles + docs together) and only the
   production definition is counted.
6. Enforcement by omission. SEARCHED, complete. Family enumerated and
   each member checked: `force_select` (bool gate plus dispatch arm),
   `force_prefetch` (bool gate plus arm), `prefetch_obj` (Prefetch-type
   gate plus arm), `skip` (bool gate plus sibling predicate read),
   `nested_strategy` (strategy gate plus planner read), `SKIP` (single
   assignment plus identity arm), four factories (each pins exactly one
   shape), container keys (str-type plus model-surface plus
   selected-relation gates), container values (`isinstance` gate). No
   member lacks the guard its contract requires; the two deliberate
   allowances (empty no-op, `force_prefetch` + strategy) are stated in
   the owner docstring and pinned by oracles.

### Enumeration

Instrument: `git grep` censuses over HEAD blobs across all 117 package
`.py` files, plus a full HEAD read of `optimizer/hints.py` and region
reads of every file a hit implicates. Populations censused, not sampled:
`OptimizerHint` mentions (11 files: the definition, root re-export,
walker, nested_planner, extension, types/base, types/definition,
nested_fetch, lateral_fetch, the types `__init__` docstring, the
querysets comment); `optimizer_hints` mentions (9 files: conf, extension, hints,
nested_fetch, nested_planner, walker, types/base, types/definition,
types/finalizer); `class OptimizerHint` (1); `SKIP` assignments (1:
`:280`);
factories (4); `_require_*` definitions (2) with call sites (4, all
in-file: two factories plus two `__post_init__` arms); `isinstance(v,
OptimizerHint)` gates (1); `definition.optimizer_hints or {}` reads (2:
walker helper, extension inline); `getattr(hint, "nested_strategy",
None)` (1); `OptimizerHint(` production constructions (1: the `SKIP`
assignment; the example direct construction and every test construction
are declaring consumers / oracles). Every member lands in F1, an
R-exclusion, or a named sibling/file-local home; nothing is unassigned.

### Challenges

Each challenge posits a change on one of the rule's variation axes and
counts authoritative definitions that must move. Consumers, oracles, and
projections that also move are listed, never counted.

- C1 (record-fields axis): add a sixth field with a factory. Moves only
  the dataclass declaration plus its factory in `optimizer/hints.py`;
  the `isinstance` container gate follows by name, and existing readers
  are untouched until a consumer for the new field is written (new code,
  not a moved definition). Count: 1.
- C2 (validation axis): change a conflict arm (admit `skip` +
  `force_prefetch`, or reject the empty no-op). Moves only
  `__post_init__`; the factory helpers, the container gates, and the
  walker dispatch order (which the owner docstring states is
  documentation, not arbitration, and which the sibling dispatch family
  owns) do not move as definitions. Oracles pinning the old arm move as
  oracles. Count: 1.
- C3 (sentinel/factory axis): replace the `SKIP` spelling or add a
  factory. Moves only the sentinel assignment / new factory in
  `optimizer/hints.py`; the sibling predicate's identity arm reads the
  sentinel by name and follows by construction. Count: 1.
- C4 (value-vs-container separation control): change the value shape
  (C1) and the container key policy moves nowhere; change the container
  policy (scalar-field keys admitted) and the value shape moves nowhere
  (the `_validate_optimizer_hints` selected-relation gate alone). Two
  rules, two owners, each count 1. This confirms the intentional
  separation between the hints-owned value contract and the
  types/base-owned container contract (file-local F-HINTREAD /
  F-HINTVAL).
- C5 (read-discipline control): the two `or {}` spellings move alone
  under one-sided changes. "The walker must hand out a copy so planning
  cannot mutate the definition map" moves only the walker helper (the
  audit only reads); "the audit must tolerate a definition missing the
  attribute" moves only the extension inline. Each moves exactly 1 body
  and never the other, and neither fires in production today (the field
  is typed non-optional and always a dict off the validated path), so
  sharing them would relieve no change obligation. Count per read: 1.

All counts are 1. No posited change moves two definitions of one
contract.

## Findings

### F1: the hint value contract is single-owned at `OptimizerHint` (CONFIRM single ownership)

Contract + variation: one frozen record with five fields (`force_select`,
`force_prefetch`, `prefetch_obj`, `skip`, `nested_strategy`), one sentinel
(`SKIP`), four factories each pinning exactly one shape, and
construction-time rejection of every other shape: non-bool flags, `skip`
combined with anything, `force_select` + `force_prefetch`, non-`Prefetch`
or force-combined `prefetch_obj`, and `nested_strategy` combined with
`skip` / `prefetch_obj` / `force_select` or failing sibling resolution.
Deliberate allowances: the empty no-op (the walker falls through to
cardinality dispatch) and `force_prefetch` + `nested_strategy`
(redundant-but-harmless, stated). Varies on fields, conflict arms, and
factories (C1-C3).

Sites + roles: definition `optimizer/hints.py::OptimizerHint` with
`::_require_prefetch`, `::_require_strategy`, and the post-body `SKIP`
assignment; consumers compose by name (walker dispatch and reads,
planner strategy read, the types/base shape-agnostic value gate, the
definition annotation, the root re-export, example declarations);
oracles spell expectations independently (`test_hints.py` minus the
sibling predicate class, walker/base/extension/live rows); projections
describe (docstrings, the `conf.py` paragraph, GLOSSARY/README/specs,
mention comments).

Challenges: C1-C3 count 1 definition each; C4 confirms the container
separation; C5 confirms the reads are independent. Consumers, oracles,
and projections that move with an intentional contract change are listed
in each challenge, never counted.

Owner + lifetime: `optimizer/hints.py::OptimizerHint` by responsibility
(principle 7): the narrowest module every legitimate consumer already
imports downward with no reversal (the walker-side reason the class
lives in the optimizer subpackage is stated in the module docstring),
holding the record, the factories, the validation, and the sentinel
together so one edit moves the whole contract. No stored derivation
beyond frozen immutability: instances are immutable values with no
cache, no publish point, and no invalidation; the `Meta`-to-definition
flow copies the mapping once at class creation.

Migration: none owed; every site already composes the owner by name.
The factory-side `_require_*` calls exist because `None` is each
field's legitimate default (without them `prefetch(None)` /
`strategy(None)` would collapse into the no-op hint); that sharing
already exists inside the owner.

Distinct behavior: the skip read (sibling predicate), strategy
resolution (sibling selection), plan-time application (sibling dispatch),
and Prefetch-lookup derivation (sibling lookups) stay outside; R3-R7
record each boundary.

Behavioral proof: static-reviewed. Nothing moves, so no equivalence
proof is owed; the census (one class, one sentinel assignment, four
factories, two helpers with four in-file calls, one value gate) plus
the challenge counts decide the verdict. The oracles that would catch a
behavioral drift already exist in-tree (`test_hints.py`
conflict/factory/hostile rows, the container bad-values row, live
strategy rows).

Structural gate: already present, no new gate owed. Enforcement is the
container `isinstance(v, OptimizerHint)` gate: any second shape fails
schema construction with the dedicated message, pinned by the
bad-values oracle. Negative control: a lookalike (dict,
`SimpleNamespace`, second record) offered as a hint value is rejected
by that gate while every `test_hints.py` row still passes against the
true owner (the rows construct the owner, never the lookalike). A
bespoke "exactly one class" existence test per helper is forbidden
shape; the plausible bypass (a consumer accepting an unvalidated shape)
is exactly what the value gate closes, and the first-run check holds
(the census above shows one class at HEAD).

Coupling: none. No defect blocks landing because nothing lands.

Freshness: input pins under Judgment; any fingerprint change reopens
the finding.

### Rejections and exclusions (contract difference + trigger each)

- R1. Extension inline `or {}` versus the walker helper. Difference:
  narrowed read at a site whose definition is already guarded non-None
  (audit context, read-only) versus the None-able request-time resolver;
  C5 moves each alone. Trigger: `optimizer_hints` becomes genuinely
  Optional in production (a real None off the validated path), at which
  point both reads converge into the helper.
- R2. `_meta_optimizer_hints` key gate versus the `_validate_optimizer_hints`
  key re-check. Difference: production entry gate versus self-validating
  second phase pinned by the direct-call oracle (`test_base.py:2536`);
  same file, same owner, intentional per verified hostile-mapping N3,
  with both phases file-local to types/base (F-HINTREAD / F-HINTVAL).
  Converged, not re-litigated. Trigger: the key policy leaves
  `types/base.py`, at which point the two phases home with it together.
- R3. `hint_is_skip`. Sibling family `optimizer-hint-skip-predicate`
  (queued, separate item). Difference: the None/sentinel/attribute read
  with the audit's never-raises contract versus the value shape it
  reads. Trigger: `skip` leaves the record (the predicate has nothing
  left to read).
- R4. `resolve_strategy` plus `StrategySelection`. Sibling family
  `nested-connection-strategy-selection`. Difference: name-to-instance
  resolution with hostile-dunder armor versus field carriage; the hint
  validates through it by name at build time. Trigger: the strategy
  vocabulary moves into the hint module.
- R5. `_apply_hint`. Sibling family `optimizer-hint-dispatch`.
  Difference: plan-time application with plan-time refusals (to_attr,
  many-side select_related) versus construction-time shape; the dispatch
  order is documentation because `__post_init__` already rejected every
  arbitrable conflict. Trigger: dispatch moves into the record.
- R6. Prefetch-lookup derivation. Sibling family
  `attached-prefetch-lookups-read`. Difference: reads off the hinted
  `Prefetch` object (lookup strings) versus the shape carrying the
  object. Trigger: lookup derivation moves into the hint module.
- R7. `_select_nested_strategy` re-resolution. Consumer of F1 plus R4.
  Difference: plan-time default fallback (`active_strategy()` when no
  hint sets a strategy) versus build-time typo-loud validation;
  re-resolution cannot raise on a landed schema. Trigger: the planner
  stops re-resolving and the factory return becomes the plan-time
  instance.
- R8. `_ValidatedMeta.optimizer_hints: dict[str, object]`. Stage
  separation: the pre-validation snapshot (values unvalidated by
  construction; `__init_subclass__` gates before the cast) versus the
  post-validation definition map. Trigger: validation moves before the
  snapshot.
- R9. The `isinstance` value gate. Enforcement site at the container
  boundary, not a second definition: it invokes the shape where the
  rule must hold and stays there. Trigger: a second accepted value type
  (the gate genuinely branches).

Convergences checked fresh, none re-litigated: hostile-mapping N3 plus
the f12 vocabulary seam (the hints double gate is intentional
self-validation); types/base F-HINTREAD / F-HINTVAL / F-TYPOFMT
file-locals (container read, container validation, typo format); the
run-5 hints-file near-miss on double key-stringness now homed via R2.
No new index rows are owed: the family row exists, the four siblings
are queued, and every R-exclusion above is a boundary, not a family.

## Defects

None found. Checks performed while tracing for contract: the module
placement claim (walker consumer plus root re-export) matches the
imports; the `__post_init__` priority-order claim matches the sibling
dispatch arms (every arbitrable conflict is rejected at construction);
the `_require_strategy` dunder-armor claim was verified against the
`resolve_strategy` body (base-`str` slot equality, hash-free linear
registry scan, `getattr` plan read with `BaseException` absorb,
safe-rendered message); the `_validate_optimizer_hints` "already
shape-checked" claim matches the `__init_subclass__` call order; the
extension-to-walker import direction is consistent (no cycle); the axis
6 omission sweep closed with every member guarded. No already-ticked
row was found factually wrong: the run-5 shape description matches
HEAD's five-field record and the blob drift since is typing/hardening
with no second definition, so per the drift rule nothing reopens.

## Pending execution

None. The verdict is static-decidable (definition counts from source
census plus challenges); no equivalence proof is owed because nothing
moves, and no gate is relied on beyond the container `isinstance`
enforcement and the in-tree oracles. No pytest ran: executing oracles
can only confirm the suite is green, which proves nothing about
definition count. The entry's one authorized focused test was not
spent. No workspace copy was created (no source-mutating proof ran);
census probes were read-only greps plus source reads in the shared
tree. The `--cell sharded` and `--cell pg` cells are inapplicable by
construction: the target reaches no database, alias, or dialect
decision (construction-time validation plus in-memory map reads; the
PG-marked live strategy rows pin sibling fetch behavior with hints as
input, and no claim here depends on their execution).

## Judgment

The optimizer hint shape is already one rule in one body:
`optimizer/hints.py::OptimizerHint` holds the record, the sentinel,
the factories, and every conflict arm; the container layer validates
keys and enforces the value type without restating the shape; every
read composes by name. Everything that looks like a second definition
is either a narrowed read that moves alone (R1), an intentional
self-validating phase owned in the same file (R2), a queued sibling
family (R3-R6), a plan-time consumer of this shape plus a sibling
(R7), a validation stage (R8), or the enforcement site itself (R9).
CONFIRM single ownership, zero edits, no new index rows owed.

Type gates (shared venv, tree-state -- zero edits, so these record the
concurrently-dirty tree, not a change): `uv run mypy` clean (119
files), `uv run basedpyright` 0 errors / 0 warnings / 0 notes, `uv run
python scripts/check_any.py` 130 uses at 90 sites (matches the run-9
baseline).

Freshness (full input pins; `git hash-object` WT vs `git rev-parse
HEAD:path`; HEAD `5c3496e0`; ITEM_BASELINE
`cac31c9e030e2c7474f4f5ea959349dfef09ab1e` equals WT on all five
indexed files):

- Indexed 5: `optimizer/hints.py` WT `ee68ae03` HEAD `f6776564`;
  `optimizer/walker.py` WT `4fd8077f` HEAD `13e1be20`;
  `optimizer/nested_planner.py` WT `b6ff0a0e` HEAD `8c3a45f5`;
  `types/base.py` WT `763a5acc` HEAD `e8416cc0`;
  `types/definition.py` WT `ef9e871a` HEAD `fd339a7c`.
- Read neighbors (HEAD): `__init__.py` `8b165672` (clean);
  `conf.py` `eccddc21`; `optimizer/extension.py` `b7b6c434`;
  `optimizer/lateral_fetch.py` `a48cb0a4` (clean);
  `optimizer/nested_fetch.py` `bedaa76e`; `types/__init__.py`
  `1bf69028` (clean); `types/finalizer.py` `662826eb`;
  `utils/querysets.py` `69ac3ea3`.
- Oracles/examples (HEAD): `tests/optimizer/test_hints.py` `d3e413bd`;
  `tests/optimizer/test_walker.py` `ca5c32d7`;
  `tests/optimizer/test_extension.py` `9d57709f`;
  `tests/types/test_base.py` `0d070aee`; `tests/base/test_init.py`
  `4cc12105`; `examples/fakeshop/apps/library/schema.py` `75d358f8`;
  `test_query/test_library_api.py` `91f0238b`;
  `test_query/test_optimizer_auto_api.py` `47e2b003`.
- Searched population: all 117 package `.py` files via HEAD greps
  (mechanism, factory, sentinel, gate, construction, async, and
  serialization censuses above); every other package module is excluded
  on the strength of its census silence for this mechanism.

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

Recorded BEFORE opening `## Findings` (headings + `Status:`/`Run:` lines only).
Trace derived fresh from WT bytes at HEAD `5c3496e0`; WT-vs-HEAD dirt on all
five indexed files attributed by content below (hardening-only, shape-identical).

### W2 site census + roles

DEFINITION (owner candidate): `django_strawberry_framework/optimizer/hints.py`
- `OptimizerHint` frozen dataclass: 5 fields (`force_select`, `force_prefetch`,
  `prefetch_obj`, `skip`, `nested_strategy`), one `SKIP: ClassVar` declaration +
  one `SKIP = OptimizerHint(skip=True)` assignment, four factories (`strategy`,
  `select_related`, `prefetch_related`, `prefetch`), `__post_init__` with five
  rejection arms (bool-type gate, skip-conflict, select+prefetch conflict,
  prefetch_obj type-via-`_require_prefetch` + conflict, nested_strategy
  conflict + `_require_strategy` re-validation), two in-owner `_require_*`
  helpers each shared by its factory and `__post_init__`, one `hint_is_skip`
  value gate (`None` -> False, `is SKIP` -> True, else `getattr(hint,"skip")`).

CONSUMERS (compose by name, no shape restatement):
- `optimizer/walker.py::_resolve_optimizer_hints` (map read, `None` -> `{}`),
  `_apply_hint` (skip via `hint_is_skip`, then `prefetch_obj` /
  `force_select` / `force_prefetch` arms, empty hint -> `False` fallback),
  call site `hints_map.get(django_name)` plus the consumer-assigned
  `is None` gate.
- `optimizer/nested_planner.py::_select_nested_strategy` (single
  `getattr(hint, "nested_strategy", None)` read, re-resolve via
  `resolve_strategy`, else `active_strategy()`), plan-head
  `hint_is_skip(hints_map.get(...))` gate, one `_select_nested_strategy`
  call site.
- `optimizer/extension.py::check_schema` (`hint_is_skip(hints.get(...))` gate).

CONTAINER / ENFORCEMENT (distinct Meta-key contract, not the value shape):
- `types/base.py::_meta_optimizer_hints` (mapping shape + str-key gate),
  `_validate_optimizer_hints` (unknown-key guard, selected-relation guard,
  one `isinstance`-value gate naming no field), call site in
  `__init_subclass__`, `cast` to `dict[str, OptimizerHint]`.
- `types/definition.py::optimizer_hints` slot (typed storage only).

UPSTREAM (composed, not duplicated): `optimizer/nested_fetch.py`
`StrategySelection` + `resolve_strategy` own the strategy-name grammar;
hints.py calls both and adds only the explicit-`None` rejection.

ORACLES: `tests/optimizer/test_hints.py`, `test_walker.py`,
`test_nested_fetch.py`, `test_extension.py`, `tests/types/test_base.py`
et al. construct via public factories / spell expectations; independent.
PROJECTIONS: module + class + factory docstrings.

Package-wide reader sweep (regex over `django_strawberry_framework/`):
`.skip` / `force_select` / `force_prefetch` / `prefetch_obj` / `.SKIP`
readers are hints.py itself plus walker `_apply_hint` only; every skip
read outside the owner goes through `hint_is_skip` (walker, planner,
extension: 3 call sites, 0 hand-rolled `is SKIP or .skip` dispatches);
`nested_strategy` readers are hints.py plus planner
`_select_nested_strategy` only. No second skip-dispatch, no second
conflict matrix, no second factory set anywhere in the package.

### W2 change challenges (definition counts)

- X1 fifth hint kind (e.g. a projection field): 1 — field + conflict arm +
  factory land in `OptimizerHint`; the new walker dispatch arm is a consumer
  move, listed not counted.
- X2 second sentinel (e.g. `DEFAULT`): 1 — ClassVar + assignment in the class.
- X3 factory validating differently (e.g. `prefetch` accepting a lookup
  string): 1 — `_require_prefetch` is the single type gate shared by the
  factory and `__post_init__`; one edit moves both paths.
- X4 serializing hints (e.g. `to_dict`): 1 — one new method on the owner.
- X5 relaxing a conflict rule (e.g. allow skip+force_prefetch): 1 — one
  `__post_init__` arm.
- X6 renaming a field (e.g. `skip` -> `skip_relation`): 1 definition
  (class + same-file `hint_is_skip`) plus N by-name consumer reads.

### W2 owner choice (principle 7)

`optimizer/hints.py::OptimizerHint`. It holds the state contract (record +
validity + construction API); every legitimate consumer (walker, planner,
extension, types/base, types/definition) already imports it with no
dependency reversal and no cycle; the container layer owns the distinct
Meta-key-surface contract and the dispatch arms own plan effects, so
neither is a valid owner for the value shape.

### W2 zero-edit pre-checks

- `git diff ITEM_BASELINE --name-only` = `docs/dry/dry-0_0_15.md` alone.
- 5/5 WT pins match dispatch pins; 5/5 HEAD pins match; no
  `## Implementation`; `git status --short` = 463 lines; HEAD unmoved.
- WT-vs-HEAD hunks touching hint-shape lines: hints.py
  (`isinstance` -> `truth.is_instance`, docstring reword, `hint_is_skip`
  tail restructure with identical semantics), walker.py (one
  `type_cls.__name__` -> `truth.name` in a hint error string), types/base.py
  (name-rendering, casts, key-loop hoist, `isinstance` ->
  `truth.is_instance`); nested_planner.py + definition.py have zero
  hint-shape hunk lines. All concurrent hardening; shape (fields,
  factories, arms, gates, call sites) identical at both states.
- Type gates re-run whole-package (shared venv): mypy clean (119 files),
  basedpyright 0/0/0, check_any 130/90 — match the run-9 baseline.
- Ruff: vacuous (tracked diff touches no `.py`; artifact is scratch `.md`).

### W2 reconciliation (read AFTER sealing the trace above)

F1 count + owner: CONFIRM. W1's census (1 class, 1 SKIP assignment, 4
factories, 2 helpers with 4 in-file calls, 1 value gate) reproduces from
my independent sweep; my X1-X6 stress changes (fifth kind, second
sentinel, divergent factory validation, serialization, relaxed conflict,
field rename) all count 1 with no landable second owner. Owner
`optimizer/hints.py::OptimizerHint` CONFIRM under principle 7 — the
container layer owns the distinct Meta-key contract (C4 separation
control holds: key-policy moves never touch the value shape) and the
dispatch arms own plan effects, so neither can own the value shape.
W1 traced HEAD lines, I traced WT bytes; the WT-vs-HEAD hunks are
hardening-only (recorded above), so both states decide identically.

R1 (narrowed `or {}` read): CONFIRM — walker helper vs extension inline
verified at both call sites; trigger (genuinely-Optional hints) exact.
R2 (double key gate): CONFIRM — both phases verified in types/base.py,
same file/owner, convergence on f14-N3 grounded (N3 names this exact
double gate); direct-call oracle pin `test_base.py:2536` verified present
at HEAD. R3-R6 (queued siblings): CONFIRM — all four name REAL open
plan rows with undispatched `## Families` items (`optimizer-hint-skip-predicate`,
`nested-connection-strategy-selection`, `optimizer-hint-dispatch`,
`attached-prefetch-lookups-read`); each contract difference matches the
bodies I read (predicate read vs shape, resolution vs carriage, plan-time
application vs construction-time shape, lookup derivation vs carriage).
R7 (dual consumer): CONFIRM EXACT — `_select_nested_strategy` reads F1's
field then re-resolves through R4 with `active_strategy()` fallback, per
the body. R8 (pre-validation stage): CONFIRM — `dict[str, object]`
snapshot verified, gated before the cast. R9 (enforcement site): CONFIRM —
the `isinstance` gate names no field and is pinned by the bad-values
oracle (`match=` row verified at HEAD `test_base.py:2575`).

Matrix: axis 2 zero-async reason RE-VERIFIED (`git grep` for `async def`
/ `await` across all three files at HEAD: no matches); axis 4 zero-serialization
RE-VERIFIED; axes 1/3/5/6 searches agree with my own package-wide reader
sweep (no second skip-dispatch, no rebuilt hint, oracles independent).
Enumeration: mechanism counts reproduced (SKIP assignments 1 at HEAD:280;
`_require_*` call sites 4, all in-file; value gates 1; `or {}` reads 2;
`nested_strategy` getattr reads 1); every HEAD line citation spot-checked
(15/15: walker 741/888/904/1843, planner 224/1092/1165/1166/1426,
extension 1549, definition 177, base 706/880/1092/1310/1510) matches.
"No new index rows owed": ENDORSED — family row exists, four siblings
queued, R-exclusions are boundaries, F-HINTREAD/F-HINTVAL/F-TYPOFMT
convergences grounded in the verified File types/base artifact.
Pending-"None": CORRECT → plain `verified` (static-decidable; no `proof:`
owed; focused test correctly unspent — suite-green would prove nothing
about definition count). Cells `inapplicable by construction`: CONFIRM
(construction-time validation + in-memory map reads reach no database,
alias, or dialect; PG-marked live rows pin sibling fetch with hints as
input only). Structural gate ADEQUATE (existing `isinstance` enforcement
+ in-tree oracles; negative control reasoned; first-run holds).
Freshness: 5/5 indexed pins re-hash clean at BOTH states; 5/5
neighbor/oracle spot pins match; WT == ITEM_BASELINE on all five indexed
files (all dirt predates dispatch); searched population stated.
No-ticked-row-wrong check: AGREE (run-5 five-field description matches
HEAD; drift is typing/hardening). Zero defects: AGREE — no (Worker-2)
entries owed.

Verdict: `verified`, plain. Zero-edit CONFIRM stands; nothing to revise.
