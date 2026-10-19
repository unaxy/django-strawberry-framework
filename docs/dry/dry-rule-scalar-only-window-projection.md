# DRY review: `scalar-only-window-projection`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

Target: the scalar-only window projection — how a nested
connection selection with no `edges { node }` still window-plans
with a minimal child projection instead of fetching full rows.

Contract (spec-033 Decision 4 scalar-only bullet + Decision 6):
a scalar-only (`pageInfo`-only / `totalCount`-only) NESTED
selection is planned, not a fallback; with no node-child
scalars the windowed child queryset is restricted to pk +
attach-complete connector set + concrete deterministic-order
columns via a direct `.only()`, gated on the threaded
`enable_only` flag; related-span and unresolvable order
entries are skipped (the window `OVER (ORDER BY ...)` and the
queryset `ORDER BY` reference them in SQL regardless, so a
skipped column only forgoes loading an attribute a scalar-only
selection never reads). Varies over column classes,
order-entry shapes, relation shapes, and the operation gate.

Traced at WT bytes (HEAD `5c3496e0` + worktree). All line
numbers below are WT lines. Fingerprints (WT `git hash-object`
/ HEAD `git rev-parse HEAD:` / baseline `git rev-parse
807a7f09:`; baseline is the item `git stash create` commit,
taken at dispatch):

| File | WT | HEAD | Baseline |
|---|---|---|---|
| `optimizer/nested_planner.py` | `b6ff0a0e` | `8c3a45f5` | `b6ff0a0e` |
| `optimizer/join_taxonomy.py` | `aa289013` | `8026dc8d` | `aa289013` |
| `optimizer/plans.py` | `2e962ae2` | `97a524e2` | `2e962ae2` |
| `optimizer/walker.py` | `4fd8077f` | `13e1be20` | `4fd8077f` |

WT == baseline on all four indexed files (no bytes moved
since dispatch); WT == dispatch pins. Dirt attribution (every
hunk diffed vs `git show HEAD:`, none in `## Owned changes`
except the landed D1 walker fix already at HEAD, so all WT
dirt below is concurrent work — read, not traced as family
behavior, not edited, not reverted):

- `nested_planner.py` 11+/1-: `truth` import, M2M advisory
  silence in `_advise_composite_index`, one `truth.name`
  fallback-log touch. None in F5 lines
  (`:187`-`:222`, `:701`-`:739`, `:1284`-`:1285`,
  `:1373`-`:1379` — all WT==HEAD there).
- `join_taxonomy.py` 102+/88-: truth-migration rewrites
  (`_attr`/`_flag`/`_first_truthy`) + `_child_link_is_virtual`
  arms in `_partition_expr` / `_parent_join_column` /
  `classify_relation_join`, incl. a forward multi-column
  `None` arm and removal of a `BaseException` swallow. The
  family reads `prefetch_attach_columns` BY NAME (`:735`
  here, `walker.py:1604`); both reads verified intact at WT.
  Owner-internal drift belongs to f23's owner, not reopened.
- `plans.py` 4+/2-: `truth` import, `truth.name` in
  `resolver_key`, `truth.static_attr` in
  `ends_in_unique_column`. The entry parser `:813`-`:843`
  and `OptimizationPlan.apply` `:324`-`:339` are WT==HEAD.
- `walker.py` 13+/11-: `truth` import + `truth.name` /
  `static_attr` / `is_subclass` rewrites. Aliases `:104`-`:112`,
  `_ensure_connector_only_fields` `:1578`-`:1613`,
  `_plan_connection_relation` `:1819`-`:1854` all WT==HEAD.

Supporting fingerprints (WT / HEAD): `tests/optimizer/
test_walker.py` `ca5c32d7` clean;
`examples/fakeshop/test_query/test_library_api.py` WT
`099e25b9` vs HEAD `91f0238b` (dirt at `:1050`, `:1084`,
`:5513`, `:9753`, `:11594` — none inside the oracle tests
cited below); `docs/SPECS/
spec-033-connection_optimizer-0_0_9.md` `33b845a3` clean;
`optimizer/selections.py` `1f6d3e04` / `f49ea7fa`;
`optimizer/extension.py` `8e3fe7c1` / `b7b6c434`;
`optimizer/lateral_fetch.py` `a48cb0a4` clean;
`keyset.py` `7d43c6b1` / `6af980b8`; `connection.py`
`48de0243` / `99969652`; `list_field.py` `6c0992f2` /
`37d2e6dc`; `optimizer/single_parent_fetch.py` `3a4bb89b`
clean; `optimizer/nested_fetch.py` `c36826bb` / `bedaa76e`.

Sites and roles, WT bytes:

