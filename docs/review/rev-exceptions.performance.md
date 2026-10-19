# Review · Performance: `django_strawberry_framework/exceptions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=c78eb5f150bcd2a5f448a135e078ef58a5594cf4

Path class: cold — every executable line beyond class definition runs only
while constructing an exception that aborts declaration, finalization,
generation, or an already-failing request. The one per-request-reachable
constructor (`PathResolutionError` via apply-time order validation) fires only
on invalid input that returns an error. Nothing runs per request, resolver,
row, connection, or outbound message on any success path.

## Trace

Read the whole live target (232 lines) plus every production raise and catch
site the Performance axis needs: `classify_path` and `validate_lookup_expr`
in `django_strawberry_framework/utils/relations.py` (the only constructors of
the two typed errors), all four `classify_path` production callers
(`filters/sets.py::_candidate_metadata_for`,
`orders/sets.py::OrderSet._expand_meta_fields`,
`orders/sets.py::OrderSet._resolve_order_expressions`,
`utils/relations.py::path_traverses_to_many` via its cached wrapper), every
`OptimizerError` raise site (`types/resolvers.py::_check_n1`,
`optimizer/field_meta.py::FieldMeta.from_django_field`,
`optimizer/plans.py::window_partition_for_prefetch`,
`optimizer/predicates.py::attach_exists`,
`utils/connections.py::window_range_plan` and
`::assert_window_fetch_mode`, plus the two further `plans.py` guards), the
`truth` helpers the message builders call, and `tests/test_exceptions.py`
(construction census). `review_inspect.py` orientation only (0 per-row leads,
0 hot entry points, 0 import-time work, 2 `getattr` calls of interest, both
on raise paths). Sibling axis records did not exist when this pass ran
(concurrent dispatches).

The target is dirty vs HEAD (the `truth` message-builder migration) but
identical to ITEM_BASELINE (`git diff <ITEM_BASELINE> -- <target>` empty),
so the fingerprints below are what was reviewed. The plan's `## Owned
changes` holds no row for this target (only closed items' rows).

Measurements, both in copy `review/exceptions.py/performance` (slot-2),
package digest `sha256:c8c86495...fdcfe3a5af2` on both runs (the two figures
compare with each other; the digest is not the `## Bench baseline` digest, so
no figure is claimed against the baseline table), instruments
`scripts/_bench_common.py` blob `253a3953`, `scripts/importtime_report.py`
blob `15f679c9`, probe blob `e0a05a40`:

- `review-20260929T042150-92733b`: `python <root>/performance/probe_raise_costs.py
  <root>/performance/raise_costs.json` (probe by absolute path, copy unedited;
  Django 6.1 via `sqlite-memory` bootstrap, real `ContentType` model + real
  `app_label` field for the model/terminal branches). `parity: ok`. Timeit
  medians over 20000 repeats x 7 batches: `ConfigurationError(...)` 37.6 ns,
  `OptimizerError(...)` 38.2 ns, `PathResolutionError(model, ...)` 5291.8 ns,
  `PathResolutionError(object(), ...)` 4912.5 ns,
  `LookupValidationError(field, ...)` 4635.2 ns,
  `LookupValidationError(object(), ...)` 4449.9 ns, `str()` of either 14.5 ns,
  the function-local `from .utils import truth` 158.4 ns.
- `review-20260929T042203-6cb71c`: `python scripts/importtime_report.py
  --rounds 5 --json <root>/performance/importtime.json`: `exceptions` self
  117 us, cumulative 117 us (dependency-free: cumulative equals self);
  `utils.truth` self 189 us; `utils` package self 74 us, cumulative 1295 us;
  package cumulative 202484 us over 69 modules. The target is 0.06% of
  package import.

No bench figure moves: the plan-cache, optimizer-walk, and nested-fetch
benches never construct these exceptions on their success paths, and the one
per-request raise (`OptimizerError` under strictness `"raise"`) aborts the
request it fires on.

Cells: default, sharded, and pg are all inapplicable by construction — the
target reaches no database, alias, or dialect decision (no ORM, no
connections, no raw SQL, no `using`). The probe's `sqlite-memory` bootstrap
opened an in-memory database only to configure Django for fixtures; the
target itself issues no queries, so `count_queries.py` would exit 2 with
nothing comparable measured. No `--cell` run.

Fingerprints (`git hash-object` of every file read):

