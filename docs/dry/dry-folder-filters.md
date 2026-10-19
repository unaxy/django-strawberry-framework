# DRY review: `filters/` folder integration

Status: verified
Run: 0.0.15 2026-10-09-13

Verdict: 3 consolidations CONFIRMED and landed (`filters-model-less-leaf-view`,
`filters-scoped-seed-rows`, `filters-projection-child-filter`, each count 2→1
with a census gate + failability pin); 2 count-2+ findings blocked-on-hunt with
byte-exact migrations specified and zero edits
(`lookup-table-declared-filters-read`, `custom-loop-queryset-return-assertion`);
4 tree-falsified prior assignments flagged for the closeout defect-homing pass
(rows not reopened); 21 folder-local rules single-owned; 10 merges rejected
with triggers; 0 defects.

## Pins and fingerprints

HEAD `23b5f421` (detached, intended).
`ITEM_BASELINE=528d8cf09337d7e7b1ef10cff4c478f522c4730b` (before copy in
slot-1). Blob fingerprints below are `git hash-object` (WT), `git rev-parse
HEAD:<path>` (HEAD), `git rev-parse ITEM_BASELINE:<path>` (BASE), all
short-8, re-verified after the last edit:

| File | WT | HEAD | BASE |
|---|---|---|---|
| `filters/__init__.py` (162 lines) | `ecff967b` | `ecff967b` | `ecff967b` |
| `filters/base.py` (1595 lines) | `77c2e7a6` | `a43513a7` | `77c2e7a6` |
| `filters/factories.py` (79 lines) | `3132a702` | `3132a702` | `3132a702` |
| `filters/inputs.py` (1377 lines) | `a269a3fe` | `d77a113c` | `a269a3fe` |
| `filters/sets.py` (5042 lines) | `d6bb78d1` | `b8740187` | `9428aba9` |