- Definitions (one body each, all in
  `optimizer/nested_planner.py`):
  - D1 `_project_scalar_only_window` (`:701`-`:739`): the
    projection body (pk + attach set + order columns, fresh
    `.only()`, `enable_only` early return). Sole production
    caller `:1374` (the F1 scalar branch). Zero test
    imports; two test docstring mentions.
  - D2 `_concrete_order_columns` (`:200`-`:222`): the
    order-to-columns walk with the SKIP posture for
    related spans / unresolvables / attname-or-name index.
    Sole production caller D1 (`:737`). One test pin
    through the walker namespace (`test_walker.py:2726`).
  - D3 `_order_entry_field_name` (`:187`-`:197`): the
    name-half shim; body delegates to the shared parser
    (`:196`). Sole production caller D2 (`:215`). Zero
    test imports; one docstring mention (indirect cover).
  - D4 scalar-only detection: `scalar_only = not
    node_selections` (`:1285`) over
    `_connection_node_selections` (`:801`-`:819`), a thin
    adapter over `selections.connection_node_children`.
    Single site.
- Consumers composing by name (listed, not counted):
  - Attach columns: `join_taxonomy.py::
    RelationJoinDescriptor.prefetch_attach_columns`
    (f23-consolidated owner), read at `:735` and
    `walker.py:1604`.
  - Entry parsing: `plans.py::
    order_entry_name_and_direction` (`:813`-`:843`),
    read by D3 plus the advisory walk (`:284`), the
    lateral backend (`lateral_fetch.py:1197`), the
    keyset guard (`connection.py:891`), and
    `ends_in_unique_column` (`plans.py:887`).
  - Deterministic order: `plans.py::
    effective_connection_order` (open family
    `connection-order-ladder`), read at `:1361`.
  - Operation flag: the walker G2 gate
    (`_enable_only_for_operation`, spec-035 Decision 4),
    threaded walker `:1844` -> planner `:1378` -> D1
    (`:724`).
  - Unwrap: `selections.py::connection_node_children`
    (`:673`), read by the D4 adapter and the extension
    root extractor (`extension.py:707`).
  - Walker aliases (`walker.py:104`-`:112`):
    `_project_scalar_only_window` and
    `_order_entry_field_name` assignment-only (no reader
    through the module — full census below);
    `_concrete_order_columns` read by one test.
    Historical-compat spelling, documented at `:95`-`:103`.
  - Single-parent fast path: inherits the planned child
    queryset (incl. a scalar-only `.only()`) via
    `pristine_child_queryset`; counted shapes excluded
    by eligibility (`with_total_count` -> `None`).
- Oracles (independent — literal column sets / query
  counts, never read the owner):
  - Package (`tests/optimizer/test_walker.py`, clean):
    `:3591` planned-not-fallback, `:3611` pk/connector/
    order `.only()`, `:2680` non-pk order column, `:3640`
    generic morph half, `:2712` entry shapes via the
    walker namespace, `:5071` G2 gate; `:2314` is the
    sibling-path contrast, `:2022` the adjacent shim pin.
  - Live (`test_library_api.py`, oracle lines clean):
    `test_nested_books_connection_has_next_page_without_edges`
    (pageInfo-only nested, asserts root + one windowed
    prefetch) and `test_nested_total_count_without_edges`
    (`:7870`, totalCount-only nested, asserts the true
    count from the annotation + 2 queries). Both are
    sidecar-free, so both reach the scalar branch.
- Projections (describe, never own): spec-033 Decision 4
  scalar-only bullet + Decision 6 planned-scalar paragraph,
  the writer/walk docstrings, the GLOSSARY
  connection-aware-planning paragraph.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. The rule is
   optimizer-internal (nested windows only). Sibling
   flavors carrying order vocabulary: `list_field.py::
   _has_deterministic_ordering` (E12) and
   `keyset.py::split_order_ref` (E11) — both excluded with
   triggers re-checked fresh (zero `plans` imports in
   `list_field.py`; `split_order_ref` still loud,
   strings-only, no traversal at WT `:192`-`:217`).
2. Sync/async twins — RULED OUT. The family path is
   plan-time and sync-only: selection reads, `_meta` /
   descriptor reads, lazy `.only()` construction. No
   await boundary exists in it, so no twin can drift.
   Async execution runs the same planned queryset
   through the shared fetch body.
3. Derived rather than repeated knowledge — SEARCHED.
   Every input fact has one derivation: pk attname read
   once at `:729`, attach set via the f23 owner, order
   names via the shared parser. The name/attname index
   idiom spelled at both order walks is E2 (standing R6,
   trigger intact).
