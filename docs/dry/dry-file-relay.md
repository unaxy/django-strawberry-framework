# DRY review: `django_strawberry_framework/relay.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

The target owns the consumer-facing root Relay refetch surface: the
`DjangoNodeField` / `DjangoNodesField` factories (bare + typed forms), the
nullable-by-contract dispatch around them, and the write-side typed-id
primitive every mutation flavor consumes. Read in full (627 lines), plus every
connected implementation a sound judgment needs: the encode/decode internals
([types-relay][types-relay]`::decode_global_id`, `::install_is_type_of`,
`::_NODE_TYPE_HINT_ATTR`, the four `resolve_*` defaults), the shared
Relay-target guard
([list-field][list-field]`::_validate_relay_djangotype_target`, also consumed
by [connection][connection]), the subsystem-clear bus
([registry][registry]`::register_subsystem_clear`), the cooperative deadline
([resource-policy][resource-policy]`::check_deadline`), the directives
containment ([directives][directives]`::validated_field_directives`), the coded
error shape ([errors][errors]`::coded_error_extensions`,
`::GLOBALID_INVALID_ERROR_CODE`), the executor fact
([execution-mode][execution-mode]`::async_execution`), the queryset primitives
([querysets][querysets]`::model_for`, `::coerce_field_value_or_none`,
`::reject_async_in_sync_context`, `::_RELAY_ASYNC_RECOURSE`,
`::sync_pipeline_recourse`), the write-pipeline alias reader
([write-tx][write-tx]`::current_write_pipeline`), the write-side consumers
(`::decode_model_global_id` importers in [mutations-resolvers][mutations-resolvers]
and [write-values][write-values], plus the form/serializer decoders that reach
it through the shared pipeline), the public re-export
([testing-relay][testing-relay]`::decode_global_id`), the package-root manifest
([package-init][package-init]), the oracles ([test-relay-node-field][test-relay-node-field],
live rows in [test-library-api][test-library-api]), and the contract sources
([spec-032][spec-032]) with the module docstring as projection (verified
accurate against bodies: Decisions 3/4/5/11, nullable dispatch, the
`GLOBALID_INVALID` boundary, the annotation-shape engine notes).

What the target owns:

- The two root factories `DjangoNodeField` / `DjangoNodesField` (construction
  guards, ledger append, `strawberry.field` return) with their nested
  `_resolve` closures and the nodes `_gather` coroutine.
- The read pipeline shared by both resolvers: `_decode_or_graphql_error`,
  `_node_id_slot`, `_coerce_pk_or_none`, `_check_typed_match`.
- The write-side typed-id contract: `GlobalIDDecode`, `DecodeResult`,
  `_resolve_real_pk`, `decode_model_global_id`.
- The batch positional contract: `_interleave`, `_check_nodes_result`.
- The decode-routing stamp: `_stamp_node_type`, `_await_and_stamp`.
- The thin Relay-target wrapper `_validate_node_target`.
- The finalize-time ledger `_node_fields_declared` /
  `_clear_node_fields_declared` (registered as `relay.node_fields`) and the
  sync-executor recourse sentence `_SYNC_RESOLVER_RECOURSE`.

Relay vs `types/relay.py` split (the axis-1 question this file exists to
answer): `types/relay.py` owns encode/decode grammar, the `resolve_*`
per-type defaults, the hint attribute, and the `is_type_of` consumer. This
file owns the ROOT fields only (spec-031 Decision 11, stated in the module
docstring and verified: zero `resolve_node`/`resolve_nodes` defaults, zero
`definition_for_graphql_name` reads, zero encoder branches here; the decode
primitive is imported, never re-implemented). Consumers compose by name
throughout; no second definition of any owned rule found.

## Verification

### Matrix

1. **Cross-flavor mirroring.** Relay root fields vs connection field vs list
   field vs write flavors, each in local vocabulary. The Relay-target guard is
   single-sited at [list-field][list-field]`::_validate_relay_djangotype_target`
   with 1 definition + 2 call sites ([connection][connection] call, this file's
   `_validate_node_target` call; definition in list-side code) — F8. The typed-id decode is
   single-sited here with four flavor consumers (model/Form/serializer/relation
   paths via `decode_model_global_id`) — F7. The `GLOBALID_INVALID` raises in
   [filters-base][filters-base] (filter-input surface, `FieldError`-adjacent
   shapes) vs `_decode_or_graphql_error` (root `id:`/`ids:` surface,
   `GraphQLError` with no existence oracle) share a code constant, not a
   contract — R1. The `node`/`nodes` twins share helpers, never bodies — R2.
   The deadline, directives, and coded-extensions calls are consumer links to
   their owners, verified single-sited there.
2. **Sync/async twins.** Two colored pairs compared by behavior, not shape.
   (a) `DjangoNodeField._resolve` sync tail vs `DjangoNodesField._gather`
   per-type loop: both dispatch per call (no construction-time commit — the
   deliberate contrast with connection.py's committed split, stated in the
   `_gather` comment and verified: no resolver captured at factory time),
   both coerce-then-dispatch, both stamp; differences are color duties (await
   point, `reject_async_in_sync_context` on sync only, sequential awaits never
   `asyncio.gather(` — probe-verified absent as a call). (b)
   `_stamp_node_type` vs `_await_and_stamp`: the latter is the one-line async
   sibling, sharing the stamp body by call, not by copy. No drift: the pure
   decisions (`_interleave`, `_check_nodes_result`, `_check_typed_match`,
   `_node_id_slot`) are colorless and called from both branches. Third-state
   refusal (`async_execution()` raising under sync-executor-plus-loop) guards
   both entry paths before any ORM work — verified in both resolver sources.
3. **Derived-not-repeated knowledge.** The id slot (`resolve_id_attr()` +
   `model_for` + `_meta.pk`/`get_field`) is derived ONCE in `_node_id_slot`
   and read by both the coercer and the pk-mapper (probe: exactly 2
   `_node_id_slot(resolved_type)` call sites); neither consumer re-derives it
   (no second `resolve_id_attr()` / `_meta.pk` read in either body —
   `_coerce_pk_or_none` takes `field` from the slot, `_resolve_real_pk` takes
   both halves). The `graphql_type_name` pair in `_check_typed_match` reads
   the canonical definition attribute at both sites from the same two objects
   (expected/received), not a re-typed name table. `model_for` is called, never
   re-spelled (`__django_strawberry_definition__.model` occurs zero times
   here).
4. **Round-trip pairs.** Decode/encode: decode lives in `types/relay.py`,
   encode lives there too; this file holds NEITHER half (consumer of decode
   only — verified: no `encode_typename` reference). Coerce-then-filter (read)
   vs coerce-then-map-to-pk (write): two halves of the NodeID contract sharing
   the slot derivation, intentionally different tails (filter on the slot vs
   real-pk lookup) — F7 records the split. Register/clear of the declaration
   ledger: append at both factories, clear via the bus — F6. Stamp/honor: stamp
   here, honor in `install_is_type_of` — F9.
5. **Other media.** [test-relay-node-field][test-relay-node-field] (package
   oracles: dispatch, stamp isolation, custom NodeID, ledger, twins,
   `_check_nodes_result` shape, async colour) and the live rows in
   [test-library-api][test-library-api] (bare/typed/mixed/hidden/malformed/
   per-table counts/async) are independent oracles spelling wire literals,
   never reading owner tables. [spec-032][spec-032] Decisions 3/4/5/11 plus
   Edge cases are the contract source; the module docstring projects them
   (each claim verified against its body during this trace). No consumer
   restates a rule: every call site invokes the owner by name.
6. **Enforcement by omission.** Both factories enforce the full read chain
   (deadline → decode → typed-match → coerce → dispatch → stamp); the batch
   field additionally enforces decode-all-before-any-query and the empty-list
   zero-query short-circuit, while the single field enforces the no-query
   uncoercible early `null`. Each asymmetry is the documented contract
   (Decision 5 shapes differ: single-`null` vs whole-field failure), verified
   against [spec-032][spec-032], not a gap. The write primitive enforces all
   four statuses on every caller (single return type, no optional checks).
   `definition_for_graphql_name` is never called here (zero occurrences,
   probe-verified) — correct: the registry-side decode family stays behind
   `decode_global_id`. No gap: no defect.

### Enumeration

Instrument: `ast` parse of the target. `len(ast.Module.body)` = **42**
(docstring + 21 imports + `__all__` + 2 module state + 13 `FunctionDef` + 1
`AsyncFunctionDef` + 2 `ClassDef` + 1 bus-registration `Expr`). Rule-bearing
named members = **20 rows covering 30 named items** below (every function, class, enum member group,
record field group, module constant, the bus call, and the three nested
closures). Imports / docstring are machinery/projection, not rules. Proof:
`docs/dry/temp-tests/dry-file-relay/probe_w1.py` (`ALL OK`, 93 checks,
execution-verified read-only, no source mutation, no DB, no shared-tree
pytest).

| # | Member | Home |
|---|---|---|
| 1 | `__all__` | Manifest projection (family `package-root-public-surface`, consumer link; pinned by `tests/base/test_init.py`) |
| 2 | `_node_fields_declared` | F6 |
| 3 | `_SYNC_RESOLVER_RECOURSE` | F5 (rejected separation) |
| 4 | `_clear_node_fields_declared` | F6 |
| 5 | `register_subsystem_clear(...)` call | F6 |
| 6 | `_decode_or_graphql_error` | R1 |
| 7 | `_node_id_slot` | L1 |
| 8 | `_coerce_pk_or_none` | F2 (consumer-thin picker) |
| 9 | `_check_typed_match` | L2 |
| 10 | `GlobalIDDecode` + `OK`/`DECODE_FAILED`/`WRONG_MODEL`/`UNCOERCIBLE_PK` | F7 |
| 11 | `DecodeResult` + `status`/`pk`/`resolved_type` | F7 |
| 12 | `_resolve_real_pk` | F7 |
| 13 | `decode_model_global_id` | F7 |
| 14 | `_validate_node_target` | F8 |
| 15 | `_interleave` | L3 |
| 16 | `_check_nodes_result` | L3 |
| 17 | `_stamp_node_type` | F9 |
| 18 | `_await_and_stamp` | F9 |
| 19 | `DjangoNodeField` + nested `_resolve` | R2 |
| 20 | `DjangoNodesField` + nested `_resolve` + `_gather` | R2 |

Consumer-only links (no finding owed; owners keep the rule):
`decode_global_id`, `_NODE_TYPE_HINT_ATTR` (owner [types-relay][types-relay]);
`model_for` ×3 (owner [querysets][querysets], F1);
`coerce_field_value_or_none` ×1 (owner [querysets][querysets], F2);
`reject_async_in_sync_context` ×2 (owner [querysets][querysets], F3);
`validated_field_directives` ×2 with distinct labels (owner
[directives][directives]); `check_deadline` ×2 (owner
[resource-policy][resource-policy]); `coded_error_extensions` +
`GLOBALID_INVALID_ERROR_CODE` (owner [errors][errors]);
`async_execution` ×2 (owner [execution-mode][execution-mode]);
`current_write_pipeline` ×1 (owner [write-tx][write-tx]);
`resolve_node`/`resolve_nodes` classmethods (owner [types-relay][types-relay]
defaults, consumer overrides preserved by construction).

### Challenges

Authoritative definitions counted only; consumers, oracles, projections
listed, not counted. All probes execution-verified read-only unless marked
static-reviewed.

- F1: change the model lookup (read via `registry.get` instead of the
  definition attribute) → 0 definitions here (3 `model_for(resolved_type)`
  consumers call the owner; `__django_strawberry_definition__.model` occurs
  zero times outside the import). Change the raw-manager seed to
  `base_queryset` → 0 definitions move (the raw
  `model_for(...)._default_manager` + `using` composition is the recorded
  separation; [querysets][querysets]`::base_queryset` docstring names it).
- F2: change coercion mechanics (drop `run_validators`, so out-of-range pks
  reach the ORM as `OverflowError`) → 1 definition
  ([querysets][querysets]`::coerce_field_value_or_none`); here 0 (one call,
  field picked locally — the picker-vs-mechanics split the docstring states).
- F3: change disposal (stop closing coroutines) → 1 definition
  (`_dispose_sync_awaitable`); here 0 (2 `reject_async_in_sync_context` calls
  with owner/method/context/recourse spelled per seam).
