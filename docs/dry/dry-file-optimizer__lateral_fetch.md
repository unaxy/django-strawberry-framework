# DRY review: `optimizer/lateral_fetch.py`

Status: verified
Run: 0.0.15 2026-09-19-1
Target: `django_strawberry_framework/optimizer/lateral_fetch.py` (1181 lines)
Blob: `db1ea315d774f55e893c108c6e0bc995299a9fa2` (worktree == HEAD ==
ITEM_BASELINE `6ef1a75f`; zero diff on all three; target worktree-clean)
Item baseline: `6ef1a75fefb7c57ef968f9b7b86835990a9c3b53`
Ledger check: `## Owned changes` in [dry-0_0_15][dry-plan] names exactly one
optimizer-area row (walker D1 seal-policy); no row touches this item's
paths. Confirmed before reading the target.

## System trace

The target owns the Postgres `CROSS JOIN LATERAL` nested-connection fetch
backend: one plan-time spec record (`LateralWindowSpec`), one pure SQL
renderer (`build_lateral_sql`), one fetch-time fail-closed recognizer
(`_recognize_lateral_fetch` + `window_predicate_signature`), one
`RecognizedFetchQuerySet` subclass (`LateralQuerySet`), and one strategy
(`LateralPrefetchStrategy` / `LATERAL_STRATEGY`). Its correctness contract is
degradation, not SQL: every unrecognized shape executes the identical windowed
ORM body the default strategy would have planned (via
`attach_windowed_prefetch` with a rebind wrap).

Sites read (roles: definition / consumer / oracle / projection):

- Definitions consumed (not owned here): `nested_fetch.py::RecognizedFetchQuerySet`
  (+ `::rebind` lazy-importing `window_predicate_signature`),
  `nested_fetch.py::NestedConnectionRequest.__post_init__`,
  `nested_fetch.py::attach_windowed_prefetch`,
  `nested_fetch.py::WINDOWED_STRATEGY / ::resolve_strategy / ::AUTO_STRATEGY`,
  `plans.py::apply_window_pagination` (ORM dialect),
  `plans.py::deferred_loading_of`, `plans.py::order_entry_name_and_direction`,
  `plans.py::WINDOW_ROW_NUMBER / ::WINDOW_TOTAL_COUNT / ::WINDOW_ROW_NUMBER_REVERSED`,
  `utils/connections.py::window_range_plan / ::WindowRangePlan`,
  `utils/connections.py::assert_window_fetch_mode_for`,
  `join_taxonomy.py::classify_relation_join / ::LateralJoinShape /
  ::RelationJoinDescriptor`, `keyset.py::keyset_seek_sql`,
  `keyset.py::build_keyset_seek_plan / ::KeysetSeekPlan`,
  `nested_fetch.py::unwindowable_child_queryset_reason`.
- Consumers of this file's definitions: `single_parent_fetch.py` (imports
  `_deduplicate_parent_ids`, `_is_window_qual`, `_parent_in_values`,
  `_select_columns`, `window_predicate_signature`; docstring cites
  `_recognize_lateral_fetch` as the structural twin);
  `nested_fetch.py::RecognizedFetchQuerySet.rebind` (lazy
  `window_predicate_signature`).
- Oracles: `tests/optimizer/test_lateral_fetch.py` (1494 lines, 69 tests,
  blob `67431054…`): spec-building, visibility WHERE, pure builder, queryset
  plumbing, parent-id extraction, signature boundary, scripted-cursor
  execution, windowed fallback; `tests/optimizer/test_nested_fetch.py`
  strategy-resolution rows; `tests/optimizer/test_walker.py` lateral-plan
  rows; `tests/test_lateral_pg_parity.py` + `tests/test_predicate_pg_explain.py`
  (Postgres tier only); `tests/optimizer/test_single_parent_fetch.py`
  (counterpart contract).
- Projections: module docstring (owns the degradation + SQL-namespace +
  injection-surface statements); `docs/README.md` strategy section;
  `docs/GLOSSARY.md` nested-fetch-strategy entry; archived
  `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (strategy seam) and
  `docs/SPECS/spec-053-boundary_dry_squeeze-0_0_15.md` (ORM-vs-lateral
  renderer pair). Prior-cycle records used as trigger checks only:
  concurrent untracked `docs/dry/dry-file-keyset.md` (keyset twins),
  `docs/bug_hunt/bug_hunt-0_0_15.md` lateral hunt note (25 matrices, PG
  execution explicitly unverified).

Sibling dirt (read-only; never edited): `optimizer/hints.py` (worktree
`8064af14…` vs HEAD `da46ef89…`), `optimizer/join_taxonomy.py` (worktree
`e1cbb3e3…` vs HEAD `9b355a50…`, +39 composite-pk feature),
`optimizer/nested_fetch.py` (worktree `29ce5201…` vs HEAD `4d8d37a7…`),
`optimizer/nested_planner.py` (worktree `e69dbf5f…` vs HEAD `0ad8ff5d…`).
Mechanism sites below cite which bytes were read: `nested_fetch.py`
`attach_windowed_prefetch` / `resolve_strategy` / `RecognizedFetchQuerySet`
/ `NestedConnectionRequest` bodies were read at WORKTREE bytes
(`29ce5201…`); `single_parent_fetch.py` was read at `e995270a…` (clean,
== HEAD); `plans.py` at `cce98531…`, `keyset.py` at `df4b5e2f…`,
`utils/connections.py` at `f549389e…` (all clean, == HEAD);
`join_taxonomy.py` only grepped at worktree bytes (`e1cbb3e3…`) for link-field
ownership statements.

## Verification

### Matrix

1. Cross-flavor policy mirroring: no flavor twin. The target is
   optimizer-internal; the one shared vocabulary it touches is the strategy
   seam (`StrategySelection`, `resolve_strategy`, `NestedConnectionStrategy`),
   owned by `nested_fetch.py` (read at worktree bytes). No
   types/filters/orders/mutations/forms/DRF mirror exists to compare.
   Searched package for second `CROSS JOIN LATERAL` emitters: none outside
   this file's builder + tests.
2. Sync/async twins: none in-file (AST probe asserts zero
   `AsyncFunctionDef`; word grep finds no `async`/`await`/`sync_to_async`
   in-file). Execution is sync-only by construction (`_fetch_all` override,
   blocking `connection.cursor()`, `Model.from_db` + `setattr`
   instantiation). Async callers reach it through the shared sync boundary
   (family `one-sync-boundary`, owned at `utils/querysets.py`); no async twin
   is owed. Single-parent counterpart is likewise sync-only.
3. Derived rather than repeated knowledge: all derivations compose by name
   from their owners — order via `plans.py::order_entry_name_and_direction`
   (`_order_columns`), projection via `plans.py::deferred_loading_of`
   (`_select_columns`), range decisions via
   `utils/connections.py::window_range_plan` (`build_lateral_sql`),
   fetch-mode guard via `utils/connections.py::assert_window_fetch_mode_for`
   (both `__post_init__`s), join links via the request's
   `join_taxonomy.py::RelationJoinDescriptor` (`_build_lateral_spec` reads,
   never re-derives). No inline re-derivation found.
4. Inverse / round-trip pairs: (a) `build_lateral_sql` (render) /
   `_recognize_lateral_fetch` + `window_predicate_signature` (verify) — one
   `WindowRangePlan` grammar, ORM `Q` dialect at `plans.py` vs raw-SQL
   dialect here; (b) `keyset.py::keyset_seek_q` (ORM) /
   `keyset.py::keyset_seek_sql` (SQL) with lateral adapter
   (`_keyset_seek_sql`) + structural verifier (`_keyset_seek_quals_match`);
   (c) `_instantiate_row` + `_apply_lateral_converters` reproduce the
   windowed `.only()` / converter-chain row shape (consumer of
   `Model.from_db`, not a second definition). Each pair is inventoried in
   `### Challenges`.
