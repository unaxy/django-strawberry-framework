# DRY review: `optimizer/single_parent_fetch.py`

Status: verified
Run: 0.0.15 2026-09-19-1
Target: `django_strawberry_framework/optimizer/single_parent_fetch.py` (293 lines)
Blob: `e995270af9b213b7f931c03d7dc8f7c084819e1b` (worktree == HEAD ==
ITEM_BASELINE `e995270a`; zero diff on all three; target worktree-clean)
Item baseline: `e995270af9b213b7f931c03d7dc8f7c084819e1b` (resolves to the
target's own blob per `git cat-file -t`; `git diff HEAD --name-only` on the
target and on this artifact path prints nothing)
Ledger check: `## Owned changes` in the cycle plan names exactly one
optimizer-area row (walker D1 seal-policy: `_build_child_queryset` seal
policy + docstring); no row touches this item's paths. Confirmed before
reading the target. No production edit is made in this file item, so the
walker row is read-only context and needs no attribution.

## System trace

The target owns the runtime single-parent degenerate fast path for the
windowed nested prefetch: one plan-time spec record
(`SingleParentWindowSpec`), one eligibility predicate
(`single_parent_spec`), one fetch-time recognizer + executor
(`_single_parent_where_ids` + `_fetch_single_parent_rows`), and one
`RecognizedFetchQuerySet` subclass (`SingleParentWindowQuerySet`). Its
correctness contract is degradation, not SQL: every unrecognized shape
returns `None` and the shared skeleton's `_fetch_all` runs the
already-planned windowed body — a performance downgrade, never a
correctness cliff. The wrap is plan-time (rides the plan cache); only the
len==1 decision is fetch-time.

Sites read (roles: definition / consumer / oracle / projection):

- Definitions consumed (not owned here):
  `nested_fetch.py::RecognizedFetchQuerySet` (skeleton: `_clone`,
  `rebind`, `_fetch_all`, `_dst_window_signature` capture) +
  `::WindowedPrefetchStrategy.plan` (the sole caller of
  `single_parent_spec`, lazy import) + `::attach_windowed_prefetch`
  (shared floor) + `::NestedConnectionRequest` (seam record whose
  `__post_init__` already enforces the fetch-mode guard upstream of the
  spec) + `::unwindowable_child_queryset_reason` (first fetch gate);
  `lateral_fetch.py::_deduplicate_parent_ids`, `::_is_window_qual`,
  `::_parent_in_values`, `::_select_columns`, `::window_predicate_signature`
  (all five imported by name); `plans.py::WINDOW_ROW_NUMBER` (row-number
  grammar) + `::apply_window_pagination` (the mirrored numbering);
  `utils/connections.py::window_range_plan` / `::WindowRangePlan`
  (`plain_first_page`, `fetch_limit` decisions);
  `join_taxonomy.py::LateralJoinShape` / `::classify_relation_join`
  (DIRECT_FK shape + `parent_link_field` resolution, incl. the
  generic-relation `None` arm); `plans.py::deferred_loading_of`
  (projection read behind `_select_columns`);
  `conf.py::single_parent_fast_path_setting` (fetch-time flag) +
  `::SINGLE_PARENT_FAST_PATH_KEY`; `optimizer/__init__.py::logger`
  (debug line); `connection.py::_resolve_from_window` (probe
  re-inference from the ABSENT `_dst_total_count`); Django's
  `_filter_prefetch_queryset` (the `__in` injector, via test helper).
- Consumers of this file's definitions: `nested_fetch.py`
  (lazy `single_parent_spec` + `SingleParentWindowQuerySet`); no other
  production importer (package grep for `single_parent` names only this
  file, `nested_fetch.py`, `conf.py`, and `lateral_fetch.py` prose).
- Oracles: `tests/optimizer/test_single_parent_fetch.py` (285 lines, 15
  tests: 5-window reject matrix + keyset + subclass plan-time rows,
  15-arm fetch refusal matrix, 4 sqlite row-synthesis rows incl. probe
  sentinel + duplicated-id + nested-prefetch, clone-carry row; declares
  `_parent_in_values` / `_deduplicate_parent_ids` defensive matrices
  owned by `test_lateral_fetch.py`, imported not re-tested);
  `examples/fakeshop/test_query/test_single_parent_fastpath_api.py`
  (live wire-SQL rows: window skipped/probe/count/offset/keyset/empty
  plus the setting-off row); `test_nested_fetch.py` strategy rows
  (floor intact). All read as oracles, never rewritten; counted as
  definitions: zero.
- Projections: module docstring (degradation contract + the two
  verified corrections); `SingleParentWindowSpec` /
  `single_parent_spec` / `_fetch_single_parent_rows` docstrings (arm
  inventories); `conf.py` key comment (fetch-time, plan-cache
  invisible); `nested_fetch.py::WindowedPrefetchStrategy` docstring
  (wrap + lateral-out-of-v1-scope statements). Prior-cycle records used
  as trigger checks only: the lateral_fetch file item (F-D/F-E/F-F
  vocabulary, strategy seam, selection-adjacent guards — re-challenged
  fresh below, never inherited) and the plans/selections items
  (plan-record grouping, AST machinery — no rule here re-derives them).
- Node-root correction verified at source, not taken on prose:
  `types/relay.py::_resolve_node_default` returns `qs.first()` (an
  instance), so `node(id:)` roots never reach the windowed prefetch.

Sibling dirt (read-only; never edited): `optimizer/nested_fetch.py`
(worktree `29ce5201…` vs HEAD `4d8d37a7…`),
`optimizer/nested_planner.py` (worktree `e69dbf5f…` vs HEAD
`0ad8ff5d…`), `optimizer/join_taxonomy.py` (worktree `e1cbb3e3…` vs
HEAD `9b355a50…`), `optimizer/hints.py` (worktree `8064af14…` vs HEAD
`da46ef89…`). Mechanism sites below cite which bytes were read: the
skeleton + strategy bodies were read at WORKTREE bytes
(`29ce5201…`); `single_parent_fetch.py` at `e995270a…` (clean, ==
HEAD); `lateral_fetch.py`, `plans.py`, `utils/connections.py`,
`conf.py`, `types/relay.py`, `connection.py` at clean == HEAD bytes;
`join_taxonomy.py` link-field ownership statements grepped at worktree
bytes (`e1cbb3e3…`).

## Verification

### Matrix

1. Cross-flavor policy mirroring: no flavor twin. The target is
   optimizer-internal; the one shared vocabulary it touches is the
   nested-fetch seam (strategy + skeleton + recognizer helpers), owned
   by `nested_fetch.py` / `lateral_fetch.py`. No
   types/filters/orders/mutations/forms/DRF mirror exists to compare.
   Searched package for second pristine-clone `LIMIT` re-query
   executors and second `SingleParentWindowSpec` carriers: none
   outside this file + its one strategy caller + tests.
2. Sync/async twins — the item's fenced question: single-parent vs
   nested vs lateral is THREE fetch shapes under ONE skeleton in ONE
   sync color, not three twins and not one shape. Shapes: (a) the
   windowed ORM body (default floor), (b) the lateral raw-SQL branch
   (Postgres only), (c) the pristine-clone `LIMIT` re-query with
   Python-synthesized row numbers (this file, vendor-neutral). All
   three execute inside the sync `_fetch_all` override; the file
   carries zero `AsyncFunctionDef` (probe asserts 0 file-wide) and no
   `async`/`await`/`sync_to_async` token. Async callers reach every
   shape through the shared sync boundary (family `one-sync-boundary`,
   owned at `utils/querysets.py`); no async twin is owed by any of
   the three. The remaining split is vendor (Postgres-vs-else in
   lateral), not color. Single-parent counterpart likewise sync-only.
