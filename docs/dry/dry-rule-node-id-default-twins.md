# DRY review: `node-id-default-twins`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Four `"pk"`-default resolutions, four contracts. S1 [relay.py][relay]
`:167-174` (`_node_id_slot`): the slot pair `(id_attr, field|None)`;
the `"pk"` arm returns the FIELD for the coerce/filter consumers.
Exact lines HEAD-clean context under a foreign docstring hunk. S2
[types/relay.py][types-relay] `:352-355` (`_resolve_id_default`):
`"pk"` -> row-class `pk.attname` for the `__dict__` cache key; the
assignment line is foreign-rewritten (truth hunk) — HELD. S3
[walker.py][walker] `:869-871`: `"pk"` -> walk-model `pk.attname`
seeding the `FieldMeta` scan + `.only()` projection; exact lines
HEAD-clean context (2 changed lines above, adjacency proven from
the hunk). S4 [lateral_fetch.py][lateral] `:1203-1204`
(`_order_columns`): order-entry `"pk"` -> child pk column for SQL
rendering; file clean. Census `== "pk"` 15/11 reproduced; the rest
(membership, reverse, stamp, quote sweep) classifies out of the
rule (What shrinks). H2/G/I own stamp/slot, fetch twins,
composite detection; this item judges the four resolutions only.

## Verification

### Matrix

1: F1 FIELD (landed) + F2 NAME (rejected) + F4/bool/reverse read;
no fifth resolution. 2: all four sync pure `_meta` reads; async
paths consume the slot value, no twin. 3: one spelling, four
provenances (declared / row-class / walk-model / child-meta),
each forced by its reader. 4: `_column_ref` (reverse lookup
spelling) + `encode_typename` (type half) are distinct rules. 5:
docstrings state each rule; spec-015 pins S2 (`:272`, `:324`
Decision 7); oracles literal incl. live relation-pk. 6: every
slot consumer resolves or compares consistently; no gap.

### Challenges

- R1 (S1 vs F1 owner): C1 alias vocabulary is Django's
(excluded); C2 composite fail-closed moves the owner only (S1
exempt by the committed finalize gate); C3 missing-name moves
each under its own contract (raise vs fall-through). Naive
composition swallows a loud `AttributeError` into silent `None`.
- R2 (S2+S3 twin): C1 rename-default is S0 + three one-token
edits (shared part x2 single-expression, perf-only keys); C2
attname->name flip breaks both downstream contracts; C3
proxy/source moves S2 only. Below bar; S2 held.
- R3 (S4 order-name): C1 rename-default never reaches S4
(Django `order_by` vocabulary); C2 Django-side (excluded).

## Findings

### R1: slot-pair vs segment-field owner — REJECTED

- Sites: S1 stays the single slot definition; [relations.py][relations]
owns the strict segment core. Callers + node-field oracles compose
the slot, never the owner directly.
- Challenges: C1-C3 count 1 per our-change (above).
- Migration: none (zero-edit). Index row for Worker-0:
`node-id-slot-pair`, owner relay.py, `rejected`.
- Distinct: fail-open pair vs strict single (converges with the
verified C1 exclusion); the `except` is S1's own fall-through
posture. Composition is fidelity-barred: naive try/except
swallows no-`_meta` loudness, a pre-check is added machinery.
- Proof: static rejection + P1 probe (What shrinks). Control /
coupling: none. No new tests.
- Freshness: HEAD `c37a08a0`, baseline `c275b07e`; relay
`edfa8d6d`, relations `b0cc6c33` (C1 pin, untouched).
- Triggers: owner gains a fail-open variant; S1's domain widens
past Relay-gated types; a third strict-core site appears.

### R2: attname twin — HELD (S2 foreign-dirty)

