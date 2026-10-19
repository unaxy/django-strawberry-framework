# DRY review: `optimizer-execution-frame`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `optimizer-execution-frame`. Provisional owner
`django_strawberry_framework/optimizer/_context.py`; seed member files
`_context.py`, `extension.py`, `types/resolvers.py`, `nested_fetch.py`,
`selections.py`, transitive `walker.py`, `nested_planner.py`,
`connection.py`; re-derived below, not trusted. Prior records used only
as rejected-candidate triggers: the `_context.py` file item (frame +
keys + reset + accessors + stash pair + re-export) and the
`extension.py` file item (sole production begin/end/clear caller +
seven frame readers).

## System trace

Rule: the per-execution optimizer frame — one managed execution's
scratch plus its request-context hand-off, opened and closed around
`on_execute`. Nine slots behind one lease (`optimizer`,
`strategy`, `strictness`, `scoped_relations`, `plans`, `key_parts`,
`converted`, borrowed `stashes`, `publishes_to_context` flag); one
carrier `ContextVar`; one read choke; one open/close pair; one
start-of-execution reset over the key set; per-slot accessors; the
frame-mediated stash read/write pair with its publish gate.

Whole-package mechanism sweep (every `.py` under
`django_strawberry_framework/`, vocabulary census re-derived in this
pass; counts are code sites, prose excluded):

- `begin_execution_frame` definition: 1
  (`django_strawberry_framework/optimizer/_context.py::begin_execution_frame`).
  Production call sites: exactly 1
  (`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.on_execute`).
- `end_execution_frame` definition: 1; production call sites: exactly 1
  (same `on_execute`, in `finally`).
- `clear_optimizer_context` definition: 1; production call sites:
  exactly 1 (same `on_execute`, gated on
  `operation_publishes_to_context`).
- `_execution_frames` carrier: 1 `ContextVar`; `_active_frame` sole
  `.get()` choke: every one of the 11 frame readers in `_context.py`
  goes through it, so no accessor can infer a running optimizer from a
  value a copied context still holds.
- Five `DST_OPTIMIZER_*` string literals: all five live in
  `_context.py` and nowhere else in production (zero raw
  `dst_optimizer_*` literals elsewhere, swept). `DST_OPTIMIZER_KEYS`
  re-lists them by name; no package consumer outside the target.
- Direct shape-dispatch calls (`get_context_value` /
  `stash_on_context` / `clear_context_key`) in production: none with
  optimizer keys. Every optimizer stash read/write goes through
  `optimizer_value` / `stash_for_optimizer` or a frame accessor. The
  `_stash_on_context` alias `extension.py` imports is test-compat only:
  zero production calls. The only direct dispatch users are the
  parallel `DST_RESOURCE_*` seam and the dispatch itself.

Roles:

- **Definition (1 owner):**
  `django_strawberry_framework/optimizer/_context.py` — five key
  constants, `DST_OPTIMIZER_KEYS`, `_ExecutionFrame` (nine slots,
  `clear()` empties exactly the four owned containers while borrowed
  `stashes` and per-frame scalars die with the frame),
  `_FrameScope`, `_execution_frames`, `_active_frame`,
  `begin_execution_frame` / `end_execution_frame`, eleven reader/publish
  functions in seven groups (three `active_*`, three `*_memo`, the
  scoped-relation publish/read pair, `operation_publishes_to_context`,
  the `optimizer_value` / `stash_for_optimizer` pair,
  `clear_optimizer_context`), plus the `get_context_value` /
  `stash_on_context` re-export bindings (composition, not a second
  definition of the bodies owned by
  `django_strawberry_framework/utils/context.py`).
- **Lifecycle caller / composing consumer (1):**
  `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.on_execute`
  (sole opener/closer/clearer); `execution_plan_memo` in
  `_get_or_build_plan`; `cache_key_parts_memo` in `_build_cache_key`;
  `publish_scoped_relations` + `optimizer_value` + `stash_for_optimizer`
  in `_publish_plan_to_context` / `_stash_union`; `active_optimizer`
  in `apply_connection_optimization`. The `_stash_union`
  accumulation policy lives here with its consumer: the frame owns the
  stores, the extension owns the publish policy.
