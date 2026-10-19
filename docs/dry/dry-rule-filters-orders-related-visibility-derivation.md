# DRY review: `filters-orders-related-visibility-derivation`

Status: verified
Run: 0.0.15 2026-10-12-29

Three derivations, three specified lifetimes, two consumers: filters nested-branch
(per-branch filtered rows, eager per level, no memo), filters flat-hop (per-scope
rows, request-wide memo), orders per-scope (per-scope rows, per-call memo). No
shared rule survives the challenges. REJECT unification. Zero-edit.
`ITEM_BASELINE=42ee501820e5ea5a588df5588a46bfdf257ee992` (HEAD `c37a08a0`
unmoved; zero-edit so attribution moot). Never read any `worker-memory/`.
Fences honored: seeds as given (e8), run-24 item-2 `apply∘initial` verdict
stands (built on, not re-litigated), run-24 item-1 verdict routing stands.

## System trace

Filters nested `filters/sets.py:3427-3484` + `:3487-3519`: per active branch,
`apply_type_visibility_*` then recursive child `apply_*`
(`run_permissions=False`, `_depth+1`); keyed by branch name; fresh dict per
level. Filters flat `:3962` / `:4056` / `:4079` / `:4099`: per-scope rows in
the request-wide hop map, keys `(id(declaration),alias)` / `(scope,alias)`;
sync first-use, async prefill. Orders `orders/sets.py:922-943` (lazy closure,
key scope, own recourse `:939`) / `:946-967` (eager prefill, `__getitem__`):
per-scope rows, per-call memo. Shared below (compose by name): apply twins
(`querysets.py:4554/:4923`), custom verdict + `relation_target_type` /
`relation_visibility_type` / `relation_path_visibility_types` (`:4711/:4744/
:4764`), `walk_declared_relation_path` + `RelationHop` (`permissions.py:587/
:546`), `leading_relation_hops`, `_iter_visibility_steps` (`:3332`),
`visible_row_exists` / `visible_value` (`predicates.py:422/:434`) vs
`related_rows_exist` (`:334`). Consumers: filters `apply_sync/async`,
`_q_for_branch` (`:4762/:4769` fallback), `_apply_related_constraints`,
`_apply_active_leaf`; orders `_resolve_order_expressions`, `_apply_orderings`,
`apply_sync/async`. Excluded subjects: instance rechecks, node/locate, cascade,
walker child, write decodes (run-24 items 1-2 + run-22 items 9-10 verdicts).

## Verification

### Matrix

1. Cross-flavor: write/cascade/node/instance/walker/list/connection compose the
   apply twins with per-subject seeds; run-24 item-1 R2 + item-2 R1-R4 carry.
2. Sync/async: all three derivations twin; rows agree across colors (P1-P3),
   hook-call counts differ only where specified (P3 `derivations[mode]`).
3. Derived-twice: three key grammars (branch / scope / (scope,alias)) for three
   lifetimes; walk inputs pre-resolved through shared primitives.
4. Round-trip: N/A — derivation is one-way (input -> scoped rows).
5. Media: spec-027 D8 (decomposition, steps 3/4a/5/8, split) + spec-028 D8
   (step 4, step 7, split, no-dispatcher); owner docstrings name each pairing.
6. Omission: filters nested + flat and orders per-scope each carry theirs;
   forms/mutations decode single relations (no traversal); cascade applies
   unconditionally per contract. None lacks its derivation.

### Challenges

