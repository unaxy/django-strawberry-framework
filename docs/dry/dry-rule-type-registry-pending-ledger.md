# DRY review: `type-registry-pending-ledger`

Status: verified
Run: 0.0.15 2026-09-19-1

Family `type-registry-pending-ledger`. Provisional owner
`django_strawberry_framework/registry.py::TypeRegistry` (F3 aspects).
Member files: `django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/relations.py`,
`django_strawberry_framework/types/base.py`,
`django_strawberry_framework/types/finalizer.py` (all four worktree-clean
vs `HEAD` `bfaee91d` and vs `ITEM_BASELINE`
`960a0c6b8c7bebe2244c79222d15da27ceb18138`: both diffs byte-empty,
confirmed). Prior records used only as triggers, never verdicts: the
registry file item's F3 aspects (`docs/dry/dry-file-registry.md`,
verified) + the two verified siblings (`type-registry-enum-cache`,
`type-registry-definition-store` — their F1/F2/F3/F5 boundary
statements checked, not inherited; the definition-store item recorded
the pending-vs-store split — pending removes by record identity vs
store by type key — re-proved below as B6). Never read any
`worker-memory/`.

## System trace

Rule: the registry's memory of what CANNOT resolve yet. Every
auto-synthesized relation becomes a `PendingRelation` record at class
creation (target looked up later, never bound early), and
`finalize_django_types()` Phase 1 either rewrites every record's
sentinel annotation through the registered target or raises before
mutating a single class. Forward references — including mutual pairs —
resolve regardless of declaration order; a target with no registered
type fails loud; nothing ever degrades into a placeholder.

Boundary against the sibling families on the one class (re-derived,
agrees with both siblings): F1 owns `_types` / `_primaries` /
`_models` plus `register` / `unregister` map arms / `get` and friends;
F2 owns `_definitions` plus the atomic pair and both accessors; F3 owns
`_pending` plus identity-matched add/iter/discard; F4 owns `_enums`
plus the pair; F5 owns `_finalized` plus the guard and the flip. The
`_pending` rebind inside `unregister` (subset drop by `source_type`)
and the `_pending.clear()` line inside `clear()` are those lifecycles
consuming F3 state, not second definitions — the same treatment both
siblings give the store arms. Record shape (`PendingRelation`,
`PendingRelationAnnotation`) is owned by [relations][relations]; the
ledger owns the list and its removal keys.

Sites + roles. *Definitions* (one each, probe-pinned): `add_pending_relation`,
`iter_pending_relations`, `discard_pending`
([registry][registry]`::TypeRegistry`); the `_pending` list (1
construction, 2 rebinds, 1 clear, 1 read); the single
`PendingRelation(` construction site and the single
`registry.add_pending_relation(` call line (both in
[base][base], one flow); the single `registry.discard_pending(` drain
line ([finalizer][finalizer] Phase 1). *Producer*:
`DjangoType.__init_subclass__` via `_build_annotations` (sole; every
auto-synthesized relation defers unconditionally). *Consumer*:
finalizer Phase 1 (drains into a list before mutating, per the
stale-view docstring; resolves via `registry.get`, rewrites via
`resolved_relation_annotation`). *Oracles*: [test-registry][test-registry]
(identity-match, non-hashable-field, phase-atomicity pair, pending
drain/retain, consumer-authored discard, unregister subset-drop),
[test-definition-order][test-definition-order] (forward-ref graph,
unresolved-target wording, ambiguity-before-unresolved ordering),
[test-finalizer][test-finalizer] (hostile-name diagnostic, malformed
field-name, missing-definition typing), [test-relations][test-relations]
(hash/equality/frozen shape rows), [test-gfk][test-gfk]
(declaration-time GFK rejection). All spell literals independently;
none enumerates the owner. *Projections*: the ledger docstrings
(verified against bodies), [spec-010][spec-010] (scaffolding shape),
[spec-018][spec-018] (import-order trap closure, ambiguity audit),
[GOAL.md][goal] migration note (unregistered target raises) + non-goal
(never silently weaken relations into placeholders).

