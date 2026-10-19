# Review · Mechanics: `django_strawberry_framework/registry.py`

Status: findings-recorded
Run: 0.0.15 2026-09-28-3

Baselines: CYCLE_BASELINE=6ac698704402240b954f95072bed4639354ab831 ITEM_BASELINE=da5c1882de6a2330b1ce41878b78c073ef5a36b4

## Trace

Required reading in order: AGENTS.md, START.md, REVIEW.md,
worker-1.md, the plan (`docs/review/review-0_0_15.md`, run 0.0.15
2026-09-28-3, incl. its `## Owned changes`, which holds no row for
this target as a reviewed item; the types/relations.py rows touched
this file only as a prose owner), `docs/review/rev-registry.md`
(skeleton, Status: reviewing, Path class blank). Sibling axis
records `docs/review/rev-registry.performance.md` and
`docs/review/rev-registry.comments.md` did not exist when read; no
Handoff or Cross-axis sections to absorb.

Target read whole (641 lines) live at blob `492654d2` (dirty).
`git diff ITEM_BASELINE -- django_strawberry_framework/registry.py`
is empty: the item baseline captured the dirty tree, so live IS the
baseline. HEAD blob for the target differs (`git diff HEAD` is
+54/-23): the concurrent truth-migration (`truth.IdentityMap` maps,
`truth.name` error rendering, `_identity_index`, nested enum dict).
Reviewed live as dispatched; every verdict below grades the live
bytes, and the L1/C1 paths are behavior-identical at HEAD and live
(no HEAD..live hunk touches the finalized guards or the
subsystem-clear bus), so neither is an artifact of concurrent work.

Orientation: `review_inspect.py` overview at
`docs/review/temp-tests/registry/mechanics/inspect/` (json
`docs/review/temp-tests/registry/mechanics/registry.json`): 32
symbols, 3 control-flow hotspots, 0 hot entry points. Leads only.

Edges traced by read (callers, importers, registrations, oracles):

- Sole production `register_with_definition` caller:
  `DjangoType.__init_subclass__` (`types/base.py`, one call site);
  standalone `register_definition` has zero production callers
  (package-wide census) and serves test fixtures only.
- Finalizer: pending drain-then-discard
  (`types/finalizer.py`, collects into locals during iteration,
  single `discard_pending` after the loop, never interleaved);
  the `_globalid_setting_snapshot` stamp/compare seam (spec-031);
  the pre-bind `iter_subsystem_clears(before_bind=True)` replay.
- Decode: `types/relay.py::decode_global_id` is the sole
  production `definition_for_graphql_name` caller (type-name
  branch); the model-label branch uses `get` + `get_definition`.
- Subsystem bus: 20 import-time registrations across
  filters (2), orders (2), forms (3), mutations (3), auth (2),
  rest_framework (3), optimizer (2), connection (2), relay (1);
  7 carry `before_bind=True`, all input-namespace rows.
  Callback bodies read for the routed lead:
  `connection.py::clear_connection_type_cache`,
  `connection.py::clear_window_edge_class_cache`,
  `relay.py::_clear_node_fields_declared` touch module globals
  only and import nothing at call time.
- Import seam: `utils/imports.py::import_attr_if_importable`
  returns `None` on `ImportError` and fails loud
  (`AttributeError`) on a missing attribute, so the
  `unregister` eviction string cannot rot silently into a skip.
- Identity storage: `utils/truth.py::IdentityMap` read whole
  (`keys`/`items`/`values` return snapshot lists, so
  `reversed(...keys())` in `clear` is sound; `setdefault`,
  `pop`/`get` with defaults, `__contains__` all present).
- Public surface: the package root re-exports no registry name;
  consumers import `django_strawberry_framework.registry`
  directly; the module defines no `__all__`, so none can disagree.
- Oracles: `tests/test_registry.py` (80 tests, read whole),
  `types/converters.py::convert_choices_to_enum` (first-writer-wins
  enum contract), GLOSSARY `Meta.primary` + `finalize_django_types`
  anchors, spec-027 Decision 9 / spec-028 Decision 9 (registration
  seam; rationale retractions of the `except ImportError` block
  shape), spec-030 P3b (connection co-clear; mechanism retired,
  tolerance contract live), spec-031 (snapshot + decode entry),
  spec-032 Decision 8 (node ledger).

