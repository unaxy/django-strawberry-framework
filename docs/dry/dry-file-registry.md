# DRY review: `django_strawberry_framework/registry.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

The target owns the package's process-global collected-type store plus the
lifecycle bus every subsystem teardown rides. Read in full (610 lines), plus
every connected implementation a sound judgment needs: the finalizer build
([finalizer][finalizer]`::finalize_django_types`), the set-lifecycle
descriptor ([sets-mixins][sets-mixins]`::SetLifecycleAttrs`), the generated-input
reset ([utils-inputs][utils-inputs]`::clear_generated_input_namespace`), the import
owner ([utils-imports][utils-imports]`::import_attr_if_importable`), the
`DjangoType` collection entry ([types-base][types-base]`::DjangoType.__init_subclass__`),
the enum/relation consumers ([converters][converters]`::convert_choices_to_enum`,
`::resolved_relation_annotation`), the Relay decode caller
([types-relay][types-relay]`::decode_global_id`), the memoized consumer
([definition][definition]`::DjangoTypeDefinition.related_target`),
the declaration-registry factory ([mutations-sets][mutations-sets]`::make_declaration_registry`),
the connection cache ([connection][connection]`::clear_connection_type_cache`),
and the full oracle file ([test-registry][test-registry], 2115 lines).

What the target owns:

- `TypeRegistry`: model-to-type-plus-primary maps, definition store, pending-relation
  ledger, choice-enum cache, finalize gate flag, per-type teardown ledger, GlobalID
  setting snapshot storage, and the `clear()` full reset.
- The subsystem-clear bus: `_subsystem_clears`, `register_subsystem_clear`,
  `iter_subsystem_clears`, the `before_bind` phase vocabulary. 17 owner callbacks
  register at import time (7 `before_bind=True` emit/cache rows, 10 full-clear-only
  declaration/ledger rows); `TypeRegistry.clear()` replays all, the finalizer replays
  the `before_bind` subset pre-bind.
- The process-global singleton `registry` and the best-effort per-type co-clear
  helper `_clear_if_importable` (single caller: `unregister`'s connection-cache
  eviction; delegates to [utils-imports][utils-imports]`::import_attr_if_importable`).

Relation to the DRY.md worked example (recorded precisely): this file owns
NEITHER half of that lifecycle. The reset population is declared by
`FilterSet._lifecycle` / `OrderSet._lifecycle`
([sets-mixins][sets-mixins]`::SetLifecycleAttrs`, `::binding_attrs`); the reset body is
[utils-inputs][utils-inputs]`::clear_generated_input_namespace`. This file is the
transport: owner modules register `clear_*_input_namespace` callbacks on the bus,
and `clear()` replays them. Three owners composed by name: descriptor (population),
`clear_generated_input_namespace` (body), `registry.py` (bus + phase flag). The
`registry.clear()` path spells no slot name; verified by grep (`binding_attrs` /
`SetLifecycleAttrs` occur zero times in the target). Four distinct state kinds stay
separate: `TypeRegistry` maps, per-subclass set binding attrs, declaration ledgers
(`make_declaration_registry` instances, `before_bind=False`), input-namespace module
ledgers (`before_bind=True`).

Registry vs finalizer split (`types/finalizer.py` vs `registry.py`): the registry owns
collected state, the mutation boundary (`_check_mutable`), teardown replay, the phase
vocabulary, and the decode lookup (`definition_for_graphql_name`). The finalizer owns
build policy: phases, the primary-ambiguity audit, annotation rewrite (via converters),
interface injection, `strawberry.type` decoration, bind orchestration, teardown
REGISTRATION for synthesis artifacts, and snapshot COMPUTE-plus-compare. The finalizer
reads the store through public getters only, with one sanctioned exception: the
`_globalid_setting_snapshot` read/write (stored-derivation halves, see F9). The
one-shot `models_with_multiple_types()` generator is materialized once per build into
`multi_type_models` (comment-pinned at the call site).

Consumers (all compose by name; no second definition found): `related_visibility_queryset`
([querysets][querysets], `registry.get` resolve step of `queryset-seed-and-model-read`),
`visible_related_object(s)` (same, via the former), optimizer walker/extension
(`get` / `get_definition` / `model_for_type` / `iter_types`), `permissions.py`,
`list_field.py`, `types/definition.py` (memoized, post-finalize only), `types/relay.py`
(decode), `types/resolvers.py`, `mutations`/`auth` resolvers (`get` / `types_for`
split), `testing/relay.py`, the `inspect_django_type` command, and the schema audit.
Oracles: [test-registry][test-registry] (map, primary, teardown, pending-identity, phase
atomicity, ambiguity audit, unregister, tolerance). Projections: in-file docstrings
(verified accurate against bodies), glossary clear/snapshot/invariant entries, and
specs 018/027/028/031/032/036/038/050 as contract sources.

## Verification

### Matrix

1. **Cross-flavor mirroring.** 17 `register_subsystem_clear` call sites enumerated
   (8 visible in a minimal process: `connection.type_cache`, `relay.node_fields`,
   `forms/mutations` declarations + shape caches + input namespaces; 9 more appear
   once their subsystem imports: `filters/orders` namespaces + helper ledgers,
   `rest_framework` namespace + shape cache + choice enums, `auth` declarations +
   current-user-alias namespace). Sibling declaration registries (`mutations` / `forms` /
   `auth` via `make_declaration_registry`) share mechanics through that factory with
   disjoint ledgers — already consolidated, intentionally separate from `TypeRegistry`
   (declaration-stage vs collected-type-stage; `before_bind=False` keeps declarations
   across finalize retry while emit state resets). Verdict: distinct contracts (R3).
2. **Sync/async twins.** Zero `async def` in the file (AST-verified: 30 function nodes,
   all `FunctionDef`). Every method is in-memory dict/list/set work: no ORM I/O, no
   awaits, no threads, no cancellation surface. Reads are colorless across sync/async
   callers; mutation is import-time-only by contract (`_check_mutable` + class docstring).
   `one-sync-boundary` and `sealed-execution-queryset` checked, not inherited: no row
   here performs ORM execution or awaits a consumer hook. Trigger: a registry method
   touching the DB or awaiting.
3. **Derived-not-repeated knowledge.** `get()` 3-state derives from `_types`/`_primaries`
   per call; `models_with_multiple_types()` derives per call (one-shot generator, called
   once per build); `definition_for_graphql_name` scans `iter_definitions()` per call
   (pure derivation, deliberately uncached); `types_for()` returns a `tuple()` snapshot.
   The only memoized derivation is owned elsewhere: `related_target` caches post-finalize
   keyed on `is_finalized()` ([definition][definition]). `_already_registered` centralizes
   2 of 5 collision phrasings; the other 3 are inline, test-pinned, intentionally
   distinct (F10).