Connected sources read for judgment, outside the members:
[converters][converters]`::resolved_relation_annotation` (rewrite body:
pure shape switch, no registry read — the lookup stays the finalizer's
via `registry.get`); [definition][definition] (record + `field_map`
live-read leg); [sets-mixins][sets-mixins] (`LazyRelatedClassMixin`,
`RelatedSetTargetMixin`, `collect_related_declarations` — the open
families' string-laziness seam, stated not decided); installed `.venv`
Strawberry (no pending vocabulary — not re-read here; no anchor
claimed). Excluded on strength of body: every other package module
(zero `add_pending_relation` / `discard_pending` /
`iter_pending_relations` / `_pending` / `PendingRelation` vocabulary
over the 117-file sweep; `forms/converter.py`-style docstring-only
mentions absent here — the sweep is clean).

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The mutation/form declaration
   ledgers (`make_declaration_registry`) are pre-bind, per-flavor,
   disjoint declaration lists — a different subject (declared
   operations) from collected relation intents. Filter/Order
   `RelatedFilter` / `RelatedOrder` string targets resolve through the
   open `lazy-related-class-resolution` / `related-set-target-lifecycle`
   / `related-declaration-collection` families: their seam is the lazy
   class read (`resolve_lazy_class` + `_resolved_target` + owner bind),
   drained at finalizer Phase 2.5 subpass 2, while this ledger drains at
   Phase 1. Different mechanism, different phase, different removal key.
   Seams stated; nothing decided for those items. Trigger: a set-side
   lazy target written into `_pending`.
2. **Sync/async twins.** Zero `AsyncFunctionDef` in all four members
   (AST-verified: registry 30/0, relations 3/0, base 32/0, finalizer
   42/0). Collection/finalize/drain are import-time dict + class-attr
   work; no ORM I/O, no awaits. Trigger: a ledger method touching the
   DB or awaiting.
3. **Derived rather than repeated knowledge.** `PendingRelation`
   snapshots `related_model` / `relation_kind` / `nullable` beside the
   live `FieldMeta` in `definition.field_map` — one flow writes both,
   exactly one site reads each for routing (finalizer Phase 1 reads the
   map; the record fields are introspection-only per the record
   docstring). No production site routes on a record snapshot (R-A).
   Trigger: a routing read off a record field.
4. **Inverse / round-trip pairs.** add/iter/discard; declare →
   resolve → drain; fail → retain → retry; sentinel install →
   sentinel rewrite. All pinned by oracles below. No un-pend primitive
   besides `discard_pending` (resolved set), `unregister` (source
   subset), `clear()` (all, test-only) by design.
5. **Contracts restated in another medium.** Production (ledger pair +
   sole producer + sole drain); oracles (independent literals, no owner
   reads); projections (docstrings verified against bodies; specs pin
   the deferral shape and the trap closure; [GOAL.md][goal] pins loud
   failure + the no-placeholder non-goal). The record docstring's
   "production consumer reads the live `FieldMeta`" clause matches the
   finalizer body.
6. **Enforcement by omission.** `add_pending_relation` and
   `discard_pending` call `_check_mutable` (import-time-only;
   post-finalize late import fails loud); `iter_pending_relations` is a
   pure read (no guard owed — Phase 1 runs pre-flip, retry reads the
   retained list). `clear()` bypasses by the documented test-only
   contract; `unregister`'s subset drop is the pinned F1/F3 boundary,
   not a gap. The no-concrete-model hole cannot reach the ledger:
   `_build_annotations` raises at declaration (GFK oracle). No member
   lacks a guard its contract requires: no defect. The missing
   standing assert for `clear()`'s pending arm is oracle-strength, not
   omission — D1.

### Enumeration

Instrument: `ast.parse` counts + token sweeps over the 117-file
package population (`git ls-files django_strawberry_framework |
grep -c` = 117, re-counted). Every ledger member assigned; every
challenge ends in the family row or a recorded rejection (no file-local
row — each overlap has its owning family or rejection recorded).

- `add_pending_relation` / `iter_pending_relations` /
  `discard_pending`: exactly 1 def each; the only production
  `add_pending_relation(` call line is [base][base] (1 site); the only
  production `discard_pending(` call line is [finalizer][finalizer] (1
  site); the only production `iter_pending_relations()` read line is
  the Phase-1 loop (docstring mentions excluded).
- `_pending`: exactly 1 storage list; 1 construction, 2 rebinds
  (`unregister` subset, `discard_pending` resolved-set), 1 `clear()`
  reset, 1 `yield from` read.
- `PendingRelation(`: exactly 1 construction site (the deferral
  branch); consumer-authored relations `continue` before it (no
  record); `related_model is None` raises before it (no record).
- `PendingRelationAnnotation`: 1 install line (same branch), 1 rewrite
  line (Phase 1 resolved arm), 1 metaclass repr (unfinalized-schema
  error shape).

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted. Workspace probes P1 map one-to-one
onto C1–C5 (29/29 `execution-verified`); negative control N1 proved by
mutation.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Circular FK pair (A→B, B→A, both types registered, either declaration order) | **1** (unconditional deferral: back-ref pends too; one drain resolves both; no ordering definition exists to move). Oracles: `test_pending_set_is_cleaned_after_success…`, the definition-order full-graph row. Probes B2/B3. |
| C2 | Relation to a never-registered type (the string-reference shape at this layer: `related_model` with no `DjangoType`) | **1** (the Phase-1 unresolved check; raises before any class mutation, list preserved for retry). Pinning oracle: `test_unresolved_target_raises_with_source_field_and_target` (message shape) + the phase-atomicity pair (retention + retry). Probes B4. Set-side string laziness is a different mechanism (open families; matrix 1). |
| C3 | `clear()` with pending entries — loss vs loud? | **1** (`clear()`'s `_pending.clear()` line; silent drop is the contract: test-only fresh lifecycle, intents belong to the discarded build). Behavior `execution-verified` (B7); standing-oracle arm missing — D1 (proof-strength, unfixed). |
| C4 | Consumer-authored relation (annotation or assigned field on a relation column) | **0** (short-circuits before the construction site at the producer; the finalizer's `consumer_authored` drain arm is defense-in-depth for a path the documented call graph never takes). Oracle: `test_finalize_discards_consumer_authored…` (in the authorized focused run: passed). |
| C5 | New snapshot attr on the record (same fact twice as the definition?) | **0** second definitions (R-A: record snapshots stay introspection-only; exactly one live reader — the `field_map` — routes. A routing read off a record field fires the trigger). |

**Experiment (executed, disposable workspace).** Copy per [DRY.md][dry]
"Tests" (`rsync`, docs excluded); every command via
`uv run --directory "$WS"` with `$WS` as cwd:

```shell
WS=/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/pending-ledger-w1
uv run --directory "$WS" python -c "import django_strawberry_framework as p; print(p.__file__)"
uv run --directory "$WS" python probe_pending_ledger.py
```

Proof (`CHECKS_PASSED=29/29`): ledger/accessor/construction/drain
singularity counts, forward-ref both orders, mutual-pending drain,
sentinel install, unresolved loud failure (wording + retention +
untouched annotations + retry), identity discard of equal-by-value
twins, discard-keeps-definitions, unregister-by-source vs
discard-by-record split, clear drops pending + definitions, sentinel
repr, GFK-at-declaration raise with no record. Status:
`execution-verified`. Rejects "a second ledger exists", "back-refs
bind early", "unresolved targets degrade", "discard is
equality-based", "clear keeps pending". Copy `__file__`:
`.../dry-ws/pending-ledger-w1/django_strawberry_framework/__init__.py`;
DB `NAME` resolved from inside `$WS`:
`.../dry-ws/pending-ledger-w1/examples/fakeshop/db.sqlite3` (copy's own
tree and database; never the shared tree; the probes open no DB at
all). No source mutation in the proof; searched population inside the
copy: 117 `.py` (matches the shared tree). `grep -c truncated` == 0.

**Negative control N1 (executed, disposable workspace).** Backed up
the copy's `registry.py`, mutated `discard_pending` to
equality-match, re-ran the probe: fails exactly at `B5 identity drops
one twin only` (both twins dropped), exit 1. Restored the backup,
re-ran: 29/29; copy md5 identical to the shared tree. The standing
identity oracle
(`test_discard_pending_uses_identity_match_with_real_pending_relation`)
pins the same contract in the suite — the mutation that breaks the
probe breaks that oracle's shape too. Status: `execution-verified`.

One authorized shared-tree focused run:
`uv run pytest tests/test_registry.py --no-cov -n0 -k "pending or
phase_1 or discard or unresolved or finalize_discards"` → 7 passed
(consumer-authored discard, atomicity pair, drain/retain, identity,
non-hashable, unregister subset-drop).

## Findings

### F1 — pending ledger (REJECTED consolidation: single-owned, overlaps intentionally separate)

- **Contract + variation.** Forward-reference memory: entries that
  cannot resolve yet. Varies on: target registered later (resolve) vs
  never (raise) vs author-owned (skip + drain); drop-one-source vs
  drop-resolved-set vs drop-all. Never varies on match semantics
  (identity, always) or on placeholder degradation (never — the
  [GOAL.md][goal] non-goal).
- **Sites + roles.** *Definitions*: the add/iter/discard triple + the
  list (one each). *Producer*: `_build_annotations` (sole, 1 call
  line, 1 construction site). *Consumer*: finalizer Phase 1 (sole, 1
  iter line + 1 discard line). *Oracles / projections*: as listed in
  System trace.
- **Challenges.** C1 → 1; C2 → 1; C3 → 1; C4 → 0; C5 → 0.
  Count > 1 nowhere in one rule: no duplication.
- **Owner + lifetime (principles 7, 4).**
  `django_strawberry_framework/registry.py::TypeRegistry` (F3 aspects)
  stands: narrowest cohesive owner every consumer can import without
  reversing a dependency (`base.py` already imports the registry at
  module top; the finalizer drains through the public pair; moving the
  list into [relations][relations] would strand the drain on a module
  the finalizer must then import for state, and moving it into
  [base][base] would reverse the registry edge). Stored-derivation
  lifetime: validity key = collection → finalize (drained) or
  `clear()`/`unregister` (dropped); publish point =
  `__init_subclass__` via `add_pending_relation` (single flow writes
  the map entry, the store entry, and the pending record from one
  `Meta`); who may mutate = `add_pending_relation` /
  `discard_pending` (import-time-only via `_check_mutable`) +
  `unregister` (source subset) + `clear()` (all, test-only bypass);
  reads = `iter_pending_relations` (unguarded by design — Phase 1 and
  retry run pre-flip); terminal state = resolved-or-raised at finalize:
  resolved records are discarded, unresolved entries raise
  `ConfigurationError` with the retained list intact for retry; no
  entry survives a successful finalize (drain census: pending empty
  after every passing finalize row).
- **Migration.** None (zero-edit rejection: no behavior hunk, no test
  hunk; every durable home below already exists).
- **Distinct behavior (stays separate).** Unconditional deferral
  (back-refs pend too — the import-order trap stays closed); loud
  failure at finalize vs loud failure at declaration (unregistered
  target vs model-less relation — different layers, different
  oracles); identity removal (resolved set) vs source removal
  (unregister subset) vs full reset (`clear()`); snapshot fields vs
  live `FieldMeta` (R-A).
- **Behavioral proof.** `execution-verified` for singularity counts,
  both declaration orders, mutual drain, sentinel install, unresolved
  wording + retention + untouched classes + retry, identity discard,
  removal-key split, clear-drop pair, sentinel repr, GFK raise with no
  record (workspace 29/29 + N1 + the authorized 7-passed focused run).
  `static-reviewed` for the zero-`async` census, the zero second-site
  census, docstring-vs-body prose, and oracle-body independence (plain
  test classes, `object()` sentinels where identity matters; none reads
  the owner). Observable behavior pinned: forward declaration order
  irrelevant; mutual pairs drain; missing target raises naming
  `Source.field -> Target` and preserves everything for retry;
  equal-by-value twins discard singly; `clear()` empties the ledger.
  Rejects every duplication direction in C1–C5.
- **Structural gate.** No new gate added; the existing identity oracle
  (`test_discard_pending_uses_identity_match_with_real_pending_relation`)
  is the structural pin for the identity contract and its negative
  control is proved (N1: equality mutation fails the contract shape).
  Ledger unity (no second ledger) rests on the one-way import edges
  (base → registry, finalizer → registry by name; sole call lines
  A4/A5) plus triggers R-A/R-B below — a behavior-preserving hand copy
  of the triple passes every standing oracle by construction, so only
  a source census could pin unity, and that is a bespoke existence
  test per helper, which [DRY.md][dry] forbids for gate-only findings
  (same bar as the verified enum-cache, definition-store, taxonomy,
  and accessor items). Coverage that stays: the identity row (fails a
  lost identity arm — proved), the atomicity pair (fail a lost
  retain/retry), the unresolved-wording row (fails a lost loud path),
  the unregister subset row (fails a lost source-key), the drain rows
  (fail a lost discard). D1 names the one arm no standing row fails.
- **Coupling.** None. Adjacent verified items untouched: the F4 cache,
  the F2 store, the file-registry item, and every oracle file keep
  their blobs (fingerprints below); no edit here can stale them.
- **Freshness.** Working-tree blob ids (`git hash-object`):
  `registry.py` `9cc8bb55…`, `types/relations.py` `6bd7c63d…`,
  `types/base.py` `91c58747…`, `types/finalizer.py` `77fd9a2d…`,
  `types/converters.py` `9ceb34af…`, `types/definition.py`
  `fa6c4d330…`,   `sets_mixins.py` working `ad8987ea…` (seam read only; body-cited lines outside
  any concurrent hunk — that file carries concurrent dirt, never
  edited), `tests/test_registry.py` `e330cfb8…`,
  `tests/types/test_relations.py` `89b5c6ff…`,
  `tests/types/test_finalizer.py` `462275e5…`,
  `tests/types/test_definition_order.py` `7dd04d67…`,
  `tests/types/test_generic_foreign_key.py` `5dd0d387…`, [GOAL.md][goal] `7dfbef5c…`. Searched population: whole
  package (117 `.py`, both trees). Any fingerprint change reopens the
  finding.
- **Reconsideration triggers (recorded at the owners).** The ledger
  stays single-owned until one fires: T-producer fires if a second
  production `add_pending_relation(` call line appears; T-drain fires
  if a second `discard_pending(` drain lands outside finalizer Phase
  1; T-record fires if a routing decision reads a record snapshot
  field instead of `field_map` (R-A). Durable homes: the
  `discard_pending` identity docstring, the `PendingRelation` snapshot
  clause, this finding. The plan's `## Responsibility index` row for
  `type-registry-pending-ledger` already covers all four member files;
  no new row owed.

### Rejections (intentional separations, each with difference + trigger + home)

- R-A pending snapshot vs definition live-read (F2 owns the store).
  Difference: record carries `related_model` / `relation_kind` /
  `nullable` for self-contained introspection; the production consumer
  (Phase 1) reads the live `FieldMeta` from
  `definition.field_map[snake_case(field_name)]` instead — one flow
  writes both, exactly one site routes on each. Collapsing the
  snapshot loses introspection without a definition in hand;
  collapsing the map read reintroduces the stale-snapshot risk the
  record docstring names. Trigger: a routing read off a record field
  (T-record). Home: [relations][relations]`::PendingRelation`
  (snapshot clause) + this finding.
- R-B ledger vs store removal keys (verified, agrees with the
  definition-store item's split). Difference: ledger removes by record
  identity (`discard_pending`: resolved set) and by source identity
  (`unregister`: subset); store removes by type key. Different keys
  for different lifetimes (drained at finalize vs kept for the build).
  Re-proved as B6. Trigger: a relation intent needing
  declaration-lifetime reads. Home: the F3 family item (this
  artifact).
- R-C ledger vs set-side lazy targets (open families own the seam).
  Difference: model-relation forward refs (class `related_model`,
  Phase-1 drain, identity removal) vs sidecar string/callable targets
  (Phase-2.5 expansion, owner-bound re-store, `None`-placeholder
  skip). A string reaching `_pending` today is impossible
  (`related_model` is class-or-`None` at the producer; `None` raises
  at declaration). Trigger: a set-side lazy target written into
  `_pending` (matrix-1 standing trigger). Home: those family items.
- R-D sentinel vs nullable (`None`) placeholder. Difference: the
  unfinalized sentinel fails loud at schema build (metaclass repr
  names the gate); the set-side `None` target skips silently by
  contract. Unifying them would silence the [GOAL.md][goal]
  non-goal guard. Trigger: a silently-skipped model relation. Home:
  [relations][relations]`::PendingRelationAnnotation` + the
  [GOAL.md][goal] non-goal.

## Defects

- D1 (proof-strength gap, UNFIXED): no standing oracle asserts
  `clear()` empties `_pending` (nor `_definitions` — the same gap the
  verified definition-store item records as its D1).
  `test_clear_drops_all_state` pins the map + reverse-index + enum
  arms only; `test_unregister_removes_pending_relations_sourced_from_type`
  pins the subset drop for `unregister`, not the full drop for
  `clear()`; the drain/retain rows pin finalize-time behavior, not
  teardown. The C3 contract (silent full drop as test-teardown) is
  execution-verified in the workspace (B7) and the adjacent arms are
  suite-pinned, so the rejection stands; but a future regression
  deleting the `_pending.clear()` line would stay green until a ghost
  pending record breaks an unrelated finalize. Owner:
  `tests/test_registry.py` (extend `test_clear_drops_all_state` with
  the pending arm, or a sibling row — same homing the sibling D1
  names; Worker 0 to dedupe at closeout). Not fixed inside this item
  (any edit to that file would stale the verified F4 + file-registry
  fingerprints).

## Pending execution

None. All behavioral proofs `execution-verified` in the disposable
workspace (29/29 + N1, copy `__file__` + copy DB `NAME` recorded, no
source mutation, `grep -c truncated` == 0); the one authorized
shared-tree focused test ran green post-trace (7 passed) with zero
edits in flight, so no run is invalidated. No `execution-deferred`
items. `FAKESHOP_SHARDED=1` and Postgres cells `inapplicable by
construction`: every executed claim is in-memory dict work plus pure
class construction/decoration; the probes open no DB (recorded `NAME`
is the copy's own file, never touched). Full-suite gate business is
deferred to the final-gate item with reason: the entry command
authorizes workspace runs plus one focused `--no-cov` test, and a
green unmutated suite would discharge no failability proof for a
rejection that proposes no new gate.

## Judgment

Single-owned forward-reference memory: single producer, single drain,
identity-matched removal, resolved-or-raised terminal state. What
lands in pending (every auto-synthesized relation, target or not)
vs what fails loud at declaration (model-less relations) vs what
fails loud at finalize (unregistered targets) is pinned per layer
with its oracle. The same-fact-twice test against the definition
store fails on difference + trigger + home (R-A/R-B); the lazy-set
seams belong to open families (R-C, stated not decided).
Consolidation rejected; zero edits; no new tests owed beyond the D1
homing note.

## Implementation (Worker 1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`960a0c6b8c7bebe2244c79222d15da27ceb18138`) is empty for
`django_strawberry_framework/registry.py`,
`django_strawberry_framework/types/relations.py`,
`django_strawberry_framework/types/base.py`, and
`django_strawberry_framework/types/finalizer.py` (and vs `HEAD`
`bfaee91d` likewise); the only new path is this artifact (untracked,
owned by this item). The plan's `## Owned changes` ledger holds no
row on any family path (only `optimizer/walker.py`, two fakeshop live
files, `tests/base/test_init.py`, `tests/optimizer/test_extension.py`,
`extensions/error_policy.py`) — confirmed by full read; nothing to
attribute, no stop triggered. Dirty paths elsewhere (auth/mutations,
connection, filters/forms/mutations/optimizer sets, resource policy,
`tests/*`, `docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md`)
are concurrent work on other items' rows — read-only here except the
two seam lines in `sets_mixins.py`, which sit outside every concurrent
hunk; never edited. No commit per standing rule.

After the (zero) edits: `uv run ruff check` + `uv run ruff format
--check` on all four member paths — all green, all already formatted
(proves the no-edit claim mechanically; `.md` artifacts are excluded
from format). No `CHANGELOG.md` touch.

Scratch paths (removal is Worker 0's, after `verified`, by explicit
path): `WS` tree
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/pending-ledger-w1`
(includes its own `.venv`, created by the authorized runs, plus
`probe_pending_ledger.py` holding the 29 executed checks + N1). No
manifest (no `prove_failability.py` run — no gate added, none owed).

Worker 0 rows: tick Family `type-registry-pending-ledger` (this
artifact); no `## Responsibility index` change (provisional owner +
all four member files already covered, status stays `open` until
Worker 2); no `## Owned changes` append (zero tracked edits); home D1
on a NAMED owning card at closeout (dedupe with the definition-store
D1 naming the same `test_clear_drops_all_state` extension).

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md
[goal]: ../GOAL.md
[spec-010]: SPECS/spec-010-foundation-0_0_4.md
[spec-018]: SPECS/spec-018-meta_primary-0_0_6.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[base]: ../../django_strawberry_framework/types/base.py
[converters]: ../../django_strawberry_framework/types/converters.py
[definition]: ../../django_strawberry_framework/types/definition.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[registry]: ../../django_strawberry_framework/registry.py
[relations]: ../../django_strawberry_framework/types/relations.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py

<!-- tests/ -->
[test-definition-order]: ../../tests/types/test_definition_order.py
[test-finalizer]: ../../tests/types/test_finalizer.py
[test-gfk]: ../../tests/types/test_generic_foreign_key.py
[test-registry]: ../../tests/test_registry.py
[test-relations]: ../../tests/types/test_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Independent verification (Worker 2)

Own trace, source-derived (every count re-swept from the four members +
converters + sets_mixins + oracles; reconciled with `## Findings`
claim-by-claim below).

**Ledger primitives.** `django_strawberry_framework/registry.py::TypeRegistry`
defines exactly one each of `add_pending_relation` (append + `_check_mutable`),
`iter_pending_relations` (`yield from`, deliberately unguarded), `discard_pending`
(identity rebind + `_check_mutable`). `_pending` touched exactly five ways:
construction (`__init__`, 1), rebind by source identity (`unregister`, 1),
rebind by record identity (`discard_pending`, 1), `clear()` inside `clear()` (1),
read (`yield from`, 1). Agrees with W1 (1/1/1 defs; 1 construct, 2 rebinds,
1 clear, 1 read).

**Producer.** Sole production `PendingRelation(` site is
`django_strawberry_framework/types/base.py::_build_annotations` (1 site); sole
production `registry.add_pending_relation(` call line is
`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__` (1
line, same flow: `register_with_definition` then the pending loop). Deferral is
unconditional: consumer-authored names `continue` before the branch, and
`related_model is None` raises before it — so no record exists for either.
Agrees with W1.

**Consumer / drain.** Sole production `registry.discard_pending(` line is
`django_strawberry_framework/types/finalizer.py::finalize_django_types` Phase 1
(1 line); sole production `iter_pending_relations()` read is the Phase-1 loop.
Retry-preservation confirmed against the body: the ambiguity audit and the
`if unresolved: raise` both run before any annotation mutation, and
`discard_pending` runs only after the rewrite loop — so a Phase-1 failure leaves
both the classes and the list intact for retry. The rewrite itself delegates to
`django_strawberry_framework/types/converters.py::resolved_relation_annotation`
(pure shape switch, no registry read; lookup stays the finalizer's
`registry.get`, live `FieldMeta` via `definition.field_map`). Agrees with W1,
including the R-A split (no production routing read off a record snapshot
field) and the R-B split (discard by record identity vs unregister by
source/type key).

**Second-ledger sweep.** 117-file vocabulary sweep re-run from source: zero
`add_pending_relation` / `discard_pending` / `iter_pending_relations` /
`_pending` / `PendingRelation` outside `registry.py`, `types/base.py`,
`types/finalizer.py`, `types/relations.py` (plus `TYPE_CHECKING` import and
oracle construction in tests). The lazy seams
(`django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin.resolve_lazy_class`,
`::RelatedSetTargetMixin._resolved_target`, `::collect_related_declarations`)
are consumers of a different mechanism — string/callable sidecar targets,
owner-bound re-store, `None`-skip, Phase-2.5 drain — with zero pending
vocabulary; they are seams owned by open families, not second ledgers. Agrees
with W1 (R-C stated, not decided).

**Owner (Worker 2 choice).** `TypeRegistry` (F3 aspects). The list and its three
removal keys (identity, source-subset, full reset) co-locate with the sibling
map lifecycles (F1/F2/F4/F5); the record shape stays with `types/relations.py`.
Moving the list into `relations.py` strands the drain on a state module, moving
it into `base.py` reverses the registry edge (`base.py` already imports the
registry at module top). Agrees with W1.

**Challenges re-judged.** C1 circular → 1 (unconditional deferral, one drain;
no ordering definition exists). C2 never-registered → 1 (Phase-1 unresolved
check; oracle `test_unresolved_target_raises_with_source_field_and_target` +
atomicity pair pin wording + retention + retry). C3 `clear()` with pending → 1
(see lifetime judgment below). C4 consumer-authored → 0 (producer
short-circuit; finalizer arm is defense-in-depth on a path the call graph never
takes). C5 snapshot attr → 0 (R-A; trigger T-record stands). All agree with W1.

**Lifetime judgment (C3, HARD): silent drop is CONTRACT, not gap.** `clear()`
is documented test-only at both the module docstring ("Test isolation via the
`clear()` helper") and the method docstring ("Test-only - production code
should never need to call this", the only mutator bypassing `_check_mutable`).
The distinguishing fact: `clear()` drops the entire build (`_types`,
`_definitions`, `_enums` alongside `_pending`) — pending intents belong to the
discarded build and their definitions reference discarded classes, so retaining
them would corrupt the fresh lifecycle. A loud failure on nonempty pending
would break the primary teardown use (reset after a retained-list Phase-1
failure). Production misuse (calling test-only `clear()` live) already discards
the whole registry; pending silence adds no independent loss. The residual risk
is oracle-strength only — D1 — not behavior. C3 verdict: contract, correctly
rejected as a consolidation; D1 correctly kept as proof-strength.

**D1 dedupe judgment.** Confirmed identical home: `tests/test_registry.py`
`test_clear_drops_all_state` pins maps/enums only (verified at source: asserts
`get` / `model_for_type` / `get_enum`, no `_pending` or `_definitions` arm),
while `test_unregister_removes_pending_relations_sourced_from_type` pins the
subset drop, not the full drop. The definition-store D1 names the same test
extension per W1; one card extending that single test with both arms covers
both gaps. Worker 0 to dedupe at closeout — endorsed. No new `(Worker 2)`
defect entry: D1 already stands, and the sweep found no further defect.

**Gate judgment.** No new gate owed — endorsed. The identity contract (the only
behavioral variation axis) is pinned by
`test_discard_pending_uses_identity_match_with_real_pending_relation` with a
proved negative control (N1: equality mutation fails exactly the twin row).
Ledger unity cannot be behavior-pinned (a hand copy passes every oracle by
construction); only a source census could, and that is the bespoke-existence
shape `DRY.md` forbids for gate-only findings — the same bar as the verified
enum-cache, definition-store, taxonomy, and accessor items. Triggers
T-producer / T-drain / T-record plus standing oracles (atomicity pair,
unresolved wording, unregister-subset, drain rows) carry the remainder; D1
names the one unpinned arm.

**Freshness re-hashed (Worker 2, `git hash-object` full ids).**
`registry.py` `9cc8bb553fd417fc465809a541769a8383469cda`,
`types/relations.py` `6bd7c63da7787c61624960dd8060f67671c03d44`,
`types/base.py` `91c587477ff8257e80dbb9a9c79859f34c5b4c7e`,
`types/finalizer.py` `77fd9a2dd229eb9de5f29188c5058035d3606323`,
`types/converters.py` `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`,
`types/definition.py` `fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`,
`sets_mixins.py` `ad8987ea2fb18bc9f2809ed3b203e87a78db5ba3`,
`tests/test_registry.py` `e330cfb81e4bbe9f4f04bc7e1b30038097a3bb10`,
`tests/types/test_relations.py`
`89b5c6ffb04b0c9eae759460b899ef1acf775dde`,
`tests/types/test_finalizer.py`
`462275e5fbaed61bded4aecbb0fd98f6d6847e4d`,
`tests/types/test_definition_order.py`
`7dd04d67ed4d35c6aff138c7ed8193458691f38a`,
`tests/types/test_generic_foreign_key.py`
`5dd0d3871e784bd767b5ce5cf7ce760e34cf482c`, `GOAL.md`
`7dfbef5c784519d5f95311aaeb8c6766ee966b02`. Every prefix matches the finding;
no fingerprint changed.

**Item-scoped diff.** Empty on all four member paths vs both `ITEM_BASELINE`
`960a0c6b8c7bebe2244c79222d15da27ceb18138` and `HEAD` `bfaee91d` (both diffs
byte-empty, re-confirmed). `AGENTS.md` prose on the zero-edit artifact: no
tracked production/test edits, no `CHANGELOG.md` touch, `path::Symbol`
citations with link definitions, scratch paths named by explicit path for
Worker 0 removal, concurrent dirt (auth/mutations, connection, filters/forms/
mutations/optimizer sets, resource policy, `tests/*`, hunt + plan docs)
preserved untouched. Ruff on all four members: `ruff format --check` green
(4 files already formatted), `ruff check` green.

**`## Pending execution` empty — judged correct.** No `execution-deferred`
proof remains (29/29 probes + N1 negative control `execution-verified` with
copy `__file__` + copy DB recorded, no source mutation; one authorized
shared-tree focused run green with zero edits in flight). No test run repeated
here per standing rule. Sharded/PG `inapplicable by construction` accepted:
every executed claim is in-memory dict work plus class construction with no DB
open. Full-suite gate business stays with the final-gate item.

Status: verified.
