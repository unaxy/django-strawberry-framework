# DRY review: `optimizer/_context.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

Target `django_strawberry_framework/optimizer/_context.py` (410 lines, read in
full) owns the optimizer's per-execution state and its request-context
hand-off: the five `DST_OPTIMIZER_*` stash-key constants, the nine-slot
`_ExecutionFrame` behind one lease, the open/close pair, one accessor group
per slot, the frame-mediated stash read/write pair with its publish gate, the
start-of-execution reset over the key set, and the re-export path for the two
shape-agnostic helpers. No queryset, seal, alias, sync-boundary, or transport
vocabulary anywhere in the file (full read; imports are `contextlib`,
`ContextVar`, `typing`, `utils/context.py`, `utils/operation_lease.py` only).

Sites found (every role re-derived from this side, never inherited):

- *Definitions (all in the target):* the five key constants;
  `DST_OPTIMIZER_KEYS`; `optimizer/_context.py::_ExecutionFrame` (nine slots);
  `optimizer/_context.py::_FrameScope`; the `_execution_frames` carrier;
  `optimizer/_context.py::_active_frame` (sole read choke);
  `optimizer/_context.py::begin_execution_frame` /
  `optimizer/_context.py::end_execution_frame`; fourteen public functions in
  nine accessor groups (three `active_*`, three `*_memo`, the scoped-relation
  publish/read pair, `operation_publishes_to_context`, the
  `optimizer_value` / `stash_for_optimizer` pair, `clear_optimizer_context`);
  the `get_context_value` / `stash_on_context` re-export bindings.
- *Consumers (package):* `optimizer/extension.py`
  (sole production opener via `on_execute`, sole `clear_optimizer_context`
  caller, sole `begin/end` caller; `execution_plan_memo`,
  `cache_key_parts_memo`, `publish_scoped_relations`, `optimizer_value`,
  `stash_for_optimizer`, `active_optimizer`, all five keys, and the
  `stash_on_context` re-export chain); `types/resolvers.py` (three keys,
  `active_strictness`, `optimizer_value`, `relation_is_optimizer_scoped` —
  reads only, never publishes); `optimizer/nested_fetch.py`
  (`active_nested_strategy` via `active_strategy`); `optimizer/selections.py`
  (`converted_selections_memo`). Transitive only: `optimizer/walker.py`
  reaches the strategy through `nested_planner.py` → `nested_fetch.py`;
  `connection.py` reaches strictness through `types/resolvers.py::_check_n1`;
  `optimizer/plans.py` touches no frame symbol at all (verified by search).
- *Oracles (independent — they spell the contract without reading the
  owner):* `tests/optimizer/test_extension.py::test_on_execute_sets_and_resets_context_var`
  (frame open/close), `::test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends`
  (lease revocation + collectability over all seven read channels),
  `::test_an_operation_in_a_context_that_outlived_a_request_publishes_as_its_own`
  (second operation publishes as its own), `::test_clear_optimizer_context_removes_all_keys_from_object_and_dict`
  (spells all five keys on object and dict shapes) plus the slots-mapping,
  frozen-mapping, and QueryDict clear pins; `tests/types/test_resolvers.py`
  frame/strictness/scoped-relation rows (open frames directly);
  `tests/optimizer/test_walker.py` strategy-through-frame rows;
  `tests/optimizer/test_selections.py::test_ast_to_converted_selections_memoized_per_execution`;
  `tests/optimizer/test_nested_fetch.py` strategy rows; live
  `examples/fakeshop/test_query/test_extension_isolation_api.py` (reads the
  published key set over HTTP via `get_context_value`). Raw `dst_optimizer_*`
  literals appear in tests/live tests only as consumer-emulating reads and in
  `scripts/review_inspect.py::DEFAULT_MARKERS` as an analysis keyword —
  oracles and tooling, never definitions (production literals live only at
  the five constant assignments, probe-verified).
- *Projections:* the target's module/frame/function docstrings; consumer
  docstrings citing the frame (`extension.py::on_execute`,
  `nested_fetch.py::active_strategy`, `selections.py` memo comment,
  `types/resolvers.py::_optimizer_scoped_relation`); in-flight specs
  (`spec-002`, `spec-033`, `spec-047`, `spec-053`, `spec-058` prose);
  the `DST_OPTIMIZER_*` seam mention in `docs/GLOSSARY.md`; the kanban
  tracked-path row for this file.
- *Upstream:* `strawberry_django/optimizer.py` carries two raw `ContextVar`s
  (`optimizer`, `enabled`) and no lease, frame, or stash vocabulary —
  reference only, different package, nothing to consolidate.
- *Adjacent sibling:* `extensions/operation_state.py` (per-extension binding
  + runner ownership + engine-assignment compat) and `resource_policy.py`
  (parallel `DST_RESOURCE_*` seam, own lease, `restored_context_keys`) were
  read for candidacy; both differ in contract (see R1 and the matrix).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The only sibling stash vocabulary is
   `resource_policy.py` (`DST_RESOURCE_*`, own lease, restore-based nesting
   via `restored_context_keys`). Different payload (request budget vs
   optimizer scratch), different lifetime (runner-armed vs frame-opened),
   different nesting policy (snapshot-restore vs per-operation mapping with
   an outermost-publishes flag) — same lease mechanism, different rule, and
   the mechanism itself is single-owned at
   `utils/operation_lease.py::OperationLease`, composed by name on both
   sides. No second definition of any frame rule. The operation-state
   carrier/scope machinery is likewise composed by name (`OperationLease`,
   `operation_is_nested` as the nesting input to `begin_execution_frame`).
2. **Sync/async twins.** Zero `async def`, zero `await` in the target
   (probe-verified). One colorless body per accessor; the extension's sync
   and async resolver paths share the single frame `on_execute` opens, and
   `end_execution_frame` absorbs cross-context token resets (`ValueError`
   suppress) for task/generator teardown. No twin machinery lives here.
