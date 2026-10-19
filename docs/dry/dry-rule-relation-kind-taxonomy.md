# DRY review: `relation-kind-taxonomy`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

The relation-kind classifier answers two questions for the whole
package: which of the five Django relation shapes a descriptor is
(`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`,
`"forward_single"`, `"generic"`), and which of those render as
GraphQL lists. The provisional owner holds all three pieces in one
module: [relations][relations]`::relation_kind` (the decision),
[relations][relations]`::is_many_side_relation_kind` (the predicate),
[relations][relations]`::MANY_SIDE_RELATION_KINDS` (the table).

Whole-package sweep for the mechanism (every `relation_kind` /
`is_many_side` / `MANY_SIDE` import or call, every hand-rolled
`isinstance(...ManyToMany...)` / `one_to_many` / `remote_field`
shape check) finds exactly one authoritative decision plus
consumers that compose it by name and neighbors with distinct
contracts. No second classifier exists: in particular there is no
inline `isinstance` chain that classifies kinds anywhere.

Definition (1): [relations][relations]`::relation_kind` +
`::is_many_side_relation_kind` + `::MANY_SIDE_RELATION_KINDS`.

Consumers (compose by name, listed never counted): the
[field-meta][field-meta] stamp (`_from_field_shape` reads flags via
`relation_bool`/`relation_name`, computes `kind` once, gates
nullable and elision on it) plus its `relation_kind` /
`is_many_side` delegating properties; `walker.py::plan_relation`
(many-side dispatches to prefetch, plus the `force_select` guard);
[join-taxonomy][join-taxonomy]`::classify_relation_join` (lenient
`relation_kind` call with a documented never-raises fallback);
`plans.py::window_partition_for_prefetch` and
`nested_planner.py::_connector_only_field` (shims over the join
classifier); `extension.py::plan_relation` (delegate to the
walker); `converters.py::resolved_relation_annotation`,
`types/base.py` (relation-shape validation, `PendingRelation`
snapshot), `types/resolvers.py` (`_check_n1` probe branch,
resolver dispatch incl. the `reverse_one_to_one` arm),
`types/finalizer.py` (connection-synthesis eligibility),
`inspect_django_type.py` (relation rows); `filters/sets.py`
(`_relay_filter_class_for_field`, docstring cites the shared
classifier); `connection.py` (`_resolve_order_path_field`
forward-single screen); `classify_path` / `_lenient_traverses_to_many`
/ `is_forward_concrete_relation` (interior uses at the owner).

Oracles: `tests/utils/test_relations.py` (80 tests: kind pins
incl. MTI, 5.2 M2M shape, generic parity, hostile-metadata pins,
the 32-path to-many matrix), `test_field_meta.py` (kind +
many-side delegation pins), `test_join_taxonomy.py`
(windowability pins), live HTTP suites for the wire behavior.

Projections: `inspect_django_type.py::_RELATION_KIND_LABELS`
(display names), module/slot docstrings, `TREE.md` prose.
`PendingRelation.relation_kind` is a snapshot field whose
docstring states production reads the live `FieldMeta` instead.

The `## Owned changes` D1 row (walker seal-policy fix) was read;
this family needs no walker edit, so that row is untouched.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** The stamp serves every
flavor from one `field_map`; filters/orders/mutations/forms/REST
read slots or the classifier by name. Neighbor flag reads with
their own contracts are rejected below (R-D through R-H), each
with its difference. Discharged.
2. **Sync/async twins.** No such surface: the classifier is pure
(flag reads plus contained truth tests), zero ORM I/O, zero
await. Inapplicable by construction.
3. **Derived rather than repeated knowledge.** Every consumer
reads the decision (`relation_kind`, `is_many_side`, or the
`FieldMeta` slots/property) rather than recomputing the five
flags. The write flavors' raw `many_to_many` reads operate on a
forward-only population the taxonomy agrees with (R-D).
Discharged.
4. **Inverse / round-trip pairs.** No such surface: one-way
classification, no un-classify, no parse-back. Discharged.
5. **Contracts restated in another medium.** Oracles execute the
classifier (raw-vs-snapshot parity probes, kind pins) and never
mirror its tables; display labels and docstrings are
projections. Discharged.
6. **Enforcement by omission.** No member lacks a required guard:
the defensive `one_to_many`-without-`auto_created` fallback is
test-pinned; the strict stamp and the lenient taxonomy differ
by stated policy (R-C), not by gap. Discharged.

