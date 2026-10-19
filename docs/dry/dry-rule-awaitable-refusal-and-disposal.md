# DRY review: `awaitable-refusal-and-disposal`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

The family owns one rule: a refused awaitable is detected, then released
without awaiting it (native coroutine closed, future cancelled, any other
awaitable untouched — it has no standard cleanup protocol), and only then
refused with the seam's own tail (a raise or, at one seam, a sentinel).
Owner: `django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`
(the kind inventory), with two composed halves beside it in the same module:
`::_disposed_awaitable` (detect + dispose, bool; the raise stays at the
caller) and `::reject_async_in_sync_context` (detect + dispose + raise
`SyncMisuseError`). The owner module is untouched by this item — the
consolidation migrates the last two inline members to calls.

Census (roles per DRY.md vocabulary; every pin re-derived on current bytes,
holding artifacts cited as evidence only):

- **Definition (1, post-change):**
  `django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`.
- **Former inline definitions, now consumers (F1):**
  `django_strawberry_framework/auth/mutations.py::_authenticated_actor_or_none`
  (was `isawaitable` → duck-typed `.close()` → anonymous; now
  `if _disposed_awaitable(...): return None`);
  `django_strawberry_framework/routers.py::_factory_application` (was
  coroutine-gated `.close()`; now unconditional `_dispose_sync_awaitable`
  with the coroutine gate kept for the hint — R1).
- **Composed consumers (verified, untouched):** the owner's own callers
  (`::reject_async_in_sync_context`, `::_apply_sidecar_sync`,
  `::_apply_sidecar_async` residual arm, `::apply_type_visibility_sync` via
  the raising guard, `::apply_type_visibility_async` nested arm,
  `::reject_awaitable_sync_source`, `::reject_residual_async_source`);
  `django_strawberry_framework/relay.py` (2 refusal seams:
  `DjangoNodeField` tail, `DjangoNodesField` sync loop);
  `django_strawberry_framework/list_field.py` + `connection.py` (colored
  `async_guard=` wiring through `::prepared_resolver_source` /
  `::_prepare_pipeline_source`);
  `django_strawberry_framework/utils/permissions.py::invoke_permission_method`
  (F-AWAIT: 1 guard call, zero inline spellings — re-verified);
  `django_strawberry_framework/mutations/permissions.py::_require_sync_bool_auth_result`
  (single body behind both flavor bases; consumers-of-consumers:
  `mutations/resolvers.py::authorize_or_raise`, both `check_permission`
  defaults, `DjangoModelPermission.has_perm`).
- **Oracles:** `tests/utils/test_querysets.py` (owner pins incl.
  future-cancel); `tests/auth/test_queries.py` (auth seam incl. 2 new rows);
  `tests/auth/test_mutations.py` (logout ok-capture + async-gate rows, same
  helper); `tests/test_routers.py` (factory matrix incl. 1 new row);
  `tests/mutations/test_permissions.py`, `tests/utils/test_permissions.py`,
  `tests/test_relay_node_field.py`, `tests/test_connection.py` (seam pins).
- **Projections:** owner + seam docstrings (updated at the 2 seams);
  `docs/GLOSSARY.md` SyncMisuseError entry and archived specs (frozen;
  behavior they pin is preserved, no update owed).
- **Excluded on fresh body reads (not second definitions):** await-completion
  sites (`types/resolvers.py` ×3, `optimizer/extension.py::_async_optimize`,
  `connection.py` count-attach, `relay.py` async branches,
  `_graphql_core_patches.py` — R2); the async-iterable refusal
  (`::reject_async_iterable_in_sync_context` + `::is_async_only_iterable` —
  adjacent sub-rule, proposed index row, no disposal possible: an async
  generator has no sync cleanup protocol);
  `utils/execution_mode.py::async_execution` third-state raise (no value in
  hand, nothing to dispose); `utils/typing.py::is_async_callable`
  (callable-color prediction, already indexed file-local);
  `middleware/request_body.py` color dispatch; `consumers.py` task cancel,
  lease/stream/ledger `.close()` (resource lifecycles, not awaitables).