3. **Derived rather than repeated knowledge.** `DST_OPTIMIZER_KEYS` re-lists
   the five constants by name, not by string; `__all__` mirrors the 22
   public bindings in-file (probe-verified exact). Memo keyings
   (`id(operation)`, field-node ids) are each written and read at one site
   pair, with lifetimes stated at the owner. Nothing re-derives a key set,
   name, or default from another medium.
4. **Inverse / round-trip pairs.** Four pairs, each with one owner:
   `begin_execution_frame` / `end_execution_frame` (open/close);
   `stash_for_optimizer` / `optimizer_value` (write/read);
   `publish_scoped_relations` / `relation_is_optimizer_scoped` (write/read);
   `DST_OPTIMIZER_KEYS` / `clear_optimizer_context` (publish set/reset set).
   The union accumulation policy (`_stash_union`) deliberately lives with its
   consumer in `extension.py` — frame owns the stores, extension owns the
   publish policy. One direction each, no split halves.
5. **Contracts restated in another medium.** Media inventoried above
   (System trace): definitions move once at the owner; consumers compose by
   name; oracles spell literals/identities without reading the owner;
   specs/glossary/live tests describe. Counted at the owner in every
   challenge below.
6. **Enforcement by omission.** Full 9-slot accessor coverage, probe-verified
   (every slot read by at least one accessor; `clear()` empties exactly the
   four owned container stores while borrowed `stashes` and per-frame scalars
   die with the frame — the documented borrow). Outside-a-frame answers are
   all fail-closed and documented (`None` memos, `False` scoped/publishes,
   context-object fallback for the stash pair, `None`/frozen skip for the
   clear). No member lacks its guard. One coverage note, not a defect: no
   unit oracle opens a frame with `nested=True` directly — the nested branch
   is covered line-wise through full nested operations (union-publish rows);
   nothing about the branch is unpinned, and no contract row is broken.

### Enumeration

Instrument: `ast.parse` over the target, counting `ast.Module.body` —
**32 members**. Every member lands below; every challenge ends in the family
row F1 (sub-rules Ra–Rf) or a rejection R1–R4. Imports are composition, the
docstring is projection; neither is a rule.

| # | Member | Home |
|---|---|---|
| 0 | module docstring (hand-off shape + re-export rationale + frame lifetime) | projection, F1 |
| 1–6 | `__future__`, `contextlib`, `ContextVar`, `typing`, `utils.context` (3 names), `OperationLease` imports | composition; the 2 re-exported names → F1-Rf |
| 7 | `__all__` (22 names, exact mirror, probe-verified) | F1-Ra/Rf |
| 8–12 | five `DST_OPTIMIZER_*` constants (sole string literals, probe-verified) | F1-Ra |
| 13 | `_ExecutionFrame` (9 slots; `clear` owns 4, probe-verified) | F1-Rc |
| 14 | `_FrameScope` (lease + token) | F1-Rc |
| 15 | `_execution_frames` carrier (one `ContextVar`, probe-verified) | F1-Rc |
| 16 | `_active_frame` (sole `.get()` choke, probe-verified) | F1-Rc |
| 17–18 | `begin_execution_frame` / `end_execution_frame` (sole construct/set/reset, probe-verified) | F1-Rc |
| 19–21 | `active_optimizer`, `active_nested_strategy`, `active_strictness` | F1-Rd |
| 22–24 | `execution_plan_memo`, `cache_key_parts_memo`, `converted_selections_memo` | F1-Rd |
| 25–26 | `publish_scoped_relations` / `relation_is_optimizer_scoped` | F1-Rd |
| 27 | `operation_publishes_to_context` | F1-Re |
| 28–29 | `optimizer_value` / `stash_for_optimizer` | F1-Re |
| 30 | `DST_OPTIMIZER_KEYS` (by-name composition of Ra) | F1-Rb |
| 31 | `clear_optimizer_context` (delegates per-key delete to `clear_context_key`) | F1-Rb |

Indexed families swept with no vocabulary in the target (full 410-line read
is the closed population): `sealed-execution-queryset`,
`child-queryset-alias-inheritance`, `one-sync-boundary` (R2–R4, checked, do
not inherit); `operation-bound-extension-mechanism` (R1, checked, do not
inherit). `logger-single-sourcing`, `type-registry-*`, mutation/filter/form
families: zero tokens.

### Challenges

