# DRY review: `prefetch-attach-column-projection`

Status: verified
Run: 0.0.15 2026-10-01-9

## System trace

Target: the prefetch attach-column projection — how the columns
Django needs loaded to attach prefetched rows are derived from the
join descriptor. Contract: the attach-complete `.only()` set
(connector, plus the `GenericRelation` morph half), the generic
child-column resolution primitive, the connector-first attach-key
order, and the never-raises posture. Varies per relation shape,
morph presence, projection-completeness policy, order.

Traced at HEAD bytes only (`5c3496e0`). All three indexed files
are worktree-dirty with concurrent truth-migration edits (diffed
vs `git show HEAD:`: `join_taxonomy.py` 190 lines,
`_safe_getattr`/`_safe_flag`/`_first_truthy` rewrites plus a new
`_child_link_is_virtual`; `walker.py` 24 lines, `truth.name` /
`truth.static_attr` / `truth.is_subclass`; `nested_planner.py` 12
lines, `truth` import plus the M2M advisory silence); none of it
is in `## Owned changes`, so it is concurrent work — NOT traced,
NOT edited, NOT reverted. Every line number below is a HEAD line.

Sites and roles, HEAD bytes:

- Definition
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (`:166`-`:181`): the property projecting
  `(parent_join_column?, content_type_column?)` in attach-key
  order, with the two input facts derived beside it
  (`_parent_join_column` `:205`, `_generic_child_attname`
  `:290`, the generic classify arms `:336`-`:351`). One
  definition of the attach set; no second exists package-wide
  (mechanism census below).
- Consumers composing by name, exactly two: both call
  `classify_relation_join(field).prefetch_attach_columns` and
  append each column via `append_unique`:
  - `optimizer/walker.py::_ensure_connector_only_fields`
    (`:1576`-`:1611`, call `:1602`): injects the set into
    `plan.only_fields` for every optimizer-built prefetch child
    plan (list prefetch, forced prefetch, nested-connection
    child builds all route through
    `_build_prefetch_child_queryset_from_base` `:1207`, which
    calls the writer at `:1236`). Log-and-skip on empty.
  - `optimizer/nested_planner.py::_project_scalar_only_window`
    (`:725`): injects the same set into the direct `.only()`
    for scalar-only windows, beside the pk leg (`:719`, Relay
    edge identity) and the order-column leg. Vacuous no-op on
    empty.
- Consumers of the two INPUT facts (not the set), each
  composing by name under its own contract:
  - `optimizer/nested_planner.py::_connector_only_field`
    (`:167`-`:183`): shim over `parent_join_column` only,
    historical name kept for direct test-double pins; zero
    production callers at HEAD (f21 O1 owns the existence
    question for closeout homing).
  - `optimizer/nested_planner.py::_advise_composite_index`
    (`:646`-`:651`): builds the morph-FIRST equality prefix
    for the index advisory — the deliberate counter-order the
    property docstring states (`:173`-`:174`).
- Input legs (verified f21/F1 dual contract, taken as input):
  both attach readers feed FieldMeta legs (walker field-map
  values, planner `field_map.get`); the fallback slots
  (`reverse_connector_attname`, `target_field_attname`) and
  parity slots (`content_type_field_name`,
  `object_id_field_name`) resolve kind + connector + morph,
  while partition/lateral/through degrade unread.
- Oracles (all spell expectations independently; none feeds a
  FieldMeta to the classifier): the generic attach pin
  `tests/optimizer/test_join_taxonomy.py:163`
  (`(object_id, content_type)` order-pinned); walker writer
  rows in `tests/optimizer/test_walker.py` (`:1982` M2M pk,
  `:2004` log-on-unknown, `:2022` shim pin, `:2272` reverse
  O2O, `:2292` generic morph, `:5057`/`:5074` G2 gates); the
  live `test_generic_relation_tags_resolve_over_http_with_optimizer`
  (`test_library_api.py:5454`), which pins generic list-prefetch
  behavior over HTTP (one tag-table query for two parents) —
  it exercises the walker writer's FieldMeta leg but does not
  pin the projected set. Scoped honestly: no live suite pins a
  generic WINDOWED connection, so the scalar-window attach loop
  has no live oracle; no claim here depends on one — both
  writers compose the one pinned property, and the set's
  content is pinned at the owner.
