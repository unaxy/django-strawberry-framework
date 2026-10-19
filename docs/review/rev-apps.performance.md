# Review · Performance: `django_strawberry_framework/apps.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=d4ff8d5067f177b771ba3870240d266cdc285f86

## Trace

Target read whole (47 lines, blob `8ae1a3a3`). `git diff <ITEM_BASELINE> --
<target>` is empty and `git diff HEAD -- <target>` is empty, so the tree
reviewed is both the item baseline and HEAD. The plan's `## Owned changes`
holds no row for this target.

Orientation: `review_inspect.py` overview at `<root>/performance/inspect/`
(json `<root>/performance/apps.json`): 1 class, 1 method, 0 hotspots,
0 markers, 0 hot entry points, 0 ORM calls, 0 per-row calls; the only
first-party calls are the four `apply()` dispatches inside
`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready`.

Symbols and every production caller (search census over the package, tests
and examples):

- `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig` —
  instantiated only by Django's app loader (`"django_strawberry_framework"`
  in `INSTALLED_APPS`, `examples/fakeshop/config/settings.py`); the class
  body holds two string attributes. Cold.
- `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` —
  called only by Django's app loader (once per process; some test runners
  fire it more than once) and by `tests/test_apps.py` (4 call sites, all
  cold). Body: four function-local imports plus four `apply()` calls
  (`_django_patches`, `_strawberry_patches`, `_cross_web_patches`,
  `_graphql_core_patches`). Cold.
- No resolver, optimizer, connection, schema-build or request-handling
  module imports or calls the target; the package `__init__` does not
  import it (verified: no `apps` row in the importtime report).

`Path class: cold` — every executable line runs at process start (app-loader
import of the module, `ready()` dispatch) or in tests; nothing runs per
request, resolver, row, connection or outbound message.

Measurements, all in copy `review/apps.py/performance` (slot-2), package
digest `sha256:41e15d13...52a54c` on every run (all three figures compare
with each other; the digest is not the `## Bench baseline` digest, so no
figure is claimed against the baseline table), instruments
`scripts/importtime_report.py` blob `15f679c9`,
`scripts/_bench_common.py` blob `253a3953`:

- `review-20260928T230611-226e47`: `python <root>/performance/probe_ready_cost.py
  <root>/performance/ready_cost.json` (probe blob `74f23ba1`, run by absolute
  path, copy unedited; `config.test_settings`, `django.setup()`).
  `parity: ok` (all four patches installed before and after). timeit medians:
  re-entrant `ready()` 339.4 us (min 228.1 us, 51 repeats — the 4x
  settings-gate + validate + installed-check path with all patches already
  installed); apps-module import after setup 416 ns median (min 333 ns,
  1001 repeats — a `sys.modules` dict hit).
- `review-20260928T230620-a48fda`: `python scripts/importtime_report.py
  --rounds 5 --top 80 --json <root>/performance/importtime.json`: 69 rows,
  none for `apps` or any `_*_patches` module — `import
  django_strawberry_framework` never pulls the AppConfig or any patch
  module, so the target's package-import contribution is 0.
- `review-20260928T230634-3a8842`: `python
  <root>/performance/probe_import_marginal.py
  <root>/performance/import_marginal.json` (probe blob `d2bd4ca1`, median
  of 5 fresh interpreters replaying app-loader order without
  `django.setup()`: package import untimed, apps import timed): 218.6 us
  median (min 196.1 us), exactly 1 new module (the apps module itself;
  `django.apps` pre-paid by the package import). The 2621.8 us first
  iteration is cold-filesystem noise; the median over the remaining four
  (196–257 us) is the figure.

Cells: default only. Sharded and pg are `inapplicable by construction`: the
module runs zero queries, performs no connection I/O, reads no alias and
makes no dialect decision; `count_queries.py` would exit 2 with nothing
comparable measured. No `--cell` run.