Each change posited against the rule's own variation axes; the count is
authoritative definitions only. Consumers, oracles, projections listed,
never counted. Probe + focused-test executions below are the proofs.

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| C1 | Ra key spelling | rename `DST_OPTIMIZER_PLANNED` (name and string) | **1** (the constant; extension + resolvers + oracles follow by name) | independent here |
| C2 | Ra/Rb key set | add a sixth stash key | **1** (constant + `KEYS` entry, same file/owner; publisher + readers + clear follow) | independent here |
| C3 | Rc frame shape | add a tenth frame member | **1** (`__slots__` + init + `clear` decision + accessor + `__all__`, all here) | independent here |
| C4 | Rc/Re nesting policy | nested operations also publish to the context object | **1** (`begin` flag computation + the two publish gates; `on_execute`'s clear call composes `operation_publishes_to_context` by name) | independent here |
| C5 | Rc teardown order | change close-then-reset ordering or the cross-context suppress | **1** (`end_execution_frame`; runner scopes in `operation_state.py` untouched — different owner, different lifetime) | independent here; split from R1 proved |
| C6 | Re read fallback | frame miss falls through to the context object instead of frame-only | **1** (`optimizer_value`) | independent here |
| C7 | Rd memo lifetime | key `key_parts` by document text instead of `id(operation)` | **1** (the memo store here; `_build_cache_key` composes it) | independent here |
| C8 | Rd scoped publish | replace in-place union with last-wins assignment | **1** (`django_strawberry_framework/optimizer/_context.py::publish_scoped_relations`) | independent here |
| C9 | Rb reset delegation | inline per-key deletion in `django_strawberry_framework/optimizer/_context.py::clear_optimizer_context` instead of delegating to `django_strawberry_framework/utils/context.py::clear_context_key` | **1** (the loop body; the shape dispatch stays single-owned at the callee) | independent here |
| C10 | Rf re-export binding | drop the re-export so optimizer consumers import `django_strawberry_framework/utils/context.py::get_context_value` direct | **1** (the two binding lines plus the two `__all__` entries, same owner) | independent here |

Ten challenges, every count 1: each posited change moves exactly one
authoritative definition; consumers, oracles, and projections follow by
name and are never counted. Two executions back the table. Probe
`docs/dry/temp-tests/dry-file-optimizer___context/probe.py` (read-only,
parse-plus-text-search, never imports the package): 21/21 PASS,
`FAILURES: none` on re-run in this pass (see `## Implementation
(Worker 1)`). One focused shared-tree run of exactly three oracles with
`--no-cov -n0`, 3 passed (command and node ids under `## Findings` F1
and `## Implementation (Worker 1)`); it discharges the ordering and
lifetime behavior C4/C5 posit changes to.

## Findings

### F1 `optimizer-execution-frame` (confirmed single-owner; zero-edit)

- **Contract + variation.** One managed execution's optimizer scratch plus
  its request-context hand-off, opened and closed around `on_execute`, read
  through one lease-checked choke. Six sub-rules, each varying only on its
  own axis. Ra key vocabulary: the five
  `django_strawberry_framework/optimizer/_context.py::DST_OPTIMIZER_*`
  constants (sole `dst_optimizer_*` literals in package production code,
  probe-verified); varies by key rename/add/remove. Rb reset set:
  `django_strawberry_framework/optimizer/_context.py::DST_OPTIMIZER_KEYS`
  (by-name composition of Ra, no package consumer outside the target) plus
  `django_strawberry_framework/optimizer/_context.py::clear_optimizer_context`
  (per-key delete delegated to
  `django_strawberry_framework/utils/context.py::clear_context_key`); varies
  with Ra. Rc frame plus lifecycle:
  `django_strawberry_framework/optimizer/_context.py::_ExecutionFrame`
  (nine slots),
  `django_strawberry_framework/optimizer/_context.py::_FrameScope`,
  `django_strawberry_framework/optimizer/_context.py::_execution_frames`
  (one carrier `ContextVar`),
  `django_strawberry_framework/optimizer/_context.py::_active_frame` (sole
  `.get()` choke),
  `django_strawberry_framework/optimizer/_context.py::begin_execution_frame`
  /
  `django_strawberry_framework/optimizer/_context.py::end_execution_frame`
  (sole construct/set/reset); varies by member, nesting policy, teardown
  order. Rd nine-slot accessors (three `active_*`, three `*_memo`, the
  scoped-relation publish/read pair); varies by slot, memo keying, publish
  accumulation. Re stash pair plus publish gate:
  `django_strawberry_framework/optimizer/_context.py::optimizer_value`
  (frame-only read),
  `django_strawberry_framework/optimizer/_context.py::stash_for_optimizer`
  (frame mapping always, context object only when publishing),
  `django_strawberry_framework/optimizer/_context.py::operation_publishes_to_context`
  (the gate); varies by fallback and destination. Rf helper re-export:
  `django_strawberry_framework/utils/context.py::get_context_value` and
  `django_strawberry_framework/utils/context.py::stash_on_context` bound and
  re-exported (in `__all__`) because the optimizer subpackage and its tests
  reach for them at
  [django_strawberry_framework/optimizer/_context.py][ctx]; varies by which
  helpers the subpackage addresses there.
- **Sites + roles.** Definitions: all in
  `django_strawberry_framework/optimizer/_context.py` (five constants,
  `DST_OPTIMIZER_KEYS`, frame, scope, carrier, choke, open/close pair,
  fourteen public functions in nine accessor groups, two re-export
  bindings). Consumers (compose by name, never counted):
  [django_strawberry_framework/optimizer/extension.py][ext] (sole
  production opener/closer/clearer; owns only the `_stash_union` publish
  policy, which correctly stays with it),
  [django_strawberry_framework/types/resolvers.py][resolvers] (reads only),
  [django_strawberry_framework/optimizer/nested_fetch.py][nested-fetch]
  (strategy via `active_strategy`),
  [django_strawberry_framework/optimizer/selections.py][selections]
  (converted memo); transitives
  [django_strawberry_framework/optimizer/walker.py][walker] via
  [django_strawberry_framework/optimizer/nested_planner.py][nested-planner],
  [django_strawberry_framework/connection.py][connection] via
  `django_strawberry_framework/types/resolvers.py::_check_n1`;
  [django_strawberry_framework/optimizer/plans.py][plans] touches no frame
  symbol (verified negative). Oracles (independent, spell the contract
  without reading the owner): [`tests/optimizer/test_extension.py`][test-ext] frame,
  lease-revocation, nested-publish, and clear rows;
  `tests/types/test_resolvers.py` frame/strictness/scoped rows;
  `tests/optimizer/test_walker.py` strategy rows;
  `tests/optimizer/test_selections.py` memo row;
  `tests/optimizer/test_nested_fetch.py` strategy rows; live
  `examples/fakeshop/test_query/test_extension_isolation_api.py` over HTTP.
  Projections: module/frame/function docstrings, consumer docstrings,
  in-flight specs, the seam mention in [docs/GLOSSARY.md][glossary].
- **Challenges.** C1 rename one key: 1. C2 sixth key: 1. C3 tenth frame
  member: 1. C4 nested-publish policy: 1. C5 teardown order: 1. C6 read
  fall-through: 1
  (`django_strawberry_framework/optimizer/_context.py::optimizer_value`).
  C7 `key_parts` rekey: 1. C8 union-to-last-wins: 1
  (`django_strawberry_framework/optimizer/_context.py::publish_scoped_relations`).
  C9 clear delegation inline: 1. C10 drop re-export: 1. Full table under
  `### Challenges`; every count is authoritative definitions only.
- **Owner + lifetime.** Owner:
  `django_strawberry_framework/optimizer/_context.py` throughout (principle
  7): the narrowest cohesive owner every legitimate consumer can import
  without reversing a dependency — the walker, the selection adapter, and
  the nested-fetch strategy sit below
  `django_strawberry_framework/optimizer/extension.py` in the dependency
  order and cannot import it, while
  `django_strawberry_framework/utils/context.py` owns only the
  shape-agnostic dispatch and must not gain optimizer vocabulary; folding
  into the runner or the resource seam would couple independent lifetimes
  and nesting policies. Principle-4 lifetime fields for the stored
  derivation: owner
  `django_strawberry_framework/optimizer/_context.py::_ExecutionFrame`;
  validity key = the lease held-state (frame answers only between
  `begin_execution_frame` and `end_execution_frame`; a copied context whose
  lease closed answers as no-optimizer-running); publish point =
  `begin_execution_frame` at `on_execute` entry, outermost-publishes flag
  computed from the runner nesting input plus the live-frame check; who may
  mutate = the frame accessors (scoped publish, stash writes, memo stores)
  and the end-of-execution `clear()`; invalidated =
  `end_execution_frame` closes the lease first (observable from every
  copied context), then empties exactly the four owned containers
  (`scoped_relations`, `plans`, `key_parts`, `converted`) while borrowed
  `stashes` and per-frame scalars die with the frame; outside a frame every
  reader fails closed (`None` memos, `False` scoped/publishes,
  context-object fallback for the stash pair only).
- **Migration.** None: already single-sited. Zero production edits; nothing
  becomes a call, declaration, or deletion.
- **Distinct behavior.** What stays separate, and where recorded: the
  `_stash_union` accumulation policy stays with its consumer in
  `django_strawberry_framework/optimizer/extension.py` (frame owns the
  stores, extension owns the publish policy — recorded at the frame
  docstring and the `### Matrix` axis-4 row); the lease mechanism stays
  single-owned at
  [django_strawberry_framework/utils/operation_lease.py][lease]`::OperationLease`
  and is composed by name on both the frame and the resource seam; the
  nesting fact stays with the runner at
  [django_strawberry_framework/extensions/operation_state.py][op-state]`::operation_is_nested`
  and is composed by name as the `nested` input to
  `django_strawberry_framework/optimizer/_context.py::begin_execution_frame`;
  the re-exported bodies stay owned by
  [django_strawberry_framework/utils/context.py][u-context] (the binding
  here is composition, counted, not a second definition); the parallel
  `DST_RESOURCE_*` seam stays owned by
  [django_strawberry_framework/extensions/resource_policy.py][res-policy]
  (request budget, runner-armed, snapshot-restore — a different rule, see
  R1 and the `### Matrix` axis-1 row).
- **Behavioral proof.** `execution-verified` (1): read-only probe
  `docs/dry/temp-tests/dry-file-optimizer___context/probe.py`, run as
  `python3 docs/dry/temp-tests/dry-file-optimizer___context/probe.py`
  from the repo root — 21/21 PASS, `FAILURES: none` on the pass-2 re-run.
  It rejects a second definition structurally: a duplicate key literal
  anywhere under `django_strawberry_framework/` fails
  `literals-single-sourced`; a split frame fails `construct-once`,
  `choke-get-once`, `set-reset-once-each`; an unreadable slot fails its
  `slot-read-*`; a fifth owned container fails `clear-owns-4-spares-rest`.
  `execution-verified` (2): one focused shared-tree run,
  `uv run pytest tests/optimizer/test_extension.py::test_on_execute_sets_and_resets_context_var "tests/optimizer/test_extension.py::test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends" "tests/optimizer/test_extension.py::test_an_operation_in_a_context_that_outlived_a_request_publishes_as_its_own" --no-cov -n0`
  — 3 passed in 2.20s. The first rejects stale open/close ordering (C5);
  the second rejects a copied context reaching a closed frame over all
  seven read channels (C5 lease revocation); the third rejects an inner
  operation erasing or inheriting the outer publish (C4 nesting policy).
  `static-reviewed`: the per-name consumer census (probe section 7,
  orientation only) and the full 410-line read confirm every consumer
  composes the owner by name; no ordering, transactional, or async surface
  exists to execute beyond the three oracles above. Nothing is
  `execution-deferred`.
- **Structural gate + negative control.** No new gate proposed: the owner
  is already single and the existing independent oracles already fail on
  bypass — e.g.
  `tests/optimizer/test_extension.py::test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends`
  fails if any reader reaches the frame past the lease (that is exactly
  what it pins), and
  `tests/optimizer/test_extension.py::test_clear_optimizer_context_removes_all_keys_from_object_and_dict`
  fails if the reset set drifts from the five keys. Negative control:
  a behavior-preserving hand copy of the owner body (same answers, new
  choke) passes every behavior oracle — as DRY.md notes it must — while
  the probe's `choke-get-once` / `construct-once` counts catch the copy;
  the mutation demonstration itself is not run here (a source-mutating
  proof needs the disposable workspace, unauthorized in this pass), so the
  control stands as `static-reviewed`, not executed. No bespoke
  existence test per helper is added (no justified bypass population
  beyond what the oracles cover — not a `gate-only` finding needing one).
- **Coupling.** None. Zero-edit item; no defect blocks any consolidation;
  pass-1 `## Defects` is empty (see below).
- **Freshness.** Worktree `git hash-object` values at resubmission (any
  change reopens this finding). Target:
  `django_strawberry_framework/optimizer/_context.py` `3d8dcfdf` (clean
  vs HEAD). Consumers/transitives:
  `django_strawberry_framework/optimizer/extension.py` `49667a93`,
  `django_strawberry_framework/types/resolvers.py` `f3341e6a`,
  `django_strawberry_framework/optimizer/nested_fetch.py` `4d8d37a7`,
  `django_strawberry_framework/optimizer/selections.py` `a48f6172`,
  `django_strawberry_framework/optimizer/walker.py` `9b111ed9`,
  `django_strawberry_framework/optimizer/nested_planner.py` `0ad8ff5d`,
  `django_strawberry_framework/optimizer/plans.py` `cce98531` (excluded:
  zero frame symbols, verified negative). Mechanism/upstream:
  `django_strawberry_framework/utils/context.py` `cd0adcc5`,
  `django_strawberry_framework/utils/operation_lease.py` `10c164b7`,
  `django_strawberry_framework/extensions/operation_state.py` `b2674a22`.
  Concurrent dirt, left untouched (worktree value first, HEAD second):
  `django_strawberry_framework/extensions/resource_policy.py`
  `583bf460` / `52084078` (dirty at pass 2; Worker-2-era value
  `647133d2` predates the external hunk),
  `django_strawberry_framework/connection.py` `3c4d5dcb` / `93e998f2`
  (dirty, external hunk, left alone). Oracles:
  `tests/optimizer/test_extension.py` `4e60f0b7`,
  `tests/types/test_resolvers.py` `88f7fb07`,
  `tests/optimizer/test_walker.py` `5bbd7a56`,
  `tests/optimizer/test_selections.py` `04bbb23d`,
  `tests/optimizer/test_nested_fetch.py` `7fbd957b`,
  `examples/fakeshop/test_query/test_extension_isolation_api.py`
  `6901fd03`. Contract sources: `docs/GLOSSARY.md` `bcc99607`,
  `docs/SPECS/spec-002-optimizer-0_0_2.md` `93ed4200`,
  `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` `5c6b9a8b`,
  `docs/SPECS/spec-047-resource_policy-0_0_14.md` `08a0394a`,
  `docs/SPECS/spec-053-boundary_dry_squeeze-0_0_15.md` `52f9c54e`,
  `docs/SPECS/spec-058-graph_substrate-0_1_1.md` `d8e4e0c7`. Excluded by
  body: `django_strawberry_framework/optimizer/plans.py` (above);
  `strawberry_django/optimizer.py` (different package: two raw
  `ContextVar`s, no lease/frame/stash vocabulary — reference only, no
  blob owed); `scripts/review_inspect.py` `88ef35bd` (tooling keyword
  list, never a definition). Searched population: every `.py` tracked by
  `git ls-files` (probe section 6 census).

### Rejected candidates

- **R1 `operation-bound-extension-mechanism`.** Concrete difference: the
  runner at
  `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
  owns per-extension binding plus runner ownership plus
  engine-assignment compat plus resume; the frame owns per-execution
  scratch plus outermost-publishes. Same lease mechanism, different rule;
  the mechanism is already single-owned at
  `django_strawberry_framework/utils/operation_lease.py::OperationLease`
  and composed by name on both sides. Reconsideration trigger: the runner
  binding and the frame lifetime merging into one object (e.g. operation
  state moving into the frame, or the frame owned by the runner) — then
  the two rules move together and this rejection reopens. Durable home:
  the owner
  `django_strawberry_framework/extensions/operation_state.py::_OperationBoundExtension`
  (one plain docstring clause owed there; production untouched in this
  pass, so the clause is named here for the holding family item
  `dry-rule-operation-bound-extension-mechanism.md`, not landed).
- **R2 `sealed-execution-queryset`.** Concrete difference: sealed-queryset
  execution contract vs optimizer stash vocabulary — zero seal/alias/
  queryset tokens anywhere in the 410-line target (full-read closed
  population), so there is nothing to consolidate. Trigger: the frame
  ever keying stored state off seal decisions. Durable home: the owner
  `django_strawberry_framework/utils/querysets.py::_seal_or_defect`
  (holding family item `dry-rule-sealed-execution-queryset.md`).
- **R3 `child-queryset-alias-inheritance`.** Concrete difference: child
  queryset alias inheritance vs optimizer stash vocabulary — zero tokens
  in the target. Trigger: the frame ever deriving or storing aliases.
  Durable home: the owner
  `django_strawberry_framework/utils/querysets.py::base_queryset`
  (holding family item
  `dry-rule-child-queryset-alias-inheritance.md`).
- **R4 `one-sync-boundary`.** Concrete difference: single-sync-boundary
  ORM execution vs colorless frame accessors — zero `async def`/`await`
  and zero sync-boundary vocabulary in the target (probe-verified).
  Trigger: the frame ever awaiting, running ORM work, or owning a
  boundary. Durable home: the owner
  `django_strawberry_framework/utils/querysets.py::run_in_one_sync_boundary`
  (holding family item `dry-rule-one-sync-boundary.md`).

## Defects

Pass-1 defects: none. The trace found no docstring contradicting its
body, no missing guard on any family member (axis 6 discharged with full
9-slot coverage and fail-closed outside-frame answers), and no layering
claim the imports contradict. (Worker-2 entries D-W2-1–D-W2-4 live in
`## Defects (Worker 2)` below and are answered by this resubmission, not
by production edits.)

