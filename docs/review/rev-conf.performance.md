# Review · Performance: `django_strawberry_framework/conf.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=0ec338aef4e12fe5930ce0839d10d93ec3403c6d

Path class: hot — `django_strawberry_framework/conf.py::Settings.__getattr__`
plus `django_strawberry_framework/conf.py::Settings.user_settings` run once
per request through the package views (body-cap reader) and once per
single-parent-spec nested-fetch evaluation (fast-path reader); every other
reader in the module is cold (Trace).

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-conf.md` (skeleton only). Sibling axis records
(`rev-conf.{performance,mechanics,comments}.md`) did not exist when read;
no Handoff or Cross-axis text was therefore available.

Target read whole (570 lines) at blob `ae3de0a3`. The target is dirty vs
HEAD (`git diff HEAD --stat`: 40 insertions, 86 deletions — concurrent
work, reviewed as it stands per the dispatch; no hunk attributed here).

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/conf/performance/inspect/` (json
`docs/review/temp-tests/conf/performance/conf.json`): 17 symbols,
0 Django/ORM markers, 0 per-row leads, 0 hot entry points (+0 reachable),
3 import-time calls (`object()`, `Settings(None)`,
`setting_changed.connect`). Leads only; every discharge below is by trace
or measurement.

Production caller census (search over package, tests, examples) per reader:

- `settings` singleton: no production importer (`from ...conf import
  settings` hits docstrings and tests only). Production reaches it solely
  through the readers' module-global `getattr(settings, KEY, default)`.
- `django_strawberry_framework/conf.py::single_parent_fast_path_setting` —
  HOT, once per fetch evaluation: called by
  `django_strawberry_framework/optimizer/single_parent_fetch.py::_fetch_single_parent_rows`,
  itself called by `_fetch_recognized_rows` on every windowed-prefetch
  queryset evaluation carrying a single-parent spec. Live-read is the
  tested contract (`tests/base/test_conf.py::test_single_parent_fast_path_setting_reads_explicit_values_live`).
- `django_strawberry_framework/conf.py::max_request_body_bytes_setting` —
  HOT, once per request: called by
  `django_strawberry_framework/views.py::_resolved_max_request_body_bytes`
  when the mount passes no explicit value, reached from the boundary
  enforcement `run` calls before anything else on both views (GET
  included). Cold only for mounts passing an explicit value.
- `django_strawberry_framework/conf.py::nested_connection_strategy_setting` —
  cold: read by `django_strawberry_framework/optimizer/nested_fetch.py::resolve_strategy`
  at `None`, called at extension construction (strategy fixed per
  instance) plus the constructor-skipped-subclass fallback in
  `_configuration` (degenerate path; one settings read).
- `django_strawberry_framework/conf.py::testing_endpoint_setting` — cold
  (test-client construction / per test-client call).
- `django_strawberry_framework/conf.py::hide_flat_filters_setting` — cold
  (input-class build time).
- `django_strawberry_framework/conf.py::relay_globalid_strategy_setting` —
  cold (once per finalization; pinned must-not-run-post-finalize in
  `tests/types/test_relay_interfaces.py`).
- `django_strawberry_framework/conf.py::resource_policy_setting`,
  `django_strawberry_framework/conf.py::error_policy_setting` — cold
  (once at schema construction).
- `django_strawberry_framework/conf.py::upstream_patches_enabled` — cold
  (four `apply()` gates at app load).
- `django_strawberry_framework/conf.py::reload_settings`,
  `django_strawberry_framework/conf.py::Settings.reload`,
  `django_strawberry_framework/conf.py::Settings._reload_from_django` —
  cold (test-only signal traffic).

Looks-for discharge:

- N+1 / per-row queries, `len(qs)` / `bool(qs)`, `only()` / `defer()`,
  unbatched writes, `blog.id` vs `blog_id`: none — the module has no ORM
  usage at all (0 markers per inspect; grep for `objects.` / `QuerySet` /
  `_meta` over the target: 0 hits).
- Repeated `_meta` walks, regex compilation, schema/type lookups: none —
  no `re` import, no `_meta`, no registry/schema reference in the module.
