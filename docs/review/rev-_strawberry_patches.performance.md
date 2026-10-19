# Review · Performance: `django_strawberry_framework/_strawberry_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f3d32be142a493b44bf522d75471843f2fc86285

## Trace

Target read whole (853 lines, blob `2b39199b`). `git diff <ITEM_BASELINE> -- <target>`
is empty, so the tree reviewed is the item baseline. The target is dirty vs HEAD
by exactly the concurrent truthful-reads switch (8 insertions, 5 deletions:
`from .utils import truth`, `truth.class_dict` in
`django_strawberry_framework/_strawberry_patches.py::_captured_upstream_method` and
`django_strawberry_framework/_strawberry_patches.py::_patch_is_installed`), which
predates the item baseline and sits in none of this item's hunks; it touches
import/apply paths only (R6). The plan's `## Owned changes` holds no row for
this target (only the closed `utils/strings.py`, `types/relations.py`,
`_django_patches.py` and `_graphql_core_patches.py` rows).

Orientation: `review_inspect.py` overview at `<root>/performance/inspect/`
(json `<root>/performance/_strawberry_patches.json`): 0 per-row leads, 0 hot
entry points (the static tool cannot see monkeypatch installation; hotness is
established by the installation trace below), 0 ORM markers, `isinstance` x3
(the envelope guard), 9 import-time calls (method capture, `textwrap.dedent`,
four `setattr` stamps).

Symbols and every production caller (search census over the package, tests and
examples; `consumers.py`, `views.py` and `_cross_web_patches.py` mentions are
prose citations, not imports; installed strawberry 0.324.0 sources read for the
call sites below):

- `django_strawberry_framework/_strawberry_patches.py::apply` — called only from
  `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
  (per-process app load; may fire more than once under some Django test
  runners) and from tests. Cold.
- `django_strawberry_framework/_strawberry_patches.py::_patched_parse_json` —
  installed on `BaseView.parse_json` by `apply`; runs once per POST body parse
  (sync and async `parse_http_body`), twice per multipart parse (`operations` /
  `map` fields), and per GET `variables` / `extensions` parse unless shielded.
  Package views reach it via
  `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin.parse_json`
  `super().parse_json(data)` (`views.py:821`), after the boundary's own strict
  decode. Hot: per request, both transports.
- `django_strawberry_framework/_strawberry_patches.py::_translated_parse_json` —
  called by `_patched_parse_json` and `_patched_parse_query_params` on the same
  hot paths: one delegated `json.loads` plus two `except` clauses. Hot.
- `django_strawberry_framework/_strawberry_patches.py::_patched_parse_query_params` —
  installed on `BaseView.parse_query_params`; runs per GET request carrying
  params, routing its two nested parses through the translator so the envelope
  guard stays off the GET path. Hot: per GET request.
- `django_strawberry_framework/_strawberry_patches.py::_patched_sync_parse_multipart`
  / `::_patched_async_parse_multipart` — installed on the two transports'
  `parse_multipart`; one delegated parse plus a `try`/`except` each. Hot: per
  multipart request.
- `django_strawberry_framework/_strawberry_patches.py::_raised_inside_the_upload_utility` —
  runs only inside the multipart delegates' `except` arm, i.e. on a traversal
  failure that is already being raised. Error path only.
- `django_strawberry_framework/_strawberry_patches.py::_validate_upstream_shape`,
  `::_patch_is_installed`, `::_captured_upstream_method`,
  `::_mark_patch_replacement` — at module import or once per `apply`
  (`inspect.signature` + `inspect.getsource` + `dedent` + audited-source
  membership). Cold.

`Path class: hot` — the installed wrappers run once per request body, query-param
or multipart parse on every operation served by the installed Strawberry (sync
and async), including package views through the boundary-mixin delegate.

Measurements, all in copy `review/_strawberry_patches.py/performance` (slot-3),
package digest `sha256:a5e0fd4e...396d` on every run (all three figures compare
with each other; the digest is not the `## Bench baseline` digest, so no figure
is claimed against the baseline table), instruments
`scripts/importtime_report.py` blob `15f679c9`,
`scripts/_bench_common.py` blob `253a3953`, Django 6.1, strawberry 0.324.0:

- `review-20260928T221214-45937b`: `python <root>/performance/probe_hot_costs.py
  <root>/performance/hot_costs.json` (probe blob `028d8f61`, run by absolute
  path, copy unedited). `parity: ok` (patched and pristine return identical
  documents on every accepted input; scalar and `map=[{}]` rejections raise
  the documented 400 reasons). Interleaved timeit medians, patched minus
  pristine: object body str +32.1 ns (779.9 vs 747.8; `json.loads` alone on
  the same body 688.7 ns, so the wrapper is ~4% of the parse); object body
  bytes +39.6 ns; batch of 50 dicts +926.3 ns; batch of 200 dicts +3605.1 ns
  (slope ~18 ns/element for the `all()` scan); query-params shield +21.1 ns
  over two params vs pristine upstream; sync multipart success +126.3 ns
  (2010.0 vs 1883.7); async multipart success +109.0 ns (both sides ~30 us,
  dominated equally by the harness event loop; the delta is the figure).
  Error-path totals (informational, no upstream counterpart): scalar-body
  400 ~1.1 us, `map=[{}]` 400 ~3.2 us including the traceback walk.
- `review-20260928T221228-72d4a4`: `python <root>/performance/probe_cold_costs.py
  <root>/performance/cold_costs.json` (probe blob `38a67f51`).
  `parity: ok`, patch installed. `_validate_upstream_shape` 69.6 us;
  re-entrant `apply` 71.2 us; post-setup import 0.2 us pulling 0 modules;
  marginal import (median of 5 fresh interpreters replaying app-loader order:
  package import untimed, patch import timed, no `django.setup()`) 5.07 ms
  median (4.74 min) pulling exactly 35 modules (the patch module itself plus
  the `cross_web`, `strawberry.http` and `strawberry.subscriptions` trees it
  patches).
- `review-20260928T221231-bc46a2`: `python scripts/importtime_report.py
  --rounds 5 --top 80 --json <root>/performance/importtime.json`: 69 rows,
  none for `_strawberry_patches`, `testing` or `apps` — `import
  django_strawberry_framework` never pulls the patch module, so its
  package-import contribution is 0. Package cumulative 194.7 ms, self
  24.4 ms over 69 modules.

No bench-baseline figure moves: the plan-cache, optimizer-walk and nested-fetch
benches never enter HTTP body parsing, and the import-time row for this module
is absent (package import pulls 0 of it).

Cells: default only. Sharded and pg are `inapplicable by construction`: the
module runs zero queries, performs no connection I/O, reads no alias and makes
no dialect decision; `count_queries.py` would exit 2 with nothing comparable
measured. No `--cell` run.

Fingerprints (`git hash-object`): `django_strawberry_framework/_strawberry_patches.py`
2b39199bb2de42e40ae49d62bd24cc8a7a962c1b;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`django_strawberry_framework/views.py`
48ee582ecdba41d49beb2434f2a9e0af992d39d4 (delegate at `views.py:821` only);
`tests/test_strawberry_patches.py`
94a5bfa489029328cda91dff893882bf8fc93e6f (caller census only);
`examples/fakeshop/test_query/test_transport_api.py`
b1681e8c725ceb46a0243c770a7dcd295edefc06 (caller census only);
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef;
`scripts/_bench_common.py`
253a39533f35b94f6afb7a1167c2c38489bbbbef.
Upstream shapes read in the installed strawberry 0.324.0
(`strawberry/http/base.py`, `sync_base_view.py`, `async_base_view.py`,
`file_uploads/utils.py`): not git-tracked, cited by version.

## Findings

### High

None.

### Medium

None.

### Low

None.

Looks-for discharge (REVIEW.md "Performance"), each `none` with the reason:

- N+1 / per-row queries, `await` per row, `.filter()` on a prefetch: none;
  the module runs zero queries — JSON parsing plus `isinstance` checks only.
  The async multipart delegate awaits the upstream parse exactly once, as
  upstream does.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()` (either direction):
  none; no queryset in the module.
- `only()` / `defer()` deferred loads: none.
- Unbatched writes (`bulk_create` / `bulk_update`): none; no writes.
- `blog.id` vs `blog_id`: none; no model-instance attribute access.
- Repeated `_meta` walks: none; no `_meta` in the module.
- Repeated settings reads: none on any hot path — `apply` reads
  `upstream_patches_enabled("strawberry")` once per call, and `apply` runs at
  app load (at most a few times per process) plus tests; the installed
  wrappers read no settings per request.
- Repeated regex compilation: none; no regex in the module.
- Repeated schema or type lookups per request: none — the wrappers call
  module-global captured callables (one `LOAD_GLOBAL` each, no table walk)
  and touch no schema or type registry. The installed-method dispatch itself
  is the attribute lookup the pristine path also pays.
- `lru_cache` on methods (`B019`): none; the module holds no cache.
- Locks, cache reads, re-parses or extra round trips on a per-request path:
  none added — the body is parsed exactly once by the delegated original (no
  re-parse: the companion `cross_web` patch moves the sync raise into
  `parse_json` rather than decoding eagerly); no locks, cache reads, or I/O.
  The GET shield routes around the patched method straight to the translator,
  so GET params skip the envelope guard entirely (measured +21.1 ns vs
  pristine over two params).
- Import-time cost: measured zero via package import (no report row) and
  5.07 ms self-plus-upstream via `ready()` once per process (R4); no
  settings read at import.
- Allocation in the walk: the walker never touches the module, and the hot
  wrappers allocate nothing on success beyond the parsed document itself
  (two `isinstance` tests; the batch `all()` generator is O(1) space; the
  shield's `dict(params)` copy is byte-for-byte upstream's). See R1-R3.

## Rejected

- **R1: per-request `parse_json` overhead (+32.1 ns object str, +39.6 ns
  bytes; shield +21.1 ns over two params;
  `review-20260928T221214-45937b`).** Two extra frames plus the guard's
  `isinstance` tests, against ~750 ns of `json.loads` on the same body and
  milliseconds of request handling. The only removable slice is inlining
  `_translated_parse_json` into its two callers (~tens of ns per the shield
  delta), which duplicates the two-clause translation the module keeps in
  one place precisely so the two call sites cannot drift. Plainness and the
  single owner win. Reopens if the translator gains per-call work beyond
  the two `except` clauses, or a request budget names `parse_json`.
- **R2: the batch `all()` scan is O(n) in batch size (~18 ns/element:
  +926.3 ns at 50, +3605.1 ns at 200;
  `review-20260928T221214-45937b`).** The scan IS the guard — upstream
  checks no element types, so any sampling or length cap that skips
  elements misses a trailing scalar and recreates the 500 (correctness, not
  tunability). Upstream re-iterates the batch twice more downstream
  (validation, per-item `.get`), so this is the cheapest of its three
  passes; even a 200-operation batch pays +3.6 us against 45 us of parse
  alone. Reopens if batch sizes grow unbounded without upstream fixing
  #3398, or the scan is ever performed twice per request.
- **R3: multipart delegates cost +126.3 ns sync / +109.0 ns async on the
  success path, and the `map=[{}]` translation costs ~3.2 us total
  (`review-20260928T221214-45937b`).** Success-path delta is the wrapper
  `try`/`except` (zero-cost when quiet) plus the two guarded tiny parses;
  the ~3.2 us error-path total (one `json.loads`, the upload utility's
  `deepcopy`, the traceback walk) runs only for a request that is already
  being rejected. Caching `replace_placeholders_with_files.__code__` would
  save one attribute lookup per translated failure only. Reopens if the
  success path gains work or the traceback walk leaves the error path.
- **R4: `ready()` imports the patch module plus 35 upstream modules
  (`cross_web`, `strawberry.http`, `strawberry.subscriptions` trees) for
  5.07 ms once per process (`review-20260928T221228-72d4a4`).** Cold,
  one-time, and shared: the sibling `cross_web` patch needs the same
  trees, and any process that serves HTTP GraphQL imports `strawberry.http`
  through its views regardless — the patch import only moves that cost
  from URL load to app load. Only a Django process that never touches the
  views (a worker) pays it purely for the patch, and 5 ms once per process
  is noise against Django startup. Checking the gate before importing
  upstream would complicate the capture-at-import / reload-recovery design
  for milliseconds nobody observes. Reopens if a startup budget names app
  load, the import set grows, the module gains import-time work, or the
  gate-off path must stop paying the import.
- **R5: re-entrant `apply()` re-validates before the installed-check
  (`inspect.signature` + `getsource` + `dedent`, 69.6 us of the 71.2 us
  re-entrant total; `review-20260928T221228-72d4a4`).** Cold: `ready()`
  fires at most a few times per process, so the lifetime cost is ~0.2 ms.
  Caching the validated source across calls would trade the fail-loud
  drift check's plainness (revalidate-then-install, every time) for
  microseconds nobody observes. Reopens if `apply()` is ever called per
  request or in a tight loop — then validate once and only re-validate
  when an installed method changes.
- **R6: the concurrent truthful-reads delta (`truth.class_dict` in the
  capture and installed-check paths).** All sites run at import or `apply`
  time only — cold, inside the measured 5.07 ms marginal import and
  71.2 us re-entrant `apply` totals — and the delta is concurrent work
  outside this item's fence (it predates `ITEM_BASELINE`), so no finding
  here may touch it. Reopens if any of the touched functions moves onto a
  hot path.

No finding carries a Proof line: zero findings means no `Proof` is owed,
and no bench figure moves. The probes stay re-runnable from the commands
in `## Trace` at `review/_strawberry_patches.py/verify-performance-<n>`.

