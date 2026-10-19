# DRY review: `types/definition.py`

Status: verified
Run: 0.0.15 2026-09-28-7

## System trace

Target [types-definition][types-definition] at HEAD blob
`fa6c4d33` (468 lines; worktree `1c59a3fe`, 434 lines, is
concurrent-external hunt dirt — the `truth.*` migration — absent from
the ledger and the cycle baseline; traced at HEAD bytes throughout,
both fingerprints recorded, nothing tracked touched). The module owns
three things: the `DjangoTypeDefinition` canonical metadata record
(29 slots) every subsystem reads; the `graphql_type_name` surface-name
derivation gate; and two fail-soft lookups — `related_target_for`
(relation → `(target_definition, model_field)`) and the custom-id
detection cluster (`has_custom_id_resolver_for` /
`origin_has_custom_id_resolver` + four helpers) guarding the
optimizer's FK-id elision.

Sites found (HEAD bytes; `C` = consumer, `O` = oracle, `P` =
projection). Name derivation: definition :241 (the one derivation),
9 consumer files (`connection`, `filters/base`, [filters-inputs][filters-inputs] via
`_owner_type_name`, `finalizer`, `inspect`, `registry`
(`definition_for_graphql_name`), root `relay`, `testing/relay`,
`types/relay`); `origin.__name__` census finds no inline copy (the two
other hits are Python-class display labels). Name gate: the
`fullmatch` census is exactly 3 tokens (`scalars` foreign regex +
[types-base][types-base] :1295 + this file :257) — the open
`graphql-name-gate` pair. Relation lookup: `filters/base` :675 (direct
call in the `__`-walk), `filters/sets` :2091 (lenient `getattr` +
callable probe, registry fallback), `walker` :498 (pair spent whole,
registry-only fallback), `finalizer` :1222–1223 (owner-agreement
check). Id detection: `walker` :1460/1466 (memoized path +
definition-less fallback through the same free function). Caches: both
private dicts are read/written only in this file (6 touch lines + 2
field declarations).
Slots: single construction at [types-base][types-base] :795, single
stamp at :824, single `finalized` flip at [types-finalizer][types-finalizer]
:1147, single `relation_connections` write at :538, single
`definition.connection` read at [connection][connection] :1517; no
package read of `definition.primary` (introspection mirror as
documented); `fields_class` has no reader (forward-reserved as
documented). Oracles: [test-definition-relations][test-definition-relations]
(23 tests, all three surfaces incl. hostile arms, cache literals,
message spellings; independent — they drive inputs, never read owner
tables) plus the disjoint `Meta.name` half in
[test-base][test-base] :292–323. Projections: the 15-clause class
docstring (each clause verified against its owning body), the
`relation_connections` glossary line, TREE one-liners, the KANBAN 053
bullet homing D1, and 8 spec-Decision cites (all resolve).

Connected behavior examined: the base construction pipeline
(`__init_subclass__`, `_select_fields` order, sidecar population, the
four-corner union), the finalizer bind/audit/flip steps, the relay
install + strategy resolver + composite gate + `_node_id_default`,
the registry lookup quartet (`get` / `get_definition` /
`primary_for` / `is_finalized`), the exceptions safe-renderers, the
walker elision guard + id-column projection + fallbacks, the filterset
lenient consumer + `__func__` override detector, the forms
`_model_column_for` opposite-polarity pair, `relation_attr` /
`relation_bool` (the lenient-read owner), `_plain_text`, the
`_validate_djangotype_target` proof, the testing-mint gate, and the
CLI predictor. Also read with no rule interaction:
[types-relations][types-relations] (pending-relation deferral,
referenced by base/finalizer, never by this file),
[types-resolvers][types-resolvers] (consumes `field_map` /
`has_custom_get_queryset` / `selected_fields` by name — consumer
posture), and [exceptions][exceptions] (the composed safe-renderers).

## Verification

### Matrix

**1. Cross-flavor policy mirroring.** Read every sibling flavor for a
mirror of the three rules. Filters consumes all three by name (walk,
acceptance set, strategy stamp); orders mirrors nothing (its sidecar
binds through the SAME finalizer body as filters — `related_attr` +
filter-only hook, one body with an adapter, finalizer-owned);
mutations resolves relation INPUT names (the reverse-map owner), never
definitions; forms resolves backing COLUMNS with opposite relation
polarity and opposite failure posture (R9); DRF reaches the strategy
stamp only through `decode_model_global_id`; auth reaches nothing.
The one mirror-shaped pair (`_model_column_for`) is a rejection, not a
family. No flavor re-derives the surface name (9 consumers compose the
property). No second id-detection exists in any flavor.

**2. Sync/async twins.** Inapplicable with reason: token grep over HEAD
bytes for `async def` / `await` / `sync_to_async` / `asyncio` returns
0; all 8 callables are sync, the module executes no ORM and crosses no
await boundary (registry dict probes + pure string/class reads only).
Considered `one-sync-boundary` and `async-only-queryset-row-adapter`:
checked, no surface (Exclusions).

**3. Derived rather than repeated knowledge.** Audited every
derivation: (a) the surface-name derivation is single-sited (:241);
all 9 consumer files compose it; the `origin.__name__` census (4
hits: derivation + docstring + 2 display labels) closes the
no-inline-copy claim. (b) The `(definition, field)` pair derives once
(`related_target_for`); the walker/filters fallbacks answer different
shapes with different postures (R11). (c) pk identity is NAME
vocabulary end to end (`_target_pk_name` → predicate tuple arm;
`attname` × 0 here — R8). (d) The MRO walk here is a marker scan, the
fourth MRO question alongside dispatch/override/collection (R7). (e)
`str.__str__` normalization is per-site vocabulary with 3 verdicts
(R1). (f) `_meta.get_field`-by-name resolutions each answer their own
question; the closest pair is opposite-polarity (R9).

**4. Inverse / round-trip pairs.** (a) GlobalID encode/decode is owned
by [types-relay][types-relay] (payload memberships + encoder/decoder);
this file declares the two slots the pair writes/reads (raw override +
effective stamp) — declaration posture, no pair owned here. (b)
`relation_connections` is ONE map (generated → underlying) written
once (:538-leader finalizer) and read in both directions — two read
directions, not a pair. (c) Declaration gate (base :1295) +
derivation gate (:257) is the open `graphql-name-gate` pair (C1). (d)
Effective-slot read (honor the install) vs raw-annotation scan
(bypass it) is a rejection (R14). (e) The per-method cache write/read
pairs are intra-body disciplines, not cross-site pairs.

**5. Contracts restated in another medium.** Per rule: production (this
file) + oracles ([test-definition-relations][test-definition-relations]
23 tests; every hostile arm, both caches incl. negatives, all four
name messages, the unhashable/empty-input gates — plus the disjoint
[test-base][test-base] half proving the C1 count) + projections (the
15-clause class docstring, verified clause-by-clause against owner
bodies; glossary/TREE one-liners; 8 spec-Decision cites, all
resolving; the KANBAN 053 bullet). Media counted per finding; oracles
listed, never counted; the docstring is projection (D1/D2 filed where
it contradicts its sources).

**6. Enforcement by omission.** Enumerated the fail posture of every
public entry and every fail-soft arm: `graphql_type_name` raises (wrap
+ trio, 4 messages); `related_target_for` degrades to `None` on all 7
unreadable steps; `has_custom_id_resolver_for` answers `False` for
malformed pk (never cached) and delegates otherwise; the module
function answers `False` for malformed pk and fail-closed `True` for
unreadable class metadata; `_resolves_id_off_pk` answers `False` for
non-Node + absent-annotation and `True` for hostile remainder;
`_class_has_custom_id_resolver` answers `False` for absent markers and
`True` for unreadable namespaces; `_is_framework_relay_id_resolver`
answers `False` for unreadable descriptors (→ consumer-owned
upstream). Each posture is established by its docstring + named
oracles; both caches key on validated input only (unhashable inputs
rejected pre-cache, pinned). One step lacks its guard: the
`is_relation` truthiness test escapes hostile `__bool__` (D3, contract
source: the "never an exception" test rule + the owner's own
read-and-truth-test doctrine). No other omission; the
None/False/True/raise variance across methods is per-contract (lookup
vs gate vs safety predicate vs derivation), each with a source.

### Enumeration

Instrument: `ast.parse` over the pinned HEAD blob
`fa6c4d330e72d7dceb5f2af7f56e460c6cf72383`, counting
`ast.Module.body` members — **17 top-level statements** (1 docstring +
9 import statements binding 13 names + 1 regex + 1 class carrying 29
slots + 3 methods + 5 functions). Every member lands below; the class
is further mapped slot-by-slot (32/32); every challenge ends in a
family row, a file-local row, or a rejection. (HEAD line numbers
throughout.)

| # | Statement (HEAD) | Binds / carries | Home |
|---|---|---|---|
| 0 | module docstring (one-line record statement) | prose projection | F-MECH |
| 1 | `from __future__ import annotations` | deferred evaluation | F-MECH |
| 2 | `import re` | `re` (name regex) | F-MECH |
| 3 | `from collections.abc import Callable` | strategy annotation | F-MECH |
| 4 | `from dataclasses import dataclass, field` | record + cache fields | F-MECH |
| 5 | `from typing import Any, Literal` | cache/spec annotations | F-MECH |
| 6 | `from django.db import models` | `models` (model/field types) | F-MECH |
| 7 | `from ..exceptions import ConfigurationError, _safe_arg_repr, _safe_type_name` | raise + render vocabulary | F-MECH |
| 8 | `from ..optimizer.field_meta import FieldMeta` | `field_map` values | F-MECH |
| 9 | `from ..optimizer.hints import OptimizerHint` | hints values | F-MECH |
| 10 | `_GRAPHQL_NAME_RE` (:16) | name grammar | C1 facet |
| 11 | `class DjangoTypeDefinition` (:20: docstring + 29 slots + 3 methods; slot map below) | canonical record + 3 rules | F-RECORD + F-OVERRIDES + F-SIDECARS + F-SHAPE + F-STRATEGY + F-RELTARGET (+ FAM-LENIENT facet) + F-CUSTOMID + C1 facet |
| 12 | `origin_has_custom_id_resolver` (:374) | shared detector | F-CUSTOMID |
| 13 | `_normalize_pk_name` (:397) | pk-name normalizer | F-CUSTOMID |
| 14 | `_resolves_id_off_pk` (:407) | NodeID placement probe | F-CUSTOMID |
| 15 | `_class_has_custom_id_resolver` (:440) | namespace marker scan | F-CUSTOMID |
| 16 | `_is_framework_relay_id_resolver` (:454) | default recognition | F-CUSTOMID |

