# DRY review: `type-registry-model-type-map`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-registry-model-type-map`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F1 aspects).
Plan-named members: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/finalizer.py`,
`django_strawberry_framework/types/base.py`,
`django_strawberry_framework/types/definition.py`,
`django_strawberry_framework/types/relay.py`,
`django_strawberry_framework/types/resolvers.py`,
`django_strawberry_framework/optimizer/extension.py`,
`django_strawberry_framework/optimizer/walker.py`,
`django_strawberry_framework/permissions.py`,
`django_strawberry_framework/utils/querysets.py`,
`django_strawberry_framework/utils/inputs.py`,
`django_strawberry_framework/mutations/sets.py`,
`django_strawberry_framework/auth/mutations.py`,
`django_strawberry_framework/testing/relay.py`,
`django_strawberry_framework/management/commands/inspect_django_type.py`
(all fifteen read in full at the map-relevant sections; `HEAD` is `bfaee91d`;
`ITEM_BASELINE` is `4016227cb1f049de2622eef0ae816de44c1fd56b`).
Prior records used only as triggers, never verdicts: the registry file
item's F1 aspects (`docs/dry/dry-file-registry.md`, verified) + the three
verified siblings (`type-registry-enum-cache`, `type-registry-definition-store`,
`type-registry-pending-ledger` — their F1/F2/F3/F4/F5 boundary statements
checked, not inherited; every edge below re-derived, including the
definition-store item's routed `model_for`-vs-`model_for_type` read-rule
question, judged here). Never read any `worker-memory/`.

## System trace

Rule: the model-to-type map answers "which `DjangoType` serves this model".
Exact-key multi-map with an optional declared primary: many types per model,
at most one primary, one model per class, no empty-list residue. Reads are
pure per-call derivations; writes happen once per type at class creation
through the atomic register-plus-define pair. No hierarchy walk exists:
a proxy, an MTI child, or any subclass resolves only under its own exact
key, and an unregistered key returns `None` — each consumer then follows
its own loud/soft contract (axis 6 table).

Boundary against the sibling families on the one class (re-derived, agrees
with all three siblings): F1 owns `_types` / `_primaries` / `_models` plus
`register` / `unregister` map arms / `get` / `model_for_type` / `iter_types` /
`primary_for` / `types_for` / `models_with_multiple_types` /
`_detach_type_from_model`; F2 owns `_definitions` plus the atomic pair and
both accessors; F3 owns `_pending` plus identity-matched add/discard; F4
owns `_enums` plus the pair; F5 owns `_finalized` plus the guard and the
flip. The `_types` / `_primaries` / `_models` resets inside `clear()` and the
subset drops inside `unregister` are those lifecycles consuming F1 state,
not second definitions — the same treatment every sibling gives the store,
ledger, and cache arms.

Sites + roles. *Definitions* (one each, probe-pinned S1–S10): `register`,
`unregister`, `get`, `model_for_type`, `iter_types`, `primary_for`,
`types_for`, `models_with_multiple_types`, `_detach_type_from_model`, the
three dicts (constructed once in `__init__`), the singleton `registry`
(publication). Sole production writer: `DjangoType.__init_subclass__`
(via `register_with_definition`, [base][base] single call line; zero direct
production `register(` callers, S8). *Resolvers* (`registry.get`, 16 calls
in 12 files, S1): the finalizer Phase-1 drain + connection synthesis (2),
the walker root map + relation fallback (2), the mutation binder + override
shape probe (2), the filter target resolver + child-owner fallback (2), and
one each in permissions cascade, serializer strict read, auth user-primary
bind, `related_target_for`, relation-resolver visibility check, Relay
model-label decode, schema audit, and `related_visibility_queryset`.
*Reverse readers*: `model_for` (alias read, 14 calls in 5 files: root relay,
mutation resolvers, permissions, types relay, querysets-internal) vs
`model_for_type` (index read, 3 calls in 2 files: extension twice, inspect
once) — R-B. *Scanners*: `iter_types` (extension audit, 1), 
`models_with_multiple_types` (finalizer materialization, 1), `types_for` +
`primary_for` (ambiguity audit + both binders, 5 + 3), `iter_definitions`
by-name scans (inspect bare-name resolver; Relay decode via F8 — adjacent
families, R-F). *Validity-keyed caches* (consumers, R-H): `related_target`
memo (`is_finalized` key), optimizer plan cache (origin-identity key),
connection-class cache (type-identity key, evicted/purged), set-owner
bindings (set-lifecycle families). *Oracles*:
[test-registry][test-registry] (round-trip, lone fallback, ambiguity triple,
reverse collision, idempotence, flip raises, rollback pair, order, clear
map/primary arms, unregister subset/purge/noop/guard rows, audit rows),
[test-converters][test-converters] (primary resolution ×3, ambiguity
surfacing), [test-finalizer][test-finalizer] (ambiguity wording, missing
primary definition), [test-permissions][test-permissions] (proxy target,
secondary-never-cascades, unregistered skip), live multi-type + node
refetch rows. All spell literals independently; none enumerates the owner.
*Projections*: the `get` 3-state docstring, the `_detach` shared-inverse
docstring, the audit + binder docstrings (incl. the auth D16 cross-cite),
the `model_for` caller-responsibility docstring, [spec-018][spec-018]
(primary truth + ambiguity), [spec-036][spec-036] Decision 11 (bind error
shapes), [spec-031][spec-031] Decision 8 (model-label routing via `get`).

Connected sources read for judgment, outside the members:
[filters-sets][filters-sets] (owner-aware pair + child-owner branch —
beyond-list consumers, inventoried), [serializer][serializer] (strict read —
beyond-list consumer), [root-relay][root-relay] + [mutation-resolvers][mutation-resolvers]
(`model_for` callers — beyond-list, inventoried), [list-field][list-field] +
[testing-relay][testing-relay] (alias-vs-canonical guards — F2-adjacent,
checked not claimed), installed `.venv` Django (`related_model`
exact-class semantics — behavior anchor, not fingerprinted). Excluded on
strength of body: every other package module (zero map-accessor calls in
the S1–S10 AST census over the 117-file copy population); `utils/inputs.py`
(zero map calls — membership correction below, not a silent drop).

Membership corrections for Worker 0: `utils/inputs.py` is NOT a map site
(its `registry` tokens are `clear()`-lifecycle prose plus its own
`_collision_registry`, the set-naming rule owned elsewhere — AST-proved,
S1–S10). Conversely the family is larger than the fifteen: `filters/sets.py`
(2 `get` calls), `rest_framework/serializer_converter.py` (1), `relay.py`
(3 `model_for` calls), and `mutations/resolvers.py` (5 `model_for` calls)
are map consumers the provisional list omits — inventoried above, no new
index row owed (all covered by this family row).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** Three primary-resolution error
   shapers (mutation binder, auth binder, serializer strict read) share the
   getter + split protocol and differ only in surface wording (R-D, R-E).
   Filter owner-aware reads vs direct `get` are temporal phases of one
   answer (R-F). Declaration ledgers are pre-bind per-flavor lists, a
   different subject (checked, owned by the sealed-authorization families).
   No flavor keeps a second model-to-type map (S1–S10 census).
2. **Sync/async twins.** Zero `AsyncFunctionDef` in all five
   map-adjacent modules (AST-verified in the shared tree: registry 30/0,
   base 32/0, finalizer 42/0, definition 8/0, relations 3/0). Every
   accessor is in-memory dict work; sync and async consumers call the same
   colorless getters. Trigger: a map accessor touching the DB or awaiting.
3. **Derived rather than repeated knowledge.** `get` 3-state, `types_for`
   snapshot, `models_with_multiple_types` one-shot generator, and the
   decode/name scans are pure per-call derivations, deliberately uncached.
   No production site scans definitions by model (S11: zero
   `definition.model ==`; the single `is not None` read is the set-owner
   compat guard, R-A). `graphql_type_name` derived once (F2, checked).
   `definition.primary` zero package reads (F2 C6, checked). Trigger: a
   second derivation site for any of these.
4. **Inverse / round-trip pairs.** register/unregister, register/get/
   model_for_type, pair/rollback (F2), add/discard identity (F3),
   mark/is/clear-reset (F5) — all pinned by the oracles above. No un-map
   primitive besides `unregister` (one type) and `clear()` (all) by design.
5. **Contracts restated in another medium.** Production (owner + sole
   producer + 16 resolvers composing by name); oracles (independent
   literals, plain classes + real models, no owner reads); projections
   (docstrings verified against bodies; specs pin the primary truth, the
   bind shapes, and the model-label routing). No consumer restates which
   type serves a model: every site calls the owner.
6. **Enforcement by omission.** Every `registry.get`_None arm audited —
   loud at build (finalizer unresolved/ambiguity, decode, both binders,
   serializer strict read, synthesis degrade-or-raise), soft at runtime
   (cascade skip, default-manager fallback, visibility `None`, warn audit,
   `_meta` fallback, `related_target_for` `None`, filter `None`), display
   only (inspect). No site lacks the arm its contract requires: no defect.
   The walker `_meta` fallback and the default-manager fallback are
   documented graceful-degradation policies with oracles, not gaps.

### Enumeration

Instrument: AST call/attribute census over the 117-file package population
(`git ls-files django_strawberry_framework | grep -c` = 117, re-counted;
executed inside the WS copy as probe steps S1–S14, 83/83 with the M-series)
plus token greps in the shared tree for prose/code separation. Every map
member assigned; every challenge ends in the family row or a recorded
rejection (no file-local row — each overlap has its owning family or
rejection recorded).

- `registry.get`: 16 code calls in exactly 12 files (S1; prose mentions in
  base/testing-relay/walker/definition/finalizer/filters-sets/auth/types-relay/querysets
  docstrings excluded by AST shape).
- `model_for_type`: 3 calls in 2 files (S2). `primary_for`: 3 calls in 1
  file (S3). `types_for`: 5 calls in 3 files (S4). `iter_types`: 1 (S5).
  `models_with_multiple_types`: 1 (S6). `register_with_definition`: 1
  producer (S7). Direct `register(`: zero production callers (S8).
  `add_pending_relation`: 1 producer (S9, F3 anchor).
- `_types` / `_primaries` / `_models` attribute reads: `registry.py` only
  (S10). `definition.model ==` scans: zero (S11). `definition.model is not
  None`: finalizer compat guard only (S12). Both-`get`-and-`types_for`
  files: exactly the two binders + the audit (S13). `model_for` callers:
  exactly 5 files (S14).

### Challenges

Counts are authoritative definitions only; resolvers, reverse readers,
scanners, caches, oracles, projections listed, never counted. Workspace
probes M1–M18 map one-to-one onto C1–C5 (83/83 `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | New model inheritance shape (proxy type for a proxy model; MTI-child type; unregistered subclass of a registered model) | **1** (exact-key `register`/`get`; no hierarchy walk exists to move). Probes M13/M14 + oracle `test_proxy_target_filtered_default_manager_composes` (proxy resolves by its own key). |
| C2 | Second type claiming one model (secondary view; duplicate-primary collision; ambiguous read; build-time audit) | **1** (the owner predicate + storage; the audit, both binders, and all 16 resolvers are enforcement/consumers adapting to the contract, listed not counted). Probes M5–M7/M12/M17 + oracles below. |
| C3 | `clear()` / `unregister()` lifetime (retain vs drop the map arms) | **1** per arm (`clear()`'s 3-dict drop; `unregister()`'s detach + primary purge). The F1/F4 boundary from the enum-cache item CHECKED, not inherited: unlike the F2/F3 D1 gap (which names `_definitions`/`_pending` only), the map arms are fully asserted — `test_clear_drops_all_state`, `test_clear_resets_primaries`, the unregister subset/purge/sibling rows. Probes M10/M11. |
| C4 | Answer model-to-type by scanning definitions (`definition.model ==`) | **0** (no such site; S11 census; the one `is not None` read is owner-compat, R-A). Consolidating that direction would put request-time resolution behind a linear walk. |
| C5 | Unify the reverse read on the index (`model_for` → `model_for_type`) | **2** coexisting readers, intentionally separate (R-B): unifying rewrites the failure mode (`AttributeError` → `None`) at 14 call sites and adds a registry import to an import-free helper. Probes M15/M16 pin both modes. |

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/model-type-map-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_model_type_map.py
```

Proof (`CHECKS_PASSED=83/83`): empty/fallback/idempotence/flip/ambiguity/
collision/order/reverse-collision/rollback/clear/unregister/split-protocol/
proxy/MTI/alias-vs-index/stale-split/audit/walker-fallback behaviors plus
the S1–S14 AST censuses. Status: `execution-verified`. Rejects "a second
map exists", "resolution walks the hierarchy", "ambiguity resolves",
"clear/unregister leave map residue", "the alias and the index agree
post-teardown", "a model-keyed definition scan exists". Copy `__file__`:
`.../dry-ws/model-type-map-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/model-type-map-w1/examples/fakeshop/db.sqlite3` (copy's own
tree and database; never the shared tree; the probes open no DB at all).
No source mutation in the proof; searched population inside the copy: 117
`.py` (matches the shared tree). `grep -c truncated` == 0.

**Negative control N1 (executed, disposable workspace).** Backed up the
copy's `registry.py`, mutated `get` to first-wins on ambiguity, re-ran the
probe: fails exactly at `M5-get-none-ambiguous` + `M12-ambiguous-split`
(81/83, exit 1). Restored the backup, re-ran: 83/83; copy md5 identical to
pre-mutation and `diff` vs `git show HEAD:` byte-empty. The standing suite
rows (`test_get_returns_none_when_multiple_and_no_primary`, the ambiguity
audit rows) pin the same contract in CI — the mutation that breaks the
probe breaks those rows' shape too. Status: `execution-verified`.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "register or get or
primary or types_for or ambiguity or unregister or multi or iter_types or
clear_drops or clear_resets"` → 54 passed, 26 deselected (round-trip,
lone fallback, ambiguity triple, collisions, idempotence, flip raises,
rollback pair, order, clear map/primary arms, unregister subset/purge/
sibling/noop/guard rows, audit rows).

## Findings

### F1 — model-type map (REJECTED consolidation: single-owned, overlaps intentionally separate)

- **Contract + variation.** Exact-key model-to-type multi-map with an
  optional declared primary. Varies on: primary declared or not (`get`
  3-state), registration order (`types_for`), one vs many types
  (ambiguity protocol). Never varies on hierarchy (no walk), on reader
  (all 16 resolvers share the predicate), or on placeholder degradation
  (unregistered is `None`, never a guess).
- **Sites + roles.** *Definitions*: the nine accessors + storage + singleton
  (one each). *Sole producer*: `__init_subclass__` (1 call line, S7/S8).
  *Resolvers / reverse readers / scanners / caches / oracles /
  projections*: as listed in System trace.
- **Challenges.** C1 → 1; C2 → 1 (+ listed enforcers); C3 → 1 per arm
  (fully pinned); C4 → 0; C5 → 2 intentionally separate. Count > 1
  nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/registry.py::TypeRegistry` (F1 aspects)
  stands: narrowest cohesive owner every consumer can import without
  reversing a dependency (base, filters, walker, resolvers already import
  the registry; the reverse would cycle). Stored-derivation lifetime:
  validity key = class creation → `clear()`/`unregister()`; publish point
  = `register_with_definition` inside `__init_subclass__` (single flow
  writes the map entry, the store entry, and the alias from one `Meta`);
  who may mutate = `register` (import-time-only via `_check_mutable`) +
  `unregister` (drop one: detach + unconditional primary purge) +
  `clear()` (drop all, test-only bypass); reads = the nine accessors
  (unguarded pure per-call derivations — post-finalize request-time
  resolution requires reads through the finalized snapshot); derived
  caches name their own keys (`is_finalized`, origin identity — R-H).
  Between declare and finalize readers are the field-factory guards + the
  finalizer; between finalize and clear, decode/optimizer/inspect/cascade
  (read-only); after `clear()`/`unregister()` the class alias is
  intentionally stale (lifecycle split, M16/C6-analog).
- **Migration.** None (zero-edit rejection: no behavior hunk, no test
  hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** `get` (primary-or-lone-or-None)
  vs `primary_for` (strict) vs `types_for` (ordered snapshot) vs
  `iter_types` (per-type pairs) vs `model_for_type` (reverse, None
  passthrough); predicate (`get`) vs build-time enforcement (audit, R-C);
  alias vs index reverse reads (R-B); binder wordings per surface (R-D).
- **Behavioral proof.** `execution-verified` for empty/fallback/
  idempotence/flip/ambiguity/collision/order/reverse-collision/rollback/
  clear/unregister/split/proxy/MTI/alias/index/stale/audit/fallback
  (workspace 83/83 + N1 + the authorized 54-passed focused run).
  `static-reviewed` for the zero-`async` census, docstring-vs-body prose,
  and oracle-body independence (plain classes + real models; none reads
  the owner). Observable behavior pinned: proxy/MTI resolve only by own
  key; second type without primary is `None` everywhere and raises once
  at build; clear empties all three dicts; unregister keeps the sibling
  and purges the primary slot; the alias stays stale after teardown while
  the index drops (callers-responsible contract). Rejects every
  duplication direction in C1–C5.
- **Structural gate.** Deferred with reason: a behavior-preserving hand
  copy of the owner accessors passes every standing oracle by
  construction (the copy is correct — identical keys, identical `None`
  arms), so no behavioral gate can pin unity; only a source census
  could, and that is a bespoke existence test per helper, which
  [DRY.md][dry] forbids for gate-only findings (same bar as the verified
  enum-cache, definition-store, pending-ledger, taxonomy, and accessor
  items). Unity rests on the one-way import edges (all consumers import
  the registry; S8/S10 prove no second writer/reader) plus the recorded
  triggers below. Coverage that stays (each fails a real break — the
  focused run is green on the unmutated tree): the round-trip/lone/
  ambiguity/collision/idempotence/flip rows, the rollback pair, the
  clear/unregister rows, the audit rows, the proxy/secondary oracles.
  The ambiguity-loudness arm additionally carries N1's proved shape.
- **Coupling.** None. Adjacent verified items untouched: the F2/F3/F4
  stores, the file-registry item, and every oracle file keep their blobs
  (fingerprints below); no edit here can stale them.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `registry.py` `9cc8bb55…`, `types/finalizer.py` `77fd9a2d…`,
  `types/base.py` `91c58747…`, `types/definition.py` `fa6c4d330…`,
  `types/relay.py` `52439862…`, `types/resolvers.py` `f3341e6a…`,
  `optimizer/extension.py` `49667a93…`, `optimizer/walker.py`
  `9b111ed9…`, `permissions.py` `757dce34…`, `utils/querysets.py`
  `96618fba…` (= `HEAD`, clean — read freely, never edited),
  `utils/inputs.py` `ee31d360…`, `mutations/sets.py` `936f5ae7…`
  (vs `HEAD` `cffa29e5…`: the known concurrent
  `__name__`-to-`_safe_class_name` hunk, sampled and confirmed outside
  every cited map line — never edited), `auth/mutations.py`
  `200805d2…` (vs `HEAD` `dbe64995…`: same known hunk family, likewise
  outside the cited lines — never edited), `testing/relay.py`
  `df0dc72a…`, `management/commands/inspect_django_type.py`
  `46dffb3d…`, `tests/test_registry.py` `e330cfb8…`,
  `tests/test_permissions.py` `4a1d7775…`,
  `tests/types/test_converters.py` `2bdedee4…`,
  `tests/types/test_finalizer.py` `462275e5…`,
  `docs/dry/dry-file-registry.md` `4350662b…`. Searched population:
  whole package (117 `.py`, both trees); installed Django read as a
  behavior anchor, not a fingerprinted input. Any fingerprint change
  reopens the finding. Item-scoped diff vs `ITEM_BASELINE`
  (`4016227c…`): empty on all fifteen paths (the only baseline diff in
  the package is another item's `optimizer/nested_planner.py` +9,
  untouched).
- **Reconsideration triggers (recorded at the owners).** The map stays
  single-owned until one fires: T-hierarchy fires if a resolution path
  needs a superclass/proxy walk instead of exact-key (today S-census
  proves none); T-split fires if a runtime path needs the ambiguity
  reason, not just `None` (today only the binders split, via the
  documented `get`+`types_for` protocol); T-reverse fires if a caller
  needs the alias to track teardown (today callers-responsible, M16).
  Durable homes: the `get` 3-state docstring, the `model_for`
  caller-responsibility docstring, the audit docstring, this finding.
  The plan's `## Responsibility index` row for
  `type-registry-model-type-map` already covers the fifteen files; Worker
  0 owes two row narrowings (drop `utils/inputs.py`; add the four
  beyond-list consumers named in System trace) — no new row.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A map vs store (F2 owns the store). Difference: per-model
  multiplicity + primary predicate + hot-path reverse lookup vs per-type
  declaration record; one `Meta` feeds all writes in one flow; zero
  model-keyed definition scans (S11). Deriving the map from a scan would
  put request-time lookups behind a linear walk. Trigger: a model-keyed
  read that cannot use the map. Home: the F1 family item + the F2
  finding (C5 there). The finalizer set-owner `issubclass` compat check
  is owner binding, not lookup (reviewed, stays).
- R-B alias (`model_for`) vs index (`model_for_type`). Difference: same
  fact, opposite contracts — the alias raises `AttributeError` for
  programmer error (callers-responsible, import-free, 14 hot-path calls)
  while the index returns `None` for expected-absent (3 round-trip
  callers + `None` passthrough); M15/M16 pin both modes and the
  post-teardown divergence shape. Collapsing to one holder changes the
  failure mode at fourteen sites. Trigger: a caller needing the other's
  mode (T-reverse). Home: the `model_for` docstring + this finding.
- R-C predicate (`get` → `None`) vs build-time audit
  (`_audit_primary_ambiguity`). Difference: reason-agnostic runtime
  predicate the soft consumers depend on (skip-edge, default-manager
  fallback, warn-audit, `_meta` fallback — all oracled) vs bulk
  once-per-build sorted single-raise. Raising in `get` would break every
  soft arm; splitting in the audit needs `primary_for`+`types_for` the
  predicate deliberately hides. Trigger: a runtime path needing the
  reason (T-split; the binders show the shape). Home: the `get`
  docstring ("cannot distinguish … without checking `types_for`") + the
  audit docstring.
- R-D binder splits (`_resolve_primary_type` vs
  `_resolve_user_primary_or_raise`). Difference: one shared getter + one
  shared 4-line split protocol (both compose the owner by name; the auth
  docstring cites the linkage), two surface-specific messages that change
  for different reasons (mutation bind vs auth surface bind). A shared
  helper would need a message mode flag for four lines. Trigger: a third
  surface needing the split → consider a shared splitter then. Home:
  both docstrings + this finding.
- R-E strict serializer read (`_require_relation_primary`, no-split
  raise) vs the split binders. Difference: class-creation-time single
  state ("no registered primary" is true for both missing and ambiguous,
  and names the fix; the finalize audit refines it before any request).
  Trigger: a surface needing the missing/ambiguous distinction at class
  creation. Home: its docstring (the spec-039 strictness clause).
- R-F owner-aware reads (filter target resolver, child-owner branch,
  `related_target_for`) vs direct `get`. Difference: temporal/binding
  phases of the same answer — the owner path resolves through
  `related_target_for` (which itself calls `get`) and falls back to
  direct `get` pre-bind; the call-site prose forbids re-deriving
  primary-first precedence there. No second precedence exists to move.
  Trigger: an owner-aware read disagreeing with the map (a defect, not
  drift). Home: the call-site docstrings + this finding.
- R-G name scans (inspect bare-name resolver, `definition_for_graphql_name`)
  vs the model map. Difference: different keys (SDL/Python/GraphQL names
  vs model classes) for different questions (operator lookup, GlobalID
  decode vs relation resolution); owned rule-wise by the inspect file
  item and Family `relay-node-name-decode`. Trigger: a name-keyed lookup
  needing model-keyed semantics. Home: those items.
- R-H cached derivations (related-target memo, plan cache, connection
  cache, owner bindings) vs the map. Difference: each names its validity
  key (`is_finalized`, origin identity, type identity, set lifecycle);
  all consume map state by name and invalidate with it (eviction/purge/
  replay or key construction). Trigger: a cache surviving the key it
  names. Home: each owner.

## Defects

None meeting the [AGENTS.md][agents] bar (contract row + feasible shape +
wire/config input). Asymmetries checked while tracing that hold: the
serializer message is accurate in both unresolved states (names the fix;
the audit refines it); `model_for`'s raw `AttributeError` is the
documented callers-responsible contract with the stale-split pinned
(M16); the walker `_meta` fallback and the default-manager fallback are
documented graceful-degradation policies with oracles; the filter
child-model `None` guard and the mutation probe's explicit `None` branch
are present; the concurrent `__name__`→`_safe_class_name` hunks touch
message rendering only, outside every cited map line.

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace (83/83 + N1, copy `__file__` + copy DB `NAME` recorded, no
source mutation, byte-identical restore, `grep -c truncated` == 0); the
one authorized shared-tree focused test ran green post-trace (54 passed)
with zero edits in flight, so no run is invalidated. No
`execution-deferred` items. `FAKESHOP_SHARDED=1` and Postgres cells
`inapplicable by construction`: every executed claim is in-memory dict
work plus pure class construction/decoration; the probes open no DB
(recorded `NAME` is the copy's own file, never touched). Full-suite gate
business is deferred to the final-gate item with reason: the entry
command authorizes workspace runs plus one focused `--no-cov` test, and
a green unmutated suite would discharge no failability proof for a
rejection that proposes no gate.

## Judgment

Single-owned map, single producer, sixteen resolvers composing by name,
both reverse readers pinned with their failure modes, all scanners and
caches validity-keyed. The eight resemblance candidates (store, alias,
audit, binder twins, strict read, owner-aware paths, name scans, cached
derivations) are intentional separations with recorded differences,
triggers, and existing homes. Consolidation rejected; zero edits; no new
tests owed (standing oracles at the mandated tiers pin every challenged
axis; the ambiguity arm additionally carries N1's proved shape).

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`4016227cb1f049de2622eef0ae816de44c1fd56b`) is empty for all fifteen
family paths (and vs `HEAD` `bfaee91d` likewise, except the two known
concurrent-work files `mutations/sets.py` + `auth/mutations.py`, whose
hunks were sampled: `__name__`-to-`_safe_class_name` message rendering
only, outside every cited map line — never edited, so no attribution
stop triggered). The plan's `## Owned changes` ledger holds exactly one
row on a family path (`optimizer/walker.py`, the committed D1 seal-policy
fix — verified inside its own item; this trace's walker reads touch only
the map sections, no interaction) — confirmed by full read; nothing else
on this family's paths, as briefed. `utils/querysets.py` was read at
current-HEAD bytes and fingerprinted only (its file item is BLOCKED; a
consolidation touching it would STOP — none does). No commit per standing
rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff format
--check` on all fifteen member paths — all green, all already formatted
(read-only verification; `--fix`/write-formatting withheld because the
tree carries concurrent dirt this item must not tidy; `.md` artifacts are
excluded from format). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/model-type-map-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_model_type_map.py` holding the 83 executed checks + N1). No
manifest (no `prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `type-registry-model-type-map` (this
artifact); narrow the `## Responsibility index` file coverage (drop
`utils/inputs.py`; add `filters/sets.py`,
`rest_framework/serializer_converter.py`, `relay.py`,
`mutations/resolvers.py` as covered consumers); no `## Owned changes`
append (zero tracked edits); no defect homing (none found).

## Independent verification (Worker 2)

Reading-order note: the dispatch brief ordered the full artifact before
verification, so `## Findings` was seen first. Every count below was still
re-derived from scratch with independent AST probes over the 117-file package
population in the shared tree (never from W1's probe file), then reconciled
claim by claim. No `worker-memory/` read.

Own trace. Contract: exact-key multi-map model-to-type with optional declared
primary. `registry.py::TypeRegistry.get` returns primary-or-lone-or-None;
`registry.py::TypeRegistry.primary_for` is strict; `registry.py::TypeRegistry.types_for`
is an ordered snapshot; unregistered key returns None; no hierarchy walk exists
in the `get` body (two dict probes, no MRO traversal). Definitions (one each):
`register`, `unregister`, `get`, `model_for_type`, `iter_types`,
`primary_for`, `types_for`, `models_with_multiple_types`,
`_detach_type_from_model`, the three dicts (`_types` / `_primaries` /
`_models` constructed once in `__init__`), the singleton `registry`. Sole
production writer: `types/base.py::DjangoType.__init_subclass__` via the
`register_with_definition` pair (1 call line; zero direct production
`register` callers — AST-verified). Owner I would choose:
`registry.py::TypeRegistry` (F1 aspects): every resolver already imports the
registry, so the reverse would cycle; narrowest cohesive owner with the
enforcement authority (`_check_mutable`, `clear`, `unregister`).

Resolver census (my AST call census, code calls only, docstring prose
excluded): `registry.get` 16 calls in exactly 12 files —
`types/finalizer.py` 2, `optimizer/walker.py` 2, `mutations/sets.py` 2,
`filters/sets.py` 2, and 1 each in `permissions.py`,
`rest_framework/serializer_converter.py`, `auth/mutations.py`,
`types/definition.py`, `types/resolvers.py`, `types/relay.py`,
`optimizer/extension.py`, `utils/querysets.py`. Reverse readers: bare
`model_for` 14 calls in 5 files (`mutations/resolvers.py` 5,
`types/relay.py` 3, `relay.py` 3, `utils/querysets.py` 2,
`permissions.py` 1) vs `registry.model_for_type` 3 calls in 2 files
(`optimizer/extension.py` 2,
`management/commands/inspect_django_type.py` 1). Scanners:
`registry.types_for` 5 in 3 files (finalizer 3, both binders 1 each),
`registry.primary_for` 3 in 1 file (finalizer),
`registry.iter_types` 1 (extension audit),
`registry.models_with_multiple_types` 1 (finalizer). C4 probe: zero
`definition.model ==` equality scans over definitions anywhere in the
package; the only `is not None` reads are the set-owner compat guards
(`filters/sets.py`, `types/finalizer.py`), not lookups.

Cache-validity check (each cache judged REAL, none is a defect):
related-target memo (`types/definition.py::DjangoTypeDefinition.related_target_for`)
populates only when `registry.is_finalized()` is true, so pre-finalize
mutation can never lock in a transient None; definitions are recreated fresh
after `clear()` so the per-object memo dies with its object; `unregister`
can only run pre-finalize (its `_check_mutable` guard raises post-finalize),
where the memo is never populated — no stale-cache path exists. Optimizer
plan cache (`optimizer/extension.py::DjangoOptimizerExtension._plan_cache`)
is per-extension-instance keyed on (printed operation + reachable fragments,
cache-relevant vars, target model identity, root path, origin type identity);
a re-registered type is a new identity, so it cannot collide; the
module-level `_doc_key_cache` LRU is a pure function of document text plus
operation name and carries no registry state. Connection-class cache
(`connection.py::_connection_type_cache`) is type-identity keyed, purged on
`clear()` via its registered subsystem callback and evicted per-type on
`unregister()` via the best-effort co-clear — both public mutators covered.
Set-owner bindings reset through `binding_attrs`-driven
`clear_generated_input_namespace`, itself replayed by `clear()` — validity
key is the set lifecycle, invalidated with it. No cache survives the key it
names; no `clear()`/`unregister()` invalidation gap found.

Population completeness: my 117-file sweep found no map-accessor call
outside the inventoried set. The beyond-list four (`filters/sets.py`,
`rest_framework/serializer_converter.py`, `relay.py`,
`mutations/resolvers.py`) are confirmed map consumers covered by this family
row — no new index row owed. `utils/inputs.py` correction CONFIRMED: zero
map calls; its only `registry` tokens are `clear()`-lifecycle prose and its
own `_collision_registry` (the set-naming rule owned elsewhere). Worker 0
should narrow the index row (drop `utils/inputs.py`; add the four
consumers).

C5 judgment (Worker 2): agree — two reverse readers, intentionally separate,
not a unification candidate. `utils/querysets.py::model_for` reads the
class-attached alias (`__django_strawberry_definition__.model`), is
import-free, and raises raw `AttributeError` for programmer error; the
registry index read returns `None` (with `None` passthrough) for
expected-absent. Different sources, opposite failure contracts, different
import costs; collapsing them rewrites the failure mode at 14 hot-path sites
to serve 3 round-trip callers. Count stays 2.

Hierarchy-walk judgment (Worker 2): agree — "proxy resolves only under own
key" is genuinely the contract. Opened
`tests/test_permissions.py::test_proxy_target_filtered_default_manager_composes`:
it pins the positive (a proxy-model type resolving through its own exact
key). The negative rests on the `get` body itself (two exact dict probes, no
walk possible in seven lines). Swept every map-adjacent module for a manual
MRO workaround: `types/finalizer.py` MRO use is Strawberry surface
collection, `types/definition.py` MRO use is id-resolver detection,
`types/relay.py` MRO use is interface filtering — none is a model-to-type
walk. No shadow map exists; reconsideration trigger T-hierarchy stands as
recorded.

Challenges agreed: C1 → 1 (exact-key predicate; no walk to move), C2 → 1
(owner predicate + storage; audit/binders/16 resolvers listed-not-counted —
correctly, they are enforcement/consumers adapting to the contract),
C3 → 1 per arm (map arms fully asserted, F1/F4 boundary re-checked not
inherited), C4 → 0, C5 → 2 intentionally separate. Rejections R-A..R-H each
carry a contract difference, a trigger, and an existing durable home;
R-H's validity keys re-verified above. Owner choice agreed (dependency
direction wins). No-gate reasoning agreed: a behavior-preserving hand copy
passes every standing oracle by construction, so only a source census could
pin unity — a bespoke existence test per helper, forbidden for gate-only
findings at the same bar as the verified enum-cache, definition-store,
pending-ledger, taxonomy, and accessor items. `## Pending execution` empty
judged correct: 83/83 + N1 recorded with copy `__file__`, copy DB `NAME`,
and byte-identical restore; the 54-passed focused run is green on the
unmutated tree; sharded/PG inapplicable by construction (in-memory dict work
plus class construction; probes open no DB); full-suite gate business
belongs to the final-gate item.

Freshness re-hashed by Worker 2 (`git hash-object` working tree):
`registry.py` `9cc8bb55…`, `types/finalizer.py` `77fd9a2d…`,
`optimizer/walker.py` `9b111ed9…`, `utils/inputs.py` `ee31d360…`,
`utils/querysets.py` `96618fba…` (= `HEAD:bfaee91d` blob, clean — read at
HEAD, never edited). Item-scoped diff vs `ITEM_BASELINE`
(`4016227cb1f049de2622eef0ae816de44c1fd56b`) is EMPTY on all fifteen family
paths (verified directly). The only baseline diff in the package is the
concurrent `optimizer/nested_planner.py` +9: verified outside every map
line (planner, not registry/walker/extension map sections) and left alone,
as briefed; all other working-tree dirt is concurrent work out of scope.
Per-claim delta vs W1: none — full agreement on every count, role, cache
key, rejection, and hash. Zero edits; AGENTS.md prose holds (no process
provenance, `path::Symbol` citations, standing oracles at mandated tiers;
`.md`-only change needs no ruff pass).

Worker 0 rows: tick Family `type-registry-model-type-map` as `verified`
(Run `0.0.15 2026-09-19-1`, zero edits, no pending execution); narrow the
`## Responsibility index` file coverage (drop `utils/inputs.py`; add
`filters/sets.py`, `rest_framework/serializer_converter.py`, `relay.py`,
`mutations/resolvers.py` as covered consumers); no `## Owned changes`
append; no defect homing. Scratch removal is Worker 0's, by explicit path:
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/model-type-map-w1`
(includes its `.venv` + `probe_model_type_map.py`).

### Defects note (Worker 2)

None meeting the [AGENTS.md][agents] bar (contract row + feasible shape +
wire/config input); no new entry under the artifact's `## Defects`: the serializer message
accuracy, `model_for` raw-`AttributeError` callers-responsible shape, both
documented graceful-degradation fallbacks, the filter child-model `None`
guard, and the concurrent `__name__`-to-`_safe_class_name` hunks (message
rendering only, outside every cited map line) were each re-checked and hold.
Cache-invalidation sweep above found no surviving-the-key cache.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[dry]: DRY.md

<!-- docs/ -->
[spec-018]: SPECS/spec-018-meta_primary-0_0_6.md
[spec-031]: SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-036]: SPECS/spec-036-mutations-0_0_11.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutation-resolvers]: ../../django_strawberry_framework/mutations/resolvers.py
[root-relay]: ../../django_strawberry_framework/relay.py
[serializer]: ../../django_strawberry_framework/rest_framework/serializer_converter.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->
[test-converters]: ../../tests/types/test_converters.py
[test-finalizer]: ../../tests/types/test_finalizer.py
[test-permissions]: ../../tests/test_permissions.py
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Bounded re-review (Worker 2, Q12)