- Projections: the property + slot docstrings (incl. the
  attach-vs-advisory order contrast), both writer comments
  naming the shared owner, the shim docstring. Zero standing
  `docs/` prose names this rule (grep over `docs/*.md` +
  `docs/SPECS/*.md` for `prefetch_attach_columns` /
  `attach-complete` / `attach column`: 0 hits).

Established inputs (verified rows, used as triggers to check,
never re-litigated): f21 `window-partition-resolution`
(partition/connector facet, F1 questions, O1 shim existence,
standing D1 dual contract); f22 `lateral-join-shape` (shape/link
facet; its S5 converges to this item as same-owner sibling);
File `optimizer/join_taxonomy.py` F3 (family name adopted,
boundary re-derived fresh here) with R5/R8/R14/R15/R16;
walker F-W9/R5 (converged naming); f17 R11 + f20 R15 (excluded
against this row); the `relation-kind-taxonomy` R-A/R-B/R-C
tri-split rejections.

## Verification

### Matrix

1. Cross-flavor policy mirroring — SEARCHED. No flavor outside
   the optimizer derives attach columns. `mutations/resolvers.py`
   `:755` mentions `object_id` only as an illustrative scalar
   in the partial-input exclude carve-out (write-path
   validation vocabulary); `rest_framework/resolvers.py`
   `::_relation_object_identity` snapshots `(object, pk, alias)`
   for validator-tamper detection (write-path identity);
   `permissions.py`, `orders/inputs.py`, `forms/inputs.py`
   generic mentions are cascade/ordering/form exclusions. Each
   excluded on a contract difference (E13).
2. Sync/async twins — RULED OUT with reason. The property is a
   pure sync derivation over field metadata; both consumers run
   once at plan time (sync) under the G2 gate regardless of
   execution color. `async def.*connector|scalar_only|attach`
   over the package: 0 hits. No twin exists to drift.
3. Derived rather than repeated knowledge — SEARCHED. Every
   attach-adjacent derivation composes the descriptor by name:
   the advisory equality (`join.parent_join_column` /
   `join.content_type_column`), the lateral correlation name
   (`parent_link_field.attname`), the single-parent filter
   kwarg (same), the lateral/single-parent select-column
   mirrors (`deferred_loading_of` reflection of the applied
   projection). None re-derives WHICH columns attach needs.
4. Inverse / round-trip pairs — SEARCHED. The read half of the
   attach round-trip (building `rel_obj_attr` from row values)
   is Django-owned (`get_prefetch_querysets`); the package owns
   no inverse. Nearest package read-side is
   `types/resolvers.py::_prefetch_cache_name` (cache-KEY
   vocabulary, E7) — naming, not columns.
5. Contracts restated in another medium — SEARCHED. Production
   (1 definition + 2 writers + 2 fact consumers), oracles
   (package pins + one live behavioral pin, listed above),
   projections (docstrings/comments only; zero standing docs
   prose). A change to the set moves the property; writers,
   oracles, and prose follow or pin — counted once under
   Challenges.
6. Enforcement by omission — ENUMERATED. Optimizer-built
   prefetch child querysets: list prefetch, hint
   force-prefetch, nested-connection child builds (all via the
   base helper → the walker writer), scalar-only windows (the
   planner writer). Every member covered; consumer-supplied
   hint querysets are outside the family by the consumer-wins
   contract (`plans.py` `:1392` drops the optimizer's
   `only_fields` under a consumer projection; the
   `prefetch_obj` hint arm appends the consumer's Prefetch
   untouched). No gap.

### Enumeration

Family item: the population is the rule's mechanism, not a
file member list. Instruments, all at HEAD bytes:

- `git grep -n "prefetch_attach_columns" HEAD --
  django_strawberry_framework/`: 7 lines in 3 files (1
  definition `:166` + 1 docstring mention in
  `join_taxonomy.py`; 1 call `:1602` + 1 docstring mention in
  `walker.py`; 1 loop `:725` + 1 comment + 1 shim-docstring
  mention in `nested_planner.py`).
- `git grep -n "parent_join_column" HEAD --
  django_strawberry_framework/`: definition slot + derive +
  classify arms in `join_taxonomy.py`; the connector shim
  `:183` and the advisory reads `:646` in `nested_planner.py`;
  prose only elsewhere.
