# DRY review: `prefetch-child-build-seam`

Status: verified
Run: 0.0.15 2026-10-01-12

## System trace

The prefetch-child build seam: one builder answers the queryset that goes
inside every package-generated `Prefetch`, with the seal chosen per call
site. `optimizer/walker.py::_build_child_queryset` (walker.py:547) builds
the base (related-model seed via `utils/querysets.py::base_queryset` plus
the target's visibility hook through
`utils/querysets.py::apply_type_visibility_sync` under a `policy`
parameter defaulting to `_LIST_RELATION_CHILD_POLICY`);
`optimizer/walker.py::_build_connection_child_queryset` (walker.py:640) is
the nested-connection seam fixing `policy=_PREFETCH_CHILD_POLICY`;
`optimizer/walker.py::_build_prefetch_child_queryset` (walker.py:1177) is
the list-path wrapper (build base, then apply);
`optimizer/walker.py::_build_prefetch_child_queryset_from_base`
(walker.py:1214) walks the child selections into a child plan, absorbs it,
and applies it onto the already-built base;
`optimizer/walker.py::_absorb_child_plan` (walker.py:1479) delegates the
absorb to `optimizer/plans.py::OptimizationPlan.merge_metadata_from`.
The nested planner (`optimizer/nested_planner.py::plan_connection_relation`,
nested_planner.py:1090) reaches the builder and the applier through the two
injected callables the walker's `_plan_connection_relation` binds
(walker.py:1854-1855), classifying the base between the two calls with
`optimizer/nested_fetch.py::unwindowable_child_queryset_reason`
(nested_planner.py:1301).

Connected behavior examined at current bytes: the seal-policy records
(`utils/querysets.py::_PREFETCH_CHILD_POLICY` /
`_LIST_RELATION_CHILD_POLICY`, querysets.py:2985/2998, owned by verified
`sealed-execution-queryset`); the runner's captured-model seam
(`utils/querysets.py::_captured_model`, querysets.py:4235) and source seal
(`_prepared_visibility_source`, querysets.py:4270); the plan-merge pair
(`optimizer/plans.py::merge_from` / `merge_metadata_from`, plans.py:341/372);
the unwindowable gate and its three consumers; the consumer-prefetch seal
(`utils/querysets.py::_sealed_prefetch_related_lookups`, second policy
consumer at querysets.py:2701); the strategy `Prefetch` wrap
(`optimizer/nested_fetch.py:351`); the hint rebase pair
(walker.py:1406/1447, owned by open `optimizer-hint-dispatch`); the
filterset child-visibility derivation
(`filters/sets.py::_derive_related_visibility_querysets_sync`,
filters/sets.py:2912); the strict model read
(`list_field.py::_model_from_definition`, list_field.py:1171); and every
`getattr(*definition, "model", None)` spelling package-wide (4 hits, 2 in
family). The nominating File `optimizer/walker.py` F-W3 sections were read
for orientation only; every count below is re-derived at current bytes.

## Verification

### Matrix

1. Cross-flavor: swept the whole package (120 files) for a second
   prefetch-child builder. `Prefetch(` constructions: the generated list
   child (walker.py:1139, in family), the hint rebase pair (consumer
   `Prefetch` adaptation, open `optimizer-hint-dispatch`), the strategy
   wrap (nested_fetch.py:351, consumes the already-built child, verified
   `nested-fetch-strategy-seam`). No third builder. Resolver-surface
   `apply_type_visibility_sync` callers (connection, list_field,
   permissions, mutations, types, filters) seal their own seeds; none
   builds a generated child or applies a child plan. Discharged.
2. Sync/async: zero `async def` / `await` in both targets (grep count 0/0).
   Plan time is sync-only by construction; the async twin is the runner
   (`apply_type_visibility_async`), owned by verified
   `sealed-execution-queryset`; the `SyncMisuseError` recourse prose on the
   builder is intact. No twin. Discharged.
