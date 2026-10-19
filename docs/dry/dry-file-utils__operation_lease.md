# DRY review: `utils/operation_lease.py`

Status: verified
Run: 0.0.15 2026-09-28-7

Item kind: FILE (inventory backstop). No consolidation performed; every rule
the target defines or enforces is homed to a family, a file-local row, or a
rejection. Zero production edits, zero test edits, zero plan edits.

## System trace

Target `django_strawberry_framework/utils/operation_lease.py`: 77 lines, CLEAN.
Worktree blob `10c164b731b381d2b62adb5e2c5ce6b694a53fd0` == HEAD blob, `git
status` names no hunk on this path, and the plan's `## Owned changes` ledger
carries no row naming this file. HEAD is `0c0537e2`, unmoved since dispatch;
`ITEM_BASELINE=d3075d1b06e1fdcff3cee817874c2a05f6a01923` noted. The 398 dirty
paths elsewhere are concurrent work, left alone; every connected file I traced
that carries concurrent dirt was diffed against HEAD and its hunks verified
disjoint from the lease-cited lines (see Freshness).

What the target owns: `OperationLease`, one scope's revocable handle on the
state that scope owns. A `ContextVar` cannot be revoked — `asyncio.create_task`
copies the whole context, and token reset rewrites only the creating context —
so the owner of per-operation state binds the LEASE in place of the payload and
closes it when its scope ends. Every reader asks the lease through `held()`,
so a copied binding answers `None` at the instant the scope ends rather than
when the owner is collected. Token reset stays as cleanup (restoring the
enclosing operation in the owning context); the lease is the authority for
whether what a context holds is still live.

Consumer census (repo-wide grep for `OperationLease` / `operation_lease`,
`.pyc` excluded): exactly four production importers, all composing by name:

- [operation-state][operation-state] — runner scopes (`OperationLease(scope)`),
  per-extension state leases (`OperationLease(ref(state))`), mode leases via
  `bind_operation_mode`; `_bind` / `_unbind` / `_already_bound` own the
  close-first-then-reset discipline.
- [optimizer-context][optimizer-context] — the optimizer execution frame
  (`_FrameScope`, `begin_execution_frame` / `end_execution_frame`,
  `_active_frame`); the owner clears the frame's own mutable containers after
  closing, exactly the posture the lease docstring assigns owners.
- [resource-policy][resource-policy] — the armed request budget (`_BudgetScope`,
  `begin_resource_budget` / `end_resource_budget`, `_armed_budget`,
  `budget_resume_binding` re-binds the same lease across stream resumes).
- [execution-mode][execution-mode] — the carried executor mode
  (`bind_operation_mode` / `current_operation_mode`); the runner owns all
  three undo pieces.

Oracles: no test imports `operation_lease` directly (grep over `tests/` and
`examples/` empty). Behavior is pinned at the consumer seams, independently of
the owner's internals: [test-operation-state][test-operation-state] asserts a
copied context's `nested_scope` lease reads `held() is None` after teardown
from another task (stream-close and throw-and-close rows), plus weakref
release rows; copied-context/outlived-operation rows also exist in the
optimizer, execution-mode, schema, router, orders, and resource-policy suites
and two live `test_query` modules. Projections: the module + class docstrings
(including the ledger-separation paragraph, the durable home of R-LEDGER),
each consumer's copied-context rationale paragraph, and the glossary
per-operation-extension-isolation anchor.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Discharged by search. The target is
   flavor-neutral infrastructure with four consumers across engine, optimizer,
   policy, and mode surfaces; no flavor carries a local revocable-read twin.
   The two same-word candidates were traced and rejected: the orders
   normalization ledger (R-LEDGER, converge) and the sessions actor lock
   (R-LOCK, fresh). No second revocable-read owner exists.
2. **Sync/async twins.** Inapplicable with reason, not by absence: `held()` /
   `close()` perform no I/O and hold no lock, so they are deliberately
   uncolored — called from sync teardowns (`_unbind`,
   `end_execution_frame`) and async paths alike. Coloring the lease would put
   an await point inside teardowns that must run from sync `finally`s.
