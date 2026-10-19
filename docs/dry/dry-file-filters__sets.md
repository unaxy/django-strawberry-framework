# DRY review: `filters/sets.py`

Status: verified
Run: 0.0.15 2026-09-30-8

## System trace

The target owns the filter family's declaration, validation, and apply
pipeline: `FilterSet` + `FilterSetMetaclass` (3529 lines, read in full),
plus the row-preserving optimizer's build-time substrate that lives
nowhere else (generation-policy table + ownership oracle, audited-release
gate, generation provenance, exact-class family-profile registry,
candidate metadata + expansion snapshot). Read whole, plus every
connected implementation a sound judgment needs: the mirror twin
[orders-sets][orders-sets]`::OrderSet` (832 lines, whole, FIRST by
behavior + contract), the shared substrate
[sets-mixins][sets-mixins] (whole), the sibling owners
[filters-inputs][filters-inputs]`::LOOKUP_NAME_MAP` /
`::LOGIC_OPERATORS` / `::_field_specs`,
[filters-base][filters-base]`::RelatedFilter` /
`::_GLOBALID_RELATION_PK_ATTR` / `::_relation_uses_non_pk_to_field` /
`::_marked_pk_field_name` / `::GlobalIDFilter` /
`::GlobalIDMultipleChoiceFilter`,
[utils-inputs][utils-inputs]`::GeneratedInputArgumentsFactory` /
`::make_dynamic_set_getter` / `::clear_generated_input_namespace` /
`::promote_set_meta_fields` / `::set_input_type_name`,
[input-values][input-values]`::SetInputTraversal` /
`::iter_active_fields` / `::ActiveField` / `::set_traversal_depth_cap`,
[utils-querysets][utils-querysets]`::base_queryset` /
`::run_in_one_sync_boundary` / `::model_for`,
[utils-relations][utils-relations]`::classify_path` /
`::relation_kind` / `::is_many_side_relation_kind` /
`::path_traverses_to_many`, [utils-permissions][utils-permissions]
(facade mechanics), [order-inputs][order-inputs],
[order-base][order-base]`::RelatedOrder`,
[order-factories][order-factories], [filters-init][filters-init],
[finalizer][finalizer] (owner binding), [relays][relays]
(`implements_relay_node`), [predicates][predicates]
(`correlated_inner_root`, `attach_exists`), [errs][errs], the installed
`django-filter` 26.1 `filter_for_lookup` / `filter_for_field` /
`get_filters` bodies (mirror + empty-body-CSV premises verified
against the RUNNING upstream, not prose), the cookbook
`FilterSetMetaclass.__new__` head (port-delta check), oracles
[test-sets][test-sets] (9027 lines, 265 test functions),
[test-filter-inputs][test-filter-inputs], [test-filter-base][test-filter-base],
live suites (`test_library_api`, `test_scalars_filter_api`,
`test_optimizer_auto_api`, `test_products_visibility_api`,
`test_multi_db`), [glossary][glossary] (22 `FilterSet` mentions,
projection), and the prior sibling artifacts
[dry-file-sets-mixins][dry-file-sets-mixins],
[dry-file-filters-inputs][dry-file-filters-inputs],
[dry-file-filters-base][dry-file-filters-base],
[dry-file-filters-factories][dry-file-filters-factories] as
rejected-candidate triggers only (every reuse below re-verified
fresh against bodies; nothing inherited).

What the target owns (no consolidation inside a file item): sixteen
reuse-consumer records against open index families (every candidate
from the dispatch verified: eleven confirmed consumers, one partial,
four correctly withheld), eighteen file-local rule rows (single
definition each, package-wide second-definition sweep under
Challenges), and five rejections with contract difference + trigger +
home. Zero new index families: the optimizer substrate
(provenance, profiles, candidates, snapshot, audit gate, ownership
oracle) is single-sited in this file (sweep: exactly one `def` per
mechanism package-wide), so it is file-local, not a family.

Consumers of the target (all compose by name): the finalizer bind
subpasses (`_owner_definition` write, expansion drive), the Layer-5
BFS factory (`_build_input_fields` reads resolved filter instances,
never a parallel map), the Layer-6 dynamic getter (`FilterSet` as
base class), both `inputs` namespace clears, the permission
traversal, and the live/package oracles. Oracles are independent:
[test-sets][test-sets] spells expectations literally (0 references to
`LOOKUP_NAME_MAP` / `_FORM_KEY_BY_PYTHON_ATTR`; 265 functions),
live suites assert wire shapes. Projections: the module docstring
(spec-027 layer/decision claims), per-symbol docstrings (each
verified against its body; six load-bearing claims pinned under
Defects as spot-checks held), the cookbook-port note (deltas
documented inline), and DRY.md's worked example (`"__all__"`
separation re-derived fresh at its owner in R-1).

## Verification

### Matrix

1. **Cross-flavor mirroring (orders twin FIRST, by behavior +
   contract).** Both wholes read. Shared substrate confirmed
   consumer-side: `_lifecycle` declarations (filter with snapshot
   `extra`, order without), `_permission` configs,
   `::expanded_once` (filter with `on_reentry`, order without),
   `::should_cache_expansion`, `::require_re_readable_field_declaration`,
   `::collect_related_declarations` (filter
   `inherit_from_bases=False` over `declared_filters` + `class_items`
   + `base_declarations_attr`; order `True` over class-body `attrs`),
   `_field_type_suffix` (filter overrides, order keeps default).
   Divergences are contract pairs, rejected R-m1..R-m4, never
   merged: expansion build (filter expands related graphs + freezes
   candidate metadata + publishes snapshot + writes `base_filters`;
   order merges meta fields + related orders, no snapshot, no
   `base_filters`, no reentry); normalizers (filter operator-bag +
   logic-wire-copy + related-strip + range patch; order flat
   purity-attested terms); apply pairs (filter visibility-derive +
   related-constrain + form-validate + `.qs` + logic tree; order
   permission-check + annotate/order_by); metaclasses (django-filter
   subclass vs plain `type`, opposed inherit policies, filter-only
   tombstone rebuild + declared-provenance stamp); `apply`
   dispatcher (filter-only, spec-028 DoD 4(c) stated on `OrderSet`);
   `check_permissions` bound delegate (filter-only, cookbook shape);
   `_prepare_permission_input` (order-only lazy-spec warm-up;
   filter specs are module-materialized). Forms/mutations/rest
   carry no related-set graph and import nothing here (withheld,
   verified 0 hits). Trigger for any R-m row: a change to one
   side's contract that must move the other.
2. **Sync/async twins (by behavior, not shape).** Three `async
   def` in the target (`_derive_related_visibility_querysets_async`,
   `_collect_nested_visibility_querysets_async`, `apply_async`)
   against their sync twins. One body is impossible (principle 5):
   the async derive must await consumer `async get_queryset`
   hooks mid-traversal; the sync derive must raise
   `SyncMisuseError` there instead; `apply_async` alone pre-walks
   logic arms and wraps finalize in `run_in_one_sync_boundary`.
   The contrast is recorded at both owners (twin docstrings name
   each other's `run_permissions=False` / `parent_db` / `_depth`
   threading). Order twins differ again (no visibility derive, no
   pre-walk; only the permission wrap) — same verdict, R-m3.
   Trigger: a twin pair whose await points collapse to one
   coloring.
3. **Derived rather than repeated knowledge.**
   `_FORM_KEY_BY_PYTHON_ATTR` derives from `LOOKUP_NAME_MAP` once
   at import (P1 pins equality with the first-match scan, not just
   spot values); `_input_traversal` reads the contained traversal
   (`is`, P5 both families); `binding_attrs` derives the reset
   tuple; `.origin` reads the registered type (never `.type` /
   `.type_cls`; stated at both read sites); `FILTER_DEFAULTS`
   installs the authored table (never a snapshot of the mutable
   global; the ownership anchor is the private normalized
   baseline by VALUE). The one deliberate mirror is
   `_generation_origin_for_field`: upstream exposes no selection
   API, so it replicates upstream's exact merged-walk +
   `isnull`-Boolean reselect (verified line-for-line against
   installed 26.1; P8 pins pristine/override/unresolvable/isnull
   arms, including the TextField-MRO subtlety the first probe
   draft got wrong). No name-by-concatenation, no `_meta`
   re-derivation (`get_fields` narrows `super().get_fields()`),
   no settings re-read. Trigger: a derivation whose source table
   moves without it.
4. **Round-trip pairs.** Stamp (`_stamp_generation_provenance`
   at three generation sites + metaclass declared stamp) vs read
   (`filter_generation_provenance`, `None` = fail-closed) vs
   inherit (`_expand_related_filter` appends breadcrumbs via
   `replace`, never mutates the child record); publish (one
   atomic snapshot under the write gate) vs reset
   (`binding_attrs` walk); build profile
   (`_family_profile_for`) vs consume (`routable` bit only);
   normalize (wire keys into `data`) vs compose
   (`_evaluate_logic_tree` off `data`, tree keys absent from
   `cleaned_data` by django-filter form design); bind (finalizer
   writes `_owner_definition`) vs resolve (three `.origin`
   readers + `registry.get` fallback that explicitly refuses to
   recompose `primary_for`); `LOGIC_OPERATORS` declare
   (inputs) vs iterate (all three logic traversals share the one
   `_iter_logic_branches`, both spellings). Each half single-sited.
5. **Other media.** Production, oracles, projections classified
   per finding; only definitions counted in Challenges. Six
   docstring claims re-derived true (pinned under Defects, not
   defects): no `__init__` on `FilterSet` (AST: 40 methods, none
   `__init__`); `super().filter_for_field` calls
   `cls.filter_for_lookup` (installed source:
   `filter_class, params = cls.filter_for_lookup(...)`);
   empty-body dynamic CSV premise (`class ConcreteInFilter
   (BaseInFilter, filter_class): pass` in installed 26.1);
   `is_many_side_relation_kind(relation_kind(field))` cardinality
   call; metaclass alias write-back; cookbook deltas
   (tombstone rebuild, declared stamp) documented inline, not
   silent. [test-sets][test-sets] never derives from an owner.
   Spec-027 decisions + glossary are contract sources, never
   counted.
6. **Enforcement by omission.** Generation-site census: every
   instance-returning path in `filter_for_field` stamps
   (default + both replacements; `None` returns no filter, so no
   row exists — fail-closed, upstream-identical); declared
   leaves stamped in the metaclass (own-ness from the class body,
   never from the private slot; borrowed-instance
   restamp closes the super()+borrow hole); expanded copies
   inherit, never mint. `distinct` stamping is framework-origin
   only by the recorded row-preserving rationale; consumer
   `distinct` keeps working on the outer path (documented in
   `CandidateFilterMetadata`, not an omission). Depth caps fire
   on all four entry shapes (both applies, permission walk,
   logic evaluation + async pre-walk). `_normalize_input`
   dispatches all three `ActiveField` kinds (LOGIC copied,
   RELATED stripped, LEAF normalized). Dual-spelling consistency
   traced end to end: permission recursion, async pre-walk, and
   Q composition all read through the one `_iter_logic_branches`,
   so a wire-spelled arm is gated everywhere it is applied
   (spot-check held). Unknown top-level keys degrade to
   upstream form semantics (form drops them; unreachable over
   the wire since the generated input class is closed) —
   spot-check held, no contract source for a stricter rule. No
   gap: no defect.

### Enumeration

Instrument: `ast` parse of the target. 74 top-level statements
(module docstring + 28 imports + 45 others, incl. one
`TYPE_CHECKING` guard). Imports + docstring + guard are
machinery/projection, not rules. 96 rule-bearing leaves: 43
module-level + `FilterSetMetaclass.__new__` + 52 `FilterSet`
members (12 class attrs + 40 methods, 3 of them `async`).
Every leaf lands below: 16 in reuse-consumer rows, 80 in
file-local rows L1–L18. No `__all__` manifest (the 24 hits are
the `Meta.fields` `"__all__"` string literal, verified by AST).

| # | Member(s) | Home |
|---|---|---|
| 1 | `_LOGIC_PYTHON_ATTRS` | `filter-logic-operators` (reuse, emission) |
| 2 | `_FORM_KEY_BY_PYTHON_ATTR` | `lookup-name-spelling-grammar` (reuse, reverse) |
| 3 | `FilterSet._form_key_for_python_attr` | `lookup-name-spelling-grammar` (reuse, reverse) |
| 4 | `FilterSet._iter_logic_branches` | `filter-logic-operators` (reuse, emission) |
| 5 | `FilterSet._field_type_suffix` | `set-type-naming` (reuse, config) |
| 6 | `FilterSet._permission` | `active-input-permission-facade` (reuse, config) |
| 7 | `FilterSet._MAX_LOGIC_DEPTH` | `active-input-permission-facade` (reuse, cap) |
| 8 | `FilterSet._permission_fallback_path` | `active-input-permission-facade` (reuse, hook) |
| 9 | `FilterSet._check_permission_depth` | `active-input-permission-facade` (reuse, hook) |
| 10 | `FilterSet._run_logic_permission_checks` | `active-input-permission-facade` (reuse, hook) |
| 11 | `FilterSet.check_permissions` | `active-input-permission-facade` (reuse, delegate) |
| 12 | `FilterSet._lifecycle` | `subsystem-clear-lifecycle` (reuse, population) |
| 13 | `FilterSet._owner_definition` | `subsystem-clear-lifecycle` (reuse, population) |
| 14 | `FilterSet._expanded_filters` | `subsystem-clear-lifecycle` (reuse, population) |
| 15 | `FilterSet._expanded_snapshot` | `subsystem-clear-lifecycle` (reuse, population) |
| 16 | `FilterSet._is_expanding_filters` | `subsystem-clear-lifecycle` (reuse, population) |
| 17 | `_lookups_for_field_class_cache`, `_lookups_for_field` | L1 |
| 18 | `_MODEL_CHOICE_ONLY_EXTRAS`, `_strip_model_choice_extras` | L2 |
| 19 | `_forward_relation_extra`, `_forward_m2m_extra`, `_reverse_o2o_extra`, `_reverse_rel_extra`, `_PUBLIC_PACKAGE_FILTER_DEFAULTS`, `FilterSet.FILTER_DEFAULTS` | L3 |
| 20 | `_NormalizedPolicyEntry`, `_normalize_policy_entry`, `_PACKAGE_POLICY_BASELINE`, `FilterSet._generation_origin_for_field` | L4 |
| 21 | `_AUDITED_DJANGO_FILTER_RANGE`, `_release_is_audited`, `_DJANGO_FILTER_OPTIMIZER_AUDITED` | L5 |
| 22 | `_GENERATION_PROVENANCE_ATTR`, `FilterOrigin`, `FilterGenerationProvenance`, `filter_generation_provenance`, `_stamp_generation_provenance`, `_FRAMEWORK_GENERATED_ORIGINS` | L6 |
| 23 | `_FilterFamilyProfile`, 8 singletons, `_ALL_FAMILY_PROFILES`, `_FILTER_FAMILY_REGISTRY`, `_EmptyBodyDynamicCsvReference`, `_EMPTY_BODY_DYNAMIC_CSV_ATTRS`, `_dynamic_csv_profile_for`, `_family_profile_for` | L7 |
| 24 | `CandidateFilterMetadata`, `ExpansionSnapshot`, `_candidate_metadata_for`, `FilterSet._expansion_snapshot` | L8 |
| 25 | `FilterSetMetaclass`, `FilterSetMetaclass.__new__` | L9 |
| 26 | `_expand_related_filter` | L10 |
| 27 | `FilterSet.get_filters` | L11 |
| 28 | `FilterSet.get_fields` | L12 |
| 29 | `FilterSet.filter_for_field`, `FilterSet.filter_for_lookup`, `FilterSet._is_generation_capable`, `FilterSet._is_own_pk_under_relay_owner`, `FilterSet._relay_filter_class_for_field`, `FilterSet._resolve_relation_target_type` | L13 |
| 30 | `FilterSet._iter_input_items`, `FilterSet._validate_logic_branch_shape`, `FilterSet._validate_logic_element_shape`, `FilterSet._normalize_input`, `FilterSet._require_range_patch_filter`, `FilterSet._operator_bag_items` | L14 |
| 31 | `FilterSet._iter_visibility_steps`, `FilterSet._derive_related_visibility_querysets_sync`, `FilterSet._derive_related_visibility_querysets_async`, `FilterSet._collect_nested_visibility_querysets_async`, `FilterSet._target_type_for_related_filter` | L15 |
| 32 | `FilterSet._logic_depth`, `FilterSet._apply_info`, `FilterSet._nested_qs_by_branch_id`, `FilterSet._raise_logic_depth_exceeded` | L16 |
| 33 | `FilterSet._invoke_suppressing_framework_distinct`, `FilterSet._apply_flat_leaves`, `FilterSet.filter_queryset`, `FilterSet._evaluate_logic_tree`, `FilterSet._q_for_branch`, `FilterSet._apply_related_constraints` | L17 |
| 34 | `FilterSet._apply_common_prelude`, `FilterSet._apply_common_finalize`, `FilterSet.apply_sync`, `FilterSet.apply_async`, `FilterSet.apply`, `FilterSet._validate_form_or_raise` | L18 |
| 35 | metaclass `collect_related_declarations` call; `f.filterset` / `related_filter.filterset` / `child._owner_definition.origin` reads; `get_filters` `expanded_once` call; `should_cache_expansion` call; `get_fields` `require_re_readable_field_declaration` call; `apply_async` `run_in_one_sync_boundary` wrap; `base_queryset(child_model, using=parent_db)`; `setattr(..., _GLOBALID_RELATION_PK_ATTR, True)` + `_relation_uses_non_pk_to_field` read; `registry.get` x2 + `.origin` reads; `classify_path` / `relation_kind` / `is_many_side_relation_kind` / `path_traverses_to_many` reads | consumer facets inside L9/L11/L12/L13/L15/L18 (roles recorded in Findings; homes stay put) |

