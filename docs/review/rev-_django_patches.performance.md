# Review · Performance: `django_strawberry_framework/_django_patches.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8482f9a925f3c073013b20e7ef783e9dc5c1ac3e

## Trace

Target read whole (427 lines, blob `63f3fa9c`). `git diff <ITEM_BASELINE> -- <target>`
is empty, so the tree reviewed is the item baseline. The target is dirty vs HEAD
by exactly the concurrent truthful-reads switch (10 insertions, 6 deletions:
`from .utils import truth`, `truth.class_dict` / `truth.is_instance` in
`django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor`,
`django_strawberry_framework/_django_patches.py::_validate_upstream_shape` and
`django_strawberry_framework/_django_patches.py::_patch_is_installed`), which
predates the item baseline and sits in none of this item's hunks; it touches
import/apply paths only (R5). The plan's `## Owned changes` holds no row for
this target (only the closed `utils/strings.py` and `types/relations.py` rows).

Orientation: `review_inspect.py` overview at `<root>/performance/inspect/`
(json `<root>/performance/_django_patches.json`): 0 per-row leads, 0 hot entry
points, 0 ORM markers, one `isinstance` site, 7 import-time calls (descriptor
capture, two `textwrap.dedent`, `globals().get`, two `setattr`).

Symbols and every production caller (search census over the package, tests and
examples; sibling `_strawberry_patches.py` mentions are prose precedent, not
imports):

- `django_strawberry_framework/_django_patches.py::apply` — called only from
  `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`
  (per-process app load; may fire more than once under some Django test
  runners) and from tests. Cold.
- `django_strawberry_framework/_django_patches.py::_patched_remove_databases_failures` —
  installed on `SimpleTestCase` by `apply`; runs at `tearDownClass`, once per
  test class, over connection aliases with `getattr` / `setattr` only (no
  query, no connection I/O). Cold, test-only.
- `django_strawberry_framework/_django_patches.py::_validate_upstream_shape` —
  once per `apply` (`inspect.signature` + `inspect.getsource` + `dedent` +
  audited-set membership). Cold.
- `django_strawberry_framework/_django_patches.py::_patch_is_installed` —
  once per `apply` plus tests. Cold.
- `django_strawberry_framework/_django_patches.py::_captured_upstream_descriptor` —
  at module import (and reload recovery). Cold.
- `django_strawberry_framework/_django_patches.py::_disallowed_connection_methods` —
  once per connection per teardown (two string `==` against the audited
  sources, then one attribute read). Cold.
- `django_strawberry_framework/_django_patches.py::_is_database_failure` —
  the teardown loop plus
  `django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`
  (consumer test `setUp` / debug middleware / instrumentation; no
  package-internal caller on any request path). One `None` check plus one
  `isinstance`, ~45 ns (R4).

No optimizer, resolver, connection, schema-build or request-handling module
imports or calls the target.

`Path class: cold` — every executable line runs at process start
(import / `ready()`), at test-class teardown, or at consumer test setup;
nothing runs per request, resolver, row, connection or outbound message in
the package's own request path.

Measurements, all in copy `review/_django_patches.py/performance` (slot-2),
package digest `sha256:c9db5de2...0eae97c9` on every run (all four figures
compare with each other; the digest is not the `## Bench baseline` digest, so
no figure is claimed against the baseline table), instruments
`scripts/importtime_report.py` blob `15f679c9`,
`scripts/_bench_common.py` blob `253a3953`:

- `review-20260928T205807-0b49f2`: `python <root>/performance/probe_cold_costs.py
  <root>/performance/cold_costs.json` (probe blob `e582889d`, run by absolute
  path, copy unedited; Django 6.1, connection-feature shape, 4 disallowed
  methods). `parity: ok`. timeit medians: `_is_database_failure` 45.0 ns
  (hit) / 47.1 ns (miss); `_disallowed_connection_methods` 54.3 ns per
  connection; `_validate_upstream_shape` 50.0 us; re-entrant `apply` 51.5 us;
  patched teardown 1357.8 ns vs upstream 1177.8 ns on an all-wrapped
  connection (delta 180 ns per teardown, i.e. one `isinstance` per method).
