# DRY review: `custom-visibility-type-routing`

Status: verified
Run: 0.0.15 2026-10-12-24

Verdict core single-owned; the 5 spellings are 5 input contracts composing it by name.
REJECT unification. Zero-edit. `ITEM_BASELINE=ca0fcb38842c66cc77bfcecd85c8191788b3b22c`
(HEAD `c37a08a0` unmoved; every touch path dirty-concurrent, unattributed hunks moot —
no edit). Never read any `worker-memory/`.

## System trace

Detector `types/base.py::_detect_custom_get_queryset` (:954) walks the MRO to `DjangoType`.
`__init_subclass__` stamps `_is_default_get_queryset` (:676, before the Meta early-return)
and `definition.has_custom_get_queryset` (:864) from ONE local (:675).
`DjangoType.has_custom_get_queryset()` (:915) reads the class-attr definition flag, else the
negated sentinel. Class attr and registry definition are the same object
(`register_with_definition` + :883; `register_definition` rejects a different one).
Five verdict sites: (a) `types/resolvers.py::_custom_visibility_type` (:440: FieldMeta ->
`registry.get` -> `get_definition` -> FLAG, None on miss); (b)
`utils/querysets.py::relation_visibility_type` (:4744: model+root -> `relation_target_type`
-> METHOD); (c) `optimizer/walker.py::_target_has_custom_get_queryset` (:223:
type+definition -> FLAG if definition else METHOD; bool); (d)
`utils/permissions.py::RelationHop.scope` (:574: inline METHOD, type-or-None); (e)
`orders/sets.py:838` (inline METHOD over declared-owner-or-registry type). Whole-package
sweep: these + the finalizer flag-pair (:1450) are EVERY `has_custom_get_queryset` read;
bare `register(` has ONE package caller (inside the atomic pair, `registry.py:501`, with
rollback); `unregister`/`clear` drop type AND definition together. Bare-without-definition
arises only via direct `registry.register` — registry-internal (spec-018:489) — and
`finalize_django_types()` refuses it (`finalizer.py:392-395`, `:415-419`); a schema is
unbuildable unfinalized (relation sentinels, `types/relations.py:56`). Consumers: (c)
injected into nested_planner (`walker.py:1994`, read at `nested_planner.py:1212`); (d)
read by the filters flat-leaf walk (`filters/sets.py:3822`, `:3992`, `:4116`).

## Verification

### Matrix

1. Cross-flavor: all verdict readers compose the core; write flavors, cascade
   (`permissions.py:701`), rechecks (`querysets.py:4684`) apply the hook UNCONDITIONALLY
   (identity is a no-op; registration, not the hook, is their contract — spec-034:256).
2. Sync/async: verdict is pure sync; (a) is computed once at resolver-factory time
   (`resolvers.py:665`) and shared by both color twins. No twin.
3. Derived-twice: flag vs method read the SAME slot (same stamp instant, same object;
   zero post-creation writes package-wide). Inherited-definition corner -> D1.
4. Round-trip: N/A — verdict has no inverse.
5. Media: the method "Readers:" docstring (`base.py:924-932`) lists all 6 flag/method
   sites (projection, moves only with a new site). Contract prose: spec-010:446,
   spec-034:83, spec-028:526, spec-053 B5 (planned `scopes_rows` — tension, see
   Judgment). e3 R1 trigger unfired (bodies apply unconditionally — different unit).
6. Omission: resolver (a), optimizer (c), filters flat (d), declared branches
   (e8-seeded), orders (e) each carry their gate; cascade/recheck/node apply
   unconditionally per contract. None lacks its gate.

### Challenges

- C1 identity-hook detection change -> `_detect_custom_get_queryset` only; both stamps
  read its return; all 5 sites follow. Count 1.
- C2 proxy/concrete resolution change -> `relation_target_type` only; (b) composes it,
  (d)/(e) inputs are pre-resolved by it, (a)/(c) never take root. Count 1.
- C3 root re-entry rule change -> same single owner. Count 1.
- C4 return-shape unification (bool vs type-or-None) -> per-caller contracts (planner
  needs bool; resolvers need the type to RUN the hook); merging is a mode flag.
