# DRY review: `ambient-fallback-executor-read`

Status: verified
Run: 0.0.15 2026-10-01-11

## System trace

The rule as the holding file item framed it: a caller that has its
own answer to every outcome asks one question about which GraphQL
executor is driving the operation here —
[exec-mode][exec-mode]`::operation_is_async`. The bound mode when
the package runner bound one, the ambient loop when nothing did (a
plain `strawberry.Schema` and nothing else) — stated, never
refused.

Verdict: REJECT the consolidation — single-owned, zero-edit. One
definition ([exec-mode][exec-mode]`::operation_is_async`,
`:118–:127`); 2 consumer calls in 2 files, every one by name as
the caller's `async_executor=` answer; every nearby shape excluded
with a contract difference + trigger (E1–E10). No production,
test, or doc line moves.

Consumer census (whole package, re-derived fresh at WT bytes; code
calls, docstring mentions excluded): `list_field.py:1735` and
`connection.py:2155`, both as `async_executor=` to
`utils/querysets.py::reject_async_iterable_in_sync_context`, which
takes the reading as a parameter and never samples anything
itself (body read — its docstring states the split and cites the
owner by `path::Symbol`). Reference census incl. prose: 8 refs
(the 1 def + 2 calls + 2 imports + `__all__` + 2 docstring
mentions), identical counts WT-vs-HEAD. Held boundary, never
counted: `async_execution` — 1 def + 17 calls in 8 files, owned
by verified Family `async-execution-dispatch-decision`.

Concurrency: all three indexed files fingerprinted at task start;
pins match dispatch exactly (`exec-mode` WT `b86a08cd` / HEAD
`b86a08cd`, CLEAN; `list_field` `f7b75c2a` / `3842542a`;
`connection` `6c4b01f9` / `38491372`). Dirt attributed by diff
content vs `git show HEAD:<path>`, nothing edited, reverted, or
tidied:

- Both dirty files carry zero added/removed lines with a fact
  token (`operation_is_async`, `async_execution`,
  `in_async_context`, `current_operation_mode`, `OperationMode`,
  `SyncMisuseError`) — the verdict-critical read sites are
  content-identical HEAD-vs-WT (`:1735` / `:2155`, both
  `async_executor=operation_is_async(),` at both bytes).
- `list_field.py` (243-line diff): the f47 ledgered owner import
  + `ListArgumentError` composition (`coded_error_extensions` —
  the hunks this item could build on, untouched); everything
  else concurrent truth migration (`truth.render` / `name` /
  `describe` / `is_instance` / `static_attr`, validator rewrites)
  in imports, `_validate_djangotype_target`, wire-name readers,
  argument normalization, and factory headers. No hunk reaches
  the `:1731–:1758` executor region.
- `connection.py` (265-line diff): all concurrent — window /
  keyset / relation machinery plus truth-migration tokens
  (`truth.render` / `name` / `IdentityMap` / `own_attr`); no
  `## Owned changes` row covers a connection hunk. No hunk
  reaches the `:2152–:2155` guard site.
- `exec-mode`: CLEAN, WT identical to HEAD.

Baselines: `ITEM_BASELINE=67dcdf2e91497f6b616966108387c0ccbcced018`
(resolves, type `commit`); `git diff <baseline> -- <three indexed
paths>` is empty — the tree did not move under this item. HEAD
`dd0b6691` unmoved throughout. Address
`dry/ambient-f50/consolidate` (slot-2; all gate runs there).
The adjacent f48 + f49 artifacts were read as orientation only;
every count, challenge, and trigger below is re-derived fresh at
current bytes with this item's own instruments.

## Verification

### Matrix

Each axis was searched against the rule's mechanism (the
statable executor fact: the read body, its two inputs, its
consumers, the guard they feed), not the targets' neighbours.

1. Cross-flavor policy mirroring — searched. The fact has
   exactly 2 consumers (list + connection), both feeding the
   same shared guard with the same bool; no flavor restates the
   bound-or-ambient arms. The 17 refusing-dispatch calls share
   neither contract nor absence posture (E1). No mirror.
2. Sync/async twins — searched, none of the read itself. The
   read is one synchronous function answering ABOUT color; the
   per-color pipeline twins its consumers select between are
   downstream of the verdict, not twins of it. The statable
   fact vs the refusing dispatch is the verified-F2 boundary
   (E1), not a twin pair to merge — composition in either
   direction is considered and rejected under F1.
3. Derived rather than repeated knowledge — searched. The fact
   is derived once, in the owner body; it is never re-derived.
   `in_async_context` is imported exactly once package-wide
   (the owner); `current_operation_mode` has zero external
   readers at both bytes; `get_running_loop` / `get_event_loop`
   / `_get_running_loop` / every `running_loop` / `get_loop` /
   loop-policy spelling occurs zero times in the package; the
   only other `strawberry.utils.inspect` reference is the
   owner's own docstring. No second derivation.
