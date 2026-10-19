# DRY review: `async-execution-dispatch-decision`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule as the holding file item framed it: a resolver that can
serve both execution surfaces asks one question before handing back a
value only the asynchronous executor can complete —
[exec-mode][exec-mode]`::async_execution`. True under the
asynchronous executor; false under the synchronous one without a
running loop (the branch that finishes the work itself); a
`SyncMisuseError` naming both recourses for the synchronous executor
driving while a loop runs (neither branch is honest there); the
ambient loop when no mode is bound (a plain `strawberry.Schema` and
nothing else).

Verdict: REJECT the consolidation — single-owned, zero-edit. One
definition ([exec-mode][exec-mode]`::async_execution`, `:130–:156`);
17 consumer calls in 8 files, every one by name; every nearby shape
excluded with a contract difference + trigger (E1–E11). No
production, test, or doc line moves.

Consumer census (whole package, re-derived fresh at WT bytes; code
calls, docstring mentions excluded):
`types/resolvers.py` 6 (`:470`, `:493`, `:723`, `:750`, `:817`,
`:890`), `types/relay.py` 2 (`:1052`, `:1121`), `connection.py` 2
(`:1161`, `:1207`), `relay.py` 2 (`:651`, `:746`),
`list_field.py` 2 (`:1616`, `:1758`), `mutations/fields.py` 1
(`:323`), `auth/mutations.py` 1 (`:487`), `schema.py` 1 (`:196`).
One transitive consumer: `auth/queries.py::current_user` via the
shared `_make_auth_field` seam (no direct call). Reference census
incl. docstrings: 23 refs (the 17 calls + 6 prose mentions),
identical counts WT-vs-HEAD per file. Held boundary, never counted:
`operation_is_async` — 1 def + 2 calls (`connection.py:2155`,
`list_field.py:1735`, both as the caller's `async_executor=`
answer), owned by the queued F3 family.

Concurrency: all nine indexed files fingerprinted at task start; pins
match dispatch exactly (`exec-mode` WT `b86a08cd` / HEAD `b86a08cd`,
CLEAN; `schema` `7390c985` / `f3b6df8f`; `list_field` `f7b75c2a` /
`3842542a`; `connection` `6c4b01f9` / `38491372`; `relay`
`63bbba0b` / `037723cd`; `types/relay` `a9b90a17` / `a200f190`;
`types/resolvers` `5abd9b93` / `2c588030`; `mutations/fields`
`3368f696` / `0fada991`; `auth/mutations` `8d9e8561` / `101dbf82`).
Dirt attributed by diff content vs `git show HEAD:<path>`, nothing
edited, reverted, or tidied:

- Six dirty files carry zero added/removed lines with a dispatch
  token (`async_execution`, `operation_is_async`,
  `in_async_context`, `current_operation_mode`, `OperationMode`,
  `SyncMisuseError`): `schema`, `list_field`, `connection`,
  `types/relay`, `mutations/fields`, `auth/mutations` — incl. the
  f47 ledgered compositions in `schema` + `list_field`, buildable
  but untouched.
- `relay.py` (2 token lines): one hunk at the `:651` call site —
  `if not async_execution():` →
  `if not async_execution() and inspect.isawaitable(result):` plus
  `resolved.__name__` → `truth.name(resolved)` — concurrent
  truth-migration work (no ledger row covers a relay code hunk;
  run-2 adopted only a trigger docstring there). Verdict-neutral:
  the site composes `async_execution()` by name at both bytes; the
  added conjunct is a value-shape short-circuit, not a second
  executor decision. Untouched.
- `types/resolvers.py` (2 token lines): a docstring reword at the
  `:620–:624` dispatch comment (f44's ledgered `_absence_catch_spec`
  work is elsewhere in the file; this hunk matches no ledger row —
  concurrent). Verdict-neutral prose. Untouched.

Baselines: `ITEM_BASELINE=b94c0c8fec103bd81ef91650455206adc2d08f12`
(resolves, type `commit`); `git diff <baseline> -- <nine indexed
paths>` is empty — the tree did not move under this item. HEAD
`dd0b6691` unmoved throughout. Address
`dry/asyncdisp-f49/consolidate` (slot-2; all gate runs there).

## Verification

### Matrix

Each axis was searched against the rule's mechanism (the
mode × loop dispatch: the decision body, its two inputs, its
refusal, its consumers), not the targets' neighbours.

1. Cross-flavor policy mirroring — searched. Dispatch sites
   in all 8 consumer files (schema window, list ×2, connection
   ×2, node, nodes, type-relay ×2, type-resolvers ×6, mutation,
   auth) all call the one decision by name; no flavor restates
   the mode × loop arms.
   The four `SyncMisuseError` pipeline raises share the TYPE, not
   the contract (E2). No mirror.
