# Review · Performance: `django_strawberry_framework/resource_policy.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e3af18216bc75ecbd6bd080d78cdb1b209458e79

## Trace

Read the whole live target (1371 lines) plus every hot-path helper it calls
per field: `django_strawberry_framework/utils/policies.py::copy_policy`,
`django_strawberry_framework/utils/policies.py::canonical_policy`,
`django_strawberry_framework/utils/truth.py::is_instance`,
`django_strawberry_framework/utils/context.py::get_context_value`,
`django_strawberry_framework/utils/operation_lease.py::OperationLease.held`,
`django_strawberry_framework/utils/querysets.py::normalized_row_source`.
Traced every package caller of the per-field seams: `policy_from_info` from
`_raw_list_bound`, `list_field.py:447` (`_normalize_list_arguments`),
`utils/connections.py:758` (keyset-cap ceiling), `check_deadline:939`
(exceptional only); `check_deadline` from `connection.py:1356`,
`relay.py:593,677`, `types/resolvers.py` (3 single-object resolvers +
both `bounded_rows` colors via `_raw_list_bound`), `mutations/resolvers.py:204`;
`begin_resource_budget` / `end_resource_budget` once per operation from
`extensions/resource_policy.py`. `ResourcePolicy.narrowed` has no package or
example caller (consumer/test-only API). `resource_policy_setting` is called
only through `resolve_policy` at schema construction. No sibling axis record
existed when this pass closed, so no Cross-axis proofs were owed.

Path class: hot. `check_deadline` runs per collection field per request and per
parent row on nested relation paths (the single-object resolvers call it before
any elision check; the many-side reaches it through `bounded_rows` per parent);
`policy_from_info` runs per collection field per request; `begin` / `end` run
once per operation.