- **Direct frame readers:** `types/resolvers.py` (three key constants,
  `active_strictness`, `optimizer_value`,
  `relation_is_optimizer_scoped` — reads only, never publishes);
  `optimizer/nested_fetch.py::active_strategy`
  (`active_nested_strategy`, defaulting to windowed outside a frame);
  `optimizer/selections.py::ast_to_converted_selections`
  (`converted_selections_memo`).
- **Transitive only:** `optimizer/walker.py` reaches the strategy via
  `nested_planner.py` into `nested_fetch.py::active_strategy`
  (verified: zero frame tokens in `walker.py` itself; the ledgered D1
  fix there — `_PREFETCH_CHILD_POLICY` in `_build_child_queryset` —
  touches seal policy, not the frame, and is recorded here only for the
  population touch the plan item names); `optimizer/nested_planner.py`
  via `active_strategy`; `connection.py` via
  `apply_connection_optimization` (`active_optimizer`) and via
  `types/resolvers.py::_check_n1` (strictness/scoped reads).
  `optimizer/plans.py` touches no frame symbol (verified negative).
- **Second-lifecycle search (the owner routinely off-seed):** no second
  begin/end/clear pair exists anywhere in the package — counts above
  are 1/1/1. The runner at
  `django_strawberry_framework/extensions/operation_state.py::operation_is_nested`
  owns the nesting fact (composed by name as the `nested` input) and the
  operation state whose `stashes` mapping the frame borrows; the lease
  mechanism is single-owned at
  `django_strawberry_framework/utils/operation_lease.py::OperationLease`
  and composed by name on the frame, the runner scopes, the resource
  seam, and `utils/execution_mode.py`. Same mechanism, different rules.
- **Oracles (independent):**
  `tests/optimizer/test_extension.py::test_on_execute_sets_and_resets_context_var`,
  `::test_an_execution_frame_a_task_copied_answers_nothing_once_the_execution_ends`
  (seven read channels), `::test_an_operation_in_a_context_that_outlived_a_request_publishes_as_its_own`,
  `::test_optimizer_context_all_exports` (`__all__` composition pin),
  the clear rows, `tests/types/test_resolvers.py` frame/strictness/scoped
  rows, `tests/optimizer/test_selections.py::test_ast_to_converted_selections_memoized_per_execution`,
  strategy rows, and the NEW gate below. Live
  `examples/fakeshop/test_query/test_extension_isolation_api.py` reads
  the published key set over HTTP.
- **Projections:** the `_context.py` module/frame/function docstrings
  (incl. the eight-slot lifetime account and the borrow clause),
  consumer docstrings citing the frame, spec-030/033/036 prose, the
  seam mention in `docs/GLOSSARY.md`.
- **Upstream:** `strawberry_django/optimizer.py` carries two raw
  `ContextVar`s and no lease/frame/stash vocabulary — reference only.

