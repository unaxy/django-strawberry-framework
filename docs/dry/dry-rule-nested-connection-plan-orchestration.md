# DRY review: `nested-connection-plan-orchestration`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is nested-connection plan orchestration: how one
recognized nested Relay connection selection becomes a windowed
`Prefetch` plan, or stays unplanned with strictness-visible
bookkeeping. Re-derived fresh at WT bytes (`5c3496e0` + concurrent
dirt), not inherited: the population is the mechanism (the planning
entry, the per-key window pass, the fallback log, the identity
filter, the node unwrap, the raw-field resolve, the result record,
the walker delegation, the strategy dispatch, every composed read),
swept package-wide by exact-match spelling, not just the thirteen
indexed files.

What the trace found is an already-consolidated rule in one home
with a pure delegation seam:

- The orchestration in `optimizer/nested_planner.py` (WT `b6ff0a0e`):
  `plan_connection_relation` (the entry: eight ordered refusal
  arms, one scheme selector, one child build through the shared
  seam, one deterministic order, scalar/keyset projection
  branches, one shared fetch-mode value, one fully-resolved
  request per window to the field-static strategy, merge-only-on
  acceptance into an isolated plan, the field-static advisory
  latch, metadata absorb plus identity recording on the success
  path only), `NestedConnectionPlanResult` (the isolated plan +
  accepted keys + `accepted`), `_divergent_key_windows` (the
  per-payload arguments-derived pass shared by both window
  schemes), `_log_connection_fallback` (the plan-time debug
  trace), `_identities_for_response_keys` (the per-key filter
  over the walker's parallel tuples), `_connection_node_selections`
  (the adapter over the selections-owned unwrap), and
  `_raw_relation_field` (the `_meta` resolve for the partition
  derivation). Seven definitions, one module, each counted once.
- The delegation in `optimizer/walker.py` (WT `4fd8077f`):
  `_plan_connection_relation` passes the normalized selection
  plus eight injected callables into the planner and atomically
  merges the returned plan (`plan.merge_from(result.plan)`).
  Pure delegate: no branch, no second planning body. Its sole
  production caller is the walker's one connection branch
  (`walker.py:782`, behind the `relation_connections`
  metadata recognition). The walker's historical re-export
  aliases (`walker.py:104-112`) are pure name bindings for
  test pins, never second bodies.

Owner re-derived (not inherited): `plan_connection_relation` is
the narrowest module the walker already delegates to with no
dependency reversal; it holds the sole `NestedConnectionRequest(`
construction site (`nested_planner.py:1462`), the sole production
`strategy.plan(` dispatch (`nested_planner.py:1479`), the sole
per-payload window pass, and the sole success-path absorb. No
other module plans a nested connection: the root connection path
slices a real queryset (a different contract, X-root), the
extension configures strategy/cache/strictness but plans nothing,
and the resolve side reads windows back (the round trip's read
half, X-readback).

Sites and roles, WT bytes:

- Definitions (all in `optimizer/nested_planner.py`, WT
  `b6ff0a0e`): `plan_connection_relation` (`:1090`),
  `NestedConnectionPlanResult` + `accepted` (`:156`),
  `_divergent_key_windows` (`:967`), `_log_connection_fallback`
  (`:1041`), `_identities_for_response_keys` (`:1057`),
  `_connection_node_selections` (`:801`), `_raw_relation_field`
  (`:1079`).
- Delegation consumer: `optimizer/walker.py::_plan_connection_relation`
  (`:1819`, eight injected callables + one `merge_from`), called
  once from the connection branch (`:782`).
- Composed owners (each read by name; call-site censuses in
  `### Enumeration`): scheme predicates + identity derivation +
  child builders (walker-injected, incl. the
  `_build_connection_child_queryset` seam and the open
  `prefetch-child-build-seam` family), SKIP (hints, f16),
  strategy registry + request/seam/classifier (nested_fetch,
  f17/f18/verified classifier), join + windowability
  (join_taxonomy, f21), hint value + per-field strategy name
  (hints, f15), deterministic order (plans ladder, open
  `connection-order-ladder`), unwrap + observers + vocabulary +
  response keys (selections), merges + appenders + deferred
  unpack + entry vocabulary (plans), lookup (utils/relations,
  verified accessor), target model + cursor state (definition /
  keyset), windows (F2 adapters, f19), bounds + range + fetch
  mode + sidecar + cap + signal (utils/connections, f19/f20),
  cursor codec + seek (keyset), strategy default + plan cache +
  strictness (extension), `to_attr` grammar + advisory + scalar
  and cursor projections (same-file siblings; four open
  families).
- Oracles (all spell expectations independently; none reads an
  owner table): `tests/optimizer/test_walker.py` orchestration
  rows (per-key window sets, divergent/malformed/conflict pins,
  strategy accept/refuse/raise rows, no-leakage rows),
  `tests/optimizer/test_nested_fetch.py` result-record rows,
  `tests/test_relay_connection.py` alias-routing + strictness
  rows, `tests/optimizer/test_plans.py` window rows, plus live
  `/graphql/` suites (auto strategy, single-parent fast path,
  keyset, library shapes).
- Projections: the target module docstring (transactional
  contract), the planner/walker/connection/`_check_n1`
  consumer docstrings, the GLOSSARY connection-aware-planning
  + strictness anchors, the README strategy-override
  paragraph, TREE module lines, spec-033 Decisions 4/5/6/8/11
  + spec-035 Decisions 4/5.

Dirt attribution (by diff content vs `git show HEAD:`, all
thirteen indexed files): every WT-hunk is concurrent work,
untouched. WT == ITEM_BASELINE on all twelve dirty indexed
files (only `utils/connections.py` is clean), so the dirt
predates this item. By content: the `truth` import migration
(planner, walker, fetch, hints, plans, selections, relations,
resolvers, connection, keyset, extension), the lenient-reader
removal + composite-FK virtual-link arms (join_taxonomy,
relations), the M2M advisory silence arm (planner F3 lines,
the concurrent D1 session), and oracle extensions (relay,
nested_fetch, join_taxonomy suites). Exactly one WT hunk
touches an F1 line: the strategy-refusal log's
`type(strategy).__name__` -> `truth.name(type(strategy))`
one-liner (`nested_planner.py:1491`), a truth-migration
spelling with identical rendered output on genuine
strategies. No hunk touches the delegation (`walker.py:782`,
`:1819-1854`), the request build (`:1462`), the absorb
(`:1503`), the identity writes (`:1243-1255`, `:1508-1517`),
or any composed-owner contract the orchestration depends
on. The `## Owned changes` ledger holds no row on these
paths except the committed D1 seal (`fd39cac6`, in HEAD),
so there is nothing to build on and nothing to reconcile.

Count correction vs the file item (evidence only, the file
artifact is not edited): the file item's F1 says "twelve
injected callables"; the fresh WT census counts eight
(`resolve_optimizer_hints`, `resolve_relation_target`,
`response_key_arguments_conflict`, `aliased_arguments_diverge`,
`target_has_custom_get_queryset`, `resolver_identities_for`,
`build_child_queryset`,
`build_prefetch_child_queryset_from_base`), agreeing with
the walker re-trace ("still eight `Callable` params"). The
verdict never depended on the number.

Principle-11 note (`accepted` / `accepted_response_keys`):
zero production readers package-wide (the walker merges
unconditionally; an empty-plan merge is a no-op). KEPT: it
is the transactional result's public acceptance signal from
the "isolate nested planning" design (`991d5120`), pinned
by oracles (`test_nested_plan_result_reports_strategy_acceptance`),
costing one field plus one property. Removing it would
delete the boundary's vocabulary to save nothing. Recorded
here so the question is not re-raised.

## Verification

### Matrix

Each axis discharged against the family's real surface (the
planning entry, both window schemes, both cursor
vocabularies, the delegation, the resolve read-back):