### Enumeration

Instrument: whole-package content sweep over
`django_strawberry_framework/` for the mechanism vocabulary
(`relation_kind`, `is_many_side`, `MANY_SIDE`,
`WINDOWABLE_RELATION_KINDS`, `one_to_many` / `many_to_many` /
`one_to_one` flag reads, `remote_field` / `through` walks,
`content_type_field_name` / `object_id_field_name` slots,
`isinstance` against relation classes). Population: every match
triaged below. Members: 1 definition trio, 16 consumer sites,
2 kind-sets, 9 rejection candidates. No member unassigned; every
`### Challenges` row ends in the definition or a rejection.

### Challenges

Authoritative definitions only; consumers, oracles, and
projections that also move are listed, never counted.

- CH1 (new Django relation shape: composite-pk relation, new
generic form, version drift). Definitions forced: **1**. The
decision reads `many_to_many` / `one_to_many` / `one_to_one` /
`auto_created` plus the generic slots and never `concrete`
except the reverse-O2O arm, so the Django 6.1 M2M `concrete`
flip the stamp handled at FL4 needs nothing here: the M2M arm
keys on the stable `many_to_many` flag on every supported
release. MTI parent link and reverse O2O classify identically
on 5.2 and 6.x.
- CH2 (new kind string: a sixth `RelationKind`). Definitions
forced: **1** (`relation_kind` plus the set-membership answer,
one edit site; the predicate reads the table). The
`FieldMeta` properties compose by name. `WINDOWABLE` membership,
label rows, and resolver dispatch are kind-level USES that move
with the feature, listed not counted.
- CH3 (generic-detection change). Definitions forced: **1**
(the duck-typed arm). The FL7 parity slots flow through the
stamp so raw and snapshot classify identically; the
non-`None`-slots (never `hasattr`) form is load-bearing and
judged correct (principle 2).
- CH4 (R1/R5 placement). Re-derived fresh: R1 (taxonomy cannot
route through `FieldMeta`: `remote_field` / `through` carriage
gap plus end-to-end never-raises) and R5 (strict stamp reads vs
lenient taxonomy reads share one body at `relation_attr`) live
at different layers — read body vs classification use — with
different triggers. Verdict: stay separate. Counts: R5 is a
completed sharing (0 definitions to move); R1 is a durable
rejection below.

## Findings

### F1 `relation-kind-taxonomy` (rejected: single-owned, no duplication)

- Contract + variation: five-shape cardinality classifier plus
the many-side set. Varies per field shape (CH1), kind
vocabulary (CH2), generic form (CH3).
- Sites + roles: definition at [relations][relations]; 16
consumer sites compose by name; oracles execute; projections
describe. No second definition.
- Challenges: CH1 count 1, CH2 count 1, CH3 count 1.
- Owner + lifetime: [relations][relations]. Dependency direction
is decisive (principle 7): [field-meta][field-meta] already
imports the owner, and `types/base.py` imports the stamp, so
moving the decision to the stamp would force the owner module
(`classify_path`, the lenient fallback, `is_forward_concrete_relation`)
to import the optimizer — a cycle. Pure derivation; the
cached snapshot slots (`FieldMeta`, `PendingRelation`) carry
definition lifetime and are rebuilt at class creation.
- Migration: none (rejection; zero edits).
- Distinct behavior: everything below stays separate at its
recorded home.
- Behavioral proof: static-reviewed (body reads over the full
sweep population plus oracle inspection). No ordering,
transactional, or async behavior exists here, so no execution
proof is owed.
- Structural gate: none, with reason. A syntactic census gate
cannot distinguish a bypassing classifier from the legitimate
flag/token uses this artifact enumerates (cascade predicates,
write screens, `WINDOWABLE` membership, resolver dispatch,
display labels); pinning "exactly one definition" would be the
bespoke existence test per helper the method forbids. The
population is open-ended, so no mechanical check can be both
sound and stable.
- Coupling: none.
- Freshness: fingerprints under `## Implementation (Worker 1)`.
- Principle 1: the family already declares the variation (the
`RelationKind` literal, the many-side table, one driver). No
second declaration to fold. Principle 11: deletion reviewed —
the set has no direct production importers but is the
predicate's table (principle 2, keep); the snapshot field is
introspection-carrying by documented intent (keep).