3. Derived knowledge: the seal-validation model was spelled identically at
   both child call sites (`target_model=getattr(target_definition,
   "model", None)`); consolidated into the builder (F2). The
   `has_custom_qs` verdict derivation was already single-owned
   (`_target_has_custom_get_queryset`, composed directly on the list path
   and via injection on the nested path). Strict/lenient model reads
   elsewhere excluded (R5). Discharged.
4. Round-trip: no encode/decode pair in the seam; build, classify, apply,
   absorb is a pipeline, not a round trip. `merge_from` (full result
   commit, 2 consumers: walker.py:1857, nested_planner.py:1480) vs
   `merge_metadata_from` (metadata-only child absorb, 2 consumers plus the
   internal `merge_from` call) are distinct operations, not inverses.
   Discharged.
5. Other media: oracles move with the contract (the seam test's two calls
   updated, verdicts unchanged; one new oracle added, mutant-proved).
   Prose projections citing the builder (spec-045 Decision 5, the sealed
   and alias family artifacts, two live-tier docstrings) describe behavior
   this change preserves. No oracle reads from the owner. Discharged.
6. Omission: the seam's family is {plain list path, nested-connection
   path}; both compose the builder (wrapper default seal / injected seam
   seal). The hint path plans consumer-supplied `Prefetch` objects
   (different population, open `optimizer-hint-dispatch`); root pipelines
   build root querysets, not prefetch children. No member lacks the seam.
   Discharged.

### Enumeration

Instrument: full read of both indexed files (walker.py 1852 lines,
nested_planner.py 1521 lines) plus package-wide grep censuses over all 120
package files for the mechanism vocabulary (`_build_child_queryset`,
`_build_connection_child_queryset`, `_build_prefetch_child_queryset`,
`_absorb_child_plan`, `merge_metadata_from`, `Prefetch(`,
`apply_type_visibility_sync(`, `_LIST_RELATION_CHILD_POLICY` /
`_PREFETCH_CHILD_POLICY`, `unwindowable_child_queryset_reason(`,
`getattr(*definition, "model", None)`, `target_model`). Every nominated
member lands in F1; the model-read pair lands in F2; every other census
hit lands in R1-R5 or a cited verified/open family. No member unassigned.

### Challenges

- C1 (third seal): a third child path needing a third seal adds one
  call-site argument (plus the policy record, owned by
  `sealed-execution-queryset`, only if new flags are needed). Count 1.
- C2 (new base-build step): a new seed/visibility step lands in
  `_build_child_queryset` once; both paths inherit it. Count 1.
- C3 (new child-plan application step): lands in
  `_build_prefetch_child_queryset_from_base` once; the list wrapper and
  the injected nested call inherit it. Count 1.
- C4 (new absorb field): lands in `merge_metadata_from` once (plus its
  field-inventory assertion); the wrapper and the planner's direct call
  inherit it. Count 1. (Static-reviewed: no behavior change proposed.)
- C5 (seal-validation-subject derivation change): before, the
  `getattr(target_definition, "model", None)` read moved at 2 sites
  (walker.py:1196, nested_planner.py:1299). Count 2 -> 1 after F2.
  Execution-verified (P1, P2).
- C6 (None-tolerance change): same 2 sites before (both rely on the
  `getattr` default for a `None` definition on the unregistered-model
  fallback path). Count 2 -> 1 after F2. Same proofs as C5.
- P1: focused run `uv run pytest -n0 --no-cov -q
  tests/optimizer/test_walker.py -k
  "child_builder_spends_the_passed_definition or
  connection_child_seam_still_admits or
  refuses_sliced_hook_result_for_plain_list"` -> 3 passed
  (execution-verified, shared tree).