- `git grep -n "content_type_column" HEAD --
  django_strawberry_framework/`: definition slot + derive +
  classify arm in `join_taxonomy.py`; the advisory read
  `:650`-`:651` in `nested_planner.py`; prose only elsewhere.
- `git grep -n "rel_obj_attr|get_prefetch_querysets" HEAD --
  django_strawberry_framework/`: prose citations only (owner
  docstring, classifier comment, scalar-window comment,
  planner fetch-time note, plans window note) — the Django
  contract the property mirrors, never reimplemented.
- `git grep -n "\.only(" HEAD --
  django_strawberry_framework/optimizer/*.py` (code, not
  prose): exactly 3 writers — `plans.py:333` (plan apply),
  `nested_planner.py:729` (scalar window), `:763` (keyset
  cursor extension, E8). No fourth projection writer exists.
- `git grep -n "attname" HEAD` over `nested_fetch.py`,
  `selections.py`, `extension.py`, `hints.py`: 0 code hits in
  the first three relevant files (`predicates.py` has only
  the alias-namespace collector, E14).
- `git grep -n "classify_relation_join" HEAD --
  django_strawberry_framework/`: the def plus exactly 5
  production call sites in 3 modules (f21-censused; the two
  attach readers among them).

Every hit lands below: the definition in F1, the two
property readers and two fact readers as F1 consumers, the
remaining call sites in their verified families, the oracles
under their heading, the near-misses as S/E rows. Nothing
unassigned.

### Challenges

Each change posited with its authoritative-definition count
(consumers, oracles, projections listed, never counted):

- C1, a third attach column (e.g. a composite-FK second leg
  joins the attach key): the property gains the append — 1
  definition. Both writers loop the tuple and follow with
  zero edits; the advisory keeps its own prefix (R16).
- C2, morph-first attach order: the property swaps its two
  appends — 1 definition. Both writers follow; the advisory
  order is the deliberate counter-rule and does not move.
- C3, M2M attach needing through-table columns instead of
  the child pk: the `_parent_join_column` M2M arm — 1
  definition. The shim, the property, and both writers
  follow by construction.
- C4, generic morph resolution without `related_model`
  (e.g. resolving names from the GFK itself):
  `_generic_child_attname` — 1 definition, shared by the
  partition call and both attach calls.
- C5, reverse-FK connector reads a new slot: the
  `_parent_join_column` reverse arm — 1 definition. Same
  follow-through as C3.
- C6, the never-raises posture flips (a shape raises
  instead of degrading): the four contained per-site
  answers move as 1 module (standing R12: per-site
  policies, no shared guard to flip).

Consumers moving with each challenge (not counted): the two
writers (C1/C2/C3/C5), the connector shim (C3/C5), the
advisory prefix (C3/C5). Oracles pinning the verdicts: the
generic order pin (C1/C2/C4), the shim + writer rows
(C3/C5), the hostile-shape pins (C6).

No experiment was needed: every count above is settled by
the cited reads, and the attach/morph/order behaviors are
already execution-pinned by the oracles. No `proof:` entry
is owed.

## Findings

### F1: prefetch attach-column projection is single-owned (CONFIRM, zero-edit)

Contract + variation: the attach-complete `.only()` set for
prefetch writers (connector + generic morph half),
connector-first attach-key order, generic child-column
resolution, never-raises posture. Varies per relation
shape, morph presence, completeness policy, order.

Sites + roles: 1 definition (the property beside its two
input derivations and classify arms); 2 set consumers (the
walker writer, the planner scalar-window writer); 2 fact
consumers (the connector shim, the advisory prefix); 8
package oracle pins + 1 live behavioral pin; docstring /
comment projections only.

Challenges: C1–C6 all count 1; no second attach
derivation, morph resolution, or attach order exists.

Owner + lifetime (principle 7): the property on
`RelationJoinDescriptor`, beside the facts it projects —
the narrowest module both writers already import downward
with no reversal, and the same owner f21/f22 confirmed
for the adjacent facets. Pure derivation, stated "not
cached": each call classifies fresh (the two writers each
call `classify_relation_join` once per child build; the
call is attribute reads, no I/O). No stored derivation, so
no lifetime fields are owed.

Migration: none — zero-edit verdict. Both writers already
compose the owner by name.