Row 35 names call sites, not new homes: the definitions they
compose live in their index families
(`related-set-target-lifecycle`, `related-declaration-collection`,
`set-expansion-once-skeleton`, `set-expansion-cache-write-gate`,
`re-readable-field-declaration-gate`, `one-sync-boundary`,
`child-queryset-alias-inheritance`,
`queryset-seed-and-model-read` (partial: `base_queryset` call
present, `model_for` 0 hits — for the family item to adjudicate),
`globalid-relation-pk-marker`, `type-registry-model-type-map`
(`primary_for` explicitly refused by comment),
`orm-lookup-path-resolution`). Correctly withheld (0 hits):
`set-arguments-factory-bfs`, `dynamic-set-class-getter`,
`globalid-decode-input-hardening`, `sealed-execution-queryset`;
`lazy-related-class-resolution` transitive only (no direct call).

### Challenges

Authoritative definitions counted only; consumers, oracles,
projections listed, not counted. Probes P1–P9
(`docs/dry/temp-tests/dry-file-filters__sets/probe_sets.py`, 93
asserts, execution-verified read-only in the shared tree:
throwaway subclasses only, shipped classes read never built, no
DB, no source mutation; target blob `4ab65a26` before and after).
Static review suffices elsewhere (single definitions composed by
name; twin colorings inspected, not executed — no consolidation
proposed, so no equivalence gate is owed).

- `lookup-name-spelling-grammar` (reuse): rename a Django
  lookup's python attr → 1 (`LOOKUP_NAME_MAP`); change
  first-wins to last-wins → 1 (the `reversed` construction);
  drop verbatim fallthrough → 1 per side (owner `.get`,
  reverse dict `.get`) — two coordinated edits inside ONE
  grammar, both halves read the one table (P1 pins the reverse
  equals the first-match scan over all 26 entries).
- `filter-logic-operators` (reuse): add a fourth operator → 1
  (`LOGIC_OPERATORS` + descriptor; `BY_*` maps derive);
  change `not_` cardinality → 1 (`is_sequence` axis);
  change Q composition → 1 (`_compose_*`). Emission (row 1/4,
  `_permission` `logic_keys`, `_normalize_input` wire copy,
  `_evaluate_logic_tree` `op.compose`) iterates, never
  restates (P2).
- `set-type-naming` (reuse): change the filter bag suffix → 1
  (row 5 declaration). `set-arguments-factory-bfs` non-membership
  holds: 0 factory references in the target.
- `related-set-target-lifecycle` / `related-declaration-collection`
  (reuse, consumer-only): flip the filter inherit policy → 1
  call-site argument; change bind-once semantics → 1
  (`_bind_owner`); no declaration here (0 `_bind_owner` /
  `resolve_lazy_class` hits; resolution entered only through
  `.filterset` property reads).
- `set-expansion-once-skeleton` / `set-expansion-cache-write-gate`
  (reuse, consumer-only): change guard lifetime → 1
  (`expanded_once`); add a third write condition → 1
  (`should_cache_expansion`); give orders an `on_reentry` →
  1 call site. The `_build` publish spelling stays family-owned
  (snapshot + `base_filters` side effect), correctly unshared.
- `re-readable-field-declaration-gate` (reuse, consumer-only):
  admit generators → 1 (predicate); drop the filter string
  exemption → 1 call-site policy (top-level `"__all__"` IS a
  string; upstream rejects other strings).
- `active-input-permission-facade` (reuse): new shared walker →
  1 (mixin); sixth traversal axis → 1 (traversal shape);
  filter remap → 1 (row 8); depth cap → 1 (row 7 + row 9);
  label wording → 1 (mechanics). P5 pins traversal identity
  both families + remap split + lifecycle tuples.
- `subsystem-clear-lifecycle` (reuse, population): add a family
  cached slot → reset population moves in 1 (`binding_attrs`
  derivation) + declaration + publish adapters; rename →
  declaration only, clear plus skeleton follow by construction
  (P5 pins both lifecycle tuples + traversal identity both
  families; the clear body reads `binding_attrs`, never a slot
  literal).
- `one-sync-boundary` (reuse, consumer-only): change boundary
  semantics → 1 (`run_in_one_sync_boundary` at its owner); add an
  entry shape → consumer call site. The target's `apply_async`
  wraps finalize in the one boundary and pre-walks logic arms
  (async-only); `apply_sync` never enters it — 0 definitions
  here, 1 system-wide.
- `child-queryset-alias-inheritance` (reuse, consumer): change alias
  inheritance → 1 (`base_queryset` at its owner); the target calls
  `base_queryset(child_model, using=parent_db)` at the
  related-visibility seam — consumer, 0 definitions here.
- `queryset-seed-and-model-read` (reuse, partial): `base_queryset`
  call present (2 hits), `model_for` 0 hits — seed half consumed,
  model-read half absent at this seam; for the family item to
  adjudicate. Change either half → 1 definition at the owner;
  0 here.
- `globalid-relation-pk-marker` (reuse, consumer): change the marker
  attr → 1 (`_GLOBALID_RELATION_PK_ATTR` at its owner); change the
  non-pk-`to_field` predicate → 1
  (`_relation_uses_non_pk_to_field`); the target stamps (one
  `setattr`) and reads the predicate in `filter_for_field` —
  consumer, 0 definitions here.
- `type-registry-model-type-map` (reuse, consumer): change the
  model-to-type map → 1 (registry owner); the target reads
  `registry.get` twice plus three `.origin` readers, and explicitly
  refuses to recompose `primary_for` (comment at the seam) —
  consumer, 0 definitions here.
- `orm-lookup-path-resolution` (reuse, consumer): change path
  classification → 1 (`classify_path`); change cardinality → 1
  (`relation_kind` + `is_many_side_relation_kind` read as one
  call); change to-many traversal → 1 (`path_traverses_to_many`);
  the target reads all four at the visibility/constrain seams —
  consumer, 0 definitions here.
- Correctly withheld (0 hits, verified): `set-arguments-factory-bfs`
  (no `GeneratedInputArgumentsFactory` reference),
  `dynamic-set-class-getter` (no `make_dynamic_set_getter`),
  `globalid-decode-input-hardening` (no decode symbols),
  `sealed-execution-queryset` (no seal symbols);
  `lazy-related-class-resolution` transitive only (no direct
  `resolve_lazy_class` / `_bind_owner` call — entered only through
  `.filterset` property reads).
- L1 `_lookups_for_field` memo: exclude another transform → 1
  (the exclusion predicate); change the memo key → 1 (class-keyed
  cache); return the cached list itself → 1 (the copy on return;
  P6 rejects aliasing: a caller-appended mutant never leaks).
- L2 ModelChoice extras strip: add an extras key → 1 (the extras
  table); change strip timing → 1 (the strip helper).
- L3 relation extras + defaults table: add a relation shape → 1
  (its extra callable); change a default mapping → 1 (the defaults
  table the class attr installs, never a snapshot of the mutable
  global — ownership anchor is the private normalized baseline by
  value).
- L4 policy table + baseline + origin oracle: add a policy axis → 1
  (entry + table); change the baseline → 1 (by value); change the
  reselect rule → 1 (the oracle, which deliberately mirrors
  upstream's merged-walk + `isnull`-Boolean reselect — upstream
  exposes no selection API; P8 pins pristine/override/
  unresolvable/isnull arms).
- L5 audit gate: audit another release → 1 (range table); change
  parse strictness → 1 (the predicate; P4 pins fail-closed parses
  plus the env-consistent flag).
- L6 provenance: change the record shape → 1 (the record); change
  the fail-closed default → 1 (the reader: `None` = unstamped);
  add a framework origin → 1 (the origins set; P9 pins the
  stamp/read round-trip).
- L7 family profiles + dynamic-CSV validator: add a family → 1
  (singleton + registry row); change a structural predicate → 1
  (exact-class for shipped families, two-base structural shape for
  dynamic CSV; P3 pins scalar/choice/model-choice/globalid arms,
  subclass/three-base/body-added refusals, and the closed set).
- L8 candidate metadata + snapshot: add a metadata field → 1 (the
  record); change snapshot scope → 1 (published atomically under
  the write gate; reset walks `binding_attrs`).
- L9 metaclass: flip the collect policy → 1 call-site argument
  (consumer config of the shared collector); change the tombstone
  rebuild → 1 (here); change the declared-provenance stamp → 1
  (here; own-ness from the class body, never from the private
  slot — the borrowed-instance restamp closes the super()+borrow
  hole).
- L10 related expansion: change the breadcrumb shape → 1; mint
  instead of inherit → 1 (the inherit rule: expanded copies append
  breadcrumbs via `replace`, never mutate the child record).
- L11 `get_filters` publish: change the publish population → 1
  (the `_build` closure: snapshot + `base_filters` side effect);
  change the guard lifetime → 1 per guard at its owner (consumer
  call sites here).
- L12 `get_fields` narrow: change per-field expansion → 1 (the
  dict branch through `_lookups_for_field`, transforms excluded);
  change the sweep → 1 (the top-level string branch over
  `model._meta`, PK added, M2M removed) — two branches, one
  owner, distinct contracts (R-1 records the separation).
- L13 generation conditional: add a generation seam → 1 (here);
  change the capability predicate → 1 (identity, not spelling; P7
  pins pristine/override/shadow/init arms); change the relay
  target rule → 1; every instance-returning path stamps (default +
  both replacements; `None` returns no filter so no row exists —
  fail-closed, upstream-identical).
- L14 normalization: add an input kind → 1 (the dispatcher, which
  covers all three `ActiveField` kinds: LOGIC copied, RELATED
  stripped, LEAF normalized); change a shape rule → 1; change
  range-patch membership → 1 (the patch filter).
- L15 visibility derive: add a visibility step → 1 (the step
  iterator); change the await seam → 1 per twin coloring (the
  async derive awaits consumer `async get_queryset` hooks
  mid-traversal, the sync derive raises `SyncMisuseError` there;
  one body is impossible — R-m3 records the contrast at both
  owners).
- L16 depth/info channels: change the cap → 1 (cap value + the
  raiser); add a channel → 1 (caps fire on all four entry shapes:
  both applies, permission walk, logic evaluation + async
  pre-walk).
- L17 flat-leaf + logic tree: change Q composition → 1 (the branch
  composer off `data`); change the flat-leaf adapter → 1; change
  the related-constrain rule → 1 (`distinct` stamping is
  framework-origin only by the recorded row-preserving rationale;
  consumer `distinct` keeps working on the outer path).
- L18 apply pipeline: add a pipeline stage → 1 (prelude/finalize
  pair); change dispatch policy → 1 (the dispatcher, filter-only
  by the recorded DoD); change form-failure semantics → 1 (the
  validate-or-raise helper; unknown top-level keys degrade to
  upstream form semantics — spot-check held, no contract source
  for a stricter rule).
- R-m1 filter-vs-order expansion build (rejection): change one
  side's publish contract → 0 here + 0 there as shared (each side
  keeps its own `_build`: filter expands related graphs + freezes
  candidate metadata + publishes snapshot + writes `base_filters`;
  order merges meta fields + related orders, no snapshot, no
  `base_filters`, no reentry). Difference + trigger + home under
  Findings.
- R-m2 filter-vs-order normalizers (rejection): change one side's
  normalize contract → 0 shared (filter operator-bag +
  logic-wire-copy + related-strip + range patch; order flat
  purity-attested terms). Difference + trigger + home under
  Findings.
- R-m3 filter-vs-order apply pairs + twin coloring (rejection):
  change one side's apply contract → 0 shared (filter
  visibility-derive + related-constrain + form-validate + `.qs` +
  logic tree; order permission-check + annotate/order_by; async
  pre-walk + boundary wrap filter-only). Difference + trigger +
  home under Findings.
- R-m4 filter-vs-order metaclasses (rejection): change one side's
  class-construction contract → 0 shared (django-filter subclass
  vs plain `type`; opposed inherit policies; filter-only tombstone
  rebuild + declared-provenance stamp; filter-only `apply`
  dispatcher + `check_permissions` delegate; order-only
  `_prepare_permission_input` lazy-spec warm-up). Difference +
  trigger + home under Findings.
- R-1 per-field `"__all__"` expansion vs model-level `"__all__"`
  sweep (rejection): change either lookup set or sweep membership
  → the other does not move (share a token, not a contract).
  Difference + trigger + home under Findings (durable home: the
  `get_fields` docstring).

Package-wide mechanism sweep (every `def` per mechanism; call sites
as consumers): the optimizer-substrate mechanisms (provenance
stamp/read, family profiles, candidate metadata, snapshot publish,
audit predicate, ownership oracle) are defined exactly once
package-wide — only other references are the oracle file and
same-file consumers — so they are file-local rows (L4–L8), not a
family. No consolidation is proposed anywhere in this item, so no
behavioral-equivalence gate is owed (principle 8: inspection
suffices for single definitions composed by name; execution pins
what ordering/await shape decides via P1–P9).
## Independent verification (Worker 2)

Own trace, recorded before reconciling with W1's `## Findings` (which is
absent — see D1). Target read in full (3529 lines, blob
`4ab65a26b0ccf56f7f40f4938282bba9690673d1`, equals `HEAD` blob);
`orders/sets.py` read for the mirror (top 31 statements; `OrderSet`
16 members = docstring + 5 attrs + 10 methods, 1 `async`); `sets_mixins.py`
permission/lifecycle owners, `filters/inputs.py` grammar owners,
`optimizer/predicates.py` (`correlated_inner_root` / `attach_exists`,
consume-by-name), and the probe re-run below inspected.

### Own rule derivation + owners I would choose

- Grammar reverse half (`_FORM_KEY_BY_PYTHON_ATTR`,
  `FilterSet._form_key_for_python_attr`): consumer of
  `filters/inputs.py::LOOKUP_NAME_MAP`. Owner: inputs. Agree.
- Logic emission (`_LOGIC_PYTHON_ATTRS`, `_iter_logic_branches`):
  consumer of `filters/inputs.py::LOGIC_OPERATORS`. Owner: inputs. Agree.
- Naming (`_field_type_suffix = "FilterInputType"`): consumer of
  `sets_mixins.py::ClassBasedTypeNameMixin`. Owner: sets_mixins. Agree.
- Permission facade (`_permission`, `_MAX_LOGIC_DEPTH`,
  `_permission_fallback_path`, `_check_permission_depth`,
  `_run_logic_permission_checks`, `check_permissions`): consumer of
  `sets_mixins.py::ActiveInputPermissionMixin` + `utils/input_values.py`
  traversal. Owner: sets_mixins. Agree.
- Lifecycle population (`_lifecycle`, `_owner_definition`,
  `_expanded_filters`, `_expanded_snapshot`, `_is_expanding_filters`):
  consumer of `sets_mixins.py::SetLifecycleAttrs` + the registry clear bus.
  Owner: sets_mixins/registry. Agree.
- Everything else (memo, extras strip, policy table + baseline + origin
  oracle, audit gate, provenance stamp/read, family profiles + dynamic-CSV
  validator, candidate metadata + snapshot, metaclass, expansion, get_filters
  publish, get_fields `__all__` pair, generation conditional + capability +
  pk/relay/target seams, normalization + logic-shape + range-patch +
  operator-bag, visibility derive sync/async + nested pre-walk, depth/info
  channels, flat-leaf adapter + logic tree, prelude/finalize/sync/async/
  dispatcher + form validate): file-local. Each `def` swept package-wide
  with exactly one definition site; only other references are the oracle
  `tests/filters/test_sets.py` and same-file consumers. Agree.