5. Contracts restated in another medium: every production rule below lists
   its oracles (package tests, 69 in-file) and projections (module
   docstring, README, GLOSSARY, archived spec-033/spec-053). PG-tier oracles
   (`test_lateral_pg_parity.py`) are cited, not counted. No rule requires a
   doc/test move: nothing is edited in this file item.
6. Enforcement by omission: `_build_lateral_spec` downgrade arms enumerated
   (C8 challenges); each arm's sibling coverage checked against
   `single_parent_fetch.py::single_parent_spec` eligibility and the planner's
   strategy-independent refusal arms (`nested_fetch.py` worktree bytes +
   `unwindowable_child_queryset_reason`). Divergences (THROUGH_TABLE,
   visibility WHERE, counted keyset, select_related) are intentional
   contract separations, recorded with triggers in the findings.

### Enumeration

Instrument: `ast.Module.body` walk (no imports of the target; Django
settings never touched). 44 top-level statements: 13 imports (consumers,
not rules), 21 def/class members, 9 module assigns, 1 `__future__` import
counted among the 13. Probe:
`docs/dry/temp-tests/dry-file-optimizer__lateral_fetch/probe_enumeration.py`
— `OK blob=db1ea315… top_level=44 defs=21 assigns=9`.

Every rule-bearing member (21 defs + 9 assigns) lands in exactly one home.
`LateralWindowSpec.__post_init__`, `LateralQuerySet._fetch_recognized_rows`,
`LateralPrefetchStrategy.plan`, and `build_lateral_sql::order_sql` are covered
inside their owner's row.

| # | Member | Home |
|---|---|---|
| 1 | `LATERAL_SQL_STEM` + 5 derived aliases | FL1 file-local |
| 2 | `_ARRAY_BINDABLE_PARENT_FIELD_TYPES` | FL2 file-local |
| 3 | `_WINDOW_ANNOTATIONS` | F-A (consumer) |
| 4 | `LateralWindowSpec` (+ `__post_init__`) | FL3 record; `__post_init__` enforces F-C |
| 5 | `build_lateral_sql` | F-A `window-range-dual-render` (SQL renderer half) |
| 6 | `_keyset_seek_sql` | F-B `keyset-seek-dual-dialect` (lateral adapter half) |
| 7 | `LateralQuerySet` | F-D `recognized-fetch-queryset-skeleton` (subclass adapter) |
| 8 | `_RecognizedLateralFetch` | FL4 file-local (lateral-only carry record) |
| 9 | `_fetch_lateral_rows` | FL5 file-local (lateral-only executor) |
| 10 | `_deduplicate_parent_ids` | F-E `nested-recognizer-shared-vocabulary` (owner) |
| 11 | `_apply_lateral_converters` | FL6 file-local (lateral-only converter pass) |
| 12 | `_recognize_lateral_fetch` | FL7 file-local (lateral-only recognizer body) |
| 13 | `_is_window_qual` | F-E (owner; structural classifier half) |
| 14 | `_normalize_window_node` | FL8 file-local (signature-only helper) |
| 15 | `window_predicate_signature` | F-E (owner; shared safety boundary) |
| 16 | `_keyset_seek_quals_match` | F-B (lateral verifier half) |
| 17 | `_visibility_quals_match` | FL9 file-local (DIRECT_FK-only recognizer) |
| 18 | `_parent_in_values` | F-E (owner) |
| 19 | `_instantiate_row` | FL10 file-local (lateral-only row builder) |
| 20 | `LateralPrefetchStrategy` | F-F `nested-fetch-strategy-seam` (member backend) |
| 21 | `LATERAL_STRATEGY` | F-F (member singleton) |
| 22 | `_plain_single_table_where` | FL11 file-local (v1 admission test) |
| 23 | `_build_lateral_spec` | FL12 file-local (plan gate; arms in C8) |
| 24 | `_order_columns` | FL13 file-local (derives via plans owner) |
| 25 | `_select_columns` | F-E (owner; also derives via plans owner) |

Single-definition proof: package-wide `def`-grep for every row-10..25
helper name returns exactly one definition (the `_fetch_single_parent_rows`
hit is the distinct single-parent counterpart, not a duplicate); the FL-row
private names return hits in this file only. Consumers import by name
(`single_parent_fetch.py` five imports; `nested_fetch.py::rebind` one lazy
import) — enforcement sites, never second definitions.

### Challenges

Change challenges posit a plausible rule change and count AUTHORITATIVE
definitions that must move (consumers / oracles / projections listed, not
counted). All static-reviewed against the blob above; no behavior execution
owed (zero-edit file item; every challenge resolves by body identity).

- C1 (F-A): render `offset` pages with an inclusive floor instead of
  exclusive (`rn > %s` → `rn >= %s`). Moves: `utils/connections.py`
  (`lower_bound` decision + `apply_window_pagination` ORM Q-render) = 1
  owner; lateral SQL text follows via `window_range_plan`. Count: 1.
  Oracles: `test_lateral_fetch.py` range-shape rows + `test_plans.py`.
- C2 (F-A): add a fourth window annotation (e.g. abs row number).
  Moves: `plans.py` constant + both renderers + both recognizers' allow
  lists = the vocabulary owner plus mechanical followers; the lateral
  allow-list `_WINDOW_ANNOTATIONS` is a consumer set, counted under the
  same single grammar. Count: 1 grammar.
- C3 (F-B): change the keyset seek shape (drop the redundant leading
  bound). Moves: `keyset.py::build_keyset_seek_plan` + both dialect
  renderers + lateral verifier = 1 plan owner with dialect followers.
  Count: 1. (Verifier/divergence coupling recorded at F-B, not a second
  definition.)
- C4 (F-C): allow probe + count together. Moves:
  `utils/connections.py::assert_window_fetch_mode_for` = 1; both
  `__post_init__`s follow. Count: 1.
- C5 (F-D): change the clone-surviving contract (e.g. a second per-strategy
  slot). Moves: `nested_fetch.py::RecognizedFetchQuerySet` (`_clone` +
  `rebind` + `_fetch_all`) = 1; both subclasses follow. Count: 1.
- C6 (F-E): change the signature grammar (e.g. fold `lookup_name` out).
  Moves: `window_predicate_signature` + `_normalize_window_node` = 1 owner
  body; both recognizers follow. Count: 1. Consumers
  (`single_parent_fetch.py`, `nested_fetch.py::rebind`) listed, not
  counted.
- C7 (F-F): add a fourth built-in strategy name. Moves:
  `nested_fetch.py::resolve_strategy` registry + `StrategySelection`
  annotation chain = 1; `LateralPrefetchStrategy` untouched. Count: 1.