- P2: failability mutant in the workspace copy (builder's `model=`
  replaced with `model=None`, i.e. the passed definition ignored):
  the new oracle FAILS with the table defect (`requires a QuerySet over
  Category's concrete table; got a Item queryset`), the pre-existing seam
  oracle still passes (1 failed, 1 passed). Run
  dry-20261002T042003-85af2a at dry/childseam-f56/consolidate, slot-2,
  cell default (execution-verified; copy re-synced clean afterwards,
  dry-20261002T042017-380c8a / dry-20261002T042019-d4e3d4).

## Findings

### F1 - one builder, two call-site-chosen seals (CONFIRMED single-owned)

Contract: the queryset-boundary abstraction. The base child queryset is
built once (`_build_child_queryset`: related-model seed, optional
visibility hook under a call-site seal); the child optimization plan is
applied onto an already-built base
(`_build_prefetch_child_queryset_from_base`: walk, connector columns,
absorb, apply); the list path composes both through
`_build_prefetch_child_queryset`, the nested path through the injected
seam plus its own classification gate between the two calls. Variation
axes: seal per path (slice licence only where a gate answers for it),
base-build steps, child-plan application steps.

Sites + roles: `_build_child_queryset` (definition);
`_build_connection_child_queryset` (call-site seal choice, composes the
builder by name); `_build_prefetch_child_queryset` (list-path
composition, single caller at walker.py:1124);
`_build_prefetch_child_queryset_from_base` (definition, 2 callers: the
wrapper + the planner's injected call at nested_planner.py:1312);
`plan_connection_relation` (injecting consumer; policy-agnostic - zero
seal-policy references); the seal-policy records (definitions owned by
verified `sealed-execution-queryset`, passed by name only); the
unwindowable gate (definition owned by verified
`unwindowable-child-queryset-classification`, 3 consumers by name);
`_absorb_child_plan` (one-caller pass-through to `merge_metadata_from`,
kept - see R2).

Challenges: C1/C2/C3/C4, each count 1.

Owner + lifetime (principle 7): `optimizer/walker.py`. The walker owns
plan construction and both seals' call-site premises are stated on its
members; the planner cannot own the seam (it must stay importable from
the walker without a cycle, hence injection). Lifetime: plan-local
`OptimizationPlan` pairs, absorbed before return, never cached mid-build
(the child non-cacheability poisons the parent through the absorb).

Migration: none - the shape stands as nominated.

Distinct behavior: the planner's intermediate classification (it must see
the base before child-plan application, so the nested path cannot use the
list wrapper); the wrapper's default seal; the seam's fixed seal. Each
recorded on its member's docstring.

Behavioral proof: static-reviewed (no behavior change proposed; counts
over closed, grep-enumerated populations).

Structural gate: none owed - no consolidation on this axis, and each
member already has exactly one spelling (censuses above).

Coupling: none.

Freshness: walker.py HEAD 57a27b4a / baseline b71db9e0 / WT 9d7a07bd;
nested_planner.py HEAD 8c3a45f5 / baseline b6ff0a0e / WT 748ed33a;
querysets.py WT 6d471bd7 / HEAD adc74b64; plans.py WT 2e4332cc / HEAD
a584c63f; nested_fetch.py WT 9f5d8914 / HEAD 3bd9a5b2; 120-file package
censuses as listed under Enumeration. Baseline is ITEM_BASELINE
20f44bae (= pre-edit WT for both targets); HEAD dd0b6691 throughout.

### F2 - seal-validation-subject derivation (CONFIRMED count-2, consolidated 2 -> 1)

Contract: the model the child visibility seals validate against is the
captured child definition's model, read once per child build. Both seals
of one visibility call (source + result) take the same value, so they
cannot validate against two tables.

Sites + roles: before, two definitions of the read -
walker.py:1196 (`target_model=getattr(target_definition, "model", None)`
in `_build_prefetch_child_queryset`) and nested_planner.py:1299 (the
identical expression feeding the injected seam). After: one definition
in `_build_child_queryset` (`model=getattr(target_definition, "model",
None)`); both call sites pass `target_definition=` through. Consumers
of the consolidated seam: the list wrapper, the injected nested call,
and the two direct-test callers. `_captured_model` (verified
`sealed-execution-queryset`) owns the `None` fallback the read feeds,
not the read itself.

