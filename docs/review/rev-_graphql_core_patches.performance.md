# Review · Performance: `django_strawberry_framework/_graphql_core_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=e4385002efab0df029451349a7738a02e19928e2

## Trace

Target read whole (129 lines, blob `a188b290`). `git diff <ITEM_BASELINE> -- <target>`
is empty, so the tree reviewed is the item baseline. The target is dirty vs HEAD
by exactly the concurrent truthful-reads switch (4 insertions, 2 deletions:
`from .utils import truth`, `truth.class_dict` in
`django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method`
and `django_strawberry_framework/_graphql_core_patches.py::_patch_is_installed`),
which predates the item baseline and sits in none of this item's hunks; it touches
import/apply paths only (R5). The plan's `## Owned changes` holds no row for
this target. Sibling axis records (`rev-_graphql_core_patches.mechanics.md`,
`rev-_graphql_core_patches.comments.md`) did not exist when this pass closed.

Orientation: `review_inspect.py` overview at `<root>/performance/inspect/`
(json `<root>/performance/_graphql_core_patches.json`): 0 per-row leads,
1 hot entry point (`_patched_complete_list_value`, via the `info` parameter),
0 ORM markers, 3 import-time calls (method capture, two `setattr`).

Symbols and every production caller (search census over the package, tests and
examples):

- `django_strawberry_framework/_graphql_core_patches.py::apply` — called only from
  `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
  (per-process app load; function-local import) and from tests. Cold.
- `django_strawberry_framework/_graphql_core_patches.py::_patched_complete_list_value` —
  installed on `ExecutionContext.complete_list_value` by `apply`; invoked by the
  graphql-core executor once per list-field completion on every executed
  operation, sync and async, while installed (default-on). Hot.
- `django_strawberry_framework/_graphql_core_patches.py::_await_residual` —
  defined and awaited only inside the wrapper's async-iterable branch. Rare path.
- `django_strawberry_framework/_graphql_core_patches.py::_validate_upstream_shape` —
  once per `apply` (`inspect.signature` over 6 parameters). Cold.
- `django_strawberry_framework/_graphql_core_patches.py::_patch_is_installed` —
  once per `apply` plus tests. Cold.
- `django_strawberry_framework/_graphql_core_patches.py::_captured_upstream_method` —
  at module import plus tests. Cold.

No optimizer, resolver, connection, schema-build or request-handling module
imports or calls the target; the package `__init__` never imports it (import
sites: `apps.py::ready` only, plus tests).

`Path class: hot` — `_patched_complete_list_value` runs once per list-field
completion on every executed operation while the patch is installed, which
`ready()` does by default.

Measurements, all in copy `review/_graphql_core_patches.py/performance` (slot-2),
package digest `sha256:c5a2742119d1fc7fdaef99f295304d31bccf3912c32f9448bf8287c508fb789c`
on every run (both figures compare with each other; the digest is not the
`## Bench baseline` digest, so no figure is claimed against the baseline table;
later runs note `shared=moved 3` (concurrent work outside the measured bytes —
the digest is identical, so all figures compare):

- `review-20260928T213834-c8a48b`: `python <root>/performance/probe_predicate_order.py`
  (probe blob `3c415038`, run by absolute path, copy unedited; output
  `<root>/performance/predicate_order.json`, blob `c00bb35e`). Interleaved
  timeit, min-of-5 per round, median of 9 rounds, 10000 iters: current order
  `not is_iterable(result) and isinstance(result, AsyncIterable)` on a sync
  list 205.8 ns median (rounds 204.0-207.8); swapped order 87.5 ns median
  (rounds 85.5-89.4); delta 118.3 ns (-57%), ranges non-overlapping. Async
  result: 173.1 vs 169.6 ns, delta 3.6 ns with overlapping ranges (noise —
  both orders evaluate the same predicates there). graphql-core 3.2.8, where
  `is_iterable` is one `Iterable` ABC check plus a 5-tuple exclusion scan and
  `isinstance(x, AsyncIterable)` is a single ABC check.