- C8 (FL12 arms): each `_build_lateral_spec` downgrade arm challenged for
  a missing sibling (axis 6): custom-QS-subclass (single-parent same arm —
  parallel, separate contracts); select_related/annotations/extra/group_by
  (single-parent checks a subset: `extra`, `group_by`, order, annotations
  `{WINDOW_ROW_NUMBER}` + select_related/projection freeze — stricter in
  some axes, looser in others; each proves its own re-query, no shared
  gate to merge); THROUGH_TABLE admitted here, refused by single-parent
  (correction-2 exclusion: M2M `extra(select=…)` irreproducible from a
  pristine clone — intentional separation, trigger: pristine-clone
  prefetch-attr reproduction); visibility WHERE admitted here (DIRECT_FK
  non-keyset only), absent in single-parent (its re-query inherits the
  pristine WHERE instead of recompiling — separation, trigger: a second
  fetch path needing raw-SQL splicing); counted keyset refused here
  (whole-partition scan buys nothing raw), refused by single-parent
  (no count synthesis) — same verdict, separate reasons; composite-pk /
  `defer()` / expression-order arms are lateral-expressibility limits with
  no counterpart. No arm owes a guard elsewhere: every refusal degrades to
  the planned windowed body inside `plan`.
- C9 (FL1/FL2): rename the SQL stem / reclassify one field type's
  bindability. Moves: 1 constant each; grep-proved single-site. Count: 1.
- C10 (FL4/FL5/FL6/FL7/FL9/FL10/FL11/FL13 + record FL3/FL8): add a lateral
  execution step (e.g. a second converter chain). Moves: this file only;
  package `def`-grep + consumer-import census show no second site.
  Count: 1 each.
- C11 (sync/async): move lateral execution off the requesting thread.
  No async twin exists to move; the await boundary lives at the shared
  sync-boundary owner (family `one-sync-boundary`). Inapplicable by
  construction: raw cursor + `from_db` instantiation must run in a sync
  context; recorded, not counted.

## Findings

Worker 0 note: families F-A..F-F are NAMED here for the plan's
`## Responsibility index`; no plan edit made from this item. Suggested
owners/holding items follow principle 7 (narrowest importable owner).
No consolidation in a file item — every family below is already-single or
already-shared by construction; the family item decides gates.

### F-A `window-range-dual-render` (new family; owner `utils/connections.py::window_range_plan`)

Contract: one `WindowRangePlan` decision set (`lower_bound`,
`fetch_upper_bound`/`fetch_limit`, `add_marker_rows`, `plain_first_page`,
`reverse`) rendered twice — ORM `Q` objects by
`plans.py::apply_window_pagination`, raw SQL by `build_lateral_sql`
(in-branch `ORDER BY … LIMIT` for `plain_first_page`, outer
`rn`-filter + `OR rn = 1` marker otherwise). Variation axes: slice
(`offset`, `limit`, `reverse`, `next_page_probe`, `with_total_count`).
Sites: definition `utils/connections.py::window_range_plan`;
renderers `plans.py::apply_window_pagination` + `lateral_fetch.py::
build_lateral_sql` (this file); verifiers `_recognize_lateral_fetch` +
`window_predicate_signature` (this file); vocabulary owners
`plans.py::WINDOW_*` consumed via `_WINDOW_ANNOTATIONS` (this file);
oracles `test_lateral_fetch.py` range rows + `test_plans.py`;
projections module docstring + archived spec-053 pair note.
Challenges: C1, C2 (count 1 grammar). Already-consolidated shape: the
shared plan object exists; renderers compose it by name. Suggested holding:
family item (or the unticked `utils/connections.py` file item if the
family never opens).

### F-B `keyset-seek-dual-dialect` (new family; owner `keyset.py::build_keyset_seek_plan`)

Contract: one `KeysetSeekPlan` (direction bits via `keyset_seek_greater`,
arity checks) rendered as ORM `Q` (`keyset_seek_q`) and SQL
(`keyset_seek_sql`), with lateral halves: value-preparing adapter
(`_keyset_seek_sql`, arity/order pinned to `spec.order_columns` by
`_build_lateral_spec`) and fetch-time structural verifier
(`_keyset_seek_quals_match`, exact 2-child squash shape + per-arm
lookup/column/table/value checks). Sites: definition `keyset.py`;
adapter + verifier this file; oracles `test_lateral_fetch.py` keyset rows
+ keyset-tier tests; projections `keyset.py` module prose. Challenges: C3
(count 1). Rejected sub-candidate: merging the verifier into the plan
owner — verifier proves FETCH-time tree identity (mutation detection),
the owner proves PLAN-time shape; different responsibilities, trigger: a
seek representation both sides could import without losing the
time-of-check distinction. Coordination note: concurrent untracked
`docs/dry/dry-file-keyset.md` traces the owner halves; Worker 0
adjudicates the family name against it.

### F-C `window-fetch-mode-guard` (new family; owner
`utils/connections.py::assert_window_fetch_mode_for`)

Contract: probe/count mutual exclusion (`next_page_probe` only with
`with_total_count=False`) enforced at construction. Sites: definition
`utils/connections.py`; enforcement `NestedConnectionRequest.__post_init__`
(`nested_fetch.py`, worktree bytes) + `LateralWindowSpec.__post_init__`
(this file); oracle keyset/count-mode tests (named, not counted).
Challenges: C4 (count 1). Already-single; no gate owed beyond the assert
itself (fail-loud at construction, not a bypassable branch).

### F-D `recognized-fetch-queryset-skeleton` (new family; owner
`nested_fetch.py::RecognizedFetchQuerySet`)

Contract: clone-surviving spec slot + planned-window signature capture at
`rebind` + recognized-rows-or-windowed-body `_fetch_all`. Sites:
definition/skeleton `nested_fetch.py` (worktree bytes); adapters
`LateralQuerySet` (this file: `_dst_lateral_spec` slot +
`_fetch_recognized_rows` → `_fetch_lateral_rows`) and
`SingleParentWindowQuerySet` (`single_parent_fetch.py`); oracles
plumbing rows in both test files. Challenges: C5 (count 1).
Sub-behaviors stay separate: the two recognizers prove different queries
(lateral SQL vs pristine `LIMIT` re-query) — sharing stops at the
skeleton by design (principle 5: shared lifecycle, kept adapters).

### F-E `nested-recognizer-shared-vocabulary` (new family; owner this file)

Contract: the window-identity helpers every nested-fetch recognizer
composes by name — `window_predicate_signature` (order-independent,
multiplicity-preserving, `None`-on-unreadable), `_is_window_qual`
(structural classifier only, explicitly NOT sufficiency),
`_parent_in_values` (column+table matched, expression-free `__in`),
`_select_columns` (only/defer projection via the plans owner),
`_deduplicate_parent_ids` (hashable fast path, unhashable fallback, NULL
drop). Sites: definitions this file; consumers
`single_parent_fetch.py` (5 imports) + `nested_fetch.py::rebind` (lazy
signature import); oracles signature/parent-id rows in both test files;
projections the helpers' own docstrings (each states its insufficiency /
twin relation). Challenges: C6, C10-partial (count 1). Already-single;
single-parent's `_single_parent_where_ids` + `_fetch_single_parent_rows`
are the twin recognizer body, not a second definition of any member.

### F-F `nested-fetch-strategy-seam` (new family; owner `nested_fetch.py`)

