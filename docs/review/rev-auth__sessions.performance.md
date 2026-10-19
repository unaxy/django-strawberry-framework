# Review · Performance: `django_strawberry_framework/auth/sessions.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=5bdea138317eca79e8727c89022df017e3e73d46

Path class: hot — `django_strawberry_framework/auth/sessions.py::classify_transport`,
`::require_session` and the capability predicates run once per login/logout
mutation per request (twice on the async bodies, which branch on the loop then
re-run the prologue inside the boundary), and
`django_strawberry_framework/auth/sessions.py::scope_session_lock` is acquired
once per Channels login/logout. Frequency is per auth mutation, not per row:
no symbol here runs per resolver row, per connection frame, or per request on
non-auth paths (the `me` resolver never touches this module).

## Trace

Read the whole live target (279 lines, blob `865d6e70`; dirty vs HEAD
+28/-146, concurrent work predating this pass; blob identical at pass start
and pass end, so the fingerprints below are what was reviewed). Skeleton
`docs/review/rev-auth__sessions.md` read (`Status: reviewing`, blank Path
class); sibling axis records `rev-auth__sessions.mechanics.md` /
`rev-auth__sessions.comments.md` absent (concurrent run, not yet written), so
none of their Handoff or Cross-axis sections existed to read. Plan
`docs/review/review-0_0_15.md` read including `## Owned changes` (no row
names this target; no Routed lead on this item). Orientation:
`review_inspect.py` overview + stripped source under `<root>/performance/
inspect/` (JSON `<root>/performance/sessions.json`): 0 per-row leads, 0 hot
entry points by name (the module exports plain helpers, no resolvers), 0
Django/ORM markers, 2 import-time work items (both trivial: one f-string key
plus one frozen dataclass).

Importer census (sole production importer):
`django_strawberry_framework/auth/mutations.py` (`from . import sessions`)
is the only production importer. Executable call sites: the shared prologue
(`django_strawberry_framework/auth/mutations.py::_transport_prologue`:
classify once, capability predicate once, pre-check once per login/logout);
the threaded-transport branches in the sync bodies (no re-classify); the
async loop-branch re-classifies
(`django_strawberry_framework/auth/mutations.py::_login_resolve_body_async`
and `::_logout_resolve_body_async`, which then re-run the full prologue
inside the one sync boundary); one
`django_strawberry_framework/auth/sessions.py::scope_session_lock`
acquisition per Channels login/logout
(`::_channels_http_login_establish`, `::_channels_logout`). The read path
(`me`) calls `_authenticated_actor_or_none` + the gate and never classifies.
`django_strawberry_framework/consumers.py` does not import this module (it
reaches the engine through
`django_strawberry_framework/utils/sessions.py::session_store_class`
directly, by the opt-in-boundary contract both module docstrings state).

Seams followed out of the target:
`django_strawberry_framework/utils/sessions.py::session_store_class`
(call-time `settings.SESSION_ENGINE` read + `import_string`, honors
`override_settings` by documented contract),
`django_strawberry_framework/utils/sessions.py::scope_singleton` /
`::scope_key` (dict get-or-create + one `truth.is_instance`),
`django_strawberry_framework/utils/imports.py::require_optional_module`
(deliberately unmemoized per its docstring, so eviction-simulated absence
tests re-hit the guard),
`django_strawberry_framework/utils/permissions.py::ChannelsRequestAdapter`
(a plain class, not an `HttpRequest` subclass, so the two classifier checks
are order-free; `session` is one `Mapping.get`),
`django_strawberry_framework/utils/lazy.py::unwrap_lazy_object` (one
real-class check, identity for the common non-proxy case).

Measurements, copy `review/auth/sessions.py/performance`, package digest
`sha256:6b2d9c42a88afa2fdfb82dfc7abb78b083aba7b4005ed7cf5cefd6442d75a092`
(tree as it stands; every figure is self-referenced within this digest).
Provenance on every run: python 3.14.2, django 6.1,
strawberry-graphql 0.324.0, default cell (the probe opens no database).