2. Sync/async twins — searched, none of the decision itself. The
   decision is one synchronous function answering ABOUT color; the
   per-color pipeline twins it selects between (sync/async bodies
   in every consumer) are consumers of the verdict, not twins of
   it. The refusing dispatch vs the statable fact
   (`operation_is_async`) is the queued F3 boundary (E1), not a
   twin pair to merge.
3. Derived rather than repeated knowledge — searched. The verdict
   is derived once, in the owner body; it is never re-derived.
   `in_async_context` is imported exactly once package-wide (the
   owner); `current_operation_mode` has zero external readers at
   both bytes; `asyncio.get_running_loop` /
   `get_event_loop` occur zero times in the package. No second
   derivation.
4. Inverse / round-trip pairs — searched. The decision has no
   inverse half: it is a read (mode + loop → verdict), not an
   encode/decode pair. The carry it reads (bind here,
   close/reset in the runner) is owned by Family
   `carried-operation-executor-mode`. No scattered half.
5. Contracts restated in another medium — classified, never
   counted. Oracles: the owner entry matrix (8 rows in
   [test-exec-mode][test-exec-mode], incl. the disagreement row
   pinning the typed error + both recourse substrings), the
   list-field three-state matrix (3 tests × 2 flavors in
   [test-list-field][test-list-field], incl. the
   no-abandoned-awaitable control), the auth seam-split pin
   ([test-auth-mutations][test-auth-mutations]`::test_auth_field_dispatch_splits_sync_and_async_resolver_bodies`),
   the live nested-sync refusal
   ([test-list-async-api][test-list-async-api]`::test_async_a_nested_synchronous_operation_refuses_a_list_field`).
   Every pin spells literals (`"await schema.execute"`,
   `"worker thread"`, `"OperationMode.SYNC"`) or asserts
   behavioral splits without reading the owner. Projections: the
   owner module grammar, the [glossary][glossary] `SyncMisuseError`
   executor bullet, the [readme][readme] dispatch paragraph, the
   spec-050 decision prose, the consumer docstrings citing by
   `path::Symbol`. Each medium moves for its own reason.
6. Enforcement by omission — family enumerated, each member
   checked. Every resolver-return branch on the driving executor
   composes a reader by name: 17 dispatch calls + 2 fact
   pass-throughs + 1 transitive consumer. Write pipelines
   (mutations/forms/rest_framework resolvers) branch nowhere —
   the field dispatches once and routes to `resolve_sync` /
   `resolve_async` (E11). Transports (views, middleware,
   consumers, routers) select entry points and never branch a
   resolver return on color (E6). The optimizer extension hook
   passes values through by shape (E3). Zero members lack the
   dispatch; no gap.

### Enumeration

Instrument one: `grep -rn` censuses over all 120 package files
(117 tracked + 3 untracked: `_multipart.py`, `utils/lazy.py`,
`utils/truth.py`)
for the mechanism vocabulary (`async_execution`,
`operation_is_async`, `current_operation_mode`,
`in_async_context`, `OperationMode`, `SyncMisuseError`,
`is_async_callable`, `iscoroutinefunction`,
`isawaitable`, `get_running_loop`, `get_event_loop`,
`operation_is_nested`, `except SyncMisuseError`), run at WT bytes
and re-run at HEAD bytes via `git show HEAD:` /
`git grep HEAD`. Instrument two: full body reads of the owner,
all 17 call sites, and every exclusion site below. Every hit is
homed: F1 carries the rule; E1–E11 carry the exclusions.

| Population | Hits | Home |
|---|---|---|
| `async_execution` def | 1 (`exec-mode:130`) | F1 |
| `async_execution()` code calls | 17 in 8 files, all by name | F1 consumers |
| `async_execution` docstring mentions | 6 (types/resolvers 1, mutations/fields 4, auth/mutations 1) | F1 projections |
| `in_async_context` refs | 1 import + 3 calls, all in `exec-mode`; 0 elsewhere at both bytes | F1 substrate |
| `current_operation_mode` external readers | 0 at both bytes (2 internal calls only) | F1 substrate |
| `operation_is_async` | 1 def + 2 calls | E1 (queued F3) |
| `raise SyncMisuseError` | 5 (1 dispatch + 4 pipeline) | F1 + E2 |
| `except SyncMisuseError` | 1 (`filters/sets.py:3841`) | E8 |
| value-shape `isawaitable` branches | 8 sites in 5 files | E3 |
| `is_async_callable` | 1 def + 3 code calls | E4 |
| bare `iscoroutinefunction` | 5 (middleware 2, typing 2, views 1) | E4 + E6 |
| `schema.py::_operation_mode` | 1 def + 2 calls | E5 (f48 S2) |
| transport entry/selection sites | views 1, middleware 2, consumers 2, routers 0 dispatch | E6 |
| `operation_is_nested` | 1 def + 1 aliased consumer | E7 |
| `get_running_loop` / `get_event_loop` | 0 in the package | E9 (absent) |
| decision's carry-side reads | 1 (`current_operation_mode()` at `:143`; the only other call is F3's at `:124`) | E5 boundary |
| `DjangoSchema` subclasses overriding dispatch | 0 | Matrix 6 |