Instrument: one scratch probe,
`docs/review/temp-tests/registry/mechanics/probe_mechanics.py`
(copied into the copy as `tests/test_mech_probe_registry.py`),
run `review-20260929T072925-224309` (address
`review/registry.py/mechanics`, cell default, exit 0, 3 passed:
unknown-type post-finalize `unregister` raises, post-finalize
`register_type_teardown` raises, `clear` under poisoned
connection+relay modules drops state without raising). Committed
module run `review-20260929T072947-38e8ff` (same address, cell
default, exit 0, 80 passed, incl. all four clear-tolerance twins).

Cells: default run for every probe above. Sharded and pg are
`inapplicable by construction` for this target (pure in-memory
maps; the module references no connection, alias, `using`, or
dialect token, and its tests use models as identity keys plus
`_meta` introspection only, never a query) and were not run; the
verifier judges the claim.

Looks-for discharge (Mechanics floor):

- Rule enforced at a caller instead of its owner: none. The
  register-before-definition ordering is documented at both ends
  and the sole production path uses the atomic pair (R4); the
  snapshot stamp/compare lives in the finalizer per spec-031 with
  the registry owning only the slot; the finalized-subclass
  reject lives in `__init_subclass__` with `_check_mutable` as
  the deliberate second boundary, documented as defense-in-depth.
- Policy in an adapter, mechanism in a policy layer: none. The
  registry stores and replays; domain validation lives at the
  owners (relay strategy validation, finalizer audits, the
  imports module owning every best-effort shape).
- Decision vs contract sources: L1 (pin gap, not a body
  mismatch). Every body-vs-contract comparison holds: the
  `Meta.primary` anchor (get/primary_for/types_for surface,
  duplicate-primary message, audit fix sentence), the
  `finalize_django_types` anchor (clear runs teardowns yet is no
  general unfinalizer), spec-031 (sentinel-vs-None, unconditional
  stamp, clear-reset), the registration seam (no import inside
  `clear`).
- Branch no real path reaches: none, besides the deliberately
  unreachable invariant tail in R1. Every other defensive
  branch is pinned: rollback `else`-restore, idempotent
  re-register both directions, reverse collision, ambiguous
  `get`, teardown retry.
- Mode flag standing in for a named adapter: none.
  `before_bind` is a subset selector over one callable type with
  two documented consumers (`clear` replays all, the finalizer
  pre-bind replays the flagged subset) and 7 production flagged
  rows; no adapter varies behind it.
- State owned in two places: none. `_types`/`_models` move
  through the shared `_detach_type_from_model` (both the
  `unregister` purge and the rollback); `_primaries`
  snapshot/restore is pinned for all three rollback shapes;
  the enum dict nests field names under one identity-keyed
  model entry; subsystem state lives at its owner with the bus
  holding resolved callables only.
- Dependency pointing the wrong way: none. Module top imports
  leaves only (`exceptions`, `utils.truth`,
  `utils.imports`); `types.*` enters via `TYPE_CHECKING` or
  the decode-time function-local relay import;
  `connection` is reached through the best-effort seam that
  fails loud on rename.
- `django.conf.settings` read at import: none. Zero settings
  references in the module; the snapshot is computed by the
  finalizer, never here.
- `__all__` disagreeing with the public surface: none. Absent,
  not disagreeing: the root re-exports no registry name and
  every consumer imports the submodule directly.
- Two sites implementing one rule: none (DRY challenges, every
  count 1). Posit `change the empty-list invariant` — one
  definition (`_detach_type_from_model`, shared by purge and
  rollback). Posit `rephrase already-registered` — one
  definition (`_already_registered`, shared by type and enum
  collisions). Posit `reword the finalized refusal` — one
  definition (`_check_mutable`). The per-type eviction
  (best-effort string seam) vs the registry-wide replay
  (resolved-callback bus) are correctly separate: one evicts a
  single entry without importing subsystems, the other replays
  whole-subsystem teardowns; neither can serve the other's call.
- Sync/async twins that drifted: none. No async surface in the
  module.