- F4: change the decode key (`graphql_type_name` → `type_cls.__name__`) → 1
  definition ([registry][registry]`::definition_for_graphql_name`); here 0
  (`definition_for_graphql_name` occurs zero times; decode reached only
  through `decode_global_id`).
- F5: unify the three recourse wordings into `sync_pipeline_recourse` → 1
  definition would move but the contracts differ (refused — R-detail in
  Findings). Change this file's sentence → 1 definition here
  (`_SYNC_RESOLVER_RECOURSE`, 2 use sites).
- F6: add a third lifecycle phase → 1 definition (the bus); here 0 (one
  registration, one clear body). Change ledger semantics (count, not just
  emptiness) → 1 definition here (consumers of emptiness: the finalize-time
  check — listed, not counted).
- F7: add a fifth decode status → 1 definition (`GlobalIDDecode`) + 4
  consumer mappings listed (model/form/serializer/relation decoders map the
  status to their own surfaces; each mapping is a consumer, verified by
  import grep). Apply visibility inside `_resolve_real_pk` → 1 definition
  here (the no-visibility-applied clause with its no-leak reasoning names the
  exact lines to move). Make the helper raising → 1 definition here
  (`\n    raise ` absent from `decode_model_global_id` source,
  probe-verified).
- F8: reorder the base guards → 1 definition
  ([list-field][list-field]`::_validate_djangotype_target`); change the
  Relay-shape predicate → 1 definition (`types/base.py::_is_relay_shaped`,
  static-reviewed); here 0 (label + message + `None` resolver seam only).
- F9: rename the hint attribute → 1 definition
  ([types-relay][types-relay]`::_NODE_TYPE_HINT_ATTR`); here 0 (imported, 1
  `setattr` site). Drop the pre-stamp copy → 1 definition here
  (`_stamp_node_type`).
- L1: change the pk-fallback (map literal `"pk"` through `get_field`) → 1
  definition (`_node_id_slot`); inline the slot read at either consumer → the
  other consumer keeps the old mapping (within-group position of the
  duplication this file item must NOT consolidate — recorded for the family
  item; today count = 1).
- L2: attach an extensions code to the wrong-type error → 1 definition
  (`_check_typed_match`; `extensions=` absent, probe-verified); change
  identity to equality → 1 definition (the `is not` comparison).
- L3: change hole semantics (drop uncoercible instead of `null`-holing) → 1
  definition (`_interleave`); drop the length gate → 1 definition
  (`_check_nodes_result`); relax the override contract (accept shrunk lists)
  → 1 definition (the `ConfigurationError` arm).
- R1: move the filter-surface `GLOBALID_INVALID` raises onto
  `_decode_or_graphql_error` → refused (different error envelopes and
  different no-leak shapes; only the code constant + `coded_error_extensions`
  shape are shared, both owned by [errors][errors]).
- R2: merge the two factories into one parameterized body → refused
  (single-null vs whole-field-failure vs empty-short-circuit vs per-type
  batching are different contracts sharing helpers, not one contract twice).

## Findings

Fingerprint master table (working tree at probe time; `relay.py` equals
`HEAD:` so the target is CLEAN):

| Path | Blob |
|---|---|
| `django_strawberry_framework/relay.py` | `c3c5aea5` (= `HEAD:`) |
| `django_strawberry_framework/types/relay.py` | `52439862` |
| `django_strawberry_framework/list_field.py` | `f357eded` |
| `django_strawberry_framework/registry.py` | `9cc8bb55` |
| `django_strawberry_framework/resource_policy.py` | `647133d2` |
| `django_strawberry_framework/connection.py` | working `3c4d5dcb` vs HEAD `93e998f2` (concurrent cursor-guard dirt, content-attributed, untouched) |
| `django_strawberry_framework/utils/directives.py` | `380786cf` |
| `django_strawberry_framework/utils/errors.py` | `3e25e93b` |
| `django_strawberry_framework/utils/execution_mode.py` | `9805cdaf` |
| `django_strawberry_framework/utils/querysets.py` | `1539b66c` |
| `django_strawberry_framework/utils/write_transaction.py` | `eca9ad4d` |
| `django_strawberry_framework/utils/write_values.py` | `d28587c7` |
| `django_strawberry_framework/exceptions.py` | `e06b0b7f` |
| `django_strawberry_framework/testing/relay.py` | `df0dc72a` |
| `django_strawberry_framework/__init__.py` | `0ef72601` |
| `django_strawberry_framework/filters/base.py` | `ba52351c` |
| `django_strawberry_framework/mutations/resolvers.py` | `3fd1e571` |
| `tests/test_relay_node_field.py` | `2fd9e458` |
| `examples/fakeshop/test_query/test_library_api.py` | `ea74fb5d` |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | `c646c9d1` |

Searched population for every "no second site" claim: full package source
(`django_strawberry_framework/`, 117 `.py` files per the plan
reconciliation), the four test trees, and the specs above. Excluded on body
strength: modules with zero `relay`/`GlobalID`/`resolve_node` vocabulary
(all other subsystems — the grep population is enumerated in the probe, not
by assertion here).

### F1 `queryset-seed-and-model-read` (reuse, consumer)

- **Contract + variation.** `type_cls.__django_strawberry_definition__.model`
  lookup plus the model-keyed vs type-keyed seed split. Varies on
  alias-pinning (`using`) and on seed source (registered-type model vs
  relation-target model).
- **Sites + roles.** Definition:
  [querysets][querysets]`::model_for` (+ `::base_queryset` /
  `::initial_queryset`). Consumers here (3): `_node_id_slot` (model for the
  slot read), `_resolve_real_pk` (model for the raw manager), and
  `decode_model_global_id` (model identity vs `expected_model`). Oracles:
  package + live Relay suites. Projection: the `base_queryset` docstring's
  "`relay.py` deliberately does not use this" clause (verified true:
  `base_queryset`/`initial_queryset` occur zero times here).
- **Challenges.** As listed (model-lookup change → 0 here; seed change → 0
  here).
- **Owner + lifetime.** [querysets][querysets]`::model_for` (existing owner;
  pure derivation per call, no lifetime owed).
- **Migration.** None (file item).
- **Distinct behavior.** The raw-manager composition in `_resolve_real_pk`
  (`model_for(...)._default_manager` + conditional `.using()`) stays
  in-file: it is the recorded intentional separation (caller-owned alias,
  pipeline fallback), not a second seed definition.
- **Behavioral proof.** Probe checks `model-for-sites-3`,
  `no-initial-seed-here`, `real-pk-raw-manager`, `real-pk-no-base-seed`
  (execution-verified, read-only). Oracle bodies static-reviewed.
- **Structural gate.** Existing Relay oracles (wrong result on a bypassed
  lookup fails the typed-decode rows); no new gate owed (no consolidation).
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `utils/querysets.py` `1539b66c`.

### F2 `field-value-coercion` (reuse, consumer)

- **Contract + variation.** Raw literal → field-typed value or `None`
  (`to_python` + `run_validators`, out-of-range rejected pre-query). No
  legitimate variation in mechanics; WHICH field varies per caller.
- **Sites + roles.** Definition:
  [querysets][querysets]`::coerce_field_value_or_none`. Consumer here (1):
  `_coerce_pk_or_none` (picks the slot field via L1, delegates mechanics).
  Sibling consumers: `utils/write_values.py::coerce_relation_pk_or_none`,
  `filters/base.py::_coerce_int_in_members` (listed, not counted).
- **Challenges.** Mechanics change → 1 definition (owner); field-choice
  change → per-caller (here: L1).
- **Owner + lifetime.** [querysets][querysets]`::coerce_field_value_or_none`
  (existing owner; pure, no lifetime).
- **Migration.** None.
- **Distinct behavior.** The `None`-field fall-through (non-concrete NodeID
  attr passes the raw string) stays here: it is the slot contract (L1), not
  coercion mechanics.
- **Behavioral proof.** Probe `coerce-delegates-once`, `coerce-field-from-slot`,
  `coerce-none-passthrough`, `coerce-call-sites-3` (execution-verified).
- **Structural gate.** Existing uncoercible-`null`/hole oracles; no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `utils/querysets.py` `1539b66c`.

### F3 `awaitable-refusal-and-disposal` (reuse, consumer ×2 seams)

- **Contract + variation.** A sync-context awaitable return is disposed and
  refused loudly (`SyncMisuseError`). Varies on owner/method/context/recourse
  wording per seam only.
- **Sites + roles.** Definitions: [querysets][querysets]`::reject_async_in_sync_context`
  (+ `::_dispose_sync_awaitable`). Consumers here (2 seams): single-node
  `resolve_node` tail (`owner=resolved.__name__`, `method="resolve_node"`)
  and batch `resolve_nodes` tail (`method="resolve_nodes"`), both with
  `context="Relay refetch"` and F5 recourse.
- **Challenges.** Disposal change → 1 definition (owner); per-seam wording
  change → the recourse constant (F5).
- **Owner + lifetime.** `utils/querysets.py` (existing owner; no stored
  derivation).
- **Migration.** None.
- **Distinct behavior.** The async-accepting branches (single awaitable ride
  in `_await_and_stamp`, batch `inspect.isawaitable` awaits in `_gather`)
  stay: refusal applies to sync execution only.
- **Behavioral proof.** Probe `nodes-sync-rejects-awaitable`,
  `node-awaitable-branch`, `sync-recourse-use-sites-2`
  (execution-verified). Async-misuse oracles static-reviewed.
- **Structural gate.** Existing sync-misuse oracle rows; no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `utils/querysets.py` `1539b66c`.

### F4 `relay-node-name-decode` (reuse, relation checked, not inherited)

- **Contract + variation.** Unique Relay-Node definition by
  `graphql_type_name`; miss/ambiguity raise. No variation in scan population.
- **Sites + roles.** Definition:
  [registry][registry]`::TypeRegistry.definition_for_graphql_name`.
  Relation here: consumed transitively through
  [types-relay][types-relay]`::decode_global_id` (imported, never
  re-implemented); zero direct `definition_for_graphql_name` reads in this
  file (probe-verified). Direct consumer: `decode_global_id`'s type-name
  branch.
- **Challenges.** Decode-key change → 1 definition (registry); here 0.
- **Owner + lifetime.** `registry.py` (existing owner; pure per-call
  derivation, deliberately uncached).
- **Migration.** None.
- **Distinct behavior.** The model-label branch (`apps.get_model` + F1 `get`)
  stays in `types/relay.py`; only the type-name branch inverts into the
  registry. This file's relation to the family is consumer-of-decode, never
  decoder.
- **Behavioral proof.** Probe `no-definition-for-graphql-here`,
  `decode-owned-elsewhere` (execution-verified).
- **Structural gate.** Existing decode match/Meta.name/ignore/miss/ambiguity
  oracles; no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `registry.py` `9cc8bb55`;
  `types/relay.py` `52439862`.

### F5 `sync-boundary-recourse-wording` (reuse, rejected separation)

- **Contract + variation.** The `SyncMisuseError` recourse sentence naming
  what the consumer should do instead. Varies per boundary kind.
- **Sites + roles.** Indexed definition:
  [querysets][querysets]`::sync_pipeline_recourse` (three write flavors).
  Separate here: `_SYNC_RESOLVER_RECOURSE` (sync-executor recourse: "make the
  consumer override synchronous or run the schema asynchronously", 2 use
  sites). Genuinely different third wording:
  [querysets][querysets]`::_RELAY_ASYNC_RECOURSE` (async IS possible at the
  Relay node defaults). This file references neither the template nor the
  Relay-default wording (both counts zero, probe-verified).
- **Challenges.** Unify all three → refused (see Distinct behavior); rephrase
  this file's sentence → 1 definition here.
- **Owner + lifetime.** This file for its own sentence (stateless constant,
  no lifetime); the template stays with `utils/querysets.py`.
- **Migration.** None.
- **Distinct behavior.** Three wordings, three contracts: sync-executor
  boundary (this file — neither branch can await), async-capable Relay
  defaults (`_RELAY_ASYNC_RECOURSE`), flavor-templated sync pipelines
  (`sync_pipeline_recourse`). Merging them misdirects at least one seam's
  consumer. Recorded here so no cycle re-litigates.
- **Behavioral proof.** Probe `sync-recourse-*` (6 checks,
  execution-verified).