### Rejections (intentional separations, each with difference + trigger + home)

- R-A `WINDOWABLE_RELATION_KINDS` ([join-taxonomy][join-taxonomy]).
Difference: windowability is a fetch-strategy predicate, not
cardinality — reverse O2O is windowable (child carries the
parent id) yet single-valued, so it cannot derive from the
many-side set. Trigger: the fetch strategy stops distinguishing
them. Home: the set comment plus the module taxonomy table.
- R-B lenient taxonomy end-to-end (prior R1, re-derived, agreed).
Difference: needs `remote_field` (forward-M2M reverse query
name) and `through` (join table), neither carried on
`FieldMeta` by design, under a never-raises contract the strict
stamp cannot offer; local names already compose the shared
bodies (`lenient=True`). The interior `_parent_join_column`
raw-`one_to_many` read is this surface's own dispatch detail,
not a second taxonomy. Trigger: `FieldMeta` gains
`remote_field` / `through` carriage. Home: the "takes the RAW
Django relation field" clause.
- R-C strict/lenient read axis (prior R5, re-derived, agreed).
Difference: two failure policies, one read body — already
shared, not two families. Kept separate from R-B (read layer
vs classification-use layer). Trigger: a third policy. Home:
`relation_attr` docstring axis clause.
- R-D write decode kinds (`mutations/inputs.py::
model_column_write_kind`, `::relation_input_annotation` raw
`many_to_many`). Difference: coarser `RELATION_MULTI` /
`RELATION_SINGLE` decode vocabulary over a forward-only
population — reverse relations fail loud before reaching it
(the `mutation_input_field_specs` screen) and the generator
selects forward columns only, where the raw read and the
taxonomy agree; reasons to change are decode-shape, not
rendering. Routing through the taxonomy would couple the write
family to kind strings without relieving any change and would
risk turning contained `False` answers into strict-mode raises
(principle 8). Trigger: a forward collection-shaped relation
with `many_to_many=False` reaches the write path. Homes: the
`model_column_write_kind` docstring plus the fail-loud screen
body; the form-side `_model_column_for` population docstring.
- R-E serializer model cardinality (`serializer_converter.py::
_model_relation_cardinality`). Difference: DRF-alignment guard
vocabulary (`serializer_many` vs `model_many`) with
lenient-`getattr` failure policy; the taxonomy's strict reads
would raise where this must answer. Different reasons to
change (serializer shape vs GraphQL rendering). Trigger: a
model shape where flags and taxonomy disagree. Home: the guard
docstrings.
- R-F cascade edge predicates (`permissions.py::
_is_cascadable_edge`, `::_is_unsupported_forward_edge`).
Difference: single-column cascade composability
(`isinstance ForeignKey` + `column`, MTI link included,
multi-column and virtual shapes excluded/failing closed) —
answers which edges a one-column `__in` walk can compose, not
cardinality. Trigger: cascade needs beyond-forward-concrete
cardinality. Home: the predicate docstrings.
- R-G to-field predicate (`filters/base.py::
_relation_uses_non_pk_to_field`). Difference: join-column
question using the `many_to_one` flag the taxonomy never
reads. Trigger: `to_field` support beyond forward FK/O2O.
Home: its docstring.
- R-H column-presence screens (`orders/inputs.py`, `filters/sets.py`
M2M sweep, `rest_framework/resolvers.py` attestation,
`forms/resolvers.py` M2M names). Difference: each answers a
local "backed by what" question (orderable columns, sweep
exclusion, attested state), never "which kind". Trigger: any of
them needs reverse-kind precision. Homes: their docstrings.
- R-I projections (`_RELATION_KIND_LABELS`,
`PendingRelation.relation_kind` snapshot). Difference: display
names and an introspection copy with no production readers by
documented intent. Trigger: a production reader of the copy
appears. Homes: the labels comment and the record docstring.
- Raw kind-token comparisons (`resolvers.py`
`reverse_one_to_one` dispatch, `connection.py` /
`is_forward_concrete_relation` `forward_single` screens,
`join_taxonomy.py` `generic` arm) are USES of the shared
vocabulary where `is_many_side` lacks the needed precision,
not definitions. Listed, not counted, no home owed beyond the
owner.