Contract: strategy selection + planning floor — `NestedConnectionStrategy`
protocol, `StrategySelection`, `resolve_strategy` (hostile-hardened name
match), `attach_windowed_prefetch` (shared windowed floor),
`WINDOWED_STRATEGY` / `LATERAL_STRATEGY` / `AUTO_STRATEGY` singletons.
Sites: definitions `nested_fetch.py` (worktree bytes) + member backend
`LateralPrefetchStrategy` (this file: spec-or-downgrade `plan`, always
ending in the shared floor) + member singleton `LATERAL_STRATEGY`;
oracles strategy-resolution rows (`test_nested_fetch.py`,
`test_walker.py`); projections README/GLOSSARY strategy entries.
Challenges: C7 (count 1). No second seam exists; lateral `plan` adds no
selection logic (delegates `resolve_strategy` callers untouched).

### FL1–FL13 file-local rows (this file only; challenge in `### Challenges`)

Each carries the single-site proof (package `def`-grep exactly-one +
consumer census) and the change that would reopen it (a second importing
site or a sibling re-derivation):

- FL1 lateral SQL namespace (`LATERAL_SQL_STEM` + 5 derived aliases;
  C9; reopen: a second SQL emitter quoting the same aliases).
- FL2 array-bindability table (`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`; C9;
  reopen: a second adapter making the same scalar/structured cut).
- FL3 `LateralWindowSpec` record incl. counted-keyset + visibility
  field prose (C10; reopen: a second spec carrying the same plan).
- FL4 `_RecognizedLateralFetch` approved-bytes carry record (C10).
- FL5 `_fetch_lateral_rows` executor incl. vendor gate, dedup-before-bind,
  approved-`visibility_where_sql` reuse, param/SQL positional alignment
  (audited: parent ids → seek → visibility → range bounds match placeholder
  order; C10).
- FL6 `_apply_lateral_converters` (C10).
- FL7 `_recognize_lateral_fetch` body (C8-adjacent; the WHERE-walk
  structure mirrors — not duplicates — `_single_parent_where_ids`, which
  proves a different query with different arms).
- FL8 `_normalize_window_node` (C6-helper; used by the signature only).
- FL9 `_visibility_quals_match` byte-equal DIRECT_FK recognizer returning
  the approved pair (C10; single-parent has no visibility arm by design).
- FL10 `_instantiate_row` (`from_db` + window-attr + M2M prefetch-alias
  stamping; C10).
- FL11 `_plain_single_table_where` v1 admission test (C8; reopen: a second
  raw-SQL splicer needing the same gate).
- FL12 `_build_lateral_spec` plan gate with its 10+ downgrade arms (C8;
  each arm's sibling coverage adjudicated; omissions intentional per
  recorded triggers).
- FL13 `_order_columns` (derives via `plans.py` owner; single-parent pins
  `tuple(request.order_by)` directly instead — parallel freeze, separate
  needs).

### Rejections

- R1 (ORM `Q` vs SQL text): considered merging `apply_window_pagination`
  and `build_lateral_sql` range sections; rejected — both already render
  one shared plan object (F-A consolidated). Trigger: a range decision
  expressible in one dialect but not the other.
- R2 (`LateralQuerySet` vs `SingleParentWindowQuerySet`): considered one
  recognizer queryset; rejected — specs, recognizers, and row sources
  differ; sharing stops at the F-D skeleton. Trigger: a third backend
  needing a different clone contract.
- R3 (verifier into keyset owner): rejected at F-B with trigger.
- R4 (three plan-gate arm sets into one): lateral `_build_lateral_spec`
  vs single-parent eligibility vs planner strategy-independent refusals —
  rejected, three contracts (raw-SQL expressibility / pristine-re-query
  reproducibility / strategy-independent safety), triggers per arm in C8.
- R5 (async twin): no twin exists; sync-only recorded (matrix axis 2),
  never a gap.

## Defects

None. Audited while tracing (all static-reviewed against blob
`db1ea315…`): SQL/param positional alignment in `build_lateral_sql`
(parent relation → seek → visibility → range) matches; signature keeps
multiplicity (`tuple(sorted(…))` on a list) and `lookup_name` rides each
leaf (no `gt`/`lte` confusion); `planned_signature is None` fails closed
on both recognizers; `_parent_in_values` requires expression-free
list/tuple rhs; `_visibility_quals_match` splices the recognizer-approved
pair, never a recompile; `_build_lateral_spec` docstring arm summary is
completed by the `LateralWindowSpec` keyset/visibility prose + body
comments (summary, not contradiction — no defect bar met).

## Pending execution

None. Zero-edit file item; every proof above is `static-reviewed`
(body-identity, single-`def` census, import census). The one mechanical
probe (`probe_enumeration.py`: AST counts + blob pin + no-async assert)
ran read-only: `uv run python
docs/dry/temp-tests/dry-file-optimizer__lateral_fetch/probe_enumeration.py`
→ `OK blob=db1ea315… top_level=44 defs=21 assigns=9`. No shared-tree
pytest run (not authorized by the entry command; inspection beats
execution on every challenge).

## Judgment

File item discharged with zero edits: 30 rule-bearing members assigned
(6 families named for Worker 0: F-A `window-range-dual-render`, F-B
`keyset-seek-dual-dialect`, F-C `window-fetch-mode-guard`, F-D
`recognized-fetch-queryset-skeleton`, F-E
`nested-recognizer-shared-vocabulary`, F-F `nested-fetch-strategy-seam`;
13 file-local rows FL1–FL13; 5 rejections with triggers), matrix
discharged on all six axes, challenges counted (every count 1 or
inapplicable-by-construction). The file composes its owners by name
throughout; the only multi-site definitions it owns (F-E vocabulary) are
already-single with named consumers. No consolidation owed here by design.

<!-- MARK2 -->

## Independent verification (Worker 2)

Phase 1 independent trace. Target read whole (1181 lines, worktree-clean,
confirmed below). No production edit owed or made: file-item verdict scope is
coverage + assignment; candidates route to holding families named here with my
own naming (F-A..F-I, FL1.., R-1..). I did not read any other section of this
artifact. One contamination note: a package-wide docs grep I ran matched this
artifact file and printed a fragment of Worker 1's rows. I did not open the
file, did not run further searches inside `docs/dry/`, and did not use the
fragment: the families, names, and counts below are my own trace. Phase 2 can
judge whether the exposure matters.

### Enumeration

Instrument: every name in `ast.Module.body` of
`django_strawberry_framework/optimizer/lateral_fetch.py`. Count: 44 members
(indices 0-43: 1 docstring Expr, 13 Import/ImportFrom, 9 module assigns
including `LATERAL_STRATEGY`, 4 ClassDef, 17 FunctionDef, 0 AsyncFunctionDef).

Preamble (indices 0-13) are consumers/projections, not definitions: the
docstring plus imports that compose by name from `keyset.py`,
`utils/connections.py`, `join_taxonomy.py`, `nested_fetch.py`, `plans.py`.
Every other member lands below; no member is unassigned.

