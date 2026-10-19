# DRY review: `django_strawberry_framework/mutations/fields.py`

Status: verified
Run: 0.0.15 2026-09-18-1

Item kind: FILE (inventory backstop). No consolidation performed; every rule
below is routed to an open family holding item, recorded file-local with its
proving challenge, or is a rejection carrying its contract difference +
trigger. Zero production edits; zero tracked files changed.

## System trace

Target (360 lines, FRESH): the write-side field factory
[mutations-fields][mutations-fields]`::DjangoMutationField` plus its guard
trio, its forward-ref / signature machinery, and its transaction marker. What
it owns on the WORKING tree:

- `::DjangoMutationField` — the write-side root-field factory (validates the
  target at the construction line, synthesizes the per-operation signature +
  lazy `data:` / payload-return refs, stamps the resolver, returns
  `strawberry.field(resolver=...)` with no class-attribute annotation).
- `::_validate_mutation_target` + `::_has_mutation_protocol` +
  `::_is_registered_mutation_target` — the construction-time target guard
  (concrete validated mutation / form-mutation family member with own
  `_mutation_meta` and a current ledger entry; duck-typed, not
  `issubclass(DjangoMutation)`, per spec-038 Decision 5).
- `::_lazy_ref` + `::build_lazy_field_signature` — the shared
  `Annotated[..., strawberry.lazy(...)]` forward-ref leaf and the injected
  `(__signature__, __annotations__)` builder the auth fixed-field factories
  ride (`login_mutation` / `logout_mutation` via
  [auth-mutations][auth-mutations]`::_make_auth_field`, `current_user` via
  [auth-queries][auth-queries]`::current_user` + `::_lazy_ref`).
- `::_synthesized_mutation_signature` — the per-operation `id` / `data`
  argument map (spec-036 Decision 14) over the
  [mutations-operations][mutations-operations] predicates.
- `::MUTATION_CLASS_MARKER` — the `_django_mutation_cls` stamp
  [schema][schema]`::_marked_mutation_class` and
  [resource-policy][resource-policy]`::_mutation_input_specs` read back.

EXTERNAL in-flight hunk (never edited, reverted, or tidied): working blob
`8c60a5c6…` vs HEAD blob `cf518361…` (+60/-17, `git diff HEAD` first-hand):
the `_safe_class_name` import plus the hardening of
`::_validate_mutation_target` (guarded `isinstance`, guarded own-`__dict__`
snapshot read, `_safe_class_name` labels), `::_has_mutation_protocol`
(try/except probe answering `False` on a raising metaclass), and
`::_is_registered_mutation_target` (identity `is` scan over both ledgers,
citing [mutations-sets][mutations-sets]`::make_declaration_registry`
#"Identity-scan dedup"). Attributed by content to concurrent work (the
sibling `mutations/__init__.py` item's first-hand read; companion oracle
dirt in [test-fields][test-fields] working `53e39ccb…` vs HEAD
`db83f239…`). Since this file item makes ZERO production edits, the dirt is
not a stop: the trace below reads the WORKING tree throughout, records BOTH
fingerprints per finding, and flags every hunk-touching finding
`pending-settle` for Worker 0 instead of a verdict.