4. Inverse / round-trip pairs — SEARCHED. The projection
   is one-way (plan -> queryset); no decode half exists.
   Mask READERS (`_consumer_projection`, lateral
   `_select_columns`) are E5 (standing R13). The
   `to_attr` grammar (f28) and keyset codec are separate
   owned rules, untouched.
5. Contracts restated in another medium — SEARCHED.
   Spec-033 prose and glossary prose are projections;
   the oracles above are independent (literal sets, see
   `{"id", "card_id", "decided_at"} <= set(only_fields)`
   at `test_walker.py:2707`, and live 2-query pins).
6. Enforcement by omission — ENUMERATED. Nested planned
   windows: covered. Root connections: no scalar-only
   projection (E10 — contract scopes to nested; root
   fetch bounded by the page slice). Sidecar /
   unwindowable / refused / `SKIP` windows: deliberately
   unplanned per Decision 6 (never reach D1 — the
   `:1256` early return precedes the scalar branch).
   Non-`QUERY` operations: deliberately unprojected per
   the G2 gate. Keyset scalar-only windows: take the
   SAME project branch (no edges -> no cursor minting;
   the cursor order projects via D2) — no omission.

### Enumeration

Family item (no file-member enumeration owed): the
mechanism sweep covered the whole package for (a) direct
`.only()` / `.defer()` queryset writers, (b) order-entry
walks, (c) scalar-only detectors, (d) attach-column
readers. Writer census (package-wide grep, WT): exactly
three code sites — `:739` (D1, this family), `:773`
(keyset extend, E4), `plans.py:334` (generic
`OptimizationPlan.apply`, E6). Order-walk census: D2
(skip), `_concrete_order_terms` (None, E1), lateral
`_order_columns` (None/downgrade, E3), keyset guard read
(composes parser), `ends_in_unique_column` (unique check,
composes parser). Detector census: D4 only (the extension
root extractor composes the same unwrap; root has no
scalar branch — E10). Attach-reader census: D1 `:735`,
`_ensure_connector_only_fields` (E7), `_connector_only_field`
shim (E9, zero production callers).

### Challenges

Each change posited + definitions forced (consumers listed,
never counted):

- C1 new column class (order must also cover related
  spans): D2 alone moves (skip arm). Count 1.
- C2 new order-entry shape (a new expression kind):
  `order_entry_name_and_direction` alone moves; D3/D2
  follow by composition. Count 1, outside the family.
- C3 new relation shape (a new attach half): the
  join-taxonomy owner alone moves (f23); D1 follows by
  composition. Count 1, outside the family.
- C4 new scalar-only shape (a new scalar that must not
  force node planning): `connection_node_children`
  alone moves. Count 1, outside the family.
- C5 gate change (a new operation kind):
  `_enable_only_for_operation` alone moves (the G2 gate,
  walker `:145`); D1 follows by composition via the threaded
  `enable_only` bool (walker `:1844` -> planner `:1378` ->
  `:724`). Count 1, outside the family. (Completion tail:
  finished from the cut-off line; lines 1-237 held
  byte-intact.)

## Findings

Re-verification (completion pass): every load-bearing
claim below was re-checked at current WT bytes and holds —
no correction to the record is owed. Fingerprints: WT ==
baseline on all four indexed files (`b6ff0a0e`,
`aa289013`, `2e962ae2`, `4fd8077f`) — holds. D1 `:701`-`:739`
sole production caller `:1374` — holds (scoped census:
only other hits are the walker alias, docstrings, and two
test docstring mentions). D2 `:200`-`:222` sole production
caller D1 (`:737`), one test pin through the walker
namespace (`:2726`) — holds. D3 `:187`-`:197` delegating at
`:196`, sole production caller D2 (`:215`), zero test
imports, one docstring mention — holds. D4 `:1285` over
the `:801`-`:819` adapter — holds. Parser consumer list
(D3 `:196`, advisory `:284`, lateral `:1197`, keyset guard
`connection.py:891`, `ends_in_unique_column` `:887`) —
holds. G2 threading (walker `:1844` -> planner `:1378` ->
D1 `:724`) — holds. Attach reads (`:735`,
`walker.py:1604`), `effective_connection_order` read
(`:1361`), walker aliases (`:104`-`:112`, doc `:95`-`:103`),
single-parent `pristine_child_queryset` inheritance with
`with_total_count` refusal — holds. Oracle pins
(`:3591`, `:3611`, `:2680`, `:3640`, `:2712`, `:5071`,
`:2314`, `:2707` literal set; live `:7791`, `:7870`) —
holds. Writer census (three `.only()` bodies `:739`,
`:773`, `plans.py:334`; the `:766`-`:767` defer-clear sits
inside the E4 body) — holds. Order-walk / detector /
attach-reader censuses — holds. E11 loud/strings-only and
E12 zero-`plans`-imports — holds. Dirt attribution (family
lines WT==HEAD; hunks at planner `:28`/`:643`/`:1488`) —
holds. Spec-033 Decision 4/6 scalar-only prose — holds.