- Guard one flavor has and a sibling lacks: L1 (both guards
  exist; the pins are missing) and R6 (the bus registration
  is unguarded by design, no contract establishes the rule).

Fingerprints (`git hash-object`, live tree):
`django_strawberry_framework/registry.py`
`492654d219d1061fef33f186d962dc5369b71ebe`;
`tests/test_registry.py`
`48af782ff707baaf1619da26d2e286d2ba5178f4`;
`django_strawberry_framework/utils/imports.py`
`291ecedd30c7d8af9c007758112e867c09d031eb`;
`django_strawberry_framework/utils/truth.py`
`d5c96bc8d191d3fce0a20140d8e91063bb466ec9`;
`django_strawberry_framework/connection.py`
`1fca6266cd5f748915875badf1881680b599de37`;
`django_strawberry_framework/relay.py`
`e75e2b66a9b406f60d55e952a001d640392331c1`;
`django_strawberry_framework/types/finalizer.py`
`b9d8acb2b9428cc8297550414ff86bdd98e0d1a7`;
`django_strawberry_framework/types/relay.py`
`4b2a9df59d6dc99270e3aa8ffac397468f7eee1b`;
`django_strawberry_framework/types/converters.py`
`f6cadb0856c725d96ce316abb4418b4c9d55bf9d`;
`django_strawberry_framework/types/base.py`
`dc67f084cbc969d64b7b1f1ef18c388095d394f7`;
`django_strawberry_framework/__init__.py`
`0ef72601ecac300ac87ff993af1b04a4f1bc335a`;
`docs/GLOSSARY.md`
`3413edc36ccf2ab50d9e0f3c9d78cf1df75024cd`.

## Findings

### High

None.

### Medium

None.

### Low

#### L1: two finalized-guard behaviors are documented but unpinned

- **Observation** — Two behaviors of the finalized lifecycle are
  true, documented, and reachable through the public mutators,
  yet no committed test pins them. (a)
  `django_strawberry_framework/registry.py::TypeRegistry.unregister`
  documents guard-before-check ordering: post-finalize calls
  raise `ConfigurationError` "even for unknown types". The
  known-type arm is pinned
  (`test_unregister_raises_after_finalize`) and the
  unknown-unfinalized arm is pinned
  (`test_unregister_is_noop_on_unknown_type`), but the
  unknown-plus-finalized cell has no row: a future reorder
  (None-check first) would silently turn the documented raise
  into a no-op. (b)
  `django_strawberry_framework/registry.py::TypeRegistry.register_type_teardown`
  carries `self._check_mutable()`, but
  `test_mutators_reject_calls_after_mark_finalized` — named
  "every mutator" — exercises only five of the seven mutators
  (`register`, `register_definition`, `add_pending_relation`,
  `discard_pending`, `register_enum`); deleting the guard line
  changes behavior with the suite still green, since statement
  coverage executes the line through unfinalized calls.
- **Evidence** — Workspace run `review-20260929T072925-224309`
  (address `review/registry.py/mechanics`, cell default, exit 0,
  3 passed): the scratch probe asserts both behaviors raise
  `ConfigurationError` matching "finalized" on the live tree, so
  the pins hold today and the gap is coverage, not behavior.
  Census: `mark_finalized` appears in `tests/` +
  `examples/fakeshop/` only inside
  `test_mutators_reject_calls_after_mark_finalized` (definition,
  docstring, one call), and `register_type_teardown` outside the
  target appears only in `tests/test_registry.py`, so no other
  module pins either cell.
- **Impact** — A guard deletion or reorder lands silently: the
  suite stays green (the lines remain executed) while the
  documented finalized boundary weakens. Bounded to test-only
  drift; production behavior today is correct.
- **Severity** — Low. Test-only gap on correct behavior; no
  production change, one test extended.
- **Recommendation** — Owner: `tests/test_registry.py`. Extend
  `test_mutators_reject_calls_after_mark_finalized` with the two
  rows (teardown-after-finalize raises;
  unregister-of-unknown-after-finalize raises), which also makes
  the "every mutator" name true. No production change.
- **Must not change** — Production behavior: both guards stay
  exactly as they are. The test's existing five rows stay intact.
