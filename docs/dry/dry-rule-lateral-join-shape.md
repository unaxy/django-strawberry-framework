# DRY review: `lateral-join-shape`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

The rule candidate is the lateral-join shape: the
`LateralJoinShape` vocabulary (which join a correlated child
subquery uses for one parent), its construction from a relation
field, the resolved link fields each shape joins on, and how the
lateral and single-parent fetch backends share that meaning. The
owner candidate,
`optimizer/join_taxonomy.py::LateralJoinShape`, is re-derived
below, not inherited.

Scope held in this item: the enum, the four shape-assignment
arms of the classifier, M2M link-pair resolution, the
DIRECT_FK link read, the generic `None`-link posture, and the
shape/link reads in both fetch backends. The partition facet
(`windowable`, `partition_expr`, `parent_join_column`) is the
verified sibling `window-partition-resolution` (f21); the
attach-complete projection is the queued sibling
`prefetch-attach-column-projection`; kind detection is the
verified sibling `relation-kind-taxonomy`; strategy selection,
the strategy seam, and the fetch skeleton are the verified
siblings f17/f18 plus the queued
`recognized-fetch-queryset-skeleton`; the queryset-state
classifier is the queued
`unwindowable-child-queryset-classification`. Each is converged
or excluded with a contract difference below, never absorbed.

Traced at HEAD bytes (`5c3496e0`), with a working-tree
cross-check. Two indexed files are dirty with concurrent work
(the bug-hunt truth migration, typing, maintainer
`except BaseException` deletions, and a virtual-link arm — none
of it in the plan's `## Owned changes` ledger, so all of it
untouchable here); the other two are clean at HEAD. The shape
rule is identical at both states: the enum still holds the
same three members with the same values, the classifier still
carries the same four shape-assignment arms with the same
outcomes, the descriptor is still constructed once, and
`LateralJoinShape` is still named in exactly three production
files. The working-tree `join_taxonomy.py` respells the
definition interior (plain `getattr` reads, dropped
containment arms, a virtual-link `None` arm on the DIRECT_FK
link) without adding, removing, or re-homing any site, so the
single-ownership verdict holds at both states; the read-policy
difference is hunt-owned ground, not this family's. Line
numbers cited are HEAD lines.

Sites found, by role. One definition; every other site composes
it by name.

- Definition.
  `django_strawberry_framework/optimizer/join_taxonomy.py::LateralJoinShape`
  (`:71`): the three-member enum (`DIRECT_FK`,
  `THROUGH_TABLE`, `UNSUPPORTED`, `:74`-`:76`, values defined
  once, never compared as strings anywhere). Its construction
  is one body, not several: the four shape-assignment arms of
  `classify_relation_join` (`:351` generic to `DIRECT_FK`,
  `:357` M2M to `THROUGH_TABLE`, `:361` windowable to
  `DIRECT_FK`, `:368` else to `UNSUPPORTED`), the single
  `RelationJoinDescriptor` construction (`:370`), the M2M
  link-pair resolver (`_through_link_fields`, `:253`, sole
  `m2m_field_name` naming-API site), and the DIRECT_FK link
  read (`:366`, `field.field`; generic leaves `None`).
- Consumers (read by name, stay at their boundary).
  `django_strawberry_framework/optimizer/lateral_fetch.py::_build_lateral_spec`:
  the visibility gate (`:1084`, non-`DIRECT_FK` refuses a
  carried WHERE), the shape dispatch (`:1129` `THROUGH_TABLE`
  arm, `:1144` `DIRECT_FK` arm, `:1151` else-`None` refusing
  `UNSUPPORTED` and any unknown shape), and the link-field
  reads (`:1125`-`:1142`).
  `django_strawberry_framework/optimizer/single_parent_fetch.py::single_parent_spec`:
  the combined gate (`:144`, non-`DIRECT_FK` or unresolved
  link refuses) and the link reads (`:154`-`:159`).
