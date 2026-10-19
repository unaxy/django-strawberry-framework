# Review · Performance: `django_strawberry_framework/auth/mutations.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=8a53fa0958877d9c10e62631deb5b38e2096d539

Path class: hot — the login / logout / register resolver bodies run once per
mutation per request (`django_strawberry_framework/auth/mutations.py::login_mutation`,
`::logout_mutation`, `::register_mutation` fields via
`django_strawberry_framework/auth/mutations.py::_make_auth_field._resolve`
dispatch, plus the shared helpers the read path reuses through
`django_strawberry_framework/auth/queries.py::current_user`); the factories,
`django_strawberry_framework/auth/mutations.py::bind_auth_mutations`, and the
register-rider synthesis are declaration / finalize cold.

## Trace

Read the whole live target (1367 lines, blob `84183c89`; dirty with
concurrent work at read time, `git diff --stat` 84 insertions / 113 deletions
vs HEAD, attributed to other sessions and not graded; blob identical at pass
start and pass end, so the fingerprints below are what was reviewed).
Skeleton `docs/review/rev-auth__mutations.md` read (`Status: reviewing`,
blank Path class); sibling axis records
`rev-auth__mutations.mechanics.md` / `rev-auth__mutations.comments.md`
absent (concurrent run, not yet written), so none of their Handoff or
Cross-axis sections existed to read. Plan `docs/review/review-0_0_15.md` read
including `## Owned changes` (no row names this target; no Routed lead on
this item). Orientation: `review_inspect.py` overview + stripped source under
`<root>/performance/inspect/` (JSON `<root>/performance/mutations.json`): 0
per-row leads, 14 hot entry points (+8 reachable), 2 import-time work items
(both trivial), 13 calls of interest (all cold).

Hot-path map (every caller traced over the package, tests, examples):

- `django_strawberry_framework/auth/mutations.py::_make_auth_field._resolve`
  runs once per auth field per request; it reads
  `django_strawberry_framework/utils/execution_mode.py::async_execution`
  (180 ns, measured) and calls the sync or async body.
- Login:
  `django_strawberry_framework/auth/mutations.py::_login_resolve_body` /
  `::_login_resolve_body_async` open with
  `django_strawberry_framework/auth/mutations.py::_login_authenticate`
  (transport prologue + permission gate + storability preflight + one
  `auth.authenticate`), then the Django or Channels establish step. The async
  Django arm wraps the sync body in exactly one
  `django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`;
  the async Channels arm runs the prologue in one boundary and awaits the
  native establish (no nested bridge).
- Logout:
  `django_strawberry_framework/auth/mutations.py::_logout_resolve_body` /
  `::_logout_resolve_body_async` open with
  `django_strawberry_framework/auth/mutations.py::_logout_prologue`, then the
  Django or Channels teardown under the same one-boundary discipline.
- Register rides
  `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`
  with the password-aware decode / write step pair
  (`django_strawberry_framework/auth/mutations.py::_register_decode_step`,
  `::_register_write_step`).
- The read path reuses this target's helpers:
  `django_strawberry_framework/auth/queries.py::_current_user_resolve_body`
  calls
  `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`
  and the shared gate (actor-not-lookup: the resolver itself issues no
  queryset work).
- Cold: the four factories, `_declare_*`, `_make_permission_holder`,
  `django_strawberry_framework/auth/mutations.py::derive_register_fields`,
  `django_strawberry_framework/auth/mutations.py::_synthesize_register_rider`,
  `django_strawberry_framework/auth/mutations.py::_resolve_user_primary_or_raise`,
  `django_strawberry_framework/auth/mutations.py::bind_auth_mutations`.

Measurements, copy `review/auth/mutations.py/performance`, package digest
`sha256:b09615232d47c288dde033bdab0e9504332ddd3c0388761b776c2039bb811c87`
(tree as it stands; every figure is self-referenced within this digest).
`_bench_common.py` blob `253a3953` matches the plan `## Bench baseline`
instrument; `importtime_report.py` is `15f679c9` (equals gate-2's, differs
from the baseline's `bfce84b9`, so the importtime row compares to nothing
there). Provenance on every run: python 3.14.2, django 6.1,
strawberry-graphql 0.324.0, in-memory SQLite
(`file:dsf-bench-default?mode=memory&cache=shared`).