3. **Derived rather than repeated knowledge.** Discharged. `held()` answers
   the stored slot; nothing re-derives liveness by another means. The
   three identical consumer read shapes (`None if lease is None else
   lease.held()`) compose two owned facts — each site's own `ContextVar`
   default and the one owned `held()` — by name (R-READ, converge with the
   verified execution-mode R1).
4. **Inverse / round-trip pairs.** No pair inside the file. `held`/`close`
   are not inverses: close is terminal, there is no reopen, and the
   lifecycle runs one way (`__init__` settles, `close` ends). Bind/unbind
   pairing lives at each owner (begin/end frame, begin/end budget,
   `_bind`/`_unbind`); the lease owns neither half of any owner's pair.
5. **Contracts restated in another medium.** Counted, all zero-definition:
   four consumer rationale paragraphs + the glossary anchor are projections;
   the test rows above are oracles asserting wire/lifetime behavior through
   the public `held()` seam. A wording change to the lease contract moves
   one definition (here) plus projections, never a second implementation.
6. **Enforcement by omission.** Owner obligation enumerated, no gap with a
   contract source. "Close on every exit path" is owed by each scope owner,
   and each states it: `_bind` unwinds through `_unbind` on `BaseException`;
   `end_execution_frame` closes first and unconditionally; `end_resource_budget`
   closes (adopted bindings keep the lease while ending the binding);
   `bind_operation_mode` hands all three undo pieces to the runner. No spec,
   glossary, owner-prose, or oracle row extends enforcement INTO the lease —
   a lease cannot know its owner's exit paths — so the absence of a guard
   here is the design, not a defect. Not behavior-preserving to add one;
   not proposed.

### Enumeration

Instrument: every name in `ast.Module.body` at HEAD bytes (`10c164b7`, 77
lines). Count: 6 top-level statements. Every member homed; no sampling.