- Handoff, not a shape site.
  `django_strawberry_framework/optimizer/nested_fetch.py`
  carries `join: RelationJoinDescriptor` on
  `NestedConnectionRequest` (`:253`) and reads only f21's
  `partition_expr` (`:339`); it never names `LateralJoinShape`.
  `nested_planner.py` reads the sibling facets
  (`parent_join_column`, `content_type_column`, `windowable`);
  `walker.py`/`plans.py` read the descriptor through the f21
  shims. None of them names the shape.
- Oracles (listed, not counted).
  `tests/optimizer/test_join_taxonomy.py`: per-kind shape
  assertions (`test_reverse_fk_classifies_direct_fk`,
  `test_forward_m2m_classifies_through_table`,
  `test_reverse_m2m_classifies_through_table`,
  `test_forward_single_classifies_unsupported`,
  `test_reverse_one_to_one_classifies_direct_fk`,
  `test_generic_relation_classifies_direct_fk_partitioned_by_object_id`)
  plus link-resolution and fail-closed assertions.
  `tests/optimizer/test_lateral_fetch.py`:
  `test_spec_refuses_unsupported_lateral_join_shape`,
  `test_build_window_spec_unsupported_shape_returns_none`
  (including a hostile non-member shape),
  `test_spec_downgrades_for_unresolvable_through_link_fields`,
  the DIRECT_FK/THROUGH_TABLE spec builders, and the
  visibility-WHERE refusal pair.
  `tests/optimizer/test_single_parent_fetch.py`: the
  eligibility matrix (`test_spec_rejects_ineligible_windows`
  and arms). `examples/fakeshop/apps/library/tests/test_generic_connection.py::test_lateral_strategy_generic_connection_degrades_to_windowed`:
  the live generic-degradation path.
- Projections. The module table
  (`join_taxonomy.py:1`-`:48`), the descriptor docstring, and
  the backend docstrings each restate the shape meanings; all
  agree with the classifier arms. No `docs/` or board prose
  names the enum (only a historical bug-hunt progress file
  mentions it).

## Verification

### Matrix

1. Cross-flavor policy mirroring: searched. The shape rule is
   optimizer-internal; the HEAD census (`git grep`) finds
   `LateralJoinShape` in exactly three production files (the
   definition plus the two fetch backends) and `lateral_shape`
   reads in exactly two. No type, filter, order, mutation,
   form, or rest surface mirrors it. No second surface exists.
2. Sync/async twins: inapplicable with reason. Classification
   is a pure synchronous function over field objects, and both
   backends read the shape at plan time on the sync path; the
   async fetch contract belongs to the queued skeleton
   sibling, which carries specs opaquely and classifies
   nothing. No twin surface exists to compare.
3. Derived rather than repeated knowledge: searched, none
   found. Neither backend reads `relation_kind` /
   `RelationKind` / `many_to_many` (zero hits); no site
   compares the `"direct_fk"` / `"through_table"` /
   `"unsupported"` value strings (literals exist only at the
   enum); the `m2m_field_name` naming API is called at one
   site. The two `parent_link_table = child table`
   derivations (lateral `:1148`, single-parent `:160`) are
   consumer consequences under each backend's own `DIRECT_FK`
   gate, challenged as X6 below, not restated
   classifications.
4. Inverse / round-trip pairs: inapplicable with reason. The
   enum has no parse half: values are never deserialized,
   never cross a wire boundary, and the unknown-shape oracle
   proves the dispatch fails closed on non-members. Nothing
   to pair.
5. Contracts restated in another medium: discharged. Oracles
   assert each shape per relation kind and each refusal arm
   (cited above); projections agree with the arms. A
   membership change moves the classifier plus its oracles
   together, which is a contract change, not a second
   definition.
6. Enforcement by omission: enumerated, no gap. Lateral
   handles `DIRECT_FK` and `THROUGH_TABLE`, refuses
   `UNSUPPORTED`, unknown members, and unresolved links.
   Single-parent accepts `DIRECT_FK`-with-link only; its
   `THROUGH_TABLE` exclusion is a documented backend
   capability limit (module-docstring correction 2 plus the
   `single_parent_spec` docstring), not a missing guard. The
   windowed default is shape-agnostic by design (f21 ground).
   Every member is enforced somewhere; no member is enforced
   nowhere.