- `review-20260929T143117-4c3a90` (exit 0):
  `probe_query_counts.py` (probe blob `3aabcaa4`; live `/graphql/` POSTs via
  `django.test.Client` against the migrated in-memory fakeshop schema, each
  operation warmed once on a throwaway client then measured once on a fresh
  client inside `capture_queries`, at `create_users(1)` vs `create_users(2)`
  — 6 vs 12 users): login_ok 12 -> 12, login_bad 1 -> 1, logout_authed
  4 -> 4, logout_anon 0 -> 0, me_authed 2 -> 2, me_anon 0 -> 0,
  register_ok 7 -> 7. Every surface constant; `VERDICT=batched-shape`.
  (Two earlier revisions failed on probe defects — missing `testserver`
  `ALLOWED_HOSTS`, `review-20260929T143013-9b4b8f`, and a warm/measured
  register-username collision, `review-20260929T143045-56b1fe` —
  superseded, not cited.)
- `review-20260929T143133-018e39` (exit 0):
  `probe_hotpath_costs.py` (probe blob `6c00c640`; `timeit` medians, 7
  repeats x 2000 iterations except where noted, on the finalized fakeshop
  schema's real holders): `payload_cls_for` 283.4 ns,
  `payload_object_slot` 478.9 ns, resolve pair 829.0 ns, register
  `wire_name_map` 224.0 ns, post-warm function-local import 177.2 ns (x500),
  `actor_anon` 266.5 ns, `actor_authed` 260.6 ns, `actor_missing` 38.5 ns,
  login preflight pair 164.0 ns, `async_execution` 179.5 ns,
  `request_from_info` 839.5 ns, `classify_transport` 788.5 ns,
  `require_session` (+classify) 829.1 ns, AllowAny `authorize_or_raise`
  970.5 ns (x1000). Every entry under its generous bound (14/14 `ok`).
- `review-20260929T143147-a9760b` (exit 0):
  `importtime_report.py --rounds 5`, JSON
  `<root>/performance/importtime.json`: 69 modules on the package import,
  0 naming `auth` (`review-20260929T143201-2a56af` row inspection,
  `auth_rows= []`).
- `count_queries.py` not run: the session mutations need an HTTP
  request + session + middleware (the prologue rejects anything else), which
  the anonymous `schema.execute_sync` harness cannot provide; the live-Client
  probe above is the query-shape instrument instead, with absolute counts
  plus two-cardinality constancy.

Cells: default measured (both probes use in-memory SQLite by construction).
Sharded and pg are `inapplicable by construction` for every discharged entry:
the target passes no `using`, reads no alias, holds no raw SQL and no
dialect branch (single-row pk / unique-key statements plus Django session
CRUD through the default router — settings carry no `DATABASE_ROUTERS`, so
`shard_b` changes nothing for auth), and every CPU rejection is pure Python
with no database reach. The verifier judges.

Fingerprints (`git hash-object` of every file whose body was read):

- `django_strawberry_framework/auth/mutations.py` 84183c893fdbf258e112ccf6d1cc66f6bc50c513
- `django_strawberry_framework/auth/queries.py` b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9
- `django_strawberry_framework/auth/__init__.py` 2e480818424d4b130e613e3e2da027aaad7144ad
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `django_strawberry_framework/mutations/resolvers.py` c9cff0590157de85bd9374ab85588b00e62080e0
- `django_strawberry_framework/mutations/inputs.py` 840da733f95678be5ea494bb6ab595c8425a1884
- `django_strawberry_framework/mutations/__init__.py` c13283f85f65c7d8864d961489d2a089a9e6b3f7
- `django_strawberry_framework/utils/execution_mode.py` 9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9
- `django_strawberry_framework/utils/querysets.py` 8fc556d582b313e4aed7cddaa15f9a8480d88a46
- `django_strawberry_framework/utils/permissions.py` 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890
- `django_strawberry_framework/utils/write_values.py` 13548c76605ec264cf95e7d10dc6a8bc813b360d
- `django_strawberry_framework/auth/sessions.py` 865d6e704d2df50bcad465ad3005eccb39e8c545
- `django_strawberry_framework/types/relay.py` 4b2a9df59d6dc99270e3aa8ffac397468f7eee1b
- `django_strawberry_framework/utils/truth.py` d5c96bc8d191d3fce0a20140d8e91063bb466ec9
- `django_strawberry_framework/utils/sessions.py` 21041723250de58876d95eaec14e1078a6f16a4f
- `examples/fakeshop/apps/accounts/schema.py` dd2e81b3474e7d0ce8c42eb573642addc579af1b
- `examples/fakeshop/test_query/test_auth_api.py` 17fc9ddb7c31c5ae936795fe524f233b3a1e4304
- `examples/fakeshop/config/schema.py` 303ea2da9df1f8611c02926fd28c59e5ccf9ecac
- `examples/fakeshop/apps/products/services.py` ece9da7a1d5a1ad88f09f42a980c4436972a68a0
- `examples/fakeshop/config/settings.py` e2ba51142ef2921163a7d3b8a880ed109df4e3a8
- `scripts/_bench_common.py` 253a39533f35b94f6afb7a1167c2c38489bbbbef
- `scripts/count_queries.py` a34e186595aa9d4899e3a63f843b4666d469da8e
- `scripts/importtime_report.py` 15f679c9ad736b71215d8ead0733116f56083cef
- `tests/auth/test_mutations.py` ff8a261d09ca63a0f606673bf11b9262f2bb1f35
- `tests/auth/test_queries.py` 86fa35e3659ff838ac61a7bf5f9df6878f9bad2a
- `docs/review/rev-auth__mutations.md` 0d96992a3beaa129f3310d388a01425f7c20b4fd

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry is `none` with the reason, measured where a number backs it.
Static negatives below are native-search sweeps over the target (zero
executable hits; the only matches are prose — `cache` in ledger docstrings,
`_mutation_meta` attribute names, the `ValidationError` import).

- N+1 and per-row queries: none, measured. Seven live surfaces constant at
  6 -> 12 users (`review-20260929T143117-4c3a90`): 12/1/4/0/2/0/7. The file
  holds one `for` loop (the cold ≤4-entry ledger scan in
  `django_strawberry_framework/auth/mutations.py::_declared_auth_surface`),
  zero `await` inside any loop, zero `.filter(` calls (no prefetch to
  discard), and the register write is one INSERT + one by-pk refetch. The
  `me` resolver issues no queryset work by rule (actor-not-lookup) and
  measures 0 queries anonymous.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. Zero hits for
  all four spellings; the target holds no queryset at all.
- `only()` / `defer()`: none. Zero hits; no queryset columns to defer.
- Unbatched writes where `bulk_create` / `bulk_update` fit: none. The only
  row write is the single-user register INSERT (plus Django's own session /
  `last_login` writes); no batch shape exists.
- `blog.id` vs `blog_id`: none. Zero FK-attribute reads (no `.objects`, no
  `_id` attr, no model attribute access on any hot path).
- Repeated `_meta` walks: none. Zero `_meta` hits. The per-request
  `payload_object_slot` -> `implements_relay_node` ->
  `truth.is_subclass` MRO check measures 478.9 ns
  (`review-20260929T143133-018e39`); caching it is R1.
- Repeated settings reads: none on the served paths. Zero `settings` hits
  in the target. The one reachable settings read,
  `logout_supported` -> `uses_signed_cookie_sessions` ->
  `session_store_class` (`settings.SESSION_ENGINE` + `import_string`),
  fires only on a Channels-WebSocket logout (other transports return before
  it) and must read at call time for `override_settings`; R7.
- Repeated regex compilation: none. Zero `re.` hits.
- Repeated schema or type lookups per request: none rising to a finding.
  `payload_cls_for` (283.4 ns, one `getattr` on the materialized inputs
  module) + `payload_object_slot` (478.9 ns) run once per login / logout;
  both match the shared pipeline's documented recompute choice (R1). No
  `get_user_model()` on any hot path (declaration and bind only).
- `lru_cache` on methods: none. Zero hits; the only memo is the cold
  declaration ledger.
- Locks: none removable. One `scope_session_lock` acquisition per Channels
  login / logout (plus the documented outer/inner actor lease in logout);
  the Django HTTP path holds no lock. R6.
- Cache reads: none. Zero cache hits outside ledger-cache prose.
- Re-parses: none. No document parsing, no plan-cache touch.
- Extra round trips on the per-request path: none beyond one justified
  duplicate. Login persists the session twice (explicit `save()` for
  fail-before-payload durability, then middleware for the rotated cookie);
  the pair is the documented durability + cookie-emission tradeoff (R5).
  Everything else is inherent single-row Django session semantics, and the
  anonymous logout / `me` paths measure 0 queries.
- Import-time cost: none, measured. The package root never imports auth
  (structural opt-in in `django_strawberry_framework/auth/__init__.py`):
  0 of 69 `importtime_report.py` rows name `auth`
  (`review-20260929T143147-a9760b`). The auth import itself reads no
  settings, pulls no channels/asgiref (both function-local), and runs only
  ledger construction + one `register_subsystem_clear`.
- Allocation in the walk: none. The target is not the optimizer walk and
  holds no hot loop; per-request allocations are one small gate-data dict,
  tuples, and the payload object itself — all inherent. No throwaway list /
  dict rebuild / string building in any loop; every f-string, `join`, and
  comprehension sits on a cold or raising path.

## Rejected

- R1: stash the payload class / object slot on the holder at bind instead of
  recomputing `payload_cls_for` + `payload_object_slot` per login / logout
  (829.0 ns measured). Rejected: the shared pipeline
  (`django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync`)
  recomputes the identical pair per request for every mutation by documented
  choice (`build_payload` "recomputed, never re-derived"), so an auth-only
  cache splits one rule into two owners to save 0.002% of a
  hash-plus-12-query login — below any bench spread, unpinnable except by a
  white-box timing test. Trigger: the shared pipeline memoizes the pair per
  class; the auth prologues ride the same seam.
- R2: hoist `_build_wire_name_map` out of the register `write_step` (224.0 ns
  per register). Rejected: the standard model pipeline
  (`django_strawberry_framework/mutations/resolvers.py::_run_pipeline_sync`)
  builds the same map in the same position per request; the rider matches it
  exactly, and the owner of any change is that pipeline, not this item.
  Trigger: the shared pipeline hoists or caches the map; the rider inherits.
- R3: hoist the function-local `from ..mutations import resolvers` (and
  `write_values` / `errors`) imports to module top (177.2 ns each post-warm,
  2–3 per operation). Rejected: no cycle exists (verified: nothing under
  `mutations/`, `optimizer/extension.py`, `relay.py`, or
  `resource_policy.py` imports the auth package), but `resolvers` drags the
  optimizer / relay / resource-policy closure into the opt-in auth import;
  hoisting trades cold import weight for hot nanoseconds — the wrong
  direction under the hot-path trade rule. The `channels` / `asgiref`
  lazies additionally guard a soft dependency and a mount-it-yourself rare
  path. Trigger: the per-request import cost appears in a measured profile
  with the hash and DB work factored out.
- R4: reuse the event-loop-resolved request inside the async Channels
  prologues instead of resolving twice (`request_from_info` 839.5 ns x2).
  Rejected: `_login_authenticate` / `_logout_prologue` stay self-contained
  single seams for both sync and async callers; threading a pre-resolved
  request complicates that seam to save under a microsecond beside ~50 ms
  of authenticate-plus-session work. Trigger: request resolution grows past
  low-single-digit microseconds or async Channels login is separately
  reworked.
- R5: drop one of login's two session UPDATEs (explicit `save()` +
  middleware save of identical bytes). Rejected: the explicit save turns a
  store outage into a GraphQL error before any success payload, and the
  middleware save emits the rotated cookie (clearing `modified` would
  suppress the transition that makes the session usable) — durability and
  cookie emission each need one write, and the resolver cannot set the
  cookie itself. Trigger: Django emits the rotated cookie without requiring
  `modified`, or the durability check moves into middleware.