Slot map for #11 (32/32 = 29 fields + 3 methods):

| Slots / methods | Home |
|---|---|
| `origin`, `model`, `name`, `description`, `fields_spec`, `exclude_spec`, `selected_fields`, `field_map`, `optimizer_hints`, `has_custom_get_queryset`, `primary`, `interfaces`, `finalized` (13) | F-RECORD |
| `consumer_authored_fields`, `consumer_annotated_relation_fields`, `consumer_annotated_scalar_fields`, `consumer_assigned_relation_fields`, `consumer_assigned_scalar_fields` (5) | F-OVERRIDES |
| `filterset_class`, `orderset_class`, `fields_class` (3) | F-SIDECARS |
| `connection`, `cursor_field`, `relation_shapes`, `relation_connections` (4) | F-SHAPE |
| `globalid_strategy`, `effective_globalid_strategy` (2) | F-STRATEGY |
| `related_target_for` + `_related_target_cache` | F-RELTARGET (+ FAM-LENIENT facet on the :316/:323 read rungs) |
| `has_custom_id_resolver_for` + `_custom_id_resolver_cache` | F-CUSTOMID |
| `graphql_type_name` | C1 |

Rules: 8 file-local (F-MECH, F-RECORD, F-OVERRIDES, F-SIDECARS,
F-SHAPE, F-STRATEGY, F-RELTARGET, F-CUSTOMID); 1 new holding family
(FAM-LENIENT `lenient-relation-metadata-read`, count 2); 3
convergences (C1 `graphql-name-gate`, C2 `optimizer-hint-shape`, C3
`type-registry-finalize-gate` — all transcribing nothing); 19
rejections (R1–R19, 8 converging on verified rows with fresh trigger
checks, 11 fresh). Index rows named for Worker-0: 28 (8 file-local + 1
new family + 19 rejected).

### Challenges

Each change posited against the rule's own variation axes; the count
is authoritative definitions only. Consumers, oracles, projections
listed, never counted ([dry][dry] Vocabulary). All bodies judged at HEAD bytes. Static review
only: no probe was run because every verdict rests on body comparison,
whole-tree census greps, and pinned oracles — no behavior exists that
an execution could distinguish and the cited oracles do not already
cover (D3's hostile-truthiness shape is decided by language semantics
+ the owner's own doctrine, likewise static).

| # | Rule | Change posited | Definitions forced | Verdict |
|---|---|---|---|---|
| 1 | F-MECH | add/remove a module import (new consumer edge) | 1 (this block; the leaf manifest is a different surface) | F-MECH |
| 2 | F-RECORD | add a 30th slot | 1 (the dataclass; construction + readers are consumers) | F-RECORD |
| 3 | F-RECORD | rename a slot | 1 + consumers | F-RECORD |
| 4 | F-OVERRIDES | add a fifth corner | 1 here (vocabulary; the base union arm is base's rule) | F-OVERRIDES |
| 5 | F-SIDECARS | wire the FieldSet sidecar | 0 here (slot reserved) + base/finalizer (their rules) | F-SIDECARS |
| 6 | F-SHAPE | add a synthesis slot | 1 | F-SHAPE |
| 7 | F-STRATEGY | add a sixth classification string | 0 here (slot admits any `str`) + relay install (its rule) | F-STRATEGY |
| 8 | F-STRATEGY | change the guard sentinel (`None` → `UNSET`) | 1 (default + contract here) + install/readers (consumers) | F-STRATEGY |
| 9 | F-RELTARGET | resolve through pre-finalize (pending) types | 1 (cache arm + walk) | F-RELTARGET |
| 10 | F-RELTARGET | GFK gains `related_model` | 1 (target-model arm) | F-RELTARGET |
| 11 | F-RELTARGET | key the cache by `(name, attname)` | 1 (cache discipline) | F-RELTARGET |
| 12 | F-CUSTOMID | add a third marker spelling | 1 (`resolver_names`) | F-CUSTOMID |
| 13 | F-CUSTOMID | exempt a fourth framework default | 1 (`_is_framework_relay_id_resolver`) | F-CUSTOMID |
| 14 | F-CUSTOMID | allow off-pk elision when the stub carries the column | 1 (`_resolves_id_off_pk`) | F-CUSTOMID |
| 15 | F-CUSTOMID | normalize folds pk names (strip/case) | 1 (`_normalize_pk_name`; two call sites, one body) | F-CUSTOMID |
| 16 | name grammar | allow the `__` prefix | **2** (base :1295 + :257) | C1 holding family |
| 17 | normalization | non-`str` verdict change (raise → coerce) | 1 (per-site; out of the family) | R1 |
| 18 | wording | reword one name message | 1 (that message) | R4 |
| 19 | copy step | change the copy primitive (impossible — stdlib) → 0; change one verdict → 1 | 0 / 1 | R1 |
| 20 | except breadth | change one arm's verdict (e.g. corrupted `_meta` raises) | 1 (that arm) | R2 |
| 21 | type gates | flip one `isinstance` gate to exact-type | 1 (that gate) | R3 |
| 22 | grammar | adopt one owned rejection-message grammar | 0 (no owner at HEAD; trigger unfired) | R4 |
| 23 | sanitize | allow `__`-prefixed enum members unprefixed | 1 (converters only; gates untouched) | R5 |
| 24 | probe timing | probe callers need tuple-declared shapes | trigger unfired (no tuple at the probe site) | R6 |
| 25 | MRO reads | harden every MRO read (identity-scan posture) | 1 here (walks move separately) | R7 |
| 26 | pk identity | identity read needing name + attname together | trigger unfired (`attname` × 0 here) | R8 |
| 27 | column policy | ModelForm treats reverse relations as columns | 1 (forms only; opposite polarity) | R9 |
| 28 | proof strength | list-field proof gains a fourth arm | 1 (list-field only; no proof obligation here) | R10 |
| 29 | fallback guards | walker fallback gains `except` arms | 1 (walker only; different posture) | R11 |
| 30 | suppression | suppression removes a second field | 1 (synthesis performer only) | R12 |
| 31 | slot mapping | decode needs the slot's FIELD (not just attr) | 1 (`_node_id_slot` only) | R13 |
| 32 | annotation scan | composite gate honors installed defaults | 1 (types/relay scan only) | R14 |
| 33 | default identity | Strawberry renames `Node.resolve_id` | 1 (the `node_default` arm) | R15 |
| 34 | projection | projection switches to name-only matching | 1 (walker projection only) | R16 |
| 35 | pk verdict | pk normalization raises on malformed | 1 (ours; `_plain_text` untouched) | R17 |
| 36 | gate verbs | unify all finalized gates into one verb | refused (5 verbs); a 6th verb → 1 | R18 |
| 37 | registry import | hoist to module top | 0 (statically safe; stated reason wrong → D2) | R19 |
| 38 | relay imports | hoist to module top | 0 (safe; weight/colocation) | R19 |
| 39 | read mechanism | harden how relation metadata is read | **2** (owner + inline idiom) | FAM-LENIENT |
| 40 | lenient outcome | lenient gains a third outcome (log-and-default) | **2** (owner + inline idiom) | FAM-LENIENT |

## Findings

### F-MECH — module mechanics (file-local)

- **Contract + variation.** One-line record statement; 9 import
  statements binding 13 names, every one consumed (regex, record
  machinery, annotations, raise + render vocabulary, `field_map` /
  hints value types); 3 in-function lazy sites (registry + FieldDoesNotExist
  at :290–292, strawberry relay at :418–419, `.relay` default at
  :456–458). Varies only as the module's consumer edges do.
- **Sites + roles.** Definition: this block. Consumers: every symbol in
  the module. The registry site's "Do NOT hoist" comment states a
  `definition -> registry -> definition` cycle — the stated mechanism
  is wrong (D2); the relay sites state no reason (weight/colocation —
  R19). The verified `types-dependency-direction-prose` row owns the
  subpackage direction; this block's edges conform to it (no new
  evidence for that row).
- **Challenges.** #1 counts 1 (a tenth import lands here; the sibling
  `types/__init__.py` leaf manifest is a different surface under its
  verified row).
- **Owner + lifetime.** This module (mechanics have no lifetime).
- **Migration.** None — zero-edit.
- **Distinct behavior.** `Callable`/`Literal`/`field`/`Any` are
  annotation/slot machinery only (verified by use census).
- **Behavioral proof.** `static-reviewed` (import composition +
  name-use census; inspection decides).
- **Structural gate.** None owed (mechanics; RUF022 + the import census
  already execute in CI).