Challenges: C5 count 2 -> 1; C6 count 2 -> 1.

Owner + lifetime (principle 7): the builder
(`optimizer/walker.py::_build_child_queryset`), by derive-where-consumed:
the builder is the read's only consumer, while the sibling
`has_custom_qs` verdict stays caller-derived because both callers also
spend it on their cacheable flips (walker.py:1107-1109,
nested_planner.py:1184/1310-1311). No stored derivation (pure call-time
read, not cached).

Migration: `_build_child_queryset` and `_build_connection_child_queryset`
take `target_definition=` instead of `target_model=`; the wrapper and
the planner pass the definition they already hold; the seam test's two
calls updated to the new keyword (verdicts unchanged).

Distinct behavior: none - the identical expression with identical
None-tolerance moved from two callers into their sole callee; no await
or I/O sits between the old and new read points, and the read observes
immutable registration metadata.

Behavioral proof: execution-verified. P1 pins both seals' behavior
through the new keyword (3/3 green); P2 proves the new oracle rejects
the wrong result (a builder ignoring the passed definition fails with
the table defect naming the class-carried table, while the pre-existing
oracle passes the mutant - which is why the new oracle was owed).
Principle-8 equivalence holds by construction (same expression, same
points of observation up to unobservable metadata-read timing).

Structural gate: the new oracle IS the gate - it fails for any
derivation that stops spending the passed definition, whatever the
spelling (mutant-proved). No census test owed: the `target_model`
parameter no longer exists, so a second hand derivation has no seam to
feed and bypass is unspellable; a spelling census would be a bespoke
existence test per helper.

Coupling: none (lands standalone; D1 below is untouched by it).

### R1 - planner-passes-policy alternative (rejected)

The seam could be deleted with the planner calling `_build_child_queryset`
directly under `policy=_PREFETCH_CHILD_POLICY`. Rejected: the seal choice
would move seal-policy vocabulary into the planner, which today holds
zero policy references (census E) and takes the seam as a fixed-policy
callable; the licence and the premise it rests on stay described once,
walker-side. Contract difference: fixed seal chosen with its premise
prose (walker) vs policy-agnostic injection consumer (planner).
Durable home: the seam docstring carries the trigger (landed in this
change) - a child path whose seal needs planner-local state moves the
choice into the planner with a `policy` argument.

### R2 - absorb wrapper vs direct merge (single-owned; D1 filed)

`_absorb_child_plan` (one caller, pure delegation to
`merge_metadata_from`) beside the planner's direct
`plan.merge_metadata_from(sub_plan)` (nested_planner.py:1503) is one
definition at `optimizer/plans.py::merge_metadata_from`, not two: an
absorb-semantics change touches the owner once either way. Deleting the
wrapper would relieve no change obligation, so it is kept; routing the
planner through an injected wrapper would add a ninth injection callable
for a one-line delegation (machinery). The wrapper's "no separate line"
rationale is already falsified by the planner site - filed as D1, not
fixed here. Trigger: the absorb gains logic beyond delegation - then the
planner site routes through the (injected) wrapper or the wrapper dies;
specified home the wrapper docstring / `merge_metadata_from`, unlanded
while D1 owns that prose.

### R3 - third-module model helper (rejected as machinery)

A shared `_target_model(definition)` helper would need a third-module
home (the planner cannot import the walker - cycle) plus threading to
both call sites, all to name one `getattr` with a default. F2 moves the
read to its sole consumer instead: no helper, no flags, no new edge.
Trigger: a third consumer outside the builder's reach.

### R4 - third-site exclusions (distinct contracts)

