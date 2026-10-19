# DRY review: `relation-link-readers`

Status: verified
Run: 0.0.15 2026-10-11-19
Item: Family `relation-link-readers` (run 19, item 2)
Worktree: `~/projects/worktrees/django-strawberry-framework/dry-0015`
ITEM_BASELINE: `c723f857fc19d6dc07dea4b7438051e6976719ae` (resolves as commit)
HEAD: `c37a08a085113d628a554ee199f4d741d7c86cdf` (unmoved the whole item)

## System trace

Six targets in `utils/relations.py` at HEAD bytes: `RelationLink` :764,
`relation_link` :814, `m2m_through_model` :856, `m2m_through_link_fields`
:870, `is_single_column_foreign_key` :912, `leading_relation_hops` :562.
The link five landed in `fe6a6df0`, the hops in `37dcbf70`; the seventh
`fe6a6df0` sibling was deleted by `337b3317` with zero references left.
Worktree dirt on `relations.py` is foreign hunt work (lenient-arm
deletion); every byte below is `git show HEAD:` / `git grep HEAD`. The
stack composes by name (`relation_link` -> through-link-fields ->
through-model; `FieldMeta` stamps slots; taxonomy, predicates, filters,
mutations, permissions, types, inspector consume). Zero edits, no attribution owed.

## Verification

### Matrix

1. Cross-flavor: every flavor composes the relations owner; no flavor-local
   link vocabulary (the `forms`/`mutations` `m2m` names are other subjects).
2. Sync/async: inapplicable, pure sync metadata reads, zero `async def`.
3. Derived-twice: full residue census in F1/F5/F6; each spelling counts 1.
4. Round-trip: no inverse; the side-swap is inside the one through body.
5. Other media: oracles spell own pins; specs 001/002/003/016/027/033-035
   describe `fe6a6df0`; zero-edit falsifies none.
6. Omission: every consumer enumerated; no attname-join remains; each
   `target_field` read is gated on a proven FK or Django-semantic (F5/F6).

### Challenges

- C1: M2M convention flip -> M2M arm = 1; new link shape -> body = 1;
  attname rename -> the two owner properties = 1 site.
- C2: `through_fields` honoring -> link-fields = 1; slot rename -> model
  read = 1; Django breaks the naming API -> old R10 trigger, unfired.
- C3: drop O2O from cascade -> permissions wrapper narrows = 1; a
  column-carrying non-FK -> write gate admits, join gate must not = 1+1.
- C4: GFK traversable -> `classify_path` = 1 (hops follow); prefix
  strictness -> hops = 1; cardinality rule -> classifier = 1.
- C5: Django unifies reverse targets with link targets -> trigger,
  unfired; composite `to_field` leaves -> the filters site = 1.
- C6: GFK restriction -> predicates arm = 1; prefix tolerance ->
  refused by contract (fail-closed) = 0.

## Findings

### F1 — link-column derivation single-owned (no edit)

`local_related_fields` x3 + `foreign_related_fields` x1 code sites, all
inside the `relation_link` body; zero elsewhere package-wide. 8 consumer
calls in 6 files compose by name; the attname properties sit ON the
owner. Owner: `utils/relations.py::relation_link` (narrowest importable
home). Proof: static-reviewed census + C1, every count 1.

### F2 — through reads layered single-owned (no edit)

