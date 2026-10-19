# DRY review: `composite-pk-detection-twins`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Two spellings of "model has composite pk", opposite postures:

- `utils/relations.py:885` `has_composite_pk(model) -> bool` —
`len(pk_fields) > 1` with a `None` fallback. Sole production
caller: the FK-id-elision stamp
(`optimizer/field_meta.py:377`). Its "Single-sited here"
docstring scopes itself to the stamp's two readers
(registered types + the walker's fallback map), never the
gate below.
- `types/relay.py:194` `_check_composite_pk_for_relay_node` —
`isinstance(model._meta.pk, CompositePrimaryKey)`
early-return, then the explicit-`NodeID` escape hatch, else
`ConfigurationError`. Sole production caller: Phase 2.5
(`types/finalizer.py:988`). Spec-015 pins the spelling
("Detection is `isinstance(...)`").

Owner state: the predicate's detection core is behavior-equal
WT vs HEAD (the concurrent rewrite removed only the
`BaseException` wrapper); signature unchanged. Relations is
read-only for this item; the gate's docstring + detection
lines are byte-identical WT vs HEAD (sole in-function
foreign hunk: the raise-line truth migration).

## Verification

### Matrix

1. Cross-flavor: no third flavor mirrors detection; the
filter/order pk reads are membership/column, classified
under Findings.
2. Sync/async: both are sync pure `_meta` reads. No twin.
3. Derived-twice: the question itself — one Django fact, two
API spellings, proven equivalent (Challenges); the lateral
column probe and the membership readers are distinct
contracts, not copies.
4. Round-trip: detection is one-way; no encode/decode pair.
5. Other media: both verdicts pinned both sides (Findings);
spec-015:239 pins the gate spelling; both docstrings state
their rule; the shape probe is retained evidence.
6. Omission: lateral downgrades via its column probe; keyset
and filters read pk members width-agnostically and owe no
detection. No contract source demands detection elsewhere.

### Challenges

- C1 (Django retires one API): someone else's rule (DRY.md
exclusion) — and each such change moves ONE family:
`pk_fields` churn reaches the predicate + the two
membership readers, never the gate; `CompositePrimaryKey`
churn reaches the gate, never the predicate. Count 1.
- C2 (our composite notion refines): the notion IS Django's;
no refinement exists (1-field composite refused by the
constructor on floor and ceiling; no third pk shape).
Implausible.
- C3 (elision/gate skew): RULED OUT — `unnest` + `>= 2`
identical in Django 5.2.16 and 6.1.2; the 8-shape probe
agrees with Django's own `is_composite_pk` on every row;
the sole divergence is surgically inconsistent `_meta`,
production-unreachable.
- Security clause (argued, rejected): elision skips a fetch
on visibility-admitted rows (a wrong id string, never
foreign rows); the gate is scope enforcement with its own
escape hatch. Neither guards the trust boundary; 0 of 2
feed visibility/scoping.

## Findings

### F1: composite-pk detection — REJECTED (predicate vs gate)

