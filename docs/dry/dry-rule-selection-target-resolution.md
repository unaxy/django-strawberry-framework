# DRY review: `selection-target-resolution`

Status: verified
Run: 0.0.15 2026-10-09-13

## System trace

Run-13 re-trace at HEAD `23b5f421` + WT (the run-12 record below is
preserved; every line number and pin re-derived at current bytes).
WT line numbers throughout unless marked HEAD. WT/HEAD offsets vary
by region (the WT/HEAD walker diff is +32/-25): through the family
each WT line sits one before HEAD's (the +1 `truth` import is
outweighed by a -2 log hunk above); the spend sites drift further
(first call WT :832 / HEAD :828, fallthrough WT :861 / HEAD :857,
second call WT :1643 / HEAD :1636).

The rule, re-derived fresh at current bytes: plan-time resolution of one
GraphQL selection name to its Django target across TWO namespaces -
synthesized relation connections, then model fields - from one built table.
`django_strawberry_framework/optimizer/walker.py::_resolve_selection_target`
(WT walker.py:428; HEAD :429) answers the exact `snake_case` reversal first in each
namespace (connection slot, WT :444, before field map, WT :447);
on a miss it reads the forward table (WT :450), where a connection
outranks a model field of the same GraphQL name (WT :457), then the
fields half (WT :460). Unknown names answer `None` and the caller
keeps the reversed name for the Relay custom-pk `id` branch
(WT :861).

All nine nominated members are present in the walker with the nominated
responsibilities (WT def lines; HEAD def one line later through the
family: 268 / 273 / 297 / 319 / 322 / 334 / 360 / 410 / 429):

- `_schema_name_converter` (WT :267) - the schema's `NameConverter`
  from planner/resolver `info`, `None` passing through.
- `_graphql_names_by_python_name` (WT :272) - authoritative published
  names per Strawberry field: `converter.get_graphql_name(field)` when a
  converter is present, else per-field explicit-`graphql_name`-or-camel
  (WT :291). Skips fields with no `python_name` (WT :286).
- `_ForwardNames` (WT :296) - the one record: converter held
  strongly, `connections` GraphQL-name-to-relation map, `fields`
  GraphQL-name-to-`(django_name, field)` map.
- `_forward_names_memo` (WT :318) - per-`(type_cls, id(converter))`
  entries; the value holds its converter so the `id` key cannot be reused
  while the entry lives (WT :311).
- `clear_forward_names` (WT :321) plus the bus registration
  (WT :330, `owner="optimizer.forward_names"`).
- `_build_forward_names` (WT :333) - the two `setdefault` loops over
  the same iterations in the same order: connections from
  `relation_connections` (WT :342, authoritative name or
  `to_camel_case`), fields from `field_map` (WT :348, skipping
  nameless metadata). First declaration wins in both.
- `_forward_names` (WT :359) - memoized only for a FINALIZED
  definition plus a present converter (WT :386); the memoized build
  reads `definition.relation_connections` (WT :401) while the
  uncacheable build spends the caller's map (WT :390). Insert-only
  (WT :405); every other read is `.get`.
- `_field_by_graphql_name` (WT :409) - reads the fields half. It
  passes `{}` connections, which the memoized path ignores in favour of
  the definition's slot (WT :401) under the same key both readers
  share, so both readers land on one entry; the uncacheable path builds
  empty connections the caller never reads.
- `_resolve_selection_target` (WT :428) - the consolidated resolver
  above.

Two production spend sites, both in-module, both composing by name:
`_walk_selections` (WT :832, both namespaces) and
`_selected_scalar_names` (WT :1643, fields half only - the helper
walks a single-valued relation's child scalars for FK-id elision, and a
connection child answers `None` below regardless, WT :1652, so the
absence can only decline the elision, never misplan it).

Whole-package mechanism census (every hit inspected; literal searches
except where marked regex): `snake_case(` calls - WT walker.py:443, :861,
:1630 plus the `utils/strings.py::snake_case` definition (:120) and one
prose mention (:866), zero elsewhere; `converter.get_graphql_name(` -
walker.py:289 only (the two selections.py hits at :624/:633 are prose);
`apply_naming_config(` code - selections.py:649 only (:641 is the
`getattr` fetch, the rest prose); `to_camel_case(` code - walker.py:292,
:345, :354, finalizer.py:241, :246, :252, :742, mutations/inputs.py:220;
`name_converter` reads - walker.py:269 (the helper), selections.py:639
(inline), inspect_django_type.py:151 (config-sourced, default-converter);
`relation_connections` code reads - walker (fast path :444, build :342,
memoized :401, root :815), finalizer (its own slot :521, teardown
:559, synthesis :606/:1033), inspect_django_type (sibling render :374,
no GraphQL vocabulary), definition.py:213 (the declaration). The nine
family symbols occur in production only in the walker; the only other
mentions are two docstring citations (selections.py:617,
strings.py:136) and the test pins below. The nested planner carries no
resolution machinery: one comment block (nested_planner.py:1315) and one
by-name consumer call `connection_field_names(info)`
(nested_planner.py:1321).

