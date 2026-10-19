# Review · Comments: `django_strawberry_framework/connection.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e6b022ba44f4e14da9e1825cea7047aa38d03298

## Trace

Read the whole live target (`django_strawberry_framework/connection.py`, 2285 lines:
module docstring, 45 symbol docstrings, 50 comment blocks per the
`review_inspect.py` census of 96 entries, 41 flagged) and the whole own test
module (`tests/test_connection.py`, 3203 lines: module docstring, 113
function docstrings, 4 class docstrings, 158 comment lines). No sibling axis
records existed at dispatch (only `rev-connection.md`, `Status: reviewing`);
required reading was AGENTS.md, START.md, REVIEW.md, worker-1.md, the plan,
and `rev-connection.md`. The target and its test module are dirty with
concurrent work versus HEAD, but byte-identical to ITEM_BASELINE
(`git diff ITEM_BASELINE -- <both paths>` is empty); every grade below is
against the live text at the fingerprints in this section.

Orientation: `review_inspect.py` overview + stripped source under
`docs/review/temp-tests/connection/comments/inspect/` plus
`connection.json` / `test_connection.json`.
`build_tree_md.py --list-docstrings` passes on the target and on
`tests/test_connection.py` (1 module, 0 breaking, each).
`check_citations.py --paths <file> --substrings --json` reports 17
citations, 0 violations in the target and 18 citations, 0 violations in the
test module. Provenance sweep (REVIEW.md pattern, regex mode) on the target
hits only kept spec-Decision pointers plus `now` (4), `no longer` (1),
`legacy` (1), each discharged below; on the test module only the leads
graded in Findings/Rejected. No `we`/`you`/`I` (one `I/O` false positive),
no `Tests that`/`Ensures` (113/113 clean), no `.py:NN`, no public symbol
without a docstring in either file.