Connected code read for judgment, outside the item (full reads unless
noted): [mutations-init][mutations-init] (sibling F1 leaf: re-exports
`DjangoMutationField`; ruled robust to the hunk first-hand),
[mutations-operations][mutations-operations] (descriptors + predicates),
[mutations-inputs][mutations-inputs]`::build_payload_type` + `INPUTS_MODULE_PATH`,
[mutations-sets][mutations-sets]`::make_declaration_registry` +
`::make_meta_validating_metaclass` + `::build_and_stash_payload` (grazed
ranges noted in findings), [mutations-resolvers][mutations-resolvers]
(docstring + `::make_resolver_entries` + `::coerce_lookup_id` by reference),
[auth-mutations][auth-mutations] (`::_make_auth_field`, `::login_mutation`,
`::logout_mutation`, `::register_mutation` — the one caller routing through
`DjangoMutationField`), [auth-queries][auth-queries]`::current_user`,
[directives][directives]`::validated_field_directives` (full),
[execution-mode][execution-mode]`::async_execution` (full),
[exceptions][exceptions] safe renderers (full),
[schema][schema]`::_marked_mutation_class` (grazed),
[resource-policy][resource-policy]`::_mutation_input_specs` (grazed),
[list-field][list-field] factory-site async asymmetry + `::_validate_djangotype_target`
+ `::DjangoListField` dispatch (grazed), [relay][relay]`::DjangoNodeField` /
`::DjangoNodesField` dispatch + directives (grazed),
[connection][connection]`::DjangoConnectionField` head (grazed),
[utils-inputs][utils-inputs]`::build_lazy_input_annotation` (grazed),
[filters-inputs][filters-inputs]`::_build_logic_fields` (grazed),
[forms-sets][forms-sets] + [rf-sets][rf-sets] `input_module_path` seams
(grep), [orders-inputs][orders-inputs] lazy-marker prose (grep), oracles
[test-fields][test-fields] (full 601-line read) and the live
[products-api][products-api] signature + async rows (grep-confirmed).
Excluded with reason: every other indexed family was judged on its
mechanism against this target's REAL surface and found to have none here
(see Matrix + Challenges C9-C12); all other concurrent dirt
(`connection.py`, `tests/test_connection.py`, staged
`tests/utils/test_querysets.py`, `filters/inputs.py`, `filters/sets.py`,
`forms/inputs.py`, `extensions/resource_policy.py` hunks,
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`) is untouched;
none of it is in this item's paths.

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Sibling read-side factories
(`DjangoListField`, `DjangoConnectionField`, `DjangoNodeField` /
`DjangoNodesField`) each own a construction-time target validator AND ride
the one directives containment AND dispatch runtime-async for their default
generated resolver — the same three beats this factory plays. Considered
merges with the read-side target validators: rejected, see R7 (registered
`DjangoType` + Relay-shape vs concrete-mutation-protocol: different
populations, different contracts). Considered merge of the directives
containment: already single-sited at
[directives][directives]`::validated_field_directives` — this file is a
consumer (family nominated, F6). Considered merge of the async dispatch:
runtime `async_execution()` per-call dispatch is the SHARED shape for every
package-owned default resolver ([list-field][list-field] `::_default`,
[relay][relay] nodes `_resolve`, [auth-mutations][auth-mutations]
dispatchers); the `is_async_callable` construction-time half exists ONLY
where a consumer `resolver=` seam exists, which this factory has not — the
module docstring states the asymmetry and both halves were verified at
their sites. No second runtime-dispatch definition lives here. Auth fixed
fields consume `::_lazy_ref` + `::build_lazy_field_signature` by name
(families nominated, F3/F4). The form / serializer flavors are accepted
through the duck-typed protocol, not a second factory (oracle
[test-fields][test-fields]`::test_generalized_target_accepts_modelform_and_plain_form_family`
+ serializer generalization row, both read).

**2. Sync/async twins.** No colored pair is defined here: one `_resolve`
closure dispatches per call via `async_execution()`, mirroring
[relay][relay]`::DjangoNodesField` `_resolve`. The sync/async ENTRY pair
(`resolve_sync` / `resolve_async`) is owned at
[mutations-resolvers][mutations-resolvers]`::make_resolver_entries`
(indexed family `shared-write-entry-factory`): this file CONSUMES the
entries by name (`mutation_cls.resolve_sync` / `.resolve_async`) and never
re-spells the UNSET-normalization or the `sync_to_async` boundary — see R1
(check, do not inherit). Compared by behavior, not shape: both twins run
the same pipeline body; the field adds no second boundary.

**3. Derived rather than repeated knowledge.** Payload name
`f"{mutation_cls.__name__}Payload"` is predicted here but MATERIALIZED at
[mutations-inputs][mutations-inputs]`::build_payload_type` (`type(f"{mutation_name}Payload", …)`);
the bind ([mutations-sets][mutations-sets]`::build_and_stash_payload`)
passes `__name__` through and stashes `_payload_type_name`, which
[mutations-resolvers][mutations-resolvers]`::payload_cls_for` reads back
(compose by name — the correct shape). Two spellings of one grammar today:
family nominated, F1. Input names are NOT re-derived: `data:` consults the
`mutation_cls.input_type_name(meta)` / `.input_module_path` seams (model →
`mutations.inputs`, form flavors → `forms.inputs`, serializer →
`rest_framework.inputs`; seams verified by grep), and `INPUTS_MODULE_PATH`
is imported, never re-spelled. The `Annotated[..., strawberry.lazy(...)]`
leaf spelling vs [utils-inputs][utils-inputs]`::build_lazy_input_annotation`
vs [filters-inputs][filters-inputs]`::_build_logic_fields` self-ref:
rejected merges, see R5/R6.

**4. Inverse / round-trip pairs.** Two halves inventoried: (a) signature
synthesis (declares `id`/`data` args) vs `_resolve` `takes_id` gating
(consumes `id` kwarg) — same-file pair, file-local with trigger, FL5/C3;
(b) `MUTATION_CLASS_MARKER` stamp (this file) vs reads in
[schema][schema]`::_marked_mutation_class` (transaction window) and
[resource-policy][resource-policy]`::_mutation_input_specs` (budget
classification) — one constant, consumers by name: family nominated, F2.
No pack/unpack, build/parse, or input/output-shaping second half lives
here: payload construction is [mutations-inputs][mutations-inputs]' half
alone.

**5. Contracts restated in another medium.** Production (this file);
authoritative contract sources (spec-036 Decisions 5/7/8/14, spec-038
Decision 5, spec-040 D12/P1/P2 — cited, not re-verified against archived
spec text; the in-file docstring carries the Decision pointers as
projection); projections (module docstring: no-annotation timing claim,
runtime-dispatch claim, `id: ID!` server-side-decode claim, `.field()`
fallback note — each verified against its body/site); independent oracles
([test-fields][test-fields] construction/guard/metadata/directives rows —
spelled literally, never reading the owner; live
[products-api][products-api]`::test_create_update_delete_item_argument_signatures_over_http`
+ `::test_create_item_over_graphql_async` — wire verdicts). A payload-name
or signature change moves production once; oracles + projections follow as
their own media, not counted (C1/C6).

**6. Enforcement by omission.** Family enumerated: model create / update /
delete, plain-form `"form"` sentinel, ModelForm create / update,
serializer create / update (descriptors + flavor validation read). The
construction guard fires on EVERY `DjangoMutationField(...)` call —
including the `::register_mutation` rider path — so no flavor bypasses it.
The fixed auth surfaces (`login` / `logout` / `current_user`) take NO
mutation target and never call this factory: different contract (spec-040
fixed holders + ledgers), not an omission — N/A by construction, never a
verdict. The `takes_id = operation != "form"` inline mirrors the seam shape
([mutations-sets][mutations-sets]`::resolver_seams` `with_id`: default
`True`, `False` only for the model-less plain `DjangoFormMutation`),
not the signature predicate `operation_takes_id`: create is inline-True
/ predicate-False by design (the inline governs the dispatch kwarg —
create passes `id=UNSET` to a `with_id` seam whose `(cls, info, *, data,
id)` signature requires `id` with no defaults — while the predicate
governs the signature arg, which create omits); update T/T, delete T/T,
form F/F. The divergence trigger is a flavor whose `with_id` seam shape
diverges from `operation != "form"`, unreachable under the supported
API, so no member lacks a guard its contract requires (C3 ends here
with 0 defects; the trigger is recorded at FL5).

### Enumeration

Instrument: `python3 -c "ast.parse"` over the WORKING file, counting
`ast.Module.body` members — **19 top-level statements**. Every member
lands below; every challenge in `### Challenges` ends in a family row, a
file-local row, or a rejection.

| # | Statement | Binds | Home |
|---|---|---|---|
| 1 | module docstring | prose projection | projection (verified per claim in Matrix 5) |
| 2–11 | 10 imports (`__future__`, `inspect`, `typing`, `strawberry`, `Info`, `..exceptions`, `..utils.directives`, `..utils.execution_mode`, `.inputs INPUTS_MODULE_PATH`, `.operations` predicates) | compose-by-name | no rule defined (C9–C12 end here, 0 definitions) |
| 12 | `MUTATION_CLASS_MARKER = "_django_mutation_cls"` | 1 name | F2 family row |
| 13 | `def _validate_mutation_target` | guard | FL1 file-local (pending-settle) |
| 14 | `def _has_mutation_protocol` | probe | FL2 file-local (pending-settle) |
| 15 | `def _is_registered_mutation_target` | ledger check | FL3 file-local (pending-settle) |
| 16 | `def _lazy_ref` | forward-ref leaf | F4 family row |
| 17 | `def build_lazy_field_signature` | signature builder | F3 family row |
| 18 | `def _synthesized_mutation_signature` | per-op arg map | FL4 file-local (robust-to-both) |
| 19 | `def DjangoMutationField` | factory | FL5 file-local (robust-to-both) |

Payload-name prediction (line 297) → F1 family row. `takes_id` inline
(line 330) → FL5/C3. Directives label + `async_execution()` dispatch
(lines 337/354) → F6 consumer + R4 note.

### Challenges

Each rule: change posited, authoritative-definition count (consumers,
oracles, projections listed, not counted).

- **C1. Rename the payload suffix** (`Payload` → `Result`).
  Definitions forced: [mutations-inputs][mutations-inputs]`::build_payload_type`
  (`type(f"{mutation_name}Payload", …)`) AND
  [mutations-fields][mutations-fields]`::_synthesized_mutation_signature`
  (`f"{mutation_cls.__name__}Payload"`). Count = **2** (shared token or
  not). [mutations-sets][mutations-sets]`::build_and_stash_payload` passes
  `__name__` through and stashes the built name (0 edits — composes by
  name); auth fixed names (`"Login"` / `"Logout"`) ride the base-name
  argument (0 edits); oracles spelling `CreateItemPayload!` move as media.
  → F1 family nomination. Robust-to-both (neither line in the hunk).
- **C2. Rename the transaction marker.** Definitions forced: the
  `::MUTATION_CLASS_MARKER` constant alone — both readers import the name
  (compose by name, 0 edits). Count = **1**. → F2 family nomination.
  Robust-to-both.
- **C3. Add a fifth operation kind** (axes: id-less non-`"form"`; id-bearing;
  data-less). The descriptor table + flavor validation own the vocabulary
  (family nominated, F5 — this file consumes `operation_takes_id` /
  `operation_takes_data` by name, 0 edits). The `_resolve` inline
  `operation != "form"` mirrors the seam shape, not the predicate:
  create is inline-True / predicate-False by design (the dispatch kwarg
  passes `id=UNSET` to the `with_id` seam, whose `(cls, info, *, data,
  id)` signature requires `id` with no defaults, while the signature
  omits `id:` — the in-file comment states the convention); replacing
  the inline with `operation_takes_id` would omit `id=` and `TypeError`
  every create mutation. The true divergence trigger is a flavor whose
  `with_id` seam shape diverges from `operation != "form"` (a second
  model-less flavor, or a model-backed `"form"`). Unreachable under the
  supported API (closed flavor vocabularies read), so file-local with
  trigger, not a defect: the fix direction is to consult the seam shape
  (`with_id` on the meta/seam, or probe the seam), never
  `operation_takes_id`. Count = 1 inline site + 1 owning seam factory.
  → FL5. Robust-to-both (line 330 outside hunk).
- **C4. Change the root-field signature shape** (`root`/`info`/keyword-only
  args). Definitions forced: `::build_lazy_field_signature` alone; both
  consumers ([mutations-fields][mutations-fields] synthesis,
  [auth-mutations][auth-mutations]`::_make_auth_field`) call it (0 edits).
  Count = **1**. → F3 family nomination. Robust-to-both.
- **C5. Change the lazy forward-ref shape.** Definitions forced:
  `::_lazy_ref` alone for the mutation/auth surface (all four auth call
  sites + both synthesis sites route through it). Count = **1** (+ R5/R6
  stay separate). → F4 family nomination. Robust-to-both.
- **C6. Change the per-operation argument map** (e.g. update drops `id`).
  Definitions forced: `::_synthesized_mutation_signature` alone (predicates
  compose by name; oracles move as media). Count = **1**. → FL4.
  Robust-to-both.
- **C7. Hostile construction target** (axes: raising `__class__`,
  raising metaclass `__getattr__`, raising `__dict__`, raising `__eq__`
  on the ledger path, raising `__name__`). Definitions forced: the guard
  trio alone (each hostile axis collapses to the typed
  `ConfigurationError`; oracles in [test-fields][test-fields] move as
  media). Count = **1**. → FL1/FL2/FL3. **Hunk-touching →
  pending-settle** (the WORKING behavior was traced, not the HEAD
  behavior; verdict waits for settle).
- **C8. Change the sync/async dispatch decision.** Definitions forced: the
  `_resolve` closure alone (`async_execution()` is owned at
  [execution-mode][execution-mode] and consumed here). Count = **1**. →
  FL5. Robust-to-both.
- **C9–C12. Checked no-surface (0 definitions here; do not inherit).**
  C9 `shared-write-entry-factory` (owner
  [mutations-resolvers][mutations-resolvers]`::make_resolver_entries`):
  rejected, R1. C10 `sealed-authorization-source` (owners at
  [mutations-sets][mutations-sets]): rejected, R2. C11
  `type-registry-model-type-map` (owner `registry.py::TypeRegistry`):
  rejected, R3. C12 `one-sync-boundary` (owner
  `utils/querysets.py::run_in_one_sync_boundary`): rejected, R4.
  `subsystem-clear-lifecycle` + `sync-boundary-recourse-wording`:
  checked, no surface (no clear callback, no ledger, no recourse string
  in this file).

## Findings

- **F1 — `mutation-payload-name` (family nomination, open).**
  Contract: the generated payload class is named `<MutationName>Payload`
  and materializes as a `mutations.inputs` module global. Variation axes:
  suffix spelling; hosting namespace. Sites + roles:
  [mutations-inputs][mutations-inputs]`::build_payload_type` = definition
  (materializes); [mutations-fields][mutations-fields]`::_synthesized_mutation_signature`
  = second spelling (predicts at construction, bind has not run);
  [mutations-sets][mutations-sets]`::build_and_stash_payload` = consumer
  (passes `__name__`, stashes built name);
  [mutations-resolvers][mutations-resolvers]`::payload_cls_for` = consumer
  (reads the stash); oracles ([test-fields][test-fields] payload rows,
  live [products-api][products-api] signature row) = media; docstring
  Decision-5 namespace clause = projection. Challenges: C1 count 2.
  Owner + lifetime: [mutations-inputs][mutations-inputs] (the materializer
  owns the grammar, principle 2/7); no stored derivation beyond the
  `_payload_type_name` stash (owner sets.py, validity = until
  `registry.clear()`, published at phase-2.5 bind, mutated by the bind
  only). Migration (for the family item): pure
  `payload_type_name_for(base_name)` at inputs.py; the fields.py site
  becomes a call (timing-safe: needs only the class-name string, which
  exists at construction). Distinct behavior: auth fixed names stay
  explicit arguments. Behavioral proof: static-reviewed (both spellings
  read first-hand; agreement pinned by oracles). Structural gate: the
  existing `test_no_class_attribute_annotation_builds_and_types_payload`
  + live signature rows fail if either spelling moves alone (negative
  control not run — gate-only observation, no bespoke test owed).
  Coupling: none. Freshness: fields.py work `8c60a5c6…` + HEAD
  `cf518361…`; inputs.py `fc442047…`; sets.py `cffa29e5…`; resolvers.py
  `3fd1e571…`; test_fields.py work `53e39ccb…` + HEAD `db83f239…`.
  **Robust-to-both** (hunk touches neither spelling).
- **F2 — `mutation-class-marker` (family nomination, open).**
  Contract: the synthesized resolver carries the bound mutation class
  under `_django_mutation_cls`. Sites + roles:
  [mutations-fields][mutations-fields]`::MUTATION_CLASS_MARKER` =
  definition (stamp); [schema][schema]`::_marked_mutation_class` =
  consumer (transaction window); [resource-policy][resource-policy]`::_mutation_input_specs`
  = consumer (budget classification). Challenges: C2 count 1. Owner:
  fields.py (narrowest owner every consumer imports without a reversed
  dependency, principle 7). Migration: none (already compose-by-name).
  Proof: static-reviewed. Freshness: fields.py dual + schema.py
  `2f727321…` + resource_policy.py `583bf460…`. **Robust-to-both.**
- **F3 — `lazy-root-field-signature` (family nomination, open).**
  Contract: a root field whose return materializes at phase 2.5 carries an
  injected `(__signature__, __annotations__)` with Strawberry-reserved
  `root`/`info` + keyword-only GraphQL args. Sites + roles:
  [mutations-fields][mutations-fields]`::build_lazy_field_signature` =
  definition; `::_synthesized_mutation_signature` = internal consumer;
  [auth-mutations][auth-mutations]`::_make_auth_field` = consumer.
  Challenges: C4 count 1. Owner: fields.py (the write factory owns the
  no-annotation timing that forces the idiom, principle 7). Migration:
  none. Proof: static-reviewed. Freshness: fields.py dual + auth/mutations.py
  `dbe64995…`. **Robust-to-both.**
- **F4 — `write-field-lazy-forward-ref` (family nomination, open).**
  Contract: `Annotated[<name>, strawberry.lazy(<module>)]` names a
  phase-2.5-materialized class. Sites + roles:
  [mutations-fields][mutations-fields]`::_lazy_ref` = definition;
  login/logout/current_user return refs + synthesis sites = consumers;
  [utils-inputs][utils-inputs]`::build_lazy_input_annotation` = rejected
  merge (R5); [filters-inputs][filters-inputs]`::_build_logic_fields`
  self-ref = rejected merge (R6). Challenges: C5 count 1. Owner: fields.py
  (per-flavor `module_path` parameter is the load-bearing divergence:
  `data:` names the flavor namespace while payload names
  `mutations.inputs` — spec-038 Decision 5; folding into the Decision-11
  helper would hide it). Proof: static-reviewed. Freshness: fields.py
  dual + utils/inputs.py `ee31d360…` + filters/inputs.py `06797dc7…`
  (concurrent hunk noted; the cited self-ref line is outside it — still,
  Worker 0 re-checks at settle) + orders/inputs.py `6f6ec946…`.
  **Robust-to-both** as to THIS item's hunk.
- **F5 — `mutation-operation-descriptors` (family nomination, open).**
  Contract: the write-side operation vocabulary (create/update/delete +
  `form` sentinel: id/data args, input kinds, permission actions, flavor
  support). Sites + roles:
  [mutations-operations][mutations-operations]`::MutationOperationDescriptor`
  + predicates = owner; [mutations-fields][mutations-fields] (predicates +
  `input_type_name`/`input_module_path` seams) = consumer; sets.py,
  forms/sets.py, rest_framework/sets.py, inputs.py = further consumers
  (grazed/grep-verified). Challenges: C3 (this file: 0 edits on vocabulary
  change). Owner: operations.py (principle 1: one validated record type +
  driver). Proof: static-reviewed. Freshness: fields.py dual +
  operations.py `16223c6b…` + forms/sets.py `36ce80b4…` + rf-sets.py
  `2c7117d6…`. **Robust-to-both.**
- **F6 — `hostile-directives-containment` (family nomination, open).**
  Contract: consumer `directives=` is validated to a tuple at the
  construction line (bare char-wise types + raising iterators +
  non-iterables → typed `ConfigurationError`). Sites + roles:
  [directives][directives]`::validated_field_directives` = definition;
  [mutations-fields][mutations-fields] (label `"DjangoMutationField"`) +
  list/connection/node/auth factories = consumers (verified by grep +
  full read here). Challenges: label/message change → count 1 (message
  wording intentionally fixed across callers). Owner: directives.py
  (already single-sited; three near-identical copies predate it per its
  docstring). Proof: static-reviewed. Freshness: fields.py dual +
  directives.py `380786cf…` + list_field.py `f357eded…` + relay.py
  `c3c5aea5…` + connection.py `3c4d5dcb…` (concurrent hunk noted;
  unrelated cursor-guard lines — Worker 0 re-checks at settle) +
  auth/mutations.py `dbe64995…`. **Robust-to-both** as to THIS item's hunk.
- **FL1/FL2/FL3 — construction target guard trio (file-local).**
  Contract: reject a non-concrete / non-family / unregistered target with a
  typed `ConfigurationError` at the assignment line, never a raw escape.
  Challenge C7 count 1 (oracles move as media). Second site sought across
  list/connection/node validators (R7: different populations), the auth
  holder seals (R2: seal vs read), and the declaration registries
  (mechanics owner, this trio is their call-site guard, not a copy).
  Proof: static-reviewed against the WORKING tree + oracle rows read
  (hostile `__class__` / `__dict__` / `__eq__` / `__name__` / metaclass
  rows all target the WORKING behavior). **Hunk-touching → pending-settle**
  (no verdict until the hunk lands or reverts; Worker 2 re-checks C7
  against the settled bytes).
- **FL4 — per-operation signature synthesis (file-local).**
  Contract: create `data:` / update `id + data:` / delete `id` /
  `"form"`-sentinel `data:`-only, `data:` via flavor seams, payload ref
  always `mutations.inputs`. Challenge C6 count 1. No second site (auth
  builds its own argument LISTS but calls F3 — consumer, not copy).
  Proof: static-reviewed; pinned by `test_model_flavor_dispatch_unchanged`
  + live signature row. Freshness: fields.py dual + operations.py
  `16223c6b…`. **Robust-to-both.**
- **FL5 — `DjangoMutationField` factory body (file-local).**
  Contract: validate → gate `id` (C3 trigger recorded) → per-call
  sync/async dispatch → stamp → contain directives → `strawberry.field`.
  Passthrough kwargs (`description` / `deprecation_reason` / `directives`)
  mirror every sibling factory's Strawberry-forward shape by necessity
  (each factory names its own; the callee shape is Strawberry's, not a
  package rule). No second write-field factory exists (`register_mutation`
  calls this one). Proof: static-reviewed; pinned by metadata-passthrough
  + directives + live async rows. Freshness: fields.py dual.
  **Robust-to-both.**

### Rejected candidates

- **R1 `shared-write-entry-factory`: not inherited.** Difference: entries
  normalize UNSET kwargs into a flavor pipeline body (+ its async
  boundary); the field dispatcher selects sync/async per call and gates
  `id`, calling the entries by name. One entry factory stays at
  [mutations-resolvers][mutations-resolvers]`::make_resolver_entries`.
  Trigger: a second site synthesizing its own `resolve_sync`/`resolve_async`
  pair instead of calling the seams. (C9.)
- **R2 `sealed-authorization-source`: not inherited.** Difference: this file
  READS `_mutation_meta` (snapshot + `operation`); sealing is owned at
  [mutations-sets][mutations-sets]`::make_meta_validating_metaclass` (+
  `_ValidatedMutationMeta`; auth holder mirrors). Trigger: this file
  writing or rebinding `_mutation_meta`. (C10.)
- **R3 `type-registry-model-type-map`: not inherited.** Difference: the
  ledger check asks "will phase 2.5 bind THIS class" over
  `iter_mutations()` / `iter_form_mutations()`; the type map asks "which
  type serves THIS model". Trigger: consulting `registry.get(model)` from
  this file. (C11.)
- **R4 `one-sync-boundary`: not inherited.** Difference: `_resolve` reads
  the executor mode; it performs no ORM work and opens no boundary (the
  one-boundary rule lives in the resolver/auth bodies). Trigger: ORM work
  or a `sync_to_async` call inside `_resolve`. (C12.)
- **R5 `build_lazy_input_annotation`: not merged into `::_lazy_ref`.**
  Difference: the Decision-11 helper validates + ledgers + names via a
  callback for set families; the field leaf takes a bare
  `(type_name, module_path)` with the per-flavor namespace divergence.
  Trigger: a mutation/auth ref needing validation + ledger recording.
- **R6 `filters/inputs.py` self-ref: not merged.** Difference: filter
  self-recursion inside `filters.inputs` with sequence/non-sequence arms —
  a different namespace and a different contract. Trigger: a shared
  namespace/shape change spanning filter + mutation inputs.
- **R7 read-side target validators: not merged with the guard trio.**
  Difference: registered-`DjangoType` (+ Relay-shape) identity against the
  type registry vs concrete-mutation-protocol + declaration-ledger
  membership. Distinct populations, distinct reasons to change.
  Trigger: one factory accepting both a `DjangoType` and a mutation class.
- **R8 (consumer note, not a rejection).** Message rendering consumes the
  indexed `typed-rejection-value-tail` family (`_safe_arg_repr` everywhere;
  the hunk moves the remaining `__name__` reads to `_safe_class_name`).
  No second renderer defined here. Sibling F1 leaf re-export ruled robust
  to the hunk first-hand — adopted, not re-derived.

## Defects

None. Axis-6 sweep: every flavor's guard present; the fixed-auth
no-target surface carries its own contract (spec-040), not an omission;
the C3 inline mirrors the seam shape with create as inline-True /
predicate-False by design, and the unreachable seam-shape divergence
names no contract row, no feasible consumer shape, and no wire input
that reaches it — a file-local trigger, never a release blocker. No
docstring/body contradiction found (each projection claim verified at
its site); no layering contradiction (form-base import avoided via duck
typing, as documented).

## Pending execution

None. All proofs `static-reviewed`: single-owner records, compose-by-name
consumption, and inspection-grade equivalence (no ordering, transactional,
or async behavior is decided in this file — dispatch only). No
`docs/dry/temp-tests/` scratch created; no shared-tree pytest run made or
owed. Sharded/Postgres cells: `inapplicable by construction` — the target
opens no database, alias, or dialect decision (ledger reads only; all ORM
work lives in [mutations-resolvers][mutations-resolvers] and below).

## Judgment

Zero-edit file item: 19/19 enumerated, six matrix axes discharged against
the real factory surface, six family nominations for Worker 0 (F1–F6, all
robust to the external hunk), three file-local rows (FL1–FL3
pending-settle on the hunk; FL4/FL5 robust), eight rejections with
contract differences + triggers, no defects, no pending execution. The
closest neighbor (sibling F1) stands adopted as robust; nothing here
relitigates it.

## Implementation (Worker 1)

Zero tracked changes. Item-scoped diff state: `git diff 71ec05c435ef… --
django_strawberry_framework/mutations/fields.py` shows ONLY the external
hunk (working `8c60a5c6…` vs HEAD `cf518361…`, +60/-17: guarded
`isinstance` / guarded own-`__dict__` snapshot read / try-except protocol
probe / identity-`is` ledger scan over both ledgers / `_safe_class_name`
import + labels); `git status --short` shows no other touch by this worker
under the item's paths, and the new artifact below is untracked (never
`git add`ed). Nothing edited, reverted, tidied, formatted, or staged; no
pytest run; no ruff run owed (no `.py` touched; `.md` outside ruff scope).