4. Inverse / round-trip pairs — searched. The read has no
   inverse half: it is a read (mode + loop → bool), not an
   encode/decode pair. The carry it reads (bind here,
   close/reset in the runner) is owned by verified Family
   `carried-operation-executor-mode`. No scattered half.
5. Contracts restated in another medium — classified, never
   counted. Oracles: the owner entry matrix (8 rows in
   [test-exec-mode][test-exec-mode], incl. the nested-fact row
   pinning `SYNC|False` where the dispatch refuses, and the 2
   plain-schema fallback rows pinning both ambient
   polarities). Every pin spells literals (`"None|True|True"`,
   `"OperationMode.SYNC"`, `"sync"` / `"async"`) or asserts
   behavioral splits without reading the owner. Projections:
   the owner module grammar (two-questions split +
   plain-schema boundary clause), the guard docstring citing
   the owner by `path::Symbol`, the list asymmetry comment,
   the connection Decision-10 comment. Each medium moves for
   its own reason.
6. Enforcement by omission — family enumerated, each member
   checked. Every `async_executor=` binding composes the read
   by name: 2 call sites + the guard's `bool` parameter (which
   samples nothing). Write pipelines branch nowhere — the
   field dispatches once and routes to `resolve_sync` /
   `resolve_async` (E10). Transports select entry points and
   never branch a resolver return on color (E6). The optimizer
   extension hook passes values through by shape (E3). Zero
   members lack the read; no gap.

### Enumeration

Instrument one: `/tmp/f50-census.py` over all 120 on-disk
package files (117 tracked + 3 untracked: `_multipart.py`,
`utils/lazy.py`, `utils/truth.py`; `__pycache__` excluded) for
the mechanism vocabulary (`operation_is_async`,
`async_execution`, `current_operation_mode`,
`in_async_context`, loop getters, `async_executor`, the guard,
shape detectors, `operation_is_nested`, `SyncMisuseError`,
`OperationMode`, `bind_operation_mode`), re-run at HEAD bytes
via `git grep HEAD` (tracked only — untracked files have no
HEAD bytes). Instrument two: full body reads of the owner,
both `async_executor=` sites, the guard, and every exclusion
site below. Every hit is homed: F1 carries the rule; E1–E10
carry the exclusions.

| Population | Hits | Home |
|---|---|---|
| `operation_is_async` | 1 def + 2 calls + 2 imports + `__all__` + 2 prose mentions, identical WT-vs-HEAD | F1 |
| `async_execution` | 1 def + 17 code calls in 8 files + 6 prose mentions, identical WT-vs-HEAD | E1 (verified f49) |
| `current_operation_mode` | 1 def + 2 internal calls + `__all__`; 0 external readers at both bytes | F1 substrate |
| `in_async_context` | 1 import + 3 calls, all in `exec-mode`; 0 elsewhere at both bytes | F1 substrate |
| loop getters (`get_running_loop` / `get_event_loop` / `_get_running_loop` / `running_loop` / `get_loop` / policy / new / set) | 0 in the package at both bytes | E9 (absent) |
| `async_executor` | 2 call sites + param + docstring + guard condition, identical WT-vs-HEAD | F1 consumers |
| `reject_async_iterable_in_sync_context` | 1 def + 2 calls + 2 imports + 2 prose mentions | F1 consumer seam |
| `raise SyncMisuseError` | 5 (1 dispatch + 4 pipeline) | E1 + E2 |
| `except SyncMisuseError` | 1 (`filters/sets.py:3841`) | E2 |
| value-shape `isawaitable` branches | 15 lines: 12 code branches + relay `:651` conjunct + 2 prose-adjacent | E3 |
| `is_async_only_iterable` | 1 def + 5 value branches | E3 |
| `is_async_callable` | 1 def + 3 code calls | E4 |
| bare `iscoroutinefunction` | 5 code calls (middleware 2, typing 2, views 1) | E4 + E6 |
| `schema.py::_operation_mode` | 1 def + 2 calls | E5 (verified f48) |
| transport entry/selection sites | views 1, middleware 2, consumers 2, routers 0 dispatch | E6 |
| `operation_is_nested` | 1 def + 1 aliased consumer | E7 |
| `DjangoSchema` subclasses overriding the read | 0 | Matrix 6 |

### Challenges

The rule's variation axes, re-derived fresh: fallback polarity
(V1), fallback presence (V2), bound verdict (V3), consumer
count (V4), executor vocabulary (V5), answer shape (V6).
Counts are authoritative definitions of the fact read;
consumers, oracles, and projections that also move are listed,
never counted.