### Challenges

The rule's variation axes, re-derived fresh: refusal condition
(V1), unbound-mode fallback (V2), refusal shape (V3), consumer
count (V4), executor vocabulary (V5). Counts are authoritative
definitions of the dispatch decision; consumers, oracles, and
projections that also move are listed, never counted.

- C1 refusal removed (V1: nested sync-in-async becomes legal, the
  raise arm goes away): counts 1 (`async_execution`). Oracles
  listed: the disagreement row, the 2 list-field refusal params,
  the live nested-sync row — all pin the raise.
- C2 recourse gains a third option (V1+V3): counts 1 (the raise
  wording). Projections listed: the glossary bullet, the README
  paragraph. The 4 pipeline wordings do not move (E2).
- C3 unbound answers sync instead of ambient (V2): counts 1 (the
  `None` arm here). `operation_is_async`'s own `None` arm is F3's
  rule — listed, not counted. Oracles listed: the 2 plain-schema
  fallback rows.
- C4 dedicated mismatch error type (V3): counts 1 (the raise).
  Consumers listed: the 1 `except SyncMisuseError` site keeps
  covering it only if it catches the new type too (E8 trigger
  stays armed, unfired).
- C5 ninth consumer flavor (V4): counts 0 — it calls
  `async_execution()` by name, as all 17 existing calls do.