Item-scoped diff (`ITEM_BASELINE` → WT): `filters/sets.py` +39/−10 (3 new
helpers + 6 one-line compositions, this item's consolidations) and
`tests/filters/test_sets.py` +186/−0 (3 census gates + walkers + 1 import);
the other four folder files are byte-identical to `ITEM_BASELINE` (their
WT-vs-HEAD dirt predates the item and is concurrent work, never touched).
`tests/filters/test_sets.py` WT blob `ee6690d0`.

## System trace

The folder owns the filter family end to end: `base.py` (filter primitives
+ identity column + enum-value marker), `inputs.py` (GraphQL input-shape
derivation + the leaf form-key table), `sets.py` (`FilterSet` declaration,
expansion, normalization and the apply pipeline), `factories.py` (the BFS
input builder over the shared substrate), `__init__.py` (the 17-name
consumer surface + the Decision-11 helper in two spellings). Data flows
declaration → `get_filters` expansion (with candidate metadata frozen) →
`filter_lookup_table` grouping → input-class build → `_normalize_input` form
data → `apply_sync`/`apply_async` (visibility derive → related constraints
→ flat leaves → logic tree). Every cross-folder seam (naming, permissions,
lifecycle, expansion skeleton, seal, sync boundary, queryset seeding, error
shape, traversal budget) is owned outside and composed by name; the folder
owns no cross-folder definition.

Member-file inputs re-derived at current bytes (not inherited):
[file-init][file-init] (16-name census), [file-base][file-base] (s7, F-9/F-10
named), [file-factories][file-factories] (14 members, F-1/F-2), [file-inputs][file-inputs]
(s8, F-1/F-2 named, L-n named), [file-sets][file-sets] (s9, rows 1–35). Where
the tree falsified an assignment the record sits under Findings as FF
(flag for closeout; no row reopened, nothing re-applied).

### Attribution of the working-tree dirt (by diff content vs HEAD)

- `filters/base.py` (WT `77c2e7a6` vs HEAD `a43513a7`): truth-migration
  reads (`truth.static_attr`, `truth.kind`, `truth.qualname`) plus hostile
  guard/arm deletions — concurrent work, untouched. This item's cited
  consumer lines that carry `truth.*` keep their verdicts; no edit touches
  them.
- `filters/inputs.py` (WT `a269a3fe` vs HEAD `d77a113c`): same migration
  (18 hunk headers), including both `declared_filters` reads
  (`@@ -1043,7 +1075,11 @@`, `@@ -1088,7 +1124,11 @@`) — concurrent work,
  untouched; FAM-4 is blocked on exactly these two hunks.
- `filters/sets.py` (WT `d6bb78d1` vs HEAD `b8740187`): 58 hunk headers
  (50 hunt migration — truth reads, `pyright: ignore` re-tokens, comment
  rewords — one display-merged with this item's site-1 edit at
  `@@ -3012,16 +3059,14 @@`, plus 8 this item's own) and WT-only
  `_inherits_unchanged` / `_registered_profile` (0 hits at HEAD, part of
  the uncommitted set) — concurrent work, untouched.
  All four queryset-assertion sites (FAM-5) sit inside hunt hunks
  (`@@ -4037`, `@@ -4292`, `@@ -4418`, `@@ -4429`). Every line this item
  edited is HEAD-identical outside those hunks (each edited line verified
  verbatim at HEAD; the item diff carries zero `truth.*`/`except`/`getattr`
 /`cast(` tokens on any added or removed line).
- `filters/__init__.py`, `filters/factories.py`: clean (WT = HEAD).

## Verification

### Matrix

1. Cross-flavor: the Decision-11 helper body is owned once
   (`utils/inputs.py::build_lazy_input_annotation`); the filter and order
   twins (`_filter_input_annotation` / `_order_input_annotation`,
   `FilterInput` / `OrderInput`) pass family values only (FC-2). The BFS
   substrate is owned once (`GeneratedInputArgumentsFactory`); both
   factories declare 6 hook attrs + 2 caches + 1 hook method with
   family-divergent values (FC-1). The scope-seed rhyme across
   filters/orders/relay is three contracts, not one rule (FR-4). The
   orders-normalize twin stays under its rejected row. Discharged.
2. Sync/async: `base.py`, `inputs.py`, `factories.py`, `__init__.py` carry
   zero `async def` / `await`; all five `async def`s live in `sets.py`
   (visibility derive, nested-visibility pre-walk, flat-hop prefill,
   scoped-rows await, `apply_async`). Twin pairs share pure decisions only:
   the seed (FAM-2, consolidated), the depth assert (f51, 5 composers),
   the `run_permissions=False` derivation contract; twin bodies stay
   separate (FR-6). Discharged.
3. Derived knowledge: every same-token population in the folder was walked
   on body strength. Genuine re-derivations: the model-less guard pair
   (FAM-1), the scope-seed pair (FAM-2), the child-resolution pair (FAM-3),
   the declared-read pair (FAM-4, blocked), the queryset-assertion
   quadruple (FAM-5, blocked). The parent-stamp reads (FR-1), the
   field-name half of f60 (FR-2), the cardinality recompute (FR-3), the
   `_base_manager` seed (FR-5), the gate-path guard (FR-7), the
   sibling child reads (FR-8), the recursion trio (FR-9) and the
   non-walkable raises (FR-10) are distinct contracts with triggers.
   Discharged.
4. Round-trip: the annotation half (inputs.py arms at `:375`/`:408`) and
   the coercion half (base.py chain) read the same trio (f59 CONFIRMED);
   GlobalID encode/decode halves share `resolve_globalid_target_definition`
   (family-verified; this item re-verifies composition only, no second
   site); the table build (inputs.py)
   and the table reads (sets.py) share one object by source identity
   (`filters-lookup-table-lifecycle`). Discharged.
5. Other media: package oracles (`tests/filters/`, 630 rows in
   `test_sets.py` alone, all green post-edit), live `/graphql` rows (the
   scalars/library/visibility suites pin wire behavior), projections
   (module/class/method docstrings; the three member D1s are already homed
   to closeout per plan rows 115/117/118 and never fixed here —
   inputs-D1a verified verbatim-present, inputs-D1b's region since gained
   the enum arm so its closer re-derives the count).
   No medium carries a second definition of a folder rule. Discharged.
6. Omission: all five files enumerated below; every member lands in a
   member-artifact assignment re-verified at current bytes, a family row,
   or one of this item's 26 rows. No unassigned member remains.
   Discharged.

### Enumeration

Instrument: `ast` top-level census plus `grep -c` anchor checks over the
folder at WT bytes (post-edit); every anchor count ≥ 1 re-verified
(zero misses across the full three-file inventory).

| File | Top-level members | Homes |
|---|---|---|
| `__init__.py` | 8 imports, ledger + clear + bus row, `_filter_input_annotation`, `filter_input_type`, `_FilterSetT`, `FilterInput`, `__all__` (17) | `filters-leaf-manifest`, `filters-consumer-helper-spellings` |
| `base.py` | 51 (43 run-8 + 8 new: enum septet + `_bound_field_name`) | s7 stands + f59/f60 + `filters-enum-member-value`, `filters-bound-filter-path` |
| `factories.py` | 9 class members (2 caches + 6 hook attrs + 1 hook method); Layer-6 gone | `set-arguments-factory-bfs` row + FF-1 (members 1/2/13/14) |
| `inputs.py` | 52 (46 run-8 + 6 new: table trio + range cache + 2 helpers) | s8 stands + `lookup-name-spelling-grammar`, `filter-logic-operators`, `model-choice-list-ness`, `filters-range-input-cache` |
| `sets.py` | 70 module members (68 pre-edit + 2 landed helpers) + `FilterSet` (27 methods new since run-8 plus new hand-off slots, 3 gone; 1 method + 6 compositions landed here) | s9 stands + FAM-1..5 + `filters-expansion-build`, `filters-generation-conditional`, `filters-generation-eligibility`, `filters-audited-optimizer-range`, `filters-lookup-table-lifecycle`, `filters-input-normalization`, `filters-related-visibility-derive`, `filters-hop-visibility`, `filters-branch-restriction`, `filters-projection-and-chain`, `filters-leaf-gate-walk`, `filters-apply-pipeline`, `filters-apply-channels` + FC convergences |

### Challenges

Authoritative definitions only; consumers, oracles and projections that
also move are listed, never counted. Post-edit bytes.

- C1 model-less leaf posture change → 1 (`_leaf_lookups_by_attr`; was 2).
- C2 scope-seed policy change → 1 (`_scoped_seed_rows`; was 2).
- C3 projection child-resolution change → 1 (`_projection_child_filter`;
  was 2).
- C4 new lookup token in the grammar → 1 (`LOOKUP_NAME_MAP`; the bag
  sniff set derives by comprehension; table grouping and form keys
  compose).
- C5 new logic operator → 1 (descriptor + tuple entry; wire/attr maps
  derive; `_iter_logic_branches` and the tree compose).
- C6 new relation-identity shape → 1 (trio in `base.py`; both annotation
  arms and both filter bodies compose).
- C7 new branch-restriction step → 1 (`_restrict_through_branch`; nested
  branches and flat walking leaves compose).
- C8 new hop-visibility reader → 1 (`_hop_visible_rows`; the async
  pre-pass and first-use derive compose).
- C9 declared-map read change → 2 (FAM-4, blocked-on-hunt).
- C10 queryset-assertion wording change → 4 in 2 wordings (FAM-5,
  blocked-on-hunt).

## Findings

### FAM-1 — `filters-model-less-leaf-view` (CONFIRMED count-2, CONSOLIDATED 2→1)

- Contract + variation: a `FilterSet` without `Meta.model` exposes no
  leaf lookups — the empty map makes `_normalize_input` reject any leaf
  and `_supplied_leaf_filters` supply none. Varies on the model-less
  posture only (C1).
- Sites + roles: 2 identical 3-line guards
  (`filter_lookup_table(cls).by_input_attr if cls._meta.model is not None
  else {}`) in `_normalize_input` and `_supplied_leaf_filters`. Same
  inputs (`cls`), same output, same reasons to change — and coupled: if
  the pre-pass and the form ever disagreed, gates would fire for leaves
  the form never runs (or vice versa). Both lines HEAD-identical
  (verified verbatim at HEAD).
- Challenges: C1 count 2 → 1.
- Owner + lifetime: `FilterSet._leaf_lookups_by_attr` (new classmethod,
  this item); both readers compose by name. Pure derivation, not cached.
- Behavioral proof: `tests/filters/test_sets.py`, 630/630 green in slot-2
  (`dry-20261010T003307-60446f`), covering normalize rejection rows and
  supplied-leaf visibility/gate rows through both readers.
- Structural gate:
  `test_leaf_lookups_compose_the_shared_table_view` (exact AST multiset:
  1 view-read + 2 composers), green in slot-2 and in the shared tree.
- Failability: re-inlining either site fails exactly the gate row
  (`prove` entry 1, pinned, byte-identical restore).

### FAM-2 — `filters-scoped-seed-rows` (CONFIRMED count-2, CONSOLIDATED 2→1)

- Contract + variation: the unscoped seed rows a scoping type's
  visibility hook filters on an alias —
  `base_queryset(model_for(scope), using=parent_db)`. Varies on the seed
  policy only (C2).
- Sites + roles: 2 identical seed lines in the sync derive
  (`_scoped_rows`) and the async pre-fill (`_await_scoped_rows`) of the
  same hop map. Same inputs, same contract; both lines HEAD-identical.
  The orders twins and the relay spelling are different contracts
  (FR-4), not further sites of this rule.
- Challenges: C2 count 2 → 1.
- Owner + lifetime: module-level `_scoped_seed_rows` (new, beside the
  hop helpers); both colorings compose by name. Pure derivation.
- Behavioral proof: same 630-row suite (flat-hop visibility sync +
  async oracles run both colorings).
- Structural gate: `test_scoped_seeds_compose_the_shared_seed` (exact
  AST multiset: 1 `model_for` read + 2 composers), green both trees.
- Failability: re-inlining either site fails exactly the gate row
  (`prove` entry 2, pinned, byte-identical restore).

### FAM-3 — `filters-projection-child-filter` (CONFIRMED count-2, CONSOLIDATED 2→1)

- Contract + variation: the child filter a `ChildProjection` answers
  for — the target set's current filter under the projection name, via
  class-level `get_filters()` (fresh expansion). Varies on the
  resolution rule only (C3).
- Sites + roles: 2 identical `child_cls.get_filters()[projection.name]`
  reads in the visibility walk (`_visibility_hops`) and the gate walk
  (`_leaf_gates`). Coupled: disagreeing answers would scope visibility
  for one filter while firing gates for another. Both lines
  HEAD-identical. The breadcrumb-keyed, instance-level and
  template-level reads are different contracts (FR-8).
- Challenges: C3 count 2 → 1.
- Owner + lifetime: module-level `_projection_child_filter` (new, beside
  the projection helpers); both walks compose by name. Pure read.
- Behavioral proof: same 630-row suite (projection visibility + gate
  oracles run both walks).
- Structural gate:
  `test_projection_child_filters_compose_the_shared_resolution` (exact
  AST multiset: 1 inline resolution + 2 composers), green both trees.
- Failability: re-inlining either site fails exactly the gate row
  (`prove` entry 3, pinned, byte-identical restore).

### FAM-4 — `lookup-table-declared-filters-read` (CONFIRMED count-2, BLOCKED-ON-HUNT)

- Contract + variation: the name-keyed declared map a table build reads
  (`declared_filters` off the filterset class). One flow, one object.
- Sites + roles: 2 identical 4-line reads (comment + cast +
  `truth.static_attr`) in `_group_filters_by_head` and its sole caller
  `filter_lookup_table` — the caller re-reads what the callee just read.
  Both hunks are hunt dirt (`@@ -1043,7 +1075,11 @@`,
  `@@ -1088,7 +1124,11 @@` in `filters/inputs.py`; HEAD spelled both
  `declared_filters = getattr(filterset_cls, "declared_filters", {})`).
  Zero edits; nothing touched.
- Owner + lifetime (specified, unlanded): read once in
  `filter_lookup_table`, pass the map into
  `_group_filters_by_head(filterset_cls, all_filters,
  declared_filters)`; the callee keeps `filterset_cls` for its error
  wording. Behavior-preserving by construction (same object, same flow).
- Behavioral proof owed: the lookup-table oracles
  (`test_normalize_input_rejects_what_the_lookup_table_does_not_hold`
  + grouping/alias rows) stay green; the migration changes no value.
- Structural gate owed: exact AST census pinning the
  `declared_filters` read to the caller (f55 shape), plus a failability
  entry re-adding the callee read.
- Index: new open family row for Worker-0 (below); a family item lands
  it once the hunt's migration settles.

### FAM-5 — `custom-loop-queryset-return-assertion` (CONFIRMED count-4, BLOCKED-ON-HUNT)

- Contract + variation: upstream `BaseFilterSet.filter_queryset`'s
  QuerySet-return assertion, mirrored at every custom filter-invocation
  site so a non-queryset return fails loud with the site identity.
- Sites + roles: 4 spellings in 2 wordings —
  `_filter_child_rows` (`:4108`), `_apply_active_leaf` no-hop arm
  (`:4363`) worded `filter {field_name!r}`; `_apply_flat_leaves`
  non-routed (`:4488`) and routed (`:4499`) worded `.{name}`. All four
  sit in hunt hunks (`@@ -4037`, `@@ -4292`, `@@ -4418`, `@@ -4429`;
  HEAD spelled `isinstance` + `type(...).__name__`). The migration
  touching all four identically is empirical proof of the shared
  change obligation. Zero edits; nothing touched.
- Owner + lifetime (specified, unlanded): a shared
  `_require_queryset_result(result, subject)` helper owning the
  predicate + sentence shape; each site formats its subject phrase
  (field-name vs filter-name wording stays per-site — messages
  unchanged). Behavior-preserving by construction.
- Behavioral proof owed: the apply-pipeline oracles stay green; only
  assert bodies move.
- Structural gate owed: exact AST census pinning the
  `isinstance-QuerySet` assert shape to the helper, plus a failability
  entry re-inlining one site.
- Index: new open family row for Worker-0 (below); a family item lands
  it once the hunt's migration settles.

### FC-1 — BFS factory declarations (CONFIRM consolidated posture)

Both factories declare over the shared substrate by bare data: 6 hook
attrs + 2 caches + 1 `_build_input_triples` override each
(filters `:33`–`:79`, orders `:67`–`:75`), family-divergent values only.
The filter hook splices `_build_logic_fields`, the order hook returns
bare triples — the documented semantic divergence, not a merge
candidate. `set-arguments-factory-bfs` row 468 stands; zero new sites.

### FC-2 — Decision-11 helper twins (CONFIRM single-owned)

`_filter_input_annotation` (`:63`) and `_order_input_annotation`
(orders `:55`) are thin family bindings over
`build_lazy_input_annotation` (base/label/ledger/namer/module differ by
family); `filter_input_type` + `FilterInput[...]` (and the order
spellings) compose their twin with a spelling label. One body, four
declarations. No duplication, no row.

### FC-3 — relation-identity rule (CONFIRM f59)

f59's census holds verbatim at current bytes: the trio in `base.py`
(`relation_identity_column` `:1215`, `_model_identity_column`,
`model_choice_identity_column`), both annotation arms calling it
(inputs.py `:375` + `:408`), the walk helper
(`_relation_identity_column_for` `:1268`) with its internal read
(`:1284`) and its runtime caller (`_coerce_relation_identity` `:1294`).
Single-owned, zero-edit. Row 1330 stands.

### FC-4 — bound-filter walk (CONFIRM f60, still blocked)

f60's count-2 holds: `IntegerInFilter.filter` (parent → `_meta` →
model → `get_model_field(model, _bound_field_name(self))`) and
`_relation_identity_column_for` (same walk, `None`-on-unbound
contract); `_model_field_for_filter` stays the examined-and-excluded
build-time third spelling. Site 1's `_meta` line is still hunt dirt
(`truth.static_attr`), so the family stays blocked-on-hunt with its
specified migration unlanded. Row 1331 stands; this item specifies no
competing migration.

### FC-5 — depth-cap binding (CONFIRM f51 ledger)

`_assert_logic_depth` (`:3483`) plus exactly the 5 ledgered composers
(`:3553`, `:3633`, `:4619`, `:4907`, `:4978`), each a one-liner over
`_assert_logic_depth`. The ledger row (Owned changes, f51)
holds byte-exact. No drift, no row.

### FC-6 — sealed-execution participation (CONFIRM, census drift noted)

`filters/sets.py` carries zero seal tokens (case-insensitive grep, 0
hits) and participates only by composing `apply_type_visibility_sync` /
`_async` by name — now 6 call sites (`:3437`, `:3472`, `:3967`,
`:4036`, `:4051`, `:4090`; s17 counted 2). All four new sites belong
to the flat-hop machinery and follow the same composition. The s17
verdict (no second seal body) stands; the consumer census grew by
construction. Noted for closeout refresh; no row.

### FC-7 — queryset seed + model read (CONFIRM e8/F2, census drift noted)

Every filters-side seed composes `base_queryset` by name (`base.py`
`:1594`; `sets.py` `:2558`, `:3385`, `:4152` + the FAM-2 helper) and
`model_for` appears exactly once post-edit (inside `_scoped_seed_rows`;
s9's "0 hits" predates the flat-hop pair — see FF-4). Package censuses
drifted with feature growth (`model_for` 21 lines / 7 files vs e8's
17 / 5; `base_queryset` 14 / 9 vs 8 / 8 — grep counts, methodology
differs, closer re-derives by body read). F2's single-owned verdict
stands; e8 is open/pending so its re-verification refreshes the
numbers. No row.

### FC-8 — sync boundary + post-apply exclusion (CONFIRM)

`apply_async` routes finalization through `run_in_one_sync_boundary`
(`:5006`) — the open `one-sync-boundary` row's filters leg, composing
by name. `_filter_child_rows` returns its result unsealed (no seal
token in the file), so the `post-set-apply-result-validation` R-child
exclusion stands. No row.

### FC-9 — child-derivation exclusion (CONFIRM, line refs stale)

The `child-derivation-unsealed` row-306 exclusion holds: the child
`apply_sync` / `apply_async` returns at `:3438` / `:3473` travel
unsealed into the parent's correlated `EXISTS` (subquery-RHS
downstream, outer seal intact). Only the row's cited lines are stale
(`:2761`/`:2796` → `:3438`/`:3473`) — recorded as a correction for
Worker-0, not a finding.

### FC-10 — lookup-path + registry + coercion + error-shape consumers (CONFIRM)

`orm-lookup-path-resolution` (12 consumer hits, all by name),
`type-registry-model-type-map` (`registry.get` exactly `:2856` +
`:3627`, live calls), `field-value-coercion` (5 `base.py` hits),
`coded-error-extensions-shape` (sets 2 + base 6). No second site for
any of the four owners. No row.

### FC-11 — clear-lifecycle convergences (CONFIRM)

The subsystem-clear rows hold: `filters.helper_references` ledger +
clear + bus registration (`__init__.py`), `filters.input_namespace`
heavy-clear wrapper (`clear_filter_input_namespace` `:1358`, still a
thin delegate + `register_subsystem_clear(owner=..., before_bind=True)`
`:1373`), factory caches cleared through the heavy path (wrapper
docstring), `FilterSet._lifecycle` binding descriptor (`:1785`). The
`_lookup_table` slot (`:1776`) is deliberately outside
`_lifecycle.extra`: its source-identity check
(`cached.source is all_filters`, inputs.py `:1124`) rebuilds on any
new `get_filters()` object, which is exactly what a clear produces —
sound by construction, covered by the
`filters-lookup-table-lifecycle` row. No new family row.

### FC-12 — Meta-alias survivors (CONFIRM sub-rule standing)

f32's getter is gone (FF-1) but its alias sub-rule stands coherent:
`promote_set_meta_fields` + `read_set_meta_fields` +
`resolve_set_meta_fields` + `canonicalize_set_meta_fields` in
`utils/inputs.py`, `FILTERSET_FIELDS_ALIAS`, both metaclass
write-backs (`sets.py:1113` with alias, `orders/sets.py:369` without)
and the orders expansion read (`orders/sets.py:561`). The families
compose the write-back by bare call. No duplication, no row.

### FC-13 — sets-mixins + runner seams (CONFIRM convergence)

Every shared-seam call in `sets.py` composes its owner once and only
once: `collect_related_declarations` (`:1129`),
`reject_captured_branches` (`:1944`), `should_cache_expansion`
(`:2002`), `expanded_once` (`:2024`),
`require_re_readable_field_declaration` (`:2098`),
`run_in_one_sync_boundary` (`:5006`); the config trio
(`_lifecycle` `:1785`, `_permission` `:1798`, `_field_type_suffix`
`:1869`) declares family values the mixins read. The never-rowed
owner-side names (`set-type-naming`, `active-input-permission-facade`,
`related-set-target-lifecycle`, expansion skeleton/gate, re-readable
gate, declaration collection) stay the owning folders' business; this
item records the filters-side facets only. No row.

### FC-14 — `construct_search` still deferred (CONFIRM s5)

Still zero runtime callers (only the `get_filters` TODO + docstring
mentions); the prefix map + builder stay tested directly. The s5
deferred-surface posture holds. No row.

### FF-1 — Layer-6 is gone: f32 + row 469 + factories F-2/L-a falsified (flag for closeout)

Prior assignment: `dynamic-set-class-getter` single-owned — the getter
plus 8 composed helpers count 1, both families compose by bare
declaration (f32, run 10; row 469); factories members 1/13/14 compose
F-2 and member 2 (`_RESERVED_FACTORY_KEYS`) is file-local L-a (file
artifact, 14 members).
Tree at current bytes: `make_dynamic_set_getter`,
`normalize_set_meta_for_factory`, `make_set_meta_cache_key`,
`create_dynamic_set_class`, `make_hashable_meta_value` — zero hits
package-wide; 6 of 11 mechanism helpers gone; both factory declaration
groups gone (`factories.py` is 79 lines, orders 83); both public
wrappers, both caches, both reserved-key literals, `AutoFilter` /
`AutoOrder` — all zero hits; Layer-6 tests zero hits outside a binary
artifact. Deleted by committed `899cb35b` ("delete test-only package
code"), which postdates f32. What survives is the smaller alias
sub-rule (FC-12), not the getter rule.
Row 469's claim ("getter + 8 composed helpers count 1, both families
compose by bare declaration") no longer names anything in the tree, and
the factories artifact's members 1/2/13/14 have no bytes. Flagged for
the closeout defect-homing pass (retire-or-revise row 469 + f32's
record + the factories enumeration); rows not reopened here, nothing
re-applied.

### FF-2 — `__init__` census 16 → 17 + 3 unassigned members (flag for closeout)

Prior assignment: 16 re-exported names, `__all__` exactly those 16
(file artifact rows 1–12, run 7).
Tree at current bytes: `__all__` names 17 (`:144`–`:162`); new since
the artifact are `_filter_input_annotation` (`:63`),
`FilterInput` (`:110`) and `_FilterSetT` (`:107`), plus the base-import
shape drift (12 from `.base` + `Filter` direct from `django_filters`).
The 16-count and the 12-row enumeration no longer match. This item
homes the current shape in `filters-leaf-manifest` +
`filters-consumer-helper-spellings`; the stale census itself is flagged
for closeout (record-only revision of the file artifact's counts).

### FF-3 — lookup-grammar reverse half moved files (flag for closeout)

Prior assignment: the reverse half of `lookup-name-spelling-grammar`
lives in `sets.py` (`_FORM_KEY_BY_PYTHON_ATTR` + `_form_key_for_python_attr`,
sets-artifact rows 2–3, STAND at run-8 s9).
Tree at current bytes: both members zero hits package-wide (only stale
regenerable `docs/shadow/current/` mirrors + historical dry records
mention them). The reverse half now lives in `inputs.py` as
`FilterLookupTable.by_input_attr`, built by `filter_lookup_table`;
`sets.py` consumes it by name (FAM-1's readers, `_leaf_form_entries`).
Rows 2–3 name no bytes; the family itself (never rowed — see
`lookup-name-spelling-grammar` below) is homed by this item in its
current shape. Flagged for closeout (rows 2–3 retire at the s9 record).

### FF-4 — `model_for` census in `sets.py` 0 → 2 → 1 (flag for closeout)

Prior assignment: s9's `queryset-seed-and-model-read` facet —
`base_queryset` composed, `model_for` 0 hits in `sets.py` (partial).
Tree at current bytes: the flat-hop machinery added 2 `model_for`
call sites (since unified by FAM-2 into `_scoped_seed_rows`, now 1).
The "0 hits" claim is falsified; e8/F2's package censuses (17 sites /
5 files, 8 / 8) predate the growth and this item's −1 (now 21 / 7 and
14 / 9 by grep). F2's single-owned verdict stands in all records —
only the counts refresh. Flagged for closeout (s9 facet + e8 census
refresh at e8's pending re-verification).

### FL-1 — `filters/__init__.py` local rules (CONFIRM, 2 rows)

- `filters-leaf-manifest`: the 17-name `__all__` mirror (12 from
  `.base`, `Filter` direct, 2 from `.sets`, 2 defined here), the
  `filters.helper_references` ledger + clear + bus registration. Owner
  `__init__.py`; definitions live in home modules. Challenge: new
  export → 1 (`__all__` line; the binding follows the import).
- `filters-consumer-helper-spellings`: `_filter_input_annotation`
  (validate + ledger + annotate, `:63`) composed by `filter_input_type`
  and `FilterInput[...]` with spelling labels; `_FilterSetT` bound.
  Challenge: helper-body change → 1 (FC-2's shared owner) + 0 here.
  Oracle: `test_filter_input_type_returns_forwardref_in_annotation_args`
  (form pinned at the shared helper).

### FL-2 — `filters/base.py` local rules (CONFIRM, 2 rows)

- `filters-enum-member-value`: `EnumMemberValue` + `_EnumMemberFieldMixin`
  / `_EnumMemberFilterMixin` + `_EnumChoiceField` / `_EnumCharField` +
  `EnumChoiceFilter` / `EnumLookupFilter` (`:416`–`:502`, new since
  run-8). The marker always predicates, always cleans to itself;
  consumers compose by name (inputs.py `_scalar` wrap arm, sets.py
  selection + family registry). Challenge: member-is-value change → 1
  (the mixin pair). Oracles: enum pins in `tests/filters/test_sets.py`
  (`test_enum_choice_filter_resolves_to_the_choice_family_profile`
  through `test_enum_member_value_survives_copy_and_pickle`) + base
  choice tests.
- `filters-bound-filter-path`: `_bound_field_name` (`:344`, new) — the
  one str-typed bound-filter-path read (raise on `None`). 13 consumer
  sites, all in-folder (base 1, inputs 1, sets 11: filter bodies, table
  gate-paths, expansion, candidate build, flat-leaf walk, hop readers,
  branch validators, path census). A same-named private helper over
  DRF serializer fields (`serializer_converter.py:343`) is a different
  rule — different type, different binder — correctly separate.
  Challenge: bound-path read change → 1. Oracle: bound/unbound rows in
  `tests/filters/test_base.py` + every consumer's suite.

### FL-3 — `filters/inputs.py` local rules (CONFIRM, 4 rows)

- `lookup-name-spelling-grammar` (inputs-artifact F-1, never rowed —
  homed here in current shape): owner `LOOKUP_NAME_MAP` (the one
  grammar definition); reverse half now `FilterLookupTable.by_input_attr`
  (same file, FF-3); consumers `_build_input_fields` grouping,
  `_LOOKUP_PYTHON_ATTRS` sniff vocabulary, sets.py table readers.
  Challenge C4 count 1.
- `filter-logic-operators` (inputs-artifact F-2, never rowed — homed
  here): owner the descriptor triple + `LOGIC_OPERATORS` + both derived
  maps + `_compose_*`; sets.py composes (`_iter_logic_branches`,
  `_LOGIC_PYTHON_ATTRS`, tree evaluation). Challenge C5 count 1.
- `model-choice-list-ness` (inputs-artifact L-n, never rowed — homed
  here): owner `_model_choice_takes_list` (`:386`); sole
  `BaseCSVFilter` isinstance spelling package-wide; 2 in-file
  consumers (`:590`, `:719`). Challenge: list-ness change → 1.
- `filters-range-input-cache`: `_RANGE_INPUT_CLASSES` (`:851`,
  instance-keyed `WeakKeyDictionary`, self-cleaning, no clear row by
  design) + `_build_range_input_class` (`:892` read) + the positional
  patch builder. Challenge: range-input naming/caching change → 1.

### FL-4 — `filters/sets.py` generation rules (CONFIRM, 4 rows)

- `filters-expansion-build`: metaclass (`collect_related_declarations`
  + `promote_set_meta_fields` write-back + declared provenance stamp),
  `_expand_related_filter` (+ `_filter_paths`), `get_filters`
  (guard + requires + candidate freeze + snapshot publish),
  `get_fields` (per-field `__all__` + sweep narrowing + re-readability
  gate), `_lookups_for_field` (+ class cache), `_strip_model_choice_extras`.
- `filters-generation-conditional`: `filter_for_field` /
  `filter_for_lookup` + `_generation_origin_for_field` oracle +
  own-PK + relation-identity + enum-selection branches
  (`:2673`/`:2679`) + cardinality helper + target-type resolvers.
- `filters-generation-eligibility`: policy baseline
  (`_PUBLIC_PACKAGE_FILTER_DEFAULTS` + `_PACKAGE_POLICY_BASELINE` +
  normalizer), provenance records, family registry (+ enum arms
  `:766`–`:767`) + dynamic-CSV validator, candidate rows + snapshot.
  (`_inherits_unchanged` / `_registered_profile` inside this rule are
  WT-only concurrent dirt — cited, never homed.)
- `filters-audited-optimizer-range`: `_AUDITED_DJANGO_FILTER_RANGE` +
  `_release_is_audited` + `_DJANGO_FILTER_OPTIMIZER_AUDITED`
  (import-time verdict, read per build).
- Challenges: new generation branch / family / range edge → 1 each
  (L13 ladder, registry, range tuple). Oracles: generation + routing
  rows throughout `tests/filters/test_sets.py`.

### FL-5 — `filters/sets.py` apply rules (CONFIRM, 9 rows)

- `filters-lookup-table-lifecycle`: `filter_lookup_table` build
  (group + gate paths + aliasing + own-attr publish) + `_lookup_table`
  slot + source-identity reads (FC-11 for the clear posture).
- `filters-input-normalization`: `_normalize_input` (+ FAM-1 reader) +
  `_leaf_form_entries` + `_require_range_patch_filter` +
  `_operator_bag_items` + `_LOOKUP_PYTHON_ATTRS` + branch/element
  shape validators.
- `filters-related-visibility-derive`: `_iter_visibility_steps` +
  `_branch_visibility_seed` + sync/async derives + nested pre-walk +
  flat-hop prefill + `_target_type_for_related_filter`.
- `filters-hop-visibility`: `_flat_leaf_walk` + `_visibility_hops` (+
  FAM-3 walk) + `_projection_hop` + `_hop_visible_rows` +
  `_hop_visibility` map + `_scoped_rows`/`_await_scoped_rows` (+ FAM-2
  readers) + via-types/rows + `_UndeclaredHopSet` + hop readers.
- `filters-branch-restriction`: `_restrict_to_related` /
  `_reaches_related` / `_restrict_through_branch` / `_admitted_rows`
  (one restriction for nested branches and walking flat leaves).
- `filters-projection-and-chain`: `ChildProjection` /
  `ProjectedChildFilter` (+ class cache + reduce) / `_owner_bound_child`
  + `_leaf_chain` / `_bound_terminal` / `_LeafChain` (+ key-hop /
  key-attname re-read via `_relation_key_value`).
- `filters-leaf-gate-walk`: `_supplied_leaf_filters` (+ FAM-1 reader) +
  `_permission_walk_gates` + `_leaf_gates` (+ FAM-3 walk) +
  `_expansion_origin` + `_permission_fallback_path`.
- `filters-apply-pipeline`: prelude/finalize + `apply_sync` /
  `apply_async` / `apply` + `_apply_flat_leaves` + `_filter_child_rows`
  + `_invoke_suppressing_framework_distinct` + `_leaf_applies` /
  `_chain_base` + `_apply_relation_leaf` + `_apply_active_leaf` /
  `_reaches_hop` + `filter_queryset` + `_evaluate_logic_tree` +
  `_q_for_branch` + `_apply_related_constraints` +
  `_validate_form_or_raise` + permission delegates.
- `filters-apply-channels`: the hand-off slots `_logic_depth`,
  `_apply_info`, `_nested_qs_by_branch_id`, `_flat_hop_visibility`,
  `_projection_children` (per-instance/request lifetime, no clear).
- Challenges: new restriction / projection / gate / apply step → 1
  each at the named owner. Oracles: the apply + visibility + logic-tree
  rows (flat/projection/enum/gate blocks cited under FAM-1..3).

### FR-1 — parent-stamp cast merge (REJECTED)

`ProjectedChildFilter._child` and `.filter` read the bound parent
through the identical raising cast (`getattr(self, "parent")`, `:1274`
/ `:1295`; both HEAD-identical); `.field`
reads the same stamp with a `None`-default check. Two raisings + one
check: a shared raising helper would serve 2 of 3 reads while any
stamp-typing change still visits all three to check contracts — a new
member without a relieved obligation. Trigger: a third raising read,
or the read gaining logic beyond the cast. Home: this record.

### FR-2 — walk helper composing the bound-path read (REJECTED)

`_relation_identity_column_for` inlines its `field_name` read instead
of composing `_bound_field_name`: different contracts (walk returns
`None` for unbound; the helper raises). Composing would change the
walk's unbound verdict. The walk-duplication question itself stays
with f60. Trigger: the walk adopts raise-on-unbound. Home: f60's
record.

### FR-3 — cardinality threading into the relay helper (REJECTED, O1 STANDS)

s9-O1 re-derived: `filter_for_lookup` computes `many_side` (`:2728`)
for the raw-pk ternary (`:2742`) while the relay arm (`:2741`) calls
`_relay_filter_class_for_field`, which recomputes it (`:2813`) — one
redundant pure call on the relay-`exact` path. Threading the flag
couples the helper's "pick a class for a field" contract to a
precomputed input to save nanoseconds. Trigger: a second caller with
its own cardinality, or a non-pure classifier. Home: this record.

### FR-4 — cross-family seed merge (REJECTED)

`base_queryset(model_for(scope), using=alias)` rhymes across filters
(FAM-2 pair), orders (`orders/sets.py:929` + `:960`, per-call readers
with async recourse) and relay (`relay.py:325`, node-lookup seed):
three responsibilities (hop-map fill, per-call readers, node fetch),
three map protocols. One helper would couple visibility seeding to
relay defaults. The filters pair is one rule (FAM-2); the orders pair
is the orders folder's own business (same shape, family-local
decision). Trigger: a shared alias-pinned type-seed need at the
querysets owner. Home: this record.

### FR-5 — `_base_manager` admission seed merge (REJECTED)

`_hop_visible_rows` seeds unscoped undeclared-hop rows via
`_hop_model(hop)._base_manager.using(parent_db)` (`:4079`) — deliberately
not `base_queryset` (`_default_manager`): unscoped rows bypass custom
default-manager filtering to match join semantics. Different manager
contract, correctly separate. Trigger: `base_queryset` gains a manager
parameter. Home: this record.

### FR-6 — twin-body merges, any pair (REJECTED)

Sync/async twin bodies stay separate: the visibility derives (only
the contract + depth assert + seed are shared), the scoped-rows twins
(FAM-2 shares the seed; key/store/return stay per-coloring), the
`_compose_*` trio (three genuinely different bodies — note
`_compose_or`'s empty guard duplicates its loop's empty result, kept
as defensive symmetry, not a defect), the normalize/element raises
(FR-10). Merging any twin pair needs mode flags or signature
coupling. Trigger per pair: a third coloring, or the shared part
outgrowing the per-coloring part. Home: this record.

### FR-7 — gate-path guard merge (REJECTED)

`_permission_fallback_path` (`:3288`) guards on model-lessness like
FAM-1's pair but with a different consequent (gate on the attr itself
vs expose no lookups). Unifying the trigger alone (`_meta.model is
None`, spelled across the class) is vocabulary churn; unifying the
consequents needs a view flag. Trigger: the fallback adopts the
empty-map posture. Home: this record.

### FR-8 — sibling child-filter reads merge (REJECTED)

`child_cls.get_filters()[child_name]` (`:3889`, breadcrumb key),
`child.filters[projection.name]` (`:4230`, live instance map) and
`base_filters[projection.name]` (`:1283`, possibly-stale published
map for the unbound template) answer different questions than FAM-3's
fresh class-level resolution. Folding any of them into the helper
would collapse fresh/published/instance/breadcrumb contracts.
Trigger: contract collapse. Home: this record.

### FR-9 — recursion-driver merge (REJECTED)

`_visibility_hops` (hop collection, pre-form, class-level),
`_leaf_gates` (gate collection, class-level) and `_leaf_chain`
(chain building, bound-instance) recurse the same projection spine
with different outputs and timing. One driver with per-question
adapters is machinery; the shared step (child resolution) is already
FAM-3. Trigger: a fourth projection recursion. Home: this record.

### FR-10 — non-walkable-input raise merge (REJECTED)

`_normalize_input`'s top-level raise and
`_validate_logic_element_shape`'s branch-element raise share the
predicate (`iter_input_items(x) is None`, composed by name) but carry
different actionable messages (top-level vs branch context).
Unifying the verdict would lose the context or add a where-flag.
Trigger: message unification. Home: this record.

## Defects

Zero new defects. The three member D1s stay homed to closeout (plan
rows 115/117/118; inputs-D1a verbatim-present, inputs-D1b's region
gained the enum arm). `_compose_or`'s empty guard duplicates its
loop's empty result but is defensive symmetry, not a defect (FR-6).
The stale `docs/shadow/current/` mirrors of the deleted reverse map
are regenerable tool output, not tree defects.

## Pending execution

No `proof:` entries (every consolidation proof ran complete in slot-2;
see Implementation — nothing is `execution-deferred`). Gate entries
for the final gate (re-run as listed; results bind to the tree state
at gate time):

- `gate: uv run python scripts/workspace.py run dry/folder-filters/consolidate -- basedpyright`
- `gate: uv run python scripts/workspace.py run dry/folder-filters/consolidate -- basedpyright -p pyrightconfig.floor.json`
- `gate: uv run python scripts/workspace.py run dry/folder-filters/consolidate -- python scripts/check_truthful_reads.py --check`
- `gate: uv run python scripts/workspace.py run dry/folder-filters/consolidate -- pytest tests/filters/test_sets.py -n0 -q --no-cov`
- `gate: uv run python scripts/workspace.py prove dry/folder-filters/consolidate ~/dry/tmp/folder-filters-failability.json`

Cells: `sharded` and `pg` stay `unverified` (filter apply paths read
and pin database aliases; inapplicable-by-construction is correctly
NOT claimed). They need the maintainer's separate word per the entry
brief.

## Judgment

Folder item with landed consolidations, ready for verification.
CONFIRM: FAM-1/2/3 consolidated 2→1 with census gates + failability
pins (all proofs green); every cross-boundary composition the file
artifacts claimed still composes by name at WT (FC-1..FC-14, all
censuses re-derived); 21 folder-local rules single-owned with proving
challenges (FL-1..FL-5); ten folder-level merges rejected with
triggers (FR-1..FR-10). FLAG (tree falsified the assignment, rows not
reopened): Layer-6 deletion falsifies f32/row-469 + factories F-2/L-a
(FF-1, retire-or-revise at closeout); `__init__` census 16→17 (FF-2,
record-only); reverse-map members moved to `inputs.py` (FF-3, s9 rows
2–3 retire); `model_for` census drift (FF-4, refresh at e8's pending
re-verification). BLOCKED-ON-HUNT: FAM-4 (exact hunks `@@ -1043,7
+1075,11 @@`, `@@ -1088,7 +1124,11 @@` in `inputs.py`) and FAM-5 (exact
hunks `@@ -4037,9 +4103,9 @@`, `@@ -4292,9 +4358,9 @@`, `@@ -4418,9
+4484,9 @@`, `@@ -4429,9 +4495,9 @@` in `sets.py`) — migrations
specified byte-exactly, tree untouched. 26 index rows named for
Worker-0 (21 file-local + 3 consolidated + 2 open families) plus 4
corrections. Zero defects.
Needs-maintainer: `sharded`/`pg` cell authorization; nothing else —
no attribution need (all hunt hunks identified by content, none
touched) and no combined-fix coupling.

## Implementation (Worker-1)

Landed FAM-1/2/3 at the owner (`filters/sets.py`, +39/−10, blob
`9428aba9` → `d6bb78d1`) with permanent census gates in
`tests/filters/test_sets.py` (+186/−0, 3 walkers + 3 tests + `import
ast`): `_leaf_lookups_by_attr` (+ 2 compositions),
`_scoped_seed_rows` (+ 2), `_projection_child_filter` (+ 2). No new
cast, no `Any`, no suppression, no `pragma: no cover`; the two
touched paths are `ruff check --fix` + `ruff format` clean and
`check_trailing_commas.py --check` clean (0 violations); banned-word
sweep over the test additions clean. Item diff carries zero hunt
tokens on any added/removed line; orphan sweep: the three new names
are referenced by their tests + record only (no other production
reader; `git grep` over package/tests/examples/scripts confirms).

Proofs (all in slot-2 `dry/folder-filters/consolidate` unless noted;
copy fresh, shared tree unmoved at every run):

- `basedpyright`: 0 errors, 0 warnings, 0 notes
  (`dry-20261010T003019-0520ba`).
- `basedpyright -p pyrightconfig.floor.json`: 0/0/0
  (`dry-20261010T003136-387ea2`).
- `check_truthful_reads.py --check`: errors 0
  (`dry-20261010T003258-e80bf1`).
- `pytest tests/filters/test_sets.py -n0 --no-cov -q`: 630 passed
  (`dry-20261010T003307-60446f`).
- `prove` (3-entry manifest, each mutant fails exactly its declared
  census row, restores byte-identical `d6bb78d1`):
  3/3 pinned (`dry-20261010T003351-d613da`).
- Shared tree (the one authorized focused run, single invocation):
  the 3 census nodes, 3 passed in 1.63s.

Failability judgment (handed, per the runner's requirement): 1 failing
row per entry is the complete pin, not weak coverage — each mutation
re-inlines an identical spelling, so the change is behavior-preserving
by construction and no behavioral row can fail; the census row is the
boundary's dedicated pin (`expect_failing` names exactly it).

Ledger-ready rows for Worker-0 (not applied — workers never edit the
plan):

- `django_strawberry_framework/filters/sets.py` — Folder integration
  `filters/` — `_leaf_lookups_by_attr` (NEW) + 2 compositions;
  `_scoped_seed_rows` (NEW) + 2 compositions;
  `_projection_child_filter` (NEW) + 2 compositions.
- `tests/filters/test_sets.py` — Folder integration `filters/` —
  `test_leaf_lookups_compose_the_shared_table_view` +
  `_leaf_lookup_view_spellings`;
  `test_scoped_seeds_compose_the_shared_seed` + `_scoped_seed_spellings`;
  `test_projection_child_filters_compose_the_shared_resolution` +
  `_projection_child_filter_spellings`; `import ast`.

## Index rows for Worker-0

26 new rows (21 file-local + 3 consolidated + 2 open families) + 4
corrections. Holding item for the 24 folder-held rows: Folder
integration `filters/`. The 2 open-family rows need their Family
holding items queued (post-hunt landings).

| Family | Owner | Files covered | Holding item | Status |
|---|---|---|---|---|
| `filters-leaf-manifest` | `django_strawberry_framework/filters/__init__.py::__all__` (17-name mirror; defs in home modules; ledger + clear + bus row) | `django_strawberry_framework/filters/__init__.py` | Folder integration `filters/` | file-local |
| `filters-consumer-helper-spellings` | `django_strawberry_framework/filters/__init__.py::_filter_input_annotation` (composed by `filter_input_type` + `FilterInput[...]`; `_FilterSetT` bound) | `django_strawberry_framework/filters/__init__.py` | Folder integration `filters/` | file-local |
| `filters-enum-member-value` | `django_strawberry_framework/filters/base.py::EnumMemberValue` (+ member mixins + choice/char fields + `EnumChoiceFilter` / `EnumLookupFilter`; consumers in `inputs.py` + `sets.py` by name) | `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-bound-filter-path` | `django_strawberry_framework/filters/base.py::_bound_field_name` (str-typed bound-filter-path read, raise on `None`; 13 consumer sites, all in-folder) | `django_strawberry_framework/filters/base.py`, `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `lookup-name-spelling-grammar` | `django_strawberry_framework/filters/inputs.py::LOOKUP_NAME_MAP` (the one grammar definition; reverse now `FilterLookupTable.by_input_attr`, same file; named F-1 by File `filters/inputs.py` s8, homed here in current shape) | `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filter-logic-operators` | `django_strawberry_framework/filters/inputs.py::LOGIC_OPERATORS` (+ descriptor triple + derived maps + `_compose_*`; sets.py composes; named F-2 by File `filters/inputs.py` s8, homed here) | `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `model-choice-list-ness` | `django_strawberry_framework/filters/inputs.py::_model_choice_takes_list` (sole `BaseCSVFilter` isinstance spelling package-wide; 2 in-file consumers; named L-n by File `filters/inputs.py` s8, homed here) | `django_strawberry_framework/filters/inputs.py` | Folder integration `filters/` | file-local |
| `filters-range-input-cache` | `django_strawberry_framework/filters/inputs.py::_RANGE_INPUT_CLASSES` (instance-keyed `WeakKeyDictionary`, self-cleaning, no clear row; + builder + patch) | `django_strawberry_framework/filters/inputs.py` | Folder integration `filters/` | file-local |
| `filters-expansion-build` | `django_strawberry_framework/filters/sets.py::FilterSet.get_filters` (+ metaclass + `_expand_related_filter` + `get_fields` + lookup/extra helpers) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-generation-conditional` | `django_strawberry_framework/filters/sets.py::FilterSet.filter_for_lookup` (+ `filter_for_field` + origin oracle + own-PK/relation/enum branches) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-generation-eligibility` | `django_strawberry_framework/filters/sets.py::_FILTER_FAMILY_REGISTRY` (+ policy baseline + provenance + candidate rows + snapshot) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-audited-optimizer-range` | `django_strawberry_framework/filters/sets.py::_AUDITED_DJANGO_FILTER_RANGE` (+ release check + import-time verdict) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-lookup-table-lifecycle` | `django_strawberry_framework/filters/inputs.py::filter_lookup_table` (group + gate paths + aliasing + own-attr publish; source-identity lifecycle; sets.py readers) | `django_strawberry_framework/filters/inputs.py`, `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-input-normalization` | `django_strawberry_framework/filters/sets.py::FilterSet._normalize_input` (+ leaf entries + range-patch guard + bag sniff + validators) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-related-visibility-derive` | `django_strawberry_framework/filters/sets.py::FilterSet._iter_visibility_steps` (+ branch seed + sync/async derives + pre-walks + target-type) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-hop-visibility` | `django_strawberry_framework/filters/sets.py::FilterSet._hop_visible_rows` (+ walk + hops + scoped readers + via + hop facings) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-branch-restriction` | `django_strawberry_framework/filters/sets.py::_restrict_through_branch` (+ `_restrict_to_related` / `_reaches_related` / `_admitted_rows`; nested + flat compose) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-projection-and-chain` | `django_strawberry_framework/filters/sets.py::ProjectedChildFilter` (+ projection helpers + `_leaf_chain` / terminal / key re-read) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-leaf-gate-walk` | `django_strawberry_framework/filters/sets.py::FilterSet._leaf_gates` (+ supplied leaves + walk gates + origin + fallback path) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-apply-pipeline` | `django_strawberry_framework/filters/sets.py::FilterSet.apply_sync` (+ prelude/finalize + async/dispatcher + flat leaves + relation leaf + logic tree + branch constraints + validate) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-apply-channels` | `django_strawberry_framework/filters/sets.py::FilterSet` hand-off slots (`_logic_depth` + `_apply_info` + `_nested_qs_by_branch_id` + `_flat_hop_visibility` + `_projection_children`; per-instance/request, no clear) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | file-local |
| `filters-model-less-leaf-view` | `django_strawberry_framework/filters/sets.py::FilterSet._leaf_lookups_by_attr` (NEW this item; 2 identical guards → 1 + 2 composers; census gate + pin) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | consolidated (run 13 FAM-1: CONFIRMED count-2 + CONSOLIDATED 2→1, census gate + failability pin, 0 defects; verified pending W2) |
| `filters-scoped-seed-rows` | `django_strawberry_framework/filters/sets.py::_scoped_seed_rows` (NEW this item; 2 identical seeds → 1 + 2 composers; census gate + pin) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | consolidated (run 13 FAM-2: CONFIRMED count-2 + CONSOLIDATED 2→1, census gate + failability pin, 0 defects; verified pending W2) |
| `filters-projection-child-filter` | `django_strawberry_framework/filters/sets.py::_projection_child_filter` (NEW this item; 2 identical resolutions → 1 + 2 composers; census gate + pin) | `django_strawberry_framework/filters/sets.py` | Folder integration `filters/` | consolidated (run 13 FAM-3: CONFIRMED count-2 + CONSOLIDATED 2→1, census gate + failability pin, 0 defects; verified pending W2) |
| `lookup-table-declared-filters-read` | `django_strawberry_framework/filters/inputs.py::filter_lookup_table` (owner candidate; declared-map read spelled twice in one flow: `_group_filters_by_head` + sole caller; named FAM-4 by Folder integration `filters/`) | `django_strawberry_framework/filters/inputs.py` | Family `lookup-table-declared-filters-read` | open (run 13 FAM-4: CONFIRMED count-2 but blocked-on-hunt — both reads inside truth-migration hunks, migration specified byte-exactly but unlanded, zero edits; verified pending W2, pending execution) |
| `custom-loop-queryset-return-assertion` | `django_strawberry_framework/filters/sets.py` (owner candidate; upstream assertion mirrored at 4 custom-invocation sites in 2 wordings; named FAM-5 by Folder integration `filters/`) | `django_strawberry_framework/filters/sets.py` | Family `custom-loop-queryset-return-assertion` | open (run 13 FAM-5: CONFIRMED count-4 but blocked-on-hunt — all four sites inside truth-migration hunks, migration specified byte-exactly but unlanded, zero edits; verified pending W2, pending execution) |

Corrections owed on existing rows (Worker-0 edits, not new rows):

- `child-derivation-unsealed`: cited lines `:2761`/`:2796` → `:3438`/`:3473`
  (FC-9; exclusion verdict unchanged).
- `dynamic-set-class-getter`: closeout retire-or-revise — row 469's claim
  names no bytes since `899cb35b` (FF-1; f32's record + the factories
  enumeration ride along).
- `queryset-seed-and-model-read`: F2 census refresh at e8's pending
  re-verification (FF-4; verdict stands, counts drifted).
- File `filters/sets.py` s9 rows 2–3: retire at the s9 record — both
  members moved to `inputs.py` (FF-3).

## Independent verification (Worker-2)

### Own trace (recorded from mechanical evidence; see sequencing note)

Sequencing note: this section was written after reading the artifact
header, System trace, Verification, Findings FAM-1 through FC-11,
Defects, Pending execution, Judgment, Implementation, and Index rows.
That ordering slips the worker-2.md expectation-first rule for those
rows. The counts and site lists below were derived before that read
from `git show ITEM_BASELINE` bytes and folder-wide greps, not from
artifact prose; the reconciliation below re-derives every verdict
mechanically rather than matching prose.

Target read at WT bytes: `filters/__init__.py` (162 lines),
`filters/base.py` (1595), `filters/factories.py` (79),
`filters/inputs.py` (1377), `filters/sets.py` (5042). Item-scoped
diff `git diff ITEM_BASELINE -- --name-only` names 3 files:
`filters/sets.py`, `tests/filters/test_sets.py`,
`docs/dry/dry-0_0_15.md`. The plan diff is Worker-0 dispatch +
submission notes only (no Worker-1 symbols); Worker-1's owned set is
exactly the 2 claimed files. No new package/test file was added; the
only new file is this artifact (untracked).

Baseline definition counts (`git show ITEM_BASELINE:sets.py`):

- `by_input_attr`: exactly 2 code reads (baseline L3047 in
  `_normalize_input`, L3797 in `_supplied_leaf_filters`), both
  spelled `filter_lookup_table(cls).by_input_attr if
  cls._meta.model is not None else {}`. Post-edit: 1 read inside
  `FilterSet._leaf_lookups_by_attr` + 2 composers. Count 2, now 1.
  Roles: both pre-edit sites definitions (same inputs `cls`, same
  output, same change reason, coupled: pre-pass and form must agree).
  Owner I would choose: a `FilterSet` classmethod (needs `cls` for
  both the table build and the model check; both consumers are
  classmethods; module-level would take `cls` anyway and imply no
  narrower home). Matches Worker-1.
- `model_for(`: exactly 2 (baseline L4006 in `_scoped_rows`, L4021
  in `_await_scoped_rows`), both spelled
  `base_queryset(model_for(scope), using=parent_db)`. Post-edit: 1
  inside `_scoped_seed_rows` + 2 composers. Count 2, now 1. Roles:
  both definitions (same inputs, same hop-map contract across
  colorings). Owner I would choose: module-level beside the hop
  helpers (pure function of scope type + alias, no `cls`/`self`
  state; both callers are colorings of one map). Matches Worker-1.
- `get_filters()[`: exactly 3 baseline (2 `projection.name` at
  L3782 in `_visibility_hops` and L3853 in `_leaf_gates`, 1
  `child_name` at L3860). Post-edit: 1 `projection.name` inside
  `_projection_child_filter` + 2 composers; the `child_name` read
  stands. Count 2 for the projection contract, now 1; the
  `child_name` site is a different contract (breadcrumb-derived key
  from `_expansion_origin`, not a projection; different inputs and
  change reasons). Roles: the 2 projection reads definitions
  (coupled: visibility and gates must answer for the same child);
  the `child_name` read a distinct definition correctly excluded.
  Owner I would choose: module-level beside the projection helpers
  (pure function of the projection object). Matches Worker-1.

Missed-site sweeps at WT bytes (all folder-wide, body-strength):

- `filter_lookup_table(`: 4 hits (definition, `_build_input_fields`,
  `_leaf_lookups_by_attr`, `_permission_fallback_path`). The three
  consumers read different views (`heads` + `gate_paths` for build,
  `by_input_attr` for leaves, `gate_paths` for the permission
  fallback) with different model-less fallbacks (`{}` for leaves vs
  identity for gates). Not one rule; no third leaf-view site.
- `base_queryset(`: 5 hits (1 in `base.py` without alias, 4 in
  `sets.py`). Only the helper seeds via `model_for(scope)`; the
  other three seed an already-resolved model (`child_model`,
  hop model) on a threaded alias. Different inputs; no third
  scope-seed site. `model_for(` appears exactly once post-edit
  (inside the helper).
- `get_filters()`: code reads are the table build, the helper,
  `_filter_paths`, `_expand_related_filter`, and the `child_name`
  site. Different keys and purposes; the `base_filters` and
  instance-`filters` projection reads are lifecycle-distinct
  (stale template vs per-request copy vs fresh expansion). No
  missed projection-resolution site.
- `_meta.model is not None`: exactly 1 post-edit (inside the
  helper). The `_permission_fallback_path` model-less arm returns
  the attr itself, not an empty map — a permission-gating
  contract, not a leaf-supply contract. Correctly separate.
- Sync/async twins share pure decisions only (`_iter_visibility_steps`,
  the depth assert, `run_permissions=False`); twin bodies stay
  colored. No twin merge missed.

FAM-4/FAM-5 were not discovered in my pre-reading sweep; I learned
their shape from the dispatch summary and the Findings peek. Their
verification below is mechanical (hunk attribution vs the Owned
changes ledger and HEAD bytes), not prose-matching.

### Header-shape ruling (Worker-2)

The artifact opens `# Folder integration ... (run 13)` plus a `Run:`
/ `Submission Status:` prose line instead of the DRY.md-mandated
`# DRY review:` + `Status:` + `Run:` block. Both sibling folder
artifacts in this run use the standard shape. Ruling: acceptable
with a correction note, NOT revision-needed for the shape alone.
The deviation is record-only (title wording + status-line spelling);
every mandated section is present (`System trace`, `Verification`
with Matrix/Enumeration/Challenges, `Findings`, `Defects`, `Pending
execution`, `Judgment`, `Implementation (Worker-1)`), plus the
run-standard `Pins and fingerprints` and `Index rows for Worker-0`
extras the siblings also carry. Returning a fully-traced item with
landed consolidations for a header rewording would spend a pass to
no semantic effect; Worker-2's verdict edit already rewrites the
header Status line, so normalizing the title and Run line there is
minimal and preserves all reasoning. The same standard applies to
any item: a header wording slip with all sections present is
normalized at verification; a shape deviation that hides a missing
mandated section would be revision-needed. On a verified verdict
this header will carry a standard `Status: verified` line in the
DRY.md-mandated header position (line 3, replacing the
`Submission Status:` prose); the title becomes
`# DRY review: filters/ folder integration` and the Run line
`Run: 0.0.15 2026-10-09-13`.

### Reconciliation: FAM-1/2/3 (landed consolidations)

All three CONFIRMED count-2 at BASE, CONSOLIDATED 2 to 1 at WT,
ownership and adapter shapes endorsed.

- Definition counts re-derived from BASE bytes (not artifact prose):
  `by_input_attr` exactly 2, `model_for(` exactly 2,
  `get_filters()[projection.name]` exactly 2 (plus 1 `child_name`
  correctly excluded). Post-edit: each 1 definition + 2 composers.
  No third site for any rule (folder-wide greps: `model_for(` 1
  post-edit, `_meta.model is not None` 1 post-edit,
  `filter_lookup_table(` 4 with distinct views, `base_queryset(` 5
  with distinct inputs).
- Roles: pre-edit pairs are definitions (same inputs, outputs,
  change reasons; FAM-1 and FAM-3 pairs coupled across readers).
  Consumers, oracles (630 package rows + live suites), projections
  (docstrings) listed, not counted. No oracle rewritten to read
  from its owner (new tests are AST censuses over source text,
  importing the module for `__file__` only; existing tests
  untouched, diff +186/-0).
- Ownership challenged and endorsed: FAM-1 classmethod (needs `cls`;
  both consumers classmethods), FAM-2 module-level (pure scope +
  alias; both callers colorings of one map), FAM-3 module-level
  (pure projection read). Narrowest cohesive owners, no reversed
  dependencies. Adapter shapes are one-line compositions, no mode
  flags, no new indirection beyond the shared body.
- Observable equivalence on principle-8 axes: all three extract
  byte-identical pure expressions with unchanged call counts (2
  calls before, 2 via helper after), same short-circuit order
  (unconditional for FAM-1, post-miss for FAM-2, in-walk for
  FAM-3), same exceptions, zero query/transaction/cancellation
  effects (table build caches on the class as before; seed and
  resolution build lazily). The 630-row suite green in two
  independent copies corroborates.
- Structural gates: exact AST multisets (1 definition + 2
  composers each), green in shared tree (3 passed, 0.60s) and in
  verify-1 copy (within the 630). Negative controls re-run in
  verify-1 via the TMPDIR manifest: 3/3 pinned, each 1 failing row
  exactly its declared census, restores byte-identical
  (`d6bb78d1`), runner marks `weakly=False`. The handed
  failability judgment (1 row per entry is the complete pin
  because the mutation is behavior-preserving by construction) is
  correct and tool-endorsed.
- Tests at mandated tier: AST censuses cannot be live (they assert
  source shape, not wire output); behavioral coverage rides the
  630 package rows plus live wire suites. Banned-word sweep over
  all 186 added test lines + 39 added production lines: 0 hits.
- Type gates re-run in verify-1 (fresh copy, shared unmoved):
  basedpyright 0/0/0, floor 0/0/0, truthful-reads errors 0. No new
  cast, `Any`, suppression, or object-widening in the diff; new
  helpers are private with docstrings; no overrides need
  `@override`. Ruff format check + ruff check pass on both
  touched paths.
- Attribution: all 9 sets.py hunks on HEAD-identical lines (removed
  lines verified verbatim at HEAD; added lines carry zero hunt
  tokens); one context-only adjacency at BASE 3043 shares only the
  raise-closing context with the truth-migration hunk, changed
  lines disjoint. Test hunks pure additions (import + EOF append),
  disjoint from the ledgered f51 block at L5211.

### Reconciliation: FAM-4/5 (blocked-on-hunt)

Both CONFIRMED with counts re-derived, blocks verified
independently by diff content vs the Owned changes ledger, tree
untouched, migrations specified correctly.

- FAM-4 (`lookup-table-declared-filters-read`, count-2): WT=BASE
  (both reads `truth.static_attr` + cast + comment), HEAD=1-line
  `getattr`. Both hunks are hunt dirt predating the item, absent
  from the ledger (only f51 owns sets.py/test_sets.py lines, not
  these). Item diff touches no inputs.py line. Caller/callee share
  one object in one flow (`_group_filters_by_head` sole-called by
  `filter_lookup_table`, verified); specified migration (read once
  in caller, pass the map, callee keeps `filterset_cls` for error
  wording) is behavior-preserving and byte-exact. Block correct.
- FAM-5 (`custom-loop-queryset-return-assertion`, count-4 in 2
  wordings): 4 sites verified at WT with `truth.*` spellings, at
  HEAD with `isinstance` + `type().__name__`, at BASE already
  migrated. All four sit in hunt hunks, absent from the ledger.
  Item hunks end at BASE 4047, FAM-5 sites at 4100+. Tree
  untouched. The hunt touching all four identically is empirical
  shared-obligation evidence. Specified migration (shared
  `_require_queryset_result` with per-site subject phrases,
  messages unchanged) preserves both wordings. Block correct.
- Counts: FAM-4 count-2 (shape change moves both), FAM-5 count-4
  (shape change moves all four; phrasing change moves 2 per
  wording; artifact records "4 in 2 wordings" accurately).

### Reconciliation: FC-1..14, FL-1..5, FR-1..10, FF-1..FF-4

Cross-boundary compositions hold (all 14 endorsed after
re-derivation): FC-1 both factories 9 members each with
family-divergent values, hooks diverge semantically as documented;
FC-2 both helper twins thin over the shared owner; FC-3 f59 trio +
4 consumers verified; FC-4 f60 count-2 holds with site 1 still hunt
dirt (stays blocked, no competing migration); FC-5 depth binding +
exactly 5 composers at the ledgered lines; FC-6 zero seal tokens,
6 visibility call sites (s17 verdict stands, census grew by
construction); FC-7 seeds compose by name, `model_for` exactly 1
post-edit (package drift noted for e8); FC-8 sync boundary composes,
R-child exclusion stands (no seal token); FC-9 exclusion holds,
only cited lines stale (correction endorsed); FC-10 all four owner
censuses re-derived (registry 2 live calls, coercion 5, error shape
2+6); FC-11 clear rows hold including the deliberate
`_lookup_table`-outside-`_lifecycle` posture; FC-12 alias sub-rule
coherent post-FF-1; FC-13 every shared-seam call once and only once;
FC-14 zero runtime callers still.

Folder-local rules single-owned (all 21 endorsed): FL-1 2 rows
(17-name manifest verified, helper spellings verified); FL-2 2 rows
(enum septet 7 + bound path 1 = the 8 new members, 13 consumers
counted 11+1+1); FL-3 4 rows (grammar, operators, list-ness with
sole package-wide spelling verified, range cache); FL-4 4 rows
(expansion, conditional, eligibility, range); FL-5 9 rows
(table lifecycle, normalization, visibility derive, hop visibility,
restriction, projection/chain, gate walk, pipeline, channels).
Enumeration counts re-derived and matching: base 51, inputs 52,
sets module 70 (68 + 2 landed), FilterSet 66 methods (1 new +
6 compositions landed), factories 9 class members each,
`__all__` 17. No unassigned member found; matrix discharged
against the real surface on all six axes (no inapplicability
claimed; async census 5-in-sets/0-elsewhere verified).

Rejected merges (all 10 endorsed, each carries its contract
difference + trigger): FR-1 raising-vs-check (2 of 3, trigger third
raising); FR-2 walk-None vs helper-raise (trigger raise adoption,
home f60); FR-3 cardinality threading (nanosecond saving vs contract
coupling, trigger second caller); FR-4 cross-family seeds (three
responsibilities/maps, trigger shared querysets need); FR-5
`_base_manager` vs `_default_manager` (join semantics, trigger
manager parameter); FR-6 twin bodies (per-coloring remainder,
trigger third coloring); FR-7 gate fallback vs leaf view (different
consequents, trigger empty-map adoption — matches my independent
analysis); FR-8 sibling child reads (fresh/published/instance/
breadcrumb, trigger collapse — matches my child_name analysis);
FR-9 recursion drivers (different outputs/timing, trigger fourth
recursion); FR-10 non-walkable raises (shared predicate, different
messages, trigger unification).

Falsification flags (all 4 evidence-verified, non-reopening
correct): FF-1 Layer-6 zero hits + `899cb35b` stat confirms
deletion (factories 79/83 lines); row 469 + f32 + factories
members name no bytes, retire-or-revise at closeout correct (this
item owns none of those records). FF-2 `__all__` 17 counted, file
artifact 16 falsified; current shape homed in 2 new rows, stale
census flagged record-only correct. FF-3 reverse-map zero hits,
now `by_input_attr` in inputs.py; s9 rows 2-3 retire correct.
FF-4 `model_for` 0 falsified (BASE 2, WT 1 post-FAM-2, package 7
files); F2 verdict stands, counts refresh at e8's pending
re-verification correct. No row reopened in any flag; nothing
re-applied.

### Rulings: 26 index rows + 4 corrections (Worker-2)

All 26 ENDORSED for Worker-0 transcription (21 file-local + 3
consolidated + 2 open families) and all 4 corrections ENDORSED.
Reasons: each file-local names the narrowest in-folder owner with
its proving challenge verified (counts above); each consolidated
names its NEW helper with the 2-to-1 evidence verified (counts,
gates, pins); each open family names its candidate owner with the
count and hunt block verified (hunks, ledger absence, zero edits).
Corrections: child-derivation lines verified at `:3438`/`:3473`;
dynamic-getter retirement verified by zero hits + deletion commit;
seed-read census refresh verified by drift counts; s9 rows 2-3
retirement verified by zero hits + move to inputs.py. No row
corrected or rejected; no wording change owed. Worker-0
transcribes verbatim; the 2 open-family rows queue their Family
holding items post-hunt.

### Pending execution, cells, freshness, coupling

Pending execution complete and correctly typed: no `proof:` owed
(every consolidation proof ran complete — 630 suite, 3 gates, 3/3
prove pins in slot-2, all re-run green in verify-1); 5 `gate:`
entries cover the type gates, the suite, and the prove re-run.
The TMPDIR-manifest gate (`prove ... consolidate
~/dry/tmp/folder-filters-failability.json`) re-ran
successfully in verify-1 (3/3 pinned), proving re-runnability at
verification time; at final-gate time it re-runs iff the TMPDIR
file persists (scratch, outside repo and workspace evidence). That
fragility is acceptable: as a `gate:` (not `proof:`) its failure
reopens no item per DRY.md, recording an environment note instead.
Cells `unverified` with inapplicability correctly NOT claimed: the
apply paths thread and pin aliases (`using=parent_db` /
`parent_qs.db` / `queryset.db` at 5+ sites plus hop visibility),
so alias reach is real; the honesty is right and complete.
Freshness fingerprints re-derived and matching for all five folder
files in all three states plus the test blob; excluded modules
cited by file + lines + contract difference per the run standard
(siblings fingerprint folder files only). No cross-finding coupling
exists (three helpers independent, tests independent); FAM-1/FAM-3
note their within-finding reader coupling explicitly. Nothing
accepted alone that must land together.

<!-- LINK DEFINITIONS -->
<!-- Root -->
<!-- docs/ -->
[file-base]: dry-file-filters__base.md
[file-factories]: dry-file-filters__factories.md
[file-init]: dry-file-filters____init__.md
[file-inputs]: dry-file-filters__inputs.md
[file-sets]: dry-file-filters__sets.md
<!-- docs/SPECS/ -->
<!-- docs/builder/ -->
<!-- django_strawberry_framework/ -->
<!-- tests/ -->
<!-- examples/ -->
<!-- scripts/ -->
<!-- .venv/ -->
<!-- External -->