- `django_strawberry_framework/exceptions.py` 206e9f8d914f640134cf72e374fadeac41d13a39
- `django_strawberry_framework/utils/relations.py` 05ff55b098382a4a7aafe5a097c3b5e906f8f985
- `django_strawberry_framework/utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9
- `django_strawberry_framework/orders/sets.py` 60859f2d54525acfdb3dc997d3e931ff3d58d956
- `django_strawberry_framework/filters/sets.py` e47c6758e540e0bd9caa8cb90103263b26e905e1
- `django_strawberry_framework/types/resolvers.py` 640905c63f465db4de16c3a07492b27f3d12d3ad
- `django_strawberry_framework/utils/connections.py` efcf749a26dc7d3fa9b3cc142789a11de2647070
- `django_strawberry_framework/optimizer/plans.py` 33140a766cd3fb2484a40fe499d466c8ced8b4a6
- `django_strawberry_framework/optimizer/predicates.py` 4673e81bc65013f5391682fb482bbb07f9c89345
- `django_strawberry_framework/optimizer/field_meta.py` bcddf517b0145be6c06c717d5379e29c271cfea5
- `tests/test_exceptions.py` 4b5818c22d24865a38a44e73782b49ee3dc9f94d
- `scripts/_bench_common.py` 253a39533f35b94f6afb7a1167c2c38489bbbbef
- `scripts/importtime_report.py` 15f679c9ad736b71215d8ead0733116f56083cef

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry below is `none` with the reason, measured where a number backs
it (probe run `review-20260929T042150-92733b`, import run
`review-20260929T042203-6cb71c`, same package digest):

- N+1 / per-row queries (`await` per row, `.filter()` on a prefetch): none.
  No ORM access anywhere in the file; no loop over rows; the only loops in
  reach run while an exception message is being built on a raising path.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()` (either direction):
  none. No querysets.
- `only()` / `defer()` deferred loads: none. No querysets.
- Unbatched writes (`bulk_create` / `bulk_update`): none. No writes.
- `blog.id` vs `blog_id`: none. The one model-attribute read
  (`getattr(meta, "label", None)` in `_model_label`) touches an already
  fetched `_meta`, costs nothing observable, and runs only on the
  `PathResolutionError` raise path.
- Repeated `_meta` walks: none in the target. The `_meta` walks that reach
  these exceptions live in `utils/relations.py::classify_path` (another
  item); the target's `_model_label` reads one attribute off the passed
  model. The one repeated-raise shape (the `path_traverses_to_many` lenient
  ladder catching `PathResolutionError`) is already bounded to a single
  construction per distinct `(model, field_path)` pair: the catch sits
  inside `_traverses_to_many`, whose result the `lru_cache`-wrapped
  `_path_traverses_to_many_cached` memoizes.
- Repeated settings reads: none. No settings access.
- Repeated regex compilation: none. No regex.
- Repeated schema / type lookups per request: none. No schema or type
  lookups.
- `lru_cache` on methods (`B019`): none. The module holds no cache.
- Locks, cache reads, re-parses, extra round trips on a per-request path:
  none — there is no per-request success path. The per-request-reachable
  raises are `OptimizerError` under strictness `"raise"`
  (`types/resolvers.py::_check_n1`, bare `Exception.__init__`, ~38 ns, and
  the request aborts) and `PathResolutionError` on invalid order input
  (`orders/sets.py::OrderSet._resolve_order_expressions`, ~5.3 us, and the
  request returns an error). The `window_partition_for_prefetch`
  raise-to-fallback contract has no production caller and no
  `except OptimizerError` exists in the package, so no raise-and-catch loop
  runs anywhere in production.
- Import-time cost: none, measured. Self 117 us with cumulative equal to
  self (no module-scope imports beyond `__future__`: no Django, no
  Strawberry, no package imports); 0.06% of package import. The four
  function-local `from .utils import truth` imports cost 158 ns each once
  `utils` is in `sys.modules` (every production raise site already imports
  far more), and the worst-case first-hit cold import is bounded by the
  `utils` + `truth` rows (~1.5 ms, once per process, on an error path).
- Allocation in the walk: none. The walker never touches the module; the
  typed constructors build two f-strings plus two `truth.render` calls on
  their raising path only (~5 us, measured), and `str()` / `repr()` render
  is standard `Exception` behaviour at 14.5 ns (the truth migration removed
  the old `__str__` / `__repr__` guards rather than adding render cost).

## Rejected

- **R1: hoist `from .utils import truth` to module scope (saves ~158 ns x2
  per typed construction, ~6% of the ~5 us).** Rejected: the hoist is a
  circular import — executing the `utils` package `__init__` at
  `exceptions` module scope runs `utils` modules that import `exceptions`
  (`utils/relations.py` imports it at module scope). Correctness-load-bearing
  placement on a raise-only path. Reopens if the cycle is broken (e.g.
  `truth` moves out of the `utils` package) and raise-path microseconds are
  measured to matter.