- C6 third executor color (V5): counts 1 here (the new color's
  verdict arm) + 1 in the carried vocabulary (f48's family) + 1
  in F3's reader — one per family, each family's own change
  (coupling noted, not counted twice).

Family-level: every challenge counts at most 1; a new consumer
counts 0.

## Findings

### F1 — the async-execution dispatch decision (single-owned, zero-edit)

- **Contract + variation.** Whether a resolver may hand back a
  value only the async executor completes: true under ASYNC,
  false under SYNC-without-loop, refused under SYNC-with-loop,
  ambient when unbound. Varies on bound mode × loop presence
  (V1–V5); the refusal branch is the contract, not an error
  path.
- **Sites + roles.** Definition: 1
  ([exec-mode][exec-mode]`::async_execution`, incl. its wording).
  Consumers: 17 calls in 8 files + 1 transitive
  (`auth/queries.py` via `_make_auth_field`). Oracles: owner
  matrix (8 rows), list-field matrix (3 × 2), auth seam pin (1),
  live nested-sync refusal (1) — `### Matrix` axis 5.
  Projections: owner grammar, glossary bullet, README paragraph,
  spec-050 prose, consumer docstrings.
- **Challenges.** C1–C6 above: every change counts at most 1
  definition, 0 for a new consumer.
- **Owner + lifetime.** Principle 7: the owner is
  [exec-mode][exec-mode] — the neutral leaf every legitimate
  consumer already imports (all 8 consumer files import the
  decision from it; moving the decision into any consumer would
  make 7 files import a sibling flavor for its machinery). The
  refusal must name the call that caused it, so the decision and
  its wording live at the single reader every flavor calls.
  Pure derivation, not cached (principle 4); no stored state
  beyond the carried binding, whose lifetime the
  `carried-operation-executor-mode` family owns.
- **Migration.** None — zero-edit. No production, test, or doc
  line moves.
- **Distinct behavior.** The statable fact stays in queued F3
  (E1); the carried vocabulary + binding stay in f48 (E5); every
  refusal seam keeps its own wording (E2); value/shape
  classification stays separate (E3, E4); transports keep
  selecting entries (E6); pipelines keep running their color's
  body (E11).
- **Behavioral proof.** `static-reviewed`. One definition body +
  17 call-site bodies read at WT bytes; whole-package mechanism
  censuses closed at WT and HEAD bytes with identical counts;
  oracles read (not run — the gate owns suite-green; no pytest
  ran in this item). Nothing ordering-, transactional-, or
  async-sensitive was judged: the verdict is body-composed-by-name
  (DRY.md's inspection-alone clause). Wrong result (a) "a second
  definition hides under another spelling" is rejected by the
  mechanism censuses (1 def; `in_async_context` 1 import + 3
  calls owner-only; external mode readers 0; loop getters 0;
  call counts identical HEAD-vs-WT). Wrong result (b) "a call
  site restates the arms" is rejected by the 17 body reads
  (every site calls by name; the closest shape — relay `:651`'s
  `not async_execution() and isawaitable` — conjoins a
  value-shape check with the verdict, it does not recompute
  it). Wrong result (c) "a flavor dispatches without the
  decision" is rejected by the axis-6 family enumeration (every
  executor branch on a resolver return composes a reader;
  pipelines and transports branch on nothing).
- **Structural gate.** None owed. Three plausible bypasses,
  each judged against the gate-only bar (justified population,
  never a bespoke existence test per helper — f48 precedent,
  verifier-endorsed):
  - sampling `in_async_context` for an executor question:
    plausible (the easiest mistake), but the population is
    unjustified — the same token legitimately answers "may I
    touch the ORM here" (the owner module's own documented
    split), so a reference census conflates two jobs and
    reddens on the first legitimate ORM-touch read; it would
    be weakened, not fixed. Standing enforcement is the
    docstring grammar (principle 10) + the disagreement
    oracles. CONVERGE with f48's bypass-3 judgment on fresh
    evidence (this item's censuses + body reads are its own).
  - reading `current_operation_mode` externally and re-spelling
    the arms: population closable (0 external readers today),
    but the bypass is implausible — the leaf reader sits next
    to `async_execution()`, and no author reaching for it has
    a reason to re-spell arms instead of calling the decision.
    A census would guard a bypass nobody has a reason to
    write (f48 bypass-1 analog).
  - branching a value-shape check AS an executor verdict:
    unjustified — value branches are legitimate and numerous
    (E3), and no syntactic population distinguishes "executor
    verdict" from "value completion".
  The package-wide censuses in this artifact are the first-run
  check that the rule currently holds, and the in-tree oracles
  pin every contract verdict. Negative control reasoned: a hand
  copy of the decision body passes every behavior oracle (the
  copy is correct), which is exactly why no new oracle is
  proposed as a gate. No failability run is owed: nothing
  lands, so no divergence exists to prove catchable.
- **Coupling.** None. Zero-edit verdict; a third executor color
  (C6) would move one arm per family — noted, not a landing
  dependency.
- **Freshness.** WT (`git hash-object`) / HEAD (`git rev-parse
  HEAD:<path>`), same-kind pairs: `exec-mode` `b86a08cd` /
  `b86a08cd` (CLEAN), `schema` `7390c985` / `f3b6df8f`,
  `list_field` `f7b75c2a` / `3842542a`, `connection` `6c4b01f9`
  / `38491372`, `relay` `63bbba0b` / `037723cd`, `types/relay`
  `a9b90a17` / `a200f190`, `types/resolvers` `5abd9b93` /
  `2c588030`, `mutations/fields` `3368f696` / `0fada991`,
  `auth/mutations` `8d9e8561` / `101dbf82`, `auth/queries`
  `4f3ab00f` / `4f3ab00f` (CLEAN), `querysets` `6d471bd7` /
  `adc74b64`, `op-state` `5f6f255d` / `009714fd`,
  `optimizer/extension` `8e3fe7c1` / `b7b6c434`,
  `_graphql_core_patches` `efadf7fb` / `b4737d78`,
  `utils/typing` `1fa47d59` / `defbe7ee`, `views` `c944b4be` /
  `fbf00ddf`, `middleware/request_body` `1febddbc` / `63a9a4a8`,
  `consumers` `6e48bd70` / `8e33fc3c`, `types/base` `e7a62d32`
  / `e0ad32aa`, `filters/sets` `14884190` / `76abccb0`,
  `routers` `7ebf31e9` / `a71c5369`, `test_execution_mode`
  `724ed67f` / `724ed67f` (CLEAN), `test_list_field` `5b4e5339`
  / `09d93c61`, `test_auth_mutations` `8c95103b` / `59d13bda`,
  live `test_list_field_async_api` `4a570915` / `4a570915`
  (CLEAN). Census population: 120 package files. Call counts
  identical WT-vs-HEAD per file (1/2/2/2/2/7/5/2 incl.
  docstrings); external mode/loop readers 0 at both bytes. Any
  fingerprint change reopens the finding.

### E1 — `operation_is_async` and its two consumers (boundary, held by queued F3)

1 def + 2 calls (`connection.py:2155`,
`list_field.py:1735`, both as `async_executor=`). Contract
difference: states the fact for callers with their own answer
to every outcome — never refuses. The split is load-bearing:
posit dropping F1's refusal and the guard both F3 call sites
feed (taking a bool) is unaffected. Boundary: this family owns
the refusing dispatch; queued Family
`ambient-fallback-executor-read` owns the fact read. Trigger: a
third reader needing a different absence posture reopens the
substrate, not the readers.

### E2 — the four pipeline `SyncMisuseError` raises (excluded, CONVERGE)

`querysets.py:223` (hook-awaitable), `:526`
(async-iterable source), `:3290` (sidecar-awaitable), `:4835`
(sync-source-awaitable). Contract difference: each refuses a
produced VALUE on a sync path (detect + dispose + raise with
per-seam recourse) — none reads the mode or the loop, none
answers which executor drives. The TYPE is shared, the
contracts differ. CONVERGE with the verified File
`utils/execution_mode.py` R3 + the rejected
`sync-boundary-recourse-wording` family (12 wordings / 9 files,
each single-owned) on fresh evidence. Trigger: a raise
conditioned on mode × loop rather than value shape.

### E3 — value-shape completion branches (excluded)

8 sites: `connection.py:874` (post-upstream completion),
`relay.py:659` (post-guard completion), `:767` (inside the
`_gather` coroutine), `:780` (sync-branch guard arm via the
shared refuser), `types/resolvers.py:766,836,911` (inside
already-async coroutines awaiting an `AwaitableOrValue`),
`optimizer/extension.py:1171` (pass-through hook),
`_graphql_core_patches.py:152–156` (residual-awaitable
completion). Contract difference: branch on what a produced
VALUE is (awaitable or not), never on which executor drives —
zero mode/loop reads across all 8 bodies. Trigger: a value
branch conditioned on the driving executor rather than the
value shape.

### E4 — resolver-shape classification (excluded, CONVERGE)

`is_async_callable` (1 def, 3 code calls —
`types/base.py:503` validation, `connection.py:2210` +
`list_field.py:1778` per-construction commitment) and bare
`iscoroutinefunction` (5: `middleware/request_body.py:147,168`,
`utils/typing.py:221,231`, `views.py:594`). Contract difference:
classify what a callable IS at construction/selection/
validation time, never which executor IS DRIVING at operation
time. Pinned at one site: `list_field.py:1778` commits the
wrapper per-construction while `:1616` dispatches per-call —
two moments, two jobs. CONVERGE with the verified File
`utils/execution_mode.py` R4 on the fresh census.
Trigger: a shape check used to branch a resolver return at
runtime.

### E5 — the carried fact and its publication (boundary, verified f48)

`OperationMode`, `_OPERATION_MODES`, `bind_operation_mode`,
`current_operation_mode`, `schema.py::_operation_mode`,
`_OperationModeMarker`, `_declared_operation_mode`, the
runner bind. Contract difference: the fact the decision READS
vs the question it ANSWERS. This family consumes
`current_operation_mode` by name (1 of its 2 internal calls);
f48 owns the carry. Trigger: a reader needing a different fact
(a new color, a new absence posture) reopens f48's S1, not
this decision.

### E6 — transport entry selection (excluded)

`views.py:594` (sync/async view wrapper at `as_view()` time),
`middleware/request_body.py:147,168` (chain color),
`consumers.py:1186,1194` (`subscribe` / `stream` pass-through
entry calls), `routers.py` (no dispatch surface). Contract
difference: choose WHICH entry point runs — the flag's cause —
while the decision reads the carried effect; no site branches
a resolver return on its own color. Trigger: a transport
branching a resolver return on its own color instead of the
carried mode.

### E7 — `operation_is_nested` (excluded, CONVERGE)

1 def (`op-state:391`) + 1 aliased consumer
(`optimizer/extension.py:1126`, passing `nested=` to the
optimizer frame only). Contract difference: runner nesting vs
executor color are independent facts over separate storage —
`_RUNNER_SCOPES` via `_live_scope` vs `_OPERATION_MODES` via
`current_operation_mode` — with separate readers and no
combined predicate. The mode half of the combination is
pinned by
`test_a_nested_operation_restores_the_outer_mode_on_the_way_out`
(inner op reads SYNC, outer restores ASYNC).
CONVERGE with the verified File `utils/execution_mode.py` R5
on the fresh census. Trigger: a consumer needing both answers
as one predicate.

### E8 — dedicated executor-mismatch error (excluded, CONVERGE)

Considered: a new exception instead of reusing
`SyncMisuseError`. Rejected: the marker's documented contract
is "reserved for sync boundaries" and this misuse — a value
the sync executor cannot complete — is exactly that; the one
`except SyncMisuseError` site (`filters/sets.py:3841`) plus
the `ConfigurationError` / `RuntimeError` handlers already
cover it. CONVERGE with the verified File
`utils/execution_mode.py` R7 on the fresh census. Trigger: a
consumer needing to distinguish executor-mismatch from
async-hook misuse by type.

### E9 — `schema.py` loop-getter plumbing (excluded, absent)

The file item's matrix-6 note named `asyncio.get_running_loop`
reads in `schema.py` as executor plumbing. At current bytes
the subject is absent: zero `get_running_loop` /
`get_event_loop` occurrences in the package (the window thread
carries no loop reads). No body to converge with; the trigger
("a loop read used as an executor verdict") is armed on the
empty population and unfired.

### E10 — `auth/queries.py::current_user` (transitive consumer, not a site)

Composes `_make_auth_field` (the `auth/mutations.py`
dispatch seam) with split bodies; branches on nothing itself.
Listed so the family census closes over the auth surface;
no decision, no exclusion.

### E11 — single-boundary pipeline execution (excluded)

`run_in_one_sync_boundary` + the write-pipeline async
variants (mutations/forms/rest_framework resolvers): run the
sync body on one worker under the async surface. Contract
difference: executes already-dispatched work — the FIELD
dispatched once (`mutations/fields.py:323`) and routed to
`resolve_sync` / `resolve_async`; the pipeline branches on no
executor input. Standing `one-sync-boundary` family
territory. Trigger: a pipeline branching on the executor
instead of running its color's body.

## Defects

None found while tracing. Checks performed for contract: 9
docstring-vs-body pairs at the dispatch seams (the owner
grammar vs the four arms; the list-field asymmetry comment vs
`:1616` + `:1758` + `:1778`; the connection Decision-10
comment vs the committed split + `:1161` + `:1207`; the relay
refetch docstrings vs `:651` + `:746`; the two type-relay
docstrings vs `:1052` + `:1121`; the type-resolvers lazy-load
comment vs the 6 gated sites; the mutation-field comment vs
`:323`; the auth seam comment vs `:487`; the schema
execution-mode split vs `:196`) — every claim matches its
body at WT bytes. The relay `:651` concurrent hunk changes a
guard shape this item does not own; it still composes the
decision by name, so it is verdict-neutral here and left
entirely alone (concurrent work, never judged from this
item).

## Pending execution

None. Every verdict is `static-reviewed` (closed censuses at
both bytes, body comparison, pinned oracles read — inspection
decides; nothing ordering-, transactional-, or async-sensitive
was judged). No `proof:` entry: nothing lands, so no
failability probe is owed. No `gate:` entry: zero-edit, no
regression witness needed. No shared-tree pytest ran (the gate
owns suite-green). Sharded and PG cells are inapplicable by
construction: the traced surface is carried-mode reads ×
ambient-loop reads at resolver seams, reaching no database,
alias, or dialect decision — stated for Worker-2 to judge.

## Judgment

REJECT the consolidation: the async-execution dispatch
decision is single-owned — one definition, 17 consumer calls
in 8 files composing by name at both bytes, six challenges
counting at most 1, zero external mode/loop readers — and the
verdict is therefore a proved zero-edit: no tracked file
changed, no test added, no `## Owned changes` row owed.
Eleven exclusions carry contract differences plus triggers
(E1 + E5 queued/verified-family boundaries, E2/E4/E7/E8
converge on standing rows with fresh evidence, E3/E6/E11
fresh splits, E9 absence, E10 transitive consumer); zero
defects; no new index rows.

Worker-0 instructions: (a) tick the plan item Family
`async-execution-dispatch-decision` as verified under Run
`0.0.15 2026-10-01-11` once Worker 2 agrees, transcribing the
family row to `consolidated` (single-owned: F1 counts ≤1 per
challenge, consumers by name — f48 precedent for the
single-owned-zero-edit transcription); (b) no `## Owned
changes` row; (c) no new index rows — every exclusion is a
boundary on an existing or queued row, not a family; (d) the
queued F3 family (`ambient-fallback-executor-read`) is
untouched by this verdict and still owns its item.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped attribution vs
`ITEM_BASELINE=b94c0c8fec103bd81ef91650455206adc2d08f12`: `git
diff <baseline> -- <nine indexed paths>` is empty — all
WT-vs-HEAD dirt predates the baseline window (f47/f44 ledgered
hunks + concurrent truth migration) and was never touched;
the artifact itself is a new untracked file, the item's only
output. The [plan][plan] `## Owned changes` ledger gains no
row from this item. No `uv run ruff` run (no `.py` touched;
`.md` is outside ruff format scope; census greps ran inline,
no script file). No shared-tree pytest run (see `## Pending
execution`). No `docs/dry/temp-tests/` scratch created. Three
workspace runs at `dry/asyncdisp-f49/consolidate` (slot-2,
each provenance-fresh, shared tree unmoved since sync), all
green: `basedpyright` 0 errors / 0 warnings / 0 notes
(`dry-20261001T203522-c9b8f8`), `check_any` 128 uses at 89
sites exit 0 (`dry-20261001T203532-ecccd1`),
`check_truthful_reads --check` 119 files tier-1 0 / errors 0
(`dry-20261001T203533-6fc8fd`) — tree-state results matching
the run-11 baseline, zero-edit item. No new cast / `Any` /
suppression (no code changed; `ALLOWED_ANY` untouched). No
commit. mypy never run, never cited.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[plan]: dry-0_0_15.md
[readme]: ../README.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exec-mode]: ../../django_strawberry_framework/utils/execution_mode.py