- **Structural gate.** Existing misuse-message oracles match substrings; no
  new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `utils/querysets.py` `1539b66c`.
- **Reconsider trigger.** A fourth sync/async-boundary recourse with the same
  "neither branch can await" contract appearing in this file's seams.

### F6 `subsystem-clear-lifecycle` (reuse, consumer)

- **Contract + variation.** Owner-registered zero-arg teardowns keyed by
  stable logical owner; `before_bind` phase membership. Varies on phase only.
- **Sites + roles.** Definitions: the bus in [registry][registry]
  (`register_subsystem_clear` / `iter_subsystem_clears` /
  `_subsystem_clears`). Consumer here: `register_subsystem_clear(
  _clear_node_fields_declared, owner="relay.node_fields")` + the ledger +
  the clear body (one of 17 owner callbacks; full-clear-only row).
- **Challenges.** New phase → 1 definition (bus); here 0. Ledger-semantics
  change → 1 definition here (only emptiness is load-bearing, per the pinned
  comment — verified: no reader counts entries).
- **Owner + lifetime.** `registry.py` bus (existing owner; entries live
  owner-import → process end).
- **Migration.** None.
- **Distinct behavior.** Declaration-ordering rule (directives contained
  BEFORE the ledger append so a rejected construction leaves no phantom
  entry) stays here: construction discipline, not lifecycle mechanics.
- **Behavioral proof.** Probe `bus-owner-key`, `ledger-empty-load-bearing`,
  `clear-empties-only` (execution-verified, global read-only).
- **Structural gate.** Existing `relay.node_fields` tolerance/clear oracles;
  no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `registry.py` `9cc8bb55`.

### F7 `typed-globalid-decode` (new family, open)

- **Contract + variation.** The write-side typed-`GlobalID` contract:
  shape-decode → model check → pk coerce → real-pk map, non-raising, with a
  four-status vocabulary the caller maps to its own error surface. Varies on
  the caller's error shape only (never on the decode steps).
- **Sites + roles.** Definitions (all here): `GlobalIDDecode` (4 statuses),
  `DecodeResult` (3 fields), `_resolve_real_pk`, `decode_model_global_id`.
  Consumers: [mutations-resolvers][mutations-resolvers] (model path, imports
  both names), [write-values][write-values] (relation decoder, function-local
  import), the form/serializer decoders through the shared write pipeline
  (listed via pipeline, not counted). Oracles:
  [test-relay-node-field][test-relay-node-field] custom-NodeID rows
  (`resolves_custom_node_id_to_real_pk`, `no_row_is_uncoercible`,
  `non_field_node_id`) + flavor-level wrong-model/hidden/uncoercible rows.
  Projections: the `decode_model_global_id` docstring (verified: each step
  named matches its body line).
- **Challenges.** New status → 1 definition (`GlobalIDDecode`) + consumer
  mappings listed; visibility-in-mapper → 1 definition (`_resolve_real_pk`);
  raising contract → 1 definition (`decode_model_global_id`, raiseless
  probe-verified); broad-`except` narrowing → 1 definition (the
  `except Exception` arm — practically `ConfigurationError`-only since decode
  performs no ORM/hook work; spot-check holds, not a defect).
- **Owner + lifetime.** `django_strawberry_framework/relay.py` (narrowest
  cohesive owner every write flavor can import without reversing a
  dependency; flavors already import from here). No stored derivation (pure
  per call; the one query, `_resolve_real_pk`'s `values_list(...).first()`,
  is uncached by contract — visibility stays downstream).
- **Migration.** None (file item).
- **Distinct behavior.** The READ twin (`_coerce_pk_or_none` + `{id_attr:
  value}` filter, no pk mapping) stays separate: readers filter on the slot,
  writers need the real pk (the docstring's slug-vs-pk case). The no-leak
  property holds on both (hidden → pk resolved → downstream hook rejects).
- **Behavioral proof.** Probe `write-4-statuses`, `write-never-raises-graphql`,
  `write-broad-except-decode`, `write-model-identity`, `real-pk-*` (7 checks,
  execution-verified). Oracle bodies static-reviewed.
- **Structural gate.** Existing custom-NodeID + wrong-model + hidden rows
  (fail on a bypassed mapper: raw slug handed to `get(pk=...)` misses);
  negative control reasoned (hand copy of the mapper body passes oracles —
  correct, since the copy IS correct); no `prove_failability.py` run (no
  consolidation proposed → no gate owed).
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; consumers `utils/write_values.py`
  `d28587c7`, `mutations/resolvers.py` `3fd1e571`, `utils/querysets.py`
  `1539b66c` (pipeline reader `3820` listed, not counted).

### F8 `relay-node-target-guard` (new family, open)

- **Contract + variation.** Relay-Node-shaped `DjangoType` target validation
  at factory construction: base guards (class, subclass, registered,
  canonical-by-identity, callable resolver) + the Relay-shape fifth guard.
  Varies on the factory label + Relay error message only.
- **Sites + roles.** Definitions: [list-field][list-field]
  (`_validate_djangotype_target` base, `_validate_relay_djangotype_target`
  Relay fifth guard + `_is_relay_shaped` predicate in `types/base.py`,
  static-reviewed). Consumers: this file's `_validate_node_target` (label +
  message + `None` resolver seam; 2 call sites, one per factory) and
  [connection][connection]`::2303` (its own label + message). Oracles:
  construction-time rejection rows per factory.
- **Challenges.** Guard reorder → 1 definition (base); shape-predicate change
  → 1 definition (`_is_relay_shaped`); here 0 (pass-through verified:
  `None,` + `field=field` in source).
- **Owner + lifetime.** `list_field.py` (existing narrowest owner both
  connection and relay already import; no reversed dependency). Stateless
  construction guard, no lifetime.
- **Migration.** None.
- **Distinct behavior.** Per-factory `relay_error_message` wording stays at
  each caller (grep-from-trace triage); the `None`-resolver seam stays
  (refetch fields have no `resolver=` parameter — the docstring states why).
- **Behavioral proof.** Probe `guard-*` (5 checks, execution-verified).
- **Structural gate.** Existing per-factory rejection oracles; no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `list_field.py` `f357eded`;
  `connection.py` working `3c4d5dcb` (traced incl. hunk for the mirroring
  pass — hunk touches none of the guard sites; never judged).

### F9 `relay-node-type-stamp` (new family, open)

- **Contract + variation.** The decode-routing decision carried into
  abstract-type resolution: stamp the resolved `DjangoType` on the fetched
  instance (best-effort copy-then-set), honored before the isinstance
  fallback. No legitimate variation in attribute or precedence.
- **Sites + roles.** Definitions: halves split by responsibility —
  attribute + honor in [types-relay][types-relay] (`_NODE_TYPE_HINT_ATTR`,
  `install_is_type_of` closure); stamp in this file (`_stamp_node_type`,
  async sibling `_await_and_stamp` sharing the body by call). Consumers: both
  factories' resolvers (4 stamp call sites: single sync/async + batch
  sync/async-loop). Oracles: multi-type `__typename` rows + stamp
  pass-through/uncopyable-object unit rows in
  [test-relay-node-field][test-relay-node-field].
- **Challenges.** Attribute rename → 1 definition (`_NODE_TYPE_HINT_ATTR`);
  precedence flip → 1 definition (`install_is_type_of`); copy-drop → 1
  definition (`_stamp_node_type`).
- **Owner + lifetime.** Split by responsibility (principle 7, dependency
  direction wins): `types/relay.py` owns the attribute + honor (every
  `is_type_of` reader imports from there); this file owns the stamp (only
  the root refetchers route by decode). Lifetime: per-instance hint, never
  stored beyond the response (copy-before-stamp prevents cross-field leak —
  verified in source + oracle).
- **Migration.** None.
- **Distinct behavior.** Unstamped instances (relation/consumer resolvers)
  keep pre-032 isinstance behavior — the documented fallback, not a gap.
- **Behavioral proof.** Probe `stamp-*` (4 checks) + `await-and-stamp-shape`
  (execution-verified). Oracle bodies static-reviewed.
- **Structural gate.** Existing multi-type + isolation oracles; no new gate.
- **Coupling.** None.
- **Freshness.** `relay.py` `c3c5aea5`; `types/relay.py` `52439862`.

### L1 `relay-node-id-slot` (file-local)

- **Contract.** The single statement of which concrete model column backs a
  Relay type's GlobalID id slot: `resolve_id_attr()` names it, literal
  `"pk"` maps to `model._meta.pk`, else `model._meta.get_field`, else `None`
  (non-concrete pass-through).
- **Proving challenge.** Searched the full package for a second
  `resolve_id_attr` + `_meta.pk`/`get_field` composition: the only
  composition site is `_node_id_slot` (both consumers call it; neither body
  re-reads the slot — probe `slot-consumers-2` + absence checks). Nearest
  neighbors differ in contract: `types/relay.py::_resolve_id_attr_default`
  (annotation-scan default with stamped cache — the scan, not the
  model-column mapping) and `_resolve_id_default` (per-row read, not a
  field pick). Change the `"pk"` fallback → 1 definition here. No second
  site after the matrix → file-local.
- **Owner.** `django_strawberry_framework/relay.py::_node_id_slot` (pure per
  call, no lifetime).