| # | Member | Home (my naming) |
|---|--------|------------------|
| 14-19 | `LATERAL_SQL_STEM`, `LATERAL_PARENT_ALIAS`, `LATERAL_PARENT_COLUMN`, `LATERAL_WINDOW_ALIAS`, `LATERAL_CHILD_ALIAS`, `LATERAL_THROUGH_ALIAS` | FL1 file-local SQL namespace (stem owned once, five derived by f-string; single edit) |
| 20 | `_ARRAY_BINDABLE_PARENT_FIELD_TYPES` | FL2 file-local bindability table |
| 21 | `_WINDOW_ANNOTATIONS` | consumer of F-A vocabulary (references plans constants by name; follows renames by construction) |
| 22 | `LateralWindowSpec` (+ `__post_init__`) | record in F-C (guard consumer) / F-I (visibility slot carrier) |
| 23 | `build_lateral_sql` | F-A SQL-renderer half |
| 24 | `_keyset_seek_sql` | F-B lateral adapter (consumer of shared plan + SQL renderer) |
| 25 | `LateralQuerySet` | F-D adapter |
| 26 | `_RecognizedLateralFetch` | FL4 lateral-only carry record |
| 27 | `_fetch_lateral_rows` | FL5 lateral-only executor |
| 28 | `_deduplicate_parent_ids` | FL6 owner here; `single_parent_fetch.py` imports it (consumer, named in its comment) |
| 29 | `_apply_lateral_converters` | FL7 lateral-only converter pass |
| 30 | `_recognize_lateral_fetch` | F-E consumer (recognizer body) |
| 31 | `_is_window_qual` | F-E structural classifier (shared by both recognizers) |
| 32 | `_normalize_window_node` | F-E normalizer |
| 33 | `window_predicate_signature` | F-E owner (capture + compare contract) |
| 34 | `_keyset_seek_quals_match` | F-B lateral verifier half |
| 35 | `_visibility_quals_match` | F-I recognition half |
| 36 | `_parent_in_values` | FL8 owner here; `single_parent_fetch.py` imports it (consumer) |
| 37 | `_instantiate_row` | FL9 lateral-only row builder (R-2 for the Django-iterable resemblance) |
| 38 | `LateralPrefetchStrategy` (+ `plan`) | F-F member (lateral backend) |
| 39 | `LATERAL_STRATEGY` | F-F singleton |
| 40 | `_plain_single_table_where` | F-I admission half |
| 41 | `_build_lateral_spec` | FL10 plan gate (downgrade arms enumerated under axis 6) |
| 42 | `_order_columns` | F-H reader (of `order_entry_name_and_direction`) |
| 43 | `_select_columns` | F-H reader (of `deferred_loading_of`) |

Holding families (my names): F-A `window-range-dual-render`, F-B
`keyset-seek-dual-dialect`, F-C `fetch-mode-guard`, F-D
`recognized-queryset-skeleton`, F-E `window-signature-verify`, F-F
`strategy-seam`, F-G `join-vocabulary`, F-H `order-projection-vocabulary`,
F-I `visibility-scope-carry`.

Rejections (my names, contract difference + trigger):
R-1 reversal rendering: `plans.py::_reverse_order_by` (flips direction AND
swaps NULLS positioning, raises loudly on unreversible terms) vs
`build_lateral_sql::order_sql(descending_flip=...)` (direction-only flip;
expression/explicit-NULLS orders downgrade out at `_order_columns`). Posit
"swap NULLS placement on reversal": count 1 (plans only). Trigger that would
unite them: lateral accepts expression/explicit-NULLS orders.
R-2 row materialization: `_instantiate_row` + `_apply_lateral_converters`
resemble Django's `ModelIterable`, but Django is framework population
(out of scope for the package-source population); no package-owned second
definition exists. Trigger: a package-owned second model-materializer.
R-3 parent binding shape: `unnest(array)` vs `VALUES` rows are two branches of
one function on one field-type predicate, not two definitions. Trigger: a
second parent-binding site.

### Matrix (each axis discharged with the search run)

1. Cross-flavor mirroring. Searched package for second `CROSS JOIN LATERAL`
emitters: only this module (SQL lines for branch + outer join) plus prose
references in `nested_fetch.py`, `connection.py`, docs. Searched
`ROW_NUMBER()` / `COUNT(1) OVER` / `_dst_row_number` emitters: `plans.py`
(ORM window, F-A other half), this module (SQL mirror), prose-only mentions
in `orders/sets.py` (checked lines 685-714: docstring stating to-many
aggregate orders never sit below the window; no implementation),
`connection.py` (consumer), `selections.py` (observers), `conf.py` (comment).
No sibling-flavor (types/filters/orders/mutations/forms/rest) duplicates a
lateral rule; the target's surface is optimizer-internal. Verdict: discharged,
no second owner.
2. Sync/async twins. Grep for `async def|await|sync_to_async` across
`optimizer/`: exactly one hit, `extension.py::_async_optimize`, which awaits
the result then calls the same sync `_optimize`. No async twin of
`build_lateral_sql`, `_fetch_all`, or the recognizer exists; fetch executes
through sync `cursor.execute` inside sync `_fetch_all`. The backend split is
Postgres-vs-else vendor gate (`connection.vendor != "postgresql"`, line 503),
not sync/async; pure-builder tests inject `quote_name` so they run on SQLite
by construction. `connection.py` / `nested_planner.py` dirt does not add an
async path (diffstat 65+9 lines, concurrent, content read at worktree blob).
Verdict: axis inapplicable with reason; no twin to count.
3. Derived knowledge. Verified each derivation is composed once by name:
SQL aliases from `LATERAL_SQL_STEM` (FL1); projection via shared
`plans.py::deferred_loading_of`; order parse via shared
`plans.py::order_entry_name_and_direction`; join facts read (never re-walked)
from `join_taxonomy.py::classify_relation_join` (F-G); seek structure from
`keyset.py::KeysetSeekPlan` via `build_keyset_seek_plan`; parent values via
`Field.get_db_prep_value`; converters via `connection.ops.get_db_converters`
+ expression converters; instances via `Model.from_db`. No fact is
reconstructed by a second means. Verdict: discharged, count 1 each.
4. Round-trip pairs. (a) `build_lateral_sql` (render) /
`_recognize_lateral_fetch` + `window_predicate_signature` (verify): one
grammar, render half + prove half (F-A/F-E). (b) `keyset.py::keyset_seek_q`
(ORM) / `keyset.py::keyset_seek_sql` (SQL) sharing `build_keyset_seek_plan`,
plus lateral adapter `_keyset_seek_sql` and verifier
`_keyset_seek_quals_match` (F-B). (c) `encode_keyset_cursor` /
`decode_keyset_cursor`: both owned in `keyset.py`; lateral carries values
only. (d) `_apply_lateral_converters` + `_instantiate_row` reproduce
framework-iterable effects: R-2 (framework population). Verdict: discharged;
pairs share owners, no drifting twin.
5. Contracts in other media. Oracles (read as oracles, never rewritten):
`tests/optimizer/test_lateral_fetch.py` (1494 lines, clean tree),
`tests/test_keyset.py` lateral-seek rows, `tests/optimizer/test_walker.py`
lateral-plan row, `tests/test_lateral_pg_parity.py` (Postgres tier),
`tests/optimizer/test_single_parent_fetch.py` cross-reference rows naming
`_parent_in_values` / `_deduplicate_parent_ids` owners. Projections (describe,
never own): module docstrings, `docs/README.md` strategy paragraph,
`docs/GLOSSARY.md` strategy entry, `docs/TREE.md` file rows. Counted as
definitions: zero. Verdict: discharged.
6. Enforcement by omission (every fetch mode checked). `FetchMode` has four
members (`utils/connections.py`): COUNTED, PROBED, CONSTANT_FALSE, NONE.
Lateral coverage per mode: COUNTED renders `COUNT(1) OVER ()` in-branch and
outer-selects it; the counted-KEYSET shape downgrades inside
`LateralPrefetchStrategy.plan` (named reason: qualify-wrapped
filtered-count window is already whole-partition). PROBED renders
`fetch_limit` in-branch LIMIT (plain first page) or `fetch_upper_bound`
outer filter plus probe sentinel (offset page, composes with marker rows);
both renderers share `_probe_increment` so the +1 cannot drift. NONE /
CONSTANT_FALSE render no count and no probe. Keyset count-free renders the
seek in-branch with `ORDER BY ... LIMIT`. Reverse renders the reversed
`ROW_NUMBER()` + reversed-bound filter in both dialects. Marker shapes render
`OR rn = 1` in both. Unbounded renders no upper bound in both.
`_build_lateral_spec` downgrade arms enumerated: counted keyset;
select_related/annotations/extra/extra_tables/group_by; visibility gate
(keyset, non-DIRECT_FK, `is_empty()`, non-plain-single-table);
composite/columnless pk; custom QuerySet subclass; unresolvable order
(empty/expression/traversal/`?`/non-local/multi-table); keyset
arity/order mismatch; `defer()`/multi-table projection or unreadable
`deferred_loading_of`; unresolvable `parent_link_field` (generic/unsupported);
through-field unlink; `UNSUPPORTED` shape. `single_parent_spec`
eligibility enumerated separately (count-free, non-reverse, plain QuerySet,
DIRECT_FK with link, plain-first-page) and is windowed-only by documented
design, as is the lateral single-parent variant (out of v1 scope, stated in
both modules). Planner-level refusal arms (sidecar, SKIP, unwindowable child,
unwindowable kind, malformed/conflicting payloads, `UnwindowableConnection`)
never reach any strategy; divergent aliases plan per response key. Verdict:
discharged; every mode has a rendering or a named downgrade, no omission gap.