Distinct behavior: the connector shim stays a
single-column read (f21 O1 owns its existence question);
the advisory stays morph-first (R16); select-side,
cursor, predicate, cache-key, and lookup reads stay
separate (S/E rows).

Behavioral proof: `static-reviewed` throughout — the
verdict is inventory-shaped (counts over cited reads),
and every behavior the rule governs is already pinned by
the in-tree oracles above (generic order, M2M pk,
reverse O2O, morph completeness, log-on-unknown, G2
gates, live generic prefetch). No failability run is
owed: nothing lands, so no divergence exists to prove
catchable.

Structural gate: none owed. The plausible bypass is a
third writer spelling attach columns inline instead of
composing the property; no mechanical census closes that
beyond a bespoke literal/AST existence test per helper,
which is the forbidden shape (f17/f21 precedent,
verifier-endorsed). The HEAD package-wide census above is
the first-run check that the rule currently holds, and
the in-tree oracles pin every contract verdict so a
divergent second site fails behaviorally where it
matters. Negative control reasoned: a hand copy of the
property body passes every behavior oracle (the copy is
correct), which is exactly why no new oracle is proposed
as a gate.

Coupling: none. Zero-edit verdict; no finding depends on
another landing.

Freshness: HEAD `5c3496e0`. `optimizer/join_taxonomy.py`
HEAD `8026dc8d` (WT `aa289013` concurrent dirt — NOT
traced); `optimizer/walker.py` HEAD `13e1be20` (WT
`4fd8077f` — NOT traced); `optimizer/nested_planner.py`
HEAD `8c3a45f5` (WT `b6ff0a0e` — NOT traced);
`optimizer/plans.py` HEAD `97a524e2` (WT `2e962ae2` —
NOT traced); `optimizer/field_meta.py` HEAD `7c9afe35`
(WT `99f7b1d3` — NOT traced); `optimizer/lateral_fetch.py`
`a48cb0a4` (clean); `optimizer/single_parent_fetch.py`
`3a4bb89b` (clean); `optimizer/nested_fetch.py` HEAD
`bedaa76e` (WT `c36826bb` — census only, NOT traced);
`optimizer/predicates.py` HEAD `965d1282` (WT `d9e2f789`
— census only); `optimizer/selections.py` HEAD
`f49ea7fa` (WT `1f6d3e04` — census only);
`optimizer/extension.py` HEAD `b7b6c434` (WT `8e3fe7c1`
— census only); `optimizer/hints.py` HEAD `f6776564`
(WT `ee68ae03` — census only); `utils/relations.py`
HEAD `3b35dfcd` (WT `23df6180` — NOT traced);
`types/resolvers.py` HEAD `09d40f34` (WT `a8c6a46e` —
NOT traced); `mutations/resolvers.py` HEAD `d77a6c68`
(WT `2ff49673` — NOT traced);
`rest_framework/resolvers.py` HEAD `fc9d8ee5` (WT
`074d6e4b` — NOT traced);
`tests/optimizer/test_join_taxonomy.py` HEAD `481294c3`
(WT `df9be570` — oracle cited at HEAD);
`tests/optimizer/test_walker.py` `ca5c32d7` (clean);
`test_query/test_library_api.py` HEAD `91f0238b` (WT
`099e25b9` — oracle cited at HEAD). Searched
population: every `.py` under
`django_strawberry_framework/` via the `git grep HEAD`
instruments above; every module EXCLUDED on body
evidence is named in an S/E row.

### Standing rejections taken as input (trigger-checked fresh)

- S1, partition/connector facet (verified f21): same owner,
  different rule (grouping + child connector vs attach
  set). Converged as same-owner sibling.
- S2, lateral shape/link facet (verified f22): same owner,
  different rule (correlated-join shape + resolved link
  objects). Converged as same-owner sibling per f22 S5.
- S3, select-side attname (verified walker-R5 / F-R5):
  `_record_relation_access` still appends the source-row
  local column (`walker.py:1163`) while the writer appends
  the child-side attach key (`:1611`); different values on
  a forward FK. Trigger unfired (no call site needs both).
- S4, the six `pk.attname` readers (verified R8): the
  scalar-window pk (`:719`, edge identity) still sits
  beside the attach loop (`:725`) under separate reasons,
  deduped by `append_unique`. Trigger unfired.