## Defects

None. Every asymmetry was checked against a contract source:
the defensive fallback is test-pinned; the write-path raw
reads are enforced forward-only by the fail-loud screen; the
strict/lenient split is stated at the owner. No missing guard,
no security, routing, authorization, or data-exposure question.

## Pending execution

None. Every proof is static-reviewed over the sweep population
and oracle bodies; the rule is pure derivation with no
ordering, transactional, or async surface, so no workspace
proof and no shared-tree test run is owed.

## Judgment

Single authoritative definition; count 1 on all three
variation axes. No inline second classifier exists anywhere in
the package. Every neighbor is a consumer composing by name, a
distinct contract with its own reasons to change, or a
projection. R1/R5 stay separate (different layers). No gate is
justifiable without becoming a bespoke existence test. Outcome:
reject the consolidation, zero edits, rejections recorded with
triggers and homes.

## Independent verification (Worker 2)

Re-derived from independent whole-package sweeps (mechanism
vocabulary, `isinstance` chains over relation classes, flag
reads, generic slots, `def` census) plus opening every
candidate body below — not from the Findings text. Reconciliation
per claim follows the trace.

### Own classifier sweep (every candidate site + verdict)

Definition (1): `utils/relations.py::relation_kind` (the only
`def relation_kind` decision body in the package) +
`::is_many_side_relation_kind` + `::MANY_SIDE_RELATION_KINDS`
(one trio, one module, one edit site). The `def` census finds
exactly one other `relation_kind` spelling —
`optimizer/field_meta.py::FieldMeta.relation_kind` — whose body
is the one-line delegate `return relation_kind(self)`: a
consumer by construction, not a second decision. No other
`def` maps flags to the five-kind vocabulary.

Consumers composing by name (each opened; each reads
`relation_kind` / `is_many_side_relation_kind` /
`FieldMeta.relation_kind` / `FieldMeta.is_many_side`, never
re-derives the five flags into kinds): `field_meta.py`
(`_from_field_shape` computes `kind` once via the owner and
gates nullable/elision on it; its own raw flag reads populate
snapshot carriage slots, and the `attname` drop keys on
`concrete`/`many_to_many` column-backing, not kind);
`walker.py::plan_relation` + the `force_select` guard;
`join_taxonomy.py::classify_relation_join` (lenient call with
documented never-raises fallback); `plans.py` /
`nested_planner.py` shims over the join classifier;
`extension.py::plan_relation` (delegate to the walker);
`converters.py::resolved_relation_annotation`,
`types/base.py` relation-shape validation,
`types/resolvers.py` dispatch (incl. the `reverse_one_to_one`
arm and the `_check_n1` kind probe),
`types/finalizer.py` connection synthesis (all via
`FieldMeta` slots); `filters/sets.py::
_relay_filter_class_for_field`; `connection.py::
_resolve_order_path_field` (`forward_single` screen);
`inspect_django_type.py` relation rows; interior owner uses
(`classify_path`, `_lenient_traverses_to_many`,
`is_forward_concrete_relation`).

