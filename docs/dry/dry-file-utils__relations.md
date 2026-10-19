# DRY review: `utils/relations.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target [utils-relations][utils-relations] at HEAD blob
`8dbc3fe668dd` (770 lines; worktree `05ff55b0`, 681 lines,
15 hunks, 92+/181- vs HEAD). The worktree state equals
`ITEM_BASELINE` (`4f015340`) for this file — the item-scoped
diff is empty, so every hunk predates the item and no stop
triggered. Hunk H7 (the `classify_path` docstring +14) matches
the ledger's ONE owned hunk by content (adopted orphan
`orm-lookup-path-resolution`, four-walkers-separate rationale,
pure additive, quoted verbatim under `## Implementation`);
H1–H6 and H8–H15 are concurrent-external (the hunt `truth.*`
migration: `relation_attr`/`safe_truthy` deleted, `except
BaseException` arms narrowed, `_safe_type_name` -> `truth.kind`;
the `truth.py` module itself is untracked hunt work). Traced
at HEAD bytes throughout (`git show HEAD:` / `git grep HEAD`
per region); nothing tracked touched. Cite key: bare
stems name package modules (`converters`/`finalizer`/
`resolvers` = `types/*`; `resolvers-drf` =
`rest_framework/resolvers.py`; `leaf` =
`utils/__init__.py`; `oracles` =
`tests/utils/test_relations.py`); `:NNN` indexes HEAD
bytes unless noted.

What the target owns at HEAD: the five-kind relation
taxonomy (`relation_kind` + `is_many_side_relation_kind` +
`MANY_SIDE_RELATION_KINDS`, converged onto verified
`relation-kind-taxonomy`); the strict ORM path classifier
(`classify_path` + `ClassifiedPath`/`RelationPathHop` + the
lenient fallback ladder + the two-layer `lru_cache`, converged
onto verified `orm-lookup-path-resolution`); the
instance-accessor dispatch (`instance_accessor`, converged onto
verified `relation-instance-accessor`); the owner side of the
open `lenient-relation-metadata-read` adoption (`relation_attr`
+ `relation_bool` + `safe_truthy` — one body, two failure
policies); and five file-local rules (strict slot read, two
write-flavor predicates, composite-pk probe, module
mechanics). Consumers compose every export by name; no second
definition of any rule exists.

Sites found (`D` = definition, `C` = consumer, `O` = oracle,
`P` = projection). Taxonomy trio + read contract (`D` here):
`C` field-meta stamp + delegating property, walker x2,
join-taxonomy lenient call, filters/sets, connection keyset
screen, types/resolvers dispatch, inspect labels (`P`),
interior uses (classify, lenient walk, forward-concrete
predicate). Classifier + ladder + records + cache pair (`D`
here): `C` filters/sets, orders/sets x2, to-many probes;
`validate_lookup_expr` has zero production callers (staged
API, spec-058/060 `P`). Lenient body (`D` here, adopted into
the open family): `C` field-meta 17 strict calls,
join-taxonomy 2 lenient calls + alias, in-file readers;
member side = definition.py :315-324 rungs. Accessor (`D`
here): 6 calls across 5 modules + 1 pure string reader.
Oracles: [test-relations][test-relations] (80 tests at HEAD:
kind pins incl. MTI/generic/hostile, accessor tiers, strict
classifier arms, the 32-path legacy-parity matrix,
lookup-tail pins, cache-handle pins — all executing the
owner or Django itself, never mirroring its tables) plus
the stamp/taxonomy/wire pins the three verified families
record. Projections: module + per-def docstrings (each
clause verified against its body; two stale censuses filed
as D1 homed + D2 new), spec-058/060, GOAL non-goal.

Connected behavior examined (all at HEAD bytes): the four
walker contracts (connection :787, plans :653, querysets
:2306, list_field :716 — subject/failure/return triples
re-derived), both classifier consumers (filters :964,
orders :536/:720), the to-many probes (filters :1606,
orders :726 via alias), the taxonomy boundary
(join-taxonomy :96/:104/:296-299), the morph/partition
legs, the stamp (field-meta :162-164/:253-302), the
rewrite path (finalizer :948 + converters :795), the
definition rungs (:315-324), the to-attr grammar
(nested-planner :729), the OUT exclusions (permissions
:596/:618, filters/base :638, walker :673, strings :252),
and the flag-read population (`one_to_many` 6 files,
`many_to_many` 12 files — every file triaged). Excluded
on body strength: the write-decode/population readers
(R8/R12/R13/R17/R18), the serializer/cascade/to-field
guards (R9/R10/R11), the planner/taxonomy legs
(R6/R15/R16/R21/R30), declaration/registry/spelling
mechanisms (R31/R32/R33), the orchestration owner (R-O,
consumer-only).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Every sibling flavor
read for a taxonomy/classifier/accessor mirror. Set flavors
consume the classifier + probe by name (filters/orders).
Write flavors consume the predicates by name
(mutations/forms/DRF) and keep their own decode/cardinality
vocabularies (R8/R9/R12/R13). Cascade answers composability,
not cardinality (R10). The optimizer consumes kind,
accessor, and lenient reads by name and owns its
partition/through/morph legs (R6/R15/R16/R21). No flavor
re-derives a kind, a path plan, or an accessor: `def
relation_kind` census = 2 (owner + the one-line
FieldMeta delegate), `def instance_accessor` = 1,
`classify_path` def = 1, second `_meta` multi-segment
walks = the 4 known contracts only (R1).

**2. Sync/async twins.** Inapplicable with reason: zero
`async def`, zero `await` in the 770 HEAD lines
(grepped); every export is pure metadata reads plus
contained calls, zero ORM I/O. `path_traverses_to_many`
serves both pipelines from one cached body (the verified
orm verdict, re-confirmed — no colored pair exists).

**3. Derived rather than repeated knowledge.** (a) `pk`
alias: `_meta.pk` here vs `pk.name` (connection,
list_field) vs unresolved (plans, prefetch) — per-contract
derivation, converged (R3). (b) Separator: `LOOKUP_SEP`
here vs literal `"__"` in connection :800 / plans :679 —
spelling, T3 unfired (R4). (c) Forward-M2M: flag test
here, never kind-routed (R28). (d) Column backing: kind
gate + `column`/`related_model` here vs keyset/certifier
screens (R29). (e) Composite-ness vs pk projections
(R30). (f) GFK: three tests for three contracts (R27).
(g) `MANY_SIDE` has no direct production importer — the
predicate's table by documented intent (principle 11
keep, re-verified by census).

**4. Inverse / round-trip pairs.** None owed: one-way
classification (no un-classify), one-way accessor (no
parse-back; the reverse scan is R17, not a second half),
cache handles with no inverse. `validate_lookup_expr` is
the AFTER-terminal contract, not the path contract's
mirror (R2). The twin caches clear together by one
handle (R26).

**5. Contracts restated in another medium.** Production
(this file) + oracles (80 executing tests spelling
literals + Django's own answers; cache handles pinned;
nothing reads the owner's tables) + projections
(docstrings verified clause-by-clause; two stale
censuses filed as D1/D2; spec-058/060 name the staged
tail; GOAL non-goal pins the loud failure). Media
counted per finding; oracles listed, never counted.

**6. Enforcement by omission.** Every member checked
against the guard its contract requires. The strict
classifier raising inside the lenient taxonomy is
handled at the taxonomy's own boundary
(join-taxonomy :296-299, stated `forward_single`
default) — no gap. `relation_name` is strict-only by
design (both call sites are strict build/classify
paths; the taxonomy reads those slots via its own
lenient leg, never this helper) — no gap. `is_many_side`
fails closed to `False` on a hostile kind — no gap.
Hidden (`+`) relations raise typed through the
classifier and never reach the accessor — no gap. The
deprecated-snapshot prose (D1) and the M2M census
omission (D2) are doc-only defects, filed, not
omission gaps. The definition-rung truthiness hole
(D3) belongs to the open lenient family per its
Coupling, not to this file. No member lacks a guard:
no axis-6 defect.

### Enumeration

Instrument: `ast.parse` over HEAD bytes
(`ast.Module.body` = 38 top-level members) plus full
nested expansion (every docstring, dataclass slot,
Protocol member, `__all__` entry read). 38/38 homed;
no member unassigned. Nested members fold into their
parent's finding (hop 4 slots, path 6 slots, Protocol
5 members, `__all__` 17 entries — each verified used).