Contract trace, each claim checked against its body and one real caller:
`_consume_window` / `_resolve_from_window` caller census (exactly one code
caller each; direct test callers are defensive-tail probes, not paths);
upstream `ListConnection.resolve_connection` dispatch
(`isinstance(nodes, (AsyncIterator, AsyncIterable)) and in_async_context()`)
and `QuerySet.__aiter__` (a plain queryset takes the async branch — no
coroutine is received anywhere); spec-033 SHIPPED with the async pipeline
an explicit Non-goal (the `until ... rides the 033 work` event came and
went); glossary `Meta.relation_shapes` entry (already carries the corrected
`until an async connection pipeline lands` clause F5 mirrors); spec-047
Decisions 7 (ceiling) and 9 (cooperative deadline); spec-032 Decision 9
(conformance suite incl. `relay_max_results`); spec-034 Decision 12
(composition is contract-pinning); spec-045 Decision 2 (`chain`-shadow
fail-closed, content-verified); spec-030 P3a/P3b (lazy-subpackage pins in
`tests/filters/test_finalizer.py` + `tests/orders/test_inputs.py`);
keyset `v1 column contract` vocabulary; `MAX_TYPE_WRAPPER_DEPTH`
Power-of-Ten cap; `ledger.add(set_class)` orphan registration; the four
base guards + Relay guard (4+1, matching `relay.py`'s four-plus-fifth);
every shipped connection target carrying at least one sidecar
(root fields plus `connection`/`both` relation shapes, kanban
`DecisionType` included); package-root exports; fakeshop dogfood
(`products/schema.py`, `library/schema.py`); strictness default `off`;
`effective_connection_order` caller census (exactly the two order sites);
`_TOTAL_COUNT_ATTR` single writer; `prepared_resolver_source` guard order;
`post_process_queryset_result_sync` awaitable rejection;
`_validate_djangotype_target` node-field sharing (via
`_validate_relay_djangotype_target`); `registry.clear()` subsystem replay
(no `ImportError` guard survives); 83 other-module prose units extracted to
`other-prose.txt` (10 write-pipeline substring false positives excluded),
every genuine one graded in Findings/Rejected/Routed.

Cells: no workspace run was needed — every instrument above is static
(source reads, AST census, citation resolution, spec/glossary/upstream
comparison). Sharded and pg are inapplicable by construction to this
Comments pass (no database-reaching probe; all Proofs are static `grep -c`
plus grade judgments; Worker-2's prose edits owe `--code-digest`
identity, not cell runs). Cells unverified: none.

Fingerprints (`git hash-object` full; upstream sha256 12-char):
target `68d1ea2c325eb8a3c34d34df7bc6125ad736ec16`;
`tests/test_connection.py` `8e08b23fbf7eee84a94ab406d8713855056087a1`;
`list_field.py` `450e87cd`, `utils/connections.py` `efcf749a`,
`utils/querysets.py` `8fc556d5`, `utils/typing.py` `a672cd6b`,
`utils/inputs.py` `b5af8255`, `filters/__init__.py` `86b25818`,
`registry.py` `492654d2`, `keyset.py` `279ad7b0`, `relay.py` `e75e2b66`,
`resource_policy.py` `cc3f9d80`, `utils/relations.py` `05ff55b0`,
`__init__.py` `0ef72601`, `optimizer/extension.py` `39a8739c`,
`optimizer/walker.py` `d5759ef8`, `optimizer/selections.py` `b189fa15`,
`optimizer/plans.py` `33140a76`, `optimizer/nested_planner.py` `d32d1b7b`,
`optimizer/nested_fetch.py` `1678609e`, `optimizer/lateral_fetch.py`
`db1ea315`, `optimizer/single_parent_fetch.py` `e995270a`,
`types/base.py` `dc67f084`, `types/finalizer.py` `b9d8acb2`,
`filters/factories.py` `ad5634c4`, `orders/factories.py` `b9fd62bc`,
`orders/sets.py` `60859f2d`, `mutations/fields.py` `0e4d5ed1`;
`tests/test_keyset_connection.py` `70db0483`,
`tests/test_relay_connection.py` `a4769a3d`, `tests/test_registry.py`
`48af782f`, `tests/optimizer/test_plans.py` `1e09d6d8`,
`tests/types/test_base.py` `bb56c89b`,
`tests/filters/test_finalizer.py` `4bbcfaab`,
`tests/orders/test_inputs.py` `be8b48a3`,
`tests/utils/test_connections.py` `65d54027`,
`test_connection_pagination_api.py` `d6a4f720`,
`test_keyset_api.py` `305b972f`, `test_library_api.py` `2cd1b6dd`,
`test_products_api.py` `fe78cf9d`, `test_multi_db.py` `893956aa`,
`test_kanban_api.py` `7dcb922b`, `library/schema.py` `9682db07`,
`products/schema.py` `04a5afe3`, `kanban/schema.py` `fd432eb3`,
`config/schema.py` `303ea2da`, `docs/GLOSSARY.md` `3413edc3`,
spec-032 `1e96ad41`, spec-033 `5c6b9a8b`, spec-034 `788245cb`,
spec-045 `97561f2d`, spec-047 `844eab53`; upstream
`strawberry/relay/types.py` `2b9bd850dc3a`, Django `query.py`
`5e86af673328` (Django 6.1). A finding's Freshness lists only files
beyond these: none.

## Findings

### High

None.

### Medium

- Observation: two docstrings claim the window derivation is shared by
  `both resolve_connection paths`. The production call graph has exactly
  one chain: `DjangoConnection.resolve_connection` calls `_consume_window`
  once (line 1324), which calls `_resolve_from_window` once (line 682).
  No second resolve path exists (sync/async converge before
  `_consume_window`; the direct test callers are defensive-tail probes,
  not paths). A reader hunting the second path finds nothing.
- Evidence: package-wide caller census of both symbols (only prose
  mentions plus the single code call site each); the `keyset_state`
  branches inside `_resolve_from_window` are the sharing the sentence
  should name (offset + keyset windows through one derivation).
- Impact: miscounted sharing on the file's two central docstrings; a
  future editor may invent or preserve a phantom second path.
- Severity: Medium (stale count on internal code, two sites).
- Recommendation: give `both` its true referent at each site; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c 'both ``resolve_connection`` paths'
  django_strawberry_framework/connection.py` prints `0` (2 today, lines
  303 and 623); both rewritten sentences earn grade true (each names a
  sharing the call graph and the branch structure verify).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_from_window`
  + `::_consume_window`.
- Grade: stale.
- Text-before:
  `The single edge / cursor / pageInfo / totalCount derivation shared by both resolve_connection paths (spec-033 Decision 5).`
  and
  `Shared entry from both resolve_connection paths.`
- Text-after:
  `The single edge / cursor / pageInfo / totalCount derivation shared by the offset and keyset window branches (spec-033 Decision 5).`
  and
  `Single entry from resolve_connection for both wrapper and non-wrapper sources.`

- Observation: the `_resolve_from_window` docstring frames the keyset
  backend as future: `the resolve-side surface a future keyset-cursor
  backend inherits: it makes _dst_row_number page-relative ... and
  derives hasNextPage from this same overfetch, and hasPreviousPage from
  "a cursor was supplied"`. That backend exists in this same function:
  keyset windows arrive page-relative (`first_rn > 1 can never fire`),
  `hasNextPage` derives from the probe overfetch or the seek count, and
  `hasPreviousPage` from `keyset_seek_supplied or first_rn > 1`.
- Evidence: the `keyset_state` / `keyset_after` parameters and every
  `keyset_seek_supplied` branch of the function body; the page-relative
  comment block (lines 576-581) stating the present behavior the
  `future` sentence defers.
- Impact: a reader believes keyset windows are unbuilt and misreads the
  live branches as speculative scaffolding.
- Severity: Medium (stale docstring on internal code).
- Recommendation: recast in the present tense the body proves; see
  text-after. The mirror sentence in
  `utils/connections.py::split_window_rows` is a Routed lead, not part
  of this fix.
- Must not change: n/a.
- Proof: `grep -c "keyset-cursor backend"
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  337; the `a future` half sits at the end of line 336, so the Proof
  keys on the unbroken half); the rewritten sentence earns grade true
  (page-relative numbering, overfetch `hasNextPage`, cursor-supplied
  `hasPreviousPage`, all as the body computes them).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_from_window`.
- Grade: stale.
- Text-before:
  `split_window_rows + the hasNextPage derivation here are the resolve-side surface a future keyset-cursor backend inherits: it makes _dst_row_number page-relative (so row_number < total no longer holds) and derives hasNextPage from this same overfetch, and hasPreviousPage from "a cursor was supplied".`
- Text-after:
  `split_window_rows + the hasNextPage derivation here are the resolve-side surface the keyset-cursor backend rides: it makes _dst_row_number page-relative (so row_number < total does not hold there) and derives hasNextPage from this same overfetch, and hasPreviousPage from "a cursor was supplied".`

- Observation: the `_resolve_keyset_connection` docstring's dispatch
  sentence says `an async field receives a coroutine that iterates with
  the async engine and counts via acount`. No coroutine is received
  anywhere on this path. The code mirrors upstream exactly:
  `isinstance(nodes, (AsyncIterator, AsyncIterable)) and
  async_execution()`, and a Django `QuerySet` is async-iterable (it
  defines `__aiter__`), so the same lazy queryset iterates with
  `async for` and counts via `acount()` under async execution.
- Evidence: the `_resolve_async` branch (lines 1140-1148) and the
  count-only async branch (line 1095); upstream
  `ListConnection.resolve_connection`
  (`isinstance(nodes, (AsyncIterator, AsyncIterable)) and
  in_async_context()`); `QuerySet.__aiter__` in the installed Django
  sources.
- Impact: wrong stated mechanism for the keyset sync/async fork (DRY
  principle 10: worse than none); a reader hunting the coroutine's
  producer finds nothing.
- Severity: Medium (stale docstring on internal code).
- Recommendation: state the actual dispatch (async-iterable queryset +
  execution color); see text-after.
- Must not change: n/a.
- Proof: `grep -c "receives a coroutine"
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  1027); the rewritten sentence earns grade true (async-iterable source,
  async-engine iteration, `acount`, sync materialization otherwise).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_keyset_connection`.
- Grade: stale (wrong stated mechanism).
- Text-before:
  `Sync/async dispatch mirrors ListConnection.resolve_connection: a sync field materializes the lazy queryset in the resolver's context; an async field receives a coroutine that iterates with the async engine and counts via acount.`
- Text-after:
  `Sync/async dispatch mirrors ListConnection.resolve_connection: the queryset is async-iterable, so under async execution the page iterates with the async engine and counts via acount; otherwise the sync path materializes it in the resolver's context.`

- Observation: the `_resolve_order_path_field` in-function import
  comment claims `mirrors the file's defensive-Django-imports idiom`.
  No such file idiom exists. The module already imports `django.db` at
  top level (line 53), which transitively imports
  `django.core.exceptions`, so the local import defends against nothing;
  the file's only other in-function import (filters/orders, serving the
  lazy-subpackage contract) is not a Django import at all.
- Evidence: the top-level `from django.db import models`; the
  in-function import census of the file (exactly two sites, only this
  one Django); no cycle is possible (Django never imports this package).
- Impact: wrong stated reason (DRY principle 10: worse than none);
  future editors preserve a meaningless placement rule.