- Repeated settings reads: present on the two hot readers; rejected (R1)
  with measured bounds.
- `lru_cache` on methods: none — no `functools` import in the module.
- Locks, cache reads, re-parses, extra round trips on a per-request path:
  none — no locks, no cache backend, no parsing, no network/DB round
  trip; one hot read is one Django `LazySettings` getattr plus one dict
  lookup (plus nested `AttributeError` round-trips when the key is
  absent — R1).
- Import-time cost: none with numbers (below) — no settings read at
  import (`Settings(None)` defers; the signal `connect` reads nothing).
- Allocation in the walk: none — the module owns no walk; the hot path
  allocates nothing per call except the absent-key exceptions (R1). The
  `__getattr__` set-literal guard specifically allocates nothing:
  CPython folds it to a `frozenset` constant (proven in the probe run).

Measurements (address `review/conf.py/performance`, cell default):

- Hot-read probe
  `docs/review/temp-tests/conf/performance/probe_hot_read.py`,
  run `review-20260928T233530-1659fc` (copy fresh, package digest
  `sha256:41e15d13e6b3319ad3be2833eed44c172f16590b77b202838bfc57cc2e52a54c`),
  `timeit` median over 7 x 20000, minimal Django bootstrap, no database:
  fast-path/absent 1369.5 ns, body-cap/absent 1380.4 ns,
  `user_settings.get`/absent 1090.7 ns, `{}.get` floor 25.4 ns,
  fast-path/present 232.2 ns, body-cap/present 236.5 ns,
  fast-path/present-true 234.8 ns; guard-set-folded True.
- Import time `scripts/importtime_report.py --rounds 5`,
  run `review-20260928T233624-5fc277`
  (`docs/review/temp-tests/conf/performance/importtime.json`, same
  package digest): conf self 125 us, cumulative 21676 us (first-time
  children in run order, incl. the `django.test.signals` subtree);
  `utils` 1269/76 us, `utils.truth` 186/186 us, `exceptions` 122/122 us.
  Instrument blob `15f679c9` differs from the cycle baseline's
  `bfce84b9`, so the row compares nothing to the baseline — standalone
  characterization. No `## Bench baseline` figure moves (no finding).

Cells: sharded and pg `inapplicable by construction` — the target
reaches no database, alias, or dialect decision (pure in-memory
settings reads; no ORM import or usage). Default cell measured above.

Fingerprints (`git hash-object`): `django_strawberry_framework/conf.py`
`ae3de0a36e2f7737a2c8350e532cdb761b295bcf` (live, dirty);
`tests/base/test_conf.py`
`55b333eb2fff714365058d0a8651fc3a57c603e3` (whole);
`django_strawberry_framework/optimizer/single_parent_fetch.py`
`e995270af9b213b7f931c03d7dc8f7c084819e1b` (fetch call site);
`django_strawberry_framework/views.py`
`48ee582ecdba41d49beb2434f2a9e0af992d39d4` (request call site);
`django_strawberry_framework/optimizer/nested_fetch.py`
`1678609e8f331dceb173cddea118e9e0bfe72a61` (`resolve_strategy`);
`django_strawberry_framework/optimizer/extension.py`
`39a8739c7e568e89aff030d98d0ba31d9f04371c` (construction site);
`django_strawberry_framework/utils/__init__.py`
`1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee` (import weight);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (eager root).

## Findings

### High

None.

### Medium

None.

### Low

None.

## Rejected

### R1: per-request / per-fetch live settings re-read (~1.37 us absent-key, ~0.23 us present-key)