### Definition counts per posited change (my rules)

- Window rendering (F-A): change the marker predicate (e.g. marker row
identity): moves `apply_window_pagination` + `build_lateral_sql` = 2
definitions; `window_range_plan` owns the decisions (bounds/marker/probe) and
does not move; `split_window_rows`/`_resolve_from_window` are consumers.
- Seek planning (F-B): remove the redundant leading bound: moves
`keyset_seek_q` + `keyset_seek_sql` + `_keyset_seek_quals_match` = 3
definitions; `build_keyset_seek_plan`/`KeysetSeekPlan` own the structure;
`_keyset_seek_sql` (adapter) follows.
- Fetch-mode guard (F-C): permit probe+count: moves
`assert_window_fetch_mode` = 1 definition; both `__post_init__`s and
`apply_window_pagination` are enforcement-site consumers.
- Queryset skeleton (F-D): carry a new clone attribute: moves
`RecognizedFetchQuerySet._clone` (+ `rebind` capture) = 1 definition;
subclasses declare slot names only.
- Recognizer vocabulary (F-E): rename the `_dst_*` namespace: moves the
`WINDOW_*` constants in `plans.py` = 1 definition; `_WINDOW_ANNOTATIONS`,
the single-parent annotation check, and the signature normalizer all compose
the constants by name and follow by construction.
- Strategy seam (F-F): add a fourth builtin name: moves the
`_builtin_strategies` registry = 1 definition; `StrategySelection`,
`_require_strategy`, `OptimizerHint.strategy` are consumers.
- Join vocabulary (F-G): change a shape mapping: moves
`classify_relation_join` = 1 definition; `_build_lateral_spec`,
`window_partition_for_prefetch`, planner shims are readers.
- Order/projection vocabulary (F-H): change dash rule or loading-tuple read:
moves `order_entry_name_and_direction` / `deferred_loading_of` = 1 each;
`_order_columns` / `_select_columns` are readers.
- Reversal (R-1): NULLS-on-reversal: count 1 (`_reverse_order_by` only).

### Owners I would choose per rule (principle 7)

Window-range decisions: `utils/connections.py::window_range_plan`
(responsibility: pure slice arithmetic shared by both renderers and the
resolver; every consumer can depend on it without reversing a dependency).
Seek structure: `keyset.py::build_keyset_seek_plan` (cursor contract owner;
both dialects + verifier depend on it). Fetch-mode exclusion:
`utils/connections.py::assert_window_fetch_mode` (single boundary every
window entry shares). Skeleton lifecycle: `nested_fetch.py` (seam owner;
adapters stay in `lateral_fetch.py` / `single_parent_fetch.py` per principle
5). Window signature: `lateral_fetch.py::window_predicate_signature`
(only module that discards the ORM query and executes from a stored plan, so
the fail-closed proof lives beside the backend that needs it; single-parent
consumes it). Strategy registry: `nested_fetch.py` (protocol + selection
owner; hint module consumes). Join facts: `join_taxonomy.py` (sole
classifier; strategies read). Order/projection reads: `plans.py` (existing
owners; lateral reads). Lifetimes (principle 4): plan-cacheable spec fields
frozen at `_build_lateral_spec` (per-user values never enter the cache;
custom `get_queryset` marks non-cacheable in `nested_planner.py`); window
signature captured at `rebind` before prefetch appends `__in`; approved
visibility bytes carried on `_RecognizedLateralFetch` so the executor splices
proven bytes (no recompile seam). Observable behavior (principle 8): row sets
byte-mirror the ORM window per backend; worst case of any fetch-time surprise
is windowed performance (fail-closed recognizer + superclass `_fetch_all`).

### Defects

None found by me. Candidates considered and rejected with reason (GOAL.md
trust boundary: a defect needs a contract row plus a feasible project shape
under supported public API reaching it): (a) `_deduplicate_parent_ids`
unhashable fallback keeps order/duplicates: docstring openly scopes dedupe to
hashable ids; pk values reaching it via normalized `__in` lists are hashable
scalars, and no contract source requires unhashable dedupe: no row, not a
defect. (b) Empty parent list rendering `(VALUES )`: unreachable, early `[]`
return precedes the build. (c) Through-join direction
`child.child_join_column = through.through_child_column`: verified correct
against `_build_lateral_spec` field resolution. (d) Signature `None`
fail-closed and `planned None` downgrade: correct closed behavior on both
recognizers.

### Freshness fingerprints

