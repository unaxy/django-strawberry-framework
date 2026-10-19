# DRY review: `related-object-visibility-recheck`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

Posited rule (index row; owner candidate
[querysets.py][querysets]
`::related_visibility_queryset_or_default`; indexed files
[querysets.py][querysets], [types-resolvers.py][types-resolvers],
[write-values.py][write-values], [rf-resolvers.py][rf-resolvers],
[forms-resolvers.py][forms-resolvers],
[mutations-resolvers.py][mutations-resolvers] as transitive
consumer): a related object resolved by client-supplied id must
be re-checked through the related type's `get_queryset`
visibility hook, so a writer cannot attach a row it could not
see. No prior family artifact exists; this trace is fresh at
HEAD bytes, census-first (the 6 indexed files were not assumed
complete).

Verdict: CONFIRM the consolidation. The write-side recheck is
one rule with a single body at every layer, and every member
composes it by name. Five neighbor-merges are rejected with
contract differences and triggers.

- F-write: the write-side recheck -- the 7-helper cluster in
  [querysets.py][querysets] (`:4451`-`:4645`) plus the 2-function
  decode spine in [write-values.py][write-values] (`:194`,
  `:283`), consumed by all three write flavors (7 decoder call
  sites) plus one direct `None`-handling consumer. Zero second
  bodies package-wide.
- R1 (rejected merge): the read-path twin
  [types-resolvers.py][types-resolvers]
  `::_visible_related_object` (`:407`) -- instance recheck
  through CUSTOM hooks on UNPLANNED relations only, color-aware.
  Five contract differences; its own file-local rule.
- R2 (rejected merge): the Relay node fetch
  [types-relay.py][types-relay] `::_resolve_node_default` /
  `::_resolve_nodes_default` (`:949` / `:1014`, + async sibs) --
  SELF-type node identity resolution with id-attr filter,
  required/missing semantics, and order-preserving bulk.
- R3 (rejected merge): the write-target locate
  [mutations-resolvers.py][mutations-resolvers]
  `::locate_instance` (`:683`) -- SELF-type target fetch with
  the write-alias pin + row-lock sandwich.
- R4 (rejected merge): the filter-branch derivation
  [filters-sets.py][filters-sets]
  `::_derive_related_visibility_querysets_sync` / `_async`
  (`:2711` / `:2771`) -- per-branch querysets with the OPPOSITE
  no-primary default (refuse, never fall back).
- R5 (rejected sub-merge): routing the non-member inline
  `apply(initial_queryset(...))` compositions (twin, relay x6,
  locate) through `::visibility_scoped_related_queryset` -- the
  composition has no variation of its own; both parts are
  already single-owned and composed by name.

Sites and roles (all re-derived at HEAD `83998e08` bytes):

- Definitions (F-write, one body each):
  `::visibility_scoped_related_queryset` (`:4451`, the
  apply-through-initial composition), `::related_visibility_queryset`
  (`:4475`, registry resolve `:4498` + scope, `None` when no
  primary), `::related_visibility_queryset_or_default` (`:4504`,
  the default-manager fallback `:4519`-`:4522`, the index-row
  owner), `::_stringified` (`:4525`, the comparison basis),
  `::stringified_pks_present` (`:4535`, the one-query
  present-set), `::pks_all_present` (`:4562`, the subset test),
  `::visible_related_object` (`:4576`, single resolve
  `:4615`-`:4617`), `::visible_related_objects` (`:4620`,
  batched resolve `:4641`-`:4642`); the spine
  `::decode_visible_relation` (`:194`, calls `:236`) and
  `::decode_visible_relation_ids` (`:283`, calls `:326`-`:328`),
  with `::type_check_relation_id` (`:129`, spine-internal
  callers `:229` / `:316` only) and
  `::materialize_relation_id_container` (`:260`).