| # | Member (HEAD line) | Home |
|---|---|---|
| 1 | Module docstring (:1) | FL-MECH |
| 2 | `from __future__` (:3) | FL-MECH |
| 3 | `dataclass` import (:5) | FL-MECH |
| 4 | `lru_cache` import (:6) | FL-MECH |
| 5 | `typing` imports (:7) | FL-MECH |
| 6 | `FieldDoesNotExist` import (:9) | FL-MECH |
| 7 | `LOOKUP_SEP` import (:10) | FL-MECH |
| 8 | exceptions import (:12-17) | FL-MECH |
| 9 | `TYPE_CHECKING` block (:19-20) | FL-MECH |
| 10 | `__all__` (:22-40, 17 entries) | FL-MECH |
| 11 | `RelationKind` (:42-48) | F-TAX |
| 12 | `MANY_SIDE_RELATION_KINDS` (:50-52) | F-TAX |
| 13 | `_MISSING` (:54) | FL-MECH (decl; pair converges context R5, standing row already lists this file — transcribes nothing) |
| 14 | `safe_truthy` (:57-69) | F-LENIENT (adopt) |
| 15 | `relation_attr` (:72-102) | F-LENIENT (adopt) |
| 16 | `relation_bool` (:105-129) | F-LENIENT (adopt) |
| 17 | `relation_name` (:132-140) | FL-NAME |
| 18 | `_RelationFieldLike` (:143-157) | F-TAX (read contract) |
| 19 | `relation_kind` (:160-232) | F-TAX |
| 20 | `is_many_side_relation_kind` (:235-240) | F-TAX |
| 21 | `RelationPathHop` (:243-261) | F-ORM |
| 22 | `ClassifiedPath` (:264-284) | F-ORM |
| 23 | `_resolve_segment_field` (:287-303) | F-ORM |
| 24 | `_is_traversable_relation` (:306-320) | F-ORM |
| 25 | `classify_path` (:323-406) | F-ORM |
| 26 | `validate_lookup_expr` (:409-484) | F-ORM (F3 facet) |
| 27 | `_lenient_traverses_to_many` (:487-518) | F-ORM |
| 28 | `_classify_path_cached` (:521-531) | F-ORM |
| 29 | `_traverses_to_many` (:534-548) | F-ORM |
| 30 | `_path_traverses_to_many_cached` (:551-554) | F-ORM |
| 31 | `path_traverses_to_many` (:557-596) | F-ORM |
| 32 | `_path_traverses_to_many_cache_clear` (:599-608) | F-ORM |
| 33 | `.cache_clear` handle (:611) | F-ORM |
| 34 | `.cache_info` handle (:612) | F-ORM |
| 35 | `is_forward_many_to_many` (:615-638) | FL-FM2M |
| 36 | `is_forward_concrete_relation` (:641-691) | FL-FCON |
| 37 | `instance_accessor` (:694-748) | F-ACC |
| 38 | `has_composite_pk` (:751-770) | FL-HCP |

### Challenges

Counts are authoritative definitions only; consumers,
oracles, projections listed, never counted. Converged
challenges re-derived at HEAD bytes, not inherited.

| # | Change posited | Definitions forced |
|---|---|---|
| C-TAX1 | New Django relation shape | **1** (`relation_kind`; CONVERGE taxonomy CH1 — stable-flag arms, `concrete` only in the reverse-O2O arm) |
| C-TAX2 | Sixth `RelationKind` | **1** (classifier + table, one site; CONVERGE CH2) |
| C-TAX3 | Generic-detection change | **1** (duck-typed arm; CONVERGE CH3) |
| C-ORM1 | Transform segment in path position | **0** shared (each walker answers per its contract; CONVERGE orm C1) |
| C-ORM2 | New mid-path failure mode | **0** shared / 5 independent (raise vs 3x `None` vs `False`, each meaning differs; CONVERGE C2) |
| C-ORM3 | 5+ segment path | **0** (all five loop; CONVERGE C3) |
| C-LEN1 | Read-mechanism hardening | **2** (the one body here + the definition rungs; ADOPT — the open family's count) |
| C-LEN2 | Third lenient outcome | **2** (same two; ADOPT) |
| C-ACC1 | Django accessor-scheme change | **0** moves / 1 holder (tier 2 delegates upstream; CONVERGE accessor CH1) |
| C-ACC2 | `related_name` override | **1** (helper + stamp; CONVERGE CH2) |
| C-NAME1 | New slot value shape | **1** (`relation_name`; field-meta + classifier compose) |
| C-FM2M1 | M2M writability rule change | **1** (predicate; 4 consumers follow, incl. the forms site D2 names) |
| C-FCON1 | Column-backing rule change | **1** (predicate; 2 consumers follow) |
| C-HCP1 | Composite-detection change | **1** (probe; 1 consumer follows) |
| C-MECH1 | New public export | **1** (`__all__` + def move as one site) |

## Findings

### F-TAX — relation-kind taxonomy trio (CONVERGE verified `relation-kind-taxonomy`)

- **Contract + variation.** Five-shape cardinality
  classifier (`RelationKind` + `relation_kind` +
  `_RelationFieldLike` read contract) plus the many-side
  table (`MANY_SIDE_RELATION_KINDS` +
  `is_many_side_relation_kind`). Varies per field shape,
  kind vocabulary, generic form (C-TAX1..3, each 1).
- **Sites + roles.** Definition: the trio here (sole;
  `def relation_kind` census = 2, the second the
  one-line FieldMeta delegate — a consumer by
  construction). Consumers by name: field-meta stamp +
  property, walker x2, join-taxonomy lenient call,
  filters/sets, connection keyset screen, types/resolvers
  dispatch, interior uses (classify, lenient walk,
  forward-concrete predicate). Oracles: kind/hostile
  pins. Projections: inspect labels, docstrings (D1
  filed on the kind-vocabulary parenthetical).
- **Owner + lifetime.** Here, per the verified family
  (dependency direction decisive — the owner is leaf-ward;
  moving the decision to the stamp cycles the optimizer).
  Pure derivation; `MANY_SIDE` has zero direct
  production importers (census) and stays as the
  predicate's table (principle 11 keep, re-verified).
- **Behavioral proof.** `static-reviewed` (full sweep
  population + oracle bodies; no ordering/transactional/
  async surface).
- **Structural gate.** None — the verified no-gate
  verdict stands (open-ended flag vocabulary; the three
  candidate gates stay unsound for the recorded
  reasons).
- **Triggers re-checked at HEAD, all unfired:** R-A
  sets still differ exactly on `reverse_one_to_one`;
  R-B FieldMeta still carries no `remote_field`/`through`
  slot (full grep); R-C still one body, sole lenient
  consumer, no third policy; R-D write-kind + fail-loud
  screen present; R-E serializer guard present; R-F
  cascade predicates present; R-G to-field predicate
  present; R-H column screens present; R-I NARROWED —
  the `PendingRelation` snapshot half is retired
  (`2bcd50bd` deleted the field; its trigger can no
  longer fire), the labels half stands. R-I narrowing
  + this finding's D1 are the same drift, both filed.
- **Freshness.** Target `8dbc3fe668dd`; field-meta
  `18ea719a`; join-taxonomy `9b355a50`; walker
  `75f9c6b6`; filters/sets `993e887a`; connection
  `4894f90f`; types/resolvers `72d62dc4`; inspect
  `2807d0fc`; oracles `e51cebaa`.

### F-ORM — strict path classification + ladder (CONVERGE verified `orm-lookup-path-resolution`)

- **Contract + variation.** Immutable hop-plan
  classification (`classify_path` + records + segment
  helpers) with the lenient walk composed INTO the one
  ladder body (`_traverses_to_many`), served through
  the two-layer cache to `path_traverses_to_many`; the
  lookup-expression tail (`validate_lookup_expr`) is
  the separate F3 contract with zero production
  callers (staged API named by spec-058/060 —
  re-verified: def-only in-package, 3 spec hits).
  Varies per walker contract (C-ORM1..3: 0 shared).
- **Sites + roles.** Definitions: all here (one strict
  plan, one documented compatibility arm, one
  composition body, one cache pair). Consumers:
  filters/sets (direct-raise vs expanded-fail-closed),
  orders/sets x2 (declaration + apply validation),
  to-many probes. Oracles: strict arms, 32-path
  matrix, tail pins, cache-handle pins.
- **Owner + lifetime.** Here, per the verified family
  (strictest contract + leafward import direction +
  adjacent taxonomy). Principle-4: exactly one stored
  derivation — the bounded `lru_cache` pair keyed on
  definition-time-stable `(model, field_path)`,
  cleared by the paired handle; `classify_path` stays
  `not cached` by stated contract (unhashable doubles).
- **Behavioral proof.** `static-reviewed` (walker
  triples re-derived at HEAD bytes; the verified
  execution probes stand as prior evidence, not
  re-run — a file item runs no probe).
- **Structural gate.** None owed (file item converges;
  the family carries its verdict).
- **Triggers re-checked at HEAD, all unfired:** T1 (no
  caller takes another walker's answer — all four
  triples re-derived unchanged); T2 (no accessor
  fallback, no non-raising mode); T3 (literals still
  in connection :800 / plans :679); field_meta R3
  (elision still single-hop — `_target_pk_name` reads
  one model).
- **Durable-home note.** The F1 clause this family
  recorded on `classify_path` exists ONLY as the
  ledgered worktree hunk H7 (O1); HEAD lacks it. The
  separation verdict does not depend on the prose.
- **Freshness.** Target `8dbc3fe668dd`; connection
  `4894f90f`; plans `cce98531`; querysets `3616927d`;
  list_field `21380eb7`; filters/sets `993e887a`;
  orders/sets `6044ab1a`; oracles `e51cebaa`.

### F-ACC — instance accessor (CONVERGE verified `relation-instance-accessor`)

- **Contract + variation.** Three-tier dispatch
  (precomputed slot, live `get_accessor_name()`,
  `name`) with typed guards; diverges from the query
  name exactly where Django diverges (C-ACC1: 0
  moves/1 holder; C-ACC2: 1).
- **Sites + roles.** Definition: here (sole; `def`
  census = 1). Consumers by name, re-verified exact:
  6 calls across 5 modules (field-meta stamp,
  walker x2, nested-planner, finalizer, resolvers) +
  the connection pure string reader. Oracles: tier +
  hostile pins, stamp pins, S3 end-to-end pin.
- **Owner + lifetime.** Here, per the verified family
  (narrowest importer-safe owner; stamp lifetime =
  definition lifetime, stated at the slot).
- **Behavioral proof.** `static-reviewed` (census +
  bodies; the verified execution probes stand as
  prior evidence).
- **Structural gate.** None — the verified no-gate
  verdict stands (misuse vocabulary pervasively
  legitimate; the sound census has its second
  legitimate member in R17).
- **Triggers re-checked at HEAD, all unfired:** R-A
  (helper still strict-only; scan present at
  querysets :2356); R-B (attach key still child-side,
  both docstrings state the contrast); R-C (grammar
  still field-name keyed — nested-planner :729,
  connection :2137); R-D (forward-only population
  unchanged); R-E (helper never returns `None`).
- **Freshness.** Target `8dbc3fe668dd`; field-meta
  `18ea719a`; walker `75f9c6b6`; nested-planner
  `b4dfd4a6`; finalizer `de34ae2a`; resolvers
  `72d62dc4`; connection `4894f90f`; querysets
  `3616927d`; join-taxonomy `9b355a50`.

### F-LENIENT — lenient read body (ADOPT into open `lenient-relation-metadata-read`)

- **Contract + variation.** Read one relation-metadata
  attribute, degrading to the caller's default when
  unanswerable; the strict and lenient policies share
  the one body (`relation_attr` + `relation_bool` +
  `safe_truthy` truth-test half). Varies as the read
  mechanism + the lenient outcome (C-LEN1/2: 2 —
  this body + the definition rungs).
- **Sites + roles.** Owner-side definition: the one
  body here. Member-side definition: the inline idiom
  at definition.py :315-324 (two rungs, one spelling —
  re-verified fresh at HEAD `fa6c4d33`). Consumers of
  the owner (listed): field-meta 17 strict calls,
  join-taxonomy lenient wrappers (sole `lenient=True`
  consumer — 2 call sites, re-verified), in-file
  readers (classifier, name reader, accessor x3).
  Oracles: taxonomy lenient rows + definition
  malformed-metadata rows (hostile doubles).
- **Disproof attempted, failed.** Same `(object, name,
  default)` -> value-or-default read at request time
  under the same change rule the owner's docstring
  states; strict/bare/non-relation readers stay out
  per the contract's own exclusions.
- **Migration.** The family item's call (adopts the two
  rungs into the owner; dependency check stands —
  leaf-ward, no reversal). No edit here (file item).
