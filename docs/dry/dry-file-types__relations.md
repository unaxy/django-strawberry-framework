# DRY review: `types/relations.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target [types-relations][types-relations] at HEAD blob
`5e9b5cdbc7fb` (61 lines; worktree hash identical — CLEAN, no
hunt dirt, no ledger row; traced at shared-tree bytes throughout,
nothing tracked touched). The module owns two things: the
`PendingRelation` identity record (5 slots, frozen, `eq=False`)
every auto-synthesized relation field is collected into, and the
`PendingRelationAnnotation` sentinel (with its repr-shaping
metaclass) installed in `__annotations__` until finalization
rewrites it. It owns no list, no drain, no guard: the list and its
removal keys belong to verified `type-registry-pending-ledger`
(registry F3), the sole construction + install flow to
[types-base][types-base] `_build_annotations` /
`__init_subclass__`, the sole resolve + drain + rewrite to
[types-finalizer][types-finalizer] Phase 1, the rewrite shape to
[types-converters][types-converters]`::resolved_relation_annotation`.
Connected-file `:NNN` cites below index worktree bytes (hunt
dirt shifts them vs HEAD; every relied-upon region was verified
count-identical at HEAD — 20/20 checks); target `:NNN` cites
are stable (CLEAN).

Sites found (`D` = definition, `C` = consumer, `O` = oracle, `P` =
projection). Record shape: this file :19–41 (the one `D`;
`eq=False` is unique package-wide — census 1). Sole production
construction: [types-base][types-base] :1963 (1 site, `C`); sole
production `add_pending_relation(` call :818 (1 line, same flow,
`C`). Sole install of the sentinel: base :1971 (1 line, `C`);
sole rewrite: [types-finalizer][types-finalizer] :898 (1 line, `C`,
via `resolved_relation_annotation` with `field_meta` from
`definition.field_map[pending.field_name]` at :883). Ledger triple
+ `_pending` touches in [registry][registry] exactly as the
verified family records (construct :131, unregister rebind
:336–337, append :528, read :541, discard rebind :554, clear
:616 — all `C` of the record type, `D` of the ledger). Sole
`resolved_relation_annotation(` production call is the rewrite
line (converters :39 is its own docstring bullet). Oracles:
[test-relations][test-relations] (5 tests: non-hashable hash,
set membership, equal-valued twins distinct, sentinel repr
literal, frozen — all independent literals, never owner reads);
[test-registry][test-registry] :323/:603/:924/:953/:1767 (clear,
consumer-authored discard, atomicity pair, identity match,
unregister subset); [test-definition-order][test-definition-order]
:230 (unresolved-target wording); [test-base][test-base] :1731–1732
(sentinel install + repr substring);
[test-finalizer][test-finalizer] :43/:74 (missing-field-metadata
raise, missing-definition typing);
[test-gfk][test-gfk] :28 (declaration-time GFK raise, no record).
Projections: the module + 3 class docstrings (each clause verified
against its owning body below), [spec-010][spec-010] (scaffolding
shape), [spec-018][spec-018] (import-order trap closure),
[goal][goal] (loud failure + the no-placeholder non-goal), the
`utils/relations.py` kind-vocabulary parenthetical (STALE — D1).

Connected behavior examined: the base producer region (field_map
build :634, construction :795–820, deferral branch :1955–1972),
the finalizer Phase-1 loop + formatters (:95–140, :855–905), the
registry ledger (:125–135, :330–340, :525–556, :610–620), the
rewrite entry (converters :756–770), the field_map ownership
contract ([types-definition][types-definition] invariant prose +
slot :162), the resolvers runtime sentinels
([types-resolvers][types-resolvers] :71–93), the SKIP ClassVar
([hints][hints] :142/:254–265), the instance-repr sentinel
([utils-converters][utils-converters] :48–62), the sealed-holder
metaclass ([auth-mutations][auth-mutations] :216–242), the four
set-family metaclasses (no `__repr__` in any), and the 117-file
package vocabulary sweep (re-run fresh). Excluded on body
strength: [utils-converters][utils-converters] (R2),
[types-resolvers][types-resolvers] (R3), [hints][hints] (R4),
[types-definition][types-definition] (R6, grammar composition),
set-side lazy seams (R7, vaulted by the clean sweep),
[auth-mutations][auth-mutations] + set metaclasses (R10).
`types/__init__.py` and the package root export neither name
(not a consumer surface — internal scaffolding).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Read every sibling flavor
for a deferral/pending mirror. Mutations/forms keep pre-bind
declaration ledgers (`make_declaration_registry`) — declared
operations, not collected relation intents. Filters/orders
`RelatedFilter`/`RelatedOrder` string targets resolve through the
open lazy-set families (lazy class read, owner bind, Phase-2.5
drain) — different mechanism, phase, and removal key (R7,
CONVERGE with verified pending-ledger R-C, trigger re-checked).
DRF/auth reach nothing pending-shaped. The set-family
metaclasses collect declarations; none shapes an error repr
(R10). No flavor re-declares the record or the sentinel: the
117-file sweep finds `PendingRelation` vocabulary only in the 4
ledger members plus one docstring-only mention (D1).

**2. Sync/async twins.** Inapplicable with reason: the target is
3 classes + 1 pure method, 61 lines read whole — zero `async
def`, zero `await`, zero ORM, zero I/O. Collection is
import-time construction; resolution is a dict loop. Considered
`one-sync-boundary` and `async-only-queryset-row-adapter`:
checked, no surface.

