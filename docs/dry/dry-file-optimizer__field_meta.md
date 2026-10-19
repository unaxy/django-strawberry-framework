# DRY review: `optimizer/field_meta.py`

Status: verified
Run: 0.0.15 2026-09-19-1

## System trace

Target [field-meta][field-meta] (350 lines) is the package's
relation-field vocabulary: the frozen `FieldMeta` snapshot stamped
once per `DjangoType` at class-creation time into
`DjangoTypeDefinition.field_map`, plus the two builders
(`from_django_field` entry guard, `_from_field_shape` shared shape
helper) and the `_target_pk_name` defensive pk reader. It owns the
stamp-time derivations (cardinality-gated nullable, attname
poison-drop, FK target-column record, elision conjunction,
reverse-connector + generic parity slots) and consumes the shared
relation readers (`utils/relations.py::relation_attr`,
`::relation_bool`, `::relation_name`, `::relation_kind`,
`::is_many_side_relation_kind`, `::instance_accessor`,
`::has_composite_pk`) and the typed-failure vocabulary
(`exceptions.py::OptimizerError`, `::_safe_type_name`) by name.

Sites found (whole-package search for `FieldMeta|field_meta|
from_django_field|_from_field_shape|_target_pk_name|
_DjangoFieldLike`, 112 hits): stamp producers `types/base.py`
(`field_map` build at class creation), walker fallback
(`walker.py::_resolve_field_map` unregistered path); shape-helper
co-consumer `types/resolvers.py::_field_meta_for_resolver` (test-
double fallback with `is_relation=True`); slot consumers
`walker.py` (elision branch, `target_pk_name` custom-id check,
`attname`/`related_model`/`accessor` reads),
`types/resolvers.py` (`_build_fk_id_stub`, many/single dispatch,
visibility), `types/converters.py::resolved_relation_annotation`,
`types/base.py::_build_annotations` (`PendingRelation` nullable +
kind), `types/finalizer.py` (resolve through `field_map`),
`types/definition.py` (`field_map` slot type),
`management/commands/inspect_django_type.py` (relation rows).
Raw-field neighbors that deliberately do NOT read `FieldMeta`:
`optimizer/join_taxonomy.py` (needs `remote_field`/`through`,
never-raises lenient mode), `optimizer/plans.py`
(`window_partition_for_prefetch` shim over the classifier),
`optimizer/nested_planner.py::_raw_relation_field` (same
`remote_field` reason, stated), `optimizer/extension.py` (never
imports it: plan-cache/walker-drive surface, not vocabulary).

Contract sources (authoritative definitions only): each neighbor's
module docstring + owning symbol body; `tests/optimizer/
test_field_meta.py` (33 tests) as oracle; `utils/relations.py`
docstrings for the shared readers.

## Verification

### Matrix