- Consumers, oracles, projections moving with a change: listed in F1, not counted. No
  experiment owed: every behavior below is read from unambiguous bodies + settled
  interpreter semantics.

## Findings

F1 (verdict+routing) — REJECT consolidation, single-owned. Contract: "which type's
custom `get_queryset` scopes these rows", varying ONLY on what the caller starts from
(edge/model+root/resolved pair/pre-resolved hop/declared-or-registry). Sites: 1 detector
+ 2 stamps/1 instant + 1 slot + 1 method (definitions, all in `types/base.py` +
`types/definition.py`); (a)-(e) consumers composing by name; nested_planner/filters/orders
transitive consumers; 8 existing oracle pins (P1-P3). Challenges: C1-C3 count 1; C4
rejected. Owner + lifetime: detector owns the rule; stamps live with the class/definition
from creation, never invalidated (pure function of the class body; post-creation MRO
mutation stales BOTH stores identically — unsupported per START.md). Migration: none
(zero-edit). Shrinkage: 0 lines; machinery attestation: no helper added — a
`(type, definition)` predicate is pure indirection for (b)/(d)/(e) (no definition in hand
-> falls back to the method it renames) and a bare-shape behavior change for (a).
Distinct behavior: the 5 input contracts + (a)/(c) degrade arms stay; bare divergence
unservable (P1). Behavioral proof: P1 execution-verified (1 passed this session via
`heavy`, `--no-cov -n0`); P2/P3 static-reviewed (cited pins, green at the run-14 gate;
one-test budget spent on P1). P1 `tests/types/test_finalizer.py:133`
`test_incomplete_registry_registration_is_typed_at_finalize` — rejects finalize admitting
a bare registration. P2 `tests/types/test_base.py:1660,1672,1689,1721,2611` — rejects wrong
verdict truth (default/override/inheritance/hostile-meta). P3
`test_query/test_products_visibility_api.py:703` (live: hidden row nulls with AND without
optimizer — (a)/(c) agreement) + `tests/optimizer/test_extension.py:398` (True arm pins
no-elision). Negative control: P1 (unservable shape refused) + P3 hidden->null both legs
(bypass attempt must-hide). Coupling: spec-053 B5 overlap (see Judgment — the maintainer's call
before any B5 build); e8 owns seeds (fence honored, seeds untouched); f57 owns
target-resolution pairing (resolve-half boundary). Freshness (WT blobs, all
dirty-concurrent; HEAD `c37a08a0`): `types/base.py 52e72ed3`, `types/resolvers.py
8cd980b0`, `utils/querysets.py f9267729`, `optimizer/walker.py 5508e486`,
`utils/permissions.py dbb8f602`, `orders/sets.py 79c369b3`, `types/definition.py
cde8437f`, `types/finalizer.py 2dbe6efc`, `registry.py c5aa2050`, `test_finalizer.py
001393cd`, `test_base.py bc858987`, `test_products_visibility_api.py 4cb1f7d8`,
`test_extension.py 9ade4151`. Searched: full package + test trees for the verdict
mechanism; contract sources spec-010/018/034/053.
R1 finalizer either-owner refusal (:1450): different contract (fail-closed bind guard, not
routing). Trigger: a routing call needing an either-custom verdict.
R2 unconditional-apply sites (recheck/cascade): no verdict read; identity is a no-op.
Trigger: a fast path gated on custom there.
R3 relay decode strategy read (`types/relay.py:964`): GlobalID rule, not visibility.
Trigger: decode branching on the hook.
R4 `_has_custom_id_resolver` (`walker.py:1712`): name-similar, different predicate (id
shape). Trigger: id rule keyed on hooks.
R5 `registry.get`+`get_definition` pairing miss contracts (raise/None/degrade per caller):
f57's unit, each miss arm carries its own logic. Trigger: a shared resolve-or-raise shape.
R6 (c) class-fallback arm: LIVE (public `plan_relation` seam omits the definition; pinned
`test_definition_order.py:92-112`, `test_extension.py:4268`) — not P11-deletable. Trigger:
seam requiring the definition.

## Defects