Lifetime (principle 4), re-verified link by link at current bytes: owner
the walker; validity key `(type_cls, id(converter))` with the type held
by the key and the converter held strongly by the value; publish point
`_forward_names` on finalized-plus-converter calls only; insert-only,
readers `.get`; invalidated by `registry.clear()` through the subsystem
bus. Premise chain: synthesis runs before the finalized flip
(finalizer.py:1033 before :1141, with `strawberry.type` at :1140 and the
surface audit at :1132 between them; synthesis skips finalized types,
finalizer.py:664); `field_map` is write-once (the single
`DjangoTypeDefinition(` construction at types/base.py:850 fed by the
comprehension at :692, plus the walker fallback comprehension at
walker.py:502; every `field_map[` hit package-wide is a read, and no
`.field_map =` / `update` / `pop` / `setdefault` / `clear` exists);
`relation_connections` post-flip mutation runs only from the registered
type teardown (finalizer.py:559, registered via finalizer.py:603 from
synthesis at finalizer.py:792); `registry.clear()` runs type teardowns
first (registry.py:654), drops the definitions (registry.py:660), then
fans out the subsystem clears including this memo (registry.py:672),
while every other mutator honours `_check_mutable`. Uncacheable calls
build fresh.

Walker dirt attribution (every hunk of the +32/-25 WT/HEAD diff, by
content): the `truth` import (:17) plus eight `truth.name` /
`truth.static_attr` / `truth.is_subclass` hunks (plan_relation log :235,
`_graphql_names_by_python_name` :277, `_hook_info` :572, the id-branch
:886 with its `node_cls` widening, three `_apply_hint` messages, the pk-set
message :1535) are the external truth migration (one lands inside this
family at :277, untouched by this zero-edit item); the
`target_model=` to `target_definition=` threading plus seal docstrings
(`_build_child_queryset`, `_build_connection_child_queryset`,
`_build_prefetch_child_queryset`, `_scoped_hint_prefetch`) are f56's
ledgered `prefetch-child-build-seam` consolidation. The D1 seal-policy
row is committed at HEAD (walker imports plus the `_LIST_RELATION_CHILD_POLICY`
default). No other hunk touches the nine members.

## Verification

### Matrix

1. Cross-flavor: no second walk exists (single `_walk_selections`
  at walker.py:764; the write-side input flavors resolve through
  precomputed `InputFieldSpec.graphql_name` declarations consumed by key,
  never through schema-converter resolution - mutations/resolvers.py:516,
  :545, write_values.py:371, rest_framework/resolvers.py:392,
  rest_framework/inputs.py:1051, :1370, forms/inputs.py:712,
  extensions/resource_policy.py:346, :361, utils/errors.py:322,
  utils/inputs.py:1243 (the audit); filters/sets.py and forms/resolvers.py
  carry no `.graphql_name` consumer and no converter/caser machinery at
  current bytes - verified by zero-hit grep). The nested planner holds
  no twin (one by-name consumer call above). Discharged.
2. Sync/async: zero `async def` / `await` in the walker (re-grepped);
  the rule is pure plan-time resolution with no await boundary, so no
  twin can exist. Discharged.
3. Derived knowledge: every same-token site inspected on body strength
  (finalizer prediction, selections vocabulary, mutation audits/specs,
  field-map fallback, sibling render, extension audit,
  `_field_meta_for_resolver`, spec readers) - each carries a distinct
  contract in `## Findings` R1-R6, none a second definition.
  Discharged.
4. Round-trip: the lossy reversal (`snake_case`) and the forward table
  are composed inside ONE body (`_resolve_selection_target`: fast path
  then table), not split across modules; the write-side reverse map
  (`mutations/inputs.py::relation_input_python_attr` at :558, verified
  family `mutation-input-reverse-map`) runs over input attrs, a different
  population. Discharged.
5. Other media: oracles spell literal wire names and columns, never
  read the owner's table (the build-count spy counts invocations of
  the table INPUT; every verdict assertion pins literals). Projections:
  the `snake_case` docstring cite (strings.py:136), the selections
  docstring cite (selections.py:617), spec-033 Decision 3
  (metadata-driven connection recognition, citing
  `_resolve_selection_target` against `relation_connections` plus the
  forward maps), the finalizer fall-through clause (finalizer.py:644).
  No medium carries a second definition. Discharged.
6. Omission: the selection-name consumers are exactly the two spend
  sites (package-wide `snake_case(` census above; `get_graphql_name`
  census one site). `_selected_scalar_names` omits the connection
  namespace by documented construction and fails safe to `None`
  (WT :1652). The unknown-name fallthrough (WT :861) keeps
  the reversed name for the Relay `id` branch, then skips. No member
  lacks a guard the rule owes it. Discharged.

