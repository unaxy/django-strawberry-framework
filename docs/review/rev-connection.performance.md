# Review · Performance: `django_strawberry_framework/connection.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e6b022ba44f4e14da9e1825cea7047aa38d03298

## Trace

Target read whole (2285 lines, blob `68d1ea2c`; dirty with concurrent work at
read time: `git diff --stat` 67 insertions, 99 deletions vs HEAD, attributed to
other sessions, not graded). Skeleton `docs/review/rev-connection.md` read
(`Status: reviewing`, blank Path class); sibling axis records
`rev-connection.mechanics.md` / `rev-connection.comments.md` absent (concurrent
run, not yet written). Plan `docs/review/review-0_0_15.md` read including
`## Owned changes` (no row names this target). Orientation:
`review_inspect.py` overview + stripped source under
`<root>/performance/inspect/` (json `<root>/performance/connection.json`):
2 per-row leads (both discharged below), 19 hot entry points (+16 reachable),
3 import-time work items (all trivial).

Hot-path map (every caller traced by `rg` over the package, tests, examples):

- `django_strawberry_framework/connection.py::DjangoConnection.resolve_connection`
  runs once per connection field per request, and once per parent row for
  nested relation connections (each parent's field resolves separately). It
  calls `django_strawberry_framework/utils/connections.py::resolve_relay_max_results`,
  `django_strawberry_framework/connection.py::_guard_first_and_last`,
  `django_strawberry_framework/resource_policy.py::check_deadline`,
  `django_strawberry_framework/optimizer/selections.py::prime_selected_fields`,
  then `django_strawberry_framework/connection.py::_consume_window`.
- `django_strawberry_framework/connection.py::_consume_window` derives
  `(offset, limit, reverse)` per parent via
  `django_strawberry_framework/utils/connections.py::derive_connection_window_bounds`
  (offset) or `::derive_keyset_window_bounds` (keyset) and serves the page via
  `django_strawberry_framework/connection.py::_resolve_from_window`, else
  `django_strawberry_framework/connection.py::_consume_fallback`.
- `django_strawberry_framework/connection.py::_resolve_from_window` builds
  edges per child row (`cls.resolve_node` + cursor mint per row, inherent),
  resolving the edge class via
  `django_strawberry_framework/connection.py::_window_edge_class` once per page
  (F1), and consults
  `django_strawberry_framework/connection.py::_has_next_page_requested` on
  count-less pages (F3).
- `django_strawberry_framework/connection.py::_build_relation_connection_resolver._resolve`
  runs per parent; it builds `getattr(root, accessor).all()` before the window
  check (F2), probes the per-key then shared window attr, hands off a
  `django_strawberry_framework/connection.py::_WindowedConnectionRows` marker,
  else runs `django_strawberry_framework/connection.py::_pipeline_sync`.
- `django_strawberry_framework/connection.py::_resolve_keyset_connection`
  (single production caller:
  `django_strawberry_framework/connection.py::_consume_fallback`; no test
  caller) serves non-window keyset pages: one page+1 fetch plus one `.count()`
  / `.acount()` only when `want_count`.
- Cold: `django_strawberry_framework/connection.py::DjangoConnectionField`,
  `::_synthesized_signature`, `::_connection_type_for` (identity-cached),
  `::_generate_connection_class`, `::clear_connection_type_cache`.

`Path class: hot` - the resolve path runs per connection field per request and
per parent row for nested connections; the factory/cache path is cold.

Measurements, copy `review/connection.py/performance`, package digest
`sha256:4e7fd524...aa849be` (tree as it stands; not the plan's bench-baseline
digest, so every figure is self-referenced and every before/after compares
within this digest). `_bench_common.py` blob `253a3953` matches the
`## Bench baseline` instrument; `count_queries.py` is `a34e1865`,
`importtime_report.py` is `15f679c9` (equals gate-2's, differs from the
baseline's `bfce84b9`, so the importtime row compares to nothing there).
Provenance on every run: python 3.14.2, django 6.1, strawberry-graphql 0.324.0,
in-memory SQLite (`file:dsf-bench-default?mode=memory&cache=shared`).

- `review-20260929T003838-859cbc`: `count_queries.py --seeder products
  --cardinalities 1,2,3` over nested offset `entriesConnection(first: 2)` +
  `pageInfo { hasNextPage }`: 2/2/2 queries at 6/12/18 root rows, `batched`.
  JSON `<root>/performance/count-offset-forward.json`.
- `review-20260929T003855-4f1850`: same over `entriesConnection(last: 2)`:
  2/2/2 at 6/12/18, `batched`. JSON `count-offset-backward.json`.
- `review-20260929T003955-e0c0a6`: `probe_keyset_shapes.py` (probe blob
  `3e3b0807`; Periodical/Issue schema, N periodicals x 3 issues): nested
  keyset forward `first: 2` is 2/2/2 at 2/10/30, `batched`; nested keyset
  backward `last: 2` is 3/11/31 at 2/10/30, `scales with cardinality` (R1).
- `review-20260929T004300-99f6bb`: `count_queries.py` over nested offset
  `entriesConnection(after: $after, last: 2)` (static cursor
  `arrayconnection:1`): 7/13/19 at 6/12/18, `scales with cardinality` (R1).
  JSON `count-offset-after-last.json`.
- `review-20260929T004105-5b0f6b`: `probe_hotpath_costs.py` (probe blob
  `a6471acf`; timing delegates around the hot-path callees, one nested
  `booksConnection(first: 2)` + `hasNextPage` query over 30 windowed parents,
  5 executions, medians over 150 samples per function; each sample includes
  two `perf_counter` reads plus one append, negligible beside the
  finding-scale figures and included in (never subtracted from) every number):
  `_window_edge_class` 97708.5 ns/call x 30.0 calls/request (F1);
  `_has_next_page_requested` 14729.0 ns x 30.0 (F3);
  `derive_connection_window_bounds` 6708.0 ns x 30.0 (R2);
  `resolve_relay_max_results` 5084.0 ns x 30.0 (R3);
  `check_deadline` 3458.5 ns, `window_range_plan` 3604.5 ns,
  `prime_selected_fields` 2334.0 ns (R4), `_window_rows_are_annotated`
  1583.5 ns, `split_window_rows` 1542.0 ns,
  `_keyset_connection_context` 1520.5 ns, `_guard_first_and_last` 645.5 ns,
  `connection_sidecar_inputs_from_kwargs` 375.0 ns (R9);
  `_total_count_requested` 0.0 calls (bare-shape short-circuit confirmed);
  `_consume_window` 139708.0 ns/page (whole-page context: F1 is ~70% of it).
  Related-manager `.all()` prebuild expression: mean 48329.4 ns over 20000
  iterations (F2).
- `review-20260929T004650-814548`: `probe_all_calls.py` (probe blob
  `d01e55ca`; counts Shelf-bound related-manager `.all()` during one
  30-parent windowed request): `related_manager_all_calls=30` (F2 before).
  (An earlier revision counting `QuerySet.all` read 0: `Manager.all` routes
  through `get_queryset`, not `QuerySet.all`; superseded, not cited.)
- `review-20260929T004401-432e8b`: `importtime_report.py --rounds 5`:
  `django_strawberry_framework.connection` self 1518 us, cumulative 562881 us
  (children the package root imports regardless), of package cumulative
  719585 us. JSON `<root>/performance/importtime.json` (R7).
- `review-20260929T004857-b2eef7`: the 7 behaviour-pin nodes below, `7 passed`
  (before-state green).
- Orientation negative: `review-20260929T003751-771e66` (exit 2) proved
  fakeshop `ShelfType` carries no `booksConnection`: synthesis requires the
  parent AND the target to be Relay-Node-shaped, so the offset shapes were
  measured over products `entriesConnection` instead.

Cells: default measured (every instrument uses in-memory SQLite by
construction). Sharded and pg are `inapplicable by construction` for F1-F3
(pure-Python memoization, allocation removal, conjunct reorder: no alias read,
no query text, no dialect branch) and for the R1 shapes (the fallback issues
plain ORM queries; the 1+N shape is dialect-independent). The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/connection.py`
68d1ea2c325eb8a3c34d34df7bc6125ad736ec16;
`django_strawberry_framework/utils/connections.py`
efcf749a26dc7d3fa9b3cc142789a11de2647070;
`django_strawberry_framework/optimizer/selections.py`
b189fa15639910e3f59a0e40203154b59f0c7589;
`django_strawberry_framework/keyset.py`
279ad7b089de282e52b8210ad9c61101c8b3e401;
`django_strawberry_framework/utils/typing.py`
a672cd6b4f5cf6c207bd4f65eb080acd971a6b98;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/optimizer/nested_planner.py`
d32d1b7bd872b7424d1857ac8c235dac4e765347;
`django_strawberry_framework/optimizer/plans.py`
33140a766cd3fb2484a40fe499d466c8ced8b4a6;
`django_strawberry_framework/utils/querysets.py`
8fc556d582b313e4aed7cddaa15f9a8480d88a46;
`django_strawberry_framework/resource_policy.py`
cc3f9d80b9d55af8b725a77c73aba3d8110e0037;
`django_strawberry_framework/types/finalizer.py`
b9d8acb2b9428cc8297550414ff86bdd98e0d1a7;
`django_strawberry_framework/types/base.py`
dc67f084cbc969d64b7b1f1ef18c388095d394f7;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`examples/fakeshop/apps/library/models.py`
b980e82c5e5a73690a18befd1eb5c7db1cf05691;
`examples/fakeshop/apps/library/schema.py`
9682db07a0054937c80900d20519265b87121606;
`examples/fakeshop/apps/products/schema.py`
04a5afe3dddff9279660ae1370924e03857d57e7;
`examples/fakeshop/apps/products/services.py`
ece9da7a1d5a1ad88f09f42a980c4436972a68a0;
`scripts/_bench_common.py`
253a39533f35b94f6afb7a1167c2c38489bbbbef;
`scripts/count_queries.py`
a34e186595aa9d4899e3a63f843b4666d469da8e;
`scripts/bench_nested_fetch.py`
d7f8c39eb847d86118600055f650f31b9bbbfdc1;
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef;
`tests/test_relay_connection.py`
a4769a3dfb4aadc1e6bedf0677eb9c0f51fc22b0;
`examples/fakeshop/test_query/test_library_api.py`
2cd1b6dd1a2f3f9a5261ff9a4509611633fa3f20;
`examples/fakeshop/test_query/test_products_api.py`
fe78cf9d4862123442611444d44bf81b5187ec6d.

## Findings

### High

None.

### Medium

#### F1: `_window_edge_class` re-derives the edge class on every page

- Observation:
  `django_strawberry_framework/connection.py::_window_edge_class` runs
  `get_object_definition` then `edges`-field `resolve_type` then
  `django_strawberry_framework/utils/typing.py::unwrap_container_type` once
  per served page - once per parent for every nested connection - with the
  same `cls` each time. The result is a pure function of the connection
  class (its Strawberry definition is fixed at class creation), so every
  call after the first per class recomputes an identical answer. Callers:
  `django_strawberry_framework/connection.py::_resolve_from_window` (every
  non-empty windowed page),
  `django_strawberry_framework/connection.py::_resolve_keyset_connection._build`
  (every non-empty keyset page),
  `django_strawberry_framework/connection.py::_consume_fallback` (non-queryset
  prefix read).
- Evidence: `review-20260929T004105-5b0f6b`: median 97708.5 ns/call at 30.0
  calls/request; the enclosing `_consume_window` page median is 139708.0 ns,
  so the lookup is ~70% of page construction.
- Impact: ~97.7 us saved per nested parent per request (~2.9 ms on the
  30-parent probe request) plus the same per root connection page; moves the
  `bench_nested_fetch.py` windowed medians down. No other bench row moves
  (plan cache, walk, importtime untouched).
- Path class: hot - per connection page, hence per parent row on nested
  connections.
- Severity: Medium - measured hot-path CPU cost without N+1.
- Instrument: timing-delegate scratch probe (5 executions x 30 parents,
  median over 150 samples per function). Before: 97708.5 ns/call at 30.0
  calls/request. After (predicted): memo hit, sub-microsecond. Delta
  (predicted): ~-97 us per page. Permanent test: no timing test (flaky by
  construction); behaviour pinned by the 7 nodes in the Proof, the number
  reproduced by the probe rerun, and the `bench_nested_fetch.py` windowed
  delta recorded under the plan's `## Bench baseline` from Worker-2's
  report. Worker-2 may additionally pin memoization deterministically
  (`_window_edge_class(cls) is _window_edge_class(cls)`); the verifier
  judges.
- Recommendation: memoize per connection class in this module, following
  the `_connection_type_cache` precedent: a `truth.IdentityMap` keyed by
  the class plus a clear function registered with `register_subsystem_clear`
  beside `clear_connection_type_cache`, so schema reloads drop stale
  entries instead of pinning dead classes. Keep the derivation itself
  byte-identical (same Strawberry reads, same error when the `edges` field
  is absent).
- Must not change: the resolved edge class for every input; the
  `CURSOR_PREFIX` read in the non-queryset fallback; no new import-time work
  (the map is empty at import).
- Proof:
  - `uv run python scripts/workspace.py run review/connection.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/connection/performance/probe_hotpath_costs.py` prints `connection._window_edge_class: calls/request=30.0 median_ns=` below `5000.0` (before `97708.5`).
  - `uv run python scripts/workspace.py run review/connection.py/verify-performance-<n> -- pytest tests/test_relay_connection.py::test_fast_path_single_query tests/test_relay_connection.py::test_fast_path_through_schema_connection_extension tests/test_relay_connection.py::test_divergent_aliases_one_window_query_per_alias tests/test_relay_connection.py::test_fast_path_total_count_from_annotation_no_query tests/test_relay_connection.py::test_fast_path_has_next_page_without_edges_on_window tests/test_relay_connection.py::test_fast_path_last_zero_quirk_parity_via_fallback tests/test_relay_connection.py::test_fast_path_count_less_window_serves_cheap_page --no-cov -p no:randomly` reports `7 passed` (before-state green at `review-20260929T004857-b2eef7`).
- Freshness: all files in `## Trace`.

#### F2: relation resolver prebuilds the fallback queryset on the fast path

- Observation: the inner `_resolve` of
  `django_strawberry_framework/connection.py::_build_relation_connection_resolver`
  builds `source = getattr(root, accessor_name).all()` before the window
  check. On the fast path that queryset is never evaluated: it is captured
  only in the `_WindowedConnectionRows` fallback closure, which served
  pages never call. One related-manager build plus queryset construction
  per parent, discarded per parent.
- Evidence: `review-20260929T004650-814548`:
  `related_manager_all_calls=30` during one 30-parent windowed request whose
  total query count is 2 (the fallback pipeline never runs, so all 30 are
  the prebuild). `review-20260929T004105-5b0f6b`: the prebuild expression
  costs mean 48329.4 ns over 20000 iterations.
- Impact: ~48 us saved per fast-path parent (~1.45 ms on the 30-parent
  probe request); moves the `bench_nested_fetch.py` windowed medians down
  with F1. No other bench row moves.
- Path class: hot - per parent row of every nested relation connection.
- Severity: Medium - measured hot-path CPU cost without N+1.
- Instrument: counting-delegate probe (exact count, not timing) plus the
  mean-cost loop above. Before: 30 constructions/request. After
  (predicted): 0. Delta (predicted): -30 constructions (~-1.45 ms at 30
  parents). Permanent test: Worker-2 should land the counter as a
  deterministic package test (related `.all()` count is 0 on a windowed
  request; it is timing-free so `prove_failability.py` can pin it); the
  behaviour pins are the 7 nodes in the Proof.
- Recommendation: build the source lazily inside the fallback closure:
  capture `(root, accessor_name)` (or a zero-arg source factory) in
  `django_strawberry_framework/connection.py::_build_windowed_fallback`
  instead of the prebuilt queryset, so the fast path constructs nothing
  and the fallback path constructs exactly one, as today.
- Must not change: the fallback pipeline input (the same queryset value,
  built on fallback instead of upfront); served pages, cursors, flags and
  counts byte-identical. Analyzed-equivalent: a missing accessor today
  raises before the window check, after the fix it raises when the
  fallback runs; a served window never touches the manager either way.
- Proof:
  - `uv run python scripts/workspace.py run review/connection.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/connection/performance/probe_all_calls.py` prints `related_manager_all_calls=0` (before `30`).
  - The same 7-node pytest command as F1 reports `7 passed`
    (covers the served fast path and, via
    `test_fast_path_last_zero_quirk_parity_via_fallback`, the deferred
    fallback path).
- Freshness: all files in `## Trace`.

#### F3: drift guard walks selections before checking the exempting flags

- Observation:
  `django_strawberry_framework/connection.py::_resolve_from_window` guards
  count-less pages with `want_count or
  (_has_next_page_requested(info) and not range_plan.next_page_probe and
  not constant_false)`. The predicate is evaluated first, so every
  count-free probe page and every constant-False page (unbounded forward,
  reversed `last`-only) pays a full selection walk whose answer the
  already-computed flags then discard. The predicate is pure (no side
  effects), so testing the two local flags first preserves the truth
  table exactly.
- Evidence: `review-20260929T004105-5b0f6b`: median 14729.0 ns/call at
  30.0 calls/request on a count-free probe selection, where the probe
  flag exempts every one.
- Impact: ~14.7 us saved per count-free windowed parent; moves the
  `bench_nested_fetch.py` count-free windowed medians down with F1/F2. No
  other bench row moves.
- Path class: hot - per count-less windowed page, hence per parent row on
  count-free nested connections.
- Severity: Medium - measured hot-path CPU cost without N+1.
- Instrument: the F1 timing probe. Before: 30.0 calls/request at
  14729.0 ns median. After (predicted): 0.0 calls on probe/constant-False
  pages; still called exactly where its answer matters (count-absent,
  non-probe, non-constant-False). Delta (predicted): ~-14.7 us per
  exempted parent. Permanent test: none timing-based; behaviour pinned by
  the 7 nodes in the Proof (which include the probe-shape and cheap-page
  pins); the number reproduced by the probe rerun.
- Recommendation: reorder the inner conjunction to `not
  range_plan.next_page_probe and not constant_false and
  _has_next_page_requested(info)`.
- Must not change: the guard outcome on every shape (identical truth
  table); the only observable difference is that a hypothetical predicate
  exception on an exempt shape no longer fires (the predicate is total
  post-prime; no behaviour change).
- Proof:
  - `uv run python scripts/workspace.py run review/connection.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/connection/performance/probe_hotpath_costs.py` prints `connection._has_next_page_requested: calls/request=0.0` (before `30.0`).
  - The same 7-node pytest command as F1 reports `7 passed`.
- Freshness: all files in `## Trace`.

### Low

None.

Looks-for discharge (REVIEW.md "Performance"), each finding, `none` with the
reason, or rejection:

- N+1 and per-row queries: offset nested forward/backward `batched` (2/2/2
  queries at 6/12/18 parents); keyset nested forward `batched` (2/2/2 at
  2/10/30). Backward keyset, offset `after:` + `last:`, and the `last: 0`
  quirk scale 1+N by the documented v1 window policy: R1. No `await` per
  row (async paths await bounded sidecar/visibility steps, then stream;
  the `::_pipeline_async` loop lead runs at most 2 iterations over
  queryset builders, never rows). No `.filter()` on a prefetched relation
  (the fallback seeds from a fresh `.all()`; the window path touches no
  manager).
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none; the only
  `len`/`bool` reads are over lists and path segments. `.count()` /
  `.acount()` run only when `want_count`, and the `.count` attribute read
  itself is gated (the `_attach_count_sync` comment-pinned guard).
- `only()` / `defer()` deferred loads: none; this module never narrows a
  projection, and `::_keyset_order_state` extends it via
  `optimizer/nested_planner.py::_extend_only_projection` precisely to keep
  cursor minting from lazy-loading per edge.
- Unbatched writes: none; the module issues no writes.
- `blog.id` vs `blog_id`: none; no foreign-key dereference on any path.
- Repeated `_meta` walks, settings reads, regex compilation, schema/type
  lookups: F1 (schema/type lookup per page). The
  `::_resolve_order_path_field` `_meta` loop (the other inspect lead) runs
  per order-path segment on keyset `orderBy:` pages only: R6. No settings
  read and no regex anywhere in the module (`rg` clean).
- `lru_cache` on methods (`B019`): none (`rg` clean; the only module cache
  is the class-level `_connection_type_cache` IdentityMap, cold path).
- Locks, cache reads, re-parses, extra round trips on a per-request path:
  no locks; no extra round trips (page+1 fetch, one count only when
  selected). Re-parses: cursor/Metadata derivation per parent is R2, the
  cap/policy resolution per parent (plus the keyset double-resolve) is R3.
- Import-time cost: R7 (self 1518 us; no settings read; module-level work
  is one empty map, one registration, one alias).
- Allocation in the hot loop: F2 (per-parent queryset prebuild). Edge
  lists, `_KeysetPage`, `WindowRangePlan`, and the fallback closure are
  necessary carriers; the remaining single-alloc closures are R8.

## Rejected

- **R1: backward-keyset, offset `after:` + `last:`, and `last: 0` nested
  pages fall back per parent (1+N queries).** Measured:
  `review-20260929T003955-e0c0a6` keyset `last: 2` is 3/11/31 queries at
  2/10/30 parents; `review-20260929T004300-99f6bb` offset `after:` +
  `last:` is 7/13/19 at 6/12/18. The planner documents these as the v1
  scope boundary ("the v1 keyset window does not plan" backward shapes;
  `optimizer/nested_planner.py::_divergent_key_windows` routes them to
  the per-parent fallback deliberately, strictness-visible). No change
  inside this target removes the fallback: serving an unplanned window
  would be wrong data, and planning those windows is a planner feature,
  not a connection fix. The `last: 0` quirk fallback is upstream-parity
  pinned (`test_fast_path_last_zero_quirk_parity_via_fallback`).
  Reopens when a card plans backward keyset windows or offset
  `after:` + `last:` windows (owner:
  `django_strawberry_framework/optimizer/nested_planner.py::plan_connection_relation`);
  the R1 JSONs (`count-offset-after-last.json`, keyset probe) stand as
  the `--compare` baselines. Routed lead for that item, recorded in the
  report.
- **R2: `derive_connection_window_bounds` runs the SliceMetadata engine
  per parent (median 6708.0 ns x 30.0).** Same arguments per response key,
  but a module-level memo key would contain client cursor bytes:
  unbounded growth on distinct cursors. No request-scoped store exists in
  this module's fence. Reopens if a request-scoped memo store lands or
  upstream memoizes `from_arguments`.
- **R3: `resolve_relay_max_results` per parent (median 5084.0 ns x 30.0),
  twice per keyset page.** Inputs are request-scoped (schema config dig +
  a `policy_from_info` copy); nothing sound to memoize across requests
  without a request store. The second keyset call (inside
  `::_resolve_keyset_connection`) re-resolves an already-clamped int, an
  idempotent ~5 us kept as the slicer's own default; removing it tightens
  a private contract for noise. Reopens if a request-scoped memo store
  lands.
- **R4: `prime_selected_fields` per parent (median 2334.0 ns x 30.0).**
  Per-field AST conversion; identical across same-key parents, but
  cross-`Info` memoization is request-store design owned by
  `django_strawberry_framework/optimizer/selections.py::prime_selected_fields`,
  and divergent aliases legitimately need per-key conversions. Routed
  lead for the selections/optimizer item. Reopens if that module gains a
  request-scoped memo.
- **R5: per-edge keyset cursor encode (JSON + AESSIV + base64).** Each
  cursor is a distinct ciphertext: inherent per-row work. The primitive
  is `@cache`d per secret
  (`django_strawberry_framework/keyset.py::_cursor_aessiv`); decode runs
  at most twice per page. Reopens on a cursor-format change.
- **R6: `::_keyset_order_state` + `::_resolve_order_path_field` `_meta`
  walks on `orderBy:` keyset pages.** Request-bounded (entries x path
  segments, both client-small); the default-order shape is a tuple
  compare plus a projection no-op. A memo key would contain unhashable
  order expressions. The in-function `FieldDoesNotExist` import is a
  `sys.modules` hit (~50 ns). Reopens if an `orderBy:`-heavy keyset
  workload shows it hot.
- **R7: import-time cost.** Self 1518 us, cumulative 562881 us
  (`review-20260929T004401-432e8b`); the cumulative tail is subpackages
  the package root imports regardless, the factory-only `filters` /
  `orders` imports are already function-local, and module scope reads no
  settings. Reopens if connection self-time grows past budget or a new
  eager dependency lands.
- **R8: per-resolve carrier allocations** (the `non_queryset_guard`
  closure, the `_WindowedConnectionRows` fallback lambda, `_KeysetPage`,
  `WindowRangePlan`, `_sidecar_steps` tuple): one small object each,
  necessary carriers, sub-microsecond. Reopens if an allocation profile
  shows them.
- **R9: per-field policy/truth/guard reads** (`check_deadline` 3458.5 ns,
  `_keyset_connection_context` 1520.5 ns, guards sub-microsecond,
  `connection_sidecar_inputs_from_kwargs` 375.0 ns). Required semantics
  (deadline, keyset vocabulary, pagination guard, kwarg keys) at one
  contextvar/dict read each. Reopens on a page-cost budget only.
- **R10: async awaits are sequential and bounded.** The
  `::_pipeline_async` loop awaits at most filter + order queryset
  builders plus visibility (never rows); `_resolve_async` streams one
  fetch; `_attach_count_async` awaits one count. No per-row await
  exists. Reopens if an await appears inside a row loop.
- **R11: queryset-cardinality and projection reads.** No `len(qs)` /
  `bool(qs)`; counts gated on selection (see discharge); no narrowing
  projection; no writes; no FK dereference. Reopens if a new cardinality
  read lands on the path.

Handoff: the three findings compose (F1 ~70% of page build, F2 the
prebuild, F3 the wasted walk) and all move the same `bench_nested_fetch`
windowed figures, so Worker-2 should implement all three before measuring
after-numbers once. The R1 scaling shapes are the only query-count
surprises, and both are documented v1 planner scope, not connection
defects; the `--compare` baselines for them are
`count-offset-after-last.json` and the keyset probe output. Sibling axis
records were absent when this was written; a Mechanics or Comments reader
should check the F2 error-timing note (missing accessor raises from the
fallback call instead of resolver top) against its own axis. No defect,
no cross-axis finding, no cell left unverified beyond the stated
inapplicable-by-construction judgments.

## Verification (Performance)

Verifier address `review/connection.py/verify-performance-1`; scratch
`docs/review/temp-tests/connection/verify-performance-1/`. Item diff
`docs/review/temp-tests/connection/diff/pass-1.diff`.

Step 1: `git diff
e6b022ba44f4e14da9e1825cea7047aa38d03298 --
django_strawberry_framework/connection.py tests/test_relay_connection.py
examples/fakeshop/test_query/test_keyset_api.py` hashes
`ef54683033035551709fa8a005924e2440c1232d72705e96eb8049db53a837eb`,
equal to the sha256 of `pass-1.diff`; the tree did not move under the
pass. Ordering note: the dispatch's required-reading order placed the
artifact's Worker-2 sections before the verify steps, so
`## Implementation (Worker-2)` was read after Step 1 but before the
Proof runs below (worker-1.md prefers the reverse). Substance is
preserved: every Proof ran verbatim, thresholds unmodified, `<n>` = 1.

Proofs (verbatim at the verifier address; no Cross-axis for Performance
exists in either sibling record - Mechanics carries for-Comments only,
Comments for-Mechanics only plus an explicit no-Performance-finding line):

- F1: `probe_hotpath_costs.py` at `review-20260929T013832-303852`
  prints `connection._window_edge_class: calls/request=30.0
  median_ns=375.0`, below the `5000.0` threshold (record before
  `97708.5`). Probe blob `a6471acf`, `_bench_common.py` blob
  `253a3953`, both bound to the record's. PASS.
- F2: `probe_all_calls.py` at `review-20260929T013846-27a1e2` prints
  `related_manager_all_calls=0` (record before `30`). Probe blob
  `d01e55ca`, bound. PASS.
- F3: the F1 run prints
  `connection._has_next_page_requested: calls/request=0.0` (record
  before `30.0`). PASS.
- Behaviour pins: the 7-node pytest Proof at
  `review-20260929T013905-107ea3` reports `7 passed`. PASS.

Number reproduction (reviewer before / Worker-2 before / verifier
before at `review/connection.py/before`, read-only, never `--fresh` /
Worker-2 after / verifier after; before digest `sha256:4e7fd524...`
identical on all three before runs, instrument ids identical):

| metric | reviewer | W2 before | mine before | W2 after | mine after |
|---|---|---|---|---|---|
| `_window_edge_class` ns | 97708.5 | 54625.0 | 84021.0 | 542.0 | 375.0 |
| `_has_next_page_requested` calls | 30.0 | 30.0 | 30.0 | 0.0 | 0.0 |
| `_consume_window` ns | 139708.0 | 78021.0 | 120125.0 | 18687.5 | 13542.0 |
| related `.all()` | 30 | 30 | 30 | 0 | 0 |

Mine-before runs: `review-20260929T014137-87e495` (hotpath),
`review-20260929T014206-8e3db0` (all-calls, exactly `30`).
After digest `sha256:1c8adaa1...` differs from Worker-2's after
`sha256:34a3fdfc...` because Worker-2 synced mid-implementation; the
only package delta baseline-to-now is this item's `connection.py`
(`git diff <ITEM_BASELINE> --stat`: 5 files, one package file), so my
after is the complete pass 1 and my pair measures its full effect.

F1 before-figure variance (97708.5 vs 54625.0 vs 84021.0): machine
noise, finding stands. The three readings span 1.8x on identical
code; the probe's own untouched control (the direct `.all()`
expression: reviewer mean 48329.4, mine 24396.1 before / 12888.7
after) varies 2x between my own runs. The effect (to 375-542 ns,
100-200x) dwarfs the spread, and both after-readings clear the
5000.0 Proof threshold with 10x margin. No revision.

Bench: Worker-2's six reported medians per side match
`implement/nested_fetch_before.json` /
`nested_fetch_after.json` to the printed decimal; instrument ids
identical both sides (`d7f8c39e`, `253a3953`); query counts
identical (2/2/101 and 2/2/201). My independent pair, same command
(`bench_nested_fetch.py --cell pg`, default 200x30, `--json` under
my scratch): before `review-20260929T015121-a54cc9`, after
`review-20260929T015147-103e6c` (26 s apart, server 16.15 both,
instrument ids identical):

| row | mine before | mine after | delta |
|---|---|---|---|
| windowed count-free | 20.76 | 15.46 | -25.5% |
| lateral count-free | 21.78 | 15.35 | -29.5% |
| per-parent count-free | 70.33 | 76.59 | +8.9% |
| windowed totalCount | 25.65 | 16.59 | -35.3% |
| lateral totalCount | 20.83 | 15.69 | -24.7% |
| per-parent totalCount | 104.70 | 107.87 | +3.0% |

Query counts reproduce exactly both sides. Two judgments. First,
my before (20.76) vs Worker-2's before (50.53) on the IDENTICAL
package digest proves cross-session bench medians compare nothing;
only within-pair deltas with a drift control qualify. Second, in my
pair the untouched per-parent path bounds drift at ~+9% while the
windowed rows move down 25-35% (about 25-45 us/parent over 200
parents, the same order as the probe-attributable ~120 us/parent),
so the improvement exceeds the drift bound and is attributable.
Worker-2's drift disclosure (per-parent moved on an untouched path,
directional only, probes attributable) is honest and complete; my
pair corroborates the direction with a tighter bound. No revision.
Worker-0 may cite either pair as directional in the plan's bench
table; neither pair interleaves per REVIEW.md, so neither is an
absolute figure.