- **Proof** — At `review/registry.py/verify-mechanics-<n>`:
  `uv run python scripts/workspace.py run
  review/registry.py/verify-mechanics-<n> -- pytest
  tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized
  --no-cov` reports `1 passed`. Failability expectation for the
  verifier: reverting the `self._check_mutable()` line in
  `register_type_teardown`, or moving it below the `model is
  None` check in `unregister`, must fail this node.
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner:
  `tests/test_registry.py`. Contract sources: the
  `TypeRegistry.unregister` docstring guard-before-check
  sentence; the `TypeRegistry._check_mutable` docstring
  ("refuse mutation after `mark_finalized`", and teardown
  registration is a mutation); the test's own "every mutator"
  name.

## Rejected

### R1: `_detach_type_from_model` subscripts a possibly-None index

`_identity_index` returns `int | None` and the detach helper
subscripts it directly, so a broken `_types`/`_models` lock-step
would surface as `TypeError` (`list indices must be integers`)
rather than a loud invariant failure. Unreachable through the
public mutators: `register` and `_detach_type_from_model` are the
only `_types[model]` list writers, the reverse-collision raise
fires before any mutation, and no contract names the
broken-invariant error (the previous `list.remove` raised an
equally uncontracted `ValueError`). Robustness row, never a
release blocker. Trigger: a new mutator touching one map without
the other, or a typing gate flagging the `None` subscript.

### R2: `clear()` is not atomic across subsystem callbacks

A raising subsystem callback aborts the replay loop, leaving
later subsystems uncleared while the registry maps are already
dropped. No contract promises atomicity; the failure is fail-loud
(the clearing test errors, never a silent partial state) and the
next fixture entry-clear retries the remaining callbacks, so the
system self-heals. Trigger: a contract promising `clear()`
atomicity, or an incident of a raising subsystem callback.

### R3: two subsystems could collide on one bus owner string

`register_subsystem_clear` overwrites by owner, so a shared owner
string would silently drop one subsystem's teardown. Owners are
first-party dotted identities, distinct by census across all 20
production registrations; only a first-party typo collides, and
raise-on-replace enforcement is incompatible with the documented
reload-replace (`importlib.reload` must install the new function
object under the same owner). Trigger: a second registration
under one owner, or a collision incident.

### R4: `register_definition` requires no prior `register`

The asymmetry is documented at both ends and never manifests in
production: the sole production caller uses
`register_with_definition` (package-wide census: one call site,
`DjangoType.__init_subclass__`), and standalone use is test
fixtures building definition-only entries. Trigger: a production
caller of standalone `register_definition`, or a
definition-without-registration reaching the finalizer.

### R5: `unregister` leaves the model-keyed enum cache behind

