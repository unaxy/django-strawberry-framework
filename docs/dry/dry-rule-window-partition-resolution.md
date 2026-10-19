# DRY review: `window-partition-resolution`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is window-partition resolution: given one Django
relation field, decide whether a windowed prefetch can group by a
parent key, and derive that parent-side `PARTITION BY` expression plus
the child-side connector column the prefetch attach reads — or fail
closed so the planner falls back per-parent instead of guessing. The
owner candidate, `optimizer/join_taxonomy.py::classify_relation_join`,
is re-derived below, not inherited.

Scope held in this item: the kind vocabulary, the windowability
predicate, the partition derivation, the connector derivation, the
hostile-kind sink, and the never-raises posture over all of them at
HEAD. The lateral facet (`LateralJoinShape`, link-field resolution,
through carriage) is the queued sibling `lateral-join-shape`; the
attach-complete set composition (`prefetch_attach_columns`) and the
morph-column derivation it shares are the queued sibling
`prefetch-attach-column-projection`; kind detection is the verified
sibling `relation-kind-taxonomy`; strategy selection, the strategy
seam, window slicing, and window rendering are the verified siblings
f17/f18/f19/f20. Each is converged or excluded with a contract
difference below, never absorbed.

Traced at HEAD bytes (`5c3496e0`), with a working-tree cross-check.
All four indexed files are dirty with concurrent work (the bug-hunt
truth migration, typing, maintainer `except BaseException`
deletions — none of it in the plan's `## Owned changes` ledger, so
all of it untouchable here). The rule-region census is identical at
both states: every consumer call site is textually identical modulo
hunk-shifted line numbers, the `RelationKind` literal still holds the
same five members, and `WINDOWABLE_RELATION_KINDS` still holds the
same four. The working-tree `join_taxonomy.py` respells the
definition interior (plain `getattr` reads, dropped containment
arms, virtual-link arms) without adding, removing, or re-homing any
site, so the single-ownership verdict holds at both states; the
read-policy difference is hunt-owned ground, not this family's.
Line numbers cited are HEAD lines. Prior file/family records were
read as orientation and adjudicated fresh; nothing below is
inherited.

Sites found, by role. One definition; every other site composes it
by name.

- Definition.
  `django_strawberry_framework/optimizer/join_taxonomy.py::classify_relation_join`
  (`:318`): one pure function mapping a relation field to one
  frozen `RelationJoinDescriptor`. Its parts are one definition,
  not several: `WINDOWABLE_RELATION_KINDS` (`:85`, the membership
  half), `_partition_expr` (`:184`), `_parent_join_column`
  (`:205`), the kind/windowable/partition/connector classify arms
  including the generic `object_id` partition call and the
  `forward_single` sink (`:328`-`:380`), the shared read aliases
  (`:100`-`:110`), and the guarded picker (`:113`). The generic
  name-resolution helper (`:290`) is homed in the queued sibling
  `prefetch-attach-column-projection` per the verified file split
  and composed here by name — shared mechanism, single-homed,
  still one definition for every challenge below.