Fingerprints (`git hash-object`): `django_strawberry_framework/apps.py`
8ae1a3a3b12f0c9792094959c573ea6fab5d804f;
`django_strawberry_framework/__init__.py`
0ef72601ecac300ac87ff993af1b04a4f1bc335a;
`django_strawberry_framework/conf.py`
ae3de0a36e2f7737a2c8350e532cdb761b295bcf;
`django_strawberry_framework/_django_patches.py`
6918a213170ea902386a5845da8c6cd1f901baf2;
`django_strawberry_framework/_strawberry_patches.py`
90f711fb420b8902434406735c2e367f011e4177;
`django_strawberry_framework/_cross_web_patches.py`
52bf8f5712d632817587f93c4eeb881fd74ffaae;
`django_strawberry_framework/_graphql_core_patches.py`
90ac4f3cc15be1c24dc1f0281206e260d7555cb6;
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
  the module runs zero queries — four `apply()` calls at app load, no ORM.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()` (either direction):
  none; no queryset in the module.
- `only()` / `defer()` deferred loads: none.
- Unbatched writes (`bulk_create` / `bulk_update`): none; no writes.
- `blog.id` vs `blog_id`: none; no model-instance attribute access.
- Repeated `_meta` walks: none; no `_meta` in the module.
- Repeated settings reads: none on any hot path — `ready()` triggers one
  `upstream_patches_enabled` read per `apply()` (4 reads per call, each one
  settings-dict lookup plus validation over at most four mapping names),
  and `ready()` runs at most a few times per process. See R2.
- Repeated regex compilation: none; no regex in the module.
- Repeated schema or type lookups per request: none; no lookups, and nothing
  runs per request.
- `lru_cache` on methods (`B019`): none; the module holds no cache.
- Locks, cache reads, re-parses or extra round trips on a per-request path:
  none — there is no per-request path. The one re-validation cost
  (re-entrant `ready()` 339.4 us across four patch modules) is cold; see R1.
- Import-time cost: measured zero via package import (no report row) and
  218.6 us self once per process via the app loader, with no settings read
  at import (the four patch imports are function-local to `ready()`). See R3.
- Allocation in the walk: the walker never touches the module, and `ready()`
  allocates nothing but four bound-method lookups per call (post-setup
  import 416 ns). See R4.

## Rejected

- **R1: re-entrant `ready()` re-runs all four `apply()` validations
  (339.4 us median, 228.1 us min; `review-20260928T230611-226e47`).**
  Cold: the loader fires `ready()` once per process, test runners a few
  times, so the lifetime cost is ~1 ms. Skipping validation on re-fire
  would trade each patch module's fail-loud drift check
  (revalidate-then-install, every time) for microseconds nobody observes —
  and the check is owned by the patch modules, not this dispatcher. Reopens
  if `ready()` is ever called per request or in a tight loop.
- **R2: `ready()` performs four settings-gate reads per call (one per
  `apply()` via `django_strawberry_framework/conf.py::upstream_patches_enabled`).**
  Each is one settings-dict lookup plus validation over at most four
  mapping names — single-digit microseconds inside the measured 339.4 us
  total, at most a few times per process. Hoisting to one read would couple
  the dispatcher to the gate's per-dependency contract. Reopens if any
  `apply()` moves onto a hot path.
- **R3: the app loader pays a 218.6 us marginal import for the apps module
  itself (`review-20260928T230634-3a8842`), once per process.** Cold,
  one-time, with no plain fix — the import IS the AppConfig registration,
  and the package import itself pays 0 (no report row). Reopens if the
  module gains import-time work beyond the `AppConfig` import, or if a
  startup budget names this module.
- **R4: the first `ready()` eagerly imports all four patch modules (and
  their transitive imports) in every process, including production
  workers.** The eager-import shape is the fail-loud-at-startup contract
  (an unsupported upstream change breaks at boot, not at first request),
  and each patch module's own item owns its import cost (the django patch
  measured 96.6 us self in its item). Lazy-loading would defer the drift
  failure to first use. Reopens if a startup budget names this dispatcher
  or a patch import grows an order of magnitude.

No finding carries a Proof line: zero findings means no `Proof` is owed,
and no bench figure moves. The probes stay re-runnable from the commands
in `## Trace` at `review/apps.py/verify-performance-<n>`.