4. **Round-trip pairs.** register/unregister, register+get+model_for_type,
   register_definition/get_definition, register_with_definition atomicity,
   add/discard_pending (identity-matched), register_enum/get_enum,
   register_subsystem_clear/iter/clear-replay, mark/is/clear-reset. All pinned by
   [test-registry][test-registry] oracles; the module docstring states the wire
   invisibility rationale (map identity, teardown order, pending identity, phase
   atomicity unobservable over `/graphql/`).
5. **Other media.** Docstrings = projections (each verified against its body; the
   module "Used by" list matches the finalizer loop and converter call sites).
   [test-registry][test-registry] = oracles (independent expectations; two tests reach
   into `registry._finalized` as sanctioned harness bypass per the `unregister`
   docstring). Glossary + specs = contract sources/projections. No consumer restates a
   rule: every call site invokes the owner by name.
6. **Enforcement by omission.** All 9 mutators audited: `register`,
   `register_type_teardown`, `unregister`, `register_definition`,
   `register_with_definition` (via `register`), `add_pending_relation`,
   `discard_pending`, `register_enum` call `_check_mutable`; `clear()` bypasses by
   documented contract (test-pinned fresh-finalize cycles); `mark_finalized` IS the flag
   flip. `unregister`'s pre-finalize no-op vs post-finalize raise is documented and
   tested. No gap: no defect.

### Enumeration

Instrument: `ast` parse of the target. 16 top-level statements; 33 rule-bearing named
members (3 module functions, 2 module state attrs, 27 `TypeRegistry` methods,
1 singleton). Imports / docstring / `TYPE_CHECKING` block are machinery or projections,
not rules. Every member lands below; no file-local row (each rule has a second site or
a recorded rejection).

| # | Member | Home |
|---|---|---|
| 1 | `_clear_if_importable` | F1 (sub-rule) + R1 |
| 2 | `_subsystem_clears` | F6 |
| 3 | `GLOBALID_SETTING_UNSET` | F9 |
| 4 | `register_subsystem_clear` | F6 |
| 5 | `iter_subsystem_clears` | F6 |
| 6 | `TypeRegistry.__init__` | F1 (pure construction of all family maps; per-map contracts in F2-F9) |
| 7 | `_check_mutable` | F5 |
| 8 | `_detach_type_from_model` | F1 (shared by `unregister` + rollback; R2 for the remainder) |
| 9 | `_already_registered` | F10 |
| 10 | `register` | F1 |
| 11 | `register_type_teardown` | F7 |
| 12 | `_run_type_teardowns` | F7 |
| 13 | `unregister` | F1 (+ R1 eviction tail) |
| 14 | `get` | F1 |
| 15 | `model_for_type` | F1 |
| 16 | `iter_types` | F1 |
| 17 | `primary_for` | F1 |
| 18 | `types_for` | F1 |
| 19 | `models_with_multiple_types` | F1 (drives the finalizer audit) |
| 20 | `register_definition` | F2 |
| 21 | `register_with_definition` | F2 (+ R2) |
| 22 | `get_definition` | F2 |
| 23 | `definition_for_graphql_name` | F8 (`iter_definitions` scanned as consumer) |
| 24 | `iter_definitions` | F2 |
| 25 | `add_pending_relation` | F3 |
| 26 | `iter_pending_relations` | F3 |
| 27 | `discard_pending` | F3 |
| 28 | `is_finalized` | F5 |
| 29 | `mark_finalized` | F5 |
| 30 | `register_enum` | F4 |
| 31 | `get_enum` | F4 |
| 32 | `clear` | F6 (replay; resets F1/F2/F3/F4/F5/F7/F9 state) |
| 33 | `registry` | F1 (published store) / F6 (clear receiver) |

### Challenges

Authoritative definitions counted only; consumers, oracles, projections listed, not
counted. Probes P1-P10 (`docs/dry/temp-tests/dry-file-registry/probe_registry.py`,
40 asserts, execution-verified read-only in the shared tree).

- F1: change the single-type-no-primary fallback (return `None` always) → 1 definition
  (`get`); probe `single-no-primary-returns-lone` rejects (P2). Change the no-empty-list
  invariant → 1 definition (`_detach_type_from_model`); probes `no-empty-list-residue`,
  `types-for-empty` reject (P2/P3). Re-derive "primary-or-lone" without calling `get()` →
  0 production sites do (all 15 importer modules call the owner; private-map grep shows
  no external `_types`/`_primaries` reads). Consumers: walker, extension, permissions,
  definition cache, relay decode, mutation/auth resolvers, finalizer loop
  (`queryset-seed-and-model-read` consumes; not merged — the map is the definition, the
  read is the consumer).
- F2: change the atomicity (leave a half-registered pair on definition failure) → 1
  definition (`register_with_definition`); probes `rollback-drops-new-type`,
  `rollback-restores-primary`, `rollback-keeps-definition` reject (P10). Add a new
  `register` side effect → the rollback mirror must move with it (docstring-flagged
  coupling; R2 records why it stays inline).
- F3: change identity-match to equality-match → 1 definition (`discard_pending`); probe
  `identity-discard` rejects with equal-by-value records (P7). Change the record shape →
  [relations][relations]`::PendingRelation` (owner of the shape; this family owns the ledger).
- F4: change the cache key `(model, field_name)` → 1 definition (`register_enum` /
  `get_enum` pair); consumer [converters][converters]`::convert_choices_to_enum` unchanged
  (calls by name). Probes `enum-collision-wording`, idempotent re-register (P4).
- F5: change the guard message → 1 definition (`_check_mutable`); add a new mutator →
  checklist (one `_check_mutable()` call; omission would be the defect). Probes
  `finalized-guard-all-mutators`, `clear-bypasses-guard` (P5).
- F6: add a third lifecycle phase beyond the `before_bind` bool → 1 definition site
  (this module: register filter + iter filter); the two replay sites (`clear`, finalizer
  pre-bind) are consumers. Probes `bus-entry-shape`, `narrow-subset`,
  `full-strictly-wider` (P9); laziness proved by the 8-owner minimal-process census.
- F7: change LIFO to FIFO → 1 definition (`_run_type_teardowns`); change retry-retention
  to drop-on-failure → 1 definition; probes `teardown-lifo`, `failed-teardown-retains-type`,
  `retry-drains` (P6).
- F8: change the decode key to `type_cls.__name__` → 1 definition
  (`definition_for_graphql_name`); probes `decode-match`, `decode-ignores-non-node`,
  `decode-ambiguity-names-both`, `decode-miss-names-key` (P8, stub Node subclasses on a
  fresh instance — no global touched).
- F9: change compute-once → [finalizer][finalizer]`::finalize_django_types` (1 definition,
  compute owner); change reset-on-clear → `clear()` (1 definition, storage owner);
  change the unset-vs-None distinction → 1 definition (`GLOBALID_SETTING_UNSET`).
  Static-reviewed (global-mutating path; probes stop at the storage contract).
- F10: rephrase the canonical "already registered" form → 1 definition
  (`_already_registered`, exactly 2 call sites); probes `reverse-collision-wording`,
  `enum-collision-wording` (P4). The 3 inline phrasings (primary-flip,
  duplicate-primary, definition-rebind) are test-pinned distinct — intentional
  separation, not drift.