- Contract: detection answers Django-composite, with no
our-variation axis. Postures differ by design: a total
bool for a stamp conjunction vs a raising scope gate with
a remediation hatch.
- Sites: the two definitions above (rejected as one rule).
Consumers: the stamp, the finalizer. Oracles: four
committed tests (both verdicts both sides) + the probe.
Projections: two docstrings, spec-015:239, two glossary
bodies.
- Challenges: C1–C3 above; no plausible our-change moves
two sites. Count 1 → independence.
- Owner/lifetime: none; stays split. No stored derivation.
Durable-home clause OWED at the predicate docstring once
the relations rewrite lands (closeout rides it).
- Migration: none (zero-edit). Index row for Worker-0:
`composite-pk-detection-twins`, owner none, files
relations/relay/finalizer/field_meta, `rejected`.
- Shrinkage: net 0; no machinery (nothing added).
- Distinct: the postures; the lateral column probe
(join-column availability + value read, fail-safe
downgrade); the membership readers (`field_meta.py:417`,
`filters/base.py:324` — which-members, width-agnostic);
prose citations (`relay.py:204`, `types/base.py:1233`);
Django's own `is_composite_pk` (someone else's rule).
- Proof: the shape probe, execution-verified (command in
`## What shrinks`); its stale-state row observes the
split, so a non-discriminating comparator fails it; the
committed oracles pin both verdicts both sides. No new
tests (zero-edit).
- Negative control: none (rejection; the split threatens
no bypass — both total on real `_meta`).
- Coupling: none. The relations rewrite is fenced
read-only ground, not coupling.
- Freshness: HEAD `c37a08a0`, baseline `bd955be4`; WT
blobs relations `b0cc6c33`, relay `3b4447ae`,
finalizer `2dbe6efc`, field_meta `478419b7`, lateral
`995f1aa2`, filters/base `82c153fc`; gate detection
HEAD-identical; whole-repo
`CompositePrimaryKey|pk_fields|has_composite_pk` census
classified, no fourth detection; contract sources:
Django 5.2.16 + 6.1.2 `options.py`/`composite.py`,
spec-015, four oracles.
- Triggers: T1 a production shape where the spellings
disagree (Django permits 1-field composite, or
`pk_fields` gains non-pk members) → compose on the
survivor; T2 our notion diverges from Django's → the
refinement lands as one predicate both compose; T3 a
third DETECTION consumer appears (membership/column
reads excluded) → re-count; T4 Django retires
`pk_fields` or `CompositePrimaryKey` → the surviving
family re-counts; T5 the relations rewrite touches the
predicate or settles → re-verify + home the clause.

## Defects

None.

## Pending execution

None.

## Judgment

One Django fact, two API spellings, proven equivalent on
every production shape; postures intentionally separate;
no bar met (counts 1, no drift, outside the trust
boundary). Zero edits.

## Independent verification (Worker-2)

### Own trace (pre-findings)

Sites + roles (own census, package-wide): `relations.py:885`
`has_composite_pk` (definition; 1 production caller
`field_meta.py:377`, the elision stamp; oracles
`test_relations.py:979`, `test_field_meta.py:464`) vs
`relay.py:194` `_check_composite_pk_for_relay_node`
(definition: `isinstance` early-return + `NodeID` escape +
raise; 1 caller `finalizer.py:988`; oracles
`test_relay_interfaces.py:237`/:261/chain/:1616).
Neighbors with other contracts: `lateral_fetch.py:1095`
(join-column VALUE read, fail-safe downgrade),
`filters/base.py:324` + `field_meta.py:417` (`pk_fields`
membership, width-agnostic), prose cites only.
Django's own `is_composite_pk`: zero package hits.

Mechanism equivalence, re-derived from Django source both
ends + execution: `pk_fields = unnest([pk])`
(6.1.2 `options.py:993`; floor wheel 5.2.16 `:984`,
identical); `unnest` expands `CompositePrimaryKey` to
`.fields` else `[pk]` (identical both ends);
constructor refuses <2 members (`composite.py:61` floor,
`:61` ceiling); `contribute_to_class` sets `_meta.pk`
(identical). So `len(pk_fields)>1` ⟺ `isinstance(pk,
CompositePrimaryKey)` on every Django-constructed
`_meta`. The predicate's `None` fallback is dead on the
floor (5.2.16 HAS `pk_fields`). Executed battery, ceiling
(exit 0, 14/14):
`PYTHONPATH=".:examples/fakeshop"
DJANGO_SETTINGS_MODULE=config.test_settings uv run python
docs/dry/temp-tests/composite-pk-detection-twins-verify-1/probe_equivalence.py`
— agreement on single/composite/proxy-x2/MTI-x2/text-pk/
uuid-pk/MTI-under-composite(definable, both False);
1-field refused (`ValueError`); stale control (patched
`pk`, untouched cached `pk_fields`) observes
predicate-False/gate-True, proving discrimination;
post-restore agreement. Postures differ by design: total
bool for a stamp conjunction (fail-closed data plane) vs
raising scope gate with remediation hatch (finalization
refusal). No owner; stays split. Pre-findings verdict:
reject, below bar.