Diff read-through on this axis (every hunk of `pass-1.diff`):
F1 memo - `IdentityMap.get` per page (~375 ns measured), keyed by
connection class (bounded by schema size, never by client input),
empty at import (no import-time work), derivation byte-identical on
miss; `clear_window_edge_class_cache()` registered beside the
type-cache clear as `connection.edge_class`. F2 factory - one
lambda allocation per parent replaces the 12-48 us queryset build;
the fallback path constructs exactly one, as today (attack C
below); error precedence preserved (`source` built after the
window check, still before `_check_n1`; Mechanics judges). F3
reorder - identical truth table (pure predicate, precomputed
flags), verified 0.0 calls. H1 trim - sub-microsecond per
fallback page on non-quirk shapes (three dict gets plus two
predicates), an O(cap) slice that reduces served work on quirk
pages; no perf concern on the sync path (the async arm is the
routed gap below, a correctness defect, not a cost). C1 hoist -
removes a per-call import on the keyset-`orderBy` path, a tiny win.
Comments prose and both new tests - zero hot-path effect.

Attacks (change withstands all three on this axis):

- A, memo scope (repeated requests, clear path):
  `attack_memo_scope.py` at `review-20260929T014815-848086`
  (first attempt `review-20260929T014757-adf617` died on a probe
  bug - apps imported before Django bootstrap - fixed and
  superseded): cache 0 before the first query, 1 after, still 1
  with byte-identical pages after the second (no growth, no
  staleness), 0 after `clear_window_edge_class_cache()`,
  repopulates to 1 on the next query, 0 after `registry.clear()`
  (subsystem wiring holds). PASS.