- Consumers, all by name: form single `:217` + form multi
  per-element map `:228`-`:280` (needs the object for
  `to_field_name`); model single `:618` + model M2M `:654` via
  `relation_into(single=, multi=)` (`:405`, wired `:503`-`:511`);
  serializer single `:259` + serializer multi `:288`; the
  scope-specs direct consumer `:1516`-`:1528` (calls
  `related_visibility_queryset`, keeps its OWN `None`-skip per
  the owner's prescribed contract, ANDs visibility onto the
  author's queryset, then pin + lock).
- Neighbor definitions (each single-owned, each excluded):
  twin `:407` + 7 gated call sites (`:651` / `:666` / `:727` /
  `:744` / `:763` / `:800` / `:820`) with the many-side sibling
  `::_visible_many_rows` (`:431`, sites `:589` / `:613`), all
  gated by `::_custom_visibility_type` (`:381`) +
  `::_optimizer_scoped_relation` (`:456`); relay node `:949` /
  `:989` / `:1014` / `:1059` (6 inline compositions `:984` /
  `:1009` / `:1051` / `:1053` / `:1076` / `:1078`); locate
  `:683`-`:725` (composition `:713`-`:717`, lock, `get` /
  `DoesNotExist`); filter derivation `:2711` / `:2771`
  (5 call sites `:2870` / `:3334` / `:3341` / `:3548` / `:3609`,
  missing-primary refusal `:2685`-`:2708`, resolve `:2888` /
  `:2918`).
- Intentional non-members: `::refetch_optimized` (`:827`,
  `:864` -- the one documented exception: own-write
  round-trip, no visibility filter, spec-036 Decision 9);
  [relay.py][relay] `:300` (NodeID-to-pk pre-resolution WITHOUT
  visibility, enforced downstream by the locate / relation /
  form queries -- documented); [orders-sets.py][orders-sets]
  `:837` (no derivation by construction -- flat `order_by`
  needs none); `post_process_queryset_result_sync/async`
  (`:4819` / `:4842`, consumer-SOURCE shape, not related
  recheck); cascade edge [permissions.py][permissions]
  `:701`-`:720` (model-keyed alias-pinned base + custom policy
  + renderer -- four params the owner does not take);
  [rf-resolvers.py][rf-resolvers] `:1932` / `:2048` (post-save
  M2M attestation snapshots); connection / list-field / walker
  apply sites (own-source scoping).
- Oracles: owner cluster --
  [test-querysets.py][test-querysets] `:216` + `:229`
  (batched present-set), `:4677`-`:4681` (subset),
  `:4685`-`:4693` (single resolve),
  [test-forms-resolvers.py][test-forms-resolvers] `:1320`
  (no-primary default manager); spine --
  [test-write-values.py][test-write-values] `:80`, `:129`,
  `:151`, `:483`, `:588`, `:658` (incl. the one-query pin);
  twin -- [test-types-resolvers.py][test-types-resolvers]
  `:1290` (`None` short-circuit), `:1445` (seam), live
  [test-products-visibility-api.py][test-products-visibility-api]
  `:260` (async branch); filters --
  [test-filters-sets.py][test-filters-sets] `:5046`, `:5212`
  (unregistered raises), `:5840`; locate --
  [test-mutations-resolvers.py][test-mutations-resolvers]
  `:1246` (lock), `:1276` (opt-out); relay --
  [test-relay-interfaces.py][test-relay-interfaces]
  `:726` / `:738` / `:750` / `:765` (async),
  `:1378` / `:1396` (free-function); live hidden-attach --
  [test-library-api.py][test-library-api] `:8903` / `:8925`,
  `:10433` (query-count parity). Cited by content at HEAD
  bytes; no pytest run (dispatch forbids it).
- Projections (verified against their bodies): the cluster
  docstrings (sharing claims hold transitively -- two
  precision notes under F-write, no contract impact), the
  spine docstrings (the cross-flavor invariant), the flavor
  colorings, the twin one-liner + both gate docstrings, the
  relay four-step shape cite at `::initial_queryset` (`:316`),
  plus [orders-sets.py][orders-sets] `:837`,
  [finalizer.py][finalizer] `:1378`,
  [errors.py][errors] `:326`, [mutations-sets.py][mutations-sets]
  `:1681`, [library-schema.py][library-schema] `:1238`,
  [write-transaction.py][write-transaction] `:142`-`:143`,
  [relay.py][relay] `:259`, [forms-resolvers.py][forms-resolvers]
  `:32`, [walker.py][walker] `:586` (deliberate NOT
  `initial_queryset`), [querysets.py][querysets] `:4826`.

Dirt attribution (by diff content vs `git show HEAD:`, not by
dirty status; the ledger names [types-resolvers.py][types-resolvers]
once -- the adopted `one-sync-boundary` orphan, whose 3
lazy-fetch arms + docstring ARE worktree dirt here,
DRY-attributed; everything else below is concurrent-external):

- [querysets.py][querysets]: the cluster (`:4451`-`:4645`)
  has ZERO hunks. Adjacent `:4431` / `:4711` hunks are the
  `_safe_class_name` -> `truth.name` rename (truth migration).
- [types-resolvers.py][types-resolvers]: twin body (`:407`-`:430`),
  all 7 gates, both many-rows sites logic-intact. Hunks: the
  ledger orphan arms (`:642` / `:715` / `:786` + `:543`
  docstring), `check_deadline` insertions (deadline feature),
  `isinstance(x, type)` -> `truth.is_type` (`:396`, truth
  migration).
- [write-values.py][write-values]: visibility tail
  (`:326`-`:328`) intact. Hunks: NodeID batching restructure
  of the type-check half, `except BaseException` ->
  `except TypeError` narrowing, truth migration, docstring
  rewrites (all concurrent).
- [rf-resolvers.py][rf-resolvers]: decoders (`:236`-`:295`)
  and scope-specs logic intact; the `:1514` hunk is a pin-label
  `truth.name` rename (truth migration).
- [forms-resolvers.py][forms-resolvers] /
  [mutations-resolvers.py][mutations-resolvers]: zero hunks in
  the decoder / locate / refetch ranges (`:182`-`:280`,
  `:589`-`:870`).
- Decision impact: none. The probe ran both states to prove
  the point (identical ALL OK).

Three-state fingerprints (indexed files):

- [querysets.py][querysets]: HEAD `392e50d0`, worktree
  `cfc773ba`, `9aaaad5d` `8fc556d5`; `7f549142` == worktree.
- [types-resolvers.py][types-resolvers]: HEAD `574e9768`,
  worktree `7a953c53`, `9aaaad5d` `640905c6`;
  `7f549142` == worktree.
- [write-values.py][write-values]: HEAD `01a3318c`, worktree
  `4fa8118d`, `9aaaad5d` `13548c76`; `7f549142` == worktree.
- [rf-resolvers.py][rf-resolvers]: HEAD `420fc3ca`, worktree
  `3fc6a366`, `9aaaad5d` `c49ce3c2`; `7f549142` == worktree.
- [forms-resolvers.py][forms-resolvers]: HEAD `ea839d84`,
  worktree `6e613333`, `9aaaad5d` `a1000f21`;
  `7f549142` == worktree.
- [mutations-resolvers.py][mutations-resolvers]: HEAD `7a25afea`,
  worktree `dd00ec6e`, `9aaaad5d` `c9cff059`;
  `7f549142` == worktree.
- Nothing moved since `ITEM_BASELINE`
  (`7f54914298798481fb141326ec44565fbce00799`
  -- window diff names only the plan's own dispatch lines);
  HEAD `83998e08d48c911199527ed0411ab8041805c8b5`; snapshot
  `9aaaad5de73f6ff36eea3264e5b085fef1b046cc`.
- Cited files (HEAD / worktree):
  [filters-sets.py][filters-sets] `3d307402` / `ec278851`,
  [types-relay.py][types-relay] `968fb95a` / `6c2e8c20`,
  [relay.py][relay] `a09485a1` / `fd88aafa`,
  [mutations-sets.py][mutations-sets] `f8c64500` / `10724da6`,
  [errors.py][errors] `793855e0` / `6048b7fe`,
  [permissions.py][permissions] `d77c5050` / `42c3c19c`,
  [write-transaction.py][write-transaction] `c0a12b34` /
  `49102e69`, [orders-sets.py][orders-sets] `c4564c08` /
  `125d808c`, [finalizer.py][finalizer] `cb2dde6b` / `7d354e77`,
  [list-field.py][list-field] `77ddb86c` / `1dcb0c43`.
  Oracles (HEAD / worktree):
  [test-querysets.py][test-querysets] `3ff4094a` /
  `b1fc954b`, [test-write-values.py][test-write-values]
  `8d09921b` / `9f459e2f`,
  [test-forms-resolvers.py][test-forms-resolvers] `66498cb4` /
  `6cab42c2`,
  [test-mutations-resolvers.py][test-mutations-resolvers]
  `4f94c05a` / `eeab4fbe`,
  [test-types-resolvers.py][test-types-resolvers] `346e945d` /
  `d78d605f`,
  [test-relay-interfaces.py][test-relay-interfaces] `515ebce5` /
  `3ffb75b8`, [test-filters-sets.py][test-filters-sets]
  `19d508bd` / `fc21a7a8`,
  [test-relay-node-field.py][test-relay-node-field] `7c0f22ed` /
  `7f47c3dd`, [test-library-api.py][test-library-api]
  `91f0238b` / `099e25b9`,
  [test-products-visibility-api.py][test-products-visibility-api]
  `318bc95e` (clean), [library-schema.py][library-schema]
  `75d358f8` (clean).

Prior records (file items s9 / s14, run-7 re-traces) used as
triggers only: the F5 files-covered append (re-derived --
mutations IS a transitive consumer via `:618` / `:654`), the
twin pins, and the "count 1" holdings were all re-derived
above from HEAD bytes before being relied on. The s13
standing note (directory pathspec for censuses) was honored
for every census below.

## Verification

### Matrix

1. Cross-flavor mirroring: model, form, and serializer
   relation decoders all compose the spine by name (7 call
   sites, 0 bodies); the scope-specs path composes the
   `None`-returning primitive directly with its own
   `None`-skip. No flavor carries a second resolve, scope,
   fallback, membership, or subset body.
2. Sync/async twins: the write cluster is sync-only by
   pipeline design (`SyncMisuseError` on async hooks -- the
   write pipeline runs one sync body); the twin and the relay
   node paths are color-aware (async branches honored). The
   color split is the documented pipeline/read contrast
   (principle 5), not drift -- compared by contract, and the
   probe pins both signatures (R6).
3. Derived knowledge: `registry.get` + scope is spelled once
   (`:4498`-`:4501`); the twin takes a resolved type (no
   resolve), relay/locate take their own type (no resolve),
   filters/cascade resolve with their own base + error/skip
   (different contracts). One Django fact, four genuinely
   different compositions -- not four definitions of one
   rule.
4. Round-trip pairs: the recheck has no inverse. The GlobalID
   decode (`type_check_relation_id`) feeds the pk the
   visibility query consumes; the NodeID-to-pk read
   ([relay.py][relay] `:300`) deliberately skips visibility
   because every downstream consumer rechecks -- the omission
   is documented at the read, not a gap.
5. Other media: production (one body per level), oracles
   (listed above, every level pinned independently incl. the
   one-query and query-count tripwires), projections
   (docstrings, verified). Listed, not counted.
6. Enforcement by omission: every write path attaching
   related rows rechecks -- model FK/M2M, form single/multi,
   serializer single/multi/queryset-scoping, update/delete
   locate. The two deliberate non-applications each name
   their reason in prose (refetch own-write exception;
   NodeID pre-resolution downstream-enforced). No member
   lacks a guard its contract requires.

### Enumeration

Instruments: `git grep` censuses with the directory pathspec
(`django_strawberry_framework`, never `**/*.py`) plus
full-body reads of every hit file at HEAD bytes.

- `related_visibility_queryset_or_default`: 1 def (`:4504`)
  + 2 callers (`:4615`, `:4641`) + 2 prose cites, 1 file.
- `related_visibility_queryset`: 1 def (`:4475`) + 2 callers
  (`:4519`, [rf-resolvers.py][rf-resolvers] `:1519`) + prose.
- `visible_related_object`: 1 def (`:4576`) + 1 caller
  (`:236`) + prose; `visible_related_objects`: 1 def
  (`:4620`) + 1 caller (`:326`) + prose.
- `visibility_scoped_related_queryset`: 1 def (`:4451`) + 1
  caller (`:4501`) + prose. `stringified_pks_present`: 1 def
  (`:4535`) + 1 caller (`:4642`) + prose. `pks_all_present`:
  1 def (`:4562`) + 1 caller (`:327`) + prose.
- `decode_visible_relation`: 1 def (`:194`) + 2 callers
  (`:217`, `:259`). `decode_visible_relation_ids`: 1 def
  (`:283`) + 3 callers (`:618`, `:654`, `:288`).
  `type_check_relation_id`: 1 def (`:129`) + 2 callers
  (`:229`, `:316`, both spine-internal).
- `initial_queryset(`: 10 code sites (owner `:4469`, twin
  `:415`, relay x6, locate `:715`, refetch `:864`) + def +
  prose. Every site classified: 1 member composition, 3
  rejected merges, 1 documented exception, prose.
- `apply_type_visibility_sync(`: 13 code callers (owner,
  twin `:428`, twin-many `:452`, relay x3, locate, filters,
  cascade, walker, list-field, connection, post-process) +
  def/overloads + prose. `apply_type_visibility_async(`: 9
  code callers. Every site classified; non-members scope
  their OWN or their consumer's source, never a related
  object by pk.
- `visible_related_object` twin census: private
  `::_visible_related_object` 1 def + 7 gated calls;
  `::_visible_many_rows` 1 def + 2 gated calls. No third
  object-recheck body.
- `pk__in` + `values_list("pk"` membership shape: 1 body
  (`:4559`); the 3 other `values_list("pk"` sites
  ([relay.py][relay] `:300`, [rf-resolvers.py][rf-resolvers]
  `:1932` / `:2048`) are the NodeID read and the attestation
  snapshots -- different rules, zero visibility.
- Subset shape: 1 body (`:4573`); zero `<=` / `issubset`
  re-spellings.
- Every member lands in F-write, R1, R2, R3, R4, R5, or the
  exclusion list above. Nothing unassigned.

### Challenges

Merge tests (posit a change to the SHARED rule; count
definitions forced to move together):

- M1 -- an unregistered related model must now REFUSE
  instead of default-manager fallback: the or_default body
  alone (1 + its oracles). The twin (takes a resolved type),
  relay/locate (own type, no resolve), filters (already
  refuses with its own error) never move. Count: 1.
- M2 -- honor async hooks in async context: twin + relay
  already do (0 new); the write cluster keeps
  `SyncMisuseError` by pipeline design (one sync body --
  changing THAT is architecture, not recheck). Count: 0 for
  this family.
- M3 -- pin the recheck read to the row's own alias: the
  twin alone (1 -- the only site holding an instance).
- M4 -- custom-hooks-only: the twin gate alone (1).
- M5 -- add a step to "scope the initial queryset" (the R5
  shared form): would move 6 sites -- but no such step is
  plausible (three pin disciplines, two colors, twin
  symmetry), and both parts already single-own their own
  changes. Count: N/A, recorded to show the work.

Per-rule challenges:

- C1 -- a fourth write flavor: 2 adapter call sites (single
  + multi colorings via the `skip` / `project` params), 0
  bodies (principle 5 -- the three existing flavors are the
  worked examples).
- C2 -- the fallback gains a step (e.g. alias pin): 1 body
  (`:4504`).
- C3 -- the comparison basis changes: 1 body (`:4525`);
  subset: 1 body (`:4562`).
- C4 -- resolve precedence changes: 1 body (`:4475`); the
  scope-specs consumer untouched (composes by name).
- C5 -- the twin trust boundary changes: 1 gate (`:456`) +
  the twin as its consumer.
- C6 -- node id-attr / required / bulk changes: relay only.
- C7 -- filter missing-primary error changes: filters only.
- C8 -- locate lock shape changes: locate only.

Every genuine rule change moves at most 1 definition. By
DRY's counting rule that is independence, even where the
stated visibility reason coincides.

Probe (execution-verified, disposable copy; read-only -- the
only SQL attempted is a SELECT against a nonexistent table
in an empty in-memory database): `/tmp/e3_probe.py` over a
`git archive HEAD` tree inside the copy (run
`dry-20261001T000756-31604e`, exit 0, package `__file__`
under `head-tree/`), plus the copy's own worktree bytes (run
`dry-20261001T000809-1f1090`, exit 0, identical ALL OK).
Slot venv lacks locked deps (standing s13 infra finding);
both runs used the disclosed
`PYTHONPATH=<shared-venv>/site-packages` shim with the
probed package first on `sys.path`.

- R0: all 28 cluster + consumer names resolve by name.
- R1-R2: unregistered model -> `None`; or_default ->
  unevaluated default-manager queryset (resolve + fallback
  contracts execute as documented).
- R3: subset semantics pure (`True` / `False`).
- R4: twin short-circuits `None` with no query.
- R5: the batched spine composes end to end through the
  owner to a SELECT (`OperationalError: no such table` --
  chain liveness, read-only).
- R6: twin `(related, target_type, info)` vs public
  `(related_model, pk, info, async_recourse)` -- the
  signature contrast execution-pinned.

## Findings

### F-write -- CONFIRMED single-owned, no edit

Contract + variation: a write flavor attaching related rows
by client-supplied id resolves each id through the related
primary's `get_queryset` (default manager when no primary
is registered); hidden and missing collapse to the uniform
`relation_field_error` (no existence leak). Varies by flavor
projection (`skip` / `project` params), recourse wording
(param), and single-vs-batched shape (two spine functions).
Sites + roles: definitions = the 7-helper cluster + the
2-function spine (roles above); consumers = 7 flavor decoder
call sites + the scope-specs direct consumer.
Challenges: M1 = 1 (this contract alone); M2 = 0 (already
covered per color); C1 = 0 bodies; C2/C3/C4 = 1 body each.
Owner + lifetime (principles 7/4): layered -- the cluster
owns the resolve/scope/membership primitives (the narrowest
cohesive owner every flavor already imports), the spine
owns the decode compose, flavors own their colorings;
per-call, nothing stored.
Migration: none -- already single (every link composes by
name, re-derived at every level).
Distinct behavior kept: per-caller `None`-handling (spine
maps to the error, scope-specs skips -- prescribed at the
owner `:4486`-`:4493`); form multi per-element map (needs
the object for `to_field_name`); flavor null policies at
the callers; the refetch exception and the NodeID
pre-resolution (recorded at their owners, cited above).
Behavioral proof: execution-verified (probe R0-R3 + R5) +
static (one body per level, zero second bodies
package-wide).
Structural gate: none proposed -- bypass means not calling
the spine, whose future-flavor population cannot be
enumerated; the per-flavor hidden-attach oracles plus the
one-query (`:658`) and query-count (`:10433`) tripwires pin
the composition instead. A red result would be a defect,
not a gate.
Precision notes (no contract impact, not defects): the
"decoders call it" phrasings at [write-values.py][write-values]
`:140`-`:144` and the owner's `:4459`-`:4464` are
transitive (direct callers are the spine functions) -- the
sharing claims hold; the worktree already rewords the
former toward the spine.
Freshness: fingerprints in System trace (all three states
for indexed files; HEAD/worktree for cited + oracles).

