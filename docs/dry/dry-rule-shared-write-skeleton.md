# DRY review: `shared-write-skeleton`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `shared-write-skeleton`. Provisional owner
`mutations/resolvers.py::run_write_pipeline_sync` — CONFIRMED below.
Known member files: `mutations/resolvers.py`, `forms/resolvers.py`,
`rest_framework/resolvers.py`, `auth/mutations.py`. This artifact also
covers the index row `shared-write-entry-factory`
(`mutations/resolvers.py::make_resolver_entries`, members the first three
files), held by this same item. Prior records only as triggers: the
`mutation-error-envelope` verdict (single envelope, all flavors composing)
and the `one-sync-boundary` verdict (single async boundary) were re-verified
against source, nothing inherited. Never read any `worker-memory/`.

Attribution (STOP rule): the plan `## Owned changes` ledger holds no row on
any of the four member paths (rows cover only `optimizer/walker.py`, two
fakeshop live files, `tests/base/test_init.py`,
`tests/optimizer/test_extension.py`, `extensions/error_policy.py`,
`registry.py`, `relay.py`, `list_field.py`, `types/relay.py`,
`types/finalizer.py`, `types/resolvers.py`, `utils/relations.py`,
`tests/utils/test_errors.py`, `mutations/inputs.py`,
`tests/mutations/test_inputs.py`, `types/base.py`,
`inspect_django_type.py` + its test — full read). `forms/resolvers.py` is
clean vs HEAD (worktree blob equals HEAD blob, see Freshness).
`mutations/resolvers.py` + `rest_framework/resolvers.py` +
`auth/mutations.py` carry EXTERNAL concurrent dirt, verified vs
`git diff HEAD`: the hostile-hardening campaign only — safe-renderer imports
plus message-label call sites in `mutations/resolvers.py` (alias guard owner,
two pk-drift messages, delete drift message, `authorize_or_raise` target
names), hook/containment hardening inside serializer adapters in
`rest_framework/resolvers.py` (`_hook_mapping`, `_frozen_hook_view`,
`_merged_serializer_kwargs`, save-kwarg and relation guards, all message
labels), seal/conflict message labels in `auth/mutations.py`. Zero overlap
with any skeleton site (the five rider bodies, the factory, the phase order,
the transaction calls — all byte-identical to HEAD). No dirty path was
edited, so no STOP arose — reading the dirty files was free, and every proof
that mutates source ran in the disposable workspace.

## System trace

Rule: the shared write pipeline skeleton — locate, authorize, decode, write,
tail — spanning the response transaction, shared across the model, form, and
serializer flavors (principle 5: share the lifecycle, keep the adapters).

The exact phase sequence, owned in one body
(`mutations/resolvers.py::run_write_pipeline_sync` —
[mresolvers][mresolvers]):

1. Cooperative deadline (`check_deadline`) BEFORE the transaction opens.
2. Pure derive: `meta` / `primary_type` / payload class / slot / model /
   `needs_locate` (no DB).
3. `open_write_pipeline` (substrate at [wtx][wtx]): managed-alias gate, then
   one nested `transaction.atomic` + pinned pipeline context; yields `using`.
   The `error_payload_builder` closure (rollback-then-envelope) is built here.
4. Locate (update/delete only): `coerce_lookup_id` (typed GlobalID decode +
   pk coerce) -> `locate_instance` (visibility `get_queryset`, pinned alias,
   `select_for_update` lock) -> not-found envelope; then
   `check_instance_write_alias`. Create and plain form skip (`instance None`).
5. Snapshot `authorized_pk` + `target_state` onto the pipeline context —
   before the first consumer-controlled code.
6. `pipeline_alias_guard` spanning every consumer-reachable phase;
   `authorization_phase` wrapping exactly the single `authorize_or_raise`
   call (authorize BEFORE decode — the security invariant); post-auth
   `reject_substituted_row` on update/delete.
7. `decode_step(instance)` -> decoded or `list[FieldError]` (envelope
   short-circuit, rollback marked).
8. `write_step(instance, decoded)` -> saved or `list[FieldError]` (same
   short-circuit; the actual save/delete runs inside the flavor's
   `pipeline_write_phase` window).
9. Tail: `tail_step(saved)` when supplied (delete snapshot payload); else
   `{ ok: true }` for a model-less mutation; else the update pk-drift
   backstop -> `refetch_optimized` (by pk, no visibility filter, G2 plan) ->
   vanished-row `conflict` envelope, else `build_payload`.

Every flavor's pipeline (sync/async per flavor, one shared boundary):

- Model create/update: `_run_pipeline_sync` rides the skeleton with
  `_model_decode_step` / `_model_write_step`. Model delete: `_run_delete`
  rides the same skeleton with a no-op decode, `_delete_write_step`
  (snapshot-then-delete), and a snapshot `tail_step`.
- ModelForm + plain form: ONE body `_run_form_pipeline_sync`
  ([fresolvers][fresolvers]) rides the
  skeleton with `_modelform_decode_step` and a `_primary_type`-picked write
  (`_modelform_write_step` vs `_plain_form_write_step`); plain skips locate
  and takes the model-less tail.
- Serializer (create/update only — delete rejected at bind by
  `require_non_delete_operation`): `_run_serializer_pipeline_sync`
  ([sresolvers][sresolvers]) rides the
  skeleton with `_serializer_decode_step` / `_serializer_write_step`
  (construct, validate, savepoint-contained save, relation attestation).