## Findings

Ten named families for Worker 0 to add to the responsibility index (all `open`; no
consolidation inside a file item — Migration is `none`, owned by the future family
item). Reused index names appear only as consumer links (`queryset-seed-and-model-read`)
or checked-not-inherited (`one-sync-boundary`, `sealed-execution-queryset`).

### F1 `type-registry-model-type-map`

- **Contract + variation.** Model-to-type multi-map with an optional declared primary:
  many types per model, at most one primary, one model per class, no empty-list residue.
  Varies on: primary declared or not (`get` 3-state), registration order (`types_for`).
- **Sites + roles.** Definitions: `register`, `unregister`, `get`, `model_for_type`,
  `primary_for`, `types_for`, `iter_types`, `models_with_multiple_types`,
  `_detach_type_from_model`, `__init__` (construction), singleton `registry` (publication).
  Consumers: finalizer loop + audits, walker, extension, permissions, definition cache,
  relay decode, mutation/auth resolvers, `related_visibility_queryset`
  (`queryset-seed-and-model-read`), testing/relay, inspect command. Oracles:
  [test-registry][test-registry] round-trip/primary/multi-type/unregister tests.
  Projections: method docstrings, glossary primary entries.
- **Challenges.** As listed (fallback → 1; empty-list invariant → 1; re-derivation → 0 sites).
- **Owner + lifetime.** `django_strawberry_framework/registry.py::TypeRegistry` (F1 aspects).
  Narrowest cohesive owner every consumer can import without reversing dependencies;
  no stored derivation beyond the maps themselves (process-global; published at import;
  mutated import-time-only; invalidated by `clear()` / `unregister`).
- **Migration.** None (file item).
- **Distinct behavior.** `get` (primary-or-lone-or-None) vs `primary_for` (strict) vs
  `types_for` (ordered snapshot) stay separate; the ambiguity they jointly describe is
  refused at finalization by `_audit_primary_ambiguity`, not here.
- **Behavioral proof.** P1-P3, P10 (execution-verified; instrument failability proved in
  a disposable workspace: `get()` fallback deleted → probe fails at `get-round-trip`;
  shared-tree blob unchanged `9cc8bb55`; workspace removed).
- **Structural gate.** Probes above + `test_register_and_get_round_trips`,
  `test_get_returns_none_when_multiple_and_no_primary`,
  `test_unregister_keeps_siblings_intact_in_multi_type_case` (existing oracles;
  negative control demonstrated at instrument level; oracle failability not re-proved —
  no consolidation relies on it).
- **Coupling.** None.
- **Freshness.** `registry.py` `9cc8bb55` (= HEAD, clean); consumers `querysets.py`
  `1539b66c`, `permissions.py` `757dce34`, `walker.py` `9b111ed9`,
  `extension.py` `49667a93`, `definition.py` `fa6c4d330`, `types/relay.py` `52439862`,
  `types/resolvers.py` `f3341e6a`, `mutations/sets.py` `cffa29e5`, `base.py` `91c58747`;
  `connection.py` working `3c4d5dcb` vs HEAD `93e998f2` (concurrent cursor-guard dirt,
  content-attributed, untouched); importer census = 15 modules, no external
  `_types`/`_primaries` reads.

### F2 `type-registry-definition-store`

- **Contract + variation.** One collected definition per type class; atomic
  register-plus-define with snapshot-conditional rollback. Varies on: idempotent
  same-definition re-register (no-op) vs different-definition rebind (raise).
- **Sites + roles.** Definitions: `register_definition`, `get_definition`,
  `iter_definitions`, `register_with_definition` (+ `_detach_type_from_model` shared).
  Sole producer: `DjangoType.__init_subclass__`. Consumers: finalizer loops, walker,
  extension audit, `list_field.py`, `testing/relay.py`. Oracles: definition-rebind,
  rollback (3 tests), idempotence tests.
- **Challenges.** Atomicity → 1; new side-effect mirror → flagged coupling (R2).
- **Owner + lifetime.** `TypeRegistry` (F2 aspects); definitions live from
  `__init_subclass__` to `clear()`/`unregister`; never mutated post-construction
  (write-once mirror `definition.primary` is introspection-only prose at
  [definition][definition]).
- **Migration.** None.
- **Distinct behavior.** Rollback restores the pre-call primary snapshot; `unregister`
  purges unconditionally (R2).
- **Behavioral proof.** P10 execution-verified.
- **Structural gate.** Probes + `test_register_with_definition_rolls_back_register_on_definition_failure`,
  `..._rollback_restores_pre_existing_primary`,
  `..._idempotent_re_register_does_not_corrupt_state`.
- **Coupling.** None.
- **Freshness.** Same registry blob; `base.py` `91c58747`; `finalizer.py` `77fd9a2d`.

### F3 `type-registry-pending-ledger`

- **Contract + variation.** Ordered ledger of relations whose target resolves at
  finalization; removal by identity, never equality. No legitimate variation in match
  semantics.
- **Sites + roles.** Definitions: `add_pending_relation`, `iter_pending_relations`,
  `discard_pending`. Record shape owned by [relations][relations]`::PendingRelation`.
  Producer: `__init_subclass__`. Consumer: finalizer Phase 1 (drains into a list before
  mutating, per the stale-view docstring). Oracles: identity-match + non-hashable-field
  + phase-atomicity tests.
- **Challenges.** Identity→equality → 1 definition (P7 rejects).
- **Owner + lifetime.** `TypeRegistry` (F3 aspects); records live collection→finalize,
  drained on success, preserved on Phase-1 failure for retry.
- **Migration.** None.
- **Distinct behavior.** `unregister` drops by `source_type` identity (subset removal);
  `discard_pending` drops by record identity (resolved-set removal).
- **Behavioral proof.** P7 execution-verified.
- **Structural gate.** Probes + `test_discard_pending_uses_identity_match_with_real_pending_relation`,
  `test_discard_pending_tolerates_non_hashable_django_field`,
  `test_phase_1_failure_is_atomic_and_retryable_after_missing_target_registers`.
- **Coupling.** None.
- **Freshness.** Registry blob; `relations.py` `6bd7c63d`; `finalizer.py` `77fd9a2d`.

### F4 `type-registry-enum-cache`

- **Contract + variation.** `(model, field_name)` → one `Enum` class; same-class
  re-register is a no-op (converter retry pattern), different-class collides loudly.
- **Sites + roles.** Definitions: `register_enum`, `get_enum`. Consumer:
  [converters][converters]`::convert_choices_to_enum` (get-then-register). Oracles:
  enum cache/idempotence/collision tests.
- **Challenges.** Key change → 1 definition (P4).
- **Owner + lifetime.** `TypeRegistry` (F4 aspects); entries live collection→`clear()`.
  First reader wins the GraphQL name (converter contract, not registry policy).