Phase-1 independent trace. HEAD `bfaee91d`; worktree read 2026-09-21. Prior
sections of this artifact were NOT read (blinded phase). Zero package edits;
concurrent dirt preserved.

### 1. Map contract with resolution paths (from CURRENT source)

Storage (all in `django_strawberry_framework/registry.py::TypeRegistry`):
`_types: dict[model, list[type]]`, `_primaries: dict[model, type]`,
`_models: dict[type, model]` (reverse), `_definitions: dict[type,
DjangoTypeDefinition]`, `_enums: dict[(model, field_name), Enum]`,
`_pending: list[PendingRelation]`.

Write path: exactly one construction site,
`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
builds one `DjangoTypeDefinition`, then calls
`registry.py::TypeRegistry.register_with_definition` (atomic
`register` + `register_definition` with snapshot rollback through
`registry.py::TypeRegistry._detach_type_from_model`), then
`registry.py::TypeRegistry.add_pending_relation` per relation field.

Resolution paths, all exact-key dict lookups (verified: `registry.py`
contains no `isinstance`, no `issubclass`, no `__mro__`, no
`concrete_model`):

- `registry.py::TypeRegistry.get`: `_primaries.get(model)` first; else
  single-candidate fallback (`_types.get(model)` with `len == 1`); else
  `None`. The `None` state conflates "unregistered" and
  "multi-type-no-primary"; callers split them with `types_for`.
- `registry.py::TypeRegistry.primary_for`: strict `_primaries.get`.
- `registry.py::TypeRegistry.types_for`: immutable tuple snapshot of
  `_types.get(model, ())`, registration order.
- `registry.py::TypeRegistry.model_for_type`: `_models.get(type_cls)`
  (`None` for `None`/unregistered); consumer is
  `django_strawberry_framework/optimizer/extension.py` (GraphQL return
  type back to Django model).
- `registry.py::TypeRegistry.get_definition` /
  `registry.py::TypeRegistry.iter_definitions`: `_definitions` access /
  iteration.
- `registry.py::TypeRegistry.definition_for_graphql_name`: linear scan
  over `iter_definitions()` for `implements_relay_node(type_cls)` and
  `definition.graphql_type_name == name`; one match returns, zero
  raises miss, two-plus raises ambiguity. Sole consumer is the
  type-name branch of
  `django_strawberry_framework/types/relay.py::decode_global_id`.
- `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for`:
  `model._meta.get_field(field_name)` to `related_model` to
  `registry.get(target_model)` to `registry.get_definition(target_type)`;
  `None` at every miss step; memoized per field name only when
  `registry.is_finalized()`.
- Finalize relation resolution
  (`django_strawberry_framework/types/finalizer.py`, Phase 1/2): per
  pending record `registry.get(pending.related_model)`; miss joins the
  unresolved list and raises `ConfigurationError` via
  `finalizer.py::_format_unresolved_targets_error` (GOAL.md deliberate
  raise; non-goal guards the no-silent-stub rule). The ambiguity audit
  (`finalizer.py::_audit_primary_ambiguity` over
  `registry.py::TypeRegistry.models_with_multiple_types` +
  `primary_for` + `types_for`) runs before unresolved-target
  collection.
- Model-label decode branch (`types/relay.py::decode_global_id`):
  `apps.get_model` to `registry.get(model)` to `get_definition`.

No hierarchy walk: a subclass of a registered model does NOT resolve
to its parent's type. No proxy handling at the map layer: a proxy
model and its concrete model are distinct identity keys;
proxy/concrete-table compatibility lives downstream
(`utils/querysets.py`, `permissions.py` cascade), never in the map.

### 2. definition.py reads with roles (which map findings depend on which dirt hunk)

Worktree-vs-HEAD dirt in `types/definition.py` = four hardening hunks
(guarded `isinstance` + `str.__str__` + `_safe_*` rendering); the
`registry.py` worktree diff is docstring-only (single-inverse prose on
`definition_for_graphql_name`, no behavior). Map-core paths (`get`,
`primary_for`, `types_for`, pending, finalize audits) read NO dirtied
field: pure identity-dict lookups, dirt-independent.

- Hunk 1, `DjangoTypeDefinition.graphql_type_name` normalization:
  depended on by `definition_for_graphql_name` (decode scan key),
  `types/relay.py` encode + mismatch diagnostics,
  `types/finalizer.py` audit/owner-axis messages and the
  second-owner `graphql_type_name` comparison,
  `filters/base.py::_accepted_globalid_type_names` + diagnostics,
  `filters/inputs.py::_owner_type_name` (delegates; docstring names
  the three callers sharing the one rule), `connection.py`
  `<TypeName>Connection`, `relay.py` node-type check,
  `testing/relay.py`, `management/commands/inspect_django_type.py`.
  All are consumers of the one derivation, none re-derives.
- Hunk 2, `related_target_for` field-name gate: depended on by
  `filters/base.py` relation walk, `filters/sets.py` owner binding,
  `types/finalizer.py::_bind_set_owner` divergence check,
  `optimizer/walker.py::_resolve_target_pair` (definition-first with
  a registry-only fallback in the same shape).
- Hunks 3-4, `_normalize_pk_name` / `_resolves_id_off_pk` (behind
  `has_custom_id_resolver_for` / `origin_has_custom_id_resolver`):
  depended on by `optimizer/walker.py::_has_custom_id_resolver`
  (FK-id elision guard), whose definition path and definition-less
  fallback share the one free function so they cannot drift.

### 3. Definition counts (change challenge)

- New model shape (add model M + type T(M)): count 1. The
  `register_with_definition` call in `__init_subclass__` writes
  `_types` + `_models` + `_definitions` atomically; `graphql_type_name`
  and friends are derived projections of that one record; finalizer,
  relay, filters, connection follow by construction.
- Second type for one model (T2(M) beside T1(M), primary optional):
  count 1. `TypeRegistry.register` owns the `_types[model]` list +
  `_primaries[model]` slot; `get`'s three-state logic and the
  ambiguity audit consume that one record. Posit "change the
  primary-selection rule": one edit at the `_primaries` slot and its
  two readers.
- Name-grammar change (rename the GraphQL surface rule): count 1.
  `DjangoTypeDefinition.graphql_type_name` (DRY.md principle 2);
  `definition_for_graphql_name` is its declared single inverse scan,
  `_owner_type_name` delegates.

### 4. Owners I would choose (DRY.md principle 7)

- Model-to-type map (registration, primary slot, reverse lookup,
  pending list, finalize audits): `registry.py::TypeRegistry`.
  Existing owner with that responsibility; every legitimate consumer
  imports it without reversing a dependency; lifetime = registry
  lifecycle (import-time mutation, finalize publishes, `clear()`
  test-only resets).
- GraphQL surface-name grammar: `DjangoTypeDefinition.graphql_type_name`
  (DRY.md principle 2, one owned translation); the registry scan is
  the single inverse consumer, not a second grammar.
- Relation-target derivation: `DjangoTypeDefinition.related_target_for`
  (memoized derivation; cache valid post-finalize only, keyed by
  field name, bounded by fresh definitions after `clear()`); walker,
  filters, finalizer compose by name.
- PK-name normalization + id-off-pk classification:
  `types/definition.py::_normalize_pk_name` +
  `types/definition.py::_resolves_id_off_pk` behind
  `types/definition.py::origin_has_custom_id_resolver`.
- Error strings stay with their emitters
  (`finalizer.py::_format_unresolved_targets_error`,
  `finalizer.py::_format_ambiguity_error`); not map definitions.

### 5. Whether the dirt breaks anything derived

No. All four `definition.py` hunks are hostile-input hardening with
identical behavior on honest inputs: same returns, same raises, same
message text; only the triggering input class widens to hostile
impostors (liar `__class__`, raising `__str__`/`__mro__`/`__dict__`,
raising `resolve_id_attr`, non-string `id_attr`). Outcomes on those
inputs are the already-contracted fail-closed values
(`ConfigurationError` with `_safe_*` rendering for
`graphql_type_name`; `None` for `related_target_for`; `None`/`False`
for `_normalize_pk_name`; `True` fail-closed for
`_resolves_id_off_pk`). No contract row breaks; no new resolution
path; no changed return state or exception on any input reachable
through supported public API (`Meta.name`, real field names, real pk
names are genuine strings from trusted application Python per GOAL.md
Trust boundary). Verdict on the delta: benign-equivalent,
hostile-only.

Oracle coverage read (not run): hostile rows in
`tests/types/test_definition_relations.py` (liar-str, raising-class,
unreadable-origin, empty/invalid names, unhashable/empty pk names,
hostile `__mro__`/`__dict__`/`resolve_id_attr`, cache-behavior rows);
`tests/test_registry.py` (type-name decode match, `Meta.name` key,
Relay-only scan, miss, ambiguity, `get` three-state, primary
collisions, ambiguity audit, pending atomicity);
`tests/types/test_definition_order.py` (unresolved-target raise,
ambiguity-before-unresolved ordering);
`tests/types/test_finalizer.py`, `tests/types/test_converters.py`,
`tests/filters/test_finalizer.py`, `tests/orders/test_finalizer.py`,
`tests/test_connection.py` (connection name from
`graphql_type_name`), `tests/types/test_base.py`
(`Meta.name` override), live
`examples/fakeshop/test_query/test_library_api.py` node-refetch rows.

### 6. Freshness fingerprints (HEAD + worktree separately)

- HEAD: `bfaee91dcd332a5f86250fff90ab21b377bc674e`.
- `django_strawberry_framework/registry.py` HEAD blob
  `9cc8bb553fd417fc465809a541769a8383469cda`; worktree blob
  `612bea87fdcf5e5a254caf70c9947b9535f638c3` (diff: docstring-only
  addition on `definition_for_graphql_name`).
- `django_strawberry_framework/types/definition.py` HEAD blob
  `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`; worktree blob
  `01f78d93baf8fb6ca3ab11df1a2a495640fb7655` (diff: four
  guarded-`isinstance` + `str.__str__` + `_safe_*` hunks listed in
  section 2).
- Both files dirty at task start; treated as concurrent work,
  preserved, unedited. No status set; no verdict on prior findings
  proposed.

PHASE-1-TRACE-RECORDED docs/dry/dry-rule-type-registry-model-type-map.md