1. Cross-flavor policy mirroring -- DISCHARGED by comparison.
   No sibling flavor (mutations, forms, rest_framework,
   filters, orders) owns a nested-planning surface. The two
   adjacent pipelines are different contracts, not mirrors:
   the root connection path (`connection.py::_finalize_queryset`,
   `_resolve_keyset_connection`) slices a real queryset the
   resolver already holds, while the nested planner builds a
   windowed `Prefetch` for children not yet fetched; the
   mutation-payload extractor (`extension.py:704-707`)
   composes the same unwrap owner rather than re-walking.
   Searched: `Prefetch(` constructions in the optimizer are
   the walker list path, the hint path, and the windowed
   strategy floor -- no second nested-connection builder.
2. Sync/async twins -- DISCHARGED, no twin. Zero `async def`,
   zero `await` in the planner (the two `async` tokens are
   docstring rationale about `SynchronousOnlyOperation`
   avoidance); orchestration is plan-time sync derivation,
   and strategies execute inside Django's sync prefetch
   machinery. The async-facing rules touched (cursor-column
   loading, morph alias-lateness) are single-sited with
   stated async rationale, not twins.
3. Derived rather than repeated knowledge -- DISCHARGED by
   census. Every derivation composes its owner by name (the
   call-site table in `### Enumeration`); reconstructed-fact
   candidates investigated: the identity filter vs the
   derivation (X17, filter-over-parallel vs cartesian
   construction), the `_check_n1` probe (threaded `to_attr`
   parameter, never rebuilt), the fetch-mode read-back
   (physical shape under seam-enforced exclusivity,
   X-readback). No fact has two derivations.
4. Inverse / round-trip pairs -- DISCHARGED. Four pairs, each
   single-owned with a composed half: request build
   (planner, sole site) vs window read
   (`connection.py::_resolve_from_window`, incl. the
   fetch-mode read-back and the defensive tail);
   `to_attr` build (canonical) vs resolve probe (delegates,
   per-key first then shared; never parsed back -- zero
   unescape sites, correctly one-way); keyset seek encode
   (mint, keyset-owned) vs decode (composed codec);
   advisory key (single site). `resolve_strategy` has no
   inverse (f17). No pair has two owners.
5. Contracts restated in another medium -- DISCHARGED. Every
   medium a change moves is classified in System trace:
   oracles (4 package suites + 4 live suites, all
   independent spellings incl. literal window/identity
   pins) and projections (target + consumer docstrings,
   2 GLOSSARY anchors, README + TREE lines, spec
   Decisions). No restated definition.
6. Enforcement by omission -- DISCHARGED. Families
   enumerated, each member checked: all eight refusal arms
   fire on their shapes (unknown field, same-key conflict,
   SKIP, missing related model, empty window set,
   unwindowable join, unwindowable base, strategy refused
   every window), each with an oracle pin; the keyset path
   shares `_divergent_key_windows` so no gate is
   offset-only; the scalar branch carries cursor columns
   for keyset targets through the shared effective order
   (no scalar/keyset gap); every accepted window passes
   the first-accepted advisory latch; both `to_attr`
   schemes probe resolve-side per-key-first. No member
   lacks its guard; no gap found.

### Enumeration

Instrument: exact-spelling construction/dispatch/reader
censuses over the whole package (`grep -rn` for each
mechanism token below; WT bytes). Population: the seven
definitions, the delegation, and every composed read the
orchestration performs. Each lands in F1 (single-owned),
a converge (verified family), or an exclusion with its
contract difference + trigger (open family or carried
rejection).

Definition census (each exactly one `def` / `class`,
package-wide):

