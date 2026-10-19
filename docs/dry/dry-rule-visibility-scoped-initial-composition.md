# DRY review: `visibility-scoped-initial-composition`

Status: verified
Run: 0.0.15 2026-10-12-24

The `apply∘initial` composition has no own variation: seed, recourse, and
apply are each single-owned elsewhere, and the residual pairing is one
variable used twice. REJECT unification. Zero-edit.
`ITEM_BASELINE=c4c741202171ead8a623e4d4a0f94a8bd27b42d0` (HEAD `c37a08a0`
unmoved; every member path dirty-concurrent, unattributed hunks moot — no
edit). Never read any `worker-memory/`. Fences honored: seeds taken as given
(e8), the related-decode chain is context (run-22 item 9), GlobalID decode
out (run-22 item 10).

## System trace

Helper `utils/querysets.py:4637-4658` =
`apply(related_type, initial(related_type), info, async_recourse)`; 1 direct
caller (`related_visibility_queryset:4687`); zero test/example/script
references. `locate_instance` (`mutations/resolvers.py:706-748`) inlines the
same shape with `_MUTATION_ASYNC_RECOURSE` (:736-741) inside
`pin_write_queryset` + `base_locked_queryset`. Node resolvers
(`types/relay.py`) inline it x3 sync (:1071, :1141, :1143) + x3 async (:1096,
:1166, :1168) with default (Relay) recourse; no async helper exists. Twin
`types/resolvers.py::_visible_related_object` (:462-483) seeds at :470 but
pins `.using(alias)` (:471-473) + `.filter(pk)` (:474-475) BETWEEN seed and
apply (:479/:483). Whole-package census: 26 executable `apply_*` calls, 8
spelling `apply∘initial` (helper + locate + node x6); every other call seeds
differently (cascade :704 alias-pinned + render/policy; orders :934/:965
alias-pinned; connection :1931/:1994 pipeline source + model=; filters
child_base / `_scoped_seed_rows`; walker :666 plan child + seams; list_field
:1434/:1480 caller source + model=; `_visible_many_rows` caller source).
`initial_queryset(` census complete: the 8 + twin seed :470 + `refetch_optimized`
:886 (no apply — the spec-036 D9 recorded exception) + def + prose cites.
`model=` reaches apply only at excluded-seed sites; composition sites are
type-keyed and omit it by contract (apply docstring :4603-4606). Recourse:
relay default (:433-436), pipeline template (:440-458), mutation constant
(:223), form constant passed at :241, serializer passed at :1553, model
decode passed at :682.

## Verification

### Matrix

1. Cross-flavor: chain surfaces (model/form/serializer) compose the helper
   via `related_visibility_queryset(_or_default)`; node/locate are not
   parties to the spec-038 invariant (owner: write_values spine, spec-038:1265).
2. Sync/async: node is a twin pair; the helper is sync-only. Routing the sync
   half alone splits the twin (principle 5); an async twin helper is new
   public API for zero obligation.
3. Derived-twice: the pairing is single-variable-twice-use at all 8 — zero
   logic, zero branches; seed/recourse/apply each single-owned.
4. Round-trip: N/A — the composition has no inverse (decode halves fenced).
5. Media: helper docstring (related-decode contract); spec-039:2396/:2481
   cite the public name; spec-038:551/:1265 the invariant; e3 R1-R5 triggers
   re-checked unfired at current bytes (see Findings).
6. Omission: `refetch_optimized` the ONE recorded exception (spec-036 D9);
   every other initial-seed applies (census complete).

### Challenges

- C1 thread `model=` through the composition -> 0 move (type-keyed omit by
  contract; every `model=` passer seeds differently). Count 0.