## Pending execution

Nothing deferred. Every proof this artifact relies on has run: the probe
(`python3 docs/dry/temp-tests/dry-file-optimizer___context/probe.py`,
21/21 PASS, `FAILURES: none`) and the focused oracle run (`uv run
pytest` with `--no-cov -n0` over the three node ids named in F1,
3 passed) — commands and results also recorded under
`## Implementation (Worker 1)`. No `execution-deferred` proof exists, so
there is no deferred command to list. Out-of-scope cells: sharded and
Postgres runs are unverified and not authorized in this pass; they are
`inapplicable by construction` for this finding (the target's closed
population carries no queryset, seal, alias, sync-boundary, database
routing, or dialect vocabulary — full 410-line read plus probe), Worker 2
to judge.

## Judgment

The optimizer execution-frame rule (Ra–Rf) is already single-owned at
`django_strawberry_framework/optimizer/_context.py`: ten challenges each
force exactly one authoritative definition, every consumer composes the
owner by name, the four neighboring families are rejected with contract
differences plus triggers, and both executions are green. Zero-edit
result is legitimate (matrix discharged against the real surface,
enumeration 32/32 assigned, no second definition found). The new family
`optimizer-execution-frame` is owed one Responsibility-index row plus one
Families line in the plan (Worker 0). No production edit, no gate, no
coupling, no defect.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff
`git diff 32df596687f5868418bfb221d0aa187dfc582895 -- django_strawberry_framework/optimizer/_context.py`
is empty (0 bytes; target blob `3d8dcfdf` equals HEAD; no test hunks
landed for this scope). No `.py` file was created, edited, or formatted by this
item, so `ruff format` / `ruff check` have no surface (intentionally not
run repo-wide: the tree carries concurrent dirt listed under Freshness,
and a repo-wide formatter pass could touch it). Scratch paths (untracked,
this run only): probe
`docs/dry/temp-tests/dry-file-optimizer___context/probe.py` (read-only;
reused, not rewritten) and this artifact
`docs/dry/dry-file-optimizer___context.md` itself. Focused executions
recorded here as run in this pass: (1) `python3
docs/dry/temp-tests/dry-file-optimizer___context/probe.py` from the repo
root — 21/21 PASS, `FAILURES: none`; (2) `uv run pytest
tests/optimizer/test_extension.py::test_on_execute_sets_and_resets_context_var
"tests/optimizer/test_extension.py::test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends"
"tests/optimizer/test_extension.py::test_an_operation_in_a_context_that_outlived_a_request_publishes_as_its_own"
--no-cov -n0` — 3 passed in 2.20s (Django settings
`config.test_settings`, default SQLite mode; sharded/Postgres cells not
authorized, see `## Pending execution`). This is the item's single
authorized shared-tree focused run; no other pytest invocation was made.