- **R2: memoize `_model_label` / `_terminal_label` per model/field (saves
  the `truth.static_attr` namespace walk per raise).** Rejected: runs only
  while building an exception that aborts the request, declaration, or
  generation; the one repeated-raise shape is already memoized one level up
  (`_path_traverses_to_many_cached`); a cache here would pin consumer model
  classes process-wide (registry-clear lifecycle questions) to save
  microseconds on an error path. Plainness wins by rule on a cold path.
  Reopens if a per-request raise-and-catch loop over the same model appears
  outside the cached wrapper.
- **R3: build the typed messages lazily in `__str__` so raise-and-swallow
  sites (the filters fail-closed arm, the lenient ladder) skip the ~5 us
  format.** Rejected: both catch sites either re-raise with the message
  interpolated (orders: `f"...{exc}"` needs the string) or fire once per
  class at generation (filters expanded leaf); lazy rendering would
  reintroduce render-at-call-time semantics the truth migration deliberately
  removed (standard `Exception` behaviour is the documented contract).
  Reopens if a hot raise-and-swallow loop is demonstrated.
- **R4: the ~5.3 us `PathResolutionError` construction on invalid order
  input per request (`orders/sets.py::OrderSet._resolve_order_expressions`).**
  Rejected as a target finding: invalid input must produce a typed error
  naming model, path, and segment, and the request returns an error — the
  cost is inherent to the contract, and the valid-input path raises nothing.
  The call-site choice (uncached `classify_path` per request per term) is a
  lead for the owning item, routed below. Reopens if invalid-input error
  responses dominate a measured profile.
- **R5: `__reduce__` tuple + `vars(self)` allocation per pickle.** Rejected:
  no production pickle path constructs these (pickle/copy coverage is
  `tests/test_exceptions.py` only); ~100 ns. Reopens if the exceptions cross
  a process boundary on a hot path.
- **R6: `LookupValidationError.__init__` cost (~4.6 us).** Rejected:
  `validate_lookup_expr` has zero production callers (tests only), so the
  constructor never runs in production. Reopens if a production caller
  lands — and then only if it raises outside an error path.

No finding carries a Proof line: zero findings means no `Proof` is owed,
and no bench figure moves. The probes stay re-runnable from the commands in
`## Trace` at `review/exceptions.py/verify-performance-<n>`.

Handoff: Read beyond the trace: the full `OptimizerError` raise-site census
above (every site builds a plain str/f-string outside the target; the class
adds no `__init__`, measured at ~38 ns), the `except OptimizerError`
absence (no production raise-and-catch loop; the
`window_partition_for_prefetch` fallback contract is historical/Test-pinned
with no production caller), and the `SyncMisuseError` multiple inheritance
(a `ConfigurationError` subclass defined in `utils/querysets.py`, zero
target cost). One Routed lead for Worker-0 (owning item `orders/sets.py`,
not a finding here): `orders/sets.py::OrderSet._resolve_order_expressions`
calls the uncached `classify_path` per request per order term, six lines
above the cached `_path_traverses_to_many` probe over the same pair — the
owning Performance pass should check whether the strict result can ride the
cached wrapper. No Cross-axis findings: nothing in this pass belongs to
Mechanics or Comments. Sibling records were absent at review time, so no
cross-axis text of theirs was read. Open threads: none on Performance.

## Verification (Performance)

Pass 1, address `review/exceptions.py/verify-performance-1`, scratch
`docs/review/temp-tests/exceptions/verify-performance-1/`.

Step 1 — item diff integrity: `git diff
c78eb5f150bcd2a5f448a135e078ef58a5594cf4 --
django_strawberry_framework/exceptions.py tests/test_exceptions.py`
sha256 `f2acd1efc5f70cb073f6a4e0806a9b1287d1814cc4408f41f5b03971d451d256`
hash-equals `docs/review/temp-tests/exceptions/diff/pass-1.diff`
(same sha256); live blobs `93401220` / `1374fef5` match Worker-2's
fingerprints. The tree did not move under the pass.

