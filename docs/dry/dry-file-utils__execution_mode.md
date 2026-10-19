# DRY review: `utils/execution_mode.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target `django_strawberry_framework/utils/execution_mode.py` owns one
fact — which GraphQL executor is driving the current operation — and
the two questions resolvers ask of it. `OperationMode` is the
two-member color vocabulary (`SYNC` = `execute_sync`, `ASYNC` =
`execute` / `stream` / `subscribe`); `_OPERATION_MODES` carries it as
an `OperationLease` in a `ContextVar`; `bind_operation_mode` binds it
and hands the runner everything that undoes the binding;
`current_operation_mode` reads the lease; `operation_is_async` states
the fact with an ambient-loop fallback for plain `strawberry.Schema`;
`async_execution` is the dispatch decision that refuses the
sync-executor-with-running-loop disagreement with `SyncMisuseError`
rather than guessing.

Trace basis is HEAD bytes (`0c0537e2`, blob `9805cdaf`, 153 lines):
worktree hash equals HEAD blob, `git status --short` names no path
under the target, the item-scoped diff vs `ITEM_BASELINE`
`06dfd4b5aa5e2858ad7f0180f695f57545e8c2b8` is empty, and no
`## Owned changes` ledger row names this file (plan-wide census:
`execution_mode` appears only in the file-item row, the dispatch
brief, and the unrelated `operation_lease` row). Zero-edit file item:
nothing tracked touched, no consolidation, no plan edit. Dirt
elsewhere in the tree is concurrent work, left alone.

Fact chain, traced end to end: upstream hands `sync` to
`schema.py::DjangoSchema.get_extensions`; `schema.py::_operation_mode`
translates it once to the enum; the schema puts an
`extensions/operation_state.py::_OperationModeMarker` in the chain it
built (admitted and refusal paths alike); the runner reads the marker
once (`_declared_operation_mode`) and binds the mode everywhere it
binds state (`_bind`), closing the lease and resetting the token on
every exit path including stream resumes. Upstream ground truth
verified in the installed `.venv` strawberry
(`schema/schema.py`): `get_extensions(sync=True)` is called only on
the `execute_sync` path (`:821`); `execute` (`:747`) and
`stream`/`subscribe` (`:1158`) call `get_extensions()` with the
`False` default, and `subscribe` (`:1090`) is a thin wrapper around
`stream` — so the "subscribe is ASYNC" clause holds by construction.

Consumer census (whole package, re-derived fresh):
`async_execution` — `schema.py` (mutation-window color),
`list_field.py`, `connection.py`, `relay.py`, `types/relay.py`,
`types/resolvers.py`, `mutations/fields.py`, `auth/mutations.py`;
`operation_is_async` — `list_field.py` + `connection.py` (both as the
caller's `async_executor=` answer to
`utils/querysets.py::reject_async_iterable_in_sync_context`, which
takes the reading as a parameter and never samples anything itself);
`bind_operation_mode` + `OperationMode` — `extensions/operation_state.py`
(single bind site) and `schema.py` (marker construction);
`current_operation_mode` — in-module readers plus test lifetime rows.
`in_async_context` is imported nowhere else in the package: the two
fallbacks and the misuse check here are the only ambient-loop reads.

Oracles: `tests/utils/test_execution_mode.py` (clean at HEAD,
`bbe5f97e`: entry-point matrix, the nested-`execute_sync` disagreement
row, both plain-schema fallback rows, the enum pin);
`tests/extensions/test_operation_state.py` mode-lifetime rows
(no-marker chain, nested restore, copied-context reads-nothing,
per-frame binding, cancelled/failed binds-nothing);
`tests/test_list_field.py` three-state executor matrix;
live `examples/fakeshop/test_query/test_list_field_async_api.py`.
Projections: the [`SyncMisuseError`][glossary-syncmisuseerror]
glossary entry (executor-mismatch bullet), the
[ordered-offset dispatch][docs-readme-list-field] prose in
`docs/README.md`, the module docstring grammar, and the consumer
docstrings citing the readers by `path::Symbol`.

## Verification

### Enumeration

Instrument: every node of `ast.Module.body` of the target at HEAD
bytes; count = 15 nodes. Named symbols homed below; every member lands
in a family row, a file-local row, or a rejection.