Handoff: Read beyond the trace: `conf.py::upstream_patches_enabled` whole
(one settings read per `apply`, mapping validation over at most four
names), the four patch modules' `apply`/`_patch_is_installed` entry points
(cold, each owned by its own item), `__init__.py` whole (no `apps` import —
the importtime report confirms it), `examples/fakeshop/config/settings.py`
`INSTALLED_APPS` (the loader pickup), and the `tests/test_apps.py` caller
census via search (`ready()` dispatch contract, re-fire idempotence, reload
recovery — all cold). Sibling axis records did not exist when this pass
closed, so no cross-axis text existed to answer; this record places none.
Open threads: none on Performance. The one subtle measurement is the import
story: package import contributes 0 (no report row), the app loader
contributes 218.6 us self once per process, and post-setup import is a
416 ns dict hit — a verifier re-running the marginal probe must replay
app-loader order without `django.setup()`, since `setup()` fires `ready()`
and turns the import into the dict hit. Scratch kept under
`docs/review/temp-tests/apps/performance/` (inspect/, `apps.json`,
`probe_ready_cost.py`, `ready_cost.json`, `probe_import_marginal.py`,
`import_marginal.json`, `importtime.json`); the copy at
`review/apps.py/performance` was never edited (every header reads `fresh`).

## Verification (Performance)

Step 1: `git diff d4ff8d5067f177b771ba3870240d266cdc285f86 -- tests/test_apps.py
django_strawberry_framework/apps.py` hashes equal to
`docs/review/temp-tests/apps/diff/pass-1.diff` (sha256
`aba74b2ec756b8442902e5adcfa51c5d9796190ad3da447ef8995f23ee1a23ef`
both sides, `diff` empty). The tree did not move under the pass.

Proof lines: none to run. This record carries zero findings and states
no `Proof` is owed; none of the three axis records holds a
`## Cross-axis` section, so no other record holds a Proof for
Performance either. (Step-1 hash check ran before any other read; the
`## Implementation (Worker-2)` text was read before the probe
re-runs below, which is moot with zero verbatim lines to run.)

Numbers reproduced, all at `review/apps.py/verify-performance-1`
(slot-3), package digest
`sha256:41e15d13e6b3319ad3be2833eed44c172f16590b77b202838bfc57cc2e52a54c`
on every run — identical to the reviewer's three runs — instruments
`scripts/importtime_report.py` blob `15f679c9` and
`scripts/_bench_common.py` blob `253a3953`, both identical to the
reviewer's; every header reads `fresh`, shared tree unmoved since sync:

- Ready cost (`review-20260928T232015-0ff706`, same probe + command as
  reviewer `review-20260928T230611-226e47`): parity `ok` before and
  after; re-entrant `ready()` 205.4 us median / 190.7 us min over 51
  repeats (reviewer 339.4 / 228.1); post-setup apps import 334 ns
  median / 292 ns min over 1001 repeats (reviewer 416 / 333). Same
  order, same parity, same conclusion (cold, ~1 ms lifetime); the
  delta is machine drift between sessions on identical code (digest
  identical), not a code move — the item touches no package file.
- Import time (`review-20260928T232041-34f5be`, same command as
  reviewer `review-20260928T230620-a48fda`): 69 rows, zero rows for
  `apps` or any `_*_patches` module — exactly the reviewer's
  "measured zero via package import". Package cumulative 281.2 ms
  vs reviewer 395.5 ms is the same session drift; row count, module
  order and the 0-contribution verdict reproduce.
