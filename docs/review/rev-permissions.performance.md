# Review · Performance: `django_strawberry_framework/permissions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=623c43216c5c50961b3dc0f5448ae6d21926ece1

## Trace

Target read whole (740 lines, blob `ef66f8b9`; dirty with concurrent
work at read time: `git diff --stat` 25 insertions, 24 deletions vs
HEAD, attributed to other sessions, not graded; `git diff` vs
ITEM_BASELINE is empty, so the read is exactly the item baseline).
Skeleton `docs/review/rev-permissions.md` read (`Status: reviewing`,
blank Path class); sibling axis records
`rev-permissions.mechanics.md` / `rev-permissions.comments.md` absent
(concurrent run, not yet written). Plan
`docs/review/review-0_0_15.md` read including `## Owned changes` (no
row names this target). Orientation: `review_inspect.py` overview +
stripped source under `<root>/performance/inspect/` (json
`<root>/performance/permissions.json`): 1 per-row lead (discharged
below: the loop is over edges, not rows), 3 hot entry points (+8
reachable), 1 import-time work item (one `ContextVar` call, trivial).

Hot-path map (callers traced by `rg` over the package, tests,
examples):

- `django_strawberry_framework/permissions.py::apply_cascade_permissions`
  runs once per consumer `get_queryset` call that cascades, i.e. once
  per resolver per request on every cascaded type. Production callers:
  all four products schema hooks
  (`examples/fakeshop/apps/products/schema.py`: Category / Item /
  Property / Entry `get_queryset`), each on every non-staff request.
  Per call it seals the root
  (`django_strawberry_framework/utils/querysets.py::_prepared_visibility_source`),
  validates `fields=`, installs one `_TraversalState` frame, and walks
  the model's cached `_EdgePlan`.
- `django_strawberry_framework/permissions.py::_walk` runs once per
  edge of the walked model: `registry.get` resolve, `base_queryset`
  seed, one edge path-frame install, one
  `apply_type_visibility_sync` (source seal + consumer hook + result
  seal), one `_validated_target_subquery` re-projection, one
  `Q(...__in...)` + `queryset.filter` composition (F1).
- `django_strawberry_framework/permissions.py::aapply_cascade_permissions`
  runs the same sync walk inside one
  `run_in_one_sync_boundary` hop per call; no per-edge and no per-row
  await exists.
- Cold: `_edge_plan` classification (runs once per model, then
  `lru_cache` hits), `_validate_fields` (early `None` return on the
  shipped full-walk shape), `_cycle_error` and both error renderers'
  `_render` bodies (defect path only).

`Path class: hot` - the root call runs once per resolver per request
on every cascaded type, and the walk body runs once per forward edge
of the walked model.

Measurements, copy `review/permissions.py/performance` (slot-2),
package digest `sha256:b9d32f80...e641a` (tree as it stands; not the
plan's bench-baseline digest, so every figure is self-referenced and
every before/after compares within this digest). Provenance: python
3.14.2, django 6.1, strawberry-graphql 0.324.0
(`review-20260929T064043-beb17b`); `importtime_report.py` blob
`15f679c9` (equals gate-2's, differs from the baseline's `bfce84b9`,
so the importtime row compares to nothing there). Every probe below
executes zero SQL (queryset construction, closure timing and call
counts only; no `django_db` marker, no test DB).

- `review-20260929T063516-0f2854`: `probe_cascade_costs.py` (probe
  blob `9c726cdf`; products Entry/Item/Property/Category types,
  identity hooks, timeit-style interleaved A/B medians, 3000 iters +
  300 warmup per arm, alternating per round): full 2-edge cascade
  275.1 us; chained `.filter` x2 66.79 us vs single `.filter(a, b)`
  58.96 us (delta 7.8 us; the probe asserts `str(query)` identity
  between the shapes); eager renderer construction 1.458 us vs lazy
  closure shape 0.167 us (delta 1.29 us); `truth.name` 0.375 us;
  `_edge_plan` hit 0.083 us; `registry.get` 0.166 us; edge
  ContextVar frame 0.959 us; `base_queryset` 3.92 us; source seal
  19.58 us; result seal 19.42 us. JSON
  `<root>/performance/costs.json`. (The first run,
  `review-20260929T063501-74b54b` exit 1, died on a probe-side
  model/queryset mismatch before measuring; superseded, not cited.)