### R1 -- REJECTED: read-path twin merge

Shared form considered: treating
`::_visible_related_object` as a second definition of the
resolve-through-visibility rule, or routing one through
the other.
Contract differences (each independently fatal):

1. Subject: a materialized read-path instance (prefetch
   cache, unplanned relation, FK stub) vs a write-input
   client pk. Different populations, different trust
   postures.
2. Trigger: CUSTOM hooks on UNPLANNED relations only (both
   gates at all 9 call sites) vs always recheck whatever
   hook the primary declares. Default-identity targets
   never reach the twin.
3. Resolve: takes a resolved type (no resolve, no fallback)
   vs resolves + default-manager fallback. M1 moves only
   the public side.
4. Color: color-aware (async branch `:424`-`:427`) vs
   sync-only (`SyncMisuseError`). M2 moves neither (twin
   already covers its color; the public side's stance is
   the pipeline's rule).
5. Alias: pinned to the instance's own `_state.db`
   (`:416`-`:418`) vs default routing + pipeline pin. M3
   moves only the twin.

Challenges: M1/M3/M4 = 1 per side; M2 = 0; C5 = 1 gate.
Reconsideration trigger: the twin drops its gates (runs
every hook unconditionally), goes sync-only, AND takes
`(model, pk)` -- i.e. becomes the public signature (R6
pins the distance).
Durable home: already at the owner -- the twin one-liner
plus the `::_custom_visibility_type` (custom-only reason)
and `::_optimizer_scoped_relation` (per-relation trust
boundary) docstrings jointly record the split. No edit
owed.

### R2 -- REJECTED: Relay node merge

Shared form considered: the 6 inline
`apply(initial_queryset(cls), ...)` compositions in
`::_resolve_node_default` / `::_resolve_nodes_default` (+
async sibs) as second definitions of the scoping
composition.
Contract differences: SELF-type node identity resolution
(`cls`, never a related model -- no resolve, no fallback);
sync/async TWIN pair (no async owner exists -- routing the
sync half through the owner splits the twin for zero
obligation relief); id-attr filter + required
(`get`/`DoesNotExist`) vs lenient (`first`/`None`) +
order-preserving bulk -- a richer contract than "scope
the base".
Challenges: C6 = relay only; M1/M2/M4 never move it.
Reconsideration trigger: an async sibling of the owner
appears AND relay collapses to pk-first (abandons
id-attr/required/bulk) -- or the family explicitly widens
to "scope any initial queryset" (then R5 re-opens).
Durable home: already at the owner -- `::initial_queryset`
names the Relay four-step shape, and the node docstrings
state the color + required contracts. No edit owed.

### R3 -- REJECTED: write-target locate merge

Shared form considered: `::locate_instance`'s
`:713`-`:717` composition as a second definition.
Contract differences: subject is the write TARGET
(self-type), not a related object; the pin + row-lock
sandwich (`pin_write_queryset` + `base_locked_queryset` +
`get` / `DoesNotExist` -> `None`) is the locate's own
concurrency contract; no resolve, no fallback. Routing
through the owner would relieve no change obligation (the
composition has no variation of its own -- R5) while
misnaming the subject ("related").
Challenges: C8 = locate only; M1/M3/M4 never move it.
Reconsideration trigger: locate drops pin + lock (the
concurrency hardening reverted to plain pk-first).
Durable home: already at the owner -- the docstring states
the visibility + pin + lock contract. No edit owed.

### R4 -- REJECTED: filter-branch derivation merge

Shared form considered: `::_derive_related_visibility_querysets_sync`
/ `_async` as second definitions of resolve-through-visibility.
Contract differences: subject is per-branch QUERYSETS for
filter composition, not objects by pk; the no-primary
default is OPPOSITE -- `ConfigurationError` refusal
(`:2690`-`:2705`: skipping would silently return
unfiltered rows) vs default-manager fallback; the base is
alias-pinned (`parent_db`) with recursion into child
`apply` plus the `run_permissions=False` permission
contract. It composes the LOWER rule (`apply_*`) by name --
sharing the visibility boundary is not sharing this rule.
Challenges: C7 = filters only; M1 moves the opposite
default (refusal text) while the owner moves the fallback.
Reconsideration trigger: filters adopt default-manager
fallback for unregistered targets (abandon the
refuse-to-skip contract).
Durable home: already at the owner -- the refusal + alias
+ permission docstrings state the contract. No edit owed.

### R5 -- REJECTED: one-line composition routing

Shared form considered: routing the twin, relay x6
(sync), and locate inline `apply(initial_queryset(...))`
compositions through `::visibility_scoped_related_queryset`.
No own variation: every plausible change to the parts
moves the already-single lower owners (`::initial_queryset`,
`::apply_type_visibility_sync`), never the composition as
a unit (M5). The surroundings defeat sharing without mode
flags: three pin disciplines (none / instance alias /
write alias), two colors, relay twin symmetry, and the
name misleads (no subject is related). Token-sharing
without obligation relief is not a DRY finding
(principle 11, reverse).
Reconsideration trigger: a composition-level step all
four sites adopt identically.
Durable home: this finding (the composition is one line;
the reasons live with the per-site contracts above). No
edit owed.

Worker-0 index rows (this family item names; plan edits are
Worker-0's):

- Family `related-object-visibility-recheck` -> status
  `consolidated` (F-write single-owned, no edit; R1-R5
  exclusions with triggers; D1 doc-only defect filed).
- Files-covered REVISE: drop `types/resolvers.py` (the twin
  is its own file-local rule below); keep `utils/querysets.py`,
  `utils/write_values.py`, `rest_framework/resolvers.py`,
  `forms/resolvers.py`, `mutations/resolvers.py` (transitive
  consumer, confirmed via `:618` / `:654`).
- `types-relation-instance-recheck` | owner
  [types-resolvers.py][types-resolvers]
  `::_visible_related_object` (+ `::_visible_many_rows`
  many-side sibling) | files `types/resolvers.py` | holding
  item Family `related-object-visibility-recheck` | status
  `file-local` (1 twin body + 7 gated calls + 1 many body +
  2 gated calls; public-helper merge excluded in R1 with
  trigger).
- No new rows for R2/R3/R4 (each lives entirely in one
  already-verified file item's territory; the exclusions
  carry the triggers) or R5 (a non-rule).

## Defects

- D1 (doc-only, owner [querysets.py][querysets]
  `::visible_related_object` docstring `:4594`): cites
  ``_relation_visibility_error`` ("the `036`
  ``_relation_visibility_error`` does not return"), a helper
  extinct at HEAD -- the name's last def was in
  [mutations-resolvers.py][mutations-resolvers] before the
  spec-039 consolidation (`efe1ad6c` moved the sentence
  here; the surviving equivalent is
  [errors.py][errors] `::relation_field_error` `:322`).
  Persists in the worktree (cluster has zero hunks). Route:
  closeout doc correction (one cite reword, no behavior).

## Pending execution

- `proof:` `uv run python scripts/workspace.py run
  dry/relvis-recheck-e3/consolidate -- sh -c
  'PYTHONPATH=<shared-venv>/site-packages python3
  /tmp/e3_probe.py head-tree'` -- execution-verified
  (run `dry-20261001T000756-31604e`, exit 0, `E3-PROBE ALL
  OK`, package `__file__` under `head-tree/` holding `git
  archive HEAD` bytes; discharges F-write R0-R3 + R5, R1
  R4 + R6). `<copy>` =
  `/private/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/dsf-ws/0b901faeac791a7b/dry/slots/slot-2`,
  `<shared-venv>` =
  `~/.t3/worktrees/django-strawberry-framework/dry-0015/.venv/lib/python3.14/site-packages`.
  The `head-tree/` extraction + `/tmp/e3_probe.py` stay on
  disk for Worker-2; remove by explicit path after
  verification.
- Worktree comparison (same command, `.` as the tree):
  run `dry-20261001T000809-1f1090`, exit 0, identical ALL
  OK -- decision-neutral drift proved behaviorally.
  Informational; discharges nothing.
- Shared-tree authorization unspent: zero edits landed, no
  oracle added, no pytest run -- no `gate:` command owed.

## Judgment

The related-object visibility recheck is one rule with a
single body at every layer: the 7-helper cluster owns the
resolve/scope/membership primitives, the 2-function spine
owns the decode compose, and all three write flavors plus
the scope-specs path consume them by name (7 decoder call
sites, 0 second bodies). The lookalikes are distinct
per-site rules -- the read-path twin (custom-only,
unplanned-only, color-aware), Relay node identity, the
write-target locate, and the filter-branch derivation
(which refuses where this rule falls back) -- each
single-owned, each excluded on contract differences with
a trigger. Zero production edits; one doc-only defect
filed. The family is CONFIRMED as consolidated.

Item-scoped diff state: no tracked edits; one new untracked
artifact (this file). `git diff 7f549142 --stat` names only
`docs/dry/dry-0_0_15.md` (+22 dispatch lines); all package
dirt pre-dates the baseline (verified `7f549142` tree bytes
== worktree bytes on all six indexed files). Scratch:
`<copy>/head-tree/` (HEAD-bytes extraction, copy-only) +
`/tmp/e3_probe.py` (read-only probe, OS temp).

## Independent verification (Worker-2)

### Own trace (HEAD `83998e08` bytes, directory pathspec)

Censuses below are all `git grep -n <name> HEAD --
django_strawberry_framework` plus full-body reads; counts are
mine, re-derived before reconciling with `## Findings`.

- Owner I would choose: the same layered owner --
  [querysets.py][querysets]
  `::related_visibility_queryset_or_default` (`:4504`) for the
  resolve + default-manager fallback, the cluster for the
  resolve/scope/membership primitives, the spine for the
  decode compose, flavors for their colorings. No rival
  owner: every other candidate body resolves its own type
  (relay, locate), an already-resolved type (twin), or
  refuses where this rule falls back (filters).
- Cluster defs: 8 in `:4451`-`:4645` (7 public + private
  `::_stringified` `:4525`). `or_default`: 1 def + 2
  callers (`:4615`, `:4641`). `related_visibility_queryset`:
  1 def + 2 callers (`:4519`, [rf-resolvers.py][rf-resolvers]
  `:1519`). `visibility_scoped_related_queryset`: 1 def + 1
  caller (`:4501`). `stringified_pks_present`: 1 def + 1
  caller (`:4642`). `pks_all_present`: 1 def + 1 caller
  ([write-values.py][write-values] `:327`).
  `visible_related_object`: 1 def + 1 caller (`:236`).
  `visible_related_objects`: 1 def + 1 caller (`:326`).
- Spine: `decode_visible_relation` 1 def (`:194`) + 2
  callers ([forms-resolvers.py][forms-resolvers] `:217`,
  [rf-resolvers.py][rf-resolvers] `:259`);
  `decode_visible_relation_ids` 1 def (`:283`) + 3 callers
  ([mutations-resolvers.py][mutations-resolvers] `:618` /
  `:654`, [rf-resolvers.py][rf-resolvers] `:288`);
  `type_check_relation_id` 1 def (`:129`) + 2
  spine-internal callers (`:229`, `:316`);
  `materialize_relation_id_container` 1 def (`:255`) + 2
  callers (`:309` spine-internal, forms `:260`).
- Consumer links: 5 spine-direct + forms-multi `:266`
  (flavor-single map) + forms-multi `:260` (materializer) +
  scope-specs `:1519` (direct `None`-skip `:1525`, AND
  `:1528`-`:1529`, pin + lock). Zero additional sites.
- `initial_queryset(`: 10 code sites (owner `:4469`, twin
  [types-resolvers.py][types-resolvers] `:415`, relay x6,
  locate `:715`, refetch `:864`) + def + prose.
- `apply_type_visibility_sync(`: 13 code callers;
  `apply_type_visibility_async(`: 9 code callers. Every
  non-member scopes its own or its consumer's source (spot
  bodies read: cascade, post-process x2, connection,
  list-field, walker, filters) -- never a related object
  by pk.
- Twin: 1 def (`:407`) + 7 calls (`:651` / `:666` / `:727`
  / `:744` / `:763` / `:800` / `:820`); many sibling 1
  def (`:431`) + 2 calls (`:589` / `:613`).
  `::_custom_visibility_type` (`:381`, 1 call `:564`);
  `::_optimizer_scoped_relation` (`:456`, 8 calls).
- `values_list("pk"`: 4 code sites -- the one body
  (`:4559`), [relay.py][relay] `:300` (NodeID read, no
  visibility, downstream-enforced per its `:269`-`:272`
  doc), attestation snapshots (`:1932` / `:2048`, bodies
  read, no visibility). Subset `<=`: 1 body (`:4573`),
  zero `issubset`. `{str(pk)}`: 1 body (`:4532`).
- `registry.get(` related-model resolves: owner `:4498`
  (resolve + scope + `None`), twin gate `:398`
  (custom-only, no scope), cascade `:701` (skip-on-None,
  own base), filters `:2218` / `:2918` (owner-aware type
  resolve, no scope), relay `:877` (GlobalID shape
  decode, raises), schema-build sites (no scope). No
  second resolve-through-visibility.
- Sync-only: zero `async def` / `await` in `:4451`-`:4645`
  and spine `:129`-`:330` (prose mentions excepted);
  twin + relay carry both colors (branches read).
- Oracles spot-read by content: `:216` boundary,
  `:4677` subset, `:4685` single, `:658` one-query,
  forms `:1320` no-primary, twin `:1290` / `:1445`,
  live `:8903` / `:8925` / `:10433` -- all as cited.

### Reconciliation

- Enumeration: every member count above matches W1's
  bullet-for-bullet, with two readings pinned down: the
  "7-helper cluster" is the 7 public helpers (plus
  private `::_stringified`, 8 defs in range); the "7
  decoder call sites" are the 5 spine-direct calls plus
  the 2 shared-composition calls inside the forms-multi
  body (`:260`, `:266`). Nothing unassigned; the
  zero-second-body claim holds on my censuses.
- F-write: confirmed -- one body per level, every link
  composes by name, per-caller `None`-handling as
  prescribed at the owner (`:4486`-`:4493`). M1 = 1
  (or_default alone); M2 = 0; C1 = 0 bodies (the three
  flavors + `relation_into` wiring are the worked
  pattern); C2/C3/C4 = 1 body each.
- R1: the 5 contract differences re-derived at the twin
  body (`:407`-`:430` + gates): instance subject,
  custom-only + unplanned-only trigger, resolved-type
  input (no resolve/fallback), color-aware
  (`:421`-`:427`), instance-alias pin (`:416`-`:418`).
  M1/M3/M4 = 1 per side; trigger (drop gates + go
  sync-only + take `(model, pk)`) is the correct
  reunion condition. One precision correction (WD2
  below); the difference itself stands.
- R2/R3/R4: contract differences re-derived at the
  bodies (relay `:949` + async sibs: self-type,
  id-attr, required/lenient, bulk; locate `:683`-`:725`:
  self-type target + pin/lock/`get`; filters `:2711` /
  `:2771` + refusal `:2690`-`:2705`: opposite default,
  alias-pinned base, 5 call sites). C6/C7/C8 each
  single-homed. Triggers are the correct reunion
  conditions.
- R5: confirmed non-rule -- the 8 inline compositions
  (twin, relay x6, locate) share no variation of their
  own; three pin disciplines + two colors + twin
  symmetry defeat sharing; both parts single-owned.
- D1: the defect is real -- `_relation_visibility_error`
  occurs exactly once package-wide (the `:4594` cite),
  zero defs anywhere, zero hits in tests/examples; the
  survivor [errors.py][errors] `::relation_field_error`
  (`:322`) documents the spec-039 fold; the cite
  persists in the worktree (`:4533`); closeout routing
  is correct. One provenance correction (WD1 below).
- Index rows judged as exact replacement text:
  `consolidated` + files-covered REVISE (drop
  `types/resolvers.py`, keep the other five with
  mutations as transitive consumer via `:618` / `:654`)
  + new file-local row `types-relation-instance-recheck`
  (all 9 twin/many call sites verified inside
  `types/resolvers.py`) + no rows for R2/R3/R4/R5 --
  endorsed, with WD2/WD3 wording applied on
  transcription.
- Matrix 1-6: discharged -- cross-flavor (7 links, 0
  bodies), color split (pipeline-sync vs read-colorful,
  structural), derived knowledge (one resolve+scope
  spelling, four different compositions), round-trip
  (no inverse; NodeID omission documented at the read),
  oracles + projections (listed, spot-verified), no
  omission gap (both non-applications documented
  in prose at their sites).
- Dirt attribution: cluster zero hunks (mechanical
  overlap check over `:4451`-`:4645`); bracketing
  `:4431` / `:4711` hunks are truth migration; twin
  body + all 7 call shapes intact in the worktree
  (hunks are `check_deadline` + adopted
  `run_in_one_sync_boundary` orphan arms); spine tail
  intact in the worktree (restructure is the
  type-check half); rf `:1514` hunk is the disclosed
  pin-label rename; forms `:182`-`:280` and mutations
  `:589`-`:870` clean (mechanical checks). All
  decision-neutral; BASE `7f549142` == worktree on all
  six indexed files (hashes below).
- Fingerprints (mine): [querysets.py][querysets] HEAD
  `392e50d0` WT `cfc773ba`; [types-resolvers.py][types-resolvers]
  HEAD `574e9768` WT `7a953c53`;
  [write-values.py][write-values] HEAD `01a3318c` WT
  `4fa8118d`; [rf-resolvers.py][rf-resolvers] HEAD
  `420fc3ca` WT `3fc6a366`;
  [forms-resolvers.py][forms-resolvers] HEAD `ea839d84`
  WT `6e613333`; [mutations-resolvers.py][mutations-resolvers]
  HEAD `7a25afea` WT `dd00ec6e` -- all equal to W1's,
  all BASE == WT. Cited spot-checks match W1
  (filters `3d307402`/`ec278851`, relay
  `968fb95a`/`6c2e8c20`, errors
  `793855e0`/`6048b7fe`).
- Zero-edit: `git diff 7f549142 --stat` names only
  `docs/dry/dry-0_0_15.md` (+42 dispatch lines, window
  grown since W1's +22, still dispatch-only). No
  tracked file touched by either worker; my scratch is
  `/tmp/e3w2_probe.py` + `/tmp/e3w2_head/` (OS temp,
  outside the repo). W1's probe and slot-2 tree were
  not read or executed.

### Execution (own probe, HEAD bytes)

`/tmp/e3w2_probe.py` (authored fresh, never read W1's)
over a `git archive HEAD` tree at `/tmp/e3w2_head`,
run `dry-20261001T002755-1bd8f2`, exit 0,
`E3W2-PROBE ALL OK`, package `__file__` under
`/tmp/e3w2_head/`, read-only (in-memory sqlite; the
only SQL is a SELECT against a nonexistent table):

- V0 names resolve; V1 unregistered model -> `None`;
  V2 or_default -> unevaluated default-manager
  queryset; V3 subset `True` / `False`; V4 twin
  `None` short-circuit with zero queries
  (`CaptureQueriesContext`); V5a batched + V5b single
  spine -> owner -> SELECT (`OperationalError: no such
  table`); V6 signature contrast
  `(related, target_type, info)` vs `(related_model,
  pk, info, async_recourse)`. Discharges the F-write
  compose-by-name chain and the R1 twin distance. No
  pytest run (probe-only, per dispatch).

### Defects (Worker-2)

- WD1 (precision, D1 parenthetical): "`efe1ad6c` moved
  the sentence here" is wrong. `efe1ad6c`'s querysets
  hunk only adds
  `::visibility_scoped_related_queryset`; the sentence
  arrives via `60dbf469` ("Finish
  spec-039-serializer_mutations-0_0_13.md", 2026-06-27;
  `-S'does not return'` hit, adds the exact lines). The
  "last def in mutations-resolvers before spec-039"
  half is correct (`e9c13f55~1:711` has the def;
  `e9c13f55` removes it). Correction for closeout to
  apply with the D1 reword; no behavior impact.
- WD2 (precision, R1 difference 2): "both gates at all
  9 call sites" overreaches by one -- `:613`
  (unprefetched many path) carries only the
  custom-only gate; 8/9 are both-gated. The trigger
  substance stands (a fresh manager queryset is
  trivially unplanned, so the second gate holds
  vacuously there). Worker-0 wording: "both gates at
  8 sites; custom-only at the unprefetched many path
  (`:613`), unplanned-by-construction".
- WD3 (precision, cite): `::materialize_relation_id_container`
  is defined at `:255`, not `:260`. No impact.

Verdict: verified. Every row (F-write, R1-R5, D1, the
index-row instructions) survives on the independent
evidence above; WD1-WD3 are decision-neutral wording
corrections recorded here for closeout/Worker-0, not
round-trips. The plan-item tick is left to the
maintainer (the plan file is tracked and this
delegation touches nothing tracked except this
artifact).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[errors.py]: ../../django_strawberry_framework/utils/errors.py
[filters-sets.py]: ../../django_strawberry_framework/filters/sets.py
[finalizer.py]: ../../django_strawberry_framework/types/finalizer.py
[forms-resolvers.py]: ../../django_strawberry_framework/forms/resolvers.py
[list-field.py]: ../../django_strawberry_framework/list_field.py
[mutations-resolvers.py]: ../../django_strawberry_framework/mutations/resolvers.py
[mutations-sets.py]: ../../django_strawberry_framework/mutations/sets.py
[orders-sets.py]: ../../django_strawberry_framework/orders/sets.py
[permissions.py]: ../../django_strawberry_framework/permissions.py
[querysets.py]: ../../django_strawberry_framework/utils/querysets.py
[relay.py]: ../../django_strawberry_framework/relay.py
[rf-resolvers.py]: ../../django_strawberry_framework/rest_framework/resolvers.py
[types-relay.py]: ../../django_strawberry_framework/types/relay.py
[types-resolvers.py]: ../../django_strawberry_framework/types/resolvers.py
[walker.py]: ../../django_strawberry_framework/optimizer/walker.py
[write-transaction.py]: ../../django_strawberry_framework/utils/write_transaction.py
[write-values.py]: ../../django_strawberry_framework/utils/write_values.py

<!-- tests/ -->
[test-filters-sets.py]: ../../tests/filters/test_sets.py
[test-forms-resolvers.py]: ../../tests/forms/test_resolvers.py
[test-mutations-resolvers.py]: ../../tests/mutations/test_resolvers.py
[test-querysets.py]: ../../tests/utils/test_querysets.py
[test-relay-interfaces.py]: ../../tests/types/test_relay_interfaces.py
[test-relay-node-field.py]: ../../tests/test_relay_node_field.py
[test-types-resolvers.py]: ../../tests/types/test_resolvers.py
[test-write-values.py]: ../../tests/utils/test_write_values.py

<!-- examples/ -->
[library-schema.py]: ../../examples/fakeshop/apps/library/schema.py
[test-library-api.py]: ../../examples/fakeshop/test_query/test_library_api.py
[test-products-visibility-api.py]: ../../examples/fakeshop/test_query/test_products_visibility_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
