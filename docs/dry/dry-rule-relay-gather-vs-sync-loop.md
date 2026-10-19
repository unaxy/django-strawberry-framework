# DRY review: `relay-gather-vs-sync-loop`

Status: verified
Run: 0.0.15 2026-10-11-18

## System trace

Target: `DjangoNodesField._resolve` in
`django_strawberry_framework/relay.py` — the async `_gather` closure
(:807-828) vs the sync loop (:829-848). Read the whole module in full,
plus `types/relay.py` fetch defaults (:985-1176), `reject_async_in_sync_context`
(`utils/querysets.py:202-232`), `async_execution()`, and spec-032. Shared
before the `:799` dispatch: grouping (`slots`/`_node_id_slot`, coercion gate,
`groups`, `positions`, :785-798). Shared inside both loops by name:
`resolve_nodes` call, `_check_nodes_result`, `_stamp_node_type` listcomp,
`_interleave`. The loops differ in exactly one statement each: `await result`
vs `reject_async_in_sync_context(...)` (dispose + raise). Whole-package
censuses, re-derived fresh: `resolve_nodes(` 2 call sites (both here);
`_check_nodes_result` 1 def + 2 calls; `_interleave` 1 def + 2 calls;
`_stamp_node_type` 1 def + 4 calls (single sync, `_await_and_stamp`,
both loops); `_SYNC_RESOLVER_RECOURSE` 1 def + 2 uses;
`asyncio.gather(` 0 in `relay.py`; `async_execution()` 2 calls here
(single :678, batch :799). Standing oracles pin both colors:
`tests/test_relay_node_field.py` (sync-override-under-async,
async-override-under-sync refusal, wrong-length) and live
`test_library_api.py` (mixed-type batch sync + async, query counts).
Prior triggers checked, not substituted: file-relay R2 (third arity —
unfired) and types-relay prelude-twin-spells (single-slot seam + await
boundary — holds). Attribution: `relay.py` is dirty vs HEAD with ~15
hunks; only the `typed-globalid-decode` trigger docstring matches the
`## Owned changes` ledger, the rest match neither ledger nor `## Cycle
baseline` (external, concurrent); item-baseline diff is empty, so all
dirt predates dispatch. Zero edits made, so no path was stopped mid-edit.

## Verification

### Matrix

1. Cross-flavor: `resolve_nodes` has exactly 2 callers package-wide
   (both loops). `connection.py` `resolve_node(` sites (3) resolve
   single rows, never per-type id batches — different contract.
2. Sync/async twins: the pair itself. Compared by behavior: async
   completes awaitables, sync refuses them; every pure decision is
   already one shared helper. The single-node field defers async
   completion to the executor (`_await_and_stamp` return); batch must
   complete per type before `_interleave` — the color split is structural.
3. Derived knowledge: `node_ids` strings pass through untouched to
   `resolve_nodes`; no name/field set re-derived at either loop.
4. Round-trip: inapplicable — one-directional fetch (ids to rows);
   encode/decode grammar owned by `types/relay.py`.
5. Other media: spec-032 pins the gathering coroutine, per-call
   dispatch, the override contract, wrong-length `ConfigurationError`,
   and sync-awaitable `SyncMisuseError`; oracles assert rows/errors,
   never loop spelling. No second definition in tests or docs.
6. Omission: enumerated both loop members — each carries its color's
   guard (await vs refuse). `_resolve_real_pks_batched` groups
   (:395-407) map coerced values to pks (no fetch/stamp/interleave) —
   different mechanism, not a missing member.

### Challenges

- C1 new grouping rule (cap types, new hole policy): grouping is one
  site above the dispatch (:785-798). Count 1.
- C2 new per-type fetch contract (new kwarg, tuple return): the two call
  lines are consumer sites of one owned contract, not definitions. Count 1.
- C3 new stamp rule: `_stamp_node_type` is 1 def + 4 by-name calls. Count 1.
- C4 new interleave order: `_interleave` is 1 def + 2 by-name calls. Count 1.
- C5 new await-vs-reject discipline: await arm exists only in `_gather`,
  refuse arm only in the sync loop — two rules (complete vs refuse),
  one site each. Count 1 per discipline.
- C6 sequential-vs-gather policy: awaits exist only in `_gather`
  (`asyncio.gather(` count 0); the sync loop is unaffected. Count 1.
- C7 group iteration order (sorted groups): belongs at the single
  grouping site (`groups` is insertion-ordered, built once) — a sane
  change edits 1 site, never both loops. Count 1.

## Findings

### F1 per-type nodes-fetch loop twin (rejected — color-forced, pure decisions shared)