- `review-20260929T063709-f9fc4d`: same probe rerun: full cascade
  270.7 us; chained/single 66.83/59.13 us (delta 7.7 us);
  eager/lazy 1.416/0.167 us (delta 1.25 us); all other rows within
  2%. JSON `<root>/performance/costs-rerun.json`.
- `review-20260929T064027-9ba9a6` and rerun
  `review-20260929T064034-35b8bd`: `probe_cascade_pins.py` (probe
  blob `2050c28a`; deterministic counts, the Proof vehicle):
  `cascade_filter_calls_2edge=2`, `renderer_truth_name_calls=3`,
  both runs identical.
- `review-20260929T063721-a74342`: `importtime_report.py --rounds
  5`: `django_strawberry_framework.permissions` self 475 us,
  cumulative 475 us (its dependencies are imported by the package
  root regardless), of package self 29266 us over 69 modules. JSON
  `<root>/performance/importtime.json` (R12).
- `review-20260929T063741-b0b988`: the existing zero-round-trip pin
  `tests/test_permissions.py::test_identity_hook_targets_compose_default_manager`,
  `1 passed` (before-state green; the subqueries compile into the
  caller's single `SELECT`).

No bench-baseline figure moves: no bench runs the cascade
(`bench_plan_cache.py`, `bench_optimizer_walk.py` and
`bench_nested_fetch.py` build no cascaded `get_queryset`), and both
findings are sub-bench-spread CPU covered by deterministic pins
instead.

Cells: default measured. Sharded and pg are `inapplicable by
construction` for F1-F2 (the probes execute zero SQL; the changed
lines move no alias read, no query text and no dialect branch: one
`.filter` call grouping and two closure bodies). The alias behaviour
itself is pinned by the `FAKESHOP_SHARDED`-gated
`test_multi_db_subquery_pinned_to_caller_alias`, which these
findings do not touch. The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/permissions.py`
ef66f8b9ce5c17813558d10150f945d0c9420bef;
`django_strawberry_framework/utils/querysets.py`
8fc556d582b313e4aed7cddaa15f9a8480d88a46;
`django_strawberry_framework/registry.py`
492654d219d1061fef33f186d962dc5369b71ebe;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`examples/fakeshop/apps/products/schema.py`
04a5afe3dddff9279660ae1370924e03857d57e7;
`tests/test_permissions.py`
c22af72892e3430ea51d5e4bef0112871445c604;
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef;
`<root>/performance/probe_cascade_costs.py`
9c726cdf284aebe7d34860ed34f43da08a3c10b6;
`<root>/performance/probe_cascade_pins.py`
2050c28aa499432f02ba148d79646926d03adb79.

## Findings

### High

None.

### Medium

#### F1: per-edge `.filter()` re-clones the accumulated subqueries

- Observation:
  `django_strawberry_framework/permissions.py::_walk` calls
  `queryset.filter(condition)` once per walked edge. Every call
  clones the queryset, and every clone after the first deep-copies
  the `__in` subqueries the earlier edges already composed, so
  subquery cloning is quadratic in the edge count. One
  `.filter(*conditions)` builds the identical `WHERE` with a single
  clone of the un-narrowed query.
- Evidence: `review-20260929T063516-0f2854` (rerun
  `review-20260929T063709-f9fc4d`): chained 2-edge composition
  66.79 us vs single-call 58.96 us, delta 7.8 us (rerun 7.7 us),
  interleaved medians over 3000 rounds; the probe asserts
  `str(query)` identity between the shapes. Full 2-edge cascade
  context is 275.1 us (rerun 270.7 us), so the shape costs ~2.8%
  at 2 edges and grows with each further edge.
- Impact: ~-7.8 us per 2-edge cascade call; no bench row moves
  (no bench runs the cascade).
- Path class: hot - once per resolver per request on every
  cascaded type, once per edge inside the walk.
- Severity: Medium - measured structural hot-path cost without
  N+1 (quadratic-to-linear clone shape, three orders above the
  nanosecond Low precedent, fix keeps the code as plain).
- Instrument: interleaved A/B timeit medians (B1 pair) plus the
  deterministic counting probe. Before: 2 `.filter` calls per
  2-edge cascade (`review-20260929T064027-9ba9a6`, rerun
  `review-20260929T064034-35b8bd`); chained/single delta 7.8 us.
  After (predicted): 1 `.filter` call; ~-7.8 us on the 2-edge
  shape. Delta (predicted): -1 call, -(n-1) `Query` clones.
  Permanent test: Worker-2 lands the counter as a deterministic
  package test (0-edge root issues 0 calls; 2-edge Entry with
  identity hooks issues 1); call counts are unobservable on the
  wire, so package tier is correct, while SQL identity and the
  zero-round-trip shape stay pinned where they are
  (`test_identity_hook_targets_compose_default_manager` with
  `django_assert_num_queries(1)` plus the live
  `test_cascade_query_count_fixed`). No absolute time threshold
  in the Proof (a 3% delta sits below cross-session drift);
  Worker-2 reports interleaved before/after B0 medians from the
  `before` + `implement` copies instead.
- Recommendation: accumulate the per-edge conditions in a list
  and, after the loop, `if conditions: queryset =
  queryset.filter(*conditions)`. Keep the per-edge `Q` shape,
  the nullable `__isnull` disjunct and the edge order identical.
- Must not change: the composed SQL (identical `WHERE`; the
  probe asserts `str(query)` equality); still zero evaluation
  (pure composition); the 0-edge path still issues no `.filter`
  call (guard the empty list: a bare `.filter()` would add a
  pointless clone).
- Proof:
  - `uv run python scripts/workspace.py run review/permissions.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/permissions/performance/probe_cascade_pins.py` prints `cascade_filter_calls_2edge=1` (before `2`).
  - `uv run python scripts/workspace.py run review/permissions.py/verify-performance-<n> -- pytest tests/test_permissions.py::test_identity_hook_targets_compose_default_manager tests/test_permissions.py::test_unregistered_target_model_skipped --no-cov -p no:cacheprovider` reports `2 passed`.
- Freshness: all files in `## Trace`.

### Low

#### F2: error renderers compute defect-only names on the happy path

- Observation:
  `django_strawberry_framework/permissions.py::_root_error_renderer`
  computes `truth.name(cls)` and
  `django_strawberry_framework/permissions.py::_edge_error_renderer`
  computes `truth.name(field.model)`, `truth.name(target_type)`
  and the edge f-string at factory time, on every root call and
  every walked edge, but the values are consumed only by the
  inner `_render` on the defect path. The happy path pays three
  naming calls per root-plus-edge for strings it never reads.
- Evidence: `review-20260929T063516-0f2854` (rerun
  `review-20260929T063709-f9fc4d`): eager construction 1.458 us
  vs lazy closure shape 0.167 us, delta 1.29 us (rerun 1.25
  us); `truth.name` alone 0.375 us; the counting probe reads 3
  naming calls per root-plus-edge construction
  (`review-20260929T064027-9ba9a6`, rerun
  `review-20260929T064034-35b8bd`).
- Impact: ~-1.3 us per root call with one edge (~-2.3 us at 2
  edges, ~0.8% of the 275 us cascade); no bench row moves.
- Path class: hot - same caller as F1.
- Severity: Low - bounded constant shaving on a hot path (same
  family as the implemented nanosecond branch reorder, two
  orders up); rides F1's change to the same file.
- Instrument: the F1 probes (B2 pair + counter). Before: 3
  `truth.name` calls per root-plus-edge; eager/lazy delta 1.29
  us. After (predicted): 0 naming calls at construction; ~-1.3
  us per root-plus-edge. Delta (predicted): -3 naming calls, -1
  f-string. Permanent test: Worker-2 lands a deterministic
  package test asserting both factories build with
  `truth.name` patched to raise (white-box construction pin,
  unobservable on the wire, so package tier); rendered prose
  stays pinned by the existing defect-path nodes in the Proof.
  No time threshold, same drift reason as F1.
- Recommendation: move the `name` / `edge` computations into
  the `_render` closures (capture `cls`, `model`,
  `target_type`, `field`, `alias`; compute on defect). Keep
  every message string byte-identical and both factory
  signatures unchanged.
- Must not change: every rendered message (same names, same
  wording; the move only delays evaluation to the defect it
  describes).
- Proof:
  - `uv run python scripts/workspace.py run review/permissions.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/permissions/performance/probe_cascade_pins.py` prints `renderer_truth_name_calls=0` (before `3`).
  - `uv run python scripts/workspace.py run review/permissions.py/verify-performance-<n> -- pytest tests/test_permissions.py::test_unsealable_hook_query_class_fails_closed_with_cascade_prose tests/test_permissions.py::test_unsealable_root_query_class_fails_closed_with_cascade_prose --no-cov -p no:cacheprovider` reports `2 passed`.
- Freshness: all files in `## Trace`.

Looks-for discharge (REVIEW.md "Performance"), each finding, `none`
with the reason, or rejection:

- N+1 and per-row queries: none. The walk iterates forward edges
  (schema-bounded, typically 1-3), never rows: R1. No `await` per
  row (the async twin awaits one sync boundary around the whole
  walk: R11). No `.filter()` on a prefetched relation (the walk
  composes onto the sealed root, never onto a `Prefetch`
  result): R1.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none in
  the module (`rg` clean): R2.
- `only()` / `defer()` deferred loads: none in the module (the
  only projection is the narrowing `.values(attname)`
  re-projection, which is the contract): R2.
- Unbatched writes: none; the module issues no writes: R2.
- `blog.id` vs `blog_id`: none; no FK dereference, only the
  `field.target_field.attname` metadata read: R2.
- Repeated `_meta` walks, settings reads, regex compilation,
  schema/type lookups: the `_meta` classification is cached in
  `_edge_plan` (83 ns hits): R3. No settings read and no regex
  anywhere in the module (`rg` clean). Per-edge `registry.get`
  is two dict gets: R4.
- `lru_cache` on methods (`B019`): none; `_edge_plan` is a
  module-level function: R10.
- Locks, cache reads, re-parses, extra round trips on a
  per-request path: no locks; no cache reads; zero round trips
  (lazy composition into the caller's single `SELECT`, pinned
  by `test_identity_hook_targets_compose_default_manager` and
  the live `test_cascade_query_count_fixed`, corroborated at
  `review-20260929T063741-b0b988`). The seal cost is R6, the
  identity-hook seal shape is R7.
- Import-time cost: R12 (self 475 us; one `ContextVar`, class
  defs, no settings read).
- Allocation in the hot loop: F1 (per-edge `.filter` clones),
  F2 (per-call/per-edge renderer strings). The remaining
  per-edge allocations are necessary carriers: the `base_queryset`
  seed (R9), the edge path frame (R5), one `Q` and one
  `.values` re-projection per composed edge (the contract).

## Rejected

- **R1: the `_walk` loop composes one lazy subquery per edge.**
  The `review_inspect.py` per-row lead (`queryset.filter` inside
  the `for`) is the edge loop, not a row loop: it iterates the
  cached plan tuple (schema-bounded), each iteration composes
  one `__in` subquery, and nothing evaluates (pure `.filter`
  composition into the caller's single `SELECT`). Pinned by
  `test_identity_hook_targets_compose_default_manager`
  (`django_assert_num_queries(1)`, `IN (SELECT` count 2) and the
  live `test_cascade_query_count_fixed`. Reopens if an
  evaluation (`list`, `len`, `bool`, iteration, `.first()` and
  kin) lands inside `_walk`.
- **R2: no cardinality, projection, write or FK-dereference
  reads.** No `len(qs)` / `bool(qs)` / `.count()` / `.exists()`
  (`rg` clean); no `only()` / `defer()`; no writes of any kind;
  the single `target_field.attname` read is field metadata, not
  a row dereference. Reopens if any such read lands on the
  path.
- **R3: `_edge_plan` is looked up three times per root call**
  (`_validate_fields`, the preflight, `_walk`). Each is an
  `lru_cache` hit at 83 ns (`review-20260929T063516-0f2854`),
  ~250 ns total; threading one plan object through all three
  would tangle the validator/walk signatures for noise.
  Reopens if the cache is removed or a lookup shows hot.
- **R4: `registry.get` per edge (166 ns).** Two dict gets plus
  a length check; the registry is mutable until
  `finalize_django_types()` (and tests re-register per test),
  so no sound memo exists at this layer. Reopens if the
  registry gains an immutable snapshot API the walk can key
  off.
- **R5: per-edge path frame (`dataclasses.replace` +
  `ContextVar` set/reset, 959 ns).** Required: the nested
  cascade inside the consumer hook reads the parent's edge
  frame from the var, and no parameter channel passes through
  consumer code, so the frame must be installed before the
  hook runs. Reopens on a cycle-path redesign that carries the
  path out of band.
- **R6: the seals dominate (~78 us of the 275 us cascade) but
  are the security boundary.** Source seal 19.58 us, result
  seal 19.42 us, paid once at the root plus twice per edge
  (the `apply_type_visibility_sync` source/result pair). The
  rebuild is the fail-closed contract (spec-045 Decision 3: a
  hook can mutate the source it was handed, so the result is
  always re-sealed), owned by
  `django_strawberry_framework/utils/querysets.py`, out of this
  item's fence; no worker weakens an authorization boundary to
  buy a number. Reopens only with a boundary-owned fast path
  plus its proof, at the `utils/querysets.py` item.
- **R7: identity-hook targets pay full seals per edge.**
  Deliberate on both sides: registration (not hook
  customization) is what puts a target inside the visibility
  contract, because a filtered `_default_manager` IS the
  policy of a proxy type; and the single sync-misuse site
  (Decision 10) forbids re-deciding routing here. A
  `has_custom_get_queryset` fast path that skipped validation
  for any input class would weaken the fail-closed posture of
  R6. Same reopen trigger as R6.
- **R8: `_validate_fields` rebuilds the cascadable name set.**
  Only on the `fields=` path; shipped hooks pass `fields=None`
  and take the early return, so the hot shape pays nothing.
  Reopens if `fields=` becomes the hot shape.
- **R9: `base_queryset` per edge (3.92 us).** Each edge needs
  its own fresh target-model seed pinned to the root alias;
  no sharing is possible across edges. Reopens on a shared-seed
  design that preserves per-edge alias pinning.
- **R10: `lru_cache` placement.** `_edge_plan` is a
  module-level function over an immutable-metadata argument;
  no method cache and no `B019` anywhere in the module (`rg`
  clean). Reopens if a cache moves onto a method.
- **R11: the async twin awaits once per walk.** A single
  `run_in_one_sync_boundary` hop around the whole sync walk
  (the neutral one-boundary owner); no per-edge and no per-row
  await exists. Reopens if a hop appears inside the edge
  loop.
- **R12: import-time cost.** Self 475 us, cumulative 475 us
  (`review-20260929T063721-a74342`): class defs, one
  `ContextVar`, no settings read. The heavy imports
  (`utils/querysets.py`, `registry.py`) are pulled by the
  package root regardless of this module. Reopens if
  self-time grows past budget or a new eager dependency
  lands.
- **R13: sub-microsecond residue.** `names_to_walk == set()`
  allocates one empty set on nested calls only; `model_for` /
  `_captured_model` re-read `__django_strawberry_definition__`
  per seal (single-digit attribute reads, and threading
  `model=field.related_model` through is equivalence-unproven
  for proxy/concrete pairs). Each is noise beside the ~39 us
  per-edge seal pair. Reopens if a profile shows any of them.

Handoff: F1 and F2 compose (both shave the same 275 us
composition; implement both, then measure after-numbers once
with interleaved before/after B0 medians from the `before` +
`implement` copies). The dominant cascade cost is the R6 seal
pair in `utils/querysets.py`, deliberately rejected here under
the no-weaken rule; any future seal-cost work belongs to that
item, never to a cascade-local bypass. Left for siblings: the
vestigial `_cascadable_edges` / `_cascadable_edge_names` pair
(zero production readers) costs nothing at runtime and is
already KANBAN-homed for deletion, so no Performance finding
and no Cross-axis entry; Mechanics owns it. Sibling axis
records were absent when this was written. Cells sharded/pg
are claimed inapplicable by construction (zero-SQL probes;
findings move no alias read, query text or dialect branch);
the verifier judges.

## Verify performance

Precondition: `git diff ITEM_BASELINE --` on the two touched
paths is byte-identical to `docs/review/temp-tests/permissions/diff/pass-1.diff`
(326 lines, `diff -q` clean), so the shared tree carries exactly
the change under grade. Fingerprints: shared `permissions.py`
`6c97d887`, `tests/test_permissions.py` `c113d05e`.

Address note: the pool holds 4/4 bound copies (`before`,
`performance`, `mechanics`, `implement`), so no
`verify-performance-1` copy could bind. All after-side runs went
to `review/permissions.py/implement` (slot-4, hashed `6c97d887` /
`c113d05e`: exactly the shared pass-1 tree) and all before-side
runs to `review/permissions.py/before` (slot-1, hashed
`ef66f8b9` / `c22af728`: exactly the ITEM_BASELINE blobs), every
run read-only except the one overlay window below, which was
restored byte-identical (`cmp` clean, hashes re-verified).
Before digest `sha256:b9d32f80...e641a` matches the reviewer's
measured tree; after digest `sha256:04203a6a...5dba6`. The two
copies differ only in the pass-1 pair (recursive diff over the
package, tests and example sources, caches excluded). Flag for
Worker-0: release the reviewer copies before dispatching the
Comments verifier, which will hit the same bind wall.

### F1 (per-edge `.filter()` clones): pass

- Proof 1: `probe_cascade_pins.py` (blob `2050c28a`, as
  recorded) prints `cascade_filter_calls_2edge=1` after
  (`review-20260929T071035-e12e53`) and `2` before
  (`review-20260929T071112-ae2d7d`). Single guarded
  `.filter(*conditions)` confirmed in the diff; the `if
  conditions:` guard stands.
- Proof 2: `test_identity_hook_targets_compose_default_manager`
  + `test_unregistered_target_model_skipped` report `2 passed`
  (`review-20260929T071044-15b220`).
- Failability: the new `test_two_edge_cascade_issues_a_single_filter_call`
  fails on the before copy (`assert 2 == 1`, old code issues
  exactly the reviewer's before-count) and passes after
  (`review-20260929T071121-6908b8` before-overlay run,
  `review-20260929T071101-b4f881` after run, `3 passed`
  incl. the sibling pins). `prove` pins the revert mutant to
  exactly its row (`review-20260929T071145-d77982`, 3/3
  `pinned`, implement copy hash-verified intact afterwards).
- SQL byte-identical: full 2-edge cascade `str(query)` sha256
  identical before/after (`review-20260929T071434-122c84` /
  `-186bf7`, diff of rendered bodies empty), and the B1
  `str(chained.query) == str(single.query)` assert passed in
  all 12 interleave runs on both trees. Zero evaluation
  preserved (composition only; the `django_assert_num_queries(1)`
  pin in Proof 2 still greens). 0-edge path issues no call on
  either tree (`test_zero_edge_root_issues_no_filter_call`
  passes before and after, correctly: its failability is the
  guard-drop mutant, `prove`-pinned exact, since true-before
  already issues no call).
- Interleaved B0 (6 rounds, alternating before/after, same
  `9c726cdf` instrument both sides): before medians 274.00,
  263.83, 263.67, 276.17, 263.92, 266.71 -> median 265.31 us;
  after medians 244.21, 243.96, 246.33, 246.96, 248.17, 247.17
  -> median 246.65 us; delta -18.67 us (-7.0%), every after
  round below every before round. Every control row flat
  (seals +0.00/+0.10, B1 pair -0.10/-0.06, plan/registry/frame/base
  within 0.02 us), so the delta is the change, not drift. It
  exceeds the B1 plain-subquery reference (-7.6 us in-tree)
  because the cascade clones sealed, not plain, subqueries;
  direction predicted, magnitude floored, no row moves wrong.
  Run ids: before `review-20260929T071246-feaebd`,
  `-071251-e39917`, `-071255-e75255`, `-071305-7c8d2a`,
  `-071309-c15d89`, `-071314-4bb6e5`; after
  `review-20260929T071248-369fc4`, `-071253-38e789`,
  `-071257-859061`, `-071307-79900f`, `-071312-68073c`,
  `-071316-318537`.

### F2 (eager renderer names): pass

- Proof 1: same probe prints `renderer_truth_name_calls=0`
  after (`-e12e53`) and `3` before (`-ae2d7d`).
- Proof 2: the two `unsealable_*_fails_closed_with_cascade_prose`
  defect-path nodes report `2 passed`
  (`review-20260929T071053-0670c1`).
- Failability: the new
  `test_error_renderers_build_without_naming_calls` fails on
  the before copy (`AssertionError: named at construction`,
  `-6908b8`) and passes after (`-b4f881`); the lazy-naming
  revert mutant `prove`-pinned exact (`-d77982`).
- Messages byte-identical: all 11 rendered messages (5 root +
  6 edge codes, fixed details) byte-equal before/after
  (`-122c84` / `-186bf7`, empty diff). Signatures unchanged:
  the diff touches neither factory `def` line, only moving
  the `name` / `edge` computations inside `_render`.
- In-cascade effect: `renderer_eager_us` 1.416 -> 0.333
  (-1.08 us per root-plus-edge construction) in the same
  interleave; the lazy-shape control flat at 0.167 both sides.

### Whole-diff reading (Performance)

The pass-1 diff outside F1/F2 is Comments prose (docstrings,
one import comment, test prose) plus test imports (`mock`,
`truth`, two renderer names) that never enter the package
graph. No hot-path line beyond the two findings moves; the
`conditions` accumulator adds one list plus two appends
(~0.1 us, inside the measured B0 win). Re-checked timed
shapes only, per brief: every figure above was measured on
the final tree carrying the Comments edits.

### Attacks

- Other cell: `test_multi_db_subquery_pinned_to_caller_alias`
  passes under `--cell sharded` on the implemented tree
  (`review-20260929T071446-2e6e07`, `1 passed`): F1's
  regrouping preserves Decision-8 alias pinning on the
  multi-db path. Stronger than inapplicable.
- Before/after message + SQL identity probe (scratch
  `probe_identity.py`, 11 codes + cascade SQL sha): empty
  diff, both sides exit 0.
- No new finding. R6 seals deliberately untouched (flat in
  the interleave, as rejected).

### Cells judged

- default: measured throughout.
- sharded: reviewer claimed inapplicable by construction;
  judged stronger: the zero-SQL argument holds for the
  probes, and the one reachable sharded behavior (alias pin)
  is verified green above, so the cell is covered, not
  merely excused.
- pg: concur inapplicable by construction. The change moves
  no query text (SQL sha identical), no alias read and no
  dialect branch — the same `Q` objects in the same order
  reach Django's compiler, which is backend-agnostic — and no
  pg-gated test covers the cascade (grep clean over the
  package and live cascade modules), so there is nothing to
  execute there.

### Bench rows

No bench row moves, verified by construction: zero hits for
`cascade|permissions|get_queryset|apply_cascade|aapply` across
`bench_plan_cache.py`, `bench_optimizer_walk.py`,
`bench_nested_fetch.py`, `_bench_common.py`,
`importtime_report.py` and `count_queries.py`, plus
`strategy_schemas.py` (whose synthetic non-cascading types
feed the one bench that executes queries; the plan benches
never execute a resolver). Importtime cannot move either:
no new module, no new import in the target (moved lines +
prose only). Worker-2 reported no bench delta; corroborated.

Scratch: `docs/review/temp-tests/permissions/verify-performance-1/`
(`proof-pins-after.log`, `proof-pins-before.log`,
`proof-f1-pytest.log`, `proof-f2-pytest.log`, `pins-after.log`,
`pins-before.log`, `prove-manifest.json`, `prove.log`,
`run_costs_probe.py`, `probe_identity.py`,
`identity-before/after.log`, `attack-sharded.log`,
`interleave/round-*-{before,after}.{json,log}`).

Status: verified

Handoff: Both findings land exactly as recorded, with
failability shown two independent ways (true-before runs and
exact mutants) and the B0 win (-18.67 us interleaved) meeting
the predicted direction above the reference floor. The only
judgment call a later reader could revisit is the 0-edge pin
passing on true-before: correct by Must-not-change (the
before tree already issues no call there), pinned instead by
the guard-drop mutant. The pool-full address substitution is
provenance-complete (every run id cites its real address and
digest); Worker-0 must release reviewer copies before the
Comments verifier binds. No open threads on the Performance
axis.