- Sites: S2's assignment line is `+`-side foreign — untouchable;
S3's lines are clean context, but the pair lands together or not
at all. Record-only.
- Challenges: C1-C3 (above); on the merits below bar
(F2-C4-analogous: x2 single-expression, perf-only keys, no
drift, distinct model sources + key contracts).
- Migration when S2's hunk lands: re-verify C1-C3 at landed
bytes (expected: reject, no edits); a third site or drift
instead reopens toward a utils owner both import cleanly (the
new helper still owes the bar). No walker->types composition:
relay-closure drag needs laziness walker already uses for
types — machinery for 2 lines, barred.
- Proof: static + P1 + live PatronProfile oracle. Control /
coupling: none. No new tests.
- Freshness: types/relay `3b4447ae`, walker `5508e486`; S3's
lines are context in `@@ -877,8 +862,11`. Any byte change
reopens.
- Trigger T-H1: the foreign hunk lands; either twin's lines
change or drift; a third id-default->attname site appears; the
default moves off `"pk"`.

### R3: order-name resolution — REJECTED

- Sites: S4 stays inline, lateral-only; oracles pin
`"pk"`->column + DESC flip + non-local downgrade.
- Challenges: C1-C2 (above); order vs slot vocabularies never
share a change.
- Migration: none (zero-edit). Index row for Worker-0:
`lateral-order-pk-name`, owner lateral_fetch.py, `rejected`.
- Proof: static + pinned oracles. Control / coupling: none.
No new tests.
- Freshness: lateral `995f1aa2` (file clean). Sources: S4
docstring, Django `order_by("pk")`.
- Triggers: an order context consumes the slot vocabulary or
vice versa; Django retires the order alias.

## Defects

None. The relation-pk oracle-gap hypothesis was refuted by the
live PatronProfile test (correctness + no-lazy-load asserts).

## Pending execution

None.

## Judgment

Per-site idioms, not one rule: field vs attname vs order-term
outputs, four model provenances, no shared our-change. One
hold (S2 foreign-dirty, migration + trigger specified), two
rejections, zero edits.

## Independent verification (Worker-2)

### Own trace (recorded before opening Findings)

Four sites, four contracts. S1 `relay.py::_node_id_slot`
(:146-174): input a resolved Relay type; model from `model_for`
(the registry); output the `(id_attr, field|None)` slot pair --
`"pk"` yields the FIELD (`model._meta.pk`), unknown names yield
None (fail-open fall-through for the coerce/filter consumers).
S2 `types/relay.py::_resolve_id_default` (:320-366): input
`(cls, row)`; model from the ROW's real class (proxy-aware);
output a `__dict__`-key STRING -- `"pk"` yields `pk.attname`,
then cache-read with `getattr` fallback (Decision 7's
no-lazy-load read half). S3 `walker.py::_walk_selections` id
branch (:867-892): input the `"id"` selection + plan model;
output a `.only()` PROJECTION string -- `"pk"` yields the
walk-model `pk.attname`, verified against `field_map` by
name-or-attname (the Decision-7 write half S2's read depends
on). S4 `lateral_fetch.py::_order_columns` (:1177-1213): input
order-entry STRINGS; model from child meta; output `(db column,
desc)` pairs for SQL rendering, `"pk"` yielding
`child_meta.pk.attname` with downgrade-to-None on any non-local
shape. F1 `utils/relations.py::_resolve_segment_field`
(:255-271): input any model-ish + path segment; output the
FIELD; raises `FieldDoesNotExist` (strict, for typed
conversion). Census `== "pk"`: 14 literal hits + the C1-landed
keyset composer = 15/11, no fifth resolution. My challenges:
alias-rename is Django/Strawberry-excluded; composite
fail-closed moves F1 only (S1's pk arm sits behind the
committed finalize gate); posture change moves S1 xor F1
(fall-through vs raise); attname-key change moves S2+S3 (x2
single-expression, perf-only, distinct provenances -- below
bar); order-vocabulary change moves S4 alone. Per-pair
verdicts: slot-vs-owner REJECT, attname twin HOLD-then-likely
reject (S2 foreign), order-name REJECT.

### Reconciliation