<!-- tests/ -->
[test-auth-mutations]: ../../tests/auth/test_mutations.py
[test-exec-mode]: ../../tests/utils/test_execution_mode.py
[test-list-field]: ../../tests/test_list_field.py

<!-- examples/ -->
[test-list-async-api]: ../../examples/fakeshop/test_query/test_list_field_async_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Recorded expectation-first: every census below was re-derived with my
own instruments at WT and HEAD bytes BEFORE opening `## Findings`
(the relay `:651` body, all 17 call-site bodies, and the
package-wide mechanism sweeps were read first). Owner I chose from
that trace: `utils/execution_mode.py::async_execution` — the neutral
leaf every consumer already imports; matches W1's F1.

### My trace (pre-read)

- ONE definition: `def async_execution` exactly once package-wide
  (`exec-mode:130`), identical body at WT and HEAD (`exec-mode`
  CLEAN `b86a08cd`). No second definition anywhere under any
  spelling (mechanism sweeps below).
- 17 consumer calls in 8 files, every one composing by name (all
  bodies read): `schema.py` 1 (`:196`), `list_field.py` 2
  (`:1616` dispatch, `:1758` `is_async_context=` pass),
  `connection.py` 2 (`:1161`, `:1207`, both value-gated
  conjuncts), `relay.py` 2 (`:651` negated conjunct, `:746`
  gather dispatch), `types/relay.py` 2 (`:1052`, `:1121`),
  `types/resolvers.py` 6 (`:470`, `:493`, `:723`, `:750`,
  `:817`, `:890`), `mutations/fields.py` 1 (`:323`),
  `auth/mutations.py` 1 (`:487`). Reference census incl.
  docstrings: 23 (17 + 6 prose: resolvers 1, mutations/fields 4,
  auth/mutations 1; `.pyc` excluded).