| # | Member | Home |
|---|---|---|
| 1 | Module docstring (ContextVar-copy problem, lease answer, token-cleanup split, ledger-separation paragraph) | FL2 (durable home of R-LEDGER's recorded split) |
| 2 | `from __future__ import annotations` | FL2 |
| 3 | `from typing import Generic, TypeVar` | FL2 |
| 4 | `__all__ = ("OperationLease",)` | FL2 |
| 5 | `PayloadT = TypeVar("PayloadT")` (unexported; zero external importers by grep) | FL2 |
| 6 | `class OperationLease(Generic[PayloadT])`: docstring, `__slots__`, `__init__`, `held`, `close` | FL1 |

6/6 homed: 2 file-local rows, 0 new families, 6 rejections below. O1 (the
`__weakref__` slot) is an observation on member 6, not a home.

### Challenges

- **FL1, revocable handle.** (a) Second payload slot or a closed flag beside
  the slot: 1 definition (here; the no-second-flag invariant is stated in
  the class docstring). (b) Non-idempotent close or a close callback: 1
  definition. (c) `held()` gains a third answer: 1 definition; the four
  consumer `None`-contracts are re-examined as consumers (listed, not
  counted). (d) A fifth leased fact: 0 definitions move — it binds an
  `OperationLease` and composes by name.
- **FL2, module mechanics.** Export `PayloadT`, add a second export, or
  reword the contract prose: 1 definition each.
- **R-LEDGER.** Ledger publish/claim/once-per-pair change: ledger only.
  Lease read/close change: lease only. Fresh structural facts: the ledger
  binds DIRECTLY (`ContextVar[_NormalizationLedger | None]`), `orders/sets.py`
  holds no `OperationLease` import, and close shapes differ (tombstone plus
  two clears under one lock vs one store).
- **R-LOCK.** Mutex semantics change (`async with` discipline, lock order):
  sessions only. `held`/`close` change: lease only. Shared word, disjoint
  verbs.
- **R-AUTH.** Forgery-resistance change (filing, evidence, recall):
  private-state only. Revocation change: lease only. Composition site
  ([operation-state][operation-state] carrier-behind-authority plus
  payload-behind-lease) proves the separation is load-bearing.
- **R-READ.** "A copied context keeps the last mode" (the verified R1
  challenge, re-posed): only that reader moves; runner-scope, budget, and
  frame readers keep fail-closed. No change moves all readers without
  moving `held` itself, which is already one definition.
- **R-BOUNDARY.** Trigger re-checked unfired: still one variable per
  concern, no shared driver; lifetimes still disjoint (chain-entry vs
  operation).
- **R-MANIFEST.** Manifest/type-param change: the owning module only, in
  each of the three modules.

## Findings

### FL1 `operation-lease-revocable-handle` (file-local)

- **Contract + variation.** One scope's revocable handle on state bound in a
  `ContextVar`: `held()` answers the payload or `None` once the owning scope
  ended; `close()` ends the lease here and in every copied context, is
  idempotent, and is one store into a single payload slot with no second
  flag. Varies on payload type only (`Generic[PayloadT]`).
- **Sites + roles.** Definition: target `OperationLease` (sole). Consumers:
  the four importers above (each binds/closes/reads at its own boundary).
  Oracles: the consumer-seam rows in System trace. Projections: target
  docstrings, consumer rationale paragraphs, glossary anchor.
- **Challenges.** Above; counts 1 / 1 / 1 / 0.
- **Owner + lifetime.** Owner is the target (principle 7: narrowest module
  every legitimate consumer already imports; zero production imports of its
  own beyond `typing`). Principle 4: owner = the scope owner via its
  `ContextVar` binding; validity key = the lease held-state; publish point =
  the owner's bind; who may mutate = the owner closes, readers only read;
  invalidation = `close()`, observed in every copied context at that
  instant. Payloads with mutable containers of their own are cleared by
  their owner ([optimizer-context][optimizer-context]`::end_execution_frame`
  is the worked shape), which is the only code that knows the containers.
- **Migration.** None — file item, no consolidation; the rule is already
  single-owned and every site already composes it by name.
- **Distinct behavior.** Terminal close with no reopen; uncolored reads (see
  Matrix axis 2); close idempotent because owners close on every exit path.
- **Behavioral proof.** Static-reviewed: zero-edit trace; the
  copied-context `held() is None` oracles and weakref release rows reject a
  lease that answers past its scope. No execution run (entry authorizes
  none for this trace; nothing was changed to prove).
- **Structural gate.** None proposed. Owner already single; a would-be gate
  ("every per-operation `ContextVar` binds a lease") needs the folder
  item's enumerated variable population plus negative controls, which this
  file item cannot justify. Not claimed as gate-only.
- **Coupling.** None.
- **Freshness.** Target worktree == HEAD `10c164b731b3` (77 lines, status
  clean for the path). Consumers: [operation-state][operation-state]
  worktree `d9ed9cc67f` vs HEAD `b2674a22d2`,
  [optimizer-context][optimizer-context] `dbc3063052` (clean),
  [resource-policy][resource-policy] worktree `cc3f9d80b9` vs HEAD
  `4b69e974de`, [execution-mode][execution-mode] `9805cdaf` (clean);
  concurrent hunks verified disjoint from lease-cited lines (no added or
  removed line mentions a lease; the two grep hits are diff context on the
  import lines). Searched population: whole-package grep for
  `OperationLease` / `operation_lease` (4 importers + definition + glossary
  + kanban constants projection, `.pyc`/sqlite excluded).

### FL2 `operation-lease-module-mechanics` (file-local)

- **Contract + variation.** Single-name manifest (`__all__` admits only
  `OperationLease`), unexported `PayloadT`, annotation-only imports, and
  the module docstring as the contract's prose projection — including the
  ledger-separation paragraph that durably homes R-LEDGER. No variation
  axis; the manifest is this module's surface by construction.
- **Sites + roles.** Definition: target members 1–5. No consumers of
  `PayloadT` (grep: zero external importers). No oracles; the manifest is
  stated, not behavior.
- **Challenges.** Above; count 1 per change.
- **Owner + lifetime.** Owner is the target; no stored derivation.
- **Migration / Distinct behavior / Coupling.** None; see FL1. The
  ledger-separation paragraph stays here per principle 10 (grammar at the
  owner, already present — verified against both bodies, see R-LEDGER).
- **Behavioral proof.** Static-reviewed (zero-edit trace).
- **Freshness.** Same target fingerprint as FL1.

### R-LEDGER `operation-lease-vs-normalization-ledger` (rejected, CONVERGE)

CONVERGE with the verified `orders-ledger-vs-operation-lease` rejection
(File [orders-sets][orders-sets]) on fresh evidence. The ledger is an
append-only attestation TRANSPORT with a write protocol descendants must
use: `publish` appends under a lock (a guard must receive an application
that happened in a child task, a copied context, or a `sync_to_async`
worker thread), `claim` is once-per-(class, input) with fail-closed
disagreement detection, and `close` sets a tombstone plus two clears under
ONE lock acquisition so a descendant observes the open ledger in full or
the closed one, never a half-cleared one. A lease holds one payload and
answers reads — it has no write protocol, no lock, and no claim identity —
so closing it is one store. Shared `close` name, disjoint contracts:
ledger-close exists because descendants may still be publishing INTO it;
lease-close exists because copied contexts may still be READING it. The
change challenges move one side only (see Challenges). Durable home: the
target docstring paragraph (already states the split; verified against
both bodies) plus the orders artifact.
Reconsideration trigger: the ledger's publish protocol is deleted leaving
a pure read-handle behind, or a second mutable-ledger-with-terminal-closure
appears. Neither is present: the worktree ledger still publishes, claims,
and tombstones under its lock.

### R-LOCK `operation-lease-vs-actor-lease` (rejected, fresh)

[sessions][sessions]`::actor_lease` is an `asyncio.Lock` — mutual exclusion
held with `async with`, with a documented lock order (scope session lock
outer, actor lease inner). `OperationLease` has no acquire/release, never
spans an await, and answers reads with payload-or-`None`. Same word,
disjoint verbs: the actor lease serializes actors in time; the operation
lease revokes readability at scope end. (START.md's standing line — a lock
private to one layer is not a synchronization contract — cuts the same
way from the other side.) Reconsideration trigger: either side gains the
other's verb — an acquire/release discipline on `OperationLease`, or a
held-or-`None` read on the actor lock.

### R-AUTH `operation-lease-vs-private-authority` (rejected, fresh)

[private-state][private-state]`::PrivateAuthority` is an identity-keyed
unforgeable store answering "what was settled for this owner" — its enemy
is a resolver rewriting an attribute to widen a later request. A lease
answers "is this scope still live, and what did it hold" — its enemy is a
copied context outliving its operation. Forgery resistance vs revocation:
[operation-state][operation-state] composes BOTH (the carrier variable
filed behind `PrivateAuthority`, the state behind `OperationLease`), which
proves the separation load-bearing — merging them would ask one object to
be both unforgeable-by-identity and revocable-by-scope. Reconsideration
trigger: a store that must be both at once in one object.

### R-READ `operation-lease-reader-shape` (rejected, CONVERGE)

CONVERGE with the verified execution-mode R1 ("the four lease-reader
twins: 4 readers, 0 shared obligations") on a fresh census. Three readers
spell `None if lease is None else lease.held()` identically
(`current_operation_mode`, `_active_frame`, `_armed_budget`); the fourth
(`_already_bound`) composes `held()` into an identity check instead.
Per DRY principle 6 this is composition by name, not restatement: each
reader joins its own variable's documented `None` contract (no runner
involved / outside a managed execution / no budget armed / not this
scope) with the one owned `held()`. A shared `held-or-None` helper would
couple four modules' binding contracts to save two tokens. Reconsideration
trigger: a change that must move every reader's `None`-contract together
(e.g. three-state liveness) — today each `None` is deliberately
indistinguishable per its own site contract, and none exists.

### R-BOUNDARY `operation-lease-vs-boundary-contextvar` (rejected, CONVERGE)

CONVERGE with the verified File `_boundary_ordering.py` rejection
(Boundary ContextVar vs sibling ContextVars), whose population names this
file. Trigger re-checked unfired on fresh bytes: the boundary variable is
still uniquely published by a middleware around the downstream call and
uniquely read by Django itself via the exemption object, with chain-entry
lifetime; lease-backed variables are runner-published, package-read, with
operation lifetime. This file owns the lease mechanism, never the
variables. Reconsideration trigger: any two of the population's variables
share a publisher, a reader, and a lifetime.

### R-MANIFEST `operation-lease-manifest-vs-sibling-manifests` (rejected, fresh with precedent)

Considered: one shared "module manifest + TypeVar plumbing" rule across
this file (`__all__`, `PayloadT`), [policies][policies] (`__all__`,
`PolicyT`), and [private-state][private-state] (`__all__`, `StateT` /
`MemberT`). Rejected: each module owns its surface and its type
parameters — `PayloadT` has zero external importers, and a manifest change
in any one module moves that module alone. Same direction as the verified
leaf-manifest rows (each level owns its surface). Reconsideration
trigger: a lint/gate change treating all three spellings identically.

## Defects

None. No contract-row break found; nothing routes to the maintainer.

O1 (observation, not a defect — observed-not-homed): the `__weakref__`
slot on `OperationLease` has no weakref-taker in the tree. Census:
[operation-state][operation-state] weakrefs the STATE (`OperationLease(ref(state))`),
never the lease; the test suites weakref contexts, sentinels, and
extensions, never a lease; repo-wide grep for `ref(lease`,
`ref(scope.lease`, `proxy(lease`, `ref(binding` is empty. Cost is one
pointer per lease; no contract row breaks either way, so this is not
filed as a defect and no removal is proposed — narrowing a shared
cross-task handle's lifetime vocabulary would be gratuitous churn with
zero change-obligation relief. The folder `utils/` item may re-home it.

## Judgment

Zero-edit file item, complete. Target CLEAN at HEAD bytes; 6/6 enumerated
statements homed (2 file-local, 0 new families, 6 rejections: 3 converges
on verified verdicts with fresh trigger checks, 3 fresh with triggers);
no defects; no pending execution. The lease rule is already single-owned
and every production site already composes it by name — the file item's
backstop obligation is discharged with nothing to consolidate.

## Index rows for Worker-0

| `operation-lease-revocable-handle` | `django_strawberry_framework/utils/operation_lease.py::OperationLease` | `django_strawberry_framework/utils/operation_lease.py` | File `utils/operation_lease.py` | file-local |
| `operation-lease-module-mechanics` | `django_strawberry_framework/utils/operation_lease.py` (`__all__`, `PayloadT`, imports, contract docstring) | `django_strawberry_framework/utils/operation_lease.py` | File `utils/operation_lease.py` | file-local |
| `operation-lease-vs-normalization-ledger` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; CONVERGE with verified `orders-ledger-vs-operation-lease` on fresh evidence) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/orders/sets.py` | File `utils/operation_lease.py` | rejected |
| `operation-lease-vs-actor-lease` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/utils/sessions.py` | File `utils/operation_lease.py` | rejected |
| `operation-lease-vs-private-authority` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; fresh pair, no prior verdict) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/utils/private_state.py` | File `utils/operation_lease.py` | rejected |
| `operation-lease-vs-boundary-contextvar` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; CONVERGE with verified Boundary-ContextVar-vs-siblings on fresh evidence, trigger re-checked unfired) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/_boundary_ordering.py` | File `utils/operation_lease.py` | rejected |
| `operation-lease-reader-shape` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; CONVERGE with verified execution-mode R1 on fresh evidence — 4 readers, 0 shared obligations) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/extensions/operation_state.py` | File `utils/operation_lease.py` | rejected |
| `operation-lease-manifest-vs-sibling-manifests` | `django_strawberry_framework/utils/operation_lease.py` (rejection recorded here; fresh pair following the verified leaf-manifest direction) | `django_strawberry_framework/utils/operation_lease.py`, `django_strawberry_framework/utils/policies.py`, `django_strawberry_framework/utils/private_state.py` | File `utils/operation_lease.py` | rejected |

## Independent verification (Worker-2)

Traced expectation-first: full target read, AST enumeration, whole-package
`OperationLease` grep, and the three converged-from artifacts opened before
this artifact's `## Findings`. HEAD `0c0537e2` unmoved at finish; target
worktree blob `10c164b731b3` == HEAD, 77 lines, `git status` clean on the
path, item-scoped diff empty (zero-edit confirmed, not claimed).