The two hot readers re-read live on every request / fetch evaluation
instead of caching. Rejected: the live read is the tested contract, not
an accident — `test_single_parent_fast_path_setting_reads_explicit_values_live`
(fetch-time `override_settings` must be observed, never baked into a plan
cache), `test_delattr_clears_stale_cache_and_restores_defaults` (silent
`del` without signal must be noticed on next read), and
`test_django_backed_resync_fails_loud_after_silent_bad_replacement`
every read retries a rejected live shape). Decomposing the absent-key
1.37 us: ~1.09 us is Django's own `LazySettings` absent-key
`AttributeError` inside the per-read live check (unavoidable for ANY live
read of a possibly-absent key — the check IS the live-sync mechanism),
~0.28 us the conf-level `KeyError`-to-`AttributeError` hop. Shaving the
conf hop (e.g. `.get` on the cached dict) would split the eight-reader
family into two shapes for ~280 ns on paths dominated by millisecond
queries — unmeasurable at request level, moving no bench figure.
Trigger: a production profile attributing over ~1% of request or fetch
time to conf reads, or a Django exception-free absent-key read API.

### R2: `upstream_patches_enabled` validates the whole mapping per read

One `dict()` copy plus two loops and a set difference on every call.
Rejected: cold — the only production callers are the four patch-module
`apply()` gates at app load. Trigger: a per-request caller appears.

### R3: `_normalize_user_settings` copies non-`dict` mappings via `dict(value)`

Rejected: runs only at cache (re)build — signal delivery, direct
`reload`, explicit construction — never on the steady-state hot path,
which hits the cached plain `dict` (and the `type(value) is dict` fast
path at build). Trigger: a hot caller passing non-`dict` mappings
repeatedly; none exists.

### R4: conf import cumulative 21.7 ms via the `django.test.signals` subtree

Rejected: one-time process-start (cold) cost; `setting_changed`'s
canonical home is `django.test.signals` (no lighter spelling exists),
and conf's own body is 125 us self with no settings read at import.
Trigger: a package import budget breach attributed to conf self time.

Handoff: Performance review is closed with no findings and four
rejections. The one judgment call a verifier or implementer could
revisit is R1's ~280 ns conf-level exception hop: I read it as
unimplementable (splits the reader family for nothing measurable), but
the probe command re-runs verbatim at the verify address if anyone
wants to re-weigh it. Everything else was discharged by absence (no
ORM, no regex, no functools, no locks in the module) or by cold call
sites. The target was dirty (40+/86- vs HEAD) — a re-review is owed if
the concurrent change lands a new hot reader or touches
`Settings.__getattr__` / `Settings.user_settings`. No Routed gaps, no
cross-axis text placed or owed, no sibling records existed to
cross-check.

## Verification (Performance)

Verify pass 1, address `review/conf.py/verify-performance-1`, item
scratch root `docs/review/temp-tests/conf/`, this pass under
`verify-performance-1/`. Required reading done in order (AGENTS.md,
START.md, REVIEW.md, worker-1.md, the plan incl. its `## Owned
changes`, the artifact, all three axis records with every Handoff and
Cross-axis section) plus the whole live target (577 lines).

Step 1: `git diff
0ec338aef4e12fe5930ce0839d10d93ec3403c6d --
django_strawberry_framework/conf.py tests/base/test_conf.py` hashes
equal to `docs/review/temp-tests/conf/diff/pass-1.diff`
(sha256 `6baebb463903ce27a91002aa444afc0957497cebca2cbf6d004896e2f61703d9`
both sides, `diff` empty). The tree did not move under the pass.

