# DRY review: `pk-segment-name-inlines`

Status: verified
Run: 0.0.15 2026-10-11-21

## System trace

Four walkers spell `X._meta.pk.name if <piece> == "pk" else <piece>`
(live : HEAD; every line byte-identical to HEAD):

- `orders/sets.py:836` (:822) `OrderSet._scoped_hops` — joined-path
STRING per scoping hop, fed to `predicates.py::visible_row_exists`.
Passthrough posture (no try): inputs pre-validated by
`_active_order_terms` → `classify_path`, and `zip(segments, joins)`
bounds the walk to classified hops, so the loop cannot raise.
- `connection.py:892` (:890) `_resolve_order_path_field` — terminal
FIELD or None for cursor-column anchoring. try/except-None over raw
order-path input.
- `utils/permissions.py:699` (:741) `_walk_undeclared_hops` —
undeclared-hop NAME string into visibility EXISTS
(`_reaches_related` → `predicates.py::related_rows_exist`).
Consumes pre-classified `leading_relation_hops` (raw segment);
never raises. Not a gate slot (gates read the declared walk).
- `list_field.py:728` (:761) `_resolve_order_field_path` —
`(FIELD, OPTS)` or None for order-term certification.
try/except-None over raw input; walks OPTS, not a model.

Considered owner: `utils/relations.py:255`
`_resolve_segment_field` — answers the FIELD, raises
`FieldDoesNotExist`; already shared by `classify_path` and
`_lenient_traverses_to_many`. Composing `(...).name` is the only
fence-legal consolidation (no new helper).

## Verification

### Matrix

1. Cross-flavor: no mirror in filters/forms/rest
(`filters/sets.py:4308` binds the literal, no conditional).
2. Sync/async: all four are sync pure reads; async callers reuse the
same sync helpers. No twin.
3. Derived-twice: the name-vs-column split is intentional per
context, not one fact twice — `lateral_fetch.py:1203`,
`types/relay.py:355`, `walker.py:871` resolve ATTNAME where a column
is required; the four sites are name contexts (`get_field` input /
ORM path strings).
4. Round-trip: the alias is read one way; Django owns both
directions. No pair.
5. Other media: four walk docstrings state the rule; oracles pin
orders (`test_sets.py:2838`, `"pk"` → `"patron"`) and connection
(`test_keyset_connection.py:404`, `"pk"` → `"id"`); the
list_field/permissions TRUE arms assert nothing (D1). Spec corpus:
zero pk-segment sentences → nothing to rewrite.
6. Omission: walkers not honoring `pk` —
`plans.py::_select_path_missing_connectors` (`"pk"` → drop path;
fail-safe) and `querysets.py::_prefetch_relation_target_or_none`
(`"pk"` → None; `pk` names only to-one relations). No contract
source establishes `pk` must be honored there → intentional
per-contract, not defects (`classify_path` rationale stands).

### Challenges

- C1 ("pk" alias retired): Django-side change, excluded per DRY.md
(Django-owned token grammar); implausible (bedrock API). No count.
- C2 (alias resolves to attname in name contexts): no motivator —
column contexts already do (`lateral_fetch.py:1203`); name contexts
accept both spellings and the docstrings pin name. Implausible.
- C3 (mid-path vs terminal-only): all four honor mid-path, matching
Django query parity (`author__pk` valid; list_field mirrors
`find_ordering_name`; orders/permissions build ORM paths).
Terminal-only diverges from Django. Implausible.
- C4 (compose `(...).name`): string pair cannot — `(...).name`
renames attname → name (`get_field` accepts attname, Django
`options.py`), while the inline is the identity off-`pk`; that
falsifies "mirrors input" and the walk docstrings (ONLY pk
renamed). Field pair composes behavior-identically (proven single
+ composite) but is x2 single-expression, non-security, no-drift —
below bar, F1-adjacent, recorded-separate trigger unfired.
- Security clause (argued, rejected): the policy lives in the walks
(hop enumeration, scope binding), recorded separate; the alias
spelling carries no policy; drift modes fail loud (`FieldError`) at
three sites and loud-or-contrived at the fourth; zero drift exists.
Consolidating spelling removes no security-relevant obligation.

## Findings