| Member | Def site | Production callers |
|---|---|---|
| `plan_connection_relation` | nested_planner.py:1090 | walker.py:1834 (delegation only) |
| `NestedConnectionPlanResult` + `accepted` | nested_planner.py:156 | constructed at :1152/:1170/:1177/:1194/:1257/:1268/:1302/:1495 (8 refusal arms) + :1518 (success); `accepted` read by oracles only |
| `_divergent_key_windows` | nested_planner.py:967 | nested_planner.py:1214 (sole) |
| `_log_connection_fallback` | nested_planner.py:1041 | 4 in-file arms (:1155/:1225/:1231/:1488) |
| `_identities_for_response_keys` | nested_planner.py:1057 | 2 in-file writes (:1245/:1511) |
| `_connection_node_selections` | nested_planner.py:801 | nested_planner.py:1284 (sole) |
| `_raw_relation_field` | nested_planner.py:1079 | nested_planner.py:1265 (sole) |
| `_plan_connection_relation` (delegate) | walker.py:1819 | walker.py:782 (connection branch only) |
| `NestedConnectionRequest(` build | nested_planner.py:1462 | sole package construction site |
| `strategy.plan(` dispatch | nested_planner.py:1479 | sole production dispatch (the other two `plan(` calls are strategy-internal delegation, f18) |
| `_advise_composite_index(` call | nested_planner.py:1485 | sole production caller (first-accepted latch) |
| `active_strategy()` call | nested_planner.py:240 | sole production caller (f17 read) |

Composed-read census (each one `def`, readers compose by
name; home in Findings):

| Owner read | Readers (production) |
|---|---|
| `merge_from` | walker.py:1854 (delegation absorb), nested_planner.py:1480 (strategy loop) |
| `merge_metadata_from` | walker.py:1487 (absorb seam), nested_planner.py:1503 (success path), plans.py:362 (inside `merge_from` itself) |
| `_absorb_child_plan` | walker.py:1239 (sole; the planner cannot compose it without reversing the walker-imports-planner edge, X18) |
| `classify_relation_join` | walker.py:1604, nested_planner.py:184 (shim) / :735 (scalar) / :1266 (F1 join), plans.py:996 |
| `hint_is_skip` | walker.py:1277, nested_planner.py:1176, extension.py:1543 |
| `declared_cursor_state_for_definition` | nested_planner.py:1202, connection.py:1505 |
| `unwindowable_child_queryset_reason` | lateral_fetch.py:640, nested_planner.py:1301, single_parent_fetch.py:244 |
| `effective_connection_order` | nested_planner.py:1361, connection.py:1816 (the cursor-parity pair) |
| `connection_field_names` | nested_planner.py:1283, extension.py:704, connection.py:1248 |
| `connection_node_children` | nested_planner.py:819 (adapter), extension.py:707 (root extractor) |
| `connection_total_count_selected` / `connection_has_next_page_selected` | nested_planner.py:1411-1412, selections.py:821-824 (inside `connection_count_required`) |
| `response_keys` | walker.py:697 (derivation), nested_planner.py:1157/:1227/:1233/:1490 (logging); walker binds it as `_response_keys` (:90), the planner imports it directly |
| `window_range_plan` | nested_planner.py:1440, lateral_fetch.py:391, plans.py:1135, single_parent_fetch.py:146, utils/connections.py:565 (inside `assert_window_fetch_mode_for`), connection.py:477 |
| `relation_connection_to_attr` | nested_planner.py:1475 (build) + 2 in-file delegates; resolve probes connection.py:2320/:2330 (per-key first, shared fallback) |
| `instance_accessor` | nested_planner.py:1476 (lookup) + 5 sibling readers |
| `has_connection_sidecar_kwargs` / `has_connection_sidecar_input` | nested_planner.py:1015 (per-payload gate); kwargs delegates to input in one module; connection.py:1849/:2340 gate resolve |
| `_dst_` window-grammar construction | 2 f-strings inside the canonical (nested_planner.py:786/:788); the finalizer marker, plans annotation constants, and `_dst_cursor_value_` are separate namespaces (X13) |

### Challenges

Each rule in the family: changes posited on its variation
axes, authoritative definitions counted (consumers,
oracles, projections listed, never counted). All decided
statically -- single-site censuses plus body reads decide
single ownership; no ordering, transactional, or async
behavior moves under this verdict, so no execution probe
is owed (every claim below is `static-reviewed`):

- Orchestration: posit a ninth refusal arm -- 1 definition
  (`plan_connection_relation` gains the arm; the delegation
  passes through; oracles gain one pin each, listed).
  Posit a third window scheme -- 1 orchestration
  definition (the scheme selector + payload map + loop;
  the new scheme's `to_attr` spelling lives in the
  open grammar family X13, counted there).
  Posit a new strategy-dispatch input (e.g. per-key
  strategy) -- 1 request-build site (sole
  `NestedConnectionRequest(` census) + the f17 read.
  No second planning body exists (the walker delegates;
  the root path never plans nested; the extension plans
  nothing).
- Per-key window pass: posit a new per-payload gate -- 1
  definition (`_divergent_key_windows`); both schemes and
  both cursor vocabularies inherit it. Posit a new
  fallback reason -- 1 log shape
  (`_log_connection_fallback` + reason strings; other
  media stay separate, X19).