HEAD `bfaee91dcd332a5f86250fff90ab21b377bc674e`. Target
`django_strawberry_framework/optimizer/lateral_fetch.py` clean:
worktree `db1ea315d774f55e893c108c6e0bc995299a9fa2` =
HEAD `db1ea315d774f55e893c108c6e0bc995299a9fa2` (1181 lines).
Neighbors (worktree blob read; HEAD blob alongside where dirty-concurrent):
`optimizer/nested_fetch.py` worktree
`29ce5201877864b01079c849b92a1e812166affd` vs HEAD
`4d8d37a7f52cf94d2916f17db3a8a21393e28d57` (dirty: `resolve_strategy`
hostile-`__class__` hardening per worktree-vs-HEAD diff; lateral-relevant
`attach_windowed_prefetch`/`RecognizedFetchQuerySet` hunks untouched).
`optimizer/single_parent_fetch.py` clean `e995270af9b213b7f931c03d7dc8f7c084819e1b`
both. `optimizer/plans.py` clean `cce985319c8833f3660653327d3003f1f03655a5`
both. `optimizer/walker.py` clean `9b111ed938951a073a9226ccbcfacabc3af981e8`
both. `optimizer/join_taxonomy.py` worktree
`e1cbb3e327785de3b59ccafef6b463df52e06396` vs HEAD
`9b355a5090ce471e373849dd0a61da8f808e78b9` (dirty: composite-pk
`_child_link_is_virtual` feature per diff; lateral `parent_link_field=None`
refusal rides it as designed). `optimizer/hints.py` worktree
`8064af14930636d6b12a538a996603ccadfdb420` vs HEAD
`da46ef891ccd8a2d42c8ac7519d9f42c9cb73b74` (dirty: hostile `Prefetch` guard
per diff; strategy surface untouched). `utils/connections.py` clean
`f549389ef0ed97bfbe4b158ab21bfc993b71b714` both. `keyset.py` clean
`df4b5e2f105c2b9fa956eac7cea25ba8a0a8de80` both.
`optimizer/nested_planner.py` worktree
`e69dbf5f30aa4623a5aad93edfacdabb391d6601` vs HEAD
`0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04` (dirty-concurrent, +9 lines,
hunks not itemized; cited lines read at worktree blob).
`connection.py` worktree `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` vs HEAD
`93e998f2c7ea1d7f18607a6e37e394466ac75ad4` (dirty-concurrent, +65/-1, hunks
not itemized; cited lines read at worktree blob). Oracle
`tests/optimizer/test_lateral_fetch.py` clean
`67431054f47a1707459a57eb21e08a5986140ef6` both (1494 lines).
`orders/sets.py` lines 685-714 read for axis-1 discharge (prose only).
Contract sources: `docs/dry/DRY.md` `e8151123ff7e129fe9881ec342231e9e1795148e`
both; `docs/dry/worker-2.md` `4f089ea4a58d73295638e83abf8c612bf31487f8` both;
`GOAL.md` `7dfbef5c784519d5f95311aaeb8c6766ee966b02` both; `AGENTS.md`
`e42247fa310bf7a85914d7efa7f177ee5307b860` both. Item-scoped diff on tracked
paths: EMPTY (no production edit; this section appended to the untracked
artifact only). No status set; no verdict on Worker 1 proposed.

PHASE-1-TRACE-RECORDED docs/dry/dry-file-optimizer__lateral_fetch.md

## Iterations

### Worker 2 phase-2 reconciliation (pass 2; verdict: verified)

Phase-1 trace above stands with the corrections in this section. Worker 1's
record read in full (phase-2 disclosure). No worker-memory read. HEAD is
still `bfaee91d`; target still worktree-clean (`db1ea315…` both); every
neighbor hash re-pinned identical to phase 1 (table below). Item-scoped diff
on tracked paths: EMPTY. Concurrent dirt preserved; nothing committed.

1. Contamination verdict. The phase-1 fragments (family names F-A/F-B, FL
labels, axis framings, oracle names) match Worker 1's rows in exactly two
places of substance: my phase-1 labels F-A `window-range-dual-render` and
F-B `keyset-seek-dual-dialect` are identical to Worker 1's. I judge the
F-A/F-B NAMING likely primed by the fragment and quarantined accordingly:
those two labels are adopted-from-fragment, not independently coined.
Everything else evidences independent derivation: my extra families F-G/F-H/F-I
(which I dissolve below — they were over-structuring, not copies), my
rejections R-1/R-2/R-3 (no counterpart in the fragment), my explicit
four-mode FetchMode walk, my `_WINDOW_ANNOTATIONS` compose-by-name count, my
unhashable-dedupe/through-join/empty-VALUES defect candidates, and my
`orders/sets.py` prose check all lie outside what the fragment showed.
Re-derivation of the two primed rows, cleanly from source (labels set
aside): (i) the window-range rule groups `window_range_plan` (decisions) +
two renderers (`apply_window_pagination`, `build_lateral_sql`) because both
modules' docstrings state the sharing explicitly and both bodies call/read
the same plan object — any trace from the source lands here; posit
"marker-predicate change" moves 2 renderer bodies, decisions stay 1 owner;
(ii) the seek rule groups `build_keyset_seek_plan` + two dialect renderers +
lateral adapter/verifier because the adapter calls `seek.plan(values)` and
`keyset_seek_sql(refs, plan)` and the verifier reads `seek.plan()` at
runtime — posit "drop redundant leading bound" moves 3 bodies textually
under 1 plan owner. No conclusion (counts, owners, zero-edit, no-defect)
depended on the fragment: the counts differ from Worker 1's in method (see
4) yet converge on "no second authoritative definition." FL4/FL5 label
matches are consistent with independent source-order numbering and carry no
weight. Verdict: naming-only exposure, substance re-derived clean; no row
re-derived differently because of it.

2. Enumeration reconciliation (44 = 44; rule-bearing 30 = 30; imports 13
incl. future, def/class 21, assigns 9 — full agreement on counts; their
probe `OK 44/21/9` matches my inline AST count). Row map, Worker 1 #1-25
against my homes, every member homed on both sides, deltas adjudicated:
- #1 FL1, #2 FL2, #4 FL3-record, #5 F-A, #6 F-B, #7 F-D, #8 FL4, #9 FL5,
  #11 FL6-converters, #13 F-E, #15 F-E, #16 F-B, #19 row-builder, #20/21
  F-F: AGREE (numbering-only deltas on my side, no substance gap).
- #3 `_WINDOW_ANNOTATIONS` (their F-A-consumer) vs my F-A-vocabulary
  consumer: AGREE, same role.
- #10 `_deduplicate_parent_ids` (their F-E) vs my FL6-owner-with-consumer:
  ACCEPT THEIRS. My "file-local" label violates the DRY backstop sentence
  (a row naming a second site is a family, never file-local); the
  `single_parent_fetch.py` import is the second site. Re-homed to F-E.
- #18 `_parent_in_values` (their F-E) vs my FL8: ACCEPT THEIRS, same
  backstop reason (imported by single-parent). Re-homed to F-E.
- #12 `_recognize_lateral_fetch` (their FL7 file-local) vs my F-E-consumer:
  ACCEPT THEIRS. The body is single-site; it consumes F-E vocabulary but
  is itself file-local. My label was imprecise; corrected to FL7-equivalent.
- #14 `_normalize_window_node` (their FL8) vs my F-E-normalizer: ACCEPT
  THEIRS. Used only by `window_predicate_signature` in this file; the
  narrower home is accurate. (C6 still counts it inside the owner body.)
- #17/#22 visibility pair + #4-spec-slot + #23-gate (their FL9/FL11/FL3/FL12)
  vs my family F-I: DISSOLVE MY F-I. A single-site cluster is not a
  cross-site family and needs no family item; their decomposition is
  tighter. Every member stays homed; no coverage lost.
- #24 `_order_columns` (their FL13) and #25 `_select_columns` (their F-E)
  vs my family F-H: DISSOLVE MY F-H. `_select_columns` is IMPORTED by
  single-parent, so F-E is the correct home (my "reader" framing inverted
  the provider direction); `_order_columns` is single-site (single-parent
  freezes `tuple(request.order_by)` directly — parallel, separate need),
  so FL13 is correct.
- My F-G join-vocabulary: WITHDRAWN as a family from this item. The owner
  (`join_taxonomy.py`) lives in another item; the correct record here is
  "consumed definition, read never re-derived," which Worker 1's site list
  already carries. No index row owed.
- Net family delta resolved: my 9 collapse to Worker 1's 6 (F-A..F-F);
  my 10 file-local + preamble-consumers map onto their 13 with the
  re-homings above; no member unassigned on either side.