### F1: pk-segment name mapping — REJECTED (four per-walk idioms)

- Contract: field-layer walks honor Django's `pk` alias per
segment; pinned by Django query parity; postures differ
(passthrough / None / pre-resolved).
- Sites: the four definitions above. `_resolve_segment_field` is
the FIELD owner (answers field + raise), not this rule's owner.
Projections: four docstrings. Oracles: two pinned, two unpinned.
- Challenges: C1–C4 above; no plausible our-change moves two
sites. Count 1 → independence.
- Owner/lifetime: none; stays inline. No stored derivation.
- Migration: none (zero-edit). Index row for Worker-0:
`pk-segment-name-inlines`, owner none, files orders/connection/
permissions/list_field/relations, `rejected`.
- Shrinkage: net 0; no machinery (nothing added).
- Distinct: string-answer pair vs field-answer pair; name-vs-column
split; exclusions — `_target_pk_name` (model-level name-or-None
for fabricated shapes; composing it leaves the conditional, zero
rule shrinkage, cross-flavor import), `_is_model_column` (bool
membership incl. attname), `list_field.py:775` (whole-path
compiler-mirror guard), `plans.py:1096` (terminal uniqueness
membership over all three spellings), `keyset.py:248` (F1
sibling), relay id-attr sites (F3 sibling), `types/base.py:1714` /
`:2007`, `filters/sets.py:4288` / `:4308`, `_key_gate_path` (name
reads, no segment conditional).
- Proof: executed Django probes (`uv run`, quoted in
`## What shrinks`); static zip⊆classified non-raising proofs per
loop. No new tests (zero-edit).
- Negative control: none (rejection; staying inline threatens no
bypass).
- Coupling: none. Sibling items C1 (F1) / H1 (F3) untouched; C1's
outcome is trigger T3, not coupling.
- Freshness: HEAD `c37a08a0`, baseline `19ee1cee`; live blobs
orders `79c369b3`, connection `3e111147`, permissions `dbb8f602`,
list_field `b5cfe957`, relations `b0cc6c33`; HEAD lines
:822/:890/:741/:761 byte-identical; population `== "pk"` 15 hits
in 11 files plus `pk.name` / attname census — no fifth
segment→name mapping; contract sources: walk docstrings, Django
`options.py`, two pinning oracles.
- Triggers: T1 a third string-site, or a second alias rule at
either string site; T2 the owner gains a passthrough/non-raising
NAME variant; T3 C1 lands and extends the field-owner contract to
cursor/certification walks; T4 Django changes the alias; T5 any
site's spelling drifts.

## Defects

- D1 (oracle gap): no asserting oracle for the pk-TRUE arm at
`list_field.py:728` and `utils/permissions.py:699`; siblings pin
theirs (orders `:2838`, connection `:404`). Statement coverage
of one conditional expression cannot see the arm. Owner:
`tests/test_list_field.py` + `tests/test_permissions.py`
(live-first if reachable; permissions arm needs a relation-keyed
model plus a pk segment).

## Pending execution

None.

## Judgment

Four per-walk idioms, two responsibilities, no plausible
our-change moves two sites; security clause rejected; zero edits.

## Independent verification (Worker-2)

Pass 1, `dry/pk-segment-name-inlines/verify-1`, detached HEAD
`c37a08a0`, baseline `19ee1cee` (stash commit, HEAD-is-ancestor).
Order note: the artifact file was already open when this pass
started, so Findings were seen before the trace below finished;
every claim was still re-derived with own patterns, own probes,
own drift table before reconciling. No landable candidate found.

Own trace. Census `== "pk"` over the package: 15 hits / 11 files
(14 code + 1 docstring `relay.py:304`), classified exactly as W1.
Sweep `pk\.name` (regex): the 4 segment-conditionals plus
name-reads `types/base.py:1714` / `:2007`,
`filters/sets.py:4288` / `:4308` (literal bind, no conditional),
docstrings only elsewhere; `_key_gate_path` is getattr
name-or-None, no conditional. No fifth segment-to-name mapping.
Postures re-derived: orders:836 passthrough (loop body is attr
reads + stamped-flag `has_custom_get_queryset`: structurally
non-raising; `_active_order_terms`->`classify_path` at the two
callers plus `zip(segments, joins)` buys alignment, not
non-raising); connection:891 None-on-failure over raw input
(try/except); permissions:699 pre-resolved (consumes raw
`hop.segment` from `leading_relation_hops`; body is total reads)
-- `RelationPathHop.segment` is the raw spelling
(`relations.py:350` `segment=segment`); list_field:728
None-on-failure over raw input walking OPTS. Contract split
confirmed: string-answer pair (ORM-path EXISTS inputs) vs
field-answer pair (FIELD answers). Pre-findings verdict: reject,
zero-edit -- same as W1.