Per-finding robustness: F1, F2, F3, F4, F5, F6, FL4, FL5, R1–R8 =
**robust-to-both** (traced lines byte-identical between `8c60a5c6…` and
`cf518361…` per the `git diff HEAD` first-hand read); FL1, FL2, FL3 =
**pending-settle** (the guard trio IS the hunk; C7 traced against WORKING
bytes only — Worker 0 holds the verdict until the hunk lands or reverts,
then Worker 2 re-runs C7 against the settled bytes; the companion oracle
dirt [test-fields][test-fields] working `53e39ccb…` vs HEAD `db83f239…`
settles with it). Pending entries for Worker 0: (1) add index rows for
F1–F6 (owners/provenance as recorded; suggested holding items are the
`mutation-payload-name`, `mutation-class-marker`,
`lazy-root-field-signature`, `write-field-lazy-forward-ref`,
`mutation-operation-descriptors`, `hostile-directives-containment` family
items); (2) add file-local rows FL1–FL5 for `mutations/fields.py`;
(3) keep FL1–FL3 flagged pending-settle, not verified. Scratch paths: none
created (no `docs/dry/temp-tests/dry-file-mutations__fields/` needed —
zero executions owed).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Read order kept: AGENTS.md, DRY.md,
worker-2.md, plan row (`mutations/fields.py`, unticked), working
target (360 lines, blob `8c60a5c6…`), item-scoped diff (0 bytes vs
`71ec05c4…`; HEAD-vs-work hunk +60/-17 confirmed external),
consumers/tests first-hand, then `## Findings`. No worker-memory
read. No scratch created (static evidence only; no pytest owed or
run). Verdict: **revision-needed** — one blocking artifact
correction at C3/FL5 (wrong agreement table + breaking fix
direction); everything else agrees.