- **Distinct behavior.** Walk/ladder/precedence/cache
  stay in definition.py; strict callers, bare
  callers, non-relation reads stay separate.
- **Behavioral proof.** `static-reviewed` (owner body
  + both rungs + oracles compared at HEAD bytes; a
  file item runs no failability probe).
- **Structural gate.** Owed by the family item (census
  over the lenient spelling + diverged-default
  negative control, per the naming finding).
- **Coupling.** D3 (definition's truthiness hole):
  `relation_attr` adoption preserves it (standalone —
  D3 rides its own card), `relation_bool` adoption
  closes it (combined fix — the maintainer authorizes, or the
  family redesigns standalone). PLUS the R14 interplay:
  landing the adoption fires join_taxonomy R13's
  trigger (a second `lenient=True` consumer) — the
  family item adjudicates the alias-declaration move;
  R-C holds regardless (no third policy).
- **Freshness.** Target `8dbc3fe668dd`; definition
  `fa6c4d33`; field-meta `18ea719a`; join-taxonomy
  `9b355a50`; oracles `e51cebaa` (relations suite) +
  `481294c3` (taxonomy suite); definition-suite rows
  per the naming finding (rungs re-read here at
  definition HEAD bytes).
- **Worker-0 note.** The family row + `## Families`
  item already exist and already list both files; no
  new row owed. Worktree caveat O2: the concurrent
  truth-migration deletes this owner body in the
  worktree — the family item re-derives on the
  landing state.

### FL-NAME — strict slot read (file-local)

- **Contract + variation.** Read one optional
  GenericRelation field-name slot, requiring `str` or
  `None` (C-NAME1: 1). Strict-only by design — both
  call sites (field-meta carriage, the generic arm)
  are strict build/classify paths.
- **Sites + roles.** Definition here (sole). Consumers:
  field-meta x2, `relation_kind` x2 (composed via
  `relation_attr` strict). Oracles: generic pins
  (incl. `None`-slots fallback).
- **Owner + lifetime.** Here (single site every
  consumer already imports). Pure read, no lifetime.
- **Behavioral proof.** `static-reviewed` (sole-def
  census + bodies).
- **Structural gate.** None owed (single site; the
  kind/generic oracles fail any drift).
- **Coupling.** None.
- **Freshness.** Target `8dbc3fe668dd`; field-meta
  `18ea719a`; oracles `e51cebaa`.

### FL-FM2M — forward-writable-M2M predicate (file-local)

- **Contract + variation.** `True` exactly for a
  forward, writable `ManyToManyField` (`many_to_many`
  + `concrete`/`not auto_created`), splitting what
  the kind vocabulary deliberately collapses
  (C-FM2M1: 1; D2 filed on the docstring census).
- **Sites + roles.** Definition here (sole).
  Consumers (4, re-verified): mutations
  `editable_input_fields`, mutations
  `_relation_field_index`, DRF `_attestable_m2m_fields`,
  forms `_model_column_for` (the D2 site). Oracles:
  accept/reject/hostile pins + stock shape.
- **Owner + lifetime.** Here (single site so the
  predicate cannot drift across the write surfaces).
  Pure derivation.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** None owed (sole site; the
  accept/reject oracles fail drift).
- **Coupling.** None.
- **Freshness.** Target `8dbc3fe668dd`; mutations
  `fc442047`; resolvers-drf `0d302782`; forms
  `6418753d`; oracles `e51cebaa`.

### FL-FCON — forward concrete-column predicate (file-local)

- **Contract + variation.** `True` exactly for a
  forward FK/OneToOne with a real local column (kind
  gate for version independence + `column`/
  `related_model` reads excluding the virtual GFK),
  per spec-036 L3-1 (C-FCON1: 1).
- **Sites + roles.** Definition here (sole).
  Consumers (2, matching the docstring census):
  forms `_model_column_for`, mutations
  `_relation_field_index`. Oracles: column/guard
  pins in the relations + input suites.
- **Owner + lifetime.** Here (the M2M guard belongs
  at the predicate so the next caller inherits the
  whole contract). Pure derivation.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `8dbc3fe668dd`; forms
  `6418753d`; mutations `fc442047`.

### FL-HCP — composite-pk probe (file-local)

- **Contract + variation.** Whether a model declares
  a multi-field pk (`pk_fields` length), failing the
  FK-id-elision eligibility closed (C-HCP1: 1).
- **Sites + roles.** Definition here (sole).
  Consumer: field-meta elision stamp (sole call).
  Oracles: elision-eligibility pins.
- **Owner + lifetime.** Here (single site so
  registered types + the walker fallback stamp
  identically). Pure read.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `8dbc3fe668dd`; field-meta
  `18ea719a`.

### FL-MECH — module mechanics (file-local)

- **Contract + variation.** One-line module docstring;
  7 imports binding exactly the names the bodies use
  (future, dataclass, lru_cache, typing x4,
  FieldDoesNotExist, LOOKUP_SEP, 4 exceptions);
  TYPE_CHECKING `models` import; `__all__` naming
  exactly the 17 public symbols (9 private names
  correctly excluded); `_MISSING` absent-sentinel
  declaration (C-MECH1: 1).
- **Sites + roles.** Definition here. `_MISSING` pair
  converges with verified context R5 (standing row
  already lists this file — re-checked, transcribes
  nothing). Re-export consumer: `utils/__init__.py`
  (3 names).
- **Challenges.** No second definition moves (prose
  + imports + manifest).
- **Owner + lifetime.** Here. Module scope.
- **Behavioral proof.** `static-reviewed` (name-use
  census: every import + every `__all__` entry
  resolved to a def/use).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `8dbc3fe668dd`; leaf
  `1a4c2ec8`.

### R1 — four walkers, four contracts (rejected)

CONVERGE with verified orm F1 on fresh evidence. One
split-and-`get_field` mechanism, four contracts (raise
the hop plan / terminal column-or-`None` / projection
traversability / fail-open terminal model /
certification pair — five bodies counting the owner).
Each triple re-derived at HEAD unchanged. Difference:
terminal rule + failure mode + inputs differ per
caller. Trigger: F1-T1/T2 (a caller needing another
walker's answer; an accessor fallback or non-raising
mode) — both re-checked unfired. Home: the F1 record
+ the ledgered H7 clause (worktree-only, O1) + this
finding.

### R2 — lookup-expression tail (rejected)

CONVERGE with verified orm F3 on fresh evidence.
Difference: `(terminal, lookup_expr)` cursor walk over
`get_transform`/`get_lookup` returning the final
lookup class — the AFTER-terminal contract, never
`_meta.get_field`. Zero production callers
re-verified (def-only in-package); staged API named
by spec-058/060, not dead code (principle 11).
Trigger: a production caller needing path-shaped
answers from it. Home: its own docstring + this
finding.

### R3 — `pk`-alias handling per contract (rejected)

CONVERGE with verified orm matrix-3 on fresh evidence.
Difference: `_meta.pk` here vs `pk.name` (connection,
list_field) vs unresolved (plans, prefetch) — each
answers what its contract needs (field object vs
name vs conservative miss). Trigger: one owned
pk-alias rule. Home: the per-walker bodies + this
finding.

### R4 — separator spelling (rejected)

CONVERGE with verified orm T3 on fresh evidence.
Difference: spelling, not a rule (`LOOKUP_SEP` here
vs literal `"__"` at connection :800 / plans :679
for the identical constant; zero change obligation).
Trigger: T3 (spelling unification re-opens the
C-count on that axis only) — unfired. Home: this
finding.

### R5 — windowable vs many-side sets (rejected)

CONVERGE with verified taxonomy R-A on fresh
evidence. Difference: fetch-strategy predicate vs
cardinality — reverse O2O is windowable yet
single-valued, so it cannot derive from the
many-side set. Trigger re-checked unfired (sets
still differ exactly on `reverse_one_to_one`).
Home: the set comment + module taxonomy table +
this finding.

### R6 — raw vs snapshot layers (rejected)

CONVERGE with verified taxonomy R-B (+ field_meta
R1) on fresh evidence. Difference: partition/through
facts need `remote_field`/`through`, neither on
FieldMeta by design, under a never-raises policy the
strict stamp cannot offer. Trigger re-checked
unfired (no such slots — full grep). Home: the
raw-field clause + this finding.

### R7 — two policies, one read body (rejected)

CONVERGE with verified taxonomy R-C on fresh
evidence. Difference: none left to consolidate —
already one body (`relation_attr`/`relation_bool`
+ `safe_truthy` half), two policies. Trigger
re-checked unfired (no third policy; sole lenient
consumer re-verified). Home: the axis clause + this
finding.

### R8 — write-decode vocabulary (rejected)

CONVERGE with verified taxonomy R-D on fresh
evidence. Difference: coarser RELATION_MULTI/SINGLE
decode vocabulary over a forward-only population
(the fail-loud screen, re-verified present), with
decode-shape reasons to change; routing through
kinds risks turning contained `False` into strict
raises (principle 8). Trigger: a forward
collection-shaped relation with `many_to_many=False`
reaches the write path — unfired. Home: the
write-kind docstring + screen + this finding.

### R9 — serializer cardinality guard (rejected)

CONVERGE with verified taxonomy R-E on fresh
evidence. Difference: DRF-alignment guard
vocabulary with a lenient answer policy the strict
reads cannot offer. Trigger: a model shape where
flags and taxonomy disagree — unfired. Home: the
guard docstrings + this finding.

### R10 — cascade edge predicates (rejected)

CONVERGE with verified taxonomy R-F on fresh
evidence. Difference: single-column `__in`
composability (which edges a one-column walk can
compose), not cardinality. Trigger: cascade needs
beyond-forward-concrete cardinality — unfired.
Home: the predicate docstrings + this finding.

### R11 — to-field predicate (rejected)

CONVERGE with verified taxonomy R-G on fresh
evidence. Difference: join-column question using
the `many_to_one` flag the taxonomy never reads.
Trigger: `to_field` beyond forward FK/O2O —
unfired. Home: its docstring + this finding.

### R12 — column-presence screens (rejected)

CONVERGE with verified taxonomy R-H on fresh
evidence. Difference: each answers a local
"backed by what" question (orderable columns,
sweep exclusion, attested state, form backing),
never "which kind". Trigger: any needing
reverse-kind precision — unfired. Home: their
docstrings + this finding.

### R13 — display labels + retired snapshot (rejected)

CONVERGE with verified taxonomy R-I on fresh
evidence, NARROWED: the labels half stands
(display names, projection); the snapshot half is
retired — `2bcd50bd` deleted the field, so its
trigger (a production reader of the copy) can no
longer fire. The leftover consumer prose is D1.
Trigger: a production reader of the labels as
data. Home: the labels comment + this finding.

### R14 — lenient-alias declaration (rejected)

CONVERGE with verified join_taxonomy R13 on fresh
evidence. Difference: the 3 local names are a
3-line policy pin ("lenient here") over the
already-shared bodies, kept local so the call
sites read as taxonomy code; a shared module
would couple machinery to one consumer. Trigger
re-checked unfired at HEAD (sole `lenient=True`
consumer — 2 sites, 1 module). INTERPLAY: landing
F-LENIENT fires this trigger (a second lenient
consumer) — the family item adjudicates the move.
Home: the alias comment + this finding.

### R15 — morph detect/carry/resolve tri-split (rejected)

CONVERGE with verified join_taxonomy R14 on fresh
evidence. Difference: the generic slots are
DETECTED by `relation_kind`, CARRIED by FieldMeta,
RESOLVED to attnames by `_generic_child_attname`
(consuming `kind`) — three contracts over one slot
pair. Trigger re-checked unfired (still exactly
these three readers — census). Home: the standing
record + this finding.

### R16 — partition query-name vs accessor (rejected)

CONVERGE with verified join_taxonomy R7 (+ accessor
R-B) on fresh evidence. Difference: the attach key
Django's prefetch uses to map child rows to parents
is explicitly NOT the accessor (both docstrings
state it). Trigger: Django unifies the attach key
with the accessor — unfired. Home: the partition
docstring + this finding.

### R17 — reverse-accessor scan (rejected)

CONVERGE with verified accessor R-A on fresh
evidence. Difference: reverse question (accessor
spelling -> field, over non-concrete reverse rels)
with a fail-open per-candidate policy; the helper
raises typed errors by contract, so routing through
it changes raised exceptions (principle 8).
Trigger: helper gains a lenient mode AND the scan
contract changes — unfired. Home: the scan
docstring + oracle pin + this finding.

### R18 — forward `field_name` reads (rejected)

CONVERGE with verified accessor R-D on fresh
evidence. Difference: forward-only population where
`name` IS the attribute by Django contract — no
derivation present, nothing to centralize. Trigger:
a forward-shaped relation whose attribute differs
from `name` — unfired. Home: the branch comment +
this finding.

### R19 — N1-check fallback (rejected)

CONVERGE with verified accessor R-E on fresh
evidence. Difference: `None`-tolerance for direct
test-double callers; the helper never returns
`None` — not a derivation. Trigger: helper gains
a `None` return — unfired. Home: the fallback
comment + this finding.

### R20 — window `to_attr` grammar (rejected)

CONVERGE with verified accessor R-C on fresh
evidence. Difference: prefetch-attach namespace
(`_dst_<field>_connection`, field-name keyed —
re-verified at nested-planner :729), not instance
reading; the resolver needs BOTH (accessor for
rows, field name for the window probe). Trigger:
windows attach keyed on the accessor — unfired.
Home: the resolver fast-path paragraph + this
finding. (Grammar ownership now sits with the open
`relation-connection-to-attr-grammar` family.)

### R21 — guarded first-picker (rejected)

CONVERGE with verified join_taxonomy R4 on fresh
evidence. Difference: "first value testing true, a
raising truth test counting as `False`" — a
contained policy inline `or` cannot express, and
no second named guarded-picker exists (census).
The picker CONSUMES `safe_truthy`; it is not a
rival truth test. Trigger: a second site needing
raising-tolerant first-pick — unfired. Home: the
picker body + this finding.

### R22 — frozen-record idiom (rejected)

CONVERGE with the verified hook-context
frozen-record-idiom direction on fresh evidence.
Difference: `@dataclass(frozen=True)` is stdlib
spelling shared with dozens of records whose
contracts differ per record (hop: segment topology;
path: strict plan; neither shares a lifecycle
driver). Trigger: a shared record driver gaining a
validated lifecycle a member here could declare
into — unfired. Home: the standing row + this
finding.

### R23 — `except` arms vs a shared guard (rejected)

CONVERGE with the verified J1 direction on fresh
evidence. Difference: per-site arms with per-site
verdicts (typed re-raise ×N, `False`, `None`
(rung-side), `ConfigurationError` with subject) —
each fused to its method contract; a driver would
need a verdict mode flag (principle 5). Trigger:
the standing J1 trigger — unfired. Home: the
standing row + this finding.

### R24 — exact-type gates vs a shared gate (rejected)

CONVERGE with the verified J2 direction on fresh
evidence. Difference: per-site `type(x) is`
exclusions (bool/str/list-tuple/str-path) over
boundary values, each with its own refusal —
the shared gate's trigger (a new foreign-object
protocol needing exclusion) is re-checked
unfired. Home: the standing row + this finding.

