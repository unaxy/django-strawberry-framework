# DRY review: `type-teardown-lifecycle`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-teardown-lifecycle`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F7 aspects).
Member files: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py`. Prior records used only
as triggers, never verdicts: the registry file item's F7 aspects + R1/R2
(`docs/dry/dry-file-registry.md`, verified) and the six verified
registry siblings (`type-registry-model-type-map`,
`type-registry-definition-store`, `type-registry-pending-ledger`,
`type-registry-enum-cache`, `type-registry-finalize-gate`,
`subsystem-clear-lifecycle` is open, not used) — every boundary below
re-derived against the tree at `HEAD bfaee91d`, especially the
finalize-gate guard-vs-flags split and the definition-store C3/C4
lifetime. Never read any `worker-memory/`.

Attribution before edit (item fences edits, never reading): both worktree
hunks on the family paths match `## Owned changes` ledger rows by
content — the `registry.py` hunk is the Family
`relay-node-name-decode` docstring trigger clause, the
`types/finalizer.py` hunk is the Family `globalid-setting-snapshot`
trigger clause (both this cycle's own). No other hunk exists on either
family path vs `HEAD` (both diffs show only those clauses), and the
item-scoped diff vs `ITEM_BASELINE 78471afe` is byte-empty on both
paths. The `types/base.py`, `connection.py`, `relay.py`,
`types/relay.py` dirt read for content is ledgered (`relay-pk-`
`suppression-read-mirror`, `typed-globalid-decode`,
`relay-node-type-stamp`) or content-attributed external concurrent work
(`connection.py` cursor-guard feature, outside every cited cache line) —
never edited, so no stop triggered. Dirt elsewhere is concurrent work,
left alone.

## System trace

Rule: teardown is the inverse of registration — removing a type and its
records so rebuilds and tests start clean. `TypeRegistry.unregister`
drops one type; `TypeRegistry.clear` drops everything the instance owns
and replays the subsystem bus. There is no single "drop everything
except X" rule: each aspect's drop/retain/conditional semantics differ
by lifetime, and each difference is pinned below with its oracle.

Per-aspect drop-vs-retain table (every cell body-read + probe-pinned
P1/P2; counts are authoritative definitions, oracles listed not counted):

- F1 map (`_types` / `_models` / `_primaries`): `unregister` detaches
  the type and purges the primary slot unconditionally (even with
  siblings remaining — caller re-declares via a fresh cycle);
  `clear()` drops all. Oracles: `test_unregister_removes_from_types_`
  `models_primaries_definitions`, `test_unregister_keeps_siblings_`
  `intact_in_multi_type_case`, `test_unregister_of_primary_leaves_`
  `state_that_audit_rejects`, `test_clear_resets_primaries`.
- F2 definitions (`_definitions`): `unregister` pops one; `clear()`
  clears all. Oracles: the unregister-drop row above; the `clear()`
  definition arm has NO standing row — definition-store D1
  (proof-strength gap, already homed for closeout carding, blocks
  nothing; behavior discharged by executed C4 there).
- F3 pending (`_pending`): `unregister` drops the `source_type`
  subset; `clear()` drops all. Oracles:
  `test_unregister_removes_pending_relations_sourced_from_type`;
  the `clear()` pending arm is the same D1 gap (one card covers both).
- F4 enums (`_enums`): `unregister` NEVER touches (verified: zero
  `_enums` tokens in the method body) — the pinned F1/F4 boundary a
  sibling recorded and this item re-verified by body read; a type
  leaving the map must not orphan the sibling still reading the same
  column (first-wins name preserved). `clear()` drops all. Oracle:
  `test_two_djangotypes_reading_same_choice_field_share_one_enum`
  (unregister A, build B, assert `is`-shared).
- F5 gate (`_finalized`): `unregister` refuses post-finalize via
  `_check_mutable` (guard fires before the registration check, so even
  unknown types raise); it never flips or resets the flag. `clear()`
  resets to `False` (documented test-only bypass). Oracles:
  `test_unregister_raises_after_finalize`, `test_mutators_reject_`
  `calls_after_mark_finalized`, the clear-then-fresh pair.
- F7 teardowns (`_type_teardowns`): `unregister` runs the type's
  callbacks LIFO *before* the registration drops (callbacks observe a
  still-resolving registration — test-pinned), retaining a failed
  callback AND the registration for retry; `clear()` runs every type's
  callbacks in reverse attachment order, then drops. Oracles:
  `test_type_teardowns_run_in_reverse_order_once_before_`
  `registration_drops` × {clear, unregister},
  `test_failed_type_teardown_remains_registered_for_retry` × {clear,
  unregister}, `test_register_type_teardown_rejects_invalid_`
  `registration`. Sole production producer: finalizer synthesis
  (`register_type_teardown` exactly 1 production call site at
  [finalizer][finalizer] line 612; package sweep shows no other).
- F8 name-decode: pure per-call derivation, no stored state — nothing
  to drop under either mutator by construction.
- F9 snapshot (`_globalid_setting_snapshot`): `unregister` retains
  (load-bearing for retry: a stamped snapshot plus retained types
  keeps the mixed-strategy refusal armed across unregister +
  re-register; resetting it would let a settings change silently mix
  old-stamped and new-stamped types). `clear()` resets to
  `GLOBALID_SETTING_UNSET`. Oracles: the `override_settings` +
  `clear()` + rebuild rows (retain arm has no direct row; the
  reaching sequence needs a harness-only mid-test settings change,
  so no oracle gap is owed).
- F6 bus (`_subsystem_clears`): `unregister` replays NOTHING — running
  registry-wide resets for a single-type removal would wipe sibling
  state (e.g. all input namespaces). Its only co-clear is the
  per-type connection-cache eviction via `_clear_if_importable`
  (exactly 1 call site; hygiene, not correctness — leftover is
  identity-keyed). `clear()` replays every registered callback. The
  bus dict itself is never dropped by either mutator (entries live
  owner-import → process end). Oracles:
  `test_unregister_evicts_connection_type_cache_entry`,
  `test_unregister_tolerates_unimportable_connection_submodule`,
  `test_clear_runs_owner_registered_subsystem_callback`, the four
  poisoned-`sys.modules` tolerance rows.

WHO calls `unregister` (package + test sweep, 117 files): production
code NEVER calls it — the finalizer retry path relies on the six
per-loop `definition.finalized` skips, never on removal. In-repo
callers are tests only: [test-registry][test-registry] (fresh-instance
rows + the global multi-type/ambiguity/refusal rows),
[test-relay-connection][test-relay-connection] (the synthesis-teardown
rows drain the sole producer's callbacks through `unregister`
directly), and the `tests/types/test_resolvers.py` finally blocks
which pass MODEL classes (`registry.unregister(Category)` with
`Category` a model, never a `_models` key — a silent no-op shape,
contained by that module's autouse `registry.clear()` fixture; noted
as an observation, not a defect: no contract row breaks). The
`tests/optimizer/test_extension.py::_force_unregister_after_finalize`
helper deliberately bypasses the public mutator via private-map
surgery (maps + definitions only — a gap simulation for
`check_schema`, not a teardown; leaves pending/teardowns/enums/cache
behind by design of the simulation). No user-code caller exists in
the repo; the method is public API for test teardown.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** No flavor keeps a second
   type-teardown ledger (package sweep: `register_type_teardown(` /
   `_type_teardowns` occur only in [registry][registry], the one
   finalizer producer, and the oracle files). The mutation/form
   declaration ledgers are pre-bind disjoint declaration lists
   (rejected separation, owned by their factory) — a different
   subject from collected-type teardown.
2. **Sync/async twins.** Zero `AsyncFunctionDef` in either member
   (registry 30/0 per the file item, re-confirmed; finalizer 42/0
   per the gate item). Both mutators are in-memory dict/list work;
   no ORM I/O, no awaits. Trigger: a teardown method touching the
   DB or awaiting.
3. **Derived rather than repeated knowledge.** `unregister`'s
   docstring enumerates exactly what it drops; `_enums` absence in
   that enumeration plus the sharing oracle states retention —
   the enum-cache W2 judged the wording adequate, re-checked here.
   No site re-derives the drop set from `__init__`.
4. **Inverse / round-trip pairs.** register/unregister,
   teardown-register/run/drain, mark/refuse/clear-reset — all pinned
   by the oracles above. `unregister`-then-re-register leaves a
   clean, unfinalized, definition-less slot (P4).
5. **Contracts restated in another medium.** Production (owner
   pair); oracles (independent literals, plain classes +
   `object()` sentinels; the two tests reaching into
   `registry._finalized` do so as the sanctioned harness bypass the
   `unregister` docstring names); projections (docstrings verified
   against bodies; specs 018/027/031/032/036/040 as contract
   sources). No consumer restates the drop set.
6. **Enforcement by omission.** `register_type_teardown` and
   `unregister` both call `_check_mutable`; the run helpers are
   private; `clear()` bypasses by its documented test-only
   contract. No member lacks a guard its contract requires: no
   defect.

### Enumeration

Instrument: `ast.parse` def census + token sweeps over the 117-file
package population (`git ls-files django_strawberry_framework |
grep -c` = 117, re-counted). Every teardown member assigned; every
challenge ends in the family row or a recorded rejection.

- `register_type_teardown` / `_run_type_teardowns`: exactly 1 def
  each; the only production caller of the former is the finalizer
  synthesis path; `_type_teardowns`: exactly 1 storage dict
  (construction, per-type run + pop, reversed replay in `clear()`,
  test-only drain).
- `unregister`: 1 def; touches `_types`, `_models`, `_primaries`,
  `_definitions`, `_pending`, `_type_teardowns` (run), and the
  connection cache (evict-one); touches `_enums` zero times,
  `_globalid_setting_snapshot` zero times, `_finalized` zero times
  (guard read only), `_subsystem_clears` zero times.
- `clear()`: 1 def; drops all seven instance aspects plus replays
  the bus; resets `_finalized` and the snapshot.
- `_clear_if_importable`: 1 def, exactly 1 call site (the
  `unregister` eviction tail); the `clear()` side rides the
  owner-registered `connection.type_cache` callback instead (R1,
  re-checked unfired: still 1 literal, 1 direct call site).
- Rollback mirror (`register_with_definition` except-block): touches
  `_detach_type_from_model` + `_primaries` restore only — never
  definitions, pending, teardowns, or enums (R2, re-checked
  unfired: still 1 pair def + 1 production caller).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes P1–P6 map onto
C1–C4 (32/32 `execution-verified`); negative control N1 proved by
mutation.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New per-type registry aspect (a second dict keyed by `type_cls`) | **1** rule in **2** enforcement sites (the `unregister` arm + the `clear()` arm) plus its oracle rows. The two arms are granularities of one policy (drop-one vs drop-all), not two copies — the same shape DRY.md names for pipeline flavors. P3 proves no generic rule exists: an attached attribute with no arm survives BOTH mutators, so a new aspect without arms leaks and no standing oracle catches it (each aspect carries its own rows; D1 shows even an existing `clear()` arm can go unpinned). |
| C2 | `unregister`-then-re-register the same class | **1** (the lifecycle; P4: slot resolves, definition-less until re-defined, gate open). The retained enum contributes **0** moved (converter first-wins contract, sibling oracle). |
| C3 | Collapse all per-aspect arms into one teardown record (shared drop helper / aspect table) | **Rejected** (F1): the aspects do not share a policy — enums retain, snapshot retains, gate refuses, bus does not replay, teardowns run-before-drop with retry retention, primary purges unconditionally where the rollback restores. A table would restate each policy per row and remove no change obligation. |
| C4 | Change LIFO to FIFO / drop-on-failure instead of retry-retain | **1** (`_run_type_teardowns`; file-item probes + the × {clear, unregister} oracle pairs reject). |

**Experiment (executed, disposable workspace).** Copy per [dry][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/teardown-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_teardown.py
```

Proof (`CHECKS_PASSED=32/32`): full unregister drop/retain table
(P1: map/primary/definition/pending dropped, sibling kept, enum +
snapshot retained, teardown ran while registered then drained;
P1b unknown no-op; P1c post-finalize raise with maps untouched),
full clear table (P2: all seven aspects dropped/reset + bus
replayed), new-aspect leaks through both mutators (P3),
unregister-then-re-register clean (P4), model-key no-op shape (P5),
retry retention + LIFO (P6). Status: `execution-verified`. Copy
`__file__`:
`.../dry-ws/teardown-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/teardown-w1/examples/fakeshop/db.sqlite3` (copy's own
tree and database; never the shared tree; the probes open no DB at
all). No source mutation in the proof; searched population inside
the copy: 117 `.py` (matches the shared tree).
`grep -c truncated` == 0.

**Negative control N1 (executed, disposable workspace).** Removed
only the `self._definitions.pop(type_cls, None)` arm from the
copy's `registry.py`, re-ran: fails exactly at
`P1-definition-dropped` (exit 1). Restored byte-identical (md5
`cc18443b…` before and after), re-ran: 32/32. Status:
`execution-verified`. Proves the instrument fails the divergence
it guards.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "unregister
or teardown or clear_drops_all_state or clear_runs_owner or
clear_allows_fresh or clear_resets_primaries"` → 20 passed (every
oracle row this finding relies on, green post-trace with zero
edits in flight, so no run is invalidated).

## Findings

### F1 — type teardown lifecycle (REJECTED consolidation: single-owned, per-aspect lifetimes intentionally separate)

- **Contract + variation.** Teardown is the inverse of
  registration with per-aspect granularity: drop-one
  (`unregister`, pre-finalize only) vs drop-all (`clear()`,
  test-only, guard bypass). Varies on: purge vs restore (primary:
  unconditional purge vs rollback snapshot restore — R2),
  drop vs retain (enums, snapshot — stated sibling-lifetime and
  retry reasons), refuse vs drop (finalized flag — guard, not
  state), run-before-drop vs plain drop (teardowns — LIFO +
  retry retention), replay vs evict-one (bus vs connection
  cache — R1).
- **Sites + roles.** *Definitions*: `register_type_teardown`,
  `_run_type_teardowns`, the `unregister` per-type drain, the
  `clear()` reversed replay (one each). *Producer*: finalizer
  synthesis (sole). *Consumers*: the per-aspect oracles above.
- **Challenges.** C1 → 1 rule / 2 sites; C2 → 1 (+0 contrast);
  C3 → rejected; C4 → 1. Count > 1 nowhere in one rule: no
  duplication.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/registry.py::TypeRegistry` (F7
  aspects plus the per-aspect `unregister`/`clear()` arms)
  stands: narrowest cohesive owner every consumer can import
  without reversing a dependency (finalizer and base already
  import the registry at module top). Stored-teardown lifetime:
  validity key = registration → first successful drain;
  publish point = `register_type_teardown` during Phase 2.5
  synthesis (import-time-only via `_check_mutable`, registered
  type required); who may run = `unregister` (one type, before
  its drops) + `clear()` (all, reversed, before the maps drop);
  retained on failure with the registration intact for retry.
  The remaining aspects keep the lifetimes their sibling
  families record (F1–F6, F8, F9).
- **Migration.** None (zero-edit rejection: no behavior hunk, no
  test hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** Enum retention (sibling
  reuse + first-wins name); snapshot retention (mixed-strategy
  refusal across retry); guard refusal (runtime snapshot
  protection); bus non-replay (sibling-state protection);
  evict-one vs purge-all (hygiene vs reset — R1); purge vs
  snapshot-restore (removal vs rollback — R2).
- **Behavioral proof.** `execution-verified` for both drop
  tables, the no-op shapes, re-register cleanliness, retry
  retention, and LIFO order (workspace 32/32 + N1 + the
  authorized 20-passed focused run). `static-reviewed` for the
  zero-`async` census, the single-producer sweep, and
  oracle-body independence (plain classes + `object()`
  sentinels; none reads the owner).
- **Structural gate.** Deferred with reason: a
  behavior-preserving hand copy of the drain (identical arms,
  identical order/retention) passes every standing oracle by
  construction, so no behavioral gate can pin unity; only a
  source census could ("every `__init__` attribute has a drop
  arm"), and that is a bespoke existence test per helper, which
  [dry][dry] forbids for gate-only findings — the same bar as
  all six verified siblings. Unity rests on the one-way import
  edges plus the triggers below. Coverage that stays: the
  per-aspect unregister/clear rows (each fails a real leak —
  N1 demonstrates the shape), the LIFO/retry pairs, the
  eviction row. D1 names the one arm no standing row fails.
- **Coupling.** None.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `registry.py` `612bea87…`, `types/finalizer.py`
  `f4266a15…`,   `tests/test_registry.py` `e330cfb8…`,
  `tests/test_relay_connection.py` `b6bd90d9…`, `tests/optimizer/test_extension.py`
  `883720ee…`, `tests/types/test_resolvers.py`
  `88f7fb07…`, `tests/conftest.py` `3578a7bf…`,
  `types/base.py` worktree `4bd9ad16…` (`HEAD`
  `91c58747…`; delta is the ledgered relay-pk-suppression
  consolidation, outside every cited teardown line),
  `connection.py` worktree `3c4d5dcb…` (`HEAD`
  `93e998f2…`; delta is the concurrent cursor-guard feature,
  outside every cited cache line), `relay.py` worktree
  `69085e7a…` + `types/relay.py` worktree `c333c785…`
  (both ledgered docstring clauses, outside teardown lines),
  `docs/dry/dry-file-registry.md` `4350662b…`,
  `dry-rule-type-registry-enum-cache.md` `8afa1681…`,
  `dry-rule-type-registry-definition-store.md`
  `a3842ee8…`, `dry-rule-type-registry-pending-ledger.md`
  `82f6fdb9…`, `dry-rule-type-registry-finalize-gate.md`
  `6f2d1726…`, `dry-rule-type-registry-model-type-map.md`
  `26d77471…`. Searched population: whole package (117
  `.py`, both trees). Any fingerprint change reopens the
  finding.
- **Reconsideration triggers (recorded at the owners).** The
  lifecycle stays single-owned until one fires: T-aspect fires
  if a new per-type aspect lands without both arms + oracle
  rows (C1 — the leak P3 demonstrates); T-unify fires if two
  aspects converge on one drop policy with no retain/refuse/
  run-behavior difference (C3); T-producer fires if a second
  production caller of `register_type_teardown` appears.
  Durable homes: the `register_type_teardown` docstring (inverse
  discipline + identity-check ownership),
  `registry.py::TypeRegistry.unregister` (drop enumeration +
  R1 consistency rationale), this finding.

### Rejections (intentional separations, each with difference + trigger + home)

- R1 re-checked (prior deferral, not inherited):
  per-type connection eviction vs whole-cache purge. Difference:
  identity-keyed hygiene at removal time vs owner-callback purge
  at reset time; different granularity, mechanism, lifecycle
  moment. Recount: exactly 1 `_clear_if_importable` call site +
  1 connection literal (the `clear()` side rides the bus);
  trigger unfired. Home:
  `registry.py::TypeRegistry.unregister` + this finding.
  Reconsider on a third direct reach-in or a per-type evict
  helper exported from `connection.py`.
- R2 re-checked (prior deferral, not inherited): rollback
  restores the pre-call `_primaries` snapshot and touches only
  THIS call's appended state; `unregister` purges
  unconditionally (primary slot, definitions, pending). A shared
  helper needs a restore-vs-delete mode flag obscuring both
  sites; the common `_types`/`_models` removal IS shared
  (`_detach_type_from_model`). Recount: still 1 pair def + 1
  caller; trigger unfired. Home:
  `registry.py::TypeRegistry.register_with_definition` +
  this finding. Reconsider on a third partial-rollback site.
- R3 (considered shared form: one teardown record listing every
  aspect). Difference: the table above — no two non-map aspects
  share a drop policy, and the map arms themselves split by
  granularity with intentional deviations; the record would
  restate each policy per row and remove no change obligation
  (C3). Trigger: T-unify above. Home: this finding.

## Defects

None meeting the [agents][agents] bar (contract row + feasible
shape + wire/config input). Two observations kept out for cause:
(a) the `tests/types/test_resolvers.py` finally blocks call
`registry.unregister` with MODEL classes — a silent no-op shape
(P5 proves the shape); contained by that module's autouse
`registry.clear()` fixture (entry/exit), so no leak reaches any
later test — dead cleanup, not a stale-type bug. (b) The
`tests/optimizer/test_extension.py::_force_unregister_after_`
`finalize` helper drops maps + definitions only — a documented
test-only gap simulation for `check_schema`, not a teardown; its
partial surgery never runs outside those fixtures. Neither is
fixed inside this item (both live in other items' oracle files).

## Pending execution

None. All behavioral proofs `execution-verified` in the
disposable workspace (32/32 + N1, copy `__file__` + copy DB
`NAME` recorded, no source mutation, byte-identical restore);
the one authorized shared-tree focused test ran green post-trace
(20 passed) with zero edits in flight, so no run is invalidated.
No `execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres
cells `inapplicable by construction`: every executed claim is
in-memory dict work plus pure class construction on fresh
instances; the probes open no DB (recorded `NAME` is the copy's
own file, never touched). Full-suite gate business is deferred
to the final-gate item with reason: the entry command authorizes
workspace runs plus one focused `--no-cov` test, and a green
unmutated suite would discharge no failability proof for a
rejection that proposes no gate.

## Judgment

Teardown is the inverse of registration with per-aspect
lifetimes, all single-owned at `TypeRegistry`: every aspect's
records are dropped or retained by a stated rule, each rule
carries its oracle rows (save the already-homed D1 arms), and
the only production producer drains through the one LIFO
mechanism. The ad-hoc appearance is intentional — different
lifetimes (sibling reuse, retry arming, runtime protection,
sibling-state protection), not a consolidation candidate.
Consolidation rejected; zero edits.

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`78471afe506b0b600ea43a381539217a48f9ab0c`) is empty for
`django_strawberry_framework/registry.py` and
`django_strawberry_framework/types/finalizer.py` (and vs `HEAD`
`bfaee91d` likewise, except the two ledgered docstring clauses
matched to `## Owned changes` above); the only new path is this
artifact (untracked, owned by this item). No test file touched,
so no test-tier obligation arises beyond the consumed focused
run. No `CHANGELOG.md` touch. No commit per standing rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff
format --check` have no touched `.py` paths to run against
(vacuously satisfied; `.md` artifacts are excluded from
format). The artifact itself uses reference-style links with the
bottom `LINK DEFINITIONS` block and `path::Symbol` citations.

Scratch paths (removal is Worker 0's, after `verified`, by
explicit path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/teardown-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_teardown.py` holding the 32 executed checks + N1). No
manifest (no `prove_failability.py` run — no gate added, none
owed).

