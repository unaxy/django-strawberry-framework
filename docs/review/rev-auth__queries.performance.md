# Review · Performance: `django_strawberry_framework/auth/queries.py`

Status: verified
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=f26a7dff116cf2968524bab663453025006e185b

Path class: hot — `django_strawberry_framework/auth/queries.py::_current_user_resolve_body` runs once per `me` field per request (sync directly through the shared dispatch, async inside the one shared `sync_to_async` bridge); the `django_strawberry_framework/auth/queries.py::current_user` factory, the alias-namespace trio construction plus clear row, and the bind-materialized alias are declaration / finalize cold.

## Trace

Required reading, in order: AGENTS.md, START.md, REVIEW.md, worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15 2026-09-28-3, incl. its `## Owned changes`, which holds no row for this target and no Routed lead on this item), `docs/review/rev-auth__queries.md` (skeleton: `Status: reviewing`, blank Path class). Sibling `rev-auth__queries.mechanics.md` read whole with its Handoff (Status `no-findings`; no `## Cross-axis` sections; its re-verified no-cycle note and its R4 actor-before-gate necessity corroborate R1 and R2 below). Sibling `rev-auth__queries.comments.md` did not exist at close (siblings run concurrently); no foreign Handoff or `## Cross-axis (for Performance)` owed. The main artifact carries no Worker-2 sections yet.

Target read whole, all 121 lines, as it stands: blob `b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9`. `git diff ITEM_BASELINE --` the target is empty (0 bytes), so the live tree equals the item baseline and the fingerprints below are the baseline's.

Orientation: `review_inspect.py` overview + stripped source under `docs/review/temp-tests/auth-queries/performance/inspect/` (JSON `docs/review/temp-tests/auth-queries/performance/queries.json`): 0 per-row leads, 1 hot entry point (+0 reachable), 2 import-time work items (the trio call, the clear row), 0 control-flow hotspots, 0 calls of interest. Leads only.

Hot-path map (every caller traced over the package, tests, examples):

- `django_strawberry_framework/auth/mutations.py::_make_auth_field._resolve` runs once per `me` field per request; it reads `django_strawberry_framework/utils/execution_mode.py::async_execution` (158.2 ns, measured) and calls the sync body directly or awaits the async bridge.
- `django_strawberry_framework/auth/queries.py::_current_user_resolve_body` is the sync body (bound via `functools.partial` at declaration): `django_strawberry_framework/utils/permissions.py::request_from_info`, then `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`, then `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` with `instance=actor`, then return. End to end 3323.1 ns anonymous (measured, pure Python, zero queries).
- The async arm is `django_strawberry_framework/auth/mutations.py::_sync_bridged_async_body` around that same body: exactly one `django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary` entry per `me` (pinned by `tests/auth/test_queries.py::test_async_me_dispatch_awaits_the_native_async_body_exactly_once`).
- Cold: `django_strawberry_framework/auth/queries.py::current_user` (ledger-cached holder via `django_strawberry_framework/auth/mutations.py::_declare_fixed_auth_surface`, the partial, the bridge closure, `django_strawberry_framework/mutations/fields.py::_lazy_ref` + `| None`, `django_strawberry_framework/auth/mutations.py::_make_auth_field`), the `django_strawberry_framework/utils/inputs.py::make_input_namespace` trio construction, the `register_subsystem_clear` row, and the bind-materialized alias (resolved once at schema build, never per request).

Measurements, copy `review/auth/queries.py/performance`, package digest `sha256:6b2d9c42a88afa2fdfb82dfc7abb78b083aba7b4005ed7cf5cefd6442d75a092` (tree as it stands; every figure is self-referenced within this digest). `_bench_common.py` blob `253a3953` matches the plan `## Bench baseline` instrument; `importtime_report.py` is `15f679c9` (equals gate-2's, differs from the baseline's `bfce84b9`, so the importtime row compares to nothing there). Provenance on every run: python 3.14.2, django 6.1, strawberry-graphql 0.324.0, in-memory SQLite (`file:dsf-bench-default?mode=memory&cache=shared`).