Concur on all three findings. Differences: (N1,
verdict-neutral) the S3 cite `:869-871` overreaches by one line
-- WT :869 (`id_attr = node_cls.resolve_id_attr()`) is
foreign-changed (`type_cls` -> `node_cls`); the twin itself
(:870-871) is clean context as claimed, and the hold rests on
S2 regardless. Composite-exemption re-derived against the
gate: the gate raises for composite pk unless an explicit
NodeID annotation escapes, and an escaped type resolves
`id_attr` to the annotation name, so S1's pk arm serves only
gated single-column pks; the pathological `pk`-NAMED annotation
shape returns `meta.pk` identically on both sides and Django's
`CompositePrimaryKey.to_python` exists, so the shape is
verdict-neutral and C2's count-1 stands. Fidelity re-derived
from both bodies: current S1 raises `AttributeError` on a
`_meta`-less model while composed S1 returns `(id_attr, None)`
-- loud-to-silent off-domain, both arms unreachable through
registered types (C1-analogous), so the rejection rests on
no-change-obligation (C1 excluded, C2/C3 count 1) with fidelity
as belt-and-braces, matching W1.

### Independent consolidation search

(D1) Name-or-attname scan triple (S3 `field_map` scan + S4
`concrete_fields` scan + `_is_model_column` bool): same
predicate, but single-expression arms over Django-owned
name/attname spelling, no drift, distinct collections and
not-found postures (skip vs downgrade vs bool) -- fails the
bar. Trigger: OUR matching rule gains a spelling all three
must accept. (E) `relay.py:313/:398` passthrough pair: H2 owns
slot reads (no-poach) and x2 single-expression is below bar
anyway. Trigger: H2 reopens slot-reader shape. (F) Shared
`"pk"` literal constant: barred outright --
Strawberry/Django-owned spelling, no trigger by construction.
(G) S1+S2+S3 triple over `resolve_id_attr` output: the shared
read is already single-owned (S0); outputs differ by kind
(field vs key vs projection), so one helper needs a mode flag
-- machinery, barred. Trigger: outputs unify. Standing R8 (six
`pk.attname` readers) trigger re-checked: S2/S3/S4 reasons
(cache key vs projection vs order column) intact at WT bytes --
unfired. No above-bar consolidation on clean lines exists;
zero-edit stands.

### Checks

Item-scoped diff vs `c275b07e` empty (plan file only); no new
files (3 untracked package files predate the cycle baseline);
no temp-tests residue. Blobs re-pinned: relay `edfa8d6d`,
relations `b0cc6c33`, types/relay `3b4447ae`, walker `5508e486`,
lateral `995f1aa2` -- all match; HEAD `c37a08a0` unmoved. Relay
:167-174 byte-identical to HEAD below the foreign docstring
hunk (ends WT :166); S2's assignment + cache rewrite are
`+`-foreign (ledger owns no types/relay hunk outside the
adopted stamp comment); S3 twin (:870-871) clean context in
`@@ -877,8 +862,11` (reproduced at -U3); lateral file
clean. Matrix: all six axes judged -- ax6's "no gap" holds
(every slot consumer takes `slot` or calls the slot).
Oracle-gap refutation confirmed textually (ids minted from
`patron_id`, one `library_patronprofile` statement carrying
`patron_id`, zero `library_patron` touches). Pending `None`
correct (static-only proofs, no witnesses). Coupling none
(R1's C2 needs the gate's existence, committed at HEAD, not
item I's mechanism). Shape: body 127 (cap 150, links + shrinks
excluded per precedent), trace 16, judgment 4; Run line
matches; 10/10 link groups; symbol + scratchpad cites; no new
tests; ruff vacuous (zero `.py` touched); artifact excluded
from layout rules (checker confirms). Spec-015 `:272` (S2
shape) + Decision 7 `:324` (S2+S3 joint contract) read,
consistent, zero sentences falsified.

### Defects

None. N1 above is a record nit, verdict-neutral.

Verdict: verified. Zero-edit stands: two rejections concurred,
one hold concurred with a concrete re-verify migration and a
firable T-H1.

## What shrinks

Net package change: zero lines. What was counted and where it
stays:

- The four resolutions stay inline, one per reader: S1 (slot
pair, FIELD answer, fail-open); S2 (cache key, row-class
attname); S3 (scan seed + projection, walk-model attname); S4
(order term, child-meta attname). No fifth id-default
resolution exists. Whole-package census `== "pk"` (15 hits, 11
files): the four sites; the F1 owner (`relations.py:269`) +
landed keyset composer; the F2 NAME x4 (closed); the batched
slot-compare pair (`relay.py:313` / `:398`, WT consumers, not
resolutions); the bool membership (`querysets.py:3464`,
`_is_model_column`, order-term acceptance); the whole-path
guard (`list_field.py:775`); docstring prose (`relay.py:304`).
`in (...,"pk")` membership (`filters/base.py:921`,
`plans.py:1096`, `definition.py:415` via `_normalize_pk_name`)
accepts spellings, never resolves. Reverse `_column_ref`
(`predicates.py:236`, field->`"pk"` for lookups, MTI-join
avoidance) runs the other direction in another domain. The
`"pk"` producers (`types/relay.py:272` stamp + `:312` default)
are H2's production side. Single-quote `'pk'`: zero hits
package-wide. Pure slot consumers (`types/relay.py:1057` /
`:1130` pass-through, WT `values_list("pk")` reads) listed,
uncounted.
- S1-vs-owner behavior contrast (why the merge fails
fidelity): current S1 on a `_meta`-less model raises
`AttributeError` at `model._meta.pk`; composed S1 (`try: owner /
except FieldDoesNotExist: None`) returns `(id_attr, None)` —
the fall-through shape meaning "no column, use the raw
literal". Loud becomes silent off-domain (principle 8:
exceptions raised are observable); both arms unreachable
through registered types (`model_for` + class-creation
validation), but the strict core's refusal must stay loud, so
faithful composition owes a pre-check — added machinery
restating the owner's guard. C2 detail: the composite gate
(HEAD-committed, `types/relay.py` `_check_composite_pk_for_relay_node`)
raises unless a consumer `NodeID` escapes the composite
surface — and an escaped type has `id_attr != "pk"`, so S1's
pk arm never sees a composite pk while the owner serves
ungated path classification. Different input domains, count 1.
- P1 probe, read-only shared-tree (`PatronProfile`, the live
relation-pk model), quoted: `pk field: OneToOneField | name:
patron | attname: patron_id`; `dict keys: ['_state',
'address_2', 'favorite_genre_id', 'patron_id',
'postal_code']`; `getattr(probe, "pk"): 7`. The `__dict__`
carries the attname never the name (S2's mapping is necessary
for the Decision-7 cache hit, spec-015 `:272` confirmed
mechanically); the bare literal still resolves (the mapping's
marginal value over no mapping is the hit, not correctness);
mapping to the NAME would serve `str(related row)` — refused
live by the no-lazy-load assert below.
- Oracle inventory: S1 — node-field tests (default + `NodeID`
arms) + the counting-slot threading test; S2 — unit pins
(dict-cache-first, getattr-fallback, `"pk"` fallback) + the
live relation-pk test; S3 — walker `only()` pins + the same
live test's single-statement shape; S4 — unit pins (`"pk"` ->
column, `-` DESC flip, non-local downgrade to windowed). The
live `test_patron_profile_relay_id_is_built_from_the_relation_primary_key_column`
mints ids from `patron_id` over `/graphql`, asserts one
statement against `library_patronprofile` with `patron_id` in
the SQL and zero touches to `library_patron` — pinning S2's
attname choice (name would lazy-load) and S3's projection
context on the name!=attname shape. Zero spec sentences
falsified (zero-edit; spec-015 `:272` / `:324` read, consistent).
- NodeID interplay classification: `encode_typename` owns the
TYPE half of the wire id; these four own the ID half's COLUMN;
the stamp/default (S0) produces the slot VALUE. Three rules,
three wire/contract halves, no shared change.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[lateral]: ../../django_strawberry_framework/optimizer/lateral_fetch.py
[relations]: ../../django_strawberry_framework/utils/relations.py
[relay]: ../../django_strawberry_framework/relay.py
[types-relay]: ../../django_strawberry_framework/types/relay.py
[walker]: ../../django_strawberry_framework/optimizer/walker.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