- **Behavioral proof.** Probe `slot-*` (5 checks, execution-verified).
- **Freshness.** `relay.py` `c3c5aea5`; `utils/querysets.py` `1539b66c`
  (F1/F2 owners listed as the consumers' downstream, not counted).

### L2 `relay-typed-match-rejection` (file-local)

- **Contract.** Typed-form mismatch rejects with `GraphQLError` naming
  expected/received `graphql_type_name`, identity-compared, deliberately
  code-less (only `GLOBALID_INVALID` carries a code).
- **Proving challenge.** Searched for a second wrong-node-type raise: none —
  the write side reports `WRONG_MODEL` status (F7, different contract:
  non-raising + caller-mapped), the filter side reports relation
  `FieldError`s (different envelope). `extensions=` absent from the body
  (probe-verified); identity `is not` verified. One definition, two in-file
  call sites → file-local.
- **Owner.** `django_strawberry_framework/relay.py::_check_typed_match`
  (stateless, no lifetime).
- **Behavioral proof.** Probe `typed-*` (4 checks, execution-verified).
- **Freshness.** `relay.py` `c3c5aea5`.

### L3 `relay-batch-reassembly` (file-local)

- **Contract.** Per-type `resolve_nodes` results reassemble into input order
  with `null` holes: `positions` reserves uncoercible holes, `_order_nodes`
  (owner: types/relay defaults) yields per-type 1:1 lists, `_check_nodes_result`
  gates length (materializing generators first), `_interleave` indexes by
  within-group position.
- **Proving challenge.** Searched for a second positional-reassembly body:
  none — connection pagination assembles edges/pageInfo under cursor
  contracts (different rule, different shapes); list-field windowing slices
  (different rule). Both helpers called from exactly the two in-file branches
  (sync + `_gather`; probe `interleave-shared`, `nodes-result-call-sites-2`).
  Change hole semantics / drop the gate / relax the override contract → 1
  definition each, both here. No second site → file-local.
- **Owner.** `django_strawberry_framework/relay.py::_interleave` +
  `::_check_nodes_result` (pure, no lifetime; the 1:1 contract documented on
  `DjangoNodesField`).
- **Behavioral proof.** Probe `interleave-*`, `nodes-result-*` (7 checks,
  execution-verified) + existing shrunk/generator/wrong-length oracle rows
  (static-reviewed).
- **Freshness.** `relay.py` `c3c5aea5`; `types/relay.py` `52439862`
  (`_order_nodes` listed as upstream, not counted).

### R1 `root-vs-filter GLOBALID_INVALID raises` (rejection)

- **Considered shared form.** One `ConfigurationError → coded GraphQLError`
  helper behind both this file's `_decode_or_graphql_error` and the three
  `GLOBALID_INVALID` raises in [filters-base][filters-base].
- **Difference.** Different envelopes and different no-leak shapes: root
  raises bare `GraphQLError("Invalid GlobalID: ...")` on a whole `id:`/`ids:`
  argument before any query (nothing leaks row existence); filter raises are
  field-keyed (`FieldError`-adjacent / filter-envelope) inside predicate
  construction with per-column coercion context. Only the code constant +
  `coded_error_extensions` shape are shared — both already owned by
  [errors][errors] and consumed by name on both sides (probe:
  `GLOBALID_INVALID_ERROR_CODE` occurs exactly twice here: import + the one
  raise).
- **Trigger.** A third root-argument decode site, or the filter surface
  adopting the whole-argument pre-query failure shape.
- **Home.** `django_strawberry_framework/relay.py::_decode_or_graphql_error`
  (docstring already states the FilterSet precedent + the narrow scope;
  verified accurate).
- **Freshness.** `relay.py` `c3c5aea5`; `filters/base.py` `ba52351c`;
  `utils/errors.py` `3e25e93b`.

### R2 `single-vs-batch factory bodies` (rejection)

- **Considered shared form.** One parameterized resolver behind
  `DjangoNodeField._resolve` and `DjangoNodesField._resolve` (+ `_gather`).
- **Difference.** Different wire contracts sharing helpers, not one contract
  twice: nullable-single (`null` for hidden/missing/uncoercible, one
  `resolve_node` call, coroutine-or-value return) vs ordered batch (decode-all-
  before-any-query whole-field failure, empty-list zero-query short-circuit,
  per-type `resolve_nodes` grouping with duplicates preserved, one gathering
  coroutine with sequential awaits, positional reassembly). The shared parts
  are ALREADY shared (`_decode_or_graphql_error`, `_check_typed_match`,
  `_coerce_pk_or_none`, `_check_nodes_result`, `_interleave`,
  `_stamp_node_type`, `check_deadline`, `validated_field_directives` —
  8 helpers, each called from both sides by name). What remains inline per
  side IS the contract difference; a mode flag would obscure both.
- **Trigger.** A third root refetch arity (e.g. keyset-single) duplicating
  the decode→match→coerce→dispatch→stamp spine with a new tail.
- **Home.** `django_strawberry_framework/relay.py` module docstring (bare vs
  typed + nullable-by-contract + batch-failure-shape prose; verified against
  both bodies).
- **Freshness.** `relay.py` `c3c5aea5`.

## Defects

No new defects. Spot-checks that could have been defects all hold: the
`except Exception` in `decode_model_global_id` is practically
`ConfigurationError`-only (decode performs no ORM work and invokes no
consumer hook, so no `SyncMisuseError` can escape the try — the narrow
`except ConfigurationError` in `_decode_or_graphql_error` and the broad one
here agree on every reachable input); `_interleave` is total over the
`positions` alphabet (every group key is filled in both branches; the
all-holes batch yields `per_type = {}` indexed zero times); the third-state
`async_execution()` refusal guards BOTH entry paths before any ORM work
(single `if not async_execution()` + batch `if async_execution():`,
probe-verified); the directives-before-ledger ordering leaves no phantom
entry on rejected construction (both factories, source-verified); the
typed-form annotation mismatch fails loud at runtime per the documented
contract (not silently). No `## Owned changes` coupling (zero edits).

## Pending execution

None. All behavioral proofs execution-verified read-only in the shared tree
(probe `ALL OK`, 93 checks; no source mutation, no DB opened, no registry
writes — global read-only). No consolidation proposed, so no consolidation
gate with negative control is owed. DB-backed cells inapplicable by
construction: the probes touch no queryset, alias, or dialect decision (the
one query in the target, `_resolve_real_pk`'s pk lookup, was verified by
source read only and never executed). No shared-tree pytest run, per the
item fence.

## Judgment

Zero-edit file item: matrix discharged against the real surface (relay vs
`types/relay.py` split stated with the zero-counts that prove it; twins
compared by behavior; third-state refusal on both paths), 28/28 enumeration
rows assigned (6 reused families as consumer/checked/rejected links, 3 new
families for Worker 0, 3 file-local rows with proving challenges, 2
rejections with differences + triggers + homes). Every rule has exactly one
authoritative definition; all cross-module reads compose by name. No
production edit, no test change, no defect.

## Implementation (Worker 1)

No tracked changes. Item-scoped diff state: `git diff
dcce998ac8867a4c14ca46a17676bf182c3d18ae --
django_strawberry_framework/relay.py` is empty (probe `item-diff-empty`
check, re-measured after all reads) — the target blob `c3c5aea5` equals
`HEAD:`, so the target is CLEAN and no hunk attribution was owed. The
`## Owned changes` ledger paths (`optimizer/walker.py`,
`test_products_visibility_api.py`, `test_multi_db.py`) were never touched.
Concurrent dirt left untouched: `connection.py` working hunk (`3c4d5dcb` vs
HEAD `93e998f2`), `tests/test_connection.py`, staged
`tests/utils/test_querysets.py` (+31),
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` (plan file read,
never edited). No commit per standing rule. No ruff run owed (no tracked
`.py` edits; artifact is `.md` only; the probe is untracked scratch).
Scratch created (not tracked changes): this artifact
`docs/dry/dry-file-relay.md` and the read-only probe
`docs/dry/temp-tests/dry-file-relay/probe_w1.py` (`ALL OK`, 93 checks; no
source mutation, no DB, no shared-tree pytest; Worker 0 removes the probe
dir by explicit path after `verified`).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Read order kept: AGENTS.md, DRY.md,
worker-2.md, the plan item (File `relay.py`), the full target (627
lines), the item-scoped diff (re-measured empty myself, see below),
connected sites ( honor/decode in [types-relay][types-relay], the guard
in [list-field][list-field], the bus in [registry][registry], the
queryset primitives plus the `base_queryset` separation clause in
[querysets][querysets], the third-state refusal in
[execution-mode][execution-mode], the consumers in
[mutations-resolvers][mutations-resolvers] / [write-values][write-values],
the filter raises in [filters-base][filters-base], the guard call site
in [connection][connection], both oracle files, [spec-032][spec-032]
Decisions 3/4/5/11), the probe (ran myself:
`uv run python docs/dry/temp-tests/dry-file-relay/probe_w1.py` →
`ALL OK 93 checks`). The trace below re-derives every count from
source instruments (AST + `str.count`, values quoted); only then did
it reconcile against `## Findings`.

### Own trace (rule, sites, count, owner I would choose)

- T1 model read + raw-manager separation: 3 `model_for(resolved_type)`
  consumers here (slot read, raw manager, model-identity check); 0
  direct `__django_strawberry_definition__.model`; 0 `base_queryset` /
  `initial_queryset`. The `_default_manager` + conditional `.using()`
  composition appears once (`_resolve_real_pk`) and is the recorded
  separation (`base_queryset` docstring: "`relay.py` deliberately does
  not use this" — verified verbatim). Count here: 0 definitions.
  Owner: [querysets][querysets]`::model_for`.
- T2 pk coercion: 1 `coerce_field_value_or_none(field, node_id)` call;
  field picked from `_node_id_slot(resolved_type)[1]`; `None`-field
  fall-through returns the raw string. Count here: 0 mechanics, 1
  local field-choice. Owner: [querysets][querysets]
  `::coerce_field_value_or_none`.
- T3 refusal seams: 2 `reject_async_in_sync_context` calls
  (`resolve_node` tail, `resolve_nodes` tail), each spelling
  owner/method/context/recourse; async-accepting branches
  (`isawaitable` rides) are separate color duties. Count here: 0.
  Owner: [querysets][querysets].
- T4 node decode relation: `decode_global_id` imported, and its module
  verified as `types.relay`; 0 `definition_for_graphql_name` here; 0
  `encode_typename` here; 0 `def _resolve_node(s)_default` here (4
  prose mentions only). Relation = transitive consumer of decode,
  never a decoder. Count here: 0. Owner:
  [registry][registry]`::TypeRegistry.definition_for_graphql_name`
  via [types-relay][types-relay]`::decode_global_id`.
- T5 recourse wordings: 3 wordings, 3 contracts — this file's
  `_SYNC_RESOLVER_RECOURSE` (mentions `execute_sync`, names both
  factories, 2 `recourse=` use sites) vs
  [querysets][querysets]`::_RELAY_ASYNC_RECOURSE` (async IS possible)
  vs the `sync_pipeline_recourse` template (3 write flavors); this
  file references neither of the other two (both counts 0). Owner of
  the local sentence: this file (stateless constant).
- T6 bus registration: 2 `register_subsystem_clear` occurrences
  (import + 1 call with `owner="relay.node_fields"`); ledger list +
  clear-only body; both factories append distinct labels (1 each).
  Count here: 0 lifecycle mechanics. Owner: [registry][registry] bus.
- T7 GlobalID decode contract: `GlobalIDDecode` (4 statuses) +
  `DecodeResult` (3 fields) + `_resolve_real_pk` +
  `decode_model_global_id`, all defined here; body contains no
  `raise` (verified); `except Exception` present. Consumers:
  [mutations-resolvers][mutations-resolvers] (import + call),
  [write-values][write-values] (function-local import + call), form /
  serializer decoders via the shared write pipeline (1 mention each;
  reached through the shared relation path, listed not counted).
  Owner: this file (narrowest cohesive owner every write flavor can
  import without reversing a dependency).
- T8 node-target guard: `_validate_node_target` delegates to
  [list-field][list-field]`::_validate_relay_djangotype_target` with
  `None` + `field=field` + per-factory message; 2 call sites here;
  [connection][connection] calls the same owner once; the owner
  module does not self-call (0). Count here: 0 guard logic. Owner:
  [list-field][list-field].
- T9 type stamp/honor split: `_NODE_TYPE_HINT_ATTR` imported (object
  identity with [types-relay][types-relay] verified `is`); honor
  branch inside `install_is_type_of` (hint-first, isinstance
  fallback); stamp here (`_stamp_node_type` + `_await_and_stamp`
  calling it by name); 5 `_stamp_node_type(` occurrences = def + 4
  call sites (single sync, await-sibling, batch sync loop, gather
  loop). Owner split by responsibility (dependency direction wins):
  attribute + honor in [types-relay][types-relay], stamp here.
- T10 id-slot derivation: 1 composition site (`resolve_id_attr()` +
  `model_for` + `_meta.pk` / `get_field` + `FieldDoesNotExist` →
  `None`); exactly 2 `_node_id_slot(resolved_type)` consumers;
  neither body re-reads the slot. Nearest neighbors differ in
  contract (annotation-scan default; per-row read). Count: 1 here.
  Owner: this file `::_node_id_slot`.
- T11 typed-match: `resolved is not target_type`; `graphql_type_name`
  ×2; no `extensions=`; 2 in-file call sites; no second wrong-type
  raise in the package (write side = `WRONG_MODEL` status, filter
  side = `FieldError` envelopes — different contracts). Count: 1.
  Owner: this file `::_check_typed_match`.
- T12 batch interleave: `_interleave(positions, per_type)` from
  exactly 2 branches; `_check_nodes_result(resolved_type, result,
  pks)` from exactly 2 sites (materialize-then-length-gate →
  `ConfigurationError`); connection pagination (cursor/pageInfo)
  and list windowing (slices) differ in contract — no second
  positional-reassembly body. Count: 1 each. Owner: this file.
- T13 root-vs-filter raises: root code-const occurrences = 2 (import
  + 1 raise); [filters-base][filters-base] occurrences = 5 (import +
  refs around 3 raise sites). Different envelopes (whole-argument
  pre-query `GraphQLError` vs field-keyed filter shapes) and
  different no-leak shapes; shared const + extensions shape owned by
  [errors][errors]. Refuse the merge.
- T14 single-vs-batch factories: nullable-single (one `resolve_node`
  call, coroutine-or-value return, uncoercible → `null` no-query)
  vs ordered batch (decode-all-before-any-query whole-field failure,
  empty-list zero-query short-circuit, per-type grouping with
  duplicates preserved, one gathering coroutine with sequential
  awaits — `asyncio.gather(` count 0, `asyncio` only in a comment —
  positional reassembly). 8 helpers already shared by name; the
  inline remainder IS the contract difference. Refuse the merge.

### Reconciliation vs W1 (per row)

F1 agree (consumer ×3; separation clause verified verbatim). F2
agree (consumer-thin picker; mechanics at owner). F3 agree (2 seams;
async branches correctly excluded). F4 agree (transitive relation,
checked not inherited; zero-counts re-measured). F5 agree (rejected
separation; 3 wordings / 3 contracts; trigger adequate). F6 agree
(consumer; emptiness-load-bearing verified; ordering rule stays
here). F7 agree — endorse `typed-globalid-decode` as a NEW open
family: one non-raising definition with 4 statuses and 4+ consumer
mappings, a genuine error-shape variation axis, owned at the
narrowest importable site; correctly NOT consolidated inside this
file item. F8 agree — endorse `relay-node-target-guard` as NEW open:
1 definition + 2 call sites here and 1 in connection, owner at
`list_field.py` (both importers, no reversed dependency); the
per-factory label/message + `None` seam correctly stay at callers.
F9 agree — endorse `relay-node-type-stamp` as NEW open: split
ownership is the principle-7 answer (honor readers import from
types/relay; only root refetchers route by decode); attribute /
precedence / copy challenges each hit exactly one definition. L1/L2/
L3 agree as file-local (each count = 1, second-site searches
reproduced: slot 2-consumers-0-rederivations; typed-match no second
raise; interleave/check 2-sites-each with differing neighbors). R1/
R2 agree as rejections (differences + triggers + homes all present
and accurate). No over-splitting: F7/F9/L1/L2/L3 share a file but
have disjoint consumers, change axes, and owners — one family would
re-couple independent reasons to change.

### Enumeration (member by member, my count)

Instrument: `ast` parse, `len(ast.Module.body)` = 42, confirmed.
Composition (mine): 1 docstring + 21 imports (17 `ImportFrom` + 4
`Import`) + 1 `__all__` + 2 module state (ledger `AnnAssign`,
recourse `Assign`) + 13 `FunctionDef` + 1 `AsyncFunctionDef` + 2
`ClassDef` + 1 bus-registration `Expr` = 42. Correction: the artifact
prose says "14 `FunctionDef`" — the tree has 13 (the probe's
`top-def-names` lists the correct 16 defs and `module-body-42`
passes, so nothing is orphaned; the parenthetical then sums to 43,
not 42). Rows 1–20 assign every member: 1 manifest→package-root
family link; 2/4/5 ledger+clear+bus→F6; 3 recourse→F5; 6 decode→R1;
7 slot→L1; 8 coerce→F2; 9 typed-match→L2; 10 enum+4 members→F7; 11
record+3 fields→F7; 12/13 pk-mapper+typed decode→F7; 14 guard→F8;
15/16 interleave+length-gate→L3; 17/18 stamp+sibling→F9; 19 single
factory + nested `_resolve`→R2; 20 batch factory + nested `_resolve`
+ nested `_gather`→R2. That is 20 assignment rows covering 30 named
items — the artifact's "28 rows" label does not reproduce under any
natural counting (20 rows / 30 items by mine); coverage is intact
regardless. Guard-site wording correction: 1 definition + 2 call
sites (relay, connection), not "three call sites". All three are
label-only; Worker 0 should correct them editorially without
reopening. Consumer-only links re-verified with counts: `model_for`
×3, `coerce_field_value_or_none` ×1, `reject_async_in_sync_context`
×2, `validated_field_directives` ×2 with distinct labels,
`check_deadline` ×2, code const ×2 (import + 1 raise),
`async_execution` ×2, `current_write_pipeline` ×1, `resolve_node(s)`
classmethods owned by types-relay defaults.

### Matrix judgment (against the real surface)

1. Cross-flavor: guard single-sited (1 def, 2 calls); typed decode
  single-sited here with flavor consumers via import + shared
  pipeline; `GLOBALID_INVALID` shares const+shape only (owner
  [errors][errors]); node/nodes twins share 8 helpers by name.
  Discharged. 2. Sync/async: colored pairs compared by behavior —
  per-call dispatch with no construction-time commit (verified: no
  resolver captured at factory time), `reject_*` on sync only,
  sequential awaits, pure decisions (`_interleave`,
  `_check_nodes_result`, `_check_typed_match`, `_node_id_slot`)
  colorless and shared; third-state refusal guards both entries
  (it lives in `async_execution()` itself, called pre-ORM on both
  paths — verified in source). Discharged. 3. Derived knowledge:
  slot derived once, read twice, never re-derived; type names read
  from the canonical definition attribute; `model_for` called, never
  re-spelled. Discharged. 4. Round-trip: encode+decode both live in
  types/relay, neither half here (0 `encode_typename`);
  read-filter vs write-map tails intentionally differ (F7 records
  the split); ledger append/clear and stamp/honor are split pairs
  with named halves. Discharged. 5. Other media: package oracle
  (867 lines) spells wire literals (`Invalid GlobalID`,
  `GLOBALID_INVALID` ×2, `SyncMisuseError` ×8, `__typename` ×18,
  custom-NodeID rows) and reads no owner table
  (`_node_id_slot`/`coerce_field_value_or_none` absent); live oracle
  rows (`node(` ×21, `nodes(` ×10, `Wrong node` ×2) likewise; spec
  Decisions 3/4/5/11 exist with matching subjects; module docstring
  claims spot-verified against bodies. No oracle rewritten
  (test-tree status: only concurrent connection/querysets test dirt,
  untouched). Discharged. 6. Omission: asymmetries (batch-only
  decode-all-first + empty short-circuit; single-only no-query
  `null`; write-side 4 statuses with no optional checks) verified
  against [spec-032][spec-032], not gaps; `definition_for_graphql_name`
  correctly absent here. No defect.

### Counts, equivalence, zero-edit, gates

Definition counts confirmed per T1–T14; roles confirmed (6 reused
as consumer/relation/rejected links, 3 new open, 3 file-local, 2
rejected). Equivalence (principle 8): zero production edits, so no
observable behavior changes; all probes read-only (no DB, no
registry writes, no source mutation); DB-backed cells inapplicable
by construction (probes touch no queryset, alias, or dialect; the
one query, `_resolve_real_pk`'s pk lookup, verified by source read
only). Item-scoped diff re-measured empty by me (`git diff
dcce998ac8867a4c14ca46a17676bf182c3d18ae --
django_strawberry_framework/relay.py` → empty); target blob
`c3c5aea5` equals `HEAD:` (clean); `git status --short` shows
`relay.py` unmodified. Rejections R1/R2 (+ F5 separation) each
carry concrete difference + trigger + home. Fingerprints re-hashed
by me — all 20 match the master table (`types/relay.py`
`52439862`, `list_field.py` `f357eded`, `registry.py` `9cc8bb55`,
`resource_policy.py` `647133d2`, `directives.py` `380786cf`,
`errors.py` `3e25e93b`, `execution_mode.py` `9805cdaf`,
`querysets.py` `1539b66c`, `write_transaction.py` `eca9ad4d`,
`write_values.py` `d28587c7`, `exceptions.py` `e06b0b7f`,
`testing/relay.py` `df0dc72a`, `__init__.py` `0ef72601`,
`filters/base.py` `ba52351c`, `mutations/resolvers.py` `3fd1e571`,
`test_relay_node_field.py` `2fd9e458`, `test_library_api.py`
`ea74fb5d`, `spec-032` `c646c9d1`; `connection.py` working
`3c4d5dcb` vs HEAD `93e998f2` is the content-attributed concurrent
cursor-guard hunk, guard sites untouched). No consolidation → no
new gate owed; existing oracles per finding listed; negative control
reasoned (a hand copy passes because it is correct) — acceptable
with no gate owed. `## Pending execution`: none, correct. Coupling:
none, correct.

### AGENTS.md prose check

Artifact is `.md` only plus the untracked read-only probe: no ruff
run owed (a repo-wide `--fix` would risk the concurrent dirt;
same standing rule W1 applied). Citations use `path::Symbol` via
the reference-style link block; no process provenance; no test-tier
change (correct for zero-edit); concurrent dirt preserved; no
commit. This section sits before `<!-- LINK DEFINITIONS -->` and
adds no bare links, so the scaffold footer stays intact.

### Defects (Worker 2)

None in package source. Re-verified spot-checks hold: the broad
`except Exception` is practically `ConfigurationError`-only
(decode performs no ORM work and invokes no consumer hook, so the
narrow and broad handlers agree on every reachable input);
`_interleave` is total over the `positions` alphabet (every group
key filled in both branches; all-holes batch indexes nothing);
third-state refusal guards both entries; directives-before-ledger
ordering leaves no phantom entry in either factory; the typed-form
annotation mismatch fails loud at runtime per contract. The only
corrections owed are the three artifact label slips above
(13 `FunctionDef`; 20 rows / 30 items; guard 1 def + 2 calls) —
prose, not package defects, and not a reopen.

### Judgment (Worker 2)

Zero-edit file item verified: matrix discharged against the real
surface (relay vs types/relay split proved with zero-counts; twins
compared by behavior; third-state refusal on both paths), every
member assigned (6 reused, 3 new open, 3 file-local, 2 rejected),
every rule single-owned with cross-module reads composing by name.
No production edit, no test change, no defect, no pending
execution. The 3 new families are justified (rulings above) and go
to Worker 0 as open family items. `Status: verified`.

## Scoped re-trace (run 8) — Worker 1

Scoped run: `0.0.15 2026-09-30-8` (queue s4). HEAD `83998e08` at
start, verified unmoved at finish (`git rev-parse HEAD` both
times). Prior text above is prior evidence only and stands
untouched; this section appends. Zero production edits; a file
item owes none. Every claim below is traced at HEAD bytes unless
marked worktree or pre-merge; the worktree is read only for hunk
attribution. Two read-only probes, `/tmp`-only, no Django
import, no DB, no source mutation, no workspace, no pytest:
`/tmp/relay_r8_probe.py` (115 checks) + `/tmp/relay_r8_conn.py`
(40 checks) — 155/155 `ALL OK`. Five first-draft expectations
failed on probe precision (docstrings tripping body-only
checks, `__slots__` tripping a `slots` token, import-vs-call
count), all corrected in the instrument, none a finding.

### Scope of the delta (drift base → HEAD → worktree → pre-merge)

Drift base `0c0537e2` → HEAD `83998e08` on the target is 4
commits. One is behavior-bearing, re-read in full:

- `2935e0e4` (relay hunk 60+/-, plus the types/relay half):
  the node/nodes resolve seams now take the decoded `node_id`
  STRING. `DjangoNodeField._resolve` gates
  (`if _coerce_pk_or_none(resolved, node_id) is None: return
  None`, value discarded) and hands
  `resolved.resolve_node(node_id, ...)` the string;
  `DjangoNodesField._resolve` gates per id into `None` holes
  and groups `list[str]` per type for
  `resolve_nodes(node_ids=node_ids)`. The types/relay.py
  defaults coerce the string themselves through new
  [types-relay][types-relay]`::_node_value_or_none` /
  `::_node_values` helpers that COMPOSE
  `::_coerce_pk_or_none` BY CALL (in-function import for the
  load cycle), plus `_raise_if_required` and `None`-key arms
  in `_order_nodes`; `_coerce_node_ids` is deleted. Commit
  message + 3 new oracles + 1 helper in
  [test-relay-node-field][test-relay-node-field] (string-seam
  pin, `007`-spelling fix, `abc`-uncoercible fix).

The other 3 commits are proved non-behavioral on this target
by full-diff read (every hunk): `999a1aab`, `b20277fe`,
`fef11e64` are annotations (`Any` → narrow types,
`Awaitable`/`Iterable`/`_NodeT`, `ModelField`), the
`TYPE_CHECKING` guard, the `collections.abc` import widening,
two `cast()` wraps (identity at runtime), one bare local
annotation (`manager: ...`, no runtime effect), and one
parameter rename (`pks` → `node_ids`, both call sites
positional). Mechanical screen (base → HEAD per-symbol,
annotations + docstrings stripped): 16/16 def/class names
present both sides, 0 added, 0 removed; code-differing
exactly the two factories (the 2935 reshape) plus three
hand-adjudicated no-ops (`_check_typed_match` cast,
`_resolve_real_pk` bare annotation, `_check_nodes_result`
rename + cast). `b63df99d` (id-filter split) touches
[types-relay][types-relay] only: the two new filters take
already-coerced values, no second coercion definition, no
rule ownership moves on this target.

HEAD → worktree is 19 `-U0` hunks, 189+/63-, worktree blob
`fd88aafa` (781 lines vs HEAD 655). Hunk attribution by
content against `git show HEAD:` (full diff read): ONE owned
hunk, the ledger's run-2 orphan `typed-globalid-decode`
trigger docstring — 4 additive prose lines closing
`::decode_model_global_id`'s docstring, AST-verified
docstring-contained and code-inert, byte-identical
9aaaad5d↔worktree (fresh `diff`, zero lines), absent at HEAD
(the merge took main's side, which lacks the orphan). The
other 18 hunks are concurrent-external and untouched: the
`utils/truth.py` migration (1 import + `truth.*` renders),
the lazy-proxy unwrap in `::_stamp_node_type`, the
slot-threading (`slot=`/`slots` memo) across the coercer,
mapper, batch loop and write decode, the new
`::_decode_and_coerce` / `::_resolve_real_pks_batched` split
halves, the `isawaitable`-gated refusal calls, prose
rewordings (directives, deadline, edge-case cites), and the
`decode_model_global_id` docstring + body reshape AROUND the
owned paragraph (the paragraph's hunk is mixed: 4 owned
prose lines inside concurrent prose + code). The worktree
`_decode_and_coerce` equals its 9aaaad5d bytes modulo
HEAD-side typing annotations only. Nothing judged from
worktree bytes; nothing edited, reverted, or tidied.

Pre-merge bytes `9aaaad5d` (read-only evidence via `git
show`, never applied): target blob
`f5760b45f161cccf9dce6d2c84b45311b5b03291`, 749 lines —
pre-typing bytes (0 `TYPE_CHECKING`/`_NodeT`/
`_RelayDjangoType` hits) carrying the tree's behavior dirt
(16 `truth.`/`_decode_and_coerce`/`_resolve_real_pks_batched`/`slot=`
hits) plus the owned trigger paragraph. The merge took
main's 2935 reshape + typing under the tree's behavior
shapes; the owned paragraph rode the tree side only.

### Enumeration (fresh instrument at HEAD bytes)

Instrument: `ast.parse` over `git show HEAD:` bytes: **43
top-level statements** — 1 module docstring, 20 imports (17
`ImportFrom` + 3 `Import`), 1 `TYPE_CHECKING` guard, 1
`Assign` (`_NodeT`), 1 `Assign` (`__all__`), 1 `AnnAssign`
(ledger) + 1 `Assign` (recourse), 13 `FunctionDef`, 1
`AsyncFunctionDef`, 2 `ClassDef`, 1 bus-registration `Expr`.
Delta vs run-7's 42 is exactly +1 net, all typing-drift: +1
guard, +1 `_NodeT`, −1 import (`django.db models` moved
under the guard; `Awaitable`/`Iterable`/`TYPE_CHECKING`/
`TypeVar`/`cast` join existing statements). The 16 def/class
names and their order are unchanged; 0 added, 0 removed, 0
renamed. Nested: `_resolve` ×2 (one per factory) +
`_gather` ×1 (inside the batch `_resolve`); `GlobalIDDecode`
4 members, `DecodeResult` 3 fields — all re-derived.

Every member lands in a home; every challenge below ends in
one:

| Members | Home |
|---|---|
| 0 docstring | projection (F7 cite D1; rest verified) |
| 1–20 imports, 21 guard | machinery / consumer links (F1–F4, F6, R1) |
| 22 `_NodeT` | typing machinery, no rule |
| 23 `__all__` | manifest projection (F-record, unchanged) |
| 24–25 ledger + recourse | F6 / F5 |
| 26–27 clear + bus call | F6 |
| 28 decode-or-error | R1 |
| 29 slot | L1 (REVISED note) |
| 30 coercer | F2 (REVISED: gate role) |
| 31 typed-match | L2 |
| 32–33 enum + record | F7 (REVISED census) |
| 34–35 mapper + typed decode | F7 |
| 36 guard wrapper | F8 |
| 37–38 interleave + length gate | L3 (REVISED note) |
| 39–40 stamp + async sibling | F9 |
| 41 single factory + `_resolve` | R2 (REVISED prose) |
| 42 batch factory + `_resolve` + `_gather` | R2 (REVISED prose) |

No new family is named: the coercion flow stays
sole-picker here with mechanics at its owner, and the three
run-7-named families (`typed-globalid-decode`,
`relay-node-target-guard`, `relay-node-type-stamp`) stand
open per the run-8 staleness record (rules + owners
untouched). One consumer-membership nomination for Worker-0
to route (not a new row): F2 `field-value-coercion` gains a
composing consumer, [types-relay][types-relay]`::_node_value_or_none`
→ `::_coerce_pk_or_none` (home item s14 / the F2 family
item, which owns that file's rows).

### Matrix re-discharge (at HEAD bytes)

**1. Cross-flavor policy mirroring — CONFIRM.** Guard
single-sited (1 definition + 2 calls here + 1 in
[connection][connection], re-derived); typed decode
single-sited here with flavor consumers via import +
per-element compose (F7 revise); `GLOBALID_INVALID` shares
const + shape only (root 2 hits, filter 4+ hits around 3
raise sites, owner [errors][errors]); node/nodes twins
share 6 bilateral helpers by name (R2 revise); deadline,
directives, coded-extensions, pipeline-reader calls are
consumer links to their owners. `2935e0e4`'s stat touches
no flavor file besides this target + types/relay + the
oracle — `connection.py`'s row-passing `resolve_node`
shape seen, untouched by the drift, not judged here.

**2. Sync/async twins — REVISE (shape re-derived, verdict
stands).** Colored pairs compared by behavior: (a) single
tail vs batch `_gather` loop — both dispatch per call (no
construction-time commit: `resolve_node=`/`resolver=resolved`
0 hits), both gate-then-dispatch STRINGS, both stamp;
color duties only (await points, `reject_*` on sync only,
sequential awaits, `asyncio.gather(` 0 hits). (b)
`_stamp_node_type` vs `_await_and_stamp`: one-line async
sibling composing by call. Pure decisions (`_interleave`,
`_check_nodes_result`, `_check_typed_match`,
`_node_id_slot`) colorless and shared. Third-state refusal
guards both entries pre-ORM (`if not async_execution()` /
`if async_execution():`, re-derived). REVISED: the coercion
is now gate-only on both root paths (values discarded,
strings handed on); the defaults re-coerce through the
composing helpers.

**3. Derived-not-repeated knowledge — CONFIRM.** Slot
derived ONCE (`::_node_id_slot`, 1 def), read by exactly 2
code calls (coercer + mapper; package-wide census: no
other caller — [types-relay][types-relay] reaches the slot
only through `::_coerce_pk_or_none`), neither consumer
body re-reads `resolve_id_attr`/`_meta`/`get_field`
(code-only AST, docstrings excluded). Type names read from
the canonical definition attribute; `model_for` called ×3,
never re-spelled (0 direct `.model` reads). The worktree
`slots` memo is concurrent dirt, never judged.

**4. Inverse / round-trip pairs — REVISE (upstream arms
noted, verdict stands).** Decode+encode both live in
[types-relay][types-relay], neither half here (0
`encode_typename`, 0 `definition_for_graphql_name`,
re-derived). Read-filter vs write-map tails intentionally
differ (F7). Ledger append/clear and stamp/honor are split
pairs with named halves. REVISED: upstream `_order_nodes`
gained `None`-key arms (`list[str | None]`) serving the
Strawberry-`relay.node()` raw-string path; this file's
halves (`_interleave`, `_check_nodes_result`) are
byte-identical modulo the behavior-identical rename.

**5. Contracts restated in another medium — REVISE
(oracle set grew, verdict stands).** Package oracle: 26
test functions (was 23; +3 2935 pins + 1 helper,
re-derived by name), spelling wire literals (`Invalid
GlobalID`, `GLOBALID_INVALID`, `SyncMisuseError`,
`__typename`), reading no owner table (`_node_id_slot`/
`coerce_field_value_or_none` 0 hits). Live rows (37
`node(`/`nodes(` hits) likewise. [spec-032][spec-032]
Decisions 3/4/5/11 present (blob `1e96ad41`, clean).
REVISED: F7's projection carries one stale consumer-name
cite (D1); every other docstring claim re-verified.

**6. Enforcement by omission — CONFIRM.** Both factories
enforce deadline → decode → typed-match → gate → dispatch
→ stamp; batch-only decode-all-first + empty short-circuit
vs single-only no-query `null` re-derived against
[spec-032][spec-032] (Decision 5 shapes differ — contract,
not gap). Write primitive enforces all four statuses on
every caller (single return type). No gap: no new defect
beyond D1.

### Challenges (definition counts at HEAD)

Authoritative definitions counted only; consumers, oracles,
projections listed, not counted. All counts probe-verified
(`execution-verified`); oracle/spec bodies
`static-reviewed`.

| # | Rule | Change posited | Definitions forced | Home |
|---|---|---|---|---|
| C-F1 | model read + seed | read via `registry.get`; seed via `base_queryset` | **0 here** (3 `model_for` consumers; separation clause verbatim) | F1 CONFIRM |
| C-F2a | coercion mechanics | drop `run_validators` | **1** ([querysets][querysets]`::coerce_field_value_or_none`; here 0) | F2 REVISE |
| C-F2b | field choice | coerce against `_meta.pk` unconditionally | **1** (`::_coerce_pk_or_none` via L1; [types-relay][types-relay]`::_node_value_or_none` composes by call, 0 new) | F2 REVISE |
| C-F2c | gate threshold | gate on `node_id == ""` too | **1** (the two `is None` gates move together — one rule, two call sites) | F2 REVISE |
| C-F3 | disposal | stop closing coroutines | **1** (owner; here 0, 2 seams) | F3 CONFIRM |
| C-F4 | decode key | `graphql_type_name` → `__name__` | **1** ([registry][registry]; here 0) | F4 CONFIRM |
| C-F5 | recourse sentence | rephrase this file's wording | **1 here** (2 use sites); unify-all-3 refused | F5 CONFIRM |
| C-F6 | lifecycle | third phase; count-entries semantics | **0 / 1 here** (bus owns phase; ledger owns emptiness) | F6 CONFIRM |
| C-F7a | decode status | fifth status | **1** (`::GlobalIDDecode`) + consumer mappings listed | F7 REVISE |
| C-F7b | mapper visibility | apply visibility in `::_resolve_real_pk` | **1 here** | F7 REVISE |
| C-F7c | raising | make the helper raising | **1 here** (raiseless re-derived) | F7 REVISE |
| C-F8 | guard | reorder base; change shape predicate | **1 + 1** (both in [list-field][list-field]/types base; here 0) | F8 CONFIRM |
| C-F9 | stamp | rename attr; flip precedence; drop copy | **1 / 1 / 1 here** (attr+honor upstream, stamp here) | F9 CONFIRM |
| C-L1 | slot fallback | map `"pk"` through `get_field` | **1 here** (2 direct + 1 transitive consumer, 0 re-derivations) | L1 REVISE |
| C-L2 | typed error | attach code; `is` → `==` | **1 here** each | L2 CONFIRM |
| C-L3 | reassembly | drop holes; drop gate; relax contract | **1 here** each (upstream `None` arms listed, not counted) | L3 REVISE |
| C-R1 | merge root/filter raises | move filter raises onto `::_decode_or_graphql_error` | refused (envelopes + no-leak shapes differ) | R1 CONFIRM |
| C-R2 | merge factories | one parameterized body | refused (contracts differ; 6 bilateral + 2 batch-internal helpers) | R2 REVISE |

### Findings: CONFIRM / REVISE ledger (12 + 9)

- **F1 `queryset-seed-and-model-read` — CONFIRM.** 3
  `model_for(resolved_type)` consumers, 0 direct
  `.model` reads, 0 `base_queryset`/`initial_queryset`,
  raw-manager + conditional `.using()` composition ×1;
  the separation clause verbatim at HEAD
  ([querysets][querysets] `#"relay.py.. deliberately does"`).
- **F2 `field-value-coercion` — REVISE (role value→gate +
  new composing consumer; counts hold).** Mechanics still
  1 definition at
  [querysets][querysets]`::coerce_field_value_or_none`
  (1 delegate call); the picker still here (slot field,
  `None`-passthrough). REVISED: both root-field calls now
  discard the value (`is None` gates, 2 sites); the write
  decode still uses it (1 site); [types-relay][types-relay]`::_node_value_or_none`
  (via `::_node_values`, used by all four defaults)
  composes the picker by call — 0 new definitions. The
  `::_coerce_pk_or_none` docstring's "SAME one the
  resolution filters on" clause now describes the gate +
  the defaults' re-coercion, verified true at both.
- **F3 `awaitable-refusal-and-disposal` — CONFIRM.** 2
  seams with per-seam owner/method + shared context +
  F5 recourse; async-accepting branches excluded (color
  duties); `asyncio.gather(` 0.
- **F4 `relay-node-name-decode` — CONFIRM.** 0 direct
  `definition_for_graphql_name`, 0 `encode_typename`,
  decode reached only through imported
  `::decode_global_id` (2 calls); decode body untouched
  by the drift.
- **F5 `sync-boundary-recourse-wording` — CONFIRM.**
  Rejected separation stands: 3 wordings / 3 contracts
  re-derived (this file's sentence, 2 use sites, vs the
  template vs the Relay-default wording, both 0 hits
  here). Trigger stands.
- **F6 `subsystem-clear-lifecycle` — CONFIRM.** 1 bus
  registration (`owner="relay.node_fields"`), ledger +
  clear-only body, 2 factory appends,
  directives-before-ledger order re-derived in both
  factories; finalizer reads emptiness only
  (`if _node_fields_declared and not any(`).
- **F7 `typed-globalid-decode` — REVISE (census
  precision + D1; counts hold).** Definitions still 4
  here (enum, record, mapper, primitive); raiseless,
  `except Exception` wrapping decode only, model
  identity `is`, no-leak split all re-derived.
  REVISED: the batched set decode
  ([write-values][write-values]`::decode_visible_relation_ids`)
  exists at HEAD but composes the single primitive per
  element via `::type_check_relation_id` — a consumer,
  not a second definition (the worktree split halves
  are concurrent, never judged). Consumer mappings:
  model root-id, single relation, batched set, form
  multi — all through the one primitive.
- **F8 `relay-node-target-guard` — CONFIRM.** `None` +
  `field=field` pass-through, 2 call sites here, 1 in
  [connection][connection], predicate in types base —
  all re-derived; delegation body typing-untouched.
- **F9 `relay-node-type-stamp` — CONFIRM.** Split
  ownership stands (attribute + honor upstream, stamp
  here); def + 4 call sites; async sibling composes by
  call; `None` passthrough, copy, suppress-setattr all
  re-derived.
- **L1 `relay-node-id-slot` — REVISE note, file-local
  stands.** Composition site still exactly 1; direct
  consumers still exactly 2 with 0 re-derivations
  (code-only AST); `"pk"` fallback + `None` arm
  re-derived. New: one TRANSITIVE consumer (the
  types/relay composing helper via the coercer) —
  listed, not counted; still 1 definition.
- **L2 `relay-typed-match-rejection` — CONFIRM.**
  Identity `is not`, both `graphql_type_name` reads,
  `extensions` absent from the body (code-only AST), 2
  in-file call sites; write/filter counterparts differ
  in contract (re-derived).
- **L3 `relay-batch-reassembly` — REVISE note,
  file-local stands.** `::_interleave` + 2 call sites,
  `::_check_nodes_result` + 2 call sites (materialize →
  length gate → `ConfigurationError`), param rename
  behavior-identical. Upstream `_order_nodes` gained
  `None`-key arms for the Strawberry path — listed, not
  counted; no second reassembly body (connection/list
  shapes differ in contract, re-read).
- **R1 `root-vs-filter GLOBALID_INVALID raises` —
  CONFIRM.** Refusal stands: whole-argument pre-query
  `GraphQLError` vs field-keyed filter envelopes;
  shared const + extensions shape owned by
  [errors][errors] (root 2 hits, filter 4+ hits).
- **R2 `single-vs-batch factory bodies` — REVISE prose,
  refusal CONFIRMS.** The contracts differ as recorded
  (nullable-single vs whole-field-failure vs
  empty-short-circuit vs per-type batching, all
  re-derived). Correction: 6 helpers are bilateral by
  name (decode, typed-match, gate, stamp, deadline,
  directives); `_check_nodes_result` + `_interleave`
  are batch-internal (0 single-side hits) — the prior
  "8 helpers, each called from both sides" over-claims.
  The refusal verdict is unaffected (the inline
  remainder IS the contract difference); trigger
  stands.
- **Enumeration — REVISE (counts, not coverage).**
  42→43/top-level-statements accounting above; every
  member homed; 0 added/removed/renamed defs.
- **Matrix — axes 1/3/6 CONFIRM; 2/4/5 REVISE** as
  recorded above (gate-only twins, upstream `None`
  arms, grown oracle set + D1).

### Defects (run 8)

- **D1 (run-8, doc-only, minor; owner
  `django_strawberry_framework/relay.py::decode_model_global_id`
  projection, F7):** the docstring names the relation
  `<field>_id` consumer ``_decode_relation_id_set``,
  which is defined nowhere at HEAD, at the drift base,
  or in the worktree (package-wide `git grep`: the
  relay.py docstring line + one test comment are the
  only hits; the name died no later than `e9c13f55`,
  which predates the drift base). The live consumers
  are [mutations-resolvers][mutations-resolvers]`::coerce_lookup_id`
  (correctly cited) and the
  [write-values][write-values] relation decoders
  (`::type_check_relation_id` /
  `::decode_visible_relation_ids`). No wire effect —
  steps + statuses + raiselessness all verified true.
  Routing note for Worker-0: the concurrent worktree
  hunk rewrites this same paragraph (new consumer
  names + body reshape around the owned trigger
  lines) — home the repair against HEAD bytes, never
  by judging the concurrent content. No other defect;
  all run-7 spot-checks re-hold at HEAD (broad-`except`
  wraps decode only; `_interleave` total over the
  `positions` alphabet; third-state refusal on both
  paths; directives-before-ledger in both factories).

### Pending execution (run 8)

None. All 155 probe checks are `execution-verified`
read-only (`git show` bytes, AST + token census; no
Django import, no DB, no registry writes, no source
mutation). No consolidation proposed, so no
consolidation gate with negative control is owed.
DB-backed cells inapplicable by construction (probes
touch no queryset, alias, or dialect; the one query in
the target, `::_resolve_real_pk`'s pk lookup, verified
by source read only, never executed). No `workspace.py`
run: no proof mutates source, so none is owed. No
shared-tree pytest run, per the item fence. Oracle and
spec bodies stay `static-reviewed`, the honest label
for a zero-edit item.

### Judgment (run 8)

Zero-edit file re-trace: matrix re-discharged against
HEAD bytes (gate-only twins + string seams re-derived;
slot read-twice-never-rederived; split pairs named;
oracle set +3; omission asymmetries contract-checked),
43/43 enumeration members homed (0 added/removed/renamed
defs), 21/21 rows re-derived (12 CONFIRM + 9 REVISE, all
REVISEs evidence-carrying and none moving rule
ownership), every rule still exactly one authoritative
definition with cross-module reads composing by name
(the new types/relay helpers compose the picker by
call). One new doc-only defect (D1, stale consumer-name
cite, pre-drift). One consumer-membership nomination
for Worker-0 (F2 gains the composing helper; home item
s14 / the F2 family item). No production edit, no test
change, no pending execution.

### Freshness (run 8)

Target `django_strawberry_framework/relay.py`: HEAD blob
`a09485a1` (655 lines) / worktree `fd88aafa` (781
lines) / pre-merge `f5760b45` (749 lines). Item baseline
`ITEM_BASELINE=64954c826b2a59f8068a4375f0e2fbf6e84021a8`;
HEAD `83998e08` unmoved start→finish. Zero tracked paths
touched: `git status --short` shows the target modified
(concurrent + 1 owned prose hunk, attributed above, left
untouched) and this artifact untracked (the sole written
path).

| Path | HEAD | Worktree | 9aaaad5d |
|---|---|---|---|
| `django_strawberry_framework/relay.py` | `a09485a1` | `fd88aafa` | `f5760b45` |
| `django_strawberry_framework/types/relay.py` | `968fb95a` | `6c2e8c20` | `4b2a9df5` |
| `django_strawberry_framework/list_field.py` | `77ddb86c` | `1dcb0c43` | `f5b0183e` |
| `django_strawberry_framework/registry.py` | `9d2021eb` | `57fa18ae` | `27358cbc` |
| `django_strawberry_framework/resource_policy.py` | `47befb3f` | `927b89a2` | `5b4a80f0` |
| `django_strawberry_framework/connection.py` | `3d6dd424` | `64b85d0e` | `1fca6266` |
| `django_strawberry_framework/utils/directives.py` | `0368ff51` | `bbbf3b42` | `84f770d4` |
| `django_strawberry_framework/utils/errors.py` | `793855e0` | `6048b7fe` | `6a389474` |
| `django_strawberry_framework/utils/execution_mode.py` | `b86a08cd` | `b86a08cd` | `9805cdaf` |
| `django_strawberry_framework/utils/querysets.py` | `392e50d0` | `cfc773ba` | `8fc556d5` |
| `django_strawberry_framework/utils/write_transaction.py` | `c0a12b34` | `49102e69` | `4a83f43d` |
| `django_strawberry_framework/utils/write_values.py` | `01a3318c` | `4fa8118d` | `13548c76` |
| `django_strawberry_framework/exceptions.py` | `f27e1f91` | `34e2e6be` | `93401220` |
| `django_strawberry_framework/testing/relay.py` | `8e5f9c9d` | `0c48f0a9` | `f807bf92` |
| `django_strawberry_framework/__init__.py` | `8b165672` | `8b165672` | `0ef72601` |
| `django_strawberry_framework/filters/base.py` | `e2e683a8` | `fc1cf61f` | `3b1dcbce` |
| `django_strawberry_framework/mutations/resolvers.py` | `7a25afea` | `dd00ec6e` | `c9cff059` |
| `django_strawberry_framework/types/finalizer.py` | `cb2dde6b` | `7d354e77` | `b9d8acb2` |
| `tests/test_relay_node_field.py` | `7c0f22ed` | `7f47c3dd` | `d4ce0c7d` |
| `examples/fakeshop/test_query/test_library_api.py` | `91f0238b` | `099e25b9` | `26dd0abb` |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | `1e96ad41` | `1e96ad41` | `1e96ad41` |

Searched population for every "no second site" claim:
full package source at HEAD (`git grep HEAD`, 117+ `.py`
files), both oracle files at HEAD bytes, and the spec
above. Excluded on body strength: modules with zero
`relay`/`GlobalID`/`resolve_node` vocabulary (all other
subsystems — the connected-source probe names every
examined module). Any fingerprint change reopens the
affected rows. Corpus note: `docs/dry/worker-memory/`
was never read; no other worker's scratch was opened.

## Independent verification (run 8)

Expectation-first at HEAD bytes (`83998e08`, confirmed unmoved at
finish). Read order kept: the governing docs, the queue record's run-8
section, the owned-changes ledger, the full target at HEAD bytes (655
lines, read whole), the four drift-base→HEAD commits on the target in
full, the HEAD→worktree diff in full (19 hunks), the connected sources
at HEAD bytes, both oracle files, the spec. Then the run-8 submission,
reconciled row by row below. Instruments (all read-only, `/tmp`-only,
no Django import, no DB, no source mutation, no pytest):
`/tmp/w2_relay_probe.py` (110 checks, `ALL OK`), `ast` enumeration +
normalized per-symbol base→HEAD diff, chain-order instruments,
scoped `git grep` censuses, a 63-hash freshness re-hash. No sibling
role scratch under `docs/dry/` was opened.

### Own trace (drift delta at HEAD bytes)

Drift base `0c0537e2`→HEAD on the target is exactly 4 commits, one
carrying behavior. `2935e0e4` (relay hunk read whole): both root
resolvers now gate on `if _coerce_pk_or_none(resolved, node_id) is
None:` with the value discarded (2 sites, re-derived) and hand the
decoded `node_id` string to `resolve_node` / `resolve_nodes`
(`groups` retyped `list[str]`); the types/relay half deletes
`_coerce_node_ids` (0 hits at HEAD) and adds `_node_value_or_none`,
which composes `relay.py::_coerce_pk_or_none` BY CALL behind an
in-function import carrying the load-cycle comment, plus
`_node_values` (map + required-raise) and `_raise_if_required`, plus
`None`-key arms in `_order_nodes`. Routing measured at HEAD bytes:
single-sync calls `_node_value_or_none` directly, batch ×2 call it
via `_node_values`, single-async receives the computed `value` as a
parameter from single-sync — all four defaults route through the one
helper body, zero new coercion bodies. The other 3 commits
(`999a1aab`, `b20277fe`, `fef11e64`) are annotations + the
`TYPE_CHECKING` guard + import widening + 2 identity `cast()` wraps +
1 bare local annotation + the positional `pks`→`node_ids` rename +
comments, each hunk read. Normalized screen (annotations, docstrings,
`cast`, bare annotations stripped): 16/16 def/class names identical
in order, 0 added/removed/renamed; 13/16 symbols byte-equal, the 3
differing exactly the two factories (the 2935 reshape) and
`_check_nodes_result` (the rename). `b63df99d` touches
[types-relay][types-relay] only (+ `LIFECYCLE.html`, not package
code): `_apply_node_filter` / `_apply_nodes_filter` take required
already-coerced values, no fallthrough, no second coercion body.

Value→gate, my reads: both root gates discard (`is None`, no
assignment, `pk =` absent from both factory segments); the string
reaches `resolved.resolve_node(node_id, ...)` and per-type
`node_ids=node_ids`; the write decode keeps `pk =
_coerce_pk_or_none(...)` → `_resolve_real_pk(resolved_type, pk)`
(value used, 1 site). Chain order re-derived in both factories:
deadline → decode → typed-match → gate → dispatch (both batch sites)
→ stamp.

### Per-row judgments (21 rows, my counts)

- **F1 CONFIRM.** 3 `model_for(resolved_type)` consumers; 0 direct
  `.model` reads; 0 `base_queryset`/`initial_queryset`; raw-manager
  + conditional `.using()` ×1; separation clause verbatim
  (double-backtick form) in [querysets][querysets]. 0 here.
- **F2 REVISE (role value→gate + composing consumer).** Mechanics 1
  at the owner (1 delegate call); picker here (slot field,
  `None`-passthrough); 2 root gates discard, write uses; the
  composing helper composes by call, 0 new coercion bodies.
  Correction C2 (below) tightens the routing parenthetical; counts
  hold, ownership unchanged.
- **F3 CONFIRM.** 2 seams, per-seam owner/method, shared context ×2,
  F5 recourse ×2; async branches excluded; `asyncio.gather(` 0.
- **F4 CONFIRM.** 0 `definition_for_graphql_name`, 0
  `encode_typename`, `decode_global_id` imported + 2 calls.
- **F5 CONFIRM.** 3 wordings / 3 contracts re-derived; local
  sentence 2 use sites; template + default wording 0 hits here.
- **F6 CONFIRM.** 1 bus registration
  (`owner="relay.node_fields"`); ledger + clear-only body; 2
  factory appends; directives-before-ledger in both; finalizer
  reads `if _node_fields_declared and not any(`.
- **F7 REVISE (census + D1; counts hold).** 4 definitions here;
  raiseless (code-only); `except Exception` wraps the decode call
  only; model identity `is`; single-query mapper. The batched set
  decode exists and maps per element through
  `::type_check_relation_id` (1 `decode_model_global_id(` call in
  that body, 0 direct in the batched body): consumer, not a second
  definition. Live consumers `::coerce_lookup_id`,
  `::type_check_relation_id`, `::decode_visible_relation_ids` all
  present at HEAD.
- **F8 CONFIRM.** `None` + `field=field` pass-through; 2 calls
  here, 1 in [connection][connection], predicate in types base.
- **F9 CONFIRM.** Attribute + honor upstream, stamp here; def + 4
  calls (5 occurrences); sibling composes by call; `None`
  pass-through, copy, suppress-setattr re-derived.
- **L1 REVISE note, file-local stands.** Composition site exactly
  1 (code-only); 2 direct code calls; 0 re-derivations in either
  consumer body (code-only); `"pk"` fallback + `None` arm;
  1 transitive consumer via the coercer — listed, not counted.
- **L2 CONFIRM.** Identity `is not`; 2 code `graphql_type_name`
  reads (a 3rd hit is docstring prose); `extensions` absent
  code-only; 2 in-file calls.
- **L3 REVISE note, file-local stands.** `_interleave` + 2 calls,
  gate + 2 calls, materialize → length gate →
  `ConfigurationError`; rename positional at both call sites;
  upstream `None` arms re-derived (`list[str | None]`, both
  branches) — listed, not counted; no second body (connection /
  list shapes differ in contract, re-read).
- **R1 CONFIRM.** Root 2 hits (import + 1 raise); filter 5 hits
  around 3 raise sites; whole-argument pre-query vs field-keyed
  envelopes differ; shared const + shape owned by
  [errors][errors].
- **R2 REVISE prose, refusal stands.** 6 helpers verified
  bilateral by name (decode, typed-match, gate, stamp, deadline,
  directives — each present in both factory segments); gate-check
  + interleave batch-internal (0 single-side hits). The run-7
  "8 bilateral" over-claim is corrected; the inline remainder is
  the contract difference, trigger stands.
- **Enumeration REVISE (counts, not coverage).** 43/43 homed by my
  instrument; member table indices 0–42 reproduce exactly; 0
  added/removed/renamed, order same; nested `_resolve` ×2 +
  `_gather` ×1; enum 4 / record 3. Correction C1 (below) fixes the
  import-kind split; total 20 imports stands.
- **M1 CONFIRM.** Guard 1 def + 2 calls here + 1 connection;
  typed decode single-sited with per-element consumers; const +
  shape shared only; 6 bilateral helpers; deadline/directives/
  coded-extensions/pipeline links consumer-side.
- **M2 REVISE (gate-only twins, verdict stands).** Per-call
  dispatch, no construction-time commit (both patterns 0);
  gate-then-dispatch strings on both paths; color duties only;
  sibling composes by call; pure decisions colorless; third-state
  refusal on both entries pre-ORM.
- **M3 CONFIRM.** Slot derived once, read twice, never re-derived
  (code-only); type names from the canonical attribute; `model_for`
  ×3, never re-spelled.
- **M4 REVISE (upstream arms noted, verdict stands).** Neither
  half here (0/0 re-derived); read vs write tails intentionally
  differ; ledger + stamp split pairs named; upstream `None` arms
  listed, not counted.
- **M5 REVISE (oracle set grew + D1, verdict stands).** Package
  oracle 26 test functions (23 + the 3 string-seam pins +
  `_strawberry_node_schema`, names re-derived), spelling wire
  literals, reading no owner table; live rows 38 occurrences on 37
  lines (C3); [spec-032][spec-032] Decisions 3/4/5/11 present
  (blob `1e96ad41`); module docstring re-verified except D1.
- **M6 CONFIRM.** Both factories enforce the full chain in order
  (re-derived); batch-only vs single-only asymmetries match
  Decision 5; write primitive 4 statuses, no optional checks;
  registry read correctly absent. No gap.

### Enumeration (my instrument)

`ast.parse` over `git show HEAD:` bytes: 43 statements = 1 docstring
+ 20 imports + 1 `TYPE_CHECKING` guard + 3 `Assign` (`_NodeT`,
`__all__`, recourse) + 1 `AnnAssign` (ledger) + 13 `FunctionDef` + 1
`AsyncFunctionDef` + 2 `ClassDef` + 1 bus `Expr`. Every member lands
in the run-8 member table (indices verified one by one against my
dump); all challenges end in a home. No new family is owed: the
coercion flow stays sole-picker here with mechanics at its owner.

### Attribution (HEAD→worktree, my decomposition)

19 default-context hunks (189+/63-, blob `fd88aafa` unchanged since
the submission), each read: 1 mixed hunk carrying the 4 owned
trigger-docstring lines (additive, docstring-contained, code-inert,
byte-`diff` vs `9aaaad5d` zero lines, absent at HEAD where the
`riggers (Family` pattern counts 0) inside the concurrent
`decode_model_global_id` docstring + body reshape; the other 18 are
concurrent-external (truth-migration import + renders, lazy-proxy
unwrap, `slot=`/`slots` threading, the two new split halves,
`isawaitable`-gated refusals, comment rewordings). The worktree
`_decode_and_coerce` equals its `9aaaad5d` bytes modulo annotation
spellings only (`Any`→`object`, narrowed containers). Nothing was
judged from worktree bytes; all counts above are HEAD bytes, so no
concurrent hunk underwrites any verdict. Label note C5: the
submission's "`-U0`" tag misnames the width (U3 = 19, U0 = 36); the
19-hunk substance it attributes is exactly this decomposition.

### D1 adjudication — CONFIRMED (doc-only, minor, moves nothing)

The name is dead: no `def _decode_relation_id_set` repo-wide at
HEAD; scoped census (package + tests + examples) at HEAD and at the
drift base gives exactly the relay.py docstring line + the one test
comment; the `def` existed at `e9c13f55^` and is gone at `e9c13f55`,
which predates the drift base; the worktree paragraph no longer
carries the name (concurrent rewrite, never judged). The docstring
sentence cites it as a live consumer beside `coerce_lookup_id`,
which is real — stale cite, no wire effect (steps + statuses +
raiselessness all re-verified true). It sits correctly inside F7's
REVISE as a projection note and moves no definition count, no
owner, no index row. Routing agrees with the submission: repair
against HEAD bytes; the concurrent paragraph is out of scope.

### Nomination judgment — ENDORSED

F2 `field-value-coercion` gains the composing consumer
[types-relay][types-relay]`::_node_value_or_none` →
`::_coerce_pk_or_none`: the edge is real (by-call composition,
verified), membership (not a new row) is the right shape since no
new rule is named, and the holding item s14 / the F2 family item is
the right home (that file's rows live there). Carried with C2's
routing precision: single-sync direct, batch ×2 via `_node_values`,
single-async by parameter.

### Defects

D1 confirmed as above (submission's). No new package defect found:
run-7 spot-checks re-hold at HEAD (broad-`except` wraps decode
only; `_interleave` total over the `positions` alphabet; third-state
refusal on both paths; directives-before-ledger in both factories).
Record corrections (metadata precision, none moving a verdict,
index row, or decision — no resubmission owed): C1 import-kind
split is 16 `ImportFrom` + 4 `Import` (total 20 stands); C2 F2
routing parenthetical as tightened above; C3 live census 38
occurrences on 37 lines (one double-hit comment line); C4
pre-merge dirt 17 occurrences on 16 lines (one line carries two
`truth.` reads); C5 hunk-width label as above.

### Pending execution

None. All proofs execution-verified read-only; no consolidation, so
no consolidation gate with negative control is owed; DB-backed cells
inapplicable by construction (no queryset, alias, or dialect read
executed — the one query verified by source read only). No
`workspace.py` run: no proof mutates source, so none is owed. No
shared-tree pytest run, per the item fence. Oracle and spec bodies
stay `static-reviewed`.

### AGENTS.md prose check

Item-scoped diff re-measured empty by me (`git diff
64954c826b2a59f8068a4375f0e2fbf6e84021a8 --
django_strawberry_framework/relay.py` → 0 bytes); target blob
`a09485a1` equals `HEAD:` for every judged byte. Touched paths: this
`.md` artifact only, so no ruff/mypy run is owed; citations reuse
the existing reference-style link block (no new ref-ids, scaffold
intact); no process provenance; concurrent dirt preserved; no
commit. Freshness re-hash: all 63 hashes (21 paths × HEAD /
worktree / `9aaaad5d`) reproduce the submission's table exactly.

### Judgment

Zero-edit file re-trace verified: drift delta owned at HEAD bytes
(2935 value→gate + composing helpers; typing rest proved inert),
43/43 members homed, 21/21 rows survive with independent counts (12
CONFIRM + 9 REVISE, no ownership moves), every rule exactly one
authoritative definition with cross-module reads composing by name,
1 doc-only defect confirmed, 1 consumer-membership nomination
endorsed, no pending execution. `Status: verified`.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[directives]: ../../django_strawberry_framework/utils/directives.py
[errors]: ../../django_strawberry_framework/utils/errors.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[package-init]: ../../django_strawberry_framework/__init__.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[resource-policy]: ../../django_strawberry_framework/resource_policy.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[write-tx]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values]: ../../django_strawberry_framework/utils/write_values.py
[filters-base]: ../../django_strawberry_framework/filters/base.py

<!-- tests/ -->
[test-library-api]: ../../examples/fakeshop/test_query/test_library_api.py
[test-relay-node-field]: ../../tests/test_relay_node_field.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