Classify-or-consume verdicts for every second-classifier
suspect: (a) no inline `isinstance` chain classifies kinds
anywhere — the `isinstance` hits are `filters/sets.py` (filter
TABLE keyed by `ManyToManyField`/`OneToOneRel`/`ManyToOneRel`/
`ManyToManyRel`, the upstream django-filter vocabulary, plus
the M2M sweep exclusion), `permissions.py`
(`ForeignObject`/`ForeignObjectRel` cascade-composability
predicates), `utils/querysets.py` (retained-schema bases, not
relation logic), `mutations/inputs.py`
(`FileField`/`ImageField`, unrelated); (b) flag reads used AS
classification: none — `mutations/inputs.py`
(`model_column_write_kind` / `relation_input_annotation` /
index arms) answer write-decode over a forward-only
population where raw reads and taxonomy agree, and disagree
outside it (`GenericRelation` is taxonomy-many-side but
write-single) with decode-shape reasons to change;
`serializer_converter.py::_model_relation_cardinality`
(`many_to_many or one_to_many`) is a DRF-alignment guard with
a lenient answer policy the strict taxonomy cannot offer;
`permissions.py` cascade predicates answer single-column
`__in`-composability (`ForeignKey` + `column`); `filters/base.py`
to-field predicate reads `many_to_one`/`one_to_one`, a flag
the taxonomy never touches, for a join-column question;
`orders/inputs.py` / sweeps / attestation / `_model_column_for`
answer local column-backing; `join_taxonomy.py::
_parent_join_column` raw `one_to_many`/`many_to_many` reads
are that surface's own connector dispatch keyed off the
already-computed `kind`, not a kind decision; generic-slot
reads outside the owner are `field_meta.py` snapshot carriage
(feeds the owner, raw/snapshot parity) and `join_taxonomy.py::
_generic_child_attname` (child-column resolution, consumes
`kind`); (c) kind-token comparisons (`reverse_one_to_one`
dispatch, `forward_single` screens, `generic` arm) and
`WINDOWABLE_RELATION_KINDS` membership are USES of the shared
vocabulary where `is_many_side` lacks precision, not
definitions.

### Consolidation search result

Searched independently for a real consolidation; none exists.
The nearest misses all fail the shared-responsibility test:
`_model_relation_cardinality` vs the many-side predicate
(agrees on stock shapes, must diverge by policy —
lenient-answer vs strict-raise — and by reason to change);
`model_column_write_kind` vs the taxonomy (coarser
`RELATION_MULTI`/`SINGLE` decode vocabulary, forward-only by
the fail-loud screen; routing it through kind strings couples
the write family without relieving any change and risks
turning contained `False` into strict raises — principle 8);
`_parent_join_column` vs `relation_kind` (join-column vs
cardinality contracts); the `filters/sets.py` class-keyed
filter table vs kinds (upstream filter vocabulary vs
rendering). Each stays separate with its difference, trigger,
and home as recorded. No production edit owed.

### Gate judgment (challenge focus 3)

Judged hard against the logger precedent
(`dry-rule-logger-single-sourcing.md`: `getLogger` count over
117 files). Three candidate gates considered and rejected with
reasoning, not on assertion:

- G1 "exactly one `def relation_kind`": a bespoke existence
  test per helper, which DRY.md forbids outright; and unsound
  — a genuine bypass would never reuse the name, it would be
  an inline flag/`isinstance` chain in different vocabulary
  (the exact shape this item's suspects take).
- G2 "no `isinstance(*, *Rel/*Field)` outside
  `utils/relations.py`": born red — legitimate sites exist
  today (`filters/sets.py` table keys + sweep,
  `permissions.py`, `utils/querysets.py` retained bases).
  Curing it needs per-helper carve-outs, i.e. bespoke
  assertions.
- G3 "every `many_to_many`/`one_to_many` read outside the
  taxonomy is allow-listed": same defect — legitimate
  multi-flag readers exist today with distinct contracts
  (serializer R-E reads two flags; `_parent_join_column`
  reads two flags plus `kind`; cascade reads three). Any
  token threshold is arbitrary, needs the same allow-list,
  and is unsound anyway: a bypass can read through the
  shared `relation_bool` like every consumer does.

The disanalogy with the logger is load-bearing: `getLogger`
is a closed population (exactly one way to acquire a logger,
exactly one legitimate site, AST census with per-region
identity + cardinality + negative control). The relation-flag
vocabulary is pervasive with dozens of legitimate uses
answering different contracts, so the bypass population is
open-ended and cannot be enumerated with per-region identity
+ cardinality without bespoke per-helper assertions. No
machinery is demanded for its own sake; no sound stable gate
exists. W1's no-gate outcome ACCEPTED with this reasoning.

### Per-claim agreement / difference

Agreed on all W1 claims: 1 definition trio; no inline second
classifier; CH1/CH2/CH3 each count 1 (CH2's function-plus-
table edit is one site in one module — the predicate reads
the table — so count 1 stands); owner `utils/relations.py`
(dependency direction verified: `field_meta.py` imports the
owner, `types/base.py` + `converters.py` + `definition.py` +
`resolvers.py` + `finalizer.py` import the stamp, the owner
imports only exceptions + Django — moving the decision to the
stamp cycles `classify_path`/fallback/`is_forward_*` into the
optimizer); all 9 separations R-A..R-I with difference +
trigger + home (every home opened and existing: join-taxonomy
table + set comment + raw-field clause; `relation_attr`
axis clause; write-kind docstring + fail-loud screen +
`_model_column_for` population docstring; serializer guard
docstrings; cascade predicate docstrings; to-field docstring;
column-screen docstrings/comments; labels comment +
`PendingRelation` snapshot docstring stating production reads
live `FieldMeta`); R1/R5 stay separate (read body vs
classification-use layers, re-judged); zero edits; no
defects (every asymmetry contract-sourced; none found
independently either).

### Fingerprints, diff, execution

Freshness re-hashed (`git hash-object`, worktree): all 26
W1-listed blobs match exactly, including the three dirty ones
(`forms/inputs.py` `436fcf42…`, `filters/sets.py` `4a40e51b…`,
`connection.py` `3c4d5dcb…`) and all three oracles
(`test_relations.py` `37db9b64…`, `test_field_meta.py`
`5212e936…`, `test_join_taxonomy.py` `481294c3…`); no
fingerprint changed, nothing reopens. Item-scoped diff
confirmed empty: `git diff 80f68092… -- django_strawberry_framework
tests` prints nothing — the zero-edit result holds, and per
AGENTS.md prose the `git status` dirt vs HEAD is concurrent
work: the three dirty member files' hunks (connection
cursor-guard, filters declared-filter guard, forms basis
guard) were spot-checked to sit outside every family site
and are left alone, never reverted. `## Pending execution`
stays empty, judged: the rule is pure derivation (flag reads
plus contained truth tests; no ordering, transactional, or
async surface), every proof is static review over the sweep
population plus oracle bodies, so no workspace proof and no
shared-tree run is owed. No `.py` touched: no `ruff` input.

## Defects

None. (Worker 2: none found; no `(Worker 2)` entries.)

## Pending execution

None (Worker 2 confirms: pure derivation, nothing deferred).

## Judgment (Worker 2)

`Status: verified`. Single-owned taxonomy, REJECT with the 9
recorded separations; no gate justifiable (reasoning above);
zero edits; no pending execution.

Plan rows for Worker 0: tick Family `relation-kind-taxonomy`
(this artifact); responsibility-index row
``relation-kind-taxonomy`` `open` → `rejected`; no sub-rule
decomposed, so no new index rows.

## Implementation (Worker 1)

