# Review · Performance: `django_strawberry_framework/routers.py`

Status: no-findings
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=eb71162ba7be2797bf4dbdb4e7d24da989e96eed

Path class: cold — every executable line runs at process start (module
import in the consumer's `asgi.py`), at class materialization (the
first `DjangoGraphQLProtocolRouter` symbol access, once per process
outside eviction tests), or at router construction (the `asgi.py`
call site, once per process). Per-connection dispatch is upstream
`ProtocolTypeRouter.__call__` plus wrappers owned elsewhere
(`django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator`,
covered by that item's hot-path record, and channels' own
middleware); this module defines no `__call__`, no resolver, and no
loop. The inspect "hot entry point" on
`django_strawberry_framework/routers.py::_websocket_application` is a
name-match false positive: it is the construction-time injection-seam
selector, called once per `__init__`.

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-routers.md` (skeleton: `Status: reviewing`, blank Path
class). Sibling axis records
(`rev-routers.{performance,mechanics,comments}.md`) did not exist when
read; no Handoff or Cross-axis text was available. The plan's Routed
lead on this item (consumers.py Comments wordings in
`tests/test_routers.py`) is test-file prose — Comments scope, judged
out-of-axis here and left for `rev-routers.comments.md`, which grades
that module whole.

Target read whole (543 lines, blob `e18772f7`). The target is dirty vs
HEAD (`+24/-18` per `git diff --stat` — concurrent work, reviewed as
it stands per the dispatch; no hunk attributed here). The dirty content
is the truthful-reads migration (`describe_value` to `truth.describe`,
`inspect.iscoroutine` to a `types.CoroutineType` check, narrowed
`except` clauses) on construction and raise paths only: no new
hot-path reader, no per-request change. A re-review is owed if
concurrent work lands a per-request caller of any target symbol.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/routers/performance/inspect/` (json
`docs/review/temp-tests/routers/performance/routers.json`): 10
symbols, 0 Django/ORM markers, 0 per-row leads, 1 import-time call
(`threading.Lock`, R6).

Callers traced by `rg` over the package, tests, and examples: no
package module imports routers (the only in-repo importers are
`tests/test_routers.py` and one row in
`tests/mutations/test_write_transaction.py`); the root
`django_strawberry_framework/__init__.py` never imports it (the dotted
import path is the opt-in boundary, so WSGI deployments never pay for
it). Production callers are the consumer's `asgi.py` (import once,
construct once) and nothing else.
`django_strawberry_framework/routers.py::require_channels` has one
production caller,
`django_strawberry_framework/routers.py::_build_router_class_uncached`.
`django_strawberry_framework/consumers.py::resolved_revalidation_window`
and
`django_strawberry_framework/consumers.py::build_revalidating_consumer_class`
are pure construction-time validation/factory (bodies read). The
module-level import chain (`consumers.py`, `utils/sessions.py`)
reaches for stdlib plus already-imported Django/parent-package names
only — no `channels`, pinned by
`tests/test_routers.py::test_consumers_module_imports_with_channels_absent`
and
`tests/test_routers.py::test_routers_module_import_succeeds_without_channels`
(docstrings read).

Measurements, address `review/routers.py/performance`, package digest
`sha256:336177e5...75b2b4` on every run (tree as it stands, not the
plan's bench-baseline digest; every figure is self-referenced and no
before/after exists — no findings). No bench-baseline figure moves:
the plan-cache, walk, and nested-fetch benches never execute routers
code, and the importtime row below is standalone. Provenance on every
run: python 3.14.2, macOS arm64.

- `review-20260929T103407-23e6db`: `probe_import.py` (probe blob
  `1e9398ad`), fresh interpreters in the copy: a plain package import
  leaves both `routers` and `django_strawberry_framework.routers` out
  of `sys.modules` (`False False`), and a fresh `import
  django_strawberry_framework.routers` costs 0.3250 s net of the empty
  interpreter — dominated by the parent-package import the consumer
  already pays.
- `review-20260929T103428-40febf`: `probe_import_delta.py` (probe blob
  `05d887e6`), min-of-5 fresh interpreters each: plain package
  0.3365 s, with routers 0.3326 s, marginal -0.0039 s — the routers
  chain (routers + consumers + sessions bodies) sits below the
  fresh-interpreter noise floor. Corroborated independently by the
  consumers item's 69-module `importtime_report.py` census, in which
  `routers`, `consumers`, and `sessions` are all ABSENT
  (`rev-consumers.performance.md`, run `review-20260929T023116-2e3794`).