- Severity: Medium (stale comment on internal code).
- Recommendation: delete the comment line; the import itself is
  behavior-neutral either way (hoisting is a Mechanics call, see
  Cross-axis).
- Must not change: n/a.
- Proof: `grep -c "defensive-Django-imports"
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  833).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_order_path_field`.
- Grade: stale (wrong stated reason).
- Text-before:
  `# In-function import mirrors the file's defensive-Django-imports idiom.`
- Text-after: (delete the line).

- Observation: the `_build_relation_connection_resolver` docstring dates
  the async posture `(0.0.9)` and lifts it `until an async connection
  pipeline rides the 033 work`. Spec-033 is SHIPPED (all seven slices
  final-accepted) with the async pipeline an explicit Non-goal
  (`Async connection pipeline. ... The window planning below is
  sync-pipeline planning; the async story is untouched`), so the waited
  event came and went while the posture stands. A reader may conclude
  the posture already lifted.
- Evidence: spec-033 `Status:` line + Non-goals section; the resolver
  body is still sync-only (`def _resolve`, `_pipeline_sync`);
  the glossary `Meta.relation_shapes` entry already carries the
  corrected clause (`until an async connection pipeline lands`), which
  the text-after mirrors verbatim.
- Impact: version-anchored stale `until` on the posture readers consult
  before choosing `relation_shapes = {"<field>": "list"}`.
- Severity: Medium (stale docstring on internal code).
- Recommendation: drop the version anchor and the spent `until` clause
  for the glossary's landing clause; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'rides the ``033`` work'
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  2157) and `grep -c "posture (0.0.9)"
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  2152); the rewritten paragraph earns grade true (sync-only, no
  `resolver=` seam, `SyncMisuseError`, list recourse, landing clause).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_build_relation_connection_resolver`.
- Grade: stale.
- Text-before:
  `Async-get_queryset posture (0.0.9): this is sync-pipeline-only and has no resolver= seam (the documented escape a *root* connection uses for an async hook), so a Relay target whose get_queryset is async def raises SyncMisuseError on every query of its synthesized <field>Connection; relation_shapes = {"<field>": "list"} is the recourse until an async connection pipeline rides the 033 work.`
- Text-after:
  `Async-get_queryset posture: this is sync-pipeline-only and has no resolver= seam (the documented escape a *root* connection uses for an async hook), so a Relay target whose get_queryset is async def raises SyncMisuseError on every query of its synthesized <field>Connection; relation_shapes = {"<field>": "list"} is the recourse until an async connection pipeline lands.`

### Low

- Observation: the `_build_relation_connection_resolver` docstring names
  the board card (`the cooperation seam DONE-033-0.0.9's window-pagination
  planning uses`). Card ids are board residue, banned from code prose.
- Evidence: read verbatim (line 2096).
- Impact: bounded; process attribution where the mechanism alone belongs.
- Severity: Low.
- Recommendation: drop the card id; see text-after. Expect `deferred`
  if no higher finding touches this file (five Mediums do, so it rides).
- Must not change: n/a.
- Proof: `grep -c "DONE-033" django_strawberry_framework/connection.py`
  prints `0` (1 today); the rewritten clause earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_build_relation_connection_resolver`.
- Grade: process provenance (board residue).
- Text-before:
  `keeping Django's prefetch caches reachable as the cooperation seam DONE-033-0.0.9's window-pagination planning uses`
- Text-after:
  `keeping Django's prefetch caches reachable as the cooperation seam window-pagination planning uses`

- Observation: the same docstring calls the shared window attr `the
  shared legacy attr`. Both attrs are live schemes (per-key for
  divergent aliases, shared otherwise); the shared attr is the common
  path, not a deprecated one, so `legacy` mislabels it.
- Evidence: the probe code (per-key first, shared fallback, lines
  2170-2175); both schemes planned by the walker today.
- Impact: bounded; a reader may treat the common path as deprecated.
- Severity: Low.
- Recommendation: drop the adjective; see text-after. The twin in
  `optimizer/nested_planner.py` (`legacy shared-to_attr request`) is a
  Routed lead.
- Must not change: n/a.
- Proof: `grep -c "legacy attr"
  django_strawberry_framework/connection.py` prints `0` (1 today, line
  2114; `shared` ends line 2113, so the Proof keys on the unbroken
  half); the rewritten clause earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_build_relation_connection_resolver`.
- Grade: stale (inaccurate label).
- Text-before:
  `then falls back to the shared legacy attr`
- Text-after:
  `then falls back to the shared attr`

- Observation: the `_resolve_from_window` docstring carries a
  spec-revision history clause (`that is the scheme an earlier spec
  revision described`). Spec-draft archaeology is process provenance;
  the present-tense invariant after the semicolon carries the whole
  design fact.
- Evidence: read verbatim (lines 356-359).
- Impact: bounded; history no reader can act on (no revision named).
- Severity: Low.
- Recommendation: keep the invariant, drop the history; see text-after.
- Must not change: n/a.
- Proof: `grep -c "an earlier spec revision"
  django_strawberry_framework/connection.py` prints `0` (1 today);
  the rewritten parenthetical earns grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_from_window`.
- Grade: process provenance (spec-revision history).
- Text-before:
  `(that is the scheme an earlier spec revision described; neither upstream strawberry-django nor this package's port overwrites the forward row number - both keep it forward and use a separate reversed annotation only for the plan-time __lte filter)`
- Text-after:
  `(neither upstream strawberry-django nor this package's port overwrites the forward row number - both keep it forward and use a separate reversed annotation only for the plan-time __lte filter)`

- Observation: the `_KeysetPage` class docstring says `spec-algorithm`.
  Bare `spec` vocabulary with no number; the file's own sibling
  docstrings say `the Relay pagination algorithm ... in the value
  domain`.
- Evidence: read verbatim (line 946); contrast
  `_resolve_keyset_connection` (`The Relay pagination algorithm, in the
  value domain`) and the `has_next_page` / `has_previous_page`
  value-domain docstrings.
- Impact: bounded; vague pointer where exact file vocabulary exists.
- Severity: Low.
- Recommendation: adopt the file's value-domain vocabulary; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "spec-algorithm"
  django_strawberry_framework/connection.py` prints `0` (1 today);
  the rewritten first line earns grade true (description, names the
  inputs).
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_KeysetPage`.
- Grade: process provenance (vague bare-spec vocabulary).
- Text-before:
  `One fetched keyset page plus the spec-algorithm pageInfo inputs.`
- Text-after:
  `One fetched keyset page plus the value-domain pageInfo inputs.`

- Observation: the two `resolve_connection` comments carry bare
  `(spec-047)` parentheticals (the bare form REVIEW.md names
  provenance). Exact Decision upgrades exist and are verified:
  Decision 7 is the ceiling comment's subject verbatim, Decision 9 the
  deadline comment's.