1. **Cross-flavor policy mirroring.** `FieldMeta` is flavor-free:
one stamp serves types, filters, orders, mutations, forms, REST
(all read `field_map` or the builders by name; no flavor spells
cardinality/nullable/attname locally). Whole-package search for
re-derived cardinality (`many_to_many|one_to_many|one_to_one`
outside `utils/relations.py` + this target + write-surface
`is_forward_many_to_many` predicates) finds only the documented
`join_taxonomy.py` lenient reads (R1) and write-surface predicates
with their own contracts. Discharged.
2. **Sync/async twins.** No such surface: zero `async def`, zero
`sync_to_async`, zero ORM I/O in the target. Pure dataclass +
attribute reads at stamp time; stamp runs at class creation or
inside the sync walk. Inapplicable by construction (nothing
awaits, nothing executes queries).
3. **Derived rather than repeated knowledge.** Every derivation
reads once here: nullable gate (FL3), attname drop (FL4),
target-column record (FL5), elision conjunction (FL6),
connector/generic slots (FL7). Walker/resolvers/converters/
finalizer/inspect read the slots, never recompute them, except
the two documented raw-field neighbors (R1/R2: `remote_field` /
`through` live only on the raw descriptor). `target_field_name`
has no external reader beyond the elision conjunction + tests;
kept as the derivation's observable input (FL5). Discharged.
4. **Inverse / round-trip pairs.** No such surface: stamp is
one-way (no un-stamp, no parse-back of a snapshot into a
descriptor). `field_map` keying (`snake_case` at stamp in
`types/base.py`, raw `f.name` in the walker fallback) coincides
for every Django field name; the walker snake-cases the lookup
side. No grammar with two halves. Discharged.
5. **Contracts restated in another medium.** Oracles:
`tests/optimizer/test_field_meta.py` (33 tests: shape pins,
guard pins, MTI, 5.2 M2M shape, walker-plan pins) asserts
behavior, never reads the owner's tables (imports callables to
execute them). Live HTTP suites pin the wire behavior the slots
drive. Module + slot docstrings state the rules; [tree][tree]
prose is projection. No restatement counted as definition.
Discharged.
6. **Enforcement by omission.** Enumerated the asymmetric
members; each is contract-stated, not a gap: scalar `nullable`
falls through to `field.null` (pinned by oracle, consumed only
on relation paths); `GenericForeignKey` stamps
`forward_single` with empty slots (excluded downstream by
`is_forward_concrete_relation`'s column/related-model gate);
`target_field_name` stored without an external reader (FL5
audit input); deferred-column safety lives at resolve time in
`_build_fk_id_stub`, not at stamp (R4). No member lacks a guard
its contract source requires. Discharged.

### Enumeration

Instrument: every name in `ast.Module.body` of [field-meta][field-meta].
Count: **10** top-level statements = 1 module docstring + 5
imports + 1 `TYPE_CHECKING` block + 2 classes + 1 def. Imports
and both docstrings carry no rule. Inner members:
`_DjangoFieldLike` = 1 docstring + 2 slots; `FieldMeta` = 1
docstring + 18 field slots + 4 methods. Every rule-bearing
member lands below in a family row (F-prefix, new name for
Worker 0 to add), a file-local row (FL-prefix), or a rejection
(R-prefix). No member unassigned.

Top-level (10): module docstring (projection, no rule);
`__future__`/`dataclasses`/`typing`/`exceptions`/`relations`
imports (no rule); `TYPE_CHECKING` block (no rule);
`_DjangoFieldLike` (FL1); `FieldMeta` (rows below);
`_target_pk_name` (FL5).

`_DjangoFieldLike` (3): docstring (projection); `name: str`,
`is_relation: bool` (FL1 input contract).

`FieldMeta` fields (18): `name` (FL2); `is_relation` (FL2);
`many_to_many`/`one_to_many`/`one_to_one` (F1 kind inputs);
`nullable` (FL3); `related_model` (FL5/FL6 input + consumers);
`attname` (FL4); `target_field_name`/`target_field_attname`
(FL5); `target_pk_name` (FL5); `fk_id_elision_eligible` (FL6);
`reverse_connector_attname` (FL7); `auto_created`/`concrete`
(F1 kind inputs + FL7); `accessor_name` (F2);
`content_type_field_name`/`object_id_field_name` (FL7, F1
generic inputs).

`FieldMeta` methods (4): `relation_kind` (F1);
`is_many_side` (F1); `from_django_field` (FL1);
`_from_field_shape` (FL2).

### Challenges

Authoritative definitions only (neighbor bodies + oracle
bodies); consumer / oracle / projection moves listed, never
counted. Read-only probes P1-P6 below ran in the shared tree
(`uv run python`, no source mutation); no shared-tree pytest
run (inspection beats execution on every row).

- C1 (kind taxonomy): posit a sixth `RelationKind` (new generic
shape). Definitions forced: **1** (`utils/relations.py::
relation_kind`; this file's `relation_kind`/`is_many_side`
properties compose it by name, flags flow through the stamp).
Probe P6: `relation_kind(raw) == fm.relation_kind` and
many-side parity hold on a forward FK. Consumers (walker
`plan_relation`, converters, finalizer, inspect) read the
property, never re-derive.
- C2 (accessor): posit a new reverse-naming rule (no
`related_name`). Definitions forced: **1**
(`utils/relations.py::instance_accessor`; stamp calls it once
on the raw descriptor, later reads hit the precomputed slot).
Probe P2: reverse-FK accessor resolves; walker plans the
prefetch lookup from `instance_accessor(FieldMeta)`.
- C3 (nullability): posit forward-FK `null=True` renders
nullable. Definitions forced: **1** (FL3 gate: many-side
kinds `False`, reverse O2O `True`, else `field.null`). Probes
P1 (non-null FK `False`), P4 (nullable scalar falls through
to `field.null`), oracle reverse-O2O test (`True`).
- C4 (attname): posit a new non-column shape keeps a real
column. Definitions forced: **1** (FL4 drop: non-concrete
or M2M `None`; duck-typed double without `concrete` keeps).
Probes P2/P3 (`None` on reverse FK and M2M), P5 (M2M double
drops even without `concrete`).
- C5 (FK target): posit a non-PK `to_field` relation.
Definitions forced: **1** (FL5 record: `target_field_name`
vs `target_pk_name` comparison feeds FL6; `_target_pk_name`
defensive `_meta` walk). Probe P1 (`id`/`id`, eligible);
oracle to-field tests pin ineligibility.
- C6 (input shape): posit a descriptor without `is_relation`
(resolver test double). Definitions forced: **1** (FL2 shared
builder; `from_django_field` reads `bool(is_relation)`,
`_field_meta_for_resolver` hard-codes `True`). Probe P5:
identical observable `FieldMeta` for the same flags.
- C7 (hostile input): posit a descriptor without `name` or
with a non-`str` name. Definitions forced: **1** (FL1 guard
`OptimizerError`, truth-test contained). Probes: both raise
`OptimizerError` with the typed message.
- C8 (pk read): posit a stand-in `related_model` without
`_meta`. Definitions forced: **1** (`_target_pk_name`
returns `None`, disabling elision, never raising). Probe:
`None` for `None`/bare/`_meta=None` inputs.
- C9 (generic parity): posit a `GenericRelation` snapshot.
Definitions forced: **1** (FL7 slots; duck-typed detector
reads non-`None` slots, never `hasattr`). Oracle generic
test: raw and snapshot both classify `generic`/many-side.

## Findings

### F1 `relation-kind-taxonomy` (family, consumer; NEW for Worker 0 to add)

- Contract + variation: GraphQL/runtime cardinality classifier
over the five Django relation flags, plus the many-side set.
Varies per field shape only.
- Sites + roles: definition at `utils/relations.py::
relation_kind` (+ `::is_many_side_relation_kind`, `::
MANY_SIDE_RELATION_KINDS`). This file: stamp-input consumer
(flags read via `relation_bool`/`relation_name`) + composing
consumer (`relation_kind`/`is_many_side` properties delegate
by name). Fellow consumers: `walker.py::plan_relation`,
`types/converters.py::resolved_relation_annotation`,
`types/finalizer.py`, `inspect_django_type.py`,
`optimizer/join_taxonomy.py`. Oracles: `tests/utils/
test_relations.py` + `tests/optimizer/test_field_meta.py`
(kind pins incl. MTI, 5.2 M2M, generic parity).
- Challenges: C1, count 1.
- Owner + lifetime: `utils/relations.py`; no stored
derivation here (properties compute per read; slots are the
classifier's inputs, owned under FL7). Pure derivation says
"not cached".
- Migration: none (file item; no consolidation here).
- Distinct behavior: `is_forward_many_to_many` /
`is_forward_concrete_relation` (same module) answer narrower
write-surface questions; untouched.
- Behavioral proof: static-reviewed + probes P1/P6
(parity raw vs snapshot, forward FK + M2M + O2O shapes).
- Structural gate: family item.
- Coupling: none.
- Freshness: [field-meta][field-meta] `7215c887`,
[relations][relations] `7662b0bb`, searched population whole
`django_strawberry_framework/` (112-hit census).

### F2 `relation-instance-accessor` (family, producer + consumer; NEW)

- Contract + variation: instance-attribute name for relation
rows (`book_set` vs query name `book`). Varies per reverse
relation without `related_name` only.
- Sites + roles: definition at `utils/relations.py::
instance_accessor` (three-tier: precomputed slot, then
`get_accessor_name()`, then `name`). This file: stamp-time
producer (calls it once on the raw descriptor into
`accessor_name`) + later reads compose by name (walker
prefetch lookups, `types/resolvers.py`, `connection.py`
all call the helper on `FieldMeta`). Oracles: reverse-FK
accessor test + live prefetch suites.
- Challenges: C2, count 1.
- Owner + lifetime: `utils/relations.py`; the slot is a
stamp-time cache with definition lifetime (rebuilt per
`DjangoType` creation; walker fallback rebuilds per
unregistered model). No invalidation story owed: stamp
inputs are class-creation stable.
- Migration: none. Distinct behavior: `field.name` stays the
GraphQL/optimizer-key vocabulary (stated at owner).
- Behavioral proof: static-reviewed + probe P2.
- Structural gate: family item. Coupling: none.
- Freshness: [field-meta][field-meta] `7215c887`,
[relations][relations] `7662b0bb`.

### FL1 field-shape input guard (file-local)

`_DjangoFieldLike` (`name` + `is_relation` Protocol) +
`from_django_field` guard: missing/unreadable attributes or a
raising truth test → `OptimizerError`; non-`str` name →
`OptimizerError`. Proving challenge C7: a new malformed shape
moves only this guard (typed stamp-time failure, never a late
`AttributeError` mid-walk). Second site searched (whole
package): none — `_field_meta_for_resolver` delegates to FL2,
never re-guards. Oracles: hostile/reject tests. Proof:
static-reviewed + hostile probes (both raise). No stored state.

### FL2 shared shape builder (file-local)

`_from_field_shape(field, *, is_relation, field_name=None)`:
the one body both entries share (`from_django_field` after
its guard; `_field_meta_for_resolver` with `is_relation=True`
for `is_relation`-less doubles). Proving challenge C6: a new
test-double shape moves only this helper; the observable
`FieldMeta` stays identical across entries (probe P5).
`field_name=None` re-read via `relation_attr` exists only for
the resolver fallback. No second builder in the package.
Proof: static-reviewed + P5. Lifetime: none stored.

### FL3 cardinality-gated nullable (file-local)

Many-side kinds → `False`; `reverse_one_to_one` → `True`;
else `field.null` (scalars fall through identically, pinned
by oracle). Proving challenge C3: a nullability change moves
only this gate; consumers (`converters.py`,
`PendingRelation.nullable`, inspect rows, walker elision
preconditions) read the slot directly per the module
docstring. No second nullable derivation (whole-package
search for `field.null` finds only stamp + scalar converter
paths with their own contracts). Proof: static-reviewed +
probes P1/P4 + oracle O2O pair.

### FL4 attname poison-drop (file-local)

Non-column relations stamp `attname=None`: positively
non-concrete OR many-to-many on any supported Django (5.2
reports forward M2M `concrete=True`, 6.1 `False`; the `or
is_m2m` arm covers the floor). Duck-typed doubles omitting
`concrete` keep `attname` (resolver-test-double contract).
Proving challenge C4: a new non-column shape moves only this
branch; the walker appends `attname` to `only_fields`
verbatim so a leaked name would poison the projection.
Consumers: `walker.py::_record_relation_access`,
`types/resolvers.py::_build_fk_id_stub`. Proof:
static-reviewed + probes P2/P3/P5 + 5.2-shape oracle test.

### FL5 FK target-column record (file-local)

`target_field_name` / `target_field_attname` (via
`target_field` slot reads, non-`str` → `None`) +
`target_pk_name` via `_target_pk_name` (defensive `_meta`
walk: `None` for missing `_meta`/`pk`/name, all errors
contained — the fabricated-shape resolver path needs it).
Proving challenge C5/C8: a target-column change moves only
this record; `target_field_name` has no external reader
beyond FL6 + tests and stays as the derivation's observable
input (deleting it would blind the to-field-vs-pk
comparison). Consumers of the rest: walker custom-id check,
`join_taxonomy.py` synthetic-double fallback
(`target_field_attname`). Proof: static-reviewed + probe P1
(`id`/`id`) + defensive-`None` probes.

### FL6 fk-id-elision eligibility (file-local)

Six-way conjunction: `attname` + `related_model` +
`target_pk_name` present, `target_field_name ==
target_pk_name`, `kind == "forward_single"`, no composite pk
(short-circuit order keeps hostile stand-ins from reaching
`has_composite_pk`, which raises typed errors by its own
contract). Proving challenge C5: a new eligible shape (e.g.
composite-pk support) moves only this conjunction.
Consumers: `walker.py::_plan_select_relation` elision branch
(+ custom-qs/id-resolver/id-only gates there, each owned
elsewhere). Resolve-time deferred safety is R4, not here.
Proof: static-reviewed + probe P1 (`True` on plain FK) +
oracle edge-case tests.

### FL7 connector + parity slots (file-local)

`reverse_connector_attname` (`field.field.attname`),
`content_type_field_name`/`object_id_field_name` (via
`relation_name`), `auto_created`/`concrete` passthrough.
Proving challenge C9: a new parity slot moves only this
stamp; the duck-typed `relation_kind` detector reads
non-`None` slots (never `hasattr`, since the slotted
dataclass always carries them) so raw and snapshot classify
identically. Consumers: `join_taxonomy.py` fallbacks
(connector + synthetic doubles), generic partition/attach
via kind. Flags double as F1 classifier inputs through
`relation_bool`, never direct reads. Proof:
static-reviewed + oracle generic test.

### Rejections

- R1 join-taxonomy raw reads. Considered: routing
`join_taxonomy.py` (`_safe_getattr`/`_safe_flag` flag reads,
`remote_field`/`through` walks) through `FieldMeta`.
Difference: the taxonomy needs `remote_field` (forward-M2M
reverse query name) and `through` (M2M join table), neither
carried on `FieldMeta` by design, under a never-raises
lenient policy the strict stamp cannot offer; its local
names already compose the shared bodies
(`relation_attr`/`relation_bool` `lenient=True`, stated at
both owners). Change C4/C9 moves exactly one side.
Trigger: `FieldMeta` gains `remote_field`/`through`
carriage — then re-check. Home:
`optimizer/join_taxonomy.py` (durable: module docstring
"takes the RAW Django relation field" clause).
- R2 plan shims + raw resolve. Considered: feeding
`plans.py::window_partition_for_prefetch` and
`nested_planner.py::_raw_relation_field` from `FieldMeta`.
Difference: same `remote_field` carriage gap (R1) plus the
shim's historical raise contract over the classifier.
Trigger: R1's trigger. Home: `optimizer/plans.py`
(docstring "Takes the RAW Django relation field" clause)
and `optimizer/nested_planner.py::_raw_relation_field`.
- R3 pk-name read vs `orm-lookup-path-resolution`.
Considered: unifying `_target_pk_name` (single pk-name
defensive read for elision) with `utils/relations.py::
classify_path` (multi-segment strict classification with
the lenient fallback ladder). Difference: one answers "the
target pk NAME or `None`" failing closed; the other answers
"the immutable hop plan" raising typed errors — same
`_meta` neighborhood, different contracts, no shared body
(trigger checked fresh this item; the adjacent family stays
open at its own item). Trigger: elision needs a
multi-segment path — then compose `classify_path` by name.
Home: family `orm-lookup-path-resolution`.
- R4 resolve-time stub guard vs stamp flag. Considered:
unifying `types/resolvers.py::_build_fk_id_stub`
(deferred-column + `None`-id + stub-build fallbacks at
resolve time) with FL6 (eligibility at stamp time).
Difference: different lifetimes — a consumer `.only()`
can drop the FK column after the plan elided the join
(spec-035 Decision 5), so the column must be re-checked
per row; the stamp cannot see it. Trigger: deferred state
becomes stamp-visible — then re-check. Home:
`types/resolvers.py::_build_fk_id_stub` (docstring B2
clause).
- R5 strict/lenient read policy. Considered: merging the
strict stamp reads here with the lenient taxonomy reads
(R1). Difference: two failure policies, one read body —
already recorded at the owner (`utils/relations.py::
relation_attr` docstring: "the only axis on which the two
surfaces differ ... share one read body"). Trigger: a third
policy — then extend the `lenient` axis, never a copy.
Home: `utils/relations.py::relation_attr`.
- R6 non-memberships (checked, not inherited):
`optimizer-execution-frame` (zero frame imports; stamp
runs at class creation, not in an execution);
`plan-cache-key-and-two-tier-memo` and walker-drive
planning (`optimizer/extension.py` never imports this
module — vocabulary vs drive, verified by the 112-hit
census); `one-sync-boundary` (zero ORM I/O). The
extension item (`plan-cache/walker-drive surface`) and the
`orm-lookup-path-resolution` family (path walks) were both
re-checked fresh as adjacent triggers; neither gains a site
here.

## Defects

None found while tracing. Every asymmetry checked against a
contract source in the body or an oracle test: scalar
`nullable` fall-through (oracle-pinned), GFK
`forward_single`-with-empty-slots (gated downstream by
`is_forward_concrete_relation`), `target_field_name`
write-mostly audit slot (FL5), deferred-column lifetime
split (R4), `has_composite_pk` typed raise inside the
short-circuited conjunction (stamp-time typed failure is
the documented contract). No guard any contract source
requires is missing; no security, routing, authorization,
or data-exposure question arose.

## Pending execution

None. Every proof is static-reviewed (call-site census over
the 112-hit whole-package search, body inspection) plus
read-only probes P1-P6 (`uv run python` against the live
package, no source mutation, no database write). No
shared-tree pytest run was needed (inspection beats
execution on every row); no workspace mutating proof was
needed (nothing order-, transaction-, or async-behavioral).

## Judgment

Zero-edit file item. All 10 top-level members assigned: 2
new family-consumer rows named for Worker 0 (`F1
relation-kind-taxonomy`, `F2 relation-instance-accessor`),
7 file-local rows each with its proving challenge (FL1-FL7),
6 rejections with differences + triggers + durable homes
(R1-R6). No consolidation lives in a file item; the raw-
field taxonomy, the plan shims, the stub guard, and the
read-policy axis stay separate by recorded intent. Target
clean at open and at close; no production edit made or owed.

## Implementation (Worker 1)

No tracked changes. Target [field-meta][field-meta]
untouched (worktree blob `7215c887` at open and close;
`git diff HEAD -- django_strawberry_framework/optimizer/
field_meta.py` empty; `git diff
7aade5843b4b80a938e0e2037017e2c8c4034b14 -- <same path>`
empty). No tests added (oracles already pin every row at
the mandated tiers: 33 package tests + live HTTP suites).
No `ruff` run needed (no edits). No commit (maintainer
only). Item-scoped diff: empty for production paths; this
artifact is a new untracked file only. Scratch:
`docs/dry/temp-tests/dry-file-optimizer__field_meta/`
(probes ran inline; dir holds no files).

## Independent verification (Worker 2)

Run `0.0.15 2026-09-19-1` at pinned HEAD `bfaee91d`.
Own trace recorded from the target + whole-package reads before
reconciling with `## Findings` below (artifact was on disk; no
`worker-memory/` read).

Own trace (sites, roles, counts, owner I would choose):

- Target `django_strawberry_framework/optimizer/field_meta.py` (350
  lines): frozen `FieldMeta` stamp + `from_django_field` guard +
  `_from_field_shape` shared builder + `_target_pk_name` defensive
  pk reader + `_DjangoFieldLike` input contract. Stamp-time only:
  zero `async def`, zero `sync_to_async`, zero ORM I/O (verified by
  read). Consumers read slots by name; nothing here executes queries.
- Cross-file producers: `types/base.py::field_map` build
  (`FieldMeta.from_django_field` at class creation),
  `optimizer/walker.py::_resolve_field_map` unregistered fallback
  (same builder). Co-consumer of the shared builder:
  `types/resolvers.py::_field_meta_for_resolver` (`is_relation=True`
  hard-code for `is_relation`-less doubles). Slot consumers:
  `optimizer/walker.py` (`target_pk_name`, `fk_id_elision_eligible`,
  `related_model`, `attname` slot reads; `instance_accessor`
  called on the `FieldMeta` at the prefetch-lookup site),
  `types/resolvers.py` (`relation_kind`, `is_many_side`,
  `attname`/`related_model` slot reads; `instance_accessor` on the
  raw field), `types/converters.py::resolved_relation_annotation`
  (slot read), `types/finalizer.py` (resolve through `field_map`;
  `instance_accessor(raw field)` for the synthesized connection
  resolver's `accessor_name` arg), `types/definition.py`
  (`field_map` slot type),
  `management/commands/inspect_django_type.py` (relation rows via
  `relation_kind`/`is_many_side`/`nullable`). Raw-field neighbors
  that must stay raw: `optimizer/join_taxonomy.py`
  (`remote_field`/`through`, lenient never-raises mode),
  `optimizer/plans.py::window_partition_for_prefetch` shim,
  `optimizer/nested_planner.py::_raw_relation_field`,
  `optimizer/extension.py` (never imports this module).
- Oracles: `tests/optimizer/test_field_meta.py` (33 `def test_`
  counted) asserts behavior by executing callables
  (`fm.relation_kind`, slot pins, guard pins, MTI, 5.2 M2M,
  generic parity); never reads the owner's tables. Live HTTP
  suites pin the wire behavior the slots drive. Prose
  (module + slot docstrings, `TREE.md`) is projection.
- Posited changes, definition counts (authoritative only):
  C1 sixth `RelationKind` -> 1
  (`utils/relations.py::relation_kind`; properties compose by
  name); C2 new reverse-naming rule -> 1
  (`utils/relations.py::instance_accessor`; stamp calls once,
  walker later hits the precomputed slot tier); C3 FK
  `null=True` renders nullable -> 1 (FL3 gate); C4 new
  non-column shape -> 1 (FL4 drop); C5 non-PK `to_field` -> 1
  (FL5 record feeds FL6); C6 `is_relation`-less double -> 1
  (FL2 shared builder); C7 malformed descriptor -> 1 (FL1
  `OptimizerError` guard); C8 `_meta`-less stand-in -> 1
  (`_target_pk_name` returns `None`); C9 `GenericRelation`
  snapshot -> 1 (FL7 slots; duck-typed detector reads
  non-`None` slots). Owner I would choose per case: F1/F2 at
  `utils/relations.py` (`relation_kind`, `instance_accessor`
  — narrowest cohesive owner every consumer can import
  without reversing a dependency); FL1-FL7 here (stamp-local
  derivations with no second site).

Enumeration (member-by-member vs own AST count): `ast.Module.body`
= 10 (1 module docstring + 5 imports + 1 `TYPE_CHECKING` block +
2 classes + 1 def) — matches. `FieldMeta` body = 23 (1
docstring + 18 field slots + 4 methods) — matches. Every
rule-bearing member is assigned: F1 (kind flags +
`relation_kind`/`is_many_side`), F2 (`accessor_name`),
FL1 (`_DjangoFieldLike` + `from_django_field` guard), FL2
(`_from_field_shape` + `name`/`is_relation`), FL3 (`nullable`),
FL4 (`attname`), FL5 (`related_model`/`target_*` +
`_target_pk_name`), FL6 (`fk_id_elision_eligible`), FL7
(`reverse_connector_attname`/`auto_created`/`concrete`/
generic slots). No member unassigned. Imports + docstrings +
`TYPE_CHECKING` carry no rule — agreed.

Matrix judged against the real surface: (1) cross-flavor —
agreed discharged (flavor-free stamp; only documented
`join_taxonomy.py` lenient reads + write-surface
`is_forward_many_to_many`/`is_forward_concrete_relation`
predicates with their own contracts, verified by read);
(2) sync/async — agreed inapplicable by construction (zero
await/ORM surface above); (3) derived knowledge — agreed
discharged (every derivation reads once here; walker reads
the `attname` *slot* via the `FieldMeta`-typed
`django_field`, not the raw descriptor; scalar
`field.null` paths in `converters.py` are separate
contracts); (4) round-trip — agreed none (one-way stamp,
`snake_case` keying coincides); (5) other-medium — agreed
discharged (oracles execute, never mirror owner tables;
checked `test_field_meta.py` imports/behavior pins);
(6) omission — agreed discharged (scalar fall-through,
GFK `forward_single`-with-empty-slots gated downstream by
`is_forward_concrete_relation`, write-mostly
`target_field_name` kept as FL6's observable input,
deferred-column split at resolve time — each contract-stated).

Definition counts + roles confirmed; no oracle rewritten to
read its owner (spot-checked `relation_kind` pins go through
`fm.relation_kind`). Principle-8: zero-edit item, so no
observable behavior to preserve; static review + read-only
probes are adequate for this stamp-time vocabulary file
(nothing ordering-, transaction-, or async-behavioral; no
database/alias/dialect path, so no sharded/Postgres cell
owed). `## Pending execution` none — agreed (no
`execution-deferred` proof owed; no mutating proof needed).

Zero-edit file item: coverage + assignment validated; no
production edit owed or demanded. Candidates routed: F1
`relation-kind-taxonomy` and F2 `relation-instance-accessor`
to their holding families (both already indexed as `open`);
R3 `orm-lookup-path-resolution` adjacency re-checked fresh
(`_target_pk_name` single pk-name failing-closed read vs
`classify_path` multi-segment strict plan — different
contracts, no shared body) and correctly left open at its
own item.

Rejections carry difference + trigger + durable home:
R1/R2 (`remote_field`/`through` carriage gap; homes at the
stated `RAW field` docstring clauses — verified present),
R3 (above; home at the open family — legitimate interim
route for a file item, durable sentence owed at the family),
R4 (stamp-time eligibility vs resolve-time deferred check,
different lifetimes; home at `_build_fk_id_stub` B2 clause
— verified present), R5 (strict vs lenient failure policy;
home at `utils/relations.py::relation_attr` docstring,
which already states the axis — ownership is correct, not
split: the stamp is a consumer of that policy, the owner
holds it), R6 (non-memberships checked: `extension.py`
never imports this module per 112-line census,
`optimizer-execution-frame`/`one-sync-boundary` have zero
surface here). All triggers are the change that would make
the sites one rule.

Freshness re-hashed: `field_meta.py` worktree `7215c887…` ==
`HEAD:field_meta.py` (matches artifact); `utils/relations.py`
`7662b0bb…` == HEAD (matches); searched population 112
lines with hits (recomputed: 112 lines / 144 matches —
artifact's `112-hit census` = lines, confirmed);
`consumers.py` / `extensions/error_policy.py` /
`list_field.py` / `schema.py` / `utils/querysets.py` each
count 0 in the artifact (exact-path grep) — the
`9031cb3d`..`bfaee91d` package drift touches no finding.
Item-scoped diff empty (`git diff 23d4c90d… --
optimizer/field_meta.py` and `git diff HEAD -- <same>`
both empty); artifact is new untracked file only
(`?? docs/dry/dry-file-optimizer__field_meta.md`).
`connection.py` concurrent cursor-guard hunk
(`_offset_cursor_prefix` / `_reject_negative_offset_cursor` /
fallback branch) touches none of the fingerprinted sites
(`accessor_name` resolver at `2120+`, `relation_kind` at
`868`, no `instance_accessor` import) — call site untouched,
correctly left alone. Owned-changes ledger (`walker.py` D1
fix + 2 live test files) touches none of this item's paths
— confirmed by content.

Structural gates (`family item` for F1/F2): deferral is
legitimate, not a gap. A file item owes no consolidation
and must not invent a bespoke existence test per helper
(`DRY.md` "never a bespoke existence test per helper");
the single-owner gate with its negative control belongs to
the family item holding all sites, both of which are
`open` in the plan. No `gate-only` finding is claimed here.

`AGENTS.md` prose on the (empty) diff: no process
provenance, `path::Symbol` citations throughout, tests at
the mandated tiers (33 package tests + live HTTP suites;
no new example model needed). No `ruff` run owed: zero
touched production/test paths, so `ruff check` /
`ruff format --check` have no input; state-only, no edit.

Defects: none found by Worker 2. Asymmetries re-checked
against contract sources; no missing guard, no security /
routing / authorization / data-exposure question.

Verdict: `verified` (zero edits, no pending execution).
One wording note (not a defect): F2's "connection.py all
call the helper on `FieldMeta`" overreads — `connection.py`
itself receives `accessor_name` while
`types/finalizer.py::finalize_django_types` calls
`instance_accessor(raw field)` for it; the helper-on-
`FieldMeta` (precomputed-slot tier) is exercised by the
walker prefetch-lookup path. Single definition still holds.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