## Verification

### Matrix

1. **Cross-flavor policy mirroring** — read all write flavors (model / form /
   serializer resolvers compose the owner via `_require_sync_bool_auth_result`
   and the visibility runners; their `*_ASYNC_RECOURSE` constants compose
   `::sync_pipeline_recourse`). Recourse wording is a separate, already
   rejected family (`sync-boundary-recourse-wording`) — R4, untouched.
2. **Sync/async twins** — the owner already unifies both colorings' disposal
   (sync raise-guards AND async nested/residual arms compose it). The twin
   that must not merge is async *completion* (await sites) — R2 stands,
   distinguished below on fresh reads.
3. **Derived knowledge** — coroutine detection was spelled twice
   (`inspect.iscoroutine` in the owner, `truth.is_instance(..., CoroutineType)`
   in routers). Post-change the disposal-kind inventory lives only in the
   owner; routers' remaining truth-check selects the *message* (R1), a
   different rule. The `callable()` floor is routers R6's, not this family's.
4. **Inverse / round-trip pairs** — disposal is one-way (no inverse); the
   refusal's other half (completion) is the rejected R2 pair. No pair inside.
5. **Contracts in another medium** — oracles spell every kind-behavior
   independently (coroutine-closed, future-cancelled, exotic-undispatched,
   hint-present/absent, anonymous-collapse); none reads the owner. Projections
   updated at the 2 seams only.
6. **Enforcement by omission** — enumerated every boundary that can meet an
   awaitable: get_queryset sync runner, read + write permission gates,
   sidecar `apply_sync`, list + connection sync sources, Relay node/nodes,
   auth actor, routers factory, async nested/residual arms — all compose the
   owner post-change. Omissions reasoned, none a gap: iterable refusal (no
   sync protocol exists), third-state raise (no value), completion sites (R2).

### Enumeration

Instrument: grep token sweeps over `django_strawberry_framework/**/*.py` for
`isawaitable`, `iscoroutine(`, `isfuture`, `CoroutineType`,
`_dispose_sync_awaitable`, `_disposed_awaitable`,
`reject_async_in_sync_context`, `.close()`, `.cancel()`, plus a
`SyncMisuseError`-raise census. Population closed: 16 `isawaitable` call
sites post-change (6 owner-internal + 2 relay refusal pre-checks, all
composed; 8 completion sites — R2), 2 `iscoroutine(` (owner kind-label +
owner), 1 `isfuture` (owner), 1 `CoroutineType` (routers hint gate — R1),
zero awaitable `.close()` outside the owner. Disposal compositions: 9
boundaries (5 direct owner calls + 4 via the bool half), 1 definition.

### Challenges