### Enumeration

Instrument: `muse.search` over `django_strawberry_framework/` for the
rule's mechanism vocabulary (`snake_case(`, `get_graphql_name`,
`apply_naming_config`, `to_camel_case`, `name_converter`,
`relation_connections`, all nine family symbols), plus definition
reads of every hit, plus exhaustive `.graphql_name` (23 hits) and
`graphql_camel_name` censuses for the write-side population. Count: 9/9
nominated members present, all in the walker; 2 in-module spend sites; 0
production readers outside the walker. Examined-and-excluded, each on body
strength:

| Site | Verdict |
|---|---|
| Nested planner connection-vocabulary read | consumer by name, no machinery |
| Finalizer `_field_surface_names` + synthesis guard | R1: pre-decoration prediction, default converter |
| Selections `connection_field_names` | R2: structural vocabulary, no field objects |
| Mutation input audit + spec build | R3: write-side, bind-time, deliberate casers |
| Field-map fallback (`_resolve_field_map`) | R4: input population, not resolution |
| `spec.graphql_name` readers (8 modules, re-derived) | R5: precomputed declarations |
| inspect sibling render, extension audit, `_field_meta_for_resolver` | R6: python-name space, no wire vocabulary |
| Relay/globalid decoders | excluded: type-name-plus-pk, not field selection |

### Challenges

Each axis moves exactly one definition; both spend sites compose by
name and move on none. Consumers, oracles, projections listed, never
counted.

- C1 lossy-name recovery (a new unrecoverable spelling, a digit
  boundary, an explicit `name=`): `_build_forward_names` moves once
  (the two fallback arms, WT :345, :354); the authoritative
  read is untouched (it delegates to the converter). Count 1.
- C2 namespace precedence (fields before connections, or a third
  namespace): `_resolve_selection_target` moves once (WT :457).
  Count 1.
- C3 first-declaration-wins (last-wins, or a collision raise): the
  two `setdefault` loops move once (WT :346, :355). Count 1. (Valid
  schemas cannot reach a tie: `_audit_field_surface` rejects
  camel-colliding fields at finalization, finalizer.py:266.)
- C4 memo validity (key by definition, a new invalidation event):
  `_forward_names` moves once (WT :386); both readers keep
  their call shape. Count 1.
- C5 authoritative-name source (a new Strawberry field slot, a new
  converter method): `_graphql_names_by_python_name` moves once
  (WT :272). Count 1.
- C6 converter-fetch sharing (one helper for the walker fetch, the
  selections inline line, the inspect read): REJECTED - three sites,
  three `None` contracts (per-field fallback here at WT :288, default
  vocabulary in selections at :646, default converter in inspect at
  :151); the shared token is Strawberry's attribute name, not a package
  rule, and each site's `None` arm moves alone. Count 1 per contract.
  Carried as R2's trigger.

Proof status: all six `static-reviewed` (definition counts over
closed, grep-enumerated populations; zero-edit, so no equivalence is
owed). The rule's current hold is additionally execution-verified:
the six package oracles pinning it pass 6/6 at WT bytes
(`uv run pytest tests/optimizer/test_walker.py -k "forward_name or
name_resolution or explicitly_named_fields or
digit_boundary_relation_connection" --no-cov -n0 -q`).

## Findings

### F1 `selection-target-resolution` - CONFIRMED single-owned, zero-edit

- Contract + variation: plan-time GraphQL-selection-name to Django
  target across the connection and field namespaces; exact reversal
  fast path, memoized forward table on a miss, connections before
  fields, first declaration wins. Varies on recovery spelling (C1),
  precedence (C2), tie-break (C3), memo validity (C4), name source
  (C5).
- Sites + roles: 9 definitions, all in `optimizer/walker.py` (one
  rule, one module). Consumers: `_walk_selections`,
  `_selected_scalar_names` (in-module, by name). Oracles:
  `test_plan_uses_exact_graphql_names_for_explicitly_named_fields`,
  `test_name_resolution_defensively_skips_unusable_metadata`,
  `test_forward_name_maps_build_once_per_type_and_converter`,
  `test_forward_name_maps_answer_per_schema_converter`,
  `test_forward_name_maps_wait_for_finalization`,
  `test_plan_projects_digit_boundary_relation_connection_as_windowed_prefetch`
  (all in tests/optimizer/test_walker.py at :540, :575, :630, :676,
  :715, :3200), plus the live rows
  `test_edition_digit_boundary_names_project_their_own_django_columns`,
  `test_patron_profile_explicitly_named_fields_each_return_their_own_column`,
  `test_publisher_printings_2_connection_pages_from_one_partitioned_window`,
  `test_distributor_mixed_case_scalar_projects_its_own_column`,
  `test_consignment_mixed_case_forward_key_joins_its_target_in_one_statement`,
  `test_distributor_mixed_case_reverse_relation_loads_through_one_prefetch`
  (test_query/test_library_shapes_api.py at :143, :169, :318, :427,
  :450, :479). Projections: the two docstring cites, spec-033 Decision 3,
  the finalizer fall-through clause (Matrix axis 5).
