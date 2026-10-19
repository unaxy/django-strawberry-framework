# DRY review: `relation-identity-column`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Fresh family trace at HEAD `23b5f421` + WT. WT line numbers throughout
unless marked HEAD. The rule, re-derived fresh at current bytes: which
model column names a relation's identity for filter annotation (the
GraphQL input scalar) and runtime coercion (the raw value a relation
leaf compares). One kernel plus two source adapters plus a two-link
runtime chain, all in `django_strawberry_framework/filters/base.py`
(WT defs; HEAD defs 38 lines later: 1253 / 1268 / 1284 / 1306 / 1325):

- `_model_identity_column` (WT :1230) - the kernel: `meta.get_field(to_field_name)`
  or `meta.pk` (WT :1240), followed through any relation-valued key
  (`while isinstance(column, models.ForeignKey): column = column.target_field`,
  WT :1241, the only `while isinstance` follow loop package-wide), gated to a
  `models.Field` (WT :1243). `None` when the model is unresolved.
- `relation_identity_column` (WT :1215) - relation adapter: the
  `is_relation` gate (WT :1225) plus `related_model` extraction, then
  the kernel with `None` (WT :1227).
- `model_choice_identity_column` (WT :1246) - queryset adapter: the
  filter's `queryset.model` unless the queryset is callable (WT :1262),
  falling back to the relation target (WT :1263), then the kernel with
  `extra["to_field_name"]` (WT :1265).
- `_relation_identity_column_for` (WT :1268) - runtime reader: the bound
  filter's parent-`_meta.model` plus live `field_name` through
  `get_model_field` (WT :1278-1284), then `relation_identity_column`.
  Its walk half belongs to queued family `bound-filter-model-field-walk`
  (F-10); its identity-reader half belongs here.
- `_coerce_relation_identity` (WT :1287) - runtime coercer: the chain
  read (WT :1294) plus `coerce_field_value_or_none` (WT :1297), the
  verified `field-value-coercion` owner. Unbound (`None` column) passes
  through; uncoercible answers `None` ("names no row").

Production call graph, complete at WT bytes (every caller a by-name
composition; zero inline re-derivations):

- `_model_identity_column` <- 2: `:1227`, `:1265`.
- `relation_identity_column` <- 2: `:1284`,
  `filters/inputs.py::_relation_identity_annotation` (:375).
- `model_choice_identity_column` <- 1:
  `filters/inputs.py::_model_choice_identity_annotation` (:409).
- `_relation_identity_column_for` <- 1: `:1294`.
- `_coerce_relation_identity` <- 2: `RelationPkFilter.filter` (:1352),
  `RelationPkMultipleFilter.filter` (:1388).

The two annotation arms ride `convert_filter_to_input_annotation`'s kind
table (`_pk_multi` :582, `_pk` :585, `_model_choice` :588) and type the
column through the shared `_scalar_from_model_field` / `SCALAR_MAP`
seam, so a filter input agrees with the `DjangoType` reading the same
key. The trio region (`relation_identity_column` through
`_coerce_relation_identity`, WT :1215-1297) is byte-identical between
HEAD and WT (`cmp` clean over the extracted region): the owner carries
zero concurrent dirt.

Whole-package mechanism census (every hit body-read; `muse.search`
regex over `django_strawberry_framework/`, `__pycache__` excluded):
`related_model` + column derivations - only the trio (base.py:1227,
:1240, :1264); `_meta.pk` readers - 35 hits across 19 files, each a
distinct contract (`## Findings` R1-R6/R8); `.target_field` code reads -
base.py:1242 (the follow loop), permissions.py:528 (visibility `__in`
edge), predicates.py:410 (parent-link storage walk, R8),
field_meta.py:294 (metadata), lateral_fetch.py:358/:591/:1133 (spec
fields); `to_field_name` code reads - base.py:1230/:1265 (this rule),
forms/resolvers.py:172 (object-to-key, R7), sets.py:338 (upstream
mirror, R6); `.get_field(` callers - 27 hits, only :1240 passes a
`to_field_name`; `is_relation` gates - 77 hits, only :1225/:1263
admit an identity source; `pk_fields` readers - 3 (composite
detector, non-pk predicate, composite metadata); `while isinstance`
loops - 1 in production (:1241); the otherwise-spelled parent-link
follow loop (predicates.py:409) is R8's distinct contract. No second
identity-column site exists outside the indexed files.