- S5, morph detect/carry/resolve tri-split (verified R14):
  still exactly three readers — `relation_kind` detects
  (`utils/relations.py:234`-`:245`), `FieldMeta` carries
  (`:167`-`:168`), `_generic_child_attname` resolves.
  Trigger unfired.
- S6, attach vs advisory order (verified R16): the
  property still orders connector-first with the contrast
  stated (`:173`-`:174`); the advisory still prefixes
  morph-first (`:650`-`:651`). Trigger unfired.
- S7, M2M pk attname vs pk name (verified R15):
  `_parent_join_column` still reads the target pk ATTNAME
  (`:236`) while `_target_pk_name` still reads the pk NAME
  (`field_meta.py:345`). Trigger unfired.
- S8, routing reads through `FieldMeta` (verified
  field_meta-R1 / R-B): the snapshot still carries
  neither `remote_field` nor `through` (full slot census
  `:150`-`:168`), and the planner still re-resolves raw
  for the gap (`:1256`). Standing D1's subset legs do not
  reopen this. Trigger unfired.
- S9, read bodies (verified R-C / R3): the taxonomy still
  composes `relation_attr` / `relation_bool` with
  `lenient=True` (`:100`-`:110`). Trigger unfired.
- S10, per-site containment (verified R12): the four
  contained answers (kind sink, M2M `None`, link-pair
  `(None, None)`, morph `None`) still each own their
  policy. Trigger unfired.

### Fresh exclusions (contract difference plus trigger each)

- E1, `_connector_only_field` shim: single-connector read
  vs attach-complete set (non-generic projection of one
  input fact, not the set rule). Trigger: the shim gains
  the morph half — then it duplicates the property and
  must compose it.
- E2, `_advise_composite_index` equality build: B-tree
  equality-prefix order vs attach-protocol order (same
  two facts, reader-stated opposite order). Trigger:
  either order's owner changes its rule.
- E3, lateral `_select_columns`: SQL select-list reflection
  of an ALREADY-APPLIED projection (via
  `deferred_loading_of`) vs column-set derivation. The
  attach columns reach the lateral subquery through the
  walker's projection, never re-derived. Trigger: the
  mirror starts choosing columns instead of reflecting
  them.
- E4, lateral correlation naming
  (`_prefetch_related_val_`, `lateral_fetch.py:1142`):
  subquery output naming from the resolved link field vs
  the `.only()` load set. Trigger: the name starts
  driving which columns load.
- E5, single-parent `parent_link_attname`
  (`single_parent_fetch.py:158`): per-parent `.filter()`
  kwarg (correlation predicate) vs load projection; the
  load set rides the pristine child queryset wholesale.
  Trigger: the spec starts projecting columns.
- E6, resolvers `_prefetch_cache_name`: `_prefetched_objects_cache`
  KEY vocabulary (which string Django files results under)
  vs which child COLUMNS load. Trigger: a cache-key read
  starts constraining the projection.
- E7, `_extend_only_projection` (keyset cursor columns):
  cursor minting from ordering-column values vs attach
  completeness. Queued `keyset-cursor-column-projection`
  owns it. Trigger: cursor columns start serving attach.
- E8, `attached-prefetch-lookups-read` (queued sibling):
  queryset-STATE reads of already-attached
  `_prefetch_related_lookups` (lenient
  `plans.py::_consumer_prefetch_lookups` `:562`, strict
  forward in `walker.py::_hint_prefetch_over_pk_set`)
  vs descriptor-DERIVED column projection. Lookup strings
  vs column attnames; downstream-of-planning vs
  plan-time. Converged as disjoint; its item adjudicates
  the read. Trigger: either read starts deriving columns
  from the descriptor.
- E9, `scalar-only-window-projection` (queued sibling):
  the whole three-leg window projection (pk + attach +
  order) vs the attach leg it consumes by name at `:725`.
  Converged as consumer; its item owns the window rule.
  Trigger: the window starts spelling attach columns
  instead of composing the property.
- E10, `composite-index-advisory` (queued sibling): index
  recommendation vs attach loading; consumes the same
  two facts in its own order (E2 is the consumer-side
  statement). Trigger: the advisory starts driving the
  load set.
- E11, f17 strategy selection / f20 range derivation
  (verified): WHICH backend fetches / WHICH row numbers
  fetch vs WHICH columns load. Their R11/R15 excluded
  against this row; converged from this side. Trigger
  per row: the sibling starts deriving load columns.