- `review-20260928T214159-3d0a64`: `python scripts/importtime_report.py
  --rounds 5 --top 80 --json <root>/performance/importtime.json` (blob
  `f2aa83ed`): 69 rows, none for `_graphql_core_patches` (nor `apps` or
  `testing`) — `import django_strawberry_framework` never pulls the patch
  module, so its package-import contribution is 0. Package cumulative
  188.2 ms over 69 modules. Instruments `scripts/importtime_report.py` blob
  `15f679c9`, `scripts/_bench_common.py` blob `253a3953`.
- `review-20260928T214221-1bef80`, `review-20260928T214228-639e00`,
  `review-20260928T214234-fe508b`: `--collect-only` counts for the F1 Proof:
  `tests/test_graphql_core_patches.py` 10 nodes,
  `examples/fakeshop/test_query/test_list_field_async_api.py` 78 nodes
  (88 together).

Cells: default only. Sharded and pg are `inapplicable by construction`: the
module runs zero queries, reads no alias and makes no dialect decision — the
hot path evaluates three pure predicates over in-memory executor values;
`count_queries.py` would exit 2 with nothing comparable measured. No `--cell`
run.

Fingerprints (`git hash-object`): `django_strawberry_framework/_graphql_core_patches.py`
a188b290b24bce07198611cef7c37935f7a437d1;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`tests/test_graphql_core_patches.py`
53dca51737e6163c09549d015713ebf9dfcdec88;
`examples/fakeshop/test_query/test_list_field_async_api.py`
49e423ea593b8883c4c07593accd822390e82468 (docstring + count only);
`tests/test_apps.py`
5ca8b62c53185343ebfec95315f59ec6104fc851 (caller census only);
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef;
`scripts/_bench_common.py`
253a39533f35b94f6afb7a1167c2c38489bbbbef;
installed graphql-core 3.2.8 `pyutils/is_iterable.py`
142c3a14699a6a205882cb479b9a6a8ea3b69cc9,
`execution/execute.py`
869f59f3f5662fc55e3dbb48023e6879dab40a8a.

## Findings

### High

None.

### Medium

None.

### Low

#### F1: wrapper tests the expensive predicate first on the hot sync-list path

- Observation: `django_strawberry_framework/_graphql_core_patches.py::_patched_complete_list_value`
  guards the residual-await branch with `not is_iterable(result) and
  isinstance(result, AsyncIterable) and self.is_awaitable(res)`. On the common
  sync-list path the first conjunct short-circuits, so every list completion
  pays `is_iterable` (one call, one `Iterable` ABC check, one 5-tuple exclusion
  scan) before the single-ABC `isinstance(result, AsyncIterable)` test that
  would have short-circuited cheaper. The order mirrors upstream's branch
  nesting, but the wrapper owes upstream behavioural correspondence, not
  conjunct order — and the third conjunct already breaks any literal mirror.
- Evidence: hot-path trace above (executor calls it per list completion;
  installed default-on by `ready()`); measurement
  `review-20260928T213834-c8a48b`: current order 205.8 ns vs swapped 87.5 ns
  median per sync list, delta 118.3 ns, non-overlapping round ranges;
  async path unchanged (3.6 ns noise). Before/after framing: "before" is the
  current order the file uses, "after" is the swapped order the file will use —
  the probe characterizes the two orders absolutely, so Worker-2's
  before/implement reruns reproduce the same pair and the file change selects
  between them; the static Proof below shows the selection landed.
- Impact: 118 ns saved per sync-list completion on every executed operation.
  Sub-bench-spread; no bench figure moves.
- Path class: hot — runs once per list-field completion on every executed
  operation (sync and async) while installed.
- Severity: Low — ns-scale CPU on a hot path without N+1; same shape as the
  `utils/strings.py` L1 branch-order precedent.
- Instrument: timeit scratch probe (interleaved rounds, min-of-5 per round,
  median of 9, 10000 iters). Before: 205.8 ns (current order). After:
  87.5 ns (swapped order). Delta: -118.3 ns (-57%) per sync-list completion;
  async path 173.1 -> 169.6 ns (noise). Permanent test: none can pin 118 ns
  (timing-flaky by construction); the trigger set is pinned by the existing
  10 + 78 behaviour nodes in the Proof. No bench figure moves.