Attribution: `connection.py` worktree dirt is the ledger-external
cursor-guard hunk (worktree `3c4d5dcb…` vs HEAD `93e998f2…`, both
re-hashed this pass, matching the plan's record); the item-scoped diff
of that path carries zero frame tokens, so the external hunk cannot
collide with this family, and the path is not edited. Every other
member file is worktree-clean (verified). The walker D1 ledger row was
read before editing and is frame-free.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The only sibling stash vocabulary
   is `resource_policy.py` (`DST_RESOURCE_*`, own lease,
   snapshot-restore nesting, runner-armed budget) — different payload,
   lifetime, and nesting policy; mechanism composed by name. The
   operation-state carrier/scope machinery likewise composes
   `OperationLease` and `operation_is_nested` by name. No second
   definition of any frame rule.
2. **Sync/async twins.** Zero `async def` / zero `await` in the target;
   one colorless body per accessor. The extension's sync/async resolver
   twin (`_optimize` vs the `_async_optimize` closure) shares the
   single frame `on_execute` opens; `connection.py` keeps two colored
   bodies sharing pure decisions while its frame reads stay sync
   accessors. Contrast recorded here and at the owner: frame sharing is
   safe exactly because no accessor awaits, pins an alias, runs ORM
   work, or holds a transaction — the opposite of the write-pipeline
   reason for one sync body. No twin machinery lives in the frame, and
   none is owed.
3. **Derived rather than repeated knowledge.** `DST_OPTIMIZER_KEYS`
   re-lists the five constants by name; `__all__` mirrors the 22 public
   bindings (pinned by `test_optimizer_context_all_exports`); memo
   keyings (`id(operation)`, field-node ids) each written/read at one
   site pair with lifetimes stated at the owner. Nothing re-derives a
   key set, name, or default from another medium.
4. **Inverse / round-trip pairs.** Four pairs, one owner each:
   begin/end, stash write/read, scoped publish/read, key set/reset.
   `_stash_union` stays with its consumer in `extension.py` by design.
5. **Contracts restated in another medium.** Definitions move once at
   the owner; consumers compose by name; oracles spell
   literals/identities without reading the owner; specs/glossary/live
   tests describe. Counts taken at the definition only, every finding.
6. **Enforcement by omission.** Full nine-slot accessor coverage; every
   outside-a-frame answer fails closed (`None` memos, `False`
   scoped/publishes, context-object fallback for the stash pair only,
   `None`/frozen skip for the clear). The lifecycle singularity had no
   pin — a second opener/closer/clearer would pass every behavior
   oracle — which is the justified population the new gate below
   closes. No member lacks a guard its contract requires.

### Enumeration

Instrument: exact-token census over every package `.py` (whole-tree
`rglob`, population printed per pattern; zero-hit patterns confirmed
by the sweep, not by sampling) plus a full read of `_context.py`
(410 lines) and `on_execute`. Assignment: 1/1/1 lifecycle
definitions with 1/1/1 production call sites (all `on_execute`); 1
carrier; 1 choke with 11 in-file readers; 5 key literals + 1 by-name
key set + 1 reset; 11 public reader/publish functions in 7 groups; 2
re-export bindings; 1 consumer owning only `_stash_union`; 3 direct
reader modules; 3 transitive modules; 1 verified-negative module
(`plans.py`); 4 composed-not-duplicated neighbors (runner,
lease, shape dispatch, resource seam). Nothing unassigned.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Add a sixth stash key (new `DST_OPTIMIZER_*` constant published by a new code path) | **1** (constant + `KEYS` entry, same owner file; publisher, readers, and clear follow by name) |
| C2 | Change reset timing (clear at execution end instead of start, or close-then-reset reorder in `end_execution_frame`) | **1** (`clear_optimizer_context` call site / `end_execution_frame` body; runner scopes untouched — different owner, different lifetime) |
| C3 | Add a second begin/end pair (a new execution path opening its own frame instead of composing `on_execute`) | **0 existing moved + 1 new decision point** — no second pair exists to move; the new gate below fails on exactly this while every behavior oracle passes, which is what proves today's count is 1 |
| C4 | Change stash lifetime (empty borrowed `stashes` in `clear()`, or frame-miss fall-through to the context object in `optimizer_value`) | **1** (`_ExecutionFrame.clear` / `optimizer_value`; the borrow clause and the frame-only read are the owner's documented contract) |

## Findings

### F1 — optimizer execution frame (single-owned; gate-only lifecycle pin)

- **Contract + variation.** One managed execution's optimizer scratch
  plus its request-context hand-off, opened and closed around
  `on_execute`, read through one lease-checked choke. Varies by key
  vocabulary (C1), reset timing and teardown order (C2), member set and
  nesting policy (C3), stash lifetime and read fallback (C4).
- **Sites + roles.** As inventoried above: 1 definition owner
  (`django_strawberry_framework/optimizer/_context.py`); 1 lifecycle
  caller (`extension.py::on_execute`); 3 direct reader modules; 3
  transitive modules; oracles and projections as listed.
- **Challenges.** C1, C2, C4 -> 1 definition; C3 -> 0 existing + 1 new
  decision point (proof of current count 1, not duplication).
- **Owner + lifetime (principle 7).**
  `django_strawberry_framework/optimizer/_context.py` throughout: the
  narrowest cohesive owner every legitimate consumer can import
  without reversing a dependency — the walker, the selection adapter,
  and the nested-fetch strategy sit below `extension.py` in the
  dependency order and cannot import it, while `utils/context.py`
  owns only the shape-agnostic dispatch and must not gain optimizer
  vocabulary, and folding into the runner or the resource seam would
  couple independent lifetimes and nesting policies. Dependency
  direction wins over narrowness. Principle 4: owner
  `django_strawberry_framework/optimizer/_context.py::_ExecutionFrame`;
  validity key = the lease held-state (answers only between
  `begin_execution_frame` and `end_execution_frame`; a copied context
  whose lease closed answers as no-optimizer-running); publish point
  = `begin_execution_frame` at `on_execute` entry with the
  outermost-publishes flag from the runner nesting input plus the
  live-frame check; who may mutate = the frame accessors (scoped
  publish, stash writes, memo stores) and end-of-execution `clear()`;
  invalidated = `end_execution_frame` closes the lease first
  (observable from every copied context), then empties exactly the
  four owned containers while borrowed `stashes` and per-frame scalars
  die with the frame.
- **Migration.** Production: none (already single; zero production
  hunks). Tests: one structural gate added (below). No oracle
  rewritten (the standing oracles are untouched; the new test scans
  source, it does not import the owner it checks).
- **Distinct behavior (stays separate, where recorded).**
  `_stash_union` stays in `extension.py` (frame owns stores, extension
  owns publish policy); `active_strategy`'s windowed default stays in
  `nested_fetch.py` (strategy-domain default, not a frame rule); the
  re-exported bodies stay owned by `utils/context.py`; the
  `DST_RESOURCE_*` seam, the runner scopes, and `OperationLease`
  stay with their owners (same mechanism, different rules); the
  sync/async twin split stays in `resolve`/`connection.py` while the
  frame stays colorless (contrast above).
- **Behavioral proof (`execution-verified`).** Disposable workspace
  copy per [DRY.md][dry] "Tests" (docs/ excluded):
  `WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/optimizer-execution-frame`.
  From inside `WS`, `import django_strawberry_framework` resolves to
  the copy's own `__init__.py` and settings `DATABASES.default.NAME`
  resolves to the copy's own `examples/fakeshop/db.sqlite3` (never the
  shared tree). In `WS`: the new gate plus the `__all__` pin plus the
  three lifecycle oracles (open/close ordering, lease revocation over
  seven read channels, nested publish) — 5 passed. The three oracles
  reject stale open/close ordering (C2), a copied context reaching a
  closed frame (C2/C4 lease revocation), and an inner operation erasing
  or inheriting the outer publish (C3 nesting policy). Zero production
  edits, so no migration equivalence is owed beyond these; principle-8
  axes (exceptions, query effects, await points, cleanup order) are
  untouched by construction. The one authorized shared-tree run (the
  new gate, `--no-cov -n0`) passed: 1 passed. Rejects the wrong
  results "a second pair would fail a behavior oracle", "the gate
  pins behavior rather than singularity".
- **Structural gate.** NEW
  `tests/optimizer/test_extension.py::test_execution_frame_lifecycle_calls_are_single_sited`:
  AST scan over the whole package population asserting exactly one
  production `Call` each to `begin_execution_frame` /
  `end_execution_frame` / `clear_optimizer_context` (leading-underscore
  aliases normalized, so the composition shape is pinned too),
  per-region identity (every hit in `optimizer/extension.py`),
  rejected parse failures (`unparseable` must be empty), and a live
  population (`scanned > 0`; fail-closed on an empty census).
  Justified population: the begin/end/clear pairing mechanism; the
  plausible bypass is a second lifecycle pair on a new execution path,
  which every behavior oracle passes by construction. Negative
  controls (3, one per call) proved via
  [`scripts/prove_failability.py`][prove-script] in `WS` with
  `--scratch-root` outside both trees (manifest at
  `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/frame-manifest.json`;
  full report in `## Implementation (Worker 1)`): each mutant adds
  one dead helper (never invoked, behavior-preserving) carrying the
  second call; each fails exactly the new gate (1 row, 0 errors,
  green baseline) with the restore proved by `filecmp` plus SHA-256.
  The complete 3-entry proof ran against the as-written gate body;
  after the layout-mandated set collapse (formatting only, same
  assertions) the 5-test set re-ran green in `WS` and entry 1
  re-ran green-baseline/red-mutant with restore proved, so the final
  body carries both.
  The runner's `WEAKLY PINNED` label on each 1-row entry is a builder
  floor for boundaries owed many rows; here one lifecycle is owed one
  row, each mutant fails exactly its owning row, which is the exact
  pin, not a weak one. Recorded as judgment, not as a second run.
- **Coupling.** None. Production untouched; the gate reads source text
  and reaches no database, alias, or dialect decision (sharded/PG
  cells inapplicable by construction). No dependency on any other
  family or on the ledgered walker D1 work.
- **Freshness.** Worktree blob ids (`git hash-object`; any change
  reopens the finding): `_context.py`
  `3d8dcfdfba5ba644b4759f80e95d57ba0fa1a98b`, `extension.py`
  `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`,
  `types/resolvers.py`
  `f3341e6a9f52659925762bce097033bac67e3b51`,
  `nested_fetch.py`
  `4d8d37a7f52cf94d2916f17db3a8a21393e28d57`,
  `selections.py`
  `a48f6172c6f04331740d1b110d742f17701ff846`, `walker.py`
  `9b111ed938951a073a9226ccbcfacabc3af981e8` (ledgered D1 fix,
  frame-free), `nested_planner.py`
  `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04`, `plans.py`
  `cce985319c8833f3660653327d3003f1f03655a5` (excluded: zero frame
  symbols), `utils/context.py`
  `cd0adcc509a3a40e5b46ba761c6cbfec2c44359c`,
  `utils/operation_lease.py`
  `10c164b731b381d2b62adb5e2c5ce6b694a53fd0`,
  `extensions/operation_state.py`
  `b2674a22d2dfd58ff97c51a02e16068bb22032e9`,
  `utils/execution_mode.py`
  `9805cdafd2445b2e3a1a98eafd0c653cc89bb4f9` (excluded: parallel
  lease user, different rule), `resource_policy.py` worktree
  `647133d23785d325856b2d1d495d18c5741dd23c` (excluded: parallel
  seam; concurrent dirt, untouched), `connection.py` worktree
  `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a` vs HEAD
  `93e998f2c7ea1d7f18607a6e37e394466ac75ad4` (external hunk,
  frame-free, untouched),   `tests/optimizer/test_extension.py`
  post-edit `883720eed4aed462d3804d0106db71749abd74ac`
  (pre-edit `4e60f0b7ab8777dc0fd9c95bdf3950884ca937b5`).
  Searched population: every package `.py` (token census) plus the
  full reads named in the trace.

No sub-rule decomposed: the lifecycle, keys, reset, accessors, stash
pair, and re-export share one owner, one lifetime, and one holding
item; splitting them would over-split. Worker 0 owes no new index
row beyond the family itself.

### Rejected candidates

- **R1 fold the frame into `extension.py`.** Concrete difference:
  dependency direction — the walker, the selection adapter, and the
  nested-fetch strategy sit below the extension and cannot import it;
  the frame exists so those readers compose the lifetime without
  reversing it. Trigger: a dependency inversion that lets every
  current reader import the extension (then the two rules move
  together and this reopens). Durable home: the `_context.py` module
  docstring (already states the dependency-order reason; no prose
  edit owed).
- **R2 fold the key vocabulary into `utils/context.py`.** Concrete
  difference: shape-agnostic dispatch vs optimizer vocabulary — the
  dispatcher must not name optimizer keys, and the reset set must not
  live where resource keys live. Trigger: a third context-key family
  needing shared key-set machinery (then the machinery, not the
  vocabularies, is the family). Durable home: the `utils/context.py`
  module docstring (already states the two-subsystem split).
- **R3 merge the frame with the runner operation state or the
  resource seam.** Concrete difference: per-execution optimizer
  scratch with outermost-publishes vs per-extension binding with
  resume (runner) vs runner-armed budget with snapshot-restore
  (resource); three lifetimes, three nesting policies, one shared
  lease mechanism already single-owned at `OperationLease`. Trigger:
  the frame lifetime and either neighbor merging into one object.
  Durable home: the runner docstring at
  `extensions/operation_state.py::_OperationBoundExtension` and the
  frame borrow clause (both already state the split).
- **R4 split the accessors into sync/async twins.** Concrete
  difference: no accessor awaits, pins an alias, runs ORM work, or
  holds a transaction — there is no execution contract differing by
  color, so a twin split would be machinery, not DRY. The genuine
  twins (`resolve`, `connection.py` bodies) share this one frame.
  Trigger: a frame reader needing to await (then that reader, not the
  frame, owns the boundary). Durable home: this artifact's matrix
  axis-2 row (the colorless contract, stated once).

## Defects

None. While tracing: no docstring contradicts its body (the borrow
clause, the four-owned-containers `clear()`, the close-then-reset
order, and the publish-gate prose all match the code); no family
member lacks a guard its contract requires (axis 6 discharged with
the previously unpinned singularity now gated); no layering claim
the imports contradict. Nothing routed; the consolidation depends on
no repair.

## Pending execution

None for this item. Every executed proof is recorded above with its
workspace command and outcome (`execution-verified`); the one
authorized shared-tree focused run (the new gate, `--no-cov -n0`)
passed (1 passed). Full-suite green and sharded/PG cells belong to
the final gate item, not this family: the production diff here is
empty and the new test reaches no database.

## Judgment

Single-owned rule, no duplication to consolidate: 4 challenges force
1 definition (C3: 0 existing + 1 new decision point, proof of count
1). The lifecycle singularity had behavior oracles but no structural
pin, so the item lands a gate-only addition: one AST singularity pin
over the begin/end/clear pairing with three executed negative
controls. Zero production edits; one test added at the mandated
tier (`tests/`, package mechanism, matching every frame oracle's
home).

## Implementation (Worker 1)

Tracked changes (item-scoped diff vs `ITEM_BASELINE`
`4eaa77f020334f128effe1c0f5e92de49661c95d`):

- `tests/optimizer/test_extension.py` (+51, no deletions):
  `test_execution_frame_lifecycle_calls_are_single_sited` (gate-only
  lifecycle-singularity pin; production untouched). Target confirmed
  clean before editing (empty `git diff HEAD`, absent from `git
  status` and from the plan's `## Owned changes` ledger).
- New untracked artifact: this file
  (`docs/dry/dry-rule-optimizer-execution-frame.md`).

After the edit: `uv run ruff check --fix
tests/optimizer/test_extension.py` then `uv run ruff format
tests/optimizer/test_extension.py` until `ruff format --check` and
`ruff check` both pass on the touched path. No `CHANGELOG.md` touch.
No commit. Concurrent dirt (10 package files incl. `connection.py`,
8 test files, bug-hunt and plan artifacts, untracked sibling
`dry-file-*.md`/`dry-rule-*.md`) never edited, reverted, or tidied;
the `connection.py` hunk attributed by content as external and
frame-free.

Workspace failability report (run in `WS` via
`uv run --directory "$WS" python scripts/prove_failability.py
<manifest> --scratch-root <outside-both-trees>`; package `__file__`
and DB `NAME` verified as the copy's own before any verdict):

```text
[1/3] second begin -> gate fails, 1 row, 0 errors, baseline 1 passed
[2/3] second end -> gate fails, 1 row, 0 errors, baseline 1 passed
[3/3] second clear -> gate fails, 1 row, 0 errors, baseline 1 passed
restores: filecmp True + sha256 match, all three
failing (each): test_execution_frame_lifecycle_calls_are_single_sited
```

Reading of the three `WEAKLY PINNED` labels: see Findings (one
lifecycle owed one row each; exact pins, judged by hand as the
runner requires).

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/optimizer-execution-frame`
(includes its own `.venv`, created by the authorized run), manifest
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/frame-manifest.json`,
scratch-root
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/frame-failability-scratch`.

Worker 0 rows: tick Family `optimizer-execution-frame` (this
artifact); no new responsibility-index row (no sub-rule decomposed);
append to `## Owned changes`:
`tests/optimizer/test_extension.py` — Family
`optimizer-execution-frame` —
`test_execution_frame_lifecycle_calls_are_single_sited` (gate-only
lifecycle-singularity pin; production untouched).

## Independent verification (Worker 2)

Own census first (whole-package token grep plus full reads of
`django_strawberry_framework/optimizer/_context.py` (410 lines) and
`django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.on_execute`;
the artifact above was opened before this trace finished, so every
count below was re-derived, not trusted):

- `begin_execution_frame` def 1, production calls exactly 1
  (`extension.py::on_execute`, line `frame = _begin_execution_frame(`).
  `end_execution_frame` def 1, production calls exactly 1 (same
  `on_execute`, `finally`). `clear_optimizer_context` def 1,
  production calls exactly 1 (same `on_execute`, gated on
  `operation_publishes_to_context`). No second pair package-wide.
  Test-only callers (`tests/types/test_resolvers.py`,
  `tests/optimizer/test_nested_fetch.py`,
  `tests/optimizer/test_selections.py`,
  `tests/optimizer/test_walker.py`,
  `tests/optimizer/test_extension.py` clear/begin rows) are oracles,
  not definitions; the gate scans package source only, so they are
  out of its population by construction.
- Five `DST_OPTIMIZER_*` literals, all in `_context.py`; zero raw
  `dst_optimizer_*` literals elsewhere. `DST_OPTIMIZER_KEYS`
  re-lists the five by name, same file: one definition for C1.
- One carrier `ContextVar` in `_context.py`
  (`_execution_frames`); `_active_frame` is the sole `.get()` choke
  and all 11 public readers go through it (verified per function:
  `active_optimizer`, `active_nested_strategy`,
  `active_strictness`, `execution_plan_memo`,
  `cache_key_parts_memo`, `converted_selections_memo`,
  `publish_scoped_relations`, `relation_is_optimizer_scoped`,
  `operation_publishes_to_context`, `optimizer_value`,
  `stash_for_optimizer` in 7 groups). `_ExecutionFrame` has exactly
  9 slots; `clear()` empties the 4 owned containers and borrows
  `stashes`. `_FrameScope` 1. Two re-export bindings
  (`get_context_value`, `stash_on_context`) owned by
  `django_strawberry_framework/utils/context.py`. `__all__` counts
  22, matching the composition pin.
- `extension.py` imports `_stash_on_context` but never calls it in
  production (zero production calls confirmed): test-compat alias
  only. Direct `get_context_value` / `stash_on_context` /
  `clear_context_key` production users are the `DST_RESOURCE_*`
  seam and the dispatch itself; no optimizer-key call bypasses the
  frame accessors.
- Direct readers: `types/resolvers.py` (reads only, never
  publishes), `nested_fetch.py::active_strategy`,
  `selections.py::ast_to_converted_selections`. Transitive:
  `walker.py` (zero frame tokens confirmed) via `nested_planner.py`
  (imports `active_strategy` from `nested_fetch.py`) via
  `nested_fetch.py`; `connection.py` via
  `extension.py::apply_connection_optimization`
  (`active_optimizer`) and `types/resolvers.py::_check_n1`.
  `plans.py` negative confirmed (only prose "Python frame" hit, no
  symbol). `consumers.py` "frame" hits are all websocket protocol
  frames, unrelated to this family. Subscriptions ride the same
  `on_execute` / resolver paths; no separate lifecycle surface.
- Owner I would choose: `optimizer/_context.py`, on the dependency
  direction W1 states and I re-judged: `extension.py` imports
  `walker.py`, `selections.py`, `nested_fetch.py`
  (`resolve_strategy`), so housing the frame in `extension.py`
  would force those readers to import upward (a cycle for
  `nested_fetch.py`); `utils/context.py` must stay shape-agnostic
  (serves the resource seam too); runner and resource seam have
  different lifetimes and nesting policies under one shared
  `OperationLease` mechanism. Dependency direction wins. Agree.

Per-claim reconciliation: definition counts, site roles, 1/1/1
lifecycle singularity, direct/transitive/negative assignments,
C1/C2/C4 count 1 and C3 count 0+1, the four
composed-not-duplicated neighbors, walker D1 frame-free, and the
GATE-ONLY outcome all agree with my census. No difference found.
Matrix: all six axes judged discharged against the real surface;
axis 2 (colorless frame vs colored twins) and axis 6 (singularity
had no pin; the gate closes exactly that population) carry the
weight and both hold. One note (not a defect): R4's durable home
is this artifact's matrix axis-2 row rather than an owner
docstring clause; the difference and trigger are concrete, the
artifact persists outside the removal list, and the closeout
Outcomes record rejections with triggers, so the chain is intact.

Gate checking-vs-reading: the new test scans source text via AST
and imports the owner only for `__file__` path resolution; it
reads no owner value. Standing oracles untouched (diff is +51/-0
in one test file). `path::Symbol` citations: the artifact uses
them; the test docstring uses bare names, matching every standing
docstring in `tests/optimizer/test_extension.py` (e.g. the clear
rows, the `__all__` pin). No prose-rule violation.

Zero production change confirmed: item-scoped diff vs
`4eaa77f020334f128effe1c0f5e92de49661c95d` is exactly
`tests/optimizer/test_extension.py +51/-0`. Gate-only is RIGHT
here: no reader duplicates lifecycle logic (readers compose
accessors; `_stash_union` policy stays with its consumer by the
recorded split), so a consolidation would be machinery hiding
risk, not a removed change obligation. Fold candidates
re-judged: R1 (fold into extension) independently rejected on the
import cycle above; R2/R3 homes opened and confirmed
(`utils/context.py` module docstring two-subsystem split;
`extensions/operation_state.py` runner split prose plus the frame
borrow clause). Freshness re-hashed: all 12 blob ids match the
record (including `tests/optimizer/test_extension.py` post-edit
`883720ee...`); no drift.

Negative control RE-RUN in a fresh workspace copy taken after
W1's edits (rsync excluding `.git`, `.venv`, `__pycache__`,
`docs/`; never branched):
copy `__file__` =
`.../dry-ws-w2/optimizer-execution-frame/django_strawberry_framework/__init__.py`
(its own tree, via `uv run --directory "$WS"`); DB `NAME` =
copy's own `examples/fakeshop/db.sqlite3`. Baseline: new gate
1 passed. Strongest mutant (C3 pair: dead never-invoked helper
appended to the copy's `extension.py` carrying one extra
`_begin_execution_frame` + one extra `_end_execution_frame`
call): gate FAILS exactly (`begin` 2 hits, `end` 2 hits,
`clear` 1 hit, failing on the begin assertion; behavior
preservation static-reviewed: unreferenced `def`, body never
runs). Restore proved (`filecmp` True, sha256
`96f41b6c...` pre/post match); re-run 1 passed. W1's recorded
3/3 therefore adjudicated as re-proved, not merely trusted.

Lint/layout on `tests/optimizer/test_extension.py` (run myself):
`uv run ruff format --check` (already formatted),
`uv run ruff check` (all checks passed),
`python3 scripts/check_trailing_commas.py --check` (clean).
ASCII, line length, tier all hold.

Test tier: `tests/optimizer/` package tier is CORRECT. A second
lifecycle pair is behavior-preserving dead code by construction,
so no live GraphQL query over `/graphql` could distinguish it;
the property is source-structural, and every frame oracle
already lives at this tier. `## Pending execution` empty is
RIGHT: the gate body does `rglob` + `ast.parse` + asserts only,
reaching no database, alias, or dialect decision (sharded/PG
inapplicable by construction, reason stated).

`connection.py` worktree dirt re-checked: 0 frame tokens in its
`git diff HEAD` hunk set (64 insertions cursor-guard work,
external, untouched). Concurrent dirt elsewhere preserved; this
item touches nothing but its artifact and the one test.

## Defects

None from Worker 2. No docstring contradicts its body, no member
lacks a guard, no layering claim the imports contradict.

## Judgment (Worker 2)

Verdict: verified. Single-owned rule, gate-only pin justified,
negative control re-proved in a fresh copy, all checks green.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->
[prove-script]: ../../scripts/prove_failability.py

<!-- .venv/ -->

<!-- External -->