- R6: remove or narrow the per-scope lock / actor lease on Channels
  login / logout. Rejected: the single `scope_session_lock` acquisition is
  the same-scope mutation serialization (security invariant), and logout's
  outer-scope/inner-lease order is the documented acyclic mutual exclusion
  with transport revalidation; the Django path is already lock-free.
  Trigger: lock contention appears in a multiplexed-connection profile.
- R7: cache the signed-cookie-engine answer instead of reading
  `settings.SESSION_ENGINE` + `import_string` per WebSocket logout.
  Rejected: the call-time read honors `override_settings(SESSION_ENGINE=…)`
  by documented contract, non-WebSocket logouts never reach it, and a
  WebSocket logout is rare beside the session teardown it guards. Trigger: a
  settings-change-safe cache exists and WebSocket-logout rate makes ~1 us
  matter.

Handoff: Performance closes no-findings. The file is a thin, already-batched
authenticator: single-row query shapes proven constant across table sizes
(including two zero-query anonymous paths), per-request Python overhead
~4 us against 10–200 ms of hashing plus session DB work, zero package-import
cost by structural opt-in, and every closest candidate either matches the
shared pipeline's documented choice (R1, R2) or trades cold weight for hot
nanoseconds (R3). The `## Bench baseline` rows stand — no figure moves; a
verifier reproduces the two probes at
`review/auth/mutations.py/verify-performance-<n>` (absolute paths in
`## Trace`, expected constancy plus 14/14 bounds `ok`). Open threads: none.
Sibling axis records were absent at review time; if the Mechanics or Comments
passes land findings that touch a resolver body, their verifiers should
re-run `probe_query_counts.py` to confirm the counts above still hold.

