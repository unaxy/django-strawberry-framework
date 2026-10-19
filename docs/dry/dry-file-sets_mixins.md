# DRY review: `django_strawberry_framework/sets_mixins.py`

Status: verified
Run: 0.0.15 2026-09-18-1

## System trace

The target owns the set-family shared substrate both shipped set families
compose by name: class-derived GraphQL type naming, lazy related-class
resolution, the related-set owner-bind plus lazy-target lifecycle, the
metaclass collect-and-bind step, the class-level expansion cache plus
reentry-guard skeleton with its two-condition write gate, the `Meta.fields`
re-readability gate, the per-family binding-state descriptor, and the
active-input permission facade. Read in full (768 lines), plus every
connected implementation a sound judgment needs: the two set declarations
([filters-sets][filters-sets]`::FilterSet`, [orders-sets][orders-sets]`::OrderSet`),
their related declarations ([filters-base][filters-base]`::RelatedFilter`,
[orders-base][orders-base]`::RelatedOrder`), both metaclasses
([filters-sets][filters-sets]`::FilterSetMetaclass`,
[orders-sets][orders-sets]`::OrderSetMetaclass`), the reset body
([utils-inputs][utils-inputs]`::clear_generated_input_namespace`) with its
light/heavy namespace pair (`::make_input_namespace`, `::make_set_input_namespace`),
the naming delegate ([utils-inputs][utils-inputs]`::set_input_type_name`) and its
two re-export aliases, the permission mechanics
([utils-permissions][utils-permissions]`::request_from_info`,
`::active_permission_targets`, `::run_active_input_permission_checks` and peers),
the traversal shape ([input-values][input-values]`::SetInputTraversal`), the
shared pascal guard ([utils-strings][utils-strings]`::pascal_case_or_raise`),
the three write-flavor lifecycles ([forms-sets][forms-sets], [mutations-sets][mutations-sets],
[rest-sets][rest-sets]), the bus ([registry][registry]`::register_subsystem_clear`),
the upstream cookbook substrate, and the oracle file ([test-sets-mixins][test-sets-mixins],
954 lines, 30 test functions).

What the target owns (nine rules; no consolidation inside a file item):