- E12, mutations partial-input mapping +
  rest_framework identity snapshot: write/validation
  vocabulary vs fetch projection. Trigger: a write path
  starts projecting prefetch columns.
- E13, predicates `_effective_alias_names`: reserved-alias
  namespace avoidance vs attach. Trigger: none (no
  shared meaning).

No new index rows owed: every sub-rule above either
converges to a verified row or names a real open row.

## Defects

None. The trace found no non-duplication defect at HEAD
bytes, and no ticked row proved factually wrong (f21 O1's
zero-production-caller census re-confirmed fresh at HEAD).

## Pending execution

None. No `proof:` entry (static trace; every challenge
settles on cited reads plus in-tree oracles) and no
`gate:` entry. Sharded/PG cells: inapplicable by
construction — the rule is pure plan-time metadata
derivation (field-attribute reads plus `_meta` lookups;
no queryset execution, no alias, no dialect decision),
stated for Worker-2 to judge. No pytest was run; every
proof is `static-reviewed`.

## Judgment

CONFIRM: the prefetch attach-column projection is
single-owned at
`optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
— 1 definition, 2 set consumers + 2 fact consumers by
name, C1–C6 all count 1, 10 standing rows trigger-clean,
13 fresh exclusions with triggers, zero defects, no new
index rows.

Type gates (shared venv, read-only): `mypy` clean (119
source files, no issues), `basedpyright` clean (0 errors,
0 warnings, 0 notes), `check_any.py` clean (130 allowed
uses at 90 sites). Vacuous as consolidation gates —
zero-edit verdict, no symbol added, moved, or removed —
reported here per convention for the verifier to re-run.

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

## Independent verification (Worker-2)

Recorded BEFORE opening `## Findings` (headings + head/tail
only read before this section was written). Fresh trace at HEAD
`5c3496e0` WT bytes; fingerprints: `join_taxonomy.py` WT
`aa289013` / HEAD `8026dc8d`, `walker.py` WT `4fd8077f` / HEAD
`13e1be20`, `nested_planner.py` WT `b6ff0a0e` / HEAD `8c3a45f5`
(all match dispatch pins). Package-wide name census for
`prefetch_attach_columns`: 1 `def` (property), 2 read sites, 5
prose mentions (docstrings/comments), zero other spellings.

### Sites + roles (Worker-2)