- **Migration.** None.
- **Distinct behavior.** None inside; name derivation lives in `build_enum_from_choices`.
- **Behavioral proof.** P4 execution-verified.
- **Structural gate.** Probes + `test_register_enum_caches_by_model_field`,
  `test_register_enum_same_class_is_idempotent`,
  `test_register_enum_different_class_for_same_key_raises`.
- **Coupling.** None.
- **Freshness.** Registry blob; `converters.py` `9ceb34af`.

### F5 `type-registry-finalize-gate`

- **Contract + variation.** Boolean build gate: mutations import-time-only; `clear()`
  alone bypasses for test teardown. No variation in guard placement (every mutator).
- **Sites + roles.** Definitions: `_check_mutable`, `is_finalized`, `mark_finalized`
  (+ `clear()` bypass). Consumers: finalizer entry/no-op + last-statement flip,
  `DeclarationRegistry.register` mirror (fail-loud parity prose), `__init_subclass__`
  (first-line reject). Oracles: post-finalize mutator + unregister + concrete-type tests.
- **Challenges.** Message → 1; new mutator → checklist (P5).
- **Owner + lifetime.** `TypeRegistry` (F5 aspects); flips once per build, reset by `clear()`.
- **Migration.** None.
- **Distinct behavior.** `mark_finalized` (the flip) needs no guard; `clear()` bypass is
  the documented escape hatch, not a hole.
- **Behavioral proof.** P5 execution-verified.
- **Structural gate.** Probes + `test_mutators_reject_calls_after_mark_finalized`,
  `test_unregister_raises_after_finalize`,
  `test_registering_concrete_type_after_finalization_raises`.
- **Coupling.** None.
- **Freshness.** Registry blob; `finalizer.py` `77fd9a2d`; `mutations/sets.py` `cffa29e5`.

### F6 `subsystem-clear-lifecycle`

- **Contract + variation.** Owner-registered zero-arg teardowns keyed by stable logical
  owner (reload-safe replace, no string drift); `before_bind=True` marks per-pass
  emit-state resets the finalizer also runs pre-bind. Varies on phase membership only.
- **Sites + roles.** Definitions: `_subsystem_clears`, `register_subsystem_clear`,
  `iter_subsystem_clears`, `clear()` replay. Consumers: finalizer pre-bind replay (narrow),
  17 owner callbacks (7 narrow, 10 full-only). Oracles: owner-callback, before_bind-filter,
  string-reference/empty-owner rejection, four poisoned-`sys.modules` tolerance tests.
- **Challenges.** New phase → 1 definition site (P9).
- **Owner + lifetime.** `registry.py` bus (principle 7: narrowest owner every subsystem can
  import without cycles; callbacks resolved at owner-import time so partial-load skips).
  Entries live owner-import→process end (test save/restore is harness-only).
- **Migration.** None.
- **Distinct behavior.** Declaration rows (`before_bind=False`) survive finalize retry;
  emit rows reset per pass. `clear()` replays narrow∪full; finalizer replays narrow only.
- **Behavioral proof.** P9 execution-verified (entry shape, subset relation, tuple
  snapshot, 8-owner laziness census in a minimal process).
- **Structural gate.** Probes + `test_clear_runs_owner_registered_subsystem_callback`,
  `test_before_bind_iteration_excludes_full_clear_only_callbacks`,
  `test_clear_tolerates_unimportable_{filter,order,connection,relay}_*`.
- **Coupling.** None.
- **Freshness.** Registry blob; `finalizer.py` `77fd9a2d`; all 17 call sites enumerated
  by body (owners listed in System trace).

### F7 `type-teardown-lifecycle`

- **Contract + variation.** Identity-safe inverses for framework-owned class mutations,
  run LIFO with failed-callback retention for retry, before the registration drops.
  No variation in order or retention.
- **Sites + roles.** Definitions: `register_type_teardown`, `_run_type_teardowns`,
  replay in `clear()` (reversed) + `unregister`. Sole producer: finalizer synthesis
  (`register_type_teardown` at Phase 2.5). Callbacks own same-name-replacement checks.
  Oracles: reverse-order × {clear, unregister}, retry-retention × {clear, unregister},
  invalid-registration tests.
- **Challenges.** Order → 1; retention → 1 (P6).
- **Owner + lifetime.** `TypeRegistry` (F7 aspects); callbacks live registration→first
  successful drain; teardown runs while the registration still resolves (test-pinned).
- **Migration.** None.
- **Distinct behavior.** One-way mutations (intentional, single-interpreter lifecycle)
  stay unregistered; only leak-across-lifecycle artifacts register inverses.
- **Behavioral proof.** P6 execution-verified.
- **Structural gate.** Probes + `test_type_teardowns_run_in_reverse_order_once_before_registration_drops`,
  `test_failed_type_teardown_remains_registered_for_retry`,
  `test_register_type_teardown_rejects_invalid_registration`.
- **Coupling.** None.
- **Freshness.** Registry blob; `finalizer.py` `77fd9a2d`.

### F8 `relay-node-name-decode`

- **Contract + variation.** Unique Relay-Node definition by `graphql_type_name`
  (`Meta.name`-honoring, non-Node invisible); miss/ambiguity raise naming the key or
  both origins. No variation in scan population.
- **Sites + roles.** Definition: `definition_for_graphql_name` (in-function
  `implements_relay_node` import = cycle dodge, both directions documented).
  Consumer: [types-relay][types-relay]`::decode_global_id` type-name branch (model-label
  branch uses F1 `get`). Oracles: match / Meta.name / non-Relay-ignore / miss /
  ambiguity tests; live accept/refuse in `test_library_api.py`.
- **Challenges.** Key change → 1 definition (P8).
- **Owner + lifetime.** `TypeRegistry` (F8 aspects); pure derivation per call, explicitly
  not cached (no lifetime fields owed).
- **Migration.** None.
- **Distinct behavior.** Model-label decode (F1 `get` + `apps.get_model`) stays in
  `types/relay.py`; only the type-name branch inverts here.
- **Behavioral proof.** P8 execution-verified on a fresh instance with stub Node
  subclasses (global untouched).
- **Structural gate.** Probes + `test_definition_for_graphql_name_{returns_match,honors_meta_name,ignores_non_relay_definitions,unknown_raises,ambiguous_raises}`.
- **Coupling.** None.
- **Freshness.** Registry blob; `types/relay.py` `52439862`.

### F9 `globalid-setting-snapshot`

- **Contract + variation.** Validated `RELAY_GLOBALID_STRATEGY` computed once per build;
  `GLOBALID_SETTING_UNSET` distinguishes not-yet-computed from a `None` (no-override)
  snapshot; retry under a changed value refuses (mixed-strategy guard); `clear()` resets.
- **Sites + roles.** Storage definition: sentinel + `_globalid_setting_snapshot` +
  `clear()` reset (registry). Compute definition:
  [finalizer][finalizer]`::finalize_django_types` (unconditional validate + compare).
  Readers: Relay loop stamping + `install_globalid_typename_resolver` paths. Contract
  source: spec-031 snapshot decision; projection: glossary snapshot entry.