### Enumeration

Family item: the population is the rule's mechanism, not a
file member list. Instruments, all at HEAD bytes:

- `git grep -n "LateralJoinShape" HEAD --
  django_strawberry_framework/`: 13 hits in 3 files (7
  definition-side in `join_taxonomy.py` including the class
  line, the annotation, one comment, and the 4 assignment
  arms; 1 import + 3 reads in `lateral_fetch.py`; 1 import +
  1 read in `single_parent_fetch.py`).
- `git grep -n "RelationJoinDescriptor(" HEAD --
  django_strawberry_framework/`: 1 hit (the classifier
  return).
- `git grep -n '"direct_fk"|"through_table"|"unsupported"'
  HEAD -- django_strawberry_framework/`: 3 hits, all at the
  enum.
- `git grep -n "relation_kind|RelationKind" HEAD --
  .../lateral_fetch.py .../single_parent_fetch.py`: 0 hits.
- `git grep -n "lateral_shape|LateralJoinShape" HEAD --
  .../nested_fetch.py`: 0 hits (opaque carriage confirmed).
- `git grep -n "through_model" HEAD --
  django_strawberry_framework/ | grep -v join_taxonomy`: 0
  hits (carried, test-asserted, unread in production; O1).

Every hit lands below: the definition in F1, the backend
reads as F1 consumers, the opaque carriage as a handoff, the
oracles under their heading, the `through_model` carriage as
O1. Nothing unassigned.

### Challenges

Each change posited with its authoritative-definition count
(consumers, oracles, projections listed, never counted):

- X1, add a fourth member: the enum gains the member and the
  classifier gains the arm — 1 definition. Lateral's
  else-`None` refuses unknown shapes with zero edits (proved
  by the hostile-shape oracle); single-parent's
  `is not DIRECT_FK` needs no edit unless the new member
  must be accepted, which is new backend behavior, not a
  restated rule.
- X2, move a relation between shapes (e.g. generic leaves
  `DIRECT_FK`): the classifier arm — 1 definition. All four
  gate/dispatch reads compare by member name and follow with
  zero edits.
- X3, change link resolution (e.g. the M2M parent-side rule):
  `_through_link_fields` / the DIRECT_FK field read — 1
  definition. Both backends read the resolved objects and
  follow with zero edits.
- X4, respell a member value: the enum literal — 1
  definition. Zero string comparisons exist package-wide
  (every read is `is` / `is not`).
- X5, change the unresolved-link posture (e.g. generic
  resolves a link): the generic arm — 1 definition. The
  three `None` refusals (lateral `:1126` and `:1131`,
  single-parent `:144`) are enforcement sites
  of the once-declared "None means degrade" descriptor
  contract, one per backend boundary — enforcement sites
  stay at their boundary.
