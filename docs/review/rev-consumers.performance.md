# Review · Performance: `django_strawberry_framework/consumers.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=cf28b509ad848b9219ef23444c4e99cbd19c1fb8

Path class: hot — admission runs once per operation
(`django_strawberry_framework/consumers.py::revalidate_operation_actor`),
the outbound checkpoint once per outbound frame
(`django_strawberry_framework/consumers.py::send_revalidated_operation_frame`
via the generated adapter's `send_json`), the result-source gate once per
subscription event
(`django_strawberry_framework/consumers.py::_stop_aware_results`), and the
Host validator once per handshake
(`django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator`).
The factory, window validation, revocation close attempts, and loop
containment are cold (Trace).

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md,
the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl.
its `## Owned changes`, which holds no row for this target),
`docs/review/rev-consumers.md` (skeleton: `Status: reviewing`, blank Path
class). Sibling axis records
(`rev-consumers.{performance,mechanics,comments}.md`) did not exist when
read and still do not; no Handoff or Cross-axis text was available.

Target read whole (1715 lines, blob `67887b5b`). The target is dirty vs
HEAD (`0c0537e2`: +86/-458 per `git diff --stat` — concurrent work,
reviewed as it stands per the dispatch; no hunk attributed here). A
re-review is owed if the concurrent change lands a new hot-path reader.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/consumers/performance/inspect/` (json
`docs/review/temp-tests/consumers/performance/consumers.json`): 42
symbols, 0 Django/ORM markers, 1 per-row lead (discharged below: upstream
value pull, not a query), 2 hot entry points (+1 reachable), 1
import-time call (`scope_key`, a pure string format).

Hot-path map (callers traced by `rg` over the package plus first-hand
reads of the installed upstream at strawberry-graphql 0.324.0):

- Admission, once per operation:
  `django_strawberry_framework/consumers.py::revalidate_operation_actor`,
  called by the two handler subclasses
  `django_strawberry_framework/consumers.py::build_revalidating_consumer_class`
  generates (`handle_subscribe` / `handle_start`, overriding the upstream
  entry points verified in `subscriptions/protocols/*/handlers.py`).
- Outbound, once per frame: the generated adapter's `send_json`
  override. Verified first-hand: both protocols' `send_message` end at
  `self.websocket.send_json(message)`, and `AsyncBaseHTTPView.run`
  instantiates `self.websocket_adapter_class` by name, so the override
  is the single funnel for `next` / `data` / operation `error`
  (gated via
  `django_strawberry_framework/consumers.py::send_revalidated_operation_frame`)
  and for every control frame (delegated arm under the same lease).
- Per event:
  `django_strawberry_framework/consumers.py::_stop_aware_results`,
  wrapping whatever `schema.stream` (transport-ws, verified) /
  `schema.subscribe` (legacy, verified) returns, installed per handler
  by
  `django_strawberry_framework/consumers.py::_install_stop_aware_schema`.
- Per handshake:
  `django_strawberry_framework/consumers.py::DjangoWebSocketHostValidator.__call__`
  via
  `django_strawberry_framework/consumers.py::_host_validation_request`,
  composed outermost by the router (routers.py:518).
- Cold: `django_strawberry_framework/consumers.py::build_revalidating_consumer_class`
  (once per router class inside the channels guard, routers.py:381),
  `django_strawberry_framework/consumers.py::resolved_revalidation_window`
  (per router construction, routers.py:497, measured 57 ns),
  `django_strawberry_framework/consumers.py::_ConnectionRevocation.close`
  / `::_ConnectionRevocation._attempt_close` (at most 2 attempts per
  connection, only after revocation),
  `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`
  (once per teardown),
  `django_strawberry_framework/consumers.py::_contain_message_loop_failure`
  (only on a loop escape).

Measurements, address `review/consumers.py/performance`, package digest
`sha256:d2021bf2...c6deb` on every run (tree as it stands, not the
plan's bench-baseline digest; every figure is self-referenced and no
before/after exists — no findings). No bench-baseline figure moves: the
plan-cache, walk, and nested-fetch benches never execute consumers code,
and the importtime row below is standalone (instrument id differs from
the baseline's). Provenance on every run: python 3.14.2, macOS arm64.

- `review-20260929T023104-0c19e2`: `probe_hot_costs.py` (probe blob
  `5dd03a20`), timeit median over 7 x 20000 (7 x 2000 for the host and
  cold rows; lease holds 7 x 2000 inside one loop), minimal Django
  settings, no database opened: frame-type test 18.2/19.2 ns (info /
  control); `revoked` 13.4/13.7 ns; `actor_lease` lookup 776.9 ns;
  provenance read 775.2 ns; uncontended lease hold 198.0 ns;
  window-0.0 short-circuit 7.4 ns (no clock read); window-hit check
  82.5 ns; function-local imports 60.9 / 64.5 / 110.1 ns
  (`channels.auth.get_user` / `session_store_class` / the four
  error-policy helpers); `masking_is_active` 119.6 ns;
  `is_maskable_result` (not-a-result) 50.9 ns; `mask_execution_result`
  identity 22.7 / 49.8 ns (`errors=None` / `errors=[]`);
  `schema_error_policy` 69.5 / 83.0 ns (plain / carrying);
  `session_store_class` resolve 1622.1 ns; host projection 2887.9 ns
  (4451.0 ns with `get_host()`); `resolved_revalidation_window` 56.7 ns.
- `review-20260929T022951-575f02`: same probe before the two mask rows
  were added; every shared figure reproduces within noise (lease
  793.5 ns, session-store 1629.5 ns, host 2913.7 ns). An earlier
  revision failed with a probe-side NameError and was fixed before any
  figure was taken; no figure comes from it.
- `review-20260929T023116-2e3794`: `importtime_report.py --rounds 5`
  (`docs/review/temp-tests/consumers/performance/importtime.json`):
  package 69 modules, cumulative 195027 us, self 24213 us;
  `consumers`, `routers`, and `utils.sessions` are all ABSENT from the
  census — a plain package import pays zero for this target.
  Instrument `15f679c9` equals gate-2's and differs from the cycle
  baseline's `bfce84b9`, so the row compares nothing there;
  `_bench_common.py` blob `253a3953` matches the baseline.
- `review-20260929T023305-52a832`: `probe_first_import.py` (probe blob
  `6c1a01d2`), min over 5 fresh interpreters each: plain package
  189963.4 us, with consumers 190108.3 us, marginal 144.9 us — cold,
  once per process, WebSocket deployments only.

Cells: default measured (the probes open no database at all — minimal
in-process settings, in-memory scope dicts). Sharded and pg are
`inapplicable by construction`: no figure involves a query, an alias
read, or a dialect branch, and the record pins no query count; the only
database reads the target triggers (the session + user loads inside
upstream `channels.auth.get_user` on a revalidation miss) are
constant-bounded and upstream-owned, not a shape this review measures.
The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):
`django_strawberry_framework/consumers.py`
`67887b5be1bc80cfc4f051de54d38fde00396ff3` (live, whole, dirty);
`django_strawberry_framework/utils/sessions.py`
`21041723250de58876d95eaec14e1078a6f16a4f` (whole);
`django_strawberry_framework/extensions/error_policy.py`
`a1defd394d8eda9b698964030a09efe6914278db` (whole, 425 lines);
`django_strawberry_framework/routers.py`
`e18772f76beed8f42cc5bba0d7b9a4e4f7f77bd2` (import block + construction
sites at :50-:54, :381, :497, :518);
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a` (exports);
`tests/test_consumers.py`
`7dee4bedeb95c06d8eaf2a8c216c682c3d61541b` (whole, 171 lines);
`tests/test_routers.py`
`36c962b1a3c8ba8c879e7d89c44bfe17b4a31c71` (the channels-absent import
proof at :3208-:3246 only);
`scripts/importtime_report.py`
`15f679c9ad736b71215d8ead0733116f56083cef` and
`scripts/_bench_common.py`
`253a39533f35b94f6afb7a1167c2c38489bbbbef` (instruments, equal to the
run-header ids).

## Findings

### High

None.

### Medium

None.

### Low

None.

Proof lines: none exist — zero findings, and neither sibling record
exists to carry a `## Cross-axis (for Performance)` section.

Looks-for discharge (REVIEW.md "Performance"), each a finding, `none`
with the reason, or a rejection:

- N+1 and per-row queries: none. The one inspect lead (`await anext`
  in `django_strawberry_framework/consumers.py::_stop_aware_results`)
  pulls upstream execution values, never queries. The per-checkpoint
  session + user loads are constant-bounded (at most one store load +
  one user load per miss inside upstream `get_user`, which is already
  `@database_sync_to_async`, so exactly one sync boundary) and zero on
  the anonymous carve-out, on a window hit, and on an idle socket: R1.
  No `await` per row, no `.filter()` on a prefetched relation (the
  module builds no queryset at all).
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none — no
  queryset, no `len` over one (`rg` + 0 inspect markers).
- `only()` / `defer()`: none — the module never narrows a projection.
- Unbatched writes: none — the module issues no writes (scope-dict
  writes only).
- `blog.id` vs `blog_id`: none — no foreign-key dereference.
- Repeated `_meta` walks, settings reads, regex compilation,
  schema/type lookups: no `_meta`, no `re` import. Settings reads:
  `SESSION_ENGINE` per revalidation miss via
  `django_strawberry_framework/utils/sessions.py::session_store_class`
  (1622 ns, R2) and `DEBUG` per subscription event via
  `django_strawberry_framework/extensions/error_policy.py::masking_is_active`
  (120 ns, R3). Schema/type lookups: policy resolved once per
  subscription (70–83 ns, R4); the window attribute is a plain read
  (deliberately not `getattr`-defaulted, per the code comment).
- `lru_cache` on methods (`B019`): none — no `functools` import.
- Locks, cache reads, re-parses, extra round trips on a per-request
  path: the actor lease per frame (lookup 777 ns, uncontended hold
  198 ns, R5); no cache backend, no re-parse, no extra round trip
  (the miss path crosses one sync boundary by delegation, and the
  store is constructed outside it, IO-free).
- Import-time cost: none with numbers — the 69-module census proves a
  plain package import never reaches this target, and its marginal
  first import is 145 us cold with no settings read (R6).
- Allocation in the hot loop: the per-event mask returns its input
  identical (23–50 ns, allocates nothing) unless errors were
  rewritten, in which case the copy is the mechanism; per-frame work
  is one dict get plus a 3-element frozenset test (~19 ns); per-miss
  work is dominated by the two upstream-owned database loads (R7).

## Rejected

- **R1: one session + one user load per revalidation miss (the
  window-0.0 default revalidates every admission and every
  information-bearing frame).** The security contract, not an
  accident: spec-046 Decision 11 as the module docstring states it,
  constant-bounded per checkpoint, with the positive window as the
  lever that removes the read entirely and zero reads on idle,
  anonymous, or revoked-latch paths. No batching exists across
  checkpoints because each checkpoint authorizes a different send.
  Reopens if the contract gains a cheaper validity signal than a
  session + user load.
- **R2: `session_store_class()` re-resolves per miss (1622 ns:
  settings read, truth checks, `import_string`).** The live
  `SESSION_ENGINE` read is the override-honoring contract (its
  docstring: read at call time, never captured), and 1.6 us is noise
  beside the millisecond database loads it precedes on the only path
  that calls it. Reopens if `SESSION_ENGINE` becomes
  immutable-at-startup (then resolve once) or a profile attributes
  miss latency to the resolver itself.
- **R3: `masking_is_active` reads `DEBUG` per event (120 ns) and
  `is_maskable_result` classifies per event (51 ns).** The per-event
  granularity is the documented design (same as the query path's
  teardown read), and the pair totals ~170 ns against a subscription
  event costing microseconds to milliseconds upstream. Reopens on a
  per-event budget breach with masking-gate attribution.
- **R4: `schema_error_policy` per subscription (70–83 ns).** Already
  minimal: resolved once per subscription while the schema outlives
  the socket; per-event work reuses the policy object. Reopens if a
  cheaper call shape appears for the same fail-closed fallback.
- **R5: the actor lease per frame (lookup 777 ns including
  `django_strawberry_framework/utils/sessions.py::scope_singleton`'s
  two function-local imports, uncontended hold 198 ns).** The
  mutual-exclusion guarantee, stated as such on both sides
  (`utils/sessions.py` module docstring: the waiting IS the
  guarantee): validation, revocation transition, and the asynchronous
  send must be one critical section, shared with the auth layer's own
  logout. Hoisting the two imports would save ~120 ns per lookup and
  split the import-light shape of `utils/sessions.py` for nothing a
  profile could see. Reopens on a contended-lease profile — which is
  the documented head-of-line cost, accepted — or a per-frame budget
  breach with lease attribution.
- **R6: function-local imports on hot paths (61–108 ns each).**
  `channels.auth.get_user` + the session-store resolver per miss and
  the four error-policy helpers per subscription stay local because
  the module-level import graph must stay `channels`-free AND
  `strawberry`-free so `routers.py` can import this module above its
  own guard — pinned by
  `tests/test_routers.py::test_consumers_module_imports_with_channels_absent`,
  and the resolver grouping follows the precedent the docstring
  names. The 69-module census confirms the payoff: plain package
  import never touches this file. Reopens if the soft-dependency
  guard moves below this module.
- **R7: Host projection per handshake (2888 ns, 4451 ns with
  `get_host()`).** Once per connection, bounded by the handshake's
  header count (client-small), and every step is Django-semantics
  load-bearing (case normalization, comma-join of duplicates,
  Latin-1 decode, `unknown` reconstruction). Reopens on a
  handshake-flood profile attributing to the projection.
- **R8: post-revocation frames still take the lease (no pre-lease
  revoked fast path).** A latch pre-check would save ~1 us per frame
  pipelined behind a close, but the close-retry path requires the
  lease ("at most one attempt in flight" holds by construction only
  under it), so only a terminal-state bypass would be sound — saving
  one uncontended acquisition, a handful of times, on a connection
  that is already ending, at the cost of a second state read outside
  the machine. Denial stays read-free regardless (no session read).
  Reopens if a hostile client pipelines frames behind a close at a
  rate where acquisition shows in a profile.

Handoff: Performance review is closed with no findings and eight
rejections. The judgment calls a verifier could revisit are R5's ~120
ns import-hop inside the lease lookup and R8's terminal-state bypass:
both were read as unimplementable-for-noise (the former splits an
import-light module, the latter a security state machine), and the
probe reruns verbatim at the verify address if anyone wants to
re-weigh them. Everything else was discharged by absence (no ORM, no
regex, no functools, no locks beyond the one deliberate lease) or by
sub-microsecond measurement against millisecond-dominated paths. The
target was dirty (+86/-458 vs HEAD) — a re-review is owed if the
concurrent change lands new hot-path readers. No defects, no Routed
leads, no cross-axis text placed or owed (sibling records never
appeared); the known Host-denial logging note already lives on the
board and is not re-raised here. No bench figure moves. Cells
unverified: none beyond the stated inapplicable-by-construction
judgments for sharded/pg.

## Verification (Performance)

Address `review/consumers.py/verify-performance-1`, scratch
`docs/review/temp-tests/consumers/verify-performance-1/`.
Item diff `docs/review/temp-tests/consumers/diff/pass-1.diff`.

Step 1 (tree still carries the change): `git diff
cf28b509ad848b9219ef23444c4e99cbd19c1fb8 --
django_strawberry_framework/consumers.py tests/test_routers.py`
hashes `sha256:8f9551da...4273`, equal to the hash of
`pass-1.diff`. Pass; grading proceeds.

Proof lines (expectation-first): none exist. This record holds zero
findings ("Proof lines: none exist"); the Mechanics record's only
`## Cross-axis` section is for Comments (C1, C2); the Comments record
holds no `## Cross-axis` section. Confirmed by grep over all three
records. Nothing to run. Ordering note: the artifact-header read
pulled the first lines of `## Implementation (Worker-2)` before this
empty-Proof declaration was written; no Proof outcome could be
influenced since the runnable set is empty and was established from
the axis records.

Worker-2 numbers for this axis: none reported (pass is prose-only;
"no measurement exists to compare"). Nothing to reproduce there;
instead the reviewer's three measurements were re-run verbatim at the
verify address against the post-change tree:

- Hot costs (`probe_hot_costs.py`, same file, blob `5dd03a20`):
  `review-20260929T030156-01e320`, exit 0, copy fresh. All 22 rows
  reproduce within the reviewer's own inter-run spread: frame
  19.0/18.4 ns (was 18.2/19.2), revoked 13.4/13.4 (was 13.4/13.7),
  lease lookup 813.0 (was 776.9), provenance 791.6 (was 775.2),
  lease hold 179.9 (was 198.0), window 7.3/79.9 (was 7.4/82.5),
  imports 63.6/61.8/97.8 (was 60.9/64.5/110.1), masking 118.0 (was
  119.6), is_maskable 47.8 (was 50.9), mask 22.3/51.3 (was
  22.7/49.8), policy 69.0/80.5 (was 69.5/83.0), session resolve
  1613.2 (was 1622.1), host 2927.8 / 4583.3 with get_host (was
  2887.9 / 4451.0), window-cold 59.7 (was 56.7). Largest move -9%
  (lease hold), inside cross-run noise; no number moves.
- Import census (`importtime_report.py --rounds 5`):
  `review-20260929T030216-034efb`, exit 0, JSON under the verify
  scratch dir. Instrument ids identical to the reviewer's
  (`15f679c9` / `253a3953`), so the rows compare: 69 modules both
  sides, `consumers` / `routers` / `sessions` all ABSENT both sides
  — the plain-import zero-cost claim holds after the change.
  Package cumulative 195027 -> 201468 us (+3.3%) is cross-run drift
  on a shared box; unattributable to this item since both changed
  files sit outside the measured import graph.
- First import (`probe_first_import.py`, blob `6c1a01d2`):
  `review-20260929T030244-b852a8`, exit 0. Marginal -620.8 us vs
  the reviewer's +144.9 us: the signal (one module's docstring
  parse) sits below the fresh-interpreter noise floor (~1 ms on a
  ~191 ms base), so the sign flip is expected. The load-bearing
  claim — cold, once per process, sub-millisecond, WebSocket
  deployments only — stands on either reading.

Package digest differs from the review pass (`c8c86495...` vs
`d2021bf2...`): expected, since the digest covers docstring bytes
the pass changed. Comparability binds on `--code-digest` identity
instead, re-run here in the shared tree, exit 0, digests equal
both sides and matching Worker-2's report (`consumers.py`
`cf167fe8...48afe`, `test_routers.py` `a7be3a89...439`): the diff
moved no executable code, so no Performance number can move and no
bench-baseline figure moves (the benches never execute consumers
code, per the review record).

Whole-diff reading (12 `@@` hunks, 44+/37-): every hunk is
docstring or `#`-comment text in the two item files; no `+` line
holds an executable statement (`import` / `from` / `def` / `class` /
`@` / `await`: zero hits), and no import line was added or removed
(the two `import` grep hits are the prose word "import-time").
Path class hot stands; R1-R8 stand (no body they reason about
changed).

Attacks, all passing, no new finding:

- A1: executable-statement scan over every `+` line — none.
- A2: import-line scan over the diff — only prose "import-time".
- A3: new-hot-path-reader census (the reviewer's re-review
  trigger). Outside `consumers.py` and its two test modules, the
  only references to the four hot symbols are the four
  pre-existing `DjangoWebSocketHostValidator` lines in
  `routers.py` (:52, :127, :141, :518) — byte-identical now and at
  ITEM_BASELINE. The trigger has not fired.
- A4: import census re-run (above) — target still absent.

Disputes: none recorded (`grep -c disputed` on the main artifact
hits only "zero disputed" / "nothing disputed or blocked").
Nothing to judge.

Test tier / failability: none owed — no code changed, no test added,
no gate relied on. No `prove` run exists or is required.

Cells: default measured (all three probes open no database);
sharded and pg remain inapplicable by construction — concur, since
the diff carries no query, alias, or dialect content. Cells
unverified: none.

Fingerprints: `consumers.py`
`0791c04a6c7b2619562f33dc707b002cde718c6b` (= Worker-2's
post-edit value), `test_routers.py`
`f513d869c78247d103a2e52d32b053d98ddc1f0d` (same),
`probe_hot_costs.py` `5dd03a20...` and `probe_first_import.py`
`6c1a01d2...` (equal the reviewer's probe blobs).

Verdict: verified. The prose-only pass moves no Performance number;
every reviewer figure reproduces within noise, the import-graph
claims still hold, and no new hot-path reader exists.

Handoff: Performance verification is closed with no findings, no
disputes, and no routed gaps. The only judgment call is the
first-import sign flip (-620.8 us vs +144.9 us), read as
below-noise-floor agreement rather than a regression — a future
reader wanting a tighter marginal should interleave before/after on
one copy pair instead of comparing min-of-5 across sessions. The
reviewer's re-review trigger (new hot-path readers from concurrent
work) was checked directly and has not fired as of this pass.