Proof lines run verbatim at this address: none exist, so none were
run. The Performance record carries zero Proof lines ("No finding
carries a Proof line"), and no `## Cross-axis (for Performance)`
section exists in any of the three axis records (the only Cross-axis
section is Mechanics' `## Cross-axis (for Comments)` C1-C3).

Numbers reproduced. Worker-2 claims for Performance: no findings
(0/0/0) and "No bench figure moves". Both reviewer instruments
re-run at this address on the post-pass tree, same copy both runs
(slot-2, fresh, synced 2026-09-29T04:39:36Z, package digest
`sha256:b164b5bc...1c3f10`, shared tree unmoved since sync):

- Probe `review-20260929T043936-7b1705` (probe blob `e0a05a40`,
  `_bench_common.py` blob `253a3953`, both identical to the review
  runs; the package digest differs from the reviewer's `c8c86495`
  because the measured tree now holds the prose change itself —
  expected, and the code-digest identity below proves the executable
  bytes identical). `parity: ok`. Review -> verify medians:
  `ConfigurationError` 37.6 -> 37.1 ns, `OptimizerError` 38.2 ->
  37.2 ns, `PathResolutionError(model)` 5291.8 -> 4992.8 ns,
  `(object())` 4912.5 -> 4436.0 ns,
  `LookupValidationError(field)` 4635.2 -> 4333.3 ns, `(object())`
  4449.9 -> 4021.9 ns, `str()` 14.5 -> 12.8/13.1 ns, local truth
  import 158.4 -> 149.3 ns. Every row moves the same direction
  (1-10% faster): cross-session machine drift, not movement — no
  executable byte changed, and a timing comparison would require
  interleaved medians anyway.
- Importtime `review-20260929T043945-e2bf0f` (instrument blobs
  `253a3953` + `15f679c9`, identical to the review run):
  `exceptions` self 113 us = cumulative (was 117),
  `utils.truth` self 173 (was 189), `utils` self 83 / cumulative
  1218 (was 74 / 1295), package cumulative 204697 us over 69
  modules (was 202484 over 69). Same module count, still
  dependency-free (cumulative equals self), still ~0.06% of
  package import; deltas are min-of-5 noise.

Diff read through Performance: all six hunks are docstring-only
(five target docstring hunks, one test docstring hunk); no import,
no raise site, no caller, no executable line touched.
`review_inspect.py --code-digest` exits 0 on both files with
Worker-2's exact digest pairs (`2c01d220...8b8d10`,
`bdbf204b...c4714c5`). No number can move; no bench figure moves;
no query-count test is owed (the target issues no queries).

Attacks on the current state, all passing (recorded, not findings):

- A1 import surface: module scope still holds only
  `from __future__ import annotations`; the four truth imports are
  still function-local. No new import-time cost is possible.
- A2 raise/catch census: 6 `raise PathResolutionError`, 6 `raise
  LookupValidationError`, 14 `raise OptimizerError`, 0 `except
  OptimizerError` package-wide — the review-time shape, unchanged;
  no raise-and-catch loop introduced.
- A3 ORM/DB surface: no executable Django / Strawberry / ORM
  reference in the live target (every match is a class name or
  docstring prose). Path class cold re-affirmed.
- A4 routed-lead owner untouched: `orders/sets.py` has no
  item-scoped hunk (blob `60859f2d`, unchanged vs all three
  records), so the uncached-`classify_path` lead is neither
  worsened nor in fence.
- A5 per-request reachability: the diff adds no code, so no new
  per-request path exists; the two per-request-reachable raises
  still fire only on error input.

Disputes: none recorded ("No finding disputed, discharged, or
deferred"). Nothing to judge.

Failability / test tier: none owed — zero Performance findings and
a prose-only diff mean no change exists to fail. No revert, no
`prove` manifest, no pytest node.

Cells unverified: none. default, sharded, and pg remain
inapplicable by construction (no database, alias, or dialect
reach; docstring-only diff).

Scratch: `docs/review/temp-tests/exceptions/verify-performance-1/`
holds `probe_raise_costs.py` (verbatim copy of the reviewer probe,
blob `e0a05a40`), `raise_costs.json`, `importtime.json`. Run ids:
`review-20260929T043936-7b1705`, `review-20260929T043945-e2bf0f`.

Fingerprints (`git hash-object`, live tree at verify time):
`django_strawberry_framework/exceptions.py`
`93401220b5e2c528a421481721f0e2ac460aa0bd`;
`tests/test_exceptions.py`
`1374fef552bcc5c34c47d921a6db2f1f9c7ae07f`;
`django_strawberry_framework/orders/sets.py`
`60859f2d54525acfdb3dc997d3e931ff3d58d956` (unchanged vs all three
records).

Handoff: Performance verify pass 1 closed `verified`. Read beyond
the record's trace: the item diff whole (six docstring hunks), the
live target's import block and raise/catch census, and Worker-2's
`## Implementation` claims for Performance (no-findings n/a, no
bench figure moves — both upheld). Conclusions not stated above:
the ~6-10% probe speedups are same-direction drift across every
row on a byte-identical executable, so they corroborate rather
than qualify the no-move verdict; the importtime row is the
stronger anchor (same module count, dependency-free shape
preserved). Open threads: none on Performance.