### R25 — rejection wordings vs an owned grammar (rejected)

CONVERGE with verified per-subject-rejection-grammars
on fresh evidence. Difference: each message names its
subject + renders hostile values through the composed
safe-renderers; still no owned grammar at HEAD.
Trigger: the package adopts one owned
rejection-message grammar — unfired. Home: the
standing row + this finding.

### R26 — twin-cache split (rejected)

Fresh same-file intentional separation: the
classifier cache (`(model, field_path)` -> frozen
plan) vs the answer cache (`(model, field_path)`
-> bool) hold different values for different
readers (the uncached public classifier stays
double-friendly; the probe stays one lookup),
emptied together by the one handle. A single
cache would force the classifier onto hashable
inputs or the probe onto re-derivation. Trigger:
one cache keyed to serve both readers. Home: the
clear-handle docstring + this finding.

### R27 — GFK three-tests split (rejected)

Fresh same-file intentional separation: a forward
`GenericForeignKey` is UNTRAVERSABLE to the
classifier (no `path_infos` -> typed raise),
VIRTUAL to the column predicate (`column`/`related_model`
`None` -> excluded), and `forward_single` to the
kind classifier (no generic slots to claim it).
Three tests because three contracts ask three
questions (can the walk follow it / can a write
target it / what shape is it) — a shared "is
virtual" predicate would need a verdict mode flag.
Trigger: one predicate serving all three
contracts. Home: the three docstrings + this
finding.

