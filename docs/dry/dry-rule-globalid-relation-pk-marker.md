# DRY review: `globalid-relation-pk-marker`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

The marker answers "which column does this relation's GlobalID identify": the
target pk by default, the pk-qualified relation path when the forward FK/O2O
binds on a non-pk `to_field` (a Relay GlobalID always carries the target pk,
while the FK stores/joins on the `to_field` column, so the raw
`{field__lookup: node_id}` predicate compares the pk against the wrong
column). Provisional owner confirmed:
[filters-base][filters-base]`::_GLOBALID_RELATION_PK_ATTR` +
`::_relation_uses_non_pk_to_field` + `::_marked_pk_field_name`; known member
files [filters-base][filters-base] + [filters-sets][filters-sets] complete —
package-wide grep for the trio finds production code in exactly those two
files (remainder: oracles in [test-base][test-base] / [test-sets][test-sets],
one plan-doc projection, this family's records).

- **Write (stamp).** Single site:
  [filters-sets][filters-sets]`::FilterSet.filter_for_field`
  #"if _relation_uses_non_pk_to_field(field)": stamps boolean `True` under
  the attr constant on the freshly built `relay_replacement` only when the
  predicate says so. `filter_for_lookup` returns class+params pairs and never
  an instance, so no second stamp site can exist there by construction.
- **Derive (predicate).** Single definition:
  [filters-base][filters-base]`::_relation_uses_non_pk_to_field` (concrete +
  single-valued-forward guards, then `target_field is not target_pk` by
  object identity, never by name spelling).
- **Read (derive-at-filter-time).** Single home:
  [filters-base][filters-base]`::_marked_pk_field_name`, called by exactly
  the two sibling readers (`GlobalIDFilter.filter`,
  `GlobalIDMultipleChoiceFilter.filter`); both compile the returned
  `f"{live field_name}__pk"` through the shared whole-value helper, never by
  a private spelling.
- **Lifetime.** Set once at generation (class build / first `get_filters`);
  rides the instance `__dict__` through `deepcopy` (expansion rebase +
  per-request copies — the live-instance pin at
  [test-sets][test-sets] #"live, _GLOBALID_RELATION_PK_ATTR, None) is True"
  proves the request-time copy still carries it); read per request at filter
  time; invalidated with the filterset lifecycle (`registry.clear()` resets
  `_expanded_filters` + snapshot; regeneration re-stamps). Validity key: the
  generating (filterset class, field) binding. Sole mutator: the stamp site.
  No new shared state beyond django-filter's own instance lifecycle.

## Verification

### Matrix

1. **Cross-flavor mirroring** — searched, no twin: orders family has no
   GlobalID relation surface (no GlobalID symbols in `orders/base.py`);
   write-side `relay.py::_resolve_real_pk` is the decode pipeline's own
   seam ([decode-rule][decode-rule] states the difference); cascade
   `permissions.py` `target_field` projection answers membership-values, not
   the GlobalID column; optimizer `field_meta.py` / `join_taxonomy.py` /
   `lateral_fetch.py` `target_field` reads answer join planning. Different
   questions, recorded under Findings.
2. **Sync/async twins** — inapplicable with reason: both filter bodies are
   sync; the derivation has no await boundary and touches no async state.
3. **Derived knowledge** — single-sited: the `__pk` path is derived once
   from the live `field_name`, never stored (the frozen-path alternative is
   rejected in prose at the attr block); pk-vs-`to_field` is object
   identity, never a respelled name.
4. **Round-trip pairs** — stamp (generation) / read (filter time) share the
   attr constant + predicate + derive-home by name across the module edge.
   No inverse duplication.
5. **Contracts in another medium** — oracles classified honestly: literal
   behavior pins (stub-qs predicates `{"shelf__exact": "7"}`,
   `{"genres__in": ["1", "2"]}`; row sets `{"a-child"}`,
   `{"a-child", "b-child"}`, expanded-leaf parent rows; silent-wrong pins
   `wrong.count() == 0`; `GLOBALID_INVALID` empty-id pins) are independent;
   the `getattr(..., _GLOBALID_RELATION_PK_ATTR) is True` stamping
   assertions import the owner constant, so they move with a rename — pins,
   not independent oracles. Projections (attr block + all four docstrings +
   stamp-site comment) verified against the bodies they describe.
6. **Enforcement by omission** — enumerated every generated GlobalID leaf
   shape: own-PK (no marker; predicate on the own pk — correct), forward
   FK/O2O to pk (no marker; byte-identical — correct), forward FK/O2O to
   non-pk `to_field` exact+`in` (marker — corrected), M2M/reverse (no
   marker; terminal lookup resolves against the related pk — reverse proved
   by execution, P1), `isnull` (upstream Boolean; never reads the marker —
   correct), consumer-declared / override-generated (unstamped by design;
   consumer owns the predicate — intentional separation, trigger below). No
   contract source extends the marker to declared leaves, so no defect.

### Enumeration

Census instrument: `def`/`Assign` of the three names + production
`setattr`/`getattr`-on-attr + call sites, package-wide grep (78 trio hits;
production subset below; remainder oracles/docs/records).

| # | Site | Role |
|---|---|---|
| 1 | [filters-base][filters-base]`::_GLOBALID_RELATION_PK_ATTR` (1 assign) | definition (slot) |
| 2 | [filters-base][filters-base]`::_relation_uses_non_pk_to_field` (1 def) | definition (stamp predicate) |
| 3 | [filters-base][filters-base]`::_marked_pk_field_name` (1 def) | definition (read/derive home) |
| 4 | [filters-sets][filters-sets]`::FilterSet.filter_for_field` (1 `setattr`, 1 predicate call) | consumer (sole stamper) |
| 5 | `GlobalIDFilter.filter` (1 `_marked_pk_field_name` call) | consumer (reader) |
| 6 | `GlobalIDMultipleChoiceFilter.filter` (1 `_marked_pk_field_name` call) | consumer (reader) |
| 7 | [finalizer][finalizer] `_audit_globalid_filter_strategies` | excluded: resolves targets via `resolve_globalid_target_definition`; zero `to_field`/`target_field`/`__pk` hits — no parallel derivation |
| 8 | `permissions.py` / optimizer readers of `target_field` | excluded: different contracts (see Matrix 1) |
| 9 | [test-base][test-base] marker block + [test-sets][test-sets] stamp/rebase rows | oracles (10 + 8 executed in workspace, below) |
| 10 | attr comment block + 4 docstrings + stamp-site comment | projections (verified) |

### Challenges

- **C1 — new non-pk-`to_field` member; marker missing: loud or silent?**
  Definitions to move: **1** (the stamp predicate; callers follow by
  name). Missing-marker behavior is **silent** wrong-column (empty result),
  never loud — pinned by the standing red-green pairs (`wrong.count() ==
  0` beside the correct row set in both cardinalities). All
  framework-generated instances funnel through the single stamp site
  (`filter_for_lookup` builds no instances), so the silent shape is
  unreachable on framework paths; it is the declared-filter shape, which
  the consumer owns (separation below).
- **C2 — marker present but column renamed.** Definitions to move:
  **0**. Django-level rename: the predicate compares field objects by
  identity, not names. Mid-flight `field_name` rebase (expansion): the
  boolean survives `deepcopy` and the path derives at read from the live
  name — execution-verified in the workspace (expanded leaf
  `children__target` filters the parent correctly; 8/8 sets-side tests
  green on the mutated tree, P2). The frozen-absolute-path alternative
  (`"target__pk"` going stale to a `FieldError`) is the rejected design,
  recorded at the attr block.
- **C3 — rename the slot; add a third consumer.** Rename: **1** (the
  constant; stamp + both readers follow by name). Third consumer: **0**
  existing definitions move (one additive `_marked_pk_field_name(self)`
  call); a direct `getattr(flag)` read beside the home would be a second
  derivation — the trigger below.

Experiments (all in the disposable workspace; shared-tree runs forbidden
beyond the one authorized): P1 reverse-needs-no-marker, execution-verified;
P2 negative control (owner bypassed by a behavior-identical hand copy —
10/10 behavior oracles still pass), execution-verified; one focused
`--no-cov` shared-tree run, green. Commands + fingerprints under Findings.

## Findings

**F-1 `globalid-relation-pk-marker` — CONFIRMED single-owned; reject
further consolidation (no second definition exists).**

- **Contract + variation.** A forward FK/O2O bound on a non-pk `to_field`
  carries a boolean flag (never a frozen path); GlobalID predicates derive
  `f"{live field_name}__pk"` at filter time. Varies on covered relation
  shapes only (C1: 1; C2: 0; C3: 1/0).
- **Sites + roles.** Enumeration rows 1–6 (3 definitions, 1 stamper, 2
  readers sharing the home); rows 7–10 excluded/listed, not counted.
- **Challenges.** C1/C2/C3 above with counts 1 / 0 / 1+0.
- **Owner + lifetime.** Owner: the [filters-base][filters-base] trio
  (principle 7: the predicate rule lives where both consumers live;
  [filters-sets][filters-sets] already depends on base, so no reversed
  dependency; no other family imports the trio). Lifetime per principle 4
  in System trace. No move.
- **Migration.** None — already composed by name at every site.
- **Distinct behavior.** Kept separate with contract differences (Matrix 1):
  write-side `_resolve_real_pk` (NodeID→pk on the write path), cascade
  membership projection (`permissions.py`), join planning
  (`field_meta.py`/`join_taxonomy.py`/`lateral_fetch.py`), declared-filter
  predicates (consumer-owned byte-for-byte). Triggers: a marker read in
  the write pipeline; a `target_field` read deciding a GlobalID column
  outside `_marked_pk_field_name`; a framework-derived declared predicate.
  Home: this finding + the respective owner.
- **Behavioral proof.** Execution-verified: (i) authorized shared-tree
  `tests/filters/test_base.py::test_global_id_filter_non_pk_to_field_matches_by_target_pk
  --no-cov` — 1 passed; (ii) workspace P1 (reverse `children__in`
  resolves against child pk, SQL shows `child.id IN (...)` over the
  code-bound join — no marker needed); (iii) workspace P2 + sets-side
  marker selection (10 + 8 passed). Static-reviewed: census counts,
  single-stamp verification, byte-identical predicates. No
  `execution-deferred` entries.
- **Structural gate.** DEFERRED with proved reason: P2 shows a correct
  hand copy passes every behavior oracle, so sharing is pinnable only by
  a bespoke AST/name-cardinality shape — forbidden per [dry][dry]
  ("never a bespoke existence test per helper"). The durable pin is the
  existing prose at the owner (attr block + `_marked_pk_field_name`
  "single home" docstring), already present, so no projection edit is
  owed either. Revisit trigger: a third flag reader, a per-method copy,
  or a new pk-qualified filter family.
- **Coupling.** None. Zero production edits; nothing to land together.
- **Freshness.** `filters/base.py` working `ba52351c` == HEAD (clean);
  `filters/sets.py` working `4a40e51b` vs HEAD `4ab65a26` (external +22
  declared-bag hunk, predates `ITEM_BASELINE`, item-scoped diff empty —
  untouched); `tests/filters/test_base.py` `04da73cd` == HEAD (clean);
  `tests/filters/test_sets.py` working `a624a78d` vs HEAD `85d31c4b`
  (external +34 companion hunk at 5143+, marker rows at 715–1010/1320–1380
  untouched); `tests/_relation_fixtures.py` `1846a0093`;
  `types/finalizer.py` excluded by zero-hit grep; HEAD `bfaee91d`;
  `ITEM_BASELINE` `407552ad8cb17dafcae3dba30e63fc88d3502787` present.
  Workspace copy `__file__` =
  `.../dry-ws/globalid-relation-pk-marker/django_strawberry_framework/__init__.py`;
  DB `NAME` = the copy's own `examples/fakeshop/db.sqlite3`
  (fixture tables created + dropped inside the run; shared DB untouched).

## Defects

None filed. Considered and released with reason (not dropped): a
consumer-declared `GlobalIDFilter` on a non-pk-`to_field` relation filters
the raw column silently — but no contract source extends the marker to
declared leaves (the byte-for-byte ownership rule is the contract), so
per axis 6 this is an intentional separation (trigger above), not a
defect. The missing fakeshop non-pk-`to_field` relation (marked path stays
package-side, as the standing tests document) needs no new example model
inside this item; adding one is a schema decision for the maintainer, not a DRY
consolidation — noted, not filed.

## Pending execution

None. Every proof is `execution-verified` above (workspace `__file__` +
DB `NAME` recorded). Sharded/Postgres cells inapplicable by construction:
the marker decides a predicate column by field identity — no
alias/`using` decision, no dialect branch (`__pk` traversal is
vendor-neutral). Full-suite gate business belongs to the final-gate item:
the entry authorizes workspace runs plus one focused test, and a green
unmutated suite would discharge no failability proof for a finding that
proposes no gate.

## Judgment

Already one rule, one owner, shared by name at every site: one slot, one
stamp predicate, one read/derive home, one stamp site, two readers, zero
parallel derivations package-wide. Challenges count 1/0/1+0; lifetime
stated; separations carry triggers; no defect meets the bar. Zero
production edits; artifact only.

## Implementation (Worker 1)

Tracked changes: this artifact only (new file, untracked until Worker 0
records it). Item-scoped diff vs `ITEM_BASELINE`
`407552ad8cb17dafcae3dba30e63fc88d3502787` on both family paths is empty
(`git diff <baseline> -- filters/base.py filters/sets.py` prints nothing:
the `sets.py` +22 hunk predates the baseline — external concurrent dirt,
attributed, untouched). `## Owned changes` ledger confirms nothing on
either family path. No dirty path edited → no STOP arose. No
`CHANGELOG.md` touch; no commit.

Hygiene: `grep -c truncated` == 0 (shared tree). Ruff: `.md` is outside
ruff's corpus; scaffold checked via `scripts/check_trailing_commas.py` on
this path until clean (below). No pytest after edits (the only
shared-tree run is the pre-artifact authorized focused test).

Scratch paths (removal is Worker 0's, after `verified`, by explicit path):
`WS`
`/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/globalid-relation-pk-marker`
(left on disk holding its own `.venv` + the P2-mutated `base.py`; the
shared tree was never mutated). No `docs/dry/temp-tests/` needed (all
execution went to the workspace per the work order).

Worker 0 rows (exact): tick Family `globalid-relation-pk-marker`
([dry-plan][dry-plan] responsibility row + families list) as verified, Run
0.0.15 2026-09-19-1, CONFIRMED single-owned, zero production edits, no
pending execution; no `## Owned changes` row (no tracked edit landed);
home nothing (zero defects).

Worker 0 rows (exact): tick Family `globalid-relation-pk-marker`
([dry-plan][dry-plan] responsibility row + families list) as verified, Run
0.0.15 2026-09-19-1, CONFIRMED single-owned, zero production edits, no
pending execution; no `## Owned changes` row (no tracked edit landed);
home nothing (zero defects).

## Independent verification (Worker 2)

Recorded BEFORE re-reading `## Findings` (sites/roles/counts/owner derived
from the tree: [filters-base][filters-base], [filters-sets][filters-sets],
[test-base][test-base], [test-sets][test-sets], package-wide grep).

### Own trace (pre-reading)

- **Contract as I derive it.** A forward FK/O2O bound on a non-pk
  `to_field` stores/joins on that column while a Relay GlobalID carries the
  target pk, so the GlobalID relation predicate must compile against
  `f"{live field_name}__pk"`. Every other relation shape keeps the raw
  `{field_name__lookup_expr: node_id}` predicate byte-identical.
- **Marker write/read contract.** Slot
  [filters-base][filters-base]`::_GLOBALID_RELATION_PK_ATTR` =
  `"_dst_globalid_relation_pk"` holds a BOOLEAN `True` (never a frozen
  path). Stamp predicate
  [filters-base][filters-base]`::_relation_uses_non_pk_to_field` decides
  (`concrete` + `many_to_one`/`one_to_one` guards, then
  `model_field.target_field is not related_model._meta.pk` by identity).
  Read/derive home
  [filters-base][filters-base]`::_marked_pk_field_name` returns
  `f"{live field_name}__pk"` iff the flag is truthy and `field_name` is
  non-empty, else `None`. Boolean-not-path is what survives
  `_expand_related_filter` deepcopy + `field_name` rebase.
- **Writers found (1).**
  [filters-sets][filters-sets]`::FilterSet.filter_for_field`
  #"if _relation_uses_non_pk_to_field(field)": one
  `setattr(relay_replacement, _GLOBALID_RELATION_PK_ATTR, True)` plus one
  predicate call. `filter_for_lookup` returns class+params pairs, never an
  instance — no second stamp site can exist there by construction.
  Package-wide grep for `_dst_globalid_relation_pk` finds exactly the slot
  assign plus this `setattr`; no other writer.
- **Readers found (1 home + 2 callers).** One `getattr` home inside
  `::_marked_pk_field_name`
  (#"if getattr(filter_instance, _GLOBALID_RELATION_PK_ATTR, False)").
  Two callers, one call each: `GlobalIDFilter.filter`
  (#"pk_field_name = _marked_pk_field_name(self)" at the single-value
  branch) and `GlobalIDMultipleChoiceFilter.filter` (same call at the
  `in`-branch). No direct `getattr(flag)` read beside the home anywhere in
  production.
- **Definition counts.** 3 definitions, all in
  [filters-base][filters-base]: slot (1 assign), stamp predicate (1 def),
  read/derive home (1 def). 1 stamp consumer (single `setattr`). 2 read
  consumers (one home-call each). Zero second definitions package-wide
  (trio grep: production hits only in the two member files; remainder
  oracles/projections/records).
- **Owner I would choose.** [filters-base][filters-base] trio, principle 7 +
  lifetime: the predicate rule lives where both consumers live; sets already
  depends on base so no reversed dependency; narrowest cohesive owner every
  legitimate consumer can import; lifetime (set once at generation, rides
  instance `__dict__` through deepcopy/per-request copies, read per request,
  invalidated with the filterset lifecycle, sole mutator the stamp site)
  matches base's filter-instance ownership. No move.

### Enumeration (member-by-member, agrees 1-10)

Rows 1-3 (definitions), row 4 (sole stamper), rows 5-6 (two readers via the
home), row 7 ([finalizer][finalizer] `_audit_globalid_filter_strategies` —
opened: resolves via `resolve_globalid_target_definition`, zero
`to_field`/`target_field`/`__pk` hits, encode-only-strategy audit, different
contract), row 8 (`permissions.py`/optimizer `target_field` readers —
opened each, see sweep below), row 9 (oracles), row 10 (projections,
verified against bodies). No member missed; census instrument
(`def`/`Assign` + `setattr`/`getattr` + call sites, 78 trio hits) adequate.

### Reconciliation (agree on every point)

- 3 definitions in `filters/base.py` (slot, stamp predicate, read/derive
  home) — AGREE (lines verified: slot assign, predicate def, home def).
- 1 stamp consumer (single `setattr`) — AGREE (one guarded `setattr` +
  one predicate call in `filter_for_field`).
- 2 read consumers (one home-call each) — AGREE (`GlobalIDFilter.filter`
  + `GlobalIDMultipleChoiceFilter.filter`, each exactly one
  `_marked_pk_field_name(self)` call, both through the shared whole-value
  helper).
- Finalizer/optimizer/permissions `target_field` readers excluded with
  differences — AGREE (sweep below).
- C1 new `to_field` → 1; C2 rename/rebase → 0; C3 slot rename → 1; third
  consumer → 0 — AGREE (counts re-derived: C1 moves only the stamp
  predicate; C2 moves nothing — identity compare + live-name derivation;
  C3 rename moves only the constant; additive third consumer moves zero
  existing definitions).
- Owner `filters/base.py` (principle 7 + lifetime) — AGREE (my independent
  owner matches).
- CONFIRMED single-owned, zero second definitions, zero edits, durable home
  already at owner (no projection edit) — AGREE.
- No defects; no pending execution (all executed; P2 10/10 → gate deferral;
  sets-side 8/8; 1 focused shared-tree test green) — AGREE (judged below).
- `sets.py` +22 + test companion predate baseline, untouched — AGREE
  (re-hashed below; marker rows untouched).

### C1 silent-wrong-column judgment (challenged HARD) — accepted risk + trigger, NOT a defect

- **Oracle-body reading (opened, not summarized).**
  [test-base][test-base] `test_global_id_filter_non_pk_to_field_matches_by_target_pk`
  and `test_global_id_multiple_choice_filter_non_pk_to_field_union_by_pk`
  do BOTH in one body: (a) hand-stamp the marker (`setattr(f, ..., True)`)
  and assert the CORRECT row set (`{"a-child"}`, `{"a-child","b-child"}`) —
  pinning the CONTRACT (marked path derives `target__pk`); (b) build the
  RAW unqualified ORM (`filter(target__exact=pk)`,
  `filter(target__in=[pks])`) and assert `wrong.count() == 0` — pinning
  NECESSITY (unqualified compares pk against the stored `code` column and
  is wrong when `pk != code`, with `assert alpha.pk != alpha.code` making
  the divergence load-bearing). The `filter_for_field` stamp tests
  (`test_filter_for_field_marks_non_pk_to_field_relation_globalid_with_pk_path`
  asserts `is True`; `test_filter_for_field_fk_to_pk_relation_globalid_carries_no_marker`
  + `generated_forward_fk_in_*` negatives assert `is not True`) pin
  SUFFICIENCY (framework generation always stamps exactly the non-pk
  shape). The expanded-leaf tests pin the rebase shape (boolean survives,
  live-name derivation correct; stale absolute path would `FieldError`).
  So "pinned by pairs" = necessity pairs (wrongness of the unqualified
  shape) PLUS stamp-always-happens pins (generation tests) — not pairs
  alone.
- **What the pair pins.** The `wrong.count() == 0` pair pins that the
  CURRENT code is wrong IN THE MISSING-MARKER CASE (unqualified predicate
  against a non-pk `to_field` silently returns empty). It does NOT by
  itself pin that the marker is always stamped — the generation/stamp
  assertions do that, for framework paths. Both halves exist, so the silent
  shape is unreachable on framework-generated paths (`filter_for_lookup`
  builds no instances; every generated instance funnels through the single
  stamp site).
- **Defect? No.** Per [AGENTS.md][agents] trust boundary (via
  [dry][dry] axis 6 + `## Defects`): a defect needs the contract row it
  breaks + a feasible project shape under supported public API + the wire
  input reaching it. The reachable silent shape is the DECLARED-filter
  shape (consumer hand-builds `GlobalIDFilter` on a non-pk-`to_field`
  relation, bypassing `filter_for_field`). No contract source extends the
  marker to declared leaves — the byte-for-byte ownership rule (consumer
  owns a declared predicate) IS the contract establishing the separation,
  stated in Matrix 6 and Findings. A louder failure there (raise when an
  unmarked declared leaf sits on a non-pk `to_field`) would change what is
  accepted and seize a consumer-owned predicate — never
  behavior-preserving, and ambiguous-or-newly-proposed routes to the maintainer, not
  to a defect. Hence accepted risk with trigger, correctly released (not
  dropped) under `## Defects`.
- **Trigger that reopens it.** A framework-derived declared predicate; a
  third flag reader or per-method `getattr(flag)` copy beside the home; a
  new pk-qualified filter family; a marker read in the write pipeline; a
  `target_field` read deciding a GlobalID column outside
  `_marked_pk_field_name`. Any of these makes the silent shape a framework
  promise again.

### Parallel-derivation sweep — no second derivation (exclusions confirmed by opening each)

- `optimizer/join_taxonomy.py` #"target_field": join-column resolution
  (`target_field.attname` / `target_field_attname` fallback for FK join
  planning). Answers "which column to join on", not "which column a
  GlobalID identifies". Different contract.
- `permissions.py` #"field.target_field.attname": cascade re-projection to
  `.values(target column)` for the membership subquery (binds the FK's
  actual target column incl. `to_field`). Answers membership-values shape,
  not GlobalID predicate qualification. Different contract.
- `optimizer/field_meta.py` #"target_field": `target_field_name` /
  `target_field_attname` metadata + `target_pk_name` comparison for FK-id
  elision eligibility. Answers projection/elision metadata, not filter
  predicate construction. Different contract.
- `optimizer/lateral_fetch.py` #"spec.parent_link_field.target_field":
  parent-link target type check (`_ARRAY_BINDABLE_PARENT_FIELD_TYPES`) +
  join-column rendering for lateral SQL. Answers lateral execution
  planning, not GlobalID decoding. Different contract.
- [finalizer][finalizer] `_audit_globalid_filter_strategies`: opened
  (1914-1959) — encode-only-strategy audit via
  `resolve_globalid_target_definition`; zero `to_field`/`target_field`/`__pk`
  hits. Different contract (schema-build rejection of undecodable
  targets).
- Write-side `relay.py::_resolve_real_pk`: decode pipeline's own seam per
  the cited decode rule; not a filter-predicate derivation. Excluded with
  reason.
- Result: zero readers re-deriving non-pk-`to_field` → `__pk` without the
  marker. W1 exclusions stand.

### No-gate reasoning — judged CORRECT (P2 standard)

- P2 negative control (behavior-identical hand copy bypassing the owner →
  10/10 behavior oracles still pass) proves sharing is pinnable only by a
  bespoke AST/name-cardinality shape — forbidden per [dry][dry]
  ("never a bespoke existence test per helper"). Gate DEFERRED with proved
  reason, not omitted. Durable pin is existing prose at the owner (attr
  block + `_marked_pk_field_name` "single home" docstring), already
  present → no projection edit owed. Revisit trigger stated (third reader,
  per-method copy, new pk-qualified family). Sets-side 8/8 + 1 focused
  shared-tree `--no-cov` green are behavior proofs, not gates; a green
  unmutated suite discharges no failability proof for a finding proposing
  no gate. `## Pending execution: None` correct; sharded/Postgres
  `inapplicable by construction` judged sound (predicate-column choice by
  field identity; `__pk` traversal vendor-neutral; no alias/`using`/dialect
  branch).

### Freshness re-hashed (Worker 2, `git hash-object` / `git rev-parse`)

- `filters/base.py` working `ba52351c` == `HEAD:filters/base.py`
  `ba52351c` == `ITEM_BASELINE:filters/base.py` `ba52351c` — clean,
  matches artifact.
- `filters/sets.py` working `4a40e51b` == `ITEM_BASELINE:filters/sets.py`
  `4a40e51b` vs `HEAD:filters/sets.py` `4ab65a26` — external +22
  declared-bag hunk, predates baseline, item-scoped diff
  (`git diff 407552ad -- filters/base.py filters/sets.py`) EMPTY —
  confirmed; untouched by this item.
- `tests/filters/test_base.py` working `04da73cd` == HEAD `04da73cd` —
  clean, matches artifact.
- `tests/filters/test_sets.py` working `a624a78d` vs HEAD `85d31c4b` —
  external +34 companion hunk (declared-bag test at 5143+), marker rows at
  715-1010/1320-1380 untouched — matches artifact.
- `tests/_relation_fixtures.py` `1846a0093` == HEAD — matches artifact.
- `HEAD` `bfaee91d`; `ITEM_BASELINE`
  `407552ad8cb17dafcae3dba30e63fc88d3502787` present (rev-parses);
  `09c24baf` rev-parses as the current stash (WIP) object — consistent
  with concurrent dirt elsewhere, not a branch move (stayed on branch, no
  switch).
- Searched population: whole package trio grep; excluded modules opened
  (finalizer, permissions, field_meta, join_taxonomy, lateral_fetch).
  Fingerprint change in none of the family inputs → finding fresh.

### `## Pending execution` + AGENTS.md prose — judged CORRECT

- `## Pending execution: None`: every proof listed is
  `execution-verified` (workspace `__file__` + DB `NAME` recorded;
  shared-tree run was the single authorized focused test). No
  `execution-deferred` entry remains; no `gate:` witness owed for a
  gateless finding. Correct.
- AGENTS.md prose on empty diff: `## Implementation (Worker 1)` claims
  item-scoped diff vs `ITEM_BASELINE` on both family paths is empty —
  CONFIRMED (`git diff <baseline> -- filters/base.py filters/sets.py`
  prints nothing; the `sets.py` +22 predates the baseline). Ledger check
  (no rows on either family path) consistent; no STOP arose (no dirty
  family path edited). Concurrent dirt elsewhere left alone — correct per
  dirty≠untouchable + out-of-scope rules.
- Citations use `path::Symbol` + #"substring" with link definitions; no
  raw `path:NN` in standing sections; no process provenance in production
  (artifact-only change); test tier correct (`tests/` package-side oracles
  with inline `Model.objects.create` / `relation_fixture_tables` — library
  app has no `services.py`; missing fakeshop `to_field` fixture correctly
  NOT added in-item per test-tier rule, released as noted-not-filed).
- Ruff: touched path is `.md` only (outside ruff corpus);
  `scripts/check_trailing_commas.py` scaffold holds (link-definitions
  block present, canonical groups intact).

### Defects

None (Worker 2). The two considered-and-released items (declared-filter
silent-wrong-column; missing fakeshop `to_field` fixture) were correctly
released with reason, not dropped — see C1 judgment above. No new defect
found while tracing.

### Verdict

`Status: verified`. CONFIRMED single-owned, zero second definitions, zero
production edits, durable home already at owner, no pending execution.
Plan rows below exact.

### Plan rows (exact)

- Tick Family `globalid-relation-pk-marker`
  (`docs/dry/dry-0_0_15.md` responsibility row + `## Families` list) as
  **verified**, Run `0.0.15 2026-09-19-1`, CONFIRMED single-owned, zero
  production edits, no pending execution.
- No `## Owned changes` row (no tracked edit landed).
- Home nothing (zero defects, zero Worker-2 defects).
- Scratch paths (removal is Worker 0's, after `verified`, by explicit
  path): `/var/folders/7w/4f56z27561b1v4r5t_qbhrvh0000gn/T/opencode/dry-ws/globalid-relation-pk-marker`.
  Preserve all concurrent dirt; do not commit.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md

<!-- docs/ -->
[decode-rule]: dry-rule-typed-globalid-decode.md
[dry]: DRY.md
[dry-plan]: dry-0_0_15.md
[file-base]: dry-file-filters__base.md
[file-sets]: dry-file-filters__sets.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->
[fixtures]: ../../tests/_relation_fixtures.py
[test-base]: ../../tests/filters/test_base.py
[test-sets]: ../../tests/filters/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Run-8 scoped re-trace (Worker 1, REOPENED item s19)

The 2026-09-19 artifact above (verified, accepted under the 2026-09-22
ruling) is PRIOR EVIDENCE ONLY. Zero-edit scoped re-trace at HEAD bytes
per the s19 dispatch: scope the drift delta, CONFIRM or REVISE every
prior family finding, re-derive the marker rule plus member/reader census,
adjudicate the fired revisit trigger, judge the carried s7/s9
filters-side evidence from the family side, attribute dirt by content,
fingerprint all three states. No pytest (dispatch: read-only probes
only); every proof below is static-reviewed at HEAD bytes (`git show
HEAD:`, `git grep HEAD`) plus one read-only AST census probe in the
disposable copy (`/tmp/s19_probe.py`, no imports, no writes). This
section is pure ASCII.

### Scope and fingerprints

HEAD `83998e08d48c911199527ed0411ab8041805c8b5` at dispatch, unmoved at
close. `ITEM_BASELINE` `8384652a86496563c755ebe67f557eff1c72a76c`
rev-parses (stash object at dispatch). Drift base
`0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`.

| Path | work == BASE | HEAD | DRIFT | State |
|---|---|---|---|---|
| `filters/base.py` | `fc1cf61f` | `e2e683a8` | `ba52351c` | dirty, predates baseline |
| `filters/sets.py` | `ec278851` | `3d307402` | `993e887a` | dirty, predates baseline |
| `tests/filters/test_base.py` | `b7ae27b6` | `2c507b75` | `e1cfc066` | dirty, predates baseline |
| `tests/filters/test_sets.py` | `fc21a7a8` | `19d508bd` | `a5dc67c0` | dirty, predates baseline |
| `tests/_relation_fixtures.py` | `7b344afb` | `7b344afb` | `7b344afb` | clean, all three match |
| `filters/inputs.py` (examined nonmember) | `c933bb5d` | `2c853e24` | n/a | dirty, predates baseline |

Full ids: base work/BASE `fc1cf61f3536c4f6ed916ad544c8f12c6afeeb5f`,
HEAD `e2e683a8fabc5fac318ba2fa78abdf92c872973c`, DRIFT
`ba52351c284425336262ae6c2b82b262f6586fc0`; sets work/BASE
`ec278851996aff2835677b4ca77197da2a1c2728`, HEAD
`3d307402a8c29860957a23bd99a821e094c606a6`, DRIFT
`993e887a700112ea431f89b9ec49ab6f3ff25f55`; test_base work/BASE
`b7ae27b6467f73784df9c12f16c646fd2681e106`, HEAD
`2c507b750be9752a11ec7cf9eba8d760f77e27e9`, DRIFT
`e1cfc06669cc3b3dae8eb4d7a04ae4f97672008e`; test_sets work/BASE
`fc21a7a89d0a9f3f8764c0581125a6319d5254a6`, HEAD
`19d508bddb56f21c10649491fd277a3fe7650a7b`, DRIFT
`a5dc67c06aed5bc23e37662a102dde9c80380bdf`; fixtures
`7b344afb7455b6b89573be38cf6e07e68bef20f2` everywhere.

Item-scoped diff vs `ITEM_BASELINE` on every family path above is EMPTY
(work == BASE on all five; `git diff 8384652a --` prints nothing).
Probe: workspace run `dry-20260930T222406-2e6162`, copy fresh, shared
unmoved since sync, 12/12 checks green (counts below corroborated on
copy bytes, which equal worktree bytes; HEAD bytes verified by the
parallel `git grep HEAD` census with identical counts).

### Drift delta (base `0c0537e2` .. HEAD `83998e08` on members)

`git log --oneline 0c0537e2..83998e08 -- filters/base.py filters/sets.py`
is exactly the 8 dispatched commits. Behavior-bearing (2):

- `bbe54687` "filter a relation key on a non-Relay target by its raw
  primary key": adds `RelationPkFilter` / `RelationPkMultipleFilter`
  (raw-pk siblings carrying the SAME flag, reading via the SAME home),
  the `_RELATION_IDENTITY_FILTER_CLASSES` 4-tuple + 2 family profiles +
  registry rows in sets.py, rewrites `filter_for_lookup` (every
  framework-owned relation key converts; GlobalID iff Relay target else
  raw-pk; exhaustive exact/in/isnull/other) and the `filter_for_field`
  relation branch (4-tuple gate, `type(default)` rebuild, renamed local
  `relay_replacement` -> `identity_replacement`, marker lines
  preserved), adds `relation_identity_column` +
  `_relation_identity_column_for` + `_coerce_relation_identity`, and
  updates the attr-block comment (raw-pk sentence). This commit FIRED
  the revisit trigger (new pk-qualified filter family + new flag
  readers); adjudicated below.
- `57131b99` "type a declared ModelChoiceFilter from the column its form
  cleans": refactors `relation_identity_column` onto the shared
  `_model_identity_column`, adds `model_choice_identity_column`, adds
  the ModelChoice ladder entry in `filters/inputs.py`. Zero marker
  bytes touched (no trio name in the diff; no sets.py hunk). Declared
  ModelChoice stays consumer-owned and unmarked by design (commit prose:
  "The filter stays the consumer's") -- the Matrix-6 declared-leaf
  separation extends to a new declared shape.

Typing-only (6), each verified trio-safe: `999a1aab` (zero trio-name
hits in the member diffs), `b20277fe` (predicate signature `Any` ->
`object` only; body untouched), `849f67bc` (zero trio-name hits;
`@override` adds), `dfbea72b` (trio lines context-only; `cast`
removals around the GlobalID readers), `e37448e5` (sets.py 1-line
coverage exclude), `fef11e64` (zero trio-name hits). Net trio-body
verdict DRIFT -> HEAD: slot assign byte-identical, predicate body
byte-identical (annotation only), home def + body byte-identical, both
GlobalID readers body-identical modulo casts/`@override`, stamp
predicate-call + `setattr` lines preserved inside the rewritten branch.

### Re-derived rule and census at HEAD

Contract (unchanged): a forward FK/O2O bound on a non-pk `to_field`
stores/joins on that column while the identity value (a Relay GlobalID
or, since `bbe54687`, a raw target pk) carries the target pk, so the
predicate compiles against `f"{live field_name}__pk"`. Owner trio
confirmed in [filters-base][filters-base]: slot `:280` (literal
`"_dst_globalid_relation_pk"`, sole literal occurrence package-wide),
predicate `:283` (concrete + single-valued-forward guards, then
`target_field is not target_pk` by identity), home `:315` (sole
`getattr` read at `:327`, sole `__pk` f-string at `:330`).

- Write (stamp): still the single site
  [filters-sets][filters-sets]`::FilterSet.filter_for_field` `:1789-1790`
  (`if _relation_uses_non_pk_to_field(field): setattr(...)`), now
  covering both primitive pairs through the 4-tuple gate (`:217`,
  def + 1 consumer) and the `type(default)` rebuild. `filter_for_lookup`
  still returns class+params pairs only (12 pair-returns + 2 raises at
  HEAD; AST check: no slot/`setattr`/predicate reference in its body),
  so no second stamp site can exist there by construction.
- Read: home + FOUR callers, one call each: `GlobalIDFilter.filter`
  `:953`, `GlobalIDMultipleChoiceFilter.filter` `:1096`,
  `RelationPkFilter.filter` `:1237` (passes the home value straight
  into `_apply_lookup_predicate`), `RelationPkMultipleFilter.filter`
  `:1275-1276` (`_marked_pk_field_name(self) or self.field_name`, then
  ONE `{field__in: kept}` via `_apply_lookups`). No direct
  `getattr(flag)` read beside the home anywhere in production (attr-name
  hits: assign + home `getattr` + `setattr` + import + prose only).
- Lifetime (unchanged, inherited by the new readers): stamped once at
  generation, rides the instance `__dict__` through `deepcopy`
  (`:1170`) + `field_name` rebase (`:1171`, class-agnostic in
  `_expand_related_filter`), read per request at filter time,
  invalidated with the filterset lifecycle. The new readers share it by
  construction (same slot, same home, same expansion path).

Enumeration (run-8; prior rows 1-4/7-10 keep their numbers):

| # | Site | Role | Disp |
|---|---|---|---|
| 1 | slot assign (1) | definition | CONFIRM |
| 2 | stamp predicate def (1) | definition | CONFIRM (annotation-only drift) |
| 3 | read/derive home def (1) | definition | CONFIRM |
| 4 | `filter_for_field` (1 `setattr`, 1 predicate call) | sole stamper | REVISE shape (4-tuple gate, `type(default)` rebuild) |
| 5 | `GlobalIDFilter.filter` (1 home call) | reader | CONFIRM |
| 6 | `GlobalIDMultipleChoiceFilter.filter` (1 home call; non-`in` keeps the pre-existing upstream-OR arm at `:1084`) | reader | CONFIRM |
| 5b | `RelationPkFilter.filter` (1 home call) NEW | reader | NEW (trigger discharge) |
| 6b | `RelationPkMultipleFilter.filter` (1 home call) NEW | reader | NEW (trigger discharge) |
| 7 | finalizer `_audit_globalid_filter_strategies` (zero `to_field`/`target_field`/`__pk` hits at HEAD) | excluded | CONFIRM |
| 8 | `permissions.py` (`:530` membership re-projection) + optimizer `target_field` readers (join planning / metadata) + write-side `relay.py::_resolve_real_pk` (`:246`) | excluded | CONFIRM (each re-opened; contracts unchanged) |
| 9 | oracles: prior pins stand + `test_relation_pk_filters_generated_for_non_pk_to_field_match_by_target_pk` (`:1637`: isinstance selection + `is True` stamping on both leaves at `:1655-1656` + literal row-set behavior pins) | oracles | REVISE (extended) |
| 10 | projections: attr block (raw-pk sentence ADDED, read-clause still names 2), home docstring (still names 2 / "two siblings"), stamp comment (raw-pk sentence ADDED), 2 new RelationPk docstrings (verified against bodies) | projections | REVISE (2 stale censuses, already in s7 D1) |
| 11 | `relation_identity_column` `:1100` + `_model_identity_column` `:1115` + `model_choice_identity_column` `:1131` + runtime chain `:1153`/`:1169` (s7 F-9, already rowed) | excluded: answers which column types/coerces the value, never derives `__pk`, never reads the flag | NEW separation row |
| 12 | declared ModelChoice pair (consumer-owned, unmarked; `57131b99`) | excluded: byte-for-byte consumer predicate | NEW separation row |

Matrix (run-8): (1) cross-flavor mirroring -- CONFIRM: `orders/base.py`
still zero GlobalID hits; write-side `_resolve_real_pk` still the
decode pipeline's own seam (prose + callers re-read); cascade
`target_field` still membership-values (`:485-535` re-read, s3 rewrite
changes wording, not the question); optimizer reads still join
planning/metadata; finalizer still zero-hit. New adjacent rules (F-9
chain, ModelChoice typing, always-`__in` R9) each carry a contract
difference (rows 11-12, R9 below). (2) sync/async -- CONFIRM
inapplicable: all four `filter` bodies sync (AST-verified), no await
boundary. (3) derived knowledge -- CONFIRM: `__pk` path still derived
once from the live name (sole code `__pk` at `:330`; the one other
production `__pk` hit is an unrelated `nested_planner.py` comment);
identity compare still by object identity. (4) round-trip pairs --
CONFIRM: stamp/read still share constant + predicate + home by name
across the module edge, now with 4 readers. (5) contracts in another
medium -- REVISE: new oracle classified (row 9: row sets are
independent; the `is True` stamping assertions import the owner
constant, so pins); projections verified except the 2 stale reader
censuses (row 10, s7 D1). (6) enforcement by omission -- REVISE and
re-enumerate: own-PK (no marker), forward FK/O2O to pk (no marker),
forward FK/O2O to non-pk `to_field` exact+`in` (marker, now both
primitive pairs), M2M/reverse (no marker; predicate unchanged so the
prior P1 execution shape carries by construction), `isnull` (upstream
Boolean, never reads the marker; the e2e pin exists at HEAD), declared
/ override-generated incl. the NEW declared ModelChoice shape
(unstamped by design, consumer owns the predicate). No contract source
extends the marker to declared leaves, so no defect.

Challenges (run-8): C1 new non-pk shape -> 1 (stamp predicate; the
silent-wrong shape stays unreachable on framework paths: pairs-only
`filter_for_lookup` + single stamp site covering both pairs; the
reachable silent shape is a hand-built declared filter, consumer-owned
as before). C2 rename/rebase -> 0 (identity compare + live-name
derivation + class-agnostic expansion, all unchanged). C3 slot rename
-> 1 (constant); the predicted third consumer ARRIVED twice and moved 0
existing definitions (two additive home calls) -- the C3 prediction is
confirmed by the drift itself. Restated trigger: a fifth reader, a
direct `getattr(flag)` beside the home, a second stamp site, a marker
read in the write pipeline, a `target_field` read deciding an identity
column outside the home, or a framework-derived declared predicate.

### Trigger adjudication (fired revisit trigger)

Prior trigger ("a third flag reader, a per-method copy, or a new
pk-qualified filter family") FIRED on all reader/family legs and is
DISCHARGED by design: the new pk-qualified filter family is the
RelationPk pair, and both new readers compose the owner by name (same
slot, same predicate, same home, same stamp site; zero new definitions
of stamp, flag, or derivation). The `RelationPkMultipleFilter`
explicit `__in` at `:1276` is NOT a marker derivation: it is the
cardinality-shape rule (exact-on-many means related-to-any, s7 R9),
while the `__pk` qualification still comes from the home call on the
line above. No per-method copy exists. No new plan family row is owed:
the pair are consumers inside THIS family (s7 homed them to
F-7/F-b/F-c/F-9, no new rule), and the genuinely new adjacent rules
(F-9, F-10) are already rowed by s7. Decline with evidence recorded.

### Carried s7/s9 evidence judged from the family side

- s7 F-7 (CONFIRM rule, REVISE census): AGREE on every count from
  independent HEAD bytes (1 slot, 1 predicate def + 1 call, 1 home def
  + 1 internal read, 1 stamp, 2->4 home callers, 2 production files).
  s7 W2 endorsed; carried as recorded.
- s7 F-9 `relation-identity-column` (already rowed): distinct rule from
  the family side -- it resolves which column types/coerces an identity
  value (input scalar + runtime coercion), never derives a `__pk`
  predicate path and never reads the flag (row 11). Separation
  endorsed; no row from this item.
- s7 F-10 `bound-filter-model-field-walk` (already rowed): distinct
  rule (model-field resolution walk); no flag read. No row from this
  item. s7 W2 confirmed count-2; the family side adds nothing.
- s7 R9 (always-`__in` vs lookup-honoring): ENDORSED from the family
  side -- the multi `__in` spelling is the membership-shape contract,
  not a second marker derivation; trigger (a shared multi-predicate
  policy owner) sound. R10-R13: out of family scope; stand as filed
  (each disputed and held by s7 W2).
- s7 D1 (five stale docstring censuses, W2-verified, endorsed for
  closeout homing): the two marker miscounts (attr-block read-clause,
  home "two siblings") are already filed there. DEDUPE: no new defect
  from this item; the closeout repair is authored against HEAD bytes.
- s9 marker reuse row (CONFIRM rule, REVISE shape + census): AGREE --
  stamp still single-sited (`:1790`), predicate still single-called
  (`:1789`), 0 reads in sets.py, def + 4 consumers in base, tuple def +
  1 consumer, both pairs covered via `type(default)`. s9 W2
  corroborated ("consistent with s7 F-7 on all three claims"). s9 D1
  (provenance GlobalID-only wordings) is sets-side projections, out of
  family scope.

### Worktree dirt attribution (by content; all concurrent, zero owned)

`## Owned changes` names no family path. Work == BASE on all five
fingerprinted files, so every work-vs-HEAD hunk predates the item.

- `filters/base.py` (16 hunks): exactly ONE touches family bytes --
  the predicate's `target_pk` line reads `_meta` via
  `truth.static_attr` (concurrent truth-migration; `utils/truth.py`
  itself is untracked concurrent work). The other 15 are the same
  population s7 attributed: `truth.*` swaps, `_safe_*` import removal,
  containment-narrowing (`_materialize_list_shaped_values`,
  Array/List/Integer filters), docstring-only. Census preserved (probe
  counts on dirt bytes match HEAD counts exactly).
- `filters/sets.py` (33 hunks): ZERO touch marker bytes (no trio name
  in the whole diff; stamp region `:1749-1791` byte-identical to HEAD).
  Content: imports, CSV profiles, metaclass, `get_fields`/normalize,
  generation-conditional truth-migration -- all concurrent.
- Oracles: trio hits 42 worktree == 42 HEAD across the same 2 files;
  every marker row (`:521-667`, `:1301-1327`, `:1637-1656` in test_base;
  `:729-1010`, `:1374-1401` in test_sets) untouched. One adjacent pin,
  `test_r6_relation_isnull_filters_correctly_no_500`, is deleted in the
  worktree by concurrent churn; it exists at HEAD, and this finding
  traces HEAD bytes, so Matrix-6 stands.
- Nothing edited, nothing reverted; dirt elsewhere in the tree ignored
  as out of scope.

### Defects (run-8)

None filed. Considered and released with reason (not dropped): (a) a
hand-built `RelationPkFilter` on a non-pk-`to_field` relation without
the flag filters the raw column silently -- the same accepted-risk
shape as the declared-GlobalID case (byte-for-byte consumer ownership
is the contract; RelationPk is generated-only per the
`filters/__init__.py` precedent, so the reachable shape needs a
deliberate hand-build); restated trigger above, not a defect. (b) No
RelationPk-specific expansion-rebase oracle -- the rebase mechanism
(deepcopy + `field_name` rewrite) is class-agnostic and the home
derives from the live name for every reader identically; no contract
source requires a per-class pin, so per axis 6 this is not an
enforcement gap. The pre-existing s7-D1 closeout homing already covers
the two stale marker censuses.

### Pending execution (run-8)

None. Every proof is static-reviewed at HEAD bytes (bodies, counts,
`git grep HEAD` populations, AST census run
`dry-20260930T222406-2e6162`); no ordering, transactional, or async
behavior is decided by this rule, so no execution-deferred entry
exists, and the dispatch authorizes no pytest. The structural-gate
deferral carries under the P2 standard: sharing is still pinnable only
by a bespoke AST/name-cardinality shape (forbidden per [dry][dry]), and
the durable pin remains the owner prose (attr block + home docstring),
whose reader censuses the s7-D1 closeout repair updates. Sharded and
Postgres cells inapplicable by construction (unchanged reason: the
marker decides a predicate column by field identity -- no alias/`using`
decision, no dialect branch, `__pk` traversal vendor-neutral).

### Judgment (run-8)

F-1 `globalid-relation-pk-marker` -- REVISE counts, CONFIRMED
single-owned: one slot, one stamp predicate, one read/derive home, one
stamp site covering both primitive pairs, four readers composing the
home by name, zero parallel derivations package-wide. The fired trigger
discharged by design (C3's prediction confirmed: two additive readers,
zero existing definitions moved). Separations carry triggers; carried
s7/s9 evidence endorsed from the family side with no new rows; the two
stale projections dedupe to the already-homed s7 D1. Zero production
edits; artifact only.

### Item-scoped diff state

HEAD unmoved at close (`83998e08`); work == `ITEM_BASELINE` on all
member and oracle paths (item-scoped diff empty). This item touched no
tracked file: the sole write is this artifact (untracked `??`).
Probes live in `/tmp/s19_probe.py` (read-only AST/grep census in the
disposable copy). No commit.

Worker 0 rows (exact): tick Family `globalid-relation-pk-marker`
([dry-plan][dry-plan] responsibility row + families list) as verified,
Run 0.0.15 2026-09-30-8, REOPENED run 8 re-trace s19 (F-1 REVISE
counts 2->4 readers + widened stamp gate, CONFIRM set, trigger
discharged by design, zero-edit, no pending execution); no
`## Owned changes` row (no tracked edit landed); home nothing (zero
new defects; the two stale marker censuses already ride the s7-D1
closeout homing).

## Run-8 verification (Worker 2)

Expectation-first re-trace at HEAD bytes with own instruments; every W1
figure below was re-derived, not trusted. Read-only probes only (`git
show HEAD:`, `git grep HEAD` with a directory pathspec, one AST census
probe of my own on HEAD bytes plus the same probe on dirt bytes, all
executions via `workspace.py run dry/globalid-retrace-s19/verify`).
No pytest (not authorized), no tracked edit besides this artifact.
This section is pure ASCII.

### Fingerprints (re-hashed; all three states)

HEAD `83998e08d48c911199527ed0411ab8041805c8b5` unmoved at close.
`ITEM_BASELINE` `8384652a86496563c755ebe67f557eff1c72a76c`
rev-parses. Drift base `0c0537e2dd94a2f5faf3468ad7ee9aa26b3acf62`
rev-parses. Work == BASE on all six fingerprinted paths (full ids
reproduce W1's table byte for byte); HEAD blobs `e2e683a8` /
`3d307402` / `2c507b75` / `19d508bd`; DRIFT blobs `ba52351c` /
`993e887a` / `e1cfc066` / `a5dc67c0`; fixtures `7b344afb` all three
states. (`filters/inputs.py` DRIFT rev-parses to `82b52d97`; W1's
"n/a" is unrecorded, not absent -- record note N2, moves nothing.)
Item-scoped diff vs baseline on every family path: 0 bytes
(re-run). The tree's only baseline diff is the plan's own +42
dispatch record (Worker-0's rows, out of scope).

### Drift delta (re-scoped with own instruments)

`git log 0c0537e2..83998e08` on the members is exactly the 8
commits. Trio-name hits in the member diffs, counted myself:
`bbe54687` 9, `b20277fe` 5, `dfbea72b` 2, the other five 0.
`bbe54687` verified hunk by hunk: RelationPk pair (same flag,
same home), 4-tuple def + consumer, `type(default)` rebuild,
`filter_for_lookup` rewrite, identity chain, attr-comment raw-pk
sentence; stamp predicate-call + `setattr` lines preserved
modulo the local rename. `57131b99`: no sets.py hunk, zero trio
bytes, ModelChoice ladder entry, "stays the consumer's" prose.
Typing six trio-safe on my reading: `b20277fe` signature-only
(`Any` -> `object`) with trio lines context; `dfbea72b`
context-only with cast removals around the readers; the rest
zero-hit. Net DRIFT -> HEAD trio bodies, diffed myself: slot
assign byte-identical, predicate body byte-identical
(annotation only), home def + body byte-identical, both
GlobalID readers body-identical modulo signature + `@override`
(the one `cast(` add in the file delta sits in `RelatedFilter`,
outside the family).

### Own census at HEAD bytes (probe + grep)

Slot 1 assign (`:280`, sole literal package-wide); predicate 1
def (`:283`) + 1 production call (sets `:1789`); home 1 def
(`:315`) + sole `getattr` read (`:327`) + sole code `__pk`
(`:330`, every other hit prose; the one non-member production
`__pk` hit is the unrelated `nested_planner.py` comment);
`setattr` exactly 1 (sets `:1790`); attr-name hits are assign +
home `getattr` + `setattr` + import + prose only, in exactly
`filters/base.py` + `filters/sets.py` (package-wide trio grep,
directory pathspec). Home callers exactly 4, one call each:
`GlobalIDFilter.filter` `:953`,
`GlobalIDMultipleChoiceFilter.filter` `:1096`,
`RelationPkFilter.filter` `:1237` (home value straight into
`_apply_lookup_predicate`, whose `None` arm keeps the raw
predicate -- the established multi-reader shape),
`RelationPkMultipleFilter.filter` `:1275` (`or self.field_name`
fallback) + `:1276` single `{field__in: kept}` via
`_apply_lookups`. `filter_for_lookup`: 12 pair-returns + 2
raises, zero trio refs (AST). All four `filter` bodies sync,
zero `await` (AST). 4-tuple AnnAssign `:217` + 1 consumer
(`:1749` gate); `type(default)` rebuild `:1772`; expansion
`deepcopy` `:1170` + rebase `:1171`, class-agnostic (no class
check in the body).

### Per-row judgments (own evidence above)

Rows 1/2/3 CONFIRM (annotation-only drift on 2 noted). Row 4
REVISE shape CONFIRM (gate + rebuild + rename + raw-pk comment
sentence, all read). Rows 5/6 CONFIRM (the `:1084` non-`in`
upstream arm verified at its exact line). Rows 5b/6b NEW
CONFIRM (bodies read; both compose the home by name). Row 7
CONFIRM (finalizer zero `to_field`/`target_field`/`__pk` hits,
grep exit 1). Row 8 CONFIRM (permissions `:530` membership
re-projection + `:50`/`:493` prose, optimizer join/metadata
reads, relay `:246` write seam -- each re-opened; trio grep
already bounds production to the two member files). Row 9
REVISE CONFIRM (`:1637` test read: isinstance selection +
`is True` stamping on both leaves at `:1655-1656` importing
the owner constant at `:42`, so pins; literal row sets
independent). Row 10 REVISE CONFIRM (raw-pk sentences added;
both stale reader censuses read at HEAD bytes -- attr-block
read-clause, home "two siblings"; 2 new RelationPk docstrings
verified against their bodies). Row 11 NEW separation CONFIRM
(defs `:1100`/`:1115`/`:1131`/`:1153`/`:1169` read; no flag
read -- home calls only at the 4 filter sites; no `__pk`
derivation -- sole code `__pk` at `:330`). Row 12 NEW
separation CONFIRM (declared ModelChoice unmarked by design;
no generation path stamps a declared leaf).

Matrix: (1) CONFIRM (orders zero GlobalID hits; cascade still
membership-values under the s3 rewrite; optimizer still
join/metadata; adjacent F-9/ModelChoice/R9 differences
carried). (2) CONFIRM (4 sync bodies, AST). (3) CONFIRM
(derive-once from the live name; identity compare).
(4) CONFIRM (stamp/read share constant + predicate + home by
name, now 4 readers). (5) REVISE CONFIRM (oracle
classification + 2 stale censuses to s7 D1). (6) REVISE
CONFIRM (re-enumerated; M2M/reverse carries by construction
-- predicate and no-marker path unchanged; isnull e2e pin
exists at HEAD test_sets `:8541`, read; declared incl.
ModelChoice unmarked by design). C1 -> 1 / C2 -> 0 / C3 ->
1+0 CONFIRM (silent shape unreachable on framework paths:
pairs-only lookup + single stamp covering both pairs via
`type(default)`; C3's prediction confirmed by the drift
itself: two additive home calls, zero existing definitions
moved -- byte-identity above).

### Trigger adjudication (fired; DISCHARGED by design -- agree)

Derived independently: the new pk-qualified family is the
RelationPk pair and both new readers compose the owner by
name (same slot, same predicate, same home, same stamp;
zero new stamp/flag/derivation definitions). The `:1276`
explicit `__in` is NOT a marker derivation on my reading:
the `__pk` qualification is the home's return value consumed
at `:1275`, while the `__in` suffix is the cardinality-shape
decision (the method's own docstring: exact-on-many means
related-to-any) -- s7 R9's always-`__in` vs lookup-honoring
contract, which I endorse from the family side for the same
reason. No per-method copy (sole `getattr` at `:327`). No new
plan family owed: the pair are consumers inside THIS family
(s7 homed them to F-7/F-b/F-c/F-9, verified in the s7
artifact), and F-9/F-10 are already rowed there. The restated
trigger (fifth reader, direct `getattr(flag)`, second stamp,
write-pipeline read, identity-column read outside the home,
framework-derived declared predicate) covers every leg.

### Carried s7/s9 evidence (judged from the family side -- agree)

s7 F-7: my HEAD counts are identical to s7 W1/W2's on every
figure (1 read, 1 stamp, 1 call, 2->4 callers at the same
four lines, 2 production files); carried as recorded. s7
F-9/F-10: distinct rules on my derivation (column resolution
/ model-field walk; neither reads the flag); no row from
this item. s7 R9: endorsed (above); R10-R13 out of scope,
each disputed and held by s7 W2 (verified). s7 D1: both
marker miscounts verified at HEAD bytes and already filed
there (W2-verified, closeout homing endorsed) -- DEDUPE,
no new defect. s9 marker row: stamp `:1790` / call `:1789`
/ 0 reads / def + 4 consumers / tuple + 1 consumer all
reproduce on my instruments; the "consistent with s7 F-7"
corroboration quote is accurate. s9 D1 is sets-side
projections, out of family scope.

### Dirt attribution (by content; all concurrent, zero owned)

`## Owned changes` names no family path (ledger read). Base
16 hunks (reproduces); sets 32 hunks, not 33 (record note
N1 -- same bytes, fingerprints identical, so a W1 miscount;
moves nothing). Exactly ONE base hunk touches family bytes:
the predicate's `target_pk` line reads `_meta` via
`truth.static_attr` (concurrent truth-migration;
`utils/truth.py` is untracked `??`). It moves nothing: the
finding traces HEAD bytes, the `_meta` read is equivalent
in every feasible shape, and census is preserved -- my
probe on dirt bytes reproduces every HEAD count exactly
(1/1/1 defs, 4 callers, 1 read, 1 write, 12+2 pairs-only,
all sync, sole code `__pk`). Sets diff: zero trio names in
the whole diff; the `:1747-1791` stamp block diffs
byte-identical HEAD vs worktree. Oracles: trio hits 30+12
== 42 both revisions across exactly the 2 test files
(tests+examples-wide grep: no third file); no worktree
hunk overlaps any marker row in either file; the adjacent
r6 pin exists at HEAD `:8541` and is deleted in the
worktree by concurrent churn -- Matrix-6 traces HEAD bytes,
so it stands. Nothing edited, nothing reverted.

### Defects (run-8; Worker 2)

None. Both releases judged sound on my derivation: (a) the
hand-built-RelationPk silent shape needs a deliberate
hand-build (generated-only verified: zero RelationPk hits
in `filters/__init__.py`, the IntegerIn/IntegerRange
precedent) and the byte-for-byte consumer-ownership
contract is the separation -- accepted risk with the
restated trigger, not a defect. (b) No per-class rebase
oracle is owed: the mechanism is class-agnostic (verified)
and every reader derives from the live name through the
same home (verified) -- no contract source requires a
per-class pin. The s7-D1 dedupe is correct (above).

### Pending execution

None. Every proof is static-reviewed at HEAD bytes; the
dispatch authorizes no pytest and no ordering /
transactional / async behavior is decided by this rule.
The structural-gate deferral carries under the P2
standard: the drift adds only additive home-call
consumers, so sharing is still pinnable only by a bespoke
shape, and the durable pin remains the owner prose whose
reader censuses ride the s7-D1 closeout repair. Sharded
and Postgres inapplicable by construction (no
alias/`using` decision and no dialect branch in any of
the four reader bodies -- verified).

### Record-precision notes (move no verdict)

N1: sets dirt hunks 32, not 33 (above). N2: inputs.py
DRIFT blob rev-parses (`82b52d97`); W1's "n/a" means
unrecorded. Neither touches any count, census, or
judgment.

### Verdict

`Status: verified`. F-1 `globalid-relation-pk-marker` --
REVISE counts, CONFIRMED single-owned: one slot, one stamp
predicate, one read/derive home, one stamp site covering
both primitive pairs, four readers composing the home by
name, zero parallel derivations package-wide. The fired
trigger discharged by design; carried s7/s9 evidence
endorsed with no new rows; the two stale projections
dedupe to the already-homed s7 D1. Zero production edits;
artifact only.

### Plan rows (exact)

- Tick Family `globalid-relation-pk-marker`
  (`docs/dry/dry-0_0_15.md` responsibility row + families
  list) as **verified**, Run `0.0.15 2026-09-30-8`,
  REOPENED run 8 re-trace s19 (F-1 REVISE counts 2->4
  readers + widened stamp gate, CONFIRM set, trigger
  discharged by design, zero-edit, no pending execution).
- No `## Owned changes` row (no tracked edit landed).
- Home nothing (zero new defects; the two stale marker
  censuses already ride the s7-D1 closeout homing).
- Record notes N1/N2 ride along (no resubmission; W1's
  figures stand corrected in this section).