- C2 change the seed -> `initial_queryset` once (e8's unit). Count 1.
- C3 change recourse -> one constant each (relay / pipeline template /
  per-surface); the helper threads it as a parameter. Count 1 each.
- C4 the pairing must diverge (`apply(A, initial(B))`) -> implausible: one
  variable used twice; a cross-model mismatch fails closed at the source
  seal (model-row validation). No drift at any of the 8. Count 0.
- C5 a new mandatory apply seam -> all 26 apply callers move as consumers
  (listed, not counted); the composition gains no shared step. R5's trigger
  ("a composition-level step all four sites adopt identically") unfired.
- Full-coverage variant (rename + async twin) = public API change + new
  helper removing zero definitions — barred machinery.
- No experiment owed: every behavior below is read from unambiguous bodies.

## Findings

F1 (apply∘initial composition) — REJECT, per-subject contracts. Sites: 1
helper definition (related-decode composition) + locate/node inlines as
consumers composing `apply_*` + `initial_queryset` by name, each carrying its
subject contract; twin/many + the 18 other-seed calls excluded; oracles
P1-P4; projections (docstrings, spec-038/039, e3 record). Challenges C1-C5
above (max count 1, at already-single lower owners). Owner: none new — the
helper keeps the related-decode composition; locate/node contracts stay at
their bodies. Migration: none. Shrinkage: 0 lines; machinery attestation: no
helper added — a generic rename is a public API change (spec-039:2396/:2481
cite the name) and full coverage owes an async twin; both refused for zero
obligation removed. Distinct behavior: three pin disciplines (none / instance
alias / write alias), two colors, recourse per surface — stay per-site.
Behavioral proof: P1 execution-verified (1 passed this session via `heavy`,
`--no-cov -n0`); P2-P4 static-reviewed (bodies read; one-test budget spent on
P1). P1 `tests/test_permissions.py:1870`
`test_sync_helper_raises_syncmisuseerror_on_async_target_hook` — rejects a
unified fixed recourse (cascade wording + "Relay node defaults" absent). P2
`tests/types/test_relay_interfaces.py:887,915,950` — node twins refuse
homogeneously ("one error shape"); sync-only routing splits the pair. P3
`tests/utils/test_write_values.py` recourse-threading pins +
`tests/rest_framework/test_resolvers.py:1315` — the helper's recourse
parameter is a live contract. P4
`tests/mutations/test_resolvers.py:1318,1392` — locate's pin+lock sandwich is
fused with its composition. Negative control: P1's NOT-relay assert (a
fixed-recourse unification fails it); the twin's alias-between (helper
routing would mis-seal routing — the seal reads `source.using` pre-hook).
Coupling: e8 owns seeds; run-22 item 9 owns the trio; run-22 item 10 owns
GlobalID decode. Freshness (WT blobs; HEAD `c37a08a0`):
`utils/querysets.py f9267729`, `mutations/resolvers.py 8710bfa9`,
`types/relay.py f3673a1b`, `types/resolvers.py 8cd980b0`,
`test_permissions.py ad552c1b`, `test_relay_interfaces.py 5c5ed7fe`,
`test_write_values.py 281f0545`, `test_resolvers.py(mutations) c88b0d9b`,
`test_resolvers.py(rest_framework) 03e9c8c0`, e3 artifact df48972c.
Searched: full package + test trees for `apply_type_visibility_*` (26
executable calls) and `initial_queryset(`; contract sources spec-036 D9,
spec-038, spec-039, e3 R1-R5.
R1 twin (`_visible_related_object`): instance subject + alias/filter between
seed and apply + gated/custom-only/color-aware — different composition.
Trigger (e3 R1, unfired): drops gates, goes sync-only, takes `(model, pk)`.
R2 node: self-type identity + twin + id-attr/required/bulk. Trigger (e3 R2,
unfired): async helper appears AND relay collapses to pk-first.
R3 locate: write target + pin/lock concurrency contract. Trigger (e3 R3,
unfired): drops pin + lock.
R4 other-seed calls (cascade/orders/connection/filters/walker/list/many):
different seeds (+seams). Trigger: a site adopts bare `initial_queryset(T)`
with no seam — then it joins this question.
R5 composition routing (e3 R5 confirmed fresh): no own variation (C1-C5).
Trigger (unfired): a composition-level step all sites adopt identically.
R6 helper name `..._related_...`: kept (public; rename = API change).
Trigger: a second subject routed through it — then the rename re-opens.

## Defects

None. The helper docstring's "model and form paths pass their own
surface-specific wording" verifies true (model :682, form :241, serializer
:1553, write_values pass-through :258/:382).

## Pending execution

None.

## Judgment

Eight sites spell `apply(T, initial(T))` with one variable; everything that
can vary (seed, recourse, apply, seams) is already single-owned, and the
surroundings (three pin disciplines, twin symmetry, per-surface recourse,
public related-name) defeat sharing. Generalizing buys a public rename +
spec churn + an async twin and removes zero definitions. REJECT, zero-edit,
ready for verification.

## What shrinks