### R28 — M2M-forwardness flag test (rejected)

Fresh same-file intentional separation: the
predicate tests `many_to_many` + `concrete`/
`auto_created` flags directly and deliberately does
NOT route through `relation_kind` — the kind
vocabulary collapses forward and reverse M2M (both
`"many"`) while the write surfaces need exactly
that split. Trigger: the kind vocabulary gains a
forward/reverse M2M split. Home: the predicate
docstring (states it) + this finding.

### R29 — forward-single screens (rejected)

Fresh triple: the column predicate (write-target
backing: kind + column + related model) vs the
keyset screen (connection :812: kind + non-null —
a cursor cannot anchor NULLs or fan-out) vs the
certifier (list_field :716: field-or-`None` —
refuses whatever it cannot read). Three
"forward-single" tests, three reasons to change
(write shape vs cursor anchorability vs ordering
certification). Trigger per pair: the two
contracts start answering one question. Home:
the three bodies + this finding.

### R30 — composite probe vs pk projections (rejected)

CONVERGE with the verified join_taxonomy
six-`pk.attname`-readers direction on fresh
evidence. Difference: composite-NESS (`pk_fields`
length — a fail-closed elision gate) vs NAME
(identifier) vs ATTNAME (loaded column attribute)
projections. Trigger: a seam needing two
projections from one read — unfired. Home: the
standing row + this finding.

### R31 — registry walk vs `_meta` walk (rejected)

CONVERGE with verified orm OUT (+ definition
F-RELTARGET) on fresh evidence. Difference:
`related_target_for` walks the TYPE REGISTRY graph
(single hop + `None`-precedence + finalized-gated
cache — a lookup, never `_meta.get_field` per
segment) while `classify_path` walks `_meta`
(multi-segment, raises, no cache). The shared
lenient rungs route to F-LENIENT, not here.
Trigger: the registry walk gains a second hop or
the classifier gains registry reads — unfired.
Home: the target-walk docstring + this finding.

### R32 — declaration/spelling/registry non-walks (rejected)

CONVERGE with verified orm OUT on fresh evidence,
each body re-opened at HEAD: permissions hops
(:596/:618 — declaration-graph prefix match, never
`get_field`); `flatten_lookup_path` (strings :252 —
`__` -> `_` mangler, produces identifiers, resolves
nothing); `resolve_globalid_target_definition`
(filters/base :638 — registry graph via
`related_target_for`); `_walk_selections` (walker
:673 — GraphQL-selection descent via field maps).
Difference per body: different subject and
mechanism, none a `_meta` multi-segment walk.
Trigger per body: the mechanism gains `_meta`
per-segment resolution — all unfired. Home: the
standing OUT record + this finding.

### R33 — relation-model reader (rejected)

CONVERGE with the verified rest_framework
`relation-model-of-vs-taxonomy-reads` direction on
fresh evidence. Difference: `_relation_model_of`
answers the relation's MODEL for schema/runtime
agreement attestation; the taxonomy answers
cardinality/rendering — different questions over
the same fields. Trigger: an agreement check
needing kind precision — unfired (attestation
still branches forward-M2M vs column vs other).
Home: the standing row + this finding.

### R-O — nested-plan orchestration (consumer-only converge, transcribes nothing)

The open `nested-connection-plan-orchestration`
family already lists this file; every edge from
that orchestration into this module is a by-name
consumption (accessor: nested-planner :1411,
walker :1057/:1270; kind: walker :212/:1297;
taxonomy legs), and no orchestration definition
lives here. No adoption, no new row — the family
item owns the orchestration; this note records
the consumer posture for its sweep.

## Defects

- D1 (stale projection, UNFIXED, minor — HOMED HERE
  from the `types/relations.py` context item, judged
  on fresh evidence): the `relation_kind` docstring
  names `(and the registry's typed PendingRelation
  sentinel)` (HEAD :180-181) as a consumer that
  disambiguates `reverse_many_to_one` from forward
  M2M. Both halves are stale at HEAD, re-verified
  fresh: the record carries no kind (5 slots +
  carries-none clause at [types-relations][types-relations]
  HEAD `5e9b5cdb`, post-`2bcd50bd`), the record is
  not a sentinel (`PendingRelationAnnotation` is),
  and the sole rewrite path branches
  `is_many_side`/`nullable` only (converters :795-806),
  collapsing both kinds identically. Owner:
  `utils/relations.py::relation_kind` docstring (drop
  the parenthetical or retarget it to the
  FieldMeta/optimizer consumers that actually read
  kind). Filed for normal closeout homing; the lines
  are byte-identical at HEAD (`8dbc3fe668dd`) and
  worktree (`05ff55b0`), outside every hunk. Not
  fixed inside this item (file item; zero-edit).
- D2 (stale projection, UNFIXED, minor — NEW):
  the `is_forward_many_to_many` docstring census
  (HEAD :626-633) names three consuming write
  surfaces but omits the fourth: forms
  `_model_column_for` ([forms-inputs][forms-inputs]
  HEAD :478, `if not is_forward_many_to_many(column):
  return None`). The call postdates the census text
  (`99a9f2d7` after `03538f36` — verified
  ancestor order), so the docstring never covered
  it. Owner: `utils/relations.py::is_forward_many_to_many`
  docstring (add the forms site). Filed for normal
  closeout homing. Not fixed inside this item.
- O1 (observation, not a defect): the orm-F1 durable
  clause exists only as ledgered worktree hunk H7;
  HEAD lacks it. Ledgered-orphan provenance; closeout
  decides landing, not this item.
- O2 (observation, not a defect): the concurrent
  worktree truth-migration deletes F-LENIENT's
  candidate owner body (`relation_attr`/`safe_truthy`
  absent in worktree `05ff55b0`). The family item
  re-derives on the landing state; standing R-C/R13
  verdicts are keyed to HEAD bytes `8dbc3fe668dd`.

## Pending execution

None. All behavioral proofs are `static-reviewed`
(censuses + bodies over pure-metadata surface — no
ordering, transactional, or async claim needs
execution; the verified families' execution probes
stand as prior evidence, not re-run). No
`execution-deferred` items. Sharded/PG cells
`inapplicable by construction`: the target executes
no ORM and reaches no database, alias, or dialect
decision. No workspace runs were made (read-only
trace; no source-mutating probe exists).

## Judgment