- `review-20260929T160146-8533d0` (exit 1): probe defect (strawberry has no
  `__version__`), superseded, not cited.
- `review-20260929T160157-b97a3c` (exit 0): `probe_hotpath_costs.py` first
  revision, 9/9 `ok` (classify ~708/801/824 ns, require_session 51 ns,
  require_channels warm 249 ns, signed-cookie 2174 ns). Superseded by the
  extended probe below, not cited.
- `review-20260929T160425-8b9320` (exit 0): `probe_hotpath_costs.py`
  (extended revision, probe blob `8cf64d49`; `timeit`
  medians, 7 repeats x 2000 iterations, plus uncontended-lock medians at 7
  x 500): classify_django 707.3 ns, classify_channels_http 822.3 ns,
  classify_channels_ws 813.7 ns, require_session_django 50.4 ns,
  require_channels_warm 250.4 ns, uses_signed_cookie_default 2227.9 ns,
  login_supported 40.7 ns, logout_supported_django 40.0 ns,
  logout_supported_ws_default 2389.6 ns, truth_failed_adapter_check 247.6
  ns, truth_passed_http_check 233.6 ns, scope_lock_helper_per_op 2452.2 ns
  vs bare_lock_per_op 258.9 ns. Every entry under its generous bound
  (13/13 `ok`). A sync Django login pays ~800 ns of boundary CPU; an
  async one ~1.6 us (two classifies); a WebSocket logout adds ~2.2 us —
  all beside 10–200 ms of hashing plus session DB work (the
  `rev-auth__mutations.performance.md` scale, whose classify/require
  figures agree with these to first order on byte-identical target code).
- `count_queries.py` not run: the module reaches no database (zero ORM
  markers; the vocabulary sweep below finds no query spelling), and the
  auth surfaces' live query shapes — login_ok 12, login_bad 1,
  logout_authed 4, logout_anon 0, me 2/0, register_ok 7, every one
  constant across user-table sizes — were already proved batched in the
  verified `rev-auth__mutations.performance.md` probe, which includes
  this module's (zero) contribution.

Cells: default measured (the probe uses fabricated shapes and opens no
database by construction). Sharded and pg are `inapplicable by
construction` for every discharged entry: the target passes no `using`,
reads no alias, holds no raw SQL and no dialect branch (one settings
string read plus `sys.modules` imports), and every CPU entry is pure
Python with no database reach. The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):

- `django_strawberry_framework/auth/sessions.py` 865d6e704d2df50bcad465ad3005eccb39e8c545
- `django_strawberry_framework/auth/mutations.py` 98ae63f1965a08d28332ae6e24aa24ea39d9d511
- `django_strawberry_framework/utils/sessions.py` 21041723250de58876d95eaec14e1078a6f16a4f
- `django_strawberry_framework/utils/imports.py` 291ecedd30c7d8af9c007758112e867c09d031eb
- `django_strawberry_framework/utils/lazy.py` 770f36ae9cc9eec1201e5daece196ed038d758d1
- `django_strawberry_framework/utils/permissions.py` 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890
- `tests/auth/test_sessions.py` b71c84ecd4dc90b9af37518d186716f1d64d9a96
- `docs/review/rev-auth__mutations.performance.md` b9070df1d9696cb29a586400070af86526d1e169
- `docs/review/rev-routers.performance.md` 3350ca5845cb5b5f0ca4cce3213b4f57ac2b4695

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry is `none` with the reason, measured where a number backs it.
The static negatives below are a vocabulary sweep over the target (the only
matches are prose: `for`/`while`/`settings` inside docstrings and comments;
zero executable hits).

- N+1 and per-row queries: none, measured. The module holds no loop, no
  comprehension, and no `await` beside the single uncontended lock
  acquisition; zero queryset spellings (`.filter(`, `.count(`, `.exists(`,
  `bulk_`, `objects.` all absent). The covering live shapes are constant
  (see Trace).
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. The target
  holds no queryset at all.