Handoff: Read beyond the trace: `apps.py::ready` whole (the once-per-process
caller; function-local imports of all four patch modules), `__init__.py`
whole (no patch import at package import — the importtime absence is by
construction), `conf.py::upstream_patches_enabled` (one settings read per
`apply`, whole-mapping validation), `utils/truth.py::class_dict` (the
concurrent delta's added hop, cold), `views.py::_RequestBodyBoundaryMixin.parse_json`
body (the per-request package-view delegate at `views.py:821`), the
installed strawberry 0.324.0 `base.py` / `sync_base_view.py` /
`async_base_view.py` / `file_uploads/utils.py` call sites (the nine-site
inventory in the module docstring holds: POST body, two multipart fields
and GET params per transport plus the dead-code subscription site), and the
`tests/test_strawberry_patches.py` / `test_transport_api.py` caller census
via search (apply lifecycle plus live wire pins, no new hot caller). Sibling
axis records did not exist when this pass closed, so no cross-axis text
existed to answer; this record places none. Open threads: none on
Performance. The two facts a later pass must not misread: (1) the hot-path
deltas (+32 ns object, ~18 ns/batch element, +126 ns multipart) are the
feature's own cost, removable only by weakening the guard or duplicating
the translator — that is why this hot module carries zero findings; (2) the
5.07 ms marginal import is first-importer cost for upstream trees every
HTTP-serving process pays regardless, not patch code. Scratch kept under
`docs/review/temp-tests/_strawberry_patches/performance/` (inspect/,
`_strawberry_patches.json`, `probe_hot_costs.py`, `hot_costs.json`,
`probe_cold_costs.py`, `cold_costs.json`, `importtime.json`); the copy at
`review/_strawberry_patches.py/performance` was never edited (every header
reads `fresh`).

## Verification (Performance)

Step 1: `git diff f3d32be142a493b44bf522d75471843f2fc86285 --
django_strawberry_framework/_strawberry_patches.py
tests/test_strawberry_patches.py tests/test_views.py
examples/fakeshop/test_query/test_products_api.py
examples/fakeshop/test_query/test_transport_api.py` is byte-identical
to `docs/review/temp-tests/_strawberry_patches/diff/pass-1.diff` (both
`sha256:210d0559...3a6fd4e23`, 12095 bytes); the tree did not move
under the pass.

Proof lines: none owed, none run. This record carries zero Proof
lines (zero findings; `## Findings` states "no `Proof` is owed"),
the Mechanics record holds no `## Cross-axis` section, and the
Comments record's `## Cross-axis` is None — there is no Performance
proof anywhere to execute, at any address.

Worker-2 numbers for this axis: none claimed ("no number moved, no
bench figure touched", hot-path deltas stand, `## Bench baseline`
untouched), so step 2 reproduces the reviewer's three figures
instead. All three re-ran at
`review/_strawberry_patches.py/verify-performance-1`, cell `default`,
copy slot-2 (synced 2026-09-28T22:51:55+00:00, never edited — every
header reads `fresh`; the fourth run notes shared-moved 1 for the
concurrently written Mechanics verification record, while its
package digest matches the other three, so the measured tree is
identical), package digest
`sha256:41e15d13e6b3319ad3be2833eed44c172f16590b77b202838bfc57cc2e52a54c`.
The digest differs from the reviewer's `a5e0fd4e...` for the expected
reason: pass 1 changed package prose bytes. Code is identical (five
`--code-digest` equalities below), instruments are identical
(`importtime_report.py` `15f679c9`, `_bench_common.py` `253a3953`,
Django 6.1, strawberry 0.324.0), and the two probe blobs are the
reviewer's byte-for-byte (`028d8f61`, `38a67f51`).

Reproduction (reviewer -> verifier):

- Hot costs, `review-20260928T225155-5ca57b` (probe by absolute path,
  `--json` under `verify-performance-1/`, `parity: ok` and identical
  400 reasons both sides): object str delta 32.07 -> 44.25 ns
  (779.90/747.83 -> 743.82/699.57; `json.loads` anchor 688.66 ->
  663.77 ns, so the wrapper stays ~5% of the parse); object bytes
  39.63 -> 45.87 ns; batch 50 926.31 -> 1019.21 ns; batch 200
  3605.08 -> 3253.42 ns (slope ~18 -> ~15 ns/element);
  query-params shield 21.10 -> 8.38 ns over two params; sync
  multipart 126.28 -> 102.85 ns; async multipart 109.04 -> 226.96 ns
  (both sides ~29-30 us, harness-event-loop dominated; the delta is
  loop noise). Error-path totals: scalar 400 1129.23 -> 1131.00 ns,
  `map=[{}]` 400 3181.83 -> 3267.25 ns. Every delta the same order
  of magnitude, within interleaved-median run noise on a shared
  machine; no figure moves in the load-bearing sense.
- Cold costs, `review-20260928T225204-a54b1d`: `parity: ok`,
  installed true. `_validate_upstream_shape` 69.63 -> 65.45 us;
  re-entrant `apply` 71.24 -> 68.24 us; post-setup import 0.209 ->
  0.205 us pulling 0 modules; marginal import median 5070.46 ->
  5383.33 us (min 4744.42 -> 4887.71) pulling exactly the same 35
  modules (same sorted list). Timings within noise; counts exact.
- Import time, `review-20260928T225209-b33b90`
  (`importtime_report.py --rounds 5 --top 80`): 69 rows both sides,
  none for `_strawberry_patches`, `testing` or `apps` either side —
  package-import contribution still 0. Package cumulative 194.7 ->
  201.7 ms, self 24.4 -> 24.0 ms over the same 69 modules is
  cross-session machine drift on modules this item cannot touch (the
  patch module is not among the imported set), not an item effect.
  Instrument ids identical to the reviewer's both scripts.

Item diff read whole through this axis: 15 hunks across 5 files
(+36/-29), every hunk docstring or comment lines only (F1, F2, F8,
L1, L2, L3 on the target; F3, F9, F10, L4 in the own test module;
F6 in `tests/test_views.py`; F4, F5, L6 in `test_products_api.py`;
F7, L5 in `test_transport_api.py`), zero executable lines.
Corroborated independently: `review_inspect.py --code-digest
f3d32be1...:<path> <path>` exits 0 with equal digests on all five
files (`6d124535...6f4b61e`, `9cd25a75...2a220ca`,
`98eeaeb6...6d7ad0ec`, `c4bc802f...6d7ee`, `f282ed6d...1963b3d`),
matching every digest Worker-2 claimed. A prose-only diff moves no
number — confirmed: every figure above reproduces, and no bench
figure moves (the plan-cache, optimizer-walk and nested-fetch
benches never enter HTTP body parsing).

Attacks on the current state (all pass, no new finding):

- Unmeasured cardinality: batch-100 probe
  (`attack_batch100.py`, `review-20260928T225309-3e314d`, same
  address, `parity: ok`): delta 1633.71 ns (23186.25 vs 21552.54),
  i.e. 16.34 ns/element; segment slopes 50->100 12.29, 100->200
  16.20, 50->200 14.89 ns/element — linear, inside the reviewer's
  ~18 ns/element band, no quadratic hiding between the measured
  points. R2's "cheapest of upstream's three passes" stands.
- Static census on the live target: zero ORM/query/cache/regex
  tokens (`objects.` / `QuerySet` / `.filter(` / `bulk_create` /
  `bulk_update` / `_meta` / `lru_cache` / `re.compile` — 0 hits);
  the one settings read (`upstream_patches_enabled`, target
  line 847) sits inside `apply()` (cold, app load), the other hits
  are docstring prose; `isinstance`/`all` code hits are only the
  guard (lines 643/645); `dict(params)` only the pinned upstream
  source (line 466) and the shield body (line 685).
- Cells attack: zero DB/alias/dialect tokens (`connection` /
  `using=` / `alias` / `postgres` / `sqlite` / `shard` / `dialect` /
  `vendor` — 0 hits); the module still runs zero queries and reads
  no alias. Sharded and pg remain `inapplicable by construction` —
  I concur with the reviewer's stated reason.
- Caller census unchanged: `apply` only from `apps.py::ready`
  (function-local import, cold) and tests; the hot wrappers are the
  same installed slots, package views still via the
  boundary-mixin delegate. No new hot caller exists; `Path class:
  hot` stands, and R1-R6 stand with it.
- No cardinality, flavor, cell or caller variant can move a number
  the diff cannot change: the wrapper, translator, shield,
  delegates, validation and import paths are byte-identical code.

Disputes: none recorded — `## Implementation (Worker-2)` carries
zero `disputed:` lines ("no disputed, deferred, blocked, or stopped
row"); nothing to judge.

Failability and test tier: none owed. A prose-only change adds no
test, removes no node, and no gate relies on it; Worker-2's "no
permanent test, no failability" is correct for this axis. No
`workspace.py prove` run.

Cells: `default` only. Sharded and pg `inapplicable by
construction` (concur, see attacks). Cells unverified: none.

Fingerprints (`git hash-object`, live tree as verified): target
`90f711fb420b8902434406735c2e367f011e4177` (equals Worker-2's
after-hash; its before-hash `2b39199b...` equals this record's
`## Trace`); `tests/test_strawberry_patches.py`
`c06add916e033bd1e8e43211541d21bb1619ab14`;
`tests/test_views.py`
`3f9c81153f4fa742479d1b8d7792a18e294e6253`;
`examples/fakeshop/test_query/test_products_api.py`
`fe78cf9d4862123442611444d44bf81b5187ec6d`;
`examples/fakeshop/test_query/test_transport_api.py`
`6d65274f9e7b5589d60777d7e0484b3ad10df394` (all four equal
Worker-2's after-hashes); unchanged and equal to this record's
`## Trace`: `apps.py` `8ae1a3a3...`, `conf.py` `ae3de0a3...`,
`__init__.py` `0ef72601...`, `utils/truth.py` `d5c96bc8...`,
`views.py` `48ee582e...`, `importtime_report.py` `15f679c9...`,
`_bench_common.py` `253a3953...`. Probe copies under
`verify-performance-1/` hash `028d8f61...` and `38a67f51...`,
identical to the reviewer's; the attack script hashes
`9ea11790...`.

Scratch: `docs/review/temp-tests/_strawberry_patches/verify-performance-1/`
(two probe copies, one attack script, four JSON outputs). The copy
at `review/_strawberry_patches.py/verify-performance-1` was never
edited (every header reads `fresh`).

Handoff: Verification is complete with no new finding: zero proofs
owed, three figures reproduced within noise, prose-only identity
independently confirmed on all five files, a batch-100 attack
confirms the linear slope, static and caller censuses unchanged, no
dispute to judge, no failability owed, no cell left unverified. The
one fact a later pass must not misread is the package-digest change
(`a5e0fd4e...` -> `41e15d13...`): it is the pass-1 prose bytes, not
a code change — the five `--code-digest` equalities are the binding
proof. Nothing routes elsewhere; no open thread on Performance.