- Optimizer-substrate ruling: provenance / profiles / candidates /
  snapshot / audit gate / ownership oracle are rightly file-local, not a
  family. Sweep: each mechanism has exactly one `def` package-wide;
  `routable` / `CandidateFilterMetadata` / `ExpansionSnapshot` /
  `FilterGenerationProvenance` / `_FILTER_FAMILY_REGISTRY` referenced only
  in the target + `tests/filters/test_sets.py` (oracle role). No second
  definition in `optimizer/` (`field_meta.py::fk_id_elision_eligible` is a
  different rule — fetch-side FK elision, unrelated contract and trigger).
  `optimizer/predicates.py::correlated_inner_root` /
  `::attach_exists` are consumed by name (import + 2 call sites), never
  restated. No hidden family. Agree with W1.

### Enumeration check (member-by-member vs own AST count)

Instrument: `ast` parse. 74 top-level statements = module docstring + 28
imports + 45 others (incl. one `TYPE_CHECKING` guard). `FilterSet` body =
53 = docstring + 12 class attrs (`FILTER_DEFAULTS`, `_owner_definition`,
`_expanded_filters`, `_expanded_snapshot`, `_is_expanding_filters`,
`_lifecycle`, `_permission`, `_MAX_LOGIC_DEPTH`, `_logic_depth`,
`_apply_info`, `_nested_qs_by_branch_id`, `_field_type_suffix`) + 40
methods (3 `async`: `_derive_related_visibility_querysets_async`,
`_collect_nested_visibility_querysets_async`, `apply_async`). Metaclass
body = docstring + `__new__`. Rule-bearing leaves = 43 module-level
(excl. the `FilterSet` container) + nested `FilterSetMetaclass.__new__` +
52 `FilterSet` members = 96. Every leaf lands: rows 1–16 (16 reuse
leaves, each verified present with the stated role), L1–L18 file-local
rows sum to 80 (L9 covers both the metaclass statement and its nested
`__new__`), row 35 call-site facets all present (`expanded_once` /
`should_cache_expansion` / `require_re_readable_field_declaration` /
`collect_related_declarations` calls; `f.filterset` /
`related_filter.filterset` / `child._owner_definition.origin` reads;
`run_in_one_sync_boundary` wrap; `base_queryset` 2 hits, `model_for` 0
hits — partial as stated; pk-marker setattr + read; `registry.get` x2;
`.origin` reads; `classify_path` / `relation_kind` /
`is_many_side_relation_kind` / `path_traverses_to_many` reads). Withheld
at 0 hits confirmed: `GeneratedInputArgumentsFactory` /
`make_dynamic_set_getter` (0), globalid-decode symbols (0), seal symbols
(0); `resolve_lazy_class` / `_bind_owner` 0 (consumer-only holds). No
`__all__` manifest (all 21 `__all__` hits are the `Meta.fields` string
literal / prose). Counts agree with W1 exactly.

### Matrix vs real surface

1. Cross-flavor: mirror read first hand. Divergences confirmed in bodies:
   `inherit_from_bases=False` + declared/class-items/base-attr args here vs
   `True` over class-body attrs there; `on_reentry` here only; no
   `_field_type_suffix` override there (keeps default); no `apply`
   dispatcher there (only `apply_sync`/`apply_async`); no
   `check_permissions` delegate there; `_prepare_permission_input`
   order-only. Axis discharged.
2. Sync/async: 3 async confirmed; one body impossible (consumer `async
   get_queryset` awaits vs `SyncMisuseError`; async-only pre-walk +
   boundary wrap). Contrast recorded at both owners' docstrings. Axis
   discharged.
3. Derived knowledge: reverse-map equality re-proven by probe P1 re-run
   (first-match scan over all 26 entries, passed); `binding_attrs`
   derivation, `.origin` reads, normalized-by-value baseline confirmed by
   read; deliberate `_generation_origin_for_field` mirror reasoned
   (no upstream selection API) with P8 arms passing. Axis discharged.
4. Round-trip pairs: stamp/read/inherit, publish/reset, profile/consume,
   normalize/compose, bind/resolve, declare/iterate — each half
   single-sited by read. Axis discharged.
5. Other media: oracle independence verified — 0 `LOOKUP_NAME_MAP` /
   `_FORM_KEY_BY_PYTHON_ATTR` references in `tests/filters/test_sets.py`;
   no-`__init__` (AST) and no-`__all__`-manifest claims verified;
   remaining docstring claims read-consistent. Axis discharged.
6. Omission: generation-site census, declared-stamp own-ness,
   inherit-not-mint, depth caps, 3 `ActiveField` kinds, single
   `_iter_logic_branches` for dual spellings, unknown-key upstream
   semantics — read-consistent; no contract source for a stricter rule,
   so no gap and no defect. Axis discharged.

### Counts, roles, equivalence, zero-edit

- Definition counts (1 per reuse challenge) confirmed against single-owner
  tables; consumers/oracles/projections listed, not counted. No oracle
  rewritten (item-scoped diff empty; tests untouched).
- Principle 8: no consolidation proposed, so no equivalence gate is owed.
  Probe re-run in the shared tree (read-only: throwaway subclasses, no DB,
  no source mutation): `W1 PROBES PASSED: 93`, target blob `4ab65a26`
  before and after. Twin colorings inspected, not executed — acceptable
  with no consolidation proposed.
- Zero-edit confirmed by me: `git diff
  52ba3e8dc765b1442223668f7d0fe9b536b831a6 --
  django_strawberry_framework/filters/sets.py` is 0 bytes;
  `git status --short -- django_strawberry_framework/filters/sets.py` is
  clean; working blob equals `HEAD` blob. Coverage + assignment validate
  (96/96 leaves homed); no production edit owed by a file item.

### Rejections, fingerprints, gates, Pending, coupling — NOT verifiable

The artifact ends mid-`### Challenges` (line 320, literal
`...[truncated 9117 chars]`). The remainder of Challenges, all of
`## Findings` (R-m1–R-m4 + R-1 contract differences + triggers +
  fingerprints + structural gates + negative controls + coupling), plus
`## Defects`, `## Pending execution`, `## Judgment`, and the
`<!-- LINK DEFINITIONS -->` block are absent, so none of these can be
checked. One surviving fingerprint matches: Challenges cites target blob
`4ab65a26` = working/`HEAD` blob. Twin-gate negative controls, Pending
absence, and coupling marks cannot be confirmed from what is on disk.

### AGENTS.md prose check

Surviving citations use `path::Symbol` form, no line numbers, no process
provenance. Violation, consequent on D1: the ~20 reference-style link ids
used (`[orders-sets]`, `[test-sets]`, …) have no bottom definition block
(file truncated before it), so cross-file links are unresolvable.

### Pass-2 completion check (Worker 2, resuming own pass)