- **Contract + variation.** Ordered batch refetch: per type, call
  `resolve_nodes` once, complete-or-refuse the `AwaitableOrValue`,
  validate, stamp, reassemble. Varies only on executor color.
- **Sites + roles.** Definitions: `_gather` loop (async completion) +
  sync loop (sync refusal) — one rule each. Owners composed by name:
  check, stamp, interleave, refusal, slot. Consumers: the two call
  lines. Oracles: five rows in the trace. Projection: spec-032.
- **Challenges.** C1–C7: every count is 1.
- **Owner + lifetime.** No new owner: each color owns its completion
  statement; pure decisions stay put (principle 7). Nothing stored.
- **Migration / shrinkage / coupling.** None; +0/-0 (`b032a3eb` diff empty).
- **Distinct behavior.** `await` (complete) vs dispose-and-raise
  (refuse); sequential awaits vs none. Recorded at the loop comments.
- **Behavioral proof.** Standing oracles, both colors: sync-override-
  under-async, async-override-under-sync refusal, wrong-length, live
  mixed-type order + counts. Static-reviewed (zero-edit; not re-run).
- **Negative control.** The standing refusal oracle refuses bypass
  behaviorally (`..._raises_sync_misuse`); nothing further owed.
- **Freshness.** Blobs: `relay.py` `edfa8d6d` (dirty, external hunks,
  baseline diff empty), `types/relay.py` `3b4447ae`, `querysets.py`
  `f9267729`, node-field tests `122d5398`, live library `b9aa189d`;
  HEAD `c37a08a0`. Population: whole package (censuses above).
  Contract sources: spec-032; prior file-relay R2.
- **Considered shared forms, refused.** (a) One body + adapters: needs
  a generator-driver protocol or mode flag — barred machinery; the
  principle-5 `connection.py` precedent answers this axis identically.
  (b) Extract the 3-line tail: +1 helper, -0 obligations (principle 11).
  (c) `_call_resolve_nodes` wrapper: two consumer sites ≠ two definitions.
- **Sub-rules named for the index.** `relay-batch-fetch-loop-color-twin`
  (rejected; T1 shared completion primitive, T2 identical logic accretes,
  T3 colorless drift). `relay-resolve-nodes-call-twin` (rejected; trigger:
  call lines diverge). `relay-batch-pk-mapping-loop` (rejected-pair;
  trigger: it starts fetching/stamping rows).

## Defects

None. The target's contracts all hold as read: `_interleave` total
over both branches' output, third-state refusal before ORM work on
both entries, `result` vs `rows` a narrowing rename with identical
semantics, every group non-empty by construction.

D1 (Worker-2, artifact-shape, verdict-neutral): `## Pending execution`
is present with a `None.` placeholder; DRY.md says the section is absent
when no proof or witness is owed. Zero-edit lists nothing either way, so
the fix is deleting the 3-line section at closeout. Suggested home:
Worker-0 closeout (no production owner). Fixed at closeout: section deleted.

## Judgment

Zero-edit: the twin loops are two color-forced completion rules
sharing every pure decision by name; all seven change counts are 1,
both colors are oracle-pinned, and every sharing shape needs barred
machinery. No second definition, no drift, no security rule duplicated.

## What shrinks

Nothing — this item is a proved zero-edit, so this section records what was
measured and why each considered consolidation fails the bar instead of a
reduction figure.

Measured population (whole package, fresh at HEAD `c37a08a0`). The
nodes-fetch rule has exactly two loop bodies, both inside
`DjangoNodesField._resolve`: the `_gather` coroutine (:807-828) and the sync
loop (:829-848). Every other line of the rule is already single-owned:
grouping (:785-798, one site), `_check_nodes_result` (1 def + 2 calls),
`_stamp_node_type` (1 def + 4 calls), `_interleave` (1 def + 2 calls),
`reject_async_in_sync_context` (1 def, relay uses 2 of its package-wide
calls), `_SYNC_RESOLVER_RECOURSE` (1 def + 2 uses). `resolve_nodes` is
called from exactly 2 sites (both loops); its contract is defined once in
`types/relay.py` (`_resolve_nodes_default` + `_resolve_nodes_async` +
`_order_nodes` + the `_RELAY_RESOLVER_DEFAULTS` table) and projected once in
spec-032. `asyncio.gather(` count in `relay.py` is 0 — the sequential-await
discipline holds by inspection, not just by comment.