No tracked changes. Production and test trees untouched
(`git diff <item-baseline> -- django_strawberry_framework/
tests/` empty for this item's paths); this artifact is the
only new file (untracked). No `ruff` input (no `.py` touched);
scaffold follows the canonical 10-header link-definitions
layout. Scratch paths: none created. No tool output pasted.

Item-scoped diff state: dispatch `ITEM_BASELINE=80f68092`
vs worker-open `1dec9695` drift is concurrent test/doc edits
only — every member path below confirms clean-or-attributed.

Attribution stop-rule check: `connection.py` worktree
`3c4d5dcb` vs HEAD `93e998f2` hunks are the cursor-guard
feature (import, `_offset_cursor_prefix` /
`_reject_negative_offset_cursor`, fallback branch); the family
site (`_resolve_order_path_field`, `relation_kind` screen) is
outside every hunk — left alone, no edit made. `filters/sets.py`
worktree `4a40e51b` vs HEAD `4ab65a26` hunk is the declared-filter
form-key guard, far from `_relay_filter_class_for_field` —
left alone. `forms/inputs.py` hunk is the `_form_field_basis`
`isinstance` guard, far from `_model_column_for` — left alone.
All other member files are clean (worktree == HEAD).

Freshness fingerprints (`git hash-object`; `HEAD:` shown where
the worktree is dirty):

- `utils/relations.py` `7662b0bb669c4dfba4a437f3b8f309357f718dca`
- `optimizer/field_meta.py` `7215c887aa26b1d828503ca30dd3b02546fe68b3`
- `optimizer/walker.py` `9b111ed938951a073a9226ccbcfacabc3af981e8` (incl. ledgered D1 fix)
- `optimizer/join_taxonomy.py` `9b355a5090ce471e373849dd0a61da8f808e78b9`
- `optimizer/plans.py` `cce985319c8833f3660653327d3003f1f03655a5`
- `optimizer/nested_planner.py` `0ad8ff5d0ee1673e4d1fcbc5dd200a2bd7a87e04`
- `optimizer/extension.py` `49667a9370cef73fdf4a170fe9bafa3a1eb19a2a`
- `types/converters.py` `9ceb34afec591a554fd71b7b3f3b9eae4f37fa75`
- `types/base.py` `91c587477ff8257e80dbb9a9c79859f34c5b4c7e`
- `types/relations.py` `6bd7c63da7787c61624960dd8060f67671c03d44`
- `types/resolvers.py` `f3341e6a9f52659925762bce097033bac67e3b51`
- `types/finalizer.py` `77fd9a2dd229eb9de5f29188c5058035d3606323`
- `management/commands/inspect_django_type.py` `46dffb3db4dcd0cd47e4b7cd91b575fbed9d5c7d`
- `mutations/inputs.py` `fc4420475f404297822d7d94bee7bdd275700803`
- `permissions.py` `757dce34cecd7a249b2634947a771d4608808bfe`
- `filters/base.py` `ba52351c284425336262ae6c2b82b262f6586fc0`
- `orders/inputs.py` `6f6ec946351fb56d92637a3c7e75a9fd8fc0b516`
- `rest_framework/serializer_converter.py` `32904418a169941c2afa1c9cd6866c55debc64f3`
- `rest_framework/resolvers.py` `8024703ec0fb09758daeec0585e0065de1c61fc3`
- `forms/inputs.py` worktree `436fcf428933c824fffefc44c0044557ca803446`; `HEAD:` `55614839ff479b3610b6026be65f2107ee560fcd`
- `filters/sets.py` worktree `4a40e51b288cad04cce3124697874c399d33f0fc`; `HEAD:` `4ab65a26b0ccf56f7f40f4938282bba9690673d1`
- `connection.py` worktree `3c4d5dcb4b6931d8a588c1d23ed9675b98d6742a`; `HEAD:` `93e998f2c7ea1d7f18607a6e37e394466ac75ad4`
- `utils/__init__.py` `1a4c2ec8bfd31ff7b55b337dfe405ffbd2f24cee`
- Oracles: `tests/utils/test_relations.py` `37db9b64c74756f5d300031513ee8008824a9ec9`; `tests/optimizer/test_field_meta.py` `5212e9368b98ad727eef684ee23d91d20d56532e`; `tests/optimizer/test_join_taxonomy.py` `481294c323dd0ef2e8f7bf974802858c3b5b428c`
- Searched population: whole `django_strawberry_framework/` mechanism sweep (triaged above); prior `field_meta.py` file-item census (112-hit lines) re-derived, R1/R3/R5 triggers re-checked fresh.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[join-taxonomy]: ../../django_strawberry_framework/optimizer/join_taxonomy.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