- X6, change what `DIRECT_FK` implies for the link table
  (lateral `:1148` and single-parent `:160` both derive
  "child table" under their own `DIRECT_FK` gate):
  considered shared form is a descriptor-owned link-table
  fact read by name from both backends. Rejected: it would
  own 2 lines, and the posited change contradicts `DIRECT_FK`'s
  definitional contract ("the child table carries the parent
  id", module table), so it is not a variation axis — a link
  living off the child table is a new shape, not an edit to
  two derivations. Count stays 1. Trigger: a `DIRECT_FK`
  relation whose link lives off the child table, at which
  point both derivations must move together and the shared
  form is owed.

No experiment was needed: every count above is settled by
the cited reads, and the refusal/unknown-shape behaviors are
already execution-pinned by the oracles. No `proof:` entry
is owed.

## Findings

### F1: lateral-join shape is single-owned (CONFIRM, zero-edit)

- Contract + variation. `LateralJoinShape` is the
  vocabulary for how a correlated child subquery joins to
  one parent (`DIRECT_FK`: child carries the parent id;
  `THROUGH_TABLE`: the M2M join table owns the attach;
  `UNSUPPORTED`: nothing to correlate). It varies on
  member vocabulary, per-relation membership, link
  resolution, and the unresolved-link posture. All six
  challenges count 1.
- Sites + roles. One definition
  (`join_taxonomy.py::LateralJoinShape` plus the
  classifier arms, link resolvers, and single construction);
  four consumer reads in two backends (lateral visibility
  gate, lateral two-arm dispatch with fail-closed else,
  single-parent combined gate); one opaque handoff
  (`nested_fetch.py` request carriage); oracles and
  projections as inventoried. No second definition exists
  in any module the seeds name or beyond them.
- Owner + lifetime. The taxonomy module owns it: it already
  owns relation classification (f21 verified), both
  legitimate consumers already import from it with no
  reversed dependency, and it is the narrowest home the
  backends share. Nothing is stored or cached — the
  descriptor is derived per plan call — so no lifetime
  fields are owed.
- Migration. None: every site already composes the owner
  by name. Zero-edit verdict.
- Distinct behavior. Per-shape backend behavior stays
  separate by contract: lateral renders different SQL per
  shape, single-parent excludes `THROUGH_TABLE` per its
  documented v1 capability limit, and the windowed default
  ignores the shape entirely. Lifting the single-parent
  exclusion or adding a lateral arm changes one backend,
  never the taxonomy. Recorded here and at the existing
  consumer docstrings; no prose edit owed.
- Behavioral proof. Static census plus existing oracles:
  per-kind classification, both refusal directions
  (`UNSUPPORTED` member and hostile non-member), both
  unresolved-link arms, the M2M side swap, and the live
  generic-degradation query. `static-reviewed`; nothing
  execution-deferred.
- Structural gate. None owed: the rule is already single
  and the risky bypass (a backend classifying relations
  itself) has no plausible population — both backends take
  the descriptor as a request field, and the zero-hit
  `relation_kind` census in both files is the standing
  evidence. A bespoke existence test per enum would be
  machinery, not a gate.
- Coupling. None.
- Freshness. HEAD `5c3496e0`; ITEM_BASELINE `75d0451d`
  (a stash-commit of dispatch-time state, resolves).
  `join_taxonomy.py`: HEAD `8026dc8d`, baseline and WT
  `aa289013` (equal — nothing moved during this pass; the
  delta is concurrent hunt/typing dirt: `_safe_*` to
  `_attr`/`_flag` respell, maintainer `except BaseException`
  deletions, a `_child_link_is_virtual` arm — all outside
  `## Owned changes`, untouched). `lateral_fetch.py`:
  `a48cb0a4` at all three states (clean).
  `single_parent_fetch.py`: `3a4bb89b` at all three states
  (clean). `nested_fetch.py`: HEAD `bedaa76e`, baseline
  and WT `c36826bb` (delta confined to import,
  `unwindowable_child_queryset_reason`, skeleton, and
  `resolve_strategy` hunks — none near the `join`
  handoff). Searched population: the six HEAD censuses
  above over the whole package. Excluded on body strength:
  `correlated_inner_root` / the EXISTS adapter (filter
  compilation, not join classification),
  `resolve_strategy` (config-driven selection, zero shape
  reads), `FieldMeta` (verified morph-carry split),
  `through_model` carriage (O1).

### Standing rejections taken as input (trigger-checked fresh)

- `LateralJoinShape` vs `NestedConnectionStrategy`
  (join_taxonomy-R6, both owners): still distinct —
  join vocabulary vs strategy seam (f18 verified the
  seam). Trigger unfired.
- No `GENERIC` lateral arm: the enum still holds exactly
  three members and the generic arm still classifies
  `DIRECT_FK` with a `None` link that both backends
  refuse. Trigger unfired.
- `m2m_field_name` resolution vs through-model FK scan:
  the naming API is still called at one site
  (`:272`-`:285`). Trigger unfired.

### Fresh exclusions (contract difference plus trigger each)

- S1, `recognized-fetch-queryset-skeleton` (queued): the
  clone-surviving spec slot plus recognize-or-run-windowed
  fetch protocol both backends subclass. Different subject
  (fetch execution vs join classification) and different
  change reasons (a new backend subclasses the skeleton;
  a new relation kind extends the classifier). Trigger: a
  backend that classifies joins inside its skeleton
  override.
- S2, `unwindowable-child-queryset-classification`
  (queued): classifies child QUERYSET state (custom
  subclass, annotations, `extra`), where this family
  classifies the RELATION FIELD. Both backends call both
  classifiers because the inputs differ. Trigger: one
  classifier starts reading the other's input.
- S3, `nested-fetch-strategy-seam` (verified f18): the
  strategy protocol plus the request record that carries
  `join` opaquely. Handoff vs classification. Trigger: the
  seam starts interpreting shape members.
- S4, `nested-connection-strategy-selection` (verified
  f17): config-driven backend selection that never reads
  the shape (zero hits); shape-driven downgrade happens
  INSIDE the lateral backend after selection. Trigger:
  selection starts branching on members.
- S5, `prefetch-attach-column-projection` (queued):
  sibling facet of the same descriptor (attach-complete
  `.only()` set for prefetch writers) with disjoint
  readers (`nested_planner.py`, `walker.py`). Same owner,
  adjacent facet, no shared variation axis with the
  shape/link reads. Converged as same-owner-sibling; its
  item adjudicates it.
- S6, `window-partition-resolution` (verified f21):
  sibling facet (`windowable`, `partition_expr`,
  `parent_join_column`). Taken as input; disjoint arms
  and readers from the shape/link facet.

### O1: `through_model` rides the descriptor unread (observation)

No production site outside `join_taxonomy.py` reads
`join.through_model`: lateral derives the through table
from `parent_link_field.model`, and the oracles assert the
carriage. One declaration, zero second writers — not
duplication, not a defect (the "M2M join table when
`THROUGH_TABLE`" claim is true; only the module-docstring
"join-SQL selector" phrasing reads looser than the backend
actually resolves). Verdict-neutral; recorded so closeout
can decide whether the carriage or the phrasing wants a
touch. No index row owed.

## Defects

None. The trace found no non-duplication bug: the arms
agree with the module table, the gates agree with the
descriptor contract, and the oracles pin every refusal
direction.

## Pending execution

None. No `proof:` entry (all counts static-settled with
oracle backing) and no `gate:` entry.

Cells: `inapplicable by construction` — the rule is pure
plan-time metadata over field objects (enum, classifier,
dispatch reads); it executes no query, takes no alias /
`using` / dialect branch. Each backend's fetch-time
database behavior belongs to the seam/skeleton siblings,
not this family. Worker-2 judges the claim.

## Judgment

CONFIRM: the lateral-join shape is single-owned at
`django_strawberry_framework/optimizer/join_taxonomy.py::LateralJoinShape`
plus `classify_relation_join` — one vocabulary, one
construction, one link resolution, with both fetch backends
composing it by name and the request carrying it opaquely.
Zero-edit verdict: no tracked file changed, no ledger row
owed, no new index row.

Type gates (shared tree, read-only, zero-edit so vacuous as
consolidation gates, reported for the verifier to re-run):
`mypy` clean (no issues in 119 source files),
`basedpyright` clean (0 errors, 0 warnings, 0 notes),
`check_any.py` clean (130 allowed uses at 90 sites).

## Independent verification (Worker-2)

Recorded BEFORE reading `## Findings` (only the `Status:`/`Run:` lines,
section headings, and `## Judgment` opened beforehand). Fresh trace at
HEAD `5c3496e0` bytes, WT pins verified below.

### Own site census (mechanism sweep, whole package)

Searched `LateralJoinShape`, `lateral_shape`, `parent_link_field |
through_child_field`, `through_model`, `DIRECT_FK | THROUGH_TABLE |
UNSUPPORTED`, `m2m_field_name | .through`, `many_to_many | is_m2m |
one_to_many` (optimizer), `classify_relation_join`, and the
`"direct_fk" | "through_table"` string literals across
`django_strawberry_framework/` (+ tests/examples for oracles).

Definitions (all in `django_strawberry_framework/optimizer/join_taxonomy.py`):

- D1 `join_taxonomy.py::LateralJoinShape` — the 3-member vocabulary
  (`DIRECT_FK`, `THROUGH_TABLE`, `UNSUPPORTED`). Only declaration; the
  `"direct_fk"` / `"through_table"` value literals occur nowhere else.
- D2 `join_taxonomy.py::classify_relation_join` — the one classifier
  (generic -> `DIRECT_FK`, m2m -> `THROUGH_TABLE`, other windowable ->
  `DIRECT_FK`, else `UNSUPPORTED`). Only construction.
- D3 `join_taxonomy.py::_through_link_fields` (+ the `_through_model`
  read) — the one M2M link resolution. Only `m2m_field_name` /
  `m2m_reverse_field_name` / `.through` join reader package-wide
  (`forms/resolvers.py:413` `m2m_field_names` is a form-field local set,
  different subject).
- D4 `join_taxonomy.py::RelationJoinDescriptor` lateral slots
  (`lateral_shape`, `parent_link_field`, `through_child_field`,
  `through_model`) — the one record declaration.

Consumers (compose by member name / slot read, no second derivation):

- C1 `lateral_fetch.py:1084` (`is not DIRECT_FK` visibility-WHERE gate),
  `:1129` / `:1144` (`THROUGH_TABLE` vs `DIRECT_FK` dispatch in
  `_build_lateral_spec`), `:1125` / `:1130` (link-field reads). All
  member-identity reads; the `LateralWindowSpec.through_table` slot is a
  downstream table-name projection, not a shape vocabulary.
- C2 `single_parent_fetch.py:144` (DIRECT_FK + link gate), `:154`
  (link read). Same member-identity composition.
- C3 `nested_fetch.py:254` — `NestedConnectionRequest.join` carries the
  descriptor; the module reads only `partition_expr` (`:340`, the
  window-partition sibling's surface). Opaque carriage for THIS rule.
- C4 `nested_planner.py:654` — `getattr(join, "through_model", None)`
  M2M silence guard in `_advise_composite_index`. An OUTSIDE
  `through_model` reader: consumer, not a second writer or classifier.
- C5 `nested_planner.py:1266` `join = classify_relation_join(...)` —
  the plan-time construction feeding C3; `walker.py:1604`,
  `nested_planner.py:184,735`, `plans.py:996` call the same classifier
  for sibling surfaces (attach columns / partition), not the shape.

Oracles: `tests/optimizer/test_join_taxonomy.py` (member-identity
asserts over real relation fields; `:152` pins the no-`GENERIC`-arm
rule), `tests/optimizer/test_lateral_fetch.py` (`:1357` builds an
`UNSUPPORTED` request). They name members as expected values; none
derives expectations FROM the classifier. Independent.

Projections: prior-cycle DRY artifacts + `docs/bug_hunt/bug_hunt-0_0_13.md`
mention the enum; no standing spec prose owns the shape. No independent
oracle in docs; none needed for a CONFIRM.

Excluded as different subjects (own read, fresh): `UNSUPPORTED` in
`auth/mutations.py` / `consumers.py` (websocket wording);
`field_meta.py` `many_to_many` / `one_to_many` flag carriage (record
slots, no shape derivation); `NestedConnectionStrategy`
(strategy selection, sibling family f18).

### Own change challenges (definition counts)

- X1 fifth join shape (a `GENERIC` arm, the shape the owner prose at
  `join_taxonomy.py:353-356` explicitly refuses): forces D1 (member) +
  D2 (arm) + D3-or-link-read (generic link facts) — all inside the ONE
  owner module, one change obligation — plus consumer extensions at C1
  (dispatch arm; today `else -> None` refuses) and C2 (gate decision).
  Backend arms are consumer-owned SQL, listed not counted. Count: 1.
- X2 second classifier (some module deriving DIRECT_FK vs THROUGH_TABLE
  from flags without D2): none found. Nearest misses are C4 (reads the
  descriptor's own slot) and `field_meta.py` (carries flags, derives no
  shape). Count: 1 (no second body to move).
- X3 member-identity vs string dispatch (a consumer comparing
  `"direct_fk"` / `"through_table"` literals): no literal read outside
  D1. Every dispatch is `is` / `is not` on members. Count: 1.
- X4 link-resolution move (M2M sides swap for self-referential M2M):
  owned once at D3 (`forward_field is field` arm); C1 reads the resolved
  objects. Count: 1.
- X5 `through_model` carriage drop: D4 declares, D2 writes, C4 reads
  (M2M silence). One declaration, one writer, one consumer. Count: 1;
  carriage-vs-marker is a phrasing question, not a second definition.

### Owner I would choose (principle 7)

`django_strawberry_framework/optimizer/join_taxonomy.py::LateralJoinShape`
+ `classify_relation_join`: the module already owns every join-derived
fact (partition, attach column, shape, links); both fetch backends and
the planner already depend on it with no reversed edge; the narrowest
cohesive home every legitimate consumer imports. No alternative owner
is landable (the backends cannot own a vocabulary they both read; the
request record cannot own the classification it carries).

### Zero-edit + freshness (re-verified myself)

- `git diff ITEM_BASELINE --name-only` = `docs/dry/dry-0_0_15.md` alone;
  `-- django_strawberry_framework/` = empty. No `## Implementation` in
  this artifact. Tracked diff for the item: empty (plan edit is
  Worker-0's, outside the item's production scope).
- WT pins match dispatch pins 4/4: join_taxonomy `aa289013...`,
  lateral_fetch `a48cb0a4...` (= HEAD, clean), single_parent_fetch
  `3a4bb89b...` (= HEAD, clean), nested_fetch `c36826bb...`. HEAD pins
  `8026dc8d...` / `bedaa76e...` likewise match. Dirt in join_taxonomy /
  nested_fetch is concurrent (hunt) work by position — untouched.
- Status count not re-derived (plan-side assertion; my scope is the
  item diff + artifact, both confirmed above).

### Reconciliation with `## Findings` (read AFTER the above)

Claim-by-claim adjudication on fresh evidence (my census above vs
W1's sections; every difference reconciled):

- F1 count-1 + owner: ENDORSE. Census identical to mine
  (13 hits / 3 files re-confirmed; D1-D4 = W1's "one
  definition"; C1/C2 = the four consumer reads; C3 = the
  opaque handoff). Owner identical with the same principle-7
  reasoning. Challenges: W1 X1-X4 match my X1-X4 (fourth
  member, membership move, link resolution, value respell);
  W1 X5 (unresolved-link posture) verified — the three `None`
  refusals sit at the cited lines and are enforcement sites,
  correctly uncounted; W1 X6 (link-table derivation at
  lateral `:1148` + single-parent `:160`) is a challenge I had
  not posited — both sites verified, the rejection is
  well-formed (2-line shared form, definitional contract,
  stated trigger). All counts 1. No consolidation candidate
  found by either trace.
- Standing rejections (3): ENDORSE, trigger-clean. Re-verified
  on my own sample: exactly 3 members; generic still
  `DIRECT_FK` + `None` link refused by both backends; the
  `m2m_field_name` naming API still called at one site. They
  match plan rows join_taxonomy-R6, R10, R11.
- Fresh exclusions S1-S6: ENDORSE. Statuses checked against
  the plan: S1 open, S2 open, S3 consolidated f18, S4
  consolidated f17, S5 open, S6 consolidated f21 — all name
  REAL rows with exact framings. Each carries a contract
  difference + trigger. S4's "selection never reads the
  shape" verified (zero shape hits in `nested_fetch.py` on my
  independent searches); S5's disjoint readers verified
  (`walker.py:1604`, `nested_planner.py:735`).
- O1: premise HEAD-TRUE, WT-FALSE; disposition ENDORSED with
  a rider. W1's "0 hits" enumeration is correct at HEAD — I
  re-ran `git grep -n "through_model" HEAD` minus
  join_taxonomy: empty; HEAD `nested_planner.py` has zero
  `through_model`. At WT, concurrent (hunt, uncommitted,
  untouchable) dirt adds ONE outside consumer read my trace
  found first: `nested_planner.py:654`
  `getattr(join, "through_model", None)`, the M2M silence
  guard in `_advise_composite_index` — verified present in
  WT, absent at HEAD. It is a consumer, not a second writer
  or classifier, so F1 is unaffected at BOTH states and O1's
  "not duplication, not a defect, verdict-neutral, no index
  row" disposition STANDS. Rider for closeout (not a row):
  the WT reader makes the carriage load-bearing for the
  advisory, so the carriage-vs-phrasing decision now has one
  consumer to weigh. W1's WT cross-check covered only
  indexed-file interiors, which bounds the miss; no `## Defects`
  entry — nothing in production is broken.
- Matrix (6 axes): ENDORSE. Axis 1 census matches mine; axes
  2/4 inapplicability reasons judged sound (pure sync
  function over field objects; no parse half, fail-closed
  oracle exists); axis 3 re-verified at HEAD (zero
  `relation_kind` / `RelationKind` / `many_to_many` in both
  backends; zero value-string compares); axis 5 oracles all
  exist (4 cited test names grepped present); axis 6 matches
  the backend docstrings I read.
- Cells `inapplicable by construction`: ENDORSE. I read the
  whole classify path: attribute + `_meta` reads only, no
  query execution, no alias / `using` / dialect branch; the
  shape reads are plan-time identity compares. The
  "fetch-time DB behavior belongs to the seam/skeleton
  siblings" split is exact — no DB decision sits inside this
  rule's surface.
- Pending-execution "None": ENDORSE → plain `verified`. Every
  count is static-settled with oracle backing (both refusal
  directions incl. the hostile non-member); no `proof:` owed,
  no `gate:` owed.
- No new index rows owed: ENDORSE. Every S-row pre-exists;
  O1 needs none (rider rides closeout prose, not a row).
- Freshness: ENDORSE. All pins match mine on all three
  states; ITEM_BASELINE resolves; searched population stated
  and re-runnable. One bounded gap (above): the WT-only
  nested_planner read postdates the HEAD trace — concurrent,
  out of scope, verdict-neutral.
- Structural gate none-owed: ENDORSE. No plausible bypass
  population (backends take the descriptor as a request
  field); a bespoke enum-existence test would be machinery.
  The refusal oracles pin the risky directions.
- Type gates (re-ran whole-package myself): `mypy` clean
  ("no issues found in 119 source files"), `basedpyright`
  clean ("0 errors, 0 warnings, 0 notes"), `check_any.py`
  clean ("130 allowed use(s) at 90 site(s)") — all match
  W1's report exactly. Ruff: VACUOUS — the item touches zero
  tracked paths (my only edit is this untracked scratch
  artifact; `.md` is outside ruff). No AGENTS.md prose issue
  in the empty tracked diff; the artifact is per-cycle
  scratch (raw `path:NN` allowed, no style verdict spent).

Differences from my pre-reading trace, all reconciled: (a) my
C4 vs W1's "unread" — WT-only concurrent dirt, W1 HEAD-correct,
verdict unaffected (rider above); (b) W1's X6 — extra challenge,
verified and endorsed; (c) nil otherwise — censuses, counts,
owner, exclusions, and gates converge.

Verdict: `verified`, plain. No revision candidate, no block:
zero-edit CONFIRM stands at HEAD and WT.

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