Cells: default, sharded, and pg are all `inapplicable by
construction`: the target reaches no database, no alias read, and no
dialect branch — no ORM marker, no `connection` / `using` / router
consultation in executable code (`rg` + 0 inspect markers), and the
record pins no query count. The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/routers.py`
`e18772f76beed8f42cc5bba0d7b9a4e7c7f77bd2` (live, whole, dirty);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (whole, 169 lines);
`django_strawberry_framework/consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (import block,
`resolved_revalidation_window` head,
`build_revalidating_consumer_class` head);
`django_strawberry_framework/utils/imports.py`
`291ecedd30c7d8af9c007758112e867c09d031eb`
(`require_optional_module` body);
`django_strawberry_framework/utils/sessions.py`
`21041723250de58876d95eaec14e1078a6f16a4f` (import block);
`tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (the concurrency pin at
:1526-:1532 and the two channels-absent import pins at :3156-:3214
only).

## Findings

### High

None.

### Medium

None.

### Low

None.

Proof lines: none exist — zero findings, and no sibling record
exists to carry a `## Cross-axis (for Performance)` section.

Looks-for discharge (REVIEW.md "Performance"), each a finding, `none`
with the reason, or a rejection:

- N+1 and per-row queries: none. No ORM call, no `await` in a loop,
  no resolver, no queryset built (0 inspect markers; `rg` for the
  database-shaped vocabulary hits docstrings only).
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none — no
  queryset; the only truthiness reads are `callable(...)` guards at
  construction.