Fingerprints (`git hash-object`) of everything inspected: target `cc3f9d80`
(dirty vs HEAD at read time: 22 insertions, 34 deletions of concurrent work, not
this item's); `utils/policies.py` `0a2b7dba`; `utils/truth.py` `d5c96bc8`;
`utils/context.py` `edebf0ea`; `utils/operation_lease.py` `10c164b7`;
`utils/querysets.py` `8fc556d5`; `list_field.py` `f5b0183e`;
`utils/connections.py` `efcf749a`; `types/resolvers.py` `640905c6`;
`conf.py` `3820c575`; `connection.py` `1fca6266`; `relay.py` `f5760b45`;
`extensions/resource_policy.py` `0134d83a`; `mutations/resolvers.py` `c9cff059`;
`tests/test_resource_policy.py` `585c536e`.

Looks-for discharge (each entry: finding, none+reason, or rejection+trigger):

- N+1 / per-row queries: none. The module emits zero queries: no manager or
  queryset evaluation call exists in it; the only queryset interaction is
  slicing, which bounds rows (adds `LIMIT`) rather than multiplying queries.
- `await` per row: none. `_windowed_rows_async` pulls one async stream to its
  bound with an early close; the awaits feed a single stream, not per-row
  queries, and early termination closes rather than draining.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. The single `len()`
  in the module is `len(rows)` on a Python list the async seam built itself.
- `only()` / `defer()`: none (no occurrences).
- Unbatched writes: none (the module performs no writes at all).
- `blog.id` vs `blog_id`: none (no model attribute reads at all).
- Repeated `_meta` walks / settings reads / regex compilation / schema-or-type
  lookups per request: none. No `_meta`, no `re`, no registry/schema import;
  the one settings reader is reached only at schema construction (see Trace).
- `lru_cache` on methods: none (no `lru_cache` in the module).
- Locks, cache reads, re-parses, extra round trips on the per-request path:
  none. The per-field path is a `ContextVar` get, dict/attribute reads, and
  type tests; no lock, cache, parse, or I/O.
- Import-time cost: none. `importtime_report.py --rounds 5` at
  `review-20260929T095501-085c97` gives `resource_policy` self 1239 us
  (dataclass processing; the two policy constructions are a fraction of it),
  cumulative 28.2 ms in shared package imports; no settings read at import
  (the only module-level calls are `ResourcePolicy()`, `canonical_policy`,
  `ContextVar`).
- Allocation in the walk: none. The module holds no walker loop; the async
  seam's list is the result itself, and the `[*notes, note]` copy sits on the
  exceptional cleanup path only.
- Per-field policy copy cost: R1 (rejected, measured).
- `_deadline_expired` `None` classification cost: F1 (finding, measured).
- `narrowed` per-call `fields()` set: R2 (cold). Per-operation canonical
  validation: R3 (boundary). `normalized_row_source` subclass probe per call:
  R4 (owned by the `utils/querysets.py` item). `check_deadline` placement
  ahead of the FK-elision early return: R5 (owned by the `types/resolvers.py`
  item; reported as a Routed lead).

Cells: sharded and pg are inapplicable by construction for F1: the finding
moves no query, alias, or dialect decision (the module holds no
`connections[]` use and no vendor branch; slicing is backend-agnostic `LIMIT`),
and its Proof probe opens no database. The behavior pins ran in the default
cell. No bench figure moves (sub-spread CPU delta; see F1).

## Findings

### High

None.

### Medium

#### F1: `_deadline_expired` pays three MRO-walking type tests to classify `None`

- Observation: `django_strawberry_framework/resource_policy.py::_deadline_expired`
  classifies the `None` deadline - the value every `check_deadline` call sees
  in the default configuration (`execution_deadline_seconds` defaults to
  `None`, and the mirror stashes `None`) - by falling through to three
  `django_strawberry_framework/utils/truth.py::is_instance` calls, each of
  which fetches a real MRO and identity-scans it. `None` is the single most
  common input and takes the slowest branch.
- Evidence: timeit medians (20k x 9, plus an interleaved 20k x 11 A/B pair) at
  `review-20260929T095422-f72ee2` (fresh copy, package digest
  `sha256:d677641c6051db8c14aabb6d287edcae03b202a526e1c0acb89482861e79cbbb`):
  `_deadline_expired(None)` 834.6 ns, one `truth.is_instance(None, bool)`
  247.3 ns, `check_deadline` armed/no-deadline 1012.4 ns vs armed/live-deadline
  361.4 ns. The interleaved A/B of current vs a `None`-first variant measures
  843.5 ns vs 29.0 ns (delta +814.6 ns). The `None` branch is behaviorally
  `return None` today (not a builtin number, not a bool, not int/float), so a
  leading `if deadline is None: return None` is identical on every input.
- Impact: `check_deadline` runs per collection field per request and per
  parent row on nested relation paths (see Path class); ~0.8 us of its ~1.0 us
  default-configuration cost is this classification. A 100-row nested read
  pays ~80 us of it per request.
- Severity: Medium (measured cost on a hot path, no N+1).
- Recommendation: open `_deadline_expired` with `if deadline is None: return
  None`. One line, same rule, no new path: every other input flows exactly as
  today.
- Must not change: the full truth table - absent / cleared / `None` / `bool` /
  non-numeric answers `None` (request runs); exact builtin numbers go to the
  clock; numeric subclasses, non-finite values, and clock-overflowing ints read
  as expired. The narrowing contract in `_effective_deadline` is untouched.
- Proof:
  - `uv run python scripts/workspace.py run review/resource_policy.py/verify-performance-<n> -- python /Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015/docs/review/temp-tests/resource_policy/performance/probe_hot.py` prints `deadline_expired_none: median_ns=` below `150.0` and `check_deadline_armed_none: median_ns=` below `600.0` (before `834.6` / `1012.4`).
  - `uv run python scripts/workspace.py run review/resource_policy.py/verify-performance-<n> -- pytest tests/test_resource_policy.py::test_no_stashed_deadline_leaves_the_request_running tests/test_resource_policy.py::test_a_non_numeric_stashed_deadline_leaves_the_request_running tests/test_resource_policy.py::test_a_future_deadline_leaves_the_request_running tests/test_resource_policy.py::test_a_passed_deadline_reports_the_configured_seconds_not_the_clock tests/test_resource_policy.py::test_a_numeric_subclass_deadline_fails_closed_instead_of_being_asked tests/test_resource_policy.py::test_a_non_finite_deadline_with_no_budget_armed_fails_closed tests/test_resource_policy.py::test_a_narrowing_deadline_arrives_where_the_operation_configured_none --no-cov -p no:randomly` reports `9 passed` (before-state green at `review-20260929T095430-cfb4c7`).
- Freshness: all files in `## Trace`.
- Path class: hot - per collection field per request, per parent row on nested
  relation paths (see `## Trace`).
- Instrument: `timeit` median over 20k x 9 repeats (A/B pair interleaved 20k x
  11); no database opened.
- Before: `_deadline_expired(None)` 834.6 ns; `check_deadline` armed/None
  1012.4 ns (run `review-20260929T095422-f72ee2`).
- After (predicted): ~29 ns unit (the A/B variant leg); seam ~200 ns.
- Delta (predicted): ~-0.8 us per `check_deadline` call in the default
  configuration. No bench figure moves (sub-spread).
- Permanent test: none timing-based (flaky by construction); behavior pinned
  by the 9 existing nodes in the Proof (the change is behavior-identical, so no
  new test can pin the saving), the number reproduced by the probe rerun.

### Low

None.

## Rejected

- R1: per-field `policy_from_info` copies the whole 20-field policy to read one
  int (`_raw_list_bound` reads `.max_list_rows`, the keyset-cap seam
  `.max_page_size`; a list field with arguments pays both copies). Measured:
  `copy_policy` 428.9 ns of `policy_from_info` armed 525.0 ns. Rejected: the
  copy is the authority boundary (the armed object and the default singleton
  must never reach consumer code), and a no-copy internal reader would restate
  the armed-outranks-mirror precedence plus the exact-type rule beside
  `policy_from_info` - a second security-read path that can drift. Trigger:
  a third per-field call site appears, or copy cost exceeds 2 us; revisit then
  as ONE shared internal reader, never per-site shortcuts.
- R2: `ResourcePolicy.narrowed` rebuilds the `{field.name}` known-set via
  `fields()` per call. Cold: zero package or example callers (consumer /
  test-only API). Trigger: a per-request package caller appears.
- R3: `begin_resource_budget` re-validates all 20 bounds per operation
  (`canonical_policy`; the begin/end pair measures 7.8 us once per request).
  The re-validation is the boundary: the values are re-read from an object the
  caller retained and validated on ordinary terms. Trigger: a second
  begin/end pair per request appears (nested budgets restore; measure then).
- R4: `_windowed_rows` pays `normalized_row_source`'s
  `truth.is_subclass(source_type, QuerySet)` probe even for plain lists. Single
  necessary call at this seam; the probe's cost is owned by the
  `utils/querysets.py` item's Performance pass. Trigger: that item's verdict.
- R5: the forward-FK resolver in `types/resolvers.py` calls `check_deadline`
  before its elision early return, so an elided (zero-work) row still pays the
  ~1.0 us check. Call placement in another pending item's file, and moving a
  safety check is a boundary tradeoff for that item's Mechanics pass; F1
  shrinks every call regardless. Reported as a Routed lead for the
  `types/resolvers.py` Performance pass. Trigger: that item's review.

Handoff: The file is genuinely lean on the hot path - ContextVar plus copies
plus type tests, zero queries, zero per-request settings reads, zero caching or
locking to tune - so F1 (the `None` branch dominating `check_deadline` in the
default configuration) is the only measured cost worth a code change, and R1 is
the only other candidate that survived measurement (rejected on
security-rule singularity, not on size). Beyond the record: the per-row
`check_deadline` fan-out through the single-object resolvers (R5) is where any
future deadline-seam work lives, and it belongs to the `types/resolvers.py`
item, not here. The plan's Routed lead from conf.py Comments ("Probed by the
hunt" wording in `tests/test_resource_policy.py`) is prose with no Performance
content; it routes onward to this item's Comments pass untouched. Open thread
for Worker-0: none on this axis - F1's Proof is self-contained at
`review/resource_policy.py/verify-performance-<n>`, pins are green
before-state, and sharded/pg are inapplicable by construction with the reason
stated.

## Verify performance

Precondition: `git diff ITEM_BASELINE --` on the three touched paths is
byte-identical to `docs/review/temp-tests/resource_policy/diff/pass-1.diff`
(`cmp` clean, checked twice: before the first proof run and after the last),
so the shared tree carries exactly the change under grade. Fingerprints:
`resource_policy.py` `5b4a80f0`, `tests/test_resource_policy.py` `a52bfb89`,
`test_resource_policy_api.py` `56b70d75` (all match the pass-diff index lines).

Address note: my copy (`review/resource_policy.py/verify-performance-1`,
slot-4) arrived with a gutted venv - every `RECORD`/`METADATA`/`WHEEL` gone
and 7 top-level import files (`typing_extensions.py`, `six.py`, the
`ujson`/`cbor2`/`cffi`/`autobahn` native shims) deleted, so the first two
proof runs failed at `import django_strawberry_framework`
(`review-20260929T101922-b89e6f`, `review-20260929T101947-2ac2a0`, both exit 1;
`--fresh` does not repair it since resync preserves `.venv` and `uv sync`
trusts the surviving dist-info dirs). I removed only my own copy's `.venv`
and let the tool rebuild it authoritatively from the lock on the next
`--fresh` run; every verdict run below is on that rebuilt venv (package
digest `sha256:336177e5...`, the after-change tree). The `before` copy
(slot-1) carries identical damage and is not mine: read-only probe attempted
(`review-20260929T102711-814fcd`, exit 1, same `ModuleNotFoundError`), never
`--fresh`, never edited. Flag for Worker-0: an external actor (or a racing
sync) is gutting copy venvs; slots 2 and 3 are healthy.

### F1 (`_deadline_expired` None-first guard): pass

- Proof 1 (probe): `probe_hot.py` at my address prints
  `deadline_expired_none: median_ns=63.8` (threshold `<150.0`) and
  `check_deadline_armed_none: median_ns=452.8` (threshold `<600.0`)
  (`review-20260929T102308-4b8dd2`, exit 0, fresh copy, shared unmoved).
  The probe's interleaved A/B legs read current 33.0 ns vs none-first 30.1
  ns (delta +2.8 ns), confirming the live code already is the None-first
  shape. Before-side: the reviewer's `review-20260929T095422-f72ee2`
  (834.6 / 1012.4 ns) audits clean (`workspace.py audit`: all 3 cited ids
  ok, digest `sha256:d677641c...`, the before tree); cross-session medians
  compare nothing, and the Proof thresholds are absolute, so no before
  rerun is owed beyond the (unrunnable, documented above) before copy.
- Proof 2 (pins): the 7 listed nodes report `9 passed` (the non-finite node
  parametrizes x3) (`review-20260929T102333-0da734`, exit 0, same digest,
  default cell).
- Behavior identity: 19-row truth table (None / True / False / str /
  object / list / dict / future+past float+int / 0.0 / 0 / int+float
  subclass / nan / +-inf / 10**400) through the live body and a clone of
  the ITEM_BASELINE body (verified textually against
  `git show ITEM_BASELINE:...`: identical except the 2 added lines) -
  19/19 identical and equal to the Must-not-change verdicts
  (`review-20260929T102622-d0e8a8`, exit 0). `_effective_deadline` is
  untouched (0 mentions in the pass diff). The falsy-but-numeric attack
  rows (0, 0.0) still reach the clock and read expired.
- No new timing test: the pass diff adds 0 `def test` nodes and 0
  timing words (`timeit`/`median`/`perf_counter`/benchmark) - by design,
  per the record; the saving is reproduced by the probe rerun, behavior by
  the existing pins.

### Cells: concur inapplicable by construction

Judged independently: the module holds no `connections[]` use, no vendor
branch, no alias or dialect decision (the only `django.db` import is the
`QuerySet` type for slicing checks; the `alias` hits are GraphQL-alias
prose and the SQLite/PostgreSQL mention is an int-width comment, not a
branch); the probe opens no database; the pins are pure deadline logic.
Sharded and pg prove nothing here. Default-cell runs cited above.

### Bench rows: none moves

Static: no bench instrument names a changed seam (`check_deadline` /
`_deadline_expired` / `narrowed` / `resource_policy` absent from all four
benches plus `_bench_common.py`). Plan-cache, optimizer-walk and importtime
never execute the changed lines (plan build / walk / import only); the
change adds no import, so the module count cannot move. Nested-fetch
executes real requests, hence `check_deadline` via the resolvers, but the
delta there is strictly a sub-microsecond saving per call on ~20-100 ms
rows (bound: even 200 calls x 0.6 us is 0.6% of the smallest row, inside
observed cross-run spread) and can only improve, never regress.

### Rejections R1-R5: stand

- R1: both copy arms intact (`policy_from_info` lines 907/909 plus the
  stash line 634); call sites still exactly the recorded four
  (`_raw_list_bound`, `list_field.py:447`, `utils/connections.py:758`,
  `check_deadline:944` exceptional) - no third per-field site. Copy cost
  here 1277.9 ns, still under the 2 us trigger (machine-local reading).
- R2: `narrowed` still rebuilds the known-set per call (line 415) and still
  has zero package callers (`grep \.narrowed(` over the package: empty).
- R3: begin path still re-validates via `canonical_policy` (line 665);
  still one begin/end pair per operation.
- R4: still a single `normalized_row_source` call (line 1059); the owning
  `utils/querysets.py` item is still pending, trigger intact.
- R5: `types/resolvers.py` is untouched by this item (the one
  `types/resolvers` hit in the pass diff is the F2 docstring cite, not a
  code hunk) and its item is still pending - the lead stays routed there.

### L1 + prose edits: disturb no Performance claim

Whole-diff reading: the production hunks are the F1 guard, the L1
cold-path simplification, and two docstring-only hunks; L1's `narrowed`
has zero package callers, so it cannot touch the hot path (its behavior
proof belongs to the Mechanics verifier; observed only: a `None` reaching
the new `value > current` would raise rather than silently narrow - still
fail-closed). Both test files are prose-only by `--code-digest` identity
(tests `sha256:12f02293...` both sides, live-tier `sha256:002fba4e...`
both sides). No dispute was recorded; no new finding on this axis.

Handoff: beyond the record's trace I read the pass diff whole, the live
hunks, the bench scripts (for the no-move bound), and the pool state (for
the venv-damage attribution). The only surprise is environmental: two of
four slots have identically gutted venvs, and `--fresh` cannot heal that
state since the tool preserves `.venv` across resyncs. Open threads: none
on this axis - the before-copy repair (venv rebuild) is Worker-0's call,
and this verdict does not need it.

Status: verified