### Own trace (recorded before reading Findings)

Rules re-derived on the WORKING tree, with the count each posited
change forces and the owner I would choose:

| # | Rule | Sites + roles (mine) | Count | Owner (mine) |
|---|---|---|---|---|
| T1 | Payload-name grammar `<Name>Payload` | [mutations-inputs][mutations-inputs]`::build_payload_type` (materializes, `type(f"{mutation_name}Payload", …)`); [mutations-fields][mutations-fields]`::_synthesized_mutation_signature` (predicts, `f"{mutation_cls.__name__}Payload"`); [mutations-sets][mutations-sets]`::build_and_stash_payload` (pass-through + stash, 0 edits); [mutations-resolvers][mutations-resolvers]`::payload_cls_for` (reads stash, 0 edits) | **2** | inputs.py (materializer; pure `payload_type_name_for(base_name)`, fields site becomes a call — timing-safe, only `__name__` needed at construction) |
| T2 | Resolver class stamp | `::MUTATION_CLASS_MARKER` (defines); [schema][schema] + [resource-policy][resource-policy] import the name (consumers) | 1 | fields.py |
| T3 | Lazy signature builder | `::build_lazy_field_signature` (defines); internal synthesis + [auth-mutations][auth-mutations]`::_make_auth_field` (consumers, calls by name) | 1 | fields.py |
| T4 | Lazy forward-ref leaf | `::_lazy_ref` (defines); synthesis sites + login/logout/current_user refs (consumers) | 1 | fields.py (per-flavor `module_path` divergence is load-bearing) |
| T5 | Operation vocabulary | [mutations-operations][mutations-operations] descriptors + predicates (owner); this file consumes `operation_takes_id` / `operation_takes_data` by name (0 edits) | 0 here | operations.py |
| T6 | Directives containment | [directives][directives]`::validated_field_directives` (defines); this file + list/relay/connection/auth (consumers with labels) | 0 here (1 at owner) | directives.py |
| T7 | Construction guard trio | `::_validate_mutation_target` + `::_has_mutation_protocol` + `::_is_registered_mutation_target` (one guard, three functions) | 1 | fields.py (hunk-touching → pending-settle) |
| T8 | Per-op signature synthesis | `::_synthesized_mutation_signature` | 1 | fields.py (file-local) |
| T9 | Factory body + dispatch gate | `::DjangoMutationField`; `takes_id` inline mirrors the **seam shape** ([mutations-sets][mutations-sets]`::resolver_seams` `with_id`), not the signature predicate | 1 + owning seam factory | fields.py (file-local; trigger on seam-shape divergence) |