- `review-20260929T153812-6ef0fe` (exit 0): `probe_query_counts.py` (probe blob `71da5132`; live `/graphql/` POSTs via `django.test.Client` against the migrated in-memory fakeshop schema, each operation warmed once on a throwaway client then measured once on a fresh client inside `capture_queries`, at `create_users(1)` vs `create_users(2)` — 6 vs 12 users): me_authed 2 -> 2 (django_session x1 + auth_user x1, both middleware-lazy single-row loads), me_anon 0 -> 0. `VERDICT=batched-shape`. (Three earlier revisions failed on probe defects — a brace typo in the query string, `review-20260929T153551-b4a82d`, and client construction inside the capture window counting `force_login` writes, `review-20260929T153612-b93ff7` + `review-20260929T153707-0e5ad5` — superseded, not cited.)
- `review-20260929T153828-92545a` (exit 0): `probe_hotpath_costs.py` (probe blob `2cb55efc`; `timeit` medians, 7 repeats x 500–2000 iterations): local_import 149.5 ns, actor_anon 238.9 ns, actor_authed 243.0 ns, actor_missing 32.1 ns, request_from_info 1920.3 ns, gate_allowany 867.3 ns, async_execution 158.2 ns, resolve_body_anon 3323.1 ns. Every entry under its generous bound (8/8 `ok`).
- `review-20260929T153844-7216b6` (exit 0): `importtime_report.py --rounds 5`, JSON `<root>/performance/importtime.json`: 69 modules on the package import, 0 naming `auth` (`review-20260929T153853-7e4df4` row inspection, `auth_rows= []`; `review-20260929T153900-28fe0c` confirms the row key is `module`, so the empty list is not vacuous).
- `count_queries.py` not run: the `me` field needs an HTTP request + session + middleware (anonymous `schema.execute_sync` cannot provide them), so the live-Client probe above is the query-shape instrument instead, with absolute counts plus two-cardinality constancy — the same instrument substitution the verified `auth/mutations.py` Performance pass used.