## Independent verification (Worker 2)

Own trace, recorded before reconciling with `## Findings` below (no
`## Findings` section exists in this artifact — see D-W2-1; reconciliation
is against the visible `## System trace` / `### Matrix` / `### Enumeration` /
`### Challenges` only). Instrument: full 410-line read of the target plus
`ast.parse` census plus text search over `git ls-files *.py` for every public
name; probe `docs/dry/temp-tests/dry-file-optimizer___context/probe.py`
re-run by Worker 2 (all PASS, `FAILURES: none`).

### Own context rules (re-derived)

- Ra key vocabulary: five `DST_OPTIMIZER_*` constants, sole
  `dst_optimizer_*` string literals in package production code
  (probe-verified; only other hits are test/live-test consumer-emulating
  reads and `scripts/review_inspect.py::DEFAULT_MARKERS`). Owner I would
  choose: `django_strawberry_framework/optimizer/_context.py`.
- Rb reset set: `DST_OPTIMIZER_KEYS` (by-name composition of Ra, no package
  consumer outside the target) + `clear_optimizer_context` (per-key delete
  delegated to `django_strawberry_framework/utils/context.py::clear_context_key`).
  Same owner as Ra.
- Rc execution frame + lifecycle: `_ExecutionFrame` (9 slots), `_FrameScope`
  (lease + token), one `_execution_frames` carrier `ContextVar`, sole
  `.get()` choke `_active_frame`, sole construct/set/reset in
  `begin_execution_frame` / `end_execution_frame` (probe-verified once each),
  `clear()` empties exactly the 4 owned containers
  (`scoped_relations`, `plans`, `key_parts`, `converted`; borrowed `stashes`
  + per-frame scalars die with the frame). Nesting input composed by name
  from `django_strawberry_framework/extensions/operation_state.py::operation_is_nested`;
  lease mechanism composed by name from
  `django_strawberry_framework/utils/operation_lease.py::OperationLease`.
  Same owner.