- Challenges: C1-C5 count 1 each, C6 rejected at 1 per contract
  (`### Challenges`).
- Owner + lifetime: `optimizer/walker.py`, the current home, by
  principle 7. The contract (what a plan-time selection means),
  both consumers, both resolved-into maps, and the enforcement
  authority (the walk) all live there; no legitimate consumer
  outside it exists. Alternatives rejected: selections.py (lower;
  AST-only by design - hosting the table would drag
  DjangoType/registry/FieldMeta machinery beneath the layer that
  deliberately lacks it, reversing the dependency the table's
  readers already follow); any `utils/` module (both consumers are
  in the walker, so an extraction serves nobody); the finalizer
  (wrong time: pre-decoration, no schema converter exists);
  types/base (registration time, no `info`). Lifetime as traced
  above: `(type_cls, id(converter))` key, converter held strongly,
  finalized-plus-converter publish, insert-only, bus invalidation.
- Migration: none - the rule already reads as one table composed by
  name at both spend sites.
- Distinct behavior (rejections, each with contract difference,
  trigger, durable home):
  - R1 finalizer prediction vs walker table: same direction,
    opposite times. The finalizer predicts pre-decoration names
    under the DEFAULT converter because no schema exists at
    finalization; the walker resolves post-decoration names
    through the ACTIVE converter. A custom-converter rename
    moves the walker only; a new synthesis collision shape moves
    the finalizer only. Trigger: finalization gains schema
    access (or must predict a non-default converter exactly).
    Home: finalizer.py:644 (fall-through clause, existing).
  - R2 selections vocabulary vs walker table: different subjects
    and converter methods. The walker resolves MODEL names
    holding StrawberryFields (explicit-name aware, per-field
    fallback); selections resolves five FRAMEWORK-OWNED
    structural names without field objects
    (`apply_naming_config` over python names, whole-record
    default). The shared one-line converter fetch carries a
    third `None` contract at the inspect read. Trigger: a
    selection walk holds StrawberryFields (or must reproduce
    owning-type renames). Home: selections.py:612 (difference +
    limitation, existing).
  - R3 mutation input audit/spec build vs walker table: write
    side, bind/materialization time, deliberately converter-free
    (the audit predicts with Strawberry's caser by documented
    design, mutations/inputs.py:203; the spec build names with
    the package caser, mutations/inputs.py:604). A schema-naming
    change moves the walker only. Trigger: input specs resolve
    through the active schema converter. Home:
    mutations/inputs.py:203 (existing).
  - R4 field-map fallback vs resolution: the fallback builds an
    INPUT population (all model fields at plan time for
    unregistered models, walker.py:502), not a resolution; every
    C1-C5 axis moves it at count 0. Key-grammar questions stay
    with the standing rejected row
    `walker-fallback-vs-registration-field-map` (population plus
    time, registry-coverage-gate trigger) - referenced, not
    re-litigated. Home: walker.py:467 (policy prose, existing).
  - R5 `spec.graphql_name` readers vs walker table: precomputed
    write-side declaration names consumed by key across eight
    modules (re-derived: the run-12 filters/sets + forms/resolvers
    members are gone at current bytes; neither file carries a
    `.graphql_name` consumer or any converter machinery now) -
    no request-time resolution anywhere on those paths. Trigger:
    a spec name computed from the schema converter at request
    time. Home: this artifact (code shape is the statement; no
    prose owed for a non-duplication).
  - R6 python-space reads vs walker table: the inspect sibling
    lookup (inspect_django_type.py:356), the extension
    unregistered-target audit (extension.py:1474), and
    `_field_meta_for_resolver` (resolvers.py:408) all match
    python names to metadata with zero GraphQL vocabulary.
    Trigger: any of them starts matching wire names. Home: this
    artifact, same standing as R5.
- Behavioral proof: `static-reviewed` for all six challenges (no
  behavior change proposed); the six pinning oracles additionally
  re-executed green at WT bytes (command under `### Challenges`),
  which also covers the external truth-migration hunk inside
  `_graphql_names_by_python_name`.
- Structural gate: none owed. The owner is private, single-module,
  both spend sites in-module; any new selection walk routes
  through the single `_walk_selections` (Matrix axis 1), so no
  plausible bypass population exists. A census pinning today's
  one-site mechanism counts would be a bespoke existence test per
  helper, which the method forbids; the durable protection is the
  existing behavioral pins (build count, per-converter answers,
  finalization gating, the clear, the digit-boundary window
  oracle, the live rows) plus this artifact's censuses as the
  re-derivation baseline.
