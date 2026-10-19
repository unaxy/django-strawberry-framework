# DRY review: `branch-target-type-resolution`

Status: verified
Run: 0.0.15 2026-10-11-17

## System trace

Seeds re-derived fresh. (A) `filters/sets.py::FilterSet._resolve_relation_target_type`:
field-driven (`cls` owner map `related_target_for(field_name)` to `.origin`, else
`registry.get(field.related_model)`); sole caller `filter_for_lookup` (generation
wire-shape). (B) `filters/sets.py::FilterSet._target_type_for_related_filter`:
branch-driven (child binding `.origin`, else `registry.get(child._meta.model)`);
callers `_branch_visibility_seed` (request `get_queryset` scoping) + finalizer
subpass-2.5 audit. Swept: every `.origin` read, `related_target_for` caller,
owner-preferring registry caller, orders `_scoped_hops`, finalizer axes, relay
decode. Probe P1-P8 green (see `## Implementation (Worker-1)`).

## Verification

### Matrix

1. Cross-flavor: orders scoping PRESENT per-hop (spec-028 D8s4); write flavors
model-only by spec (039D7, 036D11: no owner exists); cascade/resolver model-only
(no binding at layer). Discharged.
2. Sync/async: A/B sync pure derivation; visibility twins consume B's answer,
never re-resolve. Discharged.
3. Derived knowledge: four `related_target_for` callers answer different outputs
(type / definition / pair / agreement bool); all registry fallbacks compose
`registry.get` by name. Discharged.
4. Round-trip: relay decode takes wire input (no owner possible); GlobalID halves
share the strategy slot, not these resolvers. Discharged.
5. Other media: 10 oracles spell literals (10/10 green); spec-027 D4/D8 +
spec-028 D6/D8 prose; docstrings cite by name. No second definition. Discharged.
6. Omission: orders scoping present per-hop; single-type-helper absence
intentional (spec-028 D6/D8s4 + finalizer pairing prose). No gap. Discharged.

### Enumeration

`muse.search` regex over the package for `\.origin`, `related_target_for`,
`_owner_definition`, `registry\.(get|primary_for)` + body reads. 1 `.origin`
definition (the dataclass field) + 30 consumer reads: bound-type readers (B arm,
own-PK, via-types root, `set_bound_type`, walker pair); mapped-target readers (A
arm, base.py walk, finalizer agreement); decode/validate (relay decode, list +
connection validators, testing gate); message renders (projections). 0 ungrouped.

### Challenges

- C1 slot rename: mechanical incl. writers that cannot compose a reader. No count.
- C2 `.origin` shape: definitions 1, readers consumers; A+B merge relieves
12 readers to 11. Count 1.
- C3 registry precedence: moves inside `registry.get`; A/B move 0. Count 1.
- C4 new axis: field-binding overrides move A only; child multi-binding B only;
new hop `_scoped_hops` only. Count 1 each.
- C5 observability (execution): P7 A bound-is-unbound; P8 B bound-is-not-unbound;
P3 same model, different answers. Split observed.

## Findings

### F1 A-vs-B — REJECTED (distinct contracts)

Six axes. Inputs disjoint (field + name vs `RelatedFilter`; key leaves have no
child set; branch names may span hops, P6). Owner slot: `cls` map vs child
identity. Model: field vs child `_meta`. Precedence: A arm stays primary-keyed
(P1), B arm binding-keyed, secondary-capable (P2). Consumers: generation vs
request visibility + finalize guard. Liveness: A arm production-vacuous
(first-bind lineage + Django inheritance return the same field object; only the
synthetic 5420 shape diverges) while B arm is the live row-leak guard (P8). One
shared helper would take a field-or-declaration union (banned mode flag) to own
3 lines of None-chaining (not real logic). Trigger: A arm live on a production
pair, either domain subsuming the other, or A gaining binding-keyed semantics.
Home: this artifact + the mirror docstrings.