- Rd 9-slot accessors: three `active_*`, three `*_memo`, the scoped-relation
  publish/read pair — every slot read by >=1 accessor (probe-verified),
  outside-a-frame answers fail closed (`None` memos, `False` scoped).
  Same owner.
- Re stash pair + publish gate: `optimizer_value` (frame-only read, no
  fall-through; context-object fallback only outside a frame),
  `stash_for_optimizer` (frame mapping always; context object only when
  `publishes_to_context`), `operation_publishes_to_context` gate. Same owner.
- Rf helper re-export: `get_context_value` / `stash_on_context` imported from
  `django_strawberry_framework/utils/context.py` and re-exported (in
  `__all__`) because the optimizer subpackage and its tests reach for them
  at this path. Owner of the bodies stays `utils/context.py`; the binding
  here is composition, correctly counted, not a second definition.

Change counts (authoritative definitions only; consumers/oracles/projections
follow, never counted): C1 rename one key = 1; C2 sixth key = 1 (constant +
`KEYS` entry, same owner); C3 tenth frame member = 1; C4 nested-publish
policy = 1; C5 teardown order = 1; C6 read fall-through = 1 (`optimizer_value`);
C7 `key_parts` rekey = 1; C8 union→last-wins = 1. All agree with W1's C1–C7
and the visible C8 prefix. Owners I would choose: `_context.py` throughout;
no competing owner found (extension owns only the `_stash_union` publish
policy, which correctly stays with its consumer — frame owns stores,
extension owns policy).

Consumers verified: `optimizer/extension.py` sole production
begin/end/clear caller (`_begin_execution_frame` at line ~1052,
`_end_execution_frame` in `finally`, `_clear_optimizer_context` gated on
`_operation_publishes_to_context()`); `types/resolvers.py` reads only (3
keys + `active_strictness` + `optimizer_value` +
`relation_is_optimizer_scoped`); `optimizer/nested_fetch.py`
(`active_nested_strategy` via `active_strategy`, defaulting to windowed);
`optimizer/selections.py` (`converted_selections_memo`). Transitive:
`optimizer/walker.py` → `optimizer/nested_planner.py` → `nested_fetch.py`
→ frame; `connection.py` → `types/resolvers.py::_check_n1` → frame;
`optimizer/plans.py` touches no frame symbol (zero `_context` imports,
zero `DST_`/`memo`/`frame` bindings — confirmed by search). Agree with W1
throughout, including the `plans.py` negative.