- Recommendation: at the wrapper condition, swap the first two conjuncts to
  `isinstance(result, AsyncIterable) and not is_iterable(result) and
  self.is_awaitable(res)` (91 chars, fits one line). Keep all three conjuncts,
  the delegate-first call, and the residual double-await exactly. A one-line
  order rationale is welcome (upstream comments its own hot-path orderings the
  same way) but not required.
- Must not change: the exact trigger set (wrap iff not-sync-iterable AND
  async-iterable AND `res` awaitable); delegation to
  `_original_complete_list_value` before the predicates (upstream raises on
  non-iterables before they run); the residual double-await outcome.
- Proof:
  - `uv run python -c "src=open('django_strawberry_framework/_graphql_core_patches.py').read(); assert src.index('isinstance(result, AsyncIterable)') < src.index('not is_iterable(result)'), 'conjunct order'"` (shared tree, no import; fails before, passes after; format-proof).
  - `uv run python scripts/workspace.py run review/_graphql_core_patches.py/verify-performance-<n> -- pytest tests/test_graphql_core_patches.py --no-cov` reports `10 passed`.
  - `uv run python scripts/workspace.py run review/_graphql_core_patches.py/verify-performance-<n> -- pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov` reports `78 passed`.
  - Number reproduction: rerun the probe at `review/_graphql_core_patches.py/verify-performance-<n>`; expect the same pair within run noise (swapped median below 0.6x current median, round ranges non-overlapping on the sync path).
- Freshness: all files in `## Trace`.

Looks-for discharge (REVIEW.md "Performance"), each `none` with the reason:

- N+1 / per-row queries, `await` per row, `.filter()` on a prefetch: none;
  zero queries — the module has no Django ORM reference (no `django` import;
  it operates on graphql-core executor values). The one `await` awaits the
  single residual awaitable per async list, which IS the fix.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()` (either direction):
  none; no queryset in the module.
- `only()` / `defer()` deferred loads: none.
- Unbatched writes (`bulk_create` / `bulk_update`): none; no writes.
- `blog.id` vs `blog_id`: none; no model-instance attribute access.
- Repeated `_meta` walks: none; no `_meta` in the module.
- Repeated settings reads: none on any hot path — `apply` reads
  `upstream_patches_enabled("graphql_core")` once per call, and `apply` runs
  at app load plus tests (docstring-pinned "Read once per patch `apply()`
  (i.e. at app load)").
- Repeated regex compilation: none; no regex in the module.
- Repeated schema or type lookups per request: none; per-completion work is
  three pure predicates, no lookups. Upstream re-evaluates two of them — that
  duplication ends only by restructuring upstream (R2).
- `lru_cache` on methods (`B019`): none; the module holds no cache.
- Locks, cache reads, re-parses or extra round trips on a per-request path:
  none added — the wrapper adds one call plus pure predicates, no I/O. The one
  re-parse (`inspect.signature` per `apply`) is cold; see R3.
- Import-time cost: measured 0 via package import (no report row, 69 rows);
  the module loads lazily in `ready()` only. See R4.
- Allocation in the walk: the optimizer walk never touches the module, and the
  sync path allocates nothing per call (pure predicates; upstream's own branch
  allocates the same way). The `_await_residual` closure exists only on the
  async path, which already allocates a coroutine upstream. See R6.

## Rejected

- **R1: `is_awaitable`-first order (`self.is_awaitable(res) and ...`).**
  Structurally dominated: on the common sync path `res` is a plain list, where
  `is_awaitable` costs two `isinstance` checks plus a `hasattr` — more than
  the single ABC check F1 puts first — and on sync lists with async children
  it is true, so no short-circuit is saved either. Reopens if both orders are
  measured and `is_awaitable`-first wins, or the wrapper ever needs
  `res`-awaitability for a non-`AsyncIterable` class.
- **R2: drop `not is_iterable(result)` (wrap whenever `AsyncIterable` plus
  awaitable).** Broadens the trigger set to doubly-iterable results with async
  children. Outcomes coincide today only because upstream's sync-path coroutine
  is fully completing — an upstream behaviour detail
  `_validate_upstream_shape` does not pin (signature only). Keep the exact
  bug-shaped trigger set. Reopens if the retirement sentinel shows upstream
  unifying the branches, or shape validation pins coroutine-completeness.
- **R3: cache anything across `apply()` calls (`inspect.signature`, the
  settings read plus mapping validation, the installed-check `class_dict`).**
  Cold: `apply` runs at `ready()` (at most a few times per process) plus tests;
  lifetime cost is microseconds. Caching would trade the fail-loud
  revalidate-then-install plainness for time nobody observes. Reopens if
  `apply()` is ever called per request or in a tight loop.
- **R4: the `ready()` import of the patch module costs startup time.**
  Package-import contribution measured 0 (no report row,
  `review-20260928T214159-3d0a64`); the `ready()` import adds exactly the one
  module file (its `.conf` / `.utils.truth` imports already have package-import
  rows, `graphql.*` is pre-paid by strawberry) plus one capture and two
  `setattr` calls, once per process. Cold, one-time, no plain fix — skipping
  the import needs a signal Django does not provide. Reopens if the module
  gains import-time work or an import no sibling already pays.
- **R5: the concurrent truthful-reads delta (`truth.class_dict` in the capture
  and installed-check paths, plus the import).** Both sites run at import or
  `apply` time only — cold — and the delta is concurrent work outside this
  item's fence (it predates `ITEM_BASELINE`; the item diff is empty), so no
  finding here may touch it. Reopens if any of the three functions moves onto
  a hot path.
- **R6: hoist `_await_residual` to module level to avoid defining a closure
  per async-list completion.** The definition runs only on the async path,
  which already allocates at least one coroutine upstream, and hoisting would
  thread `is_awaitable` through for zero observable gain. Reopens if async-list
  completion profiling shows closure definition on the measured path.

No bench figure moves for any finding or rejection above. The probes stay
re-runnable from the commands in `## Trace` at
`review/_graphql_core_patches.py/verify-performance-<n>`.