D1 discharged. Truncation marker gone from W1 text (the only remaining
`truncated 9117` hits are this section's own historical quotes of D1).
Artifact 482 → 1696 lines: Challenges remainder covers the 6 remaining
reuse rows + withheld note + L1–L18 + R-m1–R-m4/R-1; `## Findings` holds
39 records (16 reuse + L1–L18 + 5 rejections), each with all 10 DRY.md
fields — spot-checked R-m1–R-m4 + R-1 (difference + trigger + home all
real against read bodies) and L4/L8/L18 + reuse rows (freshness hashes
`4ab65a26` / `6044ab1a` / `82b52d97` / `1539b66c` all re-hash clean;
HEAD `9031cb3d`). `## Defects` (none), `## Pending execution` (none —
P1–P9 executed, twin colorings need no gate, sharded cells inapplicable
by construction), `## Judgment` (zero-edit, no new index/family rows —
confirmed: every cross-file rule reuses an open family, substrate
file-local) all present and consistent with pass 1. Gates: rejections
correctly carry no gate (difference + trigger + home is the owed form);
reuse/file-local rows pin existing oracles with hand-copy negative
controls and route new gates to holding family items — the correct
file-item posture. Coupling: none everywhere, correct (nothing lands).
Link block: 25 uses / 25 defs bidirectional exact, all paths on disk,
10 group headers. Pass-1 sections byte-preserved; item-scoped diff still
0 bytes; target blob unchanged. AGENTS.md prose violation cured by the
completed link block; new citations keep `path::Symbol` form. No new
defects. Verdict: verified.

## Defects (Worker 2)

- D1 (Worker 2, blocking, owner: this item — Worker 1 resubmission): the
  artifact `docs/dry/dry-file-filters__sets.md` is truncated mid-sentence
  in `### Challenges` (ends line 320 with the literal text
  `...[truncated 9117 chars]`) and is missing the rest of Challenges, the
  entire `## Findings` section (R-m1–R-m4 + R-1 with contract difference,
  trigger, owner/lifetime, migration, fingerprints, behavioral proof,
  structural gate + negative control, coupling), `## Defects`,
  `## Pending execution`, `## Judgment`, and the link-definition block.
  A `ready-for-verification` verdict cannot be checked against an
  incomplete record. Resubmission must complete the artifact without
   rewriting the verified surviving sections; Worker 2 (same verifier)
   then completes the findings/gate/Pending/coupling checks.

## Findings

Reuse-consumer records against open index families (no consolidation
inside a file item, so Migration is `none` throughout and each record
routes to its holding family item). Then file-local L1–L18, then
rejections R-m1–R-m4 + R-1.

### `lookup-name-spelling-grammar` (reuse, reverse)

- **Contract + variation.** One Django-lookup ↔ python-attr spelling
  grammar; varies on the table rows only (new/renamed lookup).
- **Sites + roles.** Definition:
  [filters-inputs][filters-inputs]`::LOOKUP_NAME_MAP`. Consumers here:
  `_FORM_KEY_BY_PYTHON_ATTR` (reverse, built once from the table)
  + `FilterSet._form_key_for_python_attr` + the forward `.get` in
  `_build_input_fields`. Oracles: literal pin test + bag wire-name
  pins + live wire spellings. Projection: spec Decision pointer.
- **Challenges.** Rename a lookup → 1; first-wins to last-wins → 1
  (the `reversed` construction); drop verbatim fallthrough → 1 per
  side (two coordinated edits inside one grammar).
- **Owner + lifetime.**
  [filters-inputs][filters-inputs]`::LOOKUP_NAME_MAP` (principle 2:
  one grammar). Reverse derived once at import; no stored derivation
  with a lifetime beyond the import binding.
- **Migration.** None (already compose by name).
- **Distinct behavior.** Unknown-token verbatim fallthrough is shared
  grammar, not divergence (both halves fall through identically).
- **Behavioral proof.** P1 execution-verified (reverse equals the
  first-match scan over all 26 entries; round-trips; fallthroughs;
  remaps).
- **Structural gate.** P1 plus the pin oracles (fail on table change);
  no new gate owed — zero-edit file item, gate belongs to the family
  item. Negative control: a hand copy of the table passes the behavior
  oracles (the copy is correct), so no bespoke existence test is
  claimed here.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [filters-inputs][filters-inputs] `82b52d97`; HEAD `9031cb3d`;
  population: package-wide table sweep (one definition).

### `filter-logic-operators` (reuse, emission)

- **Contract + variation.** The filter logical-operator vocabulary
  (python attr, wire name, sequence cardinality, Q composition);
  varies on operator membership + per-operator axes.
- **Sites + roles.** Definition:
  [filters-inputs][filters-inputs]`::LOGIC_OPERATORS` (+ descriptor,
  `BY_*` maps derive). Consumers here: `_LOGIC_PYTHON_ATTRS`,
  `FilterSet._iter_logic_branches`, `_permission` `logic_keys`,
  `_normalize_input` wire copy, `_evaluate_logic_tree` compose.
  Oracles: operator pins + live `and:` rows.
- **Challenges.** Fourth operator → 1 (tuple + descriptor; maps
  derive); `not_` cardinality → 1 (`is_sequence` axis); Q
  composition → 1 (composer).
- **Owner + lifetime.**
  [filters-inputs][filters-inputs]`::LOGIC_OPERATORS` (principle 2).
  Emission iterates per call; nothing stored, no lifetime owed.
- **Migration.** None.
- **Distinct behavior.** `not_` single vs `and_`/`or_` list shape is
  one `is_sequence` axis, not a fork; emission never restates.
- **Behavioral proof.** P2 execution-verified (attrs, wire/pyattr
  cover, empty/inactive filtering, dual-spelling accept,
  `not_` single, permission `logic_keys` identity).
- **Structural gate.** P2 plus operator oracles; no new gate owed
  (family item owns it). Negative control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [filters-inputs][filters-inputs] `82b52d97`;
  [dry-file-filters-inputs][dry-file-filters-inputs] family home;
  HEAD `9031cb3d`.

### `set-type-naming` (reuse, config)

- **Contract + variation.** Class-derived set-family input naming;
  varies on the two suffixes only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin`. Consumer here:
  `FilterSet._field_type_suffix` declaration (filter-bag suffix).
  Oracles: live root/bag names.
- **Challenges.** Bag suffix → 1 (the row-5 declaration).
- **Owner + lifetime.**
  [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin` (principle 2).
  Pure derivation per call; no stored state.
- **Migration.** None.
- **Distinct behavior.** The filter suffix override stays family
  config; the order side keeps the default (cookbook divergence
  stated at the twin).
- **Behavioral proof.** P5 execution-verified (both family suffix
  wirings).
- **Structural gate.** Pin oracles; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.

### `related-set-target-lifecycle` (reuse, consumer-only)

- **Contract + variation.** Idempotent owner bind + lazy resolve +
  family gate; varies on the two attr-name params plus the family
  gate only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::RelatedSetTargetMixin`. Consumers here:
  metaclass `collect_related_declarations` call (bind step),
  `f.filterset` / `related_filter.filterset` /
  `child._owner_definition.origin` reads. Oracles: binding pins +
  live expansion rows.
- **Challenges.** Flip the inherit policy → 1 call-site argument;
  change bind-once semantics → 1 (`_bind_owner` at the owner).
- **Owner + lifetime.**
  [sets-mixins][sets-mixins]`::RelatedSetTargetMixin`; owner slot per
  declaration instance (lifetime: declaration instance).
- **Migration.** None.
- **Distinct behavior.** No declaration here (0 `_bind_owner` /
  `resolve_lazy_class` hits); resolution entered only through the
  `.filterset` property reads.
- **Behavioral proof.** Static-reviewed (single definitions composed
  by name; calls read at both seams).
- **Structural gate.** Family pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`;
  [filters-base][filters-base] `ba52351c`;
  [order-base][order-base] `4736fda0`; HEAD `9031cb3d`.

### `related-declaration-collection` (reuse, consumer-only)

- **Contract + variation.** Ordered collect with inherit-merge policy;
  varies on the merge policy plus the two family attr maps.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::collect_related_declarations`. Consumer
  here: the metaclass call (`inherit_from_bases=False` over
  `declared_filters` + `class_items` + `base_declarations_attr`;
  the twin passes `True` over class-body `attrs`).
- **Challenges.** Tombstone rule → 1 (owner); diamond rule → 1
  (owner); policy flip → 1 call-site argument (consumer config).
- **Owner + lifetime.**
  [sets-mixins][sets-mixins]`::collect_related_declarations`; runs once
  per class creation, stored on the new class.
- **Migration.** None.
- **Distinct behavior.** The two opposed policies stay per call site
  (django-filter merges MRO itself; plain `type` does not; stated at
  both call sites).
- **Behavioral proof.** Static-reviewed (both call sites read in full
  against the owner body).
- **Structural gate.** Family pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.

### `set-expansion-once-skeleton` (reuse, consumer-only)

- **Contract + variation.** Own-dict cache read + reentry fallback +
  guard lifetime; varies on guard lifetime only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::expanded_once`. Consumer here:
  `get_filters` `expanded_once` call (with `on_reentry`; the twin
  calls without).
- **Challenges.** Guard lifetime → 1 (owner); order `on_reentry` → 1
  call site.
- **Owner + lifetime.**
  [sets-mixins][sets-mixins]`::expanded_once`; guard lives one `_build`
  call, cache lives to `registry.clear()`.
- **Migration.** None.
- **Distinct behavior.** The `_build` publish spelling stays
  family-owned (snapshot + `base_filters` side effect), correctly
  unshared (R-m1).
- **Behavioral proof.** Static-reviewed (call shape read at both
  consumers).
- **Structural gate.** Family pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`; HEAD `9031cb3d`.

### `set-expansion-cache-write-gate` (reuse, consumer-only)

- **Contract + variation.** Two-condition cache-write predicate; varies
  on write conditions only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::should_cache_expansion`. Consumer here:
  the `_build` closure's `should_cache_expansion` call.
- **Challenges.** Third write condition → 1 (owner).
- **Owner + lifetime.**
  [sets-mixins][sets-mixins]`::should_cache_expansion`; pure predicate,
  no lifetime.
- **Migration.** None.
- **Distinct behavior.** Publish semantics (what is stored) stay in the
  family `_build`, not the predicate (R-m1).
- **Behavioral proof.** Static-reviewed.
- **Structural gate.** Family pin; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`; HEAD `9031cb3d`.

### `re-readable-field-declaration-gate` (reuse, consumer-only)

- **Contract + variation.** Structural re-walkability gate; varies on
  the family subject plus accepted spellings only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::require_re_readable_field_declaration`.
  Consumer here: the `get_fields`
  `require_re_readable_field_declaration` call with the filter
  string exemption (top-level `"__all__"` is a string; upstream
  rejects other strings).
- **Challenges.** Admit generators → 1 (predicate); drop the filter
  string exemption → 1 call-site policy.
- **Owner + lifetime.**
  [sets-mixins][sets-mixins] gate pair; stateless predicate.
- **Migration.** None.
- **Distinct behavior.** The string exemption is call-site policy
  (order side is strict); R-1 records the `"__all__"` separation it
  protects.
- **Behavioral proof.** Static-reviewed (call-site comment read
  against the gate body).
- **Structural gate.** Family pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`; HEAD `9031cb3d`.

### `active-input-permission-facade` (reuse)

- **Contract + variation.** One `_permission` record per family plus
  the mixin walkers; varies on label, target attr, traversal axes,
  and hook overrides.
- **Sites + roles.** Definitions:
  [sets-mixins][sets-mixins]`::ActiveInputPermissionMixin` (+ attrs)
  with mechanics in [utils-permissions][utils-permissions] and shape
  in [input-values][input-values]`::SetInputTraversal`. Consumers
  here: `_permission`, `_MAX_LOGIC_DEPTH`,
  `_permission_fallback_path`, `_check_permission_depth`,
  `_run_logic_permission_checks`, `check_permissions` (delegate).
  Oracles: denial rows + permission pins.
- **Challenges.** New shared walker → 1 (mixin); sixth traversal
  axis → 1 (traversal shape); filter remap → 1 (row-8 override);
  depth cap → 1 (row 7 + row 9); label wording → 1 (mechanics).
- **Owner + lifetime.** Facade at
  [sets-mixins][sets-mixins]`::ActiveInputPermissionMixin`; mechanics at
  [utils-permissions][utils-permissions]; shape at
  [input-values][input-values]`::SetInputTraversal`. Traversal read per
  call, never cached at import (override reachability).
- **Migration.** None.
- **Distinct behavior.** Filter logic recursion + depth cap + form-key
  remap vs order verbatim path + lazy warm-up stay per family
  (hooks, not forked facade).
- **Behavioral proof.** P5 execution-verified (traversal identity both
  families, remap split, lifecycle tuples, suffix wirings).
- **Structural gate.** P5 plus denial oracles; no new gate owed.
  Negative control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`;
  [utils-permissions][utils-permissions] `9889d6fe`;
  [input-values][input-values] `f2566609`; HEAD `9031cb3d`.

### `subsystem-clear-lifecycle` (reuse, population)

- **Contract + variation.** Descriptor-declared reset population with
  bus replay; varies on slot membership only.
- **Sites + roles.** Definition:
  [sets-mixins][sets-mixins]`::SetLifecycleAttrs` +
  `::binding_attrs`; bus at the registry; reset body at
  [utils-inputs][utils-inputs]`::clear_generated_input_namespace`.
  Population here: `_lifecycle`, `_owner_definition`,
  `_expanded_filters`, `_expanded_snapshot`, `_is_expanding_filters`.
  Oracles: clear/rebuild pins.
- **Challenges.** New cached slot → 1 reset definition
  (`binding_attrs` derivation) + declaration + publish adapters;
  rename → declaration only.
- **Owner + lifetime.** Descriptor at
  [sets-mixins][sets-mixins]`::SetLifecycleAttrs` (narrowest home both
  set bases import without cycles); body at
  [utils-inputs][utils-inputs]`::clear_generated_input_namespace`;
  bus at the registry. Lifetime: declared at class creation,
  derived per clear, binding state lives first-build to `clear()`.
- **Migration.** None.
- **Distinct behavior.** Filter-only snapshot `extra` is the stated
  metadata-must-reset-with-filters contract, not an omission.
- **Behavioral proof.** P5 execution-verified (both lifecycle tuples
  exact).
- **Structural gate.** Clear/rebuild pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [sets-mixins][sets-mixins] `ad8987ea`;
  [utils-inputs][utils-inputs] `ee31d360`; HEAD `9031cb3d`.

### `one-sync-boundary` (reuse, consumer-only)

- **Contract + variation.** One sync execution boundary for ORM work;
  varies on boundary membership only.
- **Sites + roles.** Definition at the querysets owner. Consumer here:
  the `apply_async` `run_in_one_sync_boundary` wrap (finalize +
  async pre-walk inside; `apply_sync` never enters).
- **Challenges.** Boundary semantics → 1 (owner); new entry shape →
  1 consumer call site.
- **Owner + lifetime.** Querysets owner; boundary lives one apply
  call.
- **Migration.** None.
- **Distinct behavior.** Sync/async twin coloring differs per family
  (order twins wrap permission only, no visibility derive, no
  pre-walk — R-m3).
- **Behavioral proof.** Static-reviewed (colorings inspected, not
  executed — no consolidation proposed, so no equivalence gate is
  owed).
- **Structural gate.** Boundary oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; querysets owner `1539b66c`;
  HEAD `9031cb3d`.

### `child-queryset-alias-inheritance` (reuse, consumer)

- **Contract + variation.** Child querysets inherit the parent alias;
  varies on alias threading only.
- **Sites + roles.** Definition at the querysets owner
  (`base_queryset`). Consumer here: `base_queryset(child_model,
  using=parent_db)` at the related-visibility seam.
- **Challenges.** Alias inheritance → 1 (owner).
- **Owner + lifetime.** Querysets owner; alias threads one derive
  call.
- **Migration.** None.
- **Distinct behavior.** None inside; the seam passes the alias
  through rather than deciding it.
- **Behavioral proof.** Static-reviewed (call site read against the
  owner signature).
- **Structural gate.** Alias oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; querysets owner `1539b66c`;
  HEAD `9031cb3d`.

### `queryset-seed-and-model-read` (reuse, partial)

- **Contract + variation.** Queryset seeding + model reads; varies per
  half.
- **Sites + roles.** Definition at the querysets owner. Consumer half
  here: `base_queryset` call present (2 hits). Absent half:
  `model_for` 0 hits — no registered-type seed at this seam.
- **Challenges.** Either half → 1 at the owner; 0 here.
- **Owner + lifetime.** Querysets owner; for the family item to
  adjudicate the partial membership.
- **Migration.** None.
- **Distinct behavior.** Partial by construction (seed without
  model-read at this seam).
- **Behavioral proof.** Static-reviewed (hit counts verified by
  search).
- **Structural gate.** Family oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; querysets owner `1539b66c`;
  HEAD `9031cb3d`.

### `globalid-relation-pk-marker` (reuse, consumer)

- **Contract + variation.** Boolean flag on forward FK/O2O bound on a
  non-pk `to_field` (never a frozen path); varies on covered
  relation shapes only.
- **Sites + roles.** Definitions:
  [filters-base][filters-base]`::_GLOBALID_RELATION_PK_ATTR` +
  `::_relation_uses_non_pk_to_field` +
  `::_marked_pk_field_name` (single stamp predicate, single
  read/derive home). Stamp consumer here: `filter_for_field` (one
  `setattr` + predicate read). Read consumers: the GlobalID filter
  branches. Oracles: marker stamping + rebase survival pins in
  [test-sets][test-sets].
- **Challenges.** New relation shape → 1 (stamp predicate);
  mid-flight rename → 0 (derived at read — rebase-immune).
- **Owner + lifetime.**
  [filters-base][filters-base] trio; derived at filter time, never
  stored as a path.
- **Migration.** None.
- **Distinct behavior.** None inside; the stamp is the single site.
- **Behavioral proof.** Static-reviewed (stamp/read sites read
  against the trio bodies).
- **Structural gate.** Marker oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [filters-base][filters-base] `ba52351c`; HEAD `9031cb3d`.

### `type-registry-model-type-map` (reuse, consumer)

- **Contract + variation.** Model-to-GraphQL-type map; varies on map
  membership only.
- **Sites + roles.** Definition at the registry owner. Consumers here:
  two `registry.get` reads + three `.origin` readers (never `.type` /
  `.type_cls`; stated at both read sites); `primary_for` explicitly
  refused by comment at the seam.
- **Challenges.** Map membership → 1 (owner).
- **Owner + lifetime.** Registry owner; reads per apply, never
  cached here.
- **Migration.** None.
- **Distinct behavior.** The `primary_for` refusal is recorded
  intention (no recomposition), not an omission.
- **Behavioral proof.** Static-reviewed (read sites + refusal comment
  read against the registry body).
- **Structural gate.** Registry oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; registry owner read at HEAD
  `9031cb3d`.

### `orm-lookup-path-resolution` (reuse, consumer)

- **Contract + variation.** ORM path classification + cardinality +
  to-many traversal; varies per predicate only.
- **Sites + roles.** Definitions at the relations owner
  (`classify_path`, `relation_kind`,
  `is_many_side_relation_kind`, `path_traverses_to_many`). Consumers
  here: the four reads at the visibility/constrain seams
  (`is_many_side_relation_kind(relation_kind(field))` cardinality
  call pinned as a spot-check).
- **Challenges.** Classification → 1; cardinality → 1 (one call);
  to-many traversal → 1.
- **Owner + lifetime.** Relations owner; pure predicates, no lifetime.
- **Migration.** None.
- **Distinct behavior.** None inside; all four compose by name.
- **Behavioral proof.** Static-reviewed (call shapes read against the
  owner bodies).
- **Structural gate.** Path oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; relations owner `7662b0bb`;
  HEAD `9031cb3d`.

### L1 `_lookups_for_field` memo (file-local)

- **Contract + variation.** Field-class → concrete lookups, transforms
  excluded, memoized by field class, copies on return; varies on
  exclusion membership + memo key + return aliasing.
- **Sites + roles.** Definition here (cache + function). Consumers:
  per-field `"__all__"` expansion (L12) + defaults install (L3).
  Oracle: [test-sets][test-sets] lookup pins.
- **Challenges.** Exclusion → 1; memo key → 1; aliasing → 1 (the copy;
  P6 rejects).
- **Owner + lifetime.** Here; memo lives per field class for the
  process (keys are Django field classes, stable across clear).
- **Migration.** None (file item).
- **Distinct behavior.** Copies (never the cached list) — the
  caller-append mutant test pins it.
- **Behavioral proof.** P6 execution-verified (`None`, no-transform,
  exact/gt presence, copy, class-keyed).
- **Structural gate.** P6 plus lookup pins; no new gate owed (no
  consolidation). Negative control: a hand copy of the body passes
  the behavior oracles, so no bespoke existence test is claimed.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide `def` sweep (one definition).

### L2 ModelChoice extras strip (file-local)

- **Contract + variation.** Strip ModelChoice-only extras before
  install; varies on extras keys + strip timing.
- **Sites + roles.** Definition here (table + helper). Consumer: the
  defaults install path (L3). Oracle: [test-sets][test-sets].
- **Challenges.** Key → 1 (table); timing → 1 (helper).
- **Owner + lifetime.** Here; pure transform, no lifetime.
- **Migration.** None.
- **Distinct behavior.** None inside.
- **Behavioral proof.** Static-reviewed (single definition composed by
  name).
- **Structural gate.** Existing oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L3 relation extras + defaults table (file-local)

- **Contract + variation.** Per-relation-shape extra callables +
  package defaults installed on the class; varies per shape + per
  default mapping.
- **Sites + roles.** Definition here (four extras + public table +
  class attr). Consumer: generation (L13). Oracle:
  [test-sets][test-sets].
- **Challenges.** Shape → 1 (its extra); mapping → 1 (the table).
- **Owner + lifetime.** Here; the class attr installs the authored
  table (never a snapshot of the mutable global — anchor is the
  private normalized baseline by value).
- **Migration.** None.
- **Distinct behavior.** Forward-M2M, forward-M2O, reverse-O2O,
  reverse-rel stay per shape.
- **Behavioral proof.** Static-reviewed.
- **Structural gate.** Existing oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition each).

### L4 policy table + baseline + origin oracle (file-local)

- **Contract + variation.** Normalized generation-policy entries +
  package baseline (by value) + per-field origin oracle; varies per
  axis + baseline + reselect rule.
- **Sites + roles.** Definition here (entry, normalizer, baseline,
  oracle). Consumers: generation (L13) + provenance stamp (L6).
  Oracle: [test-sets][test-sets].
- **Challenges.** Axis → 1; baseline → 1; reselect → 1 (deliberate
  upstream mirror — no upstream selection API exists).
- **Owner + lifetime.** Here; baseline is a value snapshot named at
  import (ownership anchor, not a cache).
- **Migration.** None.
- **Distinct behavior.** The mirror is the recorded deliberate
  exception to derive-once (reason at the seam).
- **Behavioral proof.** P8 execution-verified (pristine, override,
  unresolvable, `isnull`-Boolean incl. the TextField-MRO arm).
- **Structural gate.** P8 plus oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; installed
  upstream 26.1 read (mirror verified against the running bodies).

### L5 audit gate (file-local)

- **Contract + variation.** Audited-release range + predicate + env
  flag; varies on range membership + parse strictness.
- **Sites + roles.** Definition here (range, predicate, flag).
  Consumer: the optimizer-substrate paths that depend on audited
  upstream behavior. Oracle: [test-sets][test-sets].
- **Challenges.** Release → 1 (table); strictness → 1 (predicate).
- **Owner + lifetime.** Here; flag computed at import (fail-closed
  parse).
- **Migration.** None.
- **Distinct behavior.** Garbage/empty/dev-suffixed versions fail
  closed by contract.
- **Behavioral proof.** P4 execution-verified (audited/unaudited arms
  + env consistency).
- **Structural gate.** P4 plus oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L6 provenance (file-local)

- **Contract + variation.** Generation-provenance stamp/read/inherit
  with fail-closed `None`; varies on record shape + origins.
- **Sites + roles.** Definition here (attr, `FilterOrigin`,
  `FilterGenerationProvenance`, reader, stamper, origins set).
  Stamp sites: three generation sites + metaclass declared stamp;
  inherit site: related expansion breadcrumbs. Oracle:
  [test-sets][test-sets].
- **Challenges.** Record → 1; fail-closed default → 1 (reader);
  origin → 1 (set).
- **Owner + lifetime.** Here; record travels on the filter instance
  (lifetime: filter instance; inherit appends via `replace`, never
  mutates the child).
- **Migration.** None.
- **Distinct behavior.** `None` = unstamped = fail-closed; inherit
  never mints.
- **Behavioral proof.** P9 execution-verified (unstamped `None`,
  stamped round-trip, origins set).
- **Structural gate.** P9 plus oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition per mechanism).

### L7 family profiles + dynamic-CSV validator (file-local)

- **Contract + variation.** Exact-class family profiles (8 shipped
  singletons + registry) + structural two-base dynamic-CSV check;
  varies per family + per structural predicate.
- **Sites + roles.** Definition here (profile record, singletons,
  registry, empty-body reference + attrs, two profile fns). Consumer:
  generation (L13). Oracle: [test-sets][test-sets].
- **Challenges.** Family → 1 (singleton + row); predicate → 1.
- **Owner + lifetime.** Here; stateless classifiers (exact identity
  for shipped, structural shape for dynamic).
- **Migration.** None.
- **Distinct behavior.** Subclasses, swapped/three bases, unaudited
  scalars, body-added members all refuse (pinned); the closed set
  is exact.
- **Behavioral proof.** P3 execution-verified (all arms + closed set).
- **Structural gate.** P3 plus oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L8 candidate metadata + snapshot (file-local)

- **Contract + variation.** Per-candidate metadata frozen at build +
  atomic expansion snapshot under the write gate; varies per field
  + per snapshot scope.
- **Sites + roles.** Definition here (two records + two fns).
  Publisher: `_build` (L11); resetter: `binding_attrs` walk (reuse).
  Oracle: [test-sets][test-sets] (snapshot reset/rebuild pins).
- **Challenges.** Field → 1 (record); scope → 1 (snapshot).
- **Owner + lifetime.** Here; snapshot lives first-build to `clear()`
  (published atomically, reset by the generic walk).
- **Migration.** None.
- **Distinct behavior.** The order side has no snapshot by contract
  (R-m1) — not an omission.