Worker 0 rows: tick Family `type-teardown-lifecycle` (this
artifact); no `## Responsibility index` change (provisional owner
+ both member files already covered, status stays `open` until
Worker 2); no `## Owned changes` append (zero tracked edits); no
defect homing (none found).

## Independent verification (Worker 2)

Recorded from a pre-read trace (frozen at
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/w2-teardown-trace.md`
before this artifact was opened; never read any `worker-memory/`).
Body-reads: [registry][registry] in full (614 lines),
[finalizer][finalizer] in full (2058 lines), plus consumers
`connection.py::_connection_type_cache` / `clear_connection_type_cache`,
`tests/test_registry.py` teardown rows, `tests/types/test_converters.py`
enum-reuse row, `tests/types/test_relay_interfaces.py` retry row,
`tests/optimizer/test_extension.py::_force_unregister_after_finalize`.

Sites/roles, definition counts, owner: sole definition
`django_strawberry_framework/registry.py::TypeRegistry` (`__init__`
declares `_types` / `_primaries` / `_models`, `_definitions`,
`_pending`, `_enums`, `_finalized`, `_type_teardowns`,
`_globalid_setting_snapshot`; `_run_type_teardowns` LIFO engine;
`unregister` per-type drain; `clear()` full reset + bus replay;
`_detach_type_from_model` shared invariant; `_check_mutable` guard;
`_subsystem_clears` bus; `_clear_if_importable` per-type co-clear).
Consumers: finalizer retry (six per-loop
`definition.finalized` skips, snapshot compute/read block,
pre-bind `iter_subsystem_clears(before_bind=True)` sweep),
finalizer synthesis (sole `register_type_teardown` producer),
connection cache (full-purge callback + per-type evict).
Oracles are independent literals / plain classes / `object()`
sentinels; none reads the owner (two `_finalized` reaches are the
docstring-named harness bypass). Owner I would choose:
`django_strawberry_framework/registry.py::TypeRegistry` — matches
provisional (narrowest importable owner; finalizer already imports
it; holds every slot + guard + replay).

Per-aspect re-derivation (agree on every cell): `unregister` drops
F1 map (+primary purge via `_detach_type_from_model` + conditional
`_primaries.pop`), F2 one definition (`_definitions.pop`), F3
source-subset (`is`-filtered `_pending`), runs F7 LIFO-before-drop
with retry retention (`_run_type_teardowns` before drops; failed
callback re-appended + reraise, registration retained), evicts
connection-cache one (best-effort `_clear_if_importable` pop);
retains F4 enums (zero `_enums` tokens in body) + F9 snapshot (zero
snapshot tokens); refuses on F5 (`_check_mutable` first, even for
unknown types); replays no F6 bus. `clear()` drops all seven
(`_types`, `_primaries`, `_models`, `_enums`, `_definitions`,
`_pending`, `_type_teardowns`), resets `_finalized` + snapshot to
`GLOBALID_SETTING_UNSET`, replays every bus callback. Six skips
(not four — artifact wins; my pre-read undercount missed the
synthesis + sidecar-subpass loops).

F10-new-aspect challenge (agree, REJECT stands): a new per-type
slot needs `unregister`-one + `clear()`-all (2 enforcement sites)
plus oracle rows (never counted). That is one rule with two
enforcement sites (fine), not three rules. An audit line is a
consumer (reads, never drops) unless it holds its own drop logic.
A central teardown record would restate the seven genuinely
differing policies per row (retain / refuse / run-before-drop /
no-replay / purge-vs-restore / evict-one-vs-purge-all) and remove
no change obligation while coupling independent owners
(converters, connection, finalizer, subsystems). "Policies
genuinely differ" is TRUE; not seven ad-hoc arms.

Retain asymmetry (both justified + read, agree): F4 retain =
sibling-identity, read via `get_enum` on next registration
(`test_two_djangotypes_reading_same_choice_field_share_one_enum`
`is`-shares, first-wins name). F9 retain = retry arming, read on
every finalize including retry
(`django_strawberry_framework/types/finalizer.py::finalize_django_types`
#"current_globalid_setting" stamp-or-compare + mixed-strategy
raise; `test_retry_lifecycle_rejects_setting_change_no_mixed_strategy`).
`unregister` stays legal after a partial failure (`_finalized`
still `False`) so clearing the snapshot would disarm the guard;
retaining it is load-bearing, not dead weight. No permanent row
pins the F9 retain arm, but no gap is owed (reaching it needs a
partial-failure + settings-change harness, unlike D1's plain
register/clear shape).

Production-caller sweep (agree, one completeness note): zero
`.unregister(` calls in `django_strawberry_framework/`; no
washout paths, signal handlers, or `atexit`. Finalizer retry is
per-entry skips only. In-repo callers are tests-only. The WHO-calls
list omits `tests/types/test_converters.py` (covered as the F4
oracle) and `tests/test_list_field.py::test_djangolistfield_rejects_a_target_the_registry_has_never_seen`
(unregistered-target rejection) — still tests-only, verdict
unaffected; noted as trace incompleteness, not a defect.

Gate (agree, same bar as siblings): no gate deferred with reason.
A hand copy passes every behavior oracle by construction; only a
source census ("every `__init__` attribute has a drop arm") could
pin unity, and that is the bespoke per-helper existence test
[DRY][dry] forbids for gate-only findings. Identical bar to all
six verified `type-registry-*` siblings.

Challenges (agree): C1 1 rule / 2 sites (+ oracle rows, not
counted); C2 1 (+0 enum — my pre-read posited a policy-flip shape
vs the artifact's re-register-cleanliness shape, same count);
C3 rejected (mine was the conn-evict-via-bus subcase of the
general record); C4 1 (`_run_type_teardowns`). Count > 1 nowhere.
R1/R2 unfired re-verified (1 `_clear_if_importable` def + 1 call
site + 1 connection literal; 1 pair def + 1 production caller;
`_detach_type_from_model` shared). D1 already-homed names the one
unpinned arm (`test_clear_drops_all_state` pins map/enum only;
definition + pending arms share one closeout card).

Freshness re-hashed (all match, none stale): `registry.py`
`612bea87…`, `types/finalizer.py` `f4266a15…`,
`tests/test_registry.py` `e330cfb8…`,
`tests/test_relay_connection.py` `b6bd90d9…`,
`tests/optimizer/test_extension.py` `883720ee…`,
`tests/types/test_resolvers.py` `88f7fb07…`,
`tests/conftest.py` `3578a7bf…`, `types/base.py` worktree
`4bd9ad16…` (`HEAD` `91c58747…` ledgered consolidation outside
teardown lines), `connection.py` worktree `3c4d5dcb…` (`HEAD`
`93e998f2…` concurrent cursor-guard outside cache lines),
`relay.py` `69085e7a…` + `types/relay.py` `c333c785…` (ledgered
clauses), sibling artifacts `4350662b…` / `8afa1681…` /
`a3842ee8…` / `82f6fdb9…` / `6f2d1726…` / `26d77471…`.
Population 117 `.py` both trees.

`## Pending execution` (agree, None): 32/32 + N1
execution-verified in the disposable copy (copy `__file__` + copy
DB `NAME` recorded, no source mutation, byte-identical restore);
20-pass focused run green post-trace with zero edits in flight.
`FAKESHOP_SHARDED=1` / Postgres inapplicable by construction
(in-memory dict/list + pure class construction; probes open no
DB) — Worker 1 states the reason, judged valid. Full-suite gate
deferred to the final-gate item (entry command authorizes
workspace runs + one focused `--no-cov`; a green unmutated suite
discharges no failability proof for a gateless rejection).

AGENTS.md prose on empty diff (agree): worktree `M` hunks on both
members are this cycle's ledgered docstring clauses only
(`definition_for_graphql_name` trigger at Family
relay-node-name-decode; snapshot-block trigger at Family
globalid-setting-snapshot); item-scoped diff vs `ITEM_BASELINE
78471afe` byte-empty on both paths. No production lines, no test
lines, no `CHANGELOG.md`, no commit. Ruff vacuous (zero touched
`.py`; `.md` excluded). Artifact keeps reference-style links,
bottom definitions block, and `path::Symbol` citations.
Concurrent dirt preserved; nothing reverted.

Defects (Worker 2): none meeting the [AGENTS][agents] bar. The
WHO-calls omission above is an observation, not a defect (no
contract row breaks, no wire/config input reaches it).

Verdict: `verified`. Zero edits, no pending execution.

Exact plan rows for Worker 0: tick Family
`type-teardown-lifecycle` (`docs/dry/dry-rule-type-teardown-lifecycle.md`)
as `verified (Run 0.0.15 2026-09-19-1; REJECTED single-owned,
per-aspect lifetimes intentionally separate, no gate; zero edits;
D1 already-homed; no pending execution)`; `## Responsibility index`
row `type-teardown-lifecycle` stays `open` → `rejected` (owner
`django_strawberry_framework/registry.py::TypeRegistry`, files
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py` already covered);
no `## Owned changes` append; scratch removal by explicit path
only: `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/teardown-w1`
(+ `probe_teardown.py` inside; no manifest).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[registry]: ../../django_strawberry_framework/registry.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py
[test-relay-connection]: ../../tests/test_relay_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