### Enumeration (member-by-member vs own count)

Own `ast.Module.body` count: **32** — agrees with W1. Mapping agrees row
for row: 0 module docstring (projection); 1–6 six import statements
(`__future__`, `contextlib`, `ContextVar`, `typing`, `utils.context`
3 names, `OperationLease`); 7 `__all__` (22 names, exact mirror,
probe-verified); 8–12 five key constants; 13 `_ExecutionFrame`; 14
`_FrameScope`; 15 `_execution_frames` carrier; 16 `_active_frame`; 17–18
begin/end; 19–21 three `active_*`; 22–24 three `*_memo`; 25–26 scoped pair;
27 `operation_publishes_to_context`; 28–29 stash pair; 30
`DST_OPTIMIZER_KEYS`; 31 `clear_optimizer_context`. Every member lands in
W1's F1 (Ra–Rf) rows; nothing unassigned. Imports are composition, the
docstring projection — agree.

### Counts, roles, oracles

Definition/consumer/oracle/projection roles agree with W1, with one
nuance (observation, not a blocker):
`tests/optimizer/test_extension.py::test_clear_optimizer_context_removes_all_keys_from_object_and_dict`
imports the five key constants FROM the owner, so it does not pin key-set
membership independently (a sixth key would pass untested); the
frozen-mapping / `QueryDict` / slots-mapping pins are behavioral
(no-raise), and raw `dst_optimizer_*` literals in live/unit tests are
consumer-emulating reads. No oracle was rewritten in this item (zero-edit;
working tree carries no test hunks for this scope) — the AGENTS/DRY
constraint holds.

### Equivalence (principle 8)

Zero production edits (item-scoped diff empty, confirmed below): no
observable behavior to preserve, no migration, equivalence holds
trivially. No ordering, transactional, or async surface changed.

### Zero-edit, coverage, assignment, new family

Item-scoped diff `git diff
32df596687f5868418bfb221d0aa187dfc582895 --
django_strawberry_framework/optimizer/_context.py` is empty (0 bytes);
worktree blob `3d8dcfdf…` == `HEAD` blob. Zero-edit legitimate for a file
item: matrix discharged against the real surface (verified below),
challenges recorded with counts, no second definition found.

New family `optimizer-execution-frame` (owner `_context.py`; covers
`_context` + `extension` + `types/resolvers` + `nested_fetch` +
`selections`, transitive `walker` / `nested_planner` / `connection`):
**endorsed, justified** — one responsibility (per-execution optimizer
scratch + request hand-off, one lifetime opened/closed at `on_execute`),
one owner every legitimate consumer can import without reversing a
dependency. Splitting Ra–Rf into six families would over-split (same
owner/files/holding item); folding into `operation-bound-extension-mechanism`
or the `DST_RESOURCE_*` seam would couple independent lifetimes and nesting
policies (runner-armed snapshot-restore vs frame-opened
outermost-publishes); folding into `utils/context.py` would reverse the
dependency. Worker 0 rows owed (see return message): one Responsibility
index row + one Families line.

### Matrix (vs real surface)

1. Cross-flavor: agree — `resource_policy.py` differs in payload, lifetime,
   nesting policy; mechanism single-owned at `OperationLease`. 2. Twins:
   agree — zero `async def`/`await`, one colorless body per accessor. 3.
   Derived: agree — `KEYS` by name, `__all__` exact, memo keyings single-sited.
   4. Round-trip pairs: agree — four pairs, one direction each; `_stash_union`
   correctly stays with the consumer. 5. Media: agree with the nuance above.
   6. Omission: agree — 9-slot coverage probe-verified, outside-frame answers
   fail closed; the `nested=True`-never-opened-directly note is coverage
   commentary, not a defect (nested branch covered line-wise through full
   nested operations).

### Rejections, fingerprints, gates, Pending, coupling

- R1–R4 (R1 `operation-bound-extension-mechanism`; R2–R4
  `sealed-execution-queryset`, `child-queryset-alias-inheritance`,
  `one-sync-boundary`): directionally agree — R1 differs in contract
  (per-extension binding + runner ownership + resume vs per-execution
  scratch + outermost-publishes); R2–R4 have zero vocabulary in the target
  (full-read closed population). BUT no contract-difference + trigger text
  exists in this artifact (no `## Findings`), so the rejections are
  **unverifiable as records** — D-W2-1.
- Freshness fingerprints: **absent** (zero `blob`/`hash` mentions) — every
  verdict in this artifact is unverifiable against later movement — D-W2-2.
  Worker 2 re-hashes (see return message): target `3d8dcfdf…` (clean);
  `extension.py` `49667a93…`, `types/resolvers.py` `f3341e6a…`,
  `nested_fetch.py` `4d8d37a7…`, `selections.py` `a48f6172…`,
  `utils/context.py` `cd0adcc5…`, `utils/operation_lease.py` `10c164b7…`,
  `operation_state.py` `b2674a22…`, `resource_policy.py` `647133d2…`,
  `walker.py` `9b111ed9…` (ledgered D1 fix, committed follow-through),
  `nested_planner.py` `0ad8ff5d…`, `plans.py` `cce98531…`,
  `connection.py` worktree `3c4d5dcb…` (concurrent external hunk, left alone).
- Structural gates: none proposed (zero-edit, owner already single) — no
  negative controls to run; any future gate-only finding owes a justified
  population. N/A, agree.