Reconciliation vs W1: T1–T8 agree (roles, counts, owners, homes).
T9 agrees on the home (FL5 file-local) but **disagrees on the
mechanism W1 records** — see the blocking correction below.

**F1 ruling (confirmed genuine duplication, count 2).** Both
f-strings read first-hand; neither is a call to the other and no
shared helper exists, so a suffix rename forces both to move while
the stash pass-through and `payload_cls_for` need 0 edits. The
fields.py site cannot compose-by-name today (bind has not run at
construction; only `__name__` exists), which is exactly why the
family consolidation (pure name function at inputs.py) is owed —
not evidence the site is a mere consumer. Becomes a family item
with consolidation owed, as W1 nominates.

### Enumeration (member-by-member, own count 19)

`ast.Module.body` on the working file: 19 statements — 1 module
docstring + 10 imports + 1 `MUTATION_CLASS_MARKER` assign + 7
`def`s (`_validate_mutation_target`, `_has_mutation_protocol`,
`_is_registered_mutation_target`, `_lazy_ref`,
`build_lazy_field_signature`, `_synthesized_mutation_signature`,
`DjangoMutationField`). Matches W1's table row-for-row; every
member lands in a family row, a file-local row, a rejection, or
projection/no-rule. Payload-name prediction (line 297) → F1;
`takes_id` inline (line 330) → FL5; directives label +
`async_execution()` (lines 354/337) → F6 consumer + R4. Agree.