- `only()` / `defer()`: none — no projection exists to narrow.
- Unbatched writes: none — the module issues no writes of any kind.
- `blog.id` vs `blog_id`: none — no model attribute reads.
- Repeated `_meta` walks, settings reads, regex compilation,
  schema/type lookups: no `_meta`, no settings read (`django.conf`
  never imported outside `TYPE_CHECKING`; the one `DJANGO_SETTINGS_MODULE`
  hit is the docstring's `asgi.py` example). `re.compile` runs once
  per router construction (R1); `inspect.signature` + `bind` once
  per factory construction (R2); `importlib.import_module` once per
  class-cache fill (R3); `truth.is_type` / `is_subclass` /
  `callable` once per construction. The schema passes through
  untouched — no schema or type lookup at all.
- `lru_cache` on methods (`B019`): none — no `functools` import, no
  decorator in the module.
- Locks, cache reads, re-parses, extra round trips on a per-request
  path: there is no per-request path in this module. The class-build
  lock is cold-only (R4); the warm class access is one global read
  (R5); no cache backend, no re-parse beyond R1's single eager
  compile, no round trip.
- Import-time cost: none with numbers — the package import never
  reaches this target (`False False`), and the routers chain's
  marginal import sits below the noise floor (-3.9 ms min-of-5
  delta). Module-level work is hint-string interpolation plus one
  `threading.Lock()` (R6).
- Allocation in the hot loop: none — there is no hot loop. Error
  strings (`truth.describe` + f-strings) are built on raise paths
  only; every success path allocates nothing beyond the composed
  wrappers themselves.

## Rejected

- **R1: `re.compile(value)` per router construction (plus Django's
  lazy recompile of the same pattern at the first handshake).** The
  eager compile is the fail-fast contract the validator's docstring
  states (a malformed pattern is a construction error, never a dead
  route), paid once per process in `asgi.py`; the pattern is one
  tiny consumer string. Reopens if router construction ever moves
  onto a per-request path.
- **R2: `inspect.signature(factory)` + `bind(schema=schema)` per
  factory construction.** Once per process, and the pre-bind is the
  no-false-rejection contract (`_factory_application` rejection 1:
  a `TypeError` caught around the call could not be told apart from
  one raised inside a correct factory's body). Reopens on the same
  trigger as R1.
- **R3: `require_channels()` re-runs `importlib.import_module`
  unmemoized.** It runs once per `_ROUTER_CLASS` cache fill — once
  per process outside eviction tests — and the non-memoization is
  the eviction-test contract the docstring states (a cached module
  object would let a stale binding satisfy the guard after
  `sys.modules` eviction). Reopens if class materialization moves
  per-request.
- **R4: the `_ROUTER_CLASS_LOCK` double-checked build.** The lock is
  never touched on the warm path, and the cold path is uncontended
  in every real deployment (one `asgi.py` import); the shape is
  pinned by
  `tests/test_routers.py::test_concurrent_first_class_access_returns_one_cached_class`.
  Reopens on a contended-build profile.
- **R5: module `__getattr__` re-fires on every
  `DjangoGraphQLProtocolRouter` access (never cached into
  globals).** Per-access cost is one string compare plus one warm
  global read (nanoseconds), paid once per `asgi.py` import in
  production — in-package re-resolvers do not exist — and the
  non-caching is the same eviction-test contract as R3. Reopens if
  a per-request caller of the symbol appears.
- **R6: module-level hint interpolation plus `threading.Lock()`.**
  Once per process, and the measured marginal import of the whole
  chain is below the noise floor; the lock object itself is one
  allocation. Reopens if routers ever joins the package-root import
  graph (today it is absent by the opt-in-boundary contract, so no
  WSGI deployment pays it).

Handoff: Performance review is closed with no findings and six
rejections. The judgment calls a verifier could revisit are R1's
double compile (eager here, lazy in Django) and R5's unmemoized
module hook: both were read as contract-load-bearing cold-path costs
(fail-fast validation; eviction-test freshness), and both probes
rerun verbatim at the verify address. Everything else was discharged
by absence (no ORM, no settings, no functools, no hot loop, no
per-request symbol) or by sub-noise-floor measurement. The target
was dirty (+24/-18 vs HEAD, the truthful-reads migration on
construction/raise paths only) — a re-review is owed if concurrent
work lands a per-request caller of any target symbol. No defects;
the plan's Routed lead (test-file prose) was judged out-of-axis and
left for the Comments pass; no cross-axis text placed or owed. No
bench figure moves. Cells unverified: none beyond the stated
inapplicable-by-construction judgments for all three cells
(default/sharded/pg — no database reached).

## Verify performance

No-findings stands. Pass-1 moves no number: the whole
`docs/review/temp-tests/routers/diff/pass-1.diff` is prose in the
one item file. `django_strawberry_framework/routers.py` carries
exactly 8 `@@` hunks (+23/-17): the 2 Comments Mediums (T1 "the
single" scoping across the `_CHANNELS_INSTALL_HINT` comment and the
`require_channels` / `_build_router_class_uncached` docstrings; T2
Django ceiling 6.0 -> 6.1) plus the 5 riding Lows (module
docstring, `_MISSING_DJANGO_APPLICATION_HINT` comment,
`_validated_websocket_url_pattern`, `_factory_application`, and
`DjangoGraphQLProtocolRouter` docstrings). The inverse proof
holds: `review_inspect.py --code-digest
eb71162ba7be2797bf4dbdb4e7d24da989e96eed:django_strawberry_framework/routers.py
django_strawberry_framework/routers.py` exits 0 with two equal
digests (`sha256:38c32db5...`, output under
`docs/review/temp-tests/routers/verify-performance-1/code-digest.txt`),
so production code is identical modulo docstrings and comments. No
bench row moves: the plan-cache, walk, and nested-fetch benches
never execute routers code (review Trace), and identical
executable bytes mean every review figure still measures the same
code — no bench rerun is owed by a prose-only change. The review's
two import probes were not rerun (this dispatch is fully static,
bind no copy); rerun would be vacuous under digest identity.

Disturbance check: live `git diff ITEM_BASELINE --
django_strawberry_framework/routers.py` is byte-identical to
`pass-1.diff` (`diff` clean), the diff pre-image `e18772f7` equals
the review fingerprint and the post-image `299da0f5` equals live
(`git hash-object`
`299da0f541f184ec833e01a4d9c83cc0d7880d15`), and the item-wide
live diff vs ITEM_BASELINE is that one file only — no concurrent
drift in any item file. Both test files are byte-identical to
ITEM_BASELINE (empty `git diff`): `tests/test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` and
`tests/auth/test_mutations.py`
`ff8a261d09ca63a0f606673bf11b9262f2bb1f35`, both equal to the
review fingerprints — the 19 deferred test-file Lows are untouched
as recorded. Whole-diff reading: zero `+` lines hold an
executable statement (`import` / `from` / `def` / `class` / `@` /
`await`: 0 hits); the one broader-pattern hit is a docstring
continuation starting with the word "with". Path class cold
stands.

Rejection triggers re-checked, all six stand: R1 (eager
`re.compile` per construction) and R2 (signature pre-bind per
factory construction) — code unchanged and construction still
once per process, since no per-request caller appeared (importer
census live == ITEM_BASELINE == exactly `tests/test_routers.py`
and `tests/mutations/test_write_transaction.py`; no package
module imports routers, and the remaining live
`DjangoGraphQLProtocolRouter` hits are prose only:
`consumers.py` docstrings :289/:1518, `auth/sessions.py:150`
error string); R3 (unmemoized `require_channels`) — the guard
body and its eviction-test contract are untouched; R4
(double-checked build lock) — untouched; R5 (unmemoized module
`__getattr__`) — its trigger (a per-request caller of the symbol)
has not fired per the census above; R6 (module-level hint
interpolation plus `Lock`) — `django_strawberry_framework/__init__.py`
is byte-identical to the review's whole-read fingerprint
(`0ef72601ecac300ac87ff993af1b04a4f1bc335a`) with zero
"routers" references, so the opt-in boundary holds and no WSGI
deployment pays the chain.

Cross-axis / disputes: none owed — this record carries no
`## Cross-axis` section, the Mechanics record routes only to
Comments, and no disposition is disputed. Test tier /
failability: none owed — prose-only, no test added, no gate
relied on. Cells: concur `inapplicable by construction` for
default, sharded, and pg — the diff carries no query, alias, or
dialect content. Cells unverified: none.

Scratch: `docs/review/temp-tests/routers/verify-performance-1/`
(`code-digest.txt`, `live-diff.txt`,
`importers-live.txt`/`importers-baseline.txt`, identical).

Handoff: Performance verification is closed with no findings, no
disputes, and no routed gaps. The revisitable judgments the
reviewer flagged (R1's double compile, R5's unmemoized hook) were
re-read against the live bytes and the identical census: both
remain contract-load-bearing cold-path costs. Read beyond this
record: the plan incl. `## Owned changes`, the three sibling
records whole, `pass-1.diff` whole, the live target whole. Open
threads: none on this axis.

Status: verified