`fe6a6df0` deleted the taxonomy-local `_through_link_fields` and the
taxonomy now imports both relations readers; zero through-FK scanners
exist (only Django's own `_get_m2m_attr` scans, upstream). Old R10
re-derived fresh: the naming-API strategy won, rationale verbatim at
the new owner, trigger unfired. Proof: static-reviewed + C2.

### F3 — one-column gate vs write-backing screens (rejected)

isinstance-FK + column (join/cast/filter API guarantee) vs kind +
column + related model (write backing) vs the R29 screens (cursor,
certification): four tests, four change reasons, C3b moves exactly
one. All consumers on-contract (5 shape gates, 2 write screens).
Trigger per pair: two contracts answer one question.

### F4 — leading hops a facet, not a fifth walker (no edit)

No `_meta` walk of its own: longest classifiable prefix of the cached
`classify_path`, adding only the prefix rule. Walking, cardinality
and traversability changes move the classifier alone (C4); 5 consumer
sites in 4 files compose by name. Answers hop plans, never columns.

### F5 — lookup-comparison target vs link targets (rejected)

`filters/sets.py:4237` reads `path_infos[-1].target_fields`, and
Django source proves it differs from the link: forward identical
(both are `foreign_related_fields`); reverse DIVERGES (hardcoded pk
vs `to_field` targets); M2M DIVERGES (target-side vs source-side).
The link answer would misbind leaves across models (Django-owned
spelling). Trigger: Django unifies the two answers.

### F6 — correlation-step walk vs hop plan (rejected)

`predicates.py::_correlation_steps` answers per-segment column pairs
(M2M unrolled, `ConfigurationError` on non-relations) where the
classifier answers hop records and the prefix helper tolerates tails;
tolerance here would fail open (uncorrelated EXISTS). C6 counts 1/0.
Trigger: the steps answer hop plans instead of pairs.

## Defects

None. The `field_meta.py:298` parenthetical (reverse child pk, M2M
target pk) re-verified accurate against Django's three `target_field`
definitions before filing anything.

## Judgment

Zero-edit: `fe6a6df0`'s consolidation is complete at HEAD: no residue, no
second definition on any axis; the near-misses are contract forks with triggers.

## What shrinks

Nothing: no definitions removed, no call sites rewritten, no tests
added or removed. Net package +0/-0, tests +0/-0 over ITEM_BASELINE.
The bar check: no plausible change forces edits at 2+ definitions
carrying real logic (every challenge counts 1 or 1+1-separate), the
copies never drifted (the one historical twin was already moved into
the owner by `fe6a6df0`), nothing here is security / data-exposure /
db-routing relevant beyond already-gated FK reads, and no principle-11
abstraction without responsibility survives (the sibling was already
deleted by `337b3317`). Freshness: HEAD `c37a08a0`; blobs relations
`63f46750`, join_taxonomy `053eefeb`, field_meta `1098cce2`,
filters/base `85959fe5`, filters/sets `ee059735`, predicates
`71593939`, lateral `995f1aa2`, permissions `b7ab8c69`,
mutations/inputs `f821661e`; population the whole package at HEAD via
`git grep HEAD`; contract sources `fe6a6df0` / `37dcbf70` / `337b3317`
plus Django venv `related.py` / `reverse_related.py`.

## Index rows for Worker-0

- `relation-link-column-read` | `relations.py::relation_link` | relations
  + 6 consumer files | consolidated, single-owned, no edit (F1).
- `m2m-through-link-resolution` | through-link-fields (+model) |
  relations + taxonomy + predicates | consolidated, R10 substance
  survives with trigger unfired (F2).
- `single-column-fk-gate-vs-write-backing` | rejected, four screens
  with trigger per pair (F3).
- `leading-relation-prefix-fallback` | `leading_relation_hops` |
  relations + 4 consumer files | consolidated, facet, no edit (F4).
- `lookup-comparison-target-vs-link-targets` | rejected, Django-source
  divergence on reverse + M2M (F5).
- `correlation-step-walk-vs-hop-plan` | rejected, pairs vs hops with
  fail-closed vs tolerant postures (F6).

## Independent verification (Worker-2)

### Own trace (recorded before reading `## Findings`; only `###` titles + index-row one-liners seen)

Rule: "which columns join this relation" + the screens/walkers beside it.
Every cite below is HEAD bytes (`git show HEAD:` / `git grep HEAD`); the
worktree `utils/relations.py` is hunt-dirty and was never read for verification.

Sites + roles (mine): DEFINITION `utils/relations.py::relation_link` (the one
link reader: forward from own slots, M2M via the through source FK, reverse via
`.field`; malformed answers empty; `local_related_fields` x3 plus
`foreign_related_fields` x1, all inside this one body, `_link_field_tuple` its
validator); DEFINITION `utils/relations.py::m2m_through_link_fields` (+
`m2m_through_model`: through-table FK pair from the forward field's
`m2m_field_name` naming API, side-swap internal; the only `through`-slot and
only `m2m_field_name` code reads package-wide); DEFINITION
`utils/relations.py::RelationLink` (carrier/target record); four DEFINITION
screens (`is_single_column_foreign_key`: join/cast/filter gate;
`is_forward_concrete_relation`: write-backing; `is_forward_many_to_many`:
writable M2M; `is_many_side_relation_kind`: list-vs-single); DEFINITION
`utils/relations.py::leading_relation_hops` (longest-classifying-prefix facet
over the cached classifier, no own `_meta` walk). CONSUMERS composing by name:
`optimizer/join_taxonomy.py::_carrier_attnames`/`_forward_join_columns`,
`optimizer/field_meta.py::FieldMeta._from_field_shape` (owns the stamp shape),
`optimizer/predicates.py::_correlation_steps` (owns pair direction, the M2M
two-link split, indices, `referenced`, the generic restriction),
`filters/base.py::_relation_uses_non_pk_to_field`,
`mutations/inputs.py::_carrier_backed_link`, the gate's 5 call sites, and the
hops' 5 consumer sites / 6 call sites (filters/sets.py x2, orders/sets.py,
utils/permissions.py, utils/querysets.py). Django-source readings, not OUR
rule: `filters/sets.py::_leaf_chain` `path_infos[-1].target_fields` (the column
Django's lookup compares), `filters/base.py::_model_identity_column`
follow-down, the `permissions.py` re-projection and lateral `.target_field`
reads (all on gate-passed or descriptor-resolved single-column FKs),
`predicates.py::_stored_column` (MTI stored-column rule). ORACLES spell own
literals (e.g. `tests/utils/test_relations.py::test_relation_link_reads_the_link_column_pairs`
asserts attname tuples); PROJECTIONS are the spec/module-doc restatements.

Challenges (mine), each count 1: C1 through-FK resolution changes move only
`m2m_through_link_fields`; C2 pair-validation changes move only
`relation_link`/`_link_field_tuple`; C3a a gate widening moves only
`is_single_column_foreign_key`; C3b a write-backing change moves only
`is_forward_concrete_relation` with the gate untouched (each screen owns its
change reason); C4 prefix semantics move only `leading_relation_hops`, beside
four distinct walkers (`classify_path`, `_lenient_traverses_to_many`,
`_correlation_steps`, the querysets prefetch-target walk: different contracts,
populations, postures); C5 a Django lookup-comparison change moves only the
sets.py:4237 site (Django's rule, not ours); C6 a pairing change moves only
`_correlation_steps`. Owner I would choose: `utils/relations.py`, already the
owner throughout; the sets.py:4237 read stays local. Independent hunt (sweeps
above, each surviving site read individually): no inline link derivation
survives, no second definition, no drift, no principle-11 abstraction without
responsibility.

### Reconciliation (after reading `## Findings`; every difference explicit)

F1 agree, one count correction (verdict-neutral): the x3/x1 census and 8 calls
match my exhaustive grep exactly, but consumer FILES are 5, not 6
(filters/base, mutations/inputs, field_meta, join_taxonomy, predicates;
tests add 5 more calls in 1 file, so no reading gives "8 in 6"). Corrected
F1/index-row-1 text for Worker-0: "8 consumer calls in 5 files". Conclusion
(single-owned, compose by name) unaffected. F2 agree: standalone
`_through_link_fields` zero hits anywhere; `fe6a6df0`'s deletion and the
near-verbatim rationale move verified via git (docs/review untouched); zero
scanners (only by-name `get_field` + Django's upstream `_get_m2m_attr` scan);
trigger unfired (naming API present in installed Django 6.1.2). F3 agree with
a better cut than mine: my fourth screen (`is_many_side_relation_kind`, a
kind-set read) was the wrong population; W1's four (gate, write-backing,
cursor `keyset.py:343`, certification attestation screen) I located, read,
and found each test-pinned with its own change reason; C3b moves exactly one
verified (write gate admits, join gate must not); 5 shape gates / 2 write
screens verified. F4 agree: no own `_meta` walk verified (segment loop +
cached classifier only); correction to MY trace: 5 calls in 4 files, not 6
(W1 right). F5 agree: divergence re-proved at installed Django source
(forward `foreign_related_fields` related.py:899; reverse hardcoded pk :919;
M2M target-side join2infos); misbind + trigger sound. F6 agree: pairs-vs-hops
and fail-closed-vs-tolerant postures read in both bodies; trigger sound.
Matrix agree on all axes: axis-4 side-swap is internal (one body); axis-5 the
shape-cites verified in 001/003/016/027/033/034/035 (002 thinnest: one generic
connector-columns sentence — precision note only); zero-edit falsifies none.
Proofs: static-reviewed censuses SUFFICIENT, no execution owed (absence claims
need pinned-byte sweeps, not runs; Django claims verified at Django source;
pinning oracles exist and are cited; the gate runs the suite; no workspace run
needed for zero-edit). Freshness: all 9 blobs match my recomputation. Index
rows: 6 rows accurate modulo the F1 file-count correction above. No oracle
rewritten; AGENTS.md prose rules hold (`:NN` allowed in dry scratchpad, no
banned content, no tests added); ruff owed on nothing (no .py touched;
artifact excluded from layout rules, `--check` exit 0). No production defects
found; corrections live here, not under `## Defects`.

Verdict: verified. Zero-edit stands: every challenge counts 1 or 1+1-separate,
rejections carry contract differences + triggers, no consolidation missed.

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