Consolidation hunt (own). Field pair composes exactly (single +
composite + relation-keyed agree; `get_field` failures map to the
same None arms) but is x2 single-expression, non-security, no
drift: below bar. String pair: composition renames attname to name
in the intermediate, which my probes show the ORM erases
(`names_to_path` joins byte-identical for `author__name` vs
`author_id__name`); still below bar (same C1-C3 implausibility)
and it falsifies the ONLY-pk-renamed pins, so no candidate.
NAME-variant owner: absent, and creating one is added machinery.
`_target_pk_name`: composing it leaves the conditional (zero
shrinkage) and imports optimizer from below. `_is_model_column`
(bool), `plans.py:1096` (uniqueness over 3 spellings),
list_field:775 (whole-path compiler mirror): wrong contracts.
Security clause: gates read the declared walk alone (walk
docstring: "an undeclared hop has no branch gate";
`relation_path_gates` defaults `undeclared=False`), both string
sites feed ORM EXISTS paths; drift table re-derived per site --
orders/permissions: wrong name -> FieldError loud, unmapped "pk"
-> ORM-honored alias, identical rows; connection: None ->
`keyset_contract_error` GraphQLError loud; list_field: None ->
False verdict, fail-closed refusal. No drift direction silently
widens exposure. C3 parity confirmed (`pk__name` resolves on a
relation-keyed model). Django probes re-run on venv Django 6.1.2
/ Python 3.14.8: `S.get_field("pk")` raises, `M.pk.name == "pk"`,
`M.get_field("pk") is M.pk`, attname accepted -- all confirm W1.
Script: `docs/dry/temp-tests/pk-segment-name-inlines-verify-1/w2_django_probes.py`.

Matrix: axis-1 `filters/sets.py:4308` binds the literal (sweep);
axis-2 all four sync pure reads; axis-3 the 3 attname sites are
column contexts (`lateral_fetch.py:1203` db-column ORDER BY,
`types/relay.py:353` row `__dict__` key, `walker.py:870` `.only()`
mask); axis-4 one-way alias, Django owns both directions; axis-5
both oracles independent and TRUE-arm-pinning
(`test_sets.py` `ProfilePaths` `"pk"` -> `"patron"`,
`test_keyset_connection.py` `"pk"` -> `"id"` + None arms);
axis-6 omissions per-contract and safe-direction
(`_select_path_missing_connectors` drops to a fallback query,
`_prefetch_relation_target_or_none` keeps status-quo, pk names
only to-one relations). Omission pair is not a defect.

Triggers: T1/T2/T4/T5 firable and measurable as stated. T3 RULED:
does NOT fire on C1 landing -- C1 is verified keyset-side-only
(owner bytes unedited, third call site, contract unchanged), so
the conjunction's extension clause is false; this rejection is
not time-bombed. D1 confirmed: zero `pk` tokens in
`tests/test_list_field.py`; only unrelated `pk` tokens in
`tests/test_permissions.py`; `NumberFilter(field_name="pk")`
leaves walk None / zero hops; the filters pk-relation test can
only pass identically under either spelling. Coverage selection
(190 passed, 1 skipped, 22.6s): lines 699 + 728 covered,
TRUE arms unasserted -- statement-covered-but-unasserted exactly.
Homing to 053 test-debt (Worker-0) is correct; not blocking.