Indexed-file dirt attribution (by diff content vs `git show HEAD:`):
base.py's 17 hunks are the external truth migration (`truth.*` reads
plus the import) and hostile-guard deletions plus doc rewords, all
above :1215 or below :1400 - none touches the trio or chain.
inputs.py's 18 hunks are the same migration (including the two
annotation arms' message-only reword at :375-382 and :408-418, which
rename the diagnostic rendering but leave both owner calls intact)
plus the range-shape fail-loud hunk - concurrent, untouched by this
zero-edit item. Lifetime (principle 4): pure derivation, not cached -
no stored result, no validity key, no invalidation; every read walks
live `_meta`.

## Verification

### Matrix

1. Cross-flavor: the three write flavors share `relation_id_scalar`
   (mutations/inputs.py:463) for id typing and
   `coerce_relation_pk_or_none` (utils/write_values.py:110) for raw-pk
   coercion; the Relay flavor shares `_node_id_slot` /
   `_coerce_pk_or_none` (relay.py:146/:177); the column-less write
   relations compose the write owner through
   `annotate_queryset_relation` (mutations/inputs.py:528). Each read on
   body strength: raw-pk-only with no FK-follow and no `to_field`
   (R1/R2), id-slot resolution through the Strawberry type (R3).
   Distinct contracts, recorded in `## Findings`. Discharged.
2. Sync/async: 0 `async def` / `await` in filters/base.py and
   filters/inputs.py (re-grepped; the folder's `async` hits are all in
   filters/sets.py visibility-derivation twins, which never touch the
   identity column). The rule is pure `_meta` derivation plus
   in-process coercion with no await boundary, so no twin can exist.
   Discharged.
3. Derived knowledge: every same-token population above inspected on
   body strength; each site carries a distinct contract (R1-R8). The
   one genuine re-derivation - the bound-filter walk shared by
   `IntegerInFilter.filter` and `_relation_identity_column_for` - is
   queued family `bound-filter-model-field-walk` (F-10), not this
   rule. Discharged.
4. Round-trip: the annotation half (column to scalar) and the coercion
   half (value to column type) read the SAME owner - both arms call
   the trio, both filter bodies call the chain. The halves are
   composed, not split; the GlobalID encode/decode halves likewise
   share `resolve_globalid_target_definition`. Discharged.
5. Other media: the 9 package oracles spell literal expectations
   (`Int`, `list[int]`, column identity, match/drop verdicts); the two
   direct owner tests assert the target itself (the run-7 precedent,
   s7-endorsed). The 4 live rows pin wire behavior over `/graphql/`.
   Projections: the base.py module docstring (:16), the RelationPk
   docstring cite (:1334), the two inputs.py docstring cites (:370,
   :404), spec-027 Decision 4 (conversion table + raw-pk rows). No
   medium carries a second definition. Discharged.
6. Omission: the relation-leaf filter classes enumerated -
   `RelationPkFilter` / `RelationPkMultipleFilter` compose both
   halves; consumer `ModelChoiceFilter` / `ModelMultipleChoiceFilter`
   compose the annotation arm while runtime cleaning stays in
   django-filter's own form field BY CONTRACT (trio docstring :1250
   plus spec-027); the GlobalID pair decodes through the node id
   (Relay contract, excluded); `RelatedFilter` is a branch, not a
   leaf. No member lacks a guard the rule owes it. Discharged.

### Enumeration

Instrument: `muse.search` regex over `django_strawberry_framework/`
for the rule's mechanism vocabulary (`related_model` + column,
`_meta.pk`, `target_field`, `to_field_name`, `.get_field(`,
`is_relation`, `pk_fields`, `while isinstance`), plus definition
reads of every hit, plus the production caller census of all five
symbols. Count: 3 kernel/adapters + 2 chain links, all in
filters/base.py; 2 annotation arms + 3 kind-table registrations + 2
filter bodies composing by name; 0 production readers outside
filters/base.py and filters/inputs.py. Examined-and-excluded, each on
body strength:

| Site | Verdict |
|---|---|
| Write-side `relation_id_scalar` + `coerce_relation_pk_or_none` | R1/R2: raw-pk-only, no follow, no to-field |
| Relay `_node_id_slot` + `_coerce_pk_or_none` | R3: id-slot through the Strawberry type |
| Leaf-chain key (`_leaf_chain` + `_relation_key_value`) | R4: visibility predicate build, not typing |
| pk-marker trio (`_relation_uses_non_pk_to_field`, `_marked_pk_field_name`) | R5: predicate path, never the column |
| Remaining `_meta.pk` / `get_field` / `target_field` / `pk_fields` readers | R6: cursor/order/join/plan/inspect contracts |
| Forms `_to_form_key_value` | R7: opposite direction (object to key) |
| Predicates `_stored_column` parent-link walk | R8: storage proof, not identity typing |
| `_scalar_from_model_field`, `coerce_field_value_or_none` | Composed seams, owned elsewhere |
| Bound-filter walk (`IntegerInFilter` + `:1278-1284`) | F-10's queued family, not this rule |

### Challenges

Each axis moves exactly one definition; the annotation arms, the
filter bodies, the oracles, and the projections compose or pin and
move on none. Counts re-derived at WT bytes; s7's HEAD counts
reproduced exactly.

- C1 new relation-valued key shape (a second hop kind, a
  multi-target `ForeignObject`): `_model_identity_column` moves once
  (:1240-1243); both adapters and both halves follow, while the
  predicates storage walk (R8) moves only on a storage-proof change.
  Count 1 per contract.
- C2 new build-time model source (queryset-model precedence, a new
  fallback): `model_choice_identity_column` moves once (:1261-1265).
  Count 1.
- C3 new runtime model source (a queryset read for the RelationPk
  path): `_relation_identity_column_for`'s reader half moves once
  (:1284); its walk half is F-10's pair member and moves there.
  Count 1 here.
- C4 raw-pk verdict change (uncoercible match-none to raise;
  member drop to reject): `RelationPkFilter.filter` /
  `RelationPkMultipleFilter.filter` move once each (:1352/:1388);
  the GlobalID malformed-raise is a different input class (s7 R13,
  trigger untriggered). Count 1 per class.
- C5 new admittable relation shape: `relation_identity_column` moves
  once (:1225) for the RelationPk path; the `:1263` fallback gate is
  a separate contract (fallback admission, not source admission)
  sharing only Django's own `is_relation` predicate - shared stdlib
  token, not a package rule. Count 1 per contract.
- C6 scalar-table change (`SCALAR_MAP` to another table):
  `_scalar_from_model_field` moves once; both annotation arms
  follow. Count 1 outside this family; this family's members move 0.

Proof status: all six `static-reviewed` (definition counts over
closed, grep-enumerated populations; zero-edit, so no equivalence is
owed). The rule's current hold is additionally execution-verified:
the nine pinning oracles pass 9/9 at WT bytes (command under
`## Implementation (Worker-1)`).

## Findings

### F1 `relation-identity-column` - CONFIRMED single-owned, zero-edit

- Contract + variation: the column naming a filter relation leaf's
  identity - the related row's primary key followed through any
  relation-valued key, or a model-choice filter's `to_field_name`
  column. The GraphQL input scalar and the runtime value coercion
  both read it. Varies on key-shape following (C1), build-time
  model source (C2), runtime model source (C3), scalar verdict
  (C4), admittable shape (C5), scalar table (C6, outside).
- Sites + roles: 5 definitions, all in filters/base.py (one kernel,
  two source adapters, two runtime links - one rule, one module).
  Consumers, all by name: `_relation_identity_annotation` and
  `_model_choice_identity_annotation` (filters/inputs.py, via the
  kind table), `RelationPkFilter.filter` and
  `RelationPkMultipleFilter.filter` (via the chain). Composed
  seams (owned elsewhere, converged not counted):
  `_scalar_from_model_field` (inputs.py + types/converters) and
  `coerce_field_value_or_none` (verified family
  `field-value-coercion`). Oracles: the 9 package pins
  (tests/filters/test_base.py: 2 direct-owner + 4 RelationPk
  behavior; tests/filters/test_inputs.py: 2 raw-pk annotation + 1
  model-choice override) plus the 4 live rows
  (test_scalars_filter_api.py: `exact`/`in`, membership rules;
  test_library_api.py: forward-relation pks over HTTP, raw-pk
  input shape). Projections: the 4 docstring cites plus spec-027
  Decision 4 (Matrix axis 5).
- Challenges: C1 count 1 per contract, C2-C3 count 1 each, C4
  count 1 per class, C5 count 1 per contract, C6 count 1 outside
  (`### Challenges`).