- `## Pending execution`: absent (no such section). W1 reportedly ran one
  focused shared-tree run of 3 tests plus the read-only probe. The probe is
  authorized (read-only experiment under `docs/dry/temp-tests/`, re-run by
  Worker 2). The 3-test run is **unauthorizable as stated**: no exact
  commands, no `--no-cov` evidence, no test names recorded anywhere in the
  artifact (no `## Implementation (Worker 1)` section), so Worker 2 cannot
  judge shared-tree authorization or coverage of C4/C5 ordering behavior —
  D-W2-3. Pending-absent does **not** hold as a verified claim.
- Coupling: none introduced by a zero-edit item — agree.

### AGENTS.md prose check

No production edits (no format/lint/test-tier/commit surface). Citations in
the visible artifact use short paths (`optimizer/_context.py::…`,
`utils/operation_lease.py::…`) where AGENTS.md requires full
`path::QualifiedName` from the repo root
(`django_strawberry_framework/optimizer/_context.py::_ExecutionFrame`) —
minor citation shorthand, D-W2-4. No `path:NN` line citations seen; no
process provenance; no cross-file markdown links (scaffold N/A).

## Defects (Worker 2)

- D-W2-1 (Worker 2) — W1 artifact truncated mid-C8, missing `## Findings`,
  `## Defects`, `## Pending execution`, `## Judgment`, `##
  Implementation (Worker 1)`. Owner: this item (Worker 1 resubmission).
  No verification can complete against an incomplete record; revision must
  restore the full finding record (F1 Ra–Rf + R1–R4 with contract
  differences, triggers, challenges, owner + lifetime, behavioral proof
  status, gates, coupling, freshness).
- D-W2-2 (Worker 2) — zero freshness fingerprints in the artifact. Owner:
  this item. Every input inspected (target, extension, resolvers,
  nested_fetch, selections, utils/context, operation_lease, operation_state,
  resource_policy, walker, nested_planner, plans, connection, oracles,
  specs, glossary) owes a `git hash-object` blob id.
- D-W2-3 (Worker 2) — focused-run commands unrecorded (3 shared-tree tests
  unnamed, no `--no-cov` evidence, no `## Implementation`). Owner: this
  item. Worker 2 cannot judge authorization or Pending-absent; resubmission
  must list exact commands + what each discharged, or move the proofs to
  `## Pending execution` as `execution-deferred`.
- D-W2-4 (Worker 2) — citation shorthand vs AGENTS.md `path::Symbol` form.
  Owner: this item. Expand to repo-rooted paths on resubmission.

## Judgment (Worker 2)

`Status: revision-needed`. The independent trace endorses W1's technical
direction (32-count enumeration, single ownership at `_context.py`,
consumer/transitive map including the `plans.py` negative, matrix
discharge, and the justified new family `optimizer-execution-frame`), but
the artifact is truncated and carries no findings, fingerprints, or
runnable record — there is nothing complete to verify. Concrete asks:
restore the full finding record past C8, add blob-id fingerprints for every
input, record the exact probe + focused-test commands (or defer pending
proofs explicitly), fix citation paths. No production edit owed; all
concurrent dirt left untouched; nothing committed.

## Independent verification (Worker 2) — pass 2

Resumed on W1 pass 2 (artifact 747 lines). Completion checks, all green:
(1) truncation marker: 0 occurrences file-wide; C8 row completed and C9–C10
added; (2) F1 carries all 10 DRY.md fields (contract, sites+roles,
challenges, owner + principle-4 lifetime, migration, distinct behavior,
behavioral proof, structural gate + negative control, coupling, freshness)
and R1–R4 each carry concrete difference + reconsideration trigger + durable
home; (3) `## Defects` (none, W2 entries cross-referenced),
`## Pending execution` (nothing deferred; sharded/Postgres ruled
inapplicable by construction with a stated no-db-vocabulary reason —
Worker 2 concurs), `## Judgment`, `## Implementation (Worker 1)` all
present and mutually consistent; (4) focused run recorded with exact
command, three node ids (all three `def` names verified present in
`tests/optimizer/test_extension.py`), `--no-cov -n0`, 3 passed in 2.20s —
a single focused shared-tree run, within the worker-1 allowance, and the
node→claim mapping (open/close ordering, lease revocation over seven read
channels, nested publish) discharges C4/C5 as claimed; probe 21/21
re-run matches the 21 structural checks; negative control honestly held as
`static-reviewed` with the workspace-authorization reason (no new gate owed
on a zero-edit file item — accepted); (5) link block 15/15 bidirectional,
zero unresolved, zero unused, every target exists; (6) pass-1 W2 sections
byte-intact (all distinctive strings present; pass-1 verdict stands as
history); (7) item-scoped diff still empty (0 bytes), target
`3d8dcfdf` clean vs HEAD; (8) D-W2-1–D-W2-4 discharged: findings restored,
21 fingerprints all re-hashed clean (dirty `resource_policy.py`
`583bf460`/`52084078` and `connection.py` `3c4d5dcb`/`93e998f2` pairs
honestly recorded, external hunks untouched), exact commands recorded,
new text fully repo-rooted. `Status: verified`. No production edit, no
gate, no coupling, no new defect. Concurrent dirt preserved; nothing
committed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[ctx]: ../../django_strawberry_framework/optimizer/_context.py
[ext]: ../../django_strawberry_framework/optimizer/extension.py
[lease]: ../../django_strawberry_framework/utils/operation_lease.py
[nested-fetch]: ../../django_strawberry_framework/optimizer/nested_fetch.py
[nested-planner]: ../../django_strawberry_framework/optimizer/nested_planner.py
[op-state]: ../../django_strawberry_framework/extensions/operation_state.py
[plans]: ../../django_strawberry_framework/optimizer/plans.py
[res-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[resolvers]: ../../django_strawberry_framework/types/resolvers.py
[selections]: ../../django_strawberry_framework/optimizer/selections.py
[u-context]: ../../django_strawberry_framework/utils/context.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-ext]: ../../tests/optimizer/test_extension.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->