- **Coupling.** D2 (the registry comment's rationale).
- **Freshness.** Target `fa6c4d330e72` (worktree `1c59a3feec53`,
  unjudged); [registry][registry] `81bd561c99cb`;
  [types-relay][types-relay] `524398622354`.

### F-RECORD — canonical metadata record (file-local)

- **Contract + variation.** The 13 core slots (`origin`, `model`,
  `name`, `description`, `fields_spec`, `exclude_spec`,
  `selected_fields`, `field_map`, `optimizer_hints`,
  `has_custom_get_queryset`, `primary`, `interfaces`, `finalized`) form
  the one collected record every subsystem reads. Invariants, each
  verified at HEAD: single construction at [types-base][types-base]
  :795 (only `DjangoTypeDefinition(` package-wide); single stamp at
  :824; `field_map` never mutated post-construction (no
  `definition.field_map[...] =` write; only reads + local bindings);
  `selected_fields` in `_meta.get_fields()` order (base
  `_select_fields` promises it); `finalized` flipped exactly once
  ([types-finalizer][types-finalizer] :1147, only writer);
  `description` consumed once (:1146 `strawberry.type` call);
  `primary` read by no package code (introspection mirror as
  documented; runtime predicate is `registry.primary_for`).
  Varies as the record shape (add/rename a slot).
- **Sites + roles.** Definition: the dataclass. Construction consumer:
  `DjangoType.__init_subclass__`. Readers: registry, optimizer,
  finalizer, relay, resolvers, filters, inspect (census per slot in
  the trace). Oracles: construction is pinned by every `DjangoType`
  test; equality-minus-caches by :608–632.
- **Challenges.** #2/#3 count 1 (construction + readers are consumers
  of the shape, listed not counted).
- **Owner + lifetime.** This module for the shape; principle-4
  lifetimes: construction-time slots immutable post-construction;
  `finalized` write-once at finalization.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Population (base), validation (base),
  finalization writes (finalizer), and setting-snapshot storage
  (registry) stay at their owners; this row owns the shape only.
- **Behavioral proof.** `static-reviewed` (single-construction +
  single-writer censuses; inspection decides).
- **Structural gate.** None owed (shape; the construction census is
  the standing proof).
- **Coupling.** None.
- **Freshness.** Target `fa6c4d330e72`; base `dda91365a7e8`;
  finalizer `de34ae2aaed1`; registry `81bd561c99cb`.

### F-OVERRIDES — four-corner override contract (file-local)

- **Contract + variation.** The 5 frozenset slots (4 corners +
  `consumer_authored_fields` union input). The union is BUILT at
  [types-base][types-base] :730 (base's rule, verified F-COLLECT) and
  READ as the short-circuit by `_build_annotations` + the CLI table
  (:265); this row owns the corner vocabulary + slot declarations.
  Varies as the corner vocabulary.
- **Sites + roles.** Definitions: slots here (vocabulary), union
  expression in base (composition — a different rule, listed not
  counted). Consumers: synthesis short-circuit, inspect display.
- **Challenges.** #4 counts 1 here (a fifth corner adds a slot; the
  base union arm moves under base's rule).
- **Owner + lifetime.** Slots here, immutable post-construction;
  union composition in base.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Corner detection (annotation scan +
  assigned walk) stays in base (verified F-AUTO/F-ASSIGN).
- **Behavioral proof.** `static-reviewed` (construction + reader
  census).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `fa6c4d330e72`; base `dda91365a7e8`;
  inspect `2807d0fc9d75`.

### F-SIDECARS — set sidecar slots (file-local)

- **Contract + variation.** `filterset_class` / `orderset_class`
  (populated from validated `Meta` at base :813–814, bound by the ONE
  finalizer body at :1214 shared across both flavors) +
  `fields_class` (forward-reserved `None`; D1 filed on its stale
  TODO anchor). Varies as the sidecar vocabulary.
- **Sites + roles.** Definitions: slots here. Populate consumer:
  base construction. Bind consumer: finalizer phase 2.5 (one body,
  filter-only hook adapter — finalizer's rule).
- **Challenges.** #5 counts 0 here (FieldSet wiring moves base +
  finalizer; the reservation already exists — the reservation
  relieves the change).
- **Owner + lifetime.** Slots here; binding owned by finalizer.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Sidecar VALIDATION stays in base (verified
  F-SIDECAR); materialization of input globals stays in finalizer.
- **Behavioral proof.** `static-reviewed`.
- **Structural gate.** None owed.
- **Coupling.** D1 (the reservation's anchor).
- **Freshness.** Target `fa6c4d330e72`; base `dda91365a7e8`;
  finalizer `de34ae2aaed1`.

### F-SHAPE — connection/cursor/shape synthesis slots (file-local)

- **Contract + variation.** `connection` (normalized
  `{"total_count": bool} | None`, single code reader
  [connection][connection] :1517), `cursor_field` (validated order
  strings or `None`; column contract enforced by `keyset` at
  finalization), `relation_shapes` (pre-normalized values, consumed by
  the synthesis at finalizer :676 with absent-keys-default), and
  `relation_connections` (generated → underlying map, written once
  per attached sibling at finalizer :538 — the only indexed write —
  and read by the [walker][walker] :368 + [inspect][inspect] :354). Varies per slot's
  grammar.
- **Sites + roles.** Definitions: slots here. Validators: base
  stage-1/2 (verified rows). Writers/readers: finalizer synthesis,
  connection factory, keyset, walker — all consumers.
- **Challenges.** #6 counts 1 (a new synthesis slot is declared
  here; its validator + writer are their owners' rules).
- **Owner + lifetime.** Declarations here; `relation_connections`
  write-once-per-sibling at finalization, read-only afterwards.
- **Migration.** None — zero-edit.
- **Distinct behavior.** The `totalCount` emission rule stays in
  `connection.py`; cursor byte rules stay in `keyset.py`; shape
  defaulting stays in the synthesis.
- **Behavioral proof.** `static-reviewed` (single-writer +
  single-reader censuses).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `fa6c4d330e72`; base `dda91365a7e8`;
  finalizer `de34ae2aaed1`; connection `4894f90fb296`; walker
  `75f9c6b65ed1`; inspect `2807d0fc9d75`.

### F-STRATEGY — GlobalID strategy slots (file-local)

- **Contract + variation.** `globalid_strategy` (raw per-type
  override, `None` = fall through to the setting snapshot then the
  package default) + `effective_globalid_strategy` (finalization-time
  classification string, set exactly once by the install step —
  two assignment lines inside ONE step body — doubling as its
  re-entrancy guard; `None` = not framework-decodable). The raw-vs-
  classification distinction (a callable value vs the `"callable"`
  string) is spec-031 Decision 10, recorded on both slots. Varies as
  the classification vocabulary (relay's rule) and the guard sentinel
  (this row).
- **Sites + roles.** Definitions: slots + guard contract here.
  Precedence/install: [types-relay][types-relay] (its rules). Readers:
  decode, strategy-aware filter, testing mint, finalizer audits —
  consumers. Setting-snapshot triggers (T-reader/T-compute/T-lifetime
  on the UNAPPLIED family) re-checked: this file reads no setting
  (no settings import; `RELAY_GLOBALID_STRATEGY` × 0) — all unfired.
- **Challenges.** #7 counts 0 here (a sixth string needs no slot
  change); #8 counts 1 (sentinel + contract prose here; install +
  readers follow as consumers).
- **Owner + lifetime.** Slots here; written once at finalization
  (install step); read-only afterwards; `None`-default pre-install.
- **Migration.** None — zero-edit.
- **Distinct behavior.** Precedence, closure install, encode/decode
  acceptance, and the snapshot lifecycle stay in relay/finalizer/
  registry under their rows.
- **Behavioral proof.** `static-reviewed` (single-step write census
  + reader census).
- **Structural gate.** None owed (the family item owns any gate).
- **Coupling.** None (the snapshot family's UNAPPLIED state is
  recorded, not depended on).
- **Freshness.** Target `fa6c4d330e72`; types/relay `524398622354`;
  finalizer `de34ae2aaed1`; filters/base `ba52351c2844`;
  [testing-relay][testing-relay] `df0dc72a1788`; snapshot rule artifact
[rule-snapshot][rule-snapshot] (`f616835bb703`).

### F-RELTARGET — relation-target lookup + memo (file-local)

- **Contract + variation.** `related_target_for(field_name)` answers
  `(target_definition, model_field) | None`: non-`str` → `None`;
  unknown field → `None`; non-relation → `None`; unresolvable target
  (`related_model None` incl. GFK, unregistered type, missing
  definition) → `None`; every unreadable step degrades to `None`
  (7 arms). Target-type precedence is composed by name from
  `registry.get` (primary-first inside the registry — the oracle at
  :494–534 pins the collapsed call against the historical
  `primary_for or get` chain). Memoized per field name ONLY
  post-finalize (`registry.is_finalized()` gate: a pre-finalize
  transient `None` must never lock in); `None` values are valid
  cached results. Varies as the walk (precedence, arms) and the cache
  discipline. NOTE (unpinned-but-correct, not a defect): no oracle
  performs the pre-finalize-`None` → register → finalize → re-lookup
  sequence; the lines execute under every lookup and the gate's
  reasoning is sound (post-finalize registration is refused at
  [types-base][types-base] :628, so staleness needs exactly the gated
  path).
- **Sites + roles.** Definition: this method + cache. Composed
  primitives: `registry.get` / `registry.get_definition` (verified
  registry families). Consumers: [filters-base][filters-base] :675, filters/sets
  :2091 (lenient probe + registry fallback), walker :498 (pair spent
  whole + registry-only fallback), finalizer :1222–1223. Oracles: FK /
  M2M / reverse / O2O both directions / scalar / missing / GFK /
  unregistered / primary-wins / memo-identity / malformed-every-step /
  unhashable-name (all independent). Facet: the :316/:323 read rungs
  spell the lenient relation-metadata read inline — routed to
  FAM-LENIENT (count 2 there); the walk, ladder, precedence
  composition, and cache discipline stay here.
- **Challenges.** #9–#11 count 1 (precedence/arm/cache changes move
  this body; consumers follow).