**3. Derived rather than repeated knowledge.** Audited every
fact the record carries: (a) `field_name` stores the raw Django
`field.name` — the same string that keys `field_map`
(base :634 builds `{f.name: ...}`); one grammar, stored once,
keyed once (F-KEY; no `snake_case(pending...)` rebuild remains
anywhere — grep-clean). (b) `django_field` /
`related_model` are resolution INPUTS (identity lookup +
annotation render), not routing snapshots: the routing read
(cardinality/nullability) is `field_map` `FieldMeta` at the sole
rewrite call (R6, CONVERGE with verified pending-ledger R-A,
narrowed at HEAD — `2bcd50bd` deleted the `relation_kind` /
`nullable` snapshots as unread). (c) `source_type` /
`source_model` are identity + diagnostic labels (unregister key,
error lines), read whole, never re-derived. (d) The frozen
spelling is stdlib idiom shared with ~30 records; the
`eq=False` arm is unique (R8).

**4. Inverse / round-trip pairs.** (a) Sentinel install (base
:1971) → rewrite (finalizer :898): the pair is owned by verified
`type-registry-pending-ledger` F1 (C1/C2 pin both halves); this
file owns the sentinel SHAPE only (F-SENTINEL). (b) Record
construct (base :1963) → discard (finalizer :904): same family,
same treatment (F-RECORD). (c) No second un-pend, un-install, or
re-pend primitive exists (sweep-clean). (d) The silent-skip half
(set-side `None` targets) is the CONVERGEd R-D split (R5), not a
pair owed here.

**5. Contracts restated in another medium.** Per rule:
production (this file) + oracles (5 shape tests + the ledger
rows named in the trace — every one spells literals, none reads
the owner) + projections (module + class docstrings verified
clause-by-clause against producer/drain bodies; spec + GOAL
pins; the one stale projection filed as D1). Media counted per
finding; oracles listed, never counted.