Proof lines: there are none to run. This record carries zero
findings and hence zero Proof lines; the Mechanics record carries no
`## Cross-axis` section at all; the Comments record's `## Cross-axis`
states `None`. Ordering note: the artifact's `## Implementation
(Worker-2)` was read after Step 1 passed but before this inventory
was written down; with zero Proof lines in existence there was
nothing whose verbatim execution the Implementation text could bias.

Numbers reproduced (reviewer instrument, reviewer probe verbatim):

- Hot-read probe (copy of the reviewer's
  `probe_hot_read.py`, `cmp`-identical, at
  `verify-performance-1/probe_hot_read.py`), medians ns/call:

  | case | reviewer `...-1659fc` | after `...-e7469d` | before `...-c9c462` | after `...-c6bc70` |
  |---|---|---|---|---|
  | fast-path/absent | 1369.5 | 2096.0 | 3032.2 | 2823.0 |
  | body-cap/absent | 1380.4 | 2091.0 | 3226.1 | 3037.4 |
  | user_settings.get/absent | 1090.7 | 1623.9 | 2618.9 | 2323.3 |
  | `{}.get` floor | 25.4 | 34.8 | 52.9 | 48.0 |
  | fast-path/present | 232.2 | 314.4 | 472.4 | 476.1 |
  | body-cap/present | 236.5 | 341.1 | 482.2 | 488.9 |
  | fast-path/present-true | 234.8 | 333.5 | 611.9 | 526.1 |
  | guard-set-folded | True | True | True | True |

  Run ids: `review-20260929T001326-e7469d` (after, fresh copy,
  digest `sha256:4e7fd524...`),
  `review-20260929T001725-c9c462` (before: pass-1 conf hunks
  reverse-applied in the copy, digest `sha256:41e15d13...` —
  exactly the reviewer's digest),
  `review-20260929T001736-c6bc70` (re-applied after, digest
  back to `sha256:4e7fd524...`, `cmp` against the shared tree
  identical). The before leg measures the reviewer's own tree
  at 2.2x the reviewer's figures minutes apart; the `{}.get`
  floor — zero package code — moves 25.4 -> 34.8 -> 52.9 ->
  48.0 across the four runs; the two after legs (identical
  tree) differ by 35-50%. Machine drift swallows every delta,
  exactly as the review record warned ("order-of-magnitude
  characterizations, not before/after deltas"). Shape
  preserved throughout: absent/present ~6x, user_settings
  ~0.78 of the fast-path read, guard folded. No number moves
  due to the change.
- Import time (`importtime_report.py --rounds 5 --json
  verify-performance-1/importtime.json`), run
  `review-20260929T001611-05bcce`: instrument ids identical to
  the reviewer's (`importtime_report.py 15f679c9...`,
  `_bench_common.py 253a3953...`), same interpreter and
  platform; package digest differs as it must (after-tree).
  Conf row self/cumulative: reviewer 125 us / 21676 us, verify
  216 us / 38365 us — but every one of the 69 modules plus
  third-party `django` (40.5 -> 71.3 ms), `psycopg`,
  `strawberry` shifted ~1.7x with it (package cumulative
  212392 -> 378741 us). Conf's share is unchanged (self
  0.51% -> 0.46% of package self; cumulative 10.2% -> 10.1%;
  module count 69 = 69). Uniform environmental drift, no
  import-cost regression.

Whole item diff read through this axis (11 hunks: 7 conf.py
code-shape, 3 conf.py prose, 1 test row; hot path class
re-affirmed — the two hot readers' call sites are untouched):

- Import narrowing (`Callable` dropped): def-time only,
  strictly less work (one fewer `IMPORT_FROM` binding); `Any`
  was already imported, zero new imports.
- Comments F1/F2/F3 prose hunks: comment/docstring text only;
  zero runtime effect (`_normalize_user_settings` co_code
  identical, see Attacks).
- Six `-> Any` widenings: annotations, which under PEP 649
  (Python 3.14 here) live in lazy `__annotate__` thunks
  evaluated only on `__annotations__` access; bodies
  untouched, `getattr` pass-through preserved, so R1's
  live-read contract and every Must-not-change oracle stand.
- New test row: test-only; five cold settings reads in the
  package tier, the mandated tier (thin-reader return values
  are unreachable from a real query — concur with Worker-2).

No bench figure moves; no bench re-run is owed for an
annotation-plus-prose change — the bytecode identity below is
stronger than a re-run, which would only re-measure drift.
Rejections R1-R4 stand (R1's ~280 ns hop untouched; R2/R3
cold code untouched; R4 import shape preserved).

Attacks (all passing, recorded, owing nothing):

- A1 bytecode identity (`verify-performance-1/bytecode_identity.py`,
  shared tree, no run id by construction): compiles the
  ITEM_BASELINE blob vs the live file and compares every
  code object. 20 families / 35 objects each side, family
  sets identical; exactly 8 deltas, all def-time-only: the
  module body (import narrowing), the `Settings` class body
  (`LOAD_SMALL_INT 205 -> 210`, the `__firstlineno__` shift
  from the F3 hunk — proven by disassembly diff), and the
  six lazy `__annotate__` thunks (2 co_code + 4 co_names-only,
  exactly the six widened returns). Callable-body deltas:
  NONE. Every per-call instruction stream is identical, so no
  timing experiment can contradict the no-move verdict.
- A2 annotation-reader sweep: `get_type_hints |
  __annotations__ | typing.get_` over
  `django_strawberry_framework/` + `tests/`: 0 hits. No code
  can observe the widened annotations, so the change is
  behavior-invisible as well as cost-invisible.
- A3 interleaved before/after (runs above): after, before,
  after on one copy; before-leg digest equals the reviewer's
  digest; drift dominates with no direction attributable to
  the change; the copy was restored byte-identical (`cmp`
  clean, digest back to `4e7fd524...`).
- A4 guard-fold re-check: the probe's frozenset-const
  assertion prints True on all three verify legs.

Disputes: none. `grep -c disputed docs/review/rev-conf.md`
prints `0`; Worker-2 records no `disputed:` and implemented
every in-scope finding.

Failability / test tier: the annotation change is
runtime-invisible, which means there is no behavior on this
axis a test could pin and no failability proof this axis can
owe — a revert changes no execution, so `expect_failing`
would be `[]` by construction and prove nothing. This axis's
inverse proof is the A1 script (exit 1 if any callable body
moves). The one new test row pins Mechanics behavior
(verbatim pass-through); its failability is the Mechanics
verifier's to judge (Worker-2's prove run
`review-20260929T000559-4b795e`). Tier concur: package tier
is correct for the row.

Cells: sharded and pg `inapplicable by construction` —
concur with the reviewer (pure in-memory settings reads; the
diff adds no import beyond the narrowed one, no ORM, no I/O,
no alias or dialect decision). Default cell measured above.
Cells unverified: none.

Fingerprints (`git hash-object`): conf.py live
`3820c575bfd4e3c384244d1bed460b75d3bb7681` (== Worker-2's
post-edit print); test_conf.py live
`7275af6887559055b90f4d83a088abfcd6c0ff5f` (== Worker-2's);
pass-1.diff `c90e8a93ebd0ac7dd67902d606e138518710d7f4`;
reviewer probe `f27fdfec7e0a755ba08b2244e4745b49fa967a51`;
`scripts/importtime_report.py`
`15f679c9ad736b71215d8ead0733116f56083cef` (== reviewer's
instrument id); rev-conf.md `fc6938cb9703a972023e6183b80d2ba6d3127964`;
rev-conf.performance.md `750a9080dd613ea17fb8d3d5dc4c9becda2267ab`
(pre-verification); rev-conf.mechanics.md
`0e98fff9bbe27b6c82ead7c540dbec6e2b47a8b6`;
rev-conf.comments.md `dee8785d037c7e3df673172019eeb79734d16854`;
review-0_0_15.md `cb20da7e98d0d060ec7f6799527c7e917cab25c1`;
HEAD `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`.

Verdict: `Status: verified`. Performance review was
no-findings; Implement pass 1 applied nothing on this axis
and moved no number on any axis.

Handoff: Verification is closed with no new findings and no
gaps. Everything beyond this record's trace that I read: the
plan's ledger (no row for this target yet — Worker-0 writes
it at closeout), Worker-2's Implementation (whole-diff
claims checked against pass-1.diff line by line), the live
target whole (577 lines), and the sibling records (Mechanics
F1's Must-not-change concurs with R1; Comments Cross-axis is
explicitly None). The judgment call most likely to be
revisited is declining a bench re-run: the bytecode proof
makes a re-run pure drift measurement, but if Worker-0 wants
one anyway the bench baseline table in the plan names the
commands. Open threads: none. The copy at
`review/conf.py/verify-performance-1` (slot-3) was edited
mid-pass (reverse + re-apply) and restored byte-identical;
the next run in it, if any, takes `--fresh` per the flow
rule. Run ids cited: `review-20260929T001326-e7469d`,
`review-20260929T001611-05bcce`,
`review-20260929T001725-c9c462`,
`review-20260929T001736-c6bc70`.