My trace. Enumeration instrument: `ast.Module.body` over HEAD bytes — 6
statements (docstring, two imports, `__all__`, `PayloadT`, the class), all
accounted for below; class body is docstring + `__slots__` + `__init__` /
`held` / `close`. Consumer census (whole-package grep): exactly four
production importers, all composing by name — the runner scopes, the
optimizer frame, the request budget, the executor mode. No test imports
the module (package + `tests/` + `examples/` grep). Oracles: the
copied-context `held() is None` rows and weakref release rows at the
consumer seams. Projections: target docstrings, consumer rationale
paragraphs, the glossary isolation anchor. Owner I would choose: the
target (principle 7 — narrowest module every consumer already imports;
zero production imports beyond `typing`). Challenge counts: slot/flag,
close-semantics, and third-answer changes each move 1 definition (here);
a fifth leased fact moves 0. Matrix: axis 2 inapplicable with reason
(uncolored reads, sync-`finally` teardowns); axis 4 no pair (terminal
close, owner-held bind halves); axis 6 owner-owed close discipline with
no contract source extending a guard into the lease.

Reconciliation. FL1 / FL2: agree — sites, roles, counts, and the
principle-4 lifetime match my trace line for line. R-LEDGER: agree —
ledger still publishes, claims once-per-pair with disagreement raise,
and tombstones-plus-clears under one lock on worktree bytes; binds the
ledger directly with no lease import; trigger (publish protocol deleted)
re-checked unfired. R-LOCK: agree — `actor_lease` is an `asyncio.Lock`
held with `async with`; disjoint verbs. R-AUTH: agree — identity-keyed
store vs scope revocation, and the runner filing carriers behind one
while leasing state behind the other proves the split load-bearing.
R-BOUNDARY: agree — trigger (same publisher, reader, lifetime) re-checked
unfired on the clean boundary file; chain-entry vs operation lifetimes
still disjoint. R-MANIFEST: agree — `PayloadT` has zero external
importers (grep over package + tests + examples); sibling manifests
verified present. O1: agree observed-not-homed — no `ref(lease…)` /
`proxy(lease…)` site exists anywhere; the runner weakrefs the state,
never the lease; the zero-defect call stands (one pointer, no contract
row breaks either way, keep-rationale recorded).