**6. Enforcement by omission.** The target defines no guard, so
the enumeration runs over the guards its CONTRACT requires of
its neighbors: GFK/model-less raise (base deferral branch —
present, oracle-pinned); unresolved-target raise before any
class mutation (finalizer — present, wording + retention +
retry pinned); consumer-authored skip (producer short-circuit +
finalizer defense arm — present, C4-adjudicated by the verified
family); import-time-only add/discard (`_check_mutable` —
present); unguarded `iter_pending_relations` (pure read, no
guard owed — family's matrix-6 verdict, stands). No member
lacks a guard its contract requires: no defect. The standing
D1 of the verified family (no oracle for `clear()`'s pending
arm) is that family's row, not re-filed here.

### Enumeration

Instrument: `ast.parse` over the target (`ast.Module.body` = 7
top-level members) plus full nested expansion (every docstring,
field, and method body). 16/16 homed; no member unassigned.

| # | Member | Home |
|---|---|---|
| 1 | Module docstring (flow map, :1–10) | F-MECH (projection; R9 trio) |
| 2 | `from __future__ import annotations` | F-MECH |
| 3 | `from dataclasses import dataclass` | F-MECH |
| 4 | `from django.db import models` | F-MECH |
| 5 | `class PendingRelation` + `@dataclass(frozen=True, eq=False)` | F-RECORD |
| 6 | `PendingRelation` docstring (identity + no-routing clauses) | F-RECORD |
| 7 | field `source_type` | F-RECORD |
| 8 | field `source_model` | F-RECORD |
| 9 | field `field_name` | F-RECORD + F-KEY (key clause) |
| 10 | field `django_field` | F-RECORD |
| 11 | field `related_model` | F-RECORD |
| 12 | `class _PendingRelationAnnotationMeta` | F-SENTINEL |
| 13 | metaclass docstring | F-SENTINEL |
| 14 | `__repr__(cls)` (error shape, :47–51) | F-SENTINEL |
| 15 | `class PendingRelationAnnotation` | F-SENTINEL |
| 16 | sentinel docstring | F-SENTINEL |

### Challenges

Counts are authoritative definitions only; consumers, oracles,
projections listed, never counted.

| # | Change posited | Definitions forced |
|---|---|---|
| C1 | Sixth record slot (new carried fact) | **1** (the record declares it; sole producer call base :1963 + sole finalizer reads + oracles compose/update — listed, never counted; cf. family C5) |
| C2 | Identity → value equality/hash semantics | **1** (`eq=False` here; the ledger's `id()` match is unaffected by design — R1; twin/non-hashable oracles fail as oracles) |
| C3 | Reword the unfinalized-schema error | **1** (metaclass `__repr__`; oracle `test_pending_relation_annotation_repr` spells the literal) |
| C4 | Sentinel mechanism (class → instance token) | **1** (sentinel + metaclass here; install base :1971 + Strawberry `TypeError` surfacing are consumers — and the change is impossible: an annotation slot requires a class, R2) |
| C5 | `field_map` key grammar change | **1** here as composition (the record's clause follows); the grammar itself is defined once at base :634 (listed, not counted) — the record owns no grammar |

## Findings

### F-RECORD — pending-relation identity record (file-local)

- **Contract + variation.** The 5 slots (`source_type`,
  `source_model`, `field_name`, `django_field`,
  `related_model`) form the one collected record per
  auto-synthesized relation; records compare and hash by
  identity (`eq=False`: equal-valued twins stay distinct, a
  non-hashable `django_field` still hashes); frozen
  post-construction; carries no cardinality/nullability (the
  record docstring's final clause). Varies as the record shape.
- **Sites + roles.** Definition: the dataclass (sole;
  `PendingRelation(` census = 1 production site base :1963 +
  oracle constructions). Producer consumer: `_build_annotations`
  + `__init_subclass__` add loop. Read consumers: finalizer
  Phase 1 (identity, map key, lookup key, render input),
  `unregister` (source key), `_format_unresolved_targets_error`
  (labels). Oracles: the 5 shape tests + ledger identity rows.
- **Challenges.** C1 → 1; C2 → 1.
- **Owner + lifetime.** This module for the shape (principle 7:
  narrowest owner every consumer already imports — base and
  finalizer both import it; moving the shape into either
  strands the other). Principle-4 lifetime: constructed at
  collection, published via `add_pending_relation`, discarded
  at finalize drain; immutable throughout (`frozen=True`,
  oracle-pinned).
- **Migration.** None — zero-edit.
- **Distinct behavior.** List/drain/removal keys stay with
  verified `type-registry-pending-ledger` (ledger owns the
  list, relations owns the shape — the family's own boundary,
  re-verified). Routing reads stay with `field_map` (R6).
- **Behavioral proof.** `static-reviewed` (sole-construction +
  sole-call-line + `eq=False`-uniqueness censuses; inspection
  decides — import composition, no ordering/transaction/async
  surface).
- **Structural gate.** None owed (gate-only justification:
  shape unity cannot be behavior-pinned — a hand copy passes
  every oracle by construction — and a source census is the
  bespoke-existence shape DRY.md forbids; same bar as the
  verified ledger/enum/store items).
- **Coupling.** None.
- **Freshness.** Target `5e9b5cdbc7fb` (HEAD == worktree);
  base `dc67f084cbc9`; finalizer `b9d8acb2b942`;
  registry `492654d219d1`; test-relations `2e18880ad7f4`.

### F-KEY — field-name key clause (file-local)

- **Contract + variation.** `field_name` is the raw Django
  `field.name`, the same string that keys
  `DjangoTypeDefinition.field_map`; finalization reads the
  relation's `FieldMeta` from that map. Varies with the key
  grammar (owned elsewhere — this row owns the record-side
  clause only).
- **Sites + roles.** Clause definition: record docstring here.
  Grammar definition: base :634 (`{f.name: ...}`,
  composed — listed, not counted). Key consumer: finalizer
  :883 (`field_map[pending.field_name]`, sole keyed read of a
  record field). Oracle: every finalize row (implicit — a
  miskeyed record raises `ConfigurationError` naming the
  field).
- **Challenges.** C5 → 1 here as composition.
- **Owner + lifetime.** Clause here (it constrains what the
  producer must store); grammar in base per the definition
  invariant prose. Lifetime: collection → finalize read.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The grammar definition, the map build,
  and the miss error stay at their owners.
- **Behavioral proof.** `static-reviewed` (sole-build +
  sole-keyed-read census; `snake_case(pending` grep-clean
  package-wide).
- **Structural gate.** None owed (clause; the finalize miss
  error is the standing loud path).
- **Coupling.** None.
- **Freshness.** Target `5e9b5cdbc7fb`; base `dc67f084cbc9`;
  finalizer `b9d8acb2b942`; definition `1c59a3feec53`.

### F-SENTINEL — unfinalized-schema sentinel + error shape (file-local)

- **Contract + variation.** `PendingRelationAnnotation` is the
  class installed as every deferred relation's annotation and
  rewritten before `strawberry.type` runs; met only by
  Strawberry when finalization was skipped, it reports
  `<unfinalized DjangoType relation; call
  finalize_django_types() before constructing
  strawberry.Schema>` via the metaclass `__repr__` instead of
  the default class repr. Varies as the error shape.
- **Sites + roles.** Definitions: sentinel class + metaclass +
  `__repr__` (sole; `__repr__` census package-wide = 2: this
  class-repr + the `_MroContinue` instance-repr — R2). Install
  consumer: base :1971 (sole). Surfacing consumer:
  Strawberry's schema-construction `TypeError` (upstream).
  Oracles: repr-literal test + install-identity rows.
- **Challenges.** C3 → 1; C4 → 1 (and C4's change is
  impossible — R2).
- **Owner + lifetime.** This module (principle 7: the shape
  the producer installs and the drain rewrites; co-locating
  with the record keeps the install/rewrite vocabulary in one
  import both flows already share). Lifetime: install at
  collection → rewrite-or-error at schema build.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The install/rewrite PAIR stays with
  verified `type-registry-pending-ledger` F1; the silent-skip
  contrast stays R5; per-message wording direction untouched
  (single wording, single site — nothing to separate).
- **Behavioral proof.** `static-reviewed` (sole-install
  census + literal oracle; the Strawberry surfacing is
  upstream behavior, pinned by the literal).
- **Structural gate.** None owed (single wording; the
  literal oracle fails any drift — proved shape, not a new
  gate).
- **Coupling.** None.
- **Freshness.** Target `5e9b5cdbc7fb`; base `dc67f084cbc9`;
  test-relations `2e18880ad7f4`; test-base `bb56c89bbcad`.

### F-MECH — module mechanics (file-local)

- **Contract + variation.** Module docstring maps the
  producer → sentinel → drain flow with resolving
  `path::Symbol` cites (`_build_annotations`,
  `finalize_django_types`, `discard_pending` — all resolve);
  3 import statements bind exactly the 3 names the bodies
  use (`annotations` future, `dataclass`, `models` — no
  `RelationKind` import remains since `2bcd50bd`). Varies as
  the map prose + import set.
- **Sites + roles.** Definition: header here. Cite targets:
  base/finalizer/registry (listed, not counted). No
  consumer surface (unexported from both `__init__` files).
- **Challenges.** None moves a second definition (prose +
  imports; the flow halves are their owners' rules — R9).
- **Owner + lifetime.** Here. Lifetime: module scope.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Producer/drain bodies stay at base /
  finalizer / registry.
- **Behavioral proof.** `static-reviewed` (cite resolution +
  name-use census).
- **Structural gate.** None owed (`check_citations` already
  executes the cite half in CI).
- **Coupling.** None.
- **Freshness.** Target `5e9b5cdbc7fb`.

### R1 — record identity vs ledger identity-match (rejected)

Fresh pair complementing verified
`type-registry-pending-ledger` F1. Difference: record-side
equality/hash posture (`eq=False` — what `==`/`hash()` on a
record MEAN) vs ledger-side removal key (`discard_pending`
matches `id()` — which records LEAVE the list). Either
changes alone: `2bcd50bd` rewrote record equality (value
hash → identity) without touching the discard body, and the
ledger docstring states the `id()` match keeps the module
independent of the record's equality. Two mechanisms, one
direction, no shared edit. Trigger: a ledger removal arm
reading `==`/`hash()`, or a record consumer relying on value
equality. Home: the record docstring identity clause +
`registry.py::TypeRegistry.discard_pending` docstring (both
already state it) + this finding.

### R2 — sentinel vs instance-repr sentinel (rejected)

Fresh pair: this class-as-annotation sentinel (class repr via
metaclass) vs [utils-converters][utils-converters]`::_MroContinue`
(singleton instance token, instance `__repr__` returning
`MRO_CONTINUE`). Difference: an `__annotations__` slot
requires a CLASS Strawberry can read as a type; an instance
token cannot occupy it, and a class repr cannot serve a
runtime dispatch token. The shared form (a repr-shaping
helper) would own nothing — the two `__repr__` bodies answer
different receivers (`cls` vs `self`) over different
subjects (schema-construction error vs conversion-dispatch
diagnostic). Trigger: a second annotation-slot sentinel, or
`_MroContinue` installed as an annotation. Home: this
finding (both docstrings already state their own shape).

### R3 — sentinel vs runtime dispatch tokens (rejected)

Fresh pair: this diagnostic error shape vs
[types-resolvers][types-resolvers] `_PLAN_UNREAD` /
`_FK_ELISION_UNSAFE` (`object()` identity tokens threading
runtime dispatch). Difference: human-read error shaping at
schema build vs opaque branch markers at request time; the
tokens deliberately carry NO diagnostic surface (identity
comparison only), the sentinel deliberately carries nothing
ELSE. Trigger: a resolver token gaining a diagnostic repr
consumers match on, or the annotation sentinel used for
runtime dispatch. Home: this finding.

### R4 — sentinel vs SKIP (rejected)

CONVERGE with the verified `optimizer/hints.py` R8 direction
(SKIP-vs-other-ClassVar-sentinels) on fresh evidence:
`OptimizerHint.SKIP` is still the sole member of its shape
(declaration [hints][hints] :142, assignment :265, identity
read :254 — re-swept); its trigger (a second ClassVar
sentinel sharing SKIP's lifecycle) is re-checked unfired;
and this sentinel is not a ClassVar at all — it is a
standalone annotation class. Difference stands: lifecycle
marker inside a record family vs install-and-rewrite
annotation. Trigger: a ClassVar sentinel sharing either
lifecycle. Home: the standing hints row + this finding.

### R5 — sentinel vs silent skip (rejected)

CONVERGE with verified `type-registry-pending-ledger` R-D on
fresh evidence. Difference stands: the unfinalized sentinel
fails LOUD at schema build (the GOAL non-goal guard) while
set-side `None` targets skip silently BY CONTRACT —
unifying them silences the guard. Trigger re-checked
(a silently-skipped model relation): the producer
short-circuit is explicit consumer ownership (family C4),
model-less relations raise at declaration, unregistered
targets raise at finalize — no silent path exists at HEAD
bytes. Home: the standing R-D homes (sentinel docstring +
GOAL non-goal) + this finding.

### R6 — record vs field_map live read (rejected)

CONVERGE with verified `type-registry-pending-ledger` R-A on
fresh evidence, NARROWED at HEAD: `2bcd50bd` deleted the
`relation_kind`/`nullable` snapshots as unread, so the
record carries NO routing snapshot at all — the only shared
facts are the key string (F-KEY), the lookup key
(`related_model` → `registry.get`, the ledger's contract,
not a routing decision), and the render input
(`django_field` beside `field_meta`). T-record re-checked
(a routing read off a record field): the sole
`resolved_relation_annotation(` call (finalizer :898)
passes `field_meta` from `field_map`; no production branch
reads a record field for cardinality/nullability. Collapsing
the record into the map loses the ledger's identity handle;
collapsing the map read into the record reintroduces the
stale-snapshot risk. Trigger: a routing read off a record
field. Home: the record docstring carries-none clause + this
finding.

### R7 — record vs set-side lazy declarations (rejected)

CONVERGE with verified `type-registry-pending-ledger` R-C on
fresh evidence. Difference stands: model-relation forward
refs (class `related_model`, Phase-1 drain, identity
removal) vs sidecar string/callable targets (Phase-2.5
expansion, owner-bound re-store, `None`-placeholder skip) —
different mechanism, phase, and removal key. Trigger
re-checked (a set-side lazy target written into `_pending`):
117-file vocabulary sweep finds `PendingRelation` /
`_pending` / ledger-verb vocabulary only in the 4 member
files plus the one docstring-only D1 mention — zero
production crossover. Home: the open lazy-set family items
+ this finding.

### R8 — frozen-dataclass idiom (rejected)

CONVERGE with the verified `rest_framework/hook_context.py`
frozen-record-idiom direction on fresh evidence: `@dataclass
(frozen=True)` is stdlib spelling shared with ~30 records
whose contracts differ per record; no shared record driver
with a validated lifecycle exists (a new KIND would extend
such a driver per principle 1 — none is owed here). The one
non-idiom arm, `eq=False`, is unique package-wide (census
1 — this record). Trigger: a shared record driver gaining
a validated lifecycle a member here could declare into.
Home: the standing row + this finding.

### R9 — flow-map prose trio (rejected)

Fresh same-flow projection separation: the module docstring
(shape owner's map: producer → sentinel → drain), the
`_build_annotations` docstring (producer's map), and the
finalizer Phase-1 comments (drain's map) describe one flow
from three use sites. Difference: each is read AT its use
site by the author changing that half; unifying strands two
readers for zero change relief (prose moves with its body,
never counted). 0 definitions either way — projections,
listed in axis 5. Trigger: prose moved to one owner with
pointers adopted by all three bodies. Home: the three
docstrings as-is + this finding.

### R10 — repr metaclass vs collection metaclasses (rejected)

Fresh pair: `_PendingRelationAnnotationMeta` (`__repr__`-only
error shaping, no instance machinery) vs the 4 set-family
metaclasses (`FilterSet` / `Form` / `Mutation` / `OrderSet`
declaration collection) plus `_SealedAuthHolderMeta`
(sealed-head write guards). Difference: shaping what an
error MESSAGE shows vs collecting declarations / sealing
writes — no shared body exists (`def __repr__` census over
the 5 rival metaclasses = 0). Trigger: a second
repr-shaping metaclass, or a collection metaclass gaining
error-shape repr. Home: this finding.

## Defects

- D1 (stale projection, UNFIXED, minor): [utils-relations][utils-relations]
  `relation_kind` docstring names `(and the registry's typed
  PendingRelation sentinel)` as a consumer that disambiguates
  `reverse_many_to_one` from forward M2M via the kind
  vocabulary. Both halves are stale at HEAD: the record
  carries no `relation_kind` (`2bcd50bd` removed the unread
  snapshots — its message says so, and the 5-slot record plus
  the 5-kwarg sole construction site confirm it), and the
  record is not a sentinel (`PendingRelationAnnotation` is).
  No pending-side consumer disambiguates the two kinds
  either: the sole rewrite call branches `is_many_side` /
  `nullable` only, collapsing both identically. Owner:
  `django_strawberry_framework/utils/relations.py::relation_kind`
  docstring (drop the parenthetical or retarget it to the
  `FieldMeta`/optimizer consumers that actually read kind).
  Filed for normal closeout homing: the line is byte-identical
  at HEAD (`8dbc3fe668dda7`) and worktree (`05ff55b098382`),
  outside every hunt hunk (HEAD :179 == worktree :121, in the
  unchanged region between diff hunks). Not fixed inside this
  item (file item; zero-edit).

## Pending execution

None. All behavioral proofs are `static-reviewed` (censuses +
inspection over import-time/dict-work surface — no ordering,
transactional, or async claim needs execution). No
`execution-deferred` items. Sharded/PG cells `inapplicable by
construction`: the target executes no ORM and reaches no
database, alias, or dialect decision. No workspace runs were
made (read-only trace; no source-mutating probe exists).

## Judgment

Single-owned scaffolding, zero-edit: the record shape, the key
clause, the sentinel error shape, and the module mechanics each
count exactly 1 authoritative definition, with the list/drain/
pair halves already owned by verified
`type-registry-pending-ledger` (all four of its triggers —
T-producer, T-drain, T-record, R-D — re-checked unfired at
HEAD bytes). Ten rejections (4 CONVERGEd onto verified
verdicts with fresh trigger checks, 6 fresh) carry contract
differences + triggers. One minor stale-projection defect
filed for closeout homing. No consolidation, no new family.

## Implementation (Worker-1)

No tracked changes. Item-scoped diff vs `ITEM_BASELINE`
(`91e69cc726ec36fe848eb10ca3e0a07d65442a50`) is empty for
`django_strawberry_framework/types/relations.py`, and
worktree hash equals HEAD blob `5e9b5cdb` — the target is
CLEAN, so no hunk attribution is owed and no stop triggered.
The only new path is this artifact (untracked, owned by this
item). Dirt elsewhere (hunt `truth.*` migration across
connected files, concurrent test/doc edits) was left alone;
every connected line relied on was verified byte-present at
both HEAD and worktree (20/20 region checks). No `.py`
touched, so no ruff run is owed (none expected per brief).
No commit per standing rule.

## Index rows for Worker-0

| `types-relations-record-shape` | `django_strawberry_framework/types/relations.py::PendingRelation` (5 slots + frozen + eq=False identity + carries-no-routing clause) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | file-local |
| `types-relations-key-clause` | `django_strawberry_framework/types/relations.py::PendingRelation` (field_name-is-raw-Django-name clause composing the base-owned field_map grammar) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | file-local |
| `types-relations-sentinel-repr` | `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` (+ `_PendingRelationAnnotationMeta.__repr__` unfinalized-schema error shape) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | file-local |
| `types-relations-module-mechanics` | `django_strawberry_framework/types/relations.py` (module docstring flow map + 3 import statements binding 3 names) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | file-local |
| `types-relations-identity-vs-ledger-match` | `django_strawberry_framework/types/relations.py::PendingRelation` (rejection recorded here; fresh pair complementing verified type-registry-pending-ledger F1 — record-side eq=False vs ledger-side id() removal key, either changes alone) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/registry.py` | File `types/relations.py` | rejected |
| `types-relations-sentinel-vs-instance-repr` | `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` (rejection recorded here; fresh pair — class-as-annotation with class repr vs `utils/converters.py` instance token with instance repr; annotation slot requires a class) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/utils/converters.py` | File `types/relations.py` | rejected |
| `types-relations-sentinel-vs-runtime-tokens` | `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` (rejection recorded here; fresh pair — diagnostic error shape vs `types/resolvers.py` opaque object() dispatch tokens) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/resolvers.py` | File `types/relations.py` | rejected |
| `types-relations-sentinel-vs-skip` | `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` (rejection recorded here; CONVERGE with verified hints-R8 on fresh evidence — not a ClassVar sentinel at all; trigger re-checked unfired) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/optimizer/hints.py` | File `types/relations.py` | rejected |
| `types-relations-sentinel-vs-silent-skip` | `django_strawberry_framework/types/relations.py::PendingRelationAnnotation` (rejection recorded here; CONVERGE with verified type-registry-pending-ledger R-D on fresh evidence — trigger re-checked, no silent model-relation path) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | rejected |
| `types-relations-record-vs-live-read` | `django_strawberry_framework/types/relations.py::PendingRelation` (rejection recorded here; CONVERGE with verified type-registry-pending-ledger R-A on fresh evidence — narrowed at HEAD, record carries no routing snapshots; T-record re-checked unfired) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/definition.py` | File `types/relations.py` | rejected |
| `types-relations-record-vs-lazy-declarations` | `django_strawberry_framework/types/relations.py::PendingRelation` (rejection recorded here; CONVERGE with verified type-registry-pending-ledger R-C on fresh evidence — trigger re-checked, zero set-side vocabulary in the ledger) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/sets_mixins.py` | File `types/relations.py` | rejected |
| `types-relations-frozen-idiom` | `django_strawberry_framework/types/relations.py::PendingRelation` (rejection recorded here; CONVERGE with the verified hook-context frozen-record-idiom direction on fresh evidence — stdlib spelling, eq=False unique package-wide) | `django_strawberry_framework/types/relations.py` | File `types/relations.py` | rejected |
| `types-relations-flow-prose-trio` | `django_strawberry_framework/types/relations.py` (rejection recorded here; fresh same-flow projection separation — shape owner vs producer vs drain docstrings, each read at its use site) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py` | File `types/relations.py` | rejected |
| `types-relations-metaclass-vs-collection-metaclasses` | `django_strawberry_framework/types/relations.py::_PendingRelationAnnotationMeta` (rejection recorded here; fresh pair — repr-only error shaping vs declaration-collection machinery, zero __repr__ in the 5 rival metaclasses) | `django_strawberry_framework/types/relations.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/forms/sets.py`, `django_strawberry_framework/mutations/sets.py`, `django_strawberry_framework/orders/sets.py`, `django_strawberry_framework/auth/mutations.py` | File `types/relations.py` | rejected |

## Families

None. No cross-file consolidation candidate: the list/drain/pair halves already belong to verified `type-registry-pending-ledger` (triggers re-checked, no new row owed — its index row already covers this file); every rule this file defines is single-sited. No `Family ...` item for Worker-0 to add.

## Independent verification (Worker-2)

Recorded before reading `## Findings` (finding titles were listed
via `grep` for structural navigation only, after this trace was
formed from the searches below; `## Index rows for Worker-0`,
`## Judgment`, and `## Implementation (Worker-1)` were read for
window/claim scope, not for verdicts).

Target `django_strawberry_framework/types/relations.py`: HEAD
`0c0537e2`, HEAD blob `5e9b5cdb`, worktree hash identical — CLEAN.
Zero-edit confirmed: `git diff 91e69cc7... --stat` names only
`docs/dry/dry-0_0_15.md` (the plan); this artifact is the one new
untracked path. No `.py` touched, so no ruff run is owed.

### My enumeration (instrument: `ast.Module.body` + class members)

Top level: 7 statements (#0 module docstring, #1 `__future__`
import, #2 `dataclass` import, #3 `models` import, #4
`PendingRelation`, #5 `_PendingRelationAnnotationMeta`, #6
`PendingRelationAnnotation`). Members: `PendingRelation`
docstring + 5 `AnnAssign` slots = 6; the metaclass docstring +
`__repr__` = 2; the sentinel docstring = 1. Total 7 + 9 = 16.
Homes I would choose before reading the findings: record shape
+ identity + carries-no-routing clause file-local at
`types/relations.py::PendingRelation` (with a converge-check
against verified `type-registry-pending-ledger`'s record-shape
split); the `field_name` key clause file-local composing the
base-owned `field_map` grammar; the sentinel + metaclass repr
file-local; module docstring + 3 imports file-local mechanics.
No second definition site found for any of the four rules.

### My sites + roles

- Definitions (all in the target): the `PendingRelation` shape
  (5 slots, `frozen=True, eq=False`), the carries-no-routing
  clause, the `PendingRelationAnnotation` sentinel, the
  `_PendingRelationAnnotationMeta.__repr__` error shape.
- Producer (consumer): `types/base.py::_build_annotations` —
  the sole `PendingRelation(` construction site and the sole
  `PendingRelationAnnotation` install (`annotations[field.name]`,
  HEAD `base.py` line 1971); verified by package-wide
  `PendingRelation` census (only `base.py`, `finalizer.py`,
  `registry.py`, `relations.py` + one docstring cite in
  `utils/relations.py` carry the vocabulary).
- Ledger (consumer, owned by verified
  `type-registry-pending-ledger`): `registry.py::TypeRegistry`
  `_pending` + `add_pending_relation` / `iter_pending_relations`
  / `discard_pending`; single `add_pending_relation(` call line
  (`base.py` line 818) and single `discard_pending(` drain line
  (`finalizer.py` line 904).
- Drain (consumer): `types/finalizer.py` Phase 1 — resolves via
  `registry.get`, rewrites `__annotations__` via
  `converters.py::resolved_relation_annotation`, discards by
  identity.
- Oracles (all spell literals independently):
  `tests/types/test_relations.py` (identity/hash/frozen/repr),
  `tests/test_registry.py` (sentinel install, identity match,
  drain), `tests/types/test_definition_order.py` (forward-ref
  graph), `tests/types/test_finalizer.py`,
  `tests/types/test_base.py` lines 1731-1732 (install +
  repr substring).
- Projections: the flow-map docstrings at shape owner /
  producer / drain, `spec-010`, `spec-018`.

### My change challenges + definition counts

- C1 (add a 6th record slot): 1 — the record. The producer
  passes the value and the drain ignores it; both compose the
  shape, neither redefines it.
- C2 (restore value equality): 1 — the record's `eq=False`.
  `discard_pending` matches by `id()` explicitly independent of
  equality (its docstring says so; body uses only `id()`), so it
  does not move; the registry identity-test oracle fails but
  oracles are not counted. Either side changes alone.
- C3 (reword the sentinel error): 1 — the metaclass
  `__repr__`. Two oracles spell it (verbatim + substring);
  not counted.
- C4 (re-key `field_name`/`field_map`): 1 — the `field_map`
  grammar owner. The record's key clause composes it at the
  use site (consumer/projection), not a second grammar.
- C5 (second construction/install site): 0 exist — census
  closed above; the sentinel is installed but never read back
  in-package, which is the documented error-shape-only
  contract, not an omission gap (axis 6: GFK rejected at
  declaration with `ConfigurationError`, unresolved target
  raises before any mutation).

### My matrix discharge

1. Cross-flavor: declaration registries (`make_declaration_registry`,
   mutations/forms) are pre-bind per-flavor operation lists —
   different subject from collected relation intents. Set-side
   lazy string targets resolve through the lazy-class seam —
   different mechanism. `OptimizerHint.SKIP` is a `ClassVar`
   opt-out, not an annotation-slot sentinel. No mirror.
2. Sync/async: inapplicable with reason — the target executes
   nothing; pure import-time shape, no await boundary exists.
3. Derived knowledge: the record carries no routing snapshots
   post-`2bcd50bd` (`relation_kind`/`nullable` deleted with the
   `RelationKind` import — verified in the commit diff);
   `FieldMeta.relation_kind` is the single live kind
   derivation. Nothing reconstructed twice.
4. Round-trip: construct (producer) / rewrite+discard (drain)
   are halves at their owners; the record is the shared shape,
   not a second grammar.
5. Other media: oracles spell literals; docstrings describe;
   specs project. Each medium moves for its own reason.
6. Omission: no missing guard established — loud failures at
   both ends (declaration-time GFK raise, pre-mutation
   unresolved raise). The unread-back sentinel is the
   documented contract.

### My convergence expectations + D1 pre-judgment

- Converge-check owed against verified
  `type-registry-pending-ledger` (record-shape split, drain,
  producer-unconditionality, silent-path triggers) — each
  trigger to be re-checked unfired at HEAD bytes, not
  inherited. `eq=False` verified unique package-wide by my
  own census (2 hits, both this file).
- D1 pre-judgment: `utils/relations.py::relation_kind`
  docstring names the registry's typed `PendingRelation`
  sentinel as a kind-disambiguating consumer, but the record
  carries no kind since `2bcd50bd` (field + import deleted;
  zero `RelationKind` vocabulary touches `PendingRelation`
  package-wide — my own census). Docstring-vs-body
  contradiction = minor doc-only defect. The 8-line bullet is
  byte-identical worktree (`utils/relations.py` lines 115-122)
  vs HEAD (lines 173-182; shift is hunt dirt above) — clean
  lines, normal closeout homing. Expect to endorse as filed
  pending the trust-boundary read.

### Reconciliation (post-findings, every check re-run fresh)

Zero substantive differences from W1's trace. Enumeration:
AGREE 16/16 — my instrument (7 top-level + 9 members) lands
the same total as W1's 16-row leaf table; every member homed,
mapping verified row by row (module docstring + 3 imports →
F-MECH; record + docstring + 5 slots → F-RECORD with
`field_name` also carrying F-KEY; metaclass + docstring +
`__repr__` + sentinel + docstring → F-SENTINEL). Matrix: AGREE
all 6 axes — axis 1's no-mirror verdict re-derived on my own
censuses, axis 2 inapplicable (pure shape, zero `async`/`await`
— re-grepped), axis 3's narrowing + grammar claims verified in
the `2bcd50bd` diff and at HEAD (`{f.name: ...}` HEAD `base.py`
line 637; `snake_case(pending` grep-clean), axis 4 halves at
their verified owners, axis 5 media counted per finding,
axis 6 guards all present (GFK raise, pre-mutation unresolved
raise, consumer-authored double arm, `_check_mutable`).
Challenges: AGREE C1–C5, every count 1, re-derived (C4's
impossibility holds — an annotation slot requires a class).
File-local findings: AGREE all 4, homes identical to mine.
Convergences: AGREE — every trigger re-checked UNFIRED at
current bytes on my own sweeps (T-producer: exactly 1
production `add_pending_relation(` call, `base.py` line 818;
T-drain: exactly 1 production `discard_pending(` drain,
`finalizer.py` line 904, the second hit docstring prose;
T-record: all 13 `pending.` reads are identity/labels/keys/
render-input, routing from `field_meta`; R-D: no silent
model-relation path — loud raises at both ends; hints-R8:
SKIP sole ClassVar sentinel, shape regions byte-same;
hook-context R3: standing row exists in plan + artifact).
The `2bcd50bd` narrowing claim is exact: `relation_kind` /
`nullable` / `_hash_component` / `__hash__` / the
`RelationKind` import deleted, and the commit touched the
discard body not at all (docstring prose only — which
strengthens the independence R1 rests on). Rejections: AGREE
all 10 — R1's either-changes-alone (my C2 agrees verbatim),
R2's `_MroContinue` instance-token pair (file read fresh),
R3's `object()` identity-token pair (compared with `is` only,
no repr), R4/R5/R6/R7 convergences above, R8 idiom direction
(`eq=False` unique package-wide — my own census: the 2nd hit
is the docstring mentioning it), R9 zero-definition prose
split, R10 (`def __repr__` census package-wide is exactly 2,
so the 0-in-5-rivals claim holds a fortiori — verified
file-wide zero in all five rival files). D1: ENDORSED as
filed — contract row broken (the docstring's own stated
consumer contract, both halves false: no pending-side kind
read since `2bcd50bd`, and the record is not a sentinel),
feasible project shape (any relational `DjangoType`), harm
concrete for a DRY cycle (principle 10: the next author
honors the wrong stated reason and preserves a dead
distinction); doc-only minor, no wire input reaches prose —
filed minor for closeout homing per the standing cycle
practice DRY.md's defect section prescribes, not as a
blocker. Byte-identical homing verified digit-for-digit
(HEAD `8dbc3fe668dd` / worktree `05ff55b09838`; HEAD
lines 173–182 == worktree lines 115–122). Freshness: all 7
pins digit-for-digit MATCH (base `dc67f084cbc9`, finalizer
`b9d8acb2b942`, registry `492654d219d1`, test-relations
`2e18880ad7f4`, definition `1c59a3feec53`, test-base
`bb56c89bbcad`, utils-relations pair above). Index rows:
14/14 match their findings; Families-none correct (the
family's own F1 records its row already covers all four
member files). Pending-None correct with sharded/PG
inapplicable-by-construction endorsed (pure shape, no ORM).
Window: plan only + this untracked artifact; zero `.py`
touched so no ruff owed. AGENTS.md prose: `path::Symbol`
cites throughout, no process provenance, 10/10 link groups.

Immaterial record notes (no home/count/gate moves, W1 text
left standing): (1) R8/matrix-3d "`~30` records" understates
my fresh census (47 `@dataclass(frozen=True` prefix hits, 41
exact-paren; the standing hook-context verdict says `~50`) —
a larger census strengthens the idiom direction; the index
row carries no headcount. (2) "117-file sweep" vs 119 `.py`
on disk today (2 untracked hunt modules postdate the
family's 117) — conclusion re-verified filesystem-wide
including untracked files: vocabulary only in the 4 members
+ the D1 docstring. (3) "None reads the owner": the
install-identity oracle rows import the owner's exported
name (`is PendingRelationAnnotation`) — pins producer
behavior, necessary and standard; the repr oracles spell
literals; nothing was rewritten (zero-edit). No Worker-2
defects. No workspace runs (read-only trace; nothing
source-mutating exists to prove).

Status: verified.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md

<!-- docs/ -->
[spec-010]: SPECS/spec-010-foundation-0_0_4.md
[spec-018]: SPECS/spec-018-meta_primary-0_0_6.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[auth-mutations]: ../../django_strawberry_framework/auth/mutations.py
[hints]: ../../django_strawberry_framework/optimizer/hints.py
[registry]: ../../django_strawberry_framework/registry.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-converters]: ../../django_strawberry_framework/utils/converters.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-definition-order]: ../../tests/types/test_definition_order.py
[test-finalizer]: ../../tests/types/test_finalizer.py
[test-gfk]: ../../tests/types/test_generic_foreign_key.py
[test-registry]: ../../tests/test_registry.py
[test-relations]: ../../tests/types/test_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