Cells: default measured (all three instruments use in-memory SQLite by construction). Sharded and pg are `inapplicable by construction` for every discharged entry: the target passes no `using`, reads no alias, holds no raw SQL and no dialect branch (the only SQL in reach is Django's session + user single-row reads through the default router — settings carry no `DATABASE_ROUTERS`, so `shard_b` changes nothing for `me`), and every CPU entry is pure Python with no database reach. The verifier judges.

Verifier reproduction, verbatim at `review/auth/queries.py/verify-performance-<n>` (`<ws>` is `/Users/riordenweber/.t3/worktrees/django-strawberry-framework/dry-0015`, `<root>` is `<ws>/docs/review/temp-tests/auth-queries`):

- `uv run python scripts/workspace.py run review/auth/queries.py/verify-performance-<n> -- python <root>/performance/probe_query_counts.py` — expect exit 0, `VERDICT=batched-shape`, me_authed 2 -> 2, me_anon 0 -> 0. (Append `--verbose` to dump every SQL statement. The probe gates constancy + anonymous-zero and reports the absolute; the absolute 2 is middleware-determined — session SELECT + user SELECT — so a middleware change moves the absolute, not the verdict.)
- `uv run python scripts/workspace.py run review/auth/queries.py/verify-performance-<n> -- python <root>/performance/probe_hotpath_costs.py` — expect exit 0, `BOUNDS 8/8 ok`.
- `uv run python scripts/workspace.py run review/auth/queries.py/verify-performance-<n> -- python scripts/importtime_report.py --rounds 5 --json <root>/verify-performance-<n>/importtime.json`, then `uv run python scripts/workspace.py run review/auth/queries.py/verify-performance-<n> -- python -c "import json; rows = json.load(open('<root>/verify-performance-<n>/importtime.json'))['rows']; names = [r['module'] for r in rows]; print(len(names), [n for n in names if 'auth' in n])"` — expect `69 []`.

Fingerprints (`git hash-object` of every file whose body was read):

- `django_strawberry_framework/auth/queries.py` b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9
- `django_strawberry_framework/auth/__init__.py` 2e480818424d4b130e613e3e2da027aaad7144ad
- `django_strawberry_framework/auth/mutations.py` 98ae63f1965a08d28332ae6e24aa24ea39d9d511
- `django_strawberry_framework/__init__.py` 0ef72601ecac300ac87ff993af1b04a4f1bc335a
- `django_strawberry_framework/mutations/resolvers.py` c9cff0590157de85bd9374ab85588b00e62080e0
- `django_strawberry_framework/mutations/fields.py` 0e4d5ed1c7efbcbb4e70db9162f2ffc85460a699
- `django_strawberry_framework/mutations/sets.py` 21c15c0b92c6046a300bf62b317535af1ab3cd29
- `django_strawberry_framework/mutations/permissions.py` 55e5edf80c601f373c1802d34fc4e497919d17e7
- `django_strawberry_framework/utils/permissions.py` 1c9cfd398e6096e03bda82ba93dfd66a6d2fb890
- `django_strawberry_framework/utils/inputs.py` b5af8255dfa18a2ff423cdd2de211723c5a15590
- `django_strawberry_framework/utils/execution_mode.py` 9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9
- `tests/auth/test_queries.py` 86fa35e3659ff838ac61a7bf5f9df6878f9bad2a
- `examples/fakeshop/test_query/test_auth_api.py` 17fc9ddb7c31c5ae936795fe524f233b3a1e4304
- `examples/fakeshop/graphql_client.py` 3cd94f4b53891e832c29f91230e711833eafa46b
- `examples/fakeshop/apps/products/services.py` ece9da7a1d5a1ad88f09f42a980c4436972a68a0
- `scripts/_bench_common.py` 253a39533f35b94f6afb7a1167c2c38489bbbbef
- `scripts/count_queries.py` a34e186595aa9d4899e3a63f843b4666d469da8e
- `scripts/importtime_report.py` 15f679c9ad736b71215d8ead0733116f56083cef
- `docs/review/rev-auth__mutations.performance.md` b9070df1d9696cb29a586400070af86526d1e169
- `docs/review/rev-auth__queries.mechanics.md` 8fedec8d57c7e84674f736ff77e3a9a6ecd4c01c
- `docs/review/rev-auth__queries.md` 8d7543933322eabb34c40fe7e26a20a396ac8a85
- `docs/review/review-0_0_15.md` 6e02525890bb2de1673a771ef181d56fbe135a74

## Findings

### High

None.

### Medium

None.

### Low

None.

## Looks-for discharge

Every entry is `none` with the reason, measured where a number backs it. Static negatives below are a native-search sweep over the target for loops, `await`, every queryset spelling (`.filter(`, `.get(`, `.create(`, `.save(`, `.update(`, `.delete(`, `objects.`, `.count(`, `.exists(`, `only(`, `defer(`, `bulk_create`, `bulk_update`, `select_related`, `prefetch_related`, `values_list`, `iterator(`, `_id` reads), `_meta`, `settings`, `re.`, `lru_cache`, `cache`, `lock`, `compile(`, thread/pool names: zero executable hits — the only two matches are the word `for` in docstrings (lines 8, 102).

- N+1 and per-row queries: none, measured. `me` is constant at 6 -> 12 users (`review-20260929T153812-6ef0fe`): authed 2 -> 2, anon 0 -> 0. The module is branchless (no `if`, loop or `try` in 121 lines — the Mechanics pass confirms 0 control-flow hotspots), a single root field returning one actor: no loop, no `await` per row, no `.filter(` on any relation, no related-object read anywhere.
- `len(qs)` / `bool(qs)` vs `.count()` / `.exists()`: none. The target holds no queryset at all (sweep: zero hits for every spelling).
- `only()` / `defer()`: none. Zero hits; no queryset columns to defer, and the returned actor is the middleware's own fully-loaded row, never a deferred re-fetch.
- Unbatched writes where `bulk_create` / `bulk_update` fit: none. A read surface: zero writes of any kind.
- `blog.id` vs `blog_id`: none. Zero model-attribute or FK reads on any path (no `_id` attr, no `.objects`, no attribute access on a model instance).
- Repeated `_meta` walks: none. Zero `_meta` hits.
- Repeated settings reads: none. Zero `settings` hits in the target, and no reachable settings read on the `me` path: request resolution, actor classification and the AllowAny gate touch no settings.
- Repeated regex compilation: none. Zero `re.` hits.
- Repeated schema or type lookups per request: none. The `CurrentUserAlias` lazy ref resolves once at schema build; the holder resolves once at declaration (ledger-cached repeat); `get_user_model()` runs at bind in `django_strawberry_framework/auth/mutations.py`, never per request. The per-request gate constructs one holder instance (a trivial zero-arg alloc inside the measured 867.3 ns gate); caching it is R4.
- `lru_cache` on methods: none. Zero hits; the only memo in reach is the cold declaration ledger.
- Locks: none. Zero lock acquisitions on the read path (no scope lock, no lease — the Channels mutual-exclusion machinery guards logins/logouts only).
- Cache reads: none. Zero cache hits.
- Re-parses: none. No document parsing, no plan-cache touch.
- Extra round trips on the per-request path: none beyond the inherent pair. The authed `me` issues exactly the two middleware-lazy single-row SELECTs (session + user, each once, each Django-cached afterwards) and the resolver body itself issues zero SQL — the file holds no queryset and the measured multiset is exactly those two tables. Anonymous is 0. Async adds the one shared bridge (the verified family discipline); sync adds nothing. Shedding the bridge is R5.
- Import-time cost: none, measured. The package root never imports auth (structural opt-in; zero `auth` hits in `django_strawberry_framework/__init__.py`): 0 of 69 `importtime_report.py` rows name `auth` (`review-20260929T153844-7216b6`). The auth import itself reads no settings, runs only ledger construction + closure defs + one `register_subsystem_clear` row, and pulls `django.contrib.auth` only when the consumer opts in — by documented design.
- Allocation in the walk: none. The target is not the optimizer walk and holds no hot loop; the hot body builds no list, dict or string — the only f-string in reach sits on the denial raise path in `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` (exceptional, never allocated on allow).
- Dispatch shape (beyond the list): the per-request indirections are one `async_execution` read (158.2 ns), one `functools.partial` call and one holder construction, all inherent — the end-to-end anonymous body measures 3323.1 ns with nothing left to remove that an owner would accept (R1–R5).

## Rejected

- R1: hoist the function-local `from ..mutations import resolvers` (`django_strawberry_framework/auth/queries.py::_current_user_resolve_body`, 149.5 ns post-warm) to module top. Rejected: `django_strawberry_framework/mutations/resolvers.py` top-level imports drag the optimizer / relay / resource-policy closure (`..optimizer.extension`, `..relay`, `..resource_policy`, `..types.relay`, `..utils.write_transaction`, verified at lines 81–119) into the opt-in auth import; hoisting trades cold import weight for hot nanoseconds — the wrong direction under the hot-path trade rule. The shape matches the five function-local sites in `django_strawberry_framework/auth/mutations.py`, whose verified Performance pass rejected identically, and the Mechanics pass re-verified at this tree that the lazy hides no cycle. Trigger: the per-request import cost appears in a measured profile with the session/user DB work factored out, or the resolvers closure sheds the heavy edges.
- R2: force the lazy user after the gate instead of before it, so a denied request skips the user SELECT. Rejected: the gate's `instance` argument IS the actor — AllowAny ignores it, but any `IsAuthenticated`-style gate keys on it (`tests/auth/test_queries.py::test_gated_me_denies_the_anonymous_caller_with_the_exact_pinned_string` pins the denial on the actor); there is no gate input cheaper than the actor, and the forced load is the row the field returns. Reordering without changing the gate contract (owned by `django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` + `django_strawberry_framework/mutations/permissions.py::run_permission_classes`) is impossible; the Mechanics pass reaches the same verdict (its R4: the read necessarily precedes the gate). Trigger: a gate shape that decides without the actor instance.
- R3: cache `request_from_info` per request (1920.3 ns of shape-sniffing per `me`). Rejected: a single root field per request runs the sniff once — there is no second in-file call to amortize a cache against — and the helper is owned by the `utils/permissions.py` item (shared by the filter / order / mutation seams), not this fence. Trigger: request resolution grows past low-single-digit microseconds in a per-request profile, or a second in-file caller appears.
- R4: pass the holder class through the gate instead of constructing `mutation_cls()` per request. Rejected: the construction is a trivial zero-arg alloc inside the measured 867.3 ns gate, and the instance exists so object-level `check_permission` overrides can hold per-request state (`django_strawberry_framework/mutations/resolvers.py::authorize_or_raise` docstring); the owner is that gate, not this item. Trigger: the shared gate stops constructing per request.
- R5: shed the async `sync_to_async` bridge for `me` with a native async body. Rejected: the bridge is the one-boundary discipline shared with login/logout (verified in `auth/mutations.py` this run); the forced lazy-user ORM touch is sync-only and must run in a sync context, and a native async arm is a transport rework owned by `auth/mutations.py` + `auth/sessions.py`, not a query-shape fix. Trigger: native async session/user loading lands for the auth family.

Handoff: Performance closes no-findings. The file is a branchless, queryset-free read seam: query shape constant across user-table sizes (authed 2 -> 2, both middleware-lazy single-row loads with zero resolver-issued SQL; anon 0 -> 0), end-to-end anonymous body ~3.3 us of inherent dispatch + gate, zero package-import cost by structural opt-in, and the one in-file micro-cost (the 149.5 ns function-local import) stays lazy for the verified cold-weight reason the sibling item already decided. The `## Bench baseline` rows stand — no figure moves: the benches measure plan cache, the optimizer walk, nested fetch and the package import, none of which this target reaches. A verifier reproduces all three instruments verbatim from `## Trace` at `review/auth/queries.py/verify-performance-<n>` (constancy + `BOUNDS 8/8 ok` + `69 []`). Open threads: none. Sibling notes: the Mechanics Handoff (1) (top-level `.mutations` import must stay) is consistent — R1 keeps that import and the lazy `resolvers` import both untouched; its Handoff (3) (a GLOSSARY family-parenthetical nit) is Comments business, recorded there for Worker-0. Sibling axis records were read as present at close (Mechanics whole; Comments absent, concurrent run); if the Comments pass lands prose touching a resolver body, its verifier should re-run `probe_query_counts.py` to confirm the counts above still hold.

## Verify performance

Precondition: the live tree carries exactly the change under grade.
`git diff ITEM_BASELINE -- tests/auth/test_queries.py docs/TREE.md` is
byte-identical to `docs/review/temp-tests/auth-queries/diff/pass-1.diff`
(`diff` exit 0; copy at
`docs/review/temp-tests/auth-queries/verify-performance-1/live-vs-itembaseline.diff`).
Fully static: no workspace copy bound, no run ids.

### (a) No-findings stands — confirmed

The target `django_strawberry_framework/auth/queries.py` is byte-identical
to ITEM_BASELINE: live blob `b036bdac7b83e7144fe4dc0c4ed75dd89a9a1ec9`,
baseline blob identical, `git diff ITEM_BASELINE --` the target is 0 bytes,
and `--code-digest` prints `sha256:27c0662b` on both sides (exit 0). The
pass diff touches only `tests/auth/test_queries.py` (Comments F1 + F2 + L1 +
L2: module-docstring first line, residue paragraph, one helper-docstring
first line, one test rename + docstring) and the two F1 TREE.md render rows
— no production file, no resolver body, no import edge. Every review figure
is therefore unchanged by construction: the query-shape constancy (authed
2 -> 2, anon 0 -> 0), the 8/8 hot-path bounds, and the 69-module / 0-auth
importtime row. The test-file `--code-digest` exit 1 is the F2 def rename
alone; the diff hunk shows the test body untouched, so the async-dispatch
pin keeps its behavior and no Performance Proof (probe scripts, not pytest
nodes) is affected.

No bench row moves: the four `## Bench baseline` instruments measure the
plan cache, the optimizer walk, nested fetch and the package import — none
reaches the target (byte-identical) or a test module / TREE.md (no bench
imports them). No rejection trigger tripped: R1 (no import edge moved; the
lazy `resolvers` import and the top-level `.mutations` import both stand),
R2 (no gate input changed), R3 (no second in-file caller exists; no code
changed at all), R4 (the shared gate untouched), R5 (the bridge discipline
stands — F2's rename to "bridged" vocabulary corroborates it, not a native
async landing). The review Handoff's conditional re-run of
`probe_query_counts.py` is not owed: the Comments pass landed no prose in a
resolver body. The Comments Handoff (1) is answered: this record carries no
`## Cross-axis (for Comments)`. Cells: sharded/pg `inapplicable by
construction` — concurred (target untouched; no alias, `using`, raw SQL or
dialect reach anywhere in the pass).

### (b) Disturbance check — clean

Target clean vs HEAD (`git status` names it nowhere) and vs ITEM_BASELINE
(0 bytes). `tests/auth/test_queries.py` live `a57722d4` and `docs/TREE.md`
live `5c9d6066` match the pass diff's to-indexes exactly — no foreign hunk
in either file. Sibling `rev-auth__queries.mechanics.md` live `8fedec8d`
matches the review fingerprint; the main artifact's drift from `8d754393`
is Worker-0's expected Status/Path-class fill, not item work. No new
defect found on this axis.

Fingerprints: `docs/review/temp-tests/auth-queries/verify-performance-1/fingerprints.txt`.
Open threads: none.

Status: verified