- `review-20260928T205835-a4164d`: `python scripts/importtime_report.py
  --rounds 5 --top 80 --json <root>/performance/importtime.json`: 69 rows,
  none for `_django_patches`, `testing` or `apps` — `import
  django_strawberry_framework` never pulls the patch module, so its
  package-import contribution is 0. Package cumulative 178.2 ms over
  69 modules.
- `review-20260928T205919-a572f4`: `python <root>/performance/probe_import_cost.py
  <root>/performance/import_cost.json` (probe blob `6846616b`): post-setup
  import is a 0.5 us `sys.modules` dict hit pulling 0 modules — `ready()`
  eagerly imports the module once per process at startup, and every later
  import is free.
- `review-20260928T205955-059fe3`: `python
  <root>/performance/probe_import_marginal.py
  <root>/performance/import_marginal.json` (probe blob `de611e0a`, median of
  5 fresh interpreters replaying app-loader order: package import untimed,
  patch import timed): 96.6 us median (93.4 min), exactly 1 new module (the
  patch module itself). `django.test.*` is already in `sys.modules` before
  the patch import because the package pays it via
  `django_strawberry_framework/conf.py` (`from django.test.signals import
  setting_changed`), whose parent `django/test/__init__.py` imports
  `testcases`/`client`/`utils` (verified in the installed Django 6.1
  source) — so the patch import adds no test-framework cost of its own.
  Header notes `shared moved: 1 (docs/dry/dry-file-testing__init__.md)`,
  concurrent docs work outside the package; the digest matches the other
  three runs.

Cells: default only. Sharded and pg are `inapplicable by construction`: the
module runs zero queries, performs no connection I/O (the teardown loop's
`getattr`/`setattr` touch attributes, never the database), reads no alias
and makes no dialect decision; `count_queries.py` would exit 2 with nothing
comparable measured. No `--cell` run.

Fingerprints (`git hash-object`): `django_strawberry_framework/_django_patches.py`
63f3fa9cba4369ce485a311c8d4f16e78c921768;
`django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/testing/_wrap.py`
0df97813659bea9ed2002f64e6885896c5cabd6f;
`django_strawberry_framework/testing/__init__.py`
48b45d1b433283c40bf8d602d71a26d261a833b2;
`django_strawberry_framework/utils/truth.py`
d5c96bc8d191d3fce0a20140d8e91063bb466ec9;
`tests/test_django_patches.py`
e26a26099c12efb2e2cab1e324b73226eab5dd76 (caller census only);
`tests/testing/test_wrap.py`
4d3c1351254377197994ee577e4f77844c7c309b (caller census only);
`tests/test_apps.py`
5ca8b62c53185343ebfec95315f59ec6104fc851 (caller census only);
`scripts/importtime_report.py`
15f679c9ad736b71215d8ead0733116f56083cef;
`scripts/_bench_common.py`
253a39533f35b94f6afb7a1167c2c38489bbbbef.

## Findings

### High

None.

### Medium

None.

### Low

None.

Looks-for discharge (REVIEW.md "Performance"), each `none` with the reason:

- N+1 / per-row queries, `await` per row, `.filter()` on a prefetch: none;
  the module runs zero queries — the teardown loop iterates connection
  aliases and performs `getattr`/`setattr` only, never I/O.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()` (either direction):
  none; no queryset in the module.
- `only()` / `defer()` deferred loads: none.
- Unbatched writes (`bulk_create` / `bulk_update`): none; no writes.
- `blog.id` vs `blog_id`: none; no model-instance attribute access.
- Repeated `_meta` walks: none; no `_meta` in the module.
- Repeated settings reads: none on any hot path — `apply` reads
  `upstream_patches_enabled("django")` once per call, and `apply` runs at
  app load (at most a few times per process) plus tests; each read is one
  settings-dict lookup plus validation over at most four mapping names.
- Repeated regex compilation: none; no regex in the module.
- Repeated schema or type lookups per request: none; no lookups, and nothing
  runs per request.
- `lru_cache` on methods (`B019`): none; the module holds no cache.
- Locks, cache reads, re-parses or extra round trips on a per-request path:
  none — there is no per-request path. The one re-parse
  (`inspect.getsource` + `dedent` per `apply`, 50.0 us) is cold; see R2.
- Import-time cost: measured zero via package import (no report row) and
  96.6 us self via `ready()` with `django.test.*` pre-paid by `conf.py`;
  no settings read at import. See R1.
- Allocation in the walk: the walker never touches the module, and the
  teardown path allocates nothing per call (loop, one `isinstance` per
  method, two `==` per connection; 180 ns per teardown over upstream).
  See R3.

## Rejected

- **R1: `ready()` imports the patch module (and `django.test`) in every
  process, including production workers.** Measured 96.6 us once per
  process (`review-20260928T205955-059fe3`), and the `django.test.*`
  half of the worry is pre-paid: the package import already pulls the
  whole test framework through `conf.py`'s `django.test.signals` import,
  so the patch import adds exactly one 96.6 us module. Cold, one-time,
  with no plain fix — skipping the import in production would need a
  reliable "tests will run" signal at `ready()` time, which Django does
  not provide. Plainness wins. Reopens if the module gains import-time
  work or an import no sibling already pays, or if a startup budget
  names this module.
- **R2: re-entrant `apply()` re-validates before the installed-check
  (`inspect.signature` + `getsource` + `dedent`, 50.0 us of the 51.5 us
  re-entrant total; `review-20260928T205807-0b49f2`).** Cold: `ready()`
  fires at most a few times per process, so the lifetime cost is
  ~0.1 ms. Caching the validated source across calls would trade the
  fail-loud drift check's plainness (revalidate-then-install, every
  time) for microseconds nobody observes. Reopens if `apply()` is ever
  called per request or in a tight loop — then validate once and only
  re-validate when the installed descriptor changes.
- **R3: teardown costs 180 ns more than upstream per `tearDownClass`
  (one `isinstance` per method over 4 methods, plus the 54.3 ns
  per-connection read-path discriminator;
  `review-20260928T205807-0b49f2`).** Test-teardown-only, and the
  `isinstance` IS the fix (Trac #37064); removing it reintroduces the
  crash. Hoisting the discriminator to a per-`apply` boolean would save
  ~50 ns per teardown class at the cost of a second cached shape beside
  `_validated_remove_databases_failures_source`. Reopens if the patched
  method ever runs per request (it cannot — it is `SimpleTestCase`
  teardown) or the disallowed-method list grows an order of magnitude
  with teardown dominating suite time.
- **R4: `_is_database_failure` is reachable per request through consumer
  debug middleware that wraps a cursor via `safe_wrap_connection_method`.**
  ~45 ns per call (one `None` check, one `isinstance`;
  `review-20260928T205807-0b49f2`) — the cheapest correct spelling of the
  documented feature, with no package-internal per-request caller.
  Nothing to remove without removing the check. Reopens if the predicate
  gains work beyond the two tests.
- **R5: the concurrent truthful-reads delta (`truth.class_dict` /
  `truth.is_instance` in the capture, validate and installed-check
  paths).** All three sites run at import or `apply` time only — cold,
  inside the measured 96.6 us import and 51.5 us re-entrant `apply`
  totals — and the delta is concurrent work outside this item's fence
  (it predates `ITEM_BASELINE`), so no finding here may touch it.
  Reopens if any of the three functions moves onto a hot path.

No finding carries a Proof line: zero findings means no `Proof` is owed,
and no bench figure moves. The probes stay re-runnable from the commands
in `## Trace` at `review/_django_patches.py/verify-performance-<n>`.