- **Behavioral proof.** Static-reviewed + oracle pins (reset/rebuild
  rows).
- **Structural gate.** Snapshot pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition; optimizer has no second
  definition — fetch-side elision there is a different contract).

### L9 metaclass (file-local)

- **Contract + variation.** Class construction: collect + tombstone
  rebuild + declared-provenance stamp + alias write-back; varies per
  rule above.
- **Sites + roles.** Definition here (metaclass + `__new__`).
  Consumers: every `FilterSet` subclass. Oracles: construction pins
  in [test-sets][test-sets] + cookbook-port note.
- **Challenges.** Collect policy → 1 call-site argument (consumer of
  the shared collector); rebuild → 1; stamp → 1 (own-ness from the
  class body — borrowed-instance restamp closes the hole).
- **Owner + lifetime.** Here; runs once per class creation.
- **Migration.** None.
- **Distinct behavior.** Cookbook deltas (tombstone rebuild, declared
  stamp) documented inline, not silent; alias write-back pinned as a
  spot-check.
- **Behavioral proof.** Static-reviewed + construction oracles.
- **Structural gate.** Construction pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L10 related expansion (file-local)

- **Contract + variation.** Expand related graphs with breadcrumb
  inheritance; varies on breadcrumb shape only.
- **Sites + roles.** Definition here. Consumers: `get_filters` drive
  (L11) + visibility derive (L15). Oracle: [test-sets][test-sets].
- **Challenges.** Breadcrumb → 1; mint-vs-inherit → 1 (inherit).
- **Owner + lifetime.** Here; breadcrumbs travel on the inherited
  record (never mutates the child).
- **Migration.** None.
- **Distinct behavior.** Copies inherit, never mint.
- **Behavioral proof.** Static-reviewed.
- **Structural gate.** Expansion oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L11 `get_filters` publish (file-local)

- **Contract + variation.** Expansion drive + atomic publish (snapshot
  + `base_filters` under the write gate); varies on publish
  population only.
- **Sites + roles.** Definition here. Consumers: the finalizer bind
  subpasses (expansion drive) + Layer-5 factory (reads resolved
  instances). Oracle: [test-sets][test-sets] + live suites.
- **Challenges.** Population → 1 (`_build`); guards → 1 each at
  their owners (consumer call sites).
- **Owner + lifetime.** Here; cache lives to `clear()`.
- **Migration.** None.
- **Distinct behavior.** Snapshot + `base_filters` side effect are the
  filter-only publish spelling (R-m1).
- **Behavioral proof.** Static-reviewed + expansion/publish oracles.
- **Structural gate.** Publish pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [finalizer][finalizer] `77fd9a2d`; HEAD `9031cb3d`.

### L12 `get_fields` narrow (file-local)

- **Contract + variation.** Narrow `super().get_fields()` with two
  `"__all__"` branches (dict-form per-field expansion vs top-level
  string sweep); varies per branch.
- **Sites + roles.** Definition here. Consumers: Layer-6 dynamic
  getter (class base) + both `inputs` namespace clears. Oracle:
  [test-sets][test-sets].
- **Challenges.** Per-field branch → 1; sweep branch → 1 (one owner,
  distinct contracts — R-1).
- **Owner + lifetime.** Here; runs per class build (no stored
  derivation beyond the published maps).
- **Migration.** None.
- **Distinct behavior.** The two branches share a token, not a
  contract (R-1, home: the docstring).
- **Behavioral proof.** Static-reviewed + fields oracles.
- **Structural gate.** Fields pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L13 generation conditional (file-local)

- **Contract + variation.** Generation capability + per-seam class
  choice + relay/pk seams; varies per seam + capability + target
  rule.
- **Sites + roles.** Definition here (six members). Consumers:
  `get_filters`/`get_fields` build paths. Oracles:
  [test-sets][test-sets] generation pins.
- **Challenges.** Seam → 1; capability → 1 (identity: P7);
  relay-target → 1 (P8 arms).
- **Owner + lifetime.** Here; decisions per build (no stored
  derivation).
- **Migration.** None.
- **Distinct behavior.** Generation-site census holds: every
  instance-returning path stamps; `None` returns no row
  (fail-closed, upstream-identical); declared leaves stamped by
  own-ness.
- **Behavioral proof.** P7 + P8 execution-verified.
- **Structural gate.** P7/P8 plus generation pins; no new gate owed.
  Negative control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [filters-base][filters-base] `ba52351c`;
  [relays][relays] `52439862`; HEAD `9031cb3d`.

### L14 normalization (file-local)

- **Contract + variation.** Input normalization over three
  `ActiveField` kinds + operator-bag + range patch; varies per kind
  + shape rule + patch membership.
- **Sites + roles.** Definition here (six members). Consumers: both
  applies (L18) + permission walk (reuse). Oracles:
  [test-sets][test-sets] normalize pins.
- **Challenges.** Kind → 1 (dispatcher: LOGIC copied, RELATED
  stripped, LEAF normalized); shape → 1; patch → 1.
- **Owner + lifetime.** Here; normalize into `data` per apply (wire
  keys copied, tree keys absent from `cleaned_data` by form design).
- **Migration.** None.
- **Distinct behavior.** Dual spellings read through the one
  `_iter_logic_branches` everywhere they are applied.
- **Behavioral proof.** Static-reviewed + normalize oracles (P2 pins
  the shared iterator).
- **Structural gate.** Normalize pins; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L15 visibility derive (file-local)

- **Contract + variation.** Related-visibility queryset derivation
  (sync + async twins + nested pre-walk); varies per step + per
  coloring.
- **Sites + roles.** Definition here (five members). Consumers: both
  applies (L18). Oracles: visibility pins + live suites.
- **Challenges.** Step → 1 (iterator); await seam → 1 per twin
  (one body impossible — R-m3).
- **Owner + lifetime.** Here; derived per apply (querysets close
  over the call).
- **Migration.** None.
- **Distinct behavior.** Async awaits consumer hooks mid-traversal;
  sync raises `SyncMisuseError` there; async alone pre-walks logic
  arms. Contrast recorded at both owners.
- **Behavioral proof.** Static-reviewed (colorings inspected, not
  executed — no consolidation proposed, no equivalence gate owed).
- **Structural gate.** Visibility oracles; no new gate owed.
  Negative control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [utils-querysets][utils-querysets] `1539b66c`;
  [predicates][predicates] `4e87c733` (consumed by name, never
  restated); HEAD `9031cb3d`.

### L16 depth/info channels (file-local)

- **Contract + variation.** Logic-depth cap + apply-info + per-branch
  nested-queryset channels; varies on cap + channels.
- **Sites + roles.** Definition here (four members). Consumers: logic
  evaluation (L17) + permission walk (reuse). Oracle:
  [test-sets][test-sets].
- **Challenges.** Cap → 1 (value + raiser); channel → 1.
- **Owner + lifetime.** Here; channels live one apply call.
- **Migration.** None.
- **Distinct behavior.** Caps fire on all four entry shapes (both
  applies, permission walk, logic evaluation + async pre-walk).
- **Behavioral proof.** Static-reviewed + depth oracles.
- **Structural gate.** Depth pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`; population:
  package-wide sweep (one definition).

### L17 flat-leaf + logic tree (file-local)

- **Contract + variation.** Flat-leaf adapter + logic-tree composer +
  related constraints + `filter_queryset`; varies per composer +
  adapter + constrain rule.
- **Sites + roles.** Definition here (six members). Consumer: the
  apply pipeline (L18). Oracles: [test-sets][test-sets] + live
  suites (`test_library_api`, `test_scalars_filter_api`,
  `test_optimizer_auto_api`, `test_products_visibility_api`,
  `test_multi_db` — wire shapes).
- **Challenges.** Composition → 1; adapter → 1; constrain → 1.
- **Owner + lifetime.** Here; Q objects composed per apply
  (unevaluated until the boundary).
- **Migration.** None.
- **Distinct behavior.** Compose reads `data` (tree keys absent from
  `cleaned_data` by django-filter form design); `distinct` stamping
  is framework-origin only by the row-preserving rationale.
- **Behavioral proof.** Static-reviewed + tree/leaf oracles.
- **Structural gate.** Tree pins; no new gate owed. Negative control
  as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [errs][errs] `3e25e93b`; HEAD `9031cb3d`.

### L18 apply pipeline (file-local)

- **Contract + variation.** Common prelude/finalize + sync/async
  entry points + dispatcher + form validation; varies per stage +
  dispatch + failure semantics.
- **Sites + roles.** Definition here (six members). Consumers: live
  queries over `/graphql` + admin/services paths. Oracles:
  [test-sets][test-sets] + live suites.
- **Challenges.** Stage → 1 (prelude/finalize); dispatch → 1
  (filter-only); failure → 1 (validate-or-raise).
- **Owner + lifetime.** Here; prelude/finalize bracket one apply
  call (async wraps finalize in the one boundary).
- **Migration.** None.
- **Distinct behavior.** Dispatcher + `check_permissions` delegate are
  filter-only (stated on the twin); unknown top-level keys degrade
  to upstream form semantics (held, no stricter contract source).
- **Behavioral proof.** Static-reviewed + apply oracles (colorings
  inspected, not executed — no consolidation proposed).
- **Structural gate.** Apply oracles; no new gate owed. Negative
  control as above.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [utils-querysets][utils-querysets] `1539b66c`; HEAD `9031cb3d`.

### R-m1 filter-vs-order expansion build (rejection)

- **Contract + variation.** Considered shared form: one expansion
  `_build`. Difference: filter expands related graphs + freezes
  candidate metadata + publishes snapshot + writes `base_filters`;
  order merges meta fields + related orders, no snapshot, no
  `base_filters`, no reentry. Two contracts agreeing on nothing but
  the guard vocabulary.
- **Sites + roles.** Filter `_build` in `get_filters` (L11) vs order
  `_build` in [orders-sets][orders-sets]`::OrderSet.get_fields`;
  guards shared (reuse). No consolidation.
- **Challenges.** Either publish contract → 0 shared definitions.
- **Owner + lifetime.** Each `_build` owns its publish (snapshot
  lifetime as in L8).
- **Migration.** None (intentional separation stays).
- **Distinct behavior.** Recorded at the `_build` closures; the
  skeleton/gate sharing is the only common mechanism.
- **Behavioral proof.** Static-reviewed (both builds read whole).
- **Structural gate.** None owed (rejection, not a consolidation).
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.
- **Trigger.** A change to one side's publish contract that must move
  the other. **Home:** the `_build` closures' docstrings.

### R-m2 filter-vs-order normalizers (rejection)

- **Contract + variation.** Considered shared form: one normalize
  pass. Difference: filter operator-bag + logic-wire-copy +
  related-strip + range patch vs order flat purity-attested terms.
- **Sites + roles.** `FilterSet._normalize_input` (L14) vs the order
  term validator in [orders-sets][orders-sets]; logic vocabulary
  shared (reuse). No consolidation.
- **Challenges.** Either normalize contract → 0 shared definitions.
- **Owner + lifetime.** Each normalizer owns its pass (per-apply
  lifetime).
- **Migration.** None.
- **Distinct behavior.** Recorded at the two normalizers.
- **Behavioral proof.** Static-reviewed (both passes read whole).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.
- **Trigger.** A change to one side's normalize contract that must
  move the other. **Home:** the normalizer docstrings.

### R-m3 filter-vs-order apply pairs + twin coloring (rejection)

- **Contract + variation.** Considered shared form: one apply body.
  Difference: filter visibility-derive + related-constrain +
  form-validate + `.qs` + logic tree vs order permission-check +
  annotate/order_by; async pre-walk + boundary wrap filter-only;
  one body per twin pair impossible (await vs `SyncMisuseError`).
- **Sites + roles.** `FilterSet.apply_*` (L18 + L15/L17) vs
  `OrderSet.apply_*` in [orders-sets][orders-sets]; boundary shared
  (reuse). No consolidation.
- **Challenges.** Either apply contract → 0 shared definitions.
- **Owner + lifetime.** Each family owns its pipeline (per-apply
  lifetime); contrast recorded at both owners.
- **Migration.** None.
- **Distinct behavior.** Recorded at both owners' apply docstrings
  (threading of `run_permissions=False` / `parent_db` / `_depth`).
- **Behavioral proof.** Static-reviewed (colorings inspected).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.
- **Trigger.** A twin pair whose await points collapse to one
  coloring. **Home:** the apply docstrings.

### R-m4 filter-vs-order metaclasses (rejection)

- **Contract + variation.** Considered shared form: one set
  metaclass. Difference: django-filter subclass vs plain `type`;
  opposed inherit policies (`False` vs `True`); filter-only tombstone
  rebuild + declared-provenance stamp; filter-only `apply`
  dispatcher + `check_permissions` delegate; order-only
  `_prepare_permission_input` lazy-spec warm-up (filter specs are
  module-materialized).
- **Sites + roles.** `FilterSetMetaclass` (L9) vs
  [orders-sets][orders-sets]`::OrderSetMetaclass`; collector shared
  (reuse). No consolidation.
- **Challenges.** Either construction contract → 0 shared
  definitions.
- **Owner + lifetime.** Each metaclass owns its construction (per
  class-creation lifetime).
- **Migration.** None.
- **Distinct behavior.** Recorded at both metaclasses + the delegate/
  warm-up seams.
- **Behavioral proof.** Static-reviewed (both metaclasses read whole).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`;
  [orders-sets][orders-sets] `6044ab1a`; HEAD `9031cb3d`.
- **Trigger.** A change to one side's construction contract that must
  move the other. **Home:** the metaclass docstrings.

### R-1 per-field `"__all__"` vs model-level `"__all__"` (rejection)

- **Contract + variation.** Considered shared form: one `"__all__"`
  handler. Difference: dict-form values expand per field through
  `_lookups_for_field` (transforms excluded) vs the top-level string
  sweeps `model._meta` (PK added, M2M removed). A token shared, a
  contract not.
- **Sites + roles.** Both branches in `FilterSet.get_fields` (L12);
  upstream `get_fields` narrowed, never re-derived. Re-derived fresh
  at the owner per the worked example in [glossary][glossary]
  projection terms.
- **Challenges.** Either branch → the other does not move (0 shared).
- **Owner + lifetime.** `FilterSet.get_fields` here; per class build.
- **Migration.** None.
- **Distinct behavior.** Recorded at the owner so no cycle
  re-litigates (principle 10 durable home).
- **Behavioral proof.** Static-reviewed (both branches read against
  upstream + the gate).
- **Structural gate.** None owed.
- **Coupling.** None.
- **Freshness.** Target `4ab65a26`; HEAD `9031cb3d`.
- **Trigger.** A change to one branch that must move the other.
  **Home:** `FilterSet.get_fields` docstring.

## Defects

None. No wire- or configuration-reachable contract broken, no guard
a contract source demands, no docstring contradicting its body found
while tracing. Six load-bearing docstring claims re-derived true
(spot-checks held, below the bar, not defects): no `__init__` on
`FilterSet` (AST: 40 methods, none `__init__`);
`super().filter_for_field` calls `cls.filter_for_lookup` (installed
26.1 source verified); the empty-body dynamic-CSV premise (installed
26.1 `ConcreteInFilter` shape verified); the
`is_many_side_relation_kind(relation_kind(field))` cardinality call;
the metaclass alias write-back; the cookbook deltas (tombstone
rebuild, declared stamp) documented inline, not silent. Owner for any
future defect at this target: the `FilterSet` owner in
`filters/sets.py`. Never fixed inside this item (nothing to fix).

## Pending execution

None. All behavioral proofs are execution-verified read-only in the
shared tree: P1–P9
(`docs/dry/temp-tests/dry-file-filters__sets/probe_sets.py`, 93
asserts; throwaway subclasses only, shipped classes read never built,
no DB, no source mutation; target blob `4ab65a26` before and after —
re-run green on resubmission, see return). Everything else is
static-reviewed (single definitions composed by name; twin colorings
inspected, not executed — no consolidation proposed, so no
equivalence gate is owed). `FAKESHOP_SHARDED=1` and Postgres cells are
inapplicable by construction: no probe reaches a database, alias, or
dialect decision (probes touch `_meta` only, never evaluate a
queryset; the `parent_db` passthrough is read, never executed).

## Judgment

Zero-edit file item: matrix discharged against the real surface
(orders twin FIRST by behavior + contract; upstream bodies read, not
prose), 96/96 members assigned (16 reuse-consumer rows against open
families — eleven confirmed consumers, one partial
`queryset-seed-and-model-read`, four correctly withheld plus the
transitive-only entry — 18 file-local rows L1–L18 with the optimizer
substrate single-sited, 5 rejections with contract difference +
trigger + home), challenges recorded with definition counts, probes
green, no defect, no pending execution. Worker-0 index/family rows
owed: NONE new — every cross-file rule reuses an open family; the
optimizer substrate (provenance, profiles, candidates, snapshot,
audit gate, ownership oracle) is file-local by the single-definition
sweep, not a family. No production edit, no test change, no defect
fixed.

