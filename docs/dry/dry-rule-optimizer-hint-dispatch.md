# DRY review: `optimizer-hint-dispatch`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Target: the optimizer-hint dispatch - how `walker.py::_apply_hint`
serves the four configurable hint shapes (`SKIP`, `prefetch_obj`,
`force_select`, `force_prefetch`) plus the empty-hint fallthrough,
at HEAD `23b5f421` + WT.

The dispatch is one private function with one call site. WT
`django_strawberry_framework/optimizer/walker.py:966` (inside
`_walk_selections`) calls `_apply_hint` (`:1313`) when the hints map
carries the relation; a `True` return skips the default cardinality
dispatch, `False` (empty hint only) falls through to it. The four
arms, in order: `hint_is_skip` (`:1347`, composed by name from
`optimizer/hints.py`, verified family `optimizer-hint-skip-predicate`),
`prefetch_obj` (`:1349`, validate-before-mutate through
`_scoped_hint_prefetch` `:1389` -> `_prefetch_hint_for_path` `:1388`,
then record + `append_prefetch_unique`), `force_select` (`:1433`,
many-side refused at plan time, else `_dispatch_single_relation` with
the custom-`get_queryset` downgrade preserved), `force_prefetch`
(`:1456`, `_dispatch_single_relation` with `prefer_prefetch=True`).
The five plan-time refusals (SKIP short-circuit aside) are each
single-sited: `to_attr`-without-consumer-assigned (`:1359`),
missing lookup (`_prefetch_hint_for_path` `:1558`), mismatched
lookup (`:1569`), `force_select` on many-side (`:1436`), and
combined-unrepresentable (`_hint_prefetch_over_pk_set` `:1532`).

The `prefetch_obj` pipeline's three helpers are each single-called
in one chain: `_scoped_hint_prefetch` (`:1475`, custom-`get_queryset`
targets resealed through `_build_child_queryset`, others through
`_hint_prefetch_over_pk_set` `:1497`), `_hint_prefetch_over_pk_set`
(`:1509`, combined hinted querysets rewritten to their pk set via
`utils/querysets.py::_pk_membership_query_or_defect` `:1530`, alias /
hints / nested prefetches carried, unservable shapes refused),
`_prefetch_hint_for_path` (`:1548`, type-relative lookup rebased onto
the accessor path). The shared predicates are composed by name:
`_target_has_custom_get_queryset` (one def `:243`, both hint arms
call it), `_dispatch_single_relation` (one def `:1008`, three
deciders: cardinality `:992`, `force_select` `:1441`,
`force_prefetch` `:1457`), `_resolve_optimizer_hints` (one def
`:544`, walker `:799` plus nested-planner injection `:1949`).

Whole-package sweep for the rule's mechanism (every value-read of
the five shape fields, plus every `OptimizerHint` mention): no
second dispatch site exists. Outside `hints.py` construction
(factories + `__post_init__` conflict matrix, verified family
`optimizer-hint-shape`) and `_apply_hint`, the only value-reads are
`nested_planner.py:1177` (`hint_is_skip`, composed),
`nested_planner.py::_select_nested_strategy` (`:209`, the sole
`nested_strategy` reader, one call site `:1473`), and
`extension.py:1510` (`hint_is_skip`, composed, schema audit). The
windowed path diverts before the dispatch (`walker.py:840-854`):
synthesized connections never reach `_apply_hint` and read exactly
SKIP + strategy, which `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`
Decision 6 fixes as the window's hint surface ("`prefetch_related()` /
`prefetch(...)` hints apply to the list-shaped planning only - the
window reads no prefetch hint"; "SKIP means the optimizer leaves this
relation alone; that contract extends to the relation's connection
sibling"). `types/base.py::_validate_optimizer_hints` validates
Meta values (different rule: declaration validation, not dispatch);
`types/definition.py:180` declares the field; examples carry
declarations + live oracles only.