Handoff: Read beyond the trace: `apps.py::ready` (the once-per-process
caller), `conf.py::upstream_patches_enabled` whole (one settings read per
`apply`, mapping validation over at most four names), `testing/_wrap.py`
whole (the only other `_is_database_failure` consumer; no
package-internal per-request caller), `django/test/__init__.py` in the
installed Django 6.1 (the `conf.py` → test-framework chain that makes the
patch import marginal), and the `tests/test_django_patches.py` /
`tests/testing/test_wrap.py` / `tests/test_apps.py` caller census via
search (apply/ready lifecycle, idempotence, self-heal — all cold). Sibling
axis records did not exist when this pass closed, so no cross-axis text
existed to answer; this record places none. Open threads: none on
Performance. The one subtle measurement in the record is the import story:
package import contributes 0 (no report row), `ready()` contributes
96.6 us self, and `django.test.*` is pre-paid by `conf.py` — a verifier
re-running the marginal probe must replay app-loader order (package
first, patch timed) without `django.setup()`, since `setup()` fires
`ready()` and turns the import into a 0.5 us dict hit. Scratch kept under
`docs/review/temp-tests/_django_patches/performance/` (inspect/,
`_django_patches.json`, `probe_cold_costs.py`, `cold_costs.json`,
`probe_import_cost.py`, `import_cost.json`, `probe_import_marginal.py`,
`import_marginal.json`, `importtime.json`); the copy at
`review/_django_patches.py/performance` was never edited (every header
reads `fresh`).

## Verification (Performance)

Step 1: `git diff 8482f9a925f3c073013b20e7ef783e9dc5c1ac3e --
django_strawberry_framework/_django_patches.py
tests/test_django_patches.py tests/testing/test_wrap.py` is byte-identical
to `docs/review/temp-tests/_django_patches/diff/pass-1.diff` (both
`sha256:77d81a7d...899871`); the tree did not move under the pass.

Proof lines: none owed, none run. This record carries zero Proof lines
(zero findings), the Mechanics record holds no `## Cross-axis` section,
and the Comments record's `## Cross-axis` is None — there is no
Performance proof anywhere to execute, at any address.