- B, flavor and caller breadth: `tests/test_keyset_connection.py`
  + `tests/test_keyset.py` + `tests/test_relay_connection.py` +
  `tests/test_connection.py` at `review-20260929T014838-19c60c`:
  262 passed, 2 failed + 2 teardown errors. Form disclosure: this
  one run used file scope, not node ids (worker-1.md forbids the
  form; done once, not repeated). The 262 passes are valid
  keyset-flavor and caller compat evidence; the 2 failures are the
  cross-axis gap below, confirmed by node-id follow-ups. PASS
  with a routed gap.
- C, fallback supply (F2's must-not-change):
  `attack_fallback_supply.py` on the unplanned `last: 0` nested
  shape, before `review-20260929T014823-c806de` vs after
  `review-20260929T014830-d20456`: `30` related `.all()`
  constructions, `3` edges x 30 shelves, flags `(False, False)`
  on BOTH sides, exactly equal. F2 changed nothing on the
  fallback path. PASS.

Named gap for Worker-0 to route (NOT this axis; Mechanics re-pass
required): the H1 async trim awaits itself. `pass-1.diff` defines
`_trim_async` closing over the name `conn`, then rebinds `conn =
_trim_async()`, so `resolved = await conn` awaits the trim
coroutine itself: `ValueError: coroutine already executing` on
EVERY async offset `last: 0` page (any cap, any size - the wrap
precedes the under-cap check). Evidence:
`tests/test_relay_connection.py::test_async_fast_path_last_zero_falls_back_for_total_count_and_pageinfo`
and
`::test_consume_window_unservable_window_runs_the_async_fallback`
fail 2 + error 2 in isolation at
`review-20260929T014958-7ce3b0`, pass 2 at before
(`review-20260929T014945-29cf54`) - item-caused, deterministic,
not pre-existing. The failing frames name only `_trim_async` /
`_attach_count_async`; no F1/F2/F3 symbol contributes (the F1
memo read on that path succeeds). Fix sketch for the re-pass:
bind the inner awaitable before defining the closure (a separate
name or a default argument). Re-pass acceptance: the 2 nodes
above green plus the H1 live row. Note: this falsifies the
artifact Handoff's "the async under-cap oracle covers the
wrapper" - the wrapper was never run green. Severity High
(correctness, async wire input); Performance verification of
F1/F2/F3 is unaffected.

Disputes: none. The only `disput*` hits are the artifact's "No
disputed finding" and the C1 recommendation's conditional
fallback, which Worker-2 did not take.

Failability (all at the verifier address): F2 -
`failability-f2.json` restores the exact deleted prebuild line;
`workspace.py prove` at `review-20260929T015031-7b7faf` exit 0:
baseline 8 passed, mutant fails exactly `expect_failing`
(`test_windowed_fast_path_constructs_no_fallback_queryset`,
`assert 4 == 0` - all four parents), restore byte-proved.
PINNED. On the script's "weakly pinned" boilerplate: judged not
weak - a 1-row exact failure with 7 unaffected compat pins and a
count-matching assertion (`4 == 0`) is a precise pin, and the
record prescribes exactly one counter test. F1/F3 -
`failability-f1f3.json` (forced memo miss; restored pre-F3
conjunct order) at `review-20260929T015318-0ef313` exit 0: both
entries "behaviour preserved", 7 passed baseline and mutant,
restores proved - F1/F3 are behavior-neutral, their only
observable delta the measured timing. Test tier: the F2 counter
is package tier (`tests/test_relay_connection.py`) and that is
correct - a related-manager construction count is unobservable
over the GraphQL wire (served pages are identical with and
without the prebuild), so no live-tier test can pin it; served
behavior is pinned at package and live tiers beside it. The test
uses inline creates per the library-acceptance convention.

Judgment calls upheld: no F1 `is` pin (concur - vacuous with and
without the memo; growth/clear attacked directly instead, attack
A); F2 factory shape with preserved error precedence (concur);
bench directional (concur, corroborated above).

Cells: concur that sharded and pg are inapplicable by
construction for F1-F3, C1 and prose (pure-Python memo,
allocation removal, conjunct reorder, import hoist - the diff
carries no alias, `using`, dialect or vendor token; grep exit 1)
and for H1 (post-fetch list trim on materialized edges). pg is
additionally exercised by the bench pair above (query counts
identical). No cell left unverified.

Fingerprints: package `connection.py`
c8b9670109d05f9a09f2f8a113e491baa7511317,
`tests/test_relay_connection.py`
fe2b2d24ab6e71e6238183690b02821abb239497,
`test_keyset_api.py`
88a432b0858c54afc91a79cedbf8938983ab2c23 (all equal Worker-2's
after-values; the tree held still throughout). Scratch
(`verify-performance-1/`): `attack_fallback_supply.py`
32a125fdf487004c7e9fe5eb54da04c2c6bad24f,
`attack_memo_scope.py`
bf832258929830890d7b5c3404a9a0fa828bd7eb,
`failability-f1f3.json`
69f839a8a03103dd35a7ae911fb5418961bf90c0,
`failability-f2.json`
1f147f19e9c58bf1dd0ff3f54d5c2006f63805b3,
`nested_fetch_after.json`
6202b7ec77d3d30bc000ab56f5b20d904e199a8c,
`nested_fetch_before.json`
83240d01fdfca3a9b4eb12c6d0e3d8bf0b732e42.

Handoff: Pass-1 Performance verifies clean: F1/F2/F3 landed as
recommended, every number reproduced or corroborated, both
judgment calls (F1 variance, bench drift) resolve without
revision, and the memo/factory/reorder withstand direct attack.
The one red item is cross-axis and must not ride home silently:
the H1 async trim self-awaits (named gap above, High,
deterministic, item-caused), needing a Mechanics re-pass whose
acceptance is the two async nodes plus the H1 live row; the
re-pass touches no Performance line (bind the inner awaitable),
so no Performance re-verification should be owed beyond a
rerun of the 7 pins. The next Performance reader on this file
should watch the R1 unplanned shapes (still 1+N by planner
scope) and the absolute bench medians (cross-session drift
proved at 2.4x on identical code - within-pair deltas with a
per-parent control only).