## Verify performance

Precondition: the live tree carries exactly the change under grade.
`git diff ITEM_BASELINE -- <3 paths>` is byte-identical to
`docs/review/temp-tests/auth-mutations/diff/pass-1.diff`
(ITEM_DIFF_MATCHES_PASS1); live blobs `auth/mutations.py`
98ae63f1, `tests/auth/test_mutations.py` 4cb49982,
`tests/auth/conftest.py` a5c413ba.

All runs at `review/auth/mutations.py/verify-performance-1`
(slot-3, package digest
`sha256:6b2d9c42a88afa2fdfb82dfc7abb78b083aba7b4005ed7cf5cefd6442d75a092`,
cell default, copy `fresh`, shared unmoved since sync).
Scratch: `docs/review/temp-tests/auth-mutations/verify-performance-1/`
(`hotpath.log`).

### (a) F1 moves no hot-path number — confirmed

The F1 code delta is holder-class construction only, which is
declaration / finalize cold: the `_SealedAuthHolderMeta` class
deleted, the `_make_permission_holder` call-site identifier swapped
to `DjangoMutationMetaclass`, and that one name added to the
already-existing top-level `..mutations.sets` import (no new module
edge — the target already imported that module at top). Every
remaining hunk in `auth/mutations.py` is comment or docstring
(M1, M2, M3, M4, L1 x2); no resolver body, prologue, establish /
teardown arm, or pipeline step carries an executable change, so no
hot-path number can move. Measured:

- Seal nodes `review-20260929T151338-a479d3`: `2 passed`
  (`test_auth_permission_holder_head_is_sealed`,
  `test_sealed_holder_rebind_message_names_the_holder`).
- Query-count probe `review-20260929T151347-a91ea5` (exit 0):
  login_ok 12 -> 12, login_bad 1 -> 1, logout_authed 4 -> 4,
  logout_anon 0 -> 0, me_authed 2 -> 2, me_anon 0 -> 0,
  register_ok 7 -> 7, `VERDICT=batched-shape` — absolutes
  identical to the review figures.
- Hot-path probe `review-20260929T151410-47f0f4` (exit 0): 14/14
  `ok` against the record's bounds (resolve pair 1048.8 ns <
  4000, wire map 263.2 ns, local import 193.1 ns, actor
  307.1 / 308.6 / 42.3 ns, preflight 187.9 ns, async_execution
  202.5 ns, request_from_info 1463.5 ns < 2000, classify 1026.7
  ns, require_session 958.3 ns, AllowAny gate 1168.6 ns).
  Cross-session medians compare nothing; the comparison is the
  verdicts (constancy + bounds), and every one holds.

### (b) No bench row moves, no rejection trigger tripped — confirmed

No bench row moves: the benches measure plan cache, the optimizer
walk, nested fetch, and the package import, while auth is a
structural opt-in (0 of 69 importtime rows at review); the diff
adds no import edge, no hot executable line, and no query, so no
bench-reachable figure can move and no bench rerun is owed. The
`## Bench baseline` rows stand.

R1–R7 stand, trigger by trigger: R1 (no shared-pipeline memo
landed; the resolve pair stays under bound); R2 (wire map still
under bound; the shared pipeline unchanged); R3 (no new
per-request import — the one added name rides the existing
top-level import; post-warm local import 193.1 ns); R4 (request
resolution under bound); R5 (login still measures exactly 12
queries including the durability + cookie-emission UPDATE pair);
R6 (no lock or lease change; logout shapes unchanged); R7 (no
settings cache; the WebSocket-logout predicate untouched).

### (c) Prose edits disturb no Performance claim — confirmed

M1–M6 / L1–L6 state no query count, timing bound, or hot/cold
classification. The two closest: M2's register scoping agrees with
R2's owner statement (register rides the shared pipeline under its
gates' labels), and M4's save-after-flush gloss matches the
measured 4-query logout (no `asave` added — the body is
untouched). L1's Decision-2 pointers, M1's clear-lifecycle
parenthetical, M3's UNSET-`None` handoff, and the M5/M6/L2–L6
test-file prose carry no number. The post-change probe reruns
above are the disturbance check: counts and bounds hold.

Cells judged: default measured (both probes use in-memory SQLite
by construction). Sharded and pg are `inapplicable by
construction`: F1 changes holder-class construction only — no
database, alias, or dialect reach — and the record's reason (no
`using`, no alias read, no raw SQL, no dialect branch; every CPU
entry pure Python) was verified against the diff, which adds no
database reach. Concur.

Handoff: Performance verification is closed: no-findings stands —
F1 is declaration-cold with byte-identical resolver bodies, both
review probes reproduced green at this address (identical query
absolutes, 14/14 bounds ok), all 7 rejections stand with triggers
untripped, no bench row moves, the 12 prose edits disturb no
Performance claim, cells judged. Open threads: none.

Status: verified