### F2 B-arm-vs-`set_bound_type` — REJECTED (thin idiom)

Same answer bound (P4, zero drift); differ unbound (fallback vs None, P5), in
read mechanic (`truth.static_attr` vs `getattr`), in role (scoping decision vs
cross-family reader). Precedent holds (J1/J2, FF-P4). A merge moves spelling
while the security decision lives only in B. Trigger: the read gains logic past
the two-hop chain; then all inline readers migrate to the owner. Home: the
reader docstring + this artifact.

### F3 remainder — EXCLUDED on body strength

Own-PK: bool about the owner (axis 1), not a scoping type. Walker: keeps the
pair per the owner-stated one-definition rule. Base.py walk: multi-hop
definition for strategy checks. Relay decode: wire input, no owner possible.
Model-only callers: finalizer shapes (pre-binding lifecycle), serializer +
mutations (spec-pinned primary), cascade/resolver/write (no binding at layer;
lookup owner-invariant anyway). Finalizer axes/audit enforce or consume B;
axis-2 prose is projection. Trigger per site: a bound owner input answering
off-primary.

### F4 orders — PRESENT, no omission (axis-6 verdict)

`_scoped_hops` resolves per-hop via `set_bound_type` + `relation_target_type`;
oracles pin declared (2842) + re-entry (2895). Missing B-shape intentional
(terms span N hops; branches have one child). Missing A-shape is contract
(spec-028 D6: ORDER BY uses the column; zero type reads in orders generation).
Sources: spec-028 D6/D8s4 + finalizer pairing prose. No defect, no maintainer route.
Trigger: single-branch order scoping outside hops.

### F5 convergences — f59 adjacent; folder row part-superseded

f59 owns the COLUMN, this family the TYPE; handoff `filter_for_lookup` to A,
then RelationPk filters to f59's column. Axes disjoint; no row reopened.
Folder-filters `+ target-type` file-local bundling is SUPERSEDED for that
member (second sites exist; re-homed here as rejected merges), verdict
CONFIRMED (zero-edit); verified row stays shut per drift rule (Worker-0 homing).

## Defects

None filed. I1 (clear): A-arm vacuity is correct behavior (arms agree); no
contract row breaks, so per the bar not a defect. Kept in F1, not re-litigated.

## Pending execution

None. No `proof:` (probe + oracles green) or `gate:` owed. Sharded/pg cells
inapplicable by construction: pure derivation over `_meta` + registry +
bindings, no connection/alias/dialect read; DB oracles run default-cell only.
Worker-2 judges.

## Judgment

REJECT, zero-edit: A and B are distinct contracts (inputs, slots, models,
precedence, consumers, liveness), the reader overlap is thin idiom, orders
scoping is present per-hop by spec, and every same-token site carries its own
contract with a trigger. Nothing to consolidate.

## Implementation (Worker-1)

Zero-edit: no tracked file changed, no test added, no ledger row. Item diff vs
`ITEM_BASELINE=f2b70252` empty over tracked paths (artifact + probe
untracked-new; all else concurrent). Probe `PYTHONPATH=examples/fakeshop uv run
python docs/dry/temp-tests/branch-target-type-resolution/probe.py`: P1-P8 green.
Oracles `heavy uv run pytest <7 node ids, filters + orders test_sets>
--no-cov -n0 -q`: 10 passed in 5.97s. Gates via heavy: basedpyright 0/0/0, floor
0/0/0, truthful-reads tier-1 0, trailing-commas 0 violations, citations OK
(3351). WT pins: sets befa6d92 orders/sets 79c369b3 definition cde8437f
finalizer 2dbe6efc relay 3b4447ae permissions dbb8f602 querysets 1b0cf162
walker 02752d50 base 82c153fc f-test_sets ed3065ac o-test_sets b0bfb16e probe
dc911755.

## What shrinks