3. Derived rather than repeated knowledge: all derivations compose by
   name — range decisions via `window_range_plan` (`fetch_limit`
   freeze), projection via `_select_columns` (behind the plans
   `deferred_loading_of` owner), join links via the request's
   `RelationJoinDescriptor` (`single_parent_spec` reads
   `lateral_shape` + `parent_link_field`, never re-derives; the folded
   `DIRECT_FK`-and-link `None` branch is justified in prose by the
   taxonomy's always-resolved invariant for genuine FK relations),
   row-number grammar via `WINDOW_ROW_NUMBER`, flag via the conf
   owner, instances via the pristine clone's own iterator. No inline
   re-derivation found.
4. Inverse / round-trip pairs: (a) `apply_window_pagination` (render)
   / `_fetch_single_parent_rows` + `window_predicate_signature`
   (verify-then-reproduce) — one `WindowRangePlan` grammar, ORM `Q`
   dialect at `plans.py` vs ORM `LIMIT` re-query here; (b) the
   `to_attr` attach contract: `attach_windowed_prefetch` plans it,
   the pristine clone (carrying the same nested prefetches)
   satisfies it, `_fetch_all`'s nested-prefetch pass completes it
   (oracle: the two-level nesting test); (c) row-number synthesis:
   `enumerate` 1-based + probe sentinel mirrors the window's
   before-limit numbering, and `_dst_total_count` ABSENCE (never
   set) is the signal `connection.py::_resolve_from_window`
   re-infers the probe from. Each pair inventoried in `### Challenges`.
5. Contracts restated in another medium: every production rule below
   lists its oracles (package tests, 15 in-file + live fastpath rows)
   and projections (module + function docstrings, conf key comment,
   strategy docstring). Live-tier SQL-text rows
   (`test_single_parent_fastpath_api.py`) are cited, not counted. No
   rule requires a doc/test move: nothing is edited in this file item.
6. Enforcement by omission: `single_parent_spec` eligibility arms
   enumerated (C8 challenges); each arm's sibling coverage checked
   against `_build_lateral_spec` downgrade arms and the planner's
   strategy-independent refusal arms (read at worktree bytes).
   Divergences (THROUGH_TABLE refused here, admitted laterally;
   visibility WHERE carried laterally, inherited-from-pristine here;
   select_related/annotations refused at fetch here vs at plan
   laterally; counted keyset refused by both for separate reasons)
   are intentional contract separations, recorded with triggers.
   Plan-time admits shapes fetch-time refuses (child annotations,
   `extra`) only as planned-never-engages: the fetch gates are
   absolute (`extra` empty, `group_by` None, annotations exactly
   `{WINDOW_ROW_NUMBER}`), so the worst case is windowed performance,
   never a wrong row.

### Enumeration

Instrument: `ast.Module.body` walk (no imports of the target; Django
settings never touched). 16 top-level statements: 1 docstring, 10
imports (consumers, not rules), 5 defs, 0 async. Probe:
`docs/dry/temp-tests/dry-file-optimizer__single_parent_fetch/probe_enumeration.py`
— `OK blob=e995270a… top_level=16 defs=5 async=0`.

Every rule-bearing member (5 defs + subsumed class members) lands in
exactly one home. `SingleParentWindowQuerySet._fetch_recognized_rows`
is covered inside the F-D adapter row; the 8 spec fields inside FL1.

| # | Member | Home |
|---|---|---|
| 0 | module docstring (degradation contract + corrections 1-2) | projection (enforced by FL2/FL4 bodies) |
| 1-10 | imports (`dataclass`, `Any`, `QuerySet`, `window_range_plan`, `logger`, `LateralJoinShape`, 5 lateral names, 3 nested names, `WINDOW_ROW_NUMBER`; incl. the fetch-time lazy conf import) | consumers of F-D / F-E / F-F + six owner reads |
| 11 | `SingleParentWindowSpec` (+ 8 fields) | FL1 file-local record |
| 12 | `single_parent_spec` | FL2 file-local plan gate |
| 13 | `SingleParentWindowQuerySet` (`_dst_spec_attr`, `_dst_single_parent_spec`, `_fetch_recognized_rows`) | F-D `recognized-fetch-queryset-skeleton` (subclass adapter) |
| 14 | `_single_parent_where_ids` | FL3 file-local WHERE-walk |
| 15 | `_fetch_single_parent_rows` | FL4 file-local executor + recognizer |

Single-definition proof: package-wide `def`-grep for every row-11..15
name returns exactly one definition (the lateral counterparts —
`_recognize_lateral_fetch`, `_fetch_lateral_rows`,
`LateralQuerySet`, `_build_lateral_spec`, `LateralWindowSpec` — are
distinct bodies proving different queries, not duplicates); the FL-row
private names return hits in this file only. The strategy caller
imports by name (`nested_fetch.py::WindowedPrefetchStrategy.plan`
lazy `single_parent_spec` + `SingleParentWindowQuerySet`) —
enforcement site, never a second definition.

### Challenges

Change challenges posit a plausible rule change and count AUTHORITATIVE
definitions that must move (consumers / oracles / projections listed,
not counted). All static-reviewed against the blob above; no behavior
execution owed (zero-edit file item; every challenge resolves by body
identity; engagement itself is proven by committed oracles — the
row-synthesis tests assert `rows is not None`).

- C1 (range decisions): change `fetch_limit` semantics (e.g. probe
  adds two sentinels). Moves: `utils/connections.py::window_range_plan`
  = 1 owner; `single_parent_spec` (freeze) + `_fetch_single_parent_rows`
  (slice) + both window renderers follow. Count: 1. Oracles: probe
  overfetch rows (package + live).
- C2 (signature grammar): fold `lookup_name` out of the leaf
  signature. Moves: `window_predicate_signature` + `_normalize_window_node`
  = 1 owner body; this file's capture (via `rebind`) + compare follow.
  Count: 1. Consumers listed, not counted.
- C3 (parent-IN recognition): match the `__in` leaf by column only,
  dropping the table check. Moves: `lateral_fetch.py::_parent_in_values`
  = 1; `_single_parent_where_ids` follows. Count: 1.
- C4 (dedup/NULL semantics): keep NULL ids as matchable branches.
  Moves: `_deduplicate_parent_ids` = 1; the `len(unique) != 1` gate
  follows. Count: 1.
- C5 (projection modeling): admit `defer()` shapes. Moves:
  `plans.py::deferred_loading_of` = 1; `_select_columns` reads;
  FL1 freeze + FL4 recompute follow. Count: 1.
- C6 (clone contract): carry a second per-strategy slot. Moves:
  `nested_fetch.py::RecognizedFetchQuerySet` (`_clone` + `rebind` +
  `_fetch_all`) = 1; both subclasses follow. Count: 1.
- C7 (strategy seam): add a fourth built-in strategy name. Moves:
  `nested_fetch.py::resolve_strategy` registry + `StrategySelection`
  chain = 1; `WindowedPrefetchStrategy.plan`'s spec-or-bare branch
  untouched. Count: 1.
- C8 (FL2 arms, axis 6 — each eligibility refusal challenged for a
  missing sibling): keyset seek (lateral admits count-free seeks —
  parallel, separate contracts: raw-SQL seek splice vs plain `LIMIT`
  irreproducibility); `with_total_count` (both refuse; lateral
  because the count scan buys nothing raw, here because a bare
  `LIMIT` cannot synthesize the partition count — same verdict,
  separate reasons); `reverse` (reversed row number uncomputable
  from a forward page); custom-QS-subclass (same arm as lateral —
  parallel, same rebind-erasure reason, separate contracts);
  DIRECT_FK+link (THROUGH_TABLE admitted laterally, refused here by
  correction 2: M2M `extra(select=…)` irreproducible from a pristine
  clone — intentional separation, trigger: pristine-clone
  prefetch-attr reproduction); plain-first-page (offset/unbounded/
  zero-limit rows each pinned by an oracle reject row; lateral's
  offset/unbounded shapes stay windowed-or-lateral by its own
  expressibility arms). Planner-level refusals (sidecar, SKIP,
  unwindowable child/kind) never reach any strategy; no arm owes a
  guard elsewhere — every refusal keeps the planned windowed body.
- C9 (FL4 gates — each fetch-time refusal challenged the same way):
  setting off (conf-owned kill switch, live-pinned); unwindowable
  (skeleton-shared classifier); `extra`/`extra_tables`/`group_by`
  (absolute emptiness — the M2M `extra(select)` block that enforces
  correction 2 at fetch); order tuple + `standard_ordering`
  (freeze-vs-drift); annotations exactly `{WINDOW_ROW_NUMBER}`
  (plan-time admits, fetch-time refuses — planned-never-engages,
  perf-only); planned-signature `None` or mismatch (mutated/added/
  dropped bound caught here, never silently ignored — oracle: the
  tightened-`lte` and added-`gt` rows); `select_related` +
  projection recompute (pristine re-query would otherwise load a
  different column/relation set); WHERE-walk residue (second filter,
  second IN, expression rhs, negated/OR root — each oracle-pinned);
  `len(unique) != 1` (zero falls to the windowed empty result, two
  stays windowed, duplicated-one dedups — all three oracle-pinned).
- C10 (row-number synthesis): number from 0, or set
  `_dst_total_count`. Moves: the `plans.py` window numbering grammar
  = 1 (the window function numbers before-limit 1-based); the
  `enumerate` + never-set-absence here mirrors it, and
  `connection.py::_resolve_from_window` consumes the absence to
  re-infer the probe. Count: 1 grammar. Oracles: rn 1..N rows +
  sentinel row + resolver probe rows.
- C11 (flag semantics): default the fast path off. Moves:
  `conf.py::single_parent_fast_path_setting` (+ key constant) = 1;
  the lazy fetch-time read follows (override_settings-observable by
  construction). Count: 1. Oracle: live setting-off row.
- C12 (link resolution): resolve `parent_link_field` for generic
  relations. Moves: `join_taxonomy.py::classify_relation_join` = 1;
  the folded `is not DIRECT_FK or ... is None` branch follows.
  Count: 1.
- C13 (M2M admission): support THROUGH_TABLE. Single-site decision
  (correction 2); trigger in C8. Count: 1 (this file only — no
  second site to move).
- C14 (sync/async): move fetch execution off the requesting thread.
  No async twin exists to move; the await boundary lives at the
  shared sync-boundary owner (family `one-sync-boundary`).
  Inapplicable by construction: ORM iteration + `setattr`
  instantiation must run in a sync context; recorded, not counted.

## Findings

Worker 0 note: families F-D/F-E/F-F are REUSED from the plan's
`## Responsibility index` (already open; no plan edit made from this
item); FL1–FL4 + R1–R6 are recorded here for routing. Suggested
owners/holding items follow principle 7 (narrowest importable owner).
No consolidation in a file item — every family below is already-single
or already-shared by construction; the family item decides gates.

### F-D `recognized-fetch-queryset-skeleton` (reuse; owner `nested_fetch.py::RecognizedFetchQuerySet`)

Contract: clone-surviving spec slot + planned-window signature capture
at `rebind` + recognized-rows-or-windowed-body `_fetch_all`. Sites:
definition/skeleton `nested_fetch.py` (worktree bytes);
`SingleParentWindowQuerySet` (this file: `_dst_single_parent_spec`
slot + `_fetch_recognized_rows` → `_fetch_single_parent_rows`) beside
the lateral adapter; oracles: clone-carry row (spec identity +
signature ride `.using().filter()`) + nested-prefetch row (recognized
rows still drive the superclass prefetch pass). Challenges: C6
(count 1). Sub-behaviors stay separate: the two recognizers prove
different queries (pristine `LIMIT` re-query vs lateral SQL) — sharing
stops at the skeleton by design (principle 5: shared lifecycle, kept
adapters). Re-challenged fresh: posit "a second per-strategy slot" —
moves the skeleton's `_clone`/`rebind` only; neither subclass body
moves. No new index row (family already open).

### F-E `nested-recognizer-shared-vocabulary` (reuse; owner `lateral_fetch.py`)

Contract: the window-identity helpers every nested-fetch recognizer
composes by name — `window_predicate_signature`, `_is_window_qual`,
`_parent_in_values`, `_select_columns`, `_deduplicate_parent_ids`.
Sites: definitions `lateral_fetch.py`; this file consumes all five by
name (FL3 + FL4 + FL1-freeze); oracles: signature/parent-id rows here
plus the declared-owned defensive matrices in `test_lateral_fetch.py`
(single owner, imported-not-retested here); projections: the helpers'
own docstrings (each states its insufficiency / twin relation).
Challenges: C2, C3, C4, C5 (count 1 each). Already-single; this
file's `_single_parent_where_ids` + `_fetch_single_parent_rows` are
the twin recognizer body, not a second definition of any member.
Re-challenged fresh: posit "drop the table check" (C3) — moves the
`_parent_in_values` body only; the twin walk follows without moving.
No new index row (family already open).

### F-F `nested-fetch-strategy-seam` (reuse; owner `nested_fetch.py`)

Contract: strategy selection + planning floor —
`NestedConnectionStrategy` protocol, `StrategySelection`,
`resolve_strategy`, `attach_windowed_prefetch` (shared floor),
`WINDOWED_STRATEGY` / `LATERAL_STRATEGY` / `AUTO_STRATEGY`.
Sites: definitions `nested_fetch.py` (worktree bytes) + member branch
`WindowedPrefetchStrategy.plan` (this file's entry: spec-or-bare,
always ending in the shared floor) + the lazy import breaking the
documented cycle; oracles: strategy-resolution rows + the
`isinstance(entry.queryset, SingleParentWindowQuerySet)` plan rows;
projections: strategy docstring (wrap + lateral-out-of-v1-scope).
Challenges: C7 (count 1). The wrap adds no selection logic.
Re-challenged fresh: posit "a fourth builtin name" — moves the
`resolve_strategy` registry only; `single_parent_spec` untouched.
No new index row (family already open).

### FL1 `SingleParentWindowSpec` record (file-local; challenge C1/C5/C12)

Plan-frozen carry: pristine child queryset (projection + nested
prefetches + visibility hook), frozen order, link attname/column/table
triple, `fetch_limit`, frozen `select_related` + `select_columns`.
Single-site proof: package `def`-grep + consumer census show no second
spec carrying the same plan (`LateralWindowSpec` carries a different
plan: model/db_table/order_columns/seek/visibility — different
contract, R-separation below). Reopen: a second importing site or a
sibling re-derivation.

### FL2 `single_parent_spec` eligibility predicate (file-local; challenge C8)

Six refusal arms (keyset / count-or-reverse / subclass / join-shape+link
/ range-plan / plain-first-page), each oracle-pinned, each adjudicated
against lateral + planner siblings in C8. Single-site proof: only
`WindowedPrefetchStrategy.plan` calls it. Reopen: a second eligibility
site.

### FL3 `_single_parent_where_ids` WHERE-walk (file-local; challenge C3)

"Window range + ONE parent IN" structural walk minus the
keyset/visibility arms: non-negated AND root, window quals skipped,
at most one IN accepted, everything else fails closed. Twin — not
duplicate — of `_recognize_lateral_fetch`'s walk (different proven
query, different residue handling: here at-most-one-IN, there
unrecognized-list + seek/visibility matchers). R1 rejects the merge
with trigger. Reopen: a third recognizer needing the same walk core.