Freshness: worktree blobs orders `79c369b3`, permissions
`dbb8f602`, list_field `b5cfe957`, relations `b0cc6c33` match the
pins; connection is `29252be7` vs pinned `3e111147`, drift
attributed by content to item B's verified port (import + 2
calls, hunks :83/:2301+, outside the fenced :892 region; plan
confirms blob `29252be7` is B's port). Fenced region
byte-identical baseline-to-worktree; all four site lines
byte-identical HEAD-to-worktree (live 836/891/699/728). Item diff
on the four package paths vs baseline: empty except B's two
ledger-owned hunks; no new files. Finding unaffected.
Pending None: correct (W1 probes re-ran here, non-raising proofs
re-derived; nothing typed `proof:`/`gate:` remains). Coupling
none: correct (zero-edit; C1 touches keyset+tests only).
Prose/shape: `:NN` citations allowed (AGENTS.md rule 28 exempts
`docs/dry/dry-*.md`); no process provenance; Run line matches
plan run 21; W1 body untouched at 150 lines, What shrinks +
10-group link defs intact (this section is the additive W2
record); no `### Enumeration` heading is acceptable on a family
item (census carried in What shrinks, checked member by member).
Ruff: zero production paths touched, nothing to run.

Reconciliation deltas (all verdict-neutral, no Defects entry --
package has no defect): (a) C4 "string pair cannot" holds at the
documented-contract level (pins falsified) though the rename is
ORM-invisible end to end -- either road reaches below-bar reject;
(b) drift letter is 2xFieldError + GraphQLError + fail-closed
refusal rather than "FieldError at three", substance identical;
(c) orders non-raising is structural, pre-validation buys
alignment; (d) connection blob + line drift (892->891) per above.
Verdict: verified. No revision candidate exists above the bar.

## What shrinks

Net package change: zero lines (rejection). What was counted and
where it stays:

- The four name-spellings stay inline, one per walk: orders `:836`
(joined scoping path), permissions `:699` (visibility EXISTS hop
name), connection `:892` (cursor-column intermediate),
list_field `:728` (certification intermediate). No fifth
segment→name spelling exists: the whole-package `== "pk"` census
(15 hits, 11 files) classifies as the four sites, the
`_resolve_segment_field` owner (`relations.py:269`, FIELD answer),
the keyset twin (`keyset.py:248`, F1 sibling), the id-attr twins
(`relay.py:169`, `types/relay.py:353`, `walker.py:870`, F3
sibling), the batched id-attr pair (`relay.py:313` / `:398`,
blocked), the bool membership (`querysets.py:3464`), the column
resolution (`lateral_fetch.py:1203`, attname), and the whole-path
guard (`list_field.py:775`).
- The considered composition, per site: orders — rejected
(attname rename falsifies mirrors-input; proven `get_field`
accepts attname per Django `options.py::_forward_fields_map`);
permissions — rejected (same rename inside visibility EXISTS
paths); connection — composable but below bar (x2
single-expression, cursor anchoring is not
visibility/scoping/db-routing, no drift); list_field — same
verdict as connection (certification fail-closedness, not data
exposure). Executed identity proofs (composite model `M`,
single-pk model `S`, Django 6.1.2 venv): `M._meta.pk.name ==
"pk"`, `M._meta.get_field("pk") is M._meta.pk` True,
`S._meta.get_field(S._meta.pk.name) is S._meta.pk` True,
`S._meta.get_field("pk")` raises `FieldDoesNotExist`.
- Exclusion triggers: `_target_pk_name` — the rule becomes
name-or-None instead of segment-conditional (implausible);
`_is_model_column` — a site needs bool column-membership, not the
name; `list_field.py:775` — per-segment certification needs the
whole-path verdict; `plans.py:1096` — walkers need
spelling-agnostic pk recognition; name reads (`types/base`,
`filters/sets`, `_key_gate_path`) — a segment conditional appears
at one; column sites (lateral, types/relay, walker) — a name
context starts resolving attname, or vice versa.
- Oracle inventory: pinning — `tests/orders/test_sets.py:2827`
(PatronProfile `"pk"` → `"patron"`),
`tests/test_keyset_connection.py:401` (`"pk"` → `"id"` plus six
None arms); gap — D1 above (zero pk-segment assertions reach
`list_field.py:728` / `utils/permissions.py:699`; the
`NumberFilter(field_name="pk")` filters tests yield zero hops, so
they never execute the permissions arm).

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