Worker-2 numbers for this axis: none claimed ("no number moved, no
bench figure touched"), so step 2 reproduces the reviewer's four
figures instead. All four re-ran at
`review/_django_patches.py/verify-performance-1`, cell `default`, copy
slot-2 (synced 2026-09-28T21:23:45Z, never edited — every header reads
`fresh`, shared tree unmoved), package digest
`sha256:c5a2742119d1fc7fdaef99f295304d31bccf3912c32f9448bf8287c508fb789c`.
The digest differs from the reviewer's `c9db5de2...` for the expected
reason: pass 1 changed package prose bytes. Code is identical (triple
`--code-digest` equality below), instruments are identical
(`importtime_report.py` `15f679c9`, `_bench_common.py` `253a3953`),
and the three probe blobs are the reviewer's byte-for-byte
(`e582889d`, `6846616b`, `de611e0a`).

Reproduction (reviewer -> verifier):

- Cold costs, `review-20260928T212345-245c15` (probe by absolute path,
  `--json` under `verify-performance-1/`, Django 6.1,
  connection-feature shape, same 4 disallowed methods, `parity: ok`
  both sides): `_is_database_failure` hit 45.0 -> 41.3 ns, miss
  47.1 -> 46.8 ns; discriminator 54.3 -> 54.8 ns;
  `_validate_upstream_shape` 50.0 -> 51.1 us; re-entrant `apply`
  51.5 -> 52.6 us; patched teardown 1357.8 -> 1362.9 ns vs upstream
  1177.8 -> 1182.8 ns, delta 180.0 -> 180.1 ns. Every figure within
  run noise; the load-bearing delta reproduces to 0.1 ns.
- Import time, `review-20260928T212352-ff6c4b` (`importtime_report.py
  --rounds 5 --top 80`): 69 rows both sides, none for
  `_django_patches`, `testing` or `apps` either side — package-import
  contribution still 0. Package cumulative 178.2 -> 186.4 ms over the
  same 69 modules is cross-session machine drift on modules this item
  cannot touch (the patch module is not among the imported set), not
  an item effect.
- Post-setup import, `review-20260928T212432-a60e56`: 0.5 us median
  both sides (min 0.4 -> 0.5), 0 new modules, `django.test`
  pre-present — exact.
- Marginal import, `review-20260928T212439-dcefcb`: median
  96.6 -> 100.2 us (min 93.4 -> 94.9), exactly 1 new module (the
  patch module itself), zero `django.test` / `django.*` / other
  modules — delta identical, timing within noise.

Item diff read whole through this axis: 7 hunks, all comment or
docstring lines (F1, F2, L1, L2 on the target; F3–F5 pointers in the
two test modules), zero executable lines. Corroborated independently:
`review_inspect.py --code-digest 8482f9a9...:<path> <path>` exits 0
with equal digests on all three files
(`ae7b3d6e...c6009`, `8970b55a...6473815`, `169dd93c...257515`),
matching the digests Worker-2 claimed. A prose-only diff moves no
number — confirmed: every figure above reproduces, and no bench
figure moves.

Attacks on the current state:

- Caller census (`_django_patches` and `_is_database_failure` over
  package, examples, tests): production importers unchanged —
  `apps.py::ready` (function-local import, cold) and
  `testing/_wrap.py` (`_is_database_failure` only; consumer test
  setup, no package-internal per-request caller). All other hits are
  prose citations, the `_PATCH_OWNER` string, the kanban file
  inventory, and tests. No hot caller exists; `Path class: cold`
  stands.
- `_is_database_failure` call sites: only `testing/_wrap.py:144` and
  the target's own teardown loop — R4's "~45 ns, cheapest correct
  spelling" still exhaustive.
- No cardinality, flavor, cell or caller variant can move a number
  the diff cannot change: the teardown loop, discriminator,
  validation and import paths are byte-identical code.

Disputes: none recorded — `## Implementation (Worker-2)` carries
zero `disputed:` lines; nothing to judge.

Failability and test tier: none owed. A prose-only change adds no
test, removes no node, and no gate relies on it; Worker-2's "no
permanent test, no failability" is correct for this axis.

Cells: `default` only. Sharded and pg remain `inapplicable by
construction` — I concur with the reviewer's stated reason (zero
queries, no connection I/O, no alias or dialect read; the teardown
loop's `getattr`/`setattr` touch attributes only). Cells unverified:
none.

Fingerprints (`git hash-object`, live tree as verified): target
`6918a213170ea902386a5845da8c6cd1f901baf2` (equals Worker-2's
after-hash; its before-hash equals this record's `## Trace`
`63f3fa9c...`); `tests/test_django_patches.py`
`6e62c784389b0490e174ae5825d9ebdb9428199a`;
`tests/testing/test_wrap.py`
`6818d96b50e848393592be1a84e84be836545ec01` (both equal Worker-2's
after-hashes); unchanged and equal to this record's `## Trace`:
`apps.py` `8ae1a3a3...`, `conf.py` `ae3de0a3...`, `__init__.py`
`0ef72601...`, `testing/_wrap.py` `0df97813...`,
`testing/__init__.py` `48b45d1b...`, `utils/truth.py`
`d5c96bc8...`, `tests/test_apps.py` `5ca8b62c...`,
`importtime_report.py` `15f679c9...`, `_bench_common.py`
`253a3953...`. Probe copies under `verify-performance-1/` hash
`e582889d...`, `6846616b...`, `de611e0a...`, identical to the
reviewer's.

Scratch: `docs/review/temp-tests/_django_patches/verify-performance-1/`
(three probe copies, four JSON outputs). The copy at
`review/_django_patches.py/verify-performance-1` was never edited.

Handoff: Verification is complete with no new finding: zero proofs
owed, four figures reproduced within noise, prose-only identity
independently confirmed, caller census unchanged, no dispute to
judge, no failability owed, no cell left unverified. The one fact a
later pass must not misread is the package-digest change
(`c9db5de2...` -> `c5a27421...`): it is the pass-1 prose bytes, not a
code change — the three `--code-digest` equalities are the binding
proof. Nothing routes elsewhere; no open thread on Performance.