- `only()` / `defer()`: none. No queryset columns to defer.
- Unbatched writes where `bulk_create` / `bulk_update` fit: none. The only
  write is a dict store (the lazily created scope lock); no row write
  exists.
- `blog.id` vs `blog_id`: none. Zero model attribute reads (no `.objects`,
  no `_id`, no FK traversal on any path).
- Repeated `_meta` walks: none. Zero `_meta` hits.
- Repeated settings reads: none rising above the one documented call-time
  read. `logout_supported` short-circuits non-WebSocket transports to
  `True` (40.0 ns, no settings touch); only a WebSocket logout reaches
  `uses_signed_cookie_sessions` -> `session_store_class`
  (`settings.SESSION_ENGINE` + `import_string`, 2227.9 ns), which must
  read at call time for `override_settings`; R3.
- Repeated regex compilation: none. Zero `re` hits.
- Repeated schema or type lookups per request: none rising to a finding.
  `classify_transport` runs one unwrap plus two real-class checks per call
  (707–824 ns total); the async bodies classify twice per mutation
  (~1.6 us). Threading the classification through is R1; the check order
  is R6.
- `lru_cache` on methods: none. Zero hits; the module holds no memo at
  all.
- Locks: none removable. One `scope_session_lock` acquisition per
  Channels login/logout (2452.2 ns uncontended vs 258.9 ns bare); the
  Django HTTP path holds no lock. R5; the wrapper shape is R7.
- Cache reads: none. Zero cache hits.
- Re-parses: none. No document parsing, no plan-cache touch.
- Extra round trips on the per-request path: none. The module issues no
  I/O: `require_channels()` re-runs `importlib.import_module` per
  Channels mutation (250.4 ns post-warm), an in-process `sys.modules`
  lookup whose non-memoization is the eviction-test contract; R2.
- Import-time cost: none. Module level runs one f-string key, one frozen
  dataclass, the `Transport` enum, and one hint interpolation; no
  settings read, no `channels` import (pinned by
  `tests/auth/test_sessions.py::test_auth_submodule_import_stays_channels_free`,
  a subprocess asserting `channels` absent from `sys.modules` after
  importing `auth` + `auth.sessions`). The package root never imports
  auth (structural opt-in in `auth/__init__.py`, blob unchanged since
  the verified 0-of-69 `importtime_report.py` census), so no bench row
  can move.
- Allocation in the walk: none. The target is not the optimizer walk and
  holds no hot loop; per-call allocations are the returned enum member,
  the pass-through session, and (once per scope, load-bearing) the lock.
  No throwaway list/dict rebuild/string building in any loop; every
  f-string sits on a raising path.

## Rejected

- R1: thread the resolved request + transport from the async bodies into
  `_login_authenticate` / `_logout_prologue` to skip the second
  `request_from_info` + `classify_transport` per async login/logout
  (~800 ns beside ~50 ms of authenticate-plus-session work). Rejected:
  the prologues stay self-contained single seams for both sync and async
  callers, the exact shape the verified `rev-auth__mutations.
  performance.md` R4 upheld for the double resolution; the fix would
  live in that closed item, not this target. Trigger: the async bodies
  are reworked anyway, or `classify_transport` grows past
  low-single-digit microseconds.