- Consumers composing by name (restate nothing).
  - `optimizer/plans.py::window_partition_for_prefetch` (`:966`):
    classify plus kind-gate plus dual `OptimizerError`, returning
    `partition_expr`. Zero production callers (exact-match census:
    the `def` line is the only package `name(` occurrence; every
    other package mention is prose or a self-naming f-string).
    Test callers only: six pins in `tests/optimizer/test_plans.py`
    plus a two-call test in `tests/optimizer/test_walker.py`.
  - `optimizer/nested_planner.py::_connector_only_field` (`:167`):
    `classify_relation_join(parent_field).parent_join_column`
    under the historical name. Zero production callers (same
    census shape). One test pin in
    `tests/optimizer/test_walker.py`. Distinct symbol from the
    walker writer below despite the shared token.
  - `optimizer/nested_planner.py::plan_connection_relation`
    (`:1080`): classifies the raw re-resolved field (`:1256`),
    gates on the predicate (`:1257`), and carries the descriptor
    on the strategy request. This gate is the boundary where
    classification ends and planning begins: the classifier
    answers, the planner decides.
  - `optimizer/nested_fetch.py::attach_windowed_prefetch`
    (`:315`): threads `request.join.partition_expr` into
    `partition_by=` (`:339`). The request (`:228`) carries the
    join windowable-by-construction (`:253`).
  - `optimizer/nested_planner.py::_project_scalar_only_window`
    (`:691`): composes `prefetch_attach_columns` (`:725`) for the
    scalar-only `.only()` mask (sibling-owned composition read;
    the derivations it masks stay this family's).
  - `optimizer/walker.py::_ensure_connector_only_fields`
    (`:1576`): composes `prefetch_attach_columns` (`:1602`) for
    prefetch child plans — the module no seed named, a consumer,
    not a second definition.
  - `optimizer/nested_planner.py::_advise_composite_index`
    (`:599`): reads `parent_join_column` plus `content_type_column`
    (`:646`) for the morph-first equality prefix (queued-sibling
    read under standing R16).
- Oracles (independent: spell values, never read the owner).
  `tests/optimizer/test_join_taxonomy.py` pins every kind verdict
  (reverse FK, both M2M directions, forward single, reverse O2O,
  generic, doubles, three fail-close arms, hostile metadata, and
  the membership-set literal); `tests/optimizer/test_plans.py`
  pins the shim's four partition equalities plus both raise arms;
  `tests/optimizer/test_walker.py` pins the connector shim, both
  M2M shim equalities, and the shared-child per-parent
  partitioning proof through the production windowed body;
  `tests/optimizer/_builders.py` composes the classifier by name
  for strategy tests; five live-tier suites pin window SQL. The
  `FieldMeta`-fed legs have no oracle — standing D1, closeout-homed,
  scoped honestly under Findings.
- Projections. The module taxonomy table, shim and gate
  docstrings, spec-033 Decision 4, the spec-033 rationale
  post-ship note plus Non-Decision deliberation, the
  `exceptions.py` `OptimizerError` bullet, and the KANBAN
  existence item.

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. Partition derivation
   exists only in the optimizer. The lookalikes are excluded with
   contract differences: the filters to-field read (standing R9,
   addressing vs grouping), filters many-side branches (E5),
   forms/M2M and mutation M2M write handling (E6), the connection
   cursor-path kind gate (E4), and the `str.rpartition` / relation
   `plan_kind` false friends. No second flavor derives a grouping
   key.
2. Sync/async twins: inapplicable with reason. The classifier is a
   pure synchronous derivation over in-memory field metadata — no
   await point, no I/O, no twin. Both execution colors consume the
   same descriptor through the plan-time path; the connection
   module's two colored bodies (verified ground) consume rendered
   plans, never the classifier.
3. Derived rather than repeated knowledge: searched. No consumer
   re-derives the partition from `relation_kind` string checks —
   the kind-dispatch census finds the one interior dispatch (plus
   the shim's shared-set use and snapshot-carriage branches,
   each excluded). `FieldMeta` carries fallback subset slots
   (standing tri-split carry leg, taken as input under D1); the
   planner re-resolves raw precisely for the partition/through gap
   (standing R-B, trigger-checked clean).
4. Inverse / round-trip pairs: inapplicable with reason. The
   partition is a one-way derivation (field to grouping key) with
   no decode half. The attach round-trips through Django's own
   prefetch machinery, not through package code, so no second half
   exists to consolidate.
5. Contracts restated in another medium: searched. Production (1
   definition), oracles (spelled values at three test tiers),
   spec-033 Decision 4 plus rationale (contract source), KANBAN
   (board-owned existence question), `exceptions.py` (projection).
   A rule change moves production once; oracles and prose are
   listed per challenge, never counted.
6. Enforcement by omission: enumerated over the closed
   `RelationKind` membership (five members, HEAD and working tree
   identical). `many`, `reverse_many_to_one`,
   `reverse_one_to_one`, and `generic` classify windowable with a
   derived partition; `forward_single` sinks to `UNSUPPORTED`.
   Every member has an owner oracle row plus its consumer path
   (`windowable` gate, shim raises, lateral degrade). No member
   lacks its verdict; the forward-single exclusion is the
   contract (spec-033), not a gap.

### Enumeration

Ten spelling instruments over the HEAD package tree, each run to
an exact executable population; prose mentions separated from
code reads throughout.

- `classify_relation_join`: one `def`, five production calls
  (plans shim, planner shim, planner gate, scalar-only loop,
  walker writer), zero other callers.
- `partition_expr` / `partition_by` / `PARTITION BY`: the one
  derivation, the two shim/gate reads, the one fetch threading,
  the renderer parameter (verified f19/f20 ground) — plus two
  `str.rpartition` false friends.
- `window_partition_for_prefetch`: one `def`, zero production
  calls, test pins only.
- `_connector_only_field`: one `def`, zero production calls, one
  test pin; the walker `_ensure_connector_only_fields` writer is
  a distinct symbol with one production caller.
- `parent_join_column` / `prefetch_attach_columns` /
  `RelationJoinDescriptor`: the one derivation, the one sibling
  composition, reads only at the censused consumers.
- `WINDOWABLE_RELATION_KINDS`: one literal, read by the
  classifier and the plans shim; no restatement.
- `remote_field` code reads: the derivation interior plus the
  filters to-field read (standing R9); everything else prose.
- `m2m_field_name` / generic-name / fallback-slot / `through`
  code reads: the derivation interior, the `FieldMeta` carry
  slots, the `relation_kind` detect arms, and the write-path
  false friends — each homed.
- `relation_kind(` dispatch: the one interior call plus
  mechanism-routing and snapshot readers, each excluded on its
  contract.
- `RelationKind` literal members: five, each with its classify
  arm and oracle row (axis 6).

Every member lands in F1 (definition plus shims plus gate),
a queued sibling (facets and downstream machinery), a standing
rejection (taken as input), or a fresh exclusion below. Nothing
unassigned; no consolidation inside the enumeration.

### Challenges

Each change posited against the rule's variation axes; counts are
authoritative definitions only. Consumers, oracles, and projections
that also move are listed, never counted. All static-reviewed
against HEAD bodies; no execution.

- C1, M2M partition expression change (forward M2M groups by a
  through-table column instead of the reverse query name):
  `_partition_expr` moves. Count 1. Follows: both M2M oracle
  rows, the shim pins, the shared-child proof, the module table.
- C2, windowable membership change (a kind leaves or joins the
  set): the set literal plus the classifier's kind arms move
  together as one record. Count 1. Follows: the membership
  oracle, the gate behavior, the shim's wrong-kind arm.
- C3, generic partition column change (different morph-name
  slots): the shared name-resolution helper moves (sibling-homed
  F3 mechanism, composed here by name). Count 1. Follows: generic
  oracle rows, the morph advisory prefix.
- C4, connector derivation change (reverse-FK connector reads a
  different slot): `_parent_join_column` moves. Count 1. Follows:
  the connector shim pin, the attach composition, both writer
  paths, connector oracle rows.
- C5, shim posture change (the plans shim returns `None` instead
  of raising): the shim alone moves; no rule site is involved.
  Count 0. This is the negative proof the shims are consumers:
  a consumer-posture change touches no definition, and no rule
  change requires touching a shim.
- C6, fallback sink change (an unreadable kind sinks to
  `UNSUPPORTED` instead of `forward_single`): the sink arm moves.
  Count 1. Follows: the hostile-metadata oracle rows.

No challenge counts above 1; no second partition, connector,
windowability, or sink definition exists at either tree state.

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (worker-2.md step 1).
Traced at HEAD `5c3496e0` bytes with a working-tree cross-check; the
four indexed files are dirty with concurrent hunt dirt, attributed by
content below. Citations are WT `path:NN` (HEAD differs by hunk
shift only; rule-region census identical at both states).

### W2 fingerprints

| File | HEAD blob | WT blob | Dispatch pin match |
|---|---|---|---|
| `optimizer/join_taxonomy.py` | `8026dc8d` | `aa289013` | 4/4 WT match |
| `optimizer/plans.py` | `97a524e2` | `2e962ae2` | 4/4 WT match |
| `optimizer/nested_planner.py` | `8c3a45f5` | `b6ff0a0e` | 4/4 WT match |
| `optimizer/nested_fetch.py` | `bedaa76e` | `c36826bb` | 4/4 WT match |

Full SHAs verified via `git rev-parse HEAD:` /
`git hash-object` (this section's `### W2 gate runs`). HEAD-vs-WT
diff over the four files: read-policy respell inside the
definition (`_safe_getattr` -> `_attr`, `_safe_flag` -> `_flag`,
`safe_truthy` -> plain truth, never-raises framing dropped) plus
one new in-module helper (`_child_link_is_virtual`) and its call
arms. No `def`/`class` added or removed besides that rename pair
and helper; no consumer call site added, removed, or re-homed
(plans `:994`, planner `:183`/`:725`/`:1256`, walker `:1604`
all present at both states). All dirt concurrent (truth
migration, typing); none in the plan's `## Owned changes`.

### W2 sites and roles (own census, WT bytes)

Definition (1): `optimizer/join_taxonomy.py::classify_relation_join`
(`:331`) with its in-module parts — `WINDOWABLE_RELATION_KINDS`
(`:80`), `_partition_expr` (`:185`), `_parent_join_column`
(`:212`), `_through_model` (`:256`), `_through_link_fields`
(`:268`), `_generic_child_attname` (`:304`), the read aliases
(`:92`-`:104`), `_child_link_is_virtual` (`:170`), the
`RelationJoinDescriptor` record (`:108`), and the classify arms
(`:341`-`:394`). One module, one entry, one reason to change:
parts, not separate definitions.

Boundary (sibling-homed facets computed in the same body):
`LateralJoinShape` (`:66`) assignment arms + link-field/through
carriage (queued `lateral-join-shape`), `prefetch_attach_columns`
(`:152`) composition (queued `prefetch-attach-column-projection`),
kind detection via `utils/relations.py::relation_kind` (verified
sibling ground). The body computes them; the siblings own their
contracts. No challenge below moves more than this one body.

Consumers composing by name (restate nothing):
`plans.py::window_partition_for_prefetch` (`:968`, classify +
imported-set kind gate + dual raise, returns
`descriptor.partition_expr`); `nested_planner.py::_connector_only_field`
(`:168`, bare `parent_join_column` projection);
`nested_planner.py::plan_connection_relation` (`:1266`, classify
raw + `windowable` gate, descriptor rides the request);
`nested_fetch.py::attach_windowed_prefetch` (`:340`,
`request.join.partition_expr` into `partition_by=`);
`nested_planner.py::_project_scalar_only_window` (`:735`,
`prefetch_attach_columns` loop); `walker.py::
_ensure_connector_only_fields` (`:1604`, same composition —
the module no seed named);
`nested_planner.py::_advise_composite_index` (`:654`-`:662`,
attribute reads `through_model`/`parent_join_column`/
`content_type_column`); `lateral_fetch.py` (`:1084`/`:1129`/
`:1144`, shape + link reads); `single_parent_fetch.py`
(`:144`, shape + link gate). Both shims have zero production
callers (exact-match package census: the `def` line is the only
`name(` occurrence; all other mentions prose or self-naming
f-strings); test callers only.

Oracles (spell values, never read the owner):
`tests/optimizer/test_join_taxonomy.py` (per-kind verdicts,
membership literal, fail-close arms), `tests/optimizer/
test_plans.py` (`:1060`-`:1117`, four partition equalities +
both raise arms), `tests/optimizer/test_walker.py`
(`:2022`-`:2031` connector pin, `:3470`-`:3475` M2M
equalities, shared-child per-parent proof). No oracle feeds a
`FieldMeta` to the classifier (standing D1's blast-radius
clause, confirmed by the call-site census above: raw fields
and namespace/class doubles only).

Projections: module taxonomy table + shim/gate docstrings,
`exceptions.py` `:231`-`:234` bullet, spec-033 Decision 4
(contract source).

### W2 change challenges (own stress set)

X1, new windowable relation kind: the set literal + one
classify arm move, same module. Count 1.
X2, second taxonomy reader (a new consumer calls the
classifier): 0 new definitions — consumer, not a copy.
X3, split the classification (generic arm to its own
classifier): would CREATE a second definition; no such split
exists at either tree state, and no landable owner exists
for the fragment (it would re-import the same read aliases
and kind vocabulary — a sibling import for machinery,
forbidden by principle 7). Not a consolidation candidate.
Count 1 (absence confirmed).
X4, reverse-M2M partition changes: `_partition_expr` only.
Count 1.
X5, through-link resolution changes: `_through_link_fields`
only. Count 1.
X6, connector slot changes: `_parent_join_column` only.
Count 1.
X7, shim posture change (raise -> `None`): the shim alone;
0 definitions. Negative proof the shims are consumers.

No challenge counts above 1. Independent package-wide sweep
for a second definition (`remote_field` code reads,
`m2m_field_name`, generic-name slots, fallback slots,
`through` reads, `relation_kind(` dispatch, `PARTITION`
rendering): every code hit is the definition interior, a
censused consumer read, a sibling-homed mechanism
(`relation_kind` detect arms, `FieldMeta` carry slots,
write-path M2M handling), or a `str.rpartition` false
friend. No real consolidation exists; nothing to demand.

### W2 owner choice (principle 7)

`optimizer/join_taxonomy.py::classify_relation_join`: the
existing owner of the join-condition vocabulary, a leaf
module (imports only `utils/relations.py` + one
`field_meta.py` predicate) every consumer already imports
without a cycle; the narrowest cohesive home the planner,
renderer, walker, and both fetch backends can all depend on.
Dependency direction agrees (no reversal). No rival owner
is landable: `plans.py` (renderer) and `nested_planner.py`
(planning orchestration) are both downstream IMPORTING
consumers, and `utils/relations.py` owns kind DETECTION, a
distinct contract (field -> label, no partition/connector
knowledge).

### W2 matrix (own discharge)

1. Cross-flavor: searched — optimizer-only; filters
to-field/many-side, forms/mutation M2M writes, connection
cursor-path reads differ in contract (addressing/routing/
writing vs grouping).
2. Sync/async twins: inapplicable with reason — pure
synchronous derivation over in-memory metadata; both
colors consume the plan-time descriptor.
3. Derived knowledge: searched — no consumer re-derives from
`relation_kind` strings; the set is imported, never
re-listed; `FieldMeta` carries subset slots (tri-split
carry leg under D1).
4. Round-trip pairs: inapplicable with reason — one-way
derivation; attach round-trips through Django, not package
code.
5. Other media: searched — 1 definition, spelled-value
oracles at three tiers, spec-033 + `exceptions.py` prose.
6. Omission: enumerated over all five `RelationKind`
members — four windowable with derived partitions,
`forward_single` sinks to `UNSUPPORTED` per spec-033
(contract, not a gap).

### W2 pre-findings positions (to reconcile below)

Standing rejections (own sample, trigger-checked fresh at
HEAD/WT bytes): R-A (sets differ by `reverse_one_to_one` —
windowability vs list-ness, still split `:80`-`:87` vs
`utils/relations.py:56`-`:58`); R-B/field_meta routing
(planner re-resolves raw via `_meta.get_field` at
`nested_planner.py:1079` because `remote_field` is not on
`FieldMeta` — routing genuinely impossible for the
partition leg); R-C/R13 lenient readers (HEAD shared
bodies vs WT plain `getattr` — hunt-owned read-policy
dirt, not family ground); R5 (walker's
`_record_relation_access:1138` reads `django_field.attname`
for FK-id elision/strictness — different subject from the
connector derivation); R6 (shape enum vs strategy
protocol); R7 (grouping key vs ORM lookup accessor); R8
(six independent pk reads); R9 (filter addressing vs
grouping); R10/R11 (through-scan and GENERIC arms refused
at the owner); J1/J2 (shared guard idioms, not the rule);
tri-split (detect/carry/resolve legs); R15 (pk-ATTNAME
vs pk-NAME); R16 (attach-key order vs advisory order).
All clean; none reopens.

Standing D1: taken as input for closeout homing, not
re-filed — correct iff W1 scopes the `FieldMeta`-fed legs
and the missing oracles honestly (verified above: both
legs live, zero `FieldMeta`-fed pins).

O1 (both shims zero production callers): test-pinned
boundary names, keep-or-home question — ROUTED, not a
defect, iff the routing target is concrete enough for
closeout homing (judged after reading).

Cells: `inapplicable by construction` iff the rule's
surface reaches no database, alias, or dialect decision —
on my trace it is pure derivation over in-memory relation
metadata (attribute reads + `_meta` field resolution at
plan time; the `_meta.get_field` calls resolve model
metadata, never rows). Provisionally endorsed; final call
after reconciling W1's reason against this surface.

### W2 reconciliation (after reading `## Findings`)

Every difference reconciled explicitly; citations are fresh
evidence recomputed by me, never inherited.

- F1 count-1 + owner: AGREE. My X1-X7 converge with C1-C6
  challenge-for-challenge (my X7 independently re-derives C5's
  count-0 negative proof; my X2/X3 stress axes W1 did not
  posit and still count <=1). Same owner, convergent
  principle-7 reasoning (I additionally refuse
  `utils/relations.py` as kind-DETECTION, a distinct
  contract). Lifetime fields agree (pure, uncached, frozen,
  request-scoped carriage).
- Lateral/single-parent descriptor reads: I census them as
  consumers; W1 homes them under sibling E1's facet. Pure
  classification difference — both agree by-name
  composition, no restatement, count unaffected. Accept
  W1's homing.
- `_generic_child_attname` homing: I treated it as an
  in-module part; W1 homes it in queued
  `prefetch-attach-column-projection` per the verified file
  split. The split sentence is REAL (file artifact F3 owns
  "the attach set, the morph column", naming the helper),
  so I converge to W1's homing entirely. C3 counts 1
  either way; the sibling trace will find the recorded
  composition.
- S1-S7: all trigger-clean CONFIRMED on my own fresh
  sample (S1 set-split, S2 exactly-three readers, S3 raw
  re-resolution, S4 exactly-two HEAD `lenient=True` sites
  with WT-at-zero noted as hunt dirt, S5 elision vs
  connector subjects, S6 filters:314 sole other code read
  with filters/inputs:1187 confirmed docstring prose, S7
  coincide/diverge per plans R-5). All seven attribution
  labels verified real (relation-kind-taxonomy family row,
  field_meta-R1/R-B, R-C, walker artifact:444 R5, R9,
  plans artifact:501 + s11:1398 R-5). The interior rows W1
  takes as input I checked independently — all clean.
- E1-E17: each carries a contract difference + trigger
  (E16 is a projection with a stated move condition — no
  trigger owed). All seven sibling boundaries name REAL
  queued rows (plan:1358/1359/1365/1367/1368/1369/1370/
  1363; E11 spans two). E-substance spot-checked fresh
  (E7 renderer takes `partition_by=` explicitly at
  plans:1014; E9/E11/E13 boundaries hold at HEAD bodies).
- O1 routing: AGREE, routed-not-a-defect. Zero-caller
  census confirmed fresh; twin homing confirmed real
  (KANBAN:309 board record + rationale:344 three paths
  (a)/(b)/(c)); planner-twin zero mentions confirmed
  (KANBAN 0, spec 0, rationale 0). Routing target
  (Worker-0, NAMED card at closeout, next to the twin
  question) + trigger = concrete enough. Endorsed.
- Standing D1 taken-as-input: AGREE, correct not to
  re-file. Both `FieldMeta` legs live (walker:1604,
  planner:735), zero `FieldMeta`-fed pins, W1 scopes
  honestly ("no claim depends on a pinned subset
  verdict").
- Matrix/enumeration: my six-axis discharge converges
  axis-for-axis; my package-wide sweep lands every member
  where W1 lands it (I additionally census the E1 shape
  reads and `_builders.py:11/:35` by-name composition —
  confirmed, consistent). Nothing unassigned either side.
- Pending-execution "None": AGREE. No `proof:` owed
  (nothing lands), no `gate:`. Cells
  `inapplicable by construction` ENDORSED on my own
  surface reason: attribute reads + `_meta` metadata
  resolution (`_meta.get_field`, `m2m_field_name()`,
  `pk.attname` touch model metadata, never rows); no
  alias/dialect/database decision anywhere in the rule's
  surface. Plain `verified` follows.
- No new index rows: ENDORSED — no new family/sub-rule;
  boundaries converge on existing queued rows.
- Tracked diff empty: CONFIRMED fresh — `git diff
  ITEM_BASELINE --name-only` = the plan edit alone,
  artifact untracked, no `## Implementation`, 4/4 WT pins
  match dispatch pins, status count 469 exact.
- Behavioral proof (static) + failability citation:
  ACCEPT. The build-033 measurement is real
  (KANBAN:309 citing `docs/builder/DONE/
  build-033-connection_optimizer-0_0_9.md`).
- Structural gate none-owed: ACCEPT. The f17 precedent is
  real and verifier-endorsed (f17 artifact:285-:296, W2
  endorse:725-:728); HEAD/WT census is the first-run
  check; hand-copy control reasoned correctly.
- W1's HEAD-vs-WT characterization: CONFIRMED via diff
  (rename pair + one helper + arms; call sites intact).
- No-ticked-row-wrong check: CONFIRMED (owner + 4 files
  + F-M provenance at plan:1357/9570).

Zero material differences remain. No `(Worker-2)` defect:
no second definition, no mis-homed site, no dishonest
scope, no owed row found in the reconciliation above.

### W2 gate runs (shared venv)

Slots 1-3 venvs damaged / slot-4 unselectable per
dispatch, so all execution below ran in the shared project
venv via `uv run` (stated per constraint); no workspace
slot touched, no pytest (zero-edit, no `proof:` owed).

- `uv run ruff format --check` + `uv run ruff check` on
  the four indexed files: `4 files already formatted`,
  `All checks passed!` (strictly vacuous — zero tracked
  paths touched; the artifact is untracked scratch).
- `uv run mypy` (whole package): `Success: no issues
  found in 119 source files` — matches W1's read.
- `uv run basedpyright` (whole package): `0 errors, 0
  warnings, 0 notes` — matches.
- `uv run python scripts/check_any.py` (whole package):
  `130 allowed use(s) of Any at 90 site(s)` — matches.

### W2 verdict

`verified`, plain (no `proof:` correctly remains; cells
`inapplicable by construction` endorsed). Zero-edit F1
CONFIRM stands: one authoritative definition at
`optimizer/join_taxonomy.py::classify_relation_join`, six
challenges at most 1, every consumer composing by name.
Worker-0 may tick the plan item and release
`dry/winpart-f21`; no ledger row, no index row, no
follow-up owed by this item. Standing D1 + O1 ride
closeout homing as recorded.

## Findings

### F1: window-partition resolution is single-owned (CONFIRM, zero-edit)

Contract: how a relation join classifies into a window partition
for fetching — the kind vocabulary, the windowability predicate,
the parent-side partition derivation, the child-side connector
derivation, the hostile-kind sink, and the never-raises posture
at HEAD. Legitimate variation axes: kind membership, partition
derivation per shape, connector derivation per shape, fallback
sink. Inputs: a raw Django relation descriptor (full fidelity:
partition, through, link fields) or a `FieldMeta` snapshot
(connector/morph subset) per the corrected dual contract of
standing D1, taken as input.

Sites and roles: one definition
(`optimizer/join_taxonomy.py::classify_relation_join` with its
in-module parts, `### Enumeration` first instrument); two
zero-production-caller shims composing it by name under
consumer-owned postures (raise vs `None`); five production
consumers (planner gate, fetch threading, two attach writers via
the sibling composition, advisory read); oracles at three tiers;
projections as censused. The kind-token comparisons outside the
definition are uses of the shared vocabulary, never restatements.

Challenges: C1-C4 and C6 count 1; C5 counts 0 (negative proof of
consumer status). No challenge moves more than the one definition.

Owner and lifetime (principles 7 and 4):
`optimizer/join_taxonomy.py::classify_relation_join`, beside the
set and readers. Responsibility: the module exists precisely as
the shared join vocabulary every fetch path classifies through;
its reads are field metadata only, its effects none, and the
planner gate beside it carries the enforcement. Dependency
direction: all six consumer modules already import downward from
it, and it imports only `utils.relations` plus stdlib — the
narrowest module every legitimate consumer can depend on without
reversal. Refused: `plans.py` (it owns plan-data structures and
window rendering, not relation vocabulary — the wider module,
and the raise contract is plans-side posture, not the rule) and
`nested_planner.py` (planning orchestration; the walker leg
classifies outside planning, and the lateral/single-parent
readers import no planner module today, so housing one pure
function there would buy two new inward edges). Lifetime:
pure per-call derivation, explicitly not cached — recomputed at
each consumer call, carried request-scoped on
`NestedConnectionRequest.join`, never stored beyond the plan
call; the record is frozen, so no mutation or invalidation
exists.

Migration: none. Nothing moves, nothing is deleted, no test is
added. The principle-11 disposition of the two shims
(delete versus keep-as-boundary-with-pins) stays with the
maintainer: the plans shim is board-homed with three recorded
resolution paths, the planner twin is routed by O1 below, and
both files are hunt-stopped against any edit regardless.

Distinct behavior staying separate: the shim postures (loud
dual-raise vs `None`-lenient — different facts per standing
plans R-5, one classifier); the F2 lateral facet and F3 attach
facet on the same record (queued siblings, converged below);
the planner gate as the planning-side enforcement of the
taxonomy's predicate.

Behavioral proof: static-reviewed throughout. The oracles pin
every raw-field verdict per kind plus both shim postures, and
the shared-child proof executes the production windowed body
through the descriptor's partition — the standing build-033
failability measurement (cited as projection, not re-run) shows
owner mutations fail production rows while shim-only mutations
fail none, which is exactly the single-ownership signature.
Scoped honestly: the `FieldMeta`-fed legs have no oracle —
standing D1 owns that gap at closeout, and no claim here depends
on a pinned subset verdict. No failability run is owed: nothing
lands, so no divergence exists to prove catchable.

Structural gate: none owed. The plausible bypass is a second
partition derivation somewhere in the package; no mechanical
census closes that beyond a bespoke literal/AST existence test
per helper, which is the forbidden shape (f17 precedent,
verifier-endorsed). The HEAD package-wide census above is the
first-run check that the rule currently holds, and the in-tree
oracles pin every contract verdict so a divergent second site
fails behaviorally where it matters. Negative control reasoned:
a hand copy of the classifier body passes every behavior oracle
(the copy is correct), which is exactly why no new oracle is
proposed as a gate.

Coupling: none. Zero-edit verdict; no finding depends on another
landing.

Freshness: HEAD `5c3496e0`. `optimizer/join_taxonomy.py` HEAD
`8026dc8d` WT `aa289013`; `optimizer/plans.py` HEAD `97a524e2`
WT `2e962ae2`; `optimizer/nested_planner.py` HEAD `8c3a45f5` WT
`b6ff0a0e`; `optimizer/nested_fetch.py` HEAD `bedaa76e` WT
`c36826bb`; `optimizer/walker.py` HEAD `13e1be20` WT `4fd8077f`;
`optimizer/lateral_fetch.py` and
`optimizer/single_parent_fetch.py` clean (`a48cb0a4`,
`3a4bb89b`); `optimizer/field_meta.py` HEAD `7c9afe35` WT
`99f7b1d3`; `utils/relations.py` HEAD `3b35dfcd` WT `23df6180`;
oracles `tests/optimizer/test_join_taxonomy.py` HEAD `481294c3`
WT `df9be570`, `tests/optimizer/test_plans.py` clean `df714065`,
`tests/optimizer/test_walker.py` clean `ca5c32d7`,
`tests/optimizer/_builders.py` clean `567defa9`; contract
sources spec-033 clean `33b845a3`, rationale clean `bfb521b1`,
KANBAN HEAD `9251b17a` WT `abd929dd`. ITEM_BASELINE `7d920a3f`
matches the working tree on every sampled path (dirty-tree
snapshot); the item-scoped diff is empty. Any fingerprint change
in the four indexed files reopens the finding.

### Standing rejections taken as input (trigger-checked fresh)

S1, windowable vs many-side sets (verified family
`relation-kind-taxonomy` R-A): the sets still differ exactly on
`reverse_one_to_one` at both states — grouping vs cardinality.
Trigger unfired.
S2, morph detect/carry/resolve tri-split (verified): still
exactly three code readers (`relation_kind` detect,
`FieldMeta` carry, `_generic_child_attname` resolve). Trigger
unfired.
S3, partition/through reads routed through `FieldMeta`
(verified field_meta-R1/R-B): the snapshot still carries
neither slot and the planner still re-resolves raw for the gap.
Trigger unfired. Standing D1's subset legs do not reopen this:
subset-tolerance is not routing.
S4, strict/lenient read bodies (verified R-C): still one body
per reader with two policies, and the taxonomy still the sole
`lenient=True` consumer (exactly two sites). Trigger unfired.
S5, select-side attname vs connector (verified walker-R5):
`_record_relation_access` still appends the source-row local
column while the connector projects the child-side attach key
(different values on a forward FK). Trigger unfired.
S6, filters to-field read (verified R9): still the only other
`remote_field` code read; addressing vs grouping. Trigger
unfired.
S7, partition vs connector facts (verified plans R-5): still
coincide on reverse FK, still diverge on both M2M directions;
no one site needs both answers. Trigger unfired.
The remaining verified interior rows (guarded picker, shape vs
strategy vocabularies, query-name vs accessor, the six
`pk.attname` readers, naming API vs scan, no `GENERIC` arm,
per-site containment, lenient-alias locality, pk name vs
attname, attach vs advisory order, module mechanics) are taken
as input without re-check: interior to the single definition,
unaffected by a zero-edit verdict.

### Fresh exclusions (contract difference plus trigger each)

E1, `lateral-join-shape` (queued sibling): same record,
different facet — which correlated SQL to emit (shape plus
link objects) vs which parent key to group by. Converged on the
owner module; excluded from this count. Trigger: a backend
derives join SQL from `partition_expr`, or the vocabularies
merge.
E2, `prefetch-attach-column-projection` (queued sibling): the
attach-complete set composition for `.only()` masking plus its
writer consumers vs the per-fact derivations it masks; the
name-resolution helper is homed there and composed here.
Trigger: a completeness-policy change forces a derivation
change, or the property inlines the derivations.
E3, walker select-vs-prefetch routing: which ORM mechanism to
plan vs which key to group by. Trigger: a routing arm resolves
a partition key.
E4, connection cursor-path kind gate: keyset traversability
(forward-single non-null chains) vs fetch grouping. Trigger:
cursor resolution consumes a prefetch partition.
E5, filters many-side branches: filter-derivation branching vs
grouping. Trigger: a filter consumer needs the partition key.
E6, forms/mutation M2M write handling: write-path assignment
and reconstruction keys vs read-path grouping. Trigger: a write
path windows a prefetch.
E7, `apply_window_pagination(partition_by=)` (verified f19/f20
ground): window rendering takes the key as input vs deriving
it. This is the far boundary where classification ends:
derivation hands a string to rendering. Trigger: the renderer
derives a default key when none is passed.
E8, `nested-connection-plan-orchestration` (queued sibling):
the planner composes gate plus request plus strategy vs
classifying. Trigger: the planner inlines kind dispatch.
E9, `_raw_relation_field`: input plumbing (snapshot to raw
re-resolution) vs derivation. Trigger: the resolver prefers
snapshot fields for partition reads.
E10, `composite-index-advisory` (queued sibling): equality-prefix
reading under its own morph-first order (standing R16) vs
derivation. Trigger: an order-rule change forces a derivation
change.
E11, scalar-only and keyset-cursor projections (queued
siblings): `.only()` masking consumers vs derivation. Trigger:
a projection derives its own connector.
E12, `relation-connection-to-attr-grammar` (queued sibling):
attach-name grammar vs grouping key. Trigger: `to_attr`
derives from `partition_expr`.
E13, `unwindowable-child-queryset-classification` (queued
sibling): queryset-shape refusal vs relation-shape
classification. Trigger: the queryset classifier reads
relation kind.
E14, kind detection (verified `relation-kind-taxonomy`):
topology vocabulary (input) vs derived join facts. Trigger:
`relation_kind` returns join facts.
E15, `FieldMeta` snapshot carriage (verified ground): metadata
snapshots vs derivation; the production subset legs are
load-bearing per standing D1 yet still carry, not derive.
Trigger: the snapshot precomputes partition/through/link
facts.
E16, the `exceptions.py` bullet: projection documenting the
raise vs owning it. Moves only with the shim's contract;
listed, never counted.
E17, the `_connector_only_field` /
`_ensure_connector_only_fields` name pair: single-column read
vs plan writer with log-and-skip. Shared token, different
contracts. Trigger: the writer delegates its read to the shim.

### O1: connector-shim existence is unhomed (routed, not a defect)

`optimizer/nested_planner.py::_connector_only_field` has zero
production callers, one test pin, and — unlike its plans twin,
which the board and the spec-033 rationale home with three
recorded resolution paths — no standing record anywhere: zero
mentions on the board or in spec-033 at HEAD. Nothing is
broken (test-pinned boundary name), so this is not a defect;
the delete/route/keep disposition needs the maintainer alongside
its twin. Worker-0: home on a NAMED card at closeout, next to
the plans-shim question. Trigger: the maintainer picks a
resolution path, or the shim gains a production caller.

## Defects

None new. No non-duplication defect was found while tracing. The
no-ticked-row-wrong check passes: the run-5 naming (owner
candidate `classify_relation_join`, four indexed files) matches
HEAD — the candidate re-derives to the same owner, and every
indexed file carries a rule-role site (definition, shim, gate
plus consumers, request carriage plus threading). Standing D1
(dual input contract) is taken as input for closeout homing, not
re-filed; O1 above is routed, not a defect.

## Pending execution

None. No `proof:` entry (nothing lands, so no failability proof
is owed) and no `gate:` entry. No pytest was run; every proof is
static-reviewed against HEAD bodies. The `--cell sharded` and
`--cell pg` cells are inapplicable by construction: partition
resolution is pure derivation over in-memory relation metadata
and reaches no database, alias, or dialect decision — the
partition value is backend-neutral by construction (the windowed
body is the shared floor all strategies thread it through),
alias reads live in the verified strategy ground, and no claim
here depends on an executed row.

## Judgment

CONFIRM: window-partition resolution is single-owned — one
definition, six challenges counting at most 1, every consumer
composing by name — and the consolidation is therefore a proved
zero-edit verdict: no tracked file changed, no test added, no
`## Owned changes` row owed, no `## Implementation` section.
Seven standing rejections trigger-checked clean plus the
verified interior taken as input; seventeen exclusions carry
contract differences plus triggers, including seven queued-sibling
boundaries; one observation routed for closeout homing; zero
defects; no new index rows.

Type gates (shared venv, read-only): `mypy` clean (119 source
files, no issues), `basedpyright` clean (0 errors, 0 warnings,
0 notes), `check_any.py` clean (130 allowed uses at 90 sites).
Vacuous as consolidation gates — zero-edit verdict, no symbol
added, moved, or removed — reported here per convention for the
verifier to re-run.

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