### F1 scalar-only window projection — CONFIRM, single-owned, zero-edit

Contract + variation: a scalar-only (`pageInfo`-only /
`totalCount`-only) NESTED selection is planned, not a
fallback, with a minimal child projection (pk +
attach-complete connector set + concrete deterministic-order
columns via a direct `.only()`), gated on the threaded
`enable_only` flag; related-span and unresolvable order
entries are skipped. Varies over column classes,
order-entry shapes, relation shapes, and the operation
gate (spec-033 Decision 4 scalar-only bullet + Decision 6).

Sites + roles: 4 definitions, all in
`optimizer/nested_planner.py`, each the sole owner of its
sub-decision — D1 `_project_scalar_only_window` (the
projection producer), D2 `_concrete_order_columns` (the
skip-arm order walk), D3 `_order_entry_field_name` (the
order-entry name-half reader), D4 `scalar_only` detection
plus the `_connection_node_selections` adapter (the
scalar-shape reader). Consumers (listed, not counted):
the f23 attach owner, the shared entry parser, the open
`connection-order-ladder` family, the G2 gate, the shared
unwrap, the walker compat aliases, the single-parent fast
path — all per the System trace. Oracles: 8 package pins
plus 2 live pins, all independent (literal sets / query
counts). Projections: spec-033 prose, docstrings, the
glossary paragraph.

Challenges: C1 forces D2 alone; C2 forces the shared
parser (outside); C3 forces the f23 owner (outside); C4
forces the shared unwrap (outside); C5 forces the G2 gate
(outside). Every count is 1: no change moves two
definitions together, so no second owner exists for any
sub-decision.

Owner + lifetime: D1
(`optimizer/nested_planner.py::_project_scalar_only_window`,
re-derived, not inherited) owns the projection; D2/D3/D4
are its composed sub-decisions, each singly owned at its
own site. No stored derivation: pure plan-time derivation
("not cached") — lifetime is one plan build, and the
result rides the returned queryset into the window
annotations applied afterwards in
`_plan_connection_relation`.

Migration: none — zero-edit verdict. D1 already reads the
attach owner and D2 by name; D2 already reads D3 by name;
D3 already reads the shared parser by name; D4 already
reads the shared unwrap by name. No former definition
remains to rewire.

Distinct behavior: the skip-vs-None order postures stay
separate (D2 vs E1/E3, each owned by its caller's failure
meaning); the keyset UNION-extend (E4) stays separate
from D1's fresh projection; the generic plan applier (E6)
stays separate (D1 never touches `only_fields`); root
connections keep no scalar branch (E10); the loud keyset
string parser (E11) and the list-field determinism check
(E12) stay separate. Recorded here; no owner prose owed
beyond what the bodies already state.

Behavioral proof: `static-reviewed` for the verdict
itself (inventory-shaped counts over cited reads), plus
one `execution-verified` probe: `uv run pytest -n0
tests/optimizer/test_walker.py::test_scalar_only_window_projects_pk_connector_and_order_columns
--no-cov` → 1 passed in the shared venv (default cell).
That probe rejects the over-fetch (full child rows under
a scalar-only selection); the remaining oracles
(non-pk order column, morph half, entry shapes, G2 gate,
sibling-path contrast, live 2-query pins) are cited and
fingerprinted, their lines verified clean. No failability
run is owed: nothing lands, so no divergence exists to
prove catchable.

Structural gate: none owed. The plausible bypass is a
second scalar-branch writer or a caller reaching past D1;
no mechanical census closes that beyond a bespoke
existence test per helper, which is the forbidden shape
(f23 precedent). The AST writer census above (three
`.only()` bodies, each in a distinct owned function) is
the first-run check that the rule currently holds, and
the in-tree oracles pin every contract verdict so a
divergent second site fails behaviorally where it
matters. Negative control reasoned: a hand copy of D1's
body passes every behavior oracle (the copy is correct),
which is exactly why no new oracle is proposed as a gate.

Coupling: none. Zero-edit verdict; no finding depends on
another landing.