- R2: memoize `require_channels()` (or skip the guard when `channels` is
  already in `sys.modules`) instead of re-running
  `importlib.import_module` per Channels mutation (250.4 ns post-warm).
  Rejected: non-memoization is the documented contract
  (`django_strawberry_framework/utils/imports.py::require_optional_module`
  "each call re-runs the import so eviction-simulated absence tests can
  evict `sys.modules` entries and re-hit the guard"), pinned by
  `tests/auth/test_sessions.py::test_classify_channels_scope_without_channels_raises_the_install_hint`
  via the `simulated_absence` eviction discipline; the routers twin drew
  the same verdict (`rev-routers.performance.md` R3). Trigger: the
  eviction discipline gains a guard-reset hook and Channels-mutation
  rate makes ~250 ns matter.
- R3: cache the signed-cookie-engine answer instead of resolving
  `settings.SESSION_ENGINE` + `import_string` per WebSocket logout
  (2227.9 ns). Rejected: the call-time read honors
  `override_settings(SESSION_ENGINE=...)` by documented contract
  (`django_strawberry_framework/utils/sessions.py::session_store_class`
  docstring), pinned by three override tests in the own test module
  (`test_uses_signed_cookie_sessions_true_under_the_signed_cookie_engine`,
  `test_signed_cookie_detection_follows_a_subclassed_engine`,
  `test_logout_unsupported_on_a_signed_cookie_websocket`);
  non-WebSocket logouts never reach it, and a WebSocket logout is rare
  beside the session teardown it guards. Trigger: a settings-change-safe
  cache exists and WebSocket-logout rate makes ~2 us matter.
- R4: hoist the function-local signed-cookies `SessionStore` import in
  `uses_signed_cookie_sessions` to module top (one post-warm
  `sys.modules` lookup, ~100–200 ns of the 2227.9 ns, per WebSocket
  logout). Rejected: hoisting drags `django.contrib.sessions.backends`
  into the opt-in auth import closure to save hot nanoseconds — cold
  weight for hot noise, the wrong direction under the hot-path trade
  rule (the `rev-auth__mutations.performance.md` R3 argument). Trigger:
  the per-request import cost appears in a measured profile with the
  session work factored out.
- R5: remove or narrow the per-scope lock acquisition on Channels
  login/logout. Rejected: the single acquisition is the same-scope
  mutation serialization (security invariant 12, pinned by
  `tests/auth/test_sessions.py::test_scope_lock_serializes_two_operations_on_one_scope`
  and `::test_no_process_global_lock_registry_in_the_sessions_module`);
  the Django path is already lock-free. Trigger: lock contention
  appears in a multiplexed-connection profile.
- R6: check `HttpRequest` before `ChannelsRequestAdapter` in
  `classify_transport` so the common Django path skips the failed
  adapter check (247.6 ns saved per Django mutation, 233.6 ns added per
  Channels one; the order is correctness-free since the classes are
  disjoint). Rejected: 248 ns per rare auth mutation is below any bench
  spread and unpinnable except by a white-box timing test, with no
  per-row multiplier to accumulate under (the run-precedent bar from
  `rev-auth__mutations.performance.md` R1, which rejected 829 ns on the
  same ground); the adapter-first order documents the shape this
  boundary exists to handle carefully. Trigger: a profile attributes
  more than 1% of auth-mutation CPU to the failed first check.
- R7: return the scope lock instead of the `@contextlib.asynccontextmanager`
  wrapper (the
  `django_strawberry_framework/utils/sessions.py::actor_lease` shape),
  saving the async-generator build plus two drives per Channels
  mutation (inside the measured 2452.2 ns helper vs 258.9 ns bare
  delta). Rejected: the wrapper also owns the lazy get-or-create plus
  the mutable-scope validation, so the split saves only the wrapper
  fraction of ~2 us beside millisecond-scale native teardown, while
  churning both call sites and the lock tests; the `actor_lease`
  precedent optimizes the per-frame outbound path, where the same
  fraction multiplies per protected frame. Trigger: Channels-auth-
  mutation rate makes sub-microsecond cost matter, or a profile shows
  the wrapper.

Handoff: Performance closes no-findings. The module is a thin, already-
minimal boundary: ~800 ns of CPU per sync auth mutation (~1.6 us async,
+~2 us for a WebSocket logout), zero queries, zero package-import cost by
structural opt-in, and every closest candidate either breaks a pinned
contract (R2 eviction discipline, R3 `override_settings`, R5 invariant
12) or saves unpinnable nanoseconds beside millisecond session work
(R1, R4, R6, R7). The `## Bench baseline` rows stand — no figure moves;
a verifier reproduces the probe at
`review/auth/sessions.py/verify-performance-<n>` via `uv run python
scripts/workspace.py run review/auth/sessions.py/verify-performance-<n>
-- python <abs path>/docs/review/temp-tests/auth-sessions/performance/
probe_hotpath_costs.py` and expects `entries=13 failed=0` (cross-session
medians compare nothing; the comparison is the 13 bounds `ok`). Open
threads: none. Sibling axis records were absent at review time; if the
Mechanics or Comments passes land findings that touch a classifier,
pre-check, lock, or capability body, their verifiers should re-run the
probe to confirm the figures above still hold.

## Verify performance

Pass 1, fully static per dispatch (no workspace copy bound, no run ids).
The record holds no findings and no Proofs, so there is nothing to run;
the verdict rests on change-carried confirmation, prose-only identity,
a whole-diff Performance reading, and the rejection triggers.

Change carried: `git diff <ITEM_BASELINE> --
django_strawberry_framework/auth/sessions.py` is byte-identical to
`<root>/diff/pass-1.diff` (`diff` exit 0; scratch
`docs/review/temp-tests/auth-sessions/verify-performance-1/live-item-diff.diff`).
Live target blob `e50011e6cae837a7b1322d704a7f8adbb69bcec3` matches the
pass-diff header (`865d6e70..e50011e6`). The shared tree carries exactly
the change sent to grade.

Prose-only: `uv run python scripts/review_inspect.py --code-digest
5bdea138317eca79e8727c89022df017e3e73d46:django_strawberry_framework/auth/sessions.py
django_strawberry_framework/auth/sessions.py` exits 0 with two equal
digests (`sha256:d54bef3769a6d4d6004c11cc7dabe61df6b793c3f25947d39e113e6d012faf85`
both sides; output kept at `.../verify-performance-1/code-digest.txt`).
No executable line moved.

Whole-diff reading (all 8 hunks, Performance axis): module docstring
(F1 subpackage scoping, F2 downstream-failure shape), install-hint
comment (F3), lock comment (F5 tense), `classify_transport` docstring
(F6 operand), `require_session` docstring (F2), three predicate first
lines (F7-F9 mood). Zero classifier, pre-check, lock, capability, or
import change; the hot path is textually the same code the 13/13 probe
bounds measured. No new finding. The Handoff's conditional probe
re-run is discharged without running: its trigger was "findings that
touch a ... body", and the digest proves no body was touched (the
Comments record already drew the same conclusion; this is the
mechanical confirmation). The Mechanics Handoff's unmeasured
`logout_supported` engine re-resolution is likewise untouched code,
still once-per-WebSocket-logout, still correctly left alone.