Net package lines over `ITEM_BASELINE=c4c74120`: 0 (zero-edit — nothing to
port; no ledger row owed).
Population census (whole package, `apply_type_visibility_*` mechanism): 26
executable calls — 8 spelling `apply∘initial` (helper
`utils/querysets.py:4653`, locate `mutations/resolvers.py:736`, node
`types/relay.py:1071/:1141/:1143` sync + `:1096/:1166/:1168` async) + 18
excluded (twin `:479/:483` with alias/filter between + many `:502/:513` on
caller source; cascade `permissions.py:711` alias-pinned + render/policy;
orders `:935/:966` alias-pinned; connection `:1931/:1994` pipeline source +
model=; filters `:3476/:3511/:4006/:4129` child_base + `:4075/:4090`
`_scoped_seed_rows`; walker `:666` plan child + seams; list_field
`:1434/:1480` caller source + model=).
`initial_queryset(` census: the 8 + twin seed + refetch seed (no apply,
spec-036 D9) + def + prose cites — complete, nothing unassigned.
Recourse census: relay default + pipeline template feeding 3 flavor constants
+ per-surface constants (cascade/walker/orders), each passed explicitly; the
helper threads recourse as a parameter with production callers passing their
surface wording.
Refused machinery: a generalized sync helper (public rename; spec-039 cites
the name twice) + an async twin (new public helper) — two API changes
removing zero definitions, since C1-C5 max out at count 1 on already-single
lower owners.

## Independent verification (Worker-2)

Own trace (before Findings): 26 executable `apply_*` calls re-derived
independently (relay 6 + locate + helper = 8 spelling `apply(T,
initial(T))` bare; twin 2 with `.using(filter)` between; many 2 on
manager source; cascade 1, orders 2, connection 2, filters 6, walker 1,
list 2 — every one seeded off `base_queryset`/pipeline/caller source,
never bare `initial_queryset`). `initial_queryset(` census: the 8 + twin
seed + refetch seed (no apply, spec-036 D9) + def + 5 prose cites —
complete, no 9th site. Helper: 1 direct caller
(`related_visibility_queryset:4687`), zero test/example/script refs;
no async helper exists. Roles: helper = related-decode definition;
locate/node inlines = consumers composing two single-owned primitives
by name; twin/many/18 = excluded other-seed consumers.
Challenges (own): C1 thread `model=` -> 0 (no composition site passes
it; `model=` reaches apply only at connection/list/walker, all
excluded-seed; omission is contract per apply docstring
"Type-keyed callers omit it"); C2 seed change -> 1
(`initial_queryset`, e8); C3 recourse change -> 1 per surface
constant, helper threads it as a parameter (threading verified at
mutations :646/:682/:740, forms :241, serializer :1553, write_values
:258/:382); C4 `apply(A, initial(B))` -> 0 (source seal rejects
cross-model with the `table` defect; verified in `_seal_or_defect`);
C5 new mandatory seam -> consumers move, composition gains no step.
Owner I would choose: none new. No shareable sync-half (node sync
triple has zero own variation; routing it splits the twin for no
obligation); no P11 deletion (helper is the spec-038 invariant's
public boundary, cited by spec-039 twice at :2396/:2481 — verified).
Reconciliation: censuses 26/8/18, C1-C5 counts, R1-R6 + e3 triggers
(all re-checked unfired at current bytes: twin still gated/custom-only
with alias/filter between; no async helper; relay still
id-attr/required/bulk; locate still pin+lock), and the twin
mis-seal negative control (seal reads `source._db` pre-hook via
`queryset_db`; helper takes no alias) all agree with W1. P1's
NOT-relay assert confirmed at `tests/test_permissions.py:1901` and
re-run green this session (`heavy uv run pytest
tests/test_permissions.py::test_sync_helper_raises_syncmisuseerror_on_async_target_hook
--no-cov -n0 -q` -> 1 passed). P2-P4 static suffices: zero-edit
REJECT needs no equivalence execution; P2-P4 are existing oracles
whose claimed pins I read and confirmed, and the gate re-runs them.
Freshness: 10/10 blobs re-hash equal (9 code/test + e3 `df48972c`);
HEAD `c37a08a0` unmoved; item-scoped diff EMPTY (whole-tree diff vs
baseline = 6 plan-bookkeeping lines in `dry-0_0_15.md` only; target
files byte-equal to baseline). AGENTS.md prose: artifact-only change,
`path:NN` cites legal in `dry-*.md`, no process provenance; nothing
to ruff. Nit (verdict-neutral, not a defect): P2 cites read 887/915/950
vs `def` lines 888/916/951 (decorator counting). No `(Worker-2)`
defects. Verdict: verified, REJECT zero-edit stands.