- Coupling: none. No other family, no defect, no pending input.
- Freshness: HEAD `23b5f421` (detached, intended).
  `ITEM_BASELINE=6be1a0e32928813a8d3df729451b5e69d44cc617` (taken on
  `23b5f421`; the baseline tree carries the WT dirt, so every BASE pin
  below equals its WT pin and the item-scoped diff is empty). Pins are
  WT / HEAD / BASE, 8 chars (`git hash-object`; BASE via
  `git show <baseline>:<path>`):
  walker.py `57ab6770` / `bc6bc969` / `57ab6770` (dispatch pins
  reproduced exactly); selections.py `e14e6e30` / `d8dc9d52` /
  `e14e6e30`; nested_planner.py `a9875bbb` / `73d03184` / `a9875bbb`;
  extension.py `49346716` / `e18210e5` / `49346716`; finalizer.py
  `8f699081` / `5934789a` / `8f699081`; types/base.py `f42bcee3` /
  `a63b7edf` / `f42bcee3`; types/resolvers.py `cab17014` / `10df9ea7`
  / `cab17014`; types/definition.py `dfad92ca` / `2562cb6f` /
  `dfad92ca`; registry.py `c5aa2050` / `47b52c52` / `c5aa2050`;
  utils/typing.py `b7e69600` / `3a5dae39` / `b7e69600`;
  utils/strings.py `0b1774a7` / `1a49fe42` / `0b1774a7`;
  utils/connections.py `2313fce5` clean; mutations/inputs.py
  `bb329e4d` / `f821661e` / `bb329e4d`; mutations/resolvers.py
  `9171b93f` / `bb6c630d` / `9171b93f`; connection.py `d537ab99` /
  `b984ca99` / `d537ab99`; inspect_django_type.py `77eaff4f` /
  `86a308ab` / `77eaff4f`; tests/optimizer/test_walker.py `cf679cf2`
  / `5c450c3e` / `cf679cf2`;
  test_query/test_library_shapes_api.py `bad9ef33` clean.
  Searched population: every `.py` under
  `django_strawberry_framework/` for the seven mechanism
  vocabularies above, plus the exhaustive `.graphql_name` (23 hits)
  and `graphql_camel_name` censuses. Any fingerprint change reopens
  this finding. Sub-rules: the memo/clear already holds its index row
  (`forward-name-memo-clear-row`, file-local, lawful convergence
  onto verified `subsystem-clear-lifecycle`); the selections
  vocabulary is single-owned inside verified File
  `optimizer/selections.py` scope - no new row owed for either.

## Defects

None filed. Investigated-but-clear (kept so the next cycle does not
re-litigate):

- I1 `_field_by_graphql_name` passes `{}` connections (WT :420) while the
  memoized `_forward_names` path reads the definition's slot (WT :401):
  the caller reads the fields half only, under the same memo key both
  readers share, so both land on one entry. Consistent by
  construction, not a divergence.
- I2 `_forward_names` fetches the converter at WT :385 and
  `_graphql_names_by_python_name` fetches it again at WT :278
  on the uncached path: a pure repeated read answering identically,
  not a second definition.

## Pending execution

None. No `proof:` entry is owed: all six challenges are
`static-reviewed` definition counts over closed, grep-enumerated
populations, and a zero-edit verdict owes no failability proof. No
`gate:` witness routes nowhere: full-suite confirmation rides the
plan's final gate. The six pinning oracles were re-executed green
at WT bytes (6/6; command under `### Challenges`, result under
`## Implementation (Worker-1)`), so no execution is deferred.

The `--cell sharded` and `--cell pg` cells are inapplicable by
construction: selection-target resolution is pure derivation over
in-memory mappings (`field_map`, `relation_connections`, Strawberry
field metadata) plus the schema's name converter, and reaches no
database, alias, or dialect decision - no member reads a connection,
routes a queryset, or branches on a backend capability, and no claim
here depends on an executed row. The six package oracles run
`plan_optimizations` in-process (registry + `_meta` only, zero
queries); the live rows execute real queries but only under the
default suite, and this verdict cites them as already-passing pins,
not as runs this item owes. Worker-2 judges.

## Judgment

CONFIRM, zero-edit: forward selection-target resolution is already
one rule in one owner (`optimizer/walker.py`), with every
same-token site in the package carrying a distinct contract
recorded above. All six challenges count 1 (C6 rejected at 1 per
contract); all six matrix axes discharged against the target's real
surface; the six pinning oracles pass at current bytes; the three
type gates are clean in the item's workspace copy. No consolidation,
no gate, no defect, no new index row is owed.

## Implementation (Worker-1)

Zero-edit: no tracked file changed, no test added, no `## Owned
changes` row owed.