- C1 fallback polarity reversed (V1: unbound answers `False`
  instead of ambient): counts 1 (`operation_is_async`).
  `async_execution`'s own `None` arm is F2's rule — listed,
  not counted (E1: the dispatch's unbound posture answers
  "no disagreement is statable", the fact's answers "best
  available fact"; either changes without the other).
  Oracles listed: the 2 plain-schema fallback rows.
- C2 fallback removed (V2: unbound raises, or answers a third
  state): counts 1 (the `None` arm here;
  `current_operation_mode` keeps answering `None`).
  Consumers listed: both `async_executor=` sites take a bool
  and move only if the answer shape changes (C6).
- C3 third executor color (V5+V3: the new color's verdict):
  counts 1 here (the bound arm) + 1 in the carried
  vocabulary (verified f48) + 1 in F2's reader — one per
  family, each family's own change (coupling noted, not
  counted twice).
- C4 third consumer flavor (V4): counts 0 — it calls
  `operation_is_async()` by name, as both existing calls do,
  and the guard takes the bool as a parameter.
- C5 refusal added to the fact (V2: SYNC-with-loop raises):
  counts 1 — and that change converts F3's contract into
  F2's, which is why it is rejected (E8): the guard both
  call sites feed takes a bool and is unaffected by F2's
  refusal either way.
- C6 answer shape widened (V6: the fact returns the mode
  enum instead of a bool): counts 1 (the def) — both
  consumers listed (they pass the bool onward and re-spell
  their binding), the guard's `bool` parameter listed.

Family-level: every challenge counts at most 1; a new
consumer counts 0.

## Findings

### F1 — the ambient-fallback executor read (single-owned, zero-edit)

- **Contract + variation.** Which executor drives the
  operation here, stated without ever refusing: the bound
  mode when the package runner bound one, the ambient loop
  otherwise. Varies on bound mode × loop presence (V1–V6);
  the never-refuses posture is the contract, not a missing
  error path.
- **Sites + roles.** Definition: 1
  ([exec-mode][exec-mode]`::operation_is_async`, `:118–:127`,
  incl. its two-line `None` arm). Consumers: 2 calls in 2
  files (`list_field.py:1735`, `connection.py:2155`, both as
  `async_executor=`) + the guard seam that takes the bool
  (`utils/querysets.py::reject_async_iterable_in_sync_context`,
  1 def + 2 calls, sampling nothing). Oracles: owner matrix
  (8 rows — `### Matrix` axis 5), notably the nested-fact row
  (`SYNC|False` where the dispatch refuses) and the 2
  plain-schema rows (both ambient polarities). Projections:
  owner grammar, guard docstring, list asymmetry comment,
  connection Decision-10 comment.
- **Challenges.** C1–C6 above: every change counts at most 1
  definition, 0 for a new consumer.
- **Owner + lifetime.** Principle 7: the owner is
  [exec-mode][exec-mode] — the neutral leaf both legitimate
  consumers already import (moving the read into either
  consumer would make the other import a sibling flavor for
  its machinery), beside F2's reader with which it shares
  only the substrate. The shared mechanism is already shared
  by name: both readers compose `current_operation_mode()`
  (its only 2 calls) and upstream `in_async_context()`.
  Pure derivation, not cached (principle 4); no stored state
  beyond the carried binding, whose lifetime verified Family
  `carried-operation-executor-mode` owns.
- **Migration.** None — zero-edit. No production, test, or
  doc line moves. Two composition shapes considered and
  rejected: defining `async_execution` via this read
  re-reads the mode (a second `ContextVar` observation point
  inside one verdict) and couples the refusal contract to
  the fact contract — a fallback-polarity change to the
  fact would ripple into the dispatch (principle 8:
  observation point moves; principle 3: two decisions
  agreeing today with separate reasons to change stay
  separate). Defining this read via `async_execution`
  inherits the refusal the fact's contract forbids (the
  guard takes a bool; routing through a raiser changes the
  exceptions raised). The residual identical two lines are
  the spelling of "absent means sample ambient" at each
  question — a helper relieves no change obligation, since
  no single rule's change moves both arms.