Freshness: HEAD `5c3496e0`, WT == item baseline
`807a7f09` on all four indexed files (re-verified this
pass): `optimizer/nested_planner.py` `b6ff0a0e` (HEAD
`8c3a45f5`); `optimizer/join_taxonomy.py` `aa289013`
(HEAD `8026dc8d`); `optimizer/plans.py` `2e962ae2` (HEAD
`97a524e2`); `optimizer/walker.py` `4fd8077f` (HEAD
`13e1be20`). Supporting: `tests/optimizer/test_walker.py`
`ca5c32d7` (clean); `test_query/test_library_api.py` WT
`099e25b9` (HEAD `91f0238b`, oracle lines clean);
spec-033 `33b845a3` (clean); `optimizer/selections.py` WT
`1f6d3e04` (HEAD `f49ea7fa`); `optimizer/extension.py` WT
`8e3fe7c1` (HEAD `b7b6c434`); `optimizer/lateral_fetch.py`
`a48cb0a4` (clean); `keyset.py` WT `7d43c6b1` (HEAD
`6af980b8`); `connection.py` WT `48de0243` (HEAD
`99969652`); `list_field.py` WT `6c0992f2` (HEAD
`37d2e6dc`); `optimizer/single_parent_fetch.py` `3a4bb89b`
(clean); `optimizer/nested_fetch.py` WT `c36826bb` (HEAD
`bedaa76e`). Searched population: every `.py` under
`django_strawberry_framework/` (scoped grep + AST census
above); every module excluded on body evidence is named
in an E row. Any fingerprint change reopens the finding.

### Exclusions (rejected candidates — contract difference + trigger)

No E8 label appears in the surviving trace, so no E8 row
is owed.

- E1 `_concrete_order_terms` (`:243`): the
  direction-carrying sibling with the None posture (an
  unresolvable entry returns None so the caller
  downgrades) vs D2's skip posture. Different failure
  meaning, different caller. Trigger: the advisory walk
  adopting skip-and-project semantics.
- E2 name/attname index idiom at both order walks: a
  shared two-line lookup shape, not a shared rule — each
  walk owns its own fallback posture (standing file-row
  rejection at `_concrete_order_columns`, trigger
  intact). Trigger: a third spelling or a posture change
  unifying the two walks.
- E3 lateral `_order_columns`
  (`lateral_fetch.py:1177`): None/downgrade posture for
  the correlated-join SQL builder — a downgrade there
  changes the fetch, not a column mask. Trigger: the
  lateral backend adopting the skip posture.
- E4 keyset extend (`_extend_only_projection`,
  `:742`-`:773` incl. the `:766`-`:767` defer-clear): a
  UNION-loader under an EXISTING mask (cursor columns
  must survive) vs D1 authoring a fresh minimal mask.
  Trigger: scalar windows ever extending rather than
  authoring the mask.
- E5 mask readers (`_consumer_projection`, lateral
  `_select_columns`; standing R13): read an existing
  mask; D1 authors one. Trigger: a reader that also
  authors.
- E6 `OptimizationPlan.apply` (`plans.py:334`): the
  generic applier of accumulated `only_fields`; D1 is
  the writer that never touches `only_fields` (docstring
  `:719`). Trigger: D1 routing through the plan
  accumulator.
- E7 `_ensure_connector_only_fields` (walker
  `:1578`-`:1613`): connector injection into an existing
  plan vs D1's fresh projection; both compose the same
  f23 owner by name. Trigger: either site spelling
  attach columns inline.
- E9 `_connector_only_field` shim (`:168`):
  single-column legacy read with zero production
  callers, superseded by the f23 owner. Trigger: a new
  caller (existence question homed per the f23 record).
- E10 root connections: no scalar branch — the contract
  scopes to nested windows; a root fetch is bounded by
  its page slice. Trigger: a root scalar-only projection
  landing.
- E11 `split_order_ref` (`keyset.py:192`-`:217`): loud
  strings-only config parser — malformed input is a
  `ConfigurationError`, never a fallback signal — vs
  the shared parser's None posture. Trigger: the keyset
  guard adopting a fallback posture.
- E12 `_has_deterministic_ordering`
  (`list_field.py:1141`): a boolean determinism check
  over an executed queryset vs plan-time column
  projection; zero `plans` imports (re-verified).
  Trigger: `list_field.py` importing the order
  vocabulary.

## Defects

None. Tracing found no non-duplication defect: every
docstring read matches its body, no family member lacks
an applicable guard (axis 6 enumerated with the contract
source for each deliberate omission), and all WT dirt in
the indexed files is concurrent work per the attribution
above — read for census only, untouched.

## Pending execution

None. No `proof:` entry (the verdict is inventory-shaped;
the one behavioral probe already ran green) and no
`gate:` entry. Default cell: executed — `uv run pytest
-n0
tests/optimizer/test_walker.py::test_scalar_only_window_projects_pk_connector_and_order_columns
--no-cov` → 1 passed in the shared venv (slot-2 venv
import-execution fails with `ModuleNotFoundError:
typing_extensions`, so the shared venv carried the
probe; the `dry/scalarwin-f29/consolidate` copy itself
was obtainable and ran a trivial command exit 0).
Sharded/PG cells: `inapplicable by construction` — the
rule is pure plan-time derivation (lazy `.only()`
construction plus field-attribute / `_meta` reads; no
queryset execution, no alias, no dialect decision),
stated for Worker-2 to judge (f28 precedent, accepted).
`--cell` runs were not authorized.