- Import marginal (`review-20260928T232057-a4ccdb`, same probe +
  command as reviewer `review-20260928T230634-3a8842`): 141.8 us
  median / 138.5 us min, exactly 1 new module (the apps module
  itself; `django.apps` pre-paid). Reviewer 218.6 / 196.1 us, same
  1-module verdict; no cold-filesystem outlier this session. Same
  one-time ~0.2 ms conclusion.

Before figure: none owed (zero findings, no bench figure moves).
Confirmed instead that no figure *can* move: read-only run at
`review/apps.py/before` (`review-20260928T232228-96ef0f`, never
`--fresh`, copy `fresh`) reports the same package digest
`41e15d13...`, and `django_strawberry_framework/apps.py` hashes
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` live and at
ITEM_BASELINE — byte-identical. The digest differs from the plan's
`## Bench baseline` digest because the tree moved since cycle entry;
no figure is claimed against that table, concurring with the reviewer.

Whole-diff reading through Performance: `pass-1.diff` is test-only —
one file (`tests/test_apps.py`, 10+/8-), two hunks (a docstring
paragraph, three fail-message string literals). No production hunk,
no query, no import, no hot-path touch. No number moves; the
reproduced figures above confirm it.

Attacks (all passing, recorded, nothing owed):

- Other caller: no production importer of the apps module (search:
  only `:meth:` docstring mentions in the patch modules, zero
  `from ...apps import`); `ready()` has zero production callers
  (only comment mentions in `conf.py` / `_cross_web_patches.py`
  prose); the 4 test call sites in `tests/test_apps.py` are cold.
  `__init__.py` holds no `apps` reference (importtime report
  confirms: no row).
- Other cell: concur sharded/pg `inapplicable by construction` —
  target holds zero ORM/DB tokens (search over `apps.py` for
  objects/QuerySet/filter/using/connections/alias/dialect/bulk/
  only/defer/_meta/settings/lru_cache/compile: zero hits), runs
  zero queries, reads no alias, makes no dialect decision.
- Import locality: module scope is one `AppConfig` import + two
  string literals; the four patch imports are function-local to
  `ready()`; no settings read at import. The marginal probe's
  1-new-module result pins it.
- Other cardinality/flavor: no queries (no cardinality axis), no
  async surface (Django calls sync `ready()`); `count_queries.py`
  would exit 2 with nothing comparable, so no run.

Disputes: none recorded. Worker-2 disputed zero findings (its one
qualification is explicitly "not a dispute" and Comments-axis).

Test tier / failability: none owed — stated. Zero Performance
findings means no permanent test and no gate; there is no production
hunk to revert, so no `prove` manifest. The F4 literals' single
consumer (fail-message f-string) is Worker-2's Comments-axis evidence,
accepted as read.

Cells unverified: none. Default cell ran (4/4 runs above); sharded
and pg inapplicable by construction, concur.

Scratch: `docs/review/temp-tests/apps/verify-performance-1/` —
`ready_cost.json`, `importtime.json`, `import_marginal.json` (all from
the runs above; probes re-used by absolute path from
`.../performance/`, copies never edited).

Fingerprints (`git hash-object`): `django_strawberry_framework/apps.py`
`8ae1a3a3b12f0c9792094959c573ea6fab5d804f` (unchanged vs reviewer and
ITEM_BASELINE); `tests/test_apps.py`
`fe912987087b560314b04274ffca6ad8a1ca7f02` (matches Worker-2 post-edit);
`scripts/importtime_report.py` `15f679c9...`; `scripts/_bench_common.py`
`253a3953...` (both match reviewer).

Verdict: `verified`. No-findings stands; the test-only change moves no
Performance number.

Handoff: Performance verify is closed with no open threads. Everything
a re-pass would need is above: the three probe commands re-run
verbatim from the review record's Trace at the verify address, and the
before-address digest check is the one-line inverse proof that a
test-only diff moves no bench figure. The ready-cost medians drift
~40% session to session on identical digests, so a future verifier
should compare orders and parity, not absolute microseconds. No
Routed gaps, no cross-axis text placed or owed.