What each considered form would move, and why it fails. (a) One loop body
with color adapters: the two bodies differ in one statement each (`await
result` vs dispose-and-raise), and the statements differ in kind, not
degree — a sync body cannot await, an async body must not refuse. Fusing
them needs either a generator-driver protocol (the body yields each fetch
result and receives the completed rows — a new driver plus an implicit
yield/receive contract for a 6-line loop) or a mode flag threading color
through a shared helper. Both are machinery the bar explicitly bars, and
neither removes a change obligation: grouping, check, stamp, and interleave
changes still land at their single owners either way. DRY.md principle 5
names this exact axis with `connection.py` as the same correct answer (two
colored bodies sharing pure decisions). (b) Extracting the identical
check-stamp-compose tail (`per_type[...] = [stamp... for ... in
check(...)]`, ~3 lines per site): net effect is +1 helper, -0 obligations —
a principle-11 abstraction with no responsibility (it names no contract, it
just re-spells two compositions that already read by name). (c) A
`_call_resolve_nodes` wrapper for the two identical call lines: the lines
are consumer sites of one owned contract, and DRY.md is explicit that two
invocations of one rule are two enforcement sites, not two definitions (the
`pipeline_write_phase` precedent). (d) Extending the merge to the
single-node field (R2's considered form): already rejected with an unfired
trigger (no third arity), and the single field's executor-deferred async
shape is a different completion mechanism from batch's complete-before-
interleave. (e) Merging with `_resolve_real_pks_batched`'s grouping loop:
different mechanism (pk mapping, no fetch/stamp/interleave) sharing only
the word "groups" — textual coincidence, not a rule.

Why no test was added. A consolidation owes a behavioral proof that fails
on a real wrong result; a rejection owes the standing oracles that already
pin both sides. Both colors are pinned: async completion (including the
sync-override-must-not-await arm) by
`test_nodes_async_with_sync_consumer_resolve_nodes_override` plus live
`test_nodes_batch_mixed_types_async`; sync refusal by
`test_nodes_sync_with_async_consumer_resolve_nodes_raises_sync_misuse`;
shape validation by `test_nodes_consumer_resolve_nodes_wrong_length_raises`;
batch order/holes/cost by the live mixed-batch and query-count rows. No
behavior changed, so no new oracle could fail on anything this item did.

Attribution note for a future consolidation. `relay.py` carries ~15
worktree-vs-HEAD hunks, of which exactly one (the `typed-globalid-decode`
trigger docstring) matches the `## Owned changes` ledger; the rest,
including the grouping-slots hunk and the sync-loop rework inside this
item's target function, match neither the ledger nor the `## Cycle
baseline` and are external concurrent work. The item-baseline diff is
empty, so all of it predates dispatch. Any future item that edits
`DjangoNodesField._resolve` must re-attribute those hunks first; this
zero-edit verdict required no edit and stopped no path.

## Independent verification (Worker-2)

### Own trace (recorded before reading `## Findings`)

Target `django_strawberry_framework/relay.py` at worktree blob
`edfa8d6d` (= item-baseline blob; HEAD blob `337a2d96` differs by
external hunks all predating dispatch; `git diff <baseline> --stat`
names only the plan file).

Sites + roles. Definitions, all in `relay.py`: `DjangoNodesField._resolve`
grouping block (grouping rule, single site before dispatch);
`DjangoNodesField._resolve._gather` (async completion, sequential await);
the sync loop (sync completion, reject-awaitable then finalize);
`_check_nodes_result` (per-type fetch contract, 2 consumers);
`_stamp_node_type` (stamp rule, 4 consumers); `_interleave` (order, 2
consumers); `_await_and_stamp` (single-fetch async boundary, 1 consumer);
`_SYNC_RESOLVER_RECOURSE` (recourse wording, 2 consumers);
`DjangoNodeField._resolve` (distinct single-fetch contract, contrast).
Oracles (external owners, composed by name):
`utils/querysets.py::reject_async_in_sync_context`,
`utils/execution_mode.py::async_execution`,
`types/relay.py::_resolve_nodes_default` / `_resolve_nodes_async`
(callee defaults), `tests/test_relay_node_field.py` (wrong-length,
materialization, stamp oracles). Projection: `mutations/fields.py`
docstring mirror note.

Definition counts per posited change (7). Grouping key / null-hole rule:
1. Per-type fetch contract: 1 (`_check_nodes_result`; call lines are
consumers). Stamp rule: 1. Interleave order: 1. Await-vs-reject: 2 sites,
2 contracts (suspend inside `async def` vs raise-or-pass in sync `def`;
color-forced, no shared body can span the boundary). Sequential policy:
1 (stated once; sweep finds no `asyncio.gather` in the package).
Call-line shape: 2 single-line consumers of the callee-owned contract,
below bar (no real logic per site; inseparable from colored drivers).

Owner I would choose: no move. Grouping, check, stamp, interleave, and
recourse are already single-owned; the two colored drivers stay as loop
bodies (principle-5 two-machines shape, cf. the `connection.py` precedent
cited in-code).

Third-loop sweep (whole package): `resolve_nodes` call sites exactly the
2 under review; singular `resolve_node` callers are the single `_resolve`
plus `connection.py` edge assembly (row-to-node, not a per-type batch);
`_resolve_nodes_default` / `_async` are callee defaults sharing
`_order_nodes` / `_node_values` by name; `_resolve_real_pks_batched`
groups write-path `(type, id_attr)` pk mapping (distinct key, distinct
rule). No third fetch loop.

P11 `_await_and_stamp`: keep. The single `_resolve` is sync `def`
returning a coroutine to Strawberry's executor, so the `await` must live
in an `async def`: the wrapper is the coroutine boundary (effect
isolation), not inlinable. Batch awaits inline because `_gather` already
is the async boundary. Symmetric, honestly kept.

Single vs batch: distinct contracts (singular `resolve_node` to one
node / None / coroutine vs grouped `resolve_nodes` to a positional list;
different override signatures, different failure shapes). Every shared
sub-decision (decode-or-error, typed-match, coerce gate, stamp, recourse)
is already composed by name.

Refused shared forms (own judgment). (a) Shared generator yielding
per-type closures: refused, needs a new driver (barred machinery) while
per-color completion stays duplicated; obscures the sequential policy.
(b) Shared tail `_check_and_stamp(resolved_type, rows, node_ids)`: refused;
shares cleanly as code but removes no change obligation (plausible changes
land in `_check_nodes_result` / `_stamp_node_type` once each; the 3-line
comprehension carries no independently-varying logic), a new name without
responsibility, below bar. (c) Async wrapper for the batch await: refused,
`_gather` already awaits at the innermost async boundary; a hop with no
responsibility.

### Reconciliation (after reading `## Findings`)

Agreements: grouping single-site before dispatch; await-vs-reject as two
rules one site each; single-vs-batch contrast (executor-deferred vs
complete-before-interleave, R2 unfired — re-verified exactly 2
`resolve_nodes` call sites); refused forms (a) generator/driver barred
machinery and (b) 3-line tail a P11 no-responsibility helper. One framing
concession: W1's C2 counts the two call lines as consumers (count 1),
which is the correct DRY.md vocabulary (`pipeline_write_phase`
precedent); my "2 sites below bar" reaches the same verdict under either
framing. One axis swap: my 7th challenge was call-line shape where W1's
C7 is group-iteration order (count 1 at the grouping site) — both valid,
same conclusion. My refused form (c) (batch-await wrapper) differs from
W1's (call-line wrapper); both are valid considered forms, both refused,
no conflict. On the parent's direct question: the tail shares cleanly as
code but removes no change obligation (plausible changes land in
`_check_nodes_result` / `_stamp_node_type` once each; not
security/data/db-routing; not drifted), so the binding bar keeps it a
rejection, not `revision-needed`.

Checks. Matrix: all 6 axes discharged against the real surface; axis-4
inapplicability (one-directional fetch) judged sound; no `### Enumeration`
(family item, correct). Roles and counts confirmed as traced; no oracle
rewritten (zero edits). Scoped diff empty: `git diff <baseline> --stat`
names only the plan file (Worker-0 bookkeeping); new-file check passes
(untracked `truth.py` / `lazy.py` / `_multipart.py` predate the artifact
by ~14h, companions of the pre-dispatch dirt). Principle 8 holds
trivially (zero edits, no observable delta). Fingerprints re-hashed: all
5 match current bytes, HEAD `c37a08a0` confirmed; W1's dirt attribution
verified (baseline blob = worktree blob `edfa8d6d`; grouping-slots and
sync-loop hunks inside the target fn predate dispatch; fingerprints
correctly pin baseline bytes). The 4 named oracle test ids exist at real
`def` lines; the one authorized focused run
(`tests/test_relay_node_field.py --no-cov -n0` via `heavy`, no pressure)
passed 35/35 on current bytes. Sub-rule rows carry contract differences +
triggers (T1-T3 / call-divergence / fetch-trigger); coupling none marked.
Ruff is vacuous (zero-edit, no touched Python paths; artifact is
markdown; not run over `.`). Artifact prose: no banned provenance terms;
raw `:NN` citations permitted here (AGENTS.md scratchpad exemption for
`docs/dry/dry-*.md`); zero cross-file links so no scaffold owed. One
defect filed: D1 (`## Pending execution` present-with-`None` instead of
absent; verdict-neutral).

Verdict: verified. The twin loops are two color-forced completion rules
sharing every pure decision by name; my independent hunt found no third
loop, no shareable decision, and no P11 deletion.