Nothing lands (zero-edit, net +0/-0 tracked): no shared definition exists and no
merge relieves an obligation. Under each trigger the relief is bounded so a
later cycle measures instead of re-deriving. F1 trigger (A arm live, one domain
subsuming the other, or A binding-keyed): the two prefer-owner-else-registry
chains collapse to one helper on the subsuming input; the loser's chain + twin
oracle arm delete. F2 trigger (bound-type read gains logic): the three inline
readers (B arm, own-PK check, via-types root) compose `set_bound_type` (~5 lines
each delete). F3 triggers (a model-only site gaining a divergent bound owner):
that site composes its matching primitive (`related_target_for` for field maps,
`relation_target_type(root=...)` for hops). F4 trigger (single-branch order
scoping): a B-shaped orders helper appears and the F1 challenge reruns over
three members. All triggers rerun from this artifact's enumeration baseline.

## Independent verification (Worker-2)

### Own trace (recorded before opening `## Findings`)

Seeds re-derived from bodies, not from the plan brief. (A)
`django_strawberry_framework/filters/sets.py::FilterSet._resolve_relation_target_type`
(field, field_name): DEFINITION, field-driven; owner arm
`cls._owner_definition.related_target_for(field_name).origin`, fallback
`registry.get(field.related_model)`; sole production caller `filter_for_lookup`
(generation wire-shape). (B)
`django_strawberry_framework/filters/sets.py::FilterSet._target_type_for_related_filter`
(RelatedFilter): DEFINITION, branch-driven; owner arm
`child_filterset._owner_definition.origin`, fallback
`registry.get(child Meta.model)`; production callers `_branch_visibility_seed`
(request `get_queryset` scoping) + finalizer subpass-2.5 audit (build-time
refusal). Owner map
`django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for`:
DEFINITION with four output contracts across callers (A answers a type, base.py
`resolve_globalid_target_definition` a terminal definition over a multi-hop
chain, walker `_resolve_relation_target` a pair, finalizer agreement a bool).
Bound reader `django_strawberry_framework/utils/permissions.py::set_bound_type`:
DEFINITION (None-defaulting, no fallback); consumers orders `_scoped_hops` x2 +
`_walk_undeclared_hops`. Orders
`django_strawberry_framework/orders/sets.py::OrderSet._scoped_hops`: DEFINITION
(per-hop scoping types; declared hop answers its target set's bound type,
re-entry the walking set's bound type, else `relation_target_type`). Hop helper
`django_strawberry_framework/utils/querysets.py::relation_target_type` (+
`relation_visibility_type`, `relation_path_visibility_types`): DEFINITION
(re-entry-aware hop type). Own-PK check, GlobalID walk, relay decode
(wire-driven, no owner possible), finalizer bind axes, cascade
(`permissions.py` edge walk), unplanned-relation recheck
(`types/resolvers.py`), finalizer shape/pending checks: each its own contract,
no binding at its layer. f59 `relation_identity_column` family: adjacent
DEFINITION answering a column (`ConcreteField`), not a type.

`.origin` census (own grep): 1 definition (the dataclass field) + consumer
reads; same-spelled non-members excluded (`FilterProvenance.origin`,
declared-record `origin`). `registry.get` census: every fallback composes it by
name (A, B, map, hop helper, walker fallback, model-only readers).

Challenges (own counts): slot rename / `.origin` shape moves 1 definition +
N consumers (an A+B merge relieves 2 readers to 1, obligation stands): count
1. Registry precedence moves inside `registry.get`: A/B move 0, count 1. New
axis (field-binding override / child multi-binding / new hop kind) moves A /
B / `_scoped_hops` alone: count 1 each. Observability: A bound==unbound on the
production call shape (owner map keys the target model only, same
`registry.get` key as the fallback; divergence needs a disagreeing synthetic
field, which the pinned oracle constructs deliberately), B bound!=unbound
(child binding answers the secondary): split observed, not one rule.

Owner I would choose: no consolidation. A stays at `FilterSet` (generation),
B at `FilterSet` (branch scoping), the map at `DjangoTypeDefinition`, the hop
helper at `utils/querysets.py`, the bound reader at `utils/permissions.py`.
Merging A+B needs a mode flag over disjoint inputs, fallbacks, None semantics
and callers: machinery, barred. Deleting A's owner arm falsifies spec-027 D4
consultation prose + the pinned owner-path oracle: keep, benign.

### Reconciliation (after opening `## Findings`)

F1 CONCUR: same six axes. Mechanism emphasis differs (W1: same field object;
W2: same `registry.get` key — the map keys the target model only); both true,
spec-027:476 pins the invariance and oracle :5420 pins the arm with a
deliberately disagreeing synthetic field. Trigger concur.
F2 CONCUR + one strengthening difference: a fourth split (isinstance gate vs
None-check) beyond W1's three; reject holds a fortiori. J1/J2 + FF-P4 exist in
plan rows. Trigger concur.
F3 CONCUR: bodies verified for cascade, resolver recheck, finalizer shape,
relay decode, walker pair, base.py multi-hop chain; 036 D11 + 039
related-primary pins verified (primary-resolution text spans D7/D8; substance
holds). Axis-2 prose is projection: concur.
F4 CONCUR: `_scoped_hops` read in full; spec-028 D8s4 + D6(b) verified; zero
type reads in orders generation verified by grep (0 hits); oracle lines
2842/2895 name the declared/re-entry tests, both green in W2's run. No defect,
no maintainer route: concur.
F5 CONCUR. Part-supersede RULING: correct per the drift rule — folder-filters
rows verified run 13 (ticks stand); the bundling refinement is recorded here
as the homing-pass finding; row stays shut; Worker-0 homing at closeout.
Zero-edit confirmed, folder artifact untouched.
Defects CONCUR (none; I1 benign): deleting A's arm would break oracle :5420
and falsify spec-027:490, so principle-11 deletion is considered and rejected.
No new (Worker-2) defects. Pending execution CONCUR (none); cells inapplicable
SOUND (pure derivation over `_meta` + registry + bindings).

### W2 execution evidence

Probe re-ran green (all P-lines: P1/P7, P2/P8, P3, P4, P5, P6). Freshness
12/12 identical (sets befa6d92, orders/sets 79c369b3, definition cde8437f,
finalizer 2dbe6efc, relay 3b4447ae, permissions dbb8f602, querysets 1b0cf162,
walker 02752d50, base 82c153fc, f-test_sets ed3065ac, o-test_sets b0bfb16e,
probe dc911755). Oracles: natural 7 pins 7/7 green; wider neighborhood 13/13
green (5 filters + 8 orders incl. applied twins). Artifact citations 8/8
resolve; trailing-commas 0 violations (both item files excluded populations).
Ruff: no .py in scope — zero-edit, probe is ignored scratch — nothing to check.
Tree-wide basedpyright/truthful-reads not re-run (no tracked .py in scope;
W1-attested green; unaffected by a zero-edit item).

### W2-carried record corrections (verdict-neutral)

OB-W2-1: W1's "7 node ids → 10 passed" is not reproducibly cited (placeholder,
no ids); natural pins give 7/7. Pins the verdict needs are green either way.
OB-W2-2: enumeration counts 30 vs W2's 41 code reads (37 dotted + 4
getattr-string; 14 prose + same-spelled non-members excluded). The 11 W1
leaves ungrouped — inspect x7 (introspection/display), definition self-reads
x3 (own field), optimizer root x1 (`extension.py:1223`, return-type root) —
each verified excludable by body read (display, self-read, plan-root
contracts; no branch-target axis moves them). No hidden consolidation. C2's
"12 readers" subgroup is not reconstructible; its conclusion (count 1) holds
under any count.

### Verdict

Verified. Zero-edit confirmed (no tracked diff; artifact untracked, probe
ignored). Every rejection carries contract difference + trigger; matrix sound
on all six axes; pins hold; no defects.