### FL4 `_fetch_single_parent_rows` executor + recognizer (file-local; challenges C9/C10/C11)

Fail-closed gate chain (C9) + pristine `.using(db)` re-query with
`fetch_limit` slice (C1) + 1-based rn synthesis with probe sentinel
and never-set total count (C10) + fetch-time setting read (C11) +
debug line via the shared logger (consumer of the consolidated
logger family). Single-site proof: sole pristine-clone `LIMIT`
executor in the package. Reopen: a second executor from a stored
plan. Consumer notes (no new families): `fetch_limit` composes the
`window-range-dual-render` plan object; the count/reverse/keyset pins
fold the upstream `window-fetch-mode-guard`; the keyset arm is a
refusal only toward `keyset-seek-dual-dialect`; `WINDOW_ROW_NUMBER`
composes the plans grammar.

### Rejections

- R1 (WHERE walks): considered merging `_single_parent_where_ids`
  into `_recognize_lateral_fetch`'s walk; rejected — different proven
  queries (window+IN only vs window+IN+seek/visibility), different
  residue contracts (at-most-one-IN vs matcher-verified residue).
  Trigger: a third recognizer needing the shared walk core.
- R2 (`SingleParentWindowQuerySet` vs `LateralQuerySet`): considered
  one recognizer queryset; rejected — specs, recognizers, and row
  sources differ; sharing stops at the F-D skeleton (matches the
  lateral item's R2 from this side). Trigger: a third backend needing
  a different clone contract.
- R3 (three plan-gate arm sets into one): `single_parent_spec`
  eligibility vs lateral `_build_lateral_spec` vs planner
  strategy-independent refusals — rejected, three contracts
  (pristine-re-query reproducibility / raw-SQL expressibility /
  strategy-independent safety), triggers per arm in C8 (matches the
  lateral item's R4 from this side).
- R4 (visibility carry): considered adding `visibility_where` to the
  spec à la lateral; rejected — the pristine re-query INHERITS the
  child WHERE (incl. any `get_queryset` scope) by construction, so
  there is nothing to compile or splice. Trigger: a fetch path that
  discards the ORM query and must reproduce a scope another way.
- R5 (async twin): no twin exists; sync-only recorded (matrix axis
  2), never a gap.
- R6 (THROUGH_TABLE support): refused by correction 2 (M2M
  `extra(select=…)` irreproducible from a pristine clone); enforced
  at plan (FL2) AND fetch (FL4 `extra` gate). Trigger:
  pristine-clone prefetch-attr reproduction.

## Defects

None. Audited while tracing (all static-reviewed against blob
`e995270a…`); each candidate names the contract row it would break
and the wire input reaching it — none met the bar:

- (a) Order-freeze engagement: `single_parent_spec` freezes
  `tuple(request.order_by)` while fetch compares
  `tuple(query.order_by)` — if `apply_window_pagination` reordered,
  the path would never engage (perf-only, silent). Rejected: the
  committed synthesis oracles assert `rows is not None` on the
  eligible shape, so engagement is proven, not assumed.
- (b) Plan/fetch gate split: plan-time admits child annotations and
  `extra` that fetch-time refuses absolutely. Rejected: worst case is
  planned-never-engages (windowed performance); no wrong row is
  reachable, and the M2M `extra(select)` block holds at BOTH levels.
- (c) `qs.none()` child: `EmptyWhere` residue fails the WHERE walk
  closed; the windowed body serves the empty page. No gap.
- (d) Module-docstring correction 1 (`node(id:)` never reaches the
  window): verified at `types/relay.py::_resolve_node_default`
  (`qs.first()` instance return), not taken on prose.
- (e) Unhashable parent ids: the `_deduplicate_parent_ids` fallback
  keeps order and NULL-drops; a single unhashable id still filters
  by attname equality. No contract source requires unhashable
  dedupe; no row broken.
- (f) Zero/two parents: both fall back (`[]` → windowed empty
  result; two → windowed pages), each oracle-pinned. No gap.

## Pending execution

None. Zero-edit file item; every proof above is `static-reviewed`
(body-identity, single-`def` census, import census). The one
mechanical probe ran read-only: `uv run python
docs/dry/temp-tests/dry-file-optimizer__single_parent_fetch/probe_enumeration.py`
→ `OK blob=e995270a… top_level=16 defs=5 async=0`. No shared-tree
pytest run (not authorized by the entry command; inspection beats
execution on every challenge — engagement and refusal behavior are
already pinned by committed oracles the final gate runs:
`tests/optimizer/test_single_parent_fetch.py`,
`examples/fakeshop/test_query/test_single_parent_fastpath_api.py`).

## Judgment

File item discharged with zero edits: 5 rule-bearing members assigned
(3 families reused for Worker 0 — `recognized-fetch-queryset-skeleton`,
`nested-recognizer-shared-vocabulary`, `nested-fetch-strategy-seam` —
4 file-local rows FL1–FL4; 6 rejections with triggers), matrix
discharged on all six axes (sync/async answered as three fetch shapes,
one skeleton, one sync color), challenges counted (every count 1 or
inapplicable-by-construction). The file composes its owners by name
throughout; it defines no multi-site rule (the five vocabulary imports
are already-single under F-E). No consolidation owed here by design.
No `## Owned changes` append (untracked artifact + probe only).

Item-scoped diff state: EMPTY on tracked paths (no production edit;
this artifact and the probe are untracked). Concurrent dirt listed in
the trace untouched throughout; nothing committed.
Scratch: `docs/dry/temp-tests/dry-file-optimizer__single_parent_fetch/probe_enumeration.py`
(remove by explicit path after verification, the directory if empty).


## Independent verification (Worker 2)

Phase 1 only: no status set, no verdict on Worker 1's work. This trace was built
from the target, its neighbors, the oracles, and package-wide content searches.
Independence note: one package-wide content search incidentally returned short
line fragments from Worker 1's artifact and the lateral-fetch artifact; neither
file was opened and nothing below reuses their naming or counts. Every family
label (HF-A through HF-H), rejection (R-a through R-d), count, and owner choice
is my own, derived from source.

### Target identity

`django_strawberry_framework/optimizer/single_parent_fetch.py`, 293 lines,
worktree-clean (worktree blob equals HEAD blob; fingerprint table below).
HEAD of this worktree is bfaee91d. No production edit is owed by this file item;
candidates route to holding families named below.

### Enumeration

Instrument: every name in `ast.Module.body`. Count is 16: 1 module docstring,
10 `ImportFrom` statements, 5 definitions
(`SingleParentWindowSpec`, `single_parent_spec`, `SingleParentWindowQuerySet`,
`_single_parent_where_ids`, `_fetch_single_parent_rows`).

Member assignment (my naming):

- Module docstring -> projection (states the runtime-only fast path, the two
  verified corrections, the strict-degradation contract). Not a definition.
- `ImportFrom` members -> consumers by name, each routed to its owner's family:
  `window_range_plan` -> HF-C; `logger` -> the package logger family;
  `LateralJoinShape` -> HF-E; `_deduplicate_parent_ids`, `_is_window_qual`,
  `_parent_in_values`, `_select_columns`, `window_predicate_signature` -> HF-A;
  `NestedConnectionRequest`, `RecognizedFetchQuerySet`,
  `unwindowable_child_queryset_reason` -> HF-B / HF-D;
  `WINDOW_ROW_NUMBER` -> HF-F; the lazy `conf::single_parent_fast_path_setting`
  import inside `_fetch_single_parent_rows` -> conf owner.
- `SingleParentWindowSpec` -> HF-H (target-owned record; contrasted with
  `LateralWindowSpec` in rejection R-a).
- `single_parent_spec` -> HF-H (the plan-time eligibility conjunction; consumes
  HF-C, HF-D, HF-E, HF-F, conf).
- `SingleParentWindowQuerySet` -> HF-B (named adapter on the shared skeleton:
  supplies the spec slot `_dst_single_parent_spec` and the recognizer entry).
- `_single_parent_where_ids` -> HF-A candidate walk with a distinct proven
  postcondition; kept target-owned per rejection R-b.
- `_fetch_single_parent_rows` -> HF-H (the fetch-time recognition sequence;
  consumes HF-A, HF-C, HF-F, HF-G, conf). No member is left unassigned; no
  consolidation is performed inside this file item.

Holding families (file item routes here, never consolidates):

- HF-A "fetch-recognizer shared vocabulary", owner
  `optimizer/lateral_fetch.py` (`_is_window_qual`, `_parent_in_values`,
  `_deduplicate_parent_ids`, `window_predicate_signature` plus
  `_normalize_window_node`, `_select_columns` which itself derives through
  `plans.py::deferred_loading_of`).
- HF-B "recognized-fetch lifecycle", owner
  `optimizer/nested_fetch.py::RecognizedFetchQuerySet` (`_clone`, `rebind`,
  `_fetch_all`, `_fetch_recognized_rows` contract).
- HF-C "window-range decisions", owner `utils/connections.py::window_range_plan`
  / `::WindowRangePlan` (`plain_first_page`, `fetch_limit`,
  `fetch_upper_bound`, marker/probe composition).
- HF-D "nested-connection strategy seam", owner `optimizer/nested_fetch.py`
  (`NestedConnectionRequest`, `WindowedPrefetchStrategy`,
  `attach_windowed_prefetch`, `active_strategy`, `resolve_strategy`).
- HF-E "join-shape taxonomy", owner `optimizer/join_taxonomy.py`
  (`LateralJoinShape`, `RelationJoinDescriptor`, `parent_link_field`
  resolution, `classify_relation_join`).
- HF-F "window annotation namespace and projection", owner
  `optimizer/plans.py` (`WINDOW_ROW_NUMBER` and siblings,
  `deferred_loading_of`, `apply_window_pagination`, deterministic-order
  helpers).
- HF-G "fetch-mode policy", owner `utils/connections.py` (`FetchMode`,
  `assert_window_fetch_mode`, `assert_window_fetch_mode_for`).
- HF-H "single-parent runtime shape", target-owned candidate (the spec record,
  the eligibility conjunction, the WHERE walk, the fetch sequence, the
  queryset slot). File-local if the matrix confirms no second site.

Rejections of my naming (contract difference plus reconsideration trigger):

- R-a: `SingleParentWindowSpec` vs `LateralWindowSpec` are not one rule. The
  lateral record renders raw SQL (db table, order columns, through join,
  visibility WHERE, keyset seek, offset/limit/reverse/count); the single-parent
  record re-queries the ORM (pristine child queryset, order_by tuple, parent
  link attname/column/table, fetch limit, select_related graph, select
  columns). Overlap (link column/table, select columns) is read from shared
  owners, not restated. Trigger: a third fetch shape needing both renderings
  from one record, or a change forcing the shared subset to move in lockstep
  beyond the owned primitives.
- R-b: `_single_parent_where_ids` vs lateral `_recognize_lateral_fetch` is not
  one walk. Mine proves "window quals plus at most one parent IN, anything else
  fails closed"; lateral proves that plus keyset-seek residue and
  visibility-WHERE byte-equality arms and returns approved bytes. Trigger: a
  lateral single-parent ORM mode sharing the exact residue grammar.
- R-c: row synthesis (`setattr` rn 1..N, never set total count, ORM instances
  from the pristine clone) vs lateral `_instantiate_row` (`from_db` plus
  converters, parent-id aliases, optional count) is not one constructor.
  Trigger: both backends materializing rows from one shared primitive.
- R-d: `single_parent_spec` vs lateral `_build_lateral_spec` is not one gate.
  Mine decides degenerate-shape eligibility (count-free plain first page,
  DIRECT_FK, plain QuerySet); lateral decides SQL-expressibility (no
  select_related/annotations/extra, plain local columns, defer/projection
  shape, keyset arity). Trigger: v1 scope admitting M2M, keyset, or counted
  shapes into the single-parent path.

### Matrix

Searches run (content search over the package source): `single_parent /
SingleParent` (33 hits, all in target, `nested_fetch.py`, `conf.py`, plus test
and artifact paths excluded from reasoning); `_select_columns /
_deduplicate_parent_ids / _parent_in_values / _is_window_qual /
window_predicate_signature` (owners in `lateral_fetch.py`, consumers in
target and `nested_fetch.py`); `_resolve_from_window`, `_resolve_node_default`,
`single_parent_fast_path_setting`, `_fetch_all`, `async def` counts
(0 in target, lateral, nested_fetch, walker), `SINGLE_PARENT_FAST_PATH_KEY`.

1. Cross-flavor policy mirroring: discharged by absence with reason. The rule
   is optimizer-internal (windowed-prefetch execution); no sibling flavor
   (types, filters, orders, mutations, forms, rest_framework) defines window
   specs, fetch recognizers, or parent-IN handling. No second surface exists.
2. Sync/async twins: inapplicable by construction. There are zero `async def`
   in the target, `lateral_fetch.py`, `nested_fetch.py`, and `walker.py`; the
   fetch executes inside Django's synchronous prefetch machinery
   (`_fetch_all`), and the async surface runs ORM work inside one
   `sync_to_async` worker (`utils/querysets.py` discipline). The target reaches
   no await, cancellation, thread-affinity, or cleanup decision, so there is no
   twin to drift. This is the correct side of the DRY.md principle 5 contrast:
   pure fetch-time decisions shared by import, one sync body, no colored copy.
3. Derived rather than repeated knowledge: discharged. Each fact is derived
   once at plan time and frozen in the spec (order tuple, fetch limit via
   `window_range_plan`, link attname/column/table via the join descriptor,
   select_related graph, select columns via `_select_columns`), then
   re-verified at fetch time, never re-derived. No site respells the link, the
   bound, or the projection.
4. Inverse / round-trip pairs: discharged. The capture/compare pair is one
   grammar owned by HF-A: `rebind` captures `window_predicate_signature` off
   the planned windowed body before the prefetch IN is appended; the fetch
   recognizer re-derives and demands equality. The target adds no second
   grammar and no second normalization.
5. Contracts restated in another medium: classified, not counted. Production
   (target), oracles (`tests/optimizer/test_single_parent_fetch.py` for
   plan/fetch units and row synthesis;
   `examples/fakeshop/test_query/test_single_parent_fastpath_api.py` for live
   HTTP payload plus OVER(/LIMIT SQL-shape assertions), and the lateral
   defensive-matrix tests that own `_parent_in_values` / `_deduplicate_parent_ids`
   arms by explicit cross-reference), and projections (module docstrings in
   target and `nested_fetch.py::WindowedPrefetchStrategy`) each keep their
   role. No oracle was rewritten to read the owner it checks, except one
   structural test (`test_clone_carries_the_spec`) that asserts the clone
   channel itself; that test pins the file's own contract, not a shared rule.
6. Enforcement by omission: discharged by enumerating the eligibility family
   (gate table below). Every ineligible shape returns `None` and the
   superclass runs the already-planned windowed body: fallback, never error,
   never a silent fast path. The absent vendor gate is justified, not a gap:
   the fast path re-queries the ORM (vendor-neutral) rather than rendering raw
   SQL, so there is no Postgres-only branch to gate.

Prompt axes. Three fetch shapes: one shared skeleton (`HF-B`) with named
adapters (`LateralQuerySet` plus lateral recognizer; `SingleParentWindowQuerySet`
plus single-parent recognizer), not mode flags: each subclass names its spec
slot via `_dst_spec_attr` and supplies `_fetch_recognized_rows`; the windowed
body is untouched in both. Sync/async twins: none exist and none are owed
(axis 2). Window-spec records: one per shape (`NestedConnectionRequest` at the
seam, `LateralWindowSpec` for SQL rendering, `SingleParentWindowSpec` for ORM
re-query), sharing primitives by name (R-a). Eligibility gates: plan-time
`single_parent_spec` admits only the count-free plain-first-page DIRECT_FK
shape on a plain QuerySet; everything else keeps the windowed plan, and every
fetch-time deviation falls back to the windowed body (gate table below).

### Challenges with definition counts

Each posited change names the definitions that must move (consumers, oracles,
and projections that also move are listed separately and not counted):

- Change window-qual classification (e.g. a new annotation kind): 1,
  `lateral_fetch.py::_is_window_qual`. Target imports it.
- Change prefetch-IN matching (e.g. stricter target/table rule): 1,
  `lateral_fetch.py::_parent_in_values`. Target imports it with keywords.
- Change NULL/unhashable dedup semantics: 1,
  `lateral_fetch.py::_deduplicate_parent_ids`. Target imports it; its
  `len(unique) != 1` gate stays target-owned.
- Change window-signature normalization (e.g. a new lookup operator): 1,
  `lateral_fetch.py::window_predicate_signature` (with
  `_normalize_window_node`). Target calls it; capture rides the shared
  `rebind`.
- Change deferred-loading unpack (only/defer read): 1,
  `plans.py::deferred_loading_of`. `lateral_fetch.py::_select_columns`
  derives through it; target consumes `_select_columns`.
- Change range semantics (`plain_first_page`, `fetch_limit`, probe
  composition): 1, `utils/connections.py::window_range_plan`. Target,
  `plans.py::apply_window_pagination`, and lateral `build_lateral_sql` all
  read it.
- Change the annotation token (rename `_dst_row_number`): 1, `plans.py`.
  All sites import the token.
- Change link resolution (generic morph, virtual multi-column link): 1,
  `optimizer/join_taxonomy.py`. Both specs read the descriptor.
- Change the recognized-or-fallback `_fetch_all` contract: 1,
  `nested_fetch.py::RecognizedFetchQuerySet`. Both subclasses inherit it.
- Change the eligibility conjunction (e.g. admit offset pages): 1,
  target `single_parent_spec`; oracles move as consumers (not counted).
- Change the fetch-time guard sequence (e.g. a new drift check): 1, target
  `_fetch_single_parent_rows`.
- Change the WHERE-walk shape (e.g. admit a visibility qual): 1, target
  `_single_parent_where_ids`.
- Change the setting key or default: 1, `conf.py`; target reads it live at
  fetch time so the flag stays plan-cache invisible.

### Owners I would choose per rule (DRY.md principle 7)

Keep the current owners: recognizer vocabulary with `lateral_fetch.py`
(narrowest cohesive owner every consumer can import without reversing the
strategy dependency); skeleton with `nested_fetch.py` (owns the strategy seam
both adapters hang off); range decisions with `utils/connections.py`
(cycle-safe home both renderers already share); link facts with
`join_taxonomy.py` (single classifier, dependency direction wins); annotation
tokens and deferred-loading unpack with `plans.py`; fetch-mode exclusion with
`utils/connections.py`; the setting with `conf.py`. The target owns only its
spec shape, its eligibility conjunction, its WHERE walk, its guard sequence,
and its spec slot: the narrowest owner the strategy's wrap site can depend on.

### Eligibility gates: every arm proved or else a defect (none outstanding)

Plan-time (`single_parent_spec`; `None` keeps the plain windowed plan):

- `keyset_seek is not None` -> `None`. Double-guarded: the seek residue would
  also fail the fetch WHERE walk. Pinned by `test_spec_rejects_a_keyset_seek`
  plus live `test_single_parent_keyset_seek_page_keeps_window_over_http`.
- `with_total_count` -> `None` (a bare LIMIT cannot count). Double-guarded:
  a counted window carries `_dst_total_count`, failing the fetch annotation
  check. Pinned by `test_spec_rejects_ineligible_windows` (counted arm) plus
  live `test_single_parent_total_count_keeps_window_over_http`.
- `reverse` -> `None` (last-only needs the reversed row number).
  Double-guarded: a reversed window carries `_dst_row_number_reversed`,
  failing the same check. Pinned by the reject matrix (reverse arm).
- Custom QuerySet subclass (`type(...) is not QuerySet`) -> `None` (the class
  rebind would erase subclass state; same rule as `_build_lateral_spec` by
  shared rationale, each stated at its site). Unreachable at fetch by
  construction (spec can only exist when this passed). Pinned by
  `test_spec_rejects_a_custom_queryset_subclass`.
- Join shape not DIRECT_FK or `parent_link_field is None` (single folded
  branch; M2M THROUGH_TABLE and generic relations excluded per the module's
  correction 2) -> `None`. Double-guarded at fetch: M2M prefetch attaches via
  `extra(select=...)`, failing the `query.extra` check. Pinned live by
  `test_m2m_shape_keeps_window_over_http`.
- Not `plain_first_page` (offset pages, unbounded `limit is None`,
  `limit == 0`) -> `None`. The fetch signature check pins the exact planned
  range, so a mutated bound cannot slip through. Pinned by the reject matrix
  (offset/unbounded/zero arms) plus live offset/seek-keep-window tests.

Fetch-time (`_fetch_single_parent_rows`; every arm returns `None` and the
superclass runs the identical windowed body):

- Missing spec, disabled setting, `unwindowable_child_queryset_reason`
  (sliced, select_for_update, combined, distinct, values), `extra` /
  `extra_tables` / `group_by`, order drift or reversed ordering, annotation
  set not exactly `{WINDOW_ROW_NUMBER}`, window-signature mismatch or
  unnormalizable plan, select_related drift, select-columns drift, WHERE tree
  not exactly window-range plus one parent IN (including negated/OR roots,
  second IN, consumer filters, expression rhs), zero parents, more than one
  parent. Each arm is pinned by a named case in
  `test_fetch_returns_none_for_unrecognized_shapes` (15 mutations),
  `test_fetch_returns_none_without_a_spec`,
  `test_fetch_returns_none_without_a_parent_filter`,
  `test_fetch_returns_none_for_a_consumer_filter_without_a_parent`,
  `test_fetch_returns_none_for_a_mutated_root_node`,
  `test_fetch_returns_none_for_zero_parents`,
  `test_fetch_returns_none_for_two_parents`.
- Duplicated single parent id dedups to one and engages (pinned by
  `test_fast_path_accepts_a_duplicated_single_parent_id`); the probe shape
  fetches `fetch_limit` rows numbered through the sentinel (pinned by
  `test_fast_path_probe_overfetches_the_sentinel_row`); `_dst_total_count` is
  never set so `connection.py::_resolve_from_window` re-infers the probe
  (pinned live by `test_single_parent_probe_shape_overfetches_without_window_over_http`
  asserting `LIMIT 3` and `hasNextPage`); keyset first-page cursors mint from
  column values and round-trip (pinned live by
  `test_single_parent_keyset_first_page_skips_window_as_staff_over_http`);
  nested prefetches survive via the pristine clone driving `_fetch_all`
  (pinned by `test_fast_path_populates_a_nested_prefetch`); the spec and the
  window signature survive every clone (pinned by
  `test_clone_carries_the_spec`).

Two observations investigated and ruled not defects (no reaching input under
supported public API): (a) `select_columns` compares `None == None` for
defer-shaped projections, so two different defer masks would compare equal;
only the prefetch machinery writes between plan and fetch and it never touches
defer, and the pristine re-query carries the planned mask either way.
(b) Annotated children still get a spec at plan time but always fail the
fetch annotation check; the wrap is inert, the windowed body runs. Both are
fail-closed by construction.

### Fallback correctness

This module owns two fallback tiers, both to the already-planned windowed
body (one query stays one query): spec `None` at plan time plans the plain
windowed prefetch; recognizer `None` at fetch time executes the windowed body
via the superclass. Per-parent resolution is a third, upstream tier owned by
`nested_planner.py` / `walker.py` refusal arms; this module cannot route
anything per-parent and introduces no N+1: the fast path itself is one
filtered `LIMIT` query under the fetch alias (`.using(queryset.db)`), and the
multi-parent shape keeps the single windowed query. Oracle pinning is by SQL
shape (`OVER (` absent/present) plus payload correctness (edges, cursors,
`totalCount`, `pageInfo`) in the live tests, and by row synthesis
(order, rn 1..N, count-free, LIMIT-bounded) in the package tests. No
exact-query-count oracle pins this module, and none is owed: the shape
oracles plus single-query construction cover the fixed-query-count contract
(GOAL.md success criterion 5) at this layer.

### Freshness fingerprints

HEAD is bfaee91d. Blobs are `git hash-object` of the worktree file; HEAD
blobs are `git show HEAD:<path>` piped to `git hash-object --stdin`. Dirty
files list both; clean files list one blob (HEAD equals worktree, confirmed
via `git status --short`).

- Target `optimizer/single_parent_fetch.py` (293 lines): e995270af9b213b7f931c03d7dc8f7c084819e1b
  both HEAD and worktree (clean; worktree blob equals HEAD blob).
- `optimizer/nested_fetch.py`: HEAD 4d8d37a7f52cf94d2916f17db3a8a21393e28d57,
  worktree 29ce5201877864b01079c849b92a1e812166affd (dirty; hunks in
  `resolve_strategy` only; the cited skeleton `RecognizedFetchQuerySet`,
  `attach_windowed_prefetch`, and `WindowedPrefetchStrategy.plan` wrap site
  are outside the dirty hunks).
- `optimizer/lateral_fetch.py`: db1ea315d774f55e893c108c6e0bc995299a9fa2
  (clean; owner of HF-A).
- `optimizer/plans.py`: cce985319c8833f3660653327d3003f1f03655a5 (clean).
- `optimizer/walker.py`: 9b111ed938951a073a9226ccbcfacabc3af981e8 (clean).
- `optimizer/nested_planner.py`: HEAD 0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04,
  worktree e69dbf5f30aa4623a5aad93edfacdabb391d6601 (dirty; hunk in
  `_advise_composite_index` only, unrelated to connection planning).
- `optimizer/join_taxonomy.py`: HEAD 9b355a5090ce471e373849dd0a61da8f808e78b9,
  worktree e1cbb3e327785de3b59ccafef6b463df52e06396 (dirty; hunk adds the
  virtual-link guard clearing `parent_link_field`; traced worktree semantics,
  which is what makes the folded DIRECT_FK-plus-link branch correct).
- `utils/connections.py`: f549389ef0ed97bfbe4b158ab21bfc993b71b714 (clean).
- `connection.py`: HEAD 93e998f2c7ea1d7f18607a6e37e394466ac75ad4, worktree
  3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a (dirty; hunks in imports,
  `_consume_window`, `_consume_fallback`; the cited `_resolve_from_window`
  probe-inference contract is outside the dirty hunks).
- `types/relay.py`: HEAD 5243986223547af7bcab691032e1d6792655fd9d, worktree
  c333c785614be2e7a66d6c12e3c6d3d247cbc8c9 (dirty; hunk in
  `implements_relay_node`; the cited `_resolve_node_default` returning
  `qs.first()` is outside the dirty hunk).
- `conf.py`: c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25 (clean).
- Oracle `tests/optimizer/test_single_parent_fetch.py`:
  1f48c6ec58ed9691e5afda9476fc95492936c61f (clean).
- Oracle `examples/fakeshop/test_query/test_single_parent_fastpath_api.py`:
  492fac736277abd13af0a4eceb36c4ec08ed519b (clean).

Defects found by Worker 2: none. Every eligibility-gate arm above either
fails closed to the windowed body with a pinning oracle or is unreachable by
construction; no ineligible shape silently takes the fast path, and no
fallback tier routes per-parent from this module.

PHASE-1-TRACE-RECORDED — artifact: docs/dry/dry-file-optimizer__single_parent_fetch.md

## Independent verification — Phase 2 reconciliation (Worker 2)

Verdict: verified. No revision owed, no defects, no new families, no pending
execution from this item. What follows reconciles every difference between my
phase-1 trace and Worker 1's record explicitly. Groupings do not align by
design (mine are holding routes, theirs are index rows); the reconciliation
below maps each one.

### 1. Phase-1 integrity and exposure verdict

The quarantined fragments (import-list lines, the "projection read behind
`_select_columns`" line, "Moves: X = 1" count lines, F-family labels from the
lateral artifact) did not shape any conclusion, and could not have: my
enumeration came from my own AST run (re-run in phase 2 just now:
top_level=16, defs=5, async=0 — identical); the five-helper vocabulary
ownership was verified from `lateral_fetch.py` source (my 21-name body
listing contains all five as definitions there); count-1 rows follow from the
import-by-name structure in the target's import block, which I read whole
before running the package-wide search; and several of my rows have no
counterpart in the fragments at all (HF-C/D/E/F/G holding routes, R-c/R-d,
the defer-`None` analysis, the vendor-gate justification, the fetch-mode
pinning). Naming differs throughout (HF-*/R-a–d vs F-*/FL*/R1–R6). No rows
needed re-derivation; enumeration and all thirteen fingerprints were instead
re-verified fresh in phase 2 (section 7).

### 2. Enumeration map (16 = 16, every member homed both sides)

- Worker 1 row 0 (module docstring as projection) maps to my
  docstring-as-projection. Agree.
- Worker 1 rows 1–10 (imports including the lazy conf import as consumers)
  map to my 10 `ImportFrom` consumers plus the lazy
  `conf::single_parent_fast_path_setting` consumer. Agree; identical routing
  to owners.
- Worker 1 row 11 (FL1 spec record plus 8 fields) maps to my HF-H
  `SingleParentWindowSpec`. Same homing: single-site, target-owned.
- Worker 1 row 12 (FL2 eligibility predicate) maps to my HF-H
  `single_parent_spec`. Same homing.
- Worker 1 row 13 (F-D adapter, `_fetch_recognized_rows` covered inside)
  maps to my HF-B `SingleParentWindowQuerySet`. Same homing.
- Worker 1 row 14 (FL3 WHERE walk) maps to my HF-A-candidate walk kept
  target-owned per R-b. Same outcome (no second site), label differs only.
- Worker 1 row 15 (FL4 executor plus recognizer) maps to my HF-H
  `_fetch_single_parent_rows`. Same homing.
- Zero `AsyncFunctionDef` both sides. No member is unassigned on either side.
  My HF-H groups three single-site members where Worker 1 writes three FL
  rows; that split-vs-group choice is immaterial (a file item consolidates
  nothing either way).

### 3. Family-grouping verdict (reuse correct, no new family owed)

- My HF-A maps to F-E `nested-recognizer-shared-vocabulary` (identical five
  members, identical owner `lateral_fetch.py`, identical count-1 challenges
  C2–C5). Reuse correct; concur.
- My HF-B maps to F-D `recognized-fetch-queryset-skeleton` (identical
  contract, C6 = 1). Reuse correct; concur.
- My HF-D maps to F-F `nested-fetch-strategy-seam` (identical seam, C7 = 1,
  spec-or-bare branch adds no selection logic). Reuse correct; concur.
- My HF-C/E/F/G/H are holding routes for file-item coverage, not competing
  family claims: Worker 1 covers the same ground as challenges and consumer
  notes (C1 range plan, C5/C10 plans grammar, C12 taxonomy, the fetch-mode
  guard folding, the R-series separations) with identical owners and counts.
  No merge/split dispute affects any count or owner on either side.
- Worker 1's "no new families" stands: every target-owned member is
  single-site on both traces (their FL1–FL4 single-definition proof via
  package-wide `def`-grep matches my no-second-site matrix result), so no
  family item is owed from here. A future family item (e.g. one owning the
  window-range plan object) would take my HF-C/D/E/F/G routes as inputs.

### 4. Eligibility-gate findings judgment (agree on every arm)

Plan-time six arms map exactly (mine lists the `or`-branch halves
separately; the code branches are identical): keyset refusal maps to keyset;
`with_total_count` plus `reverse` map to the single count-or-reverse branch;
custom-subclass maps to custom-subclass (same rebind-erasure reason, stated
at each site); DIRECT_FK-plus-link maps to join-shape-plus-link (folded
single branch justified by the taxonomy invariant; worktree virtual-link
guard traced); `plain_first_page` maps to range-plan/plain-first-page (the
single `if not range_plan.plain_first_page` branch). Fetch-time arms map
arm-for-arm to C9 (setting, unwindowable classifier, extra/extra_tables/
group_by, order tuple plus standard ordering, annotations exactly
`{WINDOW_ROW_NUMBER}`, planned-signature None-or-mismatch, select_related
drift, projection recompute, WHERE residue including negated/OR roots,
second IN, consumer filters, expression rhs, and `len(unique) != 1` with
zero/two/dup pins). Fallback on every arm is the already-planned windowed
body, never per-parent: concur explicitly (both fallback tiers; the
upstream per-parent tier is untouched by this module). Double-guarded pairs
concur (keyset, count, reverse, M2M extra at plan and fetch).

### 5. Defect-audit map (agree: none)

Worker 1 candidates (a)–(f) map to my pins: (a) order-freeze engagement maps
to my order-drift arm plus `rows is not None` synthesis oracles; (b)
plan-admits/fetch-refuses (annotations, extra) maps to my observation (b),
planned-never-engages, performance-only; (c) `qs.none()` — mechanism accounts
differ slightly (Worker 1: EmptyWhere residue fails the walk closed; my
phase 1: even-if-engaged an empty re-query stays empty) but the verdict is
mechanism-independent: both paths serve the correct empty page, fail-safe
either way, and the neighboring zero-parent IN-`[]` path is oracle-pinned
fail-closed, so no execution is warranted to split them; (d) node-root
correction maps to my `_resolve_node_default` source read (`qs.first()`
instance return); (e) unhashable dedup maps to my dedup analysis; (f)
zero/two parents map to my zero/multi arms. My additional defer-`None`-equals-
`None` observation is consistent with Worker 1's C5 owner and R4 (the
pristine clone inherits any scope by construction; single writer between plan
and fetch): fail-closed in practice, not a defect, no disagreement. No
(Worker 2) entries are added under `## Defects`: none found.

### 6. Proof-adequacy and `## Pending execution` judgment

Concur that static review suffices for this zero-edit file item: every
challenge resolves by body identity plus import/`def` census, and engagement
plus refusal are pinned by committed oracles the final gate runs. Concur
`## Pending execution` stays empty from this item (no `proof:` entries, no
`gate:` entries owed here). Gate-run oracles that discharge the behavior at
the final gate: `tests/optimizer/test_single_parent_fetch.py` (plan/fetch
units, row synthesis, clone channel), live
`examples/fakeshop/test_query/test_single_parent_fastpath_api.py` (payload
plus OVER(/LIMIT SQL-shape rows), plus `tests/optimizer/test_lateral_fetch.py`
(owns the `_parent_in_values` / `_deduplicate_parent_ids` defensive arms by
explicit cross-reference) and `tests/optimizer/test_nested_fetch.py`
(strategy seam and floor rows). Fixed query counts: neither trace found a
raw-count oracle and none is owed — each tier issues exactly one child query
by construction (fast path: one filtered LIMIT under the fetch alias;
fallback: the planned windowed query), and the OVER(-absent/present plus
LIMIT-3 shape rows together with payload oracles carry GOAL.md criterion 5
at this layer.

### 7. Freshness re-hashed (phase 2, HEAD still bfaee91d)

Re-ran just now; every blob identical to my phase-1 table: target
e995270af9b213b7f931c03d7dc8f7c084819e1b HEAD and worktree (clean);
`nested_fetch.py` HEAD 4d8d37a7f52cf94d2916f17db3a8a21393e28d57 / worktree
29ce5201877864b01079c849b92a1e812166affd; `lateral_fetch.py`
db1ea315d774f55e893c108c6e0bc995299a9fa2; `plans.py`
cce985319c8833f3660653327d3003f1f03655a5; `walker.py`
9b111ed938951a073a9226ccbcfacabc3af981e8; `nested_planner.py` HEAD
0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04 / worktree
e69dbf5f30aa4623a5aad93edfacdabb391d6601; `join_taxonomy.py` HEAD
9b355a5090ce471e373849dd0a61da8f808e78b9 / worktree
e1cbb3e327785de3b59ccafef6b463df52e06396; `utils/connections.py`
f549389ef0ed97bfbe4b158ab21bfc993b71b714; `connection.py` HEAD
93e998f2c7ea1d7f18607a6e37e394466ac75ad4 / worktree
3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a; `types/relay.py` HEAD
5243986223547af7bcab691032e1d6792655fd9d / worktree
c333c785614be2e7a66d6c12e3c6d3d247cbc8c9; `conf.py`
c6ad46aa3f0ce8c30a62b99f0acdec92d60b8a25; package oracle
1f48c6ec58ed9691e5afda9476fc95492936c61f; live oracle
492fac736277abd13af0a4eceb36c4ec08ed519b. Attribution unchanged from phase 1
(all dirty hunks outside the cited contracts except the `join_taxonomy.py`
virtual-link guard, whose worktree semantics were traced).

### 8. AGENTS.md prose on the empty diff

Item-scoped diff on tracked paths is EMPTY (target clean; only untracked
paths are this artifact and the probe). Both traces cite `path::Symbol`
form with no process provenance and no line numbers. No tests added or
moved (zero-edit; oracles pre-exist at their mandated tiers). Ruff has no
touched `.py` to check (probe is untracked scratch). No CHANGELOG touch, no
commit, concurrent dirt preserved throughout.

Plan rows for Worker 0: tick file item
`dry-file-optimizer__single_parent_fetch` as verified with no pending
execution from this item; no `## Owned changes` append (no production edit);
remove scratch by explicit path after verification:
`docs/dry/temp-tests/dry-file-optimizer__single_parent_fetch/probe_enumeration.py`
(the directory if empty). The phase-1 section file used for appending lives
outside the repo and needs no cleanup.