- Relay `:651` (`not async_execution() and isawaitable`) is a
  value-shape short-circuit ON the composed verdict, not a second
  decision: the `async_execution()` call is the mode input, the
  conjunct only skips the guard for already-complete values. HEAD
  carries the un-conjuncted `if not async_execution():` (`:528`);
  the conjunct + `truth.name` hunk is concurrent truth-migration
  dirt (no ledger row covers a relay code hunk), verdict-neutral
  at both bytes.
- 1 transitive consumer: `auth/queries.py::current_user` (`:128`)
  via the `_make_auth_field` seam, which has 3 callers (login
  `:1055`, logout `:1083`, `current_user`) and 1 dispatch body
  (`:487`) with split sync/async bodies.
- 0 external mode readers at both bytes: `in_async_context` is
  imported once package-wide (the owner; 3 owner-only calls at
  `:126`/`:145`/`:148`); `current_operation_mode` has 2 internal
  calls only (`:124`, `:143`); mode tokens appear only in the 3
  f48 carry files (owner + schema publication + runner bind).
- 0 loop primitives at both bytes under a broader instrument than
  tasked (`running_loop`, `new_event_loop`, `get_event_loop`,
  `get_loop(`, `BaseEventLoop`, `loop.run`,
  `run_until_complete`): both sweeps empty.