- Owner + lifetime: filters/base.py, the current home, by
  principle 7. The filter-flavor contract, both annotation
  consumers (inputs.py already imports base.py), and both runtime
  consumers live under it; no legitimate consumer outside the
  filter family exists. Alternatives rejected: filters/inputs.py
  (hosts nothing the runtime chain could import without reversing
  the inputs-imports-base edge); utils/relations.py (generic
  taxonomy, no queryset/`to_field`/`extra` filter-flavor
  knowledge); mutations/inputs.py write-side owner (different
  contract, R1). Dependency direction wins. Lifetime: pure
  derivation, not cached (no stored result, no invalidation).
- Migration: none - the rule already reads as one kernel composed
  by name at every link.
- Distinct behavior (rejections, each with contract difference,
  trigger, durable home):
  - R1 write-side `relation_id_scalar` (mutations/inputs.py:463):
    Relay-vs-raw branch by primary type; the raw arm reads
    `related_model._meta.pk` with NO FK-follow and NO `to_field`
    (writes always address the pk; `to_field` converts at decode).
    A relation-valued write key moves it only; a filter
    `to_field` change moves the kernel only. Trigger: write
    inputs type through a relation-valued pk or a `to_field`.
    Home: mutations/inputs.py:463 (existing docstring states the
    raw-pk rule; this artifact carries the difference).
  - R2 write-side `coerce_relation_pk_or_none`
    (utils/write_values.py:110): raw-pk M2M existence-query
    coercion taking the related model directly - no walk, no
    `to_field`, no unbound arm. Its own docstring already
    records the GlobalID counterpart; same standing here.
    Trigger: the write set decoder shares the filter walk or
    the `to_field` source. Home: this artifact (the write-side
    owner docstring states its own contract).
  - R3 Relay `_node_id_slot` + `_coerce_pk_or_none`
    (relay.py:146/:177): resolves the id slot through the
    Strawberry type's `resolve_id_attr()` (custom NodeID
    columns, reverse/non-concrete arms) - a different subject
    (Relay id slot) from filter relation identity, and its own
    docstring forbids coercing against `_meta.pk`. Trigger:
    filter identity resolves through the type's id slot. Home:
    relay.py:177 (existing).
  - R4 leaf-chain key (filters/sets.py:4216-4249 plus
    `_relation_key_value` :1457): decides which key column a
    re-read leaf COMPARES in a visibility predicate (`isnull`
    to target pk, forward to stored key plus `key_hop`, to-many
    to `path_infos` targets with the GlobalID-marker arm) - a
    different time (predicate build over visible rows) and
    different inputs (hops, marker) from typing/coercion.
    Trigger: the leaf re-read calls the identity owner for its
    column. Home: this artifact.
  - R5 pk-marker family (verified `globalid-relation-pk-marker`):
    answers which PREDICATE PATH (`<rel>` vs `<rel>__pk`),
    never which column; reciprocal of that family's row 11,
    which excludes this machinery on the same terms. Trigger:
    either derivation reads the other. Home: that family's
    artifact row 11 (existing) plus this row.
  - R6 remaining same-token readers, each a distinct contract:
    cursor/order/pagination (`_resolve_cursor_field_column`
    keyset.py:242, plans.py, nested_planner.py, walker.py,
    lateral_fetch.py spec fields, connection.py:894 pk-segment,
    orders/sets.py:831 pk-segment); Relay/node identity
    (types/relay.py, types/base.py pk names); write-pipeline pk
    equality (`canonical_pk` write_transaction.py:777);
    filter generation (`__all__` pk add sets.py:2117,
    `_forward_relation_extra` sets.py:327 mirroring UPSTREAM's
    default extra - the extra key is the seam this rule
    consumes, not a second derivation); form column resolve
    (forms/inputs.py:455); plan/visibility metadata
    (predicates.py:259/:417 path walks, field_meta.py:294,
    permissions.py:528, relations.py composite detector).
    Trigger per site: it starts typing or coercing a filter
    leaf. Home: this artifact.
  - R7 forms `_to_form_key_value` (forms/resolvers.py:165):
    object-to-key at write time (a resolved row to its
    `to_field` value for form re-validation) - the opposite
    direction from this rule's key-to-column at type time.
    Converges with s7 R12 on fresh evidence. Trigger: a shared
    to-field policy owner. Home: this artifact.
  - R8 predicates `_stored_column`
    (optimizer/predicates.py:407): the only other `target_field`
    follow loop - walks `parent_link` hops upward from an
    arbitrary field to prove which physical column stores it for
    the row-preserving-predicate check. Different start (any
    field vs a model's pk/`to_field`), different hop predicate
    (`parent_link`-only vs any-`ForeignKey`, so a `to_field` FK
    hop moves the kernel only), different `None` contract
    (passthrough vs `None`-for-unresolved), different consumers
    (predicate proof vs filter typing). The shared form
    considered - one parameterized follow helper - would own 2
    lines per site while coupling filter typing to predicate
    proofs through a mode flag, which the method forbids.
    Trigger: either loop's hop predicate subsumes the other.
    Home: predicates.py:407 (existing docstring states the
    storage contract; this artifact carries the difference).
  - F-10 separation (not a rejection): the bound-filter walk
    (`IntegerInFilter.filter` + `:1278-1284`) is queued family
    `bound-filter-model-field-walk`; this finding counts the
    identity-reader half only. No trigger - already queued.
- Behavioral proof: `static-reviewed` for all six challenges (no
  behavior change proposed); the nine pinning oracles additionally
  re-executed green at WT bytes (9/9; command under
  `## Implementation (Worker-1)`).
- Structural gate: none owed. The owner trio is already single
  with every link composing by name; the mechanism tokens
  (`_meta.pk`, `target_field`, `to_field_name`) are shared across
  the distinct R1-R8 contracts, so a census pinning today's counts
  would either carve per-site exclusions (a bespoke existence test
  per helper, which the method forbids) or false-positive on the
  lawful write/Relay/cursor readers. The durable protection is the
  existing behavioral pins (direct-owner, annotation, coercion,
  and live-wire oracles) plus this artifact's censuses as the
  re-derivation baseline.
- Coupling: none landing. Adjacent queued family F-10 will touch
  the walk half (`:1278-1284`) of `_relation_identity_column_for`;
  this zero-edit finding lands nothing, so no merge coupling -
  but F-10 must re-take these pins (any fingerprint change reopens
  this finding).
- Freshness: HEAD `23b5f421` (detached, intended).
  `ITEM_BASELINE=3cdfe5540d7bced689f084986e4726fa68acc5e6` (taken on
  `23b5f421`; the baseline tree carries the WT dirt, so every BASE pin
  below equals its WT pin and the item-scoped diff is empty). Pins are
  WT / HEAD / BASE, 8 chars (`git hash-object`; BASE via
  `git rev-parse <baseline>:<path>`):
  filters/base.py `77c2e7a6` / `a43513a7` / `77c2e7a6` (dispatch pins
  reproduced exactly); filters/inputs.py `a269a3fe` / `d77a113c` /
  `a269a3fe` (dispatch pins reproduced exactly); filters/sets.py
  `9428aba9` / `b8740187` / `9428aba9`; mutations/inputs.py
  `bb329e4d` / `f821661e` / `bb329e4d`; utils/write_values.py
  `1dc426d4` / `a9d6fa32` / `1dc426d4`; utils/write_transaction.py
  `50909be8` / `2b9f861c` / `50909be8`; relay.py `9257a51b` /
  `025f2a6a` / `9257a51b`; forms/inputs.py `df1df485` / `1b38e890`
  / `df1df485`; forms/resolvers.py `ad4abc7b` clean;
  keyset.py `a1890813` / `ec694bc8` / `a1890813`; permissions.py
  `826330cb` / `b7ab8c69` / `826330cb`;
  optimizer/predicates.py `9e7d80d1` / `71593939` / `9e7d80d1`;
  optimizer/field_meta.py `478419b7` / `1098cce2` / `478419b7`;
  optimizer/join_taxonomy.py `03cf1423` / `053eefeb` / `03cf1423`;
  optimizer/lateral_fetch.py `995f1aa2` clean;
  tests/filters/test_base.py `c702a0cf` / `221362f8` / `c702a0cf`;
  tests/filters/test_inputs.py `9fcf8145` / `873b854b` / `9fcf8145`;
  docs/SPECS/spec-027-filters-0_0_8.md `f87651e1` clean.
  Searched population: every `.py` under
  `django_strawberry_framework/` for the eight mechanism
  vocabularies above, plus the exhaustive production caller census
  of all five symbols. Any fingerprint change reopens this
  finding. Sub-rules: none - the walk half already holds its index
  row (`bound-filter-model-field-walk`, open, queued next); the
  pk-marker reciprocal already holds its row (verified family);
  no new row owed.

## Defects

None filed. Investigated-but-clear (kept so the next cycle does not
re-litigate):

- I1 a consumer `to_field_name` naming no field on the queryset
  model reaches `meta.get_field(to_field_name)` (:1240) with no
  `FieldDoesNotExist` translation: input build fails loud at
  finalize (no silent predicate, no wrong column), tempers only the
  diagnostic type. No contract source establishes a typed
  `ConfigurationError` for THAT input (the documented `None` arm
  covers a missing model, not a bad field; the sibling generation
  failures each name their own input), so per the defect bar this
  is a diagnostic-quality question for the owning spec, not a
  duplication defect. Not filed.

## Pending execution

None. No `proof:` entry is owed: all six challenges are
`static-reviewed` definition counts over closed, grep-enumerated
populations, and a zero-edit verdict owes no failability proof. No
`gate:` witness routes nowhere: full-suite confirmation rides the
plan's final gate. The nine pinning oracles were re-executed green
at WT bytes (9/9; command under `## Implementation (Worker-1)`),
so no execution is deferred.

The `--cell sharded` and `--cell pg` cells are inapplicable by
construction: relation-identity resolution is pure derivation over
in-memory `_meta` (relation shape, queryset model, `extra` keys)
plus in-process value coercion, and reaches no database, alias, or
dialect decision - no member reads a connection, routes a queryset,
or branches on a backend capability, and no claim here depends on
an executed row. The nine package oracles run under the default
cell only (four touch the default test DB through ordinary ORM
reads/writes with no alias decision); none takes an alias/`using=`
or dialect branch, and no claim here varies by backend. The live
rows are cited as already-passing pins, not as runs this item owes.
Worker-2 judges.

## Judgment

CONFIRM, zero-edit: the relation-identity column is already one
rule in one owner (filters/base.py's kernel plus two source
adapters, with the two-link runtime chain composing by name), every
same-token site in the package carrying a distinct contract
recorded above. All six challenges count 1 (C1/C5 at 1 per
contract, C4 at 1 per class); all six matrix axes discharged against
the target's real surface; the nine pinning oracles pass at current
bytes; the three type gates are clean in the item's workspace copy.
No consolidation, no gate, no defect, no new index row is owed.

## Implementation (Worker-1)

Zero-edit: no tracked file changed, no test added, no `## Owned
changes` row owed.

- Item diff vs `ITEM_BASELINE=3cdfe5540d7bced689f084986e4726fa68acc5e6`
  is empty on every item path: both indexed pins equal their BASE
  pins (`77c2e7a6`, `a269a3fe`), HEAD pins `a43513a7` / `d77a113c`,
  dispatch pins reproduced exactly. (Baseline-vs-WT deltas elsewhere
  are Worker-0's dispatch text in `docs/dry/dry-0_0_15.md`,
  concurrent, not this item's.)
- Oracle re-run (the one authorized focused shared-tree run):
  `uv run pytest tests/filters/test_base.py
  tests/filters/test_inputs.py -k "relation_identity_column or
  relation_pk or raw_pk or model_choice_keys" --no-cov -n0 -q` ->
  9 passed, 231 deselected in 5.94s.
- Type gates, all executed in the item's workspace copy
  (`dry/relidcol-f59/consolidate`, slot-2, package digest
  `sha256:3128e46b...`): `basedpyright` -> 0 errors, 0 warnings,
  0 notes (`dry-20261009T193244-e31421`); floor
  (`basedpyright -p pyrightconfig.floor.json`) -> 0/0/0
  (`dry-20261009T193356-5e7a13`); `check_truthful_reads.py --check`
  -> 120 files, 1 exempt, tier-1 0, errors 0
  (`dry-20261009T193509-7bb34d`). `check_public_types.py` not owed:
  zero-edit touches no public symbol. `check_any.py` never run
  (deleted; basedpyright `reportAny` is the Any gate).
- Ruff vacuous: no `.py` path touched, so no `ruff check --fix` /
  `ruff format` run was owed. The artifact carries the
  `<!-- LINK DEFINITIONS -->` scaffold with all 10 group headers
  and no cross-file links.

## Independent verification (Worker-2)

Own trace, recorded from work done before opening `## Findings`
(package-wide mechanism sweep + body reads at WT bytes): the rule
lives in `django_strawberry_framework/filters/base.py` as kernel
`_model_identity_column` (:1230, `meta.pk` / `get_field(to_field_name)`
plus the `ForeignKey`-follow loop :1241-1243) with source adapters
`relation_identity_column` (:1215, `is_relation` gate + `related_model`)
and `model_choice_identity_column` (:1246, queryset-model unless
callable else relation target, plus `extra["to_field_name"]`), and a
runtime chain `_relation_identity_column_for` (:1268, bound-filter
walk + `relation_identity_column`) into `_coerce_relation_identity`
(:1287, chain read + `coerce_field_value_or_none`). Consumers, all by
name: `filters/inputs.py::_relation_identity_annotation` (:364) and
`::_model_choice_identity_annotation` (:397) via the kind-table arms
(:582/:585/:588), and `RelationPkFilter.filter` (:1340) /
`RelationPkMultipleFilter.filter` (:1370) via the chain. Composed
seams owned elsewhere: `_scalar_from_model_field` / `SCALAR_MAP`,
`coerce_field_value_or_none`. My posited changes, each count 1:
follow-shape (kernel), queryset-source precedence (model-choice
adapter), runtime resolution source (chain reader half; the walk
half is a second pair member elsewhere), admittable shape (relation
gate); verdict changes move 0 rule definitions (consumers only);
scalar-table changes move 0 (outside). Owner I would choose:
filters/base.py - the filter-flavor contract both annotation
consumers already import, dependency direction wins over inputs.py
or utils/relations.py. Same-token sites examined and excluded on
body strength: write-side `relation_id_scalar` /
`coerce_relation_pk_or_none`, Relay `_node_id_slot` /
`_coerce_pk_or_none`, leaf-chain key, pk-marker predicate path,
forms `_to_form_key_value`, predicates `_stored_column`, pk-segment
alias expansions, cursor/order/join/plan readers, `canonical_pk`,
`__all__` pk add, `_forward_relation_extra`, field-meta `target`
reads. No second identity-column definition found; zero-edit
CONFIRM anticipated.

Reconciliation, every difference explicit (all record-level; none
moves the verdict):

- R1-R8 + F-10 separation: AGREE on all eight exclusions plus the
  queued-walk split, each re-derived at current WT bytes. Every
  cited site body-read: mutations/inputs.py:463/:528,
  write_values.py:110, relay.py:146/:177, sets.py:327/:1457/:2117/:4216,
  keyset.py:242, write_transaction.py:777, forms/inputs.py:455,
  forms/resolvers.py:165, predicates.py:259/:407, field_meta.py:294,
  permissions.py:528, join_taxonomy.py:256, plans.py:1006,
  nested_planner.py:744, walker.py:875, lateral_fetch.py:358,
  types/relay.py:199, types/base.py:1714, relations.py:889,
  orders/sets.py:831. Each carries a genuine contract difference;
  each trigger is the change that would reunite it.
- D1 oracle census (Worker-2 correction): the package pins are 11,
  not 9 - `tests/filters/test_inputs.py:1460`
  (declared-model-choice follow) and `:1487`
  (model-choice no-column-source) also pin the model-choice adapter
  directly. All 11 re-executed green in my copy (below). The two
  direct-owner tests call the owner as subject with
  independently-spelled expectations (`models.Patron._meta.pk`,
  `is None`); annotation/behavior pins spell literals (`int`,
  `list[int]`, message substrings). Nothing rewritten (zero-edit).
- D2 live rows (Worker-2 correction): at least 5 pin the rule over
  `/graphql/`, not 4 - scalars :215 (exact/in), :235 (membership),
  :259 (reverse FK) plus library :1488 (forward M2M pks) and :1684
  (reverse M2M pks). Cited as already-passing pins, not runs owed.
- D3 line cite (Worker-2 correction): R6's `connection.py:894`
  pk-segment site is at :892 at current bytes; contract as stated.
- D4 freshness supplement (Worker-2): the eight R6-tail modules
  carry no Worker-1 pin. Body-verified by Worker-2 at current bytes;
  pins WT / HEAD / BASE join this finding's freshness set (any
  change reopens): optimizer/plans.py `218be6d2` / `6f2d0c70` /
  `218be6d2`; optimizer/nested_planner.py `a9875bbb` / `73d03184` /
  `a9875bbb`; optimizer/walker.py `57ab6770` / `bc6bc969` /
  `57ab6770`; connection.py `d537ab99` / `b984ca99` / `d537ab99`;
  orders/sets.py `fd453bec` / `2d35adfa` / `fd453bec`;
  types/relay.py `14f79e02` / `f1c0c6f4` / `14f79e02`;
  types/base.py `f42bcee3` / `a63b7edf` / `f42bcee3`;
  utils/relations.py `cc68c6ba` / `63f46750` / `cc68c6ba`. All 16
  Worker-1 pins reproduced exactly at current bytes (no drift).
- D5 C4 bundling: accepted with note - two sub-changes bundled
  ("match-none to raise", "member drop to reject"), each count 1
  per class (scalar vs membership verdicts are cardinality-specific;
  shared `_match_none_queryset` owned once); rule definitions move
  0. C1/C2/C3/C5/C6 counts confirmed as stated (C1 "1 per contract"
  holds: the predicates walk moves only on a storage-proof change,
  verified at predicates.py:407-411).
- D6 "5 definitions" vocabulary: accepted with note - adapters and
  chain links compose the kernel by name (consumers in DRY
  vocabulary); the operative evidence, per-axis counts of 1 with
  the C3 walk-half split to queued F-10 and the C5 gate-contract
  split, is correct.
- Matrix axes 1-6: all six discharges AGREE. Axis 2 async absence
  re-grepped (0/0 in base.py/inputs.py). Axis 4 round-trip holds
  (both halves read the trio; GlobalID halves share the single
  `resolve_globalid_target_definition`, base.py:809, composed at
  :806 and finalizer.py:2070). Axis 6 omission enumeration holds
  (`RelatedFilter` a branch per its class contract; ModelChoice
  runtime cleaning stays in django-filter's form field per the
  trio docstring :1250-1259 and spec-027).
- Item-scoped diff: EMPTY, confirmed independently (`git diff
  3cdfe5540d7bced689f084986e4726fa68acc5e6` over both indexed paths
  prints nothing; BASE pins equal WT pins; no new production file -
  untracked `_multipart.py`/`lazy.py`/`truth.py` are the concurrent
  truth migration, predating the baseline). WT-vs-HEAD dirt on both
  targets is truth-migration + hostile-guard concurrent work by
  diff content (17 base.py hunks, 18 inputs.py hunks, all outside
  :1215-1297); trio region byte-identical HEAD-vs-WT (independent
  `cmp` clean); HEAD def lines 1253/1268/1284/1306/1325 reproduced.
- Observable equivalence: nothing owed (zero-edit proposes no
  behavior change); `static-reviewed` is the correct proof status
  for definition counts over closed, grep-enumerated populations.
- Pending execution: EMPTY, confirmed nothing owed. Cells
  inapplicable by construction, reason judged sound: pure `_meta`
  derivation plus in-process coercion, no connection/alias/dialect
  read; DB-touching behavior pins use the default test DB with no
  alias decision.
- Structural gate: none owed, AGREE - mechanism tokens are shared
  across eight lawful contracts, so a token census either
  false-positives or becomes a bespoke per-helper existence test;
  behavioral pins (direct-owner, annotation, coercion, live-wire)
  are the durable protection.
- I1 investigated-but-clear: ENDORSED - bad `to_field_name` fails
  loud at input build; no contract source requires a typed error
  for that input; below the defect bar.
- AGENTS.md prose rules on the item diff: empty set (no `.py`
  touched) - stated explicitly, no violation possible. Ruff:
  empty set, no run owed. Artifact scaffold: `<!-- LINK
  DEFINITIONS -->` with all 10 group headers present, zero
  cross-file links; raw `path:NN` allowed (per-cycle scratchpad).

Gate re-runs, all in Worker-2's own copy
(`dry/relidcol-f59/verify-1`, slot-3, package digest
`sha256:3128e46b...` identical to Worker-1's, copy fresh, shared
unmoved): oracles `pytest tests/filters/test_base.py
tests/filters/test_inputs.py -k "relation_identity_column or
relation_pk or raw_pk or model_choice_keys or
declared_model_choice_filter_follows or
model_choice_filter_with_no_column_source" --no-cov -n0 -q` ->
11 passed, 229 deselected (`dry-20261009T194806-b49c48`);
`basedpyright` -> 0 errors, 0 warnings, 0 notes
(`dry-20261009T194819-4030c0`); floor (`-p
pyrightconfig.floor.json`) -> 0/0/0 (`dry-20261009T194932-aad35c`);
`check_truthful_reads.py --check` -> 120 files, 1 exempt, tier-1
0, errors 0 (`dry-20261009T195043-2f0ecf`). `check_public_types.py`
not owed (zero-edit, no public symbol touched). `check_any.py`
never run (deleted).

Verdict: `verified`, plain (no `proof:` entry remains). No new
index row owed (F-10 already rowed open; R5 reciprocal confirmed
in the marker artifact's carried-evidence section; no sub-rule
found). No defect filed.

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