f61 relationship re-derived at current bytes (the nomination's
`:1432` predates f61's landing): the composed read now lives at
walker.py:1544 (`.prefetch_related(*queryset_prefetch_lookups(inner))`
inside `_hint_prefetch_over_pk_set`). It composes the f61 spelling
owner `utils/_queryset_private.py::queryset_prefetch_lookups`
directly (strict read over a genuine `QuerySet`), while
`optimizer/plans.py::_consumer_prefetch_lookups` (`:604`) is f61's
lenient adapter for hostile consumer input. Strict-vs-lenient
layered, not separated (f61's verified verdict holds); no second
spelling definition exists at either site.

Dirt attribution by diff content vs `git show HEAD:<path>`: walker
WT carries f56's ledgered `target_definition=` consolidation
(buildable) plus truth-migration hunks (`truth.name` /
`truth.static_attr` / `truth.is_subclass`, concurrent) - the three
`_apply_hint` hunks and the `_hint_prefetch_over_pk_set` hunk are
truth-only; nested_planner WT carries f56's pass-through (buildable)
plus truth import + one `truth.name` (concurrent); querysets WT dirt
touches neither `_pk_membership_query_or_defect` nor
`_combined_lost_property`. Extension `extension.py:1505`
(`definition.optimizer_hints or {}`) is HEAD-clean; the adjacent
audit hunk (`:1518`) is truth-only. No consolidation is proposed, so
no hunt-dirtied line is touched and nothing is blocked-on-hunt.

## Verification

### Matrix

1. Cross-flavor: the shape-field census above is package-wide
(`prefetch_obj`, `force_select`, `force_prefetch`,
`nested_strategy`, `hint_is_skip` value-reads; every
`OptimizerHint` mention). Mutations, forms, `rest_framework`,
filters, orders carry no reader - hints dispatch in the optimizer
only. `types/base.py` validates declarations, never dispatches.
Discharged.
2. Sync/async: zero `async def` in walker.py and nested_planner.py
(re-grepped). Planning is sync-only; async lives at fetch time
(`nested_fetch`, lateral), which never reads a hint shape (its one
strategy read is `active_nested_strategy()`, the carried decision,
not the hint). No twin can exist. Discharged.
3. Derived knowledge: same-token sites each inspected on body
strength - `to_attr` triple (`:1350` refusal check, `:1506` /
`:1545` / `:1576` carry-throughs), `prefetch_through` reads
(direct `:1506` `:1545` vs lenient-with-good-error `:1556`),
extension `or {}` (`extension.py:1505`), the seal's combined arm
(`querysets.py:3937-3944`), `_validate_optimizer_hints`. Each
carries a distinct contract in `## Findings` R1-R5; none is a
second definition. Discharged.
4. Round-trip: construction matrix (`hints.py::__post_init__`,
verified family `optimizer-hint-shape`) vs dispatch order is the
standing f15 separation, trigger-checked at current bytes: every
pair the order could arbitrate is still rejected except
(`force_prefetch`, `nested_strategy`), which live on different
paths (direct vs windowed) so no arbitration is needed. Both
docstrings still state it (`hints.py:163-168`,
`walker.py:1338-1340`). Discharged.
5. Other media: oracles spell literals, never read the owner -
`tests/optimizer/test_walker.py` B4/O4/O6 pins per shape,
`tests/optimizer/test_hints.py` construction matrix,
`tests/optimizer/test_nested_fetch.py` strategy selection,
`tests/optimizer/test_plans.py::TestConsumerPrefetchLookups`
(f61), live rows (`test_optimizer_auto_api.py` strategy
overrides, `test_combined_visibility_api.py` combined serving,
`test_library_api.py:874` hook narrowing). Projections:
glossary `OptimizerHint` / `Meta.optimizer_hints` sections,
spec-033 Decision 6, spec-004 hint slice, README "Nested
connection indexing". No medium carries a second definition;
one stale spec sentence is D1. Discharged.
6. Omission: hint fields x planning paths enumerated. Direct path
honors four shapes + fallthrough, ignores `nested_strategy`
per the `strategy()` contract ("Applies only to Relay
connection fields; a non-connection field silently ignores the
override", `hints.py:222-224`). Windowed path honors SKIP +
strategy only per spec-033 Decision 6 (R6 records why the
`force_select` silence is specified, not a gap). Audit honors
SKIP only; its predicate is target registration, which no
other shape affects. No member lacks a guard a contract
source owes it. Discharged.

### Enumeration

Instrument: `grep -rn` over `django_strawberry_framework/` for the
five shape-field tokens plus `OptimizerHint`, `_apply_hint`,
`_scoped_hint_prefetch`, `_hint_prefetch_over_pk_set`,
`_prefetch_hint_for_path`, `_select_nested_strategy`,
`_pk_membership_query_or_defect`, `_resolve_optimizer_hints`,
every hit read on body strength; `async def` census (0);
`_prefetch_related_lookups` spelling census (single live reader).
Count: 1 dispatch site, 3 single-called pipeline helpers, 1
strategy reader, 3 composed SKIP readers, 2 rewrite composers, 0
second definitions. Examined-and-excluded, each on body strength:

| Site | Verdict |
|---|---|
| `_select_nested_strategy` + planner SKIP arm | F2: intentional split, composes shared predicates |
| Seal combined arm (`querysets.py:3937-3944`) | F3/R4: distinct input contract, shared primitive |
| Extension `or {}` (`extension.py:1505`) | R1: distinct contract, no change obligation |
| Prefetch rebuild triple + `to_attr` reads | R2: per-rebuild threading, helper would be machinery |
| `__post_init__` conflict matrix | R3: standing f15 separation holds |
| Walker `:1544` vs plans `:604` lookups reads | R5: f61 strict/lenient layering holds |
| `force_select` silence on windowed path | R6: specified surface, trigger recorded |
| `_validate_optimizer_hints`, field declaration | excluded: validation/declaration, not dispatch |
| Example hint declarations + live rows | consumers/oracles, not definitions |

### Challenges

Rule F1 (four shapes + fallthrough), F2 (windowed split), F3
(combined rewrite). Counts are authoritative definitions only;
consumers, oracles, projections listed under `## Findings`.

- C1 (new shape): add a fifth hint shape -> `_apply_hint` gains
one arm (count 1); `__post_init__` gains conflict rules under its
own contract (verified family `optimizer-hint-shape`, not this
rule). The dispatch order stays documentation because
construction still rejects every arbitrable pair.
- C2 (SKIP semantics): change what SKIP means -> `hint_is_skip`
(count 1); walker, planner, audit compose by name (3 consumers,
not counted).
- C3 (prefetch_obj pipeline): change scope/rebase/record ->
the one arm + its 3 single-called helpers (count 1; one chain,
one call site).
- C4 (force routing): change select/prefetch routing ->
`_dispatch_single_relation` (count 1); three deciders compose it
(cardinality, `force_select` + downgrade, `force_prefetch`).
- C5 (combined rewrite): change the pk-set rewrite ->
`_pk_membership_query_or_defect` (count 1); seal arm + hint arm
compose by name (2 consumers with distinct input contracts,
F3/R4).
- C6 (strategy selection): change per-field override ->
`_select_nested_strategy` over `resolve_strategy` (count 1
each; verified family `nested-connection-strategy-selection`
owns the ladder).
- C7 (hints-map resolution): the walker's None-definition-safe
planning input vs the audit's narrowed declared-map read are
two contracts (R1); no shared normalization exists or is owed,
so no single change moves two definitions of one rule.

Proofs (all in the item copy `dry/hintdisp-f62/consolidate`,
slot-2, each `shared unmoved since sync`): `test_walker.py`
199 passed (`dry-20261009T210431-6c54c3`); `test_hints.py` +
`test_nested_fetch.py` + `test_plans.py` 184 passed
(`dry-20261009T210447-a09584`); live
`test_optimizer_auto_api.py` + `test_combined_visibility_api.py`
203 passed, 2 skipped (both `@pytest.mark.pg` strategy rows,
`dry-20261009T210500-c2b4ad`); `basedpyright` 0/0/0
(`dry-20261009T210902-11f0e7`); floor 0/0/0
(`dry-20261009T211017-2886bf`); truthful-reads errors 0
(`dry-20261009T211130-111799`). `check_public_types.py` not
owed (no public symbol touched). The shared-tree `--no-cov`
allowance stays unused (zero-edit).

## Findings

### F1 - hint-shape dispatch (CONFIRMED single-owned, zero-edit)

- Contract + variation: the four configurable hint shapes +
empty-hint fallthrough - SKIP (unplanned, `True`),
`prefetch_obj` (validate-before-mutate, `to_attr` refused
unless consumer-assigned, rebased onto the accessor,
non-cacheable + B8 key attribution), `force_select`
(many-side refused, custom-`get_queryset` downgrade
preserved), `force_prefetch`, empty hint (`False`,
cardinality dispatch). Varies on: shape set, per-shape
planning, refusal set.
- Sites + roles: `_apply_hint` (definition),
`_scoped_hint_prefetch` / `_hint_prefetch_over_pk_set` /
`_prefetch_hint_for_path` (definitions, one chain, one call
site each), `_walk_selections` `:966` (sole consumer),
`hint_is_skip` / `_dispatch_single_relation` /
`_target_has_custom_get_queryset` /
`_pk_membership_query_or_defect` / `append_prefetch_unique` /
`queryset_prefetch_lookups` (composed owners), test pins +
live rows (oracles), glossary + specs + README (projections).
- Challenges: C1-C4, C7, each count 1 (`### Challenges`).
- Owner + lifetime: `optimizer/walker.py::_apply_hint` (owns
it today; the single call site and the relation-branch
context admit no narrower importer). No stored derivation:
pure plan-time functions; the plan cache stores plans under
the extension's own contract (different rule).
- Migration: none - every site already composes by name.
- Distinct behavior: construction-time conflicts stay in
`hints.py` (R3); windowed SKIP/strategy stay in the planner
(F2); seal-vs-hint combined handling stays split (F3/R4).
- Behavioral proof: execution-verified - the five refusals,
the fallthrough, the downgrade, the rebase, the
validate-before-mutate order, and the non-cacheable mark are
each pinned by a named oracle re-run green above; each
rejects its wrong result (unrefused misconfiguration,
phantom plan keys, cached cross-request queryset).
- Structural gate: none owed. Private single-module owner,
one in-module call site; any new direct-path planning
routes through `_walk_selections` and any new windowed
planning through `plan_connection_relation`, so no plausible
bypass population exists. A census pinning today's one-site
mechanism counts would be a bespoke existence test per
helper, which the method forbids (f57 bar, Worker-2
endorsed). Durable protection is the per-shape behavioral
pins plus this artifact's censuses as re-derivation baseline.
- Coupling: none. D1 blocks nothing (spec prose).
- Freshness: HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=695a27e67fc0034e4dcd58b8ed4d412d399578c6`
(taken on `23b5f421`; the baseline tree carries the WT dirt,
so every BASE pin below equals its WT pin and the item diff
is empty). Pins are WT / HEAD / BASE, 8 chars
(`git hash-object`; BASE via `git rev-parse <baseline>:<path>`):
walker.py `57ab6770` / `bc6bc969` / `57ab6770` (dispatch pins
reproduced exactly); querysets.py `e6660894` / `4d8a3d39` /
`e6660894`; nested_planner.py `a9875bbb` / `73d03184` /
`a9875bbb`; hints.py `26b2b5a4` / `df40ce08` / `26b2b5a4`;
nested_fetch.py `b4c30994` / `c2ccc321` / `b4c30994`;
plans.py `39713c65` / `6f2d0c70` / `39713c65`; extension.py
`49346716` / `e18210e5` / `49346716`; _queryset_private.py
`a26a8d43` / `ff8b2b46` / `a26a8d43`; types/base.py `f42bcee3`
/ `a63b7edf` / `f42bcee3`. Contract sources (all HEAD-clean):
spec-033 `ad2e5897`, spec-004 `0d514a41`, glossary `98bb5580`.
Oracles: test_walker.py `cf679cf2` / `5c450c3e` / `cf679cf2`;
test_hints.py `8b95450a` / `009187f5` / `8b95450a`;
test_nested_fetch.py `c96e95af` / `53eb92b6` / `c96e95af`;
test_plans.py `832d0b55` / `fe606e15` / `832d0b55`;
test_optimizer_auto_api.py `73e6b1d2` x3;
test_combined_visibility_api.py `7ae261df` x3; docs/README.md
`6cbc579b` / `c602a8a6` / `6cbc579b` (label corrected by
Worker-2: the pins match `docs/README.md` in all three states,
not the clean root `README.md` `acbcd871` x3). Searched population:
every `.py` under `django_strawberry_framework/` (shape-field
+ `OptimizerHint` + helper-name censuses, all hits read);
examples (declarations only); any fingerprint change reopens.

### F2 - windowed SKIP/strategy arms (CONFIRMED intentional split, zero-edit)

- Contract: the window reads exactly SKIP + strategy
(spec-033 Decision 6); `prefetch_obj` / `force_select` /
`force_prefetch` apply to list-shaped planning only.
- Sites: planner `:1177` SKIP arm (consumer of `hint_is_skip`),
`_select_nested_strategy` (sole `nested_strategy` reader,
one call site `:1473`), walker divert `:840-854` (routes
connections past `_apply_hint`).
- Challenges: C2 (SKIP, count 1 at `hint_is_skip`), C6
(strategy, count 1). A change to the window's hint surface
moves the planner arms only; a change to the list dispatch
moves `_apply_hint` only.
- Owner: `optimizer/nested_planner.py` (window semantics live
nowhere else). No stored derivation. No migration.
- Behavioral proof: execution-verified - SKIP-suppresses-window
+ SKIP-before-sidecar pins and the per-field strategy live
rows re-run green above.
- Structural gate: none owed (same bar as F1; the divert is
the single routing point).
- Coupling / Freshness: as F1 (same pins, same copy).

### F3 - combined-hint pk-set rewrite (CONFIRMED composed, zero-edit)

- Contract: a combined hinted queryset is served as the pk set
it selects; a shape the set cannot represent fails at plan
time naming `OptimizerHint.prefetch(obj)` on `Type.field`
(glossary contract, quoted verbatim in the refusal).
- Sites: `_pk_membership_query_or_defect` (definition, single
owner of the rewrite + lost-property proof),
`_hint_prefetch_over_pk_set` (composer: trusted schema
config, keeps alias / hints / nested prefetches),
`_seal_or_defect` combined arm (composer: untrusted sealed
state, policy-pinned alias, `_clone`-parity rebuild).
- Challenges: C5, count 1. The two composers share the
primitive by name and differ on every other axis (R4).
- Owner: `utils/querysets.py::_pk_membership_query_or_defect`.
No stored derivation. No migration.
- Behavioral proof: execution-verified - combined-rewrite and
combined-refusal pins plus the live combined-serving rows
re-run green above.
- Structural gate: none owed (same bar; the primitive has two
named composers and no other reader).
- Coupling / Freshness: as F1.

### R1 - extension `or {}` (rejected; distinct contract)

`extension.py:1505` (`definition.optimizer_hints or {}` under an
already-narrowed definition) restates the None-map half of
`_resolve_optimizer_hints` (`walker.py:544-548`, whose
load-bearing half is the None-definition arm for unregistered
models). Same token, two contracts: planning-input resolution
vs declared-map audit read. Type creation already guarantees
values (`_validate_optimizer_hints`), so no shared normalization
exists or is owed; consolidating would import the walker's
private helper into the audit to exercise a dead None arm.
Relieves no change obligation. Trigger: a normalization step
both sites must share. (Line `:1505` is HEAD-clean; the
adjacent `:1518` hunk is concurrent truth dirt.)

### R2 - Prefetch rebuild triple (rejected; per-rebuild threading)

`walker.py:1506` / `:1545` / `:1573` each rebuild a `Prefetch`
preserving `to_attr`, but each preserves a different subset per
its own contract (re-scoped queryset, rewritten queryset,
rebased lookup). A shared rebuild helper needs optional
lookup/queryset params - mode-flag machinery (principle 5) for
three one-liners. The strictness split follows input contracts:
direct reads over validated `_PrefetchAny` vs lenient reads in
`_prefetch_hint_for_path`, whose defensive arm is pinned by a
hostile-surrogate oracle. Trigger: a fourth rebuild or a
`to_attr` rule with content beyond carry-through.

### R3 - construction matrix vs dispatch order (rejected; standing separation holds)

Verified family `optimizer-hint-shape` owns the conflict matrix;
the dispatch order stays documentation. Trigger-checked at
current bytes (`### Matrix` axis 4): still exactly one
co-allowed pair, on different paths. Trigger: a co-allowed pair
on one path.

### R4 - seal vs hint combined arms (rejected; distinct input contracts)

`querysets.py:3937-3944` substitutes the rewrite into a
proven-genuine rebuild of untrusted consumer state;
`walker.py:1527-1545` wraps trusted schema configuration
(stated at `querysets.py:3543-3545`: "trusted schema
configuration that no seal has walked"). Different alias
policy, hints policy, and reconstruction contract; the shared
primitive is already one definition composed twice. Merging
would couple the trust boundary to schema config. Trigger: the
hint path starts accepting unsealed request-time input.

### R5 - strict vs lenient lookups reads (rejected; f61 layering holds)

Walker `:1544` composes `queryset_prefetch_lookups` directly
(genuine `QuerySet` input); plans `:604` adapts it leniently
for hostile `Prefetch.queryset` values. f61's verified verdict
(layered, not separated) re-derived at current bytes; the
nomination's `:1432` is now `:1544` after f61's landing.
Trigger: a third trust domain needing its own adapter.

### R6 - `force_select` silence on windowed path (rejected as gap; specified surface)

The window ignores `force_select` while the direct path refuses
it on many-side. Specified, not a gap: Decision 6 fixes the
window's hint surface at exactly SKIP + strategy, and the
refusal's purpose (prevent building a wrong `select_related`)
has no windowed counterpart (the window is always
prefetch-shaped). The list sibling sharing the hint still
raises loud, so no consumer intent drops silently. Trigger: a
windowed select-shaped plan, or a contract source demanding
loud refusal on the windowed path.

## Defects

- D1 (spec drift; owner `docs/SPECS/spec-004-optimizer_beyond-0_0_3.md`,
for Worker-0 closeout homing on a named card):
`spec-004-optimizer_beyond-0_0_3.md:107` ("Test surface") states
"`.select_related()` forces select_related on a many-side
relation." HEAD code refuses it (`walker.py:1426-1430` at HEAD),
the HEAD oracle pins the raise
(`tests/optimizer/test_walker.py:1996` at HEAD), and spec-033
Decision 6 states "`select_related()` is invalid for a
many-side relation". The spec sentence contradicts all three;
the spec file is HEAD-clean (`0d514a41` x3), so the drift is
committed, not concurrent. Unfixed (out of item scope).

## Pending execution

Empty. Every behavioral proof above executed green in the item
copy; no `proof:` entry is owed. No `gate:` entry (suite
confirmation rides the plan's final gate, f57 precedent).
Cells: sharded/pg inapplicable by construction - the dispatch
is plan-time pure logic over hint records and `sql.Query`
objects; it opens no connection and makes no alias or dialect
decision (`queryset_db` preserves the hinted queryset's alias
by attribute read). The 2 live skips are `@pytest.mark.pg`
strategy-seam rows (fetch-time lateral SQL), not dispatch
coverage. Worker-2 judges.

## Judgment

CONFIRM. The optimizer-hint dispatch is one rule in one owner:
`_apply_hint` serves the four shapes + fallthrough from a
single call site, its pipeline helpers are single-called,
every shared predicate and primitive is composed by name, the
windowed split and the strict/lenient layering are specified
contracts, and the whole-package sweep finds no second
dispatch site. Zero-edit: single-ownership rule, record the
finding, touch nothing. One spec-drift defect (D1) routes to
closeout homing.

## Implementation (Worker-1)

Zero-edit: no tracked file changed, no test added, no `## Owned
changes` row owed.

- Item diff vs `ITEM_BASELINE=695a27e67fc0034e4dcd58b8ed4d412d399578c6`
is empty on every item path: walker WT pin `57ab6770` equals
its BASE pin, HEAD pin `bc6bc969`, dispatch pins reproduced
exactly (querysets `e6660894` / `4d8a3d39`, nested_planner
`a9875bbb` / `73d03184`); status count 519 unmoved apart from
this artifact itself (new untracked file, the plan's expected
+1). HEAD `23b5f421` unmoved.
- Touched `.py` paths = {} (stated explicitly): no
`ruff check --fix` / `ruff format` run owed; `check_any.py`
never run (deleted); `check_public_types.py` not owed (no
public symbol touched).
- The shared-tree `--no-cov` allowance stays unused; all six
proof runs executed in the item copy at
`dry/hintdisp-f62/consolidate` (slot-2), each reporting
`shared unmoved since sync`.
- No ledger row, no new index row (F2/F3 live under the
family's existing index row, which already names the pk-set
rewrite and the windowed split), no pending execution.

## Independent verification (Worker-2)

Recorded before opening `## Findings` (artifact read: title +
`Status:` line + tail only). Pins confirmed first: HEAD
`23b5f421`; WT blobs `57ab6770` / `e6660894` / `a9875bbb`;
HEAD blobs `bc6bc969` / `4d8a3d39` / `73d03184`; item-scoped
diff `git diff 695a27e67fc0034e4dcd58b8ed4d412d399578c6 --
<3 target paths>` empty; whole-baseline diff carries only
Worker-0's plan-dispatch text in `docs/dry/dry-0_0_15.md`;
untracked files all concurrent work (truth migration,
review `rev-*`, hunt, honest prefix/postfix) - zero-edit
claim holds at the tree level.

### Own trace

Rule: how the walker serves the four configurable
`OptimizerHint` shapes (`SKIP`, `prefetch_obj`,
`force_select`, `force_prefetch`) plus the empty-hint
fallthrough.

Sites found by a package-wide mechanism sweep over
`.prefetch_obj | .force_select | .force_prefetch |
hint_is_skip | nested_strategy | optimizer_hints`:

- `optimizer/walker.py::_apply_hint` - DEFINITION of the
  dispatch: `SKIP -> True`; `prefetch_obj` (to_attr guard,
  validate-then-mutate, rebase, record, non-cacheable) `-> True`;
  `force_select` (many-side refusal, custom-qs downgrade via
  `_dispatch_single_relation`) `-> True`; `force_prefetch ->
  True`; empty hint `-> False` (caller falls back to the
  `plan_relation` cardinality dispatch). One call site
  (`_walk_selections`, WT `:966`).
- `optimizer/walker.py::_scoped_hint_prefetch`,
  `::_hint_prefetch_over_pk_set`, `::_prefetch_hint_for_path` -
  DEFINITIONs, private decomposition of the `prefetch_obj`
  arm (visibility scoping incl. seed seal; combined-queryset
  pk-set rewrite composing
  `utils/querysets.py::_pk_membership_query_or_defect` by name
  with plan-time `ConfigurationError` on defect; type-relative
  lookup rebase with plan-time refusal on missing / wrong-target
  lookup). Each serves exactly one arm step; no second
  spelling of any step found in the sweep.
- `optimizer/hints.py::hint_is_skip` - DEFINITION owned
  elsewhere (SKIP-spelling rule): three consumers, all by name
  (`_apply_hint`, `nested_planner.py::plan_connection_relation`
  `:1177`, `extension.py` schema audit `:1510`).
- `optimizer/hints.py::OptimizerHint.__post_init__` -
  DEFINITION owned elsewhere (construction-time shape-rejection
  rule, a different rule from plan-time serving).
- `optimizer/nested_planner.py::plan_connection_relation`
  `:1177` - CONSUMER of `hint_is_skip` (SKIP arm for windowed
  connections; synthesized-connection selections route here
  from `_walk_selections` BEFORE `_apply_hint` is reachable,
  WT `:840`-`:854`, so the connection path honors SKIP +
  strategy only).
- `optimizer/nested_planner.py::_select_nested_strategy` -
  DEFINITION of the strategy arm, composing
  `nested_fetch.py::resolve_strategy` / `::active_strategy` by
  name; sole `.nested_strategy` reader in the package.
- `utils/querysets.py::_pk_membership_query_or_defect` +
  `::_COMBINED_WHAT` - DEFINITIONs owned elsewhere (pk-set
  rewrite rule + shared refusal text), composed by name.
- `optimizer/walker.py::_resolve_optimizer_hints` - CONSUMER /
  helper (hints-map source, shared with the nested planner via
  callable injection at WT `:1949`).
- `optimizer/plans.py::_consumer_prefetch_lookups` over
  `utils/_queryset_private.py::queryset_prefetch_lookups` -
  f61 layering (lenient adapter over the spelling owner);
  `_hint_prefetch_over_pk_set` composes the spelling owner by
  name (`:1544`), no restatement.
- `optimizer/walker.py::_dispatch_single_relation` - DEFINITION
  owned elsewhere (shared prefetch/select argument threading
  for the cardinality verdict + both force arms).
- `optimizer/walker.py::plan_relation` - DEFINITION owned
  elsewhere (cardinality verdict rule, the fallthrough target).

### Own change challenges

- C1 (fifth hint shape): `_apply_hint` gains one arm
  (`__post_init__` validation moves only if the shape needs
  construction-time rejection - that is the shape-validation
  rule, not this one). Dispatch count 1.
- C2 (fallthrough semantics, e.g. empty hint raises):
  `_apply_hint`'s terminal `return False` only. Count 1.
- C3 (combined-hint serving change):
  `utils/querysets.py::_pk_membership_query_or_defect` (owner,
  shared with the seal paths); `_hint_prefetch_over_pk_set`
  unchanged. Count 1, elsewhere-owned.
- C4 (SKIP semantics for windowed connections):
  `nested_planner.py:1177` arm only. Count 1.
- C5 (strategy default resolution): `nested_fetch.py`
  (`active_strategy` / `resolve_strategy`);
  `_select_nested_strategy` unchanged. Count 1,
  elsewhere-owned.
- C6 (Prefetch-object lookup read): WT `:1418`-`:1426`
  (lenient `prefetch_to`-or-`prefetch_through` read for B8 key
  attribution on the already-rebased object) vs `:1556`
  (strict `prefetch_through` read that refuses a missing
  lookup): different contracts (attribute-after-success vs
  validate-before-mutate), different subjects from
  `queryset_prefetch_lookups` (a `Prefetch` object's own lookup
  vs a queryset's attached list). Each count 1.

### Owner I would choose

`walker.py::_apply_hint` for the four-shapes-plus-fallthrough
dispatch (it already owns it); the three prefetch-arm helpers
stay as its private decomposition; SKIP-spelling stays with
`hints.py::hint_is_skip`; strategy selection stays composed
from `nested_fetch.py`; the pk-set rewrite stays composed from
`utils/querysets.py`. No consolidation owed: zero-edit
CONFIRM, pending `## Findings` reconciliation.

(Reconciliation with `## Findings` follows below after the
Worker-2 read.)

### Reconciliation

Read `## System trace` through `## Judgment` after recording
the trace above. Verdict on every difference (mine vs
Worker-1's):

- Owner: AGREE (`_apply_hint`). Helper decomposition: AGREE
  (three single-called defs, one chain). SKIP consumers: AGREE
  (exactly the same three sites). Strategy sole reader: AGREE.
  Windowed divert before `_apply_hint`: AGREE (same lines).
  pk-set rewrite composed: AGREE. f61 layering holds: AGREE
  (`:1544` composes the spelling owner directly).
- Challenge granularity: Worker-1's C1-C7 are a SUPERSET of my
  C1-C6 (extra: C2 SKIP-semantics at `hint_is_skip`, C4 routing
  at `_dispatch_single_relation`, C7 hints-map R1). Every count
  is 1 on both sides; no conflict, theirs is finer. My C6
  (Prefetch-object lookup reads) maps onto their R2 + R5 +
  Matrix axis 3.
- Residual Worker-2 extension (not a difference in verdict):
  the B8-attribution read at WT `:1418`-`:1426` is not named in
  R2, so I grounded it myself against the installed Django:
  `Prefetch.prefetch_to` is the RESULT-storing path while
  `prefetch_through` is the traversal path
  (`django/db/models/query.py` `:2572`-`:2575`), so the
  `prefetch_to`-first read attributes keys to where rows land,
  the `:1556` `prefetch_through` read matches what to traverse,
  and the `:1506` / `:1545` reads carry the traversal path
  into a rebuild. Three purposes, each single-sited, no twin:
  no second definition either way. R2's rejection stands as
  written.
- Enumeration: reproduced member by member - `async def`
  census 0/0; helper call sites exactly `:1388` / `:1389` /
  `:1497` / `:1473`; production `hint_is_skip` sites exactly
  three (`extension.py:1510`, `nested_planner.py:1177`,
  `walker.py:1347`); `_pk_membership_query_or_defect` readers
  exactly two (seal `:3938`, hint `:1530`);
  `_prefetch_related_lookups` attribute spelling read live
  only by `_queryset_private.py:87` (the seal's `:3902` read
  is a state-dict key, a different subject). "1 dispatch, 3
  helpers, 1 strategy reader, 3 SKIP readers, 2 rewrite
  composers, 0 second definitions" CONFIRMED.
- Freshness: all 19 pins reproduced in all three states,
  including BASE-via-`rev-parse` and the three HEAD-clean
  contract sources. One label fix (this pass):
  Worker-1's "README" pins match `docs/README.md`, not the
  root `README.md`; corrected in place above. No fingerprint
  drift; nothing reopened.
- R1-R6: each carries its contract difference + trigger;
  bodies re-read (R1 both arms incl. the audit's non-None
  narrowing; R2 all three rebuilds; R3 co-allowed pair
  re-derived: exactly (`force_prefetch`, `nested_strategy`)
  on different paths; R4 seal arm `:3937`-`:3944` vs hint arm
  `:1527`-`:1545` incl. the trusted-config statement at
  `querysets.py:3542`-`:3545`; R5 strict-vs-lenient trust
  domains; R6 Decision 6 surface quote verified verbatim).
- D1 drift: VERIFIED as filed, all four legs at HEAD bytes -
  spec-004 "Test surface" sentence present;
  `git show HEAD:walker.py` refuses (`if hint.force_select:`
  at `:1426`, `raise ConfigurationError` below);
  `git show HEAD:test_walker.py:1996`
  `test_plan_force_select_hint_raises_for_many_side_relation`
  pins the raise with a literal `match=` (oracle, not
  owner-reading); spec-033 Decision 6 states
  "`select_related()` is invalid for a many-side relation";
  spec-004 is `0d514a41` x3 (committed drift, out of item
  scope, correctly routed to closeout homing). No defect from
  Worker-2; `## Defects` gains no entry.
- Structural gates: "none owed" ACCEPTED - private
  single-module owner, one in-module call site, single routing
  points on both paths; a census pin would be a bespoke
  existence test the method forbids. Coupling: none; D1
  blocks nothing. Pending execution: empty, CONFIRMED owed
  nothing (all proofs executed; no `proof:`/`gate:` entry).
- Sharded/pg inapplicable-by-construction: JUDGED SOUND.
  `_pk_membership_query_or_defect` inspects and rebuilds
  `sql.Query` objects only (no connection, no SQL compilation,
  no alias decision); `queryset_db` preserves the hinted
  alias by attribute read (`QuerySet.db` routes without
  connecting). The 2 live skips are `@pytest.mark.pg`
  fetch-time lateral rows, not dispatch coverage; pg-cell
  verification stays out of scope without the maintainer's word and no
  dispatch line can behave differently under it.
- Item-scoped diff: empty (all three target paths byte-equal
  to `ITEM_BASELINE`); whole-baseline diff carries only
  Worker-0's plan text; touched `.py` paths = {} stated
  explicitly, so no `ruff check --fix` / `ruff format` run is
  owed and none ran; `check_any.py` never run; public-types
  not owed. AGENTS.md prose rules hold vacuously. No oracle
  rewritten (nothing rewritten at all).

### Worker-2 gate re-runs (own copy, `dry/hintdisp-f62/verify-1`, slot-3, each `shared unmoved since sync`)

- Focused pins `test_plan_force_select_hint_raises_for_many_side_relation`
  + `test_plan_no_flag_hint_falls_through_to_default_dispatch`:
  2 passed (`dry-20261009T211922-d3cbb7`).
- `basedpyright`: 0 errors, 0 warnings, 0 notes
  (`dry-20261009T211930-298325`).
- `basedpyright -p pyrightconfig.floor.json`: 0/0/0
  (`dry-20261009T212041-7313a9`).
- `check_truthful_reads.py --check`: errors 0, 120 files
  (`dry-20261009T212153-8837d1`).

### Worker-2 verdict

`verified` (plain, not pending execution). One rule in one
owner, zero-edit CONFIRM endorsed: F1 single-owned dispatch,
F2 intentional windowed split, F3 composed rewrite, R1-R6
rejections sound with triggers, D1 verified for closeout
homing, no Worker-2 defect. The shared-tree `--no-cov`
allowance stays unused.

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