- `set-type-naming`: [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin`
  (suffixes plus `::type_name_for`), the one set-family naming rule.
- `lazy-related-class-resolution`:
  [sets-mixins][sets-mixins]`::LazyRelatedClassMixin.resolve_lazy_class`.
- `related-set-target-lifecycle`:
  [sets-mixins][sets-mixins]`::RelatedSetTargetMixin` (bind, resolve, gate hook, set).
- `related-declaration-collection`:
  [sets-mixins][sets-mixins]`::collect_related_declarations`.
- `set-expansion-once-skeleton`:
  [sets-mixins][sets-mixins]`::expanded_once`.
- `set-expansion-cache-write-gate`:
  [sets-mixins][sets-mixins]`::should_cache_expansion`.
- `re-readable-field-declaration-gate`: `::is_re_readable_field_declaration`,
  `::require_re_readable_field_declaration`, `::_TEXT_ATOM_TYPES`,
  `::RE_READABLE_FIELDS_HELP`.
- `active-input-permission-facade`:
  [sets-mixins][sets-mixins]`::ActiveInputPermissionAttrs` plus
  `::ActiveInputPermissionMixin` composing [utils-permissions][utils-permissions] by name.
- Population half of `subsystem-clear-lifecycle` (existing index family):
  [sets-mixins][sets-mixins]`::SetLifecycleAttrs` plus `::binding_attrs`; the bus
  lives in [registry][registry], the reset body in
  [utils-inputs][utils-inputs]`::clear_generated_input_namespace`.

Relation to the [DRY.md][dry] worked example (re-derived against the body, not the
prose): the four mechanics all hold as stated. `FilterSet._lifecycle` names
`_owner_definition` / `_expanded_filters` / `_is_expanding_filters` with
`extra=("_expanded_snapshot",)`; `OrderSet._lifecycle` names
`_owner_definition` / `_expanded_fields` / `_is_expanding_fields` with empty
`extra`. `::binding_attrs` derives `(owner, cache, guard, *extra)`.
`FilterSet.get_filters` and `OrderSet.get_fields` consume the names through
`cls._lifecycle.cache` / `cls._lifecycle.guard` at the `::expanded_once`
call (probe-verified: neither function body spells a slot literal).
[utils-inputs][utils-inputs]`::clear_generated_input_namespace` reads
`lifecycle.binding_attrs` off the set root (probe-verified over the AST string
constants: zero slot literals; the single `_owner_definition` mention in that
function is a comment naming the inherited default, not a store). One drift
found, recorded as D1: the worked example's change-challenge parenthetical
describes the snapshot-reset regression test as reading the slot list from
the declaration; the test spells `"_expanded_snapshot"` literally. The reset
itself discovers the slot by construction; the test does not. The
`FilterSet.get_fields` `"__all__"` intentional separation also holds: the
per-field dict-form lookup expansion and the top-level string-sweep narrowing
are two branches on different `Meta.fields` shapes, recorded in the
[filters-sets][filters-sets]`::FilterSet.get_fields` docstring.

Consumers (all compose by name; sweep counts under Challenges): the two set
classes, the two related declarations, the two metaclasses, the two family
`inputs` modules (naming delegate plus namespace clear), the finalizer bind
subpasses (owner bind, expansion drive, `ImportError` rewrap documented on
the order side with the filter side mirrored), the Layer-5
BFS enqueue and permission traversal (resolved-target reads), and the
`filters/__init__.py` `LazyRelatedClassMixin` re-export. Oracles:
[test-sets-mixins][test-sets-mixins] (construction plus abstract-hook contracts a
request cannot express), family set suites, and the live API suites named in
the oracle module docstring. Projections: the module docstring (port
provenance plus intentional non-ports, verified: the three named cookbook
helpers are absent from the target), per-symbol docstrings (each verified
against its body), DRY.md's worked example (verified with D1 noted), and the
`FilterSet.get_fields` `"__all__"` note (verified).

## Verification

### Matrix

1. **Cross-flavor mirroring.** Read all five set flavors first. Filters and
   orders share the full substrate: `_lifecycle` declarations (filter with
   snapshot `extra`, order without), `_permission` configs, `::expanded_once`
   (filter with `on_reentry`, order without), `::should_cache_expansion`,
   `::require_re_readable_field_declaration`, `::collect_related_declarations`
   (filter `inherit_from_bases=False` over `declared_filters`, order `True`
   over class-body `attrs`), and the mixin bases. Forms, mutations, and
   `rest_framework` sets import nothing from the target: they ride
   `make_declaration_registry` ledgers plus the light
   [utils-inputs][utils-inputs]`::make_input_namespace` clear (ledger only, no
   factory cache, no per-set binding state), as their own `inputs` docstrings
   state. Their input names come from different seams
   (`_form_input_type_name_for`, `input_type_name` over the shape descriptor),
   not from `::type_name_for`. Verdict: shared lifecycle for the two
   related-set graph families; intentionally separate per-declaration
   lifecycles for the three single-declaration write flavors (R2, R3).
   Trigger: a write flavor gaining lazy related-set graph expansion.
2. **Sync/async twins.** Zero `async def` in the target (AST-verified: 24
   function nodes, all `FunctionDef`). Every member is string, dict, or
   class-attribute work: no ORM I/O, no awaits, no threads, no cancellation
   surface. The colored twins live one layer up (`FilterSet.apply_sync` /
   `apply_async`, `OrderSet.apply_sync` / `apply_async`, the
   `run_in_one_sync_boundary` permission wrap); the facade methods they call
   are colorless. `one-sync-boundary` and `sealed-execution-queryset`
   checked, not inherited: no row here executes ORM work or awaits a consumer
   hook. Trigger: an `async def` twin of a target function, or a target row
   touching the database.
3. **Derived rather than repeated knowledge.**
   [utils-inputs][utils-inputs]`::set_input_type_name` delegates
   (`return set_class.type_name_for()`); both family `inputs` modules bind
   `_input_type_name_for = set_input_type_name` (name alias, not a wrapper).
   [filters-inputs][filters-inputs]`::_pascal_case` shares only the emptiness
   guard via [utils-strings][utils-strings]`::pascal_case_or_raise` with its
   own `RangeFilter` error. `::binding_attrs` derives the tuple from the
   record fields. `::_input_traversal` reads the contained traversal (`is`,
   probe-pinned) rather than the field-for-field copy it used to be.
   `_lookups_for_field` (field to concrete lookups, transforms excluded,
   memoized by field class) and `_get_concrete_field_names_for_order`
   (model to column names, hardened past the cookbook's `hasattr(column)`
   for `column=None` virtuals) answer different questions for different
   shapes. Verdict: one derivation each; the lookalikes are distinct
   contracts (R5).
4. **Round-trip pairs.** Bind (`_bind_owner`) versus resolve
   (`_resolved_target`) versus substitute (`_set_target`, deliberately
   unvalidated: validating would import eagerly or fork acceptance rules;
   recorded at the seam). Collect plus bind (collector calls each
   declaration's `_bind_owner`). Publish (family `_build` writes cache plus
   snapshot atomically under the write gate) versus reset
   (`::clear_generated_input_namespace` deletes `::binding_attrs`).
   Materialize versus clear (parked globals stay; ledgers reset). Gate
   (`::require_re_readable_field_declaration`) versus every re-expansion
   walk. Check versus fire (permission walkers versus
   `::invoke_permission_method`). All halves single-sited; the cross-module
   halves are consumers of the half defined here.
5. **Other media.** Production, oracles, and prose classified per finding;
   only definitions counted in Challenges. DRY.md's worked example and the
   module docstrings are projections: every load-bearing sentence re-derived
   (D1 is the one drift). [test-sets-mixins][test-sets-mixins] expectations are
   independent (synthetic suffixes, stub owners, mock targets, and throwaway
   sets; the `_field_specs` identity pins read the live maps but assert
   wiring, never spelling). Specs 027/028 plus the glossary are contract
   sources. No consumer restates a rule: the sweep shows one `def` per
   mechanism package-wide, with the `_validate_target` pair as the designed
   per-family overrides of the abstract hook.
6. **Enforcement by omission.** Both shipped families declare `_lifecycle`,
   `_permission`, a related collection, a metaclass collect call, an
   `::expanded_once` call, a `::should_cache_expansion` call, and a
   re-readability gate call. Each asymmetry carries its contract source:
   filter-only `extra` (snapshot comment: metadata must reset with filters),
   filter-only `on_reentry` (order expansion never re-enters `get_fields`),
   filter-only suffix override (cookbook divergence stated on `OrderSet`),
   filter-only logic hooks versus order-only `_prepare_permission_input`
   (mixin docstring: family-only work stays on hooks), filter string-exempt
   versus order strict string accept (R6: different upstream `Meta.fields`
   shapes; both fail closed). Forms/mutations/rest lack the whole substrate
   by the recorded light-clear rationale (R3), not by omission. The
   hookless-subclass `NotImplementedError` plus the both-families-override pin
   close the gate-omission case; the `None` skip is the documented
   placeholder contract, pinned. No gap: no defect.

### Enumeration

Instrument: `ast` parse of the target. 25 top-level statements (module
docstring plus 10 imports plus 6 classes, 5 functions, 2 module constants,
1 `__all__` assignment); 24 function nodes, all
`FunctionDef`, zero `AsyncFunctionDef`. Imports and the docstring are
machinery/projections, not rules. 45 rule-bearing leaves; every one lands
below. No file-local row except the leaf manifest; each rule with a second
site joins its family.

| # | Member | Home |
|---|---|---|
| 1 | `ClassBasedTypeNameMixin` | F1 |
| 2 | `ClassBasedTypeNameMixin._root_type_suffix` | F1 |
| 3 | `ClassBasedTypeNameMixin._field_type_suffix` | F1 |
| 4 | `ClassBasedTypeNameMixin.type_name_for` | F1 |
| 5 | `LazyRelatedClassMixin` | F2 |
| 6 | `LazyRelatedClassMixin.resolve_lazy_class` | F2 |
| 7 | `RelatedSetTargetMixin` | F3 |
| 8 | `RelatedSetTargetMixin._target_attr` | F3 |
| 9 | `RelatedSetTargetMixin._owner_attr` | F3 |
| 10 | `RelatedSetTargetMixin._bind_owner` | F3 |
| 11 | `RelatedSetTargetMixin._resolved_target` | F3 |
| 12 | `RelatedSetTargetMixin._validate_target` | F3 |
| 13 | `RelatedSetTargetMixin._set_target` | F3 |
| 14 | `collect_related_declarations` | F4 |
| 15 | `expanded_once` | F5 |
| 16 | `should_cache_expansion` | F6 |
| 17 | `_TEXT_ATOM_TYPES` | F7 (R7 for the errors-table homonym) |
| 18 | `RE_READABLE_FIELDS_HELP` | F7 |
| 19 | `is_re_readable_field_declaration` | F7 |
| 20 | `require_re_readable_field_declaration` | F7 |
| 21 | `SetLifecycleAttrs` | `subsystem-clear-lifecycle` (population) |
| 22 | `SetLifecycleAttrs.owner` | `subsystem-clear-lifecycle` (population) |
| 23 | `SetLifecycleAttrs.cache` | `subsystem-clear-lifecycle` (population) |
| 24 | `SetLifecycleAttrs.guard` | `subsystem-clear-lifecycle` (population) |
| 25 | `SetLifecycleAttrs.extra` | `subsystem-clear-lifecycle` (population) |
| 26 | `SetLifecycleAttrs.binding_attrs` | `subsystem-clear-lifecycle` (population) |
| 27 | `ActiveInputPermissionAttrs` | F8 |
| 28 | `ActiveInputPermissionAttrs.family_label` | F8 |
| 29 | `ActiveInputPermissionAttrs.target_attr` | F8 |
| 30 | `ActiveInputPermissionAttrs.traversal` | F8 |
| 31 | `ActiveInputPermissionMixin` | F8 |
| 32 | `ActiveInputPermissionMixin._permission` | F8 |
| 33 | `ActiveInputPermissionMixin._input_traversal` | F8 |
| 34 | `ActiveInputPermissionMixin._request_from_info` | F8 |
| 35 | `ActiveInputPermissionMixin._extract_branch_value` | F8 |
| 36 | `ActiveInputPermissionMixin._iter_active_related_branches` | F8 |
| 37 | `ActiveInputPermissionMixin._invoke_permission_method` | F8 |
| 38 | `ActiveInputPermissionMixin._permission_fallback_path` | F8 |
| 39 | `ActiveInputPermissionMixin._active_permission_field_paths` | F8 |
| 40 | `ActiveInputPermissionMixin._active_permission_targets` | F8 |
| 41 | `ActiveInputPermissionMixin._check_permission_depth` | F8 |
| 42 | `ActiveInputPermissionMixin._run_logic_permission_checks` | F8 |
| 43 | `ActiveInputPermissionMixin._prepare_permission_input` | F8 |
| 44 | `ActiveInputPermissionMixin._run_permission_checks` | F8 |
| 45 | `__all__` | file-local (leaf manifest; challenge below) |

### Challenges

Authoritative definitions counted only; consumers, oracles, projections
listed, not counted. Probes P1-P10
(`docs/dry/temp-tests/dry-file-sets_mixins/probe_sets_mixins.py`, 116
asserts, execution-verified read-only in the shared tree: throwaway classes
only, shipped set classes read never built, no DB, no source mutation).

- F1: change the filter per-field suffix → 1 definition
  (`FilterSet._field_type_suffix`); change the empty-path guard to return the
  root name → 1 (`::type_name_for`); change `LOOKUP_SEP` joining → 1
  (delegates segment handling to the shared pascal guard; P1 pins
  `author__name` parity). Consumers: the delegate alias pair, the
  operator-bag naming, both family roots. `type-registry-model-type-map`
  checked: nothing here reads model-type maps.
- F2: change the relative-fallback scope → 1 (`::resolve_lazy_class`);
  change the zero-arg factory rule → 1; change the `ImportError` passthrough
  → 1. Consumers: both related declarations via `::_resolved_target`, the
  `filters/__init__.py` re-export, the finalizer rewrap prose. P2 rejects.
- F3: second-bind strict-mismatch-raise → 1 (`::_bind_owner`; the finalizer
  strict-equality subpass is a different-phase consumer, not a second bind
  definition); validate-on-set → 1 (the setter stays a pure store by the
  recorded eager-import rationale); drop the `None` skip → 1. Consumers: both
  families' thin wrappers plus gates, finalizer bind/audit, BFS enqueue,
  permission traversal. P3 rejects.
- F4: change the tombstone rule → 1; change diamond reconciliation → 1;
  flip the filter policy to `inherit_from_bases=True` → 1 call-site argument
  (consumer config; the definition does not move). Consumers: the two
  metaclasses. P4 rejects (inherit, override, tombstone, diamond, precedence).
- F5: `__dict__` to `getattr` cache read → 1; drop the `finally` reset → 1
  (P5 `once-exc-guard` rejects); give the order side an `on_reentry` → 1
  call site (consumer). Consumers: `FilterSet.get_filters`,
  `OrderSet.get_fields`. P5 rejects (hit, build-under-guard, reentry,
  no-MRO-inherit).
- F6: add a third write condition → 1; treat `None` targets as uncacheable
  → 1 (P6 `gate-none-target` rejects). Consumers: the two `_build`
  closures. P6 rejects.
- F7: admit generators → 1 (`::is_re_readable_field_declaration`); drop the
  text-atom exclusion → 1 (`::_TEXT_ATOM_TYPES`); reword the contract half →
  1 (`::RE_READABLE_FIELDS_HELP`); drop the filter string exemption → 1
  call-site policy (R6). Consumers: `FilterSet.get_fields`,
  `OrderSet._expand_meta_fields`. P7 rejects (every shipped shape accepted,
  one-shots plus text atoms refused, hostile `__iter__` never entered).
- Population (`subsystem-clear-lifecycle`): add a family cached slot → the
  reset population moves in exactly 1 definition (`::binding_attrs`
  derivation) plus the per-family declaration and the family `_build`
  publish code (adapters, not reset definitions); rename a slot → the
  declaration only, clear plus skeleton follow by construction (P8
  `clear-spells-no-slot`, `once-spells-no-slot` reject a re-spelling).
  Consumers: [utils-inputs][utils-inputs]`::clear_generated_input_namespace`
  body, bus replay. Oracle gap: D1.
- F8: add a shared walker method → 1 (mixin; per-function mechanics in
  [utils-permissions][utils-permissions]); add a sixth traversal axis → 1
  shape ([input-values][input-values]`::SetInputTraversal`) with family
  constructor values as consumers; change the filter fallback remap → 1
  override; change the depth cap → 1 (`FilterSet._MAX_LOGIC_DEPTH` plus
  override); change the family-label wording → 1
  ([utils-permissions][utils-permissions]`::request_from_info`; the mixin
  passes through). Consumers: both `_permission` configs, both normalizers,
  the order warm-up gate. P9 rejects (MRO, identity-equal facade, config,
  traversal identity, remap split, apply distinctness).
- File-local `__all__`: add a symbol → the definition plus the same-file
  manifest entry (one file, no second site); the package root does not
  consume this manifest (no `sets_mixins` import at the root). P10 pins
  completeness plus the three intentional non-ports.

Package-wide mechanism sweep (every `def` per mechanism; call sites as
consumers): `type_name_for`, `resolve_lazy_class`, `_bind_owner`,
`_resolved_target`, `_set_target`, `expanded_once`,
`should_cache_expansion`, `is_re_readable_field_declaration`,
`RE_READABLE_FIELDS_HELP` each defined once; `_validate_target` defined
once plus the two designed family overrides;
`collect_related_declarations` called from exactly the two metaclasses;
`expanded_once` / `should_cache_expansion` called from exactly the two
expansions; `binding_attrs` / `SetLifecycleAttrs` referenced from exactly
the two set modules plus the clear body; `_lifecycle` mentions in the
write-flavor `inputs` modules are comment-only cross-references to the
light-clear rationale (R3 evidence, not sites).

## Findings

Eight named families for Worker 0 to add to the responsibility index (all
`open`; no consolidation inside a file item, so Migration is `none` and the
holding item for each is its future family item). The population rows reuse
the open `subsystem-clear-lifecycle` family as its population sub-rule.

### F1 `set-type-naming`

- **Contract + variation.** Class-derived GraphQL naming: root from
  `cls.__name__` plus `_root_type_suffix`; per-field bag from `cls.__name__`
  plus PascalCased path plus `_field_type_suffix`; no-word-token paths raise
  instead of colliding. Varies on the two suffixes only.
- **Sites + roles.** Definition: `::ClassBasedTypeNameMixin` (suffixes plus
  `::type_name_for`). Consumers: the delegate alias pair, the filter
  operator-bag naming, both family roots. Oracles: live root/bag names plus
  `test_class_based_type_name_mixin`. Projections: mixin plus
  [utils-strings][utils-strings] docstrings (parity claim probed).
- **Challenges.** Suffix → 1; guard → 1; joining → 1.
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin`
  (principle 2: the one set-family naming rule). Pure derivation per call;
  no stored state, no lifetime fields owed.
- **Migration.** None (file item).
- **Distinct behavior.** The filter `_field_type_suffix` override stays
  family config; the order side keeps the defaults (cookbook divergence
  stated on `OrderSet`).
- **Behavioral proof.** P1 execution-verified (root, nested, flat, three
  guard spellings, both family suffix wirings, both delegate aliases,
  shared-guard delegation).
- **Structural gate.** P1 plus `test_class_based_type_name_mixin` and the
  live-name suites (existing oracles; no consolidation relies on a new
  gate, so no negative control is owed here).
- **Coupling.** None.
- **Freshness.** Target `ad8987ea` (= HEAD, clean); [filters-sets][filters-sets]
  `4ab65a26`; [orders-sets][orders-sets] `6044ab1a`; [utils-inputs][utils-inputs]
  `ee31d360`; [utils-strings][utils-strings] `3ec3b262`;
  [filters-inputs][filters-inputs] `82b52d97`; [orders-inputs][orders-inputs]
  `6f6ec946`; upstream cookbook `mixins.py` read (two shipped mixins
  byte-parallel, two factory mixins intentionally unported).

### F2 `lazy-related-class-resolution`

- **Contract + variation.** String (absolute, then bound-module-relative),
  zero-arg callable factory, or passthrough; unresolvable without scope
  re-raises `ImportError`. No legitimate variation in the attempt order.
- **Sites + roles.** Definition: `::resolve_lazy_class`. Consumers: both
  related declarations via `::_resolved_target`, the re-export, the
  finalizer rewrap prose. Oracles: `test_lazy_related_class_mixin*` pair.
- **Challenges.** Scope → 1; factory rule → 1; passthrough → 1.
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::LazyRelatedClassMixin`.
  Stateless; no lifetime.
- **Migration.** None.
- **Distinct behavior.** None inside; family gates live in F3.
- **Behavioral proof.** P2 execution-verified (passthrough, factory,
  sentinel, absolute, synthetic-module relative, both `ImportError` arms).
- **Structural gate.** P2 plus the two oracle tests.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; [filters-base][filters-base] `ba52351c`;
  [orders-base][orders-base] `4736fda0`; [filters-init][filters-init]
  `86b25818`; finalizer `77fd9a2d` (comment consumer only).

### F3 `related-set-target-lifecycle`

- **Contract + variation.** Idempotent owner bind (second bind a no-op;
  cross-owner mismatch caught at finalize, not here); lazy resolve with
  re-store; family gate firing on every non-`None` resolved read at the one
  seam; hookless subclass failing loud; setter a pure unvalidated store.
  Varies on the two attr-name parameters plus the family gate only.
- **Sites + roles.** Definition: `::RelatedSetTargetMixin` (all six
  members). Consumers: `RelatedFilter` / `RelatedOrder` thin wrappers plus
  gates, finalizer bind/audit subpasses, BFS enqueue, permission traversal.
  Oracles: the four target-mixin pins plus the both-families-override pin.
- **Challenges.** Re-bind strictness → 1; validate timing → 1; `None` skip
  → 1.
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::RelatedSetTargetMixin`.
  Owner slot per declaration instance; resolved target re-stored on first
  read (lifetime: declaration instance; invalidation: `_set_target`).
- **Migration.** None.
- **Distinct behavior.** `issubclass(FilterSet)` versus
  `issubclass(OrderSet)` gates stay per family; the `None` skip stays shared.
- **Behavioral proof.** P3 execution-verified (bind, idempotence, read,
  substitute, abstract hook, both families' slots, both overrides present).
- **Structural gate.** P3 plus the override-identity pin (fails if a family
  deletes its gate).
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; bases as in F2.

### F4 `related-declaration-collection`

- **Contract + variation.** Ordered collect of `declaration_type` instances
  onto the new class under `collection_attr`, inherited-merge policy by
  `inherit_from_bases`, non-declaration shadowing as removal, diamond
  tombstone reconciliation against direct-base precedence, then per-item
  `_bind_owner`. Varies on the merge policy plus the two family attr maps.
- **Sites + roles.** Definition: `::collect_related_declarations`.
  Consumers: `FilterSetMetaclass` (`False` over `declared_filters` with
  `class_items` plus `base_declarations_attr`) and `OrderSetMetaclass`
  (`True` over class-body `attrs`). Oracles: the three collect pins.
- **Challenges.** Tombstone → 1; diamond → 1; policy flip → 1 call-site
  argument (consumer config).
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::collect_related_declarations`.
  Runs once per class creation; result stored on the new class.
- **Migration.** None.
- **Distinct behavior.** The two policies stay per call site (django-filter
  merges MRO itself; plain `type` does not; stated at both call sites).
- **Behavioral proof.** P4 execution-verified (override, tombstone, store
  identity, owner recorded on every item).
- **Structural gate.** P4 plus the diamond plus precedence pins.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; [filters-sets][filters-sets] `4ab65a26`;
  [orders-sets][orders-sets] `6044ab1a`.

### F5 `set-expansion-once-skeleton`

- **Contract + variation.** Own-`__dict__` cache read (never MRO-inherited,
  never half-built); filter-only `on_reentry` fallback breaking
  self-referential cycles without caching; guard set plus `finally` clear
  around the family-owned `_build` (which owns the cache-write decision
  including `base_filters`). Single-threaded by stated contract.
- **Sites + roles.** Definition: `::expanded_once`. Consumers:
  `FilterSet.get_filters` (with `on_reentry`), `OrderSet.get_fields`
  (without; never re-enters by construction). Oracles: the two
  `expanded_once` pins.
- **Challenges.** Cache-read receiver → 1; `finally` → 1 (probe rejects
  removal); order `on_reentry` → 1 call site.
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::expanded_once`. Guard
  lifetime: one `_build` call; cache lifetime: class until `registry.clear()`.
- **Migration.** None.
- **Distinct behavior.** The order side's missing `on_reentry` is the stated
  no-reentry contract, not an omission (axis 6).
- **Behavioral proof.** P5 execution-verified (hit skips build, guard held
  during build, guard cleared after, reentry fallback, exception reset,
  subclass isolation).
- **Structural gate.** P5 plus the guard-reset pin.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; set modules as in F4.

### F6 `set-expansion-cache-write-gate`

- **Contract + variation.** Write only when the related collection sits on
  the class's own `__dict__` (not the family base's in-flight empty map)
  and no related entry holds an unresolved string target. No other
  variation.
- **Sites + roles.** Definition: `::should_cache_expansion`. Consumers: the
  two `_build` closures (with `related_filters`/`_filterset` and
  `related_orders`/`_orderset`). Oracles: the write-gate pin.
- **Challenges.** Third condition → 1; `None`-as-uncacheable → 1 (probe
  rejects: `None` is the skip placeholder, cacheable).
- **Owner + lifetime.** [sets-mixins][sets-mixins]`::should_cache_expansion`
  beside F5 (the correctness rule both builds share: caching early pins a
  half-resolved expansion). Pure predicate; no lifetime.
- **Migration.** None.
- **Distinct behavior.** The `None`-target accept stays (skip placeholder,
  never reaches a gate).
- **Behavioral proof.** P6 execution-verified (inherited, unresolved,
  resolved, `None`).
- **Structural gate.** P6 plus the gate pin.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; set modules as in F4.

### F7 `re-readable-field-declaration-gate`

- **Contract + variation.** `Collection` is the contract (holds members, so
  a second walk repeats); text atoms excluded (collections of characters);
  one-shot iterables refused without ever entering `__iter__`. Varies on
  the family `subject` plus `accepted` spellings only.
- **Sites + roles.** Definitions: `::is_re_readable_field_declaration`,
  `::require_re_readable_field_declaration`, `::_TEXT_ATOM_TYPES`,
  `::RE_READABLE_FIELDS_HELP`. Consumers: `FilterSet.get_fields`
  (string-exempt: top-level `"__all__"` is a string; other strings are
  upstream's to reject) and `OrderSet._expand_meta_fields`. Oracles: the
  four gate pins.
- **Challenges.** Admit one-shots → 1; drop atom exclusion → 1; reword
  contract half → 1; drop filter exemption → 1 call-site policy (R6).
- **Owner + lifetime.** [sets-mixins][sets-mixins] (gate pair plus atoms
  plus help). Stateless predicate; no lifetime.
- **Migration.** None.
- **Distinct behavior.** The filter string exemption versus the order
  strict accept (R6); the errors-table homonym versus this table (R7).
- **Behavioral proof.** P7 execution-verified (nine accept shapes, ten
  reject shapes, hostile `__iter__`, message naming receipt plus contract).
- **Structural gate.** P7 plus the four oracle pins.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; set modules as in F4; errors `3e25e93b`
  (R7 membership read at HEAD).

### F8 `active-input-permission-facade`

- **Contract + variation.** One `_permission` record per family (label,
  target attr, contained traversal); the mixin reads it on every call so a
  subclass override reaches the apply path; family-only work stays on three
  hooks plus the provenance hook; apply pipelines stay family-owned.
  Varies on label, target attr, traversal axes, and hook overrides.
- **Sites + roles.** Definitions: `::ActiveInputPermissionAttrs`,
  `::ActiveInputPermissionMixin` (facade plus hooks). Mechanics consumers
  (not definitions of the facade): [utils-permissions][utils-permissions]
  functions, [input-values][input-values]`::SetInputTraversal` shape, both
  normalizers, the order warm-up gate. Oracles: the seven permission pins
  plus live denial rows named in the oracle docstring.
- **Challenges.** New shared walker → 1; sixth traversal axis → 1 shape
  with constructor values as consumers; fallback remap → 1 override; depth
  cap → 1; label wording → 1 mechanics site.
- **Owner + lifetime.** Facade owned at
  [sets-mixins][sets-mixins]`::ActiveInputPermissionMixin`; mechanics owned
  at [utils-permissions][utils-permissions]; shape owned at
  [input-values][input-values]`::SetInputTraversal`. Traversal read per call,
  never cached at import (override reachability); `field_specs` flows by
  reference. No stored derivation beyond the family records.
- **Migration.** None.
- **Distinct behavior.** Filter logic recursion plus depth cap plus form-key
  remap versus order verbatim path plus list shape plus lazy spec warm-up;
  both `apply_*` pairs stay per family (pinned distinct).
- **Behavioral proof.** P9 execution-verified (MRO, seven identity-equal
  facade methods both families, configs, traversal identity both families,
  remap split, logic-keys versus list-shape split, apply distinctness).
  Static-reviewed: the sentinel-override derivation (covered by the oracle
  pin, not re-executed here).
- **Structural gate.** P9 plus the single-sourcing pin (fails if a family
  re-copies a facade method) and the traversal-identity pins.
- **Coupling.** None.
- **Freshness.** Target `ad8987ea`; set modules as in F4;
  [utils-permissions][utils-permissions] `9889d6fe`;
  [input-values][input-values] `f2566609`.

### Population rows for `subsystem-clear-lifecycle` (reuse, not a new family)

`SetLifecycleAttrs` plus `::binding_attrs` are the population sub-rule of
the open index family: the descriptor names the reset attrs once per
family; [utils-inputs][utils-inputs]`::clear_generated_input_namespace` is
the reset body; [registry][registry] is the bus plus phase flag. Challenges
as listed (new slot → 1 reset definition; rename → declaration only).
Owner by responsibility: descriptor at
[sets-mixins][sets-mixins]`::SetLifecycleAttrs` (narrowest home both set
bases can import without cycles); body at
[utils-inputs][utils-inputs]`::clear_generated_input_namespace` (owns ledgers,
factory caches, and the subclass walk); bus at [registry][registry]
(dependency direction wins). Lifetime: `_lifecycle` declared at class
creation; `binding_attrs` derived per clear; binding state lives
first-build to `clear()`. Behavioral proof P8 (both declarations exact,
both tuples exact, every slot exists on its class, clear plus skeleton
spell no slot literal, both expansions consume via `_lifecycle`). Coupling:
none. Freshness: target `ad8987ea`; [utils-inputs][utils-inputs] `ee31d360`;
[registry][registry] `9cc8bb55`; declarations in `4ab65a26` / `6044ab1a`.

### Rejections

- **R1 — per-field `"__all__"` expansion versus top-level `"__all__"` sweep.**
  Considered shared form: one `"__all__"` handler. Difference: dict-form
  values expand through `_lookups_for_field` (transforms excluded);
  string-form sweeps `model._meta` adding the PK and removing M2M. A change
  to either lookup set or sweep membership leaves the other. Home:
  [filters-sets][filters-sets]`::FilterSet.get_fields` docstring (states the
  two features plus the shared gate). Trigger: a change to one branch that
  must move the other.
- **R2 — set-family naming versus write-flavor input names.** Considered
  shared form: every generated input named by `::type_name_for`. Difference:
  write inputs derive from a form class plus operation kind or from the
  mutation shape descriptor, never from a set class; unifying needs a
  from-what mode flag. Home: [forms-sets][forms-sets]`::_form_input_type_name_for`,
  [mutations-sets][mutations-sets]`::DjangoMutation.input_type_name`, and the
  rest-framework twin. Trigger: a write flavor naming its input from the set
  class alone.
- **R3 — heavy set lifecycle versus light write clear.** Considered shared
  form: every family on `_lifecycle` plus factory caches. Difference: write
  flavors derive inputs from one declaration's field set (no BFS graph, no
  lazy targets, no expansion cache), so there is nothing to reset beyond the
  ledger; stated in the light-clear docstring and cross-referenced by all
  three write `inputs` modules. Home:
  [utils-inputs][utils-inputs]`::make_input_namespace`. Trigger: a write
  flavor gaining lazy related-set graph expansion.
- **R4 — descriptor-driven reset versus build-site publish writes.**
  Considered shared form: builds store through `setattr(cls,
  cls._lifecycle.cache, ...)`. Difference: the build owns publish semantics
  (snapshot construction with read-only views, the `base_filters` side
  effect, the conditional gate); routing the store through the descriptor
  saves no change obligation (the value must still be constructed
  per family). Home: `FilterSet.get_filters._build` and
  `OrderSet.get_fields._build`. Trigger: a third publish site, or a publish
  population that must equal `binding_attrs` by construction.
- **R5 — cookbook helpers not ported.** Considered shared form: port
  `get_concrete_field_names` / `InputObjectTypeFactoryMixin` /
  `ObjectTypeFactoryMixin` verbatim. Difference: the order helper hardens
  past `hasattr(column)` for `column=None` virtuals; the factories are
  Graphene-typed while this package emits Strawberry inputs through the
  single-sited BFS scaffold; the 100%-coverage gate would flag unused ports
  as dead. Home: the target module docstring plus
  `orders/inputs.py::_get_concrete_field_names_for_order`. Trigger: a
  shipped set needing the exact cookbook shape.
- **R6 — filter string exemption versus order strict accept.** Considered
  shared form: one `Meta.fields` shape policy. Difference: django-filter
  accepts dict bags and the `"__all__"` string (other strings are upstream's
  to reject); the order contract is list, tuple, set, dict-keys, or
  `"__all__"` only, failing closed with the family's own error. Home: the
  two gate call sites' comments. Trigger: unifying `Meta.fields` shapes
  across families.
- **R7 — sets `_TEXT_ATOM_TYPES` versus errors `_TEXT_ATOM_TYPES`.**
  Considered shared form: one package text-atom table. Difference: same
  name, different membership (`Promise` in errors, absent here) and different
  contracts (message-versus-container flattening versus re-walkable
  declaration); each reason to change belongs to its consumer (the write
  path already owns a third, deliberately different set). Home: both
  module sites. Trigger: a membership change that must move both tables, or
  a third consumer of either exact contract.

## Defects

- **D1 — snapshot-reset test spells the slot instead of deriving it from
  the declaration (worked-example projection drift).** The DRY.md
  change-challenge parenthetical describes the regression test as reading
  the slot list from the declaration so it passes whatever the declaration
  says; `tests/filters/test_sets.py`
  `::test_expansion_snapshot_reset_by_registry_clear_and_rebuilt_fresh`
  asserts `"_expanded_snapshot" not in BookFilter.__dict__` literally. The
  production reset is correct by construction (it walks
  `::binding_attrs`), so no wire or configuration input misbehaves today;
  the gap is proof strength: adding a second `extra` slot would be reset
  correctly yet proven by no test, and the test would need a hand-added
  line per slot. Feasible shape: a `FilterSet` declaring a second
  `extra` entry; input: `get_filters()`, then `registry.clear()`, then
  inspect the new slot. Owner: [filter-test-sets][filter-test-sets] (derive the
  asserted slots from `FilterSet._lifecycle.binding_attrs`, or correct the
  worked-example parenthetical). Never fixed inside this item.

Spot-checks that held (below the bar, not defects): the `expanded_once`
single-threaded prose matches on both consumers; the hookless
`NotImplementedError` fires before any store; the `_resolved_target`
re-store-before-gate preserves the prior inline-gate retry behavior; the
`should_cache_expansion` `None`-target accept matches the skip-placeholder
contract; the module-docstring `AND aggregateset` names the cookbook's
third consumer, not this package's.

## Pending execution

None. All behavioral proofs execution-verified read-only in the shared
tree (P1-P10, 116 asserts; throwaway classes only; shipped set classes
read, never built; shared-tree blob unchanged `ad8987ea`). No
consolidation proposed, so no consolidation gate with negative control is
owed. `FAKESHOP_SHARDED=1` and Postgres cells are inapplicable by
construction: no probe reaches a database, alias, or dialect decision.

## Judgment

Zero-edit file item: matrix discharged against the real five-flavor
surface, 45/45 members assigned (eight new families, the
`subsystem-clear-lifecycle` population reuse, one file-local manifest,
seven rejections with triggers), challenges recorded with counts, and the
worked example re-derived true on all four mechanics plus the `"__all__"`
separation, with one projection drift (D1) routed to its owner. The target
is a well-factored owner: every rule has exactly one definition, the two
set families plus the finalizer, BFS factory, and permission traversal
compose by name, and the write flavors' separate lifecycles are recorded
intention, not omission. No production edit, no test change, no defect
fixed.

## Implementation (Worker 1)

No tracked changes: Write/Edit touched only the two new paths (this
artifact plus probe scratch), and `git status` shows no tracked
modification beyond the pre-existing concurrent dirt. Target clean at
`ad8987ea`, identical to HEAD `9031cb3d`. No commit per standing rule.
Probe formatted scoped to its own path (`uv run ruff format` applied; scoped
`uv run ruff check` still reports 46 findings accepted as probe-scratch
style: `E402` is structural, `django.setup()` must precede the imports, and
`ANN`/`D`/`RUF012`/`PERF203` on throwaway probe classes mirror the oracle
test style; the scratch is gitignored, never committed, and Worker 0 removes
it after `verified`). Scoped trailing-commas `--check` on this artifact
reports it excluded from the source-layout rules (per-cycle scratch
exclusion); the canonical 10-header link block is carried regardless, and
the probe re-ran green after formatting (116 asserts). Scratch kept for
verification:
`docs/dry/temp-tests/dry-file-sets_mixins/probe_sets_mixins.py` (Worker 0
removes by explicit path after `verified`). Concurrent dirt left
untouched: `django_strawberry_framework/connection.py` working hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py` (+31),
`docs/bug_hunt/bug_hunt-0_0_15.md`, `docs/dry/dry-0_0_15.md` (plan file
read, never edited).

## Independent verification (Worker 2)

Run: 0.0.15 2026-09-18-1. Method note: I opened the artifact before
finishing consumer reads (order deviation, disclosed); every row below was
still re-derived against bodies with fresh commands (`ast` counts, `uv run`
execution, `git hash-object`), never taken from W1 prose. Zero production
edits owed; the item-scoped diff is empty (`git diff
3ecc4def3d179cfb268eb2fdea0c81c45f6ca444 --
django_strawberry_framework/sets_mixins.py` prints nothing, exit 0; `git diff
HEAD -- django_strawberry_framework/sets_mixins.py` empty; working blob
`ad8987ea` equals `HEAD`, equals W1's fingerprint).

### Own trace (re-derived against bodies)

| Rule (my name) | Definitions found | Key consumers found | Owner I would choose |
|---|---|---|---|
| Set-family naming | 1: [sets-mixins][sets-mixins]`::ClassBasedTypeNameMixin` (suffixes + `::type_name_for`) | [utils-inputs][utils-inputs]`::set_input_type_name` (body verified: `return set_class.type_name_for()`), both family `inputs` aliases (`is`, probe-pinned), operator-bag naming | The mixin (principle 2) |
| Lazy class resolution | 1: `::resolve_lazy_class` | Both related declarations via `::_resolved_target`, [filters-init][filters-init] re-export (verified present), finalizer rewrap prose | `::LazyRelatedClassMixin` |
| Related-target lifecycle | 1 class (`::RelatedSetTargetMixin`, 7 leaves) + 2 designed family `_validate_target` overrides | `RelatedFilter`/`RelatedOrder` thin wrappers (verified: `bind_filterset`, gate, lazy property, `_set_target` setter), finalizer bind/audit (17/42 mentions), BFS enqueue, permission traversal | The mixin |
| Declaration collection | 1: `::collect_related_declarations` | Exactly 2 call sites with opposed policies (verified: filter `inherit_from_bases=False` over `declared_filters` + `class_items` + `base_declarations_attr`; order `True` over `attrs`) | The function |
| Expansion skeleton | 1: `::expanded_once` | `FilterSet.get_filters` (with `on_reentry`), `OrderSet.get_fields` (without) | The function |
| Cache-write gate | 1: `::should_cache_expansion` | The two `_build` closures (`related_filters`/`_filterset`, `related_orders`/`_orderset`) | The predicate beside F5 |
| Re-readable gate | 4 leaves (predicate pair + atoms + help) | `FilterSet.get_fields` (string-exempt, comment verified) vs `OrderSet._expand_meta_fields` (strict, comment verified) | The gate pair + atoms + help |
| Permission facade | 18 leaves (`::ActiveInputPermissionAttrs` 4 + `::ActiveInputPermissionMixin` 14) | Both `_permission` configs (values verified live), both normalizers, order warm-up gate; mechanics in [utils-permissions][utils-permissions], shape in [input-values][input-values] | Facade here, mechanics + shape where they live |
| Clear population | Descriptor (6 leaves) + `::binding_attrs` derivation | [utils-inputs][utils-inputs]`::clear_generated_input_namespace` (verified: reads `binding_attrs`, zero slot literals in body), bus at [registry][registry] | Reuse open `subsystem-clear-lifecycle` |

Change counts re-derived (definitions only): suffix/guard/joining -> 1/1/1;
scope/factory/passthrough -> 1/1/1; rebind-strictness/validate-on-set/None-skip
-> 1/1/1; tombstone/diamond/policy-flip -> 1/1/1-call-site; cache-receiver/
finally/order-on_reentry -> 1/1/1-call-site; third-condition/None-uncacheable
-> 1/1; admit-one-shots/drop-atoms/reword-contract/filter-exemption ->
1/1/1/1-call-site; new-slot/rename-slot -> 1-reset-definition/declaration-only;
new-walker/sixth-axis/remap/depth-cap/label -> 1/1-shape/1-override/1/1-mechanics.
All agree with W1.

Worked-example truth re-derived: `FilterSet._lifecycle` ==
`('_owner_definition', '_expanded_filters', '_is_expanding_filters',
('\_expanded_snapshot',))` and `OrderSet._lifecycle` ==
`('_owner_definition', '_expanded_fields', '_is_expanding_fields', ())`
(verified live via `uv run`); `binding_attrs` tuples exact both families;
`expanded_once` + clear bodies spell no slot literal (verified); both
expansions call through `cls._lifecycle.cache`/`guard` (probe-pinned).
`"__all__"` separation holds: two branches on different `Meta.fields` shapes,
recorded in the [filters-sets][filters-sets]`::FilterSet.get_fields` docstring
(read in full). One correction below; mechanics 4/4 true.

### Reconciliation vs W1 (45 leaves; 8 new + population reuse + manifest; R1-R7; D1)

Agreement on every family boundary, every count, every owner, D1, and the
zero-edit verdict, with one non-blocking correction:

- **Correction (artifact prose, not a finding):** the System-trace
  parenthetical "(probe-verified: neither function body spells a slot
  literal)" overstates. Both family `_build` closures DO spell publish slots:
  `FilterSet.get_filters._build` writes `cls._expanded_filters`,
  `cls._expanded_snapshot`, `cls.base_filters`; `OrderSet.get_fields._build`
  writes `cls._expanded_fields` (both bodies read live). The probes pinned
  the correct narrower claim (`expanded_once` skeleton + clear body spell no
  slot), and R4 already records the publish-site spelling as designed
  (build owns publish semantics). No family, count, challenge, or owner
  depends on the overstated sentence; prior reasoning is preserved as-is and
  this note corrects the record. Not revision-worthy on its own.

### Enumeration check (member-by-member, own instrument)

Own `ast` run: 25 top-level statements (module docstring + 10 imports + 6
classes + 5 functions + 2 module constants + 1 `__all__`); 24 function nodes,
all `FunctionDef`, zero `AsyncFunctionDef`. Matches W1 exactly.
Leaf partition re-derived: F1 4 + F2 2 + F3 7 + F4 1 + F5 1 + F6 1 + F7 4 +
population 6 + F8 18 + manifest 1 = 45. Every W1 table row maps to a real
member (classes, attrs, methods, constants verified against source); no
member unassigned, no second site missed. Imports + module docstring =
machinery/projection, correctly uncounted.

### Matrix check (cross-flavor first, against the real surface)

1. Cross-flavor: confirmed first-hand — all three write-flavor `sets.py`
   import nothing from the target; their `inputs` `_lifecycle` mentions are
   comment-only rationale cross-refs (read in context), not sites; naming
   seams differ (R2 homes verified present). R2/R3 triggers stated. Agree.
2. Sync/async: 24/0 re-derived; members are string/dict/attr work, no ORM
   I/O; colored twins live one layer up. `one-sync-boundary` /
   `sealed-execution-queryset` correctly not inherited. Agree.
3. Derived knowledge: delegate body verified (`return
   set_class.type_name_for()`); `_input_traversal` identity verified live
   both families (`is`); `binding_attrs` derivation verified. R5
   distinct-contract ruling (field-vs-model questions) endorsed. Agree.
4. Round-trip pairs: bind/resolve/substitute, collect/bind, publish/reset,
   gate/re-expansion, check/fire — each half sited as claimed; `_set_target`
   unvalidated rationale read at the seam. Agree.
5. Other media: oracles independent (see below); DRY.md worked example +
   docstrings are projections, every load-bearing sentence re-derived
   (D1 the one drift). Agree.
6. Omission: both families declare all seven substrate pieces; each
   asymmetry carries a contract source read in place (snapshot comment,
   no-reentry comment, cookbook-divergence note, hook docstrings, R6
   comments). `None`-skip placeholder + hookless-`NotImplementedError` close
   the gate-omission case. No gap, no defect. Agree.

### Counts, roles, oracles

No oracle rewritten: `tests/test_sets_mixins.py` (954 lines, 30 test
functions — counts confirmed) spells expectations literally (synthetic
`_SampleSet…` names, live `BranchFilterInputType`), never deriving from
owner constants. The `_field_specs` identity pins assert wiring, not
spelling. Consumers/ projections tagged correctly throughout; only
definitions counted in every challenge. Agree.

### Equivalence (principle 8)

Zero-edit file item: no behavior change proposed, so no consolidation
equivalence is owed. Behavioral proofs P1–P10 re-ran green HERE
(`DJANGO_SETTINGS_MODULE=config.test_settings
PYTHONPATH=examples/fakeshop uv run python
docs/dry/temp-tests/dry-file-sets_mixins/probe_sets_mixins.py` → `W1 PROBES
PASSED: 116`; target blob still `ad8987ea` after the run — read-only as
claimed). First attempt without the documented env failed on `No module
named 'config'`; with the probe's own documented env it passes — env
sensitivity noted, not a defect. Inspection suffices for the rest (single
definitions composed by name; no ordering/transactional/async surface).

### Eight new families ruling (each earns its row)

- `set-type-naming`: one grammar, principle 2; suffix/guard/joining changes
  each hit one definition. ENDORSED.
- `lazy-related-class-resolution`: standalone contract (attempt order +
  factory rule + passthrough) with its own consumer (re-export); parent
  class of F3 is layering, not duplication; change axes disjoint from F3.
  ENDORSED (not merged into F3).
- `related-set-target-lifecycle`: one cohesive lifecycle, one class; the two
  gates are designed per-family overrides of the abstract hook. ENDORSED.
- `related-declaration-collection`: one function, class-creation-time
  responsibility distinct from F3's instance lifecycle. ENDORSED.
- `set-expansion-once-skeleton` vs `set-expansion-cache-write-gate`:
  SPLIT ENDORSED — skeleton (control flow + guard lifetime) and predicate
  (string-target correctness rule) are distinct contracts with distinct
  reasons to change (`finally` removal hits only F5; third write condition
  hits only F6). Merging would join two definitions under two change axes.
- `re-readable-field-declaration-gate`: structural `Collection` contract +
  atoms + shared help sentence; family spellings stay call-site policy
  (R6). ENDORSED.
- `active-input-permission-facade`: facade/attrs here, mechanics at
  [utils-permissions][utils-permissions], shape at
  [input-values][input-values]; three-owner split matches responsibility
  (dependency direction wins). ENDORSED.
- Population reuse of `subsystem-clear-lifecycle`: correct, not a ninth
  family; descriptor narrowest home both set bases import cycle-free; body
  owns ledgers/caches/walk; bus owns replay. ENDORSED. Worker 0 note: the
  index row's Files-covered omits `sets_mixins.py`, `filters/sets.py`,
  `orders/sets.py`, `utils/inputs.py` — extend it, status stays open.

### Rejections R1–R7 (difference + trigger + home, each re-verified)

- R1: dict-value expansion via `_lookups_for_field` vs string sweep over
  `model._meta` (+PK, −M2M) — different inputs/outputs; home the
  `::FilterSet.get_fields` docstring (read). Trigger stated. AGREE.
- R2: set-class naming vs form+operation/shape-descriptor naming; unifying
  needs a from-what mode flag; homes verified present in all three write
  `sets.py`. Trigger stated. AGREE.
- R3: heavy graph lifecycle vs ledger-only light clear; write flavors have
  no BFS graph/lazy targets/cache; homes the light-clear docstrings (read
  in context). Trigger stated. AGREE.
- R4: descriptor-routed store vs build-owned publish (snapshot immutability
  + `base_filters` side effect + conditional gate); homes the two `_build`
  closures (read). Trigger stated. AGREE.
- R5: cookbook helpers diverge (order hardening past `hasattr(column)`,
  Graphene-typed factories vs Strawberry BFS scaffold, 100%-coverage dead
  code); home the module docstring (read) + order helper. Trigger stated.
  AGREE.
- R6: django-filter dict-bag + `"__all__"`-string shape vs order closed
  list/tuple/set/keys/`"__all__"`; homes the two gate call-site comments
  (read verbatim). Trigger stated. AGREE.
- R7: same name, different membership (`Promise` in errors, verified) and
  different contracts; homes both module sites. Trigger stated. AGREE.
- Coupling: all `none` — correct, no consolidation proposed, nothing must
  land together.

### Fingerprints (re-hashed, all match W1)

Target `ad8987ea` (= HEAD, clean); [filters-sets][filters-sets] `4ab65a26`;
[orders-sets][orders-sets] `6044ab1a`; [utils-inputs][utils-inputs]
`ee31d360`; [utils-strings][utils-strings] `3ec3b262`;
[filters-inputs][filters-inputs] `82b52d97`;
[orders-inputs][orders-inputs] `6f6ec946`; [filters-base][filters-base]
`ba52351c`; [orders-base][orders-base] `4736fda0`;
[filters-init][filters-init] `86b25818`; finalizer `77fd9a2d`;
[registry][registry] `9cc8bb55`;
[utils-permissions][utils-permissions] `9889d6fe`;
[input-values][input-values] `f2566609`; errors `3e25e93b`. 15/15 match —
no finding stale. Concurrent dirt (`connection.py` hunk,
`tests/test_connection.py`, staged `tests/utils/test_querysets.py`,
`docs/bug_hunt/bug_hunt-0_0_15.md`, plan file) intersects no fingerprinted
site; left untouched.

### Gates, negative controls, Pending

No consolidation proposed → no new gate → no negative control owed; each
family names the existing oracles that would catch a second definition
(test pins + live-name suites + probe re-run above). Family items will owe
gates + `prove_failability` negative controls at consolidation time; that
obligation is future, not skipped. `## Pending execution` absent — correct:
all proofs execution-verified, and sharded/Postgres inapplicable by
construction with the reason stated (no probe reaches a database, alias, or
dialect decision). Agree.

### AGENTS.md prose check

Item-scoped diff empty → no code-comment, test-tier, or coverage-gate
concerns arise. Artifact citations use `path::Symbol` form with
reference-style links; link block carries all 10 canonical headers; no raw
`path:NN` citations (the "768/954 lines" phrases are sizes, not refs);
probe `.py` is ASCII-clean; no process provenance recorded; no spec/TODO
anchors added; concurrent files untouched. PASS.

### D1 verification (Worker 2) — endorsed as filed, non-blocking

Independently verified: `tests/filters/test_sets.py`
`::test_expansion_snapshot_reset_by_registry_clear_and_rebuilt_fresh` spells
`"_expanded_snapshot"` and `"_expanded_filters"` literally (test body read),
while the [DRY.md][dry] worked-example parenthetical claims the test reads
the slot list from the declaration. Production is correct by construction
(clear walks `::binding_attrs` — verified zero slot literals in the body),
so no wire or configuration input misbehaves; feasible shape (second
`extra` slot) + input (`get_filters()`, `registry.clear()`, inspect) are
real but the failure would be proof-silence, not wrong behavior.
Properly homed: owner is the test file ([filter-test-sets][filter-test-sets]),
correctly NOT fixed inside this item; Worker 0 to card it at closeout
(defect needs a NAMED owning card before closeout per [DRY.md][dry]).
Blocks nothing: no consolidation is proposed and the population rows
disclose the gap ("Oracle gap: D1") without depending on it. No further
defects found (spot-checks in W1 concur on re-read).

### Verdict

`Status: verified`. Zero-edit file item: 45/45 members assigned to 8
endorsed new families + the `subsystem-clear-lifecycle` population reuse +
1 file-local manifest; 7 rejections with triggers; worked example true on
all four mechanics plus separation (1 prose correction noted above, 1
proof-strength defect D1 routed, neither blocking).

### Worker 0 actions (exact rows)

Status `open` for all eight; holding item is each future family item; no
consolidation inside this file item (`Migration: none` throughout):

- Families lines: `- [ ] Family \`set-type-naming\` —
  [dry-rule-set-type-naming.md](dry-rule-set-type-naming.md)`,
  `- [ ] Family \`lazy-related-class-resolution\` —
  [dry-rule-lazy-related-class-resolution.md](dry-rule-lazy-related-class-resolution.md)`,
  `- [ ] Family \`related-set-target-lifecycle\` —
  [dry-rule-related-set-target-lifecycle.md](dry-rule-related-set-target-lifecycle.md)`,
  `- [ ] Family \`related-declaration-collection\` —
  [dry-rule-related-declaration-collection.md](dry-rule-related-declaration-collection.md)`,
  `- [ ] Family \`set-expansion-once-skeleton\` —
  [dry-rule-set-expansion-once-skeleton.md](dry-rule-set-expansion-once-skeleton.md)`,
  `- [ ] Family \`set-expansion-cache-write-gate\` —
  [dry-rule-set-expansion-cache-write-gate.md](dry-rule-set-expansion-cache-write-gate.md)`,
  `- [ ] Family \`re-readable-field-declaration-gate\` —
  [dry-rule-re-readable-field-declaration-gate.md](dry-rule-re-readable-field-declaration-gate.md)`,
  `- [ ] Family \`active-input-permission-facade\` —
  [dry-rule-active-input-permission-facade.md](dry-rule-active-input-permission-facade.md)`.
- Index rows (full lines): `| \`set-type-naming\` |
  \`django_strawberry_framework/sets_mixins.py::ClassBasedTypeNameMixin\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\`,
  \`django_strawberry_framework/utils/inputs.py\`,
  \`django_strawberry_framework/filters/inputs.py\`,
  \`django_strawberry_framework/orders/inputs.py\`,
  \`django_strawberry_framework/utils/strings.py\` | Family
  \`set-type-naming\` | open |`, `| \`lazy-related-class-resolution\` |
  \`django_strawberry_framework/sets_mixins.py::LazyRelatedClassMixin\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/base.py\`,
  \`django_strawberry_framework/orders/base.py\`,
  \`django_strawberry_framework/filters/__init__.py\`,
  \`django_strawberry_framework/types/finalizer.py\` | Family
  \`lazy-related-class-resolution\` | open |`, `|
  \`related-set-target-lifecycle\` |
  \`django_strawberry_framework/sets_mixins.py::RelatedSetTargetMixin\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/base.py\`,
  \`django_strawberry_framework/orders/base.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\`,
  \`django_strawberry_framework/types/finalizer.py\`,
  \`django_strawberry_framework/utils/inputs.py\`,
  \`django_strawberry_framework/utils/permissions.py\` | Family
  \`related-set-target-lifecycle\` | open |`, `|
  \`related-declaration-collection\` |
  \`django_strawberry_framework/sets_mixins.py::collect_related_declarations\`
  | \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\` | Family
  \`related-declaration-collection\` | open |`, `|
  \`set-expansion-once-skeleton\` |
  \`django_strawberry_framework/sets_mixins.py::expanded_once\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\` | Family
  \`set-expansion-once-skeleton\` | open |`, `|
  \`set-expansion-cache-write-gate\` |
  \`django_strawberry_framework/sets_mixins.py::should_cache_expansion\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\` | Family
  \`set-expansion-cache-write-gate\` | open |`, `|
  \`re-readable-field-declaration-gate\` |
  \`django_strawberry_framework/sets_mixins.py::is_re_readable_field_declaration\`
  | \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\` | Family
  \`re-readable-field-declaration-gate\` | open |`, `|
  \`active-input-permission-facade\` |
  \`django_strawberry_framework/sets_mixins.py::ActiveInputPermissionMixin\` |
  \`django_strawberry_framework/sets_mixins.py\`,
  \`django_strawberry_framework/filters/sets.py\`,
  \`django_strawberry_framework/orders/sets.py\`,
  \`django_strawberry_framework/utils/permissions.py\`,
  \`django_strawberry_framework/utils/input_values.py\`,
  \`django_strawberry_framework/filters/inputs.py\`,
  \`django_strawberry_framework/orders/inputs.py\` | Family
  \`active-input-permission-facade\` | open |`.
- Extend the open `subsystem-clear-lifecycle` index row's Files-covered with
  `django_strawberry_framework/sets_mixins.py`,
  `django_strawberry_framework/filters/sets.py`,
  `django_strawberry_framework/orders/sets.py`,
  `django_strawberry_framework/utils/inputs.py` (population found here).
- Card D1 on a NAMED owning card at closeout (owner
  `tests/filters/test_sets.py`; proof-strength only, non-blocking).
- Remove scratch by explicit path after ticking:
  `docs/dry/temp-tests/dry-file-sets_mixins/probe_sets_mixins.py`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[dry]: DRY.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[filters-base]: ../../django_strawberry_framework/filters/base.py
[filters-init]: ../../django_strawberry_framework/filters/__init__.py
[filters-inputs]: ../../django_strawberry_framework/filters/inputs.py
[filters-sets]: ../../django_strawberry_framework/filters/sets.py
[forms-sets]: ../../django_strawberry_framework/forms/sets.py
[input-values]: ../../django_strawberry_framework/utils/input_values.py
[mutations-sets]: ../../django_strawberry_framework/mutations/sets.py
[orders-base]: ../../django_strawberry_framework/orders/base.py
[orders-inputs]: ../../django_strawberry_framework/orders/inputs.py
[orders-sets]: ../../django_strawberry_framework/orders/sets.py
[registry]: ../../django_strawberry_framework/registry.py
[rest-sets]: ../../django_strawberry_framework/rest_framework/sets.py
[sets-mixins]: ../../django_strawberry_framework/sets_mixins.py
[utils-inputs]: ../../django_strawberry_framework/utils/inputs.py
[utils-permissions]: ../../django_strawberry_framework/utils/permissions.py
[utils-strings]: ../../django_strawberry_framework/utils/strings.py

<!-- tests/ -->
[filter-test-sets]: ../../tests/filters/test_sets.py
[test-sets-mixins]: ../../tests/test_sets_mixins.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