- **Owner + lifetime.** This method; cache lifetime = definition
  lifetime, valid only post-finalize (fresh definitions per
  `registry.clear()` bound staleness to discarded holders).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Registry precedence stays in the registry;
  per-consumer fallbacks stay per consumer (R11); the lenient-read
  rungs route to the family; D3 (truthiness escape) is filed, not
  fixed.
- **Behavioral proof.** `static-reviewed` (walk + consumers + 9
  oracle tests read at HEAD bytes; no execution).
- **Structural gate.** None owed by this file item (the family item
  owns the lenient-read gate; D3's pin is the family's `proof:`).
- **Coupling.** FAM-LENIENT (read rungs) + D3 (the truthiness hole
  the family closes or preserves by the maintainer's call).
- **Freshness.** Target `fa6c4d330e72`; registry `81bd561c99cb`;
  filters/base `ba52351c2844`; filters/sets `993e887a7001`; walker
  `75f9c6b65ed1`; finalizer `de34ae2aaed1`; oracles `196e783d1d87`.

### F-CUSTOMID — custom-id detection cluster (file-local)

- **Contract + variation.** Whether `origin` resolves its id away
  from `pk_name`, for FK-id elision safety: an MRO-level
  `resolve_id` / `resolve_<pk>` marker (ignoring the two known
  defaults — the framework-installed `_resolve_id_default` and
  Strawberry's `Node.resolve_id`) OR a `relay.NodeID` annotation
  pointing off the pk column. `has_custom_id_resolver_for` memoizes
  per normalized pk name (negatives included; malformed pk never
  cached); `origin_has_custom_id_resolver` is the shared unmemoized
  core so the memoized path and the walker's definition-less fallback
  cannot drift (walker :1460/:1466 composes both by name);
  `_normalize_pk_name` is the ONE normalizer both entries call (two
  call sites, one body: the method needs a cache key, the function
  guards the direct path); `_resolves_id_off_pk` probes the
  `NodeID` placement (non-Node → `False`; absent annotation →
  `False` — the arm serving the never-installed definition-less
  path; hostile remainder → `True`); `_class_has_custom_id_resolver`
  scans one namespace (`resolve_id` → framework check, any other
  marker → `True` at face value); `_is_framework_relay_id_resolver`
  recognizes the two closed defaults by `__func__` identity.
  Varies as markers, defaults, and placement.
- **Sites + roles.** Definition: this cluster (6 bodies, 1 rule).
  Consumers: the walker elision guard (both entries). Oracles:
  memoization incl. negatives, both default exemptions, the
  `resolve_<pk>` short-circuit, NodeID on/off pk, malformed/empty pk,
  hostile `__mro__` / `__dict__` / iteration / `resolve_id_attr` /
  `__func__` (all fail-closed as pinned).
- **Challenges.** #12–#15 count 1 (marker/default/placement/fold
  changes move one body each; the double normalization call is one
  body called twice).
- **Owner + lifetime.** This module; pure predicate + per-definition
  memo (definition lifetime; inputs stable for it).
- **Migration.** None — zero-edit.
- **Distinct behavior.** Suppression identity (R12), slot mapping
  (R13), raw-annotation scanning (R14), `__func__` override detection
  (R15), column projection (R16), and pk-name sourcing (FieldMeta's
  rule) stay separate — each with its section below.
- **Behavioral proof.** `static-reviewed` (cluster + walker guard +
  12 oracle tests read at HEAD bytes; no execution).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `fa6c4d330e72`; walker `75f9c6b65ed1`;
  types/relay `524398622354`; field_meta `18ea719a6141`; oracles
  `196e783d1d87`.

### C1 — `graphql-name-gate` (CONVERGE onto the open family)

The derivation-gate half of the family [types-base][types-base]
FAM-NEW named (row already covers this file; transcribes nothing).
Fresh evidence at HEAD bytes: the `_GRAPHQL_NAME_RE.fullmatch` census
is exactly the 2 production sites (base :1295 + :257; the third
`fullmatch` token is the foreign BigInt regex); the trio order,
`str.__str__` normalization, and 4 messages stay per site (#17–#19
count 1 — the standing per-site direction); oracle halves are
disjoint ([test-base][test-base] :292–323 `Meta.name` rows vs
[test-definition-relations][test-definition-relations] :192/:565/:583
derived-name rows, both re-read). The regex itself (:16) is owned
here and imported by base :61 — one grammar, two gates. #16 counts 2.
No third gate exists (the `startswith("__")` census closes at the R5
split). Freshness: target `fa6c4d330e72`; base `dda91365a7e8`.

### C2 — `optimizer-hint-shape` (CONVERGE, transcribes nothing)

This file declares the `optimizer_hints: dict[str, OptimizerHint]`
slot (annotation + import); value-shape enforcement lives in base
(verified C2: the `isinstance` value gate + relation-membership
gate). Declaration posture only — the family row already covers this
file ([hints][hints] `da46ef891ccd`). No `hint_is_skip` surface here
(token grep 0 at HEAD), so the
skip-predicate family is untouched. Freshness: target `fa6c4d330e72`;
hints `da46ef891ccd` (shape `103`/`143`/`242`/`271` re-read).

### C3 — `type-registry-finalize-gate` (CONVERGE, transcribes nothing)

The `cache_ok = registry.is_finalized()` read (:304) composes the
verified flag by name; the per-verb split (this read = cache-validity
vs refuse-registration / no-op / refuse-declaration / refuse-mint)
converges with verified R10 (R18). Consumer posture only; the family
row owns the flag. Transcribes nothing. Freshness: target
`fa6c4d330e72`; registry `81bd561c99cb`.

### FAM-LENIENT — `lenient-relation-metadata-read` (NEW FAMILY for Worker-0)

- **Contract + variation.** Read one relation-metadata attribute,
  degrading to the caller's default when the read is unanswerable
  (`getattr` with default + `except BaseException` → default).
  Varies as the read mechanism and the lenient outcome; strict
  callers (typed raise), bare callers (no failure policy), and
  non-relation subjects stay out.
- **Sites + roles.** Owner: TBD by the family item (candidate:
  [utils-relations][utils-relations]`::relation_attr` — its docstring
  already claims "a change to HOW relation metadata is read is one
  edit"; `relation_bool` covers the flag site). Definitions (2):
  `relation_attr` (+ `relation_bool`, same body) and the inline
  idiom at :316/:323 (two call sites, one spelling: `is_relation →
  False`, `related_model → None`). Consumers of the owner (listed):
  field_meta (10), join_taxonomy's `_safe_getattr`/`_safe_getbool`
  wrappers. Listed, not counted: the 25 bare `getattr` sites for
  these two attributes (AST-verified outside any `try` — crash-open
  contract, each owning file's axis-6 question, not this rule's);
  `filters/sets.py` :1577–1589 `__func__` override detector
  (different mechanism); this method's non-relation guarded reads
  (`__mro__`/`__dict__`/`__func__` — different subjects + verdicts).
  Oracles: the taxonomy lenient rows + this file's malformed-metadata
  rows (:210–250, independent — they drive hostile doubles).
- **Challenges.** #39 (mechanism hardening) and #40 (third lenient
  outcome) count **2**. Disproof attempted on all six axes (inputs,
  outputs, errors, timing, hooks, reasons to change) and failed —
  both spell the same (object, name, default) → value-or-default
  read at request time under the same change rule the owner's
  docstring states. Single-file-family precedent: verified
  `active-terms-purity-agreement`.
- **Migration sketch (family item's call).** The two rungs compose
  the owner (`relation_attr` preserves even the D3 hole → standalone
  path; `relation_bool` closes it → combined-fix path, the maintainer's call);
  the None-ladder, precedence, and cache stay here. Dependency check
  done: `utils/relations.py` is leaf-ward (stdlib + django +
  exceptions) and siblings already import it at top — no reversal.
- **Distinct behavior.** The walk/ladder/precedence/cache (F-RELTARGET),
  strict callers, bare callers, and non-relation reads stay separate.
- **Behavioral proof.** `static-reviewed` (owner body + both rungs +
  oracles compared at HEAD bytes; no execution — a file item runs no
  failability probe).
- **Structural gate.** Owed by the family item, not this file item;
  shape: a census gate over the lenient spelling (defaulted `getattr`
  + `except` → default on relation attributes) failing a third
  spelling (negative control: a hand copy of one rung with a diverged
  default — behavior oracles stay green, the gate goes red).
- **Coupling.** D3 (the truthiness hole): the `relation_attr`
  adoption preserves it (standalone; D3 rides its own card), the
  `relation_bool` adoption closes it (combined fix — the maintainer authorizes,
  or the family redesigns standalone; carding D3 while accepting the
  closing adoption is not a resolution).
- **Freshness.** Target `fa6c4d330e72`; utils/relations
  `8dbc3fe668dd`; join_taxonomy per verified row; oracles
  `196e783d1d87`.
- **Worker 0 transcription:** one family index row + one `## Families`
  item, both spelled in `## Index rows for Worker-0` / `## Families`.

### R1 — in-file `str` normalization vs a shared helper (rejected)

The 4 `isinstance(x, str)` + `str.__str__(x)` pairs here (:246/:251
raise, :283/:285 `None`, :399/:401 `None`, :434/:436 `True`) vs one
shared normalizer. Contract difference: the copy step is stdlib
vocabulary (frozen — challenge #19's primitive change moves 0
definitions), while each site fuses it with its own verdict (raise /
`None` / `None` / `True`); a helper would need a verdict mode flag,
which principle 5 forbids. CONVERGE-adjacent with the [file-base][file-base] FAM-NEW per-site
direction (trio order + normalization + messages stay per site) on
fresh evidence — the 4 in-file
pairs were never challenged as a group before. Reconsideration
trigger: all in-file uses converge on one verdict (then a
verdict-shaped helper owns the copy). Freshness: target
`fa6c4d330e72`; base `dda91365a7e8` (:1290, the fifth per-site pair).

### R2 — hostile-read `except` arms vs a shared guard (rejected)

The 10 remaining per-site arms here (raise-with-context ×1,
`None` ×3, `False` ×1, `True` ×5 — the :316/:323 pair routes to
FAM-LENIENT, not here) + 7 defaulted `getattr` reads vs one shared
guard driver. CONVERGE with the verified J1 direction on fresh
evidence: per-arm verdicts differ by method contract (lookup vs gate
vs safety predicate), and the standing trigger — a new guard needing
the same position-state classification — is re-checked unfired (no arm
here classifies stream position). Reconsideration trigger: the
standing J1 trigger. Freshness: target `fa6c4d330e72`; J1 record in
[file-request-body][file-request-body] (`1acec4f8e209`).

### R3 — `isinstance` gates vs a shared exact-type gate (rejected)

The 4 `isinstance(x, str)` gates here (3 verdicts) vs one shared
gate. CONVERGE with the verified J2 direction on fresh evidence —
stronger here: these gates are subclass-TOLERANT + copy (the opposite
mechanism of J2's `type(x) is` exclusion), over consumer-supplied
values, not boundary protocols. The standing trigger — a new
foreign-object protocol needing exclusion inside a boundary — is
re-checked unfired. Reconsideration trigger: the standing J2 trigger.
Freshness: target `fa6c4d330e72`; J2 record in
[file-request-body][file-request-body] (`1acec4f8e209`).

### R4 — error wordings vs an owned message grammar (rejected)

The 4 `graphql_type_name` messages (each naming its subject +
rendering hostile values through the composed safe-renderers) vs one
owned grammar. CONVERGE with verified per-subject-rejection-grammars
on fresh evidence — still no owned grammar at HEAD (challenge #22
counts 0). Reconsideration trigger: the standing trigger (the package
adopts one owned rejection-message grammar). Freshness: target
`fa6c4d330e72`; grammar record in [file-policies][file-policies]
(`0a41dec28bc2`).

### R5 — name gate vs sanitize and dunder (rejected)

This gate (invalid → raise, the second half of C1) vs
[types-converters][types-converters] enum-member sanitization
(invalid → `MEMBER_`-prefix, never raise, :621) vs [conf][conf]
`__getattr__` dunder short-circuit (:343, introspection safety).
CONVERGE with verified R18 on fresh evidence — reject vs sanitize vs
introspect, three rules sharing only the `__` token; conf
byte-identical at `c6ad46aa3f0c`. Reconsideration trigger: one owned
name-safety rule. Freshness: target `fa6c4d330e72`; converters
`058f10813927`; conf `c6ad46aa3f0c`.

### R6 — relay predicate vs id-column probe (rejected, probe side)

The inline `isinstance(origin, type) and issubclass(origin,
relay.Node)` inside `_resolves_id_off_pk` (fail-closed safety probe:
hostile reads answer `True`, non-Node answers `False`) vs
[types-base][types-base]`::_is_relay_shaped` (pre-injection shape
gate: declared-tuple OR inheritance). CONVERGE with verified R6 from
the probe side on fresh evidence: gate vs probe — no interfaces tuple
exists at the probe's post-finalization call site. Reconsideration
trigger: the standing trigger (probe callers need tuple-declared
shapes), re-checked unfired (callers pass origin only). Freshness:
target `fa6c4d330e72`; base `dda91365a7e8`.

### R7 — MRO marker scan vs the walk family (rejected)

The `getattr(origin, "__mro__", ())` marker scan (:385: "does any
class define a resolver marker") vs the scalar-dispatch walks, the
override-detection scan, and the declaration-collection scan.
CONVERGE with verified R14 on fresh evidence — a fourth question on
a fourth MRO; the standing trigger (one owned MRO-walk helper, no
such rule at HEAD) is re-checked unfired ([file-converters][file-converters] FAM-MRO
names a map-key helper only, undispatched, and this walk is not a
map-key lookup).
Reconsideration trigger: the standing R14 trigger. Freshness: target
`fa6c4d330e72`; base `dda91365a7e8`; converters `058f10813927`.

### R8 — pk-name reads vs pk-attname readers (rejected)

The `("pk", pk_name)` NAME tuple arm (:437; NAME vocabulary end to
end from [field-meta][field-meta]'s `_target_pk_name`) vs the `pk.attname` column
readers owned elsewhere. CONVERGE with the verified join-taxonomy
six-`pk.attname`-readers direction on fresh evidence —
`attname` × 0 in this file; name-vs-column split stands.
Reconsideration trigger: the standing trigger (an identity read
needing name + attname together), unfired. Freshness: target
`fa6c4d330e72`; field_meta `18ea719a6141`.

### R9 — relation lookup vs column resolution (rejected)

`related_target_for` (relation → `(definition, field)` pair;
relations ONLY, scalar → `None`; corrupted internals degrade to
`None` — request-time lookup) vs
[forms-inputs][forms-inputs]`::_model_column_for` (name → backing
COLUMN; forward-concrete ONLY, relations excluded categorically;
corrupted internals raise typed — schema-time build). Contract
differences: opposite relation polarity + opposite failure posture +
single vs pair output. Fresh pair, no prior verdict. Reconsideration
trigger: one name→field resolution with a relation-polarity parameter
serving both lifecycles. Freshness: target `fa6c4d330e72`; forms/inputs
`6418753d6db1`.

### R10 — relation lookup vs registered-definition validation (rejected)

`related_target_for` (lookup: `registry.get` + `get_definition`,
fail-soft `None`, no origin check, never raises) vs the
`registered-djangotype-definition-validation` proof (attribute +
registry-identity + origin-identity triple-`and`, typed raise).
Contract difference: lookup vs proof. Fresh pair naming this file —
CONVERGE with F1's exclusion logic on fresh evidence (the F1 sweep
covered all 12 `get_definition` consumer files incl. this one; only
the F1 pair co-locates the origin-identity arm — re-verified: this
file has no origin-identity check). Reconsideration trigger: the
lookup gains a proof obligation (raise / identity check). Freshness:
target `fa6c4d330e72`; [list-field][list-field] `21380eb72364`; F1
record in [file-testing-relay][file-testing-relay] (`5c08128ba491`).

### R11 — lookup-tail composition vs a shared helper (rejected)

The `registry.get` → `get_definition` tails: this method's
(try/except per rung, `(definition, field)` shape) vs the walker
fallback (:502–508: unguarded, `(origin, definition)` shape) vs the
filters fallback (type-only return). Contract difference: same
primitives composed, different shapes + different failure postures;
the sharing IS the verified registry primitives (compose-by-name
already satisfied). Fresh pair, no prior verdict. Reconsideration
trigger: a third site needing the exact `(definition, field)` pair +
fail-soft spelling re-spelling the walk instead of calling it.
Freshness: target `fa6c4d330e72`; walker `75f9c6b65ed1`; filters/sets
`993e887a7001`; registry `81bd561c99cb`.

### R12 — custom-id detection vs the suppression mirror (rejected)

This cluster (elision safety: "does the id resolve off the pk
column") vs the UNAPPLIED `relay-pk-suppression-read-mirror` rule
(surface identity: "which field does suppression remove"). Contract
difference: safety predicate vs identity performer/predictor — a type
can carry a custom resolver without suppression applying (non-relay
targets) and vice versa; this file takes pk names as parameters and
reads no `_meta.pk.name` itself. Fresh pair. UNAPPLIED trigger
re-checks (fresh): owner `types/base.py::_is_suppressed_relay_pk`
still 0 hits package-wide (only the CLI method + call site);
predictor still inline composing `_is_relay_shaped`; mirror gate
still 0 at HEAD (worktree-only owned dirt); maintainer decision
(a/b/c) still owed. All unfired. Reconsideration trigger:
elision-safety and suppression-identity collapse to one question.
Freshness: target `fa6c4d330e72`; base `dda91365a7e8`;
[inspect][inspect] `2807d0fc9d75`; mirror rule artifact
[rule-mirror][rule-mirror] (`0f48ee970f52`).

### R13 — off-pk predicate vs id-slot mapping (rejected)

`_resolves_id_off_pk` (boolean for the PLAN path: is pk-only elision
safe) vs [root-relay][root-relay]`::_node_id_slot` (attr + concrete
field mapping for the DECODE path: which column to coerce/filter).
Contract difference: predicate vs mapping over the same upstream seam
(`resolve_id_attr`); different paths (plan vs decode), different
failure needs (fail-closed boolean vs concrete-field-or-`None`).
Fresh pair, no prior verdict. Reconsideration trigger: one id-slot
rule serving plan + decode. Freshness: target `fa6c4d330e72`;
root relay `c3c5aea52768`.

### R14 — effective-slot read vs raw-annotation scan (rejected)

`origin.resolve_id_attr()` (MRO-resolved: honors the installed
framework default; `NodeIDAnnotationError` → `False`, the arm serving
the never-installed definition-less path) vs the composite-pk gate's
`relay.Node.resolve_id_attr.__func__(type_cls)` ([types-relay][types-relay]
:188: bypasses the install to ask Strawberry's scan directly).
Contract difference: honor-install vs bypass-install — each reads
where the other would misread (the bypass exists BECAUSE the
installed default swallows the error this gate needs). Fresh pair, no
prior verdict. Reconsideration trigger: one `resolve_id_attr` read
posture. Freshness: target `fa6c4d330e72`; types/relay
`524398622354`.

### R15 — `__func__` recognition vs override detection (rejected)

`_is_framework_relay_id_resolver` (`__func__`-unwrap + identity vs
two CLOSED default function objects: authorship question — "is this
exact object a known default") vs the filterset `__func__` override
detector ([filters-sets][filters-sets] :1577–1589: consumer-vs-
framework polarity for hook ownership) and vs the get_queryset
question, where the finalizer's recorded reasoning REFUSES
`__func__`-identity ([types-finalizer][types-finalizer] :1351–1352: a
shared function ≠ same behavior under `cls`-parameterized
overrides). Contract difference: closed-default recognition (identity
is exact — a consumer `def` is always a new object) vs behavioral
override detection (identity misleads). Same mechanism, opposite
questions. Fresh pair, no prior verdict. Reconsideration trigger: a
consumer `resolve_id` sharing identity with a default. Freshness:
target `fa6c4d330e72`; filters/sets `993e887a7001`; finalizer
`de34ae2aaed1`; types/relay `524398622354` (default owner).

### R16 — elision predicate vs id-column projection (rejected)

`_has_custom_id_resolver` guard (boolean: is elision SAFE — read at
[walker][walker] :996) vs the walker's id-column projection (:791:
which column to `.only()`-project so `_resolve_id_default` reads from
`__dict__` — FieldMeta scan by name AND attname under the G2 gate).
Contract difference: safety verdict vs load plan over the same seam;
complementary halves (guard + use), not duplicates. Fresh pair, no
prior verdict. Reconsideration trigger: one id-column rule serving
projection + elision. Freshness: target `fa6c4d330e72`; walker
`75f9c6b65ed1`.

### R17 — pk-name normalization vs boundary normalization (rejected)

`_normalize_pk_name` (plain-`str` copy, malformed → `None`, for
elision gating + cache keys) vs [strings][strings]`::_plain_text`
(plain-`str` copy, malformed → raise, for boundary name transforms).
Contract difference: `None`-posture vs raise-posture over different
subjects (pk names vs boundary names); unifying needs a verdict
parameter = mode flag. Fresh pair, no prior verdict. Reconsideration
trigger: the verdicts converge (then the surviving helper owns the
copy). Freshness: target `fa6c4d330e72`; strings `991f7dad20b3`.

### R18 — finalized gates stay per-verb (rejected)

The cache-validity read (:304) vs refuse-registration (base :628),
no-op short-circuit (finalizer :861), refuse-declaration
(mutations/sets :543), refuse-mint ([testing-relay][testing-relay] :78), and the CLI
table-print check. CONVERGE with verified R10 on fresh evidence —
five verbs + table check, each gate's verb + remediation belongs to
its boundary; the FLAG is single-owned by the verified family (C3).
Reconsideration trigger: the standing trigger (one shared gate verb),
unfired. Freshness: target `fa6c4d330e72`; base `dda91365a7e8`;
finalizer `de34ae2aaed1`; testing/relay `df0dc72a1788`.

### R19 — lazy imports vs hoisting (rejected)

The 3 in-function import sites (registry :290–292, strawberry relay
:418–419, `.relay` default :456–458) vs top-level hoisting / one
shared lazy-import posture. Contract difference: three sites, three
different reasons — the registry site claims a cycle (wrongly: D2 —
the `registry → definition` edge is `TYPE_CHECKING`-only and
registry's runtime closure is leaf-ward with a pure-dict `__init__`,
so the hoist is statically safe; the laziness is harmless churn to
remove, not a rule to share); the relay sites are import-weight +
single-use colocation (both edges acyclic: upstream never imports us;
`.relay`'s closure touches no `types.*`). No shared posture exists to
consolidate. Reconsideration trigger: the three sites sharing one
import posture. Freshness: target `fa6c4d330e72`; registry
`81bd561c99cb`; types/relay `524398622354`.

## Defects

### D1 Stale `TODO-BETA-046-0.1.1` anchor on the `fields_class` reservation (minor, HEAD, unfixed)

- **What.** Class docstring :69 reserves `fields_class` for
  `TODO-BETA-046-0.1.1`. No card carries that id (no `###` heading in
  the rendered board); the live FieldSet owner is `TODO-BETA-059-0.1.1`
  ([kanban][kanban] :797 heading: "`FieldSet` declarative field-level
  behavior (`Meta.fields_class`)"). The other 8 spec-Decision cites in
  this file all resolve (030 D8, 031 D6/D8/D10/D13, 032 D7, 033 D3,
  047 D5 — verified by grep); this anchor is the lone stale one.
- **Contract.** Docstring anchor names a plannable owner; a dead id
  misroutes the reader. Already homed: the [kanban][kanban] :288
  bullet on card TODO-ALPHA-053 (this cycle's own card) prescribes
  the retarget ("fold into whichever WP batch legitimately opens
  `types/definition.py`") — closeout dedups against it.
- **Fix shape (not applied).** Retarget to `TODO-BETA-059-0.1.1`; one
  docstring token, no behavior change.
- **Owner.** File `types/definition.py` (the docstring). Routes to
  normal closeout homing (already on card 053; blocks nothing).
- **Freshness.** Target `fa6c4d330e72` (anchor also present in
  worktree `1c59a3feec53`, unjudged); KANBAN `0b33301a9f8e`.

### D2 Wrong cycle rationale on the "Do NOT hoist" comment (minor, HEAD, unfixed)

- **What.** `related_target_for` :287–289 dodges a "`definition ->
  registry -> definition` module-load cycle" with "Do NOT hoist".
  The second edge exists only under `TYPE_CHECKING`
  ([registry][registry] :29–31, never executed); registry's runtime
  closure is leaf-ward (stdlib + django + leaf `exceptions` +
  stdlib-only `utils/imports`) with a pure-dict `__init__` and no
  module-level calls into `types.*`; the root `__init__` loads
  `.connection` (line 18, which imports registry at its line 95) before
  `.types` (line 52), and
  this submodule can only load after the root `__init__` starts — so
  the hoist is statically safe on every import path and no partial-init
  hazard exists. Per principle 10 (wrong stated reason < none), the
  comment misleads the next author into preserving laziness for a
  cycle that cannot fire.
- **Contract.** Comment claims a load-bearing cycle; the bodies show
  none. The laziness itself is harmless (keeps the edge local);
  only the rationale is false.
- **Fix shape (not applied).** Reword to the real posture
  (layering/weight) or hoist; no behavior change either way.
- **Owner.** File `types/definition.py` (the comment). Routes to
  normal closeout homing (blocks nothing).
- **Freshness.** Target `fa6c4d330e72`; registry `81bd561c99cb`.

### D3 Hostile-truthiness escape on the `is_relation` read (HEAD, unfixed, coupled to FAM-LENIENT)

- **What.** :315–320 guards the `getattr(model_field, "is_relation",
  False)` READ but tests its truthiness outside the guard (`if not
  is_relation:` :319). A field object whose read succeeds with a
  hostile-truthiness value (`__bool__` raising) escapes
  `related_target_for` raw — the one unreadable step of the seven
  that does not degrade to `None`. Repro shape (static; pure language
  semantics): a field double with an `is_relation` property returning
  an object whose `__bool__` raises; the existing :210–250 oracle
  covers raising-on-READ doubles only.
- **Contract.** The oracle rule "Every unreadable step of the target
  walk degrades to `None`, never an exception" (:210–211) + the
  method's own 7-arm fail-soft posture + the owner's doctrine: the
  lenient reader this rung re-spells guards "both the read and the
  truth test" (`relation_bool` lenient via `safe_truthy`). Sibling
  behavior (all sister arms → `None`) justified the investigation;
  these three sources establish the verdict. Production Django fields
  carry plain-bool flags, so the escape needs a fabricated/hostile
  field shape — the same threat class the :210 oracle already pins
  for this method.
- **Fix shape (not applied).** Adopt `relation_bool(...,
  lenient=True)` for the rung (closes it — the family's combined-fix
  path, the maintainer's call) or guard the truth test in place (standalone).
  Either is one expression; hostile-input behavior moves from "raw
  raise escapes" to "`None`".
- **Owner.** File `types/definition.py` (the rung). Coupled to
  FAM-LENIENT per its Coupling clause (standalone `relation_attr`
  adoption preserves the hole → D3 rides its own card; closing
  adoption needs the maintainer's combined-fix authorization).
- **Freshness.** Target `fa6c4d330e72`; utils/relations
  `8dbc3fe668dd`; oracles `196e783d1d87`.

## Pending execution

None. No `proof:` entry: every verdict is `static-reviewed` (body
comparison, AST-precise censuses, pinned oracles — inspection
decides; nothing ordering-, transactional-, or async-sensitive was
judged, and D3 rests on language semantics + the owner's own
doctrine). No `gate:` entry: zero-edit, no regression witness needed.
Sharded and PG cells are inapplicable by construction: the target
reaches no database, alias, or dialect decision (registry dict probes
+ pure string/class reads only). No workspace run was needed; none
was made.

## Judgment

File item with one genuine cross-file candidate: 17/17 members homed
(32/32 class slots + methods in the sub-map). Eight rules stand
file-local with proving challenges; the two lenient-read rungs route
to the new holding family `lenient-relation-metadata-read` (count 2,
AST-closed population, owner candidate named, dependency checked);
three convergences land on open/verified families with fresh trigger
checks (all transcribing nothing); 19 rejections carry contract
differences + triggers (8 converging on verified rows, 11 fresh).
Three HEAD defects filed unfixed (D1 stale anchor already on card
053, D2 wrong cycle rationale, D3 truthiness escape coupled to the
new family). No pending execution, no production edits.

## Implementation (Worker-1)

No tracked changes made (zero-edit result submitted for verification).
Item-scoped attribution vs
`ITEM_BASELINE=e3cea666c23765516365f4c136ea512a94736894`: `git diff
<baseline> -- django_strawberry_framework/types/definition.py
docs/dry/dry-file-types__definition.md` is empty — the HEAD-vs-worktree
dirt on the target predates the baseline window and was never touched;
the artifact itself is a new untracked file, the item's only output.
The [plan][plan] `## Owned changes` ledger gains no row from this item (no row
names the target; verified by reading). No `uv run ruff` run (no `.py`
touched; `.md` is outside ruff format scope; no `.py` scratch created).
No shared-tree pytest run (static review + pinned oracles suffice — see
`### Challenges` note). No workspace runs. No `docs/dry/temp-tests/`
scratch created. No commit.

Worker-0 instructions: (a) tick the plan item `File
types/definition.py` as verified under Run `0.0.15 2026-09-28-7` once
Worker 2 agrees; (b) add the 28 `## Responsibility index` rows under
`## Index rows for Worker-0` verbatim (1 open family row with holding
item `Family lenient-relation-metadata-read`, 8 file-local + 19
rejected); (c) add the one `## Families` item under `## Families`;
(d) home D1 (already on card TODO-ALPHA-053 :288 — dedup), D2, and D3
(coupled to the new family per its Coupling clause) at closeout.

## Index rows for Worker-0

| `types-definition-module-mechanics` | `django_strawberry_framework/types/definition.py` (docstring + 9 import statements binding 13 names + 3 in-function lazy sites) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-canonical-record` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition` (13 core slots + single-construction/stamp/immutability invariants) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-override-contract` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.consumer_authored_fields` (+ 4 corner frozensets; union composed in base) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-sidecar-slots` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.filterset_class` (+ `orderset_class`, forward-reserved `fields_class`) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-synthesis-slots` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.relation_connections` (+ `connection`, `cursor_field`, `relation_shapes`) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-strategy-slots` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.effective_globalid_strategy` (+ raw `globalid_strategy`, re-entrancy-guard contract) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-relation-lookup` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (+ post-finalize `_related_target_cache`; read rungs route to FAM-LENIENT) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `types-definition-custom-id-detection` | `django_strawberry_framework/types/definition.py::origin_has_custom_id_resolver` (+ memoized method, `_normalize_pk_name`, `_resolves_id_off_pk`, `_class_has_custom_id_resolver`, `_is_framework_relay_id_resolver`) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | file-local |
| `lenient-relation-metadata-read` | TBD by family item (candidate: `django_strawberry_framework/utils/relations.py::relation_attr` via lenient adoption of the two inline rungs; `relation_bool` for the flag site; closes-or-preserves D3 per Coupling) | `django_strawberry_framework/utils/relations.py`, `django_strawberry_framework/types/definition.py` | Family `lenient-relation-metadata-read` | open |
| `types-definition-str-normalize-vs-helper` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name` (rejection recorded here; same-file 4-pair idiom — stdlib copy + per-site verdicts; CONVERGE-adjacent with the FAM-NEW per-site direction on fresh evidence) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py` | File `types/definition.py` | rejected |
| `types-definition-except-arms-vs-shared-guard` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; CONVERGE with the verified shared-except-guard J1 direction on fresh evidence — 10 arms, 4 verdicts; lenient pair routes to FAM-LENIENT) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | rejected |
| `types-definition-gates-vs-shared-exact-gate` | `django_strawberry_framework/types/definition.py::_normalize_pk_name` (rejection recorded here; CONVERGE with the verified shared-exact-type-gate J2 direction on fresh evidence — subclass-tolerant + copy, opposite mechanism) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | rejected |
| `types-definition-wordings-vs-shared-grammar` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name` (rejection recorded here; CONVERGE with verified per-subject-rejection-grammars on fresh evidence — still no owned grammar at HEAD) | `django_strawberry_framework/types/definition.py` | File `types/definition.py` | rejected |
| `types-definition-name-gate-vs-sanitize-and-dunder` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.graphql_type_name` (rejection recorded here; CONVERGE with verified R18 on fresh evidence — reject vs sanitize vs introspect; conf byte-identical) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/conf.py` | File `types/definition.py` | rejected |
| `types-definition-probe-vs-relay-predicate` | `django_strawberry_framework/types/definition.py::_resolves_id_off_pk` (rejection recorded here; CONVERGE with verified R6 from the probe side on fresh evidence — fail-closed probe vs pre-injection gate) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py` | File `types/definition.py` | rejected |
| `types-definition-mro-scan-vs-walk-family` | `django_strawberry_framework/types/definition.py::origin_has_custom_id_resolver` (rejection recorded here; CONVERGE with verified R14 on fresh evidence — fourth question, fourth MRO; not a map-key lookup) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py` | File `types/definition.py` | rejected |
| `types-definition-pk-name-vs-attname` | `django_strawberry_framework/types/definition.py::_resolves_id_off_pk` (rejection recorded here; CONVERGE with the verified join-taxonomy pk-attname direction on fresh evidence — NAME vocabulary, attname × 0) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/optimizer/field_meta.py` | File `types/definition.py` | rejected |
| `types-definition-lookup-vs-column-resolution` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; fresh pair — opposite relation polarity + opposite failure posture + pair vs single) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/forms/inputs.py` | File `types/definition.py` | rejected |
| `types-definition-lookup-vs-proof` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; fresh pair — lookup vs proof; CONVERGE with F1's exclusion logic on fresh evidence, no origin-identity arm) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/list_field.py` | File `types/definition.py` | rejected |
| `types-definition-tail-vs-shared-helper` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; fresh pair — same registry primitives, different shapes + postures; sharing IS the primitives) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/filters/sets.py` | File `types/definition.py` | rejected |
| `types-definition-custom-id-vs-suppression-mirror` | `django_strawberry_framework/types/definition.py::origin_has_custom_id_resolver` (rejection recorded here; fresh pair — safety predicate vs identity performer/predictor; UNAPPLIED triggers all re-checked unfired) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/management/commands/inspect_django_type.py` | File `types/definition.py` | rejected |
| `types-definition-predicate-vs-slot-mapping` | `django_strawberry_framework/types/definition.py::_resolves_id_off_pk` (rejection recorded here; fresh pair — plan-path boolean vs decode-path mapping over one seam) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/relay.py` | File `types/definition.py` | rejected |
| `types-definition-effective-read-vs-raw-scan` | `django_strawberry_framework/types/definition.py::_resolves_id_off_pk` (rejection recorded here; fresh pair — honor-install vs bypass-install) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/relay.py` | File `types/definition.py` | rejected |
| `types-definition-func-recognition-vs-override-detection` | `django_strawberry_framework/types/definition.py::_is_framework_relay_id_resolver` (rejection recorded here; fresh pair — closed-default recognition vs behavioral-override detection; finalizer refuses identity for behavior) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/filters/sets.py`, `django_strawberry_framework/types/finalizer.py` | File `types/definition.py` | rejected |
| `types-definition-elision-vs-projection` | `django_strawberry_framework/types/definition.py::origin_has_custom_id_resolver` (rejection recorded here; fresh pair — safety verdict vs load plan; guard + use halves) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/optimizer/walker.py` | File `types/definition.py` | rejected |
| `types-definition-pk-normalize-vs-boundary-normalize` | `django_strawberry_framework/types/definition.py::_normalize_pk_name` (rejection recorded here; fresh pair — None-posture vs raise-posture; unify needs a verdict flag) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/utils/strings.py` | File `types/definition.py` | rejected |
| `types-definition-gates-stay-per-verb` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; CONVERGE with verified R10 on fresh evidence — cache-validity is the fourth verb; flag owned by C3) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/finalizer.py`, `django_strawberry_framework/testing/relay.py` | File `types/definition.py` | rejected |
| `types-definition-lazy-imports-vs-hoisting` | `django_strawberry_framework/types/definition.py::DjangoTypeDefinition.related_target_for` (rejection recorded here; fresh — 3 sites, 3 reasons; registry rationale wrong → D2) | `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/registry.py`, `django_strawberry_framework/types/relay.py` | File `types/definition.py` | rejected |

## Families

- [ ] Family `lenient-relation-metadata-read` — [dry-rule-lenient-relation-metadata-read.md](dry-rule-lenient-relation-metadata-read.md) — no artifact on disk; undispatched

## Independent verification (Worker-2)

Address `dry/dry-file-types__definition/verify-1`. Traced HEAD bytes
(`fa6c4d33`, 468 lines; worktree `1c59a3fe` concurrent-external hunt
dirt, never judged). No workspace runs (read-only `git show`/`git grep`
plus an AST sweep over a `/tmp` HEAD archive -- no source mutated, no
repo scratch). Zero `.py` touched, so no ruff owed (confirmed by window,
not by run).

### My pre-findings trace

Formed from the target, its consumers, and package-wide sweeps before
opening `## Findings`. AST over the pinned blob: 17 top-level
statements (docstring + 9 imports binding 13 names + 1 regex + 1 class
+ 5 functions); the class carries 33 members incl. its docstring (29
field slots + 3 methods). Homes I chose independently: the 10
mechanics statements file-local; `_GRAPHQL_NAME_RE` + the `:257`
gate converging with the `types/base.py` `:1295` gate (one grammar
imported at base `:61`, two gates -- count 2); the 29 slots file-local
in record/override/sidecar/shape/strategy/cache groups; the
`:316`/`:323` rungs as a lenient-read candidate whose second site my
sweep had to close; the 6-body custom-id cluster file-local (walker
composes both entries by name); the two caches file-local with
definition-lifetime validity. No other consolidation candidate
survived my challenges.

### Reconciliation (every difference explicit)

No verdict difference anywhere: enumeration, matrix, family count,
all 3 convergences, all 19 rejections, D1/D2/D3, index rows, and
Pending-None are AGREE, each re-derived below. The only deltas are
five immaterial record notes (E-W2-1 to E-W2-5), repaired here per the
run-7 E1 precedent; none moves a home, count, or gate.

- **Enumeration AGREE.** 17/17 + 32/32 reproduced member-by-member
  (29 slots: 13 + 5 + 3 + 4 + 2 + 2 caches; 3 methods). Every member
  lands in a family row, a file-local row, or a rejection.
- **Matrix AGREE, all 6 axes.** Axis 1: the finalizer bind is one
  generic body with a filter-only hook adapter; forms polarity/posture
  split re-read; no second surface-name derivation (9 consumer files
  re-censused) and no second id-detection. Axis 2: 0 async tokens
  re-grepped (E-W2-5 notes a dangling cross-ref). Axis 3:
  `origin.__name__` exactly 4 (derivation + docstring + 2 display
  labels), `attname` x 0, single-site derivation. Axis 4: relay pair
  owned by `types/relay.py`, slots declared here; cache pairs
  intra-body. Axis 5: 23 oracle tests, 15 docstring clauses, 8 spec
  cites all resolving, KANBAN 053 bullet verbatim. Axis 6: all 7
  fail-soft arms + per-entry postures re-derived; the one hole is D3.
- **New family AGREE (count 2, population closed by my own sweep).**
  Owner candidate `utils/relations.py::relation_attr` sound:
  leaf-ward imports (stdlib + django + exceptions, `TYPE_CHECKING`
  only beyond), siblings import it at top -- no dependency reversal.
  `relation_bool` covers the flag site; the Coupling paths check out
  against both bodies (`relation_attr` returns raw, `relation_bool`
  lenient routes through `safe_truthy`). Challenges #39/#40 count 2.
  Census correction in E-W2-1: my AST finds 26 constant-name 3-arg
  `getattr` sites for the two attrs (2 family rungs in-try + 2
  owner-module in-try walks + 22 outside-try), not "25 bare
  outside-try"; the nearest misses are named and excluded there, and
  the family item re-sweeps regardless. Count 2 stands.
- **Convergences AGREE, all fresh.** C1: `fullmatch` exactly 3
  (foreign BigInt + the pair), `startswith("__")` closes at the R5
  split, oracle halves disjoint and re-read. C2: declaration posture
  only, `hint_is_skip` x 0, shape lines re-read. C3: flag composed by
  name; per-verb split converges with verified R10 (whose row already
  names this file's cache-read verb). All triggers re-checked unfired.
- **Rejections AGREE, all 19.** Each carries its contract difference
  + trigger: 8 converges re-checked against their records at current
  bytes (J1/J2 triggers quoted verbatim and re-checked unfired on a
  0 position-vocabulary grep; grammar trigger verbatim; base R6 names
  this probe explicitly at this blob; R10/R14/R18 triggers verbatim;
  join-taxonomy direction with E-W2-4's trigger note; F1's 12-file
  sweep re-censused at exactly 12) and 11 fresh pairs re-read at both
  bodies (R1 per-site verdicts, R9 opposite polarity + posture, R10
  lookup-vs-proof with no origin-identity arm here, R11 three tail
  shapes, R12 UNAPPLIED triggers all unfired, R13 predicate-vs-map,
  R14 honor-vs-bypass with the swallow rationale, R15 closed-default
  vs behavioral with the finalizer's refusal, R16 guard-vs-use under
  the G2 gate, R17 None-vs-raise, R19 three sites/three reasons).
- **D1 ENDORSED as filed** (minor doc-only, already on card 053 --
  the `:288` bullet prescribes exactly this retarget; `:797` heading
  and dead `046` id verified). **D2 ENDORSED as filed** (minor
  doc-only: second edge `TYPE_CHECKING`-only at registry `:29-31`,
  leaf-ward runtime closure, pure-dict `__init__`, root order line 18
  before 52 with registry complete at connection `:95` -- the hoist
  is statically safe on every path). **D3 ENDORSED as filed**
  (coupled to FAM-LENIENT): `:319` tests truthiness outside the
  `:315-318` guard while every other `None`-check in the walk uses
  `is None`; contract sources are the pinned "never an exception"
  oracle rule (`:210-211`, raising-on-READ doubles only), the 7-arm
  posture, and the owner's explicit read-and-truth-test doctrine --
  the escape needs the same threat class the oracle already pins for
  this method.
- **Freshness AGREE.** All 22 `.py`/test/KANBAN pins re-derived
  digit-for-digit at HEAD (plus the worktree target pin), all 7
  artifact pins match current bytes, `conf` byte-identical to the
  R18-cited blob.
- **Index rows AGREE.** 28/28 (8 file-local + 1 open family + 19
  rejected) match their findings name-for-name; the Families item is
  present. No transcription.
- **Pending-None AGREE.** Every verdict is inspection-decidable at
  HEAD bytes (body comparison, AST censuses, pinned oracles); D3
  rests on language semantics plus the owner's doctrine. Sharded/PG
  inapplicable by construction (no database, alias, or dialect
  surface -- registry dict probes + pure reads only).

### Errata (Worker-2, verdict-neutral, repaired here)

- **E-W2-1 (family census + nearest misses).** "25 bare sites
  AST-verified outside any `try`" does not reproduce: my AST sweep
  over HEAD bytes finds 26 constant-name 3-arg `getattr` sites for
  `is_relation`/`related_model` -- the 2 family rungs (in-try) + 2
  owner-module in-try walks + 22 outside-try. The 2 in-try walks
  (`utils/relations.py` `:512`/`:688`) are function-level
  containment (the `try` covers the whole walk including
  `get_field`/`relation_kind`; the verdict is the function's `False`,
  not a per-read default) and do not move with #39/#40 -- excluded by
  mechanism, and in the owner module in any case. Further nearest
  misses for the family item's sweep, all excluded here and
  re-checkable there: `optimizer/field_meta.py` `:342-348`
  (function-level containment, same reasoning);
  `types/converters.py` `:306-318` and `exceptions.py` `:145-156`
  (per-read lenient spelling but diagnostic-label rendering --
  placeholder/typename verdicts, different rule and reasons to
  change); `rest_framework/resolvers.py` `:620-632` (non-relation
  subject). Count 2 stands; the "AST-closed" claim is repaired to
  this census.
- **E-W2-2 (strategy census).** `RELAY_GLOBALID_STRATEGY` is x 1, not
  x 0 -- the hit is the `:114` docstring projection. Substance holds:
  no settings import, no code read; all three snapshot triggers
  unfired.
- **E-W2-3 (R2 census).** "10 remaining arms" counts the
  `BaseException` hostile-read arms only; the two typed excepts
  (`:310` `FieldDoesNotExist`, `:429` `NodeIDAnnotationError`) are
  silently excluded. All-except recount is 12 (raise 1, `None` 4,
  `False` 2, `True` 5). The exclusion is principled (domain control
  flow, not hostile reads) but unstated; verdict unaffected.
- **E-W2-4 (R8 trigger wording).** The parenthetical trigger ("an
  identity read needing name + attname together") matches R15's
  trigger more than R8's ("any two reasons collapse"). Both unfired
  (`attname` x 0); verdict unaffected.
- **E-W2-5 (axis-2 cross-ref).** "(Exclusions)" dangles -- the
  artifact carries no such section. The axis is discharged by the
  re-verified 0-token grep.

### Defects / window / verdict

No Worker-2 defects: E-W2-1 to E-W2-5 are artifact record notes, not
production findings. Window vs `e3cea666` holds the plan (Worker-0's
own dispatch text) + `connection.py` (19 hunks: windowed-connection
source_factory/edge-cache/prose work, pairing with the review item
whose Status flip is the fifth path) + `test_keyset_api.py` (+1
cap test) + `test_relay_connection.py` (+1 no-fallback-queryset
test) + `docs/review/review-0_0_15.md` (1-line concurrent Status
flip that landed mid-verification) + the untracked artifact -- all
concurrent/out-of-scope, none touching the target (window diff on
the target is empty: zero-edit confirmed) or any judged region at
HEAD bytes. No item scratch (no `temp-tests/` scope; my `/tmp`
sweep rides with the scratch-custody closeout decision). Prose
rules clean: no process provenance, `path::Symbol` citations, all
10 link groups present, no tests owed, no commit.

**Verdict: `verified`** -- zero-edit file item; 17/17 + 32/32 homed;
8 file-local, 1 new holding family (count 2, population closed by
this section's sweep), 3 convergences transcribing nothing, 19
rejections; D1/D2/D3 endorsed as filed for closeout homing (D1
dedups to card 053, D3 coupled to the new family); no pending
execution.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[kanban]: ../../KANBAN.md

<!-- docs/ -->
[dry]: DRY.md
[file-base]: dry-file-types__base.md
[file-converters]: dry-file-types__converters.md
[file-policies]: dry-file-utils__policies.md
[file-request-body]: dry-file-_request_body.md
[file-testing-relay]: dry-file-testing__relay.md
[plan]: dry-0_0_15.md
[rule-mirror]: dry-rule-relay-pk-suppression-read-mirror.md
[rule-snapshot]: dry-rule-globalid-setting-snapshot.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[connection]: ../../django_strawberry_framework/connection.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[field-meta]: ../../django_strawberry_framework/optimizer/field_meta.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-inputs]: ../../django_strawberry_framework/forms/inputs.py
[hints]: ../../django_strawberry_framework/optimizer/hints.py
[inspect]: ../../django_strawberry_framework/management/commands/inspect_django_type.py
[list-field]: ../../django_strawberry_framework/list_field.py
[registry]: ../../django_strawberry_framework/registry.py
[root-relay]: ../../django_strawberry_framework/relay.py
[strings]: ../../django_strawberry_framework/utils/strings.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-converters]: ../../django_strawberry_framework/types/converters.py
[types-definition]: ../../django_strawberry_framework/types/definition.py
[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py
[types-relations]: ../../django_strawberry_framework/types/relations.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[types-resolvers]: ../../django_strawberry_framework/types/resolvers.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->
[test-base]: ../../tests/types/test_base.py
[test-definition-relations]: ../../tests/types/test_definition_relations.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