- HEAD statement texts match WT at 16/17 sites (only the relay
  `:651` concurrent hunk differs); HEAD per-file call counts are
  the same 1/2/2/2/2/6/1/1.

### Reconciliation

Every W1 census above matches mine EXACTLY (counts, per-file
splits, line numbers, pins) except E3, where my broader sweep
finds two verdict-neutral corrections (f48 precedent: W1's
undercount substantiated on W2's superset, verified with a
record note):

- E3 header + Enumeration table say "8 sites in 5 files" but list
  9 regions. The "8" counts the `inspect.isawaitable` branches;
  the `_graphql_core_patches.py` region (spelled `_is_awaitable`,
  invisible to an `isawaitable` substring grep) was appended to
  the list without updating the count. Corrected: 9 listed
  regions.
- E3 MISSES one member my sweep found: `schema.py:428`
  (`if self.is_awaitable(result): result = await result` inside
  `complete()` in `_execute_mutation_field_async`). Body read:
  branches on what the produced VALUE is, zero mode/loop reads —
  E3's contract difference covers it verbatim, and it moves under
  none of C1–C6. Homed here under E3.
- Durable E3 population: 10 regions / 11 branches in 6 files
  (connection 1, relay 3, types/resolvers 3, optimizer/extension
  1, patches 1 region holding 2 branches at `:155` + `:163`,
  schema 1). E2-homed value reads close separately (querysets
  `:220`, `:221`, `:245`, `:260`, `:3288`, `:3321`, `:3327`,
  `:4803` — all inside guard/dispose bodies). No member unhomed
  after this note; no verdict impact (an exclusion count, never a
  definition).

### Worker-0 points ruled

- (a) Single-ownership CONFIRMED on reproduced censuses (own
  greps + `git grep HEAD` + full body reads: 1 def; 17 calls in
  8 files with per-file 1/2/2/2/2/6/1/1; 1 transitive via the
  3-caller seam; external mode/loop readers 0/0 at both bytes;
  loop getters 0 under the broad instrument). No second
  definition anywhere.