D1 (minor, not security-path; owner `types/base.py`): the definition arm (`:945-951`)
reads the first MRO definition via `static_attr`, so an ABSTRACT subclass of a CONCRETE
parent answers with the PARENT's flag — contradicting `:943-944` ("an abstract base
without one answers from its own stamped ClassVar") and spec-010:446. Shape: abstract
intermediate under a concrete parent adding its own `get_queryset` -> reports False,
truth True. No framework path passes that shape (all 5 sites receive registry/defined-
origin types; bare is finalize-refused); direct-call only, zero row impact. Worker-0
homing owed.

## Pending execution

None.

## Judgment

One detector, one stamp instant, one slot; the 5 differences are input contracts, and
C1-C3 count 1. The bare divergence cannot reach a served query (internal seam + finalize
refusal, P1 green); unifying postures adds a helper, removes zero definitions — below the
bar. CONFLICT FLAG: spec-053 B5 (unbuilt) specifies this unification, and as worded ("by
effect") it changes super-only-override behavior against spec-053's own behavior-preserving
rule. the maintainer decides: strike or re-scope B5. Zero-edit, ready for verification.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (pass 1). Target traced whole-package.

Sites + roles (mine). Sole verdict definition:
`types/base.py::_detect_custom_get_queryset` (only `"get_queryset" in`
namespace probe package-wide; other `truth.mro` callers are unrelated
mechanisms). Stamp instant: `__init_subclass__` :675 local -> :676 class flag
+ :864 definition slot; zero post-creation writes; class attr IS the registry
object (:879 passes `definition`, :883 stores it; `register_definition`
rejects a different one). Router, not a second definition:
`DjangoType.has_custom_get_queryset()` (:915: definition's copy, else negated
flag defaulting identity). Five router-consumers composing by name: (a)
`types/resolvers.py:440` FieldMeta -> registry -> slot, None-on-missing, 1
caller (:665, factory-precomputed); (b) `utils/querysets.py:4744`
model+root -> `relation_target_type` -> method, 1 caller
(`relation_path_visibility_types` -> `FilterSet._branch_via_types`); (c)
`optimizer/walker.py:223` type+definition -> slot-or-method, bool, 5 walker
sites + nested_planner injection; (d) `utils/permissions.py:574`
pre-resolved `target_type` -> method, 3 `filters/sets.py` readers; (e)
`orders/sets.py:838` declared-or-registry type -> method inline in
`_scoped_hops`, 2 internal callers. Sixth consumer: `finalizer.py:1450`
flag-pair fail-closed refusal. Registry: atomic pair only (sole `register(`
caller `registry.py:501` inside `register_with_definition`; sole pair caller
`base.py:879`); unregister/clear drop type+definition together. Bare-without-
definition arises ONLY via direct `registry.register` (internal/test seam,
spec-018:489; package tests pin it).

My C1-C4 (independently posited). C1 verdict-predicate change (e.g. abstract-
intermediate override stops counting) -> detector only. Count 1, owner
`types/base.py`. C2 routing-input change (re-entry/proxy matching) ->
`relation_target_type` only; (b) composes, (d)/(e) inputs pre-resolved,
(a)/(c) rootless. Count 1, owner `utils/querysets.py`. C3 missing-definition
posture change (resolver fails closed like the walker) -> (a) only. Count 1,
owner `types/resolvers.py`: the (a)/(c) bare divergence is a one-site
contract difference, not a shared rule. C4 stamp-lifetime change (detect at
finalize instead of creation) -> `types/base.py` only (slot contract + all
readers unchanged). Count 1. Slot-removal variant implausible (deletes the
owner's published storage; consumers following an intentional contract change
do not count). Owner I would choose: `types/base.py` already owns
verdict+stamp+slot+method; routers stay at boundaries. No moves.

Second-copy/P11 hunt (mine): no second detector; no shareable tail beyond
`has_custom_get_queryset()` (already the shared seam); (a)/(b) one-caller
wrappers each carry boundary routing (registry+None-posture / root-threading)
— keep; bool-vs-type-or-None merger is a mode flag. B5 `scopes_rows`
specified-but-unbuilt; judged after P1 below.

Reconciliation (after reading Findings; every difference explicit). AGREE:
single verdict owner, 5 routers as consumers, C1-C3 count 1 (my C1/C2 match
in substance; my C3/C4 are posture/lifetime variants, same count-1
conclusion), owner `types/base.py`, zero-edit, D1 real, B5 flag real (below),
R1-R6 rejections, matrix discharge, 13/13 fingerprints match (re-hashed).
DIFF 1 (P1 scope precision, verdict-neutral): P1 covers multi-type +
pending-source bare (finalize refuses — test body read). Bare-SOLE-no-pending
PASSES finalize (every phase loop walks `iter_definitions()`; both audits
skip single-type models) but still cannot serve: relation-field paths die at
schema construction (installed Strawberry `from_type` -> `TypeError
"Unexpected type"`, the sentinel-doctrine refusal class); non-field paths
consult only agreeing readers. Double-defeat (manual decoration + direct
register) is outside supported API — covered by the trigger. W1's "bare is
finalize-refused" overstates the locus for bare-sole only. DIFF 2 (record
nit): R6's `test_definition_order.py:92-112` cite is pending-sentinel tests,
unrelated to the fallback arm — STRUCK. R6 stands on the seam contract
(`walker.py:193-209`), the definition-less delegate (`extension.py:1609`),
and the `test_extension.py:4268` pin (body read: omits definition, asserts
prefetch/custom). DIFF 3 (terminology, no action): W1's "(definitions...)"
vs my 1-definition + machinery + router — same single owner. DIFF 4: W1's
`permissions.py:701` is ROOT permissions (cascade unconditional-apply, zero
verdict gates — verified), not utils. D1 ADJUDICATION: defect (minor,
non-security-path) — wrong answer on public API contradicting code comment
`:943-944` AND spec-010:446 (both verified textually); no served path passes
it (all 5 sites receive registry/defined-origin types). Fix is code
(own-namespace definition read) -> home 053 per precedent (code -> 053,
doc-only -> 056), NOT 056. B5 ADJUDICATION: conflict REAL, route to the maintainer.
Textual: B5's "by effect" predicate vs the class-body-presence detector
diverge observably on super-only overrides (select<->Prefetch, cacheable
flip — principle-8 observable); B5 as specified breaks WP-B's own
provably-coinciding rule ((a)/(c) bare postures don't coincide). PROOFS:
P1 execution owed + done (green); P2/P3 static SUFFICES (regression anchors
for a zero-edit REJECT — all 8 pins read, names+bodies match claims);
negative controls confirmed (P1 raises; P3 nulls both legs, bodies read). My
one-test budget unspent: execution adds nothing decisive (both outcomes keep
this verdict). No `(Worker-2)` defects: bare-sole finalize admission needs
the internal register seam (rule-37 bar fails) and refuses loudly downstream.
AGENTS.md prose on empty diff: clean (no edits; `path:NN` allowed in `dry-*`
scratchpads; script excludes the file). VERDICT: verified.

## What shrinks

Net package lines over `ITEM_BASELINE=ca0fcb38`: 0 (zero-edit — nothing to port; no
ledger row owed).
Population census (whole package, verdict mechanism): 1 detector (`types/base.py:954`),
2 stamps from 1 local (`:675-676`, `:864`), 1 slot (`types/definition.py:181`), 1 method
(`types/base.py:915`), 5 verdict sites (`types/resolvers.py:440`,
`utils/querysets.py:4744`, `optimizer/walker.py:223`, `utils/permissions.py:574`,
`orders/sets.py:838`), 1 flag-pair refusal (`types/finalizer.py:1450`), 3
unconditional-apply exclusions (`utils/querysets.py:4684`, `permissions.py:701`,
`types/relay.py:958`+strategy read), 1 name-similar exclusion
(`optimizer/walker.py:1712`), 2 resolve-pairing neighbors in f57's unit
(`types/definition.py:330-332`, `optimizer/walker.py:471-472`, `:512-515`).
Registry-mutation census: bare `register(` has 1 package caller (inside the atomic pair);
`unregister`/`clear` remove type AND definition together — the registry cannot hold a bare
registration through its own public mutators.
Refused machinery: a `(type, definition)` verdict predicate would add one helper, delete
zero definitions (detector/slot/method all stay — the method is public API and (b)/(d)/(e)
hold no definition), re-spell 5 composed reads as 5 composed reads, and flip (a)'s bare
answer from None to the class verdict. Not taken.