- Evidence: spec-047 `### Decision 7 — The policy is a CEILING over
  relay_max_results, never a replacement` and `### Decision 9 — The
  execution deadline is cooperative, and says so`.
- Impact: bounded; kept Decision pointers replace bare spec tags.
- Severity: Low.
- Recommendation: attach each pointer to its Decision; see text-after.
- Must not change: n/a.
- Proof: `grep -c '(spec-047)' django_strawberry_framework/connection.py`
  prints `0` (2 today, lines 1302 and 1308); both rewritten comments
  earn grade true.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`.
- Grade: process provenance (bare spec tags; exact upgrades verified).
- Text-before:
  `(spec-047)` (ceiling comment) and `(spec-047)` (deadline comment).
- Text-after:
  `(spec-047 Decision 7)` and `(spec-047 Decision 9)`.

- Observation: `tests/test_connection.py::test_relay_max_results_cap`
  first line ends `(spec-032)`, the bare form. The exact upgrade is
  verified: spec-032 Decision 9 (`Cursor mechanics stay delegated to
  Strawberry; this card pins the conformance contract`) pins
  `relay_max_results` capping page sizes and owns the conformance
  suite this test belongs to (the spec's matrix lists this test by
  name under `relay_max_results`).
- Evidence: spec-032 Decision 9 text (`with relay_max_results ...
  capping page sizes ... What this card adds is the conformance
  suite`) plus the Slice-4 matrix row naming
  `test_relay_max_results_cap`.
- Impact: bounded; kept Decision pointer.
- Severity: Low.
- Recommendation: attach the pointer; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'caps any single page (spec-032)'
  tests/test_connection.py` prints `0` (1 today, line 1222); the
  rewritten first line earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_connection.py::test_relay_max_results_cap`.
- Grade: process provenance (bare spec tag; exact upgrade verified).
- Text-before:
  `strawberry_config(relay_max_results=N) caps any single page (spec-032).`
- Text-after:
  `strawberry_config(relay_max_results=N) caps any single page (spec-032 Decision 9).`

- Observation: the root-connection fence banner opens `spec-033 Slices
  1-2 (DONE-033-0.0.9):`. Slice numbering and card ids are both banned
  residue; the fence (DoD item 12) needs neither.
- Evidence: read verbatim (lines 2120-2126). The remaining banner
  (fence scope, Decision 9 / Decision 5 anchors, DoD item 12) is true
  and stays.
- Impact: bounded; plan residue in a standing fence marker.
- Severity: Low.
- Recommendation: re-head the banner on the spec + DoD item; see
  text-after.
- Must not change: the fence history (`stayed GREEN UNMODIFIED ...`,
  graded true, R4) and the Decision / DoD anchors.
- Proof: `grep -c "DONE-033-0.0.9" tests/test_connection.py` prints `0`
  (1 today); the rewritten banner earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_connection.py` fence banner (lines 2120-2126).
- Grade: process provenance (slice numbering + board residue).
- Text-before:
  ```text
  # spec-033 Slices 1-2 (DONE-033-0.0.9): root-connection no-regression fence. The
  # shipped root-connection planning pins here (edges { node } extraction ->
  # select_related / Prefetch on the pre-slice queryset) stayed GREEN UNMODIFIED
  # through the helper consolidation (Decision 9) and the fast-path addition
  # (Decision 5), which touch only the NESTED half. No new tests are required
  # here; this marker records the fence (DoD item 12, "no root-connection
  # regression").
  ```
- Text-after:
  ```text
  # spec-033 root-connection no-regression fence (DoD item 12, "no root-connection
  # regression"). The shipped root-connection planning pins here (edges { node }
  # extraction -> select_related / Prefetch on the pre-slice queryset) stayed GREEN
  # UNMODIFIED through the helper consolidation (Decision 9) and the fast-path
  # addition (Decision 5), which touch only the NESTED half. No new tests are
  # required here; this marker records the fence.
  ```