Challenges (own): X1 Django retires `pk_fields` — moves
predicate + 2 membership readers, never the gate; someone
else's rule (excluded), count 1. X2 composite notion
refines — notion IS Django's (constructor floor+ceiling);
each site a single expression, no real logic. X3 our
elision refines (tuple support) — stamp only. X4 our relay
refines (composite `NodeID`) — gate only. X5 skew — each
moves alone. No 2-definition real-logic change.

Disclosure: `muse.search` output exposed artifact lines
before I opened `## Findings`; every row above is
re-derived from source + my own executed probe (written
and run before the artifact read).

### Reconciliation

Agreements: sites callers oracles neighbors (exact);
floor+ceiling source identity (line pins match);
equivalence incl. the stale-row split (my battery
converges with the retained probe on all 8 overlap
shapes); postures; gate detection HEAD-identical with the
sole in-function foreign hunk the raise-line truth
migration (own diff); all 6 freshness blobs; zero-edit
(baseline→WT over the family = empty; only plan +31).
One precision nit, verdict-neutral: W2-1 — "behavior-equal
WT vs HEAD" (System trace) is loose: the concurrent
rewrite removed the `BaseException`→`ConfigurationError`
translation, so hostile-input behavior changed (typed
refusal → raw escape); the detection-core expression is
identical and every real-`_meta` verdict unchanged.
Concurrent-work territory, fenced, verdict-neutral.

### Consolidation search (independent)

Migration constructed: gate replaces the `isinstance`
line with `has_composite_pk(model)` (+ import, possibly
dropping its own). Legs, each with its flip trigger: (1)
Change obligation — fails: X1–X5 above, no plausible
our-change moves 2 real-logic sites. Flip: a refinement
of OUR notion both spellings must track. (2)
Security/data-exposure — fails: elision wrongness serves
a wrong id string on visibility-admitted rows (the stub
carries only the FK value already on the parent row;
alias set from the router — corruption, never foreign
rows); gate wrongness mints undecodable GlobalIDs → null
via the existence family (breakage, not exposure);
0 of 2 feed visibility/scoping/auth/routing. Flip: a
construction where wrong elision serves policy-hidden
rows (none — the stub fetches no row). (3) Drift —
fails: proven equivalent; the stale split is
production-unreachable. Flip: T1. (4) P11 — fails:
composition deletes nothing (both keep live callers) and
adds a relay→relations edge (acyclic — relations imports
only exceptions+truth — but responsibility-free) while
forcing 3 oracle edits (the gate oracles patch `pk`
only; a composed gate goes silent unless they also patch
`pk_fields` — rewriting oracles to the implementation)
plus a spec-015:239 rewrite. Reverse migration
(predicate composes `is_composite_pk`) fails likewise
(read-only fence, zero obligation change). No above-bar
candidate exists; below-bar concurrence stands on these
legs alone, not on the D precedent.

### Checklist

Matrix judged on the real surface: 1 third-flavor sweep
reproduced (`CompositePrimaryKey` code use only relay;
`pk_fields` exactly 3 sites; `composite` remainder prose
+ the lateral value probe; `is_composite_pk` zero hits) —
no third detection. 2 sync-pure both, agree. 3 lateral +
membership readers are distinct contracts (value /
which-members), agree. 4 one-way, agree. 5 oracles read
in full (4 pk-patch sites `:256`/`:279`/`:1310`/`:1632`
pin `isinstance`); W1 probe re-ran exit 0, output as
claimed; prose census stragglers confirmed
(`finalizer.py:21`, `predicates.py:94`). 6 lateral
downgrades fail-safe; no contract source demands
detection elsewhere, agree. Triggers T1–T5 all firable
with concrete firings; T3's membership/column exclusion
blocks false trips. Pending `None` judged correct (proof
execution-verified twice). Freshness: HEAD `c37a08a0`
confirmed, all 6 blobs re-hashed match, WT==BASE on all
6. Coupling: none (zero-edit). AGENTS.md prose: empty
diff, vacuous; `path:NN` allowed in `dry-*.md`. Shape:
body 144 ≤ 150, Judgment 4 ≤ 6, trace 24 ≤ ~25, Run
line present, 10 link groups present. Ruff: zero touched
`.py` paths (no staged/unstaged item hunks, no new
non-ignored `.py` — the listed untracked `.py` files are
concurrent work), nothing to run. Fence honored
(relations untouched). Durable-home clause OWED via T5
(closeout rides the rewrite) judged acceptable,
non-blocking — the 376-line HEAD↔WT relations delta
confirms the fence is real. Defects: none (W2).

