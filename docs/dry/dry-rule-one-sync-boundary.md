# DRY review: `one-sync-boundary`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Rule: ORM work on an async path runs inside exactly one
`sync_to_async(thread_sensitive=True)` worker per operation, with no awaits
interleaved with the ORM inside a transaction. Provisional owner
[querysets.py][querysets]`::run_in_one_sync_boundary`, confirmed below.

What the owner is: a one-line generic primitive (spec-040 D17) —
`await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)` — living on
the cycle-safe utils substrate so read-side (`filters/`, `orders/`, root
[permissions.py][permissions]) and write-side (`mutations/`, `forms/`,
`rest_framework/`, `auth/`) modules reuse it without a root-into-subpackage
import. It opens no transaction and carries no alias itself; transactions live
in callers (the write skeleton's `atomic()` inside the sync body;
[schema.py][schema]`::_execute_mutation_field_async`'s window across hops).
`SyncMisuseError` guards still fire inside `fn` because a worker is itself a
sync context.

Sweep method (whole package, token-based, closed population): every
`run_in_one_sync_boundary(` call site plus every hand-rolled `sync_to_async(`
wrapping ORM work. `sync_to_async` is imported at exactly three package
modules (pre-change): [querysets.py][querysets] (the owner),
[type-resolvers.py][type-resolvers] (three lazy-relation fetches), and
[testing-client.py][testing-client] (two test-harness session writes).
`database_sync_to_async` reaches the package only through channels
(`consumers.py::_refreshed_actor` via `channels.auth.get_user`;
`auth/mutations.py` login/logout via `channels.auth.login`/`logout`
callables); `async_to_sync` reaches it only as two function-local bridges in
`auth/mutations.py` sync bodies (the plan's one permitted sync-to-async hop
per transport). No other bridge token exists in the package.

## Verification

### Matrix

Each axis discharged for the family as a whole.

1. **Cross-flavor policy mirroring.** Model / form / serializer write flavors
   share [mutation-resolvers.py][mutation-resolvers]`::run_pipeline_async`;
   auth login / logout / register / `current_user` share the
   `_sync_bridged_async_body` seam or a native async body (read below);
   filter and order async entries each wrap only their blocking slice
   (filter finalize; order permission checks) while pure-Python shaping stays
   out. Read flavors (list / connection) never cross this boundary: queryset
   evaluation there is natively async (`__aiter__`, `aget`/`afirst`), offloaded
   per-hook by the colored visibility runners instead.
2. **Sync/async twins.** Every twin pair compared by behavior: write-pipeline
   sync/async entries (factory pair), filter/order `apply_sync`/`apply_async`,
   cascade `apply_cascade_permissions` / `aapply_cascade_permissions`, auth
   sync bodies / native async bodies, connection `_pipeline_sync` /
   `_pipeline_async`, list-field sync/async pipelines, relay node sync/async
   defaults. All share pure decisions; execution adapters differ where the
   contract differs (recorded per site under Findings).
3. **Derived rather than repeated knowledge.** The `thread_sensitive=True`
   worker discipline was spelled at four definition sites (owner + three
   inlined in [type-resolvers.py][type-resolvers]) — the consolidation below.
   The remaining repetitions name the discipline in prose only (oracles,
   docstrings), listed as projections, not counted.
4. **Inverse / round-trip pairs.** `sync_to_async` (loop-to-worker, this
   family) vs `async_to_sync` (worker-to-loop, auth sync bodies' Channels
   transport hop): opposite directions, opposite contracts, separate owners.
   Never merged.
5. **Contracts restated in another medium.** Oracles: the single-source
   identity test and off-loop thread test in `tests/utils/test_querysets.py`;
   the thread-affinity rollback probe in `tests/test_schema.py`; the
   task-context gather test in `tests/test_permissions.py`; the auth boundary
   spy in `tests/auth/conftest.py`; the new routing gate (below). Sources:
   spec-040 D17, spec-036 Decision 8. Projections: the owner module
   docstring and every site docstring quoted in Findings.
6. **Enforcement by omission.** Hunted async ORM touches with no bridge token:
   relay node async (`aget`/`afirst` — natively async Django), list/connection
   completion (`__aiter__` — natively async), filter/order async pre-walks
   (colored runners awaiting consumer `async def` hooks on the loop, by
   design). Each evaluated: native-async APIs need no worker; every
   sync-only touch found crosses the owner, a channels bridge, or the
   rejected test-harness pair. Residual: a sync-ORM call hiding in an async
   body with no bridge token would fail loud (`SynchronousOnlyOperation`)
   under the suite's async coverage — assessed, and the plan's final gate
   re-exercises it. No omission defect filed (no oracle + reaching input
   found; the bar for a defect is met by none of the above).

### Enumeration

Instrument: package-wide grep for `run_in_one_sync_boundary` (30 hits) and
`sync_to_async` (52 hits), plus import sweeps for `asgiref` / `channels.db` /
`channels.auth`, over 119 tracked `.py` files. (The plan's inventory says
117; the 2-file delta is flagged to Worker 0. The sweep is token-based over
the tree, so a count delta cannot hide a site.)

Every boundary call site with its role:

| Site | Role |
|---|---|
| [querysets.py][querysets]`::run_in_one_sync_boundary` | authoritative definition (sole) |
| [schema.py][schema] 346 / 360 / 373 (atomic enter / exit) | consumer, transaction-window variation |
| [mutation-resolvers.py][mutation-resolvers]`::run_pipeline_async` + compat re-export | consumer adapter + re-export (identity-pinned by oracle) |
| [filter-sets.py][filter-sets]`::apply_async` finalize | consumer (blocking slice only) |
| [order-sets.py][order-sets]`::apply_async` permission checks | consumer (blocking slice only) |
| [permissions.py][permissions]`::aapply_cascade_permissions` | consumer (whole sync walk) |
| [auth-mutations.py][auth-mutations] bridge, login async (2 branches), logout async (2 branches), register `resolve_async` | consumer (prologue/full-body per transport) |
| [auth-queries.py][auth-queries]`current_user` via `_sync_bridged_async_body` | transitive consumer |
| `forms/resolvers.py`, `rest_framework/resolvers.py` via `run_pipeline_async` / `make_resolver_entries` | transitive consumers (no own boundary) |
| [type-resolvers.py][type-resolvers] 3 lazy-`getattr` fetches | consolidated: was 2nd definition, now consumer |
| [testing-client.py][testing-client] `login` bracket (2 sites) | intentional separation (rejected) |
| [consumers.py][consumers]`::_refreshed_actor` (`database_sync_to_async`) | intentional separation (rejected) |
| Auth native Channels bodies (session `asave`/`aflush`, `channels.auth.*`) | intentional separation (rejected) |
| `connection.py` two colored pipelines | intentional separation (rejected; principle 5 contrast) |
| `auth/mutations.py` sync-body `async_to_sync` hops | inverse direction (rejected) |

### Challenges

- **C1 — worker-discipline change.** Posit retiring `thread_sensitive=True`,
  adding a context install, or wrapping the hop with a timeout. Before: 2
  authoritative definitions (owner + the inlined
  `sync_to_async(getattr, thread_sensitive=True)` shape spelled at 3 sites).
  After: 1. Count 2 → 1. Consolidated with execution proof (P1).
- **C2 — new async path touching the ORM.** Does it route through the one
  boundary? The failure mode existed: the three type-resolver fetches inlined
  the wrapper. The structural gate (G1) now pins routing for that shape; any
  genuinely different execution contract (transaction scope, thread
  sensitivity, auth context, native-async API) rejects with difference +
  trigger + home per the rejections below.
- **C3 — nested boundary calls.** Re-entrant or error? Proved re-entrant in
  the disposable workspace (P2): an inner `run_in_one_sync_boundary` bridged
  through `async_to_sync` inside an outer boundary body returns on the SAME
  worker thread (`same_thread=True`, `off_loop=True`), via asgiref 3.11.1's
  `CurrentThreadExecutor` escape. The tree holds zero nests by discipline
  (owner docstring: "never per-step hops"), verified by sweep — no sync body
  in the owner-call population invokes the owner. Discipline, not enforcement.

## Findings

### F1 — one sync boundary (consolidated)

- **Contract + variation.** One `sync_to_async(thread_sensitive=True)` worker
  per async operation for all sync-only ORM work. Varies in what the worker
  wraps (whole write pipeline, permission walk, filter finalize, session-auth
  prologue, single lazy `getattr`) and in transaction scope (inside-body
  atomic, schema-spanning window, none). Never varies in the hop itself.
- **Sites + roles.** Definition: [querysets.py][querysets]`::run_in_one_sync_boundary`.
  Consumers / transitive consumers / separations per the Enumeration table.
  Oracles: `tests/utils/test_querysets.py::test_run_in_one_sync_boundary_is_single_sourced_from_utils`
  (identity pin whose prose — "sites must not re-inline the wrapper" — the
  three type-resolver sites violated until this change),
  `::test_run_in_one_sync_boundary_runs_callable_off_event_loop`,
  `tests/test_schema.py` rollback-probe thread-affinity test,
  `tests/test_permissions.py::test_aapply_gather_restores_task_contexts`,
  `tests/auth/conftest.py::_sync_boundary_spy`, and new gate G1.
  Projections: owner module docstring, spec-040 D17, spec-036 Decision 8, site
  docstrings.
- **Challenges.** C1 count 2 → 1 (consolidated); C2 gate-pinned; C3 re-entrant
  by upstream mechanism, zero nests by discipline.
- **Owner + lifetime.** [querysets.py][querysets]`::run_in_one_sync_boundary`,
  chosen by responsibility — read-side and write-side
  modules already import it with no dependency reversal (principle 7), and
  [type-resolvers.py][type-resolvers] already imported its module. Lifetime
  (principle 4): per-call; no stored derivation; no alias carried; no
  transaction opened by the primitive. ContextVars propagate through asgiref's
  copied context (the cascade's install/reset runs inside the worker).
  Cancellation follows asgiref `SyncToAsync` shield semantics (the worker keeps
  running past the awaiting task's cancellation).
- **Migration.** [type-resolvers.py][type-resolvers]: three
  `sync_to_async(getattr, thread_sensitive=True)(root, name)` calls become
  `run_in_one_sync_boundary(getattr, root, name)`; the now-unused asgiref
  import is dropped (verified sole use); the module prose names the owner.
  Former definitions: none remain — the package now spells the worker hop
  exactly once.
- **Distinct behavior.** What stays separate, with difference + trigger +
  home (rejections R1–R6):
  - R1 [testing-client.py][testing-client] `login` bracket: difference =
    thread-insensitive (`thread_sensitive` absent) test-harness session
    writes outside any transaction and every resolver surface; trigger = the
    test client ever needing transaction-pinned sessions; home = its
    docstring (this artifact; no source edit).
  - R2 [consumers.py][consumers]`::_refreshed_actor`: difference =
    `database_sync_to_async`'s `close_old_connections`, which the neutral
    owner deliberately lacks; trigger = channels offering connection hygiene
    separable from the hop; home = its docstring (already states the
    must-not-rewrap contrast — verified, untouched).
  - R3 auth native Channels bodies: difference = native async session APIs
    (`asave`/`aflush`, `channels.auth.login`/`logout`) must be awaited on
    the loop and cannot run inside the worker; the boundary wraps only the
    sync prologue; trigger = Django/Channels ever offering sync session
    establishment; home = the native-body docstrings (already state it —
    verified, untouched).
  - R4 `connection.py` two colored pipelines: difference = must await
    consumer `async def` hooks (visibility / filter / order async twins); a
    single sync body in one boundary cannot await — principle 5's worked
    contrast (write pipeline = one sync body in one boundary; connection =
    two colored bodies sharing only pure decisions). Recorded here; the
    connection-side home edit waits for that file's external dirt to settle
    (left alone per attribution rule).
  - R5 [schema.py][schema] three-hop window: consumer, not rejection — the
    transaction must span the event-loop completion await (the completion
    awaitable must run on the loop; atomic enter/exit must run on the worker
    thread), pinned on one thread by asgiref affinity plus
    `_async_mutation_lock(alias)`; trigger = GraphQL execution ever offering
    a transaction-spanning-completion primitive collapsing the three calls to
    one; home = its docstring (already states it — verified, untouched).
  - R6 `auth/mutations.py` sync-body `async_to_sync` hops: inverse direction
    (worker-to-loop for the Channels transport), the plan's permitted hop;
    never a candidate for this owner.
- **Behavioral proof.** All execution-verified in the disposable workspace
  (copy `__file__` =
  `.../dry-ws/one-sync-boundary/django_strawberry_framework/__init__.py`, DB
  `NAME` = `.../dry-ws/one-sync-boundary/examples/fakeshop/db.sqlite3`):
  - P1 routing equivalence: pre-change probe reports `bridge=inline`,
    post-change `bridge=owner`, both `worker_off_loop=True`, same
    `(getattr, root, "category")` args, same `None` containment; full
    `tests/types/test_resolvers.py` (49 tests) green in both states.
  - P2 nesting: `result=inner-ok ... same_thread=True off_loop=True`
    (own process; asgiref 3.11.1 `CurrentThreadExecutor` escape confirmed in
    installed source).
  - P3 negative control: hand-reverted inline tree — all 49 behavior tests
    pass, routing trial fails (`AttributeError`: the routed name is absent).
    Every behavior oracle passes the bypass copy; only the routing gate
    catches it.
  Shared-tree focused run (authorized): new G1 plus 3 neighboring async
  containment tests — 4 passed, `--no-cov`.
- **Structural gate.** G1 ([test-resolvers.py][test-resolvers]`::test_async_lazy_single_fetches_route_through_shared_sync_boundary`)
  — delegating spy on the module-global owner across all three arms
  (reverse-OneToOne, forward fast path, forward planned path), asserting the
  routed `(getattr, root, name)` triple plus preserved `None` containment.
  Negative control proved (P3). Population justification: the mechanism sweep
  closed the inlined-`sync_to_async` population at exactly these three arms;
  the gate fails if any arm re-inlines (name lookup fails) or reorders args.
- **Coupling.** None. The import edge pre-existed; no other module moves with
  this finding.
- **Freshness.** Worktree blobs at edit time:
  `utils/querysets.py` `96618fba…` (== HEAD; read-only, unedited),
  `schema.py` `c2e1b748…`, `permissions.py` `757dce34…`,
  `orders/sets.py` `6044ab1a…`, `auth/queries.py` `5c59ba75…`,
  `testing/client.py` `91d61442…`, `consumers.py` `936210e2…`,
  `forms/resolvers.py` `4edb984b…`, `rest_framework/resolvers.py`
  `8024703e…`, `types/relay.py` `c333c785…`, `utils/execution_mode.py`
  `9805cdaf…`, `types/resolvers.py` pre `f3341e6a…` → post `5f4cce2b…`,
  `tests/types/test_resolvers.py` pre → post `8314fc09…`. Dirty members cited
  at HEAD bytes with disjoint hunks verified vs `git show HEAD:`:
  `filters/sets.py` HEAD `4ab65a26…` (external hunk `@@ -2357 +2357,27`,
  cited 3383+), `mutations/resolvers.py` HEAD `3fd1e571…` (external hunks at
  77/263/286/319/1033/1124-1146, cited 103+/1276+),
  `auth/mutations.py` HEAD `dbe64995…` (external hunks at
  41/227/235/316/1053/1326, cited 73/375+/751+/952+/1149+). Excluded on body
  strength: every module importing neither `asgiref`, `channels.db`, nor
  `channels.auth` (import sweep closed). Prior record
  `dry-file-utils__querysets.md` F11 re-derived as trigger: its
  testing-client half stands (R1); its types-sites half ("not the rule, no
  edit owed", `static-reviewed`) is superseded — same execution contract,
  proved same worker/timing/containment, and the standing single-source
  oracle prose already forbids the inlined shape. Both F11 fingerprints are
  stale (`5907a1f7…`, `fc077f38…`), which independently reopens it.

## Defects

None. The omission hunt (matrix axis 6) found no async path executing sync
ORM outside a bridge, a channels hop, or a natively-async Django API — and no
candidate meets the defect bar (contract row + feasible shape + reaching
input).

(Worker 2: no additional defects. Independent sweep confirms: no fourth
`sync_to_async` importer, no nested-boundary caller, no omission reaching a
wire input. R1/R4 owner-clause landings are closeout prose, not defects.)

## Pending execution

None. Every proof above executed in the disposable workspace; the focused
shared-tree run executed (4 passed). The full suite is the plan's final-gate
item, not this item's.

## Judgment

One definition, proved. The family consolidates the three inlined
`sync_to_async(getattr, thread_sensitive=True)` fetches onto the owner with
an executed equivalence proof and a negative-controlled routing gate; every
other shape either already composes the owner or rejects with a contract
difference, trigger, and home. The principle-5 contrast stands recorded:
write/auth/filter/order/permission paths share one sync body in one boundary;
`connection.py` keeps two colored bodies because it must await consumer
`async def` hooks.

## Implementation (Worker 1)

Tracked changes (both files clean at HEAD; diff vs HEAD == item diff;
`utils/querysets.py` untouched — worktree == HEAD `96618fba…`, read-only
confirmed):

- `django_strawberry_framework/types/resolvers.py` (+11/−6): three lazy
  single-relation fetches route through `run_in_one_sync_boundary`;
  `asgiref.sync.sync_to_async` import dropped; module prose names the owner.
  External dirt: none (file clean at entry).
- `tests/types/test_resolvers.py` (+67): G1 routing gate across all three
  arms with preserved-containment assertions.
- New (untracked): this artifact. No plan/ledger edits (Worker 0 owns both).

`uv run ruff check --fix` + `uv run ruff format` clean on both paths
(`format --check` and `check` pass); one focused shared-tree run authorized
and executed: 4 passed, `--no-cov`. Scratch addresses (explicit paths only):
WS copy at
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/one-sync-boundary/`
with WS-local `probe_routing_test.py`, `probe_nested.py`,
`trial_gate_test.py` — left for Worker 2, owned by this run, removable by
explicit path after verification.

## Independent verification (Worker 2)

Recorded BEFORE reading `## Findings` / `## Implementation (Worker 1)` above
(headers + tail link block only). HEAD `bfaee91d`; ITEM_BASELINE
`b40237e8560ce2df4f76032d443a9a3100ca3c15`; provisional owner read-only honored
(`utils/querysets.py` worktree `96618fba…` == HEAD blob, untouched).

### Boundary contract (my derivation)

`utils/querysets.py::run_in_one_sync_boundary` — run `fn(*args, **kwargs)` in
exactly ONE `sync_to_async(thread_sensitive=True)` worker (body:
`return await sync_to_async(fn, thread_sensitive=True)(*args, **kwargs)`).
Discipline: one worker per resolution, never per-step hops; the worker is itself
a sync context so the standing `SyncMisuseError` guards still fire inside `fn`.
Lifetime per-call: no alias/connection/transaction is carried by the primitive
itself — callers pass already-bound closures (`atomic.__enter__`, bound sync
bodies); thread affinity comes from asgiref routing every `thread_sensitive`
call from one async context onto the SAME thread (schema 3-hop window depends on
this, recorded at `schema.py::DjangoSchema._execute_mutation_field_async`).

### Call-site inventory (all `run_in_one_sync_boundary` references, worktree)

Consumers (all compose by name; zero second definitions):

- `schema.py` — 3-hop window: `atomic.__enter__`, `_exit_with_error`,
  `_exit_clean` (transaction open/pipeline/close share one thread).
- `mutations/resolvers.py::run_pipeline_async` — thin consumer wrapper
  (`return await run_in_one_sync_boundary(sync_body, mutation_cls, info, data,
  id)`); `::make_resolver_entries` routes `resolve_async` through it; canonical
  re-export of the owner name kept for compatibility (projection, not
  definition — body is the import, no wrapper of its own).
- `filters/sets.py` — 1 call: `cls._apply_common_finalize` (perm check + form
  validate + `.qs` read).
- `orders/sets.py` — 1 call: `cls._run_permission_checks`.
- `permissions.py::aapply_cascade_permissions` — 1 call wrapping the single sync
  walk.
- `auth/mutations.py` — 6 calls: `_sync_bridged_async_body._async_body` (bridge),
  login Django-HTTP + login Channels-HTTP authenticate (2), logout Django-HTTP +
  logout prologue (2), register pipeline (1).
- `types/resolvers.py` — 3 calls (THIS item): reverse-O2O `getattr(root,
  accessor_name)`, forward fast-path + planned-path `getattr(root, field_name)`.
- Transitive (no direct import): `auth/queries.py::_current_user_resolve_body`
  (runs inside `_sync_bridged_async_body`), `forms/resolvers.py` +
  `rest_framework/resolvers.py` (via `make_resolver_entries` /
  `run_pipeline_async`).

### Hand-rolled `sync_to_async` / `database_sync_to_async` sweep (my own)

Code-level `sync_to_async(` calls in package source: EXACTLY two modules —
`utils/querysets.py` (owner body) and `testing/client.py` (`force_login` /
`logout` test-harness bracket). Every other `sync_to_async(` hit is prose
inside `` `` `` docstrings. `types/resolvers.py` imported `sync_to_async` at
module level pre-item (3 inline call sites) and no longer does post-item, so the
importer population went 3 → 2 with no fourth anywhere: `middleware/` has only
`iscoroutinefunction`/`markcoroutinefunction` (no boundary); subscriptions
(`consumers.py`) cross via channels-owned `get_user` (`@database_sync_to_async`,
no local import); `management/` has zero sync/async/thread/executor matches.
`async_to_sync(` code sites: exactly the two function-local bridges in
`auth/mutations.py` (Channels HTTP login establish, Channels logout) — a
distinct private-transport mechanism, not the ORM boundary. Population closed;
agree it was 3 pre-item, now 2, fourth searched-for and absent.

### Definition counts

`def run_in_one_sync_boundary`: 1 (owner). `def run_pipeline_async`: 1, a
consumer that delegates by name (not a second boundary definition).
Pre-item second definition-shape: the `sync_to_async(getattr,
thread_sensitive=True)` spelling repeated at 3 call sites in
`types/resolvers.py` — one definition-shape × 3 copies. Posited change "retune
the boundary (executor, sensitivity, single-hop discipline)" forced 2
definitions to move → duplication confirmed; post-item count 1.

### Owner I would choose

`utils/querysets.py::run_in_one_sync_boundary`. Responsibility: neutral
off-event-loop substrate already depended on by read-side modules
(`filters/`, `orders/`, root `permissions.py`); a `mutations/`-sited owner
would force root modules into a subpackage dependency or a sibling-flavor
import — dependency direction wins per principle 7. No narrower valid owner
exists (every legitimate consumer already imports this module).

### Principle-8 hunk verdicts (derived from HEAD vs ITEM_BASELINE bytes)

`types/resolvers.py` +11/-6 = import swap (−`sync_to_async` import,
+`run_in_one_sync_boundary` in the pre-existing `..utils.querysets` import —
edge pre-existed, no new dependency, `utils/querysets.py` imports only
`..exceptions` + `.write_transaction`, so no cycle) + docstring reword + 3
identical call-site swaps. Each swap: `await sync_to_async(getattr,
thread_sensitive=True)(root, name)` → `await run_in_one_sync_boundary(getattr,
root, name)` against owner `await sync_to_async(fn,
thread_sensitive=True)(*args, **kwargs)`: same callable, same positional args,
same `thread_sensitive=True`, same one-hop containment, same thread/executor
routing; absence containment (`except related_does_not_exist: return None`)
untouched and still outside the hop in both versions. No flag/param dropped
(owner accepts and forwards `**kwargs`; sites pass none in either version).
Observable behavior identical on every principle-8 axis (exceptions, thread,
query effects, await points, cancellation).

### C3 nesting judgment

Zero nests by discipline, verified not assumed: every `fn` passed to the owner
is sync (`getattr` reads, `atomic` dunders, `_apply_common_finalize`,
`_run_permission_checks`, cascade walk, pipeline sync bodies, auth sync
bodies/prologues) — none can `await` a nested boundary, and an `async def`
consumer hook raises `SyncMisuseError` inside the worker rather than nesting.
Asgiref 3.11.1 `SyncToAsync.__call__` reuses the parent executor when inside an
`AsyncToSync` thread and raises on single-executor re-entry; that hatch is a
backstop this family never reaches, not a relied-upon path. Gap noted: the
no-nesting discipline lives in each caller's prose/shape, not as one recorded
clause at the owner — acceptable (owner stays mechanism-neutral) but a future
async-`fn` caller would silently become a second hop; the `SyncMisuseError`
guards are the mechanical backstop. No version pin for asgiref exists in
pyproject (transitive via Django/Channels); the boundary uses only the stable
`thread_sensitive=True` contract, so pinning is not owed by this item.

### Gate judgment

`test_async_lazy_single_fetches_route_through_shared_sync_boundary` (+67):
three arms (reverse-O2O absence, forward fast-path unsaved, forward
planned-path unsaved) each assert behavior (`is None`) AND routing (spy on
`type_resolvers.run_in_one_sync_boundary` recording `(fn, args)`; final
assertion pins `[(getattr, "profile"), (getattr, "category"),
(getattr, "category")]` plus root identity per arm). The spy delegates to the
real boundary, so arms execute the true off-loop path — routing assertion is
not a substitute for execution. Arm independence: each arm drives a distinct
branch predicate (`accessor_name` vs fast vs planned key walk); a bypass in any
one arm zeroes only its entries and breaks the ordered list. Tier:
`tests/types/` library tier — correct per AGENTS.md (unreachable from a fakeshop
GraphQL query: synthetic `SimpleNamespace` fields, unsaved instances, no
fixture shape exists at the live tier). Oracle-independence: the test reads the
owner only as the spy's delegate (execution vehicle), never as the expectation
source — expectations are literals (`getattr`, `"profile"`/`"category"`,
`is None`); a bypass breaks the call list while behavior asserts still pass
(proven by N1 variant below).

### N1 negative control (fresh WS copy — my own, W1's WS untouched)

Copy: `/tmp/dry-ws/one-sync-boundary-w2` (rsync excl. `.git/.venv/docs`;
`__file__` =
`/private/tmp/dry-ws/one-sync-boundary-w2/django_strawberry_framework/__init__.py`;
DB `NAME` =
`/private/tmp/dry-ws/one-sync-boundary-w2/examples/fakeshop/db.sqlite3` —
own tree, own DB, never branched; shared tree hashes unchanged after
(`5f4cce2b…`, `8314fc09…`). Inline-copy mutation (WS only): 3 sites back to
`sync_to_async(getattr, thread_sensitive=True)(root, name)`. Results:
49 behavior tests PASS (1 deselected), gate FAILS. Two failure modes observed:
(a) import removed → `monkeypatch.setattr` raises `AttributeError`
(setup-time fail); (b) seam kept installable but uncalled → behavior asserts
pass, routing assert fails `Left [] vs Right [3 items]`. Variant (b) proves the
gate pins routing over and above behavior. Shared-tree focused run: gate 1
passed; `-k async` 6 passed.

### Rejections (my judgments)

- `testing/client.py` harness: distinct contract (test-only session writes,
  bracket/lifespan shape, no consumer hook) — stays separate; trigger: harness
  ever sharing the per-resolution discipline.
- `consumers.py` Channels bodies (`get_user` already
  `@database_sync_to_async`): wrapping would add a second boundary AND drop
  `close_old_connections` — contrast recorded at the consumer site; check owner
  carries the mirror clause at closeout.
- `connection.py` two-colored bodies: must `await` consumer `async def` hooks
  mid-pipeline, so one sync body is impossible — principle-5 opposite answer;
  contrast must be recorded at BOTH owners (verify at reconcile).
- `schema.py` 3-hop window: consumer, not rejection (uses the owner 3×).
- `auth/*` `async_to_sync` hops: opposite-direction bridge at the private
  transport boundary (sync context awaiting Channels-native async teardown),
  never an ORM read — stays separate; trigger: a hop ever wrapping ORM work.

### Freshness (re-hashed by me)

Worktree blobs: `utils/querysets.py` `96618fba…` (== HEAD, read-only honored);
`types/resolvers.py` `5f4cce2b…`; `tests/types/test_resolvers.py`
`8314fc09…`; `schema.py` `c2e1b748…`; `permissions.py` `757dce34…`;
`orders/sets.py` `6044ab1a…`; `filters/sets.py` `4a40e51b…`;
`mutations/resolvers.py` `a322d17a…`; `auth/mutations.py` `200805d2…`;
`auth/queries.py` `5c59ba75…`; `testing/client.py` `91d61442…`;
`consumers.py` `936210e2…`; `connection.py` `3c4d5dcb…` (concurrent cursor-guard
dirt, outside family sites); `forms/resolvers.py` `4edb984b…`;
`rest_framework/resolvers.py` `8024703e…`. Item-scoped diff vs ITEM_BASELINE:
exactly the 2 claimed files (+11/-6, +67) plus concurrent
`docs/bug_hunt/bug_hunt-0_0_15.md` churn (other cycle, not this item).
Concurrent package dirt (`auth/mutations.py`, `filters/sets.py`,
`mutations/resolvers.py` vs HEAD) predates ITEM_BASELINE (zero diff vs
ITEM_BASELINE) — untouched, out of scope.

### Ruff (run by me on both touched paths)

`ruff format --check` — 2 files already formatted.
`ruff check` — All checks passed.

### Reconciliation (Worker 2) — agree-or-differ per point, after reading Findings

1. **1 definition** — AGREE. `def run_in_one_sync_boundary` occurs exactly
   once (owner); `run_pipeline_async`/`make_resolver_entries` delegate by name.
2. **Closed population** — AGREE with one count clarification: 3 importers PRE-change
   (owner, `types/resolvers.py`, `testing/client.py`), 2 POST-change; no fourth
   found (middleware/subscriptions/management swept clean; `async_to_sync`
   only the 2 known function-local auth bridges). Enumeration-table rows match
   my inventory member-for-member; raw hit counts differ by pattern scope only
   (`sync_to_async` token also matches inside `async_to_sync`; harmless).
   The 117-vs-119 inventory delta is optimizer-side (`nested_planner.py` + one);
   that file carries zero family tokens — does not touch this finding.
3. **Consumers** — AGREE on every row (schema 3-hop, `run_pipeline_async` +
   compat re-export, filters finalize, orders perm checks, cascade, auth
   bridge/2+2 branches/register, auth-queries/forms/rest transitive).
4. **Consolidation +11/-6, import-safe** — AGREE hunk-by-hunk (see principle-8
   verdicts above; edge pre-existed; `utils/querysets.py` imports only
   `..exceptions` + `.write_transaction` — no cycle).
5. **Rejections** — AGREE on R2/R3/R5 (pre-existing owner-side prose verified
   in place, untouched) and R6 (inverse direction, no home owed). R1/R4 homes
   live in-artifact only: R1's file is CLEAN (a clause could land any time —
   closeout prose-delta per cycle convention); R4's connection-side home
   correctly waits for that file's concurrent dirt to settle (editing it now
   is forbidden), and the querysets-side home is unlandable this cycle
   (read-only dispute). Neither gap breaks a contract row — acceptance
   rationale recorded under Verdict. Correction to my own trace: the "gap
   noted" under C3 is WITHDRAWN — the no-nesting discipline IS recorded at the
   owner (`utils/querysets.py:472` "never per-step hops").
6. **C1 2→1 / C2 gate-pinned / C3** — AGREE. C3 reliance is on discipline
   (all `fn` args sync by shape; `async def` hooks fail loud via
   `SyncMisuseError`), with asgiref 3.11.1 escape characterized as backstop
   (P2), not load-bearing. No pin owed (stable `thread_sensitive=True`
   contract only).
7. **Owner + per-call lifetime** — AGREE (dependency-direction reasoning
   matches mine).
8. **No defects** — AGREE (independent omission hunt: no async sync-ORM touch
   outside owner/channels/native-async).
9. **No pending execution** — AGREE. Library-tier execution is adequate here:
   2/3 gate arms drive REAL Django descriptors (`Item` unsaved-FK
   `DoesNotExist`) through the real off-loop worker (P1 `worker_off_loop`);
   the reverse-O2O arm's synthetic double isolates the absence-containment
   shape the live tier cannot mint. No async live-tier proof deferred.
10. **Gate +67, 3 arms** — AGREE. Independence judgment: expectations are
    literals (`getattr`, names, `is None`); the owner is the spy's execution
    vehicle, never the expectation source — not prohibited owner-reading. N1
    variant (b) proves behavior-pins and routing-pin fail independently.
11. **Querysets read-only `96618fba…`** — AGREE (worktree == HEAD, untouched).

### Verdict (Worker 2)

`Status: verified`. F1 consolidates the second definition-shape onto the owner
with byte-parity on every principle-8 axis, an executed equivalence proof, and
a negative-controlled routing gate; all other shapes compose or reject with
difference + trigger. R1 (testing-client clause, clean file) + R4
(connection-side clause, post-settle) land as closeout prose deltas — named
below for Worker 0; neither blocks the consolidation (Coupling: none).
No `(Worker 2)` defects. No pending execution.

Worker 0 rows owed: tick Family `one-sync-boundary` verified Run
0.0.15 2026-09-19-1 (CONSOLIDATED, N1 re-run by W2, no defects, no pending
execution); ledger `django_strawberry_framework/types/resolvers.py` +
`tests/types/test_resolvers.py` (symbols per Implementation); index
`one-sync-boundary` open → `consolidated`; scratch W1
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/one-sync-boundary/`
(+3 probe files) removable by explicit path; my WS
`/tmp/dry-ws/one-sync-boundary-w2/` lives outside the tree (no tree cleanup
owed); closeout prose: R1 clause at `testing/client.py::login`, R4 clause at
`connection.py` (post-settle) mirroring the R4 difference text.

## Scoped re-trace (run 8, s20; Worker 1)

Zero-edit re-trace at HEAD bytes. HEAD `83998e08`; drift base
`0c0537e2`; ITEM_BASELINE `5fc626c6` (stash = dispatch-time worktree
snapshot). Everything above this section is PRIOR EVIDENCE ONLY. Every
verdict below is re-derived fresh; each names CONFIRM or REVISE against
the prior finding. Read-only probes only; no pytest; nothing tracked
touched (this artifact excepted).

### Freshness (three states, re-hashed)

`before` = ITEM_BASELINE copy, `worktree` = consolidate copy (synced
this item), HEAD via `git rev-parse`. `before == worktree` on all 15
files: zero concurrent drift since dispatch on family files.

| File | Drift base | HEAD | before/worktree |
|---|---|---|---|
| `utils/querysets.py` | `3616927d` | `392e50d0` | `cfc773ba` |
| `permissions.py` | `72102cc0` | `d77c5050` | `42c3c19c` |
| `orders/sets.py` | `6044ab1a` | `c4564c08` | `125d808c` |
| `filters/sets.py` | `993e887a` | `3d307402` | `ec278851` |
| `mutations/resolvers.py` | `043a2d0b` | `7a25afea` | `dd00ec6e` |
| `auth/mutations.py` | `d1a59c44` | `72595bb1` | `d3853af4` |
| `types/resolvers.py` | `72d62dc4` | `574e9768` | `7a953c53` |
| `testing/client.py` | `d8feebb2` | `2466edae` | `2d9aa737` |
| `schema.py` | `e6b52335` | `bba03d7d` | `abad5795` |
| `auth/queries.py` | — | `837ce75f` | `837ce75f` (= HEAD) |
| `forms/resolvers.py` | — | `ea839d84` | `6e613333` |
| `rest_framework/resolvers.py` | — | `420fc3ca` | `3fc6a366` |
| `connection.py` | — | `3d6dd424` | `64b85d0e` |
| `consumers.py` | — | `5436cf35` | `7a5a77c1` |
| `tests/types/test_resolvers.py` | — | `346e945d` | `d78d605f` |

### Drift delta (drift base to HEAD, family files + schema.py)

Boundary-token grep over every in-scope commit diff (13 commits):
11 commits touch ZERO boundary tokens. The exceptions:

- `005b1f53` (schema.py only, +105/-182): deletes
  `_MutationWindowThread` + the `ThreadSensitiveContext` /
  `context_to_thread_executor` plumbing and adds the FIRST
  code-level `sync_to_async` (`:406`, `window` on a private
  single-thread executor, or the blocked caller's thread) and
  `async_to_sync` (`:394`, `complete` driven on the loop) in
  schema.py. The s20 staleness trigger, confirmed.
- `b20277fe`: retypes the owner signature (`Any` to ParamSpec);
  the one-line body is byte-identical. Behavior-inert.

All other listed commits (`5c5e32c5`, `10d2b9cd`, `bbe54687`,
`1a17dca5`, `2915250d`, `dc0ae008`) plus the typing rewrites
(`999a1aab`, `849f67bc`, `dfbea72b`, `fef11e64`, `e37448e5`)
preserve every boundary call site, import, and bridge line they
touch (cascade rewrite, filter rewrite, register branch, and
client sibling rewrite all verified token-stable). At the drift
base schema.py already held 0 owner code refs and 0 bridge code
calls (`1b6a09b1` predates the base — verified ancestor); the
trio shape predates the base too (`ddd5dbb9`, 2026-08-23).

### Boundary rule + censuses re-derived at HEAD bytes

- Owner: `def run_in_one_sync_boundary` occurs EXACTLY once
  ([querysets.py][querysets]:516); body still the one line
  `return await sync_to_async(fn, thread_sensitive=True)(*args,
  **kwargs)` (`:536`). No-nesting clause ("never per-step hops")
  still in the docstring. Rule CONFIRMED.
- Owner code calls: 10 across 5 files — filters/sets.py:3628
  (`_apply_common_finalize`), auth/mutations.py:471 (bridge),
  :867/:874 (login x2), :1069/:1070 (logout x2), :1400
  (register), mutations/resolvers.py:1431 (`run_pipeline_async`),
  permissions.py:746 (cascade walk), orders/sets.py:844
  (`_run_permission_checks`). Consumer census 5 files:
  CONFIRMED (count and composition; run-7's 6→5 stands).
- Transitive consumers CONFIRMED: auth/queries.py:128 (bridge),
  forms/resolvers.py:641 + rest_framework/resolvers.py:2535
  (`make_resolver_entries`); compat re-export still importable
  from mutations/resolvers.py (`:1434` comment + import).
- Code-level `sync_to_async(`: 7 sites in 4 modules — owner
  `:536` + trio x3 (`:642`/`:715`/`:786`) + testing/client x2
  (`:530`/`:534`) + schema.py:406. The prior "EXACTLY two
  modules" census is REVISED to four; matches s13 R1's
  corrected census line-for-line (see below).
- Code-level `async_to_sync(`: 3 sites in 2 modules — the two
  known function-local auth bridges (`:841`, `:1049`) plus
  schema.py:394 (new in drift).
- `database_sync_to_async`: 0 code imports package-wide; still
  reaches only via channels-owned callables
  (`channels.auth.login`/:793, `logout`/:1014,
  `get_user`/consumers.py:1623). CONFIRMED.
- Class-form sweep: 0 `SyncToAsync(`/`AsyncToSync(`
  instantiations, 0 `ThreadSensitiveContext` code uses; the one
  `AsyncToSync.executors` read is schema.py:390. Importer
  population closed: `middleware/request_body.py` + `views.py`
  import only `iscoroutinefunction`/`markcoroutinefunction`
  (no boundary); `consumers.py` only `asgiref.typing`.
  Population closed; no fifth `sync_to_async` importer.

### Carried evidence tested from the family side

- s13 m2 — CONFIRMED, strengthened. `git log -S
  'run_in_one_sync_boundary'` over types/resolvers.py +
  tests/types/test_resolvers.py returns ZERO commits, and `-S
  'route_through_shared_sync_boundary'` likewise: the F1
  consolidation and the G1 gate never existed in committed
  history. The trio region in history knew only the inline
  shape (introduced `ddd5dbb9`, retyped `b20277fe`). The
  run-2 ledger row ("Adopted 2026-09-21 (run 2, worktree
  entry)") is accurate as written — a worktree entry — and
  the worktree STILL carries that instance (see Dirt).
- s13 R1 corrected census — CONFIRMED line-for-line: owner
  `:536` + trio `:642`/`:715`/`:786` + schema.py:406 +
  testing `:530`/`:534`, plus `async_to_sync` at schema.py:394.
  The prior "exactly owner + 2" was already wrong at the
  drift base (trio predates it). Separation unaffected.

### Finding verdicts (CONFIRM or REVISE each)

- F1 one sync boundary — REVISED to owed-not-landed. At HEAD
  the second definition-shape is back: C1 counts 2 again
  (owner + the inlined `sync_to_async(getattr,
  thread_sensitive=True)` spelling at 3 sites). The
  consolidation case re-proved statically on HEAD bytes (same
  callable, same positional args, same `thread_sensitive=True`,
  same one-hop containment, absence-catch outside the hop in
  all three arms); the hop-equivalence execution proof (prior
  P1) stands as prior evidence — the drift around the trio is
  annotation-only. Re-landing = the worktree hunks (import
  swap + prose + 3 swaps); landing it is a Worker-0/commit
  decision, and the dirt is concurrent-external, so this
  zero-edit item does not land it. Owner choice + per-call
  lifetime: CONFIRMED (dependency direction unchanged; every
  legitimate consumer still imports the utils module).
- C2 gate — REVISED: G1 never committed (0 hits at HEAD);
  routing is unpinned in committed history and the failure
  mode it pinned (re-inline) IS the HEAD state. The standing
  identity-pin prose ("sites must not re-inline the wrapper",
  tests/utils/test_querysets.py:310-319, intact at HEAD)
  already forbids the HEAD trio shape; only its mechanical
  half (re-export identity) executes.
- C3 nesting — CONFIRMED. AST scope map: all 10 owner calls
  sit directly inside an `async def`; every `fn` arg is sync
  by shape (`getattr` x3 inline, finalize, perm checks,
  cascade walk, pipeline sync bodies, auth sync
  bodies/prologues). Zero nests by construction. Prior P2
  (asgiref 3.11.1 escape as backstop) stands un-re-executed;
  installed asgiref is still 3.11.1. The `SyncMisuseError`
  guards remain the mechanical backstop for an `async def`
  hook smuggled into a body.
- R1 testing/client — verdict STANDS, difference REVISED.
  The prior "thread-insensitive (`thread_sensitive` absent)"
  is factually wrong: asgiref 3.11.1's signature reads
  `thread_sensitive: bool = True`, so kwarg-absent IS
  thread-sensitive (as s13 already corrected). The separation
  rests instead on: harness-only surface (no runtime module
  imports `testing.*` — s13 C27 sweep), no transaction, no
  consumer hook, bracket/lifespan shape (entry + `finally`
  exit = two hops by design). Trigger STANDS (harness ever
  needing transaction-pinned sessions). Home clause still
  unlanded at BOTH states (login docstring has no owner
  contrast) — closeout prose still owed.
- R2 consumers `_refreshed_actor` — CONFIRMED. The
  must-not-rewrap contrast clause is present at HEAD
  (consumers.py:1610-1613, prose naming the owner +
  `close_old_connections`); shape unchanged (`get_user`
  awaited bare, :1630).
- R3 auth native Channels bodies — CONFIRMED: natives
  awaited on the loop (`channels_login` :797, `asave` :798,
  `aflush` :802, `channels_logout` :1020, `_channels_logout`
  direct await :1075); boundary wraps only sync prologues.
  Docstrings state it; untouched.
- R4 connection colored pipelines — verdict CONFIRMED (0
  owner compositions; must await consumer `async def`
  hooks), home STILL unlanded both sides (no contrast clause
  in connection.py at HEAD or worktree; none at the owner) —
  closeout prose still owed.
- R5 schema 3-hop window (prior "consumer") — SUPERSEDED by
  R7. The 3-hop shape no longer exists (`1b6a09b1` predates
  the drift base; `005b1f53` rewrote the mechanics).
- R6 auth `async_to_sync` hops — CONFIRMED (inverse
  direction, worker-to-loop for the Channels transport;
  `:839`/`:841`, `:1047`/`:1049`, both function-local).
- R7 (NEW) schema.py window adapter — REJECTED with evidence
  (judged, not assumed; agrees with s5's F1-out call on
  independent fresh reads). Difference: the adapter creates,
  owns, and destroys its own single-thread executor (private
  connection, closes it at `:395-397`), or borrows the
  blocked caller's thread under a sync caller
  (`thread_sensitive=executor is None`, `:406-411`); it
  drives completion INTO the loop via `async_to_sync`
  (`:394`), the opposite direction from the owner. The owner
  signature `(fn, *args, **kwargs)` with pinned
  `thread_sensitive=True` and no `executor` parameter cannot
  express either window mode — composition is
  signature-impossible, not merely unwise. The window thread
  is the thread the boundary's work lands on (asgiref
  caller-executor precedence), which the adapter's own
  docstring states (`:353-363`); disjoint contracts, disjoint
  reasons to change (a boundary-discipline change moves the
  owner only; a window-ownership change moves the adapter
  only). 0 compositions at HEAD (the one owner-name hit,
  `:355`, is that prose). Trigger: the owner ever accepting
  executor/thread-ownership routing, or asgiref ever
  offering a transaction-spanning-completion primitive
  collapsing the adapter into one boundary call. Home: the
  schema.py docstrings (module `:27-41` + `:349-377`) —
  already state it; verified, untouched. No index change:
  schema.py stays outside the 8-file covered list.
- Matrix axes — re-discharged: (1) cross-flavor mirroring
  holds (pipeline twin, bridge seam, blocking-slice-only
  filter/order entries all re-read at HEAD cites); (2)
  sync/async twins compared by behavior at the new cites,
  shared pure decisions, adapter-only differences; (3) the
  `thread_sensitive=True` spelling is at 2 definition sites
  again (owner + trio) — the F1 REVISE above; (4)
  `sync_to_async` vs `async_to_sync` stay opposite
  directions with separate owners (R6 + R7); (5) oracles
  intact at HEAD (identity pin + off-loop test, gather
  test :1936, auth spy conftest :16, window rollback tests
  :335/:430/:471 under drifted names) except G1, which
  never committed; (6) omission hunt re-closed via the
  importer census above — no new bridge importer, no
  nest, no natively-async API newly wrapped.

### Dirt attribution (by content, HEAD vs worktree)

- types/resolvers.py (66 lines): F1-consolidation instance
  (import swap, prose reword, 3 call-site swaps — the run-2
  adoption, still uncommitted, predates ITEM_BASELINE) PLUS
  truth-migration/deadline dirt (`truth` import,
  `_in_instance_namespace`, `_fk_attname_is_deferred`
  rewrite, stub prose + `BaseException` to `Exception`,
  `truth.is_type`, `check_deadline` x5 + import). Family
  verdicts hold at HEAD bytes; the worktree additionally
  satisfies F1.
- tests/types/test_resolvers.py (104 lines): the G1 gate
  (run-2 adoption, still uncommitted) + surrounding drift.
- auth/mutations.py: exactly one boundary-token hunk — the
  owner import line gains `_disposed_awaitable`
  (awaitable-refusal family; call sites untouched).
- querysets.py, permissions.py, orders/sets.py,
  filters/sets.py, mutations/resolvers.py, testing/client.py,
  schema.py, auth/queries.py, forms/resolvers.py,
  rest_framework/resolvers.py, connection.py, consumers.py:
  ZERO boundary-token hunks — all dirt concurrent-external
  by content; every family verdict holds at both states.

### Defects

None. The HEAD trio-inline state is the owed F1
consolidation itself, not a defect: behavior-identical
spelling duplication with no failing oracle (the identity
pin passes mechanically; its prose states the contract the
re-landing restores). No omission reaches a wire input.

### Pending execution

None. Static re-trace; no tracked change to prove. The
prior P1/P2/N1 executions stand as prior evidence for the
hop-equivalence shape they proved; re-execution is owed
only with the re-landing, not with this verdict.

### Judgment

Re-trace verified (Worker 1): owner + rule CONFIRMED, 5-file
consumer census re-derived intact, window adapter adjudicated
OUT (new rejection R7, signature-impossible composition),
s13 m2 + R1 carried evidence CONFIRMED from the family side
with stronger commits (`-S` searches empty), R1 difference
corrected (kwarg-absent is thread-sensitive by default),
R2/R3/R4/R6 CONFIRMED (R1/R4 home prose still owed),
F1+C2 REVISED (consolidation + gate uncommitted — owed,
never in history), C3 zero-nests CONFIRMED by scope map,
matrix re-discharged, dirt attributed by content, all three
states fingerprinted. Zero edits; index needs no change
(schema.py stays out of the 8-file list; R7 recorded here).

## Run-8 verification (Worker 2)

Expectation-first re-trace at HEAD `83998e08`, drift base
`0c0537e2`, ITEM_BASELINE `5fc626c67917415160978a213fef9ed8b9c0afdd`.
Every count below is my own instrument on HEAD bytes
(`git -C <shared> grep|show <commit> -- <dir pathspec>`, an AST
scope map over extracted HEAD bytes, `git log -S`, installed-source
reads); the W1 section above was the claim under test, never
evidence. Address `dry/syncboundary-retrace-s20/verify`; read-only
probes only, no pytest. Environment note: that copy's venv holds a
partial asgiref (dist-info 3.11.1, no `sync.py`), so the signature
read below comes from the shared venv's installed 3.11.1 source;
all static censuses are unaffected.

### Freshness (re-hashed; before == consolidate == verify everywhere)

Drift / HEAD / before-worktree short blobs; the last column extends
W1's table (W1 left drift "-" on six rows):

- `utils/querysets.py` `3616927d` / `392e50d0` / `cfc773ba`
- `permissions.py` `72102cc0` / `d77c5050` / `42c3c19c`
- `orders/sets.py` `6044ab1a` / `c4564c08` / `125d808c`
- `filters/sets.py` `993e887a` / `3d307402` / `ec278851`
- `mutations/resolvers.py` `043a2d0b` / `7a25afea` / `dd00ec6e`
- `auth/mutations.py` `d1a59c44` / `72595bb1` / `d3853af4`
- `types/resolvers.py` `72d62dc4` / `574e9768` / `7a953c53`
- `testing/client.py` `d8feebb2` / `2466edae` / `2d9aa737`
- `schema.py` `e6b52335` / `bba03d7d` / `abad5795`
- `auth/queries.py` `b036bdac` / `837ce75f` / `837ce75f` (= HEAD)
- `forms/resolvers.py` `35c282cc` / `ea839d84` / `6e613333`
- `rest_framework/resolvers.py` `0d302782` / `420fc3ca` / `3fc6a366`
- `connection.py` `4894f90f` / `3d6dd424` / `64b85d0e`
- `consumers.py` `936210e2` / `5436cf35` / `7a5a77c1`
- `tests/types/test_resolvers.py` `346e945d` / `346e945d` / `d78d605f`
- `tests/utils/test_querysets.py` `73e7a6c2` / `3ff4094a` / `b1fc954b`

Zero concurrent drift since dispatch on every family file.

### Drift re-scope (my own log + token sweep)

`git log 0c0537e2..HEAD` over the 8 members + schema.py returns
exactly 13 commits, the set W1 names. My boundary-token grep
(`run_in_one_sync_boundary|sync_to_async|async_to_sync|database_sync_to_async|SyncToAsync|AsyncToSync|ThreadSensitiveContext|close_old_connections`
over added/removed diff lines) gives 11 commits at zero; the only
exceptions are `005b1f53` (38 lines) and `b20277fe` (2 lines).
`005b1f53` numstat on schema.py is +105/-182 exactly: it deletes
`_MutationWindowThread` + the `ThreadSensitiveContext` /
`context_to_thread_executor` plumbing and adds the first code-level
`sync_to_async` (:406) and `async_to_sync` (:394) in schema.py.
`b20277fe` retypes only the owner signature (`Any` to ParamSpec);
the body line is diff context, byte-identical: behavior-inert.
`1b6a09b1` is a verified ancestor of the base; the trio shape dates
to `ddd5dbb9` (2026-08-23). At the base, schema.py holds 0 owner
code refs and 0 bridge code calls (one prose hit each), and the
trio is already inline (`:619`/`:692`/`:763`). W1's "only two
matter" stands on my instruments.

### Verdict rows (CONFIRM or REVISE each, independently)

- Owner + rule — CONFIRMED. `def run_in_one_sync_boundary`
  occurs exactly once ([querysets.py][querysets]:516); body is the
  one line `return await sync_to_async(fn,
  thread_sensitive=True)(*args, **kwargs)` (:536); the "never
  per-step hops" clause is in the docstring (:527).
- Consumer census 5 files / 10 calls — CONFIRMED call by call,
  each with its enclosing `async def` from my AST map:
  filters/sets.py:3628 (`apply_async`), auth/mutations.py:471
  (bridge `_async_body`), :867/:874 (`_login_resolve_body_async`),
  :1069/:1070 (`_logout_resolve_body_async`), :1400
  (`resolve_async`), mutations/resolvers.py:1431
  (`run_pipeline_async`), permissions.py:746 (cascade),
  orders/sets.py:844 (`apply_async`). Transitives confirmed:
  auth/queries.py via `_sync_bridged_async_body`,
  forms/resolvers.py:641 + rest_framework/resolvers.py:2535 via
  `make_resolver_entries`, compat re-export comment + import at
  mutations/resolvers.py:1434.
- Code censuses — CONFIRMED line-for-line. `sync_to_async(` code
  calls: 7 in 4 modules (owner :536, trio :642/:715/:786,
  testing/client :530/:534, schema.py:406); every other hit is
  docstring prose. `async_to_sync(`: 3 in 2 modules (:841, :1049,
  schema.py:394). `database_sync_to_async`: 0 code imports,
  prose-only; reached only via channels-owned callables.
  Class forms: 0 `SyncToAsync(`/`AsyncToSync(` instantiations; the
  one `AsyncToSync.executors` read is schema.py:390.
  `ThreadSensitiveContext`: prose-only (2 hits);
  `context_to_thread_executor`: 0 hits. Importer population
  closed: `sync_to_async` importers are exactly owner /
  types-resolvers / testing-client / schema.py; middleware and
  views import only `iscoroutinefunction` /
  `markcoroutinefunction`; consumers.py only `asgiref.typing`.
  The "EXACTLY two modules" census is REVISED to four — and it
  was already wrong at the drift base, where the trio predates it.
- s13 m2 — CONFIRMED, strengthened. `git log -S
  'run_in_one_sync_boundary'` over types/resolvers.py +
  tests/types/test_resolvers.py returns zero commits; `-S
  'route_through_shared_sync_boundary'` likewise; my extra `-S
  'from asgiref.sync import sync_to_async'` probe returns only
  the introducing `ddd5dbb9`. F1/G1 never existed in committed
  history. G1 has 0 hits at HEAD and is present in the worktree
  (:691); the worktree trio routes through the owner. The run-2
  ledger row ("Adopted 2026-09-21 (run 2, worktree entry)") is
  accurate as written, and its instance is still worktree-only.
- s13 R1 census — CONFIRMED line-for-line (owner + trio x3 +
  schema.py:406 + testing x2, plus `async_to_sync` schema.py:394).
- F1+C2 owed-not-landed — CONFIRMED as REVISED. C1 counts 2
  again at HEAD. I re-proved the consolidation case statically
  on HEAD bytes, reading all three arms: same callable
  (`getattr`), same positional args (`root`, name), same
  `thread_sensitive=True`, absence-catch outside the hop in all
  three. G1 is uncommitted so routing is unpinned and the pinned
  failure mode (re-inline) IS the HEAD state; the identity-pin
  prose ("sites must not re-inline the wrapper",
  tests/utils/test_querysets.py:310-319, intact at HEAD) already
  forbids the trio shape while only its mechanical half
  (re-export identity) executes. The re-landing framing is
  judged correct: the worktree carries the F1+G1 hunks but the
  types/resolvers.py delta also carries truth/deadline drift
  (55 of 66 numstat lines are other families'), so landing is a
  Worker-0/commit decision this zero-edit item must not take.
- C3 zero-nests — CONFIRMED by my own AST scope map: all 10
  owner calls sit directly inside an `async def`; every `fn`
  arg is sync by shape; NESTS=0. The `SyncMisuseError` backstop
  prose is intact at the bridge, cascade, and pipeline sites.
  Installed asgiref is 3.11.1 (dist-info; see environment note).
- R1 — verdict STANDS with the revised difference. Installed
  asgiref 3.11.1 source reads `thread_sensitive: bool = True`,
  so kwarg-absent IS thread-sensitive; the prior
  "thread-insensitive" was factually wrong. The separation
  grounds check out: harness-only surface (no runtime module
  imports `testing.*` — only its own `__init__` re-export),
  no transaction (0 `atomic` in the bracket), no consumer hook,
  bracket/lifespan shape (entry + `finally` exit = two hops by
  design). Trigger stands. Home clause unlanded at BOTH states
  (login docstring identical, no owner contrast): closeout
  prose still owed.
- R2 — CONFIRMED: contrast clause present at HEAD
  (consumers.py:1610-1613, naming the owner +
  `close_old_connections`); `get_user` awaited bare (:1630).
- R3 — CONFIRMED: natives awaited on the loop (`channels_login`
  :797, `asave` :798, `aflush` :802, `channels_logout` :1020,
  `_channels_logout` direct await :1075); the boundary wraps
  only sync prologues. Docstrings state it; untouched.
- R4 — CONFIRMED: 0 owner compositions (no owner calls,
  imports, or name hits in connection.py at either state) and
  the must-await-hooks prose stands; home STILL unlanded both
  sides (no contrast clause in connection.py at HEAD or
  worktree; none at the owner — the module docstring names the
  primitive and the colored runners but no R4 contrast):
  closeout prose still owed.
- R5 SUPERSEDED by R7 — CONFIRMED. The 3-hop shape no longer
  exists (0 owner code refs in schema.py; `1b6a09b1` predates
  the base).
- R7 schema.py window adapter — REJECTED with my own evidence
  (signature-impossibility derived, not trusted). The adapter
  creates, owns, and destroys a private single-thread executor
  (created :400-404, connections closed :395-397, shut down
  :417), or borrows the blocked caller's thread
  (`thread_sensitive=executor is None`, :406-411); it drives
  completion INTO the loop via `async_to_sync` (:394), the
  opposite direction from the owner. The owner `(fn, *args,
  **kwargs)` pins `thread_sensitive=True` with no `executor`
  parameter, so it cannot express either mode — and asgiref
  itself raises `TypeError` when both are set
  (`SyncToAsync.__init__`, installed source). Composition is
  signature-impossible. 0 compositions at HEAD (the one
  owner-name hit, :355, is prose). Home docstrings already
  state it (module docstring + :349-377, incl. the
  caller-executor precedence at :353-363): verified, untouched.
  This agrees with s5's carried F1-out evidence
  (dry-0_0_15.md:7011 "Family impact: F1-out evidence carried
  to s20"). Trigger and disjoint-change reasoning stand as W1
  states them.
- Matrix — re-discharged: (1) mirroring holds (pipeline twin,
  bridge seam, blocking-slice-only filter/order entries
  re-read); (2) twins share pure decisions
  (cascade/bridge/pipeline prose re-read); (3) the spelling is
  at 2 definition sites again (F1 REVISE); (4) opposite
  directions, separate owners (R6 + R7); (5) oracles intact
  (identity pin + off-loop test, gather test :1936, auth spy
  conftest :16, rollback tests :335/:430/:471) except G1,
  never committed; (6) omission re-closed via the importer
  census — no new bridge importer, no nest.
- No index change — CONFIRMED. The index row lists the 8
  covered files without schema.py (dry-0_0_15.md:303); R7
  adjudicates schema.py OUT with 0 compositions, so it stays
  out and the row needs no edit.

### Dirt attribution (by content, HEAD vs worktree)

- types/resolvers.py: git numstat 45+21 = 66; exactly 11
  boundary-token lines = the F1 instance (import swap, prose
  reword, 3 swaps); the rest is truth/deadline/resource-policy
  dirt — concurrent-external. Family verdicts hold at HEAD
  bytes; the worktree additionally satisfies F1.
- tests/types/test_resolvers.py: git numstat 85+19 = 104 (my
  plain-diff instrument splits the same bytes 86+20 = 106;
  identical bytes, algorithm split — 104 stands): the G1 gate
  + surrounding drift.
- auth/mutations.py: exactly one boundary-token hunk, the
  owner import line gaining `_disposed_awaitable`
  (awaitable-refusal family); call sites untouched.
- querysets.py, permissions.py, orders/sets.py, filters/sets.py,
  mutations/resolvers.py, testing/client.py, schema.py,
  auth/queries.py, forms/resolvers.py,
  rest_framework/resolvers.py, connection.py, consumers.py:
  ZERO boundary-token hunks — all dirt concurrent-external;
  every verdict holds at both states.

### Zero-edit vs ITEM_BASELINE

Before this append, the artifact was byte-identical to
ITEM_BASELINE (W1's section predates the pinning); before ==
consolidate == verify on all 16 files above. `git diff
ITEM_BASELINE -- .` then showed exactly one file,
docs/dry/dry-0_0_15.md (+53): Worker-0's own s20
dispatch/submission record, concurrent-ledger churn, not item
edits. Item diff on tracked package + tests is 0 bytes; this
section + the Status flip are the only tracked touches.

### Defects

None. The HEAD trio-inline state is the owed F1 consolidation,
not a defect (behavior-identical spelling duplication, no
failing oracle). No omission reaches a wire input.

### Pending execution

None. Static re-trace; no tracked change to prove. Prior
P1/P2/N1 stand as prior evidence; re-execution is owed only
with the re-landing.

### Verdict (Worker 2)

`Status: verified`. Every row survives on independent
evidence: owner + rule, 5-file/10-call census (each call site
scope-mapped), R7 signature-impossibility with 0 compositions
and stated home docstrings, R5 supersede, s13 m2 strengthened
(zero `-S` commits; run-2 row stands as a worktree entry), s13
R1 line-for-line, F1+C2 owed-not-landed with the re-landing
framing judged correct, R1's corrected difference from
installed asgiref source, R1/R4 homes unlanded at both states,
C3 zero-nests by AST map, matrix re-discharged, dirt
attributed by content, all three states fingerprinted, zero
edits. No index change (schema.py stays out). Closeout prose
still owed: R1 clause at `testing/client.py::login`, R4 clause
at `connection.py` + owner mirror.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[consumers]: ../../django_strawberry_framework/consumers.py
[filter-sets]: ../../django_strawberry_framework/filters/sets.py
[mutation-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[order-sets]: ../../django_strawberry_framework/orders/sets.py
[permissions]: ../../django_strawberry_framework/permissions.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[schema]: ../../django_strawberry_framework/schema.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[type-resolvers]: ../../django_strawberry_framework/types/resolvers.py

<!-- tests/ -->
[test-resolvers]: ../../tests/types/test_resolvers.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