- Item diff vs `ITEM_BASELINE=6be1a0e32928813a8d3df729451b5e69d44cc617`
  is empty on every item path: walker WT pin `57ab6770` equals its
  BASE pin, HEAD pin `bc6bc969`, dispatch pins reproduced exactly,
  status count 514 unmoved. (The only baseline-vs-WT delta anywhere
  is Worker-0's +39 dispatch text in `docs/dry/dry-0_0_15.md`,
  concurrent, not this item's.)
- Oracle re-run (the one authorized focused shared-tree run):
  `uv run pytest tests/optimizer/test_walker.py -k "forward_name or
  name_resolution or explicitly_named_fields or
  digit_boundary_relation_connection" --no-cov -n0 -q` →
  6 passed, 193 deselected in 0.84s.
- Type gates, all executed in the item's workspace copy
  (`dry/seltarget-f57/consolidate`, slot-2, package digest
  `sha256:3128e46b...`): `basedpyright` → 0 errors, 0 warnings,
  0 notes (`dry-20261009T183732-976bdb`); floor
  (`basedpyright -p pyrightconfig.floor.json`) → 0/0/0
  (`dry-20261009T183845-58a8f6`); `check_truthful_reads.py --check`
  → tier-1 0, errors 0 over 120 files, 1 exempt
  (`dry-20261009T183958-464520`). `check_public_types.py` not owed:
  zero-edit touches no public symbol. `check_any.py` never run
  (deleted; basedpyright `reportAny` is the Any gate).
- Ruff vacuous: no `.py` path touched, so no `ruff check --fix` /
  `ruff format` run was owed. The artifact's
  `<!-- LINK DEFINITIONS -->` block is preserved verbatim and no new
  cross-file link was added.

## Independent verification (Worker-2)

Pass 1, run 13, HEAD `23b5f421`, ITEM_BASELINE
`6be1a0e32928813a8d3df729451b5e69d44cc617`. Method note: the
required full-file read exposed `## Findings` before my trace was
complete, so every figure below was re-derived with my own commands
against current bytes; reproduction is by re-execution, not by
agreement. Line numbers are WT unless marked HEAD.

### My trace (before reconciliation)

The rule as I derive it from the walker: plan-time resolution of one
GraphQL selection name to its Django target across two namespaces
(synthesized relation connections, then model fields) from one built
table, with exact `snake_case` reversal as fast path and the forward
table on a miss, connections outranking fields.

Sites (all WT `django_strawberry_framework/optimizer/walker.py`):
`_schema_name_converter` (:267), `_graphql_names_by_python_name`
(:272), `_ForwardNames` (:296), `_forward_names_memo` (:318),
`clear_forward_names` (:321) + bus registration (:330),
`_build_forward_names` (:333), `_forward_names` (:359),
`_field_by_graphql_name` (:409), `_resolve_selection_target` (:428).
9/9 nominated members present with the nominated responsibilities;
all nine in this one module.

Roles: the nine are one rule's definition machinery (one definition
set, not nine rules). Consumers, both in-module and both composing by
name: `_walk_selections` (:832, both namespaces) and
`_selected_scalar_names` (:1643, fields half only; a connection child
answers `None` at :1652 and can only decline the FK-id elision, never
misplan it). Oracles: the six `tests/optimizer/test_walker.py` pins
plus the six live `test_library_shapes_api.py` rows. Projections: the
two docstring cites (`utils/strings.py:136`,
`optimizer/selections.py:617`), spec-033 Decision 3, the finalizer
fall-through clause.

Definition counts per posited change (my own challenges): recovery
spelling moves `_build_forward_names` only (1); namespace precedence
moves `_resolve_selection_target` only (1); tie-break moves the two
`setdefault` loops in `_build_forward_names` (1); memo validity moves
`_forward_names` only (1); name source moves
`_graphql_names_by_python_name` only (1); converter-fetch sharing is
rejected at 1 per contract (three distinct `None` contracts: per-field
fallback at walker :288, whole-record default at selections :646,
default converter at inspect :151).

Owner I would choose: `optimizer/walker.py`, the current home. The
contract (what a plan-time selection means), both consumers, both
resolved-into maps, and the enforcement authority (the walk) all live
there; no legitimate consumer outside it exists. Rejected on
responsibility: selections.py (lower, AST-only; hosting the table
would drag DjangoType/registry/FieldMeta machinery beneath the layer
that deliberately lacks it); any `utils/` module (both consumers are
in the walker, so an extraction serves nobody); the finalizer (wrong
time: pre-decoration, no schema converter); types/base (registration
time, no `info`).

### Reconciliation

Every check below re-executed by me; all agree with the artifact
unless noted.