## Judgment

CONFIRM single-owned-zero-edit. The scalar-only window
projection lives once, in
`optimizer/nested_planner.py::_project_scalar_only_window`
with three singly owned composed sub-decisions (D2/D3/D4);
every variation axis challenges to exactly one definition,
inside or outside the family as the trace records. No
consolidation lands, no test is added, no ledger row is
owed. The artifact submits as `ready-for-verification/1`.
## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (only `^## `/`^### ` header lines +
`Status`/`Run` grepped for shape validation). All line numbers are WT bytes at
HEAD `5c3496e0` + WT (fingerprints below).

### My own trace (expectation-first)

Family rule: a scalar-only nested-connection window (pageInfo/totalCount-only
selection, `[]` node children) must carry a minimal `.only()` of pk + attach
columns + concrete order columns instead of fetching full child rows, gated by
the G2 operation gate (spec-033 Decision 4/6 contract, spec-035 Decision 4 gate).

Definitions I posit (in-family, each must count 1):

- D1 `optimizer/nested_planner.py::_project_scalar_only_window` (`:701`-`:739`):
  constructs `fields = [pk] + prefetch_attach_columns + order columns`, returns
  `child_queryset.only(*fields)`; G2 refusal arm at `:724`-`:725`. Sole
  production caller `:1374` (the `if scalar_only:` arm of
  `plan_connection_relation`). Whole-package `rg` for the symbol: def `:701`,
  caller `:1374`, walker alias `:109` (no call through it anywhere), prose
  `:178` + walker `:1590`/`:1597`, test prose only. No second construction site.
- D2 `optimizer/nested_planner.py::_concrete_order_columns` (`:200`-`:222`):
  local concrete attnames from `order_by` with SKIP posture for related-span /
  unresolvable entries. Sole production caller D1 `:737`. Whole-package `rg`:
  def, caller, walker alias `:104` (read only by
  `test_concrete_order_columns_resolves_expression_relspan_and_attname_entries`
  via `walker` import), prose. No second order-column extractor for projection.
- D3 `optimizer/nested_planner.py::_order_entry_field_name` (`:187`-`:197`):
  name-half shim delegating at `:196` to the shared
  `plans.py::order_entry_name_and_direction`. Sole production caller D2 `:215`.
- D4 scalar-shape detector `scalar_only = not node_selections` (`:1285`) over
  the `_connection_node_selections` adapter (`:801`-`:819`, sole production
  caller `:1284`) over `selections.connection_node_children`. The only
  emptiness test on node children in the package: the second
  `connection_node_children` caller (`extension.py::_connection_node_child_selections`
  `:707`) never tests emptiness (root path always plans node children) — not a
  second detector.
- G2 threading: `_enable_only_for_operation` (walker `:145`-`:163`, sole
  `info.operation` reader for projection) derived once at
  `plan_optimizations` `:189`, threaded walker `:1844` ->
  `plan_connection_relation` `:1101` -> `:1378` -> D1 `:724`. One operation
  decision, no re-read at any writer.

Composed external owners (consumed, not family definitions):

- `plans.py::order_entry_name_and_direction` (`:813`-`:843`): single parser of
  the entry vocabulary. 5 consumers: D3 `:196`, `_concrete_order_terms` `:284`,
  `ends_in_unique_column` `:887`, `lateral_fetch.py::_order_columns` `:1197`,
  `connection.py` `:891`. One dash rule, one expression unwrap.