- **Challenges.** Compute-once → 1 (finalizer); reset → 1 (`clear`); unset-vs-None → 1
  (sentinel). Static-reviewed (global-mutating path; probes stop at storage).
- **Owner + lifetime.** Split by responsibility: finalizer computes (validity key = one
  build since last `clear()`; publish point = finalize entry; only finalizer mutates),
  registry stores and invalidates (`clear()`). Dependency direction wins over narrowness.
- **Migration.** None.
- **Distinct behavior.** Per-type `effective_globalid_strategy` stamping stays in the
  Relay loop; only the process-setting snapshot lives here.
- **Behavioral proof.** Static-reviewed against finalizer:885-900 + `clear()` reset line;
  no execution (would mutate the global lifecycle).
- **Structural gate.** `override_settings` + `clear()` + rebuild tests in the Relay
  suites (existing oracles; failability not re-proved).
- **Coupling.** None.
- **Freshness.** Registry blob; `finalizer.py` `77fd9a2d`.

### F10 `already-registered-error-wording`

- **Contract + variation.** Canonical `"X is already registered <label> Y"` form shared by
  the two cross-key collision sites; three other raises keep distinct test-pinned
  phrasings. Varies on label only (`against` / `as`).
- **Sites + roles.** Definition: `_already_registered` (exactly 2 call sites: reverse
  collision, enum collision). Intentional non-sites: primary-flip, duplicate-primary,
  definition-rebind raises (distinct phrasings, docstring-recorded). Oracles: substring
  matches in collision tests.
- **Challenges.** Rephrase canonical form → 1 definition (P4).
- **Owner + lifetime.** `TypeRegistry._already_registered`; stateless pure constructor,
  no lifetime.
- **Migration.** None.
- **Distinct behavior.** The three inline phrasings name different violations; unifying
  them would weaken grep-from-stack-trace triage (duplicate-primary test pins all three
  identifiers).
- **Behavioral proof.** P4 execution-verified.
- **Structural gate.** Probes + `test_register_same_class_against_two_models_raises`,
  `test_register_enum_different_class_for_same_key_raises`,
  `test_register_two_primaries_for_same_model_raises_configuration_error`.
- **Coupling.** None.
- **Freshness.** Registry blob.

### Rejections

- **R1 — per-type connection-cache eviction vs whole-cache purge.** Considered shared
  form: one connection-cache co-clear helper. Difference: `unregister` evicts ONE
  identity-keyed entry best-effort at removal time (hygiene; docstring: leftover is not
  a correctness bug); `clear()` purges the whole cache via the owner-registered
  `connection.type_cache` callback at reset time. Different granularity, mechanism, and
  lifecycle moment. Prior trigger check: `docs/dry/dry-0_0_11.md` deferred this until a
  third direct connection reach-in appears in this module — recount: exactly 1
  `_clear_if_importable` call site and 1 `"django_strawberry_framework.connection"`
  literal remain (the `clear()`-side row retired into the bus seam); trigger unfired.
  Home: `registry.py::TypeRegistry.unregister` (docstring narrates the consistency
  rationale). Reconsider when a third direct reach-in lands or `connection.py` exports a
  per-type evict helper.
- **R2 — `register_with_definition` rollback vs `unregister` purge.** Considered shared
  form: one `_drop_type_traces`. Difference: rollback restores the pre-call `_primaries`
  snapshot and touches only state THIS call appended; `unregister` purges unconditionally
  (primary slot, definitions, pending). A shared helper needs a restore-vs-delete mode
  flag obscuring both sites. The common `_types`/`_models` removal IS shared
  (`_detach_type_from_model`, build-018). Prior trigger check: `dry-0_0_11.md` deferred
  until a third partial-rollback site appears — recount: still 1 `register_with_definition`
  definition + 1 caller; trigger unfired. Home:
  `registry.py::TypeRegistry.register_with_definition` (docstring flags the mirror
  obligation). Reconsider on a third site.
- **R3 — `DeclarationRegistry` siblings vs `TypeRegistry`.** Considered shared form: one
  registry abstraction for declarations + collected types. Difference: declaration
  ledgers are pre-bind, per-flavor, disjoint by design (`make_declaration_registry`
  already single-sources their mechanics); folding them into the model-keyed store would
  couple bind policy to lookup policy and erase the `before_bind=False` survival
  contract. Home: [mutations-sets][mutations-sets]`::make_declaration_registry`
  (Decision-13 prose). Trigger: a declaration ledger needing model-keyed
  lookup/primary/pending semantics.

## Defects

No new defects. Spot-checks that could have been defects all hold: in-function imports
in `definition_for_graphql_name` / `types/relay.py` / `types/definition.py` match the
documented cycle (`registry.py` top imports only `exceptions` + `utils.imports`;
`TYPE_CHECKING` only for definition/relation types); `iter_pending_relations` stale-view
docstring matches `discard_pending`'s rebinding; `clear()` order (teardowns → own maps →
subsystem callbacks) matches the teardown-still-resolves pin; the four
poisoned-`sys.modules` tolerance-test docstrings describe the replay seam, matching HEAD
(any remainder of the TODO-ALPHA-051 routing stays homed there, not re-filed here).

## Pending execution

None. All behavioral proofs execution-verified read-only in the shared tree (P1-P10,
40 asserts; fresh instances only; one read-only pass over the live bus census);
instrument failability demonstrated in a disposable workspace (mutated `get()` fallback
→ probe fails at `get-round-trip`; shared-tree blob unchanged; workspace removed).
No consolidation proposed, so no consolidation gate with negative control is owed.

## Judgment

Zero-edit file item: matrix discharged against the real surface, 33/33 members assigned
to ten named families plus three rejections with triggers. The target is a well-factored
owner: every rule has exactly one definition, all consumers compose by name, the two
historical mirrors are either shared (`_detach_type_from_model`) or trigger-checked
(R1/R2, both unfired), and the DRY.md worked-example lifecycle resolves to three
distinct owners with this file as transport only. The `registry.clear()` reset path and
the set-family binding lifecycle are adjacent but different registries; the
registry-vs-finalizer split is mechanism-vs-policy with one sanctioned shared-sentinel
seam. No production edit, no test change, no defect.

## Implementation (Worker 1)

No tracked changes (target clean at `9cc8bb55`, item-scoped diff vs `95f14a08` empty
apart from this artifact plus probe scratch). No `ruff` run (no edits; format gate
moot). No commit per standing rule. Scratch kept for verification:
`docs/dry/temp-tests/dry-file-registry/probe_registry.py` (Worker 0 removes by explicit
path after `verified`). Concurrent dirt left untouched: `connection.py` working hunk
(`3c4d5dcb` vs HEAD `93e998f2`), `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` (+31), `docs/bug_hunt/bug_hunt-0_0_15.md`,
`docs/dry/dry-0_0_15.md` (plan file read, never edited).

## Independent verification (Worker 2)