- `utils/querysets.py::_sealed_prefetch_related_lookups`
  (querysets.py:2701): seals CONSUMER-supplied `Prefetch` children under
  `_PREFETCH_CHILD_POLICY`. Seal-only on foreign values, never builds a
  base or applies a child plan. Trigger: generated children routed
  through it.
- `optimizer/nested_fetch.py:351`: wraps the already-built
  `request.child_queryset` in the windowed `Prefetch`. Pure consumer.
  Trigger: none (consumption is the shape).
- `filters/sets.py:2912`: child-filterset visibility derivation feeding
  `apply_sync` (subquery-RHS downstream, unsealed return per verified
  `child-derivation-unsealed`). No `Prefetch`, no child plan. Trigger: a
  filterset derivation feeding a generated prefetch.
- Resolver-surface `apply_type_visibility_sync` callers (connection,
  list_field, permissions, mutations, types): seal their own seeds at
  resolve time. Trigger: a surface building plan-time prefetch children.

### R5 - strict model reads (rejected; distinct None-contract)

`list_field.py::_model_from_definition` reads the model off a definition
too, but strictly: non-`None` definition in, validated model out, loud
`ConfigurationError` otherwise, once per field at construction. The seam
read is None-tolerant by contract (the unregistered-model fallback
passes `None` through to the runner's class read) at request time.
`filters/base.py:875` (identity coercion) and `relay.py:581` (node-stamp
isinstance check) spend their reads on unrelated consumers. Trigger: the
optimizer path adopts strict-validated reads (it cannot while the
fallback passes `None`).

## Defects

- D1 (doc-only): `optimizer/walker.py::_absorb_child_plan` docstring
  claims the absorb is "folded in here - rather than a separate line at
  each absorb site - so a future third site cannot forget it", but
  `optimizer/nested_planner.py:1503` (`plan.merge_metadata_from(sub_plan)`)
  is exactly such a separate line. Owner:
  `optimizer/walker.py::_absorb_child_plan`. Unfixed (method bars defect
  fixes inside items; the F2 consolidation lands standalone and touches
  neither line).

## Pending execution

None. Every proof above executed (P1 shared-tree green, P2 workspace
mutant FAIL-then-green logic proved); no `proof:` entry is owed, and no
`gate:` witness routes nowhere. Full-suite confirmation rides the plan's
final gate.

## Judgment

CONFIRM and landed. The nominated seam stands single-owned (F1, zero-edit
on the shape); the seal-validation-subject derivation hiding inside it
was a genuine count-2 with a silent-divergence hazard on a
visibility-adjacent seam, now one definition at its sole consumer (F2,
+73/-15 with a mutant-proved oracle). One doc-only defect filed (D1).

## Implementation (Worker-1)

Tracked changes (item-scoped diff vs ITEM_BASELINE 20f44bae; HEAD
dd0b6691 unmoved; external-hunk attribution re-verified before each
edit - all dirty hunks outside the touched lines are concurrent
truth-migration / advisory work, none reverted or tidied):

- `django_strawberry_framework/optimizer/walker.py` (+17/-12):
  `_build_child_queryset` takes `target_definition=` and derives the
  seal model once; `_build_connection_child_queryset` threads it; the
  list wrapper passes through; builder docstring records the
  single-derivation rationale; seam docstring gains the R1 trigger
  clause.
- `django_strawberry_framework/optimizer/nested_planner.py` (+1/-1):
  the nested call passes `target_definition=` through.
- `tests/optimizer/test_walker.py` (+55/-2): the seam oracle's two
  calls updated to the new keyword (verdicts unchanged); new
  `test_child_builder_spends_the_passed_definition_not_a_class_reread`
  pins the passed-definition spend with a diverged class-carried
  definition. Package tier: the definition-vs-class divergence it
  guards is unconstructible through a real schema (one object), so no
  live query can express it.
- This artifact (new).

Gates (whole-scope, after final edit): `uv run basedpyright` -> 0
errors, 0 warnings, 0 notes; `uv run python scripts/check_any.py` ->
128 allowed uses at 89 sites (unchanged); `uv run python
scripts/check_truthful_reads.py --check` -> errors 0. `uv run ruff
check --fix` + `uv run ruff format` clean on exactly the three touched
`.py` paths. No new cast / Any / suppression (the moved expression is
byte-identical; the diff adds none).

## Independent verification (Worker-2)

Own trace, fixed from source before opening `## Findings`. (A
repo-wide caller sweep incidentally surfaced a few artifact lines
first; every count below was already derived from source greps, and
my challenge framings differ throughout - no inheritance.)

Sites + roles (mine): `walker.py::_build_child_queryset`
(definition - seed plus sealed visibility under a caller seal);
`walker.py::_build_connection_child_queryset` (call-site seal
choice, injected into the planner); `walker.py::
_build_prefetch_child_queryset` (list-path composition, sole
caller at walker.py:1124); `walker.py::
_build_prefetch_child_queryset_from_base` (definition, 2 callers:
the wrapper plus the planner's injected call);
`walker.py::_absorb_child_plan` (pass-through to
`plans.py::merge_metadata_from`); `nested_planner.py::
plan_connection_relation` (injecting consumer; zero seal-policy
references); the seal records, the runner's captured-model seam,
and the unwindowable gate (definitions owned by verified
families, composed by name); oracles (the seam test's two calls
plus the extension cascade pins as behavior coverage).

Challenges (mine): C1 seed-construction change -> 1 (the
builder); C2 nested-path seal change -> 1 (the seam); C3
wrapper-composition change -> 1 (the wrapper); C4
apply/absorb change -> 1 per owner (the applier, the merge
owner); C5 derivation-expression change -> 2 pre (walker.py:1196
+ nested_planner.py:1299), 1 post; C6 None-tolerance change ->
same 2 pre, 1 post. Owner I would choose: the builder - it is
the read's sole consumer (derive-where-consumed), while the
sibling `has_custom_qs` verdict correctly stays caller-derived
(both callers also spend it on cacheable flips).

Reconciliation: counts, roles, and owner agree with W1 on both
findings; only my C1-C4 framings differ (seed/seal/wrapper/
apply vs third-seal/base/apply/absorb), verdicts identical.
No second body found for any member; no shape change owed (F1);
the 2->1 consolidation targets the right owner (F2).

Rulings on (a)-(m): (a) CONFIRM C1-C4 count 1, no shape change.
(b) CONFIRM 2->1 (byte-identical expression) with None-tolerance
preserved (`None` still falls to `model_for` via
`_captured_model`). (c) CONFIRM principle-8 equivalence, with
two refinements: the old->new delta window holds
`base_queryset()` plus the branch check - sync, no await, no
I/O; the only consumer callback in reach is a custom manager's
`.all()`, which cannot feasibly mutate `definition.model`
(plain dataclass field, single construction site, no mutator);
and the read narrows from unconditional (call-site argument
evaluation) to conditional (inside `if has_custom_qs`) -
unobservable on every feasible shape (real definitions,
`SimpleNamespace` doubles, `None`), since the read has no
side effects. Short-circuit, exception (`getattr`-with-default
never raises), and hook-callback behavior are unchanged. (d)
CONFIRM by re-execution: P2 mutant `model=None` in my copy
fails exactly the new oracle with the table defect naming the
class-carried table, while the pre-existing oracle passes
(carried == passed there) - run dry-20261002T043204-c8c79f,
slot-3, cell default, fresh, shared unmoved; restore
byte-identical. (e) R1 home landed (seam docstring trigger
clause) CONFIRM; R2 unlanded home ACCEPTED per f52 RULING R3
(D1 owns the wrapper prose, so the wrapper docstring cannot
take the clause without either fixing D1 in-item or stacking
truth on a false sentence; the landing site is specified for
D1's repair); R3 machinery rejection sound (de-facto home: the
builder docstring's "only consumer" clause - named here); R4
siblings sound; R4 nested_fetch.py:351 "Trigger: none" cured
below per f52 RULING R1; R5 strict-vs-lenient distinction
sound (de-facto homes: the builder None-contract plus
`_captured_model` - named here). (f) CONFIRM D1 filed-unfixed
and standalone: its lines (the absorb docstring,
nested_planner.py:1503) sit 200+ lines from every item hunk.
(g) The `tests/` tier is CORRECT: carried-vs-passed divergence
is unconstructible through a real schema (type and definition
register atomically), so no live query can express the oracle;
it sits beside the seam oracle it extends. (h) CONFIRM dirt
attribution: since ITEM_BASELINE exactly the 3 item files
changed (plus plan bookkeeping), 8 hunks, all disjoint from
HEAD..baseline predirt (walker 13/228/271/821/1288/1319/1360/
1424, planner 28/643/1488, test file zero-predirt); the
builder-docstring edits overlap the ledger's D1-fix walker
row, hence buildable. (i) CONFIRM the three boundaries
untouched (policy records, alias lines, hint rebase pair -
none in any hunk). (j) CONFIRM axes 3 + 6: axis 3 via F2 plus
the already-single verdict derivation plus R5; axis 6 family
{list, nested} both compose, hint path a different population,
root pipelines a different subject. (k) CONFIRM enumeration
member-by-member: every vocabulary census re-derived
(builder/seam/wrapper/applier/absorb callers; merge pair 2 + 2
+ internal; production `Prefetch(` at walker.py:1139/1444/1472
+ nested_fetch.py:351; `apply_type_visibility_sync(` family-1
plus resolver surfaces; both policies; gate 1 + 3;
`getattr(*definition, "model", None)` 4 at baseline / 2 in
family, now 3 / 1 with no direct-`.model` second spelling in
the optimizer; `target_model` extinct in both targets). (l)
Cells: INAPPLICABLE BY CONSTRUCTION (W1's omission cured
here): the consolidated path is plan-time sync-only - one
attribute read plus lazy queryset composition executing zero
SQL, with no database, alias, or dialect decision (the seal
reads `_db` but routes nothing; required alias stays `None`).
Same typing as the plan-time optimizer precedents f21/f22/f23.
(m) P1 re-run shared-tree 3/3 green (0.30s); P2 re-executed
above (W1's cited run superseded, not separately audited).

Cures by addition (f52 RULING R1/R3 precedent - record
completions, no W1 rewrite needed): (1) R4
nested_fetch.py:351 honest trigger (mechanism-gain): a
strategy wrap building or selecting its own child queryset
(seal choice, visibility application) instead of wrapping the
handed `request.child_queryset`. (2) Cell typing + reason as
in (l). (3) R3/R5 de-facto homes as in (e).

Gates (own whole-scope runs, shared venv): `uv run
basedpyright` -> 0 errors, 0 warnings, 0 notes; `uv run python
scripts/check_any.py` -> 128 allowed at 89 sites (unchanged,
no new `Any`); `uv run python
scripts/check_truthful_reads.py --check` -> errors 0 (mypy
never run, never cited). `uv run ruff format --check` + `uv
run ruff check` clean on all three touched paths. The
signature change (`type[models.Model] | None` ->
`DjangoTypeDefinition | None`) type-checks with no new
cast/`Any`/suppression (the `TYPE_CHECKING` import plus
lazy annotations suffice). Diff prose rules: no process
provenance, no raw `path:NN` in added code lines, oracles at
the mandated tier.

Defects (Worker-2): none - zero package defects found; no
`## Defects` entry owed. Pending execution: none.

Pins: HEAD `dd0b6691` unmoved; ITEM_BASELINE `20f44bae`;
P2 re-execution run dry-20261002T043204-c8c79f.

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