- Register (create-only): `_run_register_pipeline_sync`
  ([authmut][authmut]) rides the skeleton
  with the password-aware `_register_decode_step` (rides `_model_decode_step`
  + EXCLUDED capture) / `_register_write_step` (validate + hash, then the
  shared model tail) — a fourth decode/write STEP PAIR, not a fourth kit.
- Login/logout/`current_user`: do NOT ride the skeleton (R1 — session
  lifecycle, own transport prologue, native async Channels paths).
- Async everywhere a sync body exists: the SAME sync body through
  `run_pipeline_async` -> `run_in_one_sync_boundary` (the `one-sync-boundary`
  owner), exposed as module entries via `make_resolver_entries`; register via
  `run_in_one_sync_boundary` directly (R2 shape difference only).

Lifetime (principle 4): the outer completion-spanning `atomic` +
`managed_write_transaction` is opened per mutation field by
[schema.py][schema]`::DjangoSchema` (commit/rollback at response
completion); the skeleton nests one per-operation `atomic` via
`open_write_pipeline`; adapter-local savepoints sit inside
(serializer save, model forced save). Stored derivation: [wtx][wtx]
`::WriteAliasContext` (`alias`, `lock`, `authorized_pk`, `target_state`,
`write_phase`, `auth_phase`/`auth_aliases`) — validity one operation,
published immediately after locate before consumer code, mutated by the
skeleton only, invalidated at context exit. No cache, no memo.
Sync/async (principle 5): composed from the `one-sync-boundary` verdict
(single sync body in one boundary; no per-step hops) — verified at the call
sites, not relitigated; the `connection.py` two-colored contrast stands
untouched.

Connected sources read: the four members (full), [wtx][wtx] (full),
[schema.py][schema] execution window, [msets][msets]`::resolver_seams` +
[fields][fields] dispatch, `rest_framework/sets.py` operation gate,
`utils/write_values.py` decode spines ([wvalues][wvalues], via the envelope verdict),
`tests/mutations/test_resolvers.py` ([test-mresolvers][test-mresolvers]) +
`tests/forms/test_resolvers.py` ([test-fresolvers][test-fresolvers]) +
`tests/rest_framework/test_resolvers.py` + `tests/auth/test_mutations.py`
(rider pins + behavior rows), live `test_products_api.py`
([live-products][live-products]) / `test_auth_api.py`
([live-auth][live-auth]) (wire oracles, listed), the two neighbor artifacts
(re-verified, see below). Excluded on strength of body: every other package
module — the gate walks all 117 `.py` and finds skeleton tokens only in the
listed files.

## Verification

### Matrix

1. **Cross-flavor mirroring.** Model, ModelForm, plain form, serializer,
   register ride the skeleton (5 rider bodies, census below); login/logout/me
   separate (R1). Delete rides only via the model arm (serializer/form
   reject it at bind). Adapters differ only in decode projection, write
   construction, and tail shape. Trigger: flavor-local locate/auth/atomic
   code.
2. **Sync/async twins.** One sync body per flavor; all async entries route
   through the shared boundary (`make_resolver_entries` triple +
   `run_pipeline_async`; register direct). No twin pipeline bodies exist.
   Trigger: a second `sync_to_async` wrapper around ORM work (population
   closed by the boundary family).
3. **Derived knowledge.** Alias resolved once per operation
   (`resolve_write_alias` inside `open_write_pipeline`), threaded or read
   from pipeline context — never re-derived per phase. Slot derived once at
   `payload_object_slot`, composed by name. Trigger: a second router call
   per operation.
4. **Round-trip pairs.** No inverse pairs in the skeleton; the error path
   pairs envelope with rollback at exactly one site
   (`error_payload_builder`); adapter savepoint rollbacks are local save
   containment, distinct contract (F1). Trigger: a second envelope-path
   `set_rollback` site.
5. **Other media.** Oracles: rider pins (delete, plain-form), entry-factory
   name test, atomic/snapshot/drift tests, serializer rollback behavior,
   auth envelope rows, live wire envelopes per flavor. Projections: the
   three pipeline module docstrings, the `write_transaction` security model,
   specs 036/038/039/040, [GOAL.md][goal]. Listed, not counted.
6. **Omission.** Eight write surfaces enumerated; authorize-before-decode
   is single-sited so no flavor can omit it by construction; every failure
   arm returns the envelope through the skeleton. Login/logout carry no
   decode/write phases to guard (R1). No defect.

### Enumeration

Instrument: docstring-tolerant AST census over the whole package (117
`.py`, matching the plan inventory) for `def run_write_pipeline_sync`,
`def make_resolver_entries`, their call sites by enclosing function, and
module-level factory assignments; plus token sweeps for
`open_write_pipeline(`, `authorize_or_raise(`, `pipeline_write_phase(`.
Population closed — the census script reports `scanned=117`.

- Definitions (1 each): `run_write_pipeline_sync`, `make_resolver_entries`,
  `error_payload_builder`, `build_payload`, `payload_cls_for`,
  `open_write_pipeline` (+ substrate phases at [wtx][wtx]).
- Skeleton riders (call by name, 5): `_run_pipeline_sync`,
  `_run_delete`, `_run_form_pipeline_sync`,
  `_run_serializer_pipeline_sync`, `_run_register_pipeline_sync`.
- Entry-factory riders (3 module pairs): model, form, serializer
  `resolve_*_sync`/`resolve_*_async`; register custom classmethod pair
  (R2).
- Non-riders: login/logout/me bodies (R1); `connection.py` colored
  pipelines (boundary-family contrast).