### Matrix (judged on the real surface)

1. Cross-flavor: read-side validators enforce a different
population/contract (registered `DjangoType` + Relay-shape vs
concrete-mutation protocol + declaration-ledger membership) —
R7 holds. Directives already single-sited; auth factories call
F3/F4 by name (verified at [auth-mutations][auth-mutations]
`::_make_auth_field` + [auth-queries][auth-queries]`::current_user`).
2. Sync/async: one `_resolve` closure, per-call dispatch; the
entry pair is owned at [mutations-resolvers][mutations-resolvers]`::make_resolver_entries`
(consumed by name; UNSET-normalization + `sync_to_async`
boundary live there, read first-hand). Agree R1.
3. Derived knowledge: F1 confirmed above; input names ride the
flavor seams (never re-spelled); R5/R6 hold (Decision-11 helper
validates + ledgers + takes a callback vs the bare
`(type_name, module_path)` leaf; filter self-ref hardcodes the
filters namespace with list/non-list arms — different
contracts). Agree.
4. Round-trip: marker stamp vs two named reads → F2; signature
vs dispatch-gate pair → file-local (mechanism corrected
below). Agree with correction.
5. Media: oracles spell `CreateItemPayload!` literally (never
import the grammar); projections verified per claim. No oracle
rewritten to read its owner. Agree.
6. Omission: guard fires on every `DjangoMutationField(...)`
call including the `::register_mutation` rider (verified it
returns `DjangoMutationField(...)`); fixed auth surfaces take
no mutation target (different contract, not an omission).
Agree — 0 defects.

