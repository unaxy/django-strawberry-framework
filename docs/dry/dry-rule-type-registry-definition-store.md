# DRY review: `type-registry-definition-store`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-registry-definition-store`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F2 aspects).
Member files: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/base.py`,
`django_strawberry_framework/types/finalizer.py` (all three worktree-clean
vs `HEAD` `bfaee91d` and vs `ITEM_BASELINE`
`534f67ea6cbc38b05a0bda008653c294e8dce310`: both diffs empty, confirmed).
Prior records used only as triggers, never verdicts: the registry file
item's F2 aspects + R2/R3 (`docs/dry/dry-file-registry.md`, verified),
the `dry-0_0_11.md` rollback-mirror deferral, and the just-verified
sibling `type-registry-enum-cache` (its F4/F1/F2/F3/F5 boundary statement
— checked, not inherited; every edge below re-derived). Never read any
`worker-memory/`.

## System trace

Rule: the registry's memory of WHAT was declared. Exactly one collected
`DjangoTypeDefinition` per type class, written through one atomic
register-plus-define pair at class creation, read back by identity for
finalization, relation resolution, decoding, and inspection. The store
answers "what did this type declare"; the model-type map (F1) answers
"which types serve this model"; the pending ledger (F3) answers "which
relations still need a target". Three aspects on one class, three
contracts — or the split is the duplication. It is three contracts
(rejected consolidation; see F1).

Boundary against the sibling families on the one class (re-derived, agrees
with the enum-cache statement): F1 owns `_types` / `_primaries` /
`_models` plus `register` / `unregister` map arms / `get` and friends; F2
owns `_definitions` plus `register_definition` /
`register_with_definition` / `get_definition` / `iter_definitions`; F3
owns `_pending` plus identity-matched add/discard; F4 owns `_enums` plus
`register_enum` / `get_enum`; F5 owns `_finalized` plus `_check_mutable` /
`mark_finalized`. The `_definitions.clear()` / `.pop()` lines inside
`clear()` / `unregister` are those lifecycles consuming F2 state, not
second definitions. `definition_for_graphql_name` lives on the registry
but its name-key decode contract (Relay-Node-only scan over
`graphql_type_name`) is owned rule-wise by Family
`relay-node-name-decode` — F2 owns the storage it scans, that family owns
what the scan means.

Sites + roles. *Definitions* (one each, counts probe-pinned):
`register_definition`, `register_with_definition`, `get_definition`,
`iter_definitions` ([registry][registry]`::TypeRegistry`); the
`_definitions` dict (written at exactly one store line, dropped at exactly
one `unregister` line and one `clear()` line); the single
`DjangoTypeDefinition(...)` construction site and the single
`cls.__django_strawberry_definition__ = definition` alias write (both in
[base][base]`::DjangoType.__init_subclass__`, one flow, one object).
*Producer*: `DjangoType.__init_subclass__` (sole; no other production
caller of the pair). *Consumers*: the finalizer phase loops + Phase-1
pending resolution + both multi-type audits (all via `get_definition` /
`iter_definitions`); `definition_for_graphql_name` (name-key scan);
the inspect command's bare-name resolver (SDL/Python-name scan);
the list-field constructor guard + `global_id_for` (registry-canonical
identity checks against the alias); optimizer walker / extension,
relation resolvers, Relay decode, connection/keyset paths (all
`get_definition` by name); `related_target_for` (reads its own record +
`registry.get`, never a second store). *Oracles*:
[test-registry][test-registry] (rebind rejection, the 4-test rollback
pack, unregister-drop, clear map/enum arms, idempotent-finalize pair,
name-decode 5-pack, clear-then-rebuild pair),
`tests/types/test_base.py` (clear-drop map arm, primary-flag introspection
rows), `tests/types/test_definition_order.py` (declare→pending→resolve
lifecycle), `tests/types/test_finalizer.py` (missing-definition typed
failure), `tests/test_list_field.py` (guard rejections incl. the
unregistered-target `None` row). All spell literals independently (plain
test classes, `object()` sentinels); none enumerates the owner.
*Projections*: the `register_definition` asymmetry note, the
`register_with_definition` atomicity/rollback docstring, the
`_detach_type_from_model` shared-inverse docstring, the
`DjangoTypeDefinition` invariants docstring (primary-mirror +
finalized-once clauses), [spec-018][spec-018] (pair shape, rollback
pseudocode, primary-truth clause), [spec-009][spec-009] (single-definition
invariant prose), [spec-016][spec-016] (`field_map`-on-definition
canonical-store precedent), the glossary `DjangoTypeDefinition` entries,
[TREE.md][tree] (module one-liners).

Connected sources read for judgment, outside the members:
[definition][definition] (record shape + mirror clauses),
[relations][relations] (F3 record shape, trigger-checked only),
[relay-types][relay-types] (decode read leg),
[root-relay][root-relay] (alias reads on error/stamp paths),
[list-field][list-field] (guard: registry-canonical identity pin),
[testing-relay][testing-relay] (guard: alias-vs-canonical identity pin),
[inspect][inspect] (bare-name scan + class-attr read),
[querysets][querysets]`::model_for` (alias read; routed to F1, not
claimed), [mutation-sets][mutation-sets] (R3 neighbor contrast),
installed `.venv` Strawberry (no definition vocabulary on the enum path —
not re-read here; the F4 artifact owns that anchor). Excluded on strength
of body: every other package module (zero `register_definition` /
`get_definition` / `iter_definitions` / `_definitions` vocabulary over
the 117-file sweep); the filter/form/serializer input builders (read
fields through `convert_scalar` / sidecar slots, never the store).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The mutation/form declaration
   ledgers (`make_declaration_registry` pair) are pre-bind, per-flavor,
   disjoint-by-design declaration lists — a different subject
   (declared operations) from collected type definitions, contrast
   stated at [mutation-sets][mutation-sets] and trigger-checked (R3).
   Filter/Order sidecars bind their owner *onto the set*
   (`set_cls._owner_definition`), never into the definition. No flavor
   keeps a second DjangoType-definition store (package sweep:
   `DjangoTypeDefinition(` == 1).
2. **Sync/async twins.** Zero `AsyncFunctionDef` across all five read
   modules (AST-verified: registry 30/0, base 32/0, finalizer 42/0,
   definition 8/0, relations 3/0; the `async def` strings in `base.py`
   are prose + error text about consumer encoders, never a twin).
   Collection/finalization/lookup are import-time dict work; no ORM I/O,
   no awaits. Trigger: an async twin of the pair or the scan.
3. **Derived rather than repeated knowledge.** `definition.model` (record
   field) vs `_models[type]` (reverse index): one `Meta.model` value
   feeds both writes in one flow; reads serve different queries and no
   production site scans definitions by model (C5: zero sites).
   `graphql_type_name` derived once (the definition property; the
   `Meta.name`-honoring rule). `definition.primary` written once, read
   zero times in-package (C6 contrast; [spec-018][spec-018] pins
   `_primaries` as the truth). Trigger: a second derivation site.
4. **Inverse / round-trip pairs.** register/get, pair/rollback,
   finalize-read/clear-drop, alias/canonical identity — all pinned by
   oracles below. No un-define primitive besides `unregister` (one type)
   and `clear()` (all) by design.
5. **Contracts restated in another medium.** Production (owner pair +
   sole producer); oracles (independent literals, no owner reads);
   projections (docstrings verified against bodies; specs pin the pair
   shape and the single-definition invariant; glossary + TREE describe,
   never restate, write rules). The `register_definition` asymmetry
   clause ("caller owns ordering") matches the `base.py` call order.
6. **Enforcement by omission.** `_check_mutable` guards every F2 mutator
   (`register` via the pair, `register_definition`, `unregister`;
   `clear()` bypasses by its documented test-only contract);
   `get_definition` / `iter_definitions` are deliberately unguarded pure
   reads — post-finalize decode *requires* reads through the finalized
   snapshot, so guarding them would break request time. `clear()` drops
   definitions + pending in one method (C4). No member lacks a guard its
   contract requires: no defect.

### Enumeration

Instrument: `ast.parse` function counts + token sweeps over the 117-file
package population (`git ls-files django_strawberry_framework | grep -c`
= 117, re-counted). Every store member assigned; every challenge ends in
the family row or a recorded rejection (no file-local row — each overlap
has its owning family or rejection recorded).

- `register_definition` / `register_with_definition` / `get_definition`
  / `iter_definitions`: exactly 1 def each; the only production caller
  of the pair is `__init_subclass__` ([base][base] single call line);
  the only `DjangoTypeDefinition(` site is the same flow.
- `_definitions`: exactly 1 storage dict; exactly 1 store line, 1
  `unregister` pop line, 1 `clear()` reset line; `register` never
  touches it, the rollback never touches it (pre-existing pin survives
  by construction — probe + oracle pinned).
- `cls.__django_strawberry_definition__` write: exactly 1 site, same
  object as the stored definition (identity probe-pinned).
- `definition_for_graphql_name`: 1 def (rule-wise a consumer owned by
  `relay-node-name-decode`; storage-wise the scan over F2 state).
- Real `for ... in ....iter_definitions()` loops: exactly 3 files
  (registry itself, finalizer phase loops, inspect bare-name resolver);
  the [mutation-sets][mutation-sets] mention is a docstring contrast
  (R3), not a loop.
- `definition.primary` package reads: zero. `definition.model`
  model-keyed definition scans: zero.

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes E1 map one-to-one
onto C1–C6 (42/42 `execution-verified`).

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Second type for one model (secondary view, proxy, MTI child) | **1** (one record per type class, keyed by `type_cls`; map multiplicity + the finalize ambiguity audit are F1/F5 business). Oracle: `test_register_two_types_same_model_without_primary_allows_both_in_types_for` + the ambiguity-audit rows + the live multi-type row. Probes E-C1 + E-ambiguity. |
| C2 | Re-registration of the same class (same vs different definition object) | **1** (the collision arm; same-object re-register is a no-op in both maps). Oracles: `test_register_definition_rejects_different_definition_for_same_type` + the 4-test rollback pack. Probes E-C2 + E-rollback. |
| C3 | `finalize_django_types()` twice | **1** (the entry guard + per-type `finalized` skip are one pair; the flag flips at exactly one Phase-3 line). Oracles: `test_finalize_is_idempotent` + `test_finalize_skips_definitions_marked_finalized_when_registry_is_unfinalized`. Probe E-C3. |
| C4 | `clear()` between declare and finalize (pending-definition loss) | **1** (one `clear()` drops both maps together; the vacuous re-finalize then marks). Standing pins: `test_clear_drops_all_state` (map/enum arms), the clear-then-rebuild pair, the unregister-drop row; the definition/pending arms have no standing assert — D1 (proof-strength, unfixed). Probes E-C4. |
| C5 | Answer model→type by scanning definitions instead of the map | **0** (no such site; consolidating that direction would delete the F1 index every hot path reads). Rejected; stays with F1. Probe E-C5 (loop census). |
| C6 | Alias/registry divergence (`unregister`/`clear`, then read via the class attribute) | **1 canonical** (the registry; the alias is the same object with MRO-inherited lookup semantics, identity-pinned at both strict gates). Oracles: the list-field guard rows, `global_id_for` guard rows, `test_unregister_removes_from_types_models_primaries_definitions`, `test_clear_does_not_remove_mutation_from_previously_finalized_classes`. Probes E-alias + E-unregister. |

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/definition-store-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_definition_store.py
```

Proof (`CHECKS_PASSED=42/42`): store/accessor/construction
singularity counts, per-type records + coexistence, ambiguity raise,
re-register idempotence + collision wording + preservation, rollback
atomicity + re-register-after, decorate-once + flag pair, clear drops
definition + pending + iteration with vacuous re-finalize, rebuild after
clear, loop census (3 files), no model-keyed scan, alias identity +
unregister divergence shape, post-finalize read/unmutated-write split,
primary flags + map predicate. Status: `execution-verified`. Rejects "a
second store exists", "the pair has a second caller", "the map can be
re-derived from a definition scan", "the alias is independently
maintained". Copy `__file__`:
`.../dry-ws/definition-store-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/definition-store-w1/examples/fakeshop/db.sqlite3` (copy's own
tree and database; never the shared tree; the probes open no DB at
all). No source mutation in the proof; restores N/A. Searched
population inside the copy: 117 `.py` (matches the shared tree).

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "register_definition
or register_with_definition or unregister_removes or clear_drops_all_state
or finalize_is_idempotent or definition_for_graphql_name or
finalized_when_registry_is_unfinalized or clear_allows_fresh"` → 18
passed (rebind, rollback 4-pack, unregister, clear, idempotent pair,
name-decode 5-pack, rebuild pair).

## Findings

### F1 — definition store (REJECTED consolidation: single-owned, overlaps intentionally separate)

- **Contract + variation.** One collected definition per type class;
  atomic register-plus-define with snapshot-conditional rollback. Varies
  on: same-object re-register (no-op) vs different-object rebind
  (raise); appended-state rollback (restore snapshot) vs `unregister`
  (purge unconditionally); drop-one vs drop-all.
- **Sites + roles.** *Definitions*: the pair + both accessors + the
  scan + the storage (one each). *Producer*: `__init_subclass__`
  (sole). *Consumers / oracles / projections*: as listed in System
  trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1; C4 → 1; C5 → 0; C6 → 1
  canonical. Count > 1 nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/registry.py::TypeRegistry` (F2 aspects)
  stands: narrowest cohesive owner every consumer can import without
  reversing a dependency (`base.py` already imports the registry; the
  reverse would cycle — [definition][definition] reaches the registry
  only in-function for exactly this reason). Stored-derivation
  lifetime: validity key = declare → `clear()`/`unregister`; publish
  point = `register_with_definition` inside `__init_subclass__` (single
  flow writes the map entry, the store entry, and the alias from one
  `Meta`); who may mutate = `register_definition` (import-time-only via
  `_check_mutable`) + `unregister` (drop one) + `clear()` (drop all,
  test-only bypass); reads = `get_definition` / `iter_definitions`
  (unguarded by design — the finalized snapshot serves request-time
  decode); never mutated post-construction (the record is built once;
  only `finalized` flips, owned rule-wise by F5). Between declare and
  finalize readers are the field-factory guards + the finalizer; between
  finalize and clear, decode/optimizer/inspect (read-only); after
  `clear()`, the class attribute is intentionally stale (lifecycle
  split, C6).
- **Migration.** None (zero-edit rejection: no behavior hunk, no test
  hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** Per-type keying (a second type
  is a second record, not a map collision — C1); retry idempotence vs
  collision (same object vs different object — C2); snapshot restore vs
  purge (rollback vs `unregister` — R2 re-checked); drop-one vs drop-all
  (`unregister` vs `clear()` — C4/C6); record field vs index
  (`definition.model` vs `_models` — R-A); alias lookup semantics
  (MRO-inherited vs exact-key — R-B); introspection mirror vs predicate
  (`definition.primary` vs `_primaries` — R-C).
- **Behavioral proof.** `execution-verified` for singularity counts,
  coexistence, ambiguity, idempotence, collision + preservation,
  rollback atomicity, decorate-once, clear-drop pair, rebuild, loop
  census, alias identity + divergence shape, read/mutate split,
  primary flags (workspace 42/42 + the authorized 18-passed focused
  run). `static-reviewed` for the zero-`async` census, the zero
  model-scan census, the zero `definition.primary` read census, the
  docstring-vs-body prose, and oracle-body independence (plain classes
  + `object()` sentinels; none reads the owner). Observable behavior
  pinned: second type gets its own record; same-object re-register is
  silent; different-object rebind raises and preserves; failed pair
  leaves the map clean; double finalize decorates once; clear empties
  store + pending together; post-clear rebuild finalizes. Rejects every
  duplication direction in C1–C6.
- **Structural gate.** Deferred with reason: a behavior-preserving hand
  copy of the owner pair passes every standing oracle by construction
  (the copy is correct — identical wording, identical identity
  semantics), so no behavioral gate can pin unity; only a source census
  could, and that is a bespoke existence test per helper, which
  [DRY.md][dry] forbids for gate-only findings. Unity rests on the
  one-way import edge (base → registry, never the reverse at module
  top) plus the recorded triggers below. Coverage that stays: the
  rebind row (fails a lost collision arm), the rollback 4-pack (fails a
  lost restore), the unregister row (fails a retained definition), the
  idempotent pair (fails a lost skip), the name-decode 5-pack (fails a
  lost scan), the rebuild pair
  (fails a lost reset). D1 names the one arm no standing row fails.
- **Coupling.** None. Adjacent verified items untouched: the F4 cache,
  the file-registry item, and every oracle file keep their blobs
  (fingerprints below); no edit here can stale them.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `registry.py` `9cc8bb55…`, `types/base.py` `91c58747…`,
  `types/finalizer.py` `77fd9a2d…`, `types/definition.py`
  `fa6c4d330…`, `types/relations.py` `6bd7c63d…`,
  `types/relay.py` `52439862…`, `relay.py` `c3c5aea5…`,
  `list_field.py` `ce682d5f…`, `testing/relay.py` `df0dc72a…`,
  `management/commands/inspect_django_type.py` `46dffb3d…`,
  `tests/test_registry.py` `e330cfb8…`,
  `tests/types/test_base.py` `4282e0b0…`,
  `docs/dry/dry-file-registry.md` `4350662b…`,
  `docs/dry/dry-rule-type-registry-enum-cache.md` `8afa1681…`.
  Concurrent-dirt reads (never edited; cited lines verified absent from
  their `git diff HEAD` hunks): `utils/querysets.py` working
  `96618fba…`, `mutations/sets.py` working `936f5ae7…`. Searched
  population: whole package (117 `.py`, both trees); installed
  Strawberry + specs + glossary read as contract anchors, not
  fingerprinted inputs. Any fingerprint change reopens the finding.
- **Reconsideration triggers (recorded at the owners).** The store stays
  single-owned until one fires: T-pair fires if a second production
  caller of `register_with_definition` (or a second
  `DjangoTypeDefinition(` site) appears; T-scan fires if a second
  `iter_definitions()` loop lands outside finalizer/inspect/decode;
  T-alias fires if a reader needs the alias to disagree with the
  canonical store (today both strict gates require identity). Durable
  homes: the pair docstring, the alias-identity clauses at
  [list-field][list-field] + [testing-relay][testing-relay], this
  finding. The plan's `## Responsibility index` row for
  `type-registry-definition-store` already covers all three member
  files; no new row owed.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A map vs store (F1 owns the map). Difference: per-model multiplicity
  + primary predicate + hot-path reverse lookup vs per-type record
  holding declaration content; one `Meta` feeds both writes in one
  flow; no site scans definitions by model (C5 census). Deriving the map
  from a scan would put request-time lookups behind a linear walk.
  Trigger: a model-keyed read that cannot use the map. Home: the F1
  family item + this finding. Related route (not claimed):
  [querysets][querysets]`::model_for` reads the alias while
  `model_for_type` reads the index — that read-rule choice is F1's
  holding item to judge.
- R-B alias vs store. Difference: same object, two lookup semantics —
  the registry dict is exact-key (canonical: both strict guards require
  `definition is registered`); the class attribute inherits through the
  MRO, which is exactly what lets the constructor guard *detect* a
  parent-inherited definition and reject it at the declaring line.
  Collapsing to one holder loses that distinction. Trigger: a reader
  needing alias/canonical disagreement (T-alias). Home: the guard
  docstrings ([list-field][list-field], [testing-relay][testing-relay])
  and this finding.
- R-C primary mirror vs primaries (F1 owns the predicate). Difference:
  write-once introspection field, zero package reads (census), vs the
  runtime predicate every resolution path calls; [spec-018][spec-018]
  names `_primaries` the single source of truth. Trigger: a production
  read of `definition.primary` for a routing decision. Home: the
  [definition][definition] invariants docstring + [spec-018][spec-018].
- R-D pending ledger vs store (F3 owns the ledger). Difference: ordered
  pre-finalize relation intents drained by identity vs collected
  declaration records kept for the build lifetime; `unregister` removes
  a subset by `source_type`, `discard_pending` removes resolved records
  by record identity — different removal keys for different reasons.
  Trigger: a relation intent needing declaration-lifetime reads. Home:
  the F3 family item.
- R-E per-type `finalized` vs global `_finalized` (F5 owns the gate).
  Difference: per-entry rerun skip (partial-recovery contract) vs whole-
  build entry guard; different granularities, one Phase-3 line flips
  each. Trigger: a third finalized-state needing its own flag. Home: the
  F5 family item.
- R-F name scan vs store (Family `relay-node-name-decode` owns the
  decode rule). Difference: GraphQL-name→definition scan over Relay-Node
  definitions only (miss/ambiguity arms are decode semantics) vs the
  storage it scans; no name→definition map exists, so the scan is the
  single implementation, not a second one. Trigger: a second name-keyed
  lookup path. Home: that family item.
- R2 re-checked (prior trigger, not inherited): rollback restores the
  pre-call `_primaries` snapshot and touches only THIS call's appended
  state; `unregister` purges unconditionally. The common
  `_types`/`_models` removal IS shared (`_detach_type_from_model`,
  build-018). Recount: still 1 pair def + 1 production caller; the
  `dry-0_0_11.md` third-site trigger stays unfired. Home:
  `registry.py::TypeRegistry.register_with_definition` (mirror-obligation
  docstring).
- R3 re-checked (prior trigger, not inherited): declaration ledgers are
  pre-bind, per-flavor, disjoint by design; folding them into the
  model-keyed store would couple bind policy to lookup policy and erase
  the `before_bind=False` survival contract. Trigger (ledger needing
  model-keyed lookup/primary/pending semantics) unfired. Home:
  [mutation-sets][mutation-sets]`::make_declaration_registry`.

## Defects

- D1 (proof-strength gap, UNFIXED): no standing oracle asserts
  `clear()` empties `_definitions` or `_pending`. `test_clear_drops_all_state`
  pins the map + reverse-index + enum arms only; `test_unregister_…`
  pins the definition drop for `unregister`, not `clear()`;
  `test_registry_clear_drops_types_and_enums` pins the map arm only.
  The C4 contract (atomic pending-definition loss + vacuous re-finalize
  + rebuild) is execution-verified in the workspace (E-C4) and the
  adjacent arms are suite-pinned, so the rejection stands; but a future
  regression dropping one of the two `clear()` reset lines would stay
  green until a ghost pending record breaks an unrelated finalize. Owner:
  `tests/test_registry.py` (extend `test_clear_drops_all_state` with the
  definition + pending arms, or a sibling row). Routes to Worker 0 for
  card homing at closeout; not fixed inside this item (any edit to that
  file would stale the verified F4 + file-registry fingerprints).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace; the one authorized shared-tree focused test ran green
post-trace (18 passed) with zero edits in flight, so no run is
invalidated. No `execution-deferred` items. `FAKESHOP_SHARDED=1` and
Postgres cells `inapplicable by construction`: every executed claim is
in-memory dict work plus pure class construction/decoration; the probes
open no DB (recorded `NAME` is the copy's own file, never touched).
Full-suite gate business is deferred to the final-gate item with reason:
the entry command authorizes workspace runs plus one focused `--no-cov`
test, and a green unmutated suite would discharge no failability proof
for a rejection that proposes no gate.

## Judgment

Single-owned store, single producer, single writer pair, all consumers
composing by name. The six resemblance candidates (map, alias, primary
mirror, pending ledger, finalized flags, name scan) are intentional
separations with recorded differences, triggers, and existing homes; the
two historical mirrors are either shared (`_detach_type_from_model`) or
trigger-checked (R2/R3, both unfired). Consolidation rejected; zero
edits; no new tests owed beyond the D1 homing note.

## Independent verification (Worker 2)

Own trace, recorded before reconciling with `## Findings` (artifact read
last, no `worker-memory/` read). Instruments: `Read` of all three member
files in full, `Grep` sweeps over `django_strawberry_framework/`, one
read-only `ast` count run against the shared tree (no DB, no mutation),
`git diff` vs both baselines.

**Store mechanism (own sweep).** `_definitions` touches, package-wide:
`registry.py` init line (1 dict), `register_definition` get/store pair
(1 store line), `get_definition` read (1), `iter_definitions` yield (1),
`unregister` pop (1 line), `clear()` reset (1 line); docstring mentions
only (detach docstring, `unregister` docstring, decode docstring). Zero
touches inside `register()` body, zero inside the pair-rollback block
(which reverts `_detach_type_from_model` + `_primaries` only). So: 1
store / 1 unregister-pop / 1 clear-reset — agrees with W1.
`DjangoTypeDefinition(` construction sites: exactly 1
(`types/base.py` inside `__init_subclass__`). `register_definition` /
`register_with_definition` / `get_definition` / `iter_definitions`: 1
`def` each; sole production caller of the pair is `__init_subclass__`
(single call line); sole alias write
`cls.__django_strawberry_definition__ = definition` in the same flow, same
object. `AsyncFunctionDef` census re-derived read-only via `ast`:
registry 30/0, base 32/0, finalizer 42/0, definition 8/0, relations 3/0 —
matches W1 exactly. `definition_for_graphql_name`: 1 def; sole
production reader is the Relay decode path (`types/relay.py`); rule-wise
a consumer owned by `relay-node-name-decode`, storage-wise an F2 scan —
agrees. Real `iter_definitions()` loops: registry self-scan, finalizer
(6 loop sites across phase/connection/audit/bind bodies), inspect
bare-name resolver; `mutations/sets.py` mention is a docstring contrast,
`optimizer/*fragment_definitions` hits are GraphQL-document vocabulary,
not the store — agrees (3 files). Consumers confirmed by name:
list-field guard (`list_field.py` canonical-identity check + alias read),
`testing/relay.py` alias-vs-canonical pin, finalizer Phase-1 pending
resolution + audits, `_synthesize_relation_connections` target-definition
read, optimizer walker/extension, relation resolvers, Relay decode,
connection/keyset paths, `definition.py::related_target_for` (own record
+ `registry.get`, no second store). **Owner I would choose:**
`registry.py::TypeRegistry` (F2 aspects) — base already imports the
registry at module top while the registry reaches the definition only
under `TYPE_CHECKING` / in-function; reversing the edge cycles. Agrees
with W1.

**Population completeness.** `git ls-files` recount: 117 `.py` — matches.
Every `_definitions` / pair / accessor / construction / alias token above
lands in the family row or a recorded rejection (R-A…R-F, R2, R3); no
file-local row owed; no second store in any flavor (mutation/form
ledgers are pre-bind declaration lists; filter/order sidecars bind onto
the set, never into the store). No consolidation found beyond W1's —
zero-edit accepted only after this independent sweep.

**F1/F2/F3/F5 boundary — judged RIGHT, four aspects not one store.**
Applied C5 myself: zero production sites scan definitions by model (no
`definition.model ==` / `is` comparison anywhere; the one `definition.model
is not None` read is the set-owner compat check, not a lookup). The map
(F1) serves model→type hot paths (`get`, `primary_for`, `types_for`);
deriving it from a scan would linear-walk request-time resolution —
deleting the index is not a consolidation. Pending (F3) removes by record
identity, store removes by type key — different removal keys, different
lifetimes (drained at finalize vs kept for the build). Finalized flags
(F5) are per-entry rerun-skip + whole-build entry guard — granularity,
not storage. Alias vs store (R-B): same object, but exact-key canonical
reads vs MRO-inherited lookup is exactly what lets the constructor guard
detect a parent-inherited definition — collapsing loses the distinction.
`definition.primary` package reads: zero (one prose mention in
`definition.py` docstring only) — mirror vs predicate split stands.
Four aspects, three-plus contracts, one class: the split is the correct
decomposition.

**D1 adjudicated — gap REAL, card class: test-strengthening (oracle
gap), blocks nothing.** Opened `tests/test_registry.py::test_clear_drops_all_state`:
registers a plain `CategoryType` (no `DjangoType`, hence no definition)
+ enum, asserts `get` / `model_for_type` / `get_enum` only. No
`get_definition`, no `iter_definitions`, no `_pending` assertion —
confirmed it does NOT pin the definition/pending arms. Behavior risk
judged nil: `clear()` body drops both arms on adjacent unconditional
lines (no branch, no guard to mis-fire), W1's E-C4 executed the
drop-pair + vacuous re-finalize + rebuild, and the adjacent arms are
suite-pinned (map/enum here; definition-drop for `unregister` at
`test_unregister_removes_from_types_models_primaries_definitions`;
pending-drop for `unregister` at
`test_unregister_removes_pending_relations_sourced_from_type`). A future
regression deleting one `clear()` reset line would stay green until a
ghost record breaks an unrelated finalize — exactly W1's wording, and
exactly oracle-strength, not behavior. C4 execution-verified discharges
the behavior; what remains is the standing oracle. Home: extend
`test_clear_drops_all_state` (or a sibling row) in `tests/test_registry.py`
— same homing W1 named. No new `## Defects` entry from Worker 2 (D1
already owned; nothing else found).

**Per-claim agreement/difference.** Agree on every count (definitions,
store/pop/reset lines, construction site, alias site, pair caller, 3
loop files, 0 model-scans, 0 primary reads), every separation (R-A…R-F
with homes, R2/R3 unfired — `_detach_type_from_model` shared at exactly
2 sites, ledger trigger unfired), owner + lifetime, C1→1 / C2→1 / C3→1 /
C4→1 / C5→0 / C6→1-canonical, and the D1 statement. Differences: none
material. One wording note (non-blocking): the F1 bullet "the scan" in
"Sites + roles *Definitions*" could misread as F2 owning decode
semantics, but the boundary paragraph + R-F already assign the rule to
`relay-node-name-decode` — no revision owed.

**No-gate reasoning — judged sound, same standard as prior verified
items.** A behavior-preserving hand copy of the pair passes every
standing oracle by construction (identical wording, identical identity
semantics); only a source census could pin unity, and per
[DRY.md][dry] that is a bespoke existence test per helper, forbidden for
gate-only findings. Same bar as the verified enum-cache (no gate),
relation-kind-taxonomy (no gate, open-ended bypass population), and
subscription-per-event-error-masking (no gate, hand-copy passes oracles)
items. Triggers T-pair / T-scan / T-alias are recorded with durable
homes (pair docstring, guard docstrings, this finding) — the correct
residual.

**Freshness re-hashed** (`git hash-object`, working tree):
`registry.py` `9cc8bb55…`, `types/base.py` `91c58747…`,
`types/finalizer.py` `77fd9a2d…`, `types/definition.py` `fa6c4d330…`,
`tests/test_registry.py` `e330cfb8…` — all match W1's prefixes; 117-file
population re-counted; HEAD `bfaee91d`. Item-scoped diff re-confirmed
empty on all three member paths vs `ITEM_BASELINE` `534f67ea…` AND vs
`HEAD` (both `git diff` exits 0, `git status --short` names none of
them). Dirty paths in the tree (auth/mutations, connection,
error/resource policy, filters/forms/mutations/optimizer sets, plan doc,
etc.) are concurrent work on other items' ledger rows — none on a family
path, none read for content except the two W1-cited lines which sit
outside every concurrent hunk (re-verified by absence from this item's
empty diff). `875f64da` resolves to a `WIP` stash object (current dirt
carrier), not a branch — no branch switch occurred.

**`## Pending execution` empty — judged adequate.** Gate-run oracles for
the clear/rebuild lifecycle are named: `test_clear_drops_all_state`
(map/enum arms), the clear-then-rebuild pair, the unregister-drop row,
the idempotent pair, the name-decode 5-pack — all inside the authorized
18-passed focused run, green post-trace with zero edits in flight, so no
run is invalidated. `FAKESHOP_SHARDED=1`/Postgres `inapplicable by
construction`: every executed claim is import-time dict work + pure
class construction; probes open no DB. Full-suite gate correctly
deferred to the final-gate item: a green unmutated suite discharges no
failability proof for a rejection proposing no gate.

**AGENTS.md prose on empty diff — clean.** No process provenance in the
artifact beyond the required scratch-path record; citations use
`path::Symbol` form; zero tracked edits so no test-tier obligation
arises (D1 homing note only). `uv run ruff format --check` +
`uv run ruff check` on all three member paths: green (re-run by Worker
2). No `CHANGELOG.md` touch. No commit.

**Verdict: `Status: verified`.** Single-owned store, single producer,
single writer pair, all consumers composing by name; six resemblance
candidates intentionally separate with triggers + homes; D1 real but
oracle-strength, homed, blocking nothing.

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`534f67ea6cbc38b05a0bda008653c294e8dce310`) is empty for
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/base.py`, and
`django_strawberry_framework/types/finalizer.py` (and vs `HEAD`
`bfaee91d` likewise); the only new path is this artifact (untracked,
owned by this item). The plan's `## Owned changes` ledger holds no row
on any family path (only `optimizer/walker.py`, two fakeshop live files,
`tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`) — confirmed by full read; nothing to
attribute, no stop triggered. The two dirty paths this trace read
(`utils/querysets.py`, `mutations/sets.py`) were never edited, and their
cited lines sit outside every concurrent hunk. No commit per standing
rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff format
--check` on all three member paths — all green, all already formatted
(proves the no-edit claim mechanically; `.md` artifacts are excluded
from format). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/definition-store-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_definition_store.py` holding the 42 executed checks). No manifest
(no `prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `type-registry-definition-store` (this
artifact); no `## Responsibility index` change (provisional owner +
all three member files already covered, status stays `open` until
Worker 2); no `## Owned changes` append (zero tracked edits); home D1
on a NAMED owning card at closeout.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->
[spec-009]: ../SPECS/spec-009-rich_schema_architecture-0_0_4.md
[spec-018]: ../SPECS/spec-018-meta_primary-0_0_6.md
[spec-016]: ../SPECS/spec-016-fieldmeta_consolidation-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[definition]: ../../django_strawberry_framework/types/definition.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[mutation-sets]: ../../django_strawberry_framework/mutations/sets.py
[querysets]: ../../django_strawberry_framework/utils/querysets.py
[registry]: ../../django_strawberry_framework/registry.py
[relations]: ../../django_strawberry_framework/types/relations.py
[relay-types]: ../../django_strawberry_framework/types/relay.py
[root-relay]: ../../django_strawberry_framework/relay.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py

<!-- tests/ -->
[test-registry]: ../../tests/test_registry.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[tree]: ../TREE.md
## Bounded re-review (Worker 2, Q13)

Phase 1 trace. Question: whether the definition-store findings still hold after
`django_strawberry_framework/types/definition.py` gained worktree dirt. No prior
diagnosis read; this trace is derived from current source only, distinguishing HEAD
behavior from worktree behavior. Zero source edits. Applicable contracts: DRY.md
principle 4 (lifetimes) and principle 7 (owner by responsibility). No status set;
no verdict on prior findings proposed here.

Targets inspected (worktree bytes read; HEAD bytes via `git show HEAD:<path>`):

- `django_strawberry_framework/registry.py::TypeRegistry` (definition aspects)
- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (producer)
- `django_strawberry_framework/types/definition.py` dirt hunks (attribution only)

### 1. Record shape + construction site(s)

`django_strawberry_framework/types/definition.py::DjangoTypeDefinition` is a
dataclass with 29 slots (HEAD and worktree identical; verified field-block diff
empty):

- `origin`, `model`, `name`, `description`, `fields_spec`, `exclude_spec`,
  `selected_fields`, `field_map`, `optimizer_hints`, `has_custom_get_queryset`
- `consumer_authored_fields`, `consumer_annotated_relation_fields`,
  `consumer_annotated_scalar_fields`, `consumer_assigned_relation_fields`,
  `consumer_assigned_scalar_fields`
- `primary`, `interfaces`, `filterset_class`, `orderset_class`, `fields_class`,
  `connection`, `cursor_field`, `relation_shapes`, `relation_connections`,
  `globalid_strategy`, `effective_globalid_strategy`, `finalized`
- `_related_target_cache`, `_custom_id_resolver_cache` (private memoization,
  `compare=False`, `repr=False`)

Derived members on the record (not stored slots): `graphql_type_name`
(property, pure derivation), `related_target_for` (lookup with post-finalize
memoization into `_related_target_cache`), `has_custom_id_resolver_for`
(memoization into `_custom_id_resolver_cache`). Module helpers
`origin_has_custom_id_resolver`, `_normalize_pk_name`, `_resolves_id_off_pk`,
`_class_has_custom_id_resolver`, `_is_framework_relay_id_resolver` support the
id-resolver detection; only `_normalize_pk_name` and `_resolves_id_off_pk` are
dirtied (see below).

Construction: exactly one production construction site, HEAD and worktree
identical (kwargs byte-identical):

- `django_strawberry_framework/types/base.py::DjangoType.__init_subclass__`
  builds `DjangoTypeDefinition(...)` with 23 explicit kwargs (everything except
  `effective_globalid_strategy`, `finalized`, and the two caches, which keep
  defaults), then calls
  `django_strawberry_framework/registry.py::TypeRegistry.register_with_definition`
  with `(meta.model, cls, definition, primary=validated.primary)`, then stores
  the same object as `cls.__django_strawberry_definition__`.
- Package-wide search for `DjangoTypeDefinition(` finds one production match
  (the site above). HEAD `git show` grep finds the same single site.
- Direct `DjangoTypeDefinition(...)` constructions in
  `tests/types/test_definition_relations.py` (hostile-metadata helper,
  memoization/equality rows) are independent oracles exercising the record, not
  production definitions; classified as oracles, not counted.

### 2. Store operations with dirt overlap verdict per operation

Store is `django_strawberry_framework/registry.py::TypeRegistry._definitions`
(`dict[type, DjangoTypeDefinition]`). Dirtied bodies in scope are all in
`django_strawberry_framework/types/definition.py`: (A) `graphql_type_name`
normalization (guarded `isinstance` + `str.__str__` + safe rendering), (B)
`related_target_for` field-name gate (guarded `isinstance` + `str.__str__`),
(C) `_normalize_pk_name` (guarded `isinstance` + `str.__str__`), (D)
`_resolves_id_off_pk` id-attr gate (guarded `isinstance` + `str.__str__`).
HEAD vs worktree behavioral delta is confined to hostile inputs (objects whose
`__class__` raises under `isinstance`, or whose `__str__`/`__repr__` raises);
normal string inputs behave identically.

- `TypeRegistry.register_definition` (write one): verdict NO dirt. Body is
  `_check_mutable` + `_definitions.get` identity check + dict store. Executes
  none of A/B/C/D.
- `TypeRegistry.register_with_definition` (atomic write pair): verdict NO dirt.
  Body snapshots `_primaries`, calls `register`, calls `register_definition`,
  rolls back via `_detach_type_from_model` + primary restore. Executes none of
  A/B/C/D.
- `TypeRegistry.get_definition` (lookup by class): verdict NO dirt. Body is a
  single `_definitions.get`. Executes none of A/B/C/D.
- `TypeRegistry.definition_for_graphql_name` (lookup by GraphQL name): verdict
  YES dirt (the only overlapping store operation). Body scans
  `iter_definitions()` and reads `definition.graphql_type_name` per Relay-Node
  candidate, so dirtied body A runs once per scanned definition. Dirtied bodies
  B/C/D do not run here.
- `TypeRegistry.iter_definitions` (iterate): verdict NO dirt. Body is
  `yield from self._definitions.items()`. A caller may execute A (as above),
  but the operation itself executes none of A/B/C/D.
- `TypeRegistry.unregister` (remove one): verdict NO dirt. Body pops
  `_definitions`, detaches model linkage, purges primary slot, filters
  `_pending`, best-effort connection-cache eviction. Executes none of A/B/C/D.
- `TypeRegistry.clear` (remove all): verdict NO dirt. Body runs type
  teardowns, clears `_types`, `_primaries`, `_models`, `_enums`,
  `_definitions`, `_pending`, `_type_teardowns`, resets finalized/snapshot,
  replays subsystem clears. Executes none of A/B/C/D.

`registry.py` worktree-vs-HEAD diff is a docstring-only addition on
`definition_for_graphql_name` (no behavior change); `types/base.py`
worktree-vs-HEAD diff (suppressed-Relay-pk extraction, optimizer-hints guards)
does not touch the construction kwargs or the register pair, so HEAD-bytes
judgment for registry/base definition aspects equals worktree judgment.

### 3. Definition counts

- New record field challenge: posit adding one slot to
  `DjangoTypeDefinition` (e.g. a new sidecar, flag, or synthesis slot).
  Authoritative definitions forced: 1 (the dataclass field declaration in
  `django_strawberry_framework/types/definition.py`). The construction kwargs
  in `__init_subclass__`, registry store operations, and test/oracle
  constructions move as consumers/oracles of that one shape (composed by
  name), not as second definitions; listed separately, not counted.
- Second record site challenge: posit a second production factory/call-site
  building `DjangoTypeDefinition` (e.g. finalizer-synthesized or test-helper-
  promoted definitions). Authoritative construction sites today: 1 (the
  `__init_subclass__` site above). Count 1 = independence; no second
  maintained shape exists in HEAD or worktree.

### 4. Owners I would choose (principle 7; lifetimes principle 4)

- Record shape: `django_strawberry_framework/types/definition.py::DjangoTypeDefinition`.
  Narrowest cohesive owner every legitimate consumer (registry, optimizer,
  finalizer, relay injection, resolvers) can depend on without reversing a
  dependency or importing sibling-flavor machinery. Registry imports it only
  under `TYPE_CHECKING`; `types/base.py` imports it for construction; all
  readers import from definition. Dependency direction wins over host-module
  size.
- Definition store (`_definitions` + the seven operations above):
  `django_strawberry_framework/registry.py::TypeRegistry`. Existing owner with
  that responsibility (process-global singleton, import-time mutation,
  test-only teardown). Lifetime: owner `TypeRegistry`; validity key the
  registry lifecycle (`_finalized` + per-build snapshot); publish point
  `register_with_definition` from `__init_subclass__` at import time; who may
  mutate `__init_subclass__` via the atomic pair plus `unregister`/`clear`
  (test-only) plus finalizer flips (`finalized`,
  `effective_globalid_strategy`, `relation_connections`); when invalidated
  `clear()` drops all, `unregister` drops one, `_check_mutable` refuses
  post-finalize mutation.
- Cached derivations: `_related_target_cache` and `_custom_id_resolver_cache`
  owned by the `DjangoTypeDefinition` instance (per-instance memoization;
  validity bounded to the definition lifetime plus the
  `registry.is_finalized()` gate for `related_target_for`; who may mutate the
  instance itself lazily; when invalidated discarded with the definition on
  `clear()`). `graphql_type_name` is a pure derivation, explicitly not cached.
- Name-scan inverse: `TypeRegistry.definition_for_graphql_name` stays the
  single inverse of the type-strategy encode (Relay-Node-only scan keyed on
  `graphql_type_name`); the dirt hardens the derivation it inverts without
  moving ownership.

### 5. Whether the dirt breaks anything derived

No. Normal-path observable behavior is identical HEAD vs worktree for every
supported input: real `str` names/field names/pk names take the same branches
and return the same values; `definition_for_graphql_name` matches the same
definitions. The dirt only changes hostile-input paths (liar `__class__`,
raising `__str__`/`__repr__`) from leaking a raw exception to a typed
fail-closed outcome (`ConfigurationError` for `graphql_type_name`; `None` /
`False` / `True`-fail-closed for the lookup/detection gates). That is
hardening inside already-owned bodies, not a second definition, and it breaks
no DRY.md principle 4/7 contract row. No GOAL.md trust-boundary defect is
raised: no contract row broken, and no feasible project shape under supported
public API with a wire/configuration input reaching a changed supported
outcome is named. Oracles read (not rewritten): normal-path lookup rows in
`tests/test_registry.py` (match, `Meta.name`, Relay-only, miss, ambiguity) and
hostile/liar rows in `tests/types/test_definition_relations.py` (unreadable
origin, hostile name, liar names/field names/pk names, liar NodeID) pin the
worktree behavior.

### 6. Freshness fingerprints (HEAD + worktree separately)

- HEAD commit: `bfaee91dcd332a5f86250fff90ab21b377bc674e`
- HEAD blobs (`git rev-parse HEAD:<path>`):
  `django_strawberry_framework/registry.py` `9cc8bb553fd417fc465809a541769a8383469cda`;
  `django_strawberry_framework/types/base.py` `91c587477ff8257e80dbb9a9c79859f34c5b4c7e`;
  `django_strawberry_framework/types/definition.py` `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`
- Worktree blobs (`git hash-object <path>`):
  `django_strawberry_framework/registry.py` `612bea87fdcf5e5a254caf70c9947b9535f638c3`;
  `django_strawberry_framework/types/base.py` `bc8dcdb6d25b9bff815ac596e6fd21fa76eb39b1`;
  `django_strawberry_framework/types/definition.py` `01f78d93baf8fb6ca3ab11df1a2a495640fb7655`
- Searched population: full package grep for `DjangoTypeDefinition(` under
  `django_strawberry_framework/` (1 production match); `git show HEAD` grep
  for the same (1 match); `git diff HEAD` for all three paths (definition.py
  four guarded-input hunks; registry.py docstring-only; base.py
  suppressed-pk/optimizer-hints hunks, construction kwargs unchanged).
- Oracles read: `tests/types/test_definition_relations.py` (full),
  `tests/test_registry.py` (definition-for-name + register-definition +
  register-with-definition rows). No test run performed (re-review only).

PHASE-1-TRACE-RECORDED docs/dry/dry-rule-type-registry-definition-store.md