## Run 0.0.15 2026-09-30-8 re-trace (Worker-1)

Scoped re-trace of queue item s9 at HEAD bytes. The run-7 artifact above is
prior evidence only: every finding below was re-derived against current HEAD
bytes with fresh `git grep HEAD` / `git show HEAD:` populations and an AST
enumeration. No production edits (file item, reviewer role). The sibling
s7 run-8 section in [dry-file-filters-base][dry-file-filters-base] was read
as connected evidence; every stamp-side claim it makes about this file is
re-counted here from this side.

ITEM_BASELINE `bbdaa9b02c785498fe78c5d4a1f04644b8c16477` (WIP commit on
detached HEAD `83998e08`, intended). Item-scoped diff vs baseline for
`django_strawberry_framework/filters/sets.py`: empty. No owned ledger hunk
names this file; all dirt is concurrent (attributed by diff content below).

### Freshness fingerprints

- HEAD blob `3d307402a8c29860957a23bd99a821e094c606a6` (3660 lines) —
  traced bytes. Every body cited below is HEAD bytes.
- Worktree hash `ec278851996aff2835677b4ca77197da2a1c2728` (3750 lines,
  83 top-level statements, 41 `FilterSet` methods).
- `9aaaad5d` bytes blob `e47c6758e540e0bd9caa8cb90103263b26e905e1`
  (3623 lines, "dry-0015 pre-ff snapshot", not an ancestor of HEAD).
- Drift base `0c0537e2` blob `993e887a700112ea431f89b9ec49ab6f3ff25f55`
  (3529 lines). The prior stamp `4ab65a26` differs from it by exactly 3
  comment-only lines (verified by blob diff), so the run-7 trace reads as
  drift-base bytes.

Connected sources (HEAD blobs, all traced via `git show HEAD:` because the
worktree copies are concurrently dirty):
[filters-base][filters-base] `e2e683a8`,
[filters-inputs][filters-inputs] `2c853e24`,
[filters-init][filters-init] `8ce8b96d`,
[sets-mixins][sets-mixins] `6764d455`,
[utils-querysets][utils-querysets] `392e50d0`,
[utils-relations][utils-relations] `72e7ff08`,
[input-values][input-values] `3c17224f`,
[utils-inputs][utils-inputs] `7b88d358`,
[utils-permissions][utils-permissions] `e2b46fd7`,
[errs][errs] `793855e0`, [relays][relays] `968fb95a`,
[finalizer][finalizer] `cb2dde6b`, `registry.py` `9d2021eb`,
[orders-sets][orders-sets] `c4564c08`, [order-base][order-base] `d4cc9129`,
[predicates][predicates] `091619a2`; oracles [test-sets][test-sets]
`19d508bd`, [test-filter-base][test-filter-base] `2c507b75`,
[test-filter-inputs][test-filter-inputs] `769e7b45`,
[test-factories][test-factories] `49491bb9`; upstream `django-filter`
26.1 (the same running version run 7 verified against).

### Dirt attribution by diff content

HEAD-vs-worktree (153+/63-, all concurrent, none traced): a
`utils/truth.py` migration (`isinstance` / `__dict__` / `__bases__` /
`vars` / `__name__` / `__qualname__` / `type(x).__name__` reads through
`truth.*`, new `truth` import, `_safe_arg_repr` import dropped) plus two
new module helpers (`_inherits_unchanged`, `_registered_profile`), one new
`FilterSet` method (`_reject_shared_bag_form_keys` with its
`resolved_lookups` pre-pass), and a declared-form-key binding fix in
`_normalize_input`. No owned ledger row covers any of it.

`9aaaad5d` vs drift base on this target is 153+/59- with 0 `RelationPk`
mentions and 42 `truth.` refs — the same count as the worktree's 42: the
pre-merge snapshot is drift-base bytes plus the same concurrent truth dirt
(plus the same 2 module helpers + 1 method; member census verified), and
the worktree is HEAD bytes plus that dirt. Neither was traced; both are
read-only attribution evidence.

Drift-base-vs-HEAD (359+/228-, 86 hunks, the re-trace subject): one
behavior commit plus typing-only drift. Verified hunk by hunk (every
typing commit's full `+/-` lines read; the brief's claim CONFIRMED):

- `bbe54687` (129+/100-, 15 hunks, all read): `filter_for_lookup`
  rewritten (GlobalID vs raw-pk selection), `filter_for_field` relation
  branch rewritten (isinstance gate + `type(default)` rebuild), the stamp
  predicate call + `setattr` widened to both primitives, new
  `_RELATION_IDENTITY_FILTER_CLASSES` tuple, 2 new family profiles +
  registry rows, `_resolve_relation_target_type` guard drop, docstrings.
- `999a1aab` (10+/6-): `cast()` only. `b20277fe` (131+/106-): every
  changed line an annotation, import, `TypeVar`, or `cast()`.
  `849f67bc` (4+/0-): `@override` only. `dfbea72b` (91+/24-): the
  `TYPE_CHECKING` metaclass base (runtime else-branch assigns the same
  class), casts, ignores, comments, `@override`. `e37448e5` (1+/1-):
  pragma comment. `fef11e64` (9+/7-): imports, annotation widening, cast
  removal, comments.

### Enumeration (fresh, HEAD bytes)

Instrument: same as run 7 — `ast` parse of HEAD bytes. Module body: 80
statements = 1 docstring + 29 imports (27 `ImportFrom` + 2 `Import`) + 12
`AnnAssign` + 14 `Assign` + 14 `FunctionDef` + 8 `ClassDef` + 2 `If`
(drift: 74; delta +6 = 1 `override` import + 4 assigns + 1
`TYPE_CHECKING` block, itemized below). Excluded scaffolding with reason:
the module docstring (projection), 29 imports (references, not
definitions), both `TYPE_CHECKING` blocks (type-only), `_M` (a `TypeVar`
binding, no rule). **Count: 46 rule-bearing module-level statements + the
nested `FilterSetMetaclass.__new__` + 52 `FilterSet` members (12 class
attrs + 40 methods, 3 of them `async`) = 99 leaves** (drift: 96; delta
+3 = `_RELATION_IDENTITY_FILTER_CLASSES` + 2 profiles; `FilterSet`
member names verified identical to drift, NEW/GONE both empty; no
`__init__`; no `__all__` manifest — all 21 `__all__` hits are the
`Meta.fields` string literal / prose, same count as run 7).

| # | Member(s) | Home (run 8) |
|---|---|---|
| 1 | `_LOGIC_PYTHON_ATTRS` | `filter-logic-operators` (reuse, emission) |
| 2 | `_FORM_KEY_BY_PYTHON_ATTR` | `lookup-name-spelling-grammar` (reuse, reverse) |
| 3 | `FilterSet._form_key_for_python_attr` | `lookup-name-spelling-grammar` (reuse, reverse) |
| 4 | `FilterSet._iter_logic_branches` | `filter-logic-operators` (reuse, emission) |
| 5 | `FilterSet._field_type_suffix` | `set-type-naming` (reuse, config) |
| 6 | `FilterSet._permission` | `active-input-permission-facade` (reuse, config) |
| 7 | `FilterSet._MAX_LOGIC_DEPTH` | `active-input-permission-facade` (reuse, cap) |
| 8 | `FilterSet._permission_fallback_path` | `active-input-permission-facade` (reuse, hook) |
| 9 | `FilterSet._check_permission_depth` | `active-input-permission-facade` (reuse, hook) |
| 10 | `FilterSet._run_logic_permission_checks` | `active-input-permission-facade` (reuse, hook) |
| 11 | `FilterSet.check_permissions` | `active-input-permission-facade` (reuse, delegate) |
| 12 | `FilterSet._lifecycle` | `subsystem-clear-lifecycle` (reuse, population) |
| 13 | `FilterSet._owner_definition` | `subsystem-clear-lifecycle` (reuse, population) |
| 14 | `FilterSet._expanded_filters` | `subsystem-clear-lifecycle` (reuse, population) |
| 15 | `FilterSet._expanded_snapshot` | `subsystem-clear-lifecycle` (reuse, population) |
| 16 | `FilterSet._is_expanding_filters` | `subsystem-clear-lifecycle` (reuse, population) |
| 17 | `_lookups_for_field_class_cache`, `_lookups_for_field` | L1 |
| 18 | `_MODEL_CHOICE_ONLY_EXTRAS`, `_strip_model_choice_extras` | L2 |
| 19 | `_forward_relation_extra`, `_forward_m2m_extra`, `_reverse_o2o_extra`, `_reverse_rel_extra`, `_PUBLIC_PACKAGE_FILTER_DEFAULTS`, `FilterSet.FILTER_DEFAULTS` | L3 |
| 20 | `_NormalizedPolicyEntry`, `_normalize_policy_entry`, `_PACKAGE_POLICY_BASELINE`, `FilterSet._generation_origin_for_field` | L4 |
| 21 | `_AUDITED_DJANGO_FILTER_RANGE`, `_release_is_audited`, `_DJANGO_FILTER_OPTIMIZER_AUDITED` | L5 |
| 22 | `_GENERATION_PROVENANCE_ATTR`, `FilterOrigin`, `FilterGenerationProvenance`, `filter_generation_provenance`, `_stamp_generation_provenance`, `_FRAMEWORK_GENERATED_ORIGINS` | L6 |
| 23 | `_FilterFamilyProfile`, 10 singletons (was 8), `_ALL_FAMILY_PROFILES`, `_FILTER_FAMILY_REGISTRY`, `_EmptyBodyDynamicCsvReference`, `_EMPTY_BODY_DYNAMIC_CSV_ATTRS`, `_dynamic_csv_profile_for`, `_family_profile_for` | L7 |
| 24 | `CandidateFilterMetadata`, `ExpansionSnapshot`, `_candidate_metadata_for`, `FilterSet._expansion_snapshot` | L8 |
| 25 | `FilterSetMetaclass`, `FilterSetMetaclass.__new__` | L9 |
| 26 | `_expand_related_filter` | L10 |
| 27 | `FilterSet.get_filters` | L11 |
| 28 | `FilterSet.get_fields` | L12 |
| 29 | `_RELATION_IDENTITY_FILTER_CLASSES` (NEW), `FilterSet.filter_for_field`, `FilterSet.filter_for_lookup`, `FilterSet._is_generation_capable`, `FilterSet._is_own_pk_under_relay_owner`, `FilterSet._relay_filter_class_for_field`, `FilterSet._resolve_relation_target_type` | L13 |
| 30 | `FilterSet._iter_input_items`, `FilterSet._validate_logic_branch_shape`, `FilterSet._validate_logic_element_shape`, `FilterSet._normalize_input`, `FilterSet._require_range_patch_filter`, `FilterSet._operator_bag_items` | L14 |
| 31 | `FilterSet._iter_visibility_steps`, `FilterSet._derive_related_visibility_querysets_sync`, `FilterSet._derive_related_visibility_querysets_async`, `FilterSet._collect_nested_visibility_querysets_async`, `FilterSet._target_type_for_related_filter` | L15 |
| 32 | `FilterSet._logic_depth`, `FilterSet._apply_info`, `FilterSet._nested_qs_by_branch_id`, `FilterSet._raise_logic_depth_exceeded` | L16 |
| 33 | `FilterSet._invoke_suppressing_framework_distinct`, `FilterSet._apply_flat_leaves`, `FilterSet.filter_queryset`, `FilterSet._evaluate_logic_tree`, `FilterSet._q_for_branch`, `FilterSet._apply_related_constraints` | L17 |
| 34 | `FilterSet._apply_common_prelude`, `FilterSet._apply_common_finalize`, `FilterSet.apply_sync`, `FilterSet.apply_async`, `FilterSet.apply`, `FilterSet._validate_form_or_raise` | L18 |
| 35 | metaclass `collect_related_declarations` call; `f.filterset` / `related_filter.filterset` x2 / `child._owner_definition.origin` reads; `get_filters` `expanded_once` call; `should_cache_expansion` call; `get_fields` `require_re_readable_field_declaration` call; `apply_async` `run_in_one_sync_boundary` wrap; `base_queryset(child_model, using=parent_db)`; `setattr(..., _GLOBALID_RELATION_PK_ATTR, True)` + `_relation_uses_non_pk_to_field` read; `registry.get` x2 + `.origin` x3 reads; `classify_path` / `relation_kind` x2 / `is_many_side_relation_kind` x2 / `path_traverses_to_many` reads | consumer facets inside L9/L11/L12/L13/L15/L18 (roles recorded in Findings; homes stay put) |
| 36 | `_M`, second `TYPE_CHECKING` block, `override` import | scaffolding/machinery, no rule |

Arithmetic: 16 reuse leaves (2 module + 14 `FilterSet`) + 83 file-local
(44 module + 1 nested `__new__` + 38 `FilterSet`) = 99; row 35 names call
sites, not new homes. The new tuple joins L13 (it is the L13 gate's class
set, consumed only by the L13 `filter_for_field` branch — not an
upstream-mirroring generation input, so not L3); the new profiles join
L7. `_relation_identity_column` / `model_choice_identity_column` /
`_model_field_for_filter`: 0 hits each in the target — the s7 F-9/F-10
machinery is base/inputs-side; this file is uninvolved.

Static zero-probe at HEAD bytes (definitions in target):
`GeneratedInputArgumentsFactory`, `make_dynamic_set_getter`,
`resolve_lazy_class`, `_bind_owner`, seal symbols, globalid-decode
symbols: 0 each. `model_for`: 0 (`base_queryset` import + 1 call — the
partial stands). `_marked_pk_field_name`: 0 (this file stamps, never
reads). `async def`: 3, same names as drift. No second owner for any
indexed family machinery.

### Matrix (current target)

1. **Cross-flavor mirroring** — searched. [orders-sets][orders-sets]
   re-read at HEAD: member-identical to drift (15 `OrderSet` members,
   NEW/GONE empty; drift is `TypeVar` + annotations + `@override`), and
   every R-m anchor re-verified (`inherit_from_bases=True`,
   no `on_reentry`, no `_field_type_suffix` override, `apply_sync` /
   `apply_async` only, no `check_permissions`, order-only
   `_prepare_permission_input`, 0 `base_filters` / `_expanded_snapshot`
   hits). The rewritten relation ladder is filter-side only, which
   widens R-m3's apply-pair difference (trigger unchanged). Forms /
   mutations / rest import nothing from this target (0 hits; only
   own-family `.sets` imports plus one prose mention). The Layer-5
   factory still reads resolved instances (its drift hunks are
   annotation-only; the `LOOKUP_NAME_MAP.get` verbatim fallthrough is
   intact). The finalizer encode-only audit correctly excludes raw-pk by
   contract (it audits GlobalID decode-path mismatch, a dimension raw
   pks lack — read at HEAD, no omission). [filters-init][filters-init]
   exports unchanged (0 `RelationPk` hits — the generated-only
   precedent holds).
2. **Sync/async twins** — searched. Same 3 `async def` with the same
   colorings: the async derive awaits consumer `async get_queryset`
   hooks while the sync twin raises `SyncMisuseError` there;
   `apply_async` alone pre-walks logic arms and wraps finalize in the
   one boundary. All twin hunks drift-to-HEAD are annotation-only; the
   contrast is still recorded at both owners' docstrings. One body is
   still impossible. Order twins unchanged (R-m3 stands).
3. **Derived knowledge** — searched. The reverse map construction is
   byte-identical with 26 table entries at both revisions (first-wins
   intact); `binding_attrs` derivation, the 3 `.origin` readers, and the
   normalized-by-value baseline install are unchanged. The one new
   declaration, `_RELATION_IDENTITY_FILTER_CLASSES`, is a literal tuple
   over 4 imported primitives with exactly 1 consumer (the L13
   isinstance gate) — a declaration, not a second derivation. The
   deliberate `_generation_origin_for_field` upstream mirror is
   byte-identical modulo type ignores (upstream still 26.1, premises
   re-verified below). No name-by-concatenation, no `_meta`
   re-derivation, no settings re-read.
4. **Round-trip pairs** — searched. Stamp (the `_stamp` closure's 3
   generation-site calls + metaclass declared stamp) vs read (3
   `filter_generation_provenance` call sites) vs inherit (expansion
   `replace`, never mutate); publish (one atomic snapshot under the
   write gate) vs reset (`binding_attrs` walk); build profile (10
   singletons + registry, exact-class + structural-CSV) vs consume
   (`routable` bit only); normalize (wire keys into `data`) vs compose
   (`_evaluate_logic_tree` off `data`); bind (finalizer
   `_owner_definition` write) vs resolve (3 `.origin` readers +
   `registry.get` fallback that refuses `primary_for` by comment);
   declare (`LOGIC_OPERATORS`) vs iterate (the one
   `_iter_logic_branches`, 1 def + 3 call sites: pre-walk, permission
   recursion, Q composition). Each half single-sited; counts verified.