Evicting `(model, field_name)` entries on a single-type removal
would break registered siblings sharing the column, and
first-writer-wins sharing is the documented
`convert_choices_to_enum` contract ("the first `DjangoType` to
read a given `(model, field_name)` wins the enum's GraphQL
name"). `unregister` is pre-finalize-only and `clear()` drops the
cache on lifecycle reset. Trigger: a post-`unregister`
re-registration publishing a stale enum name outside a test
lifecycle.

### R6: `register_subsystem_clear` carries no finalized guard

Unlike the `TypeRegistry` mutators, the bus registration has no
`_check_mutable` equivalent. No contract source establishes the
rule applies: the bus is module-global and import-time, and a
post-finalize registration only schedules work for the next
`clear()` — it cannot corrupt the finalized snapshot, whose
readers consult registry maps, not the bus. Trigger: a
post-finalize registration corrupting finalized state.

## Cross-axis (for Comments)

### C1 (Medium): the connection and relay clear-tolerance twin docstrings describe the retired `except ImportError` mechanism

Routed lead from connection.py Comments, judged in Mechanics
scope: the tolerance behavior holds; only the mechanism prose is
stale, which is this section's finding for the Comments axis.

- **Observation** — The docstrings of
  `test_clear_tolerates_unimportable_connection_submodule` and
  `test_clear_tolerates_unimportable_relay_module` in
  `tests/test_registry.py` describe an `except ImportError`
  guard with a cycle-safe local import inside
  `django_strawberry_framework/registry.py::TypeRegistry.clear`
  (spec-030 P3b / spec-032 Decision 8 mechanism). The live
  `clear` has no import and no guard: it replays resolved
  callables via
  `django_strawberry_framework/registry.py::iter_subsystem_clears`.
  Tolerance now comes from the seam (an unimported subsystem
  never registered, so there is nothing to replay; a registered
  callback is an already-resolved function object), not from a
  guard. The filter and order twins already describe the live
  mechanism and are cleared by this review — the order twin
  does NOT share the staleness — while the `unregister` twin's
  guard claim stays true (it routes through
  `django_strawberry_framework/registry.py::_clear_if_importable`
  into
  `django_strawberry_framework/utils/imports.py::import_attr_if_importable`).
- **Evidence** — Live `clear` body read (no import, no guard);
  workspace run `review-20260929T072925-224309` (poisoned
  connection+relay modules, `clear` drops state without
  raising); committed run `review-20260929T072947-38e8ff` (80
  passed, all four twins green); both callbacks read (module
  globals only, no call-time import); the spec-027/spec-028
  rationale retractions of the block shape.
- **Impact** — A reader maintaining the tolerance contract hunts
  for a guard that no longer exists, and the file now teaches two
  mechanisms side by side (live replay in the filter/order
  twins, retired guard in the connection/relay twins).
- **Severity** — Medium (proposed; owning axis judges). Stale
  behavioral prose that misleads about where the contract lives.
- **Recommendation** — Owner: `tests/test_registry.py`. Rewrite
  the two docstrings in the filter/order twins' vocabulary
  ("`clear()` itself imports nothing; it replays resolved
  callbacks"), keeping the spec pointers as Decision pointers.
  Exact text is the Comments pass's call.
- **Must not change** — n/a (Comments finding).
- **Proof** — Static, in the shared tree:
  `grep -c 'except ImportError' tests/test_registry.py` prints
  `1` (today `3`: only the `unregister` twin's true claim
  remains). Plus the grade: both rewritten docstrings grade
  true.
- **Freshness** — Trace fingerprints cover every cited file.
- **Owner + contract source** — Owner:
  `tests/test_registry.py`. Contract sources: the live
  `TypeRegistry.clear` body; the filter/order twin docstrings
  (in-file oracles of the live mechanism).

Handoff: Mechanics on `registry.py` is a small record by design:
the module is a well-factored store (shared detach helper,
single guard, single import-handling owner, bus-owned
subsystem state) and the trace closed every looks-for entry
with one test-pin Low plus the routed prose twin for Comments.
Beyond the record I read the DRY rule-file names only as a
census sanity check (owner strings), not as findings input;
no prior-cycle finding is imported. Open threads for the next
pass of this axis: none on the code — L1 is expected-deferred
(a Low on a file no higher finding touches) and C1 rides with
the Comments verifier. If Worker-2 implements L1, the Proof's
failability expectation (guard-revert fails the node) is the
load-bearing check, since the pass criterion alone also holds
pre-fix.

## Verify mechanics

Verify pass 1 over Implement pass 1 (`docs/review/temp-tests/registry/diff/pass-1.diff`,
read whole; live fingerprints at verify time match its post-images:
`django_strawberry_framework/registry.py` 27358cbc,
`tests/test_registry.py` 8bd9a869,
`tests/orders/test_composition.py` 9414d257). Address
`review/registry.py/verify-mechanics-1`, cell default throughout.
L1 arrived implemented (not deferred): the two Proof rows plus the
Comments F5 first line landed in
`tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized`.

- L1 Proof node, pass: `pytest
  tests/test_registry.py::test_mutators_reject_calls_after_mark_finalized
  --no-cov` reports `1 passed`, run
  `review-20260929T075245-130908` (copy fresh, package digest
  `sha256:ecded019e560d47d15a90b09ad8e21899e087da4bbf0bf385f2cdef5855d7152`).
  The two new rows pin the intended cells: the teardown row raises
  through `_check_mutable` before the unregistered-type check, and
  the unregister row exercises an unregistered class
  (`CategoryType` never registered in the fresh registry), so it
  pins unknown-plus-finalized.
- Failability mutant A (guard deletion), pass — the load-bearing
  check: deleting the `self._check_mutable()` line in
  `TypeRegistry.register_type_teardown` inside the verify copy only
  fails the node, run `review-20260929T075337-94df37`
  (`1 failed`, copy modified: 1 file). Failure at line 1044 for the
  right reason: without the guard the call raises `Cannot register
  class teardown for unregistered type CategoryType`, which does
  not match `finalized`.
- Failability mutant B (guard reorder), pass: moving
  `self._check_mutable()` below the `model is None` early return
  in `TypeRegistry.unregister` inside the verify copy only fails
  the node, run `review-20260929T075402-5fa5b0` (`1 failed`). Failure
  at line 1046: `DID NOT RAISE ConfigurationError` — the reorder
  silently turns the documented raise into a no-op, exactly the
  drift L1 guards against.
- Whole own module, pass: `pytest tests/test_registry.py --no-cov`
  reports `80 passed`, run `review-20260929T075424-064cc4` (copy
  byte-restored to pristine before the run: `cmp` clean against the
  shared tree, both 27358cbc).
- Zero production-code change, pass: `review_inspect.py
  --code-digest
  da5c1882de6a2330b1ce41878b78c073ef5a36b4:django_strawberry_framework/registry.py
  django_strawberry_framework/registry.py` exits 0 with two equal
  digests (`sha256:3949c41469a18c564d34006d3a18e7102735586ca0dd902e56c9cb4b2f8d6212`);
  the three target hunks are docstring-only (Comments F4/F7/F8).
  Regenerating the item diff (`git diff ITEM_BASELINE` over the
  four pass paths) is byte-identical to `pass-1.diff` (`cmp`
  clean), so no concurrent hunk landed in the item's files; the
  F11-deferred `tests/orders/test_inputs.py` is untouched vs
  `ITEM_BASELINE`.
- Rejections R1-R6 stand undisturbed, pass: the digest identity
  above proves every target body (and the mutator set) unchanged,
  which carries R1 (no new one-map mutator), R2 (`clear` body),
  R4 (registration seam), R5 (`unregister` body) and R6 (bus
  body); R3 re-censused by AST over the live package: 20
  `register_subsystem_clear` calls, 20 distinct owners, zero
  collisions, 7 `before_bind=True` rows — identical to the
  record. No trigger tripped.
- Cells, judged: default run for every check above. Sharded and pg
  are `inapplicable by construction`, concurred: the target sweep
  finds zero ORM / alias / dialect / lock tokens in code (the
  single `_meta` hit is prose inside the `model_for_type`
  docstring), and the L1 node runs against an isolated
  `TypeRegistry` with models as identity keys plus `_meta`
  introspection, never a query.
- Lint gates on the touched paths, pass (read-only): `ruff check`
  all passed, `ruff format --check` 3 files already formatted,
  `check_trailing_commas.py --check` 4 files 0 violations.

Environment note: the address's first two runs
(`review-20260929T075004-c718d1`,
`review-20260929T075014-150859`, both exit 1) failed before
collection — the reused slot venv had hollowed site-packages
(`pluggy/` held only a stale `__pycache__`; ~20 packages
similarly stripped, predating this run) while `uv sync` audited
clean. Repaired by deleting the slot's `.venv` (my bound copy
only) and letting the next `--fresh` run rebuild it; the Proof
run above is on the rebuilt venv. Sibling slot-1
(`review/registry.py/before`) shows the same hollowing and was
left untouched for Worker-0.

Status: verified. Open threads: none on this axis. C1 rides with
the Comments verifier per the record.

Handoff: verified L1 plus the undisturbed-rejections fence; every
check above ran at `review/registry.py/verify-mechanics-1` with
the cited run ids, and both failability mutants were applied and
byte-restored inside that copy only (pristine snapshot and
regenerated diff under
`docs/review/temp-tests/registry/verify-mechanics-1/`). Beyond
the record I read the live target's guard bodies, the L1 node,
the pass diff, and the bus-registration call sites for the R3
re-census; no new defects found. One item for Worker-0, not this
axis: the `before` copy's venv is damaged the same way mine was
(see Environment note) — any future before/after run on
`review/registry.py/before` needs a venv rebuild first.