### Families ruling (all 6 new + pending-settle)

- **F1 `mutation-payload-name`: CONFIRM family, consolidation
owed** (see ruling above). Folds nowhere: the grammar belongs
to the materializer.
- **F2 `mutation-class-marker`: route, agree.** Single
definition, two named consumers; already compose-by-name.
Transport-specific stamp — folds into no other family.
- **F3 `lazy-root-field-signature`: route, agree.** One
builder, two callers; the write+auth timing idiom is distinct
from the Decision-11 helper. Folds nowhere.
- **F4 `write-field-lazy-forward-ref`: route, agree.**
Per-flavor `module_path` divergence (payload always
`mutations.inputs`, `data:` per-flavor) justifies keeping it
apart from R5/R6. Carry: filters/inputs.py concurrent hunk is
a settle re-check for Worker 0 (cited self-ref line lives in
`_build_logic_fields`, a different function — robust as to
THIS item's hunk).
- **F5 `mutation-operation-descriptors`: route, agree.**
Consumer-only here; principle-1 record + driver at
operations.py. Carry: none from this item.
- **F6 `hostile-directives-containment`: route, agree.**
Consumer-only here; already single-sited at directives.py.
Carry: connection.py concurrent hunk is a settle re-check
(unrelated lines per W1 — accepted with the flag).
- **FL1–FL3 pending-settle: HOLDS (blocking for those rows
only).** Hunk scope confirmed first-hand: `_safe_class_name`
import + exactly the trio (`_validate_mutation_target`,
`_has_mutation_protocol`, `_is_registered_mutation_target`).
C7's hostile axes (raising `__class__` / metaclass /
`__dict__` / `__eq__` / `__name__`) are exactly the axes the
hunk hardens, so working behavior ≠ HEAD behavior and C7 is
traced on working-only bytes. Worker 0 holds FL1–FL3 until
the hunk lands or reverts; Worker 2 re-runs C7 then. The
+60/-17 hunk is external concurrent work — untouched.
- **FL4: agree file-local, robust-to-both.**

### Blocking correction: C3/FL5 mechanism (revision-needed)

W1 records (Matrix 6 + C3 + FL5) that the
`takes_id = operation != "form"` inline "agrees with
`operation_takes_id` on all four reachable operations (create
F/F, …)" and that the trigger's "fix direction is to replace
the inline check with `operation_takes_id`". Both halves are
wrong, verified first-hand:

- For **create**, the inline is **True** (`"create" != "form"`)
while `operation_takes_id("create")` is **False** (descriptor
`has_id_arg=False`). The pair does NOT agree F/F — and the
difference is by design: the inline governs the **dispatch
kwarg** (create passes `id=UNSET` to a seam that requires
`id`), while the predicate governs the **signature arg**
(create omits `id:`). The inline mirrors the seam shape
([mutations-sets][mutations-sets]`::resolver_seams` `with_id`:
default `True`; `False` only for the model-less plain
`DjangoFormMutation`), not the operations table.
- The recorded fix direction **breaks create**: the `with_id`
seam signature is `(cls, info, *, data, id)` with both
required (no defaults), so routing create through
`operation_takes_id` would omit `id=` → `TypeError` on every
create mutation. Reproducible statically (no pytest per
AGENTS.md): [mutations-fields][mutations-fields] line 330 vs
[mutations-operations][mutations-operations] `has_id_arg`
table vs [mutations-sets][mutations-sets]`::resolver_seams`
seam bodies.

Required correction (prose-only, no production touch): C3
must record create as inline-T / predicate-F by design (dispatch
UNSET convention, per the in-file comment), and FL5's trigger
must name the true divergence — a flavor whose `with_id` seam
shape diverges from `operation != "form"` (a second model-less
flavor, or a model-backed `"form"`) — with fix direction
"consult the seam shape (`with_id` on the meta/seam, or probe
the seam), never `operation_takes_id`". The home (FL5
file-local, no defect, unreachable today) is unchanged.