W2 correction (verdict-neutral, record-accuracy): R-READ's census
sentence is wrong. It says three readers spell the identical line with
`_already_bound` as the fourth; fresh HEAD and worktree bytes show FOUR
identical `None if lease is None else lease.held()` readers — mode,
frame, budget, and the runner-scope reader `_live_scope`
([operation-state][operation-state] worktree `:352`, HEAD `:351`) —
with `_already_bound` (`:648`, identity check) a fifth `held()` reader
and `_bound_state` (`:397`, weakref deref) a sixth. W1's own Challenges
R-READ names the runner-scope reader correctly, so this is a drafting
slip in the finding body, not an untraced surface. The rejection itself
stands strengthened: six readers across four modules, each joining its
own documented `None`-contract with the one owned `held()`, zero shared
obligations; the trigger (a change moving every `None`-contract
together) still names nothing present. No consolidation missed; no
`## Defects` entry owed (record correction, not a contract-row break).

Freshness re-hashed independently: consumers match W1 digit-for-digit
(runner `d9ed9cc67f` dirty, optimizer `dbc3063052` clean, budget
`cc3f9d80b9` dirty, mode `9805cdaf` clean; cited HEAD blobs `b2674a22d2`
/ `4b69e974de` confirmed via `git rev-parse`). Drift disjointness
re-derived, not inherited: zero added/removed lines in either dirty
consumer mention a lease (the runner diff's one hit is diff context on
the import line). Connected dirty files relied upon for rejections
(orders, sessions, private-state) verified on worktree bytes above.
Hygiene: no tracked path touched, so no ruff run owed (artifact is
untracked per-cycle scratch); no process-provenance tokens; all 10 link
groups present, every ref-id defined once and used.

Verdict: `verified`. Zero-edit file item, complete — 6/6 homed (2
file-local, 6 rejections: 3 converges with fresh trigger checks, 3
fresh), zero production defects, no pending execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[orders-sets]: dry-file-orders__sets.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[operation-state]: ../../django_strawberry_framework/extensions/operation_state.py
[optimizer-context]: ../../django_strawberry_framework/optimizer/_context.py
[policies]: ../../django_strawberry_framework/utils/policies.py
[private-state]: ../../django_strawberry_framework/utils/private_state.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[sessions]: ../../django_strawberry_framework/utils/sessions.py

<!-- tests/ -->
[test-operation-state]: ../../tests/extensions/test_operation_state.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