- (b) No-gate ENDORSED. Bypass 1 (loop sampling) plausible but
  unjustified — converges with f48's endorsed bypass-3 on fresh
  evidence (standing enforcement is the principle-10 grammar +
  the disagreement oracles, verified live below). Bypass 2
  (external mode read + re-spelled arms) closable but
  implausible — f48 bypass-1 analog holds (the decision sits
  next to the reader; no reason to re-spell). Bypass 3
  (value-shape as verdict) unjustified — E3 branches are
  legitimate and numerous (10 regions now). The reasoned
  negative control correctly rules out behavior oracles; no
  failability run owed (nothing lands). Meets the
  f48-endorsed gate-only bar; no gate owed.
- (c) Pending-None STANDS → plain `verified`. Single-owned
  zero-edit asserts no equivalence (nothing lands, nothing
  blocked), so no `proof:` entry is owed — this item meets the
  f48-(c) bar exactly (f46-pass-1 targeted blocked CONFIRMs, not
  this shape). Corroboration by W2: 16 focused oracles
  `--no-cov`, 16/16 green (entry matrix 8, list-field matrix
  3×2, auth seam pin 1, live nested-sync refusal 1). Every cited
  oracle verified WT-live with literal-spelling independence
  (recourse substrings, typed errors, the warnings-catch
  no-abandoned-awaitable control).
- (d) Exclusions VERIFIED. E2/E4/E7/E8 converge faithful
  against standing rows (File R3/R4/R5/R7 texts + triggers
  match verbatim incl. R4/R5/R7 trigger lines; e5 R-inline
  covers `exec-mode :149` as one of 4 single-sited inline
  wordings; "12 wordings / 9 files" plan row exact). E1/E5
  boundaries exact against the queued-F3 `open` row and the
  verified-f48 `consolidated` row. E3/E6/E11 bodies verified
  (E3 with the record note above; E6 transports select entries
  only — consumers `:1186`/`:1194` pass-through, routers 0,
  views `:594` + middleware `:147`/`:168` construction/chain
  color; E11 pipelines read zero executor inputs — grep-empty
  across all three resolvers + write_transaction). Each carries
  contract difference + trigger + home.
- (e) No-new-index-rows ENDORSED under the f21/f23/f34/f48
  single-owned-zero-edit precedent. E1/E5 bound existing rows;
  E2/E4/E7/E8 converge; E3/E6/E11 are non-candidate exclusions
  (no second definition claimed; triggers armed here); E9 has
  an empty population; E10 is a consumer, not a site. No fresh
  rejection row owed anywhere.
- (f) E9 absence REPRODUCED with a stronger instrument (broad
  loop-primitive sweep empty at both bytes; the file item's
  matrix-6 `schema.py` loop reads are gone at current bytes —
  refactored away between `0c0537e2` and `dd0b6691`,
  verdict-neutral). E10 transitive VERIFIED (seam def
  `:452`, dispatch `:487`, split bodies, 3 callers incl.
  `queries.py:128`; `current_user` branches on nothing).

C1–C6 judged ≤1 each on my own reading of the one body (C1 the
raise arm; C2 the wording, pipelines unmoved per E2; C3 the
`None` arm, F3's listed-not-counted; C4 the raise, the 1
`except` site listed with its trigger armed; C5 zero by 17
precedents; C6 one per family with coupling noted). The 9
docstring-vs-body seam pairs re-checked while reading every
cited body — all match; 0 defects.

Freshness: all 9 indexed pins re-hashed same-kind, exact (WT
`git hash-object` vs HEAD `git rev-parse`; `exec-mode` CLEAN);
all 16 connected pins re-hashed, exact (`auth/queries` +
`test_execution_mode` + live oracle CLEAN). Census population
120 = 117 tracked + 3 untracked `.py`, exact. Item diff vs
`ITEM_BASELINE=b94c0c8f…` is the plan edit alone (58 lines);
zero tracked edits; artifact untracked — zero-edit CONFIRMED.
`git diff <baseline> -- <nine indexed paths>` empty; HEAD
`dd0b6691` unmoved.

Gates re-run by W2 (shared tree): `ruff format --check` (9
files already formatted) + `ruff check` (all pass) on the 9
indexed paths — vacuous, zero `.py` touched; basedpyright
0/0/0; check_any 128/89; truthful-reads 119 files tier-1 0 /
errors 0 — all match the run-11 baseline exactly. mypy never
run, never cited. LINK DEFINITIONS: 10/10 canonical group
headers, 8 used refs all defined. Banned words vacuous (zero
test/production edits). Sharded/PG inapplicable-by-construction
ENDORSED (carried-mode × ambient-loop reads at resolver seams;
no database, alias, or dialect decision). Coupling none.
Defects: none.

Verdict: `verified`, plain. Worker-0: tick Family
`async-execution-dispatch-decision` (verified under Run `0.0.15
2026-10-01-11`); family row → `consolidated` (single-owned,
f48 precedent); index row → `consolidated` with the E3
correction transcribed (10 regions / 11 branches in 6 files);
no `## Owned changes` row; no new index rows; queued F3
untouched.