- Rejections: their R1-R4 map onto F-A/F-D/F-B/C8 (already-consolidated
  separations with triggers) — agree each. Their R5 no-async-twin matches
  my axis-2 inapplicability (same verdict, see 3). ADD two Worker-2 rows
  with no Worker-1 counterpart, both with triggers: R-1-reversal
  (`_reverse_order_by` NULLS-swapping raiser vs `order_sql`
  direction-only flip; trigger: lateral accepts expression/explicit-NULLS
  orders) and R-3-binding (`unnest(array)` vs `VALUES` are branches of one
  predicate, not two definitions; trigger: a second parent-binding site).
  My R-2 (framework population) duplicates their matrix 4(c) substance;
  folded there, not a separate row.

3. Matrix judgment. R5 vs my axis 2: AGREE — zero `AsyncFunctionDef` both
probes, sync-only by construction, shared sync boundary owned at
`utils/querysets.py`; theirs adds the family name, mine the
`extension.py` wrapper path; same "no twin owed" verdict. C8 vs my
FetchMode walk: BOTH COVER ALL FOUR MODES — theirs via shared-plan
construction (every mode is a `WindowRangePlan` value both renderers read),
mine via explicit per-mode rendering checks (COUNTED renders COUNT;
counted-keyset downgrades; PROBED renders `fetch_limit`/`fetch_upper_bound`
+1 sharing `_probe_increment`; NONE/CONSTANT_FALSE render neither; plus
reverse/marker/unbounded parity). No omission gap on either side; my walk
adds assurance, changes no verdict. Divergences C8 adjudicates
(THROUGH_TABLE, visibility, counted keyset, select_related) re-checked
against `single_parent_spec` and the planner arms: intentional separations
with triggers, agree each.

4. Counts, roles, owners. Methodology delta recorded honestly: Worker 1's
challenge counts are OWNER counts (followers collapse into the owner);
mine are MOVING-BODY counts (C1-analog 2, C3-analog 3). Both are correct
under their posit; the DRY question — "how many AUTHORITATIVE definitions
must one change touch" — is answered 1 in every challenge on both sides:
followers derive from (`window_range_plan`, `build_keyset_seek_plan`) or
mirror with：identically-proved shape. No hidden second authority found by
either method. F-C owner precision: ACCEPT `assert_window_fetch_mode_for`
(the spelling both `__post_init__`s call) over my cited base; count stays 1.
F-D (skeleton owned by dirty `nested_fetch.py`): consumer roles SOUND —
subclasses add genuinely different work (spec slot + distinct recognizers),
adapters per principle 5; and the worktree-vs-HEAD diff touches ONLY
`resolve_strategy` + docstring, so the F-D owner bytes are HEAD-stable and
the dirt is adjacent, not load-bearing. F-E (vocabulary owned HERE with
two consumer files): KEEP — change-obligation test finds no multi-site
move (grammar change moves signature+normalizer = 1 site; namespace change
moves plans constants = 1 site), dependency direction permits either home
but principle 11 forbids a zero-relief move, and historical origin
(lateral first, single-parent importing with "single owner" comments)
confirms it. Their "already-single by name" confirmed.

5. No-defect audits, two spot-checked myself against current worktree bytes
(hashes pinned identical to phase-1 reads). SPOT-CHECK A (param/SQL
positional alignment, `build_lateral_sql` lines 327-424): params order is
parents → seek span → visibility span → range bound in BOTH branches, and
SQL placeholder order matches (parent relation, branch seek, branch
visibility, in-branch `LIMIT %s` or outer range filter); outer select
carries no placeholders; empty parents return `[]` before any build, so an
empty `VALUES` list is unreachable. PASSES. SPOT-CHECK B (signature
multiplicity, `_normalize_window_node` + `window_predicate_signature`):
nodes sort LISTS (multiplicity preserved, never set-collapsed),
`lookup_name` rides every leaf verbatim (`gt` never equals `lte`),
expression rhs and unmapped lhs yield `None`, empty-tuple (unbounded)
stays distinct from `None` (unreadable), and both recognizers fail closed
on `None`. PASSES. The remaining two audits re-confirmed by citation of
read bodies: `_parent_in_values` requires list/tuple rhs with zero
`resolve_expression` members; `_visibility_quals_match` returns the
residue's own approved compile (byte-equal to the stored scope) which
`_fetch_lateral_rows` splices without recompiling. No defects found
(Worker 2): the `## Defects` section stays empty.

6. Freshness re-hash (phase 2, HEAD still `bfaee91d`): target
`db1ea315…`/`db1ea315…` clean; `nested_fetch.py`
`29ce5201…`/`4d8d37a7…`; `single_parent_fetch.py` `e995270a…` both;
`plans.py` `cce98531…` both; `walker.py` `9b111ed9…` both;
`join_taxonomy.py` `e1cbb3e3…`/`9b355a50…`; `hints.py`
`8064af14…`/`da46ef89…`; `nested_planner.py` `e69dbf5f…`/`0ad8ff5d…`;
`connection.py` `3c4d5dcb…`/`93e998f2…`; `utils/connections.py`
`f549389e…` both; `keyset.py` `df4b5e2f…` both; oracle
`tests/optimizer/test_lateral_fetch.py` `67431054…` both. All identical to
phase 1; no fingerprint changed; nothing reopened.

7. Proof adequacy (`## Pending execution`: NONE — stands). Backend-
observable SQL (principle 8) does not force execution HERE because this
item ships zero edits: every challenge resolves by body identity, and no
ordering/transactional/async behavior changed. The oracles the FINAL GATE
runs for this surface: default `uv run pytest` executes
`tests/optimizer/test_lateral_fetch.py` (69 rows, pure builder +
downgrades + recognition on SQLite via injected `quote_name`),
`tests/test_keyset.py` (seek rows), `tests/optimizer/test_walker.py`
(plan rows), `tests/optimizer/test_nested_fetch.py` (resolution rows),
`tests/optimizer/test_single_parent_fetch.py` (counterpart rows).
`tests/test_lateral_pg_parity.py` + `tests/test_predicate_pg_explain.py`
skip without `FAKESHOP_PG_DSN`: live-Postgres emission cells stay
UNVERIFIED unless the maintainer authorizes the PG tier — reported for the gate, not
assumed. Ruff on touched tracked paths: none touched, N/A (artifact is
untracked markdown). AGENTS.md empty-diff prose: legitimate zero-edit
result — matrix discharged, challenges counted, strongest rejections carry
triggers (R1–R5 + added R-1/R-3), backstop complete at 30/30 homed both
sides; a file item owes no production edit.

8. Verdict: `Status: verified` (set above). No `proof:` entries, so the
plan item is fully verified, not pending-execution. Plan rows for Worker 0:
(a) tick the file item `optimizer/lateral_fetch.py` verified under Run
`0.0.15 2026-09-19-1`; (b) NO new index rows from this item — F-G/F-H/F-I
dissolved, F-A..F-F already open as stated; optionally attach added
rejections R-1-reversal/R-3-binding to the owning family/file items when
they open; (c) scratch removal, by explicit path only after tick:
`docs/dry/temp-tests/dry-file-optimizer__lateral_fetch/probe_enumeration.py`
(the directory if empty thereafter). Concurrent dirt listed in the phase-1
table untouched throughout.

PHASE-2-TRACE-RECORDED docs/dry/dry-file-optimizer__lateral_fetch.md