- **Distinct behavior.** The refusing dispatch stays in
  verified F2 (E1); the carried vocabulary + binding stay in
  verified f48 (E5); every refusal seam keeps its own
  wording (E2); value/shape classification stays separate
  (E3, E4); transports keep selecting entries (E6); nesting
  stays separate (E7); pipelines keep running their color's
  body (E10). The intentional F2/F3 separation is already
  recorded at the owner (module docstring "Two questions are
  asked of that one fact, and they are different questions"),
  so no docstring edit is owed.
- **Behavioral proof.** `static-reviewed`. One definition
  body + both call-site bodies + the guard body read at WT
  bytes; whole-package mechanism censuses closed at WT and
  HEAD bytes with identical counts; oracles read (not run —
  the gate owns suite-green; no pytest ran in this item).
  Nothing ordering-, transactional-, or async-sensitive was
  judged: the verdict is body-composed-by-name (DRY.md's
  inspection-alone clause). Wrong result (a) "a second
  definition hides under another spelling" is rejected by
  the mechanism censuses (1 def; `in_async_context` 1 import
  + 3 calls owner-only; external mode readers 0; loop
  getters 0 incl. every policy/new/set spelling; call
  counts identical HEAD-vs-WT). Wrong result (b) "a call
  site restates the arms" is rejected by both body reads
  (each passes `operation_is_async()` as `async_executor=`;
  the adjacent `is_async_only_iterable` check at
  `list_field.py:1731` / the guard's `:525` branches on the
  returned value's shape — two inputs, two jobs, one call).
  Wrong result (c) "a flavor reads the executor without the
  read" is rejected by the axis-6 family enumeration (every
  `async_executor=` binding composes the read; pipelines
  and transports branch on nothing).
- **Structural gate.** None owed. Three plausible bypasses,
  each judged against the gate-only bar (justified
  population, never a bespoke existence test per helper —
  f48/f49 precedent, verifier-endorsed):
  - sampling `in_async_context` for an executor question:
    plausible (the easiest mistake), but the population is
    unjustified — the same token legitimately answers "may I
    touch the ORM here" (the owner module's own documented
    split), so a reference census conflates two jobs and
    reddens on the first legitimate ORM-touch read; it would
    be weakened, not fixed. Standing enforcement is the
    docstring grammar (principle 10) + the nested-fact
    oracle, which fails any loop-sampling second body
    (`SYNC|False` under a running loop). CONVERGE with the
    verified f48/f49 bypass judgments on fresh evidence
    (this item's censuses + body reads are its own).
  - reading `current_operation_mode` externally and
    re-spelling the arms: population closable (0 external
    readers today at both bytes), but the bypass is
    implausible — the leaf read sits next to the nullable
    reader, and no author reaching for it has a reason to
    re-spell arms instead of calling the fact. A census
    would guard a bypass nobody has a reason to write
    (f48 bypass-1 analog).
  - the guard sampling for itself (dropping the `bool`
    parameter): unjustified — the guard's own docstring
    forbids it with the reason (nested sync-in-async), and
    no syntactic population distinguishes "guard that takes
    the fact" from "guard that reads it" beyond this one
    seam. The docstring clause + the parameter shape IS the
    mechanical closure.
  The package-wide censuses in this artifact are the
  first-run check that the rule currently holds, and the
  in-tree oracles pin every contract verdict. Negative
  control reasoned: a hand copy of the read body passes
  every behavior oracle (the copy is correct), which is
  exactly why no new oracle is proposed as a gate. No
  failability run is owed: nothing lands, so no divergence
  exists to prove catchable.
- **Coupling.** None. Zero-edit verdict; a third executor
  color (C3) would move one arm per family — noted, not a
  landing dependency.
- **Freshness.** WT (`git hash-object`) / HEAD (`git rev-parse
  HEAD:<path>`), same-kind pairs: `exec-mode` `b86a08cd` /
  `b86a08cd` (CLEAN), `list_field` `f7b75c2a` / `3842542a`,
  `connection` `6c4b01f9` / `38491372`, `querysets` `6d471bd7`
  / `adc74b64`, `schema` `7390c985` / `f3b6df8f`, `op-state`
  `5f6f255d` / `009714fd`, `relay` `63bbba0b` / `037723cd`,
  `types/relay` `a9b90a17` / `a200f190`, `types/resolvers`
  `5abd9b93` / `2c588030`, `mutations/fields` `3368f696` /
  `0fada991`, `auth/mutations` `8d9e8561` / `101dbf82`,
  `auth/queries` `4f3ab00f` / `4f3ab00f` (CLEAN),
  `utils/typing` `1fa47d59` / `defbe7ee`,
  `middleware/request_body` `1febddbc` / `63a9a4a8`, `views`
  `c944b4be` / `fbf00ddf`, `consumers` `6e48bd70` / `8e33fc3c`,
  `optimizer/extension` `8e3fe7c1` / `b7b6c434`,
  `optimizer/_context` `274a138b` / `274a138b` (CLEAN),
  `_graphql_core_patches` `efadf7fb` / `b4737d78`,
  `resource_policy` `f95f1580` / `9faff1a8`, `filters/sets`
  `14884190` / `76abccb0`, `types/base` `e7a62d32` /
  `e0ad32aa`, `operation_lease` `d1d272c5` / `d1d272c5`
  (CLEAN), `test_execution_mode` `724ed67f` / `724ed67f`
  (CLEAN), live `test_list_field_async_api` `4a570915` /
  `4a570915` (CLEAN). Census population: 120 on-disk files
  (117 tracked + 3 untracked). Core counts identical
  WT-vs-HEAD (`operation_is_async` 8/8, `async_execution`
  37/37, `current_operation_mode` 4/4, `in_async_context`
  5/5, `async_executor` 5/5, loop getters 0/0). Any
  fingerprint change reopens the finding.

### E1 — `async_execution` and its 17 consumers (boundary, verified f49)

1 def + 17 code calls in 8 files (`types/resolvers.py` 6,
`types/relay.py` 2, `connection.py` 2, `relay.py` 2,
`list_field.py` 2, `mutations/fields.py` 1, `auth/mutations.py`
1, `schema.py` 1) + 1 transitive consumer
(`auth/queries.py::current_user` via `_make_auth_field`,
branching on nothing itself) — counts re-derived fresh,
call-site bodies read. Contract difference: refuses the
unanswerable combination (SYNC executor + running loop) with
a typed error naming both recourses; the fact never refuses.
The split is load-bearing: posit dropping F2's refusal and
the guard both F3 call sites feed (taking a bool) is
unaffected — and posit reversing F3's fallback polarity and
F2's unbound arm answers a different question ("no
disagreement is statable") that need not follow. Boundary:
verified Family `async-execution-dispatch-decision` owns the
refusing dispatch; this family owns the fact read. Trigger: a
third reader needing a different absence posture reopens the
substrate, not the readers.

### E2 — the four pipeline `SyncMisuseError` raises (excluded, CONVERGE)

`querysets.py:223` (hook-awaitable), `:526`
(async-iterable source — the guard's own raise), `:3290`
(sidecar-awaitable), `:4835` (sync-source-awaitable), plus
the 1 `except SyncMisuseError` site (`filters/sets.py:3841`,
translating to a "use apply_async" `RuntimeError`). Contract
difference: each refuses a produced VALUE on a sync path
(detect + dispose + raise with per-seam recourse) — none
reads the mode or the loop, none answers which executor
drives. The TYPE is shared, the contracts differ. CONVERGE
with the verified File `utils/execution_mode.py` R3 + the
rejected `sync-boundary-recourse-wording` family (12
wordings / 9 files, each single-owned) on fresh evidence.
Trigger: a raise conditioned on mode × loop rather than
value shape.

### E3 — value-shape completion branches (excluded)

12 code branches + the relay `:651` conjunct:
`connection.py:874` (post-upstream completion),
`relay.py:659` (post-guard completion), `:767` (inside the
`_gather` coroutine), `:780` (sync-branch guard arm),
`types/resolvers.py:766,836,911` (inside already-async
coroutines awaiting an `AwaitableOrValue`),
`optimizer/extension.py:1171` (pass-through hook),
`querysets.py:220,245,3288,3321,3327,4803` (awaitable
detect/dispose/consume arms),
`_graphql_core_patches.py:152–156` (residual-awaitable
completion), and the 5 `is_async_only_iterable` branches
(`list_field.py:1311,1315,1731`, `resource_policy.py:1369`,
the guard's `:525`). Contract difference: branch on what a
produced VALUE is (awaitable / async-only or not), never on
which executor drives — zero mode/loop reads across every
body read. The closest shape — relay `:651`'s
`not async_execution() and isawaitable` — conjoins the
verdict with a value-shape check; it does not recompute the
verdict. Trigger: a value branch conditioned on the driving
executor rather than the value shape.

### E4 — resolver-shape classification (excluded, CONVERGE)

`is_async_callable` (1 def, 3 code calls —
`types/base.py:503` validation, `connection.py:2210` +
`list_field.py:1778` per-construction commitment) and bare
`iscoroutinefunction` (5 code calls:
`middleware/request_body.py:147,168`, `utils/typing.py:221,231`,
`views.py:594`). Contract difference: classify what a
callable IS at construction/selection/validation time, never
which executor IS DRIVING at operation time. Pinned at two
sites: `list_field.py:1778` commits the wrapper
per-construction while `:1616` dispatches per-call and
`:1735` states the fact per-call — three moments, three
jobs. CONVERGE with the verified File
`utils/execution_mode.py` R4 on the fresh census. Trigger: a
shape check used to branch a resolver return at runtime.

### E5 — the carried fact and its publication (boundary, verified f48)

`OperationMode`, `_OPERATION_MODES`, `bind_operation_mode`,
`current_operation_mode`, `schema.py::_operation_mode`,
`_OperationModeMarker`, `_declared_operation_mode`, the
runner bind. Contract difference: the fact the read READS
vs the question it ANSWERS. This family consumes
`current_operation_mode` by name (1 of its 2 internal
calls); verified Family `carried-operation-executor-mode`
owns the carry. Trigger: a reader needing a different fact
(a new color, a new absence posture) reopens f48's S1, not
this read.

### E6 — transport entry selection (excluded)

`views.py:594` (sync/async view wrapper at `as_view()` time),
`middleware/request_body.py:147,168` (chain color),
`consumers.py:1186,1194` (`subscribe` / `stream`
pass-through entry calls), `routers.py` (no dispatch
surface). Contract difference: choose WHICH entry point runs
— the flag's cause — while the read states the carried
effect; no site branches a resolver return on its own color.
Trigger: a transport branching a resolver return on its own
color instead of the carried mode.

### E7 — `operation_is_nested` (excluded, CONVERGE)

1 def (`op-state:391`) + 1 aliased consumer
(`optimizer/extension.py:1126`, passing `nested=` to the
optimizer frame only). Contract difference: runner nesting
vs executor color are independent facts over separate
storage (`_RUNNER_SCOPES` via `_live_scope` vs
`_OPERATION_MODES` via `current_operation_mode`) with
separate readers and no combined predicate. The color half
of the combination is pinned by the nested-fact oracle row
(inner op reads SYNC while nested). CONVERGE with the
verified File `utils/execution_mode.py` R5 on the fresh
census. Trigger: a consumer needing both answers as one
predicate.

### E8 — a refusing fact read (considered, rejected)

Considered: giving the fact read the refusal (SYNC-with-loop
raises) so both readers share one "honest" shape.
Rejected: the guard both call sites feed takes a `bool` and
has its own answer to every outcome — a refusal there would
fire inside a `def` resolver path that the async executor
can still complete (the list field returns the guard-gated
coroutine for the executor to await; the connection field
passes the iterable to native async completion). The refusal
belongs to the dispatch question, which keeps it (E1).
Trigger: a fact consumer needing the unanswerable
combination refused rather than stated.

### E9 — loop-getter plumbing (excluded, absent)

Zero `get_running_loop` / `get_event_loop` /
`_get_running_loop` / `running_loop` / `get_loop` /
loop-policy / new-loop / set-loop occurrences in the
package at both bytes; the only ambient-loop token anywhere
is `in_async_context`, owner-only. No body to converge
with; the trigger ("a loop read used as an executor
verdict") is armed on the empty population and unfired.

### E10 — single-boundary pipeline execution (excluded)

`run_in_one_sync_boundary` + the write-pipeline async
variants (mutations/forms/rest_framework resolvers): run the
sync body on one worker under the async surface. Contract
difference: executes already-dispatched work — the FIELD
dispatched once (`mutations/fields.py:323`) and routed to
`resolve_sync` / `resolve_async`; the pipeline branches on
no executor input. Standing `one-sync-boundary` family
territory. Trigger: a pipeline branching on the executor
instead of running its color's body.

## Defects

None found while tracing. Checks performed for contract: 6
docstring-vs-body pairs at the fact seams (the owner grammar
vs the two arms + the never-refuses posture; the guard's
"never a reading this guard takes for itself" vs the `bool`
parameter + 0 internal samples + the 2 composing call
sites; the list-field asymmetry comment vs `:1731` +
`:1735` + `:1778`; the connection Decision-10 comment vs the
committed split + `:2152–:2155`; the `is_async_only_iterable`
"one spelling" clause vs the 1-def census; the
`is_async_callable` wrapper-shape contract vs the `:221` +
`:231` arms) — every claim matches its body at WT bytes.
The `:1735` / `:2155` regions are content-identical
HEAD-vs-WT, so no concurrent hunk bears on any verdict.

## Pending execution

None. Every verdict is `static-reviewed` (closed censuses at
both bytes, body comparison, pinned oracles read —
inspection decides; nothing ordering-, transactional-, or
async-sensitive was judged). No `proof:` entry: nothing
lands, so no failability probe is owed. No `gate:` entry:
zero-edit, no regression witness needed. No shared-tree
pytest ran (the gate owns suite-green). Sharded and PG cells
are inapplicable by construction: the traced surface is
carried-mode reads × ambient-loop reads at resolver seams,
reaching no database, alias, or dialect decision — stated
for Worker-2 to judge.

## Judgment

REJECT the consolidation: the ambient-fallback executor read
is single-owned — one definition, 2 consumer calls in 2
files composing by name at both bytes, six challenges
counting at most 1, zero external mode/loop readers — and
the verdict is therefore a proved zero-edit: no tracked file
changed, no test added, no `## Owned changes` row owed. Ten
exclusions carry contract differences plus triggers (E1 +
E5 verified-family boundaries, E2/E4/E7 converge on
standing rows with fresh evidence, E3/E6/E8/E10 fresh
splits, E9 absence); zero defects; no new index rows.

Worker-0 instructions: (a) tick the plan item Family
`ambient-fallback-executor-read` as verified under Run
`0.0.15 2026-10-01-11` once Worker 2 agrees, transcribing
the family row to `consolidated` (single-owned: F1 counts
≤1 per challenge, consumers by name — f48/f49 precedent for
the single-owned-zero-edit transcription); (b) no `## Owned
changes` row; (c) no new index rows — every exclusion is a
boundary on an existing, queued, or verified row, not a
family; (d) no queued family depends on this verdict.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for
verification). Item-scoped attribution vs
`ITEM_BASELINE=67dcdf2e91497f6b616966108387c0ccbcced018`:
`git diff <baseline> -- <three indexed paths>` is empty —
all WT-vs-HEAD dirt predates the baseline window (f47
ledgered hunks + concurrent truth migration) and was never
touched; the artifact itself is a new untracked file, the
item's only output. The [plan][plan] `## Owned changes`
ledger gains no row from this item. No `uv run ruff` run (no
`.py` touched; `.md` is outside ruff format scope; the
census script lives in `/tmp`, outside the repo). No
shared-tree pytest run (see `## Pending execution`). No
`docs/dry/temp-tests/` scratch created. Three workspace runs
at `dry/ambient-f50/consolidate` (slot-2, each
provenance-fresh, shared tree unmoved since sync), all
green: `basedpyright` 0 errors / 0 warnings / 0 notes
(`dry-20261001T205159-70e30d`), `check_any` 128 uses at 89
sites exit 0 (`dry-20261001T205211-a49692`),
`check_truthful_reads --check` 119 files tier-1 0 / errors
0 (`dry-20261001T205212-1f193b`) — tree-state results
matching the run-11 baseline, zero-edit item. No new cast /
`Any` / suppression (no code changed; `ALLOWED_ANY`
untouched). No commit. mypy never run, never cited.

## Independent verification (Worker-2)

Own trace, derived fresh with this pass's instruments before
`## Findings` was opened. Rule: the statable executor fact —
bound mode when the runner bound one, ambient loop otherwise,
never refused.

- Definition (1):
  [exec-mode][exec-mode]`::operation_is_async` (`:118–:127`).
  Whole-package `def` census: exactly 1 at WT and at HEAD. No
  second definition under any spelling.
- Consumers (2 calls): `list_field.py:1735` (WT; `:1788` at
  HEAD) and `connection.py:2155` (WT; `:2137` at HEAD), both
  composing by name as `async_executor=operation_is_async()`
  into `utils/querysets.py::reject_async_iterable_in_sync_context`.
  Guard seam verified by body read: takes `async_executor:
  bool` (`:502`), samples nothing, fires at `:525–:529`; its
  docstring names the owner by `path::Symbol` and states the
  never-samples split with the nested-sync reason.
- Substrate (shared by name, not counted): `in_async_context`
  1 import + 3 calls owner-only; `current_operation_mode` 1
  def + 2 internal calls + `__all__`, 0 external readers;
  `_OPERATION_MODES` owner-only; loop getters 0 package-wide
  at both bytes incl. every policy/new/set spelling
  (`get_event_loop`, `get_running_loop`, `new_event_loop`,
  `set_event_loop`, policy variants, `run_until_complete`);
  the 5 `import asyncio` files use only
  Lock/Task/shield/isfuture/Future/CancelledError/wrap_future
  (no loop sampling); `create_task` is the only further HEAD
  `asyncio.` use. `OperationMode` external refs are the carry
  side only (schema marker construction, runner bind);
  `OperationLease` external uses are other subjects'
  bindings.
- Oracles (read + run, never rewritten):
  [test-exec-mode][test-exec-mode] pins the full matrix in
  literal strings (bound SYNC/ASYNC, the SYNC-under-loop
  disagreement row `SYNC|False` where the dispatch refuses,
  both plain-schema fallback polarities). Test file CLEAN
  (`724ed67f` both bytes); item diff on tests empty.
- Owner this pass would choose:
  [exec-mode][exec-mode]`::operation_is_async` — the neutral
  leaf both consumers already import; no move. Zero-edit.
- Posited changes (own): fallback polarity (1: the `None`
  arm here; the dispatch's arm is F2's rule, listed not
  counted); fallback removal (1); third color (1 here + 1
  per family, coupling noted); new consumer (0, by name);
  refusal added to the fact (1 — and converts the contract
  into F2's, hence rejected); answer shape widened (1 def,
  consumers + guard param listed). Every count ≤1, 0 for a
  new consumer.

Reconciliation vs `## Findings`: no count differs. The 8/37/4/5/5
raw token counts and their WT-vs-HEAD identity reproduce
exactly (this pass classifies the 37 `async_execution` hits
as 1 def + 17 code calls in 8 files + 6 prose + imports and
`__all__`, matching E1's 17/call-site table line for line);
`raise SyncMisuseError` 5 (1 dispatch + 4 pipeline),
`except` 1, `is_async_only_iterable` 1 def + 5 branches,
`is_async_callable` 1 def + 3 calls, bare
`iscoroutinefunction` 5 code calls, `operation_is_nested` 1
def + 1 aliased consumer, `schema.py::_operation_mode` 1 def
+ 2 calls — all reproduce. All 25 freshness pins re-hashed
same-kind by this pass match (3 indexed + querysets/schema/
op-state + 18 further artifact pins); population 117 tracked
+ 3 untracked = 120. Zero-edit verified independently:
`git diff 67dcdf2e… -- .` is the plan edit alone, the package
subtree diff is empty, the artifact is untracked.

Judgments (a)–(f): (a) single-ownership CONFIRMED on the
reproduced censuses above — 1 def, 2 by-name calls, zero
external mode/loop readers at both bytes. (b) The
principle-3 two-`None`-arms call CONFIRMED as load-bearing
and correct: the arms are identical in spelling
(`if mode is None: return in_async_context()`) but
independent in contract — the fact's arm is "best available
fact", the dispatch's is the unbound posture of a refusing
question; C1's "either changes without the other" holds
(unbound-dispatch-fail-closed would not move the fact, whose
guard consumers need ambient truth on plain schemas).
F2-via-F3 fails (the dispatch still needs its own mode read
for the refusal — a second observation point — and couples
the refusal contract to the fact contract, saving nothing
since its own ambient read stays). F3-via-F2 fails (inherits
the forbidden refusal — verified the guard's `bool`
parameter and both firing paths: dispatch `:148–:156` vs
guard `:525–:529`, different messages and layers; decisive
is the connection unconditional guard site, where
non-async-only sources under SYNC+loop proceed today via
guard no-op and a refusing fact would break them —
principle 8). No shared-absence helper owed: it relieves no
change obligation, and the substrate is already shared by
name. (c) No-gate CONFIRMED against the f48/f49 gate-only
bar: bypass 1 (loop sampling) has an unjustified population
(the token legitimately answers the ORM-touch question per
the owner module's documented split — a reference census
conflates two jobs and would weaken, not fix); bypass 2
(external mode read) is closable but implausible, a bespoke
per-helper census (f48 bypass-1 analog); bypass 3 (guard
self-sampling) is closed by the docstring clause + the
single-seam parameter shape. Reasoned negative control
stands; the artifact's censuses are the first-run check;
no failability run owed (nothing lands). (d) Pending-None
CONFIRMED — the item meets the f48/f49 bar (single-owned
zero-edit asserts no equivalence: 1 def + by-name
composition + closed censuses are structural facts, so no
proof is owed), and this pass corroborated beyond it with
its own focused oracle run (`pytest
tests/utils/test_execution_mode.py --no-cov`: 8 passed),
confirming the described behavior — incl. the
agreement-today and never-refuses split — at current
bytes. Plan item reads plain `verified`. (e) All ten
exclusions VERIFIED, each with contract difference +
trigger + home: E1/E5 boundaries on consolidated f49/f48
(the 17-call table re-derived line for line); E2/E4/E7
genuine converges on standing R3/R4/R5 (rows read; E4/E7
triggers identical to standing) with fresh censuses
reproduced; E3/E6/E8/E10 fresh splits verified by body
reads (relay `:651` conjoins rather than recomputes; all
three E6 site bodies select entries, routers have no
dispatch surface; `mutations/fields.py:323` dispatches
once); E9 absence verified 0/0. (f) No-new-index-rows
CONFIRMED: boundaries, converges, fresh splits homed
in-artifact, one absence, and E8 whose durable home
already exists (owner docstring "Two questions are asked
of that one fact" clause, verified present) — no sub-rule
decomposed, no fresh rejection row owed.

Independent consolidation search (step 5): consumer-merge
(distinct flavors/branches), read-into-guard (docstring
forbids + nested-sync reason), both composition directions
(both fail, above), shared-absence helper (no obligation
relieved), nested-predicate merge (E7), wording unification
(E2) — no real consolidation exists. Coupling: none.
Sharded/PG inapplicable-by-construction CONFIRMED
(ContextVar + loop reads; no database, alias, or dialect
decision). Banned test words: no new test/production file
— none. Matrix: all six axes discharged against the
rule's real surface (axis-6 family = the guard's call
sites, 2/2 composing by name; default-branch omission is
behavior-neutral per the guard contract + docstring).

Gates re-run by this pass, tree-state: basedpyright 0
errors / 0 warnings / 0 notes; check_any 128 uses at 89
sites exit 0; check_truthful_reads 119 files tier-1 0 /
errors 0 — all match the run-11 baseline. mypy never run,
never cited. Ruff on touched paths: vacuous (zero tracked
edits — stated); owner-file hygiene run green
(`ruff format --check` formatted,
`ruff check` all passed). Artifact LINK DEFINITIONS: all
10 canonical group headers present, all 3 used refs
defined.

Defects: none. Two record-accuracy observations on
reasoning prose (not defects, carried for Outcomes
transcription): (O1) E8's parenthetical locates the
refusal-inheritance break imprecisely — the sharp
principle-8 break is the connection unconditional guard
site on non-async-only sources under SYNC+loop (guard
no-ops today; a refusing fact would raise there), plus
message/layer changes on firing paths. (O2) The no-gate
"nested-fact oracle fails any loop-sampling second body"
sentence overclaims — that oracle pins the read path;
hypothetical second bodies elsewhere would trip
consumer-surface behavior oracles instead. Neither touches
a count, contract, or the verdict.

Verdict: `verified`, plain. No pending execution; no
`## Owned changes` row; no new index rows.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[plan]: dry-0_0_15.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[exec-mode]: ../../django_strawberry_framework/utils/execution_mode.py

<!-- tests/ -->
[test-exec-mode]: ../../tests/utils/test_execution_mode.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