| # | Node | Home |
|---|---|---|
| 0 | Module docstring (mode-vs-loop disagreement, carried-not-sampled, two questions, plain-schema boundary) | FL2 |
| 1-7 | `__future__` + six imports (`ContextVar`/`Token`, `Enum`, `Any`, `in_async_context`, `OperationLease`, `SyncMisuseError`) | FL1 |
| 8 | `__all__` (5 names) | FL1 |
| 9 | `class OperationMode` + members `SYNC`/`ASYNC` | F1 |
| 10 | `_OPERATION_MODES` lease `ContextVar` | F1 |
| 11 | `bind_operation_mode` | F1 |
| 12 | `current_operation_mode` | F1 |
| 13 | `operation_is_async` | F3 |
| 14 | `async_execution` | F2 |

Count check: 7 top-level names (`__all__`, `OperationMode`,
`_OPERATION_MODES`, 4 functions) + docstring + 7 imports = 15 nodes;
4 names to F1, 1 to F2, 1 to F3, `__all__` + imports to FL1, docstring
to FL2; 0 unhomed.

### Matrix

1. **Cross-flavor policy mirroring.** Read every `SyncMisuseError`
   seam: the three write flavors via
   `utils/querysets.py::sync_pipeline_recourse` (byte-identical
   template by documented design), the Relay recourse, the permission
   recourse, the read-side guards (`reject_async_in_sync_context`,
   `reject_async_iterable_in_sync_context`,
   `reject_awaitable_sync_source`, the orderset post-apply guard),
   and this module's executor-mismatch raise. Each seam's prose is
   owned at its raise (`_disposed_awaitable` documents "the prose
   differs per seam"); the write template explicitly excludes the
   Relay and permission wordings as genuinely different. The
   executor/loop-disagreement contract exists only here. No mirror;
   see R3.
2. **Sync/async twins.** None in the target: all four definitions are
   synchronous readers; the module answers *about* execution color
   and has no color of its own. No twin to compare.
3. **Derived rather than repeated knowledge.** The mode is settled
   once (`schema.py::_operation_mode`, the single `sync: bool` to
   enum translation — whole-package census finds no second
   `OperationMode.SYNC`/`ASYNC` construction site) and carried
   (marker to runner to lease); it is never re-derived. Ambient-loop
   sampling exists only at the three documented sites in this file
   (two fallbacks, one misuse check). No second derivation.
4. **Inverse / round-trip pairs.** Bind lives here, close + token
   reset in the runner's `_Binding` lifecycle — one bind site
   (`operation_state.py::_bind`), close on every exit path. The split
   is ownership (fact vs operation lifetime, principle 7), not a
   scattered pair; see R2.
5. **Contracts restated in another medium.** Production (target +
   marker + runner + translation), oracles (three test files + one
   live module, listed above), projections (glossary entry, README
   prose, module and consumer docstrings). Each medium moves for its
   own reason; the oracle pins spell literals (`"sync"`, `"async"`,
   `"await schema.execute"`, `"worker thread"`) without reading the
   owner. Counted as one definition; the rest are roles, not copies.
6. **Enforcement by omission.** Census of runtime executor dispatch:
   every sync/async branch decision composes `async_execution` (8
   files) or `operation_is_async` (2 files) by name. Adjacent
   async-detections are different rules: `iscoroutinefunction` reads
   classify resolver *shape* at construction/selection time (R4);
   `schema.py`'s `asyncio.get_running_loop` calls are mutation-window
   executor plumbing, not dispatch. No site samples the loop to guess
   the executor; no enforcement gap.

### Challenges

- **F1, carried executor-mode fact.** (a) Rename the `"sync"` /
  `"async"` values: 1 definition (`OperationMode`; the oracle pin is
  an oracle, not counted). (b) Change close semantics so a copied
  context keeps answering: 1 definition, and it is not here
  (`OperationLease.held`/`close`). (c) Bind a further per-operation
  fact the same way: 0 definitions move — the runner declares a new
  lease binding composing `OperationLease` by name. Counts: 1 / 0.
- **F2, dispatch decision with refusal.** (a) Reword the recourse:
  1 definition (the raise here; the glossary bullet is a projection).
  (b) Add a second misuse condition: 1 definition. (c) Add a ninth
  consumer flavor: 0 definitions move — it calls `async_execution()`.
  Counts: 1 / 0.
- **F3, fact read with ambient fallback.** (a) Remove the plain-schema
  fallback: 1 definition (`operation_is_async`;
  `current_operation_mode` keeps answering `None`). (b) Reverse the
  fallback polarity: 1 definition. Count: 1.
- **R1, the four lease-reader twins.** Posit "a copied context keeps
  the last mode": only this reader would move; the runner-scope,
  budget, and optimizer-frame readers keep fail-closed (their
  payloads are not executor facts). No change moves all four without
  moving `OperationLease.held` itself, which is already one
  definition. Not one rule: 4 readers, 0 shared obligations.
- **R3, refusal wordings.** Posit "executor-mismatch recourse gains a
  third option": only the raise here moves; the write-pipeline
  template, Relay, permission, and read-guard wordings answer
  different misuses with different recourses. Count per seam: 1.
- **R6, flag translation placement.** Posit a second `sync`-flag
  consumer: today there is none (both marker constructions are the
  one schema call path); the translation stays at receipt. Count: 1.

## Findings

### F1 `carried-operation-executor-mode` (new family)

- **Contract + variation.** The executor driving an operation is a
  carried per-operation fact: a two-member color settled by entry
  point, bound by the runner as a lease, read through the lease.
  Varies on entry point only; never on thread or loop state.
- **Sites + roles.** Definition: target `OperationMode`,
  `_OPERATION_MODES`, `bind_operation_mode`,
  `current_operation_mode`. Consumers: `schema.py::_operation_mode`
  + `_OperationModeMarker` constructions (fact publication),
  `extensions/operation_state.py::_bind` (bind/close/reset owner).
  Oracles: `tests/utils/test_execution_mode.py` entry rows +
  `tests/extensions/test_operation_state.py` lifetime rows.
  Projections: target module docstring, runner docstring mode
  paragraph, marker docstring.
- **Challenges.** Above; definition count 1 per change (0 for a new
  consumer or a new leased fact).
- **Owner + lifetime.** Owner is the target: it holds the vocabulary
  and the variable every consumer must agree on (principle 7 —
  narrowest module all three consumers already import). Lifetime:
  bound by the runner per operation, closed on every exit path,
  nested operations restore via token; copied contexts read `None`
  after close. No consolidation owed inside a file item; holding
  item is the future family item (Worker-0 routes).
- **Freshness.** Target HEAD `9805cdaf` (== worktree). Runner
  HEAD `b2674a22` WT `d9ed9cc6`; schema HEAD `e6b52335` WT `84f2d5aa`;
  lease HEAD==WT `10c164b7`; oracle HEAD==WT `bbe5f97e`; lifetime
  oracle HEAD `b3a574b1` WT `7509c1cc`. Connected dirt is
  concurrent-external, content-unrelated to the traced lines,
  untouched.

### F2 `async-execution-dispatch-decision` (new family)

- **Contract + variation.** `async_execution()` answers whether a
  resolver may hand back a value only the async executor completes:
  true under ASYNC, false under SYNC-without-loop, `SyncMisuseError`
  naming both recourses for SYNC-with-loop, ambient loop when no
  mode is bound. Varies on bound mode × loop presence; the refusal
  branch is the contract, not an error path.
- **Sites + roles.** Definition: target `async_execution` (including
  its message wording). Consumers (8 files): `schema.py`,
  `list_field.py`, `connection.py`, `relay.py`, `types/relay.py`,
  `types/resolvers.py`, `mutations/fields.py`, `auth/mutations.py`.
  Oracles: the disagreement row in `tests/utils/test_execution_mode.py`
  (typed-error + both recourse substrings), the `test_list_field.py`
  matrix, live `test_list_field_async_api.py`. Projections: glossary
  `SyncMisuseError` executor bullet, README dispatch prose.
- **Challenges.** Above; count 1 per wording/condition change, 0 per
  new consumer.
- **Owner + lifetime.** Owner is the target: the refusal must name
  the call that caused it, so the decision and its wording live at
  the single reader every flavor calls. Pure derivation, not cached
  (principle 4); no stored state beyond F1's binding.
- **Freshness.** Target `9805cdaf`. Consumers (HEAD/WT):
  schema `e6b52335`/`84f2d5aa`, list_field `21380eb7`/`f5b0183e`,
  connection `4894f90f`/`1fca6266`, relay `c3c5aea5`/`e75e2b66`,
  types/relay `52439862`/`4b2a9df5`, types/resolvers
  `72d62dc4`/`640905c6`, mutations/fields `d4edcbb7`/`0e4d5ed1`,
  auth/mutations `d1a59c44`/`84183c89`; oracle `bbe5f97e` clean;
  matrix oracle `038e69ce`/`d78aa5e7`. Dirt concurrent-external,
  untouched.

### F3 `ambient-fallback-executor-read` (new family)

- **Contract + variation.** `operation_is_async()` states which
  executor is driving without ever refusing: bound mode when the
  package runner bound one, ambient loop otherwise. Varies on the
  same two inputs as F2 minus the refusal branch.
- **Sites + roles.** Definition: target `operation_is_async`.
  Consumers: `list_field.py` + `connection.py` (`async_executor=`
  argument). Oracles: fallback rows in `tests/utils/test_execution_mode.py`.
- **Challenges.** Above; count 1.
- **Owner + lifetime.** Owner is the target, beside F2: the two
  readers share the fact but not the contract (a caller needing a
  branch takes F2; a caller passing the fact onward takes F3).
  Stateless read; lifetime is F1's.
- **Freshness.** Target `9805cdaf`; consumers and oracles as in F2.

### FL1 Module mechanics (file-local)

`__all__` (exactly the 5 public names, matching the 5 exported
definitions) plus the import directions (`__future__`, stdlib,
`strawberry.utils.inspect`, sibling lease substrate, `SyncMisuseError`
from `utils/querysets.py`). Challenge: rename an export — only this
manifest and its importers move; no second manifest lists these
names (the module is not root- or `utils`-re-exported). One file,
one challenge, no second site.

### FL2 Module-docstring grammar prose (file-local)

The disagreement account (loop vs executor), carried-not-sampled,
the two-questions split, and the plain-schema boundary clause.
Challenge: restate the disagreement — only this docstring and the
consumer docstrings that cite it move, and the citers quote by
`path::Symbol` reference, never by restating the rule. Projection
owned here; no second site states this grammar.

### R1 Shared lease-`ContextVar` reader driver (rejected)

The four `None if lease is None else lease.held()` readers (target,
`optimizer/_context.py`, `resource_policy.py`,
`extensions/operation_state.py`) share two lines and one mechanism,
not one rule: each answers a different question (executor mode,
optimizer frame, request budget, runner scope) with its own
`None`-contract. A `read_lease(var)` helper would hide which variable
each owner reads while relieving no change obligation — the shared
semantics already live once in `OperationLease.held`.
**Converge** with the verified `optimizer-execution-frame` verdict
("same mechanism, different rules"; this module excluded as a
parallel lease user). Trigger: a read-semantics change that must move
all four readers without moving `held` — none exists while `held`
owns the closed-answers-nothing rule.

### R2 Bind/close reunification (rejected)

Considered: one helper owning both `bind_operation_mode` and the
runner's close/reset. Rejected: close/reset timing belongs to the
operation lifetime the runner owns (per-frame rebinds, adopted
bindings, unwind-on-partial-bind); the bind here deliberately returns
"everything that undoes it" so the runner owns all three. Moving
lifetime into the fact module reverses the dependency (principle 7).
Trigger: a second binder of `_OPERATION_MODES` appears — census
finds exactly one.

### R3 Refusal wording vs the write-pipeline recourse template (rejected)

Considered: routing this message through
`utils/querysets.py::sync_pipeline_recourse` or a shared misuse
template. Rejected: different contracts. The template answers
"async `get_queryset` met in a sync ORM pipeline" with "redefine the
hook sync"; this raise answers "sync executor driving while a loop
runs" with "await `schema.execute(...)` or run the sync call in a
worker thread". The template's own docstring excludes genuinely
different wordings (Relay, permission); this seam is a further one.
Stands beside the rejected `sync-boundary-recourse-wording` family
without joining it. Trigger: a second executor/loop-disagreement
raise appears anywhere.

### R4 Executor fact vs resolver-shape classification (rejected)

Considered: `iscoroutinefunction` / `is_async_callable` reads
(`middleware/request_body.py`, `utils/typing.py`, `types/base.py`,
`connection.py`, `list_field.py`, `views.py`) as second executor
detectors. Rejected: they classify what a callable *is* (construction
or selection time), never which executor *is driving* (operation
time). Different inputs, different moments, different consumers.
Trigger: a shape check used to branch a resolver return at runtime.

### R5 `operation_is_async` vs `operation_is_nested` (rejected)

Considered: one "operation situation" predicate. Rejected: executor
color vs runner nesting are independent facts — a nested sync
operation inside an async one is `SYNC` and nested, and the
`test_a_nested_operation_restores_the_outer_mode_on_the_way_out` row
pins exactly that combination. Different owners, different readers.
Trigger: a consumer needing both answers as one predicate.

### R6 Sync-flag translation placement (rejected)

Considered: moving `schema.py::_operation_mode` into this module
(e.g. `mode_from_sync_flag`). Rejected: the `sync` flag arrives at
`get_extensions`, so the translation stays at receipt beside its only
consumer (the two marker constructions on the one schema call path);
a move adds a hop with no second reader. Trigger: a second
`sync`-flag to mode translation need.

### R7 Dedicated executor-mismatch error (rejected)

Considered: a new exception instead of reusing `SyncMisuseError`.
Rejected: the marker's documented contract is "reserved for sync
boundaries" (`_disposed_awaitable`), and this misuse — a value the
sync executor cannot complete — is exactly that; existing
`except SyncMisuseError` / `ConfigurationError` / `RuntimeError`
handlers (notably `FilterSet.apply`'s dispatcher) already cover it,
and the glossary pins both misuses under the one marker. Trigger: a
consumer needing to distinguish executor-mismatch from async-hook
misuse by type.

## Defects

None. The one candidate checked — the "subscribe is ASYNC" clause,
which no test row executes directly — holds by upstream construction
(`subscribe` is a thin wrapper around `stream`, which calls
`get_extensions()` with `sync=False`); verified in the installed
`.venv` strawberry sources, not assumed.

## Pending execution

None. All behavioral proof is `static-reviewed`: the finding is
single-ownership per change with whole-package censuses re-derived
fresh; no source-mutating probe was needed, no test was run
(`AGENTS.md`: no pytest unless asked), and the gate owns suite-green.

## Judgment

The file is the single owner of the executor-mode fact and both its
readers; every consumer composes by name, every adjacent twin is a
different rule with a recorded trigger, and the upstream flag mapping
the whole chain rests on was verified in the installed sources.
Zero-edit: 3 new families named for Worker-0, 2 file-local rows, 7
rejections (1 converge), 0 defects.

## Index rows for Worker-0

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `carried-operation-executor-mode` | `django_strawberry_framework/utils/execution_mode.py::OperationMode` | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/schema.py`, `django_strawberry_framework/extensions/operation_state.py` | Family `carried-operation-executor-mode` | open |
| `async-execution-dispatch-decision` | `django_strawberry_framework/utils/execution_mode.py::async_execution` | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/schema.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/relay.py`, `django_strawberry_framework/types/relay.py`, `django_strawberry_framework/types/resolvers.py`, `django_strawberry_framework/mutations/fields.py`, `django_strawberry_framework/auth/mutations.py` | Family `async-execution-dispatch-decision` | open |
| `ambient-fallback-executor-read` | `django_strawberry_framework/utils/execution_mode.py::operation_is_async` | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/connection.py` | Family `ambient-fallback-executor-read` | open |
| Module mechanics (`__all__` + import directions) | `django_strawberry_framework/utils/execution_mode.py` (`__all__`) | `django_strawberry_framework/utils/execution_mode.py` | File `utils/execution_mode.py` | file-local |
| Executor-mode grammar prose | `django_strawberry_framework/utils/execution_mode.py` (module docstring) | `django_strawberry_framework/utils/execution_mode.py` | File `utils/execution_mode.py` | file-local |
| Shared lease-`ContextVar` reader driver | `django_strawberry_framework/utils/execution_mode.py::current_operation_mode` (rejection recorded here; CONVERGE with verified `optimizer-execution-frame` on fresh evidence) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/optimizer/_context.py`, `django_strawberry_framework/resource_policy.py`, `django_strawberry_framework/extensions/operation_state.py` | File `utils/execution_mode.py` | rejected |
| Bind/close reunification | `django_strawberry_framework/utils/execution_mode.py::bind_operation_mode` (rejection recorded here) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/extensions/operation_state.py` | File `utils/execution_mode.py` | rejected |
| Executor-mismatch wording vs write-pipeline recourse | `django_strawberry_framework/utils/execution_mode.py::async_execution` (rejection recorded here) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/execution_mode.py` | rejected |
| Executor fact vs resolver-shape classification | `django_strawberry_framework/utils/execution_mode.py::operation_is_async` (rejection recorded here) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/utils/typing.py`, `django_strawberry_framework/middleware/request_body.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/views.py` | File `utils/execution_mode.py` | rejected |
| `operation_is_async` vs `operation_is_nested` | `django_strawberry_framework/utils/execution_mode.py::operation_is_async` (rejection recorded here) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/extensions/operation_state.py` | File `utils/execution_mode.py` | rejected |
| Sync-flag translation placement | `django_strawberry_framework/schema.py::_operation_mode` (rejection recorded here, at owner) | `django_strawberry_framework/schema.py`, `django_strawberry_framework/utils/execution_mode.py` | File `utils/execution_mode.py` | rejected |
| Dedicated executor-mismatch error | `django_strawberry_framework/utils/execution_mode.py::async_execution` (rejection recorded here) | `django_strawberry_framework/utils/execution_mode.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/execution_mode.py` | rejected |

<!-- LINK DEFINITIONS -->

<!-- Root -->
[docs-readme-list-field]: ../../README.md

<!-- docs/ -->
[glossary-syncmisuseerror]: ../GLOSSARY.md#syncmisuseerror

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker-2)

Recorded before opening `## Findings`. Target
`django_strawberry_framework/utils/execution_mode.py` at HEAD blob `9805cdaf`
(153 lines; worktree == HEAD, CLEAN — re-verified by Worker-2:
`git hash-object` of the worktree file and of `git show HEAD:` agree).

### Enumeration (Worker-2, independent)

Instrument: every statement in `ast.Module.body`. Count: 15 (module
docstring + 7 `ImportFrom` + `__all__` Assign + `OperationMode` ClassDef
+ `_OPERATION_MODES` AnnAssign + 4 FunctionDef). Top-level names: 7
(`__all__`, `OperationMode`, `_OPERATION_MODES`, `bind_operation_mode`,
`current_operation_mode`, `operation_is_async`, `async_execution`).

### Sites, roles, definition counts (Worker-2, independent)

Expected owners and consumers from my own trace:

- F-carry (executor mode carried from entry point to resolver): ONE
  definition chain, not one token. `schema.py::DjangoSchema.get_extensions`
  is handed upstream's authoritative `sync` flag;
  `schema.py::_operation_mode` translates it to `OperationMode`
  (2 call sites: the admitted chain and the refused-configuration chain);
  `extensions/operation_state.py::_OperationModeMarker` carries it in the
  chain; `_declared_operation_mode` reads it back (exact-type, first
  found); the runner binds it via `bind_operation_mode` (sole call site
  at `operation_state.py` `#"bindings.append(_Binding(*bind_operation_mode")`);
  `current_operation_mode` reads it back through the lease. Change
  challenge (add a third executor color): `_operation_mode`, the marker
  read, and both readers move — but they are stages of one carried fact,
  one family. Owner: this module for the fact + readers;
  `schema.py::_operation_mode` for the flag translation;
  `operation_state.py` for the carry mechanism.
- F-dispatch (`async_execution`): the THIRD state (SYNC executor + running
  loop → refuse with `SyncMisuseError` naming both recourses) is the
  rule; consumers (my census): `types/resolvers.py` (5 call sites),
  `types/relay.py` (2), `connection.py` (2), `relay.py` (2),
  `list_field.py` (2: one dispatch + one `is_async_context=` pass),
  `mutations/fields.py` (1), `auth/mutations.py` (1), `schema.py` (1) =
  8 consumer files + owner = 9 files. All are consumers (call by name),
  none restates the refusal. The `SyncMisuseError` raises in
  `utils/querysets.py` (hook-awaitable, async-iterable-source,
  sidecar-awaitable, sync-source-awaitable refusals) share the exception
  TYPE, not this dispatch contract — expected rejections.
- F-fallback (ambient-loop fallback read): `operation_is_async` is the
  fact reader (bound mode or ambient loop, never refuses);
  `current_operation_mode` is the nullable fact both readers share
  (2 internal callers, plus oracles). `operation_is_async` consumers:
  `connection.py` (`async_executor=` pass-through) and `list_field.py`
  (`async_executor=` pass-through) only; the querysets guard takes the
  answer as a parameter and never samples itself. `schema.py`'s two
  `asyncio.get_running_loop()` reads are executor plumbing for
  `run_in_executor` (mutation-window thread dispatch), not executor-mode
  decisions — expected rejection. `in_async_context` has no other
  package call site outside this module's 3 reads.
- `operation_is_async` vs `async_execution` (axis 2): NOT twins to
  merge. One states the fact for callers with their own answer to every
  outcome; the other refuses the unanswerable combination. Posit
  dropping the refusal: `operation_is_async` callers are unaffected (the
  guard they feed takes a bool). Distinct contracts, shared fact —
  expected: two families sharing one substrate reader.
- `bind_operation_mode` returning `(var, token, lease)`: consumed only
  by the runner's `_Binding` pack. `current_operation_mode` consumed
  only by the two readers + oracles. `OperationLease` mechanics owned by
  `utils/operation_lease.py` (consumer relationship, not duplication).
- R1 candidate (frame vs mode): `optimizer/_context.py`'s
  `_execution_frames` / `begin_execution_frame` / `end_execution_frame`
  is the same lease-behind-ContextVar SHAPE over a different fact (the
  optimizer's per-execution scratch frame vs the operation's executor
  mode). The shape's owner is the verified `optimizer-execution-frame`
  family; expected CONVERGE with that verdict on fresh evidence
  (distinct payload, distinct lifecycle owner, shared lease mechanism
  owned by `utils/operation_lease.py`).
- Subscribe-ASYNC: `OperationMode` docstring + `_operation_mode` claim
  `subscribe` → ASYNC. Upstream proof obligation: installed
  strawberry-graphql 0.324.0 `schema.py` — `subscribe` delegates to
  `stream`, which calls `get_extensions()` with the default
  `sync=False`; only `execute_sync` passes `sync=True`. Expectation:
  cleared, no defect.
- Oracles (independent, never rewritten): `tests/utils/test_execution_mode.py`
  (8 rows incl. the nested-sync disagreement and the plain-schema
  fallback), `tests/extensions/test_operation_state.py` mode-lifetime
  rows, `tests/test_list_field.py` three-state matrix (cited by the
  oracle module docstring), live
  `examples/fakeshop/test_query/test_list_field_async_api.py`.
  Projections: module docstring, `docs/README.md` list-field dispatch
  prose, glossary `#syncmisuseerror` third bullet.
- Matrix expectations: axis 1 — single-surface infra, no flavor mirror;
  axis 2 — the two readers + sync/async pipeline pairs elsewhere are
  consumers, judged above; axis 3 — carried-vs-sampled is THE rule,
  single definition; axis 4 — bind/close round-trip owned by
  `operation_lease.py` + runner; axis 5 — docstring + README + glossary
  projections listed, not counted; axis 6 — census of ambient-loop
  readers is complete at this module + the two `schema.py` executor
  plumbings; no resolver samples the loop for dispatch.

Zero-defect expectation: the module is a 4-function fact substrate with
a complete oracle pin; I expect no defect. Item-scoped diff expectation:
empty on the target (CLEAN), artifact only.

### Reconciliation (Worker-2, after reading `## Findings`)

Verdict: **verified**. Every expectation above stands; differences: none
of substance. Per-judgment results:

- Enumeration: ENDORSED member-by-member. My independent AST count
  (15 statements; 7 top-level names) matches W1's exactly, and the
  homing table covers nodes 0–14 with 0 unhomed (4 names F1, 1 F2,
  1 F3, manifest+imports FL1, docstring FL2).
- F1 `carried-operation-executor-mode`: ENDORSED. Chain re-traced:
  `schema.py::_operation_mode` is the sole `sync`-to-enum translation
  (no second `OperationMode` construction site package-wide);
  `_refused_chain` + `_admitted_chain` both consume it; marker read
  is exact-type-first-found; `bind_operation_mode` has its sole call
  site at the runner's `_Binding` pack. All 6 F1 fingerprints
  reproduce byte-exactly (13/13 across F1–F2 including oracles).
- F2 `async-execution-dispatch-decision`: ENDORSED. My independent
  consumer census yields the same 8 files (9 with the owner); every
  site calls by name, none restates the refusal. The querysets
  `SyncMisuseError` raises share the type, not the contract.
- F3 `ambient-fallback-executor-read`: ENDORSED. The F2/F3 split is
  the correct call: shared fact, distinct contracts (refusing
  dispatch vs statable fact); dropping the refusal would not move
  F3's two `async_executor=` consumers. `in_async_context` has no
  package call site outside this module's three reads.
- R1 (CONVERGE with verified `optimizer-execution-frame`): ENDORSED
  on fresh evidence. All four
  `None if lease is None else lease.held()` lines verified at WT
  bytes (`execution_mode.py:112`, `optimizer/_context.py:220`,
  `resource_policy.py:610`, `operation_state.py:352`); the family
  artifact states the verdict W1 converges with ("Same mechanism,
  different rules", this module named as a parallel lease user).
  Trigger well-formed (a read-semantics change moving all four
  without moving `held`).
- R2–R7: each ENDORSED on independent probes. R2: binder census is
  exactly one (`_OPERATION_MODES.set` only inside `bind`).
  R3: template exclusion ("genuinely different wordings") and
  per-seam prose verified verbatim; all four read-guard wordings
  distinct. R4: 6-file detector census complete (the two further
  grep hits are docstring mentions, one documenting this very
  split); construction-time shape vs runtime dispatch confirmed at
  both field factories. R5: independent facts (separate
  `ContextVar`s); cited test exists and pins the nested-sync shape.
  R6: translation stays at receipt; both constructions consume the
  one function. R7: "reserved for sync boundaries" verified
  verbatim; handler coverage and glossary pin confirmed.
- Zero-defect call (incl. cleared subscribe-ASYNC candidate):
  ENDORSED. Verified independently in installed strawberry-graphql
  0.324.0: `subscribe` delegates to `stream`, which calls
  `get_extensions()` with the `sync=False` default; only
  `execute_sync` passes `sync=True`. No defect.
- Matrix: all six axes discharged against the real surface; axis 6
  re-derived (every further `isawaitable`/`is_async_only_iterable`
  hit branches on value shape or sidecar kind, never the
  executor; `views.py::view_is_async` is class-level transport
  color, not a loop sample). The only WT-vs-HEAD +/- line touching
  any traced token in 11 connected files is a docstring prose
  rewording (concurrent-external); all traced lines byte-identical.
- Artifact hygiene: no process provenance, `path::Symbol` citations,
  10-header link scaffold intact, `ruff format --check` + `ruff
  check` pass on the touched path, no test runs (per AGENTS.md),
  no `## Pending execution` (justified: static-reviewed
  single-ownership + fresh censuses; gate owns suite-green).

O1 (Worker-2, observed-not-homed): the
`[docs-readme-list-field]` link definition points at
`../../README.md` (root) under `<!-- Root -->`, but the body cites
the dispatch prose "in `docs/README.md`" — the def should be
`../README.md` under `<!-- docs/ -->` (the dispatch prose is the
entry-point paragraph there; root `README.md:54` is paging, not
dispatch). Referent recoverable from body text; scratch artifact;
no finding, transcription row, or trigger affected — recorded so a
future reader repairs it in one step.