- DEFINITION (1):
  `optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
  (`:152`, property): derives the attach-complete tuple
  (`parent_join_column`, plus `content_type_column` when present)
  from the descriptor's own resolved facts. Pure, sync, no I/O.
- SET consumers (2, by name):
  1. `optimizer/walker.py::_ensure_connector_only_fields` (`:1604`):
     appends each column to `plan.only_fields` (log-and-skip when
     empty).
  2. `optimizer/nested_planner.py::_project_scalar_only_window`
     (`:735`): appends each column to the direct `.only(*fields)`
     set.
- FACT consumers (2, by name; read the underlying fields, not the
  projection):
  1. `optimizer/nested_planner.py::_connector_only_field` (`:184`):
     reads `parent_join_column` only (single-column shim; zero
     production callers, one test pin — f21 O1 shape).
  2. `optimizer/nested_planner.py::_advise_composite_index`
     (`:656-661`): reads both facts to build the MORPH-FIRST
     advisory equality prefix — a different contract (advisory
     order) from the connector-first attach key, so a consumer of
     the facts, not a second projection definition.
- PROJECTIONS: class-docstring clause (`join_taxonomy.py:136`),
  property docstring (`:153`), shim docstring
  (`nested_planner.py:176`), writer comments/docstrings
  (`nested_planner.py:730`, `walker.py:1586`), fetch-time-morph
  comments (`nested_planner.py:1330`, `plans.py:1122`). Describe;
  never own.
- ORACLES (independent, literal pins): the tuple-value pin in
  `tests/optimizer/test_join_taxonomy.py:167`, the writer tests in
  `tests/optimizer/test_walker.py:1982-2306` + G2 gates
  (`:5057-5074`), the advisory tests in
  `tests/optimizer/test_nested_index_advisory.py`. None reads the
  expected set from the owner.
- EXCLUDED on body reads (different contracts):
  `_record_relation_access` (parent-side FK attname),
  scalar/id projections (`walker.py:830-866`),
  `_extend_only_projection` (cursor-column UNION over an existing
  mask), `connection.py` cursor extension,
  `window_partition_for_prefetch` (parent-side partition),
  `join.windowable` / `join.kind` reads (`nested_planner.py:1266`,
  `plans.py:996`), lateral link-field reads (f22 family),
  `.only()` appliers (`plans.py:334`) vs writers.

### Challenges (Worker-2; definitions forced)

- W2-C1 new column kind (a third attach column): 1 — the property
  body; both set consumers follow by name. The advisory decides
  separately under its own order contract (listed, not counted).
- W2-C2 attach-key order change (morph-first): 1 — property body
  only; both writers are order-agnostic loops.
- W2-C3 empty/unresolved posture change (empty tuple vs raise): 1
  definition; the two writers' degrade branches adapt as
  consumers (listed, not counted).
- W2-C4 splitting the projection (connector-only vs
  attach-complete): 1 — the facts are already separate fields, so
  a split consumer reads the fields (the existing fact-consumer
  shape); no second projection definition is forced.
- W2-C5 a third set consumer: 1 — composes by name; no new
  definition. No third writer exists today (swept every `.only(`
  writer package-wide: appliers, unions, and cursor extensions
  only).
- W2-C6 morph-half condition change (e.g. attach-complete only for
  some generic shapes): 1 — property body (or the
  `content_type_column` resolution it reads; one of the two, never
  both — the property owns the combination, the classifier owns
  the fact).

### Owner choice (Worker-2)

`RelationJoinDescriptor.prefetch_attach_columns` (principle 7):
the descriptor already owns the join-shaped facts the projection
derives from (`parent_join_column`, `content_type_column`, both
resolved in `classify_relation_join`); the projection is a pure
derivation of those facts with no further inputs; both set
consumers already import `join_taxonomy`, so no dependency
reverses; no narrower cohesive owner exists (the facts live
nowhere else). The only alternative — one writer owning the set
with the other importing across — reverses the walker/planner
sibling direction and strands the fact consumers.

### Zero-edit stress (Worker-2)

Posited a consolidation W1 might owe and failed to land one: the
only tuple-building site is the property; `_advise_composite_index`
builds a differently-ordered, differently-purposed list (advisory
prefix, morph-first, with order terms + pk appended downstream),
so folding it into the property would merge two contracts with
separate reasons to change (attach completeness vs index
coverage). No third writer, no re-derivation, no twin.

### Reconciliation (Worker-2; after reading `## Findings`)

W1 traced HEAD bytes per dispatch; I traced WT bytes. The two
traces CONVERGE on every load-bearing point, so the verdict
holds at BOTH states — stronger than either alone. Difference
by difference:

- F1 count + consumers + owner: AGREE. Same 1 definition, same
  2 set consumers by name (walker writer, planner scalar-window
  writer), same 2 fact consumers by name (connector shim,
  advisory prefix), same owner via principle 7 with the same
  dependency-direction reasoning. W1's C1–C6 exercise the
  fact-level arms (third column, order, M2M arm, GFK
  resolution, reverse arm, posture); my W2-C1–C6 exercise the
  property level (new kind, order, posture, split, third
  consumer, morph condition). Complementary, all count 1, no
  conflict — jointly they cover both variation layers.
- S1–S10: ENDORSE trigger-clean, each re-verified on fresh
  evidence at HEAD bytes: S3 (`walker.py:1163` attname vs
  writer), S4 (pk leg `:719` beside attach loop `:725`), S5
  (detect/carry/resolve three readers), S6 (connector-first
  `:173`-`:174` vs morph-first `:650`-`:651`), S7
  (`field_meta.py:345` pk NAME), S8 (slot census + raw
  re-resolve `:1256`), S9 (lenient compose `:100`-`:110`),
  S10 (contained per-site policies), S1/S2 (f21/f22 verified
  same-owner siblings). f21 O1 re-confirmed FRESH by me, not
  inherited: `_connector_only_field` has 1 `def`, zero
  production callers, one test pin
  (`test_walker.py:23`/`2031`).
- E1–E13: ENDORSE each contract difference + trigger. E2/E3/E4/E5
  bodies read fresh (advisory morph-first build, select-column
  reflection via `deferred_loading_of`, correlation naming from
  the link attname, filter kwarg + pristine queryset). E6/E13
  sites real (`_prefetch_cache_name`,
  `_effective_alias_names`). E7/E8/E9/E10 all name REAL open
  plan rows (`keyset-cursor-column-projection`,
  `attached-prefetch-lookups-read`,
  `scalar-only-window-projection`, `composite-index-advisory`
  — each `open` in the index with an undispatched family
  item). E11: f20 R15 names this row explicitly; f17 R11 covers
  this ground per its own W2 precision note — "excluded
  against this row" is fair. E12/E13 triggers sound.
- Matrix discharge: ENDORSE. Axis 1 sites verified fresh
  (`mutations/resolvers.py:755` scalar carve-out,
  `rest_framework` identity snapshot); axis 2 zero-hit claim
  consistent with the pure-sync property; axis 3/4/6 match my
  own sweeps (`.only(` writers, `rel_obj_attr` prose-only,
  consumer-wins boundary). My WT-bytes census re-performs the
  first-run check: identical shape (1 def, 2 + 2 readers).
- Index rows: NONE OWED — ENDORSED. Every sub-rule converges
  to a verified row or a real open row (four queued families
  named, all confirmed open above).
- Pending-execution "None": CORRECT → plain `verified`. No
  `proof:` is owed: zero-edit inventory verdict, nothing
  changed, so no observable-equivalence proof exists to defer;
  every governed behavior is pinned by the cited in-tree
  oracles (8 package pins counted + 1 live pin at
  `test_library_api.py:5454`, all verified present). No pytest
  run is owed for a no-op diff.
- Cells `inapplicable by construction`: JUDGED SOUND. The
  property, `classify_relation_join`, `_parent_join_column`,
  and `_generic_child_attname` are field-attribute reads plus
  `_meta` lookups only (bodies read fresh — no queryset
  execution, no alias, no dialect decision); both consumers run
  once at plan time. No cell run could observe more.
- Structural gate "none owed" + reasoned negative control:
  ENDORSE per the f17/f21 precedent (a bespoke existence test
  per helper is the forbidden shape); the package-wide census
  is the first-run check and I re-ran it fresh at WT bytes.
- Freshness: W1's pins verified on sample — all three indexed
  files in BOTH states match dispatch pins, `plans.py`
  `97a524e2`/`2e962ae2` and `field_meta.py` `7c9afe35`/`99f7b1d3`
  match, `lateral_fetch.py`/`single_parent_fetch.py`/
  `test_walker.py` confirmed clean. Comparable; nothing reopened.
- Worker-0 assertions: ALL RE-VERIFIED — no `## Implementation`
  (before my W2 section, which is expected), 3/3 WT pins match
  dispatch pins, `git diff ITEM_BASELINE --name-only` is the
  plan edit alone, status 471 = 194 M + 277 `??`. Tracked diff
  EMPTY; zero-edit stands.
- AGENTS.md prose on the item-scoped diff: the tracked diff is
  empty and the artifact is per-cycle scratch (raw `path:NN`
  allowed) — no style cleanup owed. Ruff: VACUOUS (no tracked
  `.py` touched; plan edit is `.md`, artifact untracked `.md`).
  Type gates RE-RUN whole-package in the shared venv (slots
  1–3 damaged per KNOWN, no execution probe needed one):
  `mypy` clean (119 source files), `basedpyright` 0/0/0,
  `check_any.py` 130 allowed at 90 sites — all match W1's reads
  exactly. Recorded as tree-health evidence, vacuous as
  consolidation gates.

Observations (scratch nits, NOT defects, verdict not spent):

- (Worker-2 O1) Enumeration forward-refers to "E14" for the
  predicates alias-namespace row, but Findings numbers it E13.
  The row itself exists with a contract difference + trigger;
  internal label slip only.
- (Worker-2 O2) W1's line numbers are HEAD lines (stated); mine
  are WT lines. Both cited; no contradiction.

`## Defects` addition: none — 0 defects stands (no ticked row
factually wrong; O1 census re-confirmed).

### Verdict (Worker-2)

`verified` (PLAIN — no `proof:` correctly remains, no `gate:`
entries, cells inapplicable judged sound). Zero-edit CONFIRM
of single ownership at
`optimizer/join_taxonomy.py::RelationJoinDescriptor.prefetch_attach_columns`
stands on two independent traces at two tree states.