- `join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (`:152`-`:167`): attach-complete set. 2 production readers: D1 `:735`,
  `walker._ensure_connector_only_fields` `:1604`.
- `plans.py::effective_connection_order` (`:918`+): order ladder. 2 consumers:
  `:1361`, `connection.py::_finalize_queryset` `:1816` (cursor-parity pair).
- `plans.py::OptimizationPlan.apply` (`:333`-`:334`): plan-carried `.only()` writer.
- `plans.py::deferred_loading_of` (`:581`): shared deferred-loading unpack.

Writer census (`.only(*` CODE calls, package-wide `rg`, comments excluded):
exactly 3 — `plans.py:334` (plan-carried apply), `nested_planner.py:739`
(scalar-minimal construct), `nested_planner.py:773` (keyset-union extend) —
plus the defer-clear pair `:766`-`:767` inside `_extend_only_projection`.
Disjoint contracts; no fourth writer.

Consumers / downstream: `plan_connection_relation` `:1369`-`:1389` branch
(scalar arm vs keyset-extend arm); `single_parent_fetch.single_parent_spec`
inherits the projected queryset via `pristine_child_queryset` (`:156`) with
`with_total_count` refusal (`:139`, computed `:1460` from `FetchMode`);
`with_total_count`/`next_page_probe` derived `:1460`-`:1461`.

Oracles (independent, spell expectations): `:3611`
`test_scalar_only_window_projects_pk_connector_and_order_columns` (pk +
`shelf_id` + order column under `.only()`, `defer is False`), `:3640` generic
morph triple, `:5071` G2 gate (mutation -> default empty defer-set + window
annotation kept). None reads the owner to build its expectation.

Projections: spec-033 Decision 4/6 + spec-035 Decision 4 prose; docstrings at
D1/D2/D3/D4-adapter/gate.

### My change challenges (each must force count 1)

- W2-C1 fourth projected column kind (e.g. tenant discriminator) -> D1
  `:728`-`:739` only. Count 1.
- W2-C2 order-extraction posture change (skip vs fail-soft-None) -> D2 only;
  the tri-state sibling `_concrete_order_terms` (`:243`-`:300`) does NOT move
  (advisory UNKNOWN contract, documented at `:266`-`:268`). Count 1.
- W2-C3 new order-entry spelling (dash rule / new expression shape) -> the
  shared parser only; D3 inherits via `:196`. Count 1.
- W2-C4 new operation kind under G2 -> `_enable_only_for_operation` only; every
  writer inherits the threaded bool. Count 1.
- W2-C5 second scalar-shape detector hunt -> none: single `not
  node_selections` at `:1285`; extension `:707` is unwrap-without-detection.
  Count 1.
- W2-C6 second `.only()` construction site hunt -> none: 3 writers with
  disjoint contracts; a scalar-construction change touches `:739` only. Count 1.
- W2-C7 split the skip arm (related-span vs unresolvable diverge) -> D2
  `:214`-`:221` only. Count 1.

### Owner I would choose

`_project_scalar_only_window` stays the owner; D2/D3/D4 + the G2 owner are
already singly owned and composed by name. No second definition found on any
variation axis; no consolidation owed. Expectation: CONFIRM single-owned,
zero-edit — provided the artifact's exclusions each carry a real contract
difference + trigger and its fingerprints compare.

### Freshness fingerprints (Worker-2, all three states)

- WT `git hash-object`: nested_planner `b6ff0a0e`, join_taxonomy `aa289013`,
  plans `2e962ae2`, walker `4fd8077f` (4/4 match dispatch pins).
- HEAD `git rev-parse HEAD:<path>`: `8c3a45f5`, `8026dc8d`, `97a524e2`,
  `13e1be20` (4/4 match dispatch pins; HEAD `5c3496e0` unmoved).
- ITEM_BASELINE `807a7f09`: `git diff ITEM_BASELINE --name-only` =
  `docs/dry/dry-0_0_15.md` alone (plan edit, +94); artifact untracked
  (`git ls-files` absent); `git status --short | wc -l` = 477.
- All WT dirt in the 4 indexed files is concurrent work by content (truth-
  helper refactor + M2M advisory silence + lenient-readers refactor +
  `_child_link_is_virtual` addition; `prefetch_attach_columns` body,
  parser body, D1/D2/D3/D4 bodies, G2 bodies untouched — hunk positions
  recorded in my report). Read-for-census-only; never edited/reverted.

### Reconciliation (after reading `## Findings`) + verdict

Compared my trace above against W1's System trace / Verification / Findings /
Defects / Pending execution / Judgment line by line. Result: NO material
difference. Every load-bearing claim agrees:

- F1 owner + D1/D2/D3/D4 sites, roles, sole-caller edges (`:1374`, `:737`,
  `:215`, `:1284`), G2 threading (`:1844` -> `:1378` -> `:724`), parser
  5-consumer list, attach 2-reader list, `:1361` order read, walker aliases,
  pristine inheritance + `with_total_count` refusal: all independently
  re-derived by me at identical lines. AGREE.
- Writer census (3 `.only()` bodies + defer-clear inside E4): identical. AGREE.
- C1-C5 each count 1: agree; my extra W2-C5/C6/C7 stress (detector hunt,
  second-`.only()` hunt, skip-arm split) also count 1 with no landable owner —
  strengthens CONFIRM, adds no candidate.
- 11 exclusions E1-E7+E9-E12: I re-verified each body/trigger pair (E1
  None-vs-skip `:243`; E2 standing plan row `:445`; E3 lateral `:1177`;
  E4 `:742`-`:773`; E5 `plans.py:689` + `lateral_fetch.py:1216` read-only
  signatures; E6 `:334`; E7 `:1578`-`:1613`; E9 zero production callers;
  E10 nested scope; E11 loud strings-only `:192`-`:217`; E12 zero
  `plans` imports + `:1141`). Each carries a contract difference + trigger. AGREE.
- Missing E8: benign as recorded. My independent sweep maps every candidate I
  found onto W1's 11 rows; no dropped candidate exists to fill the label, and
  labels are arbitrary. No exclusion owed there.
- Oracle pins (`:3591`, `:3611`, `:2680`, `:2707` literal set, `:3640`,
  `:2712`, `:5071`, `:2314`, `:2022`; live `:7791`, `:7870`): all re-verified
  present with cited content; none reads the owner. AGREE.
- Fingerprints: all 4 indexed WT+HEAD pins + all 9 supporting + spec-033
  (`33b845a3` at the correctly stated `docs/SPECS/` path) + oracle-file states
  re-verified identical. Comparable; any change reopens. AGREE.
- Dirt attribution: identical (my hunk cites are WT-side `:31`/`:646`/`:1491`
  vs W1's HEAD-side `:28`/`:643`/`:1488` — same hunks, notation only).
  `prefetch_attach_columns` body, parser body, D1/D2/D3/D4/G2 bodies WT==HEAD.
  Concurrent work, untouched. AGREE.
- Defects "None": my spot-checks (D1/D2/D3/D4-adapter/G2 docstrings vs bodies;
  axis-6 omissions each with a contract source; dirt hunks) found no
  contradiction and no missing guard. The D1 docstring's
  "`_plan_connection_relation`" naming is loose but not contradictory (the
  annotations land downstream in that call chain) — below the defect bar. I
  record zero `(Worker-2)` defects. AGREE.
- Index rows: none owed (family row exists; no new family named; all
  sub-decisions owned; exclusions map to existing owners). AGREE.
- Pending "None": correct — inventory-shaped verdict (static-reviewed counts),
  behavioral probe execution-verified (W1 ran 1; I re-ran 3 green, shared
  venv), nothing lands so no failability proof owed, no gate owed. No `proof:`
  remains -> plain `verified`. AGREE.
- Cells: default executed (re-verified green by me); sharded/pg `inapplicable
  by construction` ENDORSED — the scalar path is lazy `.only()` construction +
  `_meta`/field-attribute/selection reads with no queryset execution, no
  alias, no dialect decision (no `supports_index_column_ordering` probe — that
  is the advisory family's, not this one's). Consistent with the f18 binary
  (DB-reaching -> `unverified`) and the accepted f28 precedent (pure
  derivation -> inapplicable).
- Structural gate "none owed": ENDORSED under the gate-only doctrine — the
  plausible bypass (second scalar-branch writer) admits no mechanical census
  beyond a bespoke existence test per helper (forbidden shape, f23 precedent);
  my re-run writer census (3 sites) is the fresh first-run check that the rule
  holds; in-tree behavior oracles pin the contract. Negative control reasoned,
  the prescribed shape for zero-edit with no gate.
- Zero-edit / empty tracked diff: re-verified — no `## Implementation`, 4/4
  WT pins match dispatch, `git diff ITEM_BASELINE --name-only` is the plan
  edit alone (+94), status 477 with the artifact untracked, HEAD unmoved.
- Lines 1-238 vs pre-completion read: accepted on Worker-0's validation — I
  hold no pre-completion copy, so I verify internal coherence instead (lines
  1-237 first-pass voice intact, C5 tail at 238-244 carries the explicit
  completion note, 489 W1 lines + my appended section). Coherent.

Cosmetic notes (scratch artifact, exempt — not spent on the verdict): line 47
says "F5 lines" where the cited ranges are F1's; my appended section header
follows Judgment without a blank line (append seam).

AGENTS.md check: tracked diff is the plan edit alone (Worker-0's ledger);
artifact is per-cycle scratch (raw `path:NN` allowed). No `.py` touched, so
ASCII-only / no-cover / provenance gates are vacuous. `uv run ruff format
--check` + `uv run ruff check` run on the 4 indexed files as the closest
meaningful gate: 4 already formatted, all checks pass. Type gates
whole-package: mypy clean (119 files), basedpyright 0 errors, check_any 130
allowed uses. Workspace copy at `dry/scalarwin-f29/verify` obtainable
(slot-3, fresh, shared unmoved); no source-mutating proof needed for
zero-edit. Probes ran in the shared venv per KNOWN (slots 1-3 venvs damaged).

No standing disagreement exists: W1 and W2 traces converge on every
load-bearing claim.

Verdict: CONFIRM single ownership holds. Zero-edit stands. No consolidation,
no test, no ledger row, no index row owed.