- (a) Item-scoped diff: EMPTY. `git diff 6be1a0e3... --stat` shows
  exactly one file, `docs/dry/dry-0_0_15.md` (+41, Worker-0's dispatch
  text, concurrent, not this item's). No new file owes review: the
  artifact predates this pass (run-12 record). Blob-level: WT == BASE
  on all 18 pinned files (my recomputation under (j)).
- (b) Zero-edit consolidation search: I swept the package for a real
  consolidation before accepting. Package-wide mechanism censuses,
  every hit inspected: `snake_case(` calls at walker :443, :861,
  :1630 + definition + one prose mention, zero elsewhere;
  `converter.get_graphql_name(` at walker :289 only (two selections
  hits are prose); `apply_naming_config` code at selections :649 only;
  `to_camel_case(` code exactly at walker :292/:345/:354,
  finalizer :241/:246/:252/:742, mutations/inputs :220;
  `name_converter` reads at walker :269, selections :639,
  inspect :151 (+ threading params, no new reads);
  `relation_connections` code reads exactly at walker :444/:342/:401/
  :815, finalizer slot/teardown/synthesis, inspect :374,
  definition :213; `.graphql_name` exactly 23 hits; zero
  `async def`/`await` in the walker; single `_walk_selections`.
  The nine family symbols occur in production only in the walker.
  No second resolution site exists anywhere. CONFIRM zero-edit.
- (c) Enumeration member by member: 9/9 members, 2 spend sites, 0
  outside production readers — reproduced. Each excluded row read on
  body strength: nested planner (comment + one by-name
  `connection_field_names(info)` call at :1321, no machinery);
  finalizer prediction (R1); selections vocabulary (R2); mutation
  audit + spec build (R3); field-map fallback (R4); the eight
  `spec.graphql_name` reader modules (R5); inspect/extension/resolvers
  python-space reads (R6); relay decoders (type-name-plus-pk).
  One widening note: my sweep found bare `graphql_name` str params
  threaded through forms/resolvers.py — the artifact's claim is the
  precise one ("no `.graphql_name` consumer or converter machinery"),
  which holds; no dotted read and no caser/converter in either
  run-12-dropped file.
- (d) Matrix axes judged against the real surface: (1) write-side
  resolves through precomputed `InputFieldSpec.graphql_name` keyed
  reads, never schema-converter resolution — discharged. (2) No await
  boundary exists — discharged. (3) Every same-token site carries a
  distinct contract (R1-R6, bodies read) — discharged. (4)
  Reversal + forward table composed in ONE body; the write-side
  reverse map runs over input attrs — discharged. (5) Oracles pin
  literals (spot-read: the build-count spy wraps the table INPUT and
  every verdict asserts literal columns; the `_forward_names_memo ==
  {}` read asserts an externally-visible clear contract against a
  literal, not expected values derived from the owner) — discharged.
  (6) Exactly the two spend sites; the connection-namespace omission
  in `_selected_scalar_names` is documented and fails safe; the
  unknown-name fallthrough keeps the reversed name for the Relay `id`
  branch — discharged. No axis excuses another; no consolidation was
  found to excuse anything with.
- (e) Challenges: C1-C5 count 1 each, C6 rejected at 1 per contract —
  my independent counts match exactly. C3's parenthetical verified:
  `_audit_field_surface` (finalizer :266) raises on distinct-python-
  name camel collisions.
- (f) Observable equivalence (principle 8): zero-edit proposes no
  behavior change, so no equivalence is owed; all six challenges are
  `static-reviewed` definition counts over closed, grep-enumerated
  populations. No failability proof is owed by a verdict that moves
  nothing.
- (g) Sharded/pg inapplicability: ACCEPTED on its reason. I read all
  nine member bodies: pure derivation over in-memory maps plus the
  schema converter, zero database/alias/dialect surface. The six
  package oracles run `plan_optimizations` in-process (registry +
  `_meta`, zero queries — verified in the test bodies); the live rows
  are cited as already-passing pins, not runs this item owes.
- (h) Rejections: R1-R6 each carry contract difference +
  reconsideration trigger + durable home. R1 fall-through clause
  (finalizer :644-649), R3 audit design note (mutations/inputs :203),
  R2 limitation (selections :612), R4 standing-row reference, R5/R6
  artifact standing — all verified at their cites. Spec-033 Decision 3
  projection verified in the spec text (metadata-driven recognition
  through `_resolve_selection_target`).
- (i) Lifetime premise chain re-verified link by link: synthesis
  :1033 before audit :1132 before `strawberry.type` :1140 before the
  finalized flip :1141; skip-finalized guard :664; `field_map`
  write-once (single construction at types/base :850 fed by :692;
  all seven package-wide `field_map[` hits are reads; no
  `.field_map =` / update / pop / setdefault / clear); post-flip
  `relation_connections` mutation only from the registered teardown
  (:559-562, registered :603, called from synthesis :792);
  `registry.clear()` runs teardowns, drops definitions, then fans out
  subsystem clears; every other mutator honours `_check_mutable`.
  Citation nit (substance verified, no verdict impact): the registry
  pins read :660/:672 in the artifact; WT bytes show the definitions
  drop at :659 and the subsystem fan-out at :668-669.
- (j) Freshness: all 18 WT/HEAD/BASE pins re-hashed by me reproduce
  EXACTLY (walker `57ab6770`/`bc6bc969`/`57ab6770`, dispatch pins
  included; both "clean" claims confirmed triple-equal). BASE == WT
  throughout, confirming (a) at the blob level. Coverage note: the 18
  pins cover every definition/consumer/oracle/lifetime module plus the
  R1-R4/R6 bodies; the eight R5-reader/relay-decoder modules excluded
  on body strength ride the stated searched-population censuses. I
  close that tripwire gap with verifier-side pins rather than a
  re-pass (modules I inspected in my own trace; WT/HEAD/BASE):
  relay.py `9257a51b`/`025f2a6a`/`9257a51b`, utils/write_values.py
  `1dc426d4`/`a9d6fa32`/`1dc426d4`, rest_framework/inputs.py
  `0e2638fd`/`b7f4a6ba`/`0e2638fd`, rest_framework/resolvers.py
  `4d05a330`/`14ffc9c8`/`4d05a330`, forms/inputs.py
  `df1df485`/`1b38e890`/`df1df485`, extensions/resource_policy.py
  `2123cbef`/`4cd95703`/`2123cbef`, utils/errors.py
  `e9572ea9`/`9cf4e952`/`e9572ea9`, utils/inputs.py
  `0b8d3daa`/`c199eaa4`/`0b8d3daa`. Any fingerprint change in either
  set reopens this finding. Worker-0/the maintainer may still demand a W1
  re-pass to fold these into the Finding record; the verdict does not
  depend on where the pins live.
- (k) Dirt attribution: walker WT/HEAD diff is exactly +32/-25; the
  hunk list shows exactly one hunk inside the nine members (:277,
  `getattr` to `truth.static_attr`, external truth migration,
  untouched by this zero-edit item); the rest are the truth-migration
  import/log hunks and f56's ledgered `target_definition=` threading.
  No other hunk touches the family.
- (l) Oracle pins: all 12 test locations reproduced exactly
  (test_walker :540/:575/:630/:676/:715/:3200; live :143/:169/:318/
  :427/:450/:479). No oracle rewritten (empty diff); the
  build-count-spy independence point is covered under (d).
- (m) I1/I2 investigated-but-clear verified on body: I1 consistent by
  construction (same memo key, fields half only, `{}` ignored on the
  cacheable path); I2 a pure repeated read. No (Worker-2) defect
  filed.
- (n) Structural gate: none owed — agreed. Private single-module
  owner, both spend sites in-module, any new walk routes through the
  single `_walk_selections`; a census-pinning gate would be a bespoke
  existence test per helper, which the method forbids. Behavioral pins
  + censuses-as-baseline are the correct durable protection.
- (o) Pending execution: empty — confirmed nothing owed. No `proof:`
  entry (all static-reviewed, zero-edit); no `gate:` entry (suite
  confirmation rides the plan's final gate). Verdict is plain
  `verified`, not pending execution.
- (p) Coupling: none. Sub-rules: the memo/clear row already holds its
  index row (`forward-name-memo-clear-row`, file-local); no new index
  row owed.
- (q) AGENTS.md prose on the item diff: the touched-path set is empty,
  so no-provenance / citation / tier rules apply vacuously. Ruff:
  touched `.py` paths = {} (stated explicitly); no `ruff check --fix`
  / `ruff format` run owed. The artifact's link-def block is preserved
  verbatim; neither Worker-1 nor this section adds a cross-file link.
  `check_public_types.py` not owed (no public symbol touched);
  `check_any.py` never run (deleted).

### Gate re-runs (my copy, `dry/seltarget-f57/verify-1`, slot-3, fresh)

- Oracles (the one authorized focused shared-tree run):
  `uv run pytest tests/optimizer/test_walker.py -k "forward_name or
  name_resolution or explicitly_named_fields or
  digit_boundary_relation_connection" --no-cov -n0 -q` → 6 passed,
  193 deselected.
- `basedpyright` → 0 errors, 0 warnings, 0 notes
  (`dry-20261009T184957-f6cb37`).
- `basedpyright -p pyrightconfig.floor.json` → 0/0/0
  (`dry-20261009T185113-882c6a`).
- `check_truthful_reads.py --check` → 120 files, 1 exempt, tier-1 0,
  errors 0 (`dry-20261009T185225-93c395`).
- Copy package digest `sha256:3128e46b...` matches Worker-1's proof
  digest; shared tree unmoved across all three runs.

Verdict: `verified`. Forward selection-target resolution is already
one rule in one owner (`optimizer/walker.py`); all six challenges
count 1 (C6 rejected at 1 per contract); the matrix is discharged
against the target's real surface; sharded/pg inapplicability holds
by construction; no consolidation, no gate, no defect, no new index
row is owed.

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