### Rejections, fingerprints, gates, pending, coupling, prose

- **R1–R8: agree.** Each carries its contract difference +
reconsideration trigger; R4/R5/R6 spot-verified first-hand
(`_resolve` performs no ORM work and opens no boundary;
helper signatures/namespaces differ as stated).
- **Fingerprints: all match**, re-hashed myself: fields.py
work `8c60a5c6…` + HEAD `cf518361…`; test_fields.py work
`53e39ccb…` + HEAD `db83f239…`; inputs `fc442047…`, sets
`cffa29e5…`, resolvers `3fd1e571…`, operations `16223c6b…`,
auth/mutations `dbe64995…`, directives `380786cf…`,
utils/inputs `ee31d360…`, filters/inputs `06797dc7…`,
orders/inputs `6f6ec946…`, schema `2f727321…`,
resource_policy `583bf460…`, list_field `f357eded…`, relay
`c3c5aea5…`, connection `3c4d5dcb…`.
- **Zero-edit confirmed:** own-diff `git diff 71ec05c4… --
django_strawberry_framework/mutations/fields.py` is 0 bytes;
`git status` dirt under the item's paths is the external hunk
(plus this untracked artifact) — nothing by this item.
- **Gates:** no new gates owed (zero-edit file item — correct).
F1's gate is honestly recorded as gate-only observation with
the negative control NOT run — accepted at file-item stage;
**carry:** the family item must establish the gate and run
the control. `## Pending execution`: absent — agree (all
proofs inspection-grade; sharded/Postgres
`inapplicable by construction` judged sound: the target opens
no database, alias, or dialect decision — ledger reads only).
- **Coupling:** none marked — agree.
- **AGENTS.md prose:** item diff empty → no violations
possible; artifact citations use `path::Symbol` throughout;
this section reuses existing reference ids (no new link
definitions); concurrent dirt preserved; no commit.

## Defects (Worker 2)

None in production code: the `takes_id` inline is correct as
written (create's `id=UNSET` dispatch matches the `with_id`
seam, as the in-file comment states); the fault is the
artifact's description of it, owned by this item's re-pass —
see the C3/FL5 correction under `## Independent verification
(Worker 2)`, not a card. No enforcement gap, no
docstring/body contradiction, no layering violation found.

## Iterations

Worker 2 pass 1 → `Status: revision-needed`: Worker 1 to apply
the C3/FL5 prose correction only (no production edit, no test
run, no re-trace of other rows), then resubmit to the SAME
Worker 2 for re-verification. FL1–FL3 stay pending-settle
regardless; F1–F6 routing and all fingerprints stand as
verified above.

## Iterations (pass 2)

Worker 1 pass 2 applied Worker 2's blocking C3/FL5 correction prose-only: Matrix 6, C3, and `## Defects` now record create as inline-True / predicate-False by design, the trigger as a flavor whose `with_id` seam shape diverges from `operation != "form"`, and the fix direction as consult the seam shape never `operation_takes_id`; re-derived first-hand that [mutations-fields][mutations-fields]`::DjangoMutationField` line 330 is True for create while [mutations-operations][mutations-operations]`::operation_takes_id` is False, that [mutations-sets][mutations-sets]`::resolver_seams` defaults `with_id=True` with required `(cls, info, *, data, id)` and is `False` only for the plain `DjangoFormMutation`, and that the in-file comment states the `id=UNSET` dispatch convention, so the recorded replace-with-predicate direction would `TypeError` every create; home stays FL5 file-local with no production defect, and `Status` is `ready-for-verification/2`.

Worker 2 pass 2 (same Worker 2, resumed): correction confirmed in
place — Matrix 6, C3, and `## Defects` now record the seam-mirror
mechanism with create inline-True / predicate-False by design and
the consult-the-seam fix direction. Seam facts re-derived
first-hand, trusting neither worker: `resolver_seams`
`with_id=True` default with required `(cls, info, *, data, id)`
and `with_id=False` dataless seam read at the factory, and all
four call sites read — model (`mutations/sets.py` default),
ModelForm (`forms/sets.py:709` default), serializer
(`rest_framework/sets.py:1009` default), plain `DjangoFormMutation`
(`forms/sets.py:1002` `with_id=False`, the only `False` site) — so
`operation != "form"` coincides with the seam shape on every
reachable flavor and the old replace-with-predicate direction
would indeed `TypeError` create. Nothing else changed: Worker 2
sections intact, link block intact, item-scoped diff still 0
bytes, no production file touched, no pytest. F1-duplication
family routing stands (consolidation + gate owed at the family
item). `Status: verified`. Settle rule stated explicitly: this is
plain `verified`, NOT `verified, pending execution` (no deferred
proof exists — `## Pending execution` is absent); FL1–FL3 remain
flagged pending-settle, i.e. verified-on-working-bytes-only, and
the hunk landing or reverting is a fingerprint change that
reopens those rows for a C7 re-run at settle.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->
[dry]: DRY.md
[plan]: dry-0_0_15.md
[worker-1]: worker-1.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[auth-queries]: ../../django_strawberry_framework/auth/queries.py
[connection]: ../../django_strawberry_framework/connection.py
[directives]: ../../django_strawberry_framework/utils/directives.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[execution-mode]: ../../django_strawberry_framework/utils/execution_mode.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutations-fields]: ../../django_strawberry_framework/mutations/fields.py
[mutations-init]: ../../django_strawberry_framework/mutations/__init__.py
[mutations-inputs]: ../../django_strawberry_framework/mutations/inputs.py
[mutations-operations]: ../../django_strawberry_framework/mutations/operations.py
[mutations-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[relay]: ../../django_strawberry_framework/relay.py
[resource-policy]: ../../django_strawberry_framework/extensions/resource_policy.py
[rf-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py

<!-- tests/ -->
[test-fields]: ../../tests/mutations/test_fields.py

<!-- examples/ -->
[products-api]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