Handoff: Read beyond the trace: installed graphql-core 3.2.8
`pyutils/is_iterable.py` whole (the 1+5 `isinstance` shape F1 turns on),
`ExecutionContext.complete_list_value` and `is_awaitable` in installed
graphql-core 3.2.8's `graphql/execution/execute.py` (the branch F1's condition
corresponds to; the async branch
always returns a coroutine, which is why the third conjunct is pure defence),
`conf.py::upstream_patches_enabled` whole (one settings read per `apply`),
`utils/truth.py::class_dict` (the concurrent delta's cold call), and
`tests/test_graphql_core_patches.py` whole (the install lifecycle plus the
retirement sentinel that pins the trigger set F1 must preserve). Conclusions
not in the findings: F1 is deliberately minimal — swap, not drop (R2) or
reorder around `res` (R1) — because the condition's value is its exact
correspondence to upstream's async branch, and the fix preserves that set
while paying the cheapest test first. Open threads: none on Performance. The
one fact a later pass must not misread is the before/after framing: the probe
characterizes the two orders absolutely, so Worker-2's before/implement reruns
reproduce the same pair — the file change only selects between them, and the
static Proof asserts the selection. Sibling axis records did not exist when
this pass closed; this record places no cross-axis text. Scratch kept under
`docs/review/temp-tests/_graphql_core_patches/performance/` (inspect/,
`_graphql_core_patches.json`, `probe_predicate_order.py`,
`predicate_order.json`, `importtime.json`); no source file in the copy at
`review/_graphql_core_patches.py/performance` was created, edited, or deleted.

## Verification (Performance)

Pass 1, address `review/_graphql_core_patches.py/verify-performance-1`,
cell `default`. Ordering disclosure: this pass read the main artifact's
`## Implementation (Worker-2)` before running the Proof lines, against the
verify order in `worker-1.md`. The Proofs below were then run verbatim with
mechanical results (exit codes, node counts, medians), so the violation
touches procedure, not the evidence; Worker-0 judges whether it matters.

Step 1: `git diff e4385002efab0df029451349a7738a02e19928e2 --
django_strawberry_framework/_graphql_core_patches.py` is byte-equal to
`<root>/diff/pass-1.diff` (sha256
`d3ffd3146b7586ef3d2bdc9740fba17968a39626bf8da7580cfc85765a519650`
both sides). The tree did not move under the pass. No other record holds a
`## Cross-axis (for Performance)` section (Mechanics: none; Comments: none),
so the four Proof lines below are the whole Proof set.

Proof results (record's lines, verbatim):

- Static conjunct order (shared tree, no import): exit 0, `STATIC-PROOF-PASS`.
  The file uses the swapped order; zero old-order remnants (`grep -c "not
  is_iterable(result) and isinstance"` prints `0`).
- `workspace.py run review/_graphql_core_patches.py/verify-performance-1 --
  pytest tests/test_graphql_core_patches.py --no-cov`:
  `review-20260928T215500-a3fddb`, digest `sha256:a5e0fd4e...` (final state),
  copy fresh, shared unmoved: `10 passed`.
- `workspace.py run review/_graphql_core_patches.py/verify-performance-1 --
  pytest examples/fakeshop/test_query/test_list_field_async_api.py --no-cov`:
  `review-20260928T215513-e59554`, same digest, fresh: `78 passed`.
- Number reproduction at the verify address (record's probe, blob `3c415038`,
  by absolute path): `review-20260928T215540-0b139e`. Sync current 213.2 ns
  median (rounds 211.2-217.8) vs swapped 89.4 ns (88.2-91.8): ratio 0.419
  (Proof bar: below 0.6x), round ranges non-overlapping; async 176.3 vs
  174.2 ns, delta 2.1 ns noise. Reproduces the record's pair (205.8 / 87.5,
  delta 118.3) within run noise.

Worker-2 numbers reproduced from the recorded command: the
before/after JSONs under `<root>/implement/` match the report's claims
exactly (before 210.5/90.0 delta 120.5, async 176.1/172.6; after 211.5/87.6
delta 123.9, async 173.1/168.5), and this pass re-ran the probe both at the
verify address (above: 213.2/89.4, delta 123.8) and read-only at
`review/_graphql_core_patches.py/before` (never `--fresh`, never edited):
`review-20260928T215605-3ec434`, digest `sha256:c5a27421...` = the record's
digest: sync 206.7/87.3, delta 119.4; async 174.8/170.3. All three pairs
agree within noise; probe blob `3c415038` identical in all three runs. No
bench figure moves (ns-scale, sub-spread); nothing is claimed against `##
Bench baseline`, as the record frames.

Whole-diff read through Performance: the item diff is exactly two hunks
(`a188b290..90ac4f3c`). The pragma-comment hunk (Comments F1) is prose-only
with zero performance effect. The guard hunk is F1, implemented exactly per
the Recommendation (all three conjuncts, delegate-first call, residual
double-await untouched; no rationale comment added, which the record leaves
optional). No other axis changed code (Mechanics no-findings), so there is
no cross-axis hot-path move to measure. The new guard line is one line at
96 chars (within the 99 limit); the record's "91 chars" and the report's
"94 chars" both miscount the prose, immaterially — not a gap.

Attacks, all recorded with run ids, all passing:

- Doubly-iterable results (both sync-iterable and `AsyncIterable`): the one
  input shape where the swapped order evaluates MORE predicates (isinstance
  True, then `is_iterable` runs) than the current order (short-circuits at
  `not is_iterable`). Own probe `<root>/verify-performance-1/
  attack_doubly_iterable.py`, `review-20260928T215645-be2c4d`: current 211.1
  ns vs swapped 282.9 ns median, delta -71.8 ns, ranges non-overlapping. Real
  cost, bounded (~72 ns), on a near-nonexistent path: upstream dispatches
  both-iterables to its sync branch (Mechanics R6), plain lists / tuples /
  querysets are sync-only, async generators async-only, so a both-iterable
  list result is pathological while EVERY sync-list completion saves ~120 ns.
  Trigger set identical (conjunction commutes; the probe asserts equal
  booleans). The trade is correct; no finding.
- Async-iterable path: both orders evaluate the same predicates; measured
  deltas 2.1-4.6 ns across all runs are noise. No attack surface.
- Cells: sharded and pg `inapplicable by construction`, concur — the target
  has no `django` import and zero queries (the only "django" hits are stamp
  strings and error text); the hot path is three pure predicates over
  in-memory executor values. `count_queries.py` would exit 2.
- Unnamed caller: `DjangoMutationExecutionContext` inherits the patched slot
  (Mechanics trace) — the same wrapper and trigger set, covered by the same
  10 + 78 behaviour nodes; no separate caller exists to attack.

Disputes: none recorded (`## Implementation (Worker-2)` carries no
`disputed:` line). Nothing to judge.

Failability: Worker-2's if-False/if-True trigger-set mutants instead of a
revert — upheld. A revert-prove is meaningless for a semantics-preserving
reorder (the conjunction commutes, so a revert passes everything); the
load-bearing property is the exact trigger set, and breaking it in each
direction is the correct failability evidence. This pass ran its own widened
prove, `workspace.py prove
review/_graphql_core_patches.py/verify-performance-1
<root>/verify-performance-1/failability_manifest.json`,
`review-20260928T215917-d93a48`, exit 0: entry 1 (guard `if False:`,
11-node scope = unit file + async pin) baseline 11 passed, mutant fails
exactly the declared async-children live node, unit file untouched;
entry 2 (guard `if True:`, full 78-node live file) baseline 78 passed,
mutant fails exactly the declared 44 rows (34 pass); both restores
byte-proved (`filecmp` True, sha256 equal), neither weakly pinned. The
widening breaks 44 live rows, not one cherry-picked node — the delegation
pin is broad.

Test tier: no new test owed — concur with the record that no test can pin
118 ns (timing-flaky by construction). The trigger set is pinned at the
strongest reachable tiers: live `/graphql` (78 nodes) plus package (10
nodes). Permanent-test mandate satisfied without a new file.

Fingerprints (`git hash-object`): target `90ac4f3cc15be1c24dc1f0281206e260d7555cb6`
(= Worker-2's touched state); `tests/test_graphql_core_patches.py`
`53dca51737e6163c09549d015713ebf9dfcdec88`, live file
`49e423ea593b8883c4c07593accd822390e82468`, probe `3c4150384034f8f2f7d972dc3d3c440a579a5b8f`
(all equal to the records': nothing drifted).

Scratch under `<root>/verify-performance-1/`: `live_proof.log/.stderr`,
`number_repro.json/.stderr`, `before_confirm.json/.stderr`,
`attack_doubly_iterable.py/.json/.stderr`, `iftrue_probe.log/.stderr`,
`iftrue_failing_nodes.txt`, `failability_manifest.json`. The copy was
hand-mutated twice for blast-radius probing (if-False: `1 failed, 10 passed`,
`review-20260928T215751-2b1045`; if-True full file: `44 failed, 34 passed`,
`review-20260928T215817-ed38a8`), then resynced `--fresh`
(`review-20260928T215903-1ccb40`, digest `a5e0fd4e...`) before the prove;
`/tmp/verify_perf_pristine.py` safety copy superseded by the resync.

Verdict: `Status: verified`. No new findings, no named gaps on any axis,
nothing for `## Decisions`. F1 landed exactly as specified, its number
reproduces from three independent runs, and the trigger-set gates fail
exactly where declared in both directions.

Handoff: The one thing the next reader must not re-litigate is the
before/after framing: the probe characterizes the two conjunct orders
absolutely (file-independent), so before/implement/verify reruns all
reproduce the same pair and only the static Proof asserts which order the
file selects — the delta is never measured off the file. New information
this pass adds beyond the report: (1) the doubly-iterable rare-path cost
(+71.8 ns, bounded, trade correct); (2) the if-True blast radius is 44 live
rows, so the delegation pin is broad, not single-node; (3) the unit file is
insensitive to guard narrowing (lifecycle pins only), which is expected, not
a gap. Procedure note: the Implementation-before-Proofs read order is
disclosed above; the evidence is mechanical and Worker-0 judges. Open
threads: none on Performance.
