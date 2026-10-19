# Review · Performance: `django_strawberry_framework/extensions/debug.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=2dae90d03c0749ebc2f4a512dd7668b1706b51bc

## Trace

Target read whole at live blob `054e04df` (863 lines). The target is dirty vs HEAD
(concurrent work, 4 insertions / 3 deletions: `__init__` now reads
`type(allow_unsafe_production) is not bool` and `truth.describe` where HEAD read
`isinstance` and `describe_value`); construction-time cold path, no performance
content either way. Reviewed as it stands.

Callers and reachability (`rg` over the package, tests, examples): the extension is
strictly opt-in — no default-recipe install (`DjangoSchema` installs only the error
and resource policy extensions; the root package deliberately does not import this
module's name). When installed, `DjangoDebugExtension.on_operation`,
`DjangoDebugExtension.on_execute` and `DjangoDebugExtension.get_results` run per
operation; the two teardowns each call `_stash_payload_if_executed`, which calls
`_build_payload` (SQL drain + serialize over every new log entry, exception
traceback formatting over every error) and `_apply_payload_caps` (keeps the first
100 SQL rows / 25 exception rows). The fail-closed gate
(`DjangoDebugExtension._disclosure_permitted`: one `_ACKNOWLEDGEMENT` recall + one
`getattr(settings, "DEBUG", None)`) runs once per operation even when the payload is
withheld. Nothing in the module runs per resolver or per data row; per-row work is
over diagnostic rows (queries, errors) only.

Read whole beyond the target: `extensions/operation_state.py` (the `_operation_state`
read each hook pays: carrier recall + ContextVar get + lease/weakref dereference),
`utils/private_state.py` (`PrivateAuthority.recall`: one dict get + one weakref
call), `extensions/__init__.py` (documents the eager re-export that loads this
module at package import), the package `__init__.py` head (confirms no root import
of the debug name), `review_inspect.py` overview (0 per-row leads; import-time work:
the coordinator + authority constructions), the Django 6.1 `BaseDatabaseWrapper`
`queries_log` (`deque(maxlen=...)`, O(1)-ish tail indexing, O(n) full copy) and
`force_debug_cursor` lines, `tests/extensions/test_debug.py` structure plus the
collector / hop-policy / slicing / caps tests, the live-tier
`test_debug_extension_api.py` node list, and the plan item (no Routed lead; sibling
axis records do not exist yet).

Measurements, all at address `review/extensions/debug.py/performance`, cell default,
package digest `sha256:c071c3db...9e75`:

- `review-20260929T170137-e17ee0`: `python probe_log_slice.py log_slice.json`
  (timeit medians, 9 repeats): 9000-deep deque drain, current `list()` + slice vs
  indexed tail — none-new 60.24 us vs 0.14 us, ten-new 52.39 us vs 0.41 us,
  all-new 79.00 us vs 584.09 us (full indexed drain walks deque blocks: 7x
  slower — the fix must be *bounded* indexed, not a wholesale switch), short-10
  log 0.25 us vs 0.57 us. Shipped-helper equality + clamp/rollover/empty parity
  asserted in the probe.
- `review-20260929T170615-f211de`: `python probe_serialize_bounds.py
  serialize_bounds.json` (first attempt `review-20260929T170308-9b12b4` gave the
  same counts at 0.932 ms / 8.363 ms before a probe bug in the F7 section;
  shared-machine spread — the counts are the deterministic pins): 2000-entry log
  reaches `_serialize_sql_row` 2000 times for 100 admitted rows, build median
  0.710 ms; 100 errors with real tracebacks reach `_serialize_exception` 100
  times for 25 admitted rows, collect median 5.403 ms; clean-operation build
  0.51 us, ten-query build 8.89 us; coordinator acquire/release pair 0.611 us.
- `review-20260929T170616-9d61fc`: `python probe_isselect.py isselect.json`
  (parity 25/25 over a unicode/whitespace corpus): `lower().strip().startswith`
  vs a zero-alloc scan — short select 78 ns vs 111 ns, padded select 111 ns vs
  645 ns, 2KB select 634 ns vs 122 ns. The scan loses everywhere typical: filed
  as rejection R2.
- `review-20260929T171410-95654d` (plus `review-20260929T171357-d5823c`, both
  `1 passed`): `pytest` over the scratch probe copied to the copy's
  `tests/extensions/` (source
  `docs/review/temp-tests/extensions-debug/performance/test_perf_stash_probe.py`,
  node `test_sync_operation_builds_the_payload_twice`) — one sync op builds the
  payload twice (execute stash, overwritten unread by the operation rebuild):
  R1 evidence.
- `review-20260929T171419-d5932f`: `python scripts/importtime_report.py --rounds
  5 --json importtime.json`: `extensions.debug` self 1057 us, cumulative 2418
  us, of ~300 ms package cumulative (0.35%).

Cells: default only. Sharded and pg `inapplicable by construction`: no finding
branches on an alias, a dialect, or backend behavior — the bracket loop treats
every configured connection uniformly (alias and vendor are read as row labels
only), the probes assert serializer counts and timings over real/fake deques,
and the one executing probe runs a queryless op whose stash count cannot vary by
backend. (Sharded adds a second bracketed connection; the F1 bound applies to the
whole build, so the second drain only runs while budget remains.)

No bench figure moves: the plan-cache, optimizer-walk and nested-fetch benches
never install this extension, and the findings add no import. Both findings pin
their claims with serializer-count tests instead.

Fingerprints (`git hash-object`): `extensions/debug.py`
054e04df5915ed12c49ef63e4710feebca7388aa; `extensions/operation_state.py`
d9ed9cc67fea892afa2dd22a33236a52fc061fb1; `utils/private_state.py`
b3c45503c3e2f648640b95ecad4d71a8315abb51; `extensions/__init__.py`
dc3ebdc24b4817a64ea360d92bbbed340ad30bcc; `__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a; `tests/extensions/test_debug.py`
93843bd3deae18c0dce234990ce14d3594a85000;
`examples/fakeshop/test_query/test_debug_extension_api.py`
8417985a690906b8b49d4a002cc9515322c5a57e.

## Findings

### High

None.

### Medium

#### F1: the SQL drain copies the whole log and serializes every new entry, then drops all but 100

- **Observation** — `django_strawberry_framework/extensions/debug.py::_build_payload`
  drains each connection through
  `django_strawberry_framework/extensions/debug.py::_query_log_entries_since`,
  which runs `list()` over the whole bounded deque (up to 9000 entries on a
  long-lived connection: non-HTTP in-process execution never resets the log),
  serializes every new entry, and only then lets
  `django_strawberry_framework/extensions/debug.py::_apply_payload_caps` keep
  the earliest 100. Two unbounded costs ahead of a bounded cap, paid twice per
  operation (both teardowns stash).
- **Evidence** — `review-20260929T170137-e17ee0`: a 9000-deep log costs 60.24 us
  per drain with zero new entries (52.39 us with ten); a bounded indexed tail
  costs 0.14–0.41 us on the same shapes. `review-20260929T170615-f211de`: a
  2000-entry log reaches `_serialize_sql_row` 2000 times for 100 admitted rows
  (build median 0.710 ms). The full-indexed alternative is 7x *slower* than
  `list()` on an all-new deep log (deque indexing walks blocks), so the fix is a
  bounded indexed drain, not a wholesale shape switch.
- **Impact** — Path class hot: the teardowns run per operation on every schema
  with the extension installed, and the drain scales with the operation's query
  count plus stale log depth. Over-cap operations pay ~N serializations for 100
  admitted rows; every operation on a deep stale log pays the full copy even
  with zero new queries.
- **Severity** — Medium: measured cost on a hot path, no N+1 (the extension
  issues no queries; it reads the in-memory log).
- **Recommendation** — at the owner: bound the drain at the row cap.
  `_query_log_entries_since` takes the remaining budget and returns at most that
  many entries via indexed tail access over the clamped window
  (`range(min(start, n), min(start + budget, n))`, ~40 ns per tail get measured);
  `_build_payload` threads `remaining = _MAX_SQL_ROWS - len(sql_rows)` across
  the per-connection loop and stops draining once exhausted. An islice-limited
  drain also passes the Proof but keeps the O(stale) walk; indexed is the
  recommendation.
- **Must not change** — the published payload is identical for every log shape:
  the earliest 100 concatenated rows in log order across connections; the
  clamp/rollover best-effort semantics (`test_query_log_slicing_suffix_clamp_and_rollover`
  in `tests/extensions/test_debug.py` still passes unmodified); per-row degrade
  still drops only the offending row within the admitted set. Known delta: the
  refusal log line for a hostile row beyond the cap vanishes (that row never
  reached a payload); a concurrent-mutation `IndexError` inside the drain —
  unreachable in practice (no await in the drain; other threads hold other
  wrappers) — degrades exactly like today's drain failure, to the rows so far.
- **Proof** — at `review/extensions/debug.py/verify-performance-<n>`:
  `uv run python scripts/workspace.py run review/extensions/debug.py/verify-performance-<n> -- pytest tests/extensions/test_debug.py -k test_build_payload_serializes_at_most_100_new_log_entries --no-cov -n0`
  reports `1 passed`. The test is new (planned name in plain text; Worker-2
  keeps it or reports the landed name): it builds real-deque logs at N in {50,
  101, 2000} (independent literals, never the production constant), counts
  `_serialize_sql_row` calls via monkeypatch (== min(N, 100)), asserts the
  admitted payload equals the earliest 100 in log order, and asserts bounded
  touches via a pull-counting deque double (items pulled past the snapshot ≤
  100, indexed gets ≤ 100; the shipped code pulls all N).
- **Freshness** — `extensions/debug.py` 054e04df; `tests/extensions/test_debug.py`
  93843bd3.
- **Path class** — hot: per operation when installed (both teardowns drain).
- **Instrument / before / after / delta** — instrument: `probe_log_slice.py` +
  `probe_serialize_bounds.py` timeit medians plus counting wrappers. Before:
  60.24 us deep drain at zero new entries; 2000 serializer calls / 0.710 ms
  build at N=2000. After (expected, verifier measures): sub-microsecond bounded
  drain; 100 calls. Delta: −(N−100) serializations and −(stale) copy per build.

#### F2: exception collection formats every traceback, then keeps 25

- **Observation** — `django_strawberry_framework/extensions/debug.py::_collect_exceptions`
  serializes every error carrying an `original_error`, and serialization means
  `traceback.format_exception` — the single most expensive call in the module —
  before `_apply_payload_caps` keeps the earliest 25. An error storm (one broken
  resolver times a wide query) formats 4x+ the tracebacks the payload can carry,
  twice per operation.
- **Evidence** — `review-20260929T170615-f211de`: 100 errors with real
  2–3-frame tracebacks reach `_serialize_exception` 100 times for 25 admitted
  rows (collect median 5.403 ms; 8.363 ms on the first run — shared-machine
  spread, the count is the pin). Cost per format scales with stack depth.
- **Impact** — Path class hot: same teardowns as F1. The waste is bounded only
  by the error count, which unlike the query log has no deque ceiling.
- **Severity** — Medium: measured milliseconds on a hot path without N+1.
- **Recommendation** — at the owner: filter-then-cap before serializing. Walk
  `result.errors` once collecting the `original_error`-bearing errors (cheap
  attribute reads, order preserved), take the first `_MAX_EXCEPTION_ROWS`,
  serialize only those.
- **Must not change** — admitted rows identical: earliest 25 in result-error
  order, no dedup, terminal explicitly-raised `GraphQLError` retained (the
  `test_exception_collector_guards_filter_order_and_no_dedup` rows still pass
  unmodified); a failure *within* the admitted set still degrades the whole list
  to `[]`. Known improvement, pinned by the Proof: a hostile or unserializable
  error beyond position 25 no longer discards the admitted 25 — strictly more
  diagnosis, never less; nothing that published before publishes differently.
- **Proof** — at `review/extensions/debug.py/verify-performance-<n>`:
  `uv run python scripts/workspace.py run review/extensions/debug.py/verify-performance-<n> -- pytest tests/extensions/test_debug.py -k test_collect_exceptions_serializes_only_the_first_25_errors --no-cov -n0`
  reports `1 passed`. The test is new (planned name in plain text; Worker-2
  keeps it or reports the landed name): it builds E-error results at E in {10,
  26, 100} (independent literals), counts `_serialize_exception` calls via
  monkeypatch (== min(E, 25)), asserts the admitted rows are the earliest 25 in
  order, and asserts a hostile `str()` at position 100 leaves the admitted 25
  published.
- **Freshness** — `extensions/debug.py` 054e04df; `tests/extensions/test_debug.py`
  93843bd3.
- **Path class** — hot: per operation when installed (both teardowns collect).
- **Instrument / before / after / delta** — instrument: counting wrapper +
  timeit median in `probe_serialize_bounds.py`. Before: 100 formats / 5.403 ms
  collect at E=100. After (expected, verifier measures): 25 formats,
  ~1/4 the time. Delta: −(E−25) traceback formats per build.

### Low

None.

## Rejected

- **R1: the double payload build** (`on_execute` stash overwritten unread by the
  `on_operation` rebuild on non-streaming paths). Count pinned at 2 per sync op
  (`review-20260929T171410-95654d`, `1 passed`); the discarded build costs
  0.51–0.67 us clean, 8.89 us at ten queries (`review-20260929T170615-f211de`).
  Rejected: the execute stash is the only shape the streaming seam can read, no
  cheap signal distinguishes streaming from non-streaming inside the hook, and a
  skip-if-unchanged check would add shadow-equality over every mutation channel
  (log lengths plus per-error `original_error` identities — the listed-before-
  masking contract depends on the rebuild seeing the strip) to a
  security-adjacent stash, to save microseconds on typical ops. F1/F2 shrink
  both builds. Reopens if typical build medians exceed 100 us or upstream
  exposes a streaming signal making the execute stash conditional.
- **R2: a zero-alloc `isSelect` scan** (`sql.lower().strip().startswith` copies
  the statement twice per row). Rejected on measurement
  (`review-20260929T170616-9d61fc`, 25/25 parity over a unicode/whitespace
  corpus): the C-level shape costs ~78 ns on typical short statements while the
  Python char loop costs 111 ns — 645 ns with 24 spaces of padding — because
  per-character Python loses to C memcpys; the scan wins only past ~1KB (634 ns
  vs 122 ns at 2KB), where even the loss is sub-microsecond per row. Reopens if
  a profiled operation shows `isSelect` above 1% of a payload build, or with a
  C-level bounded-prefix spelling.
- **R3: the coordinator lock on the per-request path** (one acquire/release pair
  per connection per operation). Rejected: the pair costs 0.611 us
  (`review-20260929T170615-f211de`), uncontended, and the lock covers the
  dict-plus-flag transition the overlap-safe restore guarantee needs; there is
  no cheaper shape that keeps it. Reopens on measured contention above noise.
- **R4: the per-operation settings read** (`getattr(settings, "DEBUG", None)`
  once per operation in `_disclosure_permitted`). Rejected: a single ~0.1 us
  read, and the instance is per-operation so caching would buy exactly nothing;
  the documented test/management flip-between-operations forbids wider caching.
  Reopens only if the gate ever runs per row or per field.
- **R5: the fail-closed warning on every withheld operation.** Rejected: the
  per-operation log call is the deliberate misconfiguration signal, and the
  supported fix is deployment-side (remove the extension); sampling or
  once-per-process logging would weaken the alert that justifies the gate.
  Reopens only with a supported production use of the extension, which
  contradicts the fail-closed design.
- **R6: `traceback.format_exception` itself.** Rejected: the full stack is the
  diagnostic, and the explicit-arguments form is load-bearing (ambient exc state
  is gone by teardown). Bounded at 25 rows by F2; no further trigger.
- **R7: import-time cost** (`extensions.debug` self 1057 us of ~300 ms package
  cumulative, 0.35%; `review-20260929T171419-d5932f`). Rejected: cold
  (once per process), no settings read at import, nothing beyond the package's
  own already-loaded subtree. The module loads transitively at package import
  via the `extensions/__init__.py` eager re-export, which that docstring
  documents as the intended shape; making it lazy to save 1 ms is not worth the
  machinery. Reopens if module self-time exceeds 5% of package import.
- **R8: truncating SQL text inside the serializer.** Payload-identical
  (truncate-then-truncate is idempotent, marker included) but time-neutral —
  one bounded copy either way — saving only transient memory for giant
  statements. Rejected as speculative-rare. Reopens on a profiled multi-MB
  transient from one operation's statements.
- **R9: the `{**row, ...}` dict spreads in `_apply_payload_caps`** (≤125
  six-key rebuilds, ~10 us). Rejected: bounded, plain, and the spread keeps the
  admitted lists unaliased from the assembled ones. Reopens if a cap rises above
  1000 rows.
- **R10: the identity-set allocation per error in `_terminal_original_error`**
  (~100 ns; lazily creating it after the first non-`GraphQLError` return was
  considered). Rejected: the set and the 64-hop ceiling are both load-bearing
  (cycles vs long chains), and the saving is unmeasurable. No trigger.
- **R11: `_operation_state()` per hook plus the acknowledgement recall**
  (three state reads + one authority recall per operation: dict gets, weakref
  calls, ContextVar reads — sub-microsecond each). Rejected: inherent,
  architecture-owned by `operation_state.py` / `private_state.py`, with no
  per-row repetition. Nothing to route — no defect identified. Reopens only on
  a new per-row call site.

Looks-for discharged, `none`: N+1 / per-row queries (the module issues zero
queries — it reads the in-memory log); `len(qs)` / `bool(qs)`; `only()` /
`defer()`; unbatched writes; `blog.id` vs `blog_id` (no ORM use — `rg` over the
module for `_meta`, `.filter(`, `bulk_`, `only(`, `defer(`, `.count()`,
`.exists()` finds nothing); repeated `_meta` walks, regex compilation, schema or
type lookups (none in the module — no `re`, no registry/schema access);
`lru_cache` on methods / B019 (no cache in the module); cache reads, re-parses,
extra round trips on a per-request path (none — only the R3 lock, the intended
overlap guard); repeated settings reads (exactly one per operation — R4);
`str()` / `float()` coercions per row (no-ops returning the same object when
types already match); `ExitStack`, per-connection dataclasses, `connections.all()`
and state construction per operation (sub-microsecond, inherent); allocation in
the walk (no walker here; per-operation allocs are F1/F2 plus the bounded R9
spreads).

## Cross-axis

None. F2's hostile-beyond-cap improvement is documented inside that finding
rather than routed: it changes no published row, only which failures can still
suppress the admitted set, and its proof (the count pin) is this axis's.

Handoff: Read beyond the trace: the `__init__.py` acknowledgement gate and its
concurrent `truth.describe` dirt (cold, reviewed as read), the
`_stash_payload_if_executed` / `get_results` idempotence chain, the masking-order
docstring (why R1's rebuild cannot be skipped by result identity alone — the
strip mutates `original_error` in place between the two builds), Django's own
`CaptureQueriesContext` (does the same full-log copy, so F1 deliberately deviates
from the mirrored shape for a measured 400x on stale logs), and the run-1
`rev-utils__strings.performance.md` for record conventions. Conclusions the
findings do not state: the module is unusually well-bounded already (every cap
exists; the waste is work done *ahead* of the caps, not missing caps), the
double stash is the only structural 2x and it is correctly rejected, and the
verifier should weigh F1's refusal-log-line delta (beyond-cap hostile rows go
quiet) as the one judgment call in the package. Open threads: none for this
axis; sibling Mechanics/Comments records did not exist at close, so nothing was
coordinated with them. Probes and JSON under
`docs/review/temp-tests/extensions-debug/performance/` (`probe_log_slice.py`,
`probe_serialize_bounds.py`, `probe_isselect.py`,
`test_perf_stash_probe.py` + `log_slice.json`, `serialize_bounds.json`,
`isselect.json`, `importtime.json`, `debug.json`, `inspect/`).

## Verification (Performance)

Verdict: F1 pass, F2 pass. Both landed as recommended; both Proofs report
`1 passed` verbatim at `review/extensions/debug.py/verify-performance-1`;
counts re-measured before/after move the recorded direction; every production
hunk fails exactly its pin node on revert (restored, byte-checked); compat
nodes pass unmodified. One routed gap (case C below): a hostile-within-window
over-cap shape where the admitted tail is no longer backfilled — a
Mechanics-flavored observable-behavior question, not a Performance defect, so
the record verifies and Worker-0 routes it.

Step 1 — change confirmation and Proofs. No `<root>/diff/pass-1.diff` exists
under `docs/review/temp-tests/extensions-debug/`, so the hash check ran
against the dispatched inventory instead: `git diff ITEM_BASELINE --` over the
target + `tests/extensions/test_debug.py` (sha256
`7fd36d297235e7f15a3f1060e5d0e1b973617e67d027ea7bf54360e35b13b652`,
117 + 150 lines) holds exactly the Implementation inventory — the F1 helper
+ loop hunks, the F2 collector hunk, the Mechanics gate + comment, the C1
3-site reword, the Comments prose, 3 new tests, zero test-body edits (all 6
removed test lines are docstring prose). Live blobs `da22bf47` (target) and
`445e4ac3` (tests). Ordering note: the dispatch itself described the
implementation, so strict expectation-first was unavailable; both Proof lines
still ran verbatim and unmodified. `review-20260929T175943-bf2d8c`: F1 Proof
(`-k test_build_payload_serializes_at_most_100_new_log_entries`) `1 passed`
(copy slot-3 fresh, package digest `sha256:d0ab2d72...`).
`review-20260929T175959-43aa7b`: F2 Proof
(`-k test_collect_exceptions_serializes_only_the_first_25_errors`) `1 passed`.
No other record holds a `## Cross-axis (for Performance)` Proof (Mechanics
routes to Comments only; Comments has no cross-axis section). The Proof runs
also corroborate Worker-2's `75 passed` module count (`collected 75 items`).

Step 2 — numbers reproduced. Before, at the read-only `before` address
(package digest `sha256:c071c3db...`, the review's digest; never `--fresh`,
never edited), with the record's instruments verbatim:
`review-20260929T180242-c64a81` (`probe_log_slice.py`): deep drain 29.24 us
none-new / 29.27 us ten-new / 50.50 us all-new, full-indexed 385.63 us
all-new — same shape as the record (60.24 / 52.39 / 79.00 / 584.09 us),
spread is shared-machine noise. `review-20260929T180250-083aeb`
(`probe_serialize_bounds.py`): 2000 entries -> 2000 calls / 100 admitted /
0.650 ms build; 100 errors -> 100 formats / 25 admitted / 5.053 ms collect —
counts exact, timings within spread of 0.710 / 5.403 ms. After, with adapted
instruments under `verify-performance-1/` (the record's probes assert the
before shape and fail on the fixed tree by design):
`review-20260929T180532-9506f7`: shipped bounded drain 0.14 us none-new /
0.33 us ten-new / 1.67 us all-new vs full-copy 30.14 / 30.06 / 50.87 us, plus
`[:100]` parity on every case, default budget `== 100`, explicit 7 / 0 /
negative budgets, and a mid-log window. `review-20260929T180546-08f7e5`:
2000 entries -> 100 calls / 100 admitted / 0.075 ms build; 100 errors -> 25
formats / 25 admitted / 1.290 ms collect; clean build 0.48 us (was 0.44),
ten-query 7.86 us (was 7.68), bracket pair 0.539 us (was 0.616) — bounded
shapes move ~8x / ~4x, typical shapes unmoved. Compat nodes
`review-20260929T180236-262774`: slicing + collector-guards `2 passed`,
both bodies byte-identical to ITEM_BASELINE.

Whole-diff reading (Performance). The F1/F2 hunks match the recommendations
exactly (budget default `_MAX_SQL_ROWS`, `remaining` threaded across the
bracket loop with `break`, filter-then-cap preserving order). The Mechanics
gate hunk is perf-neutral: same per-operation cost class (one settings
attribute read; the acknowledgement short-circuit is preserved, `try` setup
is noise). The C1/Comments hunks are prose. The `IndexError` path reads
true: the drain call sits inside `_build_payload`'s `try`, so a concurrent
mutation degrades to the rows so far exactly like today's drain failure.
No other caller of either helper exists outside the target + its test
module (grep over package, tests, examples: empty).

Attacks. (1) Other cardinality — multi-connection over-cap scratch node
`test_build_payload_bounds_serializations_across_connections` (3 x 60
entries; copy-only, `review-20260929T180628-3afb76` `1 passed`): exactly 100
serializations, earliest-100 concatenated in order. Passing, owes nothing.
(2) Comparison probe `probe_payload_compare.py`, identical script at both
addresses (`review-20260929T180556-38604a` before,
`review-20260929T180606-5186e0` after): case A (single 2000) 2000 -> 100
calls, admitted identical 0..99; case B (3 x 60) 180 -> 100 calls, admitted
identical 60+40+0 with order preserved; case E (empty x 2) identical 0/0;
case F (100 errors) 100 -> 25 formats, admitted identical boom 0..24; case
D (hostile at index 150) admitted identical, refusals 1 -> 0 — the Known
delta, confirmed as predicted. (3) Case C (NaN-duration hostile at index 5
of 2000): admitted 100 -> 99, tail `...98,99,100` -> `...97,98,99`,
refusals 1 -> 1 — before backfills the admitted tail from beyond the cap,
after stops at the window. This is the one shape where Must-not-change
("identical for every log shape") does not hold; see the routed gap below.

Disputes: none recorded in `## Implementation (Worker-2)`; nothing to judge.

Benches. `grep` over `bench_plan_cache.py`, `bench_optimizer_walk.py`,
`bench_nested_fetch.py`, `_bench_common.py`, `count_queries.py`,
`importtime_report.py` for the extension: empty — the benches never install
it. The perf hunks add no import (the diff's one new import,
`ImproperlyConfigured`, is the Mechanics gate's, django-core, cold).
Import-time re-measured both sides with identical instrument ids
(`review-20260929T180641-8bb015` / `review-20260929T180644-767b69`):
`extensions.debug` self 931 -> 937 us, cumulative 2172 -> 2164 us; package
209.6 -> 207.0 ms over 69 modules both sides — noise. R7 stands; no bench
figure moves.

Cells (judged, not cited). Sharded and pg are inapplicable by construction:
the hunks touch no alias or dialect decision — `queries_log` is a plain
deque attribute on every backend wrapper, `alias`/`vendor` are read as row
labels only, the budget threading is alias-agnostic, and
`_collect_exceptions` reads graphql-core `result.errors` with no database
involved. Sharded's only effect is a second bracketed connection, i.e. a
second snapshot in the same loop — exactly the shape case B runs in the
default cell (distinct aliases, 60+40+0 admitted identically). The module
issues no SQL, so no backend varies the result; the pin/compat/attack nodes
all run on fake/real deques in the default cell.

Failability (`review-20260929T180739-6f40e2`, exit 0, manifest
`verify-performance-1/prove_perf.json`, anchor+replacement per hunk since
all three axes share the file): (1) helper revert -> exactly the F1 pin
fails (baseline `2 passed`, mutant `1 failed, 1 passed`; slicing compat
unaffected); (2) loop-threading revert -> exactly the scratch multi-conn
node fails (`1 passed` -> `1 failed`); (3) collector revert -> exactly the
F2 pin fails (`assert 26 == 25`; collector compat unaffected). Every
restore byte-proved (`filecmp` True, sha256 match); the copy's target blob
is `da22bf47`, equal to live.

Routed gap (for Worker-0; suggested route: this item's Mechanics verifier,
which re-reads the whole diff for observable-behavior preservation): F1's
within-connection budget counts drained entries, not admitted rows, so an
over-cap drain whose first-100 window contains a dropped (hostile or
unserializable) row publishes fewer backfilled tail rows than before (case
C: 99 rows ending `SELECT 99` vs 100 ending `SELECT 100`). Confined to
hostile shapes — stock Django never emits an unserializable entry — and
strict identity there is jointly unsatisfiable with boundedness (draining
until 100 admitted reintroduces unbounded serialization on hostile-heavy
logs, defeating F1), so this is not revision-needed: no code change is
prescribed. Suggested disposition: confirm-and-record (an amendment to the
Must-not-change sentence or a `## Decisions` line), not a re-pass.

Handoff: read beyond the record's trace: the full Implementation section,
both sibling axis records whole (Mechanics F1/C1/R1-R8, Comments F1-F17 +
R1-R8 — no Performance content disputed or duplicated), the plan item
(`implementing`, converged F1/C1 text noted) and run-3 scope/drift lines,
REVIEW.md + both role files + AGENTS.md + START.md whole, and the whole
live target (888 lines). Conclusions the checks do not state: the change
is exactly the recommended shape on both findings; the only judgment call
is the case-C backfill nuance, which the record's Known delta does not
cover but which cannot be fixed without unbounding the drain; F2 is
strictly identical-or-better (whole-list degrade has no backfill). Open
threads: the routed gap above; nothing else. Scratch kept under
`docs/review/temp-tests/extensions-debug/verify-performance-1/` (3 probes
+ 1 scratch test + 1 manifest + 8 JSONs); the scratch test also lives in
the verify copy's `tests/extensions/` (copy-only). Fingerprints:
`da22bf47` target, `445e4ac3` tests, item-diff sha256 `7fd36d29...b13b652`.