- F1 nested-vs-per-scope: Y1 new relation shape -> per-family assembly (walks
  already share primitives). Y2 new verdict -> apply boundary once. Y3 new set
  family -> 0 existing moves (precedent: orders never reused filters').
  Y4 twin-color change -> per-driver. Max 1 per rule.
- F2 flat-per-scope-vs-orders-per-scope: X1 key dimension -> filters only
  (orders alias fixed per closure). X2 apply seam -> apply once, both consume.
  X3 lifetime change -> one side. X4 None-posture / X5 undeclared fallback ->
  filters only. Max 1, each already-single.
- F3 twins: behavior-agreement oracles both colors both families (P1-P3); no
  experiment owed beyond P1 (bodies unambiguous + specified counts).

## Findings

F1 (nested-branch vs per-scope) — REJECT, two contracts. Subjects differ
(branch+input+recursion vs scope-only), keys (branch name vs scope type),
recursion (child apply + depth cap vs flat), consumers (EXISTS restriction vs
NULL-masking), timing (eager per level vs lazy/eager per call), memo (none vs
per-call). Challenges Y1-Y4 (max 1). Owner: none new — nested stays at the
derive twins, per-scope at `_visible_rows_*`. Migration: none. Shrinkage: 0;
machinery attestation: no helper — a shared driver needs branch/scope adapters
+ a recursion seam + both consumers, owning nothing. Distinct: everything
above stays per-family. Proof: P1 execution-verified; P2-P5 static (bodies
read; one-test budget spent on P1). Negative control: P1 + P5 (leak fails
them). Coupling: e8 seeds; run-24 items 1-2 verdicts; e7 seal exclusion.
Freshness (WT blobs; HEAD `c37a08a0`): `filters/sets.py befa6d92`,
`orders/sets.py 79c369b3`, `querysets.py f9267729`, `permissions.py dbb8f602`,
`predicates.py 9e7d80d1`, `test_sets.py(filters) ed3065ac`,
`test_sets.py(orders) b0bfb16e`, `test_library_api.py b9aa189d`,
`spec-027 a73f8674`, `spec-028 f2fa4c08`, item-2 artifact `cc84f615`, item-1
artifact `b7e44992`, folder-orders `5b52563e`, folder-filters `69637e95`.
Searched: full package + test trees for the derivation mechanism; contract
sources spec-027 D8, spec-028 D8, run-24 items 1-2, FR-1, FC-9.
P1 `test_library_api.py:4235` `[declared-to-one-ascending]` — live orders
hidden-as-missing; rejects a leak (misplaced row) and a broken prefill.
P2 `:4265/:4363/:4396` + staff twins — connection/nested/async agreement.
P3 `tests/filters/test_sets.py:10812` — once-per-request + inactive-never
(sync) / supplied-costs-one (async); pins the flat lifetime AND the specified
twin count divergence. P4 `:5578/:6317/:6857` — nested scope + fail-closed
raise + alias threading. P5 `:11142/:11695/:12295/:12650` — hidden-as-absent
across kinds, hops, arms (bypass pins).
R1 instance rechecks: subject + alias/filter between + color-aware (item-2 R1
re-checked unfired at current bytes). R2 node/locate: identity + twin +
pin/lock (item-2 R2/R3 unfired). R3 cascade/walker/list/connection/write
decodes: unconditional/plan/caller-source/single-relation (item-1 R2, item-2
R4, run-22 items 9-10; no bare-`initial` adoption — unfired). R4 nested-twin
pairing (`_iter_visibility_steps` shared, application colored): two machines
per principle 5 (must await consumer hooks; connection.py precedent).
Trigger: a color-polymorphic apply pipeline — then the pairing re-opens.
R5 orders twin split: FR-1 re-checked unfired (seed sites still exactly
`:934`/`:965`, still composing `base_queryset` + `model_for`). R6 flat-twin
split + nested-vs-flat (`_derive_flat_hop_visibility_async` names the twin):
`filters-hop-visibility` file-local CONFIRMED (no second site found).
Trigger: a derivation with the flat map's lifetime outside filters.
Sub-rules named for the index: `filters-nested-branch-derivation` (owner the
derive twins; merge vs orders rejected with F1 trigger: a branch derivation
keyed/consumed per-scope); `orders-per-scope-derivation` (owner
`_visible_rows_*`; merge vs filters rejected with F2 trigger: a per-scope
derivation sharing the flat map's lifetime or the nested recursion);
`set-derivation-twin-coloring` (coloring-forced splits; converges FR-1 +
file-local + principle 5; trigger: R4's).

F2 (flat per-scope vs orders per-scope) — REJECT, two contracts. Same subject
(scope rows), different lifetimes by spec (per-request shared map threaded
through siblings vs per-call closure), keys (`(scope,alias)` vs scope),
recourse (default vs per-surface — item-2 C3 + FR-3), None-posture (skip vs
impossible), undeclared fallback (raw `_base_manager` vs pre-filtered).
Challenges X1-X5 (max 1). Security clause considered and refused: unifying the
key grammar risks cross-alias reads (data leak); the residue past the fenced
seed + single apply is a 6-parameter one-liner (machinery, owns nothing).
Owner/lifetime: flat map owned by the filterset instance (`_hop_visibility`,
request validity, published by apply, read by leaves/arms/children);
orders closure owned per `apply_*` call. Migration: none. Shrinkage: 0.
Proof/negative/freshness: as F1 (P1/P3 decisive).

F3 (twin symmetry) — HELD, coloring-forced. Orders lazy-sync vs eager-async
(FR-1, trigger unfired); filters nested symmetric loop over a shared iterator
with colored application; filters flat sync-read vs async-fill. Awaiting
consumer hooks on the loop forbids sync-in-worker collapse (raises instead of
awaiting = behavior change). No moves. Proof: P1-P3 row-agreement.

## Defects

None.

## Pending execution

None.

## Judgment

One rule would need one subject, one key grammar, one lifetime, one consumer.
The trace finds two subjects (branch vs scope), three grammars, three
lifetimes, two consumers — each specified, each pinned, each challenge max 1.
Sharing past the already-single primitives buys adapters, not fewer
definitions. REJECT, zero-edit, ready for verification.

## What shrinks

Net package lines over `ITEM_BASELINE=42ee5018`: 0 (zero-edit — nothing to
port; no ledger row owed).
Population census (whole package, related-visibility derivation): 3
derivations — filters nested (`filters/sets.py:3427/:3487`, iterator `:3332`,
e8-fenced seed `:3379`, arm prefill `:3549`, consumers `:4762/:4769/:4812/
:4970/:5041`) + filters flat (`:3962/:4056/:4079/:4099`, via `:4012/:4038`,
consumers `:4394/:4405/:4411`) + orders per-scope (`orders/sets.py:922/:946`,
walk `:782`, consumers `:843/:979/:1023/:1064`) — over 8 shared primitives
(apply twins, custom verdict, 3 resolution fns, declared-path walk + hop,
`leading_relation_hops`, per-family seed/iterator), 2 predicate consumers
(`visible_row_exists` + `visible_value` vs `related_rows_exist`), 6 excluded
subjects (R1-R3). Lifetimes: per-level none / per-request shared /
per-call local — each spec-pinned (spec-027 D8 step 3 hop-map sentence,
spec-028 D8 step 4 once-per-call sentence).
Refused machinery: a scope-rows memo helper (key + seed + recourse + map as
parameters around one `apply` line — owns zero decisions, and a unified key
grammar mis-serves one alias family); a nested/branch shared driver (branch +
scope adapters + recursion seam + both consumers); a color-polymorphic derive
(sync-in-worker breaks async-only hooks by raising instead of awaiting).
All prior triggers re-checked unfired at current bytes (FR-1 seed census 2,
item-1/item-2 routers and exclusions, FC-9 seal posture, file-local row).

## Independent verification (Worker-2) — pre-read trace (written before opening ## Findings)

Sites (own code trace; roles mine). Definitions: D1-nested-sync
`django_strawberry_framework/filters/sets.py::FilterSet._derive_related_visibility_querysets_sync`
(dict[str, QS], key declared branch name, value visibility+child `apply_sync`) and
D1-nested-async `::_derive_related_visibility_querysets_async` (same, awaited) = 1
logical derivation, 2 colored bodies. D2-flat = the request-wide hop map
(dict[tuple[object, str|None], QS]; keys `(id(related_filter), parent_db)` declared,
`(scope, parent_db)` undeclared/via): writers `::_derive_flat_hop_visibility_async` +
`::_await_scoped_rows` (async pre-fill) and `::_hop_visible_rows` + `::_scoped_rows`
(sync on-first-use) = 1 logical derivation, colored halves. D3-orders-sync
`django_strawberry_framework/orders/sets.py::OrderSet._visible_rows_sync` (lazy
`_VisibleRows` closure over dict[type, QS]) and D3-orders-async
`::_visible_rows_async` (eager pre-derive over `_active_order_terms` x `_scoped_hops`)
= 1 logical derivation, 2 colored bodies. Shared single-owned primitives (not
candidates): `django_strawberry_framework/utils/querysets.py::apply_type_visibility_sync` /
`::apply_type_visibility_async` (+ `::_prepared_visibility_source` /
`::_normalized_visibility_result` sealed boundary), `::relation_target_type` /
`::relation_visibility_type` / `::relation_path_visibility_types`,
`django_strawberry_framework/types/base.py::DjangoType.has_custom_get_queryset`,
`django_strawberry_framework/utils/permissions.py::RelationHop.scope` +
`::walk_declared_relation_path`, `django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin._iter_active_related_branches`,
`FilterSet::_iter_visibility_steps` + `::_branch_visibility_seed` +
`::_target_type_for_related_filter` + `::_visibility_hops` / `::_flat_leaf_walk`,
`OrderSet::_scoped_hops`, `django_strawberry_framework/utils/relations.py::leading_relation_hops`,
`filters/sets.py::_scoped_seed_rows`. Consumers: filters `::apply_sync` / `::apply_async` /
`::_apply_related_constraints` / `::_q_for_branch` / `::_evaluate_logic_tree` /
`::_collect_nested_visibility_querysets_async` / `::_apply_relation_leaf`;
orders `::_resolve_order_expressions` / `::_apply_orderings` / `::apply_sync` /
`::apply_async`; predicates `visible_row_exists` / `visible_value` (orders) vs
`related_rows_exist` (filters). Oracles (to confirm post-read): behavioral
visibility tests at the live tier (async-only hook refusal, hidden-row
ordering/filtering). Projections: owner docstrings, spec-027 D8 / spec-028 D8.

Counts (mine, per posited change). C1 key grammar (nested `str` vs flat
`(object, alias)` vs orders `type`): rename/rekey one moves exactly 1 derivation;
cross-derivation count 1 each → independent. C2 subject (nested stores FILTERED
child qs via child `apply_*` with `run_permissions=False` + `_depth`; flat/orders
store VISIBLE rows only): change filter composition moves D1 only (count 1);
change hook invocation moves shared `apply_*` (count 1). C3 lifetime (nested
ephemeral per-level dict vs flat request-wide `_flat_hop_visibility` shared across
siblings vs orders per-call closure): re-lifetime one moves 1. C4 seed/alias
(`parent_db` pinning): `_branch_visibility_seed` (declared, resolves
type+filterset+base, real logic) vs `_scoped_seed_rows` (one-line `base_queryset`
wrapper) vs orders inline `base_queryset(model_for(scope), using=...)` x2 (one
line): 3 spellings but only 1 carries resolution logic per subject; bar needs 2+
with real logic → below bar. C5 coloring (unify sync/async twins): sync must raise
`SyncMisuseError` via `apply_sync`, async must await; one body changes observable
behavior (principle 8) → twin pairs HELD, 1 logical each. Owner I would choose:
keep 3 derivations at current owners (nested at `FilterSet._derive_*`, flat-hop at
`FilterSet._hop_visible_rows/_scoped_rows/_derive_flat_hop_visibility_async`, orders
at `OrderSet._visible_rows_*`); primitives stay where they are; no new
driver/helper/key-grammar unifier. Security expectation: sync-behind-async-only
must refuse loudly; unscoped rows must never leak via a unified key.

## Independent verification reconciliation (Worker-2) — verdict `verified` (plain)

Reconciliation (every difference explicit): none material. My D1/D2/D3 = W1's 3
derivations; my C1-C5 map onto F1/F2/F3+X/Y with identical counts (max 1 per
rule, twins 1 logical each); my owner (keep 3, no machinery) = W1's. Independent
whole-package search (every `apply_type_visibility_*` caller composes by name
with a per-subject seed; verdict/walk primitives single-owned) found no fourth
derivation and no missed pair — closest near-miss (flat vs orders per-scope
seeds) is 2 one-liners + 1 resolver, below the bar's real-logic test. Matrix:
all 6 axes discharged against the real surface (axis 4 N/A sound — one-way
derivation, predicates are consumers not inverses). Rejections: F1/F2 carry
contract differences + triggers (sub-rule index rows); R4/R6 carry triggers; R5
FR-1 re-confirmed unfired at current bytes (seed sites exactly `:934`/`:965`,
both `base_queryset(model_for(scope), using=...)`); R1-R3 exclusions stand on
re-checked prior verdicts + fences. F3 HELD correct (coloring-forced per
principle 5: sync must raise `SyncMisuseError`, async must await; collapse =
observable behavior change). Proofs: P1 reproduced green in the shared tree
(`test_related_order_reads_a_hidden_row_as_missing_for_anonymous`, 8 passed,
live `/graphql` tier, exact anonymous/staff orders — fails on a leak or broken
prefill); P2-P5 bodies read — all behavioral exact-set/order/count assertions,
static suffices, no oracle reads its owner. Negative control genuine (P1 + P5
hidden-as-absent pins fail on any leaked row). Refused security clause sound
(unified key grammar drops the alias dimension the flat map keys on →
cross-alias reads; residue past fenced seed + single apply is a parameter
carrier, i.e. machinery). Freshness: 12/14 fingerprints match; the 2 misses
(item-1/item-2 artifacts) are W2 verification appendices post-dating W1's pins
(both now `Status: verified`, cited verdicts intact) — verdict-neutral, cured
in-record. Scoped diff empty (package `git diff ITEM_BASELINE` = plan lines
only; live untouched; artifact-only change); `path:NN` citations permitted in
`docs/dry/dry-*.md`; no new tests owed; ruff format-check + check pass on the
touched path (artifact is `.md` — lint trivially clean). No defects found;
`## Defects` stays `None`.