- **X1 — kinds: "a refused future must be released, not dropped."**
  Before: 3 definitions (owner already cancels; auth + routers must each gain
  the arm — the file items' own C1 probes). After: 1. The consolidation proof.
- **X2 — protocol: "refusal must never run consumer code."** Before: 2
  definitions of exotic handling (owner ignores; auth duck-typed `.close()`
  dispatches). After: 1.
- **X3 — tail separation: "reword the routers hint / change the anonymous
  collapse."** Before and after: 0 disposal definitions move — tails stay at
  callers by design (the bool half's documented split). Proves the seam tails
  are not definitions. Reverse ("disposal gains a kind"): 1 after.

## Findings

### F1 — inline disposal ×2 composed onto the owner (CONSOLIDATED)

- **Contract + variation.** Release a refused awaitable without awaiting it:
  close coroutines, cancel futures, ignore the rest. Legitimate variation:
  which tail follows (raise type / sentinel / hint) — stays per seam.
- **Sites + roles.** Definition:
  `django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`
  (unchanged). Migrated members: `auth/mutations.py::_authenticated_actor_or_none`
  → `::_disposed_awaitable` (bool half fits: its tail is `return None`, not a
  raise); `routers.py::_factory_application` → `::_dispose_sync_awaitable`
  unconditional (hint gate kept — R1). Consumers/oracles/projections: per the
  census above.
- **Challenges.** X1 3→1, X2 2→1, X3 0 (separation proof).
- **Owner + lifetime.** `utils/querysets.py` (existing; the neutral substrate
  whose docstring claims cycle-safe wide reuse — the new routers edge adds no
  cycle: nothing under `utils/` imports routers/consumers, verified by grep;
  the module's channels-free guarantee holds since the owner needs no
  channels). No stored derivation; disposal is a pure function of its input.
  Cross-module private imports are established convention
  (`mutations/permissions.py::_require_sync_bool_auth_result`,
  `types/finalizer.py::_connection_type_for`, etc.).
- **Migration.** Auth: 5-line inline body → 2-line composed call; `import
  inspect` dropped (sole use); import extended; docstring re-points to the
  owner with the kind table. Routers: gated `.close()` → unconditional owner
  call below the kept hint gate; comment re-points, keeping the `-W error`
  rationale verbatim; import added. Owner untouched.
- **Distinct behavior.** Two intentional deltas, both in the direction the
  rule prescribes: (a) refused futures are now cancelled at both seams
  (previously dropped pending); (b) exotic awaitables are no longer
  `.close()`-dispatched at the auth seam (previously ran consumer code).
  Coroutine behavior, both error shapes, the coroutine-only hint, and the
  anonymous collapse are byte-identical. The generator-based-coroutine dusty
  corner (duck-close covered it on paper, owner does not; unreachable without
  deprecated APIs, no test anywhere pins it): accepted variation, trigger
  below.
- **Behavioral proof.** `execution-verified` throughout (default cell; sharded
  + pg inapplicable by construction — touched paths reach no database, alias,
  or dialect decision; Worker-2 judges): full `tests/auth/test_queries.py` +
  `tests/auth/test_mutations.py` (107 passed) and full `tests/test_routers.py`
  (208 passed) in the workspace copy, plus a 5-node shared-tree confirmation
  (3 new + 2 nearest oracles). Each new oracle names the wrong result it
  rejects (pending future, dispatched close). Failability (negative control):
  narrow-inline mutants fail exactly the declared sets and nothing else —
  auth mutant 2 failed / 2 passed, routers mutant 1 failed / 1 passed, restores
  sha256-proved. Run ids under Implementation.
- **Structural gate.** The new behavior oracles are the bypass gate for the
  historically observed drift (narrow re-inlining — both members were narrow):
  any seam that stops composing the owner fails them, proved by the mutants.
  A behavior-identical hand copy is deliberately ungated (no bespoke identity
  assertions per helper); trigger: a third inline copy, or a correct-copy
  bypass observed, reopens this with a principle-9 census.
- **Coupling.** None.
- **Freshness.** Worktree (post-edit)
  `auth/mutations.py 31c4e643…`, `routers.py b85953fd…`,
  `utils/querysets.py 8fc556d5…` (untouched; HEAD `3616927d…`),
  `tests/auth/test_queries.py 47865155…`,
  `tests/test_routers.py c32a8aba…`; HEAD blobs for the two production files
  `d1a59c44…` / `7d5e4814…`; consumer + excluded-module hashes in the
  Implementation record. File-item freshness values are NOT inherited (auth
  F1's 2-copy + `suppress` census is stale — concurrent work simplified the
  seam to 1 copy without `suppress` before this item; routers F1's
  `inspect.iscoroutine` spelling is now `truth.is_instance`). Contract
  sources: owner docstrings (universality claims, now true), frozen spec-046
  prose (pinned behavior preserved).
- **Reconsideration triggers.** (a) A supported consumer producing
  generator-based coroutines → extend the owner's kind inventory (one edit).
  (b) Adversarial `__class__` spoofing entering the threat model → revisit
  detection hardening coherently (detection + disposal together; hardening
  one disposal call alone fixes nothing since every `isawaitable` shares the
  exposure). (c) Correct-copy bypass observed → principle-9 census gate.

### R1 — routers hint gate stays inline (REJECTED consolidation)

The kept `truth.is_instance(application, types.CoroutineType)` check selects
the *message* (`_ASYNC_FACTORY_HINT` is coroutine-specific prose: "A coroutine
object is what an `async def` factory returns"), not the disposal. Contract
difference: message selection varies per seam and per kind; disposal does not.
Folding the gate into `_disposed_awaitable`'s bool would mis-hint futures.
Trigger: the hint ever becomes kind-generic — inline the gate into the
disposal call then.

### R2 — Executor-residual completion (REJECTED, stands)

Fresh distinction, not inherited: `_graphql_core_patches.py` AWAITS an
executor-internal residual (completion is the only correct handling there);
this family REFUSES consumer-returned awaitables at sync/async boundaries
(dispose without awaiting — an unbounded chain must never be recursively
consumed). Opposite actions at different layers with different reasons to
change; the remaining package await sites (`types/resolvers.py`,
`optimizer/extension.py`, connection count-attach, relay async branches)
complete rather than refuse for the same reason. Trigger as recorded in File
`_graphql_core_patches.py` R2.

### R3 — owner learns duck-typed `.close()` (REJECTED)

The reverse consolidation (generalize the owner to auth's old duck-type)
would run arbitrary consumer `close()` methods at every security boundary
(get_queryset, permission gates). The owner's "no standard cleanup protocol"
for exotics is the safer rule; the auth seam adopts it. Trigger: a cleanup
protocol for exotic awaitables standardizes — extend the owner then.

### R4 — sync-boundary recourse wording (OUT OF FAMILY)

Already rejected as its own family; the write-flavor recourses compose
`::sync_pipeline_recourse` while permission/Relay wordings deliberately do
not (4-clause difference). Untouched.

## Defects

None. The two behavior deltas (future-cancel, exotic no-dispatch) are the
consolidation's own contract changes, each pinned by a new oracle and proved
by mutant; no contract source outside the family constrains them.

## Judgment

One rule, now one definition. The package-wide sweep found exactly two
second definitions of awaitable disposal (both named by their holding file
items as consolidation input, both re-derived fresh on current bytes) and no
other; both now compose the owner, with the full kind-contract pinned at each
seam and the narrow-bypass mutants failing exactly the new rows. The
hint-gate, completion sites, recourse wording, and the duck-close generality
each carry a contract difference and a trigger. Ready for verification.

## Implementation (Worker-1)

Tracked changes (all via audited `workspace.py run` commands at
`dry/dry-rule-awaitable-refusal-and-disposal/consolidate`; the shared tree
was never edited directly except this artifact):

- `django_strawberry_framework/auth/mutations.py`
  (`_authenticated_actor_or_none` + imports): inline disposal → composed
  call; `import inspect` dropped; docstring kind table. (+7/−8)
- `django_strawberry_framework/routers.py` (`_factory_application` +
  imports): gated close → unconditional owner call under the kept hint gate;
  comment re-points. (+10/−6)
- `tests/auth/test_queries.py`: `import asyncio` + 2 oracles
  (future-cancelled-and-anonymous; exotic-close-never-runs). (+56/−0)
- `tests/utils/test_querysets.py`, owner, and all other consumers: untouched.
- `tests/test_routers.py`: 1 oracle (future-cancelled, contract-without-hint).
  (+29/−0)

Item-scoped diff vs `ITEM_BASELINE=afb40409…`: the 4 files above only
(+102/−14); concurrent paths since dispatch (`extensions/debug.py`,
`tests/extensions/test_debug.py`, plan, review doc) untouched. HEAD unmoved
(`0c0537e2`). Landed bytes are byte-identical (`cmp`) to the proven copy.

Proofs (workspace copy `slot-2`, cell default; package digest
`sha256:bd5634c8…` for the edited tree): edits
`dry-20260929T174922-1a3479`; `ruff check --fix` clean
(`dry-20260929T174927-ed1433`); `ruff format` no-op
(`dry-20260929T174933-bd19ae`); `check_trailing_commas.py --check` 0
violations (`dry-20260929T174937-134be1`); auth files 107 passed
(`dry-20260929T175146-068002`); routers file 208 passed
(`dry-20260929T175159-049a32`); failability `prove` both pinned with exact
declared sets and sha256-proved restores
(`dry-20260929T175240-432a9e`); landing `dry-20260929T175309-e5ba50`. The
copy venv arrived corrupt (pytest + typing_extensions files missing) and was
rebuilt from the lockfile (`dry-20260929T175120-601e60` + auto-resync) before
any test ran. Shared tree: `ruff check`, `ruff format --check`,
`check_trailing_commas.py --check` all clean on the 4 paths (read-only);
single authorized focused run, 5 nodes green.

Test tier: `tests/` — a custom awaitable `is_authenticated` and an ASGI
factory return are both undrivable over live fakeshop HTTP (stock `User`,
no `asgi.py` mount); the files' own docstrings already claim this residue,
and the new rows mirror the neighboring oracles' shape.

Freshness (worktree post-edit `git hash-object`): querysets `8fc556d5…`,
auth/mutations `31c4e643…`, routers `b85953fd…`, relay `f5760b45…`,
connection `1fca6266…`, list_field `f5b0183e…`, utils/permissions `1c9cfd39…`,
mutations/permissions `55e5edf8…`, mutations/resolvers `c9cff059…`,
forms/resolvers `a1000f21…`, rest_framework/resolvers `c49ce3c2…`,
types/resolvers `640905c6…`, optimizer/extension `39a8739c…`,
execution_mode `9805cdaf…`, typing `a672cd6b…`, middleware/request_body
`3bc5c673…`, consumers `0791c04a…`, _graphql_core_patches `90ac4f3c…`,
tests/auth/test_queries `47865155…`, tests/test_routers `c32a8aba…`,
tests/utils/test_querysets `77d45a48…`, tests/mutations/test_permissions
`a4472aee…`, tests/utils/test_permissions `71e1ff4b…`,
tests/test_relay_node_field `d4ce0c7d…`, tests/test_connection `8e08b23f…`.

## Independent verification (Worker-2)

Procedural note: the artifact arrived as one file, so `## Findings` was
visible before this trace was written. The trace below was still re-derived,
not inherited: every count re-run by fresh grep on current bytes, every cited
body re-read (seams also re-read at `ITEM_BASELINE`), and every proof
re-executed at `dry/dry-rule-awaitable-refusal-and-disposal/verify-1`.
Reconciliation with `## Findings` follows the trace.

### Own trace

- **Rule re-derived:** a refused awaitable is detected (`isawaitable`),
  released without awaiting (coroutine `.close()`, future `.cancel()`,
  exotic untouched), then refused with the seam's own tail.
- **Sites found (fresh grep):** 16 `isawaitable` call sites =
  `types/resolvers.py` x3 + `optimizer/extension.py` x1 (all completion:
  bodies `await` the value) + `utils/querysets.py` x6 (172 raising guard,
  197 bool half, 3100 sidecar-sync refusal, 3133 non-awaitable guard,
  3139 sidecar-async residual refusal, 4368 async-runner await + nested
  disposal) + `connection.py` x2 (completion: await/attach) + `relay.py`
  x4 (608 + 730 refusal pre-checks composing the raising guard; 616 + 718
  completion). `iscoroutine(` x2 (both owner: kind-label 173, disposal
  212), `isfuture` x1 (owner 214, via `asyncio.isfuture`), `CoroutineType`
  x1 (routers hint gate 288). Awaitable `.close()`/`.cancel()` outside the
  owner: zero — remaining hits are lease/stream/ledger/connection/task
  lifecycles plus two `aclose` async-iterator cleanups (resource_policy,
  consumers), all a different rule.
- **Definition count:** post-change exactly 1 —
  `utils/querysets.py::_dispose_sync_awaitable` (kind inventory) with its
  two composed halves `::_disposed_awaitable` and
  `::reject_async_in_sync_context`. Pre-change (re-read at baseline):
  3 on the future-kind axis (owner + auth duck-close + routers
  coroutine-only close), 2 on the exotic-protocol axis (owner ignore vs
  auth duck-dispatch). X1 3→1, X2 2→1 confirmed on my own reads.
- **Roles:** definition = owner; the two migrated seams are now consumers
  (auth via the bool half — correct fit, its tail is `return None`;
  routers via the direct call under the kept hint gate — correct fit, its
  tail is a raise with a coroutine-specific addendum); refusal guards,
  Relay seams, sidecar arms, permission gates all compose by call;
  oracles spell literals independently (no test imports the owner; test
  diffs are pure additions, no oracle rewritten).
- **Owner I would choose:** `utils/querysets.py` — the pre-existing kind
  inventory both seams can import without a cycle (verified: nothing
  under `utils/` imports routers/consumers; auth already imported from
  the module). Matches W1. No narrower owner exists: the rule already
  lived there and served six other boundaries.

### Reconciliation with Findings

- **F1 (consolidated):** agree on all points. Migration verified hunk by
  hunk: auth 5-line inline → 2-line call, `import inspect` dropped with
  zero remaining uses; routers gated `.close()` → unconditional owner
  call with the hint gate and the `-W error` rationale verbatim.
- **Equivalence + the 2 deltas:** detection predicate is byte-identical
  (`inspect.isawaitable` both seams, before and after), classification
  identical (always anonymous / always raise), `received` still described
  before disposal, the callable-floor ordering untouched. Delta (a)
  futures now cancelled: in the rule's direction (the owner's own
  docstring already promised it) and pinned at both seams. Delta (b)
  exotics no longer `.close()`-dispatched: in the rule's direction (the
  owner's "no standard cleanup protocol") and pinned at auth, the only
  seam that dispatched. The generator-based-coroutine dusty corner is a
  real accepted variation with a trigger; unreachable without deprecated
  APIs and still classified anonymous either way.
- **R1 (hint gate stays inline):** agree — contract difference
  (message selection vs disposal) verified: the gate now only sets the
  addendum, disposal is unconditional below it; folding would mis-hint
  futures. Trigger adequate.
- **R2 (completion stands):** agree on fresh reads — every await site
  completes (`types/resolvers.py` x3, optimizer, connection x2, relay
  616/718) including `_graphql_core_patches.py` (awaits an
  executor-internal residual), the opposite action at a different layer.
- **R3 (owner must not learn duck-close):** agree — generalizing the
  owner would run consumer `close()` at security boundaries; trigger
  adequate.
- **R4 (recourse wording out of family):** agree — separate constants
  observed, untouched by the diff.
- **Enumeration:** every member confirmed individually above; the "9
  boundaries (5 direct + 4 via bool half)" parses as 5 textual direct
  calls (174, 199, 3101, 3140, routers 298) + 4 bool-half consumers
  (auth 453, 4370, 4398, 4428) — matches grep exactly.
- **Matrix:** discharged against the real surface, axis by axis, on my
  own reads (write flavors via `_require_sync_bool_auth_result`;
  twins unified in the owner with completion distinguished; derived
  detection now single-sourced with the message check separated;
  one-way disposal; oracles independent; omission census closed with
  iterable/third-state/completion exclusions each reasoned on a body I
  read). No unsearched axis hides behind the found consolidation.

### Gates and negative controls (re-executed, not trusted)

- Focused 5-node run (3 new + 2 nearest oracles) in my own copy:
  5 passed (`dry-20260929T180301-095b8e`). The copy venv arrived corrupt
  (same `pytest`/`_pytest` breakage W1 reported); wiped and rebuilt from
  the lockfile before any test ran.
- Failability re-proven with my own manifest
  (`/tmp/dry_e1_verify1_proofs.json`, mutants derived from the baseline
  bodies I read myself): auth 2 failed / 2 passed exactly the declared
  set, routers 1 failed / 1 passed exactly the declared set, restores
  sha256-proved (`dry-20260929T180411-7e67f5`, exit 0).
- On the routers 1-row pin vs the generic "0 or 1 rows is weakly pinned"
  boilerplate: not a defect. The routers delta is one-dimensional
  (future-cancel only; coroutine behavior is identical under the mutant
  and correctly still passes its pre-existing row), so exactly one row
  *can* fail. The gate fails exactly for the divergence it guards
  (narrow re-inlining), which is what DRY.md requires.
- Sharded + pg `inapplicable by construction`: accepted — the touched
  production paths (actor classification, router construction) reach no
  database, alias, or dialect decision. No `proof:`/`gate:` entries
  remain; nothing is `execution-deferred`.

### Item-scoped diff vs AGENTS.md

- Scope confirmed: exactly the 4 files, +102/-14, every hunk the
  consolidation or its oracles; no foreign hunks inside the 4 paths.
  Concurrent dirt elsewhere left alone.
- Freshness still bound: all five `git hash-object` values match the
  artifact's worktree fingerprints (`31c4e643…`, `b85953fd…`,
  `47865155…`, `c32a8aba…`, owner `8fc556d5…`).
- `uv run ruff format --check` + `uv run ruff check` on the 4 paths:
  both pass (run by me). `check_trailing_commas.py --check`: 0
  violations (incl. non-ASCII 0). Comments cite `path::Symbol`, no
  process provenance. `tests/` tier justified: the file docstring
  already claims the awaitable-`is_authenticated` residue, the new rows
  mirror the neighbors' shape exactly (no model rows, so no seed
  helpers — same as neighbors), and the routers test names its live
  sibling.

### Sub-rule and index rows

- `async-iterable-sync-refusal`: record accepted. Single definition
  (`::reject_async_iterable_in_sync_context` + `::is_async_only_iterable`
  at `utils/querysets.py:424`/`368`) and all four consumers verified
  composed by call (list_field, connection, resource_policy). "Record
  without dispatch" is the right call — there is nothing to consolidate.
- Index rows: family tick → verified; ADD row as written; Owned-changes
  rows match the 4 touched files; no defects, no coupling, no repo
  scratch (W1 scratch + my manifest both under `/tmp`).

### Defects

None found. No `(Worker-2)` entries.

## Index rows for Worker-0

- Tick Family `awaitable-refusal-and-disposal` in [the plan][plan] →
  verified on Worker-2's verdict (owner confirmed
  `django_strawberry_framework/utils/querysets.py::_dispose_sync_awaitable`;
  members `auth/mutations.py`, `routers.py` migrated to consumers).
- ADD row: `async-iterable-sync-refusal` |
  `django_strawberry_framework/utils/querysets.py::reject_async_iterable_in_sync_context`
  (+ `::is_async_only_iterable` predicate) |
  `utils/querysets.py`, `list_field.py`, `connection.py`,
  `resource_policy.py` | single-owned, no family item (recommendation: record
  without dispatch — definition + all four consumers verified composed by
  call on current bytes).
- `## Owned changes` rows: `django_strawberry_framework/auth/mutations.py`
  (this item — `_authenticated_actor_or_none` composes
  `_disposed_awaitable`; imports; docstring);
  `django_strawberry_framework/routers.py` (this item —
  `_factory_application` composes `_dispose_sync_awaitable`; import;
  comment); `tests/auth/test_queries.py` (this item — 2 oracles);
  `tests/test_routers.py` (this item — 1 oracle).
- No defects to home. No coupling. No repo scratch (edits + proofs ran in
  the workspace copy; `/tmp/dry_e1_apply.py` + `/tmp/dry_e1_proofs.json` live
  outside the repo).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