Recorded expectation-first: the trace below was derived from the target, its
consumers, sibling flavors, oracles and docs before opening `## Findings`;
reconciliation follows the trace. No shared-tree pytest; read-only scratch at
`docs/dry/temp-tests/dry-file-registry-w2/probe_w2.py` (`W2 PROBES PASSED: 51`,
fresh `TypeRegistry()` instances only, global `registry` never written,
`_subsystem_clears` READ only, no DB queries, no source mutation). A
source-mutating negative control ran in a disposable workspace copy taken
after Worker 1's edits (recipe per DRY.md "Tests"); workspace removed,
shared blob unchanged (see below).

### Own trace (counts are authoritative definitions only)

- **Model-to-type map.** Multi-map plus optional declared primary, one model
  per class, no empty-list residue. `get` 3-state (primary / lone / `None`),
  `primary_for` strict, `types_for` ordered snapshot, `iter_types` per-type
  pairs, `model_for_type` reverse (`None` passthrough), `models_with_multiple_types`
  one-shot generator, `register` / `unregister` / `_detach_type_from_model` /
  `__init__` construction / singleton `registry` publication. Change the
  lone-fallback to always-`None` -> 1 definition (`get`); change the
  no-empty-list invariant -> 1 (`_detach_type_from_model`); re-derive
  primary-or-lone without calling `get` -> 0 production sites (all 15
  `registry.get(` importer modules call the owner; no external
  `_types`/`_primaries` reads). Owner I would choose:
  `django_strawberry_framework/registry.py::TypeRegistry` (F1 aspects) —
  narrowest cohesive owner every consumer can import without reversing a
  dependency. Consumers: finalizer loop + audits, walker, extension,
  permissions, definition cache, relay decode, mutation/auth resolvers,
  `related_visibility_queryset`, testing/relay, inspect command.