Bench rows: no figure moves. Code-identical output cannot move the
plan-cache, optimizer-walk, or nested-fetch rows, and the importtime
row stands on the structural opt-in the record cites (package root
never imports auth; no import statement changed).

Rejection triggers R1-R7: none tripped. Each trigger needs a code or
workload change that did not happen (async-body rework / guard-reset
hook / settings-safe cache / profiled import cost / lock contention /
>1% CPU attribution / profiled wrapper); every bound figure stands as
measured.

Disturbance check: item scope is exactly one file
(`tests/auth/test_sessions.py` still
`b71c84ecd4dc90b9af37518d186716f1d64d9a96`, untouched). Module first
line unchanged, so no TREE.md render is owed. Since ITEM_BASELINE two
docs outside the fence drifted (`docs/dry/dry-0_0_15.md`,
`docs/review/review-0_0_15.md`; concurrent DRY/plan work, already on
the plan's Drift lines) — no production or test disturbance, nothing
attributed to this item.

No-findings stands.

Status: verified (open threads: none)

Handoff: Performance verify pass 1 closes `verified` on a prose-only
Comments implementation. Everything a re-pass could need is on disk:
the byte-identical live diff and the `--code-digest` output under
`docs/review/temp-tests/auth-sessions/verify-performance-1/`. No
workspace copy was bound, so no copy needs release. If a later pass
ever touches executable code in this target, the Handoff's probe
command in the review section above is the re-measurement starting
point.