- Observation: the cascade banner carries a bare `(spec-034)` plus a
  separately-bare `(Decision 12)`. Both halves are verified
  (Decision 12 is `Connection / node / list composition is
  contract-pinning, not new code`, exactly the banner's `No
  connection.py source change is involved`); merge them into one kept
  pointer.
- Evidence: spec-034 Decision 12 heading + the banner's contract claim.
- Impact: bounded; one kept pointer replaces two bare halves.
- Severity: Low.
- Recommendation: merge; see text-after.
- Must not change: n/a.
- Proof: `grep -c 'composition pin (spec-034)'
  tests/test_connection.py` prints `0` (1 today, line 2130); the
  rewritten banner earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_connection.py` cascade banner (lines 2130-2132).
- Grade: process provenance (bare spec tag; exact upgrade verified).
- Text-before:
  `Connection <-> cascade composition pin (spec-034). No connection.py source change is involved: the pipeline already applies get_queryset (where the cascade lives) before filter / order / slice (Decision 12).`
- Text-after:
  `Connection <-> cascade composition pin (spec-034 Decision 12). No connection.py source change is involved: the pipeline already applies get_queryset (where the cascade lives) before filter / order / slice.`

- Observation: the post-`OrderSet` seal inventory comment reads `the
  connection takes the Relay window on whatever ordering returned`.
  The relative clause is malformed (missing the agent: whatever
  ordering the override returned).
- Evidence: read verbatim (lines 1914-1915).
- Impact: bounded clarity in the seal's rationale sentence.
- Severity: Low.
- Recommendation: restore the agent; see text-after.
- Must not change: n/a.
- Proof: `grep -c "whatever ordering returned" tests/test_connection.py`
  prints `0` (1 today); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `tests/test_connection.py` post-`OrderSet` seal comment
  (lines 1911-1916).
- Grade: stale (ungrammatical as written; not what the author means).
- Text-before:
  `The connection takes the Relay window on whatever ordering returned, so an unsealed result is a wrong page or a foreign row rather than a loud error - each row proves the seal rejects instead.`
- Text-after:
  `The connection takes the Relay window on whatever ordering the override returned, so an unsealed result is a wrong page or a foreign row rather than a loud error - each row proves the seal rejects instead.`

- Observation: `test_library_api.py::test_anonymous_inline_fragment_under_connection_field_resolves`
  opens its body `Regression for the optimizer-folder High.` A severity
  label plus review attribution in standing prose; both banned.
- Evidence: read verbatim (line 4469). No competing `High` concept
  exists (the only other occurrence, `test_glossary_api.py:211`, is the
  same review-residue locution on an optimizer subject — twin, for its
  item, not this fix).
- Impact: bounded; review residue where the crash account alone belongs.
- Severity: Low.
- Recommendation: open on the crash account directly; see text-after.
- Must not change: the `Pre-fix` crash history and the `now routes`
  mechanism (both graded true, R3/R4).
- Proof: `grep -c "optimizer-folder High"
  examples/fakeshop/test_query/test_library_api.py` prints `0` (1
  today); the rewritten opening earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_library_api.py::test_anonymous_inline_fragment_under_connection_field_resolves`.
- Grade: process provenance (severity label + review attribution).
- Text-before:
  `Regression for the optimizer-folder High. Pre-fix, a query placing an anonymous inline fragment`
- Text-after:
  `Before the fix, a query placing an anonymous inline fragment`

- Observation: the same docstring says the package `primes
  info.selected_fields with it before the connection resolver runs`.
  Under the plain reading (`the connection resolver` = the field's
  synthesized resolver) that is false: the prime runs inside
  `DjangoConnection.resolve_connection` (connection.py line 1323),
  after the synthesized resolver already returned `nodes`. The
  file's own sibling
  (`test_anonymous_inline_fragment_with_total_count_resolves`) states
  it precisely (the single prime in `resolve_connection`, ahead of
  both reads).
- Evidence: `resolve_connection` body order (guard, deadline, prime,
  `_consume_window`); the synthesized resolver returns before
  `resolve_connection` is entered; `prime_selected_fields` has exactly
  one production caller.
- Impact: bounded; ambiguous referent with a false plain reading,
  contradicted by the precise sibling one screen down.
- Severity: Low.
- Recommendation: name both ends the way the sibling does; see
  text-after.
- Must not change: n/a.
- Proof: `grep -c "before the connection resolver runs"
  examples/fakeshop/test_query/test_library_api.py` prints `0` (1
  today, line 4478); the rewritten sentence earns grade true.
- Freshness: none beyond Trace.
- Symbol: `examples/fakeshop/test_query/test_library_api.py::test_anonymous_inline_fragment_under_connection_field_resolves`.
- Grade: stale (ambiguous referent; false under the plain reading).
- Text-before:
  `The package now routes its own conversion through the anonymous-safe ast_to_converted_selections adapter and primes info.selected_fields with it before the connection resolver runs, so both shapes - the anonymous fragment directly under the connection field and one nested down at the node level - resolve and return the seeded genre names.`
- Text-after:
  `The package now routes its own conversion through the anonymous-safe ast_to_converted_selections adapter, and DjangoConnection.resolve_connection primes info.selected_fields with it before Strawberry's ListConnection.resolve_connection reads it, so both shapes - the anonymous fragment directly under the connection field and one nested down at the node level - resolve and return the seeded genre names.`

## Rejected

- R1 — Non-imperative first lines. `_connection_field_requested`
  (`Whether ...`) joins the 66-site package predicate convention;
  `_resolve_keyset_connection` (`The ...`) joins 149 `The`-opening
  function docstrings; `DjangoConnectionField` (`Factory for ...`)
  joins the 4-site field-factory family (list, connection, two node
  fields); `_pipeline_async` (`Async sibling of ...`) joins the 10-site
  async-twin family; the `_KeysetPage` properties read as attributes.
  Per the conf.py precedent, package and family conventions beat the
  imperative rule here; rewriting one site would make it inconsistent.
  Trigger: a maintainer decision enforcing mood package-wide.
- R2 — Module docstring `Target release: 0.0.9.` Seven-module standing
  convention (`list_field.py` 0.0.7, five 0.0.14 modules); the spec
  pointer beside it is kept. Trigger: the convention retired.
- R3 — Temporal language serving a present fact (no process artifact
  named): `now PROVES` (target lines 308, 426: the marker invariant),
  `now lives in optimizer/plans.py` (line 139: canonical location +
  one-source invariant), `The read is now gated` (test line 796),
  `the cooperation point the field now owns` (test line 1529, quoting
  the spec's framing), `today's SDL shape` (line 1389: current shipped
  shape), `shipped description-less` / `shipped surface` (present
  contract). Same accepted shape as the verified `used to ... It is
  now` and `no longer ... rather than the old` records. Trigger: a
  rewrite to pure present tense.
- R4 — History serving a present design fact: `matching a "totalCount"
  literal made this predicate answer False` (converter rationale, the
  guard-order precedent's twin); `Both were spelled out twice ... was a
  two-site edit` (preempts re-splitting the sidecar gate); `Re-export
  the hoisted ... under its original private name` (the back-compat
  re-export's reason); `the spec-032 concrete-class pin` /
  `the bug spec-032 records` / `the bug spec-032 uncovered`
  (attributive regression rationale, not detachable tags);
  `spec-030 ... Open Question` (the settled-question pointer motivating
  the test); `Regression pin ...` / `Pre-fix ...` / `The old raw
  order_by ...` / `stayed GREEN UNMODIFIED through ...` (regression
  motivation with true behavioral claims). Trigger: the design changing
  under any of them.
- R5 — Bare Decision numerals with the anchor on the reader's path:
  module docstring `Decision 3/4/5/6/7/10` (spec-030 named at line 3);
  `Steps 5-6 of the Decision 7 pipeline` (same file's module anchor);
  test `(Decision 2)` (spec-045 section banner 120 lines up in the same
  section; content-verified against Decision 2's `chain`-shadow text);
  live-tier `(Decision 3)` (resolvable via the cited
  `_guard_first_and_last`, whose own docstring says spec-030
  Decision 3); test `B5 plan-introspection shape` (spec-004 B5 named by
  content plus its file; the spec-053 B5 is a build batch of different
  content, so no ambiguity). Trigger: an anchor removed or a second
  same-named Decision.
- R6 — Test `__getitem__-only legacy sequence` (line 959). `legacy`
  classifies the protocol generation and matches the test double's own
  class name (`LegacySequence`); rewording without renaming would
  confuse. Trigger: the class renamed (a Mechanics change).
- R7 — `The through-schema tests are mandatory because
  ConnectionExtension.resolve wraps the resolver.` Durable testing
  constraint, true (the extension layer is untestable helper-direct).
  Trigger: none (constraint stands).
- R8 — Test-name pins in production docstrings (`Pins: test_...`,
  `test_first_and_last_guard_on_generated_subclass passes a minimal
  info`). Stable identifiers, not line numbers. Trigger: a pinned test
  renamed.
- R9 — `user-mandated` (live loan-connection docstring). Unusual
  adjective, but style only; every behavioral claim around it is true
  and the flag exists as described. Trigger: none.
- R10 — Spot-verified true vocabulary, each checked against its source:
  `v1 column contract` (keyset.py), `Power-of-Ten-capped peel`
  (`MAX_TYPE_WRAPPER_DEPTH`), `search is 0.1.2` (glossary contract),
  `rung 3` (test-tier ladder vocabulary), four-plus-Relay guard counts
  (base validator: is-type, is-subclass, registered-canonical,
  resolver-callable; relay.py's four-plus-fifth agrees), negative-cursor
  slice arithmetic (pinned by package + nested tests), the
  `_TOTAL_COUNT_ATTR` single writer (one `setattr`), orphan-ledger
  registration (`ledger.add`), lazy-subpackage
  pins (subprocess assertions), package-root exports, fakeshop dogfood,
  `no shipped connection omits both sidecars` (full root + synthesized
  census), every live pin named by the own-test module docstring.
  Trigger: the named source changing.
- R11 — Out of grading scope: example-app prose (`products/schema.py`
  module + `Query`, `library/schema.py::LoanType` — example modules are
  neither the target, own tests, nor test modules; read, true, not
  graded); nested private resolvers without docstrings (no looks-for
  entry requires them); the section separator banner and the `noqa`
  usage note (no prose claims). Trigger: none in this flow.

## Routed leads

- Routed: `django_strawberry_framework/utils/connections.py::split_window_rows`
  — `This helper plus the hasNextPage derivation in
  connection.py::_resolve_from_window are the resolve-side surface a
  future keyset-cursor backend (which makes rn page-relative) has to
  touch`. Same staleness as F2 (the page-relative keyset backend is
  live in `_resolve_from_window` today). Owner: the
  `utils/connections.py` item.
- Routed: `django_strawberry_framework/optimizer/selections.py::prime_selected_fields`
  — `connection.py::DjangoConnection.resolve_connection calls this
  immediately after the first + last guard`. The spec-047 deadline
  check (`check_deadline(info)`) sits between the guard and the prime
  (connection.py lines 1307-1323); only `immediately` is false (the
  `ahead of both reads` half still holds). Owner: the
  `optimizer/selections.py` item.
- Routed: `django_strawberry_framework/optimizer/nested_planner.py`
  `_divergent_key_windows` — `the single-window scheme sends the legacy
  shared-to_attr request`. Twin of L2 (`legacy` mislabels the live
  common path). Owner: the `optimizer/nested_planner.py` item.
- Routed: `django_strawberry_framework/list_field.py::_validate_djangotype_target`
  — `Shared by DjangoListField and DjangoConnectionField (and any future
  node field)`. The node fields exist and share it today
  (`relay.py::_validate_node_target` wraps
  `_validate_relay_djangotype_target`, which delegates here), so the
  future framing is spent. Owner: the `list_field.py` item.
- Routed: `tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`
  — the whole docstring describes an `except ImportError` guard with a
  cycle-safe local import inside `clear()` (spec-030 P3b). No such guard
  survives: `clear()` replays `iter_subsystem_clears()` callbacks
  (`clear_connection_type_cache` registers via
  `register_subsystem_clear`), so the `sys.modules` poisoning is inert
  and the `skips that block` mechanism is fiction. Primary subject is
  `registry.clear()` in the registry item's own test module, so the
  registry Comments pass owns the rewrite (order/relay twin tests
  likely share the staleness). Owner: the `registry.py` item.

## Cross-axis (for Mechanics)

- Observation: the `_resolve_order_path_field` local import
  (`from django.core.exceptions import FieldDoesNotExist`, line 834)
  has no stated reason left once F4 deletes its false idiom comment.
  `django.core.exceptions` is already imported transitively via the
  module's top-level `from django.db import models`, and no cycle is
  possible (Django never imports this package), so hoisting it to
  module scope is behavior-neutral.
- Evidence: the top-level Django import; the two-site in-function
  import census; F4.
- Impact: one unjustified local import; hoisting removes a misleading
  placement precedent.
- Severity: Low.
- Recommendation: hoist to the top-level Django import group, or record
  why it stays local.
- Must not change: import behavior (no new cycle, lazy-subpackage
  contract intact).
- Proof: `grep -c "from django.core.exceptions import FieldDoesNotExist"
  django_strawberry_framework/connection.py` prints `1` at top level
  (today nested at line 834); `uv run python scripts/build_tree_md.py
  --list-docstrings django_strawberry_framework/connection.py` still
  prints `ok`.
- Freshness: none beyond Trace.
- Symbol: `django_strawberry_framework/connection.py::_resolve_order_path_field`.
- Grade: n/a (mechanics placement; the prose defect is F4).
- Text-before: the line-834 nested import.
- Text-after: the same import in the top-level Django group.

No Performance finding arose from this pass (prose-only review; no
timing, counting, or bench instrument applies to a docstring grade).

Handoff: I graded every docstring and comment in the target (46
docstrings, 50 comment blocks) and its own test module whole (118
docstrings, 158 comment lines), plus every other-module docstring
mentioning the target's symbols (83 extracted units: package, package
tests, live tier, example schemas): 5 Mediums (F1 phantom second
resolve path, F2 future-keyset framing, F3 coroutine dispatch, F4
false import idiom, F5 spent until-033 posture) and 11 Lows (L1 card
id, L2 legacy label, L3 spec-revision history, L4 spec-algorithm, L5
bare spec-047 tags, L6-L9 test-file pointers/grammar, L10-L11 live-tier
provenance/ambiguity), one Mechanics cross-axis lead (the import hoist
F4 enables), and five Routed leads. Everything else grades true,
including all 35 path::Symbol citations (0 violations), all kept
spec-Decision pointers (each verified against its spec's text), the
mood families (R1 census counts), and the temporal/history clauses
(R3/R4, calibrated to the verified Whether/no-longer/used-to records).
Observed true for owning items, not graded here: `NO LONGER` x2 +
`formerly` in `utils/connections.py`, the `test_relay_connection.py`
temporal wordings (`no longer plans`, `anymore`, `USED to ... now`),
its bare `(Decision 5)` pointer quality, `types/base.py`'s `for 0.0.9`
dating (fact still true), the finalizer's `silently` (true
implicit/explicit contrast), and the `test_glossary_api.py:211`
optimizer-folder-High twin (provenance, optimizer subject). No
workspace runs (all instruments static); scratch under
`docs/review/temp-tests/connection/comments/` (`inspect/`,
`connection.json`, `test_connection.json`, `citations.json`,
`other-prose.txt`, `test_prose_index.txt`); live text equals
ITEM_BASELINE on both graded files. On verify: F1's fix must keep the
spec-033 Decision 5 anchor while naming a sharing the call graph
verifies; F5's must match the glossary's landing clause; L7/L10/L11
must keep their true surrounding history; every prose-only file owes
`--code-digest` identity.

## Verification (Comments)

Verifier address `review/connection.py/verify-comments-1`; scratch
`docs/review/temp-tests/connection/verify-comments-1/`; item diff
`docs/review/temp-tests/connection/diff/pass-1.diff`.

Step 1: `git diff
e6b022ba44f4e14da9e1825cea7047aa38d03298 --
django_strawberry_framework/connection.py tests/test_relay_connection.py
examples/fakeshop/test_query/test_keyset_api.py` hashes
`ef54683033035551709fa8a005924e2440c1232d72705e96eb8049db53a837eb`,
byte-equal to `pass-1.diff` (20689 bytes each); the tree did not move
under the pass. Ordering note: the artifact's first 60 lines (header +
`## Implementation (Worker-2)` opening) were read before the Proof runs
below; worker-1.md prefers the reverse. Substance is preserved: every
Proof ran verbatim, thresholds unmodified. Static Proofs ran in the
shared tree; the behavior Proof ran at the verifier address.

Proofs (record order; implemented must print 0, deferred must still
print 1):

- F1 `grep -c 'both ``resolve_connection`` paths'` prints `0`
  (was 2). PASS.
- F2 `grep -c "keyset-cursor backend"` prints `0` (was 1). PASS.
- F3 `grep -c "receives a coroutine"` prints `0` (was 1). PASS.
- F4 `grep -c "defensive-Django-imports"` prints `0` (was 1). PASS.
- F5 `grep -c 'rides the ``033`` work'` prints `0` (was 1) and
  `grep -c "posture (0.0.9)"` prints `0` (was 1). PASS.
- L1 `grep -c "DONE-033" connection.py` prints `0` (was 1). PASS.
- L2 `grep -c "legacy attr"` prints `0` (was 1). PASS.
- L3 `grep -c "an earlier spec revision"` prints `0` (was 1). PASS.
- L4 `grep -c "spec-algorithm"` prints `0` (was 1). PASS.
- L5 `grep -c '(spec-047)'` prints `0` (was 2). PASS.
- L6 `grep -c 'caps any single page (spec-032)'
  tests/test_connection.py` prints `1`. Deferred, still present. PASS.
- L7 `grep -c "DONE-033-0.0.9" tests/test_connection.py` prints `1`.
  Deferred, still present. PASS.
- L8 `grep -c 'composition pin (spec-034)' tests/test_connection.py`
  prints `1`. Deferred, still present. PASS.
- L9 `grep -c "whatever ordering returned" tests/test_connection.py`
  prints `1`. Deferred, still present. PASS.
- L10 `grep -c "optimizer-folder High"
  examples/fakeshop/test_query/test_library_api.py` prints `1`.
  Deferred, still present. PASS.
- L11 `grep -c "before the connection resolver runs"
  examples/fakeshop/test_query/test_library_api.py` prints `1`.
  Deferred, still present. PASS.

Cross-axis for Comments (Mechanics C1; the Performance record carries
no for-Comments finding):

- `grep -c "^from django.core.exceptions import FieldDoesNotExist"`
  prints `1`, at top level (line 53, Django group, no comment). PASS.
- `grep -c "^    from django.core.exceptions import"` prints `0`. PASS.
- Behavior at `review-20260929T015719-47e437` (exit 0):
  `tests/test_keyset_connection.py::test_resolve_order_path_field_arms`
  + `::test_resolve_order_path_field_accepts_mti_parent_link` report
  `2 passed`. PASS.
- Grade: the hoisted import carries no comment. PASS.

Deferral judgment (Severity ride rule): L6-L9 sit in
`tests/test_connection.py`, L10-L11 in `test_library_api.py`. The item
diff touches only `connection.py`, `tests/test_relay_connection.py`
and `test_keyset_api.py`; no higher finding (Performance F1-F3,
Mechanics H1, C1) touches either deferred file. Both files are
byte-identical to ITEM_BASELINE (`8e08b23f...`, `2cd1b6dd...`, equal
to the record's Trace fingerprints). Deferred correctly; L1-L5 rode
correctly on `connection.py`, which higher findings change.

Whole-docstring grades (every docstring/comment the diff wrote or moved,
graded as the whole it sits in; prose inventory from
`review_changed_python_diffs_against_head.py --prose` under my
`diff/`):

- `_resolve_from_window` (F1/F2/L3): true. `by the offset and keyset
  window branches` names the verified sharing (single derivation; the
  `keyset_seek_supplied` / `first_rn` branches at lines 416-607 fork
  inside it); the spec-033 Decision 5 anchor is kept. `the keyset
  backend rides` is present-tense and body-true: page-relative
  numbering (lines 582-583), probe-overfetch `hasNextPage` (line 590)
  with the seek-count read where the plain comparison cannot hold
  (lines 584-599), `hasPreviousPage` from `keyset_seek_supplied`
  with `first_rn > 1` unfirable (line 607). The F2 wording deviation
  (dropping `cursor`, since the record's text-after retained the
  Proof's keyed substring) is upheld: `keyset` is the distinguishing
  term against `offset` two paragraphs up, nothing is lost, and the
  Proof prints the governed `0`. The L3 invariant survives verbatim
  minus the history clause. No other sentence in the docstring was
  touched or falsified.
- `_consume_window` (F1): true. Exactly one production caller
  (`resolve_connection`, line 1365; the three test callers are probes,
  not paths) and the `isinstance(nodes, _WindowedConnectionRows)`
  fork serves wrapper and non-wrapper sources through one tail
  (lines 640-644 corroborate). `Single entry ... for both` is the
  sharing the call graph verifies.
- `_resolve_keyset_connection` (F3): true. The dispatch is
  `isinstance(nodes, (AsyncIterator, AsyncIterable)) and
  async_execution()` (lines 1136, 1181) with `acount()` (lines 1142,
  1186); `nodes` is a queryset by the line-1071 guard and
  `QuerySet.__aiter__` holds on the installed Django 6.1, so `the
  queryset is async-iterable` is exact. No coroutine is named.
- `_resolve_order_path_field` (F4): true by deletion; the hoisted
  import carries no comment (C1 grade above).
- `_build_relation_connection_resolver` (L1/L2/F5): true. The L1
  clause keeps the true mechanism minus the card id; `the shared
  attr` matches the per-key-first probe (lines 2226-2231); the F5
  paragraph drops the version anchor for the glossary's landing
  clause verbatim (`until an async connection pipeline lands`,
  `docs/GLOSSARY.md` line 1393, `Meta.relation_shapes` entry), and
  every surrounding claim still holds (no `resolver=` parameter in
  the line-2142 signature, `_pipeline_sync` only).
- `_KeysetPage` (L4): true. `value-domain pageInfo inputs` adopts
  the file's own vocabulary (`The Relay pagination algorithm, in the
  value domain`, `Relay's HasNextPage in the value domain`); class
  mood is a description naming the inputs.
- `resolve_connection` comments (L5): true. Decision 7 is `The
  policy is a CEILING over relay_max_results` (the ceiling comment's
  subject) and Decision 9 is `The execution deadline is
  cooperative` (the deadline comment's), verified against
  `docs/SPECS/spec-047-resource_policy-0_0_14.md` lines 838/895.
- `_build_windowed_fallback` docstring (F2-driven rewrite): true.
  `source_factory()` runs only inside the returned lambda (line 266),
  so a served window constructs no queryset; the resolver refuses
  the window when sidecar kwargs are present (the `no_sidecar` gate,
  lines 2232-2241). The pre-existing `accessor` shorthand is kept,
  not introduced.
- `_cap_offset_last_zero_page` (new, H1): true. Upstream
  `ListConnection.resolve_connection` (installed strawberry-graphql
  0.324.0, md5 `e9ccbd9b...`, both arms) takes `edges[-last:]` under
  `end == sys.maxsize` with `has_previous_page = len(edges) !=
  original_len`, so `last: 0` serves the whole list with
  `hasPreviousPage` False on both quirk shapes (with and without
  `after:`); the `max_results` check is `last > max_results`
  (`relay/utils.py`, md5 `fe475e0f...`), which `0` passes. The body
  trims to at most `cap`, flips `hasNextPage` only on a trim,
  re-anchors both cursors, and forces `hasPreviousPage` False
  (a no-op assignment matching upstream on under-cap pages, so the
  final sentence holds on every input the quirk predicate admits).
  `the same shape the keyset slicer serves` is pinned by the two
  keyset cap twins (100 edges, flags False/True). Imperative mood.
- `clear_window_edge_class_cache` (new, F1): true. Mirrors the
  sibling `clear_connection_type_cache` paragraph sentence for
  sentence (the `Test-only` family wording, graded true at review);
  the `registry.clear()` wiring exists (line 1431,
  `owner="connection.edge_class"`); identity-keyed staleness across
  schema reloads is the true mechanism. Imperative mood.
- `test_offset_last_zero_stays_bounded_by_relay_cap` (new, H1 live):
  true. States the expected behavior (`last: 0` bounded at 100,
  both `after:` shapes, flags False/True); the `edges[-0:]` account
  matches upstream; `the same shape the keyset last: 0 twins pin`
  names the two cap twins at `test_keyset_api.py` lines 309/358.
  First line `seed_data(30)` per convention.
- `test_windowed_fast_path_constructs_no_fallback_queryset` (new,
  F2): true. States the expected behavior (zero related-manager
  constructions on served windows); the paragraph matches the body
  (four `Genre` parents, `booksConnection(first: 2)`, `Manager.all`
  counter asserting 0). `genre.books.all()` names the test's own
  accessor.

Attacks: each rewritten sentence was checked against its body and one
real caller or contract source (upstream slice engine, `QuerySet`,
glossary, spec-047, the keyset twins, caller censuses); the `factory`
wording in `_resolve`'s handoff comment pre-exists at ITEM_BASELINE
(lines 2122/2186/2191 there) and the F2 change made it more true, not
false. No attack fails; no `verify 1` finding.

Inverse proof: `--code-digest` of the live target against my own
reconstruction (`verify-comments-1/reconstruction-connection.py`,
built by `build_reconstruction.py`: live text with all 14 prose
reversions to ITEM_BASELINE wording, every code hunk kept) prints
`sha256:de3bdc088829d15c5ad2538fa61c4c565ab93d4bd616a87f868619c7e8466b26`
on both sides, exit 0. Baseline-to-reconstruction carries only the
Performance/Mechanics code hunks; reconstruction-to-live carries only
prose. Worker-2's independent rebuild digests identically; the two
reconstructions differ in exactly one docstring paragraph (the
F2-driven `_build_windowed_fallback` wording, which Worker-2 kept
live and I reverted to baseline) - a prose-only divergence, immaterial
to code identity.

Gates and hygiene: `build_tree_md.py --list-docstrings` on all three
touched files prints `ok` (3 modules, 0 breaking);
`check_citations.py --paths connection.py --substrings` reports 17
citations, 0 violations (same 17 as review; the diff adds no
`path::Symbol` cite). No module first line changed on any touched
file (old and new first lines identical), so no TREE.md render is
owed. All 185 added diff lines swept: no process provenance (the only
`spec-` hits are the kept Decision pointers, one retained plus the
two L5 upgrades), no line-number citation, no `we`/`you`/`I`.

Sibling verifiers: Performance routes its one gap to Mechanics (the
H1 async trim self-await, a code defect); Mechanics files it own-axis
as V1 (revision-needed). Neither routes anything to Comments, and V1
touches no prose: the closure fix is code-only, and the helper
docstring describes the color-free helper, not the wrapper. No
Comments revision is owed for V1; the re-pass needs no Comments
re-verification unless it touches prose.

Disputes: none recorded in `## Implementation (Worker-2)`; nothing
to judge. Cells: concur inapplicable by construction (all Proofs
static; the one behavior Proof ran green in the default cell).

Verdict: verified. 10 findings implemented as governed (F1-F5, L1-L5),
6 deferred per the ride rule (L6-L11, Proofs still print 1, files
byte-identical to baseline), C1 hoist landed with true (absent)
prose, every landed docstring grades true as a whole.

Fingerprints: `connection.py`
`c8b9670109d05f9a09f2f8a113e491baa7511317`,
`tests/test_relay_connection.py`
`fe2b2d24ab6e71e6238183690b02821abb239497`,
`test_keyset_api.py`
`88a432b0858c54afc91a79cedbf8938983ab2c23` (all equal Worker-2's
after-values); deferred files equal the record's Trace values;
spec-047 `844eab53...`, glossary `3413edc3...`, upstream md5s
`e9ccbd9b...`/`fe475e0f...` all equal the records'. Scratch:
`build_reconstruction.py` (`4ce76d3d...`),
`reconstruction-connection.py` (`11027cb6...`),
`baseline-connection.py`, `diff/` (prose + stripped per-file diffs).
Run id: `review-20260929T015719-47e437` (C1 behavior, 2 passed).

Handoff: Comments pass 1 verifies clean with one standing note for
Worker-0: the F2-Comments wording deviation (`the keyset backend
rides`) is upheld as true and minimal - the record's text-after is
unlandable verbatim (it retains the Proof substring), so no
follow-up should "restore" the word `cursor` there. The six deferred
Lows belong in `## Outcomes`, not this diff. The next Comments reader
on this file inherits the record's five Routed leads plus the
observed-true vocabulary notes; nothing in this pass disturbs them.