- **Definition store + snapshot/rollback.** One definition per type class;
  atomic `register` + `register_definition` with snapshot-conditional rollback
  (pre-primary snapshot, appended-flag, `_detach_type_from_model` inverse plus
  primary restore). Change atomicity to leave a half-pair -> 1
  (`register_with_definition`); add a new `register` side effect -> the
  rollback mirror must move (docstring-flagged intra-family coupling).
  Owner: `TypeRegistry` (F2 aspects). Sole producer
  `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
  (register-then-define ordering, then `add_pending_relation`).
- **Pending ledger.** Ordered ledger, removal by `id()` identity never
  equality; record shape owned by
  `django_strawberry_framework/types/relations.py::PendingRelation`. Change
  identity to equality -> 1 (`discard_pending`); change record shape ->
  `PendingRelation`. Owner: `TypeRegistry` (F3 aspects). Consumer: finalizer
  Phase 1 (drains into a list before mutating; stale-view docstring matches
  the `self._pending = [...]` rebinding).
- **Enum cache.** `(model, field_name)` -> one `Enum`; same-class re-register
  no-op (converter retry pattern), different-class collides loudly. Change
  the key -> 1 (`register_enum` / `get_enum` pair). Consumer:
  `django_strawberry_framework/types/converters.py::convert_choices_to_enum`
  (get-then-register by name). Owner: `TypeRegistry` (F4 aspects).
- **Finalize gate + clear/mark bypass.** Boolean build gate, import-time-only
  mutations, `clear()` the documented bypass, `mark_finalized` the flip.
  Change the guard message -> 1 (`_check_mutable`); add a mutator -> checklist
  (one `_check_mutable()` call). Direct guard calls: `register`,
  `register_type_teardown`, `unregister`, `register_definition`,
  `add_pending_relation`, `discard_pending`, `register_enum` (7); indirect:
  `register_with_definition` via `register` (8th path). Owner: `TypeRegistry`
  (F5 aspects). Consumers: finalizer entry/no-op + last-statement flip,
  `DeclarationRegistry.register` mirror, `__init_subclass__` first-line reject.
- **Clear bus + owner callbacks.** Zero-arg teardowns keyed by stable logical
  owner (reload-safe replace); `before_bind` marks per-pass emit-state resets
  the finalizer also runs pre-bind. Static enumeration over package source:
  17 `register_subsystem_clear(` call sites outside `registry.py` (7
  `before_bind=True`, 10 full-only); live minimal-process census in my probe:
  8 owners (`connection.type_cache`, `relay.node_fields`,
  `forms/mutations` declarations + shape caches + input namespaces), narrow 2
  (`forms/mutations` input namespaces), full 8. The 8-vs-17 gap proves
  laziness (only an imported owner can register). Add a third phase -> 1
  definition site (register filter + iter filter); the two replay sites
  (`clear`, finalizer pre-bind) are consumers. Owner: `registry.py` bus
  (principle 7: narrowest owner every subsystem can import without cycles).
- **Teardowns LIFO.** Identity-safe inverses for framework-owned class
  mutations, LIFO with failed-callback retention for retry, run before the
  registration drops (`clear` reversed, `unregister` per-type). Change LIFO to
  FIFO -> 1 (`_run_type_teardowns`); change retention to drop-on-failure -> 1.
  Owner: `TypeRegistry` (F7 aspects). Sole producer: finalizer synthesis
  (Phase 2.5 `register_type_teardown`); callbacks own same-name-replacement
  checks.
- **Node decode.** Unique Relay-Node definition by `graphql_type_name`
  (`Meta.name`-honoring, non-Node invisible); miss/ambiguity raise naming the
  key or both origins. Change the key to `type_cls.__name__` -> 1
  (`definition_for_graphql_name`). In-function `implements_relay_node`
  import is the documented cycle dodge. Consumer:
  `django_strawberry_framework/types/relay.py::decode_global_id` type-name
  branch (model-label branch uses F1 `get` + `apps.get_model`). Owner:
  `TypeRegistry` (F8 aspects); pure derivation per call, deliberately
  uncached.
- **GlobalID snapshot split.** Validated `RELAY_GLOBALID_STRATEGY` computed
  once per build; `GLOBALID_SETTING_UNSET` distinguishes not-yet-computed
  from `None` (no-override); retry under a changed value refuses
  (mixed-strategy guard); `clear()` resets. Compute -> 1 (finalizer
  `finalize_django_types`, unconditional validate + compare); reset -> 1
  (`clear`); unset-vs-`None` -> 1 (sentinel). Split owner by responsibility:
  finalizer computes (validity key one build since last `clear()`; publish at
  finalize entry; only finalizer mutates), registry stores + invalidates.
  Dependency direction wins over narrowness. My probe executes the storage
  half on a fresh instance (initial is sentinel, sentinel is not `None`,
  `None` is a storable value, `clear()` resets to sentinel); the compute half
  is global-mutating so static-reviewed against the finalizer snapshot block
  (no execution, correctly).
- **Error wording.** Canonical `"X is already registered <label> Y"` shared by
  exactly 2 call sites (reverse-collision `against`, enum collision `as`);
  three adjacent raises keep distinct test-pinned phrasings (primary-flip,
  duplicate-primary, definition-rebind) plus the family-external raises
  (guard, teardown-invalid, decode miss/ambiguity). Rephrase the canonical
  form -> 1 (`_already_registered`). Owner:
  `django_strawberry_framework/registry.py::TypeRegistry._already_registered`;
  stateless pure constructor. Unifying the three inline phrasings would weaken
  grep-from-stack-trace triage — intentional separation, docstring-recorded.
- **Manifest.** Singleton `registry = TypeRegistry()` publishes the store
  (F1) and receives `clear()` (F6); `_subsystem_clears` dict + bus functions
  publish the lifecycle; module docstring "Used by" list matches the
  finalizer loop and converter call sites (projection, verified). No
  `__all__` in this module; the package-root surface family owns the export
  manifest elsewhere.

Relation to `types/finalizer.py` (mechanism-vs-policy: agreed). Registry
owns collected state, the mutation boundary, teardown replay, the phase
vocabulary and the decode lookup. Finalizer owns build policy (phases,
ambiguity + model-label audits, annotation rewrite via converters, interface
injection, `strawberry.type` decoration, bind orchestration, teardown
registration for synthesis artifacts, snapshot compute-plus-compare).
Finalizer reads the store through public getters only — verified: zero
`registry._types` / `_primaries` / `_models` / `_enums` / `_definitions` /
`_pending` / `_type_teardowns` / `_finalized` reads; the only private access
is the sanctioned `_globalid_setting_snapshot` seam (read + write + compare
+ stamp). The one-shot `models_with_multiple_types()` generator is
materialized once per build into `multi_type_models` (comment-pinned at the
call site) and shared by both audits.

Relation to the DRY.md worked example (transport-only: agreed).
`binding_attrs` / `SetLifecycleAttrs` occur zero times in the target
(re-derived by file read). Population declared by
`FilterSet._lifecycle` / `OrderSet._lifecycle`
(`sets_mixins.py::SetLifecycleAttrs`, `::binding_attrs`); body owned by
`utils/inputs.py::clear_generated_input_namespace`; this file is the bus +
phase flag (`register_subsystem_clear` at owner import,
`iter_subsystem_clears()` replay in `clear()`, narrow replay pre-bind in the
finalizer). Four state kinds stay separate as claimed: `TypeRegistry` maps,
per-subclass set binding attrs, declaration ledgers (`before_bind=False`),
input-namespace module ledgers (`before_bind=True`).

Reconciliation vs Worker 1: agree on all ten families, all three rejections,
zero file-local rows, zero-edit verdict and mechanism-vs-policy / transport
readings. Three immaterial prose differences (not defects, not
revision-needed): (a) matrix axis 6 says "9 mutators" but lists 8 names —
my recount is 7 direct guards + 1 indirect (`register_with_definition` via
`register`) = 8 paths, coverage complete either way; (b) matrix axis 5 says
two tests reach into `registry._finalized` as harness bypass — my grep at
`9031cb3d` finds zero `registry._finalized` writes (only `is_finalized()`
reads plus `_subsystem_clears` save/restore harness), oracle independence
unaffected; (c) challenges say "40 asserts" — the probe file carries 48
`check(` tokens (~47 asserts), mine 62 tokens / 51 passed; instrument
strength unaffected.

### Enumeration (member-by-member vs own count)

Instrument: `ast` parse of the working-tree target. Top-level
`len(ast.Module.body)` = **16** (docstring + 7 `ImportFrom` + `If`
`TYPE_CHECKING` + 3 module functions + 2 module state attrs + class +
singleton). Total function nodes = **30**, all `FunctionDef`, zero
`AsyncFunctionDef`. Rule-bearing named members = **33** (3 module functions
`_clear_if_importable` / `register_subsystem_clear` /
`iter_subsystem_clears` + 2 module state attrs `_subsystem_clears` /
`GLOBALID_SETTING_UNSET` + 27 `TypeRegistry` methods + 1 singleton
`registry`). Imports / docstring / `TYPE_CHECKING` block are machinery or
projections, not rules. Matches Worker 1's table row-for-row:

F1: `__init__`, `register`, `unregister`, `get`, `model_for_type`,
`iter_types`, `primary_for`, `types_for`, `models_with_multiple_types`,
`_detach_type_from_model`, singleton publication. F2:
`register_definition`, `register_with_definition`, `get_definition`,
`iter_definitions` (`definition_for_graphql_name` scans it as a consumer).
F3: `add_pending_relation`, `iter_pending_relations`, `discard_pending`.
F4: `register_enum`, `get_enum`. F5: `_check_mutable`, `is_finalized`,
`mark_finalized` (+ `clear()` bypass). F6: `_subsystem_clears`,
`register_subsystem_clear`, `iter_subsystem_clears`, `clear()` replay
(resetting F1/F2/F3/F4/F5/F7/F9 state). F7: `register_type_teardown`,
`_run_type_teardowns` (+ replay in `clear`/`unregister`). F8:
`definition_for_graphql_name`. F9: `GLOBALID_SETTING_UNSET` +
`_globalid_setting_snapshot` + `clear()` reset. F10:
`_already_registered`. `_clear_if_importable` is the `utils/imports.py`
consumer plus the R1 eviction tail; `unregister` carries the R1 tail;
`register_with_definition` carries R2. No member unassigned; no file-local
row.

### Matrix (against the real surface)

1. Cross-flavor: 17 static call sites enumerated by body (7 narrow, 10
   full); declaration-registry siblings (`mutations`/`forms`/`auth` via
   `make_declaration_registry`) already consolidated with disjoint ledgers,
   intentionally separate from `TypeRegistry` (declaration-stage vs
   collected-type-stage; `before_bind=False` survival). R3 stands.
2. Sync/async: zero `async def` (AST-verified), in-memory dict/list/set work
   only, no ORM I/O, no awaits, no threads, no cancellation surface; reads
   colorless, mutation import-time-only. `one-sync-boundary` and
   `sealed-execution-queryset` checked-not-inherited (no row here executes
   ORM or awaits a consumer hook). Trigger for revisit: a registry method
   touching the DB or awaiting.
3. Derived-not-repeated: `get` 3-state, `models_with_multiple_types`
   one-shot, `definition_for_graphql_name` scan and `types_for` snapshot are
   pure per-call derivations (deliberately uncached); the only memoized
   derivation is owned elsewhere (`definition.py::related_target`,
   post-finalize keyed on `is_finalized()`). `_already_registered`
   centralizes 2 of the adjacent collision phrasings; the other inline
   phrasings are intentionally distinct (F10).
4. Round-trip pairs: register/unregister, register+get+model_for_type,
   definition register/get, atomic pair, pending add/discard (identity),
   enum register/get, bus register/iter/replay, mark/is/clear-reset. All
   pinned by `tests/test_registry.py` (2115 lines) oracles; wire
   invisibility rationale (map identity, teardown order, pending identity,
   phase atomicity unobservable over `/graphql/`) stands.
5. Other media: docstrings = projections (verified against bodies; module
   "Used by" matches finalizer loop + converter sites);
   `tests/test_registry.py` = oracles (independent expectations; zero
   `_already_registered` / `binding_attrs` reads; `_subsystem_clears`
   save/restore is harness-only); glossary + specs 018/027/028/031/032/036/
   038/050 = contract sources/projections. No consumer restates a rule.
   Item-scoped diff is empty so no oracle was rewritten.
6. Enforcement by omission: all guarded mutators audited (7 direct +
   `register_with_definition` via `register`); `clear()` bypass is the
   documented test-only escape hatch; `mark_finalized` is the flip.
   `unregister` pre-finalize no-op vs post-finalize raise is documented and
   tested. No gap, no defect.

### Challenges, equivalence, zero-edit justification

Counts confirmed per family above; roles confirmed (definitions vs
consumers vs oracles vs projections as listed). Observable equivalence
(principle 8) via my 51-assert read-only probe plus the existing oracles:
short-circuit order (LIFO teardown, narrow-vs-full replay), exceptions
raised (all collision/guard/miss/ambiguity wordings), state observed
(map/definition/pending/enum/sentinel transitions), the point where
state is observed (fresh-instance isolation — global never touched).
Negative control: workspace copy mutated (`get()` lone-fallback deleted,
copy blob `c7616430` vs shared `9cc8bb55`) -> my probe fails at
`w2-lone-returns-self`; shared-tree blob still `9cc8bb55`; workspace
removed (`dry-ws` empty afterwards). Worker 1's failability proof likewise
verified: workspace removed, shared blob unchanged. No shared-tree pytest
run by me.

Zero-edit validated: `git diff 95f14a08087898f52036058405c5390bc70fa471 --
django_strawberry_framework/registry.py` is empty (0 bytes);
`git status --short` shows only pre-existing concurrent dirt plus untracked
`dry-file-*.md` artifacts. Zero file-local rows is justified, not
family-splitting: each of the ten families earns its row via a distinct
change challenge that moves exactly one definition (F1 fallback / empty-list
invariant / zero re-derivations; F2 atomicity; F3 identity-vs-equality; F4
key; F5 guard message / new-mutator checklist; F6 new phase; F7 order /
retention; F8 decode key; F9 compute-vs-reset-vs-sentinel split three ways;
F10 canonical rephrase). Merging any pair would join distinct contracts,
lifetimes or reasons to change (map vs definition vs ledger vs cache vs gate
vs bus vs per-type teardown vs decode vs snapshot vs wording). No candidate
routes to a holding family beyond the named ten; the reused
`queryset-seed-and-model-read` link stays a consumer link and
`one-sync-boundary` / `sealed-execution-queryset` stay checked-not-inherited.

### Rejections, fingerprints, gates, pending, coupling

- R1 (per-type connection eviction vs whole-cache purge): different
  granularity, mechanism and lifecycle moment (identity-keyed hygiene at
  removal vs owner-callback purge at reset). Prior defer from `dry-0_0_11.md`
  (third direct reach-in) unfired — recount: exactly 1
  `_clear_if_importable` call site and 1 connection literal. Home:
  `registry.py::TypeRegistry.unregister` docstring. Trigger: third direct
  reach-in or a per-type evict export from `connection.py`.
- R2 (rollback vs purge): rollback restores the pre-call primary snapshot
  and touches only state THIS call appended; `unregister` purges
  unconditionally. Shared `_types`/`_models` removal IS shared
  (`_detach_type_from_model`); the remainder needs a restore-vs-delete mode
  flag. Prior defer (third partial-rollback site) unfired — still 1
  definition + 1 caller (`types/base.py:822`). Home:
  `registry.py::TypeRegistry.register_with_definition` docstring.
- R3 (declaration siblings vs `TypeRegistry`): pre-bind per-flavor disjoint
  ledgers via `make_declaration_registry` (mechanics already single-sourced);
  folding into the model-keyed store would couple bind policy to lookup
  policy and erase `before_bind=False` survival. Home:
  `mutations/sets.py::make_declaration_registry` Decision-13 prose. Trigger:
  a declaration ledger needing model-keyed lookup/primary/pending semantics.
  All three carry difference + trigger + durable home; fingerprints below
  keep them fresh.

Freshness re-hashed by me (working tree vs Worker 1 claim): `registry.py`
`9cc8bb55` OK (= HEAD, clean); `utils/querysets.py` `1539b66c` OK;
`permissions.py` `757dce34` OK; `optimizer/walker.py` `9b111ed9` OK;
`optimizer/extension.py` `49667a93` OK; `types/definition.py`
`fa6c4d330` OK (9-char form of the same blob); `types/relay.py`
`52439862` OK; `types/resolvers.py` `f3341e6a` OK; `mutations/sets.py`
`cffa29e5` OK; `types/base.py` `91c58747` OK; `types/relations.py`
`6bd7c63d` OK; `types/finalizer.py` `77fd9a2d` OK; `types/converters.py`
`9ceb34af` OK. `connection.py` working `3c4d5dcb` vs HEAD `93e998f2`
(content-attributed concurrent cursor-guard feature, untouched).

Gates: no consolidation proposed so no consolidation gate with negative
control is owed (family items will owe them). Instrument failability shown
at probe level on both sides (Worker 1 workspace proof verified removed +
unchanged; my workspace proof above). `## Pending execution` correctly
absent — F9's compute half is global-mutating and static-reviewed, the
storage half executed on a fresh instance; nothing deferred needs a command.

Coupling: `None` on all ten findings is correct. The F2 register/rollback
mirror obligation is intra-family co-located code with a docstring flag,
not a cross-finding landing dependency.

### AGENTS.md prose check

No process provenance in production diff (empty); `path::Symbol` citations
throughout with reference-style links and the 10 canonical link groups
present; no `feedback.md` mention; no commit/co-author footer; tests at the
mandated tier are untouched (zero-edit); line-length / formatting moot (no
edits). The one `finalizer:885-900` range in Findings is inside a
`docs/dry/dry-*.md` per-cycle artifact where raw ranges are permitted, and
the symbol (`finalize_django_types`) is named alongside.

No new defects found. Spot-checks that could have been defects all hold:
in-function `implements_relay_node` import matches the documented cycle
(top imports only `exceptions` + `utils.imports`); `iter_pending_relations`
stale-view docstring matches `discard_pending` rebinding; `clear()` order
(teardowns -> own maps -> subsystem callbacks) matches the
teardown-still-resolves pin; poisoned-`sys.modules` tolerance seam matches
HEAD.

## Defects (Worker 2)

None. (Worker 2) No production, test-tier or contract-source defect found
while tracing. The three prose deltas noted above are artifact-wording
precision only and do not change any definition count, owner or trigger.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[converters]: ../../django_strawberry_framework/types/converters.py
[definition]: ../../django_strawberry_framework/types/definition.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[relations]: ../../django_strawberry_framework/types/relations.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[utils-imports]: ../../django_strawberry_framework/utils/imports.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