- Oracles/projections: as listed in the trace.

### Challenges

Counts are authoritative definitions only; riders, oracles, projections
listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New pipeline phase (e.g. a post-write hook) | **1** (the skeleton body; every rider inherits it; adapter-local work stays in that flavor's `write_step`, 0 new orchestration defs) |
| C2 | New write flavor (new decode/write pair) | **0** new orchestration defs (declare the step pair, ride by call — register is the worked precedent; a new entry pair rides the factory unless its dispatch shape differs, R2) |
| C3 | Phase reorder (decode before authorize) | **1** (the skeleton orders once; all flavors follow by construction — the pre-skeleton shape would force 5+) |
| C4 | Entry-dispatch normalization change (UNSET kwargs) | **1** (the factory; register's hand pair noted at R2) |

Neighbor re-verification (not inheritance): the envelope verdict's rider
table (all flavors composing one leaf/builder/assembly) matches the five
bodies found here; the boundary verdict's `run_pipeline_async` delegation
(`return await run_in_one_sync_boundary(...)`, read at
`mutations/resolvers.py::run_pipeline_async`) matches the async entries
found here. Both stand.

**Experiments (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/shared-write-skeleton
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
python3 /var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/skeleton_gate.py "$WS"
uv run --directory "$WS" python -m pytest <focused id> -n0 --no-cov -q -p no:cacheprovider
```

Copy `__file__`:
`.../dry-ws/shared-write-skeleton/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/shared-write-skeleton/examples/fakeshop/db.sqlite3`
(the copy's own tree and database; the shared tree's database untouched —
shared blobs re-hashed identical after).

Gate (`skeleton_gate.py`, scratch-only): G1 one skeleton def + the five
rider callers; G2 one factory def + the three factory modules; fail-closed
on unparseable files; prints `scanned=117`. Clean copy AND shared tree:
GATE GREEN. Negative controls (WS only, pristine backups kept, restored
after — gate GREEN again post-restore):

- Control A (entry factory): serializer entries replaced by a
  behavior-preserving hand copy of the factory body (same inner
  `resolve_sync`/`resolve_async` names, same delegation, same boundary).
  Result: G2 RED (factory modules 3→2, G1 stays green);
  `test_write_flavors_share_resolver_entry_factory` PASSES (the exact
  [DRY.md][dry] blindness point — the name assertion cannot see the
  bypass); behavior oracle
  `test_save_time_validation_after_partial_write_is_rolled_back` (full
  serializer pipeline incl. skeleton atomic) PASSES.
- Control B (skeleton): verbatim copy of the skeleton body appended in
  `mutations/resolvers.py` under a new name, form rider rerouted to it.
  Result: G1 RED (callers 5→4, G2 stays green); behavior oracle
  `test_perform_mutate_override_runs_only_on_success` (end-to-end
  `schema.execute_sync` through the copy) PASSES; the existing
  plain-form/delete delegation pins FAIL — correctly, they are the two
  already-landed partial gates, and the gap G1 closes is the three
  unpinned arms (model create/update, ModelForm, serializer, register).

One authorized shared-tree focused run (zero member edits in flight on that
file): `tests/forms/test_resolvers.py::
test_plain_form_pipeline_rides_shared_write_skeleton` `--no-cov -n0` →
1 passed.

## Findings

### F1 — write pipeline skeleton (CONFIRMED single-owned, already-single)

- **Contract + variation.** Locate -> authorize -> decode -> write -> tail
  inside one nested transaction, authorize-before-decode fixed. Varies in
  the three seams only: `decode_step` / `write_step` / `tail_step`
  (per-flavor decode projection, construction/validation, tail shape).
- **Sites + roles.** Definition:
  `mutations/resolvers.py::run_write_pipeline_sync` (+ `error_payload_builder`,
  `build_payload`, `payload_cls_for` — envelope-verdict owned). Substrate
  definitions composed by name at [wtx][wtx]. Riders/consumers/oracles/
  projections per trace. No second orchestration exists.
- **Challenges.** C1 → 1; C2 → 0; C3 → 1. Count > 1 nowhere in one rule.
- **Owner + lifetime (principles 7, 4).**
  `mutations/resolvers.py::run_write_pipeline_sync`: the write-side runtime
  owns the mutation ordering; every flavor already depends toward
  `mutations` (envelope verdict confirmed the direction), so no consumer
  reverses a dependency or imports a sibling flavor; `utils` would push
  GraphQL ordering below its consumers, a flavor owner would force sibling
  imports. Lifetime: per-operation nested atomic under the schema's
  completion-spanning transaction; `WriteAliasContext` published post-locate
  pre-consumer-code, skeleton-mutated only, exit-invalidated; nothing
  cached.
- **Migration.** None — already single. Zero tracked edits.
- **Distinct behavior (stays separate).** Model M2M null-reject vs form
  `empty_values` vs serializer `None` pass-through (decoder contracts);
  serializer savepoint + witness vs model forced-save savepoint (adapter
  containment under the one skeleton atomic); delete snapshot tail vs
  refetch tail; register password pair.
- **Behavioral proof.** `execution-verified` (WS: gate GREEN clean +
  shared tree; Control B copy behavior-green with pins failing correctly;
  shared focused run green). `static-reviewed` (5-rider census,
  hunk-vs-cite dirt adjudication, oracle independence).
- **Structural gate.** Design proved in-workspace (G1 + Control B);
  landing DEFERRED with reason: the natural home
  (`tests/mutations/test_resolvers.py`, beside the delete pin) carries
  unsettled external dirt (STOP-fenced), and landing new package tests is
  Worker 0's closeout call after settle keeps pins adjacent; the proved
  `skeleton_gate.py` logic (population = package source, bypass =
  inlined phases) is the owed shape.
- **Coupling.** None.
- **Freshness.** Worktree blobs (`git hash-object`):
  `mutations/resolvers.py` `a322d17a…` (external hunk, zero skeleton
  overlap), `forms/resolvers.py` `4edb984b…` (clean, equals HEAD),
  `rest_framework/resolvers.py` `c0b54039…` (external hunk, zero skeleton
  overlap), `auth/mutations.py` `200805d2…` (external hunk, zero skeleton
  overlap), `utils/write_transaction.py` `eca9ad4d…` (clean),
  `utils/write_values.py` `d28587c7…`, `schema.py` `c2e1b748…` (clean),
  `mutations/sets.py` `936f5ae7…`, `mutations/fields.py` `64410c86…`,
  `tests/forms/test_resolvers.py` `e11002d4…` (clean). HEAD `bfaee91d`;
  brief ITEM_BASELINE `215369da…` (open-time stash `f4a3f0e8…`; zero
  tracked edits under either). Searched population: whole package
  (117 `.py`). Any fingerprint change reopens the finding.
- **Reconsideration triggers.** T-ride fires if a rider body stops
  calling the skeleton; T-phase fires on a second `open_write_pipeline`
  + authorize composition outside it; T-entry fires if a module entry
  stops coming from the factory (F2). No owner-docstring clause added
  (zero-edit confirmation; triggers live here).

### F2 — resolver entry factory (CONFIRMED single-owned, already-single)

- **Contract + variation.** The `(resolve_sync, resolve_async)` pair:
  sync normalizes UNSET kwargs to the flavor body; async runs the same
  body through the shared boundary. No per-flavor variation — the three
  pairs are three calls with three bodies.
- **Sites + roles.** Definition:
  `mutations/resolvers.py::make_resolver_entries`. Consumers: the three
  module entry pairs (model/form/serializer). Oracles: the `__name__`
  test (blind by design — proved) + per-flavor resolve tests.
- **Challenges.** C4 → 1; new flavor entries → 0 (+1 call line).
  Async retune → 0 here (boundary family owns it).
- **Owner + lifetime (7, 4).** Same module as the skeleton (entry to the
  lifecycle it fronts; every flavor already imports it). Stateless
  construction; per-call boundary lifetime owned by the boundary family.
- **Migration.** None. Zero tracked edits.
- **Behavioral proof.** `execution-verified` (WS Control A: gate RED,
  name test + behavior green). **Structural gate.** G2 + Control A
  proved; landing DEFERRED for the same reason as G1 (home file dirty;
  closeout call).
- **Freshness / triggers.** Same fingerprints as F1. T-entry (above) is
  the trigger; home is this finding.

### R1 — session auth bodies (REJECTED consolidation)

Login/logout/`current_user` never ride the skeleton and must not: no row
to locate, no input to decode, no model to write — the lifecycle is
transport capability + permission gate + session establish/teardown, with
native async Channels paths that must await on the loop (a single sync
body is impossible — the boundary family's R3). They compose the envelope
by name (`build_payload_type`, `payload_cls_for`, `resolvers.build_payload`,
`field_error`), already single-owned elsewhere. Shared form considered:
routing session writes through decode/write seams — owns nothing, forces
row-write phases onto a session lifecycle (principles 3/11). Trigger: a
session surface needing row locate/decode/write (register proves the
skeleton accepts such a rider). Home: `auth/mutations.py` bodies + this
finding.

### R2 — register dispatch pair (REJECTED consolidation with the factory)

The `Register` rider's `resolve_sync`/`resolve_async` classmethods are
hand-rolled, not factory-made: the class is synthesized per factory call
(needs bound methods, not module functions), is create-only (`del id`
documents it), and calls the pipeline runner directly. The load-bearing
half (one-worker boundary) IS shared via `run_in_one_sync_boundary`;
only the 3-line kwarg-normalization shape is local. Shared form
considered: a factory create-only mode — owns 3 lines, couples the
generic factory to one synthesized rider (principles 3/11). Trigger: a
second synthesized rider duplicating the pair. Home:
`auth/mutations.py::Register` + this finding.

## Defects

None found while tracing. Two closest candidates examined and cleared
(not defects): serializer/form delete absence is bind-enforced
(`require_non_delete_operation` — contract, with a reaching input
impossible); register's hand dispatch pair shares the boundary primitive
(R2, no divergence). Write-path divergence needs an oracle plus a reaching
mutation — no candidate meets the bar, so nothing routes.

Worker 2 (phase 2): no additional defects. Re-traced the two cleared
candidates against current source (`mutations/sets.py::require_non_delete_operation`
exists and fires at bind; sole synthesized rider is
`auth/mutations.py::_synthesize_register_rider`, so R2's trigger has not
fired) plus the phase-order and transaction hazard sweeps from the phase-1
trace — nothing meets the Trust-boundary bar (contract row + feasible
project shape + reaching input).

## Pending execution

None. All proofs `execution-verified` in the disposable workspace plus the
one authorized shared-tree focused run (1 passed). The proved-but-unlanded
G1/G2 designs carry no `proof:` entry (proofs already ran); landing is
Worker 0's closeout call, not a pending command. `FAKESHOP_SHARDED=1` and
Postgres cells `inapplicable by construction`: counted claims are AST
call-site identities, and behavior proofs are default-alias single-row
writes — the skeleton takes the alias as a parameter and never branches
on it, so phase order is identical on any alias.

## Judgment

The shared write lifecycle is already single-owned: one skeleton body, one
entry factory, one transaction substrate — model (create/update/delete),
ModelForm, plain form, serializer, and register ride all three by name
with named decode/write/tail adapters only; session auth is a genuinely
different lifecycle with its own trigger. No consolidation exists to
perform; the two rejections carry contract differences + triggers + homes.
Both gate designs proved in-workspace with passing negative controls that
the existing name test and behavior oracles cannot see; landing deferred
with reason. Zero tracked edits; item-scoped diff is the new artifact
only.

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
WS tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/shared-write-skeleton`
(restored pristine — gate GREEN post-restore) + gate script
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/skeleton_gate.py`
+ backups
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/control-backups/`
(three pristine copies; shared-tree files untouched — blobs re-hashed
identical after all WS work).

Worker 0 rows: tick Family `shared-write-skeleton` (this artifact,
`ready-for-verification/1`, zero edits, no pending execution); no
`## Responsibility index` change (both rows — `shared-write-skeleton` and
`shared-write-entry-factory` — already held by this item with the
provisional owner and member files covered); no `## Owned changes` row
(nothing landed); no defects to home.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[authmut]: ../../django_strawberry_framework/auth/mutations.py
[fields]: ../../django_strawberry_framework/mutations/fields.py
[fresolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mresolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[msets]: ../../django_strawberry_framework/mutations/sets.py
[schema]: ../../django_strawberry_framework/schema.py
[sresolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[wtx]: ../../django_strawberry_framework/utils/write_transaction.py
[wvalues]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-fresolvers]: ../../tests/forms/test_resolvers.py
[test-mresolvers]: ../../tests/mutations/test_resolvers.py

<!-- examples/ -->
[live-auth]: ../../examples/fakeshop/test_query/test_auth_api.py
[live-products]: ../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Phase-1 independent trace, HEAD bytes primarily; Worker 1's sections not opened.

### 1. Skeleton + factory (sites / roles)

**Skeleton (authoritative definition):** `django_strawberry_framework/mutations/resolvers.py::run_write_pipeline_sync` — the single-sited write orchestration. Phase sequence per current source (each phase's owner in parens):

0. `check_deadline` (resource-policy substrate, `django_strawberry_framework/resource_policy.py::check_deadline`) — BEFORE any transaction opens.
1. `open_write_pipeline` (substrate, `django_strawberry_framework/utils/write_transaction.py::open_write_pipeline`: `require_managed_write` gate + nested `transaction.atomic` + `write_pipeline` pin context; yields the pinned alias). Managed alias itself is opened upstream by `django_strawberry_framework/schema.py::DjangoMutationExecutionContext` (completion-spanning atomic) and published via `managed_write_transaction`.
2. Locate (skeleton body, helpers `coerce_lookup_id` / `locate_instance` / `not_found_error` / `check_instance_write_alias`): update/delete only — GlobalID decode + type-check + pk coerce, visibility-scoped `SELECT ... FOR UPDATE` locate, instance-router re-check. Create and model-less plain form skip (instance None). Immediately after: immutable snapshots `authorized_pk` + `target_state` (`snapshot_target_state`), then `auth_aliases_for_permission_classes` resolution.
3. Authorize (skeleton body, gate `authorize_or_raise` -> `check_permission`; containment `pipeline_alias_guard` + `authorization_phase`, both substrate-owned): alias guard spans permission/decode/validate/write/re-fetch; auth phase permits auth-alias reads for exactly the one permission call, then closes; post-auth `reject_substituted_row` on the immutable snapshot.
4. `decode_step(instance)` (per-flavor adapter): relation-decode + payload build; `list[FieldError]` short-circuits to the error envelope (rollback-marked).
5. `write_step(instance, decoded)` (per-flavor adapter): construct/validate/save; actual writes inside `pipeline_write_phase` (substrate flag the pinned-alias guard consults); `list[FieldError]` short-circuits to the envelope (rollback-marked).
6. Tail (skeleton body, default or `tail_step`): delete's snapshot `tail_step`, else model-less `{ok: true}`, else update pk-drift backstop (`reject_substituted_row`) + `refetch_optimized` (by pk, no visibility filter, optimizer-planned) + `build_payload`. All error returns go through `error_payload_builder` (definition: `set_rollback(True)` BEFORE payload build on every envelope path).

**Entry factory (authoritative definition):** `django_strawberry_framework/mutations/resolvers.py::make_resolver_entries` — returns fresh `(resolve_sync, resolve_async)` per call. `resolve_sync` normalizes `UNSET`-default `data`/`id` kwargs to the sync body positionally; `resolve_async` runs the SAME sync body through `run_pipeline_async` -> `run_in_one_sync_boundary` (one `sync_to_async(thread_sensitive=True)` call; ORM never interleaves with awaits). Callers: model (`resolve_mutation_sync`/`resolve_mutation_async`), form (`forms/resolvers.py::resolve_form_sync`/`resolve_form_async`), serializer (`rest_framework/resolvers.py::resolve_serializer_sync`/`resolve_serializer_async`). Async twins share one sync body + execution adapter (the DRY principle-5 correct answer for this axis: ORM-in-transaction must not interleave with awaits).

**Substrate roles (consumer-by-composition, not definitions of the sequence):** `open_write_pipeline`, `require_managed_write`, `managed_write_transaction`, `pipeline_alias_guard`, `authorization_phase`, `pipeline_write_phase`, `require_write_pipeline`, `reject_substituted_row`, `pin_write_queryset`, `check_instance_write_alias`, `snapshot_target_state` — all `utils/write_transaction.py`. Reused helpers (`payload_cls_for`, `save_or_field_errors`, `refetch_optimized`, `build_payload`, `locate_instance`, `coerce_lookup_id`, `authorize_or_raise`, decode spine `utils/write_values.py::decode_provided_fields` family) are CALLED by riders, never re-spelled.

### 2. Every flavor pipeline — ride vs reimplement

- Model create / update (sync + async via `_run_pipeline_sync`): RIDES skeleton with `_model_decode_step` / `_model_write_step` adapters. Verdict: consumer.
- Model delete (`_run_delete` -> `_delete_write_step` + snapshot `tail_step`): RIDES skeleton (no-op decode, snapshot-before-delete write, snapshot tail). Verdict: consumer.
- ModelForm create / update (`forms/resolvers.py::_run_form_pipeline_sync` -> `_modelform_decode_step` / `_modelform_write_step`): RIDES skeleton; both form bases share one dispatcher call. Verdict: consumer.
- Plain form (`_run_form_pipeline_sync` with `_plain_form_write_step` -> `perform_mutate`, model-less tail): RIDES skeleton. Verdict: consumer.
- Serializer create / update (`rest_framework/resolvers.py::_run_serializer_pipeline_sync` -> `_serializer_decode_step` / `_serializer_write_step`): RIDES skeleton. Serializer-only machinery (kwargs merge, agreement guards, queryset scoping/validator pinning, intent ledger, witness, attestation) lives INSIDE its `write_step`, i.e. post-auth inside the skeleton order. Verdict: consumer.
- Auth register (`auth/mutations.py::_run_register_pipeline_sync` -> `_register_decode_step` / `_register_write_step`, create-only, `EXCLUDED`-kind password captured out of construction, hashed before the shared model tail): RIDES skeleton unchanged. Verdict: consumer. Note: its resolver pair (`Register.resolve_sync`/`resolve_async` classmethods) is BESPOKE, not via `make_resolver_entries` (see counts/candidate).
- Auth login (`_login_resolve_body` / `_login_resolve_body_async` via `_login_authenticate`): DOES NOT RIDE — separate session state machine (transport prologue -> gate with `data={"username"}` only -> preflight -> single `authenticate` -> payload-before-mutation -> establish). No locate/decode/write/tail, no pipeline transaction. Calls `authorize_or_raise` BY NAME (consumer of the auth gate, not of the skeleton). Not a reimplementation: different operation, no shared contract.
- Auth logout (`_logout_resolve_body` / `_logout_resolve_body_async` via `_logout_prologue`): DOES NOT RIDE — same reasoning (prologue -> gate -> observation-before-teardown -> native teardown). Gate consumer only.
- Auth me (`auth/queries.py::_current_user_resolve_body`): DOES NOT RIDE — read-only query (actor resolve -> gate -> nullable return). Gate consumer only.
- Auth field construction (`_make_auth_field` + `_sync_bridged_async_body`, dispatch via `async_execution`): separate auth-field rule, out of this family; named here only to exclude it.

Phase-order check (every rider traced): all six skeleton riders run locate -> authorize -> decode -> write -> tail with authorize strictly BEFORE decode (login additionally gates before `authenticate`; logout gates before teardown; me gates before return). No flavor skips, reorders, or writes before auth. The serializer's extra reads/writes (scoping, validators, intent, drift check, save) all sit inside `write_step`, i.e. post-auth by construction.

Transaction check: boundaries nest as savepoints, not competing transactions — schema completion-spanning atomic (outer, commits only after response completion) -> skeleton nested atomic per operation (per-operation isolation; rollback via exception or envelope `set_rollback`) -> adapter savepoints (serializer save `transaction.atomic`, model `forced_save_or_field_errors` savepoint) with exceptions caught OUTSIDE the savepoint so `needs_rollback` clears. Every `list[FieldError]` return is rollback-marked before a query-free payload build; `ConfigurationError` drift/router/guard failures propagate through the atomics (rollback by exception). No nested-atomic hazard, no missing-rollback-on-adapter-failure, no cross-alias escape (guard + `pin_write_queryset` + instance-router re-check traced).

### 3. Definition counts (change challenge)

- New phase (e.g. insert a post-write notification step between write and tail; or split decode into scalar/relation sub-phases): count 1 — `run_write_pipeline_sync` owns the sequence; riders supply only `decode_step`/`write_step`/`tail_step` callbacks and spell no order.
- New flavor (e.g. a bulk or new model-backed op): count 1 dispatcher body + one factory use — the new decode/write pair is the declared adapter variation (principle 5), not a new sequence definition.
- Phase reorder (e.g. authorize after decode; locate after auth): count 1 — order lives only in the skeleton; no rider can reorder (adapters are invoked in skeleton order).
- Entry normalization (e.g. change `UNSET`-default handling or the async boundary): count 2 — the factory (owns model/form/serializer entries + the `run_pipeline_async` boundary) PLUS the register bespoke pair (`Register.resolve_sync`/`resolve_async`: create-only classmethods, no `UNSET` defaults, 3-arg body, direct `run_in_one_sync_boundary` call bypassing `run_pipeline_async`). See candidate.

### 4. Owners I would choose

- Sequence: `mutations/resolvers.py::run_write_pipeline_sync` (current owner — confirmed; narrowest cohesive owner every flavor can import without a sibling-flavor dependency; dependency direction beats transport-module placement per principle 7).
- Transaction/alias substrate: `utils/write_transaction.py` (current home — confirmed; transaction + alias + lock responsibility already lives there and is importable without a utils->mutations inversion).
- Entry shape: `mutations/resolvers.py::make_resolver_entries` (current owner — confirmed; the entry is the skeleton's front door and belongs with it).
- Auth gate: `mutations/resolvers.py::authorize_or_raise` (current — confirmed; auth surfaces already consume it by call).

Candidate (named, NOT demanded; zero-edit constraint): migrate `Register.resolve_sync`/`resolve_async` onto `make_resolver_entries` via a 4-arg adapter (owner: `mutations/resolvers.py`; migration: register body gains the `(mutation_cls, info, data, id)` shape with create-only `id` ignored, factory owns the pair). Reason it stays a candidate: different binding (classmethod on rider vs module entries), different arity/defaults, and the factory's fresh-function identity contract needs checking against the field factory's comparisons. No production edit proposed.

### 5. Defects

None meeting the Trust-boundary bar (contract row + feasible project shape under supported public API + wire/configuration input that reaches it). Explicit attention as charged: no phase-order hazard (all riders authorize-after-locate-before-decode; login/logout/me gate-before-effect), no transaction hazard (savepoint nesting, envelope rollback marking, exception-path rollback all traced). The entry-normalization count-2 above is a consolidation candidate, not a defect — no wrong behavior posited.

Oracles READ (not executed, per workspace rules): `tests/mutations/test_resolvers.py::test_write_flavors_share_resolver_entry_factory` (name-only gate — asserts `__name__` thrice; passes a hand copy, so it is an existence assertion, not a single-body proof — noted, not faulted), the managed-alias atomic scaffold test, the pipeline snapshot/drift scaffolds, the hostile-name pipeline tests, `tests/forms/test_resolvers.py` plain-form rider test; serializer + auth suites sampled for rider coverage.

### 6. Freshness fingerprints

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
- Worktree `git hash-object` (dirty members worktree-first, HEAD-second): `mutations/resolvers.py` worktree `a322d17a44820c09a2b876e263fd25dc58cf753b` vs HEAD `3fd1e57199b6366a8bc0b1661518e8bc8949ece4` (D dirty); `rest_framework/resolvers.py` worktree `c0b5403979692f695d89d998121027e3b6afaf62` vs HEAD `8024703ec0fb09758daeec0585e0065de1c61fc3` (D dirty); `auth/mutations.py` worktree `200805d226ce7569e61ff9314189328b2df489e4` vs HEAD `dbe64995b87240b87a1d5119f46cc42c7cab646f` (D dirty); `forms/resolvers.py` `4edb984b299b4e2a71492e73382558b01865f48a` clean (matches HEAD); `utils/write_transaction.py` `eca9ad4d3f765964df05884e080eb3ea63190ca8` clean (matches HEAD).
- Dirty-hunk attribution (`git diff HEAD -- <path>`, inspected without editing): the `mutations/resolvers.py`, `auth/mutations.py`, and `rest_framework/resolvers.py` hunks are concurrent hostile-hardening (`_safe_class_name` label rendering; serializer hook-view/guard hardening) — they touch messages/guards around the skeleton, not the phase sequence, transaction boundaries, or factory; preserved as concurrent work, out of scope for this item. No status set; no verdict on Worker 1's work proposed.

PHASE-1-TRACE-RECORDED — artifact: `docs/dry/dry-rule-shared-write-skeleton.md`

## Iterations

### Phase 2 reconciliation (Worker 2, 2026-09-21, HEAD `bfaee91d`)

**Phase-1 integrity.** Stated: the phase-1 trace above was recorded blind —
appended via shell redirect without opening any other artifact section, before
this phase disclosed Worker 1's record. No phase-1 sentence was edited in
phase 2 (the two phase-2 edits on this artifact are the `Status:` line and
the `## Defects` Worker-2 line only). Where phase-1 framing proved wrong on
re-examination (C2/C4, candidate placement — below), the correction is
recorded here, the original left intact.

**Per-claim reconciliation.**

- Attribution: AGREE. Phase-1 diff inspection corroborates zero skeleton
  overlap; phase 2 additionally confirmed the plan `## Owned changes` ledger
  holds no row on any of the five member paths (section-wide grep, exit 1).
- Sites: AGREE. Phase-1 independently found the same 5 rider bodies (my 6
  flavor rows = their 5 bodies; form's two flavors share one dispatcher),
  the same 3 module entry pairs, the same substrate, and the same non-rider
  exclusions (login/logout/me + connection contrast).
- C1 new phase → 1: AGREE. C3 reorder → 1: AGREE.
- C2 new flavor → 0 orchestration defs: CONCEDED (phase 1 counted the new
  body as 1; orchestration definitions are 0 — the step pair is new
  variation, register is the worked precedent).
- C4 entry normalization → 1: CONCEDED with correction (below). UNSET
  defaults live only in the factory; the register pair carries none.
- Owner (skeleton + factory at `mutations/resolvers.py`, substrate at
  `utils/write_transaction.py`, principle-7 dependency-direction reasoning):
  AGREE. Lifetime (schema-spanning atomic → skeleton nested atomic →
  adapter savepoints; `WriteAliasContext` post-locate, skeleton-only,
  exit-invalidated): AGREE.
- R1 session auth rejection: AGREE (matches the phase-1 non-rider verdicts;
  the native-async-Channels impossibility note is consistent with them).
- No-defect clearings: AGREE, evidence-backed —
  `mutations/sets.py::require_non_delete_operation` confirmed present (bind
  gate exists), and the sole `_synthesize_` site in `auth/` is the register
  rider, so R2's trigger has not fired.
- `## Pending execution` None + sharded/PG inapplicability reason
  (AST identities + alias-parametrized phases): ACCEPTED — matches the
  phase-1 transaction analysis (order identical on any alias; savepoints
  alias-parametrized).

**Load-bearing dispute SETTLED: phase-1 candidate WITHDRAWN, R2 stands —
with corrected reasoning.** Phase 1 compared the register pair against the
wrong rule (`make_resolver_entries` module-entry normalization). Phase 2
found the true comparator: `mutations/sets.py::resolver_seams`, the
classmethod-seam factory single-siting the eight base bodies. Decisive
evidence: the consumer `mutations/fields.py::_resolve` calls
`mutation_cls.resolve_sync/resolve_async(info, **call_kwargs)` uniformly,
passing `id=` for every operation except the plain `"form"` sentinel — and
register is operation `"create"`, so the dispatcher passes `id=UNSET` and
the register seam `(cls, info, *, data, id)` + `del id` is EXACTLY the
`with_id=True` seam shape. Consumer-visible contract: identical. R2's three
stated sub-reasons (synthesis needs bound methods / create-only / direct
runner call) are therefore relocatable implementation details, not contract
differences — a no-generic-change migration is mechanically possible (4-arg
module adapter dropping `id` + a `resolver_seams` call in the class body).
Nevertheless R2's CONCLUSION stands, because the change challenge fails to
relieve any obligation: kwarg-evolution (the likeliest entry-shape change)
costs 2 sites today (`resolver_seams` + hand pair) and still 2 after
migration (`resolver_seams` + adapter) — relocation, not removal; a
delegation-mechanism change would not force the direct-calling pair to move
at all (1→1); UNSET/boundary changes do not touch the pair (no defaults,
direct boundary primitive). Per DRY.md, a finding relieving no change
obligation is not a finding. Separation basis, corrected: same consumer
contract, but fusion into one site buys no change-obligation relief while
adding adapter machinery (principles 3/11); durable home stays
`auth/mutations.py::Register` + R2. Trigger (unchanged): a second
synthesized rider hand-duplicating the pair.

**Gate-deferral judgment: STANDS-DEFERRED (not revision-needed).** G1/G2
designs accepted: Controls A/B are the DRY-mandated negative controls with
stated outcomes (hand-copy bypass → gate RED while name test + behavior
oracles stay green), run in-workspace with restore-to-green; Worker 2 does
not re-run proofs it cannot authorize, and the record supplies commands +
outcomes + restoration. Landing is deferred because the natural home
(`tests/mutations/test_resolvers.py`, beside the delete pin + factory name
test) is STOP-fenced dirt — confirmed still dirty at phase-2 time — and no
elsewhere-clean home is natural: the only clean flavor file
(`tests/forms/test_resolvers.py`, confirmed clean) would fracture a
package-wide gate by flavor, and a new file would violate least-action for
a two-gate landing Worker 0 already owns. Unblock conditions: the home file
settles → Worker 0 lands G1/G2 beside the sibling pins; if still fenced,
Worker 0 records designs + triggers in `## Outcomes` (the durable record
for untracked artifacts). No `proof:` entry is owed — proofs already ran.

**Freshness re-hashed (phase 2, HEAD unchanged `bfaee91d`).**
`mutations/resolvers.py` `a322d17a…`, `utils/write_transaction.py`
`eca9ad4d…` (clean), `forms/resolvers.py` `4edb984b…` (clean),
`rest_framework/resolvers.py` `c0b54039…`, `auth/mutations.py`
`200805d2…` — all five identical to phase-1 values; no drift. Dirty-hunk
attribution unchanged (concurrent hostile-hardening, zero skeleton
overlap); nothing edited, nothing reverted.

**AGENTS.md prose on the empty diff.** Zero tracked edits is the correct
zero-edit-family outcome; the item-scoped diff is the untracked artifact
only. Citations use `path::Symbol` (raw `path:NN` absent); the link-definition
block keeps all 10 canonical group headers; scratch paths are the
DRY-required explicit removal record, not process provenance; no TODO
anchors, no CHANGELOG, no new files. No ruff/format gate applies (no `.py`
touched). Concurrent dirt preserved throughout; no commit.

**Verdict: `verified`.** F1/F2 confirmed already-single, R1/R2 rejections
sustained (R2 on corrected grounds), gates proved with legitimate deferral,
no defects, no pending execution.

**Exact plan rows for Worker 0.** Tick Family `shared-write-skeleton`
(this artifact, now `verified`, zero tracked edits, no pending execution).
No `## Responsibility index` change (both rows already held by this item;
index rows `shared-write-skeleton` + `shared-write-entry-factory` stay
`open` → tick with the item). No `## Owned changes` row (nothing landed).
No defects to home. Scratch removal by Worker 0 after closeout, by explicit
path only: `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/shared-write-skeleton`,
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/skeleton_gate.py`,
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/control-backups/`.
Landing note: G1/G2 land beside the sibling pins in
`tests/mutations/test_resolvers.py` once its STOP fence clears; if still
fenced at closeout, record designs + T-entry triggers in `## Outcomes`.