5. **Other media** — searched. Oracles: [test-sets][test-sets] holds 266
   test functions (was 265) with 0 `LOOKUP_NAME_MAP` /
   `_FORM_KEY_BY_PYTHON_ATTR` refs — independence intact. The drift's
   new behavior is pinned by committed oracles spelling literal
   expectations: `test_sets` selection/build-rejection rows,
   `test_base` predicate + stamping + pk/title rows, `test_inputs` /
   [test-factories][test-factories] annotation rows, live
   `test_scalars_filter_api` (parent/children keys) and
   `test_library_api` (`allLibraryCirculationDesksFiltered`, alt-M2M
   keys) rows; projections moved with the commit (README/GLOSSARY
   relation-key rows). Docstring claims re-derived: no `__init__` (AST,
   40 methods); `super().filter_for_field` calls `cls.filter_for_lookup`
   (installed 26.1 `filterset.py`, re-read); empty-body dynamic CSV
   premise (`class ConcreteInFilter(BaseInFilter, filter_class): pass`,
   installed 26.1, re-read); cardinality composition now at 2 code
   sites (REVISE, row 35); metaclass alias write-back; cookbook deltas
   inline. Four projections went stale-narrow under the drift — defect
   D1, not finding revisions.
6. **Enforcement by omission** — enumerated. Generation-site census
   holds with widened coverage: `default` + own-PK + identity
   replacements stamp (the identity arm now covers all 4 tuple classes
   via `type(default)`); `None` returns no row (fail-closed,
   upstream-identical); declared leaves stamped by class-body own-ness
   (borrowed-instance restamp intact); expanded copies inherit, never
   mint. `distinct` stays framework-origin only (consumer `distinct`
   untouched on the outer path). Depth caps fire on all four entry
   shapes (both applies, permission walk, logic evaluation + async
   pre-walk). `_normalize_input` dispatches all three `ActiveField`
   kinds. Dual spellings still read through the one
   `_iter_logic_branches` everywhere applied. Unknown top-level keys
   still degrade to upstream form semantics (unchanged code path, no
   stricter contract source). No gap: no defect beyond D1.

### Lookup-selection and stamp rules (re-derived, new shape)

`FilterSet.filter_for_lookup` (HEAD): ownership first, then shape. The
own-PK arm is unchanged (origin gate, then `in` → multi / `isnull` →
Boolean passthrough / `exact` → scalar, else `ConfigurationError`).
Non-relations keep the upstream default except the integer `in`/`range`
reroutes (unchanged). Every remaining relation key that proves
`framework_default` converts (the drift's core: the old code returned
the model-choice default for non-Relay targets): `isnull` → upstream
Boolean; `in` → the list primitive regardless of cardinality
(`GlobalIDMultipleChoiceFilter` iff `relay_target` else
`RelationPkMultipleFilter`); `exact` → cardinality-selected
(`_relay_filter_class_for_field` iff `relay_target` else
`RelationPkMultipleFilter if many_side else RelationPkFilter`, where
`many_side = is_many_side_relation_kind(relation_kind(field))` — the
second spelling of the shared cardinality composition); any other
lookup → `ConfigurationError` naming the key, the identity spelling,
and `RelatedFilter`. `relay_target = target_type is not None and
implements_relay_node(target_type)` with `target_type` from the
owner-aware `_resolve_relation_target_type` (whose `is_relation` guard
was dropped because its sole caller now passes relations only —
verified: exactly 1 call site).

`FilterSet.filter_for_field` (HEAD): after the unchanged `None` early
return, ownership/capability/distinct prologue (with
`identity_policy_field` widened from Relay-only to any relation, so a
consumer `filter_for_lookup` override on any relation key flips the
origin to `override_generated`), the unchanged `_stamp` closure stamps
`default`; non-capable or non-framework leaves return it. The unchanged
own-PK branch rebuilds via lookup cardinality. The rewritten relation
branch admits exactly the 4 tuple classes (`isinstance(default,
_RELATION_IDENTITY_FILTER_CLASSES)` — `isnull` Booleans fall through to
`return default`), rebuilds `identity_replacement = type(default)(...)`
(preserving `filter_for_lookup`'s lookup-aware choice, never
re-selecting by cardinality), stamps `package_replacement`, then runs
the marker rule: `if _relation_uses_non_pk_to_field(field): setattr(
identity_replacement, _GLOBALID_RELATION_PK_ATTR, True)`.