- Identity recording: posit a new identity vocabulary --
  1 definition (walker's `_resolver_identities_for`);
  the planner filter follows by construction (X17).
- Merge discipline: posit a third absorb site -- the
  plans-owned `merge_metadata_from` stays the one body;
  the planner's direct call vs the walker seam is an
  import-direction constraint (X18).
- Result record: posit a new acceptance signal -- 1
  definition (`NestedConnectionPlanResult`); the walker
  merge stays unconditional (empty merge is a no-op).

## Findings

### F1 -- Nested-connection plan orchestration (CONFIRMED single-owned, zero-edit)

Contract: the transactional planning of one recognized
nested connection -- eight ordered refusal arms (unknown
field, same-key conflict, hint SKIP, missing related
model, empty window set, unwindowable join, unwindowable
base queryset, strategy refused every window), each
leaving the selection unplanned with strictness-visible
bookkeeping (malformed keys record identities so the
field's own error preempts the strictness flag);
edges/node unwrap through the once-resolved connection
vocabulary; one child-queryset build through the shared
seam under the prefetch-child seal; the deterministic
order through the plans-owned ladder; scalar-only vs
keyset projection branches; split count observers feeding
one shared fetch-mode value; one fully-resolved request
per window to the field-static strategy with
merge-only-on-acceptance into an isolated plan; the
field-static advisory latch on the first accepted window;
metadata absorb plus identity recording on the success
path only. Varies over refusal arms, window schemes,
projection branches, and absorb/identity bookkeeping.

Sites + roles: seven definitions in
`optimizer/nested_planner.py` (WT `b6ff0a0e`; pins in
`### Enumeration`); sole production caller is the walker
delegation (pure: eight injected callables + one
`merge_from`, WT `4fd8077f`); consumers compose the
neighboring owners by name (census table); oracles are
the walker
orchestration rows, the result-record rows, the
alias-routing + strictness rows, the plans window rows,
and four live suites; projections are the target +
consumer docstrings, two GLOSSARY anchors, README + TREE
lines, and the spec-033/035 Decisions.

Challenges: all rows count 1 definition (see
`### Challenges`); no second planning body, window pass,
fallback log, identity filter, unwrap adapter, raw-field
resolve, request-build site, or strategy dispatch exists
(package-wide censuses, WT bytes).

Owner + lifetime: `plan_connection_relation` -- the
narrowest module the walker already delegates to with no
reversal; every legitimate consumer (walker, strategies
via the seam, resolve-side readers) already depends on
it. No stored derivation: the isolated plan is built and
returned within the call (pure derivation, "not cached"
per principle 4).

Migration: none -- single ownership already holds by
construction. Zero-edit verdict: no production edit, no
test edit, no `## Owned changes` row.

Distinct behavior: the resolve-side read-back (fetch
mode off the window's physical shape) is the round
trip's read half, already single-owned under the
seam-enforced PROBED/COUNTED exclusivity; the `accepted`
signal stays as the boundary's vocabulary (principle-11
note in System trace).

Behavioral proof: `static-reviewed` throughout -- the
verdict is structural (single-site censuses + body
reads), and nothing moves, so there is no migration
whose observable equivalence needs executing. The
wrong result each census rejects is a second
independently-maintained definition; the census
population (whole package, exact spelling) discharges
it. No `execution-deferred` proof is owed.

Structural gate: none proposed, deliberately. A
per-helper name-census test (`NestedConnectionRequest(`
count == 1) is the bespoke existence test DRY.md
forbids; the plausible bypasses each break an existing
behavioral oracle instead: a second planning body that
skips identity recording trips the strictness
`raise` rows; one that respells `to_attr` breaks the
resolve probe and the alias-routing rows; one that
bypasses the seam breaks the fetch-mode exclusivity
assertion. The rule currently holds (every census
above is count 1 at WT bytes). Consistent with the
verified f12-f25 zero-edit precedent.

Coupling: none -- nothing lands.

Freshness: thirteen indexed files (WT / HEAD / baseline
`25bf01a14`, 8-char): nested_planner
`b6ff0a0e`/`8c3a45f5`/`b6ff0a0e`, walker
`4fd8077f`/`13e1be20`/`4fd8077f`, nested_fetch
`c36826bb`/`bedaa76e`/`c36826bb`, join_taxonomy
`aa289013`/`8026dc8d`/`aa289013`, hints
`ee68ae03`/`f6776564`/`ee68ae03`, plans
`2e962ae2`/`97a524e2`/`2e962ae2`, selections
`1f6d3e04`/`f49ea7fa`/`1f6d3e04`, extension
`8e3fe7c1`/`b7b6c434`/`8e3fe7c1`, connection
`48de0243`/`99969652`/`48de0243`, utils/connections
`5bf8f5fa` (clean all three), keyset
`7d43c6b1`/`6af980b8`/`7d43c6b1`, utils/relations
`23df6180`/`3b35dfcd`/`23df6180`, types/resolvers
`a8c6a46e`/`09d40f34`/`a8c6a46e`. Oracles (same
triple): test_walker `ca5c32d7` (clean),
test_plans `df714065` (clean), test_nested_fetch
`0b65aa96`/`7fbd957b`/`0b65aa96`,
test_relay_connection `e6b4b556`/`29a2be59`/`e6b4b556`,
test_keyset_connection `70db0483` (clean),
test_join_taxonomy `df9be570`/`481294c3`/`df9be570`,
test_optimizer_auto_api `47e2b003` (clean),
test_single_parent_fastpath_api `492fac73` (clean),
test_library_shapes_api `fbd38b2a` (clean),
test_keyset_api `315c0372` (clean). Modules excluded
on the strength of their bodies (same triple):
lateral_fetch `a48cb0a4` (clean), single_parent_fetch
`3a4bb89b` (clean), field_meta
`99f7b1d3`/`7c9afe35`/`99f7b1d3`, types/finalizer
`0807fea7`/`662826eb`/`0807fea7`, types/definition
`ef9e871a`/`fd339a7c`/`ef9e871a`, utils/querysets
`3e392d48`/`69ac3ea3`/`3e392d48`, utils/imports
`3ea52b16` (clean). Contract sources: GLOSSARY
`95cd34f3` (clean), README `cdb927d5`/`a3deca98`,
TREE `63ba442a`/`aa922f44`. Searched population: the
whole package (`django_strawberry_framework/`, 100+
`.py`) plus the oracle suites above. HEAD `5c3496e0`
unmoved throughout; WT pins match dispatch pins on
all thirteen indexed files.

### Exclusions (each with its contract difference + reconsideration trigger)

Verified-family converges (consumer link re-derived
fresh at WT bytes above; internal verdict adopted as
recorded, never re-litigated):

- X1 slice adapters + shared kernel (f19 consolidated):
  the planner calls both adapters through
  `_divergent_key_windows` and never re-derives the
  reverse/limit rule. Difference: pagination-to-window
  derivation vs window orchestration. Trigger: the
  planner deriving bounds without the adapters.
- X2 strategy selection (f17 consolidated): the planner
  reads via `_select_nested_strategy` + `active_strategy`
  (sole caller). Difference: name-to-backend resolution
  vs per-relation planning. Trigger: the planner
  branching on strategy identity beyond the read.
- X3 strategy seam (f18 consolidated): the planner is
  the sole request builder and sole production
  dispatcher; strategies own fetch. Difference:
  fetch execution vs fetch orchestration. Trigger: a
  second request-build or dispatch site.
- X4 range/fetch-mode (f20 consolidated): one
  `window_range_plan` + one `fetch_mode` per window.
  Difference: window arithmetic vs orchestration.
  Trigger: the planner computing ranges inline.
- X5 partition classifier (f21 consolidated): one
  `classify_relation_join` call per plan; the
  `_connector_only_field` shim stays that family's
  consumer question. Difference: join taxonomy vs
  orchestration. Trigger: the planner classifying
  joins without the classifier.
- X6 attach columns (f23 consolidated): scalar branch
  composes `prefetch_attach_columns`. Difference:
  attach-complete sets vs orchestration. Trigger: the
  planner projecting attach columns by hand.
- X7 unwindowable classifier (verified): the base gate
  at `:1301`. Difference: queryset-shape
  classification vs orchestration. Trigger: the
  planner testing queryset shapes inline.
- X8 hint shape (f15) + X9 SKIP predicate (f16):
  `hints_map.get` + `hint_is_skip` at `:1175-1176`.
  Difference: hint vocabulary/skip decision vs
  orchestration. Trigger: the planner reading hint
  internals directly.
- X10 instance accessor (verified): the `lookup=` read
  at `:1476`. Difference: accessor resolution vs
  orchestration. Trigger: the planner resolving
  accessors without the owner.
- X11 child-build seal (s17 `sealed-execution-queryset`
  + open `prefetch-child-build-seam`): the planner
  reaches both builders through injected callables and
  classifies the result. Difference: visibility-sealed
  construction vs orchestration. Trigger: the planner
  constructing child querysets without the seam.
- X21 relation-kind readings (verified taxonomy): via
  the classifier, never direct. Difference: kind
  vocabulary vs orchestration. Trigger: direct kind
  reads in the planner.

Open-family exclusions (adjudicated there, never here):

- X12 composite-index advisory (open): the planner
  latches one call on the first accepted window
  (`:1485`). Difference: dev-mode index recommendation
  vs window planning. Trigger: the orchestration
  branching on advisory output.
- X13 `to_attr` grammar (open): the planner builds via
  the canonical (`:1475`); resolve probes via the
  delegates; `_check_n1` threads the probed attr.
  Difference: landing-attr naming vs orchestration.
  Trigger: a second spelling of the grammar.
- X14 scalar-only projection (open): the scalar branch
  (`:1373-1379`). Difference: minimal column sets vs
  orchestration. Trigger: the orchestration
  projecting columns without the projector.
- X15 keyset cursor projection (open): the keyset
  branch (`:1386-1389`) + two `connection.py` call
  sites. Difference: mask rewriting vs orchestration.
  Trigger: a second cursor-column union.
- X16 order ladder (open `connection-order-ladder`;
  s10 scoping respected): the planner reads
  `effective_connection_order` once (`:1361`); the
  querysets tier (`default_order` / `applied_order`)
  is held for s16/s11. Difference: total-order
  derivation vs orchestration. Trigger: the planner
  ordering without the ladder.

Composed-read exclusions (single-owned in the home
module; consumer link re-derived fresh; no family row
owed beyond those above):

- X-selections (vocabulary, unwrap, observers,
  response keys): the planner resolves names once
  (`:1283`), unwraps through the adapter (`:1284`),
  and observes once (`:1411-1412`). Difference:
  per-selection AST walks vs orchestration. Trigger:
  the planner walking selections without the owners.
- X-plans-record (merges, appenders, deferred unpack,
  entry vocabulary): merge-only-on-acceptance + the
  success-path absorb. Difference: record mechanics
  vs orchestration. Trigger: the planner merging
  outside the plans-owned bodies.
- X-keyset (codec, declared state, seek carrier):
  context at `:1202`, decode inside the f19 adapter.
  Difference: cursor vocabulary vs orchestration.
  Trigger: the planner minting/decoding cursors.
- X-extension (strategy config, plan cache,
  strictness): configuration + lifecycle, no planning
  body. Difference: operation lifecycle vs
  per-relation planning. Trigger: a planning body in
  the extension.
- X-root (root connection pipeline): slices a held
  queryset; never builds a nested prefetch.
  Difference: slicing vs window building. Trigger:
  the root path planning nested windows.
- X-readback (resolve-side window read): fetch mode
  off the physical shape under seam exclusivity.
  Difference: read half vs build half. Trigger: the
  resolver re-deriving the mode per response key.

Carried rejections (file-item rows re-verified fresh
at WT bytes; durable home stays the owner as recorded
there):

- X17 identity filter vs derivation (R11): filter over
  parallel tuples vs cartesian construction; the
  `[-1]` read is safe by construction (every path
  ends in its response key, `walker.py:694-698`).
  Trigger: a caller needing filtered identities
  without the walker's derivation.
- X18 planner merge vs walker seam (R12): the seam
  adds nothing over the plans-owned body, and the
  planner cannot compose it without reversing the
  walker-imports-planner edge. Trigger: the absorb
  discipline gaining a step outside
  `merge_metadata_from`.
- X19 fallback wordings (R15): plan-time debug trace
  vs shim refusal error vs resolve-time strictness
  reasons -- three audiences, three media. Trigger:
  an oracle asserting cross-media byte parity.
- X20 sidecar arities (R17): kwargs delegates to
  input in one module; already one body. Trigger:
  the two arities diverging in behavior.
- X22 `last: 0` (R14 SUPERSEDED): both guards removed
  by `dbf0a870`; the rule lives once in
  `page_arguments` (f19, DISCHARGED s15). No trigger
  owed; noted so no cycle re-litigates.

## Defects

None. Near-misses re-verified fresh at WT bytes and NOT
filed: (a) `runtime_path[-1]` -- safe by construction
(cartesian proof, `walker.py:694-698`, X17); (b) the
direct `_optimizer_response_key_arguments` read -- guarded
by the diverge premise (read only `if divergent`,
`:1214-1223`; `_aliased_arguments_diverge` answers False
without the map); (c) the file-item D1 (M2M advisory) --
F3, not this family: WT carries the concurrent session's
silence arm on those lines (attributed above), still
concurrent-owned, Worker-0 closeout decides; (d) the
file-item D2 (keyset annotation) -- F2, not this family:
the annotation is record-typed at HEAD + WT
(`tuple[ConnectionWindowBounds, KeysetSeek | None]`,
fixed by drift; f19 closed F2 with zero defects), no
action here.

## Pending execution

None. Census verdict: nothing moves, no gate proposed, so
no `proof:` / `gate:` entry is owed. Cells: `unverified`
(default, sharded, pg) -- the orchestration's outputs are
DB-executing windowed-prefetch querysets, so
inapplicable-by-construction is not claimed (the run-9
f18 typing ruling, as applied by f19/f20).

## Judgment

CONFIRM single-owned, zero-edit. The nested-connection
plan orchestration lives once in
`optimizer/nested_planner.py::plan_connection_relation`
plus its six helpers, reached through one pure walker
delegation, composing the neighboring owners by name and
read back by one resolve side. All six challenges count
1; all six matrix axes discharge; all twenty-eight
exclusion rows carry their contract difference + trigger.
No consolidation to land, no gate to add, no defect to
home. The item touched nothing tracked.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (artifact lines
315-590 unread at write time; `## System trace` /
`## Verification` likewise unread -- the trace below is
fresh from HEAD `5c3496e0` + WT bytes).

### Own trace: sites + roles

Orchestrator (definition):
`optimizer/nested_planner.py::plan_connection_relation`
(nested_planner.py:1090) -- the full windowed-prefetch
plan sequence: ordered refusal arms, per-key window
resolution, edges/node unwrap, one child-queryset build
through the injected seam, deterministic order read,
projection branches, one request per window to the
field-static strategy, merge-only-on-acceptance, field-
static advisory latch, metadata absorb + identity
recording on the success path only.

Six private helpers (definitions, each called in
production ONLY by the orchestrator -- verified by
package-wide grep over `django_strawberry_framework/`,
`tests/`, `examples/`):

1. `_divergent_key_windows` (def :967, sole prod call
   :1214; tests call it as an oracle -- oracles, not
   definitions) -- per-payload window/sidecar/malformed
   classification returning `(planned, malformed,
   fallbacks)`.
2. `_connection_node_selections` (def :801, sole prod
   call :1284) -- edges/node unwrap adapter over
   `selections.connection_node_children`.
3. `_identities_for_response_keys` (def :1057, prod
   calls :1245 + :1511) -- parallel-tuple filter for
   per-key identity recording.
4. `_log_connection_fallback` (def :1041, prod calls
   :1155, :1225, :1231, :1488) -- per-key fallback
   debug log.
5. `_raw_relation_field` (def :1079, sole prod call
   :1265) -- live `_meta` field resolution for the
   partition derivation.
6. `_select_nested_strategy` (def :225, sole prod call
   :1436; tests pin it as an oracle) -- field-static
   hint-override-or-default strategy selection.

Eight ordered refusal arms inside the orchestrator
(each an early `return` of an empty / identities-only
result, in body order): (1) unknown field (`:1151`),
(2) per-key argument conflict (`:1154`), (3) hint SKIP
(`:1176`), (4) no related model (`:1193`), (5) no
keyed window after the arguments-derived pass
(`:1256`, malformed keys record identities first),
(6) unwindowable join (`:1267`), (7) unwindowable
base child queryset (`:1301`), (8) every window
refused by the strategy (`:1494`).

Walker delegation (consumer, count 1):
`optimizer/walker.py::_plan_connection_relation`
(def :1819, sole call :782) -- pure delegation: binds
the eight walker-owned seams
(`_resolve_optimizer_hints`, `_resolve_relation_target`,
`_response_key_arguments_conflict`,
`_aliased_arguments_diverge`,
`_target_has_custom_get_queryset`,
`_resolver_identities_for`,
`_build_connection_child_queryset`,
`_build_prefetch_child_queryset_from_base`) and
`plan.merge_from(result.plan)` (:1854). No second
walker entry exists; no orchestration logic is
restated there.

Resolve side (consumer, count 1):
`connection.py::_resolve_from_window` (single def
:356, single call :744) reads the window's physical
shape back; `types/resolvers.py::_check_n1` with
`kind="connection_to_attr"` (:281) is the strictness
read of the recorded identities, and
`optimizer/extension.py` (:1464-1476) publishes
`planned_resolver_keys`. One resolve pipeline, no
second readback.

Neighboring owners composed BY NAME (excluded from
F1 on contract difference -- each owns a distinct
rule consumed here by call, none restates the
orchestration):

- Window-slice resolution:
  `_connection_window_slice_from_arguments` /
  `_keyset_window_slice_from_arguments` (+ shared
  `_coerce_pagination_int`, also read by
  `walker.py::_normalized_alias_payload`) -- the f19
  family seam; `_divergent_key_windows` routes per
  payload but owns neither adapter.
- Scalar-only projection: `_project_scalar_only_window`
  (sole prod call :1374) -- own open family.
- Keyset cursor-column projection:
  `_extend_only_projection` (prod calls :1386 +
  `connection.py` :961/:1011 -- the resolve side
  shares the owner, not a copy) -- own open family.
- Composite-index advisory: `_advise_composite_index`
  (+ `_concrete_order_terms`, `_index_*` chain, dedup
  LRU) -- own open family; the orchestrator only
  latches it after the first accepted window.
- `to_attr` grammar: `relation_connection_to_attr` +
  two compat delegates (`connection.py` :2320/:2330
  read the delegates) -- own open family.
- Order ladder: `plans.py::effective_connection_order`
  (the s10-noted transitive read of
  `utils/querysets.py::default_order` / `applied_order`
  -- ownership held for s16/s11, NOT litigated here).
- Fetch-mode value: `utils/connections.py::FetchMode`
  / `window_range_plan().fetch_mode()` -- one shared
  value derives both `with_total_count` and
  `next_page_probe` (:1456-1461).
- Strategy seam: `nested_fetch.py::resolve_strategy` /
  `active_strategy` / `NestedConnectionRequest` (sole
  prod construction :1462; test builders are oracles).
- Join classification: `join_taxonomy.py::
  classify_relation_join` (+ `window_partition_for_
  prefetch` shim in plans.py); merge verbs
  `merge_from` / `merge_metadata_from` owned by
  `plans.py::OptimizationPlan`; connection vocabulary
  + observers owned by `selections.py`; SKIP
  predicate owned by `hints.py`; cursor codec owned
  by `keyset.py`; accessor owned by
  `utils/relations.py::instance_accessor`.
- `_connector_only_field` (:168): zero production
  callers (test pins only) -- a shim over
  `classify_relation_join`, not orchestration.

### Own change challenges (definition counts)

C1 -- ninth refusal arm (e.g. refuse a new relation
shape): 1 definition (one arm in the orchestrator
body, beside the eight). No second site restates the
arm order.

C2 -- second request-construction site (e.g. a
divergent-scheme request variant): 1 definition (the
single `NestedConnectionRequest(...)` at :1462; the
per-key loop varies `to_attr`/`seek`/`bounds`
arguments, not the construction).

C3 -- splitting the merge (strategy absorb vs child
absorb): 1 orchestration definition. The two verbs
are plans-owned (`merge_from` full vs
`merge_metadata_from` metadata-only); the
orchestration rule -- merge-only-on-acceptance
(:1480) then absorb-on-success (:1503) -- lives once
in the orchestrator. The walker's `merge_from`
(:1854) is the atomic-result consumer, a different
contract (whole-result merge, unconditional).

C4 -- second walker entry (e.g. a list-path caller
planning connections): no second entry exists (one
def :1819, one call :782); adding one would still
call the orchestrator -- 1 definition either way.

C5 -- reorder arms / move the malformed-identities
write: 1 definition (all eight arms + both
`planned_resolver_keys` write pairs live in the one
body; `_identities_for_response_keys` is the single
filter both per-key writes share).

C6 -- change the per-window count/probe derivation
(e.g. a third observer): 1 definition -- the two
observers (:1411-1412) feed the one
`fetch_mode(...)` call (:1456); the mode's meaning
is owned by `utils/connections.py`, the orchestration
choice (union-conservative observers, one shared
decision) lives here once.

All six count 1. No posited orchestration change
forces a second definition with a landable owner.

### Owner I would choose

`optimizer/nested_planner.py::plan_connection_relation`
+ the six helpers above -- the module docstring
already declares this component owns the
orchestration, every legitimate consumer (walker,
strategies, resolve side) can depend on it without
reversing a dependency, and the injected walker
seams keep the dependency direction honest
(principle 7). No narrower owner is available (the
rule spans refusal, build, order, dispatch, absorb)
and no wider one is needed.

### Matrix (own discharge)

1. Cross-flavor mirroring: searched for sibling
   nested-connection planners (`def plan_*relation`,
   `def plan_*connection`, windowed `Prefetch`
   builders) -- `walker.plan_relation` is the
   list-relation walk (different contract: no slice
   window, no strategy seam), `extension.plan_relation`
   is the cache-entry planner, strategies consume
   `NestedConnectionRequest` rather than planning it.
   No mirror. Discharged by search.
2. Sync/async twins: `nested_planner.py` contains
   zero `async def` / `await` -- the planner is
   sync-only (plan time never executes queries);
   nothing to twin. Discharged (no async surface).
3. Derived knowledge: the orchestrator derives
   nothing by re-spelling -- vocabulary
   (`connection_field_names`), order
   (`effective_connection_order`), mode
   (`fetch_mode`), join (`classify_relation_join`),
   accessor (`instance_accessor`) all compose by
   name. Discharged by inspection.
4. Inverse / round-trip pairs: plan writes windows
   under the `to_attr` grammar, `_resolve_from_window`
   reads them back; the grammar has its own single
   owner (`relation_connection_to_attr`) read by both
   sides. No second pairing. Discharged.
5. Contracts in another medium: refusal wording in
   tests/docs are oracles/projections spelling
   expected fallbacks, never second implementations.
   Discharged by role classification.
6. Enforcement by omission: enumerated the refusal
   surface -- eight arms + per-payload sidecar /
   unwindowable / malformed classification; relation
   kinds route through `join.windowable` (join
   taxonomy owns the kind table, this family owns
   the refusal). No member lacks its gate without a
   contract reason. Discharged.

### Near-misses (own verdicts, pre-findings)

N1 -- `runtime_path[-1]` in
`_identities_for_response_keys` (:1075): SAFE. Every
`runtime_paths` entry is built as
`(*prefix, response_key)` (`walker.py:694-698`), so
each path is non-empty by construction; `[-1]` is
the response key. No defect owed.

N2 -- direct `_optimizer_response_key_arguments`
read (:1217): SAFE. Reached only when
`divergent` is true, and
`_aliased_arguments_diverge` returns `False` for
selections carrying no per-key map
(`walker.py:1778-1780` + docstring "never diverge").
The diverge premise is the guard. No defect owed.

N3/N4 -- file-item D1 (M2M advisory) / D2
(keyset annotation) attribution: cannot judge
pre-findings (item-local labels); will reconcile
against `## Findings` / `## Defects` below --
holding for the reconciliation pass.

### Zero-edit / scoping / typing (own verdicts,
pre-findings)

- Item-scoped diff: `git diff ITEM_BASELINE
  25bf01a1 --name-only` names ONLY
  `docs/dry/dry-0_0_15.md` (verified this session);
  `git status --short | wc -l` = 474. Tracked diff
  for the family is EMPTY (no `## Implementation`
  expected). RE-VERIFIED independently.
- s10 scoping: the order read MUST stay a composed
  call to `plans.py::effective_connection_order`
  with the `default_order` / `applied_order`
  ownership question held for s16/s11 and no row
  split -- will confirm W1 respected it when
  reading the findings.
- Cells all `unverified`: CORRECT in advance -- the
  orchestration outputs DB-executing windowed
  querysets (per-key `to_attr` prefetches), so
  inapplicable-by-construction cannot be claimed
  under the f18 ruling; a zero-edit census claims
  no execution either.
- Pending-execution `None`: CORRECT in advance iff
  no `execution-deferred` proof exists -- a census
  verdict moves nothing, proposes no gate, so no
  `proof:` / `gate:` entry is owed (plain
  `verified`, not pending-execution).

### Reconciliation (after reading `## Findings`)

Two membership deltas vs my pre-findings census,
both conceded to W1 with no verdict consequence:

R1 -- `NestedConnectionPlanResult`: W1 includes it
as an F1 definition (7 defs: entry + record + 5
helpers); I omitted it. W1 is right: it is the
transactional result vocabulary constructed at 9
in-module sites (8 arms + success), and I verified
fresh that `accepted` / `accepted_response_keys`
have ZERO production readers outside the planner
(the walker merges unconditionally), matching W1's
principle-11 keep note. Conceded; still count 1.

R2 -- `_select_nested_strategy`: W1 places it under
X2 (f17/f18 strategy-selection read), I placed it
as a sixth F1 helper. W1 is right AND consistent
with the record: the verified f18 artifact already
names it as a reader
(`dry-rule-nested-fetch-strategy-seam.md:22`,
`:682`); my placement would double-home it. The
body (hint-name read + `resolve_strategy` /
`active_strategy`, `:237-240`) is a composed read
of two owners, and either home agrees count 1 (one
def, one prod caller `:1436`). Conceded; no index
row owed (consumers need none).

Everything else AGREES with no delta:

- Eight refusal arms (same order, same sites),
  eight injected callables (W1's count correction
  matches my independent count of 8), one walker
  delegation (def `:1819`, call `:782`), one
  resolve side (`_resolve_from_window` def `:356`
  / call `:744` + `_check_n1` strictness read).
- Challenges: my C1-C6 and W1's six rows posit
  the same axes (ninth arm, scheme/dispatch
  variation, per-payload gate, identity vocab,
  merge discipline, acceptance signal) -- all
  count 1 on both sides.
- Matrix: all six axes discharge on the same
  reasons (no sibling planner; zero `async def` /
  `await`; compose-by-name; one grammar read by
  both round-trip halves; oracles/projections
  classified; eight arms + per-payload gates
  enumerated with no gap).
- Exclusions: 28 rows recounted independently
  (12 verified-converge + 5 open-family + 6
  composed-read + 5 carried; X22 superseded with
  no trigger owed, correct). Load-bearing rows
  re-verified fresh: X2 (body + f18 record), X3
  (sole build `:1462`, sole dispatch `:1479`;
  the other two `.plan(` calls are exactly the
  strategy-internal delegations
  `nested_fetch.py:421` + `lateral_fetch.py:990`),
  X13 (build `:1475`, probes `connection.py:2320`
  / `:2330`), X16/s10 (single ladder call
  `:1361`, querysets tier unlitigated -- s10
  scoping RESPECTED), X17 (cartesian proof
  `walker.py:694-698` re-derived), X18 (sole
  seam caller `walker.py:1239`; no walker import
  in the planner -- direction verified).
- Near-misses: N1/N2 safe (verified pre-findings);
  N3/D1 confirmed WT-only dirt on F3 lines
  (`through_model` absent at HEAD, present WT
  `:654` -- concurrent-owned, closeout decides);
  N4/D2 confirmed record-typed identically at
  HEAD (`:901`) + WT (`:911`). All 4 non-filings
  ENDORSED; no defect owed.
- Freshness: 13/13 WT+HEAD pins re-verified this
  session byte-identical to dispatch pins; HEAD
  `5c3496e0` unmoved; artifact untracked (`??`);
  `git diff 25bf01a1 --name-only` is the plan
  edit alone; status count 474 re-verified.
  Zero-edit CONFIRMED (no `## Implementation`).
- Structural gate (none proposed): JUSTIFIED --
  a per-helper name census is the bespoke test
  DRY.md forbids, and each plausible bypass
  breaks an existing behavioral oracle
  (strictness `raise` rows, alias-routing rows,
  fetch-mode exclusivity assertion). No negative
  control owed without a gate. Consistent with
  the f12-f25 zero-edit precedent shape.
- Index rows: NONE owed -- endorsed. F1's family
  row exists (Worker-0 ticks it); converges land
  on verified/open families; carried rejections
  stay at their owners.
- Pending-execution `None`: CORRECT -- no
  `execution-deferred` proof exists (all
  `static-reviewed`, nothing moves). Plain
  `verified`, NOT pending-execution.
- Cells all `unverified`: CORRECT under the f18
  ruling -- DB-executing windowed-prefetch
  outputs, inapplicability not claimed.
- AGENTS.md prose: tracked diff is empty (plan
  edit only); artifact is per-cycle scratch (raw
  `path:NN` allowed, no style cleanup owed).
  Ruff: vacuous -- zero tracked `.py` touched
  (`ruff check` on the artifact path: "No Python
  files found, All checks passed").
- Type gates (whole-package, re-run this
  session): `uv run mypy` -- Success, no issues
  in 119 files; `uv run basedpyright` -- 0
  errors, 0 warnings, 0 notes; `uv run python
  scripts/check_any.py` -- exit 0 (130 allowed
  uses at 90 sites).

No `## Defects` entry from Worker-2: nothing
found. No disagreement stands -- no `blocked`,
no third pass.

VERDICT: `verified` (plain).