## What shrinks

Net package change: zero lines (rejection). What was
counted and where it stays:

- The two detection spellings stay split: `relations.py:885`
(bool, elision stamp) and `types/relay.py:194` (raising
Phase-2.5 gate with the explicit-`NodeID` hatch). Each is
one expression over the same `_meta` pair Django keeps
consistent (`pk_fields = unnest([pk])`, composite members
`>= 2` by constructor) — identical source in the floor
wheel (Django 5.2.16 `options.py:984`, `composite.py:61`)
and the ceiling venv (6.1.2). A shared predicate would
add an import edge into a file under active rewrite for
zero behavior change and zero removed obligation.
- Whole-repo `CompositePrimaryKey|pk_fields|has_composite_pk`
census, every hit classified: the predicate define + use;
the gate define + call; the lateral column probe
(`lateral_fetch.py:1095` — join-column availability that
also reads the value; composing the predicate keeps the
column read and narrows the contract, so it stays);
the membership readers (`field_meta.py:417`,
`filters/base.py:324` — which-members, correct at any
width, never a cardinality question); prose citations
(`relay.py:204`, `types/base.py:1233`, `finalizer.py:21`,
`field_meta.py:411`, lateral/predicates docstrings);
oracles (`test_relations.py:979`,
`test_field_meta.py:464`, `test_relay_interfaces.py:237`
/ `:261` / chain `:1310` / `:1616`); shared fixtures
(`tests/_relation_fixtures.py`); spec + glossary + build
prose. No fourth detection exists.
- Considered compositions, each failing the bar: gate
composes the predicate (behavior-identical on real
`_meta`, single-expression pair, non-security, no drift —
the pk-segment-name-inlines precedent, verified this run);
predicate composes Django's `is_composite_pk`
(owner-internal, read-only file, zero obligation change);
lateral probe composes the predicate (contract narrowing,
above). The three committed gate oracles pin `isinstance`
via patched-`pk`/stale-`pk_fields` state; they stay valid
for the gate as written and move in the same change only
if T1 ever lands a composition.
- Executed shape probe (exit 0, Django 6.1.2):
`PYTHONPATH=<root>:examples/fakeshop uv run python
docs/dry/temp-tests/composite-pk-detection-twins/probe_shapes.py`.
All three columns (predicate, gate spelling, Django
`is_composite_pk`) agree on single, composite,
proxy-of-single, proxy-of-composite, MTI parent, MTI
child, concrete-of-abstract, and MTI-under-composite
(child pk is the single parent link); 1-field composite
refused by Django (`ValueError`); the elision stamp is
True on a real FK to a single pk; the gate raises the
documented `ConfigurationError` on a real composite type
and passes a single-pk type. The closing stale-state row
(patched `pk`, untouched `pk_fields`) observes
predicate-False/gate-True: the production-unreachable
divergence, and the proof the probe discriminates.
- Oracle inventory (all standing, none added): predicate
direct (`test_has_composite_pk_cardinality`: single
False, composite True); stamp (`test_fk_id_elision_edge_cases`:
eligible / non-pk-`to_field` / composite-duck-FK False);
gate raise (`test_relay_node_with_composite_pk_raises`,
chain `:1310`, direct-inheritance `:1616`); gate accept
(`test_composite_pk_with_explicit_node_id_annotation_is_accepted`).
- Fence record: `utils/relations.py` untouched (read-only;
WT blob `b0cc6c33`, predicate behavior verified by the
probe at WT bytes); `types/relay.py` untouched — detection
lines HEAD-identical, sole in-function foreign hunk is the
raise-line truth migration, specified here so a future
composition ports cleanly beside it. No live source
edited; pool-full submission, nothing to port.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