Stamp-side verification from this side (own counts, HEAD bytes): the
flag lives in exactly 2 production files (owner [filters-base][filters-base]
+ this stamper); the `setattr` is exactly 1 package-wide (this file's
HEAD L1790); the predicate has exactly 1 production call (this file's
HEAD L1789; def in base); `_marked_pk_field_name` has 0 hits here and
def + 4 consumers in base (s7's 2→4 census corroborated); the tuple has
def + 1 consumer (the gate). Single stamp site, both primitives covered
via `type(default)`, predicate composition as briefed. The family row
itself belongs to the globalid-relation-pk-marker re-trace; this file's
side is recorded here only.

### CONFIRM / REVISE per prior finding

Reuse rows (16):

- `lookup-name-spelling-grammar` — CONFIRM. Reverse construction
  byte-identical; table 26 entries at both revisions; oracle
  independence holds ([test-sets][test-sets] 0 refs, 266 fns).
- `filter-logic-operators` — CONFIRM. 3 operators at both revisions;
  emission sites unchanged; the one iterator has 1 def + 3 call sites.
- `set-type-naming` — CONFIRM. Suffix override intact; 0 factory refs.
- `related-set-target-lifecycle` — CONFIRM. Bind call + 3 `.filterset`
  property reads; 0 direct `resolve_lazy_class` / `_bind_owner`.
- `related-declaration-collection` — CONFIRM. `False` policy + args
  intact in the metaclass call.
- `set-expansion-once-skeleton` — CONFIRM. `on_reentry` call intact.
- `set-expansion-cache-write-gate` — CONFIRM. Single call intact.
- `re-readable-field-declaration-gate` — CONFIRM. String exemption
  intact with its rationale comment.
- `active-input-permission-facade` — CONFIRM + owner-drift note. All six
  consumer members behavior-identical (annotations/`@override` only).
  The mixin base `_permission_fallback_path` went staticmethod →
  classmethod (`fef11e64`), but this override was already a classmethod
  at drift base, so dispatch is identical — no contract change for this
  consumer (verified by semantic AST diff: that hunk + `TypeVar`s are
  the file's whole delta).
- `subsystem-clear-lifecycle` — CONFIRM. Declaration + snapshot `extra`
  intact (annotation-only drift).
- `one-sync-boundary` — CONFIRM. 1 wrap in `apply_async`; owner body
  identical, signature generics only.
- `child-queryset-alias-inheritance` — CONFIRM. 1 call with
  `using=parent_db`; owner body identical, signature generics only
  (the adjacent `default_order`/`applied_order` additions don't touch
  it).
- `queryset-seed-and-model-read` — CONFIRM partial. `base_queryset`
  import + 1 call; `model_for` 0 hits — for the family item to
  adjudicate, as before.
- `globalid-relation-pk-marker` — CONFIRM rule, REVISE shape + census
  (this file's side; family row owned by the s19 re-trace). The stamp
  is still single-sited (HEAD L1790) but now covers both primitive
  pairs: the gate admits all 4 tuple classes and the rebuild preserves
  `type(default)`; the predicate still has its single call (HEAD
  L1789); reads stay at 0 here (def + 4 consumers in base, corroborated
  from this side).
- `type-registry-model-type-map` — CONFIRM. `registry.get` x2 +
  `.origin` x3 reads intact; `primary_for` refused by comment (the
  class-docstring `primary_for` sentence predates the drift and stands
  under its prior endorsement — not re-litigated).
- `orm-lookup-path-resolution` — CONFIRM mechanics, REVISE census. The
  cardinality composition `is_many_side_relation_kind(
  relation_kind(field))` now appears at 2 code sites (the pre-existing
  `_relay_filter_class_for_field` + the new `filter_for_lookup`
  `many_side`); both compose the same owner by name — two consumers,
  not two definitions. `classify_path` x1, `path_traverses_to_many` x1
  unchanged; all four owner predicates behavior-identical (verified by
  semantic AST diff: the file's whole delta is a `Protocol`-body
  typing idiom).

File-local rows (18):

- L1 memo — CONFIRM. Cache + copy-on-return intact
  (`ModelField` annotation only).
- L2 strip — CONFIRM mechanics, REVISE projection. Body identical; the
  docstring now names both primitives and states the existence-oracle
  rationale for dropping the `queryset` check.
- L3 extras + defaults — CONFIRM. Four extras + policy table rows
  behavior-identical (ignores only).
- L4 policy + baseline + oracle — CONFIRM. Oracle body identical modulo
  ignores; upstream mirror intact against installed 26.1.
- L5 audit gate — CONFIRM. Range, predicate, flag identical.
- L6 provenance — CONFIRM mechanics. Record, stamp/read/inherit bodies
  identical; the stale-narrow GlobalID-only wordings are defect D1
  (projections, not the contract).
- L7 profiles — CONFIRM rule, REVISE census. 8→10 singletons, registry
  +2 rows, closed tuple +2; exact-class + structural-CSV validator
  unchanged.
- L8 metadata + snapshot — CONFIRM. Records, atomic publish, and
  `binding_attrs` reset identical.
- L9 metaclass — CONFIRM. Collect policy, tombstone rebuild, declared
  stamp (class-body own-ness + borrowed restamp), alias write-back all
  identical; the `TYPE_CHECKING` base is runtime-identical
  (else-branch assigns the same class).
- L10 expansion — CONFIRM. Body identical.
- L11 `get_filters` publish — CONFIRM. Publish population + guard calls
  identical (`@override` + cast removal only).
- L12 `get_fields` — CONFIRM. Both `"__all__"` branches identical;
  R-1 stands.
- L13 generation conditional — REVISE (re-derived above). Selection
  ladder rewritten (every framework-owned relation key converts;
  GlobalID iff relay target else raw-pk; exhaustive
  exact/in/isnull/other classification); gate rewritten (4-tuple
  isinstance + `type(default)` rebuild); policy predicate widened to
  any relation; target-type guard dropped (sole-caller verified);
  `implements_relay_node` 3→2 calls (this method no longer resolves
  the target); relay helper now serves only the relay `exact` arm
  (still 1 call site). New tuple member homed here.
- L14 normalization — CONFIRM. Dispatcher + 3 kinds + shape rules +
  range patch identical (the worktree `_reject_shared_bag_form_keys`
  pre-pass is concurrent dirt, absent at HEAD).
- L15 visibility derive — CONFIRM. Step iterator, twin colorings, and
  async pre-walk identical; owner visibility call-contracts identical
  (one docstring hunk; the seal-policy drift is owner-internal and
  contract-compatible).
- L16 channels — CONFIRM. Cap + raiser + 3 channels identical; all four
  entry shapes fire.
- L17 tree — CONFIRM. Composer, flat-leaf adapter (incl. the
  `is`-identity no-op short-circuit), related constrain, and
  `filter_queryset` identical.
- L18 pipeline — CONFIRM. Prelude/finalize, both entries, dispatcher,
  and validate-or-raise identical.

Rejections (5): R-m1–R-m4 STAND — the orders twin is member-identical
with typing-only drift and every divergence anchor re-verified at HEAD
(the rewritten ladder widens R-m3's apply-pair difference; triggers
unchanged). R-1 STANDS — both branches identical, token-not-contract
separation intact.

Withheld (4 + transitive): all hold at 0 hits — `set-arguments-factory-bfs`,
`dynamic-set-class-getter`, `globalid-decode-input-hardening`,
`sealed-execution-queryset`; `lazy-related-class-resolution` still
transitive-only (0 direct calls).

### Challenges (definition counts)

Authoritative definitions counted only; consumers, oracles, projections
listed, not counted. All probes static-reviewed (HEAD-bytes body
inspection, `git grep HEAD` populations, AST walks, installed-upstream
reads) — no ordering, transactional, or async behavior is decided new
by this drift, so no execution is owed.

- New identity primitive pair on relation keys → the L13 ladder (1)
  plus its gate tuple (same L13 rule) plus L7 profile rows (same
  file-local substrate). The inputs ladder dispatches on the resolved
  instance's class (verified: `convert_with_mro` + strict-zipped
  handlers), so the selection itself stays 1 definition.
- New lookup admitted on relation keys → the `filter_for_lookup`
  exhaustive arm (1); the annotation side is lookup-agnostic per
  instance class (0).
- Cardinality-split change (a relation shape moves sides) → the relay
  helper + the inline pk ternary (2 coordinated edits inside the one
  L13 rule — observation O1 below, within-owner structure, no family).
- New non-pk relation shape → `_relation_uses_non_pk_to_field` (1, at
  its base owner); the stamp follows (0 here); a fifth marked consumer
  composes the read home (0 new). Mid-flight rebase → 0 (derived at
  read from the live `field_name`).
- New audited release → L5 range table (1). New upstream default
  family → L3 table row (1) + L7 profile row (1, same file; the
  baseline derives from the table by construction).
- New logic operator → `LOGIC_OPERATORS` (1, inputs owner); emission
  follows (0 here). New `ActiveField` kind → traversal shape (1,
  input-values owner) + the dispatcher arm (consumer adaptation, as
  before).
- Boundary semantics → `run_in_one_sync_boundary` (1, owner); alias
  inheritance → `base_queryset` (1, owner); guard lifetime →
  `expanded_once` / `should_cache_expansion` (1 each, owner); 0 here
  throughout.
- Bound-filter parent-binding change (s7 F-10) → 2, both base-side;
  this file has 0 involvement (no walk spelling here).

### New families / rows for Worker-0 (plan edits are Worker-0's)

None owed. The drift joins existing rows: the tuple → L13, the
profiles → L7, the widened stamp → the marker reuse row (whose family
row the s19 globalid-relation-pk-marker re-trace owns — this artifact
records this file's side only). O1 (observation, observed-not-homed,
stays with L13): the relay cardinality helper vs the new inline pk
ternary are two coordinated edits inside one rule at one owner — a
within-owner shape note, not a cross-site family. D1 below routes to
Worker-0 for homing.

### Defects (run 8)

- **D1 (`filters/sets.py` owner; docstring projections went
  stale-narrow under the drift).** Four bodies' prose still describes
  the pre-drift GlobalID-only shape while the code now covers both
  identity primitives: the `FilterOrigin` comment
  (`package_replacement` "a NEW `GlobalIDFilter` /
  `GlobalIDMultipleChoiceFilter` ... constructed" — raw-pk
  replacements carry it too); the `FilterGenerationProvenance`
  docstring ("the package's GlobalID replacement branches");
  the `_FRAMEWORK_GENERATED_ORIGINS` comment (same GlobalID-only
  wording); the `_generation_origin_for_field` docstring
  (`filter_for_lookup` "decides whether to convert a Relay-node
  relation to a package GlobalID primitive" — it now converts any
  framework-owned relation key to either primitive). No behavior is
  wrong; each is a docstring-contradicts-body record for Worker-0
  homing (s7-D1 precedent: doc-only, closeout). Never fixed inside
  this item.
- Checked and held (not defects): the `filter_for_field` summary line
  (primary-case framing; body states the full rule); the L17 cost note
  (illustrative example, still true); the module docstring +
  Decision-4 section headers (the decision's name; the
  single-source-of-truth claim re-verified through the convert
  dispatch); the class-docstring `primary_for` sentence (predates the
  drift, prior-endorsed).

### Pending execution

None. Every proof is static-reviewed; no ordering / transactional /
async behavior is decided new here, so no execution-deferred entry
exists. The sharded/Postgres cells are inapplicable by construction
(no alias / `using=` / dialect decision in the drift; the `parent_db`
passthrough is read, never executed — same as run 7).

### Judgment (run 8)

Zero-edit re-trace: matrix discharged against the current surface
(orders mirror re-read at HEAD, upstream premises re-verified on
installed 26.1, stamp populations counted package-wide at HEAD bytes),
99/99 members assigned (16 reuse rows, 18 file-local rows, 5
rejections — 34 CONFIRM/STAND, 5 REVISE: marker shape, orm-lookup
census, L2 projection, L7 census, L13 rules; plus 2 owner-drift notes
carried on CONFIRM rows), challenges recorded with definition counts,
one doc-only defect filed, no pending execution, no new families. The
drift's one behavior commit converts at a single selection ladder,
stamps at the single pre-existing site, and profiles the new primitives
in the pre-existing registry; every other hunk is typing-only.

### Implementation (run 8)

No production edits (file item; reviewer role — no edit rights on
production code). This artifact (untracked `??`, as in run 7) is the
only file touched; the item-scoped diff vs `ITEM_BASELINE`
`bbdaa9b02c785498fe78c5d4a1f04644b8c16477` for
`django_strawberry_framework/filters/sets.py` is empty. The worktree's
153+/63- on the target is concurrent truth-migration dirt, attributed
by content above and untouched. No pytest run and no `workspace.py`
runs: every claim is a HEAD-bytes count or body reading, shared-tree
execution would run dirty bytes unattributable to HEAD, and committed
oracles already pin the new behavior (cited statically). No scratch
files in the repo (all probes read-only: `git show HEAD:`, `git grep
HEAD`, AST walks on HEAD bytes, installed-`.venv` upstream reads,
`/tmp`-only byte dumps cited by content).

## Run-8 verification (Worker 2)

Expectation-first re-trace at HEAD bytes with own instruments; every W1
figure below was re-derived, not trusted. Read-only probes only (`git show
HEAD:`, `git grep HEAD`, AST walks on HEAD bytes, installed-`.venv`
upstream reads, `/tmp`-only dumps); no `workspace.py` runs (nothing
source-mutating was needed), no pytest (not authorized), no `.py` edits
so no ruff/mypy owed. Item-scoped diff vs `ITEM_BASELINE`
`bbdaa9b02c785498fe78c5d4a1f04644b8c16477` for the target is 0 bytes
(re-run); `git status --short` count still 448; HEAD still `83998e08`.

### Own trace (before reconciling)

Fingerprints (all re-hashed): HEAD blob `3d307402` (3660 lines),
worktree `ec278851` (3750 lines, 153+/63-), `9aaaad5d` blob `e47c6758`
(3623 lines), drift-base `0c0537e2` blob `993e887a` (3529 lines). The
`4ab65a26` bytes differ from drift base by exactly 3 comment-only lines
(re-diffed), so the run-7 trace reads as drift-base bytes.

Drift ownership: exactly 7 commits touch the target in `0c0537e2..HEAD`
— `bbe54687` plus the 6 typing commits W1 names; per-commit `+/−`
figures all reproduce. Net drift 359+/228- reproduces; hunk count is
82 under default settings (R2 below), not 86. Whole-file
typing-stripped AST diff (annotations, docstrings, `TYPE_CHECKING`
bases, `cast`, overloads, `TypeVar` removed; metaclass-base idiom
normalized): the residual is exactly the `bbe54687` footprint —
RelationPk imports, the 4-tuple, 2 profiles + closed-tuple +2 +
registry +2, the prologue predicate swap, the relation-branch
gate/rebuild/rename set, the `filter_for_lookup` ladder rewrite, the
resolver guard drop — plus typing idioms (the runtime-identical
`_FilterSetMetaclassBase` else-assign, a `Callable` import feeding an
annotation). Every other member body is behavior-identical across the
drift, which independently sustains all CONFIRM-identical rows.

Enumeration (own AST instrument): HEAD top level 80 = 1 docstring + 29
imports + 12 `AnnAssign` + 14 `Assign` + 14 `FunctionDef` + 8 `ClassDef`
+ 2 `If`; rule-bearing module-level 46 (excluding docstring, imports,
`If` guards, `_M`, the `FilterSet` container); `FilterSet` 52 members
(12 attrs + 40 methods, 3 `async` with the same names as drift);
`FilterSet` NEW/GONE empty; module NEW exactly `_M`,
`_RELATION_IDENTITY_FILTER_CLASSES`, `_RELATION_PK_PROFILE`,
`_RELATION_PK_MULTIPLE_PROFILE`, GONE empty. All 99 row leaves exist
at HEAD bytes; unhomed module and `FilterSet` sets both empty. 99/99
CONFIRMED. (`__all__`: 24 occurrences on 21 lines both revisions —
W1's "21 hits" is the line count; same vocabulary as run 7, held.)

### Adversarial focus

(1) Stamp side — all claims re-proved from this side with own counts.
Tuple holds all 4 classes; gate is `isinstance(default,
_RELATION_IDENTITY_FILTER_CLASSES)` with the `isnull`-Boolean
fall-through returning `default`; rebuild is `identity_replacement =
type(default)(...)` with a comment pinning the lookup-aware choice;
predicate call at HEAD L1789 and `setattr` at HEAD L1790 (exact lines
match). Package-wide at HEAD: exactly 1 `setattr` on the flag
(sets.py:1790); predicate def in base plus exactly 1 production call
(sets.py:1789); flag refs in exactly 2 production files (base: def +
read + 4 prose; sets: import + prose + `setattr`);
`_marked_pk_field_name` 0 hits here; base carries def + 4 consumers in
exactly `GlobalIDFilter.filter`, `GlobalIDMultipleChoiceFilter.filter`,
`RelationPkFilter.filter`, `RelationPkMultipleFilter.filter`, with the
single production `getattr` on the flag at base.py:327 inside the read
home; drift had def + 2 calls, so s7's 2→4 census is corroborated from
both sides. Reads here: 0. Consistent with s7 F-7 on all three claims.

(2) orm-lookup census — the cardinality composition
`is_many_side_relation_kind(relation_kind(field))` appears at exactly 2
code sites (HEAD 2097 `many_side = ...`, 2179 `if ...`) plus 1 docstring
mention; both call the same owner names with the identical argument —
two consumers, not two definitions. `classify_path` x1 call,
`path_traverses_to_many` x1 call. All four owner predicates are
behavior-identical across the drift (annotation/cast-stripped AST
equal; the visible delta is signatures, the Protocol property idiom,
overloads, one `cast`, and the `validate_lookup_expr` unpack in none of
the four). CONFIRM mechanics + REVISE census both hold. (Record note:
W1's parenthetical compresses that delta to "a `Protocol`-body typing
idiom" — the verdict-relevant identity claim is exact; the compression
moves nothing.)

(3) L13 — ladder re-derived from the body as briefed (ownership gate,
then `isnull` passthrough, then `target_type` / `relay_target` /
`many_side` with `in` list-shaped regardless of cardinality, `exact`
cardinality-selected, else `ConfigurationError`). Gate, `type(default)`
rebuild, and the Relay-only→any-relation predicate widening (drift
`relay_policy_field` → HEAD `identity_policy_field`, read both sides)
all verified. Guard drop justified: resolver has exactly 1 code call
site (HEAD 2095), reached only past the `if not field.is_relation:
... return` early exit, and its docstring states the contract. Relay
helper serves only the relay `exact` arm with still 1 call site. Call
count: `implements_relay_node` is 4→2, not 3→2 (R1 below) — drift has
calls at 1597 (prologue), 1669 (relation branch), 1966
(`filter_for_lookup`), 2043 (own-PK) plus the import; HEAD has 2096 +
2155 plus the import. HEAD side correct; L13 REVISE stands.

(4) D1 — all four wordings verified at HEAD bytes, each contradicting
its body: the `FilterOrigin` comment (raw-pk replacements also carry
`package_replacement` via the L1779 stamp), the
`FilterGenerationProvenance` docstring ("the package's GlobalID
replacement branches"), the `_FRAMEWORK_GENERATED_ORIGINS` comment
(same narrow wording), the `_generation_origin_for_field` docstring
(L1846, "convert a Relay-node relation to a package GlobalID
primitive" — it now converts any framework-owned relation key to
either primitive). Genuine doc-only defect; behavior correct in all
four cases. Homing endorsed: closeout defect-homing pass takes the
repair (s7-D1 precedent). Repair authors cleanly — no worktree hunk
touches any D1 line (all four wordings byte-present in the worktree),
so this is the inputs-D1 shape, not the relay-D1 shape.

### Per-row judgments (own counts)

Reuse 16: `lookup-name-spelling-grammar` CONFIRM (reverse construction
byte-identical; table 26 entries both revisions; oracle 266 fns, 0
refs). `filter-logic-operators` CONFIRM (3 operators both revisions; 1
def + 3 calls). `set-type-naming` CONFIRM (suffix intact; 0 factory
refs). `related-set-target-lifecycle` CONFIRM (bind call + 3
`.filterset` reads; 0 direct `resolve_lazy_class` / `_bind_owner`).
`related-declaration-collection` CONFIRM (`False` policy intact).
`set-expansion-once-skeleton` CONFIRM (`on_reentry` call intact).
`set-expansion-cache-write-gate` CONFIRM (single call intact).
`re-readable-field-declaration-gate` CONFIRM (string exemption +
rationale intact). `active-input-permission-facade` CONFIRM (six
members behavior-identical; mixin base staticmethod→classmethod
verified with this override already a classmethod at drift — dispatch
identical). `subsystem-clear-lifecycle` CONFIRM (declaration +
snapshot `extra` intact). `one-sync-boundary` CONFIRM (1 wrap; owner
body behavior-identical). `child-queryset-alias-inheritance` CONFIRM
(1 call with `using=parent_db`; owner body behavior-identical).
`queryset-seed-and-model-read` CONFIRM partial (`base_queryset` import
+ 1 call; `model_for` 0). `globalid-relation-pk-marker` CONFIRM rule +
REVISE shape/census (see (1)). `type-registry-model-type-map` CONFIRM
(`registry.get` x2 + `.origin` x3 code reads; `primary_for` refused by
comment). `orm-lookup-path-resolution` CONFIRM mechanics + REVISE
census (see (2)).

File-local 18: L1 CONFIRM; L2 CONFIRM mechanics + REVISE projection
(body identical per stripped diff; docstring now names both primitives
with the existence-oracle rationale — read); L3/L4/L5 CONFIRM
(identical modulo ignores; upstream mirror intact against installed
26.1); L6 CONFIRM mechanics (D1 wordings are projections); L7 CONFIRM
rule + REVISE census (10 singletons, closed tuple +2, registry +2 —
recounted); L8/L9/L10/L11/L12 CONFIRM (stripped-diff clean; R-1
branches identical); L13 REVISE (see (3)); L14 CONFIRM (3 kinds:
LOGIC copy, RELATED strip, LEAF fall-through — read); L15 CONFIRM
(twins + pre-walk identical; `apply_type_visibility_*` impl bodies
identical, HEAD adds `@overload` stubs only; the wording drift inside
`_prepared_visibility_source` is owner-internal and belongs to s18, not
this row); L16/L17/L18 CONFIRM (stripped-diff clean; 4 entry shapes;
`is`-identity short-circuit intact).

Rejections 5: R-m1–R-m4 STAND (orders twin 15 members both revisions,
NEW/GONE empty; `inherit_from_bases=True` intact; `apply_sync` /
`apply_async` only; no `check_permissions`; order-only
`_prepare_permission_input`; `base_filters` / `_expanded_snapshot` /
code `on_reentry` all 0 — the 2 `_field_type_suffix` / `on_reentry`
hits are divergence-stating prose). R-1 STANDS. Withheld 4 + transitive
hold at 0 hits; F-9/F-10 machinery 0 hits here.

Matrix: all six axes discharged against the real surface. Cross-flavor:
twin re-read, Layer-5 drift annotation-only, `LOOKUP_NAME_MAP.get`
verbatim fallthrough intact at inputs.py:1076, finalizer check is
model-label GlobalID decode-strategy mismatch (raw pks lack that
dimension — read, no omission), `filters/__init__` 0 `RelationPk`,
forms/mutations/rest 0 imports of this target. Twins: same 3 `async`
with identical colorings; drift annotation-only. Derived knowledge:
tuple def + 1 consumer (the gate). Round-trips: `_stamp` closure 3
generation-site calls + metaclass declared stamp; read def + 3 call
sites; expansion inherit; snapshot/reset; 10-singleton profile build
vs `routable`-only consume; bind vs resolve. Other media: committed
oracles pin the drift in all four test files plus live suites
(scalars parent/children rows, library named query — all read);
upstream premises re-verified on installed 26.1
(`filter_class, params = cls.filter_for_lookup(...)` at filterset.py:406;
empty-body `ConcreteInFilter` at :447). Omission: generation census
holds widened (default + own-PK + identity arms; `None` fail-closed);
declared own-ness + borrowed restamp intact; caps, kinds, dual
spellings, unknown-key semantics all read-consistent. No gap beyond D1.

Challenges: counts hold. The inputs ladder rides `convert_with_mro`
with a `zip(..., strict=True)` handler table (verified), so selection
stays 1 definition; the cardinality split is 2 coordinated edits inside
the one L13 rule (O1, within-owner — agreed, no family); F-10 stays
base-side with 0 involvement here.
New families: none owed — agreed (tuple → L13, profiles → L7, widened
stamp → marker row owned by s19; O1 observed-not-homed with L13). No
index changes from this item.

### Dirt attribution (own read, all 32 hunks)

No `## Owned changes` row names this file — every hunk is
concurrent-external. Content: truth migration (`truth` import,
`__dict__` / `__bases__` / `__name__` / `__qualname__` / `vars` /
`isinstance` reads through `truth.*`, `getattr` chains, dropped
`_safe_arg_repr` + `MethodType` imports), 2 new module helpers
(`_inherits_unchanged`, `_registered_profile`, +12 lines each side),
1 new method (`_reject_shared_bag_form_keys` with its `resolved_lookups`
pre-pass), the declared-form-key binding fix, and L7-reader / L13
prologue-predicate / L9 / L15 / L17 / L18 truth rewrites. `9aaaad5d`
vs drift is 153+/59- with 0 `RelationPk`: pre-merge bytes are
drift-base bytes plus the same dirt (`truth.` 42 lines / 46
occurrences in both — W1's "42 refs" is the line count, held).
Drift-behavior lines are semantically intact in the worktree: tuple,
profiles, registry rows, gate, stamp, ladder arms, resolver — no hunk
rewrites any of them. Closest approach: 2 hunks swap `cls.__name__` →
`truth.name(cls)` inside the ladder's two `ConfigurationError`
messages (render-level, wording byte-identical for normal classes);
verdicts describe arm structure, all intact.

### Defects, Pending, record

New defects found by me: none. D1 endorsed for closeout homing as
stated in (4). Pending execution: none owed — every proof is a
HEAD-bytes count or body reading; no ordering / transactional / async
behavior is decided new; sharded/Postgres inapplicable by construction
(no alias / `using=` / dialect decision in the drift). Citations keep
`path::Symbol` form with raw `HEAD L` refs (scratchpad-legal); link
ids bidirectional exact (no orphans either direction).

Record corrections (metadata precision, no resubmission — s1–s8
precedent; no verdict, row, or decision moves):
- R1: `implements_relay_node` drift→HEAD calls are 4→2, not 3→2 (drift
  calls at 1597, 1669, 1966, 2043 + import; HEAD at 2096, 2155 +
  import). L13 REVISE stands unchanged.
- R2: drift-base-vs-HEAD hunk count is 82, not 86 (reproduced across
  `minimal` / `patience` / `histogram` / default; `-U1` gives 101,
  `-U5` gives 67 — no standard setting yields 86). Drift subject
  unchanged: one behavior commit plus typing-only.

### Judgment

Verified, zero-edit. 99/99 members assigned with my own instrument;
34 CONFIRM/STAND + 5 REVISE all survive on independent evidence; stamp
single-sited covering both primitives via `type(default)`; 2
consumer-site orm-lookup census with behavior-identical owners; L13
fully re-derived; D1 genuine doc-only, homed to closeout; no new
families; no pending execution; item-scoped diff empty.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry-file-filters-base]: dry-file-filters__base.md
[dry-file-filters-factories]: dry-file-filters__factories.md
[dry-file-filters-inputs]: dry-file-filters__inputs.md
[dry-file-sets-mixins]: dry-file-sets_mixins.md
[glossary]: ../GLOSSARY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[errs]: ../../django_strawberry_framework/utils/errors.py
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[finalizer]: ../../django_strawberry_framework/types/finalizer.py
[input-values]: ../../django_strawberry_framework/utils/input_values.py
[order-base]: ../../django_strawberry_framework/orders/base.py
[order-factories]: ../../django_strawberry_framework/orders/factories.py
[order-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[predicates]: ../../django_strawberry_framework/optimizer/predicates.py
[relays]: ../../django_strawberry_framework/types/relay.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-relations]: ../../django_strawberry_framework/utils/relations.py

<!-- tests/ -->
[test-factories]: ../../tests/filters/test_factories.py
[test-filter-base]: ../../tests/filters/test_base.py
[test-filter-inputs]: ../../tests/filters/test_inputs.py
[test-sets]: ../../tests/filters/test_sets.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