Hub module, fully single-owned per rule: the
taxonomy trio, the classifier + ladder + cache
pair, and the accessor each converge onto their
verified family with every trigger re-checked
unfired at HEAD bytes (one narrowing: taxonomy
R-I's snapshot half retired by `2bcd50bd`); the
lenient body adopts into the open
`lenient-relation-metadata-read` family (count 2,
coupling restated incl. the R13 interplay); five
rules stand file-local; 33 rejections carry
contract differences + triggers (29 converging,
4 fresh). Two minor doc-only defects filed for
closeout homing (D1 homed here, D2 new). No
consolidation inside this file item, no new
family, zero edits.

## Implementation (Worker-1)

No tracked changes. Worktree equals `ITEM_BASELINE`
(`4f015340`) for the target — the item-scoped diff
is empty. Hunk attribution vs `git show HEAD:`
(15 hunks, matched by content):

| Hunk | Content | Attribution |
|---|---|---|
| H1 `@@ -6,16` | imports (`FieldError` +, `_safe_type_name` -, `truth` +) | concurrent-external (hunt truth migration) |
| H2 `@@ -31,11` | `__all__` drops `relation_attr`/`safe_truthy` | concurrent-external |
| H3 `@@ -54,88` | deletes `safe_truthy`+`relation_attr`; rewrites `relation_bool`/`relation_name` on `getattr`+`truth.kind` | concurrent-external |
| H4 `@@ -234,10` | `is_many_side` drops `try/except` | concurrent-external |
| H5 `@@ -291,16` | `_resolve_segment_field` rewrite | concurrent-external |
| H6 `@@ -312,12` | `_is_traversable_relation` drops `try/except` | concurrent-external |
| H7 `@@ -340,6 +276,20` | `classify_path` docstring +14, pure additive | OWNED — ledger adopted orphan `orm-lookup-path-resolution` (verbatim below) |
| H8 `@@ -360,23` | classifier body drops `try/excepts`, `any()` | concurrent-external |
| H9 `@@ -452,35` | lookup-tail single `try` + `except FieldError` | concurrent-external |
| H10 `@@ -504,14` | lenient walk composes `_resolve_segment_field` | concurrent-external |
| H11 `@@ -536,16` | ladder drops `BaseException`->`False` arm | concurrent-external |
| H12 `@@ -589,9` | hash probe -> tuple + `TypeError` | concurrent-external |
| H13 `@@ -675,20` | forward-concrete drops containment | concurrent-external |
| H14 `@@ -718,32` | accessor `getattr`+`truth.kind`, drops guards | concurrent-external |
| H15 `@@ -760,11` | composite probe drops containment | concurrent-external |

Owned-hunk verbatim (worktree :280-292, the +14 of
H7 — the four-walkers-separate rationale the ledger
names, each clause matching the verified F1 walker
contract, the final sentence restating F1-T1/T2;
all four cited symbols resolve at HEAD):

```text
    Four other ``_meta`` path walkers share the split-and-``get_field``
    mechanism under different contracts and stay separate:
    ``connection.py::_resolve_order_path_field`` answers the terminal
    concrete column or ``None`` for cursor anchoring;
    ``plans.py::_select_path_traversable`` answers traversability under a
    consumer projection for prune decisions;
    ``utils/querysets.py::_prefetch_relation_target_or_none`` answers the
    terminal model or ``None`` (fail-open, with the default ``<model>_set``
    accessor spelling) for prefetch sealing;
    ``list_field.py::_resolve_order_field_path`` answers ``(field, related
    opts)`` or ``None`` for ordering-term certification. A caller needing
    another walker's answer, or this classifier gaining an accessor-name
    fallback or a non-raising mode, reopens the question.
```

The only new path is this artifact (untracked, owned
by this item). Dirt elsewhere (hunt migration,
concurrent edits) left alone; every connected region
relied on was read at HEAD bytes. No `.py` touched,
so no ruff run is owed. No commit per standing rule.
HEAD unmoved (`0c0537e2` at dispatch and at close).

## Index rows for Worker-0

| `utils-relations-strict-slot-read` | `django_strawberry_framework/utils/relations.py::relation_name` (strict str-or-None GenericRelation slot read, no lenient axis by design) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | file-local |
| `utils-relations-forward-m2m-predicate` | `django_strawberry_framework/utils/relations.py::is_forward_many_to_many` (forward-writable-M2M flag test splitting the kind collapse; D2 filed on the docstring census) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | file-local |
| `utils-relations-forward-concrete-predicate` | `django_strawberry_framework/utils/relations.py::is_forward_concrete_relation` (kind gate + column/related_model backing test per spec-036 L3-1) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | file-local |
| `utils-relations-composite-pk-probe` | `django_strawberry_framework/utils/relations.py::has_composite_pk` (multi-field-pk fail-closed elision gate) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | file-local |
| `utils-relations-module-mechanics` | `django_strawberry_framework/utils/relations.py` (module docstring + 7 imports + TYPE_CHECKING block + 17-entry `__all__` + `_MISSING` declaration; sentinel pair converges context R5 which already lists this file) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | file-local |
| `utils-relations-four-walkers` | `django_strawberry_framework/utils/relations.py::classify_path` (rejection recorded here; CONVERGE with verified orm F1 on fresh evidence — one mechanism, four contracts; T1/T2 re-checked unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/utils/querysets.py`, `django_strawberry_framework/list_field.py` | File `utils/relations.py` | rejected |
| `utils-relations-lookup-tail` | `django_strawberry_framework/utils/relations.py::validate_lookup_expr` (rejection recorded here; CONVERGE with verified orm F3 on fresh evidence — after-terminal cursor contract, zero production callers, staged API) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-pk-alias` | `django_strawberry_framework/utils/relations.py::_resolve_segment_field` (rejection recorded here; CONVERGE with verified orm matrix-3 on fresh evidence — per-contract pk derivation, no owned rule) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/list_field.py`, `django_strawberry_framework/optimizer/plans.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/relations.py` | rejected |
| `utils-relations-separator-spelling` | `django_strawberry_framework/utils/relations.py::classify_path` (rejection recorded here; CONVERGE with verified orm T3 on fresh evidence — spelling not a rule; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/optimizer/plans.py` | File `utils/relations.py` | rejected |
| `utils-relations-windowable-vs-many-side` | `django_strawberry_framework/utils/relations.py::MANY_SIDE_RELATION_KINDS` (rejection recorded here; CONVERGE with verified taxonomy R-A on fresh evidence — strategy vs cardinality; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-raw-vs-snapshot` | `django_strawberry_framework/utils/relations.py::relation_kind` (rejection recorded here; CONVERGE with verified taxonomy R-B on fresh evidence — remote_field/through carriage gap; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-one-read-body` | `django_strawberry_framework/utils/relations.py::relation_attr` (rejection recorded here; CONVERGE with verified taxonomy R-C on fresh evidence — two policies already one body; no third policy) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-write-decode-vocab` | `django_strawberry_framework/mutations/inputs.py::model_column_write_kind` (rejection recorded here; CONVERGE with verified taxonomy R-D on fresh evidence — forward-only decode vocabulary; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/mutations/inputs.py` | File `utils/relations.py` | rejected |
| `utils-relations-serializer-cardinality` | `django_strawberry_framework/rest_framework/serializer_converter.py::_model_relation_cardinality` (rejection recorded here; CONVERGE with verified taxonomy R-E on fresh evidence — DRF-alignment guard; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/rest_framework/serializer_converter.py` | File `utils/relations.py` | rejected |
| `utils-relations-cascade-predicates` | `django_strawberry_framework/permissions.py::_is_cascadable_edge` (rejection recorded here; CONVERGE with verified taxonomy R-F on fresh evidence — single-column composability; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/permissions.py` | File `utils/relations.py` | rejected |
| `utils-relations-to-field-predicate` | `django_strawberry_framework/filters/base.py::_relation_uses_non_pk_to_field` (rejection recorded here; CONVERGE with verified taxonomy R-G on fresh evidence — join-column question on an unread flag; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/filters/base.py` | File `utils/relations.py` | rejected |
| `utils-relations-column-screens` | `django_strawberry_framework/utils/relations.py::relation_kind` (rejection recorded here; CONVERGE with verified taxonomy R-H on fresh evidence — local backing questions; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/orders/inputs.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/rest_framework/resolvers.py`, `django_strawberry_framework/forms/inputs.py` | File `utils/relations.py` | rejected |
| `utils-relations-display-labels` | `django_strawberry_framework/management/commands/inspect_django_type.py::_RELATION_KIND_LABELS` (rejection recorded here; CONVERGE with verified taxonomy R-I on fresh evidence — NARROWED: labels stand, snapshot half retired by 2bcd50bd; leftover prose is D1) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/management/commands/inspect_django_type.py` | File `utils/relations.py` | rejected |
| `utils-relations-lenient-alias-pin` | `django_strawberry_framework/optimizer/join_taxonomy.py::_safe_getattr` (rejection recorded here; CONVERGE with verified join_taxonomy R13 on fresh evidence — local policy pin; trigger unfired at HEAD, FIRES on F-LENIENT landing per Coupling) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-morph-tri-split` | `django_strawberry_framework/utils/relations.py::relation_kind` (rejection recorded here; CONVERGE with verified join_taxonomy R14 on fresh evidence — detect/carry/resolve; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/field_meta.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-partition-vs-accessor` | `django_strawberry_framework/optimizer/join_taxonomy.py::_partition_expr` (rejection recorded here; CONVERGE with verified join_taxonomy R7 + accessor R-B on fresh evidence — attach key is not the accessor; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-reverse-accessor-scan` | `django_strawberry_framework/utils/querysets.py::_reverse_relation_by_accessor_or_none` (rejection recorded here; CONVERGE with verified accessor R-A on fresh evidence — reverse question, fail-open policy; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/querysets.py` | File `utils/relations.py` | rejected |
| `utils-relations-forward-name-reads` | `django_strawberry_framework/types/resolvers.py::forward_resolver` (rejection recorded here; CONVERGE with verified accessor R-D on fresh evidence — forward-only population, no derivation; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/types/resolvers.py` | File `utils/relations.py` | rejected |
| `utils-relations-n1-fallback` | `django_strawberry_framework/types/resolvers.py::_check_n1` (rejection recorded here; CONVERGE with verified accessor R-E on fresh evidence — None-tolerance, not a derivation; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/types/resolvers.py` | File `utils/relations.py` | rejected |
| `utils-relations-to-attr-grammar` | `django_strawberry_framework/optimizer/nested_planner.py::relation_connection_to_attr` (rejection recorded here; CONVERGE with verified accessor R-C on fresh evidence — attach namespace, field-name keyed; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/nested_planner.py`, `django_strawberry_framework/connection.py` | File `utils/relations.py` | rejected |
| `utils-relations-guarded-picker` | `django_strawberry_framework/optimizer/join_taxonomy.py::_first_truthy` (rejection recorded here; CONVERGE with verified join_taxonomy R4 on fresh evidence — picker consumes safe_truthy, not a rival; trigger unfired) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/optimizer/join_taxonomy.py` | File `utils/relations.py` | rejected |
| `utils-relations-frozen-idiom` | `django_strawberry_framework/utils/relations.py::ClassifiedPath` (rejection recorded here; CONVERGE with the verified hook-context frozen-record-idiom direction on fresh evidence — stdlib spelling, no shared driver) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-except-arms` | `django_strawberry_framework/utils/relations.py::classify_path` (rejection recorded here; CONVERGE with the verified J1 shared-except-guard direction on fresh evidence — per-site verdicts; trigger unfired) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-exact-type-gates` | `django_strawberry_framework/utils/relations.py::relation_bool` (rejection recorded here; CONVERGE with the verified J2 shared-exact-type-gate direction on fresh evidence — per-site exclusions; trigger unfired) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-message-wordings` | `django_strawberry_framework/utils/relations.py::relation_bool` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence — no owned grammar at HEAD; trigger unfired) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-twin-cache-split` | `django_strawberry_framework/utils/relations.py::_classify_path_cached` (rejection recorded here; fresh same-file separation — plan cache vs answer cache, different readers, one clear handle) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-gfk-three-tests` | `django_strawberry_framework/utils/relations.py::classify_path` (rejection recorded here; fresh same-file separation — untraversable vs virtual vs forward_single, three contracts) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-m2m-flag-test` | `django_strawberry_framework/utils/relations.py::is_forward_many_to_many` (rejection recorded here; fresh same-file separation — flag test deliberately not kind-routed; kind collapses forward/reverse M2M) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-forward-single-screens` | `django_strawberry_framework/utils/relations.py::is_forward_concrete_relation` (rejection recorded here; fresh triple — write backing vs cursor anchorability vs ordering certification) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/connection.py`, `django_strawberry_framework/list_field.py` | File `utils/relations.py` | rejected |
| `utils-relations-composite-vs-pk-projections` | `django_strawberry_framework/utils/relations.py::has_composite_pk` (rejection recorded here; CONVERGE with the verified join_taxonomy six-readers direction on fresh evidence — composite-ness vs name vs attname) | `django_strawberry_framework/utils/relations.py` | File `utils/relations.py` | rejected |
| `utils-relations-registry-vs-meta-walk` | `django_strawberry_framework/types/definition.py::related_target_for` (rejection recorded here; CONVERGE with verified orm OUT + definition F-RELTARGET on fresh evidence — single-hop registry lookup vs multi-segment _meta walk) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/types/definition.py` | File `utils/relations.py` | rejected |
| `utils-relations-non-walk-mechanisms` | `django_strawberry_framework/utils/permissions.py` (rejection recorded here; CONVERGE with verified orm OUT on fresh evidence — declaration hops, spelling mangler, registry-graph, selection descent; each body re-opened) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/utils/permissions.py`, `django_strawberry_framework/utils/strings.py`, `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/optimizer/walker.py` | File `utils/relations.py` | rejected |
| `utils-relations-model-reader` | `django_strawberry_framework/rest_framework/resolvers.py::_relation_model_of` (rejection recorded here; CONVERGE with the verified rest_framework relation-model-of direction on fresh evidence — agreement attestation vs cardinality) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/rest_framework/resolvers.py` | File `utils/relations.py` | rejected |

## Families

None new. One adoption into open `lenient-relation-metadata-read`
(F-LENIENT — family row + `## Families` item already exist and
already list both files; no new row owed). One consumer-only
converge onto open `nested-connection-plan-orchestration` (R-O —
row already lists this file; no new row owed). Three convergences
onto verified families (`relation-kind-taxonomy`,
`orm-lookup-path-resolution`, `relation-instance-accessor` —
their rows stand; triggers re-checked in F-TAX/F-ORM/F-ACC).

## Independent verification (Worker-2)

Recorded from my own trace (HEAD bytes via `git show HEAD:` /
`git grep HEAD`, worktree diff by content); the dispatch brief had
already summarized W1's claims at a high level, so every check below
was re-derived from the bodies rather than from the Findings text,
then reconciled row by row. No differences found.

### Own pre-reading trace

Target at HEAD (`8dbc3fe6`, 770 lines): the five-kind taxonomy
trio + read contract, the strict path classifier + records +
lenient ladder + cache pair, the lookup tail, the lenient read
body with two policies, the instance accessor, two
write-flavor predicates, the composite probe, module
mechanics. Consumers compose by name (stamp, walker, taxonomy,
planners, resolvers, finalizer, set flavors, write flavors);
oracles execute the owner or Django; docstrings project (two
stale censuses spotted independently, both confirmed below).
Definition counts per posited change: new relation shape 1,
sixth kind 1, generic change 1, path-form change 0 shared,
failure-mode change 0 shared / 5 independent, read-hardening 2
(owner body + definition rungs), accessor-scheme 0 moves / 1
holder, each predicate/probe 1. Owner choice per rule: here in
every case (leaf-ward, every consumer already imports without
reversal). Zero-edit file item: coverage + assignment only.

### (1) Enumeration 38/38 — STANDS

Independent `ast.parse` over HEAD bytes: `Module.body` = 38
nodes (docstring + 37 statements). W1's 38-row table homes all
38: docstring + 7 imports + TYPE_CHECKING block + `__all__` +
`_MISSING` to FL-MECH (11); `RelationKind`, `MANY_SIDE`,
`_RelationFieldLike`, `relation_kind`, `is_many_side` to F-TAX
(5); the 14 classifier/ladder/cache/tail members to F-ORM;
`safe_truthy`, `relation_attr`, `relation_bool` to F-LENIENT;
`instance_accessor` to F-ACC; `relation_name`,
`is_forward_many_to_many`, `is_forward_concrete_relation`,
`has_composite_pk` file-local (4). 11+5+14+3+1+4 = 38, no
member unassigned. Every HEAD line pin spot-checked against
`git show HEAD:` (all 38 match); `__all__` = 17 entries
(counted); hop 4 slots / path 6 slots / Protocol 5 members
confirmed present.

### (2) Hunk attribution — STANDS

`git diff HEAD` = 15 hunks (`@@` headers byte-match W1's
table), 92+/181-. H7 (`@@ -340,6 +276,20`) is +14 pure
additive, diffed byte-identical against W1's quoted block
(VERBATIM-MATCH), and matches the ledger's ONE owned hunk
(adopted orphan `orm-lookup-path-resolution`,
four-walkers-separate rationale on `classify_path`); all four
cited symbols resolve exactly once at HEAD
(`connection.py`, `plans.py`, `querysets.py`,
`list_field.py`). H1-H6 + H8-H15 are the concurrent
truth-migration by content (imports/`__all__`/`relation_attr`+
`safe_truthy` deletion, `relation_bool`/`relation_name`
rewrite on `getattr`+`truth.kind`, `BaseException`-arm
narrowing/removal across 8 bodies, tuple-hash probe,
`_resolve_segment_field` rewrite) — none matches the ledger,
none stops the item. The D1/D2 regions sit outside every
hunk (verified in the diff).

### (3) Three convergences — STAND

F-TAX: `def relation_kind` census = 2 at HEAD (owner +
FieldMeta one-line `return relation_kind(self)` delegate,
re-opened — consumer by construction); `MANY_SIDE` zero
direct production importers (census — principle-11 keep
stands). All 9 triggers re-checked: R-A sets differ exactly
on `reverse_one_to_one` (WINDOWABLE has 4 incl. generic,
re-read); R-B no `remote_field`/`through` slots on FieldMeta
(3 prose hits only); R-C sole `lenient=True` consumer is
join_taxonomy :96/:104 (whole-package grep = 2 lines, 1
module), no third policy; R-D screen, R-E guard, R-F/R-G/R-H
sites all present at HEAD (each `def` counted 1); R-I
NARROWED — `2bcd50bd` message + HEAD record (5 slots,
carries-none clause) confirm the snapshot half is retired,
labels half stands.

F-ORM: `def classify_path` = 1; the four walker
subject/failure/return triples re-derived unchanged at HEAD
(connection :787 raise-free column-or-None with the
forward_single+non-null screen at :812, plans :653
projection traversability, querysets :2306 fail-open model,
list_field :716 certification pair); T1/T2 unfired (no
cross-walker caller, no accessor fallback / non-raising
mode — HEAD body raises); T3 unfired (literals still at
connection :800 / plans :679, re-read); field_meta R3
unfired (single-hop `_target_pk_name`).

F-ACC: `def instance_accessor` = 1; exactly 6 calls across 5
modules at HEAD (field-meta :299, walker :1057/:1270,
nested-planner :1411, finalizer :776, resolvers :535 —
line-for-line match); connection pure reader (0 calls).
Triggers: R-A helper strict-only + scan present at querysets
:2356; R-B attach-key contrast in both docstrings; R-C
grammar field-name keyed (nested-planner :729 def,
connection :2137 paragraph — both re-read); R-D forward-only
population; R-E helper never returns `None` (raises).

### (4) F-LENIENT adoption + R-O — STAND

F-LENIENT: definition.py rungs re-read at HEAD `fa6c4d33`
(:315-317 `is_relation`->False, :322-324
`related_model`->None — two rungs, one spelling); count 2
(owner body + inline idiom) matches the naming finding; the
owner body (`relation_attr` + `relation_bool` + `safe_truthy`
half) is one body with two policies at HEAD; field-meta 17
strict calls counted; join-taxonomy the sole lenient
consumer. Coupling restated correctly incl. the R13
interplay — R13's trigger text ("a second `lenient=True`
consumer appears") was re-read in the join_taxonomy
artifact, so landing the adoption fires it and the family
item must adjudicate the alias move; R-C holds regardless.
O2 correctly keys all of this to HEAD bytes (worktree
deletes the body).

R-O: nested-planner :1411 + walker :1057/:1270 (accessor)
and walker :212/:1297 (kind) re-read at HEAD — all by-name
consumptions; no orchestration definition lives here. The
open family row already lists this file: transcribes
nothing, correct.

### (5) 33 rejections — ALL STAND

29 converging: every standing record confirmed (orm
F1/F3/matrix-3/T1/T2/T3/OUT in the verified artifact;
taxonomy R-A..R-I in the verified artifact; accessor R-A..R-F
in the verified artifact; join_taxonomy R4/R7/R8/R13/R14 by
number in its artifact; J1/J2, per-subject-grammars,
hook-context idiom, six-readers, relation-model-of,
definition F-RELTARGET, open
`relation-connection-to-attr-grammar` rows in the plan).
Each trigger re-checked unfired at HEAD (censuses above
plus: `_first_truthy` consumes `_safe_truthy` :110, not a
rival; generic-slot readers exactly 3 files; `to_attr`
grammar field-name keyed; permissions-hops splits at :596
/:618; `flatten_lookup_path`, registry-graph walk,
selection descent each re-opened with a different
subject/mechanism).

4 fresh, each verified at its body: R26 twin caches hold
(plan) vs (bool) with one clear handle (:521-531 / :551-554
/ :599-608); R27 GFK is untraversable to the classifier
(:306-320), virtual to the column predicate (:668-676 +
:686-689), `forward_single` to the kind classifier (no
generic slots) — three contracts, three tests; R28 the M2M
predicate deliberately flag-tests because kind collapses
forward/reverse M2M (docstring states it, :615-638); R29
the three forward-single screens (write backing here vs
cursor anchorability at connection :812 vs certification
refusal at list_field :716) answer three questions.

### (6) D1 homed here — VERIFIED, defect bar MET

Fresh at HEAD bytes: the parenthetical names the registry's
typed `PendingRelation` sentinel as a kind-disambiguating
consumer. Both halves stale: the HEAD record carries no
kind (5 slots + carries-none clause, post-`2bcd50bd` whose
message states the removal) and is not a sentinel
(`PendingRelationAnnotation` is); the sole rewrite path
(converters `resolved_relation_annotation`, re-read)
branches `is_many_side`/`nullable` only, collapsing both
kinds identically; package-wide `PendingRelation` census =
ledger files + this docstring line only. Lines byte-identical
HEAD vs worktree, outside every hunk. Bar: DRY.md defect
class docstring-contradicts-body; feasible shape (any
relational `DjangoType`); harm concrete for a DRY cycle
(principle 10 — the next author preserves a dead
distinction); minor doc-only, closeout homing, not a
blocker. Homing here is correct (owner is this file).

### (7) D2 new — VERIFIED, defect bar MET

Fresh at HEAD bytes: the `is_forward_many_to_many`
docstring census (HEAD :626-633) names three write surfaces
(mutations x2 + DRF) but omits the fourth consumer,
forms `_model_column_for` (HEAD :478 `if not
is_forward_many_to_many(column): return None`, inside the
documented M2M arm — re-read with context). Consumer census
at HEAD = exactly 4 (forms :478, mutations :292/:503, DRF
:1865). Drift direction proven: `03538f36` wrote the census
paragraph, `99a9f2d7` added the forms call (parent has 0
occurrences; commit body covers `_model_column_for`
resolution), and `03538f36` is an ancestor of `99a9f2d7` —
the docstring never covered it. Bar: same class as D1
(stale exhaustive census misleads the next author about the
predicate's consumer set); minor doc-only, closeout homing.
FL-FCON's 2-consumer census re-verified exact (forms :480,
mutations :505); `has_composite_pk` sole caller field-meta
:319; `relation_name` callers field-meta x2 + in-file x2.

### Freshness, state, prose

All 20 HEAD pins re-hashed via `git rev-parse HEAD:` —
digit-for-digit match (field-meta `18ea719a`,
join-taxonomy `9b355a50`, walker `75f9c6b6`, filters/sets
`993e887a`, connection `4894f90f`, resolvers `72d62dc4`,
inspect `2807d0fc`, relations-suite `e51cebaa`, plans
`cce98531`, querysets `3616927d`, list_field `21380eb7`,
orders/sets `6044ab1a`, nested-planner `b4dfd4a6`,
finalizer `de34ae2a`, definition `fa6c4d33`, mutations
`fc442047`, resolvers-drf `0d302782`, forms `6418753d`,
leaf `1a4c2ec8`, taxonomy-suite `481294c3`). Matrix: axis 2
inapplicable sound (0 `async def`/`await` in 770 HEAD
lines); all 6 axes discharged with searches
(`one_to_many` 6 files / `many_to_many` 12 files re-counted;
oracles 80 `def test` counted). Item diff still empty
(`git diff 4f015340 -- django_strawberry_framework/` prints
nothing); HEAD unmoved (`0c0537e2`); worktree blob still
`05ff55b0`. Zero-edit: no equivalence proof, no ruff input,
no oracle rewritten. AGENTS.md prose: `path::Symbol` cites,
raw `:NN` pins permitted in `dry-*.md`, no process
provenance, 10/10 link groups intact. Index rows: 38
pipe rows counted (5 file-local + 33 rejected; R-O
correctly transcribes nothing). Pending execution None
correct; sharded/PG inapplicable sound (pure metadata
reads, no ORM execution). No new families owed. No
Worker-2 defects.

Immaterial record notes (no home/count/gate moves): (a)
F-ORM "3 spec hits" for the tail — grep finds 4 across
spec-058/060 (1+3); staged-API verdict unaffected. (b) D1
pin ":180-181" — the parenthetical + `can disambiguate`
are HEAD :179-180; content quotation exact. (c) FL-MECH
"typing x4" — the typing import binds 5 names; manifest
verdict unaffected.

Verdict: `verified`. Convergences (F-TAX with the R-I
narrowing, F-ORM, F-ACC), adoption (F-LENIENT count 2),
consumer-only R-O, all 33 rejections, and D1/D2 homing
stand as filed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-relations]: ../../tests/utils/test_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